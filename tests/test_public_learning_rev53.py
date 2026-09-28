"""Exercise public practice predicates and real catalog handlers against SQL rows."""
import unittest
import test_curriculum_catalog as catalog_fixtures
from test_curriculum_scope import scope

class PublicLearningTests(unittest.TestCase):
 topic=catalog_fixtures.CatalogTests.topic
 codes=catalog_fixtures.CatalogTests.codes
 def setUp(self):
  catalog_fixtures.CatalogTests.setUp(self)
  self.db.profile=None
  self.learning=dict(role='talaba',standalone=True,kurs=2,semestr=3,talim_bosqichi='bakalavr',talim_shakli='kechki',talim_tili='uz')
  self.db.user={'class':'2 kurs','role':'oquvchi','kabutar_learning_profile':self.learning}
 def public_topic(self,id,**values):
  return self.topic(id,institution_id=0,yonalish_id=0,yonalish_nomi='Umumiy fanlar',kurs=2,semestr=3,grade='2 kurs',**values)
 def test_independent_student_sees_all_and_own_program_is_first(self):
  own=self.public_topic(1)
  a=self.public_topic(2,talim_shakli='kunduzgi');b=self.public_topic(3,talim_tili='ru')
  private=self.topic(4,kurs=2,semestr=3,grade='2 kurs')
  result=self.catalog(token='learner')
  self.assertEqual(self.codes(result),{own,a,b,private})
  mine={code for subject in result['fanlar'] if subject['mine'] for g in subject['sinflar'] for t in g['mavzular'] for code in t['topic_codes']}
  self.assertEqual(mine,{own});self.assertTrue(result['fanlar'][0]['mine'])
  self.assertEqual(scope.authorized_codes(self.db.cursor(),5,[private,own]),[private,own])
 def test_profile_preselects_institute_without_enrollment(self):
  result=self.catalog(token='learner')
  self.assertEqual(result['viewer']['types'],['universitet'])
  self.assertEqual(result['viewer']['grade'],'2 kurs')
  self.assertFalse(result['profil_sozlanmagan'])
 def test_query_cannot_switch_independent_student_to_school(self):
  self.public_topic(1)
  school=self.topic(2,institution_type='maktab',institution_id=0,grade='2')
  self.assertEqual(self.codes(self.catalog(token='learner',institution_type='maktab')),set())
  with self.assertRaises(PermissionError):scope.authorized_codes(self.db.cursor(),5,[school])
 def test_incomplete_standalone_profile_browses_everything(self):
  self.public_topic(1)
  for field in ('kurs','talim_shakli','talim_tili','talim_bosqichi'):
   with self.subTest(field=field):
    saved=self.learning.pop(field)
    # REV77: to'liq sozlanmagan talaba bloklanmaydi — hammasini ko'radi, «o'ziniki» belgisi yo'q.
    result=self.catalog(token='learner')
    self.assertEqual(len(self.codes(result)),1);self.assertFalse(result['fanlar'][0]['mine'])
    self.assertFalse(result['viewer']['profil_toliq'])
    self.learning[field]=saved
 def test_common_program_has_no_membership_or_group(self):
  for data in ({'guruh':'201'},{'yonalish_id':7}):
   with self.assertRaises(ValueError):scope.normalize_scope(dict(institution_type='universitet',institution_id=0,
    talim_bosqichi='bakalavr',yonalish_id=0,kurs=2,semestr=3,talim_shakli='kechki',talim_tili='uz',dars_turi='amaliy',**{k:v for k,v in data.items() if k!='yonalish_id'} ) | ({'yonalish_id':7} if 'yonalish_id' in data else {}))
 def test_two_public_semesters_group_into_one_subject(self):
  first=self.public_topic(1)
  second=self.topic(2,institution_id=0,yonalish_id=0,yonalish_nomi='Umumiy fanlar',kurs=2,semestr=4,grade='2 kurs')
  result=self.catalog(token='learner')
  self.assertEqual(self.codes(result),{first,second})
  self.assertEqual(len(result['fanlar']),1)
  self.assertEqual(result['fanlar'][0]['semestrlar'],[3,4])

if __name__=='__main__':unittest.main()
