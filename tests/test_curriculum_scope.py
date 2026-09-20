"""Run audience predicates against SQLite fixtures and real handlers via AST.
This verifies relational filters and transactions, not PostgreSQL migration DDL.
"""
import ast, asyncio, copy, io, json, re, sqlite3, unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
import openpyxl
from modules import curriculum_scope as scope
from modules.test_template_import import populated_test_codes
BASE=dict(institution_type='universitet',institution_id=11,talim_bosqichi='bakalavr',yonalish_id=7,yonalish_nomi='Boshlang‘ich ta’lim',talim_shakli='kechki',talim_tili='uz',kurs=1,semestr=1,guruh='',dars_turi='maruza')
PROFILE=dict(universitet_id=11,talim_bosqichi='bakalavr',yonalish_id=7,yonalish_nomi='Boshlang‘ich ta’lim',talim_shakli='kechki',talim_tili='uz',kurs=1,semestr=1,guruh='101')
class HTTPException(Exception):
 def __init__(self,status_code,detail):super().__init__(detail);self.status_code=status_code;self.detail=detail
class DB:
 def __init__(self):
  self.sql=sqlite3.connect(':memory:');self.sql.row_factory=sqlite3.Row
  self.sql.create_function('regexp',2,lambda p,v:bool(re.search(p,str(v or ''))))
  self.user={'class':'1 kurs','role':'oquvchi'};self.profile=copy.deepcopy(PROFILE);self.admin=False;self.rollbacks=0
  self.sql.executescript('''
  CREATE TABLE curriculum_scopes(id INTEGER PRIMARY KEY,scope_key TEXT UNIQUE,institution_type TEXT,institution_id INTEGER,institution_name TEXT,talim_bosqichi TEXT,yonalish_id INTEGER,yonalish_key TEXT,yonalish_nomi TEXT,talim_shakli TEXT,talim_tili TEXT,kurs INTEGER,semestr INTEGER,guruh TEXT,dars_turi TEXT);
  CREATE TABLE dts_tree(topic_code TEXT PRIMARY KEY,curriculum_scope_id INTEGER,grade TEXT,subject_code TEXT,subject_name TEXT,dars_turi TEXT,quarter TEXT,bob_code TEXT,bob_name TEXT,bolim_code TEXT,bolim_name TEXT,mavzu_code TEXT,mavzu_name TEXT,kichik_code TEXT,kichik_name TEXT,is_deleted BOOLEAN DEFAULT FALSE);
  CREATE TABLE universitetlar(id INTEGER PRIMARY KEY,archived_at TEXT,nomi TEXT);
  INSERT INTO universitetlar VALUES(11,NULL,'Institut A'),(12,NULL,'Institut B');
  CREATE TABLE maktablar(id INTEGER PRIMARY KEY,archived_at TEXT,nomi TEXT);
  INSERT INTO maktablar VALUES(11,NULL,'Maktab A'),(12,NULL,'Maktab B');
  CREATE TABLE bogchalar(id INTEGER PRIMARY KEY,archived_at TEXT,nomi TEXT);
  INSERT INTO bogchalar VALUES(11,NULL,'Bogcha A'),(12,NULL,'Bogcha B');
  CREATE TABLE oquv_markazlari(id INTEGER PRIMARY KEY,archived_at TEXT,nomi TEXT);
  INSERT INTO oquv_markazlari VALUES(11,NULL,'Markaz A'),(12,NULL,'Markaz B');
  CREATE TABLE foydalanuvchi_muassasalari(user_id INTEGER,muassasa_turi TEXT,muassasa_id INTEGER,lavozim TEXT);
  CREATE TABLE universitet_xodim_rollari(user_id INTEGER,universitet_id INTEGER,faol BOOLEAN);
  CREATE TABLE generated_tests(id INTEGER PRIMARY KEY,topic_code TEXT);
  CREATE TABLE togarak_mavzu_kontenti(topic_code TEXT,togarak_id INTEGER);
  CREATE TABLE togaraklar(id INTEGER,teacher_id INTEGER);
  CREATE TABLE togarak_azolar(togarak_id INTEGER,user_id INTEGER,aktiv BOOLEAN,tasdiqlangan BOOLEAN);
  ''')
 def cursor(self):return Cursor(self)
 def commit(self):self.sql.commit()
 def rollback(self):self.rollbacks+=1;self.sql.rollback()
 def close(self):pass
 def add_scope(self,id,**changes):
  d=scope.normalize_scope({**BASE,**changes});d.update(id=id,institution_name='Institut')
  self.sql.execute(f"INSERT INTO curriculum_scopes({','.join(d)}) VALUES({','.join('?' for _ in d)})",list(d.values()));return d
 def add_topic(self,id,grade='1 kurs'):
  code=f'{grade}-{id:02d}-01-01-01-01-01'
  lesson=self.sql.execute('SELECT dars_turi FROM curriculum_scopes WHERE id=?',(id,)).fetchone()[0]
  self.sql.execute('INSERT INTO dts_tree(topic_code,curriculum_scope_id,grade,subject_code,subject_name,dars_turi,quarter,mavzu_name) VALUES(?,?,?,?,?,?,?,?)',(code,id,grade,f'{id:02d}','MATEMATIKA',lesson or None,'01','To‘plamlar'));return code
 def visible(self,uid=5):
  clause,args=scope.allowed_predicate(self.cursor(),uid);cur=self.cursor()
  cur.execute(f'SELECT d.topic_code FROM dts_tree d WHERE d.is_deleted=FALSE AND ({clause})',args)
  return {r['topic_code'] for r in cur.fetchall()}
