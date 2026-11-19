"""PISA matematika — kengaytma 2: tarif, kvadratik va o‘sish modellari, perimetr-yuza-qoplash, hajm va sirt (chizmali)."""
import math
from fractions import Fraction

from modules.pisa_mat_g import reg, num, som, _y, _o, fig_chiziq, fig_tortburchak, fig_L, fig_stolbik
from modules.mock_fig import _svg, _t, _l, _poly

TOP = "P_M"
TEMA = {}
_SOHA = {"PM-6": "O‘zgarish va bog‘liqlik", "PM-7": "O‘zgarish va bog‘liqlik", "PM-8": "Fazo va shakl", "PM-9": "Fazo va shakl"}
_ESKI = {"PM-6": "PM-OZG", "PM-7": "PM-OZG", "PM-8": "PM-FAZ", "PM-9": "PM-FAZ"}


def tema(kod, kb, nom, belgi, maqsad, dars):
    TEMA[kod] = {"nom": nom, "soha": _SOHA[kb], "belgi": belgi, "maqsad": maqsad, "bolim": _ESKI[kb], "kb": kb, "toplam": TOP,
                 "dars": [{"sarlavha": a, "doska": b, "ovoz": c} for a, b, c in dars]}


sh = reg


def rasmli(q, svg):
    q["rasm"] = svg
    return q


def fig_parabola(a, b, c, x0_, x1_, sarlavha="", xnom="x", ynom="y"):
    """y = a x² + b x + c grafigi [x0_, x1_] oralig‘ida."""
    W, H, ox, oy = 320, 215, 46, 180
    xs = [x0_ + (x1_ - x0_) * i / 60 for i in range(61)]; ys = [a * x * x + b * x + c for x in xs]
    lo, hi = min(0, min(ys)), max(ys); hi = hi if hi > lo else lo + 1
    sx = (W - ox - 16) / (x1_ - x0_); sy = 140 / (hi - lo)
    px = lambda x: ox + (x - x0_) * sx; py = lambda y: oy - (y - lo) * sy
    body = _t(W / 2, 14, sarlavha, it=False, size=12) + _l((ox, py(0)), (W - 8, py(0))) + _l((px(0) if x0_ <= 0 <= x1_ else ox, oy + 4), (px(0) if x0_ <= 0 <= x1_ else ox, 25))
    pts = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, ys))
    body += f'<polyline points="{pts}" fill="none" stroke="#d33" stroke-width="2"/>'
    for i in range(0, 5):
        xv = x0_ + (x1_ - x0_) * i / 4
        body += _l((px(xv), py(0)), (px(xv), py(0) + 4)) + _t(px(xv), py(0) + 16, f"{xv:g}", it=False, size=10)
        yv = lo + (hi - lo) * i / 4
        body += _l((ox - 3, py(yv)), (W - 8, py(yv)), w=.3, col="#ccc") + _t(ox - 5, py(yv) + 3, f"{yv:g}", it=False, anchor="end", size=10)
    body += _t(W - 10, py(0) - 5, xnom, anchor="end", size=12) + _t(ox + 12, 24, ynom, size=12)
    return _svg(body, W, 205)


def fig_quti(a, b, h, birlik="sm"):
    """To‘g‘ri burchakli parallelepiped (izometrik)."""
    s = min(110 / a, 80 / b, 90 / h) if min(a, b, h) > 0 else 1; dx, dy = b * s * .5, b * s * .35
    x, y = 40, 40 + dy; A, Hh = a * s, h * s
    f = [(x, y + Hh), (x + A, y + Hh), (x + A, y), (x, y)]; top = [(x, y), (x + A, y), (x + A + dx, y - dy), (x + dx, y - dy)]; side = [(x + A, y + Hh), (x + A + dx, y + Hh - dy), (x + A + dx, y - dy), (x + A, y)]
    body = _poly(f, fill="#eef5ff") + _poly(top, fill="#dbe8ff") + _poly(side, fill="#c9dcfb")
    body += _t(x + A / 2, y + Hh + 15, f"{num(a)} {birlik}", it=False, size=12) + _t(x - 6, y + Hh / 2 + 4, f"{num(h)} {birlik}", it=False, anchor="end", size=12) + _t(x + A + dx / 2 + 12, y + Hh - dy / 2 + 14, f"{num(b)} {birlik}", it=False, anchor="start", size=12)
    return _svg(body, 290, 200)


def fig_silindr(r, h, birlik="sm"):
    sc = min(70 / r, 110 / h); R, Hh = r * sc, h * sc; cx, ty = 120, 40
    body = f'<ellipse cx="{cx}" cy="{ty + Hh}" rx="{R:.1f}" ry="{R * .3:.1f}" fill="#dbe8ff" stroke="#111"/>' + _l((cx - R, ty), (cx - R, ty + Hh)) + _l((cx + R, ty), (cx + R, ty + Hh))
    body += f'<ellipse cx="{cx}" cy="{ty}" rx="{R:.1f}" ry="{R * .3:.1f}" fill="#eef5ff" stroke="#111"/>' + _l((cx, ty), (cx + R, ty), dash=True, col="#d33") + _t(cx + R / 2, ty - 6, f"r = {num(r)} {birlik}", it=False, size=12) + _t(cx + R + 8, ty + Hh / 2, f"h = {num(h)} {birlik}", it=False, anchor="start", size=12)
    return _svg(body, 290, 200)


# ═════════ 6-BO'LIM · CHIZIQLI BOG'LANISH (tarif) ═════════
tema("pm_tarif", "PM-6", "Tariflarni taqqoslash va kesishish nuqtasi", "📱", "Ikki tarif/rejadan qaysi biri foydali; qachon tenglashadi; grafik bo‘yicha qaror", [
    ("Ikki tarif", "A: y = 40 + 2x  (abonent to‘lovi + daqiqa)\nB: y = 10 + 5x\nKim arzon? Tenglashtiramiz",
     "Ko‘pincha ikkita tarif bo‘ladi: biri qat’iy to‘lovi katta, daqiqasi arzon; ikkinchisida aksincha. Qaysi biri foydali ekani ishlatish miqdoriga bog‘liq."),
    ("Kesishish nuqtasi", "40 + 2x = 10 + 5x → 30 = 3x → x = 10\nx < 10: B arzon; x > 10: A arzon",
     "Ikki to‘g‘ri chiziq kesishgan nuqta — ikkala tarif narxi teng bo‘ladigan miqdor. Undan oldin bir tarif, keyin ikkinchisi foydali."),
    ("Grafikdan qaror", "Past chiziq — arzon tarif\nChiziqlar kesishgan joyni toping",
     "Grafikda eng past chiziq — eng arzon variant. Chiziqlar kesishgan joyda narxlar tenglashadi. Shu joydan chap va o‘ng tomonda qaror o‘zgaradi."),
])


