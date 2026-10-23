"""REV160: Click SHOP-API — imzo, summa, takror to'lov va bekor qilish (soxta baza bilan)."""
import contextlib
import hashlib

from modules import click_tolov as ct

KEY = "maxfiy"


class Cur:
    def __init__(self, db): self.db, self.row = db, None
    def execute(self, sql, args=()):
        s = " ".join(sql.split())
        if s.startswith("SELECT * FROM click_tolovlar WHERE merchant_trans_id"):
            self.row = next((dict(t) for t in self.db.values() if t["merchant_trans_id"] == args[0]), None)
        elif s.startswith("SELECT * FROM click_tolovlar WHERE id"):
            self.row = dict(self.db[args[0]])
        elif s.startswith("UPDATE click_tolovlar SET status='tayyor'"):
            self.db[args[2]].update(status="tayyor"); self.row = None
        elif s.startswith("UPDATE click_tolovlar SET status='bekor'"):
            self.db[args[1]].update(status="bekor"); self.row = None
        elif s.startswith("UPDATE click_tolovlar SET status='tolandi'"):
            self.db[args[1]].update(status="tolandi", order_id=args[0]); self.row = None
        else:
            raise AssertionError(s)
    def fetchone(self): return self.row


class Academy:
    def __init__(self, db): self.db_ = db
    @contextlib.contextmanager
    def db(self): yield Cur(self.db_)


class Payments:
    def __init__(self): self.granted = []
    def migrate(self): pass
    def _locked_course(self, cur, cid): return {"id": cid, "teacher_id": 1, "price_uzs": 150000, "status": "published"}
    def _grant(self, cur, course, user, amount, ref, owner, key, source):
        self.granted.append((user, amount, ref, key, source)); return {"id": 77}


def signed(p, action):
    p = dict(p, action=str(action), sign_time="2026-10-22 05:00:00")
    p["sign_string"] = ct.imzo(p, KEY, action)
    return p


def setup(monkeypatch):
    monkeypatch.setenv("CLICK_SERVICE_ID", "11"); monkeypatch.setenv("CLICK_MERCHANT_ID", "22"); monkeypatch.setenv("CLICK_SECRET_KEY", KEY)
    db = {5: {"id": 5, "merchant_trans_id": "K7U9Tab", "course_id": 7, "user_id": 9, "amount_uzs": 150000, "status": "yaratildi", "order_id": None}}
    svc = ct.ClickService(Academy(db), Payments()); svc._ready = True
    return svc, db


BASE = {"click_trans_id": "1001", "service_id": "11", "click_paydoc_id": "555", "merchant_trans_id": "K7U9Tab", "amount": "150000.00", "error": "0"}


def test_sign_formula_matches_click_docs():
    p = signed(BASE, 0)
    raw = "1001" + "11" + KEY + "K7U9Tab" + "150000.00" + "0" + "2026-10-22 05:00:00"
    assert p["sign_string"] == hashlib.md5(raw.encode()).hexdigest()
    assert "transaction_param=K7U9Tab" in ct.tolov_havolasi({"service_id": "11", "merchant_id": "22"}, 150000, "K7U9Tab")


def test_full_payment_opens_course_once(monkeypatch):
    svc, db = setup(monkeypatch)
    r = svc.prepare(signed(BASE, 0))
    assert r["error"] == 0 and r["merchant_prepare_id"] == 5
    r = svc.complete(signed(dict(BASE, merchant_prepare_id="5"), 1))
    assert r["error"] == 0 and r["merchant_confirm_id"] == 77 and db[5]["status"] == "tolandi"
    r = svc.complete(signed(dict(BASE, merchant_prepare_id="5"), 1))   # Click qayta yuborsa
    assert r["error"] == ct.ALREADY_PAID
    assert len(svc.payments.granted) == 1 and svc.payments.granted[0][4] == "click"


def test_bad_sign_amount_and_cancel(monkeypatch):
    svc, db = setup(monkeypatch)
    bad = signed(BASE, 0); bad["sign_string"] = "0" * 32
    assert svc.prepare(bad)["error"] == ct.SIGN_FAILED
    assert svc.prepare(signed(dict(BASE, amount="1000.00"), 0))["error"] == ct.BAD_AMOUNT
    assert svc.prepare(signed(dict(BASE, merchant_trans_id="yoq"), 0))["error"] == ct.NO_ORDER
    svc.prepare(signed(BASE, 0))
    r = svc.complete(signed(dict(BASE, merchant_prepare_id="5", error="-5017"), 1))
    assert r["error"] == ct.CANCELLED and db[5]["status"] == "bekor" and not svc.payments.granted


def test_disabled_without_keys(monkeypatch):
    for k in ("CLICK_SERVICE_ID", "CLICK_MERCHANT_ID", "CLICK_SECRET_KEY"):
        monkeypatch.delenv(k, raising=False)
    assert ct.sozlama()["yoqilgan"] is False
    assert ct.ClickService(None, None).prepare(BASE)["error"] == ct.BAD_REQUEST
