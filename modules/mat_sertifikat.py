"""Matematika: Milliy sertifikat uslubidagi KIRISH testi va TO'LIQ sinov — Rasch (EAP) bilan taxminiy ball.

Rasmiy format (infoedu.uz, Bilim va malakalarni baholash agentligi spetsifikatsiyasi): 45 topshiriq, 150 daqiqa; ball Rasch modeli bilan,
sertifikat 46 balldan; A+ 70+, A 65–69,9, B+ 60–64,9, B 55–59,9, C+ 50–54,9, C 46–49,9. Bizda test FOIZ emas — qiyinlik hisobga olinadi,
lekin savollar o'zimizniki (Tematika va Repetitor banklari) va qiyinlik taxminiy (O/R/Q belgisi + o'quvchilar javobidan), shuning uchun
natija «taxminiy ball» — rasmiy emas.

Ikki rejim: «kirish» — 20 savol, 40 daqiqa, daraja va zaif mavzularni aniqlaydi (Repetitor mavzulariga yo'naltiradi);
«toliq» — rasmiy tarkib 45 savol, 150 daqiqa.
"""
import math
import random
import re
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from modules.mat_bank import HARFLAR, REPETITOR_BOSHI, baho_harfi, bank_ol, rep_bank_ol

# Rasmiy spetsifikatsiya bo'limlari (45 topshiriq); moslashtirish topshiriqlari geometriyaga qo'shilgan.
BOLIMLAR = {
    "sonlar": "Sonlar va amallar",
    "algebra": "Algebraik almashtirishlar",
    "tenglama": "Tenglama va tengsizliklar",
    "tahlil": "Matematik tahlil asoslari",
    "funksiya": "Funksiyalar",
    "toplam": "To'plam, mantiq, statistika, ehtimollik",
    "geometriya": "Geometriya",
}
TUZILMA = {"toliq": {"nom": "To'liq sinov", "savol": 45, "daqiqa": 150,
                     "bolim": {"sonlar": 2, "algebra": 11, "tenglama": 8, "tahlil": 4, "funksiya": 3, "toplam": 3, "geometriya": 14}},
           "kirish": {"nom": "Kirish testi", "savol": 20, "daqiqa": 40,
                      "bolim": {"sonlar": 1, "algebra": 5, "tenglama": 4, "tahlil": 2, "funksiya": 1, "toplam": 1, "geometriya": 6}}}
assert all(sum(v["bolim"].values()) == v["savol"] for v in TUZILMA.values())

_KALIT = [  # (bo'lim, mavzu nomidagi kalit so'zlar) — tartib muhim
    ("geometriya", ("uchburchak", "to'rtburchak", "ko'pburchak", "doira", "aylana", "burchak", "yuz", "perimetr", "hajm", "prizma", "piramida", "shar", "silindr", "konus",
                    "vektor", "koordinata", "planimetriya", "stereometriya", "kesuvchi", "urinma", "parallel", "tekislik", "fazo", "trapetsiya", "romb", "kvadrat yuz", "geometrik")),
    ("tahlil", ("hosila", "integral", "limit", "progressiya", "ketma-ketlik", "urinma", "ekstremum")),
    ("funksiya", ("funksiya", "grafik", "juft", "toq funksiya", "aniqlanish", "qiymatlar sohasi")),
    ("toplam", ("to'plam", "mantiq", "kombinator", "ehtimol", "statistika", "ma'lumot", "permutatsiya", "o'rin almashtirish", "guruhlash")),
    ("tenglama", ("tenglama", "tengsizlik", "sistema", "oraliqlar", "modul")),
    ("sonlar", ("natural son", "butun son", "oddiy kasr", "o'nli kasr", "bo'linish", "ildiz", "foiz", "prosent", "proporsiya", "boshlang'ich", "amal", "hisoblash", "son", "o'qilishi", "ekub", "ekuk", "nisbat")),
]


def bolim_of(nom, kitob=None):
    n = (nom or "").lower().replace("’", "'").replace("‘", "'")
    for b, kalitlar in _KALIT:
        if any(k in n for k in kalitlar):
            return b
    if kitob and str(kitob).startswith(("3.", "4.")):
        return "geometriya"
    return "algebra"


QIYIN_LOGIT = {"O": -1.0, "R": 0.0, "Q": 1.0}
_kesh = {"pool": None}


