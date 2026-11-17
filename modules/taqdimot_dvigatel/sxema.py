"""«Taqdimot miyasi» — bitta mavzuning mazmuni (AI yoki o'qituvchi to'ldiradi, dvigatel chizadi).

Asosiy qoida: mazmunda dizayn yo'q. Faqat nima aytilishi yoziladi; qanday chiqishini dvigatel hal qiladi.
Normallashtirish AI yozgan har xil shakllarni (satr o'rniga ro'yxat, 'A' o'rniga 0 va h.k.) bir xil holatga keltiradi
va chegaralarni qo'yadi — buzuq ma'lumot taqdimotni buzmaydi.
"""
from __future__ import annotations

import re

SXEMA = "taqdimot-miya/1"

ELEMENT_TURLARI = {
    "tarif": "Ta'rif",
    "qoida": "Qoida",
    "teorema": "Teorema",
    "formula": "Formula",
    "xossalar": "Xossalar (2–6 ta karta)",
    "misol": "Misol (shart → qadamlar → javob)",
    "masala": "Masala (hayotiy, qadamlar bilan)",
    "jadval": "Jadval",
    "taqqoslash": "Taqqoslash (2–4 ustun)",
    "chizma": "Chizma (kod chizadi)",
    "rasm": "Rasm (kutubxonadan)",
    "hayotiy": "Hayotiy misol (rasm bilan)",
    "eslatma": "Muhim / diqqat",
    "savol": "Muhokama savoli",
    "matn": "Oddiy matn / ro'yxat",
}
TUR_SINONIM = {
    "ta'rif": "tarif", "tarif": "tarif", "definition": "tarif", "taʼrif": "tarif", "ta’rif": "tarif",
    "qoida": "qoida", "rule": "qoida", "teorema": "teorema", "theorem": "teorema", "aksioma": "teorema",
    "formula": "formula", "xossa": "xossalar", "xossalar": "xossalar", "properties": "xossalar", "xususiyatlar": "xossalar",
    "misol": "misol", "example": "misol", "masala": "masala", "problem": "masala", "jadval": "jadval", "table": "jadval",
    "taqqoslash": "taqqoslash", "compare": "taqqoslash", "chizma": "chizma", "diagram": "chizma", "rasm": "rasm",
    "image": "rasm", "hayotiy": "hayotiy", "hayotiy misol": "hayotiy", "eslatma": "eslatma", "muhim": "eslatma",
    "diqqat": "eslatma", "note": "eslatma", "savol": "savol", "question": "savol", "matn": "matn", "text": "matn",
}
_BAD = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def t(v, n=600):
    """Xavfsiz matn."""
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        v = str(v)
    if isinstance(v, (list, tuple)):
        v = "; ".join(t(x, n) for x in v)
    if isinstance(v, dict):
        v = v.get("matn") or v.get("text") or ""
    v = _BAD.sub("", str(v)).replace("\r", "").strip()
    return v[:n]


def ls(v, n=12, m=400):
    if v is None:
        return []
    if isinstance(v, str):
        parts = [p.strip(" -•\t") for p in re.split(r"\n|;(?=\s)", v) if p.strip(" -•\t")]
        return [t(p, m) for p in parts][:n]
    if isinstance(v, (list, tuple)):
        return [t(x, m) for x in v if t(x, m)][:n]
    return [t(v, m)]


def _chizma(v):
    if isinstance(v, dict) and v.get("tur"):
        return v
    return None


def _javob_index(j, n):
    if isinstance(j, int):
        return j if 0 <= j < n else 0
    s = t(j, 10).strip().upper().rstrip(")")
    if s and s[0] in "ABCDEF" and len(s) <= 2:
        return min("ABCDEF".index(s[0]), n - 1)
    if s.isdigit():
        k = int(s)
        return k - 1 if 1 <= k <= n else 0
    return 0


