"""Taqdimot sozlamalari: foydalanuvchi tanlaydigan dizayn, shrift, rang, ramka, animatsiya va qismlar.

KATALOG — saytdagi «Sozlamalar» oynasi shu ro'yxatdan chiziladi (guruh, nom, izoh, variantlar). `toza()` brauzerdan
kelgan qiymatlarni tekshiradi va faqat «avto»dan farqlilarini qoldiradi. `yasash.yasa(..., sozlama=...)` ularni
qo'llaydi: uslubga (rang, fon), o'lchovga (shrift, o'lcham), slaydlarga (ramka, animatsiya, pastki panel)
va reja tuzishga (qaysi qismlar bo'lsin).
"""
from __future__ import annotations

import re

from . import olchov
from .uslub import aralash, och, toq, yorqinlik

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

SHRIFT_VARIANTLARI = [["", "Avto (uslubniki)"]] + [[k, v[0]] for k, v in olchov.SHRIFT_KATALOG.items()]
OLCHAMLAR = {"kichik": 0.9, "katta": 1.12, "juda_katta": 1.25}
TEZLIK = {"sekin": 1.5, "tez": 0.65}
FON_YORUG = ["aurora", "mesh", "minimal", "qogoz", "jurnal", "daftar", "barg", "tekis", "lenta", "tolqin", "yoy"]
FON_QORONGI = ["glow", "stars", "tekis", "chalk", "qirra", "nur", "panel"]
FON_NOMI = {"aurora": "Yumshoq dog‘lar", "mesh": "Rangli tuman", "minimal": "Minimal (chap chiziq)", "qogoz": "Qog‘oz",
            "jurnal": "Jurnal (yon tasma)", "daftar": "Katakli daftar", "barg": "Barglar", "tekis": "Tekis gradient",
            "lenta": "Rangli lenta", "tolqin": "To‘lqin", "yoy": "Yoylar", "qirra": "Qirralar (qorong‘i)", "nur": "Chiroq nuri (qorong‘i)",
            "panel": "Raqamli panel (qorong‘i)", "glow": "Nurli (qorong‘i)", "stars": "Yulduzli (qorong‘i)", "chalk": "Bo‘r doska (qorong‘i)"}
QISMLAR = [["reja", "Reja slaydi (mundarija)"], ["takrorlash", "O‘tgan mavzuni takrorlash"], ["muammo", "Muammoli savol bilan boshlash"],
           ["tarix", "Tarixiy ma’lumot"], ["xatolar", "Ko‘p uchraydigan xatolar"], ["metodika", "Metodika (o‘qituvchi uchun)"],
           ["xulosa", "Xulosa"], ["test", "Test savollari"], ["yakun", "Uy vazifasi va keyingi dars"], ["adabiyot", "Adabiyotlar"]]
ROYXAT_NOMI = [["kartalar", "Kartalar"], ["ikonli", "Belgili qatorlar"], ["raqamli", "Katta raqamlar"], ["zinapoya", "Zinapoya"],
               ["piramida", "Piramida"], ["vaqt", "Vaqt chizig‘i"], ["sikl", "Aylana (sikl)"], ["strelka", "Strelkalar"],
               ["markaz", "Markaz va bandlar"], ["zanjir", "Zanjir"]]

