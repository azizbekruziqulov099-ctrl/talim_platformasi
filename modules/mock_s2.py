"""MOCK shablonlari 13–23: trigonometrik, ratsional, logarifmik, irratsional tenglamalar; tengsizliklar; funksiyalar; integral."""
import math
from fractions import Fraction

import sympy as sp

from modules.mock_lib import M, fx, norm, sg, shablon, xa, yopiq

X = sp.symbols("x", real=True)


def _real_roots(expr):
    return sorted(set(r for r in sp.solve(expr, X) if r.is_real), key=lambda r: float(r))


# ───────── 13: trigonometrik tenglama ildizlari soni ─────────
@shablon(13, "sin kx = a")
def s13a(rng):
    k = rng.randint(2, 5)
    a, n = rng.choice([("\\frac12", 2 * k), ("-\\frac12", 2 * k), ("1", k), ("-1", k), ("0", 2 * k + 1)])
    if a == "0":
        yech = [f"$\\sin {k}x=0\\Rightarrow {k}x=\\pi n$, $x=\\frac{{\\pi n}}{{{k}}}$.", f"$0\\le x\\le 2\\pi$ dan $n=0,1,\\dots,{2 * k}$ — jami ${n}$ ta."]
    elif a in ("1", "-1"):
        yech = [f"$t={k}x\\in[0;\\,{2 * k}\\pi]$ — bu ${k}$ ta to‘liq davr.", f"$\\sin t={a}$ tenglama har davrda bitta ildizga ega: jami ${n}$ ta."]
    else:
        yech = [f"$t={k}x\\in[0;\\,{2 * k}\\pi]$ — bu ${k}$ ta to‘liq davr.", f"$\\sin t={a}$ tenglama har davrda ikkita ildizga ega: jami ${n}$ ta."]
    return yopiq(rng, f"$\\sin {k}x={a}$ tenglama $[0;\\,2\\pi]$ oraliqda nechta ildizga ega?", n, yech, noto=[n + 1, n - 1, 2 * n, k])


@shablon(13, "cos kx = 0")
def s13b(rng):
    k = rng.randint(2, 6)
    return yopiq(rng, f"$\\cos {k}x=0$ tenglama $[0;\\,\\pi]$ oraliqda nechta ildizga ega?", k,
                 [f"$\\cos {k}x=0\\Rightarrow {k}x=\\frac{{\\pi}}{{2}}+\\pi n$, $x=\\frac{{\\pi}}{{{2 * k}}}+\\frac{{\\pi n}}{{{k}}}$.", f"$0\\le x\\le\\pi$ shartidan $n=0,1,\\dots,{k - 1}$.", f"Jami ${k}$ ta."],
                 noto=[k + 1, k - 1, 2 * k])


@shablon(13, "tg x = a")
def s13c(rng):
    n = rng.randint(2, 5)
    a = rng.choice([1, -1, 2, 3])
    return yopiq(rng, f"$\\operatorname{{tg}}x={a}$ tenglama $[0;\\,{n}\\pi]$ oraliqda nechta ildizga ega?", n,
                 ["Tangens davri $\\pi$; har bir davrda $\\operatorname{tg}x=a$ tenglama bitta ildizga ega.", f"Oraliqda ${n}$ ta davr bor, shu sababli ${n}$ ta ildiz."], noto=[n + 1, n - 1, 2 * n])


# ───────── 14: haqiqiy ildizlar yig'indisi ─────────
@shablon(14, "modulli")
def s14a(rng):
    a, b = rng.randint(-6, 8), rng.randint(2, 8)
    return yopiq(rng, f"$|{xa(a)}|={b}$ tenglamaning ildizlari yig‘indisini toping.", 2 * a,
                 [f"${xa(a)}={b}$ yoki ${xa(a)}=-{b}$.", f"$x_1={a + b}$, $x_2={a - b}$.", f"Yig‘indi: ${2 * a}$."], noto=[a, 2 * b, a + b])


