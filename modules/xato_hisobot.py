"""REV501: sayt xatolari (bo'lim ochilmay qolishi — «Bu bo'limni ochib bo'lmadi») avtomatik serverga yoziladi: xato matni, qaysi
komponentda, versiya, sahifa, foydalanuvchi roli. Admin (yoki vaqtinchalik diagnostika kaliti) oxirgi xatolarni ko'radi.
Shaxsiy ma'lumot yozilmaydi; IP bo'yicha soatiga 30 tagacha; 30 kundan eskisi o'chiriladi."""
import os
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

_TAYYOR = {"ok": False}
_IP = {}


class Xato(BaseModel):
    xato: str = Field(default="", max_length=500)
    joy: str = Field(default="", max_length=400)
    url: str = Field(default="", max_length=300)
    versiya: str = Field(default="", max_length=20)
    rol: str = Field(default="", max_length=30)
    token: str = Field(default="", max_length=2000)


def create_router(platform):
    router = APIRouter(tags=["xato_hisobot"])

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            if not _TAYYOR["ok"]:
                cur.execute("""CREATE TABLE IF NOT EXISTS frontend_xato (id BIGSERIAL PRIMARY KEY, vaqt TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    user_id BIGINT, versiya TEXT, url TEXT, xato TEXT, joy TEXT, rol TEXT, ua TEXT)""")
                _TAYYOR["ok"] = True
            r = fn(cur); conn.commit(); return r
        finally:
            cur.close(); conn.close()

    @router.post("/api/frontend_xato")
    def yoz(body: Xato, request: Request, user_agent: Optional[str] = Header(None)):
        ip = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")).split(",")[0].strip()
        soat = int(time.time() // 3600)
        k = (ip, soat); _IP[k] = _IP.get(k, 0) + 1
        if _IP[k] > 30:
            return {"ok": False}
        if len(_IP) > 5000:
            _IP.clear()
        uid = None
        if body.token:
            try:
                uid = int(platform._jwt_tekshir(body.token))
            except Exception:   # noqa: BLE001
                uid = None
        def f(cur):
            cur.execute("INSERT INTO frontend_xato(user_id, versiya, url, xato, joy, rol, ua) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                        (uid, body.versiya, body.url.split("?")[0], body.xato, body.joy, body.rol, (user_agent or "")[:160]))
            cur.execute("DELETE FROM frontend_xato WHERE vaqt < NOW() - INTERVAL '30 days'")
            return {"ok": True}
        return run(f)

    @router.get("/api/admin/frontend_xato")
    def royxat(request: Request, token: str = "", limit: int = 50):
        diag = os.getenv("DIAG_KALIT", "")
        if not (len(diag) >= 24 and secrets.compare_digest(request.headers.get("x-diag-kalit", ""), diag)):
            uid = int(platform._jwt_tekshir(token))
            def adm(cur):
                cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (uid,)); return cur.fetchone() is not None
            if not run(adm):
                raise HTTPException(403, "Faqat admin")
        def f(cur):
            cur.execute("SELECT vaqt, user_id, versiya, url, xato, joy, rol, ua FROM frontend_xato ORDER BY id DESC LIMIT %s", (max(1, min(200, limit)),))
            return {"xatolar": [{**r, "vaqt": r["vaqt"].isoformat()} for r in cur.fetchall()]}
        return run(f)

    return router