def pool_ol():
    """Birlashgan savollar fondi: Tematika (T…) + Repetitor (R…). → {id: {savol, bolim, mavzu, b(qiyinlik logit), manba}}"""
    if _kesh["pool"] is None:
        p = {}
        for tur, b in (("tem", bank_ol()), ("rep", rep_bank_ol())):
            bol = {r: bolim_of(m.get("nom"), m.get("kitob")) for r, m in b.mavzular.items()}
            for sid, t in b.savol.items():
                if len(t["variantlar"]) < 4 or t.get("rasm"):   # rasmli savol — keyingi bosqich
                    continue
                p[sid] = {"t": t, "bolim": bol[t["mavzu"]], "mavzu": t["mavzu"], "b": QIYIN_LOGIT.get(t.get("qiyinlik") or "R", 0.0), "tur": tur}
        _kesh["pool"] = p
    return _kesh["pool"]


def _norm(s):
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()


def test_tuz(tur, rng, qiyinlik_emp=None):
    """Bo'limlar bo'yicha savol tanlaydi, har bo'limda qiyinlik bo'yicha tekis (quantil) tanlov; umumiy tartib — osondan qiyinga."""
    cfg = TUZILMA[tur]
    pool = pool_ol()
    emp = qiyinlik_emp or {}
    out, korildi = [], set()
    for bolim, n in cfg["bolim"].items():
        nomzod = [(sid, v) for sid, v in pool.items() if v["bolim"] == bolim]
        rng.shuffle(nomzod)
        nomzod = nomzod[:max(n * 40, 200)]
        nomzod.sort(key=lambda x: emp.get(x[0], x[1]["b"]))
        # takror matnli savollar bo'lmasin
        toza = []
        for sid, v in nomzod:
            k = _norm(v["t"]["savol"]) + "|" + "|".join(_norm(x) for x in v["t"]["variantlar"])
            if k not in korildi:
                toza.append((sid, v)); korildi.add(k)
        if len(toza) < n:
            raise ValueError(f"{bolim}: savol yetmadi")
        for i in range(n):   # tekis quantil: oson → qiyin
            out.append(toza[int((i + 0.5) * len(toza) / n)])
    out.sort(key=lambda x: (emp.get(x[0], x[1]["b"]), x[0]))
    return out


def eap_theta(natijalar):
    """natijalar: [(qiyinlik, togri_mi)] → (theta, xatolik). N(0,1) apriori, tarmoq -4…4."""
    nuqta = [-4 + i * 0.05 for i in range(161)]
    w = []
    for th in nuqta:
        lp = -th * th / 2
        for b, ok in natijalar:
            p = 1 / (1 + math.exp(-(th - b)))
            lp += math.log(p if ok else 1 - p)
        w.append(lp)
    m = max(w)
    e = [math.exp(x - m) for x in w]
    s = sum(e)
    mu = sum(t * x for t, x in zip(nuqta, e)) / s
    sd = math.sqrt(sum((t - mu) ** 2 * x for t, x in zip(nuqta, e)) / s)
    return mu, sd


def ball_shkalasi(theta):
    """Qobiliyat (logit) → 0–75 shkala: o'rta = 50, 1 logit = 10 ball (rasmiy: o'rta 50, SD 10, yuqori chegara 75)."""
    return max(0.0, min(75.0, 50.0 + 10.0 * theta))


def daraja_nomi(ball):
    if ball >= 55:
        return "yuqori"
    if ball >= 46:
        return "o'rta"
    return "tayyorgarlik kerak"


