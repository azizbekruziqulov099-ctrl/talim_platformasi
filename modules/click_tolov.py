"""REV160: Click SHOP-API — pulli kursga AVTOMATIK to'lov (admin har birini qo'lda tasdiqlamaydi).

Oqim:
  1. O'quvchi «Click orqali to'lash» → /api/kurslar/courses/{id}/click-invoice — buyurtma (merchant_trans_id) yaratiladi
     va Click to'lov sahifasi manzili qaytariladi (my.click.uz/services/pay?...).
  2. O'quvchi Click sahifasida istalgan Uzcard/Humo kartasidan yoki Click hamyonidan to'laydi.
  3. Click serverimizga ikki marta murojaat qiladi:
       POST /api/click/prepare  (action=0) — buyurtma bor, summa to'g'ri → merchant_prepare_id
       POST /api/click/complete (action=1) — pul yechildi → kurs 30 kunga AVTOMATIK ochiladi.
     Har so'rov imzosi (sign_string, MD5 + SECRET_KEY) tekshiriladi; bir to'lov ikki marta hisoblanmaydi.

Sozlash (faqat Railway → backend → Variables; kalitlar kodda va chatda turmaydi):
  CLICK_SERVICE_ID, CLICK_MERCHANT_ID, CLICK_SECRET_KEY  — Click merchant kabinetidan (merchant.click.uz)
Kalitlar qo'yilmagan bo'lsa — avtomatik Click o'chiq, qo'lda tasdiqlash (rekvizitlar) ishlayveradi.

Pul Click merchant egasining (sayt egasining) hisobiga tushadi. Shuning uchun avtomatik Click faqat sayt
administratorlari yaratgan kurslarda yoqiladi (boshqa o'qituvchilar kursi — o'z rekvizitlari va qo'lda tasdiqlash).
"""
import hashlib
import hmac
import os
import secrets
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode, urlparse

from fastapi import APIRouter, Body, Header, HTTPException, Request

PAY_URL = "https://my.click.uz/services/pay"

# Click javob kodlari (docs.click.uz)
OK, SIGN_FAILED, BAD_AMOUNT, NO_ACTION, ALREADY_PAID, NO_ORDER, NO_TRANSACTION, UPDATE_FAILED, BAD_REQUEST, CANCELLED = (
    0, -1, -2, -3, -4, -5, -6, -7, -8, -9)
NOTE = {OK: "Success", SIGN_FAILED: "SIGN CHECK FAILED!", BAD_AMOUNT: "Incorrect parameter amount",
        NO_ACTION: "Action not found", ALREADY_PAID: "Already paid", NO_ORDER: "User does not exist",
        NO_TRANSACTION: "Transaction does not exist", UPDATE_FAILED: "Failed to update user",
        BAD_REQUEST: "Error in request from click", CANCELLED: "Transaction cancelled"}


def sozlama():
    sid, mid, key = (os.getenv(k, "").strip() for k in ("CLICK_SERVICE_ID", "CLICK_MERCHANT_ID", "CLICK_SECRET_KEY"))
    return {"service_id": sid, "merchant_id": mid, "secret_key": key, "yoqilgan": bool(sid and mid and key)}


def imzo(p, secret_key, action):
    """Click sign_string: md5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id
    [+ merchant_prepare_id] + amount + action + sign_time)."""
    parts = [p.get("click_trans_id", ""), p.get("service_id", ""), secret_key, p.get("merchant_trans_id", "")]
    if str(action) == "1":
        parts.append(p.get("merchant_prepare_id", ""))
    parts += [p.get("amount", ""), p.get("action", ""), p.get("sign_time", "")]
    return hashlib.md5("".join(str(x) for x in parts).encode("utf-8")).hexdigest()


def imzo_togrimi(p, secret_key, action):
    return bool(secret_key) and hmac.compare_digest(imzo(p, secret_key, action), str(p.get("sign_string", "")).lower())


