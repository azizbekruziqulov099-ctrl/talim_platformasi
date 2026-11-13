"""REV538: tez bellashuv — har yosh va mavzuda yetarli, takrorsiz, 4 variantli savollar; to'g'ri javob variantlar ichida."""
import collections
import unittest

from modules import bellashuv_tez as T


class TezBellashuv(unittest.TestCase):
    def test_har_mavzu(self):
        orin = collections.Counter()
        for band, _ in T.BANDLAR:
            for mavzu, _nom in T.MAVZULAR[band]:
                for urug in range(15):
                    qs = T.savollar(band, mavzu, 10, urug)
                    self.assertEqual(len(qs), 10, f"{band}/{mavzu}")
                    self.assertEqual(len({(q["question"], q["option_" + q["correct_answer"].lower()]) for q in qs}), 10, "takror savol")
                    for q in qs:
                        vs = [q["option_a"], q["option_b"], q["option_c"], q["option_d"]]
                        self.assertEqual(len(set(vs)), 4); self.assertIn(q["correct_answer"], "ABCD"); orin[q["correct_answer"]] += 1
                        self.assertNotIn("$", q["question"])   # formulasiz — bellashuv ekranida oddiy matn
        self.assertGreater(min(orin.values()) / max(orin.values()), 0.8, "to'g'ri javob o'rni bir tekis taqsimlangan")

    def test_bogcha_yoshga_mos(self):
        for urug in range(30):
            for q in T.savollar("bogcha", "aralash", 10, urug):
                for v in (q["option_a"], q["option_b"], q["option_c"], q["option_d"]):
                    if v.lstrip("-").isdigit():
                        self.assertTrue(0 <= int(v) <= 22, f"bog'cha uchun katta yoki manfiy son: {v}")

    def test_hisob_togri(self):
        for urug in range(40):
            q = T.savollar("1-4", "jadval", 1, urug)[0]
            m = q["question"]; tog = int(q["option_" + q["correct_answer"].lower()])
            a, amal, b = m.replace(" = ?", "").split(" ")
            self.assertEqual(tog, int(a) * int(b) if amal == "·" else int(a) // int(b))

    def test_band(self):
        self.assertEqual(T.band_aniqla("3-A"), "1-4"); self.assertEqual(T.band_aniqla("yosh"), "bogcha")
        self.assertEqual(T.band_aniqla("10"), "9-11"); self.assertEqual(T.band_aniqla("", bola=True), "bogcha")


if __name__ == "__main__":
    unittest.main()
