"""Excel shablon ⇄ miya.

O'qituvchi (yoki ChatGPT) mavzuni Excel'da to'ldiradi, sayt uni miyaga aylantiradi. Bir varaqda bitta mavzu.
Varaqlar JSON tuzilmasining aynan nusxasi, shuning uchun ikkala yo'l ham bir xil natija beradi.
"""
from __future__ import annotations

import io
import json

from . import sxema
from .chizma import CHIZMALAR

META = [
    ("fan", "Fan nomi", "Boshlang‘ich matematika kursi nazariyasi"),
    ("daraja", "maktab | bakalavr | magistr | bogcha", "bakalavr"),
    ("sinf", "5-sinf yoki 2-kurs", "2-kurs"),
    ("raqam", "Mavzu / ma’ruza raqami", "1"),
    ("tur", "dars | ma’ruza | amaliy | seminar", "ma’ruza"),
    ("mavzu", "Mavzu nomi (titulda katta yoziladi)", ""),
    ("qisqa", "Qisqa nomi", ""),
    ("maqsad", "Dars / ma’ruza maqsadi (1–2 jumla)", ""),
    ("tayanch", "Tayanch tushunchalar — har biri yangi qatorda", ""),
    ("muassasa", "Muassasa", "Samarqand davlat pedagogika instituti"),
    ("kafedra", "Kafedra (maktabda bo‘sh)", ""),
    ("muallif", "Muallif / ma’ruzachi", ""),
    ("davr", "Semestr, o‘quv yili", ""),
    ("belgi", "Titul belgisi: $\\frac{3}{8}$, ℤ, n! ...", ""),
    ("rasm", "Titul rasmi kaliti (Rasmlar varag‘idan)", ""),
    ("chizma", "Titul chizmasi (JSON, ixtiyoriy)", ""),
    ("takrorlash_mavzu", "O‘tgan mavzu nomi (o‘yin uchun)", ""),
    ("takrorlash_oyin", "blits | mosini_top", "blits"),
    ("muammo_sarlavha", "Muammoli vaziyat sarlavhasi", ""),
    ("muammo_goya", "Muammodan chiqadigan g‘oya", ""),
    ("muammo_zanjir", "Zanjir (har biri yangi qatorda): ℕ — natural ...", ""),
    ("tarix_sarlavha", "Tarix slaydi sarlavhasi", ""),
    ("tarix_xulosa", "Tarix xulosasi (bir jumla)", ""),
    ("metodika_sarlavha", "Metodika slaydi sarlavhasi", ""),
    ("metodika_tavsiya", "Metodik tavsiya", ""),
    ("adabiyot_mustaqil", "Mustaqil o‘qish uchun eslatma", ""),
    ("keyingi_mavzu", "Keyingi mavzu", ""),
    ("keyingi_izoh", "Keyingi mavzuga tayyorlanish", ""),
]
VARAQLAR = {
    "Adabiyot": ["tur (asosiy / elektron)", "muallif", "nomi", "nashr yoki izoh"],
    "Takrorlash": ["savol", "javob"],
    "Muammo": ["sarlavha", "matn"],
    "Tarix": ["davr", "nom", "matn", "belgi", "rasm kaliti"],
    "Slaydlar": ["bo‘lim №", "bo‘lim nomi", "bo‘lim izohi", "bo‘lim belgisi", "slayd sarlavhasi", "element turi", "sarlavha",
                 "matn / shart", "formula", "qadamlar (har biri yangi qatorda)", "javob", "bandlar (har biri yangi qatorda: nom: matn | formula | misol)",
                 "jadval (1-qator ustunlar, keyin qatorlar; ustunlar | bilan)", "chizma (JSON)", "rasm kaliti", "chizma/rasm ostidagi izoh", "o‘qituvchi gapi (Notes)"],
    "Xatolar": ["xato", "sabab", "to‘g‘ri"],
    "Metodika": ["tur (bosqich / karta)", "sarlavha", "matn", "chizma (JSON)"],
    "Xulosa": ["bilaman", "bilishni xohlayman", "bilib oldim", "yoki: xulosa fikri"],
    "Test": ["savol", "A", "B", "C", "D", "to‘g‘ri (A/B/C/D)"],
    "Yakun": ["tur (nazorat / mustaqil)", "matn"],
    "Rasmlar": ["kalit", "tavsif (o‘zbekcha)", "prompt (inglizcha, rasm chizdirish uchun)", "holat"],
}


