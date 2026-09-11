"""REV45: current, institution-bound Kabutar authorization.

School/legacy employee ``lavozim`` is assigned by the existing admin/import/code
flows, never by the public role/profile selector. Student membership is an
actual class/group roster row; users.role, users.class, KB IDs, phone numbers,
message history and chat_azolari alone confer NO permission. No administrator
shortcut exists. The same policy protects messaging, discovery, media and calls.
"""
from __future__ import annotations
from fastapi import HTTPException

POLICY_MESSAGE = "Kabutar faqat faol muassasadagi tasdiqlangan sinfdoshlar, hamkasblar va biriktirilgan o‘qituvchilar bilan aloqa uchun ochiq."
_TABLES = ('users','maktablar','universitetlar','oquv_markazlari','bogchalar',
           'foydalanuvchi_muassasalari','maktab_sinflari','maktab_sinf_azolari',
           'maktab_dars_birikmalari','maktab_xodim_sinflari','parent_child',
           'universitet_xodim_rollari','universitet_guruhlari','universitet_guruh_azolari',
           'fakultetlar','kafedralar','togaraklar','togarak_azolar',
           'learning_contexts','context_memberships','course_groups',
           'organization_trials','universitet_workspace_map','kabutar_user_blocks','kindergarten_profiles',
           'military_boarding_v45','military_duty_v45')


def authenticate(platform, token):
    """Private conversations are accessible only through one's own session.

    The education admin preview token intentionally impersonates a student's
    educational dashboard. It must never be usable to inspect their messages.
    """
    actor_id = platform._jwt_tekshir(token)
    auth = getattr(platform,'_kabutar_auth_service',None)
    if auth is None:
        raise HTTPException(503,'Kabutar kirish tizimi hali ishga tushmagan')
    if auth.claims(token).get('admin_korish'):
        raise HTTPException(403,'Ko‘rish rejimida shaxsiy Kabutar suhbatlari ochilmaydi')
    return int(actor_id)


def _tables(cur):
    cur.execute('SELECT name,to_regclass(\'public.\' || name) IS NOT NULL AS present FROM unnest(%s::text[]) AS name', (list(_TABLES),))
    return {r['name'] for r in cur.fetchall() if r['present']}


def _active(alias):
    # Optional legacy columns are read as JSON to work across old installations.
    j = f'to_jsonb({alias})'
    return (f"NULLIF({j}->>'archived_at','') IS NULL AND NULLIF({j}->>'deleted_at','') IS NULL AND NULLIF({j}->>'cancelled_at','') IS NULL "
            f"AND NULLIF({j}->>'removed_at','') IS NULL AND NULLIF({j}->>'revoked_at','') IS NULL AND NULLIF({j}->>'ended_at','') IS NULL "
            f"AND LOWER(COALESCE({j}->>'faol',{j}->>'active',{j}->>'aktiv','true')) NOT IN ('false','0') "
            f"AND LOWER(COALESCE({j}->>'status','active')) NOT IN ('removed','inactive','archived','blocked','deleted','rejected','suspended','ended','pending','cancelled','withdrawn','left','expired') "
            f"AND LOWER(COALESCE({j}->>'blocked','false')) NOT IN ('true','1')")


def _institution_select(table, kind, tables):
    extra = ''
    if 'learning_contexts' in tables:
        ext = {'maktab':'maktab','universitet':'universitet','markaz':'markaz','bogcha':'bogcha'}[kind]
        extra += (f" AND NOT EXISTS(SELECT 1 FROM learning_contexts c WHERE c.external_type='{ext}' "
                  f"AND c.external_id=i.id AND NOT ({_active('c')}))")
    if kind == 'bogcha' and {'learning_contexts','kindergarten_profiles'} <= tables:
        extra += """ AND NOT EXISTS(SELECT 1 FROM learning_contexts c JOIN kindergarten_profiles kp ON kp.context_id=c.id
            WHERE c.external_type='bogcha' AND c.external_id=i.id
              AND (COALESCE(kp.onboarding_status,'')<>'active' OR kp.verification_status='rejected'))"""
    if kind == 'universitet' and {'universitet_workspace_map','learning_contexts','organization_trials'} <= tables:
        extra += """ AND NOT EXISTS(SELECT 1 FROM universitet_workspace_map wm
            LEFT JOIN learning_contexts c ON c.id=wm.context_id
            LEFT JOIN organization_trials o ON o.context_id=wm.context_id
            WHERE wm.universitet_id=i.id AND
            (c.id IS NULL OR c.active IS DISTINCT FROM TRUE OR c.context_type<>'university'
             OR o.organization_type IS DISTINCT FROM 'institute'
             OR COALESCE(o.lifecycle_status,'') NOT IN ('trial','active','read_only')))"""
    return f"SELECT '{kind}'::text kind,i.id::bigint inst_id,i.nomi::text inst_name FROM {table} i WHERE {_active('i')}{extra}"


