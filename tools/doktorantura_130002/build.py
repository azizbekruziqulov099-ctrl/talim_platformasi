#!/usr/bin/env python3
"""Build the printable memorization scheme (HTML -> PDF) from data/s*.txt."""
import html, re, sys, json
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"

def uz(s: str) -> str:
    s = re.sub(r"([oOgG])'", lambda m: m.group(1) + "‘", s)
    return s.replace("'", "’")

def rich(s: str) -> str:
    s = html.escape(uz(s), quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)

COLORS = {1: "#1D4E89", 2: "#8A4B08", 3: "#6B2C91", 4: "#2E6B30",
          5: "#B3261E", 6: "#00707A", 7: "#B0154F"}
TINTS = {1: "#E7EEF7", 2: "#F6EDE2", 3: "#F0E8F5", 4: "#E8F1E8",
         5: "#F9E9E8", 6: "#E3F2F3", 7: "#F8E6ED"}

# Themes ("shoxlar") for the tree: section -> [(theme, [question numbers])]
THEMES = {
 1: [("Fan va tushunchalar", [1,7,8,9,13,14,19,29,30,31,34]),
     ("Qonun va hujjatlar", [2,3,5,22,28,32,36,37,41,47,48]),
     ("Dars va ta'lim", [4,6,10,11,12,45,49]),
     ("Shaxs va jamoa", [15,16,17,18,21,23,25,26,27,46]),
     ("Tarbiya turlari va usullari", [20,24,33,35,38,39,40,42,43,44,50])],
 2: [("Fan va manbalar", [6,7,9,13,17,18]),
     ("Qadimgi davr, Avesto", [5,8,10]),
     ("Islom va arab istilosi", [3,14,28,30,31,32,34,35,36]),
     ("Uyg'onish allomalari", [2,4,11,12,19,21,26,33,37,41,43,44,45,50]),
     ("Temuriylar davri", [16,22,25,29]),
     ("Chor davri va jadidlar", [1,15,20,23,24,27,38,39,40,42]),
     ("XX asr va xorij pedagoglari", [46,47,48,49])],
 3: [("Mahorat mohiyati", [1,2,3,4,7,9,32,37]),
     ("Qobiliyat va malaka", [5,6,10,11,25,33,42,46]),
     ("Texnika va nutq", [12,15,16,21,22,31,35]),
     ("Muloqot va muomala", [8,13,19,23,24,28,39,41,44,45]),
     ("Ta'sir, takt, o'zini boshqarish", [14,18,20,26,27,36,40,43]),
     ("Allomalar, kuzatish, axborot", [17,29,30,34,38])],
 4: [("Fan asoslari va maqsad", [1,2,3,32]),
     ("Qadriyatlar, milliy tarbiya", [4,5,6,7]),
     ("Usullar va shakllar", [8,9,10,11,12,23,31,34]),
     ("Sinf rahbari", [13,14,15,16,17,18,19,20,21,29,30]),
     ("O'quvchi bilan ishlash", [22,24,25,26,27,28,37]),
     ("Rejalashtirish", [33,35,36,38]),
     ("Tashqari ishlar va jamoa", [39,40,41,42])],
 5: [("Ta'lim jarayoni", [1,2,3,11,12,13,14,15,16]),
     ("Tamoyillar", [4,5,6,7,8,9,10]),
     ("Mazmun va standart", [17,18,19,20,21]),
     ("Metod va texnologiya", [22,23,24,25,26,27,28,29,30,31,56]),
     ("Tashkil etish shakllari", [32,33,34,35,36,37,38,39,40,41,42]),
     ("Vositalar", [43,44]),
     ("Nazorat va baholash", [45,46,47,48,49]),
     ("Tafakkur va tarbiya", [50,51,52,53,54,55]),
     ("Fan metodikasi", [57,58,59,60,61,62,63,64,65,71]),
     ("To'garak, amaliyot, tajriba", [66,67,68,69,70]),
     ("Davlat hujjatlari", [72,73,74])],
 6: [("Qonun va ta'lim tizimi", [1,2,3,4]),
     ("Oliy ta'lim psixologiyasi", [5,6,7,8,28]),
     ("Jahon tajribasi", [9,10]),
     ("Texnologiya va metodlar", [11,12,13,16,29,30,31,32,36,38,39]),
     ("Mashg'ulot shakllari", [17,18,19,27]),
     ("Boshqaruv va kredit-modul", [20,21,22,24,35,37]),
     ("Tarbiya, oila, jamoa", [14,15,23,25,26,33,34]),
     ("Inklyuziya, bilimlar iqtisodiyoti", [40,41])],
 7: [("Talablar va texnologiyalar", [1,2,3,6]),
     ("Fikrlashni rivojlantirish", [4,5,12]),
     ("Yosh, kompetensiya, yordam", [7,8,9,10,13]),
     ("Baholash va ota-onalar", [11,14]),
     ("Matematika mazmuni", [15,16,17,18,19,20,21,22,23]),
     ("Tadqiqot statistikasi", [24,25])],
}

