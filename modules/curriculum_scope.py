"""One authoritative curriculum audience for creation, imports and learners.

Zero denotes the explicit common SCHOOL catalog, never a wildcard. Unassigned
legacy college rows are withheld until mapped; no institution is guessed.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

FIELDS = ('institution_type','institution_id','talim_bosqichi','yonalish_id','yonalish_key',
          'talim_shakli','talim_tili','kurs','semestr','guruh','dars_turi')
FORMS = ('kunduzgi','kechki','sirtqi','masofaviy')
LESSONS = ('maruza','amaliy','seminar','laboratoriya')
LESSON_LABELS = {'maruza':'Ma’ruza','amaliy':'Amaliyot','seminar':'Seminar','laboratoriya':'Laboratoriya'}
INSTITUTIONS = {'maktab':'maktablar','universitet':'universitetlar','bogcha':'bogchalar','markaz':'oquv_markazlari'}

def teacher_institutions(cur, user_id, user):
    """Resolve existing staff memberships; never accept workplace IDs from a request."""
    targets = {kind:set() for kind in INSTITUTIONS}
    if user.get('role') != 'oqituvchi':return targets
    for kind,key in [('maktab','maktab_id'),('universitet','universitet_id'),('bogcha','bogcha_id'),('markaz','markaz_id')]:
        if user.get(key):targets[kind].add(int(user[key]))
    cur.execute("SELECT to_regclass('public.foydalanuvchi_muassasalari') AS memberships, to_regclass('public.universitet_xodim_rollari') AS staff")
    tables=cur.fetchone() or {}
    if tables.get('memberships'):
        cur.execute("SELECT muassasa_turi,muassasa_id,lavozim FROM foydalanuvchi_muassasalari WHERE user_id=%s",(user_id,))
        for row in cur.fetchall():
            if row['muassasa_turi'] in targets and row.get('lavozim') not in ('talaba','oquvchi','ota-ona',''):
                targets[row['muassasa_turi']].add(int(row['muassasa_id']))
    if tables.get('staff'):
        cur.execute('SELECT universitet_id FROM universitet_xodim_rollari WHERE user_id=%s AND faol=TRUE',(user_id,))
        targets['universitet'].update(int(row['universitet_id']) for row in cur.fetchall())
    for kind,ids in targets.items():
        if ids:
            cur.execute(f"SELECT id FROM {INSTITUTIONS[kind]} x WHERE id=ANY(%s) AND NULLIF(to_jsonb(x)->>'archived_at','') IS NULL",(sorted(ids),))
            targets[kind]={row['id'] for row in cur.fetchall()}
    return targets

def catalog_context(cur, user_id=None):
    """The server decides which institution sections the current viewer may see."""
    if user_id is None:
        return {'admin':False,'types':['maktab'],'preferred_type':'maktab','grade':'','profile':None}
    cur.execute('SELECT to_jsonb(u) AS profile FROM users u WHERE user_id=%s',(user_id,))
    user=(cur.fetchone() or {}).get('profile') or {}
    cur.execute('SELECT 1 AS ok FROM admin_akkaunt WHERE uid=%s',(user_id,))
    admin=bool(cur.fetchone())
    cur.execute('SELECT to_jsonb(p) AS profile FROM talaba_profillari p WHERE user_id=%s',(user_id,))
    profile=(cur.fetchone() or {}).get('profile') or None
    grade=canonical_grade(user.get('class'))
    teacher = user.get('role') == 'oqituvchi'
    if teacher:
        workplaces=teacher_institutions(cur,user_id,user)
        types=[kind for kind,ids in workplaces.items() if ids]
        grade=''
    elif profile or 'kurs' in grade:
        types=['universitet']
    else:
        types=[t for t,k in [('maktab','maktab_id'),('bogcha','bogcha_id'),('markaz','markaz_id')] if user.get(k)]
        if grade.isdigit() and 'maktab' not in types:types.insert(0,'maktab')
        if not types:types=['maktab']
    preferred=types[0] if types else 'maktab'
    if admin:types=['maktab','bogcha','markaz','universitet']
    return {'admin':admin,'teacher':teacher,'types':types,'preferred_type':preferred,'grade':grade,'profile':None if teacher else profile}

def catalog_filter(institution_type, dars_turi=None, alias='d'):
    if not re.fullmatch(r'[a-z_]+',alias):raise ValueError('Invalid SQL alias')
    if institution_type not in INSTITUTIONS:raise ValueError('Muassasa turi noto‘g‘ri')
    clause=f'{alias}.curriculum_scope_id IN (SELECT id FROM curriculum_scopes WHERE institution_type=%s)'
    params=[institution_type]
    if dars_turi:
        kind=lesson(dars_turi)
        if institution_type!='universitet' or kind not in LESSONS:raise ValueError('Mashg‘ulot turini institut bo‘limidan tanlang')
        clause+=f' AND {alias}.dars_turi=%s';params.append(kind)
    return clause,params

def group_catalog_rows(rows, only_tested=True):
    """Keep identical topic/subject names separate across programs and lessons."""
    subjects={}
    for r in rows:
        codes=r['testli_kodlar'] if only_tested else r['barcha_kodlar']
        if not codes:continue
        key=(r['curriculum_scope_id'],r['grade'],r['subject_code'],r['subject_name'],r['dars_turi'])
        label=r['subject_name'] or 'Boshqa'
        kind=r['dars_turi'] or ''
        subject=subjects.setdefault(key,{'nom':label,'qisqa':r['subject_code'],
            'kalit':json.dumps(key,ensure_ascii=False),'dars_turi':kind,
            'dars_turi_nomi':LESSON_LABELS.get(kind,''),'scope_id':r['curriculum_scope_id'],
            'institution_type':r.get('institution_type','maktab'),
            'institution_name':r.get('institution_name',''),'sinflar':{}})
        group=subject['sinflar'].setdefault(r['grade'],{'sinf':r['grade'],'mavzular':[]})
        group['mavzular'].append({'topic_codes':codes,'nomi':r['nomi'],'savol_soni':r['savol_soni'],
            'dars_turi':kind,'scope_id':r['curriculum_scope_id'],'institution_type':r.get('institution_type','maktab')})
    for subject in subjects.values():
        subject['sinflar']=list(subject['sinflar'].values())
    return list(subjects.values())

def text_key(value):
    return re.sub(r'\s+', ' ', str(value or '').translate(str.maketrans({'‘':"'",'’':"'",'ʻ':"'",'ʼ':"'",'`':"'"}))).strip().casefold()

def canonical_grade(value):
    value = text_key(value)
    match = re.fullmatch(r'([1-6])\s*-?\s*kurs\s*(magistr)?', value)
    if match:
        return f'{match[1]} kurs' + (' magistr' if match[2] else '')
    return value.replace('-sinf','').replace('sinf','').strip()

def lesson(value):
    value = text_key(value).replace("'",'')
    return {'amaliyot':'amaliy','lab':'laboratoriya'}.get(value,value)

def normalize_scope(data):
    s = {k: data.get(k) for k in FIELDS}
    s['institution_type'] = {'institut':'universitet','school':'maktab','institute':'universitet','kindergarten':'bogcha','center':'markaz'}.get(text_key(s['institution_type']),text_key(s['institution_type']))
    if s['institution_type'] not in INSTITUTIONS: raise ValueError('Muassasa turini tanlang')
    for k in ('institution_id','yonalish_id','kurs','semestr'):
        try: s[k] = int(s[k] or 0)
        except (TypeError,ValueError): raise ValueError(f'{k}: butun son kerak')
        if s[k] < 0: raise ValueError(f'{k}: manfiy son mumkin emas')
    for k in ('talim_bosqichi','talim_shakli','talim_tili'): s[k]=text_key(s[k])
    s['yonalish_nomi']=str(data.get('yonalish_nomi') or '').strip()[:160]
    s['yonalish_key']=text_key(s['yonalish_nomi'])
    s['guruh']=re.sub(r'\s+',' ',str(s['guruh'] or '')).strip().upper()
    if len(s['guruh'])>32: raise ValueError('Guruh nomi juda uzun')
    s['dars_turi']=lesson(s['dars_turi'])
    if s['institution_type']=='universitet':
        if not s['institution_id']: raise ValueError('Institutni tanlang')
        if s['talim_bosqichi'] not in ('bakalavr','magistr'): raise ValueError('Bakalavr yoki magistrni tanlang')
        if not s['yonalish_key']: raise ValueError("Yo'nalishni tanlang")
        if s['talim_shakli'] not in (*FORMS,'umumiy'): raise ValueError("Ta'lim shaklini tanlang")
        if s['talim_tili'] not in ('uz','ru','tj','en','kk','kz'): raise ValueError("Ta'lim tilini tanlang")
        if not 1<=s['kurs']<=(2 if s['talim_bosqichi']=='magistr' else 6): raise ValueError('Kurs noto‘g‘ri')
        if s['semestr'] not in (2*s['kurs']-1,2*s['kurs']): raise ValueError('Semestr tanlangan kursga mos emas')
        if s['dars_turi'] not in LESSONS: raise ValueError("Mashg'ulot turini tanlang")
    else:
        for k in ('talim_bosqichi','yonalish_nomi','yonalish_key','talim_shakli','talim_tili','dars_turi'): s[k]=''
        for k in ('yonalish_id','kurs','semestr'): s[k]=0
        if s['institution_type']!='maktab' and not s['institution_id']: raise ValueError('Aniq muassasani tanlang')
    s['scope_key']=hashlib.sha256(json.dumps([s[k] for k in FIELDS],ensure_ascii=False).encode()).hexdigest()
    if s['institution_type']=='maktab' and not s['institution_id'] and not s['guruh']: s['scope_key']='school-common'
    return s

def grade_for_scope(scope):
    if scope['institution_type']=='universitet':
        return f"{scope['kurs']} kurs"+(' magistr' if scope['talim_bosqichi']=='magistr' else '')
    return ''

def scope_label(s):
    bits=[s.get('institution_name') or s['institution_type']]
    if s['institution_type']=='universitet':
        bits += [s['talim_bosqichi'],s.get('yonalish_nomi',''),s['talim_shakli'],s['talim_tili'],f"{s['kurs']}-kurs",f"{s['semestr']}-semestr",s['dars_turi']]
    bits += [s.get('guruh') or 'Barcha guruhlar']
    return ' · '.join(bits)

def migrate(db):
    conn=db()
    try:
        with conn.cursor() as cur:
            cur.execute(Path(__file__).resolve().parents[1].joinpath('migrations/20260920_curriculum_scope.sql').read_text())
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally: conn.close()

def get_scope(cur, scope_id=0):
    if scope_id:
        cur.execute('SELECT * FROM curriculum_scopes WHERE id=%s',(int(scope_id),))
    else:
        cur.execute("SELECT * FROM curriculum_scopes WHERE scope_key='school-common'")
    row=cur.fetchone()
    if not row: raise ValueError('O‘quv dasturi tanlanmagan yoki topilmadi')
    return dict(row)

def admin_filter(cur, scope_id=0, alias='d'):
    if not re.fullmatch(r'[a-z_]+',alias): raise ValueError('Invalid SQL alias')
    scope=get_scope(cur,scope_id)
    return f'{alias}.curriculum_scope_id=%s',[scope['id']]

def club_predicate(user_id, alias='d'):
    """Legacy club material remains available to its teacher and approved members."""
    if not re.fullmatch(r'[a-z_]+',alias): raise ValueError('Invalid SQL alias')
    if user_id is None:return 'FALSE',[]
    return f"""{alias}.curriculum_scope_id IS NULL AND EXISTS (
        SELECT 1 FROM togarak_mavzu_kontenti k JOIN togaraklar t ON t.id=k.togarak_id
        WHERE k.topic_code={alias}.topic_code AND (t.teacher_id=%s OR EXISTS (
            SELECT 1 FROM togarak_azolar a WHERE a.togarak_id=t.id AND a.user_id=%s
            AND a.aktiv=TRUE AND a.tasdiqlangan=TRUE)))""",[user_id,user_id]

def allowed_predicate(cur,user_id=None,alias='d'):
    """No client supplied university/form/course can expand a learner's audience."""
    if not re.fullmatch(r'[a-z_]+',alias): raise ValueError('Invalid SQL alias')
    if user_id is None:
        return f"{alias}.curriculum_scope_id IN (SELECT id FROM curriculum_scopes WHERE scope_key='school-common')",[]
    cur.execute('SELECT to_jsonb(u) AS profile FROM users u WHERE user_id=%s',(user_id,))
    user=(cur.fetchone() or {}).get('profile') or {}
    if not user: return 'FALSE',[]
    cur.execute('SELECT 1 AS ok FROM admin_akkaunt WHERE uid=%s',(user_id,))
    if cur.fetchone(): return 'TRUE',[]
    if user.get('role')=='oqituvchi':
        targets=teacher_institutions(cur,user_id,user)
        clauses=[];params=[]
        for kind,ids in targets.items():
            if ids:
                clauses.append('(cs.institution_type=%s AND cs.institution_id=ANY(%s))')
                params.extend([kind,sorted(ids)])
        if targets['maktab']:clauses.append("cs.scope_key='school-common'")
        if not clauses:return 'FALSE',[]
        return f"EXISTS (SELECT 1 FROM curriculum_scopes cs WHERE cs.id={alias}.curriculum_scope_id AND ({' OR '.join(clauses)}))",params
    cur.execute('SELECT to_jsonb(p) AS profile FROM talaba_profillari p WHERE user_id=%s',(user_id,))
    p=(cur.fetchone() or {}).get('profile') or {}
    if p:
        required=('universitet_id','talim_bosqichi','kurs','semestr','talim_shakli','talim_tili','yonalish_nomi','guruh')
        if any(not p.get(k) for k in required): return 'FALSE',[]
        if int(p['semestr']) not in (2*int(p['kurs'])-1,2*int(p['kurs'])): return 'FALSE',[]
        return f"""EXISTS (SELECT 1 FROM curriculum_scopes cs
          WHERE cs.id={alias}.curriculum_scope_id AND cs.institution_type='universitet'
          AND cs.institution_id=%s AND cs.talim_bosqichi=%s
          AND ((cs.yonalish_id>0 AND cs.yonalish_id=%s) OR (cs.yonalish_id=0 AND cs.yonalish_key=%s))
          AND cs.kurs=%s AND cs.semestr=%s AND cs.talim_shakli IN (%s,'umumiy')
          AND cs.talim_tili=%s AND cs.guruh IN ('',%s)
          AND EXISTS(SELECT 1 FROM universitetlar u WHERE u.id=cs.institution_id
              AND NULLIF(to_jsonb(u)->>'archived_at','') IS NULL))""",[
              p['universitet_id'],p['talim_bosqichi'],p.get('yonalish_id') or 0,text_key(p['yonalish_nomi']),
              p['kurs'],p['semestr'],p['talim_shakli'],p['talim_tili'],str(p['guruh']).strip().upper()]
    # A course without an enrolled student profile must not open other colleges.
    if re.search(r'kurs',str(user.get('class') or ''),re.I): return 'FALSE',[]
    school_grade = canonical_grade(user.get('class'))
    school_clause = ''
    school_params = []
    if user.get('role') in ('oquvchi','talaba'):
        school_clause = f' AND {alias}.grade=%s'
        school_params = [school_grade if school_grade.isdigit() else '__not_school__']
    return f"""EXISTS (SELECT 1 FROM curriculum_scopes cs
        WHERE cs.id={alias}.curriculum_scope_id AND cs.guruh='' AND (
          (cs.institution_type='maktab' AND (cs.scope_key='school-common' OR (cs.institution_id>0 AND cs.institution_id=%s)){school_clause}) OR
          (cs.institution_type='markaz' AND cs.institution_id>0 AND cs.institution_id=%s) OR
          (cs.institution_type='bogcha' AND cs.institution_id>0 AND cs.institution_id=%s)
          ))""",[int(user.get('maktab_id') or 0),*school_params,int(user.get('markaz_id') or 0),int(user.get('bogcha_id') or 0)]

