"""REV702: «So'z sandig'i» — so'z yodlash holati (Leitner qutilari) serverda. Faqat kichik natija saqlanadi:
har foydalanuvchi va til uchun bitta qator, ichida {kalit: [quti 1..5, qaytish kuni]}. Rasm, ovoz, matn saqlanmaydi.

  GET  /api/soz/holat?til=en           — foydalanuvchining shu tildagi holati
  POST /api/soz/holat {til, s}         — qurilmadagi holat bilan birlashtiriladi (ikki qurilma bir-birini o'chirmaydi)
  GET  /api/ota/bola_soz?bola_id=…     — ota-ona: farzandning tillar bo'yicha boshlagan / o'rgangan so'zlari
"""
import json
import re
import threading
from typing import Dict, List

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

try:
    from . import bogcha_reja as reja_mod
except ImportError:  # pragma: no cover
    from modules import bogcha_reja as reja_mod

try:
    from platform_core.ddl_guard import LazyMigration as _LazyMigration
except Exception:  # pragma: no cover
    _LazyMigration = None

TILLAR = ("en", "ru", "de", "fr", "es", "ar", "tr", "zh", "ja", "ko")
TIL_NOMI = {"en": "Ingliz", "ru": "Rus", "de": "Nemis", "fr": "Fransuz", "es": "Ispan", "ar": "Arab", "tr": "Turk", "zh": "Xitoy", "ja": "Yapon", "ko": "Koreys"}
KALIT_RE = re.compile(r"^[a-z0-9_]{1,48}$")
MAX_SOZ = 8000
ORGANILDI_QUTI = 3


def tozala(s):
    """Mijozdan kelgan holat: faqat to'g'ri kalitlar va [quti 1..5, kun] juftlari qoladi."""
    out = {}
    if not isinstance(s, dict):
        return out
    for k, v in s.items():
        if len(out) >= MAX_SOZ:
            break
        if not isinstance(k, str) or not KALIT_RE.match(k) or not isinstance(v, (list, tuple)) or len(v) != 2:
            continue
        try:
            quti, kun = int(v[0]), int(v[1])
        except (TypeError, ValueError):
            continue
        if 1 <= quti <= 5 and 0 <= kun <= 99999:
            out[k] = [quti, kun]
    return out


def birlashtir(eski, yangi):
    """Ikki qurilma holati: har so'z uchun keyinroq o'ynalgani (qaytish kuni kattasi; teng bo'lsa yuqori quti) qoladi."""
    out = dict(tozala(eski))
    for k, v in tozala(yangi).items():
        e = out.get(k)
        if e is None or (v[1], v[0]) > (e[1], e[0]):
            out[k] = v
    return out


def hisob(s):
    s = tozala(s)
    return {"boshlangan": len(s), "organilgan": sum(1 for v in s.values() if v[0] >= ORGANILDI_QUTI)}


def migrate(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS soz_sandiq_holat (
            user_id BIGINT NOT NULL,
            til TEXT NOT NULL,
            holat JSONB NOT NULL DEFAULT '{}'::jsonb,
            boshlangan INT NOT NULL DEFAULT 0,
            organilgan INT NOT NULL DEFAULT 0,
            yangilangan TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, til)
        )""")


class HolatBody(BaseModel):
    til: str
    s: Dict[str, List[int]] = {}


def create_router(platform):
    router = APIRouter()
    ready = {"ok": False}
    lock = threading.Lock()
    lazy = _LazyMigration("soz_sandiq") if _LazyMigration else None

    def uid_of(token, authorization):
        return int(platform._jwt_tekshir(platform._jwt_header_yoki_query(token, authorization)))

    def run_db(fn):
        conn = platform._db()
        cur = conn.cursor()
        try:
            if not ready["ok"]:
                if lazy is not None:   # muvaffaqiyatsiz migratsiya serverni qotirmaydi
                    lazy.run(conn, cur, migrate)
                    ready["ok"] = lazy.ok
                else:
                    with lock:
                        if not ready["ok"]:
                            migrate(cur)
                            conn.commit()
                            ready["ok"] = True
            return fn(conn, cur)
        finally:
            cur.close()
            conn.close()

    def oqi(cur, user_id, til):
        cur.execute("SELECT holat FROM soz_sandiq_holat WHERE user_id=%s AND til=%s", (user_id, til))
        r = cur.fetchone()
        h = (r["holat"] if r else {}) or {}
        if isinstance(h, str):
            try:
                h = json.loads(h)
            except ValueError:
                h = {}
        return h

    @router.get("/api/soz/holat")
    def holat_ol(til: str, token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        if til not in TILLAR:
            raise HTTPException(400, "Noma'lum til")
        return run_db(lambda conn, cur: {"til": til, "s": tozala(oqi(cur, user_id, til))})

    @router.post("/api/soz/holat")
    def holat_yoz(body: HolatBody, token: str = None, authorization: str = Header(None)):
        user_id = uid_of(token, authorization)
        if body.til not in TILLAR:
            raise HTTPException(400, "Noma'lum til")

        def run(conn, cur):
            s = birlashtir(oqi(cur, user_id, body.til), body.s)
            h = hisob(s)
            cur.execute("""INSERT INTO soz_sandiq_holat (user_id, til, holat, boshlangan, organilgan, yangilangan)
                           VALUES (%s, %s, %s::jsonb, %s, %s, now())
                           ON CONFLICT (user_id, til) DO UPDATE SET holat=EXCLUDED.holat, boshlangan=EXCLUDED.boshlangan,
                               organilgan=EXCLUDED.organilgan, yangilangan=now()""",
                        (user_id, body.til, json.dumps(s, separators=(",", ":")), h["boshlangan"], h["organilgan"]))
            conn.commit()
            return {"til": body.til, "s": s, **h}
        return run_db(run)

    @router.get("/api/ota/bola_soz")
    def bola_soz(bola_id: int, token: str = None, authorization: str = Header(None)):
        parent_id = uid_of(token, authorization)

        def run(conn, cur):
            if not (reja_mod.ota_bolami(cur, parent_id, bola_id) or reja_mod.adminmi(cur, parent_id)):
                raise HTTPException(403, "Bu farzand sizga ulanmagan")
            cur.execute("SELECT til, boshlangan, organilgan, yangilangan FROM soz_sandiq_holat WHERE user_id=%s ORDER BY organilgan DESC, boshlangan DESC", (bola_id,))
            return {"tillar": [{"til": r["til"], "nom": TIL_NOMI.get(r["til"], r["til"]), "boshlangan": r["boshlangan"], "organilgan": r["organilgan"],
                                "yangilangan": r["yangilangan"].isoformat() if r["yangilangan"] else None} for r in cur.fetchall()]}
        return run_db(run)

    return router
