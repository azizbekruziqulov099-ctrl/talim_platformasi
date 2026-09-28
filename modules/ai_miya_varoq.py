"""AI miya: MAVZU VAROQLI shablon — BIR VAROQ = BIR MAVZU.

  KITOB        — kitob haqida (yorliq : qiymat) + «Kod prefiksi».
  <mavzu>      — har mavzu alohida varaqda. Tepada mavzu kodi/nomi, pastda qatorlar:
                 1-qator — 1-tushuncha, 2-qator — 2-tushuncha ... tushuntirish tugagach
                 amaliy qism: misol / masala / topshiriq / test (turi «Turi» ustunida).
  NAMUNA...    — «NAMUNA» bilan boshlangan varaqlar import qilinmaydi.

Har misol, masala, topshiriq va testga KITOB KODI beriladi (masalan XB-03-A01). Kod kitobda
topshiriq yonida bosiladi; o'quvchi kodni saytga/ilovaga kiritsa — yechim AI doskada chiqadi.
Kod ustuni bo'sh bo'lsa, avtomatik yaratiladi: <prefiks>-<mavzu raqami>-<harf><tartib>.
Qisqa yozilsa (A01) — oldiga prefiks va mavzu raqami qo'shiladi.

Natija ichki 12 varaqli tuzilmaga aylantiriladi — import, nashr va dars xonasi o'zgarmaydi.
Tushuncha qatori → dars qadami (doska + ovoz) + «Tushunmadim» variantlari;
misol/masala/topshiriq → «amaliy» qadam (sharti ko'rinadi, yechimi keyin ochiladi);
test → 06_MASHQLAR (nashrdan keyin Test bo'limiga ham tushadi).
"""
import re

from modules.ai_miya_oddiy import (
    BOOK_FIELDS as SIMPLE_BOOK_FIELDS, IMAGE_TYPES, KITOB_SHEET, _embedded_images, _int, _norm, _result, _t,
    split_solution,
)

NAMUNA_PREFIX = "NAMUNA"
BOOK_FIELDS = SIMPLE_BOOK_FIELDS + [
    ("kod_prefiksi", "Kod prefiksi", "Kitobdagi topshiriq kodlarining boshi, 2–4 lotin harf. Masalan XB → XB-03-A01"),
]
META_FIELDS = [
    ("mavzu_kodi", "Mavzu kodi (DTS)", "Mavzular bazasidagi kod. Bo'sh qolsa — mavzu nomi bo'yicha bazadan topiladi."),
    ("mavzu_nomi", "Mavzu nomi *", "Bazadagi mavzu nomi bilan bir xil yozing."),
    ("mavzu_raqami", "Mavzu raqami (kod uchun)", "Kitobdagi tartib raqami: 3 → kodlar XB-03-..."),
    ("daraja", "Daraja (1–30)", "Qiyinlik darajasi."),
]
# (kalit, sarlavha, kenglik, izoh)
COLUMNS = [
    ("tartib", "№", 5, ""),
    ("turi", "Turi *", 12, "tushuncha, misol, masala, topshiriq, test, xulosa yoki kirish"),
    ("kod", "Kitob kodi", 13, "Faqat misol/masala/topshiriq/test uchun. Bo'sh qolsa avtomatik: XB-03-A01"),
    ("sarlavha", "Sarlavha *", 26, "Tushuncha nomi yoki topshiriq nomi. Doskaning tepasida chiqadi."),
    ("matn", "Tushuntirish yoki shart *", 60, "Tushunchada — o'qituvchi aytadigan matn ([1], [2] — doska qatorlari). Amaliyda — topshiriq sharti yoki test savoli."),
    ("doska", "Doskaga yoziladi", 34, "Har yangi satr (Alt+Enter) — doskada alohida qator. Formula: $\\frac{3}{8}$"),
    ("rasm", "Rasm", 14, "Rasmni katakka qo'ying yoki fayl nomini yozib, Excel + rasmlarni ZIP qiling."),
    ("variantlar", "Test variantlari", 30, "Har satrda bitta: A) ...  B) ...  C) ...  D) ..."),
    ("javob", "To'g'ri javob", 12, "Testda harf (B). Masalada qisqa javob, bir nechta bo'lsa | bilan: 2/6|1/3"),
    ("yechim", "Yechim (keyin ochiladi)", 50, "Har satr — bitta qadam. «doskaga || o'qituvchi aytadi» deb yozish mumkin."),
    ("sodda", "Tushunmadim: soddaroq", 30, "Faqat tushuncha qatori uchun."),
    ("boshqa_usul", "Tushunmadim: boshqa usulda", 30, "Faqat tushuncha qatori uchun."),
    ("sahifa", "Sahifa", 8, ""),
]
TYPE_ALIASES = {
    "tushuncha": "tushuncha", "tushuntirish": "tushuncha", "nazariya": "tushuncha", "qoida": "tushuncha",
    "kirish": "kirish", "misol": "misol", "ishlanganmisol": "misol", "namuna": "misol",
    "masala": "masala", "topshiriq": "topshiriq", "amaliy": "topshiriq", "mashq": "topshiriq",
    "amaliymashgulot": "topshiriq", "vazifa": "topshiriq", "test": "test", "xulosa": "xulosa",
}
PRACTICE = ("misol", "masala", "topshiriq", "test")
TYPE_NAMES = {"misol": "Misol", "masala": "Masala", "topshiriq": "Topshiriq", "test": "Test"}
AUTO_LETTER = {"misol": "M", "masala": "S", "topshiriq": "A", "test": "T"}
MAX_VOICE = 1500
CHUNK = 1300
CODE_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$")


