"""Real catalog/router handlers with relational fixtures; no production DB required."""
import ast
import sqlite3
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
from test_curriculum_scope import BASE,DB,HTTPException,scope

ROOT=Path(__file__).resolve().parents[1]

class Router:
 def __init__(self,**kwargs):self.routes={}
 def route(self,path):
  def register(fn):self.routes[path]=fn;return fn
  return register
 get=post=route

def load_function(path,name,namespace):
 node=next(node for node in ast.parse(path.read_text()).body if isinstance(node,ast.FunctionDef) and node.name==name)
 node.decorator_list=[]
 exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
 return namespace[name]

class CatalogTests(unittest.TestCase):
 def setUp(self):
  self.db=DB()
  self.catalog=load_function(ROOT/'samtm_platform.py','mavzular_royxati',{
   'Optional':Optional,'_db':lambda:self.db,'_curriculum':scope,'_jwt_tekshir':lambda token:5,'HTTPException':HTTPException})
 def topic(self,id,**changes):
  grade=changes.pop('grade','1 kurs')
  self.db.add_scope(id,**changes);code=self.db.add_topic(id,grade)
  self.db.sql.execute('INSERT INTO generated_tests(topic_code) VALUES(?)',(code,))
  return code
 def codes(self,result):return {code for subject in result['fanlar'] for group in subject['sinflar'] for topic in group['mavzular'] for code in topic['topic_codes']}
 def test_admin_can_open_all_four_sections(self):
  self.db.admin=True
  for id,kind in enumerate(('maktab','bogcha','markaz','universitet'),1):
   code=self.topic(id,institution_type=kind)
   result=self.catalog(token='admin',institution_type=kind)
   self.assertEqual(self.codes(result),{code});self.assertEqual(set(result['viewer']['types']),set(scope.INSTITUTIONS))
 def test_student_gets_only_own_program_and_four_separate_lessons(self):
  own={}
  for id,kind in enumerate(scope.LESSONS,1):own[kind]=self.topic(id,dars_turi=kind)
  self.topic(5,talim_shakli='sirtqi');self.topic(6,institution_id=12);self.topic(7,institution_type='maktab',grade='1')
  result=self.catalog(token='student')
  self.assertEqual(self.codes(result),set(own.values()));self.assertEqual(result['viewer']['types'],['universitet'])
  self.assertEqual(len(result['fanlar']),4)
  for kind,code in own.items():self.assertEqual(self.codes(self.catalog(token='student',dars_turi=kind)),{code})
  self.assertEqual(self.codes(self.catalog(token='student',institution_type='maktab')),set())
 def test_lesson_and_scope_do_not_merge_identical_names(self):
  self.db.admin=True
  self.topic(1);self.topic(2,institution_id=12);self.topic(3,dars_turi='seminar')
  self.db.sql.execute("UPDATE dts_tree SET subject_code='01'")
  rows=self.catalog(token='admin',institution_type='universitet')['fanlar']
  self.assertEqual(len(rows),3);self.assertEqual(len({row['kalit'] for row in rows}),3)
 def test_explicit_scope_narrows_admin_catalog_and_cannot_expand_student_access(self):
  self.topic(1);foreign=self.topic(2,institution_id=12)
  self.assertEqual(self.codes(self.catalog(token='student',scope_id=2)),set())
  self.db.admin=True
  self.assertEqual(self.codes(self.catalog(token='admin',institution_type='universitet',scope_id=2)),{foreign})
 def test_pupil_cannot_expand_grade_or_institution_via_query(self):
  self.db.profile=None;self.db.user={'role':'oquvchi','class':'7-sinf','maktab_id':11}
  own=self.topic(1,institution_type='maktab',institution_id=0,grade='7')
  self.topic(2,institution_type='maktab',institution_id=11,grade='8')
  self.topic(3,institution_type='maktab',institution_id=12,grade='7')
  self.topic(4,institution_type='bogcha',grade='7')
  self.assertEqual(self.codes(self.catalog(token='pupil')),{own})
  self.assertEqual(self.codes(self.catalog(token='pupil',sinf='8')),set())
  self.assertEqual(self.codes(self.catalog(token='pupil',institution_type='bogcha')),set())
  with self.assertRaises(PermissionError):scope.authorized_codes(self.db.cursor(),5,['8-02-01-01-01-01-01'])
 def test_kindergarten_and_center_cannot_see_another_institution(self):
  for kind,key in [('bogcha','bogcha_id'),('markaz','markaz_id')]:
   with self.subTest(kind=kind):
    self.setUp();self.db.profile=None;self.db.user={'role':'oquvchi','class':'A1',key:11}
    own=self.topic(1,institution_type=kind,grade='A1');self.topic(2,institution_type=kind,institution_id=12,grade='A1')
    self.assertEqual(self.codes(self.catalog(token='learner')),{own})
    self.assertEqual(self.catalog(token='learner')['viewer']['types'],[kind])
 def test_topics_without_tests_are_visible_only_in_topics_catalog(self):
  self.topic(1);self.db.sql.execute('DELETE FROM generated_tests')
  self.assertEqual(self.catalog(token='student')['fanlar'],[])
  self.assertEqual(len(self.catalog(token='student',faqat_testli=False)['fanlar']),1)
 def test_unknown_institution_or_lesson_is_rejected(self):
  for changes in ({'institution_type':'invalid'},{'institution_type':'maktab','dars_turi':'maruza'},{'institution_type':'universitet','dars_turi':'invalid'}):
   with self.subTest(changes=changes),self.assertRaises(HTTPException) as error:self.catalog(token='student',**changes)
   self.assertEqual(error.exception.status_code,400)
 def test_teacher_has_own_workplaces_and_not_other_institutes(self):
  self.db.profile=None;self.db.user={'role':'oqituvchi','universitet_id':11}
  own=self.topic(1);self.topic(2,institution_id=12);self.topic(3,institution_type='markaz')
  self.assertEqual(self.codes(self.catalog(token='teacher')),{own})
  self.assertEqual(self.catalog(token='teacher')['viewer']['types'],['universitet'])
  self.db.sql.execute("INSERT INTO foydalanuvchi_muassasalari VALUES(5,'markaz',11,'oqituvchi')")
  self.assertEqual(self.catalog(token='teacher')['viewer']['types'],['universitet','markaz'])
  self.assertEqual(len(self.codes(self.catalog(token='teacher',institution_type='markaz'))),1)
 def test_teacher_archived_and_inactive_workplaces_are_excluded(self):
  self.db.profile=None;self.db.user={'role':'oqituvchi'}
  self.topic(1);self.topic(2,institution_id=12)
  self.db.sql.execute('INSERT INTO universitet_xodim_rollari VALUES(5,11,TRUE),(5,12,FALSE)')
  self.assertEqual(len(self.codes(self.catalog(token='teacher'))),1)
  self.db.sql.execute("UPDATE universitetlar SET archived_at='2026' WHERE id=11")
  self.assertEqual(self.catalog(token='teacher')['viewer']['types'],[])
  self.assertEqual(self.codes(self.catalog(token='teacher')),set())

 def test_student_sees_both_semesters_as_one_subject_with_distinct_topics(self):
  for course in range(1,5):
   with self.subTest(course=course):
    self.setUp();a,b=scope.semester_pair(course);self.db.profile.update(kurs=course,semestr=a);self.db.user['class']=f'{course} kurs'
    own={self.topic(1,kurs=course,semestr=a,grade=f'{course} kurs'),self.topic(2,kurs=course,semestr=b,grade=f'{course} kurs')}
    self.topic(3,kurs=course,semestr=b,talim_shakli='sirtqi',grade=f'{course} kurs')
    result=self.catalog(token='student');self.assertEqual(self.codes(result),own)
    self.assertEqual(len(result['fanlar']),1);subject=result['fanlar'][0];self.assertEqual(subject['semestrlar'],[a,b]);self.assertEqual(self.codes(self.catalog(token='student',scope_id=1)),own)
    self.assertEqual({t['semestr'] for t in subject['sinflar'][0]['mavzular']},{a,b})
    self.db.profile['semestr']=b;self.assertEqual(self.codes(self.catalog(token='student')),own)

