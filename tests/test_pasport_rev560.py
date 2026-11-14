"""REV560: o'quvchi pasporti — esdan chiqarish modeli, daraja, nozik joylar, xulosa."""
import unittest
from datetime import datetime, timedelta, timezone

from modules import pasport as P
from modules.mat_bank import bank_ol

HOZIR = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)


def Q(savol, mavzu, urinish=1, togri=1, ox=True, kun=0):
    return {"savol_id": savol, "mavzu": mavzu, "urinish": urinish, "togri": togri, "oxirgi_togri": ox, "yangilangan": HOZIR - timedelta(days=kun)}


class Esdan(unittest.TestCase):
    def test_saqlanish_monoton(self):
        self.assertAlmostEqual(P.saqlanish(1, 0), 1.0)
        for t in (1, 3, 6):
            self.assertGreater(P.saqlanish(t, 1), P.saqlanish(t, 5)); self.assertGreater(P.saqlanish(t, 5), P.saqlanish(t, 30))
        for kun in (1, 7, 30):
            self.assertLess(P.saqlanish(1, kun), P.saqlanish(2, kun)); self.assertLess(P.saqlanish(2, kun), P.saqlanish(6, kun))   # ko'p marta to'g'ri — sekin unutiladi
        self.assertEqual(P.saqlanish(99, 10), P.saqlanish(6, 10))    # chegara
        self.assertEqual(P.saqlanish(0, 1), P.saqlanish(1, 1))       # xato kiritilsa ham buzilmaydi

    def test_holat(self):
        self.assertEqual(P.savol_holati(False, 5, 0), "xato")
        self.assertEqual(P.savol_holati(True, 1, 0.5), "mustahkam")
        self.assertEqual(P.savol_holati(True, 1, 2), "takror")          # 1 marta to'g'ri, 2 kun o'tdi
        self.assertEqual(P.savol_holati(True, 1, 6), "unutilgan")
        self.assertEqual(P.savol_holati(True, 6, 20), "mustahkam")      # 6 marta to'g'ri — 20 kundan keyin ham mustahkam
        self.assertEqual(P.savol_holati(True, 3, 9999), "unutilgan")    # vaqti noma'lum


class Daraja(unittest.TestCase):
    def test_kam_malumotda_daraja_yoq(self):
        for foiz in (0, 50, 100):
            self.assertIsNone(P.daraja_nomi(foiz, 14))                  # 14 ta savol — daraja aytilmaydi
        self.assertEqual([P.daraja_nomi(f, 15) for f in (90, 70, 50, 20)], ["yuqori", "yaxshi", "o‘rta", "past"])
        self.assertEqual([P.daraja_nomi(f, 40) for f in (85, 84, 65, 64, 45, 44)], ["yuqori", "yaxshi", "yaxshi", "o‘rta", "o‘rta", "past"])