def kod_norm(value):
    """Qidiruv uchun: katta harf, faqat harf va raqam (XB-03-A01 = xb03a01)."""
    return re.sub(r"[^A-Z0-9]", "", _t(value).upper())


def is_sheet_workbook(wb):
    return KITOB_SHEET in wb.sheetnames and "MAVZULAR" not in wb.sheetnames and any(
        _find_header(wb[name]) for name in wb.sheetnames if name != KITOB_SHEET)


def _find_header(ws):
    by_label = {_norm(label): key for key, label, _, _ in COLUMNS}
    by_label.update({_norm(key): key for key, _, _, _ in COLUMNS})
    for row in range(1, min(ws.max_row, 15) + 1):
        found = {}
        for col in range(1, min(ws.max_column, 40) + 1):
            key = by_label.get(_norm(ws.cell(row, col).value))
            if key and key not in found:
                found[key] = col
        if "turi" in found and "matn" in found:
            return row, found
    return None


def _prefix(book):
    raw = re.sub(r"[^A-Z0-9]", "", _t(book.get("kod_prefiksi")).upper())
    if raw:
        return raw[:6]
    words = re.findall(r"[A-Za-z]+", (book.get("kitob_nomi") or book.get("fan") or "KB").replace("‘", "").replace("’", "").replace("'", ""))
    if len(words) == 1:
        return words[0][:2].upper()
    return ("".join(w[0] for w in words[:2]).upper() or "KB")[:4]


def split_voice(text, board_lines):
    """Uzun tushuntirishni ≤1300 belgili bo'laklarga bo'ladi; doska qatorlari [n] belgisi
    tushgan bo'lakka o'tadi va har bo'lakda 1 dan qayta raqamlanadi. -> [(ovoz, doska)]"""
    text = _t(text)
    if len(text) <= MAX_VOICE:
        return [(text, "\n".join(board_lines))]
    sentences = re.split(r"(?<=[.!?:;])\s+", text)
    chunks, cur = [], ""
    for s in sentences:
        while len(s) > CHUNK:
            cut = s.rfind(" ", 0, CHUNK)
            cut = cut if cut > 200 else CHUNK
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(s[:cut].strip())
            s = s[cut:].strip()
        if cur and len(cur) + 1 + len(s) > CHUNK:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    used, result = set(), []
    for i, chunk in enumerate(chunks):
        lines = []

        def renumber(m):
            n = int(m.group(1))
            if n in used or not 1 <= n <= len(board_lines):
                return ""
            used.add(n)
            lines.append(board_lines[n - 1])
            return f"[{len(lines)}]"
        voice = re.sub(r"\[(\d{1,2})\]", renumber, chunk)
        result.append([voice.strip(), lines])
    rest = [line for n, line in enumerate(board_lines, 1) if n not in used]
    if rest:
        result[0][1] = result[0][1] + rest
    return [(v, "\n".join(lines)) for v, lines in result]


def parse_options(text):
    """«A) ... B) ...» (satrlarda yoki bir qatorda) -> ['...', '...']"""
    text = _t(text)
    if not text:
        return []
    parts = re.split(r"(?:^|\s|\n)([A-Ea-e])\)\s*", "\n" + text)
    options = []
    for i in range(1, len(parts) - 1, 2):
        options.append(parts[i + 1].strip().rstrip(";").strip())
    if not options:
        options = [x.strip() for x in text.split("\n") if x.strip()]
    return options


