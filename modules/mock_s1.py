"""MOCK shablonlari 1–12: sonlar, hisoblash, foiz, harakat, ildiz, progressiya, ifodalar, trigonometriya."""
import itertools
import math
from fractions import Fraction

import sympy as sp

from modules.mock_lib import M, fx, ochiq, shablon, tub, yopiq


# ───────── 1: raqamlar va bo'linish ─────────
@shablon(1, "raqamli son")
def s1a(rng):
    while True:
        k = rng.randint(3, 8)
        yech = [n for n in range(10, 100) if n == k * (n // 10 + n % 10)]
        if yech:
            break
    return yopiq(rng, f"Ikki xonali $\\overline{{xy}}$ son o‘z raqamlari yig‘indisidan {k} marta katta. Barcha shunday sonlarning yig‘indisini toping.", sum(yech),
                 [f"$10x+y={k}(x+y)$ tenglamadan $(10-{k})x={k - 1}y$ hosil bo‘ladi.", f"Raqamlarni $1\\le x\\le 9,\\ 0\\le y\\le 9$ oralig‘ida tekshiramiz: sonlar {', '.join(map(str, yech))}.",
                  f"Yig‘indi: ${'+'.join(map(str, yech))}={sum(yech)}$."])


@shablon(1, "bo'linish belgisi")
def s1b(rng):
    while True:
        d1, d2 = rng.randint(1, 9), rng.randint(0, 9)
        m = rng.choice([6, 9, 12, 15, 18, 36, 45])
        sol = [(a, b) for a in range(1, 10) for b in range(10) if int(f"{a}{d1}{b}{d2}") % m == 0]
        if len(sol) >= 2:
            break
    en = max(sol, key=lambda x: x[0] * x[1])
    return yopiq(rng, f"$\\overline{{a{d1}b{d2}}}$ to‘rt xonali son {m} ga qoldiqsiz bo‘linadi. $a\\cdot b$ ning eng katta qiymatini toping.", en[0] * en[1],
                 [f"Son {m} ga bo‘linishi uchun bo‘linish belgilari bajarilishi kerak; $a$ va $b$ ning barcha raqamli qiymatlarini tekshiramiz.",
                  f"Mos juftliklar $(a;b)$: {', '.join(f'({x};{y})' for x, y in sol)}.", f"Ko‘paytmalar ichida eng kattasi: ${en[0]}\\cdot {en[1]}={en[0] * en[1]}$."])


@shablon(1, "bo'luvchilar soni")
def s1c(rng):
    pr = rng.sample([2, 3, 5, 7, 11], 3)
    e = [rng.randint(1, 4), rng.randint(1, 4), rng.randint(1, 3)]
    odd = rng.random() < .6
    N = " \\cdot ".join(f"{p}^{{{x}}}" for p, x in zip(pr, e))
    if odd:
        pr_o = [(p, x) for p, x in zip(pr, e) if p != 2]
        if len(pr_o) == 3:
            pr_o = pr_o[1:]
        ans = math.prod(x + 1 for _, x in pr_o)
        return yopiq(rng, f"$N={N}$ sonining toq natural bo‘luvchilari nechta?", ans,
                     ["Toq bo‘luvchilarda 2 ning darajasi qatnashmaydi.", f"Qolgan tub sonlar bo‘yicha: ${'\\cdot '.join(f'({x}+1)' for _, x in pr_o)}={ans}$."] if pr_o != list(zip(pr, e)) else
                     ["Barcha tub ko‘paytuvchilar toq, shuning uchun hamma bo‘luvchilar toq.", f"${'\\cdot '.join(f'({x}+1)' for x in e)}={ans}$."])
    ans = math.prod(x + 1 for x in e)
    return yopiq(rng, f"$N={N}$ sonining barcha natural bo‘luvchilari nechta?", ans, ["Bo‘luvchilar soni: darajalarga bittadan qo‘shib ko‘paytiramiz.", f"${'\\cdot '.join(f'({x}+1)' for x in e)}={ans}$."])


# ───────── 2: hisoblang ─────────
def _kasr(rng, lo=1, hi=9):
    return Fraction(rng.randint(lo, hi), rng.randint(2, 9))


@shablon(2, "kasrli ifoda")
def s2a(rng):
    while True:
        a, b, c, d = _kasr(rng, 1, 7), _kasr(rng), _kasr(rng), rng.randint(2, 6)
        v = (a + b) / c - Fraction(d)
        if v.denominator <= 12 and abs(v) < 30 and v != 0:
            break
    ex = f"\\left({fx(a)}+{fx(b)}\\right):{fx(c)}-{d}"
    return yopiq(rng, f"Hisoblang: ${ex}$.", v, [f"Qavs ichi: ${fx(a)}+{fx(b)}={fx(a + b)}$.", f"Bo‘lish: ${fx(a + b)}:{fx(c)}={fx((a + b) / c)}$.", f"Ayirish: ${fx((a + b) / c)}-{d}={fx(v)}$."])


@shablon(2, "davriy kasr")
def s2b(rng):
    a, b, c = rng.randint(1, 9), rng.randint(1, 9), rng.randint(1, 9)
    x = Fraction(a, 9)                    # 0,(a)
    y = Fraction(b * 10 + c - b, 90)      # 0,b(c)
    op = rng.choice(["+", "·"])
    v = x + y if op == "+" else x * y
    ex = f"0{{,}}({a}){'+' if op == '+' else chr(92) + 'cdot '}0{{,}}{b}({c})"
    return yopiq(rng, f"Hisoblang: ${ex}$.", v, [f"$0{{,}}({a})=\\frac{{{a}}}{{9}}$.", f"$0{{,}}{b}({c})=\\frac{{{b}{c}-{b}}}{{90}}={fx(y)}$.", f"Natija: ${fx(x)}{'+' if op == '+' else chr(92) + 'cdot '}{fx(y)}={fx(v)}$."])


@shablon(2, "darajali ifoda")
def s2c(rng):
    p = rng.choice([2, 3, 5])
    k, m = rng.randint(2, 4), rng.randint(2, 4)
    n = rng.randint(5, 20)
    v = Fraction(k * p ** n, m * p ** (n - 1))
    return yopiq(rng, f"Hisoblang: $\\dfrac{{{'+'.join([f'{p}^{{{n}}}'] * k)}}}{{{'+'.join([f'{p}^{{{n - 1}}}'] * m)}}}$.", v,
                 [f"Surat: ${k}\\cdot {p}^{{{n}}}$, maxraj: ${m}\\cdot {p}^{{{n - 1}}}$.", f"Kasr: $\\frac{{{k}\\cdot {p}}}{{{m}}}={fx(v)}$."])


# ───────── 3: foiz ─────────
@shablon(3, "narx o'zgarishi")
def s3a(rng):
    while True:
        P, x, y = rng.choice([200, 400, 500, 800, 1000, 1200, 2000]), rng.choice([10, 20, 25, 30, 40, 50]), rng.choice([10, 20, 25, 30, 40, 50])
        v = Fraction(P) * (100 + x) / 100 * (100 - y) / 100
        if v.denominator == 1:
            break
    return yopiq(rng, f"Mahsulot narxi {P} so‘m edi. Avval {x}% ga oshirildi, keyin {y}% ga arzonlashtirildi. Yangi narx necha so‘m?", v,
                 [f"Oshirilgach: ${P}\\cdot {fx(Fraction(100 + x, 100))}={fx(Fraction(P) * (100 + x) / 100)}$.", f"Arzonlashgach: ${fx(Fraction(P) * (100 + x) / 100)}\\cdot {fx(Fraction(100 - y, 100))}={fx(v)}$."])


@shablon(3, "aralashma foizi")
def s3b(rng):
    while True:
        m1, m2 = rng.choice([100, 150, 200, 250, 300]), rng.choice([100, 200, 300, 400, 500])
        c1, c2 = rng.choice([5, 10, 15, 20, 25]), rng.choice([30, 35, 40, 45, 50])
        v = Fraction(m1 * c1 + m2 * c2, m1 + m2)
        if v.denominator == 1:
            break
    return yopiq(rng, f"Shakar miqdori {c1}% bo‘lgan {m1} g choy bilan shakar miqdori {c2}% bo‘lgan {m2} g choy aralashtirildi. Hosil bo‘lgan choyda shakar necha foiz?", v,
                 [f"Shakar: ${m1}\\cdot {c1}/100+{m2}\\cdot {c2}/100={fx(Fraction(m1 * c1 + m2 * c2, 100))}$ g.", f"Umumiy massa: ${m1 + m2}$ g, foiz: ${fx(Fraction(m1 * c1 + m2 * c2, 100))}/{m1 + m2}\\cdot 100={fx(v)}\\%$."])


@shablon(3, "foyda va zarar")
def s3c(rng):
    while True:
        n, s, x, y = rng.choice([10, 20, 40]), rng.choice([8, 10, 12, 16, 20]), rng.choice([10, 20, 25]), rng.choice([10, 20, 25, 30, 50])
        cost = Fraction(rng.choice([50, 80, 100, 120, 150, 200]))   # bitta mahsulot tannarxi
        k = rng.randint(2, n - 1) * 1
        # k ta zarar bilan, qolgani foyda bilan
        tushum = k * cost * (100 - x) / 100 + (n - k) * cost * (100 + y) / 100
        foyda = tushum - n * cost
        if foyda.denominator == 1 and foyda != 0:
            break
    return yopiq(rng, f"Do‘konchi tannarxi {cost} so‘m bo‘lgan {n} ta mahsulotdan {k} tasini {x}% zarar bilan, qolganini {y}% foyda bilan sotdi. Umumiy foyda (zarar bo‘lsa manfiy) necha so‘m?", foyda,
                 [f"Zarar bilan: ${k}\\cdot {cost}\\cdot {fx(Fraction(100 - x, 100))}={fx(k * cost * (100 - x) / 100)}$.", f"Foyda bilan: ${n - k}\\cdot {cost}\\cdot {fx(Fraction(100 + y, 100))}={fx((n - k) * cost * (100 + y) / 100)}$.",
                  f"Tushum ${fx(tushum)}$, xarajat ${fx(n * cost)}$, farq ${fx(foyda)}$."])


# ───────── 4: harakat va ish ─────────
@shablon(4, "daryodagi qayiq")
def s4a(rng):
    while True:
        v, c, T = rng.choice([50, 60, 70, 80, 90]), rng.choice([5, 10, 15, 20]), rng.choice([60, 80, 100, 120, 140, 160, 180])
        D = Fraction(T * (v * v - c * c), 2 * v)
        if c < v and D.denominator == 1 and D % 100 == 0:
            break
    km = D / 1000
    return yopiq(rng, f"Tinch suvdagi tezligi {v} m/daq bo‘lgan qayiqning yonilg‘isi ko‘pi bilan {T} daqiqaga yetadi. To‘lqinlar tezligi {c} m/daq bo‘lgan kuni qayiq boshlang‘ich nuqtadan ko‘pi bilan necha kilometr uzoqlashib, ortiga qaytib kela oladi?", km,
                 [f"Oqim bo‘ylab tezlik ${v + c}$, oqimga qarshi ${v - c}$ m/daq. Masofa $D$ bo‘lsin.", f"$\\frac{{D}}{{{v + c}}}+\\frac{{D}}{{{v - c}}}={T}$, bundan $D={T}\\cdot\\frac{{{v}^2-{c}^2}}{{2\\cdot {v}}}={fx(D)}$ m.", f"Kilometrda: ${fx(km)}$."])


@shablon(4, "birgalikda ishlash")
def s4b(rng):
    while True:
        a, b = rng.randint(2, 20), rng.randint(2, 20)
        if a != b:
            v = Fraction(a * b, a + b)
            if v.denominator <= 10:
                break
    return yopiq(rng, f"Birinchi quvur hovuzni {a} soatda, ikkinchisi {b} soatda to‘ldiradi. Ikkalasi birga ochilsa, hovuz necha soatda to‘ladi?", v,
                 [f"Bir soatda: $\\frac{{1}}{{{a}}}+\\frac{{1}}{{{b}}}=\\frac{{{a + b}}}{{{a * b}}}$.", f"To‘lish vaqti: $\\frac{{{a * b}}}{{{a + b}}}={fx(v)}$ soat."])


@shablon(4, "uchrashish")
def s4c(rng):
    while True:
        v1, v2, S = rng.choice([40, 45, 50, 60, 70]), rng.choice([30, 35, 45, 55, 65]), rng.choice([300, 360, 420, 450, 500, 600])
        t = Fraction(S, v1 + v2)
        if t.denominator <= 4 and v1 != v2:
            break
    return yopiq(rng, f"A va B shaharlar orasidagi masofa {S} km. A dan {v1} km/soat, B dan {v2} km/soat tezlik bilan ikkita avtomobil bir vaqtda bir-biriga qarab yo‘lga chiqdi. Necha soatdan keyin uchrashadi?", t,
                 [f"Yaqinlashish tezligi: ${v1}+{v2}={v1 + v2}$ km/soat.", f"Vaqt: $\\frac{{{S}}}{{{v1 + v2}}}={fx(t)}$ soat."])


# ───────── 5: darajali ifodani soddalashtirish ─────────
def _mon(a, b):
    def term(n, e):
        return "" if e == 0 else (n if e == 1 else f"{n}^{{{e}}}")
    s = term("a", a) + term("b", b)
    return s or "1"


@shablon(5, "darajalar bo'linmasi")
def s5a(rng):
    p, q, r, s = rng.randint(1, 4), rng.randint(1, 4), rng.randint(1, 4), rng.randint(1, 4)
    ea, eb = p + r, -(q + s)
    sav = f"$a,b\\neq 0$ bo‘lsa, ifodani soddalashtiring: $\\dfrac{{a^{{n+{p}}}\\,b^{{n-{q}}}}}{{a^{{n-{r}}}\\,b^{{n+{s}}}}}$."
    tog = f"\\frac{{{_mon(ea, 0)}}}{{{_mon(0, -eb)}}}"
    noto = [f"\\frac{{{_mon(p - r, 0)}}}{{{_mon(0, q + s)}}}", f"{_mon(ea, 0)}{_mon(0, q + s)}", f"\\frac{{{_mon(0, -eb)}}}{{{_mon(ea, 0)}}}", f"\\frac{{{_mon(p + r + 1, 0)}}}{{{_mon(0, q + s)}}}"]
    return yopiq(rng, sav, "$" + tog + "$", [f"$a$ bo‘yicha: $a^{{(n+{p})-(n-{r})}}=a^{{{ea}}}$.", f"$b$ bo‘yicha: $b^{{(n-{q})-(n+{s})}}=b^{{{eb}}}$.", f"Natija: ${tog}$."],
                 noto=["$" + x + "$" for x in noto], tartib=False)


@shablon(5, "daraja ko'paytmasi")
def s5b(rng):
    x, y, z, w = rng.randint(2, 5), rng.randint(2, 4), rng.randint(2, 7), rng.randint(1, 6)
    e = x * y + z - w
    tog = f"x^{{{e}}}" if e != 1 else "x"
    return yopiq(rng, f"$x\\neq 0$ bo‘lsa, soddalashtiring: $\\dfrac{{(x^{{{x}}})^{{{y}}}\\cdot x^{{{z}}}}}{{x^{{{w}}}}}$.", "$" + tog + "$",
                 [f"$(x^{{{x}}})^{{{y}}}=x^{{{x * y}}}$.", f"Ko‘paytma: $x^{{{x * y}+{z}}}=x^{{{x * y + z}}}$, bo‘lish: $x^{{{x * y + z}-{w}}}=x^{{{e}}}$."],
                 noto=[f"$x^{{{e + 1}}}$", f"$x^{{{x * y + z + w}}}$", f"$x^{{{e - 1}}}$", f"$x^{{{x + y + z - w}}}$"], tartib=False)


@shablon(5, "teng darajalar yig'indisi")
def s5c(rng):
    k, m = rng.choice([2, 3, 4, 5]), rng.choice([2, 3, 4, 5])
    p = rng.choice([2, 3, 5]); n = rng.randint(6, 16)
    v = Fraction(k * p ** n, m * p ** (n - 2))
    return yopiq(rng, f"Hisoblang: $\\dfrac{{{'+'.join([f'{p}^{{{n}}}'] * k)}}}{{{'+'.join([f'{p}^{{{n - 2}}}'] * m)}}}$.", v,
                 [f"Surat: ${k}\\cdot {p}^{{{n}}}$, maxraj: ${m}\\cdot {p}^{{{n - 2}}}$.", f"${fx(Fraction(k, m))}\\cdot {p}^{{2}}={fx(v)}$."])


# ───────── 6, 7: ildizli ifodalar ─────────
def _lat(e):
    return sp.latex(e).replace("\\left", "").replace("\\right", "")


@shablon(6, "ildizli ko'paytma")
def s6a(rng):
    m, n = rng.sample([2, 3, 5, 6, 7, 10, 11], 2)
    k = rng.randint(1, 4)
    e = (sp.sqrt(m) + sp.sqrt(n)) ** 2 + (sp.sqrt(m) - sp.sqrt(n)) ** 2 - k
    v = sp.simplify(sp.expand(e))
    return yopiq(rng, f"Hisoblang: $(\\sqrt{{{m}}}+\\sqrt{{{n}}})^2+(\\sqrt{{{m}}}-\\sqrt{{{n}}})^2-{k}$.", int(v),
                 [f"$(\\sqrt{{{m}}}\\pm\\sqrt{{{n}}})^2={m}+{n}\\pm 2\\sqrt{{{m * n}}}$.", f"Yig‘indida ildizli had yo‘qoladi: $2({m}+{n})-{k}={int(v)}$."])


@shablon(6, "ichma-ich ildiz")
def s6b(rng):
    k, l = rng.randint(2, 7), rng.randint(1, 6)
    while l == k:
        l = rng.randint(1, 6)
    p, q = k * k + l * l, k * l
    v = 2 * max(k, l)
    return yopiq(rng, f"Hisoblang: $\\sqrt{{{p}+2\\sqrt{{{q * q}}}}}+\\sqrt{{{p}-2\\sqrt{{{q * q}}}}}$.", v,
                 [f"$\\sqrt{{{q * q}}}={q}$, demak $\\sqrt{{{p}+{2 * q}}}+\\sqrt{{{p}-{2 * q}}}$.", f"${p}\\pm {2 * q}$ — to‘liq kvadratlar: $({k}\\pm {l})^2$.", f"Natija: $({k}+{l})+|{k}-{l}|={v}$."])


@shablon(6, "kub ildiz")
def s6c(rng):
    a = rng.randint(2, 9)
    v = a ** 3
    return yopiq(rng, f"Hisoblang: $\\sqrt[3]{{{v}}}\\cdot\\sqrt{{{a * a}}}+\\sqrt[3]{{{a ** 6}}}$.", a * a + a * a, [f"$\\sqrt[3]{{{v}}}={a}$, $\\sqrt{{{a * a}}}={a}$, $\\sqrt[3]{{{a ** 6}}}={a * a}$.", f"${a}\\cdot {a}+{a * a}={2 * a * a}$."])


@shablon(7, "ildizlarni soddalashtirish")
def s7a(rng):
    ds = rng.choice([2, 3, 5, 6, 7])
    c = [rng.randint(1, 5) for _ in range(6)]
    a1 = f"{c[0]}\\sqrt{{{ds}}}+{c[1]}\\sqrt{{{ds}}}-{c[2]}\\sqrt{{{ds}}}"
    # (√(c0²ds)+√(c1²ds)−√(c2²ds))(√(c3²ds)−√(c4²ds)+√(c5²ds)) → ds·(c0+c1−c2)(c3−c4+c5)
    r1, r2 = [c[0] ** 2 * ds, c[1] ** 2 * ds, c[2] ** 2 * ds], [c[3] ** 2 * ds, c[4] ** 2 * ds, c[5] ** 2 * ds]
    v = ds * (c[0] + c[1] - c[2]) * (c[3] - c[4] + c[5])
    return yopiq(rng, f"Hisoblang: $(\\sqrt{{{r1[0]}}}+\\sqrt{{{r1[1]}}}-\\sqrt{{{r1[2]}}})(\\sqrt{{{r2[0]}}}-\\sqrt{{{r2[1]}}}+\\sqrt{{{r2[2]}}})$.", v,
                 [f"Ildizlarni soddalashtiramiz: $\\sqrt{{{r1[0]}}}={c[0]}\\sqrt{{{ds}}}$, $\\sqrt{{{r1[1]}}}={c[1]}\\sqrt{{{ds}}}$, $\\sqrt{{{r1[2]}}}={c[2]}\\sqrt{{{ds}}}$.",
                  f"Birinchi qavs: $({c[0] + c[1] - c[2]})\\sqrt{{{ds}}}$, ikkinchi qavs: $({c[3] - c[4] + c[5]})\\sqrt{{{ds}}}$.", f"Ko‘paytma: ${(c[0] + c[1] - c[2])}\\cdot {(c[3] - c[4] + c[5])}\\cdot {ds}={v}$."])


@shablon(7, "ildiz kasr")
def s7b(rng):
    a, b = rng.sample([2, 3, 5, 6, 7], 2)
    e = 1 / (sp.sqrt(a) + sp.sqrt(b)) + 1 / (sp.sqrt(a) - sp.sqrt(b))
    v = sp.nsimplify(sp.simplify(e))        # 2√a/(a−b)
    ans = Fraction(2, a - b) if False else None
    tog = f"\\frac{{2\\sqrt{{{a}}}}}{{{a - b}}}" if a - b > 0 else f"-\\frac{{2\\sqrt{{{a}}}}}{{{b - a}}}"
    k = a - b
    return yopiq(rng, f"Soddalashtiring: $\\dfrac{{1}}{{\\sqrt{{{a}}}+\\sqrt{{{b}}}}}+\\dfrac{{1}}{{\\sqrt{{{a}}}-\\sqrt{{{b}}}}}$.", "$" + tog + "$",
                 ["Umumiy maxraj: $(\\sqrt{" + str(a) + "}+\\sqrt{" + str(b) + "})(\\sqrt{" + str(a) + "}-\\sqrt{" + str(b) + "})=" + f"{a}-{b}={k}$.", f"Suratda $(\\sqrt{{{a}}}-\\sqrt{{{b}}})+(\\sqrt{{{a}}}+\\sqrt{{{b}}})=2\\sqrt{{{a}}}$.", f"Natija: ${tog}$."],
                 noto=[f"$\\frac{{2\\sqrt{{{b}}}}}{{{k}}}$", f"$\\frac{{2\\sqrt{{{a}}}}}{{{a + b}}}$", f"$\\frac{{\\sqrt{{{a}}}}}{{{k}}}$", f"$-\\frac{{2\\sqrt{{{a}}}}}{{{k}}}$"], tartib=False)


@shablon(7, "ildizlar yig'indisi kvadrati")
def s7c(rng):
    a = rng.randint(3, 15)
    r = rng.randint(1, a - 1)
    b = a * a - r * r          # (√(a+√b)+√(a−√b))² = 2a + 2√(a²−b) = 2a + 2r
    v = 2 * a + 2 * r
    return yopiq(rng, f"Hisoblang: $\\left(\\sqrt{{{a}+\\sqrt{{{b}}}}}+\\sqrt{{{a}-\\sqrt{{{b}}}}}\\right)^2$.", v,
                 [f"Kvadratga ko‘taramiz: $({a}+\\sqrt{{{b}}})+({a}-\\sqrt{{{b}}})+2\\sqrt{{({a}+\\sqrt{{{b}}})({a}-\\sqrt{{{b}}})}}$.", f"Ildiz ostida: ${a}^2-{b}={a * a - b}={r}^2$.", f"Natija: $2\\cdot {a}+2\\cdot {r}={v}$."])


# ───────── 8, 9: progressiyalar ─────────
@shablon(8, "arifmetik progressiya")
def s8a(rng):
    a1, d = rng.randint(-5, 9), rng.randint(2, 6)
    n, m = rng.randint(2, 4), rng.randint(6, 9)
    a = lambda k: a1 + (k - 1) * d
    S = lambda k: k * (2 * a1 + (k - 1) * d) // 2
    diff = S(m) - S(n)
    kk = rng.randint(n + 1, m)
    cnt = m - n
    # S_m − S_n = a_{n+1}+…+a_m = cnt·(a_{n+1}+a_m)/2 ; bu a_{(n+m+1)/2} ga bog'liq faqat n+m toq bo'lsa
    if (n + m + 1) % 2:
        m += 1; diff = S(m) - S(n); cnt = m - n
    mid = (n + m + 1) // 2
    return yopiq(rng, f"$(a_n)$ arifmetik progressiyada $S_{{{m}}}-S_{{{n}}}={diff}$ bo‘lsa, $a_{{{mid}}}$ ni toping.", Fraction(diff, cnt),
                 [f"$S_{{{m}}}-S_{{{n}}}=a_{{{n + 1}}}+a_{{{n + 2}}}+\\dots+a_{{{m}}}$ — bu ${cnt}$ ta had yig‘indisi.", f"Hadlar o‘rtasi $a_{{{mid}}}$, shu sababli yig‘indi ${cnt}\\cdot a_{{{mid}}}$.", f"$a_{{{mid}}}=\\frac{{{diff}}}{{{cnt}}}={fx(Fraction(diff, cnt))}$."])


@shablon(8, "AP yig'indisi")
def s8b(rng):
    a1, d, n = rng.randint(1, 12), rng.randint(2, 7), rng.randint(8, 20)
    return yopiq(rng, f"Arifmetik progressiyada $a_1={a1}$, $d={d}$. Dastlabki {n} ta hadning yig‘indisini toping.", n * (2 * a1 + (n - 1) * d) // 2,
                 [f"$S_n=\\frac{{2a_1+(n-1)d}}{{2}}\\cdot n$.", f"$S_{{{n}}}=\\frac{{2\\cdot {a1}+{n - 1}\\cdot {d}}}{{2}}\\cdot {n}={n * (2 * a1 + (n - 1) * d) // 2}$."])


@shablon(8, "AP hadlari")
def s8c(rng):
    a1, d = rng.randint(-8, 10), rng.randint(2, 7)
    p, q = rng.randint(2, 5), rng.randint(7, 12)
    ap, aq = a1 + (p - 1) * d, a1 + (q - 1) * d
    k = rng.randint(q + 1, q + 6)
    return yopiq(rng, f"Arifmetik progressiyada $a_{{{p}}}={ap}$ va $a_{{{q}}}={aq}$. $a_{{{k}}}$ ni toping.", a1 + (k - 1) * d,
                 [f"$d=\\frac{{a_{{{q}}}-a_{{{p}}}}}{{{q}-{p}}}=\\frac{{{aq - ap}}}{{{q - p}}}={d}$.", f"$a_{{{k}}}=a_{{{q}}}+{k - q}d={aq}+{k - q}\\cdot {d}={a1 + (k - 1) * d}$."])


@shablon(9, "geometrik progressiya")
def s9a(rng):
    b1, q = rng.randint(1, 5), rng.choice([2, 3, 4, -2, -3])
    b = lambda k: b1 * q ** (k - 1)
    m, n = 5, 3   # b5 − b3 va b4 − b2
    A, B = b(5) - b(3), b(4) - b(2)
    return yopiq(rng, f"Geometrik progressiyada $b_5-b_3={A}$ va $b_4-b_2={B}$ bo‘lsa, birinchi hadini toping.", b1,
                 [f"$b_5-b_3=b_3(q^2-1)$, $b_4-b_2=b_2(q^2-1)$. Nisbat: $\\frac{{b_3}}{{b_2}}=q=\\frac{{{A}}}{{{B}}}={q}$.", f"$b_4-b_2=b_1q(q^2-1)={B}$: $b_1\\cdot {q}\\cdot {q * q - 1}={B}$.", f"$b_1={b1}$."])


@shablon(9, "GP hadi")
def s9b(rng):
    b1, q, n = rng.randint(1, 6), rng.choice([2, 3, 4]), rng.randint(4, 7)
    return yopiq(rng, f"Geometrik progressiyada $b_1={b1}$, $q={q}$. $b_{{{n}}}$ ni toping.", b1 * q ** (n - 1), [f"$b_n=b_1q^{{n-1}}$.", f"$b_{{{n}}}={b1}\\cdot {q}^{{{n - 1}}}={b1 * q ** (n - 1)}$."])


@shablon(9, "GP yig'indisi")
def s9c(rng):
    b1, q, n = rng.randint(1, 5), rng.choice([2, 3, 4]), rng.randint(4, 7)
    return yopiq(rng, f"Geometrik progressiyada $b_1={b1}$, $q={q}$. Dastlabki {n} ta hadning yig‘indisini toping.", b1 * (q ** n - 1) // (q - 1),
                 [f"$S_n=\\frac{{b_1(q^n-1)}}{{q-1}}$.", f"$S_{{{n}}}=\\frac{{{b1}({q}^{{{n}}}-1)}}{{{q}-1}}={b1 * (q ** n - 1) // (q - 1)}$."])


# ───────── 10, 11: ifodalar ─────────
@shablon(10, "algebraik kasr qiymati")
def s10a(rng):
    a = rng.randint(1, 5)
    x0 = rng.randint(a + 2, a + 9)
    # (x²−a²)/(x²+2ax+a²) : (x−a)/(x+a) = 1 emas — aniq: (x²−a²)/(x+a)² · (x+a)/(x−a)... murakkabroq:
    # ((x+a)/(x−a) − (x−a)/(x+a)) : (4ax/(x²−a²)) = 1 ... qiymatni ko'paytma bilan o'zgartiramiz
    k = rng.randint(2, 5)
    v = Fraction(k * (x0 * x0 + a * a), 1)   # ((x+a)/(x−a) + (x−a)/(x+a)) = 2(x²+a²)/(x²−a²)
    # ifoda: k·(x²−a²)/2 · ((x+a)/(x−a) + (x−a)/(x+a))/… → k(x²+a²)
    ex = f"\\frac{{{k}(x^2-{a * a})}}{{2}}\\left(\\frac{{x+{a}}}{{x-{a}}}+\\frac{{x-{a}}}{{x+{a}}}\\right)"
    return yopiq(rng, f"$x={x0}$ bo‘lganda ifodaning qiymatini toping: ${ex}$.", v,
                 [f"Qavs ichi: $\\frac{{(x+{a})^2+(x-{a})^2}}{{x^2-{a * a}}}=\\frac{{2(x^2+{a * a})}}{{x^2-{a * a}}}$.", f"Ifoda $={k}(x^2+{a * a})$.", f"$x={x0}$: ${k}({x0 * x0}+{a * a})={fx(v)}$."])


@shablon(10, "ko'phadlar")
def s10b(rng):
    a = rng.randint(1, 6)
    b = rng.choice([x for x in range(1, 7) if x != a])
    x0 = rng.randint(2, 9)
    v = (x0 + a) * (x0 - b) - (x0 * x0 + (a - b) * x0)       # = −ab
    return yopiq(rng, f"Soddalashtirib, $x={x0}$ da qiymatini toping: $(x+{a})(x-{b})-(x^2+{a - b}x)$.", v,
                 [f"Qavsni ochamiz: $(x+{a})(x-{b})=x^2+({a - b})x-{a * b}$.", f"Ayiramiz: $-{a * b}$ — ifoda $x$ ga bog‘liq emas.", f"Qiymati ${v}$."],
                 noto=[a * b, -(a + b), a - b])


@shablon(11, "x+1/x")
def s11a(rng):
    s = rng.randint(3, 8)
    kind = rng.choice([2, 3])
    v = s * s - 2 if kind == 2 else s ** 3 - 3 * s
    return yopiq(rng, f"$x+\\dfrac{{1}}{{x}}={s}$ bo‘lsa, $x^{kind}+\\dfrac{{1}}{{x^{kind}}}$ ni toping.", v,
                 ["Kvadratga ko‘taramiz: $x^2+\\frac{1}{x^2}=(x+\\frac1x)^2-2$." if kind == 2 else "Kubga: $x^3+\\frac1{x^3}=(x+\\frac1x)^3-3(x+\\frac1x)$.",
                  f"${s * s}-2={s * s - 2}$." if kind == 2 else f"${s}^3-3\\cdot {s}={v}$."])


@shablon(11, "ildizli x")
def s11b(rng):
    n = rng.choice([2, 3, 5, 6, 7])
    k = rng.randint(1, 4)
    # x=√n: (x+k)(x−k) = n−k²
    return yopiq(rng, f"$x=\\sqrt{{{n}}}$ bo‘lsa, $(x+{k})(x-{k})+x^2$ ning qiymatini toping.", 2 * n - k * k,
                 [f"$(x+{k})(x-{k})=x^2-{k * k}$.", f"$x^2={n}$, shuning uchun $2x^2-{k * k}=2\\cdot {n}-{k * k}={2 * n - k * k}$."])


@shablon(11, "ildizli kasr")
def s11c(rng):
    n = rng.choice([2, 3, 5, 6, 7, 10])
    # (√n+1)/(√n−1) − (√n−1)/(√n+1) = 4√n/(n−1)  → ·(n−1)/4 → √n ... natija: √n  → kvadrat: n
    ans = n
    return yopiq(rng, f"Hisoblang: $\\left(\\dfrac{{\\sqrt{{{n}}}+1}}{{\\sqrt{{{n}}}-1}}-\\dfrac{{\\sqrt{{{n}}}-1}}{{\\sqrt{{{n}}}+1}}\\right)^2\\cdot\\dfrac{{({n}-1)^2}}{{16}}$.", ans,
                 [f"Qavs: $\\frac{{(\\sqrt{{{n}}}+1)^2-(\\sqrt{{{n}}}-1)^2}}{{{n}-1}}=\\frac{{4\\sqrt{{{n}}}}}{{{n}-1}}$.", f"Kvadrat: $\\frac{{16\\cdot {n}}}{{({n}-1)^2}}$.", f"Ko‘paytirib: ${n}$."])


# ───────── 12: trigonometriya ─────────
@shablon(12, "ikkilangan burchak")
def s12a(rng):
    p, q, r = rng.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)])
    quad = rng.choice([1, 2, 3, 4])
    cos = Fraction(p, r) if quad in (1, 4) else -Fraction(p, r)
    sin = Fraction(q, r) if quad in (1, 2) else -Fraction(q, r)
    nom = {1: "birinchi", 2: "ikkinchi", 3: "uchinchi", 4: "to‘rtinchi"}[quad]
    f = rng.choice(["sin", "cos", "tg"])
    if f == "sin":
        v, ex, st = 2 * sin * cos, "\\sin 2\\alpha", "\\sin2\\alpha=2\\sin\\alpha\\cos\\alpha"
    elif f == "cos":
        v, ex, st = cos * cos - sin * sin, "\\cos 2\\alpha", "\\cos2\\alpha=\\cos^2\\alpha-\\sin^2\\alpha"
    else:
        t = sin / cos
        v, ex, st = 2 * t / (1 - t * t), "\\operatorname{tg} 2\\alpha", "\\operatorname{tg}2\\alpha=\\frac{2\\operatorname{tg}\\alpha}{1-\\operatorname{tg}^2\\alpha}"
    return yopiq(rng, f"$\\cos\\alpha={fx(cos)}$ va $\\alpha$ {nom} chorak burchagi bo‘lsa, ${ex}$ ni toping.", v,
                 [f"$\\sin\\alpha=\\pm\\sqrt{{1-\\cos^2\\alpha}}$, {nom} chorakda $\\sin\\alpha={fx(sin)}$.", f"${st}$.", f"Natija: ${fx(v)}$."])


