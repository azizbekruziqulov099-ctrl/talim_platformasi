"""SamTM V20 ASGI entry point — REV71 aylana importsiz institut routeri.

Railway BACKEND xizmati ``gunicorn main:app`` bilan aynan shu faylni
ishga tushirishi kerak. V19.8 school moduli yuklanmasa eski v19.2 server
yashirincha ishlab qolmaydi: deploy aniq xato bilan to'xtaydi.
"""

SAMTM_ASGI_RELEASE = "samtm-school-workspace-link-v19.8"
SAMTM_SCHOOL_PACKAGE_REVISION = "multi-school-access-2month-rev55"
SAMTM_PLATFORM_RELEASE = "samtm-institute-role-scope-four-stage-v20"
SAMTM_REQUIRED_ROUTES = {
    "/api/maktab/aqlli_jadval/v3/maktab_workspace_boglash",
    "/api/maktab/aqlli_jadval/v3/soat_imkoniyatlari",
    "/api/maktab/aqlli_jadval/v3/jadval_xlsx",
    "/api/institut/v20/bootstrap",
    "/api/institut/v20/tuzilma/import_preview",
    "/api/institut/v20/qabul/import_preview",
}

try:
    from . import samtm_platform, samtm_school, samtm_institute
    from .samtm_platform import app
    from .samtm_runtime import register_runtime
except ImportError:  # Railway Root Directory odatda backend/
    import samtm_platform
    import samtm_school
    import samtm_institute
    from samtm_platform import app
    from samtm_runtime import register_runtime


active_school_release = getattr(
    samtm_school,
    "SAMTM_SCHOOL_RELEASE",
    "",
)
if active_school_release != SAMTM_ASGI_RELEASE:
    raise RuntimeError(
        "samtm_school.py eski yoki repository ildizida emas. "
        "V19.8 paketdagi samtm_school.py ni to'liq almashtiring. "
        f"Kutilgan={SAMTM_ASGI_RELEASE}; topilgan={active_school_release or 'yoq'}"
    )

active_school_package_revision = getattr(
    samtm_school,
    "SAMTM_SCHOOL_PACKAGE_REVISION",
    "",
)
if active_school_package_revision != SAMTM_SCHOOL_PACKAGE_REVISION:
    raise RuntimeError(
        "samtm_school.py REV55 emas. Paketdagi faylni to'liq almashtiring. "
        f"Kutilgan={SAMTM_SCHOOL_PACKAGE_REVISION}; "
        f"topilgan={active_school_package_revision or 'yoq'}"
    )

samtm_institute.register_institute(app, samtm_platform)

registered_paths = {
    getattr(route, "path", None)
    for route in getattr(app, "routes", [])
}
missing_required_routes = sorted(SAMTM_REQUIRED_ROUTES - registered_paths)
if missing_required_routes:
    print("[STARTUP-WARNING] Institut route tekshiruvi: " + ", ".join(missing_required_routes), flush=True)

# /api/versiya samtm_platform modulidagi global qiymatlarni o'qiydi.
samtm_platform.SAMTM_RELEASE = SAMTM_PLATFORM_RELEASE
samtm_platform.SAMTM_PACKAGE_REVISION = (
    "institute-router-no-circular-import-rev71"
)

register_runtime(app, samtm_platform, samtm_school)
app.version = "20.0"
app.state.samtm_release = SAMTM_PLATFORM_RELEASE
app.state.teacher_first_load_enabled = True
app.state.smart_swap_enabled = True
app.state.v17_school_workspace_link_enabled = True

# Revocable authentication is installed through stable platform wrappers, so
# helpers already imported by school/institute also enforce session revocation.
try:
    from .kabutar_auth import register_auth
    from .modules.kabutar_audience import register_audience
except ImportError:
    from kabutar_auth import register_auth
    from modules.kabutar_audience import register_audience
register_auth(app, samtm_platform)
register_audience(app, samtm_platform)
# REV104: bitta akkauntdan 10 tagacha aralash profil (bog'cha bolalari, o'quvchilar, talaba; admin sinov profillari).
if __package__:
    from .kabutar_profiles import register_profiles
else:
    from kabutar_profiles import register_profiles
register_profiles(app, samtm_platform, samtm_platform._kabutar_auth_service)

# Exact nickname/KB lookup and opt-in verified-phone discovery.
try:
    from .kabutar_discovery import register_discovery
except ImportError:
    from kabutar_discovery import register_discovery
register_discovery(app, samtm_platform, samtm_platform._kabutar_auth_service)

