"""Production runtime for SamTM V20 / REV61.

Features:
- one-time schema migration guarded by PostgreSQL advisory lock;
- no repeated CREATE/ALTER on hot requests;
- request IDs, timing and graceful overload protection;
- short micro-cache for repeated read-only school requests;
- optional Redis cache when REDIS_URL is present;
- readiness/liveness endpoints and performance diagnostics.
"""
from __future__ import annotations
import asyncio, hashlib, json, os, secrets, threading, time
from collections import OrderedDict
from typing import Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

SCHEMA_VERSION = "20.0.0-rev61"
SCHEMA_HELPERS = ['_telefon_jadvallari', '_savol_javob_tarixi_tayyorla', '_ota_ona_jadvallari', '_rol_ustunlarini_tayyorla', '_togarak_mavzu_kontenti_jadvali', '_reja_jadvallari', '_togaraklar_reja_id_ustuni', '_users_profil_rasm_ustunlari', '_togarak_biriktirma_jadvali', '_mavzu_kitobi_jadvallari', '_mustaqil_ish_jadvallari', '_chat_jadvallari', '_moderatsiya_jadvallari', '_reaksiya_jadvali', '_dars_kalendar_jadvallari', '_oquvchi_kalendar_jadvallari', '_togarak_azolar_tasdiq_ustuni', '_maktab_jadvali', '_xodim_kod_jadvali', '_maktab_sinflari_jadvali', '_xodim_sinf_birikmalari_jadvali', '_maktab_fanlari_jadvali', '_tolov_jadvallari', '_sinf_azolari_jadvali', '_muassasa_jadvali', '_sinf_kop_guruh_jadvallari', '_davomat_jadvali', '_kutubxona_jadvali', '_moliya_jadvali', '_hujjatlar_jadvali', '_rejalashtirish_jadvallari', '_xodim_davomati_jadvali', '_sogliq_jadvali', '_psixolog_jadvali', '_markaz_jadvali', '_bogcha_jadvali', '_universitet_jadvali', '_tushuntirish_jadvali', '_dts_kod_ustunlarini_tayyorla', '_ai_brain_jadvallari', '_ai_pedagogik_jadvallar', '_v1845_smart_school_tables', '_v1852_create_tables', '_v1871_auto_method_tables', '_v1873_tables', '_v1875_tables', '_v1876_tables', '_v192_tables']
MOVED_DDL = ['ALTER TABLE users ADD COLUMN IF NOT EXISTS tugilgan_sana DATE', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS maktab_raqami TEXT', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS jins TEXT', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS oqituvchi_fani TEXT', "ALTER TABLE users ADD COLUMN IF NOT EXISTS asosiy_til TEXT DEFAULT 'uz'", 'ALTER TABLE users ADD COLUMN IF NOT EXISTS ovoz_jinsi TEXT', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS maktab_id INTEGER', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS markaz_id INTEGER', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS bogcha_id INTEGER', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS universitet_id INTEGER', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS lavozim TEXT', 'CREATE TABLE IF NOT EXISTS sayt_ulash_kod(\n        kod TEXT PRIMARY KEY, web_user_id BIGINT REFERENCES users(user_id),\n        yaratildi TIMESTAMP DEFAULT NOW(), ishlatildi BOOLEAN DEFAULT FALSE)', "ALTER TABLE togaraklar ADD COLUMN IF NOT EXISTS turi TEXT DEFAULT 'oddiy'", "ALTER TABLE togaraklar ADD COLUMN IF NOT EXISTS guruh_turi TEXT DEFAULT 'togarak'", 'ALTER TABLE togaraklar ADD COLUMN IF NOT EXISTS sinf TEXT', 'ALTER TABLE togaraklar ADD COLUMN IF NOT EXISTS markaz_id INTEGER', 'ALTER TABLE togaraklar ADD COLUMN IF NOT EXISTS universitet_guruh_id INTEGER', 'CREATE TABLE IF NOT EXISTS togarak_mavzulari(\n        togarak_id INTEGER REFERENCES togaraklar(id),\n        topic_code TEXT,\n        PRIMARY KEY (togarak_id, topic_code)\n    )', 'CREATE TABLE IF NOT EXISTS reaksiya_natijalari(\n        id SERIAL PRIMARY KEY,\n        user_id BIGINT NOT NULL REFERENCES users(user_id),\n        millisekund INTEGER NOT NULL,\n        yaratilgan_at TIMESTAMP DEFAULT NOW()\n    )', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS fanlari TEXT', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS ish_staji INTEGER', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS toifasi TEXT', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS haftalik_dars_soati INTEGER', 'ALTER TABLE tolovlar ADD COLUMN IF NOT EXISTS bogcha_guruh_id INTEGER REFERENCES bogcha_guruhlari(id)', 'CREATE UNIQUE INDEX IF NOT EXISTS tolovlar_bogcha_unique ON tolovlar(user_id, bogcha_guruh_id, oy)', 'CREATE TABLE IF NOT EXISTS togarak_azolar(\n            id SERIAL PRIMARY KEY, togarak_id INTEGER REFERENCES togaraklar(id),\n            user_id BIGINT REFERENCES users(user_id), aktiv BOOLEAN DEFAULT TRUE, qoshilgan_at TIMESTAMP DEFAULT NOW()\n        )', "ALTER TABLE generated_tests ADD COLUMN IF NOT EXISTS question_type TEXT DEFAULT 'single_choice'", "ALTER TABLE generated_tests ADD COLUMN IF NOT EXISTS maqsad TEXT DEFAULT 'oddiy'", 'ALTER TABLE generated_tests ADD COLUMN IF NOT EXISTS rasm_malumot BYTEA', 'ALTER TABLE generated_tests ADD COLUMN IF NOT EXISTS rasm_turi TEXT', 'ALTER TABLE users ADD COLUMN IF NOT EXISTS kundalik_baho_eslatmasi BOOLEAN NOT NULL DEFAULT FALSE']
_SCHEMA_READY: set[str] = set()
_SCHEMA_LOCK = threading.Lock()
_ORIGINALS: dict[tuple[int,str], Any] = {}

