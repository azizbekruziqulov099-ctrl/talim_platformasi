"""Kabutar authentication v31: database-backed one-use login and revocable sessions.

No SMS gateway is used. The Telegram bot alone confirms an own-contact event,
using a separate server credential. Every browser exchange also proves knowledge
of a secret which is never sent to Telegram. Existing user IDs are never moved.
"""
from __future__ import annotations
import hashlib
import hmac
import os
import re
import secrets
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Header, HTTPException, Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from pydantic import BaseModel, Field

CHALLENGE_SECONDS = 300
RESULT_SECONDS = 120
SESSION_DAYS = 30
PASSWORD_SLOTS = threading.BoundedSemaphore(4)

SCHEMA = """
CREATE TABLE IF NOT EXISTS kabutar_auth_sessions (
 session_hash TEXT PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(user_id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), expires_at TIMESTAMPTZ NOT NULL,
 revoked_at TIMESTAMPTZ, method TEXT NOT NULL DEFAULT 'legacy'
);
CREATE INDEX IF NOT EXISTS kabutar_auth_sessions_user ON kabutar_auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS kabutar_auth_sessions_expiry ON kabutar_auth_sessions(expires_at);
CREATE TABLE IF NOT EXISTS kabutar_telegram_identity (
 telegram_id BIGINT PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(user_id),
 phone TEXT NOT NULL UNIQUE, verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS kabutar_telegram_identity_user ON kabutar_telegram_identity(user_id);
CREATE TABLE IF NOT EXISTS kabutar_auth_challenges (
 challenge_hash TEXT PRIMARY KEY, browser_hash TEXT NOT NULL,
 verification_code TEXT NOT NULL, mode TEXT NOT NULL CHECK(mode IN ('login','link')),
 target_user_id BIGINT REFERENCES users(user_id), link_session_hash TEXT, user_id BIGINT REFERENCES users(user_id),
 telegram_id BIGINT, phone TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 expires_at TIMESTAMPTZ NOT NULL, confirmed_at TIMESTAMPTZ, consumed_at TIMESTAMPTZ,
 cancelled_at TIMESTAMPTZ
);
ALTER TABLE kabutar_auth_challenges ADD COLUMN IF NOT EXISTS link_session_hash TEXT;
CREATE INDEX IF NOT EXISTS kabutar_auth_challenges_expiry ON kabutar_auth_challenges(expires_at);
CREATE TABLE IF NOT EXISTS kabutar_auth_consumed (
 token_hash TEXT PRIMARY KEY, expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS kabutar_auth_consumed_expiry ON kabutar_auth_consumed(expires_at);
CREATE TABLE IF NOT EXISTS kabutar_auth_rate (
 bucket TEXT PRIMARY KEY, window_at TIMESTAMPTZ NOT NULL, hits INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS kabutar_auth_security (
 user_id BIGINT PRIMARY KEY REFERENCES users(user_id), disable_legacy BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE IF NOT EXISTS kabutar_auth_password (
 user_id BIGINT PRIMARY KEY REFERENCES users(user_id), password_hash TEXT NOT NULL,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS kabutar_education_ready BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS kabutar_nickname TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_discoverable BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS kabutar_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS users_kabutar_id_uq ON users(kabutar_id) WHERE kabutar_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS users_kabutar_nickname_uq ON users(LOWER(kabutar_nickname)) WHERE kabutar_nickname IS NOT NULL;
"""


def digest(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def normalize_phone(value: str) -> str:
    digits = re.sub(r'[^0-9]', '', value or '')
    if len(digits) == 9:
        digits = '998' + digits
    if not 10 <= len(digits) <= 15 or digits.startswith('0'):
        raise HTTPException(422, 'Telefon raqami xalqaro formatda bo‘lishi kerak')
    return '+' + digits


def password_hash(password: str, salt: Optional[bytes] = None) -> str:
    if not 10 <= len(password) <= 128:
        raise HTTPException(422, 'Parol 10–128 belgidan iborat bo‘lsin')
    salt = salt or secrets.token_bytes(16)
    if not PASSWORD_SLOTS.acquire(blocking=False):
        raise HTTPException(429, 'Bir ozdan keyin qayta urinib ko‘ring')
    try:
        key = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
    finally:
        PASSWORD_SLOTS.release()
    return 'scrypt$16384$8$1$' + salt.hex() + '$' + key.hex()


def password_matches(password: str, stored: str) -> bool:
    try:
        algorithm, n, r, p, salt, key = stored.split('$')
        if (algorithm, n, r, p) != ('scrypt', '16384', '8', '1'):
            return False
        if not 10 <= len(password) <= 128:
            return False
        actual = password_hash(password, bytes.fromhex(salt))
        return hmac.compare_digest(actual, stored)
    except (ValueError, TypeError):
        return False


class Start(BaseModel):
    mode: str = 'login'
    token: Optional[str] = None

class BrowserChallenge(BaseModel):
    challenge: str = Field(min_length=32, max_length=64)
    browser_secret: str = Field(min_length=32, max_length=128)

class Inspect(BaseModel):
    challenge: str = Field(min_length=32, max_length=64)

class Confirm(Inspect):
    telegram_user_id: int = Field(gt=0)
    contact_user_id: int = Field(gt=0)
    phone: str = Field(min_length=6, max_length=32)
    full_name: str = Field(default='', max_length=200)

class TokenBody(BaseModel):
    token: Optional[str] = None

class Logout(TokenBody):
    all_devices: bool = False

class PasswordLogin(BaseModel):
    identifier: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)

