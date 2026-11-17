"""Matnni o'lchash va qatorlarga bo'lish.

Kengliklar Calibri (Carlito) va Cambria (Caladea) metrikasidan olingan — ular PowerPoint'dagi shriftlar bilan
bir xil o'lchamda. Shuning uchun bu yerda hisoblangan qatorlar PowerPoint'da ham, saytdagi ko'rinishda ham bir xil
chiqadi. Server shrift fayllarini yuklamaydi: faqat kichik kengliklar jadvali (metrika.json).
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache

_YOL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrika.json")

# Sahnadagi shrift nomi → (PowerPoint shrifti, metrika kaliti)
SHRIFTLAR = {
    "sans": ("Calibri", "sans"),
    "serif": ("Cambria", "serif"),
    "math": ("Cambria Math", "serif"),
}


@lru_cache(maxsize=1)
def _jadval():
    with open(_YOL, encoding="utf-8") as f:
        xom = json.load(f)
    out = {}
    for k, v in xom.items():
        out[k] = ({int(c): w for c, w in v["w"].items()}, v["avg"], v["asc"], v["desc"])
    return out


def _zaxira(cp):
    if 0x2E80 <= cp <= 0x9FFF or 0xAC00 <= cp <= 0xD7AF or 0x3040 <= cp <= 0x30FF:
        return 1000
    if 0x1F000 <= cp:
        return 1000
    if 0x2100 <= cp <= 0x214F:
        return 720
    if 0x2190 <= cp <= 0x22FF:
        return 780
    return 600


def kenglik(matn: str, font: str = "sans", bold: bool = False, size: float = 16.0) -> float:
    """Matn kengligi (px)."""
    kalit = SHRIFTLAR.get(font, SHRIFTLAR["sans"])[1] + ("_b" if bold else "")
    w, _avg, _a, _d = _jadval()[kalit]
    jami = 0
    for ch in matn:
        cp = ord(ch)
        jami += w.get(cp) or _zaxira(cp)
    return jami * size / 1000.0


# ---------------------------------------------------------------- run (yugurik) belgilash
# Matn ichidagi oddiy belgilash: **qalin**, *kursiv*, ^{daraja}, _{indeks}, ==rangli== (asosiy rang).
_TOKEN = re.compile(r"(\*\*.+?\*\*|==.+?==|\^\{[^{}]*\}|_\{[^{}]*\}|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*]))")


def yugurik(matn: str, **asos) -> list[dict]:
    """Belgilangan matnni run'larga ajratadi. asos — umumiy xususiyatlar (b, i, c, f, sz)."""
    out = []
    pos = 0
    for m in _TOKEN.finditer(matn):
        if m.start() > pos:
            out.append(dict(asos, t=matn[pos:m.start()]))
        tok = m.group(0)
        if tok.startswith("**"):
            out.append(dict(asos, t=tok[2:-2], b=1))
        elif tok.startswith("=="):
            out.append(dict(asos, t=tok[2:-2], b=1, urg=1))
        elif tok.startswith("^{"):
            out.append(dict(asos, t=tok[2:-1], bl="sup"))
        elif tok.startswith("_{"):
            out.append(dict(asos, t=tok[2:-1], bl="sub"))
        else:
            out.append(dict(asos, t=tok[1:-1], i=1))
        pos = m.end()
    if pos < len(matn):
        out.append(dict(asos, t=matn[pos:]))
    return [r for r in out if r["t"]]


def run_kenglik(r: dict, scale: float = 1.0) -> float:
    sz = r.get("sz", 16) * scale
    if r.get("bl"):
        sz *= 0.68
    return kenglik(r["t"], r.get("f", "sans"), bool(r.get("b")), sz)


# ---------------------------------------------------------------- qatorlarga bo'lish
_BOSHLIQ = re.compile(r"(\s+)")


def _sozlar(runs):
    """Run'larni so'z bo'laklariga: [(run, matn, bo'shliqmi)]."""
    for r in runs:
        for qism in _BOSHLIQ.split(r["t"]):
            if qism:
                yield r, qism, qism.isspace()


def qatorlar(pp: dict, eni: float, scale: float = 1.0):
    """Bitta paragrafni qatorlarga bo'ladi. Qaytaradi: [{"w", "rs": [...], "sz"}]."""
    runs = pp.get("rs") or []
    bul = pp.get("bul")
    indent = 0.0
    if bul:
        bsz = (runs[0].get("sz", 16) if runs else 16) * scale
        indent = kenglik(bul + " ", runs[0].get("f", "sans") if runs else "sans", False, bsz) + 2
    eni_q = max(eni - indent, 10)
    lines = []
    cur, cur_w = [], 0.0

    def yop():
        nonlocal cur, cur_w
        while cur and cur[-1]["t"].isspace():
            cur_w -= run_kenglik(cur[-1], scale)
            cur.pop()
        sz = max([r.get("sz", 16) for r in cur] or [runs[0].get("sz", 16) if runs else 16])
        lines.append({"w": cur_w, "rs": cur, "sz": sz * scale})
        cur, cur_w = [], 0.0

    for r, t, bosh in _sozlar(runs):
        part = dict(r, t=t)
        w = run_kenglik(part, scale)
        if bosh:
            if cur:
                cur.append(part)
                cur_w += w
            continue
        if cur_w + w <= eni_q + 0.5 or not cur:
            if w > eni_q and not cur:
                # juda uzun so'z — harflab bo'lamiz
                buf = ""
                for ch in t:
                    nw = run_kenglik(dict(r, t=buf + ch), scale)
                    if nw > eni_q and buf:
                        cur.append(dict(r, t=buf))
                        cur_w = run_kenglik(cur[-1], scale)
                        yop()
                        buf = ch
                    else:
                        buf += ch
                if buf:
                    cur.append(dict(r, t=buf))
                    cur_w = run_kenglik(cur[-1], scale)
                continue
            cur.append(part)
            cur_w += w
        else:
            yop()
            cur.append(part)
            cur_w = w
    if cur or not lines:
        yop()
    for i, q in enumerate(lines):
        q["ind"] = indent
        q["bul"] = bul if i == 0 else None
    return lines


def joyla(pps: list[dict], eni: float, boyi: float, lh: float = 1.18, min_scale: float = 0.55):
    """Paragraflarni qutiga sig'diradi. Qaytaradi (scale, qatorlar, umumiy_balandlik, sig'dimi)."""
    scale = 1.0
    while True:
        out = []
        h = 0.0
        for pi, pp in enumerate(pps):
            qs = qatorlar(pp, eni, scale)
            for q in qs:
                q["lh"] = q["sz"] * lh
                h += q["lh"]
                q["p"] = pi
            if pi < len(pps) - 1:
                h += pp.get("sp", 0) * scale
            out.extend(qs)
        if h <= boyi + 0.5 or scale <= min_scale:
            return scale, out, h, h <= boyi + 0.5
        scale = max(min_scale, scale * 0.94)


def eng_uzun(pps: list[dict], scale: float = 1.0) -> float:
    """Bir qatorga yozilganda eng uzun paragraf kengligi."""
    best = 0.0
    for pp in pps:
        best = max(best, sum(run_kenglik(r, scale) for r in pp.get("rs") or []))
    return best
