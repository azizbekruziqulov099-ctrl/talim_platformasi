import unittest
from pathlib import Path

from backend.modules.test_games import (
    MAX_GAME_TIME_SECONDS,
    MIN_GAME_TIME_SECONDS,
    bounded_question_time_limit,
    boss_attempt_limit,
    grade_band_for_value,
    initial_lives_for_band,
    is_applicant_value,
    is_terminal_boss_failure,
    normalize_grade_band,
    score_game_rows,
    timeout_transition,
)


ROOT = Path(__file__).resolve().parents[2]


class GamifiedTestRules(unittest.TestCase):
    def test_grade_bands_and_boss_attempts(self):
        self.assertEqual(grade_band_for_value("4-sinf"), "grade_1_4")
        self.assertEqual(grade_band_for_value("5-sinf"), "grade_5_9")
        self.assertEqual(grade_band_for_value("9"), "grade_5_9")
        self.assertEqual(grade_band_for_value("11-sinf"), "grade_10_11")
        self.assertEqual(grade_band_for_value("Abituriyent"), "applicant")
        self.assertEqual(boss_attempt_limit("grade_1_4"), 3)
        self.assertEqual(boss_attempt_limit("grade_5_9"), 3)
        self.assertEqual(boss_attempt_limit("grade_10_11"), 2)
        self.assertEqual(boss_attempt_limit("applicant"), 2)
        self.assertEqual(normalize_grade_band("grade_1_5"), "grade_1_4")
        self.assertEqual(normalize_grade_band("grade_6_9"), "grade_5_9")
        self.assertTrue(is_applicant_value("Abituriyent"))
        self.assertFalse(is_applicant_value("11-sinf"))

    def test_age_lives_and_bounded_authoritative_time(self):
        self.assertEqual(initial_lives_for_band("grade_1_4"), 3)
        self.assertEqual(initial_lives_for_band("grade_5_9"), 3)
        self.assertEqual(initial_lives_for_band("grade_10_11"), 2)
        self.assertEqual(initial_lives_for_band("applicant"), 2)
        self.assertEqual(bounded_question_time_limit(5, "oson"), MIN_GAME_TIME_SECONDS)
        self.assertEqual(bounded_question_time_limit(999, "oson"), MAX_GAME_TIME_SECONDS)
        self.assertEqual(bounded_question_time_limit(None, "oson"), 60)
        self.assertEqual(bounded_question_time_limit(None, "o‘rta"), 75)
        self.assertEqual(bounded_question_time_limit(None, "murakkab", True), 150)
        self.assertEqual(bounded_question_time_limit(30, "murakkab", True), 30)
        self.assertEqual(bounded_question_time_limit("20.5", "oson"), 21)
        self.assertEqual(bounded_question_time_limit("1e2", "oson"), 60)
        self.assertEqual(bounded_question_time_limit(float("inf"), "oson"), 60)

    def test_timeout_transition_regular_life_and_boss_attempts(self):
        regular = timeout_transition(
            is_boss=False, attempts_used=0, max_attempts=1, lives_remaining=3
        )
        self.assertEqual(regular["outcome"], "advance")
        self.assertEqual(regular["lives_remaining"], 2)
        last_life = timeout_transition(
            is_boss=False, attempts_used=0, max_attempts=1, lives_remaining=1
        )
        self.assertEqual(last_life["outcome"], "game_over_lives")
        self.assertEqual(last_life["lives_remaining"], 0)

        boss_retry = timeout_transition(
            is_boss=True, attempts_used=1, max_attempts=3, lives_remaining=3
        )
        self.assertEqual(boss_retry["outcome"], "boss_retry")
        self.assertEqual(boss_retry["attempts_used"], 2)
        self.assertEqual(boss_retry["lives_remaining"], 3)
        boss_terminal = timeout_transition(
            is_boss=True, attempts_used=2, max_attempts=3, lives_remaining=3
        )
        self.assertEqual(boss_terminal["outcome"], "game_over_boss")
        self.assertEqual(boss_terminal["attempts_left"], 0)
        self.assertFalse(
            is_terminal_boss_failure(
                is_boss=True, correct=False, attempts_used=2, max_attempts=3
            )
        )
        self.assertTrue(
            is_terminal_boss_failure(
                is_boss=True, correct=False, attempts_used=3, max_attempts=3
            )
        )
        self.assertFalse(
            is_terminal_boss_failure(
                is_boss=True, correct=True, attempts_used=3, max_attempts=3
            )
        )

    def test_perfect_round_is_exactly_1000(self):
        rows = [
            {"is_boss": False, "correct": True, "attempts_used": 1, "answered_at": "now"}
            for _ in range(4)
        ] + [
            {"is_boss": True, "correct": True, "attempts_used": 1, "answered_at": "now"}
        ]
        result = score_game_rows(rows, completed=True, lifelines_used=0)
        self.assertEqual(result["score_1000"], 1000)
        self.assertTrue(result["perfect"])

    def test_lifeline_and_second_try_remove_mastery_bonus(self):
        rows = [
            {"is_boss": False, "correct": True, "attempts_used": 1, "answered_at": "now"},
            {"is_boss": False, "correct": True, "attempts_used": 1, "answered_at": "now"},
            {"is_boss": False, "correct": True, "attempts_used": 1, "answered_at": "now"},
            {"is_boss": False, "correct": False, "attempts_used": 1, "answered_at": "now"},
            {"is_boss": True, "correct": True, "attempts_used": 2, "answered_at": "now"},
        ]
        result = score_game_rows(rows, completed=True, lifelines_used=1)
        self.assertEqual(result["regular_points"], 375)
        self.assertEqual(result["boss_points"], 200)
        self.assertEqual(result["completion_points"], 100)
        self.assertEqual(result["mastery_bonus"], 0)
        self.assertEqual(result["score_1000"], 675)

    def test_terminal_game_over_cannot_receive_completion_or_mastery_bonus(self):
        rows = [
            {"is_boss": False, "correct": True, "attempts_used": 1, "answered_at": "now"}
            for _ in range(4)
        ] + [
            {"is_boss": True, "correct": False, "attempts_used": 3, "answered_at": "now"}
        ]
        result = score_game_rows(rows, completed=False, lifelines_used=0)
        self.assertEqual(result["completion_points"], 0)
        self.assertEqual(result["mastery_bonus"], 0)
        self.assertFalse(result["perfect"])


class GamifiedTestContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = (ROOT / "backend" / "modules" / "test_games.py").read_text(encoding="utf-8")
        cls.main = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
        cls.migration = (ROOT / "database" / "015_gamified_tests.sql").read_text(encoding="utf-8")
        cls.timer_migration = (ROOT / "database" / "016_game_timers.sql").read_text(encoding="utf-8")

    def test_server_owned_session_and_race_locks(self):
        for route in (
            '@router.post("/boshlash")',
            '@router.post("/javob")',
            '@router.post("/yordam")',
            '@router.post("/tayyor")',
            '@router.post("/vaqt-tugadi")',
            '@router.post("/yakunlash")',
            '@router.post("/kunlik-kirish")',
        ):
            self.assertIn(route, self.module)
        self.assertGreaterEqual(self.module.count("FOR UPDATE"), 5)
        self.assertIn("question_key", self.module)
        self.assertIn("game_session_questions", self.module)
        self.assertIn("question_snapshot", self.module)
        self.assertIn("game_actions", self.module)
        self.assertIn("action_id", self.module)

    def test_ready_handshake_prevents_unseen_timer_burn(self):
        self.assertIn("def activate_question_timer", self.module)
        self.assertIn("deadline_at=COALESCE", self.module)
        self.assertIn("clock_timestamp()", self.module)
        self.assertIn("WHEN deadline_at IS NULL THEN 'waiting'", self.module)
        self.assertIn('action_type="ready"', self.module)
        self.assertIn("timer_started_at=NULL,deadline_at=NULL", self.module)
        self.assertIn("question_payload(cur, session, row)", self.module)
        self.assertIn("/tayyor", self.timer_migration)

    def test_server_deadline_timeout_is_idempotent_and_terminal_without_reward(self):
        self.assertIn("QUESTION_TIME_EXPIRED", self.module)
        self.assertIn("TIMER_STILL_ACTIVE", self.module)
        self.assertIn('action_type="timeout"', self.module)
        self.assertIn('terminal_status="game_over"', self.module)
        self.assertIn('terminal_reason="lives_exhausted"', self.module)
        self.assertIn('terminal_reason="boss_attempts_exhausted"', self.module)
        self.assertIn("completed=False", self.module)
        self.assertIn("timed_out=TRUE", self.module)
        self.assertNotIn("elapsed_seconds", self.module)

    def test_016_compatibility_schema_and_age_migration(self):
        for fragment in (
            "initial_lives SMALLINT",
            "lives_remaining SMALLINT",
            "time_limit_seconds SMALLINT",
            "timer_started_at TIMESTAMPTZ",
            "deadline_at TIMESTAMPTZ",
            "'game_over'",
            "'grade_1_4'",
            "'grade_5_9'",
            "'ready','timeout'",
            "016_game_timers",
        ):
            self.assertIn(fragment, self.timer_migration)
        self.assertIn("UPDATE game_sessions s", self.timer_migration)
        self.assertIn("deadline_at=NULL", self.timer_migration)
        self.assertIn("samtm_016_upgrade_state", self.timer_migration)

    def test_four_choice_plus_one_boss_and_lifelines(self):
        self.assertIn("for _ in range(4)", self.module)
        self.assertIn('"fifty_fifty"', self.module)
        self.assertIn('"remove_one"', self.module)
        self.assertIn("remove_count = 2", self.module)
        self.assertIn("display_correct_letter", self.module)

    def test_points_are_append_only_and_daily_is_tashkent_based(self):
        self.assertIn("game_point_ledger", self.migration)
        self.assertIn("trg_game_point_ledger_immutable", self.migration)
        self.assertIn("BEFORE UPDATE OR DELETE", self.migration)
        self.assertIn("Asia/Tashkent", self.module)
        self.assertIn("UNIQUE(user_id,reference_key)", self.migration)
        self.assertIn("standard_test_attempts", self.migration)
        self.assertIn("canonical_subjects", self.module)
        self.assertIn("missing_codes", self.module)

    def test_classic_test_also_receives_capped_best_improvement_points(self):
        self.assertIn("award_standard_test_points", self.main)
        self.assertIn('mode="standard"', self.module)
        self.assertIn("previous_score", self.module)
        self.assertIn("improvement_xp", self.module)
        self.assertIn("_standard_urinish_yarat", self.main)
        self.assertIn("server_content_key=standard_content_key", self.main)

    def test_question_deletion_does_not_break_snapshot_sessions(self):
        question_line = next(
            line.strip()
            for line in self.migration.splitlines()
            if line.strip().startswith("question_id INTEGER")
        )
        self.assertEqual(question_line, "question_id INTEGER NOT NULL,")
        self.assertIn("question_snapshot JSONB NOT NULL", self.migration)

    def test_abandoned_game_does_not_update_mastery(self):
        self.assertIn("update_mastery=completed", self.module)
        self.assertIn("delivery_mode", self.module)


if __name__ == "__main__":
    unittest.main()