# REV42: private curriculum plans and the database-grounded assistant.
# Use the router startup API, as with the existing authentication migration.
if __package__:
    from .modules.personal_schedule import register_personal_schedule
    from .modules.kabutar_assistant import register_assistant
else:
    from modules.personal_schedule import register_personal_schedule
    from modules.kabutar_assistant import register_assistant

register_personal_schedule(app, samtm_platform, samtm_school)
assistant_service = register_assistant(app, samtm_platform)
app.router.add_event_handler("startup", assistant_service.migrate)

# REV45: participant-authorized signaling; media uses the configured TURN/SFU.
if __package__:
    from .modules.kabutar_calls import register_calls
else:
    from modules.kabutar_calls import register_calls
call_service = register_calls(app, samtm_platform)
app.router.add_event_handler("startup", call_service.migrate)

if __package__:
    from .kabutar_safety import register_safety
    from .kabutar_terms import register_terms
    from .modules.military_school import register_military_school
    from .modules.military_operations import register_military_operations
else:
    from kabutar_safety import register_safety
    from kabutar_terms import register_terms
    from modules.military_school import register_military_school
    from modules.military_operations import register_military_operations
register_safety(app, samtm_platform, samtm_platform._kabutar_auth_service)
register_terms(app, samtm_platform, samtm_platform._kabutar_auth_service)
military_service = register_military_school(app, samtm_platform)
app.router.add_event_handler("startup", military_service.migrate)
military_operations_service = register_military_operations(app, samtm_platform)
app.router.add_event_handler("startup", military_operations_service.migrate)

# REV46: comments stay attached to the original post across history pages.
if __package__:
    from .modules.kabutar_threads import register_threads
else:
    from modules.kabutar_threads import register_threads
thread_service = register_threads(app, samtm_platform)
app.router.add_event_handler("startup", thread_service.migrate)

# REV47: self-paced courses, free YouTube embeds and manual course-fee records.
# Separate from live institution groups; no third-party paid service activation.
if __package__:
    from .modules.academy import register_courses
    from .modules.academy_media import register_media
    from .modules.academy_payments import register_payments
else:
    from modules.academy import register_courses
    from modules.academy_media import register_media
    from modules.academy_payments import register_payments
academy_service = register_courses(app, samtm_platform)
academy_media_service = register_media(app, academy_service)
academy_payment_service = register_payments(app, academy_service)
app.router.add_event_handler("startup", academy_service.migrate)
app.router.add_event_handler("startup", academy_media_service.migrate)
app.router.add_event_handler("startup", academy_payment_service.migrate)
# REV160: Click SHOP-API — pulli kursga avtomatik to'lov (kalitlar faqat Railway Variables'da)
if __package__:
    from .modules.click_tolov import register_click
else:
    from modules.click_tolov import register_click
click_service = register_click(app, academy_service, academy_payment_service)
app.router.add_event_handler("startup", click_service.migrate)
# REV161: Payme Merchant API — o'sha buyurtma kodi bilan (kalitlar faqat Railway Variables'da)
if __package__:
    from .modules.payme_tolov import register_payme
else:
    from modules.payme_tolov import register_payme
payme_service = register_payme(app, academy_service, academy_payment_service, click_service)
app.router.add_event_handler("startup", payme_service.migrate)
# REV162: bog'cha — aqlli haftalik reja, tariflar (narx qulfi), ota-ona obunasi va rozilik (Click/Payme bilan)
try:
    if __package__:
        from .modules.bogcha_reja import create_router as create_bogcha_reja_router
    else:
        from modules.bogcha_reja import create_router as create_bogcha_reja_router
    app.include_router(create_bogcha_reja_router(samtm_platform, click_service))
except Exception as _bogcha_xato:   # pragma: no cover — bo'lim ishlamasa ham server to'xtamaydi
    print(f"[STARTUP-WARNING] bogcha_reja yuklanmadi: {_bogcha_xato!r}", flush=True)

# REV49: private presentation projects and a configurable slide designer.
if __package__:
    from .modules.presentations import register_presentations
else:
    from modules.presentations import register_presentations
presentation_service = register_presentations(app, samtm_platform)
app.router.add_event_handler("startup", presentation_service.migrate)

# Curriculum audience migration runs after the legacy/runtime schema migrations.
if __package__:
    from .modules.curriculum_api import create_router as create_curriculum_router
    from .modules.curriculum_scope import migrate as migrate_curriculum
else:
    from modules.curriculum_api import create_router as create_curriculum_router
    from modules.curriculum_scope import migrate as migrate_curriculum
app.include_router(create_curriculum_router(samtm_platform))
app.router.add_event_handler("startup", lambda: migrate_curriculum(samtm_platform._db))

