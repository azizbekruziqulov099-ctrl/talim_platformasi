import ast
import unittest
import sys
import types
from pathlib import Path

# Bu fayldagi sof qoidalar va manba kontraktlari DB drayverini ishlatmaydi.
# Minimal test runtime'da psycopg2 bo'lmasa ham modulni import qila olamiz;
# production backend o'z requirements fayli orqali haqiqiy drayverni oladi.
try:
    import psycopg2.extras  # noqa: F401
except ModuleNotFoundError:
    psycopg2_stub = types.ModuleType("psycopg2")
    psycopg2_extras_stub = types.ModuleType("psycopg2.extras")
    psycopg2_extras_stub.execute_values = None
    psycopg2_stub.extras = psycopg2_extras_stub
    sys.modules["psycopg2"] = psycopg2_stub
    sys.modules["psycopg2.extras"] = psycopg2_extras_stub

try:
    import fastapi  # noqa: F401
except ModuleNotFoundError:
    fastapi_stub = types.ModuleType("fastapi")

    class APIRouterStub:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, *args, **kwargs):
            return lambda func: func

        post = get

    class HTTPExceptionStub(Exception):
        def __init__(self, status_code=None, detail=None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    fastapi_stub.APIRouter = APIRouterStub
    fastapi_stub.HTTPException = HTTPExceptionStub
    sys.modules["fastapi"] = fastapi_stub

try:
    import pydantic  # noqa: F401
except ModuleNotFoundError:
    pydantic_stub = types.ModuleType("pydantic")

    class BaseModelStub:
        pass

    def field_stub(default=None, *, default_factory=None, **kwargs):
        return default_factory() if default_factory else default

    pydantic_stub.BaseModel = BaseModelStub
    pydantic_stub.Field = field_stub
    sys.modules["pydantic"] = pydantic_stub

try:
    from backend.modules.test_games import (
        MAX_GAME_TIME_SECONDS,
        MIN_GAME_TIME_SECONDS,
        answer_life_transition,
        bounded_question_time_limit,
        boss_attempt_limit,
        grade_band_for_value,
        initial_lives_for_band,
        is_applicant_value,
        numeric_answer_choices,
        normalize_grade_band,
        score_game_rows,
        timeout_transition,
    )
except ModuleNotFoundError:  # backend-only repository: tests va modules yonma-yon
    from modules.test_games import (
        MAX_GAME_TIME_SECONDS,
        MIN_GAME_TIME_SECONDS,
        answer_life_transition,
        bounded_question_time_limit,
        boss_attempt_limit,
        grade_band_for_value,
        initial_lives_for_band,
        is_applicant_value,
        numeric_answer_choices,
        normalize_grade_band,
        score_game_rows,
        timeout_transition,
    )


TEST_FILE = Path(__file__).resolve()
BACKEND_ONLY_ROOT = TEST_FILE.parents[1]
FULLSTACK_ROOT = TEST_FILE.parents[2]
if (FULLSTACK_ROOT / "backend" / "modules" / "test_games.py").exists():
    PROJECT_ROOT = TEST_FILE.parents[2]
    BACKEND_ROOT = PROJECT_ROOT / "backend"
else:
    PROJECT_ROOT = BACKEND_ONLY_ROOT
    BACKEND_ROOT = BACKEND_ONLY_ROOT


class GamifiedTestRules(unittest.TestCase):
    def test_grade_bands_and_boss_attempts(self):
        self.assertEqual(grade_band_for_value("4-sinf"), "grade_1_4")
        self.assertEqual(grade_band_for_value("5-sinf"), "grade_5_9")
        self.assertEqual(grade_band_for_value("9"), "grade_5_9")
        self.assertEqual(grade_band_for_value("11-sinf"), "grade_10_11")
        self.assertEqual(grade_band_for_value("Abituriyent"), "applicant")
        self.assertEqual(boss_attempt_limit("grade_1_4"), 1)
        self.assertEqual(boss_attempt_limit("grade_5_9"), 1)
        self.assertEqual(boss_attempt_limit("grade_10_11"), 1)
        self.assertEqual(boss_attempt_limit("applicant"), 1)
        self.assertEqual(normalize_grade_band("grade_1_5"), "grade_1_4")
        self.assertEqual(normalize_grade_band("grade_6_9"), "grade_5_9")
        self.assertTrue(is_applicant_value("Abituriyent"))
        self.assertFalse(is_applicant_value("11-sinf"))

    def test_age_lives_and_bounded_authoritative_time(self):
        self.assertEqual(initial_lives_for_band("grade_1_4"), 3)
        self.assertEqual(initial_lives_for_band("grade_5_9"), 3)
        self.assertEqual(initial_lives_for_band("grade_10_11"), 3)
        self.assertEqual(initial_lives_for_band("applicant"), 3)
        self.assertEqual(bounded_question_time_limit(5, "oson"), MIN_GAME_TIME_SECONDS)
        self.assertEqual(bounded_question_time_limit(999, "oson"), MAX_GAME_TIME_SECONDS)
        self.assertEqual(bounded_question_time_limit(None, "oson"), 60)
        self.assertEqual(bounded_question_time_limit(None, "o‘rta"), 75)
        self.assertEqual(bounded_question_time_limit(None, "murakkab", True), 150)
        self.assertEqual(bounded_question_time_limit(30, "murakkab", True), 30)
        self.assertEqual(bounded_question_time_limit("20.5", "oson"), 21)
        self.assertEqual(bounded_question_time_limit("1e2", "oson"), 60)
        self.assertEqual(bounded_question_time_limit(float("inf"), "oson"), 60)

    def test_timeout_transition_always_loses_one_and_advances(self):
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

        old_boss_row = timeout_transition(
            is_boss=True, attempts_used=1, max_attempts=3, lives_remaining=3,
            position=4, total_questions=10,
        )
        self.assertEqual(old_boss_row["outcome"], "advance")
        self.assertEqual(old_boss_row["attempts_used"], 2)
        self.assertEqual(old_boss_row["attempts_left"], 0)
        self.assertEqual(old_boss_row["lives_remaining"], 2)

    def test_life_transition_loss_level_restore_and_cap(self):
        wrong = answer_life_transition(
            correct=False, position=2, total_questions=10, lives_remaining=3
        )
        self.assertEqual(wrong["lives_lost"], 1)
        self.assertEqual(wrong["lives_gained"], 0)
        self.assertEqual(wrong["lives_remaining"], 2)
        self.assertEqual(wrong["outcome"], "advance")

        level_restore = answer_life_transition(
            correct=True, position=5, total_questions=10, lives_remaining=2
        )
        self.assertTrue(level_restore["level_completed"])
        self.assertEqual(level_restore["lives_lost"], 0)
        self.assertEqual(level_restore["lives_gained"], 1)
        self.assertEqual(level_restore["lives_remaining"], 3)

        wrong_at_level_end = answer_life_transition(
            correct=False, position=5, total_questions=10, lives_remaining=2
        )
        self.assertEqual(wrong_at_level_end["lives_lost"], 1)
        self.assertEqual(wrong_at_level_end["lives_gained"], 1)
        self.assertEqual(wrong_at_level_end["lives_remaining"], 2)

        capped = answer_life_transition(
            correct=True, position=5, total_questions=10, lives_remaining=3
        )
        self.assertEqual(capped["lives_gained"], 0)
        self.assertEqual(capped["lives_remaining"], 3)

        exhausted = answer_life_transition(
            correct=False, position=5, total_questions=10, lives_remaining=1
        )
        self.assertEqual(exhausted["outcome"], "game_over_lives")
        self.assertEqual(exhausted["lives_gained"], 0)

    def test_only_pure_numeric_write_answers_get_safe_choices(self):
        self.assertEqual(
            numeric_answer_choices("12"),
            {
                "option_a": "12",
                "option_b": "13",
                "option_c": "11",
                "option_d": "14",
                "correct_answer": "A",
            },
        )
        decimal = numeric_answer_choices("3,5")
        self.assertEqual(decimal["option_a"], "3,5")
        self.assertEqual(len({decimal[f"option_{x}"] for x in "abcd"}), 4)
        self.assertIsNone(numeric_answer_choices("12 sm"))
        self.assertIsNone(numeric_answer_choices("x = 4"))
        self.assertIsNone(numeric_answer_choices("Toshkent"))

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
        cls.module = (BACKEND_ROOT / "modules" / "test_games.py").read_text(encoding="utf-8")
        cls.module_ast = ast.parse(cls.module)
        cls.main = (BACKEND_ROOT / "main.py").read_text(encoding="utf-8")
        cls.migration = (PROJECT_ROOT / "database" / "015_gamified_tests.sql").read_text(encoding="utf-8")
        cls.timer_migration = (PROJECT_ROOT / "database" / "016_game_timers.sql").read_text(encoding="utf-8")

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
        self.assertIn('response = {"ready": True, **session_summary(cur, session)}', self.module)
        self.assertIn("/tayyor", self.timer_migration)

    def test_server_deadline_timeout_is_idempotent_and_terminal_without_reward(self):
        self.assertIn("QUESTION_TIME_EXPIRED", self.module)
        self.assertIn("TIMER_STILL_ACTIVE", self.module)
        self.assertIn('action_type="timeout"', self.module)
        self.assertIn('terminal_status="game_over"', self.module)
        self.assertIn('terminal_reason="lives_exhausted"', self.module)
        self.assertIn("completed=False", self.module)
        self.assertIn("timed_out=TRUE", self.module)
        self.assertIn('"lives_lost": transition["lives_lost"]', self.module)
        self.assertIn('"lives_gained": transition["lives_gained"]', self.module)
        self.assertNotIn("elapsed_seconds", self.module)

    def test_timeout_save_action_signature_and_ready_replay_condition_are_not_duplicated(self):
        functions = {
            node.name: node
            for node in ast.walk(self.module_ast)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        timeout = functions["timeout_game_question"]
        timeout_save_calls = [
            node
            for node in ast.walk(timeout)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "save_action"
        ]
        self.assertEqual(len(timeout_save_calls), 1)
        self.assertEqual(len(timeout_save_calls[0].args), 1)
        self.assertIsInstance(timeout_save_calls[0].args[0], ast.Name)
        self.assertEqual(timeout_save_calls[0].args[0].id, "cur")

        ready = functions["ready_game_question"]
        replay_condition = "current and current['question_key'] == request.question_key"
        matching_conditions = [
            node
            for node in ast.walk(ready)
            if isinstance(node, ast.If) and ast.unparse(node.test) == replay_condition
        ]
        self.assertEqual(len(matching_conditions), 1)

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
        self.assertIn("for round_step in range(GAME_LEVEL_SIZE)", self.module)
        self.assertIn('question["topic_code"], "choice", round_step == GAME_LEVEL_SIZE - 1, 1', self.module)
        self.assertIn('"question_type": "single_choice" if is_choice_row(row)', self.module)
        self.assertIn("numeric_answer_choices", self.module)
        self.assertIn("excluded_write_count", self.module)
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
