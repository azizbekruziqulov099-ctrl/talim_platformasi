"""REV511: 7–11-sinf algebra va geometriya — har mavzuga ma'nosi bilan farq qiladigan topshiriqlar (xilma5 uslubida)."""
import math, random, re
from fractions import Fraction as F
from xilma5 import ISM, kf, dk

UCHLIK = [(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15), (7, 24, 25), (12, 16, 20)]


def _f(x):
    x = F(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


# ───────────── ALGEBRA ─────────────
def a_ifoda(r):
    a, b, c, x = r.randint(2, 9), r.randint(2, 9), r.randint(-6, 6) or 3, r.randint(-5, 6) or 2
    return [
        lambda: (f"$x = {x}$ bo‘lsa, ${a}x^2 - {b}x$ qiymati?", a * x * x - b * x, f"${a} \\cdot {x * x} - {b} \\cdot ({x})$", [a * x * x + b * x, (a - b) * x]),
        lambda: (f"Ixchamlang: ${a}x + {b}y - {a - 1}x + {c}y$ — $y$ oldidagi koeffitsient?", b + c, f"${b} + ({c})$", [b - c, a + b]),
        lambda: (f"Qavsni oching: $-{a}(x - {b})$ — ozod had?", a * b, f"$-{a}x + {a * b}$", [-a * b, b]),
        lambda: (f"Ikki son yig‘indisi $s$, biri $x$. Ikkinchisi va birinchisining ayirmasi qaysi? (1) $s - 2x$ (2) $s - x$ (3) $2x - s$", 1, "Ikkinchisi $s - x$; ayirma $s - x - x$.", [2, 3]),
        lambda: (f"$a = {a}$, $b = {b}$ bo‘lsa, $(a - b)^2$?", (a - b) ** 2, f"$({a - b})^2$", [a * a - b * b, (a - b) * 2]),
        lambda: (f"Malika: «$-{a}(x - {b}) = -{a}x - {a * b}$». To‘g‘ri ozod had?", a * b, "Minusni qavs ichidagi har hadga ko‘paytirish: $-{a} \\cdot (-{b}) = +{a * b}$".replace("{a}", str(a)).replace("{b}", str(b)).replace("{a * b}", str(a * b)), [-a * b]),
    ]


def a_daraja(r):
    m, n = r.randint(2, 6), r.randint(2, 5); b = r.choice([2, 3, 5])
    p = r.choice([(8, F(2, 3), 4), (27, F(2, 3), 9), (16, F(3, 4), 8), (32, F(3, 5), 8), (64, F(1, 3), 4), (81, F(3, 4), 27)])
    return [
        lambda: (f"$a^{{{m}}} \\cdot a^{{{n}}} = a^{{?}}$", m + n, "Asoslar bir xil — ko‘rsatkichlar qo‘shiladi.", [m * n, m - n]),
        lambda: (f"$(a^{{{m}}})^{{{n}}} = a^{{?}}$", m * n, "Darajani darajaga — ko‘paytiriladi.", [m + n]),
        lambda: (f"${b}^{{{n + 1}}} : {b}^{{{n - 1}}}$", b * b, f"${b}^{{2}}$", [b, b ** (n + 1)]),
        lambda: (f"${p[0]}^{{{p[1].numerator}/{p[1].denominator}}}$", p[2], f"$\\sqrt[{p[1].denominator}]{{{p[0]}}}$ ni ${p[1].numerator}$-darajaga ko‘taramiz.", [p[0] * p[1].numerator // p[1].denominator, p[2] * 2]),
        lambda: (f"${b}^{{0}} + {b}^{{1}}$", 1 + b, "$a^0 = 1$", [b, 2 * b]),
        lambda: (f"$\\sqrt{{{(n * 3) ** 2}}}$", n * 3, "Arifmetik ildiz — nomanfiy.", [-(n * 3), (n * 3) ** 2]),
        lambda: (f"Zarina: «$2^3 \\cdot 2^2 = 2^6$». To‘g‘ri ko‘rsatkich?", 5, "Ko‘rsatkichlar qo‘shiladi, ko‘paytirilmaydi.", [6]),
    ]


def a_kophad(r):
    a, b = r.randint(1, 9), r.randint(1, 9); k, l = r.randint(2, 6), r.randint(2, 6)
    return [
        lambda: (f"$(x + {a})(x + {b})$ ko‘paytmada $x$ oldidagi koeffitsient?", a + b, f"$x^2 + ({a} + {b})x + {a * b}$", [a * b, 1]),
        lambda: (f"$(x + {a})(x + {b})$ ko‘paytmaning ozod hadi?", a * b, f"${a} \\cdot {b}$", [a + b]),
        lambda: (f"${k}x^2y \\cdot {l}xy^3$ birhadning koeffitsienti?", k * l, "Koeffitsientlar ko‘paytiriladi.", [k + l]),
        lambda: (f"$({k}x^2 + {a}x) + ({l}x^2 - {b}x)$ — $x^2$ oldidagi koeffitsient?", k + l, "O‘xshash hadlar qo‘shiladi.", [k * l, k - l]),
        lambda: (f"$({k * a}x^3 + {k * b}x^2) : {k}x^2$ — $x$ oldidagi koeffitsient?", a, f"${k * a}x^3 : {k}x^2 = {a}x$", [k * a, b]),
        lambda: (f"${k}x^3y^2$ birhadning darajasi?", 5, "Ko‘rsatkichlar yig‘indisi: 3 + 2.", [3, 6]),
    ]


def a_qisqa(r):
    a, b = r.randint(2, 9), r.randint(1, 9); n = r.randint(21, 99)
    return [
        lambda: (f"$(x + {b})^2$ da $x$ oldidagi koeffitsient?", 2 * b, f"$x^2 + 2 \\cdot {b} \\cdot x + {b * b}$", [b, b * b]),
        lambda: (f"Qulay usulda: ${n}^2$", n * n, f"$({n // 10 * 10} + {n % 10})^2 = {(n // 10 * 10) ** 2} + {2 * (n // 10 * 10) * (n % 10)} + {(n % 10) ** 2}$", [n * n + 10, (n // 10 * 10) ** 2 + (n % 10) ** 2]),
        lambda: (f"${n}^2 - {n - 2 * a}^2$", (2 * n - 2 * a) * (2 * a), f"Kvadratlar ayirmasi: $({n} - {n - 2 * a})({n} + {n - 2 * a}) = {2 * a} \\cdot {2 * n - 2 * a}$", [(2 * a) ** 2, 2 * a]),
        lambda: (f"$x^2 - {b * b} = 0$ tenglamaning musbat ildizi?", b, f"$(x - {b})(x + {b}) = 0$", [b * b, -b]),
        lambda: (f"$(x - {a})^3$ da $x^2$ oldidagi koeffitsient?", -3 * a, f"$x^3 - 3 \\cdot {a}x^2 + …$", [3 * a, -a]),
        lambda: (f"Bekzod: «$(x + {b})^2 = x^2 + {b * b}$». Tushib qolgan had koeffitsienti?", 2 * b, "Ikkilangan ko‘paytma $2bx$ unutilgan.", [b]),
        lambda: (f"${a}^3 + {b}^3$ ni $({a} + {b})(…)$ ko‘rinishida yozing — qavsdagi ifoda qiymati?", a * a - a * b + b * b, "Kublar yig‘indisi: $(a + b)(a^2 - ab + b^2)$", [a * a + a * b + b * b]),
    ]


def a_ajratish(r):
    p, q = r.randint(1, 8), r.randint(1, 8); k = r.randint(2, 6)
    return [
        lambda: (f"$x^2 + {p + q}x + {p * q}$ ni $(x + a)(x + b)$ ko‘rinishida yozing — kattaroq son?", max(p, q), f"Yig‘indisi {p + q}, ko‘paytmasi {p * q}: {p} va {q}", [p + q, p * q]),
        lambda: (f"${k}x^2 + {k * p}x$ dan umumiy ko‘paytuvchini chiqaring — qavs ichidagi ozod had?", p, f"${k}x(x + {p})$", [k * p, k]),
        lambda: (f"$x^2 - {p * p}$ = $(x - ?)(x + ?)$", p, "Kvadratlar ayirmasi.", [p * p]),
        lambda: (f"$ax + ay + {k}x + {k}y$ = $(a + {k})(…)$ — qavsdagi ifoda? (1) $x + y$ (2) $x - y$ (3) $xy$", 1, "Guruhlash usuli.", [2, 3]),
        lambda: (f"$x^2 - {2 * p}x + {p * p}$ — qaysi formula? (1) $(x - {p})^2$ (2) $(x + {p})^2$ (3) $(x - {p})(x + {p})$", 1, "Ayirmaning kvadrati.", [2, 3]),
    ]


def a_kasr(r):
    a, b, x = r.randint(2, 9), r.randint(2, 9), r.randint(2, 6)
    return [
        lambda: (f"$\\frac{{x^2 - {a * a}}}{{x - {a}}}$ ni qisqartiring va $x = {x}$ da qiymatini toping.", x + a, f"$\\frac{{(x - {a})(x + {a})}}{{x - {a}}} = x + {a}$", [x - a, x * x - a * a]),
        lambda: (f"$\\frac{{{a}}}{{x}} + \\frac{{{b}}}{{x}}$ — surat?", a + b, "Maxrajlar bir xil.", [a * b]),
        lambda: (f"$\\frac{{{a}}}{{x}} \\cdot \\frac{{x^2}}{{{b * a}}}$ ni soddalashtiring va $x = {b * x}$ da qiymati?", x, f"$\\frac{{x}}{{{b}}}$", [b * x, a]),
        lambda: (f"$\\frac{{1}}{{x - {a}}}$ ifoda $x$ ning qaysi qiymatida ma’noga ega emas?", a, "Maxraj nolga teng bo‘lmasligi kerak.", [-a, 0]),
        lambda: (f"$\\frac{{1}}{{{a}}} + \\frac{{1}}{{{b}}}$", _f(F(1, a) + F(1, b)), "Umumiy maxraj.", [_f(F(2, a + b))]),
        lambda: (f"Otabek: «$\\frac{{x + {a}}}{{x}} = {a}$» (x ni qisqartirdi). $x = 1$ da to‘g‘ri qiymat?", 1 + a, "Yig‘indidagi hadni qisqartirib bo‘lmaydi.", [a]),
    ]


def a_chiziqli(r):
    a, b, x = r.randint(2, 9), r.randint(1, 20), r.randint(-6, 12) or 4; c = a * x + b
    return [
        lambda: (f"${a}x + {b} = {c}$", x, f"${a}x = {c - b}$; $x = {x}$", [x + 1, (c + b) // a]),
        lambda: (f"${a}(x - {b}) = {a * (x - b)}$", x, f"$x - {b} = {x - b}$", [x - b, x + b]),
        lambda: (f"${a}x - {b} = {a - 1}x + {x - b}$", x, "Noma’lumlarni bir tomonga yig‘amiz.", [x - b, -x]),
        lambda: (f"Otasi o‘g‘lidan {a + 2} marta katta, birgalikda {(a + 3) * (x + 8)} yosh. O‘g‘li necha yoshda?", x + 8, f"$x + {a + 2}x = {(a + 3) * (x + 8)}$", [(a + 2) * (x + 8)]),
        lambda: (f"$x^2 + {2 * b}x = {x * x + 2 * b * x if x > 0 else 16 + 8 * b}$ (al-Xorazmiy usuli) — musbat ildiz?", x if x > 0 else 4, f"Kvadratgacha to‘ldiramiz: $(x + {b})^2 = …$", [b, 2 * b]),
        lambda: (f"Sardor: «${a}x = {a * x}$ dan $x = {a * x} - {a}$». To‘g‘ri ildiz?", x, f"{a} ga bo‘lish kerak.", [a * x - a]),
    ]


def a_sistema(r):
    x, y = r.randint(-5, 9) or 3, r.randint(-5, 9) or 2; a, b = r.randint(2, 5), r.randint(2, 5)
    return [
        lambda: (f"$x + y = {x + y}$, $x - y = {x - y}$. $x$ = ?", x, "Tenglamalarni qo‘shamiz: $2x = …$", [y, x + y]),
        lambda: (f"$x + y = {x + y}$, $x - y = {x - y}$. $y$ = ?", y, "Ayiramiz: $2y = …$", [x]),
        lambda: (f"${a}x + y = {a * x + y}$, $x - y = {x - y}$. $x$ = ?", x, "Qo‘shish usuli.", [y, x + 1]),
        lambda: (f"Daftar va ruchka {(x + 5) * 100 + (y + 6) * 100} so‘m, 2 daftar va ruchka {2 * (x + 5) * 100 + (y + 6) * 100} so‘m. Daftar narxi?", (x + 5) * 100, "Ikkinchidan birinchisini ayiramiz.", [(y + 6) * 100]),
        lambda: (f"$y = {a}x$ va $y = x + {(a - 1) * x}$ to‘g‘ri chiziqlar kesishgan nuqtaning abssissasi?", x, f"${a}x = x + {(a - 1) * x}$", [a * x]),
    ]


def a_funksiya(r):
    k, b, x0 = r.randint(-4, 5) or 2, r.randint(-6, 6), r.randint(-3, 4); x1, x2 = r.randint(-3, 0), r.randint(1, 4)
    return [
        lambda: (f"$y = {k}x + {b}$, $x = {x0}$ da $y$?", k * x0 + b, f"${k} \\cdot {x0} + {b}$", [k + x0 + b, k * x0]),
        lambda: (f"To‘g‘ri chiziq $({x1}; {k * x1 + b})$ va $({x2}; {k * x2 + b})$ nuqtalardan o‘tadi. Burchak koeffitsienti?", k, "$k = \\frac{y_2 - y_1}{x_2 - x_1}$", [b, -k]),
        lambda: (f"$y = {k}x + {b}$ grafigi $Oy$ o‘qini qaysi nuqtada kesadi? ($y$ ni yozing)", b, "$x = 0$ da.", [k, -b]),
        lambda: (f"$y = \\frac{{{k * 6}}}{{x}}$, $x = {6 if k else 3}$ da $y$?", k, f"${k * 6} : 6$", [k * 6, 6]),
        lambda: (f"$y = \\frac{{1}}{{x - {abs(b) + 1}}}$ funksiya qaysi nuqtada aniqlanmagan?", abs(b) + 1, "Maxraj nol bo‘lmasin.", [-(abs(b) + 1), 0]),
        lambda: (f"$f(x) = x^2$ juftmi? (1 — juft, 2 — toq, 3 — hech biri)", 1, "$f(-x) = f(x)$.", [2, 3]),
        lambda: (f"$y = {k}x + {b}$ funksiya o‘suvchimi? (1 — ha, 0 — yo‘q)", int(k > 0), "k > 0 bo‘lsa o‘sadi.", [1 - int(k > 0)]),
    ]


def a_kvadrat(r):
    p, q = r.randint(-6, 7) or 2, r.randint(-6, 7) or 3
    s, pr = p + q, p * q
    return [
        lambda: (f"$x^2 {'-' if s >= 0 else '+'} {abs(s)}x {'+' if pr >= 0 else '-'} {abs(pr)} = 0$ — kattaroq ildiz?", max(p, q), f"Viyet: yig‘indi {s}, ko‘paytma {pr}", [min(p, q), s]),
        lambda: (f"$x^2 {'-' if s >= 0 else '+'} {abs(s)}x {'+' if pr >= 0 else '-'} {abs(pr)} = 0$ — ildizlar yig‘indisi?", s, "Viyet teoremasi: $-b$.", [-s, pr]),
        lambda: (f"$x^2 {'-' if s >= 0 else '+'} {abs(s)}x {'+' if pr >= 0 else '-'} {abs(pr)} = 0$ — diskriminant?", s * s - 4 * pr, "$D = b^2 - 4ac$", [s * s + 4 * pr]),
        lambda: (f"${abs(p) + 1}x^2 = {(abs(p) + 1) * q * q}$ — musbat ildiz?", abs(q), "Chala kvadrat tenglama.", [q * q]),
        lambda: (f"$x^2 + {abs(p) + 1}x = 0$ — nolga teng bo‘lmagan ildiz?", -(abs(p) + 1), "$x(x + …) = 0$", [abs(p) + 1]),
        lambda: (f"$x^4 - {p * p + q * q}x^2 + {p * p * q * q} = 0$ nechta haqiqiy ildizga ega?", 4 if abs(p) != abs(q) else 2, "Bikvadrat: $t = x^2$; har musbat $t$ — ikki ildiz.", [2, 1]),
        lambda: (f"To‘g‘ri to‘rtburchak yuzi {(abs(p) + 2) * (abs(p) + 5)} sm², bo‘yi enidan 3 sm uzun. Eni?", abs(p) + 2, "$x(x + 3) = …$", [abs(p) + 5]),
    ]


def a_tengsizlik(r):
    a, b, c = r.randint(2, 7), r.randint(1, 15), r.randint(-4, 4); m = r.randint(1, 5)
    return [
        lambda: (f"${a}x - {b} < {a * c - b}$ — eng katta butun yechim?", c - 1, f"$x < {c}$", [c, c + 1]),
        lambda: (f"$-{a}x > {a * c}$ — eng katta butun yechim?", -c - 1, f"Manfiyga bo‘lganda belgi almashadi: $x < {-c}$", [-c, c - 1]),
        lambda: (f"$|x - {c}| \\le {m}$ — nechta butun yechim?", 2 * m + 1, f"${c - m} \\le x \\le {c + m}$", [2 * m, m]),
        lambda: (f"$(x - {c})(x - {c + m}) < 0$ — nechta butun yechim?", m - 1, f"${c} < x < {c + m}$", [m + 1, m]),
        lambda: (f"$x > {c}$ va $x \\le {c + m}$ — nechta butun yechim?", m, f"${c} < x \\le {c + m}$", [m + 1, m - 1]),
        lambda: (f"Jasur: «$-2x < 6$ dan $x < -3$». To‘g‘ri javobning chegarasi va belgisi: (1) $x > -3$ (2) $x < -3$ (3) $x > 3$", 1, "Manfiy songa bo‘lishda belgi o‘zgaradi.", [2, 3]),
    ]


def a_progressiya(r):
    a1, d, n = r.randint(-5, 9), r.randint(2, 6), r.randint(5, 12); b1, q = r.randint(1, 5), r.choice([2, 3])
    return [
        lambda: (f"Arifmetik progressiya: $a_1 = {a1}$, $d = {d}$. $a_{{{n}}}$ = ?", a1 + (n - 1) * d, "$a_n = a_1 + (n - 1)d$", [a1 + n * d, a1 * n]),
        lambda: (f"$a_1 = {a1}$, $d = {d}$ bo‘lgan arifmetik progressiyaning dastlabki {n} ta hadi yig‘indisi?", (2 * a1 + (n - 1) * d) * n // 2, "$S_n = \\frac{(2a_1 + (n - 1)d)n}{2}$", [(a1 + (n - 1) * d) * n]),
        lambda: (f"Geometrik progressiya: $b_1 = {b1}$, $q = {q}$. $b_5$ = ?", b1 * q ** 4, "$b_n = b_1 q^{n-1}$", [b1 * q ** 5, b1 * 5 * q]),
        lambda: (f"$b_1 = {b1}$, $q = {q}$: dastlabki 4 had yig‘indisi?", b1 * (q ** 4 - 1) // (q - 1), "$S_n = b_1 \\frac{q^n - 1}{q - 1}$", [b1 * q ** 4]),
        lambda: (f"Cheksiz kamayuvchi geometrik progressiya: $b_1 = {b1 * 2}$, $q = \\frac{{1}}{{2}}$. Yig‘indisi?", b1 * 4, "$S = \\frac{b_1}{1 - q}$", [b1 * 2, b1 * 3]),
        lambda: (f"{a1}, {a1 + d}, {a1 + 2 * d}, … ketma-ketlikning 10-hadi?", a1 + 9 * d, "Arifmetik progressiya.", [a1 + 10 * d]),
        lambda: (f"Har kuni avvalgisidan {d} ta ko‘p masala yechildi, 1-kuni {abs(a1) + 1} ta. 7-kuni nechta?", abs(a1) + 1 + 6 * d, "$a_7 = a_1 + 6d$", [abs(a1) + 1 + 7 * d]),
    ]


def a_trig(r):
    jad = {0: ("0", "1"), 30: ("1/2", "√3/2"), 45: ("√2/2", "√2/2"), 60: ("√3/2", "1/2"), 90: ("1", "0")}
    g = r.choice([30, 60, 90, 0]); d = r.choice([30, 45, 60, 90, 120, 180, 270])
    return [
        lambda: (f"$\\sin {g}°$ = ?", jad[g][0], "Asosiy qiymatlar jadvali.", [jad[g][1]]),
        lambda: (f"$\\cos {g}°$ = ?", jad[g][1], "Asosiy qiymatlar jadvali.", [jad[g][0]]),
        lambda: (f"${d}°$ necha radian? ($\\pi$ ning qismida, masalan 1/2)", _f(F(d, 180)), "$1° = \\frac{\\pi}{180}$", [_f(F(d, 360)), str(d)]),
        lambda: (f"$\\sin^2 {d}° + \\cos^2 {d}°$ = ?", 1, "Asosiy trigonometrik ayniyat.", [0, 2]),
        lambda: (f"$\\sin {d}°$ ishorasi: (1) musbat (2) manfiy (3) nol", 1 if 0 < d < 180 else 3 if d % 180 == 0 else 2, "Choraklar bo‘yicha.", [x for x in (1, 2, 3) if x != (1 if 0 < d < 180 else 3 if d % 180 == 0 else 2)]),
        lambda: ("$2\\sin 15° \\cos 15°$ = ?", "1/2", "$\\sin 2α$: $\\sin 30°$", ["√3/2"]),
        lambda: ("$\\cos(180° - 60°)$ = ?", "-1/2", "Keltirish formulasi: $-\\cos 60°$", ["1/2"]),
        lambda: ("$\\sin x = \\frac{1}{2}$, $0° < x < 90°$. $x$ = ? (gradusda)", 30, "Jadvaldan.", [60, 45]),
    ]


def a_statistika(r):
    xs = sorted(r.randint(2, 20) for _ in range(5)); xs[2] = xs[1]
    return [
        lambda: (f"Qator: {', '.join(map(str, xs))}. Medianasi?", xs[2], "O‘rtadagi had.", [sum(xs) // 5, xs[0]]),
        lambda: (f"Qator: {', '.join(map(str, xs))}. Modasi?", xs[1], "Eng ko‘p uchraydigan.", [xs[2] + 1, xs[-1]]),
        lambda: (f"Qator: {', '.join(map(str, xs))}. Kengligi (max − min)?", xs[-1] - xs[0], "Eng katta − eng kichik.", [xs[-1]]),
        lambda: (f"Qator: {', '.join(map(str, xs))}. O‘rta qiymati (bir xonagacha)?", dk(round(sum(xs) / 5, 1)), "Yig‘indi : soni.", [xs[2]]),
        lambda: (f"Haqiqiy uzunlik 50 sm, o‘lchangan 48 sm. Nisbiy xatolik necha foiz?", 4, "$\\frac{2}{50} \\cdot 100\\%$", [2, 48]),
        lambda: (f"{dk(xs[-1] + 0.46)} ni o‘ndan birlargacha yaxlitlang.", dk(round(xs[-1] + 0.46, 1)), "Yuzdan birlar raqami 6 ≥ 5.", [dk(xs[-1] + 0.4)]),
    ]


def a_kombinatorika(r):
    n, k = r.randint(4, 8), r.randint(2, 3); a, b = r.randint(2, 5), r.randint(2, 6)
    return [
        lambda: (f"${n}!$ = ?", math.factorial(n), "1 dan n gacha ko‘paytma.", [n * (n - 1), math.factorial(n - 1)]),
        lambda: (f"{n} kishi bir qatorga necha xil usulda turishi mumkin?", math.factorial(n), "O‘rin almashtirish: $n!$", [n * n]),
        lambda: (f"{n} kishidan {k} kishilik navbatchilar (tartib muhim emas) necha usulda tanlanadi?", math.comb(n, k), "$C_n^k$", [math.perm(n, k)]),
        lambda: (f"{n} kishidan sardor va o‘rinbosar necha usulda tanlanadi?", n * (n - 1), "Tartib muhim: $A_n^2$", [math.comb(n, 2)]),
        lambda: (f"{a} xil ko‘ylak va {b} xil shim bilan necha xil kiyinish mumkin?", a * b, "Ko‘paytirish qoidasi.", [a + b]),
        lambda: ("1, 2, 3, 4 raqamlaridan (takrorlanmasdan) nechta uch xonali son tuziladi?", 24, "$4 \\cdot 3 \\cdot 2$", [64, 12]),
    ]


def a_ehtimol(r):
    q, k = r.randint(3, 8), r.randint(2, 6)
    return [
        lambda: (f"Qutida {q} qizil va {k} ko‘k shar. Tasodifan olingan shar qizil bo‘lish ehtimoli?", _f(F(q, q + k)), "Qulay holatlar : barcha holatlar.", [_f(F(k, q + k)), _f(F(1, 2))]),
        lambda: ("Zar tashlandi. Juft son tushish ehtimoli?", "1/2", "2, 4, 6 — 3 ta 6 tadan.", ["1/3", "1/6"]),
        lambda: ("Ikkita tanga tashlandi. Ikkalasi ham gerb bo‘lish ehtimoli?", "1/4", "GG, GR, RG, RR — 1 ta qulay.", ["1/2", "1/3"]),
        lambda: ("Zar tashlandi. 7 tushish ehtimoli?", 0, "Mumkin bo‘lmagan hodisa.", ["1/7", "1/6"]),
        lambda: (f"100 marta tashlashda {q * 5} marta «gerb» tushdi. Nisbiy chastota?", _f(F(q * 5, 100)), "Ro‘y berishlar : sinovlar.", [_f(F(1, 2))]),
        lambda: ("Ikki zar tashlandi. Yig‘indi 12 bo‘lish ehtimoli?", "1/36", "Faqat (6; 6).", ["1/12", "1/6"]),
    ]


def a_log(r):
    b, n = r.choice([2, 3, 5]), r.randint(2, 5)
    return [
        lambda: (f"$\\log_{{{b}}} {b ** n}$", n, f"${b}^{n} = {b ** n}$", [b ** n // b, b]),
        lambda: (f"${b}^x = {b ** n}$", n, "Asoslar teng — ko‘rsatkichlar teng.", [b ** n, n + 1]),
        lambda: (f"$\\log_{{{b}}} x = {n}$", b ** n, "$x = b^n$", [b * n, n]),
        lambda: (f"$\\log_2 8 + \\log_2 4$", 5, "$3 + 2$", [6, 12]),
        lambda: (f"$\\log_{{{b}}} {b * b} \\cdot \\log_{{{b}}} {b}$", 2, "$2 \\cdot 1$", [3, b]),
        lambda: (f"${b}^{{x}} > {b ** n}$ — eng kichik butun yechim?", n + 1, "Asos > 1 — belgi saqlanadi: $x > n$.", [n, n - 1]),
        lambda: (f"$\\sqrt{{x + {n}}} = {n + 1}$", (n + 1) ** 2 - n, "Ikkala tomonni kvadratga ko‘taramiz.", [(n + 1) ** 2, n + 1]),
    ]


def a_hosila(r):
    a, b, x0 = r.randint(1, 5), r.randint(-6, 6), r.randint(-2, 3)
    return [
        lambda: (f"$f(x) = {a}x^2 + {b}x$. $f'({x0})$ = ?", 2 * a * x0 + b, "$f'(x) = 2ax + b$", [a * x0 * x0 + b * x0, 2 * a + b]),
        lambda: (f"$f(x) = x^3$. $f'({x0})$ = ?", 3 * x0 * x0, "$3x^2$", [x0 ** 3, 3 * x0]),
        lambda: (f"$y = {a}x^2 + {b}x$ ga $x_0 = {x0}$ nuqtada urinma burchak koeffitsienti?", 2 * a * x0 + b, "Urinma koeffitsienti = $f'(x_0)$.", [a * x0 * x0 + b * x0]),
        lambda: (f"$f(x) = x^2 - {2 * a}x$ minimum nuqtasi ($x$)?", a, "$f'(x) = 0$", [2 * a, -a]),
        lambda: (f"$\\int_0^{{{a}}} 2x\\,dx$", a * a, "$x^2$ dan $0$ dan $a$ gacha.", [2 * a, a]),
        lambda: (f"$\\lim_{{x \\to {x0}}} (x^2 + {b})$", x0 * x0 + b, "Uzluksiz funksiya — qiymatni qo‘yamiz.", [x0 + b]),
        lambda: (f"Jism $s(t) = {a}t^2$ qonun bilan harakatlanmoqda. $t = 3$ da tezligi?", 6 * a, "Tezlik = $s'(t) = 2at$.", [9 * a, 3 * a]),
    ]


# ───────────── GEOMETRIYA ─────────────
def g_burchak(r):
    a = r.randint(25, 155)
    return [
        lambda: (f"Qo‘shni burchaklardan biri ${a}°$. Ikkinchisi?", 180 - a, "Yig‘indi $180°$.", [a, 90 - a % 90]),
        lambda: (f"Vertikal burchaklardan biri ${a}°$. Ikkinchisi?", a, "Teng.", [180 - a]),
        lambda: (f"${2 * (a // 2)}°$ li burchak bissektrisasi hosil qilgan burchak?", a // 2, "Teng ikkiga bo‘ladi.", [a, 180 - a]),
        lambda: (f"Parallel to‘g‘ri chiziqlar va kesuvchi: ichki almashinuvchi burchaklardan biri ${a}°$. Ikkinchisi?", a, "Ichki almashinuvchi burchaklar teng.", [180 - a]),
        lambda: (f"Parallel to‘g‘ri chiziqlar: ichki bir tomonli burchaklardan biri ${a}°$. Ikkinchisi?", 180 - a, "Yig‘indisi $180°$.", [a]),
        lambda: (f"Ikki to‘g‘ri chiziq kesishganda hosil bo‘lgan burchaklardan uchtasining yig‘indisi ${360 - a}°$. To‘rtinchisi?", a, "To‘rttasi $360°$.", [180 - a]),
    ]


def g_uchburchak(r):
    a, b = r.randint(30, 80), r.randint(30, 70)
    return [
        lambda: (f"Uchburchakning ikki burchagi ${a}°$ va ${b}°$. Uchinchisi?", 180 - a - b, "Yig‘indi $180°$.", [a + b]),
        lambda: (f"Uchburchakning tashqi burchagi ${a + b}°$, unga qo‘shni bo‘lmagan bir ichki burchak ${a}°$. Ikkinchisi?", b, "Tashqi burchak qo‘shni bo‘lmagan ikki ichki burchak yig‘indisiga teng.", [180 - a - b]),
        lambda: (f"Teng yonli uchburchakning asosidagi burchagi ${a}°$. Uchidagi burchak?", 180 - 2 * a, "Asosdagi burchaklar teng.", [a, 180 - a]),
        lambda: (f"Tomonlari {a // 10} sm, {b // 10} sm va {a // 10 + b // 10 + 1} sm uchburchak mavjudmi? (1 — ha, 0 — yo‘q)", 0, "Uchburchak tengsizligi: eng katta tomon qolgan ikkitasi yig‘indisidan kichik bo‘lishi shart.", [1]),
        lambda: (f"To‘g‘ri burchakli uchburchakda $30°$ qarshisidagi katet {a // 5} sm. Gipotenuza?", 2 * (a // 5), "$30°$ qarshisidagi katet gipotenuzaning yarmi.", [a // 5]),
        lambda: (f"Uchburchakda katta tomon qarshisida qanday burchak yotadi? (1 — katta, 2 — kichik)", 1, "Katta tomon qarshisida katta burchak.", [2]),
    ]


def g_pifagor(r):
    a, b, c = r.choice(UCHLIK)
    return [
        lambda: (f"Katetlari {a} va {b}. Gipotenuza?", c, f"$\\sqrt{{{a * a} + {b * b}}}$", [a + b, c + 1]),
        lambda: (f"Gipotenuza {c}, bir katet {a}. Ikkinchi katet?", b, f"$\\sqrt{{{c * c} - {a * a}}}$", [c - a]),
        lambda: (f"To‘g‘ri to‘rtburchak tomonlari {a} va {b}. Diagonali?", c, "Pifagor teoremasi.", [a + b]),
        lambda: (f"Teng yonli uchburchakning yon tomoni {c}, asosi {2 * a}. Asosga tushirilgan balandlik?", b, "Balandlik asosni teng ikkiga bo‘ladi.", [c - a]),
        lambda: (f"{c} m narvon devorga tiralgan, pastki uchi devordan {a} m. Narvon devorning qancha balandligiga yetadi?", b, "Pifagor.", [c - a]),
        lambda: (f"Tomonlari {a}, {b}, {c} bo‘lgan uchburchak to‘g‘ri burchaklimi? (1 — ha, 0 — yo‘q)", 1, f"${a * a} + {b * b} = {c * c}$ — teskari teorema.", [0]),
    ]


def g_yuz(r):
    a, h, d1, d2 = r.randint(4, 14), r.randint(3, 10), r.randint(2, 9) * 2, r.randint(2, 9) * 2; b = a + r.randint(2, 8)
    return [
        lambda: (f"Parallelogramm asosi {a}, balandligi {h}. Yuzi?", a * h, "$S = ah$", [a * h // 2, 2 * (a + h)]),
        lambda: (f"Romb diagonallari {d1} va {d2}. Yuzi?", d1 * d2 // 2, "$S = \\frac{d_1 d_2}{2}$", [d1 * d2]),
        lambda: (f"Trapetsiya asoslari {a} va {b}, balandligi {h * 2}. Yuzi?", (a + b) * h, "$S = \\frac{a + b}{2}h$", [(a + b) * h * 2]),
        lambda: (f"Trapetsiya asoslari {a} va {b}. O‘rta chizig‘i? (o‘nli kasr bo‘lsa vergul bilan)", dk((a + b) / 2), "O‘rta chiziq — asoslar yarim yig‘indisi.", [dk(b - a)]),
        lambda: ("Tomonlari 13, 14, 15 bo‘lgan uchburchak yuzi (Geron)?", 84, "$p = 21$; $\\sqrt{21 \\cdot 8 \\cdot 7 \\cdot 6} = 84$", [42, 168]),
        lambda: (f"Uchburchakning o‘rta chizig‘i {a}. Unga parallel tomoni?", 2 * a, "O‘rta chiziq tomonning yarmi.", [a]),
        lambda: (f"Kvadrat diagonali {d1}. Yuzi?", d1 * d1 // 2, "$S = \\frac{d^2}{2}$", [d1 * d1]),
    ]


def g_kopburchak(r):
    n = r.choice([5, 6, 8, 9, 10, 12])
    return [
        lambda: (f"Qavariq {n}-burchak ichki burchaklari yig‘indisi?", (n - 2) * 180, "$(n - 2) \\cdot 180°$", [n * 180, (n - 1) * 180]),
        lambda: (f"Muntazam {n}-burchakning har bir ichki burchagi? (butun bo‘lmasa, vergul bilan)", dk((n - 2) * 180 / n), "Yig‘indi : n.", [dk(360 / n)]),
        lambda: (f"Qavariq {n}-burchak tashqi burchaklari yig‘indisi (har uchida bittadan)?", 360, "Har doim $360°$.", [(n - 2) * 180]),
        lambda: (f"{n}-burchakning nechta diagonali bor?", n * (n - 3) // 2, "$\\frac{n(n - 3)}{2}$", [n * (n - 3)]),
        lambda: (f"Muntazam ko‘pburchakning tashqi burchagi ${360 // n}°$. Tomonlari soni?", n, "$360° : $ tashqi burchak.", [n + 1]),
    ]


def g_aylana(r):
    rr = r.randint(2, 12); g = r.randint(20, 80) * 2; a, b, c = r.choice(UCHLIK)
    return [
        lambda: (f"Markaziy burchak ${g}°$. Shu yoyga tiralgan ichki chizilgan burchak?", g // 2, "Yarmiga teng.", [g, 180 - g]),
        lambda: ("Diametrga tiralgan ichki chizilgan burchak?", 90, "Yarim aylanaga tiralgan — $90°$.", [180, 45]),
        lambda: (f"Radiusi {c} bo‘lgan aylanada markazdan {a} masofadagi vatar uzunligi?", 2 * b, f"Yarim vatar: $\\sqrt{{{c * c} - {a * a}}} = {b}$", [b, c]),
        lambda: ("Urinma va urinish nuqtasiga o‘tkazilgan radius orasidagi burchak?", 90, "Urinma radiusga perpendikulyar.", [180, 45]),
        lambda: (f"Radiusi {rr} aylana uzunligi ($\\pi \\approx 3{{,}}14$)?", dk(round(2 * 3.14 * rr, 2)), "$2\\pi r$", [dk(round(3.14 * rr * rr, 2))]),
        lambda: (f"Radiusi {rr}, markaziy burchagi $90°$ bo‘lgan sektor yuzi ($\\pi \\approx 3{{,}}14$)?", dk(round(3.14 * rr * rr / 4, 2)), "Doira yuzining to‘rtdan biri.", [dk(round(3.14 * rr * rr, 2))]),
        lambda: (f"Muntazam oltiburchakka tashqi chizilgan aylana radiusi {rr}. Oltiburchak tomoni?", rr, "Muntazam oltiburchakda tomon = R.", [2 * rr]),
    ]


def g_vektor(r):
    a, b, c = r.choice(UCHLIK); x1, y1 = r.randint(-4, 4), r.randint(-4, 4); p, q = r.randint(-3, 4), r.randint(-3, 4)
    return [
        lambda: (f"A({x1}; {y1}), B({x1 + a}; {y1 + b}). $\\vec{{AB}}$ uzunligi?", c, "$\\sqrt{(Δx)^2 + (Δy)^2}$", [a + b]),
        lambda: (f"$\\vec a = ({p}; {q})$, $\\vec b = ({q}; {p})$. $\\vec a + \\vec b$ ning birinchi koordinatasi?", p + q, "Koordinatalar qo‘shiladi.", [p * q]),
        lambda: (f"$\\vec a = ({p}; {q})$, $\\vec b = ({q}; {-p})$. Skalyar ko‘paytma?", 0, f"${p} \\cdot {q} + {q} \\cdot ({-p}) = 0$ — perpendikulyar.", [2 * p * q]),
        lambda: (f"$\\vec a = ({p}; {q})$. $3\\vec a$ ning ikkinchi koordinatasi?", 3 * q, "Har koordinata 3 ga.", [q + 3]),
        lambda: (f"$\\vec a = ({a}; {b})$ uzunligi?", c, "Pifagor.", [a + b]),
        lambda: (f"$\\vec a = ({p}; 2)$ va $\\vec b = (4; {-2 * p})$ perpendikulyarmi? (1 — ha, 0 — yo‘q)", int(4 * p - 4 * p == 0), "Skalyar ko‘paytma nol bo‘lsa.", [0]),
    ]


def g_oxshash(r):
    k = r.choice([2, 3, 4]); a = r.randint(3, 9); s = r.randint(2, 9)
    return [
        lambda: (f"O‘xshash uchburchaklarda o‘xshashlik koeffitsienti {k}. Kichigining tomoni {a}. Kattasining mos tomoni?", k * a, "Tomonlar k marta.", [a + k]),
        lambda: (f"O‘xshashlik koeffitsienti {k}. Yuzlar nisbati?", k * k, "Yuzlar $k^2$ nisbatda.", [k, 2 * k]),
        lambda: (f"Kichik uchburchak yuzi {s}, o‘xshashlik koeffitsienti {k}. Katta uchburchak yuzi?", s * k * k, "$S_2 = k^2 S_1$", [s * k]),
        lambda: (f"Fales: burchak tomonlarida parallel chiziqlar bir tomonda {a} va {a} kesmalar ajratdi. Ikkinchi tomondagi kesmalar nisbati?", 1, "Teng kesmalar — teng kesmalar.", [2]),
        lambda: (f"Bo‘yi {k * 50} sm tayoq soyasi {a * 10} sm. Shu paytda soyasi {a * 10 * 6} sm bo‘lgan daraxt bo‘yi necha sm?", k * 50 * 6, "O‘xshash uchburchaklar.", [k * 50 + a * 50]),
    ]


def g_trigteorema(r):
    a, b = r.randint(3, 9), r.randint(3, 9)
    return [
        lambda: (f"Uchburchakda $a = {a}$, $b = {b}$, ular orasidagi burchak $30°$. Yuzi? (vergul bilan)", dk(a * b / 4), "$S = \\frac{1}{2}ab\\sin C$", [dk(a * b / 2)]),
        lambda: (f"$a = {a}$, $b = {b}$, $C = 60°$. $c^2$ = ?", a * a + b * b - a * b, "Kosinuslar teoremasi: $c^2 = a^2 + b^2 - 2ab\\cos C$", [a * a + b * b]),
        lambda: (f"$a = {a}$, $b = {b}$, $C = 90°$. $c^2$ = ?", a * a + b * b, "$\\cos 90° = 0$ — Pifagor.", [a * a + b * b - a * b]),
        lambda: (f"Sinuslar teoremasi: $a = {2 * a}$, $A = 30°$. Tashqi chizilgan aylana radiusi?", 2 * a, "$\\frac{a}{\\sin A} = 2R$", [a]),
        lambda: ("Uchburchakda $a^2 > b^2 + c^2$ bo‘lsa, $A$ burchak qanday? (1 — o‘tkir, 2 — to‘g‘ri, 3 — o‘tmas)", 3, "$\\cos A < 0$.", [1, 2]),
    ]


def g_koordinata(r):
    a, b, c = r.choice(UCHLIK); x, y = r.randint(-5, 5), r.randint(-5, 5); u, v = r.randint(-5, 5), r.randint(-5, 5)
    return [
        lambda: (f"A({x}; {y}) va B({x + a}; {y - b}) orasidagi masofa?", c, "Masofa formulasi.", [a + b]),
        lambda: (f"A({x}; {y}) va B({x + 2 * u}; {y + 2 * v}) kesma o‘rtasining abssissasi?", x + u, "$\\frac{x_1 + x_2}{2}$", [2 * x + 2 * u]),
        lambda: (f"Fazoda A(0; 0; 0) va B(2; 3; 6) orasidagi masofa?", 7, "$\\sqrt{4 + 9 + 36}$", [11, 6]),
        lambda: (f"A({x}; {y}) nuqtaning $Ox$ o‘qiga nisbatan simmetrigining ordinatasi?", -y, "Ordinata ishorasi almashadi.", [y]),
    ]


def g_stereo(r):
    a, b, c = r.randint(2, 9), r.randint(2, 9), r.randint(2, 9); rr, h = r.randint(1, 6), r.randint(2, 9)
    return [
        lambda: (f"To‘g‘ri burchakli parallelepiped {a}×{b}×{c}. Hajmi?", a * b * c, "$V = abc$", [2 * (a * b + b * c + a * c)]),
        lambda: (f"To‘g‘ri burchakli parallelepiped {a}×{b}×{c}. To‘la sirti?", 2 * (a * b + b * c + a * c), "$2(ab + bc + ac)$", [a * b * c]),
        lambda: (f"Piramida asosining yuzi {a * 3}, balandligi {h}. Hajmi?", a * h, "$V = \\frac{1}{3}Sh$", [a * 3 * h]),
        lambda: (f"Silindr radiusi {rr}, balandligi {h}. Hajmi ($\\pi$ ning koeffitsienti)?", rr * rr * h, "$V = \\pi r^2 h$", [2 * rr * h]),
        lambda: (f"Konus radiusi {rr}, balandligi {h * 3}. Hajmi ($\\pi$ koeffitsienti)?", rr * rr * h, "$V = \\frac{1}{3}\\pi r^2 h$", [rr * rr * h * 3]),
        lambda: (f"Shar radiusi {rr * 3}. Hajmi ($\\pi$ koeffitsienti)?", 36 * rr ** 3, "$V = \\frac{4}{3}\\pi r^3$", [4 * (rr * 3) ** 2]),
        lambda: (f"Sfera radiusi {rr}. Sirti ($\\pi$ koeffitsienti)?", 4 * rr * rr, "$S = 4\\pi r^2$", [rr * rr]),
        lambda: (f"Kub qirrasi 2 marta oshsa, hajmi necha marta oshadi?", 8, "$2^3$", [2, 4]),
    ]


def g_fazo(r):
    return [
        lambda: ("Bir to‘g‘ri chiziqda yotmagan uch nuqta orqali nechta tekislik o‘tadi?", 1, "Aksioma.", [3, 0]),
        lambda: ("Kesishmaydigan va parallel bo‘lmagan to‘g‘ri chiziqlar qanday ataladi? (1 — ayqash, 2 — parallel, 3 — perpendikulyar)", 1, "Ayqash to‘g‘ri chiziqlar.", [2, 3]),
        lambda: ("Ikki tekislik kesishsa, kesishmasi nima? (1 — to‘g‘ri chiziq, 2 — nuqta, 3 — tekislik)", 1, "To‘g‘ri chiziq.", [2, 3]),
        lambda: ("Kubda nechta juft ayqash qirralar bor (bitta qirraga nisbatan)?", 4, "Har qirraga 4 ta ayqash qirra.", [3, 8]),
        lambda: ("Tekislikka perpendikulyar to‘g‘ri chiziq shu tekislikdagi istalgan to‘g‘ri chiziqqa qanday? (1 — perpendikulyar, 2 — parallel)", 1, "Ta’rif bo‘yicha.", [2]),
        lambda: ("Uchburchakli piramidaning nechta qirrasi bor?", 6, "Asosda 3, yonda 3.", [4, 5]),
        lambda: ("Kub diagonali qirrasidan necha marta katta? (taqriban, vergul bilan ikki xona)", "1,73", "$a\\sqrt{3}$", ["1,41"]),
    ]


def aralash(r):
    return [t for f in (a_ifoda, a_chiziqli, a_daraja, g_burchak, g_uchburchak, g_pifagor) for t in f(r)[:2]]


def oila_tanla(nom):
    if nom == "__aralash__":
        return aralash
    n = re.sub(r"\s*\(\d+-dars\)", "", str(nom).lower()).strip()
    if re.search(r"^(\d+-test|takrorla|bobni takror|bilimingiz|amaliy mashq|masalalar yechish|yakuniy|loyiha|tarixiy|qo.shimcha|mantiqiy topshiriq|xalqaro baholash|\d+-§ ga|\d+-sinf)", n) and not re.search(r"§\.\s*\w", n):
        return None
    for pat, f in [
        (r"hosila|integral|limit|urinma va normal|boshlang.ich funksiya|differensial|tekshirish va grafik", a_hosila),
        (r"logarifm|ko.rsatkichli|irratsional", a_log), (r"ehtimol|hodisa|tasodifiy", a_ehtimol), (r"kombinator|tanlash usuli", a_kombinatorika),
        (r"moda|mediana|o.rta qiymat|ma.lumot|xatolik|yaxlit|taqribiy|nisbiy", a_statistika), (r"progressiya|ketma-ketlik", a_progressiya),
        (r"trigonometr|sinus|kosinus|tangens|radian|burish|keltirish formul|qo.shish formul|ikkilangan|α", a_trig),
        (r"kvadrat tenglama|viyet|diskriminant|chala kvadrat|bikvadrat|kvadrat uchhad|ikkinchi darajali tenglama", a_kvadrat),
        (r"tengsizlik|modul|oraliq|intervallar", a_tengsizlik), (r"sistema", a_sistema),
        (r"funksiya|grafik|dekart|y=|modellashtir", a_funksiya), (r"daraja|ildiz", a_daraja), (r"qisqa ko.paytirish|kvadrati|kubi|kvadratlar ayirmasi|kublar yig", a_qisqa),
        (r"ko.paytuvchi", a_ajratish), (r"algebraik kasr|kasr-ratsional|umumiy maxraj|ratsional", a_kasr), (r"birhad|ko.phad|o.xshash had", a_kophad),
        (r"tenglama|al-xorazmiy|ildizi", a_chiziqli), (r"ifoda|qavs|formula|xossalari|tenglik", a_ifoda),
        (r"vektor", g_vektor), (r"pifagor|balandligini topish|proporsional kesma|o.rta proporsional", g_pifagor),
        (r"o.xshash|gomotetiya|fales|proyeksiya va proporsional", g_oxshash),
        (r"sinuslar|kosinuslar|uchburchaklarni yechish|sinus yordamida", g_trigteorema),
        (r"aylana|doira|vatar|markaziy burchak|ichki chizilgan|tashqi chizilgan", g_aylana),
        (r"ko.pburchak|muntazam", g_kopburchak), (r"yuz|trapetsiya|romb|parallelogramm|kvadrat|to.g.ri to.rtburchak|o.rta chiziq|to.rtburchak|geron", g_yuz),
        (r"koordinat|simmetri|almashtirish|ko.chirish", g_koordinata),
        (r"prizma|piramida|silindr|konus|shar|sfera|ko.pyoq|hajm|sirt|kub", g_stereo),
        (r"fazo|tekislik|stereometriya|ayqash|perpendikulyar, og|uch perpendikulyar|proyeksiya", g_fazo),
        (r"uchburchak", g_uchburchak), (r"burchak|kesma|parallel|perpendikulyar|bissektrisa|geometrik shakl|yasash", g_burchak),
        (r"son|arifmetik amal", a_ifoda)]:
        if re.search(pat, n):
            return f
    return None
