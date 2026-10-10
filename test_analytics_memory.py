import ast
from datetime import datetime, timedelta, timezone
import math
from pathlib import Path
import unittest


MAIN_PATH = Path(__file__).resolve().parents[1] / "main.py"
MAIN_SOURCE = MAIN_PATH.read_text(encoding="utf-8")


def _load_memory_function():
    tree = ast.parse(MAIN_SOURCE)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_analitika_xotira_hisobi"
    )
    namespace = {
        "datetime": datetime,
        "timezone": timezone,
        "math": math,
    }
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(MAIN_PATH), "exec"), namespace)
    return namespace["_analitika_xotira_hisobi"]


memory = _load_memory_function()


class AnalyticsMemoryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 13, 12, tzinfo=timezone.utc)

    def test_recent_strong_topic_stays_stable(self):
        result = memory(
            90,
            self.now - timedelta(days=5),
            attempts=4,
            review_interval_days=30,
            now=self.now,
        )
        self.assertEqual(result["memory_status"], "stable")
        self.assertLess(result["forgetting_probability"], 35)

    def test_old_weak_topic_is_marked_forgotten(self):
        result = memory(
            45,
            self.now - timedelta(days=5),
            attempts=1,
            review_interval_days=1,
            now=self.now,
        )
        self.assertEqual(result["memory_status"], "forgotten")
        self.assertGreaterEqual(result["forgetting_probability"], 65)

    def test_retest_recovery_is_explicit(self):
        result = memory(
            76,
            self.now,
            attempts=2,
            review_interval_days=7,
            previous_score=45,
            latest_score=82,
            now=self.now,
        )
        self.assertTrue(result["recovered_after_review"])
        self.assertEqual(result["memory_status"], "recovered")

    def test_university_data_is_scoped_to_active_student_membership(self):
        self.assertIn("active_membership.member_role='student'", MAIN_SOURCE)
        self.assertIn("active_membership.status='active'", MAIN_SOURCE)
        self.assertIn('"has_university_student_access"', MAIN_SOURCE)
        self.assertIn('c["type"] == "university"', MAIN_SOURCE)


if __name__ == "__main__":
    unittest.main()
