"""Repetitor kursi banki: 150 mavzu, har birida >=20 test, javob harfi to'g'ri, takror savol yo'q; eski bankka aralashmaydi."""
import json, random, unittest
import modules.mat_bank as mb


class Repetitor150(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = mb.rep_bank_ol()

    def test_150_mavzu(self):
        self.assertEqual(sorted(self.b.mavzular), [1000 + i for i in range(1, 151)])

    def test_har_mavzuda_20_test(self):
        for r, m in self.b.mavzular.items():
            self.assertGreaterEqual(self.b.soni(r), 20, r)

    def test_testlar_tugal(self):
        ids = set()
        for t in self.b.savol.values():
            self.assertNotIn(t["id"], ids); ids.add(t["id"])
            self.assertTrue(t["savol"].strip(), t["id"])
            self.assertGreaterEqual(len(t["variantlar"]), 4, t["id"])
            self.assertEqual(len(set(t["variantlar"])), len(t["variantlar"]), t["id"])   # takroriy variant yo'q
            self.assertIn(t["javob"], "ABCDE"[:len(t["variantlar"])], t["id"])

    def test_tanlash_va_baholash(self):
        sav = mb.tanla(self.b, [1001, 1002], 15, {}, random.Random(1))
        self.assertEqual(len(sav), 15)
        r = mb.baholash(self.b, {t["id"]: t["javob"] for t in sav})
        self.assertEqual(r["togri"], 15)

    def test_eski_bank_aralashmaydi(self):
        eski = mb.bank_ol()
        self.assertFalse(any(r >= 1000 for r in eski.mavzular))
        self.assertFalse(any(k.startswith("R") for k in eski.savol))