def element(e):
    if isinstance(e, str):
        return {"tur": "matn", "matn": t(e, 900)}
    if not isinstance(e, dict):
        return None
    tur = TUR_SINONIM.get(t(e.get("tur") or e.get("type"), 30).lower(), None)
    if not tur:
        tur = "chizma" if _chizma(e.get("chizma")) and not e.get("matn") else "matn"
    out = {"tur": tur, "sarlavha": t(e.get("sarlavha") or e.get("nom"), 120), "matn": t(e.get("matn"), 900),
           "formula": t(e.get("formula"), 300), "rasm": t(e.get("rasm"), 120), "izoh": t(e.get("izoh"), 300)}
    ch = _chizma(e.get("chizma"))
    if ch:
        out["chizma"] = ch
    if tur in ("xossalar", "taqqoslash"):
        bs = []
        for b in (e.get("bandlar") or e.get("items") or [])[:6]:
            if isinstance(b, str):
                b = {"matn": b}
            if isinstance(b, dict):
                bs.append({"nom": t(b.get("nom") or b.get("sarlavha"), 80), "matn": t(b.get("matn"), 300),
                           "formula": t(b.get("formula"), 160), "misol": t(b.get("misol"), 160)})
        out["bandlar"] = [b for b in bs if b["nom"] or b["matn"] or b["formula"]]
        if not out["bandlar"]:
            out["tur"] = "matn"
    if tur in ("misol", "masala"):
        out["shart"] = t(e.get("shart") or e.get("matn"), 600)
        out["qadamlar"] = ls(e.get("qadamlar") or e.get("yechim"), 8, 260)
        out["javob"] = t(e.get("javob"), 200)
    if tur == "jadval":
        cols = ls(e.get("ustunlar"), 6, 60)
        rows = []
        for r in (e.get("qatorlar") or [])[:9]:
            if isinstance(r, (list, tuple)):
                rows.append([t(c, 160) for c in r][:len(cols) or 6])
        out["ustunlar"], out["qatorlar"] = cols, rows
        if not cols or not rows:
            out["tur"] = "matn"
    if tur == "matn" and isinstance(e.get("bandlar"), list):
        out["bandlar"] = [{"matn": t(b, 300)} for b in e["bandlar"][:8]]
    return out


