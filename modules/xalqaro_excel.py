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


# ─────────────────────── REV320: to'liq kontent — darslar, PISA matnlari, tuzilma, natijalar ───────────────────────
DARS_USTUN = ["dars_kod", "fan", "mavzu", "dars_sarlavha", "maqsad", "tartib", "turi", "sahna", "sarlavha", "doska", "ovoz", "savol", "javob"]
ROYXAT_USTUN = ["dars_kod", "maydon", "tartib", "matn"]
ROYXAT_MAYDON = ("tipik_xatolar", "strategiyalar", "kalit_sozlar")
TUSH_USTUN = ["dars_kod", "kalit", "tartib", "turi", "doska", "ovoz"]
BIRLIK_USTUN = ["birlik", "toplam", "nom", "asl", "stimul", "stimul_rasm"]
YOL_USTUN = ["yol", "tur", "qiymat"]
QADAM_ASOS = ("turi", "sahna", "sarlavha", "doska", "ovoz")


def _bosh(ws, ustun, kenglik=None):
    ws.append(ustun)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1B4B7A")
    ws.freeze_panes = "B2"
    for i, w in enumerate(kenglik or []):
        ws.column_dimensions[chr(65 + i)].width = w


def _yoyish(obj, yol=""):
    """Ichma-ich JSON → (yol, tur, qiymat) qatorlari. Ro'yxat indeksi «#0», lug'at kaliti — o'zi."""
    if isinstance(obj, dict):
        if not obj:
            yield yol, "dict0", ""
        for k, v in obj.items():
            yield from _yoyish(v, f"{yol}/{k}" if yol else str(k))
    elif isinstance(obj, list):
        if not obj:
            yield yol, "list0", ""
        for i, v in enumerate(obj):
            yield from _yoyish(v, f"{yol}/#{i}" if yol else f"#{i}")
    elif obj is None:
        yield yol, "null", ""
    elif isinstance(obj, bool):
        yield yol, "bool", "true" if obj else "false"
    elif isinstance(obj, (int, float)):
        yield yol, "son", obj
    else:
        yield yol, "matn", str(obj)


def _yigish(qatorlar):
    """_yoyish teskarisi."""
    root = None
    def qiymat(tur, q):
        if tur == "dict0": return {}
        if tur == "list0": return []
        if tur == "null": return None
        if tur == "bool": return str(q).strip().lower() == "true"
        if tur == "son":
            x = float(str(q).replace(",", ".")); return int(x) if x.is_integer() else x
        return "" if q is None else str(q)
    for yol, tur, q in qatorlar:
        segs = str(yol).split("/") if yol not in (None, "") else []
        if root is None:
            root = [] if segs and segs[0].startswith("#") else {}
        node = root
        for i, s in enumerate(segs):
            last = i == len(segs) - 1
            key = int(s[1:]) if s.startswith("#") else s
            nxt_list = (not last) and segs[i + 1].startswith("#")
            if isinstance(node, list):
                while len(node) <= key:
                    node.append(None)
                if last:
                    node[key] = qiymat(tur, q)
                else:
                    if node[key] is None:
                        node[key] = [] if nxt_list else {}
                    node = node[key]
            else:
                if last:
                    node[key] = qiymat(tur, q)
                else:
                    if key not in node:
                        node[key] = [] if nxt_list else {}
                    node = node[key]
    return root if root is not None else {}


