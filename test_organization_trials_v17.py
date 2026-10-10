import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class OrganizationTrialsV17Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
        cls.module = (
            ROOT / "backend" / "modules" / "organization_trials.py"
        ).read_text(encoding="utf-8")
        cls.migration = (
            ROOT / "database" / "014_organization_trials_wallet.sql"
        ).read_text(encoding="utf-8")

    def test_only_private_self_service_and_server_owned_trial_clock(self):
        self.assertIn('request.ownership_type != "private"', self.module)
        self.assertIn("PUBLIC_OR_STATE_REQUIRES_VERIFICATION", self.module)
        self.assertIn("NOW()+INTERVAL '30 days'", self.module)
        self.assertIn("activation_price_uzs=200000", self.migration)
        self.assertNotIn("trial_ends_at: datetime", self.module)

    def test_explicit_atomic_activation_and_immutable_ledger(self):
        self.assertIn("request.confirm_charge is not True", self.module)
        self.assertIn("EXPLICIT_CHARGE_CONFIRMATION_REQUIRED", self.module)
        self.assertGreaterEqual(self.module.count("FOR UPDATE"), 7)
        self.assertIn("organization_wallet_ledger", self.module)
        self.assertIn("samtm_immutable_wallet_ledger", self.migration)
        self.assertIn("uq_organization_single_activation_debit", self.migration)
        self.assertIn("IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST", self.module)

    def test_no_self_topup_and_admin_credit_is_audited(self):
        self.assertIn('@router.post("/admin/hamyon-toldirish")', self.module)
        self.assertIn("if not system_admin(cur, admin_user_id)", self.module)
        self.assertIn("admin_verified_credit", self.module)
        self.assertNotIn('@router.post("/hamyon-toldirish")', self.module)

    def test_expired_organization_is_read_only_not_deleted(self):
        self.assertIn("samtm_organization_trial_write_guard", self.migration)
        self.assertIn("BEFORE INSERT OR UPDATE OR DELETE", self.migration)
        self.assertIn("lifecycle_status='read_only'", self.module)
        self.assertNotIn("DELETE FROM organization_trials", self.module)
        self.assertIn('"code": "ORGANIZATION_READ_ONLY"', self.main)
        self.assertIn("status_code=423", self.main)

    def test_trial_abuse_is_race_safe(self):
        self.assertIn("uq_one_unpaid_trial_per_creator", self.migration)
        self.assertIn("WHERE lifecycle_status IN ('trial','read_only')", self.migration)
        self.assertIn("SELECT user_id,role FROM users WHERE user_id=%s FOR UPDATE", self.module)
        self.assertIn("pg_advisory_xact_lock", self.module)
        self.assertIn("UNPAID_ORGANIZATION_EXISTS", self.module)

    def test_trial_is_bound_to_real_module_workspaces(self):
        for table in (
            "kindergarten_profiles",
            "school_profiles",
            "center_profiles",
            "institute_profiles",
            "kindergarten_role_assignments",
            "school_role_assignments",
            "center_role_assignments",
            "institute_role_assignments",
        ):
            self.assertIn(table, self.module)
        self.assertIn("INSERT INTO learning_contexts", self.module)
        self.assertIn("INSERT INTO context_memberships", self.module)
        self.assertIn("organization_v17_id", self.main)
        self.assertIn("public.organization_trials", self.main)

    def test_unified_routes_and_dto_fields_are_stable(self):
        for route in (
            '@router.get("/meniki")',
            '@router.post("/sinov-boshlash")',
            '@router.post("/{organization_id}/faollashtirish")',
            '@router.post("/admin/hamyon-toldirish")',
        ):
            self.assertIn(route, self.module)
        for field in (
            "lifecycle_status",
            "access_mode",
            "trial_started_at",
            "trial_ends_at",
            "days_remaining",
            "activation_price_uzs",
            "can_activate",
            "wallet_balance_sufficient",
        ):
            self.assertIn(field, self.module)


if __name__ == "__main__":
    unittest.main()
