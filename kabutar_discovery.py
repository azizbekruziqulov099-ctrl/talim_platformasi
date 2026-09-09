"""Authenticated exact Kabutar discovery with opt-in verified-phone lookup.

Discovery returns only a small profile card. It never creates a chat membership,
reads messages, searches partial phone numbers, or elevates an account's role.
"""
from __future__ import annotations

import re
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

NICKNAME = re.compile(r'^[a-z][a-z0-9_]{4,31}$', re.ASCII)
SCHEMA = """
ALTER TABLE users ADD COLUMN IF NOT EXISTS kabutar_nickname TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_discoverable BOOLEAN NOT NULL DEFAULT FALSE;
CREATE UNIQUE INDEX IF NOT EXISTS users_kabutar_nickname_uq
    ON users(LOWER(kabutar_nickname)) WHERE kabutar_nickname IS NOT NULL;
"""


class DiscoverySettings(BaseModel):
    nickname: Optional[str] = Field(default=None, max_length=33)
    phone_discoverable: bool = False


def nickname_value(value):
    value = str(value or '').strip().lower()
    if value.startswith('@'):
        value = value[1:]
    if not value:
        return None
    if not NICKNAME.fullmatch(value):
        raise HTTPException(422, 'Nik 5–32 belgidan iborat bo‘lsin: birinchi belgi lotin harfi, keyingilari lotin harfi, raqam yoki _')
    return value


def parse_lookup(value):
    text = str(value or '').strip()
    if not text or len(text) > 80:
        raise HTTPException(422, 'KB raqami, @nik yoki + bilan to‘liq telefon raqamini kiriting')
    if text.startswith('@'):
        nickname = nickname_value(text)
        if not nickname:
            raise HTTPException(422, 'To‘liq @nikni kiriting')
        return 'nickname', nickname
    if text.startswith('+'):
        phone = re.sub(r'[\s()\-]', '', text)
        if not re.fullmatch(r'\+[1-9][0-9]{9,14}', phone, re.ASCII):
            raise HTTPException(422, 'Telefonni to‘liq xalqaro formatda kiriting: +998901234567')
        return 'phone', phone
    match = re.fullmatch(r'(?:KB[ -]?)?([0-9]{6,10})', text, re.IGNORECASE | re.ASCII)
    if match:
        return 'kabutar_id', 'KB-' + match.group(1)
    raise HTTPException(422, 'KB 6–10 raqam, nik @ bilan, telefon esa + bilan yoziladi')


def public_card(row):
    role = {
        'oqituvchi': "O'qituvchi", 'oquvchi': "O'quvchi", 'ota-ona': 'Ota-ona',
        'ota_ona': 'Ota-ona', 'mustaqil': "Mustaqil o'rganuvchi",
        "O'qituvchi": "O'qituvchi", "O'quvchi": "O'quvchi", 'Ota-ona': 'Ota-ona',
    }.get(row.get('role'), 'Kabutar foydalanuvchisi')
    # Do not return phone, Telegram ID, family names, school or administrative roles.
    return {
        'user_id': int(row['user_id']),
        'full_name': row.get('full_name') or 'Kabutar foydalanuvchisi',
        'kabutar_id': row.get('kabutar_id'),
        'kabutar_nickname': row.get('kabutar_nickname'),
        'rasm_bormi': bool(row.get('rasm_bormi')),
        'rollar': [{'turi': 'foydalanuvchi', 'muassasa': '', 'rol': role}],
        'qisqa': role,
    }


