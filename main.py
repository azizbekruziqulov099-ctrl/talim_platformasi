"""main.py — SamTM Ta'lim veb-sayt backend'i (v3).

Haqiqiy jadvallarga ulangan + Google orqali kirish (OAuth) qo'shildi.
"""
import os
import re
import secrets
import string
import httpx
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
JWT_MAXFIY_KALIT = os.getenv("JWT_MAXFIY_KALIT", "")
BAZA_URL = os.getenv("BAZA_URL", "https://talimplatformasi-production.up.railway.app")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://talimplatformasi-production.up.railway.app")
REDIRECT_URI = f"{BAZA_URL}/auth/google/callback"

app = FastAPI(title="SamTM Ta'lim API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"],
)


def _db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


# Fan kodiga qarab dashboard rangi — yangi fan qo'shilsa shu ro'yxatga qo'shiladi
FAN_RANG = {
    "MAT": "#C89B3C", "TIL": "#2D8B8B", "ADB": "#8B5FBF",
    "TAB": "#B0553A", "RUS": "#4A7C9E", "ENG": "#7C9E4A",
}


@app.get("/")
def salomat():
    return {"holat": "ishlayapti"}


@app.get("/api/bola/{bola_id}/bilim")
def bola_bilimi(bola_id: int, sinf: str = None):
    """Bolaning fan-mavzu bo'yicha bilim darajasi.
    sinf berilmasa — bolaning eng so'nggi natijalari mavjud barcha
    sinflardan olinadi (oddiy holatda muammo emas, chunki bitta
    o'quvchi odatda bitta sinfda)."""
    try:
        conn = _db()
        cur = conn.cursor()

        cur.execute("SELECT full_name FROM users WHERE user_id=%s", (bola_id,))
        bola = cur.fetchone()
        if not bola:
            raise HTTPException(status_code=404, detail="Bola topilmadi")

        sinf_shart = "AND d.grade = %s" if sinf else ""
        params = (bola_id, sinf) if sinf else (bola_id,)

        cur.execute(f"""
            SELECT d.subject_code, d.subject_name, d.topic_code,
                   COALESCE(d.mavzu_name, d.bolim_name, d.bob_name) AS mavzu_nomi,
                   lt.score
            FROM dts_tree d
            LEFT JOIN learned_topics lt
                ON lt.topic_code = d.topic_code AND lt.user_id = %s
            WHERE 1=1 {sinf_shart}
            ORDER BY d.subject_code, d.topic_code
        """, params)
        qatorlar = cur.fetchall()
        cur.close()
        conn.close()

        fanlar = {}
        for q in qatorlar:
            kod = q["subject_code"] or "BOSHQA"
            if kod not in fanlar:
                fanlar[kod] = {
                    "nom": q["subject_name"] or kod, "qisqa": kod,
                    "rang": FAN_RANG.get(kod, "#8A8578"), "mavzular": [],
                }
            if q["score"] is not None:   # faqat o'rganilgan mavzular ko'rsatiladi
                fanlar[kod]["mavzular"].append({
                    "nom": q["mavzu_nomi"], "foiz": q["score"],
                })

        # Hali birorta ham mavzu o'rganilmagan fanlarni chiqarmaymiz
        natija_royxat = [f for f in fanlar.values() if f["mavzular"]]
        for f in natija_royxat:
            f["foiz"] = round(sum(m["foiz"] for m in f["mavzular"]) / len(f["mavzular"]))

        umumiy = round(sum(f["foiz"] for f in natija_royxat) / len(natija_royxat)) if natija_royxat else 0

        return {"bola": {"ism": bola["full_name"]}, "umumiy_foiz": umumiy, "fanlar": natija_royxat}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ota/{ota_id}/farzandlar")
