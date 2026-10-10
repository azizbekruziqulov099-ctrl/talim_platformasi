"""Deterministic schedule helpers for learning centres.

The database trigger is the final concurrency guard.  These pure functions are
used by previews, tests and clients that need to explain a conflict before a
write is attempted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import Iterable, Literal


ScheduleKind = Literal["weekly", "dated"]


@dataclass(frozen=True, slots=True)
class ScheduleSlot:
    slot_id: int | None
    kind: ScheduleKind
    starts_at: time
    ends_at: time
    teacher_user_id: int
    group_id: int
    room_id: int | None = None
    weekday: int | None = None
    lesson_date: date | None = None

    def __post_init__(self) -> None:
        if self.starts_at >= self.ends_at:
            raise ValueError("ends_at must be after starts_at")
        if self.kind == "weekly":
            if self.weekday is None or not 1 <= self.weekday <= 7:
                raise ValueError("weekly slots require weekday 1..7")
            if self.lesson_date is not None:
                raise ValueError("weekly slots cannot have lesson_date")
        elif self.kind == "dated":
            if self.lesson_date is None:
                raise ValueError("dated slots require lesson_date")
            if self.weekday is not None:
                raise ValueError("dated slots cannot have weekday")
        else:
            raise ValueError("unsupported schedule kind")


@dataclass(frozen=True, slots=True)
class Conflict:
    left_id: int | None
    right_id: int | None
    resource: Literal["teacher", "group", "room"]


def _same_day(left: ScheduleSlot, right: ScheduleSlot) -> bool:
    if left.kind == right.kind == "weekly":
        return left.weekday == right.weekday
    if left.kind == right.kind == "dated":
        return left.lesson_date == right.lesson_date
    weekly = left if left.kind == "weekly" else right
    dated = right if right.kind == "dated" else left
    assert weekly.weekday is not None and dated.lesson_date is not None
    return weekly.weekday == dated.lesson_date.isoweekday()


def _overlaps(left: ScheduleSlot, right: ScheduleSlot) -> bool:
    return left.starts_at < right.ends_at and right.starts_at < left.ends_at


def find_conflicts(slots: Iterable[ScheduleSlot]) -> list[Conflict]:
    """Return stable, de-duplicated teacher/course/room collisions."""

    ordered = sorted(
        slots,
        key=lambda slot: (
            slot.kind,
            slot.lesson_date or date.min,
            slot.weekday or 0,
            slot.starts_at,
            slot.slot_id or 0,
        ),
    )
    conflicts: list[Conflict] = []
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if not _same_day(left, right) or not _overlaps(left, right):
                continue
            if left.teacher_user_id == right.teacher_user_id:
                conflicts.append(Conflict(left.slot_id, right.slot_id, "teacher"))
            if left.group_id == right.group_id:
                conflicts.append(Conflict(left.slot_id, right.slot_id, "group"))
            if (
                left.room_id is not None
                and right.room_id is not None
                and left.room_id == right.room_id
            ):
                conflicts.append(Conflict(left.slot_id, right.slot_id, "room"))
    return conflicts


def expand_weekly_slots(
    slots: Iterable[ScheduleSlot], start: date, end: date
) -> list[tuple[date, ScheduleSlot]]:
    """Expand weekly rows into an inclusive date window.

    Dated rows are returned only when they fall inside the requested window.
    A bounded window prevents accidental unbounded materialisation.
    """

    if end < start:
        raise ValueError("end must not be before start")
    if (end - start).days > 366:
        raise ValueError("schedule expansion is limited to 367 days")
    result: list[tuple[date, ScheduleSlot]] = []
    for slot in slots:
        if slot.kind == "dated":
            assert slot.lesson_date is not None
            if start <= slot.lesson_date <= end:
                result.append((slot.lesson_date, slot))
            continue
        assert slot.weekday is not None
        offset = (slot.weekday - start.isoweekday()) % 7
        current = start + timedelta(days=offset)
        while current <= end:
            result.append((current, slot))
            current += timedelta(days=7)
    return sorted(
        result,
        key=lambda item: (
            item[0],
            item[1].starts_at,
            item[1].group_id,
            item[1].slot_id or 0,
        ),
    )
