"""REV285: o'quv markazi kontenti Excel orqali (Miya kabi) — sinov imtihoni variantlari va strategiyalar.
Admin Excel'ni yuklaydi → tekshiriladi (qator raqami bilan xatolar) → bazaga yoziladi. Kod o'zgarmaydi."""
import io
import re

import openpyxl

SINOV_USTUN = ["Bo'lim", "Qism ID", "Qism nomi", "Ko'rsatma", "Qism matni (audio yoki o'qish matni)", "Sarlavhalar (| bilan)",
               "Savol ID", "Savol turi", "Savol audiosi (alohida bo'lsa)", "Savol", "A", "B", "C", "D", "To'g'ri javob"]
STRAT_USTUN = ["ID", "Bo'lim", "Nomi (uz)", "Nomi (ru)", "Nomi (en)", "Qadamlar (uz, har qadam yangi qatorda)", "Qadamlar (ru)", "Qadamlar (en)",
               "Misol", "Mashq savoli", "A", "B", "C", "To'g'ri javob", "Izoh (uz)", "Izoh (ru)", "Izoh (en)"]


def _s(v):
    return "" if v is None else str(v).strip()


def sinov_shablon(listening, reading, writing, speaking):
    """Mavjud variantdan Excel yasash (namuna/shablon)."""
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Sinov"; ws.append(SINOV_USTUN)
    for nom, B in (("listening", listening), ("reading", reading)):
        for b in B:
            elementlar = [(m, q) for m, q in b.get("audio", [])] + [("", q) for q in b.get("savollar", [])]
            for i, (aud, q) in enumerate(elementlar):
                var = q.get("variantlar") or []
                if q["tur"] == "tanlash" and len(var) > 4:      # sarlavha moslash: variantlar — qism sarlavhalari, javob — raqami
                    var, jav = [], str(q["javob"] + 1)
                else:
                    jav = "ABCD"[q["javob"]] if q["tur"] == "tanlash" else " | ".join(q["javob"])
                ws.append([nom, b["id"], b["qism"] if i == 0 else "", b.get("izoh", "") if i == 0 else "", b.get("matn", "") if i == 0 else "",
                           " | ".join(b.get("sarlavhalar") or []) if i == 0 else "", q["id"], q["tur"], aud, q["savol"], *(var + [""] * 4)[:4], jav])
    w = wb.create_sheet("Writing"); w.append(["ID", "Nomi", "So'z soni", "Topshiriq"])
    for t in writing: w.append([t["id"], t["nom"], t["soz"], t["topshiriq"]])
    sp = wb.create_sheet("Speaking"); sp.append(["ID", "Nomi", "Savollar (har biri yangi qatorda)"])
    for t in speaking: sp.append([t["id"], t["nom"], "\n".join(t["savollar"])])
    bio = io.BytesIO(); wb.save(bio); return bio.getvalue()


