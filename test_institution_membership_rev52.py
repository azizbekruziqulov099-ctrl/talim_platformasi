"""Execute membership and code issuance code with deterministic DB boundaries.

These tests do not claim to exercise a live PostgreSQL server. SQL calls,
transaction decisions and actual role/identity policy are verified together.
"""
import ast
import hashlib
from pathlib import Path
import secrets
import string
import unittest
from types import SimpleNamespace

from modules.institution_membership import (
    IDENTITIES, REFERENCES, MembershipError, _claim_university, _claim_legacy_university,
    has_login_identity, normalize_code, redeem_code, reissue_school_code, search_school_people, transfer_references,
)


class Cursor:
    def __init__(self, owner, *, old_id=-10, current_id=-20, owned_old=False):
        self.owner = owner
        self.calls = []
        self.rows = []
        self.closed = False
        self.old_id, self.current_id = old_id, current_id
        self.owned_old = owned_old
        self.old = {"user_id": old_id, "maktab_id": 7, "role": "oqituvchi", "lavozim": "fan_oqituvchisi", "jadval_raqami": 23, "fanlari": "Algebra"}
        self.old["full_name"] = "Namuna O'qituvchi"
        self.current = {"user_id": current_id, "role": "kabutar"}
        self.invite = {"stored_code": "sha256:abc", "placeholder_id": old_id, "ishlatildi": False, "hali_yangi": True}
        self.fail_table = None
        self.university = None
        self.group_rows = set()
        self.parent_schools = [7]
        self.columns = {table: set(fields) for table, fields in REFERENCES["maktab"].items()}
        self.columns.update({table: {field} for table, field in IDENTITIES.items()})
        self.columns["users"] = set(self.old) | {"markaz_id", "bogcha_id", "universitet_id", "kabutar_education_ready"}
        self.columns["telefon_hisob"] = {"user_id"}
        self.columns["school_person_profiles"].update(("school_id", "person_type"))

    def execute(self, query, params=()):
        self.calls.append((" ".join(query.split()), tuple(params)))
        self.rows = []
        if self.fail_table and query.startswith('UPDATE "' + self.fail_table + '"'):
            error = RuntimeError("simulated unique constraint")
            error.pgcode = "23505"
            raise error
        if "FROM xodim_kod WHERE kod IN" in query:
            self.rows = [self.invite] if self.invite else []
        elif "FROM users WHERE user_id=ANY" in query:
            self.rows = [self.old, self.current]
        elif "SELECT * FROM users WHERE user_id=%s FOR UPDATE" in query:
            self.rows = [self.old]
        elif "information_schema.columns" in query:
            self.rows = [{"table_name": table, "column_name": field} for table, fields in self.columns.items() if table in params[0] for field in fields]
        elif 'FROM "google_hisob"' in query:
            uid = params[0]
            self.rows = [{"exists": 1}] if uid == self.current_id or (uid == self.old_id and self.owned_old) else []
        elif "SELECT nomi FROM maktablar" in query:
            self.rows = [{"nomi": "52-maktab"}]
        elif "SELECT * FROM maktablar WHERE id=%s FOR UPDATE" in query:
            self.rows = [{"id": 7, "nomi": "52-maktab", "lifecycle_status": "active"}]
        elif "SELECT school_id FROM school_person_profiles" in query or query.startswith("SELECT child.maktab_id AS school_id"):
            self.rows = [{"school_id": school_id} for school_id in self.parent_schools]
        elif query.startswith("SELECT u.user_id,u.full_name,u.role FROM users u"):
            self.rows = [{"user_id": self.old_id, "full_name": self.old["full_name"], "role": self.old["role"]}]
        elif "SELECT 1 FROM school_person_profiles" in query:
            self.rows = [{"exists": 1}] if params[1] == 7 else []
        elif self.university and "FROM universitet_taklif_kodlari WHERE kod_hash" in query:
            self.rows = [self.university]
        elif self.university and "SELECT nomi FROM universitetlar" in query:
            self.rows = [{"nomi": "Pedagogika instituti"}]
        elif self.university and "SELECT qt.*" in query:
            self.rows = [{"id": 3, "user_id": self.old_id, "yonalish_faol": True, "guruh_id": 9}]
        elif self.university and query.startswith('UPDATE "universitet_guruh_azolari"'):
            new_id, old_id = params
            for group, uid in tuple(self.group_rows):
                if uid == old_id:
                    if (group, new_id) in self.group_rows:
                        error = RuntimeError("duplicate group membership")
                        error.pgcode = "23505"
                        raise error
                    self.group_rows.remove((group, old_id))
                    self.group_rows.add((group, new_id))
        elif self.university and "INSERT INTO universitet_guruh_azolari" in query:
            self.group_rows.add((9, params[0]))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows

    def close(self):
        self.closed = True


