import unittest

from modules.dars_xonasi import build_lesson, _split_solution


def unit(code, kind, **payload):
    return {"unit_code": code, "unit_kind": kind, "title": payload.pop("title", ""), "body": payload.pop("body", ""), "payload": payload}


TOPIC = {"topic_code": "5-01", "mavzu": "Oddiy kasr"}


class DarsXonasiTests(unittest.TestCase):
    def test_scenario_steps_are_ordered_and_variants_attach_to_step(self):
        units = [
            unit("S2", "lesson_step", tartib="2", qadam_turi="qoida", doska_matni="$\\frac{a}{b}$", ovoz_matni="Qoida"),
            unit("S1", "lesson_step", tartib="1", qadam_turi="kirish", doska_matni="Pitsa", ovoz_matni="Salom", media_id="p.png"),
            unit("V1", "variant", step_id="S2", variant_turi="hikoya", ovoz_matni="Hikoya"),
            unit("V2", "variant", step_id="S2", variant_turi="sodda", ovoz_matni="Sodda"),
            unit("T1", "task", vazifa_turi="single_choice", savol="2/6?", variant_a="a", variant_b="b", variant_c="c", variant_d="d", togri_javob="B"),
        ]
        lesson = build_lesson(TOPIC, units, lambda m: f"/m/{m}" if m else None)
        self.assertFalse(lesson["auto"])
        self.assertEqual([s["id"] for s in lesson["steps"]], ["S1", "S2"])
        self.assertEqual(lesson["steps"][0]["rasm"], "/m/p.png")
        self.assertEqual([v["turi"] for v in lesson["variants"]["S2"]], ["sodda", "hikoya"])
        self.assertEqual(lesson["savollar"][0]["togri"], 1)

    def test_old_upload_without_scenario_builds_lesson_automatically(self):
        units = [
            unit("B1", "knowledge", title="Kasr nima?", body="Butun teng bo'laklarga bo'linadi.", formula_latex="\\frac{a}{b}", qisqa_xulosa="Kasr — teng ulush."),
            unit("E1", "explanation", uslub="hayotiy", kirish_savoli="Pitsa 4 bo'lakka bo'linsa?", tushuntirish="Pastdagi son jami.", tekshiruv_savoli="3/4 da nechta?", kutilgan_javob="3"),
            unit("E2", "explanation", uslub="ko'rgazmali", tushuntirish="Doira rasmi."),
            unit("M1", "example", shart="8 dan 3 bo'yalgan", yechim_qadamlar="1) Maxrajga 8. 2) Suratga 3.", yakuniy_javob="3/8"),
            unit("Y1", "support", qayta_tushuntirish="Surat — olingan."),
        ]
        lesson = build_lesson(TOPIC, units, lambda m: None, [{"id": "t", "savol": "Q", "variantlar": list("abcd"), "togri": 0, "izoh": ""}])
        self.assertTrue(lesson["auto"])
        kinds = [s["turi"] for s in lesson["steps"]]
        self.assertEqual(kinds[0], "kirish")
        self.assertIn("qoida", kinds)
        self.assertIn("birga", kinds)
        self.assertEqual(kinds[-1], "xulosa")
        self.assertEqual(lesson["steps"][1]["doska"], "$\\frac{a}{b}$")
        self.assertEqual(len([s for s in lesson["steps"] if s["sahna"] == "M1"]), 4)
        self.assertTrue(lesson["variants"]["B1"])
        self.assertEqual(len(lesson["savollar"]), 1)

    def test_solution_splitting(self):
        self.assertEqual(_split_solution("1) Bir. 2) Ikki."), ["Bir.", "Ikki."])
        self.assertEqual(_split_solution("Birinchi\nIkkinchi"), ["Birinchi", "Ikkinchi"])


if __name__ == "__main__":
    unittest.main()
