import sys, random, re, os
sys.path.insert(0, '/tmp/m1'); sys.path.insert(0, '/tmp/gh/talim_platformasi')
from openpyxl import load_workbook
import m711
SINF, FAN0 = sys.argv[1], sys.argv[2]          # 7..11, Algebra|Geometriya
FAN = f"{FAN0} (yangi)"
SRC = '/tmp/miya/pak/03_MAKTAB_MATEMATIKA/uz/matematika/matematika_6-sinf_'   # shablon (ustunlar bir xil)
out_dir = '/tmp/m1/out'; os.makedirs(out_dir, exist_ok=True)
rng = random.Random(int(SINF) * 1000 + (1 if FAN0 == "Algebra" else 2))
darslar = m711.darslar711(SINF, FAN0)
wb = load_workbook(SRC + '2_ai_miya.xlsx')
k = wb['KITOB']
kod = f"{'ALG' if FAN0 == 'Algebra' else 'GEO'}{SINF}-YANGI-UZ"
for row in k.iter_rows(min_row=1, max_row=14):
    val = {'Kitob nomi *': f"{FAN0} {SINF}-sinf (yangi, kashfiyot darslari)", 'Fan *': FAN, 'Sinf *': SINF, 'Kitob kodi': kod, 'Til': 'uz',
           'Mualliflar': f'Darslik: {FAN0} {SINF}-sinf · Metodika: Ro‘ziqulov A. · Kabutar Ta’lim', 'Kod prefiksi': f"{'A' if FAN0 == 'Algebra' else 'G'}Y{SINF}", 'Nashr yili': '2026'}.get(str(row[0].value or ''))
    if val is not None: row[1].value = val
shablon = wb[wb.sheetnames[2]]
for name in wb.sheetnames[2:]:
    if name != shablon.title: del wb[name]
used = set(); mav = []
for i, (nom, asl, bob, x) in enumerate(darslar):
    rows = m711.dars_yasa711(asl, FAN0, bob, rng)
    ws = wb.copy_worksheet(shablon)
    t = re.sub(r"[\\/*?:\[\]]", "", f"{i + 1:03d} {nom}")[:31]
    while t in used: t = t[:28] + str(i)
    used.add(t); ws.title = t
    ws['G2'] = nom; ws['B3'] = str(i + 1); ws['G3'] = SINF; ws['B2'] = ''
    for r in range(7, ws.max_row + 1):
        for c in range(1, 18): ws.cell(r, c).value = None
    for j, q in enumerate(rows):
        turi, kod_, sarl, matn, doska, rasm, var, javob, yechim, sodda, boshqa, tek, xato, qiy, mas = (list(q) + [''] * 15)[:15]
        nq = len([y for y in str(doska or "").split("\n") if y.strip()])
        matn = re.sub(r"\s*\[(\d{1,2})\]", lambda m_: m_.group(0) if int(m_.group(1)) <= nq else "", str(matn))
        vals = [j + 1, turi, kod_, sarl, matn, doska, rasm, var, javob, yechim, sodda, boshqa, '', tek, mas, xato, qiy]
        for c, v in enumerate(vals, 1): ws.cell(7 + j, c).value = v if v not in ('', None) else None
    mav.append((nom, bob or f"{FAN0} {SINF}-sinf"))
del wb[shablon.title]
tag = f"{FAN0.lower()}_yangi_{SINF}-sinf_uz"
ai = os.path.join(out_dir, f"{tag}_2_ai_miya.xlsx"); wb.save(ai)
mw = load_workbook(SRC + '1_mavzular.xlsx'); ms = mw.worksheets[0]
for r in range(2, ms.max_row + 1):
    for c in range(1, 8): ms.cell(r, c).value = None
for i, (nom, bob) in enumerate(mav):
    for c, v in enumerate([SINF, FAN, "1" if i < len(mav) // 2 else "2", bob[:60], "", nom, ""], 1): ms.cell(2 + i, c).value = v or None
mv = os.path.join(out_dir, f"{tag}_1_mavzular.xlsx"); mw.save(mv)
from modules import ai_miya_varoq as V
p = V.parse_sheets(load_workbook(ai))
st = p['payload'].get('11_DARS_SSENARIY', [])
print(SINF, FAN0, 'darslar', len(darslar), 'xato', len(p['errors']), p['errors'][:2], 'ogoh', len(p['warnings']), '| qadam', len(st), 'testlar', len(p['payload'].get('06_MASHQLAR', [])))
