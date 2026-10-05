"""REV102: ovoz rejasi — kamroq edge-tts so'rovi (uzilish kamayadi) va bolaga qaytarish uchun pauzalar."""
import unittest

from modules.ovoz_reja import jimlik, pause_for, reja
from modules.speech_audio import mp3_frames


def frames(n, padding=False):
    """MPEG-2 Layer III, 24 kHz, 48 kbit/s, mono (edge-tts formati) — n ta kadr."""
    head = bytes([0xFF, 0xF3, 0x64 | (0x02 if padding else 0), 0xC4])
    size = 144 + (1 if padding else 0)
    return (head + bytes(range(1, size - 3))[: size - 4]) * n


class RejaTests(unittest.TestCase):
    def test_summary_words_go_in_one_request(self):
        plan = reja("Barakalla! Bugun biz [en]Green[/en], [en]Clap[/en], [en]Ears[/en] ni o'rgandik. Ertaga yana uchrashamiz!")
        self.assertEqual([(p["til"], p["matn"]) for p in plan], [
            ("uz", "Barakalla! Bugun biz"), ("en", "Green, Clap, Ears"), ("uz", "ni o'rgandik. Ertaga yana uchrashamiz!")])
        self.assertTrue(all(p["pauza"] == 0 for p in plan))

    def test_child_gets_time_after_repeat_prompt(self):
        plan = reja("Qara, bu — [en]Green.[/en] O'zbekcha — yashil. Men bilan ayt: [en]Green.[/en] Yana bir marta: [en]Green.[/en] Barakalla!", takror=True)
        pauses = [(p["matn"], p["pauza"]) for p in plan if p["pauza"]]
        self.assertEqual(pauses, [("Green.", 1.5), ("Green.", 1.5)])
        # birinchi tanishtirish («Qara, bu — Green») pauzasiz
        self.assertEqual(plan[1], {"til": "en", "matn": "Green.", "pauza": 0.0})
        # takror=False (oddiy o'quvchi, test savoli) — pauza yo'q
        self.assertFalse(any(p["pauza"] for p in reja("Men bilan ayt: [en]Green.[/en]")))

    def test_english_prompts_inside_one_tag(self):
        plan = reja("[en]Look! Apple. An apple is red. Your turn! Say: Apple. One more time: Apple. Good job![/en]", takror=True)
        self.assertEqual([p["pauza"] > 0 for p in plan], [True, True, True, False])
        self.assertEqual(plan[-1]["matn"], "Good job!")
        level2 = reja("[en]Listen and repeat:[/en] [en]Apple.[/en] [en]Again![/en] [en]Apple.[/en] [en]Good job![/en]", takror=True)
        self.assertEqual([(p["matn"], bool(p["pauza"])) for p in level2],
                         [("Listen and repeat: Apple.", True), ("Again! Apple.", True), ("Good job!", False)])

    def test_explicit_pause_mark_and_length(self):
        plan = reja("Keling, birga aytamiz: [en]Thank you![/en] ⏸ [en]How are you?[/en] ⏸ Endi davom etamiz!")
        self.assertEqual([(p["matn"], p["pauza"]) for p in plan], [
            ("Keling, birga aytamiz:", 0.0), ("Thank you!", pause_for("Thank you")), ("How are you?", pause_for("How are you?")),
            ("Endi davom etamiz!", 0.0)])
        self.assertTrue(1.5 <= pause_for("Green") < pause_for("Thank you") < pause_for("How are you?") <= 3.0)
        self.assertEqual(pause_for("Nice to meet you, my dear friend"), 3.0)

    def test_punctuation_only_and_emoji_parts_are_dropped(self):
        plan = reja("🟢 [en]Green.[/en] — yashil. 👏 [en]Clap.[/en] — qarsak.")
        self.assertEqual([p["matn"] for p in plan], ["Green.", "— yashil.", "Clap.", "— qarsak."])


class JimlikTests(unittest.TestCase):
    def test_silence_matches_audio_format(self):
        sample = frames(10, padding=True)
        silent = jimlik(sample, 1.5)
        parsed = mp3_frames(silent)
        self.assertIsNotNone(parsed)
        self.assertEqual(len(parsed), round(1.5 / 0.024))
        self.assertTrue(all(length == 144 for _, length, _ in parsed))      # padding'siz
        self.assertEqual(silent[1] & 0x01, 1)                               # CRC yo'q
        self.assertEqual(set(silent[4:144]), {0})                           # yon ma'lumot va asosiy qism — nol
        self.assertIsNotNone(mp3_frames(sample + silent + sample))          # birga qo'shilsa ham to'g'ri MP3

    def test_unknown_audio_gives_no_silence(self):
        self.assertEqual(jimlik(b"not mp3", 2), b"")
        self.assertEqual(jimlik(frames(3), 0), b"")


if __name__ == "__main__":
    unittest.main()
