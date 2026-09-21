"""Administration of explicit curriculum audiences; registered by main.py."""
from fastapi import APIRouter, HTTPException
from . import curriculum_scope as scope


def create_router(platform):
    router=APIRouter(prefix='/api/admin/curriculum',tags=['curriculum'])
    def error(exc): return HTTPException(status_code=400,detail=str(exc))

    @router.get('/scopes')
    def list_scopes(token:str):
        platform._admin_tekshir(token)
        conn=platform._db();cur=conn.cursor()
        try:
            cur.execute('SELECT * FROM curriculum_scopes ORDER BY institution_type,institution_name,talim_bosqichi,yonalish_nomi,talim_shakli,kurs,semestr,dars_turi,id')
            rows=[dict(r) for r in cur.fetchall()]
            for r in rows: r.update(label=scope.scope_label(r),grade=scope.grade_for_scope(r))
            cur.execute('SELECT COUNT(*) AS n FROM dts_tree WHERE curriculum_scope_id IS NULL AND is_deleted=FALSE')
            return {'scopes':rows,'unassigned':cur.fetchone()['n']}
        finally:cur.close();conn.close()

    @router.get('/options')
    def options(token:str,institution_type:str='universitet',institution_id:int=0):
        platform._admin_tekshir(token)
        table=scope.INSTITUTIONS.get(institution_type)
        if not table:raise HTTPException(400,'Muassasa turi noto‘g‘ri')
        conn=platform._db();cur=conn.cursor()
        try:
            cur.execute('SELECT to_regclass(%s) AS t',(table,))
            if not cur.fetchone()['t']:return {'institutions':[],'programs':[]}
            cur.execute(f"SELECT id,nomi FROM {table} x WHERE NULLIF(to_jsonb(x)->>'archived_at','') IS NULL ORDER BY nomi")
            rows=list(cur.fetchall())
            programs=platform._talaba_yonalishlari(cur,institution_id) if institution_type=='universitet' and institution_id else []
            return {'institutions':rows,'programs':programs}
        finally:cur.close();conn.close()

    def save_scope(cur, payload):
        data=dict(payload)
        data['institution_type'] = {'institut':'universitet','institute':'universitet'}.get(scope.text_key(data.get('institution_type')),scope.text_key(data.get('institution_type')))
        if data.get('institution_type')=='universitet':
            programs=platform._talaba_yonalishlari(cur,int(data.get('institution_id') or 0))
            if programs and not data.get('yonalish_id'):raise ValueError('Yo‘nalishni institutning rasmiy ro‘yxatidan tanlang')
        if data.get('institution_type')=='universitet' and data.get('yonalish_id'):
            program=next((p for p in programs if p['id']==int(data['yonalish_id'])),None)
            if not program:raise ValueError('Yo‘nalish tanlangan institutga tegishli emas yoki faol emas')
            if data.get('talim_bosqichi')!=program['bosqich']:raise ValueError('Bosqich yo‘nalishga mos emas')
            data['yonalish_nomi']=program['nomi']
            if program['shakllar'] and data.get('talim_shakli') not in (*program['shakllar'],'umumiy'):raise ValueError('Bu yo‘nalishda tanlangan ta’lim shakli mavjud emas')
            if program['tillar'] and data.get('talim_tili') not in program['tillar']:raise ValueError('Bu yo‘nalishda tanlangan til mavjud emas')
            pairs=program.get('variantlar') or []
            if pairs and data.get('talim_shakli')!='umumiy' and {'shakl':data.get('talim_shakli'),'til':data.get('talim_tili')} not in pairs:raise ValueError('Ta’lim shakli va til kombinatsiyasi mavjud emas')
        s=scope.normalize_scope(data)
        if s['institution_id']:
            table=scope.INSTITUTIONS[s['institution_type']]
            cur.execute(f"SELECT nomi FROM {table} x WHERE id=%s AND NULLIF(to_jsonb(x)->>'archived_at','') IS NULL",(s['institution_id'],))
            inst=cur.fetchone()
            if not inst:raise ValueError('Muassasa topilmadi yoki arxivlangan')
            s['institution_name']=inst['nomi']
        else:s['institution_name']='Maktab — umumiy katalog'
        if s['institution_type']=='universitet':
            cur.execute('SELECT pg_advisory_xact_lock(hashtext(%s))',(repr(scope.scope_identity(s)),))
            existing=next((r for r in scope.year_family(cur,s) if r['semestr']==s['semestr']),None)
            if existing:
                cur.execute('UPDATE curriculum_scopes SET institution_name=%s,yonalish_nomi=%s,yonalish_key=%s WHERE id=%s RETURNING *',(s['institution_name'],s['yonalish_nomi'],s['yonalish_key'],existing['id']))
                result=dict(cur.fetchone());result.update(label=scope.scope_label(result),grade=scope.grade_for_scope(result));return result
        cols=(*scope.FIELDS,'scope_key','institution_name','yonalish_nomi')
        cur.execute(f"INSERT INTO curriculum_scopes({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))}) ON CONFLICT(scope_key) DO UPDATE SET institution_name=EXCLUDED.institution_name RETURNING *",[s[k] for k in cols])
        result=dict(cur.fetchone())
        result.update(label=scope.scope_label(result),grade=scope.grade_for_scope(result))
        return result

    @router.post('/scopes')
    def create_scope(payload:dict,token:str):
        platform._admin_tekshir(token)
        conn=platform._db();cur=conn.cursor()
        try:
            result=save_scope(cur,payload)
            conn.commit()
            return {'scope':result}
        except (ValueError,TypeError) as exc:
            conn.rollback();raise error(exc)
        except Exception:
            conn.rollback();raise
        finally:cur.close();conn.close()

    @router.post('/programs')
    def create_program(payload:dict,token:str):
        """Both semesters open their four lesson sections atomically."""
        platform._admin_tekshir(token)
        conn=platform._db();cur=conn.cursor()
        try:
            kind=scope.text_key(payload.get('institution_type'))
            lessons=scope.LESSONS if kind in ('universitet','institut','institute') else ('',)
            periods=scope.semester_pair(payload.get('kurs')) if kind in ('universitet','institut','institute') else (0,)
            results=[save_scope(cur,{**payload,'semestr':semester,'dars_turi':lesson}) for semester in periods for lesson in lessons]
            conn.commit()
            return {'scopes':results,'scope':results[0]}
        except (ValueError,TypeError) as exc:
            conn.rollback();raise error(exc)
        except Exception:
            conn.rollback();raise
        finally:cur.close();conn.close()

    @router.get('/unassigned')
    def unassigned(token:str):
        platform._admin_tekshir(token)
        conn=platform._db();cur=conn.cursor()
        try:
            cur.execute("""SELECT grade,subject_name,dars_turi,COUNT(*) AS count,
                ARRAY_AGG(topic_code ORDER BY topic_code) AS topic_codes
                FROM dts_tree WHERE curriculum_scope_id IS NULL AND is_deleted=FALSE
                GROUP BY grade,subject_name,dars_turi ORDER BY grade,subject_name,dars_turi""")
            return {'groups':list(cur.fetchall())}
        finally:cur.close();conn.close()

    @router.post('/assign-legacy')
    def assign_legacy(payload:dict,token:str):
        platform._admin_tekshir(token)
        codes=list(dict.fromkeys(str(c) for c in payload.get('topic_codes',[]) if c))
        if not codes or not payload.get('scope_id'):raise HTTPException(400,'Dastur va eski mavzularni tanlang')
        conn=platform._db();cur=conn.cursor()
        try:
            s=scope.get_scope(cur,payload['scope_id'])
            cur.execute('SELECT * FROM dts_tree WHERE topic_code=ANY(%s) FOR UPDATE',(codes,))
            rows=list(cur.fetchall())
            if len(rows)!=len(codes):raise ValueError('Ayrim mavzular topilmadi')
            for r in rows:
                if r['curriculum_scope_id'] is not None:raise ValueError('Mavzu allaqachon boshqa dasturga biriktirilgan')
                if s['institution_type']=='maktab' and scope.canonical_grade(r['grade']) not in {str(i) for i in range(1,12)}:raise ValueError('Maktab dasturiga faqat 1–11-sinf mavzusi biriktiriladi')
                if scope.grade_for_scope(s) and scope.canonical_grade(r['grade'])!=scope.grade_for_scope(s):raise ValueError('Eski mavzu kursi tanlangan dasturga mos emas')
                if r.get('dars_turi') and s['institution_type']=='universitet' and scope.lesson(r['dars_turi'])!=s['dars_turi']:raise ValueError('Mashg‘ulot turi mos emas')
            cur.execute("INSERT INTO curriculum_legacy_backup(topic_code,old_row) SELECT topic_code,to_jsonb(d) FROM dts_tree d WHERE topic_code=ANY(%s) ON CONFLICT(topic_code) DO NOTHING",(codes,))
            cur.execute('UPDATE dts_tree SET curriculum_scope_id=%s,dars_turi=%s,grade=COALESCE(NULLIF(%s,\'\'),grade) WHERE topic_code=ANY(%s)',(s['id'],s['dars_turi'] or None,scope.grade_for_scope(s),codes))
            count=cur.rowcount;conn.commit();return {'assigned':count}
        except ValueError as exc:conn.rollback();raise error(exc)
        finally:cur.close();conn.close()
    return router
