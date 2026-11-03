"""REV269: O'quv markazi — ikki yo'l: «Sertifikat» (imtihonga tayyorlov) va «Erkin til» (hayot uchun).

Sof qoidalar (bazasiz sinanadi): imtihonlar katalogi, jadval bo'yicha nazorat (eslatma → motivatsiya → tanbeh,
aniq raqamlar bilan), bo'lim darvozasi (takrorlashdan o'tmasa keyingi bo'lim ochilmaydi), cheklovsiz ochilish.
Kontent mualliflik huquqiga rioya qiladi: imtihon formatlari ochiq e'lon qilingan spetsifikatsiyadan; materiallar — o'zimizniki."""
import datetime as dt
import json
import math

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# ───────────── Imtihonlar katalogi (rasmiy ochiq formatlar; 2026) ─────────────
IMTIHONLAR = {
    "milliy_cefr": {"nom": "Milliy sertifikat (CEFR, multilevel)", "tillar": ["en", "ru", "de", "fr", "es", "ar", "tr", "ko", "ja", "zh"],
                    "darajalar": ["B1", "B2", "C1"], "bolimlar": [
                        {"nom": "Listening", "topshiriq": 35, "daqiqa": 45}, {"nom": "Reading", "topshiriq": 35, "daqiqa": 60},
                        {"nom": "Writing", "topshiriq": 2, "daqiqa": 60}, {"nom": "Speaking", "topshiriq": 3, "daqiqa": 15}],
                    "shkala": "har bo'lim 75 ball; B1 38–50, B2 51–64, C1 65–75", "amal": "2 yil"},
    "ielts": {"nom": "IELTS Academic / General", "tillar": ["en"], "darajalar": [str(x / 2) for x in range(8, 19)],
              "bolimlar": [{"nom": "Listening", "topshiriq": 40, "daqiqa": 30}, {"nom": "Reading", "topshiriq": 40, "daqiqa": 60},
                           {"nom": "Writing", "topshiriq": 2, "daqiqa": 60}, {"nom": "Speaking", "topshiriq": 3, "daqiqa": 14}],
              "shkala": "1–9 band (0,5 qadam)", "amal": "2 yil"},
    "toefl": {"nom": "TOEFL iBT (2026 formati)", "tillar": ["en"], "darajalar": [str(x / 2) for x in range(2, 13)],
              "bolimlar": [{"nom": "Reading"}, {"nom": "Listening"}, {"nom": "Writing"}, {"nom": "Speaking"}],
              "shkala": "1–6 band (0,5 qadam), CEFR bilan: 6 — C2, 5–5,5 — C1, 4–4,5 — B2, 3–3,5 — B1", "amal": "2 yil"},
    "sat": {"nom": "SAT (raqamli)", "tillar": ["en"], "darajalar": ["1000", "1200", "1350", "1450", "1550"],
            "bolimlar": [{"nom": "Reading and Writing"}, {"nom": "Math"}], "shkala": "400–1600", "amal": "—"},
    "goethe": {"nom": "Goethe-Zertifikat", "tillar": ["de"], "darajalar": ["A1", "A2", "B1", "B2", "C1", "C2"], "bolimlar": [], "shkala": "CEFR", "amal": "—"},
    "trki": {"nom": "TRKI / ТРКИ", "tillar": ["ru"], "darajalar": ["A1", "A2", "B1", "B2", "C1", "C2"], "bolimlar": [], "shkala": "CEFR", "amal": "—"},
    "delf": {"nom": "DELF / DALF", "tillar": ["fr"], "darajalar": ["A1", "A2", "B1", "B2", "C1", "C2"], "bolimlar": [], "shkala": "CEFR", "amal": "muddatsiz"},
    "dele": {"nom": "DELE", "tillar": ["es"], "darajalar": ["A1", "A2", "B1", "B2", "C1", "C2"], "bolimlar": [], "shkala": "CEFR", "amal": "muddatsiz"},
    "topik": {"nom": "TOPIK", "tillar": ["ko"], "darajalar": ["1", "2", "3", "4", "5", "6"], "bolimlar": [], "shkala": "1–6", "amal": "2 yil"},
    "jlpt": {"nom": "JLPT", "tillar": ["ja"], "darajalar": ["N5", "N4", "N3", "N2", "N1"], "bolimlar": [], "shkala": "N5–N1", "amal": "muddatsiz"},
    "hsk": {"nom": "HSK", "tillar": ["zh"], "darajalar": [str(x) for x in range(1, 10)], "bolimlar": [], "shkala": "1–9", "amal": "2 yil"},
    "tys": {"nom": "TYS (Türkçe Yeterlik Sınavı)", "tillar": ["tr"], "darajalar": ["A1", "A2", "B1", "B2", "C1", "C2"], "bolimlar": [], "shkala": "CEFR", "amal": "—"},
}
YOLLAR = {"sertifikat": "Sertifikat", "erkin": "Erkin til (hayot uchun)"}
DARVOZA_FOIZ = 80   # bo'lim takrorlash testidan o'tish chegarasi


