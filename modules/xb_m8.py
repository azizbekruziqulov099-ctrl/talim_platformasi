"""TIMSS 8-sinf matematika: 13 mavzu — dars, 30 mashq, 30 test generatorlari."""
import math
import random
from fractions import Fraction

from modules.pisa_mat_g import reg, som, num, mm, _y, _o, _yopiq, fig_stolbik, fig_tortburchak, fig_chiziq, fig_pie, _svg, _t, _l, _poly
from modules import mock_fig as MF

TOP = "T11_G8_M"


def _tema(kod, nom, soha, belgi, maqsad, dars):
    return {"nom": nom, "soha": soha, "belgi": belgi, "maqsad": maqsad, "bolim": kod, "toplam": TOP, "dars": dars}


def _d(sar, doska, ovoz):
    return {"sarlavha": sar, "doska": doska, "ovoz": ovoz}


def fig_koord(pts, nom="ABCD", chiz=True):
    x0, y0, s = 150, 105, 20; body = _l((10, y0), (290, y0)) + _l((x0, 5), (x0, 205)) + _t(284, y0 - 6, "x", size=12) + _t(x0 + 8, 14, "y", size=12)
    for k in range(-7, 8):
        if k:
            body += _l((x0 + k * s, y0 - 3), (x0 + k * s, y0 + 3)) + _l((x0 - 3, y0 - k * s), (x0 + 3, y0 - k * s))
            if abs(k) % 2 == 1 or abs(k) <= 5:
                body += _t(x0 + k * s, y0 + 15, str(k), it=False, size=9) + _t(x0 - 8, y0 - k * s + 3, str(k), it=False, anchor="end", size=9)
    P = [(x0 + x * s, y0 - y * s) for x, y in pts]
    if chiz and len(P) > 2:
        body += _poly(P + [P[0]], w=1.6)
    for (px, py), n in zip(P, nom):
        body += f'<circle cx="{px}" cy="{py}" r="3" fill="#d33"/>' + _t(px + 8, py - 6, n, size=12)
    return _svg(body, 300, 210)


