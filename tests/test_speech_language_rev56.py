"""Exercise language propagation, voice selection and protected speech handlers."""
import ast
import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from modules.speech_language import split_speech_text
import test_admin_speech as fixtures
from test_curriculum_scope import HTTPException

class SpeechLanguageTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.SpeechTests();self.fixture.setUp()

    def test_chosen_language_reaches_synthesizer_and_cache_is_language_specific(self):
        for language in ('uz','ru','en','ru'):
            self.fixture.read({'text':'123 + 45','voice':'ogil','language':language})
        self.assertEqual(self.fixture.calls,[('123 + 45','ogil','+0%',lang) for lang in ('uz','ru','en')])

    def test_selected_language_keeps_explicit_mixed_language_tags(self):
        self.assertEqual([(lang,text.strip()) for lang,text in split_speech_text('123. [en]Hello.[/en] 456.','ru')],
                         [('ru','123.'),('en','Hello.'),('ru','456.')])

    def test_one_selected_language_request_keeps_paragraphs_and_uses_one_voice_segment(self):
        text='123. 456.\n\n789.'
        self.assertEqual(split_speech_text(text,'ru'),[('ru',text)])

    def test_invalid_language_is_rejected_before_synthesis(self):
        for language in ('fr','',None,[],'../../key'):
            with self.subTest(language=language),self.assertRaises(HTTPException) as error:
                self.fixture.read({'text':'Text','language':language})
            self.assertEqual(error.exception.status_code,400)
        self.assertEqual(self.fixture.calls,[])

    def test_real_synthesizer_routes_to_the_selected_gender_and_language(self):
        calls=[]
        class Communicate:
            def __init__(self,text,voice,rate):calls.append((text,voice,rate))
            async def stream(self):yield {'type':'audio','data':b'mp3'}
        source=Path(__file__).resolve().parents[1]/'modules/admin_speech.py'
        node=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.AsyncFunctionDef) and n.name=='synthesize')
        ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
        with patch.dict(sys.modules,{'edge_tts':SimpleNamespace(Communicate=Communicate)}):
            audio=asyncio.run(ns['synthesize']('123. [en]Hello.[/en]','ogil','+0%','ru'))
        self.assertEqual(audio,b'mp3mp3')
        self.assertEqual([call[1] for call in calls],['ru-RU-DmitryNeural','en-US-GuyNeural'])

    def request(self):
        self.reads=0
        async def stream():self.reads+=1;yield b'audio'
        return SimpleNamespace(headers={'content-type':'audio/webm'},stream=stream)

    def test_selected_dictation_language_reaches_transcription(self):
        self.fixture.platform.GROQ_API_KALIT='test-key';calls=[]
        async def transcribe(*args):calls.append(args);return {'text':'Привет.','language':'russian'}
        self.fixture.ns['transcribe_audio']=transcribe
        result=asyncio.run(self.fixture.routes['/dictate'](self.request(),'admin','ru'))
        self.assertEqual(result['text'],'Привет.')
        self.assertEqual(calls,[(b'audio','audio/webm','webm','test-key','ru')])

    def test_invalid_or_unauthorized_dictation_does_not_consume_audio(self):
        self.fixture.platform.GROQ_API_KALIT='test-key'
        for token,language,status in [('student','ru',403),('admin','wrong',400)]:
            with self.assertRaises(HTTPException) as error:
                asyncio.run(self.fixture.routes['/dictate'](self.request(),token,language))
            self.assertEqual(error.exception.status_code,status);self.assertEqual(self.reads,0)

    def test_provider_receives_language_hint_on_transcription_endpoint(self):
        calls=[]
        class Client:
            def __init__(self,**kwargs):pass
            async def __aenter__(self):return self
            async def __aexit__(self,*args):pass
            async def post(self,url,**kwargs):
                calls.append((url,kwargs));return SimpleNamespace(raise_for_status=lambda:None,json=lambda:{'text':'Salom.','language':'uzbek'})
        with patch.dict(sys.modules,{'httpx':SimpleNamespace(AsyncClient=Client)}):
            asyncio.run(self.fixture.ns['transcribe_audio'](b'audio','audio/webm','webm','key','uz'))
        self.assertTrue(calls[0][0].endswith('/audio/transcriptions'))
        self.assertEqual(calls[0][1]['data']['language'],'uz')

    def test_status_reports_missing_transcription_and_supported_languages(self):
        self.fixture.platform.GROQ_API_KALIT='  '
        result=self.fixture.routes['/status']('admin')
        self.assertFalse(result['dictation_available']);self.assertEqual(result['languages'],['uz','ru','en'])

if __name__=='__main__':unittest.main()
