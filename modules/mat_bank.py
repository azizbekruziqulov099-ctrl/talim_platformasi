"""REV558: Matematika banki («Tematika», 1996–2003) — mavzular, qoidalar, misollar va 5 variantli testlar.

Bank modules/mat_bank_data/tematika.json (tools/mat_bank/oqi.py Word fayllardan yasaydi). Formulalar LaTeX ($…$, $$…$$) — saytda KaTeX chizadi.
Mavjud generated_tests jadvali 4 variantli, bank esa 5 variantli (A–E) — shuning uchun bank ALOHIDA, o'z manzillari va jadvali bilan.

  GET  /api/matbank/mavzular            — mavzular ro'yxati (raqam, nom, kitob bo'limi, testlar soni)
  GET  /api/matbank/mavzu/{raqam}       — qoida va ishlangan misollar + o'quvchining shu mavzudagi natijasi
  GET  /api/matbank/test                — test (javobsiz): ?mavzu=31,32 &soni=10 &qiyinlik=O|R|Q (qiyinlik GPT qo'shgach)
  POST /api/matbank/tekshir             — javoblarni tekshiradi; to'g'ri javob va yechim TEST OXIRIDA qaytadi; tarix yoziladi
  GET  /api/matbank/mening              — mavzular bo'yicha o'quvchi natijasi (keyin «pasport» shuni o'qiydi)
Tanlash qoidasi (o'rganish uchun): avval hali ko'rilmagan savollar, keyin xato qilinganlari, oxirida to'g'ri yechilganlar (eskisi avval).
"""
import json
import os
import random
import re
import threading
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

BANK_FAYL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mat_bank_data", "tematika.json")
HARFLAR = "ABCDE"
SONI_ENG_KOP = 40
QIYINLIK = {"O": "oson", "R": "o'rta", "Q": "qiyin"}

_kesh = {"bank": None}
_qulf = threading.Lock()


class Bank:
    def __init__(self, data):
        self.manba = data.get("manba", "")
        self.mavzular = {int(m["raqam"]): m for m in data["mavzular"]}
        self.savol = {}
        for m in data["mavzular"]:
            for t in m["testlar"]:
                self.savol[t["id"]] = dict(t, mavzu=int(m["raqam"]))

    def ommaviy(self, t):
        """Savol o'quvchiga — JAVOBSIZ."""
        return {"id": t["id"], "mavzu": t["mavzu"], "manba": t["manba"], "savol": t["savol"], "variantlar": t["variantlar"], "qiyinlik": t.get("qiyinlik") or None}


def bank_ol():
    if _kesh["bank"] is None:
        with _qulf:
            if _kesh["bank"] is None:
                with open(BANK_FAYL, encoding="utf-8") as f:
                    _kesh["bank"] = Bank(json.load(f))
    return _kesh["bank"]


def _norm(s):
    return re.sub(r"\s+", "", s or "")


def tanla(bank, mavzular, soni, tarix, rng, qiyinlik=None):
    """Test uchun savollar. tarix: {savol_id: (urinish, oxirgi_togri, yangilangan)}. → [savol, …] (takror matnli savol bir marta)."""
    ichida = set(mavzular) if mavzular else set(bank.mavzular)
    nomzod = []
    for t in bank.savol.values():
        if t["mavzu"] not in ichida:
            continue
        if qiyinlik and (t.get("qiyinlik") or "") != qiyinlik:
            continue
        h = tarix.get(t["id"])
        guruh = 0 if not h or not h[0] else (1 if not h[1] else 2)
        eskilik = str(h[2]) if h and h[2] else ""
        nomzod.append((guruh, eskilik if guruh == 2 else "", rng.random(), t))
    nomzod.sort(key=lambda x: (x[0], x[1], x[2]))
    out, korildi = [], set()
    for _, _, _, t in nomzod:
        k = _norm(t["savol"]) + "|" + "|".join(_norm(v) for v in t["variantlar"])
        if k in korildi:
            continue
        korildi.add(k)
        out.append(t)
        if len(out) >= soni:
            break
    rng.shuffle(out)
    return out


