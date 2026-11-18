"""MOCK shablonlari 36–45: ochiq javobli topshiriqlar (a va b qismlar)."""
import math
from fractions import Fraction

from modules.mock_lib import fx, ochiq, shablon, xa


@shablon(36, "parametrli sistema")
def s36(rng):
    x, y = rng.randint(-5, 6), rng.randint(-5, 6)
    a1, b1, a2, b2 = rng.randint(1, 4), rng.randint(1, 4), rng.randint(1, 4), rng.randint(-4, -1)
    if a1 * b2 - a2 * b1 == 0:
        return s36(rng)
    c1, c2 = a1 * x + b1 * y, a2 * x + b2 * y
    k = rng.randint(2, 5)
    # b) a1 x + b1 y = c1 ; k a1 x + k b1 y = m  → yechimsiz bo'lishi uchun m ≠ k c1; "m" nechada cheksiz ko'p yechim: m = k c1
    return ochiq(f"$\\begin{{cases}}{a1}x+{b1}y={c1}\\\\ {a2}x{'+' if b2 > 0 else '-'}{abs(b2)}y={c2}\\end{{cases}}$ sistema berilgan.",
                 [("a) $x+y$ ni toping.", x + y), (f"b) $\\begin{{cases}}{a1}x+{b1}y={c1}\\\\ {k * a1}x+{k * b1}y=m\\end{{cases}}$ sistema cheksiz ko‘p yechimga ega bo‘ladigan $m$ ni toping.", k * c1)],
                 [f"a) Sistemani yechamiz: $x={x}$, $y={y}$ (qo‘shish yoki o‘rniga qo‘yish usuli), $x+y={x + y}$.", f"b) Cheksiz ko‘p yechim uchun tenglamalar proporsional bo‘lishi shart: $m={k}\\cdot {c1}={k * c1}$."])


@shablon(37, "trigonometrik tenglama")
def s37(rng):
    k = rng.choice([2, 3, 4, 5, 6, 8, 9, 10, 12])
    val, ang = rng.choice([("\\frac{1}{2}", 30), ("\\frac{\\sqrt3}{2}", 60), ("1", 90)])
    # sin(kx)=val  → eng kichik musbat ildiz x = ang/k (daraja)
    # b) [0,360] oraliqdagi ildizlar soni
    roots = set()
    for n in range(0, 2 * k + 2):
        for base in ([ang, 180 - ang] if ang != 90 else [90]):
            x = Fraction(base + 360 * n, k)
            if 0 <= x <= 360:
                roots.add(x)
    return ochiq(f"$\\sin {k}x={val}$ tenglama berilgan.",
                 [("a) Eng kichik musbat ildizi necha gradus?", Fraction(ang, k)), ("b) $[0^\\circ;\\,360^\\circ]$ kesmadagi ildizlari nechta?", len(roots))],
                 [f"a) $\\sin t={val}$ ning eng kichik musbat yechimi $t={ang}^\\circ$, $t={k}x$ dan $x=\\frac{{{ang}}}{{{k}}}={fx(Fraction(ang, k))}^\\circ$.",
                  f"b) $t={k}x\\in[0^\\circ;{360 * k}^\\circ]$ oraliqda $\\sin t={val}$ ning yechimlari soni sanaladi — jami ${len(roots)}$ ta."])


@shablon(38, "funksional tenglama")
def s38(rng):
    a, b = rng.randint(2, 4), rng.randint(-5, 5)
    c, d = rng.randint(1, 4), rng.randint(-6, 6)
    # f(a x + b) = c x + d  → f(t) = c (t-b)/a + d
    def f(t): return Fraction(c) * (t - b) / a + d
    t1 = rng.randint(-4, 8)
    t2 = f(rng.randint(-4, 8))
    sol = a * (t2 - d) / c + b
    return ochiq(f"$f({a}x{xa(b) if b else ''})={c}x{'+' if d >= 0 else '-'}{abs(d)}$ tenglik barcha $x$ uchun o‘rinli.".replace(f"{a}x{xa(b)}", f"{a}x{'+' if b > 0 else '-'}{abs(b)}") if b else f"$f({a}x)={c}x{'+' if d >= 0 else '-'}{abs(d)}$ tenglik barcha $x$ uchun o‘rinli.",
                 [(f"a) $f({t1})$ ni toping.", f(t1)), (f"b) $f(t)={fx(t2)}$ tenglamani yeching ($t$ ni toping).", sol)],
                 [f"$t={a}x{'+' if b >= 0 else '-'}{abs(b)}$ almashtirish: $x=\\frac{{t{'-' if b >= 0 else '+'}{abs(b)}}}{{{a}}}$.", f"$f(t)={c}\\cdot\\frac{{t{'-' if b >= 0 else '+'}{abs(b)}}}{{{a}}}{'+' if d >= 0 else '-'}{abs(d)}$.", f"a) $f({t1})={fx(f(t1))}$.", f"b) $f(t)={fx(t2)}$ dan $t={fx(sol)}$."]) if True else None


