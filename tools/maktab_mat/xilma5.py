"""REV508: 5-sinf matematika — har mavzuga MA'NOSI BILAN FARQ QILADIGAN misollar (faqat sonlar almashgan bitta shablon emas).
Har oila (mavzu turkumi) 6–10 xil topshiriq turiga ega: hisoblash, hayotiy masala, teskari savol, xatoni top, taqqoslash,
chamalash, ikki bosqichli masala va h.k. Har tur → (shart, javob, yechim, xato_variantlar)."""
import random
from fractions import Fraction as F

ISM = ["Ali", "Malika", "Bekzod", "Dilnoza", "Sardor", "Zarina", "Jasur", "Madina", "Otabek", "Nigora"]
SHAHAR = ["Samarqand", "Buxoro", "Xiva", "Namangan", "Qarshi", "Termiz", "Andijon", "Nukus"]


def _s(n):
    return f"{n:,}".replace(",", " ")


def kf(f):
    f = F(f)
    if f.denominator == 1:
        return str(f.numerator)
    if abs(f) > 1:
        b = int(f); q = f - b
        return f"{b}\\tfrac{{{q.numerator}}}{{{q.denominator}}}"
    return f"\\frac{{{f.numerator}}}{{{f.denominator}}}"


def dk(x):
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


