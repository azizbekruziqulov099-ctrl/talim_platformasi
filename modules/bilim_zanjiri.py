"""REV512: bilim zanjiri — har matematika mavzusiga «oldin bilish kerak» bo'lgan mavzular.
Dars boshida 3 savollik kirish tekshiruvi: har oldingi mavzudan bittadan savol. Xato bo'lsa — «Avval buni eslab olaylik»:
qisqa nazariya (namunaviy yechim bilan) va 6 ta amaliy mashq, keyin darsga qaytiladi.
Savollar xilma generatorlaridan (tools/maktab_mat) — 3–11-sinf mavzu oilalari."""
import os, random, re, sys, time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException

_YOL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "maktab_mat")
if _YOL not in sys.path:
    sys.path.insert(0, _YOL)

# oila → oldingi (zarur) oilalar. «modul:funksiya»
ZANJIR = {
    # 1–2-sinf (REV513)
    "xilma12:o_qosh20": ["xilma12:o_son10"], "xilma12:o_son100": ["xilma12:o_qosh20"], "xilma12:o_masala12": ["xilma12:o_qosh20"],
    "xilma12:o_ifoda12": ["xilma12:o_qosh20"], "xilma12:o_kopjadval": ["xilma12:o_qosh20", "xilma12:o_son100"], "xilma12:o_uchxonali": ["xilma12:o_son100"],
    "xilma12:o_yuz12": ["xilma12:o_kopjadval"], "xilma12:o_olchov12": ["xilma12:o_son100"], "xilma12:o_shakl12": ["xilma12:o_qosh20"],
    "xilma34:o_qoshayir": ["xilma12:o_uchxonali"], "xilma34:o_sonlar34": ["xilma12:o_uchxonali"],
    # 3–4-sinf
    "xilma34:o_kopaytir": ["xilma34:o_qoshayir", "xilma12:o_kopjadval"], "xilma34:o_bolish": ["xilma34:o_kopaytir"], "xilma34:o_alomat": ["xilma34:o_bolish"],
    "xilma34:o_kasr34": ["xilma34:o_bolish"], "xilma34:o_onli34": ["xilma34:o_kasr34", "xilma34:o_sonlar34"],
    "xilma34:o_perimetr34": ["xilma34:o_kopaytir", "xilma34:o_qoshayir"], "xilma34:o_tenglama34": ["xilma34:o_qoshayir", "xilma34:o_kopaytir"],
    "xilma34:o_jism34": ["xilma34:o_perimetr34"], "xilma34:o_yaxlit": ["xilma34:o_sonlar34"], "xilma34:o_diag34": ["xilma34:o_qoshayir", "xilma34:o_bolish"],
    "xilma6:o_tezlik": ["xilma34:o_kopaytir", "xilma34:o_bolish"], "xilma5:o_meyor": ["xilma34:o_bolish", "xilma34:o_kopaytir"],
    # 5-sinf
    "xilma5:o_kop10": ["xilma34:o_kopaytir"], "xilma5:o_tartib": ["xilma34:o_kopaytir", "xilma34:o_bolish"], "xilma5:o_masala": ["xilma5:o_tartib"],
    "xilma5:o_kasr": ["xilma34:o_kasr34", "xilma34:o_bolish", "xilma34:o_alomat"], "xilma5:o_onli": ["xilma34:o_onli34", "xilma5:o_kop10"],
    "xilma5:o_yuz": ["xilma34:o_perimetr34", "xilma34:o_bolish"], "xilma5:o_hajm": ["xilma34:o_perimetr34", "xilma34:o_kopaytir"],
    "xilma5:o_nisbat": ["xilma5:o_kasr", "xilma34:o_bolish"], "xilma5:o_foiz": ["xilma5:o_kasr", "xilma5:o_onli"],
    "xilma5:o_ortacha": ["xilma34:o_qoshayir", "xilma34:o_bolish"], "xilma5:o_burchak": ["xilma34:o_geom34"],
    "xilma5:o_uchburchak": ["xilma5:o_burchak"], "xilma5:o_tortburchak": ["xilma5:o_burchak", "xilma5:o_uchburchak"],
    # 6-sinf
    "xilma6:o_algebra": ["xilma5:o_tartib", "xilma34:o_tenglama34"], "xilma6:o_kasr_bol": ["xilma5:o_kasr"], "xilma6:o_foiz6": ["xilma5:o_foiz", "xilma5:o_kasr"],
    "xilma6:o_doira": ["xilma5:o_onli", "xilma34:o_perimetr34"], "xilma6:o_hajm6": ["xilma5:o_hajm"], "xilma6:o_diagramma": ["xilma5:o_foiz", "xilma5:o_burchak"],
    # 7–11 algebra
    "xilma711:a_ifoda": ["xilma6:o_algebra"], "xilma711:a_daraja": ["xilma34:o_kopaytir", "xilma711:a_ifoda"], "xilma711:a_kophad": ["xilma711:a_ifoda", "xilma711:a_daraja"],
    "xilma711:a_qisqa": ["xilma711:a_kophad", "xilma711:a_daraja"], "xilma711:a_ajratish": ["xilma711:a_qisqa", "xilma711:a_kophad"],
    "xilma711:a_kasr": ["xilma711:a_ajratish", "xilma5:o_kasr", "xilma6:o_kasr_bol"], "xilma711:a_chiziqli": ["xilma711:a_ifoda", "xilma6:o_algebra"],
    "xilma711:a_sistema": ["xilma711:a_chiziqli"], "xilma711:a_funksiya": ["xilma711:a_ifoda", "xilma711:a_chiziqli"],
    "xilma711:a_kvadrat": ["xilma711:a_ajratish", "xilma711:a_chiziqli", "xilma711:a_daraja"], "xilma711:a_tengsizlik": ["xilma711:a_chiziqli", "xilma711:a_kvadrat"],
    "xilma711:a_progressiya": ["xilma711:a_ifoda", "xilma711:a_daraja"], "xilma711:a_trig": ["xilma711:g_pifagor", "xilma6:o_doira"],
    "xilma711:a_log": ["xilma711:a_daraja", "xilma711:a_chiziqli"], "xilma711:a_hosila": ["xilma711:a_funksiya", "xilma711:a_daraja"],
    "xilma711:a_ehtimol": ["xilma5:o_kasr", "xilma711:a_kombinatorika"], "xilma711:a_statistika": ["xilma5:o_ortacha"],
    # 7–11 geometriya
    "xilma711:g_uchburchak": ["xilma711:g_burchak"], "xilma711:g_pifagor": ["xilma711:a_daraja", "xilma711:g_uchburchak"],
    "xilma711:g_yuz": ["xilma711:g_pifagor", "xilma5:o_yuz"], "xilma711:g_kopburchak": ["xilma711:g_uchburchak"],
    "xilma711:g_aylana": ["xilma711:g_burchak", "xilma711:g_pifagor"], "xilma711:g_vektor": ["xilma711:g_koordinata", "xilma711:g_pifagor"],
    "xilma711:g_oxshash": ["xilma5:o_nisbat", "xilma711:g_uchburchak"], "xilma711:g_trigteorema": ["xilma711:a_trig", "xilma711:g_pifagor"],
    "xilma711:g_koordinata": ["xilma711:g_pifagor"], "xilma711:g_stereo": ["xilma711:g_yuz", "xilma6:o_doira"],
}