def ota_farzandlari(ota_id: int):
    """Ota-onaning barcha ulangan farzandlari ro'yxati."""
    try:
        conn = _db()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.user_id, u.full_name FROM parent_child pc
            JOIN users u ON u.user_id = pc.child_id
            WHERE pc.parent_id = %s
        """, (ota_id,))
        r = cur.fetchall()
        cur.close(); conn.close()
        return {"farzandlar": r}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════
# GOOGLE ORQALI KIRISH (OAuth)
# ═══════════════════════════════════════════════════════════

def _jwt_yarat(user_id: int) -> str:
    """30 kun amal qiladigan sessiya tokeni yaratadi."""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    return jwt.encode(payload, JWT_MAXFIY_KALIT, algorithm="HS256")


def _jwt_tekshir(token: str) -> int:
    """Tokenni tekshiradi, user_id qaytaradi. Noto'g'ri bo'lsa xato beradi."""
    try:
        payload = jwt.decode(token, JWT_MAXFIY_KALIT, algorithms=["HS256"])
        return payload["user_id"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Sessiya eskirgan, qaytadan kiring")


@app.get("/auth/google/login")
def google_login():
    """Foydalanuvchini Google'ning kirish sahifasiga yo'naltiradi."""
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=online"
    )
    return RedirectResponse(url)


@app.get("/auth/google/callback")
async def google_callback(code: str = None, error: str = None):
    """Google qaytargandan keyin ishlaydi — email oladi, bog'langan-bog'lanmaganini
    tekshiradi, mos ekranga yo'naltiradi."""
    if error or not code:
        return RedirectResponse(f"{FRONTEND_URL}/?xato=kirish_bekor")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
            },
        )
        token_data = token_resp.json()
        if "access_token" not in token_data:
            return RedirectResponse(f"{FRONTEND_URL}/?xato=google_token")

        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo = userinfo_resp.json()

    email = userinfo.get("email")
    ism = userinfo.get("name", "")
    if not email:
        return RedirectResponse(f"{FRONTEND_URL}/?xato=email_topilmadi")

    conn = _db()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM google_hisob WHERE google_email=%s", (email,))
    r = cur.fetchone()
    cur.close()
    conn.close()

    if r:
        token = _jwt_yarat(r["user_id"])
        return RedirectResponse(f"{FRONTEND_URL}/kabinet?token={token}")
    else:
        return RedirectResponse(f"{FRONTEND_URL}/ulash?email={email}&ism={ism}")


class UlashSorov(BaseModel):
    email: str
    kod: str


class RoyxatSorov(BaseModel):
    email: str
    ism: str
    rol: str          # 'oquvchi' | 'ota-ona' | 'oqituvchi'
    sinf: str = None  # faqat rol='oquvchi' bo'lsa
    region: str = None
    district: str = None
    tugilgan_sana: str = None
    maktab_raqami: str = None

RUXSAT_ETILGAN_ROLLAR = {"oquvchi", "ota-ona", "oqituvchi"}


@app.get("/auth/ism_tekshir")
def ism_tekshir(ism: str):
    """Botda shu ismga o'xshash foydalanuvchi bor-yo'qligini tekshiradi —
    saytdan yangi ro'yxatdan o'tishda, odam bilmasdan ikkinchi
    (dublikat) hisob ochib qo'ymasligi uchun ogohlantirish beriladi.
    Faqat BOTDAN kelgan (musbat user_id) foydalanuvchilar orasidan
    qidiradi — saytdan ro'yxatdan o'tganlar (manfiy ID) hisobga olinmaydi."""
    birinchi_soz = ism.strip().split()[0] if ism.strip() else ""
    if len(birinchi_soz) < 3:
        return {"oxshash": []}

    conn = _db()
    cur = conn.cursor()
    cur.execute("""
        SELECT full_name, role FROM users
        WHERE full_name ILIKE %s AND user_id > 0
        LIMIT 3
    """, (f"%{birinchi_soz}%",))
    natija = cur.fetchall()
    cur.close()
    conn.close()
    return {"oxshash": natija}