# ───────── M8-NAT ─────────
@reg("M8-NAT", "yopiq")
def n8_bol(rng):
    k = rng.choice([3, 4, 6, 8, 9]); n = rng.randint(120, 980) * k
    return _y(rng, f"{n} soni {k} ga qoldiqsiz bo‘linadimi? Bo‘linsa bo‘linmani yozing.", n // k, [f"{n} ÷ {k} = {n // k}."], noto=[n // k + 1, n // k - 1, n // k + 10])


@reg("M8-NAT", "yopiq")
def n8_tub(rng):
    xs = rng.sample([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37], 2); a, b = xs; 
    p = rng.choice([1, 2]); n = a * b if p else a * a * b
    return _y(rng, f"{n} sonining tub (tub ko‘paytuvchilarga ajratilgan) ko‘paytuvchilari orasidagi eng kattasi qaysi?", max(a, b), [f"{n} = " + (f"{a} · {b}" if p else f"{a} · {a} · {b}") + ".", f"Eng katta tub ko‘paytuvchi: {max(a, b)}."], noto=[min(a, b), n // min(a, b) if n // min(a, b) != max(a, b) else n, a + b])


@reg("M8-NAT", "yopiq")
def n8_ekub(rng):
    g = rng.choice([2, 3, 4, 5, 6, 7]); a, b = rng.sample([2, 3, 4, 5, 7, 9, 11], 2); A, B = a * g, b * g; from math import gcd
    return _y(rng, f"{A} va {B} sonlarining eng katta umumiy bo‘luvchisini toping.", gcd(A, B), [f"{A} = {g} · {a}, {B} = {g} · {b}; {a} va {b} o‘zaro tub.", f"EKUB = {gcd(A, B)}."], noto=[A * B // gcd(A, B), min(A, B), 1])


@reg("M8-NAT", "ochiq")
def n8_ekuk(rng):
    from math import gcd
    a, b = rng.choice([(6, 8), (4, 10), (9, 12), (12, 18), (15, 20), (8, 12)]); l = a * b // gcd(a, b)
    return _o(f"Ikki avtobus bekatdan bir vaqtda chiqdi. Birinchisi har {a} daqiqada, ikkinchisi har {b} daqiqada bekatga qaytadi.", [("a) Ular bekatda yana birga uchrashguncha necha daqiqa o‘tadi?", l), ("b) Birinchi avtobus shu vaqt ichida bekatga necha marta qaytadi?", l // a)],
              [f"a) EKUK({a}, {b}) = {l} daqiqa.", f"b) {l} ÷ {a} = {l // a} marta."])


@reg("M8-NAT", "ochiq")
def n8_qoldiq(rng):
    d = rng.choice([7, 9, 11, 12]); q = rng.randint(15, 60); r = rng.randint(1, d - 1); n = q * d + r
    return _o(f"{n} ta olma {d} ta savatga teng taqsimlandi, ortib qolganini do‘konchi oldi.", [("a) Har savatga nechtadan olma tushdi?", q), ("b) Do‘konchi nechta olma oldi?", r)], [f"{n} ÷ {d} = {q} (qoldiq {r}).", f"a) {q}. b) {r}."])


@reg("M8-NAT", "yopiq")
def n8_daraja(rng):
    a = rng.choice([2, 3, 5]); n = rng.choice([3, 4, 5, 6]) 
    return _y(rng, f"{a}^{n} nimaga teng?", a ** n, [f"{a}^{n} = " + " · ".join([str(a)] * n) + f" = {a ** n}."], noto=[a * n, a ** (n - 1), a ** n + a])


# ───────── M8-KAS ─────────
@reg("M8-KAS", "yopiq")
def k8_qosh(rng):
    b1, b2 = rng.choice([(3, 4), (2, 5), (4, 6), (3, 6), (6, 8)]); a1, a2 = rng.randint(1, b1 - 1), rng.randint(1, b2 - 1); r = Fraction(a1, b1) + Fraction(a2, b2)
    return _yopiq(rng, f"Hisoblang: {a1}/{b1} + {a2}/{b2}", f"${r.numerator}/{r.denominator}$" if r.denominator != 1 else f"${r.numerator}$", [f"Umumiy maxraj: {b1 * b2 // math.gcd(b1, b2)}.", f"Natija: {r.numerator}/{r.denominator}" + (" (qisqartirilgan)." if True else ".")],
                  noto=[f"${a1 + a2}/{b1 + b2}$", f"${(r + Fraction(1, 5)).numerator}/{(r + Fraction(1, 5)).denominator}$", f"${(r - Fraction(1, 7)).numerator}/{(r - Fraction(1, 7)).denominator}$"], tartib=False)


@reg("M8-KAS", "yopiq")
def k8_kopayt(rng):
    a, b, c, d = rng.sample([2, 3, 4, 5, 6, 7], 4); r = Fraction(a, b) * Fraction(c, d)
    return _yopiq(rng, f"Hisoblang: {a}/{b} · {c}/{d}", f"${r.numerator}/{r.denominator}$" if r.denominator != 1 else f"${r.numerator}$", [f"Suratlarni ko‘paytirib, maxrajlarni ko‘paytiramiz: {a * c}/{b * d}.", f"Qisqartirsak: {r.numerator}/{r.denominator}."], noto=[f"${a * d}/{b * c}$", f"${a + c}/{b + d}$", f"${a * c}/{b + d}$"], tartib=False)


@reg("M8-KAS", "yopiq")
def k8_onli(rng):
    a = rng.randint(12, 95) / 10; b = rng.choice([2, 4, 5]); r = Fraction(round(a * 10), 10) * b
    return _y(rng, f"Hisoblang: {num(Fraction(round(a * 10), 10))} · {b}", r, [f"{num(Fraction(round(a * 10), 10))} · {b} = {num(r)}."], noto=[r / 10, r * 10, r + 1])


@reg("M8-KAS", "ochiq")
def k8_masala(rng):
    n = rng.choice([48, 60, 72, 90, 120]); 
    return _o(f"Yo‘lning {n} km i bor. Birinchi kuni uning 1/3 qismi, ikkinchi kuni qolgan masofaning 1/2 qismi bosib o‘tildi.", [("a) Birinchi kuni necha km?", Fraction(n, 3)), ("b) Ikkinchi kuni necha km?", Fraction(n, 3))],
              [f"a) {n} · 1/3 = {num(Fraction(n, 3))}.", f"b) Qolgan: {n} − {num(Fraction(n, 3))} = {num(n - Fraction(n, 3))}; uning yarmi = {num((n - Fraction(n, 3)) / 2)}."]) if n % 3 == 0 else None


@reg("M8-KAS", "ochiq")
def k8_aralash(rng):
    w = rng.randint(2, 5); a, b = rng.choice([(1, 2), (1, 4), (3, 4), (1, 3), (2, 3)]); T = Fraction(w * b + a, b)
    return _o(f"Qadoqda {w} {a}/{b} kg guruch bor. Oshpaz {w - 1} kg ishlatdi.", [("a) Qadoqda necha kg qoldi? (kasr yoki o‘nli kasr)", T - (w - 1)), ("b) Qadoqning dastlabki massasi noto‘g‘ri kasr ko‘rinishida qanday? (kasr)", T)], [f"a) {w} {a}/{b} − {w - 1} = 1 {a}/{b} = {num(T - (w - 1))}.", f"b) {w} {a}/{b} = ({w}·{b} + {a})/{b} = {T.numerator}/{T.denominator}."])


@reg("M8-KAS", "ochiq")
def k8_taqqos(rng):
    a, b = rng.choice([(3, 5), (2, 3), (5, 8), (7, 10), (3, 4)]); c = rng.randint(1, 9)
    x = Fraction(a, b)
    return _o(f"Ikki kasrni taqqoslang: {a}/{b} va 0,{c}5.", [("a) {0}/{1} ning o‘nli kasr ko‘rinishi nechaga teng?".format(a, b), x), ("b) 0,{0}5 va {1} dan qaysi biri kattaroq? Kattasini yozing.".format(c, num(x)), max(x, Fraction(c * 10 + 5, 100)))], [f"a) {a} ÷ {b} = {num(x)}.", f"b) 0,{c}5 = {num(Fraction(c * 10 + 5, 100))}. Kattasi: {num(max(x, Fraction(c * 10 + 5, 100)))}."])


# ───────── M8-BUT ─────────
@reg("M8-BUT", "yopiq")
def b8_harorat(rng):
    a = rng.randint(-15, -2); d = rng.randint(5, 18)
    return _y(rng, f"Ertalab havo harorati {a}°C edi, tushga kelib {d}°C ga isidi. Tushdagi harorat necha °C?", a + d, [f"{a} + {d} = {a + d}."], noto=[a - d, -(a + d), d - a])


@reg("M8-BUT", "yopiq")
def b8_amal(rng):
    a = rng.randint(-20, -3); b = rng.randint(-15, -2)
    return _y(rng, f"Hisoblang: ({a}) − ({b})", a - b, [f"Ayirish o‘rniga qarama-qarshi sonni qo‘shamiz: {a} + {-b} = {a - b}."], noto=[a + b, b - a, -(a - b)])


@reg("M8-BUT", "yopiq")
def b8_kopayt(rng):
    a = rng.randint(-9, -2); b = rng.randint(-9, 9)
    while b in (0, 1): b = rng.randint(-9, 9)
    return _y(rng, f"Hisoblang: ({a}) · ({b})", a * b, [f"Ishoralar: {'minus · minus = plyus' if b < 0 else 'minus · plyus = minus'}.", f"{abs(a)} · {abs(b)} = {abs(a * b)}, demak {a * b}."], noto=[-a * b, a + b, a * b + 2])


@reg("M8-BUT", "ochiq")
def b8_chuqurlik(rng):
    d = rng.randint(20, 80); u = rng.randint(5, 18)
    return _o(f"Suvosti kemasi dengiz sathidan {d} m pastda turibdi. U {u} m ga ko‘tarildi, keyin yana {u * 2} m ga cho‘kdi.", [("a) Ko‘tarilgandan keyin dengiz sathiga nisbatan qayerda? (m, pastda manfiy)", -d + u), ("b) Oxirgi holat (m)?", -d + u - 2 * u)], [f"a) −{d} + {u} = {-d + u}.", f"b) {-d + u} − {2 * u} = {-d - u}."])


@reg("M8-BUT", "ochiq")
def b8_tartib(rng):
    xs = rng.sample(range(-12, 13), 5)
    return _o(f"Sonlar: {', '.join(map(str, xs))}.", [("a) Eng kichigi qaysi?", min(xs)), ("b) Ularning yig‘indisi nechaga teng?", sum(xs))], [f"a) Eng kichik: {min(xs)}.", f"b) {' + '.join(f'({x})' for x in xs)} = {sum(xs)}."])


@reg("M8-BUT", "yopiq")
def b8_modul(rng):
    a = rng.randint(-25, -3); b = rng.randint(3, 25)
    return _y(rng, f"|{a}| + |{b}| nimaga teng?", abs(a) + abs(b), [f"|{a}| = {abs(a)}, |{b}| = {b}.", f"{abs(a)} + {b} = {abs(a) + b}."], noto=[a + b, abs(a + b) if abs(a + b) != abs(a) + b else 0, b - abs(a)])


# ───────── M8-NIS: nisbat, proporsiya, foiz ─────────
@reg("M8-NIS", "yopiq")
def i8_nisbat(rng):
    a, b = rng.choice([(2, 3), (3, 5), (4, 7), (1, 4)]); k = rng.randint(3, 12); T = (a + b) * k
    return _y(rng, f"Sinfda o‘g‘il va qiz bolalar soni {a} : {b} nisbatda. Sinfda {T} o‘quvchi bor. Qizlar necha nafar?", b * k, [f"{a} + {b} = {a + b} qism; 1 qism = {T} ÷ {a + b} = {k}.", f"Qizlar: {b} · {k} = {b * k}."], noto=[a * k, T - k, (a + b) * 2])


@reg("M8-NIS", "yopiq")
def i8_prop(rng):
    a = rng.choice([3, 4, 5, 6]); b = a * rng.choice([2, 3, 4]); c = rng.choice([5, 7, 9]); x = c * b // a
    return _y(rng, f"{a} : {b} = {c} : x. x ni toping.", x, [f"Proporsiyada o‘rtalar ko‘paytmasi = chetlar ko‘paytmasi: {a} · x = {b} · {c}.", f"x = {b * c} ÷ {a} = {x}."], noto=[c + b - a, b * c, a * c])


@reg("M8-NIS", "yopiq")
def i8_foiz(rng):
    p = rng.choice([5, 8, 12, 15, 25]); n = rng.choice([200, 400, 500, 800]) 
    return _y(rng, f"{n} ming so‘mning {p}% i necha ming so‘m?", Fraction(n * p, 100), [f"{n} · {p}/100 = {num(Fraction(n * p, 100))}."], noto=[p, n - Fraction(n * p, 100), Fraction(n * p, 10)])


@reg("M8-NIS", "ochiq")
def i8_chegirma(rng):
    P = rng.choice([80, 120, 160, 250, 400]); d = rng.choice([10, 15, 20, 25]); 
    return _o(f"Kitob narxi {P} ming so‘m. Chegirma {d}% bo‘ldi.", [("a) Chegirma necha ming so‘m?", Fraction(P * d, 100)), ("b) Yangi narx necha ming so‘m?", P - Fraction(P * d, 100))], [f"a) {P} · {d}/100 = {num(Fraction(P * d, 100))}.", f"b) {P} − {num(Fraction(P * d, 100))} = {num(P - Fraction(P * d, 100))}."])


@reg("M8-NIS", "ochiq")
def i8_foizoshish(rng):
    a = rng.choice([40, 50, 80, 120, 200]); p = rng.choice([10, 20, 25, 50]); b = Fraction(a * (100 + p), 100)
    return _o(f"Maktab ishlab chiqarish to‘garagida o‘quvchilar soni {a} tadan {num(b)} taga ko‘paydi.", [("a) Necha foizga ko‘paydi?", p), ("b) Shu foizda yana ko‘paysa, to‘garakda necha kishi bo‘ladi? (oldingi sondan {0}% ko‘p)".format(p), b * (100 + p) / 100)], [f"a) ({num(b)} − {a}) ÷ {a} · 100 = {p}%.", f"b) {num(b)} · {100 + p}/100 = {num(b * (100 + p) / 100)}."])


@reg("M8-NIS", "ochiq")
def i8_tezlik(rng):
    v1 = rng.choice([40, 60, 80]); t1 = rng.choice([3, 4, 6]); v2 = rng.choice([x for x in (30, 40, 48, 60, 120) if (v1 * t1) % x == 0]) if True else 60
    return _o(f"Avtomobil {v1} km/soat tezlikda {t1} soatda yo‘lni bosib o‘tadi.", [("a) Yo‘l necha km?", v1 * t1), (f"b) Tezlik {v2} km/soat bo‘lsa, necha soat ketadi? (teskari proporsionallik)", Fraction(v1 * t1, v2))], [f"a) {v1} · {t1} = {v1 * t1}.", f"b) {v1 * t1} ÷ {v2} = {num(Fraction(v1 * t1, v2))} soat."])


# ───────── M8-QON ─────────
@reg("M8-QON", "yopiq")
def q8_arif(rng):
    a = rng.randint(-5, 10); d = rng.choice([3, 4, 5, 7]); n = rng.choice([10, 12, 15, 20]); 
    return _y(rng, f"Ketma-ketlik: {a}, {a + d}, {a + 2 * d}, … {n}-hadini toping.", a + (n - 1) * d, [f"Har had {d} ga oshadi: a_n = {a} + (n − 1)·{d}.", f"a_{n} = {a} + {(n - 1) * d} = {a + (n - 1) * d}."], noto=[a + n * d, a * n, a + (n - 2) * d])


@reg("M8-QON", "yopiq")
def q8_geom(rng):
    a = rng.choice([1, 2, 3]); r = rng.choice([2, 3]); n = rng.choice([5, 6, 7]); 
    return _y(rng, f"Ketma-ketlik: {a}, {a * r}, {a * r * r}, … {n}-hadi nechaga teng?", a * r ** (n - 1), [f"Har had {r} marta katta: a_n = {a} · {r}^(n−1).", f"a_{n} = {a} · {r}^{n - 1} = {a * r ** (n - 1)}."], noto=[a * r * (n - 1), a + (n - 1) * r, a * r ** n])


@reg("M8-QON", "yopiq")
def q8_formula(rng):
    k = rng.choice([2, 3, 4, 5]); b = rng.choice([-1, 1, 2, 3]); n = rng.randint(6, 12)
    return _y(rng, f"Ketma-ketlikning n-chi hadi a_n = {k}n {'+' if b > 0 else '−'} {abs(b)} formula bilan berilgan. a_{n} nechaga teng?", k * n + b, [f"a_{n} = {k}·{n} {'+' if b > 0 else '−'} {abs(b)} = {k * n + b}."], noto=[k * n - b, k * (n + b), k + n + b])


@reg("M8-QON", "ochiq")
def q8_yigindi(rng):
    n = rng.choice([10, 20, 50, 100]); 
    return _o(f"1 dan {n} gacha natural sonlar yig‘indisini topamiz.", [("a) Birinchi va oxirgi sonlar yig‘indisi?", n + 1), ("b) 1 + 2 + … + {0} yig‘indisi?".format(n), n * (n + 1) // 2)], [f"a) 1 + {n} = {n + 1}.", f"b) n(n + 1)/2 = {n}·{n + 1}/2 = {n * (n + 1) // 2}."])


@reg("M8-QON", "ochiq")
def q8_kvartira(rng):
    a = rng.choice([5, 8, 10]); d = rng.choice([2, 3, 4]); n = rng.choice([8, 10, 12])
    return _o(f"Teatrda 1-qatorda {a} o‘rin, har keyingi qatorda {d} tadan ko‘p. Jami {n} qator.", [("a) Oxirgi qatorda nechta o‘rin?", a + (n - 1) * d), ("b) Zalda jami nechta o‘rin?", n * (2 * a + (n - 1) * d) // 2)], [f"a) {a} + {n - 1}·{d} = {a + (n - 1) * d}.", f"b) {n}·({a} + {a + (n - 1) * d})/2 = {n * (2 * a + (n - 1) * d) // 2}."])


@reg("M8-QON", "ochiq")
def q8_ko_payish(rng):
    a = rng.choice([3, 5, 10]); n = rng.choice([4, 5, 6]); 
    return _o(f"Bakteriya har soatda 2 marta ko‘payadi. Boshida {a} ta bor.", [(f"a) {n} soatdan keyin nechta bo‘ladi?", a * 2 ** n), (f"b) {n - 1} soatdan keyin nechta edi?", a * 2 ** (n - 1))], [f"a) {a} · 2^{n} = {a * 2 ** n}.", f"b) {a} · 2^{n - 1} = {a * 2 ** (n - 1)}."])


# ───────── M8-IFO: algebraik ifodalar ─────────
@reg("M8-IFO", "yopiq")
def f8_qiymat(rng):
    a = rng.randint(2, 7); b = rng.randint(-8, 8); x = rng.randint(-4, 6)
    return _y(rng, f"x = {x} bo‘lganda {a}x {'+' if b >= 0 else '−'} {abs(b)} ifodaning qiymati nechaga teng?", a * x + b, [f"{a}·({x}) {'+' if b >= 0 else '−'} {abs(b)} = {a * x} {'+' if b >= 0 else '−'} {abs(b)} = {a * x + b}."], noto=[a * x - b, a + x + b, a * (x + b)])


@reg("M8-IFO", "yopiq")
def f8_oxshash(rng):
    a, c = rng.sample(range(3, 9), 2); b, d = rng.sample(range(1, 9), 2)
    return _yopiq(rng, f"Soddalashtiring: {a}x + {b} + {c}x − {d}", f"${a + c}x {'+' if b - d >= 0 else '−'} {abs(b - d)}$" if b != d else f"${a + c}x$", [f"O‘xshash hadlar: ({a}x + {c}x) + ({b} − {d}).", f"= {a + c}x {'+' if b - d >= 0 else '−'} {abs(b - d)}."],
                  noto=[f"${a + c}x {'+' if b + d >= 0 else '−'} {abs(b + d)}$", f"${a * c}x {'+' if b - d >= 0 else '−'} {abs(b - d)}$", f"${a + c + b - d}x$"], tartib=False) if b != d else _y(rng, f"x = 1 bo‘lganda {a}x + {c}x ning qiymati?", a + c, [f"({a} + {c})·1 = {a + c}."], noto=[a * c, a + c + 1, a])


@reg("M8-IFO", "yopiq")
def f8_qavs(rng):
    k = rng.randint(2, 6); a = rng.randint(1, 7); b = rng.randint(1, 7)
    return _yopiq(rng, f"Qavslarni oching: {k}(x + {a}) − {b}", f"${k}x + {k * a - b}$" if k * a - b >= 0 else f"${k}x − {b - k * a}$", [f"{k}·x + {k}·{a} − {b} = {k}x + {k * a} − {b}.", f"= {k}x {'+' if k * a - b >= 0 else '−'} {abs(k * a - b)}."], noto=[f"${k}x + {a - b if a - b >= 0 else '(' + str(a - b) + ')'}$".replace("+ (", "− (").replace("(-", "(").replace("))", ")"), f"${k}x + {k * a + b}$", f"${k + a}x − {b}$"], tartib=False)


@reg("M8-IFO", "ochiq")
def f8_formula(rng):
    a = rng.choice([8, 10, 12, 15]); b = rng.choice([20, 30, 50]); n = rng.choice([3, 5, 7]); 
    return _o(f"Usta ish haqi uchun formula: S = {a}·t + {b} (t — soat, S — ming so‘m).", [(f"a) t = {n} soatda S necha ming so‘m?", a * n + b), (f"b) S = {a * n + b + a} bo‘lsa, t nechaga teng?", n + 1)], [f"a) S = {a}·{n} + {b} = {a * n + b}.", f"b) {a}·t + {b} = {a * n + b + a} → t = {n + 1}."])


@reg("M8-IFO", "ochiq")
def f8_perimetr(rng):
    a = rng.randint(3, 9); 
    return _o(f"To‘rtburchak tomonlari: uzunligi ({a} + x) sm, eni {a} sm.", [("a) x = 4 bo‘lganda perimetr necha sm?", 2 * (a + 4 + a)), ("b) x = 4 bo‘lganda yuza necha sm²?", (a + 4) * a)], [f"a) P = 2(({a} + 4) + {a}) = {2 * (a + 4 + a)}.", f"b) S = ({a} + 4)·{a} = {(a + 4) * a}."])


@reg("M8-IFO", "yopiq")
def f8_daraja(rng):
    a = rng.randint(2, 4); n = rng.randint(2, 4); m = rng.randint(2, 4)
    return _y(rng, f"{a}^{n} · {a}^{m} ni {a} ning darajasi ko‘rinishida yozing. Daraja ko‘rsatkichi nechaga teng?", n + m, [f"Asoslari bir xil darajalar ko‘paytirilganda ko‘rsatkichlar qo‘shiladi: {n} + {m} = {n + m}."], noto=[n * m, n + m + 1, abs(n - m) or 1])


# ───────── M8-TEN: tenglamalar, formulalar, funksiyalar ─────────
@reg("M8-TEN", "yopiq")
def t8_chiziqli(rng):
    a = rng.randint(2, 7); x = rng.randint(-5, 9); b = rng.randint(-9, 9); c = a * x + b
    return _y(rng, f"Tenglamani yeching: {a}x {'+' if b >= 0 else '−'} {abs(b)} = {c}", x, [f"{a}x = {c} {'−' if b >= 0 else '+'} {abs(b)} = {c - b}.", f"x = {c - b} ÷ {a} = {x}."], noto=[x + 1, x - 1, c - b])


@reg("M8-TEN", "yopiq")
def t8_funksiya(rng):
    k = rng.choice([2, 3, -2, -1, 4]); b = rng.randint(-5, 5); x = rng.randint(-3, 4)
    return _y(rng, f"f(x) = {k}x {'+' if b >= 0 else '−'} {abs(b)}. f({x}) nechaga teng?", k * x + b, [f"f({x}) = {k}·({x}) {'+' if b >= 0 else '−'} {abs(b)} = {k * x + b}."], noto=[k * x - b, k + x + b, -(k * x + b)])


@reg("M8-TEN", "yopiq")
def t8_grafik(rng):
    b = rng.choice([5, 10, 15]); k = rng.choice([5, 10]); xm = 5; x = rng.randint(1, 5)
    q = _y(rng, f"Grafikda y = {k}x + {b} funksiya tasvirlangan (x — soat, y — km). x = {x} bo‘lganda y nechaga teng?", k * x + b, [f"y = {k}·{x} + {b} = {k * x + b}."], noto=[k * x, b * x, k + b + x])
    q["rasm"] = fig_chiziq(b, k, xm, "x", "y", sarlavha=f"y = {k}x + {b}"); return q


@reg("M8-TEN", "ochiq")
def t8_ikki(rng):
    a = rng.randint(2, 5); x = rng.randint(2, 9); b = rng.randint(1, 6); c = rng.randint(1, 4); 
    return _o(f"{a}(x + {b}) = {a * (x + b)}.", [("a) x ni toping.", x), (f"b) {a}(x + {b}) = {a * (x + b)} da x + {b} nechaga teng?", x + b)], [f"a) x + {b} = {a * (x + b)} ÷ {a} = {x + b}, x = {x}.", f"b) {x + b}."])


@reg("M8-TEN", "ochiq")
def t8_masala(rng):
    a = rng.choice([3, 4, 5]); x = rng.randint(5, 20); T = (a + 1) * x
    return _o(f"Ikki sonning yig‘indisi {T}, biri ikkinchisidan {a} marta katta.", [("a) Kichik sonni toping.", x), ("b) Katta sonni toping.", a * x)], [f"x + {a}x = {T} → {a + 1}x = {T} → x = {x}.", f"Katta son: {a}·{x} = {a * x}."])


@reg("M8-TEN", "ochiq")
def t8_formulaF(rng):
    c = rng.choice([0, 10, 20, 30, 40, 100]); 
    return _o("Selsiy va Farengeyt: F = 1,8·C + 32.", [(f"a) C = {c} bo‘lganda F nechaga teng?", Fraction(18 * c, 10) + 32), ("b) F = 32 bo‘lsa C nechaga teng?", 0)], [f"a) F = 1,8·{c} + 32 = {num(Fraction(18 * c, 10) + 32)}.", "b) 32 = 1,8·C + 32 → C = 0."])


# ───────── M8-SHA ─────────
@reg("M8-SHA", "yopiq")
def s8_uchburchak(rng):
    a = rng.randint(30, 80); b = rng.randint(30, 80); 
    q = _y(rng, f"Uchburchakning ikki burchagi {a}° va {b}°. Uchinchi burchagi necha gradus?", 180 - a - b, [f"180° − {a}° − {b}° = {180 - a - b}°."], noto=[a + b, 360 - a - b, 90 - a])
    return q


@reg("M8-SHA", "yopiq")
def s8_ichki(rng):
    n = rng.choice([5, 6, 8, 9, 10, 12]); 
    return _y(rng, f"Muntazam {n} burchakning bir ichki burchagi necha gradus?", Fraction((n - 2) * 180, n), [f"Ichki burchaklar yig‘indisi: ({n} − 2)·180° = {(n - 2) * 180}°.", f"Bir burchak: {(n - 2) * 180} ÷ {n} = {num(Fraction((n - 2) * 180, n))}°."], noto=[Fraction(360, n), Fraction((n - 2) * 180, n) + 10, (n - 2) * 90])


@reg("M8-SHA", "yopiq")
def s8_ox(rng):
    k = rng.choice([2, 3, 4]); a = rng.choice([3, 4, 5, 6]); 
    return _y(rng, f"Ikki o‘xshash uchburchakning o‘xshashlik koeffitsienti {k}. Kichigining tomoni {a} sm bo‘lsa, kattasining mos tomoni necha sm?", a * k, [f"Mos tomonlar nisbati {k}: {a}·{k} = {a * k}."], noto=[a + k, a * k * k, Fraction(a, k)])


@reg("M8-SHA", "ochiq")
def s8_pifagor(rng):
    a, b, c = rng.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17), (7, 24, 25), (20, 21, 29)])
    q = _o(f"To‘g‘ri burchakli uchburchakning katetlari {a} sm va {b} sm.", [("a) Gipotenuzasi necha sm?", c), ("b) Perimetri necha sm?", a + b + c)], [f"a) c² = {a}² + {b}² = {a * a} + {b * b} = {c * c}, c = {c}.", f"b) {a} + {b} + {c} = {a + b + c}."])
    return q


@reg("M8-SHA", "ochiq")
def s8_teng_yon(rng):
    a = rng.choice([40, 50, 70, 80]); 
    return _o(f"Teng yonli uchburchakning uchidagi burchagi {a}°.", [("a) Asosidagi har bir burchak necha gradus?", Fraction(180 - a, 2)), ("b) Asosidagi burchaklar yig‘indisi necha gradus?", 180 - a)], [f"a) (180° − {a}°) ÷ 2 = {num(Fraction(180 - a, 2))}°.", f"b) 180° − {a}° = {180 - a}°."])


@reg("M8-SHA", "yopiq")
def s8_parallel(rng):
    a = rng.choice([50, 60, 70, 110, 120, 130]); 
    return _y(rng, f"Ikki parallel to‘g‘ri chiziqni kesuvchi kesgan. Ichki bir tomonli burchaklardan biri {a}°. Ikkinchisi necha gradus?", 180 - a, ["Parallel chiziqlarda ichki bir tomonli burchaklar yig‘indisi 180°.", f"180° − {a}° = {180 - a}°."], noto=[a, 90 - a if a < 90 else a - 90, 360 - a])


# ───────── M8-OLC ─────────
@reg("M8-OLC", "yopiq")
def o8_doira(rng):
    r = rng.choice([2, 5, 7, 10, 3]); 
    return _y(rng, f"Radiusi {r} sm bo‘lgan doiraning yuzi nechaga teng? (π ≈ 3,14)", Fraction(314, 100) * r * r, [f"S = π · r² = 3,14 · {r}² = 3,14 · {r * r} = {num(Fraction(314, 100) * r * r)}."], noto=[Fraction(314, 100) * 2 * r, Fraction(314, 100) * r, Fraction(314, 100) * r * r * 2])


@reg("M8-OLC", "yopiq")
def o8_hajm(rng):
    a, b, c = rng.randint(3, 10), rng.randint(2, 8), rng.randint(2, 7)
    q = _y(rng, f"To‘g‘ri to‘rtburchakli prizmaning o‘lchamlari {a} × {b} × {c} sm. Hajmi necha sm³?", a * b * c, [f"V = a·b·c = {a}·{b}·{c} = {a * b * c}."], noto=[2 * (a * b + b * c + a * c), a + b + c, a * b * c + a])
    q["rasm"] = MF.prizma(a, b, c); return q


@reg("M8-OLC", "yopiq")
def o8_silindr(rng):
    r = rng.choice([1, 2, 3, 5]); h = rng.choice([4, 5, 10]); 
    q = _y(rng, f"Silindr asosining radiusi {r} sm, balandligi {h} sm. Hajmi necha sm³? (π ≈ 3,14)", Fraction(314, 100) * r * r * h, [f"V = π·r²·h = 3,14·{r * r}·{h} = {num(Fraction(314, 100) * r * r * h)}."], noto=[Fraction(314, 100) * r * h, Fraction(314, 100) * r * r, Fraction(314, 100) * r * r * h / 3])
    q["rasm"] = MF.silindr(r, h); return q


@reg("M8-OLC", "ochiq")
def o8_trapet(rng):
    a = rng.choice([6, 8, 10]); b = rng.choice([12, 14, 16, 20]); h = rng.choice([4, 5, 6, 8]); 
    return _o(f"Trapetsiyaning asoslari {a} sm va {b} sm, balandligi {h} sm.", [("a) Yuzi necha sm²?", Fraction((a + b) * h, 2)), ("b) O‘rta chizig‘i necha sm?", Fraction(a + b, 2))], [f"a) S = (a + b)·h/2 = ({a} + {b})·{h}/2 = {num(Fraction((a + b) * h, 2))}.", f"b) (a + b)/2 = {num(Fraction(a + b, 2))}."])


@reg("M8-OLC", "ochiq")
def o8_aylana(rng):
    d = rng.choice([10, 20, 30, 50]); 
    return _o(f"G‘ildirak diametri {d} sm. (π ≈ 3,14)", [("a) Aylana uzunligi necha sm?", Fraction(314, 100) * d), ("b) G‘ildirak bir marta to‘liq aylanganda necha sm yo‘l yuradi?", Fraction(314, 100) * d)], [f"a) C = π·d = 3,14·{d} = {num(Fraction(314, 100) * d)}.", "b) Bir aylanishda aylana uzunligiga teng masofa."])


@reg("M8-OLC", "ochiq")
def o8_birlik(rng):
    a = rng.choice([2, 3, 5]); b = rng.choice([4, 6, 8]); 
    return _o(f"Hovuz uzunligi {a} m, eni {b} m, chuqurligi 1,5 m.", [("a) Hajmi necha m³?", a * b * Fraction(3, 2)), ("b) U necha litr suv sig‘diradi? (1 m³ = 1000 l)", a * b * Fraction(3, 2) * 1000)], [f"a) {a}·{b}·1,5 = {num(a * b * Fraction(3, 2))}.", f"b) {num(a * b * Fraction(3, 2))}·1000 = {num(a * b * Fraction(3, 2) * 1000)}."])


# ───────── M8-JOY: koordinatalar ─────────
@reg("M8-JOY", "yopiq")
def j8_nuqta(rng):
    x, y = rng.randint(-5, 5), rng.randint(-5, 5)
    while x == 0 or y == 0: x, y = rng.randint(-5, 5), rng.randint(-5, 5)
    ch = "I" if x > 0 and y > 0 else "II" if x < 0 and y > 0 else "III" if x < 0 else "IV"
    q = _yopiq(rng, f"A({x}; {y}) nuqta qaysi koordinata choragida joylashgan?", f"{ch} chorak", ["x>0, y>0 — I; x<0, y>0 — II; x<0, y<0 — III; x>0, y<0 — IV."], noto=[f"{c} chorak" for c in ("I", "II", "III", "IV") if c != ch], tartib=False)
    q["rasm"] = fig_koord([(x, y)], "A", chiz=False); return q


@reg("M8-JOY", "yopiq")
def j8_masofa(rng):
    x1 = rng.randint(-4, 2); d = rng.randint(2, 5); y = rng.randint(-4, 4)
    q = _y(rng, f"A({x1}; {y}) va B({x1 + d}; {y}) nuqtalar orasidagi masofa nechaga teng?", d, [f"y bir xil, shuning uchun masofa |x₂ − x₁| = {d}."], noto=[d + 1, d * 2, abs(x1) + abs(x1 + d) if abs(x1) + abs(x1 + d) != d else d + 3])
    q["rasm"] = fig_koord([(x1, y), (x1 + d, y)], "AB", chiz=False); return q


@reg("M8-JOY", "yopiq")
def j8_akslantir(rng):
    x, y = rng.randint(1, 5), rng.randint(1, 5)
    return _yopiq(rng, f"A({x}; {y}) nuqtaning Ox o‘qiga nisbatan simmetrik nuqtasi qaysi?", f"$({x}; {-y})$", ["Ox o‘qiga nisbatan simmetriyada x o‘zgarmaydi, y ishorasi o‘zgaradi."], noto=[f"$({-x}; {y})$", f"$({-x}; {-y})$", f"$({y}; {x})$"], tartib=False)


@reg("M8-JOY", "ochiq")
def j8_tortburchak(rng):
    x, y = rng.randint(-4, 0), rng.randint(-3, 0); a, b = rng.randint(2, 5), rng.randint(2, 4)
    pts = [(x, y), (x + a, y), (x + a, y + b), (x, y + b)]
    q = _o(f"Koordinata tekisligida to‘rtburchak A({x}; {y}), B({x + a}; {y}), C({x + a}; {y + b}), D({x}; {y + b}) uchlarida berilgan.", [("a) Perimetri nechaga teng?", 2 * (a + b)), ("b) Yuzi nechaga teng?", a * b)], [f"AB = {a}, BC = {b}.", f"a) P = 2·({a} + {b}) = {2 * (a + b)}.", f"b) S = {a}·{b} = {a * b}."])
    q["rasm"] = fig_koord(pts, "ABCD"); return q


@reg("M8-JOY", "ochiq")
def j8_ko_chirish(rng):
    x, y = rng.randint(-3, 3), rng.randint(-3, 3); dx, dy = rng.randint(1, 4), rng.randint(-3, 3)
    return _o(f"A({x}; {y}) nuqta ({dx}; {dy}) vektor bo‘yicha parallel ko‘chirildi.", [("a) Yangi nuqtaning x koordinatasi?", x + dx), ("b) Yangi nuqtaning y koordinatasi?", y + dy)], [f"a) {x} + {dx} = {x + dx}.", f"b) {y} + ({dy}) = {y + dy}."])


@reg("M8-JOY", "ochiq")
def j8_chiziqli(rng):
    k = rng.choice([1, 2, 3]); b = rng.randint(-2, 4)
    q = _o(f"y = {k}x {'+' if b >= 0 else '−'} {abs(b)} funksiya grafigi berilgan.", [("a) Grafik Oy o‘qini qaysi y qiymatida kesadi?", b), ("b) x = 2 da y nechaga teng?", 2 * k + b)], [f"a) x = 0: y = {b}.", f"b) y = {k}·2 {'+' if b >= 0 else '−'} {abs(b)} = {2 * k + b}."])
    return q


# ───────── M8-TAS, M8-TAH ─────────
@reg("M8-TAS", "yopiq")
def d8_qaysi(rng):
    return _yopiq(rng, rng.choice(["Bir oy davomida kunlik haroratning o‘zgarishini ko‘rsatish uchun qaysi diagramma eng mos?", "Sinfdagi bolalarning sevimli fanlari ulushini ko‘rsatish uchun qaysi diagramma mos?"]) if False else "Byudjetning qismlarga (ulushlarga) bo‘linishini ko‘rsatish uchun qaysi diagramma eng mos?", "Doira diagramma", ["Ulushlar uchun doira diagramma qulay."], noto=["Chiziqli grafik", "Nuqtali diagramma", "Jadvalsiz ro‘yxat"], tartib=False)


@reg("M8-TAS", "yopiq")
def d8_oraliq(rng):
    xs = rng.sample(range(10, 60), 6)
    return _y(rng, f"Ma’lumotlar: {', '.join(map(str, xs))}. Oraliq (eng katta − eng kichik) nechaga teng?", max(xs) - min(xs), [f"{max(xs)} − {min(xs)} = {max(xs) - min(xs)}."], noto=[max(xs), min(xs), sum(xs) // 6])


@reg("M8-TAS", "ochiq")
def d8_pie(rng):
    n = ["A", "B", "V", "G"]; v = rng.choice([[40, 30, 20, 10], [50, 25, 15, 10], [35, 35, 20, 10]]); T = rng.choice([200, 400, 600])
    q = _o(f"Doira diagrammada {T} nafar so‘rovnomada qatnashganlarning javoblari ko‘rsatilgan.", [("a) A javobni tanlaganlar necha kishi?", T * v[0] // 100), ("b) V va G javoblarni tanlaganlar jami necha kishi?", T * (v[2] + v[3]) // 100)], [f"a) {T}·{v[0]}/100 = {T * v[0] // 100}.", f"b) ({v[2]} + {v[3]})% = {v[2] + v[3]}%; {T}·{v[2] + v[3]}/100 = {T * (v[2] + v[3]) // 100}."])
    q["rasm"] = fig_pie(n, v, "So‘rovnoma"); return q


@reg("M8-TAS", "ochiq")
def d8_tab(rng):
    n = ["Dush", "Sesh", "Chor", "Pay", "Jum"]; v = [rng.randint(4, 20) * 5 for _ in range(5)]
    q = _o("Diagrammada beshta kunda sotilgan daftarlar soni ko‘rsatilgan.", [("a) Jami nechta daftar sotilgan?", sum(v)), ("b) O‘rtacha kunlik sotuv nechta?", Fraction(sum(v), 5))], [f"a) {' + '.join(map(str, v))} = {sum(v)}.", f"b) {sum(v)}/5 = {num(Fraction(sum(v), 5))}."])
    q["rasm"] = fig_stolbik(n, v, "Sotilgan daftar"); return q


@reg("M8-TAS", "yopiq")
def d8_chastota(rng):
    f = [rng.randint(2, 9) for _ in range(4)]
    return _y(rng, f"Chastota jadvali: 1 ball — {f[0]} o‘quvchi, 2 ball — {f[1]}, 3 ball — {f[2]}, 4 ball — {f[3]}. Hammasi nechta o‘quvchi?", sum(f), [" + ".join(map(str, f)) + f" = {sum(f)}."], noto=[sum(f) + 2, sum(f) - 1, max(f) * 4])


@reg("M8-TAS", "yopiq")
def d8_foiz(rng):
    T = rng.choice([20, 40, 50, 80]); a = T * rng.choice([10, 25, 50, 75]) // 100
    return _y(rng, f"{T} o‘quvchining {a} nafari ovoz berdi. Bu necha foiz?", 100 * a // T, [f"{a} ÷ {T} · 100 = {100 * a // T}%."], noto=[a, 100 - 100 * a // T, T - a])


@reg("M8-TAH", "yopiq")
def h8_ortacha(rng):
    m = rng.choice([60, 65, 70, 75, 80]); xs = [m + rng.randint(-10, 10) for _ in range(4)]; xs.append(m * 5 - sum(xs))
    return _y(rng, f"Besh test ballari: {', '.join(map(str, xs))}. O‘rtacha ball nechaga teng?", m, [f"Yig‘indi {sum(xs)}; {sum(xs)} ÷ 5 = {m}."], noto=[max(xs), sorted(xs)[2] if sorted(xs)[2] != m else m + 3, m + 5])


@reg("M8-TAH", "yopiq")
def h8_mediana(rng):
    xs = rng.sample(range(5, 50), 5); xs2 = sorted(xs); 
    return _y(rng, f"Ma’lumotlar: {', '.join(map(str, xs))}. Mediana nechaga teng?", xs2[2], [f"Tartiblaymiz: {', '.join(map(str, xs2))}.", f"O‘rtadagi son: {xs2[2]}."], noto=[xs[2] if xs[2] != xs2[2] else xs2[1], sum(xs) // 5 if sum(xs) // 5 != xs2[2] else xs2[2] + 2, max(xs)])


@reg("M8-TAH", "yopiq")
def h8_yangi(rng):
    n = rng.choice([4, 5, 6]); m = rng.choice([70, 75, 80]); k = rng.choice([2, 3, 5]); m2 = m + k; yangi = m2 * (n + 1) - m * n
    return _y(rng, f"{n} ta bahoning o‘rtachasi {m}. Yana bitta baho qo‘shilgach o‘rtacha {m2} bo‘ldi. Yangi baho nechaga teng?", yangi, [f"{m2}·{n + 1} − {m}·{n} = {yangi}."], noto=[m2, yangi - 10, yangi + 5])


@reg("M8-TAH", "ochiq")
def h8_tarqoq(rng):
    a = [rng.randint(5, 9) for _ in range(5)]; 
    return _o(f"Ma’lumotlar: {', '.join(map(str, a))}.", [("a) O‘rtachasi nechaga teng? (kasr yoki o‘nli)", Fraction(sum(a), 5)), ("b) Eng ko‘p uchraydigan son (moda) bormi? Bo‘lsa yozing, bo‘lmasa 0 yozing.", (lambda c: c[0][0] if c[0][1] > 1 and (len(c) == 1 or c[0][1] > c[1][1]) else 0)(__import__("collections").Counter(a).most_common()))], [f"a) {sum(a)}/5 = {num(Fraction(sum(a), 5))}.", "b) Eng ko‘p takrorlangan son — moda."])


@reg("M8-TAH", "ochiq")
def h8_tushun(rng):
    p, q_ = rng.choice([(20, 25), (30, 36), (40, 44)]); 
    return _o(f"Yilning birinchi yarmida {p} ming, ikkinchi yarmida {q_} ming dona mahsulot sotildi.", [("a) Butun yilda necha ming dona?", p + q_), ("b) Ikkinchi yarimda sotuv necha foizga oshdi? (butun foiz bo‘lmasa, 1 xona)", Fraction(100 * (q_ - p), p))], [f"a) {p} + {q_} = {p + q_}.", f"b) ({q_} − {p}) ÷ {p} · 100 = {num(Fraction(100 * (q_ - p), p))}%."])


@reg("M8-TAH", "yopiq")
def h8_diag(rng):
    n = ["Y", "F", "M", "A", "My"]; v = [rng.randint(10, 40) for _ in range(5)]; i = v.index(max(v))
    q = _yopiq(rng, "Chiziqli grafikda har oyda sotilgan mahsulot soni ko‘rsatilgan. Qaysi oyda eng ko‘p sotilgan?", n[i], [f"Eng baland nuqta — {n[i]} ({v[i]})."], noto=[x for j, x in enumerate(n) if j != i][:3], tartib=False)
    from modules.pisa_mat_g import fig_poliliniya
    q["rasm"] = fig_poliliniya(n, v, "Oylik sotuv"); return q


# ───────── M8-EHT ─────────
@reg("M8-EHT", "yopiq")
def e8_oddiy(rng):
    r, k = rng.sample(range(2, 9), 2)
    while abs(r - k) == 1: r, k = rng.sample(range(2, 9), 2)
    T = r + k
    return _yopiq(rng, f"Qopda {r} ta qizil va {k} ta ko‘k shar bor. Tasodifiy bitta shar olinadi. Qizil shar chiqish ehtimoli qancha?", f"${r}/{T}$", [f"Qulay hollar: {r}, barcha hollar: {T}.", f"P = {r}/{T}."], noto=[f"${k}/{T}$", f"${r}/{k}$", f"${r + 1}/{T}$"], tartib=False)


@reg("M8-EHT", "yopiq")
def e8_tanga(rng):
    n = rng.choice([2, 3]); 
    return _y(rng, f"Tanga {n} marta tashlanadi. Ikkala marta ham «gerb» tushish ehtimolining maxraji (oddiy kasr ko‘rinishida 1/?) nechaga teng?", 2 ** n, [f"Barcha natijalar soni 2^{n} = {2 ** n}.", f"Faqat bitta qulay holat, P = 1/{2 ** n}."], noto=[n, 2 * n, 2 ** n - 1])


@reg("M8-EHT", "ochiq")
def e8_zar(rng):
    s = rng.choice([4, 5, 6, 7, 8, 9]); c = 6 - abs(s - 7)
    return _o("Ikkita zar tashlanadi (jami 36 ta teng imkoniyatli natija).", [(f"a) Yig‘indi {s} bo‘ladigan natijalar soni?", c), (f"b) Yig‘indi {s} bo‘lish ehtimoli? (kasr)", Fraction(c, 36))], [f"a) Juftliklar soni: {c}.", f"b) {c}/36 = {num(Fraction(c, 36))}."])


@reg("M8-EHT", "ochiq")
def e8_qarshi(rng):
    n = rng.choice([20, 25, 40]); a = rng.randint(3, n // 2)
    return _o(f"Sinfda {n} o‘quvchi bor, ulardan {a} nafari chap qo‘l. Tasodifiy bitta o‘quvchi tanlanadi.", [("a) Chapaqay bo‘lish ehtimoli? (kasr)", Fraction(a, n)), ("b) Chapaqay bo‘lmaslik ehtimoli? (kasr)", Fraction(n - a, n))], [f"a) {a}/{n}.", f"b) 1 − {a}/{n} = {n - a}/{n}."])


@reg("M8-EHT", "ochiq")
def e8_ikki(rng):
    a, b = rng.choice([(2, 5), (3, 5), (1, 4), (3, 4)]); 
    return _o(f"Birinchi to‘pchaning g‘alaba ehtimoli {a}/{b}.", [("a) Mag‘lubiyat ehtimoli? (kasr)", 1 - Fraction(a, b)), (f"b) 20 ta o‘yinda taxminan nechta g‘alaba kutish mumkin?", Fraction(20 * a, b))], [f"a) 1 − {a}/{b} = {b - a}/{b}.", f"b) 20·{a}/{b} = {num(Fraction(20 * a, b))}."])


@reg("M8-EHT", "yopiq")
def e8_tartib(rng):
    n = rng.choice([3, 4, 5]); 
    return _y(rng, f"{n} ta turli kitobni javonga necha xil tartibda terish mumkin?", math.factorial(n), [f"{n}! = " + "·".join(str(i) for i in range(n, 0, -1)) + f" = {math.factorial(n)}."], noto=[n * n, n * 2, math.factorial(n) + n])


# ───────── dars rejalari ─────────
TEMA = {
    "M8-NAT": _tema("M8-NAT", "Natural sonlar", "Son", "🔢", "Bo‘linish, tub sonlar, EKUB va EKUK, daraja", [
        _d("Bo‘linish va tub sonlar", "Tub son: faqat 1 va o‘ziga bo‘linadi\nTub ko‘paytuvchilarga ajratish\n12 = 2·2·3", "Tub son faqat birga va o‘ziga bo‘linadi. Har qanday natural sonni tub ko‘paytuvchilarga ajratish mumkin."),
        _d("EKUB va EKUK", "EKUB — eng katta umumiy bo‘luvchi\nEKUK — eng kichik umumiy karrali\nEKUB · EKUK = a · b", "EKUB ikki son bo‘linadigan eng katta son, EKUK esa ikkalasiga bo‘linadigan eng kichik son. Takrorlanuvchi voqealar uchrashuvi masalalarida EKUK topiladi.")]),
    "M8-KAS": _tema("M8-KAS", "Kasrlar va o‘nli kasrlar", "Son", "🍰", "Kasrlar bilan amallar, aralash sonlar, o‘nli kasrlar", [
        _d("Amallar", "a/b + c/d: umumiy maxraj\na/b · c/d = ac/bd\nQisqartirishni unutma", "Kasrlarni qo‘shishdan oldin umumiy maxrajga keltiramiz. Ko‘paytirishda suratni suratga, maxrajni maxrajga ko‘paytiramiz va natijani qisqartiramiz."),
        _d("Aralash sonlar", "2 1/4 = (2·4 + 1)/4 = 9/4\nO‘nli kasrga: 3/4 = 0,75", "Aralash sonni noto‘g‘ri kasrga aylantirish uchun butun qismni maxrajga ko‘paytirib suratga qo‘shamiz.")]),
    "M8-BUT": _tema("M8-BUT", "Butun sonlar", "Son", "➖", "Manfiy sonlar, to‘rt amal, modul", [
        _d("Ishoralar", "−a − (−b) = −a + b\nMinus · minus = plyus\nMinus · plyus = minus", "Manfiy sonni ayirish — qarama-qarshi musbatni qo‘shish. Ikkita manfiy ko‘paytirilsa, musbat chiqadi."),
        _d("Modul", "|−7| = 7\nModul — nolgacha masofa", "Sonning moduli — uning sonlar o‘qidagi nolgacha bo‘lgan masofasi, shuning uchun doim manfiy emas.")]),
    "M8-NIS": _tema("M8-NIS", "Nisbat, proporsiya va foiz", "Son", "📏", "Nisbat bo‘yicha taqsimlash, proporsiya, foiz va chegirma", [
        _d("Nisbat va proporsiya", "a : b — jami a + b qism\na : b = c : x → x = bc / a\nTo‘g‘ri va teskari proporsionallik", "Nisbat bo‘yicha taqsimlashda avval qismlar yig‘indisini topamiz, bitta qism qiymatini hisoblaymiz. Proporsiyada o‘rtalar ko‘paytmasi chetlar ko‘paytmasiga teng."),
        _d("Foiz", "P ning p% i = P · p / 100\nYangi narx = P · (100 ± p) / 100\nO‘zgarish% = (yangi − eski) / eski · 100", "Sonning foizini topish uchun uni foizga ko‘paytirib yuzga bo‘lamiz. O‘zgarish foizi doim eskisiga nisbatan hisoblanadi.")]),
    "M8-QON": _tema("M8-QON", "Qonuniyatlar va ketma-ketliklar", "Algebra", "🔁", "Arifmetik va geometrik ketma-ketlik, n-chi had, yig‘indi", [
        _d("Arifmetik ketma-ketlik", "a_n = a₁ + (n − 1)·d\nYig‘indi: S = n(a₁ + a_n)/2", "Arifmetik ketma-ketlikda har had oldingisidan bir xil d ga farq qiladi. N-chi had birinchi had plyus n minus bir ko‘paytirilgan d."),
        _d("Geometrik ketma-ketlik", "a_n = a₁ · q^(n−1)\n2, 6, 18, 54 … q = 3", "Geometrik ketma-ketlikda har had oldingisidan bir xil q marta katta. N-chi had a bir ko‘paytirilgan q ning n minus birinchi darajasi.")]),
    "M8-IFO": _tema("M8-IFO", "Algebraik ifodalar", "Algebra", "🔤", "Ifoda qiymati, o‘xshash hadlar, qavslarni ochish, darajalar", [
        _d("Soddalashtirish", "O‘xshash hadlar: 3x + 5x = 8x\nQavs: k(a + b) = ka + kb", "O‘xshash hadlarni qo‘shamiz, qavsni ochganda har hadga ko‘paytiramiz. Qavs oldida minus bo‘lsa, ichidagi hamma ishoralar o‘zgaradi."),
        _d("Darajalar", "aᵐ · aⁿ = aᵐ⁺ⁿ\naᵐ / aⁿ = aᵐ⁻ⁿ", "Asoslari bir xil darajalar ko‘paytirilganda ko‘rsatkichlar qo‘shiladi, bo‘linganda ayriladi.")]),
    "M8-TEN": _tema("M8-TEN", "Tenglamalar, formulalar va funksiyalar", "Algebra", "⚖️", "Chiziqli tenglama, formula, funksiya qiymati va grafigi", [
        _d("Tenglama yechish", "ax + b = c → x = (c − b)/a\nBir tomonga nima qilsak, ikkinchisiga ham", "Tenglamani teskari amallar yordamida yechamiz: avval qo‘shiluvchini ko‘chiramiz, keyin koeffitsientga bo‘lamiz."),
        _d("Funksiya va grafik", "f(x) = kx + b\nb — y o‘qini kesgan joy\nk — qiyalik", "Funksiya qiymatini topish uchun x o‘rniga son qo‘yamiz. Chiziqli funksiya grafigi to‘g‘ri chiziq: b — boshlang‘ich qiymat, k — qiyalik.")]),
    "M8-SHA": _tema("M8-SHA", "Geometrik shakllar", "Geometriya", "🔺", "Uchburchak, ko‘pburchak, o‘xshashlik, Pifagor, parallel chiziqlar", [
        _d("Burchaklar", "Uchburchak: 180°\nn burchak: (n − 2)·180°\nParallel: ichki bir tomonli = 180°", "Uchburchak ichki burchaklari yig‘indisi yuz sakson gradus. N burchakli ko‘pburchakda — n minus ikki ko‘paytirilgan yuz sakson."),
        _d("Pifagor va o‘xshashlik", "c² = a² + b²\n3-4-5, 5-12-13, 8-15-17\nO‘xshash: mos tomonlar nisbati bir xil", "To‘g‘ri burchakli uchburchakda gipotenuza kvadrati katetlar kvadratlari yig‘indisiga teng. O‘xshash shakllarda mos tomonlar bir xil nisbatda.")]),
    "M8-OLC": _tema("M8-OLC", "Geometrik o‘lchashlar", "Geometriya", "📦", "Aylana, doira, trapetsiya, prizma va silindr hajmi", [
        _d("Yuza formulalari", "Doira: S = πr²,  C = πd\nTrapetsiya: S = (a + b)h/2", "Doira yuzi pi er kvadrat, aylana uzunligi pi d. Trapetsiya yuzi — asoslar yig‘indisining yarmi ko‘paytirilgan balandlikka."),
        _d("Hajm", "Prizma: V = S_asos · h\nSilindr: V = πr²h\n1 m³ = 1000 l", "Prizma va silindr hajmi — asos yuzi ko‘paytirilgan balandlikka. Bir kub metr — ming litr.")]),
    "M8-JOY": _tema("M8-JOY", "Koordinatalar va almashtirishlar", "Geometriya", "🧭", "Koordinata tekisligi, masofa, simmetriya, parallel ko‘chirish", [
        _d("Koordinatalar", "(x; y) — x gorizontal, y vertikal\nChoraklar: I (+,+)  II (−,+)  III (−,−)  IV (+,−)", "Nuqta koordinatasi ikki sondan iborat: avval x, keyin y. Tekislik to‘rtta chorakka bo‘linadi."),
        _d("Almashtirishlar", "Ox ga simmetriya: (x; y) → (x; −y)\nOy ga simmetriya: (x; y) → (−x; y)\nKo‘chirish: (x + a; y + b)", "Ox o‘qiga nisbatan simmetriyada y ning ishorasi o‘zgaradi. Parallel ko‘chirishda har koordinataga mos son qo‘shiladi.")]),
    "M8-TAS": _tema("M8-TAS", "Ma’lumotlarni tartiblash va tasvirlash", "Ma’lumotlar", "📊", "Diagramma tanlash, oraliq, chastota va foiz", [
        _d("Diagramma tanlash", "Ulushlar → doira\nVaqt bo‘yicha o‘zgarish → chiziqli grafik\nToifalarni solishtirish → ustunli", "Ma’lumot turiga mos diagramma tanlanadi: ulushlar uchun doira, vaqt bo‘yicha o‘zgarish uchun chiziqli grafik, toifalarni taqqoslash uchun ustunli diagramma.")]),
    "M8-TAH": _tema("M8-TAH", "Ma’lumotlarni tahlil qilish", "Ma’lumotlar", "📈", "O‘rtacha, mediana, moda va ularni solishtirish", [
        _d("Markaziy ko‘rsatkichlar", "O‘rtacha = yig‘indi / soni\nMediana — tartiblangan qatorning o‘rtasi\nModa — eng ko‘p uchraydigan", "O‘rtacha yig‘indini sonlar soniga bo‘lish bilan topiladi. Mediana — tartiblangan qatorning o‘rtasi. Moda — eng ko‘p uchraydigan qiymat.")]),
    "M8-EHT": _tema("M8-EHT", "Ehtimollik", "Ma’lumotlar", "🎲", "Oddiy ehtimol, zar va tanga, qarama-qarshi hodisa", [
        _d("Ehtimol", "P = qulay hollar / barcha hollar\nP(A emas) = 1 − P(A)\nIkki zar: 36 ta natija", "Ehtimol — qulay hollar sonining barcha teng imkoniyatli hollar soniga nisbati. Hodisa yuz bermasligi ehtimoli bir minus uning ehtimoli."),
        _d("Sanash", "n ta narsa: n! tartib\n2 tanga: 4 natija; 3 tanga: 8", "N ta turli narsani n faktorial usulda tartiblash mumkin. Har tanga tashlanishi natijalar sonini ikki baravar oshiradi.")]),
}
