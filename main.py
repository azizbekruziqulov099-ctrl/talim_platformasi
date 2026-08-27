"""SamTM V20 ASGI entry point — REV60 maktab ID va ko'p maktab tuzatishi.

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
    raise RuntimeError(
        "V19.8 majburiy API route'lari ro'yxatdan o'tmadi: "
        + ", ".join(missing_required_routes)
    )

# /api/versiya samtm_platform modulidagi global qiymatlarni o'qiydi.
samtm_platform.SAMTM_RELEASE = SAMTM_PLATFORM_RELEASE
samtm_platform.SAMTM_PACKAGE_REVISION = (
    "school-id-existing-schools-single-html-rev60"
)

register_runtime(app, samtm_platform, samtm_school)
app.version = "20.0"
app.state.samtm_release = SAMTM_PLATFORM_RELEASE
app.state.teacher_first_load_enabled = True
app.state.smart_swap_enabled = True
app.state.v17_school_workspace_link_enabled = True
