"""MOCK shablonlari 24–35: geometriya, vektorlar, kombinatorika, ehtimollik (shaklsiz — matn bilan tavsiflangan)."""
import itertools
import math
from fractions import Fraction

from modules import mock_fig as F
from modules.mock_fig import FIG
from modules.mock_lib import M, fx, shablon, tomon_pifagor, yopiq

PI = "\\pi"


# ───────── 24: to'g'ri burchakli uchburchak ─────────
@shablon(24, "balandlik")
def s24a(rng):
    a, b, c = tomon_pifagor(rng)
    FIG(F.tri_toqri(a, b, balandlik=True))
    return yopiq(rng, f"To‘g‘ri burchakli uchburchakning katetlari {a} va {b}. Gipotenuzaga tushirilgan balandlikni toping.", Fraction(a * b, c),
                 [f"Gipotenuza: $c=\\sqrt{{{a}^2+{b}^2}}={c}$.", f"Yuz ikki usulda: $\\frac{{ab}}{{2}}=\\frac{{ch}}{{2}}$.", f"$h=\\frac{{{a}\\cdot {b}}}{{{c}}}={fx(Fraction(a * b, c))}$."])


@shablon(24, "ichki chizilgan aylana")
def s24b(rng):
    a, b, c = tomon_pifagor(rng)
    FIG(F.tri_toqri(a, b, ichki=True))
    return yopiq(rng, f"Katetlari {a} va {b} bo‘lgan to‘g‘ri burchakli uchburchakka ichki chizilgan aylana radiusini toping.", Fraction(a + b - c, 2),
                 [f"Gipotenuza ${c}$.", f"To‘g‘ri burchakli uchburchakda $r=\\frac{{a+b-c}}{{2}}$.", f"$r=\\frac{{{a}+{b}-{c}}}{{2}}={fx(Fraction(a + b - c, 2))}$."])


@shablon(24, "proyeksiya")
def s24c(rng):
    a, b, c = tomon_pifagor(rng)
    FIG(F.tri_toqri(a, b))
    return yopiq(rng, f"To‘g‘ri burchakli uchburchakda gipotenuza {c}, bir katet {a}. Shu katetning gipotenuzadagi proyeksiyasini toping.", Fraction(a * a, c),
                 [f"Katet kvadrati gipotenuza bilan proyeksiya ko‘paytmasiga teng: $a^2=c\\cdot a_c$.", f"$a_c=\\frac{{{a}^2}}{{{c}}}={fx(Fraction(a * a, c))}$."])


# ───────── 25: trapetsiya ─────────
@shablon(25, "diagonallar kesishuvi")
def s25a(rng):
    while True:
        a, b = rng.randint(2, 15), rng.randint(2, 15)
        v = Fraction(2 * a * b, a + b)
        if a != b and v.denominator <= 5:
            break
    FIG(F.trapetsiya(a, b, diagonal=True))
    return yopiq(rng, f"Trapetsiyaning asoslari {a} va {b}. Diagonallar kesishgan nuqta orqali asoslarga parallel to‘g‘ri chiziq o‘tkazildi. Uning yon tomonlar orasidagi kesmasi uzunligini toping.", v,
                 ["Bu kesma asoslarning o‘rta garmonigi: $\\frac{2ab}{a+b}$.", f"$\\frac{{2\\cdot {a}\\cdot {b}}}{{{a}+{b}}}={fx(v)}$."])


@shablon(25, "o'rta chiziq")
def s25b(rng):
    a, b = rng.randint(3, 12), rng.randint(13, 30)
    FIG(F.trapetsiya(b, a, orta=True))
    return yopiq(rng, f"Trapetsiyaning o‘rta chizig‘i {Fraction(a + b, 2) if (a + b) % 2 == 0 else str(Fraction(a + b, 2))}, kichik asosi {a}. Katta asosini toping.".replace("/", ":"), b,
                 ["O‘rta chiziq asoslar yig‘indisining yarmiga teng.", f"$a+b=2\\cdot m={a + b}$, bundan $b={a + b}-{a}={b}$."]) if (a + b) % 2 == 0 else s25b(rng)


