"""AI miya uchun ODDIY shablon: 2 varaq.

  KITOB    — bitta kitob haqida ma'lumot (yorliq : qiymat).
  MAVZULAR — BIR QATOR = BITTA TUSHUNCHA. Shu qatorning o'zida uning tushuntirishi,
             doskasi, rasmi, misollari, masalasi va «Tushunmadim» variantlari bor.
             Keyingi qator — keyingi tushuncha (shu mavzuda yoki yangi mavzuda).

Testlar shablonga yozilmaydi: dars oxirida shu mavzu kodi bo'yicha Test bazasidagi
savollar beriladi.

Ovoz va doska mosligi:
  * «Doskaga yoziladi» katagida har yangi satr — doskadagi alohida qator;
  * «O'qituvchi aytadi» matnida [1], [2] ... belgisi — o'qituvchi shu joyga yetganda
    doskaning 1-, 2- ... qatori yoziladi (belgi bo'lmasa, qatorlar gap bo'ylab teng taqsimlanadi);
  * misol yechimida har satr — bitta qadam; «doskadagi yozuv || o'qituvchi gapi» ko'rinishida
    yozilsa, doskaga chap tomoni yoziladi, o'qituvchi o'ng tomonini aytadi.

Natija ichki 12 varaqli tuzilmaga aylantiriladi — import, nashr va dars xonasi o'zgarmaydi.
"""
import re

KITOB_SHEET = "KITOB"
MAVZULAR_SHEET = "MAVZULAR"
NAMUNA_PREFIX = "NAMUNA"

BOOK_FIELDS = [
    ("kitob_nomi", "Kitob nomi *", "Masalan: Matematika 5-sinf"),
    ("fan", "Fan *", "Masalan: Matematika"),
    ("sinf", "Sinf *", "1–11 yoki kurs"),
    ("kitob_kodi", "Kitob kodi", "Bo'sh qolsa avtomatik yaratiladi. Kitobni qayta yuklaganda bir xil bo'lsin."),
    ("til", "Til", "uz, ru yoki en"),
    ("mualliflar", "Mualliflar", ""),
    ("nashriyot", "Nashriyot", ""),
    ("nashr_yili", "Nashr yili", ""),
    ("isbn", "ISBN", ""),
]

# (kalit, sarlavha, kenglik, izoh, guruh)
COLUMNS = [
    ("mavzu_kodi", "Mavzu kodi (DTS) *", 20, "Mavzular bazasidagi kod. Shu mavzuning keyingi tushunchalarida bo'sh qoldirsangiz — yuqoridagi kod olinadi.", "mavzu"),
    ("mavzu_nomi", "Mavzu nomi *", 22, "Bo'sh qolsa yuqoridagi qatordagi nom olinadi.", "mavzu"),
    ("tushuncha", "Tushuncha (sarlavha) *", 22, "Shu qatorda o'rgatiladigan bitta tushuncha. Doskaning tepasida chiqadi.", "mavzu"),
    ("daraja", "Daraja (1–30)", 9, "Qiyinlik darajasi.", "mavzu"),
    ("sahifa", "Kitob sahifasi", 9, "", "mavzu"),
    ("kirish", "Kirish savoli", 30, "Ixtiyoriy. Hayotiy savol bilan boshlash: «Pitsani 8 bo'lakka bo'lsak...»", "dars"),
    ("tushuntirish", "O'qituvchi aytadi (tushuntirish) *", 50, "Jonli og'zaki tushuntirish. [1], [2] belgisi qo'ysangiz — o'qituvchi shu joyga yetganda doskaning 1-, 2-qatori yoziladi.", "dars"),
    ("doska", "Doskaga yoziladi", 32, "Qoida, formula. Har yangi satr (Alt+Enter) — doskada alohida qator. Formula: $\\frac{3}{8}$", "dars"),
    ("rasm", "Rasm", 14, "Rasmni katakka qo'ying (Qo'yish → Rasm) yoki fayl nomini yozing va Excel + rasmlarni ZIP qiling.", "dars"),
    ("misol1_shart", "1-misol: sharti", 30, "", "misol"),
    ("misol1_yechim", "1-misol: yechimi", 40, "Har satr — bitta qadam. «doskaga || o'qituvchi aytadi» ko'rinishida yozish mumkin.", "misol"),
    ("misol2_shart", "2-misol: sharti", 30, "", "misol"),
    ("misol2_yechim", "2-misol: yechimi", 40, "Har satr — bitta qadam.", "misol"),
    ("masala", "Masala (o'quvchi o'zi yechadi)", 30, "O'quvchi javob yozadi va tekshiriladi.", "misol"),
    ("masala_javob", "Masala javobi", 14, "Bir nechta to'g'ri javob | bilan: 2/6|1/3", "misol"),
    ("sodda", "Tushunmadim: soddaroq", 34, "O'quvchi «Tushunmadim» bosganda chiqadigan soddaroq tushuntirish.", "tushunmadim"),
    ("hikoya", "Tushunmadim: hikoya orqali", 34, "", "tushunmadim"),
    ("rasmli", "Tushunmadim: rasm bilan", 30, "Rasmga qarab tushuntirish matni.", "tushunmadim"),
    ("rasmli_rasm", "Tushunmadim rasmi", 14, "Rasmni katakka qo'ying yoki fayl nomi.", "tushunmadim"),
    ("boshqa_usul", "Tushunmadim: boshqa usulda", 34, "", "tushunmadim"),
    ("oldingi", "Tushunmadim: oldingi mavzu kodi", 18, "Tayanch mavzu kodi — tugma o'sha mavzuni ochadi.", "tushunmadim"),
    ("xulosa", "Xulosa (esda tut)", 30, "Tushuncha oxirida doskaga yoziladigan qisqa xulosa.", "yakun"),
]
GROUP_COLORS = {"mavzu": "173B57", "dars": "2D6E8B", "misol": "2F7D5B", "tushunmadim": "A0662B", "yakun": "5B4B8A"}
IMAGE_TYPES = {"png": "image/png", "jpeg": "image/jpeg", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}
MAX_VOICE = 1500