@shablon(14, "ikkita kvadrat uchhad")
def s14b(rng):
    while True:
        p1, q1 = rng.randint(-8, 8), rng.randint(-8, 8)
        p2, q2 = rng.randint(-8, 8), rng.randint(-8, 8)
        D1, D2 = p1 * p1 - 4 * q1, p2 * p2 - 4 * q2
        if (D1 > 0) != (D2 > 0) and (D1 > 0 or D2 > 0) and (p1, q1) != (p2, q2):
            break
    real = -p1 if D1 > 0 else -p2
    return yopiq(rng, f"$(x^2{sg(p1)}x{sg(q1)})(x^2{sg(p2)}x{sg(q2)})=0$ tenglamaning haqiqiy ildizlari yig‘indisini toping.", real,
                 [f"Birinchi ko‘paytuvchi: $D_1={p1}^2-4\\cdot({q1})={D1}$; ikkinchisi: $D_2={D2}$.", f"Faqat $D>0$ bo‘lgan ko‘paytuvchining ildizlari haqiqiy; Viyet teoremasiga ko‘ra yig‘indi ${real}$."], noto=[-real, p1 + p2, -(p1 + p2)])


@shablon(14, "ildizlar yig'indisi")
def s14c(rng):
    while True:
        a, b = rng.randint(-6, 6), rng.randint(-6, 6)
        if a != b:
            break
    return yopiq(rng, f"$x^2{sg(-(a + b))}x{sg(a * b)}=0$ tenglama ildizlari kvadratlarining yig‘indisini toping.", a * a + b * b,
                 [f"Viyet: $x_1+x_2={a + b}$, $x_1x_2={a * b}$.", f"$x_1^2+x_2^2=(x_1+x_2)^2-2x_1x_2={(a + b) ** 2}-({2 * a * b})={a * a + b * b}$."], noto=[(a + b) ** 2, a * a + b * b + 2])


@shablon(15, "kasrli tenglama")
def s15a(rng):
    a, b = rng.randint(1, 6), rng.randint(1, 6)
    c = rng.randint(1, 5)
    # (x²−a²)/(x−a) = x+b  → x+a = x+b → a=b? ... umumiy: (x²−a²)/(x−a)=k  → x=k−a, x≠a
    k = rng.choice([2 * a, rng.randint(1, 12)])
    sol = k - a
    cnt = 0 if sol == a else 1
    return yopiq(rng, f"$\\dfrac{{x^2-{a * a}}}{{x-{a}}}={k}$ tenglama nechta haqiqiy ildizga ega?", cnt,
                 [f"$x\\neq {a}$. Suratni ajratamiz: $\\frac{{(x-{a})(x+{a})}}{{x-{a}}}=x+{a}$.", f"$x+{a}={k}\\Rightarrow x={sol}$.", ("$x=" + str(sol) + "$ — chetlatilgan qiymat ($x\\neq " + str(a) + "$), shuning uchun ildiz yo‘q.") if cnt == 0 else f"$x={sol}\\neq {a}$ — mos keladi, ildiz bitta."],
                 noto=[0, 1, 2, 3])


@shablon(15, "ikki kasr")
def s15b(rng):
    while True:
        a, b = rng.randint(-5, 5), rng.randint(-5, 5)
        if a != b:
            break
    c, d = rng.randint(1, 4), rng.randint(1, 4)
    num = sp.together(c / (X - a) - d / (X - b)).as_numer_denom()[0]
    sols = [s for s in _real_roots(num) if s != a and s != b]
    return yopiq(rng, f"$\\dfrac{{{c}}}{{{xa(a)}}}=\\dfrac{{{d}}}{{{xa(b)}}}$ tenglama nechta haqiqiy ildizga ega?", len(sols),
                 [f"Aniqlanish sohasi: $x\\neq {a}$, $x\\neq {b}$.", f"Proporsiya: ${c}({xa(b)})={d}({xa(a)})$ — chiziqli tenglama.", "Yechim: " + (f"$x={sp.latex(sols[0])}$ aniqlanish sohasiga kiradi." if sols else "mos keladigan yechim yo‘q.")],
                 noto=[0, 1, 2, 3])


