"""Ochiq dars generatori (ochiq-dars/1).

Oshxona qoidasi: tayyor dars oldindan yozilmaydi. Har mavzuning «masalliqlari» (miya.masalliq: atamalar, savollar,
qismlar, keys…) va metodlar bazasi (ochiq_metodlar) tayyor turadi; o'qituvchi sinf yoki kursni (majburiy), fan va
mavzuni tanlaganda generator shulardan darsni «pishiradi»:
  qolda  — o'qituvchi har bosqich metodini, guruhlash va yakuniy o'yinni o'zi tanlaydi;
  tezkor — generator mosini o'zi (tasodifiy, lekin mos) tanlaydi;
  ai     — AI tanlaydi va o'qituvchi gaplari, materiallarni yozadi (ochiq_dars_ai).
Natija — dars rejasi: maqsadlar, texnologik xarita, bosqichlar (metod, o'qituvchi va o'quvchi faoliyati, material),
guruhlar, baholash jadvali, ilovalar. Undan Word ishlanma (ishlanma.py) va taqdimot (ochiq_miya) yasaladi.
"""
from __future__ import annotations

import hashlib
import random
import re
from functools import lru_cache

from . import ochiq_metodlar as om
from . import sxema

SXEMA = "ochiq-dars/1"
REJIMLAR = ("qolda", "tezkor", "ai")
_APO = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'"})


def _n(s) -> str:
    return re.sub(r"\s+", " ", str(s or "").lower().translate(_APO)).strip()


@lru_cache(maxsize=1)
def baza() -> dict:
    d = om.miya()
    return {"d": d, "M": {m["kod"]: m for m in d["metodlar"]}, "A": {a["kod"]: a for a in d["andozalar"]},
            "F": {f["kod"]: f for f in d["fanlar"]}, "G": {g["kod"]: g for g in d["guruhlash"]},
            "B": {b["kod"]: b for b in d["birlashtirish"]}, "Y": {y["kod"]: y for y in d["yosh_guruhlari"]},
            "I": {i["kod"]: i["nom"] for i in d["ilovalar"]}, "FMT": {f["kod"]: f for f in d["formatlar"]}}


# ---------------------------------------------------------------- sinf/kurs → yosh guruhi; fan nomi → fan guruhi
def yosh_kodi(daraja: str, sinf) -> str:
    """Sinf yoki kurs majburiy: bo'lmasa ValueError."""
    d = _n(daraja)
    m = re.search(r"\d+", str(sinf or ""))
    n = int(m.group()) if m else 0
    if d.startswith("mag"):
        if 1 <= n <= 2 or (n == 0 and str(sinf or "").strip()):
            return "m"
        raise ValueError("Magistratura kursini tanlang (1 yoki 2)")
    if d.startswith(("bak", "otm", "oliy")):
        if 1 <= n <= 4:
            return "b1-2" if n <= 2 else "b3-4"
        raise ValueError("Bakalavr kursini tanlang (1–4)")
    if 1 <= n <= 11:
        return "1-2" if n <= 2 else "3-4" if n <= 4 else "5-6" if n <= 6 else "7-9" if n <= 9 else "10-11"
    raise ValueError("Sinfni tanlang (1–11)")


_OTM_KALIT = [(("metodika",), "otm_metodika"), (("matem", "fizik", "algebr", "geometr", "astronom"), "otm_aniq"),
              (("kimyo", "biolog", "geograf", "ekolog", "tabiiy"), "otm_tabiiy"),
              (("informat", "axborot", "dastur", "kompyuter"), "otm_it"),
              (("til", "filolog", "adabiyot", "ingliz", "rus ", "nemis", "lingv"), "otm_til"),
              (("tarix", "huquq", "falsaf", "iqtisod", "siyosat", "sotsiol", "milliy"), "otm_gumanitar")]


def fan_kodi(fan: str, yosh: str) -> str:
    F = baza()["F"]
    otm = yosh in om.OTM
    f = _n(fan)
    eng, uzun = None, (False, 0)
    for k, x in F.items():
        if k.startswith("otm_") != otm:
            continue
        for a in [x["nom"]] + x["nomlar"]:
            a = _n(a)
            ball = (yosh in (x.get("yosh") or []), len(a))   # avval shu yoshda o'qitiladigan fan, so'ng eng uzun moslik
            if a and (a in f or (len(f) >= 4 and f in a)) and ball > uzun:
                eng, uzun = k, ball
    if eng:
        return eng
    if otm:
        for kalitlar, kod in _OTM_KALIT:
            if any(k in f + " " for k in kalitlar):
                return kod
        return "otm_pedagogika"
    return "umumiy"


def fan(kod: str) -> dict:
    F = baza()["F"]
    if kod in F:
        return F[kod]
    return {"kod": "umumiy", "nom": "Umumiy", "nomlar": [], "yosh": om.MAKTAB, "metodlar": [], "xos_usullar": [],
            "andozalar": ["aralash_45_kichik", "ochiq_guruh_45_kichik", "aralash_45", "ochiq_guruh_45", "takrorlash_45", "amaliy_45"],
            "amaliy_misol": "", "laboratoriya": "", "steam": ""}


UMUMIY_ANDOZALAR = ("ochiq_guruh_45_kichik", "ochiq_guruh_45", "ochiq_otm_80", "loyiha_45", "ekskursiya_45")


def andozalar(yosh: str, fan_kod: str) -> list:
    """Shu sinf va fanga mos dars turlari (andozalar) ro'yxati."""
    A = baza()["A"]
    f = fan(fan_kod)
    out = [A[k] for k in f["andozalar"] if k in A and yosh in A[k]["yosh"]]
    for k in UMUMIY_ANDOZALAR:   # ochiq dars, loyiha va ekskursiya darsi har fanda bo'lishi mumkin
        if k in A and yosh in A[k]["yosh"] and A[k] not in out and fan_kod != "jismoniy":
            out.append(A[k])
    return out


def standart_andoza(yosh: str, fan_kod: str, fmt: str) -> str:
    if fan_kod == "jismoniy":
        return "jismoniy_45"
    if yosh in om.OTM:
        return "ochiq_otm_80" if fmt in ("ochiq", "namunaviy") else "maruza_80"
    if fmt in ("ochiq", "namunaviy"):
        return "ochiq_guruh_45_kichik" if yosh == "1-2" else "ochiq_guruh_45"
    if fan_kod in ("ingliz_tili", "rus_tili"):
        return "xorijiy_til_45"
    return "aralash_45_kichik" if yosh == "1-2" else "aralash_45"


# ---------------------------------------------------------------- metod tanlash
def nomzodlar(bosqich: dict, yosh: str, fan_kod: str, ball: bool = False) -> list:
    """Bosqichga mos metodlar, eng mosi birinchi: bosqichning «afzal»lari, so'ng fanning o'z metodlari."""
    turlar = set(bosqich["metod_turi"]) - {"guruhlash", "birlashtirish"}
    if not turlar:
        return []
    f = fan(fan_kod)
    out = []
    for m in baza()["d"]["metodlar"]:
        if not turlar & set(m["tur"]) or yosh not in m["yosh"] or m["vaqt"][0] > bosqich["daq"]:
            continue
        if m["fan"] != "*" and fan_kod not in m["fan"]:
            continue
        b = (5 if m["kod"] in bosqich.get("afzal", []) else 0) + (3 if m["kod"] in f["metodlar"] else 0) + (1 if m["fan"] != "*" else 0)
        out.append((b, m["kod"]))
    out.sort(key=lambda x: -x[0])
    return [(k, b) for b, k in out] if ball else [k for _, k in out]


def guruhlash_nomzodlari(yosh: str) -> list:
    return [g["kod"] for g in baza()["d"]["guruhlash"] if yosh in g["yosh"]]


def birlashtirish_nomzodlari(yosh: str) -> list:
    return [b["kod"] for b in baza()["d"]["birlashtirish"] if yosh in b["yosh"]]


def _tanla(rng: random.Random, kodlar: list, band: set, ballar: dict | None = None):
    """Eng yuqori balli metodlar ichidan tasodifiy (takrorlanmasin); ball berilmasa — birinchi uchtalikdan."""
    bosh = [k for k in kodlar if k not in band] or kodlar
    if not bosh:
        return None
    if ballar:
        eng = max(ballar.get(k, 0) for k in bosh)
        top = [k for k in bosh if ballar.get(k, 0) >= eng]
        if len(top) < 2:
            top = [k for k in bosh if ballar.get(k, 0) >= eng - 2][:3]
        return rng.choice(top)
    return rng.choice(bosh[:3])


def guruh_soni(oquvchilar: int, yosh: str, istak: int = 0) -> int:
    if istak in (2, 3, 4):
        return istak
    lo, hi = baza()["Y"][yosh]["guruh_soni"]
    n = oquvchilar or 25
    g = 2 if n <= 14 else 3 if n <= 24 else 4
    return max(lo, min(hi, g))


# ---------------------------------------------------------------- masalliqlar (eski miyadan ham)
_UMUMIY_NOM = re.compile(r"(^|\s)(\d+\s*-?\s*)?(bo['‘’]?lim|guruh|qism|section|part|slayd)(\s*[\d.]+)?$|^.{0,2}$", re.I)
_HIKMATLAR = ["Ilm — saodat kaliti.", "O‘qigan o‘zar, o‘qimagan to‘zar.", "Bilim — kuch.", "Mehnatning tagi — rohat."]
KICHIK_NOMLAR = [("Quyonchalar", "quyon"), ("Ayiqchalar", "ayiq"), ("Burgutlar", "burgut"), ("Jayronlar", "jayron"),
                 ("Qaldirg‘ochlar", "qaldirgoch"), ("Laylaklar", "laylak"), ("Tipratikanlar", "tipratikan"), ("Toshbaqalar", "toshbaqa"),
                 ("Tulkichalar", "tulki"), ("Chumolilar", "chumoli"), ("Asalarilar", "asalari")]