def _membership_sql(tables):
    institutions = [_institution_select(t,k,tables) for t,k in (
        ('maktablar','maktab'),('universitetlar','universitet'),('oquv_markazlari','markaz'),('bogchalar','bogcha')) if t in tables]
    empty = "SELECT NULL::text kind,NULL::bigint inst_id,NULL::text inst_name WHERE FALSE"
    staff = []
    for col, kind in (('maktab_id','maktab'),('universitet_id','universitet'),('markaz_id','markaz'),('bogcha_id','bogcha')):
        if kind == 'universitet' and 'universitet_xodim_rollari' in tables:
            continue  # V20 active role assignments supersede stale profile pointers.
        staff.append(f"""SELECT u.user_id,i.kind,i.inst_id,i.inst_name,u.lavozim::text title FROM users u
            JOIN institutions i ON i.kind='{kind}' AND i.inst_id=NULLIF(to_jsonb(u)->>'{col}','')::bigint
            WHERE NULLIF(TRIM(u.lavozim),'') IS NOT NULL AND {_active('u')}""")
    if 'foydalanuvchi_muassasalari' in tables:
        uni_override = " AND m.muassasa_turi<>'universitet'" if 'universitet_xodim_rollari' in tables else ''
        staff.append(f"""SELECT m.user_id,i.kind,i.inst_id,i.inst_name,m.lavozim::text title
            FROM foydalanuvchi_muassasalari m JOIN institutions i ON i.kind=m.muassasa_turi AND i.inst_id=m.muassasa_id
            WHERE NULLIF(TRIM(m.lavozim),'') IS NOT NULL AND {_active('m')}{uni_override}""")
    if 'universitet_xodim_rollari' in tables:
        staff.append(f"""SELECT m.user_id,i.kind,i.inst_id,i.inst_name,m.rol::text title
            FROM universitet_xodim_rollari m JOIN institutions i ON i.kind='universitet' AND i.inst_id=m.universitet_id
            WHERE m.faol=TRUE AND {_active('m')}""")
    members = ["SELECT user_id,kind,inst_id,inst_name,'staff'::text role,NULL::text cohort,title::text label FROM staff"]
    if {'maktab_sinflari','maktab_sinf_azolari'} <= tables:
        members.append(f"""SELECT a.user_id,i.kind,i.inst_id,i.inst_name,'student'::text,'sinf:'||s.id,
            s.sinf::text||'-'||COALESCE(s.harf,'') FROM maktab_sinf_azolari a
            JOIN maktab_sinflari s ON s.id=a.sinf_id JOIN institutions i ON i.kind='maktab' AND i.inst_id=s.maktab_id
            WHERE {_active('a')} AND {_active('s')}""")
        members.append(f"""SELECT st.user_id,st.kind,st.inst_id,st.inst_name,'teacher'::text,'sinf:'||s.id,
            s.sinf::text||'-'||COALESCE(s.harf,'') FROM staff st JOIN maktab_sinflari s
            ON st.kind='maktab' AND st.inst_id=s.maktab_id
            AND (s.rahbar_user_id=st.user_id OR NULLIF(to_jsonb(s)->>'psixolog_user_id','')::bigint=st.user_id)
            WHERE {_active('s')}""")
        for table in ('maktab_dars_birikmalari','maktab_xodim_sinflari'):
            if table in tables:
                members.append(f"""SELECT st.user_id,st.kind,st.inst_id,st.inst_name,'teacher'::text,'sinf:'||s.id,
                    s.sinf::text||'-'||COALESCE(s.harf,'') FROM {table} b JOIN staff st
                    ON st.kind='maktab' AND st.inst_id=b.maktab_id AND st.user_id=b.user_id
                    JOIN maktab_sinflari s ON s.id=b.sinf_id AND s.maktab_id=b.maktab_id
                    WHERE {_active('b')} AND {_active('s')}""")
        if 'parent_child' in tables:
            members.append(f"""SELECT pc.parent_id,i.kind,i.inst_id,i.inst_name,'parent'::text,'sinf:'||s.id,
                s.sinf::text||'-'||COALESCE(s.harf,'') FROM parent_child pc
                JOIN users child ON child.user_id=pc.child_id
                JOIN maktab_sinf_azolari a ON a.user_id=pc.child_id JOIN maktab_sinflari s ON s.id=a.sinf_id
                JOIN institutions i ON i.kind='maktab' AND i.inst_id=s.maktab_id
                WHERE {_active('pc')} AND {_active('a')} AND {_active('s')} AND {_active('child')}""")
    # Temporary contact edge: only a verified boarding pupil's parent and the
    # currently assigned duty teacher. Midnight crossings use UTC timestamps,
    # never comparisons of clock strings; it disappears as soon as shift ends.
    if {'military_boarding_v45','military_duty_v45','parent_child','maktab_sinf_azolari','maktab_sinflari'} <= tables:
        dutybase = f"""FROM military_duty_v45 duty JOIN staff st
            ON st.kind='maktab' AND st.inst_id=duty.maktab_id AND st.user_id=duty.teacher_id
            WHERE duty.starts_at<=NOW() AND duty.ends_at>NOW()
              AND NULLIF(to_jsonb(duty)->>'handed_over_at','') IS NULL AND {_active('duty')}"""
        members.append(f"""SELECT st.user_id,st.kind,st.inst_id,st.inst_name,'teacher'::text,
            'military_duty:'||duty.id,'Navbatchi o‘qituvchi'::text {dutybase}""")
        members.append(f"""SELECT pc.parent_id,st.kind,st.inst_id,st.inst_name,'parent'::text,
            'military_duty:'||duty.id,'Yotoqxonadagi farzandning ota-onasi'::text
            FROM military_duty_v45 duty JOIN staff st
            ON st.kind='maktab' AND st.inst_id=duty.maktab_id AND st.user_id=duty.teacher_id
            JOIN military_boarding_v45 boarding ON boarding.maktab_id=duty.maktab_id AND boarding.mode='boarding'
            JOIN users child ON child.user_id=boarding.user_id
            JOIN parent_child pc ON pc.child_id=boarding.user_id
            WHERE duty.starts_at<=NOW() AND duty.ends_at>NOW()
              AND NULLIF(to_jsonb(duty)->>'handed_over_at','') IS NULL AND {_active('duty')}
              AND {_active('boarding')} AND {_active('pc')} AND {_active('child')}
              AND EXISTS(SELECT 1 FROM maktab_sinf_azolari a JOIN maktab_sinflari cl ON cl.id=a.sinf_id
                  WHERE a.user_id=boarding.user_id AND cl.maktab_id=duty.maktab_id
                    AND {_active('a')} AND {_active('cl')})""")

    if {'universitet_guruhlari','universitet_guruh_azolari','kafedralar','fakultetlar'} <= tables:
        groupjoins = """FROM universitet_guruhlari g JOIN kafedralar k ON k.id=g.kafedra_id
            JOIN fakultetlar f ON f.id=k.fakultet_id JOIN institutions i ON i.kind='universitet' AND i.inst_id=f.universitet_id"""
        active = f"{_active('g')} AND {_active('k')} AND {_active('f')}"
        members.append(f"""SELECT a.user_id,i.kind,i.inst_id,i.inst_name,'student'::text,'universitet_guruh:'||g.id,g.nomi::text
            {groupjoins} JOIN universitet_guruh_azolari a ON a.guruh_id=g.id WHERE {active} AND {_active('a')}""")
        members.append(f"""SELECT st.user_id,i.kind,i.inst_id,i.inst_name,'teacher'::text,'universitet_guruh:'||g.id,g.nomi::text
            {groupjoins} JOIN staff st ON st.kind=i.kind AND st.inst_id=i.inst_id AND st.user_id=g.rahbar_user_id WHERE {active}""")
    if {'togaraklar','togarak_azolar'} <= tables:
        base = """FROM togaraklar t JOIN institutions i ON i.kind='markaz' AND i.inst_id=NULLIF(to_jsonb(t)->>'markaz_id','')::bigint
            JOIN staff teacher ON teacher.kind=i.kind AND teacher.inst_id=i.inst_id AND teacher.user_id=t.teacher_id"""
        members.append(f"""SELECT a.user_id,i.kind,i.inst_id,i.inst_name,'student'::text,'togarak:'||t.id,t.nomi::text
            {base} JOIN togarak_azolar a ON a.togarak_id=t.id
            WHERE {_active('t')} AND {_active('a')} AND LOWER(COALESCE(to_jsonb(a)->>'tasdiqlangan','false'))='true'""")
        members.append(f"""SELECT teacher.user_id,i.kind,i.inst_id,i.inst_name,'teacher'::text,'togarak:'||t.id,t.nomi::text
            {base} WHERE {_active('t')}""")
    # Modern institution membership rows require admin approval or one of the
    # official institution import services; personal self-enrolment is excluded.
    if {'learning_contexts','context_memberships','course_groups'} <= tables:
        orgfilter = ''
        if 'organization_trials' in tables:
            orgfilter = " AND NOT EXISTS(SELECT 1 FROM organization_trials o WHERE o.context_id=c.id AND o.lifecycle_status NOT IN ('trial','active','read_only'))"
        members.append(f"""SELECT cm.user_id,'context:'||c.context_type,c.id,c.name,
            CASE WHEN cm.member_role='student' THEN 'student' WHEN cm.member_role='teacher' AND cm.group_id IS NOT NULL THEN 'teacher' ELSE 'staff' END,
            CASE WHEN cm.group_id IS NOT NULL THEN 'course:'||cm.group_id ELSE NULL END,cg.name::text
            FROM context_memberships cm JOIN learning_contexts c ON c.id=cm.context_id
            LEFT JOIN course_groups cg ON cg.id=cm.group_id AND cg.context_id=c.id
            WHERE c.context_type IN ('school','university','learning_center','kindergarten')
              AND cm.status='active' AND {_active('cm')} AND {_active('c')}
              AND NULLIF(to_jsonb(cm)->>'ended_at','') IS NULL
              AND (cm.approved_by_user_id IS NOT NULL OR cm.source IN ('school_v2','school_v23','institute_v1','kindergarten_v2','learning_center_v2'))
              AND cm.member_role IN ('student','teacher','manager','director','admin','staff','owner')
              AND (cm.member_role<>'student' OR (cm.group_id IS NOT NULL AND c.context_type<>'kindergarten'))
              AND (cm.group_id IS NULL OR (cg.id IS NOT NULL AND {_active('cg')})){orgfilter}""")
        # Teachers assigned to a group are also coworkers of other staff.
        members.append(f"""SELECT cm.user_id,'context:'||c.context_type,c.id,c.name,'staff'::text,NULL::text,'O‘qituvchi'::text
            FROM context_memberships cm JOIN learning_contexts c ON c.id=cm.context_id
            WHERE c.context_type IN ('school','university','learning_center','kindergarten')
              AND cm.member_role='teacher' AND cm.status='active' AND {_active('cm')} AND {_active('c')}
              AND NULLIF(to_jsonb(cm)->>'ended_at','') IS NULL
              AND (cm.approved_by_user_id IS NOT NULL OR cm.source IN ('school_v2','school_v23','institute_v1','kindergarten_v2','learning_center_v2')){orgfilter}""")
    return f"""WITH institutions AS NOT MATERIALIZED ({' UNION ALL '.join(institutions) or empty}),
        staff AS NOT MATERIALIZED ({' UNION ALL '.join(staff)}),
        membership_source AS NOT MATERIALIZED ({' UNION ALL '.join(members)}),
        members AS NOT MATERIALIZED (SELECT DISTINCT m.* FROM membership_source m JOIN users u ON u.user_id=m.user_id
            WHERE {_active('u')}) """


