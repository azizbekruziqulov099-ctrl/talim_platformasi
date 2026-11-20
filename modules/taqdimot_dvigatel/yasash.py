"""Miya → sahna (slaydlar rejasi va chizish).

1) Mazmun normallashtiriladi. 2) Urug' (seed) bo'yicha uslub, animatsiya va variantlar tanlanadi.
3) Slaydlar rejasi tuziladi: titul → adabiyot → takrorlash → reja → bo'limlar (muammo, tarix, mazmun) →
   yakuniy bo'lim (xatolar, metodika, xulosa, test, nazorat). 4) Har bir slayd o'z bloki bilan chiziladi.
"""
from __future__ import annotations

import random

from . import bloklar as B
from . import rasmlar, sxema, uslub
from .sahna import Slayd


def _notes_el(e):
    parts = []
    if e.get("sarlavha"):
        parts.append(e["sarlavha"] + ".")
    for key in ("matn", "shart"):
        if e.get(key):
            parts.append(e[key])
    if e.get("formula"):
        parts.append("Formula: " + e["formula"])
    for b in e.get("bandlar") or []:
        parts.append(" — ".join(x for x in (b.get("nom"), b.get("matn")) if x))
    for i, q in enumerate(e.get("qadamlar") or []):
        parts.append(f"{i + 1}-qadam: {q}")
    if e.get("javob"):
        parts.append("Javob: " + e["javob"])
    return "\n".join(parts).replace("**", "").replace("==", "")


def reja_tuz(m: dict, rng: random.Random, bolim_titul=None):
    """Slaydlar ro'yxati: [{"blok", "d", "sec"}]."""
    meta = m["meta"]
    plan = []
    plan.append({"blok": "titul", "d": {"meta": meta}, "sec": -1})
    a = m["adabiyotlar"]
    if a["asosiy"] or a["elektron"]:
        plan.append({"blok": "adabiyot", "d": {"adabiyotlar": a}, "sec": -1})
    if len(m["takrorlash"]["savollar"]) >= 2:
        plan.append({"blok": "takrorlash", "d": {"takrorlash": m["takrorlash"]}, "sec": -1})
    sections = []  # (nom, belgi, izoh, [slides])
    bol = m["bolimlar"]
    for bi, b in enumerate(bol):
        items = []
        if bi == 0:
            if m["muammo"]["masalalar"]:
                items.append(("muammo", {"muammo": m["muammo"]}))
            if m["tarix"]["voqealar"]:
                items.append(("tarix", {"tarix": m["tarix"]}))
        for sl in b["slaydlar"]:
            items.append(("kontent", {"sarlavha": sl["sarlavha"], "elementlar": sl["elementlar"], "izoh": sl.get("izoh")}))
        sections.append([b["nom"], b.get("belgi"), b.get("izoh"), items])
    yakun = []
    if m["xatolar"]:
        yakun.append(("xatolar", {"xatolar": m["xatolar"]}))
    if m["metodika"]["bosqichlar"] or m["metodika"]["kartalar"]:
        yakun.append(("metodika", {"metodika": m["metodika"]}))
    xu = m["xulosa"]
    if xu["bilaman"] or xu["bilib_oldim"] or xu["fikrlar"]:
        yakun.append(("xulosa", {"xulosa": xu}))
    if m["test"]:
        yakun.append(("test", {"test": m["test"]}))
    if m["nazorat"] or m["mustaqil_ish"] or m["keyingi"]["mavzu"]:
        yakun.append(("yakun", {"nazorat": m["nazorat"], "mustaqil_ish": m["mustaqil_ish"], "keyingi": m["keyingi"]}))
    sections = [s_ for s_ in sections if s_[3]]
    if yakun:
        if len(sections) >= 6 and sections:
            sections[-1][3].extend(yakun)
        else:
            nom = "Metodika va yakun" if m["metodika"]["bosqichlar"] or m["metodika"]["kartalar"] else "Xulosa va nazorat"
            sections.append([nom, "✓", "", yakun])
    if not sections:
        sections = [["Mavzu", None, "", [("kontent", {"sarlavha": meta["mavzu"], "elementlar": [{"tur": "matn", "matn": meta.get("maqsad") or meta["mavzu"]}]})]]]
    if bolim_titul is None:
        total = sum(len(s[3]) for s in sections)
        bolim_titul = len(sections) <= 5 and total <= 22 and rng.random() < 0.55
    reja_i = None
    if len(sections) >= 2:
        reja_i = len(plan)
        plan.append({"blok": "reja", "d": {}, "sec": -1})
    for si, (nom, belgi, izoh, items) in enumerate(sections):
        if bolim_titul:
            plan.append({"blok": "bolim", "d": {"no": si, "nom": nom, "izoh": izoh, "belgi": belgi}, "sec": si})
        for blok, d in items:
            plan.append({"blok": blok, "d": d, "sec": si})
    return plan, sections, reja_i