@sh("pm_tarif", "yopiq")
def pm_ta_1(rng):
    a0, ak = rng.choice([(40, 2), (30, 3), (50, 1), (60, 2)]); b0, bk = rng.choice([(10, 5), (0, 4), (20, 4), (10, 6)])
    x = rng.randint(5, 30)
    A = a0 + ak * x; B = b0 + bk * x
    return _y(rng, f"A tarif: oylik {a0} ming + har daqiqa {ak} ming. B tarif: oylik {b0} ming + har daqiqa {bk} ming. {x} daqiqa gaplashsangiz qaysi tarif arzon?", "A" if A < B else "B" if B < A else "Teng",
              [f"A: {a0} + {ak}·{x} = {A}; B: {b0} + {bk}·{x} = {B}.", "Arzoni — kichik summa."], noto=["Teng" if A != B else "A", "Ikkalasi ham bir xil" if A != B else "B", "Aniqlab bo‘lmaydi"]) if A != B else _y(rng, f"A tarif: oylik {a0} ming + {ak} ming/daq. B tarif: oylik {b0} ming + {bk} ming/daq. 10 daqiqada A necha ming (ming so‘mda)?", a0 + ak * 10, [f"{a0} + {ak}·10 = {a0 + ak * 10}."], noto=[a0 + ak, a0 * ak, a0 + 10])


@sh("pm_tarif", "yopiq")
def pm_ta_2(rng):
    a0, ak = rng.choice([(30, 2), (40, 3), (20, 2)]); b0, bk = a0 - rng.choice([10, 20]), ak + rng.choice([1, 2])
    x = (a0 - b0) // (bk - ak) if (a0 - b0) % (bk - ak) == 0 else None
    if x is None:
        a0, ak, b0, bk, x = 40, 2, 10, 5, 10
    return _y(rng, f"A: {a0} + {ak}x, B: {b0} + {bk}x (x — daqiqa). Qaysi x da ikkala tarif narxi teng bo‘ladi?", x, [f"{a0} + {ak}x = {b0} + {bk}x → {a0 - b0} = {bk - ak}x → x = {x}."], noto=[x + 5, x - 3 if x > 3 else x + 8, a0 - b0])


@sh("pm_tarif", "yopiq")
def pm_ta_3(rng):
    a0 = rng.choice([20, 30, 50]); k1 = rng.choice([2, 3]); x = rng.randint(4, 20)
    q = fig_chiziq(a0, k1, 20, "daqiqa", "ming so‘m", sarlavha="Tarif narxi")
    return rasmli(_y(rng, f"Grafik tarif narxini ko‘rsatadi (x=0 da boshlang‘ich to‘lov). 0 daqiqada narx necha ming so‘m?", a0, [f"Grafik y o‘qini {a0} da kesadi: boshlang‘ich to‘lov {a0} ming."], noto=[a0 + k1, a0 * 2, k1 * 10]), q)


@sh("pm_tarif", "yopiq")
def pm_ta_4(rng):
    a0 = rng.choice([20, 30, 50]); k1 = rng.choice([2, 3, 4]); x = rng.choice([5, 10, 15])
    return rasmli(_y(rng, f"Grafikdan foydalaning: 20 daqiqada narx necha ming so‘m? (ko‘k belgilangan: chiziq {a0} dan boshlanib, har daqiqada {k1} ga ko‘tariladi)", a0 + k1 * 20, [f"{a0} + {k1}·20 = {a0 + k1 * 20}."], noto=[a0 + k1, a0 * k1, k1 * 20]), fig_chiziq(a0, k1, 20, "daqiqa", "ming so‘m", sarlavha="Tarif"))


@sh("pm_tarif", "ochiq")
def pm_ta_5(rng):
    a0, ak = rng.choice([(40, 2), (60, 1), (50, 3)]); b0, bk = rng.choice([(10, 5), (20, 4), (0, 6)])
    while (a0 - b0) % (bk - ak) or (a0 - b0) // (bk - ak) <= 0: a0, ak = rng.choice([(40, 2), (60, 1), (50, 3)]); b0, bk = rng.choice([(10, 5), (20, 4), (0, 6)])
    x = (a0 - b0) // (bk - ak)
    return _o(f"A tarif: {a0} + {ak}x; B tarif: {b0} + {bk}x (ming so‘m, x — daqiqa).", [("a) Narxlar teng bo‘ladigan x:", x), ("b) Shu paytdagi narx (ming so‘m):", a0 + ak * x)],
              [f"a) {a0} + {ak}x = {b0} + {bk}x → {a0 - b0} = {bk - ak}x → x = {x}.", f"b) {a0} + {ak}·{x} = {a0 + ak * x}."])


@sh("pm_tarif", "ochiq")
def pm_ta_6(rng):
    f1 = rng.choice([15, 20, 25]) * 1000; k = rng.choice([500, 600, 800]); n = rng.choice([20, 30, 40])
    f2 = rng.choice([0, 5, 8]) * 1000; k2 = rng.choice([900, 1000, 1200])
    a = f1 + k * n; b = f2 + k2 * n
    return _o(f"Internet-paket: A — oylik {som(f1)} + har GB uchun {som(k)}; B — oylik {som(f2)} + har GB uchun {som(k2)}. Siz oyiga {n} GB ishlatasiz.", [("a) A bo‘yicha oylik to‘lov:", a), ("b) B bo‘yicha oylik to‘lov:", b)],
              [f"a) {som(f1)} + {som(k)}·{n} = {som(a)}.", f"b) {som(f2)} + {som(k2)}·{n} = {som(b)}.", f"Arzoni: {'A' if a < b else 'B'}."])


@sh("pm_tarif", "ochiq")
def pm_ta_7(rng):
    d = rng.choice([3, 4, 5]); p = rng.choice([6, 8, 10]) * 1000; f = rng.choice([10, 15, 20]) * 1000
    return _o(f"Velosiped ijarasi: kelish to‘lovi {som(f)} so‘m + har soat uchun {som(p)} so‘m.", [(f"a) {d} soatga to‘lov:", f + p * d), (f"b) {som(f + p * (d + 4))} so‘mga necha soat ijaraga olish mumkin?", d + 4)],
              [f"a) {som(f)} + {som(p)}·{d} = {som(f + p * d)}.", f"b) ({som(f + p * (d + 4))} − {som(f)}) : {som(p)} = {d + 4}."])