def blocked_contact_ids(cur, actor_id, tables=None):
    tables = _tables(cur) if tables is None else tables
    if 'kabutar_user_blocks' not in tables:
        return set()
    cur.execute("""SELECT CASE WHEN blocker_id=%s THEN blocked_id ELSE blocker_id END AS user_id
        FROM kabutar_user_blocks WHERE blocker_id=%s OR blocked_id=%s""", (int(actor_id),int(actor_id),int(actor_id)))
    return {int(r['user_id']) for r in cur.fetchall()}


def memberships(cur, user_id, tables=None):
    tables = _tables(cur) if tables is None else tables
    cur.execute(_membership_sql(tables) + 'SELECT * FROM members WHERE user_id=%s', (int(user_id),))
    return [dict(r) for r in cur.fetchall()]


def _pair(a, b):
    """Pure symmetric policy, also used by fixture regression checks."""
    if int(a['user_id']) == int(b['user_id']) or (a['kind'],int(a['inst_id'])) != (b['kind'],int(b['inst_id'])):
        return False
    if a['role'] == b['role'] == 'staff':
        return True
    if not a.get('cohort') or a.get('cohort') != b.get('cohort'):
        return False
    return (a['role'],b['role']) in {('student','student'),('teacher','student'),('student','teacher'),('teacher','parent'),('parent','teacher')}