class DiscoveryService:
    def __init__(self, platform, auth):
        self.platform, self.auth = platform, auth

    def migrate(self):
        with self.auth.transaction() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (31093110,))
            cur.execute(SCHEMA)

    def actor(self, request, mutate=False):
        # New routes require Authorization; no bearer credentials in lookup URLs.
        authorization = request.headers.get('authorization', '')
        scheme, _, token = authorization.partition(' ')
        if scheme.lower() != 'bearer' or not token.strip():
            raise HTTPException(401, 'Hisobingizga kiring')
        token = token.strip()
        user_id = self.platform._jwt_tekshir(token)
        if mutate and self.auth.claims(token).get('admin_korish'):
            raise HTTPException(403, 'Ko‘rish rejimida profil o‘zgartirilmaydi')
        return user_id

    def profile(self, cur, user_id):
        cur.execute('''SELECT u.kabutar_nickname,u.phone_discoverable,t.phone,t.verified_at
            FROM users u LEFT JOIN kabutar_telegram_identity t ON t.user_id=u.user_id
            WHERE u.user_id=%s''', (user_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(401, 'Hisob topilmadi')
        phone = row.get('phone') if row.get('verified_at') else None
        return {
            'nickname': row.get('kabutar_nickname'),
            'phone_discoverable': bool(row.get('phone_discoverable') and phone),
            'phone_verified': bool(phone),
            'phone_masked': phone[:4] + '•••••' + phone[-4:] if phone else None,
        }

    def update(self, user_id, body):
        nickname = nickname_value(body.nickname)
        try:
            with self.auth.transaction() as cur:
                self.auth.user_lock(cur, user_id)
                # Auth linking uses the same user lock; verification cannot switch
                # identity while this preference change is being applied.
                profile = self.profile(cur, user_id)
                if body.phone_discoverable and not profile['phone_verified']:
                    raise HTTPException(422, 'Avval profilingizga Telegram orqali o‘z telefoningizni tasdiqlab ulang')
                if nickname:
                    # Ensure nickname-only new accounts also have the unchanged KB
                    # needed by the existing first-message permission check.
                    self.platform._kabutar_id_ber(cur, user_id)
                cur.execute('''UPDATE users SET kabutar_nickname=%s,phone_discoverable=%s
                    WHERE user_id=%s''', (nickname, body.phone_discoverable, user_id))
                return self.profile(cur, user_id)
        except Exception as exc:
            if getattr(exc, 'pgcode', None) == '23505':
                raise HTTPException(409, 'Bu nik band. Boshqa nik tanlang') from None
            raise

    def find(self, user_id, query):
        kind, value = parse_lookup(query)
        select = '''SELECT u.user_id,u.full_name,u.role,u.kabutar_id,u.kabutar_nickname,
            (u.profil_rasm IS NOT NULL) AS rasm_bormi FROM users u'''
        # All three routes follow the existing exact-KB profile lookup policy.
        # Message and attachment permissions remain enforced by their own routes.
        with self.auth.transaction() as cur:
            if kind == 'phone':
                cur.execute(select + ''' JOIN kabutar_telegram_identity t ON t.user_id=u.user_id
                    WHERE t.phone=%s AND t.verified_at IS NOT NULL AND u.phone_discoverable=TRUE LIMIT 1''', (value,))
            elif kind == 'nickname':
                cur.execute(select + ' WHERE LOWER(u.kabutar_nickname)=%s LIMIT 1', (value,))
            else:
                cur.execute(select + ' WHERE u.kabutar_id=%s LIMIT 1', (value,))
            row = cur.fetchone()
            if not row:
                # Same response for absent, private and unverified phone numbers.
                raise HTTPException(404, 'Foydalanuvchi topilmadi yoki bu usulda topishga ruxsat bermagan')
            if int(row['user_id']) == user_id:
                raise HTTPException(400, 'Bu sizning o‘z profilingiz')
            return public_card(row)


def register_discovery(app, platform, auth_service):
    service = DiscoveryService(platform, auth_service)
    app.router.add_event_handler('startup', service.migrate)

    def response(data):
        return JSONResponse(data, headers={'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'})

    @app.get('/auth/profile/discovery')
    def get_discovery(request: Request):
        user_id = service.actor(request)
        with auth_service.transaction() as cur:
            result = service.profile(cur, user_id)
        return response(result)

    @app.post('/auth/profile/discovery')
    def set_discovery(body: DiscoverySettings, request: Request):
        auth_service.origin(request)
        user_id = service.actor(request, mutate=True)
        auth_service.rate('discovery-settings', str(user_id), 12, 60)
        return response(service.update(user_id, body))

    @app.get('/api/kabutar/find')
    def find_contact(query: str, request: Request):
        user_id = service.actor(request)
        auth_service.rate('discovery-user', str(user_id), 30, 60)
        auth_service.rate('discovery-ip', auth_service.ip(request), 120, 60)
        return response(service.find(user_id, query))

    return service
