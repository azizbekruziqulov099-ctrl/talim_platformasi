"""Bounded, network-free PDF question papers with Unicode and rendered maths.

Only authorized, saved attempt snapshots enter this renderer. Maths is parsed by
Matplotlib mathtext (never a TeX subprocess); unsupported notation fails clearly
instead of publishing raw markup or an altered formula. Fonts ship with the app.
"""
from contextlib import redirect_stderr
from html import escape
from io import BytesIO, StringIO
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from threading import RLock
import warnings

FONT_ROOT = Path(__file__).with_name("pdf_fonts")
_LOCK = RLock()
_SEGMENTS = re.compile(r"(\[lat\][\s\S]*?\[/lat\]|\$\$[\s\S]*?\$\$|\$[^$\n]+\$|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\])", re.I)
_TAGS = re.compile(r"\[\s*/?\s*(?:uz|ru|en|de|fr|tj|eng|rus)\s*\]", re.I)
_INVALID = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")


def _clean(value):
    return _INVALID.sub("", _TAGS.sub("", str(value or ""))).strip()


def _formula(part):
    if part.lower().startswith("[lat]"):
        return part[5:-6].strip()
    if part.startswith("$$") or part.startswith((r"\(", r"\[")):
        return part[2:-2].strip()
    return part[1:-1].strip()


def _raw_math_segments(text):
    """Recognize common untagged TeX atoms without treating prose as maths."""
    atom = re.compile(r"\\([A-Za-z]+)")
    args = {"frac": 2, "dfrac": 2, "tfrac": 2, "sqrt": 1, "text": 1,
            "mathrm": 1, "mathbf": 1, "overline": 1, "vec": 1, "hat": 1}
    singles = {"times", "cdot", "div", "pm", "mp", "leq", "geq", "le", "ge", "neq", "ne", "approx",
               "infty", "pi", "alpha", "beta", "gamma", "theta", "Delta", "delta", "lambda", "mu", "sigma",
               "omega", "Omega", "sum", "prod", "int", "lim", "to", "sin", "cos", "tan", "log", "ln"}
    cursor = 0

    def group(end):
        while end < len(text) and text[end].isspace(): end += 1
        if end >= len(text) or text[end] != "{":
            raise ValueError("Formuladagi qavslar to‘liq emas; administrator yozuvni tekshirsin.")
        depth, pos = 1, end + 1
        while pos < len(text) and depth:
            if text[pos] == "{": depth += 1
            if text[pos] == "}": depth -= 1
            pos += 1
        if depth: raise ValueError("Formuladagi qavs yopilmagan; administrator yozuvni tekshirsin.")
        return pos

    for match in atom.finditer(text):
        if match.start() < cursor: continue
        if match.start() > cursor: yield False, text[cursor:match.start()]
        command, end = match[1], match.end()
        if command not in args and command not in singles:
            raise ValueError("Belgisiz murakkab formula bor; administrator formulani alohida belgilasin.")
        if command == "sqrt" and end < len(text) and text[end] == "[":
            close = text.find("]", end)
            if close < 0: raise ValueError("Ildiz darajasi yopilmagan.")
            end = close + 1
        for _ in range(args.get(command, 0)): end = group(end)
        while end < len(text) and text[end] in "_^":
            end += 1
            end = group(end) if end < len(text) and text[end] == "{" else min(len(text), end + 1)
        yield True, text[match.start():end]
        cursor = end
    if cursor < len(text): yield False, text[cursor:]