def kontent_to_xlsx(kontent, til, stat_manba=None):
    """To'liq kontent (savollar, darslar, birliklar, ramka [+ uz: natijalar, davlatlar]) → bitta Excel (shu til)."""
    wb = load_workbook(io.BytesIO(json_to_xlsx(kontent.get("savollar") or [], til, stat_manba=stat_manba)))
    k = wb["KITOB"]
    k.append(("Darslar", len(kontent.get("darslar") or [])))
    k.append(("PISA matnlari", len(kontent.get("birliklar") or [])))
    ws = wb.create_sheet("DARSLAR"); _bosh(ws, DARS_USTUN, (12, 16, 10, 30, 40, 6, 10, 10, 30, 50, 70, 30, 20))
    rx = wb.create_sheet("DARS_ROYXAT"); _bosh(rx, ROYXAT_USTUN, (12, 16, 6, 70))
    tu = wb.create_sheet("TUSHUNMADIM"); _bosh(tu, TUSH_USTUN, (12, 8, 6, 10, 50, 70))
    for d in kontent.get("darslar") or []:
        for n, q in enumerate(d.get("qadamlar") or [], 1):
            ws.append([d["kod"], *(d.get(f, "") if n == 1 else "" for f in ("fan", "mavzu", "sarlavha", "maqsad")), n,
                       *(q.get(f, "") for f in QADAM_ASOS), q.get("savol", ""), q.get("javob", "")])
        for f in ROYXAT_MAYDON:
            for n, m in enumerate(d.get(f) or [], 1):
                rx.append([d["kod"], f, n, m])
        for kalit, lst in (d.get("tushunmadim") or {}).items():
            for n, e in enumerate(lst, 1):
                tu.append([d["kod"], kalit, n, e.get("turi", ""), e.get("doska", ""), e.get("ovoz", "")])
    bi = wb.create_sheet("BIRLIKLAR"); _bosh(bi, BIRLIK_USTUN, (14, 8, 30, 40, 90, 20))
    for b in kontent.get("birliklar") or []:
        bi.append([b.get(f) if b.get(f) is not None else "" for f in BIRLIK_USTUN])
    ra = wb.create_sheet("RAMKA"); _bosh(ra, YOL_USTUN, (60, 8, 70))
    for r in _yoyish(kontent.get("ramka") or {}):
        ra.append(list(r))
    if til == "uz":
        um = wb.create_sheet("UMUMIY"); _bosh(um, YOL_USTUN, (60, 8, 70))
        for nom in ("natijalar", "davlatlar"):
            for yol, tur, q in _yoyish(kontent.get(nom) or {}):
                um.append([f"{nom}/{yol}", tur, q])
    for w in (ws, tu, bi):
        for row in w.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
    y = wb["YORDAM"]
    for r in (["DARSLAR: 1 qator = darsning 1 qadami (tartib bo'yicha). fan, mavzu, dars_sarlavha, maqsad — darsning 1-qatorida."],
              ["DARS_ROYXAT: tipik_xatolar, strategiyalar, kalit_sozlar ro'yxatlari. TUSHUNMADIM: «Tushunmadim» bosilganda tushuntirishlar (q1, q2…)."],
              ["BIRLIKLAR: PISA matnlari (stimul). RAMKA: to'plamlar, mavzular, fikrlash darajalari — faqat «qiymat» ustunidagi matnni tarjima qiling, «yol» va «tur»ni o'zgartirmang."],
              ["UMUMIY (faqat o'zbekcha faylda): davlatlar natijalari va nomlari — barcha tillar uchun bitta."]):
        y.append(r)
    wb.move_sheet("YORDAM", offset=len(wb.sheetnames))
    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()


def _qatorlar(wb, nom, ustun, xato):
    if nom not in wb.sheetnames:
        return None
    rows = list(wb[nom].iter_rows(values_only=True))
    if not rows or [str(c or "").strip() for c in rows[0]][:len(ustun)] != ustun:
        xato.append(f"{nom}: ustunlar shablondagidek emas"); return []
    return [dict(zip(ustun, (("" if c is None else c) for c in r))) for r in rows[1:] if r and any(c not in (None, "") for c in r)]


