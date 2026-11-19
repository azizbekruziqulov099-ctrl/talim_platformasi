"""PISA matematika — kengaytma 3: Pifagor, burchak, trigonometriya, statistika, ehtimollik, sanash, moliya (chizmali)."""
import math
from fractions import Fraction

from modules.pisa_mat_g import reg, num, som, _y, _o, fig_narvon, fig_stolbik, fig_pie, fig_poliliniya
from modules.mock_fig import _svg, _t, _l, _poly

TOP = "P_M"
TEMA = {}
_SOHA = {"PM-10": "Fazo va shakl", "PM-11": "Noaniqlik va ma’lumot", "PM-12": "Noaniqlik va ma’lumot", "PM-13": "Miqdor"}
_ESKI = {"PM-10": "PM-FAZ", "PM-11": "PM-NOA", "PM-12": "PM-NOA", "PM-13": "PM-MIQ"}


def tema(kod, kb, nom, belgi, maqsad, dars):
    TEMA[kod] = {"nom": nom, "soha": _SOHA[kb], "belgi": belgi, "maqsad": maqsad, "bolim": _ESKI[kb], "kb": kb, "toplam": TOP,
                 "dars": [{"sarlavha": a, "doska": b, "ovoz": c} for a, b, c in dars]}


sh = reg


def rasmli(q, svg):
    q["rasm"] = svg
    return q


def fig_uchburchak(a, b, c, nomlar=("A", "B", "C"), burchak=None):
    """To‘g‘ri burchakli uchburchak: katetlar a (gorizontal), b (vertikal), gipotenuza c; to‘g‘ri burchak chap-pastda."""
    s = min(200 / a, 130 / b); x0, y0 = 40, 160
    C = (x0, y0); B = (x0 + a * s, y0); A = (x0, y0 - b * s)
    body = _poly([C, B, A], fill="#eef5ff") + f'<path d="M{C[0] + 10},{C[1]} v-10 h-10" fill="none" stroke="#111"/>'
    body += _t((C[0] + B[0]) / 2, y0 + 16, f"{num(a)}", it=False, size=12) + _t(x0 - 8, (C[1] + A[1]) / 2 + 4, f"{num(b)}", it=False, anchor="end", size=12) + _t((A[0] + B[0]) / 2 + 12, (A[1] + B[1]) / 2 - 6, f"{num(c) if c is not None else '?'}", it=False, size=12)
    return _svg(body, 280, 190)


def fig_burchak(grad, sarlavha=""):
    r = 80; cx, cy = 60, 140; a = math.radians(grad)
    body = _l((cx, cy), (cx + r * 1.4, cy), w=2) + _l((cx, cy), (cx + r * 1.4 * math.cos(a), cy - r * 1.4 * math.sin(a)), w=2)
    body += f'<path d="M{cx + 30},{cy} A30,30 0 0 0 {cx + 30 * math.cos(a):.1f},{cy - 30 * math.sin(a):.1f}" fill="none" stroke="#d33" stroke-width="2"/>' + _t(cx + 48, cy - 10, f"{grad}°", it=False, size=13)
    return _svg(body, 260, 170)


# ═════════ 10-BO'LIM · GEOMETRIYA ═════════
tema("pm_pifagor", "PM-10", "Pifagor teoremasi: narvon, diagonal, masofa", "📐", "To‘g‘ri burchakli uchburchakda tomonlarni topish; narvon, ekran diagonali, eng qisqa yo‘l", [
    ("Pifagor teoremasi", "a² + b² = c²\n3² + 4² = 5²\nc — gipotenuza (eng uzun tomon)",
     "To‘g‘ri burchakli uchburchakda katetlar kvadratlarining yig‘indisi gipotenuza kvadratiga teng. Uch kvadrat plyus to‘rt kvadrat — besh kvadrat: to‘qqiz plyus o‘n olti, yigirma besh."),
    ("Narvon va devor", "Narvon uzunligi = gipotenuza\n13² = 5² + x² → x = 12\nx² = c² − a²",
     "Devorga suyalgan narvon to‘g‘ri burchakli uchburchak hosil qiladi. Narvon uzunligi gipotenuza. Katetni topish uchun gipotenuza kvadratidan ma’lum katet kvadratini ayiramiz."),
    ("Pifagor uchliklari", "3, 4, 5   5, 12, 13   8, 15, 17   7, 24, 25\nBularni yodlab oling",
     "Ba’zi uchburchaklarning tomonlari butun sonlardan iborat: uch to‘rt besh, besh o‘n ikki o‘n uch, sakkiz o‘n besh o‘n yetti. Ularni bilsangiz, ildiz chiqarmay yechasiz."),
])

_UCH = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (6, 8, 10), (9, 12, 15), (20, 21, 29), (12, 16, 20), (15, 20, 25), (10, 24, 26), (15, 36, 39), (16, 30, 34), (21, 28, 35), (12, 35, 37), (9, 40, 41), (18, 24, 30), (30, 40, 50), (24, 32, 40), (28, 45, 53), (11, 60, 61)]


@sh("pm_pifagor", "yopiq")
def pm_pi_1(rng):
    a, b, c = rng.choice(_UCH)
    return rasmli(_y(rng, f"To‘g‘ri burchakli uchburchakning katetlari {a} sm va {b} sm. Gipotenuzasi necha sm?", c, [f"c² = {a}² + {b}² = {a * a} + {b * b} = {c * c} → c = {c}."], noto=[a + b, c + 2, c - 1]), fig_uchburchak(a, b, None))


@sh("pm_pifagor", "yopiq")
def pm_pi_2(rng):
    a, b, c = rng.choice(_UCH)
    return rasmli(_y(rng, f"{c} m uzunlikdagi narvon devorga suyalgan; uning quyi uchi devordan {a} m uzoqlikda. Narvon devorning necha metr balandligiga yetadi?", b, [f"x² = {c}² − {a}² = {c * c} − {a * a} = {b * b} → x = {b}."], noto=[c - a, a + b, b + 2]), fig_uchburchak(a, b, c))


@sh("pm_pifagor", "yopiq")
def pm_pi_3(rng):
    a, b, c = rng.choice([(3, 4, 5), (6, 8, 10), (9, 12, 15), (12, 16, 20), (15, 20, 25), (5, 12, 13), (8, 15, 17)])
    return _y(rng, f"Televizor ekrani eni {a} dm, bo‘yi {b} dm. Diagonali necha dm?", c, [f"d = √({a}² + {b}²) = √{a * a + b * b} = {c}."], noto=[a + b, c + 1, c - 2, c + 3])