# ───────── 16: tengsizlikning butun yechimlari yig'indisi ─────────
@shablon(16, "kvadrat tengsizlik")
def s16a(rng):
    while True:
        a, b = sorted(rng.sample(range(-9, 10), 2))
        if b - a >= 3:
            break
    strict = rng.random() < .5
    sol = [n for n in range(a, b + 1) if ((a < n < b) if strict else True)]
    return yopiq(rng, f"$({xa(a)})({xa(b)}){'<' if strict else chr(92) + 'le'}0$ tengsizlikning butun yechimlari yig‘indisini toping.", sum(sol),
                 [f"Parabola shoxlari yuqoriga, yechim: ${'(' if strict else '['}{a};\\,{b}{')' if strict else ']'}$.", f"Butun yechimlar: {', '.join(map(str, sol))}.", f"Yig‘indi: ${sum(sol)}$."], noto=[sum(sol) + b, sum(sol) - a])


@shablon(16, "modulli tengsizlik")
def s16b(rng):
    a, b = rng.randint(-5, 6), rng.randint(2, 7)
    sol = list(range(a - b + 1, a + b))
    return yopiq(rng, f"$|{xa(a)}|<{b}$ tengsizlikning butun yechimlari yig‘indisini toping.", sum(sol),
                 [f"$-{b}<{xa(a)}<{b}$, ya’ni ${a - b}<x<{a + b}$.", f"Butun yechimlar: {a - b + 1}, …, {a + b - 1}.", f"Yig‘indi: ${sum(sol)}$."], noto=[sum(sol) + b, sum(sol) - b])


@shablon(16, "kasr tengsizlik")
def s16c(rng):
    while True:
        a, b = sorted(rng.sample(range(-8, 9), 2))
        if b - a >= 3:
            break
    sol = list(range(a, b))      # (x−a)/(x−b) ≤ 0 → a ≤ x < b
    return yopiq(rng, f"$\\dfrac{{{xa(a)}}}{{{xa(b)}}}\\le0$ tengsizlikning butun yechimlari yig‘indisini toping.", sum(sol),
                 [f"Nollar: $x={a}$ (suratda), $x={b}$ (maxrajda).", f"Intervallar usuli: yechim $[{a};\\,{b})$ — maxrajni nolga aylantiradigan $x={b}$ kirmaydi.", f"Butun yechimlar: {a}, …, {b - 1}; yig‘indi ${sum(sol)}$."], noto=[sum(sol) + b, sum(sol) - a])


@shablon(17, "log yig'indisi")
def s17a(rng):
    while True:
        p, q = rng.randint(-3, 3), rng.randint(-3, 3)
        root = rng.randint(max(p, q) + 2, 14)
        prod = (root - p) * (root - q)
        if prod & (prod - 1) == 0:
            break
    cn = int(math.log2(prod))
    allr = _real_roots((X - p) * (X - q) - prod)
    sols = [s for s in allr if s > max(p, q)]
    return yopiq(rng, f"$\\log_2({xa(p)})+\\log_2({xa(q)})={cn}$ tenglama nechta haqiqiy ildizga ega?", len(sols),
                 [f"Aniqlanish sohasi: $x>{max(p, q)}$.", f"Logarifmlar yig‘indisi: $({xa(p)})({xa(q)})=2^{{{cn}}}={prod}$.", "Kvadrat tenglama ildizlari: " + ", ".join(sp.latex(s) for s in allr) + f". Aniqlanish sohasiga mosi: {len(sols)} ta."],
                 noto=[0, 1, 2, 3])


