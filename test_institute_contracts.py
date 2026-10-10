"""Static security and API contract tests for institute v1."""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "modules" / "institute.py"
MAIN = ROOT / "backend" / "main.py"
MIGRATIONS = tuple(ROOT / "database" / name for name in (
    "009_institute_core.sql",
    "010_institute_curriculum.sql",
    "011_institute_teaching.sql",
    "012_institute_finance_assistant.sql",
))


def source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def function_source(name: str) -> str:
    text = source(ROUTER)
    tree = ast.parse(text)
    nodes = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    if len(nodes) != 1:
        raise AssertionError(f"{name}: {len(nodes)}")
    result = ast.get_source_segment(text, nodes[0])
    if result is None:
        raise AssertionError(name)
    return result


def assignment_dict_entry(name: str, key: str):
    tree = ast.parse(source(ROUTER))
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
        ):
            if not isinstance(node.value, ast.Dict):
                raise AssertionError(f"{name} is not a dict")
            for item_key, item_value in zip(node.value.keys, node.value.values):
                if ast.literal_eval(item_key) == key:
                    return ast.literal_eval(item_value)
    raise AssertionError(f"{name}[{key!r}]")


def routes() -> list[tuple[str, str, str, bool]]:
    tree = ast.parse(source(ROUTER))
    result = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        authenticated = any(
            isinstance(default, ast.Call)
            and isinstance(default.func, ast.Name)
            and default.func.id == "Depends"
            and default.args
            and isinstance(default.args[0], ast.Name)
            and default.args[0].id == "authenticated_user"
            for default in [*node.args.defaults, *node.args.kw_defaults]
        )
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call) and decorator.args
                and isinstance(decorator.func, ast.Attribute)
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "router"
                and decorator.func.attr in {"get", "post", "put", "patch", "delete"}
                and isinstance(decorator.args[0], ast.Constant)
            ):
                result.append((
                    decorator.func.attr.upper(), str(decorator.args[0].value),
                    node.name, authenticated,
                ))
    return result


