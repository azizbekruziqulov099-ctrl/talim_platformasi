"""SamTM V19.2 platform backend.

Haqiqiy jadvallar, Google OAuth, eski Excel import va V19.2 dagi
o'qituvchi-asosli yuklama bilan bir paketda ishlaydi.
"""
import os
import asyncio
import re
import io
import json
import math
import base64
import hashlib
import secrets
import string
import threading
import unicodedata
from collections import OrderedDict
from urllib.parse import urlencode
import httpx
import psycopg2
import psycopg2.extras
import psycopg2.pool
from typing import Optional
from datetime import date, datetime, timedelta, timezone
from jose import jwt, JWTError
from fastapi import FastAPI, Header, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response, StreamingResponse
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv("DATABASE_URL", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
JWT_MAXFIY_KALIT = os.getenv("JWT_MAXFIY_KALIT", "")
BAZA_URL = os.getenv("BAZA_URL", "https://talimplatformasi-production.up.railway.app")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://talimplatformasi-production.up.railway.app")
REDIRECT_URI = f"{BAZA_URL}/auth/google/callback"
SAMTM_RELEASE = "samtm-teacher-first-smart-timetable-v19.2"
SAMTM_PACKAGE_REVISION = "all-14-sections-updated"

if len(JWT_MAXFIY_KALIT.encode("utf-8")) < 32:
    raise RuntimeError(
        "JWT_MAXFIY_KALIT o'rnatilmagan yoki juda qisqa. "
        "Kamida 32 baytli tasodifiy sir kiriting."
    )

app = FastAPI(title="SamTM Ta'lim API", version="19.2")
FRONTEND_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("FRONTEND_URLS", FRONTEND_URL).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024, compresslevel=5)


@app.exception_handler(psycopg2.Error)
async def postgres_xavfsiz_xato_javobi(request: Request, exc: psycopg2.Error):
    """Expired V17 workspaces are readable but every mutation is DB-guarded.

    PostgreSQL SQLSTATE 25006 is translated to a stable frontend contract;
    other database details are deliberately not exposed to the client.
    """
    if getattr(exc, "pgcode", None) == "25006":
        return JSONResponse(
            status_code=423,
            content={
                "detail": {
                    "code": "ORGANIZATION_READ_ONLY",
                    "message": (
                        "30 kunlik sinov tugagan. Ma'lumotlar saqlangan, "
                        "yozishni davom ettirish uchun muassasani faollashtiring."
                    ),
                    "activation_price_uzs": 200_000,
                }
            },
        )
    error_id = secrets.token_hex(4)
    print(
        f"[DB-ERROR {error_id}] path={request.url.path} "
        f"pgcode={getattr(exc, 'pgcode', None)} "
        f"type={type(exc).__name__} detail={str(exc).strip()}",
        flush=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "code": "DATABASE_ERROR",
                "message": "Baza so'rovida xato yuz berdi. Maktab sahifasi xavfsiz rejimda davom etadi.",
                "error_id": error_id,
                "path": request.url.path,
            }
        },
    )


@app.get("/api/versiya")
def versiya():
    """Deploy tekshiruvi uchun вЂ” hech qanday token/parametr kerak
    emas, brauzerda to'g'ridan-to'g'ri ochiladi."""
    return {
        "versiya": SAMTM_RELEASE,
        "package_revision": SAMTM_PACKAGE_REVISION,
        "all_14_sections_updated": True,
        "previous_version": "samtm-group-matrix-v19.1",
        "modules": [
            "kindergarten-v2", "school-v2", "learning-center-v2",
            "institute-v1",
        ],
        "module_versions": {
            "learning_center": "learning-center-v2-secure-v14",
            "institute": "faculty-screen-direct-student-xls-import-v20-rev66",
            "teacher_tools": "teacher-analytics-repetitor-v16",
            "organization_trials": "private-trial-wallet-v17",
            "test_games": "fast-feedback-v18.22",
            "test_import": "excel-auto-subject-grade-scoped-v18.16",
            "learning_path": "balanced-golden-subject-path-v18.21",
            "voice": "stream-cache-visible-state-v18.22",
            "institution_security": "admin-password-365-day-archive-v18.24",
            "admin_school_creation": "bulk-class-multi-group-v18.36",
            "employee_import": "same-sheet-class-group-hours-v19.1",
            "student_groups": "bulk-manual-groups-v18.34",
            "performance": "modular-runtime-cache-pgbouncer-v19.0",
            "frontend_chunks": "lazy-test-admin-tools-v18.37",
            "class_group_sets": "simultaneous-gender-alphabet-manual-v18.36",
            "school_timetable": "safe-swap-recommendation-manual-auto-v19.2",
            "school_workspace": "teacher-subject-class-group-hours-v19.2",
            "teacher_load_entry": "manual-teacher-create-load-compact-matrix-v19.2",
            "manual_teacher_entry": "teacher-subject-class-group-hours-one-screen-v19.2",
            "schedule_conflicts": "hard-teacher-parallel-guard-v19.2",
            "written_answers": "language-aware-exact-hints-v18.8",
        },
    }


@app.get("/api/admin/rasm_diagnostika")
def rasm_diagnostika(token: str):
    """Bazaning HAQIQIY holatini to'g'ridan-to'g'ri ko'rsatadi вЂ” import
    ekrani/frontend bilan bog'liq bo'lmagan, to'g'ridan-to'g'ri
    tekshiruv. So'nggi qo'shilgan 15 ta yozuvni AYNAN qanday
    saqlanganini (rasm bor-yo'qligi, image_url qiymati) ko'rsatadi."""
    _admin_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS jami FROM generated_tests")
    jami = cur.fetchone()["jami"]
    cur.execute("SELECT COUNT(*) AS soni FROM generated_tests WHERE rasm_malumot IS NOT NULL")
    rasm_malumotli = cur.fetchone()["soni"]
    cur.execute("SELECT COUNT(*) AS soni FROM generated_tests WHERE image_url IS NOT NULL AND image_url != ''")
    image_urlli = cur.fetchone()["soni"]
    cur.execute("""
        SELECT id, topic_code, LEFT(question, 50) AS savol_qisqa,
               (rasm_malumot IS NOT NULL) AS rasm_bormi, image_url
        FROM generated_tests ORDER BY id DESC LIMIT 15
    """)
    songgi_yozuvlar = cur.fetchall()
    cur.close()
    conn.close()
    return {
        "jami_testlar": jami,
        "rasm_malumotli_soni": rasm_malumotli,
        "image_urlli_soni": image_urlli,
        "songgi_15_yozuv": songgi_yozuvlar,
    }


@app.get("/api/admin/mavzu_kod_moslik")
def mavzu_kod_moslik(token: str, sinf: str, fan: str):
    """"Mavzular" ekranida "Test yo'q" ko'rinsa-yu, aslida test import
    qilingan bo'lsa вЂ” buning sababini TO'G'RIDAN-TO'G'RI ko'rsatadi:
    dts_tree'dagi (Mavzular) HAR BIR kichik-darajadagi topic_code'ni,
    generated_tests'dagi (Testlar) HAR BIR topic_code bilan yonma-yon
    solishtiradi вЂ” ikkalasida ham bor, faqat dts_tree'da bor, yoki
    faqat generated_tests'da bor (ya'ni "yetim" test) вЂ” HAMMASI
    ochiq-oydin ko'rinadi."""
    _admin_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    cur.execute("""
        SELECT topic_code, bob_name, bolim_name, mavzu_name, kichik_name
        FROM dts_tree WHERE grade=%s AND UPPER(subject_name)=UPPER(%s) AND is_deleted=FALSE
        ORDER BY topic_code
    """, (sinf, fan))
    dts_qatorlar = cur.fetchall()
    dts_kodlari = {r["topic_code"] for r in dts_qatorlar}

    # generated_tests'da shu sinf+fan PREFIKSI bilan boshlanadigan
    # (masalan "5-03-") barcha topic_code'lar вЂ” dts_tree'da bormi-yo'qmi,
    # ikkalasi ham.
    cur.execute("SELECT subject_code FROM dts_tree WHERE grade=%s AND UPPER(subject_name)=UPPER(%s) LIMIT 1", (sinf, fan))
    r = cur.fetchone()
    prefiks = f"{sinf}-{r['subject_code']}-" if r else None

    testli_kodlar = {}
    if prefiks:
        cur.execute("""
            SELECT topic_code, COUNT(*) AS soni FROM generated_tests
            WHERE topic_code LIKE %s GROUP BY topic_code
        """, (f"{prefiks}%",))
        testli_kodlar = {r["topic_code"]: r["soni"] for r in cur.fetchall()}

    natija = []
    for r in dts_qatorlar:
        natija.append({
            "topic_code": r["topic_code"],
            "mavzu_nomi": r["mavzu_name"] or r["kichik_name"] or r["bolim_name"] or r["bob_name"],
            "dts_tree_da_bormi": True,
            "test_soni": testli_kodlar.get(r["topic_code"], 0),
        })
    yetim_testlar = [
        {"topic_code": kod, "test_soni": soni, "dts_tree_da_bormi": False}
        for kod, soni in testli_kodlar.items() if kod not in dts_kodlari
    ]

    cur.close()
    conn.close()
    return {"prefiks": prefiks, "mavzular": natija, "yetim_testlar": yetim_testlar}


_DB_POOL = None
_DB_POOL_LOCK = threading.Lock()
_DB_POOL_MAX = max(2, int(os.getenv("DB_POOL_MAX", "10")))
_DB_POOL_WAIT_SECONDS = max(1.0, float(os.getenv("DB_POOL_WAIT_SECONDS", "2")))
_DB_POOL_SLOTS = threading.BoundedSemaphore(_DB_POOL_MAX)
_DB_STATEMENT_TIMEOUT_MS = max(5_000, int(os.getenv("DB_STATEMENT_TIMEOUT_MS", "60000")))


def _db_pool_ol():
    """Har worker uchun bitta xavfsiz, thread-safe PostgreSQL havuzi."""
    global _DB_POOL
    if _DB_POOL is not None:
        return _DB_POOL
    with _DB_POOL_LOCK:
        if _DB_POOL is None:
            _DB_POOL = psycopg2.pool.ThreadedConnectionPool(
                1,
                _DB_POOL_MAX,
                DATABASE_URL,
                cursor_factory=psycopg2.extras.RealDictCursor,
                connect_timeout=5,
                application_name=os.getenv("DB_APPLICATION_NAME", "samtm-v19"),
                options=(
                    f"-c statement_timeout={_DB_STATEMENT_TIMEOUT_MS} "
                    "-c idle_in_transaction_session_timeout=30000 "
                    "-c lock_timeout=10000"
                ),
            )
    return _DB_POOL


class _DbUlanish:
    """Psycopg2 ulanishiga o'xshaydi, ammo close() uni havuzga qaytaradi.

    Eski endpointlarning hammasi ``conn.close()`` ishlatadi. Shu adapter
    ularning kodini o'zgartirmasdan havuzni xavfsiz qiladi. Endpoint xato
    bilan ``close()`` qatoriga yetmasa ham CPython lokal obyektni bo'shatishi
    bilan ``__del__`` ulanishni qaytaradi; qaytarishdan oldin ochiq tranzaksiya
    rollback qilinadi. Shuning uchun avvalgi "20 ta ulanish abadiy band"
    muammosi qaytmaydi.
    """

    def __init__(self, raw_conn, pool):
        self._raw_conn = raw_conn
        self._pool = pool
        self._yopildi = False

    def __getattr__(self, nom):
        return getattr(self._raw_conn, nom)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            try:
                self._raw_conn.rollback()
            except Exception:
                pass
        self.close()
        return False

    def close(self):
        if self._yopildi:
            return
        self._yopildi = True
        raw_conn = self._raw_conn
        yaroqsiz = bool(getattr(raw_conn, "closed", True))
        if not yaroqsiz:
            try:
                # SELECT ham tranzaksiya ochadi. Havuzdagi keyingi so'rovga
                # eski tranzaksiya/lock o'tmasligi uchun doim tozalaymiz.
                raw_conn.rollback()
            except Exception:
                yaroqsiz = True
        try:
            self._pool.putconn(raw_conn, close=yaroqsiz)
        except Exception:
            try:
                raw_conn.close()
            except Exception:
                pass
        finally:
            _DB_POOL_SLOTS.release()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


def _db():
    """Cheklangan kutishli ulanish: baza band bo'lsa sayt osilib qolmaydi."""
    try:
        asyncio.get_running_loop()
        async_event_loop_ichida = True
    except RuntimeError:
        async_event_loop_ichida = False
    # async endpoint ichida threading.Semaphore kutishi butun event-loopni
    # ushlab qoladi. Shu holatda darhol band javobi beramiz; FastAPI'ning
    # worker threadidagi oddiy endpoint esa qisqa navbatda kutishi mumkin.
    kutish = 0 if async_event_loop_ichida else _DB_POOL_WAIT_SECONDS
    if not _DB_POOL_SLOTS.acquire(timeout=kutish):
        raise HTTPException(
            status_code=503,
            detail="Baza hozir band. Bir necha soniyadan keyin qayta urinib ko'ring.",
        )
    try:
        raw_conn = _db_pool_ol().getconn()
        if raw_conn.closed:
            _db_pool_ol().putconn(raw_conn, close=True)
            raw_conn = _db_pool_ol().getconn()
        return _DbUlanish(raw_conn, _db_pool_ol())
    except Exception:
        _DB_POOL_SLOTS.release()
        raise


@app.on_event("shutdown")
def _db_poolni_yopish():
    global _DB_POOL
    if _DB_POOL is not None:
        _DB_POOL.closeall()
        _DB_POOL = None


# Fan kodiga qarab dashboard rangi вЂ” yangi fan qo'shilsa shu ro'yxatga qo'shiladi
FAN_RANG = {
    "MAT": "#C89B3C", "TIL": "#2D8B8B", "ADB": "#8B5FBF",
    "TAB": "#B0553A", "RUS": "#4A7C9E", "ENG": "#7C9E4A",
}


@app.get("/")
def salomat():
    return {"holat": "ishlayapti"}


@app.get("/api/bola/{bola_id}/bilim")
def bola_bilimi(bola_id: int, sinf: str = None):
    """Bolaning fan-mavzu bo'yicha bilim darajasi вЂ” FAQAT bolaning O'ZI
    sinfiga tegishli mavzular bo'yicha. sinf berilmasa, avtomatik bola
    profilidagi class ustunidan olinadi. MUHIM: agar bola profilida
    sinf umuman ko'rsatilmagan bo'lsa вЂ” BARCHA sinflarni ARALASH
    ko'rsatish O'RNIGA bo'sh natija qaytariladi (aks holda 1-sinf
    bolasiga Algebra kabi butunlay boshqa sinflarning fanlari chiqib
    ketardi, chunki sinfsiz cheklov qo'yib bo'lmaydi)."""
    try:
        conn = _db()
        cur = conn.cursor()

        cur.execute("SELECT full_name, class FROM users WHERE user_id=%s", (bola_id,))
        bola = cur.fetchone()
        if not bola:
            raise HTTPException(status_code=404, detail="Bola topilmadi")

        if not sinf:
            if not bola["class"]:
                cur.close()
                conn.close()
                return {
                    "bola": {"ism": bola["full_name"]}, "umumiy_foiz": 0, "fanlar": [],
                    "jami_mavzu": 0, "otilgan_mavzu": 0, "sinf_sozlanmagan": True,
                }
            sinf = str(bola["class"]).replace("-sinf", "").strip()

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
        jami_mavzu_soni = len({q["topic_code"] for q in qatorlar})
        otilgan_mavzu_soni = len({q["topic_code"] for q in qatorlar if q["score"] is not None})

        return {
            "bola": {"ism": bola["full_name"]}, "umumiy_foiz": umumiy, "fanlar": natija_royxat,
            "jami_mavzu": jami_mavzu_soni, "otilgan_mavzu": otilgan_mavzu_soni,
        }
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