class Connection:
    def __init__(self, **options):
        self.commits = 0
        self.rollbacks = 0
        self.closed = False
        self.cur = Cursor(self, **options)

    def cursor(self):
        return self.cur

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def platform(conn, *, archived=False, locked=False, manager=True):
    return SimpleNamespace(
        _db=lambda: conn,
        _xodim_kod_variantlari=lambda code: (code, "sha256:" + hashlib.sha256(code.encode()).hexdigest()),
        _xodim_kod_yarat=lambda: ("NEWCODE12345A", "sha256:" + hashlib.sha256(b"NEWCODE12345A").hexdigest()),
        _xodim_kod_subject=lambda kind, uid: f"{kind}:{uid}",
        _xodim_kod_jadvali=lambda cur: None,
        _muassasa_jadvali=lambda cur: None,
        _xodim_kod_bloklanganmi=lambda cur, subject: locked,
        _xodim_kod_xato_urinish=lambda cur, subject: cur.execute("attempt_failed", (subject,)),
        _xodim_kod_urinishni_tozalash=lambda cur, subject: cur.execute("attempt_clear", (subject,)),
        institution_is_archived=lambda *args: archived,
        _maktab_boshqaruvchi_mi=lambda cur, actor_id, school_id: manager,
    )


class MembershipTests(unittest.TestCase):
    def test_concurrent_rotation_between_lookup_and_lock_does_not_transfer_stale_code(self):
        conn = Connection()
        original_execute = conn.cur.execute
        def rotate_on_identity_lock(query, params=()):
            if params == ("auth-user:-10",):
                conn.cur.invite = {**conn.cur.invite, "ishlatildi": True}
            original_execute(query, params)
        conn.cur.execute = rotate_on_identity_lock
        with self.assertRaises(MembershipError) as caught:
            redeem_code(platform(conn), -20, "ABCDEFGH1234")
        self.assertEqual(caught.exception.status_code, 409)
        queries = [q for q, _ in conn.cur.calls]
        self.assertEqual(sum("FROM xodim_kod WHERE kod IN" in q for q in queries), 2)
        self.assertFalse(any(q.startswith(("UPDATE", "INSERT", "DELETE")) for q in queries))

    def test_redeem_and_rotation_lock_source_before_any_code_row(self):
        for operation in (lambda p: redeem_code(p, -20, "ABCDEFGH1234"), lambda p: reissue_school_code(p, 999, 7, -10)):
            conn = Connection()
            operation(platform(conn))
            source_lock = next(i for i, (q, p) in enumerate(conn.cur.calls) if "pg_advisory_xact_lock" in q and p == ("auth-user:-10",))
            code_locks = [i for i, (q, _) in enumerate(conn.cur.calls) if "FROM xodim_kod" in q and "FOR UPDATE" in q]
            self.assertTrue(code_locks)
            self.assertTrue(all(source_lock < index for index in code_locks))

    def test_historical_consumed_sms_counts_as_account_ownership(self):
        cur = ScriptCursor([{"exists": 1}])
        columns = {"telefon_hisob": {"telefon", "user_id"}, "telefon_tasdiq_kod": {"telefon", "ishlatildi"}}
        self.assertTrue(has_login_identity(cur, -10, columns))
        self.assertIn("tk.ishlatildi=TRUE", cur.calls[0][0])
        self.assertEqual(cur.calls[0][1], (-10,))

    def test_admin_phone_without_consumed_sms_does_not_prove_ownership(self):
        cur = ScriptCursor([None])
        columns = {"telefon_hisob": {"telefon", "user_id"}, "telefon_tasdiq_kod": {"telefon", "ishlatildi"}}
        self.assertFalse(has_login_identity(cur, -10, columns))
        missing_sms_table = ScriptCursor([])
        self.assertFalse(has_login_identity(missing_sms_table, -10, {"telefon_hisob": {"telefon", "user_id"}}))
        self.assertEqual(missing_sms_table.calls, [])

    def test_office_separators_normalized_without_changing_code(self):
        self.assertEqual(normalize_code(" abcd–efgh 1234\n"), "ABCDEFGH1234")
        for value in ("1234", "A" * 13, "ABCD/EFGH1234", ""):
            with self.assertRaises(MembershipError):
                normalize_code(value)

    def test_google_negative_account_gets_teacher_and_all_existing_assignments(self):
        conn = Connection()
        result = redeem_code(platform(conn), -20, "ABCD-EFGH-1234")
        self.assertEqual(result["role"], "oqituvchi")
        self.assertEqual(result["muassasa_id"], 7)
        queries = [query for query, _ in conn.cur.calls]
        for table in ("maktab_dars_birikmalari", "maktab_sinflari", "aqlli_oqituvchi_vaqti_v2", "aqlli_jadval_slotlari_v2", "aqlli_mavzu_taqvimi_v2", "school_teacher_assignments"):
            self.assertTrue(any(query.startswith('UPDATE "' + table + '"') for query in queries), table)
        update = next((q, p) for q, p in conn.cur.calls if q.startswith("UPDATE users SET maktab_id=%s"))
        self.assertIn("role=%s", update[0])
        self.assertIn("oqituvchi", update[1])
        self.assertIn('"jadval_raqami"=%s', update[0])
        # Release the imported timetable number before assigning its unique value.
        self.assertLess(next(i for i, q in enumerate(queries) if q.startswith("UPDATE users SET maktab_id=NULL")), queries.index(update[0]))
        self.assertEqual(conn.commits, 1)
        self.assertTrue(conn.closed and conn.cur.closed)

    def test_already_owned_negative_placeholder_cannot_be_claimed(self):
        conn = Connection(owned_old=True)
        with self.assertRaises(MembershipError) as caught:
            redeem_code(platform(conn), -20, "ABCDEFGH1234")
        self.assertEqual(caught.exception.status_code, 409)
        self.assertFalse(any(query.startswith("UPDATE") for query, _ in conn.cur.calls))
        self.assertEqual(conn.commits, 0)

    def test_pupil_takes_admin_class_and_existing_roster(self):
        conn = Connection()
        conn.cur.old.update(role="oquvchi", lavozim=None, **{"class": "10", "class_letter": "A"})
        conn.cur.current.update(role="oquvchi", **{"class": "5"})
        conn.cur.columns["users"].update(("class", "class_letter"))
        result = redeem_code(platform(conn), -20, "ABCDEFGH1234")
        self.assertEqual(result["role"], "oquvchi")
        self.assertTrue(any(q.startswith('UPDATE "maktab_sinf_azolari"') and p == (-20, -10) for q, p in conn.cur.calls))
        update = next((q, p) for q, p in conn.cur.calls if q.startswith("UPDATE users SET maktab_id=%s"))
        self.assertIn('"class"=%s', update[0])
        self.assertIn("10", update[1])

    def test_parent_uses_admin_person_profile_and_preserves_child_link(self):
        conn = Connection()
        conn.cur.old.update(role="ota-ona", lavozim=None, maktab_id=None)
        result = redeem_code(platform(conn), -20, "ABCDEFGH1234")
        self.assertEqual(result["role"], "ota-ona")
        self.assertEqual(result["muassasa_id"], 7)
        self.assertTrue(any(q.startswith('UPDATE "parent_child" SET "parent_id"') and p == (-20, -10) for q, p in conn.cur.calls))

    def test_positive_real_user_never_transferred(self):
        conn = Connection(old_id=123)
        with self.assertRaises(MembershipError):
            redeem_code(platform(conn), -20, "ABCDEFGH1234")
        self.assertFalse(any(query.startswith("UPDATE") for query, _ in conn.cur.calls))

    def test_expired_used_and_unknown_codes_only_record_failed_attempt(self):
        for invite, status in ((None, 400), ({"ishlatildi": True}, 409), ({"hali_yangi": False}, 410)):
            conn = Connection()
            if invite is None:
                conn.cur.invite = None
            else:
                conn.cur.invite.update(invite)
            with self.assertRaises(MembershipError) as caught:
                redeem_code(platform(conn), -20, "ABCDEFGH1234")
            self.assertEqual(caught.exception.status_code, status)
            self.assertTrue(any(q == "attempt_failed" for q, _ in conn.cur.calls))
            self.assertFalse(any(q.startswith("UPDATE") for q, _ in conn.cur.calls))

    def test_archived_institution_does_not_consume_code(self):
        conn = Connection()
        with self.assertRaises(MembershipError) as caught:
            redeem_code(platform(conn, archived=True), -20, "ABCDEFGH1234")
        self.assertEqual(caught.exception.status_code, 410)
        self.assertEqual(conn.commits, 0)
        self.assertFalse(any(q.startswith("UPDATE xodim_kod") for q, _ in conn.cur.calls))

    def test_uniqueness_failure_rolls_back_without_consuming(self):
        conn = Connection()
        conn.cur.fail_table = "maktab_dars_birikmalari"
        with self.assertRaises(MembershipError) as caught:
            redeem_code(platform(conn), -20, "ABCDEFGH1234")
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(conn.commits, 0)
        self.assertEqual(conn.rollbacks, 1)
        self.assertFalse(any(q.startswith("UPDATE xodim_kod") for q, _ in conn.cur.calls))

    def test_login_identities_never_moved_and_unverified_phone_reservation_removed(self):
        conn = Connection()
        redeem_code(platform(conn), -20, "ABCDEFGH1234")
        mutations = [q for q, _ in conn.cur.calls if q.startswith(("UPDATE", "INSERT", "DELETE"))]
        for table in IDENTITIES:
            self.assertFalse(any(table in q for q in mutations), table)
        self.assertIn("DELETE FROM telefon_hisob WHERE user_id=%s", mutations)

    def test_second_institution_preserves_first_and_adds_membership(self):
        conn = Connection()
        conn.cur.current.update(maktab_id=88, role="oqituvchi", lavozim="direktor")
        redeem_code(platform(conn), -20, "ABCDEFGH1234")
        update = next(q for q, _ in conn.cur.calls if q.startswith("UPDATE users SET kabutar_education_ready"))
        self.assertNotIn("maktab_id", update)
        self.assertTrue(any(q.startswith("INSERT INTO foydalanuvchi_muassasalari") and p == (-20, "maktab", 7, "fan_oqituvchisi") for q, p in conn.cur.calls))

    def test_reissued_code_repairs_role_left_wrong_by_old_claimant(self):
        conn = Connection()
        conn.cur.current.update(maktab_id=7, role="oquvchi", lavozim="fan_oqituvchisi")
        redeem_code(platform(conn), -20, "ABCDEFGH1234")
        update = next((q, p) for q, p in conn.cur.calls if q.startswith("UPDATE users SET maktab_id=%s"))
        self.assertIn("role=%s", update[0])
        self.assertIn("oqituvchi", update[1])

    def test_shared_rate_lock_before_code_lookup(self):
        conn = Connection()
        with self.assertRaises(MembershipError) as caught:
            redeem_code(platform(conn, locked=True), -20, "ABCDEFGH1234")
        self.assertEqual(caught.exception.status_code, 429)
        self.assertFalse(any("FROM xodim_kod WHERE" in q for q, _ in conn.cur.calls))


