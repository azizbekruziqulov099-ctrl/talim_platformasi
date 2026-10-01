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