@shablon(39, "murakkab funksiya")
def s39(rng):
    a, b, c, d = rng.randint(1, 4), rng.randint(-4, 4), rng.randint(1, 4), rng.randint(-4, 4)
    x0 = rng.randint(-3, 4)
    f = lambda t: a * t * t + b
    g = lambda t: c * t + d
    return ochiq(f"$f(x)={a}x^2{'+' if b >= 0 else '-'}{abs(b)}$, $g(x)={c}x{'+' if d >= 0 else '-'}{abs(d)}$.",
                 [(f"a) $f(g({x0}))$ ni toping.", f(g(x0))), (f"b) $g(f({x0}))$ ni toping.", g(f(x0)))],
                 [f"a) $g({x0})={g(x0)}$, $f({g(x0)})={f(g(x0))}$.", f"b) $f({x0})={f(x0)}$, $g({f(x0)})={g(f(x0))}$."])


@shablon(40, "urinma va hosila")
def s40(rng):
    a, b, c = rng.randint(1, 3), rng.randint(-4, 4), rng.randint(-5, 5)
    x0 = rng.randint(-2, 3)
    y = lambda t: a * t ** 3 + b * t * t + c * t
    dy = lambda t: 3 * a * t * t + 2 * b * t + c
    k, y0 = dy(x0), y(x0)
    n = y0 - k * x0
    return ochiq(f"$y={a}x^3{'+' if b >= 0 else '-'}{abs(b)}x^2{'+' if c >= 0 else '-'}{abs(c)}x$ funksiya grafigi berilgan.",
                 [(f"a) $x_0={x0}$ nuqtada $y'(x_0)$ ni toping.", k), (f"b) Shu nuqtadagi urinmaning $Oy$ o‘qini kesish ordinatasini (urinma $y=kx+n$ dagi $n$) toping.", n)],
                 [f"a) $y'={3 * a}x^2{'+' if 2 * b >= 0 else '-'}{abs(2 * b)}x{'+' if c >= 0 else '-'}{abs(c)}$, $y'({x0})={k}$.", f"b) $y({x0})={y0}$. Urinma: $y-{y0}={k}(x-{x0})$, $n={y0}-{k}\\cdot {x0}={n}$."]).replace if False else ochiq(
        f"$y={a}x^3{'+' if b >= 0 else '-'}{abs(b)}x^2{'+' if c >= 0 else '-'}{abs(c)}x$ funksiya grafigi berilgan.",
        [(f"a) $x_0={x0}$ nuqtada $y'(x_0)$ ni toping.", k), (f"b) Shu nuqtadagi urinmaning $Oy$ o‘qini kesish ordinatasini (urinma $y=kx+n$ dagi $n$) toping.", n)],
        [f"a) $y'={3 * a}x^2{'+' if 2 * b >= 0 else '-'}{abs(2 * b)}x{'+' if c >= 0 else '-'}{abs(c)}$, $y'({x0})={k}$.", f"b) $y({x0})={y0}$. Urinma: $y-({y0})={k}(x-({x0}))$, $n={y0}-({k})\\cdot({x0})={n}$."])


@shablon(41, "aylanaga ichki chizilgan to'rtburchak")
def s41(rng):
    c, juft = rng.choice([(25, [(7, 24), (15, 20)]), (50, [(14, 48), (30, 40)]), (65, [(16, 63), (33, 56), (25, 60), (39, 52)]), (85, [(13, 84), (36, 77), (40, 75), (51, 68)]), (75, [(21, 72), (45, 60)])])
    (a, b), (p, q) = rng.sample(juft, 2)
    if rng.random() < .5:
        a, b = b, a
    if rng.random() < .5:
        p, q = q, p
    return ochiq(f"$ABCD$ to‘rtburchak aylanaga ichki chizilgan, $AC$ — diametr, $AC={c}$, $AB={a}$, $AD={p}$.",
                 [("a) $BC$ ni toping.", b), (f"b) $ABCD$ to‘rtburchakning yuzini toping ($CD$ ni ham hisoblang).", Fraction(a * b + p * q, 2))],
                 [f"$AC$ diametr, shuning uchun $\\angle B=\\angle D=90^\\circ$.", f"a) $BC=\\sqrt{{{c}^2-{a}^2}}={b}$.", f"b) $CD=\\sqrt{{{c}^2-{p}^2}}={q}$. $S=\\frac{{{a}\\cdot {b}}}{{2}}+\\frac{{{p}\\cdot {q}}}{{2}}={fx(Fraction(a * b + p * q, 2))}$."])


