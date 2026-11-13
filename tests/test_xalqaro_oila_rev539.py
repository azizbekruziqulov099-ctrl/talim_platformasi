"""REV539: xalqaro imtihonlar — TIMSS va PISA natijalari aralashmaydi."""
import unittest
from modules import xalqaro_baholash as X


class ImtihonOilasi(unittest.TestCase):
    def test_haftalik_oylik_faqat_ozi(self):
        for tur in ("haftalik", "oylik", "choraklik"):
            for tk in ("T11_G4_M", "T11_G8_S", "P_M", "P_R"):
                self.assertEqual(X.imtihon_oilasi(tk, tur), [tk])

    def test_yillik_juftlik(self):
        self.assertEqual(X.imtihon_oilasi("T11_G4_M", "yillik"), ["T11_G4_M", "T11_G4_S"])
        self.assertEqual(X.imtihon_oilasi("T11_G4_S", "yillik"), ["T11_G4_M", "T11_G4_S"])
        self.assertEqual(X.imtihon_oilasi("T11_G8_M", "yillik"), ["T11_G8_M", "T11_G8_S"])
        self.assertEqual(X.imtihon_oilasi("P_M", "yillik"), ["P_M", "P_S"])
        self.assertEqual(X.imtihon_oilasi("P_R", "yillik"), ["P_R"])   # jufti P_M, lekin o'zaro emas — alohida

    def test_timss_pisa_aralashmaydi(self):
        for tur in X.IMTIHON_TURLARI:
            timss = set(X.imtihon_oilasi("T11_G8_M", tur)); pisa = set(X.imtihon_oilasi("P_M", tur))
            self.assertFalse(timss & pisa, tur)
            self.assertFalse(set(X.imtihon_oilasi("T11_G4_M", tur)) & timss, tur)   # 4- va 8-sinf ham alohida


if __name__ == "__main__":
    unittest.main()
