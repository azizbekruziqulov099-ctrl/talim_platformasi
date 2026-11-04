"""REV324: bog'cha miyasida «O'yin» ustuni — qadam o'yin raqamini olib yuradi."""
from modules.ai_miya_varoq import COLUMNS, parse_sheets, template_workbook
from modules.dars_xonasi import build_lesson


def test_oyin_raqami_darsga_otadi():
    rows = [
        {"turi": "sir", "sarlavha": "Sehrli quti", "matn": "Qutida nima bor ekan?"},
        {"turi": "tushuncha", "sarlavha": "Besh", "matn": "Mana bu — besh.", "doska": "⭐⭐⭐⭐⭐"},
        {"turi": "oyin", "sarlavha": "Bosib sana", "matn": "Yulduzlarni bosib sana!", "doska": "⭐⭐⭐⭐⭐", "oyin": "31"},
        {"turi": "oyin", "sarlavha": "Noto'g'ri raqam", "matn": "Bos!", "oyin": "999"},
    ]
    wb = template_workbook(prefill=[], book={"kitob_nomi": "Mat 4-5", "fan": "Matematika", "sinf": "4-5 yosh", "til": "uz"}, blank_topics=0)
    ws = wb.create_sheet("01 Besh")
    ws.cell(2, 1, "Mavzu nomi *"); ws.cell(2, 2, "Besh soni")
    for col, (key, label, *_r) in enumerate(COLUMNS, 1):
        ws.cell(6, col, label)
        for r, row in enumerate(rows, 7):
            if key in row:
                ws.cell(r, col, row[key])
    parsed = parse_sheets(wb)
    assert not parsed["errors"], parsed["errors"]
    p = parsed["payload"]
    units = [{"unit_code": r["step_id"], "unit_kind": "lesson_step", "payload": r} for r in p["11_DARS_SSENARIY"]]
    units += [{"unit_code": r["task_id"], "unit_kind": "task", "payload": r} for r in p["06_MASHQLAR"]]
    lesson = build_lesson({"mavzu": "x"}, units, lambda x: x)
    amaliy = [s for s in lesson["steps"] if s["turi"] == "amaliy"]
    assert amaliy and amaliy[0].get("oyin") == 31
    assert all(s.get("oyin") in (None, 31) for s in amaliy)   # 999 — qabul qilinmaydi
    assert lesson["steps"][0]["turi"] == "kirish"
