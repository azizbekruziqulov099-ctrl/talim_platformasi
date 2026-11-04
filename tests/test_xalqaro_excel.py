import json, os, io
from openpyxl import load_workbook
from modules.xalqaro_excel import json_to_xlsx, xlsx_to_json, mosligini_tekshir

D = os.path.join(os.path.dirname(__file__), "..", "modules", "xalqaro_data")


def _norm(x):
    if isinstance(x, dict):
        return {k: _norm(v) for k, v in sorted(x.items()) if v not in (None, [], {}, "")}
    if isinstance(x, list):
        return [_norm(v) for v in x]
    return x


def test_rev319_excel_aylanma_va_moslik():
    uz = json.load(open(os.path.join(D, "savollar.json"), encoding="utf8"))[:60]
    ru = json.load(open(os.path.join(D, "ru", "savollar.json"), encoding="utf8"))[:60]
    for til, asl in (("uz", uz), ("ru", ru)):
        t, back, xato, _ = xlsx_to_json(json_to_xlsx(asl, til, stat_manba=uz))
        assert t == til and not xato and len(back) == len(asl)
        assert [_norm(q) for q in asl] == [_norm(q) for q in back]   # Excel → JSON — sayt o'qiydigan aynan o'sha tuzilma
    assert mosligini_tekshir(uz, ru) == []
    # to'g'ri javob tillar orasida farq qilsa — xato
    b = json_to_xlsx(ru, "ru", stat_manba=uz)
    wb = load_workbook(io.BytesIO(b)); ws = wb["SAVOLLAR"]
    for row in ws.iter_rows(min_row=2):
        if row[6].value == "tanlov":
            row[13].value = "A" if row[13].value != "A" else "B"; break
    buf = io.BytesIO(); wb.save(buf)
    _, ru2, xato, _ = xlsx_to_json(buf.getvalue())
    assert not xato and any("to'g'ri javob farq" in x for x in mosligini_tekshir(uz, ru2))
