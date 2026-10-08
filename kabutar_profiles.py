"""REV104: bitta akkauntdan 10 tagacha profil (oila / sinov profillari).

Bitta kirish (ota-ona, o'qituvchi yoki admin) ichida 10 tagacha aralash profil:
bog'cha bolasi (2-7 yosh), o'quvchi (1-11 sinf), talaba. Har profil — alohida
users qatori, shuning uchun mavzular, AI miya darslari, testlar, natijalar va
ekran vaqti har bola uchun alohida yuradi.

* Profilga kirish faqat EGA tokeni bilan: POST /auth/profiles/{id}/enter
  profil uchun yangi sessiya (method='profile') beradi.
* Profildan chiqilganda o'sha sessiya bekor qilinadi, ega tokeni bilan boshqa
  profilga kiriladi.
* Yosh / sinf / ism ega tomonidan PATCH bilan sozlanadi.
* Admin ham shu yo'l bilan «sinov bola» profillari ochib, bolaning AI
  mavzularini bola ko'zi bilan tekshira oladi (yoshni almashtirib qayta kiradi).
* Profil o'z navbatida profil ocha olmaydi; ko'rish rejimi tokeni ishlamaydi.
"""
from __future__ import annotations

import json
import re
import secrets
from typing import Optional

from fastapi import HTTPException, Request
from pydantic import BaseModel, Field

MAX_PROFILES = 10
PROFILE_ROLES = ('bogcha', 'oquvchi', 'talaba')
ROLE_LABELS = {'bogcha': 'Bog‘cha bolasi', 'oquvchi': 'O‘quvchi', 'talaba': 'Talaba'}
LANGUAGES = ('uz', 'ru', 'en', 'tj', 'kk', 'kz')

SCHEMA = """
CREATE TABLE IF NOT EXISTS kabutar_family_profiles (
 profile_user_id BIGINT PRIMARY KEY REFERENCES users(user_id),
 owner_user_id BIGINT NOT NULL REFERENCES users(user_id),
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 removed_at TIMESTAMPTZ
);
ALTER TABLE users ADD COLUMN IF NOT EXISTS profil_rasm BYTEA;
CREATE INDEX IF NOT EXISTS kabutar_family_profiles_owner ON kabutar_family_profiles(owner_user_id) WHERE removed_at IS NULL;
"""


def _scope():
    try:
        from .modules.curriculum_scope import preschool_group, preschool_group_for_age
    except ImportError:
        from modules.curriculum_scope import preschool_group, preschool_group_for_age
    return preschool_group, preschool_group_for_age


class ProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    role: str = Field(min_length=3, max_length=20)
    age: Optional[int] = Field(default=None, ge=2, le=30)
    age_group: Optional[str] = Field(default=None, max_length=20)
    grade: Optional[int] = Field(default=None, ge=1, le=11)
    language: Optional[str] = Field(default=None, max_length=4)


class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    role: Optional[str] = Field(default=None, min_length=3, max_length=20)
    age: Optional[int] = Field(default=None, ge=2, le=30)
    age_group: Optional[str] = Field(default=None, max_length=20)
    grade: Optional[int] = Field(default=None, ge=1, le=11)
    language: Optional[str] = Field(default=None, max_length=4)


def build_learning(role, age=None, age_group=None, grade=None, language='uz', owner_id=None):
    """Profil turi + yosh/sinf → (users.role, users.class, kabutar_learning_profile)."""
    preschool_group, preschool_group_for_age = _scope()
    if role not in PROFILE_ROLES:
        raise HTTPException(422, 'Profil turi: bog‘cha bolasi, o‘quvchi yoki talaba')
    learning = {'role': role, 'talim_tili': language or 'uz', 'family_owner': int(owner_id) if owner_id is not None else None}
    if role == 'bogcha':
        group = preschool_group(age_group, legacy=True) if age_group else ''
        if age is not None:
            if not 2 <= int(age) <= 7:
                raise HTTPException(422, 'Bog‘cha bolasining yoshi 2 dan 7 gacha bo‘lsin')
            group = group or preschool_group_for_age(age)
            learning['age'] = int(age)
        if not group:
            raise HTTPException(422, 'Bolaning yoshini tanlang (2–7)')
        learning['age_group'] = group
        return 'oquvchi', group, learning
    if role == 'oquvchi':
        if not grade:
            raise HTTPException(422, 'O‘quvchi profili uchun sinfni tanlang (1–11)')
        learning['grade'] = int(grade)
        if age is not None:
            learning['age'] = int(age)
        return 'oquvchi', str(int(grade)), learning
    learning['standalone'] = True
    if age is not None:
        learning['age'] = int(age)
    return 'oquvchi', None, learning