@shablon(25, "o'xshash uchburchaklar")
def s25c(rng):
    k, l = rng.choice([(1, 2), (2, 3), (1, 3), (2, 5), (3, 4)])
    S1 = rng.randint(2, 9) * k * k
    tot = Fraction(S1) * (k + l) ** 2 / (k * k)
    FIG(F.trapetsiya(l * 4, k * 4, diagonal=True))
    return yopiq(rng, f"Trapetsiya asoslari {k}:{l} nisbatda. Diagonallar kesishganda kichik asos ustidagi uchburchakning yuzi {S1}. Trapetsiyaning yuzini toping.", tot,
                 [f"Diagonallar kesishgan nuqtada hosil bo‘lgan asoslar ustidagi uchburchaklar o‘xshash, o‘xshashlik koeffitsiyenti ${k}:{l}$.", f"Yuzlar nisbati ${k * k}:{l * l}$, katta asos ustidagi uchburchak yuzi ${fx(Fraction(S1 * l * l, k * k))}$.",
                  f"Yon uchburchaklar yuzlari o‘zaro teng, har biri ${fx(Fraction(S1 * l, k))}$. Jami: ${fx(tot)}$."])


# ───────── 26: medianalar ─────────
@shablon(26, "gipotenuza medianasi")
def s26a(rng):
    a, b, c = tomon_pifagor(rng)
    FIG(F.tri_toqri(a, b, mediana=True))
    return yopiq(rng, f"To‘g‘ri burchakli uchburchakning katetlari {a} va {b}. To‘g‘ri burchak uchidan medianalar kesishgan nuqtagacha (og‘irlik markazigacha) bo‘lgan masofani toping.", Fraction(c, 3),
                 [f"Gipotenuza ${c}$, unga tushirilgan mediana ${fx(Fraction(c, 2))}$ (gipotenuzaning yarmi).", f"Og‘irlik markazi uchdan ikkini ajratadi: $\\frac{{2}}{{3}}\\cdot {fx(Fraction(c, 2))}={fx(Fraction(c, 3))}$."])


@shablon(26, "markaz")
def s26b(rng):
    m = rng.randint(2, 12) * 3
    return yopiq(rng, f"Uchburchak medianasi {m} ga teng. Uchdan medianalar kesishgan nuqtagacha masofani toping.", Fraction(2 * m, 3),
                 ["Medianalar kesishish nuqtasi har bir medianani uchidan boshlab $2:1$ nisbatda bo‘ladi.", f"$\\frac{{2}}{{3}}\\cdot {m}={fx(Fraction(2 * m, 3))}$."])


@shablon(26, "o'rta chiziqlar uchburchagi")
def s26c(rng):
    P = rng.randint(6, 40) * 2
    return yopiq(rng, f"Uchburchakning perimetri {P}. Uning o‘rta chiziqlaridan tuzilgan uchburchakning perimetrini toping.", Fraction(P, 2),
                 ["Har bir o‘rta chiziq mos tomonning yarmiga teng.", f"Perimetr ham ikki marta kichik: ${P}:2={fx(Fraction(P, 2))}$."])


# ───────── 27: to'g'ri to'rtburchak ─────────
@shablon(27, "diagonaldagi nuqta")
def s27a(rng):
    while True:
        a, b, k = rng.randint(3, 14), rng.randint(3, 14), rng.randint(1, 5)
        S = a * b
        v = Fraction(S, 2) * Fraction(k, k + 1)
        if v.denominator <= 3:
            break
    FIG(F.toqri_tortburchak(a, b, M=k))
    return yopiq(rng, f"$ABCD$ to‘g‘ri to‘rtburchakning tomonlari {a} va {b}. $AC$ diagonalda $AM:MC=1:{k}$ bo‘ladigan $M$ nuqta olindi. $BMC$ uchburchakning yuzini toping.", v,
                 [f"$S_{{ABC}}=\\frac{{{a}\\cdot {b}}}{{2}}={fx(Fraction(S, 2))}$.", f"$M$ nuqta $AC$ ni $1:{k}$ nisbatda bo‘ladi, $MC=\\frac{{{k}}}{{{k + 1}}}AC$.", f"$S_{{BMC}}=\\frac{{{k}}}{{{k + 1}}}\\cdot {fx(Fraction(S, 2))}={fx(v)}$."])


@shablon(27, "diagonal")
def s27b(rng):
    a, b, c = tomon_pifagor(rng)
    FIG(F.toqri_tortburchak(a, b))
    return yopiq(rng, f"To‘g‘ri to‘rtburchakning tomonlari {a} va {b}. Uning diagonali kvadratini toping.", c * c, [f"$d^2=a^2+b^2={a}^2+{b}^2={c * c}$."], noto=[a * a, b * b, a + b])


