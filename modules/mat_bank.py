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
RASM_PAPKA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mat_bank_data", "rasm")
DARS_FAYL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mat_bank_data", "dars.json")   # Repetitor «miyasi»: tools/mat_bank/dars_qosh.py yasaydi
# Milliy sertifikat darajalari (rasmiy shkala, ball bo'yicha): 70+ A+, 65–69,9 A, 60–64,9 B+, 55–59,9 B, 50–54,9 C+, 46–49,9 C; 46 dan past — sertifikat berilmaydi.
# DIQQAT: rasmiy ball Rasch modeli bilan hisoblanadi; bizda test FOIZI bor — shuning uchun bu «taxminiy baho» (o'zini sinash), rasmiy natija emas.
BAHO_SHKALASI = [(70.0, "A+"), (65.0, "A"), (60.0, "B+"), (55.0, "B"), (50.0, "C+"), (46.0, "C")]


def baho_harfi(foiz):
    """Test foizi (0–100) → taxminiy daraja harfi yoki None (46 dan past — C ga yetmadi)."""
    for chegara, harf in BAHO_SHKALASI:
        if foiz >= chegara - 1e-9:
            return harf
    return None


def qiyinlik_xulosasi(savollar):
    """Test savollarining qiyinligi (O/R/Q belgilari bor savollar bo'yicha). Yarmidan kamida belgi bo'lmasa — None (aniqlanmagan)."""
    b = [t.get("qiyinlik") for t in savollar if t.get("qiyinlik") in QIYINLIK]
    if not savollar or len(b) * 2 < len(savollar):
        return None
    o = sum({"O": 1, "R": 2, "Q": 3}[x] for x in b) / len(b)
    return {"daraja": "oson" if o < 1.5 else ("o'rta" if o < 2.34 else "qiyin"), "belgili": len(b), "jami": len(savollar), "taqsimot": {k: b.count(k) for k in "ORQ"}}

_kesh = {"bank": None}
_qulf = threading.Lock()


