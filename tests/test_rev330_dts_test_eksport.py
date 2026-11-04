"""REV330: testlar zaxirasi — mavjud test importi o'qiy oladigan formatda."""
import io
from openpyxl import load_workbook
from modules.dts_test_eksport import kitob, TEST_USTUNLAR
from modules.test_template_import import discover_test_worksheets, workbook_topic_metadata


def test_eksport_import_formatida():
    t = [{"topic_code": "MT45-01", "question": "2+2?", "option_a": "3", "option_b": "4", "correct_answer": "B", "difficulty": "oson"}]
    m = [{"topic_code": "MT45-01", "grade": "4-5 yosh", "subject_name": "Matematika", "mavzu_name": "Qanday sanaymiz?"}]
    wb = load_workbook(io.BytesIO(kitob(t, m)))
    sel, skip = discover_test_worksheets(wb)
    assert len(sel) == 1 and sel[0].name == "TESTLAR" and not skip
    meta = workbook_topic_metadata(wb)
    assert meta["MT45-01"]["mavzu_name"] == "Qanday sanaymiz?" and meta["MT45-01"]["subject_name"] == "Matematika"
    assert [c.value for c in wb["TESTLAR"][1]] == TEST_USTUNLAR
    assert wb["TESTLAR"].cell(2, 4).value == "2+2?"