@shablon(27, "perimetr va yuz")
def s27c(rng):
    a, b = rng.randint(3, 15), rng.randint(3, 15)
    FIG(F.toqri_tortburchak(a, b))
    return yopiq(rng, f"To‘g‘ri to‘rtburchakning perimetri {2 * (a + b)}, yuzi {a * b}. Uning diagonali kvadratini toping.", a * a + b * b,
                 [f"$a+b={a + b}$, $ab={a * b}$.", f"$d^2=a^2+b^2=(a+b)^2-2ab={(a + b) ** 2}-{2 * a * b}={a * a + b * b}$."])


# ───────── 28: muntazam ko'pburchak ─────────
@shablon(28, "diagonallar soni")
def s28a(rng):
    n = rng.choice([8, 9, 10, 12, 15, 18, 20])
    ang = Fraction(180 * (n - 2), n)
    FIG(F.kopburchak(n))
    return yopiq(rng, f"Muntazam ko‘pburchakning ichki burchagi {fx(ang)}° ga teng. Uning diagonallari nechta?", n * (n - 3) // 2,
                 [f"Ichki burchak $\\frac{{180(n-2)}}{{n}}={fx(ang)}$ dan $n={n}$.", f"Diagonallar soni $\\frac{{n(n-3)}}{{2}}=\\frac{{{n}\\cdot {n - 3}}}{{2}}={n * (n - 3) // 2}$."])


@shablon(28, "burchaklar yig'indisi")
def s28b(rng):
    n = rng.randint(7, 20)
    FIG(F.kopburchak(n))
    return yopiq(rng, f"Qavariq {n} burchakning barcha ichki burchaklari yig‘indisi necha gradus?", 180 * (n - 2), [f"$180^\\circ(n-2)=180\\cdot {n - 2}={180 * (n - 2)}$."])


@shablon(28, "tashqi burchak")
def s28c(rng):
    n = rng.choice([5, 6, 8, 9, 10, 12, 15, 18, 20, 24])
    FIG(F.kopburchak(n))
    return yopiq(rng, f"Muntazam {n} burchakning bitta tashqi burchagi necha gradus?", Fraction(360, n), [f"Tashqi burchaklar yig‘indisi $360^\\circ$, ular teng: $\\frac{{360}}{{{n}}}={fx(Fraction(360, n))}$."])


# ───────── 29: vektorlar ─────────
@shablon(29, "skalyar ko'paytma")
def s29a(rng):
    A, B = rng.randint(2, 6), rng.randint(2, 6)
    th, cs = rng.choice([(60, Fraction(1, 2)), (120, Fraction(-1, 2)), (90, Fraction(0)), (180, Fraction(-1))])
    p, q, r, s = rng.randint(1, 3), rng.randint(1, 3), rng.randint(1, 3), rng.randint(1, 3)
    ab = A * B * cs
    v = p * r * A * A + (p * s + q * r) * ab + q * s * B * B
    FIG(F.vektorlar(A, B, th))
    return yopiq(rng, f"$|\\vec a|={A}$, $|\\vec b|={B}$, ular orasidagi burchak ${th}^\\circ$. $({p}\\vec a+{q}\\vec b)\\cdot({r}\\vec a+{s}\\vec b)$ ni toping.", v,
                 [f"$\\vec a\\cdot\\vec b=|\\vec a||\\vec b|\\cos{th}^\\circ={fx(ab)}$.", f"Qavslarni ochamiz: ${p * r}\\,\\vec a^2+{p * s + q * r}\\,\\vec a\\vec b+{q * s}\\,\\vec b^2$.", f"$={p * r}\\cdot {A * A}+{p * s + q * r}\\cdot ({fx(ab)})+{q * s}\\cdot {B * B}={fx(v)}$."])


@shablon(29, "perpendikulyar vektorlar")
def s29b(rng):
    x1, y1, z1 = rng.randint(-4, 5), rng.randint(-4, 5), rng.randint(-4, 5)
    x2, y2 = rng.randint(-4, 5), rng.randint(-4, 5)
    k = rng.randint(2, 4)
    # a=(x1,y1,z1·t?): a·b = x1x2+y1y2+z1·(k·t)=0 → t = −(x1x2+y1y2)/(z1 k)
    if z1 == 0:
        return s29b(rng)
    t = Fraction(-(x1 * x2 + y1 * y2), z1 * k)
    return yopiq(rng, f"$\\vec a=({x1};\\,{y1};\\,{z1})$ va $\\vec b=({x2};\\,{y2};\\,{k}t)$ vektorlar o‘zaro perpendikulyar bo‘lsa, $t$ ni toping.", t,
                 ["Perpendikulyar vektorlarning skalyar ko‘paytmasi nol.", f"${x1}\\cdot({x2})+{y1}\\cdot({y2})+{z1}\\cdot {k}t=0$.", f"$t={fx(t)}$."])