def _t(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _norm(value):
    return re.sub(r"[^0-9a-zа-яёқғҳў]+", "", _t(value).lower().replace("‘", "'").replace("’", "'").replace("ʻ", "'"))


def _int(value):
    try:
        return int(float(_t(value)))
    except (TypeError, ValueError):
        return None


def is_simple_workbook(wb):
    return MAVZULAR_SHEET in wb.sheetnames


def _embedded_images(ws):
    """Katakka qo'yilgan rasmlar: {(qator, ustun): (kengaytma, baytlar)}."""
    found = {}
    for image in getattr(ws, "_images", []) or []:
        try:
            anchor = image.anchor._from
            key = (anchor.row + 1, anchor.col + 1)
            data = image._data()
            fmt = (getattr(image, "format", "") or "png").lower()
        except Exception:
            continue
        if fmt in IMAGE_TYPES and data and len(data) <= 5 * 1024 * 1024 and key not in found:
            found[key] = (fmt, data)
    return found


def split_solution(text):
    """Yechim satrlari → [(doska, ovoz)]. «a || b» — doskaga a, o'qituvchi b ni aytadi."""
    lines = [x.strip() for x in re.split(r"\n+", _t(text)) if x.strip()]
    if len(lines) == 1 and re.search(r"(?:^|\s)\d{1,2}\)\s", lines[0]):
        lines = [x.strip() for x in re.split(r"(?:^|\s)(?=\d{1,2}\)\s)", lines[0]) if x.strip()]
    result = []
    for line in lines[:12]:
        board, _, voice = line.partition("||")
        board, voice = board.strip(), voice.strip()
        result.append((board, voice or board))
    return result


def parse_simple(wb, media_names=None, max_images=500):
    media_names = {m.lower() for m in (media_names or set())}
    errors, warnings = [], []

    def err(row, column, message, severity="error", sheet=MAVZULAR_SHEET):
        (errors if severity == "error" else warnings).append(
            {"sheet": sheet, "row": row, "column": column, "message": message, "severity": severity})

    # ── KITOB ──
    book, rows = {}, {}
    if KITOB_SHEET not in wb.sheetnames:
        err(1, "", "KITOB varag'i topilmadi", sheet=KITOB_SHEET)
    else:
        ws = wb[KITOB_SHEET]
        labels = {_norm(label): key for key, label, _ in BOOK_FIELDS}
        for row in range(1, min(ws.max_row, 60) + 1):
            key = labels.get(_norm(ws.cell(row, 1).value))
            if key:
                book[key] = _t(ws.cell(row, 2).value)
                rows[key] = row
        for key, label, _ in BOOK_FIELDS[:3]:
            if not book.get(key):
                err(rows.get(key, 1), label.rstrip(" *"), "To'ldirilishi shart", sheet=KITOB_SHEET)
    source_id = book.get("kitob_kodi") or re.sub(
        r"[^A-Za-z0-9]+", "-", f"KITOB-{book.get('fan', '')}-{book.get('sinf', '')}-{book.get('kitob_nomi', '')}").strip("-")[:80]

    payload = {name: [] for name in ("01_KITOB", "02_DTS_XARITA", "03_BILIM", "04_TUSHUNTIRISH", "05_MISOLLAR",
                                     "06_MASHQLAR", "07_YORDAM_XATOLAR", "08_METODIKA", "09_TOGARAK",
                                     "10_LUGAT_MEDIA", "11_DARS_SSENARIY", "12_TUSHUNMADIM")}
    payload["01_KITOB"].append({
        "source_id": source_id, "kitob_nomi": book.get("kitob_nomi", ""), "fan": book.get("fan", ""),
        "sinf": book.get("sinf", ""), "til": book.get("til") or "uz", "nashr_yili": book.get("nashr_yili", ""),
        "mualliflar": book.get("mualliflar", ""), "nashriyot": book.get("nashriyot", ""), "isbn": book.get("isbn", ""),
        "manba_turi": "darslik", "fayl_nomi": "", "sahifa_boshlanish": "", "sahifa_tugash": "",
        "litsenziya": "", "izoh": "", "import_qilinsin": "ha", "_excel_row": 2,
    })
    media = {}

    ws = wb[MAVZULAR_SHEET]
    header, labels = {}, {}
    by_label = {_norm(label): key for key, label, _, _, _ in COLUMNS}
    by_label.update({_norm(key): key for key, _, _, _, _ in COLUMNS})
    for header_row in (1, 2):
        for col in range(1, ws.max_column + 1):
            key = by_label.get(_norm(ws.cell(header_row, col).value))
            if key and key not in header:
                header[key] = col
        if "tushuntirish" in header:
            first_data = header_row + 1
            break
    label_of = {key: label.rstrip(" *") for key, label, _, _, _ in COLUMNS}
    for key in ("mavzu_kodi", "tushuncha", "tushuntirish"):
        if key not in header:
            err(1, label_of[key], "Majburiy ustun topilmadi — shablonni saytdan qayta yuklab oling")
    if errors:
        return _result(payload, errors, warnings, media)

    embedded = _embedded_images(ws)

    def picture(row, key):
        name = cell_value(row, key)
        col = header.get(key)
        if col and (row, col) in embedded:
            ext, data = embedded[(row, col)]
            name = name or f"MAVZULAR_{row}_{col}.{ext}"
            if len(media) < max_images:
                media[name] = (IMAGE_TYPES[ext], data)
        elif name and name.lower() not in media_names and not name.startswith("https://"):
            err(row, label_of[key], f"«{name}» rasmi topilmadi: rasmni katakka qo'ying yoki shu nomli faylni ZIP ichiga qo'shing", "warning")
        return name

    def cell_value(row, key):
        col = header.get(key)
        return _t(ws.cell(row, col).value) if col else ""

    topics, order = {}, []
    code = name = ""
    for row in range(first_data, ws.max_row + 1):
        c = {key: cell_value(row, key) for key in header}
        if not any(c.values()) and not any(r == row for r, _ in embedded):
            continue
        if c.get("mavzu_kodi"):
            code, name = c["mavzu_kodi"], c.get("mavzu_nomi") or ""
        elif c.get("mavzu_nomi"):
            name = c["mavzu_nomi"]
        if code.upper().startswith(NAMUNA_PREFIX):
            continue
        if not code:
            err(row, label_of["mavzu_kodi"], "Mavzu kodi yozilmagan")
            continue
        topic = topics.get(code)
        if topic is None:
            topic = topics[code] = {"code": code, "name": name, "row": row, "level": None, "pages": [], "steps": [], "variants": [], "concepts": 0}
            order.append(code)
        if name and not topic["name"]:
            topic["name"] = name
        topic["concepts"] += 1
        concept = c.get("tushuncha") or topic["name"]
        if not c.get("tushuncha"):
            err(row, label_of["tushuncha"], "Tushuncha nomini yozing (doskaning sarlavhasi)", "warning")
        page = c.get("sahifa", "")
        if _int(page):
            topic["pages"].append(_int(page))
        if c.get("daraja"):
            level = _int(c["daraja"])
            if level is None or not 1 <= level <= 30:
                err(row, label_of["daraja"], "Daraja 1 dan 30 gacha butun son bo'lishi kerak")
            elif topic["level"] is None:
                topic["level"] = level
        for key in ("kirish", "tushuntirish", "sodda", "hikoya", "rasmli", "boshqa_usul"):
            if len(c.get(key, "")) > MAX_VOICE:
                err(row, label_of[key], f"{MAX_VOICE} belgidan oshmasin — tushunchani ikki qatorga bo'ling")
        if not c.get("tushuntirish") and not c.get("doska"):
            err(row, label_of["tushuntirish"], "Tushuntirish yoki doska matnini yozing")
            continue

        def add_step(kind, board, voice, title="", media_id="", scene=None, answer=""):
            number = len(topic["steps"]) + 1
            step_id = f"{code}#S{number}"
            topic["steps"].append({
                "step_id": step_id, "topic_code": code, "tartib": str(number), "qadam_turi": kind,
                "sahna": scene or step_id, "sarlavha": title, "doska_matni": board, "ovoz_matni": voice,
                "media_id": media_id, "oquvchi_savoli": "Javobingizni yozing" if kind == "birga" else "",
                "kutilgan_javob": answer, "javob_izohi": "", "daraja_1_30": c.get("daraja", ""),
                "source_id": source_id, "sahifa": page, "status": "", "import_qilinsin": "ha", "_excel_row": row,
            })
            return topic["steps"][-1]

        if c.get("kirish"):
            add_step("kirish", c["kirish"], c["kirish"], concept)
        main = add_step("qoida" if c.get("doska") else "tushuntirish", c.get("doska", ""),
                        c.get("tushuntirish") or c.get("doska", ""), concept, picture(row, "rasm"))
        markers = {int(m) for m in re.findall(r"\[(\d{1,2})\]", c.get("tushuntirish", ""))}
        lines = len([x for x in c.get("doska", "").split("\n") if x.strip()])
        if markers and max(markers) > lines:
            err(row, label_of["tushuntirish"], f"[{max(markers)}] belgisi bor, lekin doskada {lines} ta qator bor", "warning")

        variant_specs = [("sodda", "sodda", ""), ("hikoya", "hikoya", ""), ("rasmli", "rasm", "rasmli_rasm"), ("boshqa_usul", "boshqa_usul", "")]
        for key, kind, pic_key in variant_specs:
            text = c.get(key, "")
            pic = picture(row, pic_key) if pic_key else ""
            if text or pic:
                topic["variants"].append({
                    "variant_id": f"{code}#V{len(topic['variants']) + 1}", "topic_code": code, "step_id": main["step_id"],
                    "variant_turi": kind, "tugma_nomi": "", "doska_matni": "", "ovoz_matni": text or "Rasmga qarang.",
                    "media_id": pic, "takrorlash_topic_code": "", "status": "", "import_qilinsin": "ha", "_excel_row": row,
                })
        if c.get("oldingi"):
            topic["variants"].append({
                "variant_id": f"{code}#V{len(topic['variants']) + 1}", "topic_code": code, "step_id": main["step_id"],
                "variant_turi": "takrorlash", "tugma_nomi": "", "doska_matni": "",
                "ovoz_matni": "Keling, avval tayanch mavzuni eslab olamiz.", "media_id": "",
                "takrorlash_topic_code": c["oldingi"], "status": "", "import_qilinsin": "ha", "_excel_row": row,
            })
        if c.get("doska") or c.get("tushuntirish"):
            payload["03_BILIM"].append({
                "content_id": main["step_id"].replace("#S", "#B"), "topic_code": code,
                "content_type": "qoida" if c.get("doska") else "tushuntirish", "sarlavha": concept,
                "mazmun": re.sub(r"\[\d{1,2}\]", "", c.get("tushuntirish") or c.get("doska", "")).strip(),
                "qisqa_xulosa": c.get("xulosa", ""), "formula_latex": c.get("doska", ""), "muhimlik": "asosiy",
                "yosh_min": "", "yosh_max": "", "sahifa": page, "source_id": source_id, "status": "",
                "import_qilinsin": "ha", "_excel_row": row,
            })

        for n in (1, 2):
            shart, yechim = c.get(f"misol{n}_shart", ""), c.get(f"misol{n}_yechim", "")
            if not shart and not yechim:
                continue
            if shart and not yechim:
                err(row, label_of[f"misol{n}_yechim"], f"{n}-misolning yechimini yozing", "warning")
            first = add_step("misol", shart, "Misolni ko'raylik. " + shart if shart else "", f"{n}-misol")
            for board, voice in split_solution(yechim):
                add_step("misol", board, voice, "", "", first["sahna"])
            payload["05_MISOLLAR"].append({
                "example_id": f"{code}#M{len(payload['05_MISOLLAR']) + 1}", "topic_code": code, "daraja": "",
                "misol_turi": "ishlangan", "shart": shart, "berilganlar": "",
                "yechim_qadamlar": "\n".join(b for b, _ in split_solution(yechim)), "yakuniy_javob": "",
                "tekshirish_usuli": "", "tipik_xato": "", "source_id": source_id, "sahifa": page, "status": "",
                "import_qilinsin": "ha", "_excel_row": row,
            })
        if c.get("masala"):
            if not c.get("masala_javob"):
                err(row, label_of["masala_javob"], "Masala javobini yozing — o'quvchi javobi shu bilan tekshiriladi")
            add_step("birga", c["masala"], "Endi o'zing yech. " + c["masala"], "Endi o'zing yech", answer=c.get("masala_javob", ""))
        elif c.get("masala_javob"):
            err(row, label_of["masala"], "Javob bor, lekin masala sharti yozilmagan")
        if c.get("xulosa"):
            add_step("xulosa", c["xulosa"], "Esda tut: " + c["xulosa"], "Esda tut")

    if not order:
        err(first_data, "", "Birorta tushuncha topilmadi. NAMUNA qatoridan keyin o'z mavzuingizni yozing (kod NAMUNA bilan boshlanmasin).")
    for code in order:
        topic = topics[code]
        if not topic["name"]:
            err(topic["row"], label_of["mavzu_nomi"], "Mavzu nomini yozing")
        pages = topic["pages"]
        payload["02_DTS_XARITA"].append({
            "topic_code": code, "source_id": source_id, "fan": book.get("fan", ""), "sinf": book.get("sinf", ""),
            "chorak": "", "bob": "", "bolim": "", "mavzu": topic["name"], "kichik_mavzu": "",
            "sahifa_boshlanish": str(min(pages)) if pages else "", "sahifa_tugash": str(max(pages)) if pages else "",
            "oquv_maqsadi": "", "tayanch_bilimlar": "", "natija_mezoni": "", "status": "",
            "daraja_1_30": str(topic["level"] or ""), "import_qilinsin": "ha", "_excel_row": topic["row"],
            "_sheet": MAVZULAR_SHEET,
        })
        payload["11_DARS_SSENARIY"].extend(topic["steps"])
        payload["12_TUSHUNMADIM"].extend(topic["variants"])
    return _result(payload, errors, warnings, media)


def _result(payload, errors, warnings, media):
    units = sum(len(payload.get(s, [])) for s in ("03_BILIM", "05_MISOLLAR", "11_DARS_SSENARIY", "12_TUSHUNMADIM"))
    summary = {
        "format": "oddiy",
        "kitoblar": len(payload.get("01_KITOB", [])),
        "mavzular": len(payload.get("02_DTS_XARITA", [])),
        "tushunchalar": len(payload.get("03_BILIM", [])),
        "bilim_birliklari": units,
        "xatolar": sum(1 for e in errors if e.get("severity") == "error"),
        "ogohlantirishlar": len(warnings),
        "varoqlar": {s: len(rows) for s, rows in payload.items()},
        "rasmlar": len(media),
    }
    return {"payload": payload, "summary": summary, "errors": errors, "warnings": warnings,
            "preview": {s: rows[:3] for s, rows in payload.items() if rows}, "media": media}


SAMPLE_CODE = "NAMUNA-5-01-01-01-01-01-001"
SAMPLE_ROWS = [
    {
        "mavzu_kodi": SAMPLE_CODE, "mavzu_nomi": "Oddiy kasr", "tushuncha": "Surat va maxraj", "daraja": "5", "sahifa": "43",
        "kirish": "Pitsani 8 ta teng bo'lakka bo'ldik, sen 3 bo'lagini yeding. Pitsaning qancha qismini yeding?",
        "tushuntirish": "Butunni teng bo'laklarga bo'lamiz. [1] Pastdagi son — maxraj: butun nechta teng bo'lakka bo'linganini bildiradi. [2] Tepadagi son — surat: nechta bo'lak olinganini bildiradi.",
        "doska": "Maxraj — jami teng bo'laklar\nSurat — olingan bo'laklar", "rasm": "pitsa_8.png",
        "misol1_shart": "8 bo'lakdan 3 tasi olindi. Kasrni yozing.",
        "misol1_yechim": "Maxraj = 8 || Jami sakkiz bo'lak — maxrajga sakkiz yozamiz.\nSurat = 3 || Uch bo'lak olindi — suratga uch.\n$\\frac{3}{8}$ || Javob: uch sakkizdan.",
        "misol2_shart": "", "misol2_yechim": "",
        "masala": "6 bo'lakdan 2 tasi bo'yalgan. Kasrni yozing.", "masala_javob": "2/6|1/3",
        "sodda": "Nonni nechta bo'lakka kessang, o'sha son maxraj. Nechtasini olsang — surat.",
        "hikoya": "Oyim olmani 8 bo'lakka bo'ldi, men 3 tasini oldim: 8 — jami, 3 — meniki. Uch sakkizdan.",
        "rasmli": "Rasmga qara: 8 ta katak — maxraj, bo'yalgan 3 tasi — surat.", "rasmli_rasm": "kataklar_3_8.png",
        "boshqa_usul": "Sonlar nurini 0 dan 1 gacha 8 ga bo'lamiz va 3-bo'linmaga boramiz: 3/8.",
        "oldingi": "5-01-01-01-01-00-001", "xulosa": "Surat — olingan, maxraj — jami",
    },
    {
        "mavzu_kodi": "", "mavzu_nomi": "", "tushuncha": "Kasrni o'qish", "daraja": "", "sahifa": "44",
        "kirish": "",
        "tushuntirish": "Kasrni o'qishda avval maxraj, keyin surat aytiladi. [1] Uch sakkizdan deymiz. [2] Besh yettidan deymiz.",
        "doska": "$\\frac{3}{8}$ — uch sakkizdan\n$\\frac{5}{7}$ — besh yettidan", "rasm": "",
        "misol1_shart": "$\\frac{2}{9}$ ni o'qing.", "misol1_yechim": "Maxraj 9 — «to'qqizdan» || Avval maxraj: to'qqizdan.\nSurat 2 — «ikki» || Keyin surat: ikki.\nIkki to'qqizdan || Demak, ikki to'qqizdan.",
        "misol2_shart": "", "misol2_yechim": "",
        "masala": "«Yetti o'ndan» kasrini raqamda yozing.", "masala_javob": "7/10",
        "sodda": "Pastdagi son «...dan» bo'lib o'qiladi: 8 — «sakkizdan».", "hikoya": "", "rasmli": "", "rasmli_rasm": "",
        "boshqa_usul": "", "oldingi": "", "xulosa": "Avval maxraj, keyin surat",
    },
]


def template_workbook():
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
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 42
    ws.column_dimensions["C"].width = 62
    ws["A1"] = "1-QADAM. KITOB HAQIDA"
    ws["A1"].font = Font(size=16, bold=True, color="FFFFFF")
    ws["A1"].fill = PatternFill("solid", fgColor=navy)
    ws.merge_cells("A1:C1")
    ws.row_dimensions[1].height = 30
    for i, (_, label, hint) in enumerate(BOOK_FIELDS, 3):
        ws.cell(i, 1, label).font = Font(bold=True)
        value = ws.cell(i, 2)
        value.fill = PatternFill("solid", fgColor=input_fill)
        value.border = border
        ws.cell(i, 3, hint).font = Font(color="6B7785", italic=True)
    help_row = len(BOOK_FIELDS) + 5
    ws.cell(help_row, 1, "QANDAY TO'LDIRILADI").font = Font(size=13, bold=True, color=navy)
    steps = [
        "1. Shu varaqda sariq kataklarni to'ldiring (bitta fayl = bitta kitob).",
        "2. MAVZULAR varag'ida BIR QATOR = BITTA TUSHUNCHA. Uning tushuntirishi, doskasi, rasmi, misollari, masalasi va «Tushunmadim» variantlari — hammasi shu qatorda.",
        "3. Keyingi qator — keyingi tushuncha. Mavzuda bir nechta tushuncha bo'lsa, mavzu kodini birinchi qatorga yozish kifoya.",
        "4. Testlarni yozmang: dars oxirida o'quvchi shu mavzu kodi bo'yicha Test bazasidagi savollarni tanlaydi.",
        "5. Doska: har yangi satr (Alt+Enter) doskada alohida qator. Tushuntirishda [1], [2] qo'ysangiz — o'qituvchi shu joyga yetganda o'sha qator yoziladi.",
        "6. Misol yechimi: har satr — bitta qadam. «doskaga || o'qituvchi aytadi» deb yozsangiz, doskaga chap tomoni yoziladi, o'qituvchi o'ng tomonini aytadi.",
        "7. Rasm: katakka to'g'ridan-to'g'ri qo'ying yoki fayl nomini yozib, Excel va rasmlarni bitta ZIP qiling.",
        "8. Kulrang NAMUNA qatorlari import qilinmaydi. Saytda: Tekshirish → Qoralama import → Nashr.",
    ]
    for i, text in enumerate(steps, help_row + 1):
        ws.cell(i, 1, text)
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=3)
        ws.cell(i, 1).alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[i].height = 32

    ws = wb.create_sheet(MAVZULAR_SHEET)
    ws.freeze_panes = "D3"
    group_titles = {"mavzu": "MAVZU", "dars": "TUSHUNTIRISH VA DOSKA", "misol": "MISOLLAR VA MASALA",
                    "tushunmadim": "«TUSHUNMADIM» BOSILSA", "yakun": "YAKUN"}
    col = 1
    groups = []
    for key, label, width, hint, group in COLUMNS:
        if not groups or groups[-1][0] != group:
            groups.append([group, col, col])
        else:
            groups[-1][2] = col
        c = ws.cell(2, col, label)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=GROUP_COLORS[group])
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = border
        if hint:
            c.comment = Comment(hint, "Kabutar")
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = width
        col += 1
    for group, start, end in groups:
        ws.cell(1, start, group_titles[group])
        cell = ws.cell(1, start)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor=GROUP_COLORS[group])
        cell.alignment = Alignment(horizontal="center", vertical="center")
        if end > start:
            ws.merge_cells(start_row=1, start_column=start, end_row=1, end_column=end)
    ws.row_dimensions[1].height = 22
    ws.row_dimensions[2].height = 44
    keys = [key for key, *_ in COLUMNS]
    for r, sample in enumerate(SAMPLE_ROWS, 3):
        for ci, key in enumerate(keys, 1):
            c = ws.cell(r, ci, sample.get(key, ""))
            c.fill = PatternFill("solid", fgColor=sample_fill)
            c.font = Font(italic=True, color="4A5563")
            c.alignment = Alignment(vertical="top", wrap_text=True)
            c.border = border
        ws.row_dimensions[r].height = 150
    first_input = len(SAMPLE_ROWS) + 3
    for r in range(first_input, first_input + 200):
        for ci in range(1, len(COLUMNS) + 1):
            c = ws.cell(r, ci)
            c.alignment = Alignment(vertical="top", wrap_text=True)
            c.border = border
    level_col = openpyxl.utils.get_column_letter(keys.index("daraja") + 1)
    dv = DataValidation(type="whole", operator="between", formula1="1", formula2="30", allow_blank=True)
    dv.error = "Daraja 1 dan 30 gacha"
    ws.add_data_validation(dv)
    dv.add(f"{level_col}3:{level_col}3000")
    wb.active = 0
    return wb