# ───────────── Jadval va nazorat ─────────────
def kerakli_kunlar(jadval, boshi, bugun):
    """Jadval bo'yicha boshidan bugungacha nechta dars kuni bo'lishi kerak edi (bugun kiritilmaydi)."""
    turi = (jadval or {}).get("turi", "erkin")
    kunlar = [boshi + dt.timedelta(days=i) for i in range(max(0, (bugun - boshi).days))]
    if turi == "kunlar":
        tanlov = set(int(x) for x in jadval.get("kunlar") or [])   # 0 = dushanba … 6 = yakshanba
        return [k for k in kunlar if k.weekday() in tanlov]
    if turi == "haftada":
        soni = max(1, min(7, int(jadval.get("soni") or 2)))
        haftalar = math.floor(len(kunlar) / 7)
        return [None] * (haftalar * soni)   # aniq kun yo'q — faqat soni
    return []                              # «istalgan vaqtda» — majburiyat yo'q (faqat uzoq tanaffusga eslatma)


def holat(yozilish, faolliklar, bugun):
    """O'quvchining holati va unga aytiladigan gap (raqamlar bilan): yaxshi | eslatma | motivatsiya | tanbeh."""
    boshi = dt.date.fromisoformat(str(yozilish["boshlangan"])[:10])
    kunlar = sorted({dt.date.fromisoformat(str(f["kun"])[:10]) for f in faolliklar})
    jadval = yozilish.get("jadval") or {"turi": "erkin"}
    kerak = kerakli_kunlar(jadval, boshi, bugun)
    if jadval.get("turi") == "kunlar":
        qoldi = [k for k in kerak if k not in set(kunlar)]
        ketma = 0
        for k in reversed(kerak):
            if k in set(kunlar): break
            ketma += 1
    else:
        bajarildi = len([k for k in kunlar if k < bugun])
        qoldi = [None] * max(0, len(kerak) - bajarildi)
        ketma = len(qoldi)
    oxirgi = kunlar[-1] if kunlar else None
    tanaffus = (bugun - oxirgi).days if oxirgi else (bugun - boshi).days
    if jadval.get("turi") == "erkin":
        ketma = 0 if tanaffus < 7 else 1 if tanaffus < 14 else 3
    sozlar = int(yozilish.get("sozlar_soni") or 0)
    # unutish egri chizig'i (taxminiy): takrorlanmagan so'zlarning ulushi tanaffus kunlariga qarab
    unutish = 0 if tanaffus <= 2 else min(0.7, 0.12 * math.log2(tanaffus))
    yoqolayotgan = round(sozlar * unutish)
    imtihon = yozilish.get("imtihon_sana")
    qolgan_kun = (dt.date.fromisoformat(str(imtihon)[:10]) - bugun).days if imtihon else None
    if ketma <= 0:
        daraja = "yaxshi"
        gap = "Zo'r! Jadval bo'yicha ketyapsiz." + (f" Imtihongacha {qolgan_kun} kun qoldi." if qolgan_kun is not None else "")
    elif ketma == 1:
        daraja = "eslatma"
        gap = "Bugungi darsni unutmang — 20 daqiqa yetadi. Har kuni oz-ozdan o'qigan kishi tezroq natijaga erishadi."
    elif ketma == 2:
        daraja = "motivatsiya"
        gap = (f"Ikki dars o'tkazib yubordingiz. Hozir qaytsangiz, o'rgangan {sozlar} ta so'zingiz saqlanib qoladi"
               + (f"; imtihongacha {qolgan_kun} kun bor — ulgurasiz." if qolgan_kun is not None and qolgan_kun > 0 else "."))
    else:
        daraja = "tanbeh"
        gap = (f"{len(qoldi) if qoldi else ketma} ta dars o'tkazildi, oxirgi marta {tanaffus} kun oldin o'qidingiz. "
               f"Takrorlanmagan {yoqolayotgan} ta so'z esdan chiqmoqda. ")
        if qolgan_kun is not None:
            gap += (f"Imtihongacha {qolgan_kun} kun qoldi — shu sur'atda maqsadga ulgurmaysiz. " if qolgan_kun > 0 else "Imtihon sanasi o'tgan — yangi sana belgilang. ")
        gap += "Bugun qaytib, avval takrorlashdan o'ting: o'qimaslikning zarari to'planib boradi, foydasi esa har kungi kichik qadamdan."
    return {"daraja": daraja, "gap": gap, "qoldirilgan": len(qoldi) if qoldi else (ketma if jadval.get("turi") != "kunlar" else 0),
            "ketma_ket": ketma, "tanaffus_kun": tanaffus, "yoqolayotgan_soz": yoqolayotgan, "imtihongacha": qolgan_kun}


