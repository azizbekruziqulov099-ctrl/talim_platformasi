"""Matematik statistika — amaliy mashg'ulotlar uchun masala generatorlari (javoblar Python/scipy bilan)."""
from fractions import Fraction as F
from math import sqrt, log
import statistics as stt
from scipy import stats as S
from ehtimol_gen import d, fr, fk, Phi

def _tanlama(r, n=None, lo=1, hi=9):
    n = n or r.randint(8, 12)
    return [r.randint(lo, hi) for _ in range(n)]

def _qator(xs):
    return ", ".join(str(x) for x in xs)

def _var(r):
    xs = sorted(r.sample(range(2, 20, 2), 4)); ns = [r.randint(2, 9) for _ in xs]
    return xs, ns

def _var_matn(xs, ns):
    return "$x_i$: " + "; ".join(map(str, xs)) + " — $n_i$: " + "; ".join(map(str, ns))

def g_chastota(r):
    xs = _tanlama(r, r.randint(12, 20), 1, 6); v = r.choice(sorted(set(xs)))
    k = xs.count(v)
    return dict(matn=f"Tanlanma: {_qator(xs)}. ${v}$ qiymatining nisbiy chastotasini toping.", javob=fr(F(k, len(xs))),
                yechim=f"$n_{{{v}}} = {k}$, $n = {len(xs)}$; $w = \\frac{{{k}}}{{{len(xs)}}} = {d(F(k, len(xs)))}$.", xato=[str(k), d(F(1, len(set(xs)))), d(F(k, len(xs) - k))])

def g_hajm(r):
    xs, ns = _var(r)
    return dict(matn=f"Variatsion qator: {_var_matn(xs, ns)}. Tanlanma hajmini toping.", javob=str(sum(ns)),
                yechim=f"$n = \\sum n_i = {' + '.join(map(str, ns))} = {sum(ns)}$.", xato=[str(len(xs)), str(sum(xs)), str(sum(a * b for a, b in zip(xs, ns)))])

def g_emp_f(r):
    xs, ns = _var(r); x = r.choice(xs[1:]); k = sum(n for a, n in zip(xs, ns) if a < x)
    return dict(matn=f"Variatsion qator: {_var_matn(xs, ns)}. Empirik taqsimot funksiyasi $F^*({x})$ ni toping.", javob=fr(F(k, sum(ns))),
                yechim=f"$F^*(x) = \\frac{{n_x}}{{n}}$, $n_x$ — $x$ dan kichik qiymatlar soni: $\\frac{{{k}}}{{{sum(ns)}}} = {d(F(k, sum(ns)))}$.",
                xato=[d(F(k + ns[xs.index(x)], sum(ns))), d(F(xs.index(x), len(xs))), str(k)])

def g_gist(r):
    h = r.choice([2, 5, 10]); n = r.choice([50, 100, 200]); ni = r.randint(5, 30)
    return dict(matn=f"Gistogramma: interval uzunligi $h = {h}$, tanlanma hajmi $n = {n}$, intervaldagi chastota ${ni}$. Shu interval ustidagi nisbiy chastotalar gistogrammasi to‘g‘ri to‘rtburchagi balandligini toping.",
                javob=d(F(ni, n * h), 3), yechim=f"Balandlik $= \\frac{{w_i}}{{h}} = \\frac{{{ni}/{n}}}{{{h}}} = {d(F(ni, n * h), 3)}$.", xato=[d(F(ni, n), 3), d(F(ni, h), 3), d(F(ni * h, n), 3)])

def g_orta(r):
    xs, ns = _var(r); n = sum(ns); m = F(sum(a * b for a, b in zip(xs, ns)), n)
    return dict(matn=f"Variatsion qator: {_var_matn(xs, ns)}. Tanlanma o‘rta qiymatini toping (0,01 aniqlikda).", javob=d(m, 2),
                yechim=f"$\\bar{{x}} = \\frac{{\\sum x_i n_i}}{{n}} = \\frac{{{sum(a * b for a, b in zip(xs, ns))}}}{{{n}}} = {d(m, 2)}$.", xato=[d(F(sum(xs), len(xs)), 2), d(F(sum(a * b for a, b in zip(xs, ns)), len(xs)), 2), d(m + 1, 2)])

