"""SamTM V19.2 ASGI entry point.

Run locally: uvicorn main:app --host 0.0.0.0 --port 8080
Production: gunicorn main:app -c gunicorn_conf.py
"""
SAMTM_ASGI_RELEASE = "samtm-teacher-first-smart-timetable-v19.2"

try:
    from . import samtm_platform, samtm_school
    from .samtm_platform import app
    from .samtm_runtime import register_runtime
except ImportError:
    import samtm_platform, samtm_school
    from samtm_platform import app
    from samtm_runtime import register_runtime

register_runtime(app, samtm_platform, samtm_school)
app.state.samtm_release = SAMTM_ASGI_RELEASE
app.state.teacher_first_load_enabled = True
app.state.smart_swap_enabled = True