# Saytdagi sozlamalar oynasi (tartib bilan). tur: tanlov | rang | matn | qismlar
KATALOG = [
    {"guruh": "Ranglar va fon", "sozlamalar": [
        {"kalit": "asosiy_rang", "nom": "Asosiy rang", "tur": "rang",
         "izoh": "Sarlavha, chiziq va asosiy kartalar shu rangda. Juda och yoki juda to‘q bo‘lsa, o‘qilishi uchun biroz moslanadi.",
         "tayyor": ["#1D4E89", "#B5173A", "#1B7F5B", "#6A4C93", "#D9530F", "#0077B6", "#9D0208", "#21867A", "#C2185B", "#37474F"]},
        {"kalit": "matn_rangi", "nom": "Matn rangi", "tur": "rang",
         "izoh": "Asosiy yozuvlar rangi. Fonga nisbatan o‘qilmaydigan rang tanlansa, uslubniki qoladi.",
         "tayyor": ["#111111", "#333333", "#1B2A4A", "#3B2A1A", "#1F3B2D", "#FFFFFF", "#F1F5F9"]},
        {"kalit": "fon", "nom": "Fon", "tur": "tanlov", "izoh": "Slayd orqa foni. «Qorong‘i» deb yozilganlari faqat qorong‘i uslublarda ishlaydi.",
         "variantlar": [["", "Avto (uslubniki)"]] + [[k, FON_NOMI[k]] for k in FON_YORUG + [f for f in FON_QORONGI if f != "tekis"]]},
        {"kalit": "bezak", "nom": "Fon bezagi", "tur": "tanlov", "izoh": "Fanga mos mayda bezaklar (formulalar, barglar, atomlar…) fonda.",
         "variantlar": [["", "Bor"], ["yoq", "Yo‘q"]]},
    ]},
    {"guruh": "Shrift", "sozlamalar": [
        {"kalit": "shrift_sarlavha", "nom": "Sarlavha shrifti", "tur": "tanlov", "izoh": "Slayd sarlavhalari va katta raqamlar.",
         "variantlar": SHRIFT_VARIANTLARI},
        {"kalit": "shrift_matn", "nom": "Matn shrifti", "tur": "tanlov", "izoh": "Kartalar, ro‘yxatlar va izohlar matni.",
         "variantlar": SHRIFT_VARIANTLARI},
        {"kalit": "olcham_sarlavha", "nom": "Sarlavha o‘lchami", "tur": "tanlov", "izoh": "Joy yetmasa, dvigatel baribir sig‘diradi.",
         "variantlar": [["kichik", "Kichikroq"], ["", "O‘rta"], ["katta", "Katta"], ["juda_katta", "Juda katta"]]},
        {"kalit": "olcham_matn", "nom": "Matn o‘lchami", "tur": "tanlov",
         "izoh": "Katta zalda ko‘rsatish uchun «Katta». Matn ko‘p bo‘lsa, sig‘ishi uchun kichrayadi.",
         "variantlar": [["kichik", "Kichikroq"], ["", "O‘rta"], ["katta", "Katta"], ["juda_katta", "Juda katta"]]},
    ]},
    {"guruh": "Sahifa", "sozlamalar": [
        {"kalit": "ramka", "nom": "Ramka", "tur": "tanlov", "izoh": "Har slayd chetidagi ramka asosiy rangda.",
         "variantlar": [["", "Yo‘q"], ["ingichka", "Ingichka chiziq"], ["qalin", "Qalin"], ["ikki", "Qo‘sh chiziq"],
                        ["burchak", "Burchak bezaklari"], ["chap_tasma", "Chapda tasma"], ["pastki_tasma", "Pastda tasma"]]},
        {"kalit": "sahifa", "nom": "Oq sahifa-karta", "tur": "tanlov",
         "izoh": "Mazmun fon ustidagi katta oq karta ichida turadi (faqat yorug‘ uslublarda).",
         "variantlar": [["", "Avto"], ["karta", "Bor"], ["oddiy", "Yo‘q"]]},
        {"kalit": "karta", "nom": "Ta’rif va qoida kartalari", "tur": "tanlov",
         "izoh": "«Avto» — har slaydda boshqacha. Bittasini tanlasangiz — hamma joyda shu.",
         "variantlar": [["", "Avto (aralash)"], ["karta", "Oddiy karta"], ["chiziq", "Chap chiziqli"], ["blok", "Rangli blok"],
                        ["qogoz", "Sariq qog‘oz"]]},
        {"kalit": "royxat", "nom": "Ro‘yxatlar ko‘rinishi", "tur": "tanlov",
         "izoh": "«Avto» — mazmunga mos 8 xil ko‘rinish aralash. Bittasini tanlasangiz — sig‘adigan joyda shu chiqadi.",
         "variantlar": [["", "Avto (aralash)"]] + ROYXAT_NOMI},
        {"kalit": "pastki", "nom": "Pastki panel", "tur": "tanlov", "izoh": "Slayd pastidagi bo‘lim nuqtalari, bo‘lim nomi va sahifa raqami.",
         "variantlar": [["", "To‘liq"], ["raqam", "Faqat sahifa raqami"], ["yoq", "Yo‘q"]]},
        {"kalit": "muallif", "nom": "Muallif / muassasa yozuvi", "tur": "matn", "max": 80,
         "izoh": "Titul slaydida va har slayd pastida chiqadi. Masalan: A. Ro‘ziqulov · SamDPI", "namuna": "A. Ro‘ziqulov · SamDPI"},
    ]},
    {"guruh": "Animatsiya", "sozlamalar": [
        {"kalit": "anim_tezlik", "nom": "Tezligi", "tur": "tanlov", "izoh": "Elementlar qanchalik tez chiqadi.",
         "variantlar": [["sekin", "Sekin"], ["", "O‘rta"], ["tez", "Tez"]]},
        {"kalit": "chiqish", "nom": "Chiqish tartibi", "tur": "tanlov",
         "izoh": "«Bosganda» — har bosishda keyingi qism chiqadi (dars uchun). «O‘zi» — slayd ochilishi bilan hammasi ketma-ket chiqadi.",
         "variantlar": [["", "Bosganda (qadam-baqadam)"], ["birga", "O‘zi ketma-ket"], ["yoq", "Animatsiyasiz"]]},
        {"kalit": "otish", "nom": "Slayd almashishi", "tur": "tanlov", "izoh": "PowerPoint’da bir slayddan keyingisiga o‘tish effekti.",
         "variantlar": [["", "Silliq (fade)"], ["push", "Surilish"], ["wipe", "Artilish"], ["none", "Effektsiz"]]},
    ]},
    {"guruh": "Qaysi qismlar bo‘lsin", "sozlamalar": [
        {"kalit": "qismlar", "nom": "Qismlar", "tur": "qismlar", "variantlar": QISMLAR,
         "izoh": "Belgini olib tashlasangiz, o‘sha slayd taqdimotda chiqmaydi (AI ham uni yozmaydi)."},
    ]},
]

