"""REV45: authorized, configurable military school daily routines.

Weekly entries describe the published plan, never inferred attendance or an
actual event feed. No timetable is invented for a newly created military school.
"""
import json
import re
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool

if __package__ and '.' in __package__:
    from ..kabutar_policy import memberships, _active
else:
    from kabutar_policy import memberships, _active

KINDS = {'dars', 'saf', 'mashq', 'ovqat', 'dam', 'mustaqil', 'togarak', 'ketish', 'boshqa'}
MAX_DAILY_ENTRIES = 32
MAX_WEEKLY_ENTRIES = MAX_DAILY_ENTRIES * 7
ZONE = ZoneInfo('Asia/Tashkent')


def fail(status, message):
    raise HTTPException(status_code=status, detail=message)


def positive_id(value):
    if isinstance(value, bool) or not re.fullmatch(r'[1-9][0-9]{0,17}', str(value)):
        fail(422, 'Maktab yoki foydalanuvchi ID raqami noto‘g‘ri.')
    return int(value)


def validate_entries(value):
    if not isinstance(value, list) or len(value) > MAX_WEEKLY_ENTRIES:
        fail(422, f'Haftalik kun tartibida ko‘pi bilan {MAX_WEEKLY_ENTRIES} ta band bo‘lishi mumkin.')
    cleaned = []
    for entry in value:
        if not isinstance(entry, dict):
            fail(422, 'Kun tartibi bandi noto‘g‘ri.')
        day = entry.get('day')
        if isinstance(day, bool) or not isinstance(day, int) or day not in range(1, 8):
            fail(422, 'Hafta kuni 1–7 oralig‘ida bo‘lishi kerak.')
        start, end = entry.get('start'), entry.get('end')
        if not isinstance(start, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', start):
            fail(422, 'Boshlanish vaqti HH:MM shaklida bo‘lishi kerak.')
        if end and (not isinstance(end, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', end) or end <= start):
            fail(422, 'Tugash vaqti boshlanishdan keyin, shu kun ichida bo‘lishi kerak.')
        if end is None:
            end = ''
        if not isinstance(end, str):
            fail(422, 'Tugash vaqti noto‘g‘ri.')
        week = entry.get('week', 'all')
        if not isinstance(week, str) or week not in {'all', 'odd', 'even'}:
            fail(422, 'Hafta turi har hafta, toq yoki juft bo‘lishi kerak.')
        title = entry.get('title')
        if not isinstance(title, str) or not 2 <= len(title.strip()) <= 120 or any(ord(c) < 32 for c in title):
            fail(422, 'Mashg‘ulot nomini 2–120 belgi bilan yozing.')
        kind = entry.get('kind', 'boshqa')
        if not isinstance(kind, str) or kind not in KINDS:
            fail(422, 'Mashg‘ulot turini tanlang.')
        cleaned.append({'day': day, 'start': start, 'end': end, 'title': title.strip(), 'kind': kind, 'week': week})
    cleaned.sort(key=lambda e: (e['day'], e['start'], e['end']))
    for day in range(1, 8):
        rows = [e for e in cleaned if e['day'] == day]
        if len(rows) > MAX_DAILY_ENTRIES:
            fail(422, f'Bir kun uchun ko‘pi bilan {MAX_DAILY_ENTRIES} ta band kiriting.')
        for week in ('odd', 'even'):
            weekly = [e for e in rows if e['week'] in {'all', week}]
            if any(weekly[i]['start'] < (weekly[i - 1]['end'] or weekly[i - 1]['start']) or weekly[i]['start'] == weekly[i - 1]['start'] for i in range(1, len(weekly))):
                fail(422, 'Bir kundagi mashg‘ulot vaqtlarini ustma-ust qo‘ymang.')
    return cleaned


def routine_state(entries, now=None):
    now = now or datetime.now(ZONE)
    if now.tzinfo is not None:
        now = now.astimezone(ZONE)
    clock = now.strftime('%H:%M')
    week = 'odd' if now.isocalendar().week % 2 else 'even'
    today = [dict(e, status='current' if (e['start'] <= clock < e['end'] if e.get('end') else e['start'] == clock) else 'done' if (e.get('end') or e['start']) <= clock else 'next')
             for e in entries if e['day'] == now.isoweekday() and e.get('week', 'all') in {'all', week}]
    return {'date': now.date().isoformat(), 'time': clock, 'server_now': now.replace(tzinfo=ZONE).isoformat(), 'weekday': now.isoweekday(), 'week': week, 'timezone': 'Asia/Tashkent', 'today': today}


def routine_preset():
    """Editable draft matching the supplied school-day outline.

    Six study days are a selectable draft template, not a published school plan.
    Director can edit/remove days and every start/end before saving.
    The unspecified meal/rest split is a labelled 30/30-minute draft assumption.
    """
    result = []
    for day in range(1, 7):
        rows = [('07:30', '08:00', 'Nonushta · yotoqxonada qoluvchilar', 'ovqat')]
        for lesson in range(1, 6):
            hour = 7 + lesson
            rows.append((f'{hour:02d}:00', f'{hour:02d}:50', f'{lesson}-dars', 'dars'))
            if lesson < 5:
                rows.append((f'{hour:02d}:50', f'{hour+1:02d}:00', 'Tanaffus', 'dam'))
        rows.extend([
            ('12:50', '13:00', 'Tushlikka tayyorgarlik', 'dam'),
            ('13:00', '13:30', 'Tushlik · barcha o‘quvchilar', 'ovqat'),
            ('13:30', '14:00', 'Dam olish va sayr', 'dam'),
            ('14:00', '14:50', '6-dars', 'dars'),
            ('14:50', '15:00', 'Tanaffus', 'dam'),
            ('15:00', '15:45', 'To‘garak · 1-mashg‘ulot', 'togarak'),
            ('15:45', '16:30', 'To‘garak · 2-mashg‘ulot', 'togarak'),
            ('16:30', '', 'Yo‘qlama va uyga/yotoqxonaga chiqish', 'ketish'),
            ('18:00', '', 'Kechki ovqat · yotoqxonada qoluvchilar', 'ovqat'),
        ])
        result.extend(dict(day=day, start=start, end=end, title=title, kind=kind, week='all') for start,end,title,kind in rows)
    return result


class MilitarySchoolService:
    def __init__(self, platform):
        self.platform = platform

    @contextmanager
    def transaction(self):
        conn = self.platform._db()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def migrate(self):
        with self.transaction() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', (45091040,))
            self.platform._maktab_jadvali(cur)
            cur.execute("ALTER TABLE maktablar ADD COLUMN IF NOT EXISTS maktab_turi TEXT NOT NULL DEFAULT 'oddiy'")
            cur.execute('''CREATE TABLE IF NOT EXISTS maktab_kun_tartibi_v45(
                maktab_id BIGINT PRIMARY KEY REFERENCES maktablar(id) ON DELETE CASCADE,
                entries JSONB NOT NULL DEFAULT '[]'::jsonb,
                revision INTEGER NOT NULL DEFAULT 1,
                updated_by BIGINT NOT NULL REFERENCES users(user_id),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')

    def actor(self, request):
        header = request.headers.get('authorization', '')
        token = header[7:].strip() if header.lower().startswith('bearer ') else request.query_params.get('token', '')
        if not token:
            fail(401, 'Hisobingizga kiring.')
        return int(self.platform._jwt_tekshir(token))

    def context(self, cur, actor_id, school_id=None, child_id=None):
        # Global admins manage institution plans; their role is read from the
        # authoritative admin table, never a frontend or user-profile role.
        cur.execute('SELECT 1 FROM admin_akkaunt WHERE uid=%s', (actor_id,))
        admin = bool(cur.fetchone())
        rows = memberships(cur, actor_id)
        permitted = {int(r['inst_id']) for r in rows if r['kind'] == 'maktab'}
        if child_id is not None:
            child_id = positive_id(child_id)
            cur.execute("SELECT to_regclass('public.parent_child') AS name")
            if not (cur.fetchone() or {}).get('name'):
                fail(403, 'Farzand bilan bog‘lanish tasdiqlanmagan.')
            cur.execute(f'SELECT 1 FROM parent_child pc WHERE parent_id=%s AND child_id=%s AND {_active("pc")}', (actor_id, child_id))
            if not cur.fetchone():
                fail(403, 'Bu farzandning kun tartibiga ruxsat yo‘q.')
            child_schools = {int(r['inst_id']) for r in memberships(cur, child_id) if r['kind'] == 'maktab' and r['role'] == 'student'}
            permitted &= child_schools
        requested = positive_id(school_id) if school_id is not None else None
        if requested is not None and requested not in permitted and (not admin or child_id is not None):
            fail(403, 'Bu maktabdagi faol a’zolik tasdiqlanmagan.')
        ids = sorted(permitted)[:50]
        if requested and requested not in ids:
            ids.append(requested)
        if not ids:
            return None, [], False
        cur.execute(f'''SELECT m.id,m.nomi,COALESCE(to_jsonb(m)->>'maktab_turi','oddiy') AS maktab_turi,
                         to_jsonb(m)->>'direktor_user_id' AS direktor_user_id
                         FROM maktablar m WHERE m.id=ANY(%s) AND {_active('m')} ORDER BY m.nomi,m.id LIMIT 51''', (ids,))
        schools = [dict(s) for s in cur.fetchall() if s['maktab_turi'] == 'harbiy']
        if not schools:
            return None, [], False
        school = next((s for s in schools if int(s['id']) == requested), None) if requested else schools[0]
        if not school:
            return None, [], False
        direct_member = any(r['kind'] == 'maktab' and int(r['inst_id']) == int(school['id']) and r['role'] == 'staff' and r.get('label') in {'direktor', 'director'} for r in rows)
        editor = child_id is None and (admin or direct_member)
        return school, [{'id': s['id'], 'name': s['nomi']} for s in schools], editor

    def enable_existing(self, actor_id, school_id):
        school_id = positive_id(school_id)
        with self.transaction() as cur:
            cur.execute('SELECT 1 FROM admin_akkaunt WHERE uid=%s', (actor_id,))
            admin = bool(cur.fetchone())
            member = any(r['kind'] == 'maktab' and int(r['inst_id']) == school_id and r['role'] == 'staff' and r.get('label') in {'direktor', 'director'} for r in memberships(cur, actor_id))
            if not (admin or member):
                fail(403, 'Maktab turini faqat administrator yoki shu maktab direktori o‘zgartiradi.')
            cur.execute(f"UPDATE maktablar m SET maktab_turi='harbiy' WHERE id=%s AND {_active('m')} RETURNING id,nomi", (school_id,))
            if not cur.fetchone():
                fail(404, 'Faol maktab topilmadi.')
            return {'enabled': True, 'school_id': school_id}

    def read(self, actor_id, school_id=None, child_id=None):
        with self.transaction() as cur:
            school, schools, editor = self.context(cur, actor_id, school_id, child_id)
            if not school:
                if school_id and child_id is None:
                    # An explicit institution manager can enable military features
                    # for this school only. Students/parents never see this control.
                    school_id = positive_id(school_id)
                    cur.execute('SELECT 1 FROM admin_akkaunt WHERE uid=%s', (actor_id,))
                    admin = bool(cur.fetchone())
                    manager = any(r['kind'] == 'maktab' and int(r['inst_id']) == school_id and r['role'] == 'staff' and r.get('label') in {'direktor', 'director'} for r in memberships(cur, actor_id))
                    if admin or manager:
                        cur.execute(f'SELECT id,nomi FROM maktablar m WHERE id=%s AND {_active("m")}', (school_id,))
                        ordinary = cur.fetchone()
                        if ordinary:
                            return {'enabled': False, 'can_enable': True, 'school_id': ordinary['id'], 'school_name': ordinary['nomi']}
                return {'enabled': False}
            cur.execute('SELECT entries,revision,updated_at FROM maktab_kun_tartibi_v45 WHERE maktab_id=%s', (school['id'],))
            saved = cur.fetchone() or {}
            entries = saved.get('entries') or []
            if isinstance(entries, str):
                entries = json.loads(entries)
            return dict(routine_state(entries), enabled=True, school_id=school['id'], school_name=school['nomi'], schools=schools,
                        can_edit=editor, entries=entries, preset=routine_preset() if editor else [], revision=int(saved.get('revision') or 0),
                        updated_at=saved['updated_at'].isoformat() if saved.get('updated_at') else None)

    def save(self, actor_id, payload):
        if not isinstance(payload, dict):
            fail(422, 'So‘rov noto‘g‘ri.')
        school_id = positive_id(payload.get('school_id'))
        revision = payload.get('revision')
        if isinstance(revision, bool) or not isinstance(revision, int) or not 0 <= revision < 2147483647:
            fail(422, 'Kun tartibi versiyasi noto‘g‘ri.')
        entries = validate_entries(payload.get('entries'))
        with self.transaction() as cur:
            school, _, editor = self.context(cur, actor_id, school_id)
            if not school or not editor:
                fail(403, 'Kun tartibini faqat administrator yoki shu maktab direktori o‘zgartiradi.')
            cur.execute('''INSERT INTO maktab_kun_tartibi_v45(maktab_id,entries,updated_by)
                SELECT %s,%s::jsonb,%s WHERE %s=0 OR EXISTS(SELECT 1 FROM maktab_kun_tartibi_v45 WHERE maktab_id=%s)
                ON CONFLICT(maktab_id) DO UPDATE SET entries=EXCLUDED.entries,updated_by=EXCLUDED.updated_by,
                updated_at=NOW(),revision=maktab_kun_tartibi_v45.revision+1
                WHERE maktab_kun_tartibi_v45.revision=%s RETURNING revision''',
                (school_id, json.dumps(entries, ensure_ascii=False), actor_id, revision, school_id, revision))
            result = cur.fetchone()
            if not result:
                fail(409, 'Kun tartibi boshqa oynada yangilangan. Yangilab, o‘zgartirishni qayta kiriting.')
            return {'saved': True, 'revision': result['revision']}


def register_military_school(app, platform):
    service = MilitarySchoolService(platform)

    @app.get('/api/maktab/kun-tartibi')
    def get_routine(request: Request, school_id: int = None, child_id: int = None):
        return service.read(service.actor(request), school_id, child_id)

    @app.post('/api/maktab/kun-tartibi/type')
    async def enable_type(request: Request):
        actor_id = await run_in_threadpool(service.actor, request)
        raw = await request.body()
        if len(raw) > 1024:
            fail(413, 'So‘rov juda katta.')
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            fail(422, 'So‘rov JSON shaklida bo‘lishi kerak.')
        if not isinstance(payload, dict) or payload.get('maktab_turi') != 'harbiy':
            fail(422, 'Harbiy maktab turini tanlang.')
        return await run_in_threadpool(service.enable_existing, actor_id, payload.get('school_id'))

    @app.put('/api/maktab/kun-tartibi')
    async def save_routine(request: Request):
        actor_id = await run_in_threadpool(service.actor, request)
        raw = await request.body()
        if len(raw) > 65536:
            fail(413, 'Kun tartibi so‘rovi juda katta.')
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            fail(422, 'So‘rov JSON shaklida bo‘lishi kerak.')
        return await run_in_threadpool(service.save, actor_id, payload)

    return service