@app.post("/auth/royxat")
def yangi_royxat(sorov: RoyxatSorov):
    """Botsiz, to'g'ridan saytdan YANGI foydalanuvchi yaratadi.
    Telegram ID bilan TO'QNASHMASLIGI uchun MANFIY user_id beriladi
    (haqiqiy Telegram ID doim musbat bo'ladi)."""
    if sorov.rol not in RUXSAT_ETILGAN_ROLLAR:
        raise HTTPException(status_code=400, detail=f"Noto'g'ri rol: {sorov.rol}")
    if not sorov.ism.strip():
        raise HTTPException(status_code=400, detail="Ism kiritilmagan")

    conn = _db()
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tugilgan_sana DATE")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS maktab_raqami TEXT")

    cur.execute("SELECT user_id FROM google_hisob WHERE google_email=%s", (sorov.email,))
    if cur.fetchone():
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Bu email allaqachon ulangan — kirish orqali davom eting")

    cur.execute("SELECT MIN(user_id) AS eng_kichik FROM users WHERE user_id < 0")
    r = cur.fetchone()
    yangi_id = (r["eng_kichik"] - 1) if r and r["eng_kichik"] is not None else -1

    cur.execute(
        """INSERT INTO users(user_id, full_name, role, class, region, district, tugilgan_sana, maktab_raqami)
           VALUES(%s,%s,%s,%s,%s,%s,%s,%s)""",
        (yangi_id, sorov.ism.strip(), sorov.rol, sorov.sinf if sorov.rol == "oquvchi" else None,
         sorov.region, sorov.district, sorov.tugilgan_sana, sorov.maktab_raqami),
    )
    cur.execute(
        "INSERT INTO google_hisob(google_email, user_id) VALUES(%s,%s)",
        (sorov.email, yangi_id),
    )
    conn.commit()
    cur.close()
    conn.close()

    token = _jwt_yarat(yangi_id)
    return {"token": token, "user_id": yangi_id, "holat": "royxatdan otdi"}


