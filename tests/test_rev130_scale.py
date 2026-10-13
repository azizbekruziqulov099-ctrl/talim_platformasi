"""REV130: ko'p foydalanuvchi uchun — sessiya keshi, gunicorn sozlamasi, og'ir yo'llar."""
import importlib
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_session_cache_hit_expiry_and_forget(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    auth = importlib.import_module("kabutar_auth")
    monkeypatch.setattr(auth, "SESSION_CACHE_TTL", 20.0)
    auth._SESSION_CACHE.clear()
    assert not auth.session_cache_get("h1", 7)
    auth.session_cache_put("h1", 7)
    auth.session_cache_put("h2", 7)
    auth.session_cache_put("h3", 8)
    assert auth.session_cache_get("h1", 7)
    assert not auth.session_cache_get("h1", 8)          # boshqa foydalanuvchi — kesh ishlamaydi
    auth.forget_sessions(session_hash="h1")
    assert not auth.session_cache_get("h1", 7)
    auth.forget_sessions(user_id=7)                      # chiqish «hamma qurilmalarda»
    assert not auth.session_cache_get("h2", 7)
    assert auth.session_cache_get("h3", 8)
    monkeypatch.setattr(auth, "SESSION_CACHE_TTL", 0.0)  # o'chirib qo'yish mumkin
    assert not auth.session_cache_get("h3", 8)
    auth._SESSION_CACHE.clear()


def test_gunicorn_defaults_fit_postgres_connection_limit(monkeypatch):
    monkeypatch.delenv("WEB_CONCURRENCY", raising=False)
    monkeypatch.delenv("ACCESS_LOG", raising=False)
    spec = importlib.util.spec_from_file_location("rev130_gunicorn", ROOT / "gunicorn_conf.py")
    conf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(conf)
    assert 2 <= conf.workers <= 4
    assert conf.workers * 2 * 10 <= 100                  # 2 ta pul × DB_POOL_MAX=10
    assert conf.accesslog is None                         # har so'rov logi standart holatda o'chiq


def test_heavy_paths_include_document_exports():
    src = (ROOT / "samtm_runtime.py").read_text(encoding="utf-8")
    assert '"/yuklab", "/export"' in src


def test_no_per_request_alter_table_in_hot_endpoints():
    src = (ROOT / "samtm_platform.py").read_text(encoding="utf-8")
    start = src.index('@app.get("/api/auth/muassasalarim")')
    body = src[start:start + 1500]
    assert "execute(\"ALTER TABLE" not in body
    prof = src[src.index("def _ai_foydalanuvchi_profili"):][:400]
    assert "execute(\"ALTER TABLE" not in prof
