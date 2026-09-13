"""Bounded, local Presentation Studio export using the artifact-created base deck.

Native DrawingML text and Office Math are editable in PowerPoint. Formula images
inside mc:Fallback support viewers without Office Math. The accepted TeX subset
is deliberately finite; unknown commands and content that cannot fit are errors.
No shell, remote URLs, TeX executable, or python-pptx is used.
"""
from __future__ import annotations

import base64
import binascii
from copy import deepcopy
from functools import lru_cache
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import re
import threading
import zipfile

from lxml import etree as E
from PIL import Image, ImageFont, ImageOps, UnidentifiedImageError

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "a14": "http://schemas.microsoft.com/office/drawing/2010/main",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "ct": "http://schemas.openxmlformats.org/package/2006/content-types",
}
ASSETS = Path(__file__).with_name("presentation_assets")
EMU = 9525
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_DOCUMENT_BYTES = 8 * 1024 * 1024
MAX_IMAGE_PIXELS = 16_000_000
_MATH_LOCK = threading.RLock()
ACCENTS = {"cyan": "06b6d4", "blue": "3b82f6", "violet": "8b5cf6", "green": "10b981", "amber": "f59e0b"}
DEFAULT_DESIGN = {"background": "aurora", "color": "#17394b", "image": None, "overlay": 25,
                  "panel": "glass", "accent": "cyan", "text": "auto", "font": "sans", "size": "normal", "radius": "round"}


def q(tag):
    prefix, local = tag.split(":", 1)
    return "{" + NS[prefix] + "}" + local


def el(tag, *children, **attrs):
    node = E.Element(q(tag))
    for key, value in attrs.items():
        node.set(q(key) if ":" in key else key, str(value))
    for child in children:
        if isinstance(child, (tuple, list)):
            node.extend(child)
        else:
            node.append(child)
    return node


def xml(node):
    return E.tostring(node, xml_declaration=True, encoding="UTF-8", standalone=True)


