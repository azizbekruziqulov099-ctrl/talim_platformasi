"""3–4-sinf matematika (yangi): darslik mundarijasi + modellar → Miya. Har mavzu turiga aniq misol generatori."""
import random, re
from fractions import Fraction
from m1 import M, D, toza, model_qatorlari, rows_test, NARSALAR, model_savol

ISM = ["Ali", "Malika", "Bekzod", "Dilnoza", "Sardor", "Gulnora", "Jasur", "Zarina"]


def fk(f):
    f = Fraction(f)
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def gen(tur, rng, kk=None):
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
    return gen(rng.choice(["qosh", "ayir", "kop1", "bol", "perimetr", "tenglama"]), rng)


TUR = [
    (("aralash kasr", "noto'g'ri kasr", "noto‘g‘ri kasr", "butun qism"), "N061", "OYIN: pitsa", "aralash"),
    (("kasrlarni qo", "birdan a", "butundan", "birlikdan o'tib"), "N061", "OYIN: pitsa", "kasrqosh"),
    (("natural songa ko",), "N062", "OYIN: pitsa", "kasrnat"),
    (("kasrlarni taqqos",), "N061", "OYIN: pitsa", "kasrtaq"),
    (("bo‘linish alom", "bo'linish alom"), "N058", None, "alomat"),
    (("bo‘luvchi", "bo'luvchi", "karrali"), "N044", "OYIN: massiv 3 4", "karrali"),
    (("qoldiq",), "N043", "OYIN: massiv 4 3", "qoldiq"),
    (("ikki xonali songa bu", "ikki xonali songa burchakli", "uch xonali songa burchakli", "ikki xonali songa bo"), "N058", None, "bol2"),
    (("burchakli bo", "yozma bo", "bo‘lish", "bo'lish", "bo‘lis", "bo'lis"), "N042", "OYIN: massiv 3 4", "bol"),
    (("10, 100", "10 ga va", "yaxlit sonlarni ko"), "N041", None, "kop10"),
    (("ikki xonali songa ko", "ikki xonali sonni ikki", "uch xonali songa ko", "ko'p xonali sonni ikki", "ko'p xonali sonni uch"), "N057", "OYIN: massiv 4 5", "kop2"),
    (("songa ko", "ko‘paytiris", "ko'paytiris", "nol bo'lgan sonlarni ko"), "N041", "OYIN: massiv 4 3", "kop1"),
    (("qo'shish va ayiri", "qo‘shish va ayiri"), "N056", None, "qosh"),
    (("ayiris", "a y iris"), "N039", "OYIN: nur 50 -18 60", "ayir"),
    (("qo'shish", "qo‘shish", "qo 'sh", "xona qo'shiluvchi"), "N038", None, "qosh"),
    (("taqqoslash",), "N037", "OYIN: juftla 6 4", "taqqos"),
    (("ko‘p xonali", "ko'p xonali", "pozitsion", "sinflar"), "N054", None, "korxona"),
    (("yaxlitlash", "taqribiy", "aniq va", "chamalash", "xatolig"), "N055", "OYIN: nur 40 7 50", "yaxlit"),
    (("o‘nli", "o'nli", "ulushlar ko"), "N045", None, "onli"),
    (("foiz",), "N046", None, "foiz"),
    (("qism ini", "qismini", "kattaliklarning qism", "ulush", "doiraning ulush"), "N046", "OYIN: pitsa", "ulush"),
    (("kasr",), "N045", "OYIN: pitsa", "kasrtaq"),
    (("quvlama", "kechikishli"), "N065", "OYIN: nur 0 6 20", "quvlama"),
    (("qarama-qarshi", "birgalikdagi harakat"), "N065", "OYIN: nur 0 6 20", "qarama"),
    (("harakat", "tezlik", "yo‘l, vaqt", "masofa"), "N064", "OYIN: nur 0 5 20", "harakat"),
    (("narx", "qiymat"), "N052", None, "qiymat"),
    (("unumdorlik", "unumdorlig"), "N066", None, "unum"),
    (("venn", "to'plam", "qismto'plam", "tegishlilik"), "N071", "OYIN: venn 15 12 5", "toplam"),
    (("o‘rta arifmetik", "chastota", "diagramma", "grafik", "ma’lumot"), "N053", None, "ortacha"),
    (("tenglama", "tengsizli", "tenglik"), "N060", "OYIN: tarozi 3 2 11", "tenglama"),
    (("ifoda", "formula", "amal hadlari"), "N059", "OYIN: tarozi 2 5 17", "ifoda"),
    (("koordinata", "sonli nur", "shkala", "nuqtadan", "nurning"), "N037", "OYIN: nur 3 5 12", "koordinata"),
    (("perimetr",), "N049", None, "perimetr"),
    (("yuz birlik", "yuz birliklarini"), "N067", None, "yuzbirlik"),
    (("yuz", "paletka", "kvadratning yu"), "N048", None, "yuz"),
    (("kilogramm", "tonna", "massa"), "N050", None, "massa"),
    (("uzunlik",), "N031", None, "uzunlik"),
    (("kub qirra", "qirralari"), "N068", None, "kub"),
    (("hajm", "kuboid", "parallelepiped"), "N069", None, "hajm"),
    (("prizma", "piramida", "silindr", "konus", "shar", "yoyilma", "kubning"), "N068", None, "jism"),
    (("burchak", "transportir", "gradus"), "N033", None, "burchak"),
    (("soat", "minut", "sekund", "vaqt"), "N051", None, "vaqt"),
    (("simmetriya", "simmetrik"), "N070", None, "jism"),
    (("doira", "aylana"), "N046", "OYIN: pitsa", "ulush"),
    (("parallel", "perpendikular", "kesmani teng"), "N070", None, "koordinata"),
]


