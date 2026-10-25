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


class Rev166Tests(unittest.TestCase):
    def test_levels(self):
        self.assertEqual(b.yulduz_darajasi(0)["nom"], "Tuxumcha")
        d = b.yulduz_darajasi(12)
        self.assertEqual((d["emoji"], d["gacha"], d["qoldi"], d["keyingi"]["nom"]), ("🐣", 15, 3, "Polapon"))
        self.assertEqual(b.yulduz_darajasi(660)["nom"], "Bilimdon")
        top = b.yulduz_darajasi(1100)
        self.assertEqual((top["daraja"], top["dan"], top["gacha"]), (15, 1060, 1260))
        self.assertTrue(0 <= top["foiz"] <= 100)
        self.assertEqual(b.yulduz_darajasi(-4)["yulduz"], 0)

    def test_streak(self):
        sat, sun, mon = date(2026, 10, 24), date(2026, 10, 25), date(2026, 10, 26)
        fri, thu = date(2026, 10, 23), date(2026, 10, 22)
        self.assertEqual(b.ketma_ket([thu, fri, sat], mon), 3)          # yakshanba dam — zanjir uzilmaydi, bugun hali dars yo'q
        self.assertEqual(b.ketma_ket([thu, fri, sat, mon], mon), 4)
        self.assertEqual(b.ketma_ket([thu, sat], sat), 1)                # juma o'tkazib yuborildi
        self.assertEqual(b.ketma_ket([], mon), 0)

    def test_diary_weeks(self):
        today = date(2026, 10, 21)   # chorshanba
        rows = [{"sana": "2026-10-19", "fan": "Ingliz tili", "mavzu": "Salom", "tugadi": "10:00", "yulduz": 3, "ai_baho": {"baho": 5}},
                {"sana": "2026-10-21", "fan": "Matematika", "mavzu": "Bir", "tugadi": None, "yulduz": 0},
                {"sana": "2026-10-13", "fan": "Rus tili", "mavzu": "Привет", "tugadi": "09:00", "yulduz": 2}]
        hafta = [["en", "mat"], ["ru"], ["en", "mat"], ["ru"], ["en"], ["ru", "mat"], []]
        w = b.kundalik_haftalari(rows, hafta, today)
        shu, otgan = w
        self.assertEqual([k["holat"] for k in shu["kunlar"]][:4], ["otdi", "otdi", "bugun", "keladi"])
        self.assertEqual(shu["kunlar"][0]["darslar"][0], {"kalit": "en", "fan": "Ingliz tili", "mavzu": "Salom", "tugadi": True, "yulduz": 3, "baho": 5,
                                                         "sozlar": [], "togri": None, "jami": None})
        self.assertEqual(shu["kunlar"][2]["darslar"][0]["yulduz"], 0)
        self.assertEqual((shu["yulduz"], shu["darslar"], otgan["yulduz"], otgan["darslar"]), (3, 1, 2, 1))
        self.assertEqual(otgan["kunlar"][1]["rejada"], [])
        self.assertEqual(b.kundalik_haftalari([], None, today)[0]["kunlar"][0]["rejada"], [])

    def test_day_summary(self):
        rows = [{"mavzu": "Salom", "tugadi": "10:00", "yulduz": 3, "sozlar": [{"soz": "cat", "aytdi": False}, {"soz": "dog", "aytdi": True}]},
                {"mavzu": "Ranglar", "tugadi": "11:00", "yulduz": 1, "sozlar": [{"soz": "Cat", "aytdi": True}, {"soz": "red", "aytdi": False}]},
                {"mavzu": "Bir", "tugadi": None, "sozlar": []}]
        x = b.kun_xulosasi(rows)
        self.assertEqual(x["organdi"], ["Salom", "Ranglar"])
        self.assertEqual(x["takror_soz"], ["red"])                     # cat boshqa darsda to'g'ri aytildi
        self.assertEqual(x["takror_dars"], ["Ranglar"])
        self.assertEqual(x["chala"], ["Bir"])
        self.assertEqual(b.ertangi_fanlar([["en"], ["ru"], [], [], [], ["mat"], []], 5), [])
        self.assertEqual(b.ertangi_fanlar([["en"], ["ru"], [], [], [], ["mat"], []], 6), ["en"])
        self.assertIsNone(b.ertangi_fanlar(None, 1))


