"""Kod bilan chiziladigan chizmalar (GPT rasmi kerak emas, cheksiz variant).

Har bir chizma PowerPoint'ning o'z shakllaridan iborat: tahrirlanadi va bo'lakma-bo'lak chiqadi (avval o'q, keyin
belgilar, keyin nuqtalar, keyin sakrashlar...). Miya ichida chizma shunday yoziladi:
    {"tur": "son_oqi", "dan": -6, "gacha": 6, "nuqtalar": [{"x": -3, "nom": "A"}], "sakrashlar": [{"dan": -3, "ga": 2}]}
CHIZMALAR ro'yxatida har bir turning maydonlari va namunasi bor.
"""
from __future__ import annotations

import ast
import math
import re

from . import formula
from .olchov import kenglik

# ------------------------------------------------------------------ yordamchilar


class _A:
    """Chizma ichidagi animatsiya ketma-ketligi: bitta bosishda o'zi chizilib boradi."""

    def __init__(self, u, qadam, kechikish=0, bosqichli=False):
        self.u, self.s, self.t, self.boq = u, qadam, kechikish, bosqichli
        self.st = u.anim.get("stagger", 140)

    def __call__(self, rol="diagram", qadam=None, d=None, ms=None, keyin=True, dl=None):
        if self.s is None:
            return None
        e, dd, mss = self.u.anim.get(rol, self.u.anim["diagram"])
        a = {"s": self.s if qadam is None else qadam, "e": e, "ms": ms or mss, "dl": self.t if dl is None else dl}
        if d or dd:
            a["d"] = d or dd
        if keyin and dl is None:
            self.t += self.st
        return a

    def bosqich(self):
        """bosqichli rejimda keyingi bosishga o'tadi."""
        if self.boq and self.s is not None:
            self.s += 1
            self.t = 0


def lbl(s, cx, cy, t, size=16, color="#222", bold=False, a=None, font="sans", w=None, align="c"):
    t = str(t)
    if "$" in t or "\\" in t:
        tex = t.strip("$")
        fw, fa, fd = formula.olcha(tex, size)
        return formula.chiz(s, tex, cx - fw / 2 - 4, cy - (fa + fd) / 2 - 2, fw + 8, fa + fd + 4, size=size, color=color, a=a, min_scale=1.0)
    tw = w or kenglik(t, font, bold, size) + 6
    x = cx - tw / 2 if align == "c" else cx if align == "l" else cx - tw
    return s.matn(x, cy - size * 0.66, tw, size * 1.32, t, size=size, color=color, bold=bold, align=align, va="m", font=font, a=a, min_scale=0.6)


def _num(v, default=0.0):
    try:
        if isinstance(v, str):
            v = v.replace("−", "-").replace(",", ".")
            if "/" in v:
                p, q = v.split("/", 1)
                return float(p) / float(q)
        return float(v)
    except Exception:
        return default


def _fmt(v):
    v = float(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v))).replace("-", "−")
    return f"{v:g}".replace("-", "−").replace(".", ",")


def _arc(cx, cy, r, a0, a1, n=48):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _rang(u, i):
    return u.acc[i % 4]


def _bosh(u, i=0):
    """Bo'yalmagan bo'lak rangi: yorug'da och tus, qorong'ida shaffof oq."""
    return (u.tint(i, 0.9), 1.0) if not u.qorongi else ("#FFFFFF", 0.12)


# ------------------------------------------------------------------ chizmalar
def son_oqi(s, sp, x, y, w, h, u, A):
    lo, hi = _num(sp.get("dan", -5)), _num(sp.get("gacha", 5))
    if hi <= lo:
        hi = lo + 10
    step = _num(sp.get("qadam", 1), 1) or 1
    n = int(round((hi - lo) / step))
    if n > 24:
        step = step * math.ceil(n / 20)
        n = int(round((hi - lo) / step))
    cy = y + h * (0.62 if sp.get("sakrashlar") else 0.5)
    x0, x1 = x + 24, x + w - 24
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    ink = u.ink
    s.line(x0 - 16, cy, x1 + 18, cy, color=ink, lw=2.2, arr="end", a=A("diagram", d="l"))
    tick = A("item", keyin=False)
    for i in range(n + 1):
        v = lo + i * step
        s.line(X(v), cy - 7, X(v), cy + 7, color=ink, lw=1.6, a=tick)
        lbl(s, X(v), cy + 22, _fmt(v), size=15, color=u.muted, a=tick)
    A.t += A.st
    for k in sp.get("kesmalar") or sp.get("kesma") or []:
        a0, a1 = _num(k.get("dan")), _num(k.get("ga"))
        c = _rang(u, k.get("rang", 1))
        s.rect(min(X(a0), X(a1)), cy - 5, abs(X(a1) - X(a0)), 10, fill=c, op=0.55, r=5, a=A("diagram", d="l"))
        if k.get("nom"):
            lbl(s, (X(a0) + X(a1)) / 2, cy - 22, k["nom"], size=15, color=c, bold=True, a=A("accent"))
    A.bosqich()
    for i, j in enumerate(sp.get("sakrashlar") or []):
        a0, a1 = _num(j.get("dan")), _num(j.get("ga"))
        c = _rang(u, j.get("rang", 2 if i % 2 == 0 else 1))
        r = abs(X(a1) - X(a0)) / 2
        hh = min(h * 0.42, max(26, r * 0.7))
        mx = (X(a0) + X(a1)) / 2
        pts = [(mx + r * math.cos(math.radians(t)) * (1 if a1 > a0 else -1), cy - 8 - hh * math.sin(math.radians(t))) for t in range(180, -1, -10)]
        if a1 < a0:
            pts = [(mx - (px - mx), py) for px, py in pts]
        s.path(pts, line=c, lw=2.4, closed=False, a=A("diagram", d="l" if a1 > a0 else "r"))
        ex, ey = pts[-1]
        dirx = 1 if a1 > a0 else -1
        s.path([(ex - 7 * dirx, ey - 10), (ex, ey + 1), (ex + 6 * dirx * 0.2 + 5, ey - 8)], line=c, lw=2.4, closed=False, a=A("accent", keyin=False))
        if j.get("nom"):
            lbl(s, mx, cy - 18 - hh, j["nom"], size=16, color=c, bold=True, a=A("accent"))
        A.bosqich()
    for i, p in enumerate(sp.get("nuqtalar") or []):
        v = _num(p.get("x"))
        c = _rang(u, p.get("rang", 0))
        s.doira(X(v), cy, 8, fill=c, line="#FFFFFF" if not u.qorongi else None, lw=2, a=A("accent"))
        if p.get("nom"):
            lbl(s, X(v), cy - 24 if not sp.get("sakrashlar") else cy + 46, p["nom"], size=16, color=c, bold=True, a=A("accent", keyin=False))
        A.bosqich()