def _gaplar(s: str, n: int = 2) -> str:
    qism = re.split(r"(?<=[.!?])\s+", (s or "").strip())
    return " ".join(qism[:n]).strip()


def _el_matn(e: dict) -> str:
    q = [e.get("matn") or "", e.get("shart") or ""]
    q += [b.get("matn") or "" for b in e.get("bandlar") or [] if isinstance(b, dict)]
    return " ".join(x for x in q if x).strip()


def masalliq(miya: dict | None) -> dict:
    """Miyadagi tayyor masalliq; yetishmagan qismlari miyaning o'zidan (bo'limlar, test, xatolar…) to'ldiriladi."""
    m = miya or {}
    mas = sxema.masalliq_toza(m.get("masalliq"))
    meta = m.get("meta") or {}
    els = [(b, sl, e) for b in m.get("bolimlar") or [] for sl in b.get("slaydlar") or [] for e in sl.get("elementlar") or []]
    if not mas["atamalar"]:
        at = []
        for _b, sl, e in els:
            if e.get("tur") in ("tarif", "qoida", "teorema") and (e.get("sarlavha") or sl.get("sarlavha")) and e.get("matn"):
                at.append({"atama": (e.get("sarlavha") or sl.get("sarlavha"))[:60], "tarif": _gaplar(e["matn"], 1)[:240]})
            elif e.get("tur") == "lugat":
                at += [{"atama": s["soz"], "tarif": s.get("tarjima") or s.get("misol") or ""} for s in e.get("sozlar") or [] if s.get("soz")]
            elif e.get("tur") == "xossalar":
                at += [{"atama": b["nom"], "tarif": _gaplar(b.get("matn") or "", 1)} for b in e.get("bandlar") or [] if b.get("nom") and b.get("matn")]
        mas["atamalar"] = [a for a in at if a["tarif"]][:10]
    if not mas["savollar"]:
        sv = [{"savol": q["savol"], "javob": q.get("javob") or ""} for q in (m.get("takrorlash") or {}).get("savollar") or []]
        sv += [{"savol": q["savol"], "javob": q["variantlar"][q.get("javob", 0)] if q.get("variantlar") else ""} for q in m.get("test") or []]
        sv += [{"savol": q, "javob": ""} for q in m.get("nazorat") or []]
        mas["savollar"] = [q for q in sv if len(re.findall(r"\w", q["savol"] or "")) >= 4][:12]
    if not mas["bayonotlar"]:
        by = []
        for _b, _sl, e in els:
            if e.get("tur") == "togri_notogri":
                by += [{"matn": f["matn"], "togri": bool(f.get("javob")), "izoh": f.get("izoh") or ""} for f in e.get("fikrlar") or []]
        for x in m.get("xatolar") or []:
            by.append({"matn": x["xato"], "togri": False, "izoh": x.get("togri") or x.get("sabab") or ""})
        for a in mas["atamalar"][:4]:
            by.append({"matn": f"{a['atama']} — {a['tarif'][0].lower() + a['tarif'][1:] if a['tarif'] else ''}", "togri": True, "izoh": ""})
        mas["bayonotlar"] = by[:8]
    if not mas["qismlar"]:
        qs = []
        for b in (m.get("bolimlar") or [])[:4]:
            matn = " ".join(_gaplar(_el_matn(e), 2) for sl in (b.get("slaydlar") or [])[:3] for e in (sl.get("elementlar") or [])[:1])
            if matn.strip():
                qs.append({"nom": b.get("nom") or "", "matn": matn.strip()[:900], "savol": f"«{b.get('nom')}» bo‘yicha asosiy fikr nima?"})
        mas["qismlar"] = qs
    if not mas["muammoli_savol"]:
        mu = (m.get("muammo") or {})
        mas["muammoli_savol"] = (mu.get("masalalar") or [{}])[0].get("matn") or mu.get("goya") or ""
    if not mas["keys"]["vaziyat"]:
        for _b, _sl, e in els:
            if e.get("tur") in ("masala", "hayotiy") and (e.get("shart") or e.get("matn")):
                mas["keys"] = {"vaziyat": (e.get("shart") or e.get("matn"))[:900], "savollar": ["Muammo nimada?", "Qanday yechim taklif qilasiz?"]}
                break
    if not mas["taqqoslash"]["a"]:
        for _b, _sl, e in els:
            if e.get("tur") == "taqqoslash" and len(e.get("bandlar") or []) >= 2:
                a, b = e["bandlar"][:2]
                mas["taqqoslash"] = {"a": a.get("nom") or "A", "b": b.get("nom") or "B", "umumiy": [],
                                     "a_farq": [x for x in [a.get("matn")] if x], "b_farq": [x for x in [b.get("matn")] if x]}
                break
    if not mas["klaster"]["shoxlar"]:
        mas["klaster"] = {"markaz": meta.get("qisqa") or meta.get("mavzu") or "",
                          "shoxlar": [{"nom": b.get("nom") or "", "bandlar": [sl.get("sarlavha") or "" for sl in (b.get("slaydlar") or [])[:3]]}
                                      for b in (m.get("bolimlar") or [])[:4] if b.get("nom")]}
    if not mas["xato_yechim"]["xato"] and m.get("xatolar"):
        x = m["xatolar"][0]
        mas["xato_yechim"] = {"shart": "", "xato": x["xato"], "togri": x.get("togri") or "", "sabab": x.get("sabab") or ""}
    if not [x for x in mas["guruh_nomlari"] if not _UMUMIY_NOM.search(x)]:
        nomz = [s["nom"] for s in mas["klaster"]["shoxlar"]] + [a["atama"] for a in mas["atamalar"]] + list(meta.get("tayanch") or [])
        mas["guruh_nomlari"] = [x for x in dict.fromkeys(nomz) if x and len(x) <= 28 and not _UMUMIY_NOM.search(x)][:4]
    mas["guruh_nomlari"] = [x[:1].upper() + x[1:] for x in mas["guruh_nomlari"] if not _UMUMIY_NOM.search(x)]
    if not mas["vazifalar"]["A"] and m.get("mustaqil_ish"):
        mi = m["mustaqil_ish"]
        mas["vazifalar"] = {"A": mi[0], "B": mi[1] if len(mi) > 1 else "", "C": mi[2] if len(mi) > 2 else ""}
    mavzu = meta.get("mavzu") or "mavzu"
    if not mas["vazifalar"]["A"]:
        mas["vazifalar"] = {"A": f"«{mavzu}» mavzusini darslikdan o‘qib, asosiy tushunchalarni daftarga yozish",
                            "B": "Mavzu bo‘yicha 2–3 ta misol yoki savol tuzib, javobini yozish",
                            "C": "Mavzu bo‘yicha ijodiy ish: plakat, sinkveyn yoki kichik loyiha"}
    if not mas["muammoli_savol"]:
        mas["muammoli_savol"] = f"«{mavzu}» haqida nimalarni bilasiz va u hayotimizda qayerda uchraydi?"
    if not mas["tajriba"]["bosqichlar"]:
        for _b, _sl, e in els:
            if e.get("tur") == "tajriba" and e.get("bosqichlar"):
                mas["tajriba"] = {"nom": e.get("sarlavha") or e.get("maqsad") or "Tajriba", "jihozlar": [j["nom"] for j in e.get("jihozlar") or []],
                                  "bosqichlar": e["bosqichlar"], "kuzatish": e.get("natija") or "", "xavfsizlik": e.get("xavfsizlik") or ""}
                break
    if not mas["bayon"]:
        mas["bayon"] = _bayon_miyadan(m)
    if not mas["asosiy_qoida"]:
        for _b, _sl, e in els:
            if e.get("tur") in ("qoida", "teorema", "tarif") and (e.get("matn") or e.get("formula")):
                mas["asosiy_qoida"] = (_gaplar(e.get("matn") or "", 2) + (" " + e["formula"] if e.get("formula") else "")).strip()
                break
    if not mas["misollar"]:
        mas["misollar"] = [{"shart": e.get("shart") or e.get("matn") or "", "yechim": list(e.get("qadamlar") or []), "javob": e.get("javob") or ""}
                           for _b, _sl, e in els if e.get("tur") in ("misol", "masala") and (e.get("shart") or e.get("matn"))][:3]
    if not mas["mashqlar"]:
        mas["mashqlar"] = [{"shart": x, "javob": ""} for x in list(m.get("mustaqil_ish") or []) + list(m.get("nazorat") or [])][:6]
    if not mas["guruh_topshiriqlari"]:
        mas["guruh_topshiriqlari"] = _topshiriqlar_miyadan(m, mas)
    if not mas["hikmat"]:
        mas["hikmat"] = _HIKMATLAR[int(hashlib.md5(_n(meta.get("mavzu")).encode()).hexdigest(), 16) % len(_HIKMATLAR)]
    if not mas["kalit_soz"]:
        t = (meta.get("tayanch") or [meta.get("qisqa") or meta.get("mavzu") or ""])[0]
        mas["kalit_soz"] = (t.split() or [""])[0][:20]
    return mas


def bor_masalliq(miya: dict | None) -> bool:
    m = sxema.masalliq_toza((miya or {}).get("masalliq"))
    return bool(m["atamalar"] or m["savollar"] or m["qismlar"])


