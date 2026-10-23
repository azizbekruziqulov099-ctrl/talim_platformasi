"""REV161: Payme Merchant API — pulli kursga AVTOMATIK to'lov (Click bilan bir xil buyurtma kodi).

Oqim:
  1. O'quvchi «Payme orqali to'lash» → buyurtma kodi (click_tolovlar.merchant_trans_id, faqat raqam) yaratiladi
     va Payme checkout manzili qaytariladi (checkout.paycom.uz/<base64>). Mijoz Payme ilovasida «order_id» maydoniga
     shu kodni yozib ham to'lashi mumkin.
  2. Payme serverimizga JSON-RPC so'rov yuboradi (POST /api/payme, Basic «Paycom:<KEY>»):
       CheckPerformTransaction → CreateTransaction → PerformTransaction (pul yechildi → kurs AVTOMATIK ochiladi)
       CancelTransaction, CheckTransaction, GetStatement.
Sozlash (faqat Railway → backend → Variables): PAYME_MERCHANT_ID, PAYME_SECRET_KEY
  (test kassasi uchun PAYME_TEST=1 — checkout.test.paycom.uz).
Summa Payme'da tiyinda (1 so'm = 100 tiyin).
"""
import base64
import hmac
import os
import time

from fastapi import APIRouter, Request

TIMEOUT_MS = 12 * 60 * 60 * 1000   # 12 soatdan eski yaratilgan tranzaksiya bekor qilinadi

E_AUTH, E_METHOD, E_PARSE, E_RPC = -32504, -32601, -32700, -32600
E_AMOUNT, E_TX_NOT_FOUND, E_CANT_CANCEL, E_CANT_PERFORM = -31001, -31003, -31007, -31008
E_ORDER = -31050          # buyurtma topilmadi
E_ORDER_BUSY = -31051     # buyurtma uchun boshqa tranzaksiya ochiq yoki allaqachon to'langan

MSG = {
    E_AUTH: ("Недостаточно привилегий", "Ruxsat yo‘q", "Insufficient privileges"),
    E_METHOD: ("Метод не найден", "Usul topilmadi", "Method not found"),
    E_PARSE: ("Ошибка разбора JSON", "JSON xato", "Parse error"),
    E_RPC: ("Неверный запрос", "So‘rov noto‘g‘ri", "Invalid request"),
    E_AMOUNT: ("Неверная сумма", "Summa noto‘g‘ri", "Incorrect amount"),
    E_TX_NOT_FOUND: ("Транзакция не найдена", "Tranzaksiya topilmadi", "Transaction not found"),
    E_CANT_CANCEL: ("Услуга оказана, отмена невозможна", "Xizmat ko‘rsatilgan, bekor qilib bo‘lmaydi", "Cannot cancel"),
    E_CANT_PERFORM: ("Невозможно выполнить операцию", "Amalni bajarib bo‘lmaydi", "Cannot perform"),
    E_ORDER: ("Заказ не найден", "Buyurtma topilmadi", "Order not found"),
    E_ORDER_BUSY: ("Заказ уже оплачивается или оплачен", "Buyurtma to‘lanmoqda yoki to‘langan", "Order busy or paid"),
}


class PaymeXato(Exception):
    def __init__(self, code, data=None):
        super().__init__(code)
        self.code, self.data = code, data


def sozlama():
    mid, key = os.getenv("PAYME_MERCHANT_ID", "").strip(), os.getenv("PAYME_SECRET_KEY", "").strip()
    test = os.getenv("PAYME_TEST", "") == "1"
    return {"merchant_id": mid, "key": key, "test": test, "yoqilgan": bool(mid and key)}


def tolov_havolasi(cfg, amount_uzs, kod, return_url=""):
    params = f"m={cfg['merchant_id']};ac.order_id={kod};a={int(amount_uzs) * 100}"
    if return_url:
        params += f";c={return_url}"
    host = "https://checkout.test.paycom.uz/" if cfg.get("test") else "https://checkout.paycom.uz/"
    return host + base64.b64encode(params.encode("utf-8")).decode("ascii")


def auth_togrimi(header, key):
    if not key or not header or not header.lower().startswith("basic "):
        return False
    try:
        raw = base64.b64decode(header[6:].strip()).decode("utf-8")
    except Exception:
        return False
    login, _, parol = raw.partition(":")
    return login == "Paycom" and hmac.compare_digest(parol, key)


def xato_javob(req_id, code, data=None):
    ru, uz, en = MSG.get(code, ("Ошибка", "Xato", "Error"))
    err = {"code": code, "message": {"ru": ru, "uz": uz, "en": en}}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


def ms():
    return int(time.time() * 1000)