def ulush(s, sp, x, y, w, h, u, A):
    n = max(1, min(int(_num(sp.get("bolak", 4), 4)), 24))
    k = max(0, min(int(_num(sp.get("boyalgan", 1), 1)), n))
    shakl = sp.get("shakl", "doira")
    c = _rang(u, sp.get("rang", 0))
    bo = "#FFFFFF" if not u.qorongi else u.bg[0]
    yorliq = sp.get("nom") or (f"$\\frac{{{k}}}{{{n}}}$" if sp.get("kasr", True) else "")
    lh = 46 if yorliq else 0
    if shakl == "tasma":
        bw, bh = w - 20, min(64, h - lh - 10)
        bx, by = x + 10, y + (h - lh - bh) / 2
        for i in range(n):
            bf, bop = (c, 1.0) if i < k else _bosh(u)
            s.rect(bx + i * bw / n, by, bw / n, bh, fill=bf, op=bop, line=bo if not u.qorongi else u.muted, lw=2,
                   a=A("item" if i else "diagram", d="l"))
        if yorliq:
            lbl(s, x + w / 2, by + bh + 32, yorliq, size=30, color=c, bold=True, a=A("accent"))
        return
    if shakl == "kvadrat":
        side = min(w, h - lh) - 10
        cols = int(math.ceil(math.sqrt(n)))
        rows = int(math.ceil(n / cols))
        cw, ch = side / cols, side / rows
        bx, by = x + (w - side) / 2, y + 4
        for i in range(n):
            r_, c_ = divmod(i, cols)
            bf, bop = (c, 1.0) if i < k else _bosh(u)
            s.rect(bx + c_ * cw, by + r_ * ch, cw, ch, fill=bf, op=bop, line=bo if not u.qorongi else u.muted, lw=2, a=A("item"))
        if yorliq:
            lbl(s, x + w / 2, by + side + 28, yorliq, size=28, color=c, bold=True, a=A("accent"))
        return
    R = min(w, h - lh) / 2 - 6
    cx, cy = x + w / 2, y + R + 4
    bf, bop = _bosh(u)
    s.doira(cx, cy, R, fill=bf, op=bop, line=bo if not u.qorongi else u.muted, lw=2, a=A("diagram"))
    for i in range(n):
        a0 = -90 + 360 * i / n
        a1 = -90 + 360 * (i + 1) / n
        if i < k:
            pts = [(cx, cy)] + _arc(cx, cy, R, a0, a1, max(4, int(48 / n) + 2))
            s.path(pts, fill=c, line=bo, lw=2, a=A("big" if u.anim.get("big", ("",))[0] == "wedge" else "item"))
    for i in range(n):
        a0 = math.radians(-90 + 360 * i / n)
        s.line(cx, cy, cx + R * math.cos(a0), cy + R * math.sin(a0), color=bo, lw=2.2, a=A("item", keyin=False))
    if yorliq:
        lbl(s, cx, cy + R + 30, yorliq, size=28, color=c, bold=True, a=A("accent"))


def tasma(s, sp, x, y, w, h, u, A):
    n = max(1, min(int(_num(sp.get("bolak", 5), 5)), 20))
    k = max(0, min(int(_num(sp.get("boyalgan", 0), 0)), n))
    c = _rang(u, sp.get("rang", 1))
    bw = w - 30
    bh = min(56, h * 0.3)
    bx = x + 15
    by = y + h * 0.42
    if sp.get("jami"):
        s.line(bx, by - 26, bx + bw, by - 26, color=u.muted, lw=1.6, arr="both", a=A("diagram", d="l"))
        lbl(s, bx + bw / 2, by - 42, sp["jami"], size=17, color=u.ink, bold=True, a=A("accent"))
    for i in range(n):
        f, fop = (c, 1.0) if i < k else _bosh(u, 1)
        s.rect(bx + i * bw / n, by, bw / n, bh, fill=f, op=fop, line="#FFFFFF" if not u.qorongi else u.muted, lw=2, a=A("item", d="l"))
        if sp.get("bolak_nomi"):
            lbl(s, bx + (i + 0.5) * bw / n, by + bh / 2, sp["bolak_nomi"], size=15, color=u.matn_ustida(f) if fop == 1.0 else u.ink, bold=True, a=A("item", keyin=False))
    if k and sp.get("boyalgan_nomi"):
        s.line(bx, by + bh + 16, bx + k * bw / n, by + bh + 16, color=c, lw=1.6, arr="both", a=A("diagram", d="l"))
        lbl(s, bx + k * bw / n / 2, by + bh + 34, sp["boyalgan_nomi"], size=16, color=c, bold=True, a=A("accent"))


