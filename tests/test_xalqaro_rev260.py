"""REV260: Xalqaro baholash — kontent butunligi, javob tekshirish, TIMSS bali, imtihon rejasi, dars xonasi formati."""
import json
import os
import random
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import xalqaro_baholash as x  # noqa: E402

BAD_SVG = re.compile(r"<\s*(script|image|foreignObject|iframe|use)\b|on[a-z]+\s*=|href\s*=|url\s*\(", re.I)


class Kontent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.k = x.KONTENT.ensure()

    def test_hamma_toplam_va_mavzu_toliq(self):
        self.assertEqual(len(self.k.savollar), 337)
        for tk, tops in self.k.ramka["mavzular"].items():
            for t in tops:
                self.assertIn("XB-" + t["kalit"], self.k.dars_by_kod, t["kalit"])
                self.assertTrue(self.k.by_mavzu.get(t["kalit"]), f"{t['kalit']} da savol yo'q")

    def test_har_variant_togri_tuzilgan(self):
        for s in self.k.savollar:
            self.assertEqual(len(s["variantlar"]), 2, s["id"])
            self.assertIn(s["fikrlash"], ("bilish", "qollash", "mulohaza"))
            for v in s["variantlar"]:
                if v["turi"] == "tanlov":
                    self.assertEqual(len(v["javoblar"]), 4, s["id"])
                    self.assertIn(v["togri"], (0, 1, 2, 3))
                    self.assertTrue(x.tekshir(v, "ABCD"[v["togri"]]))
                    self.assertFalse(x.tekshir(v, "ABCD"[(v["togri"] + 1) % 4]))
                else:
                    self.assertTrue(x.tekshir(v, v["javob"].split("|")[0]), s["id"])
                self.assertTrue(v["yechim"])
                if v.get("rasm"):
                    self.assertFalse(BAD_SVG.search(v["rasm"]), s["id"])

    def test_dars_xonasi_formati(self):
        for kod in self.k.dars_by_kod:
            d = x.dars_payload(kod)
            self.assertTrue(d["steps"], kod)
            self.assertTrue(d["topic"]["fan"])
            for st in d["steps"]:
                lines = [ln for ln in st["doska"].split("\n") if ln.strip()]
                marks = re.findall(r"\[(\d{1,2})\]", st["ovoz"])
                if len(lines) > 1:
                    self.assertEqual([int(m) for m in marks], list(range(1, len(lines) + 1)), st["id"])
        self.assertIsNone(x.dars_payload("XB-YOQ-YOQ"))


class Qoidalar(unittest.TestCase):
    def test_ochiq_javob(self):
        self.assertTrue(x.tekshir_ochiq("3/4", "0,75"))
        self.assertTrue(x.tekshir_ochiq("0.75", "3/4|0,75"))
        self.assertTrue(x.tekshir_ochiq("12 ta", "12"))
        self.assertTrue(x.tekshir_ochiq("Fotosintez", "fotosintez"))
        self.assertFalse(x.tekshir_ochiq("13", "12"))
        self.assertFalse(x.tekshir_ochiq("", "12"))

    def test_timss_bali(self):
        self.assertEqual(x.timss_ball([(x.qiyinlik(p), i % 2 == 0) for i, p in enumerate([40, 50, 60] * 4)])[0], 500)
        hammasi = x.timss_ball([(x.qiyinlik(50), True)] * 20)[0]
        hech = x.timss_ball([(x.qiyinlik(50), False)] * 20)[0]
        self.assertGreater(hammasi, 625)
        self.assertLess(hech, 400)
        self.assertEqual(x.daraja_of(560)["kalit"], "yuqori")

    def test_imtihon_rejasi_ramkaga_mos(self):
        k = x.KONTENT.ensure()
        pool = [s for s in k.savollar if s["toplam"] == "T11_G8_M"]
        t = x.reja_boyicha_tanla(pool, 30, x.REJA["T11_G8_M"], random.Random(1))
        self.assertEqual(len({s["id"] for s in t}), 30)
        soni = {so: sum(1 for s in t if s["soha"] == so) for so in ("son", "algebra", "geometriya", "malumot")}
        self.assertEqual(soni, {"son": 9, "algebra": 9, "geometriya": 6, "malumot": 6})

    def test_davrlar(self):
        from datetime import date
        self.assertEqual(x.davr_kaliti("haftalik", date(2026, 11, 3)), "2026-H45")
        self.assertEqual(x.davr_kaliti("choraklik", date(2026, 11, 3)), "2026-2027-C2")
        self.assertEqual(x.davr_kaliti("choraklik", date(2027, 2, 1)), "2026-2027-C3")
        self.assertEqual(x.davr_kaliti("yillik", date(2027, 5, 20)), "2026-2027")
        self.assertEqual(x.davr_oxiri("haftalik", date(2026, 11, 3)), date(2026, 11, 8))

    def test_davlatlar(self):
        k = x.KONTENT.ensure()
        r = x.davlatlar_bilan(480, k.natijalar["jadvallar"]["TIMSS 2023 M8"])
        self.assertEqual(r["ozbekiston"], 421)
        self.assertEqual(r["eng_yuqori"][0], "Singapur")


if __name__ == "__main__":
    unittest.main()