def allow_direct(cur, actor_id, peer_id, school_id=None, *, ignore_blocks=False):
    if int(actor_id) == int(peer_id):
        return False
    tables = _tables(cur)
    if not ignore_blocks and int(peer_id) in blocked_contact_ids(cur, actor_id, tables):
        return False
    cur.execute(_membership_sql(tables) + 'SELECT * FROM members WHERE user_id=ANY(%s)', ([int(actor_id),int(peer_id)],))
    rows = [dict(r) for r in cur.fetchall()]
    a = [r for r in rows if int(r['user_id']) == int(actor_id)]
    b = [r for r in rows if int(r['user_id']) == int(peer_id)]
    if school_id is not None:
        a = [r for r in a if r['kind']=='maktab' and int(r['inst_id'])==int(school_id)]
    return any(_pair(x,y) for x in a for y in b)


def require_direct(cur, actor_id, peer_id, school_id=None, *, ignore_blocks=False):
    if not allow_direct(cur, actor_id, peer_id, school_id, ignore_blocks=ignore_blocks):
        raise HTTPException(403, POLICY_MESSAGE)


def contact_directory(cur, actor_id):
    tables = _tables(cur)
    mine = memberships(cur,actor_id,tables)
    if not mine:
        return [], []
    # Apply the allowed relationship in SQL: a pupil's address book must not
    # fetch every other pupil at a large institution before filtering in Python.
    conditions, params, seen = [], [], set()
    peers = {'student':('student','teacher'), 'teacher':('student','parent'), 'parent':('teacher',)}
    for row in mine:
        role, cohort = row['role'], row.get('cohort')
        if role=='staff':
            target_roles, cohort = ('staff',), None
        elif role in peers and cohort:
            target_roles = peers[role]
        else:
            continue
        key = (row['kind'],int(row['inst_id']),target_roles,cohort)
        if key in seen:
            continue
        seen.add(key)
        condition = '(kind=%s AND inst_id=%s AND role=ANY(%s)'
        params.extend([key[0],key[1],list(target_roles)])
        if cohort is not None:
            condition += ' AND cohort=%s'
            params.append(cohort)
        conditions.append(condition+')')
    if not conditions:
        return mine, []
    cur.execute(_membership_sql(tables) + f'SELECT * FROM members WHERE ({" OR ".join(conditions)}) AND user_id<>%s', params+[int(actor_id)])
    rows = [dict(r) for r in cur.fetchall()]
    blocked = blocked_contact_ids(cur, actor_id, tables)
    allowed = [r for r in rows if int(r['user_id']) not in blocked and any(_pair(a,r) for a in mine)]
    return mine, allowed


