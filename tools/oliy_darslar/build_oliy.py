#!/usr/bin/env python3
"""Oliy ta'lim amaliy darslari: BMKN (1 kurs — 10 dars, 2 kurs — 15 dars) va Ehtimollar nazariyasi (4 kurs, rus — 23 dars).

Mavzu bo'laklari: bolaklar/<guruh>/<kod>.txt. Bitta dars — bitta yoki bir nechta bo'lak (1 kursda ikki mavzu bitta darsda).
Bo'lak formati:
  ### U01 | Sarlavha
  @kirish                      — tarixiy, qiziq boshlanish: «| » satrlar doskaga, qolgani o'qituvchi gapi
  @qadam Sarlavha              — tushuncha qadami (doska buyruqlari: QOIDA, BELGILA, SON_OQI, KASR_MODEL, DOIRA_KASR, QISQART,
                                 USTUN, BOLISH, CHIZ, GRAFIK, KETMA, ISH, VENN, DARAXT, ORIN_ALMASH, ORINLASHTIR, GURUHLASH,
                                 SXEMA, ZANJIR, JADVAL, KOD; formula: $\\frac{3}{8}$)
  @sodda / @tekshiruv Savol? => to'g'ri | xato | xato
  @misol Sarlavha              — ishlangan misol: keyingi satrlar — shart; «@yechim» dan keyin «doska || ovoz» qadamlari
  @masala Sarlavha             — tanlanadigan mashq: shart, A) … D), = B, «@yechim», ixtiyoriy «@maslahat»
  @esda                        — xulosa: «| » satrlar doskaga (QOIDA: …), qolgani gap
  @test oson|o'rta|qiyin       — dars oxiridagi Kabu testi (darsdagi misollardan farqli): savol, A) … D), = B, «B: izoh», «? izoh»

python3 build_oliy.py bmkn1|bmkn2|ehtimol …  → out/<kurs>_paket.zip
"""
import glob, io, json, os, random, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)
from modules.ai_miya_varoq import template_workbook, parse_sheets   # noqa: E402

L = "ABCDEF"
BMKN_FAN = "Boshlang‘ich matematika kursi nazariyasi"
EHT_FAN = "Ehtimollar nazariyasi va matematik statistika (izoh: rus)"

# 1 kurs (kechki dastur, M1–M10): ba'zi darslarda ikki mavzu
BMKN1 = [
    ("Ratsional sonlar va o‘nli kasrlar", ["U01", "U02"]),
    ("Ko‘phadlar va haqiqiy sonlar", ["U03", "U04"]),
    ("Kompleks sonlar va trigonometrik shakl", ["U05", "U06"]),
    ("Geometriya elementlari", ["U07"]),
    ("Uchburchak va tenglik alomatlari", ["U08", "U09"]),
    ("To‘rtburchak, kvadrat, aylana va doira", ["U10"]),
    ("Parallelogramm, romb, trapetsiya", ["U11"]),
    ("Ko‘pyoqlar", ["U12"]),
    ("Aylanish jismlari", ["U13"]),
    ("Miqdorlar va matnli masalalar", ["U14", "U15"]),
]
KURSLAR = {
    "bmkn1": {"fan": BMKN_FAN, "sinf": "1 kurs", "kod": "BMKN-1K", "pref": "BMA", "til": "uz", "guruh": "bmkn",
              "darslar": BMKN1, "fayl": "BMKN_1-kurs"},
    "bmkn2": {"fan": BMKN_FAN, "sinf": "2 kurs", "kod": "BMKN-2K", "pref": "BMB", "til": "uz", "guruh": "bmkn",
              "darslar": None, "fayl": "BMKN_2-kurs"},
    "ehtimol": {"fan": EHT_FAN, "sinf": "4 kurs", "kod": "EHT-4K-RU", "pref": "EHR", "til": "ru", "guruh": "ehtimol",
                "darslar": None, "fayl": "Ehtimollar_4-kurs_rus"},
}
SOZ = {
    "uz": {"esda": "Esda tut", "test": "Test", "qism": "{n}-qism", "dars": "{n}-dars. {nom}", "salom": "Assalomu alaykum!"},
    "ru": {"esda": "Запомни", "test": "Тест", "qism": "Часть {n}", "dars": "Занятие {n}. {nom}", "salom": "Здравствуйте!"},
}
DARAJA = {"oson": 0, "o'rta": 1, "orta": 1, "qiyin": 2, "лёгкий": 0, "средний": 1, "сложный": 2}


