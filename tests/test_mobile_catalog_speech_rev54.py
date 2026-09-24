"""Regression cases for school selection, schedule times and multilingual speech."""
import asyncio
import re
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import test_admin_speech as speech_fixtures
import test_curriculum_catalog as catalog_fixtures
from test_curriculum_scope import HTTPException, scope
from modules.speech_language import detect_language, split_speech_text

class SchoolCatalogTests(unittest.TestCase):
    topic=catalog_fixtures.CatalogTests.topic
    codes=catalog_fixtures.CatalogTests.codes
    def setUp(self):
        catalog_fixtures.CatalogTests.setUp(self)
        self.db.profile=None
        self.db.user={'role':'oquvchi','class':'7-sinf'}
    def test_selecting_school_retains_common_and_adds_own_tests_with_empty_topics(self):
        common=self.topic(1,institution_type='maktab',institution_id=0,grade='7')
        own=self.topic(2,institution_type='maktab',institution_id=11,grade='7')
        foreign=self.topic(3,institution_type='maktab',institution_id=12,grade='7')
        empty='school-untested'
        self.db.sql.execute("INSERT INTO dts_tree(topic_code,curriculum_scope_id,grade,subject_code,subject_name,mavzu_name) VALUES(?,2,'7','04','FIZIKA','Nur')",(empty,))
        self.assertEqual(self.codes(self.catalog(token='pupil',institution_type='maktab')),{common})
        self.db.user['maktab_id']=11
        self.assertEqual(self.codes(self.catalog(token='pupil',institution_type='maktab')),{common,own})
        self.assertEqual(scope.authorized_codes(self.db.cursor(),5,[common,own]),[common,own])
        with self.assertRaises(PermissionError):scope.authorized_codes(self.db.cursor(),5,[foreign])
        self.assertEqual(self.codes(self.catalog(token='pupil',faqat_testli=False)),{common,own,empty})
    def test_admin_school_catalog_with_only_untested_topics_is_empty_without_error(self):
        self.db.admin=True
        self.topic(1,institution_type='maktab',institution_id=0,grade='7')
        self.db.sql.execute('DELETE FROM generated_tests')
        self.assertEqual(self.catalog(token='admin',institution_type='maktab')['fanlar'],[])
    def test_null_arrays_and_null_codes_are_ignored(self):
        self.assertEqual(scope.group_catalog_rows([{'testli_kodlar':None}]),[])
        self.assertEqual(scope.group_catalog_rows([{'testli_kodlar':[None]}]),[])

class ScheduleTests(unittest.TestCase):
    def setUp(self):
        path=catalog_fixtures.ROOT/'samtm_platform.py'
        self.settings=catalog_fixtures.load_function(path,'_talaba_jadval_sozlamalarini_tekshir',{'re':re})
        self.days=catalog_fixtures.load_function(path,'_talaba_jadval_kunlarini_tekshir',{
            're':re,'HTTPException':HTTPException,'TALABA_KUN_TURLARI':{'dars','amaliyot','dam'},'TALABA_PARA_TURLARI':{'maruza','amaliyot'}})
    def test_hidden_legacy_lesson_times_cannot_override_weekly_settings(self):
        result=self.days([{'kun':1,'paralar':[{'raqam':2,'fan':'Matematika','boshlanish':'14:00','tugash':'15:00'}]}])
        lesson=result[0]['paralar'][0]
        self.assertEqual((lesson['boshlanish'],lesson['tugash']),('',''))
        self.assertEqual((lesson['fan'],lesson['raqam']),('Matematika',2))
    def test_zero_break_and_valid_start_survive_normalization(self):
        result=self.settings({'boshlanish':'17:30','tanaffus_daqiqa':0})
        self.assertEqual(result['boshlanish'],'17:30');self.assertEqual(result['tanaffus_daqiqa'],0)
        self.assertEqual(self.settings({'boshlanish':'99:99'})['boshlanish'],'08:30')

