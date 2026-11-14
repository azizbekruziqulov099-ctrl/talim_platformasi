"""REV566: aniq geometrik chizma — koordinatalardan qayta o'lchangan sonlar berilgan sonlarga teng bo'lishi shart; zid va yaroqsiz kiritishlar rad etiladi."""
import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "mat_bank"))
import geo_chizma as G  # noqa: E402

d = lambda f, a, b: math.dist(f["nuqtalar"][a], f["nuqtalar"][b])


def burchak(f, uch, a, b):
    P = f["nuqtalar"]; u = (P[a][0] - P[uch][0], P[a][1] - P[uch][1]); v = (P[b][0] - P[uch][0], P[b][1] - P[uch][1])
    return math.degrees(math.acos((u[0] * v[0] + u[1] * v[1]) / (math.hypot(*u) * math.hypot(*v))))


class Olchov(unittest.TestCase):
    def test_romb_har_xil_berilishda(self):
        rnd = random.Random(7)
        for _ in range(60):
            a = rnd.uniform(2, 12); al = rnd.uniform(20, 160)
            d1 = 2 * a * math.cos(math.radians(al) / 2); d2 = 2 * a * math.sin(math.radians(al) / 2)
            for arg in (f"romb a={a:.6f} burchak={al:.6f}", f"romb d1={d1:.6f} d2={d2:.6f}", f"romb a={a:.6f} d1={d1:.6f}", f"romb a={a:.6f} d2={d2:.6f}", f"romb a={a:.6f} h={a * math.sin(math.radians(al)):.6f}" if al < 90 else f"romb a={a:.6f} d1={d1:.6f} d2={d2:.6f}"):
                f = G.coz(arg)
                for x, y in (("A", "B"), ("B", "C"), ("C", "D"), ("D", "A")):
                    self.assertAlmostEqual(d(f, x, y), a, delta=1e-3 * a, msg=arg)                  # 4 tomon teng va a ga teng
                self.assertAlmostEqual(d(f, "A", "C") ** 2 + d(f, "B", "D") ** 2, 4 * a * a, delta=1e-2, msg=arg)
                self.assertAlmostEqual(burchak(f, "O", "A", "B"), 90, delta=1e-6)                     # diagonallar perpendikulyar
                ba = burchak(f, "A", "B", "D"); self.assertTrue(abs(ba - al) < 0.05 or abs(ba - (180 - al)) < 0.05, f"{arg}: {ba}")

    def test_romb_3_4_5(self):
        f = G.coz("romb a=5 d1=6 d2=8"); self.assertAlmostEqual(d(f, "A", "B"), 5)
        self.assertEqual(sorted([round(d(f, "A", "C"), 6), round(d(f, "B", "D"), 6)]), [6, 8])
        self.assertAlmostEqual(d(f, "A", "C"), 8); self.assertLess(burchak(f, "A", "B", "D"), 90)             # burchak berilmasa A O'TKIR burchak (AC uzun diagonal)
        self.assertEqual({k["a"] + k["b"]: k["yozuv"] for k in f["kesmalar"] if k["yozuv"]}, {"AB": "5", "AC": "8", "BD": "6"})     # yozuv uzunligi mos diagonalda
        self.assertEqual({k["a"] + k["b"]: k["yozuv"] for k in G.coz("romb a=5 d1=6")["kesmalar"] if k["yozuv"]}, {"AB": "5", "BD": "6"})   # d2 chizilgan (8), lekin yozilmaydi
        f = G.coz("romb a=5 d1=6 d2=8 h=4.8"); self.assertAlmostEqual(d(f, "D", "E"), 4.8, places=6)
        P = f["nuqtalar"]; self.assertTrue(P["A"][0] < P["E"][0] < P["B"][0], "o'tkir A da balandlik asosi AB ning ichida")
        f = G.coz("romb a=5 d1=6 burchak=106.26 h=4.8"); self.assertAlmostEqual(d(f, "D", "E"), 4.8, places=2); self.assertAlmostEqual(d(f, "A", "C"), 6, places=2)     # burchak berilsa — A burchagi shu (o'tmas)
        self.assertEqual(G.yozuv(5.196), "5,196"); self.assertEqual(G.yozuv(4.8), "4,8"); self.assertEqual(G.yozuv(5.0), "5"); self.assertEqual(G.yozuv(2.8284), "2,828")
        self.assertEqual({k["a"] + k["b"]: k["yozuv"] for k in G.coz("romb a=6 burchak=60 h=5.196")["kesmalar"] if k["yozuv"]}, {"AB": "6", "DE": "5,196"})

    def test_uchburchaklar(self):
        f = G.coz("uchburchak a=7 b=8 c=9"); self.assertAlmostEqual(d(f, "B", "C"), 7); self.assertAlmostEqual(d(f, "C", "A"), 8); self.assertAlmostEqual(d(f, "A", "B"), 9)
        f = G.coz("uchburchak a=5 b=6 burchak=60"); self.assertAlmostEqual(burchak(f, "C", "A", "B"), 60, places=6); self.assertAlmostEqual(d(f, "A", "B"), math.sqrt(25 + 36 - 30), places=6)
        f = G.coz("togri_uchburchak a=3 b=4"); self.assertAlmostEqual(d(f, "A", "B"), 5); self.assertAlmostEqual(burchak(f, "C", "A", "B"), 90, places=6)
        f = G.coz("togri_uchburchak a=5 c=13"); self.assertAlmostEqual(d(f, "C", "A"), 12); f = G.coz("togri_uchburchak b=8 c=17"); self.assertAlmostEqual(d(f, "B", "C"), 15)
        self.assertEqual([k["yozuv"] for k in G.coz("togri_uchburchak a=3 b=4 c=5")["kesmalar"]], ["3", "4", "5"])

    def test_parallelogramm_trapetsiya_aylana(self):
        f = G.coz("parallelogramm a=6 b=4 burchak=60 h=3.4641"); self.assertAlmostEqual(d(f, "A", "B"), 6, places=6); self.assertAlmostEqual(d(f, "A", "D"), 4, places=6); self.assertAlmostEqual(d(f, "B", "C"), 4, places=6); self.assertAlmostEqual(burchak(f, "A", "B", "D"), 60, places=5); self.assertAlmostEqual(d(f, "D", "E"), 3.4641, places=3)
        f = G.coz("trapetsiya a=8 b=4 h=3"); self.assertAlmostEqual(d(f, "A", "B"), 8); self.assertAlmostEqual(d(f, "D", "C"), 4); self.assertAlmostEqual(d(f, "B", "C"), d(f, "A", "D")); self.assertAlmostEqual(d(f, "B", "C"), math.hypot(2, 3)); self.assertAlmostEqual(d(f, "D", "E"), 3)
        f = G.coz("trapetsiya a=8 b=2 h=4 yon=5"); self.assertAlmostEqual(d(f, "A", "D"), 5, places=6); self.assertAlmostEqual(d(f, "B", "C"), 5, places=6)        # teng yonli: yon = √(((a−b)/2)² + h²) = √(9+16) = 5
        f = G.coz("trapetsiya a=8 b=4 h=3 tur=togri"); self.assertAlmostEqual(d(f, "B", "C"), 5); self.assertAlmostEqual(burchak(f, "A", "B", "D"), 90, places=6); self.assertNotIn("E", f["korinadigan"])
        f = G.coz("aylana r=5 vatar=8"); self.assertAlmostEqual(d(f, "P", "Q"), 8); self.assertAlmostEqual(d(f, "O", "P"), 5); self.assertAlmostEqual(d(f, "O", "H"), 3); self.assertEqual(f["dumaloqlar"][0]["r"], 5)

    def test_chegara_va_tuzilma(self):
        for arg in ("romb a=5 d1=6 d2=8", "uchburchak a=3 b=4 c=5", "parallelogramm a=6 b=4 burchak=60", "trapetsiya a=8 b=4 h=3", "aylana r=3", "togri_uchburchak a=3 b=4"):
            f = G.coz(arg); self.assertEqual(f["arg"], arg); self.assertTrue(f["kesmalar"] and f["chegara"][2] > f["chegara"][0] and f["chegara"][3] > f["chegara"][1])
            for p in f["nuqtalar"].values():
                self.assertTrue(f["chegara"][0] - 1e-9 <= p[0] <= f["chegara"][2] + 1e-9 and f["chegara"][1] - 1e-9 <= p[1] <= f["chegara"][3] + 1e-9)
            for k in f["kesmalar"]:
                self.assertIn(k["a"], f["nuqtalar"]); self.assertIn(k["b"], f["nuqtalar"])
            for b in f["burchaklar"]:
                self.assertIn(b["uch"], f["nuqtalar"])