class PaymeService:
    def __init__(self, academy, payments, click):
        self.academy, self.payments, self.click = academy, payments, click
        self._ready = False

    def migrate(self):
        if self._ready:
            return
        self.click.migrate()   # click_tolovlar (umumiy buyurtmalar jadvali) va academy_orders 'click' manbasi
        with self.academy.db() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(47091205)")
            cur.execute("""CREATE TABLE IF NOT EXISTS payme_tranzaksiyalar (
                id BIGSERIAL PRIMARY KEY,
                payme_id TEXT NOT NULL UNIQUE,
                buyurtma_id BIGINT NOT NULL REFERENCES click_tolovlar(id),
                amount_tiyin BIGINT NOT NULL,
                state SMALLINT NOT NULL DEFAULT 1,
                reason SMALLINT,
                payme_time BIGINT NOT NULL,
                create_time BIGINT NOT NULL,
                perform_time BIGINT NOT NULL DEFAULT 0,
                cancel_time BIGINT NOT NULL DEFAULT 0
            )""")
            cur.execute("CREATE INDEX IF NOT EXISTS payme_tx_buyurtma_idx ON payme_tranzaksiyalar(buyurtma_id,state)")
            cur.execute("CREATE INDEX IF NOT EXISTS payme_tx_time_idx ON payme_tranzaksiyalar(payme_time)")
            cur.execute("ALTER TABLE academy_orders DROP CONSTRAINT IF EXISTS academy_orders_source_check")
            cur.execute("""ALTER TABLE academy_orders ADD CONSTRAINT academy_orders_source_check
                CHECK(source IN ('manual','request','click','payme'))""")
        self._ready = True

    # — yordamchilar —
    @staticmethod
    def _kod(params):
        acc = params.get("account") or {}
        return str(acc.get("order_id") or "").strip()

    def _buyurtma(self, cur, kod, lock=False):
        if not kod:
            raise PaymeXato(E_ORDER, "order_id")
        cur.execute(f"SELECT * FROM click_tolovlar WHERE merchant_trans_id=%s {'FOR UPDATE' if lock else ''}", (kod,))
        b = cur.fetchone()
        if not b:
            raise PaymeXato(E_ORDER, "order_id")
        return b

    @staticmethod
    def _tx_view(t):
        return {"create_time": int(t["create_time"]), "perform_time": int(t["perform_time"]),
                "cancel_time": int(t["cancel_time"]), "transaction": str(t["id"]), "state": int(t["state"]),
                "reason": t["reason"]}

    def _tx(self, cur, payme_id, lock=False):
        cur.execute(f"SELECT * FROM payme_tranzaksiyalar WHERE payme_id=%s {'FOR UPDATE' if lock else ''}", (str(payme_id),))
        return cur.fetchone()

    # — usullar —
    def check_perform(self, cur, p):
        b = self._buyurtma(cur, self._kod(p))
        if b["status"] in ("tolandi", "bekor"):
            raise PaymeXato(E_ORDER_BUSY, "order_id")
        if int(p.get("amount") or 0) != int(b["amount_uzs"]) * 100:
            raise PaymeXato(E_AMOUNT)
        return {"allow": True}

    def create(self, cur, p):
        t = self._tx(cur, p.get("id"), lock=True)
        if t:
            if t["state"] != 1:
                raise PaymeXato(E_CANT_PERFORM)
            if ms() - int(t["payme_time"]) > TIMEOUT_MS:
                cur.execute("UPDATE payme_tranzaksiyalar SET state=-1,reason=4,cancel_time=%s WHERE id=%s", (ms(), t["id"]))
                raise PaymeXato(E_CANT_PERFORM)
            return {"create_time": int(t["create_time"]), "transaction": str(t["id"]), "state": 1}
        b = self._buyurtma(cur, self._kod(p), lock=True)
        if b["status"] in ("tolandi", "bekor"):
            raise PaymeXato(E_ORDER_BUSY, "order_id")
        if int(p.get("amount") or 0) != int(b["amount_uzs"]) * 100:
            raise PaymeXato(E_AMOUNT)
        cur.execute("SELECT 1 FROM payme_tranzaksiyalar WHERE buyurtma_id=%s AND state=1", (b["id"],))
        if cur.fetchone():
            raise PaymeXato(E_ORDER_BUSY, "order_id")   # shu buyurtmaga boshqa Payme tranzaksiyasi ochiq
        now = ms()
        cur.execute("""INSERT INTO payme_tranzaksiyalar(payme_id,buyurtma_id,amount_tiyin,payme_time,create_time)
            VALUES(%s,%s,%s,%s,%s) RETURNING *""", (str(p.get("id")), b["id"], int(p.get("amount")), int(p.get("time") or now), now))
        t = cur.fetchone()
        cur.execute("UPDATE click_tolovlar SET status='tayyor',updated_at=NOW() WHERE id=%s AND status='yaratildi'", (b["id"],))
        return {"create_time": int(t["create_time"]), "transaction": str(t["id"]), "state": 1}

    def perform(self, cur, p):
        t = self._tx(cur, p.get("id"))
        if not t:
            raise PaymeXato(E_TX_NOT_FOUND)
        # qulflash tartibi: kurs → buyurtma → tranzaksiya
        cur.execute("SELECT course_id, turi FROM click_tolovlar WHERE id=%s", (t["buyurtma_id"],))
        seed = cur.fetchone()
        obuna = seed.get("turi") == "obuna"   # REV162: bog'cha obunasi
        course = None if obuna else self.payments._locked_course(cur, seed["course_id"])
        cur.execute("SELECT * FROM click_tolovlar WHERE id=%s FOR UPDATE", (t["buyurtma_id"],))
        b = cur.fetchone()
        t = self._tx(cur, p.get("id"), lock=True)
        if t["state"] == 2:
            return {"transaction": str(t["id"]), "perform_time": int(t["perform_time"]), "state": 2}
        if t["state"] != 1:
            raise PaymeXato(E_CANT_PERFORM)
        if ms() - int(t["payme_time"]) > TIMEOUT_MS:
            cur.execute("UPDATE payme_tranzaksiyalar SET state=-1,reason=4,cancel_time=%s WHERE id=%s", (ms(), t["id"]))
            raise PaymeXato(E_CANT_PERFORM)
        if b["status"] == "tolandi":
            raise PaymeXato(E_CANT_PERFORM)   # boshqa tizim orqali to'lab bo'lingan
        if obuna:
            self.click.obuna_ber(cur, b, "payme", f"payme:{t['payme_id']}")
            order = {"id": None}
        else:
            order = self.payments._grant(cur, course, b["user_id"], int(b["amount_uzs"]), f"PAYME-{t['payme_id']}",
                                         int(course["teacher_id"]), f"payme:{t['payme_id']}", "payme")
        now = ms()
        cur.execute("UPDATE payme_tranzaksiyalar SET state=2,perform_time=%s WHERE id=%s", (now, t["id"]))
        cur.execute("UPDATE click_tolovlar SET status='tolandi',order_id=%s,updated_at=NOW() WHERE id=%s", (order["id"], b["id"]))
        return {"transaction": str(t["id"]), "perform_time": now, "state": 2}

    def cancel(self, cur, p):
        t = self._tx(cur, p.get("id"), lock=True)
        if not t:
            raise PaymeXato(E_TX_NOT_FOUND)
        if t["state"] == 1:
            now = ms()
            cur.execute("UPDATE payme_tranzaksiyalar SET state=-1,reason=%s,cancel_time=%s WHERE id=%s",
                        (int(p.get("reason") or 0) or None, now, t["id"]))
            cur.execute("UPDATE click_tolovlar SET status='yaratildi',updated_at=NOW() WHERE id=%s AND status='tayyor'", (t["buyurtma_id"],))
            return {"transaction": str(t["id"]), "cancel_time": now, "state": -1}
        if t["state"] == 2:
            raise PaymeXato(E_CANT_CANCEL)   # kurs ochib bo'lingan — pulni qaytarish faqat qo'lda
        return {"transaction": str(t["id"]), "cancel_time": int(t["cancel_time"]), "state": int(t["state"])}

    def check(self, cur, p):
        t = self._tx(cur, p.get("id"))
        if not t:
            raise PaymeXato(E_TX_NOT_FOUND)
        return self._tx_view(t)

    def statement(self, cur, p):
        cur.execute("""SELECT t.*,b.merchant_trans_id FROM payme_tranzaksiyalar t JOIN click_tolovlar b ON b.id=t.buyurtma_id
            WHERE t.payme_time BETWEEN %s AND %s ORDER BY t.payme_time""", (int(p.get("from") or 0), int(p.get("to") or 0)))
        out = []
        for t in cur.fetchall():
            v = self._tx_view(t)
            v.update(id=t["payme_id"], time=int(t["payme_time"]), amount=int(t["amount_tiyin"]),
                     account={"order_id": t["merchant_trans_id"]})
            out.append(v)
        return {"transactions": out}

    USULLAR = {"CheckPerformTransaction": "check_perform", "CreateTransaction": "create", "PerformTransaction": "perform",
               "CancelTransaction": "cancel", "CheckTransaction": "check", "GetStatement": "statement"}

    def handle(self, auth_header, body):
        req_id = body.get("id") if isinstance(body, dict) else None
        cfg = sozlama()
        if not cfg["yoqilgan"] or not auth_togrimi(auth_header, cfg["key"]):
            return xato_javob(req_id, E_AUTH)
        if not isinstance(body, dict) or not isinstance(body.get("params", {}), dict):
            return xato_javob(req_id, E_RPC)
        usul = self.USULLAR.get(body.get("method"))
        if not usul:
            return xato_javob(req_id, E_METHOD)
        self.migrate()
        try:
            with self.academy.db() as cur:
                return {"jsonrpc": "2.0", "id": req_id, "result": getattr(self, usul)(cur, body.get("params") or {})}
        except PaymeXato as e:
            return xato_javob(req_id, e.code, e.data)


def register_payme(app, academy, payments, click):
    svc = PaymeService(academy, payments, click)
    router = APIRouter(tags=["Payme to‘lov"])

    @router.post("/api/payme")
    async def payme(request: Request):
        from starlette.concurrency import run_in_threadpool
        try:
            body = await request.json()
        except Exception:
            return xato_javob(None, E_PARSE)
        return await run_in_threadpool(svc.handle, request.headers.get("authorization", ""), body)

    app.include_router(router)
    return svc
