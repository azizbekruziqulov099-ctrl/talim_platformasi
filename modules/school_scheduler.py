"""Deterministic school timetable and calendar make-up engine.

The module is deliberately independent from FastAPI and PostgreSQL.  It can be
used by an API route, a background worker or a command-line validation tool.
All inputs and outputs are immutable dataclasses, so a request can be logged and
replayed exactly.

Hard constraints are never weakened automatically:

* a class, teacher or room cannot occupy the same shift slot twice;
* a class is scheduled only inside its configured shift;
* teacher availability, method days and the daily 6/7 lesson cap are honoured;
* room and subject shift restrictions are honoured;
* a configured class hour is pinned to its requested day and period.

If a hard constraint cannot be satisfied, the missing lesson is returned in
``ScheduleResult.hard_conflicts``.  Softer preferences (early/late subjects,
compact teacher days and spreading a subject over the week) are optimized and
reported as quality warnings when they cannot be met.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Literal, Mapping, Sequence


PreferredBand = Literal["early", "late", "any"]
AssignmentSource = Literal["regular", "class_hour"]
MakeupMode = Literal["extra_period", "compressed"]

DEFAULT_TEACHER_DAILY_MAX = 6
ABSOLUTE_TEACHER_DAILY_MAX = 7
DEFAULT_EXACT_SEARCH_MAX_UNITS = 40
MAX_EXACT_SEARCH_UNITS = 60
DEFAULT_MAX_SEARCH_NODES = 10_000
MAX_SEARCH_NODES = 20_000
MAX_WEEKLY_HOURS_PER_DEMAND = 40
# This is a bounded-work estimate, not a student/lesson count promise.  Large
# schools can generate selected sections in batches; a request is rejected only
# when its estimated candidate evaluations would monopolise one API worker.
MAX_CANDIDATE_EVALUATIONS = 5_000_000
MINUTES_PER_DAY = 24 * 60
CANONICAL_WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


@dataclass(frozen=True, order=True)
class Slot:
    """A weekly slot.

    Period numbers are local to a shift.  Therefore morning period 1 and
    afternoon period 1 are distinct physical time slots.
    """

    day: str
    shift_id: str
    period: int


@dataclass(frozen=True)
class Shift:
    id: str
    periods: tuple[int, ...]
    # Optional minute-of-day intervals, for example
    # ``{1: (480, 525), 2: (530, 575)}``.  If any shift supplies real clock
    # times, every shift in the request must supply them.  This lets the
    # collision engine catch overlapping custom/private-school shifts.
    period_times: Mapping[int, tuple[int, int]] | None = None


@dataclass(frozen=True)
class Teacher:
    id: str
    method_days: frozenset[str] = frozenset()
    available_slots: frozenset[Slot] | None = None
    max_daily_lessons: int = DEFAULT_TEACHER_DAILY_MAX
    preferred_slots: frozenset[Slot] = frozenset()
    preferred_shift: str | None = None
    avoid_first_period: bool = False


@dataclass(frozen=True)
class Room:
    id: str
    allowed_shift_ids: frozenset[str] | None = None
    allowed_subjects: frozenset[str] | None = None


@dataclass(frozen=True)
class ClassHourRule:
    """Pinned weekly class-hour configuration for one class."""

    day: str
    period: int
    teacher_id: str | None = None
    room_id: str | None = None
    subject: str = "Sinf soati"


@dataclass(frozen=True)
class ClassHourPolicy:
    """Institution policy for configured class-hour rules.

    Public-school requests use the Friday/first-period default.  Institutions
    with another approved policy can replace it explicitly.  The policy only
    validates classes that have ``SchoolClass.class_hour`` configured unless
    ``required_for_all_classes`` is true.
    """

    day: str = "Friday"
    period: int = 1
    required_for_all_classes: bool = False


@dataclass(frozen=True)
class SchoolClass:
    id: str
    shift_id: str
    home_room_id: str | None = None
    class_teacher_id: str | None = None
    class_hour: ClassHourRule | None = None


@dataclass(frozen=True)
class LessonDemand:
    """One subject's weekly requirement for one class."""

    id: str
    class_id: str
    subject: str
    teacher_id: str
    weekly_hours: int
    room_ids: tuple[str, ...] = ()
    allowed_shift_ids: frozenset[str] | None = None
    preferred_band: PreferredBand | None = None
    max_per_day: int | None = None


@dataclass(frozen=True)
class SubjectPreference:
    subject: str
    preferred_band: PreferredBand


@dataclass(frozen=True)
class TimetableRequest:
    days: tuple[str, ...]
    shifts: tuple[Shift, ...]
    classes: tuple[SchoolClass, ...]
    teachers: tuple[Teacher, ...]
    rooms: tuple[Room, ...]
    demands: tuple[LessonDemand, ...]
    subject_preferences: tuple[SubjectPreference, ...] = ()
    exact_search_max_units: int = DEFAULT_EXACT_SEARCH_MAX_UNITS
    max_search_nodes: int = DEFAULT_MAX_SEARCH_NODES
    class_hour_policy: ClassHourPolicy | None = field(
        default_factory=ClassHourPolicy
    )


@dataclass(frozen=True)
class Assignment:
    day: str
    shift_id: str
    period: int
    class_id: str
    subject: str
    teacher_id: str
    room_id: str | None
    source: AssignmentSource = "regular"
    demand_id: str | None = None
    occurrence_index: int = 1

    @property
    def slot(self) -> Slot:
        return Slot(self.day, self.shift_id, self.period)


@dataclass(frozen=True)
class HardConflict:
    code: str
    message: str
    entity_type: str | None = None
    entity_id: str | None = None
    missing_hours: int = 0
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class QualityWarning:
    code: str
    message: str
    entity_type: str | None = None
    entity_id: str | None = None
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ScheduleResult:
    assignments: tuple[Assignment, ...]
    hard_conflicts: tuple[HardConflict, ...]
    quality_warnings: tuple[QualityWarning, ...]
    search_nodes: int

    @property
    def complete(self) -> bool:
        return not self.hard_conflicts


@dataclass(frozen=True)
class _Unit:
    demand: LessonDemand
    occurrence_index: int


def _slot_interval(
    shifts: Mapping[str, Shift],
    slot: Slot,
) -> tuple[int, int] | None:
    shift = shifts.get(slot.shift_id)
    if shift is None or shift.period_times is None:
        return None
    return shift.period_times.get(slot.period)


def _slots_overlap(
    left: Slot,
    right: Slot,
    shifts: Mapping[str, Shift],
) -> bool:
    if left.day != right.day:
        return False
    if left == right:
        return True
    left_interval = _slot_interval(shifts, left)
    right_interval = _slot_interval(shifts, right)
    if left_interval is None or right_interval is None:
        return False
    return (
        left_interval[0] < right_interval[1]
        and right_interval[0] < left_interval[1]
    )


class _State:
    def __init__(
        self,
        assignments: Iterable[Assignment] = (),
        *,
        shifts: Mapping[str, Shift] | None = None,
    ) -> None:
        self.shifts = dict(shifts or {})
        self.assignments: list[Assignment] = []
        self.class_slots: set[tuple[str, Slot]] = set()
        self.teacher_slots: set[tuple[str, Slot]] = set()
        self.room_slots: set[tuple[str, Slot]] = set()
        self.class_intervals: dict[
            tuple[str, str], list[tuple[int, int, Slot]]
        ] = {}
        self.teacher_intervals: dict[
            tuple[str, str], list[tuple[int, int, Slot]]
        ] = {}
        self.room_intervals: dict[
            tuple[str, str], list[tuple[int, int, Slot]]
        ] = {}
        self.teacher_daily: dict[tuple[str, str], int] = {}
        self.class_daily: dict[tuple[str, str], int] = {}
        self.subject_daily: dict[tuple[str, str, str], int] = {}
        self.teacher_shift_periods: dict[tuple[str, str, str], list[int]] = {}
        for assignment in assignments:
            self.add(assignment)

    def _busy(
        self,
        exact_claims: set[tuple[str, Slot]],
        interval_claims: Mapping[
            tuple[str, str], Sequence[tuple[int, int, Slot]]
        ],
        entity_id: str,
        slot: Slot,
    ) -> bool:
        if (entity_id, slot) in exact_claims:
            return True
        interval = _slot_interval(self.shifts, slot)
        if interval is None:
            return False
        return any(
            interval[0] < end and start < interval[1]
            for start, end, _ in interval_claims.get(
                (entity_id, slot.day), ()
            )
        )

    def class_busy(self, class_id: str, slot: Slot) -> bool:
        return self._busy(
            self.class_slots,
            self.class_intervals,
            class_id,
            slot,
        )

    def teacher_busy(self, teacher_id: str, slot: Slot) -> bool:
        return self._busy(
            self.teacher_slots,
            self.teacher_intervals,
            teacher_id,
            slot,
        )

    def room_busy(self, room_id: str, slot: Slot) -> bool:
        return self._busy(
            self.room_slots,
            self.room_intervals,
            room_id,
            slot,
        )

    def _add_interval(
        self,
        mapping: dict[tuple[str, str], list[tuple[int, int, Slot]]],
        entity_id: str,
        slot: Slot,
    ) -> None:
        interval = _slot_interval(self.shifts, slot)
        if interval is not None:
            mapping.setdefault((entity_id, slot.day), []).append(
                (interval[0], interval[1], slot)
            )

    def _remove_interval(
        self,
        mapping: dict[tuple[str, str], list[tuple[int, int, Slot]]],
        entity_id: str,
        slot: Slot,
    ) -> None:
        interval = _slot_interval(self.shifts, slot)
        if interval is None:
            return
        key = (entity_id, slot.day)
        values = mapping[key]
        values.remove((interval[0], interval[1], slot))
        if not values:
            del mapping[key]

    def add(self, assignment: Assignment) -> None:
        slot = assignment.slot
        self.assignments.append(assignment)
        self.class_slots.add((assignment.class_id, slot))
        self.teacher_slots.add((assignment.teacher_id, slot))
        self._add_interval(self.class_intervals, assignment.class_id, slot)
        self._add_interval(self.teacher_intervals, assignment.teacher_id, slot)
        if assignment.room_id is not None:
            self.room_slots.add((assignment.room_id, slot))
            self._add_interval(self.room_intervals, assignment.room_id, slot)
        _bump(self.teacher_daily, (assignment.teacher_id, assignment.day), 1)
        _bump(self.class_daily, (assignment.class_id, assignment.day), 1)
        _bump(
            self.subject_daily,
            (assignment.class_id, assignment.subject, assignment.day),
            1,
        )
        periods = self.teacher_shift_periods.setdefault(
            (assignment.teacher_id, assignment.day, assignment.shift_id), []
        )
        periods.append(assignment.period)
        periods.sort()

    def remove(self, assignment: Assignment) -> None:
        slot = assignment.slot
        removed = self.assignments.pop()
        if removed != assignment:
            raise RuntimeError("Assignments must be removed in reverse order")
        self.class_slots.remove((assignment.class_id, slot))
        self.teacher_slots.remove((assignment.teacher_id, slot))
        self._remove_interval(
            self.class_intervals, assignment.class_id, slot
        )
        self._remove_interval(
            self.teacher_intervals, assignment.teacher_id, slot
        )
        if assignment.room_id is not None:
            self.room_slots.remove((assignment.room_id, slot))
            self._remove_interval(
                self.room_intervals, assignment.room_id, slot
            )
        _bump(self.teacher_daily, (assignment.teacher_id, assignment.day), -1)
        _bump(self.class_daily, (assignment.class_id, assignment.day), -1)
        _bump(
            self.subject_daily,
            (assignment.class_id, assignment.subject, assignment.day),
            -1,
        )
        key = (assignment.teacher_id, assignment.day, assignment.shift_id)
        periods = self.teacher_shift_periods[key]
        periods.remove(assignment.period)
        if not periods:
            del self.teacher_shift_periods[key]