_TANLOV = {s["kalit"]: {v[0] for v in s["variantlar"]} for g in KATALOG for s in g["sozlamalar"] if s["tur"] == "tanlov"}
_QISM_KALIT = {k for k, _ in QISMLAR}


def toza(z) -> dict:
    """Brauzerdan kelgan sozlamalar → tekshirilgan, faqat «avto»dan farqli qiymatlar."""
    if not isinstance(z, dict):
        return {}
    out = {}
    for k, ruxsat in _TANLOV.items():
        v = z.get(k)
        if isinstance(v, str) and v and v in ruxsat:
            out[k] = v
    for k in ("asosiy_rang", "matn_rangi"):
        v = z.get(k)
        if isinstance(v, str) and HEX.match(v):
            out[k] = v.upper()
    m = z.get("muallif")
    if isinstance(m, str) and m.strip():
        out["muallif"] = re.sub(r"\s+", " ", m).strip()[:80]
    q = z.get("qismlar")
    if isinstance(q, dict):
        ochiq = sorted(k for k, v in q.items() if k in _QISM_KALIT and v is False)
        if ochiq:
            out["qismlar"] = {k: False for k in ochiq}
    return out


def qism_bormi(z: dict, kalit: str) -> bool:
    return (z.get("qismlar") or {}).get(kalit, True) is not False


