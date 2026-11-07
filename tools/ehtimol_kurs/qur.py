import sys, random, re, os
sys.path.insert(0, '/tmp/en'); sys.path.insert(0, '/tmp/gh/talim_platformasi')
from openpyxl import load_workbook
import reja
SRC = '/tmp/miya/pak/03_MAKTAB_MATEMATIKA/uz/matematika/'
FAN, SINF = "Ehtimollar nazariyasi va matematik statistika", "2 kurs"

def javob_korinish(j):
    return j.split("|")[-1]

def test_qatori(item, kod, sarl, rng):
    tog = javob_korinish(item["javob"]); xs = []
    for x in item["xato"]:
        if x != tog and x not in xs and x not in item["javob"].split("|"): xs.append(x)
    k = 1
    while len(xs) < 3:   # yetmasa — yaqin sonlar
        try:
            v = float(tog.replace(",", ".")); c = f"{v + k * (abs(v) * 0.1 + 1):.3f}".rstrip("0").rstrip(".").replace(".", ",")
        except ValueError:
            c = f"{tog}{k}"
        if c != tog and c not in xs: xs.append(c)
        k += 1
    opts = [tog] + xs[:3]; rng.shuffle(opts)
    return ("test", kod, sarl, item["matn"], "", "", "\n".join(f"{'ABCD'[i]}) {o}" for i, o in enumerate(opts)), "ABCD"[opts.index(tog)],
            item["yechim"], "", "", "", "", "o‘rta", "")

def tekshiruv(item):
    tog = javob_korinish(item["javob"]); xs = []
    for x in item["xato"]:
        if x != tog and x not in xs and x not in item["javob"].split("|"): xs.append(x)
    xs = xs[:3]
    return f"{item['matn']} => " + " | ".join([tog] + xs) if xs else f"{item['matn']} => {tog}"

def yangi(gen, rng, kordi):
    for _ in range(40):
        it = gen(rng)
        if it["matn"] not in kordi:
            kordi.add(it["matn"]); return it
    return it

def maruza(i, m, rng):
    nom, nazariya, misollar, testlar = m
    kordi, R = set(), []
    R.append(("kirish", "", "🎯 " + re.sub(r"^\d+-ma’ruza\.\s*", "", nom), f"Assalomu alaykum! {nom}. Ma’ruza 80 daqiqa: avval tushunchalarni birga tushunamiz — har bir tushunchadan keyin sizga savol beraman, javobni tanlaysiz. Keyin namunaviy misollarni yechamiz va oxirida qisqa test.",
              "Reja:\n" + "\n".join(f"{k + 1}. {t[0]}" for k, t in enumerate(nazariya)) + "\n→ Namunalar → Test", "", "", "", "", "", "", "", "", "", ""))
    for sarl, ovoz, doska, sav in nazariya:
        tek = sav if isinstance(sav, str) else tekshiruv(yangi(sav, rng, kordi))
        R.append(("tushuncha", "", sarl, ovoz, doska, "", "", "", "", "", "", tek, "", "", ""))
    for k, g in enumerate(misollar, 1):
        it = yangi(g, rng, kordi)
        R.append(("misol", f"N{k:02d}", f"{k}-namuna", it["matn"], "", "", "", it["javob"], it["yechim"] + f"\nJavob: {javob_korinish(it['javob'])}", "", "", "", "", "o‘rta", ""))
    for k, g in enumerate(testlar, 1):
        R.append(test_qatori(yangi(g, rng, kordi), f"T{k:02d}", f"Test {k}", rng))
    R.append(("xulosa", "", "🌟 Yodda tuting", "Bugungi ma’ruzaning asosiy formulalari doskada. Ularni daftaringizga yozib oling — amaliy mashg‘ulotda kerak bo‘ladi.",
              "\n".join(t[2].split("\n")[0] for t in nazariya), "", "", "", "", "", "", "", "", "", ""))
    return R

def amaliy(j, a, rng):
    nom, _, (rs, ro, rd), gens = a
    kordi, R = set(), []
    R.append(("kirish", "", f"🎯 {j}-amaliy: {nom}", "Bugungi amaliy mashg‘ulot 80 daqiqa. Reja: 10 daqiqa formulalarni takrorlaymiz, 15 daqiqa namunalarni birga ko‘ramiz, 40 daqiqa masalalarni o‘zingiz yechasiz, 15 daqiqa test. Qiynalsangiz avval «Maslahat», keyin «Yechim»ni oching — lekin avval o‘zingiz urinib ko‘ring!",
              "⏱ 10′ takrorlash\n⏱ 15′ namunalar\n⏱ 40′ mustaqil masalalar (12 ta)\n⏱ 15′ test (8 ta)", "", "", "", "", "", "", "", "", "", ""))
    R.append(("tushuncha", "", rs, ro, rd, "", "", "", "", "", "", tekshiruv(yangi(gens[0], rng, kordi)), "", "", ""))
    for k in range(2):
        it = yangi(gens[k % len(gens)], rng, kordi)
        R.append(("misol", f"N{k + 1:02d}", f"{k + 1}-namuna", it["matn"], "", "", "", it["javob"], it["yechim"] + f"\nJavob: {javob_korinish(it['javob'])}", "", "", "", "", "o‘rta", ""))
    for k in range(12):
        it = yangi(gens[k % len(gens)], rng, kordi)
        mas = it["yechim"].split("\n")[0]
        mas = re.sub(r"=\s*[^=$]*\$\s*\.?$", "$.", mas) if mas.count("=") > 1 else "Ma’ruzadagi formulani eslang va qiymatlarni o‘rniga qo‘ying."
        R.append(("masala", f"M{k + 1:02d}", f"Masala {k + 1}", it["matn"], "", "", "", it["javob"], it["yechim"] + f"\nJavob: {javob_korinish(it['javob'])}", "", "", "", "",
                  "oson" if k < 4 else "o‘rta" if k < 9 else "qiyin", mas))
    for k in range(8):
        R.append(test_qatori(yangi(gens[(k + 1) % len(gens)], rng, kordi), f"T{k + 1:02d}", f"Test {k + 1}", rng))
    R.append(("xulosa", "", "🌟 Bugun nimani mashq qildik", "Barakalla! Bugungi formulalar doskada. Yechilmay qolgan masalalarni uyda tugating.", rd, "", "", "", "", "", "", "", "", "", ""))
    return R

