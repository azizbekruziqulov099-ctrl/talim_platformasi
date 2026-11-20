"""Kutubxona rasmlarini miyaga moslash.

1) Miyadagi noma'lum rasm kalitini (AI o'ylab topgan) kutubxonadagi eng yaqin rasmga almashtiradi;
   topilmasa — slaydda bo'sh ramka chiqmasin deb olib tashlaydi va «yo'q rasmlar» ro'yxatiga yozadi.
2) Rasmsiz slaydga, matni rasm mavzusiga aniq mos kelsa, kutubxonadan rasm qo'yadi (ehtiyotkor chegara).
3) Titul slaydiga mavzuga mos rasm tanlaydi.

Faqat illyustratsiyalar (tur "rasm") avtomatik qo'yiladi; chizmalar — aniq bog'langan joyda (kutubxona.py).
"""
from __future__ import annotations

import math
import re
from functools import lru_cache

from . import rasmlar

_APO = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'", "−": "-", "–": "-"})
_SOZ = re.compile(r"[a-z']+")
_QOSHIMCHA = ("larining", "laridagi", "laridan", "lariga", "larini", "lari", "lar", "ning", "dagi", "dan", "ga", "da", "ni",
              "ka", "qa", "si", "imiz", "ingiz", "lik", "li", "chi")
_TOXTA = {
    "va", "bilan", "uchun", "bir", "ikki", "uch", "har", "shu", "bu", "ham", "emas", "yoki", "kabi", "orqali", "qanday", "nima",
    "nimani", "nega", "qaysi", "qilib", "bo'ladi", "bo'lgan", "bo'lsa", "bo'lib", "deb", "edi", "esa", "endi", "yana", "faqat",
    "barcha", "hamma", "katta", "kichik", "yangi", "turli", "asosiy", "misol", "masala", "rasm", "tasvir", "model", "sxema",
    "mavzu", "dars", "slayd", "javob", "savol", "topshiriq", "jadval", "ta'rif", "qoida", "izoh", "muhim", "diqqat", "son",
    "sonlar", "soni", "tartib", "holat", "usul", "xil", "tur", "turi", "qism", "qismi", "o'z", "o'zi", "biz", "siz", "ular",
    "bor", "yo'q", "kerak", "mumkin", "ko'p", "oz",
}


def _ildiz(soz: str) -> str:
    s = soz  # o' / g' saqlanadi: "to'rt" (4) ≠ "tort" (pishiriq)
    for _ in range(2):
        for q in _QOSHIMCHA:
            if s.endswith(q) and len(s) - len(q) >= 4:
                s = s[: -len(q)]
                break
    out, n = "", 0
    for ch in s:  # 6 ta harf (apostrof hisobga olinmaydi): o'qituvchi → o'qituv
        out += ch
        if ch != "'":
            n += 1
            if n >= 6:
                break
    return out


def tokenlar(text: str) -> set:
    out = set()
    for t in _SOZ.findall((text or "").lower().translate(_APO)):
        t = t.strip("'")
        if len(t) >= 3 and t not in _TOXTA:
            out.add(_ildiz(t))
    return out


_YAGONA: set = set()  # faqat bitta rasmda uchraydigan so'zlar (dutor, mitoz, protsessor)
_FAN_GURUH = {"tabiiy": {"biolog", "fizika", "kimyo", "geogra", "astron", "tabiiy"}, "biolog": {"tabiiy"}, "fizika": {"tabiiy", "astron"},
              "kimyo": {"tabiiy"}, "geogra": {"tabiiy"}, "astron": {"fizika", "tabiiy"}, "huquq": {"tarbiy", "iqtiso"},
              "iqtiso": {"tarbiy", "huquq"}, "tarbiy": {"huquq", "iqtiso", "ma'nav"}, "adabiy": {"ona"}, "o'qish": {"ona", "adabiy"},
              "pedago": {"psixol", "bakala"}, "psixol": {"pedago", "bakala"}, "texnol": {"chizma"}, "chizma": {"texnol"}}


def _fan_guruh(fan: str) -> set:
    t = tokenlar(fan)
    for x in list(t):
        t |= _FAN_GURUH.get(x, set())
    if t & {"ingliz", "rus", "nemis", "fransu", "ispan", "koreys", "turk", "arab", "xitoy", "chet", "tili", "til"}:
        t |= {"tillar"}
    return t - {"fanlar", "fanl", "masala"}