class Bank:
    def __init__(self, data):
        self.manba = data.get("manba", "")
        self.mavzular = {int(m["raqam"]): m for m in data["mavzular"]}
        self.savol = {}          # o'quvchiga beriladiganlar (nuqsonli [TEKSHIR] testlar KIRMAYDI)
        self.tekshir = {}        # o'qituvchi ko'rib chiqishi kerak bo'lgan testlar
        for m in data["mavzular"]:
            for t in m["testlar"]:
                (self.tekshir if t.get("tekshir") else self.savol)[t["id"]] = dict(t, mavzu=int(m["raqam"]))
        self.darslar = {}
        try:
            with open(DARS_FAYL, encoding="utf-8") as f:
                self.darslar = json.load(f).get("darslar", {})
        except (OSError, ValueError):
            self.darslar = {}

    def dars_ol(self, raqam):
        """O'quvchiga ko'rsatiladigan dars: [TEKSHIR] belgili bo'lsa yoki yo'q bo'lsa — None."""
        d = (self.darslar.get(str(int(raqam))) if hasattr(self, "darslar") else None)
        return d if d and not d.get("tekshir") else None

    def dars_korinishi(self, raqam):
        """Dars + bankdan qo'yiladigan savollar: misolning savoli va variantlari faylda EMAS, bankdan olinadi (GPT buza olmaydi)."""
        d = self.dars_ol(raqam)
        if not d:
            return None
        kod = {t["manba"]: t for t in self.savol.values() if t["mavzu"] == int(raqam)}
        mis = []
        for x in d["misollar"]:
            t = kod.get(x["manba"])
            if t:
                mis.append(dict(x, savol=t["savol"], variantlar=t["variantlar"], qiyinlik=t.get("qiyinlik") or None))
        tek = [kod[k]["id"] for k in d["tekshir_manbalar"] if k in kod]
        return {"raqam": int(raqam), "nom": d["nom"], "bob": d.get("bob") or "", "maqsad": d["maqsad"], "oldin_bil": d["oldin_bil"], "tushuncha": d["tushuncha"],
                "misollar": mis, "xatolar": d["xatolar"], "esda_tut": d["esda_tut"], "tarix": d.get("tarix") or "", "geo": d.get("geo") or {}, "tekshir_ids": tek}

    def soni(self, raqam):
        """Mavzudagi o'quvchiga beriladigan testlar soni."""
        return sum(1 for t in self.mavzular[raqam]["testlar"] if not t.get("tekshir"))

    def ommaviy(self, t):
        """Savol o'quvchiga — JAVOBSIZ."""
        return {"id": t["id"], "mavzu": t["mavzu"], "manba": t["manba"], "savol": t["savol"], "variantlar": t["variantlar"], "qiyinlik": t.get("qiyinlik") or None, "tur": t.get("tur")}


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
        natija.append({"id": sid, "togri": ok, "javob": t["javob"], "tanlandi": h if h in HARFLAR else "", "yechim": t.get("yechim") or None, "qiyinlik": t.get("qiyinlik") or None})
    jami = len(natija)
    ball = 100.0 * togri / jami if jami else 0.0
    return {"natija": natija, "togri": togri, "jami": jami, "foiz": round(ball), "baho": baho_harfi(ball) if jami else None,
            "qiyinlik": qiyinlik_xulosasi([bank.savol[x["id"]] for x in natija]),
            "baho_izoh": "Taxminiy baho: test foizi Milliy sertifikat shkalasiga qo‘yildi (rasmiy ball boshqacha hisoblanadi)."}


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
        return {"manba": b.manba, "mavzular": [{"raqam": r, "nom": m["nom"], "kitob": m["kitob"], "bob": m.get("bob") or "", "dars": b.dars_ol(r) is not None, "testlar": b.soni(r), "misol": len(m.get("misollar") or m["namunalar"])}
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
        mis = m.get("misollar") or []
        return {"raqam": raqam, "nom": m["nom"], "kitob": m["kitob"], "bob": m.get("bob") or "", "dars": bank_ol().dars_ol(raqam) is not None, "qoida": m["qoida"], "turlar": m.get("turlar") or [],
                "namunalar": [x["matn"] for x in mis] if mis else m["namunalar"], "misollar": [{"tur": x["tur"], "tip": x["tip"]} for x in mis],
                "testlar": bank_ol().soni(raqam), "meniki": run(f)}

    @router.get("/api/matbank/dars/{raqam}")
    def dars(raqam: int, token: str = None, authorization: Optional[str] = Header(None)):
        """Repetitor darsi: maqsad, tushuncha, misol tahlili (savol bankdan), xatolar, esda tut, o'zini tekshir (savol id lari)."""
        uid(token, authorization)
        d = bank_ol().dars_korinishi(raqam)
        if not d:
            raise HTTPException(404, "Bu mavzu uchun dars hali yo'q")
        return d

    @router.get("/api/matbank/test")
    def test(token: str = None, mavzu: str = Query("", max_length=200), soni: int = Query(10, ge=1, le=SONI_ENG_KOP),
             qiyinlik: str = Query("", max_length=1), ids: str = Query("", max_length=400), authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)
        b = bank_ol()
        if ids.strip():      # aniq savollar (dars oxiridagi «o'zini tekshir»): faqat o'quvchiga beriladigan (nuqsonsiz) savollar
            tanlangan = [x for x in dict.fromkeys(re.split(r"[,\s]+", ids.strip())) if x]
            if not 1 <= len(tanlangan) <= SONI_ENG_KOP or any(x not in b.savol for x in tanlangan):
                raise HTTPException(404, "Savollar topilmadi")
            return {"soni": len(tanlangan), "savollar": [b.ommaviy(b.savol[x]) for x in tanlangan]}
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

    @router.get("/api/matbank/rasm/{nom}")
    def rasm(nom: str, token: str = None, authorization: Optional[str] = Header(None)):
        """Chizma (masalan T100-1.png). Faqat kirgan foydalanuvchiga; fayl nomi qat'iy shablon bo'yicha."""
        uid(token, authorization)
        if not re.fullmatch(r"T\d{3}-\d{1,3}\.(png|jpg|jpeg|gif|webp)", nom):
            raise HTTPException(404, "Rasm topilmadi")
        yol = os.path.join(RASM_PAPKA, nom)
        if not os.path.isfile(yol):
            raise HTTPException(404, "Rasm topilmadi")
        from fastapi.responses import FileResponse
        return FileResponse(yol, headers={"Cache-Control": "private, max-age=86400"})

    @router.get("/api/matbank/tekshirish")
    def tekshirish(token: str = None, authorization: Optional[str] = Header(None)):
        """O'qituvchi/admin uchun: manbadagi nuqsonli deb belgilangan testlar (o'quvchiga berilmaydi)."""
        u = uid(token, authorization)

        def f(cur):
            cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s UNION ALL SELECT 1 FROM users WHERE user_id=%s AND role IN ('oqituvchi','admin')", (u, u))
            if not cur.fetchone():
                raise HTTPException(403, "Faqat o'qituvchi yoki admin ko'ra oladi")
        run(f)
        b = bank_ol()
        return {"soni": len(b.tekshir), "testlar": [{"id": t["id"], "mavzu": t["mavzu"], "mavzu_nomi": b.mavzular[t["mavzu"]]["nom"], "manba": t["manba"], "savol": t["savol"],
                                                     "variantlar": t["variantlar"], "kalit": t["javob"], "sabab": t.get("tekshir_izoh") or ""} for t in b.tekshir.values()]}

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