def baholash(tur, idlar, javoblar, emp=None):
    pool = pool_ol()
    emp = emp or {}
    natija, rasch = [], []
    bolim = {k: [0, 0] for k in BOLIMLAR}
    mavzu = {}
    for sid in idlar:
        v = pool[sid]
        h = str(javoblar.get(sid) or "").strip().upper()[:1]
        ok = h in HARFLAR and h == v["t"]["javob"]
        b = emp.get(sid, v["b"])
        rasch.append((b, ok))
        bolim[v["bolim"]][1] += 1
        bolim[v["bolim"]][0] += int(ok)
        mv = mavzu.setdefault(v["mavzu"], [0, 0]); mv[1] += 1; mv[0] += int(ok)
        natija.append({"id": sid, "togri": ok, "javob": v["t"]["javob"], "tanlandi": h if h in HARFLAR else "", "bolim": v["bolim"], "mavzu": v["mavzu"], "yechim": v["t"].get("yechim") or None})
    theta, xato = eap_theta(rasch)
    ball = round(ball_shkalasi(theta), 1)
    togri = sum(1 for x in natija if x["togri"])
    return {"tur": tur, "togri": togri, "jami": len(natija), "foiz": round(100 * togri / max(1, len(natija))), "ball": ball, "xato": round(10 * xato, 1),
            "daraja": baho_harfi(ball), "daraja_nomi": daraja_nomi(ball), "sertifikat": ball >= 46,
            "bolimlar": [{"kalit": k, "nom": BOLIMLAR[k], "togri": a, "jami": n, "foiz": round(100 * a / n) if n else None} for k, (a, n) in bolim.items() if n],
            "mavzular": mavzu, "natija": natija,
            "izoh": "Taxminiy ball: Rasch modeli (savol qiyinligi hisobga olinadi), 0–75 shkala. Rasmiy natija emas — o'zingizni sinash uchun."}


def zaif_mavzular(natija, soni=6):
    """Xato qilingan savollar mavzulari → Repetitor mavzulari (150 mavzu) bo'yicha tavsiya. Tematika mavzulari nomi bo'yicha Repetitor mavzusiga moslanadi."""
    rep = rep_bank_ol()
    tem = bank_ol()
    xato = {}
    for x in natija:
        if not x["togri"]:
            xato[x["mavzu"]] = xato.get(x["mavzu"], 0) + 1
    out = []
    for raqam, n in sorted(xato.items(), key=lambda kv: -kv[1]):
        if raqam >= REPETITOR_BOSHI:
            out.append({"mavzu": raqam - REPETITOR_BOSHI, "nom": rep.mavzular[raqam]["nom"], "xato": n})
        else:
            nom = tem.mavzular[raqam]["nom"]
            toki = {w for w in re.findall(r"[a-zʻ'’‘]{4,}", nom.lower())}
            eng, bal = None, 0
            for r, m in rep.mavzular.items():
                ort = len(toki & {w for w in re.findall(r"[a-zʻ'’‘]{4,}", m["nom"].lower())})
                if ort > bal:
                    eng, bal = r, ort
            if eng:
                out.append({"mavzu": eng - REPETITOR_BOSHI, "nom": rep.mavzular[eng]["nom"], "xato": n, "manba_mavzu": nom})
    ko = {}
    for o in out:   # takrorlarni birlashtirish
        if o["mavzu"] in ko:
            ko[o["mavzu"]]["xato"] += o["xato"]
        else:
            ko[o["mavzu"]] = o
    return sorted(ko.values(), key=lambda o: -o["xato"])[:soni]


class Topshir(BaseModel):
    token: Optional[str] = None
    tur: str = Field(default="kirish", max_length=10)
    idlar: list = Field(default_factory=list)
    javoblar: dict = Field(default_factory=dict)
    sekund: int = Field(default=0, ge=0, le=20000)


