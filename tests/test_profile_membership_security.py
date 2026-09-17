"""Execute the real profile handler against a controlled DB boundary.

No production database or optional deployment dependencies are needed.
"""

import ast
import re
from pathlib import Path
from types import SimpleNamespace
import unittest


class HTTPException(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code


class Cursor:
    def __init__(self, membership):
        self.membership = membership
        self.calls = []
        self.closed = False

    def execute(self, sql, params=()):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.membership

    def close(self):
        self.closed = True


class Connection:
    def __init__(self, membership):
        self.cur = Cursor(membership)
        self.committed = False
        self.closed = False

    def cursor(self):
        return self.cur

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


class ProfileMembershipSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(__file__).resolve().parents[1] / "samtm_platform.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        handler = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "profil_yangila")
        # Talaba (oliy ta'lim) Sinf qiymatlari — "2 kurs", "1 kurs magistr" —
        # handler shu sof yordamchilar orqali tekshiriladi; ular ham manbadan olinadi.
        yordamchilar = {
            "_TALABA_SINF_REGEX", "_talaba_sinf_matni", "_talaba_sinfini_ochish",
            "_sinf_talaba_mi", "_sinf_qiymati_togri_mi", "_sinf_qiymatini_normallashtir",
        }
        helper_nodes = [
            n for n in tree.body
            if (isinstance(n, ast.FunctionDef) and n.name in yordamchilar)
            or (isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in yordamchilar for t in n.targets))
        ]
        handler.decorator_list = []
        cls.handler_code = compile(ast.Module(body=helper_nodes + [handler], type_ignores=[]), str(source), "exec")

    def invoke(self, membership, **changes):
        self.db = Connection(membership)
        fields = {
            key: None for key in (
                "full_name", "region", "district", "tugilgan_sana", "maktab_raqami",
                "maktab_turi", "sinf", "sinf_harfi", "jins", "oqituvchi_fani",
                "asosiy_til", "ovoz_jinsi", "maktab_id",
            )
        }
        fields.update(token="test-session", **changes)
        namespace = {
            "re": re,
            "ProfilYangilash": SimpleNamespace,
            "HTTPException": HTTPException,
            "MAKTAB_TURLARI": {"oddiy": "Oddiy"},
            "_jwt_tekshir": lambda token: 101,
            "_db": lambda: self.db,
        }
        exec(self.handler_code, namespace)
        return namespace["profil_yangila"](SimpleNamespace(**fields))

    def assert_no_update(self):
        self.assertFalse(any(sql.startswith("UPDATE") for sql, _ in self.db.cur.calls))
        self.assertFalse(self.db.committed)
        self.assertTrue(self.db.closed)

    def test_school_director_cannot_move_authority_to_another_school(self):
        with self.assertRaises(HTTPException) as error:
            self.invoke({"maktab_id": 10}, maktab_id=20, full_name="New name")
        self.assertEqual(error.exception.status_code, 403)
        self.assert_no_update()

    def test_unaffiliated_account_cannot_self_assign_school_membership(self):
        with self.assertRaises(HTTPException) as error:
            self.invoke({"maktab_id": None}, maktab_id=20)
        self.assertEqual(error.exception.status_code, 403)
        self.assert_no_update()

    def test_legacy_form_may_resend_same_school_and_update_display_name(self):
        result = self.invoke({"maktab_id": 10}, maktab_id=10, full_name=" Aziz ")
        self.assertEqual(result, {"holat": "saqlandi"})
        updates = [(sql, args) for sql, args in self.db.cur.calls if sql.startswith("UPDATE")]
        self.assertEqual(updates, [("UPDATE users SET full_name=%s WHERE user_id=%s", ["Aziz", 101])])
        self.assertTrue(self.db.committed)

    def test_personal_profile_edit_does_not_require_school_membership(self):
        self.assertEqual(self.invoke({"maktab_id": None}, sinf="8"), {"holat": "saqlandi"})
        self.assertEqual(self.db.cur.calls, [("UPDATE users SET class=%s WHERE user_id=%s", ["8", 101])])

    def test_same_school_without_other_changes_is_noop(self):
        self.assertEqual(self.invoke({"maktab_id": 10}, maktab_id=10), {"holat": "ozgarish_yoq"})
        self.assert_no_update()

    def test_missing_account_cannot_be_linked(self):
        with self.assertRaises(HTTPException) as error:
            self.invoke(None, maktab_id=20)
        self.assertEqual(error.exception.status_code, 404)
        self.assert_no_update()

    def test_talaba_kurs_value_is_accepted_and_canonicalised(self):
        # 1–11 sinfdan tashqari o'quvchi: "2-kurs" → bazaga kanonik "2 kurs" yoziladi
        self.assertEqual(self.invoke({"maktab_id": None}, sinf="2-kurs"), {"holat": "saqlandi"})
        self.assertEqual(self.db.cur.calls, [("UPDATE users SET class=%s WHERE user_id=%s", ["2 kurs", 101])])
        self.assertEqual(self.invoke({"maktab_id": None}, sinf="1 kurs magistr"), {"holat": "saqlandi"})
        self.assertEqual(self.db.cur.calls[-1][1], ["1 kurs magistr", 101])

    def test_unknown_class_values_are_still_rejected(self):
        for yomon in ("12", "0", "2-sinf", "7 kurs", "abituriyent"):
            with self.assertRaises(HTTPException, msg=yomon) as error:
                self.invoke({"maktab_id": None}, sinf=yomon)
            self.assertEqual(error.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
