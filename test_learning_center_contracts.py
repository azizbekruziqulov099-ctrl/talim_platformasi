"""Static and payload contract tests for learning-center v2.

These tests do not need a PostgreSQL instance and never write production data.
They guard the route/frontend contract, tenant/privacy controls and migrations.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
ROUTER_FILE = BACKEND / "modules" / "learning_center.py"
APP_FILE = BACKEND / "main.py"
API_FILE = ROOT / "frontend" / "src" / "center" / "api.js"
MIGRATIONS = (
    ROOT / "database" / "007_learning_center_core.sql",
    ROOT / "database" / "008_learning_center_operations.sql",
)

def source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def function_source(name: str) -> str:
    text = source(ROUTER_FILE)
    tree = ast.parse(text)
    nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    if len(nodes) != 1:
        raise AssertionError(f"{name}: {len(nodes)} ta funksiya topildi")
    segment = ast.get_source_segment(text, nodes[0])
    if segment is None:
        raise AssertionError(f"{name}: manba olinmadi")
    return segment


def routes() -> list[tuple[str, str, str, bool]]:
    text = source(ROUTER_FILE)
    tree = ast.parse(text)
    result: list[tuple[str, str, str, bool]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        authenticated = False
        defaults = [*node.args.defaults, *node.args.kw_defaults]
        for default in defaults:
            if (
                isinstance(default, ast.Call)
                and isinstance(default.func, ast.Name)
                and default.func.id == "Depends"
                and default.args
                and isinstance(default.args[0], ast.Name)
                and default.args[0].id == "authenticated_user"
            ):
                authenticated = True
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not decorator.args:
                continue
            func = decorator.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "router"
                and func.attr in {"get", "post", "put", "patch", "delete"}
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
            ):
                result.append(
                    (
                        func.attr.upper(),
                        decorator.args[0].value,
                        node.name,
                        authenticated,
                    )
                )
    return result


def frontend_contract() -> set[tuple[str, str]]:
    text = source(API_FILE)
    start = text.index("export const CENTER_API_CONTRACT")
    end = text.index("]);", start)
    return set(
        re.findall(r'\["(GET|POST|PUT|PATCH|DELETE)",\s*"([^"]+)"\]', text[start:end])
    )


class LearningCenterContracts(unittest.TestCase):
    maxDiff = None

    def test_router_is_included_once_and_versioned(self):
        text = source(APP_FILE)
        self.assertEqual(
            text.count(
                "app.include_router(create_learning_center_router(_jwt_tekshir))"
            ),
            1,
        )
        self.assertEqual(
            text.count(
                "from modules.learning_center import create_learning_center_router"
            ),
            1,
        )
        self.assertIn("learning-center-v2-secure-v14", text)

    def test_routes_unique_authenticated_and_frontend_complete(self):
        discovered = routes()
        pairs = [(method, path) for method, path, _, _ in discovered]
        self.assertGreaterEqual(len(discovered), 60)
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(
            [
                (method, path, name)
                for method, path, name, authenticated in discovered
                if path != "/health" and not authenticated
            ],
            [],
        )
        self.assertTrue(frontend_contract().issubset(set(pairs)))

    def test_bearer_only_and_no_query_token(self):
        auth = function_source("authenticated_user")
        self.assertIn("authorization: str | None = Header", auth)
        self.assertIn('startswith("bearer ")', auth.lower())
        self.assertNotRegex(
            source(ROUTER_FILE),
            r"(?m)^\s*def\s+\w+\([^)]*\btoken\s*:\s*str",
        )

    def test_frontend_payload_aliases_exist_in_models(self):
        text = source(ROUTER_FILE)
        for field in (
            "cefr_level:",
            "ielts_targets:",
            "monthly_price:",
            "sessions_per_week:",
            "requested_status:",
            "attendance_date:",
            "assessment_name:",
            "formula_latex:",
            "items:",
        ):
            self.assertIn(field, text)
        attempt_submit = text[
            text.index("class AttemptSubmit"):
            text.index("class AttemptScore")
        ]
        self.assertIn(
            "context_id: int | None = Field(default=None, ge=1)",
            attempt_submit,
        )
        start_attempt = function_source("start_attempt")
        self.assertNotIn("request: HumanConfirm", start_attempt)

    def test_student_attempt_never_gets_answer_key(self):
        public_items = function_source("public_assessment_items")
        self.assertIn("allowed_metadata =", public_items)
        self.assertIn("if key in allowed_metadata", public_items)
        self.assertNotIn('"correct_answer", "answer"', public_items)
        self.assertNotIn("correct_option", public_items)
        self.assertNotIn(
            'item["metadata"] = dict(item.get("metadata") or {})',
            public_items,
        )
        get_attempt = function_source("get_attempt")
        self.assertIn('"answer_key_included": False', get_attempt)
        start_attempt = function_source("start_attempt")
        self.assertIn('"answer_key_included": False', start_attempt)
        result = function_source("attempt_result")
        self.assertIn('"answer_key_included": False', result)
        self.assertNotIn("correct_answer", result)

    def test_manual_assessment_is_answerable_before_publish(self):
        validator = function_source("validate_assessment_item")
        self.assertIn('question_type not in {"multiple_choice", "short_answer"}', validator)
        self.assertIn("len(nonempty_indexes) < 2", validator)
        self.assertIn("int(correct_answer) not in nonempty_indexes", validator)
        self.assertIn("if not correct_answer", validator)
        publish = function_source("publish_assessment")
        self.assertIn("validate_assessment_item(", publish)
        self.assertIn("generated_tests WHERE id=ANY", publish)

    def test_exam_framework_and_total_score_are_authoritative(self):
        create = function_source("create_assessment")
        self.assertIn('"ielts_mock": "ielts"', create)
        self.assertIn('"cefr_mock": "cefr"', create)
        self.assertIn("request.framework != required_framework", create)
        self.assertIn("request.total_score != computed_total", create)
        self.assertNotIn("total_score_hint", create)

    def test_schedule_insert_placeholders_match_bound_values(self):
        text = source(ROUTER_FILE)
        tree = ast.parse(text)
        create_nodes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "create_schedule"
        ]
        self.assertEqual(len(create_nodes), 1)
        inserts = []
        for call in ast.walk(create_nodes[0]):
            if (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "execute"
                and len(call.args) >= 2
                and isinstance(call.args[0], ast.Constant)
                and isinstance(call.args[0].value, str)
                and "INSERT INTO center_schedule_slots" in call.args[0].value
                and isinstance(call.args[1], ast.Tuple)
            ):
                inserts.append((call.args[0].value, call.args[1]))
        self.assertEqual(len(inserts), 1)
        sql, values = inserts[0]
        placeholders = re.findall(r"(?<!%)%s", sql)
        self.assertEqual(len(placeholders), len(values.elts))

    def test_student_attempt_history_is_self_scoped_and_answer_safe(self):
        history = function_source("list_my_assessment_attempts")
        self.assertIn("at.student_user_id=%s", history)
        self.assertIn('"answer_key_included": False', history)
        self.assertIn('scope = "self"', history)
        self.assertIn('scope = "linked_child"', history)
        self.assertIn("center_parent_links", history)
        self.assertIn('"scope": scope', history)
        self.assertNotIn("component_scores", history)
        self.assertNotIn("metadata", history)
        self.assertIn('"expired"', history)

    def test_attempt_draft_is_server_saved_and_submission_upserts(self):
        draft = function_source("save_attempt_draft")
        self.assertIn("center_attempt_answers", draft)
        self.assertIn("ON CONFLICT(", draft)
        self.assertIn("answered_at=NOW()", draft)
        self.assertIn('"submitted": False', draft)
        self.assertIn('"answer_key_included": False', draft)
        self.assertIn("expire_attempt_if_late(", draft)
        get_attempt = function_source("get_attempt")
        self.assertIn('"draft_answers": draft_answers', get_attempt)
        submit = function_source("submit_attempt")
        self.assertIn("ON CONFLICT(", submit)

    def test_parent_can_only_read_linked_child_attempt_result(self):
        reader = function_source("read_attempt_for_user")
        self.assertIn("allow_linked_parent: bool = False", reader)
        self.assertIn("center_parent_links", reader)
        self.assertIn("status='active'", reader)
        result = function_source("attempt_result")
        self.assertIn("allow_linked_parent=True", result)
        review = function_source("review_attempt")
        self.assertNotIn("allow_linked_parent=True", review)

    def test_learner_homework_submission_read_is_self_scoped(self):
        submission = function_source("get_my_homework_submission")
        self.assertIn("student_user_id=%s", submission)
        self.assertIn("active_enrollment(", submission)
        self.assertIn('"scope": "self"', submission)
        self.assertIn('"can_resubmit"', submission)
        self.assertNotIn("graded_by_user_id", submission)
        self.assertNotIn("student_name", submission)

    def test_homework_list_batches_own_submission_state(self):
        listing = function_source("list_homework")
        self.assertIn("homework_id=ANY(%s)", listing)
        self.assertIn("student_user_id=%s", listing)
        self.assertIn('row["my_submission_status"]', listing)
        self.assertIn('row["can_submit"]', listing)
        self.assertIn('row["can_resubmit"]', listing)
        self.assertNotIn("for homework_id in homework_ids", listing)

    def test_late_attempt_is_persistently_expired_before_409(self):
        expiry = function_source("expire_attempt_if_late")
        self.assertIn("status='expired'", expiry)
        self.assertIn("status='in_progress'", expiry)
        submit = function_source("submit_attempt")
        self.assertIn("expire_attempt_if_late(cur, attempt, now=now)", submit)
        self.assertIn('"code": "attempt_expired"', submit)
        start = function_source("start_attempt")
        self.assertIn("expire_attempt_if_late(", start)
        get_attempt = function_source("get_attempt")
        self.assertIn("expire_attempt_if_late(", get_attempt)

    def test_future_enrollment_cannot_preview_learning_content(self):
        for name in (
            "list_courses",
            "list_schedule",
            "list_course_documents",
            "list_assessments",
            "list_billing_plans",
            "analytics_scope",
        ):
            route = function_source(name)
            self.assertIn(
                "CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Tashkent'",
                route,
                name,
            )
            self.assertIn("starts_on", route, name)

    def test_stale_teacher_assignment_does_not_retain_roster_or_analytics(self):
        enrollments = function_source("list_enrollments")
        self.assertIn("c.teacher_user_id=%s AND EXISTS(", enrollments)
        self.assertIn("teacher_role.role_key='teacher'", enrollments)
        self.assertIn("teacher_role.starts_at<=NOW()", enrollments)
        analytics = function_source("analytics_scope")
        self.assertIn("%s AND c.teacher_user_id=%s", analytics)
        self.assertIn("teacher_assignments =", analytics)
        self.assertIn("teacher_global =", analytics)
        self.assertIn("teacher_branches =", analytics)
        self.assertIn('"teacher" in roles', analytics)

    def test_invoice_plan_course_is_checked(self):
        invoice = function_source("create_invoice")
        self.assertIn("plan_course_id", invoice)
        self.assertIn("enrollment_course_id", invoice)
        self.assertIn(
            'source["plan_course_id"] != source["enrollment_course_id"]',
            invoice,
        )
        self.assertNotIn(
            'source["course_id"] != source["course_id"]',
            invoice,
        )

    def test_avatar_is_allowlisted_and_not_privileged(self):
        text = source(ROUTER_FILE)
        for forbidden in (
            '"PUBLISH"',
            '"RECORD_PAYMENT"',
            '"ASSIGN_ROLE"',
            '"SCORE_ATTEMPT"',
            '"ENROLL_STUDENT"',
        ):
            self.assertNotIn(forbidden, text.split("ASSISTANT_ACTIONS =", 1)[1].split("}", 1)[0])
        action = function_source("assistant_action")
        self.assertIn("request.action_id not in ASSISTANT_ACTIONS", action)
        self.assertIn('"autonomous_mutations": False', action)

    def test_mixed_role_teacher_workload_defaults_to_self(self):
        workload = function_source("teacher_workload")
        self.assertIn("can_view_other_teachers", workload)
        self.assertIn(
            "if requested_teacher is None and not can_view_other_teachers",
            workload,
        )
        self.assertIn("requested_teacher = user_id", workload)

    def test_staff_analytics_does_not_union_learner_enrollments(self):
        scope = function_source("analytics_scope")
        self.assertIn("not staff_user, user_id, not staff_user, user_id", scope)
        self.assertIn("student_ids: list[int] | None = None", scope)

    def test_course_creator_uses_branch_scoped_academic_roles(self):
        course = function_source("create_course")
        self.assertIn("scoped_roles = require_roles", course)
        self.assertIn(
            "scoped_roles & (MANAGER_ROLES | {\"methodist\"})",
            course,
        )
        self.assertIn("if not may_assign_other_teacher", course)

    def test_course_activation_infers_a_single_scheduled_teacher(self):
        activation = function_source("activate_course")
        self.assertIn("ARRAY_AGG(DISTINCT teacher_user_id)", activation)
        self.assertIn("len(scheduled_teachers) == 1", activation)
        self.assertIn("elif not scheduled_teachers", activation)
        self.assertIn("Jadvalda bir nechta o'qituvchi bor", activation)

    def test_require_roles_returns_only_roles_matching_the_branch(self):
        """A role in branch B must not elevate an assignment in branch A."""

        guard = function_source("require_roles")
        self.assertIn(
            'matching = [row for row in assignments if row["role_key"] in allowed]',
            guard,
        )
        self.assertIn(
            'if row["branch_id"] is None or int(row["branch_id"]) == branch_id',
            guard,
        )
        self.assertIn(
            'return {row["role_key"] for row in matching}',
            guard,
        )
        self.assertNotIn("return roles", guard)

    def test_course_access_ignores_unrelated_branch_roles(self):
        """Student/parent assignments cannot satisfy manager branch scope."""

        access = function_source("course_access")
        self.assertIn('row["role_key"] in role_keys', access)
        self.assertIn(
            "scoped_assignment_ok(MANAGER_ROLES)",
            access,
        )
        self.assertIn(
            'scoped_assignment_ok({"methodist"})',
            access,
        )
        self.assertIn(
            'and scoped_assignment_ok({"teacher"})',
            access,
        )
        self.assertNotIn(
            "if roles & MANAGER_ROLES and branch_ok",
            access,
        )

    def test_branch_role_cannot_mutate_branchless_course(self):
        permission = function_source("require_permission")
        self.assertIn(
            "require_global=require_global or branch_id is None",
            permission,
        )
        probe = function_source("has_permission")
        self.assertIn("(%s IS NULL AND branch_id IS NULL)", probe)
        enrollment = function_source("decide_enrollment")
        self.assertIn(
            'require_global=enrollment["branch_id"] is None',
            enrollment,
        )
        worklog = function_source("decide_teacher_worklog")
        self.assertIn(
            'require_global=item["branch_id"] is None',
            worklog,
        )

    def test_live_attempt_answers_are_owner_only(self):
        attempt = function_source("get_attempt")
        self.assertIn('attempt["status"] == "in_progress"', attempt)
        self.assertIn(
            'int(attempt["student_user_id"]) != user_id',
            attempt,
        )
        review = function_source("review_attempt")
        self.assertIn(
            'attempt["status"] not in {"submitted", "scored"}',
            review,
        )

    def test_staff_list_is_branch_scoped_and_hides_learners(self):
        """Branch A staff must not enumerate branch B, students or parents."""

        router_text = source(ROUTER_FILE)
        self.assertIn(
            'STAFF_ROLES = VIEW_ROLES - {"student", "parent"}',
            router_text,
        )
        staff = function_source("list_staff")
        self.assertIn(
            'if item["role_key"] in ACADEMIC_ROLES',
            staff,
        )
        self.assertIn(
            'if item["role_key"] in (MANAGER_ROLES | {"methodist"})',
            staff,
        )
        self.assertIn(
            "AND (%s OR r.user_id=%s OR r.branch_id=ANY(%s))",
            staff,
        )
        self.assertIn(
            "r.role_key NOT IN ('student','parent')",
            staff,
        )
        self.assertIn("privileged_branch_ids = sorted(", staff)

    def test_staff_mixed_roles_only_expand_privileged_branches(self):
        """Teacher A + methodist B sees self in A and staff in B, not all A."""

        staff = function_source("list_staff")
        self.assertIn("privileged_assignments = [", staff)
        self.assertIn(
            'if item["role_key"] in (MANAGER_ROLES | {"methodist"})',
            staff,
        )
        self.assertIn("r.user_id=%s", staff)
        self.assertNotIn(
            "branch_filter = None if global_scope else list(branch_ids)",
            staff,
        )

    def test_teacher_dashboard_does_not_expose_center_finance(self):
        dashboard = function_source("dashboard")
        self.assertIn('elif "teacher" in roles:', dashboard)
        self.assertIn("c.teacher_user_id=%s", dashboard)
        self.assertIn("0::NUMERIC debt", dashboard)
        self.assertIn(
            "roles & FINANCE_VIEW_STAFF_ROLES",
            dashboard,
        )
        self.assertIn(
            "if not (can_view_staff_debt or is_pure_learner_view):",
            dashboard,
        )
        self.assertIn('"can_manage_parent_links": can_manage_parent_links', dashboard)
        self.assertIn('"branch_scope": {', dashboard)
        self.assertIn('"linked_children": linked_children', dashboard)
        self.assertIn("r.branch_id IS NULL", dashboard)

    def test_migrations_are_atomic_bounded_and_registered(self):
        for migration in MIGRATIONS:
            text = source(migration)
            self.assertLess(migration.stat().st_size, 32_769)
            without_comments = re.sub(
                r"\A(?:\s*--[^\n]*(?:\n|\Z))*",
                "",
                text,
            )
            self.assertTrue(without_comments.lstrip().startswith("BEGIN;"))
            self.assertTrue(text.rstrip().endswith("COMMIT;"))
            self.assertIn("app_schema_migrations", text)
        core = source(MIGRATIONS[0])
        operations = source(MIGRATIONS[1])
        self.assertIn("samtm_center_schedule_conflict", core)
        self.assertIn("pg_advisory_xact_lock", core)
        self.assertIn("center_assistant_sessions", core)
        self.assertIn(
            "work_days SMALLINT[] NOT NULL\n"
            "    DEFAULT ARRAY[1,2,3,4,5,6]::SMALLINT[]",
            core,
        )
        self.assertIn("ck_center_branch_work_days", core)
        self.assertIn("cardinality(work_days) BETWEEN 1 AND 7", core)
        self.assertIn(
            "work_days <@ ARRAY[1,2,3,4,5,6,7]::SMALLINT[]",
            core,
        )
        self.assertIn("samtm_center_unique_smallint_array(work_days)", core)
        self.assertIn("starts_on DATE DEFAULT NULL", core)
        self.assertIn("uq_center_waitlist_position", core)
        self.assertRegex(
            core,
            r"ON center_enrollments"
            r"\(context_id,course_id,waitlist_position\)\s+"
            r"WHERE status='waitlisted'",
        )
        self.assertIn("center_teacher_work_logs", operations)
        self.assertIn(
            "ADD COLUMN IF NOT EXISTS employment_type TEXT DEFAULT NULL",
            operations,
        )
        self.assertIn(
            "ADD COLUMN IF NOT EXISTS weekly_capacity_hours NUMERIC(5,2) DEFAULT NULL",
            operations,
        )
        self.assertIn("ck_center_role_employment_type", operations)
        self.assertIn(
            "'full_time','part_time','contract','hourly'",
            operations,
        )
        self.assertIn("weekly_capacity_hours BETWEEN 1 AND 80", operations)
        self.assertIn("uq_center_attempt_in_progress", operations)
        self.assertIn(
            "'in_progress','submitted','scored','invalidated','expired'",
            operations,
        )
        self.assertIn("ck_center_assessment_attempt_status", operations)
        self.assertRegex(
            operations,
            r"ON center_assessment_attempts"
            r"\(context_id,assessment_id,student_user_id\)\s+"
            r"WHERE status='in_progress'",
        )
        self.assertIn("uq_center_worklog_schedule_slot", operations)
        self.assertIn(
            "context_id,teacher_user_id,schedule_slot_id,work_date",
            re.sub(r"\s+", "", operations),
        )
        self.assertIn("uq_center_worklog_manual_day", operations)
        self.assertIn("samtm_center_invoice_scope", operations)
        self.assertIn(
            "FOREIGN KEY(enrollment_id,context_id,course_id,student_user_id)",
            operations,
        )


if __name__ == "__main__":
    unittest.main()