def create_router(platform):
    router = APIRouter(tags=["mat_sertifikat"])
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
                cur.execute("""CREATE TABLE IF NOT EXISTS mat_sert_urinish (
                    id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, tur TEXT NOT NULL, ball REAL NOT NULL, foiz INT NOT NULL, togri INT NOT NULL, jami INT NOT NULL,
                    sekund INT NOT NULL DEFAULT 0, bolimlar TEXT NOT NULL DEFAULT '[]', yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
                cur.execute("CREATE INDEX IF NOT EXISTS mat_sert_urinish_u ON mat_sert_urinish(user_id, yaratildi DESC)")
                holat["tayyor"] = True
            r = fn(cur)
            conn.commit()
            return r
        finally:
            cur.close()
            conn.close()

    def empirik(cur, ids):
        """Savolning haqiqiy qiyinligi: >=20 urinish bo'lsa, javoblar foizidan (Rasch logiti); aks holda belgisi bo'yicha."""
        cur.execute("SELECT savol_id, SUM(urinish) AS u, SUM(togri) AS t FROM mat_bank_javob WHERE savol_id = ANY(%s) GROUP BY savol_id HAVING SUM(urinish) >= 20", (list(ids),))
        out = {}
        for r in cur.fetchall():
            p = min(0.97, max(0.03, float(r["t"]) / float(r["u"])))
            out[r["savol_id"]] = -math.log(p / (1 - p))
        return out

    @router.get("/api/matsert/turlar")
    def turlar(token: str = None, authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)

        def f(cur):
            cur.execute("SELECT id, tur, ball, foiz, togri, jami, yaratildi FROM mat_sert_urinish WHERE user_id=%s ORDER BY yaratildi DESC LIMIT 20", (u,))
            return [{"id": int(r["id"]), "tur": r["tur"], "ball": float(r["ball"]), "foiz": int(r["foiz"]), "togri": int(r["togri"]), "jami": int(r["jami"]),
                     "daraja": baho_harfi(float(r["ball"])), "sana": r["yaratildi"].isoformat()} for r in cur.fetchall()]
        return {"turlar": [{"tur": k, **{x: v[x] for x in ("nom", "savol", "daqiqa")}} for k, v in TUZILMA.items()], "tarix": run(f),
                "izoh": "Taxminiy ball (Rasch, 0–75). 46 dan sertifikat beriladi. Rasmiy natija emas."}

    @router.get("/api/matsert/test")
    def test(token: str = None, tur: str = Query("kirish", max_length=10), authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        if tur not in TUZILMA:
            raise HTTPException(400, "Tur: kirish yoki toliq")
        pool = pool_ol()
        emp = run(lambda cur: empirik(cur, list(pool)[:20000]))
        try:
            sav = test_tuz(tur, random.Random(), emp)
        except ValueError as e:
            raise HTTPException(503, str(e))
        cfg = TUZILMA[tur]
        sav_o = []
        for sid, v in sav:
            t = v["t"]
            sav_o.append({"id": sid, "bolim": v["bolim"], "savol": t["savol"], "variantlar": t["variantlar"]})
        return {"tur": tur, "nom": cfg["nom"], "daqiqa": cfg["daqiqa"], "soni": len(sav_o), "savollar": sav_o}

    @router.post("/api/matsert/topshir")
    def topshir(body: Topshir, authorization: Optional[str] = Header(None)):
        u = uid(body.token, authorization)
        if body.tur not in TUZILMA:
            raise HTTPException(400, "Tur: kirish yoki toliq")
        pool = pool_ol()
        idlar = [str(x) for x in body.idlar]
        if not idlar or len(idlar) != TUZILMA[body.tur]["savol"] or len(set(idlar)) != len(idlar) or any(x not in pool for x in idlar):
            raise HTTPException(400, "Savollar ro'yxati noto'g'ri")
        emp = run(lambda cur: empirik(cur, idlar))
        r = baholash(body.tur, idlar, {str(k): v for k, v in body.javoblar.items()}, emp)
        r["tavsiya"] = zaif_mavzular(r["natija"])

        def f(cur):
            import json as _j
            cur.execute("INSERT INTO mat_sert_urinish(user_id, tur, ball, foiz, togri, jami, sekund, bolimlar) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                        (u, body.tur, r["ball"], r["foiz"], r["togri"], r["jami"], body.sekund, _j.dumps(r["bolimlar"], ensure_ascii=False)))
            r["id"] = int(cur.fetchone()["id"])
            for x in r["natija"]:   # xatolar «Takrorlash» uchun umumiy tarixga ham yoziladi (Tematika/Repetitor bilan bir xil)
                if not x["tanlandi"]:
                    continue
                cur.execute("""INSERT INTO mat_bank_javob(user_id, savol_id, mavzu, urinish, togri, oxirgi_togri, oxirgi_harf) VALUES(%s,%s,%s,1,%s,%s,%s)
                               ON CONFLICT (user_id, savol_id) DO UPDATE SET urinish=mat_bank_javob.urinish+1, togri=mat_bank_javob.togri+EXCLUDED.togri,
                                 oxirgi_togri=EXCLUDED.oxirgi_togri, oxirgi_harf=EXCLUDED.oxirgi_harf, yangilangan=NOW()""",
                            (u, x["id"], x["mavzu"], int(x["togri"]), x["togri"], x["tanlandi"]))
        run(f)
        return r

    return router
