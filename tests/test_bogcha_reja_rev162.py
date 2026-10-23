"""REV162: aqlli haftalik reja, narx qulfi, tanlov chegaralari va AI kundalik bahosi — sof mantiq."""
import unittest
from datetime import date

from modules import bogcha_reja as b

LANGS = ["en", "ru", "de", "fr", "es", "ar", "tr", "ko", "ja", "zh"]
FANS = ["mat", "man", "olam", "ona"]


class RejaTests(unittest.TestCase):
    def test_every_age_and_mix_fits_rules(self):
        for age in range(2, 8):
            q = b.yosh_qoidasi(age)
            for nl in range(8):
                for nf in range(5):
                    for sel in (LANGS[:nl] + FANS[:nf], FANS[:nf] + LANGS[:nl]):
                        if not sel:
                            continue
                        r = b.haftalik_reja(sel, q)
                        self.assertLessEqual(len(r["faol"]), q["jami"])
                        self.assertLessEqual(sum(1 for k in r["faol"] if b.KURS[k]["turi"] == "til"), q["til"])
                        self.assertEqual(r["hafta"][6], [])                       # yakshanba — takror
                        for d in range(6):
                            self.assertLessEqual(len(r["hafta"][d]), r["sigim"][d])
                            self.assertEqual(len(set(r["hafta"][d])), len(r["hafta"][d]))   # kuniga bitta fandan bitta
                        for k in r["faol"]:
                            self.assertGreaterEqual(r["haftalik"][k], 2, (age, sel, r["haftalik"]))
                            self.assertLessEqual(r["haftalik"][k], 3)

    def test_examples_from_parents(self):
        q = b.yosh_qoidasi(2)
        one = b.haftalik_reja(["en"], q)["hafta"]
        self.assertEqual([d for d in range(7) if one[d]], [0, 2, 4])                  # kun ora
        two = b.haftalik_reja(["en", "ru"], q)["hafta"]
        self.assertTrue(all(len(two[d]) == 1 for d in range(6)))                     # har kuni bittadan
        four = b.haftalik_reja(["en", "ru", "de", "fr"], q)["hafta"]
        self.assertTrue(all(len(four[d]) == 2 for d in range(6)))                    # kuniga ikkitadan
        many = b.haftalik_reja(LANGS[:4] + FANS[:3], q)
        self.assertEqual(len(many["faol"]), 5)
        self.assertEqual(len(many["navbat"]), 2)                                      # «avval bitta tilni tugatsin»

    def test_quota_catch_up_and_sunday(self):
        q = b.yosh_qoidasi(2)
        r = b.haftalik_reja(["en", "ru", "mat"], q)
        mon = b.bugungi_kvota(r, 0, {}, {})
        self.assertEqual(sum(mon.values()), len(r["hafta"][0]))
        # dushanba o'tkazib yuborildi — seshanba qarz dars sig'imga qarab ochiladi
        tue = b.bugungi_kvota(r, 1, {}, {})
        self.assertGreater(sum(tue.values()), len(r["hafta"][1]) - 1)
        self.assertLessEqual(sum(tue.values()), r["sigim"][1])
        self.assertEqual(sum(b.bugungi_kvota(r, 6, {}, {}).values()), 0)
        # haftalik me'yor bajarilgan fan — qo'shimcha dars yo'q
        full = {k: r["haftalik"][k] for k in r["faol"]}
        self.assertEqual(sum(b.bugungi_kvota(r, 5, full, {}).values()), 0)

    def test_start_messages(self):
        q = b.yosh_qoidasi(3)
        r = b.haftalik_reja(["en"], q)
        h = {"obuna_kerak": False, "reja": r, "kvota": b.bugungi_kvota(r, 1, {"en": 1}, {})}
        self.assertIn("Keyingi dars", b.boshlash_xatosi(h, "Ingliz tili", date(2026, 10, 20)))
        self.assertIn("yakshanba", b.boshlash_xatosi(h, "Ingliz tili", date(2026, 10, 25)))
        self.assertIn("rejasida yo", b.boshlash_xatosi(h, "Rus tili", date(2026, 10, 20)))
        self.assertEqual(b.boshlash_xatosi(None, "Rus tili", date(2026, 10, 20)), "")