NOMLAR = {"xilma12:o_son10": "10 gacha sonlar va sanash", "xilma12:o_qosh20": "20 gacha qo‘shish va ayirish", "xilma12:o_son100": "100 gacha sonlar",
          "xilma12:o_kopjadval": "Ko‘paytirish jadvali", "xilma12:o_uchxonali": "Uch xonali sonlar", 'xilma34:o_qoshayir': 'Ko‘p xonali sonlarni qo‘shish va ayirish', 'xilma34:o_kopaytir': 'Ko‘paytirish', 'xilma34:o_bolish': 'Bo‘lish va qoldiqli bo‘lish', 'xilma34:o_alomat': 'Bo‘linish alomatlari', 'xilma34:o_kasr34': 'Ulush va oddiy kasrlar', 'xilma34:o_sonlar34': 'Ko‘p xonali sonlar', 'xilma34:o_onli34': 'O‘nli kasr tushunchasi', 'xilma34:o_perimetr34': 'Perimetr va yuz', 'xilma34:o_tenglama34': 'Sodda tenglamalar', 'xilma34:o_geom34': 'Burchak va geometrik shakllar', 'xilma5:o_kop10': '10, 100, 1000 ga ko‘paytirish va bo‘lish', 'xilma5:o_tartib': 'Amallar tartibi', 'xilma5:o_kasr': 'Oddiy kasrlar ustida amallar', 'xilma5:o_onli': 'O‘nli kasrlar', 'xilma5:o_yuz': 'Uchburchak yuzi', 'xilma5:o_hajm': 'Hajm', 'xilma5:o_nisbat': 'Nisbatlar', 'xilma5:o_foiz': 'Foizlar', 'xilma5:o_ortacha': 'O‘rtacha qiymat', 'xilma5:o_burchak': 'Burchaklar', 'xilma5:o_uchburchak': 'Uchburchak burchaklari', 'xilma6:o_algebra': 'Algebraik ifoda va tenglama', 'xilma6:o_kasr_bol': 'Kasrlarni bo‘lish', 'xilma6:o_doira': 'Doira va aylana', 'xilma711:a_ifoda': 'Algebraik ifodalar', 'xilma711:a_daraja': 'Daraja va ildiz', 'xilma711:a_kophad': 'Birhad va ko‘phadlar', 'xilma711:a_qisqa': 'Qisqa ko‘paytirish formulalari', 'xilma711:a_ajratish': 'Ko‘paytuvchilarga ajratish', 'xilma711:a_chiziqli': 'Chiziqli tenglamalar', 'xilma711:a_funksiya': 'Funksiya va grafik', 'xilma711:a_kvadrat': 'Kvadrat tenglamalar', 'xilma711:a_trig': 'Trigonometriya asoslari', 'xilma711:a_kombinatorika': 'Kombinatorika', 'xilma711:g_burchak': 'Burchaklar va parallel to‘g‘ri chiziqlar', 'xilma711:g_uchburchak': 'Uchburchak', 'xilma711:g_pifagor': 'Pifagor teoremasi', 'xilma711:g_yuz': 'Ko‘pburchak yuzlari', 'xilma711:g_koordinata': 'Koordinatalar'}