def uz(s):
    """o' g' → o‘ g‘ (lotin), qolgan ' → ’; $…$ formulalar va kirill matnga tegilmaydi."""
    def bir(t):
        t = re.sub(r"([OoGg])'", lambda m: m.group(1) + "‘", t)
        return t.replace("'", "’")
    def mat(t):   # formulada kirill harflar \text{} ichida bo'lsin (KaTeX matematik rejimida kirillni yozmaydi)
        bol = re.split(r"(\\text\{[^{}]*\})", t)
        return "".join(b if b.startswith("\\text{") else re.sub(r"[А-Яа-яЁё]+(?:[ \-][А-Яа-яЁё]+)*", lambda m: "\\text{" + m.group(0) + "}", b) for b in bol)
    qism = re.split(r"(\$[^$]*\$)", str(s or ""))
    return "".join(mat(q) if q.startswith("$") else bir(q) for q in qism)


def gap(lines):
    return uz(" ".join(x.strip() for x in lines if x.strip()))


# ───────────────────────── bo'lak fayli ─────────────────────────
def yangi_bolak(kod, nom):
    return {"kod": kod, "nom": nom, "kirish": {"doska": [], "matn": []}, "qadamlar": [], "misollar": [], "masalalar": [],
            "esda": {"doska": [], "matn": []}, "testlar": [], "reja": [], "natija": [], "bbb": {"bilaman": [], "savol": [], "bildim": []},
            "blits": [], "hujum": [], "klaster": [], "loyiha": [], "keys": [], "k4": [], "sinkveyn": []}


def birlashtir(bolak, qism):
    """«### U01 +» kengaytmasi asosiy bo'lakka qo'shiladi (interfaol metod bloklari)."""
    for k, v in qism.items():
        if k in ("kod", "nom", "kengaytma"):
            continue
        if isinstance(v, list):
            bolak[k] += v
        elif k == "bbb":
            for kk in v:
                bolak["bbb"][kk] += v[kk]
        elif isinstance(v, dict):
            for kk in v:
                bolak[k][kk] += v[kk]


