"""REV177: maktab o'quvchisining kun rejasi — ota-ona sozlamasini tozalash."""
import unittest

from modules import maktab_ota as mo


class RejaTozaTest(unittest.TestCase):
    def test_standart(self):
        self.assertEqual(mo.reja_row_json(None), {"dars_soni": 0, "dam_kunlari": [], "yakshanba": "takror"})

    def test_chegaralar(self):
        self.assertEqual(mo.reja_toza(12, [6, 6, 0, -1, 7, "3", True], "dam"), {"dars_soni": 8, "dam_kunlari": [3, 6], "yakshanba": "dam"})
        self.assertEqual(mo.reja_toza(-3, "0", "?"), {"dars_soni": 0, "dam_kunlari": [], "yakshanba": "takror"})

    def test_yakshanba_dars_kuni(self):
        self.assertEqual(mo.reja_toza(4, [0, 6], "dars")["dam_kunlari"], [6])

    def test_bazadan(self):
        self.assertEqual(mo.reja_row_json({"dars_soni": 5, "dam_kunlari": "[6]", "yakshanba": "takror"}),
                         {"dars_soni": 5, "dam_kunlari": [6], "yakshanba": "takror", "ozgartirildi": True})


if __name__ == "__main__":
    unittest.main()


class KundalikTest(unittest.TestCase):
    """REV180: o'quvchi kundaligi — izoh tili farq qilmaydi."""

    def test_fan_kaliti(self):
        self.assertEqual(mo.fan_kaliti("Nemis tili (izoh: rus)"), "nemis tili")
        self.assertEqual(mo.fan_kaliti("Nemis tili"), "nemis tili")
        self.assertEqual(mo.fan_kaliti(None), "")
