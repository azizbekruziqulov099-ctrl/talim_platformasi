"""SamTM V23 timetable policy engine.

This module contains only the small, stable policy contract used by
``samtm_school.py``.  Schedule search and lifecycle live in their own modules.
No database, FastAPI or frontend dependency is imported here.
"""

from __future__ import annotations

from typing import Any, Iterable


ENGINE_RELEASE = "SAMTM-TIMETABLE-ENGINE-V23.5-STRICT"

STRICT = "strict"


def _stage(value: Any) -> str:
    """Only one public generator exists; unknown legacy modes become strict."""

    text = str(value or STRICT).strip().casefold().replace("-", "_")
    aliases = {
        "strict": STRICT,
        "qat_iy": STRICT,
        "qatiy": STRICT,
        "1": STRICT,
        "default": STRICT,
    }
    return aliases.get(text, STRICT)


def _unique_text(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values or ():
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def filter_reasons(reasons: Iterable[Any], stage: Any = STRICT) -> list[str]:
    """Return every rejection reason unchanged in the canonical strict mode.

    Earlier generators removed some reasons in later stages and could silently
    open red/BAND or method-day slots.  V23 has no such relaxation stage.
    """

    _stage(stage)
    return _unique_text(reasons)


def internal_policy(stage: Any = STRICT) -> dict[str, Any]:
    """Machine-readable safety contract for backend diagnostics."""

    return {
        "stage": _stage(stage),
        "hard_rules_relaxed": False,
        "red_band_relaxed": False,
        "method_day_relaxed": False,
        "class_balance_hard": True,
        "minimum_open_day_lessons": 2,
        "partial_schedule_allowed": False,
        "checkpoint_before_improvement": True,
        "fresh_base_run_per_click": True,
    }


def mode_config() -> dict[str, Any]:
    """The one public generator configuration used by SamTM V23."""

    return {
        "id": 1,
        "generator_rejimi": 1,
        "nomi": "Yagona exact generator",
        "izoh": (
            "Avval 100% va kunlari teng jadval yaratiladi, darhol saqlanadi; "
            "keyin o‘qituvchi jadvallari worst-first yaxshilanadi."
        ),
        "policy_stage": STRICT,
        "imbalance_limit": 1,
        "minimum_open_day_lessons": 2,
        "hard_balance_class_days": True,
        "red_band_relaxed": False,
        "method_day_relaxed": False,
        "partial_schedule_allowed": False,
        "revision_history": True,
        "fresh_base_run_per_click": True,
        "stop_returns_last_checkpoint": True,
        "teacher_presence_4_5_max_hours": 8,
        "teacher_presence_6_7_max_hours": 10,
        "teacher_okno_first": True,
        "all_teachers_round_robin": True,
        "dual_shift_teachers_first": True,
        "single_shift_only_when_low_load": True,
        "improvement_time_limit": None,
    }


def public_modes() -> list[dict[str, Any]]:
    """Frontend compatibility: exactly one selectable generator."""

    return [mode_config()]


def stage_label(stage: Any = STRICT) -> str:
    labels = {STRICT: "Qat’iy qoidalar"}
    return labels[_stage(stage)]


__all__ = [
    "ENGINE_RELEASE",
    "STRICT",
    "filter_reasons",
    "internal_policy",
    "mode_config",
    "public_modes",
    "stage_label",
]
