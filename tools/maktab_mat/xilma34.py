"""REV510: 3–4-sinf matematika — har mavzuga ma'nosi bilan farq qiladigan misollar (xilma5 uslubida, yoshga mos sonlar)."""
import random, re
from fractions import Fraction as F
from xilma5 import ISM, kf, dk, _s, o_meyor, o_ortacha
from xilma6 import o_tezlik, o_yoyilma


def _f(x):
    return kf(F(x)).replace("\\tfrac", "")


def o_sonlar34(r):
    n = r.randint(10_000, 999_999); m = n + r.choice([-1, 1]) * r.choice([1000, 100, 10]); ds = r.sample(range(1, 10), 5)
    return [
        lambda: (f"${_s(n)}$ sonida nechta yuzlik bor? (jami yuzliklar)", n // 100, f"${_s(n)} = {_s(n // 100)}$ yuz ${n % 100}$", [n // 1000, (n // 100) % 10]),
        lambda: (f"${_s(n)}$ sonining minglar xonasidagi raqam?", (n // 1000) % 10, "Xonalar o‘ngdan: birlar, o‘nlar, yuzlar, minglar…", [(n // 100) % 10, (n // 10000) % 10]),
        lambda: (f"Qaysi katta: ${_s(n)}$ yoki ${_s(m)}$? (kattasini yozing)", max(n, m), "Xonalarni chapdan solishtiramiz.", [min(n, m)]),
        lambda: (f"${_s(n)}$ ni xona qo‘shiluvchilari yig‘indisi ko‘rinishida yozganda yuzlar qo‘shiluvchisi?", (n // 100) % 10 * 100, f"{_s(n)} = … + {(n // 100) % 10 * 100} + …", [(n // 100) % 10, (n // 1000) % 10 * 1000]),
        lambda: (f"${', '.join(map(str, ds))}$ raqamlaridan tuzilgan eng kichik besh xonali son?", int(''.join(map(str, sorted(ds)))), "Eng kichik raqam eng katta xonaga.", [int(''.join(map(str, sorted(ds, reverse=True))))]),
        lambda: (f"${_s(n)}$ dan oldingi son?", n - 1, "Oldingi son — 1 ga kichik.", [n + 1, n - 10]),
        lambda: (f"Malika ${_s(n)}$ ni «{n // 1000} ming {n % 1000}» deb o‘qidi. Sondagi minglar soni nechta?", n // 1000, "Minglar sinfidagi son.", [n % 1000, n // 100]),
    ]


def o_qoshayir(r):
    a, b = r.randint(1200, 89000), r.randint(300, 9900); c = r.randint(2, 9) * 100 - r.randint(1, 3)
    return [
        lambda: (f"${_s(a)} + {_s(b)}$", a + b, "Xonama-xona qo‘shamiz, o‘ndan oshsa — keyingi xonaga 1.", [a + b + 1000, a - b]),
        lambda: (f"${_s(a + b)} - {_s(b)}$", a, "Xonama-xona ayiramiz.", [a + 2 * b, a - 1000]),
        lambda: (f"Qulay usulda: ${a} + {c}$ (masalan, ${c} = {c + (100 - c % 100)} - {100 - c % 100}$)", a + c, f"${a} + {c + (100 - c % 100)} - {100 - c % 100} = {a + c}$", [a + c + 100, a + c - 10]),
        lambda: (f"Kutubxonada {_s(a)} ta kitob bor edi, {_s(b)} tasi berildi. Nechta qoldi?", a - b, f"${_s(a)} - {_s(b)}$", [a + b]),
        lambda: (f"$? + {_s(b)} = {_s(a + b)}$", a, "Noma’lum qo‘shiluvchi: yig‘indidan ma’lum qo‘shiluvchini ayiramiz.", [a + 2 * b, b]),
        lambda: (f"Bekzod: «${_s(a)} + {_s(b)} = {_s(a + b + 1000)}$». To‘g‘ri javob?", a + b, "Ortiqcha 1000 qo‘shilgan.", [a + b + 1000]),
        lambda: (f"Taxminan: ${_s(a)} + {_s(b)}$ necha mingga yaqin?", round((a + b) / 1000), "Minglargacha yaxlitlab qo‘shamiz.", [round(a / 1000), round((a + b) / 1000) + 1]),
    ]


def o_kopaytir(r):
    a, b = r.randint(12, 98), r.randint(3, 9); c = r.randint(11, 49); z = r.choice([102, 205, 306, 408]); t = r.choice([20, 30, 40, 50])
    return [
        lambda: (f"${a} \\cdot {b}$", a * b, f"${a} \\cdot {b} = {a // 10 * 10} \\cdot {b} + {a % 10} \\cdot {b}$", [a * b + b, a + b]),
        lambda: (f"${a} \\cdot {c}$", a * c, "Ikki xonali songa ustun shaklida ko‘paytiramiz.", [a * c + a, a * (c // 10)]),
        lambda: (f"${z} \\cdot {b}$", z * b, "O‘rtadagi nolga e’tibor — o‘nlar xonasida 0 qoladi.", [(z // 100 * 10 + z % 10) * b, z * b + 10 * b]),
        lambda: (f"${a} \\cdot {t}$", a * t, f"${a} \\cdot {t // 10}$, keyin oxiriga 0.", [a * (t // 10), a * t * 10]),
        lambda: (f"Taqsimot xossasi: ${a} \\cdot {b} + {a} \\cdot {10 - b}$", a * 10, f"${a} \\cdot ({b} + {10 - b}) = {a} \\cdot 10$", [a * b, a + 10]),
        lambda: (f"Bir qutida {a} ta qalam. {b} ta qutida?", a * b, "Teng qo‘shiluvchilar — ko‘paytirish.", [a + b]),
        lambda: (f"Zarina: «${a} \\cdot {b} = {a * b + b}$». To‘g‘ri javob?", a * b, "Hisobni tekshiramiz.", [a * b + b]),
        lambda: (f"Avtobusda {a % 40 + 20} ta o‘rindiq bor. {b} ta avtobusga necha yo‘lovchi o‘tiradi?", (a % 40 + 20) * b, "O‘rindiqlar × avtobuslar.", [(a % 40 + 20) + b]),
        lambda: (f"$? \\cdot {b} = {a * b}$", a, "Noma’lum ko‘paytuvchi = ko‘paytma : ma’lum ko‘paytuvchi.", [a * b - b, a + b]),
        lambda: (f"Qaysi katta: ${a} \\cdot {b}$ yoki ${a} \\cdot {b + 1}$? Ular necha birlikka farq qiladi?", a, f"Bitta ko‘paytuvchi 1 ga oshsa, ko‘paytma {a} ga oshadi.", [1, b]),
        lambda: (f"Chamalang: ${a} \\cdot {b}$ taxminan qancha? (o‘nliklargacha yaxlitlab hisoblang)", round(a, -1) * b, f"${a} \\approx {round(a, -1)}$; ${round(a, -1)} \\cdot {b}$", [a * b + 100]),
    ]


def o_bolish(r):
    b = r.randint(2, 9); q = r.randint(12, 99); qold = r.randint(1, b - 1) if b > 2 else 1
    n = q * b; nq = n + qold; d2 = r.randint(11, 25); q2 = r.randint(12, 40)
    return [
        lambda: (f"${n} : {b}$", q, f"${q} \\cdot {b} = {n}$ — tekshiruv.", [q + 1, n - b]),
        lambda: (f"${nq}$ ni ${b}$ ga qoldiqli bo‘ling. Bo‘linma?", q, f"${nq} = {b} \\cdot {q} + {qold}$", [q + 1, qold]),
        lambda: (f"${nq}$ ni ${b}$ ga bo‘lganda qoldiq?", qold, f"${nq} = {b} \\cdot {q} + {qold}$; qoldiq bo‘luvchidan kichik.", [q, b]),
        lambda: (f"${d2 * q2} : {d2}$ (burchakli bo‘lish)", q2, "Bo‘linmaning har raqamini ketma-ket topamiz.", [q2 + 1, q2 * 10]),
        lambda: (f"{nq} ta olmani {b} ta savatga teng soldik. Har savatda nechta, nechta ortib qoldi? (savatdagini yozing)", q, "Qoldiqli bo‘lish.", [qold, q + 1]),
        lambda: (f"Yig‘indini songa bo‘lish: $({b * 20} + {b * 7}) : {b}$", 27, f"${b * 20} : {b} + {b * 7} : {b} = 20 + 7$", [b * 27, 20]),
        lambda: (f"Jasur: «{nq} : {b} = {q}, qoldiq {qold + b}». Xato qayerda? To‘g‘ri qoldiq?", qold, "Qoldiq bo‘luvchidan kichik bo‘lishi shart.", [qold + b]),
    ]


def o_alomat(r):
    n = r.randint(100, 9999); s = sum(map(int, str(n)))
    k = r.choice([2, 3, 5, 9, 10]); ha = int(n % k == 0)
    return [
        lambda: (f"{n} soni {k} ga bo‘linadimi? (1 — ha, 0 — yo‘q)", ha, {2: "Oxirgi raqam juft bo‘lsa.", 3: f"Raqamlar yig‘indisi {s} — 3 ga bo‘linsa.", 5: "Oxiri 0 yoki 5.", 9: f"Raqamlar yig‘indisi {s} — 9 ga bo‘linsa.", 10: "Oxiri 0."}[k], [1 - ha]),
        lambda: (f"{n} sonining raqamlari yig‘indisi?", s, "Hamma raqamlarni qo‘shamiz.", [s + 1, len(str(n))]),
        lambda: ("36 ning bo‘luvchilari nechta?", 9, "1, 2, 3, 4, 6, 9, 12, 18, 36", [8, 6]),
        lambda: (f"6 ga karrali eng kichik ikki xonali son?", 12, "6, 12, … — ikki xonalisi 12.", [6, 18]),
        lambda: (f"{n * 10} soni 10 ga bo‘linadimi? (1 — ha, 0 — yo‘q)", 1, "Oxiri 0 bilan tugaydi.", [0]),
        lambda: (f"Oxirgi raqami {r.choice([0, 5])} bo‘lgan son albatta nimaga bo‘linadi? (son yozing)", 5, "5 ga bo‘linish alomati.", [2, 3]),
    ]


def o_yaxlit(r):
    n = r.randint(1000, 99999); x = round(r.uniform(2.1, 98.9), 1)
    return [
        lambda: (f"{_s(n)} ni o‘nliklargacha yaxlitlang.", round(n, -1), "Birlar raqamiga qaraymiz: 5 va undan katta — yuqoriga.", [n // 10 * 10 + (10 if round(n, -1) == n // 10 * 10 else 0), round(n, -2)]),
        lambda: (f"{_s(n)} ni yuzlikkacha yaxlitlang.", round(n, -2), "O‘nlar raqamiga qaraymiz.", [round(n, -1), round(n, -3)]),
        lambda: (f"{dk(x)} ni butunlargacha yaxlitlang.", round(x), "O‘ndan birlar raqami 5 va undan katta bo‘lsa — yuqoriga.", [int(x), round(x) + 1]),
        lambda: (f"Chamalang: ${r.randint(48, 52)} \\cdot {r.randint(19, 21)}$ ga eng yaqin son?", 1000, "50 · 20 = 1000 ga yaqin.", [100, 10000]),
        lambda: (f"Chizg‘ich bilan o‘lchanganda kesma {dk(x)} sm chiqdi. Butun sm gacha aniqlikda?", round(x), "Yaxlitlaymiz.", [int(x) + 1 if round(x) == int(x) else int(x)]),
    ]


def o_kasr34(r):
    d = r.choice([3, 4, 5, 6, 8, 10]); a = r.randint(1, d - 1); n = d * r.randint(2, 9); b = r.randint(1, d - 1)
    return [
        lambda: (f"{n} ning ${_f(F(1, d))}$ qismi?", n // d, f"${n} : {d} = {n // d}$", [n * d, n - d]),
        lambda: (f"{n} ning ${_f(F(a, d))}$ qismi?", n // d * a, f"Avval ulush: ${n} : {d} = {n // d}$, keyin ${n // d} \\cdot {a}$", [n // d, n * a // 1]),
        lambda: (f"Sonning ${_f(F(1, d))}$ qismi {n // d}. Son?", n, f"${n // d} \\cdot {d} = {n}$", [n // d, n // d + d]),
        lambda: (f"${_f(F(a, d))} + {_f(F(b, d))}$", _f(F(a + b, d)), "Bir xil maxrajda suratlar qo‘shiladi, maxraj o‘zgarmaydi.", [_f(F(a + b, d + d)), _f(F(a * b, d))]),
        lambda: (f"Qaysi katta: ${_f(F(a, d))}$ yoki ${_f(F(b, d))}$? (kattasini yozing)", _f(F(max(a, b), d)), "Maxrajlar teng — surati kattasi katta.", [_f(F(min(a, b), d))]) if a != b else (f"$\\frac{{1}}{{{d}}}$ va $\\frac{{1}}{{{d + 1}}}$: qaysi katta?", _f(F(1, d)), "Surat bir xil — maxraji kichigi katta.", [_f(F(1, d + 1))]),
        lambda: (f"${_f(F(d + a, d))}$ ning butun qismi?", 1, f"${d + a} : {d} = 1$ (qoldiq {a})", [a, d]),
        lambda: (f"Pizza {d} bo‘lakka bo‘lingan, {a} bo‘lagi yeyildi. Qancha qismi qoldi?", _f(F(d - a, d)), f"$1 - {_f(F(a, d))} = {_f(F(d - a, d))}$", [_f(F(a, d))]),
        lambda: (f"Ali: «$\\frac{{1}}{{4}} + \\frac{{2}}{{4}} = \\frac{{3}}{{8}}$». To‘g‘ri javob?", "3/4", "Maxrajlar qo‘shilmaydi.", ["3/8"]),
    ]


def o_onli34(r):
    x = round(r.uniform(1.1, 9.9), 1); y = round(r.uniform(1.01, 9.99), 2); sm = r.randint(11, 99)
    return [
        lambda: (f"{dk(y)} sonining o‘ndan birlar xonasidagi raqam?", int(str(f"{y:.2f}")[2]), "Verguldan keyingi birinchi raqam.", [int(str(f"{y:.2f}")[3]), int(y)]),
        lambda: (f"{sm} sm ni metrda yozing.", dk(sm / 100), "1 sm = 0,01 m", [dk(sm / 10), str(sm)]),
        lambda: (f"{int(x * 1000)} g ni kilogrammda yozing.", dk(x), "1000 g = 1 kg", [dk(x * 10), dk(x / 10)]),
        lambda: (f"Qaysi katta: {dk(x)} yoki {dk(y)}? (kattasini yozing)", dk(max(x, y)), "Butun qismlar, keyin o‘ndan birlar solishtiriladi.", [dk(min(x, y))]),
        lambda: (f"${dk(x)} + {dk(round(x / 2, 1))}$", dk(round(x + round(x / 2, 1), 1)), "Vergul vergul ostida.", [dk(round(x * 2, 1))]),
    ]


def o_olchov(r):
    m, km, kg, t, h, mi = r.randint(2, 9), r.randint(2, 9), r.randint(2, 9), r.randint(2, 9), r.randint(1, 5), r.randint(5, 55)
    return [
        lambda: (f"{km} km {m * 100} m necha metr?", km * 1000 + m * 100, "1 km = 1000 m", [km * 100 + m * 100, km + m * 100]),
        lambda: (f"{kg} kg {m * 50} g necha gramm?", kg * 1000 + m * 50, "1 kg = 1000 g", [kg * 100 + m * 50]),
        lambda: (f"{t} t necha sentner? (1 t = 10 s)", t * 10, "1 tonna = 10 sentner", [t * 100, t * 1000]),
        lambda: (f"{h} soat {mi} minut — necha minut?", h * 60 + mi, "1 soat = 60 minut", [h * 100 + mi, h + mi]),
        lambda: (f"Dars 8:{mi:02d} da boshlanib 45 minut davom etdi. Qachon tugadi? (soat:minut)", f"{8 + (mi + 45) // 60}:{(mi + 45) % 60:02d}", "Minutlarni qo‘shamiz, 60 dan oshsa — soatga.", [f"8:{(mi + 45):02d}", f"9:{mi:02d}"]),
        lambda: (f"{m} m² necha dm²?", m * 100, "1 m² = 100 dm²", [m * 10, m * 1000]),
        lambda: (f"{m} l necha ml?", m * 1000, "1 l = 1000 ml", [m * 100]),
    ]


def o_perimetr34(r):
    a, b = r.randint(3, 15), r.randint(2, 12); n = r.choice([3, 5, 6, 8]); s = r.randint(2, 9)
    return [
        lambda: (f"To‘g‘ri to‘rtburchakning tomonlari {a} sm va {b} sm. Perimetri?", 2 * (a + b), f"$P = 2({a} + {b})$", [a * b, a + b]),
        lambda: (f"To‘g‘ri to‘rtburchakning tomonlari {a} sm va {b} sm. Yuzi?", a * b, f"$S = {a} \\cdot {b}$", [2 * (a + b)]),
        lambda: (f"Kvadratning perimetri {4 * a} sm. Tomoni?", a, f"${4 * a} : 4$", [4 * a // 2, a * a]),
        lambda: (f"Yuzi {a * b} sm², eni {b} sm bo‘lgan to‘g‘ri to‘rtburchakning bo‘yi?", a, f"${a * b} : {b}$", [a * b - b, 2 * a]),
        lambda: (f"Muntazam {n}-burchakning tomoni {s} sm. Perimetri?", n * s, f"${n} \\cdot {s}$", [n + s, s * s]),
        lambda: (f"Xona {a} m × {b} m. Polga necha m² gilam kerak?", a * b, "Yuza.", [2 * (a + b)]),
        lambda: (f"Sardor: «Tomonlari {a} va {b} bo‘lgan to‘g‘ri to‘rtburchak perimetri {a + b}». To‘g‘ri javob?", 2 * (a + b), "To‘rtta tomon qo‘shiladi.", [a + b]),
        lambda: (f"Kvadratning tomoni 2 marta oshsa, yuzi necha marta oshadi?", 4, "Tomonning kvadrati.", [2, 8]),
    ]


def o_tenglama34(r):
    x, a, b = r.randint(12, 99), r.randint(10, 60), r.randint(2, 9)
    return [
        lambda: (f"$x + {a} = {x + a}$", x, "Noma’lum qo‘shiluvchi = yig‘indi − ma’lum qo‘shiluvchi.", [x + 2 * a, a]),
        lambda: (f"$x - {a} = {x}$", x + a, "Kamayuvchi = ayirma + ayiriluvchi.", [x - a, a]),
        lambda: (f"$x \\cdot {b} = {x * b}$", x, "Noma’lum ko‘paytuvchi = ko‘paytma : ma’lum ko‘paytuvchi.", [x * b - b, x + b]),
        lambda: (f"$(x + {a}) : {b} = {(x + a) // b if (x + a) % b == 0 else (x + a + b - (x + a) % b) // b}$ (tarkibli tenglama)", ((x + a) // b if (x + a) % b == 0 else (x + a + b - (x + a) % b) // b) * b - a, "Avval qavs ichidagini topamiz, keyin x ni.", [x + a]),
        lambda: (f"$x < {a}$ tengsizlikni qanoatlantiradigan eng katta natural son?", a - 1, "a dan kichik eng katta son.", [a, a + 1]),
        lambda: (f"Qaysi belgi: ${a} + {b} \\; ? \\; {a + b - 1}$ (1 — >, 2 — <, 3 — =)", 1, f"${a + b} > {a + b - 1}$", [2, 3]),
        lambda: (f"Men bir son o‘yladim, unga {a} qo‘shsam {x + a} bo‘ladi. Son?", x, "Tenglama: x + a = …", [x + 2 * a]),
    ]


def o_geom34(r):
    g = r.choice([30, 45, 60, 90, 120, 150])
    return [
        lambda: (f"To‘g‘ri burchak necha gradus?", 90, "To‘g‘ri burchak — 90°.", [180, 45]),
        lambda: (f"${g}°$ li burchak qanday? (1 — o‘tkir, 2 — to‘g‘ri, 3 — o‘tmas)", 1 if g < 90 else 2 if g == 90 else 3, "90° dan kichik — o‘tkir, katta — o‘tmas.", [x for x in (1, 2, 3) if x != (1 if g < 90 else 2 if g == 90 else 3)]),
        lambda: ("Kesishganda to‘g‘ri burchak hosil qiladigan to‘g‘ri chiziqlar qanday ataladi? (1 — parallel, 2 — perpendikulyar)", 2, "Perpendikulyar.", [1]),
        lambda: ("Kvadratning nechta simmetriya o‘qi bor?", 4, "2 ta diagonal va 2 ta o‘rta chiziq.", [2, 1]),
        lambda: ("Diametri 14 sm bo‘lgan aylananing radiusi?", 7, "Radius — diametrning yarmi.", [14, 28]),
        lambda: ("Soat 3 da millar orasidagi burchak?", 90, "Har soat oralig‘i 30°.", [30, 180]),
        lambda: (f"Burchak ${g}°$. U to‘g‘ri burchakdan qanchaga farq qiladi?", abs(90 - g), "90° bilan solishtiramiz.", [g + 90, 90]),
    ]


def o_jism34(r):
    a, b, c = r.randint(2, 9), r.randint(2, 9), r.randint(2, 9); k = r.randint(2, 9)
    return [
        lambda: (f"Qirrasi {k} sm kubning barcha qirralari uzunliklari yig‘indisi?", 12 * k, "Kubda 12 ta teng qirra.", [6 * k, 8 * k]),
        lambda: (f"Kuboid {a} × {b} × {c} sm. Qirralari uzunliklari yig‘indisi?", 4 * (a + b + c), "Har o‘lchamdan 4 tadan qirra.", [a + b + c, 2 * (a + b + c)]),
        lambda: (f"Kuboid {a} × {b} × {c} sm. Hajmi?", a * b * c, "Uch o‘lcham ko‘paytmasi.", [a + b + c, 4 * (a + b + c)]),
    ] + o_yoyilma(r)[:5]


def o_toplam(r):
    a, b = sorted(r.sample(range(1, 10), 4)), sorted(r.sample(range(1, 10), 4))
    u = sorted(set(a) | set(b)); k = sorted(set(a) & set(b)); n1, n2, both = r.randint(10, 20), r.randint(8, 18), r.randint(3, 7)
    return [
        lambda: (f"A = {{{', '.join(map(str, a))}}}, B = {{{', '.join(map(str, b))}}}. Birlashmada nechta element?", len(u), f"A ∪ B = {{{', '.join(map(str, u))}}}", [len(a) + len(b), len(k)]),
        lambda: (f"A = {{{', '.join(map(str, a))}}}, B = {{{', '.join(map(str, b))}}}. Kesishmada nechta element?", len(k), f"A ∩ B = {{{', '.join(map(str, k))}}}", [len(u), len(a)]),
        lambda: (f"Sinfda {n1} kishi futbol, {n2} kishi shaxmat o‘ynaydi, {both} kishi ikkalasini ham. Kamida bittasini o‘ynaydiganlar nechta?", n1 + n2 - both, "Venn diagrammasi: ikkalasini o‘ynaganlar ikki marta sanalmasin.", [n1 + n2, n1 + n2 - 2 * both]),
        lambda: (f"{a[0]} soni A = {{{', '.join(map(str, a))}}} to‘plamga tegishlimi? (1 — ha, 0 — yo‘q)", 1, "Ro‘yxatda bor.", [0]),
        lambda: (f"{{1, 2, 3}} to‘plamning nechta qismto‘plami bor?", 8, "∅, {1}, {2}, {3}, {1,2}, {1,3}, {2,3}, {1,2,3}", [3, 6]),
    ]


def o_diag34(r):
    v = [r.randint(2, 9) * 5 for _ in range(4)]; kun = ["Du", "Se", "Ch", "Pa"]
    jad = ", ".join(f"{k}: {x}" for k, x in zip(kun, v))
    return [
        lambda: (f"Ustunli diagrammada sotilgan non: {jad}. Eng ko‘p qaysi kunda? (sonini yozing)", max(v), "Eng baland ustun.", [min(v), sum(v)]),
        lambda: (f"Diagramma: {jad}. Jami?", sum(v), "Hammasini qo‘shamiz.", [max(v) * 4]),
        lambda: (f"Diagramma: {jad}. Eng ko‘p va eng kam farqi?", max(v) - min(v), "Ayirma.", [max(v) + min(v)]),
        lambda: (f"Baholar chastotasi: «5» — {v[0] // 5} ta, «4» — {v[1] // 5} ta, «3» — {v[2] // 5} ta. Jami nechta baho?", (v[0] + v[1] + v[2]) // 5, "Chastotalar yig‘indisi.", [3, v[0] // 5]),
    ] + o_ortacha(r)[:3]


def o_koordinata(r):
    a, b = sorted(r.sample(range(1, 20), 2))
    return [
        lambda: (f"Koordinata nurida A({a}) va B({b}) nuqtalar orasidagi masofa?", b - a, f"${b} - {a}$", [a + b]),
        lambda: (f"A({a}) nuqtadan 0 gacha masofa?", a, "Koordinata — 0 gacha masofa.", [a + 1, 0]),
        lambda: (f"Nuqta {a} dan o‘ngga {b} birlik siljidi. Yangi koordinata?", a + b, "O‘ngga — qo‘shamiz.", [b - a]),
        lambda: (f"Koordinata burchagida A({a}; {b}) nuqtaning ordinatasi?", b, "Ikkinchi son — ordinata (y).", [a]),
        lambda: (f"A({a}) va B({b}) ning o‘rtasidagi nuqta koordinatasi?", (a + b) // 2 if (a + b) % 2 == 0 else dk((a + b) / 2), "(a + b) : 2", [b - a]),
    ]


def o_mantiq(r):
    i1, i2, i3 = r.sample(ISM, 3)
    return [
        lambda: (f"{i1} {i2}dan baland, {i2} {i3}dan baland. Eng past kim? (1 — {i1}, 2 — {i2}, 3 — {i3})", 3, "Zanjir bo‘yicha.", [1, 2]),
        lambda: ("Qutida 5 ta qizil va 5 ta ko‘k shar. Qaramasdan, bir xil rangli 2 ta shar bo‘lishi uchun kamida nechta olish kerak?", 3, "2 ta har xil chiqishi mumkin, uchinchisi albatta takrorlaydi.", [2, 6]),
        lambda: ("Bitta kesish bilan tayoq 2 bo‘lakka bo‘linadi. 5 bo‘lak uchun necha kesish kerak?", 4, "Bo‘laklar soni − 1.", [5, 6]),
        lambda: ("«Barcha mushuklar hayvon. Mosh — mushuk.» Demak, Mosh hayvonmi? (1 — ha, 0 — yo‘q)", 1, "Mulohaza: umumiydan xususiyga.", [0]),
        lambda: ("Ketma-ketlik: 2, 4, 8, 16, … Keyingisi?", 32, "Har safar 2 marta.", [18, 24]),
    ]


def o_takror34(r):
    return [t for f in (o_qoshayir, o_kopaytir, o_bolish, o_perimetr34, o_tenglama34, o_olchov) for t in f(r)[:2]]


def oila_tanla(nom):
    n = re.sub(r"\s*\(\d+-dars\)", "", str(nom).lower()).strip()
    n = re.sub(r"^takrorlash\.\s*", "", n)   # «Takrorlash. Uzunlik» → mavzusi bo'yicha
    if re.fullmatch(r"takrorlash|yakuniy dar ?s|masalalar yechish|amaliy (topshiriqlar|masalalar( yechish)?)", n):
        return None   # umumiy dars — qayta qurishda bobdagi oldingi mavzu oilasi olinadi
    for pat, f in [
        (r"alomat|bo.luvchi|karrali", o_alomat), (r"to.plam|venn|eyler|qismto", o_toplam),
        (r"diagramma|chastota|grafik|ma.lumot|o.rta arifmetik", o_diag34), (r"koordinata|sonli nur|nuqta", o_koordinata),
        (r"mantiq|mulohaza", o_mantiq), (r"yaxlit|taqrib|chamal|xatolig", o_yaxlit), (r"o.nli", o_onli34),
        (r"kasr|ulush|qism", o_kasr34), (r"tenglama|tengsiz|tenglik", o_tenglama34), (r"harakat|tezlik|masofa|kechikish|quvlama", o_tezlik),
        (r"narx|qiymat|unumdor", o_meyor), (r"perimetr|yuz|paletka|nostandart|to.ldirish", o_perimetr34),
        (r"kub|kuboid|parallelepiped|prizma|piramida|silindr|konus|shar|yoyilma|hajm", o_jism34),
        (r"burchak|parallel|perpendikul|simmetr|aylana|doira|transportir|naqsh|kesma", o_geom34),
        (r"uzunlik|massa|kilogramm|tonna|soat|vaqt|birlik", o_olchov), (r"bo.lish|qoldiq", o_bolish),
        (r"ko.paytir|taqsimot|10, 100", o_kopaytir), (r"qo.shish|ayirish|qulay usul", o_qoshayir),
        (r"son|xona|sanoq|o.qilish|1 dan 100|uch xonali|nol bilan", o_sonlar34)]:
        if re.search(pat, n):
            return f
    return o_takror34
