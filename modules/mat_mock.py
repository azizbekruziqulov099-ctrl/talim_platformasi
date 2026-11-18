"""Matematika MOCK: rasmiy imtihon tuzilmasi (45 topshiriq = 55 Rasch band), har bir urinish uchun noyob (seed) savollar, yechimli.

Savollar kod bilan generatsiya qilinadi (modules/mock_s*.py shablonlari) — javob va yechim ham hisoblanadi. Server har safar seeddan imtihonni qayta tiklaydi:
mijozga javoblar yuborilmaydi. Ball: 55 bandning haqiqiy qiyinligi (Rasch, 1271 talaba kalibrovkasi) bilan EAP, T-ball (o'rta 50, SD 10), 0–75. Taxminiy, rasmiy emas.
"""
import json
import math
import os
import random
from fractions import Fraction
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from modules import mock_lib, mock_s1, mock_s2, mock_s3, mock_s4  # noqa: F401  (shablonlarni ro'yxatga oladi)
from modules.mat_bank import baho_harfi

_R = json.load(open(os.path.join(os.path.dirname(__file__), "mat_mock_data", "rasch.json")))
B = _R["b"]
TH_MEAN, TH_SD = _R["theta_mean"], _R["theta_sd"]
DAQIQA = 150
assert len(B) == 55


def slot_bandlar(slot):
    """Slotning Rasch band indekslari (0-asosli)."""
    return [slot - 1] if slot <= 35 else [35 + 2 * (slot - 36), 36 + 2 * (slot - 36)]


def slot_tur(slot):
    return "yopiq" if slot <= 35 else "ochiq"


def imtihon_tuz(seed):
    """seed → 45 ta savol (slot tartibida). Bir imtihonda takror matn bo'lmaydi."""
    out, korildi = [], set()
    for slot in range(1, 46):
        for urinish in range(30):
            rng = random.Random(f"{seed}:{slot}:{urinish}")
            f = rng.choice(mock_lib.SHABLON[slot])
            q = f(rng)
            kalit = q["savol"] + "|".join(q.get("variantlar", []))
            if kalit not in korildi:
                korildi.add(kalit)
                break
        q = dict(q)
        q["slot"], q["mavzu"] = slot, f.nom
        q["bandlar"] = slot_bandlar(slot)
        out.append(q)
    return out


def ochiq_son(s):
    """Foydalanuvchi kiritgan javob → Fraction yoki None. '5,5', '-11/2', '1/2', '3' qabul qilinadi."""
    s = str(s or "").strip().replace(",", ".").replace(" ", "").replace("−", "-")
    if not s or len(s) > 20:
        return None
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        return None


def tekshir(savollar, javoblar):
    """javoblar: {"1":"B", "36a":"5,5", ...} → 55 ta natija (band bo'yicha) va savol bo'yicha tafsilot."""
    band_ok = [False] * 55
    tafsilot = []
    for q in savollar:
        s = q["slot"]
        if q["tur"] == "ochiq":
            qis = []
            for i, qq in enumerate(q["qismlar"]):
                kir = str(javoblar.get(f"{s}{qq['h']}", "")).strip()
                ok = ochiq_son(kir) is not None and ochiq_son(kir) == Fraction(qq["son"])
                band_ok[q["bandlar"][i]] = ok
                qis.append({"h": qq["h"], "savol": qq["savol"], "javob": qq["javob"], "kiritildi": kir, "togri": ok})
            tafsilot.append({"slot": s, "tur": "ochiq", "mavzu": q["mavzu"], "savol": q["savol"], "rasm": q.get("rasm"), "qismlar": qis, "yechim": q["yechim"], "togri": all(x["togri"] for x in qis)})
        else:
            tanl = str(javoblar.get(str(s), "")).strip().upper()[:1]
            ok = tanl == q["javob"]
            band_ok[q["bandlar"][0]] = ok
            tafsilot.append({"slot": s, "tur": "yopiq", "mavzu": q["mavzu"], "savol": q["savol"], "rasm": q.get("rasm"), "variantlar": q["variantlar"], "javob": q["javob"], "tanlandi": tanl,
                             "yechim": q["yechim"], "togri": ok})
    return band_ok, tafsilot


def eap(band_ok):
    """55 band, haqiqiy b lar; apriori N(theta_mean, theta_sd²)."""
    nuqta = [-5 + i * 0.05 for i in range(201)]
    w = []
    for th in nuqta:
        lp = -((th - TH_MEAN) ** 2) / (2 * TH_SD ** 2)
        for b, ok in zip(B, band_ok):
            p = 1 / (1 + math.exp(-(th - b)))
            lp += math.log(p if ok else 1 - p)
        w.append(lp)
    m = max(w)
    e = [math.exp(x - m) for x in w]
    return sum(t * x for t, x in zip(nuqta, e)) / sum(e)