# ───────────── oilalar ─────────────
def o_sonlar(r):
    """Ko'p xonali sonlar: sinflar, o'qish/yozish, taqqoslash, yaxlitlash."""
    n = r.randint(1_200_000, 9_899_999); k = r.randint(0, 2); m = n + r.choice([-1, 1]) * r.choice([90_000, 9_000, 900])
    d = r.randint(12, 90) * 1000; sh = r.choice(SHAHAR); ds = r.sample(range(1, 10), 6); m2 = r.randint(1_000_000, 2_900_000)
    turlar = [
        lambda: (f"${_s(n)}$ sonida nechta minglik bor?", n // 1000, f"Minglar sinfi va undan yuqori: ${_s(n)} = {_s(n // 1000)}$ ming ${_s(n % 1000)}$", [n // 1_000_000, (n // 1000) % 1000, n // 100]),
        lambda: (f"${_s(n)}$ sonidagi {['yuz minglar', 'o‘n minglar', 'minglar'][k]} xonasidagi raqam?", int(str(n)[1 + k]), f"Xonalar: millionlar, yuz minglar, o‘n minglar, minglar… → {int(str(n)[1 + k])}", [int(str(n)[k]), int(str(n)[2 + k]), int(str(n)[-1])]),
        lambda: (f"Qaysi son katta: ${_s(n)}$ yoki ${_s(m)}$? (kattasini yozing)", max(n, m), "Chapdan birinchi farq qiladigan xonani solishtiramiz.", [min(n, m), n + m]),
        lambda: (f"${_s(n)}$ sonini **minglargacha** yaxlitlang.", round(n, -3), f"Yuzlar raqami {str(n)[-3]}: {'5 va undan katta — yuqoriga' if int(str(n)[-3]) >= 5 else '5 dan kichik — pastga'}.", [n // 1000 * 1000 + (0 if round(n, -3) != n // 1000 * 1000 else 1000), round(n, -2), round(n, -4)]),
        lambda: (f"{sh} aholisi ${_s(n)}$ kishi. Yil davomida ${_s(d)}$ kishiga ko‘paydi. Endi necha kishi?", n + d, f"${_s(n)} + {_s(d)} = {_s(n + d)}$", [n - d, n + d * 10, n + d // 10]),
        lambda: (f"${', '.join(str(x) for x in ds)}$ raqamlaridan (har biri bir marta) tuzish mumkin bo‘lgan eng katta olti xonali son?", int(''.join(map(str, sorted(ds, reverse=True)))), "Eng katta raqamni eng katta xonaga qo‘yamiz.", [int(''.join(map(str, sorted(ds)))), int(''.join(map(str, ds)))]),
        lambda: (f"Ali ${_s(n)}$ dan keyingi sonni ${_s(n + 10)}$ deb yozdi. To‘g‘risi qaysi?", n + 1, "Keyingi son — 1 ga katta.", [n + 10, n - 1, n + 100]),
        lambda: (f"Taxminan: ${_s(n)} + {_s(m2)}$ necha millionga yaqin?", round((n + m2) / 1e6), "Har birini millionlargacha yaxlitlab qo‘shamiz.", [round(n / 1e6), round((n + m2) / 1e6) + 1]),
    ]
    return turlar


def o_kop10(r):
    """10, 100, 1000 ga va o'nlik, yuzlik, mingliklarga ko'paytirish va bo'lish."""
    a = r.randint(12, 980); k = r.choice([10, 100, 1000]); t = r.choice([20, 30, 40, 50, 60, 70, 80, 90, 200, 300, 400, 500])
    return [
        lambda: (f"${a} \\cdot {k}$", a * k, f"{k} da {len(str(k)) - 1} ta nol — songa shuncha nol qo‘shiladi.", [a * k // 10, a * k * 10, a + k]),
        lambda: (f"${a * k} : {k}$", a, f"Oxiridan {len(str(k)) - 1} ta nolni olib tashlaymiz.", [a * 10, a // 10 or 1, a * k]),
        lambda: (f"$? \\cdot {k} = {a * k}$", a, f"Noma’lum ko‘paytuvchi: ${a * k} : {k} = {a}$", [a * k, a * 10, a + k]),
        lambda: (f"${a} \\cdot {t}$", a * t, f"${a} \\cdot {t // 10 ** (len(str(t)) - 1)} = {a * (t // 10 ** (len(str(t)) - 1))}$, keyin {len(str(t)) - 1} ta nol.", [a * (t // 10), a * t * 10, a + t]),
        lambda: (f"Bitta quti {a} ta qalam sig‘adi. {k} ta qutiga nechta qalam?", a * k, f"${a} \\cdot {k} = {a * k}$", [a + k, a * k // 10]),
        lambda: (f"{a * k} so‘mni {k} kishiga teng bo‘lishdi. Har biriga necha so‘m?", a, f"${a * k} : {k} = {a}$", [a * 10, a * k]),
        lambda: (f"Malika: «${a} \\cdot {k} = {a}{'0' * (len(str(k)) - 2)}$». Xatosini tuzating — to‘g‘ri javob?", a * k, f"{k} da {len(str(k)) - 1} ta nol bor, Malika bitta nolni unutgan.", [int(f"{a}{'0' * (len(str(k)) - 2)}") or a, a * k * 10]),
        lambda: (f"{a} m necha santimetr?", a * 100, "1 m = 100 sm, demak 100 ga ko‘paytiramiz.", [a * 10, a * 1000]),
        lambda: (f"Qaysi biri katta: ${a} \\cdot 100$ yoki ${a * 1000} : 10$? (kattasini yozing; teng bo‘lsa — shu son)", max(a * 100, a * 100), "Ikkalasi ham ${}$ — teng.".format(a * 100), [a * 10, a * 1000]),
    ]


def o_tartib(r):
    """Amallar tartibi (qavssiz va qavsli ifodalar)."""
    a, b, c, d = r.randint(12, 60), r.randint(2, 9), r.randint(3, 12), r.randint(2, 9)
    return [
        lambda: (f"${a} + {b} \\cdot {c}$", a + b * c, f"Avval ko‘paytirish: ${b} \\cdot {c} = {b * c}$, keyin ${a} + {b * c} = {a + b * c}$", [(a + b) * c, a + b + c]),
        lambda: (f"$({a} + {b}) \\cdot {c}$", (a + b) * c, f"Avval qavs: ${a + b}$, keyin ${a + b} \\cdot {c} = {(a + b) * c}$", [a + b * c, a * c + b]),
        lambda: (f"${a * d} : {d} - {b} \\cdot {min(c, 5)}$", a - b * min(c, 5), "Bo‘lish va ko‘paytirish avval, ayirish oxirida.", [(a * d // d - b) * min(c, 5), a + b * min(c, 5)]),
        lambda: (f"Jasur: «${a} + {b} \\cdot {c} = {(a + b) * c}$». To‘g‘ri javob?", a + b * c, "Jasur qo‘shishni avval bajargan, ko‘paytirish avval bo‘ladi.", [(a + b) * c, a * b + c]),
        lambda: (f"${a} + {b} \\cdot {c}$ ifodada qavsni qayerga qo‘ysak, natija ${(a + b) * c}$ bo‘ladi? (natijani yozing)", (a + b) * c, f"$({a} + {b}) \\cdot {c} = {(a + b) * c}$", [a + b * c]),
        lambda: (f"Do‘kondan {b} ta daftar ({c * 100} so‘mdan) va bitta ruchka ({a * 100} so‘m) olindi. Jami necha so‘m?", b * c * 100 + a * 100, f"${b} \\cdot {c * 100} + {a * 100} = {b * c * 100 + a * 100}$", [(b + 1) * c * 100, b * (c * 100 + a * 100)]),
        lambda: (f"$({a} - {b}) \\cdot {d} + {c}$", (a - b) * d + c, "Qavs → ko‘paytirish → qo‘shish.", [(a - b) * (d + c), a - b * d + c]),
        lambda: (f"Qaysi amal birinchi bajariladi: ${a} - {c} : {1 if c % 2 else 2} \\cdot {b}$? (1 — ayirish, 2 — bo‘lish, 3 — ko‘paytirish)", 2, "Ko‘paytirish va bo‘lish chapdan o‘ngga, qo‘shish va ayirishdan oldin: birinchi — bo‘lish.", [1, 3]),
    ]


def o_masala(r):
    """Sonlar ustida to'rt amalga matnli masalalar (har xil hayotiy holatlar)."""
    i1, i2 = r.sample(ISM, 2); a, b = r.randint(120, 480), r.randint(20, 90); n = r.randint(3, 9); v = r.randint(40, 80); t = r.randint(2, 6)
    return [
        lambda: (f"{i1}da {a} so‘m bor edi. U {n} ta konfet ({b} so‘mdan) oldi. Necha so‘m qoldi?", a * 10 - n * b, f"${a * 10} - {n} \\cdot {b} = {a * 10 - n * b}$", [a * 10 - b, n * b]) if a * 10 > n * b else (f"{i1} {n} ta daftar oldi, har biri {b} so‘m. Jami?", n * b, f"${n} \\cdot {b} = {n * b}$", [n + b]),
        lambda: (f"Avtobus soatiga {v} km yuradi. {t} soatda qancha yo‘l bosadi?", v * t, f"Yo‘l = tezlik × vaqt = ${v} \\cdot {t} = {v * t}$ km", [v + t, v * t * 10]),
        lambda: (f"{v * t} km yo‘lni mashina {t} soatda bosdi. Tezligi?", v, f"Tezlik = yo‘l : vaqt = ${v * t} : {t} = {v}$ km/soat", [v * t, v * t // 10]),
        lambda: (f"Sinfda {n * 4} o‘quvchi bor. Ularni {n} kishilik guruhlarga bo‘lishdi. Nechta guruh bo‘ldi?", 4, f"${n * 4} : {n} = 4$", [n, n * 4]),
        lambda: (f"{i1}da {a} ta marka bor, {i2}da undan {b} ta kam. Ikkalasida jami nechta?", a + a - b, f"{i2}da ${a} - {b} = {a - b}$; jami ${a} + {a - b} = {2 * a - b}$", [a + b, a - b]),
        lambda: (f"Bog‘da {a} tup daraxt bor: olma daraxtlari nokdan {b} ta ko‘p, nok — {(a - b) // 2 if (a - b) % 2 == 0 else (a - b + 1) // 2} ta. Olma daraxtlari nechta?", ((a - b) // 2 if (a - b) % 2 == 0 else (a - b + 1) // 2) + b, "Olma = nok + farq.", [b, a - b]),
        lambda: (f"{n * 7 + 3} ta olmani {n} ta savatga teng solishdi. Har savatda nechta, nechta ortib qoldi? (savatdagini yozing)", (n * 7 + 3) // n, f"${n * 7 + 3} = {n} \\cdot {(n * 7 + 3) // n} + {(n * 7 + 3) % n}$", [(n * 7 + 3) % n, n * 7]),
        lambda: (f"Pomidor 1 kg — {b * 100} so‘m, bodring 1 kg — {(b - 5) * 100} so‘m. 2 kg pomidor va 3 kg bodring necha so‘m?", 2 * b * 100 + 3 * (b - 5) * 100, "Har birining narxini topib, qo‘shamiz.", [5 * b * 100, 2 * b * 100]),
    ]


def o_kasr(r, tur="umumiy"):
    """Oddiy kasrlar: bo'lish kasr ko'rinishida, kasr↔o'nli, aralash sonlar, ko'paytirish, qismning qismi."""
    d = r.choice([2, 4, 5, 8, 10, 20, 25]); a = F(r.randint(1, d - 1), d); b = F(r.randint(1, 7), 8); n = r.randint(2, 9)
    p, q = r.randint(1, 3), r.randint(1, 3); x = F(r.randint(1, 3), 4) + p; y = F(r.randint(1, 3), 4) + q
    pirog = r.choice(["pirog", "tort", "shokolad", "non"])
    return [
        lambda: (f"${n * 3} : {n * 4}$ ni qisqartirilgan kasr ko‘rinishida yozing.", "3/4", f"$\\frac{{{n * 3}}}{{{n * 4}}} = \\frac{{3}}{{4}}$ (har ikkisi {n} ga bo‘lindi)", [f"{n * 3}/{n * 4}", "4/3"]),
        lambda: (f"${kf(a)}$ ni o‘nli kasrga aylantiring.", dk(float(a)), f"Maxrajni 10, 100 ga keltiramiz: ${kf(a)} = {dk(float(a))}$", [dk(float(a) * 10), dk(float(a) / 10)]),
        lambda: (f"${kf(x)} + {kf(y)}$", kf(x + y).replace("\\tfrac", ""), "Butun qismlarni va kasr qismlarni alohida qo‘shamiz.", [kf(x + y + 1).replace("\\tfrac", ""), kf(x * y).replace("\\tfrac", "")]),
        lambda: (f"${kf(a)} \\cdot {n}$", kf(a * n).replace("\\tfrac", ""), f"Suratni {n} ga ko‘paytiramiz: $\\frac{{{a.numerator * n}}}{{{a.denominator}}}$", [kf(F(a.numerator * n, a.denominator * n)).replace("\\tfrac", ""), kf(a + n).replace("\\tfrac", "")]),
        lambda: (f"${kf(a)} \\cdot {kf(b)}$", kf(a * b).replace("\\tfrac", ""), "Surat suratga, maxraj maxrajga ko‘paytiriladi.", [kf(F(a.numerator + b.numerator, a.denominator + b.denominator)).replace("\\tfrac", ""), kf(a + b).replace("\\tfrac", "")]),
        lambda: (f"{pirog.capitalize()}ning ${kf(a)}$ qismi yeyildi. Qolgan qismning yarmi mehmonga berildi. {pirog.capitalize()}ning qancha qismi mehmonga ketdi?", kf((1 - a) / 2).replace("\\tfrac", ""), f"Qolgan: $1 - {kf(a)} = {kf(1 - a)}$; uning yarmi: ${kf((1 - a) / 2)}$", [kf(a / 2).replace("\\tfrac", ""), kf(1 - a).replace("\\tfrac", "")]),
        lambda: (f"Qaysi biri katta: ${kf(a)}$ yoki ${kf(b)}$? (kattasini yozing)", kf(max(a, b)).replace("\\tfrac", ""), "Umumiy maxrajga keltirib, suratlarni solishtiramiz.", [kf(min(a, b)).replace("\\tfrac", "")]),
        lambda: (f"Zarina: «$\\frac{{1}}{{2}} + \\frac{{1}}{{3}} = \\frac{{2}}{{5}}$». To‘g‘ri javob?", "5/6", "Suratlarni va maxrajlarni qo‘shib bo‘lmaydi: $\\frac{3}{6} + \\frac{2}{6} = \\frac{5}{6}$", ["2/5", "2/6"]),
        lambda: (f"{n * 4} sm lentaning ${kf(F(3, 4))}$ qismi kesildi. Necha sm kesildi?", n * 3, f"${n * 4} : 4 \\cdot 3 = {n * 3}$ sm", [n * 4 - 3, n]),
    ]


def o_yuz(r):
    """Uchburchak yuzi va murakkab shakllar."""
    a, h = r.randint(4, 20) * 2, r.randint(3, 15); w, l = r.randint(3, 9), r.randint(6, 14)
    return [
        lambda: (f"Uchburchakning asosi {a} sm, balandligi {h} sm. Yuzi?", a * h // 2, f"$S = \\frac{{a \\cdot h}}{{2}} = \\frac{{{a} \\cdot {h}}}{{2}} = {a * h // 2}$ sm²", [a * h, a + h]),
        lambda: (f"Uchburchak yuzi {a * h // 2} sm², asosi {a} sm. Balandligi?", h, f"$h = \\frac{{2S}}{{a}} = \\frac{{{a * h}}}{{{a}}} = {h}$ sm", [a * h // 2 // a or 1, 2 * h]),
        lambda: (f"Bekzod uchburchak yuzini $S = {a} \\cdot {h} = {a * h}$ sm² deb topdi. Xatosi nima? To‘g‘ri javob?", a * h // 2, "Uchburchak yuzi to‘g‘ri to‘rtburchakning yarmi — 2 ga bo‘lish unutilgan.", [a * h]),
        lambda: (f"To‘g‘ri to‘rtburchakli bog‘ {l} m × {w} m. Uning burchagidan katetlari {w} m va {min(w, l) - 1} m bo‘lgan to‘g‘ri burchakli uchburchak shaklidagi gulzor ajratildi. Qolgan yuza?", l * w - w * (min(w, l) - 1) // 2 if w * (min(w, l) - 1) % 2 == 0 else l * w - w * (min(w, l) - 1) / 2, "To‘rtburchak yuzidan uchburchak yuzini ayiramiz.", [l * w, w * (min(w, l) - 1)]),
        lambda: (f"Asosi {a} sm va balandligi {h} sm bo‘lgan uchburchak bilan tomonlari {a} sm va {h} sm to‘g‘ri to‘rtburchakning yuzlari necha marta farq qiladi?", 2, "Uchburchak yuzi — to‘rtburchakning yarmi.", [1, 4]),
        lambda: (f"Ikkita bir xil uchburchakdan (asosi {a} sm, balandligi {h} sm) parallelogramm yasaldi. Uning yuzi?", a * h, f"$2 \\cdot \\frac{{{a} \\cdot {h}}}{{2}} = {a * h}$ sm²", [a * h // 2, 2 * a * h]),
    ]


def o_hajm(r):
    """Hajm: kub va kuboid, birliklar, suyuqlik."""
    a, b, c = r.randint(2, 9), r.randint(2, 9), r.randint(2, 9); k = r.randint(2, 6)
    return [
        lambda: (f"Kuboidning o‘lchamlari {a} sm, {b} sm, {c} sm. Hajmi?", a * b * c, f"$V = {a} \\cdot {b} \\cdot {c} = {a * b * c}$ sm³", [a + b + c, 2 * (a * b + b * c + a * c)]),
        lambda: (f"Qirrasi {k} sm bo‘lgan kubning hajmi?", k ** 3, f"$V = {k}^3 = {k ** 3}$ sm³", [k * 3, k * k]),
        lambda: (f"Kuboid hajmi {a * b * c} sm³, uzunligi {a} sm, eni {b} sm. Balandligi?", c, f"$c = V : (a \\cdot b) = {a * b * c} : {a * b} = {c}$ sm", [a * b, a * b * c // a]),
        lambda: (f"Akvarium {a * 10} sm × {b * 10} sm × {c * 10} sm. Unga necha litr suv sig‘adi? (1 l = 1000 sm³)", a * b * c, f"$V = {a * b * c * 1000}$ sm³ $= {a * b * c}$ l", [a * b * c * 1000, a * b * c * 10]),
        lambda: (f"{a} m³ necha dm³?", a * 1000, "1 m³ = 1000 dm³", [a * 100, a * 10]),
        lambda: (f"Qirrasi 1 sm bo‘lgan kubchalardan {a} × {b} × {c} kuboid yig‘ildi. Nechta kubcha ketdi?", a * b * c, "Kubchalar soni = hajm.", [a * b + c, a + b + c]),
        lambda: (f"Madina kub hajmini $V = 3 \\cdot {k} = {3 * k}$ deb topdi. To‘g‘ri javob?", k ** 3, "Kub hajmi — qirraning kubi: uchta qirra ko‘paytiriladi.", [3 * k]),
    ]


def o_nisbat(r):
    """Nisbatlar: soddalashtirish, teng kuchli, miqdor topish, bo'lib berish, uch qismli nisbat."""
    a, b = r.randint(1, 5), r.randint(2, 7); k = r.randint(2, 9); c = r.randint(1, 4)
    while a == b:
        b = r.randint(2, 7)
    return [
        lambda: (f"${a * k} : {b * k}$ nisbatni soddalashtiring (birinchi hadini yozing, ikkinchisi {b} bo‘lsin).", a, f"Har ikkala had {k} ga bo‘linadi: ${a} : {b}$", [a * k, b]),
        lambda: (f"${a} : {b} = {a * k} : ?$", b * k, f"Birinchi had {k} marta oshgan — ikkinchisi ham: ${b} \\cdot {k} = {b * k}$", [b + k, a * k]),
        lambda: (f"Olma va nokning nisbati ${a} : {b}$. Olma {a * k} ta. Nok nechta?", b * k, f"Bir ulush: ${a * k} : {a} = {k}$; nok: ${b} \\cdot {k} = {b * k}$", [a * k + b, b + k]),
        lambda: (f"{(a + b) * k} ta konfet {r.choice(ISM)} va {r.choice(ISM)} o‘rtasida ${a} : {b}$ nisbatda bo‘lindi. Kattaroq qism?", max(a, b) * k, f"Jami ulush ${a + b}$, bir ulush ${k}$; katta qism ${max(a, b)} \\cdot {k}$", [min(a, b) * k, (a + b) * k // 2]),
        lambda: (f"Qizil, sariq, ko‘k sharlar nisbati ${a} : {b} : {c}$. Jami {(a + b + c) * k} ta. Sariqlar nechta?", b * k, f"Bir ulush: ${(a + b + c) * k} : {a + b + c} = {k}$", [a * k, c * k]),
        lambda: (f"Sardor: «${a} : {b}$ nisbat ${a + 2} : {b + 2}$ ga teng». To‘g‘rimi? (1 — ha, 0 — yo‘q)", 0, "Teng kuchli nisbat — hadlarni bir xil songa KO‘PAYTIRISH yoki BO‘LISH bilan hosil bo‘ladi, qo‘shish bilan emas.", [1]),
        lambda: (f"Choy damlash uchun 2 qoshiq choyga {b} stakan suv kerak. 6 qoshiq choyga necha stakan?", b * 3, f"Choy 3 marta ko‘p — suv ham: ${b} \\cdot 3$", [b + 4, b * 2]),
    ]


def o_onli(r):
    """O'nli kasrlar: 10/100/1000 ga ko'paytirish-bo'lish, birliklar."""
    x = round(r.uniform(1.2, 98.7), r.choice([1, 2])); k = r.choice([10, 100, 1000]); t = r.choice([20, 30, 40, 300, 500])
    return [
        lambda: (f"${dk(x)} \\cdot {k}$", dk(x * k), f"Vergul o‘ngga {len(str(k)) - 1} xona suriladi.", [dk(x * k / 10), dk(x / k)]),
        lambda: (f"${dk(x)} : {k}$", dk(x / k), f"Vergul chapga {len(str(k)) - 1} xona suriladi.", [dk(x * k), dk(x / k * 10)]),
        lambda: (f"${dk(x)} \\cdot {t}$", dk(x * t), f"${dk(x)} \\cdot {t // 10 ** (len(str(t)) - 1)}$, keyin vergulni suramiz.", [dk(x * t / 10), dk(x + t)]),
        lambda: (f"{dk(x)} kg necha gramm?", dk(x * 1000), "1 kg = 1000 g", [dk(x * 100), dk(x * 10)]),
        lambda: (f"{int(x * 10)} sm necha metr?", dk(int(x * 10) / 100), "1 m = 100 sm — 100 ga bo‘lamiz.", [dk(int(x * 10) / 10), dk(int(x * 10) / 1000)]),
        lambda: (f"1 litr sut {dk(round(x) * 500 + 9000)} so‘m. 10 litr necha so‘m?", dk((round(x) * 500 + 9000) * 10), "10 ga ko‘paytirish — oxiriga bitta nol.", [dk((round(x) * 500 + 9000) * 100), dk(round(x) * 500 + 9010)]),
        lambda: (f"Otabek: «${dk(x)} \\cdot 100 = {dk(x)}00$». To‘g‘ri javob?", dk(x * 100), "O‘nli kasrda nol qo‘shilmaydi, vergul suriladi.", [f"{dk(x)}00"]),
    ]


def o_meyor(r):
    """Me'yor (birlik narxi, tezlik, unumdorlik)."""
    m = r.randint(3, 25) * 100; n = r.randint(3, 9); b = r.randint(2, 6)
    return [
        lambda: (f"{n} ta daftar {m * n} so‘m. Bitta daftar narxi?", m, f"Me’yor: ${m * n} : {n} = {m}$ so‘m", [m * n, m * n // 10]),
        lambda: (f"Bitta daftar {m} so‘m. {n} ta daftar?", m * n, f"Umumiy: ${m} \\cdot {n}$", [m + n]),
        lambda: (f"{m * n} so‘mga {m} so‘mlik nechta daftar olish mumkin?", n, f"Birliklar soni: ${m * n} : {m} = {n}$", [m, n * 10]),
        lambda: (f"Usta soatiga {n} ta detal yasaydi. {n * b} ta detalni necha soatda yasaydi?", b, f"${n * b} : {n} = {b}$ soat", [n * b, n + b]),
        lambda: (f"1-do‘kon: {n} ta qalam {m * n} so‘m; 2-do‘kon: {n + 1} ta qalam {m * (n + 1) - 100} so‘m. Qaysi do‘konda bitta qalam arzon? (1 yoki 2)", 2, "Har birida bitta qalam narxini topamiz.", [1]),
        lambda: (f"Avtobus {b} soatda {b * 60} km yurdi. Shu tezlikda {b + 2} soatda qancha yuradi?", (b + 2) * 60, f"Tezlik: ${b * 60} : {b} = 60$ km/soat", [b * 60 + 2, (b + 2) * b * 60]),
    ]


def o_foiz(r):
    """Foizlar: tushuncha, kasr↔o'nli↔foiz, miqdorning foizi, QQS, chegirma, omonat."""
    p = r.choice([10, 20, 25, 30, 40, 50, 60, 75]); s = r.randint(4, 40) * 1000; t = r.choice([200, 400, 500, 800])
    return [
        lambda: (f"${p}\\%$ ni oddiy kasr ko‘rinishida yozing (qisqartiring).", f"{F(p, 100).numerator}/{F(p, 100).denominator}", f"${p}\\% = \\frac{{{p}}}{{100}} = {kf(F(p, 100))}$", [f"{p}/10", f"1/{p}"]),
        lambda: (f"${t}$ ning ${p}\\%$ i?", t * p // 100, f"${t} : 100 \\cdot {p} = {t * p // 100}$", [t * p, t // p if p else 0]),
        lambda: (f"Narxi {s} so‘m bo‘lgan kitobga ${p}\\%$ chegirma. Yangi narx?", s - s * p // 100, f"Chegirma: ${s * p // 100}$; yangi narx: ${s} - {s * p // 100}$", [s * p // 100, s + s * p // 100]),
        lambda: (f"Mahsulot narxi {s} so‘m, unga 12% QQS qo‘shiladi. Jami narx?", s + s * 12 // 100, f"QQS: ${s * 12 // 100}$; jami: ${s + s * 12 // 100}$", [s * 12 // 100, s - s * 12 // 100]),
        lambda: (f"Bankka {s} so‘m yillik 10% bilan qo‘yildi. Bir yildan keyin omonat?", s + s // 10, "Foyda: summaning 10% i, uni omonatga qo‘shamiz.", [s // 10, s * 10]),
        lambda: (f"Sinfdagi {t // 10} o‘quvchining ${p}\\%$ i qizlar. Qizlar nechta?", t // 10 * p // 100, f"${t // 10} \\cdot {p} : 100$", [t // 10 - t // 10 * p // 100]),
        lambda: (f"Bir sonning ${p}\\%$ i {t * p // 100} ga teng. Sonning o‘zi?", t, f"$1\\%$ — ${t * p // 100} : {p}$, $100\\%$ — ${t}$", [t * p // 100 * p, t * p // 100]),
        lambda: (f"Qaysi chegirma ko‘p: {s} so‘mning 20% i yoki {s} so‘mdan 3000 so‘m? (ko‘p chegirma miqdorini yozing)", max(s // 5, 3000), "Ikkalasini so‘mda hisoblab solishtiramiz.", [min(s // 5, 3000)]),
    ]


def o_ortacha(r):
    """O'rtacha qiymat."""
    xs = [r.randint(3, 5) for _ in range(4)]
    while sum(xs) % 4:
        xs[0] += 1
    m = sum(xs) // 4; n = r.randint(3, 6)
    return [
        lambda: (f"Baholar: {', '.join(map(str, xs))}. O‘rtacha baho?", m, f"Yig‘indi ${sum(xs)}$, soni 4: ${sum(xs)} : 4 = {m}$", [sum(xs), max(xs)]),
        lambda: (f"{n} kunda o‘rtacha {m * 10} sahifa o‘qildi. Jami necha sahifa?", n * m * 10, "Jami = o‘rtacha × soni.", [m * 10 + n, m * 10]),
        lambda: (f"Uch kunlik o‘rtacha harorat {m * 5}°. Ikki kunda {m * 5 - 2}° va {m * 5 + 1}° edi. Uchinchi kunda?", m * 15 - (m * 5 - 2) - (m * 5 + 1), "Jami ${} — ikki kunning yig‘indisi.".format(m * 15), [m * 5, m * 5 + 2]),
        lambda: (f"To‘rt o‘quvchining o‘rtacha bo‘yi {130 + m} sm. Bo‘yi {150 + m} sm bo‘lgan beshinchi o‘quvchi qo‘shildi. Yangi o‘rtacha?", (4 * (130 + m) + 150 + m) // 5 if (4 * (130 + m) + 150 + m) % 5 == 0 else round((4 * (130 + m) + 150 + m) / 5), "Yangi yig‘indini 5 ga bo‘lamiz.", [130 + m, 140 + m]),
        lambda: (f"Dilnoza: «4, 5, 3 ning o‘rtachasi $4 + 5 + 3 = 12$». To‘g‘ri javob?", 4, "Yig‘indini sonlar soniga — 3 ga bo‘lish unutilgan.", [12]),
    ]


def o_burchak(r):
    """Burchaklar: to'g'ri chiziqda, vertikal, nuqta atrofida, noma'lum burchaklar."""
    a = r.randint(25, 155); b = r.randint(40, 120); c = r.randint(50, 130)
    return [
        lambda: (f"To‘g‘ri chiziqdagi qo‘shni burchaklardan biri ${a}°$. Ikkinchisi?", 180 - a, f"$180° - {a}° = {180 - a}°$", [90 - a if a < 90 else a - 90, 360 - a]),
        lambda: (f"Vertikal burchaklardan biri ${a}°$. Ikkinchisi?", a, "Vertikal burchaklar teng.", [180 - a]),
        lambda: (f"Nuqta atrofida uchta burchak: ${b}°$, ${c}°$ va $x$. $x$ = ?", 360 - b - c, f"$360° - {b}° - {c}° = {360 - b - c}°$", [180 - b - c if b + c < 180 else b + c - 180, b + c]),
        lambda: (f"Soat 3 da soat millari orasidagi burchak?", 90, "Siferblat 12 bo‘lak, har biri $30°$: $3 \\cdot 30° = 90°$", [30, 180]),
        lambda: (f"Jasur: «To‘g‘ri chiziqdagi qo‘shni burchaklar ${a}°$ va ${a}°$». Bu faqat qaysi holatda to‘g‘ri? (burchakni yozing)", 90, "Yig‘indi $180°$: ikkalasi teng bo‘lsa, har biri $90°$.", [180, 45]),
        lambda: (f"Ikki to‘g‘ri chiziq kesishganda hosil bo‘lgan burchaklardan biri ${a}°$. Unga qo‘shni burchak?", 180 - a, "Qo‘shni burchaklar yig‘indisi $180°$.", [a]),
    ]


def o_uchburchak(r):
    """Uchburchak turlari va burchaklari."""
    a, b = r.randint(30, 80), r.randint(30, 80)
    return [
        lambda: (f"Uchburchakning ikki burchagi ${a}°$ va ${b}°$. Uchinchisi?", 180 - a - b, f"$180° - {a}° - {b}° = {180 - a - b}°$", [360 - a - b, a + b]),
        lambda: (f"Teng yonli uchburchakning uchidagi burchak ${180 - 2 * a}°$. Asosidagi burchak?", a, f"$(180° - {180 - 2 * a}°) : 2 = {a}°$", [180 - 2 * a, 2 * a]),
        lambda: (f"Burchaklari ${a}°$, ${b}°$, ${180 - a - b}°$ bo‘lgan uchburchak qanday? (1 — o‘tkir, 2 — to‘g‘ri, 3 — o‘tmas burchakli)", 1 if max(a, b, 180 - a - b) < 90 else 2 if max(a, b, 180 - a - b) == 90 else 3, "Eng katta burchakka qaraymiz.", [x for x in (1, 2, 3) if x != (1 if max(a, b, 180 - a - b) < 90 else 2 if max(a, b, 180 - a - b) == 90 else 3)]),
        lambda: (f"To‘g‘ri burchakli uchburchakning bir o‘tkir burchagi ${a}°$. Ikkinchisi?", 90 - a if a < 90 else 10, f"$90° - {a}°$", [180 - a]),
        lambda: (f"Burchaklari ${a}°$, ${b}°$ va ${200 - a - b}°$ bo‘lgan uchburchak bormi? (1 — ha, 0 — yo‘q)", 0, "Yig‘indi $200°$ — uchburchakda $180°$ bo‘lishi shart.", [1]),
        lambda: (f"Teng tomonli uchburchakning har bir burchagi?", 60, "$180° : 3 = 60°$", [90, 45]),
    ]


def o_tortburchak(r):
    """To'rtburchaklar: parallelogramm, romb, trapetsiya xossalari, noma'lum burchaklar."""
    a, b, c = r.randint(50, 130), r.randint(60, 120), r.randint(70, 110)
    return [
        lambda: (f"Parallelogrammning bir burchagi ${a}°$. Unga qo‘shni burchak?", 180 - a, "Parallelogrammda qo‘shni burchaklar yig‘indisi $180°$.", [a, 360 - a]),
        lambda: (f"Parallelogrammning bir burchagi ${a}°$. Unga qarama-qarshi burchak?", a, "Qarama-qarshi burchaklar teng.", [180 - a]),
        lambda: (f"To‘rtburchakning uch burchagi ${a}°$, ${b}°$, ${c}°$. To‘rtinchisi?", 360 - a - b - c, f"$360° - {a}° - {b}° - {c}°$", [180 - a - b - c if a + b + c < 180 else 180, a]),
        lambda: (f"Trapetsiyaning yon tomoniga yopishgan burchaklardan biri ${a}°$. Ikkinchisi?", 180 - a, "Asoslar parallel — yon tomondagi burchaklar yig‘indisi $180°$.", [a]),
        lambda: (f"Rombning diagonallari orasidagi burchak?", 90, "Romb diagonallari perpendikulyar.", [180, 45]),
        lambda: (f"Bekzod: «Parallelogramm burchaklari ${a}°$, ${a}°$, ${a}°$, ${a}°$». Bu qanday shakl bo‘lsa to‘g‘ri? (burchakni yozing)", 90, "Hamma burchak teng bo‘lsa — har biri $90°$ (to‘g‘ri to‘rtburchak).", [a]),
    ]


def o_fazo(r):
    """Fazoviy jismlar (chizish darslari uchun — fikrlash savollari)."""
    k = r.randint(2, 4)
    return [
        lambda: ("Kubning nechta qirrasi bor?", 12, "Tepada 4, pastda 4, yonlarda 4.", [8, 6]),
        lambda: ("Kubning nechta uchi bor?", 8, "Tepada 4, pastda 4.", [12, 6]),
        lambda: ("Kuboidning nechta yog‘i bor?", 6, "Old-orqa, chap-o‘ng, ust-ost.", [8, 4]),
        lambda: (f"{k} × {k} × {k} kub yuzasi bo‘yalgan, keyin 1×1×1 kubchalarga bo‘lingan. Uchta yog‘i bo‘yalgan kubchalar nechta?", 8, "Faqat burchakdagi kubchalarda uchta yog‘ bo‘yalgan — 8 ta burchak.", [12, k * k]),
        lambda: ("Kubni yuqoridan qaraganda qanday shakl ko‘rinadi? (1 — kvadrat, 2 — uchburchak, 3 — doira)", 1, "Kubning har bir yog‘i — kvadrat.", [2, 3]),
        lambda: ("Silindrni yon tomondan qaraganda qanday shakl ko‘rinadi? (1 — doira, 2 — to‘g‘ri to‘rtburchak)", 2, "Yon tomondan — to‘g‘ri to‘rtburchak.", [1]),
    ]


OILALAR = [
    (r"million|natural son", o_sonlar), (r"10, 100 va 1000|o.nlik, yuzlik|o.nliklar, yuzliklar", o_kop10), (r"qavs|amallarni bajarish tartibi", o_tartib),
    (r"to.rt amal", o_masala), (r"kasr ko.rinishida|oddiy kasr|aralash son|kasrni|kasrlarni|qolgan qism", o_kasr), (r"uchburchakning yuz|asosi va balandligi|murakkab shakl", o_yuz),
    (r"hajm|kuboid|suyuqlik", o_hajm), (r"fazoviy|uch o.lchamli|panjara", o_fazo), (r"nisbat", o_nisbat), (r"o.nli kasr|o.lchov birlik", o_onli), (r"me.yor|birliklar sonini", o_meyor),
    (r"foiz|qqs|chegirma", o_foiz), (r"o.rtacha", o_ortacha), (r"burchak(lar)?$|burchaklar|vertikal|nuqta atrofida|to.g.ri chiziqdagi", o_burchak),
    (r"uchburchak", o_uchburchak), (r"trapetsiya|parallelogramm|romb|to.rtburchak", o_tortburchak),
]


def oila_tanla(nom):
    import re as _re
    n = str(nom).lower()
    if _re.search(r"foiz|qqs|chegirma|omonat", n):   # «kasr, o'nli kasr va foizlar» — foiz mavzusi
        return o_foiz
    # o'nli kasr uchun «o'nlik, yuzlik» — o'nli kasr oilasi ustun
    if _re.search(r"o.nli kasr", n):
        return o_onli
    if _re.search(r"uchburchakning yuz|asosi va balandligi|murakkab shakl", n):
        return o_yuz
    for pat, f in OILALAR:
        if _re.search(pat, n):
            return f
    return None


def topshiriqlar(nom, urug, soni_misol=4, soni_masala=8, soni_test=6):
    """→ (misollar, masalalar, testlar): har biri [(shart, javob, yechim, xatolar, tur_raqami)], turlar takrorlanmaydi (masalada ≤2)."""
    f = oila_tanla(nom)
    if not f:
        return None
    r = random.Random(urug)
    def bitta(tur_i, rr):
        turlar = f(rr)
        return (*turlar[tur_i % len(turlar)](), tur_i % len(turlar))
    tur_soni = len(f(random.Random(0)))
    tartib = list(range(tur_soni)); r.shuffle(tartib)
    def olish(n, takror):
        out, i = [], 0
        while len(out) < n and i < n * 6:
            t = tartib[i % tur_soni] if takror or i < tur_soni else tartib[i % tur_soni]
            try:
                item = bitta(t, random.Random(r.random()))
                if item[1] not in (None, "") and str(item[1]) not in [str(x) for x in item[3]]:
                    out.append(item)
            except Exception:   # noqa: BLE001
                pass
            i += 1
        return out
    misol = olish(soni_misol, False)
    r.shuffle(tartib)
    masala = olish(soni_masala, True)
    r.shuffle(tartib)
    test = olish(soni_test, False)
    return misol, masala, test