@shablon(29, "yig'indi uzunligi")
def s29c(rng):
    A, B, th, C = rng.choice([(3, 5, 60, 7), (5, 3, 60, 7), (3, 8, 120, 7), (8, 3, 120, 7), (5, 8, 120, 7), (7, 8, 60, 13), (5, 3, 120, 7)])
    FIG(F.vektorlar(A, B, th, yig=True))
    return yopiq(rng, f"$|\\vec a|={A}$, $|\\vec b|={B}$, ular orasidagi burchak ${th}^\\circ$. $|\\vec a+\\vec b|$ ni toping.", C,
                 [f"$|\\vec a+\\vec b|^2=|\\vec a|^2+|\\vec b|^2+2|\\vec a||\\vec b|\\cos{th}^\\circ$.", f"$={A * A}+{B * B}+2\\cdot {A}\\cdot {B}\\cdot ({fx(Fraction(1, 2) if th == 60 else Fraction(-1, 2))})={C * C}$, demak ${C}$."])


# ───────── 30: jismlar ─────────
@shablon(30, "prizma hajmi")
def s30a(rng):
    a, b, c = tomon_pifagor(rng)
    h = rng.randint(3, 12)
    FIG(F.prizma(a, b, h))
    return yopiq(rng, f"To‘g‘ri prizmaning asosi katetlari {a} va {b} bo‘lgan to‘g‘ri burchakli uchburchak, balandligi {h}. Prizmaning hajmini toping.", Fraction(a * b * h, 2),
                 [f"Asos yuzi: $\\frac{{{a}\\cdot {b}}}{{2}}={fx(Fraction(a * b, 2))}$.", f"$V=S\\cdot h={fx(Fraction(a * b, 2))}\\cdot {h}={fx(Fraction(a * b * h, 2))}$."])


@shablon(30, "piramida hajmi")
def s30b(rng):
    a, h = rng.randint(2, 12), rng.randint(2, 12)
    v = Fraction(a * a * h, 3)
    FIG(F.piramida(a, h))
    return yopiq(rng, f"Muntazam to‘rtburchakli piramida asosining tomoni {a}, balandligi {h}. Hajmini toping.", v, [f"$V=\\frac{{1}}{{3}}S_{{asos}}h=\\frac{{1}}{{3}}\\cdot {a}^2\\cdot {h}={fx(v)}$."])


@shablon(30, "silindr va konus")
def s30c(rng):
    r, h = rng.randint(2, 9), rng.randint(2, 9)
    if rng.random() < .5:
        v = Fraction(r * r * h, 3)
        FIG(F.konus(r, h))
        return yopiq(rng, f"Konusning asos radiusi {r}, balandligi {h}. Hajmining $\\pi$ ga nisbatini ($V/\\pi$) toping.", v, [f"$V=\\frac{{1}}{{3}}\\pi r^2h$, $\\frac{{V}}{{\\pi}}=\\frac{{{r}^2\\cdot {h}}}{{3}}={fx(v)}$."])
    v = r * r * h
    FIG(F.silindr(r, h))
    return yopiq(rng, f"Silindrning asos radiusi {r}, balandligi {h}. Hajmining $\\pi$ ga nisbatini ($V/\\pi$) toping.", v, [f"$V=\\pi r^2h$, $\\frac{{V}}{{\\pi}}={r}^2\\cdot {h}={v}$."])


# ───────── 31: to'plamlar va ehtimollik ─────────
@shablon(31, "to'plamlar")
def s31a(rng):
    n, a, b = rng.randint(30, 60), rng.randint(15, 30), rng.randint(12, 28)
    ab = max(0, a + b - n) + rng.randint(0, min(a, b) - max(0, a + b - n))
    only = a + b - ab
    FIG(F.venn(n, a, b, ab))
    return yopiq(rng, f"Sinfdagi {n} o‘quvchidan {a} tasi matematikani, {b} tasi fizikani yaxshi ko‘radi, {ab} tasi ikkalasini. Ikkala fanni ham yoqtirmaydiganlar nechta?", n - only,
                 [f"Kamida bittasini yoqtiradiganlar: ${a}+{b}-{ab}={only}$.", f"Hech birini yoqtirmaydiganlar: ${n}-{only}={n - only}$."])