class ProgramTests(unittest.TestCase):
 def setUp(self):
  self.db=DB()
  def admin(token):
   if token!='admin':raise HTTPException(403,'Faqat admin')
  program={'id':7,'nomi':BASE['yonalish_nomi'],'bosqich':'bakalavr','shakllar':['kechki','kunduzgi'],'tillar':['uz','ru'],
   'variantlar':[{'shakl':'kechki','til':'uz'},{'shakl':'kunduzgi','til':'ru'}]}
  platform=SimpleNamespace(_db=lambda:self.db,_admin_tekshir=admin,_talaba_yonalishlari=lambda cur,id:[program] if id==11 else [])
  create=load_function(ROOT/'modules/curriculum_api.py','create_router',{'APIRouter':Router,'HTTPException':HTTPException,'scope':scope})
  self.create=create(platform).routes['/programs']
 def test_program_creation_opens_two_semesters_four_lessons_and_is_idempotent(self):
  first=self.create(BASE,'admin')['scopes'];second=self.create(BASE,'admin')['scopes']
  self.assertEqual([s['dars_turi'] for s in first],list(scope.LESSONS)*2)
  self.assertEqual([s['id'] for s in first],[s['id'] for s in second])
  self.assertEqual(len({s['scope_key'] for s in first}),8)
  self.assertEqual(self.db.sql.execute('SELECT COUNT(*) FROM curriculum_scopes').fetchone()[0],8)
 def test_non_institute_has_no_institute_lessons(self):
  for kind in ('maktab','bogcha','markaz'):
   rows=self.create({'institution_type':kind,'institution_id':11},'admin')['scopes']
   self.assertEqual(len(rows),1);self.assertEqual(rows[0]['dars_turi'],'')
 def test_invalid_official_form_language_pair_is_rejected(self):
  with self.assertRaises(HTTPException) as error:self.create({**BASE,'talim_shakli':'kunduzgi','talim_tili':'uz'},'admin')
  self.assertEqual(error.exception.status_code,400)
  self.assertEqual(self.db.sql.execute('SELECT COUNT(*) FROM curriculum_scopes').fetchone()[0],0)
 def test_failure_on_third_lesson_rolls_back_first_two(self):
  self.db.sql.execute("CREATE TRIGGER fail_lesson BEFORE INSERT ON curriculum_scopes WHEN NEW.dars_turi='seminar' BEGIN SELECT RAISE(ABORT,'test failure'); END")
  self.db.commit()
  with self.assertRaises(sqlite3.IntegrityError):self.create(BASE,'admin')
  self.assertEqual(self.db.sql.execute('SELECT COUNT(*) FROM curriculum_scopes').fetchone()[0],0)
  self.assertEqual(self.db.rollbacks,1)
 def test_student_and_teacher_cannot_create_admin_programs(self):
  for token in ('student','teacher'):
   with self.assertRaises(HTTPException) as error:self.create(BASE,token)
   self.assertEqual(error.exception.status_code,403)

if __name__=='__main__':unittest.main()
