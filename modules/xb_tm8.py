"""TIMSS 8-sinf matematika — kengaytma: 14 yangi mavzu (dars + 6 generator → 30 mashq/30 test)."""
import math
from fractions import Fraction

from modules.pisa_mat_g import reg, num, som, _y, _o

TOP = "T11_G8_M"
TEMA = {}


def tema(kod, nom, soha, belgi, maqsad, dars):
    TEMA[kod] = {"nom": nom, "soha": soha, "belgi": belgi, "maqsad": maqsad, "bolim": kod, "toplam": TOP,
                 "dars": [{"sarlavha": a, "doska": b, "ovoz": c} for a, b, c in dars]}


def Y(kod):
    return reg(kod, "yopiq")


def O(kod):
    return reg(kod, "ochiq")


# 1 ── daraja va ildiz
tema("t8_daraja", "Daraja va kvadrat ildiz", "Sonlar", "⬆️", "Daraja hisoblash, daraja xossalari, to‘liq kvadratlar va ildiz", [
    ("Daraja", "aⁿ = a · a · … · a (n marta)\n2⁵ = 32\nHar qanday son 0-darajada = 1", "Daraja bir xil ko‘paytuvchini takror ko‘paytirishdir. Ikkining beshinchi darajasi ikki marta ikki, bunday besh marta — o‘ttiz ikki."),
    ("Xossalar", "aᵐ · aⁿ = aᵐ⁺ⁿ\naᵐ : aⁿ = aᵐ⁻ⁿ\n(aᵐ)ⁿ = aᵐⁿ", "Asoslari bir xil darajalar ko‘paytirilsa, daraja ko‘rsatkichlari qo‘shiladi; bo‘linsa ayiriladi; darajaning darajasida ko‘paytiriladi."),
    ("Kvadrat ildiz", "√49 = 7, chunki 7² = 49\n√(a²) = a (a ≥ 0)", "Kvadrat ildiz kvadrati berilgan songa teng manfiy bo‘lmagan sonni topadi. Eng muhim kvadratlarni yoddan bilish foydali."),
])


@Y("t8_daraja")
def _d1(rng):
    a, n = rng.randint(2, 6), rng.randint(2, 4)
    return _y(rng, f"{a}^{n} nechaga teng?", a ** n, [f"{a}^{n} = " + " · ".join([str(a)] * n) + f" = {a ** n}."], noto=[a * n, a ** (n + 1), a ** (n - 1), a + n])


@Y("t8_daraja")
def _d2(rng):
    a, m, n = rng.randint(2, 5), rng.randint(2, 6), rng.randint(2, 6)
    return _y(rng, f"{a}^{m} · {a}^{n} = {a}^?  — daraja ko‘rsatkichi nechaga teng?", m + n, ["Asoslari bir xil: ko‘rsatkichlar qo‘shiladi."], noto=[m * n, abs(m - n), m + n + 1])