tema("pm_kvadrat", "PM-7", "Kvadratik bog‘lanish: parabola va to‘p harakati", "🏀", "Tashlangan jism balandligi, maydon va daromadning eng katta qiymati; grafikdan o‘qish", [
    ("Parabola", "y = ax² + bx + c\na < 0 — shoxlari pastga\nO‘q cho‘qqisi: x = −b/(2a)",
     "Kvadratik bog‘lanish grafigi parabola. Agar a manfiy bo‘lsa, shoxlari pastga qaraydi va cho‘qqisi eng baland nuqta bo‘ladi. Cho‘qqining x koordinatasi minus b ni ikki a ga bo‘lganga teng."),
    ("Eng katta qiymat", "h = −5t² + 20t\nt = 2 s da eng baland\nh(2) = −20 + 40 = 20 m",
     "To‘p yuqoriga otilsa, balandligi parabola bo‘yicha o‘zgaradi. Eng baland nuqtaga cho‘qqida erishiladi. Cho‘qqining vaqtini topib, formulaga qo‘yib balandlikni hisoblaymiz."),
    ("Yerga tushishi", "h = 0 → t(−5t + 20) = 0\nt = 0 yoki t = 4\nUchish vaqti: 4 s",
     "To‘p yerga tushganda balandlik nolga teng. Tenglamani yechsak, ikkita ildiz chiqadi: otilgan paytdagi nol va yerga tushgan vaqt."),
])


@sh("pm_kvadrat", "yopiq")
def pm_kv_1(rng):
    v = rng.choice([10, 20, 30, 40]); t = v // 5 if False else v // 10
    # h = -5t^2 + v t ; cho'qqi t = v/10
    tm = Fraction(v, 10); hm = -5 * tm * tm + v * tm
    return rasmli(_y(rng, f"To‘p h = −5t² + {v}t (m) qonuni bilan harakatlanadi (t — soniya). Eng baland nuqtaga qachon yetadi (soniya)?", tm, [f"Cho‘qqi: t = −b/(2a) = {v}/10 = {num(tm)} s."], noto=[Fraction(v, 5), Fraction(v, 20), tm + 1]), fig_parabola(-5, v, 0, 0, v / 5, "h(t)", "t", "h"))


@sh("pm_kvadrat", "yopiq")
def pm_kv_2(rng):
    v = rng.choice([10, 20, 30, 40]); tm = Fraction(v, 10); hm = -5 * tm * tm + v * tm
    return _y(rng, f"To‘p h = −5t² + {v}t qonuni bilan harakatlanadi. Eng katta balandlik necha metr?", hm, [f"t = {num(tm)} da: −5·{num(tm * tm)} + {v}·{num(tm)} = {num(hm)} m."], noto=[hm + 5, hm * 2, v])


@sh("pm_kvadrat", "yopiq")
def pm_kv_3(rng):
    v = rng.choice([10, 20, 30, 40]); t = Fraction(v, 5)
    return _y(rng, f"To‘p h = −5t² + {v}t qonuni bilan harakatlanadi. U necha sekundda yerga tushadi?", t, [f"−5t² + {v}t = 0 → t(−5t + {v}) = 0 → t = {num(t)} s."], noto=[Fraction(v, 10), Fraction(v, 2), t + 1])


@sh("pm_kvadrat", "yopiq")
def pm_kv_4(rng):
    a = rng.choice([2, 3, 4, 5]); x = rng.randint(2, 6)
    return _y(rng, f"Kvadrat shaklidagi bog‘ tomoni {a * x} m. Yuza S = (tomon)². Tomon 2 marta oshsa, yuza necha marta oshadi?", 4, ["(2a)² = 4a² — yuza 4 marta oshadi."], noto=[2, 8, 6])


