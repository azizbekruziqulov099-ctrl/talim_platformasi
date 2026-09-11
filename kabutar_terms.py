"""Versioned acceptance of Kabutar community rules before posting content."""
from __future__ import annotations
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

VERSION = '2026-09-10.1'
RULES = [
    {'id':'purpose','text':'Kabutardan tasdiqlangan muassasa doirasida ta’lim va ishga oid aloqa uchun foydalanaman.'},
    {'id':'respect','text':'Haqorat, tahdid, ta’qib, kamsitish va boshqa odamni bezovta qilishga yo‘l qo‘ymayman.'},
    {'id':'privacy','text':'Boshqalarning shaxsiy ma’lumoti, rasmi, ovozi yoki hujjatini tegishli ruxsatsiz tarqatmayman.'},
    {'id':'content','text':'Zararli fayl, spam, zo‘ravonlikni targ‘ib qiluvchi yoki bolalar uchun nomaqbul material yubormayman.'},
    {'id':'safety','text':'Nojo‘ya xabar haqida shikoyat yuborish va foydalanuvchini bloklash mumkinligini tushundim.'},
]
SCHEMA = '''CREATE TABLE IF NOT EXISTS kabutar_terms_acceptance_v45(
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    accepted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(user_id,version)
);'''

class TermsAcceptance(BaseModel):
    version: str = Field(min_length=1,max_length=40)
    accepted: bool = Field(strict=True)


def is_accepted(cur,user_id):
    cur.execute('SELECT 1 FROM kabutar_terms_acceptance_v45 WHERE user_id=%s AND version=%s', (int(user_id),VERSION))
    return cur.fetchone() is not None


def ensure_accepted(cur,user_id):
    if not is_accepted(cur,user_id):
        raise HTTPException(428,'Xabar yoki media yuborishdan oldin Kabutar foydalanish qoidalarini o‘qib, qabul qiling.')


def register_terms(app,platform,auth_service):
    def migrate():
        with auth_service.transaction() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (45091032,))
            cur.execute(SCHEMA)
    app.router.add_event_handler('startup',migrate)

    def actor(request,mutate=False):
        scheme,_,token=request.headers.get('authorization','').partition(' ')
        if scheme.lower()!='bearer' or not token.strip():
            raise HTTPException(401,'Hisobingizga kiring')
        uid=platform._jwt_tekshir(token.strip())
        if auth_service.claims(token.strip()).get('admin_korish'):
            raise HTTPException(403,'Ko‘rish rejimida boshqa foydalanuvchining Kabutar sozlamalari ochilmaydi')
        return int(uid)

    def response(accepted):
        return JSONResponse({'version':VERSION,'accepted':bool(accepted),'rules':RULES},headers={'Cache-Control':'private, no-store','Referrer-Policy':'no-referrer'})

    @app.get('/api/kabutar/safety/terms')
    def get_terms(request:Request):
        uid=actor(request)
        auth_service.rate('kabutar-terms-read',str(uid),60,60)
        with auth_service.transaction() as cur:
            return response(is_accepted(cur,uid))

    @app.post('/api/kabutar/safety/terms')
    def accept_terms(body:TermsAcceptance,request:Request):
        auth_service.origin(request)
        uid=actor(request,mutate=True)
        auth_service.rate('kabutar-terms',str(uid),12,60)
        if body.version!=VERSION or body.accepted is not True:
            raise HTTPException(422,'Amaldagi qoidalarni o‘qib, qabul qilishingizni tasdiqlang')
        with auth_service.transaction() as cur:
            cur.execute('INSERT INTO kabutar_terms_acceptance_v45(user_id,version) VALUES(%s,%s) ON CONFLICT DO NOTHING', (uid,VERSION))
        return response(True)
    return {'version':VERSION}