def sinov_oqish(content):
    """Excel → {listening, reading, writing, speaking}, xatolar ro'yxati (varaq, qator, xabar)."""
    xato = []
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    except Exception:
        return None, [{"varaq": "-", "qator": 0, "xabar": "Fayl Excel (.xlsx) emas yoki buzilgan"}]
    if "Sinov" not in wb.sheetnames:
        return None, [{"varaq": "-", "qator": 0, "xabar": "«Sinov» varag'i topilmadi"}]
    bolimlar = {"listening": [], "reading": []}; qismlar = {}; idlar = set()
    for n, r in enumerate(wb["Sinov"].iter_rows(min_row=2, values_only=True), 2):
        r = [_s(x) for x in (list(r) + [None] * 15)[:15]]
        if not any(r):
            continue
        bol, qid, qnom, koor, qmatn, sarl, sid, stur, saud, savol, a, b, c, d, jav = r
        bol = bol.lower()
        if bol not in bolimlar:
            xato.append({"varaq": "Sinov", "qator": n, "xabar": "Bo'lim «listening» yoki «reading» bo'lishi kerak"}); continue
        if not qid:
            xato.append({"varaq": "Sinov", "qator": n, "xabar": "Qism ID bo'sh"}); continue
        q = qismlar.get(qid)
        if not q:
            q = {"id": qid, "qism": qnom or qid, "izoh": koor}
            if qmatn: q["matn"] = qmatn
            if sarl: q["sarlavhalar"] = [x.strip() for x in sarl.split("|") if x.strip()]
            qismlar[qid] = q; bolimlar[bol].append(q)
        if not sid or not savol:
            xato.append({"varaq": "Sinov", "qator": n, "xabar": "Savol ID yoki savol matni bo'sh"}); continue
        if sid in idlar:
            xato.append({"varaq": "Sinov", "qator": n, "xabar": f"Savol ID takrorlangan: {sid}"}); continue
        idlar.add(sid)
        stur = (stur or "tanlash").lower()
        if stur == "tanlash" and not any((a, b, c, d)) and q.get("sarlavhalar"):
            # sarlavha moslash: variantlar — qism sarlavhalari, to'g'ri javob — sarlavha raqami (1, 2, …)
            if not jav.isdigit() or not (1 <= int(jav) <= len(q["sarlavhalar"])):
                xato.append({"varaq": "Sinov", "qator": n, "xabar": f"Sarlavha raqami 1–{len(q['sarlavhalar'])} oralig'ida bo'lishi kerak"}); continue
            item = {"id": sid, "tur": "tanlash", "savol": savol, "variantlar": q["sarlavhalar"], "javob": int(jav) - 1}
        elif stur == "tanlash":
            var = [x for x in (a, b, c, d) if x]
            if len(var) < 2:
                xato.append({"varaq": "Sinov", "qator": n, "xabar": "Kamida 2 ta variant kerak"}); continue
            if jav.upper()[:1] not in "ABCD"[:len(var)] or not jav:
                xato.append({"varaq": "Sinov", "qator": n, "xabar": "To'g'ri javob A/B/C/D dan biri bo'lishi kerak"}); continue
            item = {"id": sid, "tur": "tanlash", "savol": savol, "variantlar": var, "javob": "ABCD".index(jav.upper()[0])}
        elif stur == "yozish":
            qabul = [x.strip() for x in jav.split("|") if x.strip()]
            if not qabul:
                xato.append({"varaq": "Sinov", "qator": n, "xabar": "Yozma javob uchun qabul qilinadigan javob(lar) kerak (| bilan)"}); continue
            item = {"id": sid, "tur": "yozish", "savol": savol, "javob": qabul}
        else:
            xato.append({"varaq": "Sinov", "qator": n, "xabar": "Savol turi «tanlash» yoki «yozish»"}); continue
        if saud:
            q.setdefault("audio", []).append((saud, item))
        else:
            q.setdefault("savollar", []).append(item)
        if bol == "listening" and not saud and not q.get("matn"):
            xato.append({"varaq": "Sinov", "qator": n, "xabar": "Listening savoliga audio matni yo'q (qism matni yoki savol audiosi)"})
    writing, speaking = [], []
    if "Writing" in wb.sheetnames:
        for n, r in enumerate(wb["Writing"].iter_rows(min_row=2, values_only=True), 2):
            r = [_s(x) for x in (list(r) + [None] * 4)[:4]]
            if any(r):
                if not r[3]: xato.append({"varaq": "Writing", "qator": n, "xabar": "Topshiriq bo'sh"})
                else: writing.append({"id": r[0] or f"W{n}", "nom": r[1] or f"Task {len(writing) + 1}", "soz": r[2], "topshiriq": r[3]})
    if "Speaking" in wb.sheetnames:
        for n, r in enumerate(wb["Speaking"].iter_rows(min_row=2, values_only=True), 2):
            r = [_s(x) for x in (list(r) + [None] * 3)[:3]]
            if any(r):
                sav = [x.strip() for x in r[2].split("\n") if x.strip()]
                if not sav: xato.append({"varaq": "Speaking", "qator": n, "xabar": "Savol yo'q"})
                else: speaking.append({"id": r[0] or f"S{n}", "nom": r[1] or f"Part {len(speaking) + 1}", "savollar": sav})
    soni = {k: sum(len(q.get("audio", [])) + len(q.get("savollar", [])) for q in v) for k, v in bolimlar.items()}
    for k in ("listening", "reading"):
        if soni[k] == 0: xato.append({"varaq": "Sinov", "qator": 0, "xabar": f"{k.title()} bo'limida savol yo'q"})
    return {"listening": bolimlar["listening"], "reading": bolimlar["reading"], "writing": writing, "speaking": speaking, "soni": soni}, xato