def darvoza(foiz, bolim_nomi=""):
    """Bo'lim takrorlash testi: o'tsa — keyingi bo'lim ochiladi; o'tmasa — aniq sabab va qayta tayyorlanish."""
    foiz = float(foiz or 0)
    if foiz >= DARVOZA_FOIZ:
        return {"ochildi": True, "gap": f"Ajoyib! {round(foiz)}% — keyingi bo'lim ochildi."}
    return {"ochildi": False, "gap": (f"{round(foiz)}% — o'tish uchun {DARVOZA_FOIZ}% kerak. «{bolim_nomi or 'Bu bo‘lim'}»ni bilmasdan keyingi "
                                         "darslar foydasiz bo'ladi: ular shu bilimga quriladi. Xatolaringizni ko'rib, qaytadan tayyorlaning va testni yana topshiring.")}


# ───────────── Baza va API ─────────────
def _jadvallar(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS markaz_yozilish (
        id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, yol TEXT NOT NULL, til TEXT NOT NULL, imtihon TEXT, maqsad TEXT,
        imtihon_sana DATE, jadval JSONB NOT NULL DEFAULT '{"turi":"erkin"}', daraja TEXT, sozlar_soni INT NOT NULL DEFAULT 0,
        ochiq_bolim INT NOT NULL DEFAULT 1, boshlangan DATE NOT NULL DEFAULT CURRENT_DATE, faol BOOLEAN NOT NULL DEFAULT TRUE,
        yaratilgan TIMESTAMPTZ NOT NULL DEFAULT now())""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_markaz_yozilish_user ON markaz_yozilish(user_id) WHERE faol")
    cur.execute("""CREATE TABLE IF NOT EXISTS markaz_faollik (
        id BIGSERIAL PRIMARY KEY, yozilish_id BIGINT NOT NULL REFERENCES markaz_yozilish(id) ON DELETE CASCADE,
        kun DATE NOT NULL DEFAULT CURRENT_DATE, turi TEXT NOT NULL DEFAULT 'dars', dars_kodi TEXT, daqiqa INT NOT NULL DEFAULT 0,
        foiz NUMERIC, yaratilgan TIMESTAMPTZ NOT NULL DEFAULT now())""")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_markaz_faollik_yoz ON markaz_faollik(yozilish_id, kun)")


class Yozilish(BaseModel):
    token: str
    yol: str
    til: str
    imtihon: str | None = None
    maqsad: str | None = None
    imtihon_sana: str | None = None
    jadval: dict | None = None


class Faollik(BaseModel):
    token: str
    yozilish_id: int
    turi: str = "dars"
    dars_kodi: str | None = None
    daqiqa: int = 0
    foiz: float | None = None
    sozlar_soni: int | None = None
    bolim: int | None = None
    bolim_nomi: str | None = None


def create_router(platform):
    router = APIRouter(tags=["markaz"])

    @router.get("/api/markaz/katalog")
    def katalog():
        return {"yollar": YOLLAR, "imtihonlar": IMTIHONLAR, "darvoza_foiz": DARVOZA_FOIZ}

    @router.post("/api/markaz/yozil")
    def yozil(s: Yozilish):
        uid = platform._jwt_tekshir(s.token)
        if s.yol not in YOLLAR:
            raise HTTPException(400, "Yo'l noto'g'ri")
        if s.yol == "sertifikat" and (s.imtihon not in IMTIHONLAR or s.til not in IMTIHONLAR[s.imtihon]["tillar"]):
            raise HTTPException(400, "Imtihon yoki til noto'g'ri")
        jadval = s.jadval or {"turi": "erkin"}
        if jadval.get("turi") not in ("kunlar", "haftada", "erkin"):
            raise HTTPException(400, "Jadval noto'g'ri")
        conn = platform._db(); cur = conn.cursor()
        try:
            _jadvallar(cur)
            cur.execute("""INSERT INTO markaz_yozilish (user_id, yol, til, imtihon, maqsad, imtihon_sana, jadval)
                           VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                        (uid, s.yol, s.til[:5], s.imtihon, (s.maqsad or "")[:20], s.imtihon_sana or None, json.dumps(jadval)))
            yid = cur.fetchone()["id"]; conn.commit()
        finally:
            cur.close(); conn.close()
        return {"id": yid}

    @router.get("/api/markaz/daraja/savollar")
    def daraja_savollar(til: str = "en"):
        from modules.markaz_daraja import savollar
        q = savollar(til)
        if not q:
            raise HTTPException(404, "Bu til uchun daraja testi tez orada")
        return {"til": til, "savollar": q}

    class _DarajaJavob(BaseModel):
        token: str
        yozilish_id: int
        til: str = "en"
        javoblar: dict

    @router.post("/api/markaz/daraja/natija")
    def daraja_natija(s: _DarajaJavob):
        uid = platform._jwt_tekshir(s.token)
        from modules.markaz_daraja import baholash
        n = baholash(s.til, s.javoblar or {})
        conn = platform._db(); cur = conn.cursor()
        try:
            _jadvallar(cur)
            cur.execute("UPDATE markaz_yozilish SET daraja=%s WHERE id=%s AND user_id=%s RETURNING id", (n["daraja"], s.yozilish_id, uid))
            if not cur.fetchone():
                raise HTTPException(404, "Kurs topilmadi")
            cur.execute("INSERT INTO markaz_faollik (yozilish_id, turi, foiz) VALUES (%s,'daraja',%s)", (s.yozilish_id, max(n["foiz"].values() or [0])))
            conn.commit()
        finally:
            cur.close(); conn.close()
        return n

    @router.get("/api/markaz/mashq")
    def mashq(til: str = "en", daraja: str = "A1", dars: int = 1, iz: str = "uz"):
        """REV275: 4 ko'nikma mashqlari — tinglash, diktant, gapirish (javoblar ochiq: tekshiruv brauzerda, natija /faollik ga)."""
        from modules.markaz_mashq import mashqlar
        m = mashqlar(til, daraja, dars, "ru" if iz == "ru" else "uz")
        if not m:
            raise HTTPException(404, "Bu kurs uchun mashqlar tez orada")
        return m


    # ───────── REV276: sun'iy intellekt bilan suhbat (rol o'yini) va yozishni baholash ─────────
    class _Suhbat(BaseModel):
        token: str
        yozilish_id: int
        dars: int = 1
        iz: str = "uz"
        xabarlar: list = []

    class _Yozish(BaseModel):
        token: str
        yozilish_id: int
        dars: int = 1
        iz: str = "uz"
        matn: str

    def _ai_json(platform_, tizim, xabarlar, max_tokens=400):
        import httpx
        kalit = getattr(platform_, "GROQ_API_KALIT", "")
        if not kalit:
            raise HTTPException(503, "AI hali sozlanmagan — GROQ_API_KEY kerak")
        try:
            with httpx.Client(timeout=25) as c:
                r = c.post("https://api.groq.com/openai/v1/chat/completions",
                           headers={"Authorization": f"Bearer {kalit}", "Content-Type": "application/json"},
                           json={"model": "llama-3.3-70b-versatile", "temperature": 0.4, "max_tokens": max_tokens,
                                 "response_format": {"type": "json_object"},
                                 "messages": [{"role": "system", "content": tizim}, *xabarlar]})
            r.raise_for_status()
            return json.loads(r.json()["choices"][0]["message"]["content"])
        except HTTPException:
            raise
        except Exception as e:
            print(f"[MARKAZ-AI] {type(e).__name__}: {str(e)[:200]}", flush=True)
            raise HTTPException(502, "AI hozir javob bermadi. Birozdan keyin qayta urinib ko'ring.")

    def _dars(dars):
        from modules.markaz_mashq import KURSLAR
        DARSLAR = KURSLAR[("en", "A1")]
        if not (1 <= int(dars) <= len(DARSLAR)):
            raise HTTPException(404, "Dars topilmadi")
        return DARSLAR[int(dars) - 1]

    @router.post("/api/markaz/suhbat")
    def suhbat(s: _Suhbat):
        uid = platform._jwt_tekshir(s.token)
        platform._ai_limit(uid, "markaz_suhbat")
        d = _dars(s.dars)
        rol = d["dialog"][0][0]
        izoh_til = "Russian" if s.iz == "ru" else "Uzbek (Latin script)"
        tizim = (f"You are {rol} in a real-life English conversation practice for a CEFR A1 learner. Situation: {d['rol'][0]} "
                 f"Example dialogue for this situation: " + " / ".join(f"{a}: {b}" for a, b, *_ in d["dialog"]) + ". "
                 "Rules: stay in role; reply in simple, natural English (A1: short sentences, max 12 words each, max 2 sentences); "
                 "ask one simple question to keep the conversation going; never switch to another language in 'javob'. "
                 f"Also check the learner's LAST message: if it has a grammar or word mistake, give the corrected sentence and a very short "
                 f"explanation in {izoh_til}; if it is correct, leave 'tuzatish' empty. "
                 'Return JSON: {"javob": "your English reply", "tuzatish": "corrected sentence or empty", "izoh": "short explanation or empty", "tugadi": false}. '
                 "Set tugadi=true after about 6 exchanges or when the situation is naturally finished.")
        tarix = [{"role": "assistant" if x.get("rol") == "ai" else "user", "content": str(x.get("matn") or "")[:400]} for x in (s.xabarlar or [])[-12:]]
        if not tarix:
            tarix = [{"role": "user", "content": "(The learner has just arrived. Start the conversation with a greeting.)"}]
        j = _ai_json(platform, tizim, tarix)
        return {"javob": str(j.get("javob") or "")[:400], "tuzatish": str(j.get("tuzatish") or "")[:300],
                "izoh": str(j.get("izoh") or "")[:300], "tugadi": bool(j.get("tugadi")), "rol": rol}

    @router.post("/api/markaz/yozish")
    def yozish(s: _Yozish):
        uid = platform._jwt_tekshir(s.token)
        platform._ai_limit(uid, "markaz_yozish")
        d = _dars(s.dars)
        matn = (s.matn or "").strip()[:1500]
        if len(matn.split()) < 3:
            raise HTTPException(400, "Kamida 3 ta so'z yozing")
        izoh_til = "Russian" if s.iz == "ru" else "Uzbek (Latin script)"
        tizim = ("You are a careful, encouraging English teacher marking an A1 learner's short writing. "
                 f"Task: Write 3–5 sentences. {d['rol'][0]} "
                 f"Mark it like a CEFR-aligned examiner: task achievement, vocabulary, grammar, spelling/punctuation. Explanations in {izoh_til}. "
                 "Do not invent mistakes; if a sentence is correct, do not list it. "
                 'Return JSON: {"ball": 0-100, "daraja": "pre-A1|A1|A2|B1", "xatolar": [{"asl": "...", "togri": "...", "izoh": "..."}], '
                 '"yaxshi": "one sentence of praise", "maslahat": "one concrete tip", "namuna": "a corrected model version of the whole text"}')
        j = _ai_json(platform, tizim, [{"role": "user", "content": matn}], max_tokens=700)
        out = {"ball": max(0, min(100, int(j.get("ball") or 0))), "daraja": str(j.get("daraja") or "")[:10],
               "xatolar": [{k: str(x.get(k) or "")[:300] for k in ("asl", "togri", "izoh")} for x in (j.get("xatolar") or [])[:12] if isinstance(x, dict)],
               "yaxshi": str(j.get("yaxshi") or "")[:300], "maslahat": str(j.get("maslahat") or "")[:300], "namuna": str(j.get("namuna") or "")[:1500],
               "topshiriq": d["rol"][0]}
        conn = platform._db(); cur = conn.cursor()
        try:
            _jadvallar(cur)
            cur.execute("SELECT 1 FROM markaz_yozilish WHERE id=%s AND user_id=%s", (s.yozilish_id, uid))
            if cur.fetchone():
                cur.execute("INSERT INTO markaz_faollik (yozilish_id, turi, dars_kodi, daqiqa, foiz) VALUES (%s,'yozish',%s,5,%s)", (s.yozilish_id, f"A1-{s.dars}", out["ball"]))
            conn.commit()
        finally:
            cur.close(); conn.close()
        return out

    KURS_FAN = {("en", "uz"): "Ingliz tili — Erkin til", ("en", "ru"): "Ingliz tili — Erkin til (izoh: rus)"}

    @router.get("/api/markaz/darslar")
    def darslar(token: str, til: str = "en", daraja: str = "A1", iz: str = "uz"):
        """REV277: markaz kursining darslari (Miya'ga yuklangan «… — Erkin til» kitobidan), tartib bilan."""
        platform._jwt_tekshir(token)
        fan = KURS_FAN.get((til, "ru" if iz == "ru" else "uz"))
        if not fan:
            return {"darslar": [], "fan": None}
        conn = platform._db(); cur = conn.cursor()
        try:
            cur.execute("""SELECT d.topic_code, COALESCE(NULLIF(d.kichik_name,''), NULLIF(d.mavzu_name,''), NULLIF(d.bolim_name,''), d.bob_name) AS nomi,
                                  d.grade, d.subject_name,
                                  EXISTS(SELECT 1 FROM ai_brain_units au WHERE au.topic_code=d.topic_code AND au.status='published') AS dars_bor
                           FROM dts_tree d WHERE d.is_deleted=FALSE AND d.subject_name=%s AND UPPER(COALESCE(d.grade,''))=UPPER(%s)
                           ORDER BY d.topic_code""", (fan, daraja))
            rows = [dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"[MARKAZ-DARSLAR] {type(e).__name__}: {str(e)[:200]}", flush=True)
            rows = []
        finally:
            cur.close(); conn.close()
        return {"fan": fan, "daraja": daraja, "darslar": [r for r in rows if r.get("dars_bor")]}

    @router.get("/api/markaz/men")
    def men(token: str):
        uid = platform._jwt_tekshir(token)
        conn = platform._db(); cur = conn.cursor()
        try:
            _jadvallar(cur)
            cur.execute("SELECT * FROM markaz_yozilish WHERE user_id=%s AND faol ORDER BY id DESC LIMIT 10", (uid,))
            yozil = [dict(r) for r in cur.fetchall()]
            out = []
            for y in yozil:
                cur.execute("SELECT kun, turi, daqiqa, foiz FROM markaz_faollik WHERE yozilish_id=%s ORDER BY kun DESC LIMIT 400", (y["id"],))
                f = [dict(r) for r in cur.fetchall()]
                out.append({**{k: (str(v) if isinstance(v, (dt.date, dt.datetime)) else v) for k, v in y.items()},
                            "holat": holat(y, f, dt.date.today()), "faollik_soni": len(f)})
            conn.commit()
        finally:
            cur.close(); conn.close()
        return {"kurslar": out}

    @router.post("/api/markaz/faollik")
    def faollik(s: Faollik):
        uid = platform._jwt_tekshir(s.token)
        conn = platform._db(); cur = conn.cursor()
        try:
            _jadvallar(cur)
            cur.execute("SELECT * FROM markaz_yozilish WHERE id=%s AND user_id=%s", (s.yozilish_id, uid))
            y = cur.fetchone()
            if not y:
                raise HTTPException(404, "Kurs topilmadi")
            cur.execute("INSERT INTO markaz_faollik (yozilish_id, turi, dars_kodi, daqiqa, foiz) VALUES (%s,%s,%s,%s,%s)",
                        (s.yozilish_id, s.turi[:20], (s.dars_kodi or "")[:80], max(0, min(600, s.daqiqa)), s.foiz))
            javob = {"saqlandi": True}
            if s.sozlar_soni is not None:
                cur.execute("UPDATE markaz_yozilish SET sozlar_soni=GREATEST(sozlar_soni,%s) WHERE id=%s", (int(s.sozlar_soni), s.yozilish_id))
            if s.turi == "darvoza" and s.foiz is not None:
                d = darvoza(s.foiz, s.bolim_nomi or "")
                if d["ochildi"] and s.bolim:
                    cur.execute("UPDATE markaz_yozilish SET ochiq_bolim=GREATEST(ochiq_bolim,%s) WHERE id=%s", (int(s.bolim) + 1, s.yozilish_id))
                javob["darvoza"] = d
            conn.commit()
        finally:
            cur.close(); conn.close()
        return javob

    return router
