"""Manual course payment verification, with an immutable 30-day grant ledger.

This module never charges a card and does not connect to a payment provider.
A student's request is only a claim: course access changes after the actual
course owner explicitly confirms checking the payment outside this system.
"""
from datetime import datetime, timedelta
import re
from threading import Lock

from fastapi import APIRouter, Body, Header, HTTPException, Query


PERIOD_DAYS = 30
MAX_PRICE_UZS = 100_000_000
MAX_PAGE = 50
REQUEST_DAYS = 7
MANUAL_NOTICE = (
    "To‘lov bu sahifada yechilmaydi. To‘lovni ustoz bilan kelishib amalga oshiring; "
    "ustoz tushgan pulni tekshirib tasdiqlagach, kurs 30 kunga ochiladi."
)


def _integer(value, label, minimum=1, maximum=9_223_372_036_854_775_807):
    if type(value) is not int or not minimum <= value <= maximum:
        raise HTTPException(422, f"{label} noto‘g‘ri")
    return value


def _user_id(value):
    # Imported school accounts also use negative IDs; never coerce them to abs().
    _integer(value, "Foydalanuvchi ID raqami", -9_223_372_036_854_775_808)
    if value == 0:
        raise HTTPException(422, "Foydalanuvchi ID raqami noto‘g‘ri")
    return value


