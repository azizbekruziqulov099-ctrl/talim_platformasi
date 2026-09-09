"""Real chat handlers against controlled SQL boundaries; no live DB needed."""
import ast
import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HTTPException(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code


def load_handlers(filename, names, **overrides):
    tree = ast.parse((ROOT / filename).read_text())
    selected = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    assert len(selected) == len(names)
    for node in selected:
        node.decorator_list = []
    ns = {
        "HTTPException": HTTPException, "Optional": Optional, "UploadFile": object,
        "Form": lambda value=None: value, "File": lambda value=None: value,
        "Response": lambda **args: SimpleNamespace(**args),
        "_jwt_tekshir": lambda token: 101,
        "_chat_jadvallari": lambda cur: None,
        "_reaksiya_jadvali": lambda cur: None,
        "_kabutar_ruxsat": lambda *args: True,
        "_moderatsiya_jadvallari": lambda cur: None,
        "_matnda_royxat_sozi_bormi": lambda *args: False,
        "_SOKINISH_SOZLARI_BOSHLANGICH": [], "_XAVFLI_SOZLAR_BOSHLANGICH": [],
        **overrides,
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), filename, "exec"), ns)
    return ns


class ChatDB:
    def __init__(self, *, member=True, valid_message=True, metadata=None, content=b"photo", rows=()):
        self.member = member
        self.valid_message = valid_message
        self.metadata = metadata
        self.content = content
        self.rows = list(rows)
        self.calls = []
        self.closed = self.committed = False

    def cursor(self):
        return self

    def execute(self, sql, args=()):
        self.calls.append((sql, args))

    def fetchone(self):
        sql = self.calls[-1][0]
        if sql.strip().startswith("SELECT 1 FROM chat_azolari"):
            return {"member": 1} if self.member else None
        if "SELECT id FROM chat_xabarlari" in sql:
            return {"id": 40} if self.valid_message else None
        if "SELECT guruh_id, qabul_qiluvchi_user_id" in sql:
            return self.metadata
        if "SELECT x.fayl_malumot" in sql:
            return {"fayl_malumot": self.content, "fayl_content_turi": "image/png"} if self.content else None
        if sql.strip().startswith("INSERT INTO chat_xabarlari"):
            return {"id": 150, "yaratilgan_at": None}
        return None

    def fetchall(self):
        sql, args = self.calls[-1]
        if "chat_reaksiyalar" in sql:
            return []
        if "ORDER BY" in sql:
            result = self.rows
            if "id > %s" in sql or "x.id>%s" in sql:
                result = [r for r in result if r["id"] > args[-1]]
            if "id < %s" in sql or "x.id<%s" in sql:
                result = [r for r in result if r["id"] < args[-1]]
            result = sorted(result, key=lambda row: row["id"], reverse=" DESC LIMIT" in sql)
            return [dict(r) for r in result[:60 if "LIMIT 60" in sql else 50]]
        return []

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