def miyadan_olib_tashla(m: dict, z: dict) -> dict:
    """O'chirilgan qismlarni normallashgan miyadan olib tashlaydi (reja_tuz ularni chiqarmaydi)."""
    q = z.get("qismlar") or {}
    if not q:
        return m
    if q.get("adabiyot") is False:
        m["adabiyotlar"] = {k: [] for k in m["adabiyotlar"]}
    if q.get("takrorlash") is False:
        m["takrorlash"] = dict(m["takrorlash"], savollar=[])
    if q.get("muammo") is False:
        m["muammo"] = dict(m["muammo"], masalalar=[], goya="")
    if q.get("tarix") is False:
        m["tarix"] = dict(m["tarix"], voqealar=[])
    if q.get("xatolar") is False:
        m["xatolar"] = []
    if q.get("metodika") is False:
        m["metodika"] = dict(m["metodika"], bosqichlar=[], kartalar=[])
    if q.get("xulosa") is False:
        m["xulosa"] = {k: ([] if isinstance(v, list) else "") for k, v in m["xulosa"].items()}
    if q.get("test") is False:
        m["test"] = []
    if q.get("yakun") is False:
        m["nazorat"], m["mustaqil_ish"] = [], []
        m["keyingi"] = {k: ([] if isinstance(v, list) else "") for k, v in m["keyingi"].items()}
    return m