def parse(path):
    out, u, blk, obj = {}, None, None, None
    for n, raw in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
        line = raw.rstrip()
        m = re.match(r"^###\s+(\S+)\s*(?:\|\s*(.+?)|(\+))\s*$", line)
        if m:
            kod = m.group(1) + ("+" if m.group(3) else "")
            u = out[kod] = yangi_bolak(m.group(1), m.group(2) or "")
            u["kengaytma"] = bool(m.group(3))
            blk = obj = None
            continue
        if u is None or (not line.strip() and blk is None):
            continue
        m = re.match(r"^@(\w+)\s*(.*)$", line)
        if m:
            tur, arg = m.group(1), m.group(2).strip()
            if tur in ("reja", "natija", "sinkveyn"):
                blk, obj = "royxat", u[tur]
            elif tur == "bbb":
                blk, obj = "bbb", u["bbb"]
            elif tur in ("blits", "hujum", "klaster", "loyiha"):
                obj = {"sarlavha": arg, "doska": [], "matn": [], "sodda": [], "tekshiruv": ""}
                u[tur].append(obj); blk = "dm"
            elif tur in ("keys", "k4"):
                obj = {"sarlavha": arg, "shart": [], "variantlar": [], "javob": "", "yechim": [], "maslahat": [], "qiyinlik": "o'rta"}
                u[tur].append(obj); blk = "shart"
            elif tur == "kirish":
                blk, obj = "dm", u["kirish"]
            elif tur == "qadam":
                obj = {"sarlavha": arg, "doska": [], "matn": [], "sodda": [], "tekshiruv": ""}
                u["qadamlar"].append(obj); blk = "dm"
            elif tur == "sodda":
                blk = "sodda"
            elif tur == "tekshiruv":
                obj["tekshiruv"] = arg; blk = None
            elif tur in ("misol", "masala"):
                obj = {"sarlavha": arg, "shart": [], "variantlar": [], "javob": "", "yechim": [], "maslahat": [], "qiyinlik": "o'rta" if tur == "misol" else "oson"}
                u["misollar" if tur == "misol" else "masalalar"].append(obj); blk = "shart"
            elif tur == "yechim":
                blk = "yechim"
            elif tur == "maslahat":
                blk = "maslahat"
            elif tur == "esda":
                blk, obj = "dm", u["esda"]
            elif tur == "test":
                obj = {"daraja": arg or "oson", "savol": [], "variantlar": [], "javob": "", "xato": {}, "izoh": ""}
                u["testlar"].append(obj); blk = "test"
            else:
                raise ValueError(f"{path}:{n}: noma'lum blok @{tur}")
            continue
        if blk is None or not line.strip():
            continue
        s = line.strip()
        if blk == "royxat":
            obj.append(s.lstrip("-•").strip())
            continue
        if blk == "bbb":
            mb = re.match(r"^(bilaman|savol|bildim|знаю|хочу|узнал)\s*:\s*(.+)$", s, re.I)
            if mb:
                k = {"bilaman": "bilaman", "знаю": "bilaman", "savol": "savol", "хочу": "savol"}.get(mb.group(1).lower(), "bildim")
                obj[k].append(mb.group(2).strip())
            continue
        if blk == "dm":
            (obj["doska"] if line.startswith("|") else obj["matn"]).append(line.lstrip("|").strip())
        elif blk == "sodda":
            obj["sodda"].append(s)
        elif blk == "shart":
            mv, mj = re.match(r"^([A-F])\)\s*(.+)$", s), re.match(r"^=\s*([A-F])$", s)
            if mv:
                obj["variantlar"].append(mv.group(2))
            elif mj:
                obj["javob"] = mj.group(1)
            else:
                obj["shart"].append(s)
        elif blk == "yechim":
            obj["yechim"].append(s)
        elif blk == "maslahat":
            obj["maslahat"].append(s)
        elif blk == "test":
            mv, mj, mx = re.match(r"^([A-F])\)\s*(.+)$", s), re.match(r"^=\s*([A-F])$", s), re.match(r"^([A-F]):\s*(.+)$", s)
            if mv:
                obj["variantlar"].append(mv.group(2))
            elif mj:
                obj["javob"] = mj.group(1)
            elif mx:
                obj["xato"][mx.group(1)] = mx.group(2)
            elif s.startswith("?"):
                obj["izoh"] = s[1:].strip()
            else:
                obj["savol"].append(s)
    return out