class PasswordSet(TokenBody):
    password: str = Field(min_length=10, max_length=128)
    current_password: Optional[str] = None
    reset: bool = False

class Education(TokenBody):
    role: str
    grade: Optional[int] = Field(default=None, ge=1, le=11)
    class_: Optional[int] = Field(default=None, alias='class', ge=1, le=11)
    language: str = 'uz'
    subject: Optional[str] = Field(default=None, max_length=100)

class GoogleLink(TokenBody):
    oauth_grant: str
    email: str

class InviteClaim(BaseModel):
    email: str = Field(max_length=254)
    oauth_grant: str = Field(max_length=4096)
    kod: str = Field(min_length=12,max_length=128)


class AuthService:
    def __init__(self, platform):
        self.p = platform
        self.key = platform.JWT_MAXFIY_KALIT
        self.bot_secret = os.getenv('KABUTAR_BOT_AUTH_SECRET', '')
        self.bot_username = os.getenv('KABUTAR_BOT_USERNAME', '').strip().lstrip('@')
        self.dummy_password = password_hash('not-a-real-account-password')

    @contextmanager
    def transaction(self):
        conn = self.p._db()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def migrate(self):
        with self.transaction() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (31093109,))
            cur.execute(SCHEMA)
            # Old users already chose their educational role; never ask again.
            cur.execute("CREATE TABLE IF NOT EXISTS kabutar_auth_migrations(version TEXT PRIMARY KEY)")
            cur.execute("INSERT INTO kabutar_auth_migrations(version) VALUES('31-education') ON CONFLICT DO NOTHING RETURNING version")
            if cur.fetchone():
                cur.execute("UPDATE users SET kabutar_education_ready=TRUE WHERE role IS NOT NULL AND role NOT IN ('kabutar','mustaqil') AND NOT kabutar_education_ready")
            cur.execute("DELETE FROM kabutar_auth_challenges WHERE expires_at < NOW()-INTERVAL '1 day'")
            cur.execute('DELETE FROM kabutar_auth_consumed WHERE expires_at < NOW()')
            cur.execute("DELETE FROM kabutar_auth_rate WHERE window_at < NOW()-INTERVAL '1 day'")
            cur.execute("DELETE FROM kabutar_auth_sessions WHERE expires_at < NOW()-INTERVAL '1 day'")

    def origin(self, request):
        origin = (request.headers.get('origin') or '').rstrip('/')
        if origin and origin not in self.p.FRONTEND_ORIGINS:
            raise HTTPException(403, 'So‘rov manbasi ruxsat etilmagan')

    def token(self, request, body_token=None):
        return self.p._jwt_header_yoki_query(body_token, request.headers.get('authorization'))

    def rate(self, scope, subject, limit, seconds=60):
        bucket = digest(scope + ':' + subject)
        with self.transaction() as cur:
            cur.execute("""INSERT INTO kabutar_auth_rate(bucket,window_at,hits) VALUES(%s,NOW(),1)
                ON CONFLICT(bucket) DO UPDATE SET
                hits=CASE WHEN kabutar_auth_rate.window_at < NOW()-(%s*INTERVAL '1 second') THEN 1 ELSE kabutar_auth_rate.hits+1 END,
                window_at=CASE WHEN kabutar_auth_rate.window_at < NOW()-(%s*INTERVAL '1 second') THEN NOW() ELSE kabutar_auth_rate.window_at END
                RETURNING hits""", (bucket, seconds, seconds))
            hits = cur.fetchone()['hits']
        if hits > limit:
            raise HTTPException(429, 'Ko‘p urinish. Bir oz kutib qayta urinib ko‘ring', headers={'Retry-After': str(seconds)})

    def ip(self, request):
        # Forwarded headers are trusted only behind a configured private proxy.
        if os.getenv('KABUTAR_TRUST_PROXY_HEADERS', '').lower() == 'true':
            value = request.headers.get('x-forwarded-for', '').split(',')[0].strip()
            if value:
                return value[:100]
        return request.client.host if request.client else 'unknown'

    def bot_auth(self, supplied):
        if len(self.bot_secret) < 32:
            raise HTTPException(503, 'Telegram orqali kirish hali sozlanmagan')
        if not supplied or not secrets.compare_digest(supplied.encode('utf-8'), self.bot_secret.encode('utf-8')):
            raise HTTPException(401, 'Bot tasdig‘i noto‘g‘ri')

    def user_lock(self, cur, user_id):
        cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,31))',(f'auth-user:{user_id}',))

    def disable_legacy(self, cur, user_id):
        cur.execute("""INSERT INTO kabutar_auth_security(user_id,disable_legacy) VALUES(%s,TRUE)
            ON CONFLICT(user_id) DO UPDATE SET disable_legacy=TRUE""", (user_id,))

    def recent_session(self, cur, token, user_id):
        self.user_lock(cur,user_id)
        claims = self.claims(token)
        if claims.get('admin_korish'):
            raise HTTPException(403, 'Ko‘rish rejimida akkaunt ulanmaydi')
        key = digest(claims['sid']) if claims.get('sid') else digest(token)
        cur.execute("""SELECT 1 FROM kabutar_auth_sessions WHERE session_hash=%s AND user_id=%s
            AND revoked_at IS NULL AND expires_at>NOW() AND created_at>NOW()-INTERVAL '10 minutes'
            AND method IN ('google','telegram','password') FOR UPDATE""", (key,user_id))
        if not cur.fetchone():
            raise HTTPException(403, 'Akkaunt ulash uchun avval qaytadan kiring')
        return key

    def check_link_session(self, cur, row):
        if row['mode'] != 'link':
            return
        key = row.get('link_session_hash')
        if not key:
            raise HTTPException(410, 'Ulash so‘rovini qaytadan boshlang')
        cur.execute("""SELECT 1 FROM kabutar_auth_sessions WHERE session_hash=%s AND user_id=%s
            AND revoked_at IS NULL AND expires_at>NOW() FOR UPDATE""", (key,row['target_user_id']))
        if not cur.fetchone():
            raise HTTPException(410, 'Kirish sessiyasi bekor qilingan. Ulanishni qayta boshlang')

    def _session_token(self, user_id, sid, created, expires):
        return jwt.encode({'purpose': 'access', 'user_id': int(user_id), 'sid': sid,
            'iat': created, 'exp': expires}, self.key, algorithm='HS256')

    def _issue_cur(self, cur, user_id, method, sid=None, created=None):
        self.user_lock(cur,user_id)
        cur.execute('INSERT INTO kabutar_auth_security(user_id) VALUES(%s) ON CONFLICT DO NOTHING',(user_id,))
        sid = sid or secrets.token_urlsafe(32)
        created = created or datetime.now(timezone.utc)
        expires = created + timedelta(days=SESSION_DAYS)
        cur.execute("""INSERT INTO kabutar_auth_sessions(session_hash,user_id,created_at,expires_at,method)
            VALUES(%s,%s,%s,%s,%s) ON CONFLICT(session_hash) DO NOTHING""",
            (digest(sid), int(user_id), created, expires, method))
        return self._session_token(user_id, sid, created, expires)

    def record_login(self, user_id, method):
        callback = getattr(self.p, '_kabutar_record_login', None)
        if callback and method != 'legacy':
            try:
                callback(int(user_id), method)
            except Exception:
                pass

    def issue_session(self, user_id, method='google'):
        with self.transaction() as cur:
            result = self._issue_cur(cur, user_id, method)
        self.record_login(user_id, method)
        return result

    def verify_session(self, token, payload):
        # Admin view is deliberately short-lived and maintains original checks.
        if payload.get('admin_korish'):
            return int(payload['user_id'])
        user_id = payload.get('user_id')
        if not isinstance(user_id, int) or isinstance(user_id, bool):
            raise HTTPException(401, 'Sessiya noto‘g‘ri')
        sid = payload.get('sid')
        legacy = not payload.get('purpose') and not sid
        if legacy:
            if set(payload) - {'user_id', 'exp'}:
                raise HTTPException(401, 'Qaytadan kiring')
            session_hash = digest(token)
        elif payload.get('purpose') == 'access' and isinstance(sid, str) and len(sid) >= 32:
            session_hash = digest(sid)
        else:
            raise HTTPException(401, 'Bu token kirish sessiyasi emas')
        with self.transaction() as cur:
            if legacy:
                self.user_lock(cur,user_id)
                cur.execute('SELECT disable_legacy FROM kabutar_auth_security WHERE user_id=%s',(user_id,))
                if (cur.fetchone() or {}).get('disable_legacy'):
                    raise HTTPException(401, 'Eski sessiyalar bekor qilingan. Qaytadan kiring')
                cur.execute('INSERT INTO kabutar_auth_security(user_id) VALUES(%s) ON CONFLICT DO NOTHING',(user_id,))
                cur.execute("""INSERT INTO kabutar_auth_sessions(session_hash,user_id,expires_at,method)
                    VALUES(%s,%s,to_timestamp(%s),'legacy') ON CONFLICT DO NOTHING""",
                    (session_hash, user_id, payload['exp']))
            cur.execute("""SELECT user_id FROM kabutar_auth_sessions WHERE session_hash=%s
                AND revoked_at IS NULL AND expires_at>NOW()""", (session_hash,))
            row = cur.fetchone()
        if not row or int(row['user_id']) != user_id:
            raise HTTPException(401, 'Sessiya tugagan yoki bekor qilingan. Qaytadan kiring')
        return user_id

    def claims(self, token):
        try:
            return jwt.decode(token, self.key, algorithms=['HS256'], options={'require_exp': True})
        except JWTError:
            raise HTTPException(401, 'Qaytadan kiring')

    def consume_cur(self, cur, payload):
        cur.execute("""INSERT INTO kabutar_auth_consumed(token_hash,expires_at) VALUES(%s,to_timestamp(%s))
            ON CONFLICT DO NOTHING RETURNING token_hash""", (digest(str(payload['jti'])), payload['exp']))
        if not cur.fetchone():
            raise HTTPException(401, 'Tasdiqlash avval ishlatilgan. Qaytadan kiring')

    def consume(self, payload):
        with self.transaction() as cur:
            self.consume_cur(cur, payload)

    def _challenge(self, cur, challenge, browser_secret=None):
        # Uniform lock order: user -> challenge -> session. Logout/password reset
        # follow the same order, avoiding challenge/session deadlocks.
        cur.execute('SELECT target_user_id FROM kabutar_auth_challenges WHERE challenge_hash=%s',(digest(challenge),))
        target=cur.fetchone()
        if target and target.get('target_user_id') is not None:
            self.user_lock(cur,target['target_user_id'])
        cur.execute('SELECT *, expires_at>NOW() AS live FROM kabutar_auth_challenges WHERE challenge_hash=%s FOR UPDATE', (digest(challenge),))
        row = cur.fetchone()
        if not row or (browser_secret is not None and not secrets.compare_digest(row['browser_hash'], digest(browser_secret))):
            raise HTTPException(401, 'Kirish so‘rovi topilmadi yoki brauzer mos emas')
        return row

    def _resolve_telegram(self, cur, telegram_id, phone, name, target=None):
        # Lock identities in fixed order so parallel approvals cannot claim a phone.
        for label in sorted([f'tg:{telegram_id}', f'phone:{phone}']):
            cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,31))', (label,))
        cur.execute('SELECT user_id,phone FROM kabutar_telegram_identity WHERE telegram_id=%s', (telegram_id,))
        identity = cur.fetchone()
        owned = int(identity['user_id']) if identity else None
        if owned is None:
            cur.execute("SELECT to_regclass('public.user_accounts') AS t")
            if cur.fetchone()['t']:
                cur.execute('SELECT uid FROM user_accounts WHERE telegram_id=%s AND account_index=0', (telegram_id,))
                primary = cur.fetchone()
                if primary and primary['uid'] is not None:
                    cur.execute('SELECT user_id FROM users WHERE user_id=%s', (primary['uid'],))
                    user = cur.fetchone()
                    owned = int(user['user_id']) if user else None
                if owned is None:
                    # A moved legacy raw ID must not be reclaimed by its former owner.
                    cur.execute('SELECT 1 FROM user_accounts WHERE uid=%s AND telegram_id<>%s LIMIT 1', (telegram_id, telegram_id))
                    if cur.fetchone():
                        raise HTTPException(409, 'Eski akkaunt bog‘lanishini tekshirish kerak. Google orqali kiring')
            if owned is None:
                cur.execute('SELECT user_id FROM users WHERE user_id=%s', (telegram_id,))
                user = cur.fetchone()
                owned = int(user['user_id']) if user else None
        if target is not None and owned is not None and owned != int(target):
            raise HTTPException(409, 'Telegram boshqa Kabutar akkauntiga tegishli. Akkauntlar avtomatik birlashtirilmaydi')
        user_id = int(target) if target is not None else (owned if owned is not None else telegram_id)
        cur.execute('SELECT user_id FROM telefon_hisob WHERE telefon=%s', (phone,))
        phone_owner = cur.fetchone()
        if phone_owner and phone_owner['user_id'] is not None and int(phone_owner['user_id']) != user_id:
            raise HTTPException(409, 'Bu telefon boshqa akkauntga ulangan. Avval o‘sha akkauntga kiring')
        cur.execute('SELECT telegram_id,user_id FROM kabutar_telegram_identity WHERE phone=%s OR user_id=%s', (phone,user_id))
        for other in cur.fetchall():
            if int(other['telegram_id']) != telegram_id or int(other['user_id']) != user_id:
                raise HTTPException(409, 'Telefon yoki akkaunt boshqa Telegram hisobiga ulangan')
        if owned is None and target is None:
            cur.execute("INSERT INTO users(user_id,full_name,role) VALUES(%s,%s,'kabutar') ON CONFLICT(user_id) DO NOTHING", (user_id,name.strip() or 'Kabutar foydalanuvchisi'))
        cur.execute('SELECT user_id FROM users WHERE user_id=%s', (user_id,))
        if not cur.fetchone():
            raise HTTPException(409, 'Ulanadigan akkaunt topilmadi')
        if identity and identity['phone'] != phone:
            cur.execute('UPDATE users SET phone_discoverable=FALSE WHERE user_id=%s',(user_id,))
            cur.execute('DELETE FROM telefon_hisob WHERE telefon=%s AND user_id=%s', (identity['phone'],user_id))
        cur.execute('''INSERT INTO kabutar_telegram_identity(telegram_id,user_id,phone) VALUES(%s,%s,%s)
            ON CONFLICT(telegram_id) DO UPDATE SET phone=EXCLUDED.phone,verified_at=NOW()''', (telegram_id,user_id,phone))
        cur.execute('INSERT INTO telefon_hisob(telefon,user_id) VALUES(%s,%s) ON CONFLICT(telefon) DO NOTHING', (phone,user_id))
        return user_id

    def profile_status(self, user_id):
        with self.transaction() as cur:
            cur.execute('SELECT role,kabutar_education_ready FROM users WHERE user_id=%s', (user_id,))
            user=cur.fetchone()
            if not user:
                raise HTTPException(401, 'Akkaunt topilmadi')
            cur.execute('SELECT phone FROM kabutar_telegram_identity WHERE user_id=%s', (user_id,))
            phone=(cur.fetchone() or {}).get('phone')
            cur.execute('SELECT 1 FROM google_hisob WHERE user_id=%s LIMIT 1', (user_id,))
            google=cur.fetchone() is not None
            cur.execute('SELECT 1 FROM kabutar_auth_password WHERE user_id=%s', (user_id,))
            has_password=cur.fetchone() is not None
        return {'education_ready':bool(user['kabutar_education_ready']), 'has_password':has_password,
            'identities':{'google':google,'telegram':bool(phone),'phone':bool(phone)},
            'phone_masked':phone[:4]+'•••••'+phone[-4:] if phone else None}