def xlsx_to_kontent(data):
    """Excel → (til, kontent, xatolar, ogohlantirishlar). Kontent kalitlari: savollar [+ darslar, birliklar, ramka, natijalar, davlatlar]."""
    til, savollar, xato, ogoh = xlsx_to_json(data)
    kontent = {"savollar": savollar}
    if xato and not savollar:
        return til, kontent, xato, ogoh
    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    darsq = _qatorlar(wb, "DARSLAR", DARS_USTUN, xato)
    if darsq is not None:
        darslar, by = [], {}
        for i, z in enumerate(darsq, 2):
            kod = str(z["dars_kod"]).strip()
            if not kod:
                xato.append(f"DARSLAR {i}-qator: dars_kod bo'sh"); continue
            d = by.get(kod)
            if d is None:
                d = {"kod": kod, "mavzu": str(z["mavzu"]).strip(), "sarlavha": str(z["dars_sarlavha"]).strip(), "maqsad": str(z["maqsad"]).strip(),
                     "qadamlar": [], "tushunmadim": {}, "tipik_xatolar": [], "strategiyalar": [], "kalit_sozlar": [], "fan": str(z["fan"]).strip()}
                if not d["mavzu"] or not d["sarlavha"]:
                    xato.append(f"DARSLAR {i}-qator ({kod}): darsning 1-qatorida mavzu va dars_sarlavha bo'lishi kerak")
                by[kod] = d; darslar.append(d)
            q = {f: str(z[f]).strip() if f != "doska" and f != "ovoz" else str(z[f]) for f in QADAM_ASOS}
            q["doska"] = str(z["doska"]).strip("\n"); q["ovoz"] = str(z["ovoz"]).strip()
            if not q["turi"]:
                xato.append(f"DARSLAR {i}-qator ({kod}): qadam turi bo'sh")
            if not q["ovoz"] and not q["doska"]:
                xato.append(f"DARSLAR {i}-qator ({kod}): qadamda doska ham, ovoz ham bo'sh")
            if str(z["savol"]).strip() or str(z["javob"]).strip():
                q["savol"] = str(z["savol"]).strip(); q["javob"] = str(z["javob"]).strip()
            d["qadamlar"].append(q)
        for z in _qatorlar(wb, "DARS_ROYXAT", ROYXAT_USTUN, xato) or []:
            d = by.get(str(z["dars_kod"]).strip()); f = str(z["maydon"]).strip()
            if d is None or f not in ROYXAT_MAYDON:
                xato.append(f"DARS_ROYXAT: {z['dars_kod']} / {f} — dars yoki maydon noto'g'ri"); continue
            d[f].append(str(z["matn"]).strip())
        for z in _qatorlar(wb, "TUSHUNMADIM", TUSH_USTUN, xato) or []:
            d = by.get(str(z["dars_kod"]).strip())
            if d is None:
                xato.append(f"TUSHUNMADIM: {z['dars_kod']} — bunday dars yo'q"); continue
            d["tushunmadim"].setdefault(str(z["kalit"]).strip(), []).append(
                {"turi": str(z["turi"]).strip(), "doska": str(z["doska"]).strip("\n"), "ovoz": str(z["ovoz"]).strip()})
        kontent["darslar"] = darslar
    bq = _qatorlar(wb, "BIRLIKLAR", BIRLIK_USTUN, xato)
    if bq is not None:
        kontent["birliklar"] = [{f: (str(z[f]) if z[f] != "" else None) if f == "stimul_rasm" else str(z[f]).strip() if f != "stimul" else str(z[f])
                                 for f in BIRLIK_USTUN} for z in bq]
    rq = _qatorlar(wb, "RAMKA", YOL_USTUN, xato)
    if rq is not None:
        try:
            kontent["ramka"] = _yigish((z["yol"], str(z["tur"]).strip(), z["qiymat"]) for z in rq)
        except Exception as e:   # noqa: BLE001
            xato.append(f"RAMKA: o'qib bo'lmadi ({e}) — «yol» va «tur» ustunlarini o'zgartirmang")
    uq = _qatorlar(wb, "UMUMIY", YOL_USTUN, xato)
    if uq is not None:
        for nom in ("natijalar", "davlatlar"):
            try:
                kontent[nom] = _yigish((str(z["yol"])[len(nom) + 1:], str(z["tur"]).strip(), z["qiymat"]) for z in uq if str(z["yol"]).startswith(nom + "/"))
            except Exception as e:   # noqa: BLE001
                xato.append(f"UMUMIY ({nom}): o'qib bo'lmadi ({e})")
    return til, kontent, xato, ogoh


def kontent_mosligi(asos, boshqa):
    """Tillar orasida: savollar (mosligini_tekshir), darslar ro'yxati, PISA matnlari, tuzilma (to'plam va mavzu kalitlari)."""
    xato = mosligini_tekshir(asos.get("savollar") or [], boshqa.get("savollar") or [])
    if "darslar" in boshqa and asos.get("darslar"):
        a = {d["kod"] for d in asos["darslar"]}; b = {d["kod"] for d in boshqa["darslar"]}
        if a - b: xato.append(f"Darslar: bu tilda yo'q — {', '.join(sorted(a - b)[:6])}")
        if b - a: xato.append(f"Darslar: ortiqcha — {', '.join(sorted(b - a)[:6])}")
    if "birliklar" in boshqa and asos.get("birliklar"):
        a = {x["birlik"] for x in asos["birliklar"]}; b = {x["birlik"] for x in boshqa["birliklar"]}
        if a != b: xato.append(f"PISA matnlari ro'yxati farq qiladi ({len(a ^ b)} ta)")
    if "ramka" in boshqa and asos.get("ramka"):
        ra, rb = asos["ramka"], boshqa["ramka"]
        if set(ra.get("toplamlar", {})) != set(rb.get("toplamlar", {})): xato.append("RAMKA: to'plamlar farq qiladi")
        ka = {(t, m["kalit"]) for t, ms in ra.get("mavzular", {}).items() for m in ms}
        kb = {(t, m.get("kalit")) for t, ms in rb.get("mavzular", {}).items() for m in ms}
        if ka != kb: xato.append(f"RAMKA: mavzular farq qiladi ({len(ka ^ kb)} ta)")
    return xato
