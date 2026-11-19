"""PISA matematika — kengaytma 1: sonlar, foiz-ulush, nisbat, birliklar, algebra (yangi mavzular, har biri: dars + generator savollar)."""
from fractions import Fraction

from modules.pisa_mat_g import reg, num, som, _y, _o

TOP = "P_M"
TEMA = {}
_SOHA = {"PM-1": "Miqdor", "PM-2": "Miqdor", "PM-3": "Miqdor", "PM-4": "Miqdor", "PM-5": "O‘zgarish va bog‘liqlik"}
_ESKI = {"PM-1": "PM-MIQ", "PM-2": "PM-MIQ", "PM-3": "PM-MIQ", "PM-4": "PM-MIQ", "PM-5": "PM-OZG"}


def tema(kod, kb, nom, belgi, maqsad, dars):
    TEMA[kod] = {"nom": nom, "soha": _SOHA[kb], "belgi": belgi, "maqsad": maqsad, "bolim": _ESKI[kb], "kb": kb, "toplam": TOP,
                 "dars": [{"sarlavha": a, "doska": b, "ovoz": c} for a, b, c in dars]}


def sh(kod, tur):
    return reg(kod, tur)


# ═════════ 1-BO'LIM · SONLAR VA HISOBLASH ═════════
tema("pm_butun", "PM-1", "Butun sonlar: harorat, balans, qavat", "🌡️", "Manfiy sonlar bilan hayotiy hisoblar: harorat farqi, hisob raqami, lift va dengiz sathi", [
    ("Manfiy sonlar son o‘qida", "−5 < −2 < 0 < 3\nO‘ngdagi son har doim katta\nFarq = katta − kichik",
     "Sonlar to‘g‘ri chiziqda joylashadi. Nolning o‘ng tomonida musbat, chap tomonida manfiy sonlar turadi. O‘ngdagi son doim kattaroq: minus besh minus ikkidan kichik. Ikki son orasidagi farqni topish uchun kattasidan kichigini ayiramiz."),
    ("Qo‘shish va ayirish", "a + (−b) = a − b\na − (−b) = a + b\nHarorat −3° dan +5° gacha: 5 − (−3) = 8°",
     "Manfiy sonni qo‘shish — ayirish bilan teng. Manfiy sonni ayirish esa qo‘shishga aylanadi. Masalan, harorat minus uchdan plyus beshgacha ko‘tarilsa, o‘zgarish besh minus minus uch, ya’ni sakkiz daraja."),
    ("Hayotiy holatlar", "Balans: +50 000 kirim, −70 000 chiqim\nYangi balans = eski + kirim − chiqim\nQavat: −2 = yerto‘la",
     "Bank hisobida kirim musbat, chiqim manfiy son. Yangi balans eski balansga kirimni qo‘shib, chiqimni ayirib topiladi. Balans manfiy bo‘lsa, qarz bor degani. Binoda minus ikkinchi qavat — yer ostidagi ikkinchi qavat."),
])


@sh("pm_butun", "yopiq")
def pm_butun_1(rng):
    sh_ = rng.choice(["Toshkent", "Samarqand", "Buxoro", "Nukus", "Farg‘ona"]); a = rng.randint(-15, -2); b = rng.randint(3, 18)
    return _y(rng, f"Ertalab {sh_}da harorat {a}° edi, tushda {b}° ga ko‘tarildi. Harorat necha darajaga oshdi?", b - a,
              [f"Oshish = oxirgi − boshlang‘ich = {b} − ({a}) = {b} + {-a} = {b - a}°."], noto=[b + a, a - b, abs(a) - b])


@sh("pm_butun", "yopiq")
def pm_butun_2(rng):
    bal = rng.choice(range(10, 90, 5)) * 1000; chq = bal + rng.choice(range(5, 60, 5)) * 1000
    return _y(rng, f"Hisobingizda {som(bal)} so‘m bor edi. Siz {som(chq)} so‘mlik telefon sotib oldingiz (karta bilan, ortiqchasi qarz bo‘ladi). Hisobingizdagi yangi balans qancha (so‘m)?", bal - chq,
              [f"Yangi balans = {som(bal)} − {som(chq)} = {som(bal - chq)} so‘m.", "Manfiy balans — qarz."], noto=[chq - bal, bal + chq, -(bal + chq)])


@sh("pm_butun", "yopiq")
def pm_butun_3(rng):
    q1 = rng.randint(-3, -1); q2 = rng.randint(6, 25)
    return _y(rng, f"Lift {q1}-qavatdagi avtoturargohdan {q2}-qavatga ko‘tarildi. Lift nechta qavat ko‘tarildi?", q2 - q1,
              [f"{q2} − ({q1}) = {q2 - q1} qavat.", "Nol qavat yo‘q: sanashda ehtiyot bo‘ling — bu yerda 0 yer sathi deb olingan."], noto=[q2 + q1, q2, q2 - q1 + 1])


@sh("pm_butun", "yopiq")
def pm_butun_4(rng):
    a = rng.randint(-12, -3); b = rng.randint(-9, -2); c = rng.randint(2, 9)
    t = a - b + c
    return _y(rng, f"Hisoblang: ({a}) − ({b}) + {c}", t, [f"({a}) − ({b}) = {a} + {-b} = {a - b}.", f"{a - b} + {c} = {t}."], noto=[a + b + c, a - b - c, -t])


@sh("pm_butun", "ochiq")
def pm_butun_5(rng):
    t0 = rng.randint(-20, -5); d = [rng.randint(2, 9) for _ in range(3)]; s = [rng.choice([1, -1]) for _ in range(3)]
    t = [t0]
    for dd, ss in zip(d, s):
        t.append(t[-1] + ss * dd)
    return _o(f"Qishki kunda harorat soatlar bo‘yicha o‘zgardi: boshida {t0}°; 1-soatda {'+' if s[0] > 0 else '−'}{d[0]}°; 2-soatda {'+' if s[1] > 0 else '−'}{d[1]}°; 3-soatda {'+' if s[2] > 0 else '−'}{d[2]}°.",
              [("a) 3 soatdan keyingi harorat (°):", t[3]), ("b) Eng past harorat (°):", min(t))],
              [f"a) {t0} dan boshlab: {', '.join(str(x) for x in t)}. Oxirgisi: {t[3]}°.", f"b) Eng kichik qiymat: {min(t)}°."])


@sh("pm_butun", "ochiq")
def pm_butun_6(rng):
    ish = rng.choice(range(20, 80, 5)) * 1000; kre = rng.choice(range(10, 50, 5)) * 1000; ch = rng.choice(range(30, 110, 10)) * 1000
    bal = ish - kre - ch
    return _o(f"Oy boshida hisobda {som(ish)} so‘m bor edi. Oy davomida kommunal to‘lov {som(kre)} so‘m va xaridlar {som(ch)} so‘m yechildi.",
              [("a) Oy oxiridagi balans (so‘m):", bal), ("b) Balans manfiy bo‘lsa, qarz qancha? (qarz bo‘lmasa 0 yozing):", max(0, -bal))],
              [f"a) {som(ish)} − {som(kre)} − {som(ch)} = {som(bal)}.", "b) Manfiy balans — qarz miqdori shu sonning moduli." if bal < 0 else "b) Balans manfiy emas, qarz yo‘q."])


@sh("pm_butun", "ochiq")
def pm_butun_7(rng):
    d = rng.choice([-120, -250, -400, -86]); m = rng.choice([8848, 4500, 3200, 1900])
    return _o(f"Suvosti kemasi dengiz sathidan {abs(d)} m chuqurlikda, tog‘ cho‘qqisi esa dengiz sathidan {m} m balandlikda.", [("a) Ular orasidagi balandlik farqi (m):", m - d), ("b) Kema 50 m tushsa, yangi chuqurlik (dengiz sathiga nisbatan, m):", d - 50)],
              [f"a) {m} − ({d}) = {m + abs(d)} m.", f"b) {d} − 50 = {d - 50} m."])


tema("pm_kasr", "PM-1", "Kasr va o‘nli kasr: ulush hayotda", "🍕", "Retsept, ulush, vaqt va masofani kasr bilan hisoblash; kasrlarni taqqoslash", [
    ("Kasr — butunning ulushi", "3/4 = 3 ta ulush, jami 4 ta teng bo‘lak\n3/4 = 0,75 = 75%\nBo‘lak sonini shu kasrga ko‘paytiring",
     "Kasr butunning bir qismini bildiradi. Uch to‘rtdan — butun to‘rtta teng bo‘lakka bo‘linib, uchtasi olingani. U nol butun yetmish besh yuzdan, ya’ni yetmish besh foizga teng. Sondan kasr ulushini topish uchun sonni kasrga ko‘paytiramiz."),
    ("Kasrlarni taqqoslash va qo‘shish", "1/2 + 1/3 = 3/6 + 2/6 = 5/6\nBir xil maxraj!\nO‘nli kasrga o‘tkazish: bo‘lamiz",
     "Kasrlarni qo‘shish uchun avval maxrajlarni tenglashtiramiz. Yarim va uchdan bir — umumiy maxraj olti: uch oltidan plyus ikki oltidan, besh oltidan. Taqqoslashda ham umumiy maxrajga keltirish yoki o‘nli kasrga o‘tkazish qulay."),
    ("Ulush masalalari", "x ning 2/5 qismi = 60 → x = 60 : 2/5 = 150\nQolgan qism = 1 − ulush",
     "Ba’zan ulush ma’lum, butun noma’lum bo‘ladi. Masalan, sonning ikki beshdan qismi oltmish bo‘lsa, sonni topish uchun oltmishni ikki beshga bo‘lamiz. Qolgan qismni topishda birdan olingan ulushni ayiramiz."),
])