@app.post("/auth/ulash")
def hisob_ulash(sorov: UlashSorov):
    """Google hisobini bot user_id'siga BIR MARTALIK, 15 daqiqa amal
    qiladigan kod orqali bog'laydi."""
    email, kod = sorov.email, sorov.kod
    conn = _db()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, ishlatildi,
               (yaratildi > NOW() - INTERVAL '15 minutes') AS hali_yangi
        FROM veb_ulash_kod WHERE kod=%s
    """, (kod,))
    r = cur.fetchone()
    if not r:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod noto'g'ri")
    if r["ishlatildi"]:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod allaqachon ishlatilgan")
    if not r["hali_yangi"]:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod muddati tugagan (15 daqiqa) — botdan yangisini oling")

    cur.execute("""
        INSERT INTO google_hisob (google_email, user_id) VALUES (%s,%s)
        ON CONFLICT (google_email) DO UPDATE SET user_id=EXCLUDED.user_id
    """, (email, r["user_id"]))
    cur.execute("UPDATE veb_ulash_kod SET ishlatildi=TRUE WHERE kod=%s", (kod,))
    conn.commit()
    cur.close()
    conn.close()

    token = _jwt_yarat(r["user_id"])
    return {"token": token, "holat": "ulandi"}


@app.get("/auth/men")
def joriy_foydalanuvchi(token: str):
    """Token orqali 'bu kim' ekanini tasdiqlaydi — frontend sahifa yuklanganda
    ishlatadi. Admin bo'lsa, is_admin=true qaytadi — frontend shunga qarab
    sinf-cheklovini olib tashlaydi (admin barcha sinflarni ko'rishi kerak)."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tugilgan_sana DATE")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS maktab_raqami TEXT")
    cur.execute(
        "SELECT user_id, full_name, role, class, region, district, tugilgan_sana, maktab_raqami FROM users WHERE user_id=%s",
        (user_id,),
    )
    r = cur.fetchone()
    if not r:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
    r["is_admin"] = cur.fetchone() is not None
    cur.close()
    conn.close()
    return r


# ═══════════════════════════════════════════════════════════
# TEST YECHISH (saytdan, botsiz)
# ═══════════════════════════════════════════════════════════

@app.get("/api/mavzular")
def mavzular_royxati(sinf: str = None):
    """Test yechish uchun mavjud fan/mavzularni qaytaradi — Fan → Sinf →
    Mavzu tartibida. Faqat generated_tests'da HAQIQATAN savoli bor
    mavzularni ko'rsatadi.

    MUHIM: grade ustuni ba'zan "3-4", "5-6" kabi ORALIQ ko'rinishida
    bo'ladi — bular ODDIY maktab sinfi EMAS, balki TO'GARAKNING O'Z
    maxsus guruhlari (masalan, matematik to'garak 3-4-sinf birgalikda
    o'qiydi). Shu sabab, bu yerda — ODDIY maktab testida — FAQAT sof
    raqamli sinflar (1, 2, ... 11) ko'rsatiladi, oraliqlar chiqarib
    tashlanadi. To'garak guruhlari alohida funksiyada ishlatiladi."""
    if sinf:
        sinf = sinf.replace("-sinf", "").strip()

    conn = _db()
    cur = conn.cursor()
    shart = "d.topic_code IN (SELECT DISTINCT topic_code FROM generated_tests) AND d.grade ~ '^[0-9]+$'"
    params = ()
    if sinf:
        shart += " AND d.grade = %s"
        params = (sinf,)
    cur.execute(f"""
        SELECT d.subject_code, d.subject_name, d.grade, d.topic_code,
               COALESCE(d.mavzu_name, d.bolim_name, d.bob_name, d.topic_code) AS nomi,
               (SELECT COUNT(*) FROM generated_tests g WHERE g.topic_code = d.topic_code) AS savol_soni
        FROM dts_tree d
        WHERE {shart} AND d.is_deleted = FALSE
        ORDER BY d.subject_code, d.grade, d.topic_code
    """, params)
    qatorlar = cur.fetchall()
    cur.close()
    conn.close()

    fanlar = {}
    for q in qatorlar:
        fkod = q["subject_code"] or "BOSHQA"
        if fkod not in fanlar:
            fanlar[fkod] = {"nom": q["subject_name"] or fkod, "qisqa": fkod, "sinflar": {}}

        skod = q["grade"]
        if skod not in fanlar[fkod]["sinflar"]:
            fanlar[fkod]["sinflar"][skod] = {"sinf": skod, "mavzular": []}
        fanlar[fkod]["sinflar"][skod]["mavzular"].append({
            "topic_code": q["topic_code"], "nomi": q["nomi"], "savol_soni": q["savol_soni"],
        })

    # sinflarni SONLI tartibda saralaymiz (1,2,...,11 — "11" harflar bo'yicha "2"dan oldin kelib qolmasin)
    natija = []
    for f in fanlar.values():
        f["sinflar"] = sorted(f["sinflar"].values(), key=lambda s: int(s["sinf"]))
        natija.append(f)
    return {"fanlar": natija}


@app.get("/api/test/{topic_code}")
def test_savollari(topic_code: str, soni: int = 10):
    """Berilgan mavzu bo'yicha tasodifiy savollarni qaytaradi."""
    conn = _db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d,
               question_type, is_latex, time_limit,
               COALESCE(image_file_id, image_url) AS rasm_id
        FROM generated_tests
        WHERE topic_code = %s
        ORDER BY RANDOM()
        LIMIT %s
    """, (topic_code, soni))
    savollar = cur.fetchall()
    cur.close()
    conn.close()

    if not savollar:
        raise HTTPException(status_code=404, detail="Bu mavzuda savol topilmadi")

    # Ko'rsatishdan oldin [ru]...[/ru] kabi teglarni va "10.0" formatini tozalaymiz
    for s in savollar:
        s["question"] = _matnni_tozala(s["question"])
        for maydon in ("option_a", "option_b", "option_c", "option_d"):
            s[maydon] = _matnni_tozala(s[maydon])

    # correct_answer va explanation FRONTENDGA yubormaymiz — bular javob
    # berilgandan KEYIN, /api/test/javob_tekshir orqali ochiladi
    return {"topic_code": topic_code, "savollar": savollar}


class BittaJavob(BaseModel):
    savol_id: int
    tanlangan: str


def _matnni_tozala(matn):
    """[ru]...[/ru] kabi teglarni olib tashlaydi, va "10.0" kabi butun
    sonlarni "10" ga soddalashtiradi — ham ko'rsatish, ham solishtirish
    uchun ishlatiladi."""
    if not matn:
        return matn
    tozalangan = re.sub(r"\[/?[a-zA-Z]+\]", "", matn).strip()
    if re.fullmatch(r"-?\d+\.0+", tozalangan):
        tozalangan = tozalangan.split(".")[0]
    return tozalangan


def _togri_harfni_top(option_a, option_b, option_c, option_d, correct_answer):
    """correct_answer ustuni ba'zan harf (A/B/C/D), ba'zan variantning
    TO'LIQ MATNI (masalan "20.0" yoki "[ru]родной язык[/ru]") ko'rinishida
    saqlangan — ikkalasini ham qamrab olib, HAQIQIY to'g'ri harfni
    aniqlaydi. Teglar va sonlar formatidagi farqlar e'tiborga olinmaydi."""
    ca = _matnni_tozala((correct_answer or "").strip())
    if ca.upper() in ("A", "B", "C", "D"):
        return ca.upper()
    variantlar = {"A": option_a, "B": option_b, "C": option_c, "D": option_d}
    ca_kichik = ca.lower()
    for harf, matn in variantlar.items():
        if (_matnni_tozala(matn) or "").lower() == ca_kichik:
            return harf
    return None


@app.post("/api/test/javob_tekshir")
def javob_tekshir(j: BittaJavob):
    """Bitta savolga berilgan javobni DARHOL tekshiradi — to'g'ri javob
    va tushuntirishni shu yerda ochadi (foydalanuvchi javob bergandan
    keyin, savol ko'rsatilganda EMAS — aks holda oldindan ko'rinib qolardi)."""
    conn = _db()
    cur = conn.cursor()
    cur.execute("""SELECT option_a, option_b, option_c, option_d, correct_answer, explanation
                   FROM generated_tests WHERE id=%s""", (j.savol_id,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    if not r:
        raise HTTPException(status_code=404, detail="Savol topilmadi")

    togri_harf = _togri_harfni_top(r["option_a"], r["option_b"], r["option_c"], r["option_d"], r["correct_answer"])
    togri = (j.tanlangan or "").strip().upper() == togri_harf
    return {"togrimi": togri, "togri_javob": togri_harf, "tushuntirish": r["explanation"]}


@app.get("/api/rasm/{file_id}")
async def rasm_proxy(file_id: str):
    """Telegram'da saqlangan rasmni saytda ko'rsatish uchun oraliq xizmat —
    Telegram file_id'lar to'g'ridan-to'g'ri URL emas, faqat bot tokeni
    orqali ochiladi."""
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot tokeni sozlanmagan")
    if file_id.startswith("http"):
        # Ba'zi eski yozuvlarda image_url to'g'ridan URL bo'lishi mumkin
        return RedirectResponse(file_id)
    async with httpx.AsyncClient() as client:
        meta = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                                 params={"file_id": file_id})
        meta_data = meta.json()
        if not meta_data.get("ok"):
            raise HTTPException(status_code=404, detail="Rasm topilmadi")
        file_path = meta_data["result"]["file_path"]
        img = await client.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}")
        return Response(content=img.content, media_type="image/jpeg")


class JavobItem(BaseModel):
    savol_id: int
    tanlangan: str


class TestNatijaSorov(BaseModel):
    token: str
    topic_code: str
    javoblar: list[JavobItem]


@app.post("/api/test/natija")
def test_natijasini_saqla(sorov: TestNatijaSorov):
    """Test yakunlanganda — har javobni backendda tekshiradi, foizni
    hisoblaydi, learned_topics'ga yozadi (bot ishlatgan JADVALNING O'ZIGA —
    shuning uchun dashboard darhol yangilanadi)."""
    user_id = _jwt_tekshir(sorov.token)

    conn = _db()
    cur = conn.cursor()

    savol_idlar = [j.savol_id for j in sorov.javoblar]
    cur.execute(
        """SELECT id, option_a, option_b, option_c, option_d, correct_answer
           FROM generated_tests WHERE id = ANY(%s)""",
        (savol_idlar,),
    )
    togri_harflar = {
        r["id"]: _togri_harfni_top(r["option_a"], r["option_b"], r["option_c"], r["option_d"], r["correct_answer"])
        for r in cur.fetchall()
    }

    togri_soni = 0
    for j in sorov.javoblar:
        togri_harf = togri_harflar.get(j.savol_id)
        if togri_harf and (j.tanlangan or "").strip().upper() == togri_harf:
            togri_soni += 1

    jami = len(sorov.javoblar)
    foiz = round((togri_soni / jami) * 100) if jami else 0

    cur.execute("""
        INSERT INTO learned_topics(user_id, topic_code, score, repeat_count, learned_at, next_repeat)
        VALUES(%s,%s,%s,1,NOW(),CURRENT_DATE + INTERVAL '7 days')
        ON CONFLICT (user_id, topic_code) DO UPDATE SET
            score = EXCLUDED.score,
            repeat_count = learned_topics.repeat_count + 1,
            learned_at = NOW(),
            next_repeat = CURRENT_DATE + INTERVAL '7 days'
    """, (user_id, sorov.topic_code, foiz))
    conn.commit()
    cur.close()
    conn.close()

    return {"togri": togri_soni, "jami": jami, "foiz": foiz}


# ═══════════════════════════════════════════════════════════
# SAYTDAN BOTGA ULASH — teskari yo'nalish
# (Saytda ro'yxatdan o'tgan, botni ham ishlatmoqchi bo'lganlar uchun)
# ═══════════════════════════════════════════════════════════

@app.post("/auth/sayt_kod_yarat")
def sayt_kod_yarat(token: str):
    """Saytda kirgan foydalanuvchi uchun BOTGA ulash kodi yaratadi.
    Bot bu kodni ko'rib, shu web_user_id'dagi ma'lumotni haqiqiy
    Telegram user_id'ga ko'chiradi."""
    user_id = _jwt_tekshir(token)

    kod = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    conn = _db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS sayt_ulash_kod(
        kod TEXT PRIMARY KEY, web_user_id BIGINT REFERENCES users(user_id),
        yaratildi TIMESTAMP DEFAULT NOW(), ishlatildi BOOLEAN DEFAULT FALSE)""")
    cur.execute("INSERT INTO sayt_ulash_kod(kod, web_user_id) VALUES(%s,%s)", (kod, user_id))
    conn.commit()
    cur.close()
    conn.close()

    return {"kod": kod}


# ═══════════════════════════════════════════════════════════
# O'QITUVCHI — baholash
# ═══════════════════════════════════════════════════════════

@app.get("/api/oqituvchi/togaraklar")
def oqituvchi_togaraklari(token: str):
    """O'qituvchining o'ziga tegishli barcha to'garaklarini qaytaradi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nomi, fan, max_talaba,
               (SELECT COUNT(*) FROM togarak_azolar WHERE togarak_id=togaraklar.id AND aktiv=TRUE) AS azo_soni
        FROM togaraklar
        WHERE teacher_id=%s AND aktiv=TRUE
        ORDER BY nomi
    """, (user_id,))
    natija = cur.fetchall()
    cur.close()
    conn.close()
    return {"togaraklar": natija}


@app.get("/api/oqituvchi/togarak/{togarak_id}/azolar")
def togarak_azolari(togarak_id: int, token: str):
    """Berilgan to'garakdagi o'quvchilarni, ularning OXIRGI bahosi bilan
    qaytaradi. Faqat shu to'garakning o'z o'qituvchisi ko'ra oladi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()

    cur.execute("SELECT teacher_id FROM togaraklar WHERE id=%s", (togarak_id,))
    r = cur.fetchone()
    if not r or r["teacher_id"] != user_id:
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Bu to'garak sizga tegishli emas")

    cur.execute("""
        SELECT u.user_id, u.full_name,
               (SELECT baho FROM togarak_baholar tb
                WHERE tb.togarak_id=%s AND tb.user_id=u.user_id
                ORDER BY tb.created_at DESC LIMIT 1) AS oxirgi_baho
        FROM togarak_azolar ta
        JOIN users u ON u.user_id = ta.user_id
        WHERE ta.togarak_id=%s AND ta.aktiv=TRUE
        ORDER BY u.full_name
    """, (togarak_id, togarak_id))
    azolar = cur.fetchall()
    cur.close()
    conn.close()
    return {"azolar": azolar}


class BahoSorov(BaseModel):
    token: str
    togarak_id: int
    user_id: int
    baho: int
    izoh: str = None


@app.post("/api/oqituvchi/baho_qoy")
def baho_qoy(sorov: BahoSorov):
    """Bitta o'quvchiga baho qo'yadi. Faqat to'garakning o'z o'qituvchisi,
    va faqat o'sha to'garak a'zosiga baho qo'ya oladi."""
    teacher_id = _jwt_tekshir(sorov.token)
    conn = _db()
    cur = conn.cursor()

    cur.execute("SELECT teacher_id FROM togaraklar WHERE id=%s", (sorov.togarak_id,))
    r = cur.fetchone()
    if not r or r["teacher_id"] != teacher_id:
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Bu to'garak sizga tegishli emas")

    cur.execute(
        "SELECT 1 FROM togarak_azolar WHERE togarak_id=%s AND user_id=%s AND aktiv=TRUE",
        (sorov.togarak_id, sorov.user_id),
    )
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Bu o'quvchi shu to'garak a'zosi emas")

    if not (0 <= sorov.baho <= 100):
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Baho 0-100 oralig'ida bo'lishi kerak")

    cur.execute(
        """INSERT INTO togarak_baholar(togarak_id, user_id, baho, izoh, teacher_id)
           VALUES(%s,%s,%s,%s,%s)""",
        (sorov.togarak_id, sorov.user_id, sorov.baho, sorov.izoh, teacher_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "saqlandi"}


# ═══════════════════════════════════════════════════════════
# PROFIL — tahrirlash va rol almashtirish
# ═══════════════════════════════════════════════════════════

class ProfilYangilash(BaseModel):
    token: str
    full_name: str = None
    region: str = None
    district: str = None
    tugilgan_sana: str = None
    maktab_raqami: str = None


@app.put("/api/profil")
def profil_yangila(sorov: ProfilYangilash):
    """Foydalanuvchi o'z profilini yangilaydi."""
    user_id = _jwt_tekshir(sorov.token)
    if sorov.full_name is not None and not sorov.full_name.strip():
        raise HTTPException(status_code=400, detail="Ism bo'sh bo'lishi mumkin emas")

    conn = _db()
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tugilgan_sana DATE")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS maktab_raqami TEXT")

    maydonlar = []
    qiymatlar = []
    if sorov.full_name is not None:
        maydonlar.append("full_name=%s")
        qiymatlar.append(sorov.full_name.strip())
    if sorov.region is not None:
        maydonlar.append("region=%s")
        qiymatlar.append(sorov.region.strip())
    if sorov.district is not None:
        maydonlar.append("district=%s")
        qiymatlar.append(sorov.district.strip())
    if sorov.tugilgan_sana is not None:
        maydonlar.append("tugilgan_sana=%s")
        qiymatlar.append(sorov.tugilgan_sana)
    if sorov.maktab_raqami is not None:
        maydonlar.append("maktab_raqami=%s")
        qiymatlar.append(sorov.maktab_raqami.strip())

    if not maydonlar:
        cur.close()
        conn.close()
        return {"holat": "ozgarish_yoq"}

    qiymatlar.append(user_id)
    cur.execute(f"UPDATE users SET {', '.join(maydonlar)} WHERE user_id=%s", qiymatlar)
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "saqlandi"}