class Cursor:
 def __init__(self,db):self.db=db;self.rows=[];self.rowcount=0
 def execute(self,sql,args=()):
  if 'SELECT to_jsonb(u) AS profile FROM users' in sql:self.rows=[{'profile':self.db.user}];return
  if 'SELECT to_jsonb(p) AS profile FROM talaba_profillari' in sql:self.rows=[{'profile':self.db.profile}];return
  if 'FROM admin_akkaunt' in sql:self.rows=[{'ok':1}] if self.db.admin else [];return
  if 'pg_advisory_xact_lock' in sql:self.rows=[];return
  if "to_regclass('public.foydalanuvchi_muassasalari')" in sql:self.rows=[{'memberships':True,'staff':True}];return
  sql=sql.replace(' FOR UPDATE','').replace("NULLIF(to_jsonb(u)->>'archived_at','')","NULLIF(u.archived_at,'')")
  sql=sql.replace("NULLIF(to_jsonb(x)->>'archived_at','')","NULLIF(x.archived_at,'')")
  sql=sql.replace('ARRAY_AGG(DISTINCT d.topic_code ORDER BY d.topic_code)','json_group_array(DISTINCT d.topic_code)')
  sql=re.sub(r'=\s*ANY\(%s\)',' IN (SELECT value FROM json_each(%s))',sql)
  sql=re.sub(r"(\w+) ~ ('[^']+')",r'REGEXP(\2,\1)',sql).replace('%s','?').replace('NOW()','CURRENT_TIMESTAMP')
  args=[json.dumps(a) if isinstance(a,(list,tuple)) else a for a in args]
  c=self.db.sql.execute(sql,args);self.rowcount=c.rowcount;self.rows=[dict(r) for r in c.fetchall()] if c.description else []
  for row in self.rows:
   for key in ('barcha_kodlar','testli_kodlar'):
    if key in row:row[key]=json.loads(row[key] or '[]')
 def fetchone(self):return self.rows.pop(0) if self.rows else None
 def fetchall(self):r=self.rows;self.rows=[];return r
 def close(self):pass