def allowed_contact_ids(cur, actor_id):
    return {int(r['user_id']) for r in contact_directory(cur,actor_id)[1]}


def directory_payload(cur, actor_id):
    mine, contacts = contact_directory(cur,actor_id)
    ids = sorted({int(r['user_id']) for r in contacts})
    cards = {}
    if ids:
        cur.execute('SELECT user_id,full_name,kabutar_id FROM users WHERE user_id=ANY(%s) ORDER BY full_name', (ids,))
        cards = {int(r['user_id']):dict(r) for r in cur.fetchall()}
    groups = {}
    for row in mine:
        key = (row['kind'],int(row['inst_id']))
        groups.setdefault(key, {'turi':row['kind'].replace('universitet','institut').replace('context:',''), 'muassasa_id':int(row['inst_id']), 'muassasa':row['inst_name'],'azolar':[]})
    seen = set()
    for row in contacts:
        key = (row['kind'],int(row['inst_id']))
        uid = int(row['user_id'])
        if (key,uid) in seen or uid not in cards:
            continue
        seen.add((key,uid))
        label = {'staff':'Hamkasb','teacher':'Biriktirilgan o‘qituvchi','student':'Sinf/guruh a’zosi','parent':'O‘quvchining ota-onasi'}[row['role']]
        group = {'staff':'oqituvchilar','teacher':'oqituvchilar','student':'oquvchilar','parent':'ota_onalar'}[row['role']]
        groups[key]['azolar'].append({**cards[uid],'guruh':group,'rol':group,'izoh':label + (' · '+str(row['label']) if row.get('label') else '')})
    return list(groups.values()), bool(mine)


