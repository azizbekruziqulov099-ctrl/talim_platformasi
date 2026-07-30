"""Static contract tests that do not require a running PostgreSQL server."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTER_FILE = ROOT / "backend" / "modules" / "kindergarten.py"
MIGRATION_FILE = ROOT / "database" / "003_kindergarten_platform.sql"
HARDENING_FILE = ROOT / "database" / "004_kindergarten_hardening.sql"
APP_FILE = ROOT / "backend" / "main.py"
FRONTEND_APP_FILE = ROOT / "frontend" / "src" / "App.jsx"


def route_contracts() -> list[tuple[str, str]]:
    tree = ast.parse(ROUTER_FILE.read_text(encoding="utf-8"))
    contracts: list[tuple[str, str]] = []
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
            ):
                contracts.append((func.attr.upper(), decorator.args[0].value))
    return contracts


class KindergartenContractTests(unittest.TestCase):
    def test_router_is_included_once(self):
        source = APP_FILE.read_text(encoding="utf-8")
        self.assertEqual(
            source.count("app.include_router(create_kindergarten_router(_jwt_tekshir))"),
            1,
        )

    def test_route_method_and_path_pairs_are_unique(self):
        contracts = route_contracts()
        self.assertGreaterEqual(len(contracts), 20)
        self.assertEqual(len(contracts), len(set(contracts)))

    def test_critical_routes_exist(self):
        contracts = set(route_contracts())
        required = {
            ("POST", "/onboarding/start"),
            ("PUT", "/onboarding/{draft_id}/step"),
            ("POST", "/onboarding/{draft_id}/preview"),
            ("POST", "/onboarding/{draft_id}/confirm"),
            ("GET", "/workspaces"),
            ("POST", "/join-requests"),
            ("POST", "/staff/invite"),
            ("POST", "/staff/accept-invite"),
            ("GET", "/dashboard"),
            ("POST", "/groups"),
            ("POST", "/children"),
            ("POST", "/attendance"),
            ("POST", "/daily-reports"),
            ("POST", "/calendar"),
            ("POST", "/billing/plans"),
            ("POST", "/billing/invoices/generate"),
            ("POST", "/billing/invoices/{invoice_id}/payments"),
            ("POST", "/assistant/sessions"),
            ("POST", "/assistant/sessions/{session_id}/actions"),
        }
        self.assertTrue(required.issubset(contracts), required - contracts)

    def test_migration_is_transactional_and_indexed(self):
        sql = MIGRATION_FILE.read_text(encoding="utf-8")
        self.assertTrue(sql.lstrip().startswith("--"))
        self.assertIn("\nBEGIN;", sql)
        self.assertTrue(sql.rstrip().endswith("COMMIT;"))
        for table in (
            "kindergarten_profiles",
            "kindergarten_role_assignments",
            "kindergarten_setup_drafts",
            "assistant_sessions",
            "assistant_action_events",
            "kindergarten_children",
            "kindergarten_attendance",
            "kindergarten_calendar_events",
            "kindergarten_invoices",
            "kindergarten_payments",
        ):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", sql)
        self.assertGreaterEqual(sql.count("CREATE INDEX IF NOT EXISTS"), 20)
        self.assertIn("USING BRIN", sql)

        hardening = HARDENING_FILE.read_text(encoding="utf-8")
        self.assertIn("\nBEGIN;", hardening)
        self.assertTrue(hardening.rstrip().endswith("COMMIT;"))
        self.assertIn("004_kindergarten_hardening", hardening)
        self.assertIn("idempotency_key", hardening)
        self.assertIn("fk_kindergarten_payment_invoice_context", hardening)
        self.assertIn("bogcha_guruh_bolalari", hardening)
        self.assertIn("ranked_roster", hardening)
        self.assertIn("DISTINCT ON (cg.context_id, gb.bola_user_id)", hardening)
        self.assertIn("verification_hold", ROUTER_FILE.read_text(encoding="utf-8"))

    def test_assistant_has_permission_boundaries(self):
        source = ROUTER_FILE.read_text(encoding="utf-8")
        self.assertIn('"can_confirm_privileged_actions": False', source)
        self.assertIn('"can_bypass_permissions": False', source)
        self.assertIn("requires_confirmation", source)

    def test_tenant_and_auth_hardening_contracts(self):
        source = ROUTER_FILE.read_text(encoding="utf-8")
        self.assertIn("def authenticated_user(", source)
        self.assertIn("authorization: str | None = Header", source)
        self.assertIn("def allowed_group_scope(", source)
        self.assertIn("def require_group(", source)
        self.assertIn(
            'PRIVILEGED_ROLES = {"director", "deputy_director", "administrator"}',
            source,
        )
        self.assertIn('("004_kindergarten_hardening",)', source)
        self.assertIn("request.idempotency_key", source)
        self.assertIn("creator_roles = require_roles(", source)
        self.assertIn('after_start: datetime | None = None', source)
        self.assertIn('"next_cursor": next_cursor', source)

    def test_legacy_kindergarten_mutations_sync_to_v2(self):
        source = APP_FILE.read_text(encoding="utf-8")
        self.assertGreaterEqual(
            source.count("_bogcha_v2_rolni_taminla("),
            4,
        )
        self.assertEqual(
            source.count("_bogcha_v2_bolani_taminla("),
            2,
        )
        self.assertEqual(
            source.count("_bogcha_v2_bolani_chiqar("),
            2,
        )
        self.assertIn("_bogcha_v2_xodimni_koddan_otkaz(", source)
        self.assertIn("def _jwt_header_yoki_query(", source)
        self.assertIn("def _bogcha_legacy_faol_talab(", source)
        legacy_groups = source[
            source.index("def opa_mening_guruhlarim("):
            source.index("class BolaQoshish(")
        ]
        self.assertIn("_bogcha_legacy_faol_holat(", legacy_groups)
        legacy_children = source[
            source.index("def opa_bola_qoshish("):
            source.index("class BogchaTolovBelgilash(")
        ]
        self.assertGreaterEqual(
            legacy_children.count("_bogcha_legacy_faol_talab("),
            3,
        )

    def test_jwt_secret_fails_closed(self):
        source = APP_FILE.read_text(encoding="utf-8")
        self.assertIn(
            'if len(JWT_MAXFIY_KALIT.encode("utf-8")) < 32:',
            source,
        )

    def test_staff_codes_are_hashed_and_rate_limited(self):
        source = APP_FILE.read_text(encoding="utf-8")
        self.assertIn("def _xodim_kod_yarat(", source)
        self.assertIn('for _ in range(12)', source)
        self.assertIn('"sha256:" + hashlib.sha256(', source)
        self.assertIn("def _xodim_kod_xato_urinish(", source)
        self.assertIn("INTERVAL '30 minutes'", source)
        self.assertGreaterEqual(source.count("FOR UPDATE"), 3)
        hardening = HARDENING_FILE.read_text(encoding="utf-8")
        self.assertIn("kod NOT LIKE 'sha256:%'", hardening)

    def test_legacy_kindergarten_billing_is_closed(self):
        source = APP_FILE.read_text(encoding="utf-8")
        endpoint = source[
            source.index("def bogcha_tolov_sozlash("):
            source.index('@app.get("/api/admin/bogcha_xodim_shablon")')
        ]
        self.assertIn("status_code=410", endpoint)
        self.assertNotIn("UPDATE bogchalar", endpoint)
        children = source[
            source.index("def opa_guruh_bolalari("):
            source.index('@app.delete("/api/opa/bolani_chiqar")')
        ]
        self.assertNotIn("bogcha_guruh_id", children)
        frontend = FRONTEND_APP_FILE.read_text(encoding="utf-8")
        kindergartens = frontend[
            frontend.index("function BogchalarBolimi("):
            frontend.index("function UniversitetlarBolimi(")
        ]
        self.assertNotIn("bogcha_tolov_sozlash", kindergartens)
        self.assertNotIn("oylikTolov", kindergartens)

    def test_dashboard_checklist_uses_metrics_before_redaction(self):
        source = ROUTER_FILE.read_text(encoding="utf-8")
        dashboard = source[source.index("    def dashboard("):source.index(
            '    @router.get("/groups")'
        )]
        self.assertLess(
            dashboard.index("        checklist = ["),
            dashboard.index('            metrics["groups"] = None'),
        )


if __name__ == "__main__":
    unittest.main()