def _math_image(source):
    """Return PNG bytes at 180 dpi; keep dimensions and parser work bounded."""
    from PIL import Image, ImageDraw, ImageFont
    from matplotlib import rc_context
    from matplotlib.font_manager import FontProperties
    from matplotlib.mathtext import math_to_image

    source = source.replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
    if not source or len(source) > 2000 or source.count("{") > 120:
        raise ValueError("Formula bo‘sh yoki juda uzun; savoldagi formulani tekshiring.")

    def basic(value):
        out, stderr = BytesIO(), StringIO()
        with _LOCK, warnings.catch_warnings(), redirect_stderr(stderr), rc_context({"mathtext.fontset": "dejavusans"}):
            warnings.simplefilter("error")
            try:
                math_to_image("$" + value + "$", out, prop=FontProperties(size=11), dpi=180, format="png", color="#17314b")
            except (ValueError, RuntimeError, Warning) as exc:
                raise ValueError("Savoldagi formulani PDF uchun o‘qib bo‘lmadi. Administrator formula yozuvini tekshirsin.") from exc
        if stderr.getvalue().strip():
            raise ValueError("Formulada shrift qo‘llamaydigan belgi bor. Administrator formula yozuvini tekshirsin.")
        out.seek(0)
        with Image.open(out) as image:
            if image.width > 5000 or image.height > 2000:
                raise ValueError("Formula bir sahifaga o‘qiladigan o‘lchamda sig‘maydi; uni qismlarga ajrating.")
            return image.convert("RGBA")

    # A matrix/cases expression is laid out as real rows/columns. Nested TeX
    # environments deliberately fail; a wrong mathematical rendering is worse
    # than a clear error and a corrected bank entry.
    env = re.fullmatch(r"(.*?)\\begin\{(matrix|pmatrix|bmatrix|vmatrix|Vmatrix|cases)\}([\s\S]*?)\\end\{\2\}(.*)", source)
    if env:
        prefix, kind, body, suffix = env.groups()
        if r"\begin" in body or r"\end" in body:
            raise ValueError("Ichma-ich matritsa PDFda qo‘llanmaydi; formulani alohida qismlarga ajrating.")
        rows = [row.strip() for row in re.split(r"\\\\", body) if row.strip()]
        cells = [[cell.strip() for cell in row.split("&")] for row in rows]
        if not cells or len(cells) > 8 or max(map(len, cells)) > 6 or len(set(map(len, cells))) != 1:
            raise ValueError("Matritsa qatorlari mos emas yoki o‘lchami juda katta.")
        rendered = [[basic(cell or r"\quad") for cell in row] for row in cells]
        widths = [max(row[c].width for row in rendered) for c in range(len(cells[0]))]
        heights = [max(image.height for image in row) for row in rendered]
        gap_x, gap_y = 24, 12
        content_w = sum(widths) + gap_x * (len(widths) - 1)
        content_h = sum(heights) + gap_y * (len(heights) - 1)
        left, right = {"matrix": ("", ""), "pmatrix": ("(", ")"), "bmatrix": ("[", "]"),
                       "vmatrix": ("|", "|"), "Vmatrix": ("‖", "‖"), "cases": ("{", "")}[kind]
        font = ImageFont.truetype(str(FONT_ROOT / "DejaVuSans.ttf"), max(30, content_h))
        pre, post = basic(prefix) if prefix.strip() else None, basic(suffix) if suffix.strip() else None
        bracket_w = max(20, int(content_h * .36)) if left else 0
        pre_w, post_w = (pre.width + 12 if pre else 0), (post.width + 12 if post else 0)
        image = Image.new("RGBA", (pre_w + content_w + bracket_w * 2 + post_w + 16,
                                   max(content_h + 20, pre.height if pre else 0, post.height if post else 0)), "white")
        draw = ImageDraw.Draw(image)
        for character, x in ((left, pre_w), (right, pre_w + bracket_w + content_w + 8)):
            if character:
                bbox = font.getbbox(character)
                glyph = Image.new("RGBA", (bbox[2] - bbox[0] + 4, bbox[3] - bbox[1] + 4), "white")
                ImageDraw.Draw(glyph).text((2 - bbox[0], 2 - bbox[1]), character, font=font, fill="#17314b")
                glyph.thumbnail((bracket_w, content_h + 16))
                glyph = glyph.resize((max(10, glyph.width), content_h + 12))
                image.paste(glyph, (x, (image.height - glyph.height) // 2))
        y = (image.height - content_h) // 2
        for row, height in zip(rendered, heights):
            x = pre_w + bracket_w + 4
            for cell, width in zip(row, widths):
                image.paste(cell, (x + (width - cell.width) // 2, y + (height - cell.height) // 2))
                x += width + gap_x
            y += height + gap_y
        if pre: image.paste(pre, (0, (image.height - pre.height) // 2))
        if post: image.paste(post, (image.width - post.width, (image.height - post.height) // 2))
    else:
        image = basic(source)
    result = BytesIO()
    image.save(result, "PNG")
    return result.getvalue(), image.width * .4, image.height * .4


def render_pdf(attempt, questions, answer_key, images):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, HRFlowable, KeepTogether, Table, TableStyle
    from .kabutar_assistant_exports import _metadata, _points, _answer, _topics, _topic

    with _LOCK:
        for name, file in (("Kabutar", "DejaVuSans.ttf"), ("KabutarBold", "DejaVuSans-Bold.ttf")):
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, str(FONT_ROOT / file)))
        pdfmetrics.registerFontFamily("Kabutar", normal="Kabutar", bold="KabutarBold", italic="Kabutar", boldItalic="KabutarBold")
    blue, grey = colors.HexColor("#17314b"), colors.HexColor("#526578")
    styles = {
        "body": ParagraphStyle("body", fontName="Kabutar", fontSize=10.5, leading=16, textColor=blue, spaceAfter=7, autoLeading="max", splitLongWords=True),
        "title": ParagraphStyle("title", fontName="KabutarBold", fontSize=22, leading=28, textColor=blue, spaceAfter=12),
        "meta": ParagraphStyle("meta", fontName="Kabutar", fontSize=8.5, leading=13, textColor=grey, spaceAfter=5),
        "heading": ParagraphStyle("heading", fontName="KabutarBold", fontSize=11, leading=16, textColor=blue, spaceBefore=10, spaceAfter=5, keepWithNext=True),
        "key": ParagraphStyle("key", fontName="Kabutar", fontSize=9, leading=13, textColor=blue, spaceAfter=3, autoLeading="max", splitLongWords=True),
        "keynote": ParagraphStyle("keynote", fontName="Kabutar", fontSize=8.5, leading=12, textColor=grey, spaceAfter=2, autoLeading="max", splitLongWords=True),
        "option": ParagraphStyle("option", fontName="Kabutar", fontSize=10.5, leading=16, textColor=blue, leftIndent=12, spaceAfter=5, autoLeading="max", splitLongWords=True),
    }
    stream = BytesIO()
    page_width, page_height = A4
    usable = page_width - 88
    title = "Javoblar kaliti" if answer_key else "Test savollari"
    doc = SimpleDocTemplate(stream, pagesize=A4, leftMargin=44, rightMargin=44, topMargin=56, bottomMargin=48,
                            title="Kabutar - " + title, author="Kabutar", pageCompression=1)

    with TemporaryDirectory(prefix="kabutar-pdf-") as tmp:
        formula_files = {}

        def paragraph(value, style="body"):
            value = _clean(value)
            if len(value) > 24000:
                raise ValueError("Savol matni PDF uchun juda uzun; savolni qismlarga ajrating.")
            markup = []
            tallest_formula = 0
            segments = []
            for part in _SEGMENTS.split(value):
                if _SEGMENTS.fullmatch(part):
                    segments.append((True, _formula(part)))
                elif re.search(r"\\[A-Za-z]+", part):
                    segments.extend(_raw_math_segments(part))
                else:
                    segments.append((False, part))
            for is_formula, segment in segments:
                if not segment: continue
                if is_formula:
                    source = segment
                    if source not in formula_files:
                        payload, width, height = _math_image(source)
                        if len(formula_files) >= 500:
                            raise ValueError("PDFda formulalar juda ko‘p; testni qismlarga ajrating.")
                        file = Path(tmp) / (str(len(formula_files)) + ".png")
                        file.write_bytes(payload)
                        formula_files[source] = (str(file), width, height)
                    file, width, height = formula_files[source]
                    scale = min(1, (usable - 28) / max(width, 1))
                    if scale < .65 or height * scale > 210:
                        raise ValueError("Formula o‘qiladigan o‘lchamda sahifaga sig‘maydi; uni qismlarga ajrating.")
                    tallest_formula = max(tallest_formula, height * scale)
                    markup.append(f'<img src="{file}" width="{width*scale:.2f}" height="{height*scale:.2f}" valign="middle"/>')
                else:
                    if re.search(r"\[/?lat\]|\\[A-Za-z]+|\\[\[\](){}]", segment, re.I):
                        raise ValueError("Formula belgilanishi tugallanmagan. Administrator [lat] formula [/lat] yozuvini tekshirsin.")
                    markup.append(escape(segment).replace("\n", "<br/>"))
            paragraph_style = styles[style]
            if tallest_formula > paragraph_style.leading:
                # Inline images are centered on the baseline. Their upper half
                # needs room above this paragraph as well as in its line box.
                paragraph_style = ParagraphStyle(style + "Math", parent=paragraph_style,
                    spaceBefore=max(paragraph_style.spaceBefore, (tallest_formula - paragraph_style.leading) / 2 + 4))
            return Paragraph("".join(markup) or " ", paragraph_style)

        story = [paragraph(title, "title")]
        plan = attempt.get("plan") or {}
        metadata = [(label, value) for label, value in _metadata(attempt, questions) if value and label != "Test ID"]
        story.append(paragraph("   ·   ".join(f"{label}: {value}" for label, value in metadata), "meta"))
        story.extend([HRFlowable(width="100%", color=colors.HexColor("#cbd9e6"), thickness=.7), Spacer(1, 12)])
        if answer_key:
            story.append(paragraph("Savollar faylidagi tartib bo‘yicha alohida javoblar kaliti.", "meta"))
            rows = [[paragraph("Savol", "key"), paragraph("To‘g‘ri javob va izoh", "key"), paragraph("Ball", "key")]]
            for index, question in enumerate(questions, 1):
                answer = [paragraph(_answer(question), "key")]
                if _clean(question.get("explanation")):
                    answer.append(paragraph("Izoh: " + _clean(question["explanation"]), "keynote"))
                rows.append([paragraph(str(index), "key"), answer, paragraph(str(_points(question)), "key")])
            table = Table(rows, colWidths=[42, usable - 91, 49], repeatRows=1, splitByRow=1, splitInRow=1)
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eef5")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f9fb")]),
                ("LINEBELOW", (0, 0), (-1, 0), .7, colors.HexColor("#afc2d2")),
                ("LINEBELOW", (0, 1), (-1, -1), .3, colors.HexColor("#dfe7ef")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]))
            story.append(table)
        else:
            story.append(paragraph("Ism-familiya: __________________________________   Sana: ______________", "meta"))
            topics = _topics(plan)
            for index, question in enumerate(questions, 1):
                block = [paragraph(f"{index}-savol · {_points(question)} ball", "heading")]
                topic = _topic(question, topics)
                if topic: block.append(paragraph(topic, "meta"))
                block.append(paragraph(question.get("question")))
                if index in images:
                    payload, width, height = images[index]
                    scale = min(1, usable / width, 215 / height)
                    block.append(Image(BytesIO(payload), width=width * scale, height=height * scale, hAlign="LEFT"))
                    block.append(Spacer(1, 8))
                if question.get("question_type") == "write_answer":
                    block.append(paragraph("Javob: __________________________________________________", "option"))
                    block.append(Spacer(1, 10))
                else:
                    for letter in "ABCD":
                        option = _clean(question.get("option_" + letter.lower()))
                        if option: block.append(paragraph(f"{letter}) {option}", "option"))
                block.append(Spacer(1, 7))
                # Keep ordinary questions together. Oversized questions should
                # fill the current page and continue, without an empty page gap.
                height = sum(item.wrap(usable - 12, doc.height)[1] + item.getSpaceBefore() + item.getSpaceAfter() for item in block)
                if height <= doc.height - 12:
                    story.append(KeepTogether(block))
                else:
                    story.extend(block)

        def page(canvas, current):
            canvas.saveState()
            canvas.setFillColor(grey)
            canvas.setFont("KabutarBold", 8)
            canvas.drawString(44, page_height - 31, "KABUTAR  /  TA’LIM")
            canvas.setFont("Kabutar", 8)
            canvas.drawRightString(page_width - 44, page_height - 31, title)
            canvas.setStrokeColor(colors.HexColor("#dfe7ef"))
            canvas.line(44, 35, page_width - 44, 35)
            ident = re.sub(r"[^a-zA-Z0-9_-]", "", str(attempt.get("attempt_id") or ""))[:40]
            canvas.drawString(44, 22, "Test: " + ident)
            canvas.drawRightString(page_width - 44, 22, f"{current.page}-bet")
            canvas.restoreState()

        doc.build(story, onFirstPage=page, onLaterPages=page)
    return stream.getvalue()