class Mavzular(unittest.TestCase):
    MAV = {1: {"nom": "Boshlang‘ich", "kitob": "1.1.1", "jami": 30}, 7: {"nom": "Oddiy kasrlar", "kitob": "1.2.1", "jami": 19}, 31: {"nom": "Oraliqlar usuli", "kitob": "1.7.3", "jami": 121}}

    def test_statistika_va_nozik(self):
        q = [Q(f"a{i}", 7, urinish=2, togri=1, ox=i < 2) for i in range(8)]       # 7-mavzu: 8 savol, 2 tasi to'g'ri → 25% — nozik
        q += [Q(f"b{i}", 31, ox=True, kun=0.1) for i in range(3)]                  # 31-mavzu: 3 savol, hammasi to'g'ri — lekin kam (nozik emas)
        q += [Q(f"c{i}", 1, ox=True, kun=0.2) for i in range(10)]
        m = P.matematika_bolimi(q, self.MAV, HOZIR)
        d = {x["raqam"]: x for x in m["mavzular"]}
        self.assertEqual((d[7]["ko_rilgan"], d[7]["hozirgi"], d[7]["nozik"]), (8, 25, True)); self.assertEqual(d[7]["aniqlik"], 50)
        self.assertFalse(d[31]["nozik"]); self.assertFalse(d[1]["nozik"])
        self.assertEqual([x["raqam"] for x in m["nozik"]], [7])
        self.assertEqual(m["ko_rilgan"], 21); self.assertEqual(m["jami_savol"], 170)
        # elementar = 1.1 va 1.2 mavzulari (1 va 7): 18 savol ko'rilgan → ishonchli; hozirgi = (10·100 + 8·25) / 18
        self.assertEqual(m["elementar"]["ko_rilgan"], 18); self.assertTrue(m["elementar"]["ishonchli"]); self.assertEqual(m["elementar"]["hozirgi"], round((10 * 100 + 8 * 25) / 18))
        self.assertEqual(m["elementar"]["daraja"], "yaxshi")     # 67% ≥ 65
        self.assertEqual(sum(m["holatlar"].values()), 21)

    def test_elementar_kam_savol(self):
        m = P.matematika_bolimi([Q(f"a{i}", 1) for i in range(5)], self.MAV, HOZIR)
        self.assertIsNone(m["elementar"]["daraja"]); self.assertFalse(m["elementar"]["ishonchli"])
        self.assertEqual(P.matematika_bolimi([], self.MAV, HOZIR)["ko_rilgan"], 0)

    def test_takrorlash_royxati(self):
        q = [Q(f"x{i}", 31, togri=1, ox=True, kun=4) for i in range(6)] + [Q(f"y{i}", 1, togri=6, ox=True, kun=4) for i in range(6)]
        m = P.matematika_bolimi(q, self.MAV, HOZIR)
        self.assertEqual([x["raqam"] for x in m["takrorlash"]], [31])      # 4 kun oldin 1 marta to'g'ri — takrorlash vaqti; 6 marta to'g'ri — yo'q
        self.assertEqual(m["holatlar"]["takror"] + m["holatlar"]["unutilgan"], 6)


class Faollik(unittest.TestCase):
    def test_kunlar(self):
        v = [HOZIR - timedelta(days=d, hours=h) for d, h in ((0, 0), (0, 3), (1, 0), (3, 0), (10, 0), (40, 0))]
        f = P.faollik_bolimi(v, HOZIR)
        self.assertEqual((f["kun_7"], f["kun_30"], f["jami_harakat"]), (3, 4, 6))
        self.assertEqual(P.faollik_bolimi([], HOZIR), {"oxirgi": None, "kun_7": 0, "kun_30": 0, "jami_harakat": 0})


class Xulosa(unittest.TestCase):
    def test_gaplar_raqamga_tayanadi(self):
        b = bank_ol()
        mav = {r: {"nom": m["nom"], "kitob": m["kitob"], "jami": len(m["testlar"])} for r, m in b.mavzular.items()}
        q = [Q(f"s{i}", 7, urinish=2, togri=1, ox=i < 2, kun=6) for i in range(8)]
        p = {"kim": {}, "faollik": P.faollik_bolimi([HOZIR - timedelta(days=1)], HOZIR), "matematika": P.matematika_bolimi(q, mav, HOZIR),
             "xalqaro": {"sinflar": [{"nom": "TIMSS 8", "guruh": 2, "guruhlar_soni": 3, "reyting": 480}], "sohalar": [{"nom": "Geometriya", "foiz": 33, "jami": 6}], "fikrlash": [], "imtihonlar": [], "zaif_mavzular": []}}
        g = P.xulosa_yoz(p); matn = " ".join(g)
        self.assertIn("Oxirgi 7 kunda 1 kun", matn); self.assertIn("8 ta savol ko‘rilgan", matn); self.assertIn("Nozik mavzular: 7.", matn)
        self.assertIn("2-guruh (3 ta guruhdan), reyting 480", matn); self.assertIn("Geometriya (33%)", matn); self.assertIn("takrorlash vaqti", matn)
        self.assertIn("8 savol yechilgan", matn)                       # elementar daraja aniqlanmaydi: 15 tadan kam
        bosh = P.xulosa_yoz({"faollik": P.faollik_bolimi([], HOZIR), "matematika": P.matematika_bolimi([], mav, HOZIR), "xalqaro": {"sinflar": [], "sohalar": [], "fikrlash": [], "imtihonlar": [], "zaif_mavzular": []}})
        self.assertEqual(len(bosh), 1); self.assertIn("Hali hech qanday", bosh[0])      # bo'sh o'quvchi: o'ylab topilgan gap yo'q


if __name__ == "__main__":
    unittest.main()
