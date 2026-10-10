"""Framework-free validation for additive Presentation Studio canvas edits.

Coordinates are CSS pixels on a 1280 by 720 slide. A placement changes an
existing content box; image captions and the example label stay attached. The
caller may provide its existing image decoder as ``image_validator``.
"""
from __future__ import annotations

import base64
import binascii
import math
import re

WIDTH, HEIGHT = 1280, 720
PLACEMENT_FIELDS = frozenset(("title", "body", "body2", "body3", "formula", "example", "image", "image2"))
ELEMENT_FIELDS = frozenset(("id", "kind", "x", "y", "w", "h", "text", "fontSize", "color", "image", "fill"))
MAX_ELEMENTS = 12
MAX_IMAGE_BYTES = 2 * 1024 * 1024
_INVALID_TEXT = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")


def _text(value, limit, label, required=False):
    if not isinstance(value, str) or len(value) > limit or _INVALID_TEXT.search(value) or (required and not value.strip()):
        raise ValueError(f"{label}: {'1–' if required else '0–'}{limit} belgili matn kiriting.")
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _number(value, low, high, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high or not math.isfinite(value):
        raise ValueError(f"{label}: {low}–{high} oralig‘ida son kiriting.")
    return value


def _box(value, label):
    if not isinstance(value, dict) or set(value) != {"x", "y", "w", "h"}:
        raise ValueError(f"{label}: x, y, w va h maydonlari kerak.")
    result = {key: _number(value[key], 0 if key in ("x", "y") else 1, WIDTH if key in ("x", "w") else HEIGHT, f"{label} {key}")
              for key in ("x", "y", "w", "h")}
    if result["x"] + result["w"] > WIDTH or result["y"] + result["h"] > HEIGHT:
        raise ValueError(f"{label}: element 1280 × 720 slayd chegarasidan chiqmasligi kerak.")
    return result


def _color(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError(f"{label}: rang #RRGGBB ko‘rinishida bo‘lsin.")
    return value.lower()


def _image(value, label, image_validator):
    # Validate the transport even when no image library is installed. The API
    # and exporter additionally decode the image through their existing path.
    if not isinstance(value, str) or len(value) > ((MAX_IMAGE_BYTES + 2) // 3) * 4 + 24:
        raise ValueError(f"{label}: 2 MB gacha PNG yoki JPEG rasm tanlang.")
    match = re.fullmatch(r"data:image/(png|jpeg);base64,([A-Za-z0-9+/]*={0,2})", value)
    if not match:
        raise ValueError(f"{label}: faqat PNG yoki JPEG data URL rasmi qabul qilinadi.")
    try:
        data = base64.b64decode(match[2], validate=True)
    except (ValueError, binascii.Error):
        raise ValueError(f"{label}: rasm kodi noto‘g‘ri.") from None
    signature = b"\x89PNG\r\n\x1a\n" if match[1] == "png" else b"\xff\xd8\xff"
    if not data.startswith(signature) or len(data) > MAX_IMAGE_BYTES:
        raise ValueError(f"{label}: rasm turi uning mazmuniga mos emas yoki hajmi 2 MB dan oshgan.")
    return image_validator(value) if image_validator else value


def validate_slide_geometry(slide, image_validator=None):
    """Return normalized placements/elements, raising Uzbek ``ValueError``.

    This is deliberately independent of layouts: inactive placements survive a
    layout change. Omission remains omission in callers that preserve schema-1
    and old schema-2 documents. Stacking and intentional overlaps are allowed.
    """
    if not isinstance(slide, dict):
        raise ValueError("Slayd ma’lumoti noto‘g‘ri.")
    raw = slide.get("placements", {})
    if not isinstance(raw, dict) or set(raw) - PLACEMENT_FIELDS:
        raise ValueError("Element joylashuvi maydonlari noto‘g‘ri.")
    placements = {}
    for key, value in raw.items():
        box = _box(value, f"{key} joylashuvi")
        if key == "example" and slide.get("example") and box["y"] < 28:
            raise ValueError("Misol belgisi uchun misol tepasida kamida 28 piksel joy qoldiring.")
        caption_field = "image_caption" if key == "image" else "image2_caption"
        if key in ("image", "image2") and slide.get(key) and isinstance(slide.get(caption_field), str) and slide[caption_field].strip():
            if box["y"] + box["h"] + 38 > HEIGHT:
                raise ValueError("Rasm izohi uchun rasm ostida kamida 38 piksel joy qoldiring.")
        placements[key] = box
    raw_elements = slide.get("elements", [])
    if not isinstance(raw_elements, list) or len(raw_elements) > MAX_ELEMENTS:
        raise ValueError("Slaydga ko‘pi bilan 12 ta qo‘shimcha element qo‘shish mumkin.")
    elements, ids = [], set()
    for index, raw in enumerate(raw_elements, 1):
        label = f"{index}-qo‘shimcha element"
        if not isinstance(raw, dict) or set(raw) - ELEMENT_FIELDS:
            raise ValueError(f"{label}: maydonlar noto‘g‘ri.")
        identity = _text(raw.get("id"), 100, f"{label} identifikatori", required=True)
        if identity in ids:
            raise ValueError("Qo‘shimcha element identifikatorlari takrorlanmasligi kerak.")
        ids.add(identity)
        kind = raw.get("kind")
        if kind not in ("text", "image", "rect"):
            raise ValueError(f"{label}: text, image yoki rect turini tanlang.")
        rect = _box({key: raw.get(key) for key in ("x", "y", "w", "h")}, label)
        result = {"id": identity, "kind": kind, **rect}
        if kind == "text":
            result.update(text=_text(raw.get("text", ""), 600, f"{label} matni"),
                          fontSize=_number(raw.get("fontSize", 28), 14, 72, f"{label} shrift o‘lchami"),
                          color=_color(raw.get("color", "#17394b"), f"{label} matn rangi"))
        elif kind == "image":
            result["image"] = _image(raw.get("image"), label, image_validator)
        else:
            result["fill"] = _color(raw.get("fill", "#dbe9e4"), f"{label} to‘ldirish rangi")
        elements.append(result)
    return {"placements": placements, "elements": elements}
