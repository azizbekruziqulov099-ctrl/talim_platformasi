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
        self.assertEqual(sum(1 for s in self.k.savollar if not s.get("birlik")), 337)   # TIMSS
        self.assertGreater(sum(1 for s in self.k.savollar if s.get("birlik")), 250)   # PISA (REV262)
        for tk, tops in self.k.ramka["mavzular"].items():
            for t in tops:
                self.assertIn("XB-" + t["kalit"], self.k.dars_by_kod, t["kalit"])
                self.assertTrue(self.k.by_mavzu.get(t["kalit"]), f"{t['kalit']} da savol yo'q")

    def test_har_variant_togri_tuzilgan(self):
        for s in self.k.savollar:
            self.assertEqual(len(s["variantlar"]), 1 if s.get("birlik") else 2, s["id"])
            if s.get("birlik"):
                self.assertIn(s["birlik"], self.k.birliklar)
                self.assertTrue(200 <= s["qiyinlik_ball"] <= 850)
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


class Pisa(unittest.TestCase):
    def test_pisa_darajalar_va_qiyinlik(self):
        self.assertTrue(x.daraja_of(430, "P_M")["tayanch"])
        self.assertFalse(x.daraja_of(400, "P_M")["tayanch"])
        self.assertEqual(x.daraja_of(700, "P_R")["nom"], "6-daraja")
        # PISA bali 500 bo'lgan savolni 500 balli o'quvchi 62% ehtimol bilan yechadi
        import math
        b = x.savol_qiyinligi({"qiyinlik_ball": 500})
        self.assertAlmostEqual(1 / (1 + math.exp(b)), 0.62, places=2)
        self.assertEqual(x.tavsiya_toplamlar(9), ["P_M", "P_R", "P_S", "P_F"])
        self.assertEqual(x.band_of("P_S"), "P")

    def test_birlik_savollari_ketma_ket(self):
        k = x.KONTENT.ensure()
        pool = [s for s in k.savollar if s["toplam"] == "P_M"]
        t = x.reja_boyicha_tanla(pool, 16, x.REJA["P_M"], random.Random(5))
        birliklar = [s["birlik"] for s in t]
        for b in set(birliklar):
            idx = [i for i, v in enumerate(birliklar) if v == b]
            self.assertEqual(idx, list(range(idx[0], idx[-1] + 1)), b)   # bir birlik savollari uzilmaydi


class Tillar(unittest.TestCase):
    """REV270: uch til — kontent tuzilishi bir xil, javob kalitlari bir xil, natijalar alohida."""

    def test_til_kodi(self):
        self.assertEqual(x.til_kodi("ru-RU"), "ru")
        self.assertEqual(x.til_kodi("en"), "en")
        self.assertEqual(x.til_kodi("uz-Cyrl"), "uz")
        self.assertEqual(x.til_kodi("tr"), "uz")
        self.assertEqual(x.til_kodi(None), "uz")

    def test_tarjima_tuzilishi_va_kalitlar(self):
        uz = x.KONTENT.ensure()
        for til in ("ru", "en"):
            k = x.kontent_of(til)
            for s in k.savollar:
                a = uz.by_id[s["id"]]
                self.assertEqual((s["toplam"], s["mavzu"], s["fikrlash"], len(s["variantlar"])), (a["toplam"], a["mavzu"], a["fikrlash"], len(a["variantlar"])), s["id"])
                for v, w in zip(s["variantlar"], a["variantlar"]):
                    self.assertEqual(v["turi"], w["turi"], s["id"])
                    if v["turi"] == "tanlov":
                        self.assertEqual(v["togri"], w["togri"], s["id"])
                        self.assertEqual(len(v["javoblar"]), 4, s["id"])
                    else:
                        self.assertTrue(x.tekshir(v, v["javob"].split("|")[0]), s["id"])
                        n = x._as_number(x._norm(w["javob"].split("|")[0]))
                        if n is not None:   # son javob — tarjimada ham shu son qabul qilinadi
                            self.assertTrue(x.tekshir(v, w["javob"].split("|")[0]), (til, s["id"]))
                    self.assertEqual(len(v.get("yechim") or []), len(w.get("yechim") or []), s["id"])
                    if v.get("rasm"):
                        self.assertFalse(BAD_SVG.search(v["rasm"]), s["id"])
            # to'plam faqat to'liq bo'lsa chiqadi: barcha mavzularda savol va dars bor
            for tk, tops in k.ramka["mavzular"].items():
                for t in tops:
                    self.assertIn("XB-" + t["kalit"], k.dars_by_kod, (til, t["kalit"]))
                    self.assertTrue(k.by_mavzu.get(t["kalit"]), (til, t["kalit"]))
                    self.assertEqual(len(k.by_mavzu[t["kalit"]]), len(uz.by_mavzu[t["kalit"]]), (til, t["kalit"]))

    def test_ruscha_matn_ruscha(self):
        k = x.kontent_of("ru")
        if not k.savollar:
            self.skipTest("ruscha kontent yo'q")
        matnli = [s for s in k.savollar if re.search(r"[a-zʻ‘]{3,}", re.sub(r"\$[^$]*\$", "", x.KONTENT.ensure().by_id[s["id"]]["variantlar"][0]["savol"]))]
        kir = sum(1 for s in matnli if re.search("[а-яё]", s["variantlar"][0]["savol"].lower()))
        self.assertEqual(kir, len(matnli))
        d = x.dars_payload("XB-M8-KAS", til="ru")
        self.assertEqual(d["til"], "ru")
        self.assertRegex(d["steps"][0]["doska"] + d["steps"][0]["ovoz"], "[а-яё]")

    def test_daraja_va_davlat_nomlari(self):
        self.assertEqual(x.daraja_of(560, til="ru")["nom"], "Высокий")
        self.assertEqual(x.daraja_of(380, til="en")["nom"], "Below Low")
        p = x.daraja_of(430, "P_M", til="en")
        self.assertTrue(p["tayanch"])
        self.assertIn("2", p["nom"])
        n = x.natijalar_tilda(x.DATA_DIR, "ru")
        self.assertEqual(n["uz_nomi"], "Узбекистан")
        self.assertTrue(any(r[0] == "Узбекистан" for r in n["jadvallar"]["TIMSS 2023 M8"]))
        self.assertEqual(x.imtihon_nomi("haftalik", "en"), "Weekly check")


if __name__ == "__main__":
    unittest.main()
