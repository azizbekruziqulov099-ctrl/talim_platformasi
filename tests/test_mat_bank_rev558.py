"""REV558: matematika banki — ma'lumot butunligi, tanlash va baholash qoidalari."""
import json
import random
import re
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "mat_bank"))
from modules import mat_bank as mb  # noqa: E402
import oqi  # noqa: E402


class BankButunligi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = mb.bank_ol()
        cls.data = json.load(open(mb.BANK_FAYL, encoding="utf8"))

    def test_hajm(self):
        self.assertGreaterEqual(len(self.b.mavzular), 131)
        self.assertGreaterEqual(len(self.b.savol) + len(self.b.tekshir), 5392)
        for n in (1, 31, 61, 91, 100, 121, 141):
            self.assertIn(n, self.b.mavzular, n)

    def test_har_test_tugal(self):
        ids = set()
        for t in self.b.savol.values():
            self.assertNotIn(t["id"], ids); ids.add(t["id"])
            self.assertEqual(len(t["variantlar"]), 5, t["id"])
            self.assertTrue(all(v.strip() for v in t["variantlar"]), t["id"])
            self.assertIn(t["javob"], mb.HARFLAR, t["id"])
            self.assertTrue(t["savol"].strip(), t["id"])
            self.assertRegex(t["manba"], r"^\d{2,4}-\d+-\d+$")
            for s in [t["savol"]] + t["variantlar"]:
                self.assertEqual(s.count("$") % 2, 0, f"{t['id']}: formula chegarasi buzilgan")
                self.assertNotRegex(s, r"[⎧⎨⎩\u200b]", t["id"])
                self.assertNotIn("[TEKSHIR]", s)

    # manbaning o'zida qoida yo'q (testlar darhol boshlanadi) — 10, 13, 17-mavzular; 82-mavzuda esa test yo'q. Boshqasi bo'lsa — parser xatosi.
    QOIDASIZ = {10, 13, 17}
    TESTSIZ = {82}

    def test_har_mavzuda_qoida(self):
        bosh = {r for r, m in self.b.mavzular.items() if not m["qoida"].strip()}
        self.assertEqual(bosh, self.QOIDASIZ)
        for r, m in self.b.mavzular.items():
            self.assertTrue(m["nom"].strip(), r)
        self.assertEqual({r for r, m in self.b.mavzular.items() if not m["testlar"]}, self.TESTSIZ)

    def test_javoblar_orasida_nomutanosiblik_yoq(self):
        # 5 harfning hammasi uchraydi va birontasi ustunlik qilmaydi (kalit o'qishda siljish bo'lmaganini bildiradi)
        sana = {h: 0 for h in mb.HARFLAR}
        for t in self.b.savol.values():
            sana[t["javob"]] += 1
        for h, k in sana.items():
            self.assertGreater(k / len(self.b.savol), 0.10, sana)
            self.assertLess(k / len(self.b.savol), 0.32, sana)

    def test_ommaviy_korinishda_javob_yoq(self):
        t = next(iter(self.b.savol.values()))
        self.assertNotIn("javob", self.b.ommaviy(t))
        self.assertEqual(set(self.b.ommaviy(t)), {"id", "mavzu", "manba", "savol", "variantlar", "qiyinlik", "tur"})


class Tozalash(unittest.TestCase):
    def test_word_artefaktlari(self):
        self.assertEqual(oqi.formula_toza(r"a+b\right.\ "), r"a+b\right.")
        self.assertEqual(oqi.formula_toza(r"\frac{1}{8}\mspace{6mu} m/s"), r"\frac{1}{8}\, m/s")
        s = "\\begin{matrix}\n\\begin{matrix}\n⎧ \\\\\n⎨ \\\\\n⎩\n\\end{matrix} & \\begin{matrix}\nx \\leq 0, \\\\\nx \\ge 1.\n\\end{matrix}\n\\end{matrix}"
        self.assertTrue(oqi.formula_toza(s).startswith(r"\left\{ \begin{matrix}") and oqi.formula_toza(s).endswith(r"\right."))
        self.assertEqual(oqi.matn_toza("$a\\mspace{3mu}b$ va $$c$$"), "$a\\,b$ va $$c$$")

    def test_variantlar_ajrat(self):
        s, v = oqi.variantlar_ajrat("Hisoblang: $x$ A) $1$ B) $2$ C) $3$ D) $4$ E) $5$")
        self.assertEqual((s, v), ("Hisoblang: $x$", ["$1$", "$2$", "$3$", "$4$", "$5$"]))
        s, v = oqi.variantlar_ajrat("**A)** $1$   **B)** $2$\\\n**C)** $3$   **D)** $4$\\\n**E)** $5$")
        self.assertEqual(v, ["$1$", "$2$", "$3$", "$4$", "$5$"])
        s, v = oqi.variantlar_ajrat("A nuqta (A) berilgan. A) 1 B) 2 C) 3 D) 4 E) 5")     # savol ichidagi «(A)» variant emas
        self.assertEqual(v, ["1", "2", "3", "4", "5"]); self.assertIn("A nuqta", s)
        self.assertIsNone(oqi.variantlar_ajrat("A) 1 B) 2 C) 3 D) 4")[1])