def _mod(nom):
    return __import__(nom)


def oila_kaliti(sinf, mavzu):
    n = int((re.search(r"\d{1,2}", str(sinf or "")) or [0])[0] or 0) if re.search(r"\d", str(sinf or "")) else 0
    modul = "xilma12" if n in (1, 2) else "xilma34" if n in (3, 4) else "xilma5" if n == 5 else "xilma6" if n == 6 else "xilma711" if n >= 7 else ""
    if not modul:
        return None
    try:
        f = _mod(modul).oila_tanla(mavzu)
    except Exception:   # noqa: BLE001
        return None
    if not f or f.__name__ in ("aralash", "o_takror", "o_takror34"):
        return None
    return f"{f.__module__}:{f.__name__}"


def oila_fn(kalit):
    m, f = kalit.split(":")
    return getattr(_mod(m), f)


def oila_nomi(kalit):
    if kalit in NOMLAR:
        return NOMLAR[kalit]
    doc = (oila_fn(kalit).__doc__ or "").strip().split("\n")[0].rstrip(".")
    return doc or kalit.split(":")[1].replace("o_", "").replace("a_", "").replace("g_", "")


def _variantli(item, rr):
    q, j, y, xs = item[:4]
    vs = [str(j)] + [str(x) for x in xs if str(x) != str(j)][:3]
    vs = list(dict.fromkeys(vs))
    rr.shuffle(vs)
    return {"savol": q, "variantlar": vs, "togri": vs.index(str(j)), "yechim": y}


def savol(kalit, urug):
    f = oila_fn(kalit); rr = random.Random(urug)
    turlar = f(rr)
    for _ in range(12):
        t = turlar[rr.randrange(len(turlar))]
        try:
            it = t()
        except Exception:   # noqa: BLE001
            continue
        if it[3] and str(it[1]) not in [str(x) for x in it[3]]:
            return _variantli(it, rr)
    return None


# ───── REV517: «⚡ Kabu tezkor» — chizmali tezkor savollar (o'quvchi tugmani bosadi; chizmani frontend SVG qilib chizadi) ─────
def _v(rr, togri, xatolar):
    vs = [str(togri)] + [str(x) for x in xatolar if str(x) != str(togri)]
    vs = list(dict.fromkeys(vs))[:4]; rr.shuffle(vs)
    return vs, vs.index(str(togri))


def ch_kasr(rr):
    n = rr.choice([3, 4, 5, 6, 8]); k = rr.randint(1, n - 1)
    vs, t = _v(rr, f"{k}/{n}", [f"{n - k}/{n}", f"{k}/{n + 1}", f"{n}/{k}"])
    return {"chizma": {"tur": "kasr", "n": n, "k": k}, "savol": "Doiraning qaysi qismi bo‘yalgan?", "variantlar": vs, "togri": t}


def ch_nur(rr):
    q = rr.choice([1, 2, 5, 10]); bosh = rr.randint(0, 5) * q; p = rr.randint(1, 9)
    vs, t = _v(rr, bosh + p * q, [bosh + (p - 1) * q, bosh + (p + 1) * q, bosh + p + (1 if q == 1 else 0) * 2])
    return {"chizma": {"tur": "nur", "bosh": bosh, "qadam": q, "nuqta": p}, "savol": "Nuqta qaysi sonda turibdi?", "variantlar": vs, "togri": t}


def ch_burchak(rr):
    g = rr.choice([30, 45, 60, 90, 120, 135, 150])
    tur = "o‘tkir" if g < 90 else "to‘g‘ri" if g == 90 else "o‘tmas"
    vs = ["o‘tkir", "to‘g‘ri", "o‘tmas"]
    return {"chizma": {"tur": "burchak", "g": g}, "savol": "Bu qanday burchak?", "variantlar": vs, "togri": vs.index(tur)}