class ScriptCursor:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def execute(self, query, params=()):
        self.calls.append((" ".join(query.split()), tuple(params)))

    def fetchone(self):
        return next(self.replies)

    def fetchall(self):
        return next(self.replies)


class UniversityTests(unittest.TestCase):
    def test_legacy_admin_university_code_moves_existing_exact_role(self):
        cur = ScriptCursor([[{"id": 3}], {"id": 3, "user_id": -10, "faol": True, "rol": "rektor"}])
        sync = []
        institute = SimpleNamespace(_require_active_university_source=lambda *args: None, _sync_legacy_leader=lambda *args: sync.append(args))
        result = _claim_legacy_university(cur, {"user_id": -10, "universitet_id": 5, "lavozim": "rektor"}, -20, institute)
        self.assertEqual(result, ("rektor", "oqituvchi"))
        self.assertTrue(any(q.startswith("UPDATE universitet_xodim_rollari") and p == (-20, 3, -10) for q, p in cur.calls))

    def test_student_redeem_updates_admission(self):
        cur = ScriptCursor([
            {"id": 3, "user_id": -10, "yonalish_faol": True, "guruh_id": 9}, None,
        ])
        institute = SimpleNamespace(_require_active_university_source=lambda *args: None)
        result = _claim_university(cur, {"universitet_id": 5, "placeholder_user_id": -10, "turi": "talaba", "qabul_talaba_id": 3, "xodim_rol_id": None}, {"user_id": -10}, -20, institute)
        self.assertEqual(result, ("talaba", "oquvchi"))
        self.assertTrue(any("birinchi_kirish_at=NOW()" in q and p == (-20, 3) for q, p in cur.calls))

    def test_existing_placeholder_group_transfers_before_ensure_insert(self):
        conn = Connection()
        conn.cur.old.update(maktab_id=None, universitet_id=5, role="oquvchi", lavozim="talaba")
        conn.cur.columns["universitet_taklif_kodlari"] = {"id", "placeholder_user_id", "kod_hash"}
        conn.cur.columns.update({table: set(fields) for table, fields in REFERENCES["universitet"].items()})
        conn.cur.university = {"id": 10, "universitet_id": 5, "placeholder_user_id": -10, "turi": "talaba", "qabul_talaba_id": 3, "xodim_rol_id": None}
        conn.cur.group_rows = {(9, -10)}
        institute = SimpleNamespace(_require_active_university_source=lambda *args: None, _audit=lambda *args: None)
        result = redeem_code(platform(conn), -20, "ABCDEFGH1234", institute=institute)
        self.assertEqual(result["lavozim"], "talaba")
        self.assertEqual(conn.cur.group_rows, {(9, -20)})
        self.assertEqual(conn.commits, 1)

    def test_independently_consumed_university_invite_is_rejected(self):
        cur = ScriptCursor([])
        institute = SimpleNamespace(_require_active_university_source=lambda *args: None)
        with self.assertRaises(MembershipError):
            _claim_university(cur, {"universitet_id": 5, "ishlatildi_at": "2026-09-13"}, {"user_id": -10}, -20, institute)
        self.assertEqual(cur.calls, [])

    def test_student_cannot_take_over_another_claimed_admission(self):
        cur = ScriptCursor([{"id": 3, "user_id": 999, "yonalish_faol": True}])
        institute = SimpleNamespace(_require_active_university_source=lambda *args: None)
        with self.assertRaises(MembershipError):
            _claim_university(cur, {"universitet_id": 5, "placeholder_user_id": -10, "turi": "talaba", "qabul_talaba_id": 3}, {"user_id": -10}, -20, institute)
        self.assertFalse(any(q.startswith("UPDATE") for q, _ in cur.calls))

    def test_staff_gets_exact_admin_assigned_role_and_legacy_leadership(self):
        cur = ScriptCursor([{"id": 3, "user_id": -10, "faol": True, "rol": "dekan", "fakultet_id": 8}, {"faol": True}])
        sync = []
        institute = SimpleNamespace(_require_active_university_source=lambda *args: None, _sync_legacy_leader=lambda *args: sync.append(args))
        result = _claim_university(cur, {"universitet_id": 5, "placeholder_user_id": -10, "turi": "xodim", "xodim_rol_id": 3}, {"user_id": -10}, -20, institute)
        self.assertEqual(result, ("dekan", "oqituvchi"))
        self.assertEqual(sync[0][1:], (5, -20, "dekan", 8, None))

    def test_archived_staff_scope_does_not_grant_role(self):
        cur = ScriptCursor([{"id": 3, "user_id": -10, "faol": True, "rol": "dekan", "fakultet_id": 8}, {"faol": False}])
        institute = SimpleNamespace(_require_active_university_source=lambda *args: None)
        with self.assertRaises(MembershipError):
            _claim_university(cur, {"universitet_id": 5, "placeholder_user_id": -10, "turi": "xodim", "xodim_rol_id": 3}, {"user_id": -10}, -20, institute)
        self.assertFalse(any(q.startswith("UPDATE") for q, _ in cur.calls))


