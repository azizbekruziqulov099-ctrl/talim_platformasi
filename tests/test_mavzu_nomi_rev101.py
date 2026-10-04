"""REV101: kitob mavzu nomi → kod. Boshqa yosh guruhi / boshqa til mavzusiga ulanmaydi, ikki blokdagi nusxa import'ni to'xtatmaydi."""
import unittest

from modules.mavzu_nomi import (baza_indeksi, boshqa_joylar, kitob_guruhi, kod_qismlari, nom_norm, nomzodlar,
                                nusxadan_tanla)

BOGCHA = 5  # «Bog'cha — umumiy katalog» dasturi
KITOB_67 = [
    "O'tgan yilni eslaymiz", "O'n bir va o'n ikki", "O'n beshdan o'n yettigacha", "Yigirmagacha sanaymiz",
    "Nechta ekan?", "Do'konda: tuxum sanaymiz", "1-bo'lim takrori: Sanoq 11–20",
] + [f"{i}-dars" for i in range(8, 34)] + [
    "Hayvonlar nima qila oladi?", "Yordam berasanmi?", "Sport kuni", "6-bo'lim takrori: Qila olasanmi?",
] + [f"{i}-mashg'ulot" for i in range(38, 62)] + ["Katta bayram: hammasini takrorlaymiz"]


def row(code, grade, fan, nom, scope=BOGCHA):
    return {"topic_code": code, "grade": grade, "subject_name": fan, "nom": nom, "curriculum_scope_id": scope}


def hozirgi_baza():
    """Foydalanuvchi bazasi (xatolardan tiklangan): 34–62-darslar 6-7 yoshda 1- va 3-blokda ikki nusxa,
    1–33 yo'q, «O'tgan yilni eslaymiz» faqat 4-5 yoshda (Ingliz va Rus tilida)."""
    rows = [row("4-5 yosh-01-01-01-01-01-001", "4-5 yosh", "INGLIZ TILI", "o'tgan yilni eslaymiz"),
            row("4-5 yosh-02-01-01-01-01-001", "4-5 yosh", "RUS TILI", "o'tgan yilni eslaymiz")]
    for n, nom in enumerate(KITOB_67[33:], 1):
        for blok in ("01", "03"):
            rows.append(row(f"6-7 yosh-01-{blok}-01-01-{n:02d}-001", "6-7 yosh", "INGLIZ TILI", nom.lower()))
    return rows


def kitob_tekshir(rows, nomlar, fan="Ingliz tili", sinf="6-7 yosh"):
    """samtm_platform._ai_brain_nom_boyicha_kod bilan bir xil oqim (bazasiz)."""
    baza = baza_indeksi(rows)
    group, fan_n = kitob_guruhi(sinf), nom_norm(fan)
    pending = {f"@@NOM{i}@@": {"nom": nom, "raqam": i} for i, nom in enumerate(nomlar, 1)}
    replace, ambiguous, missing, meta = {}, {}, {}, {}
    for key, info in pending.items():
        pick, elsewhere = nomzodlar(baza, info["nom"], fan_n, group)
        meta.update({r["topic_code"]: r for r in pick})
        codes = sorted({r["topic_code"] for r in pick})
        if len(codes) == 1:
            replace[key] = codes[0]
        elif codes:
            ambiguous[key] = codes
        else:
            missing[key] = elsewhere
    chosen = nusxadan_tanla(ambiguous, pending, replace, {}, meta)
    left = {k: v for k, v in ambiguous.items() if k not in chosen}
    replace.update({k: v[0] for k, v in chosen.items()})
    return pending, replace, left, missing


class GuruhVaNomTests(unittest.TestCase):
    def test_book_group_and_name_keys(self):
        self.assertEqual(kitob_guruhi("6–7 yosh"), "6-7 yosh")
        self.assertEqual(kitob_guruhi("6-7"), "6-7 yosh")
        self.assertEqual(kitob_guruhi("5-sinf"), "5")
        self.assertEqual(kitob_guruhi("2 kurs"), "2 kurs")
        self.assertEqual(kitob_guruhi(""), "")
        self.assertEqual(nom_norm("O‘n bir va o‘n ikki"), nom_norm("o'n bir va o'n ikki"))
        self.assertEqual(nom_norm("1-bo'lim takrori: Sanoq 11–20"), nom_norm("1-bo‘lim takrori: sanoq 11-20"))
        self.assertEqual(kod_qismlari("6-7 yosh-01-03-01-01-29-001"), ("6-7 yosh-01-03-01-01", 29))