def ch_uchburchak(rr):
    a, b = rr.randint(30, 80), rr.randint(30, 70)
    vs, t = _v(rr, 180 - a - b, [180 - a, 360 - a - b, a + b])
    return {"chizma": {"tur": "uchburchak", "a": a, "b": b}, "savol": "Uchinchi burchak necha gradus?", "variantlar": [f"{v}°" for v in vs], "togri": t}


def ch_massiv(rr):
    q, u = rr.randint(2, 6), rr.randint(3, 8)
    vs, t = _v(rr, q * u, [q + u, q * u + q, (q - 1) * u])
    return {"chizma": {"tur": "massiv", "q": q, "u": u}, "savol": "Hammasi nechta nuqta?", "variantlar": vs, "togri": t}


def ch_tortburchak(rr, yuz=False):
    a, b = rr.randint(2, 9), rr.randint(2, 9)
    tog = a * b if yuz else 2 * (a + b)
    vs, t = _v(rr, tog, [2 * (a + b) if yuz else a * b, a + b, tog + 2])
    return {"chizma": {"tur": "tortburchak", "a": a, "b": b}, "savol": "Yuzi necha sm²?" if yuz else "Perimetri necha sm?", "variantlar": vs, "togri": t}


def ch_soat(rr):
    s, m = rr.randint(1, 12), rr.choice([0, 15, 30, 45])
    vs, t = _v(rr, f"{s}:{m:02d}", [f"{(m // 5) or 12}:{(s * 5) % 60:02d}", f"{s % 12 + 1}:{m:02d}", f"{s}:{(m + 15) % 60:02d}"])
    return {"chizma": {"tur": "soat", "s": s, "m": m}, "savol": "Soat necha?", "variantlar": vs, "togri": t}


def ch_foiz(rr):
    p = rr.choice([10, 20, 25, 40, 50, 75])
    vs, t = _v(rr, f"{p}%", [f"{100 - p}%", f"{max(5, p // 2)}%", f"{min(95, p + 15)}%"])
    return {"chizma": {"tur": "foiz", "p": p}, "savol": "Doiraning bo‘yalgan qismi necha foiz?", "variantlar": vs, "togri": t}


def ch_togrimi(kalit, rr):
    """Har qanday mavzu: ekranda misol va javob — to'g'rimi? (✅ / ❌)"""
    f = oila_fn(kalit); turlar = f(rr)
    for _ in range(10):
        try:
            q, j, y, xs = turlar[rr.randrange(len(turlar))]()
        except Exception:   # noqa: BLE001
            continue
        if not xs or len(str(q)) > 90 or "(1" in str(q):
            continue
        togri = rr.random() < 0.5
        return {"chizma": {"tur": "togrimi", "javob": str(j if togri else xs[0])}, "savol": str(q),
                "variantlar": ["✅ To‘g‘ri", "❌ Noto‘g‘ri"], "togri": 0 if togri else 1, "yechim": y}
    return None


# REV518: chizma NOMIGA emas — har oilaga faqat O'Z MAZMUNIGA mos, javob CHIZMADAN topiladigan savollar.
def ch_guruh(rr):   # bo'lish: nuqtalar guruhlarga ajratilgan, ortgani alohida
    g, n = rr.randint(3, 5), rr.randint(2, 5); q = rr.randint(1, g - 1)
    vs, t = _v(rr, n, [n + 1, g, q])
    return {"chizma": {"tur": "guruh", "g": g, "n": n, "q": q}, "savol": f"{g * n + q} ta nuqta {g} tadan guruhlandi. Nechta to‘liq guruh bo‘ldi?", "variantlar": vs, "togri": t}


def ch_blok(rr):   # o'nlik tayoqchalar va birliklar
    o, b = rr.randint(1, 9), rr.randint(0, 9)
    vs, t = _v(rr, 10 * o + b, [10 * b + o if b else o + 1, o + b, 10 * o + b + 10])
    return {"chizma": {"tur": "blok", "o": o, "b": b}, "savol": "Tayoqchada 10 tadan kubik. Hammasi nechta?", "variantlar": vs, "togri": t}


def ch_sakrash(rr):   # son nurida sakrash — qo'shish/ayirish
    a, d = rr.randint(1, 9), rr.randint(2, 8); ayir = rr.random() < 0.4 and a > d
    natija = a - d if ayir else a + d
    vs, t = _v(rr, natija, [natija + 1, natija - 1, a])
    return {"chizma": {"tur": "sakrash", "a": a, "d": d, "ayir": ayir}, "savol": f"Kabu {a} dan {'chapga' if ayir else 'o‘ngga'} {d} qadam sakradi. Qayerga tushdi?", "variantlar": vs, "togri": t}