def _str(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def _json(v):
    v = _str(v)
    if not v:
        return None
    try:
        d = json.loads(v)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def oqi(data: bytes) -> list[dict]:
    """Excel → miyalar ro'yxati (har bir «Mavzu» varag'i bitta mavzu; odatda bitta)."""
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    if "Mavzu" not in wb.sheetnames:
        raise ValueError("Shablonda «Mavzu» varag‘i yo‘q")

    def rows(name, skip=1):
        if name not in wb.sheetnames:
            return []
        out = []
        for i, r in enumerate(wb[name].iter_rows(values_only=True)):
            if i < skip:
                continue
            vals = [_str(c) for c in r]
            if any(vals):
                out.append(vals + [""] * 20)
        return out

    meta = {}
    for r in rows("Mavzu"):
        meta[r[0]] = r[2]
    m = {"meta": {k: meta.get(k, "") for k, _, _ in META if not k.startswith(("takrorlash_", "muammo_", "tarix_", "metodika_", "adabiyot_", "keyingi_"))}}
    m["meta"]["tayanch"] = [x.strip() for x in meta.get("tayanch", "").split("\n") if x.strip()]
    m["meta"]["chizma"] = _json(meta.get("chizma"))
    asosiy, elektron = [], []
    for r in rows("Adabiyot"):
        if r[0].lower().startswith("e"):
            elektron.append({"nomi": r[2] or r[1], "izoh": r[3]})
        else:
            asosiy.append({"muallif": r[1], "nomi": r[2], "nashr": r[3]})
    m["adabiyotlar"] = {"asosiy": asosiy, "elektron": elektron, "mustaqil": meta.get("adabiyot_mustaqil", "")}
    m["takrorlash"] = {"mavzu": meta.get("takrorlash_mavzu", ""), "oyin": meta.get("takrorlash_oyin") or "blits",
                       "savollar": [{"savol": r[0], "javob": r[1]} for r in rows("Takrorlash")]}
    m["muammo"] = {"sarlavha": meta.get("muammo_sarlavha", ""), "goya": meta.get("muammo_goya", ""),
                   "zanjir": [x.strip() for x in meta.get("muammo_zanjir", "").split("\n") if x.strip()],
                   "masalalar": [{"sarlavha": r[0], "matn": r[1]} for r in rows("Muammo")]}
    m["tarix"] = {"sarlavha": meta.get("tarix_sarlavha", ""), "xulosa": meta.get("tarix_xulosa", ""),
                  "voqealar": [{"davr": r[0], "nom": r[1], "matn": r[2], "belgi": r[3], "rasm": r[4]} for r in rows("Tarix")]}
    bolimlar = []
    cur_b = None
    cur_s = None
    for r in rows("Slaydlar"):
        bno, bnom, bizoh, bbelgi, ssar, tur = r[0], r[1], r[2], r[3], r[4], r[5]
        if bnom and (cur_b is None or bnom != cur_b["nom"]):
            cur_b = {"nom": bnom, "izoh": bizoh, "belgi": bbelgi, "slaydlar": []}
            bolimlar.append(cur_b)
            cur_s = None
        if cur_b is None:
            cur_b = {"nom": "1-bo‘lim", "slaydlar": []}
            bolimlar.append(cur_b)
        if ssar or cur_s is None:
            cur_s = {"sarlavha": ssar, "izoh": r[16], "elementlar": []}
            cur_b["slaydlar"].append(cur_s)
        elif r[16]:
            cur_s["izoh"] = (cur_s.get("izoh", "") + "\n" + r[16]).strip()
        if not tur:
            continue
        e = {"tur": tur, "sarlavha": r[6], "matn": r[7], "shart": r[7], "formula": r[8], "javob": r[10], "rasm": r[14], "izoh": r[15]}
        if r[9]:
            e["qadamlar"] = [x.strip() for x in r[9].split("\n") if x.strip()]
        if r[11]:
            bs = []
            for line in r[11].split("\n"):
                if not line.strip():
                    continue
                nom, _, rest = line.partition(":") if ":" in line.split("|")[0] else ("", "", line)
                parts = [p.strip() for p in rest.split("|")]
                bs.append({"nom": nom.strip(), "matn": parts[0] if parts else "", "formula": parts[1] if len(parts) > 1 else "",
                           "misol": parts[2] if len(parts) > 2 else ""})
            e["bandlar"] = bs
        if r[12]:
            lines = [ln for ln in r[12].split("\n") if ln.strip()]
            if lines:
                e["ustunlar"] = [c.strip() for c in lines[0].split("|")]
                e["qatorlar"] = [[c.strip() for c in ln.split("|")] for ln in lines[1:]]
        ch = _json(r[13])
        if ch:
            e["chizma"] = ch
        cur_s["elementlar"].append(e)
    m["bolimlar"] = bolimlar
    m["xatolar"] = [{"xato": r[0], "sabab": r[1], "togri": r[2]} for r in rows("Xatolar")]
    me = {"sarlavha": meta.get("metodika_sarlavha", ""), "tavsiya": meta.get("metodika_tavsiya", ""), "bosqichlar": [], "kartalar": []}
    for r in rows("Metodika"):
        if r[0].lower().startswith("b"):
            me["bosqichlar"].append(r[2] or r[1])
        else:
            me["kartalar"].append({"sarlavha": r[1], "matn": r[2], "chizma": _json(r[3])})
    m["metodika"] = me
    xu = {"bilaman": [], "bilishni_xohlayman": [], "bilib_oldim": [], "fikrlar": []}
    for r in rows("Xulosa"):
        for i, k in enumerate(("bilaman", "bilishni_xohlayman", "bilib_oldim", "fikrlar")):
            if r[i]:
                xu[k].append(r[i])
    m["xulosa"] = xu
    tests = []
    for r in rows("Test"):
        vs = [v for v in r[1:5] if v]
        tests.append({"savol": r[0], "variantlar": vs, "javob": r[5] or "A"})
    m["test"] = tests
    m["nazorat"] = [r[1] for r in rows("Yakun") if r[0].lower().startswith("n") and r[1]]
    m["mustaqil_ish"] = [r[1] for r in rows("Yakun") if r[0].lower().startswith("m") and r[1]]
    m["keyingi"] = {"mavzu": meta.get("keyingi_mavzu", ""), "izoh": meta.get("keyingi_izoh", "")}
    m["rasmlar"] = [{"kalit": r[0], "tavsif": r[1], "prompt": r[2]} for r in rows("Rasmlar") if r[0]]
    return [sxema.normallashtir(m)]


def shablon(namuna: dict | None = None, korsatma_matn: str = "") -> bytes:
    """Bo'sh yoki to'ldirilgan (namuna) shablon."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    m = sxema.normallashtir(namuna) if namuna else None
    wb = Workbook()
    head_fill = PatternFill("solid", fgColor="B5173A")
    head_font = Font(bold=True, color="FFFFFF")
    wrap = Alignment(wrap_text=True, vertical="top")

    def sarlavha(ws, cols, widths=None):
        ws.append(cols)
        for i, c in enumerate(cols, 1):
            cell = ws.cell(1, i)
            cell.fill = head_fill
            cell.font = head_font
            cell.alignment = Alignment(wrap_text=True, vertical="center")
            ws.column_dimensions[get_column_letter(i)].width = (widths or {}).get(i, 24)
        ws.freeze_panes = "A2"
        ws.row_dimensions[1].height = 34

    ws = wb.active
    ws.title = "Yo‘riqnoma"
    ws.column_dimensions["A"].width = 120
    yo = [
        "TAQDIMOT MIYASI — EXCEL SHABLON (talimkabutar.uz taqdimot dvigateli)",
        "",
        "1. Bitta fayl = bitta mavzu. Varaqlarni to‘ldiring, bo‘sh qoldirilgan qismlar taqdimotga chiqmaydi.",
        "2. Faqat MAZMUN yoziladi. Rang, joylashuv, animatsiya, chizmalarni dastur o‘zi qiladi (100 dan ortiq uslub).",
        "3. «Slaydlar» varag‘i: har bir qator — bitta element. «slayd sarlavhasi» to‘ldirilgan qatordan yangi slayd boshlanadi;",
        "   sarlavhasi bo‘sh qatorlar oldingi slaydga qo‘shiladi. Bitta slaydda 1–3 element.",
        "4. Element turlari: " + ", ".join(f"{k} ({v})" for k, v in sxema.ELEMENT_TURLARI.items()),
        "5. Formulalar: $...$ ichida LaTeX. Masalan: $\\frac{a}{b}$, $x^2$, $\\sqrt{x}$, $\\mathbb{Z}$, $a\\le b$.",
        "   «formula» ustunida $ belgisisiz yoziladi: \\frac{a}{b}+\\frac{c}{d}=\\frac{ad+bc}{bd}",
        "6. Belgilash: **qalin**, ==asosiy tushuncha (rangli)==.",
        "7. Chizma ustuniga JSON yoziladi. Turlar va namunalar «Chizmalar» varag‘ida.",
        "8. Rasm: «rasm kaliti» ustuniga kalit (masalan al_xorazmiy). Har bir kalit «Rasmlar» varag‘ida tavsif va prompt bilan.",
        "   Chizilgan rasm fayli aynan shu kalit bilan nomlanadi: al_xorazmiy.png (shaffof fon, 1024×1024).",
        "9. To‘ldirilgan faylni saytdagi «Taqdimot → Kuchli taqdimot → Miya yuklash» orqali yuklang.",
        "",
        "CHATGPT BILAN TO‘LDIRISH: quyidagi ko‘rsatmani ChatGPT'ga bering, oxiriga mavzuni yozing.",
        "ChatGPT JSON beradi — uni .json faylga saqlab saytga yuklang (Excel shart emas).",
        "",
    ] + (korsatma_matn.split("\n") if korsatma_matn else [])
    for line in yo:
        ws.append([line])
    ws["A1"].font = Font(bold=True, size=14, color="B5173A")
    for row in ws.iter_rows(min_row=2):
        row[0].alignment = Alignment(wrap_text=True)

    ws = wb.create_sheet("Mavzu")
    sarlavha(ws, ["maydon", "nima yoziladi", "qiymat"], {1: 22, 2: 46, 3: 90})
    mm = m["meta"] if m else {}
    extra = {}
    if m:
        extra = {"takrorlash_mavzu": m["takrorlash"]["mavzu"], "takrorlash_oyin": m["takrorlash"]["oyin"], "muammo_sarlavha": m["muammo"]["sarlavha"],
                 "muammo_goya": m["muammo"]["goya"], "muammo_zanjir": "\n".join(m["muammo"]["zanjir"]), "tarix_sarlavha": m["tarix"]["sarlavha"],
                 "tarix_xulosa": m["tarix"]["xulosa"], "metodika_sarlavha": m["metodika"]["sarlavha"], "metodika_tavsiya": m["metodika"]["tavsiya"],
                 "adabiyot_mustaqil": m["adabiyotlar"]["mustaqil"], "keyingi_mavzu": m["keyingi"]["mavzu"], "keyingi_izoh": m["keyingi"]["izoh"]}
    for k, izoh, default in META:
        if k == "tayanch":
            v = "\n".join(mm.get("tayanch") or [])
        elif k == "chizma":
            v = json.dumps(mm["chizma"], ensure_ascii=False) if mm.get("chizma") else ""
        elif k in extra:
            v = extra[k]
        else:
            v = mm.get(k, "") if m else default
        ws.append([k, izoh, v])
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = wrap

    def varaq(name, data_rows, widths=None):
        w = wb.create_sheet(name)
        sarlavha(w, VARAQLAR[name], widths)
        for r in data_rows:
            w.append(r)
        for row in w.iter_rows(min_row=2):
            for c in row:
                c.alignment = wrap
        return w

    varaq("Adabiyot", ([["asosiy", b["muallif"], b["nomi"], b["nashr"]] for b in m["adabiyotlar"]["asosiy"]] +
                       [["elektron", "", e["nomi"], e["izoh"]] for e in m["adabiyotlar"]["elektron"]]) if m else [], {3: 50, 4: 40})
    varaq("Takrorlash", [[q["savol"], q["javob"]] for q in m["takrorlash"]["savollar"]] if m else [], {1: 60, 2: 50})
    varaq("Muammo", [[q["sarlavha"], q["matn"]] for q in m["muammo"]["masalalar"]] if m else [], {2: 90})
    varaq("Tarix", [[v["davr"], v["nom"], v["matn"], v["belgi"], v["rasm"]] for v in m["tarix"]["voqealar"]] if m else [], {3: 70})
    sl_rows = []
    if m:
        for bi, b in enumerate(m["bolimlar"], 1):
            for sl in b["slaydlar"]:
                for ei, e in enumerate(sl["elementlar"]):
                    bands = "\n".join(f"{x.get('nom', '')}: {x.get('matn', '')}" + (f" | {x['formula']}" if x.get("formula") else "") +
                                      (f" | {x['misol']}" if x.get("misol") else "") for x in e.get("bandlar") or [])
                    jad = ""
                    if e.get("ustunlar"):
                        jad = "\n".join([" | ".join(e["ustunlar"])] + [" | ".join(r) for r in e.get("qatorlar") or []])
                    sl_rows.append([bi, b["nom"], b.get("izoh", ""), b.get("belgi", ""), sl["sarlavha"] if ei == 0 else "", e["tur"], e.get("sarlavha", ""),
                                    e.get("shart") or e.get("matn", ""), e.get("formula", ""), "\n".join(e.get("qadamlar") or []), e.get("javob", ""), bands, jad,
                                    json.dumps(e["chizma"], ensure_ascii=False) if e.get("chizma") else "", e.get("rasm", ""), e.get("izoh", ""),
                                    sl.get("izoh", "") if ei == 0 else ""])
            if not b["slaydlar"]:
                sl_rows.append([bi, b["nom"], b.get("izoh", ""), b.get("belgi", "")] + [""] * 13)
    varaq("Slaydlar", sl_rows, {1: 8, 2: 22, 3: 22, 4: 10, 5: 30, 6: 12, 7: 18, 8: 50, 9: 30, 10: 40, 11: 22, 12: 44, 13: 40, 14: 40, 15: 16, 16: 30, 17: 50})
    varaq("Xatolar", [[x["xato"], x["sabab"], x["togri"]] for x in m["xatolar"]] if m else [], {1: 40, 2: 50, 3: 50})
    varaq("Metodika", ([["bosqich", "", b, ""] for b in m["metodika"]["bosqichlar"]] +
                       [["karta", c["sarlavha"], c["matn"], json.dumps(c["chizma"], ensure_ascii=False) if c.get("chizma") else ""] for c in m["metodika"]["kartalar"]]) if m else [],
          {3: 60, 4: 50})
    xr = []
    if m:
        xu = m["xulosa"]
        n = max(len(xu["bilaman"]), len(xu["bilishni_xohlayman"]), len(xu["bilib_oldim"]), len(xu["fikrlar"]))
        for i in range(n):
            xr.append([(xu[k][i] if i < len(xu[k]) else "") for k in ("bilaman", "bilishni_xohlayman", "bilib_oldim", "fikrlar")])
    varaq("Xulosa", xr, {1: 40, 2: 40, 3: 40, 4: 50})
    varaq("Test", [[q["savol"]] + (q["variantlar"] + ["", "", "", ""])[:4] + ["ABCD"[q["javob"]]] for q in m["test"]] if m else [], {1: 50})
    varaq("Yakun", ([["nazorat", q] for q in m["nazorat"]] + [["mustaqil", q] for q in m["mustaqil_ish"]]) if m else [], {2: 90})
    varaq("Rasmlar", [[r["kalit"], r["tavsif"], r["prompt"], ""] for r in m.get("rasmlar", [])] if m else [], {1: 24, 2: 50, 3: 90, 4: 14})
    w = wb.create_sheet("Chizmalar")
    sarlavha(w, ["tur", "nomi", "namuna (Slaydlar → chizma ustuniga ko‘chiring)"], {1: 14, 2: 30, 3: 120})
    for k, (_fn, nom, nam) in CHIZMALAR.items():
        w.append([k, nom, json.dumps(nam, ensure_ascii=False)])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