def strategiya_shablon(royxat_xom):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Strategiya"; ws.append(STRAT_USTUN)
    for s in royxat_xom:
        m = s["mashq"]; var = (m["variantlar"] + ["", "", ""])[:3]
        ws.append([s["id"], s["bolim"], s["nom"]["uz"], s["nom"]["ru"], s["nom"]["en"],
                   "\n".join(q["uz"] for q in s["qadamlar"]), "\n".join(q["ru"] for q in s["qadamlar"]), "\n".join(q["en"] for q in s["qadamlar"]),
                   s["misol"], m["savol"], *var, "ABC"[m["javob"]], m["izoh"]["uz"], m["izoh"]["ru"], m["izoh"]["en"]])
    bio = io.BytesIO(); wb.save(bio); return bio.getvalue()


def strategiya_oqish(content):
    xato = []
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    except Exception:
        return None, [{"varaq": "-", "qator": 0, "xabar": "Fayl Excel (.xlsx) emas yoki buzilgan"}]
    if "Strategiya" not in wb.sheetnames:
        return None, [{"varaq": "-", "qator": 0, "xabar": "«Strategiya» varag'i topilmadi"}]
    out = []
    for n, r in enumerate(wb["Strategiya"].iter_rows(min_row=2, values_only=True), 2):
        r = [_s(x) for x in (list(r) + [None] * 17)[:17]]
        if not any(r):
            continue
        sid, bol, nu, nr, ne, qu, qr, qe, misol, sav, a, b, c, jav, iu, ir, ie = r
        if bol.lower() not in ("listening", "reading", "writing", "speaking"):
            xato.append({"varaq": "Strategiya", "qator": n, "xabar": "Bo'lim: listening / reading / writing / speaking"}); continue
        qu_, qr_, qe_ = [[x.strip() for x in t.split("\n") if x.strip()] for t in (qu, qr, qe)]
        if not nu or not qu_:
            xato.append({"varaq": "Strategiya", "qator": n, "xabar": "O'zbekcha nom va qadamlar shart"}); continue
        var = [x for x in (a, b, c) if x]
        if len(var) < 2 or jav.upper()[:1] not in "ABC"[:len(var)] or not jav:
            xato.append({"varaq": "Strategiya", "qator": n, "xabar": "Mashq: kamida 2 variant va to'g'ri javob (A/B/C)"}); continue
        k = max(len(qu_), len(qr_), len(qe_))
        pad = lambda l: (l + l[-1:] * k)[:k] if l else qu_[:k]
        out.append({"id": sid or f"S{n}", "bolim": bol.lower(), "nom": {"uz": nu, "ru": nr or nu, "en": ne or nu},
                    "qadamlar": [{"uz": a1, "ru": b1, "en": c1} for a1, b1, c1 in zip(pad(qu_), pad(qr_), pad(qe_))],
                    "misol": misol, "mashq": {"savol": sav, "variantlar": var, "javob": "ABC".index(jav.upper()[0]), "izoh": {"uz": iu, "ru": ir or iu, "en": ie or iu}}})
    if not out:
        xato.append({"varaq": "Strategiya", "qator": 0, "xabar": "Birorta strategiya yo'q"})
    return out, xato
