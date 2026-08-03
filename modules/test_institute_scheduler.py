from __future__ import annotations

import unittest
from datetime import date, time

from modules.institute_scheduler import InstituteSlot, expand_slots, find_conflicts


class InstituteSchedulerTests(unittest.TestCase):
    def weekly(self, slot_id: int, **changes):
        values = {
            "slot_id": slot_id,
            "section_id": 10,
            "teacher_user_id": 20,
            "room_id": 30,
            "cohort_ids": (40,),
            "starts_at": time(9),
            "ends_at": time(10, 20),
            "kind": "weekly",
            "weekday": 1,
            "effective_from": date(2026, 9, 1),
            "effective_to": date(2026, 12, 31),
        }
        values.update(changes)
        return InstituteSlot(**values)

    def test_teacher_section_and_room_conflicts_are_reported(self):
        conflicts = find_conflicts([
            self.weekly(1),
            self.weekly(2, starts_at=time(10), ends_at=time(11)),
        ])
        self.assertEqual(
            {row.resource for row in conflicts},
            {"teacher", "section", "cohort", "room"},
        )

    def test_non_overlapping_effective_ranges_do_not_conflict(self):
        self.assertEqual(
            find_conflicts([
                self.weekly(1, effective_to=date(2026, 10, 1)),
                self.weekly(2, effective_from=date(2026, 10, 2)),
            ]),
            [],
        )

    def test_dated_slot_conflicts_with_matching_weekday(self):
        dated = InstituteSlot(
            slot_id=3, section_id=99, teacher_user_id=20, room_id=99,
            starts_at=time(9, 30), ends_at=time(10), kind="dated",
            lesson_date=date(2026, 9, 7),
        )
        resources = {row.resource for row in find_conflicts([self.weekly(1), dated])}
        self.assertEqual(resources, {"teacher"})

    def test_expand_is_bounded_and_respects_effective_range(self):
        rows = expand_slots([self.weekly(1)], date(2026, 9, 1), date(2026, 9, 30))
        self.assertEqual([row[0] for row in rows], [
            date(2026, 9, 7), date(2026, 9, 14), date(2026, 9, 21), date(2026, 9, 28),
        ])
        with self.assertRaises(ValueError):
            expand_slots([self.weekly(1)], date(2026, 1, 1), date(2027, 1, 3))

    def test_invalid_shapes_are_rejected(self):
        with self.assertRaises(ValueError):
            self.weekly(1, weekday=None)
        with self.assertRaises(ValueError):
            self.weekly(1, starts_at=time(10), ends_at=time(9))


if __name__ == "__main__":
    unittest.main()