def daraxt(s, sp, x, y, w, h, u, A):
    levels = [list(map(str, l))[:6] for l in (sp.get("darajalar") or [])][:3]
    if not levels:
        return
    root = str(sp.get("ildiz", "•"))
    nodes = [[(root, [])]]
    for li, lev in enumerate(levels):
        cur = []
        for pi, (_lab, _p) in enumerate(nodes[-1]):
            for item in lev:
                cur.append((item, pi))
        nodes.append(cur)
    leaves = len(nodes[-1])
    show_res = sp.get("natija", True) and len(levels) >= 2 and leaves <= 12
    cols = len(nodes) + (1 if show_res else 0)
    colw = w / cols
    pos = []
    for li, lev in enumerate(nodes):
        cnt = len(lev)
        gap = h / max(cnt, 1)
        pos.append([(x + colw * (li + 0.5), y + gap * (i + 0.5)) for i in range(cnt)])
    for li in range(1, len(nodes)):
        for i, (lab, pi) in enumerate(nodes[li]):
            px, py = pos[li - 1][pi]
            cx, cy = pos[li][i]
            s.line(px + 18, py, cx - 26, cy, color=u.muted, lw=1.6, a=A("item", d="l", keyin=False, dl=A.t + i * 40))
        A.t += A.st * 2
        for i, (lab, pi) in enumerate(nodes[li]):
            cx, cy = pos[li][i]
            c = _rang(u, li - 1 + (1 if li > 1 else 0))
            bw_, bh_ = min(colw * 0.55, 70), min(h / len(nodes[li]) * 0.72, 34)
            s.rect(cx - bw_ / 2, cy - bh_ / 2, bw_, bh_, fill=c, r=6, a=A("accent", keyin=False, dl=A.t + i * 30))
            lbl(s, cx, cy, lab, size=min(16, bh_ * 0.55), color=u.matn_ustida(c), bold=True, a=A("accent", keyin=False, dl=A.t + i * 30))
        A.t += A.st * 2
        A.bosqich()
    rx, ry = pos[0][0]
    s.doira(rx, ry, 14, fill=u.acc[2], a=A("accent"))
    if root != "•":
        lbl(s, rx, ry - 28, root, size=15, color=u.ink, bold=True, a=A("accent", keyin=False))
    if show_res:
        for i, (lab, pi) in enumerate(nodes[-1]):
            path = [lab]
            li = len(nodes) - 1
            p = pi
            while li > 1:
                li -= 1
                path.append(nodes[li][p][0])
                p = nodes[li][p][1]
            cx, cy = pos[-1][i]
            lbl(s, x + colw * (cols - 0.5), cy, "(" + "; ".join(reversed(path)) + ")", size=14, color=u.muted, a=A("item", keyin=False, dl=A.t + i * 30))


def venn(s, sp, x, y, w, h, u, A):
    ts = sp.get("toplamlar") or [{"nom": "A"}, {"nom": "B"}]
    ts = ts[:3]
    cx, cy = x + w / 2, y + h / 2 + 6
    R = min(h * 0.42, w * 0.26)
    if len(ts) == 1:
        centers = [(cx, cy)]
    elif len(ts) == 2:
        centers = [(cx - R * 0.55, cy), (cx + R * 0.55, cy)]
    else:
        R *= 0.86
        centers = [(cx - R * 0.55, cy - R * 0.3), (cx + R * 0.55, cy - R * 0.3), (cx, cy + R * 0.55)]
    if sp.get("universal"):
        s.rect(x + 6, y + 6, w - 12, h - 12, line=u.muted, lw=1.5, r=10, a=A("diagram"))
        lbl(s, x + 26, y + 24, sp["universal"], size=16, color=u.muted, bold=True, a=A("item", keyin=False))
    for i, (t, (ccx, ccy)) in enumerate(zip(ts, centers)):
        c = _rang(u, i)
        s.doira(ccx, ccy, R, fill=c, op=0.22, line=c, lw=2.4, a=A("diagram"))
        dx = -1 if ccx < cx - 1 else 1 if ccx > cx + 1 else 0
        lbl(s, ccx + dx * R * 0.72, ccy - R * 0.92 if len(ts) < 3 or i < 2 else ccy + R * 0.95, t.get("nom", ""), size=20, color=c, bold=True, a=A("accent"))
        els = [str(v) for v in (t.get("elementlar") or [])][:6]
        for j, v in enumerate(els):
            ex = ccx + dx * R * 0.42 if len(ts) > 1 else ccx + (j % 2 - 0.5) * R * 0.6
            ey = ccy - R * 0.35 + j * (R * 0.7 / max(1, len(els) - 1) if len(els) > 1 else 0)
            lbl(s, ex, ey, v, size=17, color=u.ink, a=A("item"))
    um = [str(v) for v in (sp.get("umumiy") or [])][:4]
    for j, v in enumerate(um):
        lbl(s, cx, cy - (len(um) - 1) * 12 + j * 24 - (R * 0.15 if len(ts) == 3 else 0), v, size=17, color=u.ink, bold=True, a=A("accent"))