# Indexes are conditional: old installations may not yet have every table.
INDEXES = [
    ("users", "CREATE INDEX IF NOT EXISTS idx_users_maktab_lavozim_v19 ON users(maktab_id,lavozim,user_id)"),
    ("users", "CREATE INDEX IF NOT EXISTS idx_users_markaz_v19 ON users(markaz_id,user_id)"),
    ("maktab_sinflari", "CREATE INDEX IF NOT EXISTS idx_maktab_sinflari_school_v19 ON maktab_sinflari(maktab_id,sinf,harf,id)"),
    ("maktab_dars_birikmalari", "CREATE INDEX IF NOT EXISTS idx_mdb_school_teacher_v19 ON maktab_dars_birikmalari(maktab_id,user_id,sinf_id)"),
    ("maktab_dars_birikmalari", "CREATE INDEX IF NOT EXISTS idx_mdb_class_subject_v19 ON maktab_dars_birikmalari(maktab_id,sinf_id,fan_nomi,guruh_kaliti)"),
    ("aqlli_jadval_urinishlari_v2", "CREATE INDEX IF NOT EXISTS idx_aju_school_status_v19 ON aqlli_jadval_urinishlari_v2(maktab_id,holat,id DESC)"),
    ("aqlli_jadval_slotlari_v2", "CREATE INDEX IF NOT EXISTS idx_ajs_teacher_week_v19 ON aqlli_jadval_slotlari_v2(urinish_id,oqituvchi_user_id,hafta_kuni,smena,dars_raqami)"),
    ("aqlli_jadval_slotlari_v2", "CREATE INDEX IF NOT EXISTS idx_ajs_class_week_v19 ON aqlli_jadval_slotlari_v2(urinish_id,sinf_id,hafta_kuni,smena,dars_raqami)"),
    ("aqlli_oqituvchi_vaqti_v2", "CREATE INDEX IF NOT EXISTS idx_aov_school_teacher_v19 ON aqlli_oqituvchi_vaqti_v2(maktab_id,user_id,hafta_kuni,smena,dars_raqami)"),
    ("aqlli_sinf_fan_yuklamalari_v2", "CREATE INDEX IF NOT EXISTS idx_asfy_school_class_v19 ON aqlli_sinf_fan_yuklamalari_v2(maktab_id,sinf_id,fan_nomi)"),
    ("togarak_azolar", "CREATE INDEX IF NOT EXISTS idx_togarak_azolar_user_v19 ON togarak_azolar(user_id,aktiv,tasdiqlangan,togarak_id)"),
    ("generated_tests", "CREATE INDEX IF NOT EXISTS idx_generated_tests_topic_v19 ON generated_tests(topic_code,id)"),
    ("dts_tree", "CREATE INDEX IF NOT EXISTS idx_dts_grade_subject_v19 ON dts_tree(grade,subject_name,is_deleted,topic_code)"),
    ("organization_trials", "CREATE INDEX IF NOT EXISTS idx_org_trials_creator_v19 ON organization_trials(creator_user_id,lifecycle_status,id)"),
]

