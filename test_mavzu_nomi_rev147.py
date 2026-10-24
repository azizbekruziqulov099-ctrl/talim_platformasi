"""REV147: maktab Mavzular Excel'ida «Kichik mavzu» to'ldirilgan — miya esa MAVZU nomini yozadi.

Oldin indeks faqat kichik mavzu nomi bo'yicha edi: «1. Tanishuv: ingliz tili» topilmay, 1–11-sinf
ingliz/nemis tili miyalarining hammasi «Mavzular bazasida topilmadi» bilan to'xtardi."""
import unittest

from modules.mavzu_nomi import baza_indeksi, kitob_guruhi, nom_norm, nomzodlar

MAKTAB = 7


def row(code, mavzu, kichik, grade="1", fan="INGLIZ TILI", scope=MAKTAB):
    return {"topic_code": code, "grade": grade, "subject_name": fan, "curriculum_scope_id": scope,
            "mavzu_name": mavzu, "nom": kichik or mavzu}


class MavzuNomiZaxiraTests(unittest.TestCase):
    def setUp(self):
        self.baza = baza_indeksi([
            row("1-01-1-01-01-001-001", "1. tanishuv: ingliz tili", "let's start english!"),
            row("1-01-1-01-02-002-001", "2. hi va bye", "hi! bye!"),
            row("1-01-1-01-02-003-001", "3. men - ali", "i'm ali"),
            # bitta mavzuning ikkita kichik mavzusi — nusxa emas
            row("1-01-1-01-02-004-001", "4. isming nima?", "what's your name?"),
            row("1-01-1-01-02-004-002", "4. isming nima?", "my name is ..."),
            # boshqa sinf va boshqa fan — ulanib ketmasin
            row("2-01-1-01-01-001-001", "1. tanishuv: ingliz tili", "hello again", grade="2"),
            row("1-02-1-01-01-001-001", "1. tanishuv: ingliz tili", "hallo!", fan="NEMIS TILI"),
        ])
        self.group, self.fan = kitob_guruhi("1-sinf"), nom_norm("Ingliz tili")

    def codes(self, nom):
        pick, _ = nomzodlar(self.baza, nom, self.fan, self.group)
        return sorted({r["topic_code"] for r in pick})

    def test_mavzu_name_found_when_kichik_filled(self):
        self.assertEqual(self.codes("1. Tanishuv: ingliz tili"), ["1-01-1-01-01-001-001"])
        self.assertEqual(self.codes("3. Men — Ali"), ["1-01-1-01-02-003-001"])

    def test_kichik_name_still_works(self):
        self.assertEqual(self.codes("Hi! Bye!"), ["1-01-1-01-02-002-001"])

    def test_several_kichik_under_one_mavzu_is_not_duplicate(self):
        self.assertEqual(self.codes("4. Isming nima?"), ["1-01-1-01-02-004-001"])

    def test_other_grade_and_subject_not_linked(self):
        pick, elsewhere = nomzodlar(self.baza, "1. Tanishuv: ingliz tili", self.fan, kitob_guruhi("3-sinf"))
        self.assertEqual(pick, [])
        self.assertTrue(elsewhere)


if __name__ == "__main__":
    unittest.main()