def tekshir(u, test_kerak=10, interfaol=True, kurs_til="uz"):
    xs, k = [], u["kod"]
    if not u["kirish"]["matn"]:
        xs.append("kirish gapi yo'q")
    if len(u["qadamlar"]) < 3:
        xs.append(f"qadamlar {len(u['qadamlar'])} ta (kamida 3)")
    for q in u["qadamlar"]:
        if not q["matn"] or not q["doska"]:
            xs.append(f"qadam «{q['sarlavha']}»: matn yoki doska yo'q")
        if len(gap(q["matn"])) > 1400:
            xs.append(f"qadam «{q['sarlavha']}»: gap uzun")
    if not u["misollar"]:
        xs.append("ishlangan misol yo'q")
    for m in u["misollar"]:
        if not m["shart"] or not m["yechim"]:
            xs.append(f"misol «{m['sarlavha']}»: shart yoki yechim yo'q")
    if len(u["masalalar"]) < 2:
        xs.append(f"tanlanadigan masalalar {len(u['masalalar'])} ta (kamida 2)")
    for m in u["masalalar"]:
        n = len(m["variantlar"])
        if not m["shart"] or n < 3 or not m["javob"] or ord(m["javob"]) - 65 >= n or not m["yechim"]:
            xs.append(f"masala «{m['sarlavha']}»: shart/variant/javob/yechim xato")
    if not u["esda"]["doska"]:
        xs.append("esda doskasi yo'q")
    if len(u["testlar"]) < test_kerak:
        xs.append(f"testlar {len(u['testlar'])} ta (kamida {test_kerak})")
    for i, t in enumerate(u["testlar"], 1):
        n = len(t["variantlar"])
        if n < 3 or not t["javob"] or ord(t["javob"]) - 65 >= n:
            xs.append(f"test {i}: variant/javob xato")
        if len({v.strip().lower() for v in t["variantlar"]}) != n:
            xs.append(f"test {i}: bir xil variantlar")
        if not t["izoh"] or not t["savol"]:
            xs.append(f"test {i}: savol yoki izoh yo'q")
        if any(x not in L[:n] or x == t["javob"] for x in t["xato"]):
            xs.append(f"test {i}: xato izohi noto'g'ri harfga")
    if interfaol:
        for key, kerak in (("reja", 3), ("natija", 2), ("hujum", 1), ("klaster", 1), ("keys", 1), ("k4", 3), ("loyiha", 1)):
            if len(u[key]) < kerak:
                xs.append(f"interfaol: {key} {len(u[key])} ta (kamida {kerak})")
        if any(not u["bbb"][k] for k in ("bilaman", "savol", "bildim")):
            xs.append("interfaol: BBB to'liq emas")
        if len(u["sinkveyn"]) != 5:
            xs.append(f"interfaol: sinkveyn {len(u['sinkveyn'])} qator (5 kerak)")
        if kurs_til == "ru" and not u["blits"]:
            xs.append("interfaol: blits-razminka yo'q")
        for q in u["hujum"] + u["klaster"] + u["loyiha"] + u["blits"]:
            if not q["matn"] or not q["doska"] or not q["tekshiruv"]:
                xs.append(f"interfaol qadam «{q['sarlavha']}»: matn/doska/tekshiruv yo'q")
        for m in u["keys"] + u["k4"]:
            n = len(m["variantlar"])
            if not m["shart"] or n < 3 or not m["javob"] or ord(m["javob"]) - 65 >= n or not m["yechim"]:
                xs.append(f"interfaol masala «{m['sarlavha']}»: shart/variant/javob/yechim xato")
            if len({v.strip().lower() for v in m["variantlar"]}) != n:
                xs.append(f"interfaol masala «{m['sarlavha']}»: bir xil variantlar")
    darsda = {gap(m["shart"]).lower() for m in u["misollar"] + u["masalalar"] + u["keys"] + u["k4"]}
    for i, t in enumerate(u["testlar"], 1):
        if gap(t["savol"]).lower() in darsda:
            xs.append(f"test {i}: darsdagi misol bilan bir xil")
    return [f"{k}: {x}" for x in xs]


# ───────────────────────── javob harflarini teng taqsimlash ─────────────────────────
class Nishon:
    def __init__(self, urugh):
        self.r, self.navbat = random.Random(urugh), []

    def keyingi(self):
        if not self.navbat:
            self.navbat = [0, 1, 2, 3]
            self.r.shuffle(self.navbat)
        return self.navbat.pop()


def aralashtir(variantlar, javob, xato, yangi):
    n = len(variantlar)
    eski = L.index(javob)
    yangi = yangi % n
    qolgan = [k for k in range(n) if k != eski]
    tartib = qolgan[:yangi] + [eski] + qolgan[yangi:]
    harf = {L[o]: L[i] for i, o in enumerate(tartib)}
    return [variantlar[k] for k in tartib], L[yangi], {harf[k]: v for k, v in xato.items()}


