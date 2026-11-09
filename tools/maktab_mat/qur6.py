import sys, random, re, os
sys.path.insert(0, '/tmp/m1'); sys.path.insert(0, '/tmp/gh/talim_platformasi')
from openpyxl import load_workbook
import m1, m2, m34, m56
SRC = '/tmp/miya/pak/03_MAKTAB_MATEMATIKA/uz/matematika/'
FAN, SINF = "Matematika (yangi)", "6"
out_dir = '/tmp/m1/out'; os.makedirs(out_dir, exist_ok=True)
rng = random.Random(6006)
darslar = m56.darslar56("6")
wb = load_workbook(SRC + 'matematika_6-sinf_2_ai_miya.xlsx')
k = wb['KITOB']
for row in k.iter_rows(min_row=1, max_row=14):
    val = {'Kitob nomi *': "Matematika 6-sinf (yangi, o‘yinli)", 'Fan *': FAN, 'Sinf *': SINF, 'Kitob kodi': "MAT6-YANGI-UZ", 'Til': 'uz',
           'Mualliflar': 'Darslik: Matematika 6-sinf darsligi, 2024 · Metodika: Ro‘ziqulov A. · Kabutar Ta’lim', 'Kod prefiksi': "MY6", 'Nashr yili': '2026'}.get(str(row[0].value or ''))
    if val is not None: row[1].value = val
shablon = wb[wb.sheetnames[2]]
for name in wb.sheetnames[2:]:
    if name != shablon.title: del wb[name]
used = set(); mav = []
for i, (nom, asl, bob, x) in enumerate(darslar):
    rows = m56.dars_yasa56(asl, bob, rng)
    ws = wb.copy_worksheet(shablon)
    t = re.sub(r"[\\/*?:\[\]]", "", f"{i + 1:03d} {nom}")[:31]
    while t in used: t = t[:28] + str(i)
    used.add(t); ws.title = t
    ws['G2'] = nom; ws['B3'] = str(i + 1); ws["G3"] = "6"; ws['B2'] = ''
    for r in range(7, ws.max_row + 1):
        for c in range(1, 18): ws.cell(r, c).value = None
    for j, q in enumerate(rows):
        turi, kod, sarl, matn, doska, rasm, var, javob, yechim, sodda, boshqa, tek, xato, qiy, mas = (list(q) + [''] * 15)[:15]
        nq = len([y for y in str(doska or "").split("\n") if y.strip()])
        matn = re.sub(r"\s*\[(\d{1,2})\]", lambda m_: m_.group(0) if int(m_.group(1)) <= nq else "", str(matn))
        vals = [j + 1, turi, kod, sarl, matn, doska, rasm, var, javob, yechim, sodda, boshqa, '', tek, mas, xato, qiy]
        for c, v in enumerate(vals, 1): ws.cell(7 + j, c).value = v if v not in ('', None) else None
    qism = bob.lower().capitalize()[:60] or "1-qism"
    mav.append((nom, qism, x.get("bet")))
del wb[shablon.title]
ai = os.path.join(out_dir, "matematika_yangi_6-sinf_uz_2_ai_miya.xlsx"); wb.save(ai)
mw = load_workbook(SRC + 'matematika_6-sinf_1_mavzular.xlsx'); ms = mw.worksheets[0]
for r in range(2, ms.max_row + 1):
    for c in range(1, 8): ms.cell(r, c).value = None
for i, (nom, qism, bet) in enumerate(mav):
    for c, v in enumerate([SINF, FAN, "1" if i < len(mav) // 2 else "2", qism, "", nom, ""], 1): ms.cell(2 + i, c).value = v or None
mv = os.path.join(out_dir, "matematika_yangi_6-sinf_uz_1_mavzular.xlsx"); mw.save(mv)
from modules import ai_miya_varoq as V
p = V.parse_sheets(load_workbook(ai))
st = p['payload'].get('11_DARS_SSENARIY', [])
print('darslar', len(darslar), 'xato', len(p['errors']), p['errors'][:3]); print('ogoh', len(p['warnings']), [w['message'][:90] for w in p['warnings'][:4]])
print('qadam', len(st), 'savolli', sum(1 for s in st if s['qadam_turi'] == 'birga'), 'oyin', sum(1 for s in st if 'OYIN:' in s['doska_matni']), 'testlar', len(p['payload'].get('06_MASHQLAR', [])))