def _bump(mapping: dict[object, int], key: object, delta: int) -> None:
    value = mapping.get(key, 0) + delta
    if value:
        mapping[key] = value
    else:
        mapping.pop(key, None)


def _duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _index(items: Sequence[object]) -> dict[str, object]:
    return {getattr(item, "id"): item for item in items}


def _is_nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _shift_validation_conflicts(
    shifts: Sequence[Shift],
    *,
    entity_scope: str = "request",
) -> list[HardConflict]:
    conflicts: list[HardConflict] = []
    timed_count = sum(shift.period_times is not None for shift in shifts)
    if timed_count not in (0, len(shifts)):
        conflicts.append(
            HardConflict(
                "incomplete_shift_clock_times",
                (
                    "Haqiqiy vaqt ishlatilsa barcha smenalarning har bir "
                    "dars vaqti kiritilishi kerak."
                ),
                entity_scope,
            )
        )

    for shift in shifts:
        if not _is_nonempty_text(shift.id):
            conflicts.append(
                HardConflict(
                    "invalid_shift_id",
                    "Smena identifikatori bo'sh bo'lishi mumkin emas.",
                    "shift",
                    str(shift.id),
                )
            )
        if not shift.periods:
            conflicts.append(
                HardConflict(
                    "shift_has_no_periods",
                    f"{shift.id} smenada dars soatlari yo'q.",
                    "shift",
                    shift.id,
                )
            )
        if any(
            isinstance(period, bool)
            or not isinstance(period, int)
            or period < 1
            for period in shift.periods
        ):
            conflicts.append(
                HardConflict(
                    "invalid_period",
                    f"{shift.id} smenada dars raqami musbat butun son emas.",
                    "shift",
                    shift.id,
                )
            )
        if len(shift.periods) != len(set(shift.periods)):
            conflicts.append(
                HardConflict(
                    "duplicate_period",
                    f"{shift.id} smenada dars raqami takrorlangan.",
                    "shift",
                    shift.id,
                )
            )
        if tuple(sorted(shift.periods)) != shift.periods:
            conflicts.append(
                HardConflict(
                    "unsorted_periods",
                    f"{shift.id} smena darslari o'sish tartibida emas.",
                    "shift",
                    shift.id,
                )
            )

        if shift.period_times is None:
            continue
        if set(shift.period_times) != set(shift.periods):
            conflicts.append(
                HardConflict(
                    "incomplete_period_clock_times",
                    f"{shift.id} smenada barcha darslarning vaqti yo'q.",
                    "shift",
                    shift.id,
                )
            )
            continue
        valid_intervals: list[tuple[int, int, int]] = []
        for period in shift.periods:
            interval = shift.period_times.get(period)
            if (
                not isinstance(interval, tuple)
                or len(interval) != 2
                or any(
                    isinstance(value, bool) or not isinstance(value, int)
                    for value in interval
                )
                or not (0 <= interval[0] < interval[1] <= MINUTES_PER_DAY)
            ):
                conflicts.append(
                    HardConflict(
                        "invalid_period_clock_time",
                        f"{shift.id}/{period} dars vaqt oralig'i noto'g'ri.",
                        "shift",
                        shift.id,
                        details={"period": period, "interval": interval},
                    )
                )
                continue
            valid_intervals.append((interval[0], interval[1], period))
        valid_intervals.sort()
        for left, right in zip(valid_intervals, valid_intervals[1:]):
            if left[1] > right[0]:
                conflicts.append(
                    HardConflict(
                        "overlapping_periods_within_shift",
                        f"{shift.id} smenada dars vaqtlari ustma-ust tushgan.",
                        "shift",
                        shift.id,
                        details={"periods": (left[2], right[2])},
                    )
                )
    return conflicts