def authorized_codes(cur,user_id,codes,strict=True):
    codes=list(dict.fromkeys(str(c).strip() for c in codes if str(c or '').strip()))
    if not codes: return []
    clause,params=allowed_predicate(cur,user_id)
    cur.execute(f'SELECT d.topic_code FROM dts_tree d WHERE d.is_deleted=FALSE AND d.topic_code=ANY(%s) AND ({clause})',[codes,*params])
    found={r['topic_code'] for r in cur.fetchall()}
    missing=[c for c in codes if c not in found]
    if user_id is not None and missing:
        club_clause, club_params = club_predicate(user_id)
        cur.execute(f"SELECT d.topic_code FROM dts_tree d WHERE d.topic_code=ANY(%s) AND d.is_deleted=FALSE AND ({club_clause})",[missing,*club_params])
        found.update(r['topic_code'] for r in cur.fetchall())
    if strict and any(c not in found for c in codes): raise PermissionError('Mavzu yoki test profil sozlamalaringizga mos emas. Talaba profilingizni tekshiring.')
    return [c for c in codes if c in found]

def check_admin_codes(cur,codes,scope_id):
    s=get_scope(cur,scope_id)
    cur.execute('SELECT topic_code FROM dts_tree WHERE topic_code=ANY(%s) AND curriculum_scope_id=%s AND is_deleted=FALSE',(list(codes),s['id']))
    found={r['topic_code'] for r in cur.fetchall()}
    if any(c not in found for c in codes): raise ValueError('Tanlangan mavzular boshqa o‘quv dasturiga tegishli yoki o‘chirilgan')
    return s