@app.get("/api/oquvchi/ota_onalarim")
def oquvchi_ota_onalarim(token: str):
    """O'quvchining O'ZIGA ulangan barcha ota-onalari ro'yxati вЂ”
    ota_farzandlari'ning aksi (o'quvchi profilida 'kimlar allaqachon
    ulangan' ko'rsatish uchun)."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _users_profil_rasm_ustunlari(cur)
    cur.execute("""
        SELECT u.user_id, u.full_name, (u.profil_rasm IS NOT NULL) AS rasm_bormi FROM parent_child pc
        JOIN users u ON u.user_id = pc.parent_id
        WHERE pc.child_id = %s
    """, (user_id,))
    r = cur.fetchall()
    cur.close(); conn.close()
    return {"ota_onalar": r}



# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# GOOGLE ORQALI KIRISH (OAuth)
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

_kabutar_auth_service = None


def _jwt_yarat(user_id: int) -> str:
    """Create a 30-day revocable session; shared wrappers retain module compatibility."""
    if _kabutar_auth_service is None:
        raise HTTPException(status_code=503, detail="Kirish xizmati hali tayyor emas")
    return _kabutar_auth_service.issue_session(user_id, "google")


import contextvars as _contextvars
# Joriy HTTP metodi (middleware yozadi). Admin "ko'rish rejimi" tokeni bilan
# faqat o'qish (GET/HEAD/OPTIONS) so'rovlariga ruxsat beriladi.
_JORIY_HTTP_METOD = _contextvars.ContextVar("samtm_joriy_http_metod", default="GET")
_KABUTAR_AUTH_REQUEST_CACHE = _contextvars.ContextVar("kabutar_auth_request_cache", default=None)


@app.middleware("http")
async def _v2252_http_metodni_yoz(request, call_next):
    token_ctx = _JORIY_HTTP_METOD.set(str(request.method or "GET").upper())
    auth_cache_ctx = _KABUTAR_AUTH_REQUEST_CACHE.set({})
    try:
        return await call_next(request)
    finally:
        _KABUTAR_AUTH_REQUEST_CACHE.reset(auth_cache_ctx)
        _JORIY_HTTP_METOD.reset(token_ctx)


def _jwt_korish_tokeni_yarat(admin_id: int, target_user_id: int, yozish: bool = False) -> str:
    """Admin uchun 90 daqiqalik вЂњko'rish rejimiвЂќ tokeni. yozish=False вЂ” faqat ko'rish;
    yozish=True вЂ” SINOV rejimi: o'sha rol qila oladigan hamma amalni bajarish mumkin
    (sayt hali ishga tushmaganda funksiyalarni sinash uchun)."""
    payload = {
        "user_id": int(target_user_id),
        "admin_korish": int(admin_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=90 if not yozish else 240),
    }
    if yozish:
        payload["yozish"] = 1
    return jwt.encode(payload, JWT_MAXFIY_KALIT, algorithm="HS256")


def _jwt_tekshir(token: str) -> int:
    """Validate purpose and revocable session once per HTTP request."""
    if not isinstance(token, str) or not token:
        raise HTTPException(status_code=401, detail="Kirish tokeni yuborilmadi")
    cache = _KABUTAR_AUTH_REQUEST_CACHE.get()
    cache_key = (token, _JORIY_HTTP_METOD.get())
    if cache is not None and cache_key in cache:
        return cache[cache_key]
    try:
        payload = jwt.decode(token, JWT_MAXFIY_KALIT, algorithms=["HS256"], options={"require_exp": True})
    except (JWTError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Sessiya eskirgan, qaytadan kiring")
    if payload.get("purpose") not in (None, "access"):
        raise HTTPException(status_code=401, detail="Bu token kirish sessiyasi emas")
    if not isinstance(payload.get("user_id"), int) or isinstance(payload.get("user_id"), bool):
        raise HTTPException(status_code=401, detail="Kirish tokeni noto'g'ri")
    if payload.get("admin_korish") and set(payload) - {"user_id", "exp", "admin_korish", "yozish"}:
        raise HTTPException(status_code=401, detail="Ko'rish tokeni noto'g'ri")
    if payload.get("admin_korish") and not payload.get("yozish") and _JORIY_HTTP_METOD.get() not in ("GET", "HEAD", "OPTIONS"):
        raise HTTPException(
            status_code=403,
            detail="Admin ko'rish rejimi: bu oynada hech narsa o'zgartirilmaydi (faqat ko'rish).",
        )
    if _kabutar_auth_service is None:
        raise HTTPException(status_code=503, detail="Kirish xizmati hali tayyor emas")
    user_id = _kabutar_auth_service.verify_session(token, payload)
    if cache is not None:
        cache[cache_key] = user_id
    return user_id


def _jwt_header_yoki_query(
    token: Optional[str],
    authorization: Optional[str],
) -> str:
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value.strip():
            return value.strip()
    if token:
        return token
    raise HTTPException(status_code=401, detail="Kirish tokeni yuborilmadi")


OAUTH_STATE_COOKIE = "__Host-google-oauth-state"
OAUTH_STATE_SECONDS = 10 * 60
# Railway frontend va backend hostlari Public Suffix List sabab cross-site:
# callback'da qo'yilgan SameSite=Lax ticket cookie frontend fetch'ida yuborilmaydi,
# SameSite=None esa third-party cookie sifatida bloklanishi mumkin. Shu sabab
# ticket URL fragmentida (server/referrer'ga bormaydi) berilib, frontend uni
# darhol o'chiradi va POST body'da almashtiradi. Stateless ticket nusxasi
# o'g'irlangan holatda barcha workerlar bo'ylab mutlaq bir martalikni DB/Redis'siz
# kafolatlab bo'lmaydi; replay oynasi ko'pi bilan 60 soniya.
OAUTH_TICKET_SECONDS = 60
# Tasdiqlangan Google emailini ulash/ro'yxat formasiga bog'laydi; odamga formani
# to'ldirish uchun yetarli, lekin umumiy sessiyadan ancha qisqa muddat.
OAUTH_REGISTRATION_GRANT_SECONDS = 15 * 60


def _oauth_imzolangan_token(purpose: str, seconds: int, **claims) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "purpose": purpose,
        "iat": now,
        "exp": now + timedelta(seconds=seconds),
        "jti": secrets.token_urlsafe(18),
        **claims,
    }
    return jwt.encode(payload, JWT_MAXFIY_KALIT, algorithm="HS256")


def _oauth_token_och(token: Optional[str], purpose: str) -> Optional[dict]:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            JWT_MAXFIY_KALIT,
            algorithms=["HS256"],
            options={"require_exp": True},
        )
    except JWTError:
        return None
    if payload.get("purpose") != purpose or not payload.get("jti"):
        return None
    return payload


def _google_registration_tekshir(grant: Optional[str], email: str) -> dict:
    payload = _oauth_token_och(grant, "google_registration_grant")
    grant_email = str(payload.get("email") if payload else "").strip().lower()
    requested_email = str(email or "").strip().lower()
    emails_match = bool(grant_email and requested_email) and secrets.compare_digest(
        grant_email.encode("utf-8"),
        requested_email.encode("utf-8"),
    )
    if not payload or payload.get("outcome") != "registration" or not emails_match:
        raise HTTPException(
            status_code=401,
            detail="Google email tasdig'i yo'q, noto'g'ri yoki eskirgan вЂ” qaytadan kiring",
        )
    return payload


def _oauth_cookie_qoy(response: Response, key: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )


def _oauth_cookie_ochir(response: Response, key: str) -> None:
    response.delete_cookie(
        key=key,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax",
    )


def _oauth_frontend_redirect(xato: Optional[str] = None, ticket: Optional[str] = None) -> RedirectResponse:
    # Fragment HTTP so'roviga, server logiga yoki Referer sarlavhasiga bormaydi.
    # Unda faqat 60 soniyalik signed ticket bor; JWT/email/ism alohida chiqmaydi.
    fragment = urlencode({"oauth_xato": xato}) if xato else urlencode({"oauth_ticket": ticket})
    response = RedirectResponse(f"{FRONTEND_URL.rstrip('/')}/#{fragment}")
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    _oauth_cookie_ochir(response, OAUTH_STATE_COOKIE)
    return response


@app.get("/auth/google/login")
def google_login(intent: Optional[str] = None):
    """Google'ga state va PKCE S256 bilan xavfsiz yo'naltiradi."""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google kirish hali sozlanmagan")

    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    state_cookie = _oauth_imzolangan_token(
        "google_oauth_state",
        OAUTH_STATE_SECONDS,
        state=state,
        verifier=verifier,
        intent="link" if intent == "link" else "login",
    )
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    response = RedirectResponse(url)
    response.headers["Cache-Control"] = "no-store"
    _oauth_cookie_qoy(response, OAUTH_STATE_COOKIE, state_cookie, OAUTH_STATE_SECONDS)
    return response


@app.get("/auth/google/callback")
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """Google qaytargandan keyin ishlaydi вЂ” email oladi, bog'langan-bog'lanmaganini
    tekshiradi, mos ekranga yo'naltiradi."""
    state_payload = _oauth_token_och(
        request.cookies.get(OAUTH_STATE_COOKIE),
        "google_oauth_state",
    )
    expected_state = state_payload.get("state") if state_payload else None
    verifier = state_payload.get("verifier") if state_payload else None
    if (
        not state
        or not expected_state
        or not verifier
        or not secrets.compare_digest(state, expected_state)
    ):
        return _oauth_frontend_redirect(xato="state")
    if error or not code:
        return _oauth_frontend_redirect(xato="kirish_bekor")

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "code_verifier": verifier,
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI,
                },
            )
            token_resp.raise_for_status()
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                return _oauth_frontend_redirect(xato="google_token")

            userinfo_resp = await client.get(
                "https://openidconnect.googleapis.com/v1/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            userinfo_resp.raise_for_status()
            userinfo = userinfo_resp.json()
    except (httpx.HTTPError, ValueError):
        return _oauth_frontend_redirect(xato="google_token")

    email = str(userinfo.get("email") or "").strip().lower()
    ism = str(userinfo.get("name") or "").strip()[:200]
    if not email:
        return _oauth_frontend_redirect(xato="email_topilmadi")
    if userinfo.get("email_verified") is not True:
        return _oauth_frontend_redirect(xato="email_tasdiqlanmagan")

    conn = _db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM google_hisob WHERE google_email=%s", (email,))
        r = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if r and state_payload.get("intent") != "link":
        ticket = _oauth_imzolangan_token(
            "google_login_ticket",
            OAUTH_TICKET_SECONDS,
            outcome="login",
            user_id=r["user_id"],
        )
    else:
        ticket = _oauth_imzolangan_token(
            "google_login_ticket",
            OAUTH_TICKET_SECONDS,
            outcome="registration",
            email=email,
            name=ism,
            intent="link" if state_payload.get("intent") == "link" else "login",
        )
    return _oauth_frontend_redirect(ticket=ticket)


class GoogleTicketExchange(BaseModel):
    ticket: str


@app.post("/auth/google/exchange")
def google_ticket_exchange(sorov: GoogleTicketExchange, request: Request):
    """60 soniyalik Google ticket'ini frontend natijasiga almashtiradi."""
    origin = (request.headers.get("origin") or "").rstrip("/")
    if origin not in FRONTEND_ORIGINS:
        response = JSONResponse(status_code=403, content={"detail": "Noto'g'ri so'rov manbasi"})
        response.headers["Cache-Control"] = "no-store"
        return response

    payload = _oauth_token_och(
        sorov.ticket,
        "google_login_ticket",
    )
    if not payload:
        response = JSONResponse(status_code=401, content={"detail": "Kirish chiptasi eskirgan"})
    elif payload.get("outcome") == "login" and isinstance(payload.get("user_id"), int):
        _auth_ticket_consume(payload)
        response = JSONResponse({
            "holat": "kirdi",
            "token": _jwt_yarat(payload["user_id"]),
        })
    elif payload.get("outcome") == "registration" and payload.get("email"):
        _auth_ticket_consume(payload)
        registration_grant = _oauth_imzolangan_token(
            "google_registration_grant",
            OAUTH_REGISTRATION_GRANT_SECONDS,
            outcome="registration",
            email=payload["email"],
            intent=payload.get("intent", "login"),
        )
        response = JSONResponse({
            "holat": "ulash",
            "email": payload["email"],
            "ism": payload.get("name", ""),
            "oauth_grant": registration_grant,
            "intent": payload.get("intent", "login"),
        })
    else:
        response = JSONResponse(status_code=401, content={"detail": "Kirish chiptasi noto'g'ri"})

    response.headers["Cache-Control"] = "no-store"
    return response


class UlashSorov(BaseModel):
    email: str
    kod: str
    oauth_grant: Optional[str] = None


class RoyxatSorov(BaseModel):
    email: str
    ism: str
    rol: str = "kabutar"  # General chat first; education is selected later.
    oauth_grant: Optional[str] = None
    sinf: Optional[str] = None  # faqat rol='oquvchi' bo'lsa
    region: Optional[str] = None
    district: Optional[str] = None
    tugilgan_sana: Optional[str] = None
    maktab_raqami: Optional[str] = None

RUXSAT_ETILGAN_ROLLAR = {"oquvchi", "ota-ona", "oqituvchi", "kabutar", "mustaqil"}


@app.get("/auth/ism_tekshir")
def ism_tekshir(ism: str):
    """Botda shu ismga o'xshash foydalanuvchi bor-yo'qligini tekshiradi вЂ”
    saytdan yangi ro'yxatdan o'tishda, odam bilmasdan ikkinchi
    (dublikat) hisob ochib qo'ymasligi uchun ogohlantirish beriladi.
    Faqat BOTDAN kelgan (musbat user_id) foydalanuvchilar orasidan
    qidiradi вЂ” saytdan ro'yxatdan o'tganlar (manfiy ID) hisobga olinmaydi."""
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
    """Verified Google creates one general Kabutar account; never merges by name."""
    registration = _google_registration_tekshir(sorov.oauth_grant, sorov.email)
    email = registration["email"]
    if sorov.rol not in RUXSAT_ETILGAN_ROLLAR:
        raise HTTPException(status_code=400, detail="Noto'g'ri rol")
    name = sorov.ism.strip()
    if not name or len(name) > 200:
        raise HTTPException(status_code=400, detail="Ism 1вЂ“200 belgidan iborat bo'lsin")
    with _kabutar_auth_service.transaction() as cur:
        # All legacy negative-ID registrations share this lock. It also ensures
        # consumed grants and unique-email ownership commit in one transaction.
        cur.execute("SELECT pg_advisory_xact_lock(%s)", (31091001,))
        cur.execute("SELECT user_id FROM google_hisob WHERE google_email=%s", (email,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Bu email allaqachon ulangan вЂ” kirish orqali davom eting")
        _auth_ticket_consume_cur(cur, registration)
        cur.execute("SELECT MIN(user_id) AS eng_kichik FROM users WHERE user_id < 0")
        row=cur.fetchone()
        new_id=(row["eng_kichik"]-1) if row and row["eng_kichik"] is not None else -1
        cur.execute("""INSERT INTO users(user_id,full_name,role,class,region,district,tugilgan_sana,maktab_raqami,kabutar_education_ready)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (new_id,name,sorov.rol,sorov.sinf if sorov.rol=="oquvchi" else None,sorov.region,sorov.district,
             sorov.tugilgan_sana,sorov.maktab_raqami,sorov.rol not in ("kabutar","mustaqil")))
        cur.execute("INSERT INTO google_hisob(google_email,user_id) VALUES(%s,%s)",(email,new_id))
        token=_kabutar_auth_service._issue_cur(cur,new_id,"google")
    _kabutar_auth_service.record_login(new_id,"google")
    return {"token":token,"user_id":new_id,"holat":"royxatdan otdi"}


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# TELEFON RAQAMI ORQALI KIRISH вЂ” SMS o'rniga, AVVAL Telegram bot
# orqali (BEPUL) yuboradi; faqat telefon Telegram bilan bog'lanmagan
# yoki yuborish muvaffaqiyatsiz bo'lsa, Eskiz.uz orqali SMS'ga
# o'tadi (bu вЂ” pullik, ESKIZ_EMAIL/ESKIZ_PASSWORD sozlangan bo'lishi
# kerak).
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

def _telefon_jadvallari(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS telefon_hisob(
        telefon TEXT PRIMARY KEY,
        user_id BIGINT REFERENCES users(user_id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS telefon_tasdiq_kod(
        telefon TEXT PRIMARY KEY,
        kod TEXT NOT NULL,
        yaratildi TIMESTAMP DEFAULT NOW(),
        ishlatildi BOOLEAN DEFAULT FALSE
    )""")


def _telefonni_normallashtir(telefon: str) -> str:
    """+998901234567 formatiga keltiradi вЂ” foydalanuvchi qanday
    yozishidan qat'i nazar (bo'shliq, tire, +998 bilan yoki
    boshlanmagan) bir xil, izchil formatga tushiradi."""
    raqamlar = re.sub(r"\D", "", telefon or "")
    if raqamlar.startswith("998") and len(raqamlar) == 12:
        return f"+{raqamlar}"
    if len(raqamlar) == 9:
        return f"+998{raqamlar}"
    raise HTTPException(status_code=400, detail="Telefon raqami noto'g'ri вЂ” +998 bilan, 9 xonali (masalan +998901234567)")


_ESKIZ_TOKEN_KESH = {"token": None, "olindi": None}


def _eskiz_token_ol():
    """Eskiz.uz token'ini oladi вЂ” 25 soatgacha keshda saqlaydi (token
    30 kun amal qiladi, lekin xavfsiz tomondan qisqaroq keshlaymiz)."""
    email = os.getenv("ESKIZ_EMAIL", "")
    parol = os.getenv("ESKIZ_PASSWORD", "")
    if not email or not parol:
        return None
    if _ESKIZ_TOKEN_KESH["token"] and _ESKIZ_TOKEN_KESH["olindi"] and \
       (datetime.now() - _ESKIZ_TOKEN_KESH["olindi"]).total_seconds() < 25 * 3600:
        return _ESKIZ_TOKEN_KESH["token"]
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post("https://notify.eskiz.uz/api/auth/login", data={"email": email, "password": parol})
        r.raise_for_status()
        token = r.json()["data"]["token"]
        _ESKIZ_TOKEN_KESH["token"] = token
        _ESKIZ_TOKEN_KESH["olindi"] = datetime.now()
        return token
    except Exception as e:
        print(f"[Eskiz login xatosi] {e}")
        return None


def _sms_yubor(telefon: str, matn: str) -> bool:
    token = _eskiz_token_ol()
    if not token:
        return False
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(
                "https://notify.eskiz.uz/api/message/sms/send",
                headers={"Authorization": f"Bearer {token}"},
                data={"mobile_phone": telefon.lstrip("+"), "message": matn, "from": "4546"},
            )
        return r.status_code == 200
    except Exception as e:
        print(f"[Eskiz SMS xatosi] {e}")
        return False


def _telegram_orqali_yubor(user_id: int, matn: str) -> bool:
    """Telegram bot API orqali BEPUL xabar yuboradi вЂ” FAQAT foydalanuvchi
    avvalroq botga /start bosgan bo'lsa ishlaydi (Telegram'ning o'zi
    qo'ygan cheklov вЂ” bot birinchi bo'lib yoza olmaydi)."""
    if not BOT_TOKEN:
        return False
    try:
        with httpx.Client(timeout=10) as client:
            r = client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": user_id, "text": matn},
            )
        return r.status_code == 200 and r.json().get("ok")
    except Exception as e:
        print(f"[Telegram yuborish xatosi] {e}")
        return False


class TelefonKodSorash(BaseModel):
    telefon: str


@app.post("/api/auth/telefon_kod_sorash")
def telefon_kod_sorash(sorov: TelefonKodSorash):
    raise HTTPException(status_code=410, detail="Telefon orqali eski kod kirishi yopilgan. Telegram orqali kirish tugmasidan foydalaning")
    """Tasdiqlash kodini yuboradi вЂ” AVVAL Telegram bot orqali (bepul,
    agar telefon allaqachon botga ulangan bo'lsa), bo'lmasa Eskiz.uz
    orqali SMS (pullik, sozlangan bo'lsa)."""
    telefon = _telefonni_normallashtir(sorov.telefon)
    kod = "".join(secrets.choice(string.digits) for _ in range(6))

    conn = _db()
    cur = conn.cursor()
    _telefon_jadvallari(cur)
    cur.execute(
        """INSERT INTO telefon_tasdiq_kod(telefon, kod, yaratildi, ishlatildi) VALUES(%s,%s,NOW(),FALSE)
           ON CONFLICT (telefon) DO UPDATE SET kod=EXCLUDED.kod, yaratildi=NOW(), ishlatildi=FALSE""",
        (telefon, kod),
    )
    cur.execute("SELECT user_id FROM telefon_hisob WHERE telefon=%s", (telefon,))
    r = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    matn = f"SamTM Ta'lim вЂ” tasdiqlash kodingiz: {kod}. Kod 10 daqiqa amal qiladi."
    usul = None
    if r and r["user_id"] and _telegram_orqali_yubor(r["user_id"], matn):
        usul = "telegram"
    elif _sms_yubor(telefon, matn):
        usul = "sms"

    if not usul:
        raise HTTPException(
            status_code=503,
            detail="Kod yuborib bo'lmadi вЂ” Telegram botga ulanmagansiz va SMS xizmati hali sozlanmagan. Google orqali kiring yoki administratorga murojaat qiling.",
        )
    return {"holat": "yuborildi", "usul": usul}


class TelefonKodTasdiqlash(BaseModel):
    telefon: str
    kod: str


@app.post("/api/auth/telefon_kod_tasdiqla")
def telefon_kod_tasdiqla(sorov: TelefonKodTasdiqlash):
    raise HTTPException(status_code=410, detail="Telefon orqali eski kod kirishi yopilgan. Telegram orqali kirish tugmasidan foydalaning")
    """Kodni tekshiradi. Telefon avvaldan ulangan bo'lsa вЂ” token beradi
    (kirish). Ulanmagan (yangi) bo'lsa вЂ” "royxat_kerak" qaytaradi,
    frontend keyin /api/auth/telefon_royxat orqali ism/rol so'raydi."""
    telefon = _telefonni_normallashtir(sorov.telefon)
    conn = _db()
    cur = conn.cursor()
    _telefon_jadvallari(cur)
    cur.execute("""
        SELECT kod, ishlatildi, (yaratildi > NOW() - INTERVAL '10 minutes') AS hali_yangi
        FROM telefon_tasdiq_kod WHERE telefon=%s
    """, (telefon,))
    r = cur.fetchone()
    if not r:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Avval kod so'rang")
    if r["ishlatildi"]:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod allaqachon ishlatilgan")
    if not r["hali_yangi"]:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod muddati tugagan вЂ” qaytadan so'rang")
    if sorov.kod.strip() != r["kod"]:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod noto'g'ri")

    cur.execute("SELECT user_id FROM telefon_hisob WHERE telefon=%s", (telefon,))
    hisob = cur.fetchone()
    if hisob and hisob["user_id"]:
        cur.execute("UPDATE telefon_tasdiq_kod SET ishlatildi=TRUE WHERE telefon=%s", (telefon,))
        conn.commit()
        cur.close(); conn.close()
        token = _jwt_yarat(hisob["user_id"])
        return {"holat": "kirdi", "token": token}

    # Kod to'g'ri, lekin bu telefon hali hech qanday hisobga ulanmagan вЂ”
    # "ishlatildi"ni ATAYLAB belgilamaymiz, chunki /telefon_royxat
    # yakunida belgilaymiz (aks holda ro'yxatdan o'tish yarim qolsa,
    # kod ishlatib bo'lingan deb hisoblanib qolardi).
    cur.close(); conn.close()
    return {"holat": "royxat_kerak"}


class TelefonRoyxatSorov(BaseModel):
    telefon: str
    kod: str
    ism: str
    rol: str
    sinf: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None


@app.post("/api/auth/telefon_royxat")
def telefon_royxat(sorov: TelefonRoyxatSorov):
    raise HTTPException(status_code=410, detail="Telefon orqali eski kod kirishi yopilgan. Telegram orqali kirish tugmasidan foydalaning")
    """Telefon orqali YANGI hisob yaratadi вЂ” kodni QAYTA tekshiradi
    (xavfsizlik: kim bo'lsa ham to'g'ridan-to'g'ri shu endpoint'ga
    kod'siz murojaat qilib hisob ochib qo'ymasin)."""
    if sorov.rol not in RUXSAT_ETILGAN_ROLLAR:
        raise HTTPException(status_code=400, detail=f"Noto'g'ri rol: {sorov.rol}")
    if not sorov.ism.strip():
        raise HTTPException(status_code=400, detail="Ism kiritilmagan")
    telefon = _telefonni_normallashtir(sorov.telefon)

    conn = _db()
    cur = conn.cursor()
    _telefon_jadvallari(cur)
    cur.execute("""
        SELECT kod, ishlatildi, (yaratildi > NOW() - INTERVAL '10 minutes') AS hali_yangi
        FROM telefon_tasdiq_kod WHERE telefon=%s
    """, (telefon,))
    r = cur.fetchone()
    if not r or r["ishlatildi"] or not r["hali_yangi"] or sorov.kod.strip() != r["kod"]:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod tasdiqlanmagan yoki muddati tugagan вЂ” qaytadan boshlang")

    cur.execute("SELECT MIN(user_id) AS eng_kichik FROM users WHERE user_id < 0")
    er = cur.fetchone()
    yangi_id = (er["eng_kichik"] - 1) if er and er["eng_kichik"] is not None else -1
    cur.execute(
        """INSERT INTO users(user_id, full_name, role, class, region, district)
           VALUES(%s,%s,%s,%s,%s,%s)""",
        (yangi_id, sorov.ism.strip(), sorov.rol, sorov.sinf if sorov.rol == "oquvchi" else None,
         sorov.region, sorov.district),
    )
    cur.execute("""
        INSERT INTO telefon_hisob(telefon, user_id) VALUES(%s,%s)
        ON CONFLICT (telefon) DO UPDATE SET user_id=EXCLUDED.user_id
    """, (telefon, yangi_id))
    cur.execute("UPDATE telefon_tasdiq_kod SET ishlatildi=TRUE WHERE telefon=%s", (telefon,))
    conn.commit()
    cur.close()
    conn.close()

    token = _jwt_yarat(yangi_id)
    return {"token": token, "user_id": yangi_id, "holat": "royxatdan otdi"}


@app.post("/auth/ulash")
def hisob_ulash(sorov: UlashSorov):
    raise HTTPException(status_code=410, detail="Eski akkaunt koвЂchirish kodi yopilgan. Profil в†’ Kirish va xavfsizlik boвЂlimida Telegram yoki Google hisobini ulang")
    """Google hisobini bot user_id'siga kod orqali bog'laydi. Ikki xil
    kod manbasini tekshiradi: botdagi veb_ulash_kod (15 daqiqa amal
    qiladi) VA xodimlar uchun xodim_kod (2 oy amal qiladi,
    admin Excel orqali xodim import qilganda yaratiladi) вЂ” shu sabab
    bitta "kod kiritish" ekrani ikkalasi uchun ham ishlaydi."""
    registration = _google_registration_tekshir(sorov.oauth_grant, sorov.email)
    email, kod = registration["email"], sorov.kod.strip()
    conn = _db()
    cur = conn.cursor()
    _xodim_kod_jadvali(cur)
    subject_hash = _xodim_kod_subject("email", email.strip().lower())
    if _xodim_kod_bloklanganmi(cur, subject_hash):
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=429,
            detail="Ko'p noto'g'ri urinish. 30 daqiqadan keyin qayta urinib ko'ring.",
        )
    cur.execute("""
        SELECT kod AS stored_code,user_id, ishlatildi,
               (yaratildi > NOW() - INTERVAL '15 minutes') AS hali_yangi
        FROM veb_ulash_kod WHERE kod=%s
        FOR UPDATE
    """, (kod,))
    r = cur.fetchone()
    muddat_matni = "15 daqiqa"
    jadval_nomi = "veb_ulash_kod"

    if not r:
        plain_code, hashed_code = _xodim_kod_variantlari(kod)
        cur.execute("""
            SELECT kod AS stored_code,user_id,ishlatildi,
                   (yaratildi > NOW() - INTERVAL '2 months') AS hali_yangi
            FROM xodim_kod
            WHERE kod IN (%s,%s)
              AND (kod LIKE 'sha256:%%' OR LENGTH(kod)>=12)
            ORDER BY CASE WHEN kod=%s THEN 0 ELSE 1 END
            LIMIT 1
            FOR UPDATE
        """, (hashed_code, plain_code, hashed_code))
        r = cur.fetchone()
        muddat_matni = "2 oy"
        jadval_nomi = "xodim_kod"

    if not r:
        _xodim_kod_xato_urinish(cur, subject_hash)
        conn.commit()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Kod noto'g'ri")
    if r["ishlatildi"]:
        _xodim_kod_xato_urinish(cur, subject_hash)
        conn.commit()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Kod allaqachon ishlatilgan")
    if not r["hali_yangi"]:
        _xodim_kod_xato_urinish(cur, subject_hash)
        conn.commit()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"Kod muddati tugagan ({muddat_matni}) вЂ” qaytadan so'rang")

    cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,31))", ("google:"+email,))
    cur.execute("SELECT user_id FROM google_hisob WHERE google_email=%s", (email,))
    existing_google = cur.fetchone()
    if existing_google and existing_google["user_id"] != r["user_id"]:
        cur.close(); conn.close()
        raise HTTPException(status_code=409, detail="Bu Google hisobi boshqa akkauntga ulangan; avtomatik birlashtirilmaydi")
    _auth_ticket_consume_cur(cur, registration)
    cur.execute("""
        INSERT INTO google_hisob (google_email, user_id) VALUES (%s,%s)
        ON CONFLICT (google_email) DO NOTHING
    """, (email, r["user_id"]))
    cur.execute(
        f"UPDATE {jadval_nomi} SET ishlatildi=TRUE WHERE kod=%s",
        (r["stored_code"],),
    )
    _xodim_kod_urinishni_tozalash(cur, subject_hash)
    conn.commit()
    cur.close()
    conn.close()

    token = _jwt_yarat(r["user_id"])
    return {"token": token, "holat": "ulandi"}


@app.get("/auth/men")
def joriy_foydalanuvchi(token: Optional[str] = None, request: Request = None):
    """Token orqali 'bu kim' ekanini tasdiqlaydi вЂ” frontend sahifa yuklanganda
    ishlatadi. Admin bo'lsa, is_admin=true qaytadi вЂ” frontend shunga qarab
    sinf-cheklovini olib tashlaydi (admin barcha sinflarni ko'rishi kerak)."""
    if request is not None:
        token = _jwt_header_yoki_query(token, request.headers.get("authorization"))
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    _users_profil_rasm_ustunlari(cur)
    cur.execute(
        "SELECT user_id, full_name, role, class, class_letter, school_type, "
        "region, district, tugilgan_sana, maktab_raqami, jins, oqituvchi_fani, "
        "COALESCE(NULLIF(asosiy_til,''), 'uz') AS asosiy_til, ovoz_jinsi, "
        "maktab_id, markaz_id, bogcha_id, universitet_id, lavozim, "
        "(profil_rasm IS NOT NULL) AS rasm_bormi FROM users WHERE user_id=%s",
        (user_id,),
    )
    r = cur.fetchone()
    if not r:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    if r["maktab_id"]:
        _maktab_jadvali(cur)
        cur.execute(
            "SELECT nomi FROM maktablar WHERE id=%s AND archived_at IS NULL",
            (r["maktab_id"],),
        )
        m = cur.fetchone()
        r["maktab_nomi"] = m["nomi"] if m else None
        if not m:
            # Arxivlangan maktab profil fallbacki orqali yana chiqib qolmasin.
            r["maktab_id"] = None
    else:
        r["maktab_nomi"] = None

    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
    r["is_admin"] = cur.fetchone() is not None
    cur.close()
    conn.close()
    if _kabutar_auth_service is not None:
        r.update(_kabutar_auth_service.profile_status(user_id))
    return r