def _structural_conflicts(request: TimetableRequest) -> list[HardConflict]:
    conflicts: list[HardConflict] = []

    if not request.days:
        conflicts.append(
            HardConflict("no_days", "Hafta kunlari kiritilmagan.", "request")
        )
    invalid_days = [day for day in request.days if not _is_nonempty_text(day)]
    if invalid_days:
        conflicts.append(
            HardConflict(
                "invalid_day",
                "Hafta kuni bo'sh matn bo'lishi mumkin emas.",
                "request",
            )
        )
    for day in sorted(_duplicates(day for day in request.days if isinstance(day, str))):
        conflicts.append(
            HardConflict(
                "duplicate_day",
                f"Hafta kuni takrorlangan: {day}.",
                "day",
                day,
            )
        )

    collections = (
        ("shift", request.shifts),
        ("class", request.classes),
        ("teacher", request.teachers),
        ("room", request.rooms),
        ("demand", request.demands),
    )
    for entity_type, items in collections:
        invalid_ids = [
            getattr(item, "id", None)
            for item in items
            if not _is_nonempty_text(getattr(item, "id", None))
        ]
        if invalid_ids:
            conflicts.append(
                HardConflict(
                    f"invalid_{entity_type}_id",
                    f"{entity_type} identifikatori bo'sh bo'lishi mumkin emas.",
                    entity_type,
                )
            )
        for duplicate in sorted(
            _duplicates(
                getattr(item, "id")
                for item in items
                if isinstance(getattr(item, "id", None), str)
            )
        ):
            conflicts.append(
                HardConflict(
                    f"duplicate_{entity_type}",
                    f"{entity_type} identifikatori takrorlangan: {duplicate}.",
                    entity_type,
                    duplicate,
                )
            )

    shifts = _index(request.shifts)
    classes = _index(request.classes)
    teachers = _index(request.teachers)
    rooms = _index(request.rooms)

    conflicts.extend(_shift_validation_conflicts(request.shifts))

    for teacher in request.teachers:
        if (
            isinstance(teacher.max_daily_lessons, bool)
            or not isinstance(teacher.max_daily_lessons, int)
            or not 1
            <= teacher.max_daily_lessons
            <= ABSOLUTE_TEACHER_DAILY_MAX
        ):
            conflicts.append(
                HardConflict(
                    "invalid_teacher_daily_max",
                    (
                        f"{teacher.id} uchun kunlik limit 1–"
                        f"{ABSOLUTE_TEACHER_DAILY_MAX} oralig'ida bo'lishi kerak."
                    ),
                    "teacher",
                    teacher.id,
                    details={"configured": teacher.max_daily_lessons},
                )
            )
        unknown_method_days = set(teacher.method_days) - set(request.days)
        if unknown_method_days:
            conflicts.append(
                HardConflict(
                    "teacher_unknown_method_day",
                    f"{teacher.id} uchun noma'lum metod kuni kiritilgan.",
                    "teacher",
                    teacher.id,
                    details={"days": tuple(sorted(unknown_method_days))},
                )
            )
        if teacher.available_slots is not None:
            for slot in sorted(teacher.available_slots):
                shift = shifts.get(slot.shift_id)
                if (
                    slot.day not in request.days
                    or shift is None
                    or slot.period not in shift.periods
                ):
                    conflicts.append(
                        HardConflict(
                            "invalid_teacher_availability_slot",
                            f"{teacher.id} uchun noma'lum bo'sh vaqt kiritilgan.",
                            "teacher",
                            teacher.id,
                            details={
                                "day": slot.day,
                                "shift_id": slot.shift_id,
                                "period": slot.period,
                            },
                        )
                    )
        if teacher.preferred_shift is not None and teacher.preferred_shift not in shifts:
            conflicts.append(
                HardConflict(
                    "teacher_unknown_preferred_shift",
                    f"{teacher.id} uchun afzal smena topilmadi.",
                    "teacher",
                    teacher.id,
                    details={"shift_id": teacher.preferred_shift},
                )
            )
        for slot in sorted(teacher.preferred_slots):
            shift = shifts.get(slot.shift_id)
            if (
                slot.day not in request.days
                or shift is None
                or slot.period not in shift.periods
            ):
                conflicts.append(
                    HardConflict(
                        "invalid_teacher_preferred_slot",
                        f"{teacher.id} uchun noma'lum afzal vaqt kiritilgan.",
                        "teacher",
                        teacher.id,
                    )
                )

    for room in request.rooms:
        if room.allowed_shift_ids is not None:
            unknown = room.allowed_shift_ids - set(shifts)
            if unknown:
                conflicts.append(
                    HardConflict(
                        "room_unknown_shift",
                        f"{room.id} xonasi noma'lum smenaga bog'langan.",
                        "room",
                        room.id,
                        details={"shift_ids": tuple(sorted(unknown))},
                    )
                )

    policy = request.class_hour_policy
    if policy is not None and (
        not _is_nonempty_text(policy.day)
        or isinstance(policy.period, bool)
        or not isinstance(policy.period, int)
        or policy.period < 1
    ):
        conflicts.append(
            HardConflict(
                "invalid_class_hour_policy",
                "Sinf soati siyosatining kuni yoki dars raqami noto'g'ri.",
                "request",
            )
        )

    for school_class in request.classes:
        shift = shifts.get(school_class.shift_id)
        if shift is None:
            conflicts.append(
                HardConflict(
                    "class_unknown_shift",
                    f"{school_class.id} sinfi noma'lum smenaga bog'langan.",
                    "class",
                    school_class.id,
                )
            )
            continue
        if (
            school_class.home_room_id is not None
            and school_class.home_room_id not in rooms
        ):
            conflicts.append(
                HardConflict(
                    "class_unknown_home_room",
                    f"{school_class.id} sinfining xonasi topilmadi.",
                    "class",
                    school_class.id,
                )
            )
        if (
            school_class.class_teacher_id is not None
            and school_class.class_teacher_id not in teachers
        ):
            conflicts.append(
                HardConflict(
                    "class_unknown_teacher",
                    f"{school_class.id} sinf rahbari topilmadi.",
                    "class",
                    school_class.id,
                )
            )
        rule = school_class.class_hour
        if rule is None:
            if policy is not None and policy.required_for_all_classes:
                conflicts.append(
                    HardConflict(
                        "class_hour_required",
                        f"{school_class.id} sinfi uchun sinf soati belgilanmagan.",
                        "class",
                        school_class.id,
                        missing_hours=1,
                    )
                )
            continue
        if not _is_nonempty_text(rule.subject):
            conflicts.append(
                HardConflict(
                    "class_hour_empty_subject",
                    f"{school_class.id} sinf soati nomi bo'sh.",
                    "class",
                    school_class.id,
                )
            )
        if policy is not None and (
            rule.day != policy.day or rule.period != policy.period
        ):
            conflicts.append(
                HardConflict(
                    "class_hour_policy_mismatch",
                    (
                        f"{school_class.id} sinf soati {policy.day} kuni "
                        f"{policy.period}-darsda bo'lishi kerak."
                    ),
                    "class",
                    school_class.id,
                    missing_hours=1,
                    details={
                        "configured_day": rule.day,
                        "configured_period": rule.period,
                        "policy_day": policy.day,
                        "policy_period": policy.period,
                    },
                )
            )
        teacher_id = rule.teacher_id or school_class.class_teacher_id
        if rule.day not in request.days:
            conflicts.append(
                HardConflict(
                    "class_hour_unknown_day",
                    f"{school_class.id} sinf soati kuni jadvalda yo'q.",
                    "class",
                    school_class.id,
                )
            )
        if rule.period not in shift.periods:
            conflicts.append(
                HardConflict(
                    "class_hour_outside_shift",
                    f"{school_class.id} sinf soati smena vaqtidan tashqarida.",
                    "class",
                    school_class.id,
                )
            )
        if teacher_id is None or teacher_id not in teachers:
            conflicts.append(
                HardConflict(
                    "class_hour_unknown_teacher",
                    f"{school_class.id} sinf soati uchun rahbar topilmadi.",
                    "class",
                    school_class.id,
                )
            )
        if rule.room_id is not None and rule.room_id not in rooms:
            conflicts.append(
                HardConflict(
                    "class_hour_unknown_room",
                    f"{school_class.id} sinf soati xonasi topilmadi.",
                    "class",
                    school_class.id,
                )
            )

    valid_bands = {"early", "late", "any"}
    for preference in request.subject_preferences:
        if preference.preferred_band not in valid_bands:
            conflicts.append(
                HardConflict(
                    "invalid_subject_band",
                    f"{preference.subject} uchun vaqt oralig'i noto'g'ri.",
                    "subject",
                    preference.subject,
                )
            )

    for demand in request.demands:
        school_class = classes.get(demand.class_id)
        teacher = teachers.get(demand.teacher_id)
        if not _is_nonempty_text(demand.subject):
            conflicts.append(
                HardConflict(
                    "demand_empty_subject",
                    f"{demand.id} talabi uchun fan nomi bo'sh.",
                    "demand",
                    demand.id,
                )
            )
        if school_class is None:
            conflicts.append(
                HardConflict(
                    "demand_unknown_class",
                    f"{demand.id} talabi uchun sinf topilmadi.",
                    "demand",
                    demand.id,
                )
            )
        if teacher is None:
            conflicts.append(
                HardConflict(
                    "demand_unknown_teacher",
                    f"{demand.id} talabi uchun o'qituvchi topilmadi.",
                    "demand",
                    demand.id,
                )
            )
        if (
            isinstance(demand.weekly_hours, bool)
            or not isinstance(demand.weekly_hours, int)
        ):
            conflicts.append(
                HardConflict(
                    "invalid_weekly_hours_type",
                    f"{demand.id} haftalik soati butun son bo'lishi kerak.",
                    "demand",
                    demand.id,
                )
            )
        elif demand.weekly_hours < 0:
            conflicts.append(
                HardConflict(
                    "negative_weekly_hours",
                    f"{demand.id} haftalik soati manfiy bo'lishi mumkin emas.",
                    "demand",
                    demand.id,
                )
            )
        elif demand.weekly_hours > MAX_WEEKLY_HOURS_PER_DEMAND:
            conflicts.append(
                HardConflict(
                    "weekly_hours_limit_exceeded",
                    (
                        f"{demand.id} haftalik soati xavfsiz server "
                        f"chegarasidan ({MAX_WEEKLY_HOURS_PER_DEMAND}) oshgan."
                    ),
                    "demand",
                    demand.id,
                    details={"configured": demand.weekly_hours},
                )
            )
        elif school_class is not None:
            class_shift = shifts.get(school_class.shift_id)
            if class_shift is not None:
                capacity = len(request.days) * len(class_shift.periods)
                if demand.max_per_day is not None and isinstance(
                    demand.max_per_day, int
                ):
                    capacity = min(
                        capacity,
                        len(request.days) * max(0, demand.max_per_day),
                    )
                if demand.weekly_hours > capacity:
                    conflicts.append(
                        HardConflict(
                            "weekly_hours_exceed_capacity",
                            (
                                f"{demand.id} haftalik soati mavjud "
                                "smena sig'imidan oshgan."
                            ),
                            "demand",
                            demand.id,
                            missing_hours=demand.weekly_hours - capacity,
                            details={"capacity": capacity},
                        )
                    )
        if demand.max_per_day is not None and (
            isinstance(demand.max_per_day, bool)
            or not isinstance(demand.max_per_day, int)
            or demand.max_per_day < 1
        ):
            conflicts.append(
                HardConflict(
                    "invalid_subject_daily_max",
                    f"{demand.id} kunlik fan limiti kamida 1 bo'lishi kerak.",
                    "demand",
                    demand.id,
                )
            )
        unknown_rooms = set(demand.room_ids) - set(rooms)
        if unknown_rooms:
            conflicts.append(
                HardConflict(
                    "demand_unknown_room",
                    f"{demand.id} uchun noma'lum xona ko'rsatilgan.",
                    "demand",
                    demand.id,
                    details={"room_ids": tuple(sorted(unknown_rooms))},
                )
            )
        if demand.allowed_shift_ids is not None:
            unknown_shifts = demand.allowed_shift_ids - set(shifts)
            if unknown_shifts:
                conflicts.append(
                    HardConflict(
                        "demand_unknown_shift",
                        f"{demand.id} noma'lum smenaga ruxsat bergan.",
                        "demand",
                        demand.id,
                        details={"shift_ids": tuple(sorted(unknown_shifts))},
                    )
                )
            if (
                school_class is not None
                and school_class.shift_id not in demand.allowed_shift_ids
            ):
                conflicts.append(
                    HardConflict(
                        "subject_not_allowed_in_class_shift",
                        (
                            f"{demand.subject} fani {school_class.id} sinfining "
                            "smenasida o'tkazilmaydi."
                        ),
                        "demand",
                        demand.id,
                        missing_hours=max(0, demand.weekly_hours),
                    )
                )
        if demand.preferred_band not in valid_bands | {None}:
            conflicts.append(
                HardConflict(
                    "invalid_demand_band",
                    f"{demand.id} uchun vaqt oralig'i noto'g'ri.",
                    "demand",
                    demand.id,
                )
            )

    estimated_candidate_evaluations = 0
    for demand in request.demands:
        if (
            not isinstance(demand.weekly_hours, int)
            or isinstance(demand.weekly_hours, bool)
            or demand.weekly_hours <= 0
        ):
            continue
        school_class = classes.get(demand.class_id)
        shift = shifts.get(school_class.shift_id) if school_class else None
        period_count = len(shift.periods) if shift else 0
        room_count = (
            len(demand.room_ids)
            if demand.room_ids
            else max(1, len(request.rooms))
        )
        estimated_candidate_evaluations += (
            demand.weekly_hours
            * len(request.days)
            * period_count
            * room_count
        )
    if estimated_candidate_evaluations > MAX_CANDIDATE_EVALUATIONS:
        conflicts.append(
            HardConflict(
                "workspace_generation_capacity_exceeded",
                (
                    "Tanlangan sinflar uchun bitta jadval qidiruvi API ishchisi "
                    "uchun juda katta. section_ids orqali sinflarni bosqichma-"
                    "bosqich yarating."
                ),
                "request",
                details={
                    "estimated_candidate_evaluations": (
                        estimated_candidate_evaluations
                    ),
                    "max_candidate_evaluations": MAX_CANDIDATE_EVALUATIONS,
                },
            )
        )

    if (
        isinstance(request.exact_search_max_units, bool)
        or not isinstance(request.exact_search_max_units, int)
        or not 0
        <= request.exact_search_max_units
        <= MAX_EXACT_SEARCH_UNITS
    ):
        conflicts.append(
            HardConflict(
                "invalid_exact_search_limit",
                (
                    "Aniq qidiruv chegarasi 0–"
                    f"{MAX_EXACT_SEARCH_UNITS} oralig'ida bo'lishi kerak."
                ),
                "request",
            )
        )
    if (
        isinstance(request.max_search_nodes, bool)
        or not isinstance(request.max_search_nodes, int)
        or not 1 <= request.max_search_nodes <= MAX_SEARCH_NODES
    ):
        conflicts.append(
            HardConflict(
                "invalid_search_node_limit",
                (
                    "Qidiruv qadamlari chegarasi 1–"
                    f"{MAX_SEARCH_NODES} oralig'ida bo'lishi kerak."
                ),
                "request",
            )
        )
    return conflicts


def _teacher_available(teacher: Teacher, slot: Slot) -> bool:
    if slot.day in teacher.method_days:
        return False
    return teacher.available_slots is None or slot in teacher.available_slots


def _room_compatible(
    room: Room,
    shift_id: str,
    subject: str,
) -> bool:
    return (
        (room.allowed_shift_ids is None or shift_id in room.allowed_shift_ids)
        and (room.allowed_subjects is None or subject in room.allowed_subjects)
    )


def _room_candidates(
    demand: LessonDemand,
    school_class: SchoolClass,
    rooms: Mapping[str, Room],
) -> tuple[str | None, ...]:
    if not rooms:
        return (None,)

    ordered: list[str] = []
    if demand.room_ids:
        ordered.extend(demand.room_ids)
    else:
        if school_class.home_room_id is not None:
            ordered.append(school_class.home_room_id)
        ordered.extend(sorted(rooms))

    result: list[str] = []
    for room_id in ordered:
        if room_id in result:
            continue
        room = rooms.get(room_id)
        if room is not None and _room_compatible(
            room, school_class.shift_id, demand.subject
        ):
            result.append(room_id)
    return tuple(result)