if __package__:
    from .modules.admin_speech import create_router as create_admin_speech_router
else:
    from modules.admin_speech import create_router as create_admin_speech_router
app.include_router(create_admin_speech_router(samtm_platform))
# REV96: o'qituvchilar uchun ham ovoz ⇄ matn (/api/speech/...).
if __package__:
    from .modules.admin_speech import create_teacher_router as create_teacher_speech_router
else:
    from modules.admin_speech import create_teacher_router as create_teacher_speech_router
app.include_router(create_teacher_speech_router(samtm_platform))
# REV96: to'garak/repetitor jurnali — davomat va to'lovlar (bot bilan bir xil jadvallar).
if __package__:
    from .modules.togarak_jurnal import create_router as create_togarak_jurnal_router
else:
    from modules.togarak_jurnal import create_router as create_togarak_jurnal_router
app.include_router(create_togarak_jurnal_router(samtm_platform))
# REV97: bog'cha yosh guruhlari 2-3/4-5/6-7 — bir martalik tozalash va admin «Miya tarkibi».
if __package__:
    from .modules.miya_tarkibi import create_router as create_miya_tarkibi_router
else:
    from modules.miya_tarkibi import create_router as create_miya_tarkibi_router
app.include_router(create_miya_tarkibi_router(samtm_platform))

# Dars xonasi: nashr qilingan AI miya kontentidan doskadagi dars.
if __package__:
    from .modules.dars_xonasi import create_router as create_dars_xonasi_router
else:
    from modules.dars_xonasi import create_router as create_dars_xonasi_router
app.include_router(create_dars_xonasi_router(samtm_platform))
app.router.add_event_handler("startup", samtm_platform._ai_brain_dars_migratsiya)

# Display-only translations; server credentials never reach the frontend.
if __package__:
    from .modules.translation_api import create_router as create_translation_router
else:
    from modules.translation_api import create_router as create_translation_router
app.include_router(create_translation_router(samtm_platform))

# REV79: institut hayoti — admin uchun kurs → guruh → talaba, muhim sanalar; talaba uchun «Mening institutim».
if __package__:
    from .modules.institut_hayoti import create_router as create_institut_hayoti_router
else:
    from modules.institut_hayoti import create_router as create_institut_hayoti_router
app.include_router(create_institut_hayoti_router(samtm_platform))

# REV82: onlayn bellashuv — o'quvchi va talabalar o'zaro test bellashuvi.
if __package__:
    from .modules.bellashuv import create_router as create_bellashuv_router
else:
    from modules.bellashuv import create_router as create_bellashuv_router
app.include_router(create_bellashuv_router(samtm_platform))
# REV143: bolalar ligasi — chempionatlar (jamoaviy/yakka, guruh + pley-off, kuboklar).
# REV146: chempionat moduli ishga tushmasa ham butun server to'xtamaydi (faqat chempionat bo'limi o'chadi).
try:
    if __package__:
        from .modules.chempionat import create_router as create_chempionat_router
    else:
        from modules.chempionat import create_router as create_chempionat_router
    app.include_router(create_chempionat_router(samtm_platform))
except Exception as _chemp_xato:   # pragma: no cover
    print(f"[STARTUP-WARNING] chempionat yuklanmadi: {_chemp_xato!r}", flush=True)
# REV83: shashka — bot (4 daraja), onlayn raqib izlash, do'st bilan kod orqali.
if __package__:
    from .modules.shashka import create_router as create_shashka_router
else:
    from modules.shashka import create_router as create_shashka_router
app.include_router(create_shashka_router(samtm_platform))
# REV86: shaxmat maktabi (o'rgatish) — /api/shaxmat/maktab shaxmat o'yin yo'lidan (/api/shaxmat/{kod}) OLDIN ulanadi.
if __package__:
    from .modules.shaxmat_maktab import create_router as create_shaxmat_maktab_router
else:
    from modules.shaxmat_maktab import create_router as create_shaxmat_maktab_router
app.include_router(create_shaxmat_maktab_router(samtm_platform))
# REV85: shaxmat — to'liq qoidalar, 4 darajali bot, onlayn reyting, do'st bilan.
if __package__:
    from .modules.shaxmat import create_router as create_shaxmat_router
else:
    from modules.shaxmat import create_router as create_shaxmat_router
app.include_router(create_shaxmat_router(samtm_platform))
# REV91: bog'cha — kunlik dars rejasi (2 ta, dam olish kuni 3 ta) va ota-onaga jonli hisobot.
if __package__:
    from .modules.bola_kuzatuv import create_router as create_bola_kuzatuv_router