class LanguageTests(unittest.TestCase):
    def test_untagged_text_uses_its_language(self):
        cases=[('Salom, bugun matematika darsi.','uz'),('Which answer is correct?','en'),
               ('Hello world!','en'),('Найдите правильный ответ.','ru'),('Ўқувчилар учун китоб.','uz'),
               ('Quyidagi sonlarning yig‘indisini hisoblang.','uz')]
        for text,language in cases:
            with self.subTest(text=text):self.assertEqual(detect_language(text),language)
    def test_mixed_sentences_tags_and_formulas(self):
        parts=split_speech_text('Salom. Hello world! Привет, мир. [uz]apple[/uz]')
        self.assertEqual([language for language,text in parts],['uz','uz','uz','uz'])
        self.assertEqual(split_speech_text('[en]2 + 3 = 5[/en]'),[('en','2 + 3 = 5')])
        self.assertEqual(detect_language('[lat]x + y[/lat]'),'uz')

class DictationTests(unittest.TestCase):
    def setUp(self):
        self.fixture=speech_fixtures.SpeechTests();self.fixture.setUp()
        self.fixture.platform.GROQ_API_KALIT='test-key'
        self.calls=[]
        async def transcribe(*args):self.calls.append(args);return {'text':'Hello world.','language':'english'}
        self.fixture.ns['transcribe_audio']=transcribe
    def request(self,body=b'audio',kind='audio/webm;codecs=opus'):
        self.reads=0
        async def stream():self.reads+=1;yield body
        return SimpleNamespace(headers={'content-type':kind},stream=stream)
    def run_request(self,request,token='admin'):
        return asyncio.run(self.fixture.routes['/dictate'](request,token))
    def test_audio_is_transcribed_with_detected_language(self):
        self.assertEqual(self.run_request(self.request()),{'text':'Hello world.','language':'english'})
        self.assertEqual(self.calls,[(b'audio','audio/webm','webm','test-key')])
    def test_admin_authorization_precedes_reading_audio(self):
        with self.assertRaises(HTTPException) as exc:self.run_request(self.request(),token='student')
        self.assertEqual(exc.exception.status_code,403);self.assertEqual(self.reads,0);self.assertEqual(self.calls,[])
    def test_missing_service_and_invalid_audio_are_explicit(self):
        for body,kind,status in [(b'', 'audio/webm',400),(b'x','text/plain',415),(b'x'*(8*1024*1024+1),'audio/webm',413)]:
            with self.subTest(status=status),self.assertRaises(HTTPException) as exc:self.run_request(self.request(body,kind))
            self.assertEqual(exc.exception.status_code,status)
        self.fixture.platform.GROQ_API_KALIT=''
        with self.assertRaises(HTTPException) as exc:self.run_request(self.request())
        self.assertEqual(exc.exception.status_code,503);self.assertEqual(self.calls,[])
    def test_provider_call_omits_language_and_uses_transcription_not_translation(self):
        sent=[]
        class Client:
            def __init__(self,**kwargs):pass
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            async def post(self,url,**kwargs):
                sent.append((url,kwargs))
                return SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'text':'Salom.','language':'uzbek'})
        path=catalog_fixtures.ROOT/'modules/admin_speech.py'
        import ast
        node=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.AsyncFunctionDef) and n.name=='transcribe_audio')
        ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),ns)
        with patch.dict(sys.modules,{'httpx':SimpleNamespace(AsyncClient=Client)}):
            result=asyncio.run(ns['transcribe_audio'](b'blob','audio/mp4','mp4','key'))
        self.assertEqual(result['text'],'Salom.')
        self.assertTrue(sent[0][0].endswith('/audio/transcriptions'))
        self.assertNotIn('language',sent[0][1]['data'])
        self.assertEqual(sent[0][1]['files']['file'],('dictation.mp4',b'blob','audio/mp4'))

if __name__=='__main__':unittest.main()