def _preferred_band(
    demand: LessonDemand,
    preferences: Mapping[str, PreferredBand],
) -> PreferredBand:
    return demand.preferred_band or preferences.get(demand.subject, "any")


def _period_is_preferred(
    periods: tuple[int, ...],
    period: int,
    band: PreferredBand,
) -> bool:
    if band == "any":
        return True
    midpoint = (len(periods) + 1) // 2
    index = periods.index(period)
    if band == "early":
        return index < midpoint
    return index >= len(periods) // 2


def _gap_count(period_positions: list[int]) -> int:
    if len(period_positions) < 2:
        return 0
    unique = sorted(set(period_positions))
    return sum(
        max(0, right - left - 1)
        for left, right in zip(unique, unique[1:])
    )


def _candidate_options(
    unit: _Unit,
    request: TimetableRequest,
    state: _State,
    *,
    classes: Mapping[str, SchoolClass],
    teachers: Mapping[str, Teacher],
    rooms: Mapping[str, Room],
    shifts: Mapping[str, Shift],
    preferences: Mapping[str, PreferredBand],
) -> list[tuple[tuple[int, ...], Assignment]]:
    demand = unit.demand
    school_class = classes[demand.class_id]
    teacher = teachers[demand.teacher_id]
    shift = shifts[school_class.shift_id]
    room_ids = _room_candidates(demand, school_class, rooms)
    if not room_ids:
        return []

    day_index = {day: index for index, day in enumerate(request.days)}
    period_index = {period: index for index, period in enumerate(shift.periods)}
    band = _preferred_band(demand, preferences)
    options: list[tuple[tuple[int, ...], Assignment]] = []

    for day in request.days:
        if (
            demand.max_per_day is not None
            and state.subject_daily.get(
                (school_class.id, demand.subject, day), 0
            )
            >= demand.max_per_day
        ):
            continue
        if state.teacher_daily.get((teacher.id, day), 0) >= teacher.max_daily_lessons:
            continue

        for period in shift.periods:
            slot = Slot(day, shift.id, period)
            if not _teacher_available(teacher, slot):
                continue
            if state.class_busy(school_class.id, slot):
                continue
            if state.teacher_busy(teacher.id, slot):
                continue

            for room_rank, room_id in enumerate(room_ids):
                if room_id is not None and state.room_busy(room_id, slot):
                    continue

                existing_periods = state.teacher_shift_periods.get(
                    (teacher.id, day, shift.id), []
                )
                existing_positions = [
                    period_index[value]
                    for value in existing_periods
                    if value in period_index
                ]
                new_position = period_index[period]
                before_gaps = _gap_count(existing_positions)
                after_gaps = _gap_count(existing_positions + [new_position])
                adjacent = any(
                    abs(new_position - existing) == 1
                    for existing in existing_positions
                )
                band_penalty = (
                    0
                    if _period_is_preferred(shift.periods, period, band)
                    else 50
                )
                same_subject_penalty = 35 * state.subject_daily.get(
                    (school_class.id, demand.subject, day), 0
                )
                teacher_gap_penalty = 12 * (after_gaps - before_gaps)
                teacher_compact_reward = -5 if adjacent else 0
                class_balance_penalty = 3 * state.class_daily.get(
                    (school_class.id, day), 0
                )
                neutral_period_penalty = (
                    new_position if band == "any" else 0
                )
                preferred_shift_penalty = (
                    80
                    if teacher.preferred_shift is not None
                    and teacher.preferred_shift != shift.id
                    else 0
                )
                avoid_first_penalty = (
                    60
                    if teacher.avoid_first_period
                    and period == shift.periods[0]
                    else 0
                )
                preferred_slot_penalty = (
                    0
                    if not teacher.preferred_slots
                    or slot in teacher.preferred_slots
                    else 25
                )
                score = (
                    band_penalty
                    + preferred_shift_penalty
                    + avoid_first_penalty
                    + preferred_slot_penalty
                    + same_subject_penalty
                    + teacher_gap_penalty
                    + teacher_compact_reward
                    + class_balance_penalty
                    + neutral_period_penalty,
                    day_index[day],
                    period_index[period],
                    room_rank,
                )
                options.append(
                    (
                        score,
                        Assignment(
                            day=day,
                            shift_id=shift.id,
                            period=period,
                            class_id=school_class.id,
                            subject=demand.subject,
                            teacher_id=teacher.id,
                            room_id=room_id,
                            demand_id=demand.id,
                            occurrence_index=unit.occurrence_index,
                        ),
                    )
                )
    options.sort(key=lambda item: item[0])
    return options


def _pinned_class_hours(
    request: TimetableRequest,
    *,
    teachers: Mapping[str, Teacher],
    rooms: Mapping[str, Room],
    shifts: Mapping[str, Shift],
) -> tuple[list[Assignment], list[HardConflict]]:
    candidates: list[Assignment] = []
    conflicts: list[HardConflict] = []

    for school_class in request.classes:
        rule = school_class.class_hour
        if rule is None:
            continue
        shift = shifts[school_class.shift_id]
        teacher_id = rule.teacher_id or school_class.class_teacher_id
        if teacher_id is None or teacher_id not in teachers:
            continue
        teacher = teachers[teacher_id]
        slot = Slot(rule.day, shift.id, rule.period)
        if not _teacher_available(teacher, slot):
            conflicts.append(
                HardConflict(
                    "class_hour_teacher_unavailable",
                    (
                        f"{school_class.id} sinf soatida {teacher_id} "
                        "o'qituvchi mavjud emas."
                    ),
                    "class",
                    school_class.id,
                    missing_hours=1,
                )
            )
            continue

        room_id = (
            rule.room_id
            or school_class.home_room_id
            or next(
                (
                    room.id
                    for room in sorted(rooms.values(), key=lambda item: item.id)
                    if _room_compatible(room, shift.id, rule.subject)
                ),
                None,
            )
        )
        if rooms and room_id is None:
            conflicts.append(
                HardConflict(
                    "class_hour_no_room",
                    f"{school_class.id} sinf soati uchun mos xona yo'q.",
                    "class",
                    school_class.id,
                    missing_hours=1,
                )
            )
            continue
        if room_id is not None:
            room = rooms.get(room_id)
            if room is None or not _room_compatible(room, shift.id, rule.subject):
                conflicts.append(
                    HardConflict(
                        "class_hour_room_incompatible",
                        f"{school_class.id} sinf soati xonaga mos emas.",
                        "class",
                        school_class.id,
                        missing_hours=1,
                    )
                )
                continue
        candidates.append(
            Assignment(
                day=rule.day,
                shift_id=shift.id,
                period=rule.period,
                class_id=school_class.id,
                subject=rule.subject,
                teacher_id=teacher_id,
                room_id=room_id,
                source="class_hour",
            )
        )

    invalid_indexes: set[int] = set()
    claim_groups: tuple[tuple[str, object], ...] = (
        ("class", lambda assignment: assignment.class_id),
        ("teacher", lambda assignment: assignment.teacher_id),
        ("room", lambda assignment: assignment.room_id),
    )
    for entity_type, key_getter in claim_groups:
        for left_index, left in enumerate(candidates):
            entity_id = key_getter(left)  # type: ignore[operator]
            if entity_id is None:
                continue
            for right_index in range(left_index + 1, len(candidates)):
                right = candidates[right_index]
                if key_getter(right) != entity_id:  # type: ignore[operator]
                    continue
                if not _slots_overlap(left.slot, right.slot, shifts):
                    continue
                invalid_indexes.update((left_index, right_index))
                conflicts.append(
                    HardConflict(
                        f"class_hour_{entity_type}_collision",
                        (
                            f"Sinf soatlari {entity_type} bo'yicha bir vaqtda "
                            "to'qnashdi."
                        ),
                        entity_type,
                        str(entity_id),
                        missing_hours=2,
                        details={
                            "left": {
                                "class_id": left.class_id,
                                "day": left.day,
                                "shift_id": left.shift_id,
                                "period": left.period,
                            },
                            "right": {
                                "class_id": right.class_id,
                                "day": right.day,
                                "shift_id": right.shift_id,
                                "period": right.period,
                            },
                        },
                    )
                )

    teacher_day_counts: dict[tuple[str, str], list[int]] = {}
    for index, assignment in enumerate(candidates):
        if index in invalid_indexes:
            continue
        teacher_day_counts.setdefault(
            (assignment.teacher_id, assignment.day), []
        ).append(index)
    for (teacher_id, day), indexes in teacher_day_counts.items():
        limit = teachers[teacher_id].max_daily_lessons
        if len(indexes) <= limit:
            continue
        invalid_indexes.update(indexes[limit:])
        conflicts.append(
            HardConflict(
                "class_hour_teacher_daily_limit",
                f"{teacher_id} uchun {day} kunlik dars limiti oshdi.",
                "teacher",
                teacher_id,
                missing_hours=len(indexes) - limit,
            )
        )

    valid = [
        assignment
        for index, assignment in enumerate(candidates)
        if index not in invalid_indexes
    ]
    return valid, conflicts


