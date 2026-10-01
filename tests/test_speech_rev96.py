"""REV96: ovozni matnga — bir nechta kalit, limitda dam olish, Groq turbo zaxirasi."""
import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from modules import admin_speech as sp


def limited(status=429):
    err = RuntimeError("limit")
    err.response = SimpleNamespace(status_code=status, headers={"retry-after": "60"})
    return err


class Rev96Tests(unittest.TestCase):
    def setUp(self):
        sp.stt_cooldowns().clear()

    def test_several_groq_keys_and_rested_key_goes_last(self):
        platform = SimpleNamespace(GROQ_API_KALIT="k1,k2")
        with patch.dict(os.environ, {"GROQ_API_KEYS": "k3", "OPENAI_API_KEY": "", "GEMINI_API_KEY": "", "STT_PROVIDERS": ""}):
            self.assertEqual([k for _, k in sp.stt_providers(platform)], ["k1", "k2", "k3"])
            sp.stt_rest("groq", "k1", limited())
            self.assertEqual([k for _, k in sp.stt_providers(platform)], ["k2", "k3", "k1"])
            health = sp.stt_health(platform)
            self.assertEqual(health[-1]["holat"], "dam")
            self.assertEqual(health[-1]["sabab"], "limit")

    def test_limit_uses_turbo_then_next_key(self):
        calls = []

        async def fake(audio, ct, ext, key, language, provider, model=None):
            calls.append((key, model))
            if key == "k1":
                raise limited()
            return {"text": "salom", "language": "uz"}

        with patch.object(sp, "transcribe_audio", fake):
            res = asyncio.run(sp.transcribe_any(b"a", "audio/webm", "webm", [("groq", "k1"), ("groq", "k2")], "uz"))
        self.assertEqual(calls, [("k1", None), ("k1", "whisper-large-v3-turbo"), ("k2", None)])
        self.assertEqual(res["text"], "salom")
        self.assertIn(sp.stt_slot("groq", "k1"), sp.stt_cooldowns())


if __name__ == "__main__":
    unittest.main()
