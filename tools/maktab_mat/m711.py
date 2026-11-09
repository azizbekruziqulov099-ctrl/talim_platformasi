"""7–11-sinf: Algebra (yangi) va Geometriya (yangi) — alohida kurslar. Darslik mundarijasi + modellar (N108–N232)."""
import math, random, re
from fractions import Fraction
from m1 import M, D, toza, model_qatorlari, rows_test, model_savol
from m34 import fk


def fmt(x):
    if isinstance(x, Fraction):
        return fk(x)
    if isinstance(x, float):
        return f"{round(x, 2):g}".replace(".", ",")
    return str(x)


def gen711(tur, rng):
    r = rng.randint
    if tur == "ifoda":
        a, b, x = r(2, 9), r(1, 15), r(-5, 6)
        return (f"$x = {x}$ bo‘lganda ${a}x^2 - {b}$ ning qiymati?", a * x * x - b, f"${a} \\cdot ({x})^2 - {b} = {a * x * x} - {b} = {a * x * x - b}$", [a * x - b, a * x * x + b, (a * x) ** 2 - b])
    if tur == "daraja":
        m, n = r(2, 9), r(2, 9)
        return (f"$a^{{{m}}} \\cdot a^{{{n}}} = a^{{?}}$", m + n, f"Asoslar teng — ko‘rsatkichlar qo‘shiladi: ${m} + {n} = {m + n}$", [m * n, abs(m - n) or 1, m + n + 1])
    if tur == "kophad":
        a, b, c, d = r(1, 6), r(1, 9), r(1, 6), r(1, 9)
        return (f"$({a}x + {b})({c}x + {d})$ ko‘paytmada $x$ oldidagi koeffitsient?", a * d + b * c, f"$x$ li hadlar: ${a}x \\cdot {d} + {b} \\cdot {c}x = {a * d + b * c}x$", [a * c, b * d, a * d])
    if tur == "qisqa":
        a, b = r(1, 9), r(1, 9)
        return (f"$({a}x + {b})^2$ yoyilmasida $x$ oldidagi koeffitsient?", 2 * a * b, f"$(m+n)^2 = m^2 + 2mn + n^2$: $2 \\cdot {a}x \\cdot {b} = {2 * a * b}x$", [a * b, a * a, b * b])
    if tur == "kvayirma":
        a, b = r(30, 99), r(1, 29)
        x, y = a + b, a - b
        return (f"${x}^2 - {y}^2$ ni qulay usulda hisoblang.", x * x - y * y, f"$({x} - {y})({x} + {y}) = {x - y} \\cdot {x + y} = {x * x - y * y}$", [(x - y) ** 2, x * x, x + y])
    if tur == "ajrat":
        a = r(2, 12)
        return (f"$x^2 - {a * a} = (x - {a})(x + ?)$", a, f"Kvadratlar ayirmasi: $x^2 - {a}^2 = (x - {a})(x + {a})$", [a * a, 2 * a, a + 1])
    if tur == "chiziqli":
        a, x, b = r(2, 9), r(-9, 12), r(1, 30)
        return (f"${a}x + {b} = {a * x + b}$ tenglamani yeching.", x, f"${a}x = {a * x + b} - {b} = {a * x}$; $x = {a * x} : {a} = {x}$", [x + 1, -x if x else 2, a * x])
    if tur == "sistema":
        x, y = r(-5, 9), r(-5, 9); a, b = r(1, 5), r(1, 5)
        return (f"$\\begin{{cases}} x + y = {x + y} \\\\ {a}x - {b}y = {a * x - b * y} \\end{{cases}}$ bo‘lsa, $x$ = ?", x, f"Birinchidan $y = {x + y} - x$; ikkinchisiga qo‘yib: ${a + b}x = {a * x - b * y + b * (x + y)}$, $x = {x}$", [y, x + 1, x + y])
    if tur == "funksiya":
        k, b, x = r(-5, 6), r(-9, 9), r(-6, 6)
        return (f"$y = {k}x {'+' if b >= 0 else '-'} {abs(b)}$ funksiyaning $x = {x}$ dagi qiymati?", k * x + b, f"${k} \\cdot ({x}) {'+' if b >= 0 else '-'} {abs(b)} = {k * x + b}$", [k * x - b, k + x + b, k * x])
    if tur == "tengsizlik":
        a, b, c = r(2, 9), r(1, 20), r(21, 60)
        g = Fraction(c - b, a)
        return (f"${a}x + {b} > {c}$ tengsizlikning yechimi $x > ?$", fmt(g), f"${a}x > {c - b}$, $x > {fmt(g)}$", [fmt(Fraction(c + b, a)), fmt(g + 1), str(c - b)])
    if tur == "kasrqisq":
        a, b = r(2, 9), r(1, 9)
        return (f"$\\frac{{x^2 - {b * b}}}{{x - {b}}}$ ni qisqartiring va $x = {a}$ da hisoblang.", a + b, f"$\\frac{{(x - {b})(x + {b})}}{{x - {b}}} = x + {b} = {a} + {b} = {a + b}$", [a - b, a * b, a + b + 1])
    if tur == "ildiz":
        a = r(2, 25)
        return (f"$\\sqrt{{{a * a}}} = ?$", a, f"${a}^2 = {a * a}$", [a * 2, a * a // 2, a + 1])
    if tur == "ildizxossa":
        a, b = rng.choice([(2, 8), (3, 12), (2, 18), (5, 20), (3, 27), (2, 32)])
        return (f"$\\sqrt{{{a}}} \\cdot \\sqrt{{{b}}} = ?$", int(math.isqrt(a * b)), f"$\\sqrt{{{a} \\cdot {b}}} = \\sqrt{{{a * b}}} = {math.isqrt(a * b)}$", [a + b, a * b, math.isqrt(a * b) + 1])
    if tur == "kvtenglama":
        x1, x2 = r(-9, 9), r(-9, 9)
        b, c = -(x1 + x2), x1 * x2
        return (f"$x^2 {'+' if b >= 0 else '-'} {abs(b)}x {'+' if c >= 0 else '-'} {abs(c)} = 0$ tenglamaning katta ildizi?", max(x1, x2), f"$D = {b * b - 4 * c}$; ildizlar ${min(x1, x2)}$ va ${max(x1, x2)}$ (Viyet: yig‘indi ${x1 + x2}$, ko‘paytma ${c}$)", [min(x1, x2), -max(x1, x2) or 1, x1 + x2])
    if tur == "diskriminant":
        a, b, c = r(1, 5), r(-9, 9), r(-9, 9)
        return (f"$ {a}x^2 {'+' if b >= 0 else '-'} {abs(b)}x {'+' if c >= 0 else '-'} {abs(c)} = 0$ tenglamaning diskriminanti?", b * b - 4 * a * c, f"$D = b^2 - 4ac = {b * b} - 4 \\cdot {a} \\cdot ({c}) = {b * b - 4 * a * c}$", [b * b + 4 * a * c, b * b - a * c, 4 * a * c])
    if tur == "viyet":
        x1, x2 = r(-9, 9), r(1, 9)
        return (f"$x^2 + px + q = 0$ ning ildizlari ${x1}$ va ${x2}$. $q$ = ?", x1 * x2, f"Viyet teoremasi: $q = x_1 x_2 = {x1 * x2}$", [x1 + x2, -(x1 + x2), x1 - x2])
    if tur == "parabola":
        a, b = r(1, 4), r(-8, 8) * 2
        return (f"$y = {a}x^2 {'+' if b >= 0 else '-'} {abs(b)}x + 1$ parabola uchining abssissasi?", fmt(Fraction(-b, 2 * a)), f"$x_0 = -\\frac{{b}}{{2a}} = {fmt(Fraction(-b, 2 * a))}$", [fmt(Fraction(b, 2 * a)), fmt(Fraction(-b, a)), "0"])
    if tur == "arifprog":
        a1, d, n = r(-10, 20), r(-5, 9), r(5, 30)
        return (f"Arifmetik progressiyada $a_1 = {a1}$, $d = {d}$. $a_{{{n}}}$ = ?", a1 + (n - 1) * d, f"$a_n = a_1 + (n-1)d = {a1} + {n - 1} \\cdot {d} = {a1 + (n - 1) * d}$", [a1 + n * d, a1 * n, a1 + (n - 1) * d + d])
    if tur == "arifyig":
        a1, d, n = r(1, 10), r(1, 6), r(5, 20)
        s = n * (2 * a1 + (n - 1) * d) // 2
        return (f"$a_1 = {a1}$, $d = {d}$ bo‘lgan arifmetik progressiyaning dastlabki {n} ta hadi yig‘indisi?", s, f"$S_n = \\frac{{2a_1 + (n-1)d}}{{2}} \\cdot n = {s}$", [a1 + (n - 1) * d, s + d, n * a1])
    if tur == "geomprog":
        b1, q, n = r(1, 5), rng.choice([2, 3, -2]), r(3, 7)
        return (f"Geometrik progressiyada $b_1 = {b1}$, $q = {q}$. $b_{{{n}}}$ = ?", b1 * q ** (n - 1), f"$b_n = b_1 q^{{n-1}} = {b1} \\cdot ({q})^{{{n - 1}}} = {b1 * q ** (n - 1)}$", [b1 * q ** n, b1 * q * (n - 1), b1 + q ** (n - 1)])
    if tur == "cheksiz":
        b1, q = r(2, 20), rng.choice([Fraction(1, 2), Fraction(1, 3), Fraction(1, 4)])
        return (f"$b_1 = {b1}$, $q = {fk(q)}$ bo‘lgan cheksiz kamayuvchi geometrik progressiya yig‘indisi?", fmt(b1 / (1 - q)), f"$S = \\frac{{b_1}}{{1 - q}} = {fmt(b1 / (1 - q))}$", [fmt(b1 / q), fmt(b1 * (1 - q)), str(b1)])
    if tur == "trig":
        a, f, v = rng.choice([(30, "sin", "1/2"), (60, "cos", "1/2"), (45, "tg", "1"), (90, "sin", "1"), (0, "cos", "1"), (60, "sin", "√3/2"), (30, "cos", "√3/2"), (45, "sin", "√2/2")])
        return (f"$\\{f if f != 'tg' else 'tan'}\\,{a}^\\circ$ = ?", v, f"Jadval qiymati: {v}", [x for x in ("1/2", "√3/2", "√2/2", "1", "0") if x != v][:3])
    if tur == "trigtenglama":
        f, v, x = rng.choice([("sin", "1/2", 30), ("cos", "1/2", 60), ("sin", "√2/2", 45), ("tg", "1", 45), ("cos", "√3/2", 30), ("sin", "√3/2", 60)])
        return (f"$\\{'tan' if f == 'tg' else f}\\,x = {v}$, $0^\\circ < x < 90^\\circ$. $x$ = ?", f"{x}°", f"Jadvaldan: $\\{'tan' if f == 'tg' else f}\\,{x}^\\circ = {v}$", [f"{y}°" for y in (30, 45, 60, 90) if y != x][:3])
    if tur == "logtenglama":
        a = rng.choice([2, 3, 5]); n = r(1, 5 if a == 2 else 3)
        return (f"$\\log_{{{a}}} x = {n}$ tenglamani yeching.", a ** n, f"Ta’rif bo‘yicha $x = {a}^{{{n}}} = {a ** n}$", [a * n, n ** a, a + n])
    if tur == "radian":
        g = rng.choice([30, 45, 60, 90, 120, 180, 270, 360])
        j = {30: "π/6", 45: "π/4", 60: "π/3", 90: "π/2", 120: "2π/3", 180: "π", 270: "3π/2", 360: "2π"}[g]
        return (f"${g}^\\circ$ necha radian?", j, f"$180^\\circ = \\pi$, demak ${g}^\\circ = {j}$", [x for x in ("π/6", "π/4", "π/3", "π/2", "π", "2π") if x != j][:3])
    if tur == "logarifm":
        a = rng.choice([2, 3, 5, 10]); n = r(1, 5 if a < 10 else 3)
        return (f"$\\log_{{{a}}} {a ** n} = ?$", n, f"${a}^{{{n}}} = {a ** n}$", [a ** n // a, n + 1, a * n])
    if tur == "korsatkich":
        a = rng.choice([2, 3, 5]); n = r(1, 6 if a == 2 else 4)
        return (f"${a}^x = {a ** n}$ tenglamani yeching.", n, f"${a ** n} = {a}^{{{n}}}$, demak $x = {n}$", [a ** n // a, n + 1, n - 1])
    if tur == "limit":
        a, b, x0 = r(1, 5), r(-5, 5), r(-3, 4)
        return (f"$\\lim_{{x \\to {x0}}} ({a}x^2 {'+' if b >= 0 else '-'} {abs(b)}x) = ?$", a * x0 * x0 + b * x0, f"Ko‘phad uzluksiz — $x = {x0}$ ni qo‘yamiz: ${a * x0 * x0 + b * x0}$", [a * x0 + b, a * x0 * x0, b * x0])
    if tur == "hosila":
        a, n, x0 = r(1, 5), r(2, 4), r(-3, 3)
        return (f"$f(x) = {a}x^{{{n}}}$ bo‘lsa, $f'({x0})$ = ?", a * n * x0 ** (n - 1), f"$f'(x) = {a * n}x^{{{n - 1}}}$; $f'({x0}) = {a * n * x0 ** (n - 1)}$", [a * x0 ** n, a * n * x0 ** n, a * (n - 1) * x0])
    if tur == "urinma":
        a, x0 = r(1, 4), r(-3, 3)
        return (f"$y = {a}x^2$ grafigiga $x_0 = {x0}$ nuqtada o‘tkazilgan urinmaning burchak koeffitsienti?", 2 * a * x0, f"$k = y'(x_0) = {2 * a} \\cdot {x0} = {2 * a * x0}$", [a * x0 * x0, a * x0, 2 * x0])
    if tur == "ekstremum":
        a, b = r(1, 4), r(-8, 8) * 2
        return (f"$f(x) = {a}x^2 {'+' if b >= 0 else '-'} {abs(b)}x$ funksiyaning minimum nuqtasi $x$ = ?", fmt(Fraction(-b, 2 * a)), f"$f'(x) = {2 * a}x {'+' if b >= 0 else '-'} {abs(b)} = 0$, $x = {fmt(Fraction(-b, 2 * a))}$", [fmt(Fraction(b, 2 * a)), "0", fmt(Fraction(-b, a))])
    if tur == "integral":
        n, a, b = r(1, 3), 0, r(1, 3)
        v = Fraction(b ** (n + 1), n + 1)
        return (f"$\\int_0^{{{b}}} x^{{{n}}}\\,dx = ?$", fk(v), f"Boshlang‘ich: $\\frac{{x^{{{n + 1}}}}}{{{n + 1}}}$; Nyuton–Leybnis: $\\frac{{{b}^{{{n + 1}}}}}{{{n + 1}}} - 0 = {fk(v)}$", [fk(Fraction(b ** n, n)), str(b ** (n + 1)), fk(v + 1)])
    if tur == "kombinatorika":
        n, k = r(5, 9), r(2, 4)
        return (f"{n} ta odamdan {k} kishilik guruhni necha xil tanlash mumkin?", math.comb(n, k), f"$C_{{{n}}}^{{{k}}} = \\frac{{{n}!}}{{{k}!({n - k})!}} = {math.comb(n, k)}$", [math.perm(n, k), n * k, math.comb(n, k) + n])
    if tur == "ehtimol":
        oq, qora = r(2, 9), r(2, 9)
        return (f"Qutida {oq} ta oq va {qora} ta qora shar. Tavakkaliga olingan shar oq bo‘lish ehtimoli?", fk(Fraction(oq, oq + qora)), f"$P = \\frac{{{oq}}}{{{oq + qora}}}$", [fk(Fraction(qora, oq + qora)), fk(Fraction(oq, qora)), "1/2"])
    if tur == "statistika":
        xs = sorted(r(1, 20) for _ in range(5))
        return (f"{', '.join(map(str, xs))} sonlarining medianasi?", xs[2], "Tartiblangan qatorning o‘rtadagi soni", [sum(xs) // 5, xs[0], xs[-1]])
    # ── geometriya
    if tur == "qoshni":
        a = r(15, 165)
        return (f"Qo‘shni burchaklardan biri ${a}^\\circ$. Ikkinchisi?", 180 - a, f"Qo‘shni burchaklar yig‘indisi $180^\\circ$: $180 - {a} = {180 - a}$", [a, 90 - a if a < 90 else a - 90, 360 - a])
    if tur == "parallel":
        a = r(20, 160)
        return (f"Ikki parallel to‘g‘ri chiziqni kesuvchi kesadi. Ichki almashinuvchi burchaklardan biri ${a}^\\circ$. Ikkinchisi?", a, "Parallel to‘g‘ri chiziqlarda ichki almashinuvchi burchaklar teng (asos: parallellik aksiomasi va teorema)", [180 - a, 90, 2 * a if 2 * a < 360 else a // 2])
    if tur == "uchburchak":
        a, b = r(20, 100), r(20, 60)
        return (f"Uchburchakning ikki burchagi ${a}^\\circ$ va ${b}^\\circ$. Uchinchisi?", 180 - a - b, f"Burchaklar yig‘indisi $180^\\circ$: ${180 - a - b}$", [360 - a - b, a + b, 90 - b])
    if tur == "tengyonli":
        a = r(20, 140)
        if a % 2:
            a += 1
        return (f"Teng yonli uchburchakning uchidagi burchagi ${a}^\\circ$. Asosidagi burchagi?", (180 - a) // 2, f"Asosdagi burchaklar teng: $(180 - {a}) : 2 = {(180 - a) // 2}$", [180 - a, a, a // 2])
    if tur == "pifagor":
        a, b, c = rng.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15), (7, 24, 25), (12, 16, 20)])
        return (f"To‘g‘ri burchakli uchburchakning katetlari {a} va {b}. Gipotenuzasi?", c, f"$c = \\sqrt{{{a}^2 + {b}^2}} = \\sqrt{{{a * a + b * b}}} = {c}$", [a + b, c + 1, abs(b - a)])
    if tur == "tortburchak":
        a = r(30, 150)
        return (f"Parallelogrammning bir burchagi ${a}^\\circ$. Unga qo‘shni burchagi?", 180 - a, f"Parallelogrammda bir tomonga yopishgan burchaklar yig‘indisi $180^\\circ$: ${180 - a}$", [a, 360 - a, 90])
    if tur == "trapetsiya":
        a, b = r(4, 30), r(4, 30)
        return (f"Trapetsiyaning asoslari {a} va {b}. O‘rta chizig‘i?", fmt(Fraction(a + b, 2)), f"$m = \\frac{{a + b}}{{2}} = {fmt(Fraction(a + b, 2))}$", [a + b, abs(a - b), fmt(Fraction(a * b, 2))])
    if tur == "yuz":
        a, h = r(3, 20), r(3, 20)
        f = rng.choice(["parallelogramm", "uchburchak", "romb"])
        if f == "parallelogramm":
            return (f"Parallelogrammning asosi {a}, balandligi {h}. Yuzi?", a * h, f"$S = a \\cdot h = {a * h}$", [a * h // 2 or 1, 2 * (a + h), a + h])
        if f == "uchburchak":
            return (f"Uchburchakning asosi {a}, balandligi {h}. Yuzi?", fmt(Fraction(a * h, 2)), f"$S = \\frac{{a h}}{{2}} = {fmt(Fraction(a * h, 2))}$", [a * h, a + h, fmt(Fraction(a * h, 4))])
        return (f"Rombning diagonallari {a} va {h}. Yuzi?", fmt(Fraction(a * h, 2)), f"$S = \\frac{{d_1 d_2}}{{2}} = {fmt(Fraction(a * h, 2))}$", [a * h, a + h, 2 * (a + h)])
    if tur == "trapyuz":
        a, b, h = r(3, 20), r(3, 20), r(2, 12)
        return (f"Trapetsiyaning asoslari {a} va {b}, balandligi {h}. Yuzi?", fmt(Fraction((a + b) * h, 2)), f"$S = \\frac{{a + b}}{{2}} \\cdot h = {fmt(Fraction((a + b) * h, 2))}$", [(a + b) * h, fmt(Fraction(a * b, 2)), a + b + h])
    if tur == "oxshash":
        k, s = r(2, 5), r(2, 20)
        return (f"O‘xshash uchburchaklarning o‘xshashlik koeffitsienti {k}. Kichigining yuzi {s}. Kattasining yuzi?", s * k * k, f"Yuzlar nisbati $k^2 = {k * k}$: ${s} \\cdot {k * k} = {s * k * k}$", [s * k, s + k, s * k * k * k])
    if tur == "kosinus":
        a, b, g, c2 = rng.choice([(3, 5, 60, 19), (5, 8, 60, 49), (3, 8, 60, 49), (7, 8, 60, 57), (5, 3, 120, 49), (8, 3, 120, 97)])
        return (f"Uchburchakda ikki tomon {a} va {b}, ular orasidagi burchak ${g}^\\circ$. Uchinchi tomon kvadrati $c^2$ = ?", c2, f"$c^2 = a^2 + b^2 - 2ab\\cos\\gamma = {a * a} + {b * b} - {2 * a * b} \\cdot ({'1/2' if g == 60 else '-1/2'}) = {c2}$", [a * a + b * b, (a + b) ** 2, abs(c2 - a * b)])
    if tur == "sinus":
        a, A, B = rng.choice([(10, 30, 90), (6, 30, 90), (8, 30, 150)])
        b = a * 2 if B in (90, 150) else a
        return (f"Uchburchakda $a = {a}$, $\\angle A = {A}^\\circ$, $\\angle B = {B}^\\circ$. $b$ = ?", b if B == 90 else a, f"Sinuslar teoremasi: $\\frac{{a}}{{\\sin A}} = \\frac{{b}}{{\\sin B}}$", [a // 2, a * 3, a + 1])
    if tur == "aylana":
        rr = r(1, 15)
        return (f"Radiusi {rr} bo‘lgan aylananing uzunligi (π ≈ 3,14)?", fmt(2 * 3.14 * rr), f"$C = 2\\pi r = {fmt(2 * 3.14 * rr)}$", [fmt(3.14 * rr * rr), fmt(3.14 * rr), str(2 * rr)])
    if tur == "sektor":
        rr, g = r(2, 12), rng.choice([30, 45, 60, 90, 120, 180])
        return (f"Radiusi {rr}, markaziy burchagi ${g}^\\circ$ bo‘lgan sektor yuzi (π ≈ 3,14)?", fmt(3.14 * rr * rr * g / 360), f"$S = \\pi r^2 \\cdot \\frac{{{g}}}{{360}} = {fmt(3.14 * rr * rr * g / 360)}$", [fmt(3.14 * rr * rr), fmt(2 * 3.14 * rr * g / 360), str(rr * g)])
    if tur == "muntazam":
        n = r(5, 12)
        return (f"Muntazam {n}-burchakning bitta ichki burchagi?", fmt(Fraction(180 * (n - 2), n)), f"$\\frac{{180^\\circ(n-2)}}{{n}} = {fmt(Fraction(180 * (n - 2), n))}$", [180 * (n - 2), fmt(Fraction(360, n)), "120"])
    if tur == "vektor":
        a, b, c = rng.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 6, 10)])
        return (f"$\\vec a = ({a}; {b})$ vektorning uzunligi?", c, f"$|\\vec a| = \\sqrt{{{a}^2 + {b}^2}} = {c}$", [a + b, c + 1, a * b])
    if tur == "masofa":
        x1, y1 = r(-5, 5), r(-5, 5); dx, dy, d = rng.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 6, 10)])
        return (f"$A({x1}; {y1})$ va $B({x1 + dx}; {y1 + dy})$ nuqtalar orasidagi masofa?", d, f"$AB = \\sqrt{{{dx}^2 + {dy}^2}} = {d}$", [dx + dy, d + 1, dx * dy])
    if tur == "prizma":
        a, b, h = r(2, 10), r(2, 10), r(2, 12)
        return (f"To‘g‘ri prizmaning asosi {a}×{b} to‘g‘ri to‘rtburchak, balandligi {h}. Hajmi?", a * b * h, f"$V = S_{{asos}} \\cdot h = {a * b} \\cdot {h} = {a * b * h}$", [a * b * h // 3 or 1, 2 * (a * b + b * h + a * h), a + b + h])
    if tur == "piramida":
        a, h = r(2, 10), r(2, 12) * 3
        return (f"Asosi tomoni {a} bo‘lgan kvadrat, balandligi {h} bo‘lgan piramida hajmi?", a * a * h // 3, f"$V = \\frac{{1}}{{3}} S h = \\frac{{1}}{{3}} \\cdot {a * a} \\cdot {h} = {a * a * h // 3}$", [a * a * h, a * h, a * a * h // 2])
    if tur == "silindr":
        rr, h = r(1, 8), r(2, 12)
        return (f"Radiusi {rr}, balandligi {h} bo‘lgan silindr hajmi (π ≈ 3,14)?", fmt(3.14 * rr * rr * h), f"$V = \\pi r^2 h = {fmt(3.14 * rr * rr * h)}$", [fmt(3.14 * rr * rr * h / 3), fmt(2 * 3.14 * rr * h), str(rr * rr * h)])
    if tur == "konus":
        rr, h = r(1, 8), r(1, 4) * 3
        return (f"Radiusi {rr}, balandligi {h} bo‘lgan konus hajmi (π ≈ 3,14)?", fmt(3.14 * rr * rr * h / 3), f"$V = \\frac{{1}}{{3}}\\pi r^2 h = {fmt(3.14 * rr * rr * h / 3)}$", [fmt(3.14 * rr * rr * h), fmt(3.14 * rr * h), str(rr * rr * h)])
    if tur == "shar":
        rr = r(1, 9)
        if rng.random() < 0.5:
            return (f"Radiusi {rr} bo‘lgan sfera sirtining yuzi (π ≈ 3,14)?", fmt(4 * 3.14 * rr * rr), f"$S = 4\\pi r^2 = {fmt(4 * 3.14 * rr * rr)}$", [fmt(3.14 * rr * rr), fmt(4 / 3 * 3.14 * rr ** 3), str(4 * rr * rr)])
        return (f"Radiusi {rr} bo‘lgan shar hajmi (π ≈ 3,14)?", fmt(4 / 3 * 3.14 * rr ** 3), f"$V = \\frac{{4}}{{3}}\\pi r^3 = {fmt(4 / 3 * 3.14 * rr ** 3)}$", [fmt(4 * 3.14 * rr * rr), fmt(3.14 * rr ** 3), str(rr ** 3)])
    if tur == "fazovektor":
        a, b, c = rng.choice([(1, 2, 2, 3), (2, 3, 6, 7), (2, 6, 9, 11), (4, 4, 7, 9)])[:3], None, None
        x, y, z = a
        d = int(math.isqrt(x * x + y * y + z * z))
        return (f"$\\vec a = ({x}; {y}; {z})$ vektorning uzunligi?", d, f"$\\sqrt{{{x}^2 + {y}^2 + {z}^2}} = \\sqrt{{{x * x + y * y + z * z}}} = {d}$", [x + y + z, d + 1, x * y * z])
    if tur == "skalyar":
        a = [r(-4, 5) for _ in range(3)]; b = [r(-4, 5) for _ in range(3)]
        return (f"$\\vec a = ({a[0]}; {a[1]}; {a[2]})$, $\\vec b = ({b[0]}; {b[1]}; {b[2]})$. $\\vec a \\cdot \\vec b$ = ?", sum(x * y for x, y in zip(a, b)), f"${a[0]} \\cdot {b[0]} + {a[1]} \\cdot {b[1]} + {a[2]} \\cdot {b[2]} = {sum(x * y for x, y in zip(a, b))}$", [sum(a) + sum(b), sum(x * y for x, y in zip(a, b)) + 1, a[0] * b[0]])
    return gen711("chiziqli", rng)


TUR711 = [
    (("kombinator", "o‘rinlashtir", "guruhlash", "faktorial", "binom"), "N217", "OYIN: joylashtir 3", "kombinatorika"),
    (("ehtimol", "hodisa", "tasodifiy"), "N219", "OYIN: kub 6", "ehtimol"),
    (("statistik", "ma’lumot", "chastota", "mediana", "diagramma"), "N126", "OYIN: galton 8", "statistika"),
    (("integral", "boshlang‘ich funksiya"), "N213", None, "integral"),
    (("urinma", "normal tenglama"), "N209", "OYIN: chiziq", "urinma"),
    (("ekstremum", "o‘sish va kamay", "modellashtir", "grafiklarni yasash", "differensial", "eng katta"), "N210", None, "ekstremum"),
    (("hosila",), "N205", None, "hosila"),
    (("limit", "uzluksiz", "orttirma"), "N202", None, "limit"),
    (("logarifmik tengla", "logarifmik tengsiz"), "N184", None, "logtenglama"),
    (("logarifm",), "N182", None, "logarifm"),
    (("ko‘rsatkichli",), "N181", None, "korsatkich"),
    (("radian", "birlik aylana", "koordinatalar boshi at"), "N185", None, "radian"),
    (("trigonometrik tengla", "trigonometrik tengsiz"), "N189", None, "trigtenglama"),
    (("sinus", "kosinus", "tangens", "kotangens", "trigonometr", "keltirish", "qo‘shish formula", "ikkilangan"), "N161", None, "trig"),
    (("cheksiz kamayuvchi",), "N159", None, "cheksiz"),
    (("geometrik progressiya",), "N157", None, "geomprog"),
    (("arifmetik progressiyaning dast", "yig‘indisi"), "N156", None, "arifyig"),
    (("arifmetik progressiya", "ketma-ketlik"), "N155", None, "arifprog"),
    (("kvadrat tengsizlik", "intervallar"), "N151", "OYIN: nur -3 6 6", "tengsizlik"),
    (("kvadrat funksiya", "y=x", "y=ax", "parabola"), "N150", None, "parabola"),
    (("viyet",), "N135", None, "viyet"),
    (("diskriminant",), "N134", None, "diskriminant"),
    (("kvadrat tenglama", "ikkinchi darajali", "kvadrat tenglamaga"), "N133", "OYIN: tarozi 3 2 11", "kvtenglama"),
    (("ildiz",), "N131", None, "ildiz"),
    (("algebraik kasr", "ratsional ifoda", "ratsional tenglama"), "N128", None, "kasrqisq"),
    (("tengsizlik",), "N129", "OYIN: nur 0 4 10", "tengsizlik"),
    (("sistema",), "N118", "OYIN: chiziq", "sistema"),
    (("funksiya", "dekart", "grafik"), "N117", "OYIN: chiziq", "funksiya"),
    (("tenglama",), "N115", "OYIN: tarozi 3 2 11", "chiziqli"),
    (("kvadratlar ayirma",), "N113", None, "kvayirma"),
    (("ko‘paytuvchilarga", "kublar"), "N114", None, "ajrat"),
    (("yig‘indining kvadrat", "yig‘indining kubi", "qisqa ko‘paytirish"), "N112", None, "qisqa"),
    (("ko‘phad", "birhad", "o‘xshash had"), "N111", None, "kophad"),
    (("daraja",), "N110", None, "daraja"),
    (("ifoda", "formula", "qavs", "arifmetik amal", "tenglik"), "N108", None, "ifoda"),
    # geometriya
    (("shar", "sfera"), "N230", None, "shar"),
    (("konus",), "N228", None, "konus"),
    (("silindr",), "N227", None, "silindr"),
    (("piramida",), "N225", None, "piramida"),
    (("prizma", "ko‘pyoq", "parallelepiped", "3d"), "N224", None, "prizma"),
    (("skalyar",), "N222", None, "skalyar"),
    (("fazoda vektor", "fazoda dekart", "fazoviy koordinata", "fazoda almash"), "N221", None, "fazovektor"),
    (("fazo", "tekislik", "stereometriya", "proyeksiya", "og‘ma", "ikki yoqli"), "N191", None, "masofa"),
    (("vektor",), "N173", None, "vektor"),
    (("koordinata", "o‘rta nuqta", "masofa"), "N174", None, "masofa"),
    (("muntazam ko‘pburchak",), "N172", None, "muntazam"),
    (("sektor", "doira yuzi", "doiraning yuzi"), "N171", "OYIN: nuqta", "sektor"),
    (("aylana uzunligi", "yoy"), "N170", "OYIN: nuqta", "aylana"),
    (("aylana", "vatar", "urinma", "markaziy", "ichki chizilgan"), "N169", "OYIN: nuqta", "aylana"),
    (("kosinuslar teorem", "uchburchaklarni yechish"), "N167", None, "kosinus"),
    (("sinuslar teorem",), "N166", None, "sinus"),
    (("o‘xshash", "gomotetiya", "almashtir", "simmetriya", "burish"), "N164", None, "oxshash"),
    (("pifagor",), "N147", None, "pifagor"),
    (("trapetsiya yuzi", "trapetsiyaning yuzi"), "N146", None, "trapyuz"),
    (("yuz",), "N145", None, "yuz"),
    (("trapetsiya", "fales", "o‘rta chiziq"), "N143", None, "trapetsiya"),
    (("parallelogramm", "romb", "to‘rtburchak", "kvadrat"), "N141", None, "tortburchak"),
    (("teng yonli",), "N123", None, "tengyonli"),
    (("uchburchak",), "N122", None, "uchburchak"),
    (("parallel",), "N121", None, "parallel"),
    (("burchak", "perpendikulyar", "kesma", "geometrik shakl", "sirkul"), "N120", None, "qoshni"),
]


def tanla711(nom, fan, bob):
    n = (nom + " " + bob).lower().replace("ʻ", "‘").replace("'", "‘")
    for k, mid, o, t in TUR711:
        if any(x in n for x in k):
            if fan == "Algebra" and mid in ("N120", "N121", "N122", "N123", "N141", "N143", "N145", "N146", "N147", "N164", "N166", "N167", "N169", "N170", "N171", "N172", "N173", "N174", "N191", "N221", "N222", "N224", "N225", "N227", "N228", "N230"):
                continue
            if fan == "Geometriya" and mid in ("N108", "N110", "N111", "N112", "N113", "N114", "N115", "N117", "N118", "N128", "N129", "N131", "N133", "N134", "N135", "N150", "N151", "N155", "N156", "N157", "N159", "N181", "N182", "N202", "N205", "N209", "N210", "N213"):
                continue
            return mid, o, t
    return ("N115", "OYIN: tarozi 3 2 11", "chiziqli") if fan == "Algebra" else ("N122", None, "uchburchak")


def dars_yasa711(nom, fan, bob, rng):
    mid, oyin, tur = tanla711(nom, fan, bob)
    R = []
    kq, kj = model_savol(mid)
    R.append(("kirish", "", f"🎯 {nom}", f"Bugungi mavzu: {nom}. [1] {M[mid]['misol']}", M[mid]["misol"], "", "", "", "", "", "", f"{kq} => {kj}" if kq and kj else "", "", "", ""))
    R += model_qatorlari(mid, oyin, nom)
    q, j, y, xs = gen711(tur, rng)
    R.append(("misol", "N01", "Namunaviy misol", q, "", "", "", "", f"{y}\nJavob: {fmt(j)}", "", "", "", "", "o‘rta", ""))
    kor, k, u = {q}, 0, 0
    while k < 8 and u < 300:
        u += 1
        q, j, y, xs = gen711(tur, rng)
        if q in kor:
            continue
        kor.add(q); k += 1
        R.append(("masala", f"M{k:02d}", f"Mashq {k}", q, "", "", "", fmt(j), f"{y}\nJavob: {fmt(j)}", "", "", "", "", "oson" if k <= 3 else "o‘rta" if k <= 6 else "qiyin", ""))
    for t in range(6):
        q, j, y, xs = gen711(tur, rng)
        R.append(rows_test(rng, q, fmt(j), [fmt(x) for x in xs], f"T{t + 1:02d}"))
    R.append(("xulosa", "", "🌟 Bugun nimani o‘rgandik", M[mid]["nazariya"], M[mid]["tushuncha"], "", "", "", "", "", "", "", "", "", ""))
    return R


def _katta(nom):
    h = [c for c in nom if c.isalpha()]
    return bool(h) and sum(c.isupper() for c in h) / len(h) > 0.8 and len(nom) > 6


def darslar711(sinf, fan):
    out, sanoq, bob = [], {}, ""
    hammasi = [y for y in D["L"] if y["sinf"] == sinf and y["fan"] == fan]
    katta_kop = sum(_katta(str(y["nom"])) for y in hammasi) > 0.6 * len(hammasi)   # darslik sarlavhalari butunlay katta harfda
    for x in hammasi:
        nom = re.sub(r"\s+", " ", str(x["nom"])).strip()
        if katta_kop:
            nom = nom.lower().capitalize()
        elif re.match(r"^[IVX]+\s*bob\.", nom) or (sum(c.isupper() for c in nom if c.isalpha()) / max(1, sum(c.isalpha() for c in nom)) > 0.8 and len(nom) > 6):
            bob = re.sub(r"^[IVX]+\s*bob\.\s*", "", nom).lower().capitalize()
            if not any(w in nom.upper() for w in ("TAKRORLASH", "TOPSHIRIQ")):
                continue
        if nom.lower().startswith(("abu abdulloh", "tavsiya etilayotgan")):
            continue
        nom = toza(nom)
        for a, b in (("Normal tenglamalari", "Urinma va normal tenglamalari"), ("Va grafiklarni yasash", "Funksiyalarni tekshirish va grafiklarni yasash"),
                     ("Yechishda differensial hisob usullari", "Masalalar yechishda differensial hisob usullari"), ("Integral tushunchalari", "Boshlang‘ich funksiya va integral tushunchalari"),
                     ("Funksiya. funksiyaning", "Funksiya. Funksiyaning"), ("Logarifm tushunchasi. logarifmik", "Logarifm tushunchasi. Logarifmik"), ("Kotangensi", "Burchakning sinusi, kosinusi, tangensi va kotangensi")):
            if nom.startswith(a):
                nom = b + nom[len(a):]
        if nom[:1].islower():
            nom = (bob + ": " if bob else "") + nom
        sanoq[nom] = sanoq.get(nom, 0) + 1
        out.append((nom if sanoq[nom] == 1 else f"{nom} ({sanoq[nom]}-dars)", nom, bob, x))
    return out