@shablon(17, "log tenglama")
def s17b(rng):
    k = rng.randint(2, 4)
    a = rng.randint(2, 6)
    # log_2(x²−a) = k → x² = 2^k + a ; ildizlar soni: 2 (2^k+a>0)
    t = 2 ** k + a
    n = 2 if t > 0 else 0
    return yopiq(rng, f"$\\log_2(x^2-{a})={k}$ tenglama nechta haqiqiy ildizga ega?", n,
                 [f"$x^2-{a}=2^{{{k}}}={2 ** k}$, ya’ni $x^2={t}$.", f"Logarifm ostidagi ifoda musbat: ${2 ** k}>0$ — shart bajariladi. $x=\\pm\\sqrt{{{t}}}$ — ikkita ildiz."], noto=[0, 1, 2, 3, 4])


# ───────── 18: irratsional tenglama ─────────
@shablon(18, "ildizlar yig'indisi = ildiz")
def s18a(rng):
    while True:
        a, b = rng.randint(1, 9), rng.randint(1, 9)
        c = rng.randint(2, 6)
        sols = [s for s in _real_roots(sp.sqrt(X + a) + sp.sqrt(X - b) - c) if s >= max(-a, b)]
        sols2 = []
        for s in sols:
            if abs(float(sp.sqrt(s + a) + sp.sqrt(s - b)) - c) < 1e-9:
                sols2.append(s)
        break
    return yopiq(rng, f"$\\sqrt{{x+{a}}}+\\sqrt{{x-{b}}}={c}$ tenglama nechta haqiqiy ildizga ega?", len(sols2),
                 [f"Aniqlanish sohasi: $x\\ge {max(-a, b)}$.", "Ildizlarni yolg‘izlab, kvadratga ko‘taramiz va topilgan qiymatni tekshiramiz.",
                  (f"Topilgan ildiz: $x={sp.latex(sols2[0])}$ — tekshirish: tenglik bajariladi." if sols2 else "Topilgan qiymatlar tenglamani qanoatlantirmaydi — ildiz yo‘q.")], noto=[0, 1, 2])


@shablon(18, "ildiz = chiziqli")
def s18b(rng):
    a, b = rng.randint(1, 8), rng.randint(0, 6)
    sols = [s for s in _real_roots((X - b) ** 2 - (X + a)) if s >= b and s >= -a]
    tot = norm(sum(sols)) if sols else Fraction(0)
    return yopiq(rng, f"$\\sqrt{{x+{a}}}=x-{b}$ tenglama ildizlari yig‘indisini toping (ildiz bo‘lmasa 0).", tot,
                 [f"Ikkala tomonni kvadratga ko‘taramiz: $x+{a}=(x-{b})^2$.", f"Kvadrat tenglama ildizlaridan $x-{b}\\ge0$ shartni qanoatlantirganlari olinadi.", "Mos ildizlar: " + (", ".join("$" + sp.latex(s) + "$" for s in sols) if sols else "yo‘q") + "."],
                 noto=[1, 2, 3, 5, 7])


# ───────── 19: tengsizlikni qanoatlantirmaydigan sonlar ─────────
@shablon(19, "kvadrat musbat")
def s19a(rng):
    while True:
        a, b = sorted(rng.sample(range(1, 14), 2))
        if b - a >= 3:
            break
    bad = [n for n in range(1, 40) if not (n - a) * (n - b) > 0]
    return yopiq(rng, f"$(x-{a})(x-{b})>0$ tengsizlikni qanoatlantirmaydigan natural sonlar nechta?", len(bad),
                 [f"Yechim: $x<{a}$ yoki $x>{b}$.", f"Qanoatlantirmaydigan natural sonlar: ${a}\\le x\\le {b}$.", f"Ularning soni: ${b}-{a}+1={len(bad)}$."], noto=[b - a, b - a + 2, a + b])