def generate_timetable(request: TimetableRequest) -> ScheduleResult:
    """Generate a deterministic weekly timetable.

    Small/medium requests use bounded backtracking.  Large requests use the
    same deterministic candidate scoring in a greedy mode to avoid an
    unbounded combinatorial search.  In both modes unscheduled hours are
    explicit hard conflicts.
    """

    structural = _structural_conflicts(request)
    if structural:
        return ScheduleResult((), tuple(structural), (), 0)

    shifts = _index(request.shifts)
    classes = _index(request.classes)
    teachers = _index(request.teachers)
    rooms = _index(request.rooms)
    preferences: dict[str, PreferredBand] = {
        item.subject: item.preferred_band
        for item in request.subject_preferences
    }

    pinned, pinned_conflicts = _pinned_class_hours(
        request,
        teachers=teachers,
        rooms=rooms,
        shifts=shifts,
    )
    state = _State(pinned, shifts=shifts)
    units = [
        _Unit(demand, occurrence)
        for demand in request.demands
        for occurrence in range(1, demand.weekly_hours + 1)
    ]
    search_nodes = 0
    search_limit_reached = False
    heuristic_mode = len(units) > request.exact_search_max_units
    greedy_repair_used = False

    candidate_kwargs = {
        "classes": classes,
        "teachers": teachers,
        "rooms": rooms,
        "shifts": shifts,
        "preferences": preferences,
    }

    if heuristic_mode:
        initial_state = _State(pinned, shifts=shifts)

        def scarcity(unit: _Unit) -> tuple[int, int, str, int]:
            options = _candidate_options(
                unit, request, initial_state, **candidate_kwargs
            )
            return (
                len(options),
                -unit.demand.weekly_hours,
                unit.demand.id,
                unit.occurrence_index,
            )

        units.sort(key=scarcity)
        for unit in units:
            search_nodes += 1
            options = _candidate_options(
                unit, request, state, **candidate_kwargs
            )
            if options:
                state.add(options[0][1])
    else:
        best_assignments = list(state.assignments)
        solved = False

        def search(remaining: tuple[_Unit, ...]) -> bool:
            nonlocal search_nodes, search_limit_reached, best_assignments, solved
            if not remaining:
                best_assignments = list(state.assignments)
                solved = True
                return True
            if search_nodes >= request.max_search_nodes:
                search_limit_reached = True
                return False

            ranked: list[
                tuple[int, str, int, _Unit, list[tuple[tuple[int, ...], Assignment]]]
            ] = []
            for unit in remaining:
                options = _candidate_options(
                    unit, request, state, **candidate_kwargs
                )
                ranked.append(
                    (
                        len(options),
                        unit.demand.id,
                        unit.occurrence_index,
                        unit,
                        options,
                    )
                )
            ranked.sort(key=lambda item: (item[0], item[1], item[2]))
            _, _, _, unit, options = ranked[0]
            if not options:
                if len(state.assignments) > len(best_assignments):
                    best_assignments = list(state.assignments)
                return False

            next_remaining = list(remaining)
            next_remaining.remove(unit)
            frozen_remaining = tuple(next_remaining)
            for _, assignment in options:
                search_nodes += 1
                state.add(assignment)
                if len(state.assignments) > len(best_assignments):
                    best_assignments = list(state.assignments)
                if search(frozen_remaining):
                    return True
                state.remove(assignment)
                if search_nodes >= request.max_search_nodes:
                    search_limit_reached = True
                    break
            return False

        search(tuple(units))
        if not solved:
            state = _State(best_assignments, shifts=shifts)
            # The exact search looks for a complete schedule.  If one demand is
            # impossible, a zero-domain MRV unit can stop that search before
            # unrelated feasible units are visited.  Preserve the best prefix,
            # then deterministically fill every still-feasible unit instead of
            # incorrectly returning an empty/needlessly sparse draft.
            assigned_units = {
                (assignment.demand_id, assignment.occurrence_index)
                for assignment in state.assignments
                if assignment.demand_id is not None
            }
            repair_units = [
                unit
                for unit in units
                if (unit.demand.id, unit.occurrence_index)
                not in assigned_units
            ]
            repair_units.sort(
                key=lambda unit: (
                    len(
                        _candidate_options(
                            unit,
                            request,
                            state,
                            **candidate_kwargs,
                        )
                    ),
                    unit.demand.id,
                    unit.occurrence_index,
                )
            )
            for unit in repair_units:
                options = _candidate_options(
                    unit,
                    request,
                    state,
                    **candidate_kwargs,
                )
                if options:
                    state.add(options[0][1])
                    greedy_repair_used = True

    assigned_by_demand: dict[str, int] = {}
    for assignment in state.assignments:
        if assignment.demand_id is not None:
            _bump(assigned_by_demand, assignment.demand_id, 1)

    conflicts = list(pinned_conflicts)
    for demand in request.demands:
        missing = demand.weekly_hours - assigned_by_demand.get(demand.id, 0)
        if missing > 0:
            conflicts.append(
                HardConflict(
                    "unscheduled_lesson_hours",
                    (
                        f"{demand.class_id} / {demand.subject}: "
                        f"{missing} soatni qoidalarga zid bo'lmasdan "
                        "joylashtirib bo'lmadi."
                    ),
                    "demand",
                    demand.id,
                    missing_hours=missing,
                    details={
                        "class_id": demand.class_id,
                        "subject": demand.subject,
                        "teacher_id": demand.teacher_id,
                    },
                )
            )
    if search_limit_reached:
        conflicts.append(
            HardConflict(
                "search_limit_reached",
                (
                    "Jadval qidiruv chegarasiga yetdi; qattiq qoida "
                    "yumshatilmadi."
                ),
                "request",
                details={"max_search_nodes": request.max_search_nodes},
            )
        )

    warnings = _quality_warnings(
        request,
        state.assignments,
        preferences=preferences,
        heuristic_mode=heuristic_mode,
    )
    if greedy_repair_used:
        warnings.append(
            QualityWarning(
                "deterministic_partial_repair",
                (
                    "To'liq jadval topilmagach xavfsiz joylashadigan darslar "
                    "deterministik tarzda saqlab qolindi."
                ),
                "request",
            )
        )
    assignments = tuple(
        sorted(
            state.assignments,
            key=lambda item: (
                request.days.index(item.day),
                tuple(shifts).index(item.shift_id),
                shifts[item.shift_id].periods.index(item.period),
                item.class_id,
                item.subject,
            ),
        )
    )

    audit = audit_assignments(request, assignments, require_complete=False)
    conflicts.extend(audit)
    return ScheduleResult(
        assignments,
        tuple(conflicts),
        tuple(warnings),
        search_nodes,
    )


