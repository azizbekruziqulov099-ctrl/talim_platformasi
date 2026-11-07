"""Ehtimollar nazariyasi — amaliy mashg'ulotlar uchun masala generatorlari.
Har generator: rng → dict(matn, javob, yechim, xato[]) — javob Python bilan aniq hisoblanadi.
Javob ko'rinishi: kasr bo'lsa «a/b|0,xxx» (ikkalasi ham qabul qilinadi), aks holda son."""
from fractions import Fraction as F
from math import comb, perm, factorial, exp, sqrt, erf, pi
import random

def d(x, k=3):
    """Son → o'zbekcha yozuv (vergul bilan), k xona."""
    if isinstance(x, F): x = float(x)
    s = f"{x:.{k}f}".rstrip("0").rstrip(".") if abs(x - round(x)) > 1e-12 else str(int(round(x)))
    return s.replace(".", ",")

def fr(x):
    """Kasr javob: «3/8|0,375»."""
    x = F(x).limit_denominator(100000)
    if x.denominator == 1: return str(x.numerator)
    return f"{x.numerator}/{x.denominator}|{d(x, 3)}"

def fk(x):
    x = F(x).limit_denominator(100000)
    return str(x.numerator) if x.denominator == 1 else f"\\frac{{{x.numerator}}}{{{x.denominator}}}"

def Phi(x):   # Laplas funksiyasi Φ(x) = (1/√(2π))∫₀ˣ e^{-t²/2}dt
    return 0.5 * erf(x / sqrt(2))

def phi(x):
    return exp(-x * x / 2) / sqrt(2 * pi)

def xato_son(qiymat, *boshqa, k=3):
    """Noto'g'ri variantlar: berilgan xato hisoblar (takrorsiz, to'g'ridan farqli)."""
    out, t = [], d(qiymat, k)
    for b in boshqa:
        s = d(b, k) if not isinstance(b, str) else b
        if s != t and s not in out: out.append(s)
    return out

# ─────────────────────────── KOMBINATORIKA ───────────────────────────
def g_orin_almashtirish(r):
    n = r.randint(4, 7); nom = r.choice(["kitobni javonga", "talabani qatorga", "rangli bayroqni ustunga", "o‘quvchini navbatga"])
    v = factorial(n)
    return dict(matn=f"{n} ta {nom} necha xil usulda terish mumkin?", javob=str(v),
                yechim=f"Hammasi o‘rin almashadi: $P_{n} = {n}! = {v}$.", xato=[str(n * n), str(factorial(n - 1)), str(2 ** n)])

def g_orinlashtirish(r):
    n, k = r.randint(6, 10), r.randint(2, 4)
    v = perm(n, k)
    lav = ["sardor", "o‘rinbosar", "kotib", "g‘aznachi"][:k]
    return dict(matn=f"{n} ta nomzoddan {', '.join(lav[:-1])} va {lav[-1]} — jami {k} ta turli lavozimga necha xil usulda saylash mumkin?",
                javob=str(v), yechim=f"Tartib muhim, takror yo‘q: $A_{{{n}}}^{{{k}}} = \\frac{{{n}!}}{{{n - k}!}} = {v}$.", xato=[str(comb(n, k)), str(n ** k), str(n * k)])

def g_kombinatsiya(r):
    n, k = r.randint(7, 15), r.randint(2, 5)
    v = comb(n, k)
    return dict(matn=f"Guruhdagi {n} talabadan konferensiyaga {k} kishini necha xil usulda tanlash mumkin?",
                javob=str(v), yechim=f"Tartib muhim emas: $C_{{{n}}}^{{{k}}} = \\frac{{{n}!}}{{{k}!\\,{n - k}!}} = {v}$.", xato=[str(perm(n, k)), str(comb(n, k - 1)), str(n * k)])

def g_takrorli(r):
    n, k = r.choice([(10, 4), (10, 3), (5, 3), (6, 4), (2, 8)])
    v = n ** k
    return dict(matn=f"{n} xil raqam/belgidan foydalanib (takrorlanishi mumkin) uzunligi {k} bo‘lgan nechta kod tuzish mumkin?",
                javob=str(v), yechim=f"Har o‘ringa {n} xil tanlov: ${n}^{{{k}}} = {v}$.", xato=[str(perm(n, k)) if n >= k else str(n * k), str(comb(n + k - 1, k)), str(n * k)])

def g_kombinatsiya_ikki(r):
    a, b, ka, kb = r.randint(5, 9), r.randint(4, 8), 2, r.randint(1, 3)
    v = comb(a, ka) * comb(b, kb)
    return dict(matn=f"{a} yigit va {b} qizdan {ka} yigit va {kb} qizdan iborat guruhni necha usulda tuzish mumkin?",
                javob=str(v), yechim=f"Ko‘paytirish qoidasi: $C_{{{a}}}^{{{ka}}}\\cdot C_{{{b}}}^{{{kb}}} = {comb(a, ka)}\\cdot{comb(b, kb)} = {v}$.",
                xato=[str(comb(a, ka) + comb(b, kb)), str(comb(a + b, ka + kb)), str(perm(a, ka) * perm(b, kb))])

