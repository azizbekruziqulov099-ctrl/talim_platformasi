"""TIMSS 4-sinf matematika — kengaytma: 12 yangi mavzu (har biri: dars + 6 generator → 30 mashq/30 test)."""
from fractions import Fraction

from modules.pisa_mat_g import reg, num, som, _y, _o, fig_stolbik

TOP = "T11_G4_M"
TEMA = {}


def tema(kod, nom, soha, belgi, maqsad, dars):
    TEMA[kod] = {"nom": nom, "soha": soha, "belgi": belgi, "maqsad": maqsad, "bolim": kod, "toplam": TOP,
                 "dars": [{"sarlavha": a, "doska": b, "ovoz": c} for a, b, c in dars]}


def Y(kod):
    return reg(kod, "yopiq")


def O(kod):
    return reg(kod, "ochiq")


# 1 ── xonalar va taqqoslash
tema("t4_xona", "Ko‘p xonali sonlar: o‘qish, taqqoslash, tartiblash", "Sonlar", "🔢", "10 000 gacha sonlarni xonalar bo‘yicha o‘qish, taqqoslash va tartiblash", [
    ("Xonalar", "4 285 = 4 ming + 2 yuz + 8 o‘n + 5 bir\nRaqamning qiymati o‘rniga bog‘liq",
     "To‘rt xonali sonda birinchi raqam mingliklarni, keyingisi yuzliklarni, so‘ng o‘nliklarni va birliklarni bildiradi. To‘rt ming ikki yuz sakson besh sonida ikkinchi raqam ikki yuzni ifodalaydi."),
    ("Taqqoslash", "Avval xonalar soni, keyin chapdan boshlab raqamlar\n4 285 > 4 192\n< > =",
     "Sonlarni taqqoslashda avval xonalar sonini solishtiring. Teng bo‘lsa, chapdan boshlab raqamlarni solishtiring: birinchi farq qiladigan raqam qaysi son kattaligini ko‘rsatadi."),
    ("Tartiblash", "Kichikdan kattaga: 1 905 < 2 034 < 2 340\nYaqin son: 4 285 ≈ 4 300",
     "Bir nechta sonni tartiblash uchun ularni juft-juft taqqoslang. Eng kichigidan boshlab yozib chiqing va oxirida tekshiring."),
])


@Y("t4_xona")
def _x1(rng):
    n = rng.randint(1000, 9999); k = rng.choice([1000, 100, 10, 1]); nom = {1000: "mingliklar", 100: "yuzliklar", 10: "o‘nliklar", 1: "birliklar"}[k]
    r = n // k % 10
    return _y(rng, f"{n} sonida {nom} xonasidagi raqam nechaga teng?", r, [f"{n} sonini xonalarga ajratamiz; {nom} xonasi: {r}."], noto=[(r + 1) % 10, (r + 3) % 10, (r + 5) % 10, n % 10 if n % 10 != r else (r + 7) % 10])


@Y("t4_xona")
def _x2(rng):
    a = rng.randint(1100, 9800); b = a + rng.choice([-1, 1]) * rng.choice([10, 100, 20, 200, 1000])
    return _y(rng, f"Qaysi son katta: {a} yoki {b}?", max(a, b), [f"Xonalarni chapdan taqqoslaymiz: katta son {max(a, b)}."], noto=[min(a, b), a + b, abs(a - b)])