def dars_yasa34(nom, rng):
    n = nom.lower()
    mid, oyin, tur = next(((m, o, t) for k, m, o, t in TUR if any(x in n for x in k)), ("N056", "OYIN: ramka 7 6", "aralash"))
    R = []
    kq, kj = model_savol(mid)
    R.append(("kirish", "", f"🎯 {nom}", f"Bugungi mavzu: {nom}. [1] {M[mid]['misol']}", M[mid]["misol"], "", "", "", "", "", "", f"{kq} => {kj}" if kq and kj else "", "", "", ""))
    R += model_qatorlari(mid, oyin, nom)
    kk = int(re.match(r"^(\d+)", nom).group(1)) if re.match(r"^\d+ ga bo", nom) else None
    q, j, y, xs = gen(tur, rng, kk)
    R.append(("misol", "N01", "Namunaviy misol", q, "", "", "", "", y, "", "", "", "", "o‘rta", ""))
    korilgan = {q}
    k, urinish = 0, 0
    while k < 8 and urinish < 300:   # cheklangan turdagi savollar kam bo'lsa — cheksiz aylanmasin
        urinish += 1
        q, j, y, xs = gen(tur, rng, kk)
        if q in korilgan:
            continue
        korilgan.add(q); k += 1
        R.append(("masala", f"M{k:02d}", f"Mashq {k}", q, "", "", "", str(j), y, "", "", "", "", "oson" if k <= 4 else "o‘rta", ""))
    for t in range(6):
        q, j, y, xs = gen(tur, rng, kk)
        R.append(rows_test(rng, q, j, xs, f"T{t + 1:02d}"))
    R.append(("xulosa", "", "🌟 Bugun nimani o‘rgandik", M[mid]["nazariya"], M[mid]["tushuncha"], "", "", "", "", "", "", "", "", "", ""))
    return R


def darslar34(sinf):
    out, sanoq = [], {}
    for x in [y for y in D["L"] if y["sinf"] == sinf]:
        nom = toza(x["nom"])
        nom = re.sub(r"^(I\s?I?\s?\.|\d{1,3})\s*(?=[A-ZА-ЯЎҚҒҲ‘'])", "", nom)
        nom = re.sub(r"\b([a-z‘'])\s(?=[a-z‘'] )", r"\1", nom)
        for a, b in (("alom ati", "alomati"), ("a y iris h", "ayirish"), ("qo 'sh ish", "qo‘shish"), ("q o'shish", "qo‘shish"), ("ko 'p a y tiri", "ko‘paytiri"), ("ta s v irla n", "tasvirlanishi"),
                     ("ay la ", "aylantirish"), ("qism ini", "qismini"), ("Yakuniy d ars", "Yakuniy dars"), ("Yakuniy d a r s", "Yakuniy dars"), ("O 'ndan", "O‘ndan"), ("M ingdan", "Mingdan"),
                     ("U zunlik", "Uzunlik"), ("b i", "bir"), ("..........", ""), (" ,?", ""), ("To‘g ‘ri", "To‘g‘ri"), ("butun qism ni", "butun qismini")):
            nom = nom.replace(a, b)
        for a, b in (("ay iris h", "ayirish"), ("aylantirishn tiris h", "aylantirish"), ("aylantirishn", "aylantirish"), ("ko‘paytiri ", "ko‘paytirish "), ("tasvirlanishi ", "tasvirlanishi"), ("ta sv irla n is h i", "tasvirlanishi"), ("qo ‘sh ish", "qo‘shish")):
            nom = nom.replace(a, b)
        nom = re.sub(r"\s+", " ", nom).strip(" .")
        if nom.lower().startswith("muqad"):
            continue
        sanoq[nom] = sanoq.get(nom, 0) + 1
        out.append((nom if sanoq[nom] == 1 else f"{nom} ({sanoq[nom]}-dars)", nom, x))
    return out
