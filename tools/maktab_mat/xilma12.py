"""REV513: 1–2-sinf matematika — har mavzuga ma'nosi bilan farq qiladigan misollar. Javoblar son (1-sinfda yozilmaydi —
dars xonasida tugmalardan tanlanadi), sanashda rasm (emoji) bilan."""
import random, re
from xilma5 import ISM

NARSA = ["🍎", "🍐", "⭐", "🐟", "🌷", "🚗", "🎈", "🐥", "🍓", "⚽"]
NOM = {"🍎": "olma", "🍐": "nok", "⭐": "yulduz", "🐟": "baliq", "🌷": "gul", "🚗": "mashina", "🎈": "shar", "🐥": "jo‘ja", "🍓": "qulupnay", "⚽": "to‘p"}


def o_son10(r):
    n = r.randint(2, 9); e = r.choice(NARSA); m = r.randint(1, n - 1); k = r.randint(2, 9)
    while k == n:
        k = r.randint(2, 9)
    return [
        lambda: (f"{e * n} — nechta {NOM[e]}?", n, "Har birini bosib sanaymiz.", [n - 1, n + 1]),
        lambda: (f"{n} dan keyin qaysi son keladi?", n + 1, "Sanoqda keyingi son 1 ta ko‘p.", [n - 1, n + 2]),
        lambda: (f"{n} dan oldin qaysi son keladi?", n - 1, "Oldingi son 1 ta kam.", [n + 1, n - 2]),
        lambda: (f"Qaysi biri ko‘p: {n} yoki {k}? (ko‘pini tanlang)", max(n, k), "Sanoqda keyinroq keladigani ko‘p.", [min(n, k)]),
        lambda: (f"{n} — bu {m} va yana nechta?", n - m, f"{m} + {n - m} = {n}", [n, m]),
        lambda: (f"{n} soni juftmi? (1 — ha, 0 — yo‘q)", int(n % 2 == 0), "Juft sonlar 2, 4, 6, 8 — ikkitadan juftlab bo‘linadi.", [int(n % 2 == 1)]),
        lambda: (f"{e * m} va {e * (n - m)} — hammasi nechta?", n, "Ikki guruhni birga sanaymiz.", [m, n - m]),
    ]


def o_qosh20(r):
    a, b = r.randint(2, 9), r.randint(2, 9); c = a + b; i = r.choice(ISM); e = r.choice(NARSA)
    return [
        lambda: (f"${a} + {b}$", c, f"{a} ga {b} ni qo‘shamiz: {'o‘nlikdan o‘tib — ' + str(a) + ' + ' + str(10 - a) + ' + ' + str(b - (10 - a)) if c > 10 else ''}{c}", [c - 1, c + 1]),
        lambda: (f"${c} - {b}$", a, f"{c} dan {b} ni olamiz.", [a + 1, c]),
        lambda: (f"$? + {b} = {c}$", a, "Noma’lum qo‘shiluvchi: yig‘indidan ma’lum qo‘shiluvchini ayiramiz.", [c, b]),
        lambda: (f"$? - {b} = {a}$", c, "Noma’lum kamayuvchi: ayirma + ayriluvchi.", [a, a - b if a > b else b]),
        lambda: (f"${c} - ? = {a}$", b, "Noma’lum ayriluvchi: kamayuvchi − ayirma.", [c, a]),
        lambda: (f"{i}da {a} ta {NOM[e]} bor edi, yana {b} ta berishdi. Nechta bo‘ldi?", c, f"{a} + {b} = {c}", [a, b]),
        lambda: (f"${a} + {b}$ va ${b} + {a}$ — natijalar tengmi? (1 — ha, 0 — yo‘q)", 1, "Qo‘shiluvchilar o‘rnini almashtirsak, yig‘indi o‘zgarmaydi.", [0]),
        lambda: (f"Savatda {c} ta {NOM[e]} bor edi, {b} tasi olindi. Nechta qoldi?", a, f"{c} − {b} = {a}", [c + b, b]),
    ]