def summa(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


def yangi_kod():
    """Bot va kommunal to'lovlardagi kabi faqat raqamli buyurtma kodi: YYMMDD + 9 tasodifiy raqam (15 xona)."""
    from datetime import datetime
    return datetime.now().strftime("%y%m%d") + "".join(secrets.choice("0123456789") for _ in range(9))


def tolov_havolasi(cfg, amount_uzs, mtid, return_url=""):
    q = {"service_id": cfg["service_id"], "merchant_id": cfg["merchant_id"], "amount": f"{int(amount_uzs)}.00",
         "transaction_param": mtid}
    if return_url:
        q["return_url"] = return_url
    return f"{PAY_URL}?{urlencode(q)}"


def javob(p, error, **extra):
    out = {"click_trans_id": p.get("click_trans_id"), "merchant_trans_id": p.get("merchant_trans_id"),
           "error": error, "error_note": NOTE.get(error, "Error")}
    out.update(extra)
    return out


class ClickService:
    def __init__(self, academy, payments):
        self.academy = academy          # AcademyService: db(), actor(), course(), can_teach()
        self.payments = payments        # ManualPaymentService: _grant(), _paid_course(), migrate()
        self._ready = False

    def migrate(self):
        if self._ready:
            return
        self.payments.migrate()
        with self.academy.db() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(47091204)")
            cur.execute("""CREATE TABLE IF NOT EXISTS click_tolovlar (
                id BIGSERIAL PRIMARY KEY,
                merchant_trans_id TEXT NOT NULL UNIQUE,
                course_id BIGINT NOT NULL REFERENCES academy_courses(id),
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                amount_uzs BIGINT NOT NULL CHECK(amount_uzs > 0),
                status TEXT NOT NULL DEFAULT 'yaratildi' CHECK(status IN ('yaratildi','tayyor','tolandi','bekor')),
                click_trans_id BIGINT,
                click_paydoc_id BIGINT,
                order_id BIGINT,
                error_note TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")
            cur.execute("CREATE INDEX IF NOT EXISTS click_tolovlar_user_idx ON click_tolovlar(user_id,course_id,id DESC)")
            # REV162: shu jadvalda bog'cha obunasi buyurtmalari ham (kurs o'rniga obuna ma'lumoti)
            cur.execute("ALTER TABLE click_tolovlar ALTER COLUMN course_id DROP NOT NULL")
            cur.execute("ALTER TABLE click_tolovlar ADD COLUMN IF NOT EXISTS turi TEXT NOT NULL DEFAULT 'kurs'")
            cur.execute("ALTER TABLE click_tolovlar ADD COLUMN IF NOT EXISTS obuna JSONB")
            # academy_orders.source endi 'click' ni ham qabul qiladi
            cur.execute("ALTER TABLE academy_orders DROP CONSTRAINT IF EXISTS academy_orders_source_check")
            cur.execute("""ALTER TABLE academy_orders ADD CONSTRAINT academy_orders_source_check
                CHECK(source IN ('manual','request','click','payme'))""")
        self._ready = True

    def admin_kursi(self, cur, course):
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (course["teacher_id"],))
        return cur.fetchone() is not None

    def avto(self, cur, course):
        return sozlama()["yoqilgan"] and self.admin_kursi(cur, course)

    # — o'quvchi —
    def invoice(self, authorization, course_id, body):
        """Click uchun (eski v160 frontend bilan mos): buyurtma + Click sahifasi manzili."""
        cfg = sozlama()
        if not cfg["yoqilgan"]:
            raise HTTPException(503, "Click avtomatik to‘lovi hali sozlanmagan")
        b = self.buyurtma(authorization, course_id, body)
        return {"pay_url": b["havolalar"]["click"], "merchant_trans_id": b["kod"], "amount_uzs": b["amount_uzs"]}

    def buyurtma(self, authorization, course_id, body):
        """REV161: bitta buyurtma kodi (faqat raqam) — Click, Payme va boshqa ulangan tizimlarda birdek ishlaydi.
        Qaytaradi: {kod, amount_uzs, havolalar: {click: url|None, payme: url|None}}."""
        uid = self.academy.actor(authorization)
        try:
            from modules import payme_tolov as _pm
        except ImportError:
            from . import payme_tolov as _pm
        cfg, pcfg = sozlama(), _pm.sozlama()
        if not (cfg["yoqilgan"] or pcfg["yoqilgan"]):
            raise HTTPException(503, "Avtomatik to‘lov hali sozlanmagan")
        self.migrate()
        ret = str((body or {}).get("return_url") or "")
        u = urlparse(ret)
        if ret and (u.scheme != "https" or len(ret) > 600):
            ret = ""
        with self.academy.db() as cur:
            course = self.academy.course(cur, course_id)
            amount = self.payments._paid_course(course)
            if int(course["teacher_id"]) == uid:
                raise HTTPException(422, "O‘z kursingiz uchun to‘lov kerak emas")
            if not self.admin_kursi(cur, course):
                raise HTTPException(409, "Bu kurs uchun avtomatik Click to‘lovi yo‘q — o‘qituvchi rekvizitlari orqali to‘lang")
            # tugallanmagan buyurtma bo'lsa — o'shasi (bir xil summa), aks holda yangisi.
            # Payme tranzaksiyasi ochilgan buyurtma ham qayta ishlatiladi (bir buyurtma — bir to'lov)
            cur.execute("""SELECT merchant_trans_id FROM click_tolovlar WHERE course_id=%s AND user_id=%s
                AND status IN ('yaratildi','tayyor') AND amount_uzs=%s AND created_at > NOW() - INTERVAL '1 day'
                ORDER BY id DESC LIMIT 1""", (course["id"], uid, amount))
            row = cur.fetchone()
            mtid = row["merchant_trans_id"] if row else yangi_kod()
            if not row:
                cur.execute("""INSERT INTO click_tolovlar(merchant_trans_id,course_id,user_id,amount_uzs)
                    VALUES(%s,%s,%s,%s)""", (mtid, course["id"], uid, amount))
        return {"kod": mtid, "amount_uzs": amount, "havolalar": {
            "click": tolov_havolasi(cfg, amount, mtid, ret) if cfg["yoqilgan"] else None,
            "payme": _pm.tolov_havolasi(pcfg, amount, mtid, ret) if pcfg["yoqilgan"] else None}}

    def obuna_buyurtma(self, cur, uid, amount, data, ret=""):
        """REV162: bog'cha obunasi uchun buyurtma (shu tranzaksiyada). Qaytaradi {kod, amount_uzs, havolalar}."""
        try:
            from modules import payme_tolov as _pm
        except ImportError:
            from . import payme_tolov as _pm
        cfg, pcfg = sozlama(), _pm.sozlama()
        if not (cfg["yoqilgan"] or pcfg["yoqilgan"]):
            raise HTTPException(503, "Avtomatik to‘lov (Click / Payme) hali ulanmagan. Admin kalitlarni qo‘ygach ishlaydi.")
        self.migrate()
        u = urlparse(ret or "")
        if ret and (u.scheme != "https" or len(ret) > 600):
            ret = ""
        import json as _json
        payload = _json.dumps(data, ensure_ascii=False, default=str)
        cur.execute("""SELECT merchant_trans_id FROM click_tolovlar WHERE turi='obuna' AND user_id=%s AND status IN ('yaratildi','tayyor')
            AND amount_uzs=%s AND obuna->>'bola_id'=%s AND obuna->'fanlar'=%s::jsonb->'fanlar'
            AND created_at > NOW() - INTERVAL '1 day' ORDER BY id DESC LIMIT 1""",
                    (uid, int(amount), str(data["bola_id"]), payload))
        row = cur.fetchone()
        mtid = row["merchant_trans_id"] if row else yangi_kod()
        if row:
            cur.execute("UPDATE click_tolovlar SET obuna=%s::jsonb, updated_at=NOW() WHERE merchant_trans_id=%s", (payload, mtid))
        else:
            cur.execute("""INSERT INTO click_tolovlar(merchant_trans_id,course_id,user_id,amount_uzs,turi,obuna)
                VALUES(%s,NULL,%s,%s,'obuna',%s::jsonb)""", (mtid, uid, int(amount), payload))
        return {"kod": mtid, "amount_uzs": int(amount), "havolalar": {
            "click": tolov_havolasi(cfg, amount, mtid, ret) if cfg["yoqilgan"] else None,
            "payme": _pm.tolov_havolasi(pcfg, amount, mtid, ret) if pcfg["yoqilgan"] else None}}

    def obuna_ber(self, cur, t, manba, kod):
        """To'langan obuna buyurtmasi → bog'cha obunasi 30 kunga (bogcha_reja.obuna_tolandi)."""
        try:
            from modules import bogcha_reja as _br
        except ImportError:
            from . import bogcha_reja as _br
        data = t["obuna"]
        if isinstance(data, str):
            import json as _json
            data = _json.loads(data)
        _br.obuna_tolandi(cur, data, kod, int(t["amount_uzs"]), manba)

    def holat(self, authorization, mtid):
        uid = self.academy.actor(authorization)
        self.migrate()
        with self.academy.db() as cur:
            cur.execute("SELECT status,course_id,amount_uzs FROM click_tolovlar WHERE merchant_trans_id=%s AND user_id=%s",
                        (str(mtid)[:64], uid))
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "To‘lov topilmadi")
            return {"status": row["status"], "course_id": row["course_id"], "amount_uzs": row["amount_uzs"]}

    # — Click serveri —
    def prepare(self, p):
        cfg = sozlama()
        if not cfg["yoqilgan"]:
            return javob(p, BAD_REQUEST)
        if str(p.get("action")) != "0":
            return javob(p, NO_ACTION)
        if str(p.get("service_id")) != cfg["service_id"] or not imzo_togrimi(p, cfg["secret_key"], 0):
            return javob(p, SIGN_FAILED)
        self.migrate()
        with self.academy.db() as cur:
            cur.execute("SELECT * FROM click_tolovlar WHERE merchant_trans_id=%s FOR UPDATE", (str(p.get("merchant_trans_id")),))
            t = cur.fetchone()
            if not t:
                return javob(p, NO_ORDER)
            if t["status"] == "tolandi":
                return javob(p, ALREADY_PAID)
            if t["status"] == "bekor":
                return javob(p, CANCELLED)
            s = summa(p.get("amount"))
            if s is None or s != Decimal(t["amount_uzs"]):
                return javob(p, BAD_AMOUNT)
            cur.execute("""UPDATE click_tolovlar SET status='tayyor',click_trans_id=%s,click_paydoc_id=%s,updated_at=NOW()
                WHERE id=%s""", (int(p.get("click_trans_id") or 0) or None, int(p.get("click_paydoc_id") or 0) or None, t["id"]))
            return javob(p, OK, merchant_prepare_id=t["id"])

    def complete(self, p):
        cfg = sozlama()
        if not cfg["yoqilgan"]:
            return javob(p, BAD_REQUEST)
        if str(p.get("action")) != "1":
            return javob(p, NO_ACTION)
        if str(p.get("service_id")) != cfg["service_id"] or not imzo_togrimi(p, cfg["secret_key"], 1):
            return javob(p, SIGN_FAILED)
        self.migrate()
        with self.academy.db() as cur:
            cur.execute("SELECT * FROM click_tolovlar WHERE merchant_trans_id=%s", (str(p.get("merchant_trans_id")),))
            seed = cur.fetchone()
            if not seed:
                return javob(p, NO_ORDER)
            # qulflash tartibi: kurs → to'lov (qo'lda tasdiqlash bilan bir xil — o'zaro qulflanib qolmaydi)
            course = None if seed.get("turi") == "obuna" else self.payments._locked_course(cur, seed["course_id"])
            cur.execute("SELECT * FROM click_tolovlar WHERE id=%s FOR UPDATE", (seed["id"],))
            t = cur.fetchone()
            if str(p.get("merchant_prepare_id")) != str(t["id"]):
                return javob(p, NO_TRANSACTION)
            if t["status"] == "tolandi":
                return javob(p, ALREADY_PAID, merchant_confirm_id=t["order_id"] or t["id"])
            if t["status"] == "bekor":
                return javob(p, CANCELLED)
            s = summa(p.get("amount"))
            if s is None or s != Decimal(t["amount_uzs"]):
                return javob(p, BAD_AMOUNT)
            try:
                click_error = int(p.get("error") or 0)
            except ValueError:
                click_error = -1
            if click_error < 0:   # Click pulni yecha olmadi — buyurtma bekor
                cur.execute("UPDATE click_tolovlar SET status='bekor',error_note=%s,updated_at=NOW() WHERE id=%s",
                            (str(p.get("error_note") or "")[:300], t["id"]))
                return javob(p, CANCELLED)
            if t.get("turi") == "obuna":   # REV162: bog'cha obunasi
                self.obuna_ber(cur, t, "click", f"click:{p.get('click_trans_id')}")
                cur.execute("UPDATE click_tolovlar SET status='tolandi',updated_at=NOW() WHERE id=%s", (t["id"],))
                return javob(p, OK, merchant_confirm_id=t["id"])
            order = self.payments._grant(
                cur, course, t["user_id"], int(t["amount_uzs"]), f"CLICK-{p.get('click_paydoc_id') or p.get('click_trans_id')}",
                int(course["teacher_id"]), f"click:{p.get('click_trans_id')}", "click")
            cur.execute("UPDATE click_tolovlar SET status='tolandi',order_id=%s,updated_at=NOW() WHERE id=%s",
                        (order["id"], t["id"]))
            return javob(p, OK, merchant_confirm_id=order["id"])


def register_click(app, academy, payments):
    svc = ClickService(academy, payments)
    router = APIRouter(tags=["Click to‘lov"])

    async def form(request):
        try:
            data = await request.form()
            return {k: str(v) for k, v in data.items()}
        except Exception:
            try:
                return {k: str(v) for k, v in (await request.json()).items()}
            except Exception:
                return {}

    @router.post("/api/click/prepare")
    async def click_prepare(request: Request):
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(svc.prepare, await form(request))

    @router.post("/api/click/complete")
    async def click_complete(request: Request):
        from starlette.concurrency import run_in_threadpool
        return await run_in_threadpool(svc.complete, await form(request))

    @router.post("/api/kurslar/courses/{course_id}/click-invoice")
    def click_invoice(course_id: int, body: dict = Body(default={}), authorization: str = Header(default="")):
        return svc.invoice(authorization, course_id, body)

    @router.post("/api/kurslar/courses/{course_id}/tolov-buyurtma")
    def tolov_buyurtma(course_id: int, body: dict = Body(default={}), authorization: str = Header(default="")):
        return svc.buyurtma(authorization, course_id, body)

    @router.get("/api/kurslar/click-holat/{mtid}")
    def click_holat(mtid: str, authorization: str = Header(default="")):
        return svc.holat(authorization, mtid)

    app.include_router(router)
    return svc