def _na(t: set) -> frozenset:
    return frozenset(x.replace("'", "") for x in t)


_ARTIKL = re.compile(r"^(the|a|an|der|die|das|le|la|les|l'|el|los|las|un|une)\s", re.I)
_RK_PREFIKS = re.compile(r"^(d_)?((m|mat|fiz|kim|bio|xb|y|v|i)-|(en|mt|am)[0-9]+-(u[0-9]+-|s[0-9]+-)?)")
_RK_FAN = {"matematika": "matematika", "fizika": "fizika", "kimyo": "kimyo", "biologiya": "biologiya",
           "xalqaro baholash": "matematika tabiiy", "tillar": "tillar", "bog'cha": "bog'cha"}
_TIL_FANLAR = {"tillar", "ingliz", "rus", "nemis", "fransu", "ispan", "koreys", "turk", "arab", "xitoy", "ona", "o'qish",
               "adabiy", "bog'cha", "tarbiy"}


def _kutubxona_qatorlari():
    """Saytning umumiy rasm kutubxonasi (≈6000 illyustratsiya) — tanlash indeksiga."""
    out = []
    for r in rasmlar.kutubxona_yozuvlari():
        i = r.get("id") or ""
        if not i or i.startswith("d_v-"):  # javob varianti rasmlari — faqat aniq kalit bilan
            continue
        sozlar = [_ARTIKL.sub("", s.strip()) for s in r.get("sozlar") or [] if isinstance(s, str)]
        slug = _RK_PREFIKS.sub("", i).replace("-", " ").replace("_", " ")
        asosiy = tokenlar(slug)
        tok = set(asosiy)
        ismlar = [_na(asosiy)] if asosiy else []
        for s in sozlar:
            t = tokenlar(s)
            tok |= t
            if t and len(s.split()) <= 3:
                asosiy |= t
                ismlar.append(_na(t))
        if not asosiy:
            continue
        turkum = (r.get("turkum") or "").lower()
        fanlar = " ".join(v for k2, v in _RK_FAN.items() if k2 in turkum)
        ft = tokenlar(fanlar)
        if "tillar" in ft or "bog'cha" in ft:
            ft |= _TIL_FANLAR
        ot = bool(any(_ARTIKL.match(s) for s in sozlar) or i.startswith(("d_mat", "d_fiz", "d_kim", "d_bio", "d_xb", "d_y-"))
                  or not i.startswith("d_"))
        out.append({"kalit": i, "tur": "rasm", "nom": rasmlar.kutubxona_nomi(r), "fan": fanlar, "asosiy": asosiy, "tok": tok,
                    "fan_tok": ft, "rk": True, "ot": ot, "past": bool(r.get("past")), "ismlar": ismlar})
    return out


@lru_cache(maxsize=1)
def _kutubxona_cache():
    try:
        return _kutubxona_qatorlari()
    except Exception:
        return []


@lru_cache(maxsize=2)
def _indeks(_mt: float):
    rows = []
    for r in rasmlar.papka_reestri():
        k = r.get("kalit") or ""
        if not k:
            continue
        kt = tokenlar(k.replace("_", " "))
        nt = tokenlar(r.get("nom") or "")
        # kalitda apostrof yo'q (oqituvchi) — nomdagi to'g'ri yozuvini olamiz (o'qituvchi)
        asosiy = {t for t in nt if t.replace("'", "") in kt} | {t for t in kt if not any(x.replace("'", "") == t for x in nt)}
        hammasi = asosiy | nt | tokenlar(r.get("izoh") or "" if r.get("tur") == "rasm" else "")
        rows.append({"kalit": k, "tur": r.get("tur") or "rasm", "nom": r.get("nom") or "", "fan": r.get("fan") or "",
                     "asosiy": asosiy, "tok": hammasi, "fan_tok": _fan_guruh(r.get("fan") or ""), "ismlar": [_na(asosiy)]})
    ichki = {r["kalit"] for r in rows}
    rows += [r for r in _kutubxona_cache() if r["kalit"] not in ichki]
    n = max(1, len(rows))
    df = {}
    for r in rows:
        for t in r["tok"]:
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log((n + 1) / c) for t, c in df.items()}
    rdf = {}
    for r in rows:
        if r["tur"] == "rasm":
            for t in r["asosiy"]:
                rdf[t] = rdf.get(t, 0) + 1
    _YAGONA.clear()
    _YAGONA.update(t for t, c in rdf.items() if c == 1)
    return rows, idf


