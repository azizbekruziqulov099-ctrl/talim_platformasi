"""REV509: 6-sinf matematika — har mavzuga ma'nosi bilan farq qiladigan misollar (xilma5 uslubida)."""
import random, re
from fractions import Fraction as F
from xilma5 import ISM, kf, dk, o_nisbat, o_burchak, o_uchburchak, o_tortburchak, o_hajm, o_fazo, o_kasr, o_foiz


def _f(x):
    return kf(F(x)).replace("\\tfrac", "")


def o_algebra(r):
    a, b, c, x = r.randint(2, 9), r.randint(3, 15), r.randint(2, 6), r.randint(2, 12)
    return [
        lambda: (f"$x = {x}$ bo‘lsa, ${a}x + {b}$ ning qiymati?", a * x + b, f"${a} \\cdot {x} + {b} = {a * x + b}$", [a + x + b, a * (x + b)]),
        lambda: (f"Soddalashtiring: ${a}x + {c}x - x$ (x oldidagi koeffitsientni yozing)", a + c - 1, f"$({a} + {c} - 1)x = {a + c - 1}x$", [a + c, a * c]),
        lambda: (f"${a}x + {b} = {a * x + b}$ tenglamani yeching.", x, f"${a}x = {a * x + b} - {b} = {a * x}$, $x = {a * x} : {a} = {x}$", [x + b, (a * x + b) // a]),
        lambda: (f"Bir daftar $x$ so‘m, ruchka undan {b * 100} so‘m qimmat. 3 daftar va 1 ruchka narxi ifodasi qaysi? (1) $4x + {b * 100}$ (2) $3x + {b * 100}$ (3) $4x$", 1, f"$3x + (x + {b * 100}) = 4x + {b * 100}$", [2, 3]),
        lambda: (f"Soddalashtiring: ${c}(x + {a}) - {c}x$", c * a, f"${c}x + {c * a} - {c}x = {c * a}$", [c + a, c * a + c]),
        lambda: (f"Sardor: «${a}x + {b} = {a * x + b}$ dan $x = {a * x + b} + {b}$». To‘g‘ri yechim?", x, f"{b} ni ayirish va {a} ga bo‘lish kerak edi.", [a * x + 2 * b]),
        lambda: (f"Noma’lum sonni 3 ga ko‘paytirib, {b} qo‘shsak {3 * x + b} bo‘ladi. Son?", x, f"$3x + {b} = {3 * x + b}$ → $x = {x}$", [3 * x, x + b]),
        lambda: (f"$y = {c}$ bo‘lsa, $y^2 + {a}y$?", c * c + a * c, f"${c}^2 + {a} \\cdot {c} = {c * c + a * c}$", [2 * c + a * c, c + a * c]),
    ]


def o_kasr_bol(r):
    a = F(r.randint(1, 4), r.choice([5, 6, 7, 8, 9])); b = F(r.randint(1, 3), r.choice([4, 5, 6])); n = r.randint(2, 6)
    return [
        lambda: (f"${_f(a)} : {n}$", _f(a / n), "Maxrajni ko‘paytiramiz (yoki $\\frac{1}{n}$ ga ko‘paytiramiz).", [_f(a * n), _f(F(a.numerator, a.denominator + n))]),
        lambda: (f"${n} : {_f(b)}$", _f(n / b), "Teskari kasrga ko‘paytiramiz.", [_f(n * b), _f(b / n)]),
        lambda: (f"${_f(a)} : {_f(b)}$", _f(a / b), "Ikkinchi kasrning teskarisiga ko‘paytiramiz.", [_f(a * b), _f(b / a)]),
        lambda: (f"{n} m arqonni ${_f(b)}$ m lik bo‘laklarga kesishdi. Nechta bo‘lak?", _f(n / b), f"${n} : {_f(b)} = {_f(n / b)}$", [_f(n * b)]),
        lambda: (f"${_f(a)}$ kg shakarni {n} ta idishga teng solishdi. Har birida necha kg?", _f(a / n), f"${_f(a)} : {n}$", [_f(a * n)]),
        lambda: (f"Dilnoza: «$\\frac{{1}}{{2}} : \\frac{{1}}{{4}} = \\frac{{1}}{{8}}$». To‘g‘ri javob?", "2", "Bo‘lishda teskari kasrga ko‘paytiriladi: $\\frac{1}{2} \\cdot 4 = 2$", ["1/8", "1/2"]),
        lambda: (f"Qaysi katta: ${_f(a)} : {n}$ yoki ${_f(a)}$? (kattasini yozing)", _f(a), "Songa (>1) bo‘lsak, son kichrayadi.", [_f(a / n)]),
    ]


def o_foiz6(r):
    s = r.randint(4, 40) * 100; p = r.choice([10, 20, 25, 40, 50]); y = r.choice([10, 20, 25])
    return [
        lambda: (f"Sonning ${p}\\%$ i {s * p // 100} ga teng. Son?", s, f"$1\\% = {s * p // 100} : {p}$; $100\\% = {s}$", [s * p // 100 * p // 10, s // 2]),
        lambda: (f"Narx {s} so‘mdan {s + s * y // 100} so‘mga oshdi. Necha foizga?", y, f"Oshish ${s * y // 100}$; $\\frac{{{s * y // 100}}}{{{s}}} \\cdot 100\\% = {y}\\%$", [s * y // 100, y * 2]),
        lambda: (f"Narx {s} so‘mdan {s - s * y // 100} so‘mga tushdi. Necha foizga kamaydi?", y, "Kamayish miqdorini boshlang‘ich narxga bo‘lamiz.", [100 - y, s * y // 100]),
        lambda: (f"O‘quvchilarning ${p}\\%$ i — {p // 5 * 2} kishi. Jami nechta o‘quvchi?", p // 5 * 2 * 100 // p, "Qismi va foiziga ko‘ra butunni topamiz.", [p // 5 * 2 * p // 100 or 1, p]),
        lambda: (f"Narx avval ${y}\\%$ oshdi, keyin ${y}\\%$ tushdi. Oxirgi narx boshlang‘ichdan qanday? (1 — teng, 2 — arzon, 3 — qimmat)", 2, f"Masalan 100 → {100 + y} → {(100 + y) * (100 - y) / 100:g}: arzonroq.", [1, 3]),
        lambda: (f"Jasur: «{s} ning ${y}\\%$ i {s // y}». To‘g‘ri javob?", s * y // 100, f"${s} : 100 \\cdot {y}$ — {y} ga bo‘lish xato.", [s // y]),
    ]


def o_doira(r):
    rr = r.randint(2, 14); d = 2 * rr
    pi = "3,14"
    return [
        lambda: (f"Radiusi {rr} sm aylananing uzunligi? ($\\pi \\approx 3{{,}}14$)", dk(round(2 * 3.14 * rr, 2)), f"$C = 2\\pi r = 2 \\cdot {pi} \\cdot {rr} = {dk(round(2 * 3.14 * rr, 2))}$ sm", [dk(round(3.14 * rr, 2)), dk(round(3.14 * rr * rr, 2))]),
        lambda: (f"Diametri {d} sm doiraning yuzi? ($\\pi \\approx 3{{,}}14$)", dk(round(3.14 * rr * rr, 2)), f"$r = {rr}$; $S = \\pi r^2 = {pi} \\cdot {rr * rr} = {dk(round(3.14 * rr * rr, 2))}$ sm²", [dk(round(3.14 * d * d, 2)), dk(round(2 * 3.14 * rr, 2))]),
        lambda: (f"Aylana uzunligi ${dk(round(2 * 3.14 * rr, 2))}$ sm. Radiusi? ($\\pi \\approx 3{{,}}14$)", rr, f"$r = C : (2\\pi) = {rr}$ sm", [d, rr * 2 + 1]),
        lambda: (f"Radiusi {rr} sm yarim doiraning perimetri? (yoy + diametr, $\\pi \\approx 3{{,}}14$)", dk(round(3.14 * rr + d, 2)), f"Yoy: $\\pi r = {dk(round(3.14 * rr, 2))}$; diametr ${d}$; jami ${dk(round(3.14 * rr + d, 2))}$", [dk(round(3.14 * rr, 2)), dk(round(2 * 3.14 * rr, 2))]),
        lambda: (f"Radiusi {rr} sm chorak doiraning yuzi? ($\\pi \\approx 3{{,}}14$)", dk(round(3.14 * rr * rr / 4, 2)), "Butun doira yuzining to‘rtdan biri.", [dk(round(3.14 * rr * rr / 2, 2)), dk(round(3.14 * rr * rr, 2))]),
        lambda: (f"Velosiped g‘ildiragining diametri 70 sm. G‘ildirak {rr * 10} marta aylanganda necha sm yuradi? ($\\pi \\approx 3{{,}}14$)", dk(round(3.14 * 70 * rr * 10, 2)), "Bir aylanishda aylana uzunligi qadar yuradi.", [dk(round(70 * rr * 10, 2))]),
        lambda: (f"Radius 2 marta oshsa, doira yuzi necha marta oshadi?", 4, "$S = \\pi r^2$: radius kvadratda — $2^2 = 4$.", [2, 8]),
        lambda: (f"Madina: «Radiusi {rr} sm doira yuzi $2 \\cdot 3{{,}}14 \\cdot {rr}$». To‘g‘ri javob?", dk(round(3.14 * rr * rr, 2)), "Bu aylana uzunligi formulasi; yuzi $\\pi r^2$.", [dk(round(2 * 3.14 * rr, 2))]),
    ]


def o_tezlik(r):
    v1, v2, t = r.randint(4, 9) * 10, r.randint(3, 8) * 10, r.randint(2, 5)
    i1, i2 = r.sample(ISM, 2)
    return [
        lambda: (f"Poyezd {t} soatda {v1 * t} km yurdi. Tezligi?", v1, f"$v = s : t = {v1 * t} : {t}$", [v1 * t, v1 + t]),
        lambda: (f"Tezlik {v1} km/soat. {v1 * t} km ni necha soatda bosadi?", t, f"$t = s : v$", [v1, v1 * t]),
        lambda: (f"Mashina {t} soat {v1} km/soat, keyin 1 soat {v2} km/soat tezlikda yurdi. Jami yo‘l?", v1 * t + v2, f"${v1} \\cdot {t} + {v2}$", [(v1 + v2) * (t + 1)]),
        lambda: (f"Ikki shahar orasi {(v1 + v2) * t} km. Ikki mashina bir vaqtda bir-biriga qarab yurdi ({v1} va {v2} km/soat). Necha soatda uchrashadi?", t, f"Yaqinlashish tezligi ${v1 + v2}$; ${(v1 + v2) * t} : {v1 + v2} = {t}$", [(v1 + v2) * t // v1, t * 2]),
        lambda: (f"{i1} {t} soatda {v1 * t} km, keyin {t} soatda {v2 * t} km yurdi. O‘rtacha tezlik?", (v1 + v2) // 2 if (v1 + v2) % 2 == 0 else round((v1 + v2) / 2, 1), "O‘rtacha tezlik = jami yo‘l : jami vaqt.", [v1 + v2, max(v1, v2)]),
        lambda: (f"{i1} {min(v1, v2) if v1 != v2 else v2} m/daq, {i2} {max(v1, v2) if v1 != v2 else v2 + 10} m/daq tezlikda bir yo‘nalishda yuradi; {i2} {i1}dan {(abs(v1 - v2) or 10) * t} m orqada. {i2} necha daqiqada yetib oladi?", t,
                 f"Quvib yetish tezligi — tezliklar ayirmasi: {abs(v1 - v2) or 10} m/daq; ${(abs(v1 - v2) or 10) * t} : {abs(v1 - v2) or 10} = {t}$", [t + 1, t * 2]),
        lambda: (f"Otabek: «{v1} km/soat tezlikda {t} soatda {v1 + t} km». To‘g‘ri javob?", v1 * t, "Yo‘l = tezlik × vaqt (qo‘shish emas).", [v1 + t]),
    ]


def o_hajm6(r):
    a, b, c = r.randint(2, 9), r.randint(2, 9), r.randint(2, 9); k = r.randint(2, 7)
    return o_hajm(r) + [
        lambda: (f"Kub hajmi {k ** 3} sm³. Qirrasi?", k, f"${k}^3 = {k ** 3}$", [k ** 3 // 3, k * 3]),
        lambda: (f"Kuboidning bir yog‘i {a} sm × {b} sm. Shu yog‘ yuzi?", a * b, f"${a} \\cdot {b}$", [2 * (a + b)]),
        lambda: (f"Kubning bitta yog‘i yuzi {k * k} sm². Hajmi?", k ** 3, f"Qirra ${k}$; $V = {k}^3$", [k * k * 6, k * 3]),
    ]


def o_diagramma(r):
    p = r.choice([10, 20, 25, 30, 40, 50]); n = r.choice([200, 400, 600, 800])
    return [
        lambda: (f"Doiraviy diagrammada bir bo‘lak ${p}\\%$. Uning markaziy burchagi?", 360 * p // 100, f"$360° \\cdot {p} : 100$", [p, 180 * p // 100]),
        lambda: (f"Markaziy burchagi ${360 * p // 100}°$ bo‘lgan bo‘lak necha foiz?", p, f"${360 * p // 100} : 360 \\cdot 100\\%$", [360 * p // 100, p * 2]),
        lambda: (f"Maktabdagi {n} o‘quvchining ${p}\\%$ i futbolni tanladi (diagrammada). Necha o‘quvchi?", n * p // 100, f"${n} \\cdot {p} : 100$", [n // p, p]),
        lambda: (f"Diagrammada uch bo‘lak: ${p}\\%$, ${100 - p - 20}\\%$ va qolgani. Qolgani necha foiz?", 20, "Hammasi $100\\%$.", [p, 100 - p]),
        lambda: (f"Yarim doira qismi necha foiz?", 50, "Butun doira — $100\\%$.", [180, 25]),
    ]


def o_yoyilma(r):
    return o_fazo(r) + [
        lambda: ("Silindrning yoyilmasi qaysi shakllardan iborat? (1 — 2 doira va to‘g‘ri to‘rtburchak, 2 — 6 kvadrat, 3 — doira va uchburchak)", 1, "Ikki asos — doira, yon sirti — to‘g‘ri to‘rtburchak.", [2, 3]),
        lambda: ("To‘rtburchakli piramidaning nechta yog‘i bor?", 5, "Asos 1 ta + yon yoqlar 4 ta.", [4, 6]),
        lambda: ("Uchburchakli prizmaning nechta uchi bor?", 6, "Har asosda 3 tadan.", [5, 9]),
        lambda: ("Konusning yoyilmasi: (1 — doira va doira sektori, 2 — ikki doira, 3 — uchburchak)", 1, "Asos — doira, yon sirti — sektor.", [2, 3]),
    ]


def o_takror(r):
    oilalar = [o_algebra, o_kasr_bol, o_foiz6, o_doira, o_tezlik, o_nisbat]
    return [t for f in oilalar for t in f(r)[:2]]


def oila_tanla(nom):
    n = str(nom).lower()
    for pat, f in [(r"takrorlash", o_takror), (r"algebra|ifoda|tenglama", o_algebra), (r"bo.lish|kasrlar", o_kasr_bol), (r"nisbat", o_nisbat),
                   (r"foiz", o_foiz6), (r"burchak", lambda r: o_burchak(r) + o_uchburchak(r)[:3] + o_tortburchak(r)[:3]),
                   (r"doira|aylana|murakkab shakl", o_doira), (r"tezlik|harakat", o_tezlik), (r"hajm|qirra|kuboid|kub", o_hajm6), (r"diagramma", o_diagramma),
                   (r"yoyilma|konus|silindr|prizma|piramida|fazoviy", o_yoyilma)]:
        if re.search(pat, n):
            return f
    return None
