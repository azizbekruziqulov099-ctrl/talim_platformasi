"""Maktab v2 uchun PostgreSQL talab qilmaydigan statik contract testlar.

Bu testlar endpointning ichki biznes natijasini emas, frontend, router,
migratsiya va jadval generatori orasidagi xavfsizlik shartnomasini tekshiradi.
Ular staging bazasiga yozmaydi va tarmoq so'rovi yubormaydi.
"""

from __future__ import annotations

import ast
import re
import unittest
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTER_FILE = ROOT / "backend" / "modules" / "school.py"
SCHEDULER_FILE = ROOT / "backend" / "modules" / "school_scheduler.py"
MIGRATION_FILE = ROOT / "database" / "005_school_platform.sql"
EXCEPTION_MIGRATION_FILE = (
    ROOT / "database" / "006_school_timetable_exceptions.sql"
)
APP_FILE = ROOT / "backend" / "main.py"
FRONTEND_APP_FILE = ROOT / "frontend" / "src" / "App.jsx"
FRONTEND_API_FILE = ROOT / "frontend" / "src" / "school" / "api.js"
FRONTEND_WORKSPACE_FILE = (
    ROOT / "frontend" / "src" / "school" / "SchoolWorkspace.jsx"
)
LOAD_FILE = ROOT / "backend" / "tests" / "load_school.py"


@dataclass(frozen=True)
class RouteContract:
    method: str
    path: str
    function_name: str
    authenticated: bool


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _is_authenticated_dependency(node: ast.AST) -> bool:
    """Return True when a function default is Depends(authenticated_user)."""

    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    defaults = [*node.args.defaults, *node.args.kw_defaults]
    for default in defaults:
        if not isinstance(default, ast.Call):
            continue
        func = default.func
        if not isinstance(func, ast.Name) or func.id != "Depends":
            continue
        if (
            default.args
            and isinstance(default.args[0], ast.Name)
            and default.args[0].id == "authenticated_user"
        ):
            return True
    return False


def route_contracts() -> list[RouteContract]:
    tree = ast.parse(_source(ROUTER_FILE))
    contracts: list[RouteContract] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "router"
                and func.attr in {"get", "post", "put", "patch", "delete"}
                and decorator.args
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
            ):
                contracts.append(
                    RouteContract(
                        method=func.attr.upper(),
                        path=decorator.args[0].value,
                        function_name=node.name,
                        authenticated=_is_authenticated_dependency(node),
                    )
                )
    return contracts


def python_function_source(path: Path, function_name: str) -> str:
    source = _source(path)
    tree = ast.parse(source)
    candidates = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    if len(candidates) != 1:
        raise AssertionError(
            f"{function_name!r} funksiyasi {len(candidates)} marta topildi"
        )
    segment = ast.get_source_segment(source, candidates[0])
    if segment is None:
        raise AssertionError(f"{function_name!r} manba qismi olinmadi")
    return segment


def javascript_function_source(source: str, function_name: str) -> str:
    """Extract a top-level named JSX function without needing a JS parser."""

    marker = f"function {function_name}("
    start = source.find(marker)
    if start < 0:
        raise AssertionError(f"{function_name!r} frontend funksiyasi topilmadi")
    next_function = source.find("\nfunction ", start + len(marker))
    return source[start:] if next_function < 0 else source[start:next_function]


def frontend_route_keys() -> set[str]:
    source = _source(FRONTEND_API_FILE)
    start = source.index("export const schoolRoutes")
    end = source.index("\n});", start)
    block = source[start:end]
    return set(re.findall(r"(?m)^  ([A-Za-z_$][A-Za-z0-9_$]*):", block))


def frontend_route_references() -> set[str]:
    return set(
        re.findall(
            r"\bschoolRoutes\.([A-Za-z_$][A-Za-z0-9_$]*)",
            _source(FRONTEND_WORKSPACE_FILE),
        )
    )