CACHEABLE_PREFIXES = tuple(x.strip() for x in os.getenv(
    "MICROCACHE_PATHS",
    "/api/maktab/dashboard,/api/maktab/yuklama_xulosasi,/api/maktab/aqlli_holatlar,/api/maktab/aqlli_jadval/v2/sozlamalar,/api/maktab/aqlli_jadval/v3/yuklama_matritsasi,/api/versiya"
).split(",") if x.strip())
CACHE_TTL = max(0.0, float(os.getenv("MICROCACHE_TTL_SECONDS", "3")))
CACHE_MAX = max(32, int(os.getenv("MICROCACHE_MAX_ENTRIES", "256")))
MAX_INFLIGHT = max(16, int(os.getenv("MAX_INFLIGHT_REQUESTS", "250")))
MAX_HEAVY = max(1, int(os.getenv("MAX_HEAVY_REQUESTS", "2")))
HEAVY_PATH_PARTS = (
    "/yaratish", "/xodim_import", "/shablon_import", "/import",
    "/oqituvchi_yuklamasi", "/oqituvchi_qoshish", "/almashtirish",
)

class _LocalCache:
    def __init__(self):
        self.data = OrderedDict()
        self.lock = asyncio.Lock()
    async def get(self, key):
        if not CACHE_TTL: return None
        async with self.lock:
            row = self.data.get(key)
            if not row: return None
            expires, value = row
            if expires <= time.monotonic():
                self.data.pop(key, None); return None
            self.data.move_to_end(key); return value
    async def set(self, key, value):
        if not CACHE_TTL: return
        async with self.lock:
            self.data[key] = (time.monotonic()+CACHE_TTL, value)
            self.data.move_to_end(key)
            while len(self.data) > CACHE_MAX:
                self.data.popitem(last=False)

_LOCAL_CACHE = _LocalCache()
_REDIS = None
try:
    import redis.asyncio as _redis
    if os.getenv("REDIS_URL"):
        _REDIS = _redis.from_url(os.environ["REDIS_URL"], decode_responses=False, socket_timeout=0.25)
except Exception:
    _REDIS = None

async def _cache_get(key):
    if _REDIS is not None:
        try: return await _REDIS.get(key)
        except Exception: pass
    return await _LOCAL_CACHE.get(key)

async def _cache_set(key, value):
    if _REDIS is not None:
        try:
            await _REDIS.setex(key, max(1,int(CACHE_TTL)), value); return
        except Exception: pass
    await _LOCAL_CACHE.set(key, value)

class RuntimeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.normal = asyncio.Semaphore(MAX_INFLIGHT)
        self.heavy = asyncio.Semaphore(MAX_HEAVY)
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or secrets.token_hex(8)
        started = time.perf_counter()
        heavy = any(part in request.url.path for part in HEAVY_PATH_PARTS)
        sem = self.heavy if heavy else self.normal
        try:
            await asyncio.wait_for(sem.acquire(), timeout=0.15)
        except asyncio.TimeoutError:
            return JSONResponse(status_code=503, content={"detail":"Server band. Bir necha soniyadan keyin qayta urinib ko'ring.","request_id":request_id}, headers={"Retry-After":"2","X-Request-ID":request_id})
        try:
            cache_key = None
            if request.method == "GET" and CACHE_TTL and request.url.path.startswith(CACHEABLE_PREFIXES):
                digest = hashlib.sha256(str(request.url).encode()).hexdigest()
                cache_key = f"samtm:v19:http:{digest}"
                cached = await _cache_get(cache_key)
                if cached:
                    payload = json.loads(cached)
                    headers = payload.get("headers", {})
                    headers.update({"X-Cache":"HIT","X-Request-ID":request_id})
                    return Response(content=bytes.fromhex(payload["body"]), status_code=payload["status"], media_type=payload.get("media_type"), headers=headers)
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter()-started)*1000:.1f}"
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            if cache_key and response.status_code == 200:
                body = b"".join([chunk async for chunk in response.body_iterator])
                rebuilt = Response(content=body, status_code=response.status_code, media_type=response.media_type, headers=dict(response.headers))
                if len(body) <= 300_000:
                    await _cache_set(cache_key, json.dumps({"status":response.status_code,"media_type":response.media_type,"headers":{"Cache-Control":f"private, max-age={int(CACHE_TTL)}"},"body":body.hex()}).encode())
                rebuilt.headers["X-Cache"] = "MISS"
                return rebuilt
            return response
        finally:
            sem.release()