class ChatBoundaryTests(unittest.TestCase):
    def platform(self, db, function, **overrides):
        return load_handlers("samtm_platform.py", ["_chat_suhbat_ruxsat", function], _db=lambda: db, **overrides)[function]

    def test_legacy_direct_send_rejects_unknown_recipient_before_upload_or_insert(self):
        class Upload:
            async def read(self):
                raise AssertionError("unauthorized upload must not be read")
        db = ChatDB()
        send = self.platform(db, "chat_xabar_yubor", _kabutar_ruxsat=lambda *args: False)
        with self.assertRaises(HTTPException) as error:
            asyncio.run(send(token="session", guruh_id=None, qabul_qiluvchi_user_id=202,
                             matn="hello", fayl_turi="audio", javob_xabar_id=None, fayl=Upload()))
        self.assertEqual(error.exception.status_code, 403)
        self.assertFalse(db.committed)
        self.assertFalse(any("INSERT" in sql for sql, _ in db.calls))

    def test_legacy_direct_send_keeps_permitted_contact_working(self):
        db = ChatDB()
        send = self.platform(db, "chat_xabar_yubor")
        result = asyncio.run(send(token="session", guruh_id=None, qabul_qiluvchi_user_id=202,
                                  matn="hello", fayl_turi=None, javob_xabar_id=None, fayl=None))
        self.assertEqual(result["id"], 150)
        self.assertTrue(db.committed)

    def test_dual_target_cannot_create_cross_context_group_direct_message(self):
        db = ChatDB()
        send = self.platform(db, "chat_xabar_yubor")
        with self.assertRaises(HTTPException) as error:
            asyncio.run(send(token="session", guruh_id=5, qabul_qiluvchi_user_id=202,
                             matn="hello", fayl_turi=None, javob_xabar_id=None, fayl=None))
        self.assertEqual(error.exception.status_code, 400)

    def test_read_marker_rejects_nonmember_and_never_inserts(self):
        db = ChatDB(member=False)
        mark = self.platform(db, "chat_korildi_belgila")
        with self.assertRaises(HTTPException) as error:
            mark("session", 40, guruh_id=5)
        self.assertEqual(error.exception.status_code, 403)
        self.assertFalse(any("INSERT" in sql for sql, _ in db.calls))

    def test_future_or_other_conversation_marker_cannot_hide_new_messages(self):
        db = ChatDB(valid_message=False)
        mark = self.platform(db, "chat_korildi_belgila")
        with self.assertRaises(HTTPException) as error:
            mark("session", 999999999, boshqa_user_id=202)
        self.assertEqual(error.exception.status_code, 400)
        self.assertFalse(db.committed)

    def test_read_marker_uses_membership_and_exact_conversation_then_monotonic_update(self):
        db = ChatDB()
        mark = self.platform(db, "chat_korildi_belgila")
        self.assertEqual(mark("session", 40, guruh_id=5), {"holat": "belgilandi"})
        self.assertEqual(db.calls[1][1], (40, 5))
        self.assertIn("GREATEST", db.calls[-1][0])
        self.assertTrue(db.committed)

    def test_group_incremental_paging_retains_every_message_in_a_burst(self):
        db = ChatDB(rows=[{"id": i, "yuboruvchi_user_id": 202, "ochirilgan": False} for i in range(1, 131)])
        get = self.platform(db, "chat_xabarlarini_olish")
        first = get("session", guruh_id=5, keyingidan=50)
        second = get("session", guruh_id=5, keyingidan=first["keyingi_id"])
        self.assertEqual([r["id"] for r in first["xabarlar"] + second["xabarlar"]], list(range(51, 131)))
        self.assertTrue(first["yana_bormi"])
        self.assertFalse(second["yana_bormi"])

    def test_personal_incremental_paging_retains_every_message_in_a_burst(self):
        db = ChatDB(rows=[{"id": i, "yuboruvchi_user_id": 202, "yaratilgan_at": None} for i in range(1, 151)])
        get = load_handlers("samtm_school.py", ["v2257_kabutar_xabarlar"], _db=lambda: db)["v2257_kabutar_xabarlar"]
        first = get("session", 202, keyingidan=50)
        second = get("session", 202, keyingidan=first["keyingi_id"])
        self.assertEqual([r["id"] for r in first["xabarlar"] + second["xabarlar"]], list(range(51, 151)))

    def test_initial_page_remains_newest_messages_in_chronological_order(self):
        db = ChatDB(rows=[{"id": i, "yuboruvchi_user_id": 202, "ochirilgan": False} for i in range(1, 131)])
        get = self.platform(db, "chat_xabarlarini_olish")
        self.assertEqual([r["id"] for r in get("session", guruh_id=5)["xabarlar"]], list(range(81, 131)))

    def test_deleted_message_cannot_be_downloaded(self):
        db = ChatDB(metadata=None)
        get = self.platform(db, "chat_fayl_korish")
        with self.assertRaises(HTTPException) as error:
            get(40, "session")
        self.assertEqual(error.exception.status_code, 404)
        self.assertIn("COALESCE(ochirilgan,FALSE)=FALSE", db.calls[0][0])
        self.assertNotIn("fayl_malumot", db.calls[0][0])

    def test_outsider_cannot_trigger_loading_the_media_bytes(self):
        db = ChatDB(metadata={"guruh_id": None, "yuboruvchi_user_id": 303, "qabul_qiluvchi_user_id": 404})
        get = self.platform(db, "chat_fayl_korish")
        with self.assertRaises(HTTPException) as error:
            get(40, "session")
        self.assertEqual(error.exception.status_code, 403)
        self.assertEqual(len(db.calls), 1)

    def test_permitted_media_rechecks_deleted_membership_and_disables_cache(self):
        db = ChatDB(metadata={"guruh_id": None, "yuboruvchi_user_id": 101, "qabul_qiluvchi_user_id": 202})
        get = self.platform(db, "chat_fayl_korish")
        response = get(40, "session")
        self.assertEqual(response.content, b"photo")
        self.assertIn("EXISTS(SELECT 1 FROM chat_azolari", db.calls[1][0])
        self.assertIn("COALESCE(x.ochirilgan,FALSE)=FALSE", db.calls[1][0])
        self.assertEqual(response.headers["Cache-Control"], "private, no-store")


if __name__ == "__main__":
    unittest.main()