def load():
    sections = []
    for f in sorted(DATA.glob("s*.txt")):
        sec = None
        for raw in f.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("@S"):
                num, title, flow = [p.strip() for p in line[2:].split("|")]
                sec = {"n": int(num), "title": title, "flow": flow, "items": []}
                sections.append(sec)
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 5:
                sys.exit(f"Bad line in {f.name}: {line[:80]} ({len(parts)} parts)")
            n, q, kod, mag, links = parts
            sec["items"].append({"n": int(n), "q": q, "kod": kod, "mag": mag,
                                 "links": links.split()})
    return sections

def check(sections):
    ids = {f"{s['n']}.{it['n']}" for s in sections for it in s["items"]}
    problems = []
    for s in sections:
        nums = [it["n"] for it in s["items"]]
        if nums != list(range(1, len(nums) + 1)):
            problems.append(f"S{s['n']} numbering broken")
        themed = sorted(q for _, qs in THEMES[s["n"]] for q in qs)
        if themed != nums:
            missing = set(nums) - set(themed)
            dup = {q for q in themed if themed.count(q) > 1}
            extra = set(themed) - set(nums)
            problems.append(f"S{s['n']} themes: missing {sorted(missing)} dup {sorted(dup)} extra {sorted(extra)}")
        for it in s["items"]:
            for l in it["links"]:
                if l not in ids:
                    problems.append(f"{s['n']}.{it['n']} -> bad link {l}")
                if l == f"{s['n']}.{it['n']}":
                    problems.append(f"{s['n']}.{it['n']} links to itself")
    return problems

def theme_of(sec_n, q_n):
    for name, qs in THEMES[sec_n]:
        if q_n in qs:
            return name
    return ""

CHECK_WORDS = ("tekshiring", "aniqlashtiring")

def row_html(sec, it):
    sid = sec["n"]
    flag = any(w in it["mag"].lower() for w in CHECK_WORDS)
    links = " · ".join(it["links"])
    return f"""
<div class="row">
  <div class="gut"><div class="node">{sid}.{it['n']}</div><div class="boxes"><i></i><i></i><i></i></div></div>
  <div class="card">
    <div class="c-q"><div class="theme">{html.escape(uz(theme_of(sid, it['n'])))}</div><div class="q">{rich(it['q'])}</div></div>
    <div class="c-k"><div class="kod">{rich(it['kod'])}</div></div>
    <div class="c-m">{rich(it['mag'])}<div class="links">{'<span class="chk">darslikdan tekshiring</span>' if flag else ''}<span class="lk">↔ {links}</span></div></div>
  </div>
</div>"""

def section_html(sec):
    sid = sec["n"]
    chips = "".join(
        f'<div class="chip"><span class="cn">{rich(name)}</span><span class="cq">{", ".join(map(str, qs))}</span></div>'
        for name, qs in THEMES[sid])
    rows = "".join(row_html(sec, it) for it in sec["items"])
    return f"""
<section class="sec" style="--c:{COLORS[sid]};--t:{TINTS[sid]}">
  <div class="sec-head">
    <div class="sh-gut"><div class="sh-node">{sid}</div></div>
    <div class="sh-body">
      <div class="sh-kicker">{sid}-bo‘lim · {len(sec['items'])} ta savol</div>
      <h2>{rich(sec['title'])}</h2>
      <div class="flow">{rich(sec['flow'])}</div>
      <div class="chips">{chips}</div>
    </div>
  </div>
  <div class="thead"><div></div><div class="th"><span>SAVOL</span><span>KOD</span><span>JAVOB MAG‘ZI</span></div></div>
  {rows}
</section>"""

