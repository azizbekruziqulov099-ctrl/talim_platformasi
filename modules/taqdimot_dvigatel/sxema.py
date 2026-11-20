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
    # barcha fanlar uchun
    "lugat": "Lug'at kartalari (so'z, o'qilishi, tarjima, rasm, misol gap) — tillar, 1–4-sinf",
    "dialog": "Dialog (ikki suhbatdosh, navbat bilan) — tillar",
    "parcha": "Matn yoki she'r parchasi (muhim so'zlar belgilangan) — adabiyot, o'qish",
    "vaqt_chizigi": "Vaqt chizig'i (sana, voqea, rasm) — tarix",
    "xarita": "Xarita (O'zbekiston yoki dunyo; viloyat/davlat va shaharlar belgilanadi) — geografiya, tarix",
    "tajriba": "Tajriba (maqsad, jihozlar, bosqichlar, natija) — tabiiy fanlar, fizika, kimyo",
    "jarayon": "Jarayon sxemasi (aylana / zanjir / rasmli qadamlar) — biologiya, texnologiya, jismoniy tarbiya",
    "galereya": "Galereya (2–4 rasm, imzo bilan) — san'at, obidalar, cholg'ular",
    "guruhlash": "Guruhlarga ajratish (2–4 ustun) — barcha fanlar",
    "moslash": "O'yin: juftini top (so'z ↔ tarjima/rasm)",
    "togri_notogri": "O'yin: to'g'ri yoki noto'g'ri",
    "bosh_joy": "O'yin: bo'sh joyni to'ldir",
    "rasmda_nima": "O'yin: rasmda nima? (variantli)",
}
YANGI_KENG = {"lugat", "dialog", "vaqt_chizigi", "xarita", "tajriba", "jarayon", "galereya", "guruhlash", "moslash",
              "togri_notogri", "bosh_joy", "rasmda_nima"}
