"""REV561: baho harfi (C…A+), qiyinlik, nuqsonli testlar o'quvchiga berilmasligi, KABUTAR fayllarni birlashtirish dasturi."""
import copy
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "mat_bank"))
from modules import mat_bank as mb  # noqa: E402
import qosh  # noqa: E402


class Baho(unittest.TestCase):
    def test_rasmiy_shkala(self):
        # Milliy sertifikat: 70+ A+, 65–69,9 A, 60–64,9 B+, 55–59,9 B, 50–54,9 C+, 46–49,9 C
        for foiz, harf in [(100, "A+"), (70, "A+"), (69.9, "A"), (65, "A"), (64.9, "B+"), (60, "B+"), (59.9, "B"), (55, "B"), (54.9, "C+"), (50, "C+"), (49.9, "C"), (46, "C"), (45.9, None), (0, None)]:
            self.assertEqual(mb.baho_harfi(foiz), harf, foiz)

    def test_testdagi_baho(self):
        b = mb.bank_ol(); ids = list(b.savol)[:10]
        for togri, kutilgan in [(10, "A+"), (7, "A+"), (6, "B+"), (5, "C+"), (4, None)]:      # 6/10 = 60% → B+, 5/10 = 50% → C+, 4/10 = 40% → C ga yetmadi
            jav = {i: (b.savol[i]["javob"] if k < togri else next(h for h in "ABCDE" if h != b.savol[i]["javob"])) for k, i in enumerate(ids)}
            r = mb.baholash(b, jav); self.assertEqual(r["baho"], kutilgan, togri); self.assertIn("Taxminiy", r["baho_izoh"])
        self.assertEqual(mb.baholash(b, {ids[0]: ""})["baho"], None)           # javobsiz — baho yo'q

    def test_qiyinlik_xulosasi(self):
        T = lambda *q: [{"qiyinlik": x} for x in q]
        self.assertEqual(mb.qiyinlik_xulosasi(T("O", "O", "O"))["daraja"], "oson"); self.assertEqual(mb.qiyinlik_xulosasi(T("R", "R", "O", "Q"))["daraja"], "o'rta")
        self.assertEqual(mb.qiyinlik_xulosasi(T("Q", "Q", "R"))["daraja"], "qiyin")
        self.assertIsNone(mb.qiyinlik_xulosasi(T("R", None, None, None)))         # belgisi yarmidan kam — aytilmaydi
        self.assertIsNone(mb.qiyinlik_xulosasi([]))


class Nuqsonli(unittest.TestCase):
    def test_uchta_test_belgilangan_va_berilmaydi(self):
        b = mb.bank_ol()
        self.assertEqual(sorted(b.tekshir), ["T100-1-015", "T100-1-019", "T141-1-001"])
        for i in b.tekshir:
            self.assertNotIn(i, b.savol); self.assertTrue(b.tekshir[i]["tekshir_izoh"])
        for seed in range(40):                                                    # qaysi mavzu va qanday urug' bo'lmasin — nuqsonli test chiqmaydi
            for ml in ([100], [141], []):
                self.assertFalse({t["id"] for t in mb.tanla(b, ml, 40, {}, random.Random(seed))} & set(b.tekshir))
        with self.assertRaises(ValueError):
            mb.baholash(b, {"T100-1-019": "D"})                                   # tekshirishga ham yuborib bo'lmaydi

    def test_soni_nuqsonlisiz(self):
        b = mb.bank_ol(); self.assertEqual(b.soni(100), 36); self.assertEqual(b.soni(141), 13); self.assertEqual(b.soni(31), len(b.mavzular[31]["testlar"]))

    def test_kabutar_maydonlari(self):
        b = mb.bank_ol()
        for t in b.savol.values():
            if t["mavzu"] in (100, 141):
                self.assertIn(t["qiyinlik"], "ORQ"); self.assertTrue(t["yechim"].strip()); self.assertIsInstance(t["tur"], int)
        self.assertEqual(len(b.mavzular[100]["misollar"]), 12); self.assertEqual(b.mavzular[141]["turlar"], list(range(1, 12)))
        self.assertTrue(os.path.isfile(os.path.join(mb.RASM_PAPKA, "T100-1.png")))
        self.assertIn("rasm:T100-1.png", b.mavzular[100]["misollar"][0]["matn"])


