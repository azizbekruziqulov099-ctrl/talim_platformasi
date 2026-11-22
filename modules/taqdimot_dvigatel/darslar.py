"""Qo'lda yozilgan va tekshirilgan dars mazmunlari (malumot/darslar/*.json).

AI ishlamasa ham ochiq dars shu yerdan to'liq tuziladi: o'rgatish ketma-ketligi, asosiy qoida, yechimli misollar,
har guruh topshirig'i va yechimi, mashqlar, o'yinlar xomashyosi, loyiha va ekskursiya. Ustuvorlik: qo'lda yozilgan →
AI yozgan (miya.masalliq) → miyaning o'zidan olingan.

Fayl tuzilmasi (bitta fan × sinf):
{"daraja": "maktab", "sinf": "5", "fan": "Matematika", "muallif": "...", "mavzular": [{"mavzu": "...", "masalliq": {...}}]}
"""
from __future__ import annotations

import json
import os
import re
from fractions import Fraction
from functools import lru_cache

from . import sxema

PAPKA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "malumot", "darslar")
_APO = str.maketrans({"‘": "'", "’": "'", "ʻ": "'", "ʼ": "'", "`": "'"})


def _n(s) -> str:
    return re.sub(r"[^\w']+", " ", str(s or "").translate(_APO).lower()).strip()


def _sinf_n(s) -> tuple[int, int]:
    m = re.findall(r"\d+", str(s or ""))
    if not m:
        return (0, 99)
    return (int(m[0]), int(m[-1]))


@lru_cache(maxsize=1)
def _barchasi() -> tuple:
    out = []
    if not os.path.isdir(PAPKA):
        return ()
    for nom in sorted(os.listdir(PAPKA)):
        if not nom.endswith(".json"):
            continue
        with open(os.path.join(PAPKA, nom), encoding="utf-8") as f:
            d = json.load(f)
        for t in d.get("mavzular") or []:
            out.append({"daraja": d["daraja"], "sinf": str(d["sinf"]), "fan": d["fan"], "mavzu": t["mavzu"], "fayl": nom,
                        "masalliq": sxema.masalliq_toza(t.get("masalliq"))})
    return tuple(out)


def _fan_mos(a: str, b: str, sinf: str, daraja: str) -> bool:
    if _n(a) == _n(b):
        return True
    from . import ochiq_dars
    try:
        y = ochiq_dars.yosh_kodi(daraja, sinf)
        return ochiq_dars.fan_kodi(a, y) == ochiq_dars.fan_kodi(b, y) != "umumiy"
    except ValueError:
        return False


def top(daraja: str, sinf, fan: str, mavzu: str) -> dict | None:
    """Shu sinf, fan va mavzu uchun qo'lda yozilgan dars (masalliq) yoki None."""
    daraja = "magistr" if str(daraja or "").startswith("magistr") else (daraja or "maktab")
    sn = _sinf_n(sinf)[0]
    mv = _n(mavzu)
    for x in _barchasi():
        if x["daraja"] != daraja or _n(x["mavzu"]) != mv:
            continue
        a, b = _sinf_n(x["sinf"])
        if sn and not a <= sn <= b:
            continue
        if fan and not _fan_mos(x["fan"], fan, str(sinf or x["sinf"]), daraja):
            continue
        return x
    return None


def royxat(daraja: str = "", sinf="") -> list:
    """Frontend uchun: qo'lda yozilgan darslar ro'yxati (daraja, sinf, fan, mavzu)."""
    sn = _sinf_n(sinf)[0] if sinf else 0
    out = []
    for x in _barchasi():
        if daraja and x["daraja"] != daraja:
            continue
        a, b = _sinf_n(x["sinf"])
        if sn and not a <= sn <= b:
            continue
        out.append({k: x[k] for k in ("daraja", "sinf", "fan", "mavzu")})
    return out


