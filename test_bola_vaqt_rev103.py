"""REV103: bog'cha bolasining kunlik vaqti (dars / erkin o'yin) va ota-ona uchun o'rganish ko'rsatkichlari — sof mantiq."""
import unittest

from modules.bola_kuzatuv import insights, time_category, time_message, time_status


class VaqtTests(unittest.TestCase):
    def test_limits_by_age_group(self):
        small = time_status({}, "4-5 yosh")
        self.assertEqual((small["dars"]["limit"], small["oyin"]["limit"], small["jami"]["limit"]), (60, 60, 120))
        big = time_status({}, "6-7 yosh")
        self.assertEqual((big["dars"]["limit"], big["oyin"]["limit"], big["jami"]["limit"]), (120, 60, 180))
        self.assertEqual(time_status({}, "")["jami"]["limit"], 120)   # guruh noma'lum — kichiklar limiti

    def test_categories_and_what_is_closed(self):
        self.assertEqual((time_category("dars"), time_category("oyin"), time_category("profil")), ("dars", "oyin", "oyin"))
        st = time_status({"dars": 3600, "oyin": 600}, "4-5 yosh")
        self.assertEqual(st["tugadi"], {"dars": True, "oyin": False, "jami": False})
        self.assertEqual(time_message(st, "dars")["kod"], "dars")          # darsda — «endi o'ynasang bo'ladi»
        self.assertIsNone(time_message(st, "oyin"))                         # o'yinda hali 50 daqiqa bor
        st = time_status({"dars": 3600, "oyin": 3600}, "4-5 yosh")
        msg = time_message(st, "oyin")
        self.assertEqual(msg["kod"], "jami")
        self.assertIn("2 soat", msg["matn"])
        self.assertIn("Ertaga uchrashamiz", msg["matn"])
        self.assertIn("3 soat", time_message(time_status({"dars": 7200, "oyin": 3600}, "6-7 yosh"), "dars")["matn"])

    def test_five_minutes_left_warning(self):
        st = time_status({"oyin": 56 * 60}, "6-7 yosh")
        self.assertEqual(time_message(st, "oyin"), {"kod": "oz_qoldi", "matn": "O'yin vaqtidan 4 daqiqa qoldi."})
        self.assertIsNone(time_message(time_status({"oyin": 30 * 60}, "6-7 yosh"), "oyin"))


class TahlilTests(unittest.TestCase):
    def lessons(self):
        return [{"faol_soniya": 420, "chalgish_soni": 1, "togri": 4, "jami": 5, "yulduz": 3, "tugadi": True, "javob_ms": 2400},
                {"faol_soniya": 300, "chalgish_soni": 0, "togri": 5, "jami": 5, "yulduz": 3, "tugadi": True, "javob_ms": 2000},
                {"faol_soniya": 60, "chalgish_soni": 2, "togri": None, "jami": None, "yulduz": None, "tugadi": False, "javob_ms": None}]

    def test_indicators_and_ranking_among_same_age_children(self):
        peers = {1: {"yulduz": 6, "javob_ms": 2200, "aniqlik": 0.9}, 2: {"yulduz": 9, "javob_ms": 3000, "aniqlik": 0.7},
                 3: {"yulduz": 3, "javob_ms": 4000, "aniqlik": 0.5}, 4: {"yulduz": 1, "javob_ms": 5000, "aniqlik": 0.4}}
        out = insights(1, self.lessons(), [True, True, False], 640.0, 5, peers)
        keys = [i["kalit"] for i in out["korsatkichlar"]]
        self.assertEqual(keys, ["tezlik", "xotira", "diqqat", "muntazam", "natija"])
        tezlik = out["korsatkichlar"][0]
        self.assertIn("2.2 soniyada", tezlik["matn"])
        self.assertIn("tengdoshlarining hammasidan tezroq", tezlik["matn"])
        self.assertIn("640 ms", tezlik["matn"])
        self.assertIn("85 foiziga", out["korsatkichlar"][1]["matn"])      # 11 / 13 javob: darslardan 9/10 + testdan 2/3
        self.assertEqual(out["reyting"], {"orin": 2, "jami": 4, "yulduz": 6})
        self.assertIn("tashxis emas", out["izoh"])
        # o'rtadagi bola — foiz bilan; eng sekin — «hozircha sekinroq» (0 foiz deb yozilmaydi)
        mid = {**peers, 1: {"yulduz": 6, "javob_ms": 3500, "aniqlik": 0.9}}
        slow = [dict(l, javob_ms=6000) if l["javob_ms"] else l for l in self.lessons()]
        self.assertIn("tengdoshlarining 67 foizidan tezroq", insights(1, [dict(l, javob_ms=3500) if l["javob_ms"] else l
                                                                       for l in self.lessons()], [], None, 5, mid)["korsatkichlar"][0]["matn"])
        slow_peers = {**peers, 1: {"yulduz": 6, "javob_ms": 6000, "aniqlik": 0.9}}
        self.assertIn("hozircha tengdoshlaridan sekinroq", insights(1, slow, [], None, 5, slow_peers)["korsatkichlar"][0]["matn"])
        # eslab qolish tengdoshlar bilan bir xil o'lchovda (darslardagi javoblar, 7 kun) taqqoslanadi
        self.assertIn("tengdoshlarining hammasidan yaxshiroq", out["korsatkichlar"][1]["matn"])

    def test_new_child_without_data(self):
        out = insights(5, [], [], None, 0, {})
        self.assertEqual([i["kalit"] for i in out["korsatkichlar"]], ["muntazam"])
        self.assertIsNone(out["reyting"])
        self.assertIn("ma'lumot kam", out["xulosa"])


if __name__ == "__main__":
    unittest.main()