def _check_text(value, maximum, label):
    if not isinstance(value, str) or len(value) > maximum:
        raise ValueError(f"{label}: matn {maximum} belgidan oshmasligi kerak.")
    if any(ord(c) < 32 and c not in "\n\t\r" for c in value) or any(0xD800 <= ord(c) <= 0xDFFF or ord(c) in (0xFFFE, 0xFFFF) for c in value):
        raise ValueError(f"{label}: yaroqsiz matn belgisi.")
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _design(value):
    if value is None:
        value = DEFAULT_DESIGN
    if not isinstance(value, dict):
        raise ValueError("Dizayn ma’lumoti noto‘g‘ri.")
    result = dict(DEFAULT_DESIGN)
    result.update(value)
    choices = {"background": ("aurora", "paper", "midnight", "solid", "image"),
               "panel": ("glass", "solid", "none"), "accent": tuple(ACCENTS),
               "text": ("auto", "light", "dark"), "font": ("sans", "serif"),
               "size": ("normal", "large"), "radius": ("round", "square")}
    for key, values in choices.items():
        if result.get(key) not in values:
            raise ValueError(f"Dizayn: {key} qiymati noto‘g‘ri.")
    if not isinstance(result.get("color"), str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", result["color"]):
        raise ValueError("Dizayn rangi #RRGGBB shaklida bo‘lishi kerak.")
    overlay = result.get("overlay")
    if isinstance(overlay, bool) or not isinstance(overlay, (int, float)) or not math.isfinite(overlay) or not 0 <= overlay <= 90:
        raise ValueError("Fon xiraligi 0–90 oralig‘ida bo‘lishi kerak.")
    if result["background"] == "image" and not result.get("image"):
        raise ValueError("Rasmli fon uchun PNG yoki JPEG rasm tanlang.")
    return result


def _validate(document):
    if not isinstance(document, dict) or document.get("schema") != 1:
        raise ValueError("Taqdimot formati noto‘g‘ri.")
    try:
        encoded_size = len(json.dumps(document, ensure_ascii=False).encode("utf-8"))
    except (ValueError, TypeError, UnicodeError):
        raise ValueError("Taqdimot ma’lumoti noto‘g‘ri.") from None
    if encoded_size > MAX_DOCUMENT_BYTES:
        raise ValueError("Taqdimot hajmi 8 MB dan oshmasligi kerak.")
    slides = document.get("slides")
    if not isinstance(slides, list) or not 1 <= len(slides) <= 40:
        raise ValueError("Taqdimot 1–40 slayddan iborat bo‘lishi kerak.")
    _check_text(document.get("title", ""), 160, "Taqdimot nomi")
    _check_text(document.get("subject", ""), 100, "Fan nomi")
    global_design = _design(document.get("design"))
    out = []
    for index, slide in enumerate(slides, 1):
        if not isinstance(slide, dict) or slide.get("layout", "text") not in ("text", "formula", "image"):
            raise ValueError(f"{index}-slayd: tuzilma noto‘g‘ri.")
        item = dict(slide)
        for name, maximum, label in [("title", 100, "sarlavha"), ("section", 60, "bo‘lim"), ("body", 600, "matn"),
                                     ("formula", 400, "formula"), ("example", 250, "misol")]:
            item[name] = _check_text(slide.get(name, ""), maximum, f"{index}-slayd {label}")
        item["design"] = _design(slide.get("design") or global_design)
        item["layout"] = item.get("layout", "text")
        out.append(item)
    return out


def _luminance(color):
    rgb = [int(color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2]


def _tokens(design):
    bg = {"aurora": "091b35", "paper": "f4f2eb", "midnight": "111a35", "image": "091b35"}.get(design["background"], design["color"][1:])
    if design["text"] == "auto":
        if design["background"] == "paper":
            light = design["overlay"] >= 45
        elif design["background"] == "solid":
            light = _luminance(bg) * (1 - design["overlay"] / 100) < .5
        else:
            light = True
    else:
        light = design["text"] == "light"
    return {"bg": bg, "fg": "f8fafc" if light else "14243b", "muted": "cbd5e1" if light else "475569",
            "panel": "14243b" if light else "ffffff", "panel_alpha": .70 if light else .78,
            "border": "ffffff" if light else "14243b", "border_alpha": .18 if light else .14,
            "accent": ACCENTS[design["accent"]], "font": "Georgia" if design["font"] == "serif" else "Arial"}


def _fill(color, opacity=1):
    c = el("a:srgbClr", val=color)
    if opacity < 1:
        c.append(el("a:alpha", val=round(max(0, opacity) * 100000)))
    return el("a:solidFill", c)


def _transform(box):
    x, y, w, h = box
    return el("a:xfrm", el("a:off", x=round(x * EMU), y=round(y * EMU)),
              el("a:ext", cx=round(w * EMU), cy=round(h * EMU)))


@lru_cache(maxsize=16)
def _font_path(family, bold):
    # Arial/Liberation Sans share metrics. The fallback is always a local font.
    from matplotlib import font_manager
    names = ["Georgia", "Liberation Serif", "DejaVu Serif"] if family == "Georgia" else ["Arial", "Liberation Sans", "DejaVu Sans"]
    with _MATH_LOCK:
        for name in names:
            try:
                return font_manager.findfont(font_manager.FontProperties(family=name, weight="bold" if bold else "normal"), fallback_to_default=False)
            except ValueError:
                continue
    raise ValueError("Eksport uchun mahalliy shrift topilmadi.")


def _wrap(text, width, height, size, family, bold, line_height, label):
    if not text:
        return []
    font = ImageFont.truetype(_font_path(family, bold), round(size * 4))
    available = (width - 6) * 4  # small cross-viewer metric allowance
    lines = []
    for para in text.split("\n"):
        if not para:
            lines.append("")
            continue
        current = ""
        for word in re.findall(r"\S+|[ \t]+", para):
            candidate = current + word.replace("\t", "    ")
            if font.getlength(candidate) <= available:
                current = candidate
                continue
            if current.strip():
                lines.append(current.rstrip())
                current = ""
            word = word.lstrip()
            if not word:
                continue
            if font.getlength(word) <= available:
                current = word
            else:
                # Long unbroken words use the same overflow-wrap behaviour as preview.
                for char in word:
                    if font.getlength(current + char) > available:
                        lines.append(current)
                        current = ""
                    current += char
        lines.append(current.rstrip())
    if len(lines) * size * line_height > height + .5:
        raise ValueError(f"{label} slaydga sig‘madi. Matnni qisqartiring, oddiy matn o‘lchamini yoki boshqa tuzilmani tanlang.")
    return lines


def _rpr(size, color, font, bold=False, tag="a:rPr"):
    return el(tag, _fill(color), el("a:latin", typeface=font), el("a:ea", typeface=font), el("a:cs", typeface=font),
              sz=round(size * 75), b="1" if bold else "0", lang="uz-Latn-UZ", dirty="0")


class _Deck:
    def __init__(self):
        try:
            with zipfile.ZipFile(ASSETS / "base.pptx") as source:
                self.blobs = {i.filename: source.read(i.filename) for i in source.infolist()}
        except (OSError, zipfile.BadZipFile):
            raise ValueError("Taqdimot eksport shabloni topilmadi. Administratorga murojaat qiling.") from None
        self.template = E.fromstring(self.blobs["ppt/slides/slide1.xml"])
        self.prototypes = {}
        for shape in self.template.xpath(".//p:sp | .//p:pic", namespaces=NS):
            name = shape.find(".//p:cNvPr", NS).get("name", "")
            self.prototypes[name] = shape
        self.background = self.template.find("p:cSld/p:spTree/p:pic", NS)
        self.media = {}
        self.decoded = {}
        self.formulas = {}
        for path in list(self.blobs):
            if path.startswith(("ppt/slides/", "ppt/notesSlides/", "ppt/media/")):
                del self.blobs[path]
        self.ct = E.fromstring(self.blobs["[Content_Types].xml"])
        for part in list(self.ct):
            if part.get("PartName", "").startswith(("/ppt/slides/", "/ppt/notesSlides/", "/ppt/media/")):
                self.ct.remove(part)
        default = self.ct.find("ct:Default[@Extension='xml']", NS)
        if default is not None:
            default.set("ContentType", "application/xml")
        # The source package assigns core-properties via its default XML type.
        # Once XML has a generic default, give that part its required override.
        if "docProps/core.xml" in self.blobs and self.ct.find("ct:Override[@PartName='/docProps/core.xml']", NS) is None:
            self.ct.append(el("ct:Override", PartName="/docProps/core.xml", ContentType="application/vnd.openxmlformats-package.core-properties+xml"))
        self.serial = 1

    def media_part(self, data):
        digest = hashlib.sha256(data).hexdigest()
        if digest not in self.media:
            path = f"ppt/media/studio_{len(self.media) + 1}.png"
            self.media[digest] = path
            self.blobs[path] = data
        return self.media[digest]

    def picture_data(self, source, label):
        if not isinstance(source, str):
            raise ValueError(f"{label}: PNG yoki JPEG rasm kerak.")
        if source in self.decoded:
            return self.decoded[source]
        match = re.fullmatch(r"data:image/(png|jpeg);base64,([A-Za-z0-9+/=\r\n]+)", source)
        if not match or len(match.group(2)) > math.ceil(MAX_IMAGE_BYTES / 3) * 4 + 100:
            raise ValueError(f"{label}: faqat 2 MB gacha PNG yoki JPEG rasm qabul qilinadi.")
        try:
            raw = base64.b64decode(match.group(2).replace("\n", "").replace("\r", ""), validate=True)
            if len(raw) > MAX_IMAGE_BYTES:
                raise ValueError()
            with Image.open(BytesIO(raw)) as picture:
                if picture.format != {"png": "PNG", "jpeg": "JPEG"}[match.group(1)] or picture.width * picture.height > MAX_IMAGE_PIXELS:
                    raise ValueError()
                picture.load()
                picture = ImageOps.exif_transpose(picture).convert("RGBA")
                picture.thumbnail((2560, 1440), Image.Resampling.LANCZOS)
                size = picture.size
                buf = BytesIO()
                picture.save(buf, format="PNG")
            result = (buf.getvalue(), size)
        except (ValueError, OSError, UnidentifiedImageError, binascii.Error, Image.DecompressionBombError):
            raise ValueError(f"{label}: rasm buzilgan, juda katta yoki PNG/JPEG formatida emas.") from None
        self.decoded[source] = result
        return result

    def fresh_slide(self):
        self.serial = 1
        root = E.Element(q("p:sld"), nsmap={k: NS[k] for k in ("p", "a", "r", "a14", "m", "mc")})
        root.set(q("mc:Ignorable"), "a14")
        common = el("p:cSld")
        tree = el("p:spTree")
        original = self.template.find("p:cSld/p:spTree", NS)
        tree.extend([deepcopy(original[0]), deepcopy(original[1])])
        common.append(tree)
        root.extend([common, el("p:clrMapOvr", el("a:masterClrMapping"))])
        rels = E.Element(q("rel:Relationships"), nsmap={None: NS["rel"]})
        rels.append(el("rel:Relationship", Id="rLayout", Type=NS["r"] + "/slideLayout", Target="../slideLayouts/slideLayout1.xml"))
        return root, tree, rels

    def relation(self, rels, path, kind="image"):
        rid = f"rStudio{len(rels) + 1}"
        rels.append(el("rel:Relationship", Id=rid, Type=NS["r"] + "/" + kind, Target=path))
        return rid

    def shape(self, name, box, fill=None, alpha=1, radius=0, border=None, border_alpha=1):
        shape = deepcopy(self.prototypes["!!NAV_GLASS"])
        self.serial += 1
        nv = shape.find("p:nvSpPr/p:cNvPr", NS)
        nv.clear()
        nv.set("id", str(self.serial))
        nv.set("name", name)
        body = shape.find("p:txBody", NS)
        if body is not None:
            shape.remove(body)
        sppr = shape.find("p:spPr", NS)
        sppr.clear()
        geometry = el("a:prstGeom", el("a:avLst"), prst="roundRect" if radius else "rect")
        if radius:
            # OOXML rounded rectangle adj is half radius as percentage of shorter side.
            geometry[0].append(el("a:gd", name="adj", fmla=f"val {round(min(.5, radius / min(box[2:])) * 100000)}"))
        sppr.extend([_transform(box), geometry, _fill(fill, alpha) if fill else el("a:noFill")])
        sppr.append(el("a:ln", _fill(border, border_alpha) if border else el("a:noFill"), w="9525" if border else "0"))
        return shape

    def text(self, tree, text, box, size, color, font, label, bold=False, align="l", line_height=1.28, name="Matn", hyperlink=None):
        if not text:
            return None
        lines = _wrap(text, box[2], box[3], size, font, bold, line_height, label)
        shape = self.shape(name, box)
        props = shape.find("p:nvSpPr/p:cNvPr", NS)
        props.set("descr", text)
        if hyperlink:
            props.append(el("a:hlinkClick", **{"r:id": hyperlink, "action": "ppaction://hlinksldjump"}))
        body = el("p:txBody", el("a:bodyPr", el("a:noAutofit"), wrap="none", lIns="0", tIns="0", rIns="0", bIns="0", anchor="t"), el("a:lstStyle"))
        for line in lines:
            para = el("a:p", el("a:pPr", el("a:lnSpc", el("a:spcPts", val=round(size * line_height * 75))),
                      el("a:spcBef", el("a:spcPts", val="0")), el("a:spcAft", el("a:spcPts", val="0")),
                      el("a:buNone"), _rpr(size, color, font, bold, "a:defRPr"), algn=align))
            t = el("a:t")
            t.text = line
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            run_props = _rpr(size, color, font, bold)
            if name == "Misol belgisi":
                run_props.set("spc", "150")
            para.append(el("a:r", run_props, t))
            para.append(_rpr(size, color, font, bold, "a:endParaRPr"))
            body.append(para)
        shape.append(body)
        tree.append(shape)
        return shape

    def picture(self, tree, rels, data, size, box, name, cover=False, radius=0):
        path = self.media_part(data)
        rid = self.relation(rels, "../media/" + Path(path).name)
        shape = deepcopy(self.background)
        self.serial += 1
        cnvpr = shape.find("p:nvPicPr/p:cNvPr", NS)
        cnvpr.clear()
        cnvpr.set("id", str(self.serial))
        cnvpr.set("name", name)
        fill = shape.find("p:blipFill", NS)
        fill.clear()
        fill.append(el("a:blip", **{"r:embed": rid}))
        iw, ih = size
        x, y, w, h = box
        if cover:
            crop = {}
            if iw / ih > w / h:
                part = (1 - (w / h) / (iw / ih)) / 2
                crop = {"l": round(part * 100000), "r": round(part * 100000)}
            else:
                part = (1 - (iw / ih) / (w / h)) / 2
                crop = {"t": round(part * 100000), "b": round(part * 100000)}
            fill.append(el("a:srcRect", **crop))
        else:
            scale = min(w / iw, h / ih)
            nw, nh = iw * scale, ih * scale
            box = (x + (w - nw) / 2, y + (h - nh) / 2, nw, nh)
        fill.append(el("a:stretch", el("a:fillRect")))
        sppr = shape.find("p:spPr", NS)
        sppr.clear()
        geom = el("a:prstGeom", el("a:avLst"), prst="roundRect" if radius else "rect")
        if radius:
            geom[0].append(el("a:gd", name="adj", fmla=f"val {round(min(.5, radius / min(box[2:])) * 100000)}"))
        sppr.extend([_transform(box), geom])
        tree.append(shape)
        return shape

    def formula(self, tree, rels, source, box, size, color, label):
        if not source.strip():
            return
        key = (source, size, color)
        if key not in self.formulas:
            try:
                ast = parse_formula(source)
                canonical = "$" + math_to_tex(ast) + "$"
                from matplotlib.font_manager import FontProperties
                from matplotlib.mathtext import MathTextParser
                from matplotlib.figure import Figure
                import matplotlib
                with _MATH_LOCK, matplotlib.rc_context({"mathtext.fontset": "stix", "text.usetex": False, "savefig.transparent": True}):
                    prop = FontProperties(size=size * .75, math_fontfamily="stix")
                    width, height, depth, _, _ = MathTextParser("path").parse(canonical, dpi=72, prop=prop)
                    if width <= 0 or height <= 0 or width > 1400 or height > 600:
                        raise ValueError("Formula o‘lchami juda katta.")
                    figure = Figure(figsize=((width + 4) / 72, (height + 4) / 72), dpi=192)
                    figure.text(2 / (width + 4), (depth + 2) / (height + 4), canonical, fontproperties=prop, color="#" + color)
                    output = BytesIO()
                    figure.savefig(output, format="png", dpi=192, transparent=True)
                    figure.clear()
                    payload = output.getvalue()
                self.formulas[key] = (ast, payload, ((width + 4) / .75, (height + 4) / .75))
            except ValueError as error:
                message = next((line.strip() for line in str(error).splitlines() if line.strip()), "Formulani tasvirlashning iloji bo‘lmadi.")
                if not message.startswith("Formula"):
                    message = "Formula tasvirlanmadi. Qo‘llab-quvvatlanadigan yozuvdan foydalaning."
                raise ValueError(f"{label}: {message}") from None
        ast, payload, native_size = self.formulas[key]
        if native_size[0] > box[2] * .94 or native_size[1] > box[3] * .90:
            raise ValueError(f"{label} slaydga sig‘madi. Formulani qisqartiring, oddiy matn o‘lchamini yoki Formula tuzilmasini tanlang.")
        native = self.shape("Formula", box)
        native.find("p:nvSpPr/p:cNvPr", NS).set("descr", source)
        body = el("p:txBody", el("a:bodyPr", el("a:noAutofit"), wrap="none", lIns="0", tIns="0", rIns="0", bIns="0", anchor="ctr"), el("a:lstStyle"))
        para = el("a:p", el("a:pPr", _rpr(size, color, "Cambria Math", tag="a:defRPr"), algn="ctr"))
        math = el("m:oMathPara", el("m:oMathParaPr", el("m:jc", **{"m:val": "center"})), el("m:oMath", math_to_omml(ast, size * .75, color)))
        para.append(el("a14:m", math))
        para.append(_rpr(size, color, "Cambria Math", tag="a:endParaRPr"))
        body.append(para)
        native.append(body)
        # A single standard AlternateContent shape prevents duplicated formulas.
        alternate = el("mc:AlternateContent", el("mc:Choice", native, Requires="a14"))
        fallback = el("mc:Fallback")
        with Image.open(BytesIO(payload)) as pic:
            # Keep fallback exactly at the rendered point size instead of enlarging to box.
            fw, fh = native_size
            x, y, w, h = box
            self.picture(fallback, rels, payload, pic.size, (x + (w - fw) / 2, y + (h - fh) / 2, fw, fh), "Formula: " + source)
        alternate.append(fallback)
        tree.append(alternate)

    def finish(self, document, count):
        presentation = E.fromstring(self.blobs["ppt/presentation.xml"])
        ids = presentation.find("p:sldIdLst", NS)
        ids.clear()
        rels = E.fromstring(self.blobs["ppt/_rels/presentation.xml.rels"])
        for node in list(rels):
            if node.get("Type") == NS["r"] + "/slide":
                rels.remove(node)
        for index in range(1, count + 1):
            rid = f"rStudioSlide{index}"
            ids.append(el("p:sldId", id=255 + index, **{"r:id": rid}))
            rels.append(el("rel:Relationship", Id=rid, Type=NS["r"] + "/slide", Target=f"slides/slide{index}.xml"))
        self.blobs["ppt/presentation.xml"] = xml(presentation)
        self.blobs["ppt/_rels/presentation.xml.rels"] = xml(rels)
        for extension, content_type in [("png", "image/png")]:
            if self.ct.find(f"ct:Default[@Extension='{extension}']", NS) is None:
                self.ct.append(el("ct:Default", Extension=extension, ContentType=content_type))
        self.blobs["[Content_Types].xml"] = xml(self.ct)
        app = E.fromstring(self.blobs["docProps/app.xml"])
        for child in app:
            local = E.QName(child).localname
            if local == "Slides": child.text = str(count)
            elif local == "Notes": child.text = "0"
            elif local == "Application": child.text = "Talim platformasi"
            elif local == "PresentationFormat": child.text = "On-screen Show (16:9)"
        self.blobs["docProps/app.xml"] = xml(app)
        if "docProps/core.xml" in self.blobs:
            core = E.fromstring(self.blobs["docProps/core.xml"])
            for child in core:
                name = E.QName(child).localname
                if name == "title": child.text = document.get("title", "")
                elif name == "subject": child.text = document.get("subject", "")
                elif name in ("creator", "lastModifiedBy"): child.text = "Talim platformasi"
                elif name in ("description", "keywords"): child.text = ""
            self.blobs["docProps/core.xml"] = xml(core)
        output = BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path, data in self.blobs.items():
                archive.writestr(path, data)
        return output.getvalue()


def export_pptx(document):
    """Return a complete editable .pptx, or an actionable Uzbek ValueError.

    Exactly 1–40 slides are exported. No field is shortened to force it to fit.
    Text wrapping uses measured local fonts and formulas use measured mathtext.
    Inputs are bounded and all caches except 16 font paths live for this call.
    """
    slides = _validate(document)
    deck = _Deck()
    sections = []
    first = {}
    for index, slide in enumerate(slides, 1):
        section = slide["section"] or "Taqdimot"
        if section not in first:
            first[section] = index
            sections.append(section)
    # Validate every supplied asset, even when an inactive layout hides it.
    for index, slide in enumerate(slides, 1):
        for src in (slide.get("image"), slide["design"].get("image")):
            if src:
                deck.picture_data(src, f"{index}-slayd rasmi")
    aurora = None
    for index, slide in enumerate(slides, 1):
        design = slide["design"]
        tokens = _tokens(design)
        large = design["size"] == "large"
        round_corners = design["radius"] == "round"
        root, tree, rels = deck.fresh_slide()
        tree.append(deck.shape("Orqa fon", (0, 0, 1280, 720), fill=tokens["bg"]))
        if design["background"] == "aurora":
            if aurora is None:
                try:
                    data = (ASSETS / "aurora.png").read_bytes()
                    with Image.open(BytesIO(data)) as image:
                        aurora = (data, image.size)
                except (OSError, ValueError):
                    raise ValueError("Aurora fon rasmi topilmadi. Administratorga murojaat qiling.") from None
            deck.picture(tree, rels, *aurora, (0, 0, 1280, 720), "Aurora", cover=True)
        elif design["background"] == "image":
            deck.picture(tree, rels, *deck.picture_data(design["image"], f"{index}-slayd foni"), (0, 0, 1280, 720), "Orqa fon rasmi", cover=True)
        if design["overlay"]:
            tree.append(deck.shape("Fon xiraligi", (0, 0, 1280, 720), fill="000000", alpha=design["overlay"] / 100))
        panel_alpha = 1 if design["panel"] == "solid" else tokens["panel_alpha"]
        if design["panel"] != "none":
            for name, box, radius in [("Bo‘limlar foni", (64, 30, 1152, 62), 18), ("Slayd ichki foni", (64, 116, 1152, 522), 24)]:
                tree.append(deck.shape(name, box, fill=tokens["panel"], alpha=panel_alpha, radius=radius if round_corners else 0,
                                       border=tokens["border"], border_alpha=tokens["border_alpha"]))
        section = slide["section"] or "Taqdimot"
        current = sections.index(section)
        start = (current // 5) * 5
        shown = sections[start:start + 5]
        tab_width = 1152 / len(shown)
        for offset, item in enumerate(shown):
            x = 64 + offset * tab_width
            active = item == section
            if active:
                tree.append(deck.shape("Faol bo‘lim", (x + 5, 35, tab_width - 10, 52), fill=tokens["accent"], alpha=.23,
                                       radius=12 if round_corners else 0, border=tokens["accent"], border_alpha=.55))
            rid = deck.relation(rels, f"slide{first[item]}.xml", "slide")
            deck.text(tree, item, (x + 12, 39, tab_width - 24, 46), 16, tokens["fg"] if active else tokens["muted"],
                      tokens["font"], f"{index}-slayd bo‘lim nomi", bold=active, align="ctr", line_height=1.28, name="Bo‘lim: " + item, hyperlink=rid)
        title_size, body_size, example_size = ((48, 28, 23) if large else (42, 24, 20))
        formula_size = 60 if large else 52
        deck.text(tree, slide["title"], (96, 146, 1088, 96), title_size, tokens["fg"], tokens["font"],
                  f"{index}-slayd sarlavhasi", bold=True, line_height=1.12, name="Sarlavha")
        formula, example = bool(slide["formula"].strip()), bool(slide["example"].strip())
        layout = slide["layout"]
        if layout == "formula":
            body_box, formula_box = (96, 254, 1088, 92), (120, 356, 1040, 140)
            label_box, example_box = (96, 514, 1088, 20), (96, 542, 1088, 66)
        elif layout == "image":
            body_box, formula_box = (628, 254, 556, 132 if formula else 252), (640, 400, 532, 104)
            label_box, example_box = (628, 522, 556, 20), (628, 550, 556, 58)
            if slide.get("image"):
                deck.picture(tree, rels, *deck.picture_data(slide["image"], f"{index}-slayd rasmi"), (96, 254, 496, 346), "Slayd rasmi", radius=12 if round_corners else 0)
        else:
            body_box = (96, 254, 1088, 154 if formula else 250 if example else 346)
            formula_box, label_box, example_box = (120, 420, 1040, 92), (96, 520, 1088, 20), (96, 548, 1088, 60)
        deck.text(tree, slide["body"], body_box, body_size, tokens["fg"], tokens["font"], f"{index}-slayd matni", name="Asosiy matn")
        if formula:
            deck.formula(tree, rels, slide["formula"], formula_box, formula_size, tokens["fg"], f"{index}-slayd formulasi")
        if example:
            deck.text(tree, "MISOL", label_box, 14, tokens["accent"], tokens["font"], f"{index}-slayd misol belgisi", bold=True, name="Misol belgisi")
            deck.text(tree, slide["example"], example_box, example_size, tokens["fg"], tokens["font"], f"{index}-slayd misoli", line_height=1.25, name="Misol")
        deck.text(tree, document.get("subject") or document.get("title", ""), (96, 665, 960, 24), 14, tokens["muted"], tokens["font"], "Fan nomi", name="Fan")
        deck.text(tree, f"{index:02d} / {len(slides):02d}", (1110, 665, 74, 24), 14, tokens["muted"], tokens["font"], "Slayd raqami", align="r", name="Slayd raqami")
        deck.blobs[f"ppt/slides/slide{index}.xml"] = xml(root)
        deck.blobs[f"ppt/slides/_rels/slide{index}.xml.rels"] = xml(rels)
        deck.ct.append(el("ct:Override", PartName=f"/ppt/slides/slide{index}.xml", ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"))
    return deck.finish(document, len(slides))

# Restricted TeX parser and dual OMML/mathtext serializer are below.  Kept in this
# module so deployments only need this file and the two bundled template assets.

"""Bounded, in-process TeX subset shared by native Office Math and mathtext.

This module deliberately has no renderer, external process, file or network IO.
Unsupported syntax raises an Uzbek ValueError instead of losing formula content.
The returned immutable AST is the sole source for both export representations.
"""


from dataclasses import dataclass
import math
import re

from lxml import etree as E


MAX_SOURCE = 400
MAX_DEPTH = 12
MAX_NODES = 250
_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
}


@dataclass(frozen=True)
class MathNode:
    kind: str
    value: str = ""
    children: tuple["MathNode", ...] = ()
    extra: str = ""


# value = (Office Math character, canonical mathtext token, italic).
_SYMBOLS = {
    "alpha": ("α", r"\alpha", True), "beta": ("β", r"\beta", True),
    "gamma": ("γ", r"\gamma", True), "delta": ("δ", r"\delta", True),
    "epsilon": ("ϵ", r"\epsilon", True), "varepsilon": ("ε", r"\varepsilon", True),
    "zeta": ("ζ", r"\zeta", True), "eta": ("η", r"\eta", True),
    "theta": ("θ", r"\theta", True), "vartheta": ("ϑ", r"\vartheta", True),
    "iota": ("ι", r"\iota", True), "kappa": ("κ", r"\kappa", True),
    "varkappa": ("ϰ", "ϰ", True), "lambda": ("λ", r"\lambda", True),
    "mu": ("μ", r"\mu", True), "nu": ("ν", r"\nu", True),
    "xi": ("ξ", r"\xi", True), "omicron": ("ο", "ο", True),
    "pi": ("π", r"\pi", True), "varpi": ("ϖ", r"\varpi", True),
    "rho": ("ρ", r"\rho", True), "varrho": ("ϱ", r"\varrho", True),
    "sigma": ("σ", r"\sigma", True), "varsigma": ("ς", r"\varsigma", True),
    "tau": ("τ", r"\tau", True), "upsilon": ("υ", r"\upsilon", True),
    "phi": ("ϕ", r"\phi", True), "varphi": ("φ", r"\varphi", True),
    "chi": ("χ", r"\chi", True), "psi": ("ψ", r"\psi", True),
    "omega": ("ω", r"\omega", True),
    "times": ("×", r"\times", False), "cdot": ("·", r"\cdot", False),
    "pm": ("±", r"\pm", False), "mp": ("∓", r"\mp", False),
    "leq": ("≤", r"\leq", False), "le": ("≤", r"\leq", False),
    "geq": ("≥", r"\geq", False), "ge": ("≥", r"\geq", False),
    "neq": ("≠", r"\neq", False), "ne": ("≠", r"\neq", False),
    "approx": ("≈", r"\approx", False), "infty": ("∞", r"\infty", False),
    "to": ("→", r"\to", False), "rightarrow": ("→", r"\to", False),
    "Rightarrow": ("⇒", r"\Rightarrow", False),
}
for _name, _char in zip(
    ("Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta", "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"),
    "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ",
):
    _token = "\\" + _name if _name in {"Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega"} else r"\mathrm{" + _char + "}"
    _SYMBOLS[_name] = (_char, _token, False)

_BY_CHAR = {values[0]: name for name, values in _SYMBOLS.items()}
_FUNCTIONS = frozenset(("sin", "cos", "tan", "log", "ln", "exp", "min", "max"))
_SPACING = {",": "\u2009", ":": "\u2005", ";": "\u2004", " ": " ", "quad": "\u2003", "qquad": "\u2003\u2003"}
_SPACE_TEX = {"\u2009": r"\,", "\u2005": r"\:", "\u2004": r"\;", " ": "\\ ", "\u2003": r"\quad ", "\u2003\u2003": r"\qquad "}
_DELIM_COMMANDS = {"{": "{", "}": "}", "vert": "|", "lvert": "|", "rvert": "|", "lbrace": "{", "rbrace": "}", "lbrack": "[", "rbrack": "]"}
_CLOSE = {"(": ")", "[": "]", "|": "|", "{": "}"}
_TEXT_CHARS = frozenset(" .,:;/+-=()[]|!?%")


def _error(message: str, position: int | None = None) -> ValueError:
    suffix = f" (belgi {position + 1})." if position is not None else "."
    return ValueError("Formula xatosi: " + message.rstrip(".") + suffix)


class _Parser:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.nodes = 0

    def node(self, kind, value="", children=(), extra=""):
        self.nodes += 1
        if self.nodes > MAX_NODES:
            raise _error(f"formula juda murakkab; ko‘pi bilan {MAX_NODES} tugun ruxsat etiladi")
        return MathNode(kind, value, tuple(children), extra)

    def guard(self, depth):
        if depth > MAX_DEPTH:
            raise _error(f"ichma-ich tuzilma {MAX_DEPTH} darajadan oshmasligi kerak", self.pos)

    def spaces(self):
        while self.pos < len(self.source) and self.source[self.pos].isspace():
            self.pos += 1

    def command_at(self):
        if self.pos >= len(self.source) or self.source[self.pos] != "\\":
            return None
        end = self.pos + 1
        if end >= len(self.source):
            raise _error("teskari qiya chiziqdan keyin buyruq kerak", self.pos)
        if self.source[end].isascii() and self.source[end].isalpha():
            while end < len(self.source) and self.source[end].isascii() and self.source[end].isalpha():
                end += 1
        else:
            end += 1
        return self.source[self.pos + 1:end], end

    def sequence(self, depth=0, close=None, right=False):
        self.guard(depth)
        items = []
        upright = False
        rm_needs_content = False
        while True:
            self.spaces()
            if self.pos >= len(self.source):
                if close is not None or right:
                    raise _error("ochilgan qavs yoki guruh yopilmagan", self.pos)
                break
            char = self.source[self.pos]
            command = self.command_at() if char == "\\" else None
            if right and command and command[0] == "right":
                break
            if close is not None and ((len(close) == 1 and char == close) or (command and close == "\\}" and command[0] == "}")):
                break
            if char in ")]}":
                raise _error("yopuvchi qavs mos kelmaydi", self.pos)
            if command and command[0] in {"right", "}"}:
                raise _error("yopuvchi qavs uchun ochuvchi qavs topilmadi", self.pos)
            if command and command[0] == "rm":
                self.pos = command[1]
                upright = True
                rm_needs_content = True
                continue
            atom = self.atom(depth + 1)
            atom = self.scripts(atom, depth + 1)
            if upright:
                atom = self.node("upright", children=(atom,))
            items.append(atom)
            rm_needs_content = False
        if rm_needs_content:
            raise _error("\\rm buyrug‘idan keyin matn kerak", self.pos)
        if not items:
            raise _error("bo‘sh formula yoki bo‘sh guruhga ruxsat berilmaydi", self.pos)
        return self.node("sequence", children=items)

    def group(self, depth):
        self.guard(depth)
        self.spaces()
        if self.pos >= len(self.source) or self.source[self.pos] != "{":
            raise _error("ushbu buyruq uchun { ... } guruhi kerak", self.pos)
        self.pos += 1
        contents = self.sequence(depth, close="}")
        self.pos += 1
        return self.node("group", children=contents.children)

    def argument(self, depth):
        self.guard(depth)
        self.spaces()
        if self.pos >= len(self.source):
            raise _error("buyruq yoki daraja argumenti yetishmaydi", self.pos)
        if self.source[self.pos] == "{":
            return self.group(depth)
        return self.atom(depth)

    def scripts(self, base, depth):
        self.guard(depth)
        sub = sup = None
        while True:
            self.spaces()
            if self.pos >= len(self.source) or self.source[self.pos] not in "_^":
                break
            mark = self.source[self.pos]
            if (mark == "_" and sub is not None) or (mark == "^" and sup is not None):
                raise _error("bir asos uchun takroriy indeks yoki daraja; { ... } bilan guruhlang", self.pos)
            self.pos += 1
            argument = self.argument(depth + 1)
            if mark == "_":
                sub = argument
            else:
                sup = argument
        if sub is not None and sup is not None:
            return self.node("subsup", children=(base, sub, sup))
        if sub is not None:
            return self.node("sub", children=(base, sub))
        if sup is not None:
            return self.node("sup", children=(base, sup))
        return base

    def delimiter(self, depth, opening, escaped=False):
        close = _CLOSE[opening]
        closing_token = "\\}" if escaped else close
        inner = self.sequence(depth, close=closing_token)
        self.pos += 2 if escaped else 1
        return self.node("delimiter", opening, inner.children, close)

    def read_delimiter(self, opening):
        self.spaces()
        if self.pos >= len(self.source):
            raise _error("\\left yoki \\right dan keyin qavs kerak", self.pos)
        command = self.command_at()
        if command:
            if command[0] not in _DELIM_COMMANDS:
                raise _error("qo‘llab-quvvatlanmaydigan qavs buyrug‘i", self.pos)
            char = _DELIM_COMMANDS[command[0]]
            self.pos = command[1]
        else:
            char = self.source[self.pos]
            self.pos += 1
        valid = "([|{." if opening else ")]|}."
        if char not in valid:
            raise _error("qavs turi mos kelmaydi", self.pos - 1)
        return "" if char == "." else char

    def text(self, depth):
        self.guard(depth)
        self.spaces()
        if self.pos >= len(self.source) or self.source[self.pos] != "{":
            raise _error("\\text uchun { ... } guruhi kerak", self.pos)
        self.pos += 1
        result = []
        while self.pos < len(self.source) and self.source[self.pos] != "}":
            char = self.source[self.pos]
            if char == "\\":
                command = self.command_at()
                if command[0] not in {" ", "%", "{", "}"}:
                    raise _error("\\text ichida faqat oddiy matn va bo‘sh joylar ruxsat etiladi", self.pos)
                char = command[0]
                self.pos = command[1]
            else:
                if not (char.isascii() and char.isalnum() or char in _TEXT_CHARS or char in _BY_CHAR):
                    raise _error("\\text ichidagi belgi qo‘llab-quvvatlanmaydi", self.pos)
                self.pos += 1
            result.append(char)
        if self.pos >= len(self.source):
            raise _error("\\text guruhi yopilmagan", self.pos)
        self.pos += 1
        if not result or not "".join(result).strip():
            raise _error("\\text guruhi bo‘sh bo‘lmasligi kerak", self.pos)
        return self.node("text", "".join(result))

    def atom(self, depth):
        self.guard(depth)
        self.spaces()
        if self.pos >= len(self.source):
            raise _error("formula argumenti yetishmaydi", self.pos)
        char = self.source[self.pos]
        if char == "{":
            return self.group(depth)
        if char in "([|":
            self.pos += 1
            return self.delimiter(depth, char)
        if char in ")]}_^":
            raise _error("belgi uchun asos yoki ochuvchi qavs yetishmaydi", self.pos)
        if char == "\\":
            command, self.pos = self.command_at()
            if command in _SYMBOLS:
                return self.node("symbol", command)
            if command in _FUNCTIONS:
                return self.node("function", command)
            if command in _SPACING:
                return self.node("space", _SPACING[command])
            if command in {"frac", "dfrac", "tfrac"}:
                numerator = self.argument(depth + 1)
                denominator = self.argument(depth + 1)
                return self.node("fraction", children=(numerator, denominator))
            if command == "sqrt":
                self.spaces()
                degree = None
                if self.pos < len(self.source) and self.source[self.pos] == "[":
                    self.pos += 1
                    degree = self.sequence(depth + 1, close="]")
                    self.pos += 1
                radicand = self.argument(depth + 1)
                return self.node("root", children=(radicand,) if degree is None else (radicand, degree))
            if command == "left":
                opening = self.read_delimiter(True)
                inner = self.sequence(depth, right=True)
                closing_command = self.command_at()
                if closing_command is None or closing_command[0] != "right":
                    raise _error("\\left uchun \\right yetishmaydi", self.pos)
                self.pos = closing_command[1]
                closing = self.read_delimiter(False)
                return self.node("delimiter", opening, inner.children, closing)
            if command == "{":
                return self.delimiter(depth, "{", escaped=True)
            if command == "mathrm":
                return self.node("upright", children=(self.argument(depth + 1),))
            if command == "text":
                return self.text(depth + 1)
            if command == "%":
                return self.node("char", "%")
            raise _error(f"\\{command} buyrug‘i qo‘llab-quvvatlanmaydi", self.pos - len(command) - 1)
        self.pos += 1
        if char in _BY_CHAR:
            return self.node("symbol", _BY_CHAR[char])
        if char == "−":
            return self.node("char", "-")
        if char == "*":
            return self.node("char", "*", extra=r"\ast")
        if char.isascii() and (char.isalnum() or char in "+-=<>/.,:;!?%"):
            return self.node("char", char)
        raise _error(f"{char!r} belgisi qo‘llab-quvvatlanmaydi", self.pos - 1)


def _validate_ast(node, depth=0):
    if not isinstance(node, MathNode):
        raise _error("formula daraxti noto‘g‘ri")
    if depth > MAX_DEPTH:
        raise _error(f"ichma-ich tuzilma {MAX_DEPTH} darajadan oshmasligi kerak")
    return 1 + sum(_validate_ast(child, depth + 1) for child in node.children)


def parse_formula(source: str) -> MathNode:
    """Parse <=400 characters into a <=250-node, <=12-level immutable AST."""
    if not isinstance(source, str):
        raise _error("formula matn bo‘lishi kerak")
    if len(source) > MAX_SOURCE:
        raise _error(f"formula {MAX_SOURCE} belgidan oshmasligi kerak")
    source = source.strip()
    for left, right in (("$$", "$$"), ("$", "$"), (r"\(", r"\)"), (r"\[", r"\]")):
        if source.startswith(left) and source.endswith(right) and len(source) >= len(left) + len(right):
            source = source[len(left):-len(right)].strip()
            break
    if not source:
        raise _error("formula bo‘sh bo‘lmasligi kerak")
    parser = _Parser(source)
    tree = parser.sequence()
    if parser.pos != len(source):
        raise _error("formula to‘liq o‘qilmadi", parser.pos)
    if _validate_ast(tree) > MAX_NODES:
        raise _error(f"formula {MAX_NODES} tugundan oshmasligi kerak")
    return tree


def math_to_tex(ast: MathNode) -> str:
    """Canonical mathtext-compatible TeX without dollar wrappers."""
    def render(node):
        kind = node.kind
        children = node.children
        if kind == "sequence":
            return "".join(render(child) for child in children)
        if kind == "group":
            return "{" + "".join(render(child) for child in children) + "}"
        if kind == "char":
            return (node.extra + " ") if node.extra else (r"\%" if node.value == "%" else node.value)
        if kind == "symbol":
            return _SYMBOLS[node.value][1] + " "
        if kind == "function":
            return "\\" + node.value + " "
        if kind == "space":
            return _SPACE_TEX[node.value]
        if kind == "text":
            text = "".join("\\ " if ch == " " else "\\" + ch if ch in "{}%" else ch for ch in node.value)
            return r"\mathrm{" + text + "}"
        if kind == "upright":
            return r"\mathrm{" + render(children[0]) + "}"
        if kind in {"sub", "sup", "subsup"}:
            base = "{" + render(children[0]) + "}"
            if kind == "sub":
                return base + "_{" + render(children[1]) + "}"
            if kind == "sup":
                return base + "^{" + render(children[1]) + "}"
            return base + "_{" + render(children[1]) + "}^{" + render(children[2]) + "}"
        if kind == "fraction":
            return r"\frac{" + render(children[0]) + "}{" + render(children[1]) + "}"
        if kind == "root":
            degree = "[" + render(children[1]) + "]" if len(children) == 2 else ""
            return r"\sqrt" + degree + "{" + render(children[0]) + "}"
        if kind == "delimiter":
            opening = "\\{" if node.value == "{" else node.value or "."
            closing = "\\}" if node.extra == "}" else node.extra or "."
            return r"\left" + opening + " " + "".join(render(child) for child in children) + r"\right" + closing + " "
        raise _error("formula daraxtida noma’lum tugun bor")
    _validate_ast(ast)
    return render(ast)


def _q(name):
    prefix, local = name.split(":", 1)
    return "{" + _NS[prefix] + "}" + local


def _el(tag, *children, **attrs):
    node = E.Element(_q(tag))
    for key, value in attrs.items():
        node.set(_q(key) if ":" in key else key, str(value))
    for child in children:
        node.extend(child if isinstance(child, (tuple, list)) else (child,))
    return node


def math_to_omml(ast: MathNode, size_points: float, color: str) -> list:
    """Return fresh OMML expression nodes for an m:oMath element."""
    if isinstance(size_points, bool) or not isinstance(size_points, (float, int)) or not math.isfinite(size_points) or not 1 <= size_points <= 400:
        raise _error("formula shrift o‘lchami noto‘g‘ri")
    if not isinstance(color, str) or not re.fullmatch(r"#?[0-9a-fA-F]{6}", color):
        raise _error("formula rangi noto‘g‘ri")
    _validate_ast(ast)
    size = str(round(size_points * 100))
    color = color.lstrip("#").upper()

    def props():
        return _el("a:rPr", _el("a:solidFill", _el("a:srgbClr", val=color)),
                   _el("a:latin", typeface="Cambria Math"), _el("a:ea", typeface="Cambria Math"),
                   _el("a:cs", typeface="Cambria Math"), sz=size, b="0", lang="en-US")

    def ctrl():
        return _el("m:ctrlPr", props())

    def run(text, italic=False):
        text_node = _el("m:t")
        text_node.text = text
        if any(ch.isspace() for ch in text):
            text_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return _el("m:r", _el("m:rPr", _el("m:sty", **{"m:val": "i" if italic else "p"})), props(), text_node)

    def render(node, upright=False):
        kind, children = node.kind, node.children
        if kind in {"sequence", "group"}:
            return [item for child in children for item in render(child, upright)]
        if kind == "upright":
            return render(children[0], True)
        if kind in {"text", "space", "function"}:
            return [run(node.value)]
        if kind == "char":
            value = "−" if node.value == "-" else "∗" if node.value == "*" else node.value
            return [run(value, not upright and node.value.isalpha())]
        if kind == "symbol":
            value, _tex, italic = _SYMBOLS[node.value]
            return [run(value, italic and not upright)]
        if kind in {"sub", "sup", "subsup"}:
            tag = {"sub": "sSub", "sup": "sSup", "subsup": "sSubSup"}[kind]
            result = _el("m:" + tag, _el("m:" + tag + "Pr", ctrl()), _el("m:e", render(children[0], upright)))
            if kind in {"sub", "subsup"}:
                result.append(_el("m:sub", render(children[1], upright)))
            if kind in {"sup", "subsup"}:
                result.append(_el("m:sup", render(children[-1], upright)))
            return [result]
        if kind == "fraction":
            return [_el("m:f", _el("m:fPr", _el("m:type", **{"m:val": "bar"}), ctrl()),
                        _el("m:num", render(children[0], upright)), _el("m:den", render(children[1], upright)))]
        if kind == "root":
            return [_el("m:rad", _el("m:radPr", _el("m:degHide", **{"m:val": "0" if len(children) == 2 else "1"}), ctrl()),
                        _el("m:deg", render(children[1], upright) if len(children) == 2 else []), _el("m:e", render(children[0], upright)))]
        if kind == "delimiter":
            return [_el("m:d", _el("m:dPr", _el("m:begChr", **{"m:val": node.value}),
                        _el("m:endChr", **{"m:val": node.extra}), _el("m:grow", **{"m:val": "1"}), ctrl()),
                        _el("m:e", [item for child in children for item in render(child, upright)]))]
        raise _error("formula daraxtida noma’lum tugun bor")
    return render(ast)