def ch_panjara(rr, foiz=False):   # 10×10 panjara — o'nli kasr yoki foiz
    k = rr.randint(5, 95)
    if foiz:
        vs, t = _v(rr, f"{k}%", [f"{100 - k}%", f"{k // 10}%", f"{min(99, k + 10)}%"])
        return {"chizma": {"tur": "panjara", "k": k}, "savol": "100 katakdan bo‘yalgani necha foiz?", "variantlar": vs, "togri": t}
    js = f"0,{k:02d}".rstrip("0") if k % 10 else f"0,{k // 10}"
    vs, t = _v(rr, js, [f"{k}", f"0,{100 - k:02d}".rstrip("0"), f"{k / 10:g}".replace(".", ",")])
    return {"chizma": {"tur": "panjara", "k": k}, "savol": "Bo‘yalgan qism — qaysi o‘nli kasr? (butun = 100 katak)", "variantlar": vs, "togri": t}


def ch_ustun(rr, savol="eng"):   # ustunli diagramma
    v = [rr.randint(2, 9) for _ in range(4)]; nom = ["Du", "Se", "Ch", "Pa"]
    if savol == "orta":
        while sum(v) % 4:
            v[rr.randrange(4)] += 1
        vs, t = _v(rr, sum(v) // 4, [max(v), sum(v), min(v)])
        return {"chizma": {"tur": "ustun", "v": v, "nom": nom}, "savol": "Ustunlar balandligining o‘rtacha qiymati?", "variantlar": vs, "togri": t}
    vs, t = _v(rr, sum(v), [max(v) * 4, sum(v) - min(v), max(v)])
    return {"chizma": {"tur": "ustun", "v": v, "nom": nom}, "savol": "To‘rt kunda jami nechta?", "variantlar": vs, "togri": t}


def ch_yaxlit(rr):   # son nurida nuqta qaysi o'nlikka yaqin
    o = rr.randint(1, 8) * 10; b = rr.choice([1, 2, 3, 4, 6, 7, 8, 9])
    vs, t = _v(rr, o + (10 if b >= 5 else 0), [o + (0 if b >= 5 else 10), o + b, o + 5])
    return {"chizma": {"tur": "yaxlit", "o": o, "b": b}, "savol": "Belgilangan son qaysi o‘nlikka yaqinroq?", "variantlar": vs, "togri": t}


def ch_tarozi(rr):   # tenglama — tarozi
    x, a = rr.randint(2, 9), rr.randint(1, 9)
    vs, t = _v(rr, x, [x + a, a, x + 1])
    return {"chizma": {"tur": "tarozi", "a": a, "s": x + a}, "savol": "Tarozi muvozanatda. Qutichadagi x necha?", "variantlar": vs, "togri": t}


def ch_kuboid(rr):
    a, b, c = rr.randint(2, 6), rr.randint(2, 5), rr.randint(2, 5)
    vs, t = _v(rr, a * b * c, [a + b + c, 2 * (a * b + b * c + a * c), a * b])
    return {"chizma": {"tur": "kuboid", "a": a, "b": b, "c": c}, "savol": "Kuboid hajmi necha sm³?", "variantlar": vs, "togri": t}


def ch_munchoq(rr):   # nisbat — rangli munchoqlar
    q, k = rr.randint(1, 5), rr.randint(1, 5)
    while q == k:
        k = rr.randint(1, 5)
    from math import gcd
    g = gcd(q, k)
    vs, t = _v(rr, f"{q // g} : {k // g}", [f"{k // g} : {q // g}", f"{q} : {q + k}", f"{q + k} : {k}"])
    return {"chizma": {"tur": "munchoq", "q": q, "k": k}, "savol": "Qizil va ko‘k munchoqlar nisbati?", "variantlar": vs, "togri": t}


def ch_qoshni(rr):   # to'g'ri chiziqdagi qo'shni burchaklar
    a = rr.randint(25, 155)
    vs, t = _v(rr, f"{180 - a}°", [f"{a}°", f"{360 - a}°", f"{abs(90 - a)}°"])
    return {"chizma": {"tur": "qoshni", "a": a}, "savol": "To‘g‘ri chiziqda. x necha gradus?", "variantlar": vs, "togri": t}


def ch_uchburchak_yuz(rr):
    a, h = rr.randint(3, 10) * 2, rr.randint(3, 9)
    vs, t = _v(rr, a * h // 2, [a * h, a + h, a * h // 4 or 1])
    return {"chizma": {"tur": "uchyuz", "a": a, "h": h}, "savol": "Uchburchak yuzi necha sm²?", "variantlar": vs, "togri": t}


def ch_doira_r(rr):
    r = rr.randint(2, 9)
    vs, t = _v(rr, 2 * r, [r, r * r, 4 * r])
    return {"chizma": {"tur": "doira_r", "r": r}, "savol": "Diametri necha sm?", "variantlar": vs, "togri": t}


def ch_grafik(rr):   # chiziqli funksiya grafigi
    k, b = rr.choice([-2, -1, 1, 2, 3]), rr.randint(-3, 3)
    if rr.random() < 0.5:
        vs, t = _v(rr, b, [k, -b if b else 1, b + 1])
        return {"chizma": {"tur": "grafik", "k": k, "b": b}, "savol": "To‘g‘ri chiziq Oy o‘qini qaysi nuqtada kesadi? (y ni tanlang)", "variantlar": vs, "togri": t}
    vs, t = _v(rr, k, [b if b != k else k + 1, -k, k * 2])
    return {"chizma": {"tur": "grafik", "k": k, "b": b}, "savol": "Grafikdan burchak koeffitsientini toping (x 1 ga oshganda y qanchaga o‘zgaradi?)", "variantlar": vs, "togri": t}


def ch_parabola(rr):
    p, q = sorted(rr.sample(range(-4, 5), 2))
    vs, t = _v(rr, f"{p} va {q}", [f"{-p} va {-q}", f"{p} va {q + 1}", f"{p * q}"])
    return {"chizma": {"tur": "parabola", "p": p, "q": q}, "savol": "Parabola Ox o‘qini qaysi nuqtalarda kesadi? (tenglama ildizlari)", "variantlar": vs, "togri": t}


def ch_oraliq(rr):
    a = rr.randint(-4, 4); yopiq = rr.random() < 0.5; ong = rr.random() < 0.5
    tog = f"x {'≥' if yopiq else '>'} {a}" if ong else f"x {'≤' if yopiq else '<'} {a}"
    xs = [f"x {'>' if yopiq else '≥'} {a}" if ong else f"x {'<' if yopiq else '≤'} {a}", f"x {'≤' if yopiq else '<'} {a}" if ong else f"x {'≥' if yopiq else '>'} {a}"]
    vs, t = _v(rr, tog, xs + [f"x = {a}"])
    return {"chizma": {"tur": "oraliq", "a": a, "yopiq": yopiq, "ong": ong}, "savol": "Son o‘qida qaysi tengsizlik tasvirlangan?", "variantlar": vs, "togri": t}


def ch_pifagor(rr):
    a, b, c = rr.choice([(3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17), (9, 12, 15)])
    vs, t = _v(rr, c, [a + b, c + 1, b])
    return {"chizma": {"tur": "pifagor", "a": a, "b": b}, "savol": "Gipotenuza x = ?", "variantlar": vs, "togri": t}


def ch_parallel(rr):
    a = rr.randint(35, 145); tur = rr.choice(["moslash", "almashinuvchi", "bir_tomonli"])
    tog = 180 - a if tur == "bir_tomonli" else a
    vs, t = _v(rr, f"{tog}°", [f"{180 - tog}°", f"{90}°", f"{360 - a}°"])
    return {"chizma": {"tur": "parallel", "a": a, "q": tur}, "savol": "a ∥ b. x necha gradus?", "variantlar": vs, "togri": t}


def ch_aylana_burchak(rr):
    g = rr.randint(25, 80) * 2
    vs, t = _v(rr, f"{g // 2}°", [f"{g}°", f"{180 - g}°", f"{g // 4}°"])
    return {"chizma": {"tur": "aylana_burchak", "g": g}, "savol": f"Markaziy burchak {g}°. Shu yoyga tiralgan ichki chizilgan burchak x?", "variantlar": vs, "togri": t}


def ch_koordinata(rr):
    x, y = rr.randint(-4, 4) or 2, rr.randint(-4, 4) or -3
    vs, t = _v(rr, f"({x}; {y})", [f"({y}; {x})", f"({-x}; {y})", f"({x}; {-y})"])
    return {"chizma": {"tur": "koordinata", "x": x, "y": y}, "savol": "A nuqtaning koordinatalari?", "variantlar": vs, "togri": t}


def ch_vektor(rr):
    x, y = rr.randint(-3, 4) or 2, rr.randint(-3, 3) or 1
    vs, t = _v(rr, f"({x}; {y})", [f"({y}; {x})", f"({-x}; {-y})", f"({x}; {-y})"])
    return {"chizma": {"tur": "vektor", "x": x, "y": y}, "savol": "Vektor koordinatalari?", "variantlar": vs, "togri": t}


def ch_trapetsiya(rr):
    a, b, h = rr.randint(3, 6), rr.randint(7, 11), rr.randint(2, 6)
    vs, t = _v(rr, (a + b) * h // 2 if (a + b) * h % 2 == 0 else f"{(a + b) * h / 2:g}".replace(".", ","), [(a + b) * h, a * b, (a + b) + h])
    return {"chizma": {"tur": "trapetsiya", "a": a, "b": b, "h": h}, "savol": "Trapetsiya yuzi?", "variantlar": vs, "togri": t}


def ch_oxshash(rr):
    k = rr.choice([2, 3]); a, b = rr.randint(2, 5), rr.randint(3, 6)
    vs, t = _v(rr, b * k, [b + k, a * k, b])
    return {"chizma": {"tur": "oxshash", "a": a, "b": b, "k": k}, "savol": "Uchburchaklar o‘xshash. x = ?", "variantlar": vs, "togri": t}


def ch_birlik_aylana(rr):
    g, sv = rr.choice([(30, "1/2"), (60, "√3/2"), (90, "1"), (150, "1/2"), (180, "0")])
    vs, t = _v(rr, sv, ["√2/2", "−1/2", "√3/2" if sv != "√3/2" else "1/2"])
    return {"chizma": {"tur": "birlik", "g": g}, "savol": f"Birlik aylanada {g}° burchak. sin {g}° = ? (nuqtaning y koordinatasi)", "variantlar": vs, "togri": t}


def ch_girdirak(rr):
    n = rr.choice([4, 6, 8]); k = rr.randint(1, n - 1)
    from fractions import Fraction as _F
    f = _F(k, n)
    vs, t = _v(rr, f"{f.numerator}/{f.denominator}", [f"{n - k}/{n}", f"1/{n}", f"{k}/{n + 1}"])
    return {"chizma": {"tur": "girdirak", "n": n, "k": k}, "savol": "Strelka sariq bo‘lakka tushish ehtimoli?", "variantlar": vs, "togri": t}


def ch_zinapoya(rr):
    a, d = rr.randint(1, 4), rr.randint(1, 3)
    vs, t = _v(rr, a + 3 * d, [a + 4 * d, a + 2 * d, 4 * a])
    return {"chizma": {"tur": "zinapoya", "a": a, "d": d}, "savol": "Naqsh davom etsa, 4-ustunda nechta kubik bo‘ladi?", "variantlar": vs, "togri": t}


# Har oila → faqat o'ziga mos chizmalar. Mos chizma yo'q oilada chizma ishlatilmaydi.
CHIZMA_OILA = {
    "xilma12:o_qosh20": [ch_sakrash], "xilma12:o_son100": [ch_blok], "xilma12:o_kopjadval": [ch_massiv, ch_guruh], "xilma12:o_olchov12": [ch_soat],
    "xilma12:o_yuz12": [lambda rr: ch_tortburchak(rr, True)], "xilma12:o_shakl12": [ch_tortburchak], "xilma12:o_uchxonali": [ch_blok],
    "xilma34:o_kopaytir": [ch_massiv], "xilma34:o_bolish": [ch_guruh], "xilma34:o_kasr34": [ch_kasr], "xilma34:o_onli34": [ch_panjara],
    "xilma34:o_perimetr34": [ch_tortburchak, lambda rr: ch_tortburchak(rr, True)], "xilma34:o_geom34": [ch_burchak], "xilma34:o_yaxlit": [ch_yaxlit],
    "xilma34:o_sonlar34": [ch_nur], "xilma34:o_diag34": [ch_ustun], "xilma34:o_tenglama34": [ch_tarozi], "xilma34:o_jism34": [ch_kuboid],
    "xilma5:o_kasr": [ch_kasr], "xilma5:o_onli": [ch_panjara], "xilma5:o_foiz": [lambda rr: ch_panjara(rr, True), ch_foiz], "xilma5:o_burchak": [ch_qoshni, ch_burchak],
    "xilma5:o_uchburchak": [ch_uchburchak], "xilma5:o_yuz": [ch_uchburchak_yuz], "xilma5:o_hajm": [ch_kuboid], "xilma5:o_nisbat": [ch_munchoq],
    "xilma5:o_ortacha": [lambda rr: ch_ustun(rr, "orta")], "xilma5:o_kop10": [ch_panjara], "xilma5:o_tartib": [ch_massiv],
    "xilma6:o_algebra": [ch_tarozi], "xilma6:o_doira": [ch_doira_r], "xilma6:o_diagramma": [ch_foiz], "xilma6:o_kasr_bol": [ch_kasr], "xilma6:o_hajm6": [ch_kuboid],
    "xilma711:a_chiziqli": [ch_tarozi], "xilma711:a_funksiya": [ch_grafik], "xilma711:a_kvadrat": [ch_parabola], "xilma711:a_tengsizlik": [ch_oraliq],
    "xilma711:a_trig": [ch_birlik_aylana], "xilma711:a_statistika": [lambda rr: ch_ustun(rr, "orta")], "xilma711:a_progressiya": [ch_zinapoya],
    "xilma711:a_ehtimol": [ch_girdirak], "xilma711:g_pifagor": [ch_pifagor], "xilma711:g_burchak": [ch_parallel], "xilma711:g_uchburchak": [ch_uchburchak],
    "xilma711:g_aylana": [ch_aylana_burchak], "xilma711:g_koordinata": [ch_koordinata], "xilma711:g_vektor": [ch_vektor], "xilma711:g_yuz": [ch_trapetsiya],
    "xilma711:g_oxshash": [ch_oxshash], "xilma711:g_stereo": [ch_kuboid],
}


def tezkor_savol(kalit, rr):
    fl = CHIZMA_OILA.get(kalit)
    if fl and rr.random() < 0.8:
        return rr.choice(fl)(rr)
    return ch_togrimi(kalit, rr) if rr.random() < 0.4 else None


def create_router(platform, dars_xonasi_tashqi=None):
    router = APIRouter(tags=["bilim_zanjiri"])

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    @router.get("/api/bilim_zanjiri/kirish")
    def kirish(topic_code: str, token: str = "", authorization: Optional[str] = Header(None)):
        """Darsdan oldin: oldingi mavzulardan 3 tagacha savol (ko'p tanlovli)."""
        u = uid(token, authorization)
        try:
            tashqi = dars_xonasi_tashqi() if callable(dars_xonasi_tashqi) else (dars_xonasi_tashqi or {})
            yukla = tashqi.get("yukla")
            les = yukla(topic_code, "uz") if yukla else None
        except Exception:   # noqa: BLE001
            les = None
        top = (les or {}).get("topic") or {}
        if not re.search(r"matem|algebra|geometr", str(top.get("fan") or ""), re.I):
            return {"savollar": []}
        k = oila_kaliti(top.get("sinf"), top.get("mavzu"))
        # REV516: 4–5 ta savol (bitta emas): har oldingi mavzudan 2 tadan; oz bo'lsa — undan oldingilaridan ham
        oldingi = list(ZANJIR.get(k or "", []))
        for ok in list(oldingi):
            if len(oldingi) >= 3:
                break
            for o2 in ZANJIR.get(ok, []):
                if o2 not in oldingi and o2 != k:
                    oldingi.append(o2)
        urug = u * 7919 + int(time.time() // 86400)
        out, korilgan = [], set()
        for tur in range(3 if len(oldingi) == 1 else 2):
            for i, ok in enumerate(oldingi[:4]):
                if len(out) >= 5:
                    break
                s = None   # REV517: avval «⚡ Kabu tezkor» — chizmali yoki «to'g'rimi?», bo'lmasa oddiy savol
                try:
                    s = tezkor_savol(ok, random.Random(f"{urug}:{topic_code}:{i}:{tur}:t"))
                except Exception:   # noqa: BLE001
                    s = None
                s = s or savol(ok, f"{urug}:{topic_code}:{i}:{tur}")
                kal = f'{s["savol"]}|{s.get("chizma")}' if s else ""   # chizmali savollar matni bir xil bo'lishi mumkin — chizmasi bilan farqlanadi
                if s and kal not in korilgan:
                    korilgan.add(kal); out.append({**s, "oila": ok, "nom": oila_nomi(ok)})
        out.sort(key=lambda x: oldingi.index(x["oila"]))
        return {"mavzu": top.get("mavzu"), "oila": k, "savollar": out}

    @router.get("/api/bilim_zanjiri/takror")
    def takror(oila: str, token: str = "", authorization: Optional[str] = Header(None)):
        """«Avval buni eslab olaylik»: qisqa nazariya + namunaviy yechim + 6 ta mashq."""
        u = uid(token, authorization)
        if oila not in {x for v in ZANJIR.values() for x in v} | set(ZANJIR):
            raise HTTPException(404, "Mavzu topilmadi")
        f = oila_fn(oila); rr = random.Random(f"{u}:{oila}:{int(time.time() // 3600)}")
        turlar = f(rr); namuna = None
        for t in turlar:
            try:
                namuna = t(); break
            except Exception:   # noqa: BLE001
                continue
        mashq = []
        for i in range(30):
            if len(mashq) >= 6:
                break
            s = savol(oila, f"{u}:{oila}:{i}:{int(time.time() // 3600)}")
            if s and s["savol"] not in [m["savol"] for m in mashq]:
                mashq.append(s)
        return {"oila": oila, "nom": oila_nomi(oila),
                "namuna": {"savol": namuna[0], "javob": str(namuna[1]), "yechim": namuna[2]} if namuna else None, "mashqlar": mashq}

    return router