_UCH = [(a, b, c) for a in range(5, 31) for b in range(a, 31) for c in range(b, 31) if a + b > c
        and math.isqrt((a + b + c) * (-a + b + c) * (a - b + c) * (a + b - c)) ** 2 == (a + b + c) * (-a + b + c) * (a - b + c) * (a + b - c)
        and (math.isqrt((a + b + c) * (-a + b + c) * (a - b + c) * (a + b - c)) // 4) * 4 == math.isqrt((a + b + c) * (-a + b + c) * (a - b + c) * (a + b - c))]


@shablon(42, "uchburchak yuzi va ichki chizilgan aylana")
def s42(rng):
    a, b, c = rng.choice(_UCH)
    p2 = a + b + c
    S = math.isqrt(p2 * (-a + b + c) * (a - b + c) * (a + b - c)) // 4
    pp = Fraction(p2, 2)
    return ochiq(f"Uchburchakning tomonlari {a}, {b} va {c}.",
                 [("a) Uchburchak yuzini toping.", S), ("b) Unga ichki chizilgan aylana radiusini toping.", Fraction(S) / pp)],
                 [f"a) Geron formulasi: $p={fx(pp)}$, $S=\\sqrt{{{fx(pp)}({fx(pp - a)})({fx(pp - b)})({fx(pp - c)})}}={S}$.", f"b) $r=\\frac{{S}}{{p}}=\\frac{{{S}}}{{{fx(pp)}}}={fx(Fraction(S) / pp)}$."])


@shablon(43, "muntazam o'n ikki burchak")
def s43(rng):
    R = rng.randint(2, 40)
    b = rng.choice([("b) Diagonallari nechta?", 54, "$\\\\frac{12\\\\cdot 9}{2}=54$."), ("b) Bitta ichki burchagi necha gradus?", 150, "$\\\\frac{180(12-2)}{12}=150$."),
                    ("b) Ichki burchaklari yig‘indisi necha gradus?", 1800, "$180(12-2)=1800$.")])
    return ochiq(f"Muntazam o‘n ikki burchakning tashqi chizilgan aylana radiusi {R}.",
                 [("a) Uning yuzini toping.", 3 * R * R), (b[0], b[1])],
                 [f"a) 12 ta teng uchburchakka bo‘lamiz, har birining yuzi $\\frac{{1}}{{2}}R^2\\sin30^\\circ=\\frac{{R^2}}{{4}}$. Yuz: $12\\cdot \\frac{{{R * R}}}{{4}}={3 * R * R}$.", "b) " + b[2]])


@shablon(44, "silindr")
def s44(rng):
    r, h = rng.randint(2, 9), rng.randint(2, 9)
    return ochiq(f"Silindrning asos radiusi {r}, balandligi {h}.",
                 [("a) Yon sirti yuzining $\\pi$ ga nisbatini toping.", 2 * r * h), ("b) Hajmining $\\pi$ ga nisbatini toping.", r * r * h)],
                 [f"a) $S_{{yon}}=2\\pi rh$, $\\frac{{S}}{{\\pi}}=2\\cdot {r}\\cdot {h}={2 * r * h}$.", f"b) $V=\\pi r^2h$, $\\frac{{V}}{{\\pi}}={r}^2\\cdot {h}={r * r * h}$."])


@shablon(45, "gumbaz")
def s45(rng):
    R = rng.choice(range(3, 61, 3))
    if rng.random() < .5:
        q = ("a) To‘liq sirtini (asosi bilan) $\\pi$ ga nisbatan toping ($S/\\pi$).", 3 * R * R, f"a) Egri sirt $2\\pi R^2$ va asos $\\pi R^2$: $3\\pi R^2$, $\\frac{{S}}{{\\pi}}=3\\cdot {R}^2={3 * R * R}$.")
    else:
        q = ("a) Egri sirtining yuzini $\\pi$ ga nisbatan toping ($S/\\pi$).", 2 * R * R, f"a) Yarim shar sirti $2\\pi R^2$, $\\frac{{S}}{{\\pi}}=2\\cdot {R}^2={2 * R * R}$.")
    return ochiq(f"Gumbaz yarim shar shaklida, radiusi {R}.", [(q[0], q[1]), ("b) Hajmini $\\pi$ ga nisbatan toping ($V/\\pi$).", Fraction(2 * R ** 3, 3))],
                 [q[2], f"b) $V=\\frac{{2}}{{3}}\\pi R^3$, $\\frac{{V}}{{\\pi}}=\\frac{{2\\cdot {R ** 3}}}{{3}}={fx(Fraction(2 * R ** 3, 3))}$."])
