from __future__ import annotations

import unittest
from decimal import Decimal

from modules.institute_grades import (
    CreditResult,
    GradeBand,
    WeightedMark,
    calculate_gpa,
    select_grade_band,
    select_transcript_attempts,
    weighted_percent,
)


class InstituteGradeCalculations(unittest.TestCase):
    def test_weighted_percent_requires_exactly_one_hundred(self):
        rows = [
            WeightedMark(Decimal("80"), Decimal("100"), Decimal("40")),
            WeightedMark(Decimal("45"), Decimal("50"), Decimal("60")),
        ]
        self.assertEqual(weighted_percent(rows), Decimal("86.00"))
        with self.assertRaises(ValueError):
            weighted_percent(rows[:1])

    def test_mark_bounds_are_enforced(self):
        with self.assertRaises(ValueError):
            WeightedMark(Decimal("11"), Decimal("10"), Decimal("100"))
        with self.assertRaises(ValueError):
            WeightedMark(Decimal("1"), Decimal("0"), Decimal("100"))

    def test_grade_band_resolves_once(self):
        bands = [
            GradeBand(Decimal("0"), Decimal("59.99"), "F", Decimal("0"), False),
            GradeBand(Decimal("60"), Decimal("100"), "P", Decimal("3"), True),
        ]
        self.assertEqual(select_grade_band(Decimal("86.25"), bands).letter_grade, "P")
        with self.assertRaises(ValueError):
            select_grade_band(Decimal("59.995"), bands)

    def test_gpa_is_credit_weighted_and_includes_failed_attempted_credit(self):
        rows = [
            CreditResult(Decimal("6"), Decimal("4"), True),
            CreditResult(Decimal("3"), Decimal("2"), True),
            CreditResult(Decimal("3"), Decimal("0"), False),
        ]
        self.assertEqual(calculate_gpa(rows), Decimal("2.50"))

    def test_empty_gpa_is_zero(self):
        self.assertEqual(calculate_gpa([]), Decimal("0.00"))

    def test_transcript_retakes_are_selected_once_by_policy(self):
        rows = [
            {
                "id": 1, "course_id": 10, "course_code": "MAT",
                "finalized_at": "2026-01-01", "final_percent": 90,
                "grade_point": 4, "passed": True,
            },
            {
                "id": 2, "course_id": 10, "course_code": "MAT",
                "finalized_at": "2026-06-01", "final_percent": 70,
                "grade_point": 2, "passed": True,
            },
            {
                "id": 3, "course_id": 20, "course_code": "PHY",
                "finalized_at": "2026-06-02", "final_percent": 80,
                "grade_point": 3, "passed": True,
            },
        ]
        self.assertEqual(
            [row["id"] for row in select_transcript_attempts(rows, "latest")],
            [2, 3],
        )
        self.assertEqual(
            [row["id"] for row in select_transcript_attempts(rows, "best")],
            [1, 3],
        )
        self.assertEqual(len(select_transcript_attempts(rows, "all")), 3)
        self.assertEqual(
            [row["id"] for row in select_transcript_attempts(rows, "invalid")],
            [2, 3],
        )


if __name__ == "__main__":
    unittest.main()