def parse_sheets(wb, media_names=None, max_images=500):
    media_names = {m.lower() for m in (media_names or set())}
    errors, warnings = [], []

    def err(sheet, row, column, message, severity="error"):
        (errors if severity == "error" else warnings).append(
            {"sheet": sheet, "row": row, "column": column, "message": message, "severity": severity})

    book, rows = {}, {}
    ws = wb[KITOB_SHEET]
    labels = {_norm(label): key for key, label, _ in BOOK_FIELDS}
    for row in range(1, min(ws.max_row, 60) + 1):
        key = labels.get(_norm(ws.cell(row, 1).value))
        if key:
            book[key] = _t(ws.cell(row, 2).value)
            rows[key] = row
    for key, label, _ in BOOK_FIELDS[:3]:
        if not book.get(key):
            err(KITOB_SHEET, rows.get(key, 1), label.rstrip(" *"), "To'ldirilishi shart")
    source_id = book.get("kitob_kodi") or re.sub(
        r"[^A-Za-z0-9]+", "-", f"KITOB-{book.get('fan', '')}-{book.get('sinf', '')}-{book.get('kitob_nomi', '')}").strip("-")[:80]
    prefix = _prefix(book)

    payload = {name: [] for name in ("01_KITOB", "02_DTS_XARITA", "03_BILIM", "04_TUSHUNTIRISH", "05_MISOLLAR",
                                     "06_MASHQLAR", "07_YORDAM_XATOLAR", "08_METODIKA", "09_TOGARAK",
                                     "10_LUGAT_MEDIA", "11_DARS_SSENARIY", "12_TUSHUNMADIM")}
    payload["01_KITOB"].append({
        "source_id": source_id, "kitob_nomi": book.get("kitob_nomi", ""), "fan": book.get("fan", ""),
        "sinf": book.get("sinf", ""), "til": book.get("til") or "uz", "nashr_yili": book.get("nashr_yili", ""),
        "mualliflar": book.get("mualliflar", ""), "nashriyot": book.get("nashriyot", ""), "isbn": book.get("isbn", ""),
        "manba_turi": "darslik", "fayl_nomi": "", "sahifa_boshlanish": "", "sahifa_tugash": "",
        "litsenziya": "", "izoh": "", "import_qilinsin": "ha", "_excel_row": 2, "kod_prefiksi": prefix,
    })
    media, by_name, codes_seen, code_list = {}, {}, {}, []
    label_of = {key: label.rstrip(" *") for key, label, _, _ in COLUMNS}
    topic_sheets = 0

    for sheet_index, name in enumerate(wb.sheetnames):
        if name == KITOB_SHEET or name.upper().startswith(NAMUNA_PREFIX):
            continue
        ws = wb[name]
        found = _find_header(ws)
        if not found:
            continue
        header_row, header = found
        meta = {}
        meta_labels = {_norm(label): key for key, label, _ in META_FIELDS}
        meta_labels.update({_norm(key): key for key, _, _ in META_FIELDS})
        meta_rows = {}
        for r in range(1, header_row):
            for c in range(1, min(ws.max_column, 12)):
                key = meta_labels.get(_norm(ws.cell(r, c).value))
                if key and key not in meta:
                    meta[key] = _t(ws.cell(r, c + 1).value)
                    meta_rows[key] = r
        embedded = _embedded_images(ws)
        data_rows = [r for r in range(header_row + 1, ws.max_row + 1)
                     if any(_t(ws.cell(r, col).value) for col in header.values() if col != header.get("tartib"))
                     or any(er == r for er, _ in embedded)]
        topic_name = meta.get("mavzu_nomi", "")
        code = meta.get("mavzu_kodi", "")
        if not data_rows:
            if topic_name or code:
                err(name, header_row + 1, "", "Mavzu varag'i bo'sh — o'tkazib yuborildi (to'ldirilgach qayta yuklang)", "warning")
            continue
        topic_sheets += 1
        if not topic_name:
            err(name, meta_rows.get("mavzu_nomi", 2), "Mavzu nomi", "Mavzu nomini yozing")
        if not code:
            if not topic_name:
                continue
            code = f"@@NOM{len(by_name) + 1}@@"
            by_name[code] = {"nom": topic_name, "sheet": name, "row": meta_rows.get("mavzu_nomi", 2)}
        number = _int(meta.get("mavzu_raqami")) or topic_sheets
        level = _int(meta.get("daraja"))
        if meta.get("daraja") and (level is None or not 1 <= level <= 30):
            err(name, meta_rows.get("daraja", 4), "Daraja", "Daraja 1 dan 30 gacha butun son bo'lishi kerak")
            level = None
        steps, variants, pages, counters = [], [], [], {}

        def cell(row, key):
            col = header.get(key)
            return _t(ws.cell(row, col).value) if col else ""

        def picture(row, key):
            value = cell(row, key)
            col = header.get(key)
            if col and (row, col) in embedded:
                ext, data = embedded[(row, col)]
                value = value or f"{prefix}_{re.sub(r'[^A-Za-z0-9]+', '_', name)}_{row}_{col}.{ext}"
                if len(media) < max_images:
                    media[value] = (IMAGE_TYPES[ext], data)
            elif value and value.lower() not in media_names and not value.startswith("https://"):
                err(name, row, label_of[key], f"«{value}» rasmi topilmadi: rasmni katakka qo'ying yoki shu nomli faylni ZIP ichiga qo'shing", "warning")
            return value

        def add_step(row, kind, board, voice, title="", media_id="", scene=None, answer="", extra=None):
            n = len(steps) + 1
            step_id = f"{code}#S{n}"
            item = {
                "step_id": step_id, "topic_code": code, "tartib": str(n), "qadam_turi": kind,
                "sahna": scene or step_id, "sarlavha": title, "doska_matni": board, "ovoz_matni": voice,
                "media_id": media_id, "oquvchi_savoli": "Javobingizni yozing" if answer else "",
                "kutilgan_javob": answer, "javob_izohi": "", "daraja_1_30": str(level or ""),
                "source_id": source_id, "sahifa": cell(row, "sahifa"), "status": "", "import_qilinsin": "ha",
                "_excel_row": row, "_sheet": name,
            }
            item.update(extra or {})
            steps.append(item)
            return item

        def book_code(row, kind):
            raw = _t(cell(row, "kod")).upper().replace(" ", "")
            counters[kind] = counters.get(kind, 0) + 1
            if not raw:
                raw = f"{AUTO_LETTER[kind]}{counters[kind]:02d}"
            if not raw.startswith(prefix + "-") and "-" not in raw:
                raw = f"{prefix}-{number:02d}-{raw}"
            if not CODE_RE.match(raw) or len(raw) > 24:
                err(name, row, label_of["kod"], "Kod faqat lotin harf, raqam va «-» dan iborat bo'lsin (24 belgigacha), masalan XB-03-A01")
                return ""
            key = kod_norm(raw)
            if key in codes_seen:
                err(name, row, label_of["kod"], f"«{raw}» kodi takrorlangan ({codes_seen[key]} bilan)")
                return ""
            codes_seen[key] = f"«{name}» {row}-qator"
            code_list.append({"kod": raw, "turi": kind, "mavzu": topic_name, "sarlavha": cell(row, "sarlavha"),
                              "sheet": name, "row": row})
            return raw

        for row in data_rows:
            c = {key: cell(row, key) for key in header}
            kind = TYPE_ALIASES.get(_norm(c.get("turi")).replace("'", ""))
            if not kind:
                err(name, row, label_of["turi"], "Turini tanlang: tushuncha, misol, masala, topshiriq, test, xulosa yoki kirish")
                continue
            if _int(c.get("sahifa")):
                pages.append(_int(c["sahifa"]))
            title = c.get("sarlavha") or ""
            text = c.get("matn") or ""
            if kind == "kirish":
                if text:
                    add_step(row, "kirish", c.get("doska") or text, text[:MAX_VOICE], title or topic_name)
                continue
            if kind == "xulosa":
                board = c.get("doska") or text
                if board:
                    add_step(row, "xulosa", board, ("Esda tut: " + text)[:MAX_VOICE], title or "Esda tut")
                continue
            if kind == "tushuncha":
                if not text and not c.get("doska"):
                    err(name, row, label_of["matn"], "Tushuntirish yoki doska matnini yozing")
                    continue
                if not title:
                    err(name, row, label_of["sarlavha"], "Tushuncha nomini yozing (doskaning sarlavhasi)", "warning")
                title = title or topic_name
                board_lines = [x.strip() for x in c.get("doska", "").split("\n") if x.strip()]
                markers = {int(m) for m in re.findall(r"\[(\d{1,2})\]", text)}
                if markers and max(markers) > len(board_lines):
                    err(name, row, label_of["matn"], f"[{max(markers)}] belgisi bor, lekin doskada {len(board_lines)} ta qator bor", "warning")
                pieces = split_voice(text or c.get("doska", ""), board_lines)
                pic = picture(row, "rasm")
                first = None
                for i, (voice, board) in enumerate(pieces):
                    st = add_step(row, "qoida" if board else "tushuntirish", board, voice, title if i == 0 else "",
                                  pic if i == 0 else "", first["sahna"] if first else None)
                    first = first or st
                for key, vkind in (("sodda", "sodda"), ("boshqa_usul", "boshqa_usul")):
                    if c.get(key):
                        variants.append({
                            "variant_id": f"{code}#V{len(variants) + 1}", "topic_code": code, "step_id": first["step_id"],
                            "variant_turi": vkind, "tugma_nomi": "", "doska_matni": "", "ovoz_matni": c[key][:MAX_VOICE],
                            "media_id": "", "takrorlash_topic_code": "", "status": "", "import_qilinsin": "ha", "_excel_row": row,
                        })
                payload["03_BILIM"].append({
                    "content_id": first["step_id"].replace("#S", "#B"), "topic_code": code,
                    "content_type": "qoida" if board_lines else "tushuntirish", "sarlavha": title,
                    "mazmun": re.sub(r"\[\d{1,2}\]", "", text or c.get("doska", "")).strip(),
                    "qisqa_xulosa": "", "formula_latex": c.get("doska", ""), "muhimlik": "asosiy",
                    "yosh_min": "", "yosh_max": "", "sahifa": c.get("sahifa", ""), "source_id": source_id, "status": "",
                    "import_qilinsin": "ha", "_excel_row": row,
                })
                continue

            # ── amaliy qism ──
            if not text:
                err(name, row, label_of["matn"], f"{TYPE_NAMES[kind]} shartini yozing")
                continue
            options = parse_options(c.get("variantlar"))
            letter = _t(c.get("javob")).upper().rstrip(").")[:1] if kind == "test" else ""
            if kind == "test" and (len(options) != 4 or letter not in ("A", "B", "C", "D")):
                if len(options) != 4:
                    err(name, row, label_of["variantlar"], f"Testda aynan 4 ta variant (A–D) bo'lsin — {len(options)} ta topildi. Test bo'limiga tushmaydi, «masala» sifatida saqlanadi", "warning")
                else:
                    err(name, row, label_of["javob"], "Test javobi A, B, C yoki D harfi bo'lsin")
                    continue
                kind = "masala"
            kod = book_code(row, kind)
            if not kod:
                continue
            if not c.get("yechim") and not c.get("javob"):
                err(name, row, label_of["yechim"], f"{kod}: yechim yoki javob yozilmagan — kod kiritilganda faqat shart chiqadi", "warning")
            pic = picture(row, "rasm")
            if kind == "test":
                payload["06_MASHQLAR"].append({
                    "task_id": f"{code}#T{len(payload['06_MASHQLAR']) + 1}", "topic_code": code, "vazifa_turi": "single_choice",
                    "daraja": "", "savol": text, "variant_a": options[0], "variant_b": options[1], "variant_c": options[2],
                    "variant_d": options[3], "togri_javob": letter, "javob_mezoni": "", "izoh": c.get("yechim", ""),
                    "vaqt_soniya": "60", "ball": "1", "rol_maqsadi": "test,mashq", "source_id": source_id,
                    "sahifa": c.get("sahifa", ""), "status": "", "import_qilinsin": "ha", "_excel_row": row,
                    "kitob_kodi": kod, "sarlavha": title, "media_id": pic,
                })
                continue
            intro = {"misol": "Endi misolni ko'ramiz", "masala": "Endi masala", "topshiriq": "Endi amaliy topshiriq"}[kind]
            voice = f"{intro}: {title}. " if title else f"{intro}. "
            voice += (text + " ") if len(text) <= 600 else "Shartni doskadan diqqat bilan o'qing. "
            voice += "Avval o'zingiz bajarib ko'ring, yechimni keyin ochasiz."
            add_step(row, "amaliy", text, voice[:MAX_VOICE], f"{TYPE_NAMES[kind]} · {title}" if title else TYPE_NAMES[kind],
                     pic, answer=c.get("javob", "") if not options else "", extra={
                         "kitob_kodi": kod, "amaliy_turi": kind, "yechim": c.get("yechim", ""),
                         "variantlar": "\n".join(f"{'ABCDE'[i]}) {o}" for i, o in enumerate(options[:5])),
                         "togri_javob": _t(c.get("javob")),
                     })

        if not steps and not any(t["topic_code"] == code for t in payload["06_MASHQLAR"]):
            err(name, data_rows[0], "", "Mavzu varag'ida birorta tushuncha yoki topshiriq topilmadi")
            continue
        if not any(s["qadam_turi"] in ("qoida", "tushuntirish") for s in steps):
            err(name, data_rows[0], label_of["turi"], "Mavzuda «tushuncha» qatori yo'q — dars faqat amaliy qismdan iborat bo'ladi", "warning")
        payload["02_DTS_XARITA"].append({
            "topic_code": code, "source_id": source_id, "fan": book.get("fan", ""), "sinf": book.get("sinf", ""),
            "chorak": "", "bob": "", "bolim": "", "mavzu": topic_name, "kichik_mavzu": "",
            "sahifa_boshlanish": str(min(pages)) if pages else "", "sahifa_tugash": str(max(pages)) if pages else "",
            "oquv_maqsadi": "", "tayanch_bilimlar": "", "natija_mezoni": "", "status": "",
            "daraja_1_30": str(level or ""), "import_qilinsin": "ha", "_excel_row": meta_rows.get("mavzu_kodi", 2),
            "_sheet": name,
        })
        payload["11_DARS_SSENARIY"].extend(steps)
        payload["12_TUSHUNMADIM"].extend(variants)

    if not payload["02_DTS_XARITA"] and not any(e["sheet"] != KITOB_SHEET for e in errors):
        err(KITOB_SHEET, 1, "", "Birorta to'ldirilgan mavzu varag'i topilmadi (NAMUNA varaqlari hisobga olinmaydi)")
    result = _result(payload, errors, warnings, media)
    result["summary"]["format"] = "varoqli"
    result["summary"]["kitob_kodlari"] = len(code_list)
    result["summary"]["kod_prefiksi"] = prefix
    result["summary"]["testlar"] = len(payload["06_MASHQLAR"])
    result["kodlar"] = code_list
    if by_name:
        result["nom_boyicha"] = by_name
    return result