# ---------------------------------------------------------------- metodni masalliq bilan to'ldirish
_REFLEKSIYA = {
    "uch_ikki_bir": ["3 ta yangi narsa", "2 ta qiziq narsa", "1 ta savol"],
    "svetofor": ["Yashil — hammasi tushunarli", "Sariq — qisman tushundim", "Qizil — yordam kerak"],
    "smayliklar": ["😊 — yoqdi, tushundim", "😐 — qisman", "🙁 — qiyin bo‘ldi"],
    "tugallanmagan_gap": ["Bugun men bildimki…", "Menga qiyin bo‘ldi…", "Endi men qila olaman…"],
    "besh_barmoq": ["Katta barmoq — kayfiyatim", "Ko‘rsatkich — nimani o‘rgandim", "O‘rta — nima qiyin bo‘ldi",
                    "Nomsiz — kimga yordam berdim", "Jimjiloq — yana nimani bilmoqchiman"],
    "pmi": ["Plyus — darsda nima yoqdi", "Minus — nima qiyin bo‘ldi", "Qiziq — nima qiziqtirdi"],
    "bilim_daraxti": ["Yashil barg — tushundim", "Sariq barg — qisman", "Qizil barg — qiyin bo‘ldi"],
    "chiqish_chiptasi": ["Bugungi darsning asosiy fikri nima?", "Nima tushunarsiz qoldi?"],
    "bbb": ["Bilaman", "Bilishni xohlayman", "Bilib oldim"],
}


def _savollar(mas, n, rng, bosh=0):
    sv = list(mas["savollar"])
    if not sv:
        return []
    return sv[bosh:bosh + n] if len(sv) >= bosh + n else (sv * 2)[:n]


def material(kod: str, mas: dict, miya: dict | None, guruhlar: list, rng: random.Random, n_guruh: int) -> dict:
    """Metodning shu mavzudagi materiali. tur — chiqish ko'rinishi (Word va taqdimot shunga qarab chizadi)."""
    meta = (miya or {}).get("meta") or {}
    if kod == "ha_yoq" and mas["bayonotlar"]:
        return {"tur": "bayonotlar", "bayonotlar": mas["bayonotlar"][:7]}
    if kod in ("blits", "zanjir", "breyn_ring", "zakovat", "estafeta", "labirint", "intervyu", "matematik_diktant", "mojizalar_maydoni"):
        out = {"tur": "savollar", "savollar": _savollar(mas, 8 if kod in ("blits", "matematik_diktant") else 6, rng)}
        if kod == "mojizalar_maydoni" and mas["kalit_soz"]:
            out["kalit_soz"] = mas["kalit_soz"].upper()
        if kod in ("breyn_ring", "zakovat"):
            out["savollar"] = _savollar(mas, 6, rng, bosh=max(0, len(mas["savollar"]) - 6))
        return out if out["savollar"] else {"tur": "yoq"}
    if kod in ("domino", "tarif_egasi", "loto", "krossvord", "men_kimman") and mas["atamalar"]:
        return {"tur": "atamalar", "atamalar": mas["atamalar"][:8]}
    if kod == "ortiqchasini_top" and len(mas["klaster"]["shoxlar"]) >= 2:
        q = []
        sh = mas["klaster"]["shoxlar"]
        for i, s in enumerate(sh[:3]):
            begona = (sh[(i + 1) % len(sh)]["bandlar"] or [sh[(i + 1) % len(sh)]["nom"]])[0]
            if len(s["bandlar"]) >= 2:
                q.append({"qator": s["bandlar"][:3] + [begona], "ortiqcha": begona, "sabab": f"qolganlari «{s['nom']}» turkumiga kiradi"})
        if q:
            return {"tur": "ortiqcha", "qatorlar": q}
    if kod in ("mozaika", "stansiyalar", "charxpalak", "bumerang", "yonaltiruvchi_matn", "insert", "kubik", "galereya") and mas["qismlar"]:
        qs = mas["qismlar"]
        return {"tur": "qismlar", "qismlar": [dict(q, guruh=guruhlar[i % len(guruhlar)]["nom"] if guruhlar else "") for i, q in enumerate(qs[:max(n_guruh, 2)])]}
    if kod in ("muammoli_vaziyat", "aqliy_hujum", "video_lavha") and mas["muammoli_savol"]:
        return {"tur": "matn", "matn": mas["muammoli_savol"]}
    if kod == "bashorat_kuzatish":
        if mas["tajriba"]["bosqichlar"]:
            return {"tur": "tajriba", "tajriba": mas["tajriba"], "savol": "Natija qanday bo‘ladi deb o‘ylaysiz? Nega?"}
        if mas["muammoli_savol"]:
            return {"tur": "matn", "matn": mas["muammoli_savol"]}
    if kod in ("tajriba_namoyish", "tadqiqot_mini") and mas["tajriba"]["bosqichlar"]:
        return {"tur": "tajriba", "tajriba": mas["tajriba"]}
    if kod in ("tadqiqot_mini", "loyiha") and mas["hayotiy_topshiriq"]["topshiriq"]:
        return {"tur": "matn", "sarlavha": mas["hayotiy_topshiriq"]["nom"], "matn": mas["hayotiy_topshiriq"]["topshiriq"]}
    if kod in ("keys", "fsmu", "akvarium", "sokratik", "rolli_oyin", "sahnalashtirish") and mas["keys"]["vaziyat"]:
        return {"tur": "keys", "keys": mas["keys"]}
    if kod == "debat":
        if mas["tezis"]:
            return {"tur": "matn", "sarlavha": "Tezis", "matn": mas["tezis"]}
        if mas["keys"]["vaziyat"]:
            return {"tur": "keys", "keys": mas["keys"]}
    if kod in ("venn", "t_jadval", "konseptual_jadval") and mas["taqqoslash"]["a"]:
        return {"tur": "taqqoslash", "taqqoslash": mas["taqqoslash"]}
    if kod in ("klaster", "nima_uchun", "baliq_skeleti") and mas["klaster"]["shoxlar"]:
        return {"tur": "klaster", "klaster": mas["klaster"]}
    if kod in ("topishmoq", "sirli_quti") and mas["topishmoq"]["matn"]:
        return {"tur": "topishmoq", "topishmoq": mas["topishmoq"]}
    if kod == "kun_hikmati":
        return {"tur": "matn", "sarlavha": "Kun hikmati", "matn": mas["hikmat"]}
    if kod in ("xatoni_top", "juft_tekshirish") and mas["xato_yechim"]["xato"]:
        return {"tur": "xato", "xato": mas["xato_yechim"]}
    if kod == "differensial" and mas["vazifalar"]["A"]:
        return {"tur": "vazifalar", "vazifalar": mas["vazifalar"]}
    if kod == "sinkveyn":
        return {"tur": "royxat", "sarlavha": "Sinkveyn", "bandlar": mas["sinkveyn"] or
                [meta.get("qisqa") or meta.get("mavzu") or "Mavzu", "… , …", "… , … , …", "to‘rt so‘zli gap", "bitta so‘z"]}
    if kod == "test_interaktiv" and (miya or {}).get("test"):
        return {"tur": "test", "test": (miya or {})["test"][:6]}
    if kod == "xronologik_lenta" and ((miya or {}).get("tarix") or {}).get("voqealar"):
        return {"tur": "voqealar", "voqealar": miya["tarix"]["voqealar"]}
    if kod in _REFLEKSIYA:
        return {"tur": "royxat", "bandlar": _REFLEKSIYA[kod]}
    if kod in ("kichik_maruza", "evristik_suhbat", "namunaviy_yechim", "modellashtirish", "ppp", "tpr", "teskari_sinf", "zinama_zina") and miya:
        sl = _mazmun_slaydlari(miya, 3)
        if sl:
            return {"tur": "slaydlar", "slaydlar": sl}
    return {"tur": "yoq"}


def _mazmun_slaydlari(miya: dict, n: int) -> list:
    """Yangi bilim bosqichi uchun mavzu miyasidan eng mazmunli slaydlar (rasm va chizmalari bilan)."""
    out = []
    for b in miya.get("bolimlar") or []:
        for sl in b.get("slaydlar") or []:
            if any(e.get("tur") in ("tarif", "qoida", "teorema", "formula", "misol", "xossalar", "rasm", "hayotiy", "jarayon", "tajriba")
                   or e.get("rasm") or e.get("chizma") for e in sl.get("elementlar") or []):
                out.append(sl)
                break
        if len(out) >= n:
            break
    return out


def _bayon_miyadan(m: dict) -> list:
    """AI masallig'i bo'lmasa — o'rgatish ketma-ketligi miyaning mazmunli slaydlaridan (ta'rif, qoida, misol, rasm)."""
    out = []
    for sl in _mazmun_slaydlari(m, 5):
        matn, misol, rasm = [], "", ""
        for e in sl.get("elementlar") or []:
            t = e.get("tur")
            if t in ("misol", "masala") and not misol:
                misol = " ".join(x for x in (e.get("shart") or e.get("matn") or "", ("Javob: " + e["javob"]) if e.get("javob") else "") if x)
            elif t == "xossalar":
                matn.append("; ".join(f"{b.get('nom') or ''} {b.get('matn') or ''}".strip() for b in e.get("bandlar") or []))
            elif e.get("matn") or e.get("formula"):
                matn.append((_gaplar(e.get("matn") or "", 3) + (" " + e["formula"] if e.get("formula") else "")).strip())
            rasm = rasm or e.get("rasm") or ""
        matn = " ".join(x for x in matn if x).strip()
        if matn or misol:
            out.append({"sarlavha": sl.get("sarlavha") or "", "matn": matn[:900], "misol": misol[:400], "savol": "", "javob": "", "rasm": rasm})
    return out


def _topshiriqlar_miyadan(m: dict, mas: dict) -> list:
    """Guruh topshiriqlari (AI yozmagan bo'lsa): miyadagi masalalar, mustaqil ish, so'ng mavzu qismlari bo'yicha topshiriq."""
    out = []
    for b in m.get("bolimlar") or []:
        for sl in b.get("slaydlar") or []:
            for e in sl.get("elementlar") or []:
                if e.get("tur") in ("masala", "misol") and (e.get("shart") or e.get("matn")):
                    out.append({"nom": sl.get("sarlavha") or "Masala", "topshiriq": e.get("shart") or e.get("matn"),
                                "yechim": "; ".join(list(e.get("qadamlar") or []) + ([f"Javob: {e['javob']}"] if e.get("javob") else [])),
                                "mahsulot": "yechim va javob"})
    out = out[len(mas.get("misollar") or []):] or out      # doskadagi namunalar takrorlanmasin
    for x in m.get("mustaqil_ish") or []:
        out.append({"nom": "Topshiriq", "topshiriq": x, "yechim": "", "mahsulot": "yechim"})
    for q in mas.get("qismlar") or []:
        out.append({"nom": q["nom"], "topshiriq": f"Matnni o‘qing: «{_gaplar(q['matn'], 3)}» Asosiy fikrni 3 ta band bilan yozing"
                    + (f" va savolga javob bering: {q['savol']}" if q.get("savol") else "."), "yechim": "", "mahsulot": "3 band va javob"})
    return out[:4]