def register_auth(app, platform):
    service=AuthService(platform)
    platform._kabutar_auth_service=service
    platform._auth_ticket_consume=service.consume
    platform._auth_ticket_consume_cur=service.consume_cur
    app.router.add_event_handler('startup',service.migrate)

    @app.middleware('http')
    async def auth_response_headers(request, call_next):
        response=await call_next(request)
        if request.url.path.startswith('/auth/') or request.url.path.startswith('/api/auth/'):
            response.headers['Cache-Control']='no-store'
            response.headers['Referrer-Policy']='no-referrer'
        return response

    @app.get('/auth/config')
    def config():
        return {'telegram':{'enabled':len(service.bot_secret)>=32 and bool(re.fullmatch(r'[A-Za-z0-9_]{5,32}',service.bot_username)), 'bot_username':service.bot_username},
            'google':{'enabled':bool(platform.GOOGLE_CLIENT_ID and platform.GOOGLE_CLIENT_SECRET)},'password':{'enabled':True}}

    @app.post('/auth/telegram/start')
    def start(body:Start,request:Request):
        service.origin(request)
        if not config()['telegram']['enabled']:
            raise HTTPException(503,'Telegram orqali kirish hali sozlanmagan')
        if body.mode not in ('login','link'):
            raise HTTPException(422,'Kirish turi noto‘g‘ri')
        target=None
        sid_hash=None
        token=None
        if body.mode=='link':
            token=service.token(request,body.token)
            target=platform._jwt_tekshir(token)
        service.rate('telegram-start-ip',service.ip(request),60)
        challenge=secrets.token_urlsafe(24)
        browser_secret=secrets.token_urlsafe(32)
        code=f'{secrets.randbelow(1000000):06d}'
        with service.transaction() as cur:
            if body.mode=='link':
                sid_hash=service.recent_session(cur,token,target)
            cur.execute('''INSERT INTO kabutar_auth_challenges(challenge_hash,browser_hash,verification_code,mode,target_user_id,link_session_hash,expires_at)
                VALUES(%s,%s,%s,%s,%s,%s,NOW()+INTERVAL '5 minutes')''',(digest(challenge),digest(browser_secret),code,body.mode,target,sid_hash))
        return {'challenge':challenge,'browser_secret':browser_secret,'verification_code':code,
            'bot_url':f'https://t.me/{service.bot_username}?start=kb_{challenge}','expires_in':CHALLENGE_SECONDS}

    @app.post('/auth/telegram/inspect')
    def inspect(body:Inspect,x_kabutar_bot_secret:Optional[str]=Header(None)):
        service.bot_auth(x_kabutar_bot_secret)
        with service.transaction() as cur:
            row=service._challenge(cur,body.challenge)
            if row['cancelled_at'] or not row['live']:
                raise HTTPException(410,'Kirish so‘rovi tugagan yoki bekor qilingan')
            return {'status':'confirmed' if row['confirmed_at'] else 'pending','mode':row['mode'],
                'verification_code':row['verification_code'],
                'expires_in':max(0,int((row['expires_at']-datetime.now(timezone.utc)).total_seconds())),
                'site':platform.FRONTEND_URL.rstrip('/')}

    @app.post('/auth/telegram/confirm')
    def confirm(body:Confirm,x_kabutar_bot_secret:Optional[str]=Header(None)):
        service.bot_auth(x_kabutar_bot_secret)
        if body.contact_user_id!=body.telegram_user_id:
            raise HTTPException(403,'Faqat o‘zingizning telefoningizni ulashing')
        phone=normalize_phone(body.phone)
        service.rate('telegram-confirm',str(body.telegram_user_id),20)
        with service.transaction() as cur:
            row=service._challenge(cur,body.challenge)
            if row['cancelled_at'] or not row['live']:
                raise HTTPException(410,'Kirish so‘rovi tugagan yoki bekor qilingan')
            if row['confirmed_at']:
                if row['telegram_id']==body.telegram_user_id and row['phone']==phone:
                    return {'status':'confirmed'}
                raise HTTPException(409,'Bu so‘rov boshqa foydalanuvchi tomonidan tasdiqlangan')
            service.check_link_session(cur,row)
            uid=service._resolve_telegram(cur,body.telegram_user_id,phone,body.full_name,row['target_user_id'])
            cur.execute('UPDATE kabutar_auth_challenges SET user_id=%s,telegram_id=%s,phone=%s,confirmed_at=NOW() WHERE challenge_hash=%s',
                (uid,body.telegram_user_id,phone,digest(body.challenge)))
        return {'status':'confirmed'}

    @app.post('/auth/telegram/poll')
    def poll(body:BrowserChallenge,request:Request):
        service.origin(request)
        just_completed=False
        with service.transaction() as cur:
            row=service._challenge(cur,body.challenge,body.browser_secret)
            if row['cancelled_at']:
                return {'status':'cancelled'}
            if row['consumed_at']:
                if (datetime.now(timezone.utc)-row['consumed_at']).total_seconds()>RESULT_SECONDS:
                    return {'status':'expired'}
            elif not row['live']:
                return {'status':'expired'}
            if not row['confirmed_at']:
                return {'status':'pending'}
            if not row['consumed_at']:
                service.check_link_session(cur,row)
            sid=hmac.new(service.key.encode(),('telegram:'+body.challenge+':'+body.browser_secret).encode(),hashlib.sha256).hexdigest()
            created=row['consumed_at'] or datetime.now(timezone.utc)
            if not row['consumed_at']:
                cur.execute('UPDATE kabutar_auth_challenges SET consumed_at=%s WHERE challenge_hash=%s',(created,digest(body.challenge)))
                token=service._issue_cur(cur,row['user_id'],'telegram',sid,created)
                just_completed=True
            else:
                cur.execute('SELECT 1 FROM kabutar_auth_sessions WHERE session_hash=%s AND revoked_at IS NULL AND expires_at>NOW()',(digest(sid),))
                if not cur.fetchone():
                    return {'status':'expired'}
                token=service._session_token(row['user_id'],sid,created,created+timedelta(days=SESSION_DAYS))
        if just_completed:
            service.record_login(row['user_id'],'telegram')
        return {'status':'complete','token':token,'user_id':row['user_id']}

    @app.post('/auth/telegram/cancel')
    def cancel(body:BrowserChallenge,request:Request):
        service.origin(request)
        with service.transaction() as cur:
            row=service._challenge(cur,body.challenge,body.browser_secret)
            # A completed login must be explicitly logged out, not invalidated by
            # a stale page-unload cancellation arriving after the successful poll.
            if not row['consumed_at']:
                cur.execute('UPDATE kabutar_auth_challenges SET cancelled_at=NOW() WHERE challenge_hash=%s',(digest(body.challenge),))
        return {'status':'cancelled' if not row['consumed_at'] else 'complete'}

    @app.post('/auth/logout')
    def logout(body:Logout,request:Request):
        service.origin(request)
        token=service.token(request,body.token)
        claims=service.claims(token)
        if claims.get('admin_korish'):
            return {'ok':True}
        try:
            uid=platform._jwt_tekshir(token)
        except HTTPException as exc:
            if exc.status_code==401:
                return {'ok':True}
            raise
        with service.transaction() as cur:
            service.user_lock(cur,uid)
            if body.all_devices:
                service.disable_legacy(cur,uid)
                cur.execute('UPDATE kabutar_auth_sessions SET revoked_at=NOW() WHERE user_id=%s AND revoked_at IS NULL',(uid,))
                cur.execute('UPDATE kabutar_auth_challenges SET cancelled_at=NOW() WHERE target_user_id=%s AND consumed_at IS NULL',(uid,))
            else:
                session_hash=digest(claims['sid']) if claims.get('sid') else digest(token)
                cur.execute('UPDATE kabutar_auth_sessions SET revoked_at=NOW() WHERE session_hash=%s',(session_hash,))
                cur.execute('UPDATE kabutar_auth_challenges SET cancelled_at=NOW() WHERE link_session_hash=%s AND consumed_at IS NULL',(session_hash,))
        return {'ok':True}

    @app.post('/auth/password/login')
    def password_login(body:PasswordLogin,request:Request):
        service.origin(request)
        identifier=body.identifier.strip().lower()
        service.rate('password-identifier',identifier,10,900)
        service.rate('password-ip',service.ip(request),120,60)
        with service.transaction() as cur:
            uid=None
            if '@' in identifier and not identifier.startswith('@'):
                cur.execute('SELECT user_id FROM google_hisob WHERE LOWER(google_email)=%s',(identifier,))
            elif identifier.startswith('@'):
                cur.execute('SELECT user_id FROM users WHERE LOWER(kabutar_nickname)=%s',(identifier[1:],))
            elif re.fullmatch(r'(kb[- ]?)?\d{6,10}',identifier):
                key='KB-'+re.sub(r'\D','',identifier)
                cur.execute('SELECT user_id FROM users WHERE kabutar_id=%s',(key,))
            else:
                try:
                    phone=normalize_phone(identifier)
                except HTTPException:
                    phone='invalid'
                cur.execute('SELECT user_id FROM kabutar_telegram_identity WHERE phone=%s',(phone,))
            found=cur.fetchone()
            if not found and re.fullmatch(r'\d{9}', identifier):
                cur.execute('SELECT user_id FROM kabutar_telegram_identity WHERE phone=%s', ('+998'+identifier,))
                found=cur.fetchone()
            if found:
                uid=found['user_id']
            cur.execute('SELECT password_hash FROM kabutar_auth_password WHERE user_id=%s',(uid,))
            stored=cur.fetchone()
        match=password_matches(body.password,stored['password_hash'] if stored else service.dummy_password)
        if not uid or not stored or not match:
            raise HTTPException(401,'Kirish ma’lumoti yoki parol noto‘g‘ri')
        with service.transaction() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,31))',(f'password:{uid}',))
            cur.execute('SELECT password_hash FROM kabutar_auth_password WHERE user_id=%s',(uid,))
            current=cur.fetchone()
            if not current or not hmac.compare_digest(current['password_hash'],stored['password_hash']):
                raise HTTPException(401,'Parol o‘zgargan. Qaytadan kiring')
            token=service._issue_cur(cur,uid,'password')
        service.record_login(uid,'password')
        return {'status':'complete','token':token,'user_id':uid}

    @app.post('/auth/password/set')
    def password_set(body:PasswordSet,request:Request):
        service.origin(request)
        token=service.token(request,body.token)
        uid=platform._jwt_tekshir(token)
        claims=service.claims(token)
        if claims.get('admin_korish'):
            raise HTTPException(403,'Ko‘rish rejimida parol o‘zgartirilmaydi')
        service.rate('password-set',str(uid),10,900)
        new_hash=password_hash(body.password)
        sid_hash=digest(claims['sid']) if claims.get('sid') else digest(token)
        with service.transaction() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,31))',(f'password:{uid}',))
            service.user_lock(cur,uid)
            cur.execute('SELECT password_hash FROM kabutar_auth_password WHERE user_id=%s',(uid,))
            current=cur.fetchone()
            cur.execute("SELECT method,created_at>NOW()-INTERVAL '10 minutes' AS recent FROM kabutar_auth_sessions WHERE session_hash=%s AND revoked_at IS NULL",(sid_hash,))
            session=cur.fetchone() or {}
            if not session:
                raise HTTPException(401,'Kirish sessiyasi bekor qilingan. Qaytadan kiring')
            recent_identity=session.get('recent') and session.get('method') in ('telegram','google')
            if current and not (body.reset and recent_identity):
                if not body.current_password or not password_matches(body.current_password,current['password_hash']):
                    raise HTTPException(403,'Amaldagi parolni kiriting yoki Telegram/Google orqali qayta tasdiqlang')
            elif not current and not recent_identity:
                raise HTTPException(403,'Parol qo‘yish uchun Telegram yoki Google orqali qaytadan kiring')
            cur.execute('''INSERT INTO kabutar_auth_password(user_id,password_hash) VALUES(%s,%s)
                ON CONFLICT(user_id) DO UPDATE SET password_hash=EXCLUDED.password_hash,updated_at=NOW()''',(uid,new_hash))
            service.disable_legacy(cur,uid)
            cur.execute('UPDATE kabutar_auth_sessions SET revoked_at=NOW() WHERE user_id=%s AND session_hash<>%s AND revoked_at IS NULL',(uid,sid_hash))
            cur.execute('UPDATE kabutar_auth_challenges SET cancelled_at=NOW() WHERE target_user_id=%s AND consumed_at IS NULL',(uid,))
        return {'ok':True}

    @app.get('/auth/profile/status')
    def profile_status(request:Request,token:Optional[str]=None):
        uid=platform._jwt_tekshir(service.token(request,token))
        return service.profile_status(uid)

    @app.post('/auth/profile/education')
    def education(body:Education,request:Request):
        service.origin(request)
        token=service.token(request,body.token)
        uid=platform._jwt_tekshir(token)
        if service.claims(token).get('admin_korish'):
            raise HTTPException(403,'Ko‘rish rejimida profil o‘zgartirilmaydi')
        if body.role not in ('oquvchi','oqituvchi','ota-ona','mustaqil') or body.language not in ('uz','ru','en'):
            raise HTTPException(422,'Rol yoki ta’lim tili noto‘g‘ri')
        grade=body.class_ or body.grade
        if body.role=='oquvchi' and not grade:
            raise HTTPException(422,'Sinfni tanlang')
        with service.transaction() as cur:
            cur.execute('SELECT role FROM users WHERE user_id=%s FOR UPDATE',(uid,))
            user=cur.fetchone()
            if not user:
                raise HTTPException(401,'Akkaunt topilmadi')
            if user['role'] not in (None,'','kabutar','mustaqil',body.role):
                raise HTTPException(409,'Mavjud ta’lim rolingizni bu oynada almashtirib bo‘lmaydi')
            cur.execute('''UPDATE users SET role=%s,class=%s,asosiy_til=%s,oqituvchi_fani=%s,kabutar_education_ready=TRUE
                WHERE user_id=%s''',(body.role,str(grade) if body.role=='oquvchi' else None,body.language,body.subject if body.role=='oqituvchi' else None,uid))
        return {'ok':True,'profile':platform.joriy_foydalanuvchi(token)}

    @app.post('/auth/invite/claim')
    def invite_claim(body:InviteClaim,request:Request):
        service.origin(request)
        grant=platform._google_registration_tekshir(body.oauth_grant,body.email)
        code=body.kod.strip().upper()
        if not re.fullmatch(r'[A-Z0-9]{12,128}',code):
            raise HTTPException(422,'Muassasa taklif kodi kamida 12 ta harf/raqamdan iborat bo‘lsin')
        service.rate('invite-email',grant['email'],10,900)
        service.rate('invite-ip',service.ip(request),120)
        plain,hashed=platform._xodim_kod_variantlari(code)
        with service.transaction() as cur:
            cur.execute("""SELECT kod AS stored_code,user_id,ishlatildi,
                yaratildi>NOW()-INTERVAL '2 months' AS live FROM xodim_kod
                WHERE kod IN (%s,%s) AND (kod LIKE 'sha256:%%' OR LENGTH(kod)>=12)
                ORDER BY CASE WHEN kod=%s THEN 0 ELSE 1 END LIMIT 1 FOR UPDATE""",(hashed,plain,hashed))
            invite=cur.fetchone()
            if not invite or invite['ishlatildi'] or not invite['live']:
                raise HTTPException(400,'Taklif kodi noto‘g‘ri, ishlatilgan yoki muddati tugagan')
            uid=invite['user_id']
            service.user_lock(cur,uid)
            cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,31))',('google:'+grant['email'],))
            cur.execute('SELECT user_id FROM google_hisob WHERE google_email=%s',(grant['email'],))
            if cur.fetchone():
                raise HTTPException(409,'Bu email allaqachon akkauntga ulangan. Google orqali kiring')
            cur.execute('SELECT user_id FROM users WHERE user_id=%s FOR UPDATE',(uid,))
            if not cur.fetchone():
                raise HTTPException(409,'Taklif qilingan xodim profili topilmadi')
            cur.execute("""SELECT 1 FROM google_hisob WHERE user_id=%s
                UNION ALL SELECT 1 FROM kabutar_telegram_identity WHERE user_id=%s
                UNION ALL SELECT 1 FROM kabutar_auth_password WHERE user_id=%s
                UNION ALL SELECT 1 FROM kabutar_auth_sessions WHERE user_id=%s
                UNION ALL SELECT 1 FROM telefon_hisob WHERE user_id=%s
                UNION ALL SELECT 1 FROM kabutar_auth_security WHERE user_id=%s LIMIT 1""",(uid,uid,uid,uid,uid,uid))
            if cur.fetchone():
                raise HTTPException(409,'Xodim profili allaqachon egasiga ulangan. Mavjud kirish usulidan foydalaning')
            cur.execute("SELECT to_regclass('public.user_accounts') AS t")
            if cur.fetchone()['t']:
                cur.execute('SELECT 1 FROM user_accounts WHERE uid=%s LIMIT 1',(uid,))
                if cur.fetchone():
                    raise HTTPException(409,'Bu xodim profili Telegram botga ulangan. Mavjud akkauntga kiring')
            service.consume_cur(cur,grant)
            cur.execute('INSERT INTO google_hisob(google_email,user_id) VALUES(%s,%s)',(grant['email'],uid))
            cur.execute('UPDATE xodim_kod SET ishlatildi=TRUE WHERE kod=%s',(invite['stored_code'],))
            cur.execute('UPDATE users SET kabutar_education_ready=TRUE WHERE user_id=%s',(uid,))
            token=service._issue_cur(cur,uid,'google')
        service.record_login(uid,'google')
        return {'status':'complete','token':token,'user_id':uid}

    @app.post('/auth/google/link')
    def google_link(body:GoogleLink,request:Request):
        service.origin(request)
        token=service.token(request,body.token)
        uid=platform._jwt_tekshir(token)
        if service.claims(token).get('admin_korish'):
            raise HTTPException(403,'Ko‘rish rejimida akkaunt ulanmaydi')
        grant=platform._google_registration_tekshir(body.oauth_grant,body.email)
        with service.transaction() as cur:
            service.recent_session(cur,token,uid)
            cur.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,31))',('google:'+grant['email'],))
            cur.execute('SELECT user_id FROM google_hisob WHERE google_email=%s',(grant['email'],))
            previous=cur.fetchone()
            if previous and previous['user_id']!=uid:
                raise HTTPException(409,'Bu Google hisobi boshqa Kabutar akkauntiga ulangan')
            service.consume_cur(cur,grant)
            cur.execute('INSERT INTO google_hisob(google_email,user_id) VALUES(%s,%s) ON CONFLICT DO NOTHING',(grant['email'],uid))
        return {'ok':True}
    return service