@sh("pm_pifagor", "yopiq")
def pm_pi_4(rng):
    a, b, c = rng.choice(_UCH); 
    return _y(rng, f"Maydon bo‘ylab to‘g‘ri yo‘l {a} m sharqqa, so‘ng {b} m shimolga. To‘g‘ri chiziq bo‘ylab boshlang‘ich nuqtagacha masofa necha metr?", c, [f"c = √({a}² + {b}²) = {c}. Yo‘l {a + b} m, to‘g‘ri chiziqda esa {c} m — qisqaroq."], noto=[a + b, c + 3, b - a if b > a else a + 2])


@sh("pm_pifagor", "ochiq")
def pm_pi_5(rng):
    a, b, c = rng.choice(_UCH)
    return rasmli(_o(f"Bog‘ to‘g‘ri to‘rtburchak shaklida: eni {a} m, bo‘yi {b} m. Siz bir burchakdan qarama-qarshi burchakka to‘g‘ri chiziq bo‘ylab yurasiz.", [("a) Diagonal uzunligi (m):", c), ("b) Chetidan yursangiz (eni + bo‘yi) necha metr ko‘p yurasiz?", a + b - c)], [f"a) √({a * a} + {b * b}) = {c} m.", f"b) {a} + {b} − {c} = {a + b - c} m."]), fig_uchburchak(a, b, c))


@sh("pm_pifagor", "ochiq")
def pm_pi_6(rng):
    a, b, c = rng.choice(_UCH)
    return _o(f"Ustun balandligi {b} m. Uni tutib turuvchi tros ustun uchidan yerga {a} m uzoqlikdagi nuqtaga tortilgan.", [("a) Tros uzunligi (m):", c), ("b) Ikkita shunday tros kerak bo‘lsa, jami uzunlik (m):", 2 * c)], [f"a) √({b}² + {a}²) = {c}.", f"b) 2·{c} = {2 * c}."])


@sh("pm_pifagor", "ochiq")
def pm_pi_7(rng):
    a, b, c = rng.choice(_UCH)
    return _o(f"To‘g‘ri burchakli uchburchak gipotenuzasi {c} sm, bir kateti {a} sm.", [("a) Ikkinchi katet (sm):", b), ("b) Uchburchak yuzi (sm²):", Fraction(a * b, 2))], [f"a) √({c}² − {a}²) = √{b * b} = {b}.", f"b) ½·{a}·{b} = {num(Fraction(a * b, 2))}."])


tema("pm_burchak", "PM-10", "Burchaklar: uchburchak, parallel chiziqlar, ko‘pburchak", "📏", "Burchaklar yig‘indisi, qo‘shni va vertikal burchaklar, ko‘pburchak ichki burchaklari", [
    ("Uchburchak burchaklari", "∠A + ∠B + ∠C = 180°\nTo‘g‘ri uchburchakda: 90° + α + β = 180°\nTashqi burchak = qolgan ikkitasi yig‘indisi",
     "Har qanday uchburchakda ichki burchaklar yig‘indisi bir yuz sakson daraja. To‘g‘ri burchakli uchburchakda ikkita o‘tkir burchak yig‘indisi to‘qson daraja."),
    ("Qo‘shni va vertikal", "Qo‘shni: α + β = 180°\nVertikal burchaklar teng\nParallel chiziqlar: mos burchaklar teng",
     "Ikki chiziq kesishganda qo‘shni burchaklar yig‘indisi yuz sakson daraja, vertikal burchaklar esa o‘zaro teng. Parallel chiziqlarni kesuvchi hosil qilgan mos burchaklar ham teng."),
    ("Ko‘pburchak", "n-burchak ichki burchaklar yig‘indisi = (n − 2)·180°\nTo‘rtburchak: 360°\nBeshburchak: 540°",
     "Ko‘pburchakni uchburchaklarga bo‘lsak, n-burchakda n minus ikkita uchburchak chiqadi. Ichki burchaklar yig‘indisi shuncha marta yuz sakson daraja."),
])


@sh("pm_burchak", "yopiq")
def pm_bu_1(rng):
    a = rng.randint(30, 80); b = rng.randint(30, 80)
    return _y(rng, f"Uchburchakning ikki burchagi {a}° va {b}°. Uchinchi burchak necha gradus?", 180 - a - b, [f"180 − {a} − {b} = {180 - a - b}°."], noto=[a + b, 90 - a, 180 - a])


@sh("pm_burchak", "yopiq")
def pm_bu_2(rng):
    a = rng.randint(20, 160)
    return rasmli(_y(rng, f"Ikki chiziq kesishganda hosil bo‘lgan burchaklardan biri {a}°. Unga qo‘shni burchak necha gradus?", 180 - a, [f"Qo‘shni burchaklar yig‘indisi 180°: 180 − {a} = {180 - a}°."], noto=[a, 90 - a if a < 90 else a - 90, 360 - a]), fig_burchak(a))


@sh("pm_burchak", "yopiq")
def pm_bu_3(rng):
    n = rng.choice([5, 6, 8, 10, 12]); 
    return _y(rng, f"{n} burchakli qavariq ko‘pburchak ichki burchaklari yig‘indisi necha gradus?", (n - 2) * 180, [f"({n} − 2)·180 = {(n - 2) * 180}°."], noto=[n * 180, (n - 1) * 180, (n - 3) * 180])


@sh("pm_burchak", "yopiq")
def pm_bu_4(rng):
    a = rng.randint(20, 70)
    return _y(rng, f"To‘g‘ri burchakli uchburchakning o‘tkir burchaklaridan biri {a}°. Ikkinchi o‘tkir burchagi necha gradus?", 90 - a, [f"90 − {a} = {90 - a}°."], noto=[180 - a, 90 + a, a])


@sh("pm_burchak", "ochiq")
def pm_bu_5(rng):
    a = rng.randint(40, 80); b = rng.randint(40, 80)
    return _o(f"Uchburchakning ikki burchagi {a}° va {b}°.", [("a) Uchinchi burchak (°):", 180 - a - b), ("b) Unga qo‘shni (tashqi) burchak (°):", a + b)], [f"a) 180 − {a} − {b} = {180 - a - b}.", f"b) Tashqi burchak = {a} + {b} = {a + b}."])


@sh("pm_burchak", "ochiq")
def pm_bu_6(rng):
    n = rng.choice([5, 6, 8, 9, 10]); S = (n - 2) * 180
    return _o(f"Muntazam {n} burchakli shakl (barcha burchaklari teng).", [("a) Ichki burchaklar yig‘indisi (°):", S), ("b) Bitta ichki burchak (°):", Fraction(S, n))], [f"a) ({n} − 2)·180 = {S}.", f"b) {S} : {n} = {num(Fraction(S, n))}."])