# ───────────────────────── dars qatorlari ─────────────────────────
MET = {
    "uz": {
        "q1": "I qism · Interfaol ma'ruza: reja va o'quv natijalari",
        "q1_matn": "Darsimiz ikki qismdan iborat: avval interfaol ma'ruza, keyin amaliy mashg'ulot. [1] Ma'ruza rejasi: {reja}. [2] Dars yakunida siz {natija}.",
        "reja": "Ma'ruza rejasi", "natija": "O'quv natijalari",
        "bbb": "BBB jadvali: Bilaman — Bilishni xohlayman — Bildim", "bbb_ust": "Bilaman | Bilishni xohlayman | Bildim",
        "bbb_matn": "Interfaol usul — BBB jadvali. [1] Birinchi ustunda mavzu bo'yicha oldindan bilganlarimiz, ikkinchisida — bugun javob topmoqchi bo'lgan savollarimiz. Uchinchi ustun hozircha bo'sh: uni dars oxirida birga to'ldiramiz. Har bir savolga javobni hozirdan taxmin qilib turing.",
        "q2": "II qism · Amaliy mashg'ulot",
        "q2_matn": "Endi ikkinchi qism — amaliy mashg'ulot. [1] Avval namunaviy misollarni birga tahlil qilamiz, keyin mashqlarni o'zingiz bajarasiz. So'ng hayotiy STEAM keys, 4K topshiriqlari — tanqidiy fikrlash, kommunikatsiya va kreativlik — hamda jamoaviy mini-loyiha. Yakunda Kabu test.",
        "q2_doska": "ZANJIR: Namuna :: birga tahlil | Mashq :: mustaqil | Keys :: STEAM | 4K :: fikrlash | Loyiha :: hamkorlik | Test :: Kabu",
        "bbb2": "BBB jadvali: Bildim",
        "bbb2_matn": "BBB jadvaliga qaytamiz. [1] Endi uchinchi ustun to'ldi — bugun nimani bildik. Dars boshidagi savollaringizga javob topildimi? Solishtiring: bu sizning bugungi o'sishingiz.",
        "sink": "Refleksiya: sinkveyn", "sink_qator": ["Mavzu", "Ikki sifat", "Uch fe'l", "Fikr", "Mohiyat"],
        "sink_matn": "Darsni sinkveyn bilan yakunlaymiz — besh qatorli qisqa she'r. [1] Birinchi qator — mavzu: {0}. [2] Ikkinchi — ikki sifat: {1}. [3] Uchinchi — uch fe'l: {2}. [4] To'rtinchi — mavzu haqida fikr: {3}. [5] Beshinchi — bir so'z bilan mohiyat: {4}. Endi daftaringizda o'z sinkveyningizni tuzing.",
    },
    "ru": {
        "q1": "Практическое занятие: цель и план",
        "q1_matn": "Сегодня практическое занятие: немного теории, вывод формулы и много практики. [1] План: {reja}. [2] Результат занятия: вы {natija}.",
        "reja": "План занятия", "natija": "Результаты",
        "bbb": "Таблица ЗХУ: Знаю — Хочу узнать — Узнал", "bbb_ust": "Знаю | Хочу узнать | Узнал",
        "bbb_matn": "Интерактивный метод — таблица ЗХУ. [1] В первой колонке то, что мы уже знаем, во второй — вопросы, на которые сегодня ищем ответ. Третья колонка пока пуста: заполним её в конце занятия. Попробуйте заранее предположить ответы.",
        "q2": "Практикум",
        "q2_matn": "Переходим к практикуму. [1] Сначала разберём образцы решений, затем вы решите задачи сами. Потом — кейс STEAM, задания 4К на критическое мышление, коммуникацию и креативность, и мини-проект для команды. В конце — тест Kabu.",
        "q2_doska": "ZANJIR: Образец :: разбор | Задачи :: сами | Кейс :: STEAM | 4К :: мышление | Проект :: команда | Тест :: Kabu",
        "bbb2": "Таблица ЗХУ: Узнал",
        "bbb2_matn": "Вернёмся к таблице ЗХУ. [1] Третья колонка заполнена — что мы узнали сегодня. Сравните с вопросами из начала занятия: на все ли нашёлся ответ?",
        "sink": "Рефлексия: синквейн", "sink_qator": ["Тема", "Два прилагательных", "Три глагола", "Фраза", "Суть"],
        "sink_matn": "Завершим занятие синквейном — пятистрочным стихотворением. [1] Первая строка — тема: {0}. [2] Вторая — два прилагательных: {1}. [3] Третья — три глагола: {2}. [4] Четвёртая — фраза о теме: {3}. [5] Пятая — одно слово-суть: {4}. Составьте свой синквейн в тетради.",
    },
}


