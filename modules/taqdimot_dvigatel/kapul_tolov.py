"""KAPUL to'lovi: noyob summali buyurtma + telefondagi karta SMS'ini botga uzatish (webhook) + avtomatik kapul qo'shish.

Qoida (foydalanuvchi talabi):
  • Mijoz N kapul tanlaydi. Unga N*1000 dan 999 so'mgacha KAM, hech kimda band bo'lmagan noyob summa beriladi
    (masalan 50 kapul → 49 037 so'm). Kapul = summani yuqoriga yaxlitlash: ceil(49 037 / 1000) = 50.
  • Shu oraliqdagi 999 ta summa band bo'lsa — keyingi oraliq (51 kapul: 50 001…50 999) olinadi, mijozga 51 kapul tushadi.
  • Yaxlit summa (50 000) hech qachon berilmaydi — boshqa kirimlar bilan adashmaslik uchun.
  • SMS kelganda matndagi summalar kutilayotgan buyurtmalar bilan solishtiriladi; topilsa kapul bir marta qo'shiladi.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import random
import re
import secrets
import uuid

from fastapi import Header, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from . import kapul

SCHEMA = """
CREATE TABLE IF NOT EXISTS kapul_buyurtma (
    id TEXT PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    kapul INT NOT NULL,
    summa INT NOT NULL,
    holat TEXT NOT NULL DEFAULT 'kutilmoqda',
    yaratildi TIMESTAMPTZ NOT NULL DEFAULT now(),
    muddat TIMESTAMPTZ NOT NULL,
    tolandi TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS kapul_buyurtma_kutilmoqda ON kapul_buyurtma(summa) WHERE holat = 'kutilmoqda';
CREATE INDEX IF NOT EXISTS kapul_buyurtma_owner ON kapul_buyurtma(owner_id, yaratildi DESC);
CREATE TABLE IF NOT EXISTS kapul_sms (
    id BIGSERIAL PRIMARY KEY,
    xesh TEXT NOT NULL UNIQUE,
    matn TEXT NOT NULL,
    natija TEXT NOT NULL,
    buyurtma_id TEXT,
    vaqt TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""
MAX_KAPUL = 1000
ORALIQ_SONI = 30                 # keyingi oraliqlardan nechtasigacha qaraladi
KECHIKKAN_SOAT = 24              # muddati o'tgan buyurtmaga ham shuncha vaqt ichida kelgan to'lov hisoblanadi
CHIQIM = re.compile(r"списани|оплата|покупк|снятие|chiqim|xarid|to'lov amalga|spisanie|oplata|purchase|withdraw|debit", re.I)
RAQAM = re.compile(r"(?<![\d])(\d{1,3}(?:[   ,]\d{3})+|\d+)(?:[.,]\d{1,2})?(?![\d])")


def summalar(matn: str) -> list[int]:
    """SMS matnidagi barcha so'm summalari (tiyinsiz), paydo bo'lish tartibida."""
    out = []
    for m in RAQAM.finditer(matn or ""):
        t = re.sub(r"[   ,]", "", m.group(1))
        if t.isdigit() and 1 <= len(t) <= 9:
            out.append(int(t))
    return out


def yangi_summa(cur, n: int, som: int) -> tuple[int, int]:
    """n kapul uchun noyob summa va unga to'g'ri keladigan kapul soni. Band bo'lsa keyingi oraliq."""
    for b in range(n, n + ORALIQ_SONI):
        lo, hi = b * som - som + 1, b * som - 1
        cur.execute("SELECT summa FROM kapul_buyurtma WHERE holat='kutilmoqda' AND summa BETWEEN %s AND %s", (lo, hi))
        band = {int(r["summa"]) for r in cur.fetchall()}
        bosh = [x for x in range(lo, hi + 1) if x not in band]
        if bosh:
            return random.choice(bosh), b
    raise ValueError("Hozir band, birozdan keyin urinib ko'ring")


def muddati_otganlar(cur):
    cur.execute("UPDATE kapul_buyurtma SET holat='muddati' WHERE holat='kutilmoqda' AND muddat < now()")


def buyurtma_och(cur, uid, n: int) -> dict:
    n = int(n)
    if not 1 <= n <= MAX_KAPUL:
        raise ValueError(f"Kapul soni 1 dan {MAX_KAPUL} gacha bo'lsin")
    muddati_otganlar(cur)
    cur.execute("SELECT count(*) AS n FROM kapul_buyurtma WHERE owner_id=%s AND holat='kutilmoqda'", (uid,))
    if cur.fetchone()["n"] >= 3:
        raise ValueError("Kutilayotgan 3 ta buyurtmangiz bor. Avval to'lang yoki bekor qiling.")
    s = kapul.sozlama(cur, yangila=True)
    if not s["karta_raqam"]:
        raise ValueError("To'lov hali yoqilmagan (karta raqami kiritilmagan)")
    for _ in range(5):                      # parallel buyurtma bir xil summa olsa — qayta urinadi
        summa, kap = yangi_summa(cur, n, s["som"])
        oid = uuid.uuid4().hex[:12]
        cur.execute("INSERT INTO kapul_buyurtma(id, owner_id, kapul, summa, muddat) VALUES(%s,%s,%s,%s, now() + make_interval(mins => %s)) "
                    "ON CONFLICT (summa) WHERE holat = 'kutilmoqda' DO NOTHING RETURNING id", (oid, uid, kap, summa, s["buyurtma_daqiqa"]))
        if cur.fetchone():
            return buyurtma_korinish(cur, oid)
    raise ValueError("Hozir band, birozdan keyin urinib ko'ring")


def buyurtma_korinish(cur, oid, uid=None) -> dict | None:
    cur.execute("SELECT id, owner_id, kapul, summa, holat, EXTRACT(EPOCH FROM (muddat - now()))::int AS qoldi FROM kapul_buyurtma WHERE id=%s", (oid,))
    r = cur.fetchone()
    if not r or (uid is not None and r["owner_id"] != uid):
        return None
    s = kapul.sozlama(cur)
    return {"id": r["id"], "kapul": int(r["kapul"]), "summa": int(r["summa"]), "holat": r["holat"], "qoldi": max(0, int(r["qoldi"])),
            "karta_raqam": s["karta_raqam"], "karta_egasi": s["karta_egasi"], "som": s["som"]}


def sms_qabul(cur, matn: str) -> dict:
    """Bitta SMS'ni qayta ishlaydi. Qaytadi: {natija, buyurtma?}. Bir xil matn ikki marta hisoblanmaydi."""
    matn = (matn or "").strip()[:2000]
    if not matn:
        return {"natija": "bosh"}
    xesh = hashlib.sha256(matn.encode()).hexdigest()
    cur.execute("SELECT natija FROM kapul_sms WHERE xesh=%s", (xesh,))
    if cur.fetchone():
        return {"natija": "takror"}
    natija, bid = "topilmadi", None
    if CHIQIM.search(matn):
        natija = "chiqim"
    else:
        muddati_otganlar(cur)
        sonlar = summalar(matn)
        cur.execute("SELECT id, owner_id, kapul, summa, holat FROM kapul_buyurtma WHERE (holat='kutilmoqda' OR (holat='muddati' AND muddat > now() - make_interval(hours => %s))) "
                    "AND summa = ANY(%s) ORDER BY (holat='kutilmoqda') DESC, yaratildi DESC", (KECHIKKAN_SOAT, sonlar or [0]))
        rows = cur.fetchall()
        if rows:
            rows.sort(key=lambda r: (0 if r["holat"] == "kutilmoqda" else 1, sonlar.index(int(r["summa"]))))
            r = rows[0]
            cur.execute("UPDATE kapul_buyurtma SET holat='tolandi', tolandi=now() WHERE id=%s AND holat IN ('kutilmoqda','muddati') RETURNING id", (r["id"],))
            if cur.fetchone():
                kapul.qosh(cur, r["owner_id"], r["kapul"], "tolov", r["id"])
                natija, bid = "tolandi", r["id"]
    cur.execute("INSERT INTO kapul_sms(xesh, matn, natija, buyurtma_id) VALUES(%s,%s,%s,%s) ON CONFLICT (xesh) DO NOTHING", (xesh, matn, natija, bid))
    return {"natija": natija, "buyurtma": bid}


def sms_kalit(cur) -> str:
    cur.execute("SELECT qiymat FROM kapul_sozlama WHERE kalit='sms_kalit'")
    r = cur.fetchone()
    if r:
        return r["qiymat"]
    k = secrets.token_urlsafe(24)
    cur.execute("INSERT INTO kapul_sozlama(kalit, qiymat) VALUES('sms_kalit', %s) ON CONFLICT (kalit) DO NOTHING", (k,))
    cur.execute("SELECT qiymat FROM kapul_sozlama WHERE kalit='sms_kalit'")
    return cur.fetchone()["qiymat"]


def sozlama_saqla(cur, d: dict) -> dict:
    """Admin sozlamalarini tekshirib saqlaydi. Noto'g'ri qiymat — ValueError."""
    for k, v in d.items():
        if k not in kapul.SOZLAMA:
            raise ValueError(f"Noma'lum sozlama: {k}")
        std = kapul.SOZLAMA[k][0]
        if isinstance(std, int):
            try:
                v = int(v)
            except (TypeError, ValueError):
                raise ValueError(f"«{kapul.SOZLAMA[k][1]}» butun son bo'lsin")
            if v < 0 or v > 1_000_000 or (k in ("som", "ppt_10_slayd", "buyurtma_daqiqa") and v < 1):
                raise ValueError(f"«{kapul.SOZLAMA[k][1]}»: qiymat noto'g'ri")
        else:
            v = re.sub(r"\s+", " ", str(v or "")).strip()[:80]
            if k == "karta_raqam" and v and not re.fullmatch(r"[\d ]{12,23}", v):
                raise ValueError("Karta raqami faqat raqamlardan iborat bo'lsin (masalan 8600 1234 5678 9012)")
        cur.execute("INSERT INTO kapul_sozlama(kalit, qiymat, yangilandi) VALUES(%s,%s, now()) ON CONFLICT (kalit) DO UPDATE SET qiymat=EXCLUDED.qiymat, yangilandi=now()",
                    (k, str(v)))
    return kapul.sozlama(cur, yangila=True)


def admin_holat(cur) -> dict:
    muddati_otganlar(cur)
    s = kapul.sozlama(cur, yangila=True)
    cur.execute("SELECT id, owner_id, kapul, summa, holat, yaratildi, tolandi FROM kapul_buyurtma ORDER BY yaratildi DESC LIMIT 40")
    ord_ = [{"id": r["id"], "uid": r["owner_id"], "kapul": r["kapul"], "summa": r["summa"], "holat": r["holat"],
             "vaqt": r["yaratildi"].isoformat(), "tolandi": r["tolandi"].isoformat() if r["tolandi"] else None} for r in cur.fetchall()]
    cur.execute("SELECT id, matn, natija, buyurtma_id, vaqt FROM kapul_sms ORDER BY id DESC LIMIT 30")
    sms = [{"id": r["id"], "matn": r["matn"], "natija": r["natija"], "buyurtma": r["buyurtma_id"], "vaqt": r["vaqt"].isoformat()} for r in cur.fetchall()]
    cur.execute("SELECT COALESCE(sum(kapul),0) AS k, count(*) AS n FROM kapul_buyurtma WHERE holat='tolandi'")
    st = cur.fetchone()
    cur.execute("SELECT COALESCE(sum(balans),0) AS b, count(*) AS n FROM kapul_hamyon")
    h = cur.fetchone()
    return {"sozlama": s, "izoh": {k: v[1] for k, v in kapul.SOZLAMA.items()}, "sms_kalit": sms_kalit(cur),
            "buyurtmalar": ord_, "sms": sms,
            "jami": {"sotilgan_kapul": int(st["k"]), "tolovlar": int(st["n"]), "hamyonlar": int(h["n"]), "hamyonlarda": int(h["b"])}}


def register(app, D, NO_STORE, fail, _json):
    P = "/api/kapul"

    def js(obj, status=200):
        return Response(json.dumps(obj, ensure_ascii=False), media_type="application/json", headers=NO_STORE, status_code=status)

    def uid_of(auth):
        return D.actor(auth)

    def admin_of(auth):
        uid = D.actor(auth)
        if not D.admin(uid):
            fail("Faqat administrator uchun", 403)
        return uid

    @app.get(P + "/holat")
    def holat(authorization: str | None = Header(None)):
        uid = uid_of(authorization)
        with D.ps.db() as cur:
            out = kapul.holat(cur, uid)
            out["tolov_yoqilgan"] = bool(kapul.sozlama(cur)["karta_raqam"])
        return js(out)

    @app.post(P + "/buyurtma")
    async def buyurtma(request: Request, authorization: str | None = Header(None)):
        uid = await run_in_threadpool(uid_of, authorization)
        body = await _json(request, 2048)

        def ish():
            with D.ps.db() as cur:
                try:
                    return buyurtma_och(cur, uid, (body or {}).get("kapul"))
                except (ValueError, TypeError) as e:
                    fail(str(e), 422)
        return js(await run_in_threadpool(ish))

    @app.get(P + "/buyurtma/{oid}")
    def buyurtma_holat(oid: str, authorization: str | None = Header(None)):
        uid = uid_of(authorization)
        with D.ps.db() as cur:
            muddati_otganlar(cur)
            r = buyurtma_korinish(cur, oid, uid)
        if not r:
            fail("Buyurtma topilmadi", 404)
        return js(r)

    @app.post(P + "/buyurtma/{oid}/bekor")
    def buyurtma_bekor(oid: str, authorization: str | None = Header(None)):
        uid = uid_of(authorization)
        with D.ps.db() as cur:
            cur.execute("UPDATE kapul_buyurtma SET holat='bekor' WHERE id=%s AND owner_id=%s AND holat='kutilmoqda'", (oid, uid))
        return js({"ok": True})

    @app.post(P + "/sms")
    async def sms(request: Request, x_kapul_kalit: str | None = Header(None)):
        """Telefondagi SMS-uzatgich ilova shu manzilga POST qiladi. Sarlavha: X-Kapul-Kalit; tana: JSON {text} yoki oddiy matn."""
        raw = (await request.body())[:8192]

        def ish():
            with D.ps.db() as cur:
                kalit = sms_kalit(cur)
                if not x_kapul_kalit or not hmac.compare_digest(x_kapul_kalit, kalit):
                    fail("Kalit noto'g'ri", 403)
                matn = ""
                try:
                    j = json.loads(raw.decode("utf-8", "replace"))
                    if isinstance(j, dict):
                        matn = str(j.get("text") or j.get("message") or j.get("body") or j.get("sms") or "")
                    elif isinstance(j, str):
                        matn = j
                except ValueError:
                    matn = raw.decode("utf-8", "replace")
                return sms_qabul(cur, matn)
        return js(await run_in_threadpool(ish))

    @app.get(P + "/admin")
    def admin(authorization: str | None = Header(None)):
        admin_of(authorization)
        with D.ps.db() as cur:
            return js(admin_holat(cur))

    @app.post(P + "/admin/sozlama")
    async def admin_sozlama(request: Request, authorization: str | None = Header(None)):
        await run_in_threadpool(admin_of, authorization)
        body = await _json(request, 4096)

        def ish():
            with D.ps.db() as cur:
                try:
                    return sozlama_saqla(cur, body if isinstance(body, dict) else {})
                except ValueError as e:
                    fail(str(e), 422)
        return js({"sozlama": await run_in_threadpool(ish)})

    @app.post(P + "/admin/qosh")
    async def admin_qosh(request: Request, authorization: str | None = Header(None)):
        admin_uid = await run_in_threadpool(admin_of, authorization)
        body = await _json(request, 2048) or {}

        def ish():
            try:
                uid, n = int(body.get("uid")), int(body.get("kapul"))
            except (TypeError, ValueError):
                fail("Foydalanuvchi raqami va kapul soni kerak", 422)
            if n == 0 or abs(n) > 100000:
                fail("Kapul soni noto'g'ri", 422)
            with D.ps.db() as cur:
                ref = "admin:" + uuid.uuid4().hex[:10]
                if n > 0:
                    b = kapul.qosh(cur, uid, n, "admin", ref)
                else:
                    b = kapul.yech(cur, uid, -n, "admin", ref)
                return {"balans": b, "admin": admin_uid}
        return js(await run_in_threadpool(ish))
