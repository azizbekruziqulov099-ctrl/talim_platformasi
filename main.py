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