@shablon(12, "tangens yig'indisi")
def s12b(rng):
    p, q, r = rng.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17)])
    sgn = rng.choice([1, -1])
    t = Fraction(q, p) * sgn           # tg α
    v = (1 + t) / (1 - t)
    return yopiq(rng, f"$\\operatorname{{tg}}\\alpha={fx(t)}$ bo‘lsa, $\\operatorname{{tg}}\\left(\\dfrac{{\\pi}}{{4}}+\\alpha\\right)$ ni toping.", v,
                 ["$\\operatorname{tg}(\\frac{\\pi}{4}+\\alpha)=\\frac{1+\\operatorname{tg}\\alpha}{1-\\operatorname{tg}\\alpha}$.", f"$=\\frac{{1+{fx(t)}}}{{1-{fx(t)}}}={fx(v)}$."])


@shablon(12, "burchaklar yig'indisi")
def s12c(rng):
    p, q, r = rng.choice([(3, 4, 5), (5, 12, 13), (8, 15, 17)])
    s1, c2 = Fraction(p, r), Fraction(p, r)       # sinα = p/r; cosβ = p/r (o'tkir burchaklar)
    c1 = Fraction(q, r); s2 = Fraction(q, r)
    v = s1 * c2 + c1 * s2
    return yopiq(rng, f"$\\alpha,\\beta$ — o‘tkir burchaklar, $\\sin\\alpha={fx(s1)}$, $\\cos\\beta={fx(c2)}$. $\\sin(\\alpha+\\beta)$ ni toping.", v,
                 [f"$\\cos\\alpha=\\sqrt{{1-\\sin^2\\alpha}}={fx(c1)}$, $\\sin\\beta=\\sqrt{{1-\\cos^2\\beta}}={fx(s2)}$.", f"$\\sin(\\alpha+\\beta)=\\sin\\alpha\\cos\\beta+\\cos\\alpha\\sin\\beta={fx(s1 * c2)}+{fx(c1 * s2)}={fx(v)}$."])