def audit_assignments(
    request: TimetableRequest,
    assignments: Sequence[Assignment],
    *,
    require_complete: bool = True,
) -> list[HardConflict]:
    """Audit a generated or externally supplied timetable.

    The default is deliberately publication-grade: all weekly demand hours and
    configured class hours must be present exactly once.  Draft/partial
    schedules can pass ``require_complete=False``; their existing rows are
    still checked against every hard constraint.
    """

    structural = _structural_conflicts(request)
    if structural:
        return structural

    conflicts: list[HardConflict] = []
    shifts: dict[str, Shift] = _index(request.shifts)
    classes: dict[str, SchoolClass] = _index(request.classes)
    teachers: dict[str, Teacher] = _index(request.teachers)
    rooms: dict[str, Room] = _index(request.rooms)
    demands: dict[str, LessonDemand] = _index(request.demands)
    state = _State(shifts=shifts)
    demand_counts: dict[str, int] = {}
    demand_day_counts: dict[tuple[str, str], int] = {}
    occurrence_claims: dict[tuple[str, int], int] = {}
    class_hour_counts: dict[str, int] = {}

    for row_index, assignment in enumerate(assignments):
        slot = assignment.slot
        school_class = classes.get(assignment.class_id)
        teacher = teachers.get(assignment.teacher_id)
        shift = shifts.get(assignment.shift_id)
        if (
            school_class is None
            or teacher is None
            or shift is None
            or assignment.day not in request.days
            or assignment.period not in shift.periods
        ):
            conflicts.append(
                HardConflict(
                    "assignment_unknown_reference",
                    "Jadval yozuvida noma'lum sinf, o'qituvchi yoki vaqt bor.",
                    "assignment",
                    assignment.demand_id,
                    details={"row_index": row_index},
                )
            )
            continue
        if school_class.shift_id != assignment.shift_id:
            conflicts.append(
                HardConflict(
                    "assignment_outside_class_shift",
                    f"{assignment.class_id} o'z smenasidan tashqariga qo'yilgan.",
                    "assignment",
                    assignment.demand_id,
                )
            )
        if not _teacher_available(teacher, slot):
            conflicts.append(
                HardConflict(
                    "assignment_teacher_unavailable",
                    f"{teacher.id} mavjud bo'lmagan vaqtda darsga qo'yilgan.",
                    "assignment",
                    assignment.demand_id,
                )
            )
        if assignment.room_id is not None:
            room = rooms.get(assignment.room_id)
            if room is None or not _room_compatible(
                room, assignment.shift_id, assignment.subject
            ):
                conflicts.append(
                    HardConflict(
                        "assignment_room_incompatible",
                        f"{assignment.room_id} xona darsga mos emas.",
                        "assignment",
                        assignment.demand_id,
                    )
                )
        elif rooms:
            conflicts.append(
                HardConflict(
                    "assignment_missing_room",
                    "Xonalar mavjud bo'lsa nashr qilinadigan dars xonasiz qolmaydi.",
                    "assignment",
                    assignment.demand_id,
                )
            )

        for busy, entity_type, entity_id in (
            (
                state.class_busy(assignment.class_id, slot),
                "class",
                assignment.class_id,
            ),
            (
                state.teacher_busy(assignment.teacher_id, slot),
                "teacher",
                assignment.teacher_id,
            ),
            (
                assignment.room_id is not None
                and state.room_busy(assignment.room_id, slot),
                "room",
                assignment.room_id,
            ),
        ):
            if busy:
                conflicts.append(
                    HardConflict(
                        f"{entity_type}_collision",
                        f"{entity_type} bir vaqtda ikki darsga qo'yilgan.",
                        entity_type,
                        entity_id,
                        details={
                            "day": slot.day,
                            "shift_id": slot.shift_id,
                            "period": slot.period,
                        },
                    )
                )

        if assignment.source == "regular":
            demand = (
                demands.get(assignment.demand_id)
                if assignment.demand_id is not None
                else None
            )
            if demand is None:
                conflicts.append(
                    HardConflict(
                        "assignment_unknown_demand",
                        "Oddiy dars mavjud talabga bog'lanmagan.",
                        "assignment",
                        assignment.demand_id,
                    )
                )
            else:
                mismatches = {
                    field_name: (actual, expected)
                    for field_name, actual, expected in (
                        ("class_id", assignment.class_id, demand.class_id),
                        ("subject", assignment.subject, demand.subject),
                        ("teacher_id", assignment.teacher_id, demand.teacher_id),
                    )
                    if actual != expected
                }
                if mismatches:
                    conflicts.append(
                        HardConflict(
                            "assignment_demand_mismatch",
                            "Dars yozuvi bog'langan talab ma'lumotiga mos emas.",
                            "assignment",
                            demand.id,
                            details={"mismatches": mismatches},
                        )
                    )
                if (
                    demand.allowed_shift_ids is not None
                    and assignment.shift_id not in demand.allowed_shift_ids
                ):
                    conflicts.append(
                        HardConflict(
                            "assignment_demand_shift_forbidden",
                            "Dars talab ruxsat bermagan smenaga qo'yilgan.",
                            "assignment",
                            demand.id,
                        )
                    )
                if (
                    demand.room_ids
                    and assignment.room_id not in demand.room_ids
                ):
                    conflicts.append(
                        HardConflict(
                            "assignment_demand_room_forbidden",
                            "Dars talab ruxsat bermagan xonaga qo'yilgan.",
                            "assignment",
                            demand.id,
                        )
                    )
                if (
                    isinstance(assignment.occurrence_index, bool)
                    or not isinstance(assignment.occurrence_index, int)
                    or not 1
                    <= assignment.occurrence_index
                    <= demand.weekly_hours
                ):
                    conflicts.append(
                        HardConflict(
                            "assignment_occurrence_out_of_range",
                            "Dars takrorlanish raqami haftalik talabdan tashqarida.",
                            "assignment",
                            demand.id,
                            details={
                                "occurrence_index": assignment.occurrence_index
                            },
                        )
                    )
                else:
                    occurrence_key = (
                        demand.id,
                        assignment.occurrence_index,
                    )
                    _bump(occurrence_claims, occurrence_key, 1)
                    if occurrence_claims[occurrence_key] == 2:
                        conflicts.append(
                            HardConflict(
                                "duplicate_assignment_occurrence",
                                "Bir haftalik dars takrorlanishi ikki marta yozilgan.",
                                "demand",
                                demand.id,
                                details={
                                    "occurrence_index": (
                                        assignment.occurrence_index
                                    )
                                },
                            )
                        )
                _bump(demand_counts, demand.id, 1)
                _bump(
                    demand_day_counts,
                    (demand.id, assignment.day),
                    1,
                )
        elif assignment.source == "class_hour":
            rule = school_class.class_hour
            if rule is None:
                conflicts.append(
                    HardConflict(
                        "unexpected_class_hour",
                        "Sinf uchun sozlanmagan sinf soati jadvalga qo'yilgan.",
                        "class",
                        school_class.id,
                    )
                )
            else:
                expected_teacher = (
                    rule.teacher_id or school_class.class_teacher_id
                )
                expected_room = rule.room_id or school_class.home_room_id
                mismatches = {
                    field_name: (actual, expected)
                    for field_name, actual, expected in (
                        ("day", assignment.day, rule.day),
                        (
                            "shift_id",
                            assignment.shift_id,
                            school_class.shift_id,
                        ),
                        ("period", assignment.period, rule.period),
                        ("subject", assignment.subject, rule.subject),
                        (
                            "teacher_id",
                            assignment.teacher_id,
                            expected_teacher,
                        ),
                    )
                    if actual != expected
                }
                if (
                    expected_room is not None
                    and assignment.room_id != expected_room
                ):
                    mismatches["room_id"] = (
                        assignment.room_id,
                        expected_room,
                    )
                if assignment.demand_id is not None:
                    mismatches["demand_id"] = (
                        assignment.demand_id,
                        None,
                    )
                if mismatches:
                    conflicts.append(
                        HardConflict(
                            "class_hour_assignment_mismatch",
                            "Sinf soati tasdiqlangan qoida bo'yicha joylashmagan.",
                            "class",
                            school_class.id,
                            details={"mismatches": mismatches},
                        )
                    )
            _bump(class_hour_counts, school_class.id, 1)
        else:
            conflicts.append(
                HardConflict(
                    "invalid_assignment_source",
                    "Dars manbasi regular yoki class_hour bo'lishi kerak.",
                    "assignment",
                    assignment.demand_id,
                )
            )

        state.add(assignment)

    for (teacher_id, day), count in state.teacher_daily.items():
        teacher = teachers.get(teacher_id)
        if teacher is not None and count > teacher.max_daily_lessons:
            conflicts.append(
                HardConflict(
                    "teacher_daily_limit_exceeded",
                    f"{teacher_id}ning {day} kungi dars limiti oshgan.",
                    "teacher",
                    teacher_id,
                    details={"day": day, "count": count},
                )
            )

    for demand in request.demands:
        count = demand_counts.get(demand.id, 0)
        if count > demand.weekly_hours:
            conflicts.append(
                HardConflict(
                    "demand_assignment_overflow",
                    f"{demand.id} uchun ortiqcha dars yozilgan.",
                    "demand",
                    demand.id,
                    details={
                        "expected": demand.weekly_hours,
                        "actual": count,
                    },
                )
            )
        elif require_complete and count < demand.weekly_hours:
            conflicts.append(
                HardConflict(
                    "demand_assignment_missing",
                    f"{demand.id} haftalik darslari to'liq emas.",
                    "demand",
                    demand.id,
                    missing_hours=demand.weekly_hours - count,
                    details={
                        "expected": demand.weekly_hours,
                        "actual": count,
                    },
                )
            )
        if demand.max_per_day is not None:
            for day in request.days:
                daily_count = demand_day_counts.get((demand.id, day), 0)
                if daily_count > demand.max_per_day:
                    conflicts.append(
                        HardConflict(
                            "demand_daily_limit_exceeded",
                            (
                                f"{demand.id} uchun {day} kunlik fan "
                                "limiti oshgan."
                            ),
                            "demand",
                            demand.id,
                            details={
                                "day": day,
                                "count": daily_count,
                                "limit": demand.max_per_day,
                            },
                        )
                    )

    for school_class in request.classes:
        expected = 1 if school_class.class_hour is not None else 0
        actual = class_hour_counts.get(school_class.id, 0)
        if actual > expected:
            conflicts.append(
                HardConflict(
                    "class_hour_assignment_overflow",
                    f"{school_class.id} uchun ortiqcha sinf soati yozilgan.",
                    "class",
                    school_class.id,
                    details={"expected": expected, "actual": actual},
                )
            )
        elif require_complete and actual < expected:
            conflicts.append(
                HardConflict(
                    "class_hour_assignment_missing",
                    f"{school_class.id} uchun sinf soati jadvalda yo'q.",
                    "class",
                    school_class.id,
                    missing_hours=expected - actual,
                )
            )
    return conflicts


def _quality_warnings(
    request: TimetableRequest,
    assignments: Sequence[Assignment],
    *,
    preferences: Mapping[str, PreferredBand],
    heuristic_mode: bool,
) -> list[QualityWarning]:
    warnings: list[QualityWarning] = []
    shifts: dict[str, Shift] = _index(request.shifts)
    demand_index: dict[str, LessonDemand] = _index(request.demands)

    if heuristic_mode:
        warnings.append(
            QualityWarning(
                "bounded_heuristic_mode",
                (
                    "Jadval katta bo'lgani uchun cheksiz qidiruv o'rniga "
                    "barqaror deterministik joylashtirish ishlatildi."
                ),
                "request",
                details={"lesson_units": sum(d.weekly_hours for d in request.demands)},
            )
        )

    band_misses: dict[str, int] = {}
    subject_days: dict[tuple[str, str, str], int] = {}
    teacher_periods: dict[tuple[str, str, str], list[int]] = {}
    teacher_preference_misses: dict[tuple[str, str], int] = {}
    for assignment in assignments:
        if assignment.demand_id is not None:
            demand = demand_index[assignment.demand_id]
            band = _preferred_band(demand, preferences)
            shift = shifts[assignment.shift_id]
            if not _period_is_preferred(shift.periods, assignment.period, band):
                _bump(band_misses, demand.id, 1)
            _bump(
                subject_days,
                (assignment.class_id, assignment.subject, assignment.day),
                1,
            )
        teacher_periods.setdefault(
            (assignment.teacher_id, assignment.day, assignment.shift_id), []
        ).append(assignment.period)
        teacher = next(
            item for item in request.teachers if item.id == assignment.teacher_id
        )
        shift = shifts[assignment.shift_id]
        if (
            teacher.preferred_shift is not None
            and teacher.preferred_shift != assignment.shift_id
        ):
            _bump(teacher_preference_misses, (teacher.id, "shift"), 1)
        if teacher.avoid_first_period and assignment.period == shift.periods[0]:
            _bump(teacher_preference_misses, (teacher.id, "first_period"), 1)
        if teacher.preferred_slots and assignment.slot not in teacher.preferred_slots:
            _bump(teacher_preference_misses, (teacher.id, "preferred_slot"), 1)

    for (teacher_id, preference), count in sorted(
        teacher_preference_misses.items()
    ):
        warnings.append(
            QualityWarning(
                "teacher_preference_not_met",
                f"{teacher_id}: {count} dars o'qituvchi afzal vaqtiga tushmadi.",
                "teacher",
                teacher_id,
                details={"preference": preference, "count": count},
            )
        )

    for demand_id, count in sorted(band_misses.items()):
        demand = demand_index[demand_id]
        warnings.append(
            QualityWarning(
                "subject_outside_preferred_band",
                (
                    f"{demand.class_id} / {demand.subject}: {count} dars "
                    "afzal vaqt oralig'idan tashqarida."
                ),
                "demand",
                demand_id,
                details={"count": count},
            )
        )

    for (class_id, subject, day), count in sorted(subject_days.items()):
        if count > 1:
            warnings.append(
                QualityWarning(
                    "subject_repeated_same_day",
                    f"{class_id}da {subject} {day} kuni {count} marta qo'yildi.",
                    "class",
                    class_id,
                    details={"subject": subject, "day": day, "count": count},
                )
            )

    for (teacher_id, day, shift_id), periods in sorted(teacher_periods.items()):
        shift = shifts[shift_id]
        positions = [shift.periods.index(period) for period in periods]
        gaps = _gap_count(positions)
        if gaps:
            warnings.append(
                QualityWarning(
                    "teacher_day_has_gaps",
                    (
                        f"{teacher_id}ning {day} kungi {shift_id} smenasida "
                        f"{gaps} ta bo'sh oraliq bor."
                    ),
                    "teacher",
                    teacher_id,
                    details={
                        "day": day,
                        "shift_id": shift_id,
                        "periods": tuple(sorted(periods)),
                        "gap_count": gaps,
                    },
                )
            )
    return warnings


# ---------------------------------------------------------------------------
# Academic calendar make-up planning
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CalendarLesson:
    id: str
    lesson_date: date
    shift_id: str
    period: int
    class_id: str
    subject: str
    teacher_id: str
    room_id: str | None = None
    status: Literal["scheduled", "cancelled"] = "scheduled"


@dataclass(frozen=True)
class Cancellation:
    lesson_id: str
    reason: str


@dataclass(frozen=True)
class CalendarDayLabel:
    lesson_date: date
    day_label: str


@dataclass(frozen=True)
class MakeupRequest:
    lessons: tuple[CalendarLesson, ...]
    cancellations: tuple[Cancellation, ...]
    candidate_dates: tuple[date, ...]
    shifts: tuple[Shift, ...]
    teachers: tuple[Teacher, ...]
    rooms: tuple[Room, ...] = ()
    day_labels: tuple[CalendarDayLabel, ...] = ()
    max_extra_lessons_per_class_per_day: int = 1
    allow_topic_compression: bool = True


