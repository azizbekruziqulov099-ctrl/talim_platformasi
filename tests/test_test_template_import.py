import unittest
from pathlib import Path

import openpyxl

try:  # fullstack repository: backend/tests va backend/modules
    from backend.modules.test_template_import import (
        discover_test_worksheets,
        embedded_images_by_row,
        is_named_test_sheet,
    )
except ModuleNotFoundError:  # backend-only repository: tests va modules
    from modules.test_template_import import (
        discover_test_worksheets,
        embedded_images_by_row,
        is_named_test_sheet,
    )


class _AnchorFrom:
    row = 6


class _Anchor:
    _from = _AnchorFrom()


class _Image:
    anchor = _Anchor()
    format = "PNG"

    @staticmethod
    def _data():
        return b"image-bytes"


class _SecondImage(_Image):
    @staticmethod
    def _data():
        return b"second-image"


class TestTemplateImportHelpers(unittest.TestCase):
    def test_discovers_all_twenty_two_test_sheets_not_only_the_first(self):
        workbook = openpyxl.Workbook()
        workbook.remove(workbook.active)
        for number in range(1, 23):
            worksheet = workbook.create_sheet(f"TESTLAR_Fan_{number}")
            worksheet.append(["TOPIC_CODE", " Question ", "correct_answer"])
            worksheet.append([f"1-FAN-{number}", f"Savol {number}", "A"])

        workbook.create_sheet("MALUMOT").append(["Topic code", "Fan"])
        # Hatto asosiy ustunlarga o'xshasa ham, TESTLAR varaqlari mavjud
        # paytda yordamchi varaq importga aralashmasligi kerak.
        workbook.create_sheet("IZOH").append(["topic_code", "question"])
        broken = workbook.create_sheet("TESTLAR_Buzilgan")
        broken.append(["topic_code", "correct_answer"])

        selected, skipped = discover_test_worksheets(workbook)

        self.assertEqual(len(selected), 22)
        self.assertEqual([item.name for item in selected[:2]], ["TESTLAR_Fan_1", "TESTLAR_Fan_2"])
        self.assertEqual(sum(item.worksheet.max_row - 1 for item in selected), 22)
        self.assertEqual(skipped[0]["varaq"], "TESTLAR_Buzilgan")
        self.assertEqual(skipped[0]["yetishmagan_ustunlar"], ["question"])

    def test_accepts_renamed_sheet_by_signature_when_no_testlar_name_exists(self):
        workbook = openpyxl.Workbook()
        workbook.active.title = "Mening savollarim"
        workbook.active.append(["topic_code", "question", "correct_answer"])
        workbook.active.append(["1-MAT-1", "2 + 2?"])

        selected, skipped = discover_test_worksheets(workbook)

        self.assertEqual([item.name for item in selected], ["Mening savollarim"])
        self.assertEqual(skipped, [])
        self.assertTrue(is_named_test_sheet("testlar_Fizika"))
        self.assertTrue(is_named_test_sheet("TESTLAR Fizika"))

    def test_accepts_renamed_valid_sheet_alongside_named_test_sheet(self):
        workbook = openpyxl.Workbook()
        workbook.active.title = "TESTLAR_Matematika"
        workbook.active.append(["topic_code", "question", "correct_answer"])
        workbook.active.append(["1-MAT-1", "2 + 2?", "A"])
        renamed = workbook.create_sheet("Qo'shimcha savollar")
        renamed.append(["topic_code", "question", "correct_answer"])
        renamed.append(["1-MAT-2", "3 + 3?", "B"])

        selected, skipped = discover_test_worksheets(workbook)

        self.assertEqual(
            [item.name for item in selected],
            ["TESTLAR_Matematika", "Qo'shimcha savollar"],
        )
        self.assertEqual(skipped, [])

    def test_embedded_image_is_keyed_by_one_based_excel_row(self):
        worksheet = type("Worksheet", (), {"_images": [_Image()]})()

        result = embedded_images_by_row(worksheet)

        self.assertEqual(result.source_count, 1)
        self.assertEqual(result.by_row, {7: (b"image-bytes", "png")})
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])

    def test_first_image_wins_when_two_images_share_one_row(self):
        worksheet = type("Worksheet", (), {"_images": [_Image(), _SecondImage()]})()

        result = embedded_images_by_row(worksheet)

        self.assertEqual(result.by_row, {7: (b"image-bytes", "png")})
        self.assertEqual(len(result.warnings), 1)


class TestTemplateImportEndpointContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        main_path = Path(__file__).resolve().parents[1] / "main.py"
        main_source = main_path.read_text(encoding="utf-8")
        start = main_source.index("async def shablon_import")
        end = main_source.index("\n@app.get(\"/api/test_rasmi/", start)
        cls.endpoint = main_source[start:end]

    def test_multi_sheet_loop_and_atomic_single_commit(self):
        self.assertIn("for test_varaq in test_varaqlar", self.endpoint)
        self.assertIn("SAVEPOINT shablon_import_qatori", self.endpoint)
        self.assertIn("ROLLBACK TO SAVEPOINT shablon_import_qatori", self.endpoint)
        self.assertEqual(self.endpoint.count("conn.commit()"), 1)
        self.assertIn("conn.rollback()", self.endpoint)

    def test_malformed_named_sheet_is_rejected_before_database_write(self):
        validation = self.endpoint.index("if buzuq_test_varaqlar")
        database_open = self.endpoint.index("conn = _db()")
        self.assertLess(validation, database_open)
        self.assertIn("status_code=400", self.endpoint[validation:database_open])

    def test_duplicate_fingerprint_uses_all_answers_and_question_type(self):
        for column in (
            "option_a", "option_b", "option_c", "option_d",
            "correct_answer", "question_type",
        ):
            self.assertIn(f"COALESCE({column}", self.endpoint)

    def test_response_contains_multi_sheet_diagnostics(self):
        for key in (
            '"import_qilingan_varaq_soni"',
            '"import_qilingan_varaqlar"',
            '"korilgan_savollar_soni"',
            '"fayldagi_topic_code_soni"',
            '"varaq_diagnostika"',
        ):
            self.assertIn(key, self.endpoint)


if __name__ == "__main__":
    unittest.main()