def _qadam_qator(q):
    r = {"turi": "tushuncha", "sarlavha": uz(q["sarlavha"]), "matn": gap(q["matn"]), "doska": "\n".join(uz(x) for x in q["doska"])}
    if q["sodda"]:
        r["sodda"] = gap(q["sodda"])
    if q["tekshiruv"]:
        r["tekshiruv"] = uz(q["tekshiruv"])
    return r


def _tanlov_qator(m, kod, nishon):
    v, j_, _ = aralashtir(m["variantlar"], m["javob"], {}, nishon.keyingi())
    return {"turi": "masala", "kod": kod, "sarlavha": uz(m["sarlavha"]), "matn": gap(m["shart"]),
            "variantlar": "\n".join(f"{L[k]}) {uz(x)}" for k, x in enumerate(v)), "javob": j_,
            "yechim": "\n".join(uz(x) for x in m["yechim"]), "maslahat": "\n".join(uz(x) for x in m["maslahat"]),
            "qiyinlik": m["qiyinlik"]}


def _bbb_jadval(B, ust, toldirilgan):
    n = min(9, max(len(B["bilaman"]), len(B["savol"]), len(B["bildim"])))
    ol = lambda xs, i: uz(xs[i]) if i < len(xs) else ""
    qator = [f"{ol(B['bilaman'], i)} | {ol(B['savol'], i)} | {ol(B['bildim'], i) if toldirilgan else ('?' if i < len(B['bildim']) else '')}"
             for i in range(n)]
    return "JADVAL: " + ust + " ;; " + " ;; ".join(qator)