def indeks():
    import os
    p = os.path.join(rasmlar.PAPKA, "reestr.json")
    return _indeks(os.path.getmtime(p) if os.path.isfile(p) else 0.0)


def _ball(q: set, r: dict, idf: dict):
    """(ball, mos so'zlar soni, asosiy (kalitdagi) so'zlar soni)."""
    umumiy = q & r["tok"]
    asos = q & r["asosiy"]
    if not umumiy or not asos:
        return 0.0, 0, 0
    b = sum(idf.get(t, 1.0) * (1.6 if t in r["asosiy"] else 1.0) for t in umumiy)
    return b, len(umumiy), len(asos)


@lru_cache(maxsize=1)
def _qisqa_sozlar():
    """2 harfli so'zlar (ot, it, uy, oy) — tokenlarga kirmaydi; sayt kutubxonasida aynan shu nomli rasm."""
    out = {}
    for r in _kutubxona_cache():
        for s in rasmlar.kutubxona_yozuvlari_lugat().get(r["kalit"], []):
            w = s.strip().lower().translate(_APO)
            if len(w) == 2 and w.isalpha():
                out.setdefault(w, []).append(r)
    return {w: sorted(v, key=lambda r: (r.get("past", False), len(r["asosiy"])))[0]["kalit"] for w, v in out.items()}


def buyum_rasmi(matn: str, band: set = frozenset()):
    """Aniq narsa nomi (lug'at so'zi, jihoz, cholg'u) uchun rasm: nomdagi so'z rasmning asosiy so'zi bo'lsa va
    faqat shu rasmga xos bo'lsa (olma → olma_savat, kolba → kolba_konus). Fan tekshirilmaydi."""
    rows, idf = indeks()
    q = tokenlar(matn)
    if not q:
        w = (matn or "").strip().lower().translate(_APO).strip(".,!?")
        k = _qisqa_sozlar().get(w) if len(w) == 2 else None
        return k if k and k not in band else None
    qn = _na(q)
    eng, kal = 0.0, None
    for r in rows:
        if r["tur"] != "rasm" or r["kalit"] in band:
            continue
        mos = q & r["asosiy"]
        if not mos:
            continue
        yagona = bool(mos & _YAGONA)
        # nomlaridan birining hamma so'zi bor (baraban → baraban, tovush_baraban emas; olma → apple/olma)
        toliq = any(s and s <= qn for s in r["ismlar"])
        b = (sum(idf.get(t, 1.0) for t in mos) + (2.0 if yagona else 0) + (3.0 if toliq else 0) - 0.15 * min(len(r["asosiy"]), 6)
             - (0.3 if r.get("past") else 0))
        if (yagona or toliq or len(mos) >= 2) and b > eng:
            eng, kal = b, r["kalit"]
    return kal


def eng_mos(matn: str, tur: str = "rasm", chegara: float = 6.5, band: set = frozenset(), fan: str = "", kamida: int = 2,
            rk: bool = True):
    """Matnga eng mos kutubxona rasmi: (kalit, ball) yoki (None, 0).

    Bitta so'z mos kelishi yetmaydi (balandlik ≠ balandlikka sakrash): kamida `kamida` ta so'z, ulardan biri
    rasmning asosiy (kalitdagi) so'zi. Fan mos kelmasa talab qattiqroq (yana bitta so'z va yuqori ball).
    """
    rows, idf = indeks()
    q = tokenlar(matn)
    if not q:
        return None, 0.0
    ft = _fan_guruh(fan)
    eng, kal = 0.0, None
    for r in rows:
        if tur and r["tur"] != tur or r["kalit"] in band or (r.get("rk") and not rk):
            continue
        b, n, na = _ball(q, r, idf)
        if not b:
            continue
        fan_mos = bool(ft and ft & r["fan_tok"])
        if fan_mos:
            # ikki so'z, yoki faqat shu rasmga xos bitta asosiy so'z (dutor, mitoz)
            yagona = q & r["asosiy"] & _YAGONA
            if yagona and r.get("rk"):
                # sayt kutubxonasida bitta so'z yetadi faqat rasm nomining o'zi shu so'z bo'lsa (son o'qi → o'qi; «tanlash» emas)
                yagona = {t for t in yagona if any(s == _na({t}) for s in r["ismlar"])}
            ok = (n >= kamida and b >= chegara) or bool(yagona)
        else:
            ok = n >= kamida + 1 and na >= 1 and b >= chegara * 1.4
        if ok and b > eng:
            eng, kal = b, r["kalit"]
    return (kal, eng) if kal else (None, 0.0)