@sh("pm_burchak", "ochiq")
def pm_bu_7(rng):
    a = rng.randint(30, 70)
    return _o(f"Ikki parallel to‘g‘ri chiziqni kesuvchi hosil qilgan mos burchaklardan biri {a}°.", [("a) Unga mos burchak (°):", a), ("b) Qo‘shni (bir tomonli ichki) burchak (°):", 180 - a)], [f"a) Mos burchaklar teng: {a}°.", f"b) 180 − {a} = {180 - a}°."])


tema("pm_trig", "PM-10", "Sinus, kosinus, tangens: balandlik o‘lchash", "🏔️", "To‘g‘ri burchakli uchburchakda nisbatlar; soya, tog‘, daraxt va binoning balandligi", [
    ("Nisbatlar", "sin α = qarshi katet / gipotenuza\ncos α = yonidagi katet / gipotenuza\ntg α = qarshi / yonidagi",
     "To‘g‘ri burchakli uchburchakda burchakning sinusi — qarshisidagi katetning gipotenuzaga nisbati. Kosinus — yonidagi katetning gipotenuzaga nisbati. Tangens — qarshi katetning yonidagi katetga nisbati."),
    ("Mashhur qiymatlar", "30°: sin = 0,5\n45°: tg = 1\n60°: sin = √3/2 ≈ 0,87",
     "O‘ttiz darajaning sinusi yarimga teng. Qirq besh darajaning tangensi birga teng. Oltmish darajaning sinusi taxminan nol butun sakson yetti."),
    ("Balandlikni o‘lchash", "h = soya · tg α\nBurchak 45° → h = soya\nKuzatuvchi bo‘yini unutmang",
     "Daraxt balandligini o‘lchash uchun uning soyasi uzunligini va quyosh nurining yer bilan hosil qilgan burchagini bilish kifoya. Balandlik soyaga burchak tangensini ko‘paytirib topiladi."),
])


@sh("pm_trig", "yopiq")
def pm_tr_1(rng):
    s = rng.choice([6, 8, 10, 12, 20])
    return rasmli(_y(rng, f"Quyosh nurlari yer bilan 45° burchak hosil qilganda daraxt soyasi {s} m. Daraxt balandligi necha metr?", s, [f"tg 45° = 1 → h = {s}·1 = {s} m."], noto=[s * 2, s // 2, s + 5]), fig_burchak(45))


@sh("pm_trig", "yopiq")
def pm_tr_2(rng):
    c = rng.choice([10, 12, 20, 30, 40])
    return rasmli(_y(rng, f"To‘g‘ri burchakli uchburchakda gipotenuza {c} sm, bir o‘tkir burchak 30°. Shu burchak qarshisidagi katet necha sm? (sin 30° = 0,5)", Fraction(c, 2), [f"qarshi katet = c·sin30° = {c}·0,5 = {num(Fraction(c, 2))}."], noto=[c, Fraction(c * 87, 100), c * 2]), fig_burchak(30))


@sh("pm_trig", "yopiq")
def pm_tr_3(rng):
    a, b, c = rng.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13)])
    return rasmli(_y(rng, f"To‘g‘ri burchakli uchburchak katetlari {a} va {b}, gipotenuza {c}. {a} li katet qarshisidagi burchakning sinusi qancha?", f"${a}/{c}$", [f"sin = qarshi/gipotenuza = {a}/{c}."], noto=[f"${b}/{c}$", f"${a}/{b}$", f"${c}/{a}$"]), fig_uchburchak(b, a, c))