class AudienceTests(unittest.TestCase):
 def setUp(self):self.db=DB();self.db.add_scope(1);self.code=self.db.add_topic(1)
 def test_all_dimensions_exclude_other_audiences(self):
  cases=[{'institution_id':12},{'yonalish_id':8},{'talim_bosqichi':'magistr'},{'talim_shakli':'kunduzgi'},{'talim_shakli':'sirtqi'},{'talim_tili':'ru'},{'kurs':2,'semestr':3},{'semestr':2},{'guruh':'102'},{'institution_type':'maktab','institution_id':0},{'institution_type':'bogcha','institution_id':11},{'institution_type':'markaz','institution_id':11}]
  for i,c in enumerate(cases,2):self.db.add_scope(i,**c);self.db.add_topic(i)
  self.assertEqual(self.db.visible(),{self.code})
 def test_shared_form_still_checks_institute(self):
  self.db.add_scope(2,talim_shakli='umumiy');shared=self.db.add_topic(2)
  self.db.add_scope(3,talim_shakli='umumiy',institution_id=12);self.db.add_topic(3)
  self.assertEqual(self.db.visible(),{self.code,shared})
 def test_missing_profile_fields_fail_closed(self):
  for field in ('universitet_id','talim_bosqichi','yonalish_nomi','talim_shakli','talim_tili','kurs','semestr','guruh'):
   with self.subTest(field=field):self.db.profile={**PROFILE,field:None};self.assertEqual(self.db.visible(),set())
 def test_missing_student_profile(self):self.db.profile=None;self.assertEqual(self.db.visible(),set())
 def test_archived_institution(self):self.db.sql.execute("UPDATE universitetlar SET archived_at='2026-09-20' WHERE id=11");self.assertEqual(self.db.visible(),set())
 def test_current_profile_form_is_authoritative(self):
  self.db.add_scope(2,talim_shakli='sirtqi');other=self.db.add_topic(2);self.db.profile['talim_shakli']='sirtqi';self.assertEqual(self.db.visible(),{other})
 def test_invalid_semester(self):self.db.profile['semestr']=3;self.assertEqual(self.db.visible(),set())
 def test_guest_and_zero_mean_school_common(self):
  self.db.add_scope(2,institution_type='maktab',institution_id=0);school=self.db.add_topic(2,grade='7')
  self.assertEqual(self.db.visible(None),{school});self.assertEqual(scope.get_scope(self.db.cursor(),0)['id'],2)
 def test_role_string_not_admin_authority(self):
  self.db.user['role']='admin';self.db.add_scope(2,institution_id=12);other=self.db.add_topic(2)
  self.assertNotIn(other,self.db.visible());self.db.admin=True;self.assertIn(other,self.db.visible())
 def test_direct_or_mixed_foreign_codes_denied(self):
  self.db.add_scope(2,institution_id=12);other=self.db.add_topic(2)
  with self.assertRaises(PermissionError):scope.authorized_codes(self.db.cursor(),5,[self.code,other])
  self.assertEqual(scope.authorized_codes(self.db.cursor(),5,[self.code,other],strict=False),[self.code])
 def test_deleted_codes_denied(self):
  self.db.sql.execute('UPDATE dts_tree SET is_deleted=TRUE')
  with self.assertRaises(PermissionError):scope.authorized_codes(self.db.cursor(),5,[self.code])
 def test_legacy_unassigned_hidden(self):self.db.sql.execute('UPDATE dts_tree SET curriculum_scope_id=NULL');self.assertEqual(self.db.visible(),set())
 def test_group_and_manual_name_normalization(self):
  self.db.add_scope(2,guruh=' 101 ',yonalish_id=0,yonalish_nomi="Boshlang'ich ta'lim");code=self.db.add_topic(2);self.assertIn(code,self.db.visible())
 def test_lessons_separate_but_both_available(self):
  self.db.add_scope(2,dars_turi='amaliy');code=self.db.add_topic(2);self.assertEqual(self.db.visible(),{self.code,code})
 def test_private_club_requires_approved_membership(self):
  self.db.sql.execute('UPDATE dts_tree SET curriculum_scope_id=NULL')
  self.db.sql.execute('INSERT INTO togaraklar VALUES(90,20)')
  self.db.sql.execute('INSERT INTO togarak_mavzu_kontenti VALUES(?,90)',(self.code,))
  self.db.sql.execute('INSERT INTO togarak_azolar VALUES(90,5,TRUE,FALSE)')
  with self.assertRaises(PermissionError):scope.authorized_codes(self.db.cursor(),5,[self.code])
  self.db.sql.execute('UPDATE togarak_azolar SET tasdiqlangan=TRUE')
  self.assertEqual(scope.authorized_codes(self.db.cursor(),5,[self.code]),[self.code])
  self.assertEqual(scope.authorized_codes(self.db.cursor(),20,[self.code]),[self.code])
