"""REV319: «Xalqaro baholash» savollar banki — Excel shablon (5 til: uz, ru, en, de, es).

Har til — alohida Excel fayl, savol ID lari va tuzilishi BIR XIL (bir tadqiqot — natijalar va reyting umumiy).
Varaqlar:
  KITOB       — til va fayl turi
  SAVOLLAR    — 1 qator = 1 variant: savol_id, variant, toplam, mavzu, soha, fikrlash, turi, savol, rasm, A–D, togri,
                javob, javob_turi, yechim («doska || ovoz», har qadam yangi qatorda), maslahat, xato_umumiy, xato_A–D,
                kunikma, usul (kunikma/usul — savolning 1-variant qatorida)
  STATISTIKA  — tilga bog'liq bo'lmagan ma'lumot (xalqaro foiz, PISA qiyinlik, asl ball …) — o'zbekcha fayldan olinadi
  DAVLATLAR   — savol_id, davlat, foiz (davlatlar bo'yicha to'g'ri yechganlar)
  YORDAM      — to'ldirish qoidalari
Excel → JSON (hozirgi savollar.json bilan aynan bir xil tuzilma) — sayt o'zgarishsiz ishlaydi."""
import io
import re

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

TILLAR = ("uz", "ru", "en", "de", "es")
TIL_NOMI = {"uz": "O'zbekcha", "ru": "Русский", "en": "English", "de": "Deutsch", "es": "Español"}
HARF = "ABCD"
SAVOL_USTUN = ["savol_id", "variant", "toplam", "mavzu", "soha", "fikrlash", "turi", "savol", "rasm", "A", "B", "C", "D", "togri",
               "javob", "javob_turi", "yechim", "maslahat", "xato_umumiy", "xato_A", "xato_B", "xato_C", "xato_D", "kunikma", "usul"]
STAT_USTUN = ["savol_id", "asl_id", "birlik", "jarayon", "kontekst", "qiyinlik_ball", "taxminiy", "oecd_foiz", "asl_ball", "blok", "xalqaro_ortacha"]
SAVOL_DARAJA = ("toplam", "mavzu", "soha", "fikrlash", "kunikma", "usul")
STAT = STAT_USTUN[1:]
TURLAR = ("tanlov", "ochiq")


def _s(v):
    return "" if v is None else str(v)