# ───────────────────────────── shablon ─────────────────────────────
SAMPLE_META = {"mavzu_kodi": "NAMUNA-5-01", "mavzu_nomi": "Oddiy kasr", "mavzu_raqami": "3", "daraja": "5"}
SAMPLE_ROWS = [
    {"turi": "tushuncha", "sarlavha": "Surat va maxraj",
     "matn": "Butunni teng bo'laklarga bo'lamiz. [1] Pastdagi son — maxraj: butun nechta teng bo'lakka bo'linganini bildiradi. [2] Tepadagi son — surat: nechta bo'lak olinganini bildiradi.",
     "doska": "Maxraj — jami teng bo'laklar\nSurat — olingan bo'laklar", "rasm": "pitsa_8.png",
     "sodda": "Nonni nechta bo'lakka kessang, o'sha son maxraj. Nechtasini olsang — surat.",
     "boshqa_usul": "Sonlar nurini 0 dan 1 gacha 8 ga bo'lamiz va 3-bo'linmaga boramiz: 3/8.", "sahifa": "43"},
    {"turi": "tushuncha", "sarlavha": "Kasrni o'qish",
     "matn": "Kasrni o'qishda avval maxraj, keyin surat aytiladi. [1] Uch sakkizdan deymiz. [2] Besh yettidan deymiz.",
     "doska": "$\\frac{3}{8}$ — uch sakkizdan\n$\\frac{5}{7}$ — besh yettidan", "sahifa": "44"},
    {"turi": "xulosa", "sarlavha": "Esda tut", "matn": "Surat — olingan bo'laklar, maxraj — jami bo'laklar.", "doska": "Surat — olingan, maxraj — jami"},
    {"turi": "misol", "kod": "M01", "sarlavha": "Kasrni yozish", "matn": "8 bo'lakdan 3 tasi olindi. Kasrni yozing.",
     "yechim": "Maxraj = 8 || Jami sakkiz bo'lak — maxrajga sakkiz yozamiz.\nSurat = 3 || Uch bo'lak olindi — suratga uch.\n$\\frac{3}{8}$ || Javob: uch sakkizdan.", "sahifa": "44"},
    {"turi": "masala", "kod": "S01", "sarlavha": "Bo'yalgan qism", "matn": "6 bo'lakdan 2 tasi bo'yalgan. Kasrni yozing.", "javob": "2/6|1/3",
     "yechim": "Jami 6 bo'lak — maxraj 6\nBo'yalgan 2 — surat 2\n$\\frac{2}{6}=\\frac{1}{3}$"},
    {"turi": "topshiriq", "kod": "A01", "sarlavha": "Kasr izla", "matn": "Uyingizdagi 3 ta narsani teng bo'laklarga bo'ling va olingan qismni kasr bilan yozing.",
     "yechim": "Masalan: olma 4 bo'lak, 1 tasi yeyildi — 1/4\nJavobda jami va olingan bo'lak aniq ko'rsatilsin"},
    {"turi": "test", "kod": "T01", "sarlavha": "Maxraj", "matn": "$\\frac{5}{9}$ kasrning maxraji nechiga teng?",
     "variantlar": "A) 5\nB) 9\nC) 14\nD) 4", "javob": "B", "yechim": "Maxraj — pastdagi son: 9."},
]


