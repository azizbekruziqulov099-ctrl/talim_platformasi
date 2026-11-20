"""Tayyor mavzular kutubxonasi.

kutubxona/<toplam>/reestr.json  — to'plam ro'yxati (mavzular: id, kod, nom, tur, fayl, ...)
kutubxona/<toplam>/miya/         — taqdimot-miya JSON'lari (dvigatel shu bilan ishlaydi)
kutubxona/<toplam>/oqituvchi/    — o'qituvchi matni (.md)
kutubxona/<toplam>/javoblar/     — test va mustaqil ish javoblari (faqat admin)
kutubxona/<toplam>/mustaqil/     — mustaqil ta'lim topshirig'i (.md) va rejasi (.json)

Yangi paket kelganda shu tuzilishda yangi papka qo'shiladi — kod o'zgarmaydi.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache

PAPKA = os.getenv("TAQDIMOT_KUTUBXONA") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "kutubxona")
NOM = re.compile(r"^[a-z0-9_\-]{1,40}$")
KOD = re.compile(r"^[A-Za-z0-9_\-]{1,20}$")
TUR_NOMI = {"maruza": "Ma’ruza", "amaliy": "Amaliy", "mustaqil": "Mustaqil ta’lim"}


def _yol(*qism):
    p = os.path.realpath(os.path.join(PAPKA, *qism))
    if not p.startswith(os.path.realpath(PAPKA) + os.sep):
        return None
    return p


@lru_cache(maxsize=64)
def _reestr(toplam: str, mtime: float):
    with open(_yol(toplam, "reestr.json"), encoding="utf-8") as f:
        return json.load(f)


def reestr(toplam: str):
    if not NOM.match(toplam or ""):
        return None
    p = _yol(toplam, "reestr.json")
    if not p or not os.path.isfile(p):
        return None
    return _reestr(toplam, os.path.getmtime(p))


def toplamlar():
    out = []
    if not os.path.isdir(PAPKA):
        return out
    for nom in sorted(os.listdir(PAPKA)):
        r = reestr(nom)
        if r:
            out.append({"kod": nom, "nom": r.get("nom") or nom, "mavzular": len(r.get("mavzular") or [])})
    return out


def mavzular(toplam: str):
    """Ochiq ro'yxat: javob fayllari nomlari ko'rsatilmaydi, faqat bor-yo'qligi."""
    r = reestr(toplam)
    if not r:
        return None
    items = []
    for m in r.get("mavzular") or []:
        items.append({
            "id": m.get("id"), "kod": m.get("kod"), "nom": m.get("nom"), "tur": m.get("tur"),
            "tur_nomi": TUR_NOMI.get(m.get("tur"), m.get("tur")),
            "slaydlar": m.get("slaydlar"), "testlar": m.get("testlar"),
            "oqituvchi": bool(m.get("oqituvchi")), "topshiriq": bool(m.get("topshiriq")),
            "reja": bool(m.get("reja")), "javoblar": bool(m.get("javoblar")),
        })
    return {"kod": toplam, "nom": r.get("nom"), "manba": r.get("manba"), "mavzular": items}


def _mavzu(toplam: str, kod: str):
    r = reestr(toplam)
    if not r or not KOD.match(kod or ""):
        return None
    for m in r.get("mavzular") or []:
        if (m.get("kod") or "").lower() == kod.lower() or (m.get("id") or "").lower() == kod.lower():
            return m
    return None


def _oqi(toplam, papka, fayl, binar=False):
    if not fayl:
        return None
    p = _yol(toplam, papka, os.path.basename(fayl))
    if not p or not os.path.isfile(p):
        return None
    with open(p, "rb") as f:
        data = f.read()
    return data if binar else data.decode("utf-8")


def miya(toplam: str, kod: str):
    m = _mavzu(toplam, kod)
    if not m:
        return None
    txt = _oqi(toplam, "miya", m.get("fayl"))
    return json.loads(txt) if txt else None


def hujjat(toplam: str, kod: str, tur: str):
    """tur: oqituvchi | topshiriq | reja | javoblar → (nom, bytes, mime) yoki None."""
    m = _mavzu(toplam, kod)
    if not m:
        return None
    papka = {"oqituvchi": "oqituvchi", "topshiriq": "mustaqil", "reja": "mustaqil", "javoblar": "javoblar"}.get(tur)
    if not papka or not m.get(tur):
        return None
    data = _oqi(toplam, papka, m[tur], binar=True)
    if data is None:
        return None
    mime = "text/markdown; charset=utf-8" if m[tur].endswith(".md") else "application/json"
    return os.path.basename(m[tur]), data, mime