def g_mediana(r):
    xs = _tanlama(r, r.choice([7, 9, 8, 10]), 1, 30)
    md = stt.median(xs)
    return dict(matn=f"Tanlanma: {_qator(xs)}. Medianani toping.", javob=d(md, 1),
                yechim=f"Tartiblaymiz: {_qator(sorted(xs))}. " + ("O‘rtadagi had" if len(xs) % 2 else "O‘rtadagi ikki hadning o‘rtachasi") + f": $Me = {d(md, 1)}$.",
                xato=[d(stt.mean(xs), 1), d(xs[len(xs) // 2], 1) if xs[len(xs) // 2] != md else d(md + 1, 1), d(sorted(xs)[len(xs) // 2 - 1] if len(xs) > 2 else md + 2, 1)])

def g_moda(r):
    xs, ns = _var(r); ns[r.randint(0, 3)] = max(ns) + 2
    return dict(matn=f"Variatsion qator: {_var_matn(xs, ns)}. Modani toping.", javob=str(xs[ns.index(max(ns))]),
                yechim=f"Moda — eng katta chastotali qiymat: $n = {max(ns)}$ ⇒ $Mo = {xs[ns.index(max(ns))]}$.", xato=[str(max(ns)), str(xs[-1]) if xs[-1] != xs[ns.index(max(ns))] else str(xs[0]), str(xs[1]) if xs[1] != xs[ns.index(max(ns))] else str(xs[2])])

def g_dispersiya(r):
    xs = _tanlama(r, r.randint(5, 7), 1, 12); n = len(xs); m = F(sum(xs), n); D = F(sum(x * x for x in xs), n) - m * m
    return dict(matn=f"Tanlanma: {_qator(xs)}. Tanlanma dispersiyasini toping (0,01 aniqlikda).", javob=d(D, 2),
                yechim=f"$\\bar{{x}} = {d(m, 3)}$, $\\overline{{x^2}} = {d(F(sum(x * x for x in xs), n), 3)}$.\n$D_T = \\overline{{x^2}} - \\bar{{x}}^2 = {d(D, 2)}$.", xato=[d(D * n / (n - 1), 2), d(sqrt(float(D)), 2), d(F(sum(x * x for x in xs), n), 2)])

def g_sigma_t(r):
    xs, ns = _var(r); n = sum(ns); m = F(sum(a * b for a, b in zip(xs, ns)), n); D = F(sum(a * a * b for a, b in zip(xs, ns)), n) - m * m
    return dict(matn=f"Variatsion qator: {_var_matn(xs, ns)}. Tanlanma o‘rtacha kvadratik chetlanishini toping (0,01 aniqlikda).", javob=d(sqrt(float(D)), 2),
                yechim=f"$\\bar{{x}} = {d(m, 3)}$; $D_T = {d(D, 3)}$; $\\sigma_T = \\sqrt{{D_T}} = {d(sqrt(float(D)), 2)}$.", xato=[d(D, 2), d(sqrt(float(D) * n / (n - 1)), 2), d(float(D) / 2, 2)])

def g_variatsiya(r):
    m, s = r.choice([(50, 5), (40, 6), (120, 18), (25, 4), (80, 12)])
    return dict(matn=f"Tanlanma o‘rta qiymati ${m}$, o‘rtacha kvadratik chetlanishi ${s}$. Variatsiya koeffitsientini (%) toping.", javob=d(100 * s / m, 1),
                yechim=f"$V = \\frac{{\\sigma}}{{\\bar{{x}}}}\\cdot 100\\% = \\frac{{{s}}}{{{m}}}\\cdot100\\% = {d(100 * s / m, 1)}\\%$.", xato=[d(100 * m / s, 1), d(s / m, 3), d(100 * s * s / m, 1)])

def g_tuzatilgan(r):
    xs = _tanlama(r, r.randint(5, 8), 1, 12); n = len(xs); m = F(sum(xs), n); D = F(sum(x * x for x in xs), n) - m * m; s2 = D * n / (n - 1)
    return dict(matn=f"Tanlanma: {_qator(xs)}. Tuzatilgan dispersiya $s^2$ ni toping (0,01 aniqlikda).", javob=d(s2, 2),
                yechim=f"$D_T = {d(D, 3)}$; $s^2 = \\frac{{n}}{{n-1}}D_T = \\frac{{{n}}}{{{n - 1}}}\\cdot{d(D, 3)} = {d(s2, 2)}$.", xato=[d(D, 2), d(sqrt(float(s2)), 2), d(D * (n - 1) / n, 2)])

def g_tuzatish(r):
    n, D = r.choice([(10, 9), (5, 4), (20, 19), (8, 7), (16, 15)])
    D = F(r.randint(2, 9) * (n - 1), n)
    return dict(matn=f"Hajmi ${n}$ bo‘lgan tanlanma dispersiyasi $D_T = {d(D, 2)}$. Tuzatilgan dispersiyani toping.", javob=d(D * n / (n - 1), 2),
                yechim=f"$s^2 = \\frac{{{n}}}{{{n - 1}}}\\cdot {d(D, 2)} = {d(D * n / (n - 1), 2)}$.", xato=[d(D, 2), d(D * (n - 1) / n, 2), d(D * n, 2)])

def g_momentlar_tekis(r):
    m, D = r.choice([(5, 3), (10, 12), (4, 1.3333333333), (8, 3)])
    b = m + sqrt(3 * D); a = m - sqrt(3 * D)
    return dict(matn=f"Tekis taqsimlangan $X\\in[a;b]$ uchun tanlanma bo‘yicha $\\bar{{x}} = {m}$, $D_T = {d(D, 2)}$. Momentlar usuli bilan $b$ ni baholang (0,01 aniqlikda).", javob=d(b, 2),
                yechim=f"$M = \\frac{{a+b}}{{2}}$, $D = \\frac{{(b-a)^2}}{{12}}$ ⇒ $b = \\bar{{x}} + \\sqrt{{3D_T}} = {m} + \\sqrt{{{d(3 * D, 2)}}} = {d(b, 2)}$.", xato=[d(a, 2), d(m + sqrt(D), 2), d(2 * m, 2)])

def g_momentlar_puasson(r):
    xs, ns = _var(r); n = sum(ns); m = F(sum(a * b for a, b in zip(xs, ns)), n)
    return dict(matn=f"Puasson taqsimotidan olingan tanlanma: {_var_matn(xs, ns)}. Momentlar usuli bilan $\\lambda$ ni baholang (0,01 aniqlikda).", javob=d(m, 2),
                yechim=f"Puasson taqsimotida $M(X) = \\lambda$ ⇒ $\\lambda^* = \\bar{{x}} = {d(m, 2)}$.", xato=[d(F(sum(xs), len(xs)), 2), d(1 / m if m else 0, 2), d(m * m, 2)])

def g_hmo_korsatkichli(r):
    xs = [r.choice([0.5, 1, 1.5, 2, 2.5, 3, 4]) for _ in range(r.randint(5, 8))]
    m = sum(xs) / len(xs)
    return dict(matn=f"Ko‘rsatkichli taqsimotdan tanlanma: {', '.join(d(x, 1) for x in xs)}. Haqiqatga maksimal o‘xshashlik usuli bilan $\\lambda$ ni baholang (0,001 aniqlikda).", javob=d(1 / m, 3),
                yechim=f"$L(\\lambda) = \\lambda^n e^{{-\\lambda\\sum x_i}}$; $\\frac{{d\\ln L}}{{d\\lambda}} = \\frac{{n}}{{\\lambda}} - \\sum x_i = 0$ ⇒ $\\lambda^* = \\frac{{1}}{{\\bar{{x}}}} = \\frac{{1}}{{{d(m, 3)}}} = {d(1 / m, 3)}$.", xato=[d(m, 3), d(1 / sum(xs), 3), d(len(xs) / (sum(xs) + 1), 3)])

def g_hmo_bernulli(r):
    n, k = r.choice([20, 40, 50, 80, 100]), None; k = r.randint(n // 10, n // 2)
    return dict(matn=f"{n} ta bog‘liqsiz tajribada hodisa {k} marta ro‘y berdi. Haqiqatga maksimal o‘xshashlik usuli bilan $p$ ni baholang.", javob=fr(F(k, n)),
                yechim=f"$L(p) = p^k(1-p)^{{n-k}}$ ⇒ $p^* = \\frac{{k}}{{n}} = \\frac{{{k}}}{{{n}}} = {d(F(k, n))}$.", xato=[d(F(n - k, n)), d(F(k, n - k)), d(F(1, 2))])

def g_ishonch_sigma(r):
    n, s, m, g = r.choice([25, 36, 49, 64, 100]), r.choice([2, 3, 4, 5, 6]), r.randint(20, 80), r.choice([0.95, 0.99, 0.9])
    t = S.norm.ppf((1 + g) / 2); dl = t * s / sqrt(n)
    return dict(matn=f"Normal bosh to‘plamda $\\sigma = {s}$. Hajmi $n = {n}$ tanlanma bo‘yicha $\\bar{{x}} = {m}$. Bosh o‘rta qiymat uchun ishonchlilik $\\gamma = {d(g, 2)}$ bo‘lgan ishonch oralig‘ining yuqori chegarasini toping (0,01 aniqlikda).",
                javob=d(m + dl, 2), yechim=f"$\\Phi(t) = \\frac{{\\gamma}}{{2}} = {d(g / 2, 3)}$ ⇒ $t = {d(t, 2)}$. Aniqlik $\\delta = t\\frac{{\\sigma}}{{\\sqrt{{n}}}} = {d(t, 2)}\\cdot\\frac{{{s}}}{{{d(sqrt(n), 0)}}} = {d(dl, 3)}$.\nOraliq: $({d(m - dl, 2)};\\ {d(m + dl, 2)})$.",
                xato=[d(m - dl, 2), d(m + t * s / n, 2), d(m + t * s, 2)])

def g_ishonch_t(r):
    n, s, m, g = r.choice([9, 16, 25, 10, 12]), r.choice([1.5, 2, 3, 4]), r.randint(10, 60), r.choice([0.95, 0.99])
    t = S.t.ppf((1 + g) / 2, n - 1); dl = t * s / sqrt(n)
    return dict(matn=f"Normal bosh to‘plamdan hajmi $n = {n}$ tanlanma: $\\bar{{x}} = {m}$, $s = {d(s, 1)}$ ($\\sigma$ noma’lum). $\\gamma = {d(g, 2)}$ ishonchlilik bilan oraliqning aniqligi $\\delta$ ni toping (0,01 aniqlikda).",
                javob=d(dl, 2), yechim=f"Styudent taqsimoti, $k = n - 1 = {n - 1}$: $t_\\gamma = {d(t, 3)}$.\n$\\delta = t_\\gamma\\frac{{s}}{{\\sqrt{{n}}}} = {d(t, 3)}\\cdot\\frac{{{d(s, 1)}}}{{{d(sqrt(n), 3)}}} = {d(dl, 2)}$.",
                xato=[d(S.norm.ppf((1 + g) / 2) * s / sqrt(n), 2), d(t * s / n, 2), d(t * s, 2)])

def g_ishonch_ulush(r):
    n, k, g = r.choice([100, 200, 400, 500]), None, 0.95; k = r.randint(n // 10, n // 2)
    w = k / n; t = S.norm.ppf(0.975); dl = t * sqrt(w * (1 - w) / n)
    return dict(matn=f"{n} ta tekshirilgan mahsulotdan {k} tasi oliy navli. Oliy nav ulushi uchun 95% ishonch oralig‘ining quyi chegarasini toping (0,001 aniqlikda).", javob=d(w - dl, 3),
                yechim=f"$w = {d(w, 3)}$, $t = 1,96$. $\\delta = t\\sqrt{{\\frac{{w(1-w)}}{{n}}}} = {d(dl, 4)}$.\nOraliq: $({d(w - dl, 3)};\\ {d(w + dl, 3)})$.", xato=[d(w + dl, 3), d(w - t * w / sqrt(n), 3), d(w, 3)])

def g_tanlanma_hajmi(r):
    s, dl, g = r.choice([2, 3, 4, 5, 10]), r.choice([0.5, 1, 2]), r.choice([0.95, 0.99])
    t = S.norm.ppf((1 + g) / 2); n = int(-(-(t * s / dl) ** 2 // 1))
    from math import ceil
    n = ceil((t * s / dl) ** 2)
    return dict(matn=f"$\\sigma = {s}$. O‘rta qiymatni $\\delta = {d(dl, 1)}$ aniqlik va $\\gamma = {d(g, 2)}$ ishonchlilik bilan baholash uchun eng kichik tanlanma hajmini toping.", javob=str(n),
                yechim=f"$n \\ge \\frac{{t^2\\sigma^2}}{{\\delta^2}} = \\frac{{{d(t, 2)}^2\\cdot{s}^2}}{{{d(dl, 1)}^2}} = {d((t * s / dl) ** 2, 2)}$ ⇒ $n = {n}$.", xato=[str(n - 1), str(ceil(t * s / dl)), str(ceil(t * t * s / dl))])

def g_z_test(r):
    a0, s, n = r.randint(40, 100), r.choice([4, 5, 6, 8, 10]), r.choice([25, 36, 49, 64, 100]); al = r.choice([0.05, 0.01])
    m = a0 + r.choice([-1, 1]) * r.choice([0.5, 1, 1.5, 2, 3]) * s / sqrt(n)
    z = (m - a0) / (s / sqrt(n)); zk = S.norm.ppf(1 - al / 2); rad = abs(z) > zk
    return dict(matn=f"$H_0: a = {a0}$, $H_1: a \\ne {a0}$. $\\sigma = {s}$, $n = {n}$, $\\bar{{x}} = {d(m, 2)}$, $\\alpha = {d(al, 2)}$. Kuzatilgan $z$ statistikasini toping (0,01 aniqlikda).",
                javob=d(z, 2), yechim=f"$z = \\frac{{\\bar{{x}} - a_0}}{{\\sigma/\\sqrt{{n}}}} = \\frac{{{d(m, 2)} - {a0}}}{{{s}/{d(sqrt(n), 0)}}} = {d(z, 2)}$.\n$z_{{kr}} = {d(zk, 2)}$ ⇒ $H_0$ {'rad etiladi' if rad else 'rad etilmaydi'}.",
                xato=[d((m - a0) / s, 2), d((m - a0) * sqrt(n) / s / 2, 2), d(-z, 2)])

def g_z_qaror(r):
    z = r.choice([1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.1, -2.2, -1.4]); al = r.choice([0.05, 0.01])
    zk = S.norm.ppf(1 - al / 2); rad = abs(z) > zk
    return dict(matn=f"Ikki tomonlama kriteriy: kuzatilgan $z = {d(z, 1)}$, $\\alpha = {d(al, 2)}$. Asosiy gipoteza rad etiladimi? (1 — ha, 0 — yo‘q)", javob="1" if rad else "0",
                yechim=f"$z_{{kr}} = {d(zk, 2)}$. $|z| = {d(abs(z), 1)}$ {'>' if rad else '≤'} $z_{{kr}}$ ⇒ $H_0$ {'rad etiladi' if rad else 'qabul qilinadi'}.", xato=["0" if rad else "1"])

def g_t_test(r):
    a0, n = r.randint(10, 50), r.choice([9, 16, 25, 12]); s = r.choice([2, 3, 4]); m = a0 + r.choice([-1, 1]) * r.choice([1, 1.5, 2, 3]) * s / sqrt(n)
    t = (m - a0) / (s / sqrt(n))
    return dict(matn=f"$H_0: a = {a0}$. Normal to‘plamdan $n = {n}$ tanlanma: $\\bar{{x}} = {d(m, 2)}$, $s = {s}$. Styudent statistikasi $T$ ni toping (0,01 aniqlikda).", javob=d(t, 2),
                yechim=f"$T = \\frac{{\\bar{{x}} - a_0}}{{s/\\sqrt{{n}}}} = {d(t, 2)}$; ozodlik darajasi $k = {n - 1}$, $t_{{kr}}(0,05) = {d(S.t.ppf(0.975, n - 1), 2)}$.", xato=[d((m - a0) / s, 2), d((m - a0) * n / s, 2), d(-t, 2)])

def g_ikki_orta(r):
    m1, m2 = r.randint(60, 80), r.randint(60, 80); s1, s2 = r.choice([5, 6, 8]), r.choice([4, 6, 10]); n1, n2 = r.choice([40, 50, 64]), r.choice([36, 50, 100])
    z = (m1 - m2) / sqrt(s1 ** 2 / n1 + s2 ** 2 / n2)
    return dict(matn=f"Ikki guruh: $\\bar{{x}} = {m1}$, $\\sigma_1 = {s1}$, $n_1 = {n1}$; $\\bar{{y}} = {m2}$, $\\sigma_2 = {s2}$, $n_2 = {n2}$. O‘rta qiymatlar tengligini tekshirish uchun $z$ ni toping (0,01 aniqlikda).", javob=d(z, 2),
                yechim=f"$z = \\frac{{\\bar{{x}} - \\bar{{y}}}}{{\\sqrt{{\\sigma_1^2/n_1 + \\sigma_2^2/n_2}}}} = \\frac{{{m1 - m2}}}{{{d(sqrt(s1 ** 2 / n1 + s2 ** 2 / n2), 4)}}} = {d(z, 2)}$.",
                xato=[d((m1 - m2) / sqrt(s1 ** 2 + s2 ** 2), 2), d((m1 - m2) / (s1 / sqrt(n1) + s2 / sqrt(n2)), 2), d(-z, 2) if z else "1"])

def g_fisher(r):
    s1, s2 = r.choice([12, 15, 20, 9.5]), r.choice([5, 6, 8, 4]); n1, n2 = r.choice([10, 13, 16]), r.choice([9, 11, 15])
    Fv = max(s1, s2) / min(s1, s2)
    return dict(matn=f"Ikki normal to‘plamdan: $s_1^2 = {d(s1, 1)}$ ($n_1 = {n1}$), $s_2^2 = {d(s2, 1)}$ ($n_2 = {n2}$). Fisher kriteriysining kuzatilgan qiymatini toping (0,01 aniqlikda).", javob=d(Fv, 2),
                yechim=f"$F = \\frac{{s_{{katta}}^2}}{{s_{{kichik}}^2}} = \\frac{{{d(max(s1, s2), 1)}}}{{{d(min(s1, s2), 1)}}} = {d(Fv, 2)}$; $F_{{kr}}(0,05;\\ {n1 - 1};\\ {n2 - 1}) = {d(S.f.ppf(0.95, n1 - 1 if s1 >= s2 else n2 - 1, n2 - 1 if s1 >= s2 else n1 - 1), 2)}$.",
                xato=[d(min(s1, s2) / max(s1, s2), 2), d(sqrt(Fv), 2), d(max(s1, s2) - min(s1, s2), 2)])

def g_ulush_test(r):
    p0, n = r.choice([0.5, 0.2, 0.1, 0.3]), r.choice([100, 200, 400]); k = int(n * (p0 + r.choice([-0.06, 0.05, 0.08, -0.03])))
    w = k / n; z = (w - p0) / sqrt(p0 * (1 - p0) / n)
    return dict(matn=f"$H_0: p = {d(p0, 1)}$. {n} ta tajribada hodisa {k} marta ro‘y berdi. Kuzatilgan $z$ ni toping (0,01 aniqlikda).", javob=d(z, 2),
                yechim=f"$w = {d(w, 3)}$; $z = \\frac{{w - p_0}}{{\\sqrt{{p_0q_0/n}}}} = \\frac{{{d(w - p0, 3)}}}{{{d(sqrt(p0 * (1 - p0) / n), 4)}}} = {d(z, 2)}$.", xato=[d((w - p0) / sqrt(w * (1 - w)), 2), d((w - p0) * n, 2), d(-z, 2)])

def g_xi2(r):
    k = r.choice([3, 4, 6]); n = r.choice([60, 120, 90, 120]) if k != 4 else 80
    e = n / k; obs = [int(e + r.randint(-6, 6)) for _ in range(k - 1)]; obs.append(n - sum(obs))
    x2 = sum((o - e) ** 2 / e for o in obs)
    return dict(matn=f"Kub {n} marta tashlanganda (teng ehtimollik gipotezasi, {k} ta guruh) kuzatilgan chastotalar: {'; '.join(map(str, obs))}. $\\chi^2_{{kuz}}$ ni toping (0,01 aniqlikda)." if k == 6 else
                f"{k} ta guruhga teng taqsimot gipotezasi. $n = {n}$, kuzatilgan chastotalar: {'; '.join(map(str, obs))}. $\\chi^2_{{kuz}}$ ni toping (0,01 aniqlikda).", javob=d(x2, 2),
                yechim=f"Nazariy chastota $n p_i = {d(e, 1)}$.\n$\\chi^2 = \\sum\\frac{{(n_i - np_i)^2}}{{np_i}} = {d(x2, 2)}$; $\\chi^2_{{kr}}(0,05;\\ {k - 1}) = {d(S.chi2.ppf(0.95, k - 1), 2)}$.",
                xato=[d(sum((o - e) ** 2 for o in obs) / n, 2), d(sum(abs(o - e) for o in obs) / e, 2), d(x2 / k, 2)])

def g_xi2_kr(r):
    k, al = r.randint(2, 8), r.choice([0.05, 0.01])
    v = S.chi2.ppf(1 - al, k)
    return dict(matn=f"Ozodlik darajasi $k = {k}$, ahamiyatlilik $\\alpha = {d(al, 2)}$ uchun $\\chi^2$ ning kritik nuqtasini toping (0,01 aniqlikda).", javob=d(v, 2),
                yechim=f"Jadvaldan: $\\chi^2_{{kr}}({d(al, 2)};\\ {k}) = {d(v, 2)}$.", xato=[d(S.chi2.ppf(1 - al, k + 1), 2), d(S.chi2.ppf(al, k), 2), d(S.chi2.ppf(1 - al / 2, k), 2)])

def g_mustaqillik(r):
    a, b, c, e = [r.randint(10, 50) for _ in range(4)]; n = a + b + c + e
    x2 = n * (a * e - b * c) ** 2 / ((a + b) * (c + e) * (a + c) * (b + e))
    return dict(matn=f"2×2 jadval: | {a} | {b} | / | {c} | {e} |. Belgilar mustaqilligini tekshirish uchun $\\chi^2$ ni toping (0,01 aniqlikda).", javob=d(x2, 2),
                yechim=f"$\\chi^2 = \\frac{{n(ad - bc)^2}}{{(a+b)(c+d)(a+c)(b+d)}} = \\frac{{{n}\\cdot({a * e - b * c})^2}}{{{(a + b) * (c + e) * (a + c) * (b + e)}}} = {d(x2, 2)}$; $\\chi^2_{{kr}}(0,05;1) = 3,84$.",
                xato=[d(x2 / n, 4), d((a * e - b * c) ** 2 / n, 2), d(sqrt(x2), 2)])

def _juftlar(r, n=None):
    n = n or r.randint(5, 7); k = r.choice([2, 1.5, -1, 3, 0.5]); b = r.randint(1, 10)
    xs = sorted(r.sample(range(1, 15), n)); ys = [round(k * x + b + r.randint(-2, 2)) for x in xs]
    return xs, ys

def g_korrelyatsiya(r):
    xs, ys = _juftlar(r); n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys)); sx = sqrt(sum((x - mx) ** 2 for x in xs)); sy = sqrt(sum((y - my) ** 2 for y in ys))
    rr = sxy / (sx * sy)
    return dict(matn=f"Juftliklar $(x;y)$: " + "; ".join(f"({x};{y})" for x, y in zip(xs, ys)) + ". Tanlanma korrelyatsiya koeffitsientini toping (0,01 aniqlikda).", javob=d(rr, 2),
                yechim=f"$\\bar{{x}} = {d(mx, 3)}$, $\\bar{{y}} = {d(my, 3)}$.\n$r = \\frac{{\\sum(x-\\bar{{x}})(y-\\bar{{y}})}}{{\\sqrt{{\\sum(x-\\bar{{x}})^2\\sum(y-\\bar{{y}})^2}}}} = \\frac{{{d(sxy, 3)}}}{{{d(sx * sy, 3)}}} = {d(rr, 2)}$.",
                xato=[d(rr * rr, 2), d(-rr, 2), d(sxy / (sx * sx), 2)])

def g_regressiya(r):
    xs, ys = _juftlar(r); n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    b1 = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs); b0 = my - b1 * mx
    return dict(matn=f"Juftliklar: " + "; ".join(f"({x};{y})" for x, y in zip(xs, ys)) + ". $y$ ning $x$ ga chiziqli regressiyasi $y = kx + b$ da $k$ ni toping (0,01 aniqlikda).", javob=d(b1, 2),
                yechim=f"Eng kichik kvadratlar usuli: $k = \\frac{{\\sum(x-\\bar{{x}})(y-\\bar{{y}})}}{{\\sum(x-\\bar{{x}})^2}} = {d(b1, 2)}$; $b = \\bar{{y}} - k\\bar{{x}} = {d(b0, 2)}$.",
                xato=[d(b0, 2), d(1 / b1 if b1 else 0, 2), d(my / mx, 2)])

def g_regressiya_bashorat(r):
    k, b, x = r.choice([1.5, 2, -0.5, 3, 0.8]), r.randint(-5, 10), r.randint(2, 12)
    return dict(matn=f"Regressiya tenglamasi $\\hat{{y}} = {d(k, 1)}x {'+' if b >= 0 else '-'} {abs(b)}$. $x = {x}$ da $y$ ning bashorat qiymatini toping.", javob=d(k * x + b, 1),
                yechim=f"$\\hat{{y}} = {d(k, 1)}\\cdot{x} {'+' if b >= 0 else '-'} {abs(b)} = {d(k * x + b, 1)}$.", xato=[d(k * x, 1), d(k + b * x, 1), d(k * x - b, 1)])