@shablon(31, "o'yin kubigi")
def s31b(rng):
    s = rng.randint(3, 11)
    c = sum(1 for x in range(1, 7) for y in range(1, 7) if x + y == s)
    return yopiq(rng, f"Ikkita o‘yin kubigi tashlandi. Tushgan ochkolar yig‘indisi {s} bo‘lish ehtimolini toping.", Fraction(c, 36),
                 [f"Barcha natijalar: $6\\cdot 6=36$.", f"Yig‘indi {s} bo‘ladigan juftliklar: ${c}$ ta.", f"Ehtimol: $\\frac{{{c}}}{{36}}={fx(Fraction(c, 36))}$."])


@shablon(31, "shar tanlash")
def s31c(rng):
    r, k = rng.randint(3, 8), rng.randint(3, 8)
    p = Fraction(math.comb(r, 2), math.comb(r + k, 2))
    return yopiq(rng, f"Qutida {r} ta qizil va {k} ta ko‘k shar bor. Tavakkaliga ikkita shar olinganda ikkalasi ham qizil bo‘lish ehtimolini toping.", p,
                 [f"Jami usullar: $C_{{{r + k}}}^2={math.comb(r + k, 2)}$.", f"Qizillar: $C_{{{r}}}^2={math.comb(r, 2)}$.", f"Ehtimol: ${fx(p)}$."])


# ───────── 32: kombinatorika ─────────
@shablon(32, "raqamlardan sonlar")
def s32a(rng):
    digs = list("".join(rng.choice("0123456789") + "" for _ in range(0)))
    while True:
        pool = [rng.choice("012345") for _ in range(2)] + list(rng.sample("12345", 2))
        pool = pool * 2 if len(pool) == 4 else pool
        digs = sorted(pool)
        if len(digs) <= 8 and "0" in digs:
            break
    odd = rng.random() < .5
    sset = set(itertools.permutations(digs))
    cnt = sum(1 for p in sset if p[0] != "0" and (int(p[-1]) % 2 == 1) == odd)
    return yopiq(rng, f"{''.join(digs)} sonining raqamlari o‘rnini almashtirib, nechta {len(digs)} xonali {'toq' if odd else 'juft'} son hosil qilish mumkin?", cnt,
                 ["Birinchi raqam $0$ bo‘lmasligi va oxirgi raqam " + ("toq" if odd else "juft") + " bo‘lishi shart.", "Takrorlanuvchi raqamlar bo‘lgani uchun har bir holatda $\\frac{n!}{k_1!k_2!\\dots}$ usuldan foydalanamiz.", f"Barcha mos joylashuvlar yig‘indisi: ${cnt}$."])


@shablon(32, "qo'mita")
def s32b(rng):
    m, w = rng.randint(5, 9), rng.randint(4, 8)
    a, b = rng.randint(1, 3), rng.randint(1, 3)
    v = math.comb(m, a) * math.comb(w, b)
    return yopiq(rng, f"Guruhda {m} ta o‘g‘il va {w} ta qiz bor. {a} ta o‘g‘il va {b} ta qizdan iborat komissiya necha usulda tuzilishi mumkin?", v,
                 [f"O‘g‘illardan: $C_{{{m}}}^{{{a}}}={math.comb(m, a)}$.", f"Qizlardan: $C_{{{w}}}^{{{b}}}={math.comb(w, b)}$.", f"Ko‘paytma: ${v}$."])


@shablon(32, "harflar")
def s32c(rng):
    word = rng.choice(["MATEMATIKA", "ARIFMETIKA", "KATTA", "PARALLEL", "OLMA", "TANISH", "SABOQ"])
    from collections import Counter
    c = Counter(word)
    v = math.factorial(len(word))
    for x in c.values():
        v //= math.factorial(x)
    return yopiq(rng, f"“{word}” so‘zi harflaridan (har bir harf o‘z sonicha ishlatilib) nechta turli so‘z yasash mumkin?", v,
                 [f"Harflar soni {len(word)}; takrorlanuvchilar: " + ", ".join(f"{k}—{x} marta" for k, x in c.items() if x > 1) + ".", f"$\\frac{{{len(word)}!}}{{{'!'.join(str(x) for x in c.values() if x > 1) + '!' if any(x > 1 for x in c.values()) else '1'}}}={v}$."])