class NarxTests(unittest.TestCase):
    def test_locked_price_for_old_subscriber(self):
        t = {"id": 2, "narx_uzs": 150000}
        old = {"tarif_id": 2, "narx_uzs": 99000, "narx_qulf_gacha": date(2028, 10, 19)}
        self.assertEqual(b.narx_hisobla(t, old, date(2027, 1, 1))["narx"], 99000)
        self.assertEqual(b.narx_hisobla(t, old, date(2028, 10, 20))["narx"], 150000)   # qulf tugadi
        self.assertEqual(b.narx_hisobla(t, None, date(2027, 1, 1))["narx"], 150000)
        self.assertEqual(b.narx_hisobla({"id": 3, "narx_uzs": 5}, old, date(2027, 1, 1))["narx"], 5)

    def test_choice_limits(self):
        q2 = b.yosh_qoidasi(2)
        self.assertEqual(b.tanlov_xatosi(["en", "ru"], {"kurs_soni": 4}, q2), "")
        self.assertIn("ta kurs", b.tanlov_xatosi(LANGS[:5], {"kurs_soni": 4}, q2))
        self.assertIn("avval farzandingiz bitta tilni tugatsin", b.tanlov_xatosi(LANGS[:5], {"kurs_soni": 0}, q2))
        self.assertEqual(b.tarif_kurs_soni({"kurs_soni": 0}, b.yosh_qoidasi(6)), 10)


class BahoTests(unittest.TestCase):
    def test_grade_parts(self):
        a = b.ai_baho({"togri": 5, "jami": 5, "ovoz_togri": 4, "ovoz_jami": 4, "javob_ms": 3000, "tugadi": True}, "4-5 yosh")
        self.assertEqual(a["baho"], 5)
        w = b.ai_baho({"togri": 1, "jami": 5, "sozlar": [{"soz": "cat", "aytdi": False}], "javob_ms": 20000, "tugadi": True,
                       "chalgish": 4}, "2-3 yosh")
        self.assertEqual(w["baho"], 2)
        self.assertIsNone(b.ai_baho({"tugadi": True})["qism"]["aniqlik"])
        day = b.kun_bahosi([{"ai_baho": a, "tugadi": "10:00"}, {"ai_baho": w, "tugadi": "11:00"}, {"ai_baho": None, "tugadi": None}])
        self.assertEqual(day["darslar"], 2)

    def test_fan_key(self):
        self.assertEqual(b.fan_kaliti("Ingliz tili (izoh: rus)"), "en")
        self.assertEqual(b.fan_kaliti("Rus tili"), "ru")
        self.assertEqual(b.fan_kaliti("Arab tili (izoh: rus)"), "ar")
        self.assertEqual(b.fan_kaliti("Matematika"), "mat")
        self.assertEqual(b.fan_kaliti("Atrof-olam"), "olam")
        self.assertEqual(b.fan_kaliti("Rasm"), "")


if __name__ == "__main__":
    unittest.main()


class Rev163Tests(unittest.TestCase):
    def test_course_bound_tariff(self):
        q = b.yosh_qoidasi(4)
        t = {"kurs_soni": 3, "kurslar": ["zh", "ja"]}
        self.assertEqual(b.tarif_kurs_soni(t, q), 2)
        self.assertEqual(b.tanlov_xatosi(["zh"], t, q), "")
        self.assertEqual(b.tanlov_kodi(["en"], t, q), "tanlov_tarif_kursi")
        self.assertIn("faqat shu kurslar", b.tanlov_xatosi(["en"], t, q))
        self.assertEqual(b.tanlov_kodi([], t, q), "tanlov_bosh")

    def test_price_lock_never_more_than_current(self):
        old = {"tarif_id": 2, "narx_uzs": 99000, "narx_qulf_gacha": date(2028, 1, 1)}
        self.assertEqual(b.narx_hisobla({"id": 2, "narx_uzs": 50000}, old, date(2027, 1, 1))["narx"], 50000)

    def test_tiny_capacity_moves_courses_to_queue(self):
        r = b.haftalik_reja(LANGS[:7] + ["mat"], {"kun": 1, "shanba": 1, "jami": 10, "til": 7, "yosh": 5})
        self.assertTrue(all(r["haftalik"][k] >= 1 for k in r["faol"]))
        self.assertEqual(len(r["faol"]) + len(r["navbat"]), 8)
