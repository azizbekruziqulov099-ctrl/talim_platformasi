import asyncio
import unittest
from types import SimpleNamespace
import test_admin_speech as fixtures
from test_curriculum_scope import HTTPException

class TranscriptionTests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.SpeechTests();self.fixture.setUp();self.fixture.platform.GROQ_API_KALIT='test-key'
    def request(self,kind='audio/webm',body=b'audio'):
        async def stream():yield body
        return SimpleNamespace(headers={'content-type':kind},stream=stream)
    def run_request(self,kind='audio/webm'):
        return asyncio.run(self.fixture.routes['/dictate'](self.request(kind),'admin','uz'))
    def test_provider_errors_keep_distinct_actionable_codes_without_leaking_details(self):
        for status,expected in [(401,'STT_PROVIDER_KEY'),(403,'STT_PROVIDER_ACCESS'),(429,'STT_LIMIT'),(400,'STT_AUDIO_REJECTED'),(413,'STT_TOO_LARGE'),(500,'STT_CONNECTION')]:
            async def fail(*args):
                error=RuntimeError('secret-key-and-private-provider-body');error.response=SimpleNamespace(status_code=status);raise error
            self.fixture.ns['transcribe_audio']=fail
            with self.subTest(status=status),self.assertRaises(HTTPException) as error:self.run_request()
            self.assertIn(expected,error.exception.detail);self.assertNotIn('secret',error.exception.detail)
    def test_timeout_is_not_mistaken_for_an_empty_success(self):
        async def fail(*args):raise TimeoutError()
        self.fixture.ns['transcribe_audio']=fail
        with self.assertRaises(HTTPException) as error:self.run_request()
        self.assertEqual(error.exception.status_code,504);self.assertIn('STT_TIMEOUT',error.exception.detail)
    def test_empty_and_invalid_provider_responses_are_rejected(self):
        for result in ({},{'text':None},{'text':''},{'text':'   '}):
            async def transcribe(*args):return result
            self.fixture.ns['transcribe_audio']=transcribe
            with self.subTest(result=result),self.assertRaises(HTTPException) as error:self.run_request()
            self.assertIn(error.exception.status_code,(422,502))
    def test_uploaded_voice_mime_aliases_are_accepted(self):
        calls=[]
        async def transcribe(*args):calls.append(args);return {'text':'Salom.','language':'uzbek'}
        self.fixture.ns['transcribe_audio']=transcribe
        for kind in ('audio/mp3','audio/m4a','audio/x-m4a','audio/wav','audio/x-wav','video/mp4','video/webm','audio/flac'):
            with self.subTest(kind=kind):self.assertEqual(self.run_request(kind)['text'],'Salom.')
        self.assertEqual(len(calls),8)
    def test_missing_configuration_has_an_explicit_remedy(self):
        self.fixture.platform.GROQ_API_KALIT=''
        with self.assertRaises(HTTPException) as error:self.run_request()
        self.assertIn('STT_NOT_CONFIGURED',error.exception.detail);self.assertIn('GROQ_API_KEY',error.exception.detail)

if __name__=='__main__':unittest.main()