# ─────────────────────────── KLASSIK EHTIMOL ───────────────────────────
def g_kub_yigindi(r):
    s = r.randint(4, 10)
    m = sum(1 for i in range(1, 7) for j in range(1, 7) if i + j == s)
    p = F(m, 36)
    return dict(matn=f"Ikkita o‘yin kubigi tashlandi. Tushgan ochkolar yig‘indisi {s} ga teng bo‘lish ehtimolini toping.",
                javob=fr(p), yechim=f"Jami teng imkoniyatli natijalar $6\\cdot 6 = 36$. Yig‘indi {s} bo‘ladigan juftlar soni $m = {m}$.\n$P = \\frac{{{m}}}{{36}} = {fk(p)}$.",
                xato=[d(F(m, 12)), d(F(1, 11)), d(F(m + 1, 36))])

def g_tanga(r):
    n = r.randint(3, 5); k = r.randint(1, n - 1)
    p = F(comb(n, k), 2 ** n)
    return dict(matn=f"Tanga {n} marta tashlandi. Gerb roppa-rosa {k} marta tushish ehtimolini toping.",
                javob=fr(p), yechim=f"Jami natijalar $2^{n} = {2 ** n}$. Gerb {k} marta: $C_{n}^{k} = {comb(n, k)}$ ta.\n$P = {fk(p)}$.",
                xato=[d(F(k, n)), d(F(1, 2 ** n)), d(F(comb(n, k), 2 * n))])

def g_idish(r):
    w, b = r.randint(4, 9), r.randint(3, 7); k = r.choice([2, 3]); kw = r.randint(1, k)
    p = F(comb(w, kw) * comb(b, k - kw), comb(w + b, k))
    return dict(matn=f"Idishda {w} ta oq va {b} ta qora shar bor. Tavakkaliga {k} ta shar olindi. Ulardan roppa-rosa {kw} tasi oq bo‘lish ehtimolini toping.",
                javob=fr(p), yechim=f"$n = C_{{{w + b}}}^{{{k}}} = {comb(w + b, k)}$, $m = C_{{{w}}}^{{{kw}}}\\cdot C_{{{b}}}^{{{k - kw}}} = {comb(w, kw) * comb(b, k - kw)}$.\n$P = \\frac{{m}}{{n}} = {fk(p)}$.",
                xato=[d(F(w, w + b) ** kw), d(F(comb(w, kw), comb(w + b, k))), d(F(kw, k))])

def g_detal(r):
    n, br, k = r.randint(10, 20), r.randint(2, 4), r.choice([2, 3])
    p = F(comb(n - br, k), comb(n, k))
    return dict(matn=f"Partiyadagi {n} ta detaldan {br} tasi yaroqsiz. Tavakkaliga {k} ta detal olinganda hammasi yaroqli bo‘lish ehtimolini toping.",
                javob=fr(p), yechim=f"$P = \\frac{{C_{{{n - br}}}^{{{k}}}}}{{C_{{{n}}}^{{{k}}}}} = \\frac{{{comb(n - br, k)}}}{{{comb(n, k)}}} = {fk(p)}$.",
                xato=[d(F(n - br, n) ** k), d(1 - p), d(F(n - br - k, n))])

def g_geometrik(r):
    R, a = r.randint(5, 10), r.randint(2, 4)
    p = F(a * a, R * R)
    return dict(matn=f"Radiusi {R} sm bo‘lgan doira ichiga tavakkaliga nuqta tashlandi. Nuqta radiusi {a} sm bo‘lgan konsentrik doira ichiga tushish ehtimolini toping.",
                javob=fr(p), yechim=f"Geometrik ehtimol — yuzalar nisbati: $P = \\frac{{\\pi\\cdot {a}^2}}{{\\pi\\cdot {R}^2}} = {fk(p)}$.",
                xato=[d(F(a, R)), d(F(2 * a, R * R)), d(F(a * a, R))])

