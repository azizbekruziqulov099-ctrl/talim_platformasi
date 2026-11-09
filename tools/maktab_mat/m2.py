"""2-sinf matematika (yangi) — darslik mundarijasi (164 dars) + 2-sinf modellari → Kabutar Miya.
Darsdagi namuna (masalan «31 + 9», «43 − 16») bo'yicha AYNAN shu turdagi misollar yaratiladi; ko'paytirish jadvali
har son uchun alohida (massiv o'yini bilan), bo'lish — teskari amal sifatida."""
import random, re
from m1 import M, D, toza, model_qatorlari, rows_test, NARSALAR, masala_qatorlari, model_savol

ISMLAR = ["Ali", "Malika", "Bekzod", "Dilnoza", "Sardor", "Gulnora", "Jasur", "Zarina"]


def turkum_qosh(a, b):
    s = a % 10 + b % 10
    return "yaxlit" if s % 10 == 0 else "otish" if s > 10 else "oddiy"


def turkum_ayir(a, b):
    return "yaxlitdan" if a % 10 == 0 else "otish" if a % 10 < b % 10 else "oddiy"


def namuna_misollar(rng, a0, op, b0, n=8):
    """«31 + 9» turidagi misollar: xona soni va «o'nlikdan o'tish/yaxlit» xususiyati saqlanadi."""
    out, sinov = [], 0
    tur = turkum_qosh(a0, b0) if op == "+" else turkum_ayir(a0, b0)
    while len(out) < n and sinov < 5000:
        sinov += 1
        a = rng.randint(10 ** (len(str(a0)) - 1), 10 ** len(str(a0)) - 1)
        b = rng.randint(10 ** (len(str(b0)) - 1) if b0 >= 10 else 1, 10 ** len(str(b0)) - 1)
        if a0 % 10 == 0:
            a -= a % 10
        if op == "+":
            if a + b > 100 or turkum_qosh(a, b) != tur:
                continue
            q, j = f"${a} + {b} = \\;?$", a + b
            yech = f"Birliklar: ${a % 10} + {b % 10} = {a % 10 + b % 10}$" + (", 10 tasi — yangi o‘nlik" if a % 10 + b % 10 >= 10 else "") + f".\nJavob: {j}"
        else:
            if b >= a or turkum_ayir(a, b) != tur:
                continue
            q, j = f"${a} - {b} = \\;?$", a - b
            yech = (f"Birliklardan ${a % 10}$ dan ${b % 10}$ ayirib bo‘lmaydi — bitta o‘nlikni 10 birlikka maydalaymiz.\n" if a % 10 < b % 10 else "") + f"${a} - {b} = {j}$\nJavob: {j}"
        if (q, j) not in [(x[0], x[1]) for x in out]:
            out.append((q, j, yech))
    return out


def jadval_qatorlari(rng, k, bolish=False):
    R = []
    for i, m in enumerate(rng.sample(range(1, 11), 8)):
        if bolish:
            R.append(("masala", f"M{i + 1:02d}", f"Bo‘lish {i + 1}", f"${k * m} : {k} = \\;?$", "", "", "", str(m),
                      f"${k} \\cdot {m} = {k * m}$, demak ${k * m} : {k} = {m}$\nJavob: {m}", "", "", "", "", "oson" if i < 4 else "o‘rta", f"{k} ni nechaga ko‘paytirsak {k * m} chiqadi?"))
        else:
            R.append(("masala", f"M{i + 1:02d}", f"Ko‘paytirish {i + 1}", f"${k} \\cdot {m} = \\;?$", "", "", "", str(k * m),
                      f"${' + '.join([str(k)] * m) if m <= 6 else f'{k} \\cdot {m}'} = {k * m}$\nJavob: {k * m}", "", "", "", "", "oson" if i < 4 else "o‘rta", f"{k} ni {m} marta qo‘shib ko‘r."))
    return R


