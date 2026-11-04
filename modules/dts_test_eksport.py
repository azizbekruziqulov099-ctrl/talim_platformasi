"""REV330: «DTS test miyasi» — bazadagi testlarni (generated_tests) mavzulari bilan Excel'ga saqlash.
Fayl mavjud test importi formatida: TESTLAR (savollar) + MALUMOT (kod → sinf/fan/bob/bo'lim/mavzu).
Miya tozalanib mavzular qayta yuklansa ham, shu faylni qayta yuklaganda testlar mavzu NOMI bo'yicha yangi kodga ulanadi."""
import io
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

TEST_USTUNLAR = ["topic_code", "difficulty", "situation", "question", "option_a", "option_b", "option_c", "option_d",
                 "correct_answer", "explanation", "question_type", "is_latex", "image_url", "audio_text", "language",
                 "life_level", "age_group", "time_limit", "maqsad"]
MALUMOT_USTUNLAR = [("topic_code", "topic_code"), ("grade", "Sinf"), ("subject_name", "Fan"), ("quarter", "Chorak"),
                    ("bob_name", "Bob"), ("bolim_name", "Bo'lim"), ("mavzu_name", "Mavzu"), ("kichik_name", "Kichik mavzu")]


def _sarlavha(ws, nomlar):
    ws.append(nomlar)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="2B3452")
        c.alignment = Alignment(vertical="center")
    ws.freeze_panes = "A2"


def kitob(testlar, mavzular):
    """testlar — generated_tests qatorlari (dict), mavzular — dts_tree qatorlari (dict). Qaytaradi: xlsx baytlar."""
    wb = Workbook()
    ws = wb.active; ws.title = "TESTLAR"
    _sarlavha(ws, TEST_USTUNLAR)
    for t in testlar:
        ws.append([("" if t.get(k) is None else t.get(k)) for k in TEST_USTUNLAR])
    for i, w in enumerate([16, 10, 24, 60, 26, 26, 26, 26, 10, 40, 12, 8, 26, 30, 8, 8, 10, 8, 20], 1):
        ws.column_dimensions[ws.cell(1, i).column_letter].width = w
    wm = wb.create_sheet("MALUMOT")
    _sarlavha(wm, [n for _, n in MALUMOT_USTUNLAR])
    for m in mavzular:
        wm.append([("" if m.get(k) is None else str(m.get(k))) for k, _ in MALUMOT_USTUNLAR])
    wi = wb.create_sheet("YORDAM")
    for line in ("DTS test miyasi — bazadagi testlar zaxirasi.",
                 "Qayta yuklash: Admin → Testlar → Excel'dan import (sinf va fanni tanlang).",
                 "Mavzu kodi o'zgargan bo'lsa, MALUMOT varag'idagi bob/bo'lim/mavzu nomi bo'yicha yangi kod topiladi.",
                 f"Testlar: {len(testlar)} ta, mavzular: {len(mavzular)} ta."):
        wi.append([line])
    wi.column_dimensions["A"].width = 110
    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()


def yig(cur, sinf, fan_kaliti=None, subject_key=lambda x: x):
    """Tanlangan sinf (va ixtiyoriy fan) testlari va ularning mavzulari."""
    cur.execute("""SELECT topic_code, grade, subject_name, quarter, bob_name, bolim_name, mavzu_name, kichik_name
                   FROM dts_tree WHERE TRIM(grade)=%s""", (sinf.strip(),))
    mav = [dict(r) for r in cur.fetchall() if not fan_kaliti or subject_key(r["subject_name"]) == fan_kaliti]
    codes = sorted({m["topic_code"] for m in mav})
    if not codes:
        return [], []
    cur.execute(f"""SELECT {", ".join(TEST_USTUNLAR)} FROM generated_tests WHERE topic_code = ANY(%s) ORDER BY topic_code, id""", (codes,))
    tests = [dict(r) for r in cur.fetchall()]
    used = {t["topic_code"] for t in tests}
    return tests, [m for m in mav if m["topic_code"] in used]
