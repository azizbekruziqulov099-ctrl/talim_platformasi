"""REV143: Bolalar ligasi — savollar, jamoalar, guruhlar va pley-off to'ri (DB'siz)."""
import random
import unittest

from modules.chempionat import (DARAJALAR, doira, golib_aniqla, guruh_jadvali, guruhlarga_bol, jamoalarga_bol, javob_ball,
                                pleyoff_juftlari, pool, profil, savol_korinish, savollar_tuz, bosqich_nomi)


class SavolTests(unittest.TestCase):
    def test_every_language_age_and_mix_builds_fair_questions(self):
        pl = pool()
        for til in pl["tillar"]:
            for daraja in DARAJALAR:
                pr = profil(daraja)
                for fanlar in (["soz"], ["harakat"], ["bilim"], ["soz", "harakat", "bilim"]):
                    for seed in range(4):
                        sav = savollar_tuz(daraja, til, fanlar, random.Random(seed), pl)
                        self.assertEqual(len(sav), pr["savol"])
                        for i, q in enumerate(sav):
                            keys = [v["k"] for v in q["variantlar"]]
                            self.assertIn(q["javob"], keys)
                            self.assertEqual(len(set(keys)), len(keys))
                            want = max(3, pr["variant"]) if q["tur"] == "ortiqcha" else min(pr["variant"], pr["sana"]) if q["tur"] == "sana" else pr["variant"]
                            self.assertEqual(len(keys), want, (til, daraja, q))
                            for izoh in ("uz", "ru", "en"):
                                v = savol_korinish(q, izoh, i, len(sav), pl)
                                self.assertNotIn("javob", v)
                                self.assertTrue(v["ovoz"].strip())

    def test_composition_is_identical_for_every_child(self):
        a = savollar_tuz("4-5 yosh", "en", ["soz", "harakat", "bilim"], random.Random(1))
        b = savollar_tuz("4-5 yosh", "en", ["soz", "harakat", "bilim"], random.Random(2))
        self.assertEqual(sorted(q["tur"] for q in a), sorted(q["tur"] for q in b))
        self.assertNotEqual([q["javob"] for q in a], [q["javob"] for q in b])   # har bolaga boshqa savol

    def test_harakat_pairs_and_odd_one_out(self):
        pl = pool()
        rng = random.Random(3)
        for _ in range(200):
            q = savollar_tuz("6-7 yosh", "en", ["harakat", "bilim"], rng, pl)
            for x in q:
                if x["tur"] == "harakat":
                    ids = {v["k"] for v in x["variantlar"]}
                    for a, b in pl["juft"]:   # to'g'ri javobning juftlari (och/yop) chalg'ituvchi bo'lmaydi
                        if x["javob"] in (a, b):
                            self.assertFalse(a in ids and b in ids)
                if x["tur"] == "ortiqcha":
                    tk = {i: k for k, v in pl["turkum"].items() for i in v}
                    kat = [tk[v["k"]] for v in x["variantlar"]]
                    self.assertEqual(sum(1 for k in kat if k == tk[x["javob"]]), 1)

    def test_score(self):
        self.assertEqual(javob_ball(False, 100, 20), 0)
        self.assertEqual(javob_ball(True, 0, 20), 150)
        self.assertEqual(javob_ball(True, 20000, 20), 100)