else:
    from modules.bola_kuzatuv import create_router as create_bola_kuzatuv_router
app.include_router(create_bola_kuzatuv_router(samtm_platform))
# REV173: maktab (1–11) til o'yinlari — ball, daraja (CEFR) va sinfdoshlar orasida o'rin.
if __package__:
    from .modules.maktab_natija import create_router as create_maktab_natija_router
else:
    from modules.maktab_natija import create_router as create_maktab_natija_router
app.include_router(create_maktab_natija_router(samtm_platform))
# REV174: maktab o'quvchisi faolligi va ota-ona: bugun/hafta, «O'zim sinayman», «Mashq ber».
if __package__:
    from .modules.maktab_ota import create_router as create_maktab_ota_router
else:
    from modules.maktab_ota import create_router as create_maktab_ota_router
app.include_router(create_maktab_ota_router(samtm_platform))
# REV106: o'qituvchi kirishda o'z fanlarini tanlaydi — faqat shu fanlar mavzulari, AI darslari va testlari.
if __package__:
    from .modules.teacher_subjects import create_router as create_teacher_subjects_router
else:
    from modules.teacher_subjects import create_router as create_teacher_subjects_router
app.include_router(create_teacher_subjects_router(samtm_platform))

# REV107: kutilmagan server xatosi ham JSON bo'lib, CORS sarlavhasi bilan qaytadi. Ilgari bunday javobda
# brauzer CORS sababli javobni o'qiy olmasdi va foydalanuvchi «Serverga ulanib bo'lmadi» degan noto'g'ri
# xabarni ko'rardi. Endi xato kodi chiqadi va Railway logida shu kod bilan to'liq sabab yoziladi.
import secrets as _rev107_secrets
import traceback as _rev107_traceback
from fastapi.responses import JSONResponse as _Rev107Json


@app.middleware("http")
async def _rev107_kutilmagan_xato(request, call_next):
    try:
        return await call_next(request)
    except Exception:
        error_id = _rev107_secrets.token_hex(4)
        print(f"[SERVER-XATO {error_id}] {request.method} {request.url.path}\n{_rev107_traceback.format_exc()}", flush=True)
        response = _Rev107Json(status_code=500, content={"detail": (
            f"Serverda kutilmagan xato (kod {error_id}). Bir daqiqadan keyin qayta urinib ko‘ring; "
            f"takrorlansa shu kodni administratorga yuboring.")})
        origin = (request.headers.get("origin") or "").rstrip("/")
        if origin and origin in samtm_platform.FRONTEND_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        return response


# REV146: ishga tushish (startup) bosqichidagi bitta modul xatosi (masalan, deploy paytida jadval qulfi
# bo'shamadi — LockNotAvailable) butun serverni yiqitmasin: xato logga yoziladi, server ishga tushadi,
# o'sha modul keyingi so'rovda yoki keyingi deployda o'z jadvalini qayta tekshiradi.
def _rev146_xavfsiz_startup(handler):
    import functools
    import inspect as _inspect

    nom = f"{getattr(handler, '__module__', '?')}.{getattr(handler, '__qualname__', '?')}"
    if _inspect.iscoroutinefunction(handler):
        @functools.wraps(handler)
        async def _async_wrap():
            try:
                return await handler()
            except Exception as exc:   # pragma: no cover — faqat deploy paytidagi kutilmagan holat
                print(f"[STARTUP-WARNING] {nom} o'tkazib yuborildi: {exc!r}", flush=True)
        return _async_wrap

    @functools.wraps(handler)
    def _wrap():
        try:
            return handler()
        except Exception as exc:   # pragma: no cover
            print(f"[STARTUP-WARNING] {nom} o'tkazib yuborildi: {exc!r}", flush=True)
    return _wrap


try:
    _rev146_startup = getattr(app.router, "on_startup", None)
    if isinstance(_rev146_startup, list):
        _rev146_startup[:] = [_rev146_xavfsiz_startup(h) for h in _rev146_startup]
except Exception as _rev146_exc:   # pragma: no cover
    print(f"[STARTUP-WARNING] startup himoyasi o'rnatilmadi: {_rev146_exc!r}", flush=True)


# REV147: asosiy sayt manziliga yo'naltirish. Ilova boshqa (ruxsat etilmagan) manzildan ochilsa, brauzer
# CORS sababli serverga so'rov yubora olmaydi — sahifa shu manzil orqali to'g'ri saytga o'tadi.
from fastapi.responses import RedirectResponse as _Rev147Redirect


