"""Kabutar member-controlled blocks and private moderation reports.

All operations use revocable bearer sessions. Blocking is a current-contact
operation; unblocking is always owned by the blocker. Report content is never
returned to the reported user and attachment bytes are never copied.
"""
from __future__ import annotations

import re
from typing import Literal, Optional

from fastapi import HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

MAX_USER_ID = 9223372036854775807
SCHEMA = """
CREATE TABLE IF NOT EXISTS kabutar_user_blocks (
    blocker_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    blocked_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(blocker_id, blocked_id),
    CHECK(blocker_id <> blocked_id)
);
CREATE INDEX IF NOT EXISTS kabutar_user_blocks_reverse_idx
    ON kabutar_user_blocks(blocked_id, blocker_id);
CREATE TABLE IF NOT EXISTS kabutar_safety_reports (
    id BIGSERIAL PRIMARY KEY,
    reporter_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    reported_user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    message_id BIGINT,
    reason TEXT NOT NULL CHECK(reason IN ('spam','abuse','unsafe','other')),
    detail TEXT NOT NULL DEFAULT '',
    message_excerpt TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','reviewed','closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS kabutar_safety_reports_status_id_idx
    ON kabutar_safety_reports(status, id DESC);
CREATE INDEX IF NOT EXISTS kabutar_safety_reports_reporter_idx
    ON kabutar_safety_reports(reporter_id, id DESC);
"""


class PeerAction(BaseModel):
    user_id: int = Field(gt=0, le=MAX_USER_ID, strict=True)


class ReportAction(BaseModel):
    user_id: Optional[int] = Field(default=None, gt=0, le=MAX_USER_ID, strict=True)
    message_id: Optional[int] = Field(default=None, gt=0, le=MAX_USER_ID, strict=True)
    reason: Literal['spam', 'abuse', 'unsafe', 'other']
    detail: str = Field(default='', max_length=1000)


def _policy():
    if __package__:
        from . import kabutar_policy
    else:
        import kabutar_policy
    return kabutar_policy


def _plain(value, maximum):
    # Preserve readable Uzbek/newlines; discard NUL, bidi overrides and controls.
    text = str(value or '')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u202a-\u202e\u2066-\u2069]', '', text)
    return text.strip()[:maximum]


def _iso(value):
    return value.isoformat() if hasattr(value, 'isoformat') else value