def dars_qatorlari(bolaklar, nom, raqam, kurs, nishon, test_soni):
    til = kurs["til"]
    S, M = SOZ[til], MET[til]
    rows = []
    bir, oxirgi = bolaklar[0], bolaklar[-1]
    kir_doska = [uz(x) for x in bir["kirish"]["doska"]]
    if len(bolaklar) > 1:
        kir_doska.append("Reja: " + " · ".join(f"[k]{i}[/k] {uz(b['nom'])}" for i, b in enumerate(bolaklar, 1)))
    rows.append({"turi": "kirish", "sarlavha": uz(nom), "matn": gap(bir["kirish"]["matn"]), "doska": "\n".join(kir_doska)})
    # ── reja va o'quv natijalari; BBB (ZXU) jadvali ──
    reja = [x for b in bolaklar for x in b["reja"]]
    natija = [x for b in bolaklar for x in b["natija"]]
    if reja:
        doska = [f"[s]{uz(M['reja'])}[/s]"] + [f"[k]{i}[/k] {uz(x)}" for i, x in enumerate(reja, 1)]
        doska += [f"[y]{uz(M['natija'])}[/y]"] + [f"• {uz(x)}" for x in natija]
        rows.append({"turi": "tushuncha", "sarlavha": uz(M["q1"]), "doska": "\n".join(doska),
                     "matn": uz(M["q1_matn"].format(reja="; ".join(reja), natija="; ".join(natija)))})
    B = {k: [x for b in bolaklar for x in b["bbb"][k]] for k in ("bilaman", "savol", "bildim")}
    if B["bilaman"]:
        rows.append({"turi": "tushuncha", "sarlavha": uz(M["bbb"]), "doska": _bbb_jadval(B, M["bbb_ust"], False), "matn": uz(M["bbb_matn"])})
    # ── I qism: nazariya (interfaol ma'ruza / qisqa nazariya) ──
    for j, b in enumerate(bolaklar):
        if j:   # ikkinchi mavzu — o'z kirishi bilan alohida qadam
            rows.append({"turi": "tushuncha", "sarlavha": uz(S["qism"].format(n=j + 1) + ": " + b["nom"]),
                         "matn": gap(b["kirish"]["matn"]), "doska": "\n".join(uz(x) for x in b["kirish"]["doska"])})
        for q in b["blits"] + b["hujum"] + b["qadamlar"] + b["klaster"]:
            rows.append(_qadam_qator(q))
    # ── II qism: amaliy mashg'ulot ──
    if reja:
        rows.append({"turi": "tushuncha", "sarlavha": uz(M["q2"]), "matn": uz(M["q2_matn"]), "doska": uz(M["q2_doska"])})
    mi = si = 0
    for b in bolaklar:
        for m in b["misollar"]:
            mi += 1
            rows.append({"turi": "misol", "kod": f"M{mi:02d}", "sarlavha": uz(m["sarlavha"]), "matn": gap(m["shart"]),
                         "yechim": "\n".join(uz(x) for x in m["yechim"]), "javob": "", "qiyinlik": m["qiyinlik"]})
    for b in bolaklar:
        for m in b["masalalar"]:
            si += 1
            rows.append(_tanlov_qator(m, f"S{si:02d}", nishon))
    k4 = bir["k4"] if len(bolaklar) == 1 else bir["k4"][:1] + oxirgi["k4"][1:]
    for m in [x for b in bolaklar for x in b["keys"]] + k4:
        si += 1
        rows.append(_tanlov_qator(m, f"S{si:02d}", nishon))
    for q in oxirgi["loyiha"]:
        rows.append(_qadam_qator(q))
    if B["bildim"]:
        rows.append({"turi": "tushuncha", "sarlavha": uz(M["bbb2"]), "doska": _bbb_jadval(B, M["bbb_ust"], True), "matn": uz(M["bbb2_matn"])})
    if len(oxirgi["sinkveyn"]) == 5:
        sk = [uz(x) for x in oxirgi["sinkveyn"]]
        rows.append({"turi": "tushuncha", "sarlavha": uz(M["sink"]), "matn": uz(M["sink_matn"].format(*sk)),
                     "doska": "\n".join(f"[k]{i}[/k] [y]{uz(M['sink_qator'][i - 1])}:[/y] {x}" for i, x in enumerate(sk, 1))})
    esda_d = [uz(x) for b in bolaklar for x in b["esda"]["doska"]]
    rows.append({"turi": "xulosa", "sarlavha": S["esda"], "doska": "\n".join(esda_d),
                 "matn": gap([x for b in bolaklar for x in b["esda"]["matn"]])})
    har = max(1, test_soni // len(bolaklar))
    testlar = []
    for j, b in enumerate(bolaklar):
        olinadi = har if j < len(bolaklar) - 1 else test_soni - har * (len(bolaklar) - 1)
        testlar += sorted(b["testlar"], key=lambda t: DARAJA.get(t["daraja"], 1))[:olinadi]
    testlar.sort(key=lambda t: DARAJA.get(t["daraja"], 1))
    for i, t in enumerate(testlar, 1):
        v, j_, xato = aralashtir(t["variantlar"], t["javob"], t["xato"], nishon.keyingi())
        rows.append({"turi": "test", "kod": f"T{i:02d}", "sarlavha": f"{S['test']} {i}", "matn": gap(t["savol"]),
                     "variantlar": "\n".join(f"{L[k]}) {uz(x)}" for k, x in enumerate(v)), "javob": j_, "yechim": uz(t["izoh"]),
                     "xato_izohi": "\n".join(f"{k} => {uz(x)}" for k, x in sorted(xato.items())),
                     "qiyinlik": "oson" if DARAJA.get(t["daraja"], 1) == 0 else "qiyin" if DARAJA.get(t["daraja"], 1) == 2 else "o'rta"})
    return rows


def mavzular_xlsx(qatorlar, path, kurs):
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Mavzular"
    ws.append(["Sinf", "Fan", "Chorak", "Bob", "Bo'lim", "Mavzu", "Kichik mavzu"])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="173B57")
    for bob, nom in qatorlar:
        ws.append([kurs["sinf"], kurs["fan"], "1", bob, bob, nom, ""])
    for col, w in zip("ABCDEFG", (10, 50, 8, 30, 30, 70, 10)):
        ws.column_dimensions[col].width = w
    wb.save(path)