def baholash(bank, javoblar):
    """javoblar: {savol_id: harf}. → {"natija": [{id, togri, javob, tanlandi}], "togri", "jami", "foiz"}. Noma'lum id va noto'g'ri harf — xato."""
    natija, togri = [], 0
    for sid, h in javoblar.items():
        t = bank.savol.get(sid)
        if not t:
            raise ValueError(f"noma'lum savol: {sid}")
        h = str(h or "").strip().upper()[:1]
        ok = bool(h) and h in HARFLAR and h == t["javob"]
        togri += int(ok)
        natija.append({"id": sid, "togri": ok, "javob": t["javob"], "tanlandi": h if h in HARFLAR else "", "yechim": t.get("yechim") or None})
    jami = len(natija)
    return {"natija": natija, "togri": togri, "jami": jami, "foiz": round(100 * togri / jami) if jami else 0}


class Tekshir(BaseModel):
    token: Optional[str] = None
    javoblar: dict = Field(default_factory=dict)


def create_router(platform):
    router = APIRouter(tags=["mat_bank"])
    holat = {"tayyor": False}

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def jadval(cur):
        if holat["tayyor"]:
            return
        cur.execute("""CREATE TABLE IF NOT EXISTS mat_bank_javob (
            user_id BIGINT NOT NULL, savol_id TEXT NOT NULL, mavzu INT NOT NULL, urinish INT NOT NULL DEFAULT 0, togri INT NOT NULL DEFAULT 0,
            oxirgi_togri BOOLEAN NOT NULL DEFAULT FALSE, oxirgi_harf TEXT NOT NULL DEFAULT '', birinchi TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            yangilangan TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY (user_id, savol_id))""")
        cur.execute("CREATE INDEX IF NOT EXISTS mat_bank_javob_mavzu ON mat_bank_javob(user_id, mavzu)")
        holat["tayyor"] = True

    def run(fn):
        conn = platform._db()
        cur = conn.cursor()
        try:
            jadval(cur)
            r = fn(cur)
            conn.commit()
            return r
        finally:
            cur.close()
            conn.close()

    def tarix_ol(cur, user_id, mavzular=None):
        if mavzular:
            cur.execute("SELECT savol_id, urinish, oxirgi_togri, yangilangan FROM mat_bank_javob WHERE user_id=%s AND mavzu = ANY(%s)", (user_id, list(mavzular)))
        else:
            cur.execute("SELECT savol_id, urinish, oxirgi_togri, yangilangan FROM mat_bank_javob WHERE user_id=%s", (user_id,))
        return {r["savol_id"]: (int(r["urinish"]), bool(r["oxirgi_togri"]), r["yangilangan"]) for r in cur.fetchall()}

    @router.get("/api/matbank/mavzular")
    def mavzular(token: str = None, authorization: Optional[str] = Header(None)):
        uid(token, authorization)
        b = bank_ol()
        return {"manba": b.manba, "mavzular": [{"raqam": r, "nom": m["nom"], "kitob": m["kitob"], "testlar": len(m["testlar"]), "misol": len(m["namunalar"])}
                                              for r, m in sorted(b.mavzular.items())]}

    @router.get("/api/matbank/mavzu/{raqam}")
    def mavzu(raqam: int, token: str = None, authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        m = bank_ol().mavzular.get(raqam)
        if not m:
            raise HTTPException(404, "Mavzu topilmadi")

        def f(cur):
            cur.execute("SELECT COUNT(*) AS ko, COALESCE(SUM(togri),0) AS tg, COALESCE(SUM(oxirgi_togri::int),0) AS ox FROM mat_bank_javob WHERE user_id=%s AND mavzu=%s", (u, raqam))
            r = cur.fetchone() or {}
            return {"ko_rilgan": int(r.get("ko") or 0), "oxirgi_togri": int(r.get("ox") or 0)}
        return {"raqam": raqam, "nom": m["nom"], "kitob": m["kitob"], "qoida": m["qoida"], "namunalar": m["namunalar"], "testlar": len(m["testlar"]), "meniki": run(f)}

    @router.get("/api/matbank/test")
    def test(token: str = None, mavzu: str = Query("", max_length=200), soni: int = Query(10, ge=1, le=SONI_ENG_KOP),
             qiyinlik: str = Query("", max_length=1), authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        b = bank_ol()
        try:
            ml = [int(x) for x in re.split(r"[,\s]+", mavzu.strip()) if x]
        except ValueError:
            raise HTTPException(400, "Mavzu raqamlari noto'g'ri")
        if any(x not in b.mavzular for x in ml):
            raise HTTPException(404, "Mavzu topilmadi")
        if qiyinlik and qiyinlik not in QIYINLIK:
            raise HTTPException(400, "Qiyinlik: O, R yoki Q")
        tarix = run(lambda cur: tarix_ol(cur, u, ml or None))
        sav = tanla(b, ml, soni, tarix, random.Random(), qiyinlik or None)
        if not sav:
            raise HTTPException(404, "Bu mavzuda savol topilmadi")
        return {"soni": len(sav), "savollar": [b.ommaviy(t) for t in sav]}

    @router.post("/api/matbank/tekshir")
    def tekshir(body: Tekshir, authorization: Optional[str] = Header(None)):
        u = uid(body.token, authorization)
        if not body.javoblar or len(body.javoblar) > 60:
            raise HTTPException(400, "Javoblar soni 1–60 bo'lishi kerak")
        b = bank_ol()
        try:
            r = baholash(b, {str(k): v for k, v in body.javoblar.items()})
        except ValueError as e:
            raise HTTPException(400, str(e))

        def f(cur):
            for x in r["natija"]:
                if not x["tanlandi"]:
                    continue    # javob bermagan savol tarixga yozilmaydi
                cur.execute("""INSERT INTO mat_bank_javob(user_id, savol_id, mavzu, urinish, togri, oxirgi_togri, oxirgi_harf) VALUES(%s,%s,%s,1,%s,%s,%s)
                               ON CONFLICT (user_id, savol_id) DO UPDATE SET urinish=mat_bank_javob.urinish+1, togri=mat_bank_javob.togri+EXCLUDED.togri,
                                 oxirgi_togri=EXCLUDED.oxirgi_togri, oxirgi_harf=EXCLUDED.oxirgi_harf, yangilangan=NOW()""",
                            (u, x["id"], b.savol[x["id"]]["mavzu"], int(x["togri"]), x["togri"], x["tanlandi"]))
        run(f)
        return r

    @router.get("/api/matbank/mening")
    def mening(token: str = None, authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        b = bank_ol()

        def f(cur):
            cur.execute("""SELECT mavzu, COUNT(*) AS ko, SUM(oxirgi_togri::int) AS ox, SUM(urinish) AS ur, SUM(togri) AS tg, MAX(yangilangan) AS oxirgi
                           FROM mat_bank_javob WHERE user_id=%s GROUP BY mavzu ORDER BY mavzu""", (u,))
            return [{"mavzu": int(r["mavzu"]), "nom": b.mavzular[int(r["mavzu"])]["nom"] if int(r["mavzu"]) in b.mavzular else "", "jami": len(b.mavzular[int(r["mavzu"])]["testlar"]) if int(r["mavzu"]) in b.mavzular else 0,
                     "ko_rilgan": int(r["ko"]), "oxirgi_togri": int(r["ox"] or 0), "urinish": int(r["ur"] or 0), "togri": int(r["tg"] or 0),
                     "oxirgi": r["oxirgi"].isoformat() if r["oxirgi"] else None} for r in cur.fetchall()]
        return {"mavzular": run(f)}

    return router