# ------------------------------------------------------------------ ranglar
def kontrast(a: str, b: str) -> float:
    la, lb = yorqinlik(a), yorqinlik(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _moslash(rang: str, fon: str, qorongi: bool, kerak: float) -> str:
    """Rang fonda o'qilishi uchun yetarlicha to'q (yorug' fonda) yoki och (qorong'ida) bo'lguncha suriladi."""
    c = rang
    for _ in range(12):
        if kontrast(c, fon) >= kerak:
            return c
        c = och(c, 0.18) if qorongi else toq(c, 0.15)
    return c


def uslubga(u, z: dict) -> list:
    """Rang va fon sozlamalarini Uslub obyektiga qo'llaydi. Qaytaradi: foydalanuvchiga ogohlantirishlar."""
    og = []
    fon0 = u.bg[0]
    if z.get("fon"):
        mos = FON_QORONGI if u.qorongi else FON_YORUG
        if z["fon"] in mos:
            u.fon_turi = z["fon"]
        else:
            og.append(f"«{FON_NOMI.get(z['fon'], z['fon'])}» foni bu uslubga mos emas ({'qorong‘i' if u.qorongi else 'yorug‘'} uslub) — uslub foni qoldi.")
    if z.get("asosiy_rang"):
        c = _moslash(z["asosiy_rang"], fon0, u.qorongi, 3.0)
        if c != z["asosiy_rang"]:
            og.append("Asosiy rang fonda o‘qilishi uchun biroz " + ("ochartirildi." if u.qorongi else "to‘qlashtirildi."))
        if u.glow == u.acc[0]:
            u.glow = c
        u.acc[0] = c
    if z.get("matn_rangi"):
        if kontrast(z["matn_rangi"], fon0) >= 4.5:
            u.ink = z["matn_rangi"]
        else:
            og.append("Tanlangan matn rangi bu fonda yaxshi o‘qilmaydi — uslub rangi qoldi.")
    return og


def fon_kodi(u, z: dict) -> str:
    """Fon rasmi kodi: uslub kodi + almashtirishlar (!fonturi, !rRRGGBB). fon_rasm() shuni o'qiydi."""
    kod = u.kod
    if z.get("fon") and u.fon_turi == z["fon"]:
        kod += "!" + u.fon_turi
    if z.get("asosiy_rang"):
        kod += "!r" + u.acc[0].lstrip("#").lower()
    return kod


def fon_kodini_och(kod: str):
    """"oila.palitra.v!qogoz!r1d4e89" → ("oila.palitra.v", "qogoz", "#1D4E89")."""
    asos, *qism = kod.split("!")
    fon, rang = None, None
    for q in qism:
        if re.fullmatch(r"r[0-9a-f]{6}", q):
            rang = "#" + q[1:].upper()
        elif q in FON_YORUG or q in FON_QORONGI:
            fon = q
    return asos, fon, rang


# ------------------------------------------------------------------ shrift va o'lcham
def shrift_sozlamasi(u, z: dict):
    """(xarita, olcham, sahna_shriftlari) — olchov.sozlama_qoy() uchun. Sarlavha alohida «head» kaliti bilan."""
    if not any(z.get(k) for k in ("shrift_sarlavha", "shrift_matn", "olcham_sarlavha", "olcham_matn")):
        return None, None, {}
    xarita = {}
    oila_head = "cambria" if u.head == "serif" else "calibri"
    xarita["head"] = z.get("shrift_sarlavha") or oila_head
    u.head = "head"
    if z.get("shrift_matn"):
        xarita["sans"] = z["shrift_matn"]
    olcham = {}
    if z.get("olcham_sarlavha"):
        olcham["head"] = OLCHAMLAR[z["olcham_sarlavha"]]
    if z.get("olcham_matn"):
        olcham["matn"] = OLCHAMLAR[z["olcham_matn"]]
    sahna_sh = {k: {"face": olchov.SHRIFT_KATALOG[v][1], "css": olchov.SHRIFT_KATALOG[v][4]} for k, v in xarita.items()}
    return xarita, olcham or None, sahna_sh


# ------------------------------------------------------------------ slaydga
def ramka_chiz(s, u, tur: str):
    W, H = 1280, 720
    c = u.acc[0]
    if tur == "ingichka":
        s.rect(16, 16, W - 32, H - 32, fill=None, line=c, lw=1.6, nm="!!ramka")
    elif tur == "qalin":
        s.rect(9, 9, W - 18, H - 18, fill=None, line=c, lw=7, nm="!!ramka")
    elif tur == "ikki":
        s.rect(10, 10, W - 20, H - 20, fill=None, line=c, lw=3, nm="!!ramka")
        s.rect(19, 19, W - 38, H - 38, fill=None, line=c, lw=1, op=0.7, nm="!!ramka2")
    elif tur == "burchak":
        L, d, lw = 74, 14, 5
        for x0, y0, sx, sy in ((d, d, 1, 1), (W - d, d, -1, 1), (d, H - d, 1, -1), (W - d, H - d, -1, -1)):
            s.line(x0, y0, x0 + sx * L, y0, color=c, lw=lw, nm="!!ramka")
            s.line(x0, y0, x0, y0 + sy * L, color=c, lw=lw, nm="!!ramka")
    elif tur == "chap_tasma":
        s.rect(0, 0, 12, H, fill=c, nm="!!ramka")
    elif tur == "pastki_tasma":
        s.rect(0, H - 8, W, 8, fill=c, nm="!!ramka")


def slaydga(sd: dict, z: dict):
    """Tayyor slayd JSON'iga animatsiya sozlamalari (tezlik, chiqish tartibi) va o'tish effekti."""
    f = TEZLIK.get(z.get("anim_tezlik"), 1.0)
    chiqish = z.get("chiqish")
    if z.get("otish"):
        sd["otish"] = z["otish"]
    if f == 1.0 and not chiqish:
        return
    qoldi = []
    for el in sd["els"]:
        a = el.get("a")
        if a and not a.get("tr"):
            if chiqish == "yoq":
                el.pop("a", None)
            else:
                if chiqish == "birga":
                    s_ = int(a.get("s", 0) or 0)
                    a["dl"] = int(a.get("dl", 0)) + s_ * 450
                    a["s"] = 0
                a["ms"] = int(int(a.get("ms", 500)) * f)
                a["dl"] = int(int(a.get("dl", 0)) * f)
        elif a and a.get("tr"):
            a["ms"] = int(int(a.get("ms", 500)) * f)
        qoldi.append(el)
    sd["els"] = qoldi
    if chiqish in ("birga", "yoq"):
        sd["qadam"] = 0


def katalog() -> list:
    return KATALOG
