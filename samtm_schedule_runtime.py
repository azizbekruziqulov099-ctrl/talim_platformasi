"""SamTM timetable generation lifecycle.

This module owns only the generation state machine.  It deliberately knows
nothing about FastAPI, PostgreSQL or React.  The school adapter supplies the
data, exact solver, validators and persistence callbacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import time
from typing import Any, Callable, Mapping, MutableMapping, Optional, Sequence


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
        return tuple(sorted(
            (int(key[0]), int(key[1]), int(value or 0))
            for key, value in ((state or {}).get("class_daily_total") or {}).items()
            if int(value or 0) > 0
        ))

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
            frozen_class_days = self._class_day_signature(state)
            if not self.persist(
                run_id=run_id, revision=revision, state=state,
                diagnostics=checkpoint_diagnostics, terminal=False,
            ):
                raise GenerationFailed(
                    f"Jadval #{run_id} topildi, ammo bazaga saqlanmadi"
                )
            checkpoint = state
            self._progress(
                run_id, revision, 55, Stage.CHECKPOINT,
                f"Jadval #{run_id} saqlandi: {total}/{total} dars. Uni hozir ochish mumkin.",
            )

            if self._is_cancelled(force=True):
                raise GenerationCancelled()

            improve_deadline = self.clock() + float(self.policy.improve_seconds)

            def accepted(candidate: MutableMapping[str, Any], details: Mapping[str, Any]) -> bool:
                nonlocal revision, checkpoint, checkpoint_diagnostics
                if self._is_cancelled():
                    return False
                self._validate_complete(candidate, total)
                if self._class_day_signature(candidate) != frozen_class_days:
                    # Birinchi jadvaldagi teng kunlik taqsimot (masalan
                    # 6/6/6/6/6 yoki 6/6/6/6/5) mutlaq qotirilgan.
                    # Notekis candidate ko'rsatilmaydi va saqlanmaydi.
                    return False
                next_revision = revision + 1
                next_diagnostics = {
                    **checkpoint_diagnostics,
                    **dict(details or {}),
                    "revision": next_revision,
                }
                if not self.persist(
                    run_id=run_id, revision=next_revision, state=candidate,
                    diagnostics=next_diagnostics, terminal=False,
                ):
                    return False
                revision = next_revision
                checkpoint = candidate
                checkpoint_diagnostics = next_diagnostics
                self._progress(
                    run_id, revision, min(94, 55 + revision), Stage.REVISION,
                    f"Jadval #{run_id}.{revision} saqlandi va ochish mumkin.",
                )
                return True

            self._progress(
                run_id, revision, 60, Stage.IMPROVING,
                f"Jadval #{run_id}: eng yomon o‘qituvchi jadvalidan boshlab qisilyapti.",
            )
            improved = self.improve(
                state=checkpoint,
                context=dict(context),
                deadline=improve_deadline,
                cancel_requested=lambda: self._is_cancelled(),
                accepted=accepted,
                seed=int(seed) ^ 0x5A17,
            )
            if isinstance(improved, MutableMapping):
                self._validate_complete(improved, total)

            if self._is_cancelled(force=True):
                raise GenerationCancelled()

            if checkpoint is None:
                raise GenerationFailed("Saqlangan to‘liq jadval yo‘q")
            if not self.persist(
                run_id=run_id, revision=revision, state=checkpoint,
                diagnostics=checkpoint_diagnostics, terminal=True,
            ):
                raise GenerationFailed("Yakuniy jadvalni belgilashda xato")
            message = (
                f"Jadval #{run_id}{'.' + str(revision) if revision else ''} tayyor: "
                f"{total}/{total} dars joylashdi va ochildi."
            )
            self._progress(run_id, revision, 100, Stage.READY, message)
            return GenerationResult(
                run_id, revision, Stage.READY, True, checkpoint,
                checkpoint_diagnostics, message,
            )
        except GenerationCancelled:
            if checkpoint is not None:
                self.persist(
                    run_id=run_id, revision=revision, state=checkpoint,
                    diagnostics=checkpoint_diagnostics, terminal=True,
                )
                message = (
                    f"To‘xtatildi. Eng yaxshi Jadval #{run_id}"
                    f"{'.' + str(revision) if revision else ''} saqlandi va ochildi."
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
                self.persist(
                    run_id=run_id, revision=revision, state=checkpoint,
                    diagnostics={**checkpoint_diagnostics, "finalizer_error": str(error)},
                    terminal=True,
                )
                message = (
                    f"Jadval #{run_id}{'.' + str(revision) if revision else ''} tayyor. "
                    "100% saqlangan jadval ochildi; qo‘shimcha yaxshilash yakunlanmadi."
                )
                self._progress(run_id, revision, 100, Stage.READY, message)
                return GenerationResult(
                    run_id, revision, Stage.READY, True, checkpoint,
                    {**checkpoint_diagnostics, "finalizer_error": str(error)}, message,
                )
            message = f"Jadval yaratilmadi: {str(error)[:700]}"
            self._progress(run_id, revision, 100, Stage.ERROR, message)
            return GenerationResult(
                run_id, revision, Stage.ERROR, False,
                diagnostics={"error": str(error)}, message=message,
            )