def g_kesma(r):
    L, a, b = r.randint(10, 20), None, None
    a = r.randint(1, L // 2); b = r.randint(a + 2, L - 1)
    p = F(b - a, L)
    return dict(matn=f"Uzunligi {L} sm bo‘lgan $[0;{L}]$ kesmaga tavakkaliga nuqta tashlandi. Nuqta $[{a};{b}]$ oraliqqa tushish ehtimolini toping.",
                javob=fr(p), yechim=f"$P = \\frac{{{b} - {a}}}{{{L}}} = {fk(p)}$.", xato=[d(F(b, L)), d(F(a, L)), d(F(b - a, L + 1))])

def g_statistik(r):
    n, m = r.choice([200, 400, 500, 1000]), None
    m = r.randint(n // 20, n // 5)
    w = F(m, n)
    return dict(matn=f"Tekshirilgan {n} ta mahsulotdan {m} tasida nuqson topildi. Nuqsonli mahsulot chiqishining nisbiy chastotasini (statistik ehtimolini) toping.",
                javob=fr(w), yechim=f"$W = \\frac{{m}}{{n}} = \\frac{{{m}}}{{{n}}} = {d(w)}$.", xato=[d(F(n - m, n)), d(F(m, n - m)), d(F(m, 100))])

# ─────────────────────────── TEOREMALAR ───────────────────────────
def g_qoshish(r):
    a, b = r.randint(2, 6), r.randint(2, 6); c = r.randint(3, 8); n = a + b + c
    p = F(a + b, n)
    return dict(matn=f"Qutida {a} ta qizil, {b} ta ko‘k va {c} ta yashil qalam bor. Tavakkaliga olingan qalam rangli (qizil yoki ko‘k) bo‘lish ehtimolini toping.",
                javob=fr(p), yechim=f"Hodisalar birgalikda emas: $P(A+B) = P(A)+P(B) = \\frac{{{a}}}{{{n}}} + \\frac{{{b}}}{{{n}}} = {fk(p)}$.",
                xato=[d(F(a * b, n * n)), d(F(c, n)), d(F(a, n))])

def g_qarama(r):
    p = r.choice([F(1, 4), F(1, 5), F(3, 10), F(2, 5)])
    return dict(matn=f"Hodisaning ro‘y berish ehtimoli ${fk(p)}$ ga teng. Unga qarama-qarshi hodisaning ehtimolini toping.",
                javob=fr(1 - p), yechim=f"$P(\\bar{{A}}) = 1 - P(A) = 1 - {fk(p)} = {fk(1 - p)}$.", xato=[d(p), d(1 / p if p else 0), d(1 - p * p)])

def g_birgalikda(r):
    pa, pb, pab = F(r.randint(3, 6), 10), F(r.randint(2, 5), 10), None
    pab = F(r.randint(1, 2), 10)
    if pab > min(pa, pb): pab = min(pa, pb) - F(1, 10)
    v = pa + pb - pab
    return dict(matn=f"$P(A) = {d(pa, 1)}$, $P(B) = {d(pb, 1)}$, $P(AB) = {d(pab, 1)}$. $P(A+B)$ ni toping.",
                javob=fr(v), yechim=f"Birgalikdagi hodisalar: $P(A+B) = P(A)+P(B)-P(AB) = {d(pa, 1)}+{d(pb, 1)}-{d(pab, 1)} = {d(v)}$.",
                xato=[d(pa + pb), d(pa * pb), d(pa + pb + pab)])

def g_kopaytirish(r):
    p1, p2 = F(r.randint(6, 9), 10), F(r.randint(5, 9), 10)
    v = p1 * p2
    return dict(matn=f"Ikki mergan nishonga bittadan o‘q uzdi. Birinchisining tekkizish ehtimoli {d(p1, 1)}, ikkinchisiniki {d(p2, 1)}. Ikkalasi ham tekkizish ehtimolini toping.",
                javob=fr(v), yechim=f"Bog‘liqsiz hodisalar: $P(AB) = P(A)\\cdot P(B) = {d(p1, 1)}\\cdot {d(p2, 1)} = {d(v)}$.", xato=[d(p1 + p2 - v), d((p1 + p2) / 2), d(1 - v)])

def g_faqat_bittasi(r):
    p1, p2 = F(r.randint(6, 9), 10), F(r.randint(5, 9), 10)
    v = p1 * (1 - p2) + (1 - p1) * p2
    return dict(matn=f"Ikki mergan nishonga bittadan o‘q uzdi: tekkizish ehtimollari {d(p1, 1)} va {d(p2, 1)}. Nishonga faqat bitta o‘q tegish ehtimolini toping.",
                javob=fr(v), yechim=f"$P = p_1 q_2 + q_1 p_2 = {d(p1, 1)}\\cdot{d(1 - p2, 1)} + {d(1 - p1, 1)}\\cdot{d(p2, 1)} = {d(v)}$.", xato=[d(p1 * p2), d(1 - (1 - p1) * (1 - p2)), d(p1 * (1 - p2))])

def g_kamida_bittasi(r):
    ps = [F(r.randint(5, 9), 10) for _ in range(3)]
    q = (1 - ps[0]) * (1 - ps[1]) * (1 - ps[2]); v = 1 - q
    return dict(matn=f"Uchta qurilma bog‘liqsiz ishlaydi; ishlash ehtimollari {d(ps[0], 1)}; {d(ps[1], 1)}; {d(ps[2], 1)}. Kamida bitta qurilma ishlash ehtimolini toping.",
                javob=fr(v), yechim=f"Qarama-qarshi hodisa — hammasi ishlamaydi: $q_1q_2q_3 = {d(1 - ps[0], 1)}\\cdot{d(1 - ps[1], 1)}\\cdot{d(1 - ps[2], 1)} = {d(q)}$.\n$P = 1 - {d(q)} = {d(v)}$.",
                xato=[d(ps[0] * ps[1] * ps[2]), d(q), d(min(1, ps[0] + ps[1] + ps[2]) if ps[0] + ps[1] + ps[2] < 1 else ps[0] * ps[1] + ps[2] * 0)])

def g_kamida_n(r):
    p = F(r.choice([1, 2, 3]), 10); P = F(r.choice([9, 95, 99]), 100 if r.random() < 0.7 else 10)
    if P >= 1: P = F(9, 10)
    from math import log, ceil
    n = ceil(log(1 - float(P)) / log(1 - float(p)))
    return dict(matn=f"Bir tajribada hodisaning ro‘y berish ehtimoli {d(p, 2)}. Hodisa kamida bir marta ro‘y berish ehtimoli {d(P, 2)} dan kam bo‘lmasligi uchun kamida nechta tajriba o‘tkazish kerak?",
                javob=str(n), yechim=f"$1 - (1-p)^n \\ge {d(P, 2)}$ ⇒ $(1-p)^n \\le {d(1 - P, 2)}$ ⇒ $n \\ge \\frac{{\\ln {d(1 - P, 2)}}}{{\\ln {d(1 - p, 2)}}} \\approx {d(log(1 - float(P)) / log(1 - float(p)), 2)}$. Demak $n = {n}$.",
                xato=[str(n - 1), str(n + 2), str(int(float(P) / float(p)))])

def g_shartli(r):
    w, b = r.randint(3, 7), r.randint(2, 6); n = w + b
    v = F(w, n) * F(w - 1, n - 1)
    return dict(matn=f"Idishda {w} ta oq va {b} ta qora shar bor. Ketma-ket (qaytarmasdan) 2 ta shar olindi. Ikkalasi ham oq bo‘lish ehtimolini toping.",
                javob=fr(v), yechim=f"Bog‘liq hodisalar: $P(A_1A_2) = P(A_1)\\cdot P(A_2|A_1) = \\frac{{{w}}}{{{n}}}\\cdot\\frac{{{w - 1}}}{{{n - 1}}} = {fk(v)}$.", xato=[d(F(w, n) ** 2), d(F(w, n) * F(w - 1, n)), d(F(w - 1, n - 1))])

def g_shartli_jadval(r):
    a, b = r.randint(20, 40), r.randint(10, 30); c, e = r.randint(10, 30), r.randint(15, 35)
    v = F(a, a + c)
    return dict(matn=f"Talabalar orasida: matematikani tanlaganlar — {a} yigit va {c} qiz; boshqa fanni tanlaganlar — {b} yigit va {e} qiz. Tavakkaliga tanlangan talaba matematikani tanlagan. Uning yigit bo‘lish ehtimolini toping.",
                javob=fr(v), yechim=f"Shartli ehtimol — faqat matematikani tanlaganlar ichida: $P = \\frac{{{a}}}{{{a}+{c}}} = {fk(v)}$.", xato=[d(F(a, a + b + c + e)), d(F(a, a + b)), d(F(c, a + c))])

def g_tola(r):
    ps = [r.randint(2, 5) for _ in range(3)]; tot = sum(ps); sh = [F(x, tot) for x in ps]
    q = [F(r.randint(1, 6), 100) for _ in range(3)]
    v = sum(a * b for a, b in zip(sh, q))
    return dict(matn=f"Mahsulotni uchta zavod {ps[0]}:{ps[1]}:{ps[2]} nisbatda yetkazadi. Ulardagi brak ulushi mos ravishda {d(q[0], 2)}; {d(q[1], 2)}; {d(q[2], 2)}. Tavakkaliga olingan mahsulot brak bo‘lish ehtimolini toping.",
                javob=d(v, 4), yechim=f"Gipotezalar: $P(H_i) = {fk(sh[0])},\\ {fk(sh[1])},\\ {fk(sh[2])}$.\nTo‘la ehtimol formulasi: $P(A) = \\sum P(H_i)P(A|H_i) = {d(v, 4)}$.",
                xato=[d(sum(q) / 3, 4), d(sum(q), 4), d(max(q), 4)])

def g_bayes(r):
    ps = [r.randint(2, 5) for _ in range(3)]; tot = sum(ps); sh = [F(x, tot) for x in ps]
    q = [F(r.randint(1, 6), 100) for _ in range(3)]
    pa = sum(a * b for a, b in zip(sh, q)); k = r.randint(0, 2); v = sh[k] * q[k] / pa
    return dict(matn=f"Mahsulotni uchta zavod {ps[0]}:{ps[1]}:{ps[2]} nisbatda yetkazadi; brak ulushlari {d(q[0], 2)}; {d(q[1], 2)}; {d(q[2], 2)}. Olingan mahsulot brak chiqdi. Uning {k + 1}-zavodniki bo‘lish ehtimolini toping (0,001 aniqlikda).",
                javob=d(v, 3), yechim=f"Avval $P(A) = {d(pa, 4)}$ (to‘la ehtimol).\nBayes: $P(H_{k + 1}|A) = \\frac{{P(H_{k + 1})P(A|H_{k + 1})}}{{P(A)}} = \\frac{{{d(sh[k] * q[k], 4)}}}{{{d(pa, 4)}}} = {d(v, 3)}$.",
                xato=[d(sh[k], 3), d(sh[k] * q[k], 3), d(q[k] / sum(q), 3)])

def g_bernulli(r):
    n = r.randint(4, 8); k = r.randint(1, n - 1); p = F(r.choice([1, 2, 3, 4, 5, 6, 7]), 10)
    v = comb(n, k) * p ** k * (1 - p) ** (n - k)
    return dict(matn=f"Bir tajribada hodisaning ehtimoli {d(p, 1)}. {n} ta bog‘liqsiz tajribada hodisa roppa-rosa {k} marta ro‘y berish ehtimolini toping (0,0001 aniqlikda).",
                javob=d(v, 4), yechim=f"Bernulli formulasi: $P_{{{n}}}({k}) = C_{{{n}}}^{{{k}}}p^{{{k}}}q^{{{n - k}}} = {comb(n, k)}\\cdot {d(p, 1)}^{{{k}}}\\cdot {d(1 - p, 1)}^{{{n - k}}} = {d(v, 4)}$.",
                xato=[d(p ** k * (1 - p) ** (n - k), 4), d(comb(n, k) * p ** k, 4), d(F(k, n), 4)])

def g_kamida_k(r):
    n = r.randint(4, 6); p = F(r.choice([2, 3, 5, 6, 8]), 10)
    v = 1 - (1 - p) ** n - n * p * (1 - p) ** (n - 1)
    return dict(matn=f"{n} ta bog‘liqsiz tajribaning har birida hodisa {d(p, 1)} ehtimol bilan ro‘y beradi. Hodisa kamida 2 marta ro‘y berish ehtimolini toping (0,0001 aniqlikda).",
                javob=d(v, 4), yechim=f"$P(k\\ge 2) = 1 - P_{n}(0) - P_{n}(1) = 1 - {d((1 - p) ** n, 4)} - {d(n * p * (1 - p) ** (n - 1), 4)} = {d(v, 4)}$.",
                xato=[d(1 - (1 - p) ** n, 4), d(comb(n, 2) * p ** 2 * (1 - p) ** (n - 2), 4), d(1 - p ** n, 4)])

def g_eng_ehtimolli(r):
    n = r.randint(10, 40); p = F(r.choice([1, 2, 3, 4, 6, 7]), 10)
    lo, hi = n * p - (1 - p), n * p + p
    k0 = [k for k in range(n + 1) if lo <= k <= hi]
    return dict(matn=f"{n} ta tajribada har birida hodisa ehtimoli {d(p, 1)}. Hodisaning eng ehtimolli ro‘y berish sonini toping.",
                javob="|".join(str(k) for k in k0), yechim=f"$np - q \\le k_0 \\le np + p$: ${d(lo, 2)} \\le k_0 \\le {d(hi, 2)}$ ⇒ $k_0 = {', '.join(map(str, k0))}$.",
                xato=[str(int(n * p) + 1) if int(n * p) + 1 not in k0 else str(int(n * p) + 2), str(int(n * p) - 1) if int(n * p) - 1 not in k0 else str(int(n * p) - 2), str(n // 2) if n // 2 not in k0 else str(n // 2 + 3)])

def g_puasson(r):
    n = r.choice([500, 1000, 2000]); lam = r.choice([1, 2, 3, 4]); p = F(lam, n); k = r.randint(0, 3)
    v = exp(-lam) * lam ** k / factorial(k)
    return dict(matn=f"Zavod {n} ta mahsulot jo‘natdi. Yo‘lda mahsulot shikastlanish ehtimoli {d(p, 4)}. Roppa-rosa {k} ta mahsulot shikastlanish ehtimolini toping (Puasson formulasi, 0,0001 aniqlikda).",
                javob=d(v, 4), yechim=f"$\\lambda = np = {lam}$. $P_n(k) \\approx \\frac{{\\lambda^k e^{{-\\lambda}}}}{{k!}} = \\frac{{{lam}^{k} e^{{-{lam}}}}}{{{k}!}} = {d(v, 4)}$.",
                xato=[d(exp(-lam), 4) if k else d(lam * exp(-lam), 4), d(lam ** k / factorial(k) / 10, 4), d(float(p) * k, 4)])

def g_laplas_lokal(r):
    n = r.choice([100, 200, 400]); p = r.choice([0.2, 0.5, 0.8]); q = 1 - p; np_ = n * p; s = sqrt(n * p * q)
    k = int(round(np_ + r.choice([-1, 0, 1]) * s * 0.5))
    x = (k - np_) / s; v = phi(x) / s
    return dict(matn=f"{n} ta tajribada hodisa ehtimoli {d(p, 1)}. Hodisa roppa-rosa {k} marta ro‘y berish ehtimolini Laplasning lokal teoremasi bilan toping (0,0001 aniqlikda).",
                javob=d(v, 4), yechim=f"$\\sqrt{{npq}} = \\sqrt{{{n}\\cdot{d(p, 1)}\\cdot{d(q, 1)}}} = {d(s, 3)}$; $x = \\frac{{k - np}}{{\\sqrt{{npq}}}} = {d(x, 2)}$.\n$\\varphi({d(x, 2)}) = {d(phi(x), 4)}$; $P \\approx \\frac{{\\varphi(x)}}{{\\sqrt{{npq}}}} = {d(v, 4)}$.",
                xato=[d(phi(x), 4), d(phi(x) / (n * p * q), 4), d(1 / s, 4)])

def g_laplas_integral(r):
    n = r.choice([100, 300, 400, 600]); p = r.choice([0.2, 0.5, 0.75, 0.8]); q = 1 - p; np_ = n * p; s = sqrt(n * p * q)
    k1 = int(np_ - r.choice([1, 1.5, 2]) * s); k2 = int(np_ + r.choice([1, 1.5, 2]) * s)
    x1, x2 = (k1 - np_) / s, (k2 - np_) / s; v = Phi(round(x2, 2)) - Phi(round(x1, 2))
    return dict(matn=f"{n} ta tajribada hodisa ehtimoli {d(p, 2)}. Hodisa {k1} dan {k2} martagacha ro‘y berish ehtimolini toping (Laplasning integral teoremasi, 0,001 aniqlikda).",
                javob=d(v, 3), yechim=f"$np = {d(np_, 1)}$, $\\sqrt{{npq}} = {d(s, 3)}$.\n$x_1 = {d(round(x1, 2), 2)}$, $x_2 = {d(round(x2, 2), 2)}$.\n$P \\approx \\Phi(x_2) - \\Phi(x_1) = {d(Phi(round(x2, 2)), 4)} - ({d(Phi(round(x1, 2)), 4)}) = {d(v, 3)}$.",
                xato=[d(Phi(round(x2, 2)) + Phi(round(x1, 2)), 3), d(2 * Phi(round(x2, 2)), 3), d(Phi(round(x2, 2)), 3)])

# ─────────────────────────── TASODIFIY MIQDORLAR ───────────────────────────
def _taqsimot(r):
    xs = sorted(r.sample(range(-2, 8), 4))
    ws = [r.randint(1, 5) for _ in xs]; t = sum(ws); ps = [F(w, t) for w in ws]
    ps = [F(round(float(p) * 10), 10) for p in ps]; ps[-1] = 1 - sum(ps[:-1])
    if any(p <= 0 for p in ps): return _taqsimot(r)
    return xs, ps

def _jadval(xs, ps):
    return "$X$: " + "; ".join(str(x) for x in xs) + " — $p$: " + "; ".join(d(p, 1) for p in ps)

def g_mx(r):
    xs, ps = _taqsimot(r); m = sum(x * p for x, p in zip(xs, ps))
    return dict(matn=f"Diskret tasodifiy miqdor taqsimoti: {_jadval(xs, ps)}. $M(X)$ ni toping.", javob=d(m, 2),
                yechim=f"$M(X) = \\sum x_i p_i = " + " + ".join(f"{x}\\cdot{d(p, 1)}" for x, p in zip(xs, ps)) + f" = {d(m, 2)}$.",
                xato=[d(sum(xs) / 4, 2), d(sum(x * x * p for x, p in zip(xs, ps)), 2), d(m + 1, 2)])

def g_dx(r):
    xs, ps = _taqsimot(r); m = sum(x * p for x, p in zip(xs, ps)); m2 = sum(x * x * p for x, p in zip(xs, ps)); v = m2 - m * m
    return dict(matn=f"Taqsimot: {_jadval(xs, ps)}. $D(X)$ ni toping.", javob=d(v, 2),
                yechim=f"$M(X) = {d(m, 2)}$, $M(X^2) = {d(m2, 2)}$.\n$D(X) = M(X^2) - M^2(X) = {d(m2, 2)} - {d(m * m, 4)} = {d(v, 2)}$.",
                xato=[d(m2, 2), d(m2 - m, 2), d(sqrt(float(v)) if v > 0 else 0, 2)])

def g_sigma(r):
    xs, ps = _taqsimot(r); m = sum(x * p for x, p in zip(xs, ps)); v = sum(x * x * p for x, p in zip(xs, ps)) - m * m
    return dict(matn=f"Taqsimot: {_jadval(xs, ps)}. O‘rtacha kvadratik chetlanish $\\sigma(X)$ ni toping (0,01 aniqlikda).", javob=d(sqrt(float(v)), 2),
                yechim=f"$D(X) = {d(v, 4)}$; $\\sigma = \\sqrt{{D(X)}} = {d(sqrt(float(v)), 2)}$.", xato=[d(v, 2), d(float(v) / 2, 2), d(sqrt(float(v)) + 1, 2)])

def g_noma_p(r):
    xs, ps = _taqsimot(r); k = r.randint(0, 3)
    return dict(matn="Taqsimot: $X$: " + "; ".join(str(x) for x in xs) + " — $p$: " + "; ".join("$p$" if i == k else d(p, 1) for i, p in enumerate(ps)) + ". Noma’lum $p$ ni toping.",
                javob=d(ps[k], 1), yechim=f"Ehtimollar yig‘indisi 1 ga teng: $p = 1 - {d(1 - ps[k], 1)} = {d(ps[k], 1)}$.", xato=[d(1 - ps[k], 1), d(ps[k] + F(1, 10), 1), d(F(1, 4), 2)])

def g_xossa(r):
    a, b, m, v = r.randint(2, 5), r.randint(-5, 6), r.randint(-3, 6), r.randint(1, 9)
    return dict(matn=f"$M(X) = {m}$, $D(X) = {v}$. $Y = {a}X {'+' if b >= 0 else '-'} {abs(b)}$ uchun $M(Y) + D(Y)$ ni toping.",
                javob=str(a * m + b + a * a * v), yechim=f"$M(Y) = {a}\\cdot{m} {'+' if b >= 0 else '-'} {abs(b)} = {a * m + b}$; $D(Y) = {a}^2\\cdot{v} = {a * a * v}$ (o‘zgarmas dispersiyani o‘zgartirmaydi).\nYig‘indi: ${a * m + b + a * a * v}$.",
                xato=[str(a * m + b + a * v), str(a * m + b + a * a * v + b), str(a * m + a * a * v)])

def g_binom_mx(r):
    n, p = r.randint(10, 100), r.choice([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8])
    return dict(matn=f"$X$ — binomial taqsimlangan: $n = {n}$, $p = {d(p, 1)}$. $M(X)$ va $D(X)$ yig‘indisini toping.", javob=d(n * p + n * p * (1 - p), 2),
                yechim=f"$M(X) = np = {d(n * p, 2)}$, $D(X) = npq = {d(n * p * (1 - p), 2)}$. Yig‘indi ${d(n * p + n * p * (1 - p), 2)}$.", xato=[d(n * p * 2, 2), d(n * p + n * p * p, 2), d(n * p, 2)])

def g_puasson_mx(r):
    lam = r.choice([0.5, 1.5, 2, 2.5, 3, 4])
    v = 1 - exp(-lam)
    return dict(matn=f"$X$ Puasson qonuni bo‘yicha taqsimlangan, $\\lambda = {d(lam, 1)}$. $P(X \\ge 1)$ ni toping (0,001 aniqlikda).", javob=d(v, 3),
                yechim=f"$P(X\\ge1) = 1 - P(X=0) = 1 - e^{{-{d(lam, 1)}}} = {d(v, 3)}$.", xato=[d(exp(-lam), 3), d(lam * exp(-lam), 3), d(1 - lam * exp(-lam), 3)])

def g_geom(r):
    p = r.choice([F(1, 6), F(1, 4), F(1, 5), F(3, 10)]); k = r.randint(2, 5)
    v = (1 - p) ** (k - 1) * p
    return dict(matn=f"Har urinishda muvaffaqiyat ehtimoli ${fk(p)}$. Birinchi muvaffaqiyat roppa-rosa {k}-urinishda bo‘lish ehtimolini toping.", javob=fr(v),
                yechim=f"Geometrik taqsimot: $P(X={k}) = q^{{{k - 1}}}p = {fk(1 - p)}^{{{k - 1}}}\\cdot{fk(p)} = {fk(v)}$.", xato=[d(p ** k), d((1 - p) ** k), d(1 - (1 - p) ** k)])

def g_gipergeom(r):
    N, M, n = r.randint(12, 20), r.randint(4, 7), r.randint(3, 5); k = r.randint(1, min(M, n) - 0)
    v = F(comb(M, k) * comb(N - M, n - k), comb(N, n))
    return dict(matn=f"{N} ta lotereya biletidan {M} tasi yutuqli. Tavakkaliga {n} ta bilet olindi. Ulardan roppa-rosa {k} tasi yutuqli bo‘lish ehtimolini toping.", javob=fr(v),
                yechim=f"Gipergeometrik: $P = \\frac{{C_{{{M}}}^{{{k}}}C_{{{N - M}}}^{{{n - k}}}}}{{C_{{{N}}}^{{{n}}}}} = {fk(v)}$.", xato=[d(comb(n, k) * F(M, N) ** k * (1 - F(M, N)) ** (n - k)), d(F(comb(M, k), comb(N, n))), d(F(k, n))])

def g_uzluksiz_f(r):
    a = r.randint(1, 3); b = a + r.randint(2, 4); x1 = a + r.randint(0, b - a - 1); x2 = r.randint(x1 + 1, b)
    v = F(x2 - x1, b - a)
    return dict(matn=f"$X$ $[{a};{b}]$ oraliqda tekis taqsimlangan. $P({x1} < X < {x2})$ ni toping.", javob=fr(v),
                yechim=f"Tekis taqsimotda $f(x) = \\frac{{1}}{{{b - a}}}$: $P = \\frac{{{x2} - {x1}}}{{{b} - {a}}} = {fk(v)}$.", xato=[d(F(x2 - x1, b)), d(F(x2, b)), d(F(x1, b - a))])

def g_zichlik_c(r):
    k = r.choice([1, 2]); a = r.randint(1, 3)
    # f(x) = C x^k, 0..a
    C = F(k + 1, a ** (k + 1))
    return dict(matn=f"$f(x) = C {'x' if k == 1 else 'x^{' + str(k) + '}'}$ ($0 \\le x \\le {a}$), qolgan joyda $0$. $C$ ni toping.", javob=fr(C),
                yechim=f"$\\int_0^{{{a}}} Cx^{{{k}}}dx = C\\frac{{{a}^{{{k + 1}}}}}{{{k + 1}}} = 1$ ⇒ $C = {fk(C)}$.", xato=[d(F(1, a ** k)), d(F(k, a ** (k + 1))), d(F(1, a))])

def g_uzluksiz_m(r):
    a = r.randint(1, 3); k = 1; C = F(2, a * a)
    m = C * F(a ** 3, 3); m2 = C * F(a ** 4, 4); v = m2 - m * m
    return dict(matn=f"Zichlik $f(x) = \\frac{{2x}}{{{a * a}}}$ ($0\\le x\\le {a}$), aks holda 0. $M(X)$ ni toping.", javob=fr(m),
                yechim=f"$M(X) = \\int_0^{{{a}}} x\\cdot\\frac{{2x}}{{{a * a}}}dx = \\frac{{2}}{{{a * a}}}\\cdot\\frac{{{a}^3}}{{3}} = {fk(m)}$.", xato=[d(F(a, 2)), d(m2), d(F(a, 3))])

def g_korsatkichli(r):
    lam = r.choice([0.5, 1, 2, 0.2]); a, b = r.choice([(0, 1), (1, 2), (0, 2), (1, 3)])
    v = exp(-lam * a) - exp(-lam * b)
    return dict(matn=f"$X$ ko‘rsatkichli taqsimlangan, $\\lambda = {d(lam, 1)}$. $P({a} < X < {b})$ ni toping (0,001 aniqlikda).", javob=d(v, 3),
                yechim=f"$P(a<X<b) = e^{{-\\lambda a}} - e^{{-\\lambda b}} = e^{{-{d(lam * a, 1)}}} - e^{{-{d(lam * b, 1)}}} = {d(v, 3)}$.", xato=[d(1 - exp(-lam * b), 3), d(exp(-lam * b), 3), d(lam * (b - a), 3)])

def g_normal(r):
    a, s = r.choice([(50, 5), (100, 10), (20, 4), (70, 6), (0, 1)]); k1, k2 = r.choice([(-1, 1), (-2, 1), (-1, 2), (0, 2), (-2, 2)])
    x1, x2 = a + k1 * s, a + k2 * s; v = Phi(k2) - Phi(k1)
    return dict(matn=f"$X \\sim N({a};\\,{s}^2)$ (o‘rta qiymat {a}, $\\sigma = {s}$). $P({x1} < X < {x2})$ ni toping (0,001 aniqlikda).", javob=d(v, 3),
                yechim=f"$P = \\Phi\\left(\\frac{{{x2} - {a}}}{{{s}}}\\right) - \\Phi\\left(\\frac{{{x1} - {a}}}{{{s}}}\\right) = \\Phi({k2}) - \\Phi({k1}) = {d(Phi(k2), 4)} - ({d(Phi(k1), 4)}) = {d(v, 3)}$.",
                xato=[d(Phi(k2) + Phi(k1), 3), d(2 * Phi(k2), 3), d(Phi(k2), 3)])

def g_uch_sigma(r):
    a, s = r.choice([(50, 5), (100, 10), (20, 4), (170, 6)]); k = r.choice([1, 2, 3])
    v = 2 * Phi(k)
    return dict(matn=f"$X \\sim N({a};\\,{s}^2)$. $|X - {a}| < {k * s}$ bo‘lish ehtimolini toping (0,001 aniqlikda).", javob=d(v, 3),
                yechim=f"$P(|X-a| < \\delta) = 2\\Phi\\left(\\frac{{\\delta}}{{\\sigma}}\\right) = 2\\Phi({k}) = {d(v, 3)}$." + (" Bu «uch sigma» qoidasi." if k == 3 else ""),
                xato=[d(Phi(k), 3), d(1 - 2 * Phi(k), 3), d(2 * Phi(k + 1), 3)])

def g_chebishev(r):
    D, e = r.choice([(4, 4), (2, 2), (9, 5), (6, 4), (1, 2)])
    v = F(D, e * e)
    return dict(matn=f"$D(X) = {D}$. Chebishev tengsizligi bo‘yicha $P(|X - M(X)| \\ge {e})$ ehtimolini yuqoridan baholang.", javob=fr(v),
                yechim=f"$P(|X-M(X)|\\ge\\varepsilon) \\le \\frac{{D(X)}}{{\\varepsilon^2}} = \\frac{{{D}}}{{{e * e}}} = {fk(v)}$.", xato=[d(1 - v), d(F(D, e)), d(F(e, D))])

def g_mlt(r):
    n = r.choice([100, 64, 36, 81]); m, s = r.choice([(2, 1), (5, 2), (10, 3)]); c = r.choice([1, 2])
    S = n * m; sS = s * sqrt(n); v = 2 * Phi(c)
    return dict(matn=f"{n} ta bog‘liqsiz tasodifiy miqdorning har biri uchun $M = {m}$, $\\sigma = {s}$. Yig‘indi $S$ ning $[{d(S - c * sS, 0)};\\,{d(S + c * sS, 0)}]$ oraliqqa tushish ehtimolini MLT bilan toping (0,001 aniqlikda).",
                javob=d(v, 3), yechim=f"$M(S) = {S}$, $\\sigma(S) = {s}\\sqrt{{{n}}} = {d(sS, 1)}$.\n$P \\approx 2\\Phi({c}) = {d(v, 3)}$.", xato=[d(Phi(c), 3), d(2 * Phi(c / 2), 3), d(1 - Phi(c), 3)])