def ichma_ich(s, sp, x, y, w, h, u, A):
    q = (sp.get("qatlamlar") or [])[:4]
    n = len(q)
    if not n:
        return
    band = min(w * 0.2, (w * 0.62) / max(n - 1, 1)) if n > 1 else 0
    rects = []
    for k in range(n):
        rx = x + k * 14
        ry = y + k * 36
        rw = w - k * 14 - k * band
        rh = h - k * 36 - k * 14
        rects.append((rx, ry, rw, rh))
    for k, layer in enumerate(q[::-1]):
        k = n - 1 - k
    for k in range(n - 1, -1, -1):
        pass
    for k in range(n):
        layer = q[n - 1 - k] if False else q[k]
    # tashqaridan ichkariga: avval ichki (eng kichik to'plam) chiqadi
    for k in range(n - 1, -1, -1):
        layer = q[k]
        rx, ry, rw, rh = rects[n - 1 - k]
        c = _rang(u, k)
        s.rect(rx, ry, rw, rh, fill=c, op=0.10 if not u.qorongi else 0.18, line=c, lw=2, r=16, a=A("diagram"))
        lbl(s, rx + 14, ry + 18, layer.get("nom", ""), size=16, color=c, bold=True, a=A("accent", keyin=False), align="l")
        ex = [str(v) for v in (layer.get("misol") or [])][:4]
        if n - 1 - k == n - 1:  # eng ichki
            for j, v in enumerate(ex):
                lbl(s, rx + rw * (0.28 + 0.44 * (j % 2)), ry + 40 + (rh - 50) * (0.3 + 0.4 * (j // 2)), v, size=18, color=u.ink, a=A("item"))
        else:
            inner = rects[n - 1 - k + 1]
            bx = inner[0] + inner[2]
            bw = rx + rw - bx
            for j, v in enumerate(ex):
                lbl(s, bx + bw / 2, inner[1] + 20 + j * min(34, (inner[3] - 20) / max(len(ex), 1)), v, size=18, color=u.ink, a=A("item"))
        A.bosqich()


def tarozi(s, sp, x, y, w, h, u, A):
    chap = sp.get("chap") or ["x"]
    ong = sp.get("ong") or ["12"]
    teng = sp.get("muvozanat", True)
    tilt = 0 if teng else (-7 if sp.get("ogir") == "chap" else 7)
    cx = x + w / 2
    label_h = 34 if sp.get("tenglama") else 0
    top = y + 14
    base_y = y + h - label_h - 8
    beam_w = w * 0.9
    s.path([(cx, top + 6), (cx + 26, base_y), (cx - 26, base_y)], fill=u.muted, op=0.6, a=A("diagram"))
    s.rect(cx - 60, base_y - 4, 120, 10, fill=u.muted, r=5, a=A("diagram", keyin=False))
    ang = math.radians(tilt)
    lx, ly = cx - beam_w / 2 * math.cos(ang), top - beam_w / 2 * math.sin(ang)
    rx_, ry_ = cx + beam_w / 2 * math.cos(ang), top + beam_w / 2 * math.sin(ang)
    s.line(lx, ly, rx_, ry_, color=u.ink, lw=6, a=A("diagram", d="l"))
    s.doira(cx, top, 9, fill=u.acc[0], a=A("accent", keyin=False))
    pw = (w - 90) / 2
    ph = min((base_y - top) * 0.62, pw * 0.75)
    pf, pop = ("#FFFFFF", 1.0) if not u.qorongi else ("#FFFFFF", 0.1)
    for side, items, (px, py) in (("chap", chap, (lx, ly)), ("ong", ong, (rx_, ry_))):
        bx = x + 6 if side == "chap" else x + w - 6 - pw
        by = py + 22
        hx = bx + pw / 2
        s.line(hx - pw * 0.3, by, px + (12 if side == "chap" else -12), py + 3, color=u.muted, lw=1.4, a=A("item", keyin=False))
        s.line(hx + pw * 0.3, by, px + (12 if side == "chap" else -12), py + 3, color=u.muted, lw=1.4, a=A("item", keyin=False))
        s.rect(bx, by, pw, ph, fill=pf, op=pop, line=u.muted, lw=2, r=12, sh=0 if u.qorongi else 1, a=A("card"))
        n = len(items)
        slot = pw / max(n, 1)
        for i, it in enumerate(items):
            it = str(it)
            ix = bx + slot * (i + 0.5)
            iy = by + ph / 2
            if it.lower() in ("x", "?", "y", "a", "n") or (it[:1].isalpha() and len(it) <= 2):
                bs = min(slot * 0.66, ph * 0.6)
                s.rect(ix - bs / 2, iy - bs / 2, bs, bs, fill=u.acc[2], r=6, a=A("accent"))
                lbl(s, ix, iy, it, size=bs * 0.45, color=u.matn_ustida(u.acc[2]), bold=True, a=A("accent", keyin=False), font="serif")
            elif re.fullmatch(r"[+]?\d{1,2}", it) and sp.get("nuqtali", True) and int(it.lstrip("+")) <= 12 and it.startswith("+"):
                cnt = int(it.lstrip("+"))
                cols = 4 if cnt > 4 else cnt
                rows = math.ceil(cnt / cols)
                dot = min(slot / (cols + 1), ph / (rows + 1.8)) * 0.85
                for d in range(cnt):
                    r_, c_ = divmod(d, cols)
                    s.doira(ix - (cols - 1) * dot * 0.62 + c_ * dot * 1.24, iy - (rows - 1) * dot * 0.62 + r_ * dot * 1.24, dot / 2, fill=u.acc[3], a=A("item", keyin=False, dl=A.t + d * 40))
                A.t += A.st
                lbl(s, ix, by + ph + 16, it, size=16, color=u.ink, bold=True, a=A("item"))
            else:
                lbl(s, ix, iy, it, size=min(40, ph * 0.45), color=u.ink, bold=True, a=A("accent"))
    if sp.get("tenglama"):
        lbl(s, cx, y + h - label_h / 2, sp["tenglama"], size=22, color=u.ink, bold=True, a=A("accent"))


def termometr(s, sp, x, y, w, h, u, A):
    lo, hi = _num(sp.get("dan", -10)), _num(sp.get("gacha", 10))
    v = _num(sp.get("qiymat", 0))
    cx = x + w * 0.38
    top, bot = y + 12, y + h - 52
    Y = lambda t: bot - (t - lo) / (hi - lo) * (bot - top)
    tf, top_ = ("#FFFFFF", 1.0) if not u.qorongi else ("#FFFFFF", 0.12)
    s.rect(cx - 14, top - 6, 28, bot - top + 20, fill=tf, op=top_, line=u.muted, lw=2, r=14, a=A("diagram"))
    s.doira(cx, bot + 26, 26, fill=u.bad, line=u.muted, lw=2, a=A("diagram", keyin=False))
    s.rect(cx - 7, Y(v), 14, bot + 10 - Y(v), fill=u.bad, r=4, a=A("diagram", d="u"))
    step = max(1, int((hi - lo) / 10))
    t = lo
    while t <= hi + 1e-9:
        s.line(cx + 16, Y(t), cx + 26, Y(t), color=u.muted, lw=1.4, a=A("item", keyin=False))
        if int(t) % (step * 2) == 0:
            lbl(s, cx + 46, Y(t), _fmt(t), size=13, color=u.muted, a=A("item", keyin=False))
        t += step
    for m in sp.get("belgilar") or []:
        mv = _num(m.get("t") if isinstance(m, dict) else m)
        nom = m.get("nom") if isinstance(m, dict) else f"{_fmt(mv)} °C"
        s.line(cx - 18, Y(mv), cx - 60, Y(mv), color=u.acc[0], lw=1.6, dash=1, a=A("item"))
        lbl(s, cx - 66, Y(mv), nom, size=15, color=u.acc[0], bold=True, a=A("accent", keyin=False), align="r")


def grafik(s, sp, x, y, w, h, u, A):
    lo, hi = _num(sp.get("dan", -5)), _num(sp.get("gacha", 5))
    fn = str(sp.get("funksiya") or "")
    f = _safe_fn(fn) if fn else None
    ys = []
    if f:
        for i in range(201):
            xv = lo + (hi - lo) * i / 200
            try:
                yv = f(xv)
                if math.isfinite(yv):
                    ys.append(yv)
            except Exception:
                pass
    pts_in = [(_num(p[0]), _num(p[1])) for p in (sp.get("nuqtalar") or []) if isinstance(p, (list, tuple)) and len(p) >= 2]
    ys += [p[1] for p in pts_in]
    ylo = _num(sp.get("y_dan"), min(ys + [-1])) if sp.get("y_dan") is not None else min(ys + [-1])
    yhi = _num(sp.get("y_gacha"), max(ys + [1])) if sp.get("y_gacha") is not None else max(ys + [1])
    if yhi - ylo < 1e-6:
        yhi, ylo = yhi + 1, ylo - 1
    pad = (yhi - ylo) * 0.08
    ylo, yhi = ylo - pad, yhi + pad
    X = lambda v: x + 20 + (v - lo) / (hi - lo) * (w - 40)
    Y = lambda v: y + h - 20 - (v - ylo) / (yhi - ylo) * (h - 40)
    grid = A("item", keyin=False)
    for gx in range(int(math.ceil(lo)), int(math.floor(hi)) + 1):
        s.line(X(gx), Y(ylo), X(gx), Y(yhi), color=u.muted, lw=0.6, op=0.35, a=grid)
        if gx != 0:
            lbl(s, X(gx), Y(0) + 14 if ylo < 0 < yhi else Y(ylo) + 14, _fmt(gx), size=12, color=u.muted, a=grid)
    ystep = max(1, int(math.ceil((yhi - ylo) / 10)))
    for gy in range(int(math.ceil(ylo)), int(math.floor(yhi)) + 1, ystep):
        s.line(X(lo), Y(gy), X(hi), Y(gy), color=u.muted, lw=0.6, op=0.35, a=grid)
        if gy != 0:
            lbl(s, X(0) - 14 if lo < 0 < hi else X(lo) - 14, Y(gy), _fmt(gy), size=12, color=u.muted, a=grid)
    A.t += A.st
    if lo < 0 < hi:
        s.line(X(0), Y(ylo), X(0), Y(yhi), color=u.ink, lw=1.8, arr="end", a=A("diagram", d="u"))
        lbl(s, X(0) + 12, Y(yhi) + 4, "y", size=16, color=u.ink, a=A("item", keyin=False), font="math")
    if ylo < 0 < yhi:
        s.line(X(lo), Y(0), X(hi), Y(0), color=u.ink, lw=1.8, arr="end", a=A("diagram", d="l"))
        lbl(s, X(hi) - 6, Y(0) + 16, "x", size=16, color=u.ink, a=A("item", keyin=False), font="math")
    if f:
        seg = []
        segs = []
        for i in range(161):
            xv = lo + (hi - lo) * i / 160
            try:
                yv = f(xv)
            except Exception:
                yv = None
            if yv is None or not math.isfinite(yv) or yv < ylo - pad * 3 or yv > yhi + pad * 3:
                if len(seg) > 1:
                    segs.append(seg)
                seg = []
                continue
            seg.append((X(xv), Y(max(ylo, min(yhi, yv)))))
        if len(seg) > 1:
            segs.append(seg)
        for sg in segs:
            s.path(sg, line=u.acc[0], lw=3, closed=False, a=A("diagram", d="l"))
        if sp.get("nom", fn):
            lbl(s, x + w - 80, y + 24, sp.get("nom") or f"$y={fn}$", size=18, color=u.acc[0], bold=True, a=A("accent"))
    for i, (px, py) in enumerate(pts_in):
        s.doira(X(px), Y(py), 6, fill=u.acc[1], a=A("accent"))
        lbl(s, X(px) + 26, Y(py) - 14, f"({_fmt(px)}; {_fmt(py)})", size=13, color=u.acc[1], a=A("item", keyin=False))


def _safe_fn(expr):
    expr = expr.replace("^", "**").replace("−", "-").replace("·", "*").replace(",", ".")
    expr = re.sub(r"(\d)\s*([a-z(])", r"\1*\2", expr)
    expr = re.sub(r"\)\s*\(", ")*(", expr)
    tree = ast.parse(expr, mode="eval")
    ok = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load, ast.Call, ast.Add, ast.Sub, ast.Mult,
          ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Mod)
    names = {"x", "sin", "cos", "tan", "sqrt", "abs", "log", "exp", "pi", "e"}
    for node in ast.walk(tree):
        if not isinstance(node, ok):
            raise ValueError("ruxsat etilmagan ifoda")
        if isinstance(node, ast.Name) and node.id not in names:
            raise ValueError("noma'lum nom")
        if isinstance(node, ast.Pow) and False:
            pass
    code = compile(tree, "<f>", "eval")
    env = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "sqrt": math.sqrt, "abs": abs, "log": math.log, "exp": math.exp,
           "pi": math.pi, "e": math.e, "__builtins__": {}}

    def f(xv):
        env["x"] = xv
        r = eval(code, env)  # noqa: S307 — faqat tekshirilgan arifmetik ifoda
        if isinstance(r, complex) or abs(r) > 1e9:
            return float("nan")
        return float(r)
    return f


def ustun(s, sp, x, y, w, h, u, A):
    nom = [str(v) for v in (sp.get("nomlar") or [])][:10]
    val = [_num(v) for v in (sp.get("qiymatlar") or [])][:10]
    n = min(len(nom), len(val))
    if not n:
        return
    mx = max(val[:n] + [1])
    base = y + h - 30
    s.line(x + 10, base, x + w - 10, base, color=u.ink, lw=1.8, a=A("diagram", d="l"))
    bw = (w - 40) / n
    for i in range(n):
        bh = (h - 70) * val[i] / mx
        c = _rang(u, i)
        s.rect(x + 20 + i * bw + bw * 0.18, base - bh, bw * 0.64, bh, fill=c, r=6, a=A("diagram", d="u"))
        lbl(s, x + 20 + i * bw + bw / 2, base - bh - 16, _fmt(val[i]), size=15, color=u.ink, bold=True, a=A("item", keyin=False))
        lbl(s, x + 20 + i * bw + bw / 2, base + 16, nom[i], size=14, color=u.muted, a=A("item", keyin=False))


def uchburchak(s, sp, x, y, w, h, u, A):
    turi = str(sp.get("turi", "oddiy"))
    nm = (sp.get("nomlar") or ["A", "B", "C"]) + ["", "", ""]
    tom = (sp.get("tomonlar") or []) + ["", "", ""]
    m = 30
    if "to'g'ri" in turi or "togri" in turi:
        P = [(x + m, y + h - m), (x + w - m, y + h - m), (x + m, y + m)]
    elif "teng tomonli" in turi:
        side = min(w - 2 * m, (h - 2 * m) / 0.866)
        cx = x + w / 2
        P = [(cx - side / 2, y + h - m), (cx + side / 2, y + h - m), (cx, y + h - m - side * 0.866)]
    elif "teng yonli" in turi:
        P = [(x + m + w * 0.08, y + h - m), (x + w - m - w * 0.08, y + h - m), (x + w / 2, y + m)]
    else:
        P = [(x + m, y + h - m), (x + w - m, y + h - m), (x + w * 0.35, y + m)]
    c = u.acc[0]
    s.path(P, fill=c, op=0.12, line=c, lw=3, a=A("diagram", d="l"))
    cx = sum(p[0] for p in P) / 3
    cy = sum(p[1] for p in P) / 3
    for i, (px, py) in enumerate(P):
        dx, dy = px - cx, py - cy
        L = math.hypot(dx, dy) or 1
        s.doira(px, py, 5, fill=u.ink, a=A("item", keyin=False))
        if nm[i]:
            lbl(s, px + dx / L * 22, py + dy / L * 22, nm[i], size=20, color=u.ink, bold=True, a=A("accent"), font="serif")
    for i in range(3):
        if not tom[i]:
            continue
        a_, b_ = P[(i + 1) % 3], P[(i + 2) % 3]
        mx_, my_ = (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2
        dx, dy = mx_ - cx, my_ - cy
        L = math.hypot(dx, dy) or 1
        lbl(s, mx_ + dx / L * 20, my_ + dy / L * 20, tom[i], size=17, color=u.acc[1], bold=True, a=A("accent"), font="math")
    if "to'g'ri" in turi or "togri" in turi:
        q = 16
        s.path([(P[0][0] + q, P[0][1]), (P[0][0] + q, P[0][1] - q), (P[0][0], P[0][1] - q)], line=u.ink, lw=1.6, closed=False, a=A("item"))
    if sp.get("balandlik"):
        tx, ty = P[2]
        s.line(tx, ty, tx, P[0][1], color=u.acc[2], lw=2, dash=1, a=A("diagram", d="d"))
        lbl(s, tx + 14, (ty + P[0][1]) / 2, "h", size=18, color=u.acc[2], bold=True, a=A("accent"), font="math")


def tortburchak(s, sp, x, y, w, h, u, A):
    kv = sp.get("tur") == "kvadrat"
    m = 40
    if kv:
        side = min(w, h) - 2 * m
        rx, ry, rw, rh = x + (w - side) / 2, y + (h - side) / 2, side, side
    else:
        rw, rh = w - 2 * m, (h - 2 * m) * 0.75
        rx, ry = x + m, y + (h - rh) / 2
    c = u.acc[1]
    s.rect(rx, ry, rw, rh, fill=c, op=0.13, line=c, lw=3, a=A("diagram", d="l"))
    a_ = sp.get("a", "a")
    b_ = sp.get("b", "a" if kv else "b")
    lbl(s, rx + rw / 2, ry + rh + 20, a_, size=18, color=u.ink, bold=True, a=A("accent"), font="math")
    lbl(s, rx - 24, ry + rh / 2, b_, size=18, color=u.ink, bold=True, a=A("accent", keyin=False), font="math")
    if sp.get("diagonal"):
        s.line(rx, ry + rh, rx + rw, ry, color=u.acc[2], lw=2, dash=1, a=A("diagram", d="l"))
    if sp.get("ichida"):
        lbl(s, rx + rw / 2, ry + rh / 2, sp["ichida"], size=22, color=c, bold=True, a=A("accent"))


def aylana(s, sp, x, y, w, h, u, A):
    R = min(w, h) / 2 - 24
    cx, cy = x + w / 2, y + h / 2
    c = u.acc[0]
    s.doira(cx, cy, R, fill=c if sp.get("doira") else None, op=0.12, line=c, lw=3, a=A("diagram"))
    s.doira(cx, cy, 5, fill=u.ink, a=A("item"))
    lbl(s, cx - 12, cy + 16, sp.get("markaz", "O"), size=17, color=u.ink, bold=True, a=A("item", keyin=False), font="serif")
    if sp.get("radius", True):
        s.line(cx, cy, cx + R * 0.94, cy - R * 0.34, color=u.acc[1], lw=2.4, a=A("diagram", d="l"))
        lbl(s, cx + R * 0.5, cy - R * 0.28, sp.get("radius") if isinstance(sp.get("radius"), str) else "r", size=18, color=u.acc[1], bold=True, a=A("accent"), font="math")
    if sp.get("diametr"):
        s.line(cx - R, cy + R * 0.0, cx + R, cy, color=u.acc[2], lw=2, dash=1, a=A("diagram", d="l"))
        lbl(s, cx + R * 0.55, cy + 16, sp.get("diametr") if isinstance(sp.get("diametr"), str) else "d", size=18, color=u.acc[2], bold=True, a=A("accent"), font="math")


def katak(s, sp, x, y, w, h, u, A):
    rows = max(1, min(int(_num(sp.get("qator", 3), 3)), 12))
    cols = max(1, min(int(_num(sp.get("ustun", 4), 4)), 16))
    k = int(_num(sp.get("boyalgan", rows * cols), rows * cols))
    cell = min((w - 20) / cols, (h - 40) / rows)
    bx = x + (w - cell * cols) / 2
    by = y + (h - 30 - cell * rows) / 2
    shakl = sp.get("shakl", "katak")
    for i in range(rows * cols):
        r_, c_ = divmod(i, cols)
        fill, fop = (_rang(u, sp.get("rang", 0)), 1.0) if i < k else _bosh(u)
        a = A("item", keyin=False, dl=A.t + (r_ * 90 + c_ * 25))
        if shakl == "nuqta":
            s.doira(bx + (c_ + 0.5) * cell, by + (r_ + 0.5) * cell, cell * 0.32, fill=fill, op=fop, a=a)
        else:
            s.rect(bx + c_ * cell, by + r_ * cell, cell, cell, fill=fill, op=fop, line="#FFFFFF" if not u.qorongi else u.muted, lw=1.5, a=a)
    A.t += rows * 90 + A.st
    if sp.get("nom"):
        lbl(s, x + w / 2, by + rows * cell + 22, sp["nom"], size=20, color=u.ink, bold=True, a=A("accent"))


def nuqtalar(s, sp, x, y, w, h, u, A):
    gs = [max(0, min(int(_num(g)), 20)) for g in (sp.get("guruhlar") or [3, 2])][:6]
    n = len(gs)
    gw = w / max(n, 1)
    for gi, cnt in enumerate(gs):
        c = _rang(u, gi)
        gx = x + gi * gw
        gf, gop = (u.tint(gi, 0.93), 1.0) if not u.qorongi else ("#FFFFFF", 0.07)
        s.rect(gx + 8, y + 8, gw - 16, h - 50, fill=gf, op=gop, line=c, lw=1.5, r=14, a=A("card"))
        cols = min(4, max(1, cnt))
        rows = math.ceil(cnt / cols) if cnt else 1
        d = min((gw - 40) / cols, (h - 80) / rows) * 0.7
        for i in range(cnt):
            r_, c_ = divmod(i, cols)
            s.doira(gx + gw / 2 - (cols - 1) * d * 0.7 + c_ * d * 1.4, y + 8 + (h - 50) / 2 - (rows - 1) * d * 0.7 + r_ * d * 1.4, d / 2,
                    fill=c, a=A("item", keyin=False, dl=A.t + i * 50))
        A.t += cnt * 50
        lbl(s, gx + gw / 2, y + h - 22, str(cnt), size=22, color=c, bold=True, a=A("accent"))
        if gi < n - 1 and sp.get("amal", "+"):
            lbl(s, gx + gw, y + (h - 50) / 2 + 8, sp.get("amal", "+"), size=26, color=u.ink, bold=True, a=A("accent", keyin=False))


def soat(s, sp, x, y, w, h, u, A):
    R = min(w, h) / 2 - 10
    cx, cy = x + w / 2, y + h / 2
    s.doira(cx, cy, R, fill="#FFFFFF", op=1.0 if not u.qorongi else 0.1, line=u.ink, lw=4, sh=0 if u.qorongi else 1, a=A("diagram"))
    for i in range(60):
        a = math.radians(i * 6 - 90)
        r1 = R * (0.86 if i % 5 == 0 else 0.92)
        s.line(cx + r1 * math.cos(a), cy + r1 * math.sin(a), cx + R * 0.97 * math.cos(a), cy + R * 0.97 * math.sin(a), color=u.ink, lw=2.4 if i % 5 == 0 else 1, a=A("item", keyin=False))
    for i in range(1, 13):
        a = math.radians(i * 30 - 90)
        lbl(s, cx + R * 0.72 * math.cos(a), cy + R * 0.72 * math.sin(a), str(i), size=R * 0.16, color=u.ink, bold=True, a=A("item", keyin=False))
    A.t += A.st
    hh = _num(sp.get("soat", 3)) % 12
    mm = _num(sp.get("daqiqa", 0)) % 60
    ah = math.radians((hh + mm / 60) * 30 - 90)
    am = math.radians(mm * 6 - 90)
    s.line(cx, cy, cx + R * 0.5 * math.cos(ah), cy + R * 0.5 * math.sin(ah), color=u.acc[0], lw=7, a=A("diagram"))
    s.line(cx, cy, cx + R * 0.78 * math.cos(am), cy + R * 0.78 * math.sin(am), color=u.acc[1], lw=4, a=A("diagram"))
    s.doira(cx, cy, 8, fill=u.ink, a=A("accent", keyin=False))


def burchak(s, sp, x, y, w, h, u, A):
    g = _num(sp.get("gradus", 60), 60)
    ox, oy = x + w * 0.2, y + h * 0.8
    L = min(w * 0.7, h * 0.9)
    s.line(ox, oy, ox + L, oy, color=u.ink, lw=3, arr="end", a=A("diagram", d="l"))
    a = math.radians(-g)
    s.line(ox, oy, ox + L * math.cos(a), oy + L * math.sin(a), color=u.ink, lw=3, arr="end", a=A("diagram", d="l"))
    pts = _arc(ox, oy, L * 0.25, 0, -g, 32)
    s.path([(ox, oy)] + pts, fill=u.acc[0], op=0.25, line=u.acc[0], lw=2, a=A("accent"))
    mid = math.radians(-g / 2)
    lbl(s, ox + L * 0.36 * math.cos(mid), oy + L * 0.36 * math.sin(mid), f"{_fmt(g)}°", size=20, color=u.acc[0], bold=True, a=A("accent"))


def kasrlar(s, sp, x, y, w, h, u, A):
    ks = [str(k) for k in (sp.get("kasrlar") or ["1/2", "2/3"])][:5]
    n = len(ks)
    rowh = min(64, (h - 10) / n)
    bw = w - 110
    for i, kz in enumerate(ks):
        try:
            p, q = [int(v) for v in kz.replace(" ", "").split("/")]
        except Exception:
            continue
        q = max(1, min(q, 20))
        c = _rang(u, i)
        ry = y + i * rowh + (h - rowh * n) / 2
        lbl(s, x + 30, ry + rowh * 0.42, f"$\\frac{{{p}}}{{{q}}}$", size=24, color=c, a=A("accent"))
        for j in range(q):
            bf, bop = (c, 1.0) if j < p else _bosh(u, i)
            s.rect(x + 80 + j * bw / q, ry + rowh * 0.15, bw / q, rowh * 0.55, fill=bf, op=bop,
                   line="#FFFFFF" if not u.qorongi else u.muted, lw=1.5, a=A("item", keyin=False, dl=A.t + j * 30))
        A.t += A.st * 2
        A.bosqich()


CHIZMALAR = {
    "son_oqi": (son_oqi, "Son o'qi", {"tur": "son_oqi", "dan": -6, "gacha": 6, "nuqtalar": [{"x": -3, "nom": "A"}], "sakrashlar": [{"dan": -3, "ga": 2, "nom": "+5"}], "kesmalar": [{"dan": 0, "ga": 2}]}),
    "ulush": (ulush, "Ulush (doira / tasma / kvadrat)", {"tur": "ulush", "bolak": 8, "boyalgan": 3, "shakl": "doira"}),
    "tasma": (tasma, "Tasma modeli (masala)", {"tur": "tasma", "bolak": 5, "boyalgan": 2, "jami": "150 bet", "bolak_nomi": "30 bet", "boyalgan_nomi": "60 bet"}),
    "daraxt": (daraxt, "Daraxt sxemasi (kombinatorika)", {"tur": "daraxt", "ildiz": "•", "darajalar": [["Sh1", "Sh2", "Sh3"], ["K1", "K2"]]}),
    "venn": (venn, "Venn diagrammasi", {"tur": "venn", "toplamlar": [{"nom": "A", "elementlar": ["1", "3"]}, {"nom": "B", "elementlar": ["4", "6"]}], "umumiy": ["2"]}),
    "ichma_ich": (ichma_ich, "Ichma-ich to'plamlar", {"tur": "ichma_ich", "qatlamlar": [{"nom": "ℕ — natural", "misol": ["1", "2", "17"]}, {"nom": "ℤ — butun", "misol": ["−5", "0"]}, {"nom": "ℚ — ratsional", "misol": ["1/2", "−3/4"]}]}),
    "tarozi": (tarozi, "Tarozi (tenglama)", {"tur": "tarozi", "chap": ["x", "+8"], "ong": ["12"], "muvozanat": True, "tenglama": "x + 8 = 12"}),
    "termometr": (termometr, "Termometr", {"tur": "termometr", "dan": -10, "gacha": 10, "qiymat": -2, "belgilar": [7, -2]}),
    "grafik": (grafik, "Funksiya grafigi", {"tur": "grafik", "funksiya": "x^2-2", "dan": -3, "gacha": 3, "nuqtalar": [[1, -1]]}),
    "ustun": (ustun, "Ustunli diagramma", {"tur": "ustun", "nomlar": ["Du", "Se", "Chor"], "qiymatlar": [3, 5, 4]}),
    "uchburchak": (uchburchak, "Uchburchak", {"tur": "uchburchak", "turi": "oddiy", "nomlar": ["A", "B", "C"], "tomonlar": ["a", "b", "c"], "balandlik": True}),
    "tortburchak": (tortburchak, "To'rtburchak", {"tur": "tortburchak", "a": "5 sm", "b": "3 sm", "ichida": "S = 15 sm²"}),
    "kvadrat": (tortburchak, "Kvadrat", {"tur": "kvadrat", "a": "4 sm"}),
    "aylana": (aylana, "Aylana / doira", {"tur": "aylana", "radius": "r", "diametr": "d", "doira": True}),
    "katak": (katak, "Kataklar / nuqtalar massivi", {"tur": "katak", "qator": 3, "ustun": 4, "boyalgan": 12, "nom": "3 · 4 = 12"}),
    "nuqtalar": (nuqtalar, "Sanoq guruhlari", {"tur": "nuqtalar", "guruhlar": [3, 4], "amal": "+"}),
    "soat": (soat, "Soat", {"tur": "soat", "soat": 3, "daqiqa": 15}),
    "burchak": (burchak, "Burchak", {"tur": "burchak", "gradus": 60}),
    "kasrlar": (kasrlar, "Kasrlarni taqqoslash", {"tur": "kasrlar", "kasrlar": ["1/2", "2/3", "3/4"]}),
}


def chiz(s, sp, x, y, w, h, u, qadam=1, kechikish=0, bosqichli=False):
    """Chizmani joylaydi. Qaytaradi: keyingi bo'sh qadam raqami."""
    if not isinstance(sp, dict):
        return qadam
    fn = CHIZMALAR.get(str(sp.get("tur", "")).strip())
    if not fn:
        return qadam
    A = _A(u, qadam, kechikish, bosqichli or bool(sp.get("bosqichli")))
    try:
        fn[0](s, sp, x, y, w, h, u, A)
    except Exception:  # noto'g'ri chizma ma'lumoti butun taqdimotni buzmasin
        return qadam
    return (A.s or qadam)
