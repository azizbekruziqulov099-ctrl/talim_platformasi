"""REV126: STT natijasi — o'zbekcha lotinda, Whisper halqalari olib tashlanadi, o'zbekcha uchun Gemini birinchi."""
import asyncio
import sys
import types
import unittest

if 'fastapi' not in sys.modules:
    try:
        import fastapi  # noqa: F401
    except ImportError:
        fa = types.ModuleType('fastapi')
        for n in ('APIRouter', 'HTTPException', 'Request'):
            setattr(fa, n, type(n, (), {'__init__': lambda s, *a, **k: None}))
        sys.modules['fastapi'] = fa
        r = types.ModuleType('fastapi.responses'); r.Response = object; sys.modules['fastapi.responses'] = r

from modules import admin_speech as sp


class SttCleanup(unittest.TestCase):
    def test_uzbek_cyrillic_becomes_latin(self):
        self.assertEqual(sp.tozala_stt('Ўзбекистон ёшлари ғалаба қилди', 'uz'), 'O‘zbekiston yoshlari g‘alaba qildi')
        self.assertEqual(sp.tozala_stt('Демек, бугун ҳаво яхши.', 'auto', 'uzbek'), 'Demek, bugun havo yaxshi.')

    def test_other_languages_untouched(self):
        self.assertEqual(sp.tozala_stt('Привет, как дела?', 'ru'), 'Привет, как дела?')

    def test_whisper_loops_removed(self):
        self.assertEqual(sp.tozala_stt('Bu ne? Bu ne? Bu ne? Bu ne? Bu ne?', 'auto'), 'Bu ne?')
        self.assertEqual(sp.tozala_stt('Men yaxshiman, rahmat. Rahmat!', 'uz'), 'Men yaxshiman, rahmat. Rahmat!')

    def test_gemini_first_for_uzbek(self):
        calls = []

        async def fake(audio, ct, ext, key, language, name, model=None):
            calls.append(name)
            return {'text': 'Салом', 'language': 'uz'}
        old = sp.transcribe_audio
        sp.transcribe_audio = fake
        try:
            res = asyncio.run(sp.transcribe_any(b'a', 'audio/webm', 'webm', [('groq', 'k'), ('gemini', 'g')], 'uz'))
        finally:
            sp.transcribe_audio = old
        self.assertEqual(calls, ['gemini'])
        self.assertEqual(res['text'], 'Salom')


if __name__ == '__main__':
    unittest.main()
