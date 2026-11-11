"""REV489: ota-ona PIN-kodi (4 raqam). Bola profilidan ota-ona profiliga qaytish, chiqish va profillarni boshqarish — faqat PIN bilan.
PIN tuzli PBKDF2 xesh bilan saqlanadi (o'zi hech qayerda yo'q); 5 marta xato — 10 daqiqa kutish."""
import hashlib
import hmac
import os
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

_TAYYOR = {"ok": False}


def _xesh(pin, tuz):
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), tuz, 120_000).hex()


def jadval(cur):
    if _TAYYOR["ok"]:
        return
    cur.execute("""CREATE TABLE IF NOT EXISTS oila_pin (owner_id BIGINT PRIMARY KEY, xesh TEXT NOT NULL, tuz TEXT NOT NULL,
        xato INT NOT NULL DEFAULT 0, qulf_gacha TIMESTAMPTZ, yangilandi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
    _TAYYOR["ok"] = True


def togri(cur, owner, pin):
    """→ (ok, xabar). Xatolar sanaladi, 5 tadan keyin 10 daqiqa qulf."""
    cur.execute("SELECT *, qulf_gacha > NOW() AS qulf FROM oila_pin WHERE owner_id=%s FOR UPDATE", (owner,))
    r = cur.fetchone()
    if not r:
        return True, ""
    if r["qulf"]:
        return False, "Ko‘p marta xato kiritildi — 10 daqiqadan keyin urinib ko‘ring"
    if hmac.compare_digest(_xesh(str(pin), bytes.fromhex(r["tuz"])), r["xesh"]):
        cur.execute("UPDATE oila_pin SET xato=0, qulf_gacha=NULL WHERE owner_id=%s", (owner,))
        return True, ""
    xato = r["xato"] + 1
    if xato >= 5:
        cur.execute("UPDATE oila_pin SET xato=0, qulf_gacha=NOW() + INTERVAL '10 minutes' WHERE owner_id=%s", (owner,))
        return False, "Ko‘p marta xato kiritildi — 10 daqiqadan keyin urinib ko‘ring"
    cur.execute("UPDATE oila_pin SET xato=%s WHERE owner_id=%s", (xato, owner))
    return False, f"PIN noto‘g‘ri ({5 - xato} ta urinish qoldi)"


class PinOrnat(BaseModel):
    token: str = ""
    pin: str = Field(..., pattern=r"^\d{4}$")
    eski_pin: Optional[str] = None


class PinTekshir(BaseModel):
    token: str = ""
    pin: str = Field(..., pattern=r"^\d{4}$")


def create_router(platform):
    router = APIRouter(tags=["oila_pin"])

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

    @router.get("/api/oila/pin")
    def bormi(token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        def f(cur):
            cur.execute("SELECT 1 FROM oila_pin WHERE owner_id=%s", (u,))
            return {"bor": cur.fetchone() is not None}
        return run(f)

    @router.post("/api/oila/pin")
    def ornat(body: PinOrnat, authorization: Optional[str] = Header(None)):
        """O'rnatish yoki almashtirish (almashtirishda eski PIN kerak)."""
        u = uid(body.token, authorization)
        def tek(cur):
            cur.execute("SELECT 1 FROM oila_pin WHERE owner_id=%s", (u,))
            return togri(cur, u, body.eski_pin or "") if cur.fetchone() else (True, "")
        ok, xabar = run(tek)
        if not ok:
            raise HTTPException(403, xabar or "Eski PIN noto‘g‘ri")
        def f(cur):
            tuz = os.urandom(16)
            cur.execute("""INSERT INTO oila_pin(owner_id, xesh, tuz) VALUES(%s,%s,%s)
                           ON CONFLICT (owner_id) DO UPDATE SET xesh=EXCLUDED.xesh, tuz=EXCLUDED.tuz, xato=0, qulf_gacha=NULL, yangilandi=NOW()""",
                        (u, _xesh(body.pin, tuz), tuz.hex()))
            return {"ok": True}
        return run(f)

    @router.post("/api/oila/pin/tekshir")
    def tekshir(body: PinTekshir, authorization: Optional[str] = Header(None)):
        u = uid(body.token, authorization)
        ok, xabar = run(lambda cur: togri(cur, u, body.pin))   # xato soni avval saqlanadi (commit), keyin javob
        if not ok:
            raise HTTPException(403, xabar)
        return {"ok": True}

    return router
