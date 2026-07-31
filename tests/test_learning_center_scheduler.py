"""Pure tests for learning-center recurring/dated conflict helpers."""

from __future__ import annotations

import unittest
from datetime import date, time

from backend.modules.learning_center_scheduler import (
    ScheduleSlot,
    expand_weekly_slots,
    find_conflicts,
)


class LearningCenterSchedulerTests(unittest.TestCase):
    def test_teacher_collision_is_cross_group(self):
        slots = [
            ScheduleSlot(1, "weekly", time(14), time(15, 30), 7, 10, 100, 1),
            ScheduleSlot(2, "weekly", time(15), time(16), 7, 11, 101, 1),
        ]
        self.assertEqual(
            [item.resource for item in find_conflicts(slots)],
            ["teacher"],
        )

    def test_group_and_room_collisions_are_reported(self):
        slots = [
            ScheduleSlot(1, "dated", time(9), time(10), 1, 10, 100,
                         lesson_date=date(2026, 9, 1)),
            ScheduleSlot(2, "dated", time(9, 30), time(11), 2, 10, 100,
                         lesson_date=date(2026, 9, 1)),
        ]
        self.assertEqual(
            {item.resource for item in find_conflicts(slots)},
            {"group", "room"},
        )

    def test_weekly_and_dated_same_weekday_collide(self):
        slots = [
            ScheduleSlot(1, "weekly", time(12), time(13), 5, 10, weekday=2),
            ScheduleSlot(
                2, "dated", time(12, 30), time(14), 5, 11,
                lesson_date=date(2026, 9, 1),
            ),
        ]
        self.assertEqual(find_conflicts(slots)[0].resource, "teacher")

    def test_expansion_is_inclusive_and_bounded(self):
        slot = ScheduleSlot(
            1, "weekly", time(10), time(11), 5, 10, weekday=1
        )
        expanded = expand_weekly_slots(
            [slot], date(2026, 8, 31), date(2026, 9, 14)
        )
        self.assertEqual(
            [item[0] for item in expanded],
            [date(2026, 8, 31), date(2026, 9, 7), date(2026, 9, 14)],
        )
        with self.assertRaises(ValueError):
            expand_weekly_slots(
                [slot], date(2026, 1, 1), date(2027, 2, 1)
            )


if __name__ == "__main__":
    unittest.main()