class InstituteContracts(unittest.TestCase):
    maxDiff = None

    def test_router_is_included_once_and_versioned(self):
        text = source(MAIN)
        self.assertEqual(text.count("from modules.institute import create_institute_router"), 1)
        self.assertEqual(text.count("app.include_router(create_institute_router(_jwt_tekshir))"), 1)
        self.assertIn("institute-v1-secure-v15", text)
        self.assertIn('"institute-v1"', text)

    def test_exact_route_count_unique_and_authenticated(self):
        found = routes()
        pairs = [(method, path) for method, path, _, _ in found]
        self.assertEqual(len(found), 67)
        self.assertEqual(len(pairs), len(set(pairs)))
        self.assertEqual(
            [(method, path, name) for method, path, name, auth in found if path != "/health" and not auth],
            [],
        )

    def test_bearer_only(self):
        auth = function_source("authenticated_user")
        self.assertIn("authorization: str | None = Header", auth)
        self.assertIn('startswith("bearer ")', auth.lower())
        self.assertNotRegex(source(ROUTER), r"(?m)^\s*def\s+\w+\([^)]*\btoken\s*:")

    def test_migrations_are_numbered_small_and_registered(self):
        for path in MIGRATIONS:
            text = source(path)
            self.assertLess(len(text.encode("utf-8")), 32769, path.name)
            self.assertIn("BEGIN;", text)
            self.assertIn("COMMIT;", text)
            self.assertIn("app_schema_migrations", text)
            self.assertIn(path.stem, text)
            self.assertNotIn("DROP TABLE", text.upper())

    def test_institute_tables_are_tenant_prefixed(self):
        text = "\n".join(source(path) for path in MIGRATIONS)
        created = re.findall(r"CREATE TABLE IF NOT EXISTS\s+(\w+)", text, re.I)
        self.assertGreaterEqual(len(created), 30)
        self.assertTrue(all(name.startswith("institute_") for name in created))
        self.assertIn("context_id BIGINT NOT NULL REFERENCES learning_contexts", text)

    def test_common_analytics_bridge_is_explicit(self):
        text = source(MIGRATIONS[0]) + source(MIGRATIONS[1])
        self.assertIn("context_memberships", text)
        self.assertIn("course_groups", text)
        commit = function_source("commit_draft")
        self.assertIn("'university'", commit)
        self.assertIn("'institute_v1'", commit)
        self.assertIn("upsert_role(", commit)

    def test_scope_is_hierarchical_and_branchless_writes_need_global(self):
        self.assertIn("campus_id", function_source("require_roles"))
        self.assertIn("faculty_id", function_source("require_roles"))
        self.assertIn("department_id", function_source("require_roles"))
        self.assertIn("require_global", function_source("create_campus"))
        self.assertIn("require_global", function_source("create_academic_year"))
        self.assertIn("require_global", function_source("change_term_status"))

    def test_sensitive_actions_require_human_confirmation(self):
        for name in (
            "commit_draft", "decide_verification", "change_term_status",
            "assign_staff", "end_staff_assignment", "publish_curriculum", "activate_section",
            "decide_enrollment", "publish_schedule", "publish_assessment",
            "finalize_result", "issue_transcript", "create_contract",
            "create_installments", "create_payment",
        ):
            self.assertIn("require_human", function_source(name), name)

    def test_money_and_final_grade_are_idempotent(self):
        self.assertIn("claim_request", function_source("create_payment"))
        self.assertIn("finish_request", function_source("create_payment"))
        self.assertIn("FOR UPDATE", function_source("create_payment"))
        self.assertIn("claim_request", function_source("finalize_result"))
        self.assertIn("finish_request", function_source("finalize_result"))
        sql = source(MIGRATIONS[3]) + source(MIGRATIONS[2])
        self.assertIn("UNIQUE(context_id,idempotency_key)", sql)

    def test_idempotency_keys_bind_actor_action_and_payload(self):
        claim = function_source("claim_request")
        self.assertIn("request_fingerprint", claim)
        self.assertIn("row[\"actor_user_id\"]", claim)
        self.assertIn("row[\"action_key\"]", claim)
        for name in ("create_grade", "finalize_result", "issue_transcript", "create_payment"):
            action = function_source(name)
            self.assertIn("request_fingerprint", action, name)
            self.assertIn("claim_request", action, name)
        self.assertIn("request_fingerprint TEXT NOT NULL", source(MIGRATIONS[3]))

    def test_avatar_has_allowlist_and_no_privileged_mutation(self):
        text = source(ROUTER)
        self.assertIn("ASSISTANT_ACTIONS", text)
        action = function_source("assistant_action")
        self.assertIn("forbidden_keys", action)
        self.assertIn('"server_mutation": False', action)
        start = function_source("start_assistant_session")
        self.assertIn('"can_publish_or_grade_or_pay": False', start)

    def test_attendance_is_warning_only(self):
        mark = function_source("mark_attendance")
        self.assertIn('"automatic_status_change": False', mark)
        self.assertIn('"human_order_required": True', mark)
        self.assertIn("unexcused_course_warning_percent", mark)
        self.assertIn("semester_absence_warning_hours", mark)
        self.assertIn('"auto_exclusion": False', function_source("commit_draft"))

    def test_student_statuses_and_order_reference_exist(self):
        text = source(MIGRATIONS[1])
        for status in (
            "active", "academic_leave", "retained", "transferred",
            "expelled", "reinstated", "graduated",
        ):
            self.assertIn(f"'{status}'", text)
        self.assertIn("status_order_ref", text)

    def test_policy_is_versioned_configurable_not_claimed_official(self):
        sql = source(MIGRATIONS[0])
        self.assertIn("policy_version", sql)
        self.assertIn("academic_policy", sql)
        self.assertIn("integration_settings", sql)
        meta = function_source("meta")
        self.assertIn("placeholder_not_connected", meta)
        issue = function_source("issue_transcript")
        self.assertIn('"official_e_signature": False', issue)
        self.assertIn('"hemis_synced": False', issue)
        self.assertIn('"custom"', function_source("meta"))

    def test_keyset_pagination_is_used_for_lists(self):
        text = source(ROUTER)
        self.assertGreaterEqual(text.count("after_id: int | None"), 20)
        self.assertGreaterEqual(text.count('"next_cursor"'), 20)
        self.assertNotIn("OFFSET %s", text)

    def test_schedule_trigger_is_final_concurrency_guard(self):
        text = source(MIGRATIONS[1])
        self.assertIn("samtm_institute_schedule_conflict", text)
        self.assertIn("BEFORE INSERT OR UPDATE", text)
        self.assertIn("teacher_user_id=NEW.teacher_user_id", text)
        self.assertIn("s.room_id=NEW.room_id", text)
        self.assertIn("institute_section_cohorts", text)

    def test_schedule_attendance_and_assessment_have_concurrency_guards(self):
        self.assertIn("pg_advisory_xact_lock(74134", function_source("create_schedule"))
        self.assertIn("pg_advisory_xact_lock(74134", function_source("publish_schedule"))
        self.assertIn("pg_advisory_xact_lock(74135", function_source("create_assessment"))
        attendance_sql = source(MIGRATIONS[2])
        self.assertIn("uq_inst_attendance_slot", attendance_sql)
        self.assertIn("WHERE schedule_slot_id IS NOT NULL", attendance_sql)
        self.assertIn("uq_inst_attendance_no_slot", attendance_sql)
        self.assertIn(
            "FOREIGN KEY(schedule_slot_id,context_id,section_id)",
            attendance_sql,
        )

    def test_onboarding_commits_minimum_working_academic_hierarchy(self):
        commit = function_source("commit_draft")
        for table in (
            "institute_campuses", "institute_faculties", "institute_departments",
            "institute_programs", "institute_academic_years", "institute_terms",
            "institute_grade_scale_bands",
        ):
            self.assertIn(f"INSERT INTO {table}", commit, table)
        self.assertIn('"transcript_attempt_policy": "latest"', commit)

    def test_scoped_student_bridge_does_not_create_global_membership(self):
        upsert = function_source("upsert_role")
        self.assertIn(
            "if campus_id is None and faculty_id is None and department_id is None",
            upsert,
        )
        enrollment = function_source("create_enrollment")
        self.assertIn("group_id,user_id,member_role", enrollment)
        self.assertIn("avval rasmiy ko'chirish", enrollment)
        self.assertNotIn(
            "DO UPDATE SET program_id=EXCLUDED.program_id",
            enrollment,
        )

    def test_section_creation_validates_lecturer_curriculum_and_cohorts(self):
        create = function_source("create_section")
        self.assertIn('row["role_key"] == "lecturer"', create)
        self.assertIn("cc.course_id=%s", create)
        self.assertIn("cu.status='published'", create)
        self.assertIn("course_allowed", create)
        self.assertIn("require_permission", create)

    def test_staff_directory_requires_staff_management_and_honors_scope(self):
        listing = function_source("list_staff")
        self.assertIn('roles_for_permission("staff.manage")', listing)
        self.assertNotIn(
            "r.campus_id IS NULL AND r.faculty_id IS NULL",
            listing,
        )
        ending = function_source("end_staff_assignment")
        self.assertIn("ROLE_GRANT_MATRIX", ending)
        self.assertIn("status='ended'", ending)
        self.assertIn("status='withdrawn'", ending)
        self.assertIn("require_human", ending)
        self.assertEqual(
            set(assignment_dict_entry("ROLE_GRANT_MATRIX", "hr_manager")),
            {"methodist", "lecturer", "advisor"},
        )

    def test_transcript_retakes_use_policy_and_issuance_is_idempotent(self):
        issue = function_source("issue_transcript")
        self.assertIn("transcript_attempt_policy", issue)
        self.assertIn("select_transcript_attempts", issue)
        self.assertIn("request_fingerprint", issue)
        self.assertIn("finish_request", issue)

    def test_dashboard_does_not_return_raw_integration_secrets(self):
        dashboard = function_source("dashboard")
        self.assertNotIn("p.integration_settings,", dashboard)
        self.assertIn("hemis_enabled", dashboard)
        self.assertIn("student_only", dashboard)
        self.assertIn("c.student_user_id=%s", dashboard)

    def test_grades_use_pure_weighted_credit_calculation(self):
        finalizer = function_source("finalize_result")
        self.assertIn("weighted_percent", finalizer)
        self.assertIn("select_grade_band", finalizer)
        transcript = function_source("issue_transcript")
        self.assertIn("calculate_gpa", transcript)
        self.assertIn("snapshot_hash", transcript)

    def test_cross_module_schedule_limit_is_not_hidden(self):
        self.assertIn(
            '"cross_module_conflicts_checked": False',
            function_source("publish_schedule"),
        )

    def test_no_ai_or_automatic_legal_status_change(self):
        action = function_source("assistant_action")
        self.assertNotIn("UPDATE institute_students", action)
        attendance = function_source("mark_attendance")
        self.assertNotIn("UPDATE institute_students", attendance)

    def test_dashboard_uses_canonical_permission_aware_menu_keys(self):
        dashboard = function_source("dashboard")
        self.assertIn("dashboard_menu_keys", dashboard)
        self.assertNotIn('"academics"', dashboard)
        self.assertNotIn('"grades"', dashboard)

        namespace = {
            "ACADEMIC_MANAGER_ROLES": {
                "owner", "founder", "rector", "vice_rector_academic",
                "administrator", "registrar", "dean", "deputy_dean",
                "department_head", "methodist",
            },
        }
        exec(function_source("dashboard_menu_keys"), namespace)  # noqa: S102
        dashboard_menu_keys = namespace["dashboard_menu_keys"]
        student_permissions = assignment_dict_entry("ROLE_PERMISSIONS", "student")
        registrar_permissions = assignment_dict_entry("ROLE_PERMISSIONS", "registrar")
        administrator_permissions = assignment_dict_entry("ROLE_PERMISSIONS", "administrator")

        student_menu = dashboard_menu_keys(
            {"student"}, set(student_permissions),
        )
        self.assertTrue(
            {"curriculum", "gradebook", "exams", "transcripts"}
            <= set(student_menu),
        )
        self.assertNotIn("transcripts.issue", student_permissions)

        registrar_menu = dashboard_menu_keys(
            {"registrar"}, set(registrar_permissions),
        )
        self.assertTrue(
            {"curriculum", "gradebook", "exams", "transcripts"}
            <= set(registrar_menu),
        )

        administrator_menu = dashboard_menu_keys(
            {"administrator"}, set(administrator_permissions),
        )
        self.assertNotIn("gradebook", administrator_menu)
        self.assertNotIn("exams", administrator_menu)
        self.assertNotIn("transcripts", administrator_menu)


if __name__ == "__main__":
    unittest.main()