@shablon(19, "modul tengsizlik")
def s19b(rng):
    a, b = rng.randint(3, 10), rng.randint(2, 6)
    bad = [n for n in range(-60, 61) if not (abs(n - a) >= b)]
    return yopiq(rng, f"$|x-{a}|\\ge {b}$ tengsizlikni qanoatlantirmaydigan butun sonlar nechta?", len(bad),
                 [f"Yechim: $x\\le {a - b}$ yoki $x\\ge {a + b}$.", f"Qanoatlantirmaydi: ${a - b}<x<{a + b}$.", f"Butun sonlar: ${a - b + 1}, \\dots, {a + b - 1}$ — jami ${len(bad)}$ ta."], noto=[2 * b, 2 * b - 2, 2 * b + 1])


@shablon(19, "kasr tengsizlik")
def s19c(rng):
    while True:
        a, b = sorted(rng.sample(range(-6, 9), 2))
        if b - a >= 4:
            break
    cnt = b - a - 1
    return yopiq(rng, f"$\\dfrac{{{xa(a)}}}{{{xa(b)}}}<0$ tengsizlikning butun yechimlari nechta?", cnt,
                 [f"Nollar: $x={a}$ va $x={b}$. Intervallar usuli: kasr manfiy bo‘ladi ${a}<x<{b}$ da.", f"Chegaralar kirmaydi. Butun sonlar: {a + 1}, …, {b - 1}.", f"Soni: ${b}-{a}-1={cnt}$."], noto=[b - a, b - a + 1, b - a - 2])


# ───────── 20: funksiya qiymati ─────────
@shablon(20, "murakkab argument")
def s20a(rng):
    a, b = rng.randint(1, 5), rng.randint(-4, 4)
    p, q = rng.randint(1, 4), rng.randint(-5, 5)
    t = rng.randint(-3, 7)
    x0 = Fraction(t - b, a)
    if x0.denominator != 1:
        return s20a(rng)
    f = lambda xx: p * xx * xx + q * xx
    return yopiq(rng, f"$f({a}x{'+' if b >= 0 else ''}{b})={p}x^2{'+' if q >= 0 else ''}{q}x$ bo‘lsa, $f({t})$ ni toping.", f(int(x0)),
                 [f"${a}x{'+' if b >= 0 else ''}{b}={t}$ dan $x={int(x0)}$.", f"$f({t})={p}\\cdot({int(x0)})^2{'+' if q >= 0 else ''}{q}\\cdot({int(x0)})={f(int(x0))}$."], noto=[f(int(x0)) + p, -f(int(x0))])


@shablon(20, "teskari funksiya")
def s20b(rng):
    a, b = rng.randint(2, 5), rng.randint(-5, 6)
    t = rng.randint(-5, 9)
    # f(x)=ax+b ; f^{-1}(t) = (t−b)/a
    v = Fraction(t - b, a)
    return yopiq(rng, f"$f(x)={a}x{'+' if b >= 0 else ''}{b}$ bo‘lsa, $f^{{-1}}({t})$ ni toping.", v, [f"$f^{{-1}}({t})=y$ bo‘lsa, $f(y)={t}$.", f"${a}y{'+' if b >= 0 else ''}{b}={t}$, $y={fx(v)}$."], noto=[a * t + b])


@shablon(20, "funksiyalar kompozitsiyasi")
def s20c(rng):
    a, b, c, d = rng.randint(1, 4), rng.randint(-3, 3), rng.randint(1, 4), rng.randint(-3, 3)
    t = rng.randint(-3, 4)
    inner = c * t + d
    v = a * inner + b
    return yopiq(rng, f"$f(x)={a}x{'+' if b >= 0 else ''}{b}$, $g(x)={c}x{'+' if d >= 0 else ''}{d}$ bo‘lsa, $f(g({t}))$ ni toping.", v,
                 [f"$g({t})={c}\\cdot({t}){'+' if d >= 0 else ''}{d}={inner}$.", f"$f({inner})={a}\\cdot({inner}){'+' if b >= 0 else ''}{b}={v}$."], noto=[c * (a * t + b) + d])