# ───────── KABUTAR fayllarni birlashtirish dasturi: sintetik markdown ─────────
def md(javob="1-B; 2-A;", qisqa_b="B", qisqa_a="A", namuna_javob="B", tur_namuna=1, kitob="9.9", testlar2=True):
    return (f"# **MAVZU: {kitob} \\| SINOV**\nMANBA: Tematika\n## **QOIDA**\n1\\. Qoida $a$.\n"
            f"## **NAMUNA 1 \\| TUR {tur_namuna} \\| TO'LIQ**\n**(96-1-1)** Savol bir.\n\nA) $1$ B) $2$ C) $3$ D) $4$ E) $5$\n\n**YECHISH:**\n1-qadam. Hisob.\n2-qadam. Natija.\n**JAVOB: {namuna_javob}**\n"
            "## **TESTLAR**\n1 \\| TUR 1 \\| O \\| **(96-1-1)** Savol bir.\n**A)** $1$   **B)** $2$\\\n**C)** $3$   **D)** $4$\\\n**E)** $5$\n"
            + ("2 \\| TUR 2 \\| Q \\| **(96-1-2)** Savol ikki.\n**A)** $1$   **B)** $2$\\\n**C)** $3$   **D)** $4$\\\n**E)** $5$\n\\[TEKSHIR\\] Shart ziddiyatli.\n" if testlar2 else "")
            + f"## **JAVOBLAR**\n{javob.replace('2-A;', '2-A \\[TEKSHIR\\];')}\n## **QISQA YECHIMLAR**\n1\\. Hisoblaymiz. $2$ → {qisqa_b}\n2\\. Boshqacha. $1$ → {qisqa_a}\n")


def BANK():
    t = lambda i, m, j: {"id": f"T999-1-{i:03d}", "blok": 1, "n": i, "manba": m, "savol": f"Savol {i}", "variantlar": ["$1$", "$2$", "$3$", "$4$", "$5$"], "javob": j}
    return {"manba": "x", "mavzular": [{"raqam": 999, "kitob": "9.9", "nom": "SINOV", "qoida": "Qoida", "namunalar": [], "testlar": [t(1, "96-1-1", "B"), t(2, "96-1-2", "A")]}]}


class Birlashtirish(unittest.TestCase):
    def ishla(self, matn, bank=None):
        b = bank or BANK(); r = qosh.oqi(matn); xato, ogoh = qosh.tekshir_va_qosh(b, 999, r); return b, xato, ogoh

    def test_togri_fayl_qoshiladi_va_tekshir_belgilanadi(self):
        b, xato, ogoh = self.ishla(md())
        self.assertEqual(xato, [])
        t1, t2 = b["mavzular"][0]["testlar"]
        self.assertEqual((t1["tur"], t1["qiyinlik"], t1["yechim"]), (1, "O", "Hisoblaymiz. $2$ → B")); self.assertNotIn("tekshir", t1)
        self.assertTrue(t2["tekshir"]); self.assertIn("ziddiyatli", t2["tekshir_izoh"]); self.assertEqual((t2["tur"], t2["qiyinlik"]), (2, "Q"))    # \[TEKSHIR\] (pandoc yozuvi) tanildi
        self.assertEqual(b["mavzular"][0]["misollar"][0]["tur"], 1); self.assertEqual(b["mavzular"][0]["turlar"], [1, 2])
        self.assertEqual(t1["javob"], "B"); self.assertEqual(t1["savol"], "Savol 1")           # manbadagi savol va javob o'zgarmaydi

    def test_javob_harfi_mos_emas_rad(self):
        _, xato, _ = self.ishla(md(javob="1-C; 2-A;")); self.assertTrue(any("kalit" in x for x in xato))
        _, xato, _ = self.ishla(md(qisqa_b="C")); self.assertTrue(any("qisqa yechim oxiridagi harf" in x for x in xato))
        _, xato, _ = self.ishla(md(namuna_javob="D")); self.assertTrue(any("NAMUNA 1" in x and "kalit" in x for x in xato))
        _, xato, _ = self.ishla(md(tur_namuna=7)); self.assertTrue(any("TUR" in x for x in xato))

    def test_rad_etilganda_bank_ozgarmaydi(self):
        b0 = BANK(); b, xato, _ = self.ishla(md(javob="1-C; 2-A;"), copy.deepcopy(b0)); self.assertTrue(xato)
        self.assertEqual(b["mavzular"][0]["testlar"], b0["mavzular"][0]["testlar"]); self.assertNotIn("misollar", b["mavzular"][0])

    def test_testlar_toplami_aynan_bir_xil(self):
        _, xato, _ = self.ishla(md(testlar2=False, javob="1-B;")); self.assertTrue(any("faylda yo'q" in x for x in xato))        # bankda 2 ta, faylda 1 ta
        b = BANK(); b["mavzular"][0]["testlar"].pop(); _, xato, _ = self.ishla(md(), b); self.assertTrue(any("bankda yo'q" in x for x in xato))   # faylda ortiqcha
        b = BANK(); b["mavzular"][0]["kitob"] = "1.1"; _, xato, _ = self.ishla(md(), b); self.assertTrue(any("kitob bo'limi" in x for x in xato))
        r = qosh.oqi(md()); self.assertEqual(qosh.tekshir_va_qosh(BANK(), 5, r)[0], ["bankda 5-mavzu yo'q"])

    def test_buzuq_tuzilma(self):
        with self.assertRaises(ValueError):
            qosh.oqi("# **SARLAVHA YO'Q**\n## **TESTLAR**\n")
        with self.assertRaises(ValueError):
            qosh.oqi(md().replace("## **JAVOBLAR**", "## **BOSHQA**"))


if __name__ == "__main__":
    unittest.main()