class NormalizationTests(unittest.TestCase):
 def test_course_not_school(self):
  for raw in ('1kurs','1 kurs','1-kurs',' 1 KURS '):self.assertEqual(scope.canonical_grade(raw),'1 kurs')
  self.assertEqual(scope.canonical_grade('1-kurs magistr'),'1 kurs magistr')
 def test_lesson_apostrophes(self):
  for raw in ("Ma'ruza",'Ma‘ruza','Ma’ruza','Maʻruza','MAʼRUZA'):self.assertEqual(scope.lesson(raw),'maruza')
 def test_bad_scopes(self):
  for c in ({'institution_id':0},{'talim_shakli':''},{'semestr':3},{'dars_turi':''},{'talim_tili':'xx'},{'yonalish_nomi':''}):
   with self.subTest(c=c),self.assertRaises(ValueError):scope.normalize_scope({**BASE,**c})
 def test_key_separates_form_and_lesson(self):
  a=scope.normalize_scope(BASE)['scope_key']
  for c in ({'talim_shakli':'sirtqi'},{'dars_turi':'amaliy'}):self.assertNotEqual(a,scope.normalize_scope({**BASE,**c})['scope_key'])
class WorkbookReplacementTests(unittest.TestCase):
 def sheet(self,rows):
  w=openpyxl.Workbook();ws=w.active;ws.title='TESTLAR'
  ws.append(['topic_code','question','correct_answer'])
  for row in rows:ws.append(row)
  return SimpleNamespace(name=ws.title,worksheet=ws,headers=['topic_code','question','correct_answer'])
 def test_blank_placeholder_does_not_replace_existing_topic(self):
  codes,by_sheet=populated_test_codes([self.sheet([['own','Savol','A'],['keep',None,None]])])
  self.assertEqual(codes,{'own'});self.assertEqual(by_sheet['TESTLAR'],{'own'})
 def test_partial_question_aborts_whole_upload(self):
  for row in ([None,'Savol','A'],['own','Savol',None]):
   with self.assertRaises(ValueError):populated_test_codes([self.sheet([['valid','Savol','B'],row])])
 def test_empty_template_cannot_erase_tests(self):
  with self.assertRaises(ValueError):populated_test_codes([self.sheet([['keep',None,None]])])
 def test_numeric_zero_is_a_valid_answer(self):
  self.assertEqual(populated_test_codes([self.sheet([['own','2-2?',0]])])[0],{'own'})
class EndpointTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  p=Path(__file__).resolve().parents[1]/'samtm_platform.py';t=ast.parse(p.read_text())
  names={'_dts_matn_normalize','_dts_sinf_normalize','_dts_chorak_normalize','_dts_fan_kodi_ol','_dts_bob_kodi_ol','_dts_bolim_kodi_ol','_dts_mavzu_kodi_ol','_dts_kichik_kodi_ol','_dts_qator_kiritish','_curriculum_scope','_mavzularni_parse','topik_toliq_yarat','topik_import','test_savollari','test_savollari_soni','aralash_savollari_soni','aralash_test_savollari','_curriculum_guard'}
  nodes=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
  for n in nodes:n.decorator_list=[]
  cls.code=compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec')
 def setUp(self):
  self.db=DB();self.db.add_scope(1);self.db.add_scope(2,institution_id=12);self.db.commit()
  ns={'re':re,'io':io,'Optional':Optional,'_curriculum':scope,'HTTPException':HTTPException,'_db':lambda:self.db,'_admin_tekshir':lambda t:99,'_jwt_tekshir':lambda t:5,'_sinf_talaba_mi':lambda x:'kurs' in x,'TopikShablonSorov':SimpleNamespace,'AralashTestSorovi':SimpleNamespace,'AralashSoniSorovi':SimpleNamespace,'UploadFile':object,'File':lambda *a,**k:None}
  exec(self.code,ns);self.ns=ns
 def test_idempotent_topics_with_distinct_scope_codes(self):
  fn=self.ns['_dts_qator_kiritish'];args=('1kurs','Matematika','1','','','To‘plamlar','');cur=self.db.cursor()
  a,_=fn(cur,*args,'maruza',1);b,status=fn(cur,*args,'maruza',1);c,_=fn(cur,*args,'maruza',2)
  self.assertEqual(a,b);self.assertEqual(status,'mavjud');self.assertNotEqual(a,c);self.assertTrue(a.startswith('1 kurs-'))
 def test_wrong_course_or_lesson_rejected(self):
  for grade,lesson in [('2 kurs','maruza'),('1 kurs','amaliy')]:
   with self.assertRaises(ValueError):self.ns['_dts_qator_kiritish'](self.db.cursor(),grade,'Matematika','1','','','Mavzu','',lesson,1)
 def test_invalid_line_not_dropped(self):
  with self.assertRaises(HTTPException):self.ns['_mavzularni_parse']('1 / Mavzu\n/ Tushib qolmasin')
 def upload(self,rows):
  w=openpyxl.Workbook();s=w.active
  for row in rows:s.append(row)
  b=io.BytesIO();w.save(b)
  class File:
   async def read(self,*a):return b.getvalue()
  return asyncio.run(self.ns['topik_import']('token',File(),1))
 def test_foreign_existing_code_cannot_be_reassigned(self):
  code=self.db.add_topic(2);self.db.commit()
  with self.assertRaises(HTTPException):self.upload([['Sinf','Fan','Mavzu','topic_code'],['1 kurs','Matematika','Yangi',code]])
  self.assertEqual(self.db.sql.execute('SELECT curriculum_scope_id FROM dts_tree').fetchone()[0],2)
 def test_import_rolls_back_all_rows(self):
  with self.assertRaises(HTTPException):self.upload([['Sinf','Fan','Mavzu','scope_id'],['1 kurs','Matematika','First',1],['1 kurs','Matematika','Second',2]])
  self.assertEqual(self.db.sql.execute('SELECT COUNT(*) FROM dts_tree').fetchone()[0],0);self.assertGreater(self.db.rollbacks,0)
 def test_direct_count_and_question_routes_reject_foreign_code(self):
  code=self.db.add_topic(2)
  for name in ('test_savollari','test_savollari_soni'):
   with self.subTest(name=name),self.assertRaises(HTTPException) as e:self.ns[name](code,token='student')
   self.assertEqual(e.exception.status_code,403)
 def test_mixed_count_and_question_routes_reject_foreign_code(self):
  code=self.db.add_topic(2)
  for name in ('aralash_test_savollari','aralash_savollari_soni'):
   with self.subTest(name=name),self.assertRaises(HTTPException) as e:self.ns[name](SimpleNamespace(token='student',topic_codes=[code]))
   self.assertEqual(e.exception.status_code,403)
if __name__=='__main__':unittest.main()
