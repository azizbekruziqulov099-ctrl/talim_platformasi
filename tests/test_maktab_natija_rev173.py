"""REV173: maktab til natijasi — birlashtirish (kamaymaydi), sinf, o'rin."""
import unittest

from datetime import date

from modules.maktab_natija import KUNLIK_BAL, Natija, birlashtir, daraja_raqami, kunlik_chegara, orin, sinf_of


class MaktabNatijaTest(unittest.TestCase):
    def test_birlashtir_kamaymaydi_va_daraja_pasaymaydi(self):
        eski = {"bal": 500, "togri": 40, "jami": 50, "otildi": 3, "daraja": "A1", "keyingi": "A2", "foiz": 40}
        yangi = {"bal": 120, "togri": 10, "jami": 12, "otildi": 1, "daraja": "Pre-A1", "keyingi": "A1", "foiz": 90}
        r = birlashtir(eski, yangi)
        self.assertEqual((r["bal"], r["togri"], r["jami"], r["otildi"]), (500, 40, 50, 3))
        self.assertEqual((r["daraja"], r["keyingi"], r["foiz"]), ("A1", "A2", 40))
        r2 = birlashtir(eski, {**yangi, "daraja": "A2", "keyingi": "B1", "foiz": 5, "bal": 900})
        self.assertEqual((r2["daraja"], r2["foiz"], r2["bal"]), ("A2", 5, 900))

    def test_yangi_foydalanuvchi_va_notogri_daraja(self):
        r = birlashtir(None, {"bal": 10, "togri": 9, "jami": 3, "daraja": "Z9", "foiz": 50})
        self.assertEqual(r["togri"], 3)          # to'g'ri javoblar jamidan oshmaydi
        self.assertEqual(r["daraja"], "")
        self.assertEqual(daraja_raqami("B1"), 4)

    def test_sinf_va_orin(self):
        self.assertEqual(sinf_of("7-A", 3), 7)
        self.assertEqual(sinf_of("10 sinf", 3), 10)
        self.assertEqual(sinf_of(None, 5), 5)
        self.assertEqual(sinf_of("bogcha", 0), 1)
        self.assertEqual(orin([100, 50, 300, 50], 50), 3)
        self.assertEqual(orin([], 0), 1)

    def test_kunlik_osish_chegarasi(self):
        bugun = date(2026, 10, 25)
        eski = {"bal": 1000, "togri": 10, "jami": 20, "otildi": 1, "kun": date(2026, 10, 24), "kun_bal": 0}
        r, bosh = kunlik_chegara(eski, {"bal": 50_000_000, "togri": 10**6, "jami": 10**6, "otildi": 200, "daraja": "", "keyingi": "", "foiz": 0}, bugun)
        self.assertEqual(r["bal"], 1000 + KUNLIK_BAL)          # kun boshidagi qiymatdan
        self.assertEqual(bosh["bal"], 1000)
        self.assertLessEqual(r["togri"], r["jami"])
        # o'sha kuni ikkinchi so'rov — chegara kun boshidan hisoblanadi (bo'lib-bo'lib yuborib aylanib o'tib bo'lmaydi)
        eski2 = {**eski, **r, "kun": bugun, "kun_bal": bosh["bal"], "kun_jami": bosh["jami"], "kun_otildi": bosh["otildi"]}
        r2, _ = kunlik_chegara(eski2, {**r, "bal": 10**7}, bugun)
        self.assertEqual(r2["bal"], 1000 + KUNLIK_BAL)

    def test_model_chegaralari(self):
        n = Natija(til="en", sinf=7, bal=10)
        self.assertEqual(n.sinf, 7)
        with self.assertRaises(Exception):
            Natija(til="en", sinf=12)


if __name__ == "__main__":
    unittest.main()
