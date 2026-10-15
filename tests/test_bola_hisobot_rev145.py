"""REV145: ota-ona hisoboti — o'rgangan so'zlar va tushunarli baho (sof mantiq)."""
import unittest

from modules.bola_kuzatuv import FinishLesson, clean_words, result_level, words_text


class WordsTests(unittest.TestCase):
    def test_clean_words_safe_unique_and_capped(self):
        raw = [{"soz": " apple ", "emoji": "🍎", "aytdi": True}, {"soz": "Apple"}, "bad", {"soz": ""},
               {"soz": "banana", "aytdi": "ha"}, *({"soz": f"w{i}"} for i in range(20))]
        out = clean_words(raw)
        self.assertEqual(out[0], {"soz": "apple", "emoji": "🍎", "aytdi": True})
        self.assertEqual(out[1], {"soz": "banana", "emoji": "", "aytdi": None})
        self.assertEqual(len(out), 12)
        self.assertEqual(clean_words(None), [])

    def test_bad_item_does_not_reject_lesson_result(self):
        body = FinishLesson(dars_kod="EN1", togri=1, jami=2, sozlar=["x", {"soz": "cat", "aytdi": True}])
        self.assertEqual(clean_words(body.sozlar), [{"soz": "cat", "emoji": "", "aytdi": True}])

    def test_level_and_text(self):
        self.assertEqual([result_level(4, 5), result_level(1, 2), result_level(1, 4), result_level(0, 0)], ["alo", "yaxshi", "mashq", None])
        self.assertEqual(words_text([{"soz": "apple", "aytdi": True}, {"soz": "juice", "aytdi": None}]), "apple ✓, juice")


if __name__ == "__main__":
    unittest.main()