def json_to_xlsx(savollar, til, stat_manba=None):
    """savollar.json (shu til) → Excel bayt. stat_manba — statistika va davlatlar olinadigan ro'yxat (odatda o'zbekcha)."""
    stat_manba = stat_manba or savollar
    st_by = {q["id"]: q for q in stat_manba}
    wb = Workbook()
    k = wb.active; k.title = "KITOB"
    for r in (("Fayl", "xalqaro_savollar"), ("Til *", til), ("Til nomi", TIL_NOMI.get(til, til)), ("Savollar", len(savollar))):
        k.append(r)
    ws = wb.create_sheet("SAVOLLAR"); ws.append(SAVOL_USTUN)
    for q in savollar:
        for n, v in enumerate(q.get("variantlar") or [], 1):
            jv = list(v.get("javoblar") or [])
            x = v.get("xatolar") or {}
            ws.append([q["id"], n, *(q.get(f, "") if n == 1 else "" for f in ("toplam", "mavzu", "soha", "fikrlash")),
                       v.get("turi", ""), v.get("savol", ""), _s(v.get("rasm")),
                       *(jv[i] if i < len(jv) else "" for i in range(4)),
                       HARF[v["togri"]] if v.get("turi") == "tanlov" and isinstance(v.get("togri"), int) else "",
                       v.get("javob", ""), v.get("javob_turi", ""),
                       "\n".join(f"{st.get('doska', '')} || {st.get('ovoz', '')}" for st in v.get("yechim") or []),
                       v.get("maslahat", ""), x.get("umumiy", ""), *(x.get(str(i), "") for i in range(4)),
                       q.get("kunikma", "") if n == 1 else "", q.get("usul", "") if n == 1 else ""])
    s = wb.create_sheet("STATISTIKA"); s.append(STAT_USTUN)
    d = wb.create_sheet("DAVLATLAR"); d.append(["savol_id", "davlat", "foiz"])
    for q in savollar:
        m = st_by.get(q["id"], q)
        s.append([q["id"], *(_s(m.get(f)) if m.get(f) is not None else "" for f in STAT)])
        for dav, f in (m.get("davlatlar") or {}).items():
            d.append([q["id"], dav, f])
    y = wb.create_sheet("YORDAM")
    for r in (["Qoida"], ["1 qator = 1 variant. savol_id va variant raqami BARCHA tillarda bir xil bo'lishi shart."],
              ["turi: tanlov (A–D variantlar, togri = A|B|C|D) yoki ochiq (javob: to'g'ri javoblar | bilan, masalan 15|15 ta)."],
              ["yechim: har qadam yangi qatorda — «doskada yoziladigan || ustoz aytadigan»."],
              ["xato_A … xato_D: shu noto'g'ri variant tanlansa ko'rsatiladigan izoh; xato_umumiy — ochiq savol uchun."],
              ["STATISTIKA va DAVLATLAR — tilga bog'liq emas: o'zbekcha fayldagisi ishlatiladi, boshqa tillarda o'zgartirmang."],
              ["Formulalar: $…$ (LaTeX). Rasm: fayl nomi yoki havola."]):
        y.append(r)
    for w in (ws, s, d):
        for c in w[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1B4B7A")
        w.freeze_panes = "C2" if w is ws else "B2"
    for col, wdt in zip("ABCDEFGHIJKLMNOPQRSTUVWXY", (12, 7, 10, 10, 8, 9, 8, 60, 14, 28, 28, 28, 28, 6, 14, 9, 70, 30, 30, 26, 26, 26, 26, 30, 30)):
        ws.column_dimensions[col].width = wdt
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()


def _son(v):
    if v is None or str(v).strip() == "":
        return None
    if isinstance(v, bool) or str(v).strip().lower() in ("true", "false"):
        return v if isinstance(v, bool) else str(v).strip().lower() == "true"
    try:
        x = float(str(v).replace(",", "."))
        return int(x) if x.is_integer() else x
    except ValueError:
        return str(v).strip()


def xlsx_to_json(data):
    """Excel → (til, savollar, xatolar, ogohlantirishlar). Savollar — sayt o'qiydigan JSON tuzilmasi."""
    xato, ogoh = [], []
    try:
        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except Exception as e:   # noqa: BLE001
        return None, [], [f"Faylni ochib bo'lmadi: {e}"], []
    for v in ("KITOB", "SAVOLLAR", "STATISTIKA", "DAVLATLAR"):
        if v not in wb.sheetnames:
            xato.append(f"«{v}» varag'i yo'q")
    if xato:
        return None, [], xato, ogoh
    meta = {str(r[0]).strip(): r[1] for r in wb["KITOB"].iter_rows(values_only=True) if r and r[0]}
    til = str(meta.get("Til *") or "").strip().lower()
    if til not in TILLAR:
        xato.append(f"KITOB: «Til *» uz, ru, en, de yoki es bo'lishi kerak (hozir: «{til}»)")
    rows = list(wb["SAVOLLAR"].iter_rows(values_only=True))
    head = [str(c or "").strip() for c in rows[0]] if rows else []
    if head[:len(SAVOL_USTUN)] != SAVOL_USTUN:
        xato.append("SAVOLLAR: ustunlar shablondagidek emas (ustunlarni o'chirmang va joyini almashtirmang)")
        return til, [], xato, ogoh
    savollar, by = [], {}
    for i, r in enumerate(rows[1:], 2):
        if not r or not any(c not in (None, "") for c in r):
            continue
        z = dict(zip(SAVOL_USTUN, (("" if c is None else c) for c in r)))
        sid = str(z["savol_id"]).strip()
        if not sid:
            xato.append(f"SAVOLLAR {i}-qator: savol_id bo'sh"); continue
        try:
            vn = int(z["variant"])
        except (TypeError, ValueError):
            xato.append(f"SAVOLLAR {i}-qator ({sid}): variant raqami noto'g'ri"); continue
        q = by.get(sid)
        if q is None:
            if vn != 1:
                xato.append(f"SAVOLLAR {i}-qator ({sid}): avval 1-variant qatori bo'lishi kerak"); continue
            q = {"id": sid, **{f: str(z[f]).strip() for f in SAVOL_DARAJA}, "variantlar": []}
            for f in ("toplam", "mavzu", "fikrlash"):
                if not q[f]:
                    xato.append(f"SAVOLLAR {i}-qator ({sid}): «{f}» bo'sh")
            by[sid] = q; savollar.append(q)
        elif vn != len(q["variantlar"]) + 1:
            xato.append(f"SAVOLLAR {i}-qator ({sid}): variant raqami ketma-ket emas ({vn})")
        turi = str(z["turi"]).strip()
        if turi not in TURLAR:
            xato.append(f"SAVOLLAR {i}-qator ({sid}): turi «tanlov» yoki «ochiq» bo'lishi kerak")
        savol = str(z["savol"]).strip()
        if not savol:
            xato.append(f"SAVOLLAR {i}-qator ({sid}): savol matni bo'sh")
        yechim = []
        for j, line in enumerate(str(z["yechim"] or "").splitlines(), 1):
            if not line.strip():
                continue
            if "||" not in line:
                xato.append(f"SAVOLLAR {i}-qator ({sid}): yechim {j}-qadamida «||» yo'q (doska || ovoz)"); continue
            a, b = line.split("||", 1)
            yechim.append({"doska": a.strip(), "ovoz": b.strip()})
        if not yechim:
            ogoh.append(f"SAVOLLAR {i}-qator ({sid}): yechim yo'q")
        v = {"turi": turi, "savol": savol, "rasm": str(z["rasm"]).strip() or None}
        xat = {}
        if str(z["xato_umumiy"]).strip():
            xat["umumiy"] = str(z["xato_umumiy"]).strip()
        if turi == "tanlov":
            jv = [str(z[h]).strip() for h in HARF]
            if any(not x for x in jv):
                xato.append(f"SAVOLLAR {i}-qator ({sid}): tanlov savolida A, B, C, D to'liq bo'lishi kerak")
            if len(set(jv)) < 4 and all(jv):
                xato.append(f"SAVOLLAR {i}-qator ({sid}): variantlar takrorlangan")
            tg = str(z["togri"]).strip().upper()
            if tg not in HARF:
                xato.append(f"SAVOLLAR {i}-qator ({sid}): togri A, B, C yoki D bo'lishi kerak"); tg = "A"
            v.update({"javoblar": jv, "togri": HARF.index(tg), "javob": str(z["javob"]).strip(), "javob_turi": str(z["javob_turi"]).strip()})
            for k2, h in enumerate(HARF):
                if str(z[f"xato_{h}"]).strip():
                    xat[str(k2)] = str(z[f"xato_{h}"]).strip()
        else:
            jav = str(z["javob"]).strip()
            if not jav:
                xato.append(f"SAVOLLAR {i}-qator ({sid}): ochiq savolda «javob» bo'sh")
            v.update({"javoblar": [], "togri": None, "javob": jav, "javob_turi": str(z["javob_turi"]).strip()})
        v.update({"yechim": yechim, "xatolar": xat, "maslahat": str(z["maslahat"]).strip()})
        q["variantlar"].append(v)
    # statistika va davlatlar
    st_rows = list(wb["STATISTIKA"].iter_rows(values_only=True))
    if st_rows and [str(c or "").strip() for c in st_rows[0]][:len(STAT_USTUN)] != STAT_USTUN:
        xato.append("STATISTIKA: ustunlar shablondagidek emas")
    else:
        for r in st_rows[1:]:
            if not r or not r[0]:
                continue
            q = by.get(str(r[0]).strip())
            if not q:
                ogoh.append(f"STATISTIKA: {r[0]} — SAVOLLAR'da yo'q"); continue
            for f, val in zip(STAT, r[1:]):
                val = _son(val)
                if val is not None:
                    q[f] = val
    for r in list(wb["DAVLATLAR"].iter_rows(values_only=True))[1:]:
        if not r or not r[0] or not r[1]:
            continue
        q = by.get(str(r[0]).strip())
        if q is not None:
            q.setdefault("davlatlar", {})[str(r[1]).strip()] = _son(r[2]) if _son(r[2]) is not None else "-"
    if not savollar:
        xato.append("SAVOLLAR varag'ida savol yo'q")
    return til, savollar, xato, ogoh


def mosligini_tekshir(asos, boshqa):
    """Tillar bir xil bo'lsin: savol ID lari, variantlar soni, turi, to'g'ri variant, son javoblar (asos — o'zbekcha)."""
    xato = []
    a = {q["id"]: q for q in asos}
    b = {q["id"]: q for q in boshqa}
    yoq = [k for k in a if k not in b]
    ortiq = [k for k in b if k not in a]
    if yoq:
        xato.append(f"O'zbekchada bor, bu tilda yo'q savollar: {len(yoq)} ta ({', '.join(yoq[:5])}{'…' if len(yoq) > 5 else ''})")
    if ortiq:
        xato.append(f"Bu tilda ortiqcha savollar (o'zbekchada yo'q): {', '.join(ortiq[:5])}")
    for k in a:
        if k not in b:
            continue
        va, vb = a[k]["variantlar"], b[k]["variantlar"]
        if len(va) != len(vb):
            xato.append(f"{k}: variantlar soni farq qiladi ({len(va)} va {len(vb)})"); continue
        for n, (x, y) in enumerate(zip(va, vb), 1):
            if x["turi"] != y["turi"]:
                xato.append(f"{k} {n}-variant: turi farq qiladi")
            elif x["turi"] == "tanlov" and x.get("togri") != y.get("togri"):
                xato.append(f"{k} {n}-variant: to'g'ri javob farq qiladi ({HARF[x['togri']]} va {HARF[y['togri']]})")
            elif x["turi"] == "ochiq":
                sa = re.findall(r"-?\d+(?:[.,]\d+)?", str(x.get("javob", "")).split("|")[0])
                sb = re.findall(r"-?\d+(?:[.,]\d+)?", str(y.get("javob", "")).split("|")[0])
                if sa and sb and sa[0].replace(",", ".") != sb[0].replace(",", "."):
                    xato.append(f"{k} {n}-variant: son javob farq qiladi ({sa[0]} va {sb[0]})")
        for f in ("toplam", "mavzu", "fikrlash"):
            if a[k].get(f) != b[k].get(f):
                xato.append(f"{k}: «{f}» farq qiladi")
    return xato
