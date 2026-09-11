"""REV45: authorized two-person WebRTC signaling, shared by all workers.

Only SDP/ICE metadata uses PostgreSQL. Audio/video never crosses this API.
TURN REST credentials are short-lived; group meetings require a private JWT
Jitsi deployment with anonymous guests disabled. No public-room fallback.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import base64
import hashlib
import hmac
import json
import os
import re
import threading
import time
import uuid
from urllib.parse import urlsplit

if __package__ and "." in __package__:
    from ..kabutar_policy import allow_direct, require_direct, require_group, memberships, ensure_terms_accepted
else:
    from kabutar_policy import allow_direct, require_direct, require_group, memberships, ensure_terms_accepted

SCHEMA = """
CREATE TABLE IF NOT EXISTS kabutar_calls_v45 (
 id TEXT PRIMARY KEY, caller_id BIGINT NOT NULL REFERENCES users(user_id),
 callee_id BIGINT NOT NULL REFERENCES users(user_id), mode TEXT NOT NULL,
 state TEXT NOT NULL DEFAULT 'ringing', request_id TEXT NOT NULL,
 offer JSONB, answer JSONB, reason TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 expires_at TIMESTAMPTZ NOT NULL DEFAULT NOW() + INTERVAL '90 seconds',
 caller_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), callee_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 CHECK(caller_id <> callee_id), CHECK(mode IN ('audio','video')),
 CHECK(state IN ('ringing','active','ended')), UNIQUE(caller_id,request_id)
);
CREATE INDEX IF NOT EXISTS kabutar_calls_v45_callee ON kabutar_calls_v45(callee_id,expires_at DESC);
CREATE INDEX IF NOT EXISTS kabutar_calls_v45_caller ON kabutar_calls_v45(caller_id,expires_at DESC);
CREATE INDEX IF NOT EXISTS kabutar_calls_v45_expiry ON kabutar_calls_v45(expires_at);
CREATE TABLE IF NOT EXISTS kabutar_call_ice_v45 (
 seq BIGSERIAL PRIMARY KEY, call_id TEXT NOT NULL REFERENCES kabutar_calls_v45(id) ON DELETE CASCADE,
 sender_id BIGINT NOT NULL, request_id TEXT NOT NULL, candidate JSONB NOT NULL,
 UNIQUE(call_id,sender_id,request_id)
);
CREATE INDEX IF NOT EXISTS kabutar_call_ice_v45_call ON kabutar_call_ice_v45(call_id,seq);
CREATE TABLE IF NOT EXISTS kabutar_call_budget_v45 (
 user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
 minute TIMESTAMPTZ NOT NULL, used INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS kabutar_call_cleanup_v45 (
 singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK(singleton), last_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
INSERT INTO kabutar_call_cleanup_v45(singleton) VALUES(TRUE) ON CONFLICT DO NOTHING;
"""


def fail(status, message):
    from fastapi import HTTPException
    raise HTTPException(status_code=status, detail=message)


def as_id(value):
    if isinstance(value, bool):
        fail(422, "Foydalanuvchi raqami noto‘g‘ri")
    try:
        result = int(value)
    except (TypeError, ValueError):
        fail(422, "Foydalanuvchi raqami noto‘g‘ri")
    if result <= 0 or result > 9223372036854775807 or str(result) != str(value):
        fail(422, "Foydalanuvchi raqami noto‘g‘ri")
    return result


def request_key(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{8,80}", value):
        fail(422, "So‘rov kaliti noto‘g‘ri")
    return value


def description(value, kind):
    if not isinstance(value, dict) or set(value) != {"type", "sdp"} or value.get("type") != kind:
        fail(422, "Qo‘ng‘iroq tavsifi noto‘g‘ri")
    sdp = value.get("sdp")
    if not isinstance(sdp, str) or not sdp.startswith("v=0") or len(sdp.encode("utf-8")) > 64000:
        fail(422, "Qo‘ng‘iroq tavsifi haddan katta yoki noto‘g‘ri")
    return value


def ice_candidate(value):
    if not isinstance(value, dict) or set(value) - {"candidate", "sdpMid", "sdpMLineIndex", "usernameFragment"}:
        fail(422, "Aloqa manzili noto‘g‘ri")
    if not isinstance(value.get("candidate"), str) or len(value["candidate"]) > 2048:
        fail(422, "Aloqa manzili noto‘g‘ri")
    for key in ("sdpMid", "usernameFragment"):
        if value.get(key) is not None and (not isinstance(value[key], str) or len(value[key]) > 256):
            fail(422, "Aloqa manzili noto‘g‘ri")
    index = value.get("sdpMLineIndex")
    if index is not None and (type(index) is not int or not 0 <= index <= 32):
        fail(422, "Aloqa manzili noto‘g‘ri")
    return value


def _json(value):
    return json.loads(value) if isinstance(value, str) else value


def _b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


def ice_config(uid, environ=None, now=None):
    env = os.environ if environ is None else environ
    urls = [s.strip() for s in env.get("KABUTAR_TURN_URLS", "").split(",") if s.strip()]
    secret = env.get("KABUTAR_TURN_SECRET", "")
    # Relay-only keeps institution participants' direct network addresses private.
    ready = bool(urls and len(secret) >= 24 and all(re.fullmatch(r"turns?:[^\s/@]+(?::\d+)?(?:\?transport=(?:udp|tcp))?", u) for u in urls))
    if not ready:
        return {"available": False, "reason": "Qo‘ng‘iroq serveri hali ulanmagan. Administrator TURN xizmatini sozlashi kerak."}
    expires = int(time.time() if now is None else now) + 4200
    username = f"{expires}:{int(uid)}"
    credential = base64.b64encode(hmac.new(secret.encode(), username.encode(), hashlib.sha1).digest()).decode()
    return {"available": True, "iceServers": [{"urls": urls, "username": username, "credential": credential}],
            "iceTransportPolicy": "relay", "expires_at": expires, "maximum_seconds": 3600}


def meeting_config(environ=None):
    env = os.environ if environ is None else environ
    raw = env.get("KABUTAR_MEET_ORIGIN", "").rstrip("/")
    try:
        parsed = urlsplit(raw)
        parsed.port  # Validate malformed/out-of-range ports before minting a JWT.
    except ValueError:
        fail(503, "Yig‘ilish serveri manzili noto‘g‘ri sozlangan.")
    valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password
             and not parsed.path and not parsed.query and not parsed.fragment
             and parsed.hostname not in {"meet.jit.si", "8x8.vc"}
             and env.get("KABUTAR_MEET_JWT_ONLY") == "1"
             and env.get("KABUTAR_MEET_ROLE_ENFORCEMENT") == "token_affiliation"
             and env.get("KABUTAR_MEET_APP_ID") and len(env.get("KABUTAR_MEET_SECRET", "")) >= 32)
    if not valid:
        fail(503, "Yig‘ilish xizmati hali ulanmagan. Yopiq JWT yig‘ilish serveri kerak.")
    return raw, parsed.hostname, env["KABUTAR_MEET_APP_ID"], env["KABUTAR_MEET_SECRET"]


def meeting_moderator(rows, group):
    """Only actual assigned teachers/managers; profile role and owner alone fail."""
    source = group.get("manba_turi")
    source_id = int(group.get("manba_id") or 0)
    cohort = f"{source}:{source_id}"
    if source in {"sinf", "universitet_guruh", "togarak", "course"}:
        return any(r.get("cohort") == cohort and r.get("role") == "teacher" for r in rows)
    managers = {"direktor", "zam_direktor_uquv", "zam_direktor_tarbiya", "markaz_direktor", "bogcha_direktor",
                "rektor", "prorektor", "dekan", "zam_dekan", "kafedra_mudiri", "institut_admin", "fakultet_admin",
                "owner", "manager", "director", "admin", "administrator"}
    return bool(group.get("turi") == "xodimlar" and any(
        r.get("role") == "staff" and r.get("kind") == source and int(r.get("inst_id") or 0) == source_id
        and r.get("label") in managers for r in rows))


class CallService:
    def __init__(self, platform):
        self.platform = platform
        self._ready = False
        self._lock = threading.Lock()

    @contextmanager
    def database(self):
        conn = self.platform._db()
        cur = None
        try:
            cur = conn.cursor()
            cur.execute("SET LOCAL statement_timeout = '5000ms'")
            cur.execute("SET LOCAL lock_timeout = '1500ms'")
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if cur is not None:
                cur.close()
            conn.close()

    def migrate(self):
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            with self.database() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(45590217)")
                cur.execute(SCHEMA)
            self._ready = True

    def authenticate(self, authorization):
        scheme, _, token = str(authorization or "").partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            fail(401, "Kabutar akkauntiga qayta kiring")
        token = token.strip()
        uid = self.platform._jwt_tekshir(token)
        auth = getattr(self.platform, "_kabutar_auth_service", None)
        if auth is None:
            fail(503, "Kabutar kirish xizmati hali ulanmagan.")
        if auth.claims(token).get("admin_korish"):
            fail(403, "Ko‘rish rejimida boshqa foydalanuvchining qo‘ng‘iroq va yig‘ilishlariga kirib bo‘lmaydi.")
        return int(uid)

    def cleanup(self, cur):
        cur.execute("UPDATE kabutar_call_cleanup_v45 SET last_at=NOW() WHERE singleton=TRUE AND last_at < NOW()-INTERVAL '60 seconds' RETURNING singleton")
        if cur.fetchone():
            # Bounded deletes; an external daily DB job can drain larger backlogs.
            cur.execute("DELETE FROM kabutar_calls_v45 WHERE id IN (SELECT id FROM kabutar_calls_v45 WHERE expires_at < NOW()-INTERVAL '1 hour' ORDER BY expires_at LIMIT 100)")

    def configuration(self, uid):
        value = ice_config(uid)
        if not value["available"]:
            return value
        # TURN credentials grant relay capacity independently of signaling.
        # Issue them only to verified institution members who accepted terms.
        with self.database() as cur:
            ensure_terms_accepted(cur, uid)
            if not memberships(cur, uid):
                fail(403, "Qo‘ng‘iroq uchun muassasadagi a’zoligingiz tasdiqlanishi kerak.")
        return value

    def authorize(self, cur, row, uid):
        if not row or uid not in (row["caller_id"], row["callee_id"]):
            fail(404, "Qo‘ng‘iroq topilmadi")
        require_direct(cur, uid, row["callee_id"] if uid == row["caller_id"] else row["caller_id"])

    def load(self, cur, call_id, uid):
        if not re.fullmatch(r"[0-9a-f-]{36}", str(call_id)):
            fail(404, "Qo‘ng‘iroq topilmadi")
        cur.execute("SELECT *, expires_at <= NOW() OR created_at < NOW()-INTERVAL '1 hour' OR (state='active' AND LEAST(caller_seen_at,callee_seen_at)<NOW()-INTERVAL '60 seconds') AS expired FROM kabutar_calls_v45 WHERE id=%s FOR UPDATE", (call_id,))
        row = cur.fetchone()
        self.authorize(cur, row, uid)
        if row["expired"] and row["state"] != "ended":
            self.end(cur, row, "timeout")
        return row

    def end(self, cur, row, reason):
        cur.execute("UPDATE kabutar_calls_v45 SET state='ended',reason=%s,offer=NULL,answer=NULL,expires_at=NOW(),updated_at=NOW() WHERE id=%s", (reason, row["id"]))
        cur.execute("DELETE FROM kabutar_call_ice_v45 WHERE call_id=%s", (row["id"],))
        row.update(state="ended", reason=reason, offer=None, answer=None)

    def summary(self, cur, row, uid, include_sdp=True):
        peer = row["callee_id"] if uid == row["caller_id"] else row["caller_id"]
        cur.execute("SELECT full_name FROM users WHERE user_id=%s", (peer,))
        name = cur.fetchone() or {}
        result = {k: row.get(k) for k in ("id", "caller_id", "callee_id", "mode", "state", "reason")}
        result.update(peer_id=peer, peer_name=name.get("full_name") or "Hamkasb", incoming=uid == row["callee_id"])
        if include_sdp:
            result.update(offer=_json(row.get("offer")), answer=_json(row.get("answer")))
        return result

    def create(self, uid, payload):
        peer = as_id(payload.get("peer_id"))
        if uid == peer:
            fail(422, "O‘zingizga qo‘ng‘iroq qilib bo‘lmaydi")
        mode = payload.get("mode")
        if mode not in ("audio", "video"):
            fail(422, "Qo‘ng‘iroq turi noto‘g‘ri")
        key = request_key(payload.get("request_id"))
        offer = description(payload.get("offer"), "offer")
        if not ice_config(uid)["available"]:
            fail(503, ice_config(uid)["reason"])
        self.migrate()
        with self.database() as cur:
            ensure_terms_accepted(cur, uid)
            require_direct(cur, uid, peer)
            # Lock both users in sorted order: crossing calls cannot create two sessions.
            for person in sorted((uid, peer)):
                cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s,4559))", (f"kabutar-call:{person}",))
            cur.execute("SELECT * FROM kabutar_calls_v45 WHERE caller_id=%s AND request_id=%s", (uid, key))
            previous = cur.fetchone()
            if previous:
                if previous["callee_id"] != peer or previous["mode"] != mode:
                    fail(409, "Bu so‘rov kaliti boshqa qo‘ng‘iroqda ishlatilgan")
                return self.summary(cur, previous, uid)
            cur.execute("SELECT id FROM kabutar_calls_v45 WHERE (caller_id IN (%s,%s) OR callee_id IN (%s,%s)) AND state <> 'ended' AND expires_at>NOW() AND created_at>NOW()-INTERVAL '1 hour' AND (state='ringing' OR LEAST(caller_seen_at,callee_seen_at)>NOW()-INTERVAL '60 seconds') LIMIT 1", (uid, peer, uid, peer))
            if cur.fetchone():
                fail(409, "Siz yoki suhbatdoshingiz boshqa qo‘ng‘iroqda")
            cur.execute("INSERT INTO kabutar_call_budget_v45(user_id,minute,used) VALUES(%s,date_trunc('minute',NOW()),1) ON CONFLICT(user_id) DO UPDATE SET minute=EXCLUDED.minute,used=CASE WHEN kabutar_call_budget_v45.minute=EXCLUDED.minute THEN kabutar_call_budget_v45.used+1 ELSE 1 END WHERE kabutar_call_budget_v45.minute<>EXCLUDED.minute OR kabutar_call_budget_v45.used<4 RETURNING used", (uid,))
            if not cur.fetchone():
                fail(429, "Bir daqiqa kutib, qayta qo‘ng‘iroq qiling")
            call_id = str(uuid.uuid4())
            cur.execute("INSERT INTO kabutar_calls_v45(id,caller_id,callee_id,mode,request_id,offer) VALUES(%s,%s,%s,%s,%s,%s::jsonb) RETURNING *", (call_id, uid, peer, mode, key, json.dumps(offer)))
            row = cur.fetchone()
            self.cleanup(cur)
            return self.summary(cur, row, uid)

    def incoming(self, uid):
        self.migrate()
        with self.database() as cur:
            cur.execute("SELECT * FROM kabutar_calls_v45 WHERE callee_id=%s AND state='ringing' AND expires_at>NOW() ORDER BY created_at DESC LIMIT 4", (uid,))
            rows = cur.fetchall()
            return {"calls": [self.summary(cur, row, uid, False) for row in rows if allow_direct(cur, uid, row["caller_id"])]}

    def read(self, uid, call_id, after=0):
        if type(after) is not int or not 0 <= after <= 9223372036854775807:
            fail(422, "Aloqa tartib raqami noto‘g‘ri")
        self.migrate()
        with self.database() as cur:
            row = self.load(cur, call_id, uid)
            if row["state"] == "active":
                column = "caller_seen_at" if uid == row["caller_id"] else "callee_seen_at"
                cur.execute(f"UPDATE kabutar_calls_v45 SET {column}=NOW(),expires_at=LEAST(created_at+INTERVAL '1 hour',NOW()+INTERVAL '70 seconds') WHERE id=%s", (call_id,))
            cur.execute("SELECT seq,candidate FROM kabutar_call_ice_v45 WHERE call_id=%s AND sender_id<>%s AND seq>%s ORDER BY seq LIMIT 128", (call_id, uid, after))
            candidates = [{"seq": r["seq"], "candidate": _json(r["candidate"])} for r in cur.fetchall()]
            result = self.summary(cur, row, uid)
            result["candidates"] = candidates
            return result

    def signal(self, uid, call_id, payload):
        action = payload.get("action")
        if action not in {"answer", "ice", "hangup", "decline"}:
            fail(422, "Aloqa amali noto‘g‘ri")
        self.migrate()
        with self.database() as cur:
            row = self.load(cur, call_id, uid)
            if action in {"hangup", "decline"}:
                if action == "decline" and uid != row["callee_id"]:
                    fail(403, "Bu qo‘ng‘iroqni rad eta olmaysiz")
                if row["state"] != "ended":
                    self.end(cur, row, "declined" if action == "decline" else "hangup")
                return {"ok": True, "state": "ended"}
            if row["state"] == "ended":
                fail(410, "Qo‘ng‘iroq tugagan")
            if action == "answer":
                ensure_terms_accepted(cur, uid)
                if uid != row["callee_id"]:
                    fail(403, "Faqat chaqirilgan foydalanuvchi javob bera oladi")
                answer = description(payload.get("answer"), "answer")
                if row.get("answer"):
                    if _json(row["answer"]) != answer:
                        fail(409, "Qo‘ng‘iroqqa boshqa qurilmada javob berilgan")
                else:
                    cur.execute("UPDATE kabutar_calls_v45 SET answer=%s::jsonb,state='active',updated_at=NOW(),caller_seen_at=NOW(),callee_seen_at=NOW(),expires_at=NOW()+INTERVAL '70 seconds' WHERE id=%s", (json.dumps(answer), call_id))
                return {"ok": True, "state": "active"}
            candidate = ice_candidate(payload.get("candidate"))
            key = request_key(payload.get("request_id"))
            if uid == row["callee_id"] and row["state"] != "active":
                fail(409, "Avval qo‘ng‘iroqqa javob bering")
            cur.execute("SELECT seq FROM kabutar_call_ice_v45 WHERE call_id=%s AND sender_id=%s AND request_id=%s", (call_id, uid, key))
            old = cur.fetchone()
            if old:
                return {"ok": True, "seq": old["seq"]}
            cur.execute("SELECT COUNT(*) AS n FROM kabutar_call_ice_v45 WHERE call_id=%s AND sender_id=%s", (call_id, uid))
            if int(cur.fetchone()["n"]) >= 64:
                fail(429, "Aloqa manzillari chegarasiga yetildi; qayta qo‘ng‘iroq qiling")
            cur.execute("INSERT INTO kabutar_call_ice_v45(call_id,sender_id,request_id,candidate) VALUES(%s,%s,%s,%s::jsonb) RETURNING seq", (call_id, uid, key, json.dumps(candidate)))
            return {"ok": True, "seq": cur.fetchone()["seq"]}

    def meeting_access(self, uid, group_id):
        with self.database() as cur:
            require_group(cur, uid, group_id, write=True)
            cur.execute("SELECT id,nomi,turi,manba_turi,manba_id,egasi_user_id FROM chat_guruhlari WHERE id=%s", (group_id,))
            group = cur.fetchone()
            if not group:
                fail(404, "Guruh topilmadi")
            moderator = meeting_moderator(memberships(cur, uid), group)
            cur.execute("SELECT full_name FROM users WHERE user_id=%s", (uid,))
            person = cur.fetchone() or {}
        return {"name": group["nomi"], "user_name": person.get("full_name") or "Ishtirokchi", "moderator": moderator}

    def meeting(self, uid, group_id):
        origin, host, app_id, secret = meeting_config()
        access = self.meeting_access(uid, group_id)
        now = int(time.time())
        # Unpredictable institution room, exact room claim, short joining token.
        room = "kb-" + hmac.new(secret.encode(), f"group:{group_id}".encode(), hashlib.sha256).hexdigest()[:32]
        payload = {"aud": "jitsi", "iss": app_id, "sub": host, "room": room,
                   "iat": now, "nbf": now-10, "exp": now+300,
                   "context": {"user": {"id": str(uid), "name": access["user_name"],
                                        "moderator": access["moderator"], "affiliation": "owner" if access["moderator"] else "member"}}}
        encoded = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())+"."+_b64(json.dumps(payload, separators=(",", ":")).encode())
        token = encoded+"."+_b64(hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).digest())
        return {"origin": origin, "room": room, "jwt": token, "expires_at": now+300,
                "name": access["name"], "moderator": access["moderator"]}


def register_calls(app, platform):
    from fastapi import APIRouter, Body, Header, Query, Response
    router = APIRouter(prefix="/api/kabutar")
    service = CallService(platform)

    def uid(authorization, response):
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["Pragma"] = "no-cache"
        return service.authenticate(authorization)

    @router.get("/calls/config")
    def config(response: Response, authorization: str | None = Header(None)):
        return service.configuration(uid(authorization, response))

    @router.get("/calls/incoming")
    def incoming(response: Response, authorization: str | None = Header(None)):
        return service.incoming(uid(authorization, response))

    @router.post("/calls")
    def create(response: Response, payload: dict = Body(...), authorization: str | None = Header(None)):
        return service.create(uid(authorization, response), payload)

    @router.get("/calls/{call_id}")
    def read(call_id: str, response: Response, after: int = Query(0, ge=0), authorization: str | None = Header(None)):
        return service.read(uid(authorization, response), call_id, after)

    @router.post("/calls/{call_id}/signal")
    def signal(call_id: str, response: Response, payload: dict = Body(...), authorization: str | None = Header(None)):
        return service.signal(uid(authorization, response), call_id, payload)

    @router.post("/meetings/group/{group_id}")
    def meeting(group_id: int, response: Response, authorization: str | None = Header(None)):
        return service.meeting(uid(authorization, response), as_id(group_id))

    @router.get("/meetings/group/{group_id}/access")
    def meeting_access(group_id: int, response: Response, authorization: str | None = Header(None)):
        return service.meeting_access(uid(authorization, response), as_id(group_id))

    app.include_router(router)
    return service
