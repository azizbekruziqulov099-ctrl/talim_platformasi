"""Milliy sertifikat uslubidagi kirish testi / to'liq sinov: tuzilma, Rasch bahosi, tavsiya."""
import random, unittest
import modules.mat_sertifikat as ms


class MatSertifikat(unittest.TestCase):
    def test_tuzilma_rasmiy(self):
        self.assertEqual(ms.TUZILMA["toliq"]["savol"], 45)
        self.assertEqual(ms.TUZILMA["toliq"]["daqiqa"], 150)
        for v in ms.TUZILMA.values():
            self.assertEqual(sum(v["bolim"].values()), v["savol"])

    def test_test_tuzish(self):
        for tur, n in (("kirish", 20), ("toliq", 45)):
            s = ms.test_tuz(tur, random.Random(3))
            self.assertEqual(len(s), n)
            self.assertEqual(len({i for i, _ in s}), n)
            for b, k in ms.TUZILMA[tur]["bolim"].items():
                self.assertEqual(sum(1 for _, v in s if v["bolim"] == b), k, b)

    def test_ball_monoton_va_chegaralar(self):
        s = ms.test_tuz("toliq", random.Random(5))
        ids = [i for i, _ in s]
        pool = ms.pool_ol()
        ballar = []
        for k in (0, 10, 20, 30, 45):
            jav = {i: (pool[i]["t"]["javob"] if n < k else "Z") for n, i in enumerate(ids)}
            r = ms.baholash("toliq", ids, jav)
            ballar.append(r["ball"])
            self.assertTrue(0 <= r["ball"] <= 75)
        self.assertEqual(ballar, sorted(ballar))
        self.assertLess(ballar[0], 46)
        self.assertGreaterEqual(ballar[-1], 70)

    def test_qiyin_savol_ko_p_ball_beradi(self):
        # bir xil sondagi to'g'ri javob: qiyin savollar to'g'ri bo'lsa — ball yuqori (Rasch)
        t1, _ = ms.eap_theta([(1, True), (-1, False)])
        t2, _ = ms.eap_theta([(1, False), (-1, True)])
        self.assertGreater(t1, t2)

    def test_daraja_harfi(self):
        self.assertEqual(ms.baho_harfi(70), "A+")
        self.assertIsNone(ms.baho_harfi(45.9))
        self.assertEqual(ms.daraja_nomi(40), "tayyorgarlik kerak")

    def test_tavsiya_repetitor_mavzulari(self):
        s = ms.test_tuz("kirish", random.Random(2))
        r = ms.baholash("kirish", [i for i, _ in s], {})
        t = ms.zaif_mavzular(r["natija"])
        self.assertTrue(t)
        for x in t:
            self.assertTrue(1 <= x["mavzu"] <= 150)


if __name__ == "__main__":
    unittest.main()
