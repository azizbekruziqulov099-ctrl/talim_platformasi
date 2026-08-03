"""Pure, deterministic credit-module grade calculations.

Database writes and authorisation stay in ``institute.py``.  Keeping the
arithmetic here makes rounding and GPA policy independently testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable


TWO_PLACES = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class WeightedMark:
    score: Decimal
    max_score: Decimal
    weight_percent: Decimal

    def __post_init__(self) -> None:
        if self.max_score <= 0:
            raise ValueError("max_score must be positive")
        if self.score < 0 or self.score > self.max_score:
            raise ValueError("score must be between zero and max_score")
        if self.weight_percent <= 0 or self.weight_percent > 100:
            raise ValueError("weight_percent must be in (0, 100]")


@dataclass(frozen=True, slots=True)
class GradeBand:
    minimum_percent: Decimal
    maximum_percent: Decimal
    letter_grade: str
    grade_point: Decimal
    passed: bool

    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.minimum_percent <= self.maximum_percent <= 100):
            raise ValueError("invalid grade band")
        if not self.letter_grade.strip():
            raise ValueError("letter_grade is required")
        if self.grade_point < 0:
            raise ValueError("grade_point cannot be negative")


@dataclass(frozen=True, slots=True)
class CreditResult:
    credits: Decimal
    grade_point: Decimal
    passed: bool = True

    def __post_init__(self) -> None:
        if self.credits <= 0:
            raise ValueError("credits must be positive")
        if self.grade_point < 0:
            raise ValueError("grade_point cannot be negative")


def weighted_percent(marks: Iterable[WeightedMark]) -> Decimal:
    rows = list(marks)
    if not rows:
        raise ValueError("at least one mark is required")
    total_weight = sum((row.weight_percent for row in rows), Decimal("0"))
    if total_weight != Decimal("100"):
        raise ValueError("assessment weights must equal 100")
    result = sum(
        (
            row.score / row.max_score * row.weight_percent
            for row in rows
        ),
        Decimal("0"),
    )
    return result.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def select_grade_band(percent: Decimal, bands: Iterable[GradeBand]) -> GradeBand:
    if percent < 0 or percent > 100:
        raise ValueError("percent must be between zero and 100")
    matches = [
        band
        for band in bands
        if band.minimum_percent <= percent <= band.maximum_percent
    ]
    if len(matches) != 1:
        raise ValueError("grade scale must resolve to exactly one band")
    return matches[0]


def calculate_gpa(results: Iterable[CreditResult]) -> Decimal:
    # Failed final attempts still consume attempted credits and contribute zero
    # grade points. Superseded retakes are filtered by the caller.
    included = list(results)
    if not included:
        return Decimal("0.00")
    credits = sum((row.credits for row in included), Decimal("0"))
    if credits <= 0:
        return Decimal("0.00")
    points = sum(
        (row.credits * row.grade_point for row in included), Decimal("0")
    )
    return (points / credits).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def select_transcript_attempts(
    results: Iterable[dict[str, Any]], policy: str = "latest",
) -> list[dict[str, Any]]:
    """Apply the institution's retake policy once per course.

    ``all`` intentionally preserves every attempt. ``latest`` and ``best``
    return one result per course so credits and GPA cannot be counted twice.
    Unknown policy values fail closed to the documented ``latest`` default.
    """
    rows = [dict(row) for row in results]
    normalized = policy if policy in {"latest", "best", "all"} else "latest"
    if normalized == "all":
        return rows

    selected: dict[int, dict[str, Any]] = {}
    for row in rows:
        course_id = int(row["course_id"])
        if normalized == "best":
            rank = (
                bool(row.get("passed")),
                Decimal(str(row.get("grade_point") or 0)),
                Decimal(str(row.get("final_percent") or 0)),
                str(row.get("finalized_at") or row.get("term_start") or ""),
                int(row.get("id") or 0),
            )
        else:
            rank = (
                str(row.get("finalized_at") or row.get("term_start") or ""),
                int(row.get("id") or 0),
            )
        existing = selected.get(course_id)
        if existing is None:
            selected[course_id] = row
            continue
        if normalized == "best":
            existing_rank = (
                bool(existing.get("passed")),
                Decimal(str(existing.get("grade_point") or 0)),
                Decimal(str(existing.get("final_percent") or 0)),
                str(existing.get("finalized_at") or existing.get("term_start") or ""),
                int(existing.get("id") or 0),
            )
        else:
            existing_rank = (
                str(existing.get("finalized_at") or existing.get("term_start") or ""),
                int(existing.get("id") or 0),
            )
        if rank > existing_rank:
            selected[course_id] = row

    return sorted(
        selected.values(),
        key=lambda row: (
            str(row.get("term_start") or row.get("finalized_at") or ""),
            str(row.get("course_code") or ""),
            int(row.get("id") or 0),
        ),
    )
