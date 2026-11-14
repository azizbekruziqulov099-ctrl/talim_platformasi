"""REV543: Kabu loyiha portfeli — loyiha kalitlari va chegaralar (frontend bilan bir xil ro'yxat)."""
import unittest

from modules import loyiha_portfel as L


class LoyihaPortfel(unittest.TestCase):
    def test_loyiha_kalitlari(self):
        # frontend (src/games/loyiha): 5 + 10 loyiha
        kutilgan = {"osimlik", "koprik", "kod", "naqsh", "byudjet", "filtr", "richag", "parashyut", "qayiq", "soya", "qiya", "masshtab", "sorov", "rang", "kod2",
                    "energiya", "tahlil", "shamol", "fraktal", "kredit"}   # REV546: 5 + 10 + 5
        self.assertEqual(L.LOYIHALAR, kutilgan)

    def test_rasm_chegarasi(self):
        self.assertLessEqual(L.RASM_MAX, 1_000_000)

    def test_modellar(self):
        self.assertEqual(L.Natija(loyiha="koprik", yulduz=3).yulduz, 3)
        with self.assertRaises(Exception):
            L.Natija(loyiha="koprik", yulduz=4)
        with self.assertRaises(Exception):
            L.Qolda(loyiha="koprik", rasm="x", izoh="a" * 401)


class Jamoalar(unittest.TestCase):
    """REV544: sinfni 3–4 kishilik jamoalarga bo'lish."""

    def test_olchamlar(self):
        for n in range(3, 41):
            b = L.jamoalarga_bol(range(1, n + 1)); o = {}
            for j, u, r in b:
                o[j] = o.get(j, 0) + 1
            self.assertEqual(len(b), n); self.assertEqual({u for _, u, _ in b}, set(range(1, n + 1)))
            self.assertGreaterEqual(min(o.values()), 3, f"n={n}: {o}")
            self.assertLessEqual(max(o.values()), 5, f"n={n}: {o}")

    def test_rollar(self):
        b = L.jamoalarga_bol(range(1, 9))
        for jamoa in {x[0] for x in b}:
            rollar = [r for j, _, r in b if j == jamoa]
            self.assertEqual(len(set(rollar)), len(rollar), "jamoada rol takrorlanmasin (4 kishigacha)")
        self.assertEqual(L.jamoalarga_bol([]), [])

    def test_rubrika_chegarasi(self):
        with self.assertRaises(Exception):
            L.Rubrika(oquvchi_id=1, loyiha="koprik", tanqidiy=0, ijodkor=3, hamkor=3, muloqot=3)
        self.assertEqual(L.Rubrika(oquvchi_id=1, loyiha="koprik", tanqidiy=4, ijodkor=1, hamkor=2, muloqot=3).hamkor, 2)


if __name__ == "__main__":
    unittest.main()