def t_ball(theta):
    return round(max(0.0, min(75.0, 50.0 + 10.0 * (theta - TH_MEAN) / TH_SD)), 1)


def baholash(seed, javoblar):
    sav = imtihon_tuz(seed)
    band_ok, taf = tekshir(sav, javoblar)
    ball = t_ball(eap(band_ok))
    xom = sum(band_ok)
    zaif = sorted({t["mavzu"] for t in taf if not t["togri"]})
    return {"seed": seed, "xom": xom, "jami_band": 55, "togri_topshiriq": sum(1 for t in taf if t["togri"]), "jami_topshiriq": 45, "ball": ball, "daraja": baho_harfi(ball),
            "sertifikat": ball >= 46, "zaif": zaif, "natija": taf,
            "izoh": "Taxminiy ball (Rasch, haqiqiy band qiyinliklari bilan). Rasmiy natija emas."}


def ochiq_korinish(seed):
    """Mijozga: javob va yechimsiz."""
    out = []
    for q in imtihon_tuz(seed):
        if q["tur"] == "ochiq":
            out.append({"slot": q["slot"], "tur": "ochiq", "savol": q["savol"], "rasm": q.get("rasm"), "qismlar": [{"h": x["h"], "savol": x["savol"]} for x in q["qismlar"]]})
        else:
            out.append({"slot": q["slot"], "tur": "yopiq", "savol": q["savol"], "rasm": q.get("rasm"), "variantlar": q["variantlar"]})
    return out


class Topshir(BaseModel):
    token: Optional[str] = None
    seed: str = Field(max_length=40)
    javoblar: dict = Field(default_factory=dict)
    sekund: int = Field(default=0, ge=0, le=20000)


def create_router(platform):
    router = APIRouter(tags=["mat_mock"])
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
                cur.execute("""CREATE TABLE IF NOT EXISTS mat_mock_urinish (
                    id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, seed TEXT NOT NULL, ball REAL NOT NULL, xom INT NOT NULL, togri INT NOT NULL,
                    sekund INT NOT NULL DEFAULT 0, yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE(user_id, seed))""")
                cur.execute("CREATE INDEX IF NOT EXISTS mat_mock_urinish_u ON mat_mock_urinish(user_id, yaratildi DESC)")
                holat["tayyor"] = True
            r = fn(cur)
            conn.commit()
            return r
        finally:
            cur.close()
            conn.close()

    @router.get("/api/matmock/turlar")
    def turlar(token: str = None, authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)

        def f(cur):
            cur.execute("SELECT id, seed, ball, xom, togri, sekund, yaratildi FROM mat_mock_urinish WHERE user_id=%s ORDER BY yaratildi DESC LIMIT 30", (u,))
            return [{"id": int(r["id"]), "seed": r["seed"], "ball": float(r["ball"]), "xom": int(r["xom"]), "togri": int(r["togri"]), "daraja": baho_harfi(float(r["ball"])),
                     "sekund": int(r["sekund"]), "sana": r["yaratildi"].isoformat()} for r in cur.fetchall()]
        return {"daqiqa": DAQIQA, "topshiriq": 45, "tarix": run(f), "izoh": "Taxminiy ball (Rasch). 46 dan sertifikat. Rasmiy natija emas."}

    @router.get("/api/matmock/test")
    def test(token: str = None, seed: str = Query(None, max_length=40), authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        seed = seed or f"{u}-{random.SystemRandom().randrange(10 ** 9)}"
        if not all(c.isalnum() or c == "-" for c in seed):
            raise HTTPException(400, "seed noto'g'ri")
        return {"seed": seed, "daqiqa": DAQIQA, "savollar": ochiq_korinish(seed)}

    @router.post("/api/matmock/topshir")
    def topshir(body: Topshir, authorization: Optional[str] = Header(None)):
        u = uid(body.token, authorization)
        if not all(c.isalnum() or c == "-" for c in body.seed):
            raise HTTPException(400, "seed noto'g'ri")
        r = baholash(body.seed, {str(k): v for k, v in body.javoblar.items()})

        def f(cur):
            cur.execute("""INSERT INTO mat_mock_urinish(user_id, seed, ball, xom, togri, sekund) VALUES(%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (user_id, seed) DO NOTHING RETURNING id""", (u, body.seed, r["ball"], r["xom"], r["togri_topshiriq"], body.sekund))
            x = cur.fetchone()
            r["id"] = int(x["id"]) if x else None
            r["qayta"] = x is None   # shu seed avval topshirilgan: yechimlar ko'rsatiladi, lekin tarixga qayta yozilmaydi
        run(f)
        return r

    return router
