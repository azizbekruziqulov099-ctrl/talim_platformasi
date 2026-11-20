"""Taqdimot rasmlari: kalit → fayl.

Qidirish tartibi:
1) taqdimot rasm papkasi (TAQDIMOT_RASM_PAPKA yoki modul ichidagi "rasmlar/") — o'qituvchi chizdirgan rasmlar,
   fayl nomi = kalit (masalan anor_8_bolak.png yoki anor_8_bolak.webp);
2) saytning umumiy rasm kutubxonasi (rasm_kutubxona) — id yoki so'z bo'yicha.
Rasm topilmasa taqdimot buzilmaydi: chizma yoki joy ushlagich chiqadi.
"""
from __future__ import annotations

import io
import os
import re
from functools import lru_cache

PAPKA = os.getenv("TAQDIMOT_RASM_PAPKA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "rasmlar")
KENGAYTMALAR = (".webp", ".png", ".jpg", ".jpeg")
KALIT = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,99}$")
MAX_BYTES = 3 * 1024 * 1024
# API o'rnatadi: ma'lumotlar bazasidagi yuklangan rasmlar (kalit -> (bayt, mime) / bor-yo'q)
TASHQI = None
TASHQI_BOR = None


def kalit_toza(key: str) -> str:
    k = (key or "").strip().lower().replace(" ", "_").replace("'", "").replace("‘", "").replace("’", "").replace("ʻ", "")
    k = re.sub(r"[^a-z0-9_\-]", "", k)
    return k[:100]


def _papkadan(key):
    k = kalit_toza(key)
    if not KALIT.match(k):
        return None
    for ext in KENGAYTMALAR:
        p = os.path.join(PAPKA, k + ext)
        if os.path.isfile(p):
            return p
    return None


def _kutubxonadan(key):
    try:
        from modules import rasm_kutubxona as rk
    except Exception:
        try:
            from .. import rasm_kutubxona as rk
        except Exception:
            return None
    try:
        for r in rk.katalog():
            if r.get("id") == key or os.path.splitext(r.get("fayl", ""))[0] == key:
                p = os.path.join(rk.RASM_PAPKA, r["fayl"])
                return p if os.path.isfile(p) else None
        hit = rk.rasm_top(key.replace("_", " "))
        if hit and os.path.isfile(hit["yol"]):
            return hit["yol"]
    except Exception:
        return None
    return None


@lru_cache(maxsize=4)
def _papka_reestri(mtime: float):
    import json
    try:
        with open(os.path.join(PAPKA, "reestr.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def papka_reestri():
    """rasmlar/reestr.json — paketdan kelgan rasm va chizmalar ro'yxati (kalit, tur, nom, izoh)."""
    p = os.path.join(PAPKA, "reestr.json")
    return _papka_reestri(os.path.getmtime(p)) if os.path.isfile(p) else []


def papkadan_qidir(q: str = "", limit: int = 60):
    q = kalit_toza(q)
    out = []
    for r in papka_reestri():
        k = r.get("kalit") or ""
        matn = f"{k} {(r.get('nom') or '')} {(r.get('izoh') or '')}".lower()
        if not q or q in k or q.replace("_", " ") in matn:
            out.append({"kalit": k, "tavsif": r.get("nom") or r.get("izoh") or "", "tur": r.get("tur") or "rasm"})
            if len(out) >= limit:
                break
    return out


@lru_cache(maxsize=4096)
def yol(key: str):
    if not key:
        return None
    return _papkadan(key) or _kutubxonadan(key)


def bor(key: str) -> bool:
    if not key:
        return False
    if yol(key):
        return True
    k = kalit_toza(key)
    try:
        return bool(TASHQI_BOR and TASHQI_BOR(k))
    except Exception:
        return False


@lru_cache(maxsize=256)
def _bytes_png(key: str, n: int, data: bytes):
    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        im = im.convert("RGBA")
        w, h = im.size
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        return buf.getvalue(), w, h


def namuna_json() -> str:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "namuna_ratsional.json"), encoding="utf-8") as f:
        return f.read()


@lru_cache(maxsize=512)
def _png(path: str, mtime: float):
    """PowerPoint uchun PNG (WebP'ni PowerPoint eski versiyalari ochmaydi) + o'lcham."""
    from PIL import Image
    with Image.open(path) as im:
        im.load()
        w, h = im.size
        if max(w, h) > 1600:
            k = 1600 / max(w, h)
            im = im.resize((int(w * k), int(h * k)), Image.LANCZOS)
            w, h = im.size
        buf = io.BytesIO()
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        im.save(buf, "PNG", optimize=True)
        return buf.getvalue(), w, h


def ol(key: str):
    p = yol(key)
    if not p:
        k = kalit_toza(key)
        if TASHQI and bor(k):
            try:
                got = TASHQI(k)
                if got:
                    return _bytes_png(k, len(got[0]), got[0])
            except Exception:
                return None
        return None
    try:
        if os.path.getsize(p) > MAX_BYTES * 4:
            return None
        return _png(p, os.path.getmtime(p))
    except Exception:
        return None


def web_bytes(key: str):
    """Sayt uchun asl fayl (webp/png/jpg) va mime."""
    p = yol(key)
    if not p:
        k = kalit_toza(key)
        if TASHQI and bor(k):
            try:
                got = TASHQI(k)
                if got:
                    return got
            except Exception:
                pass
        return None, None
    ext = os.path.splitext(p)[1].lower()
    mime = {".webp": "image/webp", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(ext, "application/octet-stream")
    with open(p, "rb") as f:
        return f.read(), mime
