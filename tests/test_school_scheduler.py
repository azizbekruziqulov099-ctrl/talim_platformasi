"""Unit tests for the deterministic school scheduling engine."""

from __future__ import annotations

import unittest
from datetime import date

from backend.modules.school_scheduler import (
    Assignment,
    CalendarDayLabel,
    CalendarLesson,
    Cancellation,
    ClassHourPolicy,
    ClassHourRule,
    LessonDemand,
    MAX_EXACT_SEARCH_UNITS,
    MAX_SEARCH_NODES,
    MAX_CANDIDATE_EVALUATIONS,
    MAX_WEEKLY_HOURS_PER_DEMAND,
    MakeupRequest,
    Room,
    SchoolClass,
    Shift,
    Slot,
    SubjectPreference,
    Teacher,
    TimetableRequest,
    audit_assignments,
    generate_timetable,
    plan_calendar_makeups,
)


DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday")
MORNING = Shift("morning", (1, 2, 3, 4, 5, 6))
AFTERNOON = Shift("afternoon", (1, 2, 3, 4, 5, 6))


class SchoolSchedulerTests(unittest.TestCase):
    def base_request(self, **overrides) -> TimetableRequest:
        data = {
            "days": DAYS,
            "shifts": (MORNING, AFTERNOON),
            "classes": (
                SchoolClass("5-A", "morning", "101", "t-class"),
                SchoolClass("5-B", "morning", "102", "t-class-b"),
            ),
            "teachers": (
                Teacher("t-math"),
                Teacher("t-history"),
                Teacher("t-class"),
                Teacher("t-class-b"),
            ),
            "rooms": (
                Room("101"),
                Room("102"),
                Room("math", allowed_subjects=frozenset({"Matematika"})),
            ),
            "demands": (
                LessonDemand(
                    "5a-math",
                    "5-A",
                    "Matematika",
                    "t-math",
                    5,
                    ("math",),
                    preferred_band="early",
                    max_per_day=1,
                ),
                LessonDemand(
                    "5b-math",
                    "5-B",
                    "Matematika",
                    "t-math",
                    5,
                    ("math",),
                    preferred_band="early",
                    max_per_day=1,
                ),
                LessonDemand(
                    "5a-history",
                    "5-A",
                    "Tarix",
                    "t-history",
                    2,
                    ("101",),
                    max_per_day=1,
                ),
            ),
        }
        data.update(overrides)
        return TimetableRequest(**data)

    def test_is_deterministic_and_collision_free(self):
        request = self.base_request()
        first = generate_timetable(request)
        second = generate_timetable(request)

        self.assertTrue(first.complete, first.hard_conflicts)
        self.assertEqual(first.assignments, second.assignments)
        self.assertEqual(first.quality_warnings, second.quality_warnings)
        self.assertEqual(len(first.assignments), 12)
        self.assertEqual(audit_assignments(request, first.assignments), [])

        teacher_slots = {
            (item.teacher_id, item.day, item.shift_id, item.period)
            for item in first.assignments
        }
        self.assertEqual(len(teacher_slots), len(first.assignments))

    def test_two_shifts_have_independent_period_numbers(self):
        request = TimetableRequest(
            days=("Monday",),
            shifts=(MORNING, AFTERNOON),
            classes=(
                SchoolClass("5-A", "morning", "101"),
                SchoolClass("8-A", "afternoon", "201"),
            ),
            teachers=(Teacher("t-math"),),
            rooms=(Room("101"), Room("201")),
            demands=(
                LessonDemand("m1", "5-A", "Matematika", "t-math", 1, ("101",)),
                LessonDemand("m2", "8-A", "Matematika", "t-math", 1, ("201",)),
            ),
        )
        result = generate_timetable(request)

        self.assertTrue(result.complete, result.hard_conflicts)
        self.assertEqual(len(result.assignments), 2)
        self.assertEqual(
            {(item.shift_id, item.period) for item in result.assignments},
            {("morning", 1), ("afternoon", 1)},
        )

    def test_method_day_availability_and_daily_cap_are_hard(self):
        teacher = Teacher(
            "limited",
            method_days=frozenset({"Tuesday"}),
            available_slots=frozenset(
                {
                    Slot("Monday", "morning", 1),
                    Slot("Monday", "morning", 2),
                    Slot("Tuesday", "morning", 1),
                }
            ),
            max_daily_lessons=2,
        )
        request = TimetableRequest(
            days=("Monday", "Tuesday"),
            shifts=(Shift("morning", (1, 2, 3)),),
            classes=(SchoolClass("5-A", "morning", "101"),),
            teachers=(teacher,),
            rooms=(Room("101"),),
            demands=(
                LessonDemand("math", "5-A", "Matematika", "limited", 3),
            ),
        )
        result = generate_timetable(request)

        self.assertFalse(result.complete)
        self.assertEqual(len(result.assignments), 2)
        self.assertEqual(
            sum(item.missing_hours for item in result.hard_conflicts),
            1,
        )
        self.assertTrue(all(item.day == "Monday" for item in result.assignments))

    def test_teacher_soft_preferences_change_candidate_order(self):
        preferred = Slot("Monday", "morning", 2)
        request = TimetableRequest(
            days=("Monday",),
            shifts=(Shift("morning", (1, 2, 3)),),
            classes=(SchoolClass("5-A", "morning"),),
            teachers=(
                Teacher(
                    "t-math",
                    preferred_slots=frozenset({preferred}),
                    preferred_shift="morning",
                    avoid_first_period=True,
                ),
            ),
            rooms=(),
            demands=(
                LessonDemand("math", "5-A", "Matematika", "t-math", 1),
            ),
        )

        result = generate_timetable(request)

        self.assertTrue(result.complete, result.hard_conflicts)
        self.assertEqual(result.assignments[0].slot, preferred)
        self.assertNotIn(
            "teacher_preference_not_met",
            {item.code for item in result.quality_warnings},
        )

    def test_available_slots_remain_hard_when_soft_preferences_conflict(self):
        only_allowed = Slot("Monday", "morning", 1)
        request = TimetableRequest(
            days=("Monday",),
            shifts=(Shift("morning", (1, 2)),),
            classes=(SchoolClass("5-A", "morning"),),
            teachers=(
                Teacher(
                    "t-math",
                    available_slots=frozenset({only_allowed}),
                    preferred_slots=frozenset(
                        {Slot("Monday", "morning", 2)}
                    ),
                    avoid_first_period=True,
                ),
            ),
            rooms=(),
            demands=(
                LessonDemand("math", "5-A", "Matematika", "t-math", 1),
            ),
        )

        result = generate_timetable(request)

        self.assertTrue(result.complete, result.hard_conflicts)
        self.assertEqual(result.assignments[0].slot, only_allowed)
        self.assertIn(
            "teacher_preference_not_met",
            {item.code for item in result.quality_warnings},
        )

    def test_teacher_daily_limit_cannot_exceed_seven(self):
        request = self.base_request(
            teachers=(Teacher("t-math", max_daily_lessons=8),),
            classes=(SchoolClass("5-A", "morning"),),
            rooms=(),
            demands=(LessonDemand("m", "5-A", "Matematika", "t-math", 1),),
        )
        result = generate_timetable(request)

        self.assertFalse(result.complete)
        self.assertIn(
            "invalid_teacher_daily_max",
            {item.code for item in result.hard_conflicts},
        )
        self.assertEqual(result.assignments, ())

    def test_friday_first_period_class_hour_is_pinned(self):
        request = self.base_request(
            classes=(
                SchoolClass(
                    "5-A",
                    "morning",
                    "101",
                    "t-class",
                    ClassHourRule("Friday", 1),
                ),
            ),
            demands=(
                LessonDemand(
                    "math",
                    "5-A",
                    "Matematika",
                    "t-math",
                    5,
                    ("math",),
                    preferred_band="early",
                    max_per_day=1,
                ),
            ),
        )
        result = generate_timetable(request)

        self.assertTrue(result.complete, result.hard_conflicts)
        class_hours = [
            item for item in result.assignments if item.source == "class_hour"
        ]
        self.assertEqual(len(class_hours), 1)
        self.assertEqual(
            (class_hours[0].day, class_hours[0].period),
            ("Friday", 1),
        )
        friday_first = [
            item
            for item in result.assignments
            if item.class_id == "5-A"
            and item.day == "Friday"
            and item.shift_id == "morning"
            and item.period == 1
        ]
        self.assertEqual(friday_first, class_hours)

    def test_early_subject_preference_is_used_when_feasible(self):
        request = self.base_request(
            classes=(SchoolClass("5-A", "morning", "101"),),
            demands=(
                LessonDemand("math", "5-A", "Matematika", "t-math", 3),
            ),
            subject_preferences=(
                SubjectPreference("Matematika", "early"),
            ),
        )
        result = generate_timetable(request)

        self.assertTrue(result.complete, result.hard_conflicts)
        self.assertTrue(all(item.period <= 3 for item in result.assignments))
        self.assertNotIn(
            "subject_outside_preferred_band",
            {item.code for item in result.quality_warnings},
        )

    def test_subject_shift_restriction_is_never_silently_ignored(self):
        request = self.base_request(
            classes=(SchoolClass("8-A", "afternoon", "101"),),
            demands=(
                LessonDemand(
                    "physics",
                    "8-A",
                    "Fizika",
                    "t-history",
                    2,
                    allowed_shift_ids=frozenset({"morning"}),
                ),
            ),
        )
        result = generate_timetable(request)

        self.assertEqual(result.assignments, ())
        self.assertIn(
            "subject_not_allowed_in_class_shift",
            {item.code for item in result.hard_conflicts},
        )

    def test_audit_detects_external_collision(self):
        request = self.base_request(
            classes=(
                SchoolClass("5-A", "morning", "101"),
                SchoolClass("5-B", "morning", "102"),
            ),
            demands=(),
        )
        assignments = (
            Assignment(
                "Monday", "morning", 1, "5-A", "Matematika", "t-math", "101"
            ),
            Assignment(
                "Monday", "morning", 1, "5-B", "Matematika", "t-math", "102"
            ),
        )
        conflicts = audit_assignments(request, assignments)

        self.assertIn("teacher_collision", {item.code for item in conflicts})

    def test_publication_audit_rejects_demand_tampering_and_bad_occurrence(self):
        request = TimetableRequest(
            days=("Monday",),
            shifts=(Shift("morning", (1,)),),
            classes=(SchoolClass("5-A", "morning"),),
            teachers=(Teacher("t-math"),),
            rooms=(),
            demands=(
                LessonDemand("math", "5-A", "Matematika", "t-math", 1),
            ),
        )
        tampered = (
            Assignment(
                "Monday",
                "morning",
                1,
                "5-A",
                "Tarix",
                "t-math",
                None,
                demand_id="math",
                occurrence_index=99,
            ),
        )

        codes = {item.code for item in audit_assignments(request, tampered)}

        self.assertIn("assignment_demand_mismatch", codes)
        self.assertIn("assignment_occurrence_out_of_range", codes)

    def test_publication_audit_requires_all_hours_but_draft_audit_does_not(self):
        request = TimetableRequest(
            days=("Monday",),
            shifts=(Shift("morning", (1,)),),
            classes=(SchoolClass("5-A", "morning"),),
            teachers=(Teacher("t-math"),),
            rooms=(),
            demands=(
                LessonDemand("math", "5-A", "Matematika", "t-math", 1),
            ),
        )

        publication_codes = {
            item.code for item in audit_assignments(request, ())
        }
        draft_codes = {
            item.code
            for item in audit_assignments(
                request,
                (),
                require_complete=False,
            )
        }

        self.assertIn("demand_assignment_missing", publication_codes)
        self.assertNotIn("demand_assignment_missing", draft_codes)

    def test_publication_audit_rejects_duplicate_occurrence_and_daily_overflow(self):
        request = TimetableRequest(
            days=("Monday", "Tuesday"),
            shifts=(Shift("morning", (1, 2)),),
            classes=(SchoolClass("5-A", "morning"),),
            teachers=(Teacher("t-math"),),
            rooms=(),
            demands=(
                LessonDemand(
                    "math",
                    "5-A",
                    "Matematika",
                    "t-math",
                    2,
                    max_per_day=1,
                ),
            ),
        )
        assignments = (
            Assignment(
                "Monday",
                "morning",
                1,
                "5-A",
                "Matematika",
                "t-math",
                None,
                demand_id="math",
                occurrence_index=1,
            ),
            Assignment(
                "Monday",
                "morning",
                2,
                "5-A",
                "Matematika",
                "t-math",
                None,
                demand_id="math",
                occurrence_index=1,
            ),
        )

        codes = {item.code for item in audit_assignments(request, assignments)}

        self.assertIn("duplicate_assignment_occurrence", codes)
        self.assertIn("demand_daily_limit_exceeded", codes)

    def test_publication_audit_requires_configured_class_hour(self):
        request = TimetableRequest(
            days=DAYS,
            shifts=(MORNING,),
            classes=(
                SchoolClass(
                    "5-A",
                    "morning",
                    class_teacher_id="t-class",
                    class_hour=ClassHourRule("Friday", 1),
                ),
            ),
            teachers=(Teacher("t-class"),),
            rooms=(),
            demands=(),
        )

        codes = {item.code for item in audit_assignments(request, ())}

        self.assertIn("class_hour_assignment_missing", codes)

    def test_exact_failure_preserves_unrelated_feasible_assignment(self):
        request = TimetableRequest(
            days=("Monday",),
            shifts=(Shift("morning", (1, 2)),),
            classes=(
                SchoolClass("5-A", "morning"),
                SchoolClass("5-B", "morning"),
            ),
            teachers=(Teacher("t-bad"), Teacher("t-good")),
            rooms=(
                Room(
                    "math-room",
                    allowed_subjects=frozenset({"Matematika"}),
                ),
            ),
            demands=(
                LessonDemand("bad", "5-A", "Tarix", "t-bad", 1),
                LessonDemand("good", "5-B", "Matematika", "t-good", 1),
            ),
        )

        result = generate_timetable(request)

        self.assertFalse(result.complete)
        self.assertEqual(
            {item.demand_id for item in result.assignments},
            {"good"},
        )
        self.assertEqual(
            {
                item.entity_id
                for item in result.hard_conflicts
                if item.code == "unscheduled_lesson_hours"
            },
            {"bad"},
        )

    def test_method_day_typo_is_rejected_instead_of_ignored(self):
        request = TimetableRequest(
            days=("Friday",),
            shifts=(Shift("morning", (1,)),),
            classes=(SchoolClass("5-A", "morning"),),
            teachers=(
                Teacher("t-math", method_days=frozenset({"Fryday"})),
            ),
            rooms=(),
            demands=(
                LessonDemand("math", "5-A", "Matematika", "t-math", 1),
            ),
        )

        result = generate_timetable(request)

        self.assertEqual(result.assignments, ())
        self.assertIn(
            "teacher_unknown_method_day",
            {item.code for item in result.hard_conflicts},
        )

    def test_overlapping_clock_shifts_collide_for_same_teacher(self):
        morning = Shift("morning", (1,), {1: (480, 525)})
        afternoon = Shift("afternoon", (1,), {1: (500, 545)})
        request = TimetableRequest(
            days=("Monday",),
            shifts=(morning, afternoon),
            classes=(
                SchoolClass("5-A", "morning", "101"),
                SchoolClass("8-A", "afternoon", "201"),
            ),
            teachers=(Teacher("t-math"),),
            rooms=(Room("101"), Room("201")),
            demands=(
                LessonDemand("m1", "5-A", "Matematika", "t-math", 1, ("101",)),
                LessonDemand("m2", "8-A", "Matematika", "t-math", 1, ("201",)),
            ),
        )

        result = generate_timetable(request)

        self.assertFalse(result.complete)
        self.assertEqual(len(result.assignments), 1)
        self.assertEqual(
            sum(item.missing_hours for item in result.hard_conflicts),
            1,
        )

    def test_class_hour_policy_is_configurable_and_enforced(self):
        request = TimetableRequest(
            days=("Thursday", "Friday"),
            shifts=(Shift("morning", (1, 2)),),
            classes=(
                SchoolClass(
                    "5-A",
                    "morning",
                    class_teacher_id="t-class",
                    class_hour=ClassHourRule("Friday", 2),
                ),
            ),
            teachers=(Teacher("t-class"),),
            rooms=(),
            demands=(),
            class_hour_policy=ClassHourPolicy("Friday", 1),
        )

        result = generate_timetable(request)

        self.assertIn(
            "class_hour_policy_mismatch",
            {item.code for item in result.hard_conflicts},
        )

    def test_search_and_unit_limits_reject_work_before_search(self):
        over_node_limit = self.base_request(
            max_search_nodes=MAX_SEARCH_NODES + 1,
        )
        over_exact_limit = self.base_request(
            exact_search_max_units=MAX_EXACT_SEARCH_UNITS + 1,
        )
        over_weekly_limit = TimetableRequest(
            days=("Monday",),
            shifts=(
                Shift(
                    "morning",
                    tuple(range(1, MAX_WEEKLY_HOURS_PER_DEMAND + 2)),
                ),
            ),
            classes=(SchoolClass("5-A", "morning"),),
            teachers=(Teacher("t"),),
            rooms=(),
            demands=(
                LessonDemand(
                    "too-large",
                    "5-A",
                    "Fan",
                    "t",
                    MAX_WEEKLY_HOURS_PER_DEMAND + 1,
                ),
            ),
        )
        demand_count = 100
        over_capacity_limit = TimetableRequest(
            days=DAYS,
            shifts=(Shift("morning", tuple(range(1, 9))),),
            classes=tuple(
                SchoolClass(f"C-{index}", "morning")
                for index in range(demand_count)
            ),
            teachers=tuple(
                Teacher(f"T-{index}")
                for index in range(demand_count)
            ),
            rooms=tuple(Room(f"R-{index}") for index in range(40)),
            demands=tuple(
                LessonDemand(
                    f"D-{index}",
                    f"C-{index}",
                    f"Fan-{index}",
                    f"T-{index}",
                    40,
                )
                for index in range(demand_count)
            ),
        )

        node_result = generate_timetable(over_node_limit)
        exact_result = generate_timetable(over_exact_limit)
        weekly_result = generate_timetable(over_weekly_limit)
        capacity_result = generate_timetable(over_capacity_limit)

        self.assertEqual(node_result.search_nodes, 0)
        self.assertIn(
            "invalid_search_node_limit",
            {item.code for item in node_result.hard_conflicts},
        )
        self.assertEqual(exact_result.search_nodes, 0)
        self.assertIn(
            "invalid_exact_search_limit",
            {item.code for item in exact_result.hard_conflicts},
        )
        self.assertEqual(weekly_result.search_nodes, 0)
        self.assertIn(
            "weekly_hours_limit_exceeded",
            {item.code for item in weekly_result.hard_conflicts},
        )
        self.assertEqual(capacity_result.search_nodes, 0)
        self.assertIn(
            "workspace_generation_capacity_exceeded",
            {item.code for item in capacity_result.hard_conflicts},
        )
        self.assertGreater(MAX_CANDIDATE_EVALUATIONS, 0)