@sh("pm_kvadrat", "ochiq")
def pm_kv_5(rng):
    P = rng.choice([20, 24, 30, 40, 36]); a = P // 2
    return _o(f"Uzunligi {P} m bo‘lgan to‘rda to‘g‘ri to‘rtburchak maydon o‘ralmoqda (bir tomoni — x, ikkinchisi — {a} − x). Yuza S = x({a} − x).", [("a) x = {0} bo‘lsa S:".format(a // 2), (a // 2) * (a - a // 2)), ("b) Eng katta yuza uchun x (m):", Fraction(a, 2))],
              [f"a) {a // 2}·({a} − {a // 2}) = {(a // 2) * (a - a // 2)}.", f"b) Parabolaning cho‘qqisi x = {a}/2 = {num(Fraction(a, 2))} — shunda yuza eng katta (kvadrat)."])


@sh("pm_kvadrat", "ochiq")
def pm_kv_6(rng):
    v = rng.choice([10, 20, 30]); tm = Fraction(v, 10)
    return rasmli(_o(f"Tosh yuqoriga otildi: h = −5t² + {v}t.", [("a) h(1) (m):", -5 + v), ("b) Yerga tushish vaqti (s):", Fraction(v, 5))], [f"a) −5 + {v} = {v - 5} m.", f"b) t = {num(Fraction(v, 5))} s."]), fig_parabola(-5, v, 0, 0, v / 5 + .2, "Tosh balandligi", "t (s)", "h (m)"))


@sh("pm_kvadrat", "ochiq")
def pm_kv_7(rng):
    a = rng.randint(2, 9)
    return _o(f"Kvadratning tomoni {a} sm. Tomon 3 sm uzaytirilsa:", [("a) Eski yuza (sm²):", a * a), ("b) Yangi yuza (sm²):", (a + 3) ** 2)], [f"a) {a}² = {a * a}.", f"b) ({a} + 3)² = {(a + 3) ** 2}."])


tema("pm_eksp", "PM-7", "O‘sish va kamayish: ikki marta, yarim yemirilish", "🦠", "Har davrda bir necha marta ko‘payish yoki yarmiga kamayish; jadval va grafik; tez o‘sish", [
    ("Ko‘paytirib o‘sish", "Har soat 2 marta: 1 → 2 → 4 → 8 → 16\nN = 2ᵗ\nChiziqli: qo‘shiladi; bu yerda: ko‘paytiriladi",
     "Ba’zi jarayonlarda har davrda miqdor bir necha marta ko‘payadi. Bakteriya har soatda ikki baravar. Bu qo‘shish emas, ko‘paytirish — shuning uchun o‘sish juda tez bo‘ladi."),
    ("Yarim yemirilish", "100 → 50 → 25 → 12,5\nHar davrda ÷ 2\nN = 100 · (1/2)ᵗ",
     "Radioaktiv modda yoki dori organizmda har davrda yarmiga kamayadi. Yuz gramm — ellik, keyin yigirma besh, keyin o‘n ikki yarim."),
    ("Chiziqli bilan farq", "Chiziqli: +5 har bosqichda\nEksponensial: ×2 har bosqichda\nBir necha bosqichdan so‘ng eksponensial ancha katta",
     "Chiziqli o‘sishda har bosqichda bir xil son qo‘shiladi, eksponensialda esa bir xil marta ko‘paytiriladi. Dastlab farq sezilmaydi, lekin bir necha bosqichdan keyin ikkinchisi ancha katta bo‘ladi."),
])


@sh("pm_eksp", "yopiq")
def pm_ek_1(rng):
    s = rng.choice([100, 200, 500, 1000]); k = rng.choice([2, 3]); t = rng.choice([3, 4, 5]) if k == 2 else rng.choice([2, 3, 4])
    return _y(rng, f"Boshida {s} ta bakteriya bor edi. Har soatda {k} baravar ko‘payadi. {t} soatdan keyin nechta bo‘ladi?", s * k ** t, [f"{s} · {k}^{t} = {s} · {k ** t} = {som(s * k ** t)}."], noto=[s + k * t, s * k * t, s * k ** (t - 1)])


@sh("pm_eksp", "yopiq")
def pm_ek_2(rng):
    d = rng.choice([80, 160, 320, 640]); t = rng.choice([2, 3, 4])
    return _y(rng, f"Dori dozasi {d} mg. Har 6 soatda organizmdagi miqdor yarmiga kamayadi. {t * 6} soatdan keyin necha mg qoladi?", Fraction(d, 2 ** t), [f"{t} marta yarmiga: {d} : 2^{t} = {num(Fraction(d, 2 ** t))} mg."], noto=[Fraction(d, 2) - t, Fraction(d, t), d - 10 * t])


@sh("pm_eksp", "yopiq")
def pm_ek_3(rng):
    a = rng.choice([5, 10, 20]); n = rng.choice([5, 6, 7])
    return _y(rng, f"A usulda har davrda +{a} qo‘shiladi (boshida {a}), B usulda har davrda ×2 (boshida {a}). {n}-davrdan keyin B usuldagi qiymat qancha?", a * 2 ** n, [f"B: {a}·2^{n} = {a * 2 ** n}; A: {a} + {a}·{n} = {a + a * n} — B ancha katta."], noto=[a * 2 * n, a + a * n, a * 2 ** (n - 1)])


@sh("pm_eksp", "yopiq")
def pm_ek_4(rng):
    s = rng.choice([1, 2, 5]); 
    return _y(rng, "Qaysi holatda o‘sish ‘tezlashib boradi’ (eksponensial)?", "Har kuni oldingi kunga nisbatan 2 marta ko‘payish", ["Ko‘paytirish bilan o‘sish tezlashadi; qo‘shish bilan — bir xil tezlikda."], noto=["Har kuni 5 tadan qo‘shilishi", "Har kuni bir xil masofa yurish", "Har oy bir xil maosh olish"])


@sh("pm_eksp", "ochiq")
def pm_ek_5(rng):
    s = rng.choice([3, 5, 10]); t = rng.choice([3, 4, 5])
    return _o(f"Gripp virusi sinfda har kuni 2 baravar ko‘paymoqda. 1-kuni {s} ta kasal.", [(f"a) {t}-kuni nechta? (1-kun — {s})", s * 2 ** (t - 1)), ("b) Qaysi kuni birinchi marta 100 dan oshadi?", next(i for i in range(1, 20) if s * 2 ** (i - 1) > 100))],
              [f"a) {s}·2^{t - 1} = {s * 2 ** (t - 1)}.", f"b) Kunlar: " + ", ".join(str(s * 2 ** (i - 1)) for i in range(1, 9)) + "…"])


@sh("pm_eksp", "ochiq")
def pm_ek_6(rng):
    d = rng.choice([200, 400, 800]); t = rng.choice([3, 4])
    return _o(f"Yarim yemirilish davri 1 soat bo‘lgan moddaning massasi boshida {d} g.", [(f"a) {t} soatdan keyin (g):", Fraction(d, 2 ** t)), ("b) 1 soatdan keyin yo‘qolgan massa (g):", d // 2)], [f"a) {d} / 2^{t} = {num(Fraction(d, 2 ** t))}.", f"b) {d} − {d // 2} = {d // 2}."])


@sh("pm_eksp", "ochiq")
def pm_ek_7(rng):
    s = rng.choice([1000, 2000, 5000]); r = rng.choice([10, 20]); n = rng.choice([2, 3])
    k = s * (100 + r) ** n // 100 ** n
    return _o(f"Qishloq aholisi har yili {r}% ga ko‘paymoqda. Hozir {som(s)} kishi.", [(f"a) {n} yildan keyin aholi soni:", k), ("b) Chiziqli o‘sish (har yili +{0}) bo‘lsa shu vaqtda:".format(s * r // 100), s + s * r // 100 * n)], [f"a) {som(s)}·{num(Fraction(100 + r, 100))}^{n} = {som(k)}.", f"b) {som(s)} + {s * r // 100}·{n} = {som(s + s * r // 100 * n)}."])


# ═════════ 8-BO'LIM · YUZA VA PERIMETR ═════════
tema("pm_perimetr", "PM-8", "Perimetr: to‘siq, ramka va yo‘lak", "🧱", "Tomonlar uzunligi bo‘yicha perimetr, to‘siq va ramka uchun material hisobi", [
    ("Perimetr", "P = tomonlar yig‘indisi\nTo‘g‘ri to‘rtburchak: P = 2(a + b)\nKvadrat: P = 4a",
     "Perimetr — shaklning barcha tomonlari uzunliklari yig‘indisi. To‘g‘ri to‘rtburchakda ikki uzunlik va ikki kenglik qo‘shiladi. Kvadratda tomon to‘rtga ko‘paytiriladi."),
    ("Murakkab shakllar", "L shakl: tashqi tomonlar yig‘indisi\nPerimetr = katta to‘rtburchak perimetri",
     "L shaklli maydon perimetrini topishda barcha tashqi tomonlarni qo‘shamiz. Kesilgan burchak perimetrni o‘zgartirmaydi — bu o‘ziga xos qoida."),
    ("Material hisobi", "Uzunlik / bir dona uzunligi = dona\nHar doim yuqoriga yaxlitla",
     "To‘siq uchun nechta ustun yoki ramka uchun necha metr reyka kerakligini hisoblashda perimetrni bir dona uzunligiga bo‘lamiz va natijani yuqoriga yaxlitlaymiz."),
])


@sh("pm_perimetr", "yopiq")
def pm_pe_1(rng):
    a = rng.randint(6, 30); b = rng.randint(4, 20)
    return rasmli(_y(rng, f"To‘g‘ri to‘rtburchak shaklidagi bog‘ tomonlari {a} m va {b} m. Atrofini o‘rash uchun necha metr to‘r kerak?", 2 * (a + b), [f"P = 2(a + b) = 2·({a} + {b}) = {2 * (a + b)} m."], noto=[a * b, a + b, 2 * a + b]), fig_tortburchak(a, b))


@sh("pm_perimetr", "yopiq")
def pm_pe_2(rng):
    a = rng.randint(10, 25); b = rng.randint(8, 18); c = rng.randint(2, a // 2); d = rng.randint(2, b // 2)
    return rasmli(_y(rng, f"Chizmada L shaklli maydon: katta to‘rtburchak {a}×{b} m, undan {c}×{d} m burchak kesilgan. Perimetr necha metr?", 2 * (a + b), ["Kesilgan burchak perimetrni o‘zgartirmaydi: 2(a + b) = " + str(2 * (a + b)) + " m."], noto=[2 * (a + b) - 2 * (c + d), 2 * (a + b) + 2 * (c + d), a * b - c * d]), fig_L(a, b, c, d))


@sh("pm_perimetr", "yopiq")
def pm_pe_3(rng):
    P = rng.choice([48, 60, 80, 120]); st = rng.choice([2, 3, 4, 5])
    return _y(rng, f"Atrofi {P} m bo‘lgan maydonga har {st} m da bitta ustun o‘rnatiladi (burchaklarda ham). Nechta ustun kerak?", P // st if P % st == 0 else -(-P // st), [f"{P} : {st} = {P / st:g} → {-(-P // st)} ta."], noto=[P // st + 1, P // st - 1, P])


@sh("pm_perimetr", "yopiq")
def pm_pe_4(rng):
    a = rng.randint(5, 30)
    return _y(rng, f"Kvadrat perimetri {4 * a} sm. Uning tomoni necha sm?", a, [f"{4 * a} : 4 = {a}."], noto=[4 * a, a * a, 2 * a])


@sh("pm_perimetr", "ochiq")
def pm_pe_5(rng):
    a = rng.randint(8, 25); b = rng.randint(6, 18); p = rng.choice([8, 12, 15]) * 1000
    return _o(f"To‘g‘ri to‘rtburchak bog‘ {a} m × {b} m. To‘r 1 metri {som(p)} so‘m.", [("a) Perimetr (m):", 2 * (a + b)), ("b) To‘r narxi (so‘m):", 2 * (a + b) * p)], [f"a) 2·({a}+{b}) = {2 * (a + b)}.", f"b) {2 * (a + b)} · {som(p)} = {som(2 * (a + b) * p)}."])


@sh("pm_perimetr", "ochiq")
def pm_pe_6(rng):
    P = rng.choice([40, 56, 72, 90]); a = rng.randint(8, P // 2 - 6)
    return _o(f"To‘g‘ri to‘rtburchak perimetri {P} sm, bir tomoni {a} sm.", [("a) Ikkinchi tomon (sm):", P // 2 - a), ("b) Yuza (sm²):", a * (P // 2 - a))], [f"a) {P} : 2 − {a} = {P // 2 - a}.", f"b) {a}·{P // 2 - a} = {a * (P // 2 - a)}."])


@sh("pm_perimetr", "ochiq")
def pm_pe_7(rng):
    a = rng.randint(3, 9); k = rng.choice([2, 3, 4])
    return _o(f"Kvadrat shaklidagi rasm tomoni {a} dm. Atrofiga {k} qator ramka o‘rnatiladi.", [("a) Bir qator uchun uzunlik (dm):", 4 * a), (f"b) {k} qator uchun uzunlik (dm):", 4 * a * k)], [f"a) 4·{a} = {4 * a}.", f"b) {4 * a}·{k} = {4 * a * k}."])


tema("pm_yuza2", "PM-8", "Murakkab shakllar yuzi va qirqish", "🧩", "L va T shakllar, ichi bo‘sh shakllar, uchburchak va trapetsiya yuzi", [
    ("Asosiy yuzalar", "To‘rtburchak: a·b\nUchburchak: ½·a·h\nTrapetsiya: ½(a + b)·h",
     "To‘g‘ri to‘rtburchak yuzi — ikki tomon ko‘paytmasi. Uchburchak yuzi — asosi bilan balandligi ko‘paytmasining yarmi. Trapetsiya — asoslar yig‘indisining yarmi ko‘paytirilsin balandlikka."),
    ("Bo‘lish va ayirish", "L shakl = katta − kesilgan\nYoki ikki to‘rtburchakka bo‘ling\nIchi bo‘sh = tashqi − ichki",
     "Murakkab shaklni oddiy bo‘laklarga bo‘lamiz yoki katta shakldan ortiqchasini ayiramiz. Masalan, L shakl yuzi — katta to‘rtburchak yuzidan kesilgan qism yuzini ayirib topiladi."),
    ("Birliklar", "m² = 10 000 sm²\nGa = 10 000 m²\nYuza birliklari kvadrat!",
     "Yuza birliklarini almashtirishda kvadratga ehtiyot bo‘ling: bir kvadrat metrda o‘n ming kvadrat santimetr bor. Bir gektar — o‘n ming kvadrat metr."),
])


@sh("pm_yuza2", "yopiq")
def pm_yu_1(rng):
    a = rng.randint(10, 25); b = rng.randint(8, 18); c = rng.randint(2, a // 2); d = rng.randint(2, b // 2)
    return rasmli(_y(rng, f"L shaklli maydon: katta to‘rtburchak {a}×{b} m, undan {c}×{d} m burchak kesilgan. Yuzi necha m²?", a * b - c * d, [f"{a}·{b} − {c}·{d} = {a * b} − {c * d} = {a * b - c * d} m²."], noto=[a * b + c * d, a * b, 2 * (a + b)]), fig_L(a, b, c, d))


@sh("pm_yuza2", "yopiq")
def pm_yu_2(rng):
    a = rng.choice([6, 8, 10, 12, 14]); h = rng.choice([4, 5, 7, 9])
    return _y(rng, f"Uchburchak asosi {a} sm, balandligi {h} sm. Yuzi necha sm²?", Fraction(a * h, 2), [f"S = ½·{a}·{h} = {num(Fraction(a * h, 2))}."], noto=[a * h, a + h, Fraction(a * h, 3)])


@sh("pm_yuza2", "yopiq")
def pm_yu_3(rng):
    a = rng.choice([6, 8, 10, 12]); b = a + rng.choice([2, 4, 6]); h = rng.choice([3, 4, 5, 6])
    return _y(rng, f"Trapetsiya asoslari {a} m va {b} m, balandligi {h} m. Yuzi necha m²?", Fraction((a + b) * h, 2), [f"S = ½({a} + {b})·{h} = {num(Fraction((a + b) * h, 2))}."], noto=[a * b, (a + b) * h, Fraction(a * b * h, 2)])


@sh("pm_yuza2", "yopiq")
def pm_yu_4(rng):
    n = rng.choice([3, 5, 8, 12]); 
    return _y(rng, f"{n} m² necha sm²?", n * 10000, [f"1 m² = 100·100 = 10 000 sm²; {n}·10 000 = {som(n * 10000)}."], noto=[n * 100, n * 1000, n * 100000])


@sh("pm_yuza2", "ochiq")
def pm_yu_5(rng):
    a = rng.randint(12, 30); b = rng.randint(8, 20); w = rng.choice([1, 2])
    return _o(f"Hovuz {a}×{b} m, atrofida {w} m kenglikdagi yo‘lak bor (ichkarida hovuz emas — yo‘lak hovuzni o‘rab turadi, tashqi o‘lchamlar {a + 2 * w}×{b + 2 * w} m).", [("a) Tashqi to‘rtburchak yuzi (m²):", (a + 2 * w) * (b + 2 * w)), ("b) Yo‘lak yuzi (m²):", (a + 2 * w) * (b + 2 * w) - a * b)],
              [f"a) {a + 2 * w}·{b + 2 * w} = {(a + 2 * w) * (b + 2 * w)}.", f"b) {(a + 2 * w) * (b + 2 * w)} − {a * b} = {(a + 2 * w) * (b + 2 * w) - a * b}."])


@sh("pm_yuza2", "ochiq")
def pm_yu_6(rng):
    a = rng.randint(12, 26); b = rng.randint(8, 16); c = rng.randint(2, 5); d = rng.randint(2, 5)
    return rasmli(_o(f"Maydon L shaklida: {a}×{b} m to‘rtburchakdan {c}×{d} m burchak kesilgan.", [("a) Maydon yuzi (m²):", a * b - c * d), ("b) Perimetri (m):", 2 * (a + b))], [f"a) {a}·{b} − {c}·{d} = {a * b - c * d}.", f"b) 2({a}+{b}) = {2 * (a + b)}."]), fig_L(a, b, c, d))


@sh("pm_yuza2", "ochiq")
def pm_yu_7(rng):
    a = rng.choice([8, 10, 12, 14]); h = rng.choice([5, 6, 8, 9]); k = rng.choice([4, 6, 9])
    return _o(f"Tom shakli — uchburchak: asosi {a} m, balandligi {h} m. Har bir m² ga {k} ta shifer kerak.", [("a) Uchburchak yuzi (m²):", Fraction(a * h, 2)), ("b) Kerakli shifer soni:", Fraction(a * h, 2) * k)], [f"a) ½·{a}·{h} = {num(Fraction(a * h, 2))}.", f"b) {num(Fraction(a * h, 2))}·{k} = {num(Fraction(a * h, 2) * k)}."])


tema("pm_qoplash", "PM-8", "Qoplash: plitka, bo‘yoq va xarajat", "🎨", "Pol, devor va tom uchun material miqdori va narxini hisoblash", [
    ("Qoplanadigan yuza", "Yuza = uzunlik × kenglik\nDevor: perimetr × balandlik − eshik/deraza\nMaterial = yuza / bir dona yuzi",
     "Qoplash uchun avval yuzani topamiz. Devorlar yuzi — xona perimetri ko‘paytirilsin balandlikka, eshik va deraza yuzasi ayriladi. Keyin yuzani bir dona plitka yuziga bo‘lamiz."),
    ("Yaxlitlash", "Plitka soni — yuqoriga yaxlitla\nBo‘yoq: yuza / 1 litr qoplashi\n+ 10% zaxira",
     "Plitka yoki bo‘yoq hisobida natijani yuqoriga yaxlitlaymiz, chunki kamroq olsak yetmaydi. Amalda ozgina zaxira ham qo‘shiladi."),
    ("Xarajat", "Xarajat = miqdor × narx\nQiyosla: qaysi material arzon?",
     "Jami xarajat — kerakli miqdor ko‘paytirilsin bir birlik narxiga. Ikki xil materialni taqqoslab, arzonini tanlaymiz."),
])


@sh("pm_qoplash", "yopiq")
def pm_qo_1(rng):
    a = rng.choice([4, 5, 6, 8]); b = rng.choice([3, 4, 5, 6]); t = rng.choice([20, 25, 50]); n = a * b * 10000 // (t * t)
    return rasmli(_y(rng, f"Xonaning poli {a}×{b} m. Pol {t}×{t} sm li plitka bilan yopilmoqda. Nechta plitka kerak?", n, [f"Pol yuzi: {a}·{b} = {a * b} m² = {som(a * b * 10000)} sm².", f"Bir plitka: {t}·{t} = {t * t} sm². Soni: {som(a * b * 10000)} : {t * t} = {som(n)}."], noto=[n + t, n - t, n * 2]), fig_tortburchak(a, b))


@sh("pm_qoplash", "yopiq")
def pm_qo_2(rng):
    L_ = rng.choice([4, 5, 6]); W = rng.choice([3, 4, 5]); H = rng.choice([2, 3]); e = rng.choice([2, 3, 4]) 
    dev = 2 * (L_ + W) * H - e
    return _y(rng, f"Xona {L_}×{W} m, balandligi {H} m. Eshik va derazalar jami {e} m². Bo‘yaladigan devor yuzi necha m²?", dev, [f"Devor: 2({L_}+{W})·{H} = {2 * (L_ + W) * H} m².", f"Eshik-deraza ayriladi: {2 * (L_ + W) * H} − {e} = {dev}."], noto=[2 * (L_ + W) * H, 2 * (L_ + W) * H + e, L_ * W * H])


@sh("pm_qoplash", "yopiq")
def pm_qo_3(rng):
    S = rng.choice([30, 45, 60, 75, 90]); q = rng.choice([6, 8, 10, 12])
    return _y(rng, f"1 litr bo‘yoq {q} m² ni qoplaydi. {S} m² devor uchun necha litr kerak? (butunga yuqoriga yaxlitlang)", -(-S // q), [f"{S} : {q} = {S / q:.2f} → {-(-S // q)} litr."], noto=[S // q, -(-S // q) + 1, S - q])


@sh("pm_qoplash", "yopiq")
def pm_qo_4(rng):
    a = rng.choice([4, 5, 6]); b = rng.choice([3, 4, 5]); p1 = rng.choice([40, 50]) * 1000; p2 = p1 + rng.choice([10, 20]) * 1000
    S = a * b
    return _y(rng, f"{a}×{b} m xona uchun A laminat {som(p1)} so‘m/m², B laminat {som(p2)} so‘m/m². A laminat qancha arzon (so‘m)?", S * (p2 - p1), [f"Farq: {som(p2 - p1)} · {S} = {som(S * (p2 - p1))} so‘m."], noto=[S * p1, S * p2, p2 - p1])


@sh("pm_qoplash", "ochiq")
def pm_qo_5(rng):
    a = rng.choice([4, 5, 6, 8]); b = rng.choice([3, 4, 5, 6]); n = rng.choice([40, 50, 60]) * 1000
    return _o(f"Xona {a}×{b} m, parket narxi {som(n)} so‘m/m².", [("a) Pol yuzi (m²):", a * b), ("b) Parket xarajati (so‘m):", a * b * n)], [f"a) {a}·{b} = {a * b}.", f"b) {a * b}·{som(n)} = {som(a * b * n)}."])


@sh("pm_qoplash", "ochiq")
def pm_qo_6(rng):
    L_ = rng.choice([4, 5, 6]); W = rng.choice([3, 4]); H = 3; e = rng.choice([4, 5, 6]); q = 8
    dev = 2 * (L_ + W) * H - e
    return _o(f"Xona {L_}×{W} m, balandligi {H} m, eshik-derazalar {e} m². 1 litr bo‘yoq {q} m² ga yetadi.", [("a) Bo‘yaladigan yuza (m²):", dev), ("b) Kerakli bo‘yoq (litr, butunga yuqoriga):", -(-dev // q))], [f"a) 2({L_}+{W})·{H} − {e} = {dev}.", f"b) {dev} : {q} = {dev / q:.2f} → {-(-dev // q)} litr."])


@sh("pm_qoplash", "ochiq")
def pm_qo_7(rng):
    a = rng.choice([30, 40, 50]); S = rng.choice([12, 18, 24]); 
    n = -(-S * 10000 // (a * a))
    return _o(f"{S} m² maydon {a}×{a} sm li plitka bilan yopiladi.", [("a) Bitta plitka yuzi (sm²):", a * a), ("b) Kerakli plitka soni (butunga yuqoriga):", n)], [f"a) {a}² = {a * a}.", f"b) {som(S * 10000)} : {a * a} = {S * 10000 / (a * a):.1f} → {n}."])


# ═════════ 9-BO'LIM · HAJM VA SIRT ═════════
tema("pm_hajm", "PM-9", "Hajm: quti, silindr va idish", "📦", "Quti, bochka va hovuz hajmi; litrga o‘tkazish; to‘lish vaqti", [
    ("Quti hajmi", "V = a · b · h\n1 m³ = 1000 litr\n1 dm³ = 1 litr",
     "To‘g‘ri burchakli qutining hajmi — uch o‘lcham ko‘paytmasi. Bir kub metr — ming litr, bir kub detsimetr — bir litr."),
    ("Silindr", "V = π · r² · h\nπ ≈ 3,14\nBochka: r = 0,5 m, h = 1 m → V ≈ 0,785 m³",
     "Silindr hajmi — asos yuzi ko‘paytirilsin balandlikka. Asos — doira, uning yuzi pi er kvadrat. Pi taxminan uch butun o‘n to‘rt."),
    ("Suv to‘lishi", "Vaqt = hajm / sarf\n1 m³ = 1000 l\nSarf: litr/daqiqa",
     "Idish necha daqiqada to‘lishini topish uchun hajmini litrda ifodalaymiz va daqiqadagi suv sarfiga bo‘lamiz."),
])


@sh("pm_hajm", "yopiq")
def pm_ha_1(rng):
    a = rng.randint(2, 9); b = rng.randint(2, 9); h = rng.randint(2, 9)
    return rasmli(_y(rng, f"Quti o‘lchamlari {a}×{b}×{h} sm. Hajmi necha sm³?", a * b * h, [f"V = {a}·{b}·{h} = {a * b * h} sm³."], noto=[a * b + h, a + b + h, 2 * (a * b + b * h + a * h)]), fig_quti(a, b, h))


@sh("pm_hajm", "yopiq")
def pm_ha_2(rng):
    a = rng.choice([1, 2, 3]); b = rng.choice([2, 3, 4]); h = rng.choice([1, 2]); 
    return _y(rng, f"Hovuz {a * 5}×{b * 2}×{h} m o‘lchamli. Unga necha litr suv sig‘adi?", a * 5 * b * 2 * h * 1000, [f"V = {a * 5 * b * 2 * h} m³ = {som(a * 5 * b * 2 * h * 1000)} litr."], noto=[a * 5 * b * 2 * h, a * 5 * b * 2 * h * 100, a * 5 * b * 2 * h * 10000])


@sh("pm_hajm", "yopiq")
def pm_ha_3(rng):
    r = rng.choice([1, 2, 3, 5]); h = rng.choice([2, 4, 5, 10]); v = Fraction(314, 100) * r * r * h
    return rasmli(_y(rng, f"Silindr: r = {r} dm, h = {h} dm (π ≈ 3,14). Hajmi necha dm³ (litr)?", v, [f"V = π r² h = 3,14·{r * r}·{h} = {num(v)} dm³."], noto=[Fraction(314, 100) * r * h, v * 2, Fraction(314, 100) * r * r]), fig_silindr(r, h, "dm"))


@sh("pm_hajm", "yopiq")
def pm_ha_4(rng):
    V = rng.choice([600, 900, 1200, 1500, 2400]); s = rng.choice([20, 30, 40, 50, 60])
    return _y(rng, f"Hajmi {som(V)} litr bo‘lgan idish daqiqasiga {s} litr suv beradigan kran bilan to‘ldiriladi. Necha daqiqada to‘ladi?", V // s if V % s == 0 else -(-V // s), [f"{V} : {s} = {V / s:g} daqiqa."], noto=[V // s + 5, V - s, V // s - 3])


@sh("pm_hajm", "ochiq")
def pm_ha_5(rng):
    a = rng.randint(3, 8); b = rng.randint(3, 8); h = rng.randint(2, 6)
    return rasmli(_o(f"Akvarium o‘lchamlari {a}×{b}×{h} dm.", [("a) Hajm (dm³ = litr):", a * b * h), ("b) 3/4 qismigacha to‘ldirilganda necha litr suv?", Fraction(3 * a * b * h, 4))], [f"a) {a}·{b}·{h} = {a * b * h}.", f"b) {a * b * h} · 3/4 = {num(Fraction(3 * a * b * h, 4))}."]), fig_quti(a, b, h, "dm"))


@sh("pm_hajm", "ochiq")
def pm_ha_6(rng):
    r = rng.choice([1, 2, 5]); h = rng.choice([5, 10, 20]); v = Fraction(314, 100) * r * r * h
    return rasmli(_o(f"Konserva bankasi silindr shaklida: r = {r} sm, h = {h} sm (π ≈ 3,14).", [("a) Asos yuzi (sm²):", Fraction(314, 100) * r * r), ("b) Hajm (sm³):", v)], [f"a) 3,14·{r * r} = {num(Fraction(314, 100) * r * r)}.", f"b) {num(Fraction(314, 100) * r * r)}·{h} = {num(v)}."]), fig_silindr(r, h, "sm"))


@sh("pm_hajm", "ochiq")
def pm_ha_7(rng):
    V = rng.choice([300, 480, 600, 900]); s = rng.choice([20, 30, 40, 60])
    return _o(f"Bochkada {V} litr suv bor. Kranni ochib, daqiqasiga {s} litr suv chiqarilmoqda.", [("a) Necha daqiqada bo‘shaydi?", Fraction(V, s)), ("b) 5 daqiqadan keyin qancha suv qoladi (litr)?", V - 5 * s)], [f"a) {V} : {s} = {num(Fraction(V, s))}.", f"b) {V} − 5·{s} = {V - 5 * s}."])


tema("pm_sirt", "PM-9", "Sirt yuzi: qadoq, bo‘yash va o‘rash", "🎁", "Quti, silindr va kub sirtini topish; qog‘oz va bo‘yoq hisobi", [
    ("Quti sirti", "S = 2(ab + bh + ah)\nKub: S = 6a²\n6 ta yoq — hammasini qo‘shing",
     "To‘g‘ri burchakli qutining sirti — oltita yoq yuzasi yig‘indisi. Qarama-qarshi yoqlar teng bo‘lgani uchun uch juft yuzani topib, ikkiga ko‘paytiramiz. Kubda oltita bir xil kvadrat bor."),
    ("Ochiq quti", "Qopqoqsiz: 5 ta yoq\nHovuz: tubi + 4 devor\nBo‘yoq faqat tashqi sirtga",
     "Hovuz yoki qopqoqsiz quti uchun faqat mavjud yoqlar yuzini qo‘shamiz. Masalan, hovuzda tub va to‘rtta devor — beshta yoq."),
    ("Silindr sirti", "Yon sirt = 2πrh\nTo‘la sirt = 2πrh + 2πr²\nOrash qog‘ozi = yon sirt",
     "Silindrning yon sirti ochilsa to‘g‘ri to‘rtburchak chiqadi: eni — aylana uzunligi, bo‘yi — balandlik. To‘la sirt uchun ikki asos yuzini qo‘shamiz."),
])


@sh("pm_sirt", "yopiq")
def pm_si_1(rng):
    a = rng.randint(2, 9); b = rng.randint(2, 9); h = rng.randint(2, 9)
    return rasmli(_y(rng, f"Quti {a}×{b}×{h} sm. Uni to‘liq o‘rash uchun necha sm² qog‘oz kerak (chok va bukilishsiz)?", 2 * (a * b + b * h + a * h), [f"S = 2({a}·{b} + {b}·{h} + {a}·{h}) = 2·{a * b + b * h + a * h} = {2 * (a * b + b * h + a * h)} sm²."], noto=[a * b * h, 2 * a * b + 2 * h, a * b + b * h + a * h]), fig_quti(a, b, h))


@sh("pm_sirt", "yopiq")
def pm_si_2(rng):
    a = rng.randint(2, 15)
    return _y(rng, f"Kub qirrasi {a} dm. Uni bo‘yash uchun sirt yuzi necha dm²?", 6 * a * a, [f"6·{a}² = {6 * a * a}."], noto=[a ** 3, 4 * a * a, 12 * a])


@sh("pm_sirt", "yopiq")
def pm_si_3(rng):
    a = rng.choice([4, 5, 6, 8]); b = rng.choice([3, 4, 5]); h = rng.choice([2, 3])
    return _y(rng, f"Hovuz {a}×{b} m, chuqurligi {h} m. Uning tubi va 4 ta devorini kafel bilan qoplash uchun necha m² kerak?", a * b + 2 * (a + b) * h, [f"Tub: {a * b}; devorlar: 2({a}+{b})·{h} = {2 * (a + b) * h}. Jami {a * b + 2 * (a + b) * h} m²."], noto=[2 * (a + b) * h, a * b * h, a * b + (a + b) * h])


@sh("pm_sirt", "yopiq")
def pm_si_4(rng):
    r = rng.choice([1, 2, 5]); h = rng.choice([10, 20, 30]); y = Fraction(628, 100) * r * h
    return rasmli(_y(rng, f"Silindr shaklidagi bankaga etiketka yopishtiriladi (π ≈ 3,14): r = {r} sm, h = {h} sm. Yon sirt yuzi necha sm²?", y, [f"S = 2πrh = 2·3,14·{r}·{h} = {num(y)} sm²."], noto=[y / 2, Fraction(314, 100) * r * r * h, y + Fraction(628, 100) * r * r]), fig_silindr(r, h))


@sh("pm_sirt", "ochiq")
def pm_si_5(rng):
    a = rng.randint(3, 9); b = rng.randint(3, 9); h = rng.randint(3, 9); p = rng.choice([2, 3, 5]) * 100
    S = 2 * (a * b + b * h + a * h)
    return rasmli(_o(f"Quti o‘lchamlari {a}×{b}×{h} dm. Sirtini bo‘yash narxi 1 dm² uchun {p} so‘m.", [("a) Sirt yuzi (dm²):", S), ("b) Bo‘yash narxi (so‘m):", S * p)], [f"a) 2({a * b} + {b * h} + {a * h}) = {S}.", f"b) {S}·{p} = {som(S * p)}."]), fig_quti(a, b, h, "dm"))


@sh("pm_sirt", "ochiq")
def pm_si_6(rng):
    a = rng.choice([4, 5, 6]); b = rng.choice([3, 4, 5]); h = rng.choice([1, 2])
    return _o(f"Ochiq (qopqoqsiz) quti: tubi {a}×{b} sm, balandligi {h * 10} sm.", [("a) Tub yuzi (sm²):", a * b), ("b) Jami sirt (qopqoqsiz, sm²):", a * b + 2 * (a + b) * h * 10)], [f"a) {a}·{b} = {a * b}.", f"b) {a * b} + 2({a}+{b})·{h * 10} = {a * b + 2 * (a + b) * h * 10}."])


@sh("pm_sirt", "ochiq")
def pm_si_7(rng):
    a = rng.randint(2, 6); k = rng.choice([2, 3])
    return _o(f"Kub qirrasi {a} sm. Qirrasi {k} marta oshirilsa:", [("a) Dastlabki sirt (sm²):", 6 * a * a), ("b) Yangi sirt (sm²):", 6 * (a * k) ** 2)], [f"a) 6·{a}² = {6 * a * a}.", f"b) 6·({a * k})² = {6 * (a * k) ** 2} ({k * k} marta katta)."])