def safe_sheet_name(title, used):
    name = re.sub(r"\s+", " ", re.sub(r"[\[\]:*?/\\']+", " ", _t(title))).strip()[:31].strip() or "Mavzu"
    base, n = name, 2
    while name.lower() in used:
        suffix = f" ({n})"
        name = base[:31 - len(suffix)] + suffix
        n += 1
    used.add(name.lower())
    return name


def template_workbook(prefill=None, book=None, blank_topics=3):
    """prefill — [{mavzu_kodi, mavzu_nomi, dars_bor}] — har biri alohida varaq bo'ladi."""
    import openpyxl
    from openpyxl.comments import Comment
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.worksheet.datavalidation import DataValidation

    navy, input_fill, sample_fill, line = "173B57", "FFF4CC", "EEF1F4", "D5DBE1"
    thin = Side(style="thin", color=line)
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = KITOB_SHEET
    ws.sheet_view.showGridLines = False
    for col, width in (("A", 24), ("B", 44), ("C", 62)):
        ws.column_dimensions[col].width = width
    ws["A1"] = "1-QADAM. KITOB HAQIDA"
    ws["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=navy)
    ws.merge_cells("A1:C1")
    ws.row_dimensions[1].height = 30
    for i, (key, label, hint) in enumerate(BOOK_FIELDS, 3):
        ws.cell(i, 1, label).font = Font(bold=True)
        value = ws.cell(i, 2)
        if book and book.get(key):
            value.value = book[key]
        value.fill = PatternFill("solid", fgColor=input_fill)
        value.border = border
        ws.cell(i, 3, hint).font = Font(color="6B7785", italic=True)
    help_row = len(BOOK_FIELDS) + 5
    ws.cell(help_row, 1, "QANDAY TO'LDIRILADI").font = Font(size=13, bold=True, color=navy)
    steps = [
        "1. Bitta fayl = bitta kitob. BIR VAROQ = BIR MAVZU: har mavzu o'z varag'ida (pastdagi yorliqlar).",
        "2. Varaq tepasida mavzu kodi va nomi. Kod bo'sh bo'lsa, mavzu Mavzular bazasidan nomi bo'yicha topiladi.",
        "3. Qatorlar tartibi = dars tartibi: 1-qator — 1-tushuncha, 2-qator — 2-tushuncha ... (Turi: tushuncha).",
        "4. Tushuntirish tugagach amaliy qism: Turi — misol, masala, topshiriq yoki test. Sharti ko'rinadi, yechimi keyin ochiladi.",
        "5. KITOB KODI: har misol/masala/topshiriq/testga kod beriladi (XB-03-A01). Kodni kitobda topshiriq yonida bosing — o'quvchi kodni ilovaga kiritsa, yechim AI doskada chiqadi. Bo'sh qolsa kod avtomatik yaratiladi.",
        "6. Doska: har yangi satr (Alt+Enter) — alohida qator. Tushuntirishda [1], [2] qo'ysangiz — o'qituvchi shu joyga yetganda o'sha qator yoziladi.",
        "7. Yechim: har satr — bitta qadam. «doskaga || o'qituvchi aytadi» deb yozish mumkin.",
        "8. Test: 4 ta variant (A–D) va to'g'ri javob harfi. Testlar Test bo'limiga ham tushadi.",
        "9. «NAMUNA» varag'i import qilinmaydi — ko'rib, xuddi shunday to'ldiring. Saytda: Tekshirish → Qoralama import → Nashr.",
    ]
    for i, text in enumerate(steps, help_row + 1):
        ws.cell(i, 1, text)
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=3)
        ws.cell(i, 1).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[i].height = 34

    def topic_sheet(title, meta, rows=(), sample=False, dars_bor=False):
        sh = wb.create_sheet(title)
        sh.sheet_properties.tabColor = "8A94A0" if sample else "2F7D5B"
        sh.freeze_panes = "E7"
        sh["A1"] = "NAMUNA — import qilinmaydi" if sample else "MAVZU VAROG'I — bir varaq = bir mavzu"
        sh["A1"].font = Font(size=14, bold=True, color="FFFFFF")
        sh["A1"].fill = PatternFill("solid", fgColor="6B7785" if sample else navy)
        sh.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(COLUMNS))
        sh.row_dimensions[1].height = 26
        for i, (key, label, hint) in enumerate(META_FIELDS):
            r, c = (2 + i // 2, 1 + (i % 2) * 5)
            sh.cell(r, c, label).font = Font(bold=True)
            sh.cell(r, c).comment = Comment(hint, "Kabutar")
            v = sh.cell(r, c + 1, meta.get(key, ""))
            sh.merge_cells(start_row=r, start_column=c + 1, end_row=r, end_column=c + 3)
            v.fill = PatternFill("solid", fgColor=sample_fill if sample else ("E6F2EC" if key in ("mavzu_kodi", "mavzu_nomi") and meta.get(key) else input_fill))
            v.border = border
            v.font = Font(bold=key in ("mavzu_kodi", "mavzu_nomi"))
        if dars_bor:
            sh.cell(2, 2).comment = Comment("Bu mavzuda nashr qilingan dars bor. Qayta yuklasangiz, yangi versiya bo'lib almashadi.", "Kabutar")
        sh.cell(4, 1, "Tartib: avval tushunchalar (1-qator — 1-tushuncha ...), keyin misol / masala / topshiriq / test. Yechim o'quvchiga keyin ochiladi.").font = Font(italic=True, color="6B7785")
        sh.merge_cells(start_row=4, start_column=1, end_row=4, end_column=len(COLUMNS))
        header_row = 6
        for col, (key, label, width, hint) in enumerate(COLUMNS, 1):
            cell = sh.cell(header_row, col, label)
            cell.font = Font(bold=True, color="FFFFFF")
            group = "2F7D5B" if key in ("kod", "variantlar", "javob", "yechim") else "A0662B" if key in ("sodda", "boshqa_usul") else "2D6E8B"
            cell.fill = PatternFill("solid", fgColor=group)
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
            if hint:
                cell.comment = Comment(hint, "Kabutar")
            sh.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width
        sh.row_dimensions[header_row].height = 36
        keys = [k for k, *_ in COLUMNS]
        total = max(len(rows) + 10, 40)
        for i in range(total):
            r = header_row + 1 + i
            data = rows[i] if i < len(rows) else {}
            for col, key in enumerate(keys, 1):
                value = data.get(key, "")
                if key == "tartib":
                    value = i + 1
                c = sh.cell(r, col, value if value != "" else None)
                c.alignment = Alignment(vertical="top", wrap_text=True)
                c.border = border
                if sample:
                    c.fill = PatternFill("solid", fgColor=sample_fill)
                    c.font = Font(italic=True, color="4A5563")
            if data:
                sh.row_dimensions[r].height = min(300, 30 + 15 * (len(data.get("matn", "")) // 70))
        types = DataValidation(type="list", formula1='"tushuncha,misol,masala,topshiriq,test,xulosa,kirish"', allow_blank=True)
        types.error = "Ro'yxatdan tanlang"
        sh.add_data_validation(types)
        col = openpyxl.utils.get_column_letter(keys.index("turi") + 1)
        types.add(f"{col}{header_row + 1}:{col}{header_row + total}")
        return sh

    used = {KITOB_SHEET.lower()}
    topic_sheet(safe_sheet_name("NAMUNA", used), SAMPLE_META, SAMPLE_ROWS, sample=True)
    if prefill:
        for i, t in enumerate(prefill, 1):
            title = safe_sheet_name(f"{i:02d} {t.get('mavzu_nomi') or t.get('mavzu_kodi')}", used)
            topic_sheet(title, {"mavzu_kodi": t.get("mavzu_kodi", ""), "mavzu_nomi": t.get("mavzu_nomi", ""),
                                "mavzu_raqami": str(t.get("mavzu_raqami") or i), "daraja": t.get("daraja", "")},
                        t.get("rows") or (), dars_bor=bool(t.get("dars_bor")))
    else:
        for i in range(1, blank_topics + 1):
            topic_sheet(safe_sheet_name(f"{i}-mavzu", used), {"mavzu_raqami": str(i)})
    wb.active = 0
    return wb