def install_schema_guards(*modules):
    """After startup migration, pure schema helpers become no-ops on requests."""
    for module in modules:
        for name in SCHEMA_HELPERS:
            fn = getattr(module, name, None)
            if not callable(fn): continue
            key=(id(module),name)
            if key in _ORIGINALS: continue
            _ORIGINALS[key]=fn
            def make_wrapper(original, helper_name):
                def wrapper(cur, *args, **kwargs):
                    if helper_name in _SCHEMA_READY:
                        return None
                    return original(cur, *args, **kwargs)
                wrapper.__name__=getattr(original,'__name__',helper_name)
                wrapper.__doc__=getattr(original,'__doc__',None)
                return wrapper
            setattr(module, name, make_wrapper(fn,name))

def _original_for(name):
    for (module_id, helper_name), fn in _ORIGINALS.items():
        if helper_name == name: return fn
    return None

def register_runtime(app, platform, school):
    install_schema_guards(platform, school)
    app.add_middleware(RuntimeMiddleware)

    @app.get("/health/live", include_in_schema=False)
    def live(): return {"status":"ok","version":"v20","schema":SCHEMA_VERSION}

    @app.get("/health/ready", include_in_schema=False)
    def ready():
        conn=platform._db(); cur=conn.cursor()
        try:
            cur.execute("SELECT 1 AS ok")
            return {"status":"ready","version":"v20","db":bool(cur.fetchone()["ok"]),"schema_version":SCHEMA_VERSION,"schema_ready":len(_SCHEMA_READY)}
        finally:
            cur.close(); conn.close()

    @app.get("/api/admin/performance_v19", include_in_schema=False)
    def perf(token: str):
        platform._admin_tekshir(token)
        return {"version":"19.2","teacher_first":True,"smart_swap":True,"max_inflight_per_worker":MAX_INFLIGHT,"max_heavy_per_worker":MAX_HEAVY,"db_pool_per_worker":platform._DB_POOL_MAX,"microcache_ttl":CACHE_TTL,"redis":bool(_REDIS),"schema_helpers_cached":sorted(_SCHEMA_READY)}

    @app.on_event("startup")
    def migrate_once():
        conn=platform._db(); cur=conn.cursor()
        locked=False
        try:
            cur.execute("SELECT pg_advisory_lock(%s)", (19001900,)); locked=True
            cur.execute("CREATE TABLE IF NOT EXISTS samtm_schema_versions(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            cur.execute("SELECT 1 FROM samtm_schema_versions WHERE version=%s", (SCHEMA_VERSION,))
            already=cur.fetchone() is not None
            if not already:
                # Helpers run in source/dependency order. Each successful helper commits
                # independently, so a later optional module cannot roll back earlier schema.
                for name in SCHEMA_HELPERS:
                    original=_original_for(name)
                    if original is None: continue
                    try:
                        original(cur); conn.commit(); _SCHEMA_READY.add(name)
                    except Exception as exc:
                        conn.rollback(); print(f"[V19 schema helper skipped] {name}: {exc}", flush=True)
                for sql in MOVED_DDL:
                    try:
                        cur.execute(sql); conn.commit()
                    except Exception as exc:
                        conn.rollback(); print(f"[V19 moved DDL skipped] {sql[:80]}: {exc}", flush=True)
                for table, sql in INDEXES:
                    try:
                        cur.execute("SELECT to_regclass(%s) AS t", (f"public.{table}",))
                        if (cur.fetchone() or {}).get("t"):
                            cur.execute(sql); conn.commit()
                    except Exception as exc:
                        conn.rollback(); print(f"[V19 index skipped] {table}: {exc}", flush=True)
                cur.execute("INSERT INTO samtm_schema_versions(version) VALUES(%s) ON CONFLICT DO NOTHING", (SCHEMA_VERSION,)); conn.commit()
            else:
                _SCHEMA_READY.update(name for name in SCHEMA_HELPERS if _original_for(name))
        finally:
            if locked:
                try: cur.execute("SELECT pg_advisory_unlock(%s)", (19001900,)); conn.commit()
                except Exception: conn.rollback()
            cur.close(); conn.close()