def main(kalitlar):
    import openpyxl
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    natijalar = []
    for kalit in kalitlar:
        kurs = KURSLAR[kalit]
        bolak = {}
        kengaytmalar = []
        for f in sorted(glob.glob(os.path.join(HERE, "bolaklar", kurs["guruh"], "*.txt"))):
            for k, v in parse(f).items():
                if v.get("kengaytma"):
                    kengaytmalar.append(v)
                    continue
                if k in bolak:
                    raise ValueError(f"{k} ikki marta")
                bolak[k] = v
        for v in kengaytmalar:
            if v["kod"] not in bolak:
                raise ValueError(f"{v['kod']} + : asosiy bo'lak yo'q")
            birlashtir(bolak[v["kod"]], v)
        darslar = kurs["darslar"] or [(b["nom"], [k]) for k, b in sorted(bolak.items())]
        xatolar, pre, mavzular = [], [], []
        nishon = Nishon(kalit)
        for i, (nom, kodlar) in enumerate(darslar, 1):
            yoq = [k for k in kodlar if k not in bolak]
            if yoq:
                xatolar.append(f"{i}-dars: bo'lak yozilmagan {yoq}")
                continue
            bs = [bolak[k] for k in kodlar]
            for b in bs:
                xatolar += tekshir(b, 10 if len(bs) == 1 else 5, kurs_til=kurs["til"])
            dnom = SOZ[kurs["til"]]["dars"].format(n=i, nom=uz(nom))
            pre.append({"mavzu_kodi": "", "mavzu_nomi": dnom, "mavzu_raqami": str(i), "rows": dars_qatorlari(bs, dnom, i, kurs, nishon, 10)})
            mavzular.append((uz(kurs["fan"].split(" (izoh")[0]), dnom))
        if not pre:
            print(f"{kalit}: dars yo'q"); continue
        book = {"kitob_nomi": f"{uz(kurs['fan'])} · {kurs['sinf']} (amaliy darslar)", "fan": kurs["fan"], "sinf": kurs["sinf"],
                "kitob_kodi": kurs["kod"], "til": kurs["til"], "kod_prefiksi": kurs["pref"], "mualliflar": "Kabutar Ta’lim"}
        wb = template_workbook(prefill=pre, book=book)
        mp = os.path.join(out, f"{kurs['fayl']}_mavzular.xlsx")
        mavzular_xlsx(mavzular, mp, kurs)
        yp = os.path.join(out, f"{kurs['fayl']}_ai_miya.xlsx")
        wb.save(yp)
        r = parse_sheets(openpyxl.load_workbook(yp))
        errs = r.get("errors") or []
        sm = r.get("summary") or {}
        print(f"{kalit}: {len(pre)} dars; parse xato {len(errs)}, ogoh {len(r.get('warnings') or [])}; testlar {sm.get('testlar')}")
        for e in errs[:10]:
            print("   XATO:", e)
        for x in xatolar:
            print("   TEKSHIRUV:", x)
        doska = []
        for d in pre:
            for r in d["rows"]:
                for x in (r.get("doska") or "").split("\n"):
                    if x.strip():
                        doska.append([d["mavzu_nomi"][:40] + " / " + r.get("sarlavha", "")[:40], x])
                for x in (r.get("yechim") or "").split("\n"):
                    x = x.split("||")[0].strip()
                    if x and r["turi"] in ("misol", "masala"):
                        doska.append([d["mavzu_nomi"][:40] + " / " + r.get("sarlavha", "")[:40], x])
        jp = os.path.join(out, f"{kalit}_doska.json")
        json.dump(doska, open(jp, "w"), ensure_ascii=False)
        os.system(f"node /tmp/chk_mat.mjs {jp} | tail -25")
        zp = os.path.join(out, f"{kurs['fayl']}_paket.zip")
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
            for f in (mp, yp):
                z.write(f, os.path.join(kurs["fayl"], os.path.basename(f)))
        natijalar.append((kalit, zp, len(pre), xatolar, errs))
    return natijalar


if __name__ == "__main__":
    main(sys.argv[1:] or ["bmkn1", "bmkn2"])