@app.get("/auth/sayt", include_in_schema=False)
def _rev147_asosiy_sayt():
    return _Rev147Redirect(str(samtm_platform.FRONTEND_URL).rstrip("/") + "/", status_code=302)


# REV147: /auth/config — ochiq ma'lumot (kirish usullari va asosiy sayt manzili). Har qanday manzil o'qiy oladi
# (cookie'siz), shunda noto'g'ri manzildan ochilgan ilova buni aniqlab, asosiy saytga o'zi o'tadi.
@app.middleware("http")
async def _rev147_ochiq_config(request, call_next):
    response = await call_next(request)
    if request.url.path == "/auth/config" and "access-control-allow-origin" not in response.headers:
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
# REV152 (xavfsizlik): 1) so'rov hajmi chegarasi — katta fayl bilan serverni qotirib bo'lmaydi;
# 2) qo'shilish kodlari (4 xonali sinf/guruh paroli, farzand kodi, kirish kodi) — taxmin qilib topishga
#    urinishlar soni cheklanadi; 3) API hujjatlari (/docs) ishlab turgan saytda yopiq.
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════
import hashlib as _rev152_hash
from fastapi.responses import JSONResponse as _Rev152Json
from starlette.concurrency import run_in_threadpool as _rev152_thread
from platform_core import limitlar as _rev152_limit

_REV152_KATTA = ("/api/admin/", "/api/kurslar/")              # admin paketlari va kurs videolari (o'z chegarasi bor)
_REV152_KOD_YOLLARI = (
    "/api/oquvchi/sinfga_qoshil", "/api/talaba/guruhga_qoshil", "/api/talaba/muassasa_tekshir",
    "/api/togarakka_qoshil", "/api/ota/farzand_boglash", "/api/oqituvchi/kirish_kodi_orqali_qoshil",
    "/kirish_kodi_qabul", "/api/auth/telefon_kod_tasdiqla", "/api/rol_kod_tasdiqla", "/api/bellashuv/qoshil",
    "/auth/ism_tekshir",
)


def _rev152_kod_yolimi(path: str) -> bool:
    return any(path == p or path.endswith(p) for p in _REV152_KOD_YOLLARI)


@app.middleware("http")
async def _rev152_himoya(request, call_next):
    path = request.url.path
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            hajm = int(request.headers.get("content-length") or 0)
        except ValueError:
            hajm = 0
        chegara = (520 if path.startswith(_REV152_KATTA) else _rev152_limit.son("SOROV_MAX_MB", 45)) * 1024 * 1024
        if hajm > chegara:
            return _Rev152Json({"detail": f"So‘rov juda katta (eng ko‘pi {chegara // (1024 * 1024)} MB)"}, status_code=413)
    if _rev152_kod_yolimi(path):
        ip = _rev152_limit.ip_of(request)
        tok = request.query_params.get("token") or request.headers.get("authorization") or ""
        kim = _rev152_hash.sha256(tok.encode()).hexdigest()[:24] if tok else "anon:" + ip
        try:
            await _rev152_thread(_rev152_limit.sarfla, "kod:user", f"{path}|{kim}", 1,
                                 _rev152_limit.son("KOD_URINISH_15DAQ", 10), 900,
                                 "Juda ko‘p urinish. 15 daqiqadan keyin qayta urinib ko‘ring.")
            await _rev152_thread(_rev152_limit.sarfla, "kod:ip", ip, 1,
                                 _rev152_limit.son("KOD_IP_15DAQ", 60), 900,
                                 "Bu tarmoqdan juda ko‘p urinish. 15 daqiqadan keyin qayta urinib ko‘ring.")
        except Exception as exc:   # 429
            status = getattr(exc, "status_code", 429)
            return _Rev152Json({"detail": getattr(exc, "detail", "Juda ko‘p urinish")}, status_code=status,
                               headers=getattr(exc, "headers", None) or {})
    return await call_next(request)


# API hujjatlari — faqat ishlab chiqishda (Railway'da yopiq): butun API xaritasi begonalarga ko'rinmasin.
if (__import__("os").getenv("RAILWAY_ENVIRONMENT") or __import__("os").getenv("RAILWAY_PROJECT_ID")) \
        and __import__("os").getenv("API_DOCS_OCHIQ", "") != "1":
    try:
        app.docs_url = None
        app.redoc_url = None
        app.openapi_url = None
        app.router.routes[:] = [r for r in app.router.routes
                                if getattr(r, "path", None) not in ("/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect")]
    except Exception as _rev152_exc:   # pragma: no cover
        print(f"[XAVFSIZLIK] /docs yopilmadi: {_rev152_exc!r}", flush=True)