class Tanlash(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = mb.bank_ol()

    def test_mavzu_va_soni(self):
        s = mb.tanla(self.b, [31], 10, {}, random.Random(1))
        self.assertEqual(len(s), 10); self.assertTrue(all(t["mavzu"] == 31 for t in s))
        self.assertEqual(len({t["id"] for t in s}), 10)
        self.assertEqual(len(mb.tanla(self.b, [], 25, {}, random.Random(2))), 25)
        self.assertEqual(len(mb.tanla(self.b, [73], 40, {}, random.Random(3))), len(self.b.mavzular[73]["testlar"]))   # savol kam mavzu

    def test_avval_korilmaganlar_keyin_xatolar_keyin_togrilar(self):
        ids = [t["id"] for t in self.b.mavzular[31]["testlar"]]
        tarix = {}
        for i in ids[:20]:
            tarix[i] = (1, True, "2026-11-01")         # to'g'ri yechilgan
        for i in ids[20:30]:
            tarix[i] = (2, False, "2026-11-10")        # xato qilingan
        s = mb.tanla(self.b, [31], 15, tarix, random.Random(4))
        # 30 dan ortiq savol hali ko'rilmagan — hammasi ko'rilmaganlardan
        self.assertTrue(all(t["id"] not in tarix for t in s))
        qolgan = [i for i in ids if i not in tarix]
        for i in qolgan:
            tarix[i] = (1, True, "2026-11-12")         # endi hamma ko'rilgan: 10 ta xatosi avval, qolgani to'g'rilar (eskisi avval)
        s = mb.tanla(self.b, [31], len(ids), tarix, random.Random(5))
        self.assertEqual({t["id"] for t in s[:0]}, set())
        xatolar = set(ids[20:30]); olingan = mb.tanla(self.b, [31], 10, tarix, random.Random(6))
        self.assertEqual({t["id"] for t in olingan}, xatolar)
        eski = mb.tanla(self.b, [31], 30, {i: (1, True, "2026-11-01" if k < 20 else "2026-11-12") for k, i in enumerate(ids)}, random.Random(7))
        self.assertTrue(set(ids[:20]) <= {t["id"] for t in eski})                     # eng eski to'g'rilar avval takrorlanadi

    def test_bir_xil_matnli_savol_ikki_marta_chiqmaydi(self):
        s = mb.tanla(self.b, [], 40, {}, random.Random(8))
        kalit = [re.sub(r"\s+", "", t["savol"]) + "|" + "|".join(re.sub(r"\s+", "", v) for v in t["variantlar"]) for t in s]
        self.assertEqual(len(kalit), len(set(kalit)))

    def test_qiyinlik_filtri(self):
        self.assertEqual(mb.tanla(self.b, [31], 10, {}, random.Random(9), "Q"), [])     # qiyinlik belgisi hali yo'q (GPT qo'shadi)


class Baholash(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = mb.bank_ol()

    def test_togri_xato_bosh(self):
        ids = list(self.b.savol)[:4]; t = [self.b.savol[i]["javob"] for i in ids]
        xato = next(h for h in mb.HARFLAR if h != t[1])
        r = mb.baholash(self.b, {ids[0]: t[0], ids[1]: xato, ids[2]: "", ids[3]: t[3].lower()})
        self.assertEqual((r["togri"], r["jami"], r["foiz"]), (2, 4, 50))
        d = {x["id"]: x for x in r["natija"]}
        self.assertTrue(d[ids[0]]["togri"] and not d[ids[1]]["togri"] and not d[ids[2]]["togri"] and d[ids[3]]["togri"])
        self.assertEqual(d[ids[1]]["javob"], t[1]); self.assertEqual(d[ids[2]]["tanlandi"], "")
        self.assertFalse(mb.baholash(self.b, {ids[0]: "Z"})["natija"][0]["togri"])        # noto'g'ri harf — xato
        self.assertIsNone(d[ids[0]]["yechim"])        # yechim yo'li hozircha yo'q (GPT tayyorlagach shu maydon to'ladi)
        t0 = self.b.savol[ids[0]]; t0["yechim"] = "1-qadam. …"
        try:
            self.assertEqual(mb.baholash(self.b, {ids[0]: t0["javob"]})["natija"][0]["yechim"], "1-qadam. …")
        finally:
            del t0["yechim"]
        with self.assertRaises(ValueError):
            mb.baholash(self.b, {"T999-9-999": "A"})
        self.assertEqual(mb.baholash(self.b, {})["foiz"], 0)


if __name__ == "__main__":
    unittest.main()
