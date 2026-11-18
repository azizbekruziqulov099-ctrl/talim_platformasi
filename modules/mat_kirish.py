"""Matematika: OLIY TA'LIMGA KIRISH uslubidagi 30 talik imtihon (o'z test bankimizdan).

Tuzilma: jami 40 ta savol — 10 ta oddiy (har biri 1,1 ball) + alohida 30 ta savol talaba tanlagan daraja bo'yicha: hammasi 2,1 yoki hammasi 3,1 ball.
Qiyinlik darajasi (1,1 / 2,1 / 3,1): bankdagi O/R/Q belgisidan; belgisiz (R) savollar matn murakkabligi (uzunlik, formulalar) bo'yicha ajratiladi.
"""
import random
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from modules.mat_bank import HARFLAR
from modules.mat_sertifikat import _norm, pool_ol, zaif_mavzular

BALL = {1: 1.1, 2: 2.1, 3: 3.1}
def maks(d):
    return round(10 * BALL[1] + 30 * BALL[d], 1)
SONI = {1: 10, "tanlov": 20}
_kesh = {"d": None}


def darajalar():
    """{id: 1|2|3} — savol darajasi. O → 1; Q → 3; qolgan (R) lar murakkablik bo'yicha: pastki 30% → 1, o'rta 40% → 2, yuqori 30% → 3."""
    if _kesh["d"] is None:
        pool = pool_ol()
        d, r = {}, []
        for sid, v in pool.items():
            q = v["t"].get("qiyinlik") or "R"
            if q == "O":
                d[sid] = 1
            elif q == "Q":
                d[sid] = 3
            else:
                t = v["t"]
                r.append((len(t["savol"]) + 4 * t["savol"].count("\\") + sum(len(x) for x in t["variantlar"]) / 4 + 3 * sum(x.count("\\") for x in t["variantlar"]), sid))
        r.sort()
        n = len(r)
        for i, (_, sid) in enumerate(r):
            d[sid] = 1 if i < 0.3 * n else (2 if i < 0.7 * n else 3)
        _kesh["d"] = d
    return _kesh["d"]


def tuz(daraja, rng):
    pool, d = pool_ol(), darajalar()
    out, korildi = [], set()
    for lv, n in ((1, 10), (daraja, 30)):
        nomzod = [sid for sid, x in d.items() if x == lv]
        rng.shuffle(nomzod)
        k = 0
        for sid in nomzod:
            t = pool[sid]["t"]
            kal = _norm(t["savol"]) + "|" + "|".join(_norm(x) for x in t["variantlar"])
            if kal in korildi:
                continue
            korildi.add(kal)
            out.append((sid, lv)); k += 1
            if k == n:
                break
        if k < n:
            raise ValueError("savol yetmadi")
    return out


class Topshir(BaseModel):
    token: Optional[str] = None
    daraja: int = Field(default=2, ge=2, le=3)
    idlar: list = Field(default_factory=list)
    javoblar: dict = Field(default_factory=dict)
    sekund: int = Field(default=0, ge=0, le=20000)