def allow_group(cur, actor_id, group_id):
    cur.execute(f'SELECT g.* FROM chat_guruhlari g JOIN chat_azolari a ON a.guruh_id=g.id WHERE g.id=%s AND a.user_id=%s AND {_active("g")} AND {_active("a")}', (int(group_id),int(actor_id)))
    row = cur.fetchone()
    if not row:
        return False
    row = dict(row)
    if row.get('turi') == 'global' or row.get('manba_turi') == 'global':
        return False
    mine = memberships(cur,actor_id)
    source = row.get('manba_turi'); source_id = int(row.get('manba_id') or 0)
    if row.get('turi') == 'xodimlar' and source in ('maktab','universitet','markaz','bogcha','context:school','context:university','context:learning_center','context:kindergarten'):
        return any(r['kind']==source and int(r['inst_id'])==source_id and r['role']=='staff' for r in mine)
    if source in ('sinf','universitet_guruh','togarak','course'):
        cohort = f'{source}:{source_id}'
        return any(r.get('cohort')==cohort and r['role'] in ('student','teacher') for r in mine)
    return False


def require_group(cur, actor_id, group_id, write=False):
    if write:
        ensure_terms_accepted(cur,actor_id)
    if not allow_group(cur,actor_id,group_id):
        raise HTTPException(403, 'Bu guruhdagi amaldagi a’zoligingiz tasdiqlanmagan yoki muassasa arxivlangan.')


def require_message(cur, actor_id, message_id, *, ignore_blocks=False):
    cur.execute('SELECT id,guruh_id,yuboruvchi_user_id,qabul_qiluvchi_user_id,ochirilgan FROM chat_xabarlari WHERE id=%s', (int(message_id),))
    row = cur.fetchone()
    if not row or row.get('ochirilgan'):
        raise HTTPException(404, 'Xabar topilmadi')
    row = dict(row)
    if row.get('guruh_id'):
        require_group(cur,actor_id,row['guruh_id'])
    else:
        actor = int(actor_id); sender = int(row['yuboruvchi_user_id']); recipient = int(row.get('qabul_qiluvchi_user_id') or 0)
        if actor not in (sender,recipient):
            raise HTTPException(403, 'Bu xabar sizga tegishli emas')
        require_direct(cur,actor,recipient if actor==sender else sender,ignore_blocks=ignore_blocks)
    return row


def ensure_terms_accepted(cur, user_id):
    if __package__:
        from .kabutar_terms import ensure_accepted
    else:
        from kabutar_terms import ensure_accepted
    ensure_accepted(cur,user_id)
