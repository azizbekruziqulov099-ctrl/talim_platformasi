"""REV564: Repetitor darsi — validator qabul/rad qoidalari, namuna dars, server."""
import copy
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "mat_bank"))
from modules import mat_bank as mb  # noqa: E402
import dars_qosh as D  # noqa: E402

NAMUNA = os.path.join(os.path.dirname(__file__), "..", "tools", "mat_bank", "dars_namuna", "KABUTAR_DARS_100_100.md")


def bank_100():
    return json.load(open(mb.BANK_FAYL, encoding="utf8"))


def ishla(matn, raqam=100, bank=None):
    d = {"darslar": {}}; xato, ogoh = D.tekshir_va_qosh(bank or bank_100(), raqam, D.oqi(matn), d); return d, xato, ogoh


class Validator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.md = open(NAMUNA, encoding="utf8").read()

    def test_namuna_dars_qabul(self):
        d, xato, ogoh = ishla(self.md)
        self.assertEqual(xato, []); x = d["darslar"]["100"]
        self.assertEqual((len(x["tushuncha"]), len(x["misollar"]), x["tekshir_manbalar"]), (5, 5, ["96-7-47", "97-7-47", "97-10-47", "97-10-48"])); self.assertFalse(x["tekshir"]); self.assertEqual(x["bob"], "3-bob. PLANIMETRIYA")

    def test_javob_harfi_notogri_rad(self):
        _, xato, _ = ishla(self.md.replace("JAVOB: D", "JAVOB: C", 1)); self.assertTrue(any("manba kaliti" in x and "96-6-38" in x for x in xato))
        _, xato, _ = ishla(self.md.replace("JAVOB: B", "JAVOB: A", 1)); self.assertTrue(any("manba kaliti" in x for x in xato))
        _, xato, _ = ishla(self.md.replace("JAVOB: E", "")); self.assertTrue(any("JAVOB: X" in x for x in xato))

    def test_kodlar_va_tur(self):
        _, xato, _ = ishla(self.md.replace("(96-6-38)", "(96-6-99)")); self.assertTrue(any("bunday test yo'q" in x for x in xato))
        _, xato, _ = ishla(self.md.replace("TUR 1 | (96-6-38)", "TUR 9 | (96-6-38)")); self.assertTrue(any("TUR 9 ≠ bankdagi TUR 1" in x for x in xato))
        _, xato, _ = ishla(self.md.replace("(96-7-47) (97-7-47)", "(96-6-38) (97-7-47)")); self.assertTrue(any("misolda yechib bo'lingan" in x for x in xato))     # o'zini tekshir savoli misolda bor
        _, xato, _ = ishla(self.md.replace("(97-10-47) (97-10-48)", "")); self.assertTrue(any("3–6 ta manba kodi" in x for x in xato))
        _, xato, _ = ishla(self.md.replace("(96-6-38)\nG'OYA", "\nG'OYA")); self.assertTrue(any("manba kodi) yo'q" in x for x in xato))

    def test_nuqsonli_test_misol_bolmaydi(self):
        _, xato, _ = ishla(self.md.replace("(96-6-38)", "(99-7-39)", 1)); self.assertTrue(any("nuqsonli" in x for x in xato))                 # 99-7-39 — [TEKSHIR]
        _, xato, _ = ishla(self.md.replace("(97-10-48)", "(99-7-39)")); self.assertTrue(any("nuqsonli" in x for x in xato))

    def test_tuzilma(self):
        for bolim in ("## MAQSAD", "## ESDA TUT", "## KO'P UCHRAYDIGAN XATOLAR"):
            _, xato, _ = ishla(self.md.replace(bolim, "## BOSHQA")); self.assertTrue(xato, bolim)
        _, xato, _ = ishla(self.md.replace("# DARS: 100 | ROMB", "# DARS: 100 | PARALLELOGRAMM")); self.assertTrue(any("nomi mos emas" in x for x in xato))
        _, xato, _ = ishla(self.md.replace("# DARS: 100", "# DARS: 101")); self.assertTrue(any("raqam" in x for x in xato))
        _, xato, _ = ishla(self.md.replace("G'OYA:", "IZOH:", 1)); self.assertTrue(any("G'OYA" in x for x in xato))
        self.assertEqual(ishla(self.md, raqam=999)[1], ["bankda 999-mavzu yo'q"])
        with self.assertRaises(ValueError):
            D.oqi("DARS yo'q\n## MAQSAD\nx")

    def test_tekshir_belgisi_darsni_yashiradi(self):
        d, xato, ogoh = ishla(self.md.replace("## ESDA TUT\n", "## ESDA TUT\n\\[TEKSHIR\\] shu qatorni ko'rib chiqing.\n"))
        self.assertEqual(xato, []); self.assertTrue(d["darslar"]["100"]["tekshir"]); self.assertTrue(any("o'quvchiga ko'rsatilmaydi" in o for o in ogoh))

    def test_pandoc_yozuvi(self):
        # docx → pandoc: sarlavhalar «## **NOM**», «\|», «1\.»
        md = self.md.replace("# DARS: 100 | ROMB", "# **DARS: 100 \\| ROMB**").replace("## MAQSAD", "## **MAQSAD**").replace("## MISOL TAHLILI", "## **MISOL TAHLILI**").replace("## O'ZINI TEKSHIR", "## **O'ZINI TEKSHIR**").replace("\n1. Romb yuzini", "\n1\\. Romb yuzini")
        self.assertEqual(ishla(md)[1], [])