class IssuanceTests(unittest.TestCase):
    def issuer(self, owned):
        path = Path(__file__).resolve().parents[1] / "modules/school_institution_v23.py"
        tree = ast.parse(path.read_text())
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_issue_import_person_code")
        namespace = {"hashlib": hashlib, "secrets": secrets, "string": string, "has_login_identity": lambda *args: owned}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
        return namespace[function.name]

    def test_imported_pupil_and_parent_receive_unique_hashed_personal_codes(self):
        cur = ScriptCursor([])
        issue = self.issuer(False)
        first = issue(cur, -10, "O'quvchi", "oquvchi")
        second = issue(cur, -11, "Ota-ona", "ota-ona")
        self.assertNotEqual(first["code"], second["code"])
        self.assertEqual(len(first["code"]), 12)
        inserted = [(q, p) for q, p in cur.calls if q.startswith("INSERT INTO xodim_kod")]
        self.assertEqual(inserted[0][1], ("sha256:" + hashlib.sha256(first["code"].encode()).hexdigest(), -10))

    def test_existing_negative_google_account_is_not_given_a_transfer_code(self):
        cur = ScriptCursor([])
        self.assertIsNone(self.issuer(True)(cur, -20, "Haqiqiy hisob", "oquvchi"))
        self.assertEqual(cur.calls, [])


