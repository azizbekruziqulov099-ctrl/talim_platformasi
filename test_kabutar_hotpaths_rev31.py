"""Exercise actual Kabutar helpers with deterministic DB failures and rows.

These are boundary tests, not a PostgreSQL concurrency or production load test.
"""
import ast
import importlib.util
import logging
from pathlib import Path
from types import SimpleNamespace
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HTTPException(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code


class IntegrityError(Exception):
    def __init__(self, pgcode="23505"):
        self.pgcode = pgcode


def helpers(*names, **values):
    tree = ast.parse((ROOT / "samtm_school.py").read_text(encoding="utf-8"))
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(selected) == len(names)
    for node in selected:
        node.decorator_list = []
    namespace = {"HTTPException": HTTPException, "psycopg2": SimpleNamespace(IntegrityError=IntegrityError), **values}
    exec(compile(ast.Module(body=selected, type_ignores=[]), "samtm_school.py", "exec"), namespace)
    return namespace


class IdCursor:
    def __init__(self, row, outcomes=()):
        self.row = row
        self.outcomes = iter(outcomes)
        self.calls = []
        self.rowcount = 0

    def execute(self, sql, args=()):
        self.calls.append((sql, args))
        if sql.startswith("UPDATE"):
            outcome = next(self.outcomes, 1)
            if isinstance(outcome, Exception):
                raise outcome
            self.rowcount = outcome

    def fetchone(self):
        return self.row


class SchemaConnection:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self

    def execute(self, sql, params=()):
        self.calls.append(sql)

    def fetchone(self):
        return {"table_name": "chat_xabarlari"}

    def commit(self):
        if self.fail:
            raise RuntimeError("simulated commit failure")
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class KabutarHotpathsTests(unittest.TestCase):
    def allocator(self, cursor):
        ns = helpers("_kabutar_id_ber", _kabutar_jadval=lambda cur: None)
        return ns["_kabutar_id_ber"](cursor, 101)

    def test_existing_six_digit_id_stays_unchanged_and_row_is_locked(self):
        cur = IdCursor({"kabutar_id": "KB-123456"})
        self.assertEqual(self.allocator(cur), "KB-123456")
        self.assertEqual(len(cur.calls), 1)
        self.assertIn("FOR UPDATE", cur.calls[0][0])

    def test_missing_account_does_not_receive_phantom_id(self):
        cur = IdCursor(None)
        with self.assertRaises(HTTPException) as caught:
            self.allocator(cur)
        self.assertEqual(caught.exception.status_code, 404)

    def test_fresh_id_is_eight_digits_without_global_count(self):
        cur = IdCursor({"kabutar_id": None})
        self.assertRegex(self.allocator(cur), r"^KB-[1-9][0-9]{7}$")
        self.assertFalse(any("COUNT(" in sql for sql, _ in cur.calls))

    def test_simultaneous_candidate_collision_does_not_abort_transaction(self):
        cur = IdCursor({"kabutar_id": None}, [IntegrityError(), 1])
        self.assertRegex(self.allocator(cur), r"^KB-[1-9][0-9]{7}$")
        self.assertTrue(any(sql.startswith("ROLLBACK TO SAVEPOINT") for sql, _ in cur.calls))
        self.assertEqual(sum(sql.startswith("UPDATE") for sql, _ in cur.calls), 2)

    def test_saturated_eight_digit_candidates_widen_to_nine(self):
        cur = IdCursor({"kabutar_id": None}, [0] * 16 + [1])
        self.assertRegex(self.allocator(cur), r"^KB-[1-9][0-9]{8}$")

    def test_non_unique_constraint_errors_are_not_silenced(self):
        cur = IdCursor({"kabutar_id": None}, [IntegrityError("23503")])
        with self.assertRaises(IntegrityError):
            self.allocator(cur)

    def test_failed_schema_commit_is_not_cached_and_retries(self):
        first, second = SchemaConnection(fail=True), SchemaConnection()
        connections = iter([first, second])
        ns = helpers("_kabutar_schema_startup", "_kabutar_jadval", _db=lambda: next(connections),
                     _KABUTAR_SCHEMA_READY=False, _KABUTAR_SCHEMA_LOCK=threading.Lock())
        with self.assertRaises(RuntimeError):
            ns["_kabutar_schema_startup"]()
        self.assertFalse(ns["_KABUTAR_SCHEMA_READY"])
        self.assertTrue(first.rolled_back and first.closed)
        ns["_kabutar_schema_startup"]()
        self.assertTrue(second.committed and ns["_KABUTAR_SCHEMA_READY"])
        # Exhausted iterator would fail if hot-path checks touched the DB.
        for _ in range(10):
            ns["_kabutar_jadval"](None)

    def test_existing_chat_permission_does_not_build_institution_directory(self):
        def forbidden(*args):
            raise AssertionError("must not load directory for existing chat")
        ns = helpers("_kabutar_ruxsat", _kabutar_universal_aloqalar=forbidden, _kabutar_aloqalar=forbidden)
        self.assertTrue(ns["_kabutar_ruxsat"](IdCursor({"exists": 1}), 101, 5, 202))
        self.assertFalse(ns["_kabutar_ruxsat"](IdCursor({"exists": 1}), 101, 5, 101))

    def test_unknown_chat_still_requires_an_allowed_institution_contact(self):
        ns = helpers("_kabutar_ruxsat", _kabutar_universal_aloqalar=lambda cur, uid: [])
        self.assertFalse(ns["_kabutar_ruxsat"](IdCursor(None), 101, None, 202))

    def test_sixty_recent_chat_previews_use_two_queries_and_no_peer_card_queries(self):
        class DirectoryDB(SchemaConnection):
            def fetchall(self):
                if "WITH recent AS" in self.calls[-1]:
                    return [{"uid": i, "oxirgi_id": i, "oxirgi": None,
                             "full_name": f"User {i}", "role": "oquvchi", "lavozim": None,
                             "kabutar_id": f"KB-{10000000 + i}", "matn": "Salom",
                             "fayl_turi": None, "yuboruvchi_user_id": i} for i in range(201, 261)]
                return []
        conn = DirectoryDB()
        cards = []
        def own_card(cur, uid):
            cards.append(uid)
            return {"user_id": uid}
        ns = helpers("v2258_kabutar_aloqalar_umumiy", _jwt_tekshir=lambda token: 101,
                     _db=lambda: conn, _chat_jadvallari=lambda cur: None,
                     _kabutar_id_ber=lambda cur, uid: "KB-10000101",
                     _kabutar_shaxs=own_card, _kabutar_universal_aloqalar=lambda cur, uid: [],
                     _KABUTAR_LAVOZIM_NOMI={})
        result = ns["v2258_kabutar_aloqalar_umumiy"]("session")
        self.assertEqual(len(result["suhbatlar"]), 60)
        self.assertEqual(len(conn.calls), 2)
        self.assertEqual(cards, [101])
        self.assertEqual(result["suhbatlar"][0]["izoh"], "O'quvchi")
        self.assertTrue(result["suhbatlar"][0]["tashqi"])

    def test_uvicorn_access_logging_removes_token_query(self):
        spec = importlib.util.spec_from_file_location("release31_logging_test", ROOT / "gunicorn_conf.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        record = logging.LogRecord("uvicorn.access", logging.INFO, "", 0,
                                   '%s - "%s %s HTTP/%s" %d',
                                   ("127.0.0.1", "GET", "/auth/men?token=SECRET_TEST_VALUE&email=private", "1.1", 200), None)
        self.assertTrue(config._RedactASGIQuery().filter(record))
        self.assertNotIn("SECRET_TEST_VALUE", record.getMessage())
        self.assertNotIn("email", record.getMessage())
        self.assertIn('GET /auth/men HTTP/1.1', record.getMessage())


if __name__ == "__main__":
    unittest.main()