class Server(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = mb.bank_ol()

    def test_dars_korinishi(self):
        d = self.b.dars_korinishi(100)
        self.assertEqual([x["manba"] for x in d["misollar"]], ["96-6-38", "97-3-47", "96-7-48", "97-7-44", "97-9-114"])
        self.assertEqual([x["nom"] for x in d["misollar"]][:2], ["Misol 1 · TUR 1", "Misol 2 · TUR 2"])
        self.assertIn("Rombning yuzi $18$ ga", d["misollar"][0]["savol"]); self.assertEqual(len(d["misollar"][0]["variantlar"]), 5)         # savol bankdan qo'yildi
        self.assertEqual(len(d["tekshir_ids"]), 4); self.assertTrue(all(i in self.b.savol for i in d["tekshir_ids"]))
        self.assertIsNone(self.b.dars_korinishi(31)); self.assertIsNone(self.b.dars_korinishi(999))

    def test_tekshir_belgili_dars_korsatilmaydi(self):
        b = mb.Bank(json.load(open(mb.BANK_FAYL, encoding="utf8"))); b.darslar["100"] = dict(b.darslar["100"], tekshir=True)
        self.assertIsNone(b.dars_ol(100)); self.assertIsNone(b.dars_korinishi(100))


if __name__ == "__main__":
    unittest.main()


class VirtualDoskaVaTarix(unittest.TestCase):
    """REV565: dars matnidagi [[GRAFIK/INTEGRAL/BIRLIK_AYLANA/DOSKA]] qatorlari va ixtiyoriy MATEMATIKA TARIXI bo'limi."""

    @classmethod
    def setUpClass(cls):
        cls.md = open(NAMUNA, encoding="utf8").read()

    def test_vidjet_qatorlari(self):
        for tur, arg in [("GRAFIK", "a*x^2+b*x+c | a=1, b=-2, c=-3 | -4..6 | -5..8"), ("GRAFIK", "sin(x)"), ("INTEGRAL", "x^2 | 0..2 | -1..3 | -1..5"), ("INTEGRAL", "sin(x) | 0..3.1416"), ("BIRLIK_AYLANA", "45"), ("BIRLIK_AYLANA", ""), ("DOSKA", ""), ("GRAFIK", "y=2x+1")]:
            self.assertIsNone(D.vidjet_xatosi(tur, arg), (tur, arg))
        for tur, arg, soz in [("RASM", "x", "noma'lum"), ("GRAFIK", "", "ifoda"), ("GRAFIK", "x^2=4", "ifoda"), ("GRAFIK", "(x+1", "qavs"), ("GRAFIK", "a+b", "x yo'q"), ("GRAFIK", "x; alert(1)", "ifoda"), ("GRAFIK", "x^2 | 6..-4", "oraliq"),
                              ("GRAFIK", "a*x | a=1,5", "parametr"), ("INTEGRAL", "x^2", "chegaralari"), ("INTEGRAL", "x^2 | 2..0", "oraliq"), ("BIRLIK_AYLANA", "400", "0–360"), ("BIRLIK_AYLANA", "abc", "son"), ("GRAFIK", "x" * 130, "ifoda")]:
            self.assertIn(soz, D.vidjet_xatosi(tur, arg), (tur, arg))

    def test_darsdagi_vidjet_va_tarix(self):
        md = self.md.replace("## TUSHUNCHA\n", "## TUSHUNCHA\n[[GRAFIK: x^2 | -3..3]]\n", 1)
        self.assertEqual(ishla(md)[1], [])
        _, xato, _ = ishla(self.md.replace("## TUSHUNCHA\n", "## TUSHUNCHA\n[[GRAFIK: x^ 2= | -3..3]]\n", 1)); self.assertTrue(any("TUSHUNCHA" in x and "ifoda" in x for x in xato))
        _, xato, _ = ishla(self.md.replace("## TUSHUNCHA\n", "## TUSHUNCHA\n[[XYZ: x]]\n", 1)); self.assertTrue(any("noma'lum virtual doska" in x for x in xato))
        d, xato, _ = ishla(self.md.replace("## TUSHUNCHA\n", "## TUSHUNCHA\n\\[\\[GRAFIK: a\\*x^2 | a=1\\]\\]\n", 1)); self.assertEqual(xato, [])       # pandoc yozuvi (\[\[ … \]\], \*) ham qabul
        self.assertIn("rombos", d["darslar"]["100"]["tarix"])
        _, xato, _ = ishla(self.md.replace("## O'ZINI TEKSHIR", "## MATEMATIKA TARIXI\n" + "uzun gap. " * 200 + "\n\n## O'ZINI TEKSHIR") if "MATEMATIKA TARIXI" not in self.md else self.md.replace("## O'ZINI TEKSHIR", "uzun gap. " * 200 + "\n\n## O'ZINI TEKSHIR"))
        self.assertTrue(any("MATEMATIKA TARIXI" in x for x in xato))
        d0, xato0, _ = ishla(self.md.replace(self.md[self.md.index("## MATEMATIKA TARIXI"):self.md.index("## O'ZINI TEKSHIR")], ""))   # tarix ixtiyoriy
        self.assertEqual((xato0, d0["darslar"]["100"]["tarix"]), ([], ""))

    def test_haqiqiy_darslar_va_server(self):
        b = mb.bank_ol(); d = b.dars_korinishi(84)
        self.assertEqual([x["manba"] for x in d["misollar"]], ["97-3-31", "96-9-82", "97-1-62", "96-1-31", "97-2-49"])
        self.assertIn("Arximed", d["tarix"]); self.assertEqual(len(d["tekshir_ids"]), 4)
        vid = [q.strip() for t in d["tushuncha"] for q in t["matn"].split("\n") if q.strip().startswith("[[")]
        self.assertEqual(len(vid), 3)
        for q in vid:
            mv = D.VID_QATOR.match(q); self.assertIsNone(D.vidjet_xatosi(mv.group(1), mv.group(2)), q)
        self.assertIn("rombos", b.dars_korinishi(100)["tarix"])
