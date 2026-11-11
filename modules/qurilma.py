"""REV486: bitta obunali profil — bitta qurilma (telefon yoki noutbuk). Obunani bir necha kishi bo'lishib ishlatmasin.
- Har qurilma o'z maxfiy belgisini (qurilma kaliti, brauzer/ilova xotirasida) yuboradi; profil birinchi kirgan qurilmaga bog'lanadi.
- Boshqa qurilmadan kirilsa — ogohlantirish; tasdiqlansa profil yangi qurilmaga o'tadi, eskisida pullik darslar ochilmaydi.
- 30 kun ichida 2 marta almashtirish — bepul; keyingilari jarima: 3-chi → 1 soat, 4-chi → 7 soat, 5-chi → 1 kun,
  6-chi va undan ko'pi → 7 kun hech bir qurilmada pullik darslar ochilmaydi (eski qurilmada ham).
- Faqat obuna bilan ochiladigan darslar (sabab: obuna, bogcha_obuna) tekshiriladi; bepul darslar, admin va o'qituvchi — cheklovsiz."""
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

BEPUL_ALMASH = 2
JARIMA = [timedelta(hours=1), timedelta(hours=7), timedelta(days=1), timedelta(days=7)]
_TAYYOR = {"ok": False}
_KALIT = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def jarima(almash_soni):
    """30 kundagi almashtirishlar soni (shu almashtirish bilan) → qulf muddati yoki None."""
    if almash_soni <= BEPUL_ALMASH:
        return None
    return JARIMA[min(len(JARIMA) - 1, almash_soni - BEPUL_ALMASH - 1)]


def jadval(cur):
    if _TAYYOR["ok"]:
        return
    cur.execute("""CREATE TABLE IF NOT EXISTS qurilma_bog (user_id BIGINT PRIMARY KEY, qurilma TEXT NOT NULL, nomi TEXT NOT NULL DEFAULT '',
        boglandi TIMESTAMPTZ NOT NULL DEFAULT NOW(), qulf_gacha TIMESTAMPTZ)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS qurilma_almash (id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, eski TEXT, yangi TEXT,
        nomi TEXT NOT NULL DEFAULT '', vaqt TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    cur.execute("CREATE INDEX IF NOT EXISTS qurilma_almash_u ON qurilma_almash(user_id, vaqt DESC)")
    _TAYYOR["ok"] = True


def holat(cur, uid, qurilma):
    """→ {"holat": "ok"|"boshqa"|"qulf"|"yangi", "gacha"?, "nomi"?}"""
    jadval(cur)
    cur.execute("SELECT * FROM qurilma_bog WHERE user_id=%s", (uid,))
    b = cur.fetchone()
    now = datetime.now(timezone.utc)
    if b and b["qulf_gacha"] and b["qulf_gacha"] > now:
        return {"holat": "qulf", "gacha": b["qulf_gacha"].isoformat()}
    if not b:
        return {"holat": "yangi"}
    if b["qurilma"] == qurilma:
        return {"holat": "ok"}
    return {"holat": "boshqa", "nomi": b["nomi"]}


def bogla(cur, uid, qurilma, nomi=""):
    """Birinchi bog'lash yoki tasdiqlangan almashtirish. → holat (qulf bo'lsa — muddati bilan)."""
    jadval(cur)
    cur.execute("SELECT * FROM qurilma_bog WHERE user_id=%s FOR UPDATE", (uid,))
    b = cur.fetchone()
    now = datetime.now(timezone.utc)
    if not b:
        cur.execute("INSERT INTO qurilma_bog(user_id, qurilma, nomi) VALUES(%s,%s,%s) ON CONFLICT (user_id) DO NOTHING", (uid, qurilma, nomi[:80]))
        return {"holat": "ok", "birinchi": True}
    if b["qurilma"] == qurilma:
        return {"holat": "ok"}
    if b["qulf_gacha"] and b["qulf_gacha"] > now:
        return {"holat": "qulf", "gacha": b["qulf_gacha"].isoformat()}
    cur.execute("INSERT INTO qurilma_almash(user_id, eski, yangi, nomi) VALUES(%s,%s,%s,%s)", (uid, b["qurilma"], qurilma, nomi[:80]))
    cur.execute("SELECT COUNT(*) AS n FROM qurilma_almash WHERE user_id=%s AND vaqt > NOW() - INTERVAL '30 days'", (uid,))
    n = int(cur.fetchone()["n"])
    j = jarima(n)
    gacha = now + j if j else None
    cur.execute("UPDATE qurilma_bog SET qurilma=%s, nomi=%s, boglandi=NOW(), qulf_gacha=%s WHERE user_id=%s", (qurilma, nomi[:80], gacha, uid))
    try:   # egasiga xabar — kimdir parolni bilib kirsa, darhol bilsin
        cur.execute("SAVEPOINT qb")
        matn = f"🔐 Profilingiz yangi qurilmada ochildi ({nomi or 'noma’lum qurilma'}). Siz bo'lmasangiz — parolni almashtiring."
        if gacha:
            matn += f" 30 kunda {n}-marta almashtirildi — darslar vaqtincha yopildi."
        cur.execute("INSERT INTO bildirishnomalar(user_id, matn, turi) VALUES(%s,%s,'qurilma')", (uid, matn))
        cur.execute("RELEASE SAVEPOINT qb")
    except Exception:   # noqa: BLE001
        cur.execute("ROLLBACK TO SAVEPOINT qb")
    out = {"holat": "qulf" if gacha else "ok", "almash": n, "bepul": BEPUL_ALMASH}
    if gacha:
        out["gacha"] = gacha.isoformat()
    return out


def tekshir(cur, uid, qurilma):
    """Pullik dars ochishdan oldin. Ruxsat bo'lmasa — HTTP 423 (frontend qurilma oynasini ko'rsatadi)."""
    q = str(qurilma or "")
    if not _KALIT.match(q):
        raise HTTPException(423, detail={"kod": "qurilma", "holat": "yangi", "xabar": "Ilovani yangilang — qurilma tasdiqlanmagan"})
    h = holat(cur, uid, q)
    if h["holat"] == "yangi":
        bogla(cur, uid, q)
        return
    if h["holat"] != "ok":
        raise HTTPException(423, detail={"kod": "qurilma", **h})


class Bogla(BaseModel):
    token: str = ""
    qurilma: str
    nomi: str = ""


def create_router(platform):
    router = APIRouter(tags=["qurilma"])

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            jadval(cur); r = fn(cur); conn.commit(); return r
        finally:
            cur.close(); conn.close()

    @router.get("/api/qurilma/holat")
    def holat_ol(qurilma: str = "", token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        return run(lambda cur: {**holat(cur, u, qurilma), "bepul": BEPUL_ALMASH})

    @router.post("/api/qurilma/bogla")
    def bogla_api(body: Bogla, authorization: Optional[str] = Header(None)):
        """Foydalanuvchi «Shu qurilmaga o'tkazish»ni tasdiqladi (yoki birinchi kirish)."""
        u = uid(body.token, authorization)
        if not _KALIT.match(body.qurilma):
            raise HTTPException(400, "Qurilma kaliti noto'g'ri")
        return run(lambda cur: bogla(cur, u, body.qurilma, body.nomi))

    return router
