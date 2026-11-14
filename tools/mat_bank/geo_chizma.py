"""REV566: ANIQ geometrik chizma. Dars qatori «[[CHIZMA: romb a=5 d1=6 d2=8]]» → koordinatalar HISOBLANADI (ko'z bilan chizilmaydi).
Berilgan sonlar bir-biriga zid bo'lsa (masalan romb uchun (d1/2)²+(d2/2)² ≠ a²) — xato; dars qabul qilinmaydi.

Shakllar:
  romb          a, d1, d2, burchak (A burchagi, gradus), h        — ikkitasi yetarli; ortiqchasi mos kelishi shart
  uchburchak    a, b, c | a, b, burchak (C burchagi)              — a=BC, b=CA, c=AB
  togri_uchburchak  a, b, c (ikkitasi yetarli)                    — to'g'ri burchak C da; a, b — katetlar, c — gipotenuza
  parallelogramm a, b, burchak [, h]                              — burchak A da; h — AB ga tushirilgan balandlik (b·sin burchak ga teng bo'lishi shart)
  trapetsiya    a, b, h [, yon] [, tur=togri]                     — a — katta asos (AB), b — kichik asos (DC); tur=togri — to'g'ri burchakli
  aylana        r [, vatar]                                       — vatar bo'lsa markazdan unga masofa ham chiziladi
Chiqish: {"nom", "nuqtalar":{ism:[x,y]}, "kesmalar":[{"a","b","yozuv","uzuq"}], "burchaklar":[{"uch","a","b","tur":"togri"|"yoy","yozuv"}],
          "dumaloqlar":[{"c","r","yozuv"}], "yozuvlar":[{"p","matn"}], "korinadigan":[nuqta nomlari], "chegara":[x0,y0,x1,y1]}
Faqat foydalanuvchi bergan sonlar yoziladi (hisoblangan boshqalar yozilmaydi).
"""
import math
import re

TOL = 1e-3          # nisbiy chegara: berilgan ortiqcha sonlar shu aniqlikda mos kelsin
SHAKLLAR = {"romb", "uchburchak", "togri_uchburchak", "parallelogramm", "trapetsiya", "aylana"}
RUXSAT = {"romb": {"a", "d1", "d2", "burchak", "h"}, "uchburchak": {"a", "b", "c", "burchak"}, "togri_uchburchak": {"a", "b", "c"}, "parallelogramm": {"a", "b", "burchak", "h"},
          "trapetsiya": {"a", "b", "h", "yon", "tur"}, "aylana": {"r", "vatar"}}


class GeoXato(ValueError):
    pass


def yozuv(v):
    """Son → qisqa matn: 5 → «5», 4.5 → «4,5», 2.8284 → «2,83»."""
    t = f"{v:.2f}" if abs(v - round(v, 2)) < 0.0005 else f"{v:.3f}"       # 4,8 → «4,8»; 5,196 → «5,196»
    return t.rstrip("0").rstrip(".").replace(".", ",")


def parse(arg):
    """«romb a=5 d1=6 d2=8» → ("romb", {a:5.0,…}). Noma'lum shakl/parametr, takror, manfiy yoki nol son — GeoXato."""
    t = (arg or "").strip().split()
    if not t:
        raise GeoXato("CHIZMA: shakl nomi yo'q")
    nom = t[0].lower()
    if nom not in SHAKLLAR:
        raise GeoXato(f"CHIZMA: noma'lum shakl «{t[0]}» (mavjud: {', '.join(sorted(SHAKLLAR))})")
    p = {}
    for x in t[1:]:
        m = re.fullmatch(r"([a-z0-9_]+)=(-?\d+(?:\.\d+)?|[a-z_]+)", x)
        if not m:
            raise GeoXato(f"CHIZMA: «{x}» noto'g'ri («a=5» ko'rinishida; o'nli kasr — nuqta bilan)")
        k, v = m.group(1), m.group(2)
        if k not in RUXSAT[nom]:
            raise GeoXato(f"CHIZMA {nom}: «{k}» parametri yo'q (mavjud: {', '.join(sorted(RUXSAT[nom]))})")
        if k in p:
            raise GeoXato(f"CHIZMA: «{k}» ikki marta berilgan")
        if k == "tur":
            if v not in ("togri", "teng_yonli"):
                raise GeoXato("CHIZMA trapetsiya: tur=togri yoki tur=teng_yonli")
            p[k] = v
            continue
        try:
            f = float(v)
        except ValueError:
            raise GeoXato(f"CHIZMA: «{k}» son bo'lsin")
        if f <= 0:
            raise GeoXato(f"CHIZMA: «{k}» musbat bo'lsin")
        if k == "burchak" and f >= 180:
            raise GeoXato("CHIZMA: burchak 0° dan katta va 180° dan kichik bo'lsin")
        p[k] = f
    return nom, p