def o_son100(r):
    n = r.randint(21, 99); a, b = r.randint(21, 69), r.randint(11, 29); t = r.randint(2, 9) * 10
    return [
        lambda: (f"{n} sonida nechta o‘nlik bor?", n // 10, f"{n} = {n // 10} o‘nlik va {n % 10} birlik", [n % 10, n]),
        lambda: (f"{n} sonida nechta birlik (birlar xonasida)?", n % 10, f"{n} = {n // 10 * 10} + {n % 10}", [n // 10]),
        lambda: (f"{n // 10} o‘nlik va {n % 10} birlik — qaysi son?", n, "O‘nliklar oldin, birliklar keyin yoziladi.", [int(f"{n % 10}{n // 10}") if n % 10 else n + 1, n // 10 + n % 10]),
        lambda: (f"Qaysi katta: {a} yoki {b + 40}? (kattasini tanlang)", max(a, b + 40), "Avval o‘nliklarni solishtiramiz.", [min(a, b + 40)]),
        lambda: (f"${a} + {b}$", a + b, f"O‘nliklar: {a // 10 * 10} + {b // 10 * 10}, birliklar: {a % 10} + {b % 10}", [a + b + 10, a + b - 10]),
        lambda: (f"${a + b} - {b}$", a, "O‘nliklardan o‘nliklarni, birliklardan birliklarni ayiramiz.", [a + 10, b]),
        lambda: (f"${t} + {100 - t}$", 100, "Yaxlit o‘nliklar: 10 ta o‘nlik = 100.", [90, 110]),
        lambda: (f"{n} ga eng yaqin yaxlit son (o‘nlik)?", round(n, -1), "Birliklar 5 va undan ko‘p bo‘lsa — yuqoridagi o‘nlik.", [n // 10 * 10 + (10 if round(n, -1) == n // 10 * 10 else 0)]),
    ]


def o_masala12(r):
    a, b = r.randint(5, 30), r.randint(2, 9); i1, i2 = r.sample(ISM, 2); e = r.choice(NARSA)
    return [
        lambda: (f"{i1}da {a} ta {NOM[e]}, {i2}da undan {b} ta ko‘p. {i2}da nechta?", a + b, f"«ko‘p» — qo‘shamiz: {a} + {b}", [a - b, a]),
        lambda: (f"{i1}da {a} ta {NOM[e]}, {i2}da undan {b} ta kam. {i2}da nechta?", a - b, f"«kam» — ayiramiz: {a} − {b}", [a + b]),
        lambda: (f"{i1}da {a} ta, {i2}da {a + b} ta {NOM[e]}. {i2}da nechta ko‘p?", b, f"Farqni topamiz: {a + b} − {a}", [2 * a + b, a]),
        lambda: (f"Bog‘da {a} ta olma daraxti va {b} ta nok daraxti bor. Hammasi nechta?", a + b, "Butunni topish — qo‘shamiz.", [a - b if a > b else a, a]),
        lambda: (f"Jami {a + b} ta shar, {a} tasi qizil, qolgani ko‘k. Ko‘klari nechta?", b, "Qismni topish — ayiramiz.", [a + b, a]),
        lambda: (f"Avtobusda {a} kishi bor edi. Bekatda {b} kishi tushdi, {b + 2} kishi chiqdi. Nechta kishi bo‘ldi?", a - b + b + 2, f"{a} − {b} + {b + 2}", [a - b, a + b]),
        lambda: (f"{i1} {a} ta konfet oldi, {b} tasini yedi. Yana nechta yesa, {a - b - 1} ta qoladi?", 1, f"Qoldi {a - b}; {a - b} − 1 = {a - b - 1}", [b, a - b]),
    ]


def o_ifoda12(r):
    a, b, c = r.randint(5, 30), r.randint(2, 9), r.randint(2, 9)
    return [
        lambda: (f"${a} + {b} - {c}$", a + b - c, "Chapdan o‘ngga bajaramiz.", [a - b + c, a + b + c]),
        lambda: (f"${a} - ({b} + {c})$", a - b - c, "Avval qavs ichidagi amal.", [a - b + c]),
        lambda: (f"Qaysi belgi: ${a} + {b} \\; ? \\; {a + b + 1}$ (1 — >, 2 — <, 3 — =)", 2, f"{a + b} < {a + b + 1}", [1, 3]),
        lambda: (f"$a = {b}$ bo‘lsa, $a + {a}$ ning qiymati?", a + b, "Harf o‘rniga sonni qo‘yamiz.", [a, b]),
        lambda: (f"$x + {b} = {a + b}$, $x$ = ?", a, "Tenglama: noma’lum qo‘shiluvchi.", [a + 2 * b, b]),
        lambda: (f"${a} + {b} + {10 - b % 10 if b % 10 else 10}$ ni qulay usulda hisoblang.", a + b + (10 - b % 10 if b % 10 else 10), f"Avval {b} + {10 - b % 10 if b % 10 else 10} = yaxlit o‘nlik", [a + 10]),
        lambda: (f"Ikkala ifoda tengmi: ${a} + {b}$ va ${a + 1} + {b - 1}$? (1 — ha, 0 — yo‘q)", 1, "Biriga 1 qo‘shib, ikkinchisidan 1 olsak — yig‘indi o‘zgarmaydi.", [0]),
    ]


def o_shakl12(r):
    a, b, c = r.randint(2, 9), r.randint(2, 9), r.randint(2, 9); n = r.choice([3, 4, 5, 6])
    return [
        lambda: (f"Siniq chiziq bo‘g‘inlari {a} sm, {b} sm va {c} sm. Uzunligi?", a + b + c, "Bo‘g‘inlar uzunliklarini qo‘shamiz.", [a + b, a * b]),
        lambda: (f"{n} burchakli shaklning nechta tomoni bor?", n, "Burchaklar soni = tomonlar soni.", [n + 1, n - 1]),
        lambda: (f"Kvadrat tomoni {a} sm. Perimetri?", 4 * a, f"{a} + {a} + {a} + {a}", [2 * a, a * a]),
        lambda: (f"Uchburchak tomonlari {a}, {b}, {c} sm. Perimetri?", a + b + c, "Tomonlar yig‘indisi.", [a + b]),
        lambda: ("To‘g‘ri to‘rtburchakning nechta to‘g‘ri burchagi bor?", 4, "Hamma burchaklari to‘g‘ri.", [2, 3]),
        lambda: (f"Kesma {a + b} sm, undan {a} sm kesildi. Qancha qoldi?", b, f"{a + b} − {a}", [a + 2 * b]),
        lambda: ("Kvadratning nechta simmetriya o‘qi bor?", 4, "Ikki diagonal va ikki o‘rta chiziq.", [2, 1]),
    ]


def o_olchov12(r):
    dm, sm, s, m = r.randint(1, 9), r.randint(1, 9), r.randint(1, 5), r.choice([15, 20, 30, 40, 45])
    return [
        lambda: (f"{dm} dm {sm} sm — necha sm?", dm * 10 + sm, "1 dm = 10 sm", [dm + sm, dm * 100 + sm]),
        lambda: (f"{dm * 10} sm — necha dm?", dm, "10 sm = 1 dm", [dm * 10, dm * 100]),
        lambda: (f"{s} m — necha dm?", s * 10, "1 m = 10 dm", [s * 100, s]),
        lambda: (f"Soat {s} da boshlangan multfilm {m} minut davom etdi. Necha minutdan keyin soat {s + 1} bo‘ladi?", 60 - m, "1 soat = 60 minut.", [m, 60]),
        lambda: (f"Non {dm * 500} so‘m, sut {sm * 1000} so‘m. Hammasi necha so‘m?", dm * 500 + sm * 1000, "Narxlarni qo‘shamiz.", [dm * 500, sm * 1000]),
        lambda: (f"{s} kg olma va {dm} kg nok — jami necha kg?", s + dm, "Massalarni qo‘shamiz.", [abs(s - dm)]),
        lambda: (f"1 soat necha minut?", 60, "Soat millari bir aylanadi — 60 minut.", [100, 30]),
    ]


def o_kopjadval(r):
    a, b = r.randint(2, 9), r.randint(2, 9); e = r.choice(NARSA)
    return [
        lambda: (f"${a} \\cdot {b}$", a * b, f"{a} ni {b} marta qo‘shamiz.", [a + b, a * b + a]),
        lambda: (f"${a * b} : {a}$", b, f"{a} · {b} = {a * b} — bo‘lish ko‘paytirishga teskari.", [a, a * b - a]),
        lambda: (f"{b} ta likopchada {a} tadan {NOM[e]}. Hammasi nechta?", a * b, f"{a} · {b}", [a + b]),
        lambda: (f"{a * b} ta {NOM[e]}ni {a} ta bolaga teng bo‘lishdi. Har biriga nechta?", b, f"{a * b} : {a}", [a * b - a, a]),
        lambda: (f"{b} ni {a} marta orttiring.", a * b, "Marta orttirish — ko‘paytiramiz.", [a + b]),
        lambda: (f"{a * b} ni {b} marta kamaytiring.", a, "Marta kamaytirish — bo‘lamiz.", [a * b - b]),
        lambda: (f"$? \\cdot {a} = {a * b}$", b, "Noma’lum ko‘paytuvchi = ko‘paytma : ma’lum ko‘paytuvchi.", [a * b, a]),
        lambda: (f"${a} \\cdot 0 + {b} \\cdot 1$", b, "Nolga ko‘paytirilsa — 0; 1 ga — son o‘zi.", [a + b, 0]),
    ]


def o_uchxonali(r):
    n = r.randint(101, 989); a, b = r.randint(120, 480), r.randint(110, 450)
    return [
        lambda: (f"{n} sonida nechta yuzlik?", n // 100, f"{n} = {n // 100} yuzlik, {(n // 10) % 10} o‘nlik, {n % 10} birlik", [(n // 10) % 10, n % 10]),
        lambda: (f"{n // 100} yuzlik {(n // 10) % 10} o‘nlik {n % 10} birlik — qaysi son?", n, "Xonalar tartibi: yuzlar, o‘nlar, birlar.", [int(str(n)[::-1]) if n % 10 else n + 1]),
        lambda: (f"${a} + {b}$", a + b, "Ustun ko‘rinishida: birlar ostida birlar.", [a + b + 100, a + b - 10]),
        lambda: (f"${a + b} - {b}$", a, "Ustun ko‘rinishida ayiramiz.", [a + 100, b]),
        lambda: (f"Qaysi katta: {a} yoki {b}? (kattasini tanlang)", max(a, b), "Avval yuzliklar solishtiriladi.", [min(a, b)]),
        lambda: (f"Kutubxonada {a} ta ertak va {b} ta she’r kitobi bor. Jami nechta?", a + b, "Qo‘shamiz.", [abs(a - b)]),
        lambda: ("1000 da nechta yuzlik bor?", 10, "10 ta yuzlik = 1000 (ming).", [100, 1]),
    ]


def o_yuz12(r):
    a, b = r.randint(2, 8), r.randint(2, 8)
    return [
        lambda: (f"To‘g‘ri to‘rtburchak {a} katak bo‘yi va {b} katak eni. Nechta katakdan iborat?", a * b, f"{a} · {b} — qatorlar × kataklar.", [a + b, 2 * (a + b)]),
        lambda: (f"Kvadrat tomoni {a} sm. Yuzi necha sm²?", a * a, f"{a} · {a}", [4 * a]),
        lambda: (f"Yuzi {a * b} sm², bo‘yi {a} sm. Eni?", b, f"{a * b} : {a}", [a * b - a]),
        lambda: ("1 dm² necha sm²?", 100, "10 sm · 10 sm", [10, 1000]),
    ]


def o_mantiq12(r):
    n = r.randint(1, 12); rim = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"][n - 1]; s = r.randint(2, 5)
    return [
        lambda: (f"Rim raqamida «{rim}» — qaysi son?", n, "I = 1, V = 5, X = 10; kichigi oldin bo‘lsa — ayiriladi.", [n + 1, n - 1 if n > 1 else 2]),
        lambda: (f"Davom ettiring: {s}, {2 * s}, {3 * s}, …", 4 * s, f"Har safar {s} ta qo‘shiladi.", [3 * s + 1, 5 * s]),
        lambda: ("3 ta qushdan 2 tasi uchib ketdi. Nechta qush qoldi?", 1, "3 − 2", [2, 5]),
        lambda: ("Dushanbadan keyin qaysi kun? (1 — Seshanba, 2 — Yakshanba, 3 — Chorshanba)", 1, "Hafta kunlari tartibi.", [2, 3]),
        lambda: (f"Xonada {s} ta stul bor, har birining 4 ta oyog‘i bor. Jami nechta oyoq?", 4 * s, f"4 · {s}", [4 + s]),
    ]


def aralash(r):
    return [t for f in (o_qosh20, o_son100, o_masala12, o_ifoda12, o_shakl12, o_olchov12) for t in f(r)[:2]]


def oila_tanla(nom):
    if nom == "__aralash__":
        return aralash
    n = re.sub(r"\s*\(\d+-dars\)", "", str(nom).lower()).strip()
    if re.fullmatch(r"takrorlash|yakuniy dars|mavzu bo.yicha yakuniy dars|masalalar yechish( va o.tilgan mavzularni mustahkamlash)?|amaliy topshiriqlar|misol va masalalar yechish", n):
        return None
    for pat, f in [
        (r"rim|mantiq|nostandart|ketma-ketlik|o.xshashlik", o_mantiq12), (r"yuz", o_yuz12),
        (r"ko.paytir|bo.lish|bo.luvchi|marta|jadvali|komponent|taqsimot|nolning", o_kopjadval),
        (r"uch xonali|ming|yuzlik", o_uchxonali), (r"santimetr|detsimetr|metr|kilometr|massa|hajm|soat|minut|vaqt|kattalik|uzunlik", o_olchov12),
        (r"shakl|kesma|chiziq|burchak|perimetr|kvadrat|to.rtburchak|simmetr|ko.pburchak|nuqta|soha|aylana|doira|nur|tekislik|sirt", o_shakl12),
        (r"masala|orttirish|kamaytirish|butunni|qism", o_masala12), (r"ifoda|qavs|tengsizlik|tenglik|tenglama|harfiy|amallarning|amal", o_ifoda12),
        (r"21 dan 100|ikki xonali|yaxlit|o.qilishi|50 - 22|43|33|30 - 7|21 \+|25 \+|28 \+|6 \+|31 \+|ustun|og.zaki|sondan|yig.indi", o_son100),
        (r"qo.shish|ayirish|o.nlikdan|noma.lum|hadlari|ko.p komponent", o_qosh20),
        (r"son|raqam|sanog|guruh|narsa|juft|toq|taqqos", o_son10)]:
        if re.search(pat, n):
            return f
    return None
