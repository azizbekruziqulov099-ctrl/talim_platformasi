import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import test_admin_speech as speech_fixtures


class SttFallbackTests(unittest.TestCase):
    def setUp(self):
        self.fixture = speech_fixtures.SpeechTests(); self.fixture.setUp()
        self.fixture.platform.GROQ_API_KALIT = 'groq-key'
        self.calls = []

    def request(self):
        async def stream():
            yield b'audio'
        return SimpleNamespace(headers={'content-type': 'audio/mp4'}, stream=stream)

    def test_next_provider_is_used_when_first_fails(self):
        async def transcribe(audio, ctype, ext, key, language, provider):
            self.calls.append(provider)
            if provider == 'groq':
                raise RuntimeError('bad key')
            return {'text': 'Salom dunyo', 'language': 'uz'}
        self.fixture.ns['transcribe_audio'] = transcribe
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-x', 'GEMINI_API_KEY': ''}):
            result = asyncio.run(self.fixture.routes['/dictate'](self.request(), 'admin', 'uz'))
        self.assertEqual(self.calls, ['groq', 'openai'])
        self.assertEqual((result['text'], result['provider']), ('Salom dunyo', 'openai'))

    def test_only_openai_or_gemini_key_makes_dictation_available(self):
        self.fixture.platform.GROQ_API_KALIT = ''
        with patch.dict(os.environ, {'OPENAI_API_KEY': '', 'GEMINI_API_KEY': 'g-key', 'STT_PROVIDERS': ''}):
            status = self.fixture.routes['/status']('admin')
        self.assertTrue(status['dictation_available'])
        self.assertEqual(status['providers'], ['gemini'])

    def test_gemini_request_shape(self):
        sent = []

        class Client:
            def __init__(self, **kwargs): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def post(self, url, **kwargs):
                sent.append((url, kwargs))
                return SimpleNamespace(raise_for_status=lambda: None,
                                       json=lambda: {'candidates': [{'content': {'parts': [{'text': ' Salom. '}]}}]})
        import sys
        with patch.dict(sys.modules, {'httpx': SimpleNamespace(AsyncClient=Client)}):
            result = asyncio.run(self.fixture.ns['transcribe_audio'](b'a', 'video/webm', 'webm', 'g', 'uz', 'gemini'))
        self.assertEqual(result['text'], 'Salom.')
        self.assertIn(':generateContent', sent[0][0])
        part = sent[0][1]['json']['contents'][0]['parts'][1]['inline_data']
        self.assertEqual(part['mime_type'], 'audio/webm')
        self.assertEqual(sent[0][1]['headers']['x-goog-api-key'], 'g')


if __name__ == '__main__':
    unittest.main()