def _mos(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def _kes(a, b, matn=None, uzuq=False):
    return {"a": a, "b": b, "yozuv": matn, "uzuq": uzuq}


def _chegara(nq, dum=()):
    xs = [p[0] for p in nq.values()]; ys = [p[1] for p in nq.values()]
    for d in dum:
        xs += [d["c"][0] - d["r"], d["c"][0] + d["r"]]; ys += [d["c"][1] - d["r"], d["c"][1] + d["r"]]
    return [min(xs), min(ys), max(xs), max(ys)]


def _asos(nom, nq, kes, burch=(), dum=(), yoz=(), korinadigan=None):
    return {"nom": nom, "nuqtalar": {k: [round(v[0], 9), round(v[1], 9)] for k, v in nq.items()}, "kesmalar": kes, "burchaklar": list(burch), "dumaloqlar": list(dum),
            "yozuvlar": list(yoz), "korinadigan": korinadigan if korinadigan is not None else list(nq), "chegara": [round(x, 9) for x in _chegara(nq, dum)]}


def romb(p):
    a, d1, d2, al, h = (p.get(k) for k in ("a", "d1", "d2", "burchak", "h"))
    if len([x for x in (a, d1, d2, al, h) if x is not None]) < 2:
        raise GeoXato("CHIZMA romb: kamida ikkita son kerak (masalan a va d1)")
    # d1 = AC, d2 = BD; A burchagi: tan(A/2) = d2/d1
    if d1 and d2:
        a0 = math.hypot(d1 / 2, d2 / 2)
    elif a and d1:
        if d1 >= 2 * a:
            raise GeoXato("CHIZMA romb: diagonal 2a dan kichik bo'lsin")
        a0, d2 = a, 2 * math.sqrt(a * a - (d1 / 2) ** 2)
    elif a and d2:
        if d2 >= 2 * a:
            raise GeoXato("CHIZMA romb: diagonal 2a dan kichik bo'lsin")
        a0, d1 = a, 2 * math.sqrt(a * a - (d2 / 2) ** 2)
    elif a and al:
        a0, d1, d2 = a, 2 * a * math.cos(math.radians(al) / 2), 2 * a * math.sin(math.radians(al) / 2)
    elif a and h:
        if h >= a:
            raise GeoXato("CHIZMA romb: balandlik tomondan kichik bo'lsin")
        alfa = math.degrees(math.asin(h / a)); a0, d1, d2 = a, 2 * a * math.cos(math.radians(alfa) / 2), 2 * a * math.sin(math.radians(alfa) / 2)
    else:
        raise GeoXato("CHIZMA romb: bu sonlar to'plamidan romb aniqlanmaydi (a bilan birga yana bittasi yoki d1 bilan d2 kerak)")
    a = a0
    alfa = math.degrees(2 * math.atan2(d2, d1))                 # (d1, d2) bo'yicha burchak; sin(alfa) = sin(180° − alfa), balandlik ikkalasida bir xil
    alfa_burchak = alfa if "burchak" not in p else (alfa if _mos(p["burchak"], alfa) else 180 - alfa)
    for nom, berilgan, hisob in (("a", p.get("a"), a), ("d1", p.get("d1"), d1), ("d2", p.get("d2"), d2), ("burchak", p.get("burchak"), alfa_burchak), ("h", p.get("h"), a * math.sin(math.radians(alfa)))):
        if berilgan is not None and not _mos(berilgan, hisob):
            raise GeoXato(f"CHIZMA romb: sonlar zid — {nom}={yozuv(berilgan)} berilgan, qolganlardan {yozuv(hisob)} chiqadi (d1²+d2² = 4a² bo'lishi kerak)")
    # Yo'nalish: burchak berilsa — A burchagi shu (AC = 2a·cos(A/2)); berilmasa — A O'TKIR burchak (AC uzun diagonal), darslikdagi odatiy ko'rinish
    if "burchak" in p:
        AC, BD = 2 * a * math.cos(math.radians(p["burchak"]) / 2), 2 * a * math.sin(math.radians(p["burchak"]) / 2)
    else:
        AC, BD = max(d1, d2), min(d1, d2)
    A, C, B, D, O = (-AC / 2, 0.0), (AC / 2, 0.0), (0.0, BD / 2), (0.0, -BD / 2), (0.0, 0.0)
    nq = {"A": A, "B": B, "C": C, "D": D, "O": O}
    yoz_ac = yoz_bd = None          # d1 va d2 yozuvlari uzunligi mos diagonalga qo'yiladi
    for kal, qiy in (("d1", d1), ("d2", d2)):
        if kal in p:
            if _mos(qiy, AC) and yoz_ac is None:
                yoz_ac = yozuv(p[kal])
            elif yoz_bd is None:
                yoz_bd = yozuv(p[kal])
            else:
                yoz_ac = yozuv(p[kal])
    kes = [_kes("A", "B", yozuv(p["a"]) if "a" in p else None), _kes("B", "C"), _kes("C", "D"), _kes("D", "A"), _kes("A", "C", yoz_ac, True), _kes("B", "D", yoz_bd, True)]
    bur = [{"uch": "O", "a": "A", "b": "B", "tur": "togri", "yozuv": None}]
    if "burchak" in p:
        bur.append({"uch": "A", "a": "B", "b": "D", "tur": "yoy", "yozuv": yozuv(p["burchak"]) + "°"})
    if "h" in p:      # D dan AB ga tushirilgan balandlik
        dx, dy = B[0] - A[0], B[1] - A[1]; t = ((D[0] - A[0]) * dx + (D[1] - A[1]) * dy) / (dx * dx + dy * dy); E = (A[0] + t * dx, A[1] + t * dy)
        nq["E"] = E; kes.append(_kes("D", "E", yozuv(p["h"]), True)); bur.append({"uch": "E", "a": "D", "b": "B", "tur": "togri", "yozuv": None})
    return _asos("romb", nq, kes, bur, korinadigan=[k for k in nq if k != "E"] + (["E"] if "h" in p else []))


def uchburchak(p):
    a, b, c, g = (p.get(k) for k in ("a", "b", "c", "burchak"))
    if a and b and c and not g:
        pass
    elif a and b and g and not c:
        c = math.sqrt(a * a + b * b - 2 * a * b * math.cos(math.radians(g)))
    elif a and b and c and g:
        pass
    else:
        raise GeoXato("CHIZMA uchburchak: uch tomon (a, b, c) yoki ikki tomon va ular orasidagi burchak (a, b, burchak) bering")
    if not (a + b > c and a + c > b and b + c > a):
        raise GeoXato(f"CHIZMA uchburchak: {yozuv(a)}, {yozuv(b)}, {yozuv(c)} tomonlardan uchburchak bo'lmaydi (har ikki tomon yig'indisi uchinchisidan katta bo'lsin)")
    if g is not None and "c" in p:
        cg = math.degrees(math.acos((a * a + b * b - c * c) / (2 * a * b)))
        if not _mos(g, cg):
            raise GeoXato(f"CHIZMA uchburchak: sonlar zid — burchak={yozuv(g)}°, tomonlardan {yozuv(cg)}° chiqadi")
    cx = (b * b + c * c - a * a) / (2 * c); cy = math.sqrt(max(b * b - cx * cx, 0.0))
    nq = {"A": (0.0, 0.0), "B": (c, 0.0), "C": (cx, cy)}
    kes = [_kes("B", "C", yozuv(p["a"]) if "a" in p else None), _kes("C", "A", yozuv(p["b"]) if "b" in p else None), _kes("A", "B", yozuv(p["c"]) if "c" in p else None)]
    bur = [{"uch": "C", "a": "A", "b": "B", "tur": "yoy", "yozuv": yozuv(g) + "°"}] if g is not None else []
    return _asos("uchburchak", nq, kes, bur)


def togri_uchburchak(p):
    a, b, c = (p.get(k) for k in ("a", "b", "c"))
    if len([x for x in (a, b, c) if x]) < 2:
        raise GeoXato("CHIZMA togri_uchburchak: ikkita tomon kerak (a, b — katetlar; c — gipotenuza)")
    if c and (a and c <= a or b and c <= b):
        raise GeoXato("CHIZMA togri_uchburchak: gipotenuza katetdan katta bo'lsin")
    if a and b:
        h = math.hypot(a, b)
    elif a and c:
        b, h = math.sqrt(c * c - a * a), c
    else:
        a, h = math.sqrt(c * c - b * b), c
    if c and not _mos(c, h):
        raise GeoXato(f"CHIZMA togri_uchburchak: sonlar zid — c={yozuv(c)} berilgan, katetlardan {yozuv(h)} chiqadi (a² + b² = c²)")
    nq = {"C": (0.0, 0.0), "B": (a, 0.0), "A": (0.0, b)}
    kes = [_kes("B", "C", yozuv(p["a"]) if "a" in p else None), _kes("C", "A", yozuv(p["b"]) if "b" in p else None), _kes("A", "B", yozuv(p["c"]) if "c" in p else None)]
    return _asos("togri_uchburchak", nq, kes, [{"uch": "C", "a": "B", "b": "A", "tur": "togri", "yozuv": None}])


def parallelogramm(p):
    a, b, al, h = (p.get(k) for k in ("a", "b", "burchak", "h"))
    if not (a and b and al):
        raise GeoXato("CHIZMA parallelogramm: a, b va burchak (A burchagi) kerak")
    hh = b * math.sin(math.radians(al))
    if h is not None and not _mos(h, hh):
        raise GeoXato(f"CHIZMA parallelogramm: sonlar zid — h={yozuv(h)} berilgan, b·sin({yozuv(al)}°) = {yozuv(hh)}")
    A, B = (0.0, 0.0), (a, 0.0); D = (b * math.cos(math.radians(al)), hh); C = (B[0] + D[0], D[1]); nq = {"A": A, "B": B, "C": C, "D": D}
    kes = [_kes("A", "B", yozuv(a)), _kes("B", "C", yozuv(b)), _kes("C", "D"), _kes("D", "A")]; bur = [{"uch": "A", "a": "B", "b": "D", "tur": "yoy", "yozuv": yozuv(al) + "°"}]
    if h is not None:
        nq["E"] = (D[0], 0.0); kes.append(_kes("D", "E", yozuv(h), True)); bur.append({"uch": "E", "a": "D", "b": "B", "tur": "togri", "yozuv": None})
    return _asos("parallelogramm", nq, kes, bur)


def trapetsiya(p):
    a, b, h, yon, tur = (p.get(k) for k in ("a", "b", "h", "yon", "tur"))
    if not (a and b and h):
        raise GeoXato("CHIZMA trapetsiya: a (katta asos), b (kichik asos) va h (balandlik) kerak")
    if a <= b:
        raise GeoXato("CHIZMA trapetsiya: a katta asos bo'lsin (a > b)")
    togri = tur == "togri"; x = 0.0 if togri else (a - b) / 2
    yon_h = math.hypot(x, h) if not togri else None
    if yon is not None:
        if togri:
            kutilgan = math.hypot(a - b, h)       # qiya yon (BC)
        else:
            kutilgan = yon_h
        if not _mos(yon, kutilgan):
            raise GeoXato(f"CHIZMA trapetsiya: sonlar zid — yon={yozuv(yon)} berilgan, qolganlardan {yozuv(kutilgan)} chiqadi")
    A, B, C, D = (0.0, 0.0), (a, 0.0), (x + b, h), (x, h); nq = {"A": A, "B": B, "C": C, "D": D, "E": (x, 0.0)}
    kes = [_kes("A", "B", yozuv(a)), _kes("B", "C", yozuv(yon) if (yon is not None and not togri) or (yon is not None and togri) else None), _kes("C", "D", yozuv(b)), _kes("D", "A", yozuv(yon) if (yon is not None and not togri) else None), _kes("D", "E", yozuv(h), True)]
    if togri:      # D A ning ustida: balandlik = DA, E nuqtasi A bilan bir joyda — ko'rsatilmaydi
        kes = [k for k in kes if not (k["a"] == "D" and k["b"] == "E")]; kes[3] = _kes("D", "A", yozuv(h), False)
        bur = [{"uch": "A", "a": "B", "b": "D", "tur": "togri", "yozuv": None}, {"uch": "D", "a": "A", "b": "C", "tur": "togri", "yozuv": None}]
        return _asos("trapetsiya", nq, kes, bur, korinadigan=["A", "B", "C", "D"])
    bur = [{"uch": "E", "a": "D", "b": "B", "tur": "togri", "yozuv": None}]
    return _asos("trapetsiya", nq, kes, bur)


def aylana(p):
    r, v = p.get("r"), p.get("vatar")
    if not r:
        raise GeoXato("CHIZMA aylana: radius (r) kerak")
    O = (0.0, 0.0); nq = {"O": O}; kes = []; yoz = []; bur = []
    dum = [{"c": [0.0, 0.0], "r": r, "yozuv": None}]
    nq["M"] = (r, 0.0); kes.append(_kes("O", "M", "r=" + yozuv(r)))
    if v is not None:
        if v >= 2 * r:
            raise GeoXato("CHIZMA aylana: vatar diametrdan (2r) kichik bo'lsin")
        d = math.sqrt(r * r - (v / 2) ** 2); nq["P"] = (-d, v / 2); nq["Q"] = (-d, -v / 2); nq["H"] = (-d, 0.0)
        kes += [_kes("P", "Q", yozuv(v)), _kes("O", "H", None, True)]; bur.append({"uch": "H", "a": "O", "b": "P", "tur": "togri", "yozuv": None})
    return _asos("aylana", nq, kes, bur, dum, yoz, korinadigan=[k for k in nq if k != "M"])


MAKROLAR = {"romb": romb, "uchburchak": uchburchak, "togri_uchburchak": togri_uchburchak, "parallelogramm": parallelogramm, "trapetsiya": trapetsiya, "aylana": aylana}


def coz(arg):
    """«romb a=5 d1=6 d2=8» → shakl (dict). Xato bo'lsa GeoXato."""
    nom, p = parse(arg)
    f = MAKROLAR[nom](p)
    f["arg"] = " ".join((arg or "").split())
    return f