# ───────── 21: grafik bo'yicha tenglama ildizlari soni ─────────
@shablon(21, "f(|x|)=k")
def s21a(rng):
    while True:
        p, q = rng.randint(-4, 4), rng.randint(-6, 2)
        k = rng.randint(-8, 8)
        # f(t)=t²+pt+q ; f(|x|) = k → t≥0 yechimlar
        ts = [s for s in _real_roots(X * X + p * X + q - k) if s >= 0]
        cnt = sum(1 if s == 0 else 2 for s in ts)
        break
    return yopiq(rng, f"$y=f(x)=x^2{'+' if p >= 0 else ''}{p}x{'+' if q >= 0 else ''}{q}$ parabola berilgan. $f(|x|)={k}$ tenglama nechta ildizga ega?".replace("+-", "-"), cnt,
                 [f"$t=|x|\\ge0$ desak, $f(t)={k}$, ya’ni $t^2{'+' if p >= 0 else ''}{p}t{'+' if q - k >= 0 else ''}{q - k}=0$.", "Faqat $t\\ge 0$ ildizlar olinadi: $t>0$ ildiz ikkita $x=\\pm t$ beradi, $t=0$ esa bitta $x=0$.", f"Jami ${cnt}$ ta ildiz."], noto=[0, 1, 2, 3, 4])


@shablon(21, "chiziqli grafik")
def s21b(rng):
    k, b = rng.choice([-3, -2, -1, 1, 2, 3]), rng.randint(-5, 5)
    y0 = rng.randint(-6, 6)
    # y=kx+b ; |y| = y0 nechta ildiz? (y0>0:2, y0=0:1, y0<0:0)
    cnt = 2 if y0 > 0 else 1 if y0 == 0 else 0
    return yopiq(rng, f"$y={k}x{'+' if b >= 0 else ''}{b}$ to‘g‘ri chiziq berilgan. $|{k}x{'+' if b >= 0 else ''}{b}|={y0}$ tenglama nechta ildizga ega?", cnt,
                 ["Modul tenglamasi $|f(x)|=a$: $a>0$ da ikkita, $a=0$ da bitta, $a<0$ da ildiz yo‘q.", f"Bu yerda $a={y0}$, $f(x)$ chiziqli — har bir qiymat bir marta qabul qilinadi: ${cnt}$ ta ildiz."], noto=[0, 1, 2, 3])


# ───────── 22: parabola va to'g'ri chiziq ─────────
@shablon(22, "kesishish nuqtalari")
def s22a(rng):
    while True:
        r1, r2 = sorted(rng.sample(range(-6, 7), 2))
        a = rng.randint(10, 30)
        m = -(r1 + r2)
        n = r1 * r2 + a
        if r2 - r1 >= 2:
            break
    # y = a − x²;  y = m x + n  →  x² + m x + (n − a) = 0 → roots r1,r2 (m=−(r1+r2), n−a = r1 r2)
    return yopiq(rng, f"$y={a}-x^2$ parabola va $y={m}x{'+' if n >= 0 else ''}{n}$ to‘g‘ri chiziq $K$ va $L$ nuqtalarda kesishadi. Nuqtalar abssissalari ayirmasini (kattasidan kichigini) toping.", r2 - r1,
                 [f"${a}-x^2={m}x{'+' if n >= 0 else ''}{n}$ dan $x^2{'+' if m >= 0 else ''}{m}x{'+' if n - a >= 0 else ''}{n - a}=0$.", f"Ildizlar: $x_1={r1}$, $x_2={r2}$.", f"Ayirma: ${r2}-({r1})={r2 - r1}$."], noto=[r1 + r2, abs(r1) + abs(r2) + 1, r2 - r1 + 1])


