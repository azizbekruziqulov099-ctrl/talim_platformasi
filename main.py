"""main.py — SamTM Ta'lim veb-sayt backend'i (v3).

Haqiqiy jadvallarga ulangan + Google orqali kirish (OAuth) qo'shildi.
"""
import os
import secrets
import string
import httpx
import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

DATABASE_URL = os.getenv("DATABASE_URL", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
JWT_MAXFIY_KALIT = os.getenv("JWT_MAXFIY_KALIT", "")
BAZA_URL = os.getenv("BAZA_URL", "https://talimplatformasi-production.up.railway.app")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://talimplatformasi-production.up.railway.app")
REDIRECT_URI = f"{BAZA_URL}/auth/google/callback"

app = FastAPI(title="SamTM Ta'lim API")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"],
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
    ishlatadi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    cur.execute("SELECT user_id, full_name, role FROM users WHERE user_id=%s", (user_id,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    if not r:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return r