class SchoolContractTests(unittest.TestCase):
    maxDiff = None

    def test_router_is_included_exactly_once(self):
        source = _source(APP_FILE)
        self.assertEqual(
            source.count("app.include_router(create_school_router(_jwt_tekshir))"),
            1,
        )
        self.assertEqual(
            source.count("from modules.school import create_school_router"),
            1,
        )

    def test_route_method_and_path_pairs_are_unique(self):
        contracts = route_contracts()
        pairs = [(item.method, item.path) for item in contracts]
        self.assertGreaterEqual(len(contracts), 35)
        self.assertEqual(len(pairs), len(set(pairs)))

    def test_critical_routes_and_methods_exist(self):
        contracts = {(item.method, item.path) for item in route_contracts()}
        required = {
            ("GET", "/health"),
            ("GET", "/meta"),
            ("GET", "/workspaces"),
            ("GET", "/dashboard"),
            ("GET", "/join/search"),
            ("POST", "/join/requests"),
            ("POST", "/onboarding/drafts"),
            ("PATCH", "/onboarding/drafts/{draft_id}"),
            ("GET", "/onboarding/drafts/{draft_id}/preview"),
            ("POST", "/onboarding/drafts/{draft_id}/commit"),
            ("GET", "/buildings"),
            ("POST", "/buildings"),
            ("GET", "/grades"),
            ("POST", "/grades"),
            ("GET", "/subjects"),
            ("POST", "/subjects"),
            ("GET", "/workloads"),
            ("POST", "/workloads"),
            ("GET", "/staff"),
            ("POST", "/staff"),
            ("POST", "/staff/invites"),
            ("GET", "/staff/{teacher_user_id}/availability"),
            ("PUT", "/staff/{teacher_user_id}/availability"),
            ("GET", "/calendar"),
            ("POST", "/calendar"),
            ("POST", "/timetable/generate"),
            ("POST", "/timetable/generations/{generation_id}/confirm"),
            ("GET", "/timetable"),
            ("GET", "/timetable/effective"),
            ("GET", "/timetable/exceptions"),
            ("POST", "/timetable/substitutions"),
            ("POST", "/timetable/exceptions/{exception_id}/revoke"),
            ("GET", "/students"),
            ("POST", "/students"),
            ("POST", "/students/parent-links"),
            ("GET", "/attendance"),
            ("POST", "/attendance"),
            ("GET", "/grade-entries"),
            ("POST", "/grade-entries"),
            ("GET", "/billing/plans"),
            ("POST", "/billing/plans"),
            ("GET", "/billing/invoices"),
            ("POST", "/billing/invoices"),
            ("POST", "/billing/payments"),
            ("POST", "/assistant/sessions"),
            ("POST", "/assistant/sessions/{session_id}/actions"),
        }
        self.assertTrue(required.issubset(contracts), required - contracts)

    def test_every_non_health_route_is_bearer_authenticated(self):
        unauthenticated = [
            (item.method, item.path, item.function_name)
            for item in route_contracts()
            if item.path != "/health" and not item.authenticated
        ]
        self.assertEqual(unauthenticated, [])

        source = _source(ROUTER_FILE)
        auth = python_function_source(ROUTER_FILE, "authenticated_user")
        self.assertIn("authorization: str | None = Header", auth)
        self.assertIn('startswith("bearer ")', auth.lower())
        self.assertNotRegex(
            source,
            r"(?m)^\s*def\s+\w+\([^)]*\btoken\s*:\s*str",
        )

    def test_cors_allows_patch_for_onboarding(self):
        source = _source(APP_FILE)
        cors_start = source.index("app.add_middleware(")
        cors_end = source.index("\n)\n", cors_start) + 3
        cors = source[cors_start:cors_end]
        self.assertIn("CORSMiddleware", cors)
        self.assertRegex(
            cors,
            r"allow_methods\s*=\s*\[[^\]]*[\"']PATCH[\"']",
        )

    def test_frontend_only_references_defined_route_helpers(self):
        defined = frontend_route_keys()
        referenced = frontend_route_references()
        self.assertFalse(
            referenced - defined,
            f"api.js da aniqlanmagan schoolRoutes: {sorted(referenced - defined)}",
        )

    def test_frontend_route_paths_match_backend(self):
        api = _source(FRONTEND_API_FILE)
        backend = {(item.method, item.path) for item in route_contracts()}
        static_contracts = {
            "workspaces": ("GET", "/workspaces"),
            "joinSearch": ("GET", "/join/search"),
            "joinRequest": ("POST", "/join/requests"),
            "onboardingDrafts": ("POST", "/onboarding/drafts"),
            "assistantSessions": ("POST", "/assistant/sessions"),
            "dashboard": ("GET", "/dashboard"),
            "timetableGenerate": ("POST", "/timetable/generate"),
            "attendance": ("POST", "/attendance"),
            "gradeEntries": ("POST", "/grade-entries"),
            "billingPlans": ("GET", "/billing/plans"),
            "billingInvoices": ("GET", "/billing/invoices"),
            "billingPayments": ("POST", "/billing/payments"),
        }
        for key, contract in static_contracts.items():
            method, path = contract
            self.assertRegex(
                api,
                rf"(?m)^\s*{re.escape(key)}:\s*[\"']{re.escape(path)}[\"']",
            )
            self.assertIn((method, path), backend)

        for resource, path in {
            "buildings": "/buildings",
            "classes": "/grades",
            "subjects": "/subjects",
            "workloads": "/workloads",
            "staff": "/staff",
            "calendar": "/calendar",
            "timetable": "/timetable",
            "attendance": "/attendance",
            "grades": "/grade-entries",
            "students": "/students",
        }.items():
            self.assertRegex(
                api,
                rf"(?m)^\s*{resource}:\s*[\"']{re.escape(path)}[\"']",
            )
            self.assertIn(("GET", path), backend)

        self.assertIn(
            "/onboarding/drafts/${draftId}/commit",
            api,
        )
        self.assertIn(
            "/timetable/generations/${generationId}/confirm",
            api,
        )

    def test_frontend_core_payloads_use_backend_field_names(self):
        source = _source(FRONTEND_WORKSPACE_FILE)

        attendance = javascript_function_source(source, "AttendancePage")
        self.assertIn("schoolRoutes.attendance", attendance)
        for field in (
            "section_id:",
            "student_user_id:",
            "attendance_date:",
            "period_no:",
            "status:",
        ):
            self.assertIn(field, attendance)
        self.assertNotIn("class_id:", attendance)
        self.assertNotIn("student_id:", attendance)

        grades = javascript_function_source(source, "GradesPage")
        self.assertIn("schoolRoutes.gradeEntries", grades)
        for field in (
            "section_id:",
            "subject_id:",
            "student_user_id:",
            "grade_type:",
            "score:",
            "max_score:",
            "graded_at:",
            "idempotency_key:",
        ):
            self.assertIn(field, grades)
        self.assertNotIn("gradesBulk", grades)
        self.assertNotIn("subject_name:", grades)

        onboarding = javascript_function_source(source, "SchoolOnboarding")
        for field in (
            "relationship,",
            "ownership_type:",
            'setup_mode: "assistant"',
            "expected_version:",
            "confirmation: true",
        ):
            self.assertIn(field, onboarding)

        timetable = javascript_function_source(source, "TimetablePage")
        for field in (
            "academic_year:",
            "term_no:",
            "section_ids:",
            "max_periods_per_shift:",
            "expected_version:",
            "confirmation: true",
        ):
            self.assertIn(field, timetable)

    def test_school_frontend_never_puts_token_in_url(self):
        api = _source(FRONTEND_API_FILE)
        workspace = _source(FRONTEND_WORKSPACE_FILE)
        combined = f"{api}\n{workspace}"
        self.assertNotRegex(combined, r"[?&]token\s*=")
        self.assertNotIn('searchParams.set("token"', combined)
        self.assertNotIn("encodeURIComponent(token)", combined)
        self.assertIn("Authorization: `Bearer ${token}`", api)
        self.assertIn('url.searchParams.delete("token")', api)
        self.assertIn('credentials: "omit"', api)

    def test_migration_is_atomic_small_and_registered(self):
        raw = MIGRATION_FILE.read_bytes()
        sql = raw.decode("utf-8")
        self.assertLess(
            len(raw),
            32769,
            "Railway konsolining 32769 bayt chegarasidan oshdi",
        )
        self.assertEqual(len(re.findall(r"(?m)^BEGIN;\s*$", sql)), 1)
        self.assertEqual(len(re.findall(r"(?m)^COMMIT;\s*$", sql)), 1)
        self.assertTrue(sql.rstrip().endswith("COMMIT;"))
        self.assertIn("pg_advisory_xact_lock", sql)
        self.assertIn("SET LOCAL lock_timeout", sql)
        self.assertIn("SET LOCAL statement_timeout", sql)
        self.assertIn("005_school_platform", sql)
        self.assertIn("app_schema_migrations", sql)

    def test_date_specific_exception_migration_is_atomic_and_strict(self):
        raw = EXCEPTION_MIGRATION_FILE.read_bytes()
        sql = raw.decode("utf-8")
        self.assertLess(len(raw), 32769)
        self.assertEqual(len(re.findall(r"(?m)^BEGIN;\s*$", sql)), 1)
        self.assertEqual(len(re.findall(r"(?m)^COMMIT;\s*$", sql)), 1)
        self.assertTrue(sql.rstrip().endswith("COMMIT;"))
        self.assertIn(
            "CREATE TABLE IF NOT EXISTS school_timetable_exceptions", sql
        )
        self.assertIn("006_school_timetable_exceptions", sql)
        self.assertIn("uq_school_active_slot_exception", sql)
        self.assertIn("WHERE status='active'", sql)
        for kind in (
            "substitution", "cancelled", "makeup_extra",
            "topic_compression",
        ):
            self.assertIn(f"exception_kind='{kind}'", sql)
        self.assertIn("target_date>lesson_date", sql)
        self.assertIn("length(idempotency_key) BETWEEN 16 AND 100", sql)
        self.assertIn("revocation_idempotency_key TEXT", sql)
        self.assertIn(
            "UNIQUE(context_id,revocation_idempotency_key)", sql
        )
        self.assertIn("ix_school_exception_target", sql)
        self.assertIn("original_teacher_user_id BIGINT NOT NULL", sql)
        self.assertRegex(
            sql,
            r"topic_compression'[\s\S]+?makeup_event_id IS NULL",
        )

    def test_migration_has_tenant_tables_and_query_indexes(self):
        sql = _source(MIGRATION_FILE)
        tables = {
            "school_profiles",
            "school_setup_drafts",
            "school_role_assignments",
            "school_invitations",
            "school_parent_students",
            "school_buildings",
            "school_floors",
            "school_rooms",
            "school_sections",
            "school_subjects",
            "school_teacher_settings",
            "school_teacher_availability",
            "school_teacher_subjects",
            "school_workloads",
            "school_calendar_events",
            "school_timetable_generations",
            "school_timetable_slots",
            "school_attendance",
            "school_grade_entries",
            "school_billing_plans",
            "school_invoices",
            "school_payments",
            "school_assistant_sessions",
            "school_assistant_actions",
            "school_audit_log",
        }
        for table in tables:
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", sql)
        self.assertGreaterEqual(
            len(re.findall(r"(?m)^CREATE (?:UNIQUE )?INDEX IF NOT EXISTS", sql)),
            20,
        )
        for index in (
            "uq_school_role_scope",
            "ix_school_parent_student",
            "ix_school_workload_context",
            "ix_school_calendar_cursor",
            "uq_school_slot_section",
            "uq_school_slot_teacher",
            "uq_school_slot_room",
            "ix_school_attendance_cursor",
            "ix_school_grade_cursor",
            "uq_school_grade_key",
            "ix_school_invoice",
            "ix_school_audit",
        ):
            self.assertIn(index, sql)

    def test_migration_cross_tenant_and_sensitive_data_contracts(self):
        sql = _source(MIGRATION_FILE)
        self.assertGreaterEqual(sql.count("UNIQUE(id,context_id)"), 10)
        self.assertGreaterEqual(
            len(
                re.findall(
                    r"FOREIGN KEY \([^)]*,context_id\)\s+"
                    r"REFERENCES \w+\(id,context_id\)",
                    sql,
                )
            ),
            12,
        )
        self.assertIn("code_hash TEXT NOT NULL UNIQUE", sql)
        self.assertNotRegex(sql, r"(?m)^\s*invite_code\s+TEXT")
        self.assertRegex(
            sql,
            r"(?:PRIMARY KEY|UNIQUE)\s*"
            r"\(context_id,parent_user_id,student_user_id\)",
        )
        self.assertIn(
            "UNIQUE(context_id,idempotency_key)",
            sql,
        )
        self.assertIn(
            "CHECK (score>=0 AND score<=max_score)",
            sql,
        )
        self.assertIn("ON DELETE RESTRICT", sql)
        cascades = re.findall(r"ON DELETE CASCADE", sql)
        self.assertLessEqual(
            len(cascades),
            1,
            "Faqat assistant action session bilan birga o'chishi mumkin",
        )
        if cascades:
            self.assertRegex(
                sql,
                r"school_assistant_actions[\s\S]+?"
                r"REFERENCES school_assistant_sessions\(id\) ON DELETE CASCADE",
            )

    def test_tenant_group_parent_and_student_privacy_guards(self):
        source = _source(ROUTER_FILE)
        require_roles = python_function_source(ROUTER_FILE, "require_roles")
        self.assertIn("context_id", require_roles)
        self.assertIn("group_id", require_roles)
        self.assertIn("row[\"group_id\"] is None", require_roles)
        self.assertIn("status='active'", require_roles)

        students = python_function_source(ROUTER_FILE, "list_students")
        self.assertIn("school_parent_students", students)
        self.assertIn("ps.parent_user_id=%s", students)
        self.assertIn("student, user_id", students)
        self.assertIn("teacher_can_access_section(", students)
        self.assertIn("s.context_id=r.context_id", students)

        teacher_scope = python_function_source(
            ROUTER_FILE, "teacher_can_access_section"
        )
        self.assertIn("school_workloads", teacher_scope)
        self.assertIn("school_role_assignments", teacher_scope)
        self.assertIn("context_id=%s", teacher_scope)
        self.assertIn("section_id=%s", teacher_scope)
        self.assertIn("group_id=%s", teacher_scope)

        attendance = python_function_source(ROUTER_FILE, "list_attendance")
        self.assertIn("school_parent_students", attendance)
        self.assertIn("parent_user_id=%s", attendance)
        self.assertIn("if student_user_id not in (None, user_id)", attendance)
        self.assertIn("require_roles(", attendance)
        self.assertIn("group_id=section[\"group_id\"]", attendance)

        grades = python_function_source(ROUTER_FILE, "list_grade_entries")
        self.assertIn("school_parent_students", grades)
        self.assertIn("if student_user_id not in (None, user_id)", grades)
        self.assertIn("g.context_id=%s", grades)
        self.assertIn("g.teacher_user_id=%s", grades)

        for mutator in ("mark_attendance", "create_grade_entry"):
            block = python_function_source(ROUTER_FILE, mutator)
            self.assertIn("context_id", block)
            self.assertIn("group_id", block)
            self.assertIn("role_key='student'", block)

    def test_privileged_mutations_require_explicit_human_confirmation(self):
        required = {
            "verify_public_school",
            "commit_draft",
            "assign_staff",
            "create_staff_invite",
            "confirm_timetable",
            "substitute_teacher",
            "assign_student",
            "link_parent_student",
            "create_billing_plan",
            "create_invoice",
            "create_payment",
        }
        for function_name in required:
            block = python_function_source(ROUTER_FILE, function_name)
            self.assertIn(
                "require_human(",
                block,
                f"{function_name} inson tasdig'ini tekshirmaydi",
            )
            self.assertIn("confirmation", block)

        calendar = python_function_source(ROUTER_FILE, "create_calendar_event")
        self.assertIn('request.status == "published"', calendar)
        self.assertIn("require_human(request.confirmation", calendar)

    def test_scheduler_is_rebuilt_and_audited_before_publication(self):
        router = _source(ROUTER_FILE)
        scheduler = _source(SCHEDULER_FILE)
        generate = python_function_source(ROUTER_FILE, "generate_timetable")
        confirm = python_function_source(ROUTER_FILE, "confirm_timetable")

        self.assertIn("run_school_scheduler", router)
        self.assertIn("audit_assignments", router)
        self.assertIn("result = run_school_scheduler(", generate)
        self.assertIn("school_timetable_generations", generate)
        self.assertIn('"ready_to_confirm"', generate)
        self.assertNotIn("'published'", generate)

        self.assertIn("fresh_result = run_school_scheduler(", confirm)
        self.assertIn("publication_audit = audit_assignments(", confirm)
        self.assertIn("fresh_result.hard_conflicts or publication_audit", confirm)
        self.assertIn("stored_slots", confirm)
        self.assertIn("signature", confirm)
        self.assertIn("Jadval qoralamasini qayta yarating", confirm)
        self.assertIn('"timetable.publish"', confirm)

        for contract in (
            "a class, teacher or room cannot occupy",
            "method days",
            "ABSOLUTE_TEACHER_DAILY_MAX = 7",
            "ClassHourPolicy",
            "hard_conflicts",
            "quality_warnings",
            "audit_assignments",
        ):
            self.assertIn(contract, scheduler)

        sql = _source(MIGRATION_FILE)
        for index in (
            "uq_school_slot_section",
            "uq_school_slot_teacher",
            "uq_school_slot_room",
        ):
            self.assertIn(index, sql)

    def test_assistant_cannot_publish_pay_or_bypass_permissions(self):
        source = _source(ROUTER_FILE)
        start = python_function_source(ROUTER_FILE, "start_assistant")
        action = python_function_source(ROUTER_FILE, "assistant_action")
        self.assertIn('"can_confirm_privileged_actions": False', source)
        self.assertIn('"can_bypass_permissions": False', source)
        self.assertIn("ASSISTANT_ACTIONS", action)
        self.assertIn("WHERE id=%s AND user_id=%s FOR UPDATE", action)
        self.assertIn("can_prepare_drafts", start)

        actions_match = re.search(
            r"ASSISTANT_ACTIONS\s*=\s*\{(?P<body>.*?)\}",
            source,
            re.DOTALL,
        )
        self.assertIsNotNone(actions_match)
        actions = actions_match.group("body").upper()
        for forbidden in (
            "PUBLISH",
            "PAYMENT",
            "CREATE_INVITE",
            "ASSIGN_ROLE",
            "CONFIRM_SCHOOL",
        ):
            self.assertNotIn(forbidden, actions)
        self.assertNotIn("create_payment(", action)
        self.assertNotIn("confirm_timetable(", action)
        self.assertNotIn("create_staff_invite(", action)
        self.assertIn('action_id == "SET_DRAFT_VALUE"', action)
        self.assertIn("school_setup_drafts", action)
        self.assertIn("allowed_fields", action)
        self.assertIn('"applied": True', action)

    def test_release_blocker_contracts_are_server_authoritative(self):
        source = _source(ROUTER_FILE)
        substitution = python_function_source(
            ROUTER_FILE, "substitute_teacher"
        )
        timetable = python_function_source(ROUTER_FILE, "list_timetable")
        onboarding = python_function_source(ROUTER_FILE, "commit_draft")
        availability = python_function_source(
            ROUTER_FILE, "put_availability"
        )
        calendar = python_function_source(ROUTER_FILE, "list_calendar")
        makeup = python_function_source(
            ROUTER_FILE, "confirm_calendar_makeup"
        )
        confirm = python_function_source(ROUTER_FILE, "confirm_timetable")

        self.assertIn("lesson_date: date", source)
        self.assertIn("idempotency_key: str", source)
        self.assertIn("school_timetable_exceptions", substitution)
        self.assertNotIn("UPDATE school_timetable_slots", substitution)
        self.assertIn('"substitution": changed', substitution)
        self.assertIn('"idempotent_replay": False', substitution)
        self.assertIn("lesson_date: date | None", timetable)
        self.assertIn("original_teacher_user_id", timetable)

        self.assertIn("max_periods_by_shift", onboarding)
        self.assertIn("max_lessons", onboarding)
        self.assertIn("use_uzbekistan_holidays", onboarding)
        self.assertIn("UZ_FIXED_PUBLIC_HOLIDAYS_V1", onboarding)
        self.assertIn("model_fields_set", availability)
        self.assertIn("method_day=EXCLUDED.method_day", availability)
        self.assertIn("preferred_shift=EXCLUDED.preferred_shift", availability)

        self.assertIn("school_parent_students", calendar)
        self.assertIn("e.group_id", calendar)
        self.assertIn("'cancelled'", makeup)
        self.assertIn("'makeup_extra'", makeup)
        self.assertIn("cancellation_event_id", makeup)
        self.assertIn("school_timetable_exceptions", confirm)
        self.assertIn("future_exceptions", confirm)
        self.assertIn("preserved_slots", confirm)

    def test_dated_lesson_contract_is_bounded_locked_and_effective(self):
        source = _source(ROUTER_FILE)
        bounds = python_function_source(
            ROUTER_FILE, "school_calendar_bounds"
        )
        require_dates = python_function_source(
            ROUTER_FILE, "require_calendar_dates"
        )
        locks = python_function_source(ROUTER_FILE, "lock_context_dates")
        effective = python_function_source(
            ROUTER_FILE, "effective_timetable_rows_for_dates"
        )
        substitution = python_function_source(
            ROUTER_FILE, "substitute_teacher"
        )
        makeup = python_function_source(
            ROUTER_FILE, "confirm_calendar_makeup"
        )
        effective_route = python_function_source(
            ROUTER_FILE, "get_effective_timetable"
        )
        revoke = python_function_source(
            ROUTER_FILE, "revoke_timetable_exception"
        )

        self.assertIn('calendar_settings["starts_on"]', bounds)
        self.assertIn('calendar_settings["ends_on"]', bounds)
        self.assertIn("academic_year_bounds(", bounds)
        self.assertIn("invalid_dates", require_dates)
        self.assertIn("value < starts_on or value > ends_on", require_dates)
        self.assertIn("pg_advisory_xact_lock", locks)
        self.assertIn("hashtextextended", locks)
        self.assertIn("sorted(set(values))", locks)

        for contract in (
            "school_timetable_exceptions",
            "exception_kind='substitution'",
            "exception_kind='makeup_extra'",
            "school_calendar_events",
            "status='published'",
            "target_date=ANY",
            "makeup_event_id",
            "published_makeup_event",
        ):
            self.assertIn(contract, effective)
        self.assertIn("effective_timetable_rows(", substitution)
        self.assertLess(
            substitution.index("lock_context_dates("),
            substitution.index("idempotency_key=%s"),
        )
        self.assertIn("request.candidate_dates", makeup)
        self.assertIn("request.cancellations", makeup)
        self.assertLess(
            makeup.index("lock_context_dates("),
            makeup.index("metadata->>'makeup_key'"),
        )
        self.assertIn("effective_timetable_rows(", effective_route)
        self.assertIn("school_calendar_bounds(", effective_route)

        self.assertIn("require_human(", revoke)
        self.assertIn("lock_context_dates(", revoke)
        self.assertIn("revocation_idempotency_key", revoke)
        self.assertIn("status='cancelled'", revoke)
        self.assertIn('"idempotent_replay": True', revoke)
        self.assertNotIn("UPDATE school_timetable_slots", revoke)

        list_timetable = python_function_source(
            ROUTER_FILE, "list_timetable"
        )
        self.assertIn("if lesson_date is not None", list_timetable)
        self.assertIn("effective_timetable_rows(", list_timetable)
        self.assertIn('"effective": True', list_timetable)
        self.assertIn(
            'schema": "005_school_platform+006_school_timetable_exceptions"',
            source,
        )

    def test_app_lazy_loads_new_school_workspace_and_keeps_legacy_exit(self):
        source = _source(FRONTEND_APP_FILE)
        self.assertIn("const SchoolWorkspace = React.lazy(", source)
        self.assertIn(
            'import("./school/SchoolWorkspace.jsx")',
            source,
        )
        self.assertIn('korinish === "maktab_workspace"', source)
        self.assertIn("<SchoolWorkspace", source)
        self.assertIn('onLegacy={() => setKorinish("maktab_legacy")}', source)
        self.assertIn('korinish === "maktab_legacy"', source)

    def test_load_probe_is_read_only_bounded_and_secret_safe(self):
        source = _source(LOAD_FILE)
        tree = ast.parse(source)
        imports = {
            node.names[0].name.split(".")[0]
            for node in tree.body
            if isinstance(node, ast.Import)
        } | {
            (node.module or "").split(".")[0]
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
        }
        forbidden_third_party = {
            "requests",
            "httpx",
            "aiohttp",
            "numpy",
            "pandas",
        }
        self.assertFalse(imports & forbidden_third_party)
        self.assertIn("urllib", imports)
        self.assertIn("concurrent", imports)
        self.assertIn('API_PREFIX = "/api/maktab-v2"', source)
        self.assertIn('api_url(base_url, "/health")', source)
        self.assertIn('api_url(base_url, "/workspaces")', source)
        self.assertIn('api_url(base_url, "/dashboard"', source)
        self.assertIn('"Authorization"', source)
        self.assertIn('"Bearer "', source)
        self.assertIn("p50", source)
        self.assertIn("p95", source)
        self.assertIn("p99", source)
        self.assertRegex(source, r"MAX_CONCURRENCY\s*=\s*\d+")
        self.assertRegex(source, r"MAX_REQUESTS\s*=\s*\d+")
        self.assertNotRegex(source, r'method\s*=\s*["\'](?:POST|PUT|PATCH|DELETE)')
        self.assertNotRegex(source, r"[?&]token=")
        self.assertNotIn('print(args.token)', source)


if __name__ == "__main__":
    unittest.main()
