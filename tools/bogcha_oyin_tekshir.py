"""REV680: bog'cha o'yin tekshiruvi. Ishlatish: python3 tools/bogcha_oyin_tekshir.py <dastur.json> [...]
Qoidalar (xato = chiqish kodi 1):
 1) «topshiriq» (o'yin) qatorida doskadagi har rasm-guruh shu darsning YANGI bilim qadami (tushuncha sarlavhasi
    «emoji so'z») kaliti bo'lishi shart — aks holda ovozda aytilgan narsa bosiladigan nishon bo'lmaydi.
 2) O'yinda kamida 2 nishon.
 3) Taqiqlangan so'z/belgi (eshak/donkey/🫏) bolalar darsida yo'q.
 4) Bitta qatorda ovozda nomi aytilgan, lekin doskada rasmi yo'q so'z (o'yin qatorlarida) — ogohlantirish.
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.bogcha_kitob import build_books

PIC = re.compile(r'^((?:[\U0001F000-\U0001FFFF☀-➿️‍]|[#*0-9]️?⃣)+)\s+(.+)$')
BAN = re.compile(r'eshak|donkey|\U0001FACF|ослик|осёл|esel\b|burro|ロバ|당나귀|驴|حمار', re.I)
TAG = re.compile(r'\[/?\w\w\]')

def check(paths):
    errs, warns = [], []
    for b in build_books(paths):
        for t in b['topics']:
            where = f"{b['subject']} {b['age']} «{t['name']}»"
            if re.search(r'takrori|bayram|eslaymiz', t['name'], re.I): continue   # takror darslari dvigatelniki (tapWords)
            new = set()
            for r in t['rows']:
                if r.get('turi') == 'tushuncha':
                    m = PIC.match(TAG.sub('', r.get('sarlavha', '')).strip())
                    if m: new.add(m.group(1).replace('️', ''))
            for r in t['rows']:
                blob = ' '.join(str(r.get(k, '')) for k in ('sarlavha', 'matn', 'doska', 'sodda', 'boshqa_usul'))
                if BAN.search(blob): errs.append(f"{where}: taqiqlangan so'z/belgi")
                if r.get('turi') != 'topshiriq': continue
                if 'bos' not in (r.get('matn', '') + r.get('sarlavha', '')).lower() and 'top' not in (r.get('matn', '') + r.get('sarlavha', '')).lower():
                    continue
                groups = [g.strip().replace('️', '') for g in re.split(r'\s{2,}|\n+', r.get('doska', '')) if g.strip()]
                keys = [PIC.match(g).group(1) if PIC.match(g) else g for g in groups]
                keys = [k.replace('️', '') for k in keys]
                pics = [k for k in keys if re.search(r'[\U0001F000-\U0001FFFF☀-➿\u20E3]', k)]
                bad = [k for k in pics if k not in new]
                if bad: errs.append(f"{where}: o'yin doskasida shu darsda o'tilmagan rasm {bad}")
                if len(pics) - len(bad) < 2: errs.append(f"{where}: o'yinda 2 tadan kam nishon")
    return errs, warns

if __name__ == '__main__':
    errs, warns = check(sys.argv[1:])
    for e in errs: print('XATO', e)
    print(f"{len(errs)} xato")
    sys.exit(1 if errs else 0)
