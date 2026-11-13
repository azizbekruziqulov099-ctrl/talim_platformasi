"""REV543: Kabu loyiha portfeli — loyiha kalitlari va chegaralar (frontend bilan bir xil ro'yxat)."""
import unittest

from modules import loyiha_portfel as L


class LoyihaPortfel(unittest.TestCase):
    def test_loyiha_kalitlari(self):
        # frontend (src/games/loyiha): 5 + 10 loyiha
        kutilgan = {"osimlik", "koprik", "kod", "naqsh", "byudjet", "filtr", "richag", "parashyut", "qayiq", "soya", "qiya", "masshtab", "sorov", "rang", "kod2"}
        self.assertEqual(L.LOYIHALAR, kutilgan)

    def test_rasm_chegarasi(self):
        self.assertLessEqual(L.RASM_MAX, 1_000_000)

    def test_modellar(self):
        self.assertEqual(L.Natija(loyiha="koprik", yulduz=3).yulduz, 3)
        with self.assertRaises(Exception):
            L.Natija(loyiha="koprik", yulduz=4)
        with self.assertRaises(Exception):
            L.Qolda(loyiha="koprik", rasm="x", izoh="a" * 401)


if __name__ == "__main__":
    unittest.main()
