"""REV174: maktab ota-ona — sof qoidalar."""
import unittest
from datetime import date

from modules.maktab_ota import Topshiriq, bajarildi_matni, hafta_jadvali, maktab_oquvchimi, soz_idlari, yozish_soni


class MaktabOtaTest(unittest.TestCase):
    def test_soz_idlari(self):
        self.assertEqual(soz_idlari(["s7_food", "S7_FOOD", "hello", "bad id", "<x>", None, "a" * 60]), ["s7_food", "hello"])
        self.assertEqual(len(soz_idlari([f"w{i}" for i in range(100)], 30)), 30)

    def test_yozish_soni(self):
        self.assertEqual(yozish_soni(22), 20)
        self.assertEqual(yozish_soni(45), 40)
        self.assertEqual(yozish_soni(999), 100)
        self.assertEqual(yozish_soni(-3), 0)

    def test_maktab_oquvchimi(self):
        self.assertEqual(maktab_oquvchimi({"role": "oquvchi", "class": "7-A"}), 7)
        self.assertIsNone(maktab_oquvchimi({"role": "oquvchi", "class": "4-5 yosh", "lp": {"role": "bogcha"}}))
        self.assertIsNone(maktab_oquvchimi({"role": "ota-ona", "class": "7"}))
        self.assertEqual(maktab_oquvchimi({"role": "oquvchi", "class": "11", "lp": '{"role": "oquvchi"}'}), 11)

    def test_hafta_jadvali_bosh_kunlar_bilan(self):
        today = date(2026, 10, 25)
        rows = [{"sana": today, "togri": 8, "jami": 10, "yozdi": 40, "soniya": 600, "fan": "Ingliz tili"},
                {"sana": today, "togri": 0, "jami": 0, "yozdi": 0, "soniya": 300, "fan": "Matematika"},
                {"sana": date(2026, 10, 22), "togri": 3, "jami": 5, "yozdi": 0, "soniya": 0, "fan": ""}]
        h = hafta_jadvali(rows, today)
        self.assertEqual(len(h), 7)
        self.assertEqual(h[-1]["sana"], "2026-10-25")
        self.assertEqual((h[-1]["faoliyat"], h[-1]["togri"], h[-1]["jami"], h[-1]["yozdi"], h[-1]["daqiqa"]), (2, 8, 10, 40, 15))
        self.assertEqual(h[-1]["fanlar"], ["Ingliz tili", "Matematika"])
        self.assertEqual(h[3]["faoliyat"], 1)
        self.assertEqual(h[0]["faoliyat"], 0)

    def test_bajarildi_matni(self):
        m = bajarildi_matni("Ali", {"til": "en", "sozlar": ["a", "b"]}, {"togri": 7, "jami": 8, "yozdi": 40})
        self.assertIn("Ali", m)
        self.assertIn("Ingliz tili", m)
        self.assertIn("7/8", m)
        self.assertIn("40 marta", m)

    def test_topshiriq_chegaralari(self):
        with self.assertRaises(Exception):
            Topshiriq(bola_id=1, til="en", sozlar=[])
        with self.assertRaises(Exception):
            Topshiriq(bola_id=1, til="en", sozlar=["a"] * 31)


if __name__ == "__main__":
    unittest.main()