@Y("t8_daraja")
def _d3(rng):
    k = rng.randint(3, 15)
    return _y(rng, f"√{k * k} nechaga teng?", k, [f"{k}² = {k * k}, demak √{k * k} = {k}."], noto=[k * 2, k + 1, k - 1, k * k // 2])


@Y("t8_daraja")
def _d4(rng):
    k, m = rng.randint(3, 12), rng.randint(2, 9)
    return _y(rng, f"√{k * k} + √{m * m} nechaga teng?", k + m, [f"{k} + {m} = {k + m}."], noto=[k * m, abs(k - m) + 1, k + m + 1, (k + m) ** 2])


@O("t8_daraja")
def _d5(rng):
    a, n = rng.randint(2, 5), rng.randint(2, 4)
    return _o(f"Hisoblang.", [(f"a) {a}^{n} =", a ** n), (f"b) {a}^{n + 1} − {a}^{n} =", a ** (n + 1) - a ** n)], [f"a) {a ** n}.", f"b) {a ** (n + 1)} − {a ** n} = {a ** (n + 1) - a ** n}."])


@O("t8_daraja")
def _d6(rng):
    k, m = rng.randint(4, 12), rng.randint(2, 9)
    return _o(f"Kvadrat shaklidagi maydon yuzasi {k * k} kv. m.", [("a) Tomoni (m):", k), ("b) Perimetri (m):", 4 * k)], [f"a) √{k * k} = {k}.", f"b) 4 · {k} = {4 * k}."])


# 2 ── EKUB, EKUK
tema("t8_bolinish", "Bo‘linish, EKUB va EKUK", "Sonlar", "🔗", "Tub sonlar, bo‘linish belgilari, eng katta umumiy bo‘luvchi va eng kichik umumiy karrali", [
    ("Bo‘linish belgilari", "2: oxiri juft\n3: raqamlar yig‘indisi 3 ga bo‘linadi\n5: oxiri 0 yoki 5", "Sonning ikkiga bo‘linishi oxirgi raqamga, uchga bo‘linishi esa raqamlar yig‘indisiga bog‘liq."),
    ("EKUB va EKUK", "12 va 18: EKUB = 6, EKUK = 36\nEKUB · EKUK = a · b", "Eng katta umumiy bo‘luvchi — ikkala songa bo‘linadigan eng katta son. Eng kichik umumiy karrali — ikkalasiga bo‘linadigan eng kichik son."),
])


def _ekub(a, b):
    return math.gcd(a, b)


@Y("t8_bolinish")
def _e1(rng):
    k = rng.randint(2, 9); a, b = k * rng.randint(2, 6), k * rng.randint(7, 12)
    g = math.gcd(a, b)
    return _y(rng, f"{a} va {b} sonlarining EKUB ini toping.", g, [f"Eng katta umumiy bo‘luvchi: {g}."], noto=[g + 1, g * 2, a * b // g if a * b // g != g else g + 3, 1 if g != 1 else 2])


@Y("t8_bolinish")
def _e2(rng):
    a, b = rng.choice([4, 6, 8, 9, 10, 12, 15]), rng.choice([5, 6, 8, 9, 14, 21])
    l = a * b // math.gcd(a, b)
    return _y(rng, f"{a} va {b} sonlarining EKUK ini toping.", l, [f"EKUK = {a}·{b}/EKUB = {l}."], noto=[a * b if a * b != l else l + a, l + a, l - 1 if l > 1 else 3, math.gcd(a, b)])


@Y("t8_bolinish")
def _e3(rng):
    n = rng.randint(100, 998)
    return _y(rng, f"{n} sonining raqamlar yig‘indisi nechaga teng?", sum(map(int, str(n))), [f"{' + '.join(str(n))} = {sum(map(int, str(n)))}."], noto=[sum(map(int, str(n))) + 1, sum(map(int, str(n))) - 1, n % 9 + 10])


@Y("t8_bolinish")
def _e4(rng):
    a, b = rng.choice([(12, 18), (8, 12), (15, 20), (6, 9), (10, 25)])
    l = a * b // math.gcd(a, b)
    return _y(rng, f"Ikki avtobus {a} va {b} daqiqada bir marta bekatga keladi. Ular birga kelgandan keyin yana necha daqiqadan keyin birga keladi?", l, [f"EKUK({a}, {b}) = {l}."], noto=[math.gcd(a, b), a * b if a * b != l else l + 6, l + a])


@O("t8_bolinish")
def _e5(rng):
    k = rng.randint(2, 9); a, b = k * rng.randint(2, 5), k * rng.randint(6, 9)
    return _o(f"Sonlar: {a} va {b}.", [("a) EKUB:", math.gcd(a, b)), ("b) EKUK:", a * b // math.gcd(a, b))], [f"a) {math.gcd(a, b)}.", f"b) {a * b // math.gcd(a, b)}."])


@O("t8_bolinish")
def _e6(rng):
    k = rng.randint(3, 8); a, b = k * rng.randint(3, 6), k * rng.randint(7, 11)
    return _o(f"{a} ta qalam va {b} ta daftarni bir xil to‘plamlarga ortiqchasiz bo‘lib chiqmoqchimiz.", [("a) Eng ko‘p to‘plam soni:", math.gcd(a, b)), ("b) Har to‘plamda qalam:", a // math.gcd(a, b))], [f"a) EKUB = {math.gcd(a, b)}.", f"b) {a} : {math.gcd(a, b)} = {a // math.gcd(a, b)}."])


# 3 ── butun sonlar
tema("t8_butun", "Butun sonlar bilan amallar", "Sonlar", "🌡️", "Manfiy sonlarni qo‘shish, ayirish, ko‘paytirish va bo‘lish", [
    ("Ishoralar", "(−)·(−) = (+)\n(−)·(+) = (−)\n(−)·(−)·(−) = (−)", "Ikki manfiy son ko‘paytmasi musbat. Har xil ishorali sonlar ko‘paytmasi manfiy."),
    ("Amallar tartibi", "Avval qavs, so‘ng daraja,\nso‘ng ko‘paytirish/bo‘lish,\nkeyin qo‘shish/ayirish", "Amallar tartibiga rioya qiling: avval qavs ichi, keyin ko‘paytirish va bo‘lish, oxirida qo‘shish va ayirish."),
])


@Y("t8_butun")
def _b1(rng):
    a, b = rng.randint(-12, -2), rng.randint(2, 9)
    return _y(rng, f"({a}) · {b} = ?", a * b, ["Har xil ishorali sonlar ko‘paytmasi manfiy."], noto=[-a * b, a + b, a - b, a * b + 1])


@Y("t8_butun")
def _b2(rng):
    a, b = rng.randint(-9, -2), rng.randint(-9, -2)
    return _y(rng, f"({a}) · ({b}) = ?", a * b, ["Manfiy · manfiy = musbat."], noto=[-a * b, a + b, a - b, a * b + 2])


@Y("t8_butun")
def _b3(rng):
    a, b, c = rng.randint(-9, 9), rng.randint(2, 6), rng.randint(2, 9)
    return _y(rng, f"{a} + {b} · {c} − {c} = ?", a + b * c - c, [f"Avval ko‘paytirish: {b}·{c} = {b * c}; keyin {a} + {b * c} − {c} = {a + b * c - c}."], noto=[(a + b) * c - c, a + b * (c - c), a + b * c + c, a - b * c - c])


@Y("t8_butun")
def _b4(rng):
    b = rng.randint(2, 9); q = rng.randint(-9, -2)
    return _y(rng, f"({b * q}) : {b} = ?", q, [f"{b * q} : {b} = {q}."], noto=[-q, q + 1, b * q, q - 1])


@O("t8_butun")
def _b5(rng):
    a, b = rng.randint(-15, -3), rng.randint(3, 12)
    return _o(f"a = {a}, b = {b}.", [("a) a + b =", a + b), ("b) a · b =", a * b)], [f"a) {a} + {b} = {a + b}.", f"b) {a} · {b} = {a * b}."])


@O("t8_butun")
def _b6(rng):
    t = rng.randint(-20, -5); d = rng.randint(3, 9)
    return _o(f"Harorat ertalab {t}° edi. Har soatda {d}° ga ko‘tarildi.", [("a) 3 soatdan keyin (°):", t + 3 * d), ("b) Nolga yetishi uchun nechchi soat kerak (to‘liq soat, ko‘p bo‘lsa yuqoriga yaxlitlang):", -(-(-t) // d))], [f"a) {t} + 3·{d} = {t + 3 * d}.", f"b) {-t} : {d} ni yuqoriga yaxlitlash."])


# 4 ── foiz
tema("t8_foiz", "Foiz va foiz o‘zgarishi", "Nisbat va foiz", "💯", "Sondan foiz topish, chegirma, narx o‘sishi, foiz o‘zgarishi", [
    ("Foiz", "p% = p/100\n40 ning 15% i = 40 · 0,15 = 6", "Foiz — yuzdan bir ulush. Sondan foizni topish uchun sonni foiz/100 ga ko‘paytiramiz."),
    ("O‘zgarish", "Narx 20% ga oshdi: yangi = eski · 1,2\nChegirma 30%: yangi = eski · 0,7", "Narx foizga oshganda eski narxni (100 + p)/100 ga ko‘paytiramiz; chegirmada (100 − p)/100 ga."),
])


@Y("t8_foiz")
def _p1(rng):
    n, p = rng.choice([40, 60, 80, 120, 200, 250, 300]), rng.choice([5, 10, 15, 20, 25, 30, 40])
    r = Fraction(n * p, 100)
    return _y(rng, f"{n} ning {p}% i nechaga teng?", r, [f"{n} · {p}/100 = {num(r)}."], noto=[n - r, r * 10, r + p, Fraction(n, p)])


@Y("t8_foiz")
def _p2(rng):
    n, p = rng.choice([40000, 60000, 80000, 120000, 200000]), rng.choice([10, 15, 20, 25, 30])
    return _y(rng, f"Mahsulot narxi {som(n)} so‘m edi, unga {p}% chegirma qilindi. Yangi narx qancha (so‘m)?", n * (100 - p) // 100, [f"{som(n)} · (100 − {p})/100 = {som(n * (100 - p) // 100)}."],
              noto=[n * (100 + p) // 100, n * p // 100, n - p, n * (100 - p) // 100 + 5000])


@Y("t8_foiz")
def _p3(rng):
    a = rng.choice([20, 40, 50, 80, 120]); p = rng.choice([10, 20, 25, 50])
    b = a * (100 + p) // 100
    return _y(rng, f"Narx {a} dan {b} gacha oshdi. Necha foizga oshgan?", p, [f"({b} − {a})/{a} · 100 = {p}%."], noto=[p + 5, p * 2, b - a, 100 - p] if p != 50 else [25, 100, 30, 40])


@Y("t8_foiz")
def _p4(rng):
    k = rng.choice([20, 25, 40, 50]); m = rng.choice([8, 12, 16, 20, 24, 40])
    tot = (m * 100) // k if (m * 100) % k == 0 else m * 5
    p = Fraction(m * 100, tot)
    return _y(rng, f"{tot} o‘quvchining {m} tasi a’lochi. A’lochilar necha foiz?", p, [f"{m}/{tot} · 100 = {num(p)}%."], noto=[p + 5, p * 2, tot - m, Fraction(tot, m)])


@O("t8_foiz")
def _p5(rng):
    n, p = rng.choice([50000, 80000, 120000, 150000]), rng.choice([10, 20, 25, 30])
    return _o(f"Telefon narxi {som(n)} so‘m. Chegirma {p}%.", [("a) Chegirma miqdori (so‘m):", n * p // 100), ("b) To‘lanadigan summa (so‘m):", n - n * p // 100)], [f"a) {som(n)}·{p}/100 = {som(n * p // 100)}.", f"b) {som(n)} − {som(n * p // 100)}."])


@O("t8_foiz")
def _p6(rng):
    n, p = rng.choice([200, 400, 500, 800]), rng.choice([5, 10, 15, 20])
    return _o(f"Maktabda {n} o‘quvchi. Ulardan {p}% i to‘garakda qatnashadi.", [("a) To‘garakdagilar soni:", n * p // 100), ("b) Qolganlar soni:", n - n * p // 100)], [f"a) {n}·{p}/100 = {n * p // 100}.", f"b) {n} − {n * p // 100}."])


# 5 ── proporsiya
tema("t8_prop", "Nisbat va proporsiya", "Nisbat va foiz", "⚖️", "To‘g‘ri va teskari proporsionallik, masshtab, nisbat bo‘yicha taqsimlash", [
    ("To‘g‘ri", "Bir kattalik necha marta oshsa, ikkinchisi ham shuncha marta oshadi\n3 kg — 12 000 → 5 kg — ?", "To‘g‘ri proporsionallikda bir kattalik ortsa, ikkinchisi ham shuncha marta ortadi. Bir birlik narxini topib, kerakli songa ko‘paytiramiz."),
    ("Teskari", "Ishchilar ko‘p — vaqt kam\n4 ishchi · 6 kun = 24 ish-kun", "Teskari proporsionallikda ko‘paytma o‘zgarmaydi: ishchilar soni ko‘paysa, kerakli vaqt kamayadi."),
])


@Y("t8_prop")
def _r1(rng):
    k, p, n = rng.randint(2, 6), rng.choice([4000, 6000, 8000, 12000]), rng.randint(7, 12)
    return _y(rng, f"{k} kg guruch {som(k * p)} so‘m. {n} kg guruch necha so‘m?", n * p, [f"1 kg = {som(p)} so‘m; {n} kg = {som(n * p)}."], noto=[(n + 1) * p, k * p, n * p - p, n * p + k])


@Y("t8_prop")
def _r2(rng):
    w, d = rng.choice([2, 3, 4, 6]), rng.choice([6, 8, 12, 9])
    n = rng.choice([x for x in [1, 2, 3, 4, 6, 8, 9, 12] if (w * d) % x == 0 and x != w])
    return _y(rng, f"{w} ishchi ishni {d} kunda bitiradi. {n} ishchi shu ishni necha kunda bitiradi?", w * d // n, [f"Ish hajmi: {w}·{d} = {w * d} ish-kun; {w * d} : {n} = {w * d // n}."], noto=[w * d * n, d + n, d - n + 10, w * d // n + 1])


@Y("t8_prop")
def _r3(rng):
    m, k = rng.choice([1000, 5000, 10000, 25000]), rng.randint(2, 9)
    return _y(rng, f"Xaritada masshtab 1 : {m}. Xaritada {k} sm masofa haqiqatda necha metr?", k * m // 100, [f"{k} sm · {m} = {k * m} sm = {k * m // 100} m."], noto=[k * m, k * m // 1000, k * m // 10, k * m // 100 + k])


@Y("t8_prop")
def _r4(rng):
    a, b = rng.choice([(2, 3), (3, 5), (1, 4), (2, 5)]); t = (a + b) * rng.randint(4, 12)
    return _y(rng, f"{t} so‘m {a} : {b} nisbatda taqsimlandi. Kichik ulush qancha (so‘m)?", t // (a + b) * a, [f"Bir qism = {t} : {a + b} = {t // (a + b)}; kichigi {a} qism."], noto=[t // (a + b) * b, t // (a + b), t // a, t - t // (a + b)])


@O("t8_prop")
def _r5(rng):
    a, b = rng.choice([(2, 3), (3, 4), (1, 5), (3, 7)]); k = rng.randint(3, 10)
    return _o(f"Aralashmada {a} qism un va {b} qism shakar bor. Un {a * k} kg.", [("a) Shakar (kg):", b * k), ("b) Jami aralashma (kg):", (a + b) * k)], [f"a) {a * k} : {a} · {b} = {b * k}.", f"b) {a * k} + {b * k}."])


@O("t8_prop")
def _r6(rng):
    v, t = rng.choice([40, 60, 80]), rng.choice([2, 3, 4, 5])
    return _o(f"Avtomobil {v} km/soat tezlik bilan {t} soat yurdi.", [("a) Yo‘l (km):", v * t), ("b) Tezlik 2 marta oshsa, shu yo‘lga ketadigan vaqt (soat):", Fraction(t, 2))], [f"a) {v}·{t} = {v * t}.", f"b) {t} : 2."])


# 6 ── ifoda
tema("t8_ifoda", "Algebraik ifodalar", "Algebra", "🔤", "O‘xshash hadlarni ixchamlash, qavslarni ochish, ifoda qiymatini topish", [
    ("O‘xshash hadlar", "3x + 5x = 8x\n2a + 7 − a = a + 7", "O‘xshash hadlar — bir xil harfli qismlari bo‘lgan hadlar. Ularning koeffitsiyentlari qo‘shiladi yoki ayiriladi."),
    ("Qavslar", "3(x + 4) = 3x + 12\n−(a − 2) = −a + 2", "Qavs oldidagi son qavs ichidagi har bir hadga ko‘paytiriladi. Qavs oldida minus bo‘lsa, ishoralar teskari bo‘ladi."),
])


@Y("t8_ifoda")
def _i1(rng):
    a, b = rng.randint(2, 9), rng.randint(2, 9); c = rng.randint(1, 9)
    return _y(rng, f"{a}x + {b}x + {c} ni ixchamlang. x = 2 bo‘lsa qiymati nechaga teng?", (a + b) * 2 + c, [f"{a + b}x + {c}; x = 2: {2 * (a + b)} + {c} = {(a + b) * 2 + c}."], noto=[a * b * 2 + c, (a + b) + c, (a + b) * 2 - c, (a + b + c) * 2])


@Y("t8_ifoda")
def _i2(rng):
    k, a, b = rng.randint(2, 7), rng.randint(1, 9), rng.randint(1, 9)
    return _y(rng, f"{k}(x + {a}) − {k}x + {b} ifodani soddalashtirsangiz qiymati qancha bo‘ladi?", k * a + b, [f"{k}x + {k * a} − {k}x + {b} = {k * a + b}."], noto=[k * a - b, a + b, k * (a + b) + 1, k * a * b])


@Y("t8_ifoda")
def _i3(rng):
    x, y = rng.randint(2, 7), rng.randint(2, 7); a, b = rng.randint(2, 6), rng.randint(2, 6)
    return _y(rng, f"x = {x}, y = {y} bo‘lganda {a}x + {b}y ning qiymatini toping.", a * x + b * y, [f"{a}·{x} + {b}·{y} = {a * x + b * y}."], noto=[a * x * b * y, (a + b) * (x + y), a * x - b * y, a + x + b + y])


@Y("t8_ifoda")
def _i4(rng):
    a, b = rng.randint(2, 9), rng.randint(2, 9)
    return _y(rng, f"3(a + {a}) − 2(a − {b}) ifoda a = 5 da nechaga teng?", 3 * (5 + a) - 2 * (5 - b), [f"3·{5 + a} − 2·{5 - b} = {3 * (5 + a) - 2 * (5 - b)}."], noto=[3 * (5 + a) + 2 * (5 - b), 5 + 3 * a + 2 * b, 3 * 5 + a - 2 * 5 + b, 3 * a - 2 * b])


@O("t8_ifoda")
def _i5(rng):
    a, b = rng.randint(2, 8), rng.randint(2, 8)
    return _o(f"Ifoda: {a}(x + 2) + {b}x. x = 3 bo‘lsin.", [("a) Qavsni oching: x ning koeffitsiyenti:", a + b), ("b) Ifoda qiymati:", (a + b) * 3 + 2 * a)], [f"a) {a}x + {b}x = {a + b}x.", f"b) {(a + b) * 3} + {2 * a}."])


@O("t8_ifoda")
def _i6(rng):
    n, p = rng.randint(3, 9), rng.choice([1500, 2000, 2500, 3000])
    return _o(f"Daftar narxi x so‘m. {n} ta daftar va {p} so‘mlik qalam sotib olindi. x = {p} bo‘lsa:", [("a) Jami (so‘m):", n * p + p), ("b) Agar x = 2 000 bo‘lsa jami:", n * 2000 + p)], [f"a) {n}·{p} + {p}.", f"b) {n}·2000 + {p}."])


# 7 ── tenglama
tema("t8_tenglama", "Chiziqli tenglamalar", "Algebra", "⚖️", "Bir noma’lumli chiziqli tenglamani yechish va tenglama tuzib masala yechish", [
    ("Tenglama", "3x + 5 = 20\n3x = 15\nx = 5", "Tenglamani yechishda ikkala tomonga bir xil amal qo‘llaymiz. Avval ozod hadni o‘tkazamiz, so‘ng x oldidagi songa bo‘lamiz."),
    ("Masala", "Noma’lumni x deb olamiz\nShartdan tenglama tuzamiz\nYechib, tekshiramiz", "Masalada noma’lum kattalikni harf bilan belgilab, shartni tenglama ko‘rinishida yozamiz."),
])


@Y("t8_tenglama")
def _t1(rng):
    x, a, b = rng.randint(2, 15), rng.randint(2, 9), rng.randint(1, 20)
    return _y(rng, f"{a}x + {b} = {a * x + b}. x nechaga teng?", x, [f"{a}x = {a * x}; x = {x}."], noto=[x + 1, x - 1, a * x, x + b])


@Y("t8_tenglama")
def _t2(rng):
    x, a, b = rng.randint(2, 12), rng.randint(2, 6), rng.randint(2, 8)
    return _y(rng, f"{a}x − {b} = {a * x - b}. x nechaga teng?", x, [f"{a}x = {a * x}; x = {x}."], noto=[x + 1, x - 1, a * x - b, x + b])


@Y("t8_tenglama")
def _t3(rng):
    x, a = rng.randint(3, 15), rng.randint(2, 6)
    return _y(rng, f"Biror sonning {a} baravariga 7 qo‘shsak {a * x + 7} chiqadi. Shu sonni toping.", x, [f"{a}x + 7 = {a * x + 7}; x = {x}."], noto=[a * x, x + 7, x + a, x - 1])


@Y("t8_tenglama")
def _t4(rng):
    x, a, b = rng.randint(2, 10), rng.randint(3, 7), rng.randint(1, 2)
    c = a * x + b - (a - b) * x
    return _y(rng, f"{a}x + {b} = {a - b}x + {c}. x nechaga teng?", x, [f"{a}x − {a - b}x = {c} − {b}; {b}x = {c - b}; x = {x}."], noto=[x + 1, x - 1, c, x + b])


@O("t8_tenglama")
def _t5(rng):
    x, a, b = rng.randint(3, 12), rng.randint(2, 7), rng.randint(1, 15)
    return _o(f"Tenglama: {a}x + {b} = {a * x + b}.", [("a) x =", x), ("b) 2x + 1 =", 2 * x + 1)], [f"a) {a}x = {a * x}, x = {x}.", f"b) 2·{x} + 1 = {2 * x + 1}."])


@O("t8_tenglama")
def _t6(rng):
    x, k = rng.randint(5, 25), rng.randint(2, 5)
    return _o(f"Ali yoshi Valining yoshidan {k} baravar katta, ikkalasi birga {x * (k + 1)} yosh.", [("a) Valining yoshi:", x), ("b) Alining yoshi:", x * k)], [f"a) x + {k}x = {x * (k + 1)}, x = {x}.", f"b) {k}·{x}."])


# 8 ── funksiya
tema("t8_funk", "Chiziqli funksiya", "Algebra", "📈", "y = kx + b: qiymat hisoblash, o‘sish va kamayish, grafik nuqtalari", [
    ("Funksiya", "y = 2x + 1\nx = 3 → y = 7", "Chiziqli funksiyada x ning har bir qiymatiga bitta y mos keladi. y ni topish uchun x ni formulaga qo‘yamiz."),
    ("Grafik", "k > 0: o‘sadi\nk < 0: kamayadi\nb — y o‘qidagi kesishish", "Funksiya grafigi to‘g‘ri chiziq. Burchak koeffitsiyenti k musbat bo‘lsa funksiya o‘sadi, manfiy bo‘lsa kamayadi."),
])


@Y("t8_funk")
def _fu1(rng):
    k, b, x = rng.randint(2, 6), rng.randint(-5, 9), rng.randint(-3, 6)
    return _y(rng, f"y = {k}x {'+' if b >= 0 else '−'} {abs(b)} funksiyada x = {x} bo‘lsa y nechaga teng?", k * x + b, [f"y = {k}·({x}) + ({b}) = {k * x + b}."], noto=[k * x - b, k + x + b, -k * x + b, (k + b) * x])


@Y("t8_funk")
def _fu2(rng):
    k = rng.choice([-4, -3, -2, 2, 3, 5]); b = rng.randint(1, 9)
    return _y(rng, f"y = {k}x + {b} funksiya qanday o‘zgaradi?", "o‘sadi" if k > 0 else "kamayadi", ["k > 0 — o‘sadi, k < 0 — kamayadi."], noto=[x for x in ["o‘sadi", "kamayadi", "o‘zgarmaydi", "avval o‘sadi, so‘ng kamayadi"] if x != ("o‘sadi" if k > 0 else "kamayadi")][:3])


@Y("t8_funk")
def _fu3(rng):
    k, b = rng.randint(2, 6), rng.randint(1, 9)
    return _y(rng, f"y = {k}x + {b} grafigi y o‘qini qaysi nuqtada kesadi (y qiymati)?", b, ["x = 0 da y = b."], noto=[k, k + b, -b, b * k])


@Y("t8_funk")
def _fu4(rng):
    k, b, x = rng.randint(2, 5), rng.randint(1, 9), rng.randint(1, 8); y = k * x + b
    return _y(rng, f"y = {k}x + {b} funksiya y = {y} qiymatni qabul qilsa x nechaga teng?", x, [f"{k}x = {y - b}, x = {x}."], noto=[x + 1, x - 1, y - b, x * k])


@O("t8_funk")
def _fu5(rng):
    p, t = rng.choice([5000, 8000, 10000]), rng.choice([3000, 5000])
    return _o(f"Taksi to‘lovi: y = {p}·x + {t} (x — km).", [("a) 4 km uchun to‘lov:", 4 * p + t), ("b) 10 km uchun to‘lov:", 10 * p + t)], [f"a) {4 * p}+{t}.", f"b) {10 * p}+{t}."])


@O("t8_funk")
def _fu6(rng):
    k, b = rng.randint(2, 5), rng.randint(1, 8)
    return _o(f"y = {k}x + {b}.", [("a) x = 0 da y =", b), ("b) x = 4 da y =", 4 * k + b)], [f"a) y = {b}.", f"b) y = {4 * k + b}."])


# 9 ── uchburchak
tema("t8_uchburchak", "Uchburchak: burchaklar va Pifagor", "Geometriya", "🔺", "Burchaklar yig‘indisi, teng yonli uchburchak, Pifagor teoremasi", [
    ("Burchaklar", "A + B + C = 180°\nTeng yonli: asosdagi burchaklar teng", "Uchburchak burchaklari yig‘indisi har doim yuz sakson gradus."),
    ("Pifagor", "a² + b² = c²\n3, 4, 5\n5, 12, 13", "To‘g‘ri burchakli uchburchakda katetlar kvadratlari yig‘indisi gipotenuza kvadratiga teng."),
])


@Y("t8_uchburchak")
def _ub1(rng):
    a, b = rng.randint(30, 80), rng.randint(30, 80)
    return _y(rng, f"Uchburchakning ikki burchagi {a}° va {b}°. Uchinchisi necha gradus?", 180 - a - b, [f"180 − {a} − {b} = {180 - a - b}."], noto=[180 - a, a + b, 360 - a - b, 90 - a])


@Y("t8_uchburchak")
def _ub2(rng):
    t = rng.choice([(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15)])
    return _y(rng, f"To‘g‘ri burchakli uchburchak katetlari {t[0]} sm va {t[1]} sm. Gipotenuzasi necha sm?", t[2], [f"{t[0]}² + {t[1]}² = {t[0] ** 2 + t[1] ** 2} = {t[2]}²."], noto=[t[0] + t[1], t[2] + 1, t[2] - 1, t[1] - t[0] + 3])


@Y("t8_uchburchak")
def _ub3(rng):
    t = rng.choice([(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17)])
    return _y(rng, f"To‘g‘ri burchakli uchburchakda gipotenuza {t[2]} sm, bitta katet {t[0]} sm. Ikkinchi katet necha sm?", t[1], [f"{t[2]}² − {t[0]}² = {t[1] ** 2}."], noto=[t[2] - t[0], t[1] + 1, t[2] + t[0], t[1] - 1])


@Y("t8_uchburchak")
def _ub4(rng):
    a = rng.randint(30, 80)
    return _y(rng, f"Teng yonli uchburchakda asosdagi burchak {a}°. Uchidagi burchak necha gradus?", 180 - 2 * a, [f"180 − 2·{a} = {180 - 2 * a}."], noto=[180 - a, 2 * a, 90 - a, 180 - a - 10])


@O("t8_uchburchak")
def _ub5(rng):
    t = rng.choice([(3, 4, 5), (5, 12, 13), (6, 8, 10), (9, 12, 15)])
    return _o(f"To‘g‘ri burchakli uchburchak: katetlar {t[0]} sm va {t[1]} sm.", [("a) Gipotenuza (sm):", t[2]), ("b) Perimetri (sm):", sum(t))], [f"a) {t[2]}.", f"b) {t[0]}+{t[1]}+{t[2]} = {sum(t)}."])


@O("t8_uchburchak")
def _ub6(rng):
    a, b = rng.randint(30, 70), rng.randint(30, 70)
    return _o(f"Uchburchakning burchaklari: {a}°, {b}° va C.", [("a) C (°):", 180 - a - b), ("b) Tashqi burchak C yonida (°):", a + b)], [f"a) 180 − {a} − {b}.", f"b) Tashqi burchak = qolgan ikki burchak yig‘indisi = {a + b}."])


# 10 ── aylana
tema("t8_aylana", "Doira va aylana", "Geometriya", "⭕", "Aylana uzunligi, doira yuzasi (π ≈ 3,14), sektor", [
    ("Formulalar", "C = 2πr\nS = πr²\nπ ≈ 3,14", "Aylana uzunligi ikki pi er; doira yuzasi pi er kvadrat. Masalalarda pi ni uch butun o‘n to‘rt yuzdan deb olamiz."),
    ("Radius va diametr", "d = 2r\nC = πd", "Diametr radiusdan ikki marta uzun. Aylana uzunligi diametrni pi ga ko‘paytirishga teng."),
])


@Y("t8_aylana")
def _a1(rng):
    r = rng.randint(2, 12)
    return _y(rng, f"Radiusi {r} sm bo‘lgan doiraning diametri necha sm?", 2 * r, [f"d = 2r = {2 * r}."], noto=[r, r * r, r + 2, 4 * r])


@Y("t8_aylana")
def _a2(rng):
    r = rng.randint(1, 10); v = Fraction(314, 100) * 2 * r
    return _y(rng, f"Radiusi {r} sm bo‘lgan aylana uzunligi (π = 3,14) necha sm?", v, [f"C = 2·3,14·{r} = {num(v)}."], noto=[v / 2, Fraction(314, 100) * r * r, v + 2, v * 2])


@Y("t8_aylana")
def _a3(rng):
    r = rng.randint(2, 10); v = Fraction(314, 100) * r * r
    return _y(rng, f"Radiusi {r} sm bo‘lgan doiraning yuzasi (π = 3,14) necha kv. sm?", v, [f"S = 3,14·{r}² = {num(v)}."], noto=[v * 2 / r, Fraction(314, 100) * 2 * r, v + r, v / 2])


@Y("t8_aylana")
def _a4(rng):
    r = rng.randint(2, 9)
    return _y(rng, f"Doira radiusi 2 marta oshsa, yuzasi necha marta oshadi?", 4, ["S = πr²: r ikki marta oshsa, yuza 2² = 4 marta oshadi."], noto=[2, 3, 8, 6])


@O("t8_aylana")
def _a5(rng):
    r = rng.randint(2, 10)
    return _o(f"Doira radiusi {r} sm (π = 3,14).", [("a) Uzunlik (sm):", Fraction(314, 100) * 2 * r), ("b) Yuza (kv. sm):", Fraction(314, 100) * r * r)], [f"a) 2·3,14·{r}.", f"b) 3,14·{r}²."])


@O("t8_aylana")
def _a6(rng):
    d = rng.choice([4, 6, 8, 10, 12, 20])
    return _o(f"Aylana diametri {d} m (π = 3,14).", [("a) Radiusi (m):", d // 2), ("b) Uzunligi (m):", Fraction(314, 100) * d)], [f"a) {d} : 2.", f"b) 3,14·{d}."])


# 11 ── statistika
tema("t8_stat", "O‘rtacha, mediana, moda", "Ma’lumotlar", "📊", "Ma’lumotlar to‘plamining markaziy qiymatlari", [
    ("O‘rtacha", "O‘rtacha = yig‘indi : soni", "O‘rtacha arifmetik — barcha qiymatlar yig‘indisini ularning soniga bo‘lish."),
    ("Mediana va moda", "Mediana — tartiblangan qatorning o‘rtasi\nModa — eng ko‘p uchraydigan qiymat", "Qiymatlarni kichikdan kattaga tartiblang: o‘rtadagi son mediana. Eng ko‘p takrorlangan son — moda."),
])


@Y("t8_stat")
def _s1(rng):
    v = [rng.randint(3, 15) for _ in range(5)]; v[-1] += (5 - sum(v) % 5) % 5
    return _y(rng, f"Sonlar: {', '.join(map(str, v))}. O‘rtachasi nechaga teng?", sum(v) // 5, [f"{sum(v)} : 5 = {sum(v) // 5}."], noto=[sum(v) // 5 + 1, sum(v) // 5 - 1, max(v), sorted(v)[2]])


@Y("t8_stat")
def _s2(rng):
    v = rng.sample(range(2, 40), 5)
    return _y(rng, f"Sonlar: {', '.join(map(str, v))}. Medianasi nechaga teng?", sorted(v)[2], ["Tartiblab o‘rtadagisini olamiz."], noto=[sorted(v)[1], sorted(v)[3], v[2] if v[2] != sorted(v)[2] else sum(v) // 5 + 1, max(v)])


@Y("t8_stat")
def _s3(rng):
    m = rng.randint(2, 9); v = [m, m, m] + rng.sample([x for x in range(1, 12) if x != m], 3); rng.shuffle(v)
    return _y(rng, f"Sonlar: {', '.join(map(str, v))}. Modasi nechaga teng?", m, ["Eng ko‘p takrorlangan."], noto=[x for x in v if x != m][:3])


@Y("t8_stat")
def _s4(rng):
    a, b, c = rng.randint(60, 90), rng.randint(60, 90), rng.randint(60, 90); d = (4 * 75) - a - b - c
    d = max(40, min(100, d)); s = a + b + c + d
    return _y(rng, f"To‘rt imtihon bali: {a}, {b}, {c}, {d}. O‘rtachasi nechaga teng?", Fraction(s, 4), [f"{s} : 4 = {num(Fraction(s, 4))}."], noto=[Fraction(s, 4) + 1, Fraction(s, 3), max(a, b, c, d), Fraction(s, 4) - 2])


@O("t8_stat")
def _s5(rng):
    v = rng.sample(range(3, 30), 5)
    return _o(f"Ma’lumotlar: {', '.join(map(str, v))}.", [("a) Eng katta va eng kichik farqi (o‘lchov kengligi):", max(v) - min(v)), ("b) Medianasi:", sorted(v)[2])], [f"a) {max(v)} − {min(v)}.", f"b) Tartiblangan: {sorted(v)}, o‘rtasi {sorted(v)[2]}."])


@O("t8_stat")
def _s6(rng):
    v = [rng.randint(5, 20) for _ in range(4)]; v.append(5 * 12 - sum(v) if 5 * 12 - sum(v) > 0 else 20)
    return _o(f"Besh o‘quvchining bo‘yi (sm bo‘yicha qisqartirilgan): {', '.join(map(str, v))}.", [("a) Yig‘indi:", sum(v)), ("b) O‘rtacha:", Fraction(sum(v), 5))], [f"a) {sum(v)}.", f"b) {sum(v)} : 5."])


# 12 ── ehtimollik
tema("t8_ehtimol", "Ehtimollik asoslari", "Ehtimollik", "🎲", "Oddiy hodisa ehtimoli, qulay holatlar va barcha holatlar nisbati", [
    ("Ehtimol", "P = qulay holatlar / barcha holatlar\n0 ≤ P ≤ 1", "Ehtimol qulay natijalar sonini barcha teng imkoniyatli natijalar soniga bo‘lish bilan topiladi."),
    ("Qarama-qarshi", "P(A) + P(A emas) = 1\nTanga: 1/2", "Hodisa ro‘y berishi va ro‘y bermasligi ehtimollari yig‘indisi birga teng."),
])


@Y("t8_ehtimol")
def _h1(rng):
    k, b = rng.randint(2, 7), rng.randint(2, 8)
    return _y(rng, f"Qutida {k} ta qizil va {b} ta ko‘k shar bor. Ko‘z yumib bitta shar olinganda qizil bo‘lish ehtimoli?", Fraction(k, k + b),
              [f"{k}/({k}+{b}) = {num(Fraction(k, k + b))}."], noto=[Fraction(b, k + b), Fraction(k, b), Fraction(1, k + b), Fraction(k + 1, k + b + 1)])


@Y("t8_ehtimol")
def _h2(rng):
    return _y(rng, "Oddiy o‘yin kubigi tashlanganda juft son tushish ehtimoli?", "1/2", ["6 holatdan 3 tasi juft: 3/6 = 1/2."], noto=["1/3", "1/6", "2/3"])


@Y("t8_ehtimol")
def _h3(rng):
    n = rng.randint(5, 12); k = rng.randint(1, n - 1)
    return _y(rng, f"Hodisa ehtimoli {k}/{n} ga teng. Hodisa ro‘y bermasligi ehtimoli?", f"{n - k}/{n}", ["1 − P."], noto=[f"{k}/{n + 1}", f"{n}/{k}", f"{k + 1}/{n}", f"{n - k}/{n + 1}", f"{n - k + 1}/{n}", f"{k}/{n}"])


@Y("t8_ehtimol")
def _h4(rng):
    n = rng.choice([20, 25, 40, 50]); k = rng.choice([x for x in range(1, 10) if (n * x) % 10 == 0 or True])
    return _y(rng, f"Sinfda {n} o‘quvchi, {k} tasi chap qo‘l. Tasodifiy o‘quvchining chap qo‘l bo‘lish ehtimoli (kasr)?", Fraction(k, n), [f"{k}/{n}."], noto=[Fraction(n - k, n), Fraction(k, n + 1), Fraction(1, n), Fraction(n, k)])


@O("t8_ehtimol")
def _h5(rng):
    k, b = rng.randint(2, 8), rng.randint(2, 8)
    return _o(f"Qutida {k} ta oq va {b} ta qora shar.", [("a) Barcha holatlar soni:", k + b), ("b) Oq shar olinishi qulay holatlar soni:", k)], [f"a) {k}+{b}.", f"b) {k}."])


@O("t8_ehtimol")
def _h6(rng):
    return _o("Oddiy o‘yin kubigi bir marta tashlanadi.", [("a) Barcha natijalar soni:", 6), ("b) 4 dan katta tushish natijalari soni:", 2)], ["a) 6.", "b) 5 va 6."])


# 13 ── koordinata
tema("t8_koord", "Koordinatalar tekisligi", "Geometriya", "🧭", "Nuqta koordinatalari, kesma uzunligi, o‘rtasi, ko‘chirish", [
    ("Nuqta", "A(x; y)\nx — gorizontal, y — vertikal", "Nuqta ikki koordinata bilan beriladi: birinchisi x, ikkinchisi y."),
    ("Masofa", "Bir to‘g‘ri chiziqda: |x₂ − x₁|\nO‘rta: ((x₁+x₂)/2 ; (y₁+y₂)/2)", "Gorizontal chiziqdagi ikki nuqta orasidagi masofa x lar ayirmasining moduli. Kesma o‘rtasining koordinatalari mos koordinatalarning o‘rtachasi."),
])


@Y("t8_koord")
def _k1(rng):
    x1, x2, y = rng.randint(-8, 0), rng.randint(1, 9), rng.randint(-5, 5)
    return _y(rng, f"A({x1}; {y}) va B({x2}; {y}) nuqtalar orasidagi masofa?", x2 - x1, [f"|{x2} − ({x1})| = {x2 - x1}."], noto=[x2 + x1 if x2 + x1 != x2 - x1 else 1, abs(x1), x2, x2 - x1 + 1])


@Y("t8_koord")
def _k2(rng):
    x1, y1 = rng.randint(-8, 8), rng.randint(-8, 8); dx, dy = 2 * rng.randint(1, 5), 2 * rng.randint(1, 5)
    return _y(rng, f"A({x1}; {y1}) va B({x1 + dx}; {y1 + dy}) kesma o‘rtasining x koordinatasi?", x1 + dx // 2, [f"({x1} + {x1 + dx})/2 = {x1 + dx // 2}."], noto=[x1 + dx, dx // 2, x1, x1 + dx // 2 + 1])


@Y("t8_koord")
def _k3(rng):
    x, y = rng.randint(1, 8), rng.randint(1, 8)
    return _y(rng, f"M({x}; {y}) nuqta x o‘qiga nisbatan simmetrik nuqtasining y koordinatasi?", -y, ["x o‘qiga nisbatan y ning ishorasi o‘zgaradi."], noto=[y, -x, x, y + 1])


@Y("t8_koord")
def _k4(rng):
    x, y, dx, dy = rng.randint(-5, 5), rng.randint(-5, 5), rng.randint(1, 6), rng.randint(1, 6)
    return _y(rng, f"A({x}; {y}) nuqta o‘ngga {dx}, yuqoriga {dy} birlik surildi. Yangi nuqtaning x + y yig‘indisi?", x + y + dx + dy, [f"({x + dx}; {y + dy}); yig‘indi {x + y + dx + dy}."], noto=[x + y, x + y + dx - dy, x + y + dx, x + y + dy])


@O("t8_koord")
def _k5(rng):
    x1, y1 = rng.randint(-6, 0), rng.randint(-6, 0); x2, y2 = x1 + 2 * rng.randint(1, 4), y1 + 2 * rng.randint(1, 4)
    return _o(f"A({x1}; {y1}), B({x2}; {y2}).", [("a) O‘rta nuqtaning x koordinatasi:", (x1 + x2) // 2), ("b) O‘rta nuqtaning y koordinatasi:", (y1 + y2) // 2)], [f"a) ({x1}+{x2})/2.", f"b) ({y1}+{y2})/2."])


@O("t8_koord")
def _k6(rng):
    a, b = rng.randint(1, 9), rng.randint(1, 9)
    return _o(f"Nuqta P({a}; {b}).", [("a) y o‘qiga simmetrik nuqtaning x koordinatasi:", -a), ("b) Koordinata boshigacha gorizontal masofa:", a)], [f"a) −{a}.", f"b) {a}."])


# 14 ── arifmetik progressiya
tema("t8_progressiya", "Qonuniyatlar va n-had formulasi", "Qonuniyatlar", "🔁", "Sonli ketma-ketlikning n-hadini topish va formulani qo‘llash", [
    ("Arifmetik", "aₙ = a₁ + d·(n − 1)\n3, 7, 11, …: aₙ = 3 + 4(n−1)", "Har hadi oldingisidan bir xil d songa farq qiladigan ketma-ketlikda n-had birinchi had plyus d ko‘paytirilgan n minus bir."),
    ("Shakllar", "n-shakldagi cho‘plar soni\n3n + 1", "Shakllar ketma-ketligida o‘zgarishni jadvalga yozib, formula toping."),
])


@Y("t8_progressiya")
def _g1(rng):
    a, d, n = rng.randint(1, 9), rng.randint(2, 7), rng.randint(8, 20)
    return _y(rng, f"Ketma-ketlik: {a}, {a + d}, {a + 2 * d}, … 20-had emas, {n}-hadini toping.", a + d * (n - 1), [f"a₁ + d(n−1) = {a} + {d}·{n - 1}."], noto=[a + d * n, a + d * (n - 2), d * n, a * d * n])


@Y("t8_progressiya")
def _g2(rng):
    a, d = rng.randint(2, 9), rng.randint(2, 6)
    return _y(rng, f"Ketma-ketlik n-hadi aₙ = {d}n + {a}. a₅ nechaga teng?", 5 * d + a, [f"{d}·5 + {a} = {5 * d + a}."], noto=[5 + d + a, d * 4 + a, d * 6 + a, 5 * (d + a)])


@Y("t8_progressiya")
def _g3(rng):
    d = rng.randint(3, 9); a = rng.randint(1, 8); k = rng.randint(5, 12)
    return _y(rng, f"{a}, {a + d}, {a + 2 * d}, … ketma-ketlikda {a + d * (k - 1)} soni nechanchi had?", k, [f"{a} + {d}(n−1) = {a + d * (k - 1)} → n = {k}."], noto=[k + 1, k - 1, d, k * 2])


@Y("t8_progressiya")
def _g4(rng):
    p = rng.randint(3, 6); n = rng.randint(5, 10)
    return _y(rng, f"1-shaklda {p + 1} ta cho‘p, har keyingisida {p} tadan ko‘p. {n}-shaklda nechta cho‘p?", p + 1 + p * (n - 1), [f"{p + 1} + {p}·{n - 1}."], noto=[p * n, p * n + 2, (p + 1) * n, p + 1 + p * n])


@O("t8_progressiya")
def _g5(rng):
    a, d = rng.randint(2, 9), rng.randint(2, 7)
    return _o(f"Ketma-ketlik: {a}, {a + d}, {a + 2 * d}, …", [("a) d =", d), ("b) 10-had:", a + 9 * d)], [f"a) {d}.", f"b) {a} + 9·{d}."])


@O("t8_progressiya")
def _g6(rng):
    d = rng.randint(2, 6); a = rng.randint(1, 5)
    return _o(f"aₙ = {d}n + {a}.", [("a) a₁ =", d + a), ("b) a₁₀ =", 10 * d + a)], [f"a) {d}+{a}.", f"b) {10 * d}+{a}."])