def qur(chiqish):
    rng = random.Random(2026)
    mavzular, sheets = [], []
    aj = 0
    for i, m in enumerate(reja.MARUZA, 1):
        bob = "Ehtimollar nazariyasi" if i <= 7 else "Matematik statistika"
        sheets.append((m[0], maruza(i, m, rng))); mavzular.append((m[0], bob, "Ma’ruza"))
        for a in [a for a in reja.AMALIY if a[1] == i]:
            aj += 1; n = f"{aj}-amaliy. {a[0]}"
            sheets.append((n, amaliy(aj, a, rng))); mavzular.append((n, bob, "Amaliy"))
    wb = load_workbook(SRC + 'matematika_1-sinf_2_ai_miya.xlsx')
    k = wb['KITOB']
    for row in k.iter_rows(min_row=1, max_row=14):
        val = {'Kitob nomi *': "Ehtimollar nazariyasi va matematik statistika (15 ma’ruza, 45 amaliy)", 'Fan *': FAN, 'Sinf *': SINF, 'Kitob kodi': "EHTIMOL-STAT-UZ",
               'Til': 'uz', 'Mualliflar': 'Ro‘ziqulov A. · Kabutar Ta’lim', 'Kod prefiksi': "ENS"}.get(str(row[0].value or ''))
        if val is not None: row[1].value = val
    shablon = wb[wb.sheetnames[2]]
    for name in wb.sheetnames[2:]:
        if name != shablon.title: del wb[name]
    used = set()
    for i, (nom, rows) in enumerate(sheets):
        ws = wb.copy_worksheet(shablon)
        t = re.sub(r"[\\/*?:\[\]]", "", f"{i + 1:02d} {nom}")[:31]
        while t in used: t = t[:29] + str(i)
        used.add(t); ws.title = t
        ws['G2'] = nom; ws['B3'] = str(i + 1); ws['G3'] = "24"; ws['B2'] = ''
        for r in range(7, ws.max_row + 1):
            for c in range(1, 18): ws.cell(r, c).value = None
        for j, q in enumerate(rows):
            turi, kod, sarl, matn, doska, rasm, var, javob, yechim, sodda, boshqa, tek, xato, qiy, mas = (list(q) + [''] * 15)[:15]
            nq = len([x for x in str(doska or "").split("\n") if x.strip()])
            matn = re.sub(r"\s*\[(\d{1,2})\]", lambda m_: m_.group(0) if int(m_.group(1)) <= nq else "", str(matn))
            vals = [j + 1, turi, kod, sarl, matn, doska, rasm, var, javob, yechim, sodda, boshqa, '', tek, mas, xato, qiy]
            for c, v in enumerate(vals, 1): ws.cell(7 + j, c).value = v if v not in ('', None) else None
    del wb[shablon.title]
    ai = os.path.join(chiqish, "ehtimollar_statistika_uz_2_ai_miya.xlsx"); wb.save(ai)
    mw = load_workbook(SRC + 'matematika_1-sinf_1_mavzular.xlsx'); ms = mw.worksheets[0]
    for r in range(2, ms.max_row + 1):
        for c in range(1, 8): ms.cell(r, c).value = None
    for i, (nom, bob, tur) in enumerate(mavzular):
        for c, v in enumerate([SINF, FAN, "1" if bob.startswith("Ehtimol") else "2", bob, tur, nom, ""], 1): ms.cell(2 + i, c).value = v
    mv = os.path.join(chiqish, "ehtimollar_statistika_uz_1_mavzular.xlsx"); mw.save(mv)
    return ai, mv, sheets

if __name__ == "__main__":
    out = '/tmp/en/out'; os.makedirs(out, exist_ok=True)
    ai, mv, sheets = qur(out)
    from modules import ai_miya_varoq as V
    p = V.parse_sheets(load_workbook(ai))
    st = p['payload'].get('11_DARS_SSENARIY', [])
    print('mavzular', len(sheets), 'xato', len(p['errors']), p['errors'][:3]); print('ogoh', len(p['warnings']), [w['message'][:90] for w in p['warnings'][:4]])
    print('qadam', len(st), 'savolli', sum(1 for s in st if s['qadam_turi'] == 'birga'), 'testlar', len(p['payload'].get('06_MASHQLAR', [])))