TUR_SINONIM = {
    "ta'rif": "tarif", "tarif": "tarif", "definition": "tarif", "taʼrif": "tarif", "ta’rif": "tarif",
    "qoida": "qoida", "rule": "qoida", "teorema": "teorema", "theorem": "teorema", "aksioma": "teorema",
    "formula": "formula", "xossa": "xossalar", "xossalar": "xossalar", "properties": "xossalar", "xususiyatlar": "xossalar",
    "misol": "misol", "example": "misol", "masala": "masala", "problem": "masala", "jadval": "jadval", "table": "jadval",
    "taqqoslash": "taqqoslash", "compare": "taqqoslash", "chizma": "chizma", "diagram": "chizma", "rasm": "rasm",
    "image": "rasm", "hayotiy": "hayotiy", "hayotiy misol": "hayotiy", "eslatma": "eslatma", "muhim": "eslatma",
    "diqqat": "eslatma", "note": "eslatma", "savol": "savol", "question": "savol", "matn": "matn", "text": "matn",
    "lugat": "lugat", "lug'at": "lugat", "lug‘at": "lugat", "vocabulary": "lugat", "sozlar": "lugat",
    "dialog": "dialog", "suhbat": "dialog", "parcha": "parcha", "sher": "parcha", "she'r": "parcha", "she’r": "parcha",
    "poem": "parcha", "matn_parcha": "parcha", "vaqt_chizigi": "vaqt_chizigi", "vaqt chizig'i": "vaqt_chizigi",
    "timeline": "vaqt_chizigi", "xronologiya": "vaqt_chizigi", "xarita": "xarita", "map": "xarita", "tajriba": "tajriba",
    "experiment": "tajriba", "jarayon": "jarayon", "process": "jarayon", "aylanish": "jarayon", "mashq": "jarayon",
    "galereya": "galereya", "gallery": "galereya", "guruhlash": "guruhlash", "klassifikatsiya": "guruhlash",
    "moslash": "moslash", "match": "moslash", "juftlash": "moslash", "togri_notogri": "togri_notogri",
    "to'g'ri_noto'g'ri": "togri_notogri", "true_false": "togri_notogri", "bosh_joy": "bosh_joy", "bo'sh joy": "bosh_joy",
    "fill": "bosh_joy", "rasmda_nima": "rasmda_nima", "picture_quiz": "rasmda_nima",
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
    if tur in YANGI_KENG or tur == "parcha":
        yangi = _fan_elementi(tur, e)
        if yangi is None:
            out["tur"] = "matn"
        else:
            out.update(yangi)
    return out


def _dl(v, n):
    return [x for x in (v or [])[:n] if isinstance(x, (dict, str))] if isinstance(v, list) else []


def _fan_elementi(tur, e):
    """Barcha fanlar uchun yangi element turlari. Bo'sh/buzuq bo'lsa None (oddiy matnga aylanadi)."""
    if tur == "lugat":
        sz = []
        for x in _dl(e.get("sozlar") or e.get("bandlar"), 6):
            x = {"soz": x} if isinstance(x, str) else x
            if t(x.get("soz")):
                sz.append({"soz": t(x.get("soz"), 40), "oqilishi": t(x.get("oqilishi") or x.get("transkripsiya"), 40),
                           "tarjima": t(x.get("tarjima"), 60), "misol": t(x.get("misol"), 140), "rasm": t(x.get("rasm"), 100)})
        return {"sozlar": sz} if sz else None
    if tur == "dialog":
        qs = []
        for x in _dl(e.get("qatorlar"), 8):
            if isinstance(x, dict) and t(x.get("matn")):
                qs.append({"kim": t(x.get("kim"), 30) or "?", "matn": t(x.get("matn"), 200), "tarjima": t(x.get("tarjima"), 200)})
        return {"qatorlar": qs} if len(qs) >= 2 else None
    if tur == "parcha":
        return {"matn": t(e.get("matn"), 1400), "muallif": t(e.get("muallif"), 80), "belgilar": ls(e.get("belgilar"), 8, 40)} if t(e.get("matn")) else None
    if tur == "vaqt_chizigi":
        vs = [{"sana": t(x.get("sana") or x.get("davr"), 30), "nom": t(x.get("nom"), 70), "matn": t(x.get("matn"), 200), "rasm": t(x.get("rasm"), 100)}
              for x in _dl(e.get("voqealar"), 6) if isinstance(x, dict) and (t(x.get("nom")) or t(x.get("matn")))]
        return {"voqealar": vs} if len(vs) >= 2 else None
    if tur == "xarita":
        hd = "dunyo" if "dun" in t(e.get("hudud"), 20).lower() or "world" in t(e.get("hudud"), 20).lower() else "ozbekiston"
        jy = []
        for x in _dl(e.get("joylar"), 10):
            x = {"nom": x} if isinstance(x, str) else x
            try:
                lat = float(x.get("lat")) if x.get("lat") not in (None, "") else None
                lon = float(x.get("lon")) if x.get("lon") not in (None, "") else None
            except (TypeError, ValueError):
                lat = lon = None
            if t(x.get("nom")):
                jy.append({"nom": t(x.get("nom"), 40), "matn": t(x.get("matn"), 100), "lat": lat, "lon": lon})
        return {"hudud": hd, "joylar": jy, "belgilash": ls(e.get("belgilash") or e.get("hududlar"), 8, 40)}
    if tur == "tajriba":
        jh = []
        for x in _dl(e.get("jihozlar"), 6):
            x = {"nom": x} if isinstance(x, str) else x
            if t(x.get("nom")):
                jh.append({"nom": t(x.get("nom"), 50), "rasm": t(x.get("rasm"), 100)})
        bq = ls(e.get("bosqichlar"), 6, 160)
        return {"maqsad": t(e.get("maqsad"), 200), "jihozlar": jh, "bosqichlar": bq, "natija": t(e.get("natija"), 260),
                "xavfsizlik": t(e.get("xavfsizlik"), 160)} if bq else None
    if tur == "jarayon":
        sh = t(e.get("shakl"), 20).lower()
        sh = "aylana" if sh.startswith("ayl") or sh == "cycle" else "qadam" if sh.startswith("qad") or e.get("tur") == "mashq" else "zanjir"
        bs = []
        for x in _dl(e.get("bosqichlar"), 6):
            x = {"nom": x} if isinstance(x, str) else x
            if t(x.get("nom")) or t(x.get("matn")):
                bs.append({"nom": t(x.get("nom"), 50), "matn": t(x.get("matn"), 140), "rasm": t(x.get("rasm"), 100)})
        return {"shakl": sh, "bosqichlar": bs} if len(bs) >= 2 else None
    if tur == "galereya":
        rs = []
        for x in _dl(e.get("rasmlar"), 4):
            x = {"rasm": x} if isinstance(x, str) else x
            if t(x.get("rasm")) or t(x.get("izoh")):
                rs.append({"rasm": t(x.get("rasm"), 100), "izoh": t(x.get("izoh"), 80)})
        return {"rasmlar": rs} if rs else None
    if tur == "guruhlash":
        gs = []
        for x in _dl(e.get("guruhlar"), 4):
            if isinstance(x, dict) and t(x.get("nom")):
                gs.append({"nom": t(x.get("nom"), 40), "bandlar": ls(x.get("bandlar"), 7, 60)})
        return {"guruhlar": gs} if len(gs) >= 2 else None
    if tur == "moslash":
        js = [{"chap": t(x.get("chap"), 60), "ong": t(x.get("ong"), 60), "rasm": t(x.get("rasm"), 100)}
              for x in _dl(e.get("juftlar"), 6) if isinstance(x, dict) and t(x.get("chap")) and (t(x.get("ong")) or t(x.get("rasm")))]
        return {"juftlar": js} if len(js) >= 2 else None
    if tur == "togri_notogri":
        fs = []
        for x in _dl(e.get("fikrlar"), 6):
            if isinstance(x, dict) and t(x.get("matn")):
                j = x.get("javob")
                ok = j is True or t(j, 10).lower() in ("true", "to'g'ri", "to‘g‘ri", "togri", "ha", "1", "t")
                fs.append({"matn": t(x.get("matn"), 160), "javob": ok, "izoh": t(x.get("izoh"), 140)})
        return {"fikrlar": fs} if fs else None
    if tur == "bosh_joy":
        gs = [{"matn": t(x.get("matn"), 160), "javob": t(x.get("javob"), 40)} for x in _dl(e.get("gaplar"), 6)
              if isinstance(x, dict) and t(x.get("matn")) and t(x.get("javob"))]
        return {"gaplar": gs} if gs else None
    if tur == "rasmda_nima":
        v = ls(e.get("variantlar"), 4, 60)
        if not t(e.get("rasm")) or len(v) < 2:
            return None
        return {"rasm": t(e.get("rasm"), 100), "savol": t(e.get("savol") or e.get("matn"), 140) or "Rasmda nima tasvirlangan?",
                "variantlar": v, "javob": _javob_index(e.get("javob", 0), len(v))}
    return None


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
                take = 1 if els[i]["tur"] in ("jadval", "taqqoslash", "xossalar") or els[i]["tur"] in YANGI_KENG else 2
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