def katalog(matn: str, fan: str = "", n: int = 60):
    """AI uchun: mavzuga eng yaqin n ta rasm (kalit — nom). Fan mos kelsa ham qo'shiladi."""
    rows, idf = indeks()
    q = tokenlar(matn)
    ft = _fan_guruh(fan)
    ballar = []
    for r in rows:
        if r["tur"] != "rasm":
            continue
        b = sum(idf.get(t, 1.0) * (1.3 if t in r["asosiy"] else 1.0) for t in q & r["tok"])
        fan_mos = bool(ft and ft & r["fan_tok"])
        if r.get("rk"):
            # sayt kutubxonasi katta: faqat so'zi mos kelganlari (fan faqat ustunlik beradi)
            if b <= 0:
                continue
            b += 2.0 if fan_mos else 0
            b -= 0.4 if r.get("past") else 0
        elif fan_mos:
            b += 2.5
        if b > 0:
            ballar.append((b, r["kalit"], r["nom"]))
    ballar.sort(reverse=True)
    return [(k, nom) for _, k, nom in ballar[:n]]


# ------------------------------------------------------------------ miyaga qo'llash
_MATNLI = {"matn", "tarif", "qoida", "teorema", "hayotiy", "savol", "misol", "masala"}


def _el_matni(e: dict) -> str:
    qism = []
    for k in ("sarlavha", "matn", "shart", "izoh", "javob"):
        v = e.get(k)
        if isinstance(v, str):
            qism.append(v)
    for b in e.get("bandlar") or []:
        if isinstance(b, dict) and isinstance(b.get("matn"), str):
            qism.append(b["matn"])
    for q in e.get("qadamlar") or []:
        if isinstance(q, str):
            qism.append(q)
    return " ".join(qism)


def _kichik(meta: dict) -> bool:
    d = (meta.get("daraja") or "").lower()
    s = (meta.get("sinf") or "").lower()
    return d == "bogcha" or "bog" in s or any(re.search(rf"(^|\D){n}\s*-?\s*sinf", s) for n in (1, 2, 3, 4))


def _royxat_sozlari(matn: str) -> list:
    """Matndagi sanab o'tilgan narsalar: «Sigir, qo‘y, ot va echki — ...» → [Sigir, qo‘y, ot, echki]."""
    out = []
    toza = (matn or "").replace("**", "").replace("==", "")
    for bo in re.split(r"[.;:!?—–()\n]", toza):
        parts = [p.strip(" ,") for p in re.split(r",|\bva\b|\band\b|\bи\b", bo) if p.strip(" ,")]
        if len(parts) < 3:
            continue
        if any(len(p.split()) > 2 for p in parts[:-1]):
            continue
        out += parts if len(parts[-1].split()) <= 2 else parts[:-1]
    return out[:6]


