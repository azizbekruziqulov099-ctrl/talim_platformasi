"""Military school recorded boarding, duty, departure and meal operations.

Plans never imply attendance. Roster membership and all authorizations are
resolved afresh from the institution's authoritative assignments.
"""
import json
import re
from datetime import datetime, timedelta
from .military_school import MilitarySchoolService, ZONE, fail, positive_id, memberships, _active
from fastapi import Request
from starlette.concurrency import run_in_threadpool

if __package__ and '.' in __package__:
    from ..kabutar_policy import _membership_sql, _tables, allow_direct
else:
    from kabutar_policy import _membership_sql, _tables, allow_direct

STATUSES = {'present', 'home', 'boarding', 'absent', 'unknown'}
TEACHER_TITLES = {'oqituvchi', 'teacher', 'direktor', 'director', 'zavuch', 'sinf_rahbar', 'direktor_orinbosari', 'tarbiyachi'}


def revision(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < 2147483647:
        fail(422, 'Ma’lumot versiyasi noto‘g‘ri. Sahifani yangilang.')
    return value


def clean_text(value, maximum=160, empty=True):
    if not isinstance(value, str) or len(value.strip()) > maximum or any(ord(c) < 32 for c in value):
        fail(422, 'Matn juda uzun yoki noto‘g‘ri.')
    text = value.strip()
    if not empty and not text:
        fail(422, 'Nomini kiriting.')
    return text


def validate_settings(payload):
    fees = {}
    for key in ('day_fee', 'boarding_fee'):
        value = payload.get(key)
        if value in ('', None):
            fees[key] = None
        elif isinstance(value, bool) or not re.fullmatch(r'\d{1,10}', str(value)) or int(value) > 1000000000:
            fail(422, 'Oylik narxni 0–1 000 000 000 so‘m oralig‘ida kiriting.')
        else:
            fees[key] = int(value)
    menu = payload.get('menu')
    if not isinstance(menu, list) or len(menu) != 7:
        fail(422, 'Haftaning yetti kuni uchun menyu kiriting.')
    cleaned = []
    for row in menu:
        if not isinstance(row, dict):
            fail(422, 'Menyu shakli noto‘g‘ri.')
        cleaned.append({meal: clean_text(row.get(meal, ''), 200) for meal in ('breakfast', 'lunch', 'dinner')})
    return dict(fees, menu=cleaned, menu_manager_id=positive_id(payload['menu_manager_id']) if payload.get('menu_manager_id') else None)


def duty_times(start, end, now=None):
    try:
        starts, ends = datetime.fromisoformat(start), datetime.fromisoformat(end)
    except (ValueError, TypeError):
        fail(422, 'Navbatchilikning boshlanish va tugash sanasini kiriting.')
    if starts.tzinfo is None or ends.tzinfo is None:
        fail(422, 'Navbatchilik vaqti vaqt mintaqasi bilan yuborilishi kerak.')
    now = now or datetime.now(ZONE)
    if not timedelta(minutes=30) <= ends - starts <= timedelta(hours=24):
        fail(422, 'Bitta navbatchilik 30 daqiqadan 24 soatgacha bo‘lishi mumkin.')
    if starts < now - timedelta(days=1) or ends <= now or starts > now + timedelta(days=90):
        fail(422, 'Navbatchilik vaqtini bugundan 90 kun ichida belgilang.')
    return starts, ends


def empty_settings():
    return {'menu': [{meal: '' for meal in ('breakfast', 'lunch', 'dinner')} for _ in range(7)], 'day_fee': None, 'boarding_fee': None, 'menu_manager_id': None}


class MilitaryOperationsService(MilitarySchoolService):
    def migrate(self):
        with self.transaction() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(45091040)")
            cur.execute('''CREATE TABLE IF NOT EXISTS military_settings_v45(
                maktab_id BIGINT PRIMARY KEY REFERENCES maktablar(id) ON DELETE CASCADE,
                settings JSONB NOT NULL, revision INTEGER NOT NULL DEFAULT 1,
                updated_by BIGINT NOT NULL REFERENCES users(user_id), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())''')
            cur.execute('''CREATE TABLE IF NOT EXISTS military_boarding_v45(
                maktab_id BIGINT NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
                user_id BIGINT NOT NULL REFERENCES users(user_id), mode TEXT NOT NULL CHECK(mode IN ('day','boarding')),
                revision INTEGER NOT NULL DEFAULT 1, updated_by BIGINT NOT NULL REFERENCES users(user_id),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(maktab_id,user_id))''')
            cur.execute('''CREATE TABLE IF NOT EXISTS military_duty_v45(
                id BIGSERIAL PRIMARY KEY, maktab_id BIGINT NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
                teacher_id BIGINT NOT NULL REFERENCES users(user_id), receiver_id BIGINT REFERENCES users(user_id),
                starts_at TIMESTAMPTZ NOT NULL, ends_at TIMESTAMPTZ NOT NULL,
                revision INTEGER NOT NULL DEFAULT 1, created_by BIGINT NOT NULL REFERENCES users(user_id),
                cancelled_at TIMESTAMPTZ, handed_over_at TIMESTAMPTZ, handed_over_by BIGINT REFERENCES users(user_id),
                handover_note TEXT NOT NULL DEFAULT '', CHECK(ends_at>starts_at))''')
            cur.execute('CREATE INDEX IF NOT EXISTS military_duty_school_time_v45 ON military_duty_v45(maktab_id,starts_at,ends_at) WHERE cancelled_at IS NULL')
            cur.execute('''CREATE TABLE IF NOT EXISTS military_departure_v45(
                maktab_id BIGINT NOT NULL REFERENCES maktablar(id) ON DELETE CASCADE,
                user_id BIGINT NOT NULL REFERENCES users(user_id), day DATE NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('present','home','boarding','absent','unknown')),
                revision INTEGER NOT NULL DEFAULT 1, recorded_by BIGINT NOT NULL REFERENCES users(user_id),
                recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(maktab_id,user_id,day))''')

    def scope(self, cur, actor, school_id, child_id=None):
        school, _, editor = self.context(cur, actor, positive_id(school_id), child_id)
        if not school:
            fail(404, 'Harbiy maktab topilmadi.')
        return school, editor

    def is_member(self, cur, user_id, school_id, role):
        return any(r['kind'] == 'maktab' and int(r['inst_id']) == school_id and r['role'] == role for r in memberships(cur, user_id))

    def require_teacher(self, cur, user_id, school_id):
        rows = memberships(cur, user_id)
        valid = any(r['kind'] == 'maktab' and int(r['inst_id']) == school_id and
                    (r['role'] == 'teacher' or (r['role'] == 'staff' and str(r.get('label', '')).lower().replace("'", '').replace('‘','').replace('’','') in TEACHER_TITLES)) for r in rows)
        if not valid:
            fail(422, 'Navbatchi va qabul qiluvchi shu maktabdagi tasdiqlangan o‘qituvchi bo‘lishi kerak.')

    def settings(self, cur, school_id):
        cur.execute('SELECT settings,revision FROM military_settings_v45 WHERE maktab_id=%s', (school_id,))
        row = cur.fetchone()
        if not row:
            return empty_settings(), 0
        value = row['settings']
        return (json.loads(value) if isinstance(value, str) else dict(value)), int(row['revision'])

    def on_duty(self, cur, actor, school_id):
        cur.execute('''SELECT 1 FROM military_duty_v45 WHERE maktab_id=%s AND teacher_id=%s
            AND starts_at<=NOW() AND ends_at>NOW() AND cancelled_at IS NULL AND handed_over_at IS NULL LIMIT 1''', (school_id, actor))
        return bool(cur.fetchone()) and self.is_member(cur, actor, school_id, 'staff')

    def student_sql(self):
        return f'''SELECT DISTINCT a.user_id FROM maktab_sinf_azolari a JOIN maktab_sinflari s ON s.id=a.sinf_id
            JOIN users u ON u.user_id=a.user_id WHERE s.maktab_id=%s AND {_active('a')} AND {_active('s')} AND {_active('u')}'''

    def people(self, actor, school_id, kind, query='', after=0):
        school_id = positive_id(school_id)
        after = int(after)
        if after < 0 or kind not in {'staff','student'}:
            fail(422, 'Ro‘yxat parametrlari noto‘g‘ri.')
        query = clean_text(query, 80)
        with self.transaction() as cur:
            _, editor = self.scope(cur, actor, school_id)
            if not editor and not (kind == 'student' and self.on_duty(cur, actor, school_id)):
                fail(403, 'Ro‘yxatga ruxsat yo‘q.')
            base = _membership_sql(_tables(cur))
            cur.execute(base + '''SELECT DISTINCT u.user_id,u.full_name FROM members m JOIN users u ON u.user_id=m.user_id
                WHERE m.kind='maktab' AND m.inst_id=%s AND m.role=%s AND u.user_id>%s
                AND (%s='' OR POSITION(LOWER(%s) IN LOWER(COALESCE(u.full_name,'')))>0)
                ORDER BY u.user_id LIMIT 101''', (school_id, 'staff' if kind == 'staff' else 'student', after, query, query))
            rows = [dict(r) for r in cur.fetchall()]
            return {'people': rows[:100], 'next': rows[99]['user_id'] if len(rows) > 100 else None}

    def read(self, actor, school_id, child_id=None, after=0):
        school_id = positive_id(school_id)
        if int(after) < 0:
            fail(422, 'Ro‘yxat parametri noto‘g‘ri.')
        now = datetime.now(ZONE)
        with self.transaction() as cur:
            school, editor = self.scope(cur, actor, school_id, child_id)
            settings, version = self.settings(cur, school_id)
            duty_editor = child_id is None and self.on_duty(cur, actor, school_id)
            can_record = child_id is None and (editor or duty_editor)
            menu_editor = child_id is None and (editor or (settings.get('menu_manager_id') == actor and self.is_member(cur, actor, school_id, 'staff')))
            target = positive_id(child_id) if child_id else actor
            cur.execute('''SELECT mode,revision FROM military_boarding_v45 WHERE maktab_id=%s AND user_id=%s''', (school_id, target))
            boarding = cur.fetchone()
            own_student = self.is_member(cur, target, school_id, 'student')
            if not own_student:
                boarding = None
            cur.execute('''SELECT status,recorded_at FROM military_departure_v45 WHERE maktab_id=%s AND user_id=%s AND day=%s''', (school_id, target, now.date()))
            departure = cur.fetchone() if own_student else None
            cur.execute('''SELECT d.id,d.teacher_id,d.receiver_id,d.starts_at,d.ends_at,d.revision,d.handed_over_at,
                d.handed_over_by,d.handover_note,u.full_name AS teacher_name,r.full_name AS receiver_name
                FROM military_duty_v45 d JOIN users u ON u.user_id=d.teacher_id LEFT JOIN users r ON r.user_id=d.receiver_id
                WHERE d.maktab_id=%s AND d.cancelled_at IS NULL AND d.ends_at>NOW()-INTERVAL '24 hours'
                AND d.starts_at<NOW()+INTERVAL '14 days' ORDER BY d.starts_at LIMIT 40''', (school_id,))
            duties = [dict(r) for r in cur.fetchall()]
            current = next((r for r in duties if r['starts_at'] <= now < r['ends_at'] and r['handed_over_at'] is None), None)
            if current and not self.is_member(cur, int(current['teacher_id']), school_id, 'staff'):
                current = None
            parent_contact = bool(child_id and boarding and boarding['mode'] == 'boarding' and current and allow_direct(cur, actor, int(current['teacher_id']), school_id))
            contact = {'user_id': current['teacher_id'], 'name': current['teacher_name']} if parent_contact else None
            receiver_member = child_id is None and self.is_member(cur, actor, school_id, 'staff')
            if receiver_member:
                for row in duties:
                    row['can_handover'] = bool((editor or row['receiver_id'] == actor) and not row['handed_over_at'] and now >= row['ends_at'] - timedelta(minutes=30))
            if not editor and not duty_editor:
                duties = [r if receiver_member and r['receiver_id'] == actor else
                          {k: r[k] for k in ('id','teacher_name','starts_at','ends_at','handed_over_at')}
                          for r in duties if r is current or (receiver_member and r['receiver_id'] == actor)]
            roster, next_cursor, counts = [], None, None
            if can_record:
                base = self.student_sql()
                cur.execute(f'''WITH roster AS ({base}) SELECT u.user_id,u.full_name,b.mode,COALESCE(b.revision,0) AS mode_revision,
                    COALESCE(d.status,'unknown') AS departure,COALESCE(d.revision,0) AS departure_revision
                    FROM roster r JOIN users u ON u.user_id=r.user_id
                    LEFT JOIN military_boarding_v45 b ON b.user_id=r.user_id AND b.maktab_id=%s
                    LEFT JOIN military_departure_v45 d ON d.user_id=r.user_id AND d.maktab_id=%s AND d.day=%s
                    WHERE r.user_id>%s ORDER BY r.user_id LIMIT 101''', (school_id,school_id,school_id,now.date(),int(after)))
                rows = [dict(r) for r in cur.fetchall()]
                roster, next_cursor = rows[:100], (rows[99]['user_id'] if len(rows)>100 else None)
                cur.execute(f'''WITH roster AS ({base}) SELECT COALESCE(d.status,'unknown') AS status,COUNT(*) AS count
                    FROM roster r LEFT JOIN military_departure_v45 d ON d.user_id=r.user_id AND d.maktab_id=%s AND d.day=%s
                    GROUP BY COALESCE(d.status,'unknown')''', (school_id,school_id,now.date()))
                counts = {r['status']: int(r['count']) for r in cur.fetchall()}
            shown_settings = settings if editor else {'menu': settings['menu']}
            return {'school_id':school_id,'date':now.date().isoformat(),'time':now.isoformat(),'can_edit':editor,
                    'can_record':can_record,'can_edit_menu':menu_editor,'revision':version,'settings':shown_settings,
                    'self_is_student':own_student,'mode': boarding['mode'] if boarding else None,
                    'monthly_fee':settings.get('boarding_fee' if boarding and boarding['mode']=='boarding' else 'day_fee') if boarding else None,
                    'departure':dict(departure) if departure else None,'duties':duties,'duty_contact':contact,
                    'roster':roster,'next':next_cursor,'counts':counts}

    def mutate(self, actor, payload):
        if not isinstance(payload, dict):
            fail(422, 'So‘rov shakli noto‘g‘ri.')
        school_id = positive_id(payload.get('school_id'))
        action = payload.get('action')
        if not isinstance(action, str):
            fail(422, 'Amal turi noto‘g‘ri.')
        now = datetime.now(ZONE)
        with self.transaction() as cur:
            _, editor = self.scope(cur, actor, school_id)
            cur.execute("SELECT LOWER(COALESCE(to_jsonb(m)->>'status','')) AS status FROM maktablar m WHERE id=%s", (school_id,))
            if (cur.fetchone() or {}).get('status') == 'read_only':
                fail(403, 'Maktab hozir faqat ko‘rish rejimida.')
            cur.execute("SELECT to_regclass('public.learning_contexts') AS contexts, to_regclass('public.organization_trials') AS trials")
            tables = cur.fetchone() or {}
            if tables.get('contexts') and tables.get('trials'):
                cur.execute("""SELECT 1 FROM learning_contexts c JOIN organization_trials o ON o.context_id=c.id
                    WHERE c.external_type='maktab' AND c.external_id=%s AND o.lifecycle_status='read_only' LIMIT 1""", (school_id,))
                if cur.fetchone():
                    fail(403, 'Maktab hozir faqat ko‘rish rejimida.')
            if action in {'settings','menu'}:
                settings, old = self.settings(cur, school_id)
                requested = revision(payload.get('revision'))
                if action == 'settings':
                    if not editor:
                        fail(403, 'Narx va mas’ullarni direktor yoki administrator belgilaydi.')
                    new = validate_settings(payload)
                    manager = new.get('menu_manager_id')
                    if manager and not self.is_member(cur, manager, school_id, 'staff'):
                        fail(422, 'Menyu mas’uli shu maktabdagi faol xodim bo‘lishi kerak.')
                else:
                    if not editor and not (settings.get('menu_manager_id') == actor and self.is_member(cur, actor, school_id, 'staff')):
                        fail(403, 'Menyuni o‘zgartirish uchun mas’ul qilib biriktirilmagansiz.')
                    new = validate_settings(dict(settings, menu=payload.get('menu')))
                cur.execute('''INSERT INTO military_settings_v45(maktab_id,settings,updated_by)
                    SELECT %s,%s::jsonb,%s WHERE %s=0
                    ON CONFLICT(maktab_id) DO UPDATE SET settings=EXCLUDED.settings,updated_by=EXCLUDED.updated_by,
                    updated_at=NOW(),revision=military_settings_v45.revision+1
                    WHERE military_settings_v45.revision=%s RETURNING revision''', (school_id,json.dumps(new,ensure_ascii=False),actor,requested,requested)) if requested == 0 else cur.execute('''UPDATE military_settings_v45 SET settings=%s::jsonb,updated_by=%s,updated_at=NOW(),revision=revision+1
                    WHERE maktab_id=%s AND revision=%s RETURNING revision''', (json.dumps(new,ensure_ascii=False),actor,school_id,requested))
            elif action in {'boarding','departure'}:
                target = positive_id(payload.get('user_id'))
                if action == 'boarding' and not editor:
                    fail(403, 'Yashash tartibini direktor yoki administrator belgilaydi.')
                if action == 'departure' and not editor and not self.on_duty(cur, actor, school_id):
                    fail(403, 'Yo‘qlamani direktor yoki hozirgi navbatchi qayd etadi.')
                if not self.is_member(cur, target, school_id, 'student'):
                    fail(422, 'O‘quvchi shu maktabning faol sinfida yo‘q.')
                requested = revision(payload.get('revision'))
                if action == 'boarding':
                    mode = payload.get('mode')
                    if not isinstance(mode, str) or mode not in {'day','boarding'}:
                        fail(422, 'Kunduzgi yoki yotoqxonada qolishni tanlang.')
                    cur.execute('''INSERT INTO military_boarding_v45(maktab_id,user_id,mode,updated_by)
                        SELECT %s,%s,%s,%s WHERE %s=0
                        ON CONFLICT(maktab_id,user_id) DO UPDATE SET mode=EXCLUDED.mode,updated_by=EXCLUDED.updated_by,
                        updated_at=NOW(),revision=military_boarding_v45.revision+1
                        WHERE military_boarding_v45.revision=%s RETURNING revision''', (school_id,target,mode,actor,requested,requested)) if requested == 0 else cur.execute('''UPDATE military_boarding_v45 SET mode=%s,updated_by=%s,updated_at=NOW(),revision=revision+1
                        WHERE maktab_id=%s AND user_id=%s AND revision=%s RETURNING revision''',(mode,actor,school_id,target,requested))
                else:
                    status = payload.get('status')
                    if not isinstance(status, str) or status not in STATUSES or payload.get('date') != now.date().isoformat():
                        fail(422, 'Bugungi sana va yo‘qlama holatini tekshiring.')
                    if status == 'boarding':
                        cur.execute("SELECT 1 FROM military_boarding_v45 WHERE maktab_id=%s AND user_id=%s AND mode='boarding'",(school_id,target))
                        if not cur.fetchone():
                            fail(422, 'Avval o‘quvchini yotoqxonada qoluvchi qilib belgilang.')
                    cur.execute('''INSERT INTO military_departure_v45(maktab_id,user_id,day,status,recorded_by)
                        SELECT %s,%s,%s,%s,%s WHERE %s=0
                        ON CONFLICT(maktab_id,user_id,day) DO UPDATE SET status=EXCLUDED.status,recorded_by=EXCLUDED.recorded_by,
                        recorded_at=NOW(),revision=military_departure_v45.revision+1
                        WHERE military_departure_v45.revision=%s RETURNING revision''',(school_id,target,now.date(),status,actor,requested,requested)) if requested == 0 else cur.execute('''UPDATE military_departure_v45 SET status=%s,recorded_by=%s,recorded_at=NOW(),revision=revision+1
                        WHERE maktab_id=%s AND user_id=%s AND day=%s AND revision=%s RETURNING revision''',(status,actor,school_id,target,now.date(),requested))
            elif action == 'duty':
                if not editor:
                    fail(403, 'Navbatchini direktor yoki administrator tayinlaydi.')
                teacher = positive_id(payload.get('teacher_id'))
                receiver = positive_id(payload['receiver_id']) if payload.get('receiver_id') else None
                self.require_teacher(cur,teacher,school_id)
                if receiver:
                    self.require_teacher(cur,receiver,school_id)
                start,end = duty_times(payload.get('starts_at'),payload.get('ends_at'),now)
                cur.execute('SELECT pg_advisory_xact_lock(%s)',(450000000000000000 + school_id,))
                cur.execute('''SELECT 1 FROM military_duty_v45 WHERE maktab_id=%s AND cancelled_at IS NULL
                    AND starts_at<%s AND ends_at>%s LIMIT 1''',(school_id,end,start))
                if cur.fetchone():
                    fail(409, 'Bu vaqtga navbatchi tayinlangan. Oldingi yozuvni bekor qiling yoki boshqa vaqt tanlang.')
                cur.execute('''INSERT INTO military_duty_v45(maktab_id,teacher_id,receiver_id,starts_at,ends_at,created_by)
                    VALUES(%s,%s,%s,%s,%s,%s) RETURNING id,revision''',(school_id,teacher,receiver,start,end,actor))
            elif action in {'handover','cancel_duty'}:
                duty_id = positive_id(payload.get('id'))
                requested = revision(payload.get('revision'))
                cur.execute('SELECT * FROM military_duty_v45 WHERE id=%s AND maktab_id=%s FOR UPDATE',(duty_id,school_id))
                duty = cur.fetchone()
                if not duty or duty['cancelled_at'] or duty['revision'] != requested:
                    fail(409, 'Navbatchilik yangilangan. Sahifani yangilang.')
                if action == 'cancel_duty':
                    if not editor:
                        fail(403, 'Navbatchilikni faqat rahbar bekor qiladi.')
                    cur.execute('UPDATE military_duty_v45 SET cancelled_at=NOW(),revision=revision+1 WHERE id=%s RETURNING revision',(duty_id,))
                else:
                    if not editor and (duty['receiver_id'] != actor or not self.is_member(cur,actor,school_id,'staff')):
                        fail(403, 'Qabulni rahbar yoki oldindan tayinlangan qabul qiluvchi tasdiqlaydi.')
                    if duty['handed_over_at'] or now < duty['ends_at']-timedelta(minutes=30):
                        fail(409, 'Qabulni navbatchilik tugashiga 30 daqiqa qolgandan boshlab tasdiqlash mumkin.')
                    cur.execute('''UPDATE military_duty_v45 SET handed_over_at=NOW(),handed_over_by=%s,handover_note=%s,
                        revision=revision+1 WHERE id=%s RETURNING revision''',(actor,clean_text(payload.get('note',''),500),duty_id))
            else:
                fail(422, 'Amal turi noto‘g‘ri.')
            result = cur.fetchone()
            if not result:
                fail(409, 'Ma’lumot boshqa oynada yangilangan. Yangilab, qayta kiriting.')
            return dict(result,saved=True)


def register_military_operations(app, platform):
    service = MilitaryOperationsService(platform)

    @app.get('/api/maktab/harbiy-amaliyot')
    def read_operations(request: Request, school_id: int, child_id: int=None, after: int=0):
        return service.read(service.actor(request), school_id, child_id, after)

    @app.get('/api/maktab/harbiy-amaliyot/people')
    def read_people(request: Request, school_id: int, kind: str, query: str='', after: int=0):
        return service.people(service.actor(request),school_id,kind,query,after)

    @app.post('/api/maktab/harbiy-amaliyot')
    async def update_operations(request: Request):
        actor = service.actor(request)
        raw = await request.body()
        if len(raw)>32768:
            fail(413, 'So‘rov hajmi juda katta.')
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            fail(422, 'So‘rov JSON shaklida bo‘lishi kerak.')
        return await run_in_threadpool(service.mutate,actor,payload)

    return service