class RolOzgartirish(BaseModel):
    token: str
    yangi_rol: str
    tasdiqlayman: bool = False


RUXSAT_ETILGAN_ROLLAR2 = {"oquvchi", "ota-ona", "oqituvchi"}


@app.put("/api/rol_ozgartir")
def rol_ozgartir(sorov: RolOzgartirish):
    """Foydalanuvchi rolini o'zgartiradi. tasdiqlayman=False bo'lsa,
    hozirgi va yangi rolni qaytarib, TASDIQ so'raydi — chunki rol
    o'zgarishi katta ta'sir qiladi (masalan o'qituvchi guruhlariga
    kirish huquqi, yoki bilim ko'rsatkichlari)."""
    user_id = _jwt_tekshir(sorov.token)
    if sorov.yangi_rol not in RUXSAT_ETILGAN_ROLLAR2:
        raise HTTPException(status_code=400, detail=f"Noto'g'ri rol: {sorov.yangi_rol}")

    conn = _db()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE user_id=%s", (user_id,))
    r = cur.fetchone()
    if not r:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    hozirgi_rol = r["role"]
    if hozirgi_rol == sorov.yangi_rol:
        cur.close()
        conn.close()
        return {"holat": "ozgarish_yoq"}

    if not sorov.tasdiqlayman:
        cur.close()
        conn.close()
        return {"holat": "tasdiq_kerak", "hozirgi_rol": hozirgi_rol, "yangi_rol": sorov.yangi_rol}

    cur.execute("UPDATE users SET role=%s WHERE user_id=%s", (sorov.yangi_rol, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "saqlandi", "yangi_rol": sorov.yangi_rol}