class Rad(unittest.TestCase):
    def rad(self, arg, soz):
        with self.assertRaises(G.GeoXato) as e:
            G.coz(arg)
        self.assertIn(soz, str(e.exception), arg)

    def test_zid_sonlar(self):
        self.rad("romb a=5 d1=6 d2=7", "zid"); self.rad("romb a=5 d1=6 d2=8 burchak=50", "zid"); self.rad("togri_uchburchak a=3 b=4 c=6", "zid"); self.rad("parallelogramm a=6 b=4 burchak=60 h=3", "zid")
        self.rad("uchburchak a=3 b=4 c=5 burchak=80", "zid"); self.rad("trapetsiya a=8 b=4 h=3 yon=9", "zid"); self.rad("romb a=5 h=4 burchak=40", "zid")

    def test_yaroqsiz(self):
        self.rad("uchburchak a=1 b=2 c=5", "bo'lmaydi"); self.rad("uchburchak a=1 b=2 c=3", "bo'lmaydi"); self.rad("romb a=5 d1=11", "kichik"); self.rad("romb a=5 h=6", "balandlik"); self.rad("trapetsiya a=4 b=8 h=3", "katta asos")
        self.rad("aylana r=3 vatar=7", "diametr"); self.rad("romb d1=6", "kamida"); self.rad("togri_uchburchak a=3", "ikkita"); self.rad("togri_uchburchak a=5 c=4", "gipotenuza")
        self.rad("xyz a=1", "noma'lum shakl"); self.rad("romb q=1 a=2", "parametri yo'q"); self.rad("romb a=-5 d1=6", "musbat"); self.rad("romb a=0 d1=6", "musbat"); self.rad("romb a=5 a=6", "ikki marta"); self.rad("", "shakl nomi")
        self.rad("parallelogramm a=6 b=4 burchak=180", "180"); self.rad("romb a=5,5 d1=6", "noto'g'ri"); self.rad("trapetsiya a=8 b=4 h=3 tur=xyz", "tur")


if __name__ == "__main__":
    unittest.main()
