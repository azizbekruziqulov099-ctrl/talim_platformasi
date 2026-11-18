"""MOCK imtihon generatori: yordamchi funksiyalar. Shablon — (rng) -> savol; javob va yechim kod bilan HISOBLANADI (qo'lda yozilmaydi)."""
import math
import random
from fractions import Fraction

SHABLON = {}   # slot -> [funksiya, ...]


def _yechim_format(nom, q):
    """Yechimni o'quvchiga tushunarli ko'rinishga keltiradi: Formula → qadamlar → Javob."""
    from modules.mock_formula import F
    qad = [x for x in q["yechim"].split("\n") if x.strip()]
    chiq = []
    if nom in F:
        chiq.append("📐 Formula: " + F[nom])
    ochiq = q.get("tur") == "ochiq"
    k = 0
    for x in qad:
        if ochiq and x[:2] in ("a)", "b)"):
            chiq.append(x)
        else:
            k += 1
            chiq.append(f"{k}-qadam. {x}")
    if ochiq:
        chiq.append("✅ Javob: " + "; ".join(f"{z['h']}) ${z['javob']}$" for z in q["qismlar"]))
    else:
        j = q["javob"]
        chiq.append(f"✅ Javob: {j}) " + q["variantlar"]["ABCD".index(j)])
    return "\n".join(chiq)


def shablon(slot, nom=""):
    def d(f):
        import functools
        from modules import mock_fig

        @functools.wraps(f)
        def w(rng):
            mock_fig.olish()
            q = f(rng)
            r = mock_fig.olish()
            q = dict(q)
            if r:
                q["rasm"] = r
            q["yechim"] = _yechim_format(f.__name__, q)
            return q
        w.slot, w.nom = slot, nom or f.__name__
        SHABLON.setdefault(slot, []).append(w)
        return w
    return d


def xa(a):
    """x − a ko'rinishi: 'x-3', 'x+3', 'x'."""
    return "x" if a == 0 else f"x{-a:+d}"


def sg(n):
    """+5 / −5 (LaTeX)."""
    return f"{n:+d}"


def norm(v):
    """sympy/son → Fraction yoki ($siz) LaTeX matn."""
    import sympy as _sp
    if isinstance(v, (int, Fraction)):
        return Fraction(v)
    v = _sp.nsimplify(v) if not isinstance(v, _sp.Basic) else v
    if getattr(v, "is_Rational", False):
        return Fraction(int(v.p), int(v.q))
    return _sp.latex(v)


def fx(v):
    """Son/kasr → LaTeX (matn, $siz)."""
    if isinstance(v, str):
        return v
    v = Fraction(v)
    if v.denominator == 1:
        return str(v.numerator)
    s = "-" if v < 0 else ""
    return f"{s}\\frac{{{abs(v.numerator)}}}{{{v.denominator}}}"


def M(v):
    """$…$ ichida."""
    return f"${fx(v)}$"


def _yaqin(v, rng):
    """Taxminiy noto'g'ri variantlar (tipik xatolar)."""
    out = []
    if isinstance(v, str):
        return out
    v = Fraction(v)
    if v.denominator == 1:
        n = v.numerator
        for d in (1, -1, 2, -2, 3, -3, 5, 10, -10):
            out.append(Fraction(n + d))
        out += [Fraction(-n), Fraction(2 * n), Fraction(n * 2 + 1)]
        if n % 2 == 0:
            out.append(Fraction(n // 2))
    else:
        p, q = v.numerator, v.denominator
        out += [Fraction(q, p) if p else Fraction(1), -v, Fraction(p + 1, q), Fraction(p - 1, q), Fraction(p, q + 1), Fraction(p, max(1, q - 1)), v + 1, v - 1, 2 * v, v / 2]
    rng.shuffle(out)
    return out


def yopiq(rng, savol, togri, yech, noto=(), tartib=True):
    """4 variantli yopiq savol. togri/noto — son, Fraction yoki matn. Variantlar o'sish tartibida (son bo'lsa)."""
    togri_f = fx(togri)
    ruy, korildi = [], {togri_f}
    ya = _yaqin(togri, rng)
    if not isinstance(togri, str) and Fraction(togri) >= 0:
        ya = [x for x in ya if Fraction(x) >= 0]      # musbat javob uchun manfiy variant bermaymiz
    for x in list(noto) + ya:
        if not isinstance(x, str) and Fraction(x) < 0 and not isinstance(togri, str) and Fraction(togri) >= 0:
            continue
        s = fx(x)
        if s not in korildi:
            ruy.append(x); korildi.add(s)
        if len(ruy) == 3:
            break
    if len(ruy) < 3:
        raise ValueError("variant yetmadi")
    hamma = [togri] + ruy
    if tartib and all(not isinstance(x, str) for x in hamma):
        hamma.sort(key=lambda x: Fraction(x))
    else:
        rng.shuffle(hamma)
    return {"tur": "yopiq", "savol": savol, "variantlar": [M(x) if not isinstance(x, str) or not x.startswith("$") else x for x in hamma],
            "javob": "ABCD"[[fx(x) for x in hamma].index(togri_f)], "yechim": yech if isinstance(yech, str) else "\n".join(yech)}


def ochiq(umumiy, qismlar, yech):
    """qismlar: [(savol_a, javob_a), (savol_b, javob_b)] — javob: son/Fraction/matn."""
    return {"tur": "ochiq", "savol": umumiy, "qismlar": [{"h": "ab"[i], "savol": s, "javob": fx(j), "son": str(Fraction(j))} for i, (s, j) in enumerate(qismlar)],
            "yechim": yech if isinstance(yech, str) else "\n".join(yech)}


def tub(n):
    if n < 2:
        return False
    return all(n % i for i in range(2, int(n ** 0.5) + 1))


def kasr_son(rng, lo=1, hi=9):
    return Fraction(rng.randint(lo, hi), rng.randint(2, 9))


def tomon_pifagor(rng):
    """Pifagor uchliklari (a,b,c)."""
    t = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (20, 21, 29), (9, 40, 41), (6, 8, 10), (9, 12, 15), (12, 16, 20), (15, 20, 25)]
    a, b, c = rng.choice(t)
    k = rng.choice([1, 1, 2])
    a, b, c = a * k, b * k, c * k
    return (a, b, c) if rng.random() < .5 else (b, a, c)
