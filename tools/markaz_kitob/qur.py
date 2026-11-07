import sys, os, re, glob, shutil, json
sys.path.insert(0, '/tmp/k4'); sys.path.insert(0, '/tmp/gh/talim_platformasi')
from openpyxl import load_workbook
import kitob2miya as K
SRC = '/tmp/miya/pak/03_MAKTAB_MATEMATIKA/uz/matematika/'

def kitob_qur(n, fayllar, chiqish, faqat_qism=None):
    media_dir = f'/tmp/k4/media_k{n}'; os.makedirs(media_dir, exist_ok=True)
    rasm_papka = os.path.join(chiqish, f'rasmlar_k{n}'); os.makedirs(rasm_papka, exist_ok=True)
    rasmlar = {}
    def rasm_nomi(src):
        if src in rasmlar: return rasmlar[src]
        nom = f"k{n}_r{len(rasmlar) + 1:03d}.webp"   # REV406: webp — hajm 3–4 barobar kichik
        if os.path.exists(src):
            from PIL import Image
            im = Image.open(src)
            if im.mode not in ("RGB", "RGBA"): im = im.convert("RGBA")
            if im.width > 1400: im = im.resize((1400, round(im.height * 1400 / im.width)))
            im.save(os.path.join(rasm_papka, nom), "WEBP", quality=88, method=6)
        rasmlar[src] = nom; return nom
    darslar_all, mavzular = [], []
    for qi, f in enumerate(fayllar, 1):
        md = K.md_ol(f, media_dir)
        dl = K.darslarga(K.bloklar(md))
        jv, ish, yech = {}, {}, {}
        for d in dl:
            if d['turi'] == 'javob': jv.update(K.javob_xaritasi(d))
            if d['turi'] == 'ishora': ish.update(K.bandlar_xaritasi(d))
            if d['turi'] == 'yechim': yech.update(K.bandlar_xaritasi(d))
        qism_nom = re.search(r"(\d+)-qism", os.path.basename(f))
        for d in dl:
            if d['turi'] in ('javob', 'ishora', 'yechim'): continue
            j = jv.get(d['nom']) or jv.get(d['nom'].replace(' · ', ' — '), {})
            rows = K.dars_qatorlari(d, j, rasm_nomi, ish.get(d['nom'], {}), yech.get(d['nom'], {})) if d['turi'] == 'dars' else K.nazorat_qatorlari(d, j)
            if rows: darslar_all.append((d['nom'], rows, qi))
    # ai_miya
    wb = load_workbook(SRC + 'matematika_1-sinf_2_ai_miya.xlsx')
    k = wb['KITOB']
    FAN, SINF = "Matematika — markaz", f"{n}-kitob"
    for row in k.iter_rows(min_row=1, max_row=14):
        val = {'Kitob nomi *': f"Matematika {n}-kitob (o‘quv markazi)", 'Fan *': FAN, 'Sinf *': SINF, 'Kitob kodi': f"MARKAZ-MAT{n}-UZ", 'Til': 'uz',
               'Mualliflar': 'Ro‘ziqulov A. · Kabutar Ta’lim', 'Kod prefiksi': f"K{n}"}.get(str(row[0].value or ''))
        if val is not None: row[1].value = val
    shablon = wb[wb.sheetnames[2]]
    for name in wb.sheetnames[2:]:
        if name != shablon.title: del wb[name]
    used = set()
    for i, (nom, rows, qi) in enumerate(darslar_all):
        ws = wb.copy_worksheet(shablon)
        t = re.sub(r"[\\/*?:\[\]]", "", f"{i + 1:03d} {nom}")[:31]
        while t in used: t = t[:28] + str(len(used))
        used.add(t); ws.title = t
        ws['G2'] = nom; ws['B3'] = str(i + 1); ws['G3'] = str(min(30, 10 + n * 4)); ws['B2'] = ''
        for r in range(7, ws.max_row + 1):
            for c in range(1, 18): ws.cell(r, c).value = None
        for j, q in enumerate(rows):
            turi, kod, sarl, matn, doska, rasm, var, javob, yechim, sodda, boshqa, tek, xato, qiy, mas = (list(q) + [''])[:15]
            vals = [j + 1, turi, kod, sarl, matn, doska, rasm, var, javob, yechim, sodda, boshqa, '', tek, mas, xato, qiy]
            for c, v in enumerate(vals, 1): ws.cell(7 + j, c).value = v if v not in ('', None) else None
        mavzular.append((nom, qi))
    del wb[shablon.title]
    ai = os.path.join(chiqish, f"matematika_markaz_{n}-kitob_uz_2_ai_miya.xlsx"); wb.save(ai)
    # mavzular
    mw = load_workbook(SRC + 'matematika_1-sinf_1_mavzular.xlsx'); ms = mw.worksheets[0]
    for r in range(2, ms.max_row + 1):
        for c in range(1, 8): ms.cell(r, c).value = None
    for i, (nom, qi) in enumerate(mavzular):
        for c, v in enumerate([SINF, FAN, str(qi), f"{qi}-qism", "", nom, ""], 1): ms.cell(2 + i, c).value = v or None
    mv = os.path.join(chiqish, f"matematika_markaz_{n}-kitob_uz_1_mavzular.xlsx"); mw.save(mv)
    return ai, mv, rasm_papka, len(darslar_all), len(rasmlar)

if __name__ == "__main__":
    n = int(sys.argv[1]); qismlar = sys.argv[2:] or None
    fl = sorted(glob.glob(f'/tmp/k4/{n}/*.docx'))
    by = {}
    for f in fl:   # bir qismning ikki nusxasi bo'lsa — «(1)» siz nusxa
        q = re.search(r"_(\d+)-qism", os.path.basename(f)).group(1)
        if q not in by or "(1)" in by[q]: by[q] = f
    fl = [by[q] for q in sorted(by, key=int)]
    if qismlar: fl = [f for f in fl if any(f"_{int(q):02d}-qism" in f or f"_{q}-qism" in f for q in qismlar)]
    out = f'/tmp/k4/out/k{n}'; shutil.rmtree(out, ignore_errors=True); os.makedirs(out)
    ai, mv, rp, nd, nr = kitob_qur(n, fl, out)
    from modules import ai_miya_varoq as V
    p = V.parse_sheets(load_workbook(ai), media_names=set(os.listdir(rp)))
    st = p['payload'].get('11_DARS_SSENARIY', [])
    print(f"kitob {n}: fayllar {len(fl)}, varaqlar {nd}, rasmlar {nr}")
    print('xato', len(p['errors']), p['errors'][:3]); print('ogoh', len(p['warnings']), [w['message'][:80] for w in p['warnings'][:5]])
    print('qadam', len(st), 'savolli', sum(1 for s in st if s['qadam_turi'] == 'birga'), 'testlar', len(p['payload'].get('06_MASHQLAR', [])))