def create_router(platform):
    router = APIRouter(tags=["mat_kirish"])
    holat = {"tayyor": False}

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def run(fn):
        conn = platform._db()
        cur = conn.cursor()
        try:
            if not holat["tayyor"]:
                cur.execute("""CREATE TABLE IF NOT EXISTS mat_kirish_urinish (
                    id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, daraja INT NOT NULL, ball REAL NOT NULL, maks REAL NOT NULL, togri INT NOT NULL,
                    sekund INT NOT NULL DEFAULT 0, yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
                cur.execute("CREATE INDEX IF NOT EXISTS mat_kirish_urinish_u ON mat_kirish_urinish(user_id, yaratildi DESC)")
                holat["tayyor"] = True
            r = fn(cur)
            conn.commit()
            return r
        finally:
            cur.close()
            conn.close()

    @router.get("/api/matkirish/info")
    def info(token: str = None, authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        d = darajalar()
        son = {k: sum(1 for x in d.values() if x == k) for k in (1, 2, 3)}

        def f(cur):
            cur.execute("SELECT id, daraja, ball, maks, togri, yaratildi FROM mat_kirish_urinish WHERE user_id=%s ORDER BY yaratildi DESC LIMIT 20", (u,))
            return [{"id": int(r["id"]), "daraja": int(r["daraja"]), "ball": float(r["ball"]), "maks": float(r["maks"]), "togri": int(r["togri"]), "sana": r["yaratildi"].isoformat()} for r in cur.fetchall()]
        return {"soni": 40, "daqiqa": 90, "ball": BALL, "maks": {2: maks(2), 3: maks(3)}, "bank": son, "tarix": run(f),
                "izoh": "Jami 40 ta savol: birinchi 10 tasi oddiy (1,1 ball), keyingi 30 tasi uchun 2,1 yoki 3,1 darajani o‘zingiz tanlaysiz."}

    @router.get("/api/matkirish/test")
    def test(token: str = None, daraja: int = Query(2, ge=2, le=3), authorization: Optional[str] = Header(None)):
        uid(token, authorization)
        try:
            sav = tuz(daraja, random.Random())
        except ValueError as e:
            raise HTTPException(503, str(e))
        pool = pool_ol()
        return {"daraja": daraja, "daqiqa": 90, "soni": len(sav), "maks": maks(daraja),
                "savollar": [{"id": sid, "ball": BALL[lv], "savol": pool[sid]["t"]["savol"], "variantlar": pool[sid]["t"]["variantlar"]} for sid, lv in sav]}

    @router.post("/api/matkirish/topshir")
    def topshir(body: Topshir, authorization: Optional[str] = Header(None)):
        u = uid(body.token, authorization)
        pool, d = pool_ol(), darajalar()
        idlar = [str(x) for x in body.idlar]
        lv = [d.get(x) for x in idlar]
        if len(idlar) != 40 or len(set(idlar)) != 40 or any(x not in pool for x in idlar) or lv != [1] * 10 + [body.daraja] * 30:
            raise HTTPException(400, "Savollar ro'yxati noto'g'ri")
        natija, ball = [], 0.0
        for sid, l in zip(idlar, lv):
            v = pool[sid]
            h = str(body.javoblar.get(sid) or "").strip().upper()[:1]
            ok = h in HARFLAR and h == v["t"]["javob"]
            ball += BALL[l] if ok else 0
            natija.append({"id": sid, "ball": BALL[l], "togri": ok, "javob": v["t"]["javob"], "tanlandi": h if h in HARFLAR else "", "mavzu": v["mavzu"], "yechim": v["t"].get("yechim") or None})
        mk = maks(body.daraja)
        r = {"daraja": body.daraja, "ball": round(ball, 1), "maks": mk, "foiz": round(100 * ball / mk), "togri": sum(1 for x in natija if x["togri"]), "jami": 40,
             "oddiy_togri": sum(1 for x in natija[:10] if x["togri"]), "tanlov_togri": sum(1 for x in natija[10:] if x["togri"]), "natija": natija, "tavsiya": zaif_mavzular(natija)}

        def f(cur):
            cur.execute("INSERT INTO mat_kirish_urinish(user_id, daraja, ball, maks, togri, sekund) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id", (u, body.daraja, r["ball"], mk, r["togri"], body.sekund))
            r["id"] = int(cur.fetchone()["id"])
            for x in natija:
                if not x["tanlandi"]:
                    continue
                cur.execute("""INSERT INTO mat_bank_javob(user_id, savol_id, mavzu, urinish, togri, oxirgi_togri, oxirgi_harf) VALUES(%s,%s,%s,1,%s,%s,%s)
                               ON CONFLICT (user_id, savol_id) DO UPDATE SET urinish=mat_bank_javob.urinish+1, togri=mat_bank_javob.togri+EXCLUDED.togri,
                                 oxirgi_togri=EXCLUDED.oxirgi_togri, oxirgi_harf=EXCLUDED.oxirgi_harf, yangilangan=NOW()""",
                            (u, x["id"], x["mavzu"], int(x["togri"]), x["togri"], x["tanlandi"]))
        run(f)
        return r

    return router
