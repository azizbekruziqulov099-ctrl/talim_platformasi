import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TeacherRepetitorLimitsContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
        cls.migration = (
            ROOT / "database" / "013_teacher_repetitor_limits.sql"
        ).read_text(encoding="utf-8")

    def test_second_personal_group_is_server_blocked_with_real_price(self):
        self.assertIn("IKKINCHI_TOGARAK_NARXI_UZS = 50_000", self.main)
        self.assertIn('"code": "SECOND_CLUB_PAYMENT_REQUIRED"', self.main)
        self.assertIn("status_code=402", self.main)
        self.assertIn("FOR UPDATE", self.main)

    def test_capacity_is_checked_on_join_approval_and_database_trigger(self):
        self.assertIn("TOGARAK_MAX_TALABA = 25", self.main)
        self.assertGreaterEqual(self.main.count("tasdiqlangan=TRUE"), 4)
        self.assertIn("samtm_togarak_25_orin_himoyasi", self.migration)
        self.assertIn("FOR UPDATE", self.migration)
        self.assertIn("CHECK (max_talaba BETWEEN 1 AND 25)", self.migration)
        self.assertIn("uq_togarak_azo_active", self.migration)

    def test_repetitor_is_persisted_for_groups_and_plans(self):
        self.assertIn('guruh_turi: str = "togarak"', self.main)
        self.assertIn('guruh_turi: str = "sinf"', self.main)
        self.assertIn("('sinf','guruh','grupa','repetitor')", self.migration)
        self.assertIn("('togarak','repetitor')", self.migration)

    def test_university_group_cannot_be_used_to_bypass_personal_quota(self):
        self.assertIn("Bu universitet guruhiga kurs ochish vakolati", self.main)
        self.assertIn("f.universitet_id=u.universitet_id", self.main)

    def test_institution_creation_is_admin_only_except_tutor_mode(self):
        modules = {
            name: (ROOT / "backend" / "modules" / name).read_text(encoding="utf-8")
            for name in (
                "kindergarten.py",
                "school.py",
                "learning_center.py",
                "institute.py",
            )
        }
        self.assertGreaterEqual(modules["kindergarten.py"].count("require_creation_admin(cur, user_id)"), 2)
        self.assertGreaterEqual(modules["school.py"].count("require_creation_admin(cur, user_id)"), 2)
        self.assertGreaterEqual(modules["institute.py"].count("require_creation_admin(cur, user_id)"), 2)
        self.assertIn('operator_model == "independent_tutor"', modules["learning_center.py"])
        self.assertIn('user["role"] == "oqituvchi"', modules["learning_center.py"])


if __name__ == "__main__":
    unittest.main()