def tree_html(sections):
    blocks = []
    for s in sections:
        sid = s["n"]
        themes = "".join(
            f'<li><span class="tn">{rich(n)}</span> <span class="tq">{", ".join(map(str, qs))}</span></li>'
            for n, qs in THEMES[sid])
        blocks.append(f"""
<div class="tb" style="--c:{COLORS[sid]};--t:{TINTS[sid]}">
  <div class="tb-node">{sid}</div>
  <div class="tb-box"><div class="tb-title">{rich(s['title'])} <span>· {len(s['items'])} savol</span></div>
  <ul>{themes}</ul></div>
</div>""")
    return f"""
<section class="page tree">
  <h2 class="pg-title">Umumiy daraxt: 328 savol 7 shoxda</h2>
  <p class="pg-lead">Tana – imtihon. Har bir bo‘lim – katta shox, har bir mavzu – kichik shox, raqamlar – shu shoxdagi savollar. Avval shu sahifani yodlang: savol qaysi shoxda ekanini bilsangiz, javob o‘zi esga tushadi.</p>
  <div class="trunk">
    <div class="trunk-top">13.00.02</div>
    {''.join(blocks)}
  </div>
</section>"""

TIMELINE = [
 ("Qadim", "Xorazmda zardushtiylik va «Avesto»: ezgu fikr, ezgu so'z, ezgu amal", "2.5 2.8 2.13"),
 ("673–674", "Ubaydulloh ibn Ziyod – Movarounnahrga birinchi yirik yurish", "2.34"),
 ("705–715", "Qutayba ibn Muslim Movarounnahrni bosib oladi", "2.36"),
 ("VIII–IX", "Masjid qoshida musulmon maktablari, keyin madrasalar", "2.30 2.31"),
 ("IX asr", "Hadis ilmining oltin davri: «Kutubi sitta»; Imom Buxoriy (810–870)", "2.14 2.32"),
 ("IX–XII", "I Uyg'onish: Xorazmiy, Farg'oniy, Forobiy, Beruniy, Ibn Sino", "2.19 2.41"),
 ("1004–1017", "Ma'mun akademiyasi (Xorazm)", "2.45"),
 ("1010", "Firdavsiy – «Shohnoma»", "2.43"),
 ("1069–1070", "Yusuf Xos Hojib – «Qutadg'u bilig»", "2.12 2.21"),
 ("1072–1074", "Mahmud Koshg'ariy – «Devonu lug'otit turk»", "2.37"),
 ("1082", "Kaykovus – «Qobusnoma» (44 bob)", "2.50"),
 ("1404 · 1425", "«Zafarnoma»: Nizomiddin Shomiy · Sharafuddin Ali Yazdiy", "2.29"),
 ("1417–1433", "Ulug'bek madrasalari: Buxoro, Samarqand, G'ijduvon", "2.16"),
 ("1500", "Navoiy – «Mahbub ul-qulub»", "2.22 2.25"),
 ("1632 · 1657", "Komenskiy – «Buyuk didaktika»", "1.14"),
 ("1824–1870", "K.D. Ushinskiy – rus ilmiy pedagogikasi asoschisi", "2.47"),
 ("1865 · 1868", "Chor Rossiyasi Toshkentni, so'ng Samarqandni bosib oladi", "2.1"),
 ("1867", "Turkiston general-gubernatorligi, Kaufman maorif siyosati", "2.39"),
 ("1874", "Xivada birinchi toshbosma (Feruz)", "2.40"),
 ("1884", "Toshkentda birinchi rus-tuzem maktabi", "2.15"),
 ("XIX oxiri – XX", "Jadidlar: usuli jadid maktablari, tovush usuli", "2.42 2.27"),
 ("1912 · 1913", "Avloniy: «Birinchi muallim» · «Turkiy Guliston yoxud axloq»", "2.24 2.20"),
 ("1888–1939", "A.S. Makarenko – jamoa nazariyasi", "2.46"),
 ("1897–1970", "T.N. Qori-Niyoziy – O'zFA birinchi prezidenti", "2.49"),
 ("1960–1963", "S. Mutallibov «Devonu lug'otit turk»ni nashr etadi", "2.33"),
]