@app.get("/api/auth/muassasalarim")
def muassasalarim(token: str):
    """Chaqiruvchi qanday muassasa(lar)ga tegishli ekanini вЂ” HAR
    BIRINI ALOHIDA вЂ” ro'yxat qilib qaytaradi. Eski (yagona ustun) va
    yangi (ko'p muassasali) manbalarni birlashtirib, takrorlarni olib
    tashlaydi. Frontend shu ro'yxat asosida "Maktabim"/"Markazim"/
    "Bog'cham"/"Institutim" kabi ALOHIDA bo'limlar(tab)ni chizadi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS maktab_id INTEGER")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS markaz_id INTEGER")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS bogcha_id INTEGER")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS universitet_id INTEGER")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS lavozim TEXT")
    cur.execute(
        "SELECT maktab_id, markaz_id, bogcha_id, universitet_id, lavozim FROM users WHERE user_id=%s",
        (user_id,),
    )
    u = cur.fetchone()

    topilganlar = {}  # (turi, muassasa_id) -> lavozim
    if u:
        for turi, mid in [("maktab", u["maktab_id"]), ("markaz", u["markaz_id"]), ("bogcha", u["bogcha_id"]), ("universitet", u["universitet_id"])]:
            # Profil fallbacki ID mavjud bo'lsa institutni darhol ko'rsatadi.
            # API ham lavozim bo'sh bo'lgani uchun ayni IDni yo'qotmasligi kerak;
            # haqiqiy amal ruxsati baribir tegishli workspace backendida tekshiriladi.
            if mid:
                topilganlar[(turi, mid)] = u["lavozim"] or ""

    _muassasa_jadvali(cur)
    cur.execute("SELECT muassasa_turi, muassasa_id, lavozim FROM foydalanuvchi_muassasalari WHERE user_id=%s", (user_id,))
    for r in cur.fetchall():
        topilganlar[(r["muassasa_turi"], r["muassasa_id"])] = r["lavozim"]

    # V2254: institut xodim rollari (rektor, dekan, kafedra mudiri, tyutor...) va
    # institut talabalari ham "mening muassasalarim" ro'yxatiga kiradi вЂ” aks holda
    # dekan kirganda umumiy o'qituvchi ish maydoniga tushib qolar edi.
    cur.execute("SELECT to_regclass('public.universitet_xodim_rollari') AS r1, to_regclass('public.universitet_qabul_talabalari') AS r2")
    _inst = cur.fetchone() or {}
    rol_manbai = set()  # institut rol jadvalidan kelganlar вЂ” v17 filtr ularga tegmaydi
    if _inst.get("r1"):
        cur.execute(
            """SELECT universitet_id, rol FROM universitet_xodim_rollari
               WHERE user_id=%s AND faol=TRUE
               ORDER BY CASE rol WHEN 'owner' THEN 0 WHEN 'rektor' THEN 1 WHEN 'prorektor' THEN 2
                                 WHEN 'institut_admin' THEN 3 WHEN 'dekan' THEN 4 WHEN 'zam_dekan' THEN 5
                                 WHEN 'fakultet_admin' THEN 6 WHEN 'kafedra_mudiri' THEN 7 ELSE 9 END, id""",
            (user_id,),
        )
        for r in cur.fetchall():
            key = ("universitet", int(r["universitet_id"]))
            rol_manbai.add(key)
            if key not in topilganlar or not topilganlar[key]:
                topilganlar[key] = r["rol"]
    if _inst.get("r2"):
        cur.execute("SELECT universitet_id FROM universitet_qabul_talabalari WHERE user_id=%s", (user_id,))
        for r in cur.fetchall():
            rol_manbai.add(("universitet", int(r["universitet_id"])))
            topilganlar.setdefault(("universitet", int(r["universitet_id"])), "talaba")

    cur.execute("""SELECT
        to_regclass('public.organization_trials') AS trials,
        to_regclass('public.learning_contexts') AS contexts,
        to_regclass('public.context_memberships') AS memberships,
        to_regclass('public.universitet_workspace_map') AS workspace_map""")
    v17_tables = cur.fetchone() or {}
    v17_ready = bool(v17_tables.get("trials") and v17_tables.get("contexts"))
    jadval_nomi = {"maktab": "maktablar", "markaz": "oquv_markazlari", "bogcha": "bogchalar", "universitet": "universitetlar"}
    v17_turi = {"maktab": "school", "markaz": "learning_center", "bogcha": "kindergarten", "universitet": "institute"}
    natija = []
    for (turi, muassasa_id), lavozim in topilganlar.items():
        # Profil yoki eski a'zolik ko'rsatkichi arxivlangandan keyin ham qolishi
        # mumkin. Arxivlangan legacy muassasani faol ro'yxatga qayta qo'shmaymiz.
        cur.execute(
            f"""SELECT muassasa.nomi
                FROM {jadval_nomi[turi]} AS muassasa
                WHERE muassasa.id=%s
                  AND NULLIF(to_jsonb(muassasa)->>'archived_at','') IS NULL""",
            (muassasa_id,),
        )
        m = cur.fetchone()
        if not m:
            # O'chib ketgan legacy ID frontendda nomsiz/stale kartaga aylanmasin.
            continue
        if v17_ready and (turi, muassasa_id) not in rol_manbai:
            if turi == "universitet" and v17_tables.get("workspace_map"):
                # Eski xatoda school contexti universitet sifatida xaritaga
                # yozilgan. WHERE'da faqat institute qidirsak o'sha noto'g'ri
                # map ko'rinmay qoladi va "Harbiylashgan maktab" yana chiqadi.
                # Shu bois avval har qanday mapni topamiz, keyin uning aynan
                # faol university/institute ekanini BOOL_OR ichida tekshiramiz.
                cur.execute("""SELECT
                        COUNT(*) AS v17_soni,
                        BOOL_OR(
                          o.organization_type='institute'
                          AND c.context_type='university'
                          AND c.active=TRUE
                          AND LOWER(COALESCE(o.lifecycle_status,''))
                              IN ('trial','read_only','active')
                        ) AS faol_v17
                    FROM organization_trials o
                    JOIN learning_contexts c ON c.id=o.context_id
                    LEFT JOIN universitet_workspace_map uwm
                      ON uwm.context_id=o.context_id
                    WHERE uwm.universitet_id=%s OR (
                      o.organization_type='institute'
                      AND c.context_type='university'
                      AND c.external_id=%s
                    )""", (muassasa_id, muassasa_id))
            else:
                cur.execute("""SELECT
                        COUNT(*) AS v17_soni,
                        BOOL_OR(
                          c.active=TRUE
                          AND LOWER(COALESCE(o.lifecycle_status,''))
                              IN ('trial','read_only','active')
                        ) AS faol_v17
                    FROM organization_trials o
                    JOIN learning_contexts c ON c.id=o.context_id
                    WHERE o.organization_type=%s AND c.external_id=%s""",
                    (v17_turi[turi], muassasa_id))
            v17_state = cur.fetchone() or {}
            if int(v17_state.get("v17_soni") or 0) > 0 and not bool(v17_state.get("faol_v17")):
                # Arxivlangan self-service muassasaning users/FM pointeri qolgan
                # bo'lsa ham uni qayta ko'rsatmaymiz.
                continue
        natija.append({"turi": turi, "muassasa_id": muassasa_id, "muassasa_nomi": m["nomi"], "lavozim": lavozim, "faol": True})

    # V17 self-service muassasalari modulli context/profile/role yozuvlariga
    # ulangan. Ularni eski pastki menyu DTO'siga ham qo'shamiz, shunda sahifa
    # yangilangandan keyin yaratilgan ish joyi yo'qolib qolmaydi. Bog'cha uchun
    # legacy a'zolik bo'lsa, V17 holatli yozuv o'sha eski yozuvni almashtiradi.
    if v17_ready:
        membership_sql = (
            "OR EXISTS(SELECT 1 FROM context_memberships cm "
            "WHERE cm.context_id=o.context_id AND cm.user_id=%s AND cm.status='active')"
            if v17_tables.get("memberships") else ""
        )
        query_params = [user_id]
        if membership_sql:
            query_params.append(user_id)
        workspace_join = (
            "LEFT JOIN universitet_workspace_map uwm ON uwm.context_id=o.context_id"
            if v17_tables.get("workspace_map") else ""
        )
        external_id_sql = (
            "CASE WHEN o.organization_type='institute' "
            "THEN uwm.universitet_id ELSE c.external_id END"
            if v17_tables.get("workspace_map") else "c.external_id"
        )
        cur.execute(
            """SELECT o.id organization_v17_id,o.context_id,
                      o.organization_type,o.display_name,o.lifecycle_status,
                      o.trial_ends_at,o.activated_at,
                      GREATEST(
                        0,CEIL(EXTRACT(EPOCH FROM (o.trial_ends_at-NOW()))/86400.0)
                      )::INTEGER days_remaining,
                      {external_id_sql} AS external_id
                 FROM organization_trials o
                 JOIN learning_contexts c ON c.id=o.context_id
                 {workspace_join}
                WHERE (o.creator_user_id=%s {membership_sql})
                  AND c.active=TRUE
                  AND (o.organization_type<>'institute' OR c.context_type='university')
                  AND LOWER(COALESCE(o.lifecycle_status,''))
                      IN ('trial','read_only','active')
                ORDER BY o.id""".format(
                    membership_sql=membership_sql,
                    workspace_join=workspace_join,
                    external_id_sql=external_id_sql,
                ),
            query_params,
        )
        type_map = {
            "kindergarten": "bogcha",
            "school": "maktab",
            "learning_center": "markaz",
            "institute": "universitet",
        }
        for org in cur.fetchall():
            turi = type_map.get(org["organization_type"])
            if not turi:
                continue
            # V17 context legacy obyektga ulangan bo'lsa, eski kartani barcha
            # muassasa turlarida almashtiramiz (avval faqat bog'chada edi).
            if org["external_id"] is not None:
                natija = [
                    item for item in natija
                    if not (
                        item["turi"] == turi
                        and int(item["muassasa_id"]) == int(org["external_id"])
                    )
                ]
            effective_read_only = (
                org["lifecycle_status"] == "read_only"
                or (
                    org["lifecycle_status"] == "trial"
                    and int(org["days_remaining"] or 0) <= 0
                )
            )
            natija.append(
                {
                    "turi": turi,
                    "muassasa_id": (
                        int(org["external_id"])
                        if org["external_id"] is not None
                        else int(org["context_id"])
                    ),
                    "context_id": int(org["context_id"]),
                    "organization_v17_id": int(org["organization_v17_id"]),
                    "muassasa_nomi": org["display_name"],
                    "lavozim": "owner",
                    "lifecycle_status": (
                        "read_only" if effective_read_only
                        else org["lifecycle_status"]
                    ),
                    "access_mode": "read_only" if effective_read_only else "write",
                    "trial_ends_at": org["trial_ends_at"],
                    "days_remaining": int(org["days_remaining"] or 0),
                    "faol": True,
                }
            )
    # DB qaytish tartibi o'zgarsa ham ro'yxat va frontend tanlovi barqaror.
    natija.sort(key=lambda item: (
        str(item.get("turi") or ""),
        str(item.get("muassasa_nomi") or "").casefold(),
        int(item.get("context_id") or item.get("muassasa_id") or 0),
    ))
    cur.close()
    conn.close()
    return {"muassasalar": natija}


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# TEST YECHISH (saytdan, botsiz)
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

@app.get("/api/mavzular")
def mavzular_royxati(sinf: str = None, turi: str = "oddiy", faqat_testli: bool = True):
    """Fan/mavzularni qaytaradi вЂ” Fan в†’ Sinf в†’ Mavzu tartibida.

    MUHIM: bitta "mavzu" ostida bir nechta "kichik mavzu" bo'lishi mumkin
    (har biri o'z topic_code'iga ega) вЂ” lekin o'quvchiga BITTA mavzu
    IKKI MARTA (har kichik mavzu uchun alohida) ko'rinishi noto'g'ri va
    chalkashtiruvchi edi. Shu sabab bu yerda MAVZU darajasida guruhlaymiz:
    har mavzu вЂ” bitta yozuv, ichida esa BARCHA kichik mavzularning
    topic_code'lari "topic_codes" ro'yxatida jamlanadi. Test yechilganda
    shu ro'yxatdagi barcha kodlardan ARALASH (random) savol olinadi
    (/api/test_aralash orqali) вЂ” shunday qilib bitta "mavzu" tanlansa,
    uning barcha kichik mavzularidan birgalikda savol chiqadi.

    faqat_testli=True (standart, test yechish uchun) вЂ” faqat
    generated_tests'da HAQIQATAN savoli bor kichik mavzularni hisobga
    oladi (agar bir mavzuning faqat qismi testli bo'lsa, faqat o'sha
    testli qismidan savol olinadi). faqat_testli=False (admin
    kontent-yaratish oqimlari uchun) вЂ” testi hali yo'q mavzularni ham
    ko'rsatadi va BARCHA kichik mavzu kodlarini beradi.

    grade ustuni ba'zan "3-4", "5-6" kabi ORALIQ ko'rinishida bo'ladi вЂ”
    bular ODDIY maktab sinfi EMAS, balki TO'GARAKNING O'Z maxsus
    guruhlari. turi="oddiy" (standart) вЂ” faqat sof raqamli sinflar
    (1,2,...11). turi="togarak" вЂ” faqat ORALIQ (to'garak) guruhlari."""
    if sinf:
        sinf = sinf.replace("-sinf", "").strip()

    togarak_mi = turi == "togarak"
    grade_shart = "d.grade !~ '^[0-9]+$'" if togarak_mi else "d.grade ~ '^[0-9]+$'"

    conn = _db()
    cur = conn.cursor()
    shart = grade_shart
    params = []
    if sinf:
        shart += " AND d.grade = %s"
        params.append(sinf)
    cur.execute(f"""
        SELECT d.subject_code, d.subject_name, d.grade,
               COALESCE(d.mavzu_name, d.bolim_name, d.bob_name) AS nomi,
               array_agg(DISTINCT d.topic_code ORDER BY d.topic_code) AS barcha_kodlar,
               array_agg(DISTINCT d.topic_code ORDER BY d.topic_code)
                   FILTER (WHERE d.topic_code IN (SELECT DISTINCT topic_code FROM generated_tests)) AS testli_kodlar,
               COUNT(gt.id) AS savol_soni
        FROM dts_tree d
        LEFT JOIN generated_tests gt ON gt.topic_code = d.topic_code
        WHERE {shart} AND d.is_deleted = FALSE
        GROUP BY d.subject_code, d.subject_name, d.grade, COALESCE(d.mavzu_name, d.bolim_name, d.bob_name)
        ORDER BY d.subject_code, d.grade, MIN(d.topic_code)
    """, params)
    qatorlar = cur.fetchall()
    cur.close()
    conn.close()

    # ``subject_code`` butun tizim bo'yicha global emas. Masalan 6-02
    # MATEMATIKA, 7-02 esa GEOMETRIYA bo'lishi mumkin. Admin sinfni avval
    # tanlaydigan ekranda API barcha sinflarni birdan qaytaradi; eski kod
    # faqat ``02`` bilan guruhlagani uchun 7-sinf geometriya mavzulari
    # boshqa sinfdagi fan nomi (masalan INGLIZ TILI) ostida ko'rinardi.
    # Fan identifikatori doim ``sinf + fan kodi`` bo'lishi shart.
    from modules.test_template_import import grade_subject_key

    fanlar = {}
    for q in qatorlar:
        kodlar = q["testli_kodlar"] if faqat_testli else q["barcha_kodlar"]
        if faqat_testli and not kodlar:
            continue  # bu mavzuning hech bir kichik qismida test yo'q вЂ” test yechish ro'yxatida ko'rsatmaymiz

        fkod = q["subject_code"] or "BOSHQA"
        fan_kaliti = grade_subject_key(q["grade"], fkod)
        if fan_kaliti not in fanlar:
            fanlar[fan_kaliti] = {"nom": q["subject_name"] or fkod, "qisqa": fkod, "sinflar": {}}

        skod = q["grade"]
        if skod not in fanlar[fan_kaliti]["sinflar"]:
            fanlar[fan_kaliti]["sinflar"][skod] = {"sinf": skod, "mavzular": []}
        fanlar[fan_kaliti]["sinflar"][skod]["mavzular"].append({
            "topic_codes": kodlar, "nomi": q["nomi"], "savol_soni": q["savol_soni"],
        })

    natija = []
    for f in fanlar.values():
        if togarak_mi:
            # "3-4", "5-6" kabi вЂ” matn bo'yicha saralaymiz (raqamga aylantirib bo'lmaydi)
            f["sinflar"] = sorted(f["sinflar"].values(), key=lambda s: s["sinf"])
        else:
            # sinflarni SONLI tartibda saralaymiz (1,2,...,11 вЂ” "11" harflar bo'yicha "2"dan oldin kelib qolmasin)
            f["sinflar"] = sorted(f["sinflar"].values(), key=lambda s: int(s["sinf"]))
        natija.append(f)
    return {"fanlar": natija}


def _qoshimcha_test_shartlari(rasimli: bool, vaqtli: bool, yozuvli: bool):
    """rasimli/vaqtli/yozuvli вЂ” None bo'lsa cheklanmaydi (aralash), True/False
    bo'lsa mos savollar filtrlanadi. SQL parcha va parametrlarni qaytaradi."""
    shartlar = []
    params = []
    if rasimli is True:
        shartlar.append("(rasm_malumot IS NOT NULL OR COALESCE(NULLIF(image_file_id, ''), image_url, '') != '')")
    elif rasimli is False:
        shartlar.append("(rasm_malumot IS NULL AND COALESCE(NULLIF(image_file_id, ''), image_url, '') = '')")
    if vaqtli is True:
        shartlar.append("COALESCE(time_limit, 0) > 0")
    elif vaqtli is False:
        shartlar.append("COALESCE(time_limit, 0) = 0")
    if yozuvli is True:
        shartlar.append("question_type = 'write_answer'")
    elif yozuvli is False:
        shartlar.append("question_type != 'write_answer'")
    return ("".join(f" AND {s}" for s in shartlar), params)


def _ruscha_sanoq_suzi(son: int, bir: str, ikki_tort: str, boshqa: str) -> str:
    """Rus tilidagi 1/2-4/5+ sanoq shaklini tanlaydi."""
    oxirgi_ikki = son % 100
    if 11 <= oxirgi_ikki <= 14:
        return boshqa
    oxirgi = son % 10
    if oxirgi == 1:
        return bir
    if 2 <= oxirgi <= 4:
        return ikki_tort
    return boshqa


def _yozma_savolga_format_korsatmasi(question, correct_answer, question_type):
    """Oddiy yozma savolga javobni oshkor qilmaydigan format ko'rsatmasi.

    Faqat harflardan tuzilgan bir yoki bir necha so'zli javoblar boyitiladi.
    Sonlar, formulalar va ``[lat]`` ifodalari o'z holicha qoladi. Savoldagi
    ``[ru]``/``[en]``/``[uz]`` teglari o'chirilmaydi: yangi ko'rsatma ham
    ayni tilda va, kerak bo'lsa, ayni teg ichida qaytariladi.
    """
    if question_type != "write_answer" or not question or not correct_answer:
        return question

    savol = str(question)
    javob = str(correct_answer)
    # Savolning o'zida formula bo'lishi mumkin, ammo javobi baribir so'z
    # bo'ladi (masalan, 90В° burchak uchun "to'g'ri"). Faqat JAVOB [lat]
    # bo'lsa son/formulaga tegmaymiz.
    if "[lat]" in javob.casefold():
        return question

    # Til teglarini faqat tahlil nusxasidan olib tashlaymiz; asl matn saqlanadi.
    sof_javob = re.sub(r"\[/?(?:ru|en|uz)\]", "", javob, flags=re.IGNORECASE).strip()
    if not sof_javob:
        return question
    ruxsat_etilgan_tinish = "'вЂвЂ™К»Кј-"
    if any(not (belgi.isalpha() or belgi.isspace() or belgi in ruxsat_etilgan_tinish) for belgi in sof_javob):
        return question

    sozlar = [soz for soz in re.split(r"\s+", sof_javob) if soz]
    harflar = [belgi for belgi in sof_javob if belgi.isalpha()]
    # Bir harfli qiymat ko'pincha algebraik belgi bo'ladi va ko'rsatma javobni
    # to'liq oshkor qilib qo'yadi; shu sabab uni formula sifatida qoldiramiz.
    if not sozlar or len(harflar) < 2 or any(not any(b.isalpha() for b in soz) for soz in sozlar):
        return question

    bosh_harf = harflar[0].upper()
    # O'zbek alifbosidagi O' va G' bitta bosh harf sifatida ko'rsatiladi.
    # Apostrofning turli Unicode ko'rinishlari bitta kanonik `вЂ`ga keladi.
    maxsus_bosh = re.match(r"([OoGg])[вЂвЂ™К»Кј']", sof_javob)
    if maxsus_bosh:
        bosh_harf = f"{maxsus_bosh.group(1).upper()}вЂ"
    harf_soni = len(harflar)
    soz_soni = len(sozlar)
    kichik = f"{savol}\n{javob}".casefold()
    if "[ru]" in kichik:
        til = "ru"
    elif "[en]" in kichik:
        til = "en"
    else:
        til = "uz"

    # Eski qisqa ko'rsatmani to'liq ko'rsatmaga almashtiramiz. Bunda aynan
    # foydalanuvchi uchratgan ``(Bosh harfi: E)`` ham takrorlanib qolmaydi.
    qisman_qoliplar = {
        "uz": r"\s*\(\s*bosh\s+harfi\s*:\s*[^)]+\)\s*",
        "en": r"\s*\(\s*first\s+letter\s*:\s*[^)]+\)\s*",
        "ru": r"\s*\(\s*(?:РїРµСЂРІР°СЏ|РЅР°С‡Р°Р»СЊРЅР°СЏ)\s+Р±СѓРєРІР°\s*:\s*[^)]+\)\s*",
    }
    savol = re.sub(qisman_qoliplar[til], " ", savol, flags=re.IGNORECASE).strip()
    sof_savol = re.sub(r"\[/?(?:ru|en|uz)\]", "", savol, flags=re.IGNORECASE)
    tekshiruv = sof_savol.casefold()

    if til == "en":
        bosh_bormi = bool(re.search(r"\banswer\s+(?:starts|begins)\s+with\b|\bfirst\s+letter\s*:", tekshiruv))
        uzunlik_bormi = bool(re.search(rf"(?<!\d){harf_soni}\s+letters?\b", tekshiruv))
        soz_bormi = bool(re.search(rf"(?<!\d){soz_soni}\s+words?\b", tekshiruv)) or (
            soz_soni == 1 and "one word" in tekshiruv
        )
        korsatma_bormi = (
            bool(re.search(r"\bwrite\s+(?:exactly\s+)?one\s+word\b", tekshiruv))
            if soz_soni == 1
            else "write the exact phrase" in tekshiruv
        )
        if bosh_bormi and uzunlik_bormi and soz_bormi and korsatma_bormi:
            return savol
        if not bosh_bormi and not uzunlik_bormi:
            if soz_soni == 1:
                tavsif = f"Answer starts with {bosh_harf} and has {harf_soni} letters"
            else:
                tavsif = f"Answer starts with {bosh_harf} and has {soz_soni} words, {harf_soni} letters total"
        else:
            qismlar = []
            if not bosh_bormi:
                qismlar.append(f"Answer starts with {bosh_harf}")
            if not uzunlik_bormi:
                qismlar.append(f"{harf_soni} letters" if soz_soni == 1 else f"{harf_soni} letters total")
            if soz_soni > 1 and not soz_bormi:
                qismlar.append(f"{soz_soni} words")
            tavsif = "; ".join(qismlar)
        korsatma = "" if korsatma_bormi else ("write one word" if soz_soni == 1 else "write the exact phrase")
        hint_matni = f"{tavsif}; {korsatma}" if tavsif and korsatma else (tavsif or korsatma)
        hint = f"[en]({hint_matni}.)[/en]"
    elif til == "ru":
        bosh_bormi = bool(re.search(r"\bРѕС‚РІРµС‚\s+РЅР°С‡РёРЅР°РµС‚СЃСЏ\s+СЃ\s+Р±СѓРєРІС‹\b|\b(?:РїРµСЂРІР°СЏ|РЅР°С‡Р°Р»СЊРЅР°СЏ)\s+Р±СѓРєРІР°\s*:", tekshiruv))
        harf_sozi = _ruscha_sanoq_suzi(harf_soni, "Р±СѓРєРІР°", "Р±СѓРєРІС‹", "Р±СѓРєРІ")
        soz_sozi = _ruscha_sanoq_suzi(soz_soni, "СЃР»РѕРІРѕ", "СЃР»РѕРІР°", "СЃР»РѕРІ")
        uzunlik_bormi = bool(re.search(rf"(?<!\d){harf_soni}\s+(?:Р±СѓРєРІР°|Р±СѓРєРІС‹|Р±СѓРєРІ)\b", tekshiruv))
        soz_bormi = bool(re.search(rf"(?<!\d){soz_soni}\s+(?:СЃР»РѕРІРѕ|СЃР»РѕРІР°|СЃР»РѕРІ)\b", tekshiruv)) or (
            soz_soni == 1 and "РѕРґРЅРѕ СЃР»РѕРІРѕ" in tekshiruv
        )
        korsatma_bormi = (
            "РЅР°РїРёС€РёС‚Рµ СЂРѕРІРЅРѕ РѕРґРЅРѕ СЃР»РѕРІРѕ" in tekshiruv
            if soz_soni == 1
            else "РЅР°РїРёС€РёС‚Рµ С‚РѕС‡РЅСѓСЋ С„СЂР°Р·Сѓ" in tekshiruv
        )
        if bosh_bormi and uzunlik_bormi and soz_bormi and korsatma_bormi:
            return savol
        if not bosh_bormi and not uzunlik_bormi:
            if soz_soni == 1:
                tavsif = f"РћС‚РІРµС‚ РЅР°С‡РёРЅР°РµС‚СЃСЏ СЃ Р±СѓРєРІС‹ {bosh_harf} Рё СЃРѕРґРµСЂР¶РёС‚ {harf_soni} {harf_sozi}"
            else:
                tavsif = (
                    f"РћС‚РІРµС‚ РЅР°С‡РёРЅР°РµС‚СЃСЏ СЃ Р±СѓРєРІС‹ {bosh_harf} Рё СЃРѕРґРµСЂР¶РёС‚ {soz_soni} {soz_sozi}, "
                    f"РІСЃРµРіРѕ {harf_soni} {harf_sozi}"
                )
        else:
            qismlar = []
            if not bosh_bormi:
                qismlar.append(f"РћС‚РІРµС‚ РЅР°С‡РёРЅР°РµС‚СЃСЏ СЃ Р±СѓРєРІС‹ {bosh_harf}")
            if not uzunlik_bormi:
                qismlar.append(f"{harf_soni} {harf_sozi}")
            if soz_soni > 1 and not soz_bormi:
                qismlar.append(f"{soz_soni} {soz_sozi}")
            tavsif = "; ".join(qismlar)
        korsatma = "" if korsatma_bormi else (
            "РЅР°РїРёС€РёС‚Рµ СЂРѕРІРЅРѕ РѕРґРЅРѕ СЃР»РѕРІРѕ"
            if soz_soni == 1
            else "РЅР°РїРёС€РёС‚Рµ С‚РѕС‡РЅСѓСЋ С„СЂР°Р·Сѓ"
        )
        hint_matni = f"{tavsif}; {korsatma}" if tavsif and korsatma else (tavsif or korsatma)
        hint = f"[ru]({hint_matni}.)[/ru]"
    else:
        bosh_bormi = bool(re.search(r"\bjavob\s+\S+\s+harfi\s+bilan\s+boshlanadi\b|\bbosh\s+harfi\s*:", tekshiruv))
        uzunlik_bormi = bool(re.search(rf"(?<!\d){harf_soni}\s+harf\b", tekshiruv))
        soz_bormi = bool(re.search(rf"(?<!\d){soz_soni}\s+so['вЂвЂ™К»Кј]?z\b", tekshiruv)) or (
            soz_soni == 1 and bool(re.search(r"\bbitta\s+(?:aniq\s+)?so['вЂвЂ™К»Кј]?z\b", tekshiruv))
        )
        qoshimchasiz_bormi = bool(re.search(r"qo['вЂвЂ™К»Кј]?shimchasiz\s+yozing", tekshiruv))
        if bosh_bormi and uzunlik_bormi and soz_bormi and qoshimchasiz_bormi:
            return savol
        qismlar = []
        if not bosh_bormi:
            qismlar.append(f"Javob {bosh_harf} harfi bilan boshlanadi")
        if soz_soni > 1 and not soz_bormi:
            qismlar.append(f"{soz_soni} soвЂz")
        if not uzunlik_bormi:
            uzunlik = f"jami {harf_soni} harf" if soz_soni > 1 else f"{harf_soni} harf"
            qismlar.append(uzunlik)
        if soz_soni == 1 and not soz_bormi:
            qismlar.append("bitta soвЂz")
        tavsif = ", ".join(qismlar)
        korsatma = "" if qoshimchasiz_bormi else "qoвЂshimchasiz yozing"
        hint_matni = f"{tavsif}; {korsatma}" if tavsif and korsatma else (tavsif or korsatma)
        hint = f"({hint_matni}.)"
        if "[uz]" in kichik:
            hint = f"[uz]{hint}[/uz]"

    return f"{savol.rstrip()} {hint}".strip()


@app.get("/api/test/{topic_code}/soni")
def test_savollari_soni(topic_code: str, qiyinlik: str = None, rasimli: bool = None, vaqtli: bool = None, yozuvli: bool = None):
    """Tanlangan sozlamalar (qiyinlik/rasm/vaqt/javob turi) bo'yicha nechta
    savol MAVJUDLIGINI qaytaradi вЂ” test boshlanishidan OLDIN frontend shu
    yordamida haqiqiy sonni ko'rsatadi."""
    conn = _db()
    cur = conn.cursor()
    shart = "topic_code = %s"
    params = [topic_code]
    if qiyinlik:
        shart += " AND difficulty = %s"
        params.append(qiyinlik)
    qoshimcha, qoshimcha_params = _qoshimcha_test_shartlari(rasimli, vaqtli, yozuvli)
    shart += qoshimcha
    params += qoshimcha_params
    cur.execute(f"SELECT COUNT(*) AS soni FROM generated_tests WHERE {shart}", params)
    soni = cur.fetchone()["soni"]
    cur.close()
    conn.close()
    return {"soni": soni}


class AralashSoniSorovi(BaseModel):
    topic_codes: list = []
    qiyinlik: Optional[str] = None
    rasimli: Optional[bool] = None
    vaqtli: Optional[bool] = None
    yozuvli: Optional[bool] = None


@app.post("/api/test_aralash/soni")
def aralash_savollari_soni(sorov: AralashSoniSorovi):
    """Aralash (bir nechta mavzu) tanlanganda вЂ” sozlamalarga mos nechta
    savol mavjudligini qaytaradi. topic_codes ichida bo'sh/noto'g'ri
    qiymat bo'lsa ham (masalan null) 422 bermasdan, shunchaki e'tiborsiz
    qoldiradi вЂ” frontendga har doim aniq javob (soni: N) qaytadi."""
    kodlar = [str(k).strip() for k in sorov.topic_codes if k and str(k).strip()]
    if not kodlar:
        return {"soni": 0}
    conn = _db()
    cur = conn.cursor()
    shart = "topic_code = ANY(%s)"
    params = [kodlar]
    if sorov.qiyinlik:
        shart += " AND difficulty = %s"
        params.append(sorov.qiyinlik)
    qoshimcha, qoshimcha_params = _qoshimcha_test_shartlari(sorov.rasimli, sorov.vaqtli, sorov.yozuvli)
    shart += qoshimcha
    params += qoshimcha_params
    cur.execute(f"SELECT COUNT(*) AS soni FROM generated_tests WHERE {shart}", params)
    soni = cur.fetchone()["soni"]
    cur.close()
    conn.close()
    return {"soni": soni}


_STANDARD_URINISH_JADVALI_BOR = None


def _standard_urinish_jadvali_bormi(cur) -> bool:
    """Migratsiya holatini har test so'rovida qayta-qayta tekshirmaydi."""
    global _STANDARD_URINISH_JADVALI_BOR
    if _STANDARD_URINISH_JADVALI_BOR is not None:
        return _STANDARD_URINISH_JADVALI_BOR
    cur.execute("SELECT to_regclass('public.standard_test_attempts') AS table_name")
    row = cur.fetchone()
    _STANDARD_URINISH_JADVALI_BOR = bool(row and row["table_name"])
    return _STANDARD_URINISH_JADVALI_BOR


_SAVOL_JAVOB_TARIXI_TAYYOR = False


def _savol_javob_tarixi_tayyorla(cur):
    """Issiq test yo'lida takroriy CREATE TABLE locklarini yo'qotadi."""
    global _SAVOL_JAVOB_TARIXI_TAYYOR
    if _SAVOL_JAVOB_TARIXI_TAYYOR:
        return
    cur.execute("SELECT to_regclass('public.savol_javob_tarixi') IS NOT NULL AS tayyor")
    tekshiruv = cur.fetchone()
    if tekshiruv and tekshiruv["tayyor"]:
        _SAVOL_JAVOB_TARIXI_TAYYOR = True
        return
    cur.execute("""CREATE TABLE IF NOT EXISTS savol_javob_tarixi(
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL REFERENCES users(user_id),
        savol_id INTEGER NOT NULL,
        topic_code TEXT,
        difficulty TEXT,
        question_type TEXT,
        togri_mi BOOLEAN NOT NULL,
        yaratilgan_at TIMESTAMP DEFAULT NOW()
    )""")


def _standard_fan_ochko_kaliti(cur, topic_codes: list[str]) -> Optional[str]:
    """Client kombinatsiyasi emas, DTS'dagi bitta haqiqiy sinf+fan kaliti."""
    kodlar = sorted({str(code or "").strip() for code in topic_codes if str(code or "").strip()})
    if not kodlar:
        return None
    cur.execute(
        """SELECT topic_code,grade,subject_code FROM dts_tree
           WHERE topic_code=ANY(%s) AND is_deleted=FALSE""",
        (kodlar,),
    )
    rows = cur.fetchall()
    by_code = {row["topic_code"]: row for row in rows}
    if any(code not in by_code for code in kodlar):
        return None
    identities = set()
    for row in rows:
        parts = str(row["topic_code"] or "").split("-")
        subject_code = row["subject_code"] or (parts[1] if len(parts) > 1 else "")
        identities.add(f"{row['grade']}|{subject_code}")
    if len(identities) != 1:
        return None
    identity = next(iter(identities))
    return hashlib.sha256(f"canonical-subject|{identity}".encode("utf-8")).hexdigest()


def _standard_urinish_yarat(cur, user_id: Optional[int], topic_codes: list[str], savollar: list[dict]) -> Optional[str]:
    if user_id is None or not savollar or not _standard_urinish_jadvali_bormi(cur):
        return None
    attempt_id = secrets.token_urlsafe(24)
    haqiqiy_kodlar = sorted({str(row.get("topic_code") or "").strip() for row in savollar if row.get("topic_code")})
    if not haqiqiy_kodlar:
        haqiqiy_kodlar = sorted({str(code or "").strip() for code in topic_codes if str(code or "").strip()})
    content_key = _standard_fan_ochko_kaliti(cur, haqiqiy_kodlar) or "unrewarded"
    cur.execute(
        """INSERT INTO standard_test_attempts(
             attempt_id,user_id,topic_codes,question_ids,expected_count,content_key
           ) VALUES(%s,%s,%s,%s,%s,%s)""",
        (
            attempt_id,
            user_id,
            haqiqiy_kodlar,
            [int(row["id"]) for row in savollar],
            len(savollar),
            content_key,
        ),
    )
    return attempt_id


@app.get("/api/test/{topic_code}")
def test_savollari(
    topic_code: str, soni: int = 10, qiyinlik: str = None,
    rasimli: bool = None, vaqtli: bool = None, yozuvli: bool = None,
    token: Optional[str] = None,
):
    """Berilgan mavzu bo'yicha tasodifiy savollarni qaytaradi.
    qiyinlik berilsa (oson/o'rta/qiyin/murakkab), faqat o'sha darajadagi
    savollar tanlanadi вЂ” bo'lmasa (aralash) barcha darajalardan aralash.
    rasimli/vaqtli/yozuvli вЂ” True/False bo'lsa mos savollargina tanlanadi,
    berilmasa (None) hammasidan aralash."""
    user_id = _jwt_tekshir(token) if token else None
    conn = _db()
    cur = conn.cursor()
    shart = "topic_code = %s"
    params = [topic_code]
    if qiyinlik:
        shart += " AND difficulty = %s"
        params.append(qiyinlik)
    qoshimcha, qoshimcha_params = _qoshimcha_test_shartlari(rasimli, vaqtli, yozuvli)
    shart += qoshimcha
    params += qoshimcha_params
    params.append(soni)
    cur.execute(f"""
        SELECT id, topic_code, question, option_a, option_b, option_c, option_d,
               question_type, correct_answer, is_latex, time_limit, difficulty,
               CASE
                   WHEN rasm_malumot IS NOT NULL THEN '/api/test_rasmi/' || id::text
                   ELSE COALESCE(NULLIF(image_url, ''), NULLIF(image_file_id, ''))
               END AS rasm_id
        FROM generated_tests
        WHERE {shart}
        ORDER BY RANDOM()
        LIMIT %s
    """, params)
    savollar = cur.fetchall()

    if not savollar:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Bu mavzuda (tanlangan sozlamalar bo'yicha) savol topilmadi")

    # DIQQAT: bu yerda [ru]/[en] teglarini ATAYLAB OLIB TASHLAMAYMIZ вЂ”
    # frontend ularni ko'rsatishda yashiradi, lekin ovoz o'qishda AYNAN shu
    # teglar orqali qaysi so'z qaysi tilda o'qilishini aniqlaydi. Faqat
    # "10.0" -> "10" kabi raqam artefaktini tozalaymiz.
    for s in savollar:
        s["question"] = _raqam_artefaktini_tozala(s["question"])
        s["question"] = _yozma_savolga_format_korsatmasi(
            s["question"], s.get("correct_answer"), s.get("question_type")
        )
        for maydon in ("option_a", "option_b", "option_c", "option_d"):
            s[maydon] = _raqam_artefaktini_tozala(s[maydon])
        # Format ko'rsatmasi tuzildi; javobning o'zi klientga chiqmaydi.
        s.pop("correct_answer", None)

    attempt_id = _standard_urinish_yarat(cur, user_id, [topic_code], savollar)
    conn.commit()
    cur.close()
    conn.close()

    # correct_answer va explanation FRONTENDGA yubormaymiz вЂ” bular javob
    # berilgandan KEYIN, /api/test/javob_tekshir orqali ochiladi
    return {"topic_code": topic_code, "savollar": savollar, "attempt_id": attempt_id}


class AralashTestSorovi(BaseModel):
    topic_codes: list = []
    soni: int = 10
    token: Optional[str] = None
    qiyinlik: Optional[str] = None
    rasimli: Optional[bool] = None
    vaqtli: Optional[bool] = None
    yozuvli: Optional[bool] = None


class MustahkamlashTestSorovi(BaseModel):
    token: str
    topic_code: str
    togarak_id: Optional[int] = None
    asosiy_limit: int = 20
    spiral_limit: int = 5
    erkin_limit: int = 3


def _mustahkamlash_savollarini_ol(cur, kodlar, limit, chiqarilgan_idlar=None):
    """Bitta test ichida savol takrorlanmasdan tasodifiy savollarni oladi."""
    kodlar = sorted({str(k or "").strip() for k in kodlar if str(k or "").strip()})
    limit = max(0, min(int(limit or 0), 100))
    if not kodlar or not limit:
        return []
    chiqarilgan_idlar = list(chiqarilgan_idlar or [])
    cur.execute(
        """SELECT id,topic_code,question,option_a,option_b,option_c,option_d,
                  question_type,is_latex,time_limit,difficulty,
                  CASE WHEN rasm_malumot IS NOT NULL
                       THEN '/api/test_rasmi/' || id::text
                       ELSE COALESCE(NULLIF(image_url,''),NULLIF(image_file_id,'')) END AS rasm_id
           FROM generated_tests
           WHERE topic_code=ANY(%s) AND NOT (id=ANY(%s))
           ORDER BY RANDOM() LIMIT %s""",
        (kodlar, chiqarilgan_idlar, limit),
    )
    return list(cur.fetchall())


@app.post("/api/oquvchi/mustahkamlash-test")
def oquvchi_mustahkamlash_test(sorov: MustahkamlashTestSorovi):
    """Bugungi mavzu + 5 spiral + 3 erkin takrorlashni serverda yig'adi.

    Asosiy mavzuda 20 tadan kam savol bo'lsa mavjud savollarning barchasi
    olinadi. Uch bo'lim orasida bitta savol qayta chiqmaydi. O'quvchi klub
    mavzusini ishlasa a'zolik ham serverda tekshiriladi.
    """
    user_id = _jwt_tekshir(sorov.token)
    topic_code = str(sorov.topic_code or "").strip()
    if not topic_code:
        raise HTTPException(status_code=400, detail="Mavzuni tanlang")
    if not 1 <= sorov.asosiy_limit <= 20 or not 0 <= sorov.spiral_limit <= 5 or not 0 <= sorov.erkin_limit <= 3:
        raise HTTPException(status_code=400, detail="Mustahkamlash testi limitlari noto'g'ri")

    conn = _db()
    cur = conn.cursor()
    try:
        if sorov.togarak_id is not None and not _togarak_kontent_ruxsat_bormi(
            cur, user_id, sorov.togarak_id
        ):
            raise HTTPException(status_code=403, detail="Siz bu to'garak a'zosi emassiz")
        cur.execute(
            """SELECT grade,subject_code,subject_name,quarter,topic_code
               FROM dts_tree WHERE topic_code=%s AND is_deleted=FALSE LIMIT 1""",
            (topic_code,),
        )
        mavzu = cur.fetchone()
        if not mavzu:
            raise HTTPException(status_code=404, detail="Mavzu DTS ro'yxatidan topilmadi")

        # Shu mavzuning barcha kichik kodlari asosiy bo'limga kiradi.
        cur.execute(
            """SELECT DISTINCT topic_code FROM dts_tree
               WHERE grade=%s AND subject_code=%s AND is_deleted=FALSE
                 AND COALESCE(mavzu_name,bolim_name,bob_name)=(
                   SELECT COALESCE(mavzu_name,bolim_name,bob_name)
                   FROM dts_tree WHERE topic_code=%s AND is_deleted=FALSE LIMIT 1
                 )""",
            (mavzu["grade"], mavzu["subject_code"], topic_code),
        )
        asosiy_kodlar = [r["topic_code"] for r in cur.fetchall()]

        # Spiral: joriy fan bo'yicha kod tartibida oldingi 5 ta mavzu.
        cur.execute(
            """SELECT topic_code FROM (
                 SELECT DISTINCT topic_code FROM dts_tree
                 WHERE grade=%s AND subject_code=%s AND is_deleted=FALSE
                   AND topic_code < %s AND NOT (topic_code=ANY(%s))
                 ORDER BY topic_code DESC LIMIT 5
               ) old_topics ORDER BY topic_code""",
            (mavzu["grade"], mavzu["subject_code"], topic_code, asosiy_kodlar),
        )
        spiral_kodlar = [r["topic_code"] for r in cur.fetchall()]

        # Erkin: shu sinfdagi boshqa mavzulardan; asosiy va spiral chiqariladi.
        chiqarilgan_kodlar = asosiy_kodlar + spiral_kodlar
        cur.execute(
            """SELECT DISTINCT topic_code FROM dts_tree
               WHERE grade=%s AND is_deleted=FALSE AND NOT (topic_code=ANY(%s))""",
            (mavzu["grade"], chiqarilgan_kodlar),
        )
        erkin_kodlar = [r["topic_code"] for r in cur.fetchall()]

        asosiy = _mustahkamlash_savollarini_ol(cur, asosiy_kodlar, sorov.asosiy_limit)
        ishlatilgan = {r["id"] for r in asosiy}
        spiral = _mustahkamlash_savollarini_ol(cur, spiral_kodlar, sorov.spiral_limit, ishlatilgan)
        ishlatilgan.update(r["id"] for r in spiral)
        erkin = _mustahkamlash_savollarini_ol(cur, erkin_kodlar, sorov.erkin_limit, ishlatilgan)
        savollar = []
        for bolim, rows in (("asosiy", asosiy), ("spiral", spiral), ("erkin", erkin)):
            for row in rows:
                row["bolim"] = bolim
                row["question"] = _yozma_savolga_format_korsatmasi(
                    _raqam_artefaktini_tozala(row["question"]), None, row.get("question_type")
                )
                for maydon in ("option_a", "option_b", "option_c", "option_d"):
                    row[maydon] = _raqam_artefaktini_tozala(row[maydon])
                savollar.append(row)
        if not asosiy:
            raise HTTPException(status_code=404, detail="Bu mavzuda hali test savollari yo'q")
        barcha_kodlar = sorted({r["topic_code"] for r in savollar})
        attempt_id = _standard_urinish_yarat(cur, user_id, barcha_kodlar, savollar)
        conn.commit()
        return {
            "mode": "mustahkamlash",
            "topic_code": topic_code,
            "topic_codes": barcha_kodlar,
            "subject": mavzu["subject_name"],
            "savollar": savollar,
            "attempt_id": attempt_id,
            "tarkib": {
                "asosiy": len(asosiy), "spiral": len(spiral),
                "erkin": len(erkin), "jami": len(savollar),
            },
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


@app.post("/api/test_aralash")
def aralash_test_savollari(sorov: AralashTestSorovi):
    """Bir nechta TANLANGAN mavzudan aralashtirib savollar oladi вЂ”
    o'quvchi bir nechta mavzuni bir vaqtda takrorlashi uchun."""
    kodlar = [str(k).strip() for k in sorov.topic_codes if k and str(k).strip()]
    if not kodlar:
        raise HTTPException(status_code=400, detail="Kamida bitta mavzu tanlang")

    user_id = _jwt_tekshir(sorov.token) if sorov.token else None
    conn = _db()
    cur = conn.cursor()
    shart = "topic_code = ANY(%s)"
    params = [kodlar]
    if sorov.qiyinlik:
        shart += " AND difficulty = %s"
        params.append(sorov.qiyinlik)
    qoshimcha, qoshimcha_params = _qoshimcha_test_shartlari(sorov.rasimli, sorov.vaqtli, sorov.yozuvli)
    shart += qoshimcha
    params += qoshimcha_params
    params.append(sorov.soni)
    cur.execute(f"""
        SELECT id, topic_code, question, option_a, option_b, option_c, option_d,
               question_type, correct_answer, is_latex, time_limit, difficulty,
               CASE
                   WHEN rasm_malumot IS NOT NULL THEN '/api/test_rasmi/' || id::text
                   ELSE COALESCE(NULLIF(image_url, ''), NULLIF(image_file_id, ''))
               END AS rasm_id
        FROM generated_tests
        WHERE {shart}
        ORDER BY RANDOM()
        LIMIT %s
    """, params)
    savollar = cur.fetchall()

    if not savollar:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Tanlangan mavzu/sozlamalarda savol topilmadi")

    for s in savollar:
        s["question"] = _raqam_artefaktini_tozala(s["question"])
        s["question"] = _yozma_savolga_format_korsatmasi(
            s["question"], s.get("correct_answer"), s.get("question_type")
        )
        for maydon in ("option_a", "option_b", "option_c", "option_d"):
            s[maydon] = _raqam_artefaktini_tozala(s[maydon])
        s.pop("correct_answer", None)

    attempt_id = _standard_urinish_yarat(cur, user_id, kodlar, savollar)
    conn.commit()
    cur.close()
    conn.close()

    return {"topic_codes": kodlar, "savollar": savollar, "attempt_id": attempt_id}


class BittaJavob(BaseModel):
    savol_id: int
    tanlangan: str
    token: str
    attempt_id: str


def _raqam_artefaktini_tozala(matn):
    """"10.0" kabi butun sonlarni "10" ga soddalashtiradi вЂ” teglarga tegmaydi."""
    if not matn:
        return matn
    tozalangan = matn.strip()
    if re.fullmatch(r"-?\d+\.0+", tozalangan):
        tozalangan = tozalangan.split(".")[0]
    return tozalangan


def _matnni_tozala(matn):
    """[ru]...[/ru] kabi teglarni olib tashlaydi, va "10.0" kabi butun
    sonlarni "10" ga soddalashtiradi вЂ” ham ko'rsatish, ham solishtirish
    uchun ishlatiladi."""
    if not matn:
        return matn
    tozalangan = re.sub(r"\[/?[a-zA-Z]+\]", "", matn).strip()
    if re.fullmatch(r"-?\d+\.0+", tozalangan):
        tozalangan = tozalangan.split(".")[0]
    return tozalangan


def _togri_harfni_top(option_a, option_b, option_c, option_d, correct_answer):
    """correct_answer ustuni ba'zan harf (A/B/C/D), ba'zan variantning
    TO'LIQ MATNI (masalan "20.0" yoki "[ru]СЂРѕРґРЅРѕР№ СЏР·С‹Рє[/ru]") ko'rinishida
    saqlangan вЂ” ikkalasini ham qamrab olib, HAQIQIY to'g'ri harfni
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


def _yozma_javobni_normallash(matn: str) -> str:
    """Yozma javobni xavfsiz va tilga zarar yetkazmaydigan ko'rinishga keltiradi."""
    tozalangan = _matnni_tozala(matn or "") or ""
    tozalangan = unicodedata.normalize("NFC", tozalangan)
    tozalangan = re.sub(r"[вЂвЂ™К»Кј']", "вЂ™", tozalangan)
    tozalangan = re.sub(r"\s+", " ", tozalangan).strip()
    return tozalangan.casefold()


def _yozma_javob_togrimi(given: str, correct: str) -> bool:
    """Yozuvli (write_answer) javoblarni tekshiradi вЂ” botdagi
    check_text_answer/is_match bilan bir xil qoidalar."""
    given = _yozma_javobni_normallash(given)
    correct = _yozma_javobni_normallash(correct)
    if given == correct:
        return True
    try:
        return float(given) == float(correct)
    except (ValueError, TypeError):
        pass
    if len(correct) <= 5:
        return given == correct
    if len(correct) > 10 and correct in given:
        return True
    return False


@app.post("/api/test/javob_tekshir")
def javob_tekshir(j: BittaJavob):
    """Bitta savolga berilgan javobni DARHOL tekshiradi вЂ” to'g'ri javob
    va tushuntirishni shu yerda ochadi (foydalanuvchi javob bergandan
    keyin, savol ko'rsatilganda EMAS вЂ” aks holda oldindan ko'rinib qolardi).
    Yozuvli (write_answer) savollarda harf emas, yozilgan matn solishtiriladi."""
    user_id = _jwt_tekshir(j.token)
    conn = _db()
    cur = conn.cursor()
    if not _standard_urinish_jadvali_bormi(cur):
        cur.close()
        conn.close()
        raise HTTPException(status_code=503, detail="Avval 015 migratsiyasini bajaring")
    cur.execute(
        """SELECT 1 FROM standard_test_attempts
           WHERE attempt_id=%s AND user_id=%s AND status='active'
             AND expires_at>NOW() AND %s=ANY(question_ids)""",
        (j.attempt_id, user_id, j.savol_id),
    )
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=409, detail="Bu savol faol test urinishingizga tegishli emas")
    cur.execute("""SELECT option_a, option_b, option_c, option_d, correct_answer,
                          explanation, question_type
                   FROM generated_tests WHERE id=%s""", (j.savol_id,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    if not r:
        raise HTTPException(status_code=404, detail="Savol topilmadi")

    if r["question_type"] == "write_answer":
        togri = _yozma_javob_togrimi(j.tanlangan, r["correct_answer"])
        togri_javob = _matnni_tozala(r["correct_answer"])
    else:
        togri_javob = _togri_harfni_top(r["option_a"], r["option_b"], r["option_c"], r["option_d"], r["correct_answer"])
        togri = (j.tanlangan or "").strip().upper() == togri_javob

    return {"togrimi": togri, "togri_javob": togri_javob, "tushuntirish": _matnni_tozala(r["explanation"])}


@app.get("/api/rasm/{file_id}")
async def rasm_proxy(file_id: str):
    """Telegram'da saqlangan rasmni saytda ko'rsatish uchun oraliq xizmat.

    MUHIM: generated_tests.image_url ko'pincha haqiqiy Telegram file_id
    EMAS вЂ” "1-02-1-01-01-01-001-1" kabi KOLLAJ KODI bo'ladi. Botning o'zi
    ham bu kodni to'g'ridan-to'g'ri ishlatmaydi вЂ” avval "images" jadvalidan
    (nameв†’file_id) haqiqiy Telegram file_id'ni qidiradi (Talim.py'dagi
    bilan AYNAN bir xil mantiq). Shu sabab bu yerda ham AVVAL images
    jadvalidan qidiramiz, faqat topilmasa file_id'ning O'ZINI ishlatamiz."""
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="Bot tokeni sozlanmagan")
    if file_id.startswith("http"):
        # Ba'zi eski yozuvlarda image_url to'g'ridan URL bo'lishi mumkin
        return RedirectResponse(file_id)

    haqiqiy_file_id = file_id
    try:
        conn = _db()
        cur = conn.cursor()
        cur.execute("SELECT file_id FROM images WHERE name=%s LIMIT 1", (file_id,))
        r = cur.fetchone()
        cur.close()
        conn.close()
        if r and r["file_id"]:
            haqiqiy_file_id = r["file_id"]
    except Exception:
        pass  # images jadvali bo'lmasa ham, file_id'ning o'zi bilan urinib ko'ramiz

    async with httpx.AsyncClient() as client:
        meta = await client.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile",
                                 params={"file_id": haqiqiy_file_id})
        meta_data = meta.json()
        if not meta_data.get("ok"):
            raise HTTPException(status_code=404, detail="Rasm topilmadi")
        file_path = meta_data["result"]["file_path"]
        img = await client.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}")
        return Response(content=img.content, media_type="image/jpeg")


EDGE_OVOZ = {
    "qiz": "uz-UZ-MadinaNeural",
    "ogil": "uz-UZ-SardorNeural",
}
_TIL_OVOZLARI = {
    "en": {"qiz": "en-US-JennyNeural", "ogil": "en-US-GuyNeural"},
    "ru": {"qiz": "ru-RU-SvetlanaNeural", "ogil": "ru-RU-DmitryNeural"},
    "de": {"qiz": "de-DE-KatjaNeural", "ogil": "de-DE-ConradNeural"},
    "fr": {"qiz": "fr-FR-DeniseNeural", "ogil": "fr-FR-HenriNeural"},
    "es": {"qiz": "es-ES-ElviraNeural", "ogil": "es-ES-AlvaroNeural"},
    "ar": {"qiz": "ar-EG-SalmaNeural", "ogil": "ar-EG-ShakirNeural"},
    "tr": {"qiz": "tr-TR-EmelNeural", "ogil": "tr-TR-AhmetNeural"},
    "zh": {"qiz": "zh-CN-XiaoxiaoNeural", "ogil": "zh-CN-YunxiNeural"},
    "ja": {"qiz": "ja-JP-NanamiNeural", "ogil": "ja-JP-KeitaNeural"},
    "ko": {"qiz": "ko-KR-SunHiNeural", "ogil": "ko-KR-InJoonNeural"},
}

# Railway jarayoni ichidagi kichik LRU kesh. Bir xil savol qayta o'qilganda
# edge-tts'ni yangidan kutmaymiz; hajm cheklovi servis xotirasini himoya qiladi.
_OVOZ_KESH = OrderedDict()
_OVOZ_KESH_JAMI_BAYT = 0
_OVOZ_KESH_MAX_ELEMENT = 96
_OVOZ_KESH_MAX_BAYT = 48 * 1024 * 1024


def _ovoz_keshdan_ol(kalit: str):
    audio = _OVOZ_KESH.pop(kalit, None)
    if audio is not None:
        _OVOZ_KESH[kalit] = audio
    return audio


def _ovoz_keshga_qoy(kalit: str, audio: bytes):
    global _OVOZ_KESH_JAMI_BAYT
    eski = _OVOZ_KESH.pop(kalit, None)
    if eski is not None:
        _OVOZ_KESH_JAMI_BAYT -= len(eski)
    _OVOZ_KESH[kalit] = audio
    _OVOZ_KESH_JAMI_BAYT += len(audio)
    while (
        len(_OVOZ_KESH) > _OVOZ_KESH_MAX_ELEMENT
        or _OVOZ_KESH_JAMI_BAYT > _OVOZ_KESH_MAX_BAYT
    ):
        _, ochirilgan = _OVOZ_KESH.popitem(last=False)
        _OVOZ_KESH_JAMI_BAYT -= len(ochirilgan)

# в”Ђв”Ђ Ovoz uchun matnni tayyorlash вЂ” botdagi ovoz.py bilan bir xil qoidalar в”Ђв”Ђ
_BIRLIK = ["", "bir", "ikki", "uch", "to'rt", "besh", "olti", "yetti", "sakkiz", "to'qqiz"]
_ONLIK = ["", "o'n", "yigirma", "o'ttiz", "qirq", "ellik", "oltmish", "yetmish", "sakson", "to'qson"]
_TARTIB = {
    "bir": "birinchi", "ikki": "ikkinchi", "uch": "uchinchi", "to'rt": "to'rtinchi",
    "besh": "beshinchi", "olti": "oltinchi", "yetti": "yettinchi", "sakkiz": "sakkizinchi",
    "to'qqiz": "to'qqizinchi", "o'n": "o'ninchi", "yigirma": "yigirmanchi", "o'ttiz": "o'ttizinchi",
    "qirq": "qirqinchi", "ellik": "ellikinchi", "oltmish": "oltmishinchi", "yetmish": "yetmishinchi",
    "sakson": "saksoninchi", "to'qson": "to'qsoninchi", "yuz": "yuzinchi", "ming": "minginchi",
}


def _son_soz(n: int) -> str:
    if n == 0:
        return "nol"
    if n < 0:
        return "minus " + _son_soz(-n)
    q = []
    if n >= 1000:
        m = n // 1000
        q.append("ming" if m == 1 else _son_soz(m) + " ming")
        n %= 1000
    if n >= 100:
        y = n // 100
        q.append("yuz" if y == 1 else _BIRLIK[y] + " yuz")
        n %= 100
    if n >= 10:
        q.append(_ONLIK[n // 10])
        n %= 10
    if n > 0:
        q.append(_BIRLIK[n])
    return " ".join(x for x in q if x)


_MATH_MAP = [
    (r"\s*в‰¤\s*", " kichik yoki teng "),
    (r"\s*в‰Ґ\s*", " katta yoki teng "),
    (r"\s*в‰ \s*", " teng emas "),
    (r"\s*\+\s*", " plyus "),
    (r"\s*-\s*", " minus "),
    (r"\s*[Г—В·]\s*|\s*\*\s*", " ko'paytirilgan "),
    (r"\s*Г·\s*", " bo'lingan "),
    (r"\s*=\s*", " teng "),
    (r"\s*>\s*", " katta "),
    (r"\s*<\s*", " kichik "),
    (r"\s*%\s*", " foiz "),
    (r"\s*в‰€\s*", " taxminan "),
]


_APOSTROF_VARIANTLARI = "\u2018\u2019\u02BB\u02BC\u0060\u00B4\u2032"


def _apostrofni_tuzat(matn: str) -> str:
    """o'/g' dan keyingi turli tirnoq-apostrof belgilarini ('  '  К»  Кј  `  Вґ)
    bitta standart apostrofga keltiradi вЂ” aks holda ovoz ularni "o'"/"g'"
    deb emas, oddiy "o"/"g" deb yoki umuman boshqacha o'qib yuboradi."""
    return re.sub(rf"([oOgG])[{_APOSTROF_VARIANTLARI}']", r"\1'", matn)


def _c_va_w_tuzat(matn: str) -> str:
    """"c" harfini (agar "ch" qismi bo'lmasa) inglizcha qoidaga ko'ra
    s/k tovushiga, "w" ni esa "v" ga almashtiradi вЂ” o'zbekcha ovoz "c"ni
    "ch" deb, "w"ni esa noto'g'ri o'qib yuborishining oldini oladi."""
    natija = []
    n = len(matn)
    i = 0
    while i < n:
        ch = matn[i]
        if ch.lower() == "c" and (i + 1 >= n or matn[i + 1].lower() != "h"):
            keyingi = matn[i + 1] if i + 1 < n else ""
            alm = "s" if keyingi.lower() in ("e", "i", "y") else "k"
            natija.append(alm.upper() if ch.isupper() else alm)
        elif ch.lower() == "w":
            natija.append("V" if ch.isupper() else "v")
        else:
            natija.append(ch)
        i += 1
    return "".join(natija)


_LATEX_KASR_NAQSHI = re.compile(r"\\(?:tfrac|dfrac|cfrac|frac)\s*\{(-?\d+)\}\s*\{(-?\d+)\}")
_LATEX_OZGARUVCHI_NAQSHI = re.compile(r"(?<![a-zA-ZК»Кј'])([xyzn])(?![a-zA-ZК»Кј'])")
_LATEX_OZGARUVCHILAR = {"x": "iks", "y": "igrik", "z": "zet", "n": "en"}


def _lat_va_latex_ochish(matn: str) -> str:
    """[lat]...[/lat] va $...$ teglarini ochib, ICHIDAGI LaTeX
    buyruqlarini (\\tfrac, \\sqrt, \\times va h.k.) tabiiy o'zbekcha
    nutqqa aylantiradi. Bu вЂ” punktuatsiya bosqichidan (figurali qavslar
    vergulga aylanadigan) OLDIN ishlashi SHART, aks holda LaTeX
    tuzilishi buzilib, keyin aniqlab bo'lmay qoladi."""
    m = re.sub(r"\[lat\](.*?)\[/lat\]", r"\1", matn, flags=re.S)
    m = re.sub(r"\$([^$]+)\$", r"\1", m)
    m = re.sub(r"\\(?:left|right)", "", m)

    # Aralash son: raqamdan keyin (bo'shliqli/bo'shliqsiz) kasr buyrug'i
    # kelsa вЂ” "butun" so'zi qo'shiladi (masalan 6\tfrac{1}{2} -> "olti butun ikkidan bir")
    m = re.sub(r"(\d)\s*(?=\\(?:tfrac|dfrac|cfrac|frac))", r"\1 butun ", m)

    def _kasr_latex(x):
        a, b = int(x.group(1)), int(x.group(2))
        return f" {_son_soz(b)}dan {_son_soz(a)} "
    m = _LATEX_KASR_NAQSHI.sub(_kasr_latex, m)

    m = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r" \1 ning kvadrat ildizi ", m)
    m = re.sub(r"\\times", " marta ", m)
    m = re.sub(r"\\cdot", " marta ", m)
    m = re.sub(r"\\div", " bo'lib ", m)
    m = re.sub(r"\\pm", " plyus-minus ", m)
    m = re.sub(r"\\leq", " kichik yoki teng ", m)
    m = re.sub(r"\\geq", " katta yoki teng ", m)
    m = re.sub(r"\\neq", " teng emas ", m)
    m = re.sub(r"\\infty", " cheksizlik ", m)
    m = re.sub(r"\\approx", " taxminan teng ", m)
    m = re.sub(r"\\pi\b", " pi ", m)

    # Darajalar: x^2 -> "x kvadrat", x^3 -> "x kub",
    # x^{5} -> "x ning beshinchi darajasi".
    def _daraja(x):
        asos, daraja = x.group(1), int(x.group(2))
        if daraja == 2:
            return f" {asos} kvadrat "
        if daraja == 3:
            return f" {asos} kub "
        return f" {asos} ning {_son_soz(daraja)}inchi darajasi "
    m = re.sub(r"([0-9A-Za-z]+)\s*\^\s*\{?(\d+)\}?", _daraja, m)

    # O'lchov birliklari вЂ” to'liq so'zga
    for naqsh, alm in [
        (r"\bkm/soat\b", " kilometr soatiga "),
        (r"\bkg\b", " kilogramm "), (r"\bgr\b", " gramm "),
        (r"\bmm\b", " millimetr "), (r"\bsm\b", " santimetr "), (r"\bkm\b", " kilometr "),
        (r"\bml\b", " millilitr "), (r"\bl\b", " litr "),
        (r"\bsm2\b|\bsmВІ\b", " kvadrat santimetr "), (r"\bm2\b|\bmВІ\b", " kvadrat metr "),
        (r"\bsm3\b|\bsmВі\b", " kub santimetr "), (r"\bm3\b|\bmВі\b", " kub metr "),
        (r"\bm\b", " metr "),
    ]:
        m = re.sub(naqsh, alm, m, flags=re.I)

    # Matematik o'zgaruvchilar вЂ” songa yopishgan bo'lsa ham (masalan "2x")
    m = _LATEX_OZGARUVCHI_NAQSHI.sub(lambda x: f" {_LATEX_OZGARUVCHILAR[x.group(1)]} ", m)
    return m


def _ovoz_uchun_tayyorla(matn: str) -> str:
    """Xom matn -> ovoz aniq o'qiydigan matn вЂ” botdagi ovoz.py:tayyorla
    bilan bir xil (matematik belgilar so'zga, sonlar so'zga, teglar tozalanadi)."""
    m = _lat_va_latex_ochish(matn) or ""
    m = _matnni_tozala(m) or ""
    m = _apostrofni_tuzat(m)
    m = _c_va_w_tuzat(m)
    m = re.sub(r"<[^>]+>", " ", m)
    m = re.sub(r"_{2,}", " bo'sh joy ", m)  # "___" (bo'sh joy) вЂ” "pastki chiziq" deb o'qilmasin
    m = re.sub(r"[_`#]+", "", m)  # * ni bu yerda OLIB TASHLAMAYMIZ вЂ” pastda MATH_MAP "ko'paytiruv"ga o'giradi
    m = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", " ", m)
    m = re.sub(r"https?://\S+", " havola ", m)

    # Kasrlar: 1/2 -> ikkidan bir (matematikadan oldin)
    def _kasr(x):
        a, b = int(x.group(1)), int(x.group(2))
        return f" {_son_soz(b)}dan {_son_soz(a)} "
    m = re.sub(r"\b(\d{1,3})\s*/\s*(\d{1,3})\b", _kasr, m)

    for naqsh, alm in _MATH_MAP:
        m = re.sub(naqsh, alm, m)

    # 5-sinf -> beshinchi sinf
    def _t(x):
        n = int(x.group(1))
        soz = _son_soz(n).split()
        soz[-1] = _TARTIB.get(soz[-1], soz[-1] + "inchi")
        return f"{' '.join(soz)} {x.group(2)}"
    m = re.sub(r"\b(\d{1,4})-(sinf|mashq|dars|savol|misol|bob|bet|mavzu|qism|topshiriq)\b", _t, m, flags=re.I)

    # 3,5 -> uch butun besh
    def _b(x):
        return f"{_son_soz(int(x.group(1)))} butun {_son_soz(int(x.group(2)))}"
    m = re.sub(r"\b(\d+)[,.](\d+)\b", _b, m)

    # Qolgan sonlar so'zga
    def _o(x):
        n = int(x.group(0))
        return _son_soz(n) if n < 1000000 else x.group(0)
    m = re.sub(r"\b\d{1,6}\b", _o, m)

    # Tinish belgilarini pauzaga aylantirish
    m = m.replace(":", ",").replace(";", ",")
    m = re.sub(r"\s*[\(\[\{]\s*", ", ", m)
    m = re.sub(r"\s*[\)\]\}]\s*", ", ", m)
    m = re.sub(r'["В«В»вЂћвЂњвЂќ]', " ", m)
    m = re.sub(r"\s*[вЂ“вЂ”/|]\s*", ", ", m)
    m = re.sub(r"\s*[вЂўв–Єв—Џв—‹*]\s*", ", ", m)
    m = re.sub(r"[вЂ¦]+", ".", m)
    m = re.sub(r"\.{2,}", ".", m)
    m = re.sub(r"(?<=\w)-(?=\w)", " ", m)
    m = re.sub(r"(,\s*){2,}", ", ", m)
    m = re.sub(r"\s+([.,!?])", r"\1", m)
    m = re.sub(r",\s*([.!?])", r"\1", m)
    m = re.sub(r"([.!?])\s*[.,]+", r"\1", m)
    m = re.sub(r"([.!?])\s*([.!?])", r"\1", m)
    m = re.sub(r"\s{2,}", " ", m).strip()
    return m.strip(" ,.")


_TIL_TEG_NAQSHI = re.compile(r"\[(uz|en|ru)\](.*?)\[/\1\]", re.S | re.I)


def _ovoz_tilini_tuzat(til: str) -> str:
    til = str(til or "").strip().lower().replace("_", "-").split("-", 1)[0]
    return til if til == "uz" or til in _TIL_OVOZLARI else "uz"


def _ovoz_jinsini_tuzat(jins: str) -> str:
    jins = str(jins or "").strip().lower()
    return "ogil" if jins in {"ogil", "o'g'il", "erkak", "male", "boy"} else "qiz"


_XORIJIY_MATEMATIKA = {
    "en": {
        "fraction": "{a} over {b}", "sqrt": "square root of {x}",
        "square": "{x} squared", "cube": "{x} cubed", "power": "{x} to the power of {n}",
        "+": " plus ", "-": " minus ", "Г—": " times ", "В·": " times ", "*": " times ",
        "Г·": " divided by ", "=": " equals ", "в‰¤": " less than or equal to ",
        "в‰Ґ": " greater than or equal to ", "в‰ ": " not equal to ", "<": " less than ", ">": " greater than ",
    },
    "ru": {
        "fraction": "{a} РґРµР»С‘РЅРЅРѕРµ РЅР° {b}", "sqrt": "РєРІР°РґСЂР°С‚РЅС‹Р№ РєРѕСЂРµРЅСЊ РёР· {x}",
        "square": "{x} РІ РєРІР°РґСЂР°С‚Рµ", "cube": "{x} РІ РєСѓР±Рµ", "power": "{x} РІ СЃС‚РµРїРµРЅРё {n}",
        "+": " РїР»СЋСЃ ", "-": " РјРёРЅСѓСЃ ", "Г—": " СѓРјРЅРѕР¶РёС‚СЊ РЅР° ", "В·": " СѓРјРЅРѕР¶РёС‚СЊ РЅР° ", "*": " СѓРјРЅРѕР¶РёС‚СЊ РЅР° ",
        "Г·": " СЂР°Р·РґРµР»РёС‚СЊ РЅР° ", "=": " СЂР°РІРЅРѕ ", "в‰¤": " РјРµРЅСЊС€Рµ РёР»Рё СЂР°РІРЅРѕ ",
        "в‰Ґ": " Р±РѕР»СЊС€Рµ РёР»Рё СЂР°РІРЅРѕ ", "в‰ ": " РЅРµ СЂР°РІРЅРѕ ", "<": " РјРµРЅСЊС€Рµ ", ">": " Р±РѕР»СЊС€Рµ ",
    },
}


def _xorijiy_ovoz_uchun_tayyorla(matn: str, til: str) -> str:
    """Ingliz/rus bo'laklaridagi [lat] formulalarni o'sha tilda o'qitadi."""
    til = _ovoz_tilini_tuzat(til)
    lugat = _XORIJIY_MATEMATIKA.get(til)
    if not lugat:
        return re.sub(r"<[^>]+>", " ", str(matn or "")).strip()
    m = re.sub(r"\[lat\](.*?)\[/lat\]", r"\1", str(matn or ""), flags=re.S | re.I)
    m = re.sub(r"\$([^$]+)\$", r"\1", m)
    m = re.sub(r"\\(?:left|right)", "", m)
    m = re.sub(
        r"\\(?:tfrac|dfrac|cfrac|frac)\s*\{([^{}]+)\}\s*\{([^{}]+)\}",
        lambda x: " " + lugat["fraction"].format(a=x.group(1), b=x.group(2)) + " ",
        m,
    )
    m = re.sub(
        r"\\sqrt\s*\{([^{}]+)\}",
        lambda x: " " + lugat["sqrt"].format(x=x.group(1)) + " ",
        m,
    )

    def _xorijiy_daraja(x):
        asos, daraja = x.group(1), x.group(2)
        kalit = "square" if daraja == "2" else "cube" if daraja == "3" else "power"
        return " " + lugat[kalit].format(x=asos, n=daraja) + " "
    m = re.sub(r"([0-9A-Za-zРђ-РЇР°-СЏ]+)\s*\^\s*\{?([0-9]+)\}?", _xorijiy_daraja, m)
    for buyruq, belgi in [
        (r"\\times", "Г—"), (r"\\cdot", "В·"), (r"\\div", "Г·"),
        (r"\\leq", "в‰¤"), (r"\\geq", "в‰Ґ"), (r"\\neq", "в‰ "),
    ]:
        m = re.sub(buyruq, belgi, m)
    m = re.sub(r"\\pi\b", " pi ", m)
    for belgi in ("в‰¤", "в‰Ґ", "в‰ ", "+", "-", "Г—", "В·", "*", "Г·", "=", "<", ">"):
        m = re.sub(rf"\s*{re.escape(belgi)}\s*", lugat[belgi], m)
    m = re.sub(r"\\[A-Za-z]+", " ", m)
    m = re.sub(r"[{}]", " ", m)
    m = re.sub(r"<[^>]+>", " ", m)
    return re.sub(r"\s+", " ", m).strip()


def _ovoz_uchun_tayyorla_til(matn: str, til: str) -> str:
    til = _ovoz_tilini_tuzat(til)
    return _ovoz_uchun_tayyorla(matn) if til == "uz" else _xorijiy_ovoz_uchun_tayyorla(matn, til)


def _ovoz_qismlarga_bol(matn: str, asosiy_til: str = "uz"):
    """Matnni [en]...[/en] / [ru]...[/ru] teglariga qarab bo'laklarga
    ajratadi вЂ” har bo'lak (til, matn). Tegdan tashqaridagi matn HAR DOIM
    o'zbekcha o'qiladi; faqat aniq til tegi ichidagi qism tilini almashtiradi.
    ``asosiy_til`` eski frontendlar bilan API mosligi uchun saqlangan."""
    asosiy_til = "uz"
    qismlar = []
    oxiri = 0
    for m in _TIL_TEG_NAQSHI.finditer(matn):
        oldingi = matn[oxiri:m.start()]
        if oldingi.strip():
            qismlar.append((asosiy_til, oldingi))
        til, ichi = m.group(1).lower(), m.group(2)
        if ichi.strip():
            qismlar.append((_ovoz_tilini_tuzat(til), ichi))
        oxiri = m.end()
    qolgan = matn[oxiri:]
    if qolgan.strip():
        qismlar.append((asosiy_til, qolgan))
    return qismlar or [(asosiy_til, matn)]


@app.get("/api/ovoz")
async def ovoz_oqish(matn: str, jins: str = "qiz", asosiy_til: str = "uz"):
    """Berilgan matnni MP3 oqimi sifatida qaytaradi.

    Birinchi audio bo'lagi tayyor bo'lishi bilan javob brauzerga uzatiladi;
    to'liq MP3 tugashini kutmaydi. Tayyor bo'lgan to'liq audio keyingi
    bosishlar uchun xotira va brauzer keshida saqlanadi.
    """
    if not matn or not matn.strip():
        raise HTTPException(status_code=400, detail="Matn berilmagan")
    try:
        import edge_tts
    except ImportError:
        raise HTTPException(status_code=500, detail="edge-tts o'rnatilmagan")

    matn = matn[:1500]
    jins = _ovoz_jinsini_tuzat(jins)
    # Tegsiz matnning qat'iy asosiy tili вЂ” o'zbekcha. URL'dan tasodifan
    # asosiy_til=en kelishi butun testni inglizcha o'qitmasligi kerak.
    asosiy_til = "uz"
    kesh_kaliti = hashlib.sha256(
        f"v18.22\0{jins}\0{matn}".encode("utf-8")
    ).hexdigest()
    kesh_sarlavhalari = {
        "Cache-Control": "private, max-age=86400, stale-while-revalidate=604800",
        "ETag": f'"{kesh_kaliti}"',
        "X-Content-Type-Options": "nosniff",
    }
    keshdagi_audio = _ovoz_keshdan_ol(kesh_kaliti)
    if keshdagi_audio is not None:
        return Response(
            content=keshdagi_audio,
            media_type="audio/mpeg",
            headers={**kesh_sarlavhalari, "X-SamTM-Voice": "cache-hit"},
        )

    async def audio_bolaklari():
        for til, bolak in _ovoz_qismlarga_bol(matn, asosiy_til):
            if til in _TIL_OVOZLARI:
                voice = _TIL_OVOZLARI[til].get(jins, _TIL_OVOZLARI[til]["qiz"])
            else:
                voice = EDGE_OVOZ.get(jins, EDGE_OVOZ["qiz"])
            tayyor = _ovoz_uchun_tayyorla_til(bolak, til)
            if not tayyor.strip():
                continue
            com = edge_tts.Communicate(tayyor, voice)
            async for chunk in com.stream():
                if chunk["type"] == "audio" and chunk.get("data"):
                    yield bytes(chunk["data"])

    # HTTP sarlavhalari yuborilishidan avval birinchi audio bo'lagi borligini
    # tekshiramiz. Shunda bo'sh 200 javob o'rniga tushunarli xato qaytadi.
    audio_iterator = audio_bolaklari().__aiter__()
    try:
        birinchi_bolak = await audio_iterator.__anext__()
    except StopAsyncIteration:
        raise HTTPException(status_code=500, detail="Ovoz yaratilmadi")
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Ovoz xizmati vaqtincha javob bermadi",
        ) from exc

    async def oqim_va_kesh():
        yigildi = bytearray(birinchi_bolak)
        yield birinchi_bolak
        async for audio_bolagi in audio_iterator:
            yigildi.extend(audio_bolagi)
            yield audio_bolagi
        _ovoz_keshga_qoy(kesh_kaliti, bytes(yigildi))

    return StreamingResponse(
        oqim_va_kesh(),
        media_type="audio/mpeg",
        headers={**kesh_sarlavhalari, "X-SamTM-Voice": "stream-miss"},
    )


class JavobItem(BaseModel):
    savol_id: int
    tanlangan: str


class TestNatijaSorov(BaseModel):
    token: str
    topic_code: Optional[str] = None       # bitta mavzu bo'lsa
    topic_codes: Optional[list] = None  # aralash (bir nechta mavzu) bo'lsa
    javoblar: list[JavobItem]
    # Yangi analitika qatlami uchun. Eski frontend/bot bu maydonlarni
    # yubormasa ham avvalgi ishlash tartibi o'zgarmaydi.
    context_id: Optional[int] = None
    group_id: Optional[int] = None
    assignment_id: Optional[int] = None
    source_type: str = "independent"
    attempt_id: Optional[str] = None
    duration_seconds: Optional[int] = None
    hints_used: int = 0
    track: str = "standard"  # standard | olympiad
    # UMUMIY natija foizini TANLANGAN (masalan 10 ta) savol soniga nisbatan
    # hisoblash uchun вЂ” javob berilmagan savollar ham hisobga olinishi kerak
    # (aks holda 10 tadan 5 tasiga javob berib, hammasi to'g'ri bo'lsa, "100%"
    # ko'rsatib qo'yardi, holbuki haqiqatda 50%). Berilmasa вЂ” eski xulq-atvorga
    # (faqat javob berilganlar soniga nisbatan) qaytiladi.
    jami_savol_soni: Optional[int] = None


@app.post("/api/test/natija")
def test_natijasini_saqla(sorov: TestNatijaSorov):
    """Test yakunlanganda вЂ” har javobni backendda tekshiradi, foizni
    hisoblaydi, learned_topics'ga yozadi (bot ishlatgan JADVALNING O'ZIGA вЂ”
    shuning uchun dashboard darhol yangilanadi). Yozuvli (write_answer)
    savollar ham to'g'ri tekshiriladi, va xato qilingan savollar ro'yxati
    (sharh bilan) qaytariladi. Aralash (bir nechta mavzu) test bo'lsa, HAR
    BIR mavzu o'ziga tegishli savollar asosida alohida baholanadi."""
    user_id = _jwt_tekshir(sorov.token)
    savol_idlar = [j.savol_id for j in sorov.javoblar]
    if len(savol_idlar) != len(set(savol_idlar)):
        raise HTTPException(status_code=400, detail="Bir savol ikki marta yuborilgan")
    if sorov.jami_savol_soni is not None and (
        not 1 <= sorov.jami_savol_soni <= 1000
        or sorov.jami_savol_soni < len(savol_idlar)
    ):
        raise HTTPException(
            status_code=400,
            detail="Jami savol soni yuborilgan noyob javoblar sonidan kam bo'lmasligi kerak",
        )
    if sorov.duration_seconds is not None and not 0 <= sorov.duration_seconds <= 86400:
        raise HTTPException(status_code=400, detail="Test vaqti noto'g'ri")
    if not 0 <= sorov.hints_used <= 1000:
        raise HTTPException(status_code=400, detail="Ishora soni noto'g'ri")
    sorov.track = (sorov.track or "standard").strip().lower()
    if sorov.track not in {"standard", "olympiad"}:
        raise HTTPException(status_code=400, detail="Test yo'li standard yoki olympiad bo'lishi kerak")
    if sorov.attempt_id is not None:
        sorov.attempt_id = sorov.attempt_id.strip()
        if (
            not sorov.attempt_id
            or len(sorov.attempt_id) > 128
            or not re.fullmatch(r"[A-Za-z0-9._:-]+", sorov.attempt_id)
        ):
            raise HTTPException(status_code=400, detail="Test urinish identifikatori noto'g'ri")

    conn = _db()
    cur = conn.cursor()
    standard_urinish = None
    standard_content_key = None
    if sorov.attempt_id and _standard_urinish_jadvali_bormi(cur):
        cur.execute(
            """SELECT * FROM standard_test_attempts
               WHERE attempt_id=%s AND user_id=%s FOR UPDATE""",
            (sorov.attempt_id, user_id),
        )
        standard_urinish = cur.fetchone()
        if not standard_urinish:
            conn.rollback()
            cur.close()
            conn.close()
            raise HTTPException(status_code=409, detail="Test urinishi topilmadi yoki boshqa foydalanuvchiga tegishli")
        if standard_urinish["status"] == "completed" and standard_urinish.get("result"):
            result = standard_urinish["result"]
            conn.commit()
            cur.close()
            conn.close()
            return result
        if standard_urinish["status"] != "active" or standard_urinish["expires_at"] <= datetime.now(timezone.utc):
            conn.rollback()
            cur.close()
            conn.close()
            raise HTTPException(status_code=409, detail="Test urinishining muddati tugagan")
        expected_ids = {int(value) for value in (standard_urinish["question_ids"] or [])}
        if any(savol_id not in expected_ids for savol_id in savol_idlar):
            conn.rollback()
            cur.close()
            conn.close()
            raise HTTPException(status_code=409, detail="Yuborilgan savol server bergan testga tegishli emas")
        sorov.jami_savol_soni = int(standard_urinish["expected_count"])
        if standard_urinish["content_key"] != "unrewarded":
            standard_content_key = standard_urinish["content_key"]
    # SQL migratsiyasidagi learned_topics ko'prigi bot yozuvlarini ushlaydi.
    # Sayt esa pastda learning_events'ga bevosita yozgani uchun ayni
    # tranzaksiyada ko'prikka "takror yozma" belgisi beriladi.
    analitika_bor = _analitika_jadvallar_bormi(cur)
    if analitika_bor:
        cur.execute("SELECT set_config('app.analytics_direct_write','on',TRUE)")

    cur.execute(
        """SELECT id, topic_code, question, option_a, option_b, option_c, option_d,
                  correct_answer, question_type, explanation, difficulty
           FROM generated_tests WHERE id = ANY(%s)""",
        (savol_idlar,),
    )
    savollar_map = {r["id"]: r for r in cur.fetchall()}
    if len(savollar_map) != len(savol_idlar):
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Testdagi ayrim savollar topilmadi")

    _savol_javob_tarixi_tayyorla(cur)

    togri_soni = 0
    xatolar = []
    javob_tarixi_qatorlari = []  # (user_id, savol_id, topic_code, difficulty, question_type, togri_mi)
    natija_har_mavzu = {}  # topic_code -> {"togri": n, "jami": n}
    for j in sorov.javoblar:
        r = savollar_map.get(j.savol_id)
        if not r:
            continue
        if r["question_type"] == "write_answer":
            togri = _yozma_javob_togrimi(j.tanlangan, r["correct_answer"])
            togri_javob = _matnni_tozala(r["correct_answer"])
        else:
            togri_harf = _togri_harfni_top(r["option_a"], r["option_b"], r["option_c"], r["option_d"], r["correct_answer"])
            togri = (j.tanlangan or "").strip().upper() == togri_harf
            togri_javob = togri_harf

        javob_tarixi_qatorlari.append((user_id, j.savol_id, r["topic_code"], r["difficulty"], r["question_type"], togri))

        tk = r["topic_code"]
        natija_har_mavzu.setdefault(tk, {"togri": 0, "jami": 0})
        natija_har_mavzu[tk]["jami"] += 1
        if togri:
            togri_soni += 1
            natija_har_mavzu[tk]["togri"] += 1
        else:
            xatolar.append({
                "savol_id": j.savol_id,
                "savol": _matnni_tozala(r["question"]),
                "sizning_javob": j.tanlangan or "(javob berilmadi)",
                "togri_javob": togri_javob,
                "tushuntirish": _matnni_tozala(r["explanation"]),
            })

    # UMUMIY foiz вЂ” agar frontend "jami_savol_soni" yuborsa (tanlangan
    # savollar soni), o'shanga nisbatan hisoblanadi вЂ” javob berilmagan
    # savollar ham "noto'g'ri" sifatida hisobga kiradi. FAQAT shu
    # ko'rsatkichga (natija ekranidagi statistika) tegishli вЂ” pastdagi
    # mavzu bo'yicha learned_topics hisobiga ASLO ta'sir qilmaydi.
    jami = sorov.jami_savol_soni if sorov.jami_savol_soni else len(sorov.javoblar)
    foiz = round((togri_soni / jami) * 100) if jami else 0

    faol_topiclar = [
        (tk, hisob) for tk, hisob in natija_har_mavzu.items() if tk
    ]
    # Bir xil attempt_id tarmoq qayta yuborishi sabab takror kelsa,
    # kalitni atomar band qilamiz. Parallel kelgan ikkita so'rovdan faqat
    # bittasi learned_topics va javob tarixiga o'tadi.
    if analitika_bor and sorov.attempt_id and faol_topiclar:
        request_key = f"test:{user_id}:{sorov.attempt_id}"
        cur.execute(
            """INSERT INTO analytics_request_keys(
                 request_key,user_id,request_type,payload
               )
               VALUES(%s,%s,'test_attempt',%s::jsonb)
               ON CONFLICT DO NOTHING
               RETURNING request_key""",
            (
                request_key,
                user_id,
                json.dumps(
                    {
                        "topic_codes": [tk for tk, _ in faol_topiclar],
                        "submitted_answers": len(savol_idlar),
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        if not cur.fetchone():
            conn.rollback()
            cur.close()
            conn.close()
            return {
                "togri": togri_soni,
                "jami": jami,
                "foiz": foiz,
                "xatolar": xatolar,
                "takroriy_urinish": True,
            }

    # Har bir mavzu (aralash bo'lsa вЂ” bir nechtasi) o'ziga tegishli
    # savollar asosida alohida learned_topics'ga yoziladi.
    # MUHIM: bu FAQAT haqiqatan JAVOB BERILGAN savollar asosida hisoblanadi
    # (yuqoridagi tuzatish bunga tegmaydi) вЂ” o'quvchi o'zi urinib ko'rgan
    # mavzular bo'yicha bilim darajasi shu tarzda avvalgidek qoladi.
    topic_soni = max(1, len(faol_topiclar))
    jami_vaqt = max(0, sorov.duration_seconds or 0)
    jami_ishora = max(0, sorov.hints_used or 0)
    vaqt_asos, vaqt_qoldiq = divmod(jami_vaqt, topic_soni)
    ishora_asos, ishora_qoldiq = divmod(jami_ishora, topic_soni)
    for topic_index, (tk, hisob) in enumerate(faol_topiclar):
        mavzu_foizi = round((hisob["togri"] / hisob["jami"]) * 100) if hisob["jami"] else 0
        cur.execute("""
            INSERT INTO learned_topics(user_id, topic_code, score, repeat_count, learned_at, next_repeat)
            VALUES(%s,%s,%s,1,NOW(),CURRENT_DATE + INTERVAL '7 days')
            ON CONFLICT (user_id, topic_code) DO UPDATE SET
                score = EXCLUDED.score,
                repeat_count = learned_topics.repeat_count + 1,
                learned_at = NOW(),
                next_repeat = CURRENT_DATE + INTERVAL '7 days'
        """, (user_id, tk, mavzu_foizi))
        # PostgreSQL migratsiyasi o'rnatilgan bo'lsa, shu urinishni
        # manbasi bilan append-only learning_events tarixiga ham yozamiz.
        # Migratsiya hali ishlatilmagan serverda eski test funksiyasi
        # to'xtab qolmasligi uchun helper mavjudlikni o'zi tekshiradi.
        _analitika_test_voqeasini_saqla(
            cur=cur,
            user_id=user_id,
            sorov=sorov,
            topic_code=tk,
            togri=hisob["togri"],
            jami=hisob["jami"],
            foiz=mavzu_foizi,
            duration_seconds=(
                vaqt_asos + (1 if topic_index < vaqt_qoldiq else 0)
                if sorov.duration_seconds is not None else None
            ),
            hints_used=(
                ishora_asos + (1 if topic_index < ishora_qoldiq else 0)
            ),
        )
    if javob_tarixi_qatorlari:
        psycopg2.extras.execute_values(
            cur,
            "INSERT INTO savol_javob_tarixi(user_id, savol_id, topic_code, difficulty, question_type, togri_mi) VALUES %s",
            javob_tarixi_qatorlari,
        )
    # V18: oddiy test ham o'yinlar bilan bir xil hisob ochkosiga ulanadi.
    # 015 migratsiyasi hali o'rnatilmagan bo'lsa helper xavfsiz no-op qiladi;
    # natijaning akademik foizi esa avvalgidek learned_topics'da qoladi.
    ochko_natija = award_standard_test_points(
        cur,
        user_id=user_id,
        topic_codes=[tk for tk, _ in faol_topiclar],
        question_count=jami,
        answered_count=len(savol_idlar),
        percent=foiz,
        attempt_id=sorov.attempt_id,
        server_content_key=standard_content_key,
    )
    response = {
        "togri": togri_soni,
        "jami": jami,
        "foiz": foiz,
        "xatolar": xatolar,
        "ochko": ochko_natija,
    }
    if standard_urinish:
        cur.execute(
            """UPDATE standard_test_attempts
               SET status='completed',completed_at=NOW(),result=%s::jsonb
               WHERE attempt_id=%s""",
            (
                json.dumps(response, ensure_ascii=False, default=str),
                standard_urinish["attempt_id"],
            ),
        )
    conn.commit()
    cur.close()
    conn.close()

    return response


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# SAYTDAN BOTGA ULASH вЂ” teskari yo'nalish
# (Saytda ro'yxatdan o'tgan, botni ham ishlatmoqchi bo'lganlar uchun)
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

@app.post("/auth/sayt_kod_yarat")
def sayt_kod_yarat(token: str):
    raise HTTPException(status_code=410, detail="Eski akkaunt koвЂchirish kodi yopilgan. Profil в†’ Kirish va xavfsizlik boвЂlimida Telegram yoki Google hisobini ulang")
    """Saytda kirgan foydalanuvchi uchun BOTGA ulash kodi yaratadi.
    Bot bu kodni ko'rib, shu web_user_id'dagi ma'lumotni haqiqiy
    Telegram user_id'ga ko'chiradi."""
    user_id = _jwt_tekshir(token)

    kod = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    conn = _db()
    cur = conn.cursor()
    pass  # V19: DDL moved to startup migration.
    cur.execute("INSERT INTO sayt_ulash_kod(kod, web_user_id) VALUES(%s,%s)", (kod, user_id))
    conn.commit()
    cur.close()
    conn.close()

    return {"kod": kod}


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# O'QITUVCHI вЂ” baholash
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

TOGARAK_MAX_TALABA = 25
SAMTM_PAYMENTS_ENABLED = False
ODDIY_OQITUVCHI_BEPUL_TOGARAK_LIMIT = 1_000_000
IKKINCHI_TOGARAK_NARXI_UZS = 0


def _togarak_sigimi(max_talaba):
    """Eski NULL yoki noto'g'ri qiymatlarni ham qat'iy 25 o'ringa keltiradi."""
    try:
        qiymat = int(max_talaba)
    except (TypeError, ValueError):
        return TOGARAK_MAX_TALABA
    if qiymat < 1:
        return TOGARAK_MAX_TALABA
    return min(qiymat, TOGARAK_MAX_TALABA)


def _togarak_yaratish_kvotasi(
    cur, user_id, foydalanuvchini_qulflash=False, shaxsiy_guruh=True
):
    """Oddiy o'qituvchining bepul guruh kvotasini bitta joyda tekshiradi.

    ``FOR UPDATE`` bilan chaqirilganda bir foydalanuvchidan kelgan parallel
    yaratish so'rovlari ketma-ket bajariladi; shu sabab bir vaqtning o'zida
    ikkita "birinchi bepul" to'garak ochilib ketmaydi.
    """
    qulf = " FOR UPDATE" if foydalanuvchini_qulflash else ""
    cur.execute(f"SELECT role FROM users WHERE user_id=%s{qulf}", (user_id,))
    foydalanuvchi = cur.fetchone()
    if not foydalanuvchi:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
    admin_mi = cur.fetchone() is not None
    if not admin_mi and foydalanuvchi["role"] != "oqituvchi":
        raise HTTPException(status_code=403, detail="To'garakni faqat o'qituvchi yoki administrator yarata oladi")

    cur.execute("ALTER TABLE togaraklar ADD COLUMN IF NOT EXISTS guruh_turi TEXT DEFAULT 'togarak'")
    cur.execute("ALTER TABLE togaraklar ADD COLUMN IF NOT EXISTS markaz_id INTEGER")
    cur.execute("ALTER TABLE togaraklar ADD COLUMN IF NOT EXISTS universitet_guruh_id INTEGER")
    cur.execute(
        """SELECT COUNT(*) AS soni FROM togaraklar
           WHERE teacher_id=%s AND aktiv=TRUE
             AND COALESCE(guruh_turi,'togarak') IN ('togarak','repetitor')
             AND markaz_id IS NULL AND universitet_guruh_id IS NULL""",
        (user_id,),
    )
    faol_soni = int(cur.fetchone()["soni"] or 0)
    bepul_qolgan = None if admin_mi else max(
        0, ODDIY_OQITUVCHI_BEPUL_TOGARAK_LIMIT - faol_soni
    )
    return {
        "admin": admin_mi,
        "faol_soni": faol_soni,
        "bepul_limit": None if admin_mi else ODDIY_OQITUVCHI_BEPUL_TOGARAK_LIMIT,
        "bepul_qolgan": bepul_qolgan,
        "bepul_yarata_oladi": bool(admin_mi or not shaxsiy_guruh or bepul_qolgan > 0),
        "shaxsiy_guruh": shaxsiy_guruh,
        "keyingi_narx_uzs": None if admin_mi else IKKINCHI_TOGARAK_NARXI_UZS,
        "tolov_hali_ochilmagan": not admin_mi,
        "guruh_max_talaba": TOGARAK_MAX_TALABA,
    }

@app.get("/api/oqituvchi/togaraklar")
def oqituvchi_togaraklari(token: str):
    """O'qituvchining o'ziga tegishli barcha to'garaklarini qaytaradi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    _togarak_azolar_tasdiq_ustuni(cur)
    cur.execute("""
        SELECT id, nomi, fan,
               LEAST(COALESCE(max_talaba, %s), %s) AS max_talaba,
               COALESCE(turi, 'oddiy') AS turi,
               COALESCE(guruh_turi, 'togarak') AS guruh_turi,
               (SELECT COUNT(*) FROM togarak_azolar WHERE togarak_id=togaraklar.id AND aktiv=TRUE AND tasdiqlangan=TRUE) AS azo_soni,
               (SELECT COUNT(*) FROM togarak_azolar WHERE togarak_id=togaraklar.id AND aktiv=TRUE AND tasdiqlangan=FALSE) AS kutilayotgan_soni
        FROM togaraklar
        WHERE teacher_id=%s AND aktiv=TRUE
        ORDER BY nomi
    """, (TOGARAK_MAX_TALABA, TOGARAK_MAX_TALABA, user_id))
    natija = cur.fetchall()
    kvota = _togarak_yaratish_kvotasi(cur, user_id)
    cur.close()
    conn.close()
    return {"togaraklar": natija, "kvota": kvota}


@app.get("/api/oqituvchi/togarak/{togarak_id}/azolar")
def togarak_azolari(togarak_id: int, token: str):
    """Berilgan to'garakdagi (TASDIQLANGAN) o'quvchilarni, ularning
    OXIRGI bahosi bilan qaytaradi. Faqat shu to'garakning o'z
    o'qituvchisi ko'ra oladi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()

    cur.execute("SELECT teacher_id FROM togaraklar WHERE id=%s", (togarak_id,))
    r = cur.fetchone()
    if not r or r["teacher_id"] != user_id:
        cur.close()
        conn.close()
        raise HTTPException(status_code=403, detail="Bu to'garak sizga tegishli emas")

    _togarak_azolar_tasdiq_ustuni(cur)
    cur.execute("""
        SELECT u.user_id, u.full_name,
               (SELECT baho FROM togarak_baholar tb
                WHERE tb.togarak_id=%s AND tb.user_id=u.user_id
                ORDER BY tb.created_at DESC LIMIT 1) AS oxirgi_baho
        FROM togarak_azolar ta
        JOIN users u ON u.user_id = ta.user_id
        WHERE ta.togarak_id=%s AND ta.aktiv=TRUE AND ta.tasdiqlangan=TRUE
        ORDER BY u.full_name
    """, (togarak_id, togarak_id))
    azolar = cur.fetchall()
    cur.close()
    conn.close()
    return {"azolar": azolar}


@app.get("/api/oqituvchi/togarak/{togarak_id}/kutilayotgan_azolar")
def togarak_kutilayotgan_azolar(togarak_id: int, token: str):
    """O'qituvchi/markaz rahbariyati uchun вЂ” parol orqali qo'shilish
    SO'ROVI yuborgan, hali TASDIQLANMAGAN foydalanuvchilar ro'yxati."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_egasi_mi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin ko'ra oladi")
    _togarak_azolar_tasdiq_ustuni(cur)
    cur.execute("""
        SELECT ta.id AS azolik_id, u.user_id, u.full_name
        FROM togarak_azolar ta JOIN users u ON u.user_id = ta.user_id
        WHERE ta.togarak_id=%s AND ta.aktiv=TRUE AND ta.tasdiqlangan=FALSE
        ORDER BY ta.id
    """, (togarak_id,))
    natija = cur.fetchall()
    cur.close(); conn.close()
    return {"azolar": natija}


@app.put("/api/oqituvchi/azo_tasdiqla")
def togarak_azo_tasdiqla(token: str, azolik_id: int):
    """Kutilayotgan qo'shilish so'rovini TASDIQLAYDI вЂ” shu zahoti
    o'quvchi to'garak kontentiga kira oladigan bo'ladi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _togarak_azolar_tasdiq_ustuni(cur)
    cur.execute(
        "SELECT togarak_id,user_id,tasdiqlangan FROM togarak_azolar WHERE id=%s AND aktiv=TRUE FOR UPDATE",
        (azolik_id,),
    )
    a = cur.fetchone()
    if not a:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if not _togarak_egasi_mi(cur, user_id, a["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin tasdiqlay oladi")
    cur.execute(
        "SELECT max_talaba FROM togaraklar WHERE id=%s AND aktiv=TRUE FOR UPDATE",
        (a["togarak_id"],),
    )
    togarak = cur.fetchone()
    if not togarak:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="To'garak topilmadi")
    sigim = _togarak_sigimi(togarak["max_talaba"])
    if not a["tasdiqlangan"]:
        cur.execute(
            """SELECT COUNT(*) AS soni FROM togarak_azolar
               WHERE togarak_id=%s AND aktiv=TRUE AND tasdiqlangan=TRUE AND id<>%s""",
            (a["togarak_id"], azolik_id),
        )
        tasdiqlangan_soni = int(cur.fetchone()["soni"] or 0)
        if tasdiqlangan_soni >= sigim:
            cur.close(); conn.close()
            raise HTTPException(
                status_code=409,
                detail=f"Guruhdagi {sigim} ta o'rin to'lgan; yangi o'quvchini tasdiqlab bo'lmaydi",
            )
    cur.execute("UPDATE togarak_azolar SET tasdiqlangan=TRUE WHERE id=%s", (azolik_id,))
    if _analitika_jadvallar_bormi(cur):
        _analitika_togarak_oquvchi_azolikni_taminla(
            cur, a["togarak_id"], a["user_id"]
        )
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "tasdiqlandi", "max_talaba": sigim}


@app.delete("/api/oqituvchi/azo_rad_etish")
def togarak_azo_rad_etish(token: str, azolik_id: int):
    """Kutilayotgan qo'shilish so'rovini RAD ETADI (yozuvni butunlay
    o'chiradi вЂ” xohlasa qayta parol kiritib so'rov yubora oladi)."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _togarak_azolar_tasdiq_ustuni(cur)
    cur.execute(
        "SELECT togarak_id,user_id,tasdiqlangan FROM togarak_azolar WHERE id=%s",
        (azolik_id,),
    )
    a = cur.fetchone()
    if not a:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="So'rov topilmadi")
    if not _togarak_egasi_mi(cur, user_id, a["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin rad eta oladi")
    cur.execute("DELETE FROM togarak_azolar WHERE id=%s", (azolik_id,))
    _analitika_legacy_guruh_azolikni_yop(
        cur, "togarak", a["togarak_id"], a["user_id"]
    )
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "rad_etildi"}


class BahoSorov(BaseModel):
    token: str
    togarak_id: int
    user_id: int
    baho: int
    topic_code: Optional[str] = None
    izoh: Optional[str] = None


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
        "SELECT 1 FROM togarak_azolar WHERE togarak_id=%s AND user_id=%s AND aktiv=TRUE AND tasdiqlangan=TRUE",
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

    topic_code = (sorov.topic_code or "").strip() or None
    if topic_code:
        cur.execute(
            """SELECT 1 FROM togarak_mavzulari
               WHERE togarak_id=%s AND topic_code=%s LIMIT 1""",
            (sorov.togarak_id, topic_code),
        )
        if not cur.fetchone():
            cur.close()
            conn.close()
            raise HTTPException(
                status_code=400,
                detail="Tanlangan mavzu bu to'garak dasturiga kirmaydi",
            )

    cur.execute(
        """INSERT INTO togarak_baholar(togarak_id, user_id, baho, izoh, teacher_id)
           VALUES(%s,%s,%s,%s,%s)""",
        (sorov.togarak_id, sorov.user_id, sorov.baho, sorov.izoh, teacher_id),
    )
    if _analitika_jadvallar_bormi(cur):
        context_id, group_id = _analitika_togarak_oquvchi_azolikni_taminla(
            cur, sorov.togarak_id, sorov.user_id
        )
        cur.execute(
            """SELECT c.context_type,g.subject
               FROM learning_contexts c
               LEFT JOIN course_groups g ON g.id=%s
               WHERE c.id=%s""",
            (group_id, context_id),
        )
        manba = cur.fetchone()
        _analitika_event_qosh(
            cur,
            user_id=sorov.user_id,
            actor_user_id=teacher_id,
            event_type="teacher_grade",
            source_type=ANALITIKA_KONTEKST_MANBASI.get(
                manba["context_type"] if manba else "club_offline", "club_offline"
            ),
            evidence_source="teacher",
            context_id=context_id,
            group_id=group_id,
            topic_code=topic_code,
            subject=manba["subject"] if manba else None,
            score_percent=sorov.baho,
            status="passed" if sorov.baho >= 60 else "failed",
            affects_mastery=bool(topic_code),
            payload={
                "togarak_id": sorov.togarak_id,
                "topic_code": topic_code,
                "izoh": sorov.izoh,
                "scope": "topic" if topic_code else "club_general",
            },
        )
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "saqlandi"}


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# OTA-ONA в†” FARZAND вЂ” botdagi ota_ona.py bilan AYNAN BIR XIL jadval
# (farzand_kod, parent_child) вЂ” shu sabab botda yaratilgan kodni
# saytda kiritish ham, aksincha ham ishlaydi.
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

FARZAND_KOD_MUDDATI = 15  # daqiqa


def _ota_ona_jadvallari(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS farzand_kod(
        kod TEXT PRIMARY KEY, child_id BIGINT NOT NULL, muddat TIMESTAMP NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS parent_child(
        id SERIAL PRIMARY KEY, parent_id BIGINT NOT NULL, child_id BIGINT NOT NULL
    )""")


@app.post("/api/farzand/kod_yarat")
def farzand_kod_yarat(token: str):
    """O'quvchi (farzand) ota-onasini ulash uchun 6 xonali kod oladi вЂ”
    botdagi bilan bir xil jadvalga yoziladi, 15 daqiqa amal qiladi."""
    child_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _ota_ona_jadvallari(cur)
    cur.execute("DELETE FROM farzand_kod WHERE child_id=%s OR muddat < NOW()", (child_id,))
    kod = None
    for _ in range(10):
        taklif = "".join(secrets.choice(string.digits) for _ in range(6))
        cur.execute("SELECT 1 FROM farzand_kod WHERE kod=%s", (taklif,))
        if not cur.fetchone():
            kod = taklif
            break
    if not kod:
        cur.close(); conn.close()
        raise HTTPException(status_code=500, detail="Kod yaratib bo'lmadi, qayta urinib ko'ring")
    cur.execute(
        "INSERT INTO farzand_kod(kod, child_id, muddat) VALUES(%s,%s,%s)",
        (kod, child_id, datetime.now() + timedelta(minutes=FARZAND_KOD_MUDDATI)),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"kod": kod, "amal_qilish_daqiqasi": FARZAND_KOD_MUDDATI}


@app.post("/api/ota/farzand_boglash")
def ota_farzand_boglash(token: str, kod: str):
    """Ota-ona farzanddan olgan 6 xonali kodni kiritib, hisobni bog'laydi."""
    parent_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _ota_ona_jadvallari(cur)
    cur.execute("DELETE FROM farzand_kod WHERE muddat < NOW()")
    cur.execute("SELECT child_id FROM farzand_kod WHERE kod=%s", (kod.strip(),))
    r = cur.fetchone()
    if not r:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod noto'g'ri yoki muddati o'tgan")
    child_id = r["child_id"]
    if child_id == parent_id:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="O'zingizni ulay olmaysiz")

    cur.execute(
        "INSERT INTO parent_child(parent_id, child_id) VALUES(%s,%s) ON CONFLICT DO NOTHING RETURNING id",
        (parent_id, child_id),
    )
    yangi_boglanish = cur.fetchone() is not None
    cur.execute("DELETE FROM farzand_kod WHERE kod=%s", (kod.strip(),))
    cur.execute("SELECT full_name FROM users WHERE user_id=%s", (child_id,))
    ism_row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return {
        "holat": "ulandi" if yangi_boglanish else "allaqachon_ulangan",
        "farzand_ismi": ism_row["full_name"] if ism_row else "",
    }


@app.delete("/api/ota/farzand_uzish")
def ota_farzand_uzish(token: str, farzand_id: int):
    """Ota-ona farzand bilan bog'lanishni uzadi."""
    parent_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    cur.execute("DELETE FROM parent_child WHERE parent_id=%s AND child_id=%s", (parent_id, farzand_id))
    ochirildi = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    if not ochirildi:
        raise HTTPException(status_code=404, detail="Bunday bog'lanish topilmadi")
    return {"holat": "uzildi"}


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# PROFIL вЂ” tahrirlash va rol almashtirish
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

class ProfilYangilash(BaseModel):
    token: str
    full_name: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    tugilgan_sana: Optional[str] = None
    maktab_raqami: Optional[str] = None
    maktab_turi: Optional[str] = None   # oddiy | xususiy | ixtisoslashgan | prezident
    sinf: Optional[str] = None          # 1..11
    sinf_harfi: Optional[str] = None    # A, B, V ...
    jins: Optional[str] = None          # ogil | qiz вЂ” dizayn uchun (o'quvchi va o'qituvchi)
    oqituvchi_fani: Optional[str] = None  # o'qituvchining o'zi o'qitadigan fan вЂ” dizayn uchun
    asosiy_til: Optional[str] = None    # uz | en | ru вЂ” tegsiz matn shu tilda o'qiladi
    ovoz_jinsi: Optional[str] = None    # ogil | qiz вЂ” ovoz erkak/ayol tanlovi
    maktab_id: Optional[int] = None     # eski mijoz mosligi: faqat joriy tasdiqlangan a'zolik IDsi


MAKTAB_TURLARI = {
    "oddiy": "рџЏ« Oddiy davlat maktabi",
    "xususiy": "рџЏў Xususiy",
    "ixtisoslashgan": "в­ђ Ixtisoslashgan (IDUM)",
    "prezident": "рџЏ† Prezident maktabi",
}





@app.post("/api/profil_rasm_yukla")
async def profil_rasm_yukla(token: str, fayl: UploadFile = File(...)):
    """Foydalanuvchi o'z profil rasmini yuklaydi (o'quvchi, ota-ona,
    o'qituvchi вЂ” barchasi uchun bir xil). Bazaning o'zida (BYTEA)
    saqlanadi вЂ” Railway diskka yozilgan faylni qayta ishga tushganda
    o'chirib yuborishi sababli, diskka yozish ishonchsiz."""
    user_id = _jwt_tekshir(token)
    tarkib = await fayl.read()
    if len(tarkib) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Rasm 5 MB dan katta bo'lmasligi kerak")
    nomi_lower = (fayl.filename or "").lower()
    if not nomi_lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        raise HTTPException(status_code=400, detail="Faqat rasm fayli (png/jpg/webp) qabul qilinadi")
    conn = _db()
    cur = conn.cursor()
    _users_profil_rasm_ustunlari(cur)
    cur.execute(
        "UPDATE users SET profil_rasm=%s, profil_rasm_turi=%s WHERE user_id=%s",
        (psycopg2.Binary(tarkib), fayl.content_type, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "yuklandi"}


@app.get("/api/profil_rasm/{user_id}")
def profil_rasm_korish(user_id: int):
    """Berilgan foydalanuvchining profil rasmini striming qiladi.
    Ochiq (token shart emas) вЂ” chunki bu rasm boshqalar (o'qituvchi,
    sinf rahbari, ota-ona) tomonidan ham ko'rinishi kerak, xuddi
    ismi kabi oddiy profil ma'lumoti."""
    conn = _db()
    cur = conn.cursor()
    _users_profil_rasm_ustunlari(cur)
    cur.execute("SELECT profil_rasm, profil_rasm_turi FROM users WHERE user_id=%s", (user_id,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    if not r or not r["profil_rasm"]:
        raise HTTPException(status_code=404, detail="Rasm topilmadi")
    return Response(content=bytes(r["profil_rasm"]), media_type=r["profil_rasm_turi"] or "image/jpeg")


@app.put("/api/profil")
def profil_yangila(sorov: ProfilYangilash):
    """Foydalanuvchi o'z profilini yangilaydi."""
    user_id = _jwt_tekshir(sorov.token)
    if sorov.full_name is not None and not sorov.full_name.strip():
        raise HTTPException(status_code=400, detail="Ism bo'sh bo'lishi mumkin emas")
    if sorov.maktab_turi is not None and sorov.maktab_turi not in MAKTAB_TURLARI:
        raise HTTPException(status_code=400, detail="Noto'g'ri maktab turi")
    if sorov.sinf is not None and sorov.sinf not in [str(i) for i in range(1, 12)]:
        raise HTTPException(status_code=400, detail="Sinf 1 dan 11 gacha bo'lishi kerak")
    if sorov.jins is not None and sorov.jins not in ("ogil", "qiz"):
        raise HTTPException(status_code=400, detail="Noto'g'ri jins qiymati")
    if sorov.asosiy_til is not None and sorov.asosiy_til not in ("uz", "en", "ru"):
        raise HTTPException(status_code=400, detail="Noto'g'ri asosiy til")
    if sorov.ovoz_jinsi is not None and sorov.ovoz_jinsi not in ("ogil", "qiz"):
        raise HTTPException(status_code=400, detail="Noto'g'ri ovoz turi")

    conn = _db()
    cur = conn.cursor()
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.

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
    if sorov.maktab_turi is not None:
        maydonlar.append("school_type=%s")
        qiymatlar.append(MAKTAB_TURLARI[sorov.maktab_turi])
    if sorov.sinf is not None:
        maydonlar.append("class=%s")
        qiymatlar.append(sorov.sinf)
    if sorov.sinf_harfi is not None:
        maydonlar.append("class_letter=%s")
        qiymatlar.append(sorov.sinf_harfi.strip().upper())
    if sorov.jins is not None:
        maydonlar.append("jins=%s")
        qiymatlar.append(sorov.jins)
    if sorov.oqituvchi_fani is not None:
        maydonlar.append("oqituvchi_fani=%s")
        qiymatlar.append(sorov.oqituvchi_fani.strip())
    if sorov.asosiy_til is not None:
        maydonlar.append("asosiy_til=%s")
        qiymatlar.append(sorov.asosiy_til)
    if sorov.ovoz_jinsi is not None:
        maydonlar.append("ovoz_jinsi=%s")
        qiymatlar.append(sorov.ovoz_jinsi)
    if sorov.maktab_id is not None:
        # users.maktab_id + lavozim maktab vakolatlarini belgilaydi. Profil
        # formasidan bu IDni almashtirish rahbarning vakolatini boshqa
        # muassasaga ko'chirib yuborishi mumkin. A'zolik faqat muassasaning
        # tasdiqlangan qo'shilish/biriktirish oqimi orqali o'zgartiriladi.
        cur.execute("SELECT maktab_id FROM users WHERE user_id=%s FOR UPDATE", (user_id,))
        joriy_profil = cur.fetchone()
        if not joriy_profil:
            cur.close(); conn.close()
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        if joriy_profil.get("maktab_id") != sorov.maktab_id:
            cur.close(); conn.close()
            raise HTTPException(
                status_code=403,
                detail="Maktabga biriktirish profil orqali o'zgartirilmaydi. Muassasaga qo'shilish yoki rahbar tasdig'idan foydalaning.",
            )
        # Bir xil ID yuborgan eski profil formasiga ruxsat bor, lekin
        # membership ustunini qayta yozmaymiz.

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
ROL_BEPUL_LIMIT = 2          # necha marta ERKIN (kod so'ramasdan) rol almashtirish mumkin
ROL_KOD_AMAL_MUDDATI = 10    # daqiqa
ROL_OYLIK_LIMIT_KUN = 30     # kod bilan almashtirilgach, keyingisi uchun necha kun kutish kerak


def _rol_ustunlarini_tayyorla(cur):
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS rol_ozgarish_soni INTEGER DEFAULT 0")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS oxirgi_rol_ozgarish TIMESTAMP")
    cur.execute("""CREATE TABLE IF NOT EXISTS rol_tasdiq_kod(
        user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
        kod TEXT NOT NULL, yangi_rol TEXT NOT NULL, yaratilgan_at TIMESTAMP DEFAULT NOW()
    )""")


def _email_yubor(qabul_qiluvchi: str, mavzu: str, matn: str) -> bool:
    """SMTP orqali email yuboradi. SMTP_HOST/SMTP_USER/SMTP_PASSWORD Railway'da
    o'rnatilgan bo'lishi kerak (masalan Gmail App Password) вЂ” aks holda False
    qaytaradi va konsolga log yozadi."""
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    parol = os.getenv("SMTP_PASSWORD")
    if not user or not parol:
        print(f"[EMAIL YUBORILMADI вЂ” SMTP sozlanmagan] {qabul_qiluvchi}: {matn}")
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(matn, "plain", "utf-8")
        msg["Subject"] = mavzu
        msg["From"] = user
        msg["To"] = qabul_qiluvchi
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, parol)
            s.sendmail(user, [qabul_qiluvchi], msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL XATO] {e}")
        return False


@app.put("/api/rol_ozgartir")
def rol_ozgartir(sorov: RolOzgartirish):
    """Foydalanuvchi rolini o'zgartiradi.
    - Admin uchun вЂ” CHEKLOVSIZ (sinab ko'rish uchun).
    - Oddiy foydalanuvchi uchun вЂ” hayotda 2 marta ERKIN (faqat tasdiq bilan),
      3-martadan boshlab Gmail'ga yuborilgan kod bilan, va kod bilan
      almashtirilgach keyingisi uchun 30 kun kutish kerak."""
    user_id = _jwt_tekshir(sorov.token)
    if sorov.yangi_rol not in RUXSAT_ETILGAN_ROLLAR2:
        raise HTTPException(status_code=400, detail=f"Noto'g'ri rol: {sorov.yangi_rol}")

    conn = _db()
    cur = conn.cursor()
    _rol_ustunlarini_tayyorla(cur)

    cur.execute("SELECT role, rol_ozgarish_soni, oxirgi_rol_ozgarish FROM users WHERE user_id=%s", (user_id,))
    r = cur.fetchone()
    if not r:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
    admin_mi = cur.fetchone() is not None

    hozirgi_rol = r["role"]
    if hozirgi_rol == sorov.yangi_rol:
        cur.close(); conn.close()
        return {"holat": "ozgarish_yoq"}

    soni = r["rol_ozgarish_soni"] or 0

    # ADMIN вЂ” cheklovsiz, sinab ko'rish uchun
    if admin_mi:
        if not sorov.tasdiqlayman:
            cur.close(); conn.close()
            return {"holat": "tasdiq_kerak", "hozirgi_rol": hozirgi_rol, "yangi_rol": sorov.yangi_rol, "admin_test": True}
        cur.execute("UPDATE users SET role=%s WHERE user_id=%s", (sorov.yangi_rol, user_id))
        conn.commit(); cur.close(); conn.close()
        return {"holat": "saqlandi", "yangi_rol": sorov.yangi_rol}

    # ODDIY FOYDALANUVCHI вЂ” hali bepul limitdan foydalanmagan
    if soni < ROL_BEPUL_LIMIT:
        if not sorov.tasdiqlayman:
            cur.close(); conn.close()
            return {
                "holat": "tasdiq_kerak", "hozirgi_rol": hozirgi_rol, "yangi_rol": sorov.yangi_rol,
                "qolgan_bepul": ROL_BEPUL_LIMIT - soni,
            }
        cur.execute(
            "UPDATE users SET role=%s, rol_ozgarish_soni=rol_ozgarish_soni+1, oxirgi_rol_ozgarish=NOW() WHERE user_id=%s",
            (sorov.yangi_rol, user_id),
        )
        conn.commit(); cur.close(); conn.close()
        return {"holat": "saqlandi", "yangi_rol": sorov.yangi_rol, "qolgan_bepul": ROL_BEPUL_LIMIT - soni - 1}

    # BEPUL LIMIT TUGAGAN вЂ” 30 kunlik muddat tekshiriladi
    if r["oxirgi_rol_ozgarish"]:
        keyingi = r["oxirgi_rol_ozgarish"] + timedelta(days=ROL_OYLIK_LIMIT_KUN)
        if datetime.now() < keyingi:
            cur.close(); conn.close()
            raise HTTPException(
                status_code=429,
                detail=f"Rol almashtirish limiti tugagan. Keyingi imkoniyat: {keyingi.strftime('%d.%m.%Y')}",
            )

    cur.close(); conn.close()
    return {"holat": "kod_kerak", "hozirgi_rol": hozirgi_rol, "yangi_rol": sorov.yangi_rol}


class RolKodSorash(BaseModel):
    token: str
    yangi_rol: str


@app.post("/api/rol_kod_yubor")
def rol_kod_yubor(sorov: RolKodSorash):
    """Bepul limit tugagan foydalanuvchi uchun вЂ” Gmail'ga tasdiqlash kodi yuboradi."""
    user_id = _jwt_tekshir(sorov.token)
    if sorov.yangi_rol not in RUXSAT_ETILGAN_ROLLAR2:
        raise HTTPException(status_code=400, detail="Noto'g'ri rol")

    conn = _db()
    cur = conn.cursor()
    _rol_ustunlarini_tayyorla(cur)
    cur.execute("SELECT google_email FROM google_hisob WHERE user_id=%s LIMIT 1", (user_id,))
    r = cur.fetchone()
    if not r or not r["google_email"]:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Gmail hisobingiz ulanmagan вЂ” avval botdagi kabinet orqali ulang")

    email = r["google_email"]
    kod = "".join(secrets.choice(string.digits) for _ in range(6))
    cur.execute("""
        INSERT INTO rol_tasdiq_kod(user_id, kod, yangi_rol, yaratilgan_at)
        VALUES(%s,%s,%s,NOW())
        ON CONFLICT (user_id) DO UPDATE SET kod=EXCLUDED.kod, yangi_rol=EXCLUDED.yangi_rol, yaratilgan_at=NOW()
    """, (user_id, kod, sorov.yangi_rol))
    conn.commit()
    cur.close(); conn.close()

    yuborildi = _email_yubor(
        email, "SamTM Ta'lim вЂ” rol o'zgartirish kodi",
        f"Rolni \"{sorov.yangi_rol}\"ga o'zgartirish uchun tasdiqlash kodi: {kod}\n"
        f"Kod {ROL_KOD_AMAL_MUDDATI} daqiqa amal qiladi. Agar bu so'rovni siz yubormagan bo'lsangiz, e'tiborsiz qoldiring.",
    )
    yashirilgan = re.sub(r"(?<=.{2}).(?=[^@]*@)", "*", email)
    return {"holat": "yuborildi" if yuborildi else "smtp_sozlanmagan", "email": yashirilgan}


class RolKodTasdiqlash(BaseModel):
    token: str
    kod: str


@app.post("/api/rol_kod_tasdiqla")
def rol_kod_tasdiqla(sorov: RolKodTasdiqlash):
    """Yuborilgan kodni tekshiradi va to'g'ri bo'lsa rolni o'zgartiradi."""
    user_id = _jwt_tekshir(sorov.token)
    conn = _db()
    cur = conn.cursor()
    _rol_ustunlarini_tayyorla(cur)
    cur.execute("SELECT kod, yangi_rol, yaratilgan_at FROM rol_tasdiq_kod WHERE user_id=%s", (user_id,))
    r = cur.fetchone()
    if not r:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Avval kod so'rang")
    if datetime.now() - r["yaratilgan_at"] > timedelta(minutes=ROL_KOD_AMAL_MUDDATI):
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod muddati tugagan вЂ” qaytadan so'rang")
    if sorov.kod.strip() != r["kod"]:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kod noto'g'ri")

    cur.execute(
        "UPDATE users SET role=%s, rol_ozgarish_soni=rol_ozgarish_soni+1, oxirgi_rol_ozgarish=NOW() WHERE user_id=%s",
        (r["yangi_rol"], user_id),
    )
    cur.execute("DELETE FROM rol_tasdiq_kod WHERE user_id=%s", (user_id,))
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "saqlandi", "yangi_rol": r["yangi_rol"]}


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# O'QITUVCHI вЂ” yangi to'garak yaratish
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

class TogarakYaratish(BaseModel):
    token: str
    nomi: str
    fan: str
    sinf: Optional[str] = None   # "1".."11" (oddiy) yoki "3-4" kabi (to'garak guruhi)
    turi: str = "oddiy"          # dars usuli: "oddiy" | "avto"
    guruh_turi: str = "togarak"  # maqsad: "togarak" | "repetitor"
    parol: Optional[str] = None
    max_talaba: Optional[int] = None
    oylik_summa: Optional[int] = None
    universitet_guruh_id: Optional[int] = None  # professor shu fanini ANIQ universitet guruhi uchun o'qitsa
    tanlangan_topic_codes: Optional[list[str]] = None  # o'qituvchi ANIQ tanlagan mavzular (berilmasa вЂ” mos kelgan BARCHASI avtomatik)
    reja_id: Optional[int] = None  # tanlangan "topik mavzu rejasi" вЂ” berilsa, shu rejaning tartibli mavzulari ko'chiriladi (tanlangan_topic_codes'dan USTUN)


def _togarak_parol_yarat(cur, tavsiya=None, ozini_ozi_hisobga_olmaslik_id=None):
    """Barcha FAOL to'garaklar orasida TAKRORLANMAYDIGAN parol
    beradi. O'qituvchi o'zi parol kiritgan bo'lsa (tavsiya) вЂ” u
    BOSHQA biror faol to'garakda band emasligi tekshiriladi (aks
    holda ikkita to'garak bir xil parolga ega bo'lib, o'quvchi
    tasodifan noto'g'ri to'garakka qo'shilib qolishi mumkin edi).
    Berilmasa вЂ” 6 xonali, tasodifiy VA takrorlanmaydigan parol
    avtomatik yaratiladi (tasodifiy taxmin bilan boshqa to'garakka
    kirib qolish ehtimoli ham shu bilan kamayadi)."""
    if tavsiya:
        tavsiya = tavsiya.strip()
        shart = "parol=%s AND aktiv=TRUE"
        params = [tavsiya]
        if ozini_ozi_hisobga_olmaslik_id is not None:
            shart += " AND id != %s"
            params.append(ozini_ozi_hisobga_olmaslik_id)
        cur.execute(f"SELECT 1 FROM togaraklar WHERE {shart}", params)
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Bu parol allaqachon boshqa to'garakda ishlatilmoqda вЂ” boshqa parol tanlang")
        return tavsiya
    for _ in range(20):
        taklif = "".join(secrets.choice(string.digits) for _ in range(6))
        cur.execute("SELECT 1 FROM togaraklar WHERE parol=%s AND aktiv=TRUE", (taklif,))
        if not cur.fetchone():
            return taklif
    raise HTTPException(status_code=500, detail="Parol yaratib bo'lmadi, qayta urinib ko'ring")


@app.post("/api/oqituvchi/togarak_yarat")
def togarak_yarat(sorov: TogarakYaratish):
    """O'qituvchi yangi to'garak yaratadi вЂ” bot ishlatadigan AYNAN SHU
    jadvalga (togaraklar) yoziladi, shuning uchun bot va sayt bir xil
    ma'lumotni ko'radi. Fan+sinf tanlanganda вЂ” o'sha fan/sinfga tegishli
    BARCHA mavzular avtomatik ravishda to'garakning "ta'lim yo'li"ga
    bog'lanadi (togarak_mavzulari)."""
    teacher_id = _jwt_tekshir(sorov.token)
    if not sorov.nomi.strip():
        raise HTTPException(status_code=400, detail="To'garak nomi kiritilmagan")
    if not sorov.fan.strip():
        raise HTTPException(status_code=400, detail="Fan kiritilmagan")
    turi_qiymati = (sorov.turi or "").strip().lower()
    if turi_qiymati not in ("oddiy", "avto"):
        raise HTTPException(status_code=400, detail="Dars usuli oddiy yoki avto bo'lishi kerak")
    guruh_turi_qiymati = (sorov.guruh_turi or "").strip().lower()
    if guruh_turi_qiymati not in ("togarak", "repetitor"):
        raise HTTPException(status_code=400, detail="Guruh turi togarak yoki repetitor bo'lishi kerak")
    if sorov.max_talaba is not None and not (1 <= sorov.max_talaba <= TOGARAK_MAX_TALABA):
        raise HTTPException(status_code=400, detail=f"Guruh sig'imi 1вЂ“{TOGARAK_MAX_TALABA} oralig'ida bo'lishi kerak")

    conn = _db()
    cur = conn.cursor()
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    pass  # V19: DDL moved to startup migration.
    _togaraklar_reja_id_ustuni(cur)
    pass  # V19: DDL moved to startup migration.
    _reja_jadvallari(cur)
    # Agar o'qituvchi biror o'quv markaziga tegishli bo'lsa (xodim
    # importi orqali "Fan o'qituvchisi" sifatida qo'shilgan bo'lsa) вЂ”
    # yaratayotgan guruhi AVTOMATIK shu markazga bog'lanadi, markaz
    # direktori/administratori uni darhol "Markaz" boshqaruv panelida
    # ko'radi вЂ” qo'lda bog'lash shart emas.
    pass  # V19: DDL moved to startup migration.
    cur.execute("SELECT markaz_id FROM users WHERE user_id=%s", (teacher_id,))
    ur = cur.fetchone()
    teacher_markaz_id = ur["markaz_id"] if ur else None

    # Professor bu fanni ANIQ bitta universitet guruhi uchun o'qitayotgan
    # bo'lsa вЂ” shu guruhga bog'laydi, guruh kuratori/dekani keyin BUTUN
    # guruhning shu fandagi bilim darajasini ko'ra oladi.
    universitet_guruh_id = None
    if sorov.universitet_guruh_id is not None:
        cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (teacher_id,))
        admin_mi = cur.fetchone() is not None
        if admin_mi:
            cur.execute("SELECT id FROM universitet_guruhlari WHERE id=%s", (sorov.universitet_guruh_id,))
        else:
            cur.execute(
                """SELECT g.id
                   FROM universitet_guruhlari g
                   JOIN kafedralar k ON k.id=g.kafedra_id
                   JOIN fakultetlar f ON f.id=k.fakultet_id
                   JOIN users u ON u.user_id=%s
                   WHERE g.id=%s
                     AND (g.rahbar_user_id=%s OR f.universitet_id=u.universitet_id)""",
                (teacher_id, sorov.universitet_guruh_id, teacher_id),
            )
        if not cur.fetchone():
            cur.close(); conn.close()
            raise HTTPException(status_code=403, detail="Bu universitet guruhiga kurs ochish vakolati sizga berilmagan")
        universitet_guruh_id = sorov.universitet_guruh_id

    shaxsiy_guruh = teacher_markaz_id is None and universitet_guruh_id is None
    kvota = _togarak_yaratish_kvotasi(
        cur,
        teacher_id,
        foydalanuvchini_qulflash=True,
        shaxsiy_guruh=shaxsiy_guruh,
    )
    if SAMTM_PAYMENTS_ENABLED and not kvota["bepul_yarata_oladi"]:
        cur.close(); conn.close()
        raise HTTPException(
            status_code=402,
            detail={
                "code": "SECOND_CLUB_PAYMENT_REQUIRED",
                "message": "Birinchi shaxsiy to'garak yoki repetitor guruhi bepul. Ikkinchisini ochish narxi 50 000 so'm; to'lov oynasi keyingi bosqichda ulanadi.",
                "price_uzs": IKKINCHI_TOGARAK_NARXI_UZS,
            },
        )

    sinf_qiymati = sorov.sinf.strip() if sorov.sinf else None
    max_talaba_qiymati = sorov.max_talaba or TOGARAK_MAX_TALABA
    reja_id_qiymati = None
    if sorov.reja_id is not None:
        if not _reja_ozi_mi(cur, teacher_id, sorov.reja_id):
            cur.close(); conn.close()
            raise HTTPException(status_code=403, detail="Bu reja sizga tegishli emas")
        reja_id_qiymati = sorov.reja_id
    try:
        parol_qiymati = _togarak_parol_yarat(cur, sorov.parol)
    except HTTPException:
        cur.close(); conn.close()
        raise
    cur.execute("""
        INSERT INTO togaraklar(nomi, fan, teacher_id, sinf, turi, guruh_turi, parol, max_talaba, oylik_summa, aktiv, markaz_id, universitet_guruh_id, reja_id)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE,%s,%s,%s) RETURNING id
    """, (sorov.nomi.strip(), sorov.fan.strip(), teacher_id, sinf_qiymati, turi_qiymati,
          guruh_turi_qiymati, parol_qiymati,
          max_talaba_qiymati, sorov.oylik_summa, teacher_markaz_id, universitet_guruh_id, reja_id_qiymati))
    yangi_id = cur.fetchone()["id"]

    bogliq_mavzu_soni = 0
    if reja_id_qiymati is not None:
        # Reja tanlangan вЂ” uning TARTIBLI mavzularini shu to'garakka
        # ko'chiramiz (tanlangan_topic_codes/avtomatik logikadan USTUN).
        cur.execute("SELECT topic_code FROM topik_mavzu_reja_qatorlari WHERE reja_id=%s ORDER BY tartib_raqami", (reja_id_qiymati,))
        mavzu_kodlari = [r["topic_code"] for r in cur.fetchall()]
        for kod in mavzu_kodlari:
            cur.execute(
                "INSERT INTO togarak_mavzulari(togarak_id, topic_code) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                (yangi_id, kod),
            )
        bogliq_mavzu_soni = len(mavzu_kodlari)
    elif sorov.tanlangan_topic_codes is not None:
        # O'qituvchi ANIQ mavzularni tanlagan вЂ” faqat SHU sinf/fanga
        # HAQIQATAN tegishli kodlarni qabul qilamiz (xavfsizlik: boshqa
        # sinf/fan kodini "surib qo'yish" mumkin emas).
        tanlangan = [k.strip() for k in sorov.tanlangan_topic_codes if k.strip()]
        if tanlangan and sinf_qiymati:
            cur.execute("""
                SELECT topic_code FROM dts_tree
                WHERE grade=%s AND UPPER(subject_name)=UPPER(%s) AND is_deleted=FALSE AND topic_code = ANY(%s)
            """, (sinf_qiymati, sorov.fan.strip(), tanlangan))
            mavzu_kodlari = [r["topic_code"] for r in cur.fetchall()]
            for kod in mavzu_kodlari:
                cur.execute(
                    "INSERT INTO togarak_mavzulari(togarak_id, topic_code) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                    (yangi_id, kod),
                )
            bogliq_mavzu_soni = len(mavzu_kodlari)
    elif sinf_qiymati:
        cur.execute("""
            SELECT topic_code FROM dts_tree
            WHERE grade=%s AND UPPER(subject_name)=UPPER(%s) AND is_deleted=FALSE
              AND topic_code IN (SELECT DISTINCT topic_code FROM generated_tests)
        """, (sinf_qiymati, sorov.fan.strip()))
        mavzu_kodlari = [r["topic_code"] for r in cur.fetchall()]
        for kod in mavzu_kodlari:
            cur.execute(
                "INSERT INTO togarak_mavzulari(togarak_id, topic_code) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                (yangi_id, kod),
            )
        bogliq_mavzu_soni = len(mavzu_kodlari)

    if _analitika_jadvallar_bormi(cur):
        _analitika_togarak_konteksti(cur, yangi_id)
    conn.commit()
    cur.close()
    conn.close()
    yangilangan_kvota = kvota
    if shaxsiy_guruh:
        yangilangan_kvota = {
            **kvota,
            "faol_soni": kvota["faol_soni"] + 1,
            "bepul_qolgan": None if kvota["admin"] else 0,
            "bepul_yarata_oladi": bool(kvota["admin"]),
        }
    return {
        "holat": "yaratildi",
        "togarak_id": yangi_id,
        "turi": turi_qiymati,
        "guruh_turi": guruh_turi_qiymati,
        "max_talaba": max_talaba_qiymati,
        "boglangan_mavzu_soni": bogliq_mavzu_soni,
        "kvota": yangilangan_kvota,
    }


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# TO'GARAK GURUH SOZLAMALARI вЂ” parolni ko'rish/almashtirish, va
# XAVFSIZ o'chirish (parol so'ralib, faqat shundan keyin o'chadi).
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

def _togarak_egasi_mi(cur, user_id, togarak_id):
    cur.execute("SELECT teacher_id, markaz_id FROM togaraklar WHERE id=%s", (togarak_id,))
    t = cur.fetchone()
    if not t:
        return False
    if t["teacher_id"] == user_id:
        return True
    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
    if cur.fetchone():
        return True
    return bool(t["markaz_id"] and _markaz_boshqaruvchi_mi(cur, user_id, t["markaz_id"]))


@app.get("/api/oqituvchi/togarak_parolini_kor")
def togarak_parolini_kor(token: str, togarak_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_egasi_mi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin ko'ra oladi")
    cur.execute("SELECT parol FROM togaraklar WHERE id=%s", (togarak_id,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    return {"parol": r["parol"] if r else None}


class TogarakParolAlmashtirish(BaseModel):
    token: str
    togarak_id: int
    yangi_parol: str


@app.put("/api/oqituvchi/togarak_parol_almashtir")
def togarak_parol_almashtir(sorov: TogarakParolAlmashtirish):
    user_id = _jwt_tekshir(sorov.token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_egasi_mi(cur, user_id, sorov.togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin o'zgartira oladi")
    if not sorov.yangi_parol.strip():
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Yangi parolni kiriting")
    try:
        yangi_parol = _togarak_parol_yarat(cur, sorov.yangi_parol, ozini_ozi_hisobga_olmaslik_id=sorov.togarak_id)
    except HTTPException:
        cur.close(); conn.close()
        raise
    cur.execute("UPDATE togaraklar SET parol=%s WHERE id=%s", (yangi_parol, sorov.togarak_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "saqlandi"}


@app.delete("/api/oqituvchi/togarak_ochir")
def togarak_ochir(token: str, togarak_id: int, parol: str):
    """Butun guruhni O'CHIRADI вЂ” QAYTARIB BO'LMAYDI. Xavfsizlik
    uchun guruhning JORIY parolini talab qiladi (frontend oldindan
    ogohlantiradi). O'ZI yaratgan (milliy bazadan emas) mavzu/testlar
    ham butunlay o'chadi вЂ” milliy bazadagi umumiy mavzularga
    tegilmaydi (faqat BOG'LANISH o'chadi)."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_egasi_mi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin o'chira oladi")
    cur.execute("SELECT parol FROM togaraklar WHERE id=%s", (togarak_id,))
    t = cur.fetchone()
    if not t:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Guruh topilmadi")
    if (t["parol"] or "") != parol.strip():
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Parol noto'g'ri")

    _togarak_mavzu_kontenti_jadvali(cur)
    cur.execute("SELECT topic_code FROM togarak_mavzu_kontenti WHERE togarak_id=%s", (togarak_id,))
    ozi_kodlari = [r["topic_code"] for r in cur.fetchall()]
    if ozi_kodlari:
        cur.execute("DELETE FROM generated_tests WHERE topic_code = ANY(%s)", (ozi_kodlari,))
        cur.execute("UPDATE dts_tree SET is_deleted=TRUE WHERE topic_code = ANY(%s)", (ozi_kodlari,))
        cur.execute("DELETE FROM togarak_mavzu_kontenti WHERE togarak_id=%s", (togarak_id,))
    cur.execute("DELETE FROM togarak_mavzulari WHERE togarak_id=%s", (togarak_id,))
    _analitika_legacy_guruh_azolikni_yop(
        cur, "togarak", togarak_id, guruhni_yop=True
    )
    cur.execute("DELETE FROM togarak_azolar WHERE togarak_id=%s", (togarak_id,))
    cur.execute("DELETE FROM tolovlar WHERE togarak_id=%s", (togarak_id,))
    cur.execute("DELETE FROM togaraklar WHERE id=%s", (togarak_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "ochirildi"}


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# TO'GARAK O'ZI MAVZU/TEST YARATISH вЂ” o'qituvchi milliy bazadagi
# tayyor mavzularga qo'shimcha, O'Z guruh uchun ORIGINAL mavzu+test+
# video-dars yaratadi. MAVJUD infratuzilmani QAYTA ISHLATADI: har bir
# yangi mavzu, sinov (SIN) topic_code bilan dts_tree'ga qo'shiladi вЂ”
# shu bilan test yechish/Bilim/spaced-repetition kabi BUTUN mavjud
# mexanizm avtomatik ishlab ketadi, hech narsa qaytadan yozilmaydi.
#
# TOPIC_CODE XAVFSIZLIGI: PostgreSQL SEQUENCE orqali вЂ” bu bazaning
# o'zi kafolatlaydigan, ATOM (bo'linmas) hisoblagich. Necha million
# mavzu yaratilmasin, ikkita so'rov bir vaqtda kelsa ham, ikkita
# turli mavzu BIR XIL kodni HECH QACHON ololmaydi вЂ” bu PostgreSQL'ning
# o'zi ta'minlaydigan kafolat, poyga holati (race condition) mumkin
# emas. Kod formati oddiy: SIN0000001, SIN0000002, ... вЂ” to'garak
# raqamiga BOG'LIQ EMAS, shu sabab har doim oddiy va bir xil uzunlikda.
#
# Ikki bosqichli ish jarayoni вЂ” ADMIN'ning "Topik shablon"/"Test
# shablon" naqshiga mos, lekin SODDA (chorak/bo'lim/kichik mavzu
# YO'Q вЂ” faqat Bob va Mavzu):
#   1) Mavzu shablon: Bob|Mavzu Excel в†’ to'ldirib yuklash
#   2) Test shablon: tanlangan mavzu(lar) uchun savol Excel в†’ to'ldirib yuklash
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

def _togarak_mavzu_kontenti_jadvali(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS togarak_mavzu_kontenti(
        topic_code TEXT PRIMARY KEY,
        togarak_id INTEGER REFERENCES togaraklar(id),
        reja TEXT,
        muhim_malumot TEXT,
        video_havola TEXT,
        yaratilgan_at TIMESTAMP DEFAULT NOW()
    )""")
    cur.execute("CREATE SEQUENCE IF NOT EXISTS togarak_mavzu_kod_seq")


def _keyingi_togarak_topic_code(cur):
    """PostgreSQL SEQUENCE'dan KEYINGI, hech qachon takrorlanmaydigan
    raqamni oladi вЂ” bazaning o'zi kafolatlaydi, poyga holati mumkin
    emas, necha million bo'lsa ham oddiy va tez."""
    cur.execute("SELECT nextval('togarak_mavzu_kod_seq') AS keyingi")
    keyingi = cur.fetchone()["keyingi"]
    return f"SIN{keyingi:07d}"


def _reja_jadvallari(cur):
    """O'qituvchi bir marta yaratib, bir nechta to'garak guruhida
    QAYTA ISHLATA oladigan 'topik mavzu rejasi' (tartibli mavzular
    ketma-ketligi) uchun jadvallar."""
    cur.execute("""CREATE TABLE IF NOT EXISTS topik_mavzu_rejalari(
        id SERIAL PRIMARY KEY,
        nomi TEXT NOT NULL,
        sinf TEXT NOT NULL,
        fan TEXT NOT NULL,
        guruh_turi TEXT NOT NULL DEFAULT 'sinf',
        yaratgan_user_id BIGINT REFERENCES users(user_id),
        yaratilgan_at TIMESTAMP DEFAULT NOW()
    )""")
    cur.execute("ALTER TABLE topik_mavzu_rejalari ADD COLUMN IF NOT EXISTS guruh_turi TEXT NOT NULL DEFAULT 'sinf'")
    cur.execute("""CREATE TABLE IF NOT EXISTS topik_mavzu_reja_qatorlari(
        id SERIAL PRIMARY KEY,
        reja_id INTEGER REFERENCES topik_mavzu_rejalari(id) ON DELETE CASCADE,
        topic_code TEXT NOT NULL,
        tartib_raqami INTEGER NOT NULL,
        UNIQUE(reja_id, tartib_raqami)
    )""")


def _togaraklar_reja_id_ustuni(cur):
    """togaraklar.reja_id ustuni yo'q bo'lsa, yaratadi. HAR SO'ROVDA
    ishga tushadi (keshlanmaydi) вЂ” chunki ko'p endpoint (masalan
    /auth/men) transaksiyani commit qilmaydi, shu sabab "faqat bir
    marta bajarish" keshi ustunni HAQIQATDA yaratilmagan holda
    "yaratildi" deb noto'g'ri belgilab qo'yishi mumkin edi."""
    cur.execute("ALTER TABLE togaraklar ADD COLUMN IF NOT EXISTS reja_id INTEGER")


def _users_profil_rasm_ustunlari(cur):
    """users.profil_rasm/profil_rasm_turi ustunlari yo'q bo'lsa,
    yaratadi. HAR SO'ROVDA ishga tushadi вЂ” sababi yuqoridagi
    _togaraklar_reja_id_ustuni bilan bir xil."""
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profil_rasm BYTEA")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profil_rasm_turi TEXT")


def _reja_ozi_mi(cur, user_id, reja_id):
    """True вЂ” agar user shu rejani yaratgan o'qituvchi yoki admin bo'lsa."""
    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
    if cur.fetchone():
        return True
    cur.execute("SELECT 1 FROM topik_mavzu_rejalari WHERE id=%s AND yaratgan_user_id=%s", (reja_id, user_id))
    return cur.fetchone() is not None


def _togarak_ozi_mi(cur, user_id, togarak_id):
    """True вЂ” agar user shu to'garakning o'qituvchisi, markaz
    rahbariyati yoki admin bo'lsa."""
    cur.execute("SELECT 1 FROM admin_akkaunt WHERE uid=%s", (user_id,))
    if cur.fetchone():
        return True
    cur.execute("SELECT teacher_id, markaz_id FROM togaraklar WHERE id=%s", (togarak_id,))
    t = cur.fetchone()
    if not t:
        return False
    if t["teacher_id"] == user_id:
        return True
    return bool(t["markaz_id"] and _markaz_boshqaruvchi_mi(cur, user_id, t["markaz_id"]))


@app.get("/api/oqituvchi/togarak_mavzu_shablon")
def togarak_mavzu_shablon(token: str, togarak_id: int):
    """1-bosqich вЂ” Bob|Mavzu Excel shablonini yaratadi. Admin'ning
    Topik shablonidan farqli: CHORAK, BO'LIM, KICHIK MAVZU yo'q вЂ”
    faqat ikkita ustun, chunki to'garak dasturi milliy dasturdan
    mustaqil, soddaroq tuzilishda."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin ko'ra oladi")
    cur.execute("SELECT nomi, fan FROM togaraklar WHERE id=%s", (togarak_id,))
    t = cur.fetchone()
    cur.close()
    conn.close()
    if not t:
        raise HTTPException(status_code=404, detail="To'garak topilmadi")

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    import io
    from fastapi.responses import StreamingResponse

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "MAVZULAR"
    for col, h in enumerate(["#", "Bob", "Mavzu"], 1):
        cell = ws.cell(1, col, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="70AD47")
        cell.alignment = Alignment(horizontal="center")
    namunalar = [(1, "1-bob. Kirish", "Tanishuv darsi"), (2, "1-bob. Kirish", "Asosiy tushunchalar"), (3, "2-bob. Amaliyot", "Birinchi mashqlar")]
    for idx, bob, mavzu in namunalar:
        ws.cell(idx + 1, 1, idx)
        ws.cell(idx + 1, 2, bob)
        ws.cell(idx + 1, 3, mavzu)
    for col, width in zip(range(1, 4), [5, 30, 35]):
        ws.column_dimensions[ws.cell(1, col).column_letter].width = width

    ws2 = wb.create_sheet("IZOH")
    ws2.cell(1, 1, "рџ“‹ TO'LDIRISH QO'LLANMASI").font = Font(bold=True, size=14)
    ws2.cell(3, 1, f"To'garak: {t['nomi']} ({t['fan']})").font = Font(bold=True)
    ws2.cell(5, 1, "Bob вЂ” mavzular guruhini nomlang, masalan '1-bob. Kirish'").font = Font(bold=True)
    ws2.cell(6, 1, "Mavzu вЂ” har bir dars/mavzu nomi, alohida qatorda")
    ws2.cell(7, 1, "Namuna qatorlarni o'chirib, o'zingiznikini yozing yoki davom ettiring")
    ws2.column_dimensions['A'].width = 70

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=togarak_mavzu_shablon_{togarak_id}.xlsx"},
    )


@app.post("/api/oqituvchi/togarak_mavzu_import")
async def togarak_mavzu_import(token: str, togarak_id: int, fayl: UploadFile = File(...)):
    """1-bosqich (yuklash) вЂ” to'ldirilgan Bob|Mavzu shablonni o'qib,
    har bir qator uchun (Mavzu bo'sh bo'lmasa) YANGI, hech qachon
    takrorlanmaydigan topic_code yaratadi va to'garak ta'lim yo'liga
    qo'shadi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin yuklay oladi")
    cur.execute("SELECT sinf, fan FROM togaraklar WHERE id=%s", (togarak_id,))
    t = cur.fetchone()
    if not t:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="To'garak topilmadi")

    import openpyxl
    import io
    content = await fayl.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    except Exception as e:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail=f"Excel o'qib bo'lmadi: {e}")
    ws = wb["MAVZULAR"] if "MAVZULAR" in wb.sheetnames else wb.active

    _togarak_mavzu_kontenti_jadvali(cur)
    pass  # V19: DDL moved to startup migration.

    qoshildi = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or len(row) < 3:
            continue
        bob, mavzu = row[1], row[2]
        if not mavzu or not str(mavzu).strip():
            continue
        topic_code = _keyingi_togarak_topic_code(cur)
        cur.execute("""
            INSERT INTO dts_tree(topic_code, grade, subject_name, quarter, bob_name, bolim_name, mavzu_name, kichik_name, is_deleted)
            VALUES(%s,%s,%s,'1',%s,'',%s,'',FALSE)
        """, (topic_code, t["sinf"] or "", t["fan"] or "", str(bob).strip() if bob else "", str(mavzu).strip()))
        cur.execute("""
            INSERT INTO togarak_mavzu_kontenti(topic_code, togarak_id) VALUES(%s,%s)
        """, (topic_code, togarak_id))
        cur.execute(
            "INSERT INTO togarak_mavzulari(togarak_id, topic_code) VALUES(%s,%s) ON CONFLICT DO NOTHING",
            (togarak_id, topic_code),
        )
        qoshildi += 1
    conn.commit()
    cur.close()
    conn.close()
    return {"qoshildi": qoshildi}


@app.get("/api/oqituvchi/togarak_mavzulari_ozi")
def togarak_mavzulari_ozi_royxati(token: str, togarak_id: int):
    """O'qituvchi tomonidan yaratilgan (milliy bazadan emas) barcha
    ORIGINAL mavzular вЂ” har biriga nechta savol borligi bilan."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin ko'ra oladi")
    _togarak_mavzu_kontenti_jadvali(cur)
    cur.execute("""
        SELECT k.topic_code, d.bob_name, d.mavzu_name AS nomi, k.reja, k.muhim_malumot, k.video_havola,
               (SELECT COUNT(*) FROM generated_tests WHERE topic_code=k.topic_code) AS savol_soni
        FROM togarak_mavzu_kontenti k
        LEFT JOIN dts_tree d ON d.topic_code = k.topic_code
        WHERE k.togarak_id=%s ORDER BY k.yaratilgan_at
    """, (togarak_id,))
    natija = cur.fetchall()
    cur.close()
    conn.close()
    return {"mavzular": natija}


class TogarakMavzuTahrirlash(BaseModel):
    token: str
    topic_code: str
    reja: Optional[str] = None
    muhim_malumot: Optional[str] = None
    video_havola: Optional[str] = None


@app.put("/api/oqituvchi/togarak_mavzu_tahrirlash")
def togarak_mavzu_tahrirlash(sorov: TogarakMavzuTahrirlash):
    """Excel orqali yaratilgan mavzuga KEYINROQ reja/muhim ma'lumot/
    video havola qo'shish yoki yangilash uchun."""
    user_id = _jwt_tekshir(sorov.token)
    conn = _db()
    cur = conn.cursor()
    _togarak_mavzu_kontenti_jadvali(cur)
    cur.execute("SELECT togarak_id FROM togarak_mavzu_kontenti WHERE topic_code=%s", (sorov.topic_code,))
    k = cur.fetchone()
    if not k:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Mavzu topilmadi")
    if not _togarak_ozi_mi(cur, user_id, k["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin tahrirlay oladi")
    cur.execute("""
        UPDATE togarak_mavzu_kontenti SET reja=%s, muhim_malumot=%s, video_havola=%s WHERE topic_code=%s
    """, (sorov.reja, sorov.muhim_malumot, sorov.video_havola, sorov.topic_code))
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "saqlandi"}


@app.delete("/api/oqituvchi/togarak_mavzu_ochir")
def togarak_mavzu_ochir(token: str, topic_code: str):
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _togarak_mavzu_kontenti_jadvali(cur)
    cur.execute("SELECT togarak_id FROM togarak_mavzu_kontenti WHERE topic_code=%s", (topic_code,))
    k = cur.fetchone()
    if not k:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Mavzu topilmadi")
    if not _togarak_ozi_mi(cur, user_id, k["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin o'chira oladi")
    cur.execute("DELETE FROM generated_tests WHERE topic_code=%s", (topic_code,))
    cur.execute("DELETE FROM togarak_mavzulari WHERE topic_code=%s", (topic_code,))
    cur.execute("DELETE FROM togarak_mavzu_kontenti WHERE topic_code=%s", (topic_code,))
    cur.execute("UPDATE dts_tree SET is_deleted=TRUE WHERE topic_code=%s", (topic_code,))
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "ochirildi"}


class TogarakTestShablonGuruh(BaseModel):
    topic_code: str
    soni: int


class TogarakTestShablonSorov(BaseModel):
    token: str
    togarak_id: int
    guruhlar: list[TogarakTestShablonGuruh]


@app.post("/api/oqituvchi/togarak_test_shablon")
def togarak_test_shablon(sorov: TogarakTestShablonSorov):
    """2-bosqich вЂ” tanlangan mavzu(lar) uchun, har biriga necha savol
    kerakligi bo'yicha, bo'sh savollar Excel shablonini yaratadi вЂ”
    admin'ning TESTLAR varag'i bilan BIR XIL ustunlar, shu sabab
    to'ldirilgach import qilinganda test yechish tizimi bilan to'liq
    mos ishlaydi."""
    user_id = _jwt_tekshir(sorov.token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, sorov.togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin ko'ra oladi")
    guruhlar = [g for g in sorov.guruhlar if g.soni > 0]
    if not guruhlar:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Kamida bitta mavzudan son tanlang")

    _togarak_mavzu_kontenti_jadvali(cur)
    kodlar = [g.topic_code for g in guruhlar]
    cur.execute("SELECT topic_code FROM togarak_mavzu_kontenti WHERE togarak_id=%s AND topic_code = ANY(%s)", (sorov.togarak_id, kodlar))
    ruxsat_etilgan = {r["topic_code"] for r in cur.fetchall()}
    cur.execute("SELECT topic_code, mavzu_name FROM dts_tree WHERE topic_code = ANY(%s)", (kodlar,))
    nomlar = {r["topic_code"]: r["mavzu_name"] for r in cur.fetchall()}
    cur.close()
    conn.close()

    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    import io
    from fastapi.responses import StreamingResponse

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "TESTLAR"
    ustunlar = [
        "topic_code", "difficulty", "situation", "question",
        "option_a", "option_b", "option_c", "option_d",
        "correct_answer", "explanation", "question_type", "is_latex",
        "image_url", "audio_text", "language", "life_level", "age_group", "time_limit",
    ]
    for col, h in enumerate(ustunlar, 1):
        cell = ws.cell(1, col, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="4472C4")
        cell.alignment = Alignment(horizontal="center")

    row_num = 2
    for g in guruhlar:
        if g.topic_code not in ruxsat_etilgan:
            continue  # boshqa to'garak yoki milliy mavzu kodi вЂ” o'tkazib yuboriladi
        for _ in range(g.soni):
            ws.cell(row_num, 1, g.topic_code)
            ws.cell(row_num, 2, "o'rta")
            ws.cell(row_num, 3, "oddiy")
            ws.cell(row_num, 11, "single_choice")
            ws.cell(row_num, 12, False)
            ws.cell(row_num, 15, "uz")
            ws.cell(row_num, 16, 1)
            ws.cell(row_num, 18, 60)
            row_num += 1

    for col, width in zip(range(1, len(ustunlar) + 1), [22, 10, 10, 45, 18, 18, 18, 18, 15, 35, 15, 8, 22, 20, 8, 8, 8, 10]):
        ws.column_dimensions[ws.cell(1, col).column_letter].width = width

    ws2 = wb.create_sheet("IZOH")
    ws2.cell(1, 1, "рџ“‹ TO'LDIRISH QO'LLANMASI").font = Font(bold=True, size=14)
    for r, satr in enumerate([
        "question вЂ” savol matni (majburiy)",
        "option_a/b/c/d вЂ” variantlar (variantli savol uchun)",
        "correct_answer вЂ” to'g'ri javob (majburiy)",
        "question_type вЂ” 'single_choice' yoki 'write_answer'",
        "topic_code va difficulty вЂ” o'zgartirmang",
    ], 3):
        ws2.cell(r, 1, satr)
    mavzu_nomlari = [f"{k}: {nomlar.get(k, '')}" for k in ruxsat_etilgan]
    ws2.cell(9, 1, "Ushbu shablondagi mavzular:").font = Font(bold=True)
    for r, s in enumerate(mavzu_nomlari, 10):
        ws2.cell(r, 1, s)
    ws2.column_dimensions['A'].width = 70

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return StreamingResponse(
        buf, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=togarak_test_shablon_{sorov.togarak_id}.xlsx"},
    )


@app.post("/api/oqituvchi/togarak_test_import")
async def togarak_test_import(token: str, togarak_id: int, fayl: UploadFile = File(...)):
    """2-bosqich (yuklash) вЂ” to'ldirilgan TESTLAR shablonni o'qib,
    generated_tests'ga qo'shadi. XAVFSIZLIK: har bir qatordagi
    topic_code ANIQ shu to'garakka tegishli ekani tekshiriladi вЂ”
    boshqa to'garak yoki milliy mavzu kodiga yozish MUMKIN EMAS."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin yuklay oladi")

    _togarak_mavzu_kontenti_jadvali(cur)
    cur.execute("SELECT topic_code FROM togarak_mavzu_kontenti WHERE togarak_id=%s", (togarak_id,))
    ozi_kodlari = {r["topic_code"] for r in cur.fetchall()}

    import openpyxl
    import io
    content = await fayl.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    except Exception as e:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail=f"Excel o'qib bo'lmadi: {e}")
    ws = wb["TESTLAR"] if "TESTLAR" in wb.sheetnames else wb.active
    headers = [str(c.value).strip() if c.value else "" for c in ws[1]]
    if "topic_code" not in headers:
        cur.close(); conn.close()
        raise HTTPException(status_code=400, detail="Excel ustunlari mos emas вЂ” 'topic_code' topilmadi")

    saved, boshqaga_tegishli, errors = 0, 0, 0
    for row in ws.iter_rows(min_row=2):
        d = {headers[i]: cell.value for i, cell in enumerate(row) if i < len(headers) and headers[i]}
        tc = d.get("topic_code")
        q = d.get("question")
        if not tc or not q or str(tc).strip() == "" or str(q).strip() == "":
            continue
        tc_s = str(tc).strip()
        if tc_s not in ozi_kodlari:
            boshqaga_tegishli += 1
            continue
        try:
            cur.execute("""
                INSERT INTO generated_tests
                (topic_code, difficulty, situation, question, option_a, option_b, option_c, option_d,
                 correct_answer, explanation, question_type, is_latex, image_url, audio_text,
                 language, life_level, age_group, time_limit)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                tc_s, d.get("difficulty") or "o'rta", d.get("situation") or "oddiy", str(q).strip(),
                d.get("option_a"), d.get("option_b"), d.get("option_c"), d.get("option_d"),
                d.get("correct_answer"), d.get("explanation"),
                d.get("question_type") or "single_choice",
                bool(d.get("is_latex")) if d.get("is_latex") not in (None, "") else False,
                d.get("image_url"), d.get("audio_text"), d.get("language") or "uz",
                d.get("life_level") or 1, d.get("age_group"), d.get("time_limit") or 60,
            ))
            conn.commit()
            saved += 1
        except Exception:
            conn.rollback()
            errors += 1

    cur.close()
    conn.close()
    return {"saved": saved, "boshqaga_tegishli": boshqaga_tegishli, "errors": errors}


@app.get("/api/oqituvchi/togarak_mavzu_savollari")
def togarak_mavzu_savollari(token: str, topic_code: str):
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _togarak_mavzu_kontenti_jadvali(cur)
    cur.execute("SELECT togarak_id FROM togarak_mavzu_kontenti WHERE topic_code=%s", (topic_code,))
    k = cur.fetchone()
    if not k:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Mavzu topilmadi")
    if not _togarak_ozi_mi(cur, user_id, k["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin ko'ra oladi")
    cur.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d, correct_answer, explanation, question_type
        FROM generated_tests WHERE topic_code=%s ORDER BY id
    """, (topic_code,))
    natija = cur.fetchall()
    cur.close()
    conn.close()
    return {"savollar": natija}


@app.delete("/api/oqituvchi/togarak_savol_ochir")
def togarak_savol_ochir(token: str, savol_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _togarak_mavzu_kontenti_jadvali(cur)
    cur.execute("SELECT topic_code FROM generated_tests WHERE id=%s", (savol_id,))
    s = cur.fetchone()
    if not s:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Savol topilmadi")
    cur.execute("SELECT togarak_id FROM togarak_mavzu_kontenti WHERE topic_code=%s", (s["topic_code"],))
    k = cur.fetchone()
    if not k or not _togarak_ozi_mi(cur, user_id, k["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin o'chira oladi")
    cur.execute("DELETE FROM generated_tests WHERE id=%s", (savol_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"holat": "ochirildi"}


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# TO'GARAK MAVZULARI вЂ” o'qituvchi MILLIY bazadan (yoki o'zi
# yaratgan) mavzularni o'z to'garagiga TANLAB biriktiradi, va har
# biriga MAZMUNLI kontent (matn/LaTeX/rasm/PDF/Word/video) yuklaydi.
# O'quvchi (to'garak a'zosi) buni ALOHIDA "Mavzular" bo'limida
# o'qiydi/ko'radi. Word matni o'qish uchun serverda AJRATIB olinadi
# (frontend Web Speech API bilan ovozli o'qiydi вЂ” alohida to'lovli
# TTS xizmat kerak emas).
#
# MUHIM CHEKLOV (halol aytilishi kerak): YouTube "obuna bo'lmasa
# ko'rolmaydi" talabi вЂ” bu YouTube'ning O'ZINING API orqali, HAR BIR
# talaba O'Z Google hisobi bilan maxsus ruxsat berishini talab
# qiladi (oddiy havola qo'yish bilan ILOJI YO'Q). Buning uchun
# alohida Google Cloud loyihasi + YouTube Data API kaliti kerak вЂ”
# buni ALBATTA gaplashib, keyingi bosqichda alohida quramiz. Hozircha
# video ko'rilish SONI (o'z platformamizda) to'liq ishlaydi.
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

def _togarak_biriktirma_jadvali(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS togarak_mavzu_biriktirma(
        id SERIAL PRIMARY KEY,
        togarak_id INTEGER NOT NULL REFERENCES togaraklar(id),
        topic_code TEXT NOT NULL,
        kontent_turi TEXT NOT NULL,
        sarlavha TEXT,
        matn TEXT,
        fayl_malumot BYTEA,
        fayl_nomi TEXT,
        fayl_turi TEXT,
        video_havola TEXT,
        korilish_soni INTEGER DEFAULT 0,
        yuklagan_user_id BIGINT REFERENCES users(user_id),
        yaratilgan_at TIMESTAMP DEFAULT NOW()
    )""")


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# MAVZU KITOBI вЂ” "sayt-bot yurituvchi to'garak" uchun poydevor.
# O'qituvchi HAR BIR mavzu uchun: (1) bir yoki bir nechta VIDEO
# (yuklangan yoki YouTube), (2) shu videolarga ANIQ SONIYASI bilan
# BOG'LANGAN misollar ketma-ketligini ("kitob varag'i" вЂ” masala +
# yechim tushuntirishi, LaTeX qo'llab-quvvatlanadi) tuzadi.
# O'quvchi (keyingi bosqichda) videoni ko'radi, mos misolni yechadi,
# tushunmasa "Tushunmadim" bosib, aynan shu joydagi tushuntirish/video
# soniyasiga yo'naltiriladi.
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

def _mavzu_kitobi_jadvallari(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS mavzu_darslik_videolari(
        id SERIAL PRIMARY KEY,
        togarak_id INTEGER NOT NULL REFERENCES togaraklar(id),
        topic_code TEXT NOT NULL,
        tartib_raqami INTEGER NOT NULL,
        sarlavha TEXT,
        video_havola TEXT NOT NULL,
        yaratilgan_at TIMESTAMP DEFAULT NOW()
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mavzu_kitob_misollari(
        id SERIAL PRIMARY KEY,
        togarak_id INTEGER NOT NULL REFERENCES togaraklar(id),
        topic_code TEXT NOT NULL,
        video_id INTEGER REFERENCES mavzu_darslik_videolari(id) ON DELETE SET NULL,
        tartib_raqami INTEGER NOT NULL,
        masala_matni TEXT NOT NULL,
        yechim_matni TEXT,
        video_soniya INTEGER,
        video_tugash_soniya INTEGER,
        yaratilgan_at TIMESTAMP DEFAULT NOW()
    )""")
    cur.execute("ALTER TABLE mavzu_kitob_misollari ADD COLUMN IF NOT EXISTS video_tugash_soniya INTEGER")


@app.get("/api/oqituvchi/mavzu_kitobi")
def mavzu_kitobi_korish(token: str, togarak_id: int, topic_code: str):
    """Bitta mavzuning to'liq 'kitobi' вЂ” videolar ro'yxati, har
    biriga bog'langan misollar (tartib bilan)."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin ko'ra oladi")
    _mavzu_kitobi_jadvallari(cur)
    cur.execute(
        "SELECT id, tartib_raqami, sarlavha, video_havola FROM mavzu_darslik_videolari WHERE togarak_id=%s AND topic_code=%s ORDER BY tartib_raqami",
        (togarak_id, topic_code),
    )
    videolar = cur.fetchall()
    cur.execute(
        "SELECT id, video_id, tartib_raqami, masala_matni, yechim_matni, video_soniya, video_tugash_soniya FROM mavzu_kitob_misollari WHERE togarak_id=%s AND topic_code=%s ORDER BY tartib_raqami",
        (togarak_id, topic_code),
    )
    misollar = cur.fetchall()
    cur.close(); conn.close()
    return {"videolar": videolar, "misollar": misollar}


class MavzuVideoQoshish(BaseModel):
    token: str
    togarak_id: int
    topic_code: str
    sarlavha: Optional[str] = None
    video_havola: str


@app.post("/api/oqituvchi/mavzu_video_qosh")
def mavzu_video_qosh(sorov: MavzuVideoQoshish):
    user_id = _jwt_tekshir(sorov.token)
    if not (sorov.video_havola or "").strip():
        raise HTTPException(status_code=400, detail="Video havolasini kiriting")
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, sorov.togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin qo'sha oladi")
    _mavzu_kitobi_jadvallari(cur)
    cur.execute(
        "SELECT COALESCE(MAX(tartib_raqami),0)+1 AS keyingi FROM mavzu_darslik_videolari WHERE togarak_id=%s AND topic_code=%s",
        (sorov.togarak_id, sorov.topic_code),
    )
    keyingi = cur.fetchone()["keyingi"]
    cur.execute(
        "INSERT INTO mavzu_darslik_videolari(togarak_id, topic_code, tartib_raqami, sarlavha, video_havola) VALUES(%s,%s,%s,%s,%s) RETURNING id",
        (sorov.togarak_id, sorov.topic_code, keyingi, sorov.sarlavha, sorov.video_havola.strip()),
    )
    yangi_id = cur.fetchone()["id"]
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "qoshildi", "video_id": yangi_id}


@app.delete("/api/oqituvchi/mavzu_video_ochir")
def mavzu_video_ochir(token: str, video_id: int):
    """Videoni o'chiradi вЂ” unga bog'langan misollar O'CHIRILMAYDI,
    faqat video_id bo'shatiladi (ON DELETE SET NULL), chunki
    misoldagi matn/yechim o'zi qimmatli, faqat video bog'lanishi
    yo'qoladi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _mavzu_kitobi_jadvallari(cur)
    cur.execute("SELECT togarak_id FROM mavzu_darslik_videolari WHERE id=%s", (video_id,))
    v = cur.fetchone()
    if not v:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Video topilmadi")
    if not _togarak_ozi_mi(cur, user_id, v["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin o'chira oladi")
    cur.execute("DELETE FROM mavzu_darslik_videolari WHERE id=%s", (video_id,))
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "ochirildi"}


class MavzuMisolQoshish(BaseModel):
    token: str
    togarak_id: int
    topic_code: str
    video_id: Optional[int] = None
    masala_matni: str
    yechim_matni: Optional[str] = None
    video_soniya: Optional[int] = None
    video_tugash_soniya: Optional[int] = None


@app.post("/api/oqituvchi/mavzu_misol_qosh")
def mavzu_misol_qosh(sorov: MavzuMisolQoshish):
    """Kitobga yangi misol qo'shadi вЂ” mavzu ichidagi UMUMIY tartibning
    OXIRIGA (video 1 в†’ uning misollari в†’ video 2 в†’ uning misollari...
    ketma-ketligi shu tartib raqami orqali saqlanadi)."""
    user_id = _jwt_tekshir(sorov.token)
    if not (sorov.masala_matni or "").strip():
        raise HTTPException(status_code=400, detail="Masala matnini kiriting")
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, sorov.togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin qo'sha oladi")
    _mavzu_kitobi_jadvallari(cur)
    if sorov.video_id is not None:
        cur.execute("SELECT 1 FROM mavzu_darslik_videolari WHERE id=%s AND togarak_id=%s", (sorov.video_id, sorov.togarak_id))
        if not cur.fetchone():
            cur.close(); conn.close()
            raise HTTPException(status_code=400, detail="Ko'rsatilgan video shu to'garakka tegishli emas")
    cur.execute(
        "SELECT COALESCE(MAX(tartib_raqami),0)+1 AS keyingi FROM mavzu_kitob_misollari WHERE togarak_id=%s AND topic_code=%s",
        (sorov.togarak_id, sorov.topic_code),
    )
    keyingi = cur.fetchone()["keyingi"]
    cur.execute("""
        INSERT INTO mavzu_kitob_misollari(togarak_id, topic_code, video_id, tartib_raqami, masala_matni, yechim_matni, video_soniya, video_tugash_soniya)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
    """, (sorov.togarak_id, sorov.topic_code, sorov.video_id, keyingi, sorov.masala_matni.strip(),
          sorov.yechim_matni.strip() if sorov.yechim_matni else None, sorov.video_soniya, sorov.video_tugash_soniya))
    yangi_id = cur.fetchone()["id"]
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "qoshildi", "misol_id": yangi_id}


class MavzuMisolTahrirlash(BaseModel):
    token: str
    misol_id: int
    video_id: Optional[int] = None
    masala_matni: str
    yechim_matni: Optional[str] = None
    video_soniya: Optional[int] = None
    video_tugash_soniya: Optional[int] = None


@app.put("/api/oqituvchi/mavzu_misol_tahrirlash")
def mavzu_misol_tahrirlash(sorov: MavzuMisolTahrirlash):
    user_id = _jwt_tekshir(sorov.token)
    if not (sorov.masala_matni or "").strip():
        raise HTTPException(status_code=400, detail="Masala matnini kiriting")
    conn = _db()
    cur = conn.cursor()
    _mavzu_kitobi_jadvallari(cur)
    cur.execute("SELECT togarak_id FROM mavzu_kitob_misollari WHERE id=%s", (sorov.misol_id,))
    m = cur.fetchone()
    if not m:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Misol topilmadi")
    if not _togarak_ozi_mi(cur, user_id, m["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin tahrirlay oladi")
    cur.execute("""
        UPDATE mavzu_kitob_misollari SET video_id=%s, masala_matni=%s, yechim_matni=%s, video_soniya=%s, video_tugash_soniya=%s WHERE id=%s
    """, (sorov.video_id, sorov.masala_matni.strip(), sorov.yechim_matni.strip() if sorov.yechim_matni else None,
          sorov.video_soniya, sorov.video_tugash_soniya, sorov.misol_id))
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "saqlandi"}


@app.delete("/api/oqituvchi/mavzu_misol_ochir")
def mavzu_misol_ochir(token: str, misol_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _mavzu_kitobi_jadvallari(cur)
    cur.execute("SELECT togarak_id, topic_code FROM mavzu_kitob_misollari WHERE id=%s", (misol_id,))
    m = cur.fetchone()
    if not m:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Misol topilmadi")
    if not _togarak_ozi_mi(cur, user_id, m["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin o'chira oladi")
    cur.execute("DELETE FROM mavzu_kitob_misollari WHERE id=%s", (misol_id,))
    cur.execute("SELECT id FROM mavzu_kitob_misollari WHERE togarak_id=%s AND topic_code=%s ORDER BY tartib_raqami", (m["togarak_id"], m["topic_code"]))
    qolganlar = cur.fetchall()
    for i, q in enumerate(qolganlar, start=1):
        cur.execute("UPDATE mavzu_kitob_misollari SET tartib_raqami=%s WHERE id=%s", (i, q["id"]))
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "ochirildi"}


class MavzuMisolSurish(BaseModel):
    token: str
    misol_id: int
    yonalish: str  # "yuqori" | "pastga"


@app.put("/api/oqituvchi/mavzu_misol_surish")
def mavzu_misol_surish(sorov: MavzuMisolSurish):
    user_id = _jwt_tekshir(sorov.token)
    conn = _db()
    cur = conn.cursor()
    _mavzu_kitobi_jadvallari(cur)
    cur.execute("SELECT togarak_id, topic_code, tartib_raqami FROM mavzu_kitob_misollari WHERE id=%s", (sorov.misol_id,))
    joriy = cur.fetchone()
    if not joriy:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Misol topilmadi")
    if not _togarak_ozi_mi(cur, user_id, joriy["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin tartiblay oladi")
    yangi_tartib = joriy["tartib_raqami"] + (1 if sorov.yonalish == "pastga" else -1)
    cur.execute(
        "SELECT id FROM mavzu_kitob_misollari WHERE togarak_id=%s AND topic_code=%s AND tartib_raqami=%s",
        (joriy["togarak_id"], joriy["topic_code"], yangi_tartib),
    )
    qoshni = cur.fetchone()
    if qoshni:
        cur.execute("UPDATE mavzu_kitob_misollari SET tartib_raqami=%s WHERE id=%s", (joriy["tartib_raqami"], qoshni["id"]))
        cur.execute("UPDATE mavzu_kitob_misollari SET tartib_raqami=%s WHERE id=%s", (yangi_tartib, sorov.misol_id))
        conn.commit()
    cur.close(); conn.close()
    return {"holat": "surildi"}


@app.get("/api/togarak_azo/mavzu_kitobi")
def oquvchi_mavzu_kitobi(token: str, togarak_id: int, topic_code: str):
    """O'QUVCHI uchun вЂ” bitta mavzuning 'kitobi' (videolar + ularga
    bog'langan misollar), mustaqil o'rganish uchun."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_kontent_ruxsat_bormi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Siz bu to'garak a'zosi emassiz")
    _mavzu_kitobi_jadvallari(cur)
    cur.execute(
        "SELECT id, tartib_raqami, sarlavha, video_havola FROM mavzu_darslik_videolari WHERE togarak_id=%s AND topic_code=%s ORDER BY tartib_raqami",
        (togarak_id, topic_code),
    )
    videolar = cur.fetchall()
    cur.execute(
        "SELECT id, video_id, tartib_raqami, masala_matni, yechim_matni, video_soniya, video_tugash_soniya FROM mavzu_kitob_misollari WHERE togarak_id=%s AND topic_code=%s ORDER BY tartib_raqami",
        (togarak_id, topic_code),
    )
    misollar = cur.fetchall()
    cur.close(); conn.close()
    return {"videolar": videolar, "misollar": misollar}


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# MUSTAQIL ISHLAR вЂ” mavzu "kitobi"dan (video+misollar) keyin,
# o'quvchi MUSTAQIL yechishi kerak bo'lgan amaliy topshiriqlar.
# O'qituvchi savol + TO'G'RI JAVOB MEZONINI yozadi; o'quvchi ERKIN
# MATNDA javob yozadi, va AI (LLM) shu mezon asosida TEKSHIRIB,
# to'g'ri-noto'g'riligini va SABABINI aniqlaydi вЂ” oddiy test (variant
# tanlash) EMAS, chunki yozma yechim/tushuntirish talab qilinadi.
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ

def _mustaqil_ish_jadvallari(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS mavzu_mustaqil_ishlar(
        id SERIAL PRIMARY KEY,
        togarak_id INTEGER NOT NULL REFERENCES togaraklar(id),
        topic_code TEXT NOT NULL,
        tartib_raqami INTEGER NOT NULL,
        savol_matni TEXT NOT NULL,
        togri_javob_mezoni TEXT NOT NULL,
        yaratilgan_at TIMESTAMP DEFAULT NOW()
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mustaqil_ish_javoblari(
        id SERIAL PRIMARY KEY,
        ish_id INTEGER NOT NULL REFERENCES mavzu_mustaqil_ishlar(id),
        user_id BIGINT NOT NULL REFERENCES users(user_id),
        javob_matni TEXT NOT NULL,
        togrimi BOOLEAN,
        ai_izohi TEXT,
        yuborilgan_at TIMESTAMP DEFAULT NOW()
    )""")


@app.get("/api/oqituvchi/mustaqil_ishlar")
def mustaqil_ishlar_royxati(token: str, togarak_id: int, topic_code: str):
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin ko'ra oladi")
    _mustaqil_ish_jadvallari(cur)
    cur.execute(
        "SELECT id, tartib_raqami, savol_matni, togri_javob_mezoni FROM mavzu_mustaqil_ishlar WHERE togarak_id=%s AND topic_code=%s ORDER BY tartib_raqami",
        (togarak_id, topic_code),
    )
    natija = cur.fetchall()
    cur.close(); conn.close()
    return {"ishlar": natija}


class MustaqilIshQoshish(BaseModel):
    token: str
    togarak_id: int
    topic_code: str
    savol_matni: str
    togri_javob_mezoni: str


@app.post("/api/oqituvchi/mustaqil_ish_qosh")
def mustaqil_ish_qosh(sorov: MustaqilIshQoshish):
    user_id = _jwt_tekshir(sorov.token)
    if not (sorov.savol_matni or "").strip() or not (sorov.togri_javob_mezoni or "").strip():
        raise HTTPException(status_code=400, detail="Savol va to'g'ri javob mezonini kiriting")
    conn = _db()
    cur = conn.cursor()
    if not _togarak_ozi_mi(cur, user_id, sorov.togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin qo'sha oladi")
    _mustaqil_ish_jadvallari(cur)
    cur.execute(
        "SELECT COALESCE(MAX(tartib_raqami),0)+1 AS keyingi FROM mavzu_mustaqil_ishlar WHERE togarak_id=%s AND topic_code=%s",
        (sorov.togarak_id, sorov.topic_code),
    )
    keyingi = cur.fetchone()["keyingi"]
    cur.execute(
        "INSERT INTO mavzu_mustaqil_ishlar(togarak_id, topic_code, tartib_raqami, savol_matni, togri_javob_mezoni) VALUES(%s,%s,%s,%s,%s) RETURNING id",
        (sorov.togarak_id, sorov.topic_code, keyingi, sorov.savol_matni.strip(), sorov.togri_javob_mezoni.strip()),
    )
    yangi_id = cur.fetchone()["id"]
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "qoshildi", "ish_id": yangi_id}


@app.delete("/api/oqituvchi/mustaqil_ish_ochir")
def mustaqil_ish_ochir(token: str, ish_id: int):
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    _mustaqil_ish_jadvallari(cur)
    cur.execute("SELECT togarak_id FROM mavzu_mustaqil_ishlar WHERE id=%s", (ish_id,))
    m = cur.fetchone()
    if not m:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Topilmadi")
    if not _togarak_ozi_mi(cur, user_id, m["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Faqat shu to'garak o'qituvchisi, markaz rahbariyati yoki admin o'chira oladi")
    cur.execute("DELETE FROM mustaqil_ish_javoblari WHERE ish_id=%s", (ish_id,))
    cur.execute("DELETE FROM mavzu_mustaqil_ishlar WHERE id=%s", (ish_id,))
    conn.commit()
    cur.close(); conn.close()
    return {"holat": "ochirildi"}


@app.get("/api/togarak_azo/mustaqil_ishlar")
def oquvchi_mustaqil_ishlar(token: str, togarak_id: int, topic_code: str):
    """O'quvchi uchun вЂ” savollar + O'ZI avval yuborgan (agar bo'lsa)
    oxirgi javobi/natijasi."""
    user_id = _jwt_tekshir(token)
    conn = _db()
    cur = conn.cursor()
    if not _togarak_kontent_ruxsat_bormi(cur, user_id, togarak_id):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Siz bu to'garak a'zosi emassiz")
    _mustaqil_ish_jadvallari(cur)
    cur.execute(
        "SELECT id, tartib_raqami, savol_matni FROM mavzu_mustaqil_ishlar WHERE togarak_id=%s AND topic_code=%s ORDER BY tartib_raqami",
        (togarak_id, topic_code),
    )
    ishlar = cur.fetchall()
    natija = []
    for ish in ishlar:
        cur.execute(
            "SELECT javob_matni, togrimi, ai_izohi FROM mustaqil_ish_javoblari WHERE ish_id=%s AND user_id=%s ORDER BY yuborilgan_at DESC LIMIT 1",
            (ish["id"], user_id),
        )
        oxirgi = cur.fetchone()
        natija.append({**ish, "oxirgi_javob": oxirgi})
    cur.close(); conn.close()
    return {"ishlar": natija}


class MustaqilIshTopshirish(BaseModel):
    token: str
    ish_id: int
    javob_matni: str


@app.post("/api/togarak_azo/mustaqil_ish_topshir")
def oquvchi_mustaqil_ish_topshir(sorov: MustaqilIshTopshirish):
    """O'quvchi javobni yuboradi вЂ” AI (agar GROQ_API_KEY sozlangan
    bo'lsa) darhol tekshirib, to'g'ri-noto'g'riligini va sababini
    aniqlaydi. AI sozlanmagan bo'lsa ham javob saqlanadi (baholashsiz)."""
    user_id = _jwt_tekshir(sorov.token)
    if not (sorov.javob_matni or "").strip():
        raise HTTPException(status_code=400, detail="Javobingizni kiriting")
    conn = _db()
    cur = conn.cursor()
    _mustaqil_ish_jadvallari(cur)
    cur.execute(
        """SELECT togarak_id,topic_code,savol_matni,togri_javob_mezoni
           FROM mavzu_mustaqil_ishlar WHERE id=%s""",
        (sorov.ish_id,),
    )
    ish = cur.fetchone()
    if not ish:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Topshiriq topilmadi")
    if not _togarak_kontent_ruxsat_bormi(cur, user_id, ish["togarak_id"]):
        cur.close(); conn.close()
        raise HTTPException(status_code=403, detail="Siz bu to'garak a'zosi emassiz")

    togrimi, izoh = None, None
    if GROQ_API_KALIT:
        tizim_promt = (
            "Sen вЂ” matematik/fan o'qituvchisisan. O'quvchining yozma javobini "
            "TO'G'RI JAVOB MEZONI bilan solishtirib bahola. "
            "FAQAT quyidagi JSON formatida javob ber, boshqa hech narsa yozma: "
            '{"togri": true yoki false, "izoh": "o\'zbek tilida, o\'quvchiga qaratilgan, '
            "qisqa (2-3 gap) tushuntirish вЂ” agar noto'g'ri bo'lsa ANIQ qayerda xato "
            "qilganini tushuntir, agar to'g'ri bo'lsa qisqa tasdiq yoz\"}"
        )
        foydalanuvchi_promt = (
            f"SAVOL: {ish['savol_matni']}\n\n"
            f"TO'G'RI JAVOB MEZONI: {ish['togri_javob_mezoni']}\n\n"
            f"O'QUVCHI JAVOBI: {sorov.javob_matni.strip()}"
        )
        try:
            with httpx.Client(timeout=20) as client:
                javob = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_API_KALIT}", "Content-Type": "application/json"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": tizim_promt},
                            {"role": "user", "content": foydalanuvchi_promt},
                        ],
                        "temperature": 0.2,
                        "max_tokens": 300,
                        "response_format": {"type": "json_object"},
                    },
                )
            javob.raise_for_status()
            matn = javob.json()["choices"][0]["message"]["content"]
            natija_json = json.loads(matn)
            togrimi = bool(natija_json.get("togri"))
            izoh = natija_json.get("izoh")
        except Exception:
            togrimi, izoh = None, "Javobingiz saqlandi, lekin avtomatik tekshirish hozircha ishlamadi вЂ” keyinroq qayta urinib ko'ring."
    else:
        izoh = "Javobingiz saqlandi. Avtomatik tekshirish hali sozlanmagan."

    cur.execute(
        """INSERT INTO mustaqil_ish_javoblari
           (ish_id,user_id,javob_matni,togrimi,ai_izohi)
           VALUES(%s,%s,%s,%s,%s) RETURNING id""",
        (sorov.ish_id, user_id, sorov.javob_matni.strip(), togrimi, izoh),
    )
    javob_id = cur.fetchone()["id"]
    if _analitika_jadvallar_bormi(cur):
        context_id, group_id = _analitika_togarak_oquvchi_azolikni_taminla(
            cur, ish["togarak_id"], user_id
        )
        cur.execute(
            """SELECT c.context_type,g.subject
               FROM learning_contexts c
               LEFT JOIN course_groups g ON g.id=%s
               WHERE c.id=%s""",
            (group_id, context_id),
        )
        manba = cur.fetchone()
        _analitika_event_qosh(
            cur,
            user_id=user_id,
            actor_user_id=user_id,
            event_type="written_work",
            source_type=ANALITIKA_KONTEKST_MANBASI.get(
                manba["context_type"] if manba else "club_offline", "club_offline"
            ),
            evidence_source="ai_tutor" if GROQ_API_KALIT else "self",
            context_id=context_id,
            group_id=group_id,
            topic_cod