class CalendarMakeupTests(unittest.TestCase):
    def test_existing_effective_makeup_occupies_target_slot(self):
        original = CalendarLesson(
            "math-original",
            date(2026, 9, 1),
            "morning",
            1,
            "5-A",
            "Matematika",
            "t-math",
            "101",
        )
        existing_makeup = CalendarLesson(
            "existing-makeup",
            date(2026, 9, 2),
            "morning",
            1,
            "5-A",
            "Matematika",
            "t-math",
            "101",
        )
        request = MakeupRequest(
            lessons=(original, existing_makeup),
            cancellations=(Cancellation("math-original", "Bayram"),),
            candidate_dates=(date(2026, 9, 2),),
            shifts=(Shift("morning", (1, 2)),),
            teachers=(Teacher("t-math"),),
            rooms=(Room("101"),),
            day_labels=(
                CalendarDayLabel(date(2026, 9, 1), "Tuesday"),
                CalendarDayLabel(date(2026, 9, 2), "Wednesday"),
            ),
            allow_topic_compression=False,
        )

        result = plan_calendar_makeups(request)

        self.assertTrue(result.complete, result.hard_conflicts)
        self.assertEqual(len(result.placements), 1)
        self.assertEqual(result.placements[0].period, 2)

    def test_cancelled_lesson_is_retained_and_moved_to_later_day(self):
        original = CalendarLesson(
            "math-1",
            date(2026, 9, 1),
            "morning",
            1,
            "5-A",
            "Matematika",
            "t-math",
            "101",
            status="cancelled",
        )
        request = MakeupRequest(
            lessons=(original,),
            cancellations=(Cancellation("math-1", "Bayram"),),
            candidate_dates=(date(2026, 9, 2), date(2026, 9, 3)),
            shifts=(Shift("morning", (1, 2, 3)),),
            teachers=(Teacher("t-math"),),
            rooms=(Room("101"),),
            day_labels=(
                CalendarDayLabel(date(2026, 9, 2), "Wednesday"),
                CalendarDayLabel(date(2026, 9, 3), "Thursday"),
            ),
        )
        result = plan_calendar_makeups(request)

        self.assertTrue(result.complete, result.hard_conflicts)
        self.assertEqual(result.original_lessons, (original,))
        self.assertEqual(len(result.placements), 1)
        self.assertEqual(result.placements[0].mode, "extra_period")
        self.assertEqual(result.placements[0].target_date, date(2026, 9, 2))
        self.assertTrue(result.requires_human_approval)
        self.assertFalse(result.ready_to_publish)
        self.assertTrue(result.placements[0].requires_human_approval)
        self.assertIn(
            "calendar_makeup_added",
            {item.code for item in result.quality_warnings},
        )

    def test_no_free_slot_uses_explicit_same_subject_compression(self):
        cancelled = CalendarLesson(
            "math-missed",
            date(2026, 9, 1),
            "morning",
            1,
            "5-A",
            "Matematika",
            "t-math",
            "101",
            status="cancelled",
        )
        later_math = CalendarLesson(
            "math-later",
            date(2026, 9, 2),
            "morning",
            1,
            "5-A",
            "Matematika",
            "t-math",
            "101",
        )
        # Every period is occupied by the class, so an additional physical
        # lesson cannot be inserted without a collision.
        occupied = (
            later_math,
            CalendarLesson(
                "other-2",
                date(2026, 9, 2),
                "morning",
                2,
                "5-A",
                "Tarix",
                "t-history",
                "101",
            ),
        )
        request = MakeupRequest(
            lessons=(cancelled, *occupied),
            cancellations=(Cancellation("math-missed", "Prezident qarori"),),
            candidate_dates=(date(2026, 9, 2),),
            shifts=(Shift("morning", (1, 2)),),
            teachers=(Teacher("t-math"), Teacher("t-history")),
            rooms=(Room("101"),),
            day_labels=(
                CalendarDayLabel(date(2026, 9, 2), "Wednesday"),
            ),
            allow_topic_compression=True,
        )
        result = plan_calendar_makeups(request)

        self.assertTrue(result.complete, result.hard_conflicts)
        self.assertEqual(result.original_lessons, request.lessons)
        self.assertEqual(len(result.placements), 1)
        placement = result.placements[0]
        self.assertEqual(placement.mode, "compressed")
        self.assertEqual(placement.target_lesson_id, "math-later")
        self.assertTrue(result.requires_human_approval)
        self.assertFalse(result.ready_to_publish)
        self.assertIn(
            "topic_compression",
            {item.code for item in result.quality_warnings},
        )

    def test_unplaceable_makeup_is_reported_and_not_deleted(self):
        original = CalendarLesson(
            "physics-1",
            date(2026, 9, 1),
            "morning",
            1,
            "8-A",
            "Fizika",
            "t-physics",
            status="cancelled",
        )
        request = MakeupRequest(
            lessons=(original,),
            cancellations=(Cancellation("physics-1", "Favqulodda tanaffus"),),
            candidate_dates=(date(2026, 9, 2),),
            shifts=(Shift("morning", (1,)),),
            teachers=(
                Teacher("t-physics", method_days=frozenset({"Wednesday"})),
            ),
            day_labels=(
                CalendarDayLabel(date(2026, 9, 2), "Wednesday"),
            ),
            allow_topic_compression=False,
        )
        result = plan_calendar_makeups(request)

        self.assertFalse(result.complete)
        self.assertEqual(result.original_lessons, (original,))
        self.assertEqual(result.placements, ())
        self.assertIn(
            "makeup_unscheduled",
            {item.code for item in result.hard_conflicts},
        )

    def test_corrupt_base_calendar_collision_is_not_reported_complete(self):
        request = MakeupRequest(
            lessons=(
                CalendarLesson(
                    "math",
                    date(2026, 9, 1),
                    "morning",
                    1,
                    "5-A",
                    "Matematika",
                    "t-math",
                    "101",
                ),
                CalendarLesson(
                    "history",
                    date(2026, 9, 1),
                    "morning",
                    1,
                    "5-A",
                    "Tarix",
                    "t-history",
                    "102",
                ),
            ),
            cancellations=(),
            candidate_dates=(),
            shifts=(Shift("morning", (1,)),),
            teachers=(Teacher("t-math"), Teacher("t-history")),
            rooms=(Room("101"), Room("102")),
        )

        result = plan_calendar_makeups(request)

        self.assertFalse(result.complete)
        self.assertIn(
            "calendar_class_collision",
            {item.code for item in result.hard_conflicts},
        )

    def test_base_calendar_teacher_and_room_collisions_are_hard_conflicts(self):
        request = MakeupRequest(
            lessons=(
                CalendarLesson(
                    "a",
                    date(2026, 9, 1),
                    "morning",
                    1,
                    "5-A",
                    "Matematika",
                    "shared-teacher",
                    "101",
                ),
                CalendarLesson(
                    "b",
                    date(2026, 9, 1),
                    "morning",
                    1,
                    "5-B",
                    "Matematika",
                    "shared-teacher",
                    "102",
                ),
                CalendarLesson(
                    "c",
                    date(2026, 9, 1),
                    "morning",
                    1,
                    "6-A",
                    "Tarix",
                    "t-history",
                    "201",
                ),
                CalendarLesson(
                    "d",
                    date(2026, 9, 1),
                    "morning",
                    1,
                    "6-B",
                    "Tarix",
                    "t-other",
                    "201",
                ),
            ),
            cancellations=(),
            candidate_dates=(),
            shifts=(Shift("morning", (1,)),),
            teachers=(
                Teacher("shared-teacher"),
                Teacher("t-history"),
                Teacher("t-other"),
            ),
            rooms=(Room("101"), Room("102"), Room("201")),
        )

        result = plan_calendar_makeups(request)
        codes = {item.code for item in result.hard_conflicts}

        self.assertFalse(result.complete)
        self.assertIn("calendar_teacher_collision", codes)
        self.assertIn("calendar_room_collision", codes)

    def test_cancelled_status_without_cancellation_record_is_hard_conflict(self):
        original = CalendarLesson(
            "math",
            date(2026, 9, 1),
            "morning",
            1,
            "5-A",
            "Matematika",
            "t-math",
            status="cancelled",
        )
        request = MakeupRequest(
            lessons=(original,),
            cancellations=(),
            candidate_dates=(date(2026, 9, 2),),
            shifts=(Shift("morning", (1,)),),
            teachers=(Teacher("t-math"),),
        )

        result = plan_calendar_makeups(request)

        self.assertFalse(result.complete)
        self.assertEqual(result.placements, ())
        self.assertIn(
            "orphan_cancelled_lesson",
            {item.code for item in result.hard_conflicts},
        )

    def test_missing_original_room_returns_conflict_instead_of_key_error(self):
        original = CalendarLesson(
            "math",
            date(2026, 9, 1),
            "morning",
            1,
            "5-A",
            "Matematika",
            "t-math",
            "missing-room",
            status="cancelled",
        )
        request = MakeupRequest(
            lessons=(original,),
            cancellations=(Cancellation("math", "Bayram"),),
            candidate_dates=(date(2026, 9, 2),),
            shifts=(Shift("morning", (1,)),),
            teachers=(Teacher("t-math"),),
            rooms=(Room("101"),),
        )

        result = plan_calendar_makeups(request)

        self.assertFalse(result.complete)
        self.assertEqual(result.placements, ())
        self.assertIn(
            "calendar_lesson_unknown_room",
            {item.code for item in result.hard_conflicts},
        )

    def test_invalid_compression_target_period_is_structured_conflict(self):
        missed = CalendarLesson(
            "missed",
            date(2026, 9, 1),
            "morning",
            1,
            "5-A",
            "Matematika",
            "t-math",
            status="cancelled",
        )
        invalid_target = CalendarLesson(
            "future",
            date(2026, 9, 2),
            "morning",
            99,
            "5-A",
            "Matematika",
            "t-math",
        )
        request = MakeupRequest(
            lessons=(missed, invalid_target),
            cancellations=(Cancellation("missed", "Bayram"),),
            candidate_dates=(date(2026, 9, 2),),
            shifts=(Shift("morning", (1,)),),
            teachers=(Teacher("t-math"),),
        )

        result = plan_calendar_makeups(request)

        self.assertFalse(result.complete)
        self.assertIn(
            "calendar_lesson_unknown_slot",
            {item.code for item in result.hard_conflicts},
        )

    def test_overlapping_clock_shifts_are_checked_for_calendar_makeups(self):
        morning = Shift("morning", (1,), {1: (480, 525)})
        afternoon = Shift("afternoon", (1,), {1: (500, 545)})
        missed = CalendarLesson(
            "missed",
            date(2026, 9, 1),
            "morning",
            1,
            "5-A",
            "Matematika",
            "t-math",
            "101",
            status="cancelled",
        )
        occupied = CalendarLesson(
            "occupied",
            date(2026, 9, 2),
            "afternoon",
            1,
            "8-A",
            "Tarix",
            "t-math",
            "201",
        )
        request = MakeupRequest(
            lessons=(missed, occupied),
            cancellations=(Cancellation("missed", "Bayram"),),
            candidate_dates=(date(2026, 9, 2),),
            shifts=(morning, afternoon),
            teachers=(Teacher("t-math"),),
            rooms=(Room("101"), Room("201")),
            allow_topic_compression=False,
        )

        result = plan_calendar_makeups(request)

        self.assertFalse(result.complete)
        self.assertEqual(result.placements, ())
        self.assertIn(
            "makeup_unscheduled",
            {item.code for item in result.hard_conflicts},
        )


if __name__ == "__main__":
    unittest.main()
