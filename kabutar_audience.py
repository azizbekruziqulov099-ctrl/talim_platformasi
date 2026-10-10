"""REV31 authenticated audience counters; no URLs, IPs or message content.

Online means an authenticated foreground tab sent a heartbeat in the last
180 seconds. This is an estimate, not an exact count of live sockets. Daily
figures start at installation and use Asia/Tashkent calendar days. Historical
login counts are not inferred from existing accounts.

Integration: register_audience(app, platform) once after platform is imported.
The auth issuer may call platform._kabutar_record_login(user_id, method) once
AFTER its successful transaction. Metrics errors must never undo a login.
"""

from collections import OrderedDict
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from threading import Lock
from time import monotonic
from typing import Any

ONLINE_SECONDS = 180
HEARTBEAT_SECONDS = 60
METRICS_CACHE_SECONDS = 10
REGISTERED_CACHE_SECONDS = 60
TIMEZONE = "Asia/Tashkent"
LOGIN_METHODS = frozenset({"telegram", "google", "password"})

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS kabutar_audience_meta (
  singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
  measurement_started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO kabutar_audience_meta(singleton) VALUES(TRUE)
ON CONFLICT(singleton) DO NOTHING;
CREATE TABLE IF NOT EXISTS kabutar_audience_presence (
  user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  last_seen_at TIMESTAMPTZ NOT NULL,
  active_day DATE NOT NULL,
  day_changed BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS kabutar_audience_presence_seen_idx
  ON kabutar_audience_presence(last_seen_at DESC);
CREATE TABLE IF NOT EXISTS kabutar_audience_daily (
  day DATE PRIMARY KEY,
  active_users BIGINT NOT NULL DEFAULT 0 CHECK(active_users >= 0),
  logins BIGINT NOT NULL DEFAULT 0 CHECK(logins >= 0)
);
"""

TOUCH_SQL = """
INSERT INTO kabutar_audience_presence(user_id,last_seen_at,active_day,day_changed)
VALUES(%s,CURRENT_TIMESTAMP,(CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Tashkent')::date,TRUE)
ON CONFLICT(user_id) DO UPDATE SET
 last_seen_at=EXCLUDED.last_seen_at,
 day_changed=(kabutar_audience_presence.active_day <> EXCLUDED.active_day),
 active_day=EXCLUDED.active_day
WHERE kabutar_audience_presence.last_seen_at <= CURRENT_TIMESTAMP - INTERVAL '60 seconds'
   OR kabutar_audience_presence.active_day <> EXCLUDED.active_day
RETURNING day_changed,active_day
"""

COUNT_DAY_SQL = """
INSERT INTO kabutar_audience_daily(day,active_users,logins)
VALUES((CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Tashkent')::date,%s,%s)
ON CONFLICT(day) DO UPDATE SET
 active_users=kabutar_audience_daily.active_users + EXCLUDED.active_users,
 logins=kabutar_audience_daily.logins + EXCLUDED.logins
"""


def _bearer_token(authorization: str | None) -> str:
    # Deliberately do not support tokens in URLs or request-body user IDs.
    from fastapi import HTTPException
    scheme, _, token = str(authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Kabutar akkauntiga qayta kiring")
    return token.strip()


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _daily_series(rows: list[dict], today: date, days: int, started_at: datetime | None) -> list[dict]:
    """No fake history before instrumentation started; fill measured zero days."""
    local_zone = timezone(timedelta(hours=5))
    first = today - timedelta(days=days - 1)
    if started_at is not None:
        # psycopg supplies aware timestamps; the fallback makes tests/old DB
        # adapters deterministic without using the machine's local timezone.
        aware = started_at if started_at.tzinfo else started_at.replace(tzinfo=timezone.utc)
        first = max(first, aware.astimezone(local_zone).date())
    existing = {str(row["day"]): row for row in rows}
    result = []
    for offset in range(max(0, (today - first).days + 1)):
        key = (first + timedelta(days=offset)).isoformat()
        row = existing.get(key, {})
        result.append({"date": key, "active_users": int(row.get("active_users", 0)),
                       "logins": int(row.get("logins", 0))})
    return result


class _HeartbeatThrottle:
    """Bounded per-worker optimization; PostgreSQL enforces cross-worker writes."""
    def __init__(self, size: int = 10000):
        self.size = size
        self.seen: OrderedDict[int, float] = OrderedDict()
        self.lock = Lock()

    def recent(self, user_id: int, now: float) -> bool:
        with self.lock:
            previous = self.seen.get(user_id)
            return previous is not None and now - previous < HEARTBEAT_SECONDS

    def mark(self, user_id: int, now: float) -> None:
        with self.lock:
            self.seen[user_id] = now
            self.seen.move_to_end(user_id)
            while len(self.seen) > self.size:
                self.seen.popitem(last=False)


class AudienceService:
    def __init__(self, platform: Any):
        self.platform = platform
        self.throttle = _HeartbeatThrottle()
        self._cache: dict[int, tuple[float, dict]] = {}
        self._cache_lock = Lock()
        self._registered: tuple[float, int] | None = None
        self._cleanup_at = 0.0
        self._cleanup_lock = Lock()

    @contextmanager
    def database(self):
        conn = self.platform._db()
        cur = None
        try:
            cur = conn.cursor()
            # This bound is transaction-local and does not leak into the pool.
            cur.execute("SET LOCAL statement_timeout = '5000ms'")
            cur.execute("SET LOCAL lock_timeout = '1500ms'")
            yield conn, cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def initialize(self) -> None:
        with self.database() as (_, cur):
            cur.execute(SCHEMA_SQL)

    def touch(self, user_id: int, *, login: bool = False) -> bool:
        now = monotonic()
        if not login and self.throttle.recent(user_id, now):
            return False
        with self.database() as (_, cur):
            cur.execute(TOUCH_SQL, (user_id,))
            row = cur.fetchone()
            changed = bool(row and row.get("day_changed"))
            if changed or login:
                cur.execute(COUNT_DAY_SQL, (int(changed), int(login)))
        self.throttle.mark(user_id, now)
        return bool(row)

    def record_login(self, user_id: int, method: str) -> None:
        # Legacy token migration, token refresh and account linking are not
        # fresh logins. The issuer explicitly names the successful method.
        if method in LOGIN_METHODS:
            self.touch(int(user_id), login=True)

    def cleanup(self) -> None:
        """Bounded cleanup, at most every 5 minutes per worker on admin reads.

        Online account-level rows expire after 31 inactive days. The small
        aggregate-only daily history expires after 90 days. No login-event or
        per-user daily history table is retained.
        """
        now = monotonic()
        if now < self._cleanup_at or not self._cleanup_lock.acquire(blocking=False):
            return
        try:
            if now < self._cleanup_at:
                return
            with self.database() as (_, cur):
                cur.execute("""DELETE FROM kabutar_audience_presence WHERE user_id IN (
                  SELECT user_id FROM kabutar_audience_presence
                  WHERE last_seen_at < CURRENT_TIMESTAMP - INTERVAL '31 days'
                  ORDER BY last_seen_at LIMIT 1000
                )""")
                cur.execute("""DELETE FROM kabutar_audience_daily
                  WHERE day < (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Tashkent')::date - 90""")
            self._cleanup_at = now + 300
        finally:
            self._cleanup_lock.release()

    def snapshot(self, days: int) -> dict:
        # Route validates 1..30; this also makes direct callers safe.
        if not 1 <= days <= 30:
            raise ValueError("days must be between 1 and 30")
        now = monotonic()
        with self._cache_lock:
            cached = self._cache.get(days)
            if cached is not None and now - cached[0] < METRICS_CACHE_SECONDS:
                return cached[1]
            with self.database() as (_, cur):
                cur.execute("""SELECT CURRENT_TIMESTAMP AS measured_at,
                  (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Tashkent')::date AS today,
                  measurement_started_at FROM kabutar_audience_meta WHERE singleton=TRUE""")
                meta = cur.fetchone()
                if self._registered is None or now - self._registered[0] >= REGISTERED_CACHE_SECONDS:
                    cur.execute("SELECT COUNT(*) AS total FROM users")
                    registered = int(cur.fetchone()["total"])
                else:
                    registered = self._registered[1]
                cur.execute("""SELECT COUNT(*) AS total FROM kabutar_audience_presence
                  WHERE last_seen_at > CURRENT_TIMESTAMP - INTERVAL '180 seconds'""")
                online_count = int(cur.fetchone()["total"])
                cur.execute("""SELECT p.user_id,u.full_name,p.last_seen_at
                  FROM kabutar_audience_presence p JOIN users u ON u.user_id=p.user_id
                  WHERE p.last_seen_at > CURRENT_TIMESTAMP - INTERVAL '180 seconds'
                  ORDER BY p.last_seen_at DESC,p.user_id LIMIT 30""")
                online = [{"user_id": str(row["user_id"]), "full_name": row.get("full_name") or "Kabutar foydalanuvchisi",
                           "last_seen_at": _iso(row["last_seen_at"])} for row in cur.fetchall()]
                cur.execute("""SELECT day,active_users,logins FROM kabutar_audience_daily
                  WHERE day >= (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Tashkent')::date - %s
                  ORDER BY day""", (days - 1,))
                rows = cur.fetchall()
            self._registered = (now, registered) if self._registered is None or now - self._registered[0] >= REGISTERED_CACHE_SECONDS else self._registered
            today_row = next((row for row in rows if row["day"] == meta["today"]), {})
            value = {
                "summary": {"registered_users": registered, "online_users": online_count,
                            "active_today": int(today_row.get("active_users", 0)),
                            "logins_today": int(today_row.get("logins", 0))},
                "daily": _daily_series(rows, meta["today"], days, meta["measurement_started_at"]),
                "online": online,
                "online_list_limit": 30,
                "online_window_seconds": ONLINE_SECONDS,
                "heartbeat_seconds": HEARTBEAT_SECONDS,
                "timezone": TIMEZONE,
                "measurement_started_at": _iso(meta["measurement_started_at"]),
                "measured_at": _iso(meta["measured_at"]),
                "registered_count_cache_seconds": REGISTERED_CACHE_SECONDS,
                "history_note": "Hisob ushbu yangilanish o'rnatilgan vaqtdan boshlanadi. Onlayn — oxirgi 3 daqiqada faol bo'lgan akkauntlar.",
            }
            self._cache[days] = (now, value)
        # Cleanup is maintenance only; failure must not prevent viewing counts.
        try:
            self.cleanup()
        except Exception:
            pass
        return value


def register_audience(app: Any, platform: Any) -> AudienceService:
    """Register once; resolves current auth functions at request time."""
    from fastapi import Header, HTTPException, Query, Response
    if getattr(app.state, "kabutar_audience", None) is not None:
        return app.state.kabutar_audience
    service = AudienceService(platform)
    app.state.kabutar_audience = service
    platform._kabutar_record_login = service.record_login
    app.router.add_event_handler("startup", service.initialize)

    @app.post("/api/presence", tags=["Kabutar"])
    def presence(authorization: str | None = Header(default=None)):
        user_id = int(platform._jwt_tekshir(_bearer_token(authorization)))
        try:
            updated = service.touch(user_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Faollik hisobini hozir yangilab bo'lmadi") from exc
        return {"ok": True, "updated": updated,
                "heartbeat_seconds": HEARTBEAT_SECONDS, "online_window_seconds": ONLINE_SECONDS}

    @app.get("/api/admin/audience", tags=["Kabutar admin"])
    def audience(response: Response, days: int = Query(default=30, ge=1, le=30),
                 authorization: str | None = Header(default=None)):
        platform._admin_tekshir(_bearer_token(authorization))
        response.headers["Cache-Control"] = "private, no-store"
        try:
            return service.snapshot(int(days))
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Faollik hisoboti hozir tayyor emas. Qayta urinib ko'ring") from exc

    return service