@sh("pm_kasr", "yopiq")
def pm_kasr_1(rng):
    n = rng.choice([24, 36, 40, 48, 60, 72, 80, 90, 120]); p, q = rng.choice([(1, 2), (1, 3), (2, 3), (3, 4), (2, 5), (3, 5), (1, 4), (5, 6)])
    if n % q: n = q * 12
    x = n * p // q
    return _y(rng, f"Sinfda {n} ta o‘quvchi bor. Ularning {p}/{q} qismi qizlar. Qizlar nechta?", x, [f"{n} · {p}/{q} = {n // q} · {p} = {x}."], noto=[n - x, n // q, x + q])


@sh("pm_kasr", "yopiq")
def pm_kasr_2(rng):
    a, b = rng.choice([(1, 2), (1, 3), (1, 4), (2, 3)]), rng.choice([(1, 6), (1, 5), (1, 8), (1, 4)])
    s = Fraction(*a) + Fraction(*b)
    return _y(rng, f"Retseptga ko‘ra {a[0]}/{a[1]} kg un va yana {b[0]}/{b[1]} kg un kerak. Jami necha kg un kerak?", f"${s.numerator}/{s.denominator}$ kg" if s.denominator > 1 else f"${s.numerator}$ kg",
              [f"{a[0]}/{a[1]} + {b[0]}/{b[1]} = {s.numerator}/{s.denominator}."],
              noto=[f"${a[0] + b[0]}/{a[1] + b[1]}$ kg", f"${s.numerator + 1}/{s.denominator}$ kg", f"${s.numerator}/{s.denominator + 1}$ kg"])


@sh("pm_kasr", "yopiq")
def pm_kasr_3(rng):
    p, q = rng.choice([(2, 5), (3, 8), (3, 10), (7, 20), (1, 4), (3, 4), (4, 5)]); x = Fraction(p, q)
    return _y(rng, f"{p}/{q} kasrni o‘nli kasr ko‘rinishida yozing.", x, [f"{p} : {q} = {num(x)}."], noto=[Fraction(q, p) if q > p else Fraction(p * 2, q), Fraction(p, 10), x + Fraction(1, 10)], tartib=True)


@sh("pm_kasr", "yopiq")
def pm_kasr_4(rng):
    p, q, ch = rng.choice([(2, 3, 24), (2, 5, 30), (3, 4, 45), (3, 7, 21), (5, 6, 40), (2, 9, 18), (3, 8, 27)]); tot = ch * q // p
    return _y(rng, f"Sonning {p}/{q} qismi {ch} ga teng. Sonning o‘zi nechaga teng?", tot, [f"x · {p}/{q} = {ch} → x = {ch} : {p}/{q} = {ch} · {q}/{p} = {tot}."], noto=[ch * p // q, ch + p, tot + q])


@sh("pm_kasr", "ochiq")
def pm_kasr_5(rng):
    soat = rng.choice([2, 3, 4, 5, 6]); a = rng.choice([(1, 2), (1, 3), (1, 4)]); b = rng.choice([(1, 6), (1, 4), (1, 5)])
    ye = Fraction(*a) + Fraction(*b); q = 1 - ye
    return _o(f"Maktab kuni davomida o‘quvchi vaqtining {a[0]}/{a[1]} qismini darslarga, {b[0]}/{b[1]} qismini uyqu va dam olishga sarfladi. Qolgani — mustaqil mashg‘ulot.",
              [("a) Darslar va dam olish birgalikda butunning qancha qismi? (kasr yoki o‘nli kasr)", ye), ("b) Mustaqil mashg‘ulotga butunning qancha qismi qoldi?", q)],
              [f"a) {a[0]}/{a[1]} + {b[0]}/{b[1]} = {num(ye)}.", f"b) 1 − {num(ye)} = {num(q)}."])


@sh("pm_kasr", "ochiq")
def pm_kasr_6(rng):
    n = rng.choice([240, 360, 480, 600, 720, 840]); a = rng.choice([(1, 3), (1, 4), (1, 5)]); b = rng.choice([(1, 6), (1, 8), (1, 10)])
    x = n * a[0] // a[1]; y = n * b[0] // b[1]
    return _o(f"Yo‘l uzunligi {n} km. Birinchi kuni yo‘lning {a[0]}/{a[1]} qismi, ikkinchi kuni {b[0]}/{b[1]} qismi bosib o‘tildi.", [("a) Ikki kunda necha km bosildi?", x + y), ("b) Necha km qoldi?", n - x - y)],
              [f"a) {n} · {a[0]}/{a[1]} = {x} km; {n} · {b[0]}/{b[1]} = {y} km; {x} + {y} = {x + y}.", f"b) {n} − {x + y} = {n - x - y} km."])


@sh("pm_kasr", "ochiq")
def pm_kasr_7(rng):
    p = rng.choice([2, 3, 4, 5]); q = rng.choice([6, 8, 9, 10]); r = rng.choice([2, 3, 5]); s = rng.choice([7, 9, 12])
    a, b = Fraction(p, q), Fraction(r, s)
    kat = "birinchisi" if a > b else "ikkinchisi"
    return _o(f"Ikki idishdagi sharbat: birinchisida {p}/{q} litr, ikkinchisida {r}/{s} litr.", [("a) Qaysi idishda ko‘p? (1 yoki 2 yozing)", 1 if a > b else 2), ("b) Farq necha litr? (o‘nli kasr, 2 xona aniqlikda yaxlitlang)", Fraction(str(round(float(abs(a - b)), 2))))],
              [f"a) {p}/{q} = {num(round(float(a), 3))}; {r}/{s} = {num(round(float(b), 3))} → {kat} ko‘p.", f"b) Farq ≈ {num(round(float(abs(a - b)), 2))} litr."])


tema("pm_daraja", "PM-1", "Daraja, kvadrat va standart shakl", "🔭", "Katta va kichik sonlarni daraja bilan yozish, kvadrat va kub, standart shakl", [
    ("Daraja nima?", "aⁿ = a · a · … · a (n marta)\n3² = 9   2³ = 8   10⁴ = 10 000\na⁰ = 1",
     "Daraja bir sonning o‘zi bilan necha marta ko‘paytirilishini ko‘rsatadi. Uch kvadrat — uch marta uch, to‘qqiz. Ikki kub — sakkiz. O‘n to‘rtinchi daraja — bir va to‘rtta nol."),
    ("Standart shakl", "5 300 000 = 5,3 · 10⁶\n0,00042 = 4,2 · 10⁻⁴\n1 ≤ a < 10",
     "Juda katta yoki juda kichik sonlarni standart shaklda yozamiz: bir va o‘n orasidagi son ko‘paytirilsin o‘nning darajasiga. Besh million uch yuz ming — besh butun uch o‘ndan o‘nning oltinchi darajasi."),
    ("Daraja amallari", "aᵐ · aⁿ = aᵐ⁺ⁿ\naᵐ : aⁿ = aᵐ⁻ⁿ\n(aᵐ)ⁿ = aᵐⁿ",
     "Asoslari bir xil darajalarni ko‘paytirsak, ko‘rsatkichlar qo‘shiladi. Bo‘lsak ayriladi. Darajaning darajasida ko‘rsatkichlar ko‘paytiriladi."),
])


@sh("pm_daraja", "yopiq")
def pm_dar_1(rng):
    a = rng.randint(2, 9); n = rng.choice([2, 3, 4]); v = a ** n
    return _y(rng, f"${a}^{n}$ ning qiymati nechaga teng?", v, [f"{a}^{n} = " + " · ".join([str(a)] * n) + f" = {v}."], noto=[a * n, a + n, a ** (n - 1) if n > 2 else a ** 3])


@sh("pm_daraja", "yopiq")
def pm_dar_2(rng):
    k = rng.randint(3, 9)
    return _y(rng, f"Standart shaklda yozilgan $10^{{{k}}}$ — bu birdan keyin nechta nol turgan son?", k, [f"10^{k} = 1 va {k} ta nol."], noto=[k - 1, k + 1, 10])


@sh("pm_daraja", "yopiq")
def pm_dar_3(rng):
    a = rng.choice([2, 3, 5, 10]); m = rng.randint(2, 6); n = rng.randint(2, 6)
    return _y(rng, f"Soddalashtiring: ${a}^{m} \\cdot {a}^{n}$", f"${a}^{m + n}$", [f"Asoslar bir xil — ko‘rsatkichlar qo‘shiladi: {m} + {n} = {m + n}."], noto=[f"${a}^{m * n}$", f"${a * a}^{m + n}$", f"${a}^{m + n + 1}$", f"${a}^{m + n + 3}$", f"${a}^{m + n - 1}$"])


@sh("pm_daraja", "yopiq")
def pm_dar_4(rng):
    a = rng.randint(2, 9); b = rng.randint(1, 9); k = rng.randint(3, 8); v = (a * 10 + b) * 10 ** (k - 1)
    t = Fraction(a * 10 + b, 10)
    return _y(rng, f"{som(v)} sonini standart shaklda yozing.", f"${num(t)} \\cdot 10^{{{k}}}$", [f"{som(v)} = {num(t)} · 10^{k}."],
              noto=[f"${num(t)} \\cdot 10^{{{k - 1}}}$", f"${num(t * 10)} \\cdot 10^{{{k}}}$", f"${num(t)} \\cdot 10^{{{k + 1}}}$"])


@sh("pm_daraja", "ochiq")
def pm_dar_5(rng):
    a = rng.randint(3, 12)
    return _o(f"Kvadrat shaklidagi maydonning tomoni {a} m.", [("a) Maydon yuzi (m²):", a * a), ("b) Kub shaklidagi quti qirrasi {0} m bo‘lsa, hajmi (m³):".format(a), a ** 3)],
              [f"a) {a}² = {a * a}.", f"b) {a}³ = {a ** 3}."])


@sh("pm_daraja", "ochiq")
def pm_dar_6(rng):
    k = rng.randint(2, 4); s = rng.choice([2, 3])
    return _o(f"Bakteriya har soatda {s} baravar ko‘payadi. Boshida 1 ta bakteriya bor.", [(f"a) {k} soatdan keyin nechta bo‘ladi?", s ** k), (f"b) {k + 2} soatdan keyin nechta bo‘ladi?", s ** (k + 2))],
              [f"a) {s}^{k} = {s ** k}.", f"b) {s}^{k + 2} = {s ** (k + 2)}."])


@sh("pm_daraja", "ochiq")
def pm_dar_7(rng):
    a = rng.randint(2, 9); m = rng.randint(3, 8)
    return _o(f"Hisoblang va javobni son bilan yozing: a) {a}^{m} : {a}^{m - 2};  b) ({a}^2)^2.", [("a) qiymat:", a ** 2), ("b) qiymat:", a ** 4)],
              [f"a) {a}^{m} : {a}^{m - 2} = {a}^2 = {a * a}.", f"b) ({a}²)² = {a}⁴ = {a ** 4}."])


tema("pm_taxmin", "PM-1", "Yaxlitlash va taxminiy hisob", "🎯", "Narx, masofa va miqdorni yaxlitlab tez baholash; xatoni tushunish", [
    ("Yaxlitlash qoidasi", "Keyingi raqam 0–4 → pastga\nKeyingi raqam 5–9 → yuqoriga\n3 476 → 3 500 (yuzlarga)",
     "Sonni yaxlitlashda saqlanadigan xonadan keyingi raqamga qaraymiz. Nol dan to‘rtgacha bo‘lsa — o‘zgarmaydi, beshdan to‘qqizgacha bo‘lsa — bitta oshiramiz. Uch ming to‘rt yuz yetmish olti yuzlarga yaxlitlansa, uch ming besh yuz bo‘ladi."),
    ("Taxminiy hisob", "398 · 5 ≈ 400 · 5 = 2000\nNarxni tez baholash: 19 900 ≈ 20 000",
     "Do‘konda aniq hisoblashga vaqt kam. Narxlarni qulay sonlarga yaxlitlab, tez baholaymiz. Uch yuz to‘qson sakkiz ni besh ga ko‘paytirish o‘rniga to‘rt yuzni beshga ko‘paytiramiz — taxminan ikki ming."),
    ("Pul yetadimi?", "Yetarlimi? Narxlarni YUQORIGA yaxlitlang\nJami ≈ … ≤ byudjet → yetadi",
     "Pul yetishini tekshirishda narxlarni yuqoriga yaxlitlaymiz. Agar yuqoriga yaxlitlangan jami ham byudjetdan oshmasa, pul aniq yetadi."),
])


@sh("pm_taxmin", "yopiq")
def pm_tax_1(rng):
    x = rng.randint(1000, 99999); n = rng.choice([10, 100, 1000]); y = (x + n // 2) // n * n
    return _y(rng, f"{som(x)} sonini {n} gacha yaxlitlang.", y, [f"{som(x)} → keyingi raqamga qarab: {som(y)}."], noto=[x // n * n, (x // n + 1) * n if (x // n + 1) * n != y else y + n, y - n])


@sh("pm_taxmin", "yopiq")
def pm_tax_2(rng):
    p1, p2, p3 = rng.randint(19, 49) * 1000 + rng.choice([900, 990, 500]), rng.randint(9, 29) * 1000 + rng.choice([900, 990]), rng.randint(5, 19) * 1000 + rng.choice([900, 800])
    byud = rng.choice([100000, 120000, 150000])
    taxm = (p1 + 999) // 1000 * 1000 + (p2 + 999) // 1000 * 1000 + (p3 + 999) // 1000 * 1000
    return _y(rng, f"Narxlar: {som(p1)}, {som(p2)} va {som(p3)} so‘m. Har birini yuqoriga mingga yaxlitlab jamini baholang (so‘m).", taxm,
              [f"Yuqoriga: {som((p1 + 999) // 1000 * 1000)} + {som((p2 + 999) // 1000 * 1000)} + {som((p3 + 999) // 1000 * 1000)} = {som(taxm)}."], noto=[p1 + p2 + p3 - 1000, taxm + 1000, taxm - 3000])


@sh("pm_taxmin", "yopiq")
def pm_tax_3(rng):
    a = rng.randint(190, 990); b = rng.randint(4, 9); ya = round(a, -2)
    return _y(rng, f"{a} · {b} ko‘paytmasini ({a} ni yuzlarga yaxlitlab) taxminan baholang.", ya * b, [f"{a} ≈ {ya}; {ya} · {b} = {ya * b}."], noto=[ya * b + 100, ya * b - 100 * b, ya + b])


@sh("pm_taxmin", "yopiq")
def pm_tax_4(rng):
    km = rng.randint(200, 900); t = rng.choice([4, 5, 6, 8]); v = km // t; ya = round(v, -1)
    return _y(rng, f"{km} km yo‘lni {t} soatda bosib o‘tdingiz. O‘rtacha tezlik taxminan necha km/soat? (o‘nlikka yaxlitlang)", ya, [f"{km} : {t} ≈ {km / t:.1f} → o‘nlikka: {ya}."], noto=[ya + 10, ya - 10, ya + 20])


@sh("pm_taxmin", "ochiq")
def pm_tax_5(rng):
    n = rng.randint(120, 480); p = rng.randint(19, 49) * 1000 + 900
    ya = round(p, -3)
    return _o(f"Maktab {n} ta o‘quvchiga bittadan kitob oladi. Bir kitob narxi {som(p)} so‘m.", [("a) Kitob narxini yaxlitlang (minglarga, so‘m):", ya), ("b) Taxminiy umumiy xarajat (so‘m):", ya * n)],
              [f"a) {som(p)} ≈ {som(ya)}.", f"b) {som(ya)} · {n} = {som(ya * n)}."])


@sh("pm_taxmin", "ochiq")
def pm_tax_6(rng):
    d = rng.choice([3, 7, 12, 29]); m = rng.randint(1100, 2400)
    return _o(f"Kitobda {m} sahifa bor. Siz kuniga {d} sahifa o‘qiysiz.", [("a) Necha kunda tugatasiz? (butun kunlarga yuqoriga yaxlitlang)", -(-m // d)), ("b) Kunlik o‘qish {0} sahifaga oshsa (yuqoriga yaxlitlang):".format(d + 5), -(-m // (d + 5)))],
              [f"a) {m} : {d} = {m / d:.2f} → {-(-m // d)} kun.", f"b) {m} : {d + 5} = {m / (d + 5):.2f} → {-(-m // (d + 5))} kun."])


@sh("pm_taxmin", "ochiq")
def pm_tax_7(rng):
    c = rng.choice([48, 52, 63, 77]); n = rng.randint(21, 38)
    pul = c * 1000 + rng.choice([0, 400, 700])
    return _o(f"{n} kishi uchun har biri {som(pul)} so‘mdan chipta olinadi.", [("a) Narxni minglarga yaxlitlang:", round(pul, -3)), ("b) Taxminiy umumiy summa (so‘m):", round(pul, -3) * n)],
              [f"a) {som(pul)} ≈ {som(round(pul, -3))}.", f"b) {som(round(pul, -3))} · {n} = {som(round(pul, -3) * n)}."])


# ═════════ 2-BO'LIM · FOIZ VA ULUSH ═════════
tema("pm_foizqayta", "PM-2", "Foiz o‘zgarishi va murakkab foiz", "📊", "Ketma-ket oshish/kamayish, narx dinamikasi, murakkab foiz (yillik o‘sish)", [
    ("Foiz o‘zgarishi", "O‘zgarish % = (yangi − eski)/eski · 100\nOshdi: ×(1 + p/100)\nKamaydi: ×(1 − p/100)",
     "Foiz o‘zgarishi doim eski qiymatga nisbatan hisoblanadi. Qiymat oshsa, uni bir plyus foiz yuzdan ga ko‘paytiramiz. Kamaysa — bir minus foiz yuzdan ga."),
    ("Ketma-ket o‘zgarish", "+20% va keyin −20% ≠ 0\n100 → 120 → 96\nKo‘paytiriladi: 1,2 · 0,8 = 0,96",
     "Yigirma foiz oshib, keyin yigirma foiz kamaysa, boshlang‘ich qiymatga qaytmaymiz. Chunki ikkinchi foiz yangi, kattaroq qiymatdan olinadi. Koeffitsiyentlar ko‘paytiriladi: bir butun ikki ni nol butun sakkizga ko‘paytirsak, nol butun to‘qson olti."),
    ("Murakkab foiz", "S = A · (1 + p/100)ⁿ\n1 000 000, 10%, 3 yil → 1 331 000",
     "Murakkab foizda har yili foiz oldingi yilgi yig‘indidan hisoblanadi. Formula: boshlang‘ich summa ko‘paytirilsin bir plyus foiz yuzdan ning n-darajasiga."),
])


@sh("pm_foizqayta", "yopiq")
def pm_fq_1(rng):
    a = rng.choice(range(20, 90, 5)) * 1000; p = rng.choice([10, 20, 25, 40, 50]); k = a * (100 + p) // 100
    return _y(rng, f"Mahsulot narxi {som(a)} so‘mdan {som(k)} so‘mga o‘zgardi. Necha foizga oshgan?", p, [f"({som(k)} − {som(a)}) / {som(a)} · 100 = {p}%."], noto=[p + 5, p - 5 if p > 5 else p + 10, 100 * (k - a) // k if (k - a) * 100 % k == 0 else p + 15])


@sh("pm_foizqayta", "yopiq")
def pm_fq_2(rng):
    a = rng.choice([10, 20, 25, 50]); v = rng.choice([200, 400, 800, 1000]) * 100
    k = v * (100 + a) // 100 * (100 - a) // 100
    return _y(rng, f"Narx {a}% ga oshirildi, keyin yangi narx {a}% ga arzonlashtirildi. Boshida {som(v)} so‘m edi. Oxirgi narx qancha?", k,
              [f"{som(v)} · {100 + a}/100 = {som(v * (100 + a) // 100)}.", f"{som(v * (100 + a) // 100)} · {100 - a}/100 = {som(k)}.", "Boshlang‘ich narxga teng emas!"], noto=[v, v + a * 10, v - a * 10])


@sh("pm_foizqayta", "yopiq")
def pm_fq_3(rng):
    s = rng.choice([1_000_000, 2_000_000, 5_000_000, 10_000_000]); p = rng.choice([10, 20]); n = rng.choice([2, 3])
    k = s * (100 + p) ** n // 100 ** n
    return _y(rng, f"Bankka {som(s)} so‘m qo‘yildi, yillik {p}% (murakkab foiz). {n} yildan keyin summa qancha bo‘ladi?", k, [f"{som(s)} · (1,{p // 10 if p == 10 else 2})^{n} = {som(k)}."],
              noto=[s + s * p * n // 100, s * (100 + p * n) // 100 + 1000, k + s // 10])


@sh("pm_foizqayta", "yopiq")
def pm_fq_4(rng):
    a = rng.choice([50, 80, 120, 200, 250]); p = rng.choice([20, 25, 40])
    k = a * (100 - p) // 100
    return _y(rng, f"Telefon batareyasi {a} soat ishlardi. Yangi dasturdan keyin ishlash vaqti {p}% ga qisqardi. Endi necha soat ishlaydi?", k, [f"{a} · {100 - p}/100 = {k} soat."], noto=[a - p, a + a * p // 100, a * p // 100])


@sh("pm_foizqayta", "ochiq")
def pm_fq_5(rng):
    o = rng.choice([20, 25, 30, 40]); a = rng.choice(range(100, 500, 20)) * 1000
    y1 = a * (100 + o) // 100; y2 = y1 * (100 - o) // 100
    return _o(f"Uy narxi bir yilda {o}% oshdi, keyingi yilda {o}% tushdi. Boshida {som(a)} so‘m edi.", [("a) 1-yildan keyin narx (so‘m):", y1), ("b) 2-yildan keyin narx (so‘m):", y2)],
              [f"a) {som(a)} · {100 + o}/100 = {som(y1)}.", f"b) {som(y1)} · {100 - o}/100 = {som(y2)}.", "Boshlang‘ichdan past!"])


@sh("pm_foizqayta", "ochiq")
def pm_fq_6(rng):
    S = rng.choice([2_000_000, 4_000_000, 5_000_000]); r = rng.choice([10, 20]); y1 = S * (100 + r) // 100; y2 = y1 * (100 + r) // 100
    return _o(f"{som(S)} so‘m yillik {r}% murakkab foiz bilan omonatga qo‘yildi.", [("a) 1 yildan keyin (so‘m):", y1), ("b) 2 yildan keyin (so‘m):", y2)],
              [f"a) {som(S)} · {100 + r}/100 = {som(y1)}.", f"b) {som(y1)} · {100 + r}/100 = {som(y2)}.", f"Oddiy foizda {som(S + S * r * 2 // 100)} bo‘lardi — murakkabda ko‘proq."])


@sh("pm_foizqayta", "ochiq")
def pm_fq_7(rng):
    a = rng.choice([40, 50, 60, 80]); b = rng.choice([a + 10, a + 20, a + 30])
    return _o(f"Maktab kutubxonasida {a} ta kitob bor edi, keyin {b} ta bo‘ldi.", [("a) Necha foizga oshgan? (1 xona aniqlikda)", Fraction(str(round((b - a) * 100 / a, 1)))), ("b) Yana shuncha foiz oshsa (yangi sondan), nechta kitob bo‘ladi? (1 xona aniqlikda)", Fraction(str(round(b * (100 + (b - a) * 100 / a) / 100, 1))))],
              [f"a) ({b} − {a}) / {a} · 100 = {(b - a) * 100 / a:.1f}%.", f"b) {b} · {1 + (b - a) / a:.3f} ≈ {round(b * (1 + (b - a) / a), 1)}."])


tema("pm_ulush", "PM-2", "Ulush va foiz diagrammasi", "🥧", "Doira diagrammasi, sektor burchagi, qism va butun orasidagi bog‘lanish", [
    ("Qism va butun", "Qism = Butun · ulush\nUlush = Qism / Butun\nFoiz = ulush · 100%",
     "Har qanday masalada uchta miqdor bor: butun, qism va ulush. Birortasi noma’lum bo‘lsa, qolgan ikkitasidan topamiz. Ulushni foizga aylantirish uchun yuzga ko‘paytiramiz."),
    ("Doira diagrammasi", "Butun doira = 360°\n1% = 3,6°\nSektor burchagi = foiz · 3,6°",
     "Doira diagrammasida butun doira uch yuz oltmish daraja. Bir foiz uch butun olti o‘ndan daraja. Sektor burchagini topish uchun foizni uch butun oltiga ko‘paytiramiz."),
    ("Diagrammadan o‘qish", "Burchak 90° → 25%\nBurchak 180° → 50%\nQism = foiz · jami / 100",
     "Burchak to‘qson daraja bo‘lsa, bu doiraning to‘rtdan biri, ya’ni yigirma besh foiz. Yuz sakson daraja — yarmi. Diagrammadagi foizni jami miqdorga ko‘paytirib, haqiqiy sonni topamiz."),
])


@sh("pm_ulush", "yopiq")
def pm_ul_1(rng):
    n = rng.choice([200, 300, 400, 500, 600, 800]); p = rng.choice([10, 15, 20, 25, 30, 35, 40])
    return _y(rng, f"Maktabda {n} ta o‘quvchi bor. Ularning {p}% i sport to‘garagiga qatnashadi. Nechta o‘quvchi qatnashadi?", n * p // 100, [f"{n} · {p}/100 = {n * p // 100}."], noto=[n - n * p // 100, n * p // 10, p])


@sh("pm_ulush", "yopiq")
def pm_ul_2(rng):
    p = rng.choice([10, 20, 25, 30, 40, 50, 5, 15]); a = p * 36 // 10 if (p * 36) % 10 == 0 else None
    if a is None:
        p = 20; a = 72
    return _y(rng, f"Doira diagrammasida bir sektor butunning {p}% ini ko‘rsatadi. Sektor burchagi necha gradus?", a, [f"1% = 3,6°; {p} · 3,6 = {a}°."], noto=[p * 3, p * 4, a + 18])


@sh("pm_ulush", "yopiq")
def pm_ul_3(rng):
    a = rng.choice([45, 72, 90, 108, 120, 144, 180]); p = round(a / 3.6, 1); p = int(p) if p == int(p) else p
    return _y(rng, f"Doira diagrammasida sektor burchagi {a}°. Bu butunning necha foizi?", p, [f"{a} : 3,6 = {num(Fraction(a * 10, 36))}%."], noto=[a // 2, a // 3, round(a / 2.5)])


@sh("pm_ulush", "yopiq")
def pm_ul_4(rng):
    jami = rng.choice([400, 500, 600, 800, 1000, 1200]); a = rng.choice([90, 120, 72, 180, 60])
    x = jami * a // 360 if (jami * a) % 360 == 0 else None
    if x is None:
        jami, a, x = 720, 90, 180
    return _y(rng, f"Diagrammada jami {jami} ta ovoz berildi. Bir nomzodning sektori {a}°. U nechta ovoz oldi?", x, [f"{a}/360 · {jami} = {x}."], noto=[jami * a // 100 if (jami * a) % 100 == 0 else x + 20, a, x * 2])


@sh("pm_ulush", "ochiq")
def pm_ul_5(rng):
    n = rng.choice([200, 400, 600, 800]); k = [rng.choice([10, 15, 20, 25]) for _ in range(2)]; r = 100 - sum(k)
    return _o(f"{n} ta o‘quvchi sevimli faniga ovoz berdi: matematika {k[0]}%, tarix {k[1]}%, qolganlari boshqa fanlar.", [("a) Boshqa fanlarga necha foiz ovoz berildi?", r), ("b) Boshqa fanlarni tanlaganlar soni:", n * r // 100)],
              [f"a) 100 − {k[0]} − {k[1]} = {r}%.", f"b) {n} · {r}/100 = {n * r // 100}."])


@sh("pm_ulush", "ochiq")
def pm_ul_6(rng):
    p = [rng.choice([20, 25, 30]), rng.choice([15, 20, 25])]; r = 100 - sum(p)
    return _o(f"Doira diagrammasida mevalar: olma {p[0]}%, nok {p[1]}%, qolgani uzum.", [("a) Uzum sektori burchagi (°):", int(r * 3.6)), ("b) Olma sektori burchagi (°):", int(p[0] * 3.6))],
              [f"a) {r}% · 3,6 = {int(r * 3.6)}°.", f"b) {p[0]} · 3,6 = {int(p[0] * 3.6)}°."])


@sh("pm_ulush", "ochiq")
def pm_ul_7(rng):
    q = rng.choice([30, 45, 60, 75]); p = rng.choice([10, 15, 20, 25, 30]); jami = q * 100 // p if (q * 100) % p == 0 else 300
    if jami == 300: q, p = 60, 20; jami = 300
    return _o(f"Sinfda {q} ta o‘quvchi {p}% ni tashkil qiladigan guruhga kiradi.", [("a) Butun sinfda nechta o‘quvchi bor?", jami), ("b) Qolganlar nechta?", jami - q)],
              [f"a) {q} : {p}% = {q} · 100 / {p} = {jami}.", f"b) {jami} − {q} = {jami - q}."])


# ═════════ 3-BO'LIM · NISBAT ═════════
tema("pm_proporsiya", "PM-3", "To‘g‘ri va teskari proporsionallik", "↔️", "Ish haqi, narx, ishchi va kun: proporsional bog‘lanishni tanib yechish", [
    ("To‘g‘ri proporsionallik", "y/x = o‘zgarmas\n3 kg — 24 000 → 5 kg — 40 000\nBir birlik narxi = 8 000",
     "Bir miqdor necha marta ko‘paysa, ikkinchisi ham shuncha marta ko‘payadi — bu to‘g‘ri proporsionallik. Uch kilogramm yigirma to‘rt ming bo‘lsa, bir kilogramm sakkiz ming. Besh kilogramm — qirq ming."),
    ("Teskari proporsionallik", "x · y = o‘zgarmas\n6 ishchi — 10 kun → 12 ishchi — 5 kun\nIshchi ↑ ⇒ kun ↓",
     "Bir miqdor ko‘paysa, ikkinchisi shuncha marta kamaysa — teskari proporsionallik. Olti ishchi ishni o‘n kunda bitirsa, o‘n ikki ishchi besh kunda bitiradi. Ko‘paytma o‘zgarmaydi."),
    ("Qaysi turini aniqlash", "Savol: ko‘p → ko‘p? To‘g‘ri\nSavol: ko‘p → kam? Teskari\nBirlik usuli: avval 1 ga keltir",
     "Masalani o‘qib, bir miqdor ortganda ikkinchisi ham ortishini yoki kamayishini aniqlang. Ortsa — to‘g‘ri, kamaysa — teskari. Eng ishonchli usul — avval bir birlikka keltirish."),
])


@sh("pm_proporsiya", "yopiq")
def pm_pr_1(rng):
    k = rng.choice([3, 4, 5]); p = rng.choice(range(6, 20)) * 1000; n = rng.randint(6, 12)
    return _y(rng, f"{k} kg olma {som(p * k)} so‘m. {n} kg olma necha so‘m?", p * n, [f"1 kg = {som(p)}; {n} kg = {som(p * n)}."], noto=[p * n + p, p * (n - 1), p * k + n])


@sh("pm_proporsiya", "yopiq")
def pm_pr_2(rng):
    ish, kun = rng.choice([(4, 12), (6, 10), (8, 15), (3, 20), (5, 24)]); y = rng.choice([2, 3, 4, 6, 10, 12])
    if (ish * kun) % y: y = ish * 2
    return _y(rng, f"{ish} ishchi ishni {kun} kunda tugatadi. {y} ishchi shu ishni necha kunda tugatadi?", ish * kun // y, [f"Ish hajmi: {ish} · {kun} = {ish * kun} ishchi-kun.", f"{ish * kun} : {y} = {ish * kun // y} kun."], noto=[kun * y // ish if (kun * y) % ish == 0 else kun + y, kun + y, ish * kun])


@sh("pm_proporsiya", "yopiq")
def pm_pr_3(rng):
    v = rng.choice([40, 60, 80, 90, 120]); t = rng.choice([2, 3, 4, 5]); t2 = rng.choice([x for x in [1, 2, 3, 4, 5, 6, 8, 10, 12] if (v * t) % x == 0 and x != t])
    return _y(rng, f"Mashina {v} km/soat tezlik bilan {t} soatda yetib boradi. Tezlik {v * t // t2} km/soat bo‘lsa, necha soatda yetadi?", t2, [f"Masofa = {v} · {t} = {v * t} km.", f"Vaqt = {v * t} : {v * t // t2} = {t2} soat."], noto=[t + 1, t * 2, t2 + 1])


@sh("pm_proporsiya", "yopiq")
def pm_pr_4(rng):
    return _y(rng, rng.choice(["Qaysi bog‘lanish teskari proporsionallik?", "Quyidagilardan qaysi biri teskari proporsionallikka misol?"]), "Ishchilar soni ko‘paysa, ish kamroq kunda bitadi",
              ["Bir miqdor ortganda ikkinchisi kamayadi va ko‘paytma o‘zgarmaydi."], noto=["Kg ko‘paysa, narx ko‘payadi", "Soat o‘tsa, masofa ortadi", "Ko‘p kitob — ko‘p sahifa"])


@sh("pm_proporsiya", "ochiq")
def pm_pr_5(rng):
    a = rng.choice([12, 15, 18, 20]); m = rng.choice([48, 60, 72, 96]); k = rng.choice([3, 4, 5, 6])
    return _o(f"{a} soatda {a * k} ta detal tayyorlanadi.", [("a) 1 soatda nechta detal?", k), (f"b) {m} soatda nechta detal?", k * m)], [f"a) {a * k} : {a} = {k}.", f"b) {k} · {m} = {k * m}."])


@sh("pm_proporsiya", "ochiq")
def pm_pr_6(rng):
    ish = rng.choice([(6, 8), (4, 12), (8, 6), (10, 12)]); yangi = ish[0] * rng.choice([2, 3])
    return _o(f"{ish[0]} nafar quruvchi devorni {ish[1]} kunda quradi.", [(f"a) Ish hajmi (ishchi-kun):", ish[0] * ish[1]), (f"b) {yangi} nafar quruvchi necha kunda quradi?", ish[0] * ish[1] // yangi)],
              [f"a) {ish[0]} · {ish[1]} = {ish[0] * ish[1]}.", f"b) {ish[0] * ish[1]} : {yangi} = {ish[0] * ish[1] // yangi}."])


@sh("pm_proporsiya", "ochiq")
def pm_pr_7(rng):
    L_ = rng.choice([2, 4, 5, 10]); w = rng.choice([30, 45, 60]); d = L_ * rng.choice([3, 4, 5])
    return _o(f"{L_} litr benzin {L_ * w * 100 // 100 * 10} so‘m emas, balki bir litr {w * 100} so‘m turadi.", [(f"a) {L_} litr benzin narxi (so‘m):", L_ * w * 100), (f"b) {som(d * w * 100)} so‘mga necha litr olinadi?", d)],
              [f"a) {L_} · {som(w * 100)} = {som(L_ * w * 100)}.", f"b) {som(d * w * 100)} : {som(w * 100)} = {d}."])


tema("pm_aralashma", "PM-3", "Aralashma, eritma va konsentratsiya", "🧪", "Sharbat, qotishma va tuzli eritma: foiz konsentratsiyani hisoblash", [
    ("Konsentratsiya", "Konsentratsiya % = modda / eritma · 100\nModda = eritma · %/100\nEritma = modda + suv",
     "Eritmadagi modda ulushi konsentratsiya deyiladi. Uni topish uchun modda massasini butun eritma massasiga bo‘lib, yuzga ko‘paytiramiz. Eritma massasi modda va suv massalari yig‘indisiga teng."),
    ("Suyultirish", "Modda o‘zgarmaydi!\n200 g 10% → 20 g tuz\n+200 g suv → 20/400 = 5%",
     "Suv qo‘shsak, modda miqdori o‘zgarmaydi, faqat eritma massasi oshadi. Shuning uchun konsentratsiya kamayadi. Yangi konsentratsiyani modda massasini yangi eritma massasiga bo‘lib topamiz."),
    ("Aralashtirish", "Jami modda = m₁ + m₂\nJami massa = M₁ + M₂\nYangi % = jami modda / jami massa",
     "Ikki eritmani aralashtirsak, moddalar ham, massalar ham qo‘shiladi. Yangi konsentratsiya jami modda massasining jami massaga nisbati."),
])


@sh("pm_aralashma", "yopiq")
def pm_ar_1(rng):
    M = rng.choice([200, 250, 400, 500, 800]); p = rng.choice([5, 10, 15, 20, 25])
    return _y(rng, f"{M} g tuzli eritmada {p}% tuz bor. Eritmada necha gramm tuz bor?", M * p // 100, [f"{M} · {p}/100 = {M * p // 100} g."], noto=[M - M * p // 100, p, M * p // 10])


@sh("pm_aralashma", "yopiq")
def pm_ar_2(rng):
    t = rng.choice([20, 30, 40, 50, 60]); M = rng.choice([200, 250, 400, 500, 600])
    while (t * 100) % M: M = rng.choice([200, 250, 400, 500, 600]); t = rng.choice([20, 30, 40, 50, 60, 80, 100])
    return _y(rng, f"{M} g eritmada {t} g shakar bor. Konsentratsiya necha foiz?", t * 100 // M, [f"{t}/{M} · 100 = {t * 100 // M}%."], noto=[t, M - t, t * 100 // M + 5])


@sh("pm_aralashma", "yopiq")
def pm_ar_3(rng):
    M = rng.choice([100, 200, 300, 400]); p = rng.choice([10, 20, 30, 40]); mod = M * p // 100; qosh = M * rng.choice([1, 2, 3]) // 1
    yangi = mod * 100 // (M + qosh)
    if (mod * 100) % (M + qosh): qosh = M; yangi = mod * 100 // (M + qosh) if (mod * 100) % (M + qosh) == 0 else p // 2
    return _y(rng, f"{M} g {p}% li eritmaga {qosh} g suv qo‘shildi. Yangi konsentratsiya necha foiz?", round(mod * 100 / (M + qosh), 1), [f"Modda: {mod} g (o‘zgarmaydi).", f"Yangi massa: {M} + {qosh} = {M + qosh} g.", f"{mod}/{M + qosh} · 100 = {round(mod * 100 / (M + qosh), 1)}%."],
              noto=[p, p // 2 if p % 2 == 0 else p - 3, round(mod * 100 / M, 1) + 5])


@sh("pm_aralashma", "yopiq")
def pm_ar_4(rng):
    a, b = rng.choice([(100, 10), (200, 20), (300, 30)]); c, d = rng.choice([(100, 30), (200, 40), (300, 50)])
    jami = a * b / 100 + c * d / 100; y = round(jami * 100 / (a + c), 1)
    return _y(rng, f"{a} g {b}% li va {c} g {d}% li eritma aralashtirildi. Yangi eritma konsentratsiyasi necha foiz?", y, [f"Modda: {a * b / 100:g} + {c * d / 100:g} = {jami:g} g.", f"Massa: {a} + {c} = {a + c} g.", f"{jami:g}/{a + c} · 100 = {y}%."], noto=[round((b + d) / 2 + 3, 1), b + d, y + 5])


@sh("pm_aralashma", "ochiq")
def pm_ar_5(rng):
    M = rng.choice([400, 500, 800]); p = rng.choice([10, 20, 25]); mod = M * p // 100
    return _o(f"{M} g sharbatda {p}% shakar bor.", [("a) Shakar massasi (g):", mod), ("b) Suv massasi (g):", M - mod)], [f"a) {M} · {p}/100 = {mod} g.", f"b) {M} − {mod} = {M - mod} g."])


@sh("pm_aralashma", "ochiq")
def pm_ar_6(rng):
    M = rng.choice([200, 400, 600]); p = rng.choice([10, 20, 30]); q = rng.choice([5, 10, 15]) if False else p // 2
    mod = M * p // 100; yangi_M = mod * 100 // q
    return _o(f"{M} g {p}% li eritmani {q}% li qilish uchun suv qo‘shiladi.", [("a) Eritmadagi modda (g):", mod), ("b) Qancha suv qo‘shish kerak (g)?", yangi_M - M)],
              [f"a) {M} · {p}/100 = {mod} g.", f"b) Yangi massa {mod} · 100 / {q} = {yangi_M} g; suv: {yangi_M} − {M} = {yangi_M - M} g."])


@sh("pm_aralashma", "ochiq")
def pm_ar_7(rng):
    a = rng.choice([2, 3, 4]); b = rng.choice([1, 2, 3]); V = (a + b) * rng.choice([20, 30, 40])
    return _o(f"Sharbat va suv {a}:{b} nisbatda aralashtirilib, jami {V} litr ichimlik tayyorlandi.", [("a) Sharbat necha litr?", V * a // (a + b)), ("b) Suv necha litr?", V * b // (a + b))],
              [f"a) {V} : {a + b} · {a} = {V * a // (a + b)}.", f"b) {V} : {a + b} · {b} = {V * b // (a + b)}."])


# ═════════ 4-BO'LIM · BIRLIKLAR VA O'LCHOVLAR ═════════
tema("pm_birlik", "PM-4", "Uzunlik, massa va hajm birliklari", "📏", "km–m–sm, t–kg–g, l–ml: birliklarni almashtirish va ularni birgalikda ishlatish", [
    ("Asosiy munosabatlar", "1 km = 1000 m; 1 m = 100 sm\n1 t = 1000 kg; 1 kg = 1000 g\n1 l = 1000 ml; 1 m³ = 1000 l",
     "Eng kerakli munosabatlarni yodlab oling: bir kilometr ming metr, bir metr yuz santimetr, bir tonna ming kilogramm, bir kilogramm ming gramm, bir litr ming millilitr."),
    ("Almashtirish usuli", "Katta → kichik: KO‘PAYTIR\nKichik → katta: BO‘L\n3,5 km = 3,5 · 1000 = 3500 m",
     "Katta birlikdan kichigiga o‘tganda sonni ko‘paytiramiz, chunki bo‘laklar ko‘p chiqadi. Kichikdan kattasiga o‘tganda bo‘lamiz. Uch butun besh o‘n kilometr — uch ming besh yuz metr."),
    ("Qo‘shma birliklar", "Retsept: 250 ml · 4 = 1000 ml = 1 l\nBoshlang‘ich va oxirgi birliklar bir xil bo‘lsin",
     "Masalada turli birliklar uchrasa, hammasini bir birlikka keltirib yechamiz. Javobni so‘ralgan birlikda yozishni unutmang."),
])


@sh("pm_birlik", "yopiq")
def pm_bi_1(rng):
    k = rng.choice([1.5, 2.4, 3.25, 0.8, 4.2, 12.5]); m = int(k * 1000)
    return _y(rng, f"{num(Fraction(str(k)))} km necha metr?", m, [f"{num(Fraction(str(k)))} · 1000 = {m} m."], noto=[int(k * 100), int(k * 10000), int(k * 10)])


@sh("pm_birlik", "yopiq")
def pm_bi_2(rng):
    g = rng.choice([250, 375, 1200, 4500, 7500, 600]); 
    return _y(rng, f"{som(g)} g necha kilogramm?", Fraction(g, 1000), [f"{som(g)} : 1000 = {num(Fraction(g, 1000))} kg."], noto=[Fraction(g, 100), Fraction(g, 10), g * 1000 // 100])


@sh("pm_birlik", "yopiq")
def pm_bi_3(rng):
    n = rng.choice([250, 200, 150, 125, 330]); k = rng.choice([4, 5, 6, 8, 12])
    return _y(rng, f"Bir stakanga {n} ml sharbat sig‘adi. {k} ta stakan necha litr bo‘ladi?", Fraction(n * k, 1000), [f"{n} · {k} = {n * k} ml = {num(Fraction(n * k, 1000))} l."], noto=[Fraction(n * k, 100), n * k, Fraction(n * k, 10000)])


@sh("pm_birlik", "yopiq")
def pm_bi_4(rng):
    a = rng.choice([2, 3, 4, 5]); b = rng.choice([150, 250, 350, 450, 750]); c = rng.choice([3, 4, 5])
    return _y(rng, f"{a} m {b} sm ni {c} marta ko‘paytiring va metrda ifodalang.", Fraction((a * 100 + b) * c, 100), [f"{a} m {b} sm = {a * 100 + b} sm; · {c} = {(a * 100 + b) * c} sm = {num(Fraction((a * 100 + b) * c, 100))} m."], noto=[Fraction((a * 100 + b) * c, 10), (a + b) * c, Fraction((a * 100 + b) * c, 1000)])


@sh("pm_birlik", "ochiq")
def pm_bi_5(rng):
    n = rng.choice([8, 12, 15, 20]); kg = rng.choice([250, 300, 450, 500])
    return _o(f"Do‘konga {n} ta quti keltirildi, har birining massasi {kg} g.", [("a) Jami massa (kg):", Fraction(n * kg, 1000)), ("b) Jami massa (g):", n * kg)], [f"a) {n} · {kg} = {n * kg} g = {num(Fraction(n * kg, 1000))} kg.", f"b) {n * kg} g."])


@sh("pm_birlik", "ochiq")
def pm_bi_6(rng):
    L_ = rng.choice([3, 4, 5, 6]); w = rng.choice([40, 50, 60, 80]); 
    return _o(f"Xona uzunligi {L_} m, kengligi {w} dm.", [("a) Kenglik metrda:", Fraction(w, 10)), ("b) Perimetr (m):", 2 * (L_ + Fraction(w, 10)))], [f"a) {w} dm = {num(Fraction(w, 10))} m.", f"b) 2 · ({L_} + {num(Fraction(w, 10))}) = {num(2 * (L_ + Fraction(w, 10)))} m."])


@sh("pm_birlik", "ochiq")
def pm_bi_7(rng):
    t = rng.choice([2, 3, 5]); kg = rng.choice([250, 400, 500, 750])
    return _o(f"Fermer {t} t bug‘doy yetishtirdi va uni {kg} kg li qoplarga solmoqda.", [(f"a) {t} t necha kg?", t * 1000), ("b) Nechta qop kerak?", t * 1000 // kg if (t * 1000) % kg == 0 else -(-t * 1000 // kg))],
              [f"a) {t} · 1000 = {t * 1000} kg.", f"b) {t * 1000} : {kg} = {t * 1000 / kg:g} → {-(-t * 1000 // kg)} qop."])


tema("pm_vaqt", "PM-4", "Vaqt, jadval va kalendar", "⏰", "Soat/daqiqa hisobi, jadval bo‘yicha yo‘l vaqti, vaqt mintaqalari va kalendar", [
    ("Vaqt birliklari", "1 soat = 60 daqiqa = 3600 s\n1 sutka = 24 soat\nVaqt farqi = oxiri − boshi",
     "Bir soat oltmish daqiqa, bir daqiqa oltmish soniya. Vaqt oralig‘ini topish uchun tugash vaqtidan boshlanish vaqtini ayiramiz. Soat va daqiqalarni alohida hisoblab, so‘ng birlashtiramiz."),
    ("Jadval bo‘yicha", "Jo‘nash 08:45, yetish 11:20\n11:20 − 08:45 = 2 soat 35 daqiqa\nKutish vaqtini qo‘shing",
     "Poyezd yoki avtobus jadvalida jo‘nash va yetib borish vaqti beriladi. Yo‘lda bo‘lgan vaqt — ularning farqi. Agar peresadka bo‘lsa, kutish vaqti ham jami vaqtga kiradi."),
    ("Vaqt mintaqalari", "Toshkent = UTC+5\nLondon = UTC+0 (qishda)\nFarq 5 soat: Toshkentda 15:00 → Londonda 10:00",
     "Dunyoda soat mintaqalari bor. Sharqroqdagi shaharda soat oldinroq. Toshkent Londondan besh soat oldinda: Toshkentda uch bo‘lsa, Londonda o‘n."),
])


@sh("pm_vaqt", "yopiq")
def pm_va_1(rng):
    h1 = rng.randint(6, 11); m1 = rng.choice([5, 15, 25, 40, 50]); h2 = h1 + rng.randint(2, 5); m2 = rng.choice([10, 20, 35, 45, 55])
    t = (h2 * 60 + m2) - (h1 * 60 + m1); hh, mm_ = divmod(t, 60)
    return _y(rng, f"Poyezd {h1:02d}:{m1:02d} da jo‘nab, {h2:02d}:{m2:02d} da yetib keldi. Yo‘lda necha daqiqa bo‘ldi?", t, [f"({h2}·60+{m2}) − ({h1}·60+{m1}) = {t} daqiqa = {hh} soat {mm_} daqiqa."], noto=[t + 60, t - 40, (h2 - h1) * 60])


@sh("pm_vaqt", "yopiq")
def pm_va_2(rng):
    h = rng.randint(8, 17); m = rng.choice([10, 20, 30, 45]); f = rng.choice([2, 3, 4, 5]); sh_ = rng.choice([("London", 5), ("Moskva", 2), ("Dubay", 1), ("Istanbul", 2)])
    return _y(rng, f"Toshkentda soat {h:02d}:{m:02d}. {sh_[0]} Toshkentdan {sh_[1]} soat orqada. {sh_[0]}da soat nechchi?", f"{h - sh_[1]:02d}:{m:02d}", [f"{h}:{m:02d} − {sh_[1]} soat = {h - sh_[1]:02d}:{m:02d}."],
              noto=[f"{h + sh_[1]:02d}:{m:02d}", f"{h - sh_[1] + 1:02d}:{m:02d}", f"{h - sh_[1]:02d}:{(m + 30) % 60:02d}"])


@sh("pm_vaqt", "yopiq")
def pm_va_3(rng):
    k = rng.randint(100, 500); return _y(rng, f"{k} daqiqa necha soat va necha daqiqa?", f"{k // 60} soat {k % 60} daq", [f"{k} : 60 = {k // 60} (qoldiq {k % 60}) → {k // 60} soat {k % 60} daqiqa."],
                                         noto=[f"{k // 60 + 1} soat {k % 60} daq", f"{k // 60} soat {(60 - k % 60) % 60 + 1} daq", f"{k // 100 + 3} soat {k % 100} daq", f"{k // 60 + 2} soat {k % 60} daq", f"{k // 60 - 1} soat {k % 60} daq", f"{k // 60} soat {(k % 60 + 7) % 60} daq"])


@sh("pm_vaqt", "yopiq")
def pm_va_4(rng):
    d = rng.choice([("2024", 29), ("2025", 28), ("2026", 28), ("2028", 29)]); a = rng.randint(1, 10)
    return _y(rng, f"{d[0]}-yil fevral oyida necha kun bor?", d[1], ["Kabisa yil 4 ga bo‘linadi (2024, 2028) — fevralda 29 kun; boshqalarda 28 kun."], noto=[28 if d[1] == 29 else 29, 30, 31])


@sh("pm_vaqt", "ochiq")
def pm_va_5(rng):
    h = rng.randint(7, 9); m = rng.choice([0, 15, 30, 45]); d1 = rng.choice([35, 50, 65, 80]); kut = rng.choice([15, 20, 25, 40]); d2 = rng.choice([40, 55, 70])
    tot = d1 + kut + d2; yet = h * 60 + m + tot
    return _o(f"Siz {h:02d}:{m:02d} da yo‘lga chiqdingiz. Birinchi avtobus {d1} daqiqa yurdi, peresadkada {kut} daqiqa kutdingiz, ikkinchisi yana {d2} daqiqa yurdi.", [("a) Umumiy vaqt (daqiqa):", tot), ("b) Yetib borgan vaqtning soat qismi (daqiqa qismi: {0}):".format(yet % 60), yet // 60)],
              [f"a) {d1} + {kut} + {d2} = {tot}.", f"b) {h:02d}:{m:02d} + {tot} daq = {yet // 60:02d}:{yet % 60:02d} → soat {yet // 60}."])


@sh("pm_vaqt", "ochiq")
def pm_va_6(rng):
    s = rng.randint(2, 6); d = rng.choice([30, 40, 50]); n = rng.choice([4, 5, 6])
    return _o(f"Maktab darslari: har dars {d} daqiqa, tanaffus 10 daqiqa. Bugun {n} ta dars bor.", [("a) Darslar jami necha daqiqa?", d * n), ("b) Tanaffuslar bilan birga (oxirgi dars keyin tanaffus yo‘q), jami daqiqa:", d * n + 10 * (n - 1))],
              [f"a) {d} · {n} = {d * n}.", f"b) {d * n} + 10 · {n - 1} = {d * n + 10 * (n - 1)}."])


@sh("pm_vaqt", "ochiq")
def pm_va_7(rng):
    b = rng.choice([(9, 30), (12, 0), (14, 45)]); mp = rng.choice([("Moskva", 2), ("London", 5), ("Seul", -4), ("Dubay", 1)])
    h = b[0] - mp[1]
    return _o(f"Toshkentda uchrashuv soat {b[0]:02d}:{b[1]:02d} da. {mp[0]} Toshkentdan {abs(mp[1])} soat {'orqada' if mp[1] > 0 else 'oldinda'}.", [(f"a) {mp[0]}da soat nechchi (soat qismi, 24 soatlik)?", h % 24), ("b) Daqiqa qismi:", b[1])],
              [f"a) {b[0]} {'−' if mp[1] > 0 else '+'} {abs(mp[1])} = {h % 24}.", f"b) Daqiqa o‘zgarmaydi: {b[1]}."])


# ═════════ 5-BO'LIM · ALGEBRA ═════════
tema("pm_ifoda", "PM-5", "Harfli ifoda va formula", "🔤", "Formulaga qiymat qo‘yish, ifodani soddalashtirish, hayotiy formulalar (yuza, harorat, narx)", [
    ("Harfli ifoda", "a, b, x — o‘zgaruvchilar\nP = 2(a + b)\nS = a · b",
     "Harflar o‘rniga sonlar qo‘yish mumkin. Perimetr formulasi: ikkiga ko‘paytirilgan tomonlar yig‘indisi. Formulaga sonlarni qo‘yib hisoblasak — ifodaning qiymati chiqadi."),
    ("Soddalashtirish", "3x + 5x = 8x\n2(x + 4) = 2x + 8\nO‘xshash hadlarni qo‘shing",
     "O‘xshash hadlar — harfli qismi bir xil bo‘lgan hadlar. Ularni qo‘shamiz. Qavs oldidagi sonni qavs ichidagi har bir hadga ko‘paytiramiz."),
    ("Hayotiy formulalar", "F = 1,8·C + 32\nNarx = a · n + b\nQiymatni qo‘yib hisoblang",
     "Selsiy bilan Farengeyt orasidagi bog‘lanish — formula. Selsiydagi haroratni bir butun sakkiz o‘ngka ko‘paytirib, o‘ttiz ikkini qo‘shsak, Farengeyt chiqadi. Hayotda ko‘p formulalar shu tarzda ishlaydi."),
])


@sh("pm_ifoda", "yopiq")
def pm_if_1(rng):
    a = rng.randint(2, 15); b = rng.randint(2, 15)
    return _y(rng, f"Formula P = 2(a + b). a = {a}, b = {b} bo‘lsa, P nechaga teng?", 2 * (a + b), [f"P = 2 · ({a} + {b}) = {2 * (a + b)}."], noto=[a + b, 2 * a + b, a * b])


@sh("pm_ifoda", "yopiq")
def pm_if_2(rng):
    c = rng.choice([-10, 0, 10, 20, 25, 30, 35, 40]); f = c * 9 // 5 + 32 if (c * 9) % 5 == 0 else None
    if f is None: c = 25; f = 77
    return _y(rng, f"Formula F = 1,8·C + 32. C = {c}° bo‘lsa, F necha?", f, [f"F = 1,8 · {c} + 32 = {f}."], noto=[f + 10, c + 32, int(1.8 * c)])


@sh("pm_ifoda", "yopiq")
def pm_if_3(rng):
    a = rng.randint(2, 9); b = rng.randint(2, 9); c = rng.randint(1, 9)
    return _y(rng, f"Soddalashtiring: ${a}x + {b}x - {c}x$", f"${a + b - c}x$", [f"({a} + {b} − {c})x = {a + b - c}x."], noto=[f"${a + b + c}x$", f"${a * b - c + 20}x$", f"${a + b - c}$", f"${a + b - c + 3}x$"])


@sh("pm_ifoda", "yopiq")
def pm_if_4(rng):
    a = rng.randint(2, 9); b = rng.randint(2, 12)
    return _y(rng, f"Qavsni oching: ${a}(x + {b})$", f"${a}x + {a * b}$", [f"{a} · x + {a} · {b} = {a}x + {a * b}."], noto=[f"${a}x + {b}$", f"${a + 1}x + {a * b}$", f"${a}x + {a + b}$", f"${a}x + {a * b + 1}$", f"${a}x - {a * b}$"])


@sh("pm_ifoda", "ochiq")
def pm_if_5(rng):
    a = rng.choice([12, 15, 18, 20]); n = rng.randint(2, 9); b = rng.choice([5000, 8000, 10000])
    return _o(f"Taksi narxi (so‘m): N = {som(a * 100)}·k + {som(b)}, bunda k — kilometr.", [("a) k = {0} da N:".format(n), a * 100 * n + b), ("b) k = {0} da N:".format(n + 3), a * 100 * (n + 3) + b)],
              [f"a) {som(a * 100)} · {n} + {som(b)} = {som(a * 100 * n + b)}.", f"b) {som(a * 100)} · {n + 3} + {som(b)} = {som(a * 100 * (n + 3) + b)}."])


@sh("pm_ifoda", "ochiq")
def pm_if_6(rng):
    a = rng.randint(3, 12); b = rng.randint(2, 9)
    return _o(f"To‘g‘ri to‘rtburchak tomonlari a = {a} sm va b = {b} sm. Formulalar: P = 2(a+b), S = a·b.", [("a) Perimetr (sm):", 2 * (a + b)), ("b) Yuza (sm²):", a * b)], [f"a) 2 · ({a} + {b}) = {2 * (a + b)}.", f"b) {a} · {b} = {a * b}."])


@sh("pm_ifoda", "ochiq")
def pm_if_7(rng):
    a = rng.randint(2, 7); b = rng.randint(2, 9); x = rng.randint(2, 6)
    return _o(f"Ifoda: {a}(x + {b}) − {a}x. x = {x} da qiymatini toping.", [("a) Soddalashtirilgan ko‘rinishdagi son:", a * b), ("b) x = {0} da qiymat:".format(x), a * b)], [f"a) {a}x + {a * b} − {a}x = {a * b}.", f"b) Ifoda x ga bog‘liq emas: {a * b}."])


tema("pm_tenglama", "PM-5", "Tenglama tuzish va yechish", "⚖️", "Masala shartidan tenglama tuzish; chiziqli tenglama; tekshirish", [
    ("Noma’lumni belgilash", "Noma’lum = x\nShartni tenglama qilib yozing\nx ni topish: teskari amal",
     "Masalada izlanayotgan sonni x deb belgilaymiz. Shartda aytilganlarni tenglik shaklida yozamiz. Keyin teskari amallar bilan x ni yolg‘iz qoldiramiz."),
    ("Teskari amallar", "x + 7 = 15 → x = 15 − 7\n3x = 21 → x = 21 : 3\nBoshqa tomonga o‘tganda ishora o‘zgaradi",
     "Qo‘shishning teskarisi — ayirish, ko‘paytirishning teskarisi — bo‘lish. Tenglikning ikkala tomoniga bir xil amal qilsak, tenglik buzilmaydi."),
    ("Tekshirish", "x = 8 → 3·8 + 4 = 28 ✓\nJavobni shartga qo‘ying",
     "Topilgan sonni tenglamaga qo‘yib tekshiramiz. Agar tenglik to‘g‘ri chiqsa — javob to‘g‘ri."),
])


@sh("pm_tenglama", "yopiq")
def pm_te_1(rng):
    a = rng.randint(2, 9); x = rng.randint(2, 15); b = rng.randint(1, 20)
    return _y(rng, f"Tenglamani yeching: ${a}x + {b} = {a * x + b}$. x = ?", x, [f"{a}x = {a * x + b} − {b} = {a * x}.", f"x = {a * x} : {a} = {x}."], noto=[x + 1, x - 1, a * x + b - a])


@sh("pm_tenglama", "yopiq")
def pm_te_2(rng):
    x = rng.randint(5, 25); k = rng.randint(2, 6)
    return _y(rng, f"Sonning {k} baravaridan 7 ni ayirsak, {k * x - 7} chiqadi. Shu son nechaga teng?", x, [f"{k}x − 7 = {k * x - 7} → {k}x = {k * x} → x = {x}."], noto=[x + 7, k * x, x - 1])


@sh("pm_tenglama", "yopiq")
def pm_te_3(rng):
    n = rng.randint(3, 8); p = rng.choice(range(3, 12)) * 1000; tot = n * p + rng.choice([5, 10, 15]) * 1000; d = tot - n * p
    return _y(rng, f"Bitta daftar {som(p)} so‘m. Daftarlar va {som(d)} so‘mlik qalam uchun jami {som(tot)} so‘m to‘landi. Nechta daftar olingan?", n, [f"{som(p)}·x + {som(d)} = {som(tot)} → x = {som(tot - d)} : {som(p)} = {n}."], noto=[n + 1, n - 1, n + 2])


@sh("pm_tenglama", "yopiq")
def pm_te_4(rng):
    x = rng.randint(4, 14); a = rng.randint(2, 5); b = rng.randint(1, 4)
    return _y(rng, f"Tenglamani yeching: ${a + b}x - {b}x = {a * x}$", x, [f"({a + b} − {b})x = {a}x = {a * x} → x = {x}."], noto=[a * x, x + b, x - 1])


@sh("pm_tenglama", "ochiq")
def pm_te_5(rng):
    x = rng.randint(8, 20); a = rng.randint(2, 4)
    return _o(f"Aka-uka yoshlari yig‘indisi {x + a * x}. Akasi ukasidan {a} marta katta.", [("a) Ukaning yoshi:", x), ("b) Akaning yoshi:", a * x)], [f"a) x + {a}x = {x + a * x} → {a + 1}x = {x + a * x} → x = {x}.", f"b) {a} · {x} = {a * x}."])


@sh("pm_tenglama", "ochiq")
def pm_te_6(rng):
    p = rng.choice([4, 5, 6, 8]); n = rng.randint(3, 9); f = rng.choice([10, 20, 30]) * 1000
    return _o(f"Dugonangiz uchun gul va {som(f)} so‘mlik sovg‘a oldingiz. Har bir gul {som(p * 1000)} so‘m, jami {som(p * 1000 * n + f)} so‘m to‘landi.", [("a) Gullar soni:", n), ("b) Gullarning umumiy narxi (so‘m):", p * 1000 * n)], [f"a) {som(p * 1000)}·x + {som(f)} = {som(p * 1000 * n + f)} → x = {n}.", f"b) {som(p * 1000)} · {n} = {som(p * 1000 * n)}."])


@sh("pm_tenglama", "ochiq")
def pm_te_7(rng):
    a = rng.randint(2, 7); b = rng.randint(1, 9); x = rng.randint(2, 15)
    return _o(f"Tenglama {a}x + {b} = {a * x + b} ning yechimini toping.", [("a) x ni toping:", x), ("b) 2x + 3 ning qiymati:", 2 * x + 3)], [f"a) {a}x = {a * x} → x = {x}.", f"b) 2 · {x} + 3 = {2 * x + 3}."])


tema("pm_tengsizlik", "PM-5", "Tengsizlik va chegaralar", "↕️", "Byudjet va chegara masalalari: eng ko‘pi bilan, kamida; tengsizlikni yechish", [
    ("Tengsizlik belgilari", "x > 5 — 5 dan katta\nx ≤ 8 — 8 dan oshmaydi\n'kamida' → ≥, 'ko‘pi bilan' → ≤",
     "Tengsizlik belgilari: katta, kichik, katta yoki teng, kichik yoki teng. 'Kamida' so‘zi — katta yoki teng, 'ko‘pi bilan' — kichik yoki teng deganidir."),
    ("Yechish", "2x + 3 ≤ 15 → 2x ≤ 12 → x ≤ 6\nManfiy songa ko‘paytirsak/bo‘lsak, belgi teskari!",
     "Tengsizlikni tenglamadek yechamiz. Faqat manfiy songa ko‘paytirganda yoki bo‘lganda belgi teskarisiga o‘zgaradi."),
    ("Butun yechimlar", "x ≤ 6, x natural → 1,2,3,4,5,6\nEng katta butun yechim: 6",
     "Hayotiy masalalarda javob ko‘pincha butun son bo‘ladi: nechta kitob olish mumkin, nechta kishi sig‘adi. Tengsizlikni yechib, butun yechimlardan eng kattasini olamiz."),
])


@sh("pm_tengsizlik", "yopiq")
def pm_tn_1(rng):
    byud = rng.choice(range(100, 400, 20)) * 1000; p = rng.choice([12, 15, 18, 20, 25]) * 1000
    return _y(rng, f"Hamyoningizda {som(byud)} so‘m bor. Bir kitob {som(p)} so‘m. Eng ko‘pi bilan nechta kitob olasiz?", byud // p, [f"{som(p)}·x ≤ {som(byud)} → x ≤ {byud / p:.2f} → eng ko‘pi {byud // p} ta."], noto=[byud // p + 1, byud // p - 1, -(-byud // p) + 1])


@sh("pm_tengsizlik", "yopiq")
def pm_tn_2(rng):
    a = rng.randint(2, 6); b = rng.randint(1, 9); c = a * rng.randint(3, 9) + b
    return _y(rng, f"Tengsizlikning eng katta butun yechimi: ${a}x + {b} \\le {c}$", (c - b) // a, [f"{a}x ≤ {c - b} → x ≤ {(c - b) / a:g} → eng katta butun: {(c - b) // a}."], noto=[(c - b) // a + 1, (c - b) // a - 1, c - b])


@sh("pm_tengsizlik", "yopiq")
def pm_tn_3(rng):
    m = rng.choice([30, 40, 45, 50]); k = rng.choice([32, 35, 36])
    return _y(rng, f"Liftga ko‘pi bilan {m * 10} kg yuk ko‘tarish mumkin. Har bir kishi o‘rtacha {m + 20} kg. Nechta kishi minsa bo‘ladi?", (m * 10) // (m + 20), [f"{m + 20}·x ≤ {m * 10} → x ≤ {(m * 10) / (m + 20):.2f} → {(m * 10) // (m + 20)} kishi."], noto=[(m * 10) // (m + 20) + 1, (m * 10) // (m + 20) - 1, m])


@sh("pm_tengsizlik", "yopiq")
def pm_tn_4(rng):
    k = rng.choice([4, 5, 6]); 
    return _y(rng, f"Qaysi tengsizlik ‘kamida {k} ball’ ni bildiradi?", f"$x \\ge {k}$", ["‘Kamida’ — katta yoki teng (≥)."], noto=[f"$x \\le {k}$", f"$x > {k}$", f"$x < {k}$"])


@sh("pm_tengsizlik", "ochiq")
def pm_tn_5(rng):
    ball = rng.choice([4, 5]); n = rng.choice([4, 5]); b = rng.choice([68, 70, 72, 75]); need = 80
    tot = need * (n + 1) - b * n
    return _o(f"{n} ta testdan o‘rtacha {b} ball oldingiz. Keyingi testdan oldingi o‘rtacha 80 dan kam bo‘lmasligi uchun kerakli minimal ball?", [("a) {0} ta testdagi jami ball:".format(n), b * n), ("b) Keyingi testda kamida necha ball kerak?", tot)],
              [f"a) {b} · {n} = {b * n}.", f"b) (x + {b * n}) / {n + 1} ≥ 80 → x ≥ {tot}."])


@sh("pm_tengsizlik", "ochiq")
def pm_tn_6(rng):
    p = rng.choice([8, 10, 12]) * 1000; f = rng.choice([30, 50, 70]) * 1000; byud = rng.choice([200, 250, 300]) * 1000
    n = (byud - f) // p
    return _o(f"Tug‘ilgan kunga {som(f)} so‘mlik tort va har biri {som(p)} so‘mlik sovg‘alar olinadi. Byudjet {som(byud)} so‘m.", [("a) Sovg‘alarga qolgan pul (so‘m):", byud - f), ("b) Eng ko‘pi bilan nechta sovg‘a olinadi?", n)], [f"a) {som(byud)} − {som(f)} = {som(byud - f)}.", f"b) {som(byud - f)} : {som(p)} = {(byud - f) / p:.2f} → {n}."])


@sh("pm_tengsizlik", "ochiq")
def pm_tn_7(rng):
    a = rng.randint(2, 5); b = rng.randint(3, 20); c = a * rng.randint(5, 12) + b
    n = (c - b) // a
    return _o(f"Tengsizlik: {a}x + {b} ≤ {c}, x — natural son.", [("a) x ning eng katta qiymati:", n), ("b) Nechta natural yechim bor?", n)], [f"a) {a}x ≤ {c - b} → x ≤ {(c - b) / a:g}. Eng katta: {n}.", f"b) 1 dan {n} gacha: {n} ta."])