@sh("pm_trig", "yopiq")
def pm_tr_4(rng):
    h = rng.choice([30, 45, 60, 75]); 
    return _y(rng, f"Binoga 45° burchak ostida qaralganda, binodan {h} m uzoqlikdan kuzatuvchi ko‘zi darajasidan boshlab bino balandligi necha metr (kuzatuvchi bo‘yi hisobga olinmaydi)?", h, [f"tg 45° = 1 → h = {h}·1 = {h} m."], noto=[h * 2, h // 2, h + 10])


@sh("pm_trig", "ochiq")
def pm_tr_5(rng):
    s = rng.choice([12, 15, 20, 24]); 
    return _o(f"45° burchak ostida tushayotgan quyosh nuri: daraxt soyasi {s} m, uning yonidagi {s // 3} m tayoq soyasi shunga mos.", [("a) Daraxt balandligi (m):", s), ("b) Tayoq balandligi (m):", s // 3)], [f"a) tg 45° = 1 → h = {s}.", f"b) Tayoq soyasi {s // 3} m → balandligi {s // 3} m."])


@sh("pm_trig", "ochiq")
def pm_tr_6(rng):
    c = rng.choice([10, 20, 30, 40])
    return _o(f"Qiya tom: uzunligi {c} m, gorizontal bilan 30° burchak hosil qiladi (sin 30° = 0,5).", [("a) Tom balandligi (m):", Fraction(c, 2)), ("b) Ikki shunday tom ketma-ket balandligi (m):", c)], [f"a) {c}·0,5 = {num(Fraction(c, 2))}.", f"b) 2·{num(Fraction(c, 2))} = {c}."])


@sh("pm_trig", "ochiq")
def pm_tr_7(rng):
    a, b, c = rng.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17)])
    return _o(f"To‘g‘ri burchakli uchburchakda katetlar {a} va {b}, gipotenuza {c}.", [(f"a) {a} li katet qarshisidagi burchak sinusi (o‘nli kasr, 2 xona):", round(a / c, 2)), (f"b) shu burchak tangensi (2 xona):", round(a / b, 2))], [f"a) {a}/{c} ≈ {num(Fraction(str(round(a / c, 2))))}.", f"b) {a}/{b} ≈ {num(Fraction(str(round(a / b, 2))))}."])


# ═════════ 11-BO'LIM · STATISTIKA ═════════
tema("pm_ortacha", "PM-11", "O‘rtacha, mediana, moda va tarqoqlik", "📊", "Ma’lumotlar to‘plamini bitta son bilan tavsiflash; qaysi o‘rtacha qachon to‘g‘ri", [
    ("O‘rtacha qiymat", "O‘rtacha = yig‘indi / soni\n4, 6, 8, 10 → 28/4 = 7\nO‘rtacha kutilmagan katta qiymatga sezgir",
     "O‘rtacha qiymat — barcha qiymatlar yig‘indisining ularning soniga bo‘linganidir. Bitta juda katta qiymat o‘rtachani ancha o‘zgartirib yuborishi mumkin."),
    ("Mediana va moda", "Mediana — tartiblangandagi o‘rtadagi qiymat\nModa — eng ko‘p takrorlangan qiymat\nJuft sondagi qiymatda: ikki o‘rtadagi o‘rtacha",
     "Mediana — qiymatlar o‘sish tartibida yozilganda o‘rtadagi son. Juft sonli qiymatlarda ikki o‘rtadagi sonning o‘rtachasi olinadi. Moda — eng ko‘p uchraydigan qiymat."),
    ("Qaysi biri?", "Maosh: mediana ko‘pincha to‘g‘ri\nDo‘kon eng ko‘p sotgan o‘lcham: moda\nBahoning o‘rtachasi: o‘rtacha",
     "Maoshlarda bir nechta juda katta maosh o‘rtachani oshirib yuboradi, shuning uchun mediana adolatliroq. Do‘konga qaysi o‘lcham ko‘proq kerakligini moda ko‘rsatadi."),
])


@sh("pm_ortacha", "yopiq")
def pm_or_1(rng):
    n = rng.choice([4, 5]); v = [rng.randint(3, 20) for _ in range(n - 1)]; m = rng.randint(4, 12); v.append(0)
    v[-1] = m * n - sum(v[:-1])
    if v[-1] < 1: v = [m] * n
    return _y(rng, f"Sonlar: {', '.join(map(str, v))}. O‘rtachasi nechaga teng?", Fraction(sum(v), n), [f"Yig‘indi {sum(v)}; soni {n}; {sum(v)} : {n} = {num(Fraction(sum(v), n))}."], noto=[Fraction(sum(v), n) + 1, max(v), sorted(v)[len(v) // 2] + 3])


@sh("pm_ortacha", "yopiq")
def pm_or_2(rng):
    v = sorted(rng.sample(range(2, 40), 5)); rng.shuffle(v)
    return _y(rng, f"Sonlar: {', '.join(map(str, v))}. Medianasi nechaga teng?", sorted(v)[2], [f"Tartiblaymiz: {', '.join(map(str, sorted(v)))}. O‘rtadagisi: {sorted(v)[2]}."], noto=[v[2] if v[2] != sorted(v)[2] else sorted(v)[1], sum(v) // 5 + 1, sorted(v)[3]])


@sh("pm_ortacha", "yopiq")
def pm_or_3(rng):
    m = rng.choice([5, 6, 7, 8]); v = [m] * 3 + [rng.choice([x for x in range(3, 12) if x != m]) for _ in range(3)]; rng.shuffle(v)
    return _y(rng, f"Qiymatlar: {', '.join(map(str, v))}. Modasi qaysi?", m, [f"{m} eng ko‘p (3 marta) uchraydi."], noto=[x for x in sorted(set(v)) if x != m][:3] + [m + 4])


@sh("pm_ortacha", "yopiq")
def pm_or_4(rng):
    mx = [rng.choice([3, 4, 5]) for _ in range(5)]; kat = rng.choice([60, 80, 100])
    return _y(rng, f"5 kishining maoshi (ming so‘m): {', '.join(str(x * 100) for x in mx[:4])} va bitta direktor {kat * 100}. Qaysi ko‘rsatkich ‘oddiy maosh’ni yaxshiroq ifodalaydi?", "Mediana", ["Bitta juda katta qiymat o‘rtachani oshirib yuboradi; mediana esa barqaror."], noto=["O‘rtacha", "Eng katta qiymat", "Yig‘indi"])


@sh("pm_ortacha", "ochiq")
def pm_or_5(rng):
    b = [rng.randint(3, 5) for _ in range(5)]; 
    return _o(f"Besh imtihon bahosi: {', '.join(map(str, b))}.", [("a) O‘rtacha baho (o‘nli kasr):", Fraction(sum(b), 5)), ("b) Mediana:", sorted(b)[2])], [f"a) {sum(b)} : 5 = {num(Fraction(sum(b), 5))}.", f"b) Tartib: {', '.join(map(str, sorted(b)))} → {sorted(b)[2]}."])


@sh("pm_ortacha", "ochiq")
def pm_or_6(rng):
    n = rng.choice([4, 5, 6]); m = rng.choice([70, 75, 80]); need = m + 2; tot = m * n
    return _o(f"{n} ta testdan o‘rtacha {m} ball oldingiz. Keyingi testdan o‘rtacha {need} ga yetishi uchun:", [(f"a) Hozirgi jami ball:", tot), ("b) Keyingi testda necha ball kerak?", need * (n + 1) - tot)], [f"a) {m}·{n} = {tot}.", f"b) {need}·{n + 1} − {tot} = {need * (n + 1) - tot}."])


@sh("pm_ortacha", "ochiq")
def pm_or_7(rng):
    v = sorted(rng.sample(range(10, 60), 6)); 
    med = Fraction(v[2] + v[3], 2)
    return _o(f"Oltita o‘quvchining bo‘yi (sm): {', '.join(map(str, [x + 100 for x in v]))}.", [("a) O‘rtacha bo‘y (sm):", Fraction(sum(v), 6) + 100), ("b) Mediana (sm):", med + 100)], [f"a) {sum(x + 100 for x in v)} : 6 = {num(Fraction(sum(v), 6) + 100)}.", f"b) Ikki o‘rtadagi: ({v[2] + 100} + {v[3] + 100})/2 = {num(med + 100)}."])


# ═════════ 12-BO'LIM · EHTIMOLLIK ═════════
tema("pm_ehtimol", "PM-12", "Ehtimollik: tanga, kub va qutidagi sharlar", "🎲", "Hodisa ehtimolini ‘qulay / barcha’ nisbati bilan topish; qarama-qarshi hodisa", [
    ("Klassik ehtimollik", "P = qulay natijalar / barcha natijalar\nTanga: P(gerb) = 1/2\nKub: P(6) = 1/6",
     "Ehtimollik — qulay natijalar sonining barcha teng imkoniyatli natijalar soniga nisbati. Tangani tashlaganda gerb kelishi ehtimoli yarim. O‘yin kubida oltita tushishi — oltidan bir."),
    ("Qarama-qarshi hodisa", "P(A emas) = 1 − P(A)\nSharlar: 3 qizil, 7 ko‘k → P(ko‘k) = 7/10\nEhtimol 0 dan 1 gacha",
     "Hodisa yuz bermasligi ehtimoli birdan hodisa ehtimolini ayirib topiladi. Ehtimol har doim nol bilan bir orasida. Nol — mumkin emas, bir — albatta."),
    ("Ikki mustaqil hodisa", "P(A va B) = P(A) · P(B)\nIkki marta gerb: 1/2 · 1/2 = 1/4\nKutilgan son = ehtimol · urinishlar",
     "Mustaqil hodisalar birga yuz berishi ehtimoli ularning ehtimollarini ko‘paytirib topiladi. Ikki tanga ikkalasi ham gerb tushishi — chorakda bir."),
])


@sh("pm_ehtimol", "yopiq")
def pm_eh_1(rng):
    q = rng.randint(2, 9); k = rng.randint(2, 9); n = q + k
    return _y(rng, f"Qutida {q} ta qizil va {k} ta ko‘k shar bor. Ko‘zni yumib bitta shar olinsa, qizil bo‘lishi ehtimoli qancha?", f"${q}/{n}$", [f"Qulay: {q}; barcha: {n}; P = {q}/{n}."], noto=[f"${k}/{n}$", f"${q}/{k}$", f"${q}/{n + 1}$", f"${q + 1}/{n}$", f"${n}/{q}$"])


@sh("pm_ehtimol", "yopiq")
def pm_eh_2(rng):
    n = rng.choice([5, 8, 10, 20]); k = rng.randint(1, n - 1)
    return _y(rng, f"Biror hodisaning ehtimoli {k}/{n} ga teng. Bu hodisa YUZ BERMASLIGI ehtimoli qancha?", f"${n - k}/{n}$", [f"1 − {k}/{n} = {n - k}/{n}."], noto=[f"${k}/{n}$", f"${n - k}/{k}$", f"${k}/{n - k}$", f"${n - k + 1}/{n}$", f"$1/{n}$"])


@sh("pm_ehtimol", "yopiq")
def pm_eh_3(rng):
    s = rng.choice([1, 2, 3, 4, 5, 6])
    return _y(rng, f"O‘yin kubi tashlandi. {s} dan KATTA son tushishi ehtimoli qancha?", f"${6 - s}/6$" if s < 6 else "$0$", [f"Qulay natijalar: {s + 1}, …, 6 — jami {6 - s} ta; P = {6 - s}/6."] if s < 6 else ["Hech qanday natija 6 dan katta emas: P = 0."],
              noto=[f"${s}/6$", f"${(7 - s)}/6$", "$1/6$", "$1/2$"])


@sh("pm_ehtimol", "yopiq")
def pm_eh_4(rng):
    n = rng.choice([100, 200, 500]); p = rng.choice([10, 20, 25]); 
    return _y(rng, f"Zavodda ishlab chiqarilgan detalning nuqsonli bo‘lish ehtimoli {p}%. {n} ta detaldan taxminan nechtasi nuqsonli bo‘ladi?", n * p // 100, [f"{n}·{p}/100 = {n * p // 100}."], noto=[n - n * p // 100, p, n // p])


@sh("pm_ehtimol", "ochiq")
def pm_eh_5(rng):
    q = rng.randint(2, 6); k = rng.randint(2, 6); m = rng.randint(1, 5); n = q + k + m
    return _o(f"Qopda {q} qizil, {k} ko‘k va {m} yashil shar bor.", [("a) Jami sharlar soni:", n), (f"b) Yashil bo‘lmagan shar chiqish natijalari soni:", q + k)], [f"a) {q} + {k} + {m} = {n}.", f"b) {q} + {k} = {q + k} — P = {q + k}/{n}."])


@sh("pm_ehtimol", "ochiq")
def pm_eh_6(rng):
    n = rng.choice([60, 120, 300, 600])
    return _o(f"O‘yin kubi {n} marta tashlansa, 6 tushishi ehtimoli 1/6.", [("a) Taxminan necha marta 6 tushadi?", n // 6), ("b) Taxminan necha marta 6 TUSHMAYDI?", n - n // 6)], [f"a) {n}/6 = {n // 6}.", f"b) {n} − {n // 6} = {n - n // 6}."])


@sh("pm_ehtimol", "ochiq")
def pm_eh_7(rng):
    k = rng.choice([2, 3])
    return _o(f"Tanga {k} marta ketma-ket tashlanadi. Har safar gerb tushishi ehtimoli 1/2 (mustaqil).", [("a) Barcha natijalar soni:", 2 ** k), ("b) Hammasi gerb bo‘lishi natijalarining soni:", 1)], [f"a) 2^{k} = {2 ** k}.", f"b) Faqat bitta (G…G): P = 1/{2 ** k}."])


tema("pm_sanash", "PM-12", "Sanash: variantlar soni va kombinatsiyalar", "🍔", "Ko‘paytirish qoidasi, ro‘yxat tuzish, tartibli va tartibsiz tanlash", [
    ("Ko‘paytirish qoidasi", "3 ta kofta × 4 ta shim = 12 ta kiyim\nQadamlar mustaqil — ko‘paytiriladi",
     "Agar birinchi tanlovda uch imkoniyat, ikkinchisida to‘rt imkoniyat bo‘lsa, jami o‘n ikki variant bo‘ladi. Mustaqil tanlovlar sonini ko‘paytiramiz."),
    ("Tartib muhim", "3 kishi navbat: 3! = 3·2·1 = 6\n5 kishi: 5! = 120\nTartib o‘zgarsa — boshqa variant",
     "Uch kishini navbatga qo‘yishning oltita usuli bor: birinchiga uch, ikkinchiga ikki, uchinchiga bir variant. Tartib ahamiyatli bo‘lsa, shunday ko‘paytiramiz."),
    ("Tartib muhim emas", "10 kishidan 2 ta tanlash: 10·9/2 = 45\nJuftlar — ikki marta sanalgan",
     "Tartib ahamiyatsiz bo‘lganda bir tanlovni bir necha marta sanab qo‘yamiz, shuning uchun tartibli sonni takrorlar soniga bo‘lamiz. O‘n kishidan ikkitasini tanlash — o‘n marta to‘qqiz, bo‘lingan ikkiga."),
])


@sh("pm_sanash", "yopiq")
def pm_sa_1(rng):
    a = rng.randint(2, 6); b = rng.randint(2, 6); c = rng.randint(2, 4)
    return _y(rng, f"Menyuda {a} ta birinchi taom, {b} ta ikkinchi taom va {c} ta ichimlik bor. Bittadan tanlab nechta turli tushlik tuzish mumkin?", a * b * c, [f"{a}·{b}·{c} = {a * b * c}."], noto=[a + b + c, a * b + c, a * b * c + a])


@sh("pm_sanash", "yopiq")
def pm_sa_2(rng):
    n = rng.choice([3, 4, 5]); f = math.factorial(n)
    return _y(rng, f"{n} ta do‘st bir qatorga necha xil usulda tizilishi mumkin?", f, [f"{n}! = " + "·".join(str(i) for i in range(n, 0, -1)) + f" = {f}."], noto=[n * n, n * 2, f + n])


@sh("pm_sanash", "yopiq")
def pm_sa_3(rng):
    n = rng.choice([5, 6, 8, 10, 12]); 
    return _y(rng, f"{n} kishidan 2 ta vakil tanlash (tartib ahamiyatsiz) necha usulda mumkin?", n * (n - 1) // 2, [f"{n}·{n - 1}/2 = {n * (n - 1) // 2}."], noto=[n * (n - 1), n * 2, n * (n - 1) // 2 + n])


@sh("pm_sanash", "yopiq")
def pm_sa_4(rng):
    a = rng.choice([3, 4, 5]); 
    return _y(rng, f"{a} xonali kod faqat 1, 2, 3 raqamlaridan tuziladi (raqamlar takrorlanishi mumkin). Nechta kod mavjud?", 3 ** a, [f"Har o‘rinda 3 tanlov: 3^{a} = {3 ** a}."], noto=[3 * a, a ** 3 if a ** 3 != 3 ** a else 3 ** a + 1, 3 ** (a - 1)])


@sh("pm_sanash", "ochiq")
def pm_sa_5(rng):
    a = rng.randint(3, 6); b = rng.randint(3, 6)
    return _o(f"Maktab formasi: {a} xil ko‘ylak va {b} xil shim bor.", [("a) Jami kiyim to‘plamlari soni:", a * b), ("b) Bitta ko‘ylakni tanlasangiz, shimlar bilan nechta to‘plam?", b)], [f"a) {a}·{b} = {a * b}.", f"b) Faqat shimni tanlaysiz: {b}."])


@sh("pm_sanash", "ochiq")
def pm_sa_6(rng):
    n = rng.choice([4, 5, 6])
    return _o(f"{n} ta bola qatorga turadi.", [("a) Tizilishlar soni:", math.factorial(n)), ("b) Ma’lum bir bola birinchi bo‘lishini xohlasak:", math.factorial(n - 1))], [f"a) {n}! = {math.factorial(n)}.", f"b) Qolgan {n - 1} ta: {(n - 1)}! = {math.factorial(n - 1)}."])


@sh("pm_sanash", "ochiq")
def pm_sa_7(rng):
    n = rng.choice([6, 8, 10])
    return _o(f"{n} ta jamoa turnirda bir-biri bilan bir martadan o‘ynaydi.", [("a) Jami o‘yinlar soni:", n * (n - 1) // 2), ("b) Har jamoa nechta o‘yin o‘ynaydi?", n - 1)], [f"a) {n}·{n - 1}/2 = {n * (n - 1) // 2}.", f"b) {n} − 1 = {n - 1}."])


tema("pm_tavakkal", "PM-12", "Xavf, kutilgan qiymat va qaror", "🎰", "Yutuq va xavfni solishtirish: lotereya, sug‘urta, takroriy tajriba natijasi", [
    ("Kutilgan qiymat", "E = Σ (qiymat · ehtimol)\nYutuq 100 000, P = 1/10 → 10 000\nChipta narxi bilan solishtir",
     "Kutilgan qiymat — har bir natija qiymatini uning ehtimoliga ko‘paytirib qo‘shishdan chiqadi. U uzoq muddatda o‘rtacha natijani ko‘rsatadi."),
    ("Adolatli o‘yin", "Kutilgan yutuq = chipta narxi → adolatli\nKutilgan yutuq < narx → yutqazish ko‘proq",
     "Agar chipta narxi kutilgan yutuqdan katta bo‘lsa, uzoq muddatda yutqazamiz. Bu lotereya va qimor o‘yinlarining asosiy qoidasi."),
    ("Sug‘urta", "Sug‘urta narxi ≈ xavf ehtimoli · zarar\nKichik ehtimol, katta zarar — sug‘urta foydali",
     "Katta zarar ehtimoli kichik bo‘lsa ham, sug‘urta tavakkalni kamaytiradi. Biz kichik, aniq to‘lov evaziga katta noaniq zararni boshqa tomonga o‘tkazamiz."),
])


@sh("pm_tavakkal", "yopiq")
def pm_tv_1(rng):
    y = rng.choice([10, 20, 50, 100]) * 1000; d = rng.choice([4, 5, 10]); 
    return _y(rng, f"Lotereyada yutuq {som(y)} so‘m, uni olish ehtimoli 1/{d}. Kutilgan yutuq necha so‘m?", y // d, [f"{som(y)}·1/{d} = {som(y // d)}."], noto=[y, y * d, y // d // 2 if (y // d) % 2 == 0 else y // d + 500])


@sh("pm_tavakkal", "yopiq")
def pm_tv_2(rng):
    y = rng.choice([100, 200, 500]) * 1000; d = rng.choice([4, 5, 10]); ch = y // d + rng.choice([5, 10, 20]) * 1000
    return _y(rng, f"Chipta narxi {som(ch)} so‘m; yutuq {som(y)} so‘m, ehtimol 1/{d}. Ko‘p marta o‘ynasangiz, har o‘yinda o‘rtacha ... bo‘ladi:", "Yutqazish", [f"Kutilgan yutuq {som(y // d)} < chipta {som(ch)} → o‘rtacha yutqazasiz."], noto=["Yutish", "Teng, foydasiz va zarari yo‘q", "Faqat g‘alaba"])


@sh("pm_tavakkal", "yopiq")
def pm_tv_3(rng):
    z = rng.choice([50, 100, 200, 400]) * 1000000; p = rng.choice([1, 2, 5]); 
    return _y(rng, f"Uy yong‘inidan zarar {som(z)} so‘m, yong‘in ehtimoli yiliga {p}%. Kutilgan yillik zarar necha so‘m?", z * p // 100, [f"{som(z)}·{p}/100 = {som(z * p // 100)}."], noto=[z // p, z * p // 10, z])


@sh("pm_tavakkal", "yopiq")
def pm_tv_4(rng):
    n = rng.choice([20, 40, 60]); k = rng.choice([7, 12, 18]); 
    return _y(rng, f"{n} marta tanga tashlanib, {k} marta gerb tushdi. Gerb tushishining tajribaviy nisbiy chastotasi qancha?", Fraction(k, n), [f"{k}/{n} = {num(Fraction(k, n))}."], noto=[Fraction(n - k, n), Fraction(1, 2), Fraction(k, n) + Fraction(1, 10)])


@sh("pm_tavakkal", "ochiq")
def pm_tv_5(rng):
    ch = rng.choice([5, 10]) * 1000; y = rng.choice([20, 50]) * 1000; d = rng.choice([5, 10])
    return _o(f"O‘yin: chipta {som(ch)} so‘m, yutuq {som(y)} so‘m, ehtimol 1/{d}.", [("a) Kutilgan yutuq (so‘m):", y // d), ("b) Kutilgan sof natija (yutuq − chipta, so‘m):", y // d - ch)], [f"a) {som(y)}/{d} = {som(y // d)}.", f"b) {som(y // d)} − {som(ch)} = {som(y // d - ch)}."])


@sh("pm_tavakkal", "ochiq")
def pm_tv_6(rng):
    n = rng.choice([100, 200, 400]); p = rng.choice([2, 5, 10])
    return _o(f"{n} ta mijoz sug‘urta qildirdi, har birining avariya ehtimoli {p}%, zarar 10 000 000 so‘m.", [("a) Taxminan nechta avariya bo‘ladi?", n * p // 100), ("b) Jami kutilgan zarar (so‘m):", n * p // 100 * 10_000_000)], [f"a) {n}·{p}/100 = {n * p // 100}.", f"b) {n * p // 100}·10 000 000 = {som(n * p // 100 * 10_000_000)}."])


@sh("pm_tavakkal", "ochiq")
def pm_tv_7(rng):
    a = rng.choice([10, 20, 30]) ; b = rng.choice([40, 50, 60])
    return _o(f"Ikki variant: A — kafolatli {som(a * 1000)} so‘m; B — 1/2 ehtimol bilan {som(b * 1000 * 2 // 1)} so‘m, aks holda 0.", [("a) B ning kutilgan qiymati (so‘m):", b * 1000), ("b) Kutilgan qiymati katta variant (1 = A, 2 = B):", 1 if a > b else 2)], [f"a) 1/2·{som(b * 2000)} = {som(b * 1000)}.", f"b) A: {som(a * 1000)}, B: {som(b * 1000)} → {'A' if a > b else 'B'}."])


# ═════════ 13-BO'LIM · MOLIYA VA HAYOTIY QARORLAR ═════════
tema("pm_kredit", "PM-13", "Kredit, foiz va to‘lov jadvali", "🏦", "Kredit to‘lovi, ortiqcha to‘lov, muddatni qisqartirish va foizni taqqoslash", [
    ("Kredit nima?", "Kredit = qarz + foiz\nOylik to‘lov = (qarz + foiz) / oylar\nOrtiqcha to‘lov = jami to‘lov − qarz",
     "Kredit — banksan vaqtincha olingan pul. Uni foiz bilan qaytaramiz. Jami to‘lov qarz va foizning yig‘indisi. Ortiqcha to‘lov — jami to‘lovdan olingan qarz ayirmasi."),
    ("Foizni solishtirish", "Yillik foiz qancha past — shuncha yaxshi\nMuddat uzaysa foiz ko‘p to‘planadi\nEffektiv stavkaga qarang",
     "Foiz kam bo‘lgan kredit arzonroq. Muddat uzaytirilsa, oylik to‘lov kamayadi, ammo jami ortiqcha to‘lov oshadi."),
    ("Jadval o‘qish", "Oy | Qoldiq | Foiz | To‘lov\nQoldiq kamayadi, foiz ham kamayadi",
     "To‘lov jadvalida har oy qarz qoldig‘i kamayadi. Foiz qoldiqdan hisoblanadi, shuning uchun ham kamayib boradi."),
])


@sh("pm_kredit", "yopiq")
def pm_kr_1(rng):
    S = rng.choice([10, 20, 30, 50]) * 1_000_000; p = rng.choice([12, 18, 24]); n = rng.choice([1, 2, 3])
    jami = S + S * p * n // 100
    return _y(rng, f"{som(S)} so‘m kredit yiliga {p}% (oddiy foiz) bilan {n} yilga olindi. Jami qancha qaytariladi (so‘m)?", jami, [f"Foiz: {som(S)}·{p}/100·{n} = {som(S * p * n // 100)}.", f"Jami: {som(S)} + {som(S * p * n // 100)} = {som(jami)}."], noto=[S + S * p // 100, S * p * n // 100, jami + S // 10])


@sh("pm_kredit", "yopiq")
def pm_kr_2(rng):
    S = rng.choice([6, 12, 24]) * 1_000_000; m = rng.choice([6, 12, 24]); 
    return _y(rng, f"{som(S)} so‘m foizsiz bo‘lib to‘lashga {m} oyga olindi. Oylik to‘lov necha so‘m?", S // m, [f"{som(S)} : {m} = {som(S // m)}."], noto=[S // (m + 12), S // m * 2, S // m + 50_000])


@sh("pm_kredit", "yopiq")
def pm_kr_3(rng):
    S = rng.choice([10, 20, 30]) * 1_000_000; a = rng.choice([18, 20, 24]); b = a - rng.choice([2, 4, 6])
    return _y(rng, f"Ikki bank {som(S)} so‘mni 1 yilga kreditga beradi: A — {a}%, B — {b}% (oddiy foiz). B da A ga qaraganda necha so‘m kam foiz to‘lanadi?", S * (a - b) // 100, [f"Farq: {som(S)}·({a} − {b})/100 = {som(S * (a - b) // 100)}."], noto=[S * a // 100, S * b // 100, (a - b) * 10000])


@sh("pm_kredit", "yopiq")
def pm_kr_4(rng):
    S = rng.choice([12, 24, 36]) * 1_000_000; m = rng.choice([12, 24]); p = rng.choice([10, 15, 20])
    yt = S * p // 100 * m // 12
    return _y(rng, f"{som(S)} so‘m {m} oyga yiliga {p}% (oddiy foiz). Ortiqcha to‘lov (foiz) necha so‘m?", yt, [f"{som(S)}·{p}/100·{m}/12 = {som(yt)}."], noto=[S * p // 100, yt * 2, yt // 2])


@sh("pm_kredit", "ochiq")
def pm_kr_5(rng):
    S = rng.choice([6, 12, 24]) * 1_000_000; p = rng.choice([12, 18]); m = 12
    foiz = S * p // 100; jami = S + foiz
    return _o(f"{som(S)} so‘m kredit 1 yilga yiliga {p}% (oddiy foiz). To‘lov 12 oyga teng bo‘linadi.", [("a) Jami to‘lov (so‘m):", jami), ("b) Oylik to‘lov (so‘m):", jami // m)], [f"a) {som(S)} + {som(foiz)} = {som(jami)}.", f"b) {som(jami)} : 12 = {som(jami // m)}."])


@sh("pm_kredit", "ochiq")
def pm_kr_6(rng):
    oy = rng.choice([500, 600, 800]) * 1000; m = rng.choice([12, 18, 24]); S = rng.choice([6, 8, 10]) * 1_000_000
    return _o(f"Muzlatgich narxi {som(S)} so‘m. Bo‘lib to‘lashda oyiga {som(oy)} so‘mdan {m} oy to‘lanadi.", [("a) Jami to‘lov (so‘m):", oy * m), ("b) Naqd narxdan necha so‘m ortiq to‘lanadi?", oy * m - S)], [f"a) {som(oy)}·{m} = {som(oy * m)}.", f"b) {som(oy * m)} − {som(S)} = {som(oy * m - S)}."])


@sh("pm_kredit", "ochiq")
def pm_kr_7(rng):
    S = rng.choice([12, 24, 30]) * 1_000_000; p = rng.choice([12, 24])
    a = S * p // 100; b = S * (p // 2) // 100
    return _o(f"{som(S)} so‘m kredit: A bank yiliga {p}%, B bank {p // 2}% (1 yil, oddiy foiz).", [("a) A bankdagi foiz summasi (so‘m):", a), ("b) B bank qancha arzon (so‘m)?", a - b)], [f"a) {som(S)}·{p}/100 = {som(a)}.", f"b) {som(a)} − {som(b)} = {som(a - b)}."])


tema("pm_byudjet2", "PM-13", "Oilaviy byudjet va jamg‘arma", "💼", "Daromad–xarajat balansi, jamg‘arma maqsadi va muddati, tejash qarori", [
    ("Balans", "Qoldiq = daromad − xarajat\nDoimiy xarajat va o‘zgaruvchan xarajat\nAvval jamg‘arma, keyin sarf",
     "Oilaning byudjeti daromad va xarajat orasidagi muvozanat. Qoldiq — daromaddan xarajatni ayirish. Yaxshi odat — avval jamg‘armani ajratib qo‘yish."),
    ("Maqsad va muddat", "Maqsad / oylik jamg‘arma = oylar\nNoutbuk 6 000 000, oyiga 500 000 → 12 oy",
     "Maqsadga yetish uchun kerakli summani oylik jamg‘armaga bo‘lamiz. Natija — necha oy kerakligi."),
    ("Qaror qilish", "Zarur → istak\nTejash: 10% kamaytirish\nChegirma bilan bahslash",
     "Xarajatlarni zarur va ixtiyoriy turlarga bo‘lamiz. Byudjet yetmasa, ixtiyoriy xarajatlarni kamaytiramiz."),
])


@sh("pm_byudjet2", "yopiq")
def pm_by_1(rng):
    d = rng.choice([4, 5, 6, 8]) * 1_000_000; x1 = rng.choice([1, 2]) * 1_000_000; x2 = rng.choice([500, 800, 1000]) * 1000; x3 = rng.choice([300, 500]) * 1000
    return _y(rng, f"Oila daromadi oyiga {som(d)} so‘m. Xarajatlar: ijara {som(x1)}, oziq-ovqat {som(x2)}, boshqa {som(x3)} so‘m. Oy oxirida qoladigan pul?", d - x1 - x2 - x3, [f"{som(d)} − {som(x1)} − {som(x2)} − {som(x3)} = {som(d - x1 - x2 - x3)}."], noto=[x1 + x2 + x3, d - x1 - x2, d - x1 - x2 - x3 + 500_000])


@sh("pm_byudjet2", "yopiq")
def pm_by_2(rng):
    M = rng.choice([6, 9, 12]) * 1_000_000; j = rng.choice([500, 600, 750, 1000]) * 1000
    while M % j: j = rng.choice([500, 600, 750, 1000, 1500, 2000]) * 1000
    return _y(rng, f"Noutbuk narxi {som(M)} so‘m. Har oy {som(j)} so‘mdan jamg‘arsangiz, necha oyda yetarli bo‘ladi?", M // j, [f"{som(M)} : {som(j)} = {M // j} oy."], noto=[M // j + 1, M // j - 2 if M // j > 3 else M // j + 3, M // (j * 2) + 1])


@sh("pm_byudjet2", "yopiq")
def pm_by_3(rng):
    d = rng.choice([3, 4, 5, 6]) * 1_000_000; p = rng.choice([10, 20, 30])
    return _y(rng, f"Daromadingiz {som(d)} so‘m. Har oy daromadning {p}% ini jamg‘arasiz. Bir yilda necha so‘m jamg‘arasiz?", d * p // 100 * 12, [f"Oylik: {som(d)}·{p}/100 = {som(d * p // 100)}; yillik: ·12 = {som(d * p // 100 * 12)}."], noto=[d * p // 100, d * p // 100 * 6, d * p // 100 * 10])


@sh("pm_byudjet2", "yopiq")
def pm_by_4(rng):
    x = rng.choice([800, 1000, 1200]) * 1000; t = rng.choice([10, 20])
    return _y(rng, f"Mobil aloqa xarajatingiz oyiga {som(x)} so‘m. Uni {t}% ga kamaytirdingiz. Yangi xarajat?", x * (100 - t) // 100, [f"{som(x)}·{100 - t}/100 = {som(x * (100 - t) // 100)}."], noto=[x - t, x * t // 100, x + x * t // 100])


@sh("pm_byudjet2", "ochiq")
def pm_by_5(rng):
    d = rng.choice([4, 5, 6]) * 1_000_000; z = rng.choice([40, 50, 60])
    return _o(f"Oylik daromad {som(d)} so‘m. Zarur xarajatlar daromadning {z}% i.", [("a) Zarur xarajatlar (so‘m):", d * z // 100), ("b) Qolgan summa (so‘m):", d - d * z // 100)], [f"a) {som(d)}·{z}/100 = {som(d * z // 100)}.", f"b) {som(d)} − {som(d * z // 100)} = {som(d - d * z // 100)}."])


@sh("pm_byudjet2", "ochiq")
def pm_by_6(rng):
    M = rng.choice([3, 6, 9]) * 1_000_000; j = rng.choice([250, 300, 500]) * 1000
    return _o(f"Velosiped {som(M)} so‘m. Siz allaqachon {som(M // 3)} so‘m jamg‘argansiz. Oyiga {som(j)} so‘mdan qo‘shasiz.", [("a) Yana qancha kerak (so‘m)?", M - M // 3), ("b) Necha oy kerak (butunga yuqoriga)?", -(-(M - M // 3) // j))], [f"a) {som(M)} − {som(M // 3)} = {som(M - M // 3)}.", f"b) {som(M - M // 3)} : {som(j)} = {(M - M // 3) / j:.2f} → {-(-(M - M // 3) // j)} oy."])


@sh("pm_byudjet2", "ochiq")
def pm_by_7(rng):
    d = rng.choice([4, 5]) * 1_000_000; zar = rng.choice([2, 3]) * 1_000_000; ixt = rng.choice([800, 1000]) * 1000; t = rng.choice([10, 20])
    return _o(f"Daromad {som(d)} so‘m, zarur xarajat {som(zar)}, ixtiyoriy xarajat {som(ixt)} so‘m. Ixtiyoriyni {t}% ga kamaytirdingiz.", [("a) Yangi ixtiyoriy xarajat (so‘m):", ixt * (100 - t) // 100), ("b) Qoladigan pul (so‘m):", d - zar - ixt * (100 - t) // 100)], [f"a) {som(ixt)}·{100 - t}/100 = {som(ixt * (100 - t) // 100)}.", f"b) {som(d)} − {som(zar)} − {som(ixt * (100 - t) // 100)} = {som(d - zar - ixt * (100 - t) // 100)}."])