class Rev167Tests(unittest.TestCase):
    def test_night_lock(self):
        from datetime import datetime as dt
        t = b.tun_sozlama({})
        self.assertEqual((t["kun"], t["shanba"], t["ertalab"]), (22, 23, 6))
        self.assertFalse(b.tun_holati(dt(2026, 10, 19, 21, 59), t)["yopiq"])     # dushanba 21:59
        self.assertTrue(b.tun_holati(dt(2026, 10, 19, 22, 0), t)["yopiq"])       # dushanba 22:00
        self.assertFalse(b.tun_holati(dt(2026, 10, 24, 22, 30), t)["yopiq"])     # shanba 22:30 — ochiq
        self.assertTrue(b.tun_holati(dt(2026, 10, 24, 23, 0), t)["yopiq"])       # shanba 23:00
        self.assertTrue(b.tun_holati(dt(2026, 10, 25, 2, 0), t)["yopiq"])        # yakshanba tungi 2:00
        self.assertTrue(b.tun_holati(dt(2026, 10, 20, 5, 59), t)["yopiq"])
        self.assertFalse(b.tun_holati(dt(2026, 10, 20, 6, 0), t)["yopiq"])
        self.assertFalse(b.tun_holati(dt(2026, 10, 19, 23, 0), {"yoqilgan": False})["yopiq"])
        self.assertEqual(b.tun_sozlama({"kun": 99, "ertalab": "x"})["kun"], 24)

    def test_discounts(self):
        self.assertEqual(b.chegirmali_narx(99000, 0), 99000)
        self.assertEqual(b.chegirmali_narx(99000, 15), 84200)
        self.assertEqual(b.chegirmali_narx(99000, 100), 0)
        self.assertEqual(b.chegirma_tanla(True, [], 1, {})["sabab"], "admin")
        c = b.chegirma_tanla(False, [{"foiz": 10, "izoh": "x"}], 2, {"2": 20, "3": 30})
        self.assertEqual((c["foiz"], c["sabab"]), (20, "oila"))              # eng kattasi, qo'shilmaydi
        self.assertEqual(b.chegirma_tanla(False, [], 4, {"2": 20, "3": 30})["foiz"], 30)
        self.assertEqual(b.chegirma_tanla(False, [], 1, {"2": 20})["foiz"], 0)
        self.assertEqual(b.oila_chegirma_sozlama({"2": 150, "3": "a"}), {"2": 100, "3": 0})


class Rev168Tests(unittest.TestCase):
    def test_trial_lessons(self):
        q = b.yosh_qoidasi(3)
        r = b.haftalik_reja(["en"], q)
        h = {"obuna_kerak": False, "reja": r, "kvota": b.bugungi_kvota(r, 1, {}, {}), "sinov": {"ru": 2, "ar": 0}}
        tue, sun = date(2026, 10, 20), date(2026, 10, 25)
        self.assertEqual(b.boshlash_xatosi(h, "Rus tili", tue), "")             # sinov darsi ochiladi
        self.assertIsNone(b.boshlash_sababi(h, "Rus tili", tue))
        self.assertIn("rejasida yo", b.boshlash_xatosi(h, "Arab tili", tue))    # sinov tugagan
        self.assertIn("yakshanba", b.boshlash_xatosi(h, "Rus tili", sun))       # yakshanba — faqat takror
        ob = {"obuna_kerak": True, "reja": r, "kvota": {}, "sinov": {"ru": 1}}
        self.assertEqual(b.boshlash_xatosi(ob, "Rus tili", tue), "")
        self.assertIn("kurs tanlashi", b.boshlash_xatosi(ob, "Nemis tili", tue))
        self.assertEqual(b.sinov_dars_soni(None), 4)
        self.assertEqual(b.sinov_dars_soni(99), 10)