class FormatTests(unittest.TestCase):
    def test_teams_balanced(self):
        for n in range(2, 60):
            for hajm in (1, 5, 10, 15, 20):
                t = jamoalarga_bol(list(range(n)), hajm, random.Random(n))
                self.assertEqual(sorted(x for g in t for x in g), list(range(n)))
                self.assertGreaterEqual(len(t), 2)
                self.assertLessEqual(max(map(len, t)) - min(map(len, t)), 1)
        self.assertEqual(jamoalarga_bol([1], 5, random.Random(1)), [])

    def test_round_robin(self):
        for n in range(2, 9):
            turlar = doira(list(range(n)))
            seen = set()
            for tur in turlar:
                band = [x for a, b in tur for x in (a, b) if x is not None]
                self.assertEqual(len(band), len(set(band)))
                for a, b in tur:
                    if b is not None:
                        seen.add(frozenset((a, b)))
            self.assertEqual(len(seen), n * (n - 1) // 2)

    def test_groups(self):
        self.assertEqual(guruhlarga_bol([1, 2], random.Random(1)), {})
        for n in range(3, 40):
            g = guruhlarga_bol(list(range(n)), random.Random(n))
            sizes = [len(v) for v in g.values()]
            self.assertEqual(sum(sizes), n)
            if n >= 6:
                self.assertGreaterEqual(min(sizes), 3)
                self.assertLessEqual(max(sizes), 4)

    def test_bracket_seeding_and_byes(self):
        p = pleyoff_juftlari([1, 2, 3, 4, 5, 6])
        self.assertEqual(len(p), 4)
        self.assertEqual(sorted(x for x in (a for a, _ in p)), [1, 2, 3, 4])
        self.assertEqual(sum(1 for _, b in p if b is None), 2)        # eng kuchli ikkitasi dam oladi
        p = pleyoff_juftlari(list(range(1, 9)))
        self.assertEqual(p[0], (1, 8))
        self.assertIn((2, 7), p)
        self.assertEqual(bosqich_nomi(len(p) * 2), "1/4")

    def test_winner_and_table(self):
        u = {"a_id": 1, "b_id": 2, "a_ball": 300, "b_ball": 300, "a_togri": 5, "b_togri": 4}
        self.assertIsNone(golib_aniqla(u, "s", False))
        self.assertEqual(golib_aniqla(u, "s", True), 1)
        u["b_togri"] = 5
        self.assertIn(golib_aniqla(u, "s", True), (1, 2))
        self.assertEqual(golib_aniqla(u, "s", True), golib_aniqla(dict(u), "s", True))
        t = guruh_jadvali([1, 2, 3], [{"a_id": 1, "b_id": 2, "a_ball": 500, "b_ball": 100, "holat": "tugadi"},
                                      {"a_id": 2, "b_id": 3, "a_ball": 200, "b_ball": 200, "holat": "tugadi"}])
        self.assertEqual([r["jamoa_id"] for r in t], [1, 3, 2])
        self.assertEqual(t[0]["ochko"], 3)


if __name__ == "__main__":
    unittest.main()


class JamoaLigaTests(unittest.TestCase):
    def test_snake_teams_are_balanced(self):
        from modules.oyin_turnir import jamoalarga_bol
        ps = [{"user_id": i, "ism": str(i), "reyting": 2000 - i * 50} for i in range(12)]
        t = jamoalarga_bol(ps, 3)
        self.assertEqual(len(t), 4)
        sums = [sum(2000 - u * 50 for u in j["azolar"]) for j in t]
        self.assertLessEqual(max(sums) - min(sums), 150)
        self.assertEqual(jamoalarga_bol(ps[:1], 3), [])

    def test_team_table(self):
        from modules.oyin_turnir import jamoa_jadvali
        jam = [{"id": 1, "azolar": [1, 2], "dam": []}, {"id": 2, "azolar": [3, 4], "dam": []}, {"id": 3, "azolar": [5, 6], "dam": [1]}]
        g = [{"tur": 1, "oq_id": 1, "qora_id": 3, "holat": "tugadi", "golib": "w"},
             {"tur": 1, "oq_id": 4, "qora_id": 2, "holat": "tugadi", "golib": "durang"},
             {"tur": 2, "oq_id": 1, "qora_id": 5, "holat": "davom", "golib": None}]
        t = jamoa_jadvali(jam, g)
        self.assertEqual([r["jamoa_id"] for r in t], [1, 3, 2])
        self.assertEqual(t[0]["ochko"], 1)          # 1½ : ½ — g'alaba
        self.assertEqual(t[1]["ochko"], 1)          # dam — g'alaba
        self.assertNotIn("2", t[0]["natijalar"])     # tugamagan uchrashuv hisoblanmaydi