def normallashtir(m: dict) -> dict:
    if not isinstance(m, dict):
        raise ValueError("Miya JSON obyekt bo'lishi kerak")
    meta = m.get("meta") or {}
    out = {"sxema": SXEMA}
    out["meta"] = {
        "fan": t(meta.get("fan"), 120), "daraja": t(meta.get("daraja"), 30).lower() or "maktab", "sinf": t(meta.get("sinf"), 40),
        "raqam": t(meta.get("raqam"), 8), "tur": t(meta.get("tur"), 30) or "dars", "mavzu": t(meta.get("mavzu"), 160) or "Mavzu",
        "qisqa": t(meta.get("qisqa"), 60), "maqsad": t(meta.get("maqsad"), 400), "tayanch": ls(meta.get("tayanch"), 10, 60),
        "muassasa": t(meta.get("muassasa"), 120), "kafedra": t(meta.get("kafedra"), 120), "muallif": t(meta.get("muallif"), 80),
        "davr": t(meta.get("davr"), 80), "til": t(meta.get("til"), 5) or "uz", "belgi": t(meta.get("belgi"), 40),
        "rasm": t(meta.get("rasm"), 120),
    }
    if _chizma(meta.get("chizma")):
        out["meta"]["chizma"] = meta["chizma"]
    a = m.get("adabiyotlar") or {}
    if isinstance(a, list):
        a = {"asosiy": a}
    asosiy = []
    for b in (a.get("asosiy") or [])[:6]:
        if isinstance(b, str):
            b = {"nomi": b}
        if isinstance(b, dict):
            asosiy.append({"muallif": t(b.get("muallif"), 80), "nomi": t(b.get("nomi"), 160), "nashr": t(b.get("nashr"), 80)})
    elektron = []
    for b in (a.get("elektron") or [])[:4]:
        if isinstance(b, str):
            b = {"nomi": b}
        if isinstance(b, dict):
            elektron.append({"nomi": t(b.get("nomi"), 80), "izoh": t(b.get("izoh"), 120)})
    out["adabiyotlar"] = {"asosiy": asosiy, "elektron": elektron, "mustaqil": t(a.get("mustaqil"), 300)}
    tk = m.get("takrorlash") or {}
    sv = []
    for q in (tk.get("savollar") or [])[:6]:
        if isinstance(q, dict) and t(q.get("savol")):
            sv.append({"savol": t(q.get("savol"), 160), "javob": t(q.get("javob"), 120)})
    out["takrorlash"] = {"mavzu": t(tk.get("mavzu"), 120), "oyin": t(tk.get("oyin"), 20) or "blits", "savollar": sv}
    mu = m.get("muammo") or {}
    out["muammo"] = {"masalalar": [{"sarlavha": t(x.get("sarlavha"), 60), "matn": t(x.get("matn"), 300)} for x in (mu.get("masalalar") or [])[:3] if isinstance(x, dict)],
                     "goya": t(mu.get("goya"), 200), "zanjir": ls(mu.get("zanjir"), 4, 40), "sarlavha": t(mu.get("sarlavha"), 120)}
    tr = m.get("tarix") or {}
    if isinstance(tr, list):
        tr = {"voqealar": tr}
    out["tarix"] = {"sarlavha": t(tr.get("sarlavha"), 120), "xulosa": t(tr.get("xulosa"), 220),
                    "voqealar": [{"davr": t(v.get("davr"), 40), "nom": t(v.get("nom"), 60), "matn": t(v.get("matn"), 260),
                                  "belgi": t(v.get("belgi"), 40), "rasm": t(v.get("rasm"), 120)} for v in (tr.get("voqealar") or [])[:4] if isinstance(v, dict)]}
    bol = []
    for b in (m.get("bolimlar") or [])[:6]:
        if not isinstance(b, dict):
            continue
        slaydlar = []
        raw_sl = b.get("slaydlar")
        if not raw_sl and b.get("elementlar"):
            els = [element(x) for x in b["elementlar"]]
            els = [x for x in els if x]
            raw_sl = []
            i = 0
            while i < len(els):
                take = 1 if els[i]["tur"] in ("jadval", "taqqoslash", "xossalar") else 2
                raw_sl.append({"sarlavha": els[i].get("sarlavha") or t(b.get("nom")), "elementlar": els[i:i + take], "_tayyor": True})
                i += take
        for sl in (raw_sl or [])[:8]:
            if not isinstance(sl, dict):
                continue
            els = sl["elementlar"] if sl.get("_tayyor") else [element(x) for x in (sl.get("elementlar") or [])]
            els = [x for x in els if x][:4]
            if els:
                slaydlar.append({"sarlavha": t(sl.get("sarlavha"), 110) or t(b.get("nom"), 110), "izoh": t(sl.get("izoh"), 2000), "elementlar": els})
        if slaydlar or t(b.get("nom")):
            bol.append({"nom": t(b.get("nom"), 60) or f"{len(bol) + 1}-bo'lim", "izoh": t(b.get("izoh"), 160), "belgi": t(b.get("belgi"), 30),
                        "slaydlar": slaydlar})
    out["bolimlar"] = bol
    out["xatolar"] = [{"xato": t(x.get("xato"), 120), "sabab": t(x.get("sabab"), 160), "togri": t(x.get("togri"), 120)}
                      for x in (m.get("xatolar") or [])[:6] if isinstance(x, dict) and t(x.get("xato"))]
    me = m.get("metodika") or {}
    out["metodika"] = {"sarlavha": t(me.get("sarlavha"), 110), "bosqichlar": ls(me.get("bosqichlar"), 4, 90),
                       "kartalar": [{"sarlavha": t(k.get("sarlavha"), 60), "matn": t(k.get("matn"), 240), "chizma": _chizma(k.get("chizma"))}
                                    for k in (me.get("kartalar") or [])[:3] if isinstance(k, dict)],
                       "tavsiya": t(me.get("tavsiya"), 260)}
    xu = m.get("xulosa") or {}
    if isinstance(xu, list):
        xu = {"fikrlar": xu}
    out["xulosa"] = {"bilaman": ls(xu.get("bilaman"), 6, 120), "bilishni_xohlayman": ls(xu.get("bilishni_xohlayman"), 6, 120),
                     "bilib_oldim": ls(xu.get("bilib_oldim"), 6, 120), "fikrlar": ls(xu.get("fikrlar"), 6, 200)}
    tests = []
    for q in (m.get("test") or [])[:6]:
        if not isinstance(q, dict):
            continue
        v = ls(q.get("variantlar"), 4, 80)
        if t(q.get("savol")) and len(v) >= 2:
            tests.append({"savol": t(q.get("savol"), 160), "variantlar": v, "javob": _javob_index(q.get("javob", 0), len(v))})
    out["test"] = tests
    out["nazorat"] = ls(m.get("nazorat"), 8, 200)
    out["mustaqil_ish"] = ls(m.get("mustaqil_ish"), 5, 200)
    k = m.get("keyingi") or {}
    if isinstance(k, str):
        k = {"mavzu": k}
    out["keyingi"] = {"mavzu": t(k.get("mavzu"), 120), "izoh": t(k.get("izoh"), 200)}
    out["rasmlar"] = [{"kalit": t(r.get("kalit"), 100), "tavsif": t(r.get("tavsif"), 300), "prompt": t(r.get("prompt"), 600)}
                      for r in (m.get("rasmlar") or [])[:12] if isinstance(r, dict) and t(r.get("kalit"))]
    return out


def rasm_kalitlari(m: dict) -> list[str]:
    """Miyadagi barcha rasm kalitlari (rasm chizdirish ro'yxati uchun)."""
    out = []
    if m["meta"].get("rasm"):
        out.append(m["meta"]["rasm"])
    for v in m["tarix"]["voqealar"]:
        if v.get("rasm"):
            out.append(v["rasm"])
    for b in m["bolimlar"]:
        for sl in b["slaydlar"]:
            for e in sl["elementlar"]:
                if e.get("rasm"):
                    out.append(e["rasm"])
    return list(dict.fromkeys(out))
