"""PISA matematika: hayotiy masala generatorlari. Har shablon (rng) -> savol dict; javob va yechim KOD bilan hisoblanadi.
tur: yopiq (4 variant, 1 ball) | ochiq (qismlar a,b; qisqa=1 qism 2 ball, ikki qism 4 ball)."""
import math
from fractions import Fraction

from modules import mock_lib as L
from modules.mock_fig import _svg, _t, _l, _poly

SH = {}   # mavzu -> [(funksiya, tur)]


def reg(mavzu, tur):
    def d(f):
        SH.setdefault(mavzu, []).append((f, tur))
        return f
    return d


def som(n):
    return f"{int(n):,}".replace(",", " ")


def num(x):
    """Kasr/son → o'quvchi ko'rinishi (o'nli vergul)."""
    x = Fraction(x)
    if x.denominator == 1:
        return str(x.numerator)
    s = f"{float(x):.4f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def mm(x):
    """Son → matematik ko'rinish (o'nli vergul, bo'shliqsiz)."""
    return num(x).replace(",", "{,}")


def _yopiq(rng, savol, togri, yech, noto=(), tartib=True):
    """4 variantli savol. Qiymatlar: son/Fraction (o'nli vergul bilan) yoki matn («$…$» bilan boshlansa — formula)."""
    def kor(v):
        return v if isinstance(v, str) else f"${mm(v)}$"
    nomerik = not isinstance(togri, str)
    ruy, korildi = [], {kor(togri)}
    ya = [] if not nomerik else L._yaqin(togri, rng)
    if nomerik and Fraction(togri) >= 0:
        ya = [x for x in ya if Fraction(x) >= 0]
    for x in list(noto) + ya:
        if nomerik and not isinstance(x, str) and Fraction(togri) >= 0 and Fraction(x) < 0:
            continue
        if kor(x) not in korildi:
            ruy.append(x); korildi.add(kor(x))
        if len(ruy) == 3:
            break
    if len(ruy) < 3:
        raise ValueError("variant yetmadi")
    hamma = [togri] + ruy
    if tartib and all(not isinstance(x, str) for x in hamma):
        hamma.sort(key=lambda x: Fraction(x))
    else:
        rng.shuffle(hamma)
    return {"tur": "yopiq", "savol": savol, "variantlar": [kor(x) for x in hamma], "javob": "ABCD"[[kor(x) for x in hamma].index(kor(togri))],
            "yechim": yech if isinstance(yech, str) else "\n".join(yech)}


_y = _yopiq


def _o(umumiy, qismlar, yech):
    q = L.ochiq(umumiy, qismlar, yech)
    import re as _re
    for z, (_, j) in zip(q["qismlar"], qismlar):
        z["javob"] = mm(j)
        z["savol"] = _re.sub(r"^[ab]\)\s*", "", z["savol"])
    return q


def _txt(rng, alt):
    return alt[rng.randrange(len(alt))]


# ───────────────────────── chizmalar ─────────────────────────
def fig_stolbik(nomlar, qiymatlar, sarlavha="", birlik=""):
    W, H, x0, y0 = 320, 210, 40, 170
    mx = max(qiymatlar); step = 10 ** (len(str(int(mx))) - 1)
    top = math.ceil(mx / step) * step
    body = _t(W / 2, 16, sarlavha, it=False, size=13)
    for k in range(0, 5):
        v = top * k / 4; y = y0 - 140 * k / 4
        body += _l((x0, y), (W - 10, y), w=.5, col="#bbb") + _t(x0 - 4, y + 4, f"{v:g}", it=False, anchor="end", size=10)
    bw = (W - x0 - 20) / len(qiymatlar)
    for i, (n, v) in enumerate(zip(nomlar, qiymatlar)):
        h = 140 * v / top; x = x0 + 8 + i * bw
        body += f'<rect x="{x:.1f}" y="{y0 - h:.1f}" width="{bw - 16:.1f}" height="{h:.1f}" fill="#5b8def" stroke="#111" stroke-width="1"/>'
        body += _t(x + (bw - 16) / 2, y0 - h - 4, f"{v:g}", it=False, size=11) + _t(x + (bw - 16) / 2, y0 + 14, n, it=False, size=11)
    if birlik:
        body += _t(x0, 190 + 14, birlik, it=False, anchor="start", size=10)
    return _svg(body, W, 215)