BAYON_METOD = {"evristik_suhbat", "kichik_maruza", "modellashtirish", "namunaviy_yechim", "mozaika", "insert", "ppp", "tpr",
               "zinama_zina", "yonaltiruvchi_matn", "bashorat_kuzatish", "tajriba_namoyish"}
MAZMUN_GURUHLI = {"mozaika", "stansiyalar", "charxpalak", "bumerang", "yonaltiruvchi_matn", "insert", "kubik"}


def mazmun_turi(b: dict) -> str:
    """Bosqichda mavzuning qaysi qismi ishlanadi."""
    if b.get("mazmun"):
        return b["mazmun"]
    t = set(b["metod_turi"])
    if "yangi_bilim" in t:
        return "bayon"
    if "guruh_ishi" in t or (b["guruh"] and t & {"mustahkamlash", "amaliy"}):
        return "guruh_topshiriq"
    if t & {"amaliy", "mustahkamlash"}:
        return "mashq"
    return ""


def bosqich_mazmuni(tur: str, qism: int, qismlar: int, oxirgi: bool, mas: dict, miya: dict | None, guruhlar: list,
                    metod_kod: str, ishlatildi: set) -> dict:
    """Bosqichning mavzu mazmuni — sinf va mehmonlar slaydda ko'radigan narsa (metod qoidalari emas)."""
    nomlar = [g["nom"] for g in guruhlar] or [""]
    if tur == "bayon":
        by = mas["bayon"]
        if by:
            k = -(-len(by) // max(1, qismlar))
            bo = by[qism * k:(qism + 1) * k] or by[-1:]
            if metod_kod in MAZMUN_GURUHLI and len(guruhlar) >= 2:
                bo = [dict(x, guruh=nomlar[i % len(nomlar)]) for i, x in enumerate(bo if len(bo) > 1 else by[:len(nomlar)])]
            return {"tur": "bayon", "bayon": bo, "qoida": mas["asosiy_qoida"] if oxirgi else "",
                    "misollar": mas["misollar"] if oxirgi else []}
        sl = _mazmun_slaydlari(miya, 3) if miya else []
        return {"tur": "slaydlar", "slaydlar": sl} if sl else {"tur": "yoq"}
    if tur == "guruh_topshiriq":
        if "guruh_topshiriq" in ishlatildi:
            ht = mas["hayotiy_topshiriq"]
            if ht["topshiriq"]:
                return {"tur": "ijodiy", "nom": ht["nom"], "topshiriq": ht["topshiriq"]}
            tur = "mashq"
        elif mas["guruh_topshiriqlari"]:
            ishlatildi.add("guruh_topshiriq")
            gt = mas["guruh_topshiriqlari"]
            return {"tur": "guruh_topshiriq", "topshiriqlar": [dict(gt[i % len(gt)], guruh=n) for i, n in enumerate(nomlar)]}
        else:
            tur = "mashq"
    if tur == "mashq" and mas["mashqlar"] and "mashq" not in ishlatildi:
        ishlatildi.add("mashq")
        return {"tur": "mashq", "mashqlar": mas["mashqlar"][:6]}
    lo, ek = mas["loyiha"], mas["ekskursiya"]
    if tur == "loyiha_kirish" and (lo["muammo"] or lo["nom"]):
        return {"tur": "loyiha_kirish", "nom": lo["nom"], "muammo": lo["muammo"], "mahsulot": lo["mahsulot"], "mezonlar": lo["mezonlar"]}
    if tur == "loyiha_himoya" and (lo["guruh_vazifalari"] or lo["nom"]):
        vz = lo["guruh_vazifalari"] or [lo["mahsulot"] or "loyiha mahsuloti"]
        return {"tur": "loyiha_himoya", "nom": lo["nom"], "guruhlar": [{"guruh": n, "vazifa": vz[i % len(vz)]} for i, n in enumerate(nomlar)],
                "mezonlar": lo["mezonlar"]}
    if tur == "ekskursiya_kirish" and (ek["joy"] or ek["bekatlar"]):
        return {"tur": "ekskursiya_kirish", "joy": ek["joy"], "kundalik": ek["kundalik"], "xavfsizlik": ek["xavfsizlik"]}
    if tur == "ekskursiya" and ek["bekatlar"]:
        return {"tur": "ekskursiya", "joy": ek["joy"], "bekatlar": [dict(x, guruh=nomlar[i % len(nomlar)]) for i, x in enumerate(ek["bekatlar"])]}
    if tur == "kundalik" and ek["kundalik"]:
        return {"tur": "kundalik", "savollar": ek["kundalik"]}
    if tur == "loyiha_himoya" and mas["guruh_topshiriqlari"]:   # loyiha masallig'i yo'q — guruh topshiriqlari loyiha vazifasi bo'ladi
        gt = mas["guruh_topshiriqlari"]
        return {"tur": "loyiha_himoya", "nom": "", "guruhlar": [{"guruh": n, "vazifa": gt[i % len(gt)]["topshiriq"]} for i, n in enumerate(nomlar)],
                "mezonlar": []}
    if tur == "ekskursiya" and mas["bayon"]:   # ekskursiya masallig'i yo'q — mavzu bayoni bekatlar sifatida
        return {"tur": "ekskursiya", "joy": "", "bekatlar": [{"nom": x["sarlavha"] or f"{i + 1}-bekat", "matn": x["matn"], "topshiriq": x["savol"],
                                                              "javob": x["javob"], "rasm": x["rasm"], "guruh": nomlar[i % len(nomlar)]}
                                                             for i, x in enumerate(mas["bayon"])]}
    return {"tur": "yoq"}


def birlashtirish_materiali(kod: str, mas: dict, miya: dict | None, guruhlar: list, rng: random.Random) -> dict:
    meta = (miya or {}).get("meta") or {}
    nomlar = [g["nom"] for g in guruhlar]
    xulosa = ((miya or {}).get("xulosa") or {}).get("fikrlar") or []
    if kod == "mozaika_rasm":
        return {"tur": "qadamlar", "bandlar": [f"{n} — to‘g‘ri javoblar uchun rasmning {i + 1}-bo‘lagini oladi" for i, n in enumerate(nomlar)]
                + ["Barcha bo‘laklar doskada birlashtiriladi — rasm mavzuning xulosasini ko‘rsatadi"],
                "rasm": meta.get("rasm") or "", "xulosa": xulosa[0] if xulosa else meta.get("maqsad") or ""}
    if kod == "umumiy_klaster" and mas["klaster"]["shoxlar"]:
        sh = mas["klaster"]["shoxlar"]
        return {"tur": "klaster", "klaster": {"markaz": mas["klaster"]["markaz"] or meta.get("mavzu") or "",
                                              "shoxlar": [dict(sh[i % len(sh)], guruh=n) for i, n in enumerate(nomlar)]}}
    if kod == "xazina_sandigi":
        kod_r = [rng.randint(1, 9) for _ in nomlar]
        return {"tur": "qadamlar", "bandlar": [f"{n} topshiriqni bajarib kodning {i + 1}-raqamini oladi: {k}" for i, (n, k) in enumerate(zip(nomlar, kod_r))]
                + [f"Sandiq kodi: {''.join(map(str, kod_r))} — ichida rag‘bat va yakuniy savol"],
                "savol": mas["muammoli_savol"] or (mas["savollar"][0]["savol"] if mas["savollar"] else "")}
    if kod == "jamoaviy_masala" and mas["jamoaviy_masala"]["shart"]:
        jm = mas["jamoaviy_masala"]
        return {"tur": "jamoaviy", "shart": jm["shart"], "qismlar": [{"guruh": n, "matn": (jm["qismlar"] or [""])[i % max(1, len(jm["qismlar"]))]}
                                                                     for i, n in enumerate(nomlar)], "yakun": jm["yakun"]}
    if kod in ("ekspertlar_estafetasi", "sinf_mehmonlarga_qarshi") and mas["savollar"]:
        return {"tur": "savollar", "savollar": mas["savollar"][-5:]}
    if kod == "jamoaviy_sinkveyn":
        qator = ["1-qator: mavzu (ot)", "2-qator: ikki sifat", "3-qator: uch fe’l", "4-qator: to‘rt so‘zli gap", "5-qator: bitta so‘z"]
        return {"tur": "royxat", "bandlar": [f"{nomlar[i % len(nomlar)]} — {q}" for i, q in enumerate(qator)] if nomlar else qator}
    if kod == "umumiy_loyiha" and mas["hayotiy_topshiriq"]["topshiriq"]:
        return {"tur": "matn", "sarlavha": mas["hayotiy_topshiriq"]["nom"], "matn": mas["hayotiy_topshiriq"]["topshiriq"]}
    if kod == "davra_shior":
        return {"tur": "matn", "sarlavha": "Dars shiori", "matn": mas["hikmat"]}
    if kod == "konsensus" and mas["keys"]["vaziyat"]:
        return {"tur": "keys", "keys": mas["keys"]}
    if kod == "bilim_daraxti":
        return {"tur": "royxat", "bandlar": [f"{n} — o‘rgangan bilimini barg qilib daraxtga ilib qo‘yadi" for n in nomlar]}
    return {"tur": "yoq"}


# ---------------------------------------------------------------- dars rejasi
_KOMP_FAN = {"matematika": ["matematik savodxonlik, fan va texnika yangiliklaridan xabardor bo‘lish hamda foydalanish"],
             "fizika": ["matematik savodxonlik, fan va texnika yangiliklaridan xabardor bo‘lish hamda foydalanish"],
             "kimyo": ["matematik savodxonlik, fan va texnika yangiliklaridan xabardor bo‘lish hamda foydalanish"],
             "tarix": ["milliy va umummadaniy"], "adabiyot": ["milliy va umummadaniy"], "huquq": ["ijtimoiy faol fuqarolik"],
             "ingliz_tili": ["kommunikativ"], "rus_tili": ["kommunikativ"], "ona_tili": ["kommunikativ"], "oqish": ["kommunikativ"]}


def _qavs(nom: str) -> str:
    return nom if nom.startswith("«") else f"«{nom}»"


def _metodik_maqsad(asosiy: dict | None, yosh: str) -> str:
    if not asosiy:
        return ""
    k, nom = asosiy["kod"], asosiy["nom"].split(" (")[0]
    if yosh == "1-2":
        return f"O‘yin texnologiyasi ({_qavs(nom)}) orqali kichik yoshdagi o‘quvchilarning faolligi va hamkorligini oshirish"
    if k == "mozaika":
        return "«Mozaika» metodi yordamida yangi bilimni o‘quvchilar mustaqil egallashini va bir-biriga o‘rgatishini tashkil etish"
    if k in ("keys", "debat", "akvarium"):
        return f"{_qavs(nom)} orqali bilimni hayotiy vaziyatda qo‘llash va tanqidiy fikrlashni rivojlantirish usullarini ko‘rsatish"
    if k in ("tadqiqot_mini", "bashorat_kuzatish", "tajriba_namoyish"):
        return f"{_qavs(nom)} orqali tadqiqotchilik ko‘nikmasini va STEAM yondashuvini dars jarayonida qo‘llash"
    return f"{_qavs(nom)} metodi orqali o‘quvchilarning faolligi, hamkorligi va mustaqil fikrlashini oshirish usullarini ko‘rsatish"


def tuz(sorov: dict, miya: dict | None = None, mas: dict | None = None) -> dict:
    """sorov: daraja, sinf (majburiy), fan, mavzu, format (ochiq|namunaviy|oddiy), andoza, oquvchilar, guruhlar,
    rejim (qolda|tezkor), tanlov {"0": metod, ...}, guruhlash, birlashtirish, urug, metodik_maqsad."""
    B = baza()
    yosh = yosh_kodi(sorov.get("daraja") or "maktab", sorov.get("sinf"))
    meta = (miya or {}).get("meta") or {}
    fan_nomi = sxema.t(sorov.get("fan") or meta.get("fan"), 120)
    fk = fan_kodi(fan_nomi, yosh)
    fmt = sorov.get("format") if sorov.get("format") in B["FMT"] else "ochiq"
    ak = sorov.get("andoza")
    mos = {a["kod"] for a in andozalar(yosh, fk)}
    if ak not in mos:  # qisqa nom ("laboratoriya", "amaliy", "maruza") yoki formatga yozilgan dars turi
        tur = str(ak or (sorov.get("format") if sorov.get("format") not in B["FMT"] else "") or "")
        ak = next((k for k in sorted(mos) if tur and k.startswith(tur)), ak)
    if ak not in B["A"] or ak not in mos:
        ak = standart_andoza(yosh, fk, fmt)
        if ak not in mos and mos:
            ak = sorted(mos)[0]
    a = B["A"][ak]
    rejim = sorov.get("rejim") if sorov.get("rejim") in REJIMLAR else "tezkor"
    urug = int(sorov.get("urug") or 0) or random.SystemRandom().randrange(1, 10 ** 6)
    rng = random.Random(urug)
    tanlov = sorov.get("tanlov") if isinstance(sorov.get("tanlov"), dict) else {}
    oquvchilar = max(4, min(60, int(sorov.get("oquvchilar") or 25)))
    ng = guruh_soni(oquvchilar, yosh, int(sorov.get("guruhlar") or 0))
    mavzu = sxema.t(sorov.get("mavzu") or meta.get("mavzu"), 200) or "Mavzu"
    if not meta.get("mavzu"):   # miyasiz (o'z mavzusi): masalliq va materiallarda mavzu nomi chiqsin
        miya = {**(miya or {}), "meta": {**meta, "mavzu": mavzu, "fan": fan_nomi}}
    manba_mazmun = "ai" if mas else ("miya" if bor_masalliq(miya) else "")
    if not mas:
        from . import darslar
        q = darslar.top(sorov.get("daraja") or "maktab", sorov.get("sinf"), fan_nomi, mavzu)
        if q:   # qo'lda yozilgan, tekshirilgan dars — ustun; bo'sh qismlari miyadan to'ldiriladi
            mas = masalliq({**(miya or {}), "masalliq": q["masalliq"]})
            manba_mazmun = "qolda"
    mas = mas or masalliq(miya)

    # guruhlar
    kichik = yosh in ("1-2", "3-4")
    if kichik:
        bosh = rng.randrange(len(KICHIK_NOMLAR))
        guruhlar = [{"nom": KICHIK_NOMLAR[(bosh + i) % len(KICHIK_NOMLAR)][0], "rasm": KICHIK_NOMLAR[(bosh + i) % len(KICHIK_NOMLAR)][1]} for i in range(ng)]
    else:
        nomlar = [x for x in mas["guruh_nomlari"] if x][:ng]
        guruhlar = [{"nom": nomlar[i] if i < len(nomlar) else f"{i + 1}-guruh", "rasm": ""} for i in range(ng)]
    gn = guruhlash_nomzodlari(yosh)
    gk = sorov.get("guruhlash") if sorov.get("guruhlash") in gn else None
    if not gk:
        afzal = ["rasm_bolaklari", "rangli_kartochka"] if yosh == "1-2" else \
            (["tushuncha_oilasi", "oldindan_tuzilgan"] if len(mas["klaster"]["shoxlar"]) >= ng and yosh not in om.OTM else ["oldindan_tuzilgan", "juft_moslash", "rangli_kartochka"])
        afzal = [k for k in afzal if k in gn] or gn
        gk = afzal[0] if rejim == "qolda" else _tanla(rng, afzal, set())
    if gk == "tushuncha_oilasi" and mas["klaster"]["shoxlar"]:
        for i, g in enumerate(guruhlar):
            sh = mas["klaster"]["shoxlar"][i % len(mas["klaster"]["shoxlar"])]
            g["kartochkalar"] = sh["bandlar"] + [sh["nom"]]
    bn = birlashtirish_nomzodlari(yosh)
    bk = sorov.get("birlashtirish") if sorov.get("birlashtirish") in bn else None
    if not bk:
        mazmunli = [k for k in bn if birlashtirish_materiali(k, mas, miya, guruhlar, random.Random(1))["tur"] != "yoq"]
        bk = (mazmunli or bn or [None])[0] if rejim == "qolda" else _tanla(rng, mazmunli or bn, set())

    bosqichlar, band = [], {bk} if bk else set()
    mturlari = [mazmun_turi(b) for b in a["bosqichlar"]]
    bayonlar = [i for i, x in enumerate(mturlari) if x == "bayon"]
    ishlatildi: set = set()
    for i, b in enumerate(a["bosqichlar"]):
        turlar = set(b["metod_turi"])
        nzb = nomzodlar(b, yosh, fk, ball=True)
        nz = [k for k, _ in nzb]
        ballar = dict(nzb)
        if "birlashtirish" in turlar and bk:
            mk, mobj, mat = bk, B["B"][bk], birlashtirish_materiali(bk, mas, miya, guruhlar, rng)
            metod = {"kod": mk, "nom": mobj["nom"], "qadamlar": [mobj["qanday"]], "tur": "birlashtirish"}
        elif "guruhlash" in turlar and gk:
            g = B["G"][gk]
            metod = {"kod": gk, "nom": g["nom"], "qadamlar": [g["qanday"]], "tur": "guruhlash"}
            mat = {"tur": "guruhlar", "guruhlar": guruhlar}
            # guruhlash bosqichida takrorlash ham bo'lsa (masalan, OTM kirish) — qo'shimcha metod tanlanmaydi
        elif nz:
            tk = tanlov.get(str(i))
            if tk not in nz:
                tk = None
            if not tk:
                mazmunli = [k for k in nz if material(k, mas, miya, guruhlar, random.Random(1), ng)["tur"] != "yoq"]
                tartib = mazmunli + [k for k in nz if k not in mazmunli]
                for k in mazmunli:
                    ballar[k] = ballar.get(k, 0) + 5   # masallig'i bor metod afzal
                if mturlari[i] == "bayon":             # yangi mavzuni o'rgatishga mos metodlar
                    for k in nz:
                        if k in BAYON_METOD:
                            ballar[k] = ballar.get(k, 0) + 6
                tk = next((k for k in tartib if k not in band), tartib[0]) if rejim == "qolda" else _tanla(rng, tartib, band, ballar)
            band.add(tk)
            mobj = B["M"][tk]
            metod = {"kod": tk, "nom": mobj["nom"], "qadamlar": mobj["qadamlar"], "tur": "metod", "natija": mobj["natija"],
                     "ehtiyot": mobj["ehtiyot"], "shakl": mobj["shakl"]}
            mat = material(tk, mas, miya, guruhlar, rng, ng)
        else:
            metod, mat = None, {"tur": "yoq"}
        if b["nom"].lower().startswith(("uy vazifasi", "uyga", "homework", "yakun va uyga")) and mas["vazifalar"]["A"]:
            mat = {"tur": "vazifalar", "vazifalar": mas["vazifalar"]}
        mz = bosqich_mazmuni(mturlari[i], bayonlar.index(i) if i in bayonlar else 0, len(bayonlar), bool(bayonlar) and i == bayonlar[-1],
                             mas, miya, guruhlar, metod["kod"] if metod else "", ishlatildi)
        if mz["tur"] != "yoq" and mat["tur"] in ("qismlar", "slaydlar"):
            mat = {"tur": "yoq"}      # mavzu mazmuni allaqachon shu bosqichda — metod materiali takrorlanmaydi
        oq = b["oqituvchi"]
        if metod and metod["tur"] == "metod":
            oq = f"{oq}. {_qavs(metod['nom'])}: {'; '.join(metod['qadamlar'])}"
        elif metod:
            oq = f"{oq}. {_qavs(metod['nom'])}: {metod['qadamlar'][0]}"
        bosqichlar.append({
            "nom": b["nom"], "daq": b["daq"], "oqituvchi": oq, "oquvchi": b["oquvchi"], "metod": metod, "material": mat,
            "guruh": b["guruh"], "ilova": list(b["ilova"]), "izoh": (f"Nega bu metod: {metod.get('natija')}" if fmt == "namunaviy" and metod and metod.get("natija") else ""),
            "nomzodlar": [{"kod": k, "nom": B["M"][k]["nom"], "vaqt": B["M"][k]["vaqt"], "shakl": B["M"][k]["shakl"]} for k in nz[:10]],
            "mazmun": mz, "nutq": "", "rasm": ""})

    asosiy = max((x for x in bosqichlar if x["metod"] and x["metod"]["tur"] == "metod"), key=lambda x: x["daq"], default=None)
    asosiy = asosiy["metod"] if asosiy else None
    dars_m = (miya or {}).get("dars") or {}
    mq = dars_m.get("maqsadlar") or {}
    maqsad = {"talimiy": mq.get("talimiy") or (meta.get("maqsad") or f"«{mavzu}» mavzusi bo‘yicha bilim va ko‘nikmalarni shakllantirish"),
              "tarbiyaviy": mq.get("tarbiyaviy") or "jamoada ishlash, bir-birini tinglash, mas’uliyat va hamkorlik madaniyatini tarbiyalash",
              "rivojlantiruvchi": mq.get("rivojlantiruvchi") or "tanqidiy va mantiqiy fikrlash, nutq va mustaqil xulosa chiqarish ko‘nikmasini rivojlantirish"}
    komp = list(dict.fromkeys(list(dars_m.get("kompetensiyalar") or []) or (_KOMP_FAN.get(fk, ["axborot bilan ishlash"]) + ["kommunikativ"])))
    natijalar = list(dars_m.get("natijalar") or []) or [f"{x} haqida bilib oladi" for x in (meta.get("tayanch") or [])[:3]] or \
        [f"«{mavzu}» mavzusining asosiy tushunchalarini tushuntira oladi"]
    jihoz = list(dict.fromkeys(list(dars_m.get("jihozlar") or []) + ["darslik", "proyektor va taqdimot"] +
                               [B["M"][x["metod"]["kod"]]["jihoz"] for x in bosqichlar if x["metod"] and x["metod"]["tur"] == "metod"
                                and B["M"][x["metod"]["kod"]]["jihoz"]]))
    if mas["tajriba"]["jihozlar"] and ak.startswith("laboratoriya"):
        jihoz += [j for j in mas["tajriba"]["jihozlar"] if j not in jihoz]

    dars = {"sxema": SXEMA, "meta": {"mavzu": mavzu, "fan": fan_nomi or fan(fk)["nom"], "fan_kod": fk, "daraja": sorov.get("daraja") or "maktab",
                                      "sinf": sxema.t(sorov.get("sinf"), 30), "yosh": yosh, "yosh_nom": B["Y"][yosh]["nom"], "format": fmt,
                                      "format_nom": B["FMT"][fmt]["nom"], "andoza": ak, "andoza_nom": a["nom"], "daqiqa": a["daqiqa"],
                                      "oquvchilar": oquvchilar, "rejim": rejim, "urug": urug,
                                      "rasm": meta.get("rasm") or _universal_rasm(mavzu, fan_nomi, sorov),
                                      "masalliq_bor": bool(manba_mazmun) or bool(mas["bayon"] and mas["guruh_topshiriqlari"]),
                                      "mazmun_manbasi": manba_mazmun},
            "metodik_maqsad": sxema.t(sorov.get("metodik_maqsad"), 300) or (_metodik_maqsad(asosiy, yosh) if fmt != "oddiy" else ""),
            "maqsadlar": maqsad, "kompetensiyalar": komp[:5], "natijalar": natijalar[:5], "jihozlar": jihoz[:12],
            "guruhlash": {"kod": gk, "nom": B["G"][gk]["nom"] if gk else "", "guruhlar": guruhlar,
                          "rollar": om.GURUH_QOIDALARI["rollar"] if not yosh == "1-2" else [{"rol": "sardor", "vazifa": "guruhni boshqaradi"},
                                                                                         {"rol": "yordamchi", "vazifa": "materiallarni tarqatadi"}],
                          "qoidalar": om.GURUH_QOIDALARI["qoidalar"], "nomzodlar": [{"kod": k, "nom": B["G"][k]["nom"]} for k in gn]},
            "birlashtirish": {"kod": bk, "nom": B["B"][bk]["nom"] if bk else "", "nomzodlar": [{"kod": k, "nom": B["B"][k]["nom"]} for k in bn]},
            "bosqichlar": bosqichlar, "uy_vazifasi": mas["vazifalar"], "masalliq": mas}
    dars["baholash"] = _baholash(dars, ak)
    dars["ilovalar"] = _ilovalar(dars, miya)
    dars["tayyorgarlik"] = _tayyorgarlik(dars)
    if a.get("izoh"):   # loyiha va ekskursiya darsi oldindan boshlanadi
        dars["tayyorgarlik"].insert(0, {"qachon": "1–2 hafta oldin", "ish": a["izoh"]})
    dars["tahlil"] = B["FMT"]["ochiq"]["tahlil"] if fmt != "oddiy" else {}
    return dars


def _universal_rasm(mavzu, fan_nomi, sorov) -> str:
    """Titul rasmi: avval mavzu nomiga mos kutubxona rasmi, topilmasa — fanning chiroyli universal rasmi."""
    from . import rasm_tanla
    try:
        kal, _b = rasm_tanla.eng_mos(" ".join([mavzu] * 2), chegara=6.0, fan=fan_nomi or "")
        if kal:
            return kal
        return rasm_tanla.universal({"mavzu": mavzu, "fan": fan_nomi, "daraja": sorov.get("daraja") or "maktab", "sinf": sorov.get("sinf")})
    except Exception:
        return ""


def _baholash(dars, ak) -> dict:
    B = baza()
    ustun = [b["nom"] for b in dars["bosqichlar"] if b["guruh"] and not (b["metod"] and b["metod"]["tur"] == "guruhlash")]
    return {"mezonlar": B["d"]["baholash"]["laboratoriya_mezonlari"] if ak.startswith("laboratoriya") else B["d"]["baholash"]["guruh_mezonlari"],
            "ustunlar": ustun, "max_ball": 5, "guruhlar": [g["nom"] for g in dars["guruhlash"]["guruhlar"]],
            "ragbat": B["d"]["baholash"]["ragbat"]}


def _ilovalar(dars, miya) -> list:
    """Ilovalarni bosqichlar tartibida raqamlaydi va bosqichlarga «(N-ilova)» havolasini qo'yadi."""
    B = baza()
    tartib = []

    def qosh(kod):
        if kod not in tartib:
            tartib.append(kod)
        return tartib.index(kod) + 1

    for b in dars["bosqichlar"]:
        kodlar = list(b["ilova"])
        mt = b["material"]["tur"]
        if mt in ("savollar", "atamalar", "bayonotlar", "ortiqcha", "topishmoq") and "oyin_kartochkalari" not in kodlar:
            kodlar.append("oyin_kartochkalari")
        if mt == "qismlar" and "tarqatma" not in kodlar:
            kodlar.append("tarqatma")
        if mt == "test":
            kodlar.append("test")
        if mt == "tajriba" and "yoriqnoma_kartasi" not in kodlar:
            kodlar.append("yoriqnoma_kartasi")
        if mt in ("keys", "taqqoslash", "klaster", "xato", "jamoaviy") and "tarqatma" not in kodlar:
            kodlar.append("tarqatma")
        mz = (b.get("mazmun") or {}).get("tur")
        if mz in ("guruh_topshiriq", "mashq", "ekskursiya") and "tarqatma" not in kodlar:
            kodlar.append("tarqatma")
        if mz == "bayon" and "tayanch_konspekt" not in kodlar:
            kodlar.append("tayanch_konspekt")
        b["ilova_raqam"] = [qosh(k) for k in kodlar]
    if dars["meta"]["format"] != "oddiy":
        for k in ("mehmon_varaqasi", "kuzatuv_varagi", "ozini_tahlil"):
            qosh(k)
    if dars["meta"]["yosh"] in om.OTM and ((miya or {}).get("adabiyotlar") or {}).get("asosiy"):
        qosh("adabiyotlar")
    return [{"raqam": i + 1, "kod": k, "nom": B["I"].get(k, k)} for i, k in enumerate(tartib)]


def _tayyorgarlik(dars) -> list:
    B = baza()
    out = [dict(x) for x in B["FMT"]["ochiq"]["tayyorgarlik"]] if dars["meta"]["format"] != "oddiy" else []
    ng = len(dars["guruhlash"]["guruhlar"])
    chop = []
    for il in dars["ilovalar"]:
        if il["kod"] in ("tarqatma", "oyin_kartochkalari", "guruh_qoidalari", "guruh_nomlari", "loyiha_varaqasi"):
            chop.append(f"{il['raqam']}-ilova — {ng} nusxa (har guruhga)")
        elif il["kod"] in ("test", "refleksiya_varagi", "uy_vazifasi", "yoriqnoma_kartasi", "ekskursiya_varaqasi", "tayanch_konspekt"):
            chop.append(f"{il['raqam']}-ilova — har o‘quvchiga ({dars['meta']['oquvchilar']} nusxa)")
        elif il["kod"] in ("mehmon_varaqasi", "kuzatuv_varagi"):
            chop.append(f"{il['raqam']}-ilova — mehmonlar soniga qarab")
    if chop:
        uch = next((x for x in out if x["qachon"] == "3 kun oldin"), None)
        if uch:
            uch["ish"] += ". Chop etish: " + "; ".join(chop)
        else:
            out.append({"qachon": "3 kun oldin", "ish": "chop etish: " + "; ".join(chop)})
    return out


# ---------------------------------------------------------------- taqdimot uchun miya
def _qadamlar(qadamlar: list) -> list:
    """Bitta uzun ko'rsatma («…; …; …») — alohida qadamlarga."""
    if len(qadamlar) == 1:
        qism = [x.strip(" .") for x in re.split(r";\s+|\.\s+(?=[A-ZА-ЯЎҚҒҲO‘])", qadamlar[0]) if x.strip(" .")]
        if len(qism) >= 2:
            return qism
    return list(qadamlar)


def _el_material(mat: dict) -> list:
    """Bosqich materiali → taqdimot elementlari."""
    t = mat.get("tur")
    if t == "bayonotlar":
        return [{"tur": "togri_notogri", "fikrlar": [{"matn": b["matn"], "javob": b["togri"], "izoh": b["izoh"]} for b in mat["bayonotlar"][:6]]}]
    if t == "savollar":
        bs = [{"nom": "", "matn": q["savol"]} for q in mat["savollar"][:6]]
        out = [{"tur": "xossalar", "korinish": "raqamli", "bandlar": bs}]
        if mat.get("kalit_soz"):
            out.insert(0, {"tur": "eslatma", "matn": "Kalit so‘z: " + " ".join("_" for _ in mat["kalit_soz"])})
        return out
    if t == "atamalar":
        return [{"tur": "moslash", "juftlar": [{"chap": a["atama"], "ong": a["tarif"][:60]} for a in mat["atamalar"][:6]]}]
    if t == "ortiqcha":
        return [{"tur": "xossalar", "korinish": "kartalar", "bandlar": [{"nom": f"{i + 1}-qator", "matn": ", ".join(q["qator"])}
                                                                      for i, q in enumerate(mat["qatorlar"][:4])]}]
    if t == "qismlar":
        return [{"tur": "xossalar", "korinish": "kartalar", "bandlar": [{"nom": q.get("guruh") or q["nom"], "matn": f"{q['nom']}: {q['savol'] or _gaplar(q['matn'], 1)}"}
                                                                      for q in mat["qismlar"][:4]]}]
    if t == "matn":
        return [{"tur": "savol", "sarlavha": mat.get("sarlavha") or "", "matn": mat["matn"]}]
    if t == "tajriba":
        tj = mat["tajriba"]
        return [{"tur": "tajriba", "maqsad": tj["nom"], "jihozlar": [{"nom": j} for j in tj["jihozlar"][:6]], "bosqichlar": tj["bosqichlar"][:6],
                 "natija": mat.get("savol") or tj["kuzatish"], "xavfsizlik": tj["xavfsizlik"]}]
    if t == "keys":
        k = mat["keys"]
        return [{"tur": "masala", "sarlavha": "Vaziyat", "shart": k["vaziyat"], "qadamlar": k["savollar"]}]
    if t == "taqqoslash":
        q = mat["taqqoslash"]
        return [{"tur": "taqqoslash", "bandlar": [{"nom": q["a"], "matn": "; ".join(q["a_farq"])}, {"nom": "Umumiy", "matn": "; ".join(q["umumiy"])},
                                                {"nom": q["b"], "matn": "; ".join(q["b_farq"])}]}]
    if t == "klaster":
        k = mat["klaster"]
        return [{"tur": "guruhlash", "guruhlar": [{"nom": (s.get("guruh") + ": " if s.get("guruh") else "") + s["nom"], "bandlar": s["bandlar"]}
                                                  for s in k["shoxlar"][:4]]}] if len(k["shoxlar"]) >= 2 else []
    if t == "topishmoq":
        return [{"tur": "savol", "sarlavha": "Topishmoq", "matn": mat["topishmoq"]["matn"]}]
    if t == "xato":
        x = mat["xato"]
        return [{"tur": "misol", "sarlavha": "Xatoni toping", "shart": x["shart"] or "Quyidagi yechimda xato bor:", "qadamlar": [x["xato"]], "javob": "?"}]
    if t == "vazifalar":
        v = mat["vazifalar"]
        return [{"tur": "xossalar", "korinish": "zinapoya", "bandlar": [{"nom": f"{k}-daraja", "matn": v[k]} for k in "ABC" if v.get(k)]}]
    if t == "royxat":
        return [{"tur": "xossalar", "korinish": "ikonli", "bandlar": [{"nom": "", "matn": x} for x in mat["bandlar"][:6]]}]
    if t == "qadamlar":
        return [{"tur": "xossalar", "korinish": "raqamli", "bandlar": [{"nom": "", "matn": x[:1].upper() + x[1:]} for x in mat["bandlar"][:6]]}]
    if t == "jamoaviy":
        return [{"tur": "masala", "sarlavha": "Jamoaviy masala", "shart": mat["shart"], "qadamlar": [f"{q['guruh']}: {q['matn']}" for q in mat["qismlar"]],
                 "javob": mat["yakun"]}]
    if t == "voqealar":
        return [{"tur": "vaqt_chizigi", "voqealar": [{"sana": v.get("davr"), "nom": v.get("nom"), "matn": v.get("matn"), "rasm": v.get("rasm")}
                                                      for v in mat["voqealar"]]}]
    if t == "guruhlar":
        return [{"tur": "guruhlash", "guruhlar": [{"nom": g["nom"], "bandlar": g.get("kartochkalar") or []} for g in mat["guruhlar"][:4]]}] \
            if len(mat["guruhlar"]) >= 2 else []
    return []


def _bosh(x: str) -> str:
    x = (x or "").strip()
    return x[:1].upper() + x[1:]


def _izoh(b: dict, qoshimcha: list | None = None) -> str:
    """Slayd izohi (Notes) — faqat o'qituvchi ko'radi: bosqich, vaqt, metod tartibi, aytadigan gapi va javoblar."""
    q = [f"{b['nom']} — {b['daq']} daqiqa."]
    if b["metod"]:
        q.append(f"Metod: {b['metod']['nom']}. " + "; ".join(_qadamlar(b["metod"]["qadamlar"])) + ".")
    q.append("O‘qituvchi: " + (b.get("nutq") or b["oqituvchi"].split(". «")[0]))
    q.append(f"O‘quvchilar: {b['oquvchi']}.")
    q += [x for x in (qoshimcha or []) if x]
    return "\n".join(q)


def _mazmun_slaydlari_dars(b: dict) -> list:
    """Bosqich mazmuni → slaydlar (sinf va mehmonlar ko'radi: mavzu, topshiriq, rasm). Javob va yechimlar — izohda."""
    mz = b.get("mazmun") or {}
    t = mz.get("tur")
    out = []
    if t == "bayon":
        for x in mz["bayon"]:
            els = [{"tur": "tarif", "sarlavha": x["sarlavha"], "matn": x["matn"]}]
            if x.get("misol"):
                els.append({"tur": "misol", "sarlavha": "Misol", "shart": x["misol"]})
            if x.get("savol"):
                els.append({"tur": "savol", "matn": x["savol"]})
            if x.get("rasm"):
                els.append({"tur": "rasm", "rasm": x["rasm"], "izoh": ""})
            sar = (f"{x['guruh']}: " if x.get("guruh") else "") + (x["sarlavha"] or b["nom"])
            out.append({"sarlavha": sar, "izoh": _izoh(b, [f"Savol javobi: {x['javob']}" if x.get("javob") else ""]), "elementlar": els[:4]})
        if mz.get("qoida"):
            out.append({"sarlavha": "Asosiy qoida — daftarga yozamiz", "izoh": _izoh(b), "elementlar": [{"tur": "qoida", "matn": mz["qoida"]}]})
        for i, x in enumerate(mz.get("misollar") or []):
            out.append({"sarlavha": f"Namuna yechim {i + 1}" if len(mz["misollar"]) > 1 else "Namuna yechim", "izoh": _izoh(b),
                        "elementlar": [{"tur": "misol", "shart": x["shart"], "qadamlar": x["yechim"][:6], "javob": x["javob"]}]})
    elif t == "slaydlar":
        for sl in mz["slaydlar"]:
            out.append({"sarlavha": sl.get("sarlavha"), "izoh": _izoh(b), "elementlar": sl.get("elementlar") or [], "joylashuv": sl.get("joylashuv") or ""})
    elif t == "guruh_topshiriq":
        for x in mz["topshiriqlar"]:
            els = [{"tur": "masala", "sarlavha": x["nom"], "shart": x["topshiriq"]}]
            if x.get("mahsulot"):
                els.append({"tur": "eslatma", "matn": f"Natija: {x['mahsulot']}"})
            out.append({"sarlavha": f"{x['guruh']} — topshiriq", "izoh": _izoh(b, [f"Yechim: {x['yechim']}" if x.get("yechim") else ""]), "elementlar": els})
    elif t == "mashq":
        ms = mz["mashqlar"]
        out.append({"sarlavha": "Mustaqil bajaramiz", "izoh": _izoh(b, ["Javoblar: " + "; ".join(f"{i + 1}) {x['javob']}" for i, x in enumerate(ms) if x.get("javob"))]),
                    "elementlar": [{"tur": "xossalar", "korinish": "raqamli", "bandlar": [{"nom": "", "matn": x["shart"]} for x in ms[:6]]}]})
    elif t == "ijodiy":
        out.append({"sarlavha": mz["nom"] or "Ijodiy topshiriq", "izoh": _izoh(b), "elementlar": [{"tur": "savol", "matn": mz["topshiriq"]}]})
    elif t == "loyiha_kirish":
        els = [{"tur": "savol", "sarlavha": mz["nom"] or "Loyiha muammosi", "matn": mz["muammo"] or mz["nom"]}]
        if mz["mezonlar"]:
            els.append({"tur": "xossalar", "korinish": "ikonli", "bandlar": [{"nom": "", "matn": _bosh(x)} for x in mz["mezonlar"][:5]]})
        out.append({"sarlavha": "Loyiha: muammo va baholash mezonlari", "izoh": _izoh(b), "elementlar": els})
    elif t == "loyiha_himoya":
        out.append({"sarlavha": "Loyiha himoyasi" + (f": {mz['nom']}" if mz.get("nom") else ""), "izoh": _izoh(b),
                    "elementlar": [{"tur": "xossalar", "korinish": "kartalar", "bandlar": [{"nom": g["guruh"], "matn": g["vazifa"]} for g in mz["guruhlar"][:4]]}]})
    elif t == "ekskursiya_kirish":
        els = [{"tur": "savol", "sarlavha": "Qayerga boramiz?", "matn": mz["joy"] or "Sayohatga chiqamiz!"}]
        if mz["kundalik"]:
            els.append({"tur": "xossalar", "korinish": "raqamli", "bandlar": [{"nom": "", "matn": x} for x in mz["kundalik"][:4]]})
        out.append({"sarlavha": "Sayohat oldidan: kuzatuv savollari", "izoh": _izoh(b, ["Xavfsizlik: " + "; ".join(mz["xavfsizlik"]) if mz["xavfsizlik"] else ""]),
                    "elementlar": els})
    elif t == "ekskursiya":
        for i, x in enumerate(mz["bekatlar"]):
            els = [{"tur": "matn", "matn": x["matn"]}]
            if x.get("rasm"):
                els.append({"tur": "rasm", "rasm": x["rasm"], "izoh": ""})
            if x.get("topshiriq"):
                els.append({"tur": "savol", "matn": x["topshiriq"]})
            out.append({"sarlavha": f"{i + 1}-bekat: {x['nom']}", "izoh": _izoh(b, [f"Bekat guruhi: {x.get('guruh') or ''}",
                                                                                  f"Javob: {x['javob']}" if x.get("javob") else ""]), "elementlar": els})
    elif t == "kundalik":
        out.append({"sarlavha": "Kuzatuv kundaligi", "izoh": _izoh(b),
                    "elementlar": [{"tur": "xossalar", "korinish": "raqamli", "bandlar": [{"nom": "", "matn": x} for x in mz["savollar"][:5]]}]})
    return out


def ochiq_miya(dars: dict, miya: dict | None = None) -> dict:
    """Dars rejasidan taqdimot miyasi — sinf va mehmonlar ko'radigani: mavzu, topshiriqlar, o'yinlar, rasmlar.
    Metod tartibi, o'qituvchi gapi, javob va yechimlar slayd izohida (Notes) — faqat o'qituvchi ko'radi."""
    m0 = miya or {}
    mt = dars["meta"]
    meta = {"mavzu": mt["mavzu"], "fan": mt["fan"], "daraja": mt["daraja"], "sinf": mt["sinf"], "tur": mt["andoza_nom"].lower(),
            "qisqa": (m0.get("meta") or {}).get("qisqa") or "", "maqsad": dars["maqsadlar"]["talimiy"],
            "tayanch": (m0.get("meta") or {}).get("tayanch") or [], "rasm": mt.get("rasm") or "", "til": "uz"}
    bolimlar = []
    gr = dars["guruhlash"]
    for i, b in enumerate(dars["bosqichlar"]):
        slaydlar = []
        if b["metod"] and b["metod"]["tur"] == "guruhlash":
            slaydlar.append({"sarlavha": "Bizning guruhlar", "izoh": _izoh(b, ["Rollar: " + "; ".join(f"{r['rol']} — {r['vazifa']}" for r in gr["rollar"])]),
                             "elementlar": [{"tur": "guruhlash", "guruhlar": [{"nom": g["nom"], "bandlar": g.get("kartochkalar") or [r["rol"] for r in gr["rollar"]][:4]}
                                                                              for g in gr["guruhlar"][:4]]}]
                             if len(gr["guruhlar"]) >= 2 else [{"tur": "matn", "matn": ", ".join(g["nom"] for g in gr["guruhlar"])}]})
            slaydlar.append({"sarlavha": "Guruhda ishlash qoidalari", "izoh": _izoh(b),
                             "elementlar": [{"tur": "xossalar", "korinish": "ikonli", "bandlar": [{"nom": "", "matn": _bosh(q)} for q in gr["qoidalar"][:5]]}]})
            if dars["baholash"]["ustunlar"]:
                slaydlar.append({"sarlavha": "Qanday baholanamiz", "izoh": _izoh(b), "elementlar": [{"tur": "jadval", "ustunlar": ["Mezon", "Ball"],
                                 "qatorlar": [[_bosh(x), str(dars["baholash"]["max_ball"])] for x in dars["baholash"]["mezonlar"][:6]]}]})
        else:
            slaydlar += _mazmun_slaydlari_dars(b)
            mat = b["material"]
            if mat["tur"] == "slaydlar":
                for sl in mat["slaydlar"]:
                    slaydlar.append({"sarlavha": sl.get("sarlavha"), "izoh": _izoh(b), "elementlar": sl.get("elementlar") or [],
                                     "joylashuv": sl.get("joylashuv") or ""})
            elif mat["tur"] != "test":       # test yakunda alohida chiqadi
                me = _el_material(mat)
                if me:
                    javob = []
                    if mat["tur"] == "savollar":
                        javob = ["Javoblar: " + "; ".join(f"{k + 1}) {q['javob']}" for k, q in enumerate(mat["savollar"][:6]) if q.get("javob"))]
                    elif mat["tur"] == "topishmoq":
                        javob = [f"Javob: {mat['topishmoq']['javob']}"]
                    elif mat["tur"] == "xato":
                        javob = [f"To‘g‘ri: {mat['xato']['togri']}. Sabab: {mat['xato']['sabab']}"]
                    slaydlar.append({"sarlavha": b["metod"]["nom"] if b["metod"] else b["nom"], "izoh": _izoh(b, javob), "elementlar": me})
            if b.get("rasm") and not any(e.get("rasm") == b["rasm"] for sl in slaydlar for e in sl.get("elementlar") or []):
                if slaydlar and len(slaydlar[0]["elementlar"]) < 4:
                    slaydlar[0]["elementlar"].append({"tur": "rasm", "rasm": b["rasm"], "izoh": ""})
                else:
                    slaydlar.append({"sarlavha": b["nom"], "izoh": _izoh(b), "elementlar": [{"tur": "rasm", "rasm": b["rasm"], "izoh": ""}]})
            if not slaydlar:
                slaydlar.append({"sarlavha": b["nom"], "izoh": _izoh(b), "elementlar": [{"tur": "matn", "matn": _bosh(b["oquvchi"])}]})
        bolimlar.append({"nom": b["nom"], "izoh": "", "slaydlar": slaydlar})
    test = []
    for b in dars["bosqichlar"]:
        if b["material"]["tur"] == "test":
            test = b["material"]["test"]
    return {"meta": meta, "bolimlar": bolimlar[:6] if len(bolimlar) <= 6 else _birlashtir_bolimlar(bolimlar),
            "test": test, "xulosa": {"fikrlar": [_bosh(x) for x in dars.get("natijalar") or []][:4]}}


def _birlashtir_bolimlar(bolimlar: list) -> list:
    """Sxema 6 bo'limgacha qabul qiladi: qisqa bosqichlar qo'shnisi bilan bitta bo'limga birlashtiriladi."""
    out = [dict(b, slaydlar=list(b["slaydlar"])) for b in bolimlar]
    while len(out) > 6:
        i = min(range(len(out) - 1), key=lambda k: len(out[k]["slaydlar"]) + len(out[k + 1]["slaydlar"]))
        a, b = out[i], out[i + 1]
        qisqa = [re.split(r"[:,(]", x["nom"])[0].strip() for x in (a, b)]
        out[i] = {"nom": f"{qisqa[0]} va {qisqa[1][:1].lower() + qisqa[1][1:]}", "izoh": "", "slaydlar": a["slaydlar"] + b["slaydlar"]}
        del out[i + 1]
    for b in out:
        b["slaydlar"] = b["slaydlar"][:8]
    return out


def katalog() -> dict:
    """Frontend uchun: yosh guruhlari, formatlar, andozalar, metodlar, guruhlash, birlashtirish, fanlar."""
    d = baza()["d"]
    return {"yosh_guruhlari": [{k: y[k] for k in ("kod", "nom", "yosh", "dars")} for y in d["yosh_guruhlari"]],
            "formatlar": [{"kod": f["kod"], "nom": f["nom"], "maqsad": f["maqsad"]} for f in d["formatlar"]],
            "andozalar": [{"kod": a["kod"], "nom": a["nom"], "daqiqa": a["daqiqa"], "yosh": a["yosh"], "fan": a.get("fan") or [],
                           "bosqichlar": [{"nom": b["nom"], "daq": b["daq"]} for b in a["bosqichlar"]]} for a in d["andozalar"]],
            "metodlar": [{k: m[k] for k in ("kod", "nom", "tur", "yosh", "fan", "vaqt", "shakl", "qadamlar", "natija", "ehtiyot")} for m in d["metodlar"]],
            "guruhlash": d["guruhlash"], "birlashtirish": d["birlashtirish"],
            "fanlar": [{"kod": f["kod"], "nom": f["nom"], "nomlar": f["nomlar"], "yosh": f["yosh"],
                        "andozalar": f["andozalar"] + ([] if f["kod"] == "jismoniy" else list(UMUMIY_ANDOZALAR))} for f in d["fanlar"]]}