@dataclass(frozen=True)
class MakeupPlacement:
    original_lesson_id: str
    original_date: date
    target_date: date
    shift_id: str
    period: int
    class_id: str
    subject: str
    teacher_id: str
    room_id: str | None
    mode: MakeupMode
    target_lesson_id: str | None = None
    # Calendar changes are drafts.  The API must persist a separate,
    # authenticated human confirmation before publishing them.
    requires_human_approval: bool = True


@dataclass(frozen=True)
class MakeupResult:
    """Calendar make-up result.

    ``original_lessons`` always contains the exact source lessons, including
    cancelled records.  The helper never erases history.
    """

    original_lessons: tuple[CalendarLesson, ...]
    placements: tuple[MakeupPlacement, ...]
    hard_conflicts: tuple[HardConflict, ...]
    quality_warnings: tuple[QualityWarning, ...]

    @property
    def complete(self) -> bool:
        return not self.hard_conflicts

    @property
    def requires_human_approval(self) -> bool:
        return any(item.requires_human_approval for item in self.placements)

    @property
    def ready_to_publish(self) -> bool:
        return self.complete and not self.requires_human_approval


def _calendar_day_label(
    target_date: date,
    labels: Mapping[date, str],
) -> str:
    # `strftime("%A")` depends on the process locale and can silently stop
    # matching method-day names after deployment.  `date.weekday()` is stable.
    return labels.get(target_date, CANONICAL_WEEKDAYS[target_date.weekday()])


def _calendar_structural_conflicts(
    request: MakeupRequest,
) -> list[HardConflict]:
    conflicts: list[HardConflict] = []
    duplicate_lesson_ids = _duplicates(
        lesson.id
        for lesson in request.lessons
        if isinstance(lesson.id, str)
    )
    duplicate_cancellations = _duplicates(
        cancellation.lesson_id
        for cancellation in request.cancellations
        if isinstance(cancellation.lesson_id, str)
    )
    if duplicate_lesson_ids or duplicate_cancellations:
        conflicts.append(
            HardConflict(
                "duplicate_calendar_identifier",
                "Kalendar darsi yoki bekor qilish yozuvi takrorlangan.",
                "calendar",
                details={
                    "lesson_ids": tuple(sorted(duplicate_lesson_ids)),
                    "cancellation_ids": tuple(
                        sorted(duplicate_cancellations)
                    ),
                },
            )
        )

    for entity_type, items in (
        ("shift", request.shifts),
        ("teacher", request.teachers),
        ("room", request.rooms),
    ):
        duplicates = _duplicates(
            getattr(item, "id")
            for item in items
            if isinstance(getattr(item, "id", None), str)
        )
        for duplicate in sorted(duplicates):
            conflicts.append(
                HardConflict(
                    f"duplicate_{entity_type}",
                    f"{entity_type} identifikatori takrorlangan.",
                    entity_type,
                    duplicate,
                )
            )
        if any(
            not _is_nonempty_text(getattr(item, "id", None))
            for item in items
        ):
            conflicts.append(
                HardConflict(
                    f"invalid_{entity_type}_id",
                    f"{entity_type} identifikatori bo'sh.",
                    entity_type,
                )
            )

    conflicts.extend(
        _shift_validation_conflicts(
            request.shifts,
            entity_scope="calendar",
        )
    )
    shifts: dict[str, Shift] = _index(request.shifts)
    teachers: dict[str, Teacher] = _index(request.teachers)
    rooms: dict[str, Room] = _index(request.rooms)
    lessons: dict[str, CalendarLesson] = _index(request.lessons)

    if (
        isinstance(request.max_extra_lessons_per_class_per_day, bool)
        or not isinstance(
            request.max_extra_lessons_per_class_per_day,
            int,
        )
        or request.max_extra_lessons_per_class_per_day < 1
        or request.max_extra_lessons_per_class_per_day
        > ABSOLUTE_TEACHER_DAILY_MAX
    ):
        conflicts.append(
            HardConflict(
                "invalid_makeup_daily_limit",
                (
                    "Kunlik qo'shimcha dars limiti 1–"
                    f"{ABSOLUTE_TEACHER_DAILY_MAX} oralig'ida bo'lishi kerak."
                ),
                "calendar",
            )
        )

    if any(not isinstance(value, date) for value in request.candidate_dates):
        conflicts.append(
            HardConflict(
                "invalid_candidate_date",
                "Qo'shimcha dars sanasi haqiqiy sana bo'lishi kerak.",
                "calendar",
            )
        )

    label_dates = [
        item.lesson_date
        for item in request.day_labels
        if isinstance(item.lesson_date, date)
    ]
    for duplicate_date in sorted(_duplicates(label_dates)):
        conflicts.append(
            HardConflict(
                "duplicate_calendar_day_label",
                "Bitta sana uchun hafta kuni ikki marta kiritilgan.",
                "calendar",
                str(duplicate_date),
            )
        )
    if any(
        not isinstance(item.lesson_date, date)
        or not _is_nonempty_text(item.day_label)
        for item in request.day_labels
    ):
        conflicts.append(
            HardConflict(
                "invalid_calendar_day_label",
                "Kalendar kuni yorlig'i noto'g'ri.",
                "calendar",
            )
        )
    supported_day_labels = set(CANONICAL_WEEKDAYS) | {
        item.day_label
        for item in request.day_labels
        if _is_nonempty_text(item.day_label)
    }

    for teacher in request.teachers:
        if (
            isinstance(teacher.max_daily_lessons, bool)
            or not isinstance(teacher.max_daily_lessons, int)
            or not 1
            <= teacher.max_daily_lessons
            <= ABSOLUTE_TEACHER_DAILY_MAX
        ):
            conflicts.append(
                HardConflict(
                    "invalid_teacher_daily_max",
                    f"{teacher.id} uchun kunlik dars limiti noto'g'ri.",
                    "teacher",
                    teacher.id,
                )
            )
        unknown_days = set(teacher.method_days) - supported_day_labels
        if unknown_days:
            conflicts.append(
                HardConflict(
                    "teacher_unknown_method_day",
                    f"{teacher.id} uchun noma'lum metod kuni kiritilgan.",
                    "teacher",
                    teacher.id,
                    details={"days": tuple(sorted(unknown_days))},
                )
            )
        if teacher.available_slots is not None:
            for slot in teacher.available_slots:
                shift = shifts.get(slot.shift_id)
                if (
                    slot.day not in supported_day_labels
                    or shift is None
                    or slot.period not in shift.periods
                ):
                    conflicts.append(
                        HardConflict(
                            "invalid_teacher_availability_slot",
                            f"{teacher.id} uchun noma'lum bo'sh vaqt bor.",
                            "teacher",
                            teacher.id,
                        )
                    )

    cancelled_ids = {
        cancellation.lesson_id for cancellation in request.cancellations
    }
    for cancellation in request.cancellations:
        if cancellation.lesson_id not in lessons:
            conflicts.append(
                HardConflict(
                    "cancelled_lesson_not_found",
                    f"{cancellation.lesson_id} kalendarda topilmadi.",
                    "lesson",
                    cancellation.lesson_id,
                )
            )
        if not _is_nonempty_text(cancellation.reason):
            conflicts.append(
                HardConflict(
                    "empty_cancellation_reason",
                    "Bekor qilingan dars sababi yozilishi kerak.",
                    "lesson",
                    cancellation.lesson_id,
                )
            )

    state = _State(shifts=shifts)
    for lesson in request.lessons:
        valid_reference = True
        if (
            not _is_nonempty_text(lesson.id)
            or not isinstance(lesson.lesson_date, date)
            or not _is_nonempty_text(lesson.class_id)
            or not _is_nonempty_text(lesson.subject)
            or lesson.status not in {"scheduled", "cancelled"}
        ):
            conflicts.append(
                HardConflict(
                    "invalid_calendar_lesson",
                    "Kalendar darsi ma'lumoti noto'g'ri.",
                    "lesson",
                    str(lesson.id),
                )
            )
            valid_reference = False
        shift = shifts.get(lesson.shift_id)
        if shift is None or lesson.period not in (
            shift.periods if shift is not None else ()
        ):
            conflicts.append(
                HardConflict(
                    "calendar_lesson_unknown_slot",
                    f"{lesson.id} darsining smena yoki soati topilmadi.",
                    "lesson",
                    lesson.id,
                )
            )
            valid_reference = False
        teacher = teachers.get(lesson.teacher_id)
        if teacher is None:
            conflicts.append(
                HardConflict(
                    "calendar_lesson_unknown_teacher",
                    f"{lesson.id} darsining o'qituvchisi topilmadi.",
                    "lesson",
                    lesson.id,
                )
            )
            valid_reference = False
        if rooms:
            room = (
                rooms.get(lesson.room_id)
                if lesson.room_id is not None
                else None
            )
            if room is None:
                conflicts.append(
                    HardConflict(
                        "calendar_lesson_unknown_room",
                        f"{lesson.id} darsining xonasi topilmadi.",
                        "lesson",
                        lesson.id,
                    )
                )
                valid_reference = False
            elif shift is not None and not _room_compatible(
                room,
                lesson.shift_id,
                lesson.subject,
            ):
                conflicts.append(
                    HardConflict(
                        "calendar_lesson_room_incompatible",
                        f"{lesson.id} darsining xonasi fanga yoki smenaga mos emas.",
                        "lesson",
                        lesson.id,
                    )
                )
                valid_reference = False
        if lesson.status == "cancelled" and lesson.id not in cancelled_ids:
            conflicts.append(
                HardConflict(
                    "orphan_cancelled_lesson",
                    (
                        f"{lesson.id} bekor qilingan, lekin sabab va "
                        "ko'chirish talabi topilmadi."
                    ),
                    "lesson",
                    lesson.id,
                    missing_hours=1,
                )
            )
        if (
            not valid_reference
            or lesson.id in cancelled_ids
            or lesson.status == "cancelled"
        ):
            continue

        day_key = lesson.lesson_date.isoformat()
        slot = Slot(day_key, lesson.shift_id, lesson.period)
        for busy, entity_type, entity_id in (
            (state.class_busy(lesson.class_id, slot), "class", lesson.class_id),
            (
                state.teacher_busy(lesson.teacher_id, slot),
                "teacher",
                lesson.teacher_id,
            ),
            (
                lesson.room_id is not None
                and state.room_busy(lesson.room_id, slot),
                "room",
                lesson.room_id,
            ),
        ):
            if busy:
                conflicts.append(
                    HardConflict(
                        f"calendar_{entity_type}_collision",
                        "Kalendar asosida bir vaqtda ikki dars bor.",
                        entity_type,
                        entity_id,
                        details={
                            "date": day_key,
                            "shift_id": lesson.shift_id,
                            "period": lesson.period,
                        },
                    )
                )
        state.add(
            Assignment(
                day=day_key,
                shift_id=lesson.shift_id,
                period=lesson.period,
                class_id=lesson.class_id,
                subject=lesson.subject,
                teacher_id=lesson.teacher_id,
                room_id=lesson.room_id,
            )
        )

    for (teacher_id, day_key), count in state.teacher_daily.items():
        teacher = teachers.get(teacher_id)
        if teacher is not None and count > teacher.max_daily_lessons:
            conflicts.append(
                HardConflict(
                    "calendar_teacher_daily_limit_exceeded",
                    f"{teacher_id}ning {day_key} kungi dars limiti oshgan.",
                    "teacher",
                    teacher_id,
                    details={"date": day_key, "count": count},
                )
            )
    return conflicts