def fig_chiziq(b, k, xmax, xnom="x", ynom="y", belgi=(), sarlavha=""):
    """y = k*x + b grafigi (0..xmax); belgi: x lar — nuqtalar belgilanadi (qiymati yozilmaydi)."""
    W, H, x0, y0 = 320, 220, 46, 185
    ymax = b + k * xmax; top = math.ceil(ymax / 5) * 5 or 5
    sx = (W - x0 - 20) / xmax; sy = 150 / top
    body = _t(W / 2, 14, sarlavha, it=False, size=12)
    body += _l((x0, y0), (W - 10, y0)) + _l((x0, y0), (x0, 25))
    for i in range(0, xmax + 1, max(1, xmax // 5)):
        body += _l((x0 + i * sx, y0), (x0 + i * sx, y0 + 4)) + _t(x0 + i * sx, y0 + 16, str(i), it=False, size=10)
    for j in range(0, 5):
        v = top * j / 4
        body += _l((x0 - 4, y0 - v * sy), (W - 10, y0 - v * sy), w=.4, col="#ccc") + _t(x0 - 6, y0 - v * sy + 3, f"{v:g}", it=False, anchor="end", size=10)
    body += _l((x0, y0 - b * sy), (x0 + xmax * sx, y0 - (b + k * xmax) * sy), w=2, col="#d33")
    for xv in belgi:
        yv = b + k * xv
        body += f'<circle cx="{x0 + xv * sx:.1f}" cy="{y0 - yv * sy:.1f}" r="3.5" fill="#d33"/>'
    body += _t(W - 12, y0 + 16, xnom, it=True, anchor="end", size=12) + _t(x0 + 12, 24, ynom, it=True, size=12)
    return _svg(body, W, 215)


def fig_tortburchak(a, b, birlik="m", tom=True, ichki=None):
    s = min(220 / a, 120 / b)
    x0, y0 = 40, 30
    body = f'<rect x="{x0}" y="{y0}" width="{a * s:.1f}" height="{b * s:.1f}" fill="#eef5ff" stroke="#111" stroke-width="1.5"/>'
    if tom:
        body += _t(x0 + a * s / 2, y0 + b * s + 16, f"{num(a)} {birlik}", it=False, size=12) + _t(x0 - 6, y0 + b * s / 2 + 4, f"{num(b)} {birlik}", it=False, anchor="end", size=12)
    if ichki:
        w, h = ichki
        body += f'<rect x="{x0 + 8}" y="{y0 + b * s - h * s - 6:.1f}" width="{w * s:.1f}" height="{h * s:.1f}" fill="#ffd9a8" stroke="#111"/>' + _t(x0 + 8 + w * s / 2, y0 + b * s - h * s / 2 - 2, "eshik", it=False, size=10)
    return _svg(body, 300, 190)


def fig_L(a, b, c, d):
    """L shakl: katta to'rtburchak a×b, undan yuqori-o'ng burchakdan c×d kesilgan."""
    s = min(200 / a, 130 / b); x0, y0 = 50, 25
    P = [(0, 0), (a - c, 0), (a - c, d), (a, d), (a, b), (0, b)]
    pts = " ".join(f"{x0 + x * s:.1f},{y0 + y * s:.1f}" for x, y in P)
    body = f'<polygon points="{pts}" fill="#eef5ff" stroke="#111" stroke-width="1.5"/>'
    body += _t(x0 + a * s / 2, y0 + b * s + 16, f"{a} m", it=False, size=12) + _t(x0 - 6, y0 + b * s / 2 + 4, f"{b} m", it=False, anchor="end", size=12)
    body += _t(x0 + (a - c / 2) * s, y0 - 6, f"{c} m", it=False, size=12) + _t(x0 + a * s + 6, y0 + d * s / 2 + 4, f"{d} m", it=False, anchor="start", size=12)
    return _svg(body, 300, 190)


def fig_narvon(x, h):
    s = 150 / max(x, h); C = (60, 175); B = (60 + x * s, 175); A = (60, 175 - h * s)
    body = _l(C, B, w=2) + _l(C, A, w=3, col="#8a5a2b") + _l(A, B, w=2.5, col="#2b6cb0")
    body += f'<path d="M{C[0] + 9},{C[1]} v-9 h-9" fill="none" stroke="#111"/>'
    body += _t((C[0] + B[0]) / 2, C[1] + 16, f"{num(x)} m", it=False, size=12) + _t(C[0] - 10, (C[1] + A[1]) / 2, f"{num(h)} m", it=False, anchor="end", size=12)
    body += _t((A[0] + B[0]) / 2 + 18, (A[1] + B[1]) / 2 - 6, "narvon ?", it=False, size=12) + _t(C[0] - 10, C[1] + 14, "devor", it=False, anchor="end", size=10)
    return _svg(body, 300, 200)


# ───────────────────────── 1) FOIZ ─────────────────────────
BUYUM = ["Planshet", "Krossovka", "Qishki kurtka", "Velosiped", "Naushnik", "Ryukzak", "Sovutgich", "Smartfon", "Kitob javoni", "Choynak"]


@reg("pisa_foiz", "yopiq")
def foiz_chegirma(rng):
    P = rng.choice(range(120, 960, 20)) * 1000; d = rng.choice([10, 15, 20, 25, 30, 40]); b = rng.choice(BUYUM)
    chg = P * d // 100; yangi = P - chg
    return _y(rng, f"«{b}» do‘konda {som(P)} so‘m turadi. Hafta oxirida unga {d}% chegirma e’lon qilindi. Chegirmadan keyingi narx qancha (so‘m)?", yangi,
              [f"Chegirma miqdori: {som(P)} · {d}/100 = {som(chg)} so‘m.", f"Yangi narx: {som(P)} − {som(chg)} = {som(yangi)} so‘m."], noto=[chg, P + chg, P - d * 1000])


@reg("pisa_foiz", "yopiq")
def foiz_oshish(rng):
    a = rng.choice(range(20, 200, 10)) * 100; p = rng.choice([10, 20, 25, 30, 40, 50]); bb = a * (100 + p) // 100
    return _y(rng, f"Bir kilogramm olma narxi {som(a)} so‘m edi, keyin {som(bb)} so‘m bo‘ldi. Narx necha foizga oshgan?", p,
              [f"Oshgan miqdor: {som(bb)} − {som(a)} = {som(bb - a)} so‘m.", f"Foiz = oshgan miqdor / eski narx · 100 = {som(bb - a)} / {som(a)} · 100 = {p}%."],
              noto=[p + 10, p // 2 if p % 2 == 0 else p - 5, 100 * (bb - a) // bb if (bb - a) * 100 % bb == 0 else p + 5, 100 + p])


@reg("pisa_foiz", "ochiq")
def foiz_ketma(rng):
    P = rng.choice(range(100, 800, 20)) * 1000; d1 = rng.choice([10, 20, 30]); d2 = rng.choice([10, 20, 25, 50])
    p1 = P * (100 - d1) // 100; p2 = p1 * (100 - d2) // 100
    return _o(f"Do‘konda palto {som(P)} so‘m. Avval {d1}% chegirma, keyin chegirmali narxdan yana {d2}% chegirma qilindi. Palto oxirida necha so‘m bo‘ldi?", [("Javobingiz (so‘m):", p2)],
              [f"1-chegirmadan keyin: {som(P)} · {100 - d1}/100 = {som(p1)} so‘m.", f"2-chegirma shu narxdan olinadi: {som(p1)} · {100 - d2}/100 = {som(p2)} so‘m.", f"Diqqat: umumiy chegirma {d1}% + {d2}% = {d1 + d2}% emas!"])


@reg("pisa_foiz", "ochiq")
def foiz_soliq(rng):
    X = rng.choice(range(50, 500, 10)) * 1000; q = rng.choice([12, 15, 20]); soliq = X * q // 100
    return _o(f"Dazmol narxi QQS siz {som(X)} so‘m. QQS {q}% ni tashkil etadi.", [("a) QQS miqdori necha so‘m?", soliq), ("b) Xaridor kassada necha so‘m to‘laydi?", X + soliq)],
              [f"a) {som(X)} · {q}/100 = {som(soliq)} so‘m.", f"b) {som(X)} + {som(soliq)} = {som(X + soliq)} so‘m."])


@reg("pisa_foiz", "ochiq")
def foiz_bank(rng):
    S = rng.choice(range(2, 40)) * 5_000_000; r = rng.choice([8, 10, 12, 15, 20]); yil = rng.choice([2, 3, 4, 5]); f1 = S * r // 100
    return _o(f"Siz bankka {som(S)} so‘m omonat qo‘ydingiz. Bank har yili boshlang‘ich summadan {r}% (oddiy foiz) qo‘shadi.", [("a) Bir yilda necha so‘m foiz daromadi olasiz?", f1), (f"b) {yil} yildan keyin hisobingizda jami necha so‘m bo‘ladi?", S + f1 * yil)],
              [f"a) {som(S)} · {r}/100 = {som(f1)} so‘m.", f"b) {yil} yilda foiz: {som(f1)} · {yil} = {som(f1 * yil)} so‘m.", f"Jami: {som(S)} + {som(f1 * yil)} = {som(S + f1 * yil)} so‘m."])


@reg("pisa_foiz", "yopiq")
def foiz_taqqos(rng):
    d = rng.choice([20, 25, 30, 40]); k, ch = rng.choice([(2, "33⅓"), (3, "25"), (4, "20")])
    bd = 100 / (k + 1)
    A = f"A do‘kon ({d}% chegirma)"; B = f"B do‘kon ({k} ta olsangiz, {k + 1}-si bepul)"
    if abs(d - bd) < 1e-9:
        d = 30 if k != 3 else 40
        A = f"A do‘kon ({d}% chegirma)"
    togri = "A do‘kon foydaliroq" if d > bd else "B do‘kon foydaliroq"
    return _yopiq(rng, f"Bir xil krossovka narxi ikkala do‘konda bir xil. {A}; {B}. Ko‘p dona olmoqchi bo‘lsangiz qaysi do‘kon foydaliroq?", togri,
                   [f"A do‘konda har bir donadan {d}% tejaladi.", f"B do‘konda {k + 1} dona uchun {k} donaning puli to‘lanadi: tejam 100/{k + 1} = {bd:.1f}%".replace(".", ","), f"{d} va {bd:.1f}% ni solishtiramiz → {togri}.".replace(".", ",")],
                   noto=["A do‘kon foydaliroq" if togri.startswith("B") else "B do‘kon foydaliroq", "Ikkalasi bir xil", "Aniqlab bo‘lmaydi"], tartib=False)


@reg("pisa_foiz", "yopiq")
def foiz_qismi(rng):
    n = rng.choice([40, 50, 60, 80, 120, 150, 200, 250]); p = rng.choice([10, 20, 25, 30, 40, 60, 75]); k = n * p // 100
    return _y(rng, f"Maktabda {n} nafar o‘quvchi bor. Ularning {p}% i to‘garakka qatnaydi. To‘garakka qatnaydigan o‘quvchilar soni nechta?", k,
              [f"{n} ning {p}% i = {n} · {p}/100 = {k}."], noto=[n - k, p, n * p])


# ───────────────────────── 2) NISBAT ─────────────────────────
SHAHAR = [("Samarqand", "Buxoro"), ("Toshkent", "Samarqand"), ("Namangan", "Andijon"), ("Xiva", "Urganch"), ("Qarshi", "Shahrisabz")]


@reg("pisa_nisbat", "yopiq")
def nisbat_masshtab(rng):
    m = rng.choice([50000, 100000, 200000, 500000]); sm = rng.choice([4, 5, 6, 8, 10, 12]); real = Fraction(sm * m, 100000)
    return _y(rng, f"Xaritaning masshtabi 1 : {som(m)}. Xaritada ikki qishloq orasi {sm} sm. Haqiqatda ular orasi necha kilometr?", real,
              [f"1 sm xaritada = {som(m)} sm haqiqatda.", f"{sm} · {som(m)} = {som(sm * m)} sm = {num(Fraction(sm * m, 100))} m = {num(real)} km."], noto=[Fraction(sm * m, 100), Fraction(sm * m, 10000), real * 10])


@reg("pisa_nisbat", "yopiq")
def nisbat_retsept(rng):
    n = rng.choice([4, 5, 6]); un = rng.choice([200, 250, 300, 400, 500]) * 1; m = rng.choice([10, 12, 15, 20, 30])
    if (un * m) % n:
        un = n * 50
    ans = un * m // n
    return _y(rng, f"Oshxonada {n} kishilik palov uchun {un} g guruch kerak. {m} kishilik palov uchun necha gramm guruch kerak?", ans,
              [f"1 kishiga: {un} / {n} = {num(Fraction(un, n))} g.", f"{m} kishiga: {num(Fraction(un, n))} · {m} = {ans} g."], noto=[un + (m - n), un * m, ans + un])


@reg("pisa_nisbat", "ochiq")
def nisbat_aralash(rng):
    a, b = rng.choice([(2, 3), (3, 5), (1, 4), (2, 5), (3, 7), (4, 5)]); k = rng.choice([2, 3, 4, 5, 6]); T = (a + b) * k
    return _o(f"Devorni bo‘yash uchun oq va ko‘k bo‘yoq {a} : {b} nisbatda aralashtiriladi. Jami {T} litr aralashma tayyorlandi.", [("Oq bo‘yoq necha litr?", a * k)],
              [f"Nisbat qismlari: {a} + {b} = {a + b} ta teng qism.", f"1 qism = {T} / {a + b} = {k} litr.", f"Oq bo‘yoq: {a} · {k} = {a * k} litr."])


@reg("pisa_nisbat", "ochiq")
def nisbat_tezlik(rng):
    v = rng.choice([36, 54, 72, 90, 108, 126, 144])
    return _o(f"Velosipedchi soatiga {v} km tezlik bilan harakatlanyapti.", [("Bu tezlik necha metr/sekund?", Fraction(v * 1000, 3600))],
              [f"1 km = 1000 m, 1 soat = 3600 s.", f"{v} km/soat = {v} · 1000 / 3600 = {num(Fraction(v * 1000, 3600))} m/s."])


@reg("pisa_nisbat", "ochiq")
def nisbat_valyuta(rng):
    kurs = rng.choice([12000, 12500, 12700, 13000]); usd = rng.choice([20, 40, 50, 80, 100]); y = rng.choice([5, 8, 10, 15, 20, 25])
    return _o(f"Valyuta ayirboshlash punktida 1 AQSh dollari {som(kurs)} so‘m.", [(f"a) {usd} dollar necha so‘m?", usd * kurs), (f"b) {som(y * kurs)} so‘m necha dollar?", y)],
              [f"a) {usd} · {som(kurs)} = {som(usd * kurs)} so‘m.", f"b) {som(y * kurs)} / {som(kurs)} = {y} dollar."])


@reg("pisa_nisbat", "ochiq")
def nisbat_masshtab2(rng):
    m = rng.choice([100000, 200000, 500000]); sm = rng.choice([6, 8, 10, 12]); v = rng.choice([40, 50, 80, 100]); km = Fraction(sm * m, 100000); soat = km / v
    return _o(f"Xaritada ikki shahar orasi {sm} sm, masshtab 1 : {som(m)}. Avtobus o‘rtacha {v} km/soat tezlikda yuradi.", [("a) Shaharlar orasi necha km?", km), ("b) Avtobus yo‘lga necha soat sarflaydi?", soat)],
              [f"a) {sm} · {som(m)} = {som(sm * m)} sm = {num(km)} km.", f"b) Vaqt = masofa / tezlik = {num(km)} / {v} = {num(soat)} soat."])


@reg("pisa_nisbat", "yopiq")
def nisbat_teskari(rng):
    n = rng.choice([4, 6, 8, 10, 12]); d = rng.choice([6, 9, 12, 15]); m = rng.choice([x for x in (2, 3, 4, 6, 8, 12, 24) if x != n and (n * d) % x == 0])
    return _y(rng, f"{n} ishchi uyni {d} kunda quradi. Xuddi shu ishni {m} ishchi necha kunda bajaradi? (Hamma bir xil tezlikda ishlaydi.)", n * d // m,
              [f"Ish hajmi = {n} · {d} = {n * d} ishchi-kun.", f"{m} ishchi: {n * d} / {m} = {n * d // m} kun.", "Ishchilar ko‘p bo‘lsa, kun kam — bu TESKARI proporsionallik."], noto=[d * m // n if (d * m) % n == 0 else d + m, d + (m - n), n * d])


# ───────────────────────── 3) CHIZIQLI BOG'LANISH ─────────────────────────
@reg("pisa_chiziqli", "yopiq")
def chiz_taksi(rng):
    a = rng.choice([4000, 5000, 6000, 8000]); b = rng.choice([1500, 2000, 2500, 3000]); k = rng.choice([4, 6, 8, 10, 12, 15])
    return _y(rng, f"Taksi chaqirganda 1-km uchun alohida to‘lov yo‘q, lekin ulanish haqi {som(a)} so‘m va har bir kilometr uchun {som(b)} so‘m olinadi. {k} km yo‘l uchun necha so‘m to‘laysiz?", a + b * k,
              [f"Narx = ulanish haqi + km narxi · km soni.", f"{som(a)} + {som(b)} · {k} = {som(a)} + {som(b * k)} = {som(a + b * k)} so‘m."], noto=[b * k, (a + b) * k, a + b + k])


@reg("pisa_chiziqli", "yopiq")
def chiz_grafik(rng):
    b = rng.choice([10, 15, 20, 25]); k = rng.choice([5, 10, 15]); xm = rng.choice([4, 5, 6]); x = rng.choice([x for x in range(1, xm + 1)])
    q = _y(rng, f"Grafikda suv to‘ldirilayotgan hovuzdagi suv hajmi (y, m³) vaqtga (x, soat) bog‘liqligi ko‘rsatilgan. Grafik (0; {b}) nuqtadan boshlanadi, 1 soatda {k} m³ qo‘shiladi. {x} soatdan keyin hovuzda necha m³ suv bo‘ladi?", b + k * x,
           [f"Grafik to‘g‘ri chiziq: y = {k}·x + {b}.", f"x = {x} da: y = {k}·{x} + {b} = {b + k * x} m³.", f"Boshlang‘ich {b} m³ ni unutmang — chiziq 0 dan boshlanmaydi."], noto=[k * x, b * x, b + k + x])
    L_ = fig_chiziq(b, k, xm, "x (soat)", "y (m³)", sarlavha="Hovuzdagi suv hajmi")
    q["rasm"] = L_
    return q


@reg("pisa_chiziqli", "ochiq")
def chiz_tarif(rng):
    a = rng.choice([30000, 40000, 50000]); b = rng.choice([1000, 2000, 3000]); T = a + b * rng.choice([5, 8, 10, 12, 15]); g = (T - a) // b
    return _o(f"Mobil tarif: oylik abonent to‘lovi {som(a)} so‘m va har 1 GB internet uchun {som(b)} so‘m qo‘shimcha. Sizda oyiga {som(T)} so‘m mablag‘ bor.", [("Oyiga ko‘pi bilan necha GB internet ishlata olasiz?", g)],
              [f"Abonent to‘lovidan keyin qoladi: {som(T)} − {som(a)} = {som(T - a)} so‘m.", f"{som(T - a)} / {som(b)} = {g} GB."])


@reg("pisa_chiziqli", "ochiq")
def chiz_tank(rng):
    V = rng.choice([200, 300, 400, 500]); q_ = rng.choice([10, 15, 20, 25, 40]); t = rng.choice([3, 4, 5, 6, 8]); bosh = V - q_ * t
    if bosh <= 0:
        bosh, V = 60, 60 + q_ * t
    return _o(f"Sig‘imi {V} litr bo‘lgan bakda dastlab {bosh} litr suv bor. Unga har soatda {q_} litr suv quyiladi.", [("Bak to‘lishi uchun necha soat kerak?", Fraction(V - bosh, q_))],
              [f"To‘ldirish kerak: {V} − {bosh} = {V - bosh} litr.", f"Vaqt = {V - bosh} / {q_} = {num(Fraction(V - bosh, q_))} soat."])


@reg("pisa_chiziqli", "ochiq")
def chiz_tarif2(rng):
    d = rng.choice([500, 1000, 2000]); x0 = rng.choice([5, 10, 15, 20]); a = d * x0; b1 = rng.choice([1000, 1500, 2000]); b2 = b1 + d; x = rng.choice([6, 8, 10, 12])
    return _o(f"Internet-kafe ikki tarif taklif qiladi. A tarif: oyiga {som(a)} so‘m + har soat {som(b1)} so‘m. B tarif: abonent to‘lovisiz, har soat {som(b2)} so‘m.", [(f"a) A tarifda {x} soat qancha turadi (so‘m)?", a + b1 * x), ("b) Necha soatda ikkala tarif narxi teng bo‘ladi?", x0)],
              [f"a) {som(a)} + {som(b1)} · {x} = {som(a + b1 * x)} so‘m.", f"b) {som(a)} + {som(b1)}·x = {som(b2)}·x → {som(a)} = {som(d)}·x → x = {x0} soat."])


@reg("pisa_chiziqli", "ochiq")
def chiz_harorat(rng):
    c = rng.choice([10, 20, 25, 30, 35, 40]); f = rng.choice([50, 68, 77, 86, 95, 104])
    return _o("Amerikada harorat Farengeyt (°F) da o‘lchanadi. Formula: F = 1,8 · C + 32 (C — Selsiy gradusi).", [(f"a) {c}°C necha °F?", Fraction(18 * c, 10) + 32), (f"b) {f}°F necha °C?", Fraction((f - 32) * 10, 18))],
              [f"a) F = 1,8 · {c} + 32 = {num(Fraction(18 * c, 10))} + 32 = {num(Fraction(18 * c, 10) + 32)}.", f"b) {f} = 1,8·C + 32 → 1,8·C = {f - 32} → C = {f - 32} / 1,8 = {num(Fraction((f - 32) * 10, 18))}."])


@reg("pisa_chiziqli", "yopiq")
def chiz_qiyalik(rng):
    v = rng.choice([40, 50, 60, 80]); s0 = rng.choice([20, 30, 40]); xm = 4
    q = _yopiq(rng, f"Grafikda avtomobil yo‘lining boshlang‘ich nuqtasidan masofasi (km) vaqt (soat) bo‘yicha ko‘rsatilgan. Chiziq (0; {s0}) nuqtadan boshlanadi va har soatda {v} km ga ko‘tariladi. Chiziqning qiyaligi nimani bildiradi?",
                "Avtomobilning tezligini (km/soat)", ["Chiziqning qiyaligi = bir soatda masofa qancha o‘zgarishi = tezlik.", f"Boshlang‘ich {s0} km — chiziqning y o‘qini kesgan joyi."],
                noto=["Avtomobil bosib o‘tgan umumiy yo‘lni", "Boshlang‘ich masofani", "Sarflangan vaqtni"], tartib=False)
    q["rasm"] = fig_chiziq(s0, v, xm, "x (soat)", "y (km)", sarlavha="Avtomobil masofasi")
    return q


@reg("pisa_chiziqli", "yopiq")
def chiz_formula(rng):
    a = rng.choice([2, 3, 5, 6]); b = rng.choice([4, 7, 10, 12]); xs = rng.sample([1, 2, 3, 4, 5], 3); xs.sort()
    ys = [a * x + b for x in xs]
    q = _yopiq(rng, f"Do‘konda sotiladigan qalam qutisining narxi (ming so‘m) qalamlar soniga bog‘liq: {xs[0]} ta qalam — {ys[0]}; {xs[1]} ta — {ys[1]}; {xs[2]} ta — {ys[2]}. Qaysi formula bu bog‘liqlikni ifodalaydi?", f"$y = {a}x + {b}$",
                [f"x {xs[1] - xs[0]} ga oshganda y {ys[1] - ys[0]} ga oshadi → har bir qalam {a} ming.", f"x = 0 deb olsak: y = {ys[0]} − {a}·{xs[0]} = {b}. Demak y = {a}x + {b}."],
                noto=[f"$y = {b}x + {a}$", f"$y = {a + b}x$", f"$y = {a}x − {b}$"], tartib=False)
    return q


# ───────────────────────── 4) YUZA, PERIMETR, HAJM (FAZO) ─────────────────────────
@reg("pisa_yuza", "yopiq")
def yuza_plitka(rng):
    a = rng.choice([3, 4, 5, 6, 8]); b = rng.choice([3, 4, 5, 6, 7]); p = rng.choice([Fraction(1, 2), Fraction(1, 4) * 2]); pl = rng.choice([Fraction(1, 2), Fraction(1, 5), Fraction(1, 4)])
    soni = Fraction(a * b) / (pl * pl)
    q = _y(rng, f"Xonaning poli {a} m × {b} m. Polga tomoni {num(pl)} m bo‘lgan kvadrat plitka yotqiziladi (bo‘sh joy qoldirilmaydi, kesilmaydi). Nechta plitka kerak?", soni,
           [f"Pol yuzi: {a} · {b} = {a * b} m².", f"Bitta plitka yuzi: {num(pl)} · {num(pl)} = {num(pl * pl)} m².", f"Plitkalar soni: {a * b} / {num(pl * pl)} = {num(soni)}."], noto=[soni / 2, soni * 2, Fraction(a * b) / pl])
    q["rasm"] = fig_tortburchak(a, b)
    return q


@reg("pisa_yuza", "yopiq")
def yuza_devor(rng):
    a = rng.choice([4, 5, 6]); b = rng.choice([3, 4, 5]); h = rng.choice([2, 3]); e = rng.choice([2, 3]) * 1
    per = 2 * (a + b); S = per * h
    q = _y(rng, f"Xona uzunligi {a} m, eni {b} m, balandligi {h} m. 4 ta devorni bo‘yash kerak (shift va pol bo‘yalmaydi, eshik-derazalar hisobga olinmaydi). Bo‘yaladigan devorlar yuzi necha m²?", S,
           [f"Poydevor perimetri: 2·({a} + {b}) = {per} m.", f"Devorlar yuzi = perimetr · balandlik = {per} · {h} = {S} m²."], noto=[a * b, (a + b) * h, 2 * a * b * h // 2 + a * b])
    q["rasm"] = fig_tortburchak(a, b)
    return q


@reg("pisa_yuza", "ochiq")
def yuza_L(rng):
    a = rng.choice([8, 10, 12]); b = rng.choice([6, 8, 9]); c = rng.choice([3, 4]); d = rng.choice([2, 3, 4])
    q = _o(f"Rasmda L shaklidagi bog‘ rejasi ko‘rsatilgan (o‘lchamlar metrda).", [("Bog‘ yuzi necha m²?", a * b - c * d)],
           [f"Katta to‘rtburchak: {a} · {b} = {a * b} m².", f"Kesib olingan burchak: {c} · {d} = {c * d} m².", f"Bog‘ yuzi: {a * b} − {c * d} = {a * b - c * d} m²."])
    q["rasm"] = fig_L(a, b, c, d)
    return q


@reg("pisa_yuza", "ochiq")
def yuza_aylana(rng):
    d = rng.choice([2, 4, 6, 10, 20, 50]); 
    return _o(f"Doira shaklidagi fontan hovuzining diametri {d} m. π ≈ 3,14 deb oling.", [("a) Hovuz aylanasining uzunligi necha m?", Fraction(314, 100) * d), ("b) Hovuz yuzi necha m²?", Fraction(314, 100) * (d // 2) ** 2)],
              [f"a) C = π · d = 3,14 · {d} = {num(Fraction(314, 100) * d)} m.", f"b) Radius r = {d} / 2 = {d // 2} m. S = π · r² = 3,14 · {(d // 2) ** 2} = {num(Fraction(314, 100) * (d // 2) ** 2)} m²."])


@reg("pisa_yuza", "ochiq")
def yuza_bog(rng):
    a = rng.choice([12, 15, 18, 20, 25]); b = rng.choice([8, 10, 12, 14]); p = rng.choice([20, 25, 30, 40]) * 1000; per = 2 * (a + b)
    q = _o(f"To‘rtburchak shaklidagi bog‘ atrofiga to‘siq qurilmoqda (o‘lchamlar metrda). 1 m to‘siq {som(p)} so‘m turadi.", [("a) To‘siq uzunligi necha metr bo‘lishi kerak?", per), ("b) To‘siq jami necha so‘m turadi?", per * p)],
           [f"a) Perimetr = 2·({a} + {b}) = {per} m.", f"b) {per} · {som(p)} = {som(per * p)} so‘m."])
    q["rasm"] = fig_tortburchak(a, b)
    return q


@reg("pisa_yuza", "ochiq")
def yuza_hajm(rng):
    a = rng.choice([4, 5, 6, 8, 10]); b = rng.choice([3, 4, 5, 6]); c = rng.choice([2, 3, 4, 5]); V = a * b * c; q_ = rng.choice([x for x in (10, 20, 30, 40, 50, 60, 100) if V % x == 0] or [10])
    return _o(f"To‘g‘ri to‘rtburchak shaklidagi akvarium: uzunligi {a} dm, eni {b} dm, balandligi {c} dm. (1 dm³ = 1 litr.)", [("a) Akvarium sig‘imi necha litr?", V), (f"b) Nasos soatiga {q_} litr suv quysa, akvarium necha soatda to‘ladi?", Fraction(V, q_))],
              [f"a) V = {a} · {b} · {c} = {V} dm³ = {V} litr.", f"b) {V} / {q_} = {num(Fraction(V, q_))} soat."])


@reg("pisa_yuza", "yopiq")
def yuza_pifagor(rng):
    a, b, c = rng.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (9, 12, 15), (8, 15, 17), (12, 16, 20)])
    q = _y(rng, f"Narvon devorga tiralgan: uning pastki uchi devordan {a} m uzoqlikda, yuqori uchi yerdan {b} m balandlikda. Narvon necha metr?", c,
           [f"Devor, yer va narvon to‘g‘ri burchakli uchburchak hosil qiladi.", f"Pifagor teoremasi: c² = {a}² + {b}² = {a * a} + {b * b} = {c * c}.", f"c = √{c * c} = {c} m."], noto=[a + b, c + 1, b - a if b > a else a + 1])
    q["rasm"] = fig_narvon(a, b)
    return q


# ───────────────────────── 5) MA'LUMOT VA EHTIMOL ─────────────────────────
KUN = ["Du", "Se", "Chor", "Pay", "Ju"]


@reg("pisa_malumot", "yopiq")
def mal_ortacha(rng):
    n = rng.choice([4, 5, 6]); m = rng.choice([15, 20, 24, 30, 36, 50]); xs = [m + rng.randint(-8, 8) for _ in range(n - 1)]; xs.append(m * n - sum(xs)); rng.shuffle(xs)
    return _y(rng, f"Aziz {n} kun davomida har kuni yugurdi (daqiqalarda): {', '.join(map(str, xs))}. U kuniga o‘rtacha necha daqiqa yugurgan?", m,
              [f"Yig‘indi: {' + '.join(map(str, xs))} = {sum(xs)}.", f"O‘rtacha = yig‘indi / kunlar soni = {sum(xs)} / {n} = {m}."], noto=[max(xs), sorted(xs)[len(xs) // 2], sum(xs) // (n + 1) if sum(xs) % (n + 1) == 0 else m + 3])


@reg("pisa_malumot", "yopiq")
def mal_median(rng):
    xs = rng.sample(range(10, 60), 7); med = sorted(xs)[3]
    return _y(rng, f"Yetti ta do‘kondagi bir xil mahsulot narxi (ming so‘m): {', '.join(map(str, xs))}. Narxlarning medianasi nimaga teng?", med,
              [f"Avval tartiblaymiz: {', '.join(map(str, sorted(xs)))}.", f"7 ta son — o‘rtadagi (4-chi) son mediana: {med}."], noto=[xs[3] if xs[3] != med else xs[0], sum(xs) // 7, max(xs)])


@reg("pisa_malumot", "yopiq")
def mal_yangi(rng):
    n = rng.choice([4, 5, 6]); m = rng.choice([70, 75, 80, 85]); k = rng.choice([1, 2, 3, 4, 5]); m2 = m + k; yangi = m2 * (n + 1) - m * n
    return _y(rng, f"{n} ta imtihon bahosining o‘rtachasi {m} ball edi. Yana bitta imtihon topshirilgach o‘rtacha {m2} ball bo‘ldi. Oxirgi imtihondan necha ball olingan?", yangi,
              [f"Oldingi yig‘indi: {m} · {n} = {m * n}.", f"Yangi yig‘indi: {m2} · {n + 1} = {m2 * (n + 1)}.", f"Oxirgi ball: {m2 * (n + 1)} − {m * n} = {yangi}."], noto=[m2, m + k * 2, yangi - 10])


@reg("pisa_malumot", "ochiq")
def mal_ehtimol(rng):
    q_, k, y = rng.sample(range(2, 9), 3); n = q_ + k + y
    return _o(f"Qopda {q_} ta qizil, {k} ta ko‘k va {y} ta yashil shar bor. Ko‘rmasdan bitta shar olinadi.", [("Qizil shar chiqish ehtimoli qancha? (oddiy kasr yoki o‘nli kasr, masalan 1/4)", Fraction(q_, n))],
              [f"Barcha sharlar: {q_} + {k} + {y} = {n}.", f"Ehtimol = qulay hollar / barcha hollar = {q_}/{n}."])


@reg("pisa_malumot", "ochiq")
def mal_diagramma(rng):
    v = [rng.randint(8, 30) * 5 for _ in range(5)]
    i, j = rng.sample(range(5), 2)
    q = _o("Diagrammada kafedagi 5 kunlik sotilgan choy (stakan) soni ko‘rsatilgan.", [(f"a) {['Dushanba','Seshanba','Chorshanba','Payshanba','Juma'][i]} va {['Dushanba','Seshanba','Chorshanba','Payshanba','Juma'][j]} kunlari jami necha stakan sotilgan?", v[i] + v[j]), ("b) Eng ko‘p va eng kam sotilgan kunlar orasidagi farq nechta?", max(v) - min(v))],
           [f"a) {v[i]} + {v[j]} = {v[i] + v[j]}.", f"b) Eng ko‘p: {max(v)}, eng kam: {min(v)} → farq: {max(v) - min(v)}."])
    q["rasm"] = fig_stolbik(KUN, v, "Sotilgan choy (stakan)")
    return q


@reg("pisa_malumot", "ochiq")
def mal_harorat(rng):
    n = 5; m = rng.choice([18, 20, 22, 25, 28]); xs = [m + rng.randint(-6, 6) for _ in range(n - 1)]; xs.append(m * n - sum(xs))
    q = _o("Diagrammada Samarqandda 5 kun davomida tushlikdagi harorat (°C) ko‘rsatilgan.", [("a) 5 kunlik o‘rtacha harorat necha °C?", m), ("b) Eng issiq va eng sovuq kun orasidagi farq necha °C?", max(xs) - min(xs))],
           [f"a) ({' + '.join(map(str, xs))}) / 5 = {sum(xs)} / 5 = {m}.", f"b) {max(xs)} − {min(xs)} = {max(xs) - min(xs)}."])
    q["rasm"] = fig_stolbik(KUN, xs, "Harorat, °C")
    return q


@reg("pisa_malumot", "ochiq")
def mal_zar(rng):
    s = rng.choice([5, 6, 7, 8, 9]); t = rng.choice([10, 11, 12]); n_s = 6 - abs(s - 7); n_t = sum(1 for x in range(1, 7) for y in range(1, 7) if x + y >= t)
    return _o("Ikkita oddiy o‘yin kubigi (zar) bir vaqtda tashlanadi. Jami 36 ta teng imkoniyatli natija bor.", [(f"a) Tushgan ochkolar yig‘indisi {s} bo‘lish ehtimoli qancha? (kasr ko‘rinishida)", Fraction(n_s, 36)), (f"b) Yig‘indi kamida {t} bo‘lish ehtimoli qancha? (kasr ko‘rinishida)", Fraction(n_t, 36))],
              [f"a) Yig‘indi {s} bo‘ladigan juftliklar: {n_s} ta → {n_s}/36 = {num(Fraction(n_s, 36))}.", f"b) Yig‘indi ≥ {t} bo‘ladigan juftliklar: {n_t} ta → {n_t}/36 = {num(Fraction(n_t, 36))}."])


# ───────────────────────── chizmalar (2-bosqich) ─────────────────────────
def fig_pie(nomlar, qiymatlar, sarlavha=""):
    cx, cy, r = 110, 105, 70; jami = sum(qiymatlar); a0 = -math.pi / 2; body = _t(150, 16, sarlavha, it=False, size=13); ranglar = ["#5b8def", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"]
    for i, (n, v) in enumerate(zip(nomlar, qiymatlar)):
        a1 = a0 + 2 * math.pi * v / jami; x0, y0, x1, y1 = cx + r * math.cos(a0), cy + r * math.sin(a0), cx + r * math.cos(a1), cy + r * math.sin(a1)
        body += f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 {1 if a1 - a0 > math.pi else 0} 1 {x1:.1f},{y1:.1f} Z" fill="{ranglar[i % 5]}" stroke="#fff" stroke-width="1.5"/>'
        body += f'<rect x="205" y="{45 + i * 22}" width="12" height="12" fill="{ranglar[i % 5]}"/>' + _t(223, 56 + i * 22, f"{n}: {v}%", it=False, anchor="start", size=12)
        a0 = a1
    return _svg(body, 300, 200)


def fig_poliliniya(nomlar, qiymatlar, sarlavha="", birlik=""):
    W, x0, y0 = 320, 44, 175; top = math.ceil(max(qiymatlar) / 10) * 10 or 10; sx = (W - x0 - 20) / (len(qiymatlar) - 1); sy = 140 / top
    body = _t(W / 2, 14, sarlavha, it=False, size=13) + _l((x0, y0), (W - 10, y0)) + _l((x0, y0), (x0, 30))
    for k in range(5):
        v = top * k / 4; body += _l((x0 - 3, y0 - v * sy), (W - 10, y0 - v * sy), w=.4, col="#ccc") + _t(x0 - 6, y0 - v * sy + 3, f"{v:g}", it=False, anchor="end", size=10)
    pts = [(x0 + i * sx, y0 - v * sy) for i, v in enumerate(qiymatlar)]
    body += _poly(pts, w=2) .replace('#111', '#2563eb')
    for (px, py), n, v in zip(pts, nomlar, qiymatlar):
        body += f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="#2563eb"/>' + _t(px, y0 + 14, n, it=False, size=10) + _t(px, py - 7, f"{v:g}", it=False, size=10)
    return _svg(body, W, 205)


def fig_soya(h, s, H):
    """Tayoq (h) soyasi s; daraxt soyasi S, balandligi ? """
    body = _l((20, 170), (290, 170)) + _l((60, 170), (60, 170 - h * 8), w=3, col="#8a5a2b") + _l((60, 170 - h * 8), (60 + s * 8, 170), w=1, dash=True)
    body += _t(40, 170 - h * 4, f"{num(h)} m", it=False, anchor="end", size=12) + _t(60 + s * 4, 186, f"{num(s)} m", it=False, size=12)
    return _svg(body + _t(200, 40, "soyaning uchi", it=False, size=0), 300, 195)


# ───────────────────────── 6) TEZLIK, MASOFA, VAQT ─────────────────────────
@reg("pisa_tezlik", "yopiq")
def tez_oddiy(rng):
    v = rng.choice([40, 60, 75, 80, 90, 100]); t = rng.choice([2, 3, 4, 5]); return _y(rng, f"Avtobus o‘rtacha {v} km/soat tezlik bilan {t} soat yurdi. U necha km yo‘l bosdi?", v * t, [f"Masofa = tezlik · vaqt = {v} · {t} = {v * t} km."], noto=[v + t, Fraction(v, t), v * t + v])


@reg("pisa_tezlik", "yopiq")
def tez_vaqt(rng):
    v = rng.choice([40, 50, 60, 80, 100]); t = rng.choice([2, 3, 4, 5, 6]); s = v * t; m = t * 60
    return _y(rng, f"Samarqanddan shaharga {s} km. Siz soatiga {v} km tezlikda yursangiz, yo‘lga necha daqiqa ketadi?", m, [f"Vaqt = masofa / tezlik = {s} / {v} = {t} soat.", f"{t} soat = {t} · 60 = {m} daqiqa."], noto=[t, s // 60 if s % 60 == 0 else t * 100, m + 60])


@reg("pisa_tezlik", "ochiq")
def tez_uchrash(rng):
    v1 = rng.choice([50, 60, 70]); v2 = rng.choice([40, 50, 80]); t = rng.choice([2, 3, 4]); S = (v1 + v2) * t
    return _o(f"Ikki shahar orasi {S} km. Ularning birinchisidan {v1} km/soat, ikkinchisidan {v2} km/soat tezlik bilan bir vaqtda bir-biriga qarab ikkita mashina yo‘lga chiqdi.", [("Ular necha soatdan keyin uchrashadi?", t)],
              [f"Yaqinlashish tezligi: {v1} + {v2} = {v1 + v2} km/soat.", f"Vaqt = {S} / {v1 + v2} = {t} soat."])


@reg("pisa_tezlik", "ochiq")
def tez_ortacha(rng):
    a = rng.choice([60, 80, 90]); b = rng.choice([30, 40, 60]); ta = rng.choice([2, 3]); tb = rng.choice([1, 2]); S = a * ta + b * tb; T = ta + tb
    return _o(f"Haydovchi {ta} soat davomida {a} km/soat, keyin {tb} soat davomida {b} km/soat tezlikda yurdi.", [("a) Jami necha km yurdi?", S), ("b) O‘rtacha tezligi necha km/soat? (jami yo‘l / jami vaqt)", Fraction(S, T))],
              [f"a) {a}·{ta} + {b}·{tb} = {a * ta} + {b * tb} = {S} km.", f"b) Jami vaqt: {T} soat. O‘rtacha tezlik = {S} / {T} = {num(Fraction(S, T))} km/soat.", "Diqqat: o‘rtacha tezlik = tezliklar o‘rtachasi EMAS."])


@reg("pisa_tezlik", "ochiq")
def tez_yoqilgi(rng):
    n = rng.choice([5, 6, 7, 8]); S = rng.choice([200, 300, 400, 500]); l = Fraction(S * n, 100); p = rng.choice([9000, 10000, 12000, 14000])
    return _o(f"Avtomobil 100 km yo‘lga {n} litr benzin sarflaydi. Benzinning 1 litri {som(p)} so‘m.", [(f"a) {S} km uchun necha litr benzin kerak?", l), (f"b) {S} km yo‘lga benzin necha so‘m turadi?", l * p)],
              [f"a) {S} / 100 = {num(Fraction(S, 100))} marta 100 km. {num(Fraction(S, 100))} · {n} = {num(l)} litr.", f"b) {num(l)} · {som(p)} = {som(l * p)} so‘m."])


@reg("pisa_tezlik", "ochiq")
def tez_grafik(rng):
    v = rng.choice([20, 30, 40, 50]); t0 = rng.choice([1, 2]); s0 = rng.choice([10, 20]); xm = 5
    q = _o(f"Grafikda velosipedchining yo‘lboshidan masofasi (km) vaqtga (soat) bog‘liq ko‘rsatilgan. U {s0} km masofadan boshlab, soatiga {v} km tezlikda yuradi.", [(f"a) 3 soatdan keyin yo‘lboshidan necha km uzoqlikda bo‘ladi?", s0 + 3 * v), ("b) Qaysi soatda u 3-soatdagidan 2 baravar uzoq bo‘ladi? (soat)", Fraction(2 * (s0 + 3 * v) - s0, v))],
           [f"a) y = {v}·x + {s0}; x = 3: {v * 3} + {s0} = {s0 + 3 * v} km.", f"b) Masofa 2·{s0 + 3 * v} = {2 * (s0 + 3 * v)}: {v}·x + {s0} = {2 * (s0 + 3 * v)} → x = {num(Fraction(2 * (s0 + 3 * v) - s0, v))} soat."])
    q["rasm"] = fig_chiziq(s0, v, xm, "x (soat)", "y (km)", sarlavha="Velosipedchi masofasi")
    return q


# ───────────────────────── 7) GEOMETRIK QONUNIYATLAR ─────────────────────────
@reg("pisa_geometriya", "yopiq")
def geo_soya(rng):
    h = rng.choice([1, 2, Fraction(3, 2)]); s = rng.choice([2, 3, 4]); S = s * rng.choice([5, 6, 8, 10]); H = Fraction(h) * S / s
    q = _y(rng, f"Bir vaqtda {num(h)} m uzunlikdagi tayoqning soyasi {s} m, daraxtning soyasi {S} m. Daraxt necha metr balandlikda?", H, [f"O‘xshash uchburchaklar: balandlik / soya bir xil.", f"{num(h)} / {s} = H / {S} → H = {num(h)} · {S} / {s} = {num(H)} m."], noto=[Fraction(S) - s + h, Fraction(S, s), H * 2])
    return q


@reg("pisa_geometriya", "yopiq")
def geo_burchak(rng):
    a = rng.choice([40, 50, 55, 60, 70]); b = rng.choice([30, 45, 50, 65]); c = 180 - a - b
    return _y(rng, f"Uchburchak shaklidagi bog‘ning ikkita burchagi {a}° va {b}°. Uchinchi burchagi necha gradus?", c, [f"Uchburchak burchaklari yig‘indisi 180°.", f"180 − {a} − {b} = {c}°."], noto=[a + b, 360 - a - b, 90 - a])


@reg("pisa_geometriya", "yopiq")
def geo_kopburchak(rng):
    n = rng.choice([5, 6, 8, 10]); S = (n - 2) * 180
    return _y(rng, f"Xiva darvozasi yonidagi maydon {n} burchakli qavariq ko‘pburchak shaklida. Uning ichki burchaklari yig‘indisi necha gradus?", S, [f"Formula: (n − 2) · 180°.", f"({n} − 2) · 180 = {S}°."], noto=[n * 180, (n - 1) * 180, 360])


@reg("pisa_geometriya", "ochiq")
def geo_masshtab_shakl(rng):
    k = rng.choice([2, 3, 4, 5]); a = rng.choice([4, 5, 6, 8]); b = rng.choice([3, 5, 7]); 
    return _o(f"Reklama banneri tomonlari {a} dm va {b} dm bo‘lgan to‘rtburchak. Xuddi shu shaklning {k} marta kattalashtirilgan varianti chop etiladi.", [("a) Kattalashtirilgan tomonlardan kattasi necha dm?", max(a, b) * k), ("b) Yuzi necha marta ortadi?", k * k)],
              [f"a) {max(a, b)} · {k} = {max(a, b) * k} dm.", f"b) Chiziqli o‘lchamlar {k} marta ortsa, yuz {k}² = {k * k} marta ortadi."])


@reg("pisa_geometriya", "ochiq")
def geo_tomonlar(rng):
    a = rng.choice([6, 8, 10, 12]); h = rng.choice([4, 5, 6, 8]); b = rng.choice([7, 9, 10]); 
    return _o(f"Uchburchak shaklidagi yer uchastkasi: asosi {a} m, shu asosga tushirilgan balandligi {h} m.", [("a) Uchastka yuzi necha m²?", Fraction(a * h, 2)), ("b) 1 m² yerga 2 kg urug‘ sarflansa, jami necha kg urug‘ kerak?", a * h)],
              [f"a) S = asos · balandlik / 2 = {a} · {h} / 2 = {num(Fraction(a * h, 2))} m².", f"b) {num(Fraction(a * h, 2))} · 2 = {a * h} kg."])


@reg("pisa_geometriya", "ochiq")
def geo_trapetsiya(rng):
    a = rng.choice([6, 8, 10]); b = rng.choice([12, 14, 16]); h = rng.choice([4, 6, 8, 10]); p = rng.choice([10, 12, 15]) * 1000
    q = _o(f"Hovli trapetsiya shaklida: parallel tomonlari {a} m va {b} m, ular orasidagi masofa {h} m. 1 m² asfalt {som(p)} so‘m.", [("a) Hovli yuzi necha m²?", Fraction((a + b) * h, 2)), ("b) Asfaltlash necha so‘m turadi?", Fraction((a + b) * h, 2) * p)],
           [f"a) S = (a + b) · h / 2 = ({a} + {b}) · {h} / 2 = {(a + b) * h // 2} m².", f"b) {(a + b) * h // 2} · {som(p)} = {som((a + b) * h // 2 * p)} so‘m."])
    return q


@reg("pisa_geometriya", "yopiq")
def geo_aylana_pizza(rng):
    d = rng.choice([20, 30, 40]); n = rng.choice([4, 6, 8, 10]); 
    return _y(rng, f"Diametri {d} sm bo‘lgan doira shaklidagi pitsa {n} ta teng bo‘lakka kesildi. Bitta bo‘lakning markaziy burchagi necha gradus?", Fraction(360, n), [f"To‘liq aylana 360°.", f"360 / {n} = {num(Fraction(360, n))}°."], noto=[Fraction(180, n), Fraction(360, n) * 2, n * 10])


# ───────────────────────── 8) QONUNIYAT VA KETMA-KETLIK ─────────────────────────
@reg("pisa_ketma", "yopiq")
def ket_arifm(rng):
    a = rng.choice([3, 5, 7, 10]); d = rng.choice([2, 3, 4, 5]); n = rng.choice([8, 10, 12, 15]); x = a + (n - 1) * d
    return _y(rng, f"Zina pog‘onalari soni qonuniyat bo‘yicha o‘sadi: {a}, {a + d}, {a + 2 * d}, {a + 3 * d}, … Shu qonuniyat bo‘yicha {n}-qadamda necha pog‘ona bo‘ladi?", x, [f"Har qadamda {d} taga oshadi.", f"{n}-had: {a} + ({n} − 1) · {d} = {a} + {(n - 1) * d} = {x}."], noto=[a + n * d, a * n, x - d])


@reg("pisa_ketma", "yopiq")
def ket_gugurt(rng):
    k = rng.choice([3, 4, 5]); n = rng.choice([5, 6, 8, 10]); x = k * n + 1
    return _y(rng, f"Gugurt cho‘plaridan zanjir yasaladi: 1 ta kvadrat uchun {k + 1} ta, har keyingisi uchun {k} tadan qo‘shimcha cho‘p kerak ({k + 1}, {2 * k + 1}, {3 * k + 1}, …). {n} ta shakl uchun nechta cho‘p kerak?", x, [f"Formula: {k}·n + 1.", f"n = {n}: {k} · {n} + 1 = {x}."], noto=[(k + 1) * n, k * n, x + k])


@reg("pisa_ketma", "ochiq")
def ket_jamgarma(rng):
    a = rng.choice([20, 30, 50]); d = rng.choice([5, 10]); n = rng.choice([6, 8, 10]); x = a + (n - 1) * d; S = n * (a + x) // 2
    return _o(f"Dilnoza birinchi haftada {a} ming so‘m yig‘di, har keyingi haftada oldingi haftadan {d} ming so‘m ortiq yig‘adi.", [(f"a) {n}-haftada necha ming so‘m yig‘adi?", x), (f"b) {n} hafta ichida jami necha ming so‘m yig‘adi?", S)],
              [f"a) {a} + ({n} − 1) · {d} = {x}.", f"b) Yig‘indi = n · (birinchi + oxirgi) / 2 = {n} · ({a} + {x}) / 2 = {S}."])


@reg("pisa_ketma", "ochiq")
def ket_o_sish(rng):
    a = rng.choice([100, 200, 500]); k = rng.choice([2, 3]); n = rng.choice([3, 4, 5]); x = a * k ** n
    return _o(f"Hovuzdagi suv o‘tlari har kuni oldingi kundagidan {k} marta ko‘payadi. Birinchi kuni {a} dona bor edi.", [(f"{n} kun o‘tgach nechta bo‘ladi?", x)],
              [f"Har kuni {k} ga ko‘paytiriladi: {a} · {k}^{n}.", f"{k}^{n} = {k ** n}, {a} · {k ** n} = {x}."])


@reg("pisa_ketma", "ochiq")
def ket_taqsimlash(rng):
    n = rng.choice([4, 5, 6]); d = rng.choice([2, 3]); a = rng.choice([10, 15, 20]); S = n * (2 * a + (n - 1) * d) // 2
    return _o(f"Stadionda 1-qatorda {a} ta o‘rindiq, har keyingi qatorda oldingisidan {d} tadan ko‘p. Jami {n} qator.", [("a) Oxirgi qatorda nechta o‘rindiq bor?", a + (n - 1) * d), ("b) Hammasi bo‘lib nechta o‘rindiq bor?", S)],
              [f"a) {a} + ({n} − 1) · {d} = {a + (n - 1) * d}.", f"b) {n} · ({a} + {a + (n - 1) * d}) / 2 = {S}."])


@reg("pisa_ketma", "yopiq")
def ket_juft(rng):
    a = rng.choice([2, 3, 4]); r = rng.choice([2, 3]); seq = [a * r ** i for i in range(5)]
    return _y(rng, f"Qonuniyatni toping va keyingi sonni yozing: {', '.join(map(str, seq[:4]))}, ?", seq[4], [f"Har son oldingisidan {r} marta katta.", f"{seq[3]} · {r} = {seq[4]}."], noto=[seq[3] + seq[1], seq[3] + a, seq[3] * seq[1]])


# ───────────────────────── 9) PUL VA BYUDJET ─────────────────────────
@reg("pisa_pul", "yopiq")
def pul_qaytim(rng):
    n = rng.choice([3, 4, 5, 6]); p = rng.choice([4500, 6500, 7800, 12500, 3200]); pul = 100000 if n * p < 100000 else 200000
    return _y(rng, f"Do‘konda {n} ta bir xil daftar sotib olindi, har biri {som(p)} so‘m. Kassirga {som(pul)} so‘m berildi. Qaytim necha so‘m?", pul - n * p, [f"Narx: {n} · {som(p)} = {som(n * p)} so‘m.", f"Qaytim: {som(pul)} − {som(n * p)} = {som(pul - n * p)} so‘m."], noto=[n * p, pul - p, pul + n * p])


@reg("pisa_pul", "yopiq")
def pul_arzon(rng):
    k = rng.choice([4, 5, 6]); a = rng.choice([3000, 3500, 4000])
    sm = rng.choice([500, 800, 1000]); big = rng.choice([6, 8, 10]); pk = a * k
    pb = (a - sm) * big
    t = "Katta qadoq" if pb / big < pk / k else "Kichik qadoq"
    return _yopiq(rng, f"Suv: kichik qadoqda {k} ta shisha — {som(pk)} so‘m; katta qadoqda {big} ta shisha — {som(pb)} so‘m. Qaysi biri bitta shisha uchun arzonroq?", t,
                  [f"Kichik qadoq: {som(pk)} / {k} = {num(Fraction(pk, k))} so‘m.", f"Katta qadoq: {som(pb)} / {big} = {num(Fraction(pb, big))} so‘m.", f"Arzonrog‘i: {t.lower()}."], noto=["Kichik qadoq" if t == "Katta qadoq" else "Katta qadoq", "Narxi bir xil", "Aniqlab bo‘lmaydi"], tartib=False)


@reg("pisa_pul", "ochiq")
def pul_byudjet(rng):
    maosh = rng.choice([4, 5, 6, 8]) * 1000000; a, b, c = rng.choice([30, 25, 20]), rng.choice([20, 15, 25]), rng.choice([10, 15, 5])
    return _o(f"Oilaning oylik daromadi {som(maosh)} so‘m. U shunday taqsimlanadi: oziq-ovqat {a}%, kommunal va transport {b}%, ta’lim {c}%.", [("a) Oziq-ovqatga necha so‘m ketadi?", maosh * a // 100), ("b) Qolgan qismi necha so‘m?", maosh * (100 - a - b - c) // 100)],
              [f"a) {som(maosh)} · {a}/100 = {som(maosh * a // 100)} so‘m.", f"b) Qolgan foiz: 100 − {a} − {b} − {c} = {100 - a - b - c}%.", f"{som(maosh)} · {100 - a - b - c}/100 = {som(maosh * (100 - a - b - c) // 100)} so‘m."])


@reg("pisa_pul", "ochiq")
def pul_kredit(rng):
    P = rng.choice([6, 8, 12, 18, 24]) * 1000000; oy = rng.choice([6, 12]); f = rng.choice([10, 20, 25]) if False else rng.choice([10, 20]); jami = P + P * f // 100; oylik = Fraction(jami, oy)
    return _o(f"Muzlatgich muddatli to‘lovga sotilmoqda: narxi {som(P)} so‘m, ustama {f}%. To‘lov {oy} oyga teng bo‘lib to‘lanadi.", [("a) Jami necha so‘m to‘lanadi?", jami), ("b) Oylik to‘lov necha so‘m?", oylik)],
              [f"a) Ustama: {som(P)} · {f}/100 = {som(P * f // 100)}. Jami: {som(jami)} so‘m.", f"b) {som(jami)} / {oy} = {num(oylik)} so‘m."])


@reg("pisa_pul", "ochiq")
def pul_valyuta2(rng):
    kurs = rng.choice([2500, 2800, 3000, 3200]); a = rng.choice([80, 120, 150, 200]); b = rng.choice([30, 50, 60])
    return _o(f"Turist Istanbuldagi bozorda {a} lirali sovg‘a oldi. 1 lira = {som(kurs)} so‘m.", [("a) Sovg‘a necha so‘m?", a * kurs), (f"b) {b} lira necha so‘m?", b * kurs)],
              [f"a) {a} · {som(kurs)} = {som(a * kurs)} so‘m.", f"b) {b} · {som(kurs)} = {som(b * kurs)} so‘m."])


@reg("pisa_pul", "yopiq")
def pul_ulgurji(rng):
    n = rng.choice([20, 25, 40, 50]); a = rng.choice([800, 1200, 1500]); sot = a * rng.choice([13, 14, 15]) // 10; f = (sot - a) * n
    return _y(rng, f"Do‘konchi {n} ta qalamni dona narxi {som(a)} so‘mdan olib, donasini {som(sot)} so‘mdan sotdi. Hammasi sotilsa, foydasi necha so‘m?", f, [f"1 dona foyda: {som(sot)} − {som(a)} = {som(sot - a)}.", f"{n} dona: {som(sot - a)} · {n} = {som(f)} so‘m."], noto=[sot * n, a * n, (sot - a)])


# ───────────────────────── 10) JADVAL VA DIAGRAMMA TAHLILI ─────────────────────────
@reg("pisa_diagramma", "yopiq")
def dia_pie(rng):
    n = ["Matematika", "Fizika", "Tarix", "Til"]; v = rng.choice([[40, 25, 20, 15], [30, 30, 25, 15], [50, 20, 20, 10], [35, 25, 25, 15]]); T = rng.choice([200, 300, 400, 500]); i = rng.randrange(4)
    q = _y(rng, f"Doira diagrammada {T} nafar o‘quvchining sevimli fani ko‘rsatilgan. «{n[i]}»ni sevimli deb tanlaganlar necha nafar?", T * v[i] // 100, [f"Diagrammada {n[i]} — {v[i]}%.", f"{T} · {v[i]}/100 = {T * v[i] // 100} nafar."], noto=[v[i], T - T * v[i] // 100, T * v[i] // 10])
    q["rasm"] = fig_pie(n, v, "Sevimli fan"); return q


@reg("pisa_diagramma", "yopiq")
def dia_o_sish(rng):
    n = ["2019", "2020", "2021", "2022", "2023"]; a = rng.choice([100, 120, 150]); d = rng.choice([20, 30, 40]); v = [a + d * i + rng.choice([0, 0, -10]) for i in range(5)]
    i = max(range(1, 5), key=lambda k: v[k] - v[k - 1]); yil = n[i]
    q = _yopiq(rng, f"Chiziqli diagrammada korxonaning yillik sotuvi (ming dona) ko‘rsatilgan. Qaysi yilda sotuv oldingi yilga nisbatan eng ko‘p oshgan?", yil, [f"Har yil oshishini hisoblaymiz: " + "; ".join(f"{n[k]}: {v[k] - v[k - 1]}" for k in range(1, 5)) + ".", f"Eng katta oshish — {yil}."], noto=[x for x in n if x != yil][:3], tartib=False)
    q["rasm"] = fig_poliliniya(n, v, "Yillik sotuv, ming dona"); return q


@reg("pisa_diagramma", "ochiq")
def dia_pie2(rng):
    n = ["Avtobus", "Piyoda", "Velosiped", "Mashina"]; v = rng.choice([[40, 30, 20, 10], [35, 25, 25, 15], [50, 20, 20, 10], [30, 40, 20, 10]]); T = rng.choice([200, 400, 600, 800])
    q = _o(f"Doira diagrammada {T} nafar o‘quvchining maktabga qatnash usuli berilgan.", [("a) Avtobusda kelganlar necha nafar?", T * v[0] // 100), ("b) Piyoda va velosipedda kelganlar jami necha nafar?", T * (v[1] + v[2]) // 100)],
           [f"a) {T} · {v[0]}/100 = {T * v[0] // 100}.", f"b) {v[1]}% + {v[2]}% = {v[1] + v[2]}%; {T} · {v[1] + v[2]}/100 = {T * (v[1] + v[2]) // 100}."])
    q["rasm"] = fig_pie(n, v, "Maktabga qatnash"); return q


@reg("pisa_diagramma", "ochiq")
def dia_stolbik_farq(rng):
    n = ["Yan", "Fev", "Mar", "Apr", "May"]; v = [rng.randint(8, 30) * 5 for _ in range(5)]
    q = _o("Diagrammada do‘kon 5 oy davomida sotgan kitoblari soni ko‘rsatilgan.", [("a) 5 oyda jami nechta kitob sotilgan?", sum(v)), ("b) Oyiga o‘rtacha nechta kitob sotilgan?", Fraction(sum(v), 5))],
           [f"a) {' + '.join(map(str, v))} = {sum(v)}.", f"b) {sum(v)} / 5 = {num(Fraction(sum(v), 5))}."])
    q["rasm"] = fig_stolbik(n, v, "Sotilgan kitoblar"); return q


@reg("pisa_diagramma", "yopiq")
def dia_mediana(rng):
    xs = [rng.randint(3, 9) for _ in range(9)]; xs.sort(); m = xs[4]; rng.shuffle(xs)
    return _y(rng, f"9 ta o‘quvchining test balli: {', '.join(map(str, xs))}. Medianani toping.", m, [f"Tartiblaymiz: {', '.join(map(str, sorted(xs)))}.", f"9 ta son — 5-chi son mediana: {m}."], noto=[max(xs), min(xs), sum(xs) // 9 if sum(xs) // 9 != m else m + 1])


@reg("pisa_diagramma", "ochiq")
def dia_ehtimol2(rng):
    q_, k = rng.choice([(3, 5), (4, 6), (2, 7), (5, 5)]); n = q_ + k; m = rng.choice([1, 2])
    return _o(f"Qutida {q_} ta qizil va {k} ta ko‘k qalam bor. Ko‘rmasdan bitta qalam olinadi.", [("a) Ko‘k qalam olinish ehtimoli qancha? (kasr)", Fraction(k, n)), ("b) Qizil qalam olinish ehtimoli qancha? (kasr)", Fraction(q_, n))],
              [f"a) {k}/{n}.", f"b) {q_}/{n}. Tekshirish: {q_}/{n} + {k}/{n} = 1."])