@Y("t4_xona")
def _x3(rng):
    n = rng.randint(1000, 9999)
    return _y(rng, f"{n} soni 100 ga yaxlitlanganda nechaga teng bo‘ladi?", round(n / 100 + 1e-9) * 100 if n % 100 != 50 else n + 50,
              [f"Yuzlikdan keyingi raqamga qaraymiz: 50 va undan ko‘p bo‘lsa — yuqoriga, kam bo‘lsa — pastga."],
              noto=[n // 100 * 100 + (100 if n % 100 < 50 else 0) + (0 if n % 100 < 50 else 100), n // 10 * 10, n // 1000 * 1000 + 100])


@Y("t4_xona")
def _x4(rng):
    m, y, o, b = rng.randint(1, 9), rng.randint(0, 9), rng.randint(0, 9), rng.randint(1, 9)
    return _y(rng, f"{m} ming, {y} yuz, {o} o‘n va {b} birdan iborat son qaysi?", m * 1000 + y * 100 + o * 10 + b, [f"{m}000 + {y}00 + {o}0 + {b} = {m * 1000 + y * 100 + o * 10 + b}."],
              noto=[m * 1000 + y * 10 + o * 100 + b, m * 100 + y * 10 + o + b, m * 1000 + o * 100 + y * 10 + b + 1])


@O("t4_xona")
def _x5(rng):
    a = rng.randint(1100, 4999); b = a + rng.randint(1, 9) * 100; c = b + rng.randint(1, 9) * 10
    return _o(f"Uch son berilgan: {c}; {a}; {b}.", [("a) Eng kichik son:", a), ("b) Eng katta son:", c)], [f"a) Eng kichigi {a}.", f"b) Eng kattasi {c}."])


@O("t4_xona")
def _x6(rng):
    n = rng.randint(2000, 8999); d = rng.choice([10, 100, 1000])
    return _o(f"{n} sonidan {d} ta ko‘p va {d} ta kam sonlarni toping.", [(f"a) {n} + {d} =", n + d), (f"b) {n} − {d} =", n - d)], [f"a) {n} + {d} = {n + d}.", f"b) {n} − {d} = {n - d}."])


# 2 ── ustunli qo'shish va ayirish
tema("t4_ustun", "Ko‘p xonali qo‘shish va ayirish", "Sonlar", "➕", "To‘rt xonali sonlarni qo‘shish va ayirish, masalalarni tekshirish", [
    ("Ustun usuli", "  3 485\n+ 2 937\n──────\n  6 422\nBirliklardan boshlanadi",
     "Sonlarni xonama-xon ustun qilib yozamiz. Birliklardan boshlab qo‘shamiz; o‘n va undan ko‘p chiqsa, keyingi xonaga bittani ko‘chiramiz."),
    ("Ayirish", "  6 000\n− 2 478\n──────\n  3 522\nTekshirish: 3 522 + 2 478 = 6 000",
     "Ayirishda yetmasa, keyingi xonadan bitta o‘n qarz olamiz. Natijani qo‘shish orqali tekshiramiz: ayirma plyus ayriluvchi kamayuvchiga teng bo‘lishi kerak."),
])


@Y("t4_ustun")
def _u1(rng):
    a, b = rng.randint(1200, 5900), rng.randint(1100, 3900)
    return _y(rng, f"{a} + {b} = ?", a + b, [f"{a} + {b} = {a + b}."], noto=[a + b + 10, a + b - 100, a + b + 1000, a + b - 10])


@Y("t4_ustun")
def _u2(rng):
    a = rng.randint(5000, 9900); b = rng.randint(1100, 4900)
    return _y(rng, f"{a} − {b} = ?", a - b, [f"{a} − {b} = {a - b}."], noto=[a - b + 100, a - b - 10, a - b + 1000, a - b - 100])


@Y("t4_ustun")
def _u3(rng):
    a, b = rng.randint(1500, 4500), rng.randint(1200, 3500)
    return _y(rng, f"Kutubxonada {a} ta kitob bor edi. Yana {b} ta kitob keltirildi. Hammasi bo‘lib nechta kitob bo‘ldi?", a + b, [f"Qo‘shamiz: {a} + {b} = {a + b}."],
              noto=[a - b, a + b + 100, a + b - 10])


@Y("t4_ustun")
def _u4(rng):
    a = rng.randint(4000, 9000); b = rng.randint(1000, 3900); s = a - b
    return _y(rng, f"Qaysi son o‘rniga «?» qo‘yilsa tenglik to‘g‘ri bo‘ladi: {b} + ? = {a}", s, [f"Noma’lum qo‘shiluvchi = yig‘indi − ma’lum qo‘shiluvchi = {a} − {b} = {s}."],
              noto=[a + b, s + 100, s - 10])


@O("t4_ustun")
def _u5(rng):
    a, b, c = rng.randint(1000, 3000), rng.randint(1000, 3000), rng.randint(500, 2500)
    return _o(f"Maktab bog‘ida {a} ta olma, {b} ta nok va {c} ta behi daraxti mevasi yig‘ildi.", [("a) Olma va nok birgalikda:", a + b), ("b) Hammasi:", a + b + c)],
              [f"a) {a} + {b} = {a + b}.", f"b) {a + b} + {c} = {a + b + c}."])


@O("t4_ustun")
def _u6(rng):
    a = rng.randint(6000, 9500); b = rng.randint(1500, 3500); c = rng.randint(500, 1400)
    return _o(f"Do‘konda {a} dona daftar bor edi. Birinchi kuni {b} dona, ikkinchi kuni {c} dona sotildi.", [("a) Ikki kunda sotildi:", b + c), ("b) Qoldi:", a - b - c)],
              [f"a) {b} + {c} = {b + c}.", f"b) {a} − {b + c} = {a - b - c}."])


# 3 ── ko'paytirish
tema("t4_kopay", "Ko‘paytirish va jadval", "Sonlar", "✖️", "Ko‘paytirish jadvali, ko‘p xonali sonni bir xonaliga ko‘paytirish, takroriy qo‘shish", [
    ("Ko‘paytirish nima", "4 · 6 = 6 + 6 + 6 + 6 = 24\nO‘rin almashtirish: 4 · 6 = 6 · 4",
     "Ko‘paytirish bir xil sonlarni takror qo‘shishdir. To‘rt marta olti — olti plyus olti plyus olti plyus olti, ya’ni yigirma to‘rt. Ko‘paytuvchilar o‘rnini almashtirsak, natija o‘zgarmaydi."),
    ("Ko‘p xonali son", "23 · 4 = 20 · 4 + 3 · 4 = 80 + 12 = 92",
     "Ikki xonali sonni bir xonaliga ko‘paytirishda sonni o‘nliklari va birliklariga ajratamiz, har birini ko‘paytirib, natijalarni qo‘shamiz."),
])


@Y("t4_kopay")
def _k1(rng):
    a, b = rng.randint(6, 9), rng.randint(6, 9)
    return _y(rng, f"{a} · {b} = ?", a * b, [f"{a} · {b} = {a * b}."], noto=[a * b + a, a * b - b, a + b * 2, a * b + 1])


@Y("t4_kopay")
def _k2(rng):
    a, b = rng.randint(12, 48), rng.randint(3, 9)
    return _y(rng, f"{a} · {b} = ?", a * b, [f"{a} · {b} = {a // 10 * 10} · {b} + {a % 10} · {b} = {a // 10 * 10 * b} + {a % 10 * b} = {a * b}."], noto=[a * b + 10, a * b - b, a * b + b * 2, a // 10 * 10 * b])


@Y("t4_kopay")
def _k3(rng):
    q, k = rng.randint(6, 12), rng.randint(5, 9)
    return _y(rng, f"Sinfda {q} ta partada {k} tadan o‘quvchi o‘tiradi. Sinfda nechta o‘quvchi bor?", q * k, [f"{q} · {k} = {q * k}."], noto=[q + k, q * k + k, q * k - q])


@Y("t4_kopay")
def _k4(rng):
    n, p = rng.randint(3, 9), rng.choice([1200, 1500, 2500, 3000, 4000])
    return _y(rng, f"1 ta daftar {som(p)} so‘m. {n} ta daftar necha so‘m turadi?", n * p, [f"{n} · {som(p)} = {som(n * p)} so‘m."], noto=[(n + 1) * p, n * p + p // 2, n * p - p])


@O("t4_kopay")
def _k5(rng):
    a, b = rng.randint(3, 9), rng.randint(15, 45)
    return _o(f"Har bir qutida {b} ta qalam bor. Qutilar soni — {a} ta.", [("a) Hammasi bo‘lib qalam:", a * b), ("b) Agar yana 1 ta quti qo‘shilsa, qalam jami:", (a + 1) * b)], [f"a) {a} · {b} = {a * b}.", f"b) {a + 1} · {b} = {(a + 1) * b}."])


@O("t4_kopay")
def _k6(rng):
    a, b = rng.randint(4, 9), rng.randint(6, 12)
    return _o(f"Maydon {a} qatordan iborat, har qatorda {b} ta gul bor.", [("a) Gullar soni:", a * b), ("b) 3 qator kamaytirilsa, qolgan gullar:", (a - 3 if a > 3 else 1) * b)],
              [f"a) {a} · {b} = {a * b}.", f"b) {(a - 3 if a > 3 else 1)} · {b} = {(a - 3 if a > 3 else 1) * b}."])


# 4 ── bo'lish va qoldiq
tema("t4_bolish", "Bo‘lish va qoldiq", "Sonlar", "➗", "Teng bo‘lish, qoldiqli bo‘lish va tekshirish", [
    ("Teng bo‘lish", "24 : 4 = 6\nTekshirish: 6 · 4 = 24", "Bo‘lish — narsalarni teng bo‘laklarga ajratish. Yigirma to‘rtni to‘rtga bo‘lsak, olti chiqadi; ko‘paytirish bilan tekshiramiz."),
    ("Qoldiq", "25 : 4 = 6 (qoldiq 1)\nBo‘luvchi · bo‘linma + qoldiq = bo‘linuvchi", "Hamma narsa teng bo‘linmasa, qoldiq qoladi. Qoldiq bo‘luvchidan doim kichik bo‘ladi."),
])


@Y("t4_bolish")
def _b1(rng):
    b, q = rng.randint(3, 9), rng.randint(4, 12)
    return _y(rng, f"{b * q} : {b} = ?", q, [f"{q} · {b} = {b * q}, demak {b * q} : {b} = {q}."], noto=[q + 1, q - 1, b, q + 2])


@Y("t4_bolish")
def _b2(rng):
    b, q, r = rng.randint(3, 9), rng.randint(5, 12), None
    r = rng.randint(1, b - 1); n = b * q + r
    return _y(rng, f"{n} ni {b} ga bo‘lganda qoldiq nechaga teng?", r, [f"{n} = {b} · {q} + {r}. Qoldiq {r}."], noto=[(r % (b - 1)) + 1 if (r % (b - 1)) + 1 != r else r + b, q % 10, b - r if b - r != r else r + 1, 0])


@Y("t4_bolish")
def _b3(rng):
    k, t = rng.randint(3, 8), rng.randint(5, 9)
    return _y(rng, f"{k * t} ta olma {k} ta savatga teng taqsimlandi. Har savatda nechta olma bor?", t, [f"{k * t} : {k} = {t}."], noto=[k * t - k, t + 1, k])


@Y("t4_bolish")
def _b4(rng):
    b = rng.randint(4, 9); q = rng.randint(6, 15); r = rng.randint(1, b - 1); n = b * q + r
    return _y(rng, f"{n} o‘quvchi {b} kishilik jamoalarga bo‘lindi. Nechta to‘liq jamoa bo‘ladi?", q, [f"{n} : {b} = {q} (qoldiq {r}). To‘liq jamoalar {q} ta."], noto=[q + 1, r, q - 1])


@O("t4_bolish")
def _b5(rng):
    b = rng.randint(4, 9); q = rng.randint(8, 20); r = rng.randint(1, b - 1); n = b * q + r
    return _o(f"{n} ta konfet {b} ta bolaga bir xil bo‘lib berildi.", [("a) Har bir bolaga konfet:", q), ("b) Ortib qolgan konfet:", r)], [f"a) {n} : {b} = {q} (qoldiq {r}).", f"b) Qoldiq {r}."])


@O("t4_bolish")
def _b6(rng):
    b = rng.randint(3, 8); q = rng.randint(10, 30); n = b * q
    return _o(f"{n} so‘m {b} ta do‘stga teng bo‘lindi.", [("a) Har biriga so‘m:", q), ("b) Tekshirish: ko‘paytma:", q * b)], [f"a) {n} : {b} = {q}.", f"b) {q} · {b} = {n}."])


# 5 ── kasrlar
tema("t4_kasr", "Kasrlarni taqqoslash va qo‘shish", "Kasrlar", "🍕", "Bir xil maxrajli kasrlar, birlik kasrlar, kasrni son o‘qida ko‘rsatish", [
    ("Kasr nima", "3/8 → 8 bo‘lakning 3 tasi\nMaxraj — bo‘laklar soni\nSurat — olingan bo‘laklar", "Kasrning maxraji butunning nechta teng bo‘lakka bo‘linganini, surati esa nechtasi olinganini ko‘rsatadi."),
    ("Taqqoslash", "Maxraj bir xil: surati katta kasr katta\n5/8 > 3/8\nSurat bir xil: maxraji kichik kasr katta\n1/3 > 1/5", "Maxraji bir xil bo‘lsa, suratiga qaraymiz. Surati bir xil bo‘lsa, bo‘laklar kattaroq bo‘lgan, ya’ni maxraji kichik kasr katta."),
    ("Qo‘shish", "2/7 + 3/7 = 5/7\nMaxraj o‘zgarmaydi", "Maxrajlari bir xil kasrlarni qo‘shganda suratlar qo‘shiladi, maxraj o‘zgarishsiz qoladi."),
])


@Y("t4_kasr")
def _f1(rng):
    d = rng.randint(5, 12); a, b = rng.sample(range(1, d), 2)
    return _y(rng, f"Qaysi kasr katta: {a}/{d} yoki {b}/{d}?", f"{max(a, b)}/{d}", [f"Maxrajlar teng, suratlari: {a} va {b}. Katta surat — katta kasr."], noto=[f"{min(a, b)}/{d}", f"{a + b}/{d}", f"{abs(a - b)}/{d}", f"{max(a, b)}/{d + 1}", f"{max(a, b) + 1}/{d}", f"{min(a, b)}/{d + 2}"])


@Y("t4_kasr")
def _f2(rng):
    d = rng.randint(6, 12); a = rng.randint(1, (d - 1) // 2); b = rng.randint(1, d - 1 - a)
    return _y(rng, f"{a}/{d} + {b}/{d} = ?", f"{a + b}/{d}", ["Maxraj bir xil — suratlar qo‘shiladi, maxraj o‘zgarmaydi."], noto=[f"{a + b}/{2 * d}", f"{a * b}/{d}", f"{a + b + 1}/{d}", f"{a + b}/{d + 1}", f"{a + b + 2}/{d}", f"{abs(a - b)}/{d}"])


@Y("t4_kasr")
def _f3(rng):
    d = rng.choice([4, 5, 8, 10]); k = rng.randint(1, d - 1); tot = d * rng.randint(2, 6)
    return _y(rng, f"{tot} ta olmaning {k}/{d} qismi necha dona?", tot // d * k, [f"{tot} : {d} = {tot // d}, keyin {tot // d} · {k} = {tot // d * k}."], noto=[tot // d, tot - tot // d * k + 1, tot // d * k + d])


@Y("t4_kasr")
def _f4(rng):
    a, b = rng.sample(range(2, 10), 2)
    return _y(rng, f"1/{a} va 1/{b} kasrlardan qaysi biri katta?", f"1/{min(a, b)}", ["Surat bir xil bo‘lsa, maxraji kichik kasr katta."], noto=[f"1/{max(a, b)}", f"2/{a + b}", f"1/{a + b}"])


@O("t4_kasr")
def _f5(rng):
    d = rng.randint(6, 12); a = rng.randint(1, 3); b = rng.randint(1, 3)
    return _o(f"Pitsa {d} bo‘lakka bo‘lindi. Ali {a} bo‘lak, Vali {b} bo‘lak yedi.", [("a) Ikkalasi yegan bo‘laklar soni:", a + b), ("b) Qolgan bo‘laklar soni:", d - a - b)], [f"a) {a} + {b} = {a + b}.", f"b) {d} − {a + b} = {d - a - b}."])


@O("t4_kasr")
def _f6(rng):
    d = rng.choice([5, 10, 4, 8]); m = rng.randint(2, 8); tot = d * m; k = rng.randint(1, d - 1)
    return _o(f"{tot} metr arqonning {k}/{d} qismi kesib olindi.", [("a) Kesib olingan qism (m):", m * k), ("b) Qolgan qism (m):", tot - m * k)], [f"a) {tot} : {d} · {k} = {m * k}.", f"b) {tot} − {m * k} = {tot - m * k}."])


# 6 ── o'nli kasrlar va pul
tema("t4_onli", "O‘nli kasrlar: pul va uzunlik", "Kasrlar", "💲", "O‘ndan va yuzdan bir, o‘nli kasrlarni taqqoslash va qo‘shish", [
    ("O‘nli kasr", "0,1 = 1/10\n0,01 = 1/100\n3,45 = 3 butun 4 o‘ndan, 5 yuzdan", "O‘nli kasrda vergul butun qismni kasr qismdan ajratadi. Birinchi raqam o‘ndan birlar, ikkinchisi yuzdan birlar."),
    ("Taqqoslash va qo‘shish", "0,8 > 0,75\nVergul ostida vergul: 2,4 + 1,35 = 3,75", "O‘nli kasrlarni taqqoslashda butun qismini, keyin o‘ndan birlarni solishtiramiz. Qo‘shishda vergulni vergul tagiga yozamiz."),
])


@Y("t4_onli")
def _o1(rng):
    a = rng.randint(11, 99) / 10; b = a + rng.choice([-0.5, 0.3, 0.2, -0.1, 0.4, -0.3])
    a, b = Fraction(round(a * 10), 10), Fraction(round(b * 10), 10)
    return _y(rng, f"Qaysi son katta: {num(a)} yoki {num(b)}?", max(a, b), ["Butun qismlar, so‘ng o‘ndan birlar solishtiriladi."], noto=[min(a, b), a + b, abs(a - b) + Fraction(1, 10)])


@Y("t4_onli")
def _o2(rng):
    a = Fraction(rng.randint(11, 59), 10); b = Fraction(rng.randint(11, 39), 10)
    return _y(rng, f"{num(a)} + {num(b)} = ?", a + b, [f"Vergul ostida vergul: {num(a)} + {num(b)} = {num(a + b)}."], noto=[a + b + Fraction(1, 10), a + b - 1, (a + b) * 10, a + b + 1])


@Y("t4_onli")
def _o3(rng):
    a = Fraction(rng.randint(60, 99), 10); b = Fraction(rng.randint(11, 59), 10)
    return _y(rng, f"{num(a)} − {num(b)} = ?", a - b, [f"{num(a)} − {num(b)} = {num(a - b)}."], noto=[a - b + 1, a - b - Fraction(1, 10), a + b, a - b + Fraction(1, 10)])


@Y("t4_onli")
def _o4(rng):
    m = rng.randint(1, 9); s = rng.randint(1, 9)
    return _y(rng, f"{m} m {s * 10} sm uzunlik metrlarda o‘nli kasr bilan qanday yoziladi?", Fraction(m * 100 + s * 10, 100), [f"{s * 10} sm = {num(Fraction(s * 10, 100))} m; jami {num(Fraction(m * 100 + s * 10, 100))} m."],
              noto=[Fraction(m * 100 + s * 10, 10), Fraction(m * 10 + s, 100) + 1, Fraction(m * 100 + s, 100)])


@O("t4_onli")
def _o5(rng):
    a = Fraction(rng.randint(11, 59), 10); b = Fraction(rng.randint(11, 49), 10)
    return _o(f"Ikki taxta uzunligi {num(a)} m va {num(b)} m.", [("a) Birgalikda uzunlik (m):", a + b), ("b) Farqi (m):", abs(a - b))], [f"a) {num(a)} + {num(b)} = {num(a + b)}.", f"b) Katta − kichik = {num(abs(a - b))}."])


@O("t4_onli")
def _o6(rng):
    a = Fraction(rng.randint(120, 480), 100); n = rng.randint(2, 4)
    return _o(f"1 kg olma {num(a)} ming so‘m.", [(f"a) {n} kg olma necha ming so‘m?", a * n), ("b) Bunga 10 ming so‘mlik berilsa, qaytim (ming so‘m):", 10 - a * n if 10 > a * n else 0)], [f"a) {num(a)} · {n} = {num(a * n)}.", f"b) 10 − {num(a * n)}."])


# 7 ── matnli masalalar
tema("t4_masala", "Ikki amalli matnli masalalar", "Sonlar", "📖", "Masalani tushunish, reja tuzish va ikki amal bilan yechish", [
    ("Masalani tahlil", "Berilgan → Topish kerak → Reja\nHar bosqichda bitta amal", "Masalani o‘qib, nima berilganini va nimani topish kerakligini ajrating. Keyin reja tuzing: avval nimani topamiz, so‘ng nimani."),
    ("Tekshirish", "Javob mantiqan to‘g‘rimi?\nBirligini yozing", "Javobni savolga qaytarib qo‘yib tekshiring. Birliklarni to‘g‘ri yozishni unutmang."),
])


@Y("t4_masala")
def _m1(rng):
    a, b, c = rng.randint(3, 9), rng.randint(5, 12), rng.randint(5, 40)
    return _y(rng, f"Do‘konda {a} qutida {b} tadan qalam bor edi. {c} ta qalam sotildi. Nechta qalam qoldi?", a * b - c if a * b > c else a * b + c, [f"Avval {a} · {b} = {a * b}, keyin {a * b} − {c}."] if a * b > c else ["—"], noto=[a * b + c, a + b - c, a * b - c + 10])


@Y("t4_masala")
def _m2(rng):
    p = rng.choice([1500, 2000, 2500, 3000]); n = rng.randint(2, 5); pul = rng.choice([20000, 30000, 50000])
    return _y(rng, f"Ali {n} ta kitobchani {som(p)} so‘mdan sotib oldi va {som(pul)} so‘m berdi. Qaytim qancha (so‘m)?", pul - n * p, [f"{n} · {som(p)} = {som(n * p)}; {som(pul)} − {som(n * p)} = {som(pul - n * p)}."], noto=[pul + n * p, pul - p, n * p])


@Y("t4_masala")
def _m3(rng):
    a, b = rng.randint(30, 80), rng.randint(5, 20)
    return _y(rng, f"Sinfda {a} o‘quvchi bor. Ularning {b} tasi qiz bola. Bolalar qiz bolalardan nechta ko‘p?", a - 2 * b if a > 2 * b else 2 * b - a,
              [f"O‘g‘il bolalar: {a} − {b} = {a - b}. Farq: {abs(a - 2 * b)}."], noto=[a - b, a + b, abs(a - 2 * b) + 2])


@Y("t4_masala")
def _m4(rng):
    k, t = rng.randint(3, 8), rng.randint(5, 9); q = rng.randint(1, k * t - 1)
    return _y(rng, f"{k} ta bog‘ga {t} tadan nihol ekildi. {q} ta nihol qurib qoldi. Nechta nihol omon qoldi?", k * t - q, [f"{k} · {t} = {k * t}; {k * t} − {q} = {k * t - q}."], noto=[k * t + q, k + t - q, k * t - q + t])


@O("t4_masala")
def _m5(rng):
    a, b, c = rng.randint(4, 9), rng.randint(6, 15), rng.randint(20, 60)
    return _o(f"Fermer {a} ta qutiga {b} kg dan olma joyladi, yana {c} kg olma sotib yubordi.", [("a) Qutilardagi olma (kg):", a * b), ("b) Jami olma (kg):", a * b + c)], [f"a) {a} · {b} = {a * b}.", f"b) {a * b} + {c} = {a * b + c}."])


@O("t4_masala")
def _m6(rng):
    a, b = rng.randint(100, 400), rng.randint(2, 6)
    return _o(f"Velosipedchi bir kunda {a} km yurdi. U {b} kun shunday yurdi, keyin {a * 2} km dam oldi.", [("a) Yurgan masofa (km):", a * b), ("b) Qolgan yo‘l (jami 2 000 km bo‘lsa):", 2000 - a * b)], [f"a) {a} · {b} = {a * b}.", f"b) 2000 − {a * b} = {2000 - a * b}."])


# 8 ── qonuniyat
tema("t4_qonun", "Sonli qonuniyatlar", "Qonuniyatlar", "🔁", "Ketma-ketlik qoidasini topish va davom ettirish", [
    ("Qoida", "3, 7, 11, 15, … → +4\nHar safar bir xil son qo‘shiladi", "Qonuniyatni topish uchun qo‘shni sonlar orasidagi farqni toping. Farq bir xil bo‘lsa, shu son har safar qo‘shiladi."),
    ("Davom ettirish", "10, 20, 40, 80 → ·2\nQoida bilan keyingi hadni toping", "Ba’zan sonlar har safar bir necha marta ortadi. Qoidani aniqlab keyingi hadlarni yozing."),
])


@Y("t4_qonun")
def _q1(rng):
    a, d = rng.randint(2, 20), rng.randint(2, 9); s = [a + d * i for i in range(5)]
    return _y(rng, f"Qonuniyatni davom ettiring: {s[0]}, {s[1]}, {s[2]}, {s[3]}, ?", s[4], [f"Har safar +{d}: {s[3]} + {d} = {s[4]}."], noto=[s[3] + d + 1, s[3] + d - 1, s[3] + d * 2, s[3] + 1])


@Y("t4_qonun")
def _q2(rng):
    a, d = rng.randint(50, 90), rng.randint(3, 8); s = [a - d * i for i in range(5)]
    return _y(rng, f"Qonuniyat qoidasi nima: {s[0]}, {s[1]}, {s[2]}, {s[3]}, …", f"har safar −{d}", [f"Farq: {s[1]} − {s[0]} = {-d}."], noto=[f"har safar +{d}", f"har safar −{d + 1}", f"har safar ·{d}"])


@Y("t4_qonun")
def _q3(rng):
    a, m = rng.randint(1, 5), rng.choice([2, 3]); s = [a * m ** i for i in range(4)]
    return _y(rng, f"Qonuniyatni davom ettiring: {s[0]}, {s[1]}, {s[2]}, ?", s[3], [f"Har safar {m} marta ko‘payadi: {s[2]} · {m} = {s[3]}."], noto=[s[2] + m, s[2] + s[1], s[2] * m + 1])


@Y("t4_qonun")
def _q4(rng):
    n, d = rng.randint(6, 12), rng.randint(2, 5); a = rng.randint(1, 9)
    return _y(rng, f"Ketma-ketlikning birinchi hadi {a}, har safar {d} dan ortadi. {n}-had nechaga teng?", a + d * (n - 1), [f"{n}-had = {a} + {d} · {n - 1} = {a + d * (n - 1)}."], noto=[a + d * n, a + d * (n - 2), a * d * n])


@O("t4_qonun")
def _q5(rng):
    a, d = rng.randint(2, 15), rng.randint(3, 8); s = [a + d * i for i in range(7)]
    return _o(f"Qonuniyat: {s[0]}, {s[1]}, {s[2]}, …", [("a) Qo‘shiladigan son:", d), ("b) 7-had:", s[6])], [f"a) {s[1]} − {s[0]} = {d}.", f"b) {s[0]} + {d}·6 = {s[6]}."])


@O("t4_qonun")
def _q6(rng):
    a = rng.randint(2, 6); s = [a * 2 ** i for i in range(6)]
    return _o(f"Qonuniyat: {s[0]}, {s[1]}, {s[2]}, {s[3]}, …", [("a) 5-had:", s[4]), ("b) 6-had:", s[5])], [f"a) {s[3]} · 2 = {s[4]}.", f"b) {s[4]} · 2 = {s[5]}."])


# 9 ── burchak va chiziqlar
tema("t4_burchak", "Burchaklar va chiziqlar", "Geometriya", "📐", "To‘g‘ri, o‘tkir, o‘tmas burchaklar; parallel va perpendikulyar chiziqlar", [
    ("Burchak turlari", "To‘g‘ri = 90°\nO‘tkir < 90°\nO‘tmas > 90°", "To‘g‘ri burchak to‘qson gradusga teng. To‘qsondan kichigi — o‘tkir, katta va yuz sakson gradusdan kichigi — o‘tmas burchak."),
    ("Chiziqlar", "Parallel: kesishmaydi\nPerpendikulyar: 90° da kesishadi", "Parallel chiziqlar hech qachon kesishmaydi. Perpendikulyar chiziqlar to‘g‘ri burchak hosil qilib kesishadi."),
])


@Y("t4_burchak")
def _a1(rng):
    g = rng.choice([30, 45, 60, 75, 90, 100, 120, 135, 150, 25, 110])
    t = "to‘g‘ri" if g == 90 else ("o‘tkir" if g < 90 else "o‘tmas")
    return _y(rng, f"{g}° li burchak qanday burchak?", t, ["90° — to‘g‘ri; 90° dan kichik — o‘tkir; katta — o‘tmas."], noto=[x for x in ["to‘g‘ri", "o‘tkir", "o‘tmas", "yoyiq"] if x != t][:3])


@Y("t4_burchak")
def _a2(rng):
    n = rng.choice([4, 5, 6, 3]); k = rng.choice(["to‘g‘ri", "o‘tkir"])
    return _y(rng, "Kvadratning har bir burchagi necha gradus?", 90, ["Kvadratning barcha burchaklari to‘g‘ri burchak — 90°."], noto=[60, 180, 45, 100])


@Y("t4_burchak")
def _a3(rng):
    a = rng.randint(20, 80)
    return _y(rng, f"To‘g‘ri burchak ikkiga bo‘lindi, birinchi qismi {a}°. Ikkinchi qismi necha gradus?", 90 - a, [f"90 − {a} = {90 - a}."], noto=[180 - a, a, 90 + a])


@Y("t4_burchak")
def _a4(rng):
    return _y(rng, "Qaysi chiziqlar hech qachon kesishmaydi?", "parallel", ["Kesishmaydigan chiziqlar parallel deyiladi."], noto=["perpendikulyar", "kesuvchi", "egri"])


@O("t4_burchak")
def _a5(rng):
    a = rng.randint(30, 80)
    return _o(f"Burchaklar: {a}° va {a + 10}°.", [("a) Ularning yig‘indisi (°):", 2 * a + 10), ("b) 180° ga to‘ldiruvchi qancha:", 180 - 2 * a - 10)], [f"a) {a} + {a + 10} = {2 * a + 10}.", f"b) 180 − {2 * a + 10}."])


@O("t4_burchak")
def _a6(rng):
    a = rng.randint(20, 85)
    return _o(f"Burchak {a}° ga teng.", [("a) 90° gacha yetmaydigan qism (°):", 90 - a), ("b) 180° gacha yetmaydigan qism (°):", 180 - a)], [f"a) 90 − {a} = {90 - a}.", f"b) 180 − {a} = {180 - a}."])


# 10 ── perimetr va yuza
tema("t4_perim", "Perimetr va yuza (to‘rtburchak)", "Geometriya", "🟩", "To‘rtburchak va kvadratning perimetri va yuzasi", [
    ("Perimetr", "P = 2 · (a + b)\nKvadrat: P = 4 · a", "Perimetr — shakl tomonlari uzunliklarining yig‘indisi. To‘rtburchakda ikki marta uzunlik va kenglik yig‘indisi."),
    ("Yuza", "S = a · b\nKvadrat: S = a · a\nBirlik: kv. sm", "Yuza — shakl egallagan joy. To‘rtburchak yuzasi uzunlik va kenglik ko‘paytmasiga teng; birligi kvadrat santimetr."),
])


@Y("t4_perim")
def _p1(rng):
    a, b = rng.randint(4, 15), rng.randint(2, 10)
    return _y(rng, f"To‘rtburchakning tomonlari {a} sm va {b} sm. Perimetri necha sm?", 2 * (a + b), [f"P = 2 · ({a} + {b}) = {2 * (a + b)}."], noto=[a * b, a + b, 2 * a + b])


@Y("t4_perim")
def _p2(rng):
    a, b = rng.randint(4, 15), rng.randint(2, 10)
    return _y(rng, f"To‘rtburchakning uzunligi {a} sm, kengligi {b} sm. Yuzasi necha kv. sm?", a * b, [f"S = {a} · {b} = {a * b}."], noto=[2 * (a + b), a + b, a * b + a])


@Y("t4_perim")
def _p3(rng):
    a = rng.randint(3, 15)
    return _y(rng, f"Kvadratning tomoni {a} sm. Perimetri necha sm?", 4 * a, [f"P = 4 · {a} = {4 * a}."], noto=[a * a, 2 * a, a + 4])


@Y("t4_perim")
def _p4(rng):
    a = rng.randint(3, 12)
    return _y(rng, f"Kvadratning tomoni {a} sm. Yuzasi necha kv. sm?", a * a, [f"S = {a} · {a} = {a * a}."], noto=[4 * a, 2 * a, a * a + a])


@O("t4_perim")
def _p5(rng):
    a, b = rng.randint(5, 15), rng.randint(3, 9)
    return _o(f"Bog‘ uzunligi {a} m, kengligi {b} m.", [("a) Perimetri (m):", 2 * (a + b)), ("b) Yuzasi (kv. m):", a * b)], [f"a) 2·({a}+{b}) = {2 * (a + b)}.", f"b) {a}·{b} = {a * b}."])


@O("t4_perim")
def _p6(rng):
    a = rng.randint(4, 12); p = 4 * a
    return _o(f"Kvadrat shaklidagi maydonning perimetri {p} m.", [("a) Bir tomoni (m):", a), ("b) Yuzasi (kv. m):", a * a)], [f"a) {p} : 4 = {a}.", f"b) {a}·{a} = {a * a}."])


# 11 ── vaqt va birliklar
tema("t4_vaqt", "Vaqt, pul va o‘lchov birliklari", "O‘lchash", "⏰", "Soat, daqiqa, kun; metr, santimetr; kilogramm, gramm", [
    ("Vaqt", "1 soat = 60 daqiqa\n1 sutka = 24 soat\n1 hafta = 7 kun", "Bir soat oltmish daqiqadan iborat. Sutka yigirma to‘rt soat, hafta yetti kun."),
    ("Uzunlik va massa", "1 m = 100 sm\n1 km = 1000 m\n1 kg = 1000 g", "Bir metrda yuz santimetr bor. Bir kilometr — ming metr. Bir kilogramm — ming gramm."),
])


@Y("t4_vaqt")
def _v1(rng):
    h, m = rng.randint(1, 4), rng.choice([10, 15, 20, 30, 45])
    return _y(rng, f"{h} soat {m} daqiqa necha daqiqa?", h * 60 + m, [f"{h} · 60 + {m} = {h * 60 + m}."], noto=[h * 100 + m, h + m, h * 60])


@Y("t4_vaqt")
def _v2(rng):
    m, s = rng.randint(1, 9), rng.choice([20, 40, 50, 75])
    return _y(rng, f"{m} m {s} sm necha santimetr?", m * 100 + s, [f"{m} · 100 + {s} = {m * 100 + s}."], noto=[m * 10 + s, m + s, m * 1000 + s])


@Y("t4_vaqt")
def _v3(rng):
    a, b = rng.randint(1, 5), rng.choice([100, 200, 250, 500])
    return _y(rng, f"{a} kg {b} g necha gramm?", a * 1000 + b, [f"{a} · 1000 + {b}."], noto=[a * 100 + b, a + b, a * 10000 + b])


@Y("t4_vaqt")
def _v4(rng):
    h = rng.randint(7, 11); d = rng.randint(2, 5)
    return _y(rng, f"Dars soat {h}:00 da boshlandi va {d} soat davom etdi. U soat nechada tugadi?", f"{h + d}:00", [f"{h} + {d} = {h + d}."], noto=[f"{h + d + 1}:00", f"{h + d - 1}:00", f"{h * d}:00"])


@O("t4_vaqt")
def _v5(rng):
    h, m = rng.randint(1, 3), rng.randint(5, 50)
    return _o(f"Film {h} soat {m} daqiqa davom etdi.", [("a) Daqiqalarda:", h * 60 + m), ("b) 2 ta shunday film (daqiqa):", 2 * (h * 60 + m))], [f"a) {h}·60 + {m} = {h * 60 + m}.", f"b) 2·{h * 60 + m}."])


@O("t4_vaqt")
def _v6(rng):
    a, b = rng.randint(2, 9), rng.randint(2, 9)
    return _o(f"Ikki arqon: {a} m va {b} m {b * 10} sm.", [("a) Birinchisi santimetrda:", a * 100), ("b) Ikkisi birga (sm):", a * 100 + b * 100 + b * 10)], [f"a) {a}·100 = {a * 100}.", f"b) {a * 100} + {b * 110}."])


# 12 ── jadval va diagramma
tema("t4_jadval", "Jadval va ustunli diagramma", "Ma’lumotlar", "📊", "Jadval va diagrammadan ma’lumot o‘qish, taqqoslash", [
    ("Diagramma", "Ustun balandligi = qiymat\nEng baland ustun — eng katta qiymat", "Ustunli diagrammada har bir ustun balandligi qiymatni bildiradi. Eng baland ustun eng katta qiymatga mos."),
    ("Jadval", "Satr va ustunlar kesishgan katak — qiymat\nJami = qiymatlar yig‘indisi", "Jadvalda satr va ustun kesishgan katak izlangan qiymatni beradi. Jami uchun hamma qiymatlarni qo‘shamiz."),
])


def _nom():
    return ["Dushanba", "Seshanba", "Chorshanba", "Payshanba"]


@Y("t4_jadval")
def _j1(rng):
    v = [rng.randint(10, 60) for _ in range(4)]; n = _nom()
    q = _y(rng, f"Diagramma: {n[0]} — {v[0]}, {n[1]} — {v[1]}, {n[2]} — {v[2]}, {n[3]} — {v[3]} ta mijoz. Eng ko‘p mijoz qaysi kuni?", n[v.index(max(v))], [f"Eng katta qiymat {max(v)} — shu kun."], noto=[x for x in n if x != n[v.index(max(v))]][:3]) if len(set(v)) == 4 else None
    if q is None:
        v = [12, 25, 38, 44]
        q = _y(rng, f"Diagramma: {n[0]} — 12, {n[1]} — 25, {n[2]} — 38, {n[3]} — 44 ta mijoz. Eng ko‘p mijoz qaysi kuni?", n[3], ["Eng katta qiymat 44."], noto=n[:3])
    return q


@Y("t4_jadval")
def _j2(rng):
    v = rng.sample(range(10, 70), 4)
    return _y(rng, f"Jadvalda 4 kunlik sotuv: {v[0]}, {v[1]}, {v[2]}, {v[3]}. Jami nechta?", sum(v), [f"Qo‘shamiz: {sum(v)}."], noto=[sum(v) + 10, sum(v) - 5, max(v) * 4])


@Y("t4_jadval")
def _j3(rng):
    v = rng.sample(range(10, 90), 2)
    return _y(rng, f"Diagrammada A ustuni {v[0]}, B ustuni {v[1]}. Ular orasidagi farq qancha?", abs(v[0] - v[1]), [f"Katta − kichik = {abs(v[0] - v[1])}."], noto=[v[0] + v[1], abs(v[0] - v[1]) + 5, max(v)])


@Y("t4_jadval")
def _j4(rng):
    v = rng.sample(range(10, 60), 3)
    return _y(rng, f"Uch sinf o‘quvchilari: {v[0]}, {v[1]}, {v[2]}. Eng kam o‘quvchili sinfda nechta bola bor?", min(v), ["Eng kichik qiymat."], noto=[max(v), sum(v), sorted(v)[1]])


@O("t4_jadval")
def _j5(rng):
    v = rng.sample(range(10, 80), 4)
    return _o(f"Sotuv (dona): 1-kun {v[0]}, 2-kun {v[1]}, 3-kun {v[2]}, 4-kun {v[3]}.", [("a) Jami:", sum(v)), ("b) Eng ko‘p va eng kam sotuv farqi:", max(v) - min(v))], [f"a) {' + '.join(map(str, v))} = {sum(v)}.", f"b) {max(v)} − {min(v)}."])


@O("t4_jadval")
def _j6(rng):
    v = rng.sample(range(10, 80), 3)
    q = _o(f"Uch do‘kon kunlik tushumi (ming so‘m): {v[0]}, {v[1]}, {v[2]}.", [("a) Eng katta tushum:", max(v)), ("b) Hammasi (ming so‘m):", sum(v))], [f"a) {max(v)}.", f"b) {sum(v)}."])
    q["rasm"] = fig_stolbik(["1", "2", "3"], v, "Tushum", "ming so‘m")
    return q