def _key(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{8,96}", value):
        raise HTTPException(422, "So‘rov kaliti noto‘g‘ri. Sahifani yangilab qayta yuboring.")
    return value


def _text(value, label, maximum, required=False):
    if not isinstance(value, str):
        raise HTTPException(422, f"{label} matn bo‘lishi kerak")
    value = value.strip()
    if len(value) > maximum or (required and not value):
        raise HTTPException(422, f"{label}: 1–{maximum} belgidan foydalaning")
    # Receipt IDs are accepted, but the form is not a place to store card data.
    if re.search(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)", value):
        raise HTTPException(422, "Karta raqamini yozmang. Qisqa chek raqami yoki to‘lov izohini kiriting.")
    if any(ord(ch) < 32 and ch not in "\n\r\t" for ch in value):
        raise HTTPException(422, f"{label} ichida noto‘g‘ri belgi bor")
    return value


def _confirmation(body):
    if not isinstance(body, dict) or body.get("confirmation") is not True:
        raise HTTPException(422, "Pul haqiqatan tushganini tekshirganingizni tasdiqlang")


def _iso(value):
    return value.isoformat() if isinstance(value, datetime) else value


def _request(row):
    fields = ("id", "course_id", "user_id", "user_name", "amount_uzs", "reference", "note",
              "status", "decision_note", "confirmed_by", "order_id", "created_at", "decided_at", "expires_at")
    result = {key: _iso(row.get(key)) for key in fields if key in row}
    result["period_days"] = PERIOD_DAYS
    return result


def _order(row):
    fields = ("id", "course_id", "user_id", "user_name", "amount_uzs", "reference", "confirmed_by",
              "source", "request_id", "status", "access_from", "access_until", "created_at")
    result = {key: _iso(row.get(key)) for key in fields if key in row}
    result["id"] = str(result["id"])
    result["period_days"] = PERIOD_DAYS
    return result


def grant_period(current, now):
    """A paid period starts after any unexpired period, otherwise immediately."""
    start = max(current, now) if current is not None else now
    return start, start + timedelta(days=PERIOD_DAYS)


class ManualPaymentService:
    payments_configured = False
    payment_mode = "manual"

    def __init__(self, service):
        self.service = service
        self._ready = False
        self._lock = Lock()

    def migrate(self):
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            with self.service.db() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(47091203)")
                cur.execute("""CREATE TABLE IF NOT EXISTS academy_payment_requests (
                    id BIGSERIAL PRIMARY KEY,
                    course_id BIGINT NOT NULL REFERENCES academy_courses(id),
                    user_id BIGINT NOT NULL REFERENCES users(user_id),
                    amount_uzs BIGINT NOT NULL CHECK(amount_uzs > 0 AND amount_uzs <= 100000000),
                    reference TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    request_key TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK(status IN ('pending','confirmed','rejected','expired')),
                    decision_note TEXT NOT NULL DEFAULT '',
                    confirmed_by BIGINT REFERENCES users(user_id),
                    order_id BIGINT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    decided_at TIMESTAMPTZ,
                    expires_at TIMESTAMPTZ NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),
                    UNIQUE(course_id,user_id,request_key)
                )""")
                cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS academy_payment_requests_one_pending_idx
                    ON academy_payment_requests(course_id,user_id) WHERE status='pending'""")
                cur.execute("""CREATE INDEX IF NOT EXISTS academy_payment_requests_course_page_idx
                    ON academy_payment_requests(course_id,status,id DESC)""")
                cur.execute("""CREATE TABLE IF NOT EXISTS academy_orders (
                    id BIGSERIAL PRIMARY KEY,
                    course_id BIGINT NOT NULL REFERENCES academy_courses(id),
                    user_id BIGINT NOT NULL REFERENCES users(user_id),
                    amount_uzs BIGINT NOT NULL CHECK(amount_uzs > 0 AND amount_uzs <= 100000000),
                    period_days SMALLINT NOT NULL DEFAULT 30 CHECK(period_days=30),
                    reference TEXT NOT NULL,
                    request_key TEXT NOT NULL,
                    source TEXT NOT NULL CHECK(source IN ('manual','request')),
                    request_id BIGINT UNIQUE REFERENCES academy_payment_requests(id),
                    confirmed_by BIGINT NOT NULL REFERENCES users(user_id),
                    status TEXT NOT NULL DEFAULT 'paid' CHECK(status='paid'),
                    access_from TIMESTAMPTZ NOT NULL,
                    access_until TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(course_id,confirmed_by,source,request_key),
                    UNIQUE(course_id,user_id,reference),
                    CHECK(access_until > access_from)
                )""")
                cur.execute("""CREATE INDEX IF NOT EXISTS academy_orders_course_page_idx
                    ON academy_orders(course_id,id DESC)""")
                cur.execute("""CREATE INDEX IF NOT EXISTS academy_orders_user_course_idx
                    ON academy_orders(user_id,course_id,id DESC)""")
            self._ready = True

    def _locked_course(self, cur, course_id, uid=None, owner=False):
        _integer(course_id, "Kurs raqami")
        # All grant paths lock course -> request -> enrollment in this order.
        cur.execute("SELECT id FROM academy_courses WHERE id=%s FOR UPDATE", (course_id,))
        if not cur.fetchone():
            raise HTTPException(404, "Kurs topilmadi")
        return self.service.owner(cur, course_id, uid) if owner else self.service.course(cur, course_id)

    @staticmethod
    def _paid_course(course):
        if course["status"] != "published":
            raise HTTPException(409, "Bu kurs hozir to‘lov qabul qilmaydi")
        return _integer(course["price_uzs"], "Kurs narxi", 1, MAX_PRICE_UZS)

    @staticmethod
    def _recipient(cur, uid):
        _user_id(uid)
        cur.execute("SELECT user_id FROM users WHERE user_id=%s", (uid,))
        if not cur.fetchone():
            raise HTTPException(404, "Foydalanuvchi topilmadi. Saytdagi hisob ID raqamini tekshiring.")

    @staticmethod
    def _expire(cur, course_id):
        cur.execute("""UPDATE academy_payment_requests SET status='expired',
            decided_at=CURRENT_TIMESTAMP,decision_note='Tekshirish muddati tugadi'
            WHERE course_id=%s AND status='pending' AND expires_at<=CURRENT_TIMESTAMP""", (course_id,))

    def create_request(self, authorization, course_id, body):
        uid = self.service.actor(authorization)
        key = _key(body.get("request_key"))
        reference = _text(body.get("reference", ""), "Chek raqami yoki izoh", 120, True)
        note = _text(body.get("note", ""), "Qo‘shimcha izoh", 1000)
        with self.service.db() as cur:
            course = self._locked_course(cur, course_id)
            self._expire(cur, course_id)
            # Retrying the original payload returns its original status and amount,
            # even if the price or publication state has since changed.
            cur.execute("""SELECT * FROM academy_payment_requests
                WHERE course_id=%s AND user_id=%s AND request_key=%s""", (course_id, uid, key))
            previous = cur.fetchone()
            if previous:
                if previous["reference"] != reference or previous["note"] != note:
                    raise HTTPException(409, "Bu so‘rov kaliti boshqa to‘lovga ishlatilgan")
                return {"payment_request": _request(previous), "notice": MANUAL_NOTICE}
            amount = self._paid_course(course)
            if course["teacher_id"] == uid:
                raise HTTPException(422, "O‘z kursingiz uchun to‘lov so‘rovi kerak emas")
            cur.execute("""SELECT id FROM academy_payment_requests
                WHERE course_id=%s AND user_id=%s AND status='pending'""", (course_id, uid))
            if cur.fetchone():
                raise HTTPException(409, "Avvalgi to‘lovingiz tekshirilmoqda. Yangi so‘rov yuborish shart emas.")
            cur.execute("""SELECT id FROM academy_orders
                WHERE course_id=%s AND user_id=%s AND reference=%s""", (course_id, uid, reference))
            if cur.fetchone():
                raise HTTPException(409, "Bu to‘lov avval hisobga olingan")
            cur.execute("""INSERT INTO academy_payment_requests
                (course_id,user_id,amount_uzs,reference,note,request_key)
                VALUES(%s,%s,%s,%s,%s,%s) RETURNING *""", (course_id, uid, amount, reference, note, key))
            return {"payment_request": _request(cur.fetchone()), "notice": MANUAL_NOTICE}

    def _grant(self, cur, course, recipient, amount, reference, owner, key, source, request_id=None):
        """Caller holds course lock; ledger and enrollment commit together."""
        cur.execute("""SELECT * FROM academy_orders
            WHERE course_id=%s AND confirmed_by=%s AND source=%s AND request_key=%s""",
                    (course["id"], owner, source, key))
        previous = cur.fetchone()
        if previous:
            if (previous["user_id"], previous["amount_uzs"], previous["reference"], previous["request_id"]) != (
                    recipient, amount, reference, request_id):
                raise HTTPException(409, "Bu so‘rov kaliti boshqa to‘lovga ishlatilgan")
            return previous
        cur.execute("""SELECT id FROM academy_orders
            WHERE course_id=%s AND user_id=%s AND reference=%s""", (course["id"], recipient, reference))
        if cur.fetchone():
            raise HTTPException(409, "Bu chek allaqachon hisobga olingan. Takror 30 kun qo‘shilmaydi.")
        self._recipient(cur, recipient)
        cur.execute("""INSERT INTO academy_enrollments(course_id,user_id)
            VALUES(%s,%s) ON CONFLICT(course_id,user_id) DO NOTHING""", (course["id"], recipient))
        cur.execute("""SELECT access_until FROM academy_enrollments
            WHERE course_id=%s AND user_id=%s FOR UPDATE""", (course["id"], recipient))
        enrollment = cur.fetchone()
        cur.execute("SELECT CURRENT_TIMESTAMP AS now")
        now = cur.fetchone()["now"]
        starts, until = grant_period(enrollment["access_until"], now)
        cur.execute("""INSERT INTO academy_orders
            (course_id,user_id,amount_uzs,reference,confirmed_by,request_key,source,request_id,access_from,access_until)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                    (course["id"], recipient, amount, reference, owner, key, source, request_id, starts, until))
        order = cur.fetchone()
        cur.execute("""UPDATE academy_enrollments SET access_until=%s,updated_at=CURRENT_TIMESTAMP
            WHERE course_id=%s AND user_id=%s""", (until, course["id"], recipient))
        return order

    def record(self, authorization, course_id, body):
        uid = self.service.actor(authorization)
        _confirmation(body)
        recipient = _user_id(body.get("user_id"))
        amount = _integer(body.get("amount_uzs"), "To‘lov summasi", 1, MAX_PRICE_UZS)
        reference = _text(body.get("reference", ""), "Chek raqami yoki izoh", 120, True)
        key = _key(body.get("request_key"))
        with self.service.db() as cur:
            course = self._locked_course(cur, course_id, uid, owner=True)
            # Check retry before current-price checks; a later price edit must not
            # make an already recorded payment retry fail or add another period.
            cur.execute("""SELECT * FROM academy_orders
                WHERE course_id=%s AND confirmed_by=%s AND source='manual' AND request_key=%s""",
                        (course_id, uid, key))
            previous = cur.fetchone()
            if previous:
                if (previous["user_id"], previous["amount_uzs"], previous["reference"]) != (recipient, amount, reference):
                    raise HTTPException(409, "Bu so‘rov kaliti boshqa to‘lovga ishlatilgan")
                return {"order": _order(previous), "access_until": _iso(previous["access_until"])}
            if amount != self._paid_course(course):
                raise HTTPException(422, "Summa kursning 30 kunlik narxiga teng bo‘lishi kerak")
            if recipient == uid:
                raise HTTPException(422, "O‘z kursingiz uchun to‘lov qaydi kerak emas")
            order = self._grant(cur, course, recipient, amount, reference, uid, key, "manual")
            # A directly recorded matching receipt settles the pending claim too.
            cur.execute("""UPDATE academy_payment_requests SET status='confirmed',confirmed_by=%s,
                order_id=%s,decided_at=CURRENT_TIMESTAMP
                WHERE course_id=%s AND user_id=%s AND reference=%s AND amount_uzs=%s AND status='pending'""",
                        (uid, order["id"], course_id, recipient, reference, amount))
            return {"order": _order(order), "access_until": _iso(order["access_until"])}

    def decide(self, authorization, request_id, body, confirm):
        uid = self.service.actor(authorization)
        _integer(request_id, "So‘rov raqami")
        if confirm:
            _confirmation(body)
        reason = "" if confirm else _text(body.get("reason", ""), "Rad etish sababi", 500, True)
        with self.service.db() as cur:
            cur.execute("SELECT course_id FROM academy_payment_requests WHERE id=%s", (request_id,))
            seed = cur.fetchone()
            if not seed:
                raise HTTPException(404, "To‘lov so‘rovi topilmadi")
            course = self._locked_course(cur, seed["course_id"], uid, owner=True)
            cur.execute("SELECT * FROM academy_payment_requests WHERE id=%s FOR UPDATE", (request_id,))
            request = cur.fetchone()
            if request["status"] == "confirmed" and confirm:
                cur.execute("SELECT * FROM academy_orders WHERE id=%s", (request["order_id"],))
                order = cur.fetchone()
                if not order:
                    raise HTTPException(409, "To‘lov qaydi topilmadi; qayta tasdiqlamang")
                return {"payment_request": _request(request), "order": _order(order),
                        "access_until": _iso(order["access_until"])}
            if request["status"] == "rejected" and not confirm:
                if request["decision_note"] != reason:
                    raise HTTPException(409, "Bu so‘rov avval boshqa sabab bilan rad etilgan")
                return {"payment_request": _request(request)}
            if request["status"] != "pending":
                raise HTTPException(409, "Bu so‘rov bo‘yicha qaror allaqachon chiqarilgan")
            cur.execute("SELECT CURRENT_TIMESTAMP AS now")
            if request["expires_at"] <= cur.fetchone()["now"]:
                raise HTTPException(409, "To‘lov so‘rovi muddati tugagan. O‘quvchi yangi so‘rov yuborsin.")
            if confirm:
                self._paid_course(course)
                # The owner sees and verifies the price captured at request time.
                # Changes to the course price never silently alter that receipt.
                order = self._grant(cur, course, request["user_id"], request["amount_uzs"],
                                    request["reference"], uid, f"request:{request_id}", "request", request_id)
                cur.execute("""UPDATE academy_payment_requests SET status='confirmed',confirmed_by=%s,
                    order_id=%s,decided_at=CURRENT_TIMESTAMP WHERE id=%s RETURNING *""",
                            (uid, order["id"], request_id))
                return {"payment_request": _request(cur.fetchone()), "order": _order(order),
                        "access_until": _iso(order["access_until"])}
            cur.execute("""UPDATE academy_payment_requests SET status='rejected',confirmed_by=%s,
                decision_note=%s,decided_at=CURRENT_TIMESTAMP WHERE id=%s RETURNING *""",
                        (uid, reason, request_id))
            return {"payment_request": _request(cur.fetchone())}

    def requests(self, authorization, course_id, owner=False, status="all", after_id=0, limit=20):
        uid = self.service.actor(authorization)
        _integer(course_id, "Kurs raqami")
        _integer(after_id, "Sahifa raqami", 0)
        _integer(limit, "Sahifa hajmi", 1, MAX_PAGE)
        if status not in {"all", "pending", "confirmed", "rejected", "expired"}:
            raise HTTPException(422, "So‘rov holati noto‘g‘ri")
        with self.service.db() as cur:
            if owner:
                self.service.owner(cur, course_id, uid)
            else:
                self.service.course(cur, course_id)
            # No row mutation during GET. Present expired claims as expired; the
            # next new request expires rows atomically while holding course lock.
            scope, args = "r.course_id=%s", [course_id]
            if not owner:
                scope += " AND r.user_id=%s"
                args.append(uid)
            if after_id:
                scope += " AND r.id<%s"
                args.append(after_id)
            if status == "expired":
                scope += " AND (r.status='expired' OR (r.status='pending' AND r.expires_at<=CURRENT_TIMESTAMP))"
            elif status == "pending":
                scope += " AND r.status='pending' AND r.expires_at>CURRENT_TIMESTAMP"
            elif status != "all":
                scope += " AND r.status=%s"
                args.append(status)
            args.append(limit + 1)
            cur.execute(f"""SELECT r.*,u.full_name AS user_name,
                CASE WHEN r.status='pending' AND r.expires_at<=CURRENT_TIMESTAMP
                    THEN 'expired' ELSE r.status END AS effective_status
                FROM academy_payment_requests r JOIN users u ON u.user_id=r.user_id
                WHERE {scope} ORDER BY r.id DESC LIMIT %s""", args)
            rows = cur.fetchall()
            items = [_request(dict(row, status=row["effective_status"])) for row in rows[:limit]]
            return {"items": items, "next_cursor": items[-1]["id"] if len(rows) > limit else None,
                    "payment_mode": "manual", "notice": MANUAL_NOTICE}

    def ledger(self, authorization, course_id, after_id=0, limit=20):
        uid = self.service.actor(authorization)
        _integer(after_id, "Sahifa raqami", 0)
        _integer(limit, "Sahifa hajmi", 1, MAX_PAGE)
        with self.service.db() as cur:
            self.service.owner(cur, course_id, uid)
            cur.execute("""SELECT o.*,u.full_name AS user_name FROM academy_orders o
                JOIN users u ON u.user_id=o.user_id
                WHERE o.course_id=%s AND (%s=0 OR o.id<%s) ORDER BY o.id DESC LIMIT %s""",
                        (course_id, after_id, after_id, limit + 1))
            rows = cur.fetchall()
            items = [_order(row) for row in rows[:limit]]
            return {"items": items, "next_cursor": int(items[-1]["id"]) if len(rows) > limit else None}

    def order(self, authorization, order_id):
        uid = self.service.actor(authorization)
        _integer(order_id, "To‘lov qaydi raqami")
        with self.service.db() as cur:
            cur.execute("SELECT * FROM academy_orders WHERE id=%s AND user_id=%s", (order_id, uid))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "To‘lov qaydi topilmadi")
            return _order(row)


