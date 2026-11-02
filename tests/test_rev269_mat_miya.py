"""REV269: matematika miyasi v2 — tekshiruv savoli, maslahat, xato izohi, qiyinlik."""
import openpyxl

from modules.ai_miya_varoq import COLUMNS, parse_sheets, template_workbook
from modules.dars_xonasi import build_lesson


def _kitob(til="uz"):
    rows = [
        {"turi": "tushuncha", "sarlavha": "Qoida", "matn": "Suratni suratga ko'paytiramiz. [1]", "doska": "$\\frac{a}{b}\\cdot\\frac{c}{d}=\\frac{ac}{bd}$",
         "tekshiruv": "$\\frac{1}{2}\\cdot\\frac{1}{3}$ nechaga teng? => 1/6"},
        {"turi": "misol", "kod": "M01", "sarlavha": "Misol", "matn": "$\\frac{2}{3}\\cdot\\frac{3}{4}$ ni hisoblang.",
         "yechim": "QISQART: 3/3 -> 1/1 (:3) || Uchlarni qisqartiramiz.\nJavob: $\\frac{1}{2}$ || Javob — bir ikkidan.",
         "maslahat": "Avval qisqartirib ko'ring.\nSuratdagi 3 va maxrajdagi 3 ga qarang.", "qiyinlik": "oson"},
        {"turi": "test", "kod": "T01", "sarlavha": "Test", "matn": "$\\frac{1}{2}\\cdot\\frac{1}{2}$ = ?",
         "variantlar": "A) 1/4\nB) 2/4\nC) 1\nD) 2/2", "javob": "A", "yechim": "1·1=1, 2·2=4.",
         "xato_izohi": "B => Suratlarni qo'shib yubordingiz.\nC => Bu kasrlarni qo'shish emas."},
    ]
    wb = template_workbook(prefill=[], book={"kitob_nomi": "Matematika 5", "fan": "Matematika", "sinf": "5", "til": til}, blank_topics=0)
    ws = wb.create_sheet("01 Kasrlarni ko'paytirish")
    ws.cell(2, 1, "Mavzu nomi *"); ws.cell(2, 2, "Kasrlarni ko'paytirish")
    for col, (key, label, *_rest) in enumerate(COLUMNS, 1):
        ws.cell(6, col, label)
        for r, row in enumerate(rows, 7):
            if key in row:
                ws.cell(r, col, row[key])
    return wb


def _lesson(parsed):
    p = parsed["payload"]
    units = [{"unit_code": r["step_id"], "unit_kind": "lesson_step", "payload": r} for r in p["11_DARS_SSENARIY"]]
    units += [{"unit_code": r["task_id"], "unit_kind": "task", "payload": r} for r in p["06_MASHQLAR"]]
    return build_lesson({"mavzu": "x"}, units, lambda x: x)


def test_tekshiruv_maslahat_xato():
    parsed = parse_sheets(_kitob())
    assert not parsed["errors"], parsed["errors"]
    lesson = _lesson(parsed)
    turlar = [s["turi"] for s in lesson["steps"]]
    assert turlar[:2] == ["qoida", "birga"]
    birga = lesson["steps"][1]
    assert birga["javob"] == "1/6" and birga["sahna"] == lesson["steps"][0]["sahna"] and birga["sarlavha"] == "Tekshiruv savoli"
    amaliy = next(s for s in lesson["steps"] if s["turi"] == "amaliy")
    assert amaliy["maslahat"] == ["Avval qisqartirib ko'ring.", "Suratdagi 3 va maxrajdagi 3 ga qarang."]
    assert amaliy["yechim"][0]["doska"].startswith("QISQART:")
    q = lesson["savollar"][0]
    assert q["xatolar"] == {"1": "Suratlarni qo'shib yubordingiz.", "2": "Bu kasrlarni qo'shish emas."}


def test_ruscha_tekshiruv_nomi():
    lesson = _lesson(parse_sheets(_kitob("ru")))
    assert lesson["steps"][1]["sarlavha"] == "Проверь себя" and lesson["steps"][1]["savol"] == "Ваш ответ"


def test_eski_paket_ishlaydi():
    import os, pytest
    yol = "/tmp/x/mat/paket/matematika/matematika_5-sinf_2_ai_miya.xlsx"
    if not os.path.exists(yol):
        pytest.skip("muallifning mahalliy paketi bu muhitda yo'q")
    wb = openpyxl.load_workbook(yol)
    parsed = parse_sheets(wb)
    assert not parsed["errors"] and not parsed["warnings"]