NUMBERS = [
 ("3", "«Ta'lim to'g'risida»gi Qonun 3 marta: 1992 · 1997 · 2020", "1.2"),
 ("O'RQ-637", "Amaldagi Ta'lim qonuni, 2020-y. 23-sentabr", "6.2"),
 ("7", "Ta'lim turlari: MUPO–OQT", "1.3"),
 ("2-iyul 1992", "Birinchi Ta'lim qonuni va Davlat gerbi – bir kunda", "1.2 1.37"),
 ("21-oktabr", "«Davlat tili haqida»gi Qonun (1989); yangi tahrir 1995-y. 21-dekabr", "5.72"),
 ("PF-4947", "Harakatlar strategiyasi, 2017-y. 7-fevral (2017–2021)", "5.73"),
 ("PQ-2909", "Oliy ta'limni rivojlantirish qarori, 2017-y. 20-aprel", "5.74"),
 ("PF-5847", "Oliy ta'limni 2030-yilgacha rivojlantirish konsepsiyasi", "6.21"),
 ("PF-60", "Taraqqiyot strategiyasi 2022–2026", "5.73"),
 ("45 daqiqa", "Dars davomiyligi", "5.35"),
 ("5", "Dars tiplari: YMTNA", "1.6 5.35"),
 ("8", "Didaktik tamoyillar: ITOK–TMNI", "5.4"),
 ("9", "Krutetskiy bo'yicha pedagogik qobiliyatlar: DAP·NTA·KXD", "1.27 3.11"),
 ("3 / 4", "Makarenko: jamoa bosqichlari P → A → J (→ O')", "1.23"),
 ("4", "Lerner–Skatkin: ta'lim mazmuni elementlari", "5.17"),
 ("5", "Lerner–Skatkin: bilish faoliyati bo'yicha metodlar", "5.30"),
 ("5", "Elkonin–Davidov: o'quv faoliyati elementlari", "6.6"),
 ("5", "Stanislavskiy: muomala bosqichlari", "3.41"),
 ("6", "Blum taksonomiyasi darajalari", "6.28"),
 ("6", "«Olti shlyapa» ranglari (de Bono)", "6.38"),
 ("12", "Forobiy: komil inson va rahbarning sifatlari", "2.4"),
 ("4 × 6", "Komenskiy: 4 bosqich, har biri 6 yil", "1.14"),
 ("6 yosh", "Ibn Sino: bolani maktabga berish yoshi", "2.44"),
 ("6500+", "«Qutadg'u bilig» baytlari", "2.21"),
 ("7500+", "«Devonu lug'otit turk»dagi so'zlar", "2.33"),
 ("44", "«Qobusnoma» boblari", "2.50"),
 ("6–10 · 11–15 · 15–18", "Kichik maktab yoshi · o'smirlik · ilk o'spirinlik", "5.15"),
 ("6+3+3+4", "Yaponiya ta'lim tizimi", "6.10"),
 ("1 kredit ≈ 30 soat", "Yiliga 60 kredit; 100 ball → harf → 5 ball", "6.35"),
 ("1994", "Salamanka deklaratsiyasi (inklyuziv ta'lim)", "6.40"),
 ("1920-yillar", "Garvard biznes maktabida keys-stadi", "6.11"),
 ("56 / 100", "Imtihonda saralash bali: 56–70 qoniqarli, 71–85 yaxshi, 86–100 a'lo", ""),
]

def timeline_html():
    items = "".join(
        f'<div class="tl-row"><div class="tl-date">{rich(d)}</div><div class="tl-dot"></div><div class="tl-ev">{rich(e)} <span class="tl-ref">↔ {r.replace(" ", " · ")}</span></div></div>'
        for d, e, r in TIMELINE)
    return f"""
<section class="page hist" style="--c:{COLORS[2]};--t:{TINTS[2]}">
  <h2 class="pg-title">Tarix vaqt chizig‘i</h2>
  <p class="pg-lead">2-bo‘lim savollarini sanalar bo‘yicha bitta chiziqqa terdik. Chiziqni yuqoridan pastga «hikoya» qilib aytib chiqing – sanalar va asarlar o‘z o‘rnida qoladi.</p>
  <div class="tl">{items}</div>
</section>"""

def numbers_html():
    rows = "".join(
        f'<tr><td class="nb">{rich(n)}</td><td>{rich(m)}</td><td class="nr">{("↔ " + r.replace(" ", " · ")) if r else ""}</td></tr>'
        for n, m, r in NUMBERS)
    return f"""
<section class="page nums">
  <h2 class="pg-title">Raqamlar kodi</h2>
  <p class="pg-lead">Imtihonda raqam aniq yozilsa, javob ishonchli ko‘rinadi. Chap ustunni ko‘rib, o‘ng tomonni aytib chiqing.</p>
  <table class="nt"><thead><tr><th>Raqam</th><th>Nimani bildiradi</th><th>Savol</th></tr></thead><tbody>{rows}</tbody></table>
</section>"""

