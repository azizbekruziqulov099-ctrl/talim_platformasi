"""REV152: pullik xizmatlar (ovoz, AI, ovozni matnga) va taxmin qilinadigan kodlar uchun cheklovlar.

Hisoblagich bazada saqlanadi (hamma worker uchun bitta). Baza vaqtincha javob bermasa — shu worker xotirasidagi
zaxira hisoblagich ishlaydi (sayt to'xtab qolmaydi, cheklov baribir ishlaydi).

sarfla(scope, subject, weight, limit, seconds) — oyna ichida jami `weight` `limit` dan oshsa 429 beradi.
"""
from __future__ import annotations

import hashlib
import os
import threading
import time

from fastapi import HTTPException

from platform_core.ddl_guard import LazyMigration

_JADVAL = LazyMigration("xavfsizlik_limit", backoff=30)
_XOTIRA: dict[str, tuple[float, int]] = {}
_QULF = threading.Lock()
_DB_FACTORY = None


def ulash(db_factory) -> None:
    """samtm_platform._db ni beradi (ishga tushishda bir marta)."""
    global _DB_FACTORY
    _DB_FACTORY = db_factory


def _kalit(scope: str, subject: str) -> str:
    return hashlib.sha256(f"{scope}\0{subject}".encode("utf-8")).hexdigest()


def _jadval_yarat(cur) -> None:
    cur.execute("""CREATE TABLE IF NOT EXISTS xavfsizlik_limit(
        bucket TEXT PRIMARY KEY, window_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), hits BIGINT NOT NULL DEFAULT 0)""")


def _xotirada(bucket: str, weight: int, seconds: int) -> int:
    now = time.monotonic()
    with _QULF:
        start, hits = _XOTIRA.get(bucket, (now, 0))
        if now - start > seconds:
            start, hits = now, 0
        hits += weight
        _XOTIRA[bucket] = (start, hits)
        if len(_XOTIRA) > 20000:   # eski yozuvlarni tozalash
            for k in list(_XOTIRA)[:5000]:
                _XOTIRA.pop(k, None)
        return hits


def hisobla(scope: str, subject: str, weight: int = 1, seconds: int = 60) -> int:
    """Oyna ichidagi jami (shu so'rov bilan). Xato bo'lsa — xotiradagi zaxira."""
    bucket = _kalit(scope, str(subject))
    weight = max(1, int(weight))
    if _DB_FACTORY is not None:
        conn = None
        try:
            conn = _DB_FACTORY()
            cur = conn.cursor()
            _JADVAL.run(conn, cur, _jadval_yarat)
            cur.execute("""INSERT INTO xavfsizlik_limit(bucket,window_at,hits) VALUES(%s,NOW(),%s)
                ON CONFLICT(bucket) DO UPDATE SET
                hits=CASE WHEN xavfsizlik_limit.window_at < NOW()-(%s*INTERVAL '1 second') THEN EXCLUDED.hits
                          ELSE xavfsizlik_limit.hits+EXCLUDED.hits END,
                window_at=CASE WHEN xavfsizlik_limit.window_at < NOW()-(%s*INTERVAL '1 second') THEN NOW()
                          ELSE xavfsizlik_limit.window_at END
                RETURNING hits""", (bucket, weight, seconds, seconds))
            row = cur.fetchone()
            conn.commit()
            cur.close()
            return int(row["hits"] if isinstance(row, dict) else row[0])
        except Exception:   # baza band (503) yoki xato — xotiradagi zaxira hisoblagich
            try:
                conn and conn.rollback()
            except Exception:
                pass
        finally:
            try:
                conn and conn.close()
            except Exception:
                pass
    return _xotirada(bucket, weight, seconds)


def sarfla(scope: str, subject, weight: int, limit: int, seconds: int, xabar: str = "") -> int:
    hits = hisobla(scope, str(subject), weight, seconds)
    if hits > limit:
        raise HTTPException(
            status_code=429,
            detail=xabar or "So‘rovlar juda ko‘p. Birozdan keyin qayta urinib ko‘ring.",
            headers={"Retry-After": str(min(seconds, 3600))},
        )
    return hits


def son(nom: str, default: int) -> int:
    """Muhit o'zgaruvchisidan butun son (Railway Variables orqali o'zgartirish mumkin)."""
    try:
        v = int(str(os.getenv(nom, "")).strip() or default)
        return v if v > 0 else default
    except ValueError:
        return default


def ip_of(request) -> str:
    """Mijoz IP manzili (kabutar_auth.AuthService.ip bilan bir xil qoida)."""
    try:
        return _ip_of(request)
    except Exception:
        return "unknown"


def _ip_of(request) -> str:
    if os.getenv("KABUTAR_TRUST_PROXY_HEADERS", "").lower() == "true":
        value = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if value:
            return value[:100]
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_ID"):
        value = (request.headers.get("x-real-ip") or "").strip()
        if value:
            return value[:100]
    return request.client.host if getattr(request, "client", None) else "unknown"
