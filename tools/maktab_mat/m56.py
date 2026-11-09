"""5–6-sinf matematika (yangi). Darslikdagi KATTA HARFLI qatorlar — bob sarlavhasi (dars emas).
«Eslang», «Matnli masalalar», «O'ylab ko'ring» darslari o'z bobining mavzusi bo'yicha tuziladi."""
import random, re
from fractions import Fraction
from m1 import M, D, toza, model_qatorlari, rows_test, model_savol
from m34 import gen as gen34, fk


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


TUR56 = [
    (("eslang", "muammoli", "o‘ylab", "oʻylab", "matnli masala", "takrorlash"), None, None, None),   # bob bo'yicha
    (("qolgan qismning",), "N080", "OYIN: pitsa", "qolgan"),
    (("kasrni natural songa bo",), "N094", "OYIN: pitsa", "kasr_n_bol"),
    (("natural sonni to‘g‘ri kasrga",), "N094", "OYIN: pitsa", "n_kasr_bol"),
    (("kasrni to‘g‘ri kasrga bo", "kasrga bo"), "N094", "OYIN: pitsa", "kasrbol"),
    (("to‘g‘ri kasrni natural songa ko", "noto‘g‘ri kasrni natural songa ko"), "N093", "OYIN: pitsa", "kasr_n_kop"),
    (("kasrni natural songa ko", "kasrlarni ko", "kasrni ko‘pa", "noto‘g‘ri kasrni", "aralash sonlarni natural"), "N093", "OYIN: pitsa", "kasrkop"),
    (("aralash sonlarni qo",), "N092", "OYIN: pitsa", "kasrqosh2"),
    (("kasr ko‘rinishi", "o‘nli kasrga aylantir", "oddiy kasr, o‘nli kasr va foiz"), "N082", "OYIN: pitsa", "onli"),
    (("o‘nli kasrni 10", "o‘nli kasrni o‘nlik", "o‘nli kasrni o‘nliklar"), "N085", None, "onli10"),
    (("o‘lchov birlik",), "N085", None, "massa"),
    (("10, 100 va 1000 ga ko", "o‘nlik, yuzlik va minglik", "10, 100 va 1000 ga bo"), "N085", None, "kop10"),
    (("qavssiz", "qavsli"), "N075", "OYIN: tarozi 2 5 17", "ifoda"),
    (("milliongacha",), "N072", "OYIN: nur 0 100 1000", "korxona"),
    (("asosi va balandligi", "uchburchakning yuzi", "murakkab shakllarning yuz"), "N089", None, "uchburchak_yuz"),
    (("hajm", "kuboid", "fazoviy jism", "panjara", "suyuqlik"), "N089", None, "hajm"),
    (("kubning qirrasini", "kuboidning qirrasini", "bir yog"), "N089", None, "kubqirra"),
    (("uch miqdor", "uchta miqdor"), "N097", None, "nisbat"),
    (("nisbat",), "N097", None, "nisbat"),
    (("me’yor", "birliklar soni", "umumiy miqdor"), "N098", None, "meyor"),
    (("qqs", "chegirma"), "N099", None, "chegirma"),
    (("o‘sish foizi", "oʻsish foizi", "kamayish foizi"), "N099", None, "osish"),
    (("foiz",), "N086", None, "foiz"),
    (("o‘rtacha tezlik",), "N064", "OYIN: nur 0 5 20", "ortacha_tezlik"),
    (("tezlik", "harakat"), "N064", "OYIN: nur 0 5 20", "harakat"),
    (("o‘rtacha qiymat", "o‘rtacha va jami"), "N087", None, "ortacha"),
    (("doiraviy diagramma",), "N107", "OYIN: pitsa", "diagramma"),
    (("vertikal", "to‘g‘ri chiziqdagi burchak"), "N088", None, "burchak_chiziq"),
    (("nuqta atrofidagi", "noma’lum burchak", "nomaʼlum bu"), "N088", None, "burchak_nuqta"),
    (("uchburchakning burchak", "uchburchakning tur", "uchburchaklarni chizish"), "N088", None, "uchburchak_burchak"),
    (("to‘rtburchak", "trapetsiya", "parallelogramm", "romb"), "N089", None, "tortburchak_burchak"),
    (("aylananing uzunligi", "doira va aylana el", "yarim va chorak doira perimetri"), "N106", "OYIN: nuqta", "aylana"),
    (("doiraning yuzi", "yarim va chorak doira yuzi", "murakkab shakllarning yuzi va peri"), "N106", "OYIN: nuqta", "doira"),
    (("konus", "silindr", "prizma", "piramida", "yoyilma"), "N089", None, "jism"),
    (("algebraik ifodalarni soddalash", "algebraik ifodalar"), "N075", "OYIN: tarozi 2 5 17", "algebra"),
    (("qiymatini t",), "N075", None, "ifodaqiymat"),
    (("tenglama",), "N075", "OYIN: tarozi 3 2 11", "tenglama"),
]
BOB_TUR = {"natural": ("N072", None, "korxona"), "to‘rt amal": ("N074", None, "kop1"), "oddiy kasr": ("N079", "OYIN: pitsa", "kasrkop"),
           "uchburchakning yuzi": ("N089", None, "uchburchak_yuz"), "hajm": ("N089", None, "hajm"), "nisbat": ("N097", None, "nisbat"),
           "o‘nli kasr": ("N082", None, "onli10"), "me’yor": ("N098", None, "meyor"), "foiz": ("N086", None, "foiz"), "o‘rtacha": ("N087", None, "ortacha"),
           "burchak": ("N088", None, "burchak_chiziq"), "uchburchakning xossa": ("N088", None, "uchburchak_burchak"), "trapetsiya": ("N089", None, "tortburchak_burchak"),
           "algebra": ("N075", "OYIN: tarozi 3 2 11", "tenglama"), "doira": ("N106", "OYIN: nuqta", "doira"), "tezlik": ("N064", None, "harakat"),
           "diagramma": ("N107", None, "diagramma"), "yoyilma": ("N089", None, "jism"), "takrorlash": ("N074", None, "aralash")}


