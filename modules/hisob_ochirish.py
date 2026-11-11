"""REV491: hisobni o'chirish (Google Play talabi). So'rov → barcha qurilmalardan chiqariladi → 7 kun ichida qayta kirib bekor qilish
mumkin → 7 kundan keyin shaxsiy ma'lumotlar o'chiriladi: kirish usullari (Telegram, Google, parol, telefon), sessiyalar, qurilma,
farzand bog'lanishlari, PIN, ko'nikmalar, avatar, kamera suratlari; profil «O‘chirilgan foydalanuvchi» bo'lib anonimlashtiriladi
(yozgan chat xabarlari va guruh natijalari muallifsiz qoladi — boshqa foydalanuvchilarning tarixi buzilmasin)."""
import json
import threading
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

KUTISH_KUN = 7
# user_id ustuni bo'yicha butunlay o'chiriladigan shaxsiy jadvallar (bo'lmasa — o'tkazib yuboriladi)
OCHIRILADI = [("kabutar_telegram_identity", "user_id"), ("google_hisob", "user_id"), ("kabutar_auth_password", "user_id"),
              ("kabutar_auth_sessions", "user_id"), ("kabutar_auth_security", "user_id"), ("user_accounts", "uid"), ("telefon_hisob", "user_id"),
              ("qurilma_bog", "user_id"), ("qurilma_almash", "user_id"), ("oila_pin", "owner_id"), ("konikma_holat", "user_id"),
              ("ekspeditsiya_profil", "user_id"), ("nazoratchi_qulf", "user_id"), ("nazoratchi_sorov", "user_id"), ("bildirishnomalar", "user_id"),
              ("parent_child", "parent_id"), ("parent_child", "child_id"), ("kurs_guruh_azo", "user_id"), ("haftalik_hisobot", "parent_id")]
_TAYYOR = {"ok": False}


def jadval(cur):
    if _TAYYOR["ok"]:
        return
    cur.execute("""CREATE TABLE IF NOT EXISTS hisob_ochirish (user_id BIGINT PRIMARY KEY, soralgan TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        bajariladi TIMESTAMPTZ NOT NULL, bajarildi TIMESTAMPTZ, sabab TEXT NOT NULL DEFAULT '')""")
    _TAYYOR["ok"] = True


def _bor(cur, t, c):
    cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND column_name=%s", (t, c))
    return cur.fetchone() is not None


def bajar(cur, uid):
    """Shaxsiy ma'lumotlarni o'chirish va profilni anonimlashtirish."""
    natija = {}
    try:   # kamera suratlari — ombordan ham
        from modules import ombor
        if _bor(cur, "kurs_nazorat_rasm", "s3_kalit"):
            cur.execute("SELECT s3_kalit FROM kurs_nazorat_rasm WHERE user_id=%s", (uid,))
            for r in cur.fetchall():
                try:
                    ombor.ochir(r["s3_kalit"])
                except Exception:   # noqa: BLE001
                    pass
            cur.execute("DELETE FROM kurs_nazorat_rasm WHERE user_id=%s", (uid,)); natija["kurs_nazorat_rasm"] = cur.rowcount
    except Exception:   # noqa: BLE001
        pass
    for t, c in OCHIRILADI:
        if _bor(cur, t, c):
            cur.execute(f'DELETE FROM "{t}" WHERE "{c}"=%s', (uid,)); natija[t] = natija.get(t, 0) + cur.rowcount
    sets = ["full_name='O‘chirilgan foydalanuvchi'"]
    for col, qiymat in (("profil_rasm", "NULL"), ("profil_rasm_turi", "NULL"), ("username", "NULL"), ("telefon", "NULL"), ("phone", "NULL"),
                        ("email", "NULL"), ("telegram_id", "NULL"), ("telegram_username", "NULL"), ("tugilgan_sana", "NULL")):
        if _bor(cur, "users", col):
            sets.append(f'"{col}"={qiymat}')
    cur.execute(f"UPDATE users SET {', '.join(sets)} WHERE user_id=%s", (uid,))
    cur.execute("UPDATE hisob_ochirish SET bajarildi=NOW() WHERE user_id=%s", (uid,))
    return natija


class Sorov(BaseModel):
    token: str = ""
    tasdiq: str
    sabab: str = ""


def create_router(platform):
    router = APIRouter(tags=["hisob_ochirish"])

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

    @router.get("/api/hisob/ochirish")
    def holat(token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        def f(cur):
            cur.execute("SELECT bajariladi FROM hisob_ochirish WHERE user_id=%s AND bajarildi IS NULL", (u,))
            r = cur.fetchone()
            return {"soralgan": bool(r), "bajariladi": r["bajariladi"].isoformat() if r else None}
        return run(f)

    @router.post("/api/hisob/ochirish")
    def sorov(body: Sorov, authorization: Optional[str] = Header(None)):
        u = uid(body.token, authorization)
        if body.tasdiq.strip().upper().replace("‘", "'").replace("’", "'") not in ("O'CHIRISH", "OCHIRISH", "DELETE", "УДАЛИТЬ"):
            raise HTTPException(400, "Tasdiqlash uchun «O‘CHIRISH» so‘zini yozing")
        def f(cur):
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (u,))
            if cur.fetchone():
                raise HTTPException(403, "Administrator hisobi bu yerdan o‘chirilmaydi")
            cur.execute("""INSERT INTO hisob_ochirish(user_id, bajariladi, sabab) VALUES(%s, NOW() + make_interval(days => %s), %s)
                           ON CONFLICT (user_id) DO UPDATE SET soralgan=NOW(), bajariladi=EXCLUDED.bajariladi, bajarildi=NULL, sabab=EXCLUDED.sabab
                           RETURNING bajariladi""", (u, KUTISH_KUN, body.sabab[:300]))
            b = cur.fetchone()["bajariladi"]
            if _bor(cur, "kabutar_auth_sessions", "user_id"):   # hamma qurilmadan chiqariladi
                cur.execute("DELETE FROM kabutar_auth_sessions WHERE user_id=%s", (u,))
            return {"ok": True, "bajariladi": b.isoformat(), "kun": KUTISH_KUN}
        return run(f)

    @router.post("/api/hisob/ochirish/bekor")
    def bekor(token: str = "", authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        def f(cur):
            cur.execute("DELETE FROM hisob_ochirish WHERE user_id=%s AND bajarildi IS NULL", (u,))
            return {"ok": True, "bekor": cur.rowcount > 0}
        return run(f)

    def ishchi():
        time.sleep(240)
        while True:
            try:
                conn = platform._db(); conn.autocommit = False; cur = conn.cursor()
                try:
                    jadval(cur); conn.commit()
                    cur.execute("SELECT pg_try_advisory_xact_lock(491491491) AS ok")
                    if cur.fetchone()["ok"]:
                        cur.execute("SELECT user_id FROM hisob_ochirish WHERE bajarildi IS NULL AND bajariladi < NOW() LIMIT 20")
                        for r in cur.fetchall():
                            n = bajar(cur, r["user_id"])
                            print(f"[hisob_ochirish] {r['user_id']}: {json.dumps(n)}", flush=True)
                    conn.commit()
                finally:
                    cur.close(); conn.close()
            except Exception as exc:   # noqa: BLE001
                print("[hisob_ochirish]", exc, flush=True)
            time.sleep(3600)

    @router.on_event("startup")
    def boshla():
        import sys as _s
        if "pytest" not in _s.modules:
            threading.Thread(target=ishchi, name="hisob-ochirish", daemon=True).start()

    return router