# ───────── 33–35 ─────────
@shablon(33, "diagonallar")
def s33a(rng):
    n = rng.randint(7, 20)
    FIG(F.kopburchak(n))
    return yopiq(rng, f"Qavariq {n} burchakning diagonallari nechta?", n * (n - 3) // 2, [f"$\\frac{{n(n-3)}}{{2}}=\\frac{{{n}\\cdot {n - 3}}}{{2}}={n * (n - 3) // 2}$."])


@shablon(33, "uchburchaklar soni")
def s33b(rng):
    n = rng.randint(6, 14)
    c = sum(1 for t in itertools.combinations(range(n), 3) if all(((t[(i + 1) % 3] - t[i]) % n) not in (1, n - 1) for i in range(3)))
    return yopiq(rng, f"Muntazam {n} burchakning uchlarida uchlari joylashgan, tomonlari ko‘pburchakning hech bir tomoni bo‘lmaydigan nechta uchburchak bor?", c,
                 [f"Jami uchburchaklar $C_{{{n}}}^3={math.comb(n, 3)}$.", "Ko‘pburchak tomonini o‘z ichiga olgan uchburchaklarni chiqarib tashlaymiz.", f"Qolgan uchburchaklar soni: ${c}$."])


@shablon(34, "tanga")
def s34a(rng):
    n = rng.randint(4, 9); k = rng.randint(1, n - 1)
    return yopiq(rng, f"Tanga {n} marta tashlandi. Aynan {k} marta gerb tushish ehtimolini toping.", Fraction(math.comb(n, k), 2 ** n),
                 [f"Barcha natijalar: $2^{{{n}}}={2 ** n}$.", f"Qulay: $C_{{{n}}}^{{{k}}}={math.comb(n, k)}$.", f"Ehtimol: ${fx(Fraction(math.comb(n, k), 2 ** n))}$."])


@shablon(34, "ikki raqamli son")
def s34b(rng):
    d = rng.choice([3, 4, 5, 6, 7, 9])
    c = sum(1 for n in range(10, 100) if n % d == 0)
    return yopiq(rng, f"Ikki xonali sonlar orasidan tavakkaliga bittasi tanlandi. Uning {d} ga bo‘linish ehtimolini toping.", Fraction(c, 90),
                 ["Ikki xonali sonlar soni 90 ta.", f"${d}$ ga bo‘linadiganlari: ${c}$ ta.", f"Ehtimol: ${fx(Fraction(c, 90))}$."])


@shablon(35, "parallel to'g'ri chiziqlardagi nuqtalar")
def s35a(rng):
    a, b = rng.randint(3, 9), rng.randint(3, 9)
    v = math.comb(a, 2) * b + math.comb(b, 2) * a
    return yopiq(rng, f"Ikkita parallel to‘g‘ri chiziqdan birida {a} ta, ikkinchisida {b} ta nuqta belgilangan. Uchlari shu nuqtalarda bo‘lgan nechta uchburchak yasash mumkin?", v,
                 [f"Ikki nuqta birinchi chiziqdan, bittasi ikkinchisidan: $C_{{{a}}}^2\\cdot {b}={math.comb(a, 2) * b}$.", f"Ikki nuqta ikkinchi chiziqdan, bittasi birinchisidan: $C_{{{b}}}^2\\cdot {a}={math.comb(b, 2) * a}$.", f"Jami: ${v}$."])


@shablon(35, "to'rtburchaklar")
def s35b(rng):
    m, n = rng.randint(3, 8), rng.randint(3, 8)
    return yopiq(rng, f"Bir-biriga parallel {m} ta gorizontal va {n} ta vertikal to‘g‘ri chiziq kesishadi. Hosil bo‘lgan to‘g‘ri to‘rtburchaklar (kataklar birikmasi ham) nechta?", math.comb(m, 2) * math.comb(n, 2),
                 [f"Ikkita gorizontal chiziqni tanlash: $C_{{{m}}}^2={math.comb(m, 2)}$.", f"Ikkita vertikal chiziqni tanlash: $C_{{{n}}}^2={math.comb(n, 2)}$.", f"Ko‘paytma: ${math.comb(m, 2) * math.comb(n, 2)}$."])
