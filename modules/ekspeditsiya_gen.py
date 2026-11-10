"""REV456: «Matematik ekspeditsiya» — misol generatorlari (maktab matematikasi darslari generatorlaridan: tools/maktab_mat).
Har chaqiruv: (savol, javob, yechim, xato_variantlar). Javoblarni Python hisoblaydi."""
import math, random
from fractions import Fraction

def fk(f):
    f = Fraction(f)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def gen34(tur, rng, kk=None):
    """→ (savol, javob, yechim, [xato javoblar])"""
    r = rng.randint
    if tur == "korxona":   # ko'p xonali sonlar, xonalar
        a = r(1000, 999999); s = str(a)
        return (f"{a} sonida nechta minglik bor? (minglar sinfidagi sonni yozing)", a // 1000, f"${a} = {a // 1000}$ ming ${a % 1000}$\nJavob: {a // 1000}", [a // 100, a // 10000 or 1, a % 1000])
    if tur == "taqqos":
        a, b = r(1000, 99999), r(1000, 99999)
        return (f"Qaysi son katta: {a} yoki {b}?", max(a, b), f"Avval xonalar sonini, keyin chapdan boshlab raqamlarni solishtiramiz.\nJavob: {max(a, b)}", [min(a, b), a + b, abs(a - b) or 1])
    if tur == "qosh":
        a, b = r(1000, 49999), r(1000, 49999)
        return (f"${a} + {b} = \\;?$", a + b, f"Ustunda: xonalar ostma-ost, birliklardan boshlab qo‘shamiz.\nJavob: {a + b}", [a + b + 10, a + b - 100, a + b + 1000])
    if tur == "ayir":
        a = r(5000, 99999); b = r(1000, a - 1)
        return (f"${a} - {b} = \\;?$", a - b, f"Ustunda: yetmasa, katta xonadan 1 ni olib 10 qilamiz.\nJavob: {a - b}", [a - b + 10, a - b - 100, a + b])
    if tur == "kop10":
        a, k = r(2, 999), rng.choice([10, 100, 1000])
        return (f"${a} \\cdot {k} = \\;?$", a * k, f"{k} ga ko‘paytirishda oxiriga {len(str(k)) - 1} ta nol yoziladi.\nJavob: {a * k}", [a * k * 10, a * k // 10 or 1, a + k])
    if tur == "kop1":
        a, b = r(12, 9999), r(2, 9)
        return (f"${a} \\cdot {b} = \\;?$", a * b, f"Xonalarni alohida ko‘paytirib, qo‘shamiz (taqsimot qonuni).\nJavob: {a * b}", [a * b + b, a * b - 10, a + b])
    if tur == "kop2":
        a, b = r(12, 999), r(11, 99)
        return (f"${a} \\cdot {b} = \\;?$", a * b, f"${a} \\cdot {b // 10 * 10} + {a} \\cdot {b % 10} = {a * (b // 10 * 10)} + {a * (b % 10)} = {a * b}$\nJavob: {a * b}", [a * b + a, a * (b // 10 * 10), a * b - 10])
    if tur == "bol":
        b, q = r(2, 9), r(12, 999)
        return (f"${b * q} : {b} = \\;?$", q, f"Burchakli bo‘lish: chapdan xonalab bo‘lamiz, tekshirish ${q} \\cdot {b} = {b * q}$.\nJavob: {q}", [q + 1, q * 10, q - 10])
    if tur == "bol2":
        b, q = r(11, 99), r(2, 99)
        return (f"${b * q} : {b} = \\;?$", q, f"Bo‘linmani chamalab topamiz va tekshiramiz: ${q} \\cdot {b} = {b * q}$.\nJavob: {q}", [q + 1, q + 10, q - 1])
    if tur == "qoldiq":
        b, q, c = r(3, 9), r(5, 99), 0
        c = r(1, b - 1); a = b * q + c
        return (f"${a}$ ni ${b}$ ga bo‘lganda qoldiq nechaga teng?", c, f"${a} = {b} \\cdot {q} + {c}$, qoldiq bo‘luvchidan kichik: ${c} < {b}$.\nJavob: {c}", [c + 1, q, b])
    if tur == "alomat":
        k = kk if kk in (2, 3, 4, 5, 9, 10) else rng.choice([2, 3, 4, 5, 9, 10]); a = r(100, 9999)
        if rng.random() < 0.5:
            a -= a % k   # yarmi bo'linadigan son bo'lsin
        ha = a % k == 0
        qoida = {2: "oxirgi raqami juft", 3: "raqamlar yig‘indisi 3 ga bo‘linadi", 4: "oxirgi ikki raqamidan tuzilgan son 4 ga bo‘linadi", 5: "oxirgi raqami 0 yoki 5", 9: "raqamlar yig‘indisi 9 ga bo‘linadi", 10: "oxirgi raqami 0"}[k]
        return (f"{a} soni {k} ga bo‘linadimi? (ha / yo‘q)", "ha" if ha else "yo‘q", f"Alomat: {qoida}.\nJavob: {'ha' if ha else 'yo‘q'}", ["yo‘q" if ha else "ha"])
    if tur == "karrali":
        a = r(2, 9) * r(2, 9)
        bl = [d for d in range(1, a + 1) if a % d == 0]
        return (f"{a} sonining nechta bo‘luvchisi bor?", len(bl), f"Bo‘luvchilari: {', '.join(map(str, bl))}.\nJavob: {len(bl)}", [len(bl) + 1, len(bl) - 1, a // 2])
    if tur == "perimetr":
        a, b = r(3, 30), r(3, 30)
        return (f"To‘g‘ri to‘rtburchakning tomonlari {a} sm va {b} sm. Perimetri?", 2 * (a + b), f"$P = 2 \\cdot ({a} + {b}) = {2 * (a + b)}$ sm\nJavob: {2 * (a + b)}", [a * b, a + b, 2 * a + b])
    if tur == "yuz":
        a, b = r(3, 25), r(3, 25)
        return (f"To‘g‘ri to‘rtburchakning bo‘yi {a} m, eni {b} m. Yuzi necha m²?", a * b, f"$S = {a} \\cdot {b} = {a * b}$ m²\nJavob: {a * b}", [2 * (a + b), a + b, a * b + a])
    if tur == "massa":
        v = rng.choice([("kg", "g", 1000), ("t", "kg", 1000), ("s", "kg", 100), ("t", "s", 10)]); x = r(2, 19)
        return (f"{x} {v[0]} — necha {v[1]}?", x * v[2], f"1 {v[0]} = {v[2]} {v[1]}\nJavob: {x * v[2]}", [x * v[2] * 10, x * v[2] // 10 or 1, x + v[2]])
    if tur == "uzunlik":
        v = rng.choice([("km", "m", 1000), ("m", "sm", 100), ("dm", "mm", 100), ("m", "mm", 1000)]); x = r(2, 19)
        return (f"{x} {v[0]} — necha {v[1]}?", x * v[2], f"1 {v[0]} = {v[2]} {v[1]}\nJavob: {x * v[2]}", [x * v[2] * 10, x * v[2] // 10 or 1, x + v[2]])
    if tur == "yuzbirlik":
        v = rng.choice([("m²", "dm²", 100), ("dm²", "sm²", 100), ("ga", "ar", 100), ("ar", "m²", 100), ("km²", "ga", 100)]); x = r(2, 19)
        return (f"{x} {v[0]} — necha {v[1]}?", x * v[2], f"1 {v[0]} = {v[2]} {v[1]}\nJavob: {x * v[2]}", [x * 10, x * v[2] * 10, x + v[2]])
    if tur == "hajm":
        a, b, c = r(2, 12), r(2, 12), r(2, 12)
        return (f"To‘g‘ri burchakli parallelepipedning o‘lchamlari {a} sm, {b} sm va {c} sm. Hajmi necha sm³?", a * b * c, f"$V = {a} \\cdot {b} \\cdot {c} = {a * b * c}$ sm³\nJavob: {a * b * c}", [2 * (a * b + b * c + a * c), a + b + c, a * b])
    if tur == "kub":
        a = r(2, 15)
        return (f"Kubning qirrasi {a} sm. Barcha 12 ta qirrasi uzunliklari yig‘indisi?", 12 * a, f"$12 \\cdot {a} = {12 * a}$ sm\nJavob: {12 * a}", [6 * a, 4 * a, a ** 3])
    if tur == "ulush":
        n = rng.choice([2, 3, 4, 5, 6, 8, 10]); x = n * r(2, 20)
        return (f"{x} ning 1/{n} qismi nechaga teng?", x // n, f"Butunni {n} ta teng bo‘lakka bo‘lamiz: ${x} : {n} = {x // n}$\nJavob: {x // n}", [x * n, x - n, x // n + 1])
    if tur == "butun":
        n, q = rng.choice([2, 3, 4, 5]), r(2, 30)
        return (f"Sonning 1/{n} qismi {q} ga teng. Sonning o‘zi nechaga teng?", n * q, f"Bitta bo‘lak {q}, butunda {n} ta bo‘lak: ${q} \\cdot {n} = {n * q}$\nJavob: {n * q}", [q, q + n, q // n or 1])
    if tur == "kasrqism":
        d = rng.choice([3, 4, 5, 6, 8]); c = r(1, d - 1); x = d * r(2, 15)
        return (f"{x} ning {c}/{d} qismini toping.", x // d * c, f"${x} : {d} \\cdot {c} = {x // d * c}$\nJavob: {x // d * c}", [x // d, x * c, x // c if x % c == 0 else x - c])
    if tur == "kasrtaq":
        d = rng.choice([5, 7, 8, 9, 10, 12]); a, b = rng.sample(range(1, d), 2)
        return (f"Qaysi kasr katta: {a}/{d} yoki {b}/{d}?", f"{max(a, b)}/{d}", f"Maxrajlari teng — surati katta kasr katta.\nJavob: {max(a, b)}/{d}", [f"{min(a, b)}/{d}", f"{a + b}/{d}"])
    if tur == "kasrqosh":
        d = rng.choice([5, 7, 8, 9, 10, 12]); a = r(1, d - 2); b = r(1, d - a - 1)
        if rng.random() < 0.5:
            return (f"${a}/{d} + {b}/{d} = \\;?$", f"{a + b}/{d}", f"Maxraj o‘zgarmaydi, suratlar qo‘shiladi.\nJavob: {a + b}/{d}", [f"{a + b}/{2 * d}", f"{a * b}/{d}"])
        return (f"${a + b}/{d} - {b}/{d} = \\;?$", f"{a}/{d}", f"Maxraj o‘zgarmaydi, suratlar ayiriladi.\nJavob: {a}/{d}", [f"{a}/{0 + d * 2}", f"{a + 1}/{d}"])
    if tur == "aralash":
        d = rng.choice([3, 4, 5, 6, 8]); w = r(1, 5); c = r(1, d - 1)
        return (f"${w}\\,\\frac{{{c}}}{{{d}}}$ ni noto‘g‘ri kasrga aylantiring.", f"{w * d + c}/{d}", f"${w} \\cdot {d} + {c} = {w * d + c}$\nJavob: {w * d + c}/{d}", [f"{w + c}/{d}", f"{w * c + d}/{d}"])
    if tur == "kasrnat":
        d = rng.choice([5, 7, 9, 11]); a = r(1, 4); k = r(2, 3)
        return (f"${a}/{d} \\cdot {k} = \\;?$", fk(Fraction(a * k, d)), f"Surat songa ko‘paytiriladi: ${a} \\cdot {k} = {a * k}$\nJavob: {fk(Fraction(a * k, d))}", [f"{a * k}/{d * k}", f"{a}/{d * k}"])
    if tur == "onli":
        a = r(1, 999); d = rng.choice([10, 100, 1000])
        s = f"{a / d:.{len(str(d)) - 1}f}".replace(".", ",")
        return (f"{a}/{d} ni o‘nli kasr ko‘rinishida yozing.", s, f"Maxrajdagi nollar soni — verguldan keyingi raqamlar soni.\nJavob: {s}", [str(a), f"{a / (d * 10):.{len(str(d))}f}".replace(".", ",")])
    if tur == "foiz":
        p, x = rng.choice([10, 20, 25, 50]), r(2, 40) * 20
        return (f"{x} ning {p}% i nechaga teng?", x * p // 100, f"1% — yuzdan bir qism: ${x} : 100 \\cdot {p} = {x * p // 100}$\nJavob: {x * p // 100}", [x * p, x // p, x - p])
    if tur == "yaxlit":
        a = r(1000, 99999); k = rng.choice([10, 100, 1000]); y = int((a + k / 2) // k * k)
        return (f"{a} ni {'o‘nliklar' if k == 10 else 'yuzliklar' if k == 100 else 'minglar'}gacha yaxlitlang.", y, f"Keyingi raqam 5 va undan katta bo‘lsa — oshiramiz, aks holda o‘zgarmaydi.\nJavob: {y}", [a // k * k + (0 if y != a // k * k else k), a, y + k])
    if tur == "harakat":
        v, t = r(4, 90), r(2, 9)
        return (f"Avtomobil soatiga {v} km tezlik bilan {t} soat yurdi. Qancha masofa bosib o‘tdi?", v * t, f"$S = v \\cdot t = {v} \\cdot {t} = {v * t}$ km\nJavob: {v * t}", [v + t, v * t + v, v])
    if tur == "qarama":
        v1, v2, t = r(30, 70), r(30, 70), r(2, 5)
        return (f"Ikki mashina bir-biriga qarab {v1} km/soat va {v2} km/soat tezlik bilan yurdi va {t} soatda uchrashdi. Oradagi masofa?", (v1 + v2) * t, f"Yaqinlashish tezligi: ${v1} + {v2} = {v1 + v2}$; $S = {v1 + v2} \\cdot {t} = {(v1 + v2) * t}$ km\nJavob: {(v1 + v2) * t}", [abs(v1 - v2) * t or 1, v1 + v2, (v1 + v2) * t + 10])
    if tur == "quvlama":
        v2 = r(40, 70); v1 = v2 + r(5, 20); s = (v1 - v2) * r(2, 6)
        return (f"Orasida {s} km bo‘lgan ikki mashina bir yo‘nalishda ketdi: oldingisi {v2} km/soat, ortdagisi {v1} km/soat. Necha soatda quvib yetadi?", s // (v1 - v2), f"Yaqinlashish tezligi: ${v1} - {v2} = {v1 - v2}$; $t = {s} : {v1 - v2} = {s // (v1 - v2)}$\nJavob: {s // (v1 - v2)}", [s // (v1 + v2) or 1, s // (v1 - v2) + 1, v1 - v2])
    if tur == "qiymat":
        n, b = r(2, 12), r(2, 9) * 1000
        return (f"Bitta daftar {b} so‘m. {n} ta daftar necha so‘m?", n * b, f"Qiymat = narx · miqdor: ${b} \\cdot {n} = {n * b}$\nJavob: {n * b}", [n + b, n * b + b, b])
    if tur == "unum":
        p, t = r(5, 30), r(2, 9)
        return (f"Usta soatiga {p} ta detal yasaydi. {t} soatda nechta yasaydi?", p * t, f"Ish = unumdorlik · vaqt: ${p} \\cdot {t} = {p * t}$\nJavob: {p * t}", [p + t, p * t + p, p])
    if tur == "vaqt":
        s, m = r(1, 5), r(1, 59)
        return (f"{s} soat {m} minut — necha minut?", 60 * s + m, f"$60 \\cdot {s} + {m} = {60 * s + m}$\nJavob: {60 * s + m}", [100 * s + m, 60 * s, s + m])
    if tur == "tenglama":
        a, x = r(2, 12), r(2, 40); b = r(1, 50)
        return (f"${a} \\cdot x + {b} = {a * x + b}$. $x$ = ?", x, f"${a} \\cdot x = {a * x + b} - {b} = {a * x}$; $x = {a * x} : {a} = {x}$\nJavob: {x}", [x + 1, a * x, x + b])
    if tur == "ifoda":
        a, b, c = r(2, 9), r(10, 50), r(2, 9)
        return (f"${b} + {a} \\cdot ({c} + 3) = \\;?$", b + a * (c + 3), f"Qavs, keyin ko‘paytirish, keyin qo‘shish: ${c} + 3 = {c + 3}$; ${a} \\cdot {c + 3} = {a * (c + 3)}$; ${b} + {a * (c + 3)} = {b + a * (c + 3)}$\nJavob: {b + a * (c + 3)}", [(b + a) * (c + 3), b + a * c + 3, b + a + c + 3])
    if tur == "toplam":
        a, b, ab = r(10, 25), r(10, 25), r(2, 9)
        return (f"Sinfda {a} kishi shaxmat, {b} kishi futbol o‘ynaydi, {ab} kishi ikkalasini. Kamida bittasini necha kishi o‘ynaydi?", a + b - ab, f"${a} + {b} - {ab} = {a + b - ab}$ (ikkalasini o‘ynaganlar ikki marta sanalmasin)\nJavob: {a + b - ab}", [a + b, a + b + ab, ab])
    if tur == "ortacha":
        xs = [r(2, 20) for _ in range(rng.choice([3, 4, 5]))]
        while sum(xs) % len(xs):
            xs[0] += 1
        return (f"{', '.join(map(str, xs))} sonlarining o‘rta arifmetigi?", sum(xs) // len(xs), f"Yig‘indi: {sum(xs)}, sonlar soni: {len(xs)}; ${sum(xs)} : {len(xs)} = {sum(xs) // len(xs)}$\nJavob: {sum(xs) // len(xs)}", [sum(xs), max(xs), min(xs)])
    if tur == "burchak":
        a = r(20, 160)
        tur_ = "o‘tkir" if a < 90 else "o‘tmas"
        return (f"{a}° li burchak qanday burchak? (o‘tkir / to‘g‘ri / o‘tmas)", tur_, f"90° dan kichik — o‘tkir, 90° — to‘g‘ri, 90° dan katta — o‘tmas.\nJavob: {tur_}", ["to‘g‘ri", "o‘tmas" if tur_ == "o‘tkir" else "o‘tkir"])
    if tur == "jism":
        j = rng.choice([("kub", 8, 12, 6), ("to‘g‘ri burchakli parallelepiped", 8, 12, 6), ("uchburchakli prizma", 6, 9, 5), ("to‘rtburchakli piramida", 5, 8, 5), ("uchburchakli piramida", 4, 6, 4)])
        return (f"{j[0].capitalize()}ning nechta qirrasi bor?", j[2], f"Uchlari {j[1]} ta, qirralari {j[2]} ta, yoqlari {j[3]} ta.\nJavob: {j[2]}", [j[1], j[3], j[2] + 2])
    if tur == "koordinata":
        a, b = r(1, 30), r(1, 30)
        return (f"Koordinata nurida A({a}) va B({b}) nuqtalar orasidagi masofa?", abs(a - b), f"Kattasidan kichigini ayiramiz: ${max(a, b)} - {min(a, b)} = {abs(a - b)}$\nJavob: {abs(a - b)}", [a + b, max(a, b), abs(a - b) + 1])
    # aralash / takrorlash
    return gen34(rng.choice(["qosh", "ayir", "kop1", "bol", "perimetr", "tenglama"]), rng)



def gen56(tur, rng, kk=None):
    r = rng.randint

    def togri():   # to'g'ri kasr: surat < maxraj, qisqarmagan
        while True:
            d = r(2, 9); f = Fraction(r(1, d - 1), d)
            if f.denominator == d:
                return f
    if tur == "kasrkop":
        a, b = togri(), togri()
        return (f"${fk(a)} \\cdot {fk(b)} = \\;?$", fk(a * b), f"Surat suratga, maxraj maxrajga ko‘paytiriladi va qisqartiriladi.\nJavob: {fk(a * b)}", [fk(a + b), fk(Fraction(a.numerator * b.numerator, a.denominator + b.denominator))])
    if tur == "kasr_n_bol":
        a, n = togri(), r(2, 6)
        return (f"${fk(a)} : {n} = \\;?$", fk(a / n), f"Kasrni natural songa bo‘lishda maxraj shu songa ko‘paytiriladi.\nJavob: {fk(a / n)}", [fk(a * n), fk(Fraction(a.numerator, a.denominator + n))])
    if tur == "n_kasr_bol":
        n, a = r(2, 9), togri()
        return (f"${n} : {fk(a)} = \\;?$", fk(n / a), f"Kasrga bo‘lish — teskari kasrga ko‘paytirish: ${n} \\cdot {fk(1 / a)} = {fk(n / a)}$\nJavob: {fk(n / a)}", [fk(n * a), fk(a / n)])
    if tur == "kasr_n_kop":
        a, n = togri(), r(2, 9)
        return (f"${fk(a)} \\cdot {n} = \\;?$", fk(a * n), f"Surat songa ko‘paytiriladi, maxraj o‘zgarmaydi; keyin qisqartiramiz.\nJavob: {fk(a * n)}", [fk(Fraction(a.numerator * n, a.denominator * n)), fk(a + n)])
    if tur == "kasrbol":
        a, b = togri(), togri()
        return (f"${fk(a)} : {fk(b)} = \\;?$", fk(a / b), f"Bo‘luvchini teskarisiga ko‘paytiramiz: ${fk(a)} \\cdot {fk(1 / b)} = {fk(a / b)}$\nJavob: {fk(a / b)}", [fk(a * b), fk(b / a)])
    if tur == "kasrqosh2":
        a, b = togri(), togri()
        return (f"${fk(a)} + {fk(b)} = \\;?$", fk(a + b), f"Umumiy maxrajga keltiramiz (EKUK), keyin suratlarni qo‘shamiz.\nJavob: {fk(a + b)}", [f"{a.numerator + b.numerator}/{a.denominator + b.denominator}", fk(a * b)])
    if tur == "qisqart":
        k = r(2, 9); a, b = r(1, 9), r(2, 12)
        f = Fraction(a, b)
        return (f"${a * k}/{b * k}$ kasrni qisqartiring.", fk(f), f"Surat va maxrajni EKUB ga bo‘lamiz.\nJavob: {fk(f)}", [f"{a * k}/{b}", f"{a}/{b * k}"])
    if tur == "ekub":
        a, b = r(2, 9) * r(2, 12), r(2, 9) * r(2, 12)
        from math import gcd
        return (f"EKUB({a}; {b}) = ?", gcd(a, b), f"Ikkala sonni tub ko‘paytuvchilarga ajratib, umumiylarini ko‘paytiramiz.\nJavob: {gcd(a, b)}", [a * b // gcd(a, b), gcd(a, b) * 2, 1])
    if tur == "onli10":
        a = r(1, 9999) / 100; k = rng.choice([10, 100, 1000])
        j = round(a * k, 2); js = (f"{j:g}").replace(".", ",")
        return (f"${str(a).replace('.', '{,}')} \\cdot {k} = \\;?$", js, f"Vergul {len(str(k)) - 1} xona o‘ngga suriladi.\nJavob: {js}", [(f"{round(a * k / 10, 3):g}").replace(".", ","), (f"{round(a * k * 10, 2):g}").replace(".", ",")])
    if tur == "nisbat":
        p, q = rng.sample(range(1, 8), 2); k = r(2, 12); jami = (p + q) * k
        return (f"{jami} ta konfet ikki bolaga {p}:{q} nisbatda bo‘lindi. Birinchisiga nechta tegdi?", p * k, f"Jami ulushlar: ${p} + {q} = {p + q}$; bir ulush: ${jami} : {p + q} = {k}$; birinchisiga: ${p} \\cdot {k} = {p * k}$\nJavob: {p * k}", [q * k, jami // 2, p + k])
    if tur == "meyor":
        n, b = r(2, 9), r(2, 12)
        return (f"{n} ta daftar {n * b * 1000} so‘m. Bitta daftar necha so‘m?", b * 1000, f"Me’yor = jami : miqdor: ${n * b * 1000} : {n} = {b * 1000}$\nJavob: {b * 1000}", [n * b * 1000 * n, b * 100, b * 1000 + 1000])
    if tur == "osish":
        x = r(2, 40) * 100; p = rng.choice([10, 20, 25, 50])
        return (f"Narx {x} so‘m edi, {p}% ga oshdi. Yangi narx?", x + x * p // 100, f"${x} + {x} \\cdot {p}/100 = {x + x * p // 100}$\nJavob: {x + x * p // 100}", [x * p // 100, x - x * p // 100, x + p])
    if tur == "chegirma":
        x = r(2, 50) * 1000; p = rng.choice([10, 15, 20, 25, 30])
        return (f"Narxi {x} so‘m bo‘lgan mahsulotga {p}% chegirma qilindi. Endi necha so‘m?", x - x * p // 100, f"Chegirma: ${x} \\cdot {p}/100 = {x * p // 100}$; ${x} - {x * p // 100} = {x - x * p // 100}$\nJavob: {x - x * p // 100}", [x * p // 100, x + x * p // 100, x - p])
    if tur == "burchak_chiziq":
        a = r(20, 160)
        return (f"To‘g‘ri chiziqdagi ikki qo‘shni burchakdan biri {a}°. Ikkinchisi?", 180 - a, f"To‘g‘ri chiziqdagi burchaklar yig‘indisi 180°: $180 - {a} = {180 - a}$\nJavob: {180 - a}", [a, 360 - a, 90 - a if a < 90 else a - 90])
    if tur == "burchak_nuqta":
        a, b = r(40, 150), r(40, 150)
        return (f"Nuqta atrofidagi uch burchakdan ikkitasi {a}° va {b}°. Uchinchisi?", 360 - a - b, f"Nuqta atrofidagi burchaklar yig‘indisi 360°: $360 - {a} - {b} = {360 - a - b}$\nJavob: {360 - a - b}", [180 - a - b if a + b < 180 else a + b - 180 or 1, a + b, 360 - a])
    if tur == "uchburchak_burchak":
        a, b = r(20, 100), r(20, 60)
        return (f"Uchburchakning ikki burchagi {a}° va {b}°. Uchinchi burchagi?", 180 - a - b, f"Uchburchak burchaklari yig‘indisi 180°: $180 - {a} - {b} = {180 - a - b}$\nJavob: {180 - a - b}", [360 - a - b, a + b, 90 - b])
    if tur == "uchburchak_yuz":
        a, h = r(2, 20) * 2, r(2, 20)
        return (f"Uchburchakning asosi {a} sm, balandligi {h} sm. Yuzi?", a * h // 2, f"$S = \\frac{{a \\cdot h}}{{2}} = \\frac{{{a} \\cdot {h}}}{{2}} = {a * h // 2}$ sm²\nJavob: {a * h // 2}", [a * h, a + h, a * h // 4 or 1])
    if tur == "tortburchak_burchak":
        a, b, c = r(60, 120), r(60, 120), r(50, 110)
        return (f"To‘rtburchakning uch burchagi {a}°, {b}° va {c}°. To‘rtinchisi?", 360 - a - b - c, f"To‘rtburchak burchaklari yig‘indisi 360°: $360 - {a} - {b} - {c} = {360 - a - b - c}$\nJavob: {360 - a - b - c}", [180 - c, a + b + c - 180, 360 - a - b])
    if tur == "aylana":
        rr = r(1, 20)
        j = f"{round(2 * 3.14 * rr, 2):g}".replace(".", ",")
        return (f"Radiusi {rr} sm bo‘lgan aylana uzunligini toping (π ≈ 3,14).", j, f"$C = 2\\pi r = 2 \\cdot 3{{,}}14 \\cdot {rr} = {j}$ sm\nJavob: {j}", [f"{round(3.14 * rr * rr, 2):g}".replace(".", ","), f"{round(3.14 * rr, 2):g}".replace(".", ",")])
    if tur == "doira":
        rr = r(1, 15)
        j = f"{round(3.14 * rr * rr, 2):g}".replace(".", ",")
        return (f"Radiusi {rr} sm bo‘lgan doira yuzini toping (π ≈ 3,14).", j, f"$S = \\pi r^2 = 3{{,}}14 \\cdot {rr}^2 = {j}$ sm²\nJavob: {j}", [f"{round(2 * 3.14 * rr, 2):g}".replace(".", ","), f"{round(3.14 * rr * 2, 2):g}".replace(".", ",") + " "])
    if tur == "algebra":
        a, b, c = r(2, 9), r(2, 9), r(1, 20)
        return (f"Soddalashtiring: ${a}x + {b}x + {c}$. Natijadagi $x$ oldidagi son?", a + b, f"O‘xshash hadlarni qo‘shamiz: ${a}x + {b}x = {a + b}x$\nJavob: {a + b}", [a * b, a + b + c, c])
    if tur == "ifodaqiymat":
        a, b, x = r(2, 9), r(1, 20), r(1, 12)
        return (f"$x = {x}$ bo‘lganda ${a}x + {b}$ ning qiymati?", a * x + b, f"${a} \\cdot {x} + {b} = {a * x + b}$\nJavob: {a * x + b}", [a + x + b, a * (x + b), a * x])
    if tur == "ortacha_tezlik":
        v1, t1, v2, t2 = r(30, 80), r(1, 4), r(30, 80), r(1, 4)
        s = v1 * t1 + v2 * t2; t = t1 + t2
        while s % t:
            v2 += 1; s = v1 * t1 + v2 * t2
        return (f"Avtobus {t1} soat {v1} km/soat, keyin {t2} soat {v2} km/soat tezlik bilan yurdi. O‘rtacha tezligi?", s // t, f"Butun yo‘l: ${v1 * t1} + {v2 * t2} = {s}$ km; butun vaqt: ${t}$ soat; ${s} : {t} = {s // t}$\nJavob: {s // t}", [(v1 + v2) // 2 if (v1 + v2) // 2 != s // t else s // t + 2, s, v1])
    if tur == "diagramma":
        p = rng.choice([10, 20, 25, 30, 40, 50])
        return (f"Doiraviy diagrammada {p}% ga to‘g‘ri keladigan sektor necha gradus?", 360 * p // 100, f"Butun doira 360°: $360 \\cdot {p}/100 = {360 * p // 100}$\nJavob: {360 * p // 100}", [p, 180 * p // 100, 360 - p])
    if tur == "kubqirra":
        a = r(2, 10)
        return (f"Kubning hajmi {a ** 3} sm³. Qirrasi necha sm?", a, f"${a} \\cdot {a} \\cdot {a} = {a ** 3}$\nJavob: {a}", [a ** 3 // 3 if a ** 3 % 3 == 0 else a + 1, a * a, a + 2])
    if tur == "qolgan":
        x = r(4, 20) * 12
        return (f"{x} so‘mning 1/3 qismi sarflandi, qolganining 1/4 qismi ham sarflandi. Necha so‘m qoldi?", x - x // 3 - (x - x // 3) // 4, f"Avval: ${x} - {x // 3} = {x - x // 3}$; keyin: ${x - x // 3} - {(x - x // 3) // 4} = {x - x // 3 - (x - x // 3) // 4}$\nJavob: {x - x // 3 - (x - x // 3) // 4}", [x - x // 3 - x // 4, x // 3, x - x // 3])
    return gen34(tur, rng, kk)



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




# ── REV461: 1–2-sinf generatorlari (rasm-emoji bilan sanash, 10/20/100 ichida amallar, jadval, vaqt, pul, shakllar)
_NARSA = ["🍎", "🍐", "⭐", "🎈", "🐟", "🌸", "🍬", "⚽", "🐥", "🥕"]
_NOM = {"🍎": "olma", "🍐": "nok", "⭐": "yulduz", "🎈": "shar", "🐟": "baliq", "🌸": "gul", "🍬": "konfet", "⚽": "to‘p", "🐥": "jo‘ja", "🥕": "sabzi"}
_ISM = ["Ali", "Malika", "Bekzod", "Dilnoza", "Sardor", "Zarina"]


def gen12(tur, rng, kk=None):
    r = rng.randint
    if tur == "sanash":
        e = rng.choice(_NARSA); n = r(3, 10)
        return (f"Nechta {_NOM[e]} bor?  {e * n}", n, f"Bittalab sanaymiz: 1, 2, …, {n}.\nJavob: {n}", [n + 1, n - 1, n + 2])
    if tur == "qoshni":
        n = r(2, 19)
        if rng.random() < 0.5:
            return (f"{n} dan keyin qaysi son keladi?", n + 1, f"Keyingi son bittaga ko‘p: {n} + 1 = {n + 1}.\nJavob: {n + 1}", [n - 1, n + 2, n])
        return (f"{n} dan oldin qaysi son keladi?", n - 1, f"Oldingi son bittaga kam: {n} − 1 = {n - 1}.\nJavob: {n - 1}", [n + 1, n - 2, n])
    if tur == "taqqos12":
        a, b = r(1, 20), r(1, 20)
        j = ">" if a > b else "<" if a < b else "="
        return (f"{a} ⬜ {b} — qaysi belgi qo‘yiladi?", j, f"{a} {'katta' if a > b else 'kichik' if a < b else 'teng'} {b}.\nJavob: {j}", [x for x in (">", "<", "=") if x != j])
    if tur == "tarkib":
        n = r(4, 10); a = r(1, n - 1)
        return (f"{n} = {a} + ?", n - a, f"{n} ni {a} va {n - a} ga ajratamiz.\nJavob: {n - a}", [n - a + 1, n, max(0, n - a - 1)])
    if tur == "qosh10":
        a = r(1, 9); b = r(1, 10 - a)
        e = rng.choice(_NARSA)
        return (f"{e * a} + {e * b} = ?   ({a} + {b})", a + b, f"{a} ga {b} ni qo‘shamiz: {a + b}.\nJavob: {a + b}", [a + b + 1, abs(a - b), a + b - 1])
    if tur == "ayir10":
        a = r(3, 10); b = r(1, a - 1)
        return (f"{a} − {b} = ?", a - b, f"{a} dan {b} ni ayiramiz: {a - b}.\nJavob: {a - b}", [a + b, a - b + 1, a - b - 1 if a - b > 1 else a - b + 2])
    if tur == "qosh20":
        a = r(6, 9); b = r(11 - a, 9)
        return (f"{a} + {b} = ?", a + b, f"Avval 10 gacha to‘ldiramiz: {a} + {10 - a} = 10, keyin yana {b - (10 - a)}: {a + b}.\nJavob: {a + b}", [a + b - 10, a + b + 1, a + b - 1])
    if tur == "ayir20":
        a = r(11, 18); b = r(a - 9, 9)
        return (f"{a} − {b} = ?", a - b, f"Avval 10 gacha ayiramiz: {a} − {a - 10} = 10, keyin yana {b - (a - 10)}: {a - b}.\nJavob: {a - b}", [a - b + 1, a - b - 1, a + b])
    if tur == "masala12":
        i1, i2 = rng.sample(_ISM, 2); e = rng.choice(_NARSA); a, b = r(2, 9), r(1, 8)
        if rng.random() < 0.5:
            return (f"{i1}da {a} ta {_NOM[e]} bor edi, {i2} yana {b} ta berdi. Endi nechta?", a + b, f"Qo‘shamiz: {a} + {b} = {a + b}.\nJavob: {a + b}", [a - b if a > b else a + b + 1, a + b + 1, a])
        a = a + b
        return (f"{i1}da {a} ta {_NOM[e]} bor edi, {b} tasini {i2}ga berdi. Nechta qoldi?", a - b, f"Ayiramiz: {a} − {b} = {a - b}.\nJavob: {a - b}", [a + b, a - b + 1, b])
    if tur == "shakl12":
        s = rng.choice([("uchburchak", 3), ("to‘rtburchak", 4), ("kvadrat", 4), ("beshburchak", 5), ("oltiburchak", 6)])
        return (f"{s[0].capitalize()}ning nechta burchagi bor?", s[1], f"Burchaklarini sanaymiz: {s[1]} ta.\nJavob: {s[1]}", [s[1] + 1, s[1] - 1, 0 if s[1] > 3 else 2])
    if tur == "onlik":
        o, b = r(1, 9), r(0, 9)
        return (f"{o * 10 + b} sonida nechta o‘nlik bor?", o, f"{o * 10 + b} = {o} o‘nlik va {b} birlik.\nJavob: {o}", [b, o + 1, o * 10])
    if tur == "qosh100":
        a, b = r(10, 60), r(5, 39)
        return (f"{a} + {b} = ?", a + b, f"O‘nliklar: {a // 10 * 10} + {b // 10 * 10}, birliklar: {a % 10} + {b % 10}.\nJavob: {a + b}", [a + b + 10, a + b - 10, a + b + 1])
    if tur == "ayir100":
        a = r(30, 99); b = r(5, a - 10)
        return (f"{a} − {b} = ?", a - b, f"Birliklardan yetmasa, bitta o‘nlikni maydalaymiz.\nJavob: {a - b}", [a - b + 10, a - b - 10, a + b])
    if tur in ("jadval2", "jadval5", "jadval"):
        k = {"jadval2": rng.choice([2, 3]), "jadval5": rng.choice([4, 5]), "jadval": r(6, 9)}[tur]; m = r(2, 10)
        return (f"{k} · {m} = ?", k * m, f"{k} ni {m} marta qo‘shamiz: {k * m}.\nJavob: {k * m}", [k * m + k, k + m, k * m - k])
    if tur == "bolish12":
        k, m = r(2, 9), r(2, 9)
        return (f"{k * m} : {k} = ?", m, f"{k} · {m} = {k * m}, demak {k * m} : {k} = {m}.\nJavob: {m}", [k, m + 1, k * m - k])
    if tur == "vaqt12":
        s = r(1, 12); m = rng.choice([0, 30])
        return (f"Soat strelkasi {s} da, minut strelkasi {12 if m == 0 else 6} da. Soat necha?", f"{s}:{m:02d}", f"Minut strelkasi {'12 da — butun soat' if m == 0 else '6 da — yarim (30 minut)'}.\nJavob: {s}:{m:02d}", [f"{s % 12 + 1}:{m:02d}", f"{s}:{30 - m:02d}", f"{12 if m == 0 else 6}:{s:02d}"])
    if tur == "pul12":
        a, b = rng.choice([(500, 200), (1000, 500), (2000, 500), (1000, 200), (5000, 1000)])
        n = r(2, 4)
        return (f"Bitta daftar {b} so‘m. {n} ta daftar necha so‘m?", b * n, f"{b} · {n} = {b * n}.\nJavob: {b * n}", [b + n, b * n + b, b * (n - 1)])
    if tur == "uzunlik12":
        d = r(1, 9)
        return (f"{d} dm — necha sm?", d * 10, f"1 dm = 10 sm, {d} dm = {d * 10} sm.\nJavob: {d * 10}", [d, d * 100, d * 10 + 1])
    return gen12("qosh10", rng)
