"""TIMSS 4-sinf matematika: 8 mavzu (kurs mavzulari) — dars, 30 mashq, 30 test generatorlari."""
import math
import random
from fractions import Fraction

from modules.pisa_mat_g import reg, som, num, mm, _y, _o, _yopiq, fig_stolbik, fig_tortburchak, _svg, _t, _l, _poly

TOP = "T11_G4_M"


def _tema(kod, nom, soha, belgi, maqsad, dars):
    return {"nom": nom, "soha": soha, "belgi": belgi, "maqsad": maqsad, "bolim": kod, "toplam": TOP, "dars": dars}


def _d(sar, doska, ovoz):
    return {"sarlavha": sar, "doska": doska, "ovoz": ovoz}


# ───────── M4-NAT: natural sonlar va amallar ─────────
@reg("M4-NAT", "yopiq")
def nat_xona(rng):
    n = rng.randint(1000, 9999); xon = rng.choice([("mingliklar", 1000), ("yuzliklar", 100), ("o‘nliklar", 10), ("birliklar", 1)]); r = (n // xon[1]) % 10
    return _y(rng, f"{n} sonida {xon[0]} xonasidagi raqam nechaga teng?", r, [f"{n} = {n // 1000} ming + {n // 100 % 10} yuz + {n // 10 % 10} o‘n + {n % 10} bir.", f"{xon[0]} xonasidagi raqam: {r}."], noto=[(n // 10) % 10 if xon[1] != 10 else n % 10, n % 10 if xon[1] != 1 else n // 10 % 10, n // 1000])


@reg("M4-NAT", "yopiq")
def nat_qosh(rng):
    a = rng.randint(120, 480) * 3; b = rng.randint(100, 400) * 2; 
    return _y(rng, f"Kema {a} yo‘lovchini olib ketdi, keyingi bekatda yana {b} kishi chiqdi. Kemada hozir nechta yo‘lovchi bor?", a + b, [f"Qo‘shamiz: {a} + {b} = {a + b}."], noto=[a - b if a > b else a + b + 10, a + b + 100, a + b - 10])


@reg("M4-NAT", "yopiq")
def nat_kopaytir(rng):
    q = rng.choice([6, 8, 12, 15]); k = rng.choice([4, 6, 7, 9]); 
    return _y(rng, f"Bog‘da {q} qator olma daraxti bor, har qatorda {k} tadan daraxt. Bog‘da hammasi bo‘lib nechta daraxt?", q * k, [f"Qatorlar soni · har qatordagi son = {q} · {k} = {q * k}."], noto=[q + k, q * k + k, q * k - q])


@reg("M4-NAT", "yopiq")
def nat_yaxlit(rng):
    n = rng.randint(1100, 8999); n -= n % 10; n += rng.choice([2, 4, 6, 8]); r = round(n / 100) * 100 if n % 100 != 50 else n + 50
    return _y(rng, f"{n} sonini eng yaqin yuzliklargacha yaxlitlang.", r, [f"O‘nlar xonasiga qaraymiz: {n // 10 % 10}. {'5 yoki undan katta — yuqoriga' if n // 10 % 10 >= 5 else '5 dan kichik — pastga'} yaxlitlaymiz.", f"Javob: {r}."], noto=[n // 100 * 100 if r != n // 100 * 100 else n // 100 * 100 + 100, n // 1000 * 1000, r + 100])


@reg("M4-NAT", "ochiq")
def nat_bolish(rng):
    k = rng.choice([6, 7, 8, 9]); b = rng.randint(8, 25); q = rng.randint(1, k - 1); n = k * b + q
    return _o(f"Maktab kutubxonasida {n} ta kitob bor. Ularni {k} ta javonga teng taqsimlashdi, ortib qolganlari stolga qo‘yildi.", [("a) Har javonda nechta kitob bor?", b), ("b) Stolga nechta kitob qo‘yildi?", q)],
              [f"{n} ÷ {k} = {b} (qoldiq {q}).", f"a) Har javonda {b} ta.", f"b) Qoldiq — {q} ta kitob stolda."])


@reg("M4-NAT", "ochiq")
def nat_kop_qadam(rng):
    n = rng.choice([24, 30, 36]); p = rng.choice([1500, 2000, 2500]); b = rng.choice([8, 10, 12]); 
    return _o(f"Sinfda {n} ta o‘quvchi bor. Har biriga {som(p)} so‘mlik daftar olinadi. Sinf rahbari {som(n * p + b * 1000)} so‘m berdi.", [("a) Daftarlar uchun jami necha so‘m kerak?", n * p), ("b) Qaytim necha so‘m?", b * 1000)],
              [f"a) {n} · {som(p)} = {som(n * p)} so‘m.", f"b) {som(n * p + b * 1000)} − {som(n * p)} = {som(b * 1000)} so‘m."])


@reg("M4-NAT", "ochiq")
def nat_tartib(rng):
    xs = rng.sample(range(1000, 9999), 4)
    return _o(f"To‘rtta sonni ko‘rib chiqing: {', '.join(map(str, xs))}.", [("a) Eng kattasini yozing.", max(xs)), ("b) Eng kichigini yozing.", min(xs))], [f"Kattaligi bo‘yicha tartiblaymiz: {', '.join(map(str, sorted(xs)))}.", f"a) Eng katta: {max(xs)}. b) Eng kichik: {min(xs)}."])


# ───────── M4-KAS: kasrlar va o‘nli kasrlar ─────────
@reg("M4-KAS", "yopiq")
def kas_qism(rng):
    n = rng.choice([12, 16, 20, 24, 30]); b = rng.choice([2, 3, 4, 5]); 
    while n % b: n += 1
    a = rng.randint(1, b - 1)
    return _y(rng, f"Pitsa {n} bo‘lakka kesilgan. Bolalar bo‘laklarning {a}/{b} qismini yeb qo‘yishdi. Nechta bo‘lak yeyilgan?", n // b * a, [f"1/{b} qism = {n} ÷ {b} = {n // b} bo‘lak.", f"{a}/{b} qism = {n // b} · {a} = {n // b * a} bo‘lak."], noto=[n // b, n - n // b * a if n - n // b * a != n // b * a else n // b * a + 1, n // b * a + n // b])


@reg("M4-KAS", "yopiq")
def kas_taqqos(rng):
    b = rng.choice([5, 6, 8, 10]); a1, a2 = rng.sample(range(1, b), 2); big = f"{max(a1, a2)}/{b}"
    return _yopiq(rng, f"Qaysi kasr kattaroq: {a1}/{b} yoki {a2}/{b}?", f"${max(a1, a2)}/{b}$".replace("/", "/"), [f"Maxrajlar bir xil ({b}) — surati kattasi kattaroq.", f"{max(a1, a2)} > {min(a1, a2)}, demak {big} kattaroq."], noto=[f"${min(a1, a2)}/{b}$", "Teng", "Aniqlab bo‘lmaydi"], tartib=False)


@reg("M4-KAS", "yopiq")
def kas_onli(rng):
    a = rng.randint(11, 99) / 10; b = rng.randint(11, 99) / 10; s = Fraction(round(a * 10) + round(b * 10), 10)
    return _y(rng, f"Matodan {num(Fraction(round(a * 10), 10))} m va {num(Fraction(round(b * 10), 10))} m kesib olindi. Jami necha metr mato kesilgan?", s, [f"O‘nli kasrlarni vergul ostiga vergul qo‘yib qo‘shamiz.", f"{num(Fraction(round(a * 10), 10))} + {num(Fraction(round(b * 10), 10))} = {num(s)} m."], noto=[s + Fraction(1, 10), s - 1, s * 10])


@reg("M4-KAS", "yopiq")
def kas_onliga(rng):
    b, a = rng.choice([(2, 1), (4, 1), (4, 3), (5, 2), (5, 4), (10, 7), (10, 3), (20, 9)]); v = Fraction(a, b)
    return _y(rng, f"{a}/{b} kasrni o‘nli kasr ko‘rinishida yozing.", v, [f"{a} ÷ {b} = {num(v)}."], noto=[Fraction(b, a * 10), v * 10, v / 10])


@reg("M4-KAS", "ochiq")
def kas_sondan(rng):
    n = rng.choice([24, 30, 36, 48, 60]); a, b = rng.choice([(1, 3), (2, 3), (3, 4), (1, 4), (2, 5), (3, 5)]) 
    while n % b: n += 6
    return _o(f"Dilnozada {n} ta stiker bor. Ularning {a}/{b} qismini do‘stiga berdi.", [("a) Do‘stiga nechta stiker berdi?", n // b * a), ("b) O‘zida nechta stiker qoldi?", n - n // b * a)],
              [f"a) {n} ÷ {b} = {n // b}, keyin · {a} = {n // b * a}.", f"b) {n} − {n // b * a} = {n - n // b * a}."])


@reg("M4-KAS", "ochiq")
def kas_narx(rng):
    p = rng.choice([2, 3, 4, 5]) * 1000 + rng.choice([500, 0]); m = rng.choice([2, 3, 4]); 
    return _o(f"1 metr lenta {num(Fraction(p, 1000))} ming so‘m turadi. Tohir {m} metr lenta oldi.", [("a) Hammasi necha ming so‘m bo‘ladi?", Fraction(p * m, 1000)), ("b) 20 ming so‘m berdi. Qaytim necha ming so‘m?", 20 - Fraction(p * m, 1000))],
              [f"a) {num(Fraction(p, 1000))} · {m} = {num(Fraction(p * m, 1000))}.", f"b) 20 − {num(Fraction(p * m, 1000))} = {num(20 - Fraction(p * m, 1000))}."])


# ───────── M4-TEN: tengliklar va noma'lum ─────────
@reg("M4-TEN", "yopiq")
def ten_qosh(rng):
    a = rng.randint(12, 90); b = a + rng.randint(10, 80)
    return _y(rng, f"□ + {a} = {b}. □ nimaga teng?", b - a, [f"Noma’lum qo‘shiluvchi = yig‘indi − ma’lum qo‘shiluvchi.", f"□ = {b} − {a} = {b - a}."], noto=[a + b, b - a + 10, b - a - 10])


@reg("M4-TEN", "yopiq")
def ten_kopayt(rng):
    a = rng.choice([3, 4, 5, 6, 7, 8, 9]); x = rng.randint(3, 12)
    return _y(rng, f"{a} · □ = {a * x}. □ nimaga teng?", x, [f"Noma’lum ko‘paytuvchi = ko‘paytma ÷ ma’lum ko‘paytuvchi.", f"□ = {a * x} ÷ {a} = {x}."], noto=[a * x - a, a * x + a, a + x])


@reg("M4-TEN", "yopiq")
def ten_tarozi(rng):
    a = rng.choice([4, 5, 6, 8]); x = rng.choice([2, 3, 4, 5]); 
    return _y(rng, f"Tarozining bir pallasida {a} kg tosh va noma’lum yuk, ikkinchisida {a + x} kg. Tarozi muvozanatda. Yuk necha kg?", x, [f"{a} + □ = {a + x}.", f"□ = {a + x} − {a} = {x} kg."], noto=[a + x, a, x + 1])


@reg("M4-TEN", "ochiq")
def ten_ikki(rng):
    a = rng.randint(2, 9); b = rng.randint(20, 60); x = rng.randint(3, 9); 
    return _o(f"Sehrgar sonni {a} ga ko‘paytirib, {b} ni qo‘shdi va {a * x + b} chiqdi.", [("a) U qaysi sondan boshlagan?", x), ("b) Agar sondan {0} ayirsa-chi: bu sondan 2 ta kam?".replace("{0}", "2").replace("Agar sondan 2 ayirsa-chi: bu sondan 2 ta kam?", "Boshlang‘ich sondan 2 ta kam bo‘lgan sonni yozing."), x - 2)],
              [f"a) Teskari amallar: ({a * x + b} − {b}) ÷ {a} = {a * x} ÷ {a} = {x}.", f"b) {x} − 2 = {x - 2}."])


@reg("M4-TEN", "ochiq")
def ten_yigindi(rng):
    s = rng.choice([30, 40, 50, 60]); a = rng.randint(8, 25)
    return _o(f"Ikkita sonning yig‘indisi {s}. Birinchisi {a} ga teng.", [("a) Ikkinchi son nechaga teng?", s - a), ("b) Ular ayirmasi nechaga teng? (kattasidan kichigini ayiring)", abs(s - 2 * a))],
              [f"a) {s} − {a} = {s - a}.", f"b) |{a} − {s - a}| = {abs(s - 2 * a)}."])


@reg("M4-TEN", "yopiq")
def ten_belgi(rng):
    a = rng.randint(4, 9); b = rng.randint(3, 8); c = a * b - rng.randint(1, 5)
    return _yopiq(rng, f"Qaysi belgi to‘g‘ri? {a} · {b} ... {c}", ">", [f"{a} · {b} = {a * b}.", f"{a * b} > {c}."], noto=["<", "=", "Hisoblab bo‘lmaydi"], tartib=False)


# ───────── M4-QON: qonuniyatlar ─────────
@reg("M4-QON", "yopiq")
def qon_qosh(rng):
    a = rng.randint(2, 20); d = rng.choice([3, 4, 5, 6, 7]); seq = [a + d * i for i in range(5)]
    return _y(rng, f"Qonuniyatni toping: {', '.join(map(str, seq[:4]))}, □. Keyingi son qaysi?", seq[4], [f"Har son oldingisidan {d} ta katta.", f"{seq[3]} + {d} = {seq[4]}."], noto=[seq[3] + d + 1, seq[3] + 2 * d, seq[3] - d])


@reg("M4-QON", "yopiq")
def qon_kamay(rng):
    a = rng.randint(60, 100); d = rng.choice([4, 5, 6, 8]); seq = [a - d * i for i in range(5)]
    return _y(rng, f"Sonlar qatori: {', '.join(map(str, seq[:4]))}, □. Bo‘sh joyga qaysi son yoziladi?", seq[4], [f"Har son oldingisidan {d} ta kam.", f"{seq[3]} − {d} = {seq[4]}."], noto=[seq[3] + d, seq[3] - 2 * d, seq[3] - d + 1])


@reg("M4-QON", "yopiq")
def qon_mashina(rng):
    k = rng.choice([2, 3, 4, 5]); b = rng.choice([1, 2, 3]); xs = [1, 2, 3, 5]; x = rng.randint(6, 12)
    q = _y(rng, f"«Sonli mashina» kiruvchi sonni bir xil qoida bilan o‘zgartiradi: 1 → {k + b}, 2 → {2 * k + b}, 3 → {3 * k + b}. {x} kirsa, nima chiqadi?", x * k + b, [f"Qoida: kirish · {k} + {b}.", f"{x} · {k} + {b} = {x * k + b}."], noto=[x * k, x + k + b, x * (k + b)])
    return q


@reg("M4-QON", "ochiq")
def qon_gugurt(rng):
    k = rng.choice([3, 4, 5]); n = rng.choice([5, 6, 7, 8]); 
    return _o(f"Gugurt cho‘plaridan kvadratlar qatori yasaladi: 1 ta kvadrat uchun 4 ta, har keyingisi uchun {k - 1 if k > 3 else 3} tadan ko‘p ... " if False else
              f"Uchburchaklar qatori: 1 ta uchburchak 3 ta cho‘p, 2 ta — 5 ta, 3 ta — 7 ta … (har yangi uchburchakka 2 ta cho‘p qo‘shiladi).", [(f"a) {n} ta uchburchak uchun nechta cho‘p kerak?", 2 * n + 1), ("b) 21 ta cho‘pdan nechta uchburchak yasash mumkin?", 10)],
              [f"a) Formula: 2 · n + 1 = 2 · {n} + 1 = {2 * n + 1}.", "b) 2 · n + 1 = 21 → n = 10."])


@reg("M4-QON", "ochiq")
def qon_jadval(rng):
    d = rng.choice([3, 4, 5]); a = rng.choice([2, 5, 8]); 
    return _o(f"Qiz har kuni oldingi kunidan {d} ta ortiq so‘z yodlaydi. 1-kuni {a} ta so‘z yodladi.", [("a) 5-kuni nechta so‘z yodlaydi?", a + 4 * d), ("b) 5 kun ichida jami nechta so‘z yodlaydi?", 5 * a + 10 * d)],
              [f"a) {a} + 4 · {d} = {a + 4 * d}.", f"b) {a} + {a + d} + {a + 2 * d} + {a + 3 * d} + {a + 4 * d} = {5 * a + 10 * d}."])


@reg("M4-QON", "yopiq")
def qon_shakl(rng):
    n = rng.choice([4, 5, 6, 7]); 
    return _y(rng, f"Qora va oq kvadratlar almashib keladi: ■ □ ■ □ ■ □ … {n * 2 + 1}-kvadrat qaysi rangda?", "Qora", ["Toq o‘rinlarda — qora, juft o‘rinlarda — oq.", f"{n * 2 + 1} — toq son, demak qora."], noto=["Oq", "Qizil", "Ko‘k"], tartib=False) if False else _yopiq(rng, f"Qora va oq kvadratlar almashib keladi: qora, oq, qora, oq, … {n * 2 + 1}-kvadrat qaysi rangda?", "Qora", ["Toq o‘rinlarda — qora, juft o‘rinlarda — oq.", f"{n * 2 + 1} — toq son, demak qora."], noto=["Oq", "Ko‘k", "Qizil"], tartib=False)


# ───────── M4-NUQ: nuqta, chiziq, burchak ─────────
def fig_burchak(g):
    r = 90; a = math.radians(g); O = (60, 150); P = (O[0] + r, O[1]); Q = (O[0] + r * math.cos(a), O[1] - r * math.sin(a))
    return _svg(_l(O, P, w=2) + _l(O, Q, w=2) + f'<path d="M{O[0] + 25},{O[1]} A25,25 0 0 0 {O[0] + 25 * math.cos(a):.1f},{O[1] - 25 * math.sin(a):.1f}" fill="none" stroke="#d33"/>' + _t(O[0] - 8, O[1] + 14, "O", size=13), 260, 170)


@reg("M4-NUQ", "yopiq")
def nuq_tur(rng):
    g = rng.choice([30, 45, 60, 90, 110, 135, 150, 180]); t = "o‘tkir" if g < 90 else "to‘g‘ri" if g == 90 else "o‘tmas" if g < 180 else "yoyiq"
    q = _yopiq(rng, f"{g}° li burchak qanday burchak?", t, [f"90° dan kichik — o‘tkir, 90° — to‘g‘ri, 90° dan katta, 180° dan kichik — o‘tmas, 180° — yoyiq.", f"{g}° — {t} burchak."], noto=[x for x in ["o‘tkir", "to‘g‘ri", "o‘tmas", "yoyiq"] if x != t], tartib=False)
    if g < 180:
        q["rasm"] = fig_burchak(g)
    return q


@reg("M4-NUQ", "yopiq")
def nuq_soat(rng):
    h = rng.choice([1, 2, 3, 4, 5, 6, 8, 9, 10, 11]); g = min(h, 12 - h) * 30
    return _y(rng, f"Soat {h}:00 ni ko‘rsatganda soat va daqiqa millari orasidagi kichik burchak necha gradus?", g, [f"Soat aylanasi 360°, 12 ta soat bo‘lagi: bir bo‘lak = 30°.", f"{min(h, 12 - h)} bo‘lak · 30° = {g}°."], noto=[h * 30 if h * 30 != g else g + 30, g + 30, g - 30 if g > 30 else g + 60])


@reg("M4-NUQ", "yopiq")
def nuq_sanash(rng):
    n = rng.choice([4, 5, 6, 8]); 
    return _y(rng, f"Tekislikda {n} ta nuqta belgilangan, hech uchtasi bir to‘g‘ri chiziqda yotmaydi. Har ikki nuqtani to‘g‘ri chiziq bilan birlashtirsak, nechta kesma hosil bo‘ladi?", n * (n - 1) // 2, [f"Har nuqtadan {n - 1} ta kesma chiqadi, lekin har kesma ikki marta sanaladi.", f"{n} · {n - 1} ÷ 2 = {n * (n - 1) // 2}."], noto=[n * (n - 1), n, n * (n - 1) // 2 + n])


@reg("M4-NUQ", "ochiq")
def nuq_yigindi(rng):
    a = rng.choice([30, 40, 50, 60, 70]); 
    return _o(f"To‘g‘ri burchakning bir qismi {a}° ga teng. Qolgan qismini toping.", [("a) Qolgan burchak necha gradus?", 90 - a), ("b) Yoyiq burchakdan shu {0}° ni ayirsak necha gradus qoladi?".replace("{0}", str(a)), 180 - a)], [f"a) 90° − {a}° = {90 - a}°.", f"b) 180° − {a}° = {180 - a}°."])


@reg("M4-NUQ", "ochiq")
def nuq_perp(rng):
    n = rng.choice([2, 3, 4]); 
    return _o(f"Kvadrat daftar varag‘ida {n} ta gorizontal va {n} ta vertikal to‘g‘ri chiziq chizildi (ular bir-biriga perpendikulyar).", [("a) Hammasi bo‘lib nechta kesishish nuqtasi hosil bo‘ldi?", n * n), ("b) Hosil bo‘lgan to‘g‘ri burchaklar soni har kesishishda nechta?", 4)], [f"a) Har gorizontal chiziq har vertikal chiziqni kesadi: {n} · {n} = {n * n}.", "b) Ikki perpendikulyar chiziq kesishganda 4 ta to‘g‘ri burchak hosil bo‘ladi."])


@reg("M4-NUQ", "yopiq")
def nuq_parallel(rng):
    return _yopiq(rng, rng.choice(["Qaysi juft chiziqlar hech qachon kesishmaydi?", "Hech qachon kesishmaydigan, bir tekislikdagi ikki to‘g‘ri chiziq qanday ataladi?"]), "Parallel", ["Bir tekislikda kesishmaydigan chiziqlar parallel deyiladi."], noto=["Perpendikulyar", "Kesishuvchi", "Urinma"], tartib=False)


# ───────── M4-SHA: shakllar ─────────
@reg("M4-SHA", "yopiq")
def sha_perimetr(rng):
    a = rng.randint(4, 14); b = rng.randint(3, 10)
    q = _y(rng, f"To‘rtburchak shaklidagi daftar muqovasining uzunligi {a} sm, eni {b} sm. Uning perimetri necha sm?", 2 * (a + b), [f"Perimetr = 2 · (uzunlik + en) = 2 · ({a} + {b}) = {2 * (a + b)} sm."], noto=[a * b, a + b, 2 * a * b])
    q["rasm"] = fig_tortburchak(a, b, "sm"); return q


@reg("M4-SHA", "yopiq")
def sha_yuza(rng):
    a = rng.randint(3, 12); b = rng.randint(2, 9)
    q = _y(rng, f"To‘rtburchak shaklidagi sport maydonchasi {a} m uzunlikda, {b} m enda. Yuzi necha kvadrat metr?", a * b, [f"Yuza = uzunlik · en = {a} · {b} = {a * b} m²."], noto=[2 * (a + b), a + b, a * b + a])
    q["rasm"] = fig_tortburchak(a, b, "m"); return q


@reg("M4-SHA", "yopiq")
def sha_kub(rng):
    f, n, t = rng.choice([("yoqlari", 6, "kub"), ("qirralari", 12, "kub"), ("uchlari", 8, "kub"), ("yoqlari", 5, "kvadrat asosli piramida"), ("uchlari", 4, "uchburchakli piramida (tetraedr)")])
    return _y(rng, f"{t.capitalize()}ning nechta {f} bor?", n, [f"{t.capitalize()}ning {f} soni {n} ta."], noto=[n + 2, n - 2 if n > 4 else n + 4, 2 * n])


@reg("M4-SHA", "yopiq")
def sha_simmetriya(rng):
    s, n = rng.choice([("Kvadrat", 4), ("To‘rtburchak (kvadrat bo‘lmagan)", 2), ("Teng tomonli uchburchak", 3), ("Doira", "cheksiz ko‘p")])
    if isinstance(n, str):
        return _yopiq(rng, f"{s}ning nechta simmetriya o‘qi bor?", n, ["Doira istalgan diametr bo‘yicha simmetrik."], noto=["1", "2", "4"], tartib=False)
    return _y(rng, f"{s}ning nechta simmetriya o‘qi bor?", n, [f"{s}da {n} ta simmetriya o‘qi bor."], noto=[n + 1, n + 2, n - 1 if n > 1 else 5])


@reg("M4-SHA", "ochiq")
def sha_kvadrat(rng):
    a = rng.randint(3, 12)
    q = _o(f"Kvadrat shaklidagi gilam tomoni {a} dm.", [("a) Perimetri necha dm?", 4 * a), ("b) Yuzi necha dm²?", a * a)], [f"a) 4 · {a} = {4 * a} dm.", f"b) {a} · {a} = {a * a} dm²."])
    q["rasm"] = fig_tortburchak(a, a, "dm"); return q


@reg("M4-SHA", "ochiq")
def sha_plitka(rng):
    a = rng.choice([4, 6, 8]); b = rng.choice([3, 5, 6]); 
    return _o(f"Uzunligi {a} m va eni {b} m bo‘lgan xonaning polini yuzi 1 m² bo‘lgan kvadrat plitkalar bilan qoplash kerak.", [("a) Nechta plitka kerak?", a * b), ("b) Har plitka 12 ming so‘m bo‘lsa, jami necha ming so‘m?", a * b * 12)], [f"a) {a} · {b} = {a * b} ta.", f"b) {a * b} · 12 = {a * b * 12} ming so‘m."])


@reg("M4-SHA", "ochiq")
def sha_tomon(rng):
    p = rng.choice([24, 28, 32, 40]); 
    return _o(f"Kvadratning perimetri {p} sm.", [("a) Uning tomoni necha sm?", p // 4), ("b) Yuzi necha sm²?", (p // 4) ** 2)], [f"a) {p} ÷ 4 = {p // 4} sm.", f"b) {p // 4} · {p // 4} = {(p // 4) ** 2} sm²."])


# ───────── M4-OQI: diagramma va jadvallarni o‘qish ─────────
MEV = ["Olma", "Nok", "Uzum", "Banan", "Shaftoli"]


def _mev(rng):
    return [rng.randint(3, 20) * 2 for _ in range(5)]


@reg("M4-OQI", "yopiq")
def oqi_eng(rng):
    v = _mev(rng); i = v.index(max(v))
    q = _yopiq(rng, "Diagrammada sinfdoshlarning sevimli mevasi ko‘rsatilgan. Qaysi meva eng ko‘p tanlangan?", MEV[i], ["Eng baland ustunni topamiz.", f"Eng baland ustun — {MEV[i]} ({v[i]})."], noto=[x for x in MEV if x != MEV[i]][:3], tartib=False)
    q["rasm"] = fig_stolbik(MEV, v, "Sevimli meva (o‘quvchilar)"); return q


@reg("M4-OQI", "yopiq")
def oqi_farq(rng):
    v = _mev(rng); i, j = rng.sample(range(5), 2)
    q = _y(rng, f"Diagrammaga qarang. {MEV[i]}ni tanlaganlar {MEV[j]}ni tanlaganlardan necha kishiga {'ko‘p' if v[i] > v[j] else 'kam'}?", abs(v[i] - v[j]), [f"{MEV[i]}: {v[i]}, {MEV[j]}: {v[j]}.", f"Farq: {max(v[i], v[j])} − {min(v[i], v[j])} = {abs(v[i] - v[j])}."], noto=[v[i] + v[j], abs(v[i] - v[j]) + 2, abs(v[i] - v[j]) + 4])
    q["rasm"] = fig_stolbik(MEV, v, "Sevimli meva (o‘quvchilar)"); return q


@reg("M4-OQI", "yopiq")
def oqi_jami(rng):
    v = _mev(rng)
    q = _y(rng, "Diagrammada ko‘rsatilgan barcha o‘quvchilar soni nechta?", sum(v), [" + ".join(map(str, v)) + f" = {sum(v)}."], noto=[sum(v) - 2, sum(v) + 4, max(v) * 5])
    q["rasm"] = fig_stolbik(MEV, v, "Sevimli meva (o‘quvchilar)"); return q


@reg("M4-OQI", "ochiq")
def oqi_ochiq(rng):
    v = _mev(rng); i, j = rng.sample(range(5), 2)
    q = _o("Diagrammada bir haftada kutubxonadan olingan kitoblar (mevalar nomi shartli).", [(f"a) {MEV[i]} va {MEV[j]} ustunlari qiymatlari yig‘indisi nechaga teng?", v[i] + v[j]), ("b) Eng baland va eng past ustun orasidagi farq nechaga teng?", max(v) - min(v))],
           [f"a) {v[i]} + {v[j]} = {v[i] + v[j]}.", f"b) {max(v)} − {min(v)} = {max(v) - min(v)}."])
    q["rasm"] = fig_stolbik(MEV, v, "Diagramma"); return q


@reg("M4-OQI", "ochiq")
def oqi_jadval(rng):
    a, b, c = rng.randint(5, 20), rng.randint(5, 20), rng.randint(5, 20)
    return _o(f"Jadvalda 4-sinfning uch guruhi to‘plagan makulatura (kg): 4-A — {a}, 4-B — {b}, 4-V — {c}.", [("a) Hammasi bo‘lib necha kg yig‘ilgan?", a + b + c), ("b) Eng ko‘p to‘plagan guruh kamida nechta kg to‘plagan? (eng katta son)", max(a, b, c))], [f"a) {a} + {b} + {c} = {a + b + c}.", f"b) Eng katta son: {max(a, b, c)}."])


@reg("M4-OQI", "ochiq")
def oqi_piktogramma(rng):
    k = rng.choice([2, 5, 10]); n = [rng.randint(2, 7) for _ in range(3)]
    return _o(f"Piktogrammada 1 ta belgi {k} ta kitobni bildiradi. Dushanba — {n[0]} belgi, Seshanba — {n[1]} belgi, Chorshanba — {n[2]} belgi.", [("a) Seshanba kuni nechta kitob?", n[1] * k), ("b) Uch kunda jami nechta kitob?", sum(n) * k)], [f"a) {n[1]} · {k} = {n[1] * k}.", f"b) ({n[0]} + {n[1]} + {n[2]}) · {k} = {sum(n) * k}."])


# ───────── M4-TAS: ma'lumotlarni tartiblash va tasvirlash ─────────
@reg("M4-TAS", "yopiq")
def tas_sanash(rng):
    n = rng.randint(7, 19)
    belg = "".join("||||/ " if False else "" for _ in range(0))
    t = ("𝍸 " * (n // 5)).strip() + (" " if n // 5 and n % 5 else "") + "|" * (n % 5)
    return _y(rng, f"Sanash belgilari (har 𝍸 — 5 ta, | — 1 ta): {t}. Hammasi nechta?", n, [f"{n // 5} ta beshlik = {n // 5 * 5} va {n % 5} ta alohida chiziq.", f"{n // 5 * 5} + {n % 5} = {n}."], noto=[n + 1, n - 1, n // 5 + n % 5])


@reg("M4-TAS", "yopiq")
def tas_moda(rng):
    xs = [rng.choice([1, 2, 3, 4, 5]) for _ in range(9)]; 
    from collections import Counter
    c = Counter(xs)
    while sorted(c.values())[-1] == (sorted(c.values())[-2] if len(c) > 1 else 0):
        xs = [rng.choice([1, 2, 3, 4, 5]) for _ in range(9)]; c = Counter(xs)
    m = c.most_common(1)[0][0]
    return _y(rng, f"O‘quvchilar olgan baholar: {', '.join(map(str, xs))}. Qaysi baho eng ko‘p uchraydi?", m, [f"Har bahoni sanaymiz: " + ", ".join(f"{k}: {v} marta" for k, v in sorted(c.items())) + ".", f"Eng ko‘p — {m}."], noto=[x for x in range(1, 6) if x != m][:3])


@reg("M4-TAS", "yopiq")
def tas_ortacha(rng):
    m = rng.choice([4, 5, 6, 7, 8]); xs = [m + rng.randint(-2, 2) for _ in range(3)]; xs.append(m * 4 - sum(xs))
    return _y(rng, f"To‘rt kunda sotilgan gazetalar soni: {', '.join(map(str, xs))}. O‘rtacha necha dona?", m, [f"Yig‘indi: {sum(xs)}.", f"{sum(xs)} ÷ 4 = {m}."], noto=[max(xs), min(xs), m + 1])


@reg("M4-TAS", "ochiq")
def tas_toldir(rng):
    a, b, c = [rng.randint(5, 15) for _ in range(3)]; T = a + b + c + rng.randint(3, 10)
    return _o(f"Sinfda {T} o‘quvchi bor. Ularning sevimli rangi: qizil — {a}, ko‘k — {b}, yashil — {c}, qolganlari sariqni yoqtiradi.", [("a) Sariqni yoqtiradiganlar necha kishi?", T - a - b - c), ("b) Qaysi rang eng ko‘p tanlangan? Shu rangni tanlaganlar sonini yozing.", max(a, b, c, T - a - b - c))],
              [f"a) {T} − ({a} + {b} + {c}) = {T - a - b - c}.", f"b) Eng katta son: {max(a, b, c, T - a - b - c)}."])


@reg("M4-TAS", "ochiq")
def tas_ustun(rng):
    v = [rng.randint(2, 9) * 5 for _ in range(4)]; n = ["Du", "Se", "Chor", "Pay"]
    q = _o("Diagrammada 4 kunlik sotilgan non soni ko‘rsatilgan.", [("a) 4 kunda jami nechta non sotilgan?", sum(v)), ("b) Eng kam sotilgan kunda nechta non sotilgan?", min(v))], [f"a) {' + '.join(map(str, v))} = {sum(v)}.", f"b) Eng kichik qiymat: {min(v)}."])
    q["rasm"] = fig_stolbik(n, v, "Sotilgan non"); return q


@reg("M4-TAS", "ochiq")
def tas_so_rov(rng):
    a, b = rng.randint(8, 20), rng.randint(8, 20)
    return _o(f"So‘rovda «Futbol» ga {a} kishi, «Voleybol» ga {b} kishi ovoz berdi.", [("a) Ovoz berganlar jami necha kishi?", a + b), ("b) Futbol voleybolga qaraganda necha ovoz ko‘p yoki kam? (farqni yozing)", abs(a - b))], [f"a) {a} + {b} = {a + b}.", f"b) |{a} − {b}| = {abs(a - b)}."])


@reg("M4-TAS", "yopiq")
def tas_tanlash(rng):
    return _yopiq(rng, rng.choice(["Sinfdagi o‘quvchilarning bo‘y uzunligi vaqt o‘tishi bilan o‘zgarishini ko‘rsatish uchun qaysi diagramma qulay?", "Bir yil davomida harorat o‘zgarishini ko‘rsatish uchun qaysi diagramma qulay?"]), "Chiziqli grafik", ["Vaqt bo‘yicha o‘zgarish chiziqli grafikda yaxshi ko‘rinadi."], noto=["Faqat jadval", "Hech qaysi", "Doira rasm"], tartib=False)


TEMA = {
    "M4-NAT": _tema("M4-NAT", "Natural sonlar va amallar", "Son", "🔢", "Xona qiymati, to‘rt amal, yaxlitlash va ko‘p qadamli masalalar", [
        _d("Xonalar", "1 248 = 1 ming + 2 yuz + 4 o‘n + 8 bir\nRaqam turgan o‘rniga qarab qiymat oladi", "Natural sonlar xonalarga ajraladi: birlik, o‘nlik, yuzlik, minglik. Bir xil raqam turgan joyiga qarab har xil qiymatga ega bo‘ladi."),
        _d("Amallar", "Qo‘shish: xonama-xona\nKo‘paytirish: qatorlar · har qatordagi\nBo‘lish: qoldiq doim bo‘luvchidan kichik", "Qo‘shishda xonama-xona, o‘ngdan chapga ketamiz. Ko‘paytirish — teng guruhlarni qo‘shish. Bo‘lishda qoldiq doim bo‘luvchidan kichik bo‘ladi."),
        _d("Yaxlitlash", "O‘nlar xonasi ≥ 5 → yuqoriga\nO‘nlar xonasi < 5 → pastga", "Yuzlikkacha yaxlitlashda o‘nliklarga qaraymiz: besh yoki undan katta bo‘lsa yuqoriga, kichik bo‘lsa pastga yaxlitlaymiz.")]),
    "M4-KAS": _tema("M4-KAS", "Kasrlar va o‘nli kasrlar", "Son", "🍕", "Butunning qismi, kasrlarni taqqoslash, o‘nli kasrlar bilan amallar", [
        _d("Kasr — butunning qismi", "a/b: butun b ta teng qism, a tasi olingan\nSondan a/b qismi: (son ÷ b) · a", "Kasr butunning teng qismlarini bildiradi. Maxraj — butun nechta teng qismga bo‘linganini, surat — nechta qismi olinganini ko‘rsatadi. Sondan kasr qismini topish uchun avval maxrajga bo‘lamiz, keyin suratga ko‘paytiramiz."),
        _d("Taqqoslash", "Maxraji bir xil: surati kattasi katta\n1/2 = 0,5   1/4 = 0,25   3/4 = 0,75", "Maxrajlari bir xil kasrlarda surati katta bo‘lgani kattaroq. Yarim — nol butun besh o‘ndan, chorak — nol butun yigirma besh yuzdan."),
        _d("O‘nli kasrlar", "Qo‘shishda vergul ostiga vergul\n2,5 + 1,75 = 4,25", "O‘nli kasrlarni qo‘shganda vergulni vergul ostiga yozamiz va xonama-xona qo‘shamiz.")]),
    "M4-TEN": _tema("M4-TEN", "Sonli tengliklar va noma’lum son", "Algebra", "⚖️", "Noma’lum qo‘shiluvchi, ko‘paytuvchi, tarozi va teskari amallar", [
        _d("Tenglik — muvozanat", "□ + 7 = 15\nBir tomonga nima qilsak, ikkinchisiga ham", "Tenglik tarozining ikki pallasidek muvozanatda turadi. Noma’lumni topishda teskari amaldan foydalanamiz."),
        _d("Teskari amallar", "Qo‘shish ↔ ayirish\nKo‘paytirish ↔ bo‘lish\n□ + 7 = 15 → □ = 15 − 7 = 8", "Qo‘shishning teskarisi — ayirish, ko‘paytirishning teskarisi — bo‘lish. Noma’lum qo‘shiluvchi yig‘indidan ma’lum qo‘shiluvchini ayirib topiladi.")]),
    "M4-QON": _tema("M4-QON", "Qonuniyatlar va bog‘lanishlar", "Algebra", "🔁", "Sonlar va shakllar qatoridagi qoidani topish", [
        _d("Qoidani topamiz", "2, 5, 8, 11, □\nFarq: +3 → □ = 14", "Qonuniyatni topish uchun qo‘shni sonlar farqini hisoblaymiz. Farq bir xil bo‘lsa, shuncha qo‘shib yoki ayirib borilgan."),
        _d("Sonli mashina", "kirish → qoida → chiqish\n1 → 5, 2 → 8, 3 → 11\nqoida: · 3 + 2", "Sonli mashinada har kirish soni bir xil qoida bilan o‘zgaradi. Bir nechta juftlikdan qoidani topamiz va yangi sonlarga qo‘llaymiz.")]),
    "M4-NUQ": _tema("M4-NUQ", "Nuqta, chiziq va burchaklar", "Geometriya", "📐", "Burchak turlari, parallel va perpendikulyar chiziqlar, soat burchagi", [
        _d("Burchak turlari", "O‘tkir < 90°\nTo‘g‘ri = 90°\nO‘tmas: 90° < burchak < 180°\nYoyiq = 180°", "Burchaklar kattaligiga qarab turlanadi: o‘tkir, to‘g‘ri, o‘tmas va yoyiq."),
        _d("Parallel va perpendikulyar", "Parallel: kesishmaydi\nPerpendikulyar: 90° da kesishadi\nSoat: 1 soat bo‘lagi = 30°", "Bir tekislikda kesishmaydigan chiziqlar parallel, to‘g‘ri burchak ostida kesishganlari perpendikulyar. Soat siferblatida har soat bo‘lagi o‘ttiz gradus.")]),
    "M4-SHA": _tema("M4-SHA", "Tekis va fazoviy shakllar", "Geometriya", "🔷", "Perimetr, yuza, kub va piramida elementlari, simmetriya", [
        _d("Perimetr va yuza", "To‘rtburchak: P = 2(a + b)\nYuza: S = a · b\nKvadrat: P = 4a, S = a · a", "Perimetr — barcha tomonlar yig‘indisi, yuza — shakl egallagan joy. To‘rtburchak perimetri ikki marta uzunlik va en yig‘indisi, yuzi esa ularning ko‘paytmasi."),
        _d("Fazoviy shakllar", "Kub: 6 yoq, 12 qirra, 8 uch\nSimmetriya o‘qi: shaklni teng ikkiga buklaydi", "Kubning oltita yog‘i, o‘n ikkita qirrasi va sakkizta uchi bor. Simmetriya o‘qi shaklni ustma-ust tushadigan ikki qismga bo‘ladi.")]),
    "M4-OQI": _tema("M4-OQI", "Diagramma va jadvallarni o‘qish", "Ma’lumotlar", "📊", "Ustunli diagramma, piktogramma va jadvaldan ma’lumot topish", [
        _d("Diagrammani o‘qish", "1) Sarlavha  2) O‘qlar  3) Ustun balandligi = qiymat\nFarq = katta − kichik", "Diagrammada avval sarlavhani, keyin o‘qlarni o‘qiymiz. Ustun balandligi qiymatni bildiradi. Ikki ustun farqi — kattasidan kichigini ayirish."),
        _d("Piktogramma", "1 belgi = k ta\nBelgilar soni · k = jami", "Piktogrammada har bir belgi ma’lum sonni bildiradi. Belgilar sonini shu songa ko‘paytiramiz.")]),
    "M4-TAS": _tema("M4-TAS", "Ma’lumotlarni tartiblash va tasvirlash", "Ma’lumotlar", "🗂️", "Sanash belgilari, moda, o‘rtacha va mos diagrammani tanlash", [
        _d("Sanash va jadval", "𝍸 = 5 ta, | = 1 ta\nModa — eng ko‘p uchraydigan qiymat", "Ma’lumotlarni sanash belgilari bilan sanaymiz: beshta chiziq bitta dasta. Eng ko‘p uchraydigan qiymat modadir."),
        _d("O‘rtacha", "O‘rtacha = yig‘indi ÷ soni\nVaqt bo‘yicha o‘zgarish → chiziqli grafik", "O‘rtacha son — hamma sonlar yig‘indisini ularning soniga bo‘lish. Vaqt davomida o‘zgarishni chiziqli grafik yaxshi ko‘rsatadi.")]),
}
