import unittest
from modules.bola_kuzatuv import diqqat_text, FinishLesson, DIQQAT_CHEGARA


class DiqqatRev171(unittest.TestCase):
    def test_matn(self):
        self.assertEqual(diqqat_text(0, 0, 0, 1), "")
        t = diqqat_text(6, 3, 300, 2)
        self.assertIn("6 marta boshqa ilovaga", t)
        self.assertIn("5 daqiqa", t)
        self.assertIn("3 marta qaytib", t)
        self.assertIn("4 marta", diqqat_text(0, 0, 0, 4))   # server sanagani ham hisobga olinadi

    def test_model(self):
        b = FinishLesson(dars_kod="x", chiqish=3, qisqa=1, yoq_soniya=90)
        self.assertEqual((b.chiqish, b.qisqa, b.yoq_soniya), (3, 1, 90))
        self.assertEqual(FinishLesson(dars_kod="x").chiqish, 0)
        self.assertEqual(DIQQAT_CHEGARA, 5)


if __name__ == "__main__":
    unittest.main()
