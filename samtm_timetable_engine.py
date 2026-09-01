"""SamTM timetable generation lifecycle.

This module owns only the generation state machine.  It deliberately knows
nothing about FastAPI, PostgreSQL or React.  The school adapter supplies the
data, exact solver, validators and persistence callbacks.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Callable, Mapping, MutableMapping, Optional, Sequence


RUNTIME_RELEASE = "SAMTM-SCHEDULE-RUNTIME-V23.6-DIAGNOSTIC-CONTINUE"


class Stage(str, Enum):
    PREPARING = "tayyorlash"
    SOLVING = "toliq_qidiruv"
    CHECKPOINT = "toliq_saqlandi"
    IMPROVING = "oqituvchi_yaxshilanmoqda"
    REVISION = "revision_saqlandi"
    READY = "tayyor"
    STOPPED = "toxtatildi"
    ERROR = "xato"


TERMINAL_STAGES = frozenset({Stage.READY, Stage.STOPPED, Stage.ERROR})


class GenerationCancelled(RuntimeError):
    pass


class GenerationFailed(RuntimeError):
    pass


@dataclass(frozen=True)
class Progress:
    run_id: int
    revision: int
    percent: int
    stage: Stage
    message: str


@dataclass
class GenerationResult:
    run_id: int
    revision: int
    stage: Stage
    complete: bool
    state: Optional[MutableMapping[str, Any]] = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    message: str = ""


@dataclass(frozen=True)
class RuntimePolicy:
    solve_seconds: float = 120.0
    post_feasible_quality_seconds: float = 2.5
    improve_seconds: float = 45.0
    cancel_poll_seconds: float = 0.25
    retry_unknown_until_stopped: bool = True


Solve = Callable[..., Mapping[str, Any]]
Validate = Callable[[Sequence[Mapping[str, Any]]], Sequence[Any]]
Persist = Callable[..., bool]
Improve = Callable[..., MutableMapping[str, Any]]
ProgressWriter = Callable[[Progress], None]
CancelCheck = Callable[[], bool]
Clock = Callable[[], float]


class ScheduleRuntime:
    """One-run controller with an immutable complete checkpoint guarantee."""

    def __init__(
        self,
        *,
        solve: Solve,
        validate: Validate,
        persist: Persist,
        improve: Improve,
        write_progress: ProgressWriter,
        cancel_requested: CancelCheck,
        policy: RuntimePolicy = RuntimePolicy(),
        clock: Clock = time.monotonic,
    ) -> None:
        self.solve = solve
        self.validate = validate
        self.persist = persist
        self.improve = improve
        self.write_progress = write_progress
        self.cancel_requested = cancel_requested
        self.policy = policy
        self.clock = clock
        self._last_cancel_poll = float("-inf")
        self._cancelled = False

    def _is_cancelled(self, *, force: bool = False) -> bool:
        if self._cancelled:
            return True
        now = self.clock()
        if force or now - self._last_cancel_poll >= self.policy.cancel_poll_seconds:
            self._last_cancel_poll = now
            self._cancelled = bool(self.cancel_requested())
        return self._cancelled

    def _progress(
        self, run_id: int, revision: int, percent: int,
        stage: Stage, message: str,
    ) -> None:
        self.write_progress(Progress(
            run_id=int(run_id), revision=int(revision),
            percent=max(0, min(100, int(percent))),
            stage=stage, message=str(message),
        ))

    @staticmethod
    def _placements(state: Optional[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        return list((state or {}).get("placements") or [])

    @staticmethod
    def _class_day_signature(state: Optional[Mapping[str, Any]]) -> tuple:
        source = state or {}
        signature: list[tuple[str, int, int, str, int]] = [
            ("aggregate", int(key[0]), int(key[1]), "", int(value or 0))
            for key, value in (source.get("class_daily_total") or {}).items()
            if int(value or 0) > 0
        ]

        # A/B weeks must be frozen independently too.  Aggregate class totals
        # alone could let a TOQ-only lesson and a JUFT-only lesson trade days
        # while keeping the visible total unchanged.
        phase_totals: dict[tuple[int, int, str], int] = {}
        for placement in source.get("placements") or ():
            job = placement.get("job") or {}
            class_id = int(job.get("sinf_id") or 0)
            day = int(placement.get("day") or 0)
            if not class_id or not day:
                continue
            raw_phases = [
                member.get("hafta_turi")
                for member in (job.get("rotation_members") or ())
            ] or [job.get("hafta_turi")]
            phases: set[str] = set()
            for raw_phase in raw_phases:
                phase = str(raw_phase or "har_hafta").strip().casefold()
                if phase in {"toq", "odd", "a"}:
                    phases.add("toq")
                elif phase in {"juft", "even", "b"}:
                    phases.add("juft")
                else:
                    phases.update(("toq", "juft"))
            for phase in phases:
                key = (class_id, day, phase)
                phase_totals[key] = phase_totals.get(key, 0) + 1
        signature.extend(
            ("phase", class_id, day, phase, count)
            for (class_id, day, phase), count in phase_totals.items()
            if count > 0
        )
        return tuple(sorted(signature))

    def _validate_complete(
        self, state: MutableMapping[str, Any], expected_jobs: int,
    ) -> None:
        rows = self._placements(state)
        if len(rows) != int(expected_jobs):
            raise GenerationFailed(
                f"To‘liq jadval emas: {len(rows)}/{int(expected_jobs)} dars"
            )
        errors = list(self.validate(rows) or [])
        if errors:
            raise GenerationFailed(
                "Jadval qattiq tekshiruvdan o‘tmadi: "
                + "; ".join(str(value) for value in errors[:12])
            )

    @staticmethod
    def _snapshot(state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        """Detach a saved checkpoint from every mutable optimizer object."""

        return copy.deepcopy(state)

    @staticmethod
    def _score_improved(details: Mapping[str, Any]) -> bool:
        """Reject a revision when the optimizer proves it is not better.

        Integrations that do not publish comparable scores keep the historical
        behavior and are still checked by the hard validator and frozen class
        day signature.  SamTM's teacher optimizer publishes lexicographic
        ``before_score``/``after_score`` tuples where a smaller tuple is better.
        """

        before = details.get("before_score")
        after = details.get("after_score")
        if before is None or after is None:
            return True
        try:
            return tuple(after) < tuple(before)
        except (TypeError, ValueError):
            return False

    def run(
        self,
        *,
        run_id: int,
        jobs: Sequence[Mapping[str, Any]],
        context: Mapping[str, Any],
        seed: int,
        initial_state: Optional[MutableMapping[str, Any]] = None,
        starting_revision: int = 0,
    ) -> GenerationResult:
        total = len(jobs)
        revision = max(0, int(starting_revision))
        revision_at_start = revision
        checkpoint: Optional[MutableMapping[str, Any]] = None
        checkpoint_diagnostics: dict[str, Any] = {}

        self._progress(
            run_id, revision, 8, Stage.PREPARING,
            f"Jadval #{run_id}: {total} ta dars tayyorlandi.",
        )
        try:
            if initial_state is None:
                if self._is_cancelled(force=True):
                    raise GenerationCancelled()
                self._progress(
                    run_id, revision, 15, Stage.SOLVING,
                    f"Jadval #{run_id}: barcha darsni 100% joylashtirish qidirilmoqda.",
                )
                attempt = 0
                while True:
                    attempt += 1
                    solved = dict(self.solve(
                        jobs=jobs,
                        context=dict(context),
                        seed=int(seed) + attempt - 1,
                        max_seconds=float(self.policy.solve_seconds),
                        quality_seconds=float(self.policy.post_feasible_quality_seconds),
                        cancel_requested=lambda: self._is_cancelled(),
                    ) or {})
                    if self._is_cancelled(force=True) and not solved.get("complete"):
                        raise GenerationCancelled()
                    if solved.get("complete"):
                        break
                    status = str(solved.get("status") or "UNKNOWN").upper()
                    # UNKNOWN — vaqt bo'lagi tugadi, imkonsizlik emas. Yangi
                    # seed bilan qidiruv foydalanuvchi to'xtatmaguncha davom etadi.
                    if status == "UNKNOWN" and self.policy.retry_unknown_until_stopped:
                        self._progress(
                            run_id, revision, 15 + (attempt % 30), Stage.SOLVING,
                            f"Jadval #{run_id}: qidiruv davom etmoqda, {attempt}-bosqich. "
                            "Vaqt bo‘lagi tugashi jadval imkonsiz degani emas.",
                        )
                        continue
                    raise GenerationFailed(
                        str(solved.get("message") or status or
                            "100% jadval topilmadi")
                    )
                state = solved.get("state")
                if not isinstance(state, MutableMapping):
                    raise GenerationFailed("Solver to‘liq state qaytarmadi")
                checkpoint_diagnostics = dict(solved.get("diagnostics") or {})
            else:
                state = initial_state
                checkpoint_diagnostics = {"reused_complete_schedule": True}

            self._validate_complete(state, total)
            checkpoint_candidate = self._snapshot(state)
            frozen_class_days = self._class_day_signature(checkpoint_candidate)
            if not self.persist(
                run_id=run_id, revision=revision,
                state=self._snapshot(checkpoint_candidate),
                diagnostics=checkpoint_diagnostics, terminal=False,
            ):
                raise GenerationFailed(
                    f"Jadval #{run_id} topildi, ammo bazaga saqlanmadi"
                )
            checkpoint = checkpoint_candidate
            self._progress(
                run_id, revision, 55, Stage.CHECKPOINT,
                f"Jadval #{run_id} saqlandi: {total}/{total} dars. Uni hozir ochish mumkin.",
            )

            if self._is_cancelled(force=True):
                raise GenerationCancelled()

            improve_seconds = float(self.policy.improve_seconds)
            improve_deadline = (
                self.clock() + improve_seconds if improve_seconds > 0 else 0.0
            )

            def accepted(candidate: MutableMapping[str, Any], details: Mapping[str, Any]) -> bool:
                nonlocal revision, checkpoint, checkpoint_diagnostics

                def rejected(reason: str) -> bool:
                    if isinstance(details, MutableMapping):
                        details["runtime_rejection_reason"] = str(reason)
                    return False

                if self._is_cancelled():
                    return rejected("cancel_requested")
                if not self._score_improved(details or {}):
                    return rejected("score_not_improved")
                candidate_snapshot = self._snapshot(candidate)
                try:
                    self._validate_complete(candidate_snapshot, total)
                except Exception as validation_error:
                    return rejected(
                        "hard_validator:" + type(validation_error).__name__
                    )
                if self._class_day_signature(candidate_snapshot) != frozen_class_days:
                    # Birinchi jadvaldagi teng kunlik taqsimot (masalan
                    # 6/6/6/6/6 yoki 6/6/6/6/5) mutlaq qotirilgan.
                    # Notekis candidate ko'rsatilmaydi va saqlanmaydi.
                    return rejected("frozen_class_day_signature")
                next_revision = revision + 1
                next_diagnostics = {
                    **checkpoint_diagnostics,
                    **dict(details or {}),
                    "revision": next_revision,
                }
                try:
                    persisted = bool(self.persist(
                        run_id=run_id, revision=next_revision,
                        state=self._snapshot(candidate_snapshot),
                        diagnostics=next_diagnostics, terminal=False,
                    ))
                except Exception as persist_error:
                    return rejected(
                        "persist_exception:" + type(persist_error).__name__
                    )
                if not persisted:
                    return rejected("persist_rejected")
                revision = next_revision
                checkpoint = candidate_snapshot
                checkpoint_diagnostics = next_diagnostics
                improvement_summary = str(
                    (details or {}).get("xulosa") or ""
                ).strip()
                self._progress(
                    run_id, revision, min(94, 60 + revision), Stage.REVISION,
                    f"Jadval #{run_id}.{revision} saqlandi"
                    + (f": {improvement_summary}." if improvement_summary else ".")
                    + " Keyingi o‘qituvchi oknosi tekshirilmoqda.",
                )
                return True

            self._progress(
                run_id, revision, 60, Stage.IMPROVING,
                f"Jadval #{run_id}: barcha muammoli o‘qituvchilarning haqiqiy "
                "oknolari navbat bilan qisilyapti.",
            )
            improved = self.improve(
                state=self._snapshot(checkpoint),
                context=dict(context),
                deadline=improve_deadline,
                cancel_requested=lambda: self._is_cancelled(),
                accepted=accepted,
                seed=int(seed) ^ 0x5A17,
            )
            if isinstance(improved, MutableMapping):
                self._validate_complete(improved, total)
                optimizer_diagnostics = {
                    str(key): copy.deepcopy(value)
                    for key, value in improved.items()
                    if str(key).startswith((
                        "v225_teacher_", "v196_teacher_window_",
                        "v226_class_day_counts_", "v225_optimizer_",
                    ))
                }
                checkpoint_diagnostics = {
                    **checkpoint_diagnostics,
                    **optimizer_diagnostics,
                }

            optimized_targets = int(
                checkpoint_diagnostics.get("v225_teacher_targets") or 0
            )
            optimized_trials = int(
                checkpoint_diagnostics.get("v225_teacher_window_trials") or 0
            )
            optimized_swaps = int(
                checkpoint_diagnostics.get("v196_teacher_window_swaps") or 0
            )
            callback_rejections = int(
                checkpoint_diagnostics.get("v225_teacher_callback_rejections") or 0
            )
            rejection_reasons = dict(
                checkpoint_diagnostics.get("v225_teacher_rejection_reasons")
                or {}
            )
            rejection_reason_text = ", ".join(
                f"{reason}={int(count or 0)}"
                for reason, count in sorted(rejection_reasons.items())
            )
            if revision == revision_at_start:
                self._progress(
                    run_id, revision, 95, Stage.IMPROVING,
                    f"Jadval #{run_id}: {optimized_targets} ta muammoli o‘qituvchi "
                    f"uchun {optimized_trials} ta hard-safe almashuv tekshirildi; "
                    f"{callback_rejections} ta nomzod validator/baza tomonidan rad etildi"
                    + (f" ({rejection_reason_text})" if rejection_reason_text else "")
                    + ". "
                    + "Saqlashga yaroqli yangi revision topilmadi.",
                )

            if self._is_cancelled(force=True):
                raise GenerationCancelled()

            if checkpoint is None:
                raise GenerationFailed("Saqlangan to‘liq jadval yo‘q")
            self._validate_complete(checkpoint, total)
            if not self.persist(
                run_id=run_id, revision=revision,
                state=self._snapshot(checkpoint),
                diagnostics=checkpoint_diagnostics, terminal=True,
            ):
                raise GenerationFailed("Yakuniy jadvalni belgilashda xato")
            message = (
                f"Eng yaxshi Jadval #{run_id}"
                + (f".{revision}" if revision else "")
                + f" asosiy #{run_id}ga qo‘yildi: {total}/{total} dars "
                "joylashdi va ochildi."
                + (
                    f" {optimized_targets} ta o‘qituvchi bo‘yicha "
                    f"{optimized_trials} ta variant tekshirildi, "
                    f"{optimized_swaps} ta yaxshilanish saqlandi."
                    if optimized_targets or optimized_trials or optimized_swaps
                    else ""
                )
            )
            self._progress(run_id, revision, 100, Stage.READY, message)
            return GenerationResult(
                run_id, revision, Stage.READY, True, checkpoint,
                checkpoint_diagnostics, message,
            )
        except GenerationCancelled:
            if checkpoint is not None:
                self._validate_complete(checkpoint, total)
                terminal_saved = False
                try:
                    terminal_saved = bool(self.persist(
                        run_id=run_id, revision=revision,
                        state=self._snapshot(checkpoint),
                        diagnostics=checkpoint_diagnostics, terminal=True,
                    ))
                except Exception as terminal_error:
                    checkpoint_diagnostics = {
                        **checkpoint_diagnostics,
                        "terminal_persist_error": str(terminal_error),
                    }
                message = (
                    f"To‘xtatildi. Eng yaxshi #{run_id}"
                    f"{'.' + str(revision) if revision else ''} varianti "
                    + (
                        f"asosiy Jadval #{run_id}ga qo‘yildi va ochildi."
                        if terminal_saved else
                        f"oldin saqlangan asosiy Jadval #{run_id}dan ochildi."
                    )
                )
                self._progress(run_id, revision, 100, Stage.STOPPED, message)
                return GenerationResult(
                    run_id, revision, Stage.STOPPED, True, checkpoint,
                    checkpoint_diagnostics, message,
                )
            message = "To‘xtatildi. Hali 100% jadval topilmagan; oldingi jadval o‘zgarmadi."
            self._progress(run_id, revision, 100, Stage.STOPPED, message)
            return GenerationResult(run_id, revision, Stage.STOPPED, False, message=message)
        except Exception as error:
            if checkpoint is not None:
                # A post-processing failure must never hide a validated schedule.
                self._validate_complete(checkpoint, total)
                final_diagnostics = {
                    **checkpoint_diagnostics, "finalizer_error": str(error),
                }
                try:
                    terminal_saved = bool(self.persist(
                        run_id=run_id, revision=revision,
                        state=self._snapshot(checkpoint),
                        diagnostics=final_diagnostics, terminal=True,
                    ))
                except Exception as terminal_error:
                    terminal_saved = False
                    final_diagnostics["terminal_persist_error"] = str(terminal_error)
                message = (
                    f"Jadval #{run_id}{'.' + str(revision) if revision else ''} tayyor. "
                    + (
                        "100% saqlangan jadval ochildi; "
                        if terminal_saved else
                        "100% oldingi checkpoint ochildi; "
                    )
                    + "qo‘shimcha yaxshilash yakunlanmadi."
                )
                self._progress(run_id, revision, 100, Stage.READY, message)
                return GenerationResult(
                    run_id, revision, Stage.READY, True, checkpoint,
                    final_diagnostics, message,
                )
            message = f"Jadval yaratilmadi: {str(error)[:700]}"
            self._progress(run_id, revision, 100, Stage.ERROR, message)
            return GenerationResult(
                run_id, revision, Stage.ERROR, False,
                diagnostics={"error": str(error)}, message=message,
            )