# ---------------------------------------------------------------- tekshiruv (to'liqlik va hisob-kitob)
TALAB = {"bayon": 3, "misollar": 2, "guruh_topshiriqlari": 4, "mashqlar": 4, "atamalar": 4, "savollar": 6, "bayonotlar": 6}
_SON = r"\d+(?:\s*/\s*\d+)?"
_IFODA = re.compile(rf"(?<![\w/.])({_SON}(?:\s*[+\-−·×:]\s*{_SON})+)\s*=\s*({_SON})(?![\w/])")


def _qiymat(s: str) -> Fraction:
    s = s.replace(" ", "")
    if "/" in s:
        a, b = s.split("/")
        return Fraction(int(a), int(b))
    return Fraction(int(s))


def _hisobla(ifoda: str) -> Fraction:
    tok = re.findall(rf"{_SON}|[+\-−·×:]", ifoda)
    # avval ko'paytirish va bo'lish, so'ng qo'shish va ayirish
    sonlar, amallar = [_qiymat(tok[0])], []
    for amal, son in zip(tok[1::2], tok[2::2]):
        v = _qiymat(son)
        if amal in "·×":
            sonlar[-1] *= v
        elif amal == ":":
            sonlar[-1] /= v
        else:
            sonlar.append(v)
            amallar.append(amal)
    natija = sonlar[0]
    for amal, v in zip(amallar, sonlar[1:]):
        natija = natija + v if amal == "+" else natija - v
    return natija


def hisob_xatolari(matn: str) -> list:
    """Matndagi «a/b + c/b = d/b», «90 : 9 = 10» kabi tengliklarni tekshiradi; noto'g'rilarini qaytaradi."""
    xato = []
    for m in _IFODA.finditer(matn or ""):
        try:
            if _hisobla(m.group(1)) != _qiymat(m.group(2)):
                xato.append(m.group(0))
        except (ZeroDivisionError, ValueError):
            continue
    return xato


def _matnlar(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _matnlar(x)
    elif isinstance(v, list):
        for x in v:
            yield from _matnlar(x)


_ATAYIN = re.compile(r"xato|noto[‘'’]g[‘'’]ri|yechgan", re.I)


def _atayin_xatosiz(m: dict) -> dict:
    """Atayin xato qilib berilgan joylar (noto'g'ri bayonotlar, «xatoni top» yechimlari, tipik xatolar) tekshiruvdan chiqariladi."""
    m = dict(m)
    m["bayonotlar"] = [b for b in m["bayonotlar"] if b["togri"]]
    m["xato_yechim"] = {k: v for k, v in m["xato_yechim"].items() if k != "xato"}
    m["qiyinchiliklar"] = [{k: v for k, v in q.items() if k != "xato"} for q in m["qiyinchiliklar"]]
    m["guruh_topshiriqlari"] = [g for g in m["guruh_topshiriqlari"] if not _ATAYIN.search(g["topshiriq"] + " " + g["nom"])]
    return m


def tekshir() -> list:
    """Barcha qo'lda yozilgan darslar: majburiy qismlar to'liqmi, yechim va javoblar bormi, hisob-kitob to'g'rimi."""
    from . import rasmlar
    xatolar = []
    for x in _barchasi():
        nom = f"{x['fayl']}: {x['mavzu']}"
        m = x["masalliq"]
        for k, n in TALAB.items():
            if len(m.get(k) or []) < n:
                xatolar.append(f"{nom}: {k} < {n}")
        if not m["asosiy_qoida"]:
            xatolar.append(f"{nom}: asosiy_qoida yo‘q")
        if any(not g["yechim"] for g in m["guruh_topshiriqlari"]):
            xatolar.append(f"{nom}: guruh topshirig‘ida yechim yo‘q")
        if not all(m["vazifalar"].get(k) for k in "ABC"):
            xatolar.append(f"{nom}: A/B/C vazifa to‘liq emas")
        for r in [b["rasm"] for b in m["bayon"]] + [b["rasm"] for b in m["ekskursiya"]["bekatlar"]]:
            if r and not rasmlar.bor(r):
                xatolar.append(f"{nom}: rasm yo‘q — {r}")
        for s in _matnlar(_atayin_xatosiz(m)):
            for h in hisob_xatolari(s):
                xatolar.append(f"{nom}: hisob xato — {h}")
    return xatolar