def plan_calendar_makeups(request: MakeupRequest) -> MakeupResult:
    """Move cancelled curriculum to later dates without deleting history.

    First, the helper searches for a genuinely free later period.  If none is
    available and ``allow_topic_compression`` is enabled, it may merge the
    missed topic with a later lesson of the same class, subject and teacher.
    Such a merge is explicit in ``MakeupPlacement.mode`` and always produces a
    ``topic_compression`` warning.
    """

    conflicts = _calendar_structural_conflicts(request)
    warnings: list[QualityWarning] = []
    placements: list[MakeupPlacement] = []
    if conflicts:
        return MakeupResult(
            request.lessons,
            (),
            tuple(conflicts),
            (),
        )
    shifts: dict[str, Shift] = _index(request.shifts)
    teachers: dict[str, Teacher] = _index(request.teachers)
    rooms: dict[str, Room] = _index(request.rooms)
    labels = {
        item.lesson_date: item.day_label
        for item in request.day_labels
    }
    lessons = {lesson.id: lesson for lesson in request.lessons}

    cancelled_ids = {item.lesson_id for item in request.cancellations}

    occupied_class: set[tuple[str, date, str, int]] = set()
    occupied_teacher: set[tuple[str, date, str, int]] = set()
    occupied_room: set[tuple[str, date, str, int]] = set()
    teacher_daily: dict[tuple[str, date], int] = {}
    extra_daily: dict[tuple[str, date], int] = {}
    compressed_targets: set[str] = set()
    calendar_state = _State(shifts=shifts)

    for lesson in request.lessons:
        if lesson.id in cancelled_ids or lesson.status == "cancelled":
            continue
        key = (lesson.lesson_date, lesson.shift_id, lesson.period)
        occupied_class.add((lesson.class_id, *key))
        occupied_teacher.add((lesson.teacher_id, *key))
        if lesson.room_id is not None:
            occupied_room.add((lesson.room_id, *key))
        _bump(teacher_daily, (lesson.teacher_id, lesson.lesson_date), 1)
        calendar_state.add(
            Assignment(
                day=lesson.lesson_date.isoformat(),
                shift_id=lesson.shift_id,
                period=lesson.period,
                class_id=lesson.class_id,
                subject=lesson.subject,
                teacher_id=lesson.teacher_id,
                room_id=lesson.room_id,
            )
        )

    ordered_cancellations = sorted(
        (
            cancellation
            for cancellation in request.cancellations
            if cancellation.lesson_id in lessons
        ),
        key=lambda item: (
            lessons[item.lesson_id].lesson_date,
            item.lesson_id,
        ),
    )
    candidate_dates = tuple(sorted(set(request.candidate_dates)))

    for cancellation in ordered_cancellations:
        original = lessons[cancellation.lesson_id]
        shift = shifts.get(original.shift_id)
        teacher = teachers.get(original.teacher_id)
        if shift is None or teacher is None or original.period not in (
            shift.periods if shift else ()
        ):
            conflicts.append(
                HardConflict(
                    "makeup_invalid_original_lesson",
                    f"{original.id} darsining smena yoki o'qituvchisi topilmadi.",
                    "lesson",
                    original.id,
                    missing_hours=1,
                )
            )
            continue

        room_candidates: tuple[str | None, ...]
        if not rooms:
            room_candidates = (None,)
        else:
            ordered_rooms = ([original.room_id] if original.room_id else []) + sorted(
                rooms
            )
            compatible_rooms: list[str] = []
            for room_id in ordered_rooms:
                if room_id is None or room_id in compatible_rooms:
                    continue
                room = rooms.get(room_id)
                if room is not None and _room_compatible(
                    room,
                    original.shift_id,
                    original.subject,
                ):
                    compatible_rooms.append(room_id)
            room_candidates = tuple(compatible_rooms)

        placed = False
        later_dates = [
            target_date
            for target_date in candidate_dates
            if target_date > original.lesson_date
        ]
        period_order = (original.period,) + tuple(
            period for period in shift.periods if period != original.period
        )
        for target_date in later_dates:
            if (
                extra_daily.get((original.class_id, target_date), 0)
                >= request.max_extra_lessons_per_class_per_day
            ):
                continue
            if (
                teacher_daily.get((teacher.id, target_date), 0)
                >= teacher.max_daily_lessons
            ):
                continue
            day_label = _calendar_day_label(target_date, labels)
            ordered_periods = sorted(
                period_order,
                key=lambda period: (
                    bool(
                        teacher.preferred_slots
                        and Slot(day_label, original.shift_id, period)
                        not in teacher.preferred_slots
                    ),
                    bool(
                        teacher.avoid_first_period
                        and period == shift.periods[0]
                    ),
                    period_order.index(period),
                ),
            )
            for period in ordered_periods:
                weekly_slot = Slot(day_label, original.shift_id, period)
                if not _teacher_available(teacher, weekly_slot):
                    continue
                slot_key = (target_date, original.shift_id, period)
                state_slot = Slot(
                    target_date.isoformat(),
                    original.shift_id,
                    period,
                )
                if calendar_state.class_busy(original.class_id, state_slot):
                    continue
                if calendar_state.teacher_busy(teacher.id, state_slot):
                    continue
                for room_id in room_candidates:
                    if room_id is not None and calendar_state.room_busy(
                        room_id,
                        state_slot,
                    ):
                        continue
                    placement = MakeupPlacement(
                        original_lesson_id=original.id,
                        original_date=original.lesson_date,
                        target_date=target_date,
                        shift_id=original.shift_id,
                        period=period,
                        class_id=original.class_id,
                        subject=original.subject,
                        teacher_id=teacher.id,
                        room_id=room_id,
                        mode="extra_period",
                    )
                    placements.append(placement)
                    occupied_class.add((original.class_id, *slot_key))
                    occupied_teacher.add((teacher.id, *slot_key))
                    if room_id is not None:
                        occupied_room.add((room_id, *slot_key))
                    calendar_state.add(
                        Assignment(
                            day=target_date.isoformat(),
                            shift_id=original.shift_id,
                            period=period,
                            class_id=original.class_id,
                            subject=original.subject,
                            teacher_id=teacher.id,
                            room_id=room_id,
                        )
                    )
                    _bump(teacher_daily, (teacher.id, target_date), 1)
                    _bump(extra_daily, (original.class_id, target_date), 1)
                    warnings.append(
                        QualityWarning(
                            "calendar_makeup_added",
                            (
                                f"{original.id} bekor qilinmadi: "
                                f"{target_date.isoformat()} kuniga ko'chirildi."
                            ),
                            "lesson",
                            original.id,
                            details={
                                "reason": cancellation.reason,
                                "target_date": target_date.isoformat(),
                                "period": period,
                            },
                        )
                    )
                    placed = True
                    break
                if placed:
                    break
            if placed:
                break

        if placed:
            continue

        if request.allow_topic_compression:
            compression_candidates = sorted(
                (
                    lesson
                    for lesson in request.lessons
                    if lesson.id not in cancelled_ids
                    and lesson.status == "scheduled"
                    and lesson.id not in compressed_targets
                    and lesson.lesson_date > original.lesson_date
                    and lesson.lesson_date in candidate_dates
                    and lesson.class_id == original.class_id
                    and lesson.subject == original.subject
                    and lesson.teacher_id == original.teacher_id
                    and lesson.shift_id == original.shift_id
                ),
                key=lambda lesson: (
                    lesson.lesson_date,
                    shift.periods.index(lesson.period),
                    lesson.id,
                ),
            )
            if compression_candidates:
                target = compression_candidates[0]
                compressed_targets.add(target.id)
                placements.append(
                    MakeupPlacement(
                        original_lesson_id=original.id,
                        original_date=original.lesson_date,
                        target_date=target.lesson_date,
                        shift_id=target.shift_id,
                        period=target.period,
                        class_id=target.class_id,
                        subject=target.subject,
                        teacher_id=target.teacher_id,
                        room_id=target.room_id,
                        mode="compressed",
                        target_lesson_id=target.id,
                    )
                )
                warnings.append(
                    QualityWarning(
                        "topic_compression",
                        (
                            f"{original.id} mavzusi {target.id} darsiga '/' "
                            "bilan tig'izlashtirildi; metodist tasdig'i kerak."
                        ),
                        "lesson",
                        original.id,
                        details={
                            "reason": cancellation.reason,
                            "target_lesson_id": target.id,
                            "target_date": target.lesson_date.isoformat(),
                        },
                    )
                )
                continue

        conflicts.append(
            HardConflict(
                "makeup_unscheduled",
                (
                    f"{original.id} bekor qilingan dars uchun keyingi "
                    "xavfsiz vaqt topilmadi; dars tarixdan o'chirilmadi."
                ),
                "lesson",
                original.id,
                missing_hours=1,
                details={"reason": cancellation.reason},
            )
        )

    return MakeupResult(
        request.lessons,
        tuple(placements),
        tuple(conflicts),
        tuple(warnings),
    )


__all__ = [
    "ABSOLUTE_TEACHER_DAILY_MAX",
    "Assignment",
    "CalendarDayLabel",
    "CalendarLesson",
    "Cancellation",
    "ClassHourPolicy",
    "ClassHourRule",
    "DEFAULT_EXACT_SEARCH_MAX_UNITS",
    "DEFAULT_MAX_SEARCH_NODES",
    "HardConflict",
    "LessonDemand",
    "MAX_EXACT_SEARCH_UNITS",
    "MAX_SEARCH_NODES",
    "MAX_CANDIDATE_EVALUATIONS",
    "MAX_WEEKLY_HOURS_PER_DEMAND",
    "MakeupPlacement",
    "MakeupRequest",
    "MakeupResult",
    "QualityWarning",
    "Room",
    "ScheduleResult",
    "SchoolClass",
    "Shift",
    "Slot",
    "SubjectPreference",
    "Teacher",
    "TimetableRequest",
    "audit_assignments",
    "generate_timetable",
    "plan_calendar_makeups",
]