class TargetedSchoolReissueTests(unittest.TestCase):
    def test_parent_with_two_school_scopes_is_not_silently_assigned_one(self):
        for operation in (lambda p: reissue_school_code(p, 999, 7, -10), lambda p: redeem_code(p, -20, "ABCDEFGH1234")):
            conn = Connection()
            conn.cur.old.update(role="ota-ona", maktab_id=None)
            conn.cur.parent_schools = [7, 8]
            with self.assertRaises(MembershipError):
                operation(platform(conn))
            self.assertFalse(any(q.startswith(("UPDATE", "INSERT", "DELETE")) for q, _ in conn.cur.calls))

    def test_parent_with_only_child_relation_can_reissue_and_claim(self):
        for operation in (lambda p: reissue_school_code(p, 999, 7, -10), lambda p: redeem_code(p, -20, "ABCDEFGH1234")):
            conn = Connection()
            conn.cur.old.update(role="ota-ona", maktab_id=None)
            conn.cur.columns.pop("school_person_profiles")
            result = operation(platform(conn))
            self.assertEqual(result["role"], "ota-ona")

    def test_rotates_consumed_person_code_without_touching_assignments(self):
        conn = Connection()
        conn.cur.invite["ishlatildi"] = True
        result = reissue_school_code(platform(conn), 999, 7, -10)
        self.assertEqual(result["code"], "NEWCODE12345A")
        self.assertEqual(result["user_id"], -10)
        mutations = [(q, p) for q, p in conn.cur.calls if q.startswith(("UPDATE", "INSERT", "DELETE"))]
        self.assertEqual(len(mutations), 2)
        self.assertTrue(mutations[0][0].startswith("UPDATE xodim_kod "))
        self.assertTrue(mutations[1][0].startswith("INSERT INTO xodim_kod("))
        self.assertEqual(conn.commits, 1)
        self.assertTrue(conn.closed and conn.cur.closed)

    def test_teacher_without_school_manager_authority_cannot_reissue(self):
        conn = Connection()
        with self.assertRaises(MembershipError) as caught:
            reissue_school_code(platform(conn, manager=False), 888, 7, -10)
        self.assertEqual(caught.exception.status_code, 403)
        self.assertEqual(conn.cur.calls, [])

    def test_manager_of_other_school_cannot_reissue_this_person(self):
        conn = Connection()
        with self.assertRaises(MembershipError) as caught:
            reissue_school_code(platform(conn), 999, 88, -10)
        self.assertEqual(caught.exception.status_code, 403)
        self.assertFalse(any(q.startswith(("UPDATE", "INSERT", "DELETE")) for q, _ in conn.cur.calls))

    def test_owned_negative_google_account_cannot_be_reissued(self):
        conn = Connection(owned_old=True)
        with self.assertRaises(MembershipError) as caught:
            reissue_school_code(platform(conn), 999, 7, -10)
        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(conn.commits, 0)
        self.assertFalse(any(q.startswith(("UPDATE", "INSERT", "DELETE")) for q, _ in conn.cur.calls))

    def test_school_pupil_and_parent_can_get_personal_codes(self):
        for role in ("oquvchi", "ota-ona"):
            conn = Connection()
            conn.cur.old.update(role=role, lavozim=None)
            if role == "ota-ona":
                conn.cur.old["maktab_id"] = None
                conn.cur.columns["school_person_profiles"].update(("school_id", "person_type"))
            result = reissue_school_code(platform(conn), 999, 7, -10)
            self.assertEqual(result["role"], role)

    def test_archived_school_code_is_not_rotated(self):
        conn = Connection()
        with self.assertRaises(MembershipError) as caught:
            reissue_school_code(platform(conn, archived=True), 999, 7, -10)
        self.assertEqual(caught.exception.status_code, 410)
        self.assertFalse(any(q.startswith(("UPDATE", "INSERT", "DELETE")) for q, _ in conn.cur.calls))

    def test_admin_preview_token_is_blocked_before_database_operation(self):
        path = Path(__file__).resolve().parents[1] / "samtm_platform.py"
        function = next(node for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == "maktab_shaxs_kirish_kodi")
        function.decorator_list = []
        class HTTPError(Exception):
            def __init__(self, status_code, detail):
                self.status_code, self.detail = status_code, detail
        namespace = {"MaktabShaxsKirishKodi": object, "_jwt_tekshir": lambda token: 999,
                     "jwt": SimpleNamespace(decode=lambda *a, **kw: {"admin_korish": 888, "yozish": True}),
                     "JWT_MAXFIY_KALIT": "unused", "HTTPException": HTTPError}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
        with self.assertRaises(HTTPError) as caught:
            namespace[function.name](SimpleNamespace(token="verified-preview-token", maktab_id=7, user_id=-10))
        self.assertEqual(caught.exception.status_code, 403)