def boyit(m: dict, avto: bool = True) -> dict:
    """Normallashtirilgan miyani joyida o'zgartiradi. Hisobot qaytaradi."""
    hisobot = {"ishlatilgan": [], "almashtirildi": [], "qoshildi": [], "yoq": []}
    rows, _ = indeks()
    if not rows:
        return hisobot
    tavsif = {r.get("kalit"): r for r in (m.get("rasmlar") or []) if isinstance(r, dict) and r.get("kalit")}
    fan = (m.get("meta") or {}).get("fan") or ""
    band = set()

    def tuzat(kalit, kontekst):
        """Mavjud bo'lsa o'zi; bo'lmasa eng yaqini; u ham bo'lmasa None."""
        if not kalit:
            return None
        if rasmlar.bor(kalit):
            return kalit
        t = tavsif.get(kalit) or {}
        matn = f"{kalit.replace('_', ' ')} {t.get('tavsif') or ''} {kontekst}"
        yangi, _b = eng_mos(matn, tur="", chegara=7.0, fan=fan or t.get("tavsif") or "")
        if yangi:
            hisobot["almashtirildi"].append([kalit, yangi])
            return yangi
        if kalit not in [y["kalit"] for y in hisobot["yoq"]]:
            hisobot["yoq"].append({"kalit": kalit, "tavsif": t.get("tavsif") or "", "prompt": t.get("prompt") or ""})
        return None

    # 1) bor kalitlarni tekshirish / almashtirish
    meta = m.get("meta") or {}
    if meta.get("rasm"):
        meta["rasm"] = tuzat(meta["rasm"], meta.get("mavzu") or "") or ""
    for blok in ("tarix",):
        for v in (m.get(blok) or {}).get("voqealar") or []:
            if isinstance(v, dict) and v.get("rasm"):
                v["rasm"] = tuzat(v["rasm"], f"{v.get('nom') or ''} {v.get('matn') or ''}") or ""
    kontent = []
    ICHKI = {"lugat": ("sozlar", lambda x: f"{x.get('tarjima') or ''} {x.get('soz') or ''}", True),
             "vaqt_chizigi": ("voqealar", lambda x: f"{x.get('nom') or ''} {x.get('matn') or ''}", False),
             "galereya": ("rasmlar", lambda x: x.get("izoh") or "", True),
             "jarayon": ("bosqichlar", lambda x: f"{x.get('nom') or ''} {x.get('matn') or ''}", False),
             "tajriba": ("jihozlar", lambda x: x.get("nom") or "", True),
             "moslash": ("juftlar", lambda x: f"{x.get('ong') or ''} {x.get('chap') or ''}", False)}
    for b in m.get("bolimlar") or []:
        for sl in b.get("slaydlar") or []:
            yangi_els = []
            for e in sl.get("elementlar") or []:
                if e.get("tur") in ICHKI:
                    maydon, matnf, buyum = ICHKI[e["tur"]]
                    for it in e.get(maydon) or []:
                        if not isinstance(it, dict):
                            continue
                        if it.get("rasm"):
                            it["rasm"] = tuzat(it["rasm"], matnf(it)) or ""
                        if not it.get("rasm") and avto:
                            if buyum:
                                kal = buyum_rasmi(matnf(it), band)
                            else:
                                kal, _b = eng_mos(matnf(it), chegara=5.0, band=band, fan=fan)
                            if kal:
                                it["rasm"] = kal
                                hisobot["qoshildi"].append(kal)
                        if it.get("rasm"):
                            band.add(it["rasm"])
                if e.get("tur") == "iqtibos":
                    if e.get("rasm"):
                        e["rasm"] = tuzat(e["rasm"], e.get("muallif") or "") or ""
                    if not e.get("rasm") and avto and e.get("muallif"):
                        e["rasm"] = buyum_rasmi(e["muallif"], band) or ""
                    if e.get("rasm"):
                        band.add(e["rasm"])
                    yangi_els.append(e)
                    continue
                if e.get("tur") == "rasmda_nima" and e.get("rasm"):
                    e["rasm"] = tuzat(e["rasm"], f"{e.get('savol') or ''} {' '.join(e.get('variantlar') or [])}") or ""
                    if not e["rasm"]:
                        continue
                    band.add(e["rasm"])
                    yangi_els.append(e)
                    continue
                if e.get("rasm"):
                    k2 = tuzat(e["rasm"], f"{sl.get('sarlavha') or ''} {_el_matni(e)}")
                    if k2:
                        e["rasm"] = k2
                    else:
                        e["rasm"] = ""
                        if e.get("tur") == "rasm" and not e.get("chizma"):
                            continue  # bo'sh ramka o'rniga element olib tashlanadi
                yangi_els.append(e)
            sl["elementlar"] = yangi_els
            kontent.append(sl)
        b["slaydlar"] = [sl for sl in b.get("slaydlar") or [] if sl.get("elementlar")]
    for sl in kontent:
        for e in sl.get("elementlar") or []:
            if e.get("rasm"):
                band.add(e["rasm"])

    if avto:
        # 2) titul rasmi — avval mavzu nomidan (eng mavzuviy rasm titulga)
        titul_kerak = not meta.get("rasm") and not meta.get("chizma")
        if titul_kerak:
            # sayt kutubxonasidan faqat mavzu nomining o'zi mos kelsa; tayanch so'zlar bilan — faqat taqdimot rasmlari
            kal, _b = eng_mos(" ".join([meta.get("mavzu") or ""] * 2), chegara=6.0, band=band, fan=fan)
            if not kal:
                matn = " ".join([meta.get("mavzu") or ""] * 2 + list(meta.get("tayanch") or []) + [meta.get("qisqa") or ""])
                kal, _b = eng_mos(matn, chegara=6.0, band=band, fan=fan, rk=False)
            if kal:
                meta["rasm"] = kal
                band.add(kal)
                hisobot["qoshildi"].append(kal)
                titul_kerak = False
        # 3) rasmsiz slaydlarga mos rasm (eng yuqori ball birinchi, har rasm bir marta)
        nomzod = []
        for sl in kontent:
            els = [e for e in sl.get("elementlar") or [] if e.get("tur") != "eslatma"]
            if len(els) != 1 or els[0].get("tur") not in _MATNLI:
                continue
            if any(e.get("rasm") or e.get("chizma") for e in sl.get("elementlar") or []):
                continue
            matn = f"{sl.get('sarlavha') or ''} {sl.get('sarlavha') or ''} {_el_matni(els[0])}"
            kal, ball = eng_mos(matn, chegara=6.5, band=band, fan=fan)
            if kal:
                nomzod.append((ball, id(sl), sl, els[0], kal))
        nomzod.sort(key=lambda x: -x[0])
        chek = max(3, round(0.75 * max(1, len(kontent))))
        qoyildi = 0
        for ball, _i, sl, el, kal in nomzod:
            if qoyildi >= chek:
                break
            if kal in band:
                kal, ball = eng_mos(f"{sl.get('sarlavha') or ''} {_el_matni(el)}", chegara=6.5, band=band, fan=fan)
                if not kal:
                    continue
            if el.get("tur") == "hayotiy":
                el["rasm"] = kal
            else:
                sl["elementlar"].append({"tur": "rasm", "rasm": kal, "izoh": ""})
            band.add(kal)
            qoyildi += 1
            hisobot["qoshildi"].append(kal)
        # 3a) kichik sinflar: matnda sanab o'tilgan narsalar rasmlari (rasmsiz matnli slaydga «galereya»)
        if _kichik(meta):
            for sl in kontent:
                els = [e for e in sl.get("elementlar") or [] if e.get("tur") != "eslatma"]
                if len(els) != 1 or els[0].get("tur") not in _MATNLI or els[0].get("rasm") or els[0].get("chizma"):
                    continue
                topildi = []
                for soz in _royxat_sozlari(_el_matni(els[0])):
                    # «Ular sut» → «sut», «shaftoli oldik» → «shaftoli»: rasm topilgan so'zning o'zi izoh bo'ladi
                    for w in ([soz] if " " not in soz else [x for x in soz.split() if len(x) >= 3]):
                        kal = buyum_rasmi(w, band | {k for k, _ in topildi})
                        if kal:
                            topildi.append((kal, w[:1].upper() + w[1:]))
                            break
                    if len(topildi) >= 4:
                        break
                if len(topildi) >= 2:
                    sl["elementlar"].append({"tur": "galereya", "rasmlar": [{"rasm": k, "izoh": s} for k, s in topildi]})
                    for k, _ in topildi:
                        band.add(k)
                        hisobot["qoshildi"].append(k)
        # 3b) bo'lim titullari uchun (slaydlarda ishlatilmagan) rasm
        for b in m.get("bolimlar") or []:
            if b.get("rasm") or not b.get("slaydlar"):
                continue
            matn = " ".join([b.get("nom") or ""] * 2 + [b.get("izoh") or ""] + [sl.get("sarlavha") or "" for sl in b["slaydlar"]])
            kal, _b = eng_mos(matn, chegara=6.5, band=band, fan=fan)
            if kal:
                b["rasm"] = kal
                band.add(kal)
                hisobot["qoshildi"].append(kal)
        # 4) titul hali bo'sh bo'lsa — butun taqdimot matni bo'yicha (slaydlarda ishlatilmagan rasm)
        if titul_kerak:
            matn = " ".join([meta.get("mavzu") or ""] * 2 + [sl.get("sarlavha") or "" for sl in kontent])
            kal, _b = eng_mos(matn, chegara=7.0, band=band, fan=fan, rk=False)
            if not kal:  # yangisi bo'lmasa — taqdimotdagi eng mavzuviy rasm titulda ham turadi
                kal, _b = eng_mos(matn, chegara=7.0, fan=fan, rk=False)
            if not kal and nomzod and qoyildi:  # eng yuqori ballli slayd rasmi
                kal = next((x[4] for x in nomzod if x[4] in band), None)
            if kal:
                meta["rasm"] = kal
                band.add(kal)
                if kal not in hisobot["qoshildi"]:
                    hisobot["qoshildi"].append(kal)
    hisobot["ishlatilgan"] = sorted(band)
    return hisobot