class FoydalanuvchiHolatiTests(unittest.TestCase):
    def test_current_database_gives_clear_errors_and_resolves_duplicates(self):
        pending, replace, left, missing = kitob_tekshir(hozirgi_baza(), KITOB_67)
        # 1–33: 6-7 yosh Ingliz tilida yo'q. «O'tgan yilni eslaymiz» endi 4-5 yoshga ulanmaydi.
        self.assertEqual(len(missing), 33)
        first = missing["@@NOM1@@"]
        self.assertIn("4-5 yosh · INGLIZ TILI", boshqa_joylar(first))
        self.assertEqual(missing["@@NOM2@@"], [])
        # 34–62: ikki nusxa (1- va 3-blok) — hammasi bitta (1-) blokka ulanadi, xato emas.
        self.assertEqual(left, {})
        tanlangan = [replace[f"@@NOM{i}@@"] for i in range(34, 63)]
        self.assertTrue(all(code.startswith("6-7 yosh-01-01-01-01-") for code in tanlangan))
        self.assertEqual(len(set(tanlangan)), 29)

    def test_after_clean_recreate_in_block_two_everything_resolves(self):
        rows = [r for r in hozirgi_baza() if not r["grade"] == "6-7 yosh"]   # eski nusxalar o'chirildi
        rows += [row(f"6-7 yosh-01-02-01-01-{n:02d}-001", "6-7 yosh", "INGLIZ TILI", nom.lower())
                 for n, nom in enumerate(KITOB_67, 1)]
        pending, replace, left, missing = kitob_tekshir(rows, KITOB_67)
        self.assertEqual((missing, left), ({}, {}))
        self.assertEqual(replace["@@NOM1@@"], "6-7 yosh-01-02-01-01-01-001")
        self.assertEqual(replace["@@NOM62@@"], "6-7 yosh-01-02-01-01-62-001")


class XavfsizlikTests(unittest.TestCase):
    def test_other_language_book_never_attaches_to_english_topics(self):
        rows = [row(f"6-7 yosh-01-01-01-01-{n:02d}-001", "6-7 yosh", "INGLIZ TILI", nom.lower())
                for n, nom in enumerate(KITOB_67, 1)]
        _, replace, left, missing = kitob_tekshir(rows, KITOB_67[:5], fan="Rus tili")
        self.assertEqual((replace, left, len(missing)), ({}, {}, 5))

    def test_older_group_topic_is_not_used_even_if_unique(self):
        rows = [row("4-5 yosh-01-01-01-01-62-001", "4-5 yosh", "INGLIZ TILI", "katta bayram: hammasini takrorlaymiz")]
        _, replace, _, missing = kitob_tekshir(rows, ["Katta bayram: hammasini takrorlaymiz"])
        self.assertEqual(replace, {})
        self.assertEqual(len(missing), 1)

    def test_school_subject_named_differently_still_found_inside_grade(self):
        rows = [row("5-07-01-01-01-01-001", "5", "ONA TILI VA O'QISH SAVODXONLIGI", "ot", scope=1),
                row("6-07-01-01-01-01-001", "6", "ONA TILI", "ot", scope=1)]
        _, replace, _, _ = kitob_tekshir(rows, ["Ot"], fan="Ona tili", sinf="5")
        self.assertEqual(replace, {"@@NOM1@@": "5-07-01-01-01-01-001"})

    def test_school_book_subject_exists_so_other_subject_is_not_used(self):
        rows = [row("5-01-01-01-01-01-001", "5", "MATEMATIKA", "kasrlar", scope=1),
                row("5-07-01-01-01-09-001", "5", "ONA TILI", "takrorlash", scope=1)]
        _, replace, _, missing = kitob_tekshir(rows, ["Takrorlash"], fan="Matematika", sinf="5")
        self.assertEqual((replace, len(missing)), ({}, 1))

    def test_unknown_book_grade_keeps_old_search(self):
        rows = [row("Abituriyent-01-01-01-01-01-001", "Abituriyent", "MATEMATIKA", "tenglamalar", scope=9)]
        _, replace, _, _ = kitob_tekshir(rows, ["Tenglamalar"], fan="Algebra", sinf="Tayyorlov")
        self.assertEqual(replace, {"@@NOM1@@": "Abituriyent-01-01-01-01-01-001"})

    def test_name_used_twice_in_book_is_not_guessed(self):
        rows = [row("5-01-01-01-01-09-001", "5", "MATEMATIKA", "takrorlash", scope=1),
                row("5-01-02-01-01-09-001", "5", "MATEMATIKA", "takrorlash", scope=1)]
        _, replace, left, _ = kitob_tekshir(rows, ["Takrorlash", "Takrorlash"], fan="Matematika", sinf="5")
        self.assertEqual(replace, {})
        self.assertEqual(len(left), 2)

    def test_copies_in_different_programs_are_not_guessed(self):
        rows = [row("6-7 yosh-01-01-01-01-01-001", "6-7 yosh", "INGLIZ TILI", "menda bor", scope=BOGCHA),
                row("6-7 yosh-02-01-01-01-01-001", "6-7 yosh", "INGLIZ TILI", "menda bor", scope=77)]
        _, replace, left, _ = kitob_tekshir(rows, ["Menda bor"])
        self.assertEqual((replace, len(left)), ({}, 1))


if __name__ == "__main__":
    unittest.main()