def dars_yasa2(nom, rng):
    n = nom.lower()
    R = []
    m_pat = re.search(r"\((\d+)\s*([+\-−])\s*(\d+)\s*\)", nom)
    m_jad = re.match(r"^(\d)\s*sonini", nom) or re.match(r"^(\d)\s*soniga", nom)
    m_bol = re.search(r"sonni\s*(\d)\s*ga\s*bo", n)
    if m_pat:
        a0, op, b0 = int(m_pat.group(1)), "+" if m_pat.group(2) == "+" else "-", int(m_pat.group(3))
        mid = "N020" if op == "+" else "N021"
        R.append(("kirish", "", f"🎯 {nom}", f"Bugun {a0} {'+' if op == '+' else '−'} {b0} kabi misollarni o‘rganamiz. [1] Avval o‘ylab ko‘ring: birliklar bilan nima bo‘ladi?",
                  f"${a0} {'+' if op == '+' else '-'} {b0}$", "", "", "", "", "", "", f"${a0} {'+' if op == '+' else '-'} {b0} = ?$ => {a0 + b0 if op == '+' else a0 - b0} | {a0 + b0 + 10 if op == '+' else a0 - b0 + 10} | {a0 + b0 - 10 if op == '+' else a0 - b0 - 1}", "", "", ""))
        R += model_qatorlari(mid, f"OYIN: nur {a0} {b0 if op == '+' else -b0} {max(a0 + b0, a0) + 2 if op == '+' else a0 + 2}", nom)
        if turkum_qosh(a0, b0) == "otish" and op == "+" and b0 < 10:
            R.append(("tushuncha", "", "🔟 O‘nlikni to‘ldiramiz", "Avval yaxlit o‘nlikkacha to‘ldiramiz, keyin qolganini qo‘shamiz. [1] O‘zing sinab ko‘r.", f"OYIN: ramka {a0 % 10} {b0}", "", "", "", "", "", "", "", "", "", ""))
        for k, (q, j, y) in enumerate(namuna_misollar(rng, a0, op, b0, 8)):
            R.append(("masala", f"M{k + 1:02d}", f"Misol {k + 1}", q, "", "", "", str(j), y, "", "", "", "", "oson" if k < 4 else "o‘rta", "Avval birliklarni, keyin o‘nliklarni hisobla."))
        for k, (q, j, y) in enumerate(namuna_misollar(rng, a0, op, b0, 6)):
            R.append(rows_test(rng, q, j, [j + 10, j - 10 if j > 10 else j + 1, j + 1], f"T{k + 1:02d}"))
        return R
    if m_jad or m_bol:
        k = int((m_jad or m_bol).group(1))
        bolish = bool(m_bol)
        mid = "N026" if bolish else ("N024" if k > 2 else "N023")
        R.append(("kirish", "", f"🎯 {nom}", f"{'Bo‘lish — teng bo‘lish.' if bolish else 'Ko‘paytirish — bir xil sonlarni qo‘shishning qisqa yozuvi.'} [1] Bugun {k} {'ga bo‘lishni' if bolish else 'ning karralarini'} o‘rganamiz.",
                  f"${' + '.join([str(k)] * 3)} = {k} \\cdot 3$" if not bolish else f"${k * 4} : {k} = 4$", "", "", "", "", "", "",
                  f"${k} \\cdot 3 = ?$ => {k * 3} | {k + 3} | {k * 3 + k}" if not bolish else f"${k * 4} : {k} = ?$ => 4 | {k * 4 - k} | {k}", "", "", ""))
        R += model_qatorlari(mid, f"OYIN: massiv {min(k, 6) if not bolish else 4} {k if not bolish else min(k, 6)}", nom)
        jad = " ; ".join(f"{k}·{i}={k * i}" for i in range(1, 11)) if not bolish else " ; ".join(f"{k * i}:{k}={i}" for i in range(1, 11))
        R.append(("tushuncha", "", "Jadval", f"{'Ko‘paytirish' if not bolish else 'Bo‘lish'} jadvalini birga aytamiz. [1] Har qator oldingisidan {k} taga {'ko‘p' if not bolish else 'farq qiladi'}.",
                  jad.replace(" ; ", "\n")[:400], "", "", "", "", "", "", f"${k} \\cdot 7 = ?$ => {k * 7} | {k * 7 + k} | {k * 6}" if not bolish else f"${k * 7} : {k} = ?$ => 7 | 6 | {k}", "", "", ""))
        R += jadval_qatorlari(rng, k, bolish)
        for i, m in enumerate(rng.sample(range(2, 11), 6)):
            R.append(rows_test(rng, f"${k * m} : {k} = ?$" if bolish else f"${k} \\cdot {m} = ?$", m if bolish else k * m, [m + 1, m - 1, k] if bolish else [k * m + k, k * m - k, k + m], f"T{i + 1:02d}"))
        return R
    # qolganlari — mavzu bo'yicha
    TUR = [
        (("uch xonali", "yuzlik"), "N019", "OYIN: nur 100 50 200", "uchxona"),
        (("metr", "detsimetr", "millimet", "kilometr"), "N031", "OYIN: nur 0 10 20", "olchov"),
        (("soat", "minut"), "N035", None, "vaqt"),
        (("siniq chiziq", "perimetr"), "N032", None, "perimetr"),
        (("yuz", "katak"), "N033", None, "yuz"),
        (("burchak", "to‘g‘ri to‘rtburchak", "kvadrat", "chiziq, nur", "yassi", "aylana", "doira", "hajm", "shakl"), "N033", None, "shakl"),
        (("amallar", "ikki amalli ifoda", "tartib"), "N029", "OYIN: tarozi 2 3 11", "tartib"),
        (("tenglama", "teskari"), "N030", "OYIN: tarozi 3 2 11", "tenglama"),
        (("nol", "1 ga"), "N028", "OYIN: massiv 3 1", "nolbir"),
        (("bo‘lish bilan ko‘paytirish", "bog‘", "bo‘luvchi", "karrali"), "N027", "OYIN: massiv 3 4", "bogliq"),
        (("ko‘paytirish xossa", "o‘rin almashtirish", "taqsimot", "yig‘indini songa"), "N025", "OYIN: massiv 4 3", "xossa"),
        (("10 ga va 100 ga", "ming", "yaxlit sonlarni ko‘paytirish", "yaxlit sonlarni bo‘lish", "ikki xonali sonni ko‘paytirish", "ko‘p xonali", "bir xonali"), "N024", "OYIN: massiv 4 5", "yaxlitkop"),
        (("ko‘paytirish tushunchasi", "ko‘paytirish komponent", "ko‘paytirish jadvali"), "N023", "OYIN: massiv 4 3", "kopaytma"),
        (("bo‘lish",), "N026", "OYIN: massiv 3 4", "bolish"),
        (("orttirish", "kamaytirish"), "N036", "OYIN: massiv 3 4", "marta"),
        (("juft va toq",), "N024", "OYIN: juftla 6 6", "juft"),
        (("yig‘indidan", "yig‘indini ayirish", "og‘zaki"), "N022", "OYIN: nur 30 -12 40", "yigindi"),
        (("ustun",), "N020", None, "ustun"),
        (("masala", "mantiqiy", "amaliy"), "N036", None, "masala"),
        (("qo‘shish",), "N020", "OYIN: nur 30 8 40", "qosh"),
        (("ayirish",), "N021", "OYIN: nur 40 -8 50", "ayir"),
    ]
    mid, oyin, tur = next(((mid, o, t) for k, mid, o, t in TUR if any(x in n for x in k)), ("N036", "OYIN: ramka 7 6", "aralash"))
    kq, kj = model_savol(mid)
    if "taqsimot" in n or "yig‘indini songa" in n:
        R.append(("kirish", "", f"🎯 {nom}", "Ikki savatda olma bor: birida 3 qator, ikkinchisida 2 qator, har qatorda 4 tadan. [1] Jami nechta? Ikki xil hisoblab ko‘ramiz.",
                  "$(3 + 2) \\cdot 4 = ?$", "", "", "", "", "", "", "$(3 + 2) \\cdot 4 = ?$ => 20 | 14 | 11", "", "", ""))
        R += [("tushuncha", "", "Taqsimot xossasi", "Birinchi usul: avval qatorlarni qo‘shamiz, 3 va 2 — 5 qator, keyin 4 ga ko‘paytiramiz — 20. [1] Ikkinchi usul: har savatni alohida hisoblab qo‘shamiz — 12 va 8, jami 20. [2] Javob bir xil: yig‘indini songa ko‘paytirish uchun har qo‘shiluvchini ko‘paytirib, natijalarni qo‘shsa bo‘ladi.",
                "$(3 + 2) \\cdot 4 = 5 \\cdot 4 = 20$\n$3 \\cdot 4 + 2 \\cdot 4 = 12 + 8 = 20$\nQOIDA: $(a + b) \\cdot c = a \\cdot c + b \\cdot c$", "", "", "", "", "", "", "$(5 + 2) \\cdot 3 = 5 \\cdot 3 + ? \\cdot 3$ => 2 | 5 | 3", "", "", ""),
              ("tushuncha", "", "🎮 O‘zing bajar", "Qatorlarni chiqar va sana. [1] 3 qator va 2 qator — jami 5 qator, har birida 4 tadan.", "OYIN: massiv 5 4", "", "", "", "", "", "", "", "", "", "")]
    else:
        R.append(("kirish", "", f"🎯 {nom}", f"Bugungi mavzu: {nom}. [1] {M[mid]['misol']}", M[mid]["misol"], "", "", "", "", "", "", f"{kq} => {kj}" if kq and kj else "", "", "", ""))
        R += model_qatorlari(mid, oyin, nom)
    mashq, testlar = [], []
    for i in range(8):
        if tur == "uchxona":
            a = rng.randint(100, 999); y, o_, b_ = a // 100, a // 10 % 10, a % 10
            mashq.append((f"{a} sonida nechta yuzlik, nechta o‘nlik va nechta birlik bor? (yuzliklar sonini yozing)", y, f"${a} = {y} \\cdot 100 + {o_} \\cdot 10 + {b_}$\nJavob: {y}"))
            b = rng.randint(100, 999); testlar.append((f"Qaysi son katta: {a} yoki {b}?", max(a, b), [min(a, b), a + b, abs(a - b) or 1]))
        elif tur == "olchov":
            v = rng.choice([("m", "sm", 100), ("dm", "sm", 10), ("sm", "mm", 10), ("km", "m", 1000), ("m", "dm", 10)]); x = rng.randint(2, 9)
            mashq.append((f"{x} {v[0]} — necha {v[1]}?", x * v[2], f"1 {v[0]} = {v[2]} {v[1]}: ${x} \\cdot {v[2]} = {x * v[2]}$\nJavob: {x * v[2]}"))
            testlar.append((f"1 {v[0]} necha {v[1]}?", v[2], [v[2] * 10, max(1, v[2] // 10), v[2] + 10]))
        elif tur == "vaqt":
            s, m = rng.randint(1, 4), rng.choice([10, 15, 20, 30, 40])
            mashq.append((f"{s} soat {m} minut — necha minut?", 60 * s + m, f"1 soat = 60 minut: ${s} \\cdot 60 + {m} = {60 * s + m}$\nJavob: {60 * s + m}"))
            testlar.append((f"{s} soat necha minut?", 60 * s, [100 * s, 60 + s, 30 * s]))
        elif tur in ("perimetr", "yuz", "shakl"):
            a, b = rng.randint(2, 9), rng.randint(2, 9)
            if tur == "yuz" or (tur == "shakl" and i % 2):
                mashq.append((f"To‘g‘ri to‘rtburchakning bo‘yi {a} sm, eni {b} sm. Yuzi necha kvadrat santimetr?", a * b, f"Kataklar: {a} qatorda {b} tadan — ${a} \\cdot {b} = {a * b}$ sm²\nJavob: {a * b}"))
                testlar.append((f"Tomonlari {a} sm va {b} sm bo‘lgan to‘g‘ri to‘rtburchak yuzi?", a * b, [2 * (a + b), a + b, a * b + a]))
            else:
                mashq.append((f"To‘g‘ri to‘rtburchakning tomonlari {a} sm va {b} sm. Perimetri necha sm?", 2 * (a + b), f"${a} + {b} + {a} + {b} = {2 * (a + b)}$ sm\nJavob: {2 * (a + b)}"))
                testlar.append((f"Kvadratning tomoni {a} sm. Perimetri?", 4 * a, [a * a, 2 * a, a + 4]))
        elif tur == "tartib":
            a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 20)
            mashq.append((f"${c} + {a} \\cdot {b} = \\;?$", c + a * b, f"Avval ko‘paytirish: ${a} \\cdot {b} = {a * b}$, keyin qo‘shish: ${c} + {a * b} = {c + a * b}$\nJavob: {c + a * b}"))
            testlar.append((f"${c} + {a} \\cdot {b} = ?$", c + a * b, [(c + a) * b, c + a + b, c * a + b]))
        elif tur == "tenglama":
            a, x = rng.randint(2, 9), rng.randint(2, 9)
            if i % 2:
                mashq.append((f"$x \\cdot {a} = {a * x}$. $x$ = ?", x, f"Noma’lum ko‘paytuvchi = ko‘paytma : ma’lum ko‘paytuvchi: ${a * x} : {a} = {x}$\nJavob: {x}"))
            else:
                mashq.append((f"$x + {a * 3} = {a * 3 + x * 5}$. $x$ = ?", x * 5, f"${a * 3 + x * 5} - {a * 3} = {x * 5}$\nJavob: {x * 5}"))
            testlar.append((f"$x \\cdot {a} = {a * x}$ bo‘lsa, $x$ = ?", x, [a * x, x + 1, a]))
        elif tur == "nolbir":
            a = rng.randint(2, 99)
            k_ = rng.choice([(f"${a} \\cdot 1$", a), (f"${a} \\cdot 0$", 0), (f"${a} : 1$", a), (f"$0 : {a}$", 0)])
            mashq.append((f"{k_[0]} = ?", k_[1], f"1 ga ko‘paytirish va bo‘lish sonni o‘zgartirmaydi; 0 ga ko‘paytirganda 0 chiqadi.\nJavob: {k_[1]}"))
            testlar.append((f"{k_[0]} = ?", k_[1], [a + 1, 1, a * 10]))
        elif tur in ("yaxlitkop", "xossa"):
            a, b = rng.randint(2, 9), rng.randint(2, 9)
            if tur == "xossa":
                c = rng.randint(2, 6)
                mashq.append((f"$({a} + {b}) \\cdot {c} = \\;?$", (a + b) * c, f"${a} \\cdot {c} + {b} \\cdot {c} = {a * c} + {b * c} = {(a + b) * c}$\nJavob: {(a + b) * c}"))
                testlar.append((f"$({a} + {b}) \\cdot {c} = ?$", (a + b) * c, [a + b * c, a * c + b, (a + b) + c]))
            else:
                mashq.append((f"${a * 10} \\cdot {b} = \\;?$", a * 10 * b, f"${a} \\cdot {b} = {a * b}$, oxiriga 0: ${a * b * 10}$\nJavob: {a * b * 10}"))
                testlar.append((f"${a * 10} \\cdot {b} = ?$", a * b * 10, [a * b, a * b * 100, a * 10 + b]))
        elif tur in ("kopaytma", "bolish", "bogliq", "marta", "juft"):
            a, b = rng.randint(2, 9), rng.randint(2, 9)
            if tur == "marta":
                mashq.append((f"Ali {a} ta konfet oldi, Malika undan {b} marta ko‘p oldi. Malika nechta oldi?", a * b, f"«marta ko‘p» — ko‘paytiramiz: ${a} \\cdot {b} = {a * b}$\nJavob: {a * b}"))
                testlar.append((f"{a} ning {b} marta ortig‘i?", a * b, [a + b, a * b + a, a]))
            elif tur in ("bolish", "bogliq"):
                mashq.append((f"{a * b} ta olmani {a} ta savatga teng bo‘lishdi. Har savatda nechta?", b, f"${a * b} : {a} = {b}$, chunki ${a} \\cdot {b} = {a * b}$\nJavob: {b}"))
                testlar.append((f"${a * b} : {a} = ?$", b, [a, a * b - a, b + 1]))
            elif tur == "juft":
                x = rng.randint(10, 99); mashq.append((f"{x} soni juftmi? (ha / yo‘q)", "ha" if x % 2 == 0 else "yo‘q", f"Oxirgi raqami {x % 10} — {'juft' if x % 2 == 0 else 'toq'}.\nJavob: {'ha' if x % 2 == 0 else 'yo‘q'}"))
                testlar.append(("Qaysi son juft?", 2 * rng.randint(6, 49), [2 * rng.randint(5, 49) + 1 for _ in range(3)]))
            else:
                mashq.append((f"{a} ta savatda {b} tadan olma bor. Jami nechta olma?", a * b, f"${' + '.join([str(b)] * a)} = {a} \\cdot {b} = {a * b}$\nJavob: {a * b}"))
                testlar.append((f"${a} \\cdot {b} = ?$", a * b, [a + b, a * b + 1, a * b - a]))
        elif tur == "yigindi":
            a, b, c = rng.randint(20, 60), rng.randint(5, 30), rng.randint(2, 15)
            mashq.append((f"$({a} + {b}) - {c} = \\;?$", a + b - c, f"Qulay usul: ${a} + ({b} - {c})$ yoki ${a + b} - {c} = {a + b - c}$\nJavob: {a + b - c}"))
            testlar.append((f"$({a} + {b}) - {c} = ?$", a + b - c, [a + b + c, a - b + c, a + b - c + 10]))
        else:
            a, b = rng.randint(10, 60), rng.randint(5, 39)
            q_op = "+" if (tur in ("qosh", "ustun", "aralash", "masala") and i % 2 == 0) or tur == "qosh" else "-"
            if q_op == "-" and b > a:
                a, b = b, a
            j = a + b if q_op == "+" else a - b
            if tur == "masala":
                nom_, bel = rng.choice(NARSALAR); i1, i2 = rng.sample(ISMLAR, 2)
                mashq.append((f"{bel} {i1}da {a} ta {nom_} bor. {i2}da {'undan ' + str(b) + ' ta ko‘p' if q_op == '+' else str(b) + ' ta kam'}. {i2}da nechta?", j, f"${a} {q_op} {b} = {j}$\nJavob: {j}"))
            else:
                mashq.append((f"${a} {q_op} {b} = \\;?$", j, f"Ustun ko‘rinishida: birliklar ostida birliklar, o‘nliklar ostida o‘nliklar.\nJavob: {j}"))
            testlar.append((f"${a} {q_op} {b} = ?$", j, [j + 10, abs(j - 10) or 1, j + 1]))
    korilgan, mashq2 = set(), []
    for q, j, y in mashq:
        if q not in korilgan:
            korilgan.add(q); mashq2.append((q, j, y))
    mashq = mashq2
    for k, (q, j, y) in enumerate(mashq):
        R.append(("masala", f"M{k + 1:02d}", f"Mashq {k + 1}", q, "", "", "", str(j), y, "", "", "", "", "oson" if k < 4 else "o‘rta", ""))
    for k, (q, j, xs) in enumerate(testlar[:6]):
        R.append(rows_test(rng, q, j, xs, f"T{k + 1:02d}"))
    R.append(("xulosa", "", "🌟 Bugun nimani o‘rgandik", M[mid]["nazariya"], M[mid]["tushuncha"], "", "", "", "", "", "", "", "", "", ""))
    return R


def darslar2():
    L = [x for x in D["L"] if x["sinf"] == "2"]
    out, sanoq = [], {}
    for x in L:
        nom = toza(x["nom"]).replace("Muqadim a", "Muqaddima")
        nom = re.sub(r"(\d)(ga|ni)\b", r"\1 \2", nom)
        nom = re.sub(r"\bva(\d)", r"va \1", nom).replace("1 ga bolish", "1 ga bo‘lish")
        nom = re.sub(r"^\d{1,3}\s+(?=[A-ZА-ЯЎҚҒҲ‘'])", "", nom)   # «69 Soat va minut» → «Soat va minut» («7 sonini» saqlanadi)
        nom = re.sub(r"b o\s*.y ic h a", "bo‘yicha", nom)
        nom = re.sub(r"\s+", " ", nom.replace("b o 'y ic h a", "bo‘yicha").replace("m inut", "minut").replace("m asalalar", "masalalar")).strip()
        if nom.lower().startswith("muqaddima"):
            continue
        sanoq[nom] = sanoq.get(nom, 0) + 1
        out.append((nom if sanoq[nom] == 1 else f"{nom} ({sanoq[nom]}-dars)", nom, x))
    return out
