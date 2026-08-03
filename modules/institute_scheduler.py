"""Pure institute schedule conflict helpers.

The PostgreSQL trigger is the concurrency authority.  These functions power
previews and explain conflicts without a database connection.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import Iterable, Literal


ScheduleKind = Literal["weekly", "dated"]


@dataclass(frozen=True, slots=True)
class InstituteSlot:
    slot_id: int | None
    section_id: int
    teacher_user_id: int
    starts_at: time
    ends_at: time
    kind: ScheduleKind
    room_id: int | None = None
    cohort_ids: tuple[int, ...] = ()
    weekday: int | None = None
    lesson_date: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None

    def __post_init__(self) -> None:
        if self.starts_at >= self.ends_at:
            raise ValueError("ends_at must be after starts_at")
        if self.kind == "weekly":
            if self.weekday is None or not 1 <= self.weekday <= 7:
                raise ValueError("weekly slots require weekday 1..7")
            if self.lesson_date is not None:
                raise ValueError("weekly slots cannot have lesson_date")
            if (
                self.effective_from is not None
                and self.effective_to is not None
                and self.effective_to < self.effective_from
            ):
                raise ValueError("effective_to must not precede effective_from")
        elif self.kind == "dated":
            if self.lesson_date is None:
                raise ValueError("dated slots require lesson_date")
            if self.weekday is not None:
                raise ValueError("dated slots cannot have weekday")
        else:
            raise ValueError("unsupported schedule kind")


@dataclass(frozen=True, slots=True)
class ScheduleConflict:
    left_id: int | None
    right_id: int | None
    resource: Literal["teacher", "section", "cohort", "room"]


def _date_ranges_overlap(left: InstituteSlot, right: InstituteSlot) -> bool:
    if left.kind == right.kind == "dated":
        return left.lesson_date == right.lesson_date
    if left.kind == right.kind == "weekly":
        if left.weekday != right.weekday:
            return False
        left_from = left.effective_from or date.min
        left_to = left.effective_to or date.max
        right_from = right.effective_from or date.min
        right_to = right.effective_to or date.max
        return left_from <= right_to and right_from <= left_to
    weekly = left if left.kind == "weekly" else right
    dated = right if left.kind == "weekly" else left
    assert dated.lesson_date is not None and weekly.weekday is not None
    if dated.lesson_date.isoweekday() != weekly.weekday:
        return False
    if weekly.effective_from and dated.lesson_date < weekly.effective_from:
        return False
    if weekly.effective_to and dated.lesson_date > weekly.effective_to:
        return False
    return True


def find_conflicts(slots: Iterable[InstituteSlot]) -> list[ScheduleConflict]:
    ordered = sorted(
        slots,
        key=lambda row: (
            row.lesson_date or row.effective_from or date.min,
            row.weekday or 0,
            row.starts_at,
            row.slot_id or 0,
        ),
    )
    result: list[ScheduleConflict] = []
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            if not _date_ranges_overlap(left, right):
                continue
            if not (left.starts_at < right.ends_at and right.starts_at < left.ends_at):
                continue
            if left.teacher_user_id == right.teacher_user_id:
                result.append(ScheduleConflict(left.slot_id, right.slot_id, "teacher"))
            if left.section_id == right.section_id:
                result.append(ScheduleConflict(left.slot_id, right.slot_id, "section"))
            if set(left.cohort_ids) & set(right.cohort_ids):
                result.append(ScheduleConflict(left.slot_id, right.slot_id, "cohort"))
            if (
                left.room_id is not None
                and right.room_id is not None
                and left.room_id == right.room_id
            ):
                result.append(ScheduleConflict(left.slot_id, right.slot_id, "room"))
    return result


def expand_slots(
    slots: Iterable[InstituteSlot], start: date, end: date
) -> list[tuple[date, InstituteSlot]]:
    if end < start:
        raise ValueError("end must not precede start")
    if (end - start).days > 366:
        raise ValueError("expansion window is limited to 367 days")
    result: list[tuple[date, InstituteSlot]] = []
    for slot in slots:
        if slot.kind == "dated":
            assert slot.lesson_date is not None
            if start <= slot.lesson_date <= end:
                result.append((slot.lesson_date, slot))
            continue
        assert slot.weekday is not None
        lower = max(start, slot.effective_from or start)
        upper = min(end, slot.effective_to or end)
        offset = (slot.weekday - lower.isoweekday()) % 7
        current = lower + timedelta(days=offset)
        while current <= upper:
            result.append((current, slot))
            current += timedelta(days=7)
    return sorted(
        result,
        key=lambda item: (item[0], item[1].starts_at, item[1].section_id),
    )