def tanla(nom, bob):
    n = nom.lower().replace("ʻ", "‘").replace("'", "‘")
    for k, mid, o, t in TUR56:
        if any(x.replace("ʻ", "‘") in n for x in k):
            if mid is None:
                break
            return mid, o, t
    b = (bob or "").lower().replace("ʻ", "‘")
    for k, v in BOB_TUR.items():
        if k in b:
            return v
    return ("N074", None, "aralash")


def dars_yasa56(nom, bob, rng):
    mid, oyin, tur = tanla(nom, bob)
    R = []
    kq, kj = model_savol(mid)
    sarl = nom if not any(x in nom.lower() for x in ("eslang", "o‘ylab", "oʻylab")) else f"{nom} — {bob.lower().capitalize()}"
    R.append(("kirish", "", f"🎯 {sarl}", f"Bugungi mavzu: {sarl}. [1] {M[mid]['misol']}", M[mid]["misol"], "", "", "", "", "", "", f"{kq} => {kj}" if kq and kj else "", "", "", ""))
    R += model_qatorlari(mid, oyin, sarl)
    q, j, y, xs = gen56(tur, rng)
    R.append(("misol", "N01", "Namunaviy misol", q, "", "", "", "", y, "", "", "", "", "o‘rta", ""))
    korilgan, k, u = {q}, 0, 0
    while k < 8 and u < 300:
        u += 1
        q, j, y, xs = gen56(tur, rng)
        if q in korilgan:
            continue
        korilgan.add(q); k += 1
        R.append(("masala", f"M{k:02d}", f"Mashq {k}", q, "", "", "", str(j), y, "", "", "", "", "oson" if k <= 4 else "o‘rta", ""))
    for t in range(6):
        q, j, y, xs = gen56(tur, rng)
        R.append(rows_test(rng, q, j, xs, f"T{t + 1:02d}"))
    R.append(("xulosa", "", "🌟 Bugun nimani o‘rgandik", M[mid]["nazariya"], M[mid]["tushuncha"], "", "", "", "", "", "", "", "", "", ""))
    return R


def darslar56(sinf):
    out, sanoq, bob = [], {}, ""
    for x in [y for y in D["L"] if y["sinf"] == sinf]:
        nom = re.sub(r"\s+", " ", str(x["nom"])).strip()
        sof = re.sub(r"^[IVX\d]+\s+", "", nom)
        harflar = [c for c in sof if c.isalpha()]
        if harflar and sum(c.isupper() for c in harflar) / len(harflar) > 0.8 and "TAKRORLASH" not in sof:
            bob = sof
            continue
        if "TAKRORLASH" in sof:
            nom = sof.capitalize()
        nom = toza(nom).replace("Oʻylab koʻring. Muammoli topshiriq", "O‘ylab ko‘ring. Muammoli topshiriq")
        kalit = f"{nom} — {bob.lower().capitalize()}" if nom.lower().startswith(("eslang", "o‘ylab", "oʻylab", "matnli")) else nom
        sanoq[kalit] = sanoq.get(kalit, 0) + 1
        out.append((kalit if sanoq[kalit] == 1 else f"{kalit} ({sanoq[kalit]}-dars)", nom, bob, x))
    return out