def register_payments(app, service):
    payments = ManualPaymentService(service)
    router = APIRouter(prefix="/api/kurslar", tags=["Kurs to‘lovlari"])

    @router.post("/courses/{course_id}/checkout")
    def checkout(course_id: int, body: dict = Body(...), authorization: str = Header(default="")):
        service.actor(authorization)
        raise HTTPException(503, MANUAL_NOTICE)

    @router.post("/courses/{course_id}/payment-request")
    def payment_request(course_id: int, body: dict = Body(...), authorization: str = Header(default="")):
        return payments.create_request(authorization, course_id, body)

    @router.get("/courses/{course_id}/my-payment-requests")
    def my_requests(course_id: int, after_id: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=MAX_PAGE),
                    authorization: str = Header(default="")):
        return payments.requests(authorization, course_id, after_id=after_id, limit=limit)

    @router.get("/courses/{course_id}/payment-requests")
    def owner_requests(course_id: int, status: str = "all", after_id: int = Query(0, ge=0),
                       limit: int = Query(20, ge=1, le=MAX_PAGE), authorization: str = Header(default="")):
        return payments.requests(authorization, course_id, owner=True, status=status, after_id=after_id, limit=limit)

    @router.post("/payment-requests/{request_id}/confirm")
    def confirm(request_id: int, body: dict = Body(...), authorization: str = Header(default="")):
        return payments.decide(authorization, request_id, body, True)

    @router.post("/payment-requests/{request_id}/reject")
    def reject(request_id: int, body: dict = Body(...), authorization: str = Header(default="")):
        return payments.decide(authorization, request_id, body, False)

    @router.get("/courses/{course_id}/payments")
    def ledger(course_id: int, after_id: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=MAX_PAGE),
               authorization: str = Header(default="")):
        return payments.ledger(authorization, course_id, after_id, limit)

    @router.post("/courses/{course_id}/payments")
    def record(course_id: int, body: dict = Body(...), authorization: str = Header(default="")):
        return payments.record(authorization, course_id, body)

    @router.get("/orders/{order_id}")
    def order(order_id: int, authorization: str = Header(default="")):
        return payments.order(authorization, order_id)

    app.include_router(router)
    return payments
