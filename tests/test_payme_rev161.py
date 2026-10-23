"""REV161: Payme Merchant API — avtorizatsiya, summa, yaratish → bajarish (kurs bir marta ochiladi), bekor, takror."""
import base64
import contextlib

from modules import payme_tolov as pm


class Cur:
    def __init__(self, db): self.db, self.rows = db, []
    def execute(self, sql, args=()):
        s = " ".join(sql.split()); D = self.db
        def one(x): self.rows = [dict(x)] if x else []
        if s.startswith("SELECT * FROM click_tolovlar WHERE merchant_trans_id"):
            one(next((b for b in D["b"].values() if b["merchant_trans_id"] == args[0]), None))
        elif s.startswith("SELECT * FROM click_tolovlar WHERE id"):
            one(D["b"][args[0]])
        elif s.startswith("SELECT course_id FROM click_tolovlar") or s.startswith("SELECT course_id, turi FROM click_tolovlar"):
            one({"course_id": D["b"][args[0]]["course_id"]})
        elif s.startswith("UPDATE click_tolovlar SET status='tayyor'"):
            if D["b"][args[0]]["status"] == "yaratildi": D["b"][args[0]]["status"] = "tayyor"
        elif s.startswith("UPDATE click_tolovlar SET status='yaratildi'"):
            if D["b"][args[0]]["status"] == "tayyor": D["b"][args[0]]["status"] = "yaratildi"
        elif s.startswith("UPDATE click_tolovlar SET status='tolandi'"):
            D["b"][args[1]].update(status="tolandi", order_id=args[0])
        elif s.startswith("SELECT * FROM payme_tranzaksiyalar WHERE payme_id"):
            one(next((t for t in D["t"].values() if t["payme_id"] == args[0]), None))
        elif s.startswith("SELECT 1 FROM payme_tranzaksiyalar WHERE buyurtma_id"):
            one({"x": 1} if any(t["buyurtma_id"] == args[0] and t["state"] == 1 for t in D["t"].values()) else None)
        elif s.startswith("INSERT INTO payme_tranzaksiyalar"):
            i = len(D["t"]) + 1
            D["t"][i] = {"id": i, "payme_id": args[0], "buyurtma_id": args[1], "amount_tiyin": args[2], "payme_time": args[3],
                         "create_time": args[4], "perform_time": 0, "cancel_time": 0, "state": 1, "reason": None}
            one(D["t"][i])
        elif s.startswith("UPDATE payme_tranzaksiyalar SET state=2"):
            D["t"][args[1]].update(state=2, perform_time=args[0])
        elif s.startswith("UPDATE payme_tranzaksiyalar SET state=-1,reason=%s"):
            D["t"][args[2]].update(state=-1, reason=args[0], cancel_time=args[1])
        else:
            raise AssertionError(s)
    def fetchone(self): return self.rows[0] if self.rows else None
    def fetchall(self): return self.rows


class Academy:
    def __init__(self, db): self.d = db
    @contextlib.contextmanager
    def db(self): yield Cur(self.d)


class Payments:
    def __init__(self): self.granted = []
    def _locked_course(self, cur, cid): return {"id": cid, "teacher_id": 1}
    def _grant(self, cur, course, user, amount, ref, owner, key, source):
        self.granted.append((user, amount, key, source)); return {"id": 88}


AUTH = "Basic " + base64.b64encode(b"Paycom:kalit").decode()


def make(monkeypatch):
    monkeypatch.setenv("PAYME_MERCHANT_ID", "m1"); monkeypatch.setenv("PAYME_SECRET_KEY", "kalit")
    db = {"b": {3: {"id": 3, "merchant_trans_id": "261022123456789", "course_id": 7, "user_id": 9, "amount_uzs": 150000, "status": "yaratildi"}}, "t": {}}
    svc = pm.PaymeService(Academy(db), Payments(), None); svc._ready = True
    return svc, db


def rpc(svc, method, **params):
    return svc.handle(AUTH, {"id": 1, "method": method, "params": params})


ACC = {"order_id": "261022123456789"}


def test_checkout_url_and_auth(monkeypatch):
    svc, _ = make(monkeypatch)
    url = pm.tolov_havolasi({"merchant_id": "m1"}, 150000, "261022123456789")
    assert base64.b64decode(url.rsplit("/", 1)[1]).decode() == "m=m1;ac.order_id=261022123456789;a=15000000"
    assert svc.handle("Basic " + base64.b64encode(b"Paycom:xato").decode(), {"id": 1, "method": "CheckTransaction"})["error"]["code"] == pm.E_AUTH


def test_full_flow_grants_once(monkeypatch):
    svc, db = make(monkeypatch)
    assert rpc(svc, "CheckPerformTransaction", amount=15000000, account=ACC)["result"] == {"allow": True}
    assert rpc(svc, "CheckPerformTransaction", amount=100, account=ACC)["error"]["code"] == pm.E_AMOUNT
    assert rpc(svc, "CheckPerformTransaction", amount=15000000, account={"order_id": "1"})["error"]["code"] == pm.E_ORDER
    r = rpc(svc, "CreateTransaction", id="px1", time=pm.ms(), amount=15000000, account=ACC)["result"]
    assert r["state"] == 1
    assert rpc(svc, "CreateTransaction", id="px1", time=pm.ms(), amount=15000000, account=ACC)["result"]["transaction"] == r["transaction"]
    assert rpc(svc, "CreateTransaction", id="px2", time=pm.ms(), amount=15000000, account=ACC)["error"]["code"] == pm.E_ORDER_BUSY
    assert rpc(svc, "PerformTransaction", id="px1")["result"]["state"] == 2
    assert rpc(svc, "PerformTransaction", id="px1")["result"]["state"] == 2      # takror — o'zgarmaydi
    assert svc.payments.granted == [(9, 150000, "payme:px1", "payme")]
    assert db["b"][3]["status"] == "tolandi"
    assert rpc(svc, "CancelTransaction", id="px1", reason=5)["error"]["code"] == pm.E_CANT_CANCEL
    assert rpc(svc, "CheckTransaction", id="px1")["result"]["state"] == 2
    assert rpc(svc, "CheckPerformTransaction", amount=15000000, account=ACC)["error"]["code"] == pm.E_ORDER_BUSY


def test_cancel_before_perform(monkeypatch):
    svc, db = make(monkeypatch)
    rpc(svc, "CreateTransaction", id="px9", time=pm.ms(), amount=15000000, account=ACC)
    r = rpc(svc, "CancelTransaction", id="px9", reason=3)["result"]
    assert r["state"] == -1 and db["b"][3]["status"] == "yaratildi"
    assert rpc(svc, "PerformTransaction", id="px9")["error"]["code"] == pm.E_CANT_PERFORM
    assert not svc.payments.granted