def _clean_name(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()[:80]


def _profile_view(row):
    learning = row.get('kabutar_learning_profile') or {}
    if isinstance(learning, str):
        try:
            learning = json.loads(learning)
        except ValueError:
            learning = {}
    role = learning.get('role') or 'oquvchi'
    return {
        'user_id': int(row['user_id']),
        'name': row.get('full_name') or '',
        'role': role,
        'role_label': ROLE_LABELS.get(role, role),
        'age': learning.get('age'),
        'age_group': learning.get('age_group') or (row.get('class') if role == 'bogcha' else None),
        'grade': learning.get('grade'),
        'language': learning.get('talim_tili') or 'uz',
        'has_photo': bool(row.get('rasm_bormi')),
        'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
    }


def register_profiles(app, platform, service):
    def migrate():
        with service.transaction() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (31104104,))
            cur.execute(SCHEMA)

    app.router.add_event_handler('startup', migrate)

    def caller(request: Request, token=None, write=False):
        tok = service.token(request, token)
        uid = platform._jwt_tekshir(tok)
        claims = service.claims(tok)
        if claims.get('admin_korish'):
            raise HTTPException(403, 'Ko‘rish rejimida profillar boshqarilmaydi')
        if write:
            service.origin(request)
        return uid, claims

    def profile_owner(cur, uid):
        cur.execute('SELECT owner_user_id FROM kabutar_family_profiles WHERE profile_user_id=%s AND removed_at IS NULL', (uid,))
        row = cur.fetchone()
        return int(row['owner_user_id']) if row else None

    def require_owner(cur, uid):
        if profile_owner(cur, uid) is not None:
            raise HTTPException(403, 'Bu profil. Profillarni asosiy akkauntdan boshqaring')

    def owned_profile(cur, owner_id, profile_id, lock=False):
        cur.execute('''SELECT u.user_id,u.full_name,u.class,u.kabutar_learning_profile,f.created_at,
                (u.profil_rasm IS NOT NULL) AS rasm_bormi
            FROM kabutar_family_profiles f JOIN users u ON u.user_id=f.profile_user_id
            WHERE f.profile_user_id=%s AND f.owner_user_id=%s AND f.removed_at IS NULL''' + (' FOR UPDATE OF f' if lock else ''),
            (profile_id, owner_id))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, 'Profil topilmadi')
        return row

    def list_profiles(cur, owner_id):
        cur.execute('''SELECT u.user_id,u.full_name,u.class,u.kabutar_learning_profile,f.created_at,
                (u.profil_rasm IS NOT NULL) AS rasm_bormi
            FROM kabutar_family_profiles f JOIN users u ON u.user_id=f.profile_user_id
            WHERE f.owner_user_id=%s AND f.removed_at IS NULL ORDER BY f.created_at, u.user_id''', (owner_id,))
        return [_profile_view(r) for r in cur.fetchall()]

    def link_parent(cur, owner_id, child_id):
        # Ega ota-ona hisobotlarini (faollik, ekran vaqti, tahlil) shu bola bo'yicha ham ko'radi.
        try:
            cur.execute('SAVEPOINT family_parent')
            cur.execute('''CREATE TABLE IF NOT EXISTS parent_child(
                id SERIAL PRIMARY KEY, parent_id BIGINT NOT NULL, child_id BIGINT NOT NULL)''')
            cur.execute('SELECT 1 FROM parent_child WHERE parent_id=%s AND child_id=%s LIMIT 1', (owner_id, child_id))
            if not cur.fetchone():
                cur.execute('INSERT INTO parent_child(parent_id,child_id) VALUES(%s,%s)', (owner_id, child_id))
            cur.execute('RELEASE SAVEPOINT family_parent')
        except Exception:
            cur.execute('ROLLBACK TO SAVEPOINT family_parent')

    def payload(cur, owner_id):
        cur.execute('SELECT full_name FROM users WHERE user_id=%s', (owner_id,))
        owner = cur.fetchone() or {}
        cur.execute('SELECT 1 FROM admin_akkaunt WHERE uid=%s', (owner_id,))
        is_admin = cur.fetchone() is not None
        profiles = list_profiles(cur, owner_id)
        return {'is_profile': False, 'owner': {'user_id': owner_id, 'name': owner.get('full_name') or '', 'is_admin': is_admin},
                'profiles': profiles, 'max': MAX_PROFILES, 'left': max(0, MAX_PROFILES - len(profiles))}

    @app.get('/auth/profiles')
    def profiles(request: Request, token: Optional[str] = None):
        uid, _ = caller(request, token)
        with service.transaction() as cur:
            owner = profile_owner(cur, uid)
            if owner is not None:
                cur.execute('SELECT full_name FROM users WHERE user_id=%s', (owner,))
                name = (cur.fetchone() or {}).get('full_name') or ''
                return {'is_profile': True, 'owner': {'user_id': owner, 'name': name}, 'profiles': [], 'max': MAX_PROFILES}
            return payload(cur, uid)

    @app.post('/auth/profiles')
    def create_profile(body: ProfileCreate, request: Request, token: Optional[str] = None):
        uid, _ = caller(request, token, write=True)
        service.rate('family-create', str(uid), 30, 3600)
        name = _clean_name(body.name)
        if not name:
            raise HTTPException(422, 'Profil ismini yozing')
        language = body.language if body.language in LANGUAGES else None
        with service.transaction() as cur:
            service.user_lock(cur, uid)
            require_owner(cur, uid)
            cur.execute("SELECT COALESCE(NULLIF(asosiy_til,''),'uz') AS til FROM users WHERE user_id=%s", (uid,))
            owner = cur.fetchone()
            if not owner:
                raise HTTPException(401, 'Akkaunt topilmadi')
            language = language or (owner['til'] if owner['til'] in LANGUAGES else 'uz')
            cur.execute('SELECT COUNT(*) AS n FROM kabutar_family_profiles WHERE owner_user_id=%s AND removed_at IS NULL', (uid,))
            if int(cur.fetchone()['n']) >= MAX_PROFILES:
                raise HTTPException(409, f'Bitta akkauntda ko‘pi bilan {MAX_PROFILES} ta profil bo‘ladi. Avval keraksizini o‘chiring')
            base_role, class_value, learning = build_learning(body.role, body.age, body.age_group, body.grade, language, uid)
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (31091001,))   # quick_start bilan bir xil ID qulfi
            cur.execute('SELECT MIN(user_id) AS eng_kichik FROM users WHERE user_id < 0')
            row = cur.fetchone()
            new_id = (row['eng_kichik'] - 1) if row and row['eng_kichik'] is not None else -1
            cur.execute('''INSERT INTO users(user_id,full_name,role,class,asosiy_til,kabutar_learning_profile,kabutar_education_ready)
                VALUES(%s,%s,%s,%s,%s,%s::jsonb,TRUE)''', (new_id, name, base_role, class_value, language, json.dumps(learning)))
            give_id = getattr(platform, '_kabutar_id_ber', None)
            if give_id:
                try:
                    cur.execute('SAVEPOINT family_kb_id')
                    give_id(cur, new_id)
                    cur.execute('RELEASE SAVEPOINT family_kb_id')
                except Exception:
                    cur.execute('ROLLBACK TO SAVEPOINT family_kb_id')
            cur.execute('INSERT INTO kabutar_family_profiles(profile_user_id,owner_user_id) VALUES(%s,%s)', (new_id, uid))
            link_parent(cur, uid, new_id)
            result = payload(cur, uid)
        result['created_id'] = new_id
        return result

    @app.patch('/auth/profiles/{profile_id}')
    def update_profile(profile_id: int, body: ProfileUpdate, request: Request, token: Optional[str] = None):
        uid, _ = caller(request, token, write=True)
        with service.transaction() as cur:
            service.user_lock(cur, uid)
            require_owner(cur, uid)
            row = owned_profile(cur, uid, profile_id, lock=True)
            current = _profile_view(row)
            role = body.role or current['role']
            changed_role = role != current['role']
            age = body.age if body.age is not None else (None if (changed_role or body.age_group) else current['age'])
            group = body.age_group if body.age_group else (None if (changed_role or body.age is not None) else current['age_group'])
            grade = body.grade if body.grade is not None else (None if changed_role else current['grade'])
            language = body.language if body.language in LANGUAGES else current['language']
            base_role, class_value, learning = build_learning(role, age, group, grade, language, uid)
            name = _clean_name(body.name) if body.name is not None else current['name']
            if not name:
                raise HTTPException(422, 'Profil ismini yozing')
            cur.execute('''UPDATE users SET full_name=%s,role=%s,class=%s,asosiy_til=%s,
                kabutar_learning_profile=%s::jsonb,kabutar_education_ready=TRUE WHERE user_id=%s''',
                (name, base_role, class_value, language, json.dumps(learning), profile_id))
            return payload(cur, uid)

    @app.delete('/auth/profiles/{profile_id}')
    def remove_profile(profile_id: int, request: Request, token: Optional[str] = None):
        uid, _ = caller(request, token, write=True)
        with service.transaction() as cur:
            service.user_lock(cur, uid)
            require_owner(cur, uid)
            owned_profile(cur, uid, profile_id, lock=True)
            # Natijalar o'chirilmaydi (bazada qoladi) — faqat ro'yxatdan olinadi va sessiyalari yopiladi.
            cur.execute('UPDATE kabutar_family_profiles SET removed_at=NOW() WHERE profile_user_id=%s', (profile_id,))
            cur.execute('UPDATE kabutar_auth_sessions SET revoked_at=NOW() WHERE user_id=%s AND revoked_at IS NULL', (profile_id,))
            return payload(cur, uid)

    @app.post('/auth/profiles/{profile_id}/enter')
    def enter_profile(profile_id: int, request: Request, token: Optional[str] = None):
        uid, _ = caller(request, token, write=True)
        service.rate('family-enter', str(uid), 120, 600)
        with service.transaction() as cur:
            require_owner(cur, uid)
            row = owned_profile(cur, uid, profile_id)
            access = service._issue_cur(cur, profile_id, 'profile')
        service.record_login(profile_id, 'profile')
        return {'status': 'complete', 'token': access, 'user_id': int(profile_id), 'profile': _profile_view(row)}

    platform._kabutar_family_profile_owner = lambda cur, uid: profile_owner(cur, uid)
    return {'max': MAX_PROFILES}