def cover_html(sections):
    total = sum(len(s["items"]) for s in sections)
    bars = "".join(
        f'<div class="cv-sec" style="--c:{COLORS[s["n"]]};--t:{TINTS[s["n"]]}"><div class="cv-n">{s["n"]}</div><div class="cv-t">{rich(s["title"])}</div><div class="cv-c">{len(s["items"])}</div></div>'
        for s in sections)
    demo = row_html({"n": 1}, {"n": 15, "q": "Shaxs shakllanishiga ta'sir etuvchi omillar",
        "kod": "I–M–T (+F)", "mag": "**I**rsiyat (biologik) · **M**uhit (ijtimoiy: oila, mahalla, jamiyat, OAV) · **T**arbiya (maqsadli ta'sir) + shaxsning o'z **F**aolligi. Yetakchi omil – **tarbiya**",
        "links": ["1.25", "6.8"]})
    return f"""
<section class="page cover">
  <div class="cv-top">13.00.02 · Tayanch doktoranturaga kirish imtihoni</div>
  <h1>Ta’lim va tarbiya nazariyasi va metodikasi</h1>
  <div class="cv-sub">Yodlash sxemasi: {total} savol · 7 bo‘lim · har savolga esda qoladigan KOD va javob mag‘zi</div>
  <div class="cv-secs">{bars}</div>

  <div class="cv-box" style="--c:{COLORS[1]};--t:{TINTS[1]}">
    <h3>Sxemani qanday o‘qish kerak</h3>
    <div class="demo">{demo}</div>
    <ul class="legend">
      <li><b>Chapdagi chiziq</b> – vaqt chizig‘i: savollar boshidan oxirigacha shu chiziqqa osilgan. Tugundagi <b>1.15</b> = 1-bo‘lim, 15-savol.</li>
      <li><b>Kulrang kichik yozuv</b> – savol qaysi shoxda (mavzuda) turgani. To‘liq daraxt keyingi sahifada.</li>
      <li><b>KOD</b> – javobning kaliti: harflar = mag‘izdagi rangli bosh harflar, raqamlar = sanalar.</li>
      <li><b>↔</b> – bog‘liq savollar: javobni boyitish uchun ulardan bir fikr qo‘shing.</li>
      <li><b>□□□</b> – takrorlaganingizda belgi qo‘ying: 1-, 3- va 7-kun.</li>
    </ul>
  </div>

  <div class="cv-grid">
    <div class="cv-box">
      <h3>Yodlash usuli</h3>
      <ol class="steps">
        <li>Avval <b>umumiy daraxtni</b> yodlang: 7 shox va ulardagi mavzular.</li>
        <li>Savolni o‘qing → <b>KODni</b> ovoz chiqarib ayting → har harfni ochib, mag‘izni ayting.</li>
        <li>O‘ng ustunni qog‘oz bilan <b>yoping</b>. Faqat KODga qarab javobni tiklang. Chiqmagan joyni belgilab qo‘ying.</li>
        <li>Kuniga bitta bo‘lim; 1-, 3- va 7-kunda takrorlab, □ ga belgi qo‘ying.</li>
      </ol>
    </div>
    <div class="cv-box">
      <h3>Imtihonda yozish formulasi: <span class="fx">T·K·M·A·X</span></h3>
      <ol class="formula">
        <li><b>T</b>a’rif – tushuncha ta’rifi, kim kiritgan.</li>
        <li><b>K</b>od – kodning har harfi alohida jumla yoki xatboshi.</li>
        <li><b>M</b>isol – maktab, dars yoki o‘z tajribangizdan.</li>
        <li><b>A</b>hamiyat – nega muhim; ↔ bog‘liq savoldan bir fikr.</li>
        <li><b>X</b>ulosa – o‘z fikringiz bilan yakunlang.</li>
      </ol>
      <p class="note">Kod 5 harfli bo‘lsa, javob kamida 7 xatbosh bo‘ladi: ta’rif + 5 harf + xulosa. Qisqa kod shu yo‘l bilan uzun javobga aylanadi.</p>
    </div>
  </div>
  <div class="cv-foot">Baholash: eng yuqori ball – 100, saralash bali – 56 · 56–70 qoniqarli · 71–85 yaxshi · 86–100 a’lo. «Darslikdan tekshiring» belgisi bor savollarni o‘z darsligingiz bilan solishtiring.</div>
</section>"""

CSS = (ROOT / "style.css").read_text(encoding="utf-8")

def build():
    sections = load()
    probs = check(sections)
    if probs:
        print("\n".join(probs))
        sys.exit(1)
    body = [cover_html(sections), tree_html(sections)]
    for s in sections:
        body.append(section_html(s))
        if s["n"] == 2:
            body.append(timeline_html())
    body.append(numbers_html())
    doc = f"""<!DOCTYPE html>
<html lang="uz"><head><meta charset="utf-8">
<title>13.00.02 – Yodlash sxemasi</title>
<style>{CSS}</style></head>
<body>{''.join(body)}</body></html>"""
    out = ROOT / "out" / "sxema.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    print("items:", sum(len(s["items"]) for s in sections), "->", out)

if __name__ == "__main__":
    build()
