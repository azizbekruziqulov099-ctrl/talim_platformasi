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

from .presentation_layout_validation import validate_slide_geometry

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
DEFAULT_DESIGN = {"template": "glass", "transition": "fade", "background": "aurora", "color": "#17394b", "image": None, "overlay": 25,
                  "panel": "glass", "accent": "cyan", "text": "auto", "font": "sans", "size": "normal", "radius": "round"}
LAYOUTS = ("text", "formula", "image", "cover", "two_columns", "two_images", "three_cards", "steps")


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
    if isinstance(value.get("template"), str) and value["template"] in TEMPLATE_DEFAULTS:
        result.update(TEMPLATE_DEFAULTS[value["template"]])
    result.update(value)
    choices = {"template": tuple(TEMPLATE_DEFAULTS), "transition": ("none", "fade", "push", "wipe"),
               "background": ("aurora", "paper", "midnight", "solid", "image"),
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
    if not isinstance(document, dict) or isinstance(document.get("schema"), bool) or document.get("schema") not in (1, 2):
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
    _check_text(document.get("audience", ""), 120, "Auditoriya")
    global_design = _design(document.get("design"))
    out = []
    for index, slide in enumerate(slides, 1):
        if not isinstance(slide, dict) or slide.get("layout", "text") not in LAYOUTS:
            raise ValueError(f"{index}-slayd: tuzilma noto‘g‘ri.")
        item = dict(slide)
        for name, maximum, label in [("title", 100, "sarlavha"), ("section", 60, "bo‘lim"), ("body", 600, "matn"),
                                     ("body2", 400, "2-matn"), ("body3", 400, "3-matn"),
                                     ("formula", 400, "formula"), ("example", 250, "misol"),
                                     ("image_prompt", 240, "1-rasm tavsifi"), ("image2_prompt", 240, "2-rasm tavsifi"),
                                     ("image_caption", 100, "1-rasm izohi"), ("image2_caption", 100, "2-rasm izohi")]:
            item[name] = _check_text(slide.get(name, ""), maximum, f"{index}-slayd {label}")
        item["design"] = _design(slide.get("design") or global_design)
        item["layout"] = item.get("layout", "text")
        edits = validate_slide_geometry(item)
        for field in ("placements", "elements"):
            if field in slide:
                item[field] = edits[field]
        out.append(item)
    return out


# Pixel geometry mirrors src/presentations/layouts.js. Cross-runtime fixtures guard
# every template/layout, optional slot and font-size combination against drift.
SECTION_COLORS = ('#176b59', '#275fa5', '#7850a0', '#a64b3c', '#765b22')
TEMPLATE_DEFAULTS = {
    'pencil': {'background': 'paper', 'overlay': 0, 'panel': 'none', 'accent': 'green', 'text': 'dark'},
    'arc': {'background': 'paper', 'overlay': 0, 'panel': 'none', 'accent': 'green', 'text': 'dark'},
    'spiral': {'background': 'paper', 'overlay': 0, 'panel': 'none', 'accent': 'amber', 'text': 'dark'},
    'bands': {'background': 'paper', 'overlay': 0, 'panel': 'none', 'accent': 'violet', 'text': 'dark'},
    'glass': {'background': 'aurora', 'overlay': 25, 'panel': 'glass', 'accent': 'cyan', 'text': 'auto'},
    'ribbon': {'background': 'midnight', 'overlay': 0, 'panel': 'solid', 'accent': 'blue', 'text': 'light'},
    'split': {'background': 'paper', 'overlay': 0, 'panel': 'none', 'accent': 'violet', 'text': 'dark'},
    'gallery': {'background': 'paper', 'overlay': 0, 'panel': 'solid', 'accent': 'blue', 'text': 'dark'},
    'steps': {'background': 'midnight', 'overlay': 10, 'panel': 'glass', 'accent': 'green', 'text': 'light'},
}
NEW_FAMILIES = frozenset(('pencil', 'arc', 'spiral', 'bands'))
MOTIF_COLORS = ('#98b879', '#63a99d', '#d9b36c', '#9b8fb8')


def _box(x, y, w, h, **more):
    return {'x': x, 'y': y, 'w': w, 'h': h, **more}


def _coords(box):
    return tuple(box[key] for key in ('x', 'y', 'w', 'h'))


def _polygon(points, fill, opacity=1):
    x, y = min(point[0] for point in points), min(point[1] for point in points)
    w, h = max(point[0] for point in points) - x, max(point[1] for point in points) - y
    return _box(x, y, w, h, kind='polygon', points=[[round(px - x, 3), round(py - y, 3)] for px, py in points], fill=fill, opacity=opacity)


def _family_decorations(identity):
    shapes = []
    def rect(x, y, w, h, fill, radius=0, opacity=1):
        shapes.append(_box(x, y, w, h, kind='rect', fill=fill, radius=radius, opacity=opacity))
    def poly(points, fill, opacity=1):
        shapes.append(_polygon(points, fill, opacity))
    if identity == 'pencil':
        rect(64, 122, 176, 506, '#dfe8da', 32, .36)
        rect(116, 164, 70, 50, '#a28ca9', 15)
        rect(116, 202, 70, 20, '#c4cccf')
        rect(116, 222, 70, 322, '#90ad66')
        rect(127, 222, 13, 322, '#bed59c')
        rect(173, 222, 13, 322, '#66884f')
        poly([[116, 544], [186, 544], [151, 622]], '#d9bea1')
        poly([[140, 598], [162, 598], [151, 622]], '#344b50')
        for at, color in enumerate(MOTIF_COLORS):
            y = 250 + at * 66
            poly([[151, y], [219, y], [231, y + 10], [231, y + 35], [151, y + 35]], color)
            poly([[219, y], [231, y + 10], [219, y + 10]], '#314c46', .25)
            rect(151, y + 7, 55, 2, '#ffffff', 0, .5)
    elif identity == 'arc':
        for at, radius in enumerate((248, 204, 160, 116)):
            cx, cy, thickness = 284, 594, 34
            outer, inner = [], []
            for step in range(25):
                angle = math.pi + step / 24 * math.pi / 2
                outer.append([cx + radius * math.cos(angle), cy + radius * math.sin(angle)])
            for step in range(24, -1, -1):
                angle = math.pi + step / 24 * math.pi / 2
                inner.append([cx + (radius - thickness) * math.cos(angle), cy + (radius - thickness) * math.sin(angle)])
            poly(outer + [[320, cy - radius], [320, cy - radius + thickness]] + inner, MOTIF_COLORS[at])
            rect(286, cy - radius + 7, 25, 3, '#ffffff', 1, .55)
            poly([[320, cy - radius], [328, cy - radius + 8], [320, cy - radius + 16]], '#314c46', .22)
        rect(82, 181, 98, 6, '#98b879', 3)
        rect(82, 202, 148, 3, '#b5c6b6', 1, .75)
        rect(82, 218, 116, 3, '#b5c6b6', 1, .55)
    elif identity == 'spiral':
        rect(84, 568, 1112, 12, '#a8b1b3', 6)
        rect(84, 568, 1112, 4, '#dbe0df', 2)
        for turn in range(5):
            x = 108 + turn * 216
            for half in (0, 1):
                upper, lower = [], []
                for step in range(19):
                    t = half / 2 + step / 36
                    px, py = x + t * 216, 574 - 51 * math.sin(t * math.pi * 2)
                    upper.append([px, py - 14])
                    lower.insert(0, [px, py + 14])
                poly(upper + lower, '#ac684c' if half else '#ce9672')
            rect(x + 80, 550, 46, 3, '#f4d6b4', 1, .8)
    elif identity == 'bands':
        rect(980, 170, 192, 448, '#dfe4e2', 26)
        rect(993, 176, 170, 435, '#f6f7f3', 18)
        for at, color in enumerate(('#9d86b7', '#d28f7e', '#93b77b', '#75a8af')):
            y = 218 + at * 90
            rect(954, y - 11, 26, 72, color, 7)
            poly([[954, y - 11], [982, y + 2], [982, y + 58], [954, y + 48]], '#314c46', .24)
            rect(976, y, 212, 66, color, 5)
            rect(990, y + 8, 182, 3, '#ffffff', 1, .38)
            poly([[1188, y], [1207, y + 15], [1207, y + 77], [1188, y + 66]], color)
            poly([[1188, y], [1207, y + 15], [1188, y + 15]], '#314c46', .3)
            rect(1003, y + 25, 38, 4, '#ffffff', 2, .72)
            rect(1003, y + 39, 132, 3, '#ffffff', 1, .45)
    return shapes


def _apply_placements(spec, slide):
    placements = slide.get('placements') or {}
    def placed(field):
        return {key: placements[field][key] for key in ('x', 'y', 'w', 'h')}
    for field in ('title', 'formula', 'example'):
        if spec.get(field) is not None and field in placements:
            spec[field].update(placed(field))
            if field == 'example':
                spec[field]['label'].update(x=spec[field]['x'], y=spec[field]['y'] - 28, w=spec[field]['w'])
    for slot in spec['bodySlots']:
        if slot['field'] in placements:
            slot.update(placed(slot['field']))
    for slot in spec['imageSlots']:
        if slot['field'] in placements:
            slot.update(placed(slot['field']))
            if slot.get('caption'):
                slot['caption'].update(x=slot['x'], y=slot['y'] + slot['h'] + 8, w=slot['w'])
    spec['elements'] = deepcopy(slide.get('elements') or [])
    spec['bodies'], spec['images'] = spec['bodySlots'], spec['imageSlots']
    return spec


def _apply_infographic(spec, design):
    """Reference compositions with body text inside or around the vector motif."""
    identity, large = spec['template'], design.get('size') == 'large'
    spec['title'] = _box(96, 126, 1088, 84, fontSize=44 if large else 38)
    spec['panel'] = _box(64, 110, 1152, 530, radius=0 if design.get('radius') == 'square' else 24)
    for at, tab in enumerate(spec['tabs']):
        tab.update(x=96 + at * 1088 / len(spec['tabs']), y=36, w=1088 / len(spec['tabs']), h=42)
    spec['decorations'], spec['bodySlots'] = [], []
    def rect(x, y, w, h, fill, radius=0, opacity=1):
        spec['decorations'].append(_box(x, y, w, h, kind='rect', fill=fill, radius=radius, opacity=opacity))
    def poly(points, fill, opacity=1):
        spec['decorations'].append(_polygon(points, fill, opacity))
    def body(at, x, y, w, h):
        spec['bodySlots'].append(_box(x, y, w, h, field=f'body{at + 1}' if at else 'body', fontSize=24 if large else 22))
    def number(at, x, y, color):
        spec['decorations'].append(_box(x, y, 36, 36, kind='circle', fill=color, opacity=1, radius=18, text=str(at + 1), fontSize=18))
    if identity == 'pencil':
        rect(608, 226, 64, 42, '#a28ca9', 13)
        rect(608, 258, 64, 17, '#c4cccf')
        rect(608, 275, 64, 286, '#90ad66')
        rect(618, 275, 12, 286, '#bed59c')
        rect(660, 275, 12, 286, '#66884f')
        poly([[608, 561], [672, 561], [640, 625]], '#d9bea1')
        poly([[630, 606], [650, 606], [640, 625]], '#344b50')
        for at, (x, y, w, h) in enumerate(((96, 266, 424, 124), (760, 358, 424, 124), (96, 468, 424, 124))):
            color = MOTIF_COLORS[at]
            body(at, x, y + 16, w, h - 16)
            rect(x, y, w, 4, color, 2)
            left, dot_x, dot_y = at != 1, 553 if at != 1 else 691, y + 12
            rect(x + w if left else 672, dot_y + 17, 88 if left else x - 672, 2, color)
            number(at, dot_x, dot_y, color)
    elif identity == 'arc':
        for at, radius in enumerate((360, 240, 120)):
            cx, cy, thickness, outer, inner = 380, 596, 112, [], []
            for step in range(33):
                angle = math.pi + step / 32 * math.pi / 2
                outer.append([cx + radius * math.cos(angle), cy + radius * math.sin(angle)])
            for step in range(32, -1, -1):
                angle = math.pi + step / 32 * math.pi / 2
                inner.append([cx + (radius - thickness) * math.cos(angle), cy + (radius - thickness) * math.sin(angle)])
            y, color = cy - radius, ('#c7dbac', '#aed7cd', '#ead5ac')[at]
            poly(outer + [[1170, y], [1184, y + 12], [1184, y + thickness - 12], [1170, y + thickness]] + inner, color)
            rect(414, y + 4, 714, 2, '#ffffff', 1, .5)
            number(at, 352, y + 38, MOTIF_COLORS[at])
            body(at, 414, y + 8, 714, 96)
    elif identity == 'spiral':
        rect(92, 408, 1096, 12, '#a8b1b3', 6)
        rect(92, 408, 1096, 4, '#dbe0df', 2)
        for turn in range(3):
            x = 176 + turn * 336
            for half in (0, 1):
                upper, lower = [], []
                for step in range(25):
                    t = half / 2 + step / 48
                    px, py = x + t * 216, 414 - 64 * math.sin(t * math.pi * 2)
                    upper.append([px, py - 18])
                    lower.insert(0, [px, py + 18])
                poly(upper + lower, '#ac684c' if half else '#ce9672')
            above, bx = turn != 1, 96 + turn * 384
            body(turn, bx, 230 if above else 526, 320, 96)
            rect(bx, 224 if above else 512, 320, 4, '#ce9672', 2)
            number(turn, bx, 336 if above else 462, '#ac684c')
    elif identity == 'bands':
        rect(274, 216, 748, 400, '#dfe4e2', 28)
        rect(286, 224, 724, 384, '#f6f7f3', 20)
        for at, color in enumerate(('#d9c9e6', '#e9c8b9', '#c7ddbb')):
            y = 236 + at * 120
            rect(244, y - 10, 40, 104, color, 6)
            poly([[244, y - 10], [294, y + 4], [294, y + 104], [244, y + 94]], '#314c46', .2)
            rect(282, y, 780, 112, color, 6)
            poly([[1062, y], [1100, y + 18], [1100, y + 126], [1062, y + 112]], color)
            poly([[1062, y], [1100, y + 18], [1062, y + 18]], '#314c46', .24)
            rect(308, y + 3, 724, 3, '#ffffff', 1, .44)
            number(at, 300, y + 38, ('#9d86b7', '#bd7d69', '#799e60')[at])
            body(at, 354, y + 8, 670, 96)


def _apply_motif_palette(spec, design):
    """Recolor the principal motif while retaining its secondary color bands."""
    accent = design.get('accent')
    if not accent or accent == TEMPLATE_DEFAULTS[spec['template']]['accent']:
        return
    palettes = {
        'cyan': {'light': '#c2e2e8', 'medium': '#76adb7', 'dark': '#3e7986'},
        'blue': {'light': '#c7d8ed', 'medium': '#799abf', 'dark': '#45658e'},
        'violet': {'light': '#dccfeb', 'medium': '#a68abd', 'dark': '#72578d'},
        'green': {'light': '#c9dfbf', 'medium': '#8db57b', 'dark': '#5e834f'},
        'amber': {'light': '#ebdab3', 'medium': '#c4a16d', 'dark': '#956f3b'},
    }
    sources = {
        'pencil': {'#90ad66': 'medium', '#bed59c': 'light', '#66884f': 'dark', '#98b879': 'medium'},
        'arc': {'#98b879': 'medium', '#c7dbac': 'light'},
        'spiral': {'#ce9672': 'medium', '#ac684c': 'dark'},
        'bands': {'#9d86b7': 'medium', '#d9c9e6': 'light'},
    }
    palette, source = palettes.get(accent), sources.get(spec['template'])
    if not palette or not source:
        return
    for shape in spec['decorations']:
        if shape.get('fill') in source:
            shape['fill'] = palette[source[shape['fill']]]


def get_layout_spec(slide=None, design=None, index=0, sections=None):
    slide, design, sections = slide or {}, design or {}, sections or []
    template_id = design.get('template') if design.get('template') in TEMPLATE_DEFAULTS else 'glass'
    is_new_family = template_id in NEW_FAMILIES
    layout_id = slide.get('layout') if slide.get('layout') in LAYOUTS else 'text'
    text_count = 3 if layout_id in ('three_cards', 'steps') else 2 if layout_id in ('two_columns', 'two_images') else 1
    image_count = 2 if layout_id == 'two_images' else 1 if layout_id in ('image', 'cover') else 0
    if is_new_family:
        nonempty = lambda value: isinstance(value, str) and bool(value.strip())
        text_count = max(text_count, 3 if nonempty(slide.get('body3')) else 2 if nonempty(slide.get('body2')) else 1)
        image_count = max(image_count if layout_id != 'cover' else 0,
                          2 if slide.get('image2') or nonempty(slide.get('image2_prompt')) else 1 if slide.get('image') or nonempty(slide.get('image_prompt')) else 0)
    large = design.get('size') == 'large'
    sizes = {'title': 48 if large else 42, 'body': 28 if large else 24, 'formula': 60 if large else 52,
             'example': 23 if large else 20, 'caption': 16, 'nav': 16}
    if is_new_family:
        sizes = {'title': 44 if large else 38, 'body': 26 if large else 22, 'formula': 46 if large else 40,
                 'example': 21 if large else 18, 'caption': 16, 'nav': 16}
    items = [({'label': item, 'firstIndex': at} if isinstance(item, str) else
              {'label': item.get('label', item.get('section', 'Taqdimot')), 'firstIndex': item.get('firstIndex', at)})
             for at, item in enumerate(sections)] if sections else [{'label': slide.get('section') or 'Taqdimot', 'firstIndex': 0}]
    section_at = next((at for at, item in enumerate(items) if item['label'] == (slide.get('section') or 'Taqdimot')), 0)
    section_color = SECTION_COLORS[section_at % len(SECTION_COLORS)]
    start = section_at // 5 * 5
    shown = items[start:start + 5]
    tx, ty, tw, th = (64, 28, 1152, 84) if template_id == 'ribbon' else (112, 34, 1104, 42) if template_id == 'split' else (64, 32, 1152, 46) if template_id == 'gallery' else (64, 30, 1152, 62)
    if is_new_family:
        tx, ty, tw, th = {'pencil': (280, 36, 896, 42), 'arc': (352, 36, 832, 42), 'spiral': (96, 36, 1088, 42), 'bands': (80, 36, 1104, 42)}[template_id]
    tabs = [_box(tx + at * tw / len(shown), ty, tw / len(shown), th, label=item['label'], firstIndex=item['firstIndex'],
                 index=item['firstIndex'], active=start + at == section_at, color=SECTION_COLORS[(start + at) % len(SECTION_COLORS)], fontSize=sizes['nav'])
            for at, item in enumerate(shown)]
    spec = {'width': 1280, 'height': 720, 'template': template_id, 'layout': layout_id, 'sectionColor': section_color, 'fontSizes': sizes,
            'navigation': _box(64, 30, 1152, 62, radius=0 if design.get('radius') == 'square' else 18) if template_id == 'glass' else None,
            'panel': _box(64, 108 if template_id == 'ribbon' else 116, 1152, 530 if template_id == 'ribbon' else 522, radius=0 if design.get('radius') == 'square' else 16 if template_id == 'ribbon' else 24),
            'title': _box(96, 146, 1088, 96, fontSize=sizes['title']), 'section': None,
            'footer': _box(96, 665, 960, 24, fontSize=14), 'page': _box(1110, 665, 74, 24, fontSize=14),
            'bodySlots': [], 'imageSlots': [], 'formula': None, 'example': None, 'tabs': tabs, 'decorations': []}
    if template_id == 'ribbon':
        spec['panel']['fill'] = 'sectionColor'
    content = _box(96, 254, 1088, 346)
    if template_id == 'split':
        spec['panel'] = _box(112, 114, 1104, 524)
        spec['title'] = _box(144, 144, 1016, 100, fontSize=sizes['title'])
        content = _box(144, 264, 1016, 336)
        spec['decorations'].append(_box(48, 114, 28, 524, kind='rect', fill='accent', opacity=1, radius=0))
    elif template_id == 'gallery':
        spec['panel'] = _box(48, 98, 1184, 540)
        spec['title'] = _box(80, 118, 1120, 92, fontSize=44 if large else 38)
        content = _box(80, 226, 1120, 382)
        spec['decorations'].append(_box(80, 211, 84, 4, kind='rect', fill='accent', opacity=1, radius=0))
    elif template_id == 'steps':
        spec['title'] = _box(116, 145, 1068, 96, fontSize=sizes['title'])
        content = _box(116, 272, 1068, 328)
        spec['decorations'].append(_box(88, 154, 8, 66, kind='rect', fill='accent', opacity=1, radius=4))
    elif is_new_family:
        content = _box(*{'pencil': (280, 246, 896, 354), 'arc': (352, 246, 824, 354), 'spiral': (96, 224, 1088, 288), 'bands': (80, 246, 824, 354)}[template_id])
        spec['title'] = _box(content['x'], 118 if template_id == 'spiral' else 132, content['w'], 94, fontSize=44 if large else 38)
        spec['panel'] = _box(content['x'] - 24, 106, content['w'] + 48, 416 if template_id == 'spiral' else 526, radius=0 if design.get('radius') == 'square' else 24)
        spec['decorations'].extend(_family_decorations(template_id))
    def add_body(field, rect, **extra):
        spec['bodySlots'].append({**rect, 'field': field, 'fontSize': sizes['body'], **extra})
    def add_image(field, rect):
        caption_field = 'image_caption' if field == 'image' else 'image2_caption'
        has_caption = bool(slide.get(field)) and bool(slide.get(caption_field, '').strip())
        caption = _box(rect['x'], rect['y'] + rect['h'] - 30, rect['w'], 30, fontSize=sizes['caption']) if has_caption else None
        spec['imageSlots'].append({**rect, 'h': rect['h'] - (38 if has_caption else 0), 'field': field,
                                  'promptField': 'image_prompt' if field == 'image' else 'image2_prompt', 'captionField': caption_field, 'caption': caption})
    if template_id == 'glass' and layout_id in ('text', 'formula', 'image'):
        is_image, is_formula = layout_id == 'image', layout_id == 'formula'
        bx, bw = (628, 556) if is_image else (96, 1088)
        height = (132 if slide.get('formula') else 252) if is_image else 92 if is_formula else 154 if slide.get('formula') else 250 if slide.get('example') else 346
        add_body('body', _box(bx, 254, bw, height))
        if is_image:
            add_image('image', _box(96, 254, 496, 346))
        if slide.get('formula'):
            spec['formula'] = _box(640 if is_image else 120, 400 if is_image else 356 if is_formula else 420,
                                   532 if is_image else 1040, 104 if is_image else 140 if is_formula else 92, fontSize=sizes['formula'])
        if slide.get('example'):
            spec['example'] = _box(bx, 550 if is_image else 542 if is_formula else 548, bw, 66 if is_formula else 58 if is_image else 60,
                                   fontSize=sizes['example'], label=_box(bx, 522 if is_image else 514 if is_formula else 520, bw, 20, fontSize=14))
    else:
        has_image = image_count > 0 and (layout_id != 'cover' or bool(slide.get('image')) or bool(slide.get('image_prompt')))
        main = dict(content)
        image_rail = is_new_family and image_count > 1 and bool(slide.get('formula') or slide.get('example'))
        if image_rail:
            rail_width, gap = math.floor(content['w'] * .35 + .5), 24
            main['w'] = content['w'] - rail_width - gap
            image_height = (content['h'] - 16) / 2
            for at, field in enumerate(('image', 'image2')):
                add_image(field, _box(content['x'] + main['w'] + gap, content['y'] + at * (image_height + 16), rail_width, image_height))
        if (image_count == 1 if is_new_family else layout_id in ('image', 'cover')) and has_image:
            gap = 32
            image_width = math.floor(content['w'] * (.58 if template_id == 'gallery' else .46) + .5)
            image_right = template_id == 'ribbon' or layout_id == 'cover'
            main['w'] = content['w'] - image_width - gap
            if not image_right:
                main['x'] = content['x'] + image_width + gap
            image_rect = _box(content['x'] + main['w'] + gap if image_right else content['x'], content['y'], image_width, content['h'])
            if template_id == 'ribbon':
                spec['title']['w'] = main['w']
                image_rect = _box(image_rect['x'], 146, image_rect['w'], 454)
            add_image('image', image_rect)
        bottom = main['y'] + main['h']
        if slide.get('example'):
            spec['example'] = _box(main['x'], bottom - (44 if is_new_family else 62), main['w'], 44 if is_new_family else 62, fontSize=sizes['example'], label=_box(main['x'], bottom - (72 if is_new_family else 88), main['w'], 18 if is_new_family else 20, fontSize=14))
            bottom -= 80 if is_new_family else 104
        if slide.get('formula'):
            height = (112 if layout_id == 'formula' else 104) if is_new_family else 132 if layout_id == 'formula' else 96
            spec['formula'] = _box(main['x'] + 8, bottom - height, main['w'] - 16, height, fontSize=sizes['formula'])
            bottom -= height + (12 if is_new_family else 16)
        main['h'] = max(48, bottom - main['y'])
        if (image_count > 1 and not image_rail) if is_new_family else layout_id == 'two_images':
            gap, column = 32, (main['w'] - 32) / 2
            image_height = max(64, math.floor(main['h'] * .57 + .5))
            for at, field in enumerate(('body', 'body2')):
                x = main['x'] + at * (column + gap)
                add_image('image2' if at else 'image', _box(x, main['y'], column, image_height))
                if not is_new_family or text_count <= 2:
                    add_body(field, _box(x, main['y'] + image_height + 16, column, max(40, main['h'] - image_height - 16)), fontSize=26 if large else 22)
            if is_new_family and text_count > 2:
                text_width = (main['w'] - gap * 2) / 3
                for at, field in enumerate(('body', 'body2', 'body3')):
                    add_body(field, _box(main['x'] + at * (text_width + gap), main['y'] + image_height + 16, text_width, max(40, main['h'] - image_height - 16)), fontSize=24 if large else 20)
        elif text_count > 1:
            gap = 28 if text_count == 3 else 36
            column = (main['w'] - gap * (text_count - 1)) / text_count
            for at in range(text_count):
                x = main['x'] + at * (column + gap)
                numbered = (layout_id == 'steps' or template_id == 'steps') and (not is_new_family or main['h'] >= 130)
                inset = (10 if is_new_family and main['h'] < 130 else 20) if text_count == 3 or numbered else 0
                if text_count == 3 or numbered:
                    spec['decorations'].append(_box(x, main['y'], column, main['h'], kind='rect', fill='accent', opacity=.08, radius=0 if design.get('radius') == 'square' else 16))
                if numbered:
                    spec['decorations'].append(_box(x + 20, main['y'] + 14, 36, 36, kind='circle', fill='accent', opacity=1, radius=18, text=str(at + 1), fontSize=20))
                add_body(f'body{at + 1}' if at else 'body', _box(x + inset, main['y'] + (68 if numbered else inset), column - inset * 2, max(32, main['h'] - (84 if numbered else inset * 2))), fontSize=(26 if large else 22) if text_count == 3 else sizes['body'])
        else:
            if layout_id == 'cover' and not has_image and (not is_new_family or not (slide.get('formula') or slide.get('example'))):
                spec['title'] = _box(main['x'], 148 if is_new_family else 168, main['w'], 108 if is_new_family else 126, fontSize=60 if large else 54)
                main['y'] = 284 if is_new_family else 320
                main['h'] = max(48, bottom - main['y'])
            add_body('body', main)
    if is_new_family and layout_id in ('three_cards', 'steps') and not any(nonempty(slide.get(key)) for key in ('formula', 'example', 'image', 'image2', 'image_prompt', 'image2_prompt')):
        _apply_infographic(spec, design)
    if is_new_family:
        _apply_motif_palette(spec, design)
    return _apply_placements(spec, slide)


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


# Ko'rinish (SlidePreview.FitText) bilan bir xil: sig'masa 6% qadam bilan
# kichrayadi, eng kami 55%. Shunda ekran va .pptx bir xil o'lchamni oladi.
FIT_MIN_SCALE = 0.55
FIT_STEP = 0.94


def _fit_size(text, box, size, family, bold, line_height, label):
    """Sig'adigan eng katta o'lchamni topadi: (size, lines). Eng kichigida ham
    sig'masa — avvalgidek aniq xato (juda uzun matn uchun)."""
    current = float(size)
    smallest = size * FIT_MIN_SCALE
    while True:
        lines = _wrap(text, box[2], box[3], current, family, bold, line_height, label, strict=False)
        if lines is not None:
            return current, lines
        if current * FIT_STEP < smallest - 1e-6:
            break
        current *= FIT_STEP
    _wrap(text, box[2], box[3], max(current, smallest), family, bold, line_height, label)  # xato matni bilan ko'taradi
    return current, []


def _wrap(text, width, height, size, family, bold, line_height, label, strict=True):
    if not text:
        return []
    font = ImageFont.truetype(_font_path(family, bold), round(size * 4))
    available = (width - 6) * 4  # small cross-viewer metric allowance
    if available <= 0 or any(font.getlength(char) > available for char in text if not char.isspace()):
        if not strict:
            return None
        raise ValueError(f"{label} slaydga sig‘madi. Elementni kengaytiring yoki matn o‘lchamini kamaytiring.")
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
        if not strict:
            return None
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

    def shape(self, name, box, fill=None, alpha=1, radius=0, border=None, border_alpha=1, kind="rect", points=None):
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
        geometry = el("a:prstGeom", el("a:avLst"), prst="ellipse" if kind == "circle" else "roundRect" if radius else "rect")
        if kind == "polygon":
            if not isinstance(points, (list, tuple)) or len(points) < 3:
                raise ValueError("Bezak ko‘pburchagi noto‘g‘ri.")
            path = el("a:path", w=round(box[2] * EMU), h=round(box[3] * EMU), stroke="false", extrusionOk="false")
            for at, point in enumerate(points):
                path.append(el("a:moveTo" if at == 0 else "a:lnTo", el("a:pt", x=round(point[0] * EMU), y=round(point[1] * EMU))))
            path.append(el("a:close"))
            geometry = el("a:custGeom", el("a:avLst"), el("a:gdLst"), el("a:ahLst"), el("a:cxnLst"),
                          el("a:rect", l="0", t="0", r="r", b="b"), el("a:pathLst", path))
        elif radius and kind != "circle":
            # OOXML rounded rectangle adj is half radius as percentage of shorter side.
            geometry[0].append(el("a:gd", name="adj", fmla=f"val {round(min(.5, radius / min(box[2:])) * 100000)}"))
        sppr.extend([_transform(box), geometry, _fill(fill, alpha) if fill else el("a:noFill")])
        sppr.append(el("a:ln", _fill(border, border_alpha) if border else el("a:noFill"), w="9525" if border else "0"))
        return shape

    def text(self, tree, text, box, size, color, font, label, bold=False, align="l", line_height=1.28, name="Matn", hyperlink=None, keep_empty=False):
        if not text and not keep_empty:
            return None
        if text:
            size, lines = _fit_size(text, box, size, font, bold, line_height, label)  # avto-kichrayish
            lines = lines or [""]
        else:
            lines = [""]
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
    """Return 1–40 editable slides; reject invalid assets or measured overflow.

    Text and formulas remain native DrawingML/OMML. The same finite geometry is
    used by the browser, including both image slots and optional captions. Every
    supplied image is validated even if the selected layout does not display it.
    """
    slides = _validate(document)
    deck = _Deck()
    sections, first = [], {}
    for index, slide in enumerate(slides):
        section = slide['section'] or 'Taqdimot'
        if section not in first:
            first[section] = index
            sections.append({'label': section, 'firstIndex': index})
    for index, slide in enumerate(slides, 1):
        for src in (slide.get('image'), slide.get('image2'), slide['design'].get('image')):
            if src is not None:
                deck.picture_data(src, f'{index}-slayd rasmi')
        for item in slide.get('elements', []):
            if item['kind'] == 'image':
                deck.picture_data(item['image'], f'{index}-slayd qo‘shimcha rasmi')
    aurora = None
    for index, slide in enumerate(slides, 1):
        design = slide['design']
        tokens = _tokens(design)
        round_corners = design['radius'] == 'round'
        spec = get_layout_spec(slide, design, index - 1, sections)
        sizes = spec['fontSizes']
        def paint(value):
            return tokens['accent'] if value == 'accent' else spec['sectionColor'][1:] if value == 'sectionColor' else tokens['panel'] if value == 'panel' else value.lstrip('#')
        root, tree, rels = deck.fresh_slide()
        tree.append(deck.shape('Orqa fon', (0, 0, 1280, 720), fill=tokens['bg']))
        if design['background'] == 'aurora':
            if aurora is None:
                try:
                    data = (ASSETS / 'aurora.png').read_bytes()
                    with Image.open(BytesIO(data)) as image:
                        aurora = (data, image.size)
                except (OSError, ValueError):
                    raise ValueError('Aurora fon rasmi topilmadi. Administratorga murojaat qiling.') from None
            deck.picture(tree, rels, *aurora, (0, 0, 1280, 720), 'Aurora', cover=True)
        elif design['background'] == 'image':
            deck.picture(tree, rels, *deck.picture_data(design['image'], f'{index}-slayd foni'), (0, 0, 1280, 720), 'Orqa fon rasmi', cover=True)
        if design['overlay']:
            tree.append(deck.shape('Fon xiraligi', (0, 0, 1280, 720), fill='000000', alpha=design['overlay'] / 100))
        if design['panel'] != 'none':
            for key, name in (('navigation', 'Bo‘limlar foni'), ('panel', 'Slayd ichki foni')):
                rect = spec.get(key)
                if rect:
                    tree.append(deck.shape(name, _coords(rect), fill=paint(rect.get('fill', 'panel')),
                                           alpha=1 if design['panel'] == 'solid' else tokens['panel_alpha'],
                                           radius=rect.get('radius', 20) if round_corners else 0,
                                           border=tokens['border'], border_alpha=tokens['border_alpha']))
        for at, item in enumerate(spec['decorations']):
            tree.append(deck.shape(f'Bezak {at + 1}', _coords(item), fill=paint(item['fill']), alpha=item.get('opacity', 1),
                                   radius=item.get('radius', 0) if round_corners else 0, kind=item['kind'], points=item.get('points')))
            if item.get('text'):
                rect = _box(item['x'], item['y'] + (item['h'] - item['fontSize'] * 1.28) / 2, item['w'], item['fontSize'] * 1.28 + 1)
                number_color = '071b24' if design['accent'] in ('cyan', 'green', 'amber') else 'ffffff'
                deck.text(tree, item['text'], _coords(rect), item['fontSize'], number_color, tokens['font'],
                          f'{index}-slayd bosqich raqami', bold=True, align='ctr', name='Bosqich raqami')
        for tab in spec['tabs']:
            active, ribbon = tab['active'], spec['template'] == 'ribbon'
            tab_box = _coords(tab)
            if active:
                if not ribbon:
                    tab_box = (tab['x'] + 5, tab['y'] + 5, tab['w'] - 10, tab['h'] - 10)
                tree.append(deck.shape('Faol bo‘lim', tab_box, fill=spec['sectionColor'][1:] if ribbon else tokens['accent'],
                                       alpha=1 if ribbon else .23, radius=(16 if ribbon else 12) if round_corners else 0,
                                       border=None if ribbon else tokens['accent'], border_alpha=.55))
                if ribbon:
                    # The active section tab joins the section panel with no gap.
                    tree.append(deck.shape('Tutash bo‘lim', (tab['x'], tab['y'] + 30, tab['w'], tab['h'] - 30), fill=spec['sectionColor'][1:]))
            rid = deck.relation(rels, f"slide{tab['firstIndex'] + 1}.xml", 'slide')
            text_box = (tab['x'] + 12, tab['y'] + 9, tab['w'] - 24, tab['h'] - 16)
            deck.text(tree, tab['label'], text_box, sizes['nav'], tokens['fg'] if active else tokens['muted'], tokens['font'],
                      f'{index}-slayd bo‘lim nomi', bold=active, align='ctr', name='Bo‘lim: ' + tab['label'], hyperlink=rid)
        if spec['section']:
            deck.text(tree, slide['section'], _coords(spec['section']), spec['section']['fontSize'], tokens['accent'], tokens['font'], f'{index}-slayd bo‘limi', bold=True, name='Bo‘lim')
        deck.text(tree, slide['title'], _coords(spec['title']), spec['title']['fontSize'], tokens['fg'], tokens['font'],
                  f'{index}-slayd sarlavhasi', bold=True, line_height=1.12, name='Sarlavha')
        for at, slot in enumerate(spec['imageSlots'], 1):
            if slide.get(slot['field']):
                deck.picture(tree, rels, *deck.picture_data(slide[slot['field']], f'{index}-slayd {at}-rasmi'),
                             _coords(slot), 'Slayd rasmi' if at == 1 else 'Slayd 2-rasmi', cover=slot.get('fit') == 'cover', radius=12 if round_corners else 0)
                if slot['caption']:
                    deck.text(tree, slide[slot['captionField']], _coords(slot['caption']), sizes['caption'], tokens['muted'], tokens['font'],
                              f'{index}-slayd {at}-rasm izohi', name=f'{at}-rasm izohi')
        for at, slot in enumerate(spec['bodySlots'], 1):
            deck.text(tree, slide[slot['field']], _coords(slot), slot['fontSize'], tokens['fg'], tokens['font'],
                      f'{index}-slayd {at}-matni', name='Asosiy matn' if at == 1 else f'{at}-matn')
        if slide['formula'].strip() and spec['formula']:
            deck.formula(tree, rels, slide['formula'], _coords(spec['formula']), spec['formula']['fontSize'], tokens['fg'], f'{index}-slayd formulasi')
        if slide['example'].strip() and spec['example']:
            label_color = tokens['fg'] if spec['template'] == 'ribbon' and design['panel'] != 'none' else tokens['accent']
            deck.text(tree, 'MISOL', _coords(spec['example']['label']), 14, label_color, tokens['font'], f'{index}-slayd misol belgisi', bold=True, name='Misol belgisi')
            deck.text(tree, slide['example'], _coords(spec['example']), spec['example']['fontSize'], tokens['fg'], tokens['font'], f'{index}-slayd misoli', line_height=1.25, name='Misol')
        for item in spec.get('elements', []):
            name = 'Qo‘shimcha element: ' + item['id']
            if item['kind'] == 'text':
                deck.text(tree, item['text'], _coords(item), item['fontSize'], item['color'][1:], tokens['font'],
                          f'{index}-slayd qo‘shimcha matni', name=name, keep_empty=True)
            elif item['kind'] == 'image':
                deck.picture(tree, rels, *deck.picture_data(item['image'], f'{index}-slayd qo‘shimcha rasmi'),
                             _coords(item), name)
            else:
                tree.append(deck.shape(name, _coords(item), fill=item['fill'][1:]))
        deck.text(tree, document.get('subject') or document.get('title', ''), _coords(spec['footer']), 14, tokens['muted'], tokens['font'], 'Fan nomi', name='Fan')
        deck.text(tree, f'{index:02d} / {len(slides):02d}', _coords(spec['page']), 14, tokens['muted'], tokens['font'], 'Slayd raqami', align='r', name='Slayd raqami')
        if design['transition'] != 'none':
            effect = el('p:' + design['transition'], **({'dir': 'l'} if design['transition'] in ('push', 'wipe') else {}))
            root.append(el('p:transition', effect, spd='med', advClick='1'))
        deck.blobs[f'ppt/slides/slide{index}.xml'] = xml(root)
        deck.blobs[f'ppt/slides/_rels/slide{index}.xml.rels'] = xml(rels)
        deck.ct.append(el('ct:Override', PartName=f'/ppt/slides/slide{index}.xml', ContentType='application/vnd.openxmlformats-officedocument.presentationml.slide+xml'))
    return deck.finish(document, len(slides))


# Restricted TeX parser and dual OMML/mathtext serializer are below.  Kept in this
# module; canvas input validation lives in presentation_layout_validation.py.

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