def yasa(miya: dict, seed: int | None = None, uslub_kod: str | None = None, anim: str | None = None, oila: str | None = None,
         palitra: str | None = None, bolim_titul: bool | None = None, rasm_bor=None, rasm_avto: bool = True):
    m = sxema.normallashtir(miya)
    from . import rasm_tanla
    try:
        rasm_hisobot = rasm_tanla.boyit(m, avto=rasm_avto)
    except Exception:  # rasm moslash xatosi taqdimotni to'xtatmasin
        rasm_hisobot = {"ishlatilgan": [], "almashtirildi": [], "qoshildi": [], "yoq": []}
    if seed is None:
        seed = random.SystemRandom().randrange(1, 2 ** 31)
    rng = random.Random(seed)
    if uslub_kod:
        u = uslub.Uslub(uslub_kod, anim or rng.choice(uslub.TINCH_ANIMATSIYALAR))
    else:
        u = uslub.tanla(rng, oila, palitra, anim)
    plan, sections, reja_i = reja_tuz(m, rng, bolim_titul)
    total = len(plan)
    # bo'limlarning birinchi/oxirgi slaydi
    sec_rng = {}
    for i, p in enumerate(plan):
        if p["sec"] >= 0:
            a, b = sec_rng.get(p["sec"], (i, i))
            sec_rng[p["sec"]] = (min(a, i), max(b, i))
    secs_nav = [(sections[si][0], sec_rng[si][0]) for si in range(len(sections)) if si in sec_rng]
    reja_items = [(sections[si][0], sec_rng[si][0], sec_rng[si][1], sections[si][1]) for si in range(len(sections)) if si in sec_rng]
    rb = rasm_bor or rasmlar.bor
    slides = []
    mot = uslub.motiflar(m["meta"].get("fan") or "")
    fon = {"src": "fon:" + u.kod + (("~" + rng.choice(mot)) if mot else "")}
    for i, p in enumerate(plan):
        # Morph o'xshash shakllarni o'zi juftlab, yozuvlarni slayddan slaydga uchirib yuboradi (xunuk) — faqat yumshoq fade
        s = Slayd(fon=fon, otish="fade")
        nav = {"total": total, "idx": i, "sections": secs_nav, "sec": p["sec"], "reja": reja_i if reja_i is not None else 0}
        k = B.K(s, u, random.Random(seed * 1009 + i * 31), nav, rb)
        d = dict(p["d"])
        si = p["sec"]
        if si >= 0:
            d.setdefault("kicker", f"{si + 1:02d} · {sections[si][0]}")
        blok = p["blok"]
        if blok == "titul":
            d["reja"] = reja_i if reja_i is not None else 1
        elif blok == "reja":
            d.update({"sections": reja_items, "maqsad": m["meta"].get("maqsad"), "tur": (m["meta"].get("tur") or "").lower()})
        B.BLOKLAR[blok](k, d)
        s.bolim = si
        # o'qituvchi izohi (Notes)
        izoh = ""
        if blok == "kontent":
            izoh = d.get("izoh") or "\n\n".join(_notes_el(e) for e in d["elementlar"])
        elif blok == "titul":
            mm = m["meta"]
            izoh = f"{mm.get('raqam') + '-' if mm.get('raqam') else ''}{mm.get('tur', '')}: {mm['mavzu']}.\n{mm.get('maqsad', '')}"
        elif blok == "muammo":
            izoh = "\n".join(f"{q['sarlavha']}: {q['matn']}" for q in m["muammo"]["masalalar"]) + ("\nG‘oya: " + m["muammo"]["goya"] if m["muammo"]["goya"] else "")
        elif blok == "tarix":
            izoh = "\n".join(f"{v['davr']} — {v['nom']}: {v['matn']}" for v in m["tarix"]["voqealar"])
        elif blok == "reja":
            izoh = "Reja interaktiv: istalgan kartani bossangiz, o‘sha bo‘limga o‘tasiz. Pastdagi raqamli doirachalar ham bo‘limlarga olib boradi."
        s.izoh = izoh
        sd = s.json()
        sd["qorongi"] = u.qorongi
        sd["blok"] = blok
        slides.append(sd)
    return {
        "sxema": "taqdimot-sahna/1", "w": 1280, "h": 720, "seed": seed, "uslub": u.json(), "meta": m["meta"],
        "slaydlar": slides, "miya": m, "rasm_hisobot": rasm_hisobot,
    }


def pptx(sahna: dict) -> bytes:
    from . import pptx_yoz

    def ol(src):
        if src.startswith("fon:"):
            return uslub.fon_rasm(src[4:]), 1280, 720
        if src.startswith("rasm:"):
            return rasmlar.ol(src[5:])
        return None
    return pptx_yoz.yoz(sahna, ol)