class SchoolPersonSearchTests(unittest.TestCase):
    def test_actual_manager_search_is_bounded_scoped_and_returns_only_identity_fields(self):
        conn = Connection()
        result = search_school_people(platform(conn), 999, 7, "Namuna%_")
        self.assertEqual(set(result["natijalar"][0]), {"user_id", "full_name", "role"})
        query, params = next((q, p) for q, p in conn.cur.calls if q.startswith("SELECT u.user_id"))
        self.assertEqual(params, (7, 7, 7, "Namuna%_"))
        self.assertIn("u.maktab_id=%s", query)
        self.assertIn("child.maktab_id=%s", query)
        self.assertIn("sp.school_id=%s", query)
        self.assertIn("u.role IN ('oqituvchi','oquvchi','ota-ona')", query)
        self.assertIn("strpos(", query)
        self.assertTrue(query.endswith("LIMIT 30"))
        self.assertEqual(conn.commits, 0)
        self.assertTrue(conn.closed and conn.cur.closed)

    def test_unscoped_actor_cannot_read_people(self):
        conn = Connection()
        with self.assertRaises(MembershipError) as caught:
            search_school_people(platform(conn, manager=False), 777, 7, "Namuna")
        self.assertEqual(caught.exception.status_code, 403)
        self.assertEqual(conn.cur.calls, [])

    def test_empty_and_oversized_search_does_not_open_database(self):
        for name in ("", "A", "A" * 101):
            conn = Connection()
            with self.assertRaises(MembershipError) as caught:
                search_school_people(platform(conn), 999, 7, name)
            self.assertEqual(caught.exception.status_code, 422)
            self.assertEqual(conn.cur.calls, [])

    def test_registered_get_rejects_preview_with_bearer_header_before_search(self):
        path = Path(__file__).resolve().parents[1] / "samtm_platform.py"
        function = next(node for node in ast.parse(path.read_text()).body if isinstance(node, ast.FunctionDef) and node.name == "maktab_shaxs_qidir")
        function.decorator_list = []
        class HTTPError(Exception):
            def __init__(self, status_code, detail):
                self.status_code = status_code
        namespace = {"Optional": __import__("typing").Optional, "Header": lambda **kw: None,
                     "_jwt_header_yoki_query": lambda query, header: "verified" if query is None and header == "Bearer test" else self.fail("Bearer only required"),
                     "_jwt_tekshir": lambda token: 999,
                     "jwt": SimpleNamespace(decode=lambda *a, **kw: {"admin_korish": 888}),
                     "JWT_MAXFIY_KALIT": "unused", "HTTPException": HTTPError}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(path), "exec"), namespace)
        with self.assertRaises(HTTPError) as caught:
            namespace[function.name](7, "Namuna", "Bearer test")
        self.assertEqual(caught.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