@shablon(22, "parabola uchi")
def s22b(rng):
    a, p, q = rng.choice([1, 2, -1, -2, 3]), rng.randint(-4, 4), rng.randint(-6, 6)
    # y = a(x+p)²+q → uchi (−p; q)
    return yopiq(rng, f"$y={a}(x{sg(p)})^2{sg(q)}$ parabola uchining koordinatalari yig‘indisini toping.", -p + q,
                 [f"Parabola $y=a(x-x_0)^2+y_0$ ko‘rinishida, uchi $(x_0;y_0)$.", f"$x_0=-({p})={-p}$, $y_0={q}$.", f"Yig‘indi: ${-p + q}$."], noto=[p + q, -p - q, q])


# ───────── 23: aniq integral ─────────
@shablon(23, "ko'phad integrali")
def s23a(rng):
    a, b, c = rng.randint(1, 6), rng.randint(-5, 5), rng.randint(-4, 4)
    lo, hi = rng.randint(0, 2), rng.randint(3, 5)
    F = lambda x: Fraction(a * x ** 3, 3) + Fraction(b * x ** 2, 2) + c * x
    v = F(hi) - F(lo)
    return yopiq(rng, f"Hisoblang: $\\displaystyle\\int_{{{lo}}}^{{{hi}}}\\left({a}x^2{'+' if b >= 0 else ''}{b}x{'+' if c >= 0 else ''}{c}\\right)dx$.", v,
                 [f"Boshlang‘ich funksiya: $F(x)=\\frac{{{a}x^3}}{{3}}{'+' if b >= 0 else ''}\\frac{{{b}x^2}}{{2}}{'+' if c >= 0 else ''}{c}x$.", f"$F({hi})={fx(F(hi))}$, $F({lo})={fx(F(lo))}$.", f"Ayirma: ${fx(v)}$."])


@shablon(23, "almashtirish")
def s23b(rng):
    a = rng.choice([3, 4, 5, 6, 8]); m = {3: 4, 4: 3, 5: 12, 6: 8, 8: 6}[a]
    # ∫_0^m x/√(x²+a²) dx = √(m²+a²) − a   (m²+a² kvadrat)
    c = int(math.isqrt(m * m + a * a))
    if c * c != m * m + a * a:
        return s23b(rng)
    return yopiq(rng, f"Hisoblang: $\\displaystyle\\int_0^{{{m}}}\\dfrac{{x\\,dx}}{{\\sqrt{{x^2+{a * a}}}}}$.", c - a,
                 [f"$u=x^2+{a * a}$ desak, $x\\,dx=\\frac{{du}}{{2}}$.", f"Integral $\\sqrt{{u}}$ ga teng: $\\sqrt{{x^2+{a * a}}}\\Big|_0^{{{m}}}$.", f"$\\sqrt{{{m * m + a * a}}}-\\sqrt{{{a * a}}}={c}-{a}={c - a}$."], noto=[c + a, c, a])


@shablon(23, "yuz")
def s23c(rng):
    a, b = rng.randint(2, 5), rng.randint(1, 3)
    # y = x² dan y = a x gacha bo'lgan yuz (0..a)
    return yopiq(rng, f"$y=x^2$ parabola va $y={a}x$ to‘g‘ri chiziq bilan chegaralangan shaklning yuzini toping.", Fraction(a ** 3, 6),
                 [f"Kesishish: $x^2={a}x$, $x=0$ va $x={a}$.", f"$S=\\int_0^{{{a}}}({a}x-x^2)dx=\\left(\\frac{{{a}x^2}}{{2}}-\\frac{{x^3}}{{3}}\\right)\\Big|_0^{{{a}}}$.", f"$=\\frac{{{a ** 3}}}{{2}}-\\frac{{{a ** 3}}}{{3}}={fx(Fraction(a ** 3, 6))}$."])