class SafetyService:
    def __init__(self, platform, auth):
        self.p, self.auth = platform, auth

    def migrate(self):
        with self.auth.transaction() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (45091031,))
            cur.execute(SCHEMA)

    def actor(self, request, mutate=False):
        authorization = request.headers.get('authorization', '')
        scheme, _, token = authorization.partition(' ')
        if scheme.lower() != 'bearer' or not token.strip():
            raise HTTPException(401, 'Hisobingizga kiring')
        token = token.strip()
        actor_id = self.p._jwt_tekshir(token)
        # Education previews cannot read or change another user's private
        # contacts, blocks or complaints. Review uses the administrator's own session.
        if self.auth.claims(token).get('admin_korish'):
            raise HTTPException(403, 'Ko‘rish rejimida Kabutar xavfsizlik ma’lumotlari ochilmaydi')
        return int(actor_id)

    @staticmethod
    def owns_block(cur, actor_id, peer_id):
        cur.execute('SELECT 1 FROM kabutar_user_blocks WHERE blocker_id=%s AND blocked_id=%s',
                    (actor_id, peer_id))
        return cur.fetchone() is not None

    def block(self, actor_id, peer_id):
        if actor_id == peer_id:
            raise HTTPException(422, 'O‘zingizni bloklab bo‘lmaydi')
        with self.auth.transaction() as cur:
            self.auth.user_lock(cur, actor_id)
            if self.owns_block(cur, actor_id, peer_id):
                return {'ok': True, 'user_id': peer_id, 'blocked': True}
            _policy().require_direct(cur, actor_id, peer_id, ignore_blocks=True)
            cur.execute('SELECT COUNT(*) AS total FROM kabutar_user_blocks WHERE blocker_id=%s', (actor_id,))
            if int(cur.fetchone()['total']) >= 2000:
                raise HTTPException(409, 'Bloklanganlar ro‘yxati to‘lgan. Avval kerak bo‘lmagan blokni olib tashlang')
            cur.execute('''INSERT INTO kabutar_user_blocks(blocker_id,blocked_id)
                           VALUES(%s,%s) ON CONFLICT(blocker_id,blocked_id) DO NOTHING''', (actor_id, peer_id))
        return {'ok': True, 'user_id': peer_id, 'blocked': True}

    def unblock(self, actor_id, peer_id):
        # No contact-policy check here: the block itself denies that policy.
        with self.auth.transaction() as cur:
            self.auth.user_lock(cur, actor_id)
            cur.execute('DELETE FROM kabutar_user_blocks WHERE blocker_id=%s AND blocked_id=%s',
                        (actor_id, peer_id))
        return {'ok': True, 'user_id': peer_id, 'blocked': False}

    def blocks(self, actor_id):
        with self.auth.transaction() as cur:
            cur.execute('''SELECT b.blocked_id AS user_id,u.full_name,b.created_at
                FROM kabutar_user_blocks b JOIN users u ON u.user_id=b.blocked_id
                WHERE b.blocker_id=%s ORDER BY b.created_at DESC,b.blocked_id LIMIT 2000''', (actor_id,))
            return {'blocks': [{'user_id': int(r['user_id']), 'full_name': r.get('full_name') or 'Kabutar foydalanuvchisi',
                                'created_at': _iso(r.get('created_at'))} for r in cur.fetchall()]}

    def report(self, actor_id, body):
        if body.user_id is None and body.message_id is None:
            raise HTTPException(422, 'Shikoyat uchun foydalanuvchi yoki xabarni tanlang')
        with self.auth.transaction() as cur:
            peer_id, excerpt = body.user_id, ''
            if body.message_id is not None:
                # Reporting remains possible when the offending sender blocked
                # the recipient. This private path ignores only the block edge;
                # current institution/class permission and participation remain.
                metadata = _policy().require_message(cur, actor_id, body.message_id, ignore_blocks=True)
                sender_id = int(metadata['yuboruvchi_user_id'])
                if sender_id == actor_id:
                    raise HTTPException(422, 'O‘z xabaringiz ustidan shikoyat yuborib bo‘lmaydi')
                if peer_id is not None and peer_id != sender_id:
                    raise HTTPException(422, 'Tanlangan xabar shu foydalanuvchiga tegishli emas')
                peer_id = sender_id
                cur.execute('''SELECT LEFT(matn,2000) AS matn FROM chat_xabarlari
                               WHERE id=%s AND COALESCE(ochirilgan,FALSE)=FALSE''', (body.message_id,))
                message = cur.fetchone()
                if not message:
                    raise HTTPException(404, 'Xabar topilmadi')
                excerpt = _plain(message.get('matn'), 2000)
            else:
                if peer_id == actor_id:
                    raise HTTPException(422, 'O‘zingiz ustidan shikoyat yuborib bo‘lmaydi')
                # A user can still report a peer they personally blocked.
                if not self.owns_block(cur, actor_id, peer_id):
                    if not _policy().allow_direct(cur, actor_id, peer_id, ignore_blocks=True):
                        raise HTTPException(403, 'Bu foydalanuvchi ustidan shikoyat yuborish ruxsati yo‘q')
            detail = _plain(body.detail, 1000)
            # Serialize own submissions; a repeated double-click reuses one report.
            self.auth.user_lock(cur, actor_id)
            cur.execute('''SELECT id FROM kabutar_safety_reports
                WHERE reporter_id=%s AND reported_user_id=%s
                  AND message_id IS NOT DISTINCT FROM %s AND reason=%s AND detail=%s
                  AND created_at > NOW()-INTERVAL '10 minutes'
                ORDER BY id DESC LIMIT 1''', (actor_id, peer_id, body.message_id, body.reason, detail))
            existing = cur.fetchone()
            if existing:
                return {'ok': True, 'report_id': int(existing['id'])}
            cur.execute('''INSERT INTO kabutar_safety_reports
                (reporter_id,reported_user_id,message_id,reason,detail,message_excerpt)
                VALUES(%s,%s,%s,%s,%s,%s) RETURNING id''',
                (actor_id, peer_id, body.message_id, body.reason, detail, excerpt))
            return {'ok': True, 'report_id': int(cur.fetchone()['id'])}

    def reports(self, actor_id, before_id=None):
        with self.auth.transaction() as cur:
            cur.execute('SELECT 1 FROM admin_akkaunt WHERE uid=%s', (actor_id,))
            if not cur.fetchone():
                raise HTTPException(403, 'Shikoyatlarni faqat vakolatli administrator ko‘ra oladi')
            cur.execute('''SELECT r.id,r.reporter_id,r.reported_user_id,r.message_id,
                   r.reason,r.detail,r.message_excerpt,r.status,r.created_at,
                   reporter.full_name AS reporter_name,reported.full_name AS reported_name
                FROM kabutar_safety_reports r
                LEFT JOIN users reporter ON reporter.user_id=r.reporter_id
                LEFT JOIN users reported ON reported.user_id=r.reported_user_id
                WHERE (%s::bigint IS NULL OR r.id < %s)
                ORDER BY r.id DESC LIMIT 50''', (before_id, before_id))
            rows = [dict(r) for r in cur.fetchall()]
            for row in rows:
                row['created_at'] = _iso(row.get('created_at'))
            return {'reports': rows, 'next_before_id': int(rows[-1]['id']) if len(rows) == 50 else None}


def register_safety(app, platform, auth_service):
    service = SafetyService(platform, auth_service)
    app.router.add_event_handler('startup', service.migrate)

    def response(value):
        return JSONResponse(value, headers={'Cache-Control': 'private, no-store', 'Referrer-Policy': 'no-referrer'})

    def mutate_actor(request, scope, limit=20, seconds=60):
        auth_service.origin(request)
        actor_id = service.actor(request, mutate=True)
        auth_service.rate(scope, str(actor_id), limit, seconds)
        return actor_id

    @app.post('/api/kabutar/safety/block')
    def block(body: PeerAction, request: Request):
        actor_id = mutate_actor(request, 'safety-block')
        return response(service.block(actor_id, body.user_id))

    @app.post('/api/kabutar/safety/unblock')
    def unblock(body: PeerAction, request: Request):
        actor_id = mutate_actor(request, 'safety-unblock')
        return response(service.unblock(actor_id, body.user_id))

    @app.get('/api/kabutar/safety/blocks')
    def blocks(request: Request):
        actor_id = service.actor(request)
        auth_service.rate('safety-block-list', str(actor_id), 30, 60)
        return response(service.blocks(actor_id))

    @app.post('/api/kabutar/safety/report')
    def report(body: ReportAction, request: Request):
        actor_id = mutate_actor(request, 'safety-report-minute', 5, 60)
        auth_service.rate('safety-report-day', str(actor_id), 30, 86400)
        return response(service.report(actor_id, body))

    @app.get('/api/admin/kabutar/reports')
    def reports(request: Request, before_id: Optional[int] = Query(default=None, gt=0, le=MAX_USER_ID)):
        actor_id = service.actor(request)
        auth_service.rate('safety-report-review', str(actor_id), 30, 60)
        return response(service.reports(actor_id, before_id))

    return service
