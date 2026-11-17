"""Slayd-bloklar: har bir pedagogik slayd turi uchun oldindan yozilgan «dastur».

Blok mazmunni oladi va uni tanlangan uslubga moslab joylaydi: kartalar, yorliqlar, chizmalar, animatsiya
ketma-ketligi, pastki navigatsiya. Har blokda bir nechta joylashuv varianti bor — urug' (seed) qaysi biri
chiqishini tanlaydi, shuning uchun bir mavzu har safar boshqacha, lekin doim tartibli ko'rinadi.
"""
from __future__ import annotations

import random
import re

from . import chizma as CH
from . import formula as FM
from .olchov import kenglik
from .sahna import H, W, Slayd, matn_balandligi
from .uslub import Uslub, och

M = 48
CT = 118
CB = 652


class K:
    """Blok konteksti."""

    def __init__(self, s: Slayd, u: Uslub, rng: random.Random, nav: dict, rasm_bor=None):
        self.s, self.u, self.rng, self.nav = s, u, rng, nav
        self.rasm_bor = rasm_bor or (lambda key: False)
        self.qadam = 0  # birinchi komponent o'zi chiqadi

    def A(self, rol="card", s=None, dl=0, d=None, ms=None):
        e, dd, mss = self.u.anim.get(rol, self.u.anim["card"])
        a = {"s": self.qadam if s is None else s, "e": e, "ms": ms or mss, "dl": int(dl)}
        if d or dd:
            a["d"] = d or dd
        return a

    def keyingi(self):
        self.qadam += 1
        return self.qadam

    @property
    def st(self):
        return self.u.anim.get("stagger", 140)


# ------------------------------------------------------------------ kichik qismlar
def kart(k: K, x, y, w, h, i=0, a=None, lnk=None, fill=None, op=None, line=None):
    u = k.u
    ks = u.kart_s
    ln, lop = u.kart_chiziq(i)
    el = k.s.rect(x, y, w, h, fill=fill or u.kart_rang(i), op=ks["op"] if op is None else op, line=line if line is not None else ln,
                  lw=1.4 if ks.get("dash") else 1.2, r=ks["r"], sh=ks["sh"], dash=1 if ks.get("dash") else 0, a=a, lnk=lnk)
    if ln:
        el["lop"] = lop
    return el


def pill(k: K, x, y, matn, color, a=None, size=11, fg=None, h=None, lnk=None):
    matn = matn.upper()
    tw = kenglik(matn, "sans", True, size) + size * 0.08 * len(matn)
    w = tw + 22
    h = h or size + 12
    k.s.rect(x, y, w, h, fill=color, r=h / 2, a=a, lnk=lnk)
    k.s.matn(x, y, w, h, matn, size=size, bold=True, color=fg or k.u.matn_ustida(color), align="c", va="m", spc=80, a=a, min_scale=0.7, lnk=lnk)
    return w


def ikon(k: K, cx, cy, glyph, color, r=17, a=None, solid=False):
    u = k.u
    if solid:
        k.s.doira(cx, cy, r, fill=color, a=a)
        fg = u.matn_ustida(color)
    else:
        k.s.doira(cx, cy, r, fill=color, op=0.14 if not u.qorongi else 0.25, a=a)
        fg = color if not u.qorongi else och(color, 0.25)
    k.s.matn(cx - r, cy - r, 2 * r, 2 * r, glyph, size=r * 1.05, bold=True, color=fg, align="c", va="m", a=a, min_scale=0.6)


def bosh_qism(k: K, kicker, sarlavha, izoh=None):
    u = k.u
    k.s.matn(M, 26, W - 2 * M, 18, kicker.upper(), size=11.5, bold=True, color=u.acc[0], spc=110, nm="!!kicker", min_scale=0.7)
    k.s.matn(M, 46, W - 2 * M, 50, sarlavha, size=31, font=u.head, bold=True, color=u.ink, nm="!!title", min_scale=0.62)
    if izoh:
        k.s.matn(M, 92, W - 2 * M, 20, izoh, size=13, italic=True, color=u.muted, min_scale=0.7)


def pastki(k: K):
    """Pastki navigatsiya: bo'lim nuqtalari, bo'lim nomi, menyu, oldingi/keyingi, sanoq."""
    u, nav = k.u, k.nav
    y = 672
    secs = nav.get("sections") or []
    cur = nav.get("sec", -1)
    x = M
    for i, (nom, first) in enumerate(secs):
        on = i == cur
        k.s.doira(x + 11, y + 11, 11, fill=u.acc[0] if on else None, line=u.acc[0] if on else u.muted, lw=1.2, lnk=first, nm=f"!!dot{i}",
                  op=1.0)
        k.s.matn(x, y, 22, 22, str(i + 1), size=10.5, bold=True, color=u.matn_ustida(u.acc[0]) if on else u.muted, align="c", va="m", lnk=first)
        x += 28
    if 0 <= cur < len(secs):
        k.s.matn(x + 6, y + 2, 360, 18, secs[cur][0], size=11.5, color=u.muted, min_scale=0.7)
    bx = W - M - 168
    fill, op = ("#FFFFFF", 0.75) if not u.qorongi else ("#FFFFFF", 0.1)
    k.s.rect(bx, y - 2, 168, 26, fill=fill, op=op, line=u.muted if not u.qorongi else None, lw=0.6, r=13, nm="!!navbar")
    k.s.matn(bx + 6, y - 2, 26, 26, "▦", size=13, color=u.muted, align="c", va="m", lnk=nav.get("reja"))
    k.s.matn(bx + 34, y - 2, 22, 26, "‹", size=17, bold=True, color=u.ink, align="c", va="m", lnk="prev")
    k.s.matn(bx + 58, y - 2, 74, 26, f"{nav['idx'] + 1:02d} / {nav['total']:02d}", size=11, color=u.muted, align="c", va="m")
    k.s.matn(bx + 136, y - 2, 22, 26, "›", size=17, bold=True, color=u.ink, align="c", va="m", lnk="next")


def tegish(k: K, x, y, w, h):
    """Ko'rinmas bosish maydoni (trigger): karta ustidagi matn bosishga xalaqit bermasin."""
    return k.s.rect(x, y, w, h, fill="#FFFFFF", op=0.0)


def _yorliq_kartasi(k: K, x, y, w, h, label, color, i=0, a=None, ichki=None):
    """Sarlavhali karta: oila uslubiga ko'ra yorliq (pill) yoki rangli tasma. Ichki joy (x, y, w, h) qaytaradi."""
    u = k.u
    kart(k, x, y, w, h, i, a=a)
    if u.tab == "bar" and label:
        k.s.rect(x, y, w, 34, fill=color, r=min(u.kart_s["r"], 10), a=a)
        k.s.rect(x, y + 20, w, 14, fill=color, a=a)
        k.s.matn(x + 16, y, w - 32, 34, label, size=13, bold=True, color=u.matn_ustida(color), va="m", a=a, min_scale=0.7)
        return x + 18, y + 46, w - 36, h - 58
    if label:
        pill(k, x + 18, y + 16, label, color, a=a, size=10.5)
        return x + 18, y + 48, w - 36, h - 62
    return x + 18, y + 16, w - 36, h - 32


def _vizual(k: K, e, x, y, w, h, s, ichida_kart=True):
    """Chizma yoki rasm (rasm bo'lmasa — chizma, u ham bo'lmasa — hech narsa)."""
    u = k.u
    ch = e.get("chizma")
    key = e.get("rasm")
    if ichida_kart:
        kart(k, x, y, w, h, 1, a=k.A("card", s))
        x, y, w, h = x + 14, y + 14, w - 28, h - 28
    cap = e.get("izoh") if e.get("tur") in ("chizma", "rasm", "hayotiy") else None
    if cap:
        k.s.matn(x, y + h - 22, w, 22, cap, size=13, italic=True, color=u.muted, align="c", min_scale=0.7, a=k.A("item", s, dl=600))
        h -= 28
    if key and k.rasm_bor(key):
        k.s.img(x, y, w, h, "rasm:" + key, a=k.A("big", s, dl=k.st))
        return s
    if ch:
        return CH.chiz(k.s, ch, x, y, w, h, u, qadam=s, kechikish=k.st, bosqichli=bool(ch.get("bosqichli")))
    if key:
        # rasm hali chizilmagan: joy ushlab turuvchi
        k.s.rect(x + w * 0.2, y + h * 0.2, w * 0.6, h * 0.6, fill=None, line=u.muted, lw=1.2, dash=1, r=12, a=k.A("item", s))
        k.s.matn(x + w * 0.2, y + h * 0.2, w * 0.6, h * 0.6, f"rasm: {key}", size=13, color=u.muted, align="c", va="m", a=k.A("item", s))
    return s



FORMULA_FAQAT = re.compile(r"^\s*\$[^$]+\$\s*$")


def yozuv(k: K, text, x, y, w, h, size=18, color=None, align="l", va="t", a=None, bold=False, min_scale=0.55, urg=None):
    """Matn yoki faqat formula bo'lsa — chiroyli formula; aralash bo'lsa — matn ichida formula."""
    color = color or k.u.ink
    if FORMULA_FAQAT.match(text or ""):
        return FM.chiz(k.s, text, x, y, w, h, size=size * 1.25, color=color, align=align, a=a)
    return k.s.matn(x, y, w, h, text, size=size, color=color, align=align, va=va, a=a, bold=bold, min_scale=min_scale, urg=urg)


def mos_olcham(text, w, h, sizes=(26, 24, 22, 20, 19, 18, 17, 16, 15), lh=1.22):
    """Joyni to'ldiradigan eng katta shrift va matn balandligi."""
    for sz in sizes:
        th = matn_balandligi(text, w, sz, lh=lh)
        if th <= h:
            return sz, th
    sz = sizes[-1]
    return sz, min(h, matn_balandligi(text, w, sz, lh=lh))


def ustun_joyla(k: K, e, ix, iy, iw, ih, col, s, text, dl0=1):
    """Karta ichida: matn (joyga mos katta shrift) → formula → chizma/rasm. Bo'sh joy qolmaydi."""
    u = k.u
    has_vis = bool(e.get("chizma") or e.get("rasm"))
    fh = 0
    fsz = 34
    if e.get("formula"):
        fw, fa, fd = FM.olcha(e["formula"], fsz)
        fh = fa + fd + 26
    gap = 16
    if has_vis:
        sz, th = mos_olcham(text, iw, ih * 0.38, sizes=(20, 19, 18, 17, 16, 15)) if text else (18, 0)
        vis_top = iy + th + (gap if text else 0) + (fh + gap if fh else 0)
        vh = iy + ih - vis_top
        if vh < 110:  # chizmaga joy yetmasa formula kichrayadi
            fh = min(fh, 60)
            vis_top = iy + th + gap + (fh + gap if fh else 0)
            vh = iy + ih - vis_top
    else:
        sz, th = mos_olcham(text, iw, max(40, ih - (fh + gap if fh else 0))) if text else (20, 0)
        if fh:
            fh = min(max(fh, (ih - th - gap) * 0.7), 150)
    if text:
        k.s.matn(ix, iy, iw, th + 4, text, size=sz, color=u.ink, urg=col, a=k.A("item", s, dl=dl0 * k.st), lh=1.22)
    y = iy + th + (gap if text else 0)
    if fh:
        k.s.rect(ix, y, iw, fh, fill=col, op=0.08 if not u.qorongi else 0.16, r=10, a=k.A("accent", s, dl=(dl0 + 1) * k.st))
        FM.chiz(k.s, e["formula"], ix + 10, y + 6, iw - 20, fh - 12, size=fsz if not has_vis else 28, color=u.ink, a=k.A("accent", s, dl=(dl0 + 1) * k.st))
        y += fh + gap
    if has_vis:
        _vizual(k, e, ix, y, iw, iy + ih - y, s, ichida_kart=False)


# ------------------------------------------------------------------ komponentlar
LABEL = {"tarif": "Ta'rif", "qoida": "Qoida", "teorema": "Teorema", "formula": "Formula", "misol": "Misol", "masala": "Masala",
         "eslatma": "Muhim", "savol": "Savol", "hayotiy": "Hayotdan", "matn": ""}


def komp_matnli(k: K, e, x, y, w, h, i=0):
    """Ta'rif / qoida / teorema / matn: karta + matn (+ formula, + chizma)."""
    u = k.u
    s = k.qadam
    col = {"tarif": u.acc[0], "qoida": u.acc[1], "teorema": u.acc[3], "savol": u.acc[2], "hayotiy": u.acc[2]}.get(e["tur"], u.acc[i % 4])
    label = e.get("sarlavha") if e["tur"] == "matn" else (e.get("sarlavha") or LABEL.get(e["tur"], ""))
    has_vis = bool(e.get("chizma") or e.get("rasm"))
    if has_vis and w > 640:
        tw = w * 0.48
        komp_matnli(k, dict(e, chizma=None, rasm=""), x, y, tw - 10, h, i)
        _vizual(k, e, x + tw + 10, y, w - tw - 10, h, s)
        return
    ix, iy, iw, ih = _yorliq_kartasi(k, x, y, w, h, label, col, i, a=k.A("card", s))
    text = e.get("matn") or ""
    if e.get("bandlar"):
        text = "\n".join("• " + b["matn"] for b in e["bandlar"] if b.get("matn"))
    ustun_joyla(k, e, ix, iy, iw, ih, col, s, text)


def komp_formula(k: K, e, x, y, w, h, i=0):
    u = k.u
    s = k.qadam
    col = u.acc[i % 4]
    ix, iy, iw, ih = _yorliq_kartasi(k, x, y, w, h, e.get("sarlavha") or "Formula", col, i, a=k.A("card", s))
    cap = e.get("matn") or e.get("izoh")
    capt = 0
    if cap:
        capt = min(90, ih * 0.35)
        k.s.matn(ix, iy + ih - capt, iw, capt, cap, size=16, color=u.muted, align="c", va="m", a=k.A("item", s, dl=2 * k.st))
    FM.chiz(k.s, e.get("formula") or "", ix, iy, iw, ih - capt, size=46, color=u.ink, a=k.A("big", s, dl=k.st))


def komp_xossalar(k: K, e, x, y, w, h, i=0):
    u = k.u
    bs = e.get("bandlar") or []
    n = len(bs)
    if not n:
        return
    if e.get("sarlavha") and h > 300:
        k.s.matn(x, y, w, 26, e["sarlavha"], size=18, bold=True, color=u.ink, a=k.A("item", k.qadam))
        y += 34
        h -= 34
    cols = 1 if w < 520 else (2 if n in (2, 4) else 3 if n in (3, 5, 6) else 2)
    if n == 1:
        cols = 1
    rows = (n + cols - 1) // cols
    gap = 16
    cw = (w - gap * (cols - 1)) / cols
    ch = (h - gap * (rows - 1)) / rows
    glyphs = ["✓", "↔", "∞", "≈", "+", "×"]
    variant = k.rng.randrange(2)
    for j, b in enumerate(bs):
        r_, c_ = divmod(j, cols)
        bx, by = x + c_ * (cw + gap), y + r_ * (ch + gap)
        col = u.acc[j % 4]
        s = k.qadam
        dl = j * k.st
        kart(k, bx, by, cw, ch, j, a=k.A("card", s, dl=dl))
        tx = bx + 18
        if variant == 0 and cw > 200:
            ikon(k, bx + 36, by + 36, glyphs[j % len(glyphs)], col, r=18, a=k.A("accent", s, dl=dl + 80))
            tx = bx + 66
        else:
            k.s.rect(bx, by + 18, 5, 34, fill=col, r=2, a=k.A("accent", s, dl=dl))
        k.s.matn(tx, by + 18, cw - (tx - bx) - 16, 36, b.get("nom") or "", size=19, bold=True, color=col, va="m", a=k.A("item", s, dl=dl + 80), min_scale=0.6)
        top = by + 64
        avail = ch - 78
        fh = 0
        if b.get("formula"):
            fw, fa, fd = FM.olcha(b["formula"], 28)
            fh = min(fa + fd + 12, avail * 0.5)
        th = 0
        if b.get("matn"):
            sz, th = mos_olcham(b["matn"], cw - 36, avail - (fh + 10 if fh else 0), sizes=(22, 20, 19, 18, 17, 16, 15, 14))
            k.s.matn(bx + 18, top, cw - 36, th + 4, b["matn"], size=sz, color=u.ink, a=k.A("item", s, dl=dl + 140), lh=1.22)
        if fh:
            FM.chiz(k.s, b["formula"], bx + 14, top + th + 10, cw - 28, fh, size=28, color=u.ink, align="l", a=k.A("item", s, dl=dl + 200))


def komp_misol(k: K, e, x, y, w, h, i=0):
    """Misol / masala: shart, chizma, keyin har bosishda bitta qadam, oxirida javob."""
    u = k.u
    s = k.qadam
    col = u.acc[2] if e["tur"] == "masala" else u.acc[0]
    has_vis = bool(e.get("chizma") or e.get("rasm"))
    if has_vis and w > 760:
        vw = w * 0.44
        komp_misol(k, dict(e, chizma=None, rasm=""), x, y, w - vw - 16, h, i)
        _vizual(k, e, x + w - vw, y, vw, h, s)
        return
    label = (e.get("sarlavha") or LABEL[e["tur"]])
    ix, iy, iw, ih = _yorliq_kartasi(k, x, y, w, h, label, col, i, a=k.A("card", s))
    qs = e.get("qadamlar") or []
    jav = e.get("javob")
    shart = e.get("shart") or e.get("matn") or ""
    jh = 50 if jav else 0
    n = len(qs)
    row = 44
    steps_h = n * row
    gap = 12
    free = ih - jh - steps_h - (gap if n else 0)
    if has_vis:
        sz, th = mos_olcham(shart, iw, free * 0.35, sizes=(20, 19, 18, 17, 16, 15)) if shart else (18, 0)
    else:
        sz, th = mos_olcham(shart, iw, free, sizes=(24, 22, 20, 19, 18, 17, 16, 15)) if shart else (18, 0)
    if shart:
        k.s.matn(ix, iy, iw, th + 4, shart, size=sz, color=u.ink, urg=col, a=k.A("item", s, dl=k.st), lh=1.22)
    y0 = iy + th + gap
    if has_vis:
        vh = free - th - gap
        if vh > 60:
            _vizual(k, e, ix, y0, iw, vh, s, ichida_kart=False)
            y0 += vh + gap
    else:
        # qadamlarni kengroq joylaymiz
        extra = max(0, free - th)
        row = min(64, row + extra / max(n, 1) * 0.5) if n else row
    for j, q in enumerate(qs):
        st = k.keyingi()
        ry = y0 + j * row
        k.s.doira(ix + 14, ry + 15, 13, fill=col, a=k.A("accent", st))
        k.s.matn(ix + 1, ry + 2, 26, 26, str(j + 1), size=12.5, bold=True, color=u.matn_ustida(col), align="c", va="m", a=k.A("accent", st))
        k.s.matn(ix + 40, ry + 4, iw - 44, row - 6, q, size=18 if row >= 48 else 16.5, color=u.ink, a=k.A("item", st, dl=80), lh=1.15, min_scale=0.6)
    if jav:
        st = k.keyingi() if n else s
        dl = 0 if n else 2 * k.st
        k.s.rect(ix, iy + ih - jh + 4, iw, jh - 6, fill=u.ok, op=0.14 if not u.qorongi else 0.3, line=u.ok, lw=1.2, r=10, a=k.A("accent", st, dl=dl))
        k.s.matn(ix + 14, iy + ih - jh + 4, iw - 28, jh - 6, "**Javob:** " + jav, size=18, color=u.ink, va="m", a=k.A("accent", st, dl=dl), min_scale=0.6)


def komp_jadval(k: K, e, x, y, w, h, i=0):
    u = k.u
    cols = e.get("ustunlar") or []
    rows = e.get("qatorlar") or []
    nc = len(cols)
    if not nc:
        return
    s = k.qadam
    if e.get("sarlavha") and h > 260:
        k.s.matn(x, y, w, 24, e["sarlavha"], size=17, bold=True, color=u.ink, a=k.A("item", s))
        y += 30
        h -= 30
    # ustun kengliklari matn uzunligiga qarab
    lens = [max([len(cols[c])] + [len(r[c]) if c < len(r) else 0 for r in rows]) + 6 for c in range(nc)]
    tot = sum(lens)
    cw = [w * L / tot for L in lens]
    nr = len(rows) + 1
    rh = min(86, h / nr)
    fs = 19 if rh >= 70 else 17 if rh >= 56 else 15
    kart(k, x, y, w, rh * nr, 0, a=k.A("card", s))
    hc = u.acc[0]
    k.s.rect(x, y, w, rh, fill=hc, r=min(u.kart_s["r"], 10), a=k.A("card", s))
    k.s.rect(x, y + rh - 10, w, 10, fill=hc, a=k.A("card", s))
    cx = x
    for c in range(nc):
        k.s.matn(cx + 10, y, cw[c] - 20, rh, cols[c], size=fs, bold=True, color=u.matn_ustida(hc), va="m", align="c" if c else "l", a=k.A("card", s), min_scale=0.6)
        cx += cw[c]
    for r_, row in enumerate(rows):
        st = k.keyingi() if len(rows) > 2 else s
        ry = y + rh * (r_ + 1)
        if r_ % 2 == 1:
            k.s.rect(x + 1, ry, w - 2, rh, fill=u.acc[0], op=0.06 if not u.qorongi else 0.1, a=k.A("item", st))
        k.s.line(x + 12, ry, x + w - 12, ry, color=u.muted, lw=0.6, op=0.4, a=k.A("item", st))
        cx = x
        for c in range(nc):
            val = row[c] if c < len(row) else ""
            if FORMULA_FAQAT.match(val):
                FM.chiz(k.s, val, cx + 6, ry + 4, cw[c] - 12, rh - 8, size=fs * 1.3, color=u.ink, a=k.A("item", st, dl=c * 60))
            else:
                k.s.matn(cx + 10, ry, cw[c] - 20, rh, val, size=fs, bold=(c == 0), color=u.ink if c else u.acc[0], va="m",
                         align="c" if c else "l", a=k.A("item", st, dl=c * 60), min_scale=0.55)
            cx += cw[c]


def komp_taqqoslash(k: K, e, x, y, w, h, i=0):
    u = k.u
    bs = e.get("bandlar") or []
    n = len(bs)
    if not n:
        return
    if e.get("sarlavha") and h > 300:
        k.s.matn(x, y, w, 26, e["sarlavha"], size=18, bold=True, color=u.ink, a=k.A("item", k.qadam))
        y += 34
        h -= 34
    gap = 16
    cw = (w - gap * (n - 1)) / n
    for j, b in enumerate(bs):
        st = k.qadam if j == 0 else k.keyingi()
        bx = x + j * (cw + gap)
        col = u.acc[j % 4]
        kart(k, bx, y, cw, h, j, a=k.A("card", st))
        k.s.rect(bx, y, cw, 48, fill=col, r=min(u.kart_s["r"], 10), a=k.A("card", st))
        k.s.rect(bx, y + 34, cw, 14, fill=col, a=k.A("card", st))
        k.s.matn(bx + 12, y, cw - 24, 48, b.get("nom") or "", size=18, bold=True, color=u.matn_ustida(col), align="c", va="m", a=k.A("card", st), min_scale=0.6)
        top = y + 62
        bottom = y + h - 16
        parts = [p for p in ("formula", "matn", "misol") if b.get(p)]
        avail = bottom - top
        fh = min(110, avail * (0.42 if len(parts) > 1 else 0.8)) if b.get("formula") else 0
        mh = min(120, avail * 0.36) if b.get("misol") else 0
        th = avail - fh - mh - (14 if fh else 0) - (14 if mh else 0) if b.get("matn") else 0
        if fh:
            k.s.rect(bx + 12, top, cw - 24, fh, fill=col, op=0.07 if not u.qorongi else 0.14, r=10, a=k.A("accent", st, dl=k.st))
            FM.chiz(k.s, b["formula"], bx + 18, top + 6, cw - 36, fh - 12, size=34, color=u.ink, a=k.A("accent", st, dl=k.st))
            top += fh + 14
        if th > 20:
            sz, tth = mos_olcham(b["matn"], cw - 32, th, sizes=(20, 19, 18, 17, 16, 15, 14))
            k.s.matn(bx + 16, top, cw - 32, th, b["matn"], size=sz, color=u.ink, align="c", a=k.A("item", st, dl=2 * k.st), lh=1.2)
            top += th + 14
        if mh:
            k.s.rect(bx + 12, top, cw - 24, mh, fill=col, op=0.12 if not u.qorongi else 0.2, r=10, a=k.A("item", st, dl=3 * k.st))
            k.s.matn(bx + 20, top + 6, cw - 40, 20, "MISOL", size=11, bold=True, color=col, align="c", spc=100, a=k.A("item", st, dl=3 * k.st))
            yozuv(k, b["misol"], bx + 20, top + 28, cw - 40, mh - 34, size=18, align="c", va="m", a=k.A("item", st, dl=3 * k.st))


def komp_chizma(k: K, e, x, y, w, h, i=0):
    u = k.u
    s = k.qadam
    top = y
    if e.get("sarlavha") and e["tur"] == "chizma":
        k.s.matn(x, y, w, 24, e["sarlavha"], size=17, bold=True, color=u.ink, a=k.A("item", s))
        top += 30
    txt = e.get("matn")
    if txt and w > 700:
        tw = w * 0.34
        ix, iy, iw, ih = _yorliq_kartasi(k, x, top, tw, y + h - top, LABEL.get(e["tur"], "") if e["tur"] != "chizma" else "", u.acc[2], i, a=k.A("card", s))
        k.s.matn(ix, iy, iw, ih, txt, size=18, color=u.ink, urg=u.acc[2], a=k.A("item", s, dl=k.st))
        _vizual(k, e, x + tw + 16, top, w - tw - 16, y + h - top, s)
    else:
        if txt:
            k.s.matn(x, top, w, 50, txt, size=16, color=u.ink, a=k.A("item", s))
            top += 56
        _vizual(k, e, x, top, w, y + h - top, s)


def komp_eslatma(k: K, e, x, y, w, h, i=0):
    u = k.u
    s = k.qadam
    col = u.bad if any(wd in (e.get("sarlavha") or "").lower() for wd in ("diqqat", "xato", "ehtiyot")) else u.acc[0]
    k.s.rect(x, y, w, h, fill=col, op=0.1 if not u.qorongi else 0.2, line=col, lw=1.2, r=min(12, h / 2), a=k.A("accent", s))
    ikon(k, x + 26, y + h / 2, "!", col, r=14, a=k.A("accent", s), solid=True)
    lab = e.get("sarlavha") or "Muhim"
    k.s.matn(x + 52, y, w - 66, h, f"**{lab}:** " + (e.get("matn") or ""), size=16, color=u.ink, va="m", a=k.A("item", s, dl=k.st), min_scale=0.6)


KOMP = {"tarif": komp_matnli, "qoida": komp_matnli, "teorema": komp_matnli, "matn": komp_matnli, "savol": komp_matnli,
        "hayotiy": komp_chizma, "formula": komp_formula, "xossalar": komp_xossalar, "misol": komp_misol, "masala": komp_misol,
        "jadval": komp_jadval, "taqqoslash": komp_taqqoslash, "chizma": komp_chizma, "rasm": komp_chizma, "eslatma": komp_eslatma}


# ------------------------------------------------------------------ bloklar
def blok_kontent(k: K, d):
    """Bo'lim ichidagi oddiy slayd: elementlarni joylashtiradi."""
    bosh_qism(k, d["kicker"], d["sarlavha"])
    els = list(d["elementlar"])
    bar = [e for e in els if e["tur"] == "eslatma"]
    els = [e for e in els if e["tur"] != "eslatma"]
    x0, y0, w0 = M, CT, W - 2 * M
    h0 = CB - CT
    if bar:
        h0 -= 72 * len(bar[:1])
    if not els and bar:
        els, bar = bar, []
        h0 = CB - CT
    n = len(els)
    flip = k.rng.random() < 0.5
    gap = 20
    regions = []
    if n == 1:
        regions = [(x0, y0, w0, h0)]
    elif n == 2:
        a, b = els
        wide = {"jadval", "taqqoslash", "xossalar"}
        if a["tur"] in wide and b["tur"] in wide:
            regions = [(x0, y0, w0, h0 * 0.5 - gap / 2), (x0, y0 + h0 * 0.5 + gap / 2, w0, h0 * 0.5 - gap / 2)]
        else:
            r = 0.56 if a["tur"] in wide or (a.get("chizma") and not b.get("chizma")) else 0.44 if b["tur"] in wide else 0.5
            wa = w0 * r - gap / 2
            regions = [(x0, y0, wa, h0), (x0 + wa + gap, y0, w0 - wa - gap, h0)]
            if flip and a["tur"] not in ("misol", "masala") and b["tur"] in ("chizma", "rasm"):
                regions = regions  # chizma doim o'ngda qoladi — o'qish tartibi
    elif n == 3:
        wa = w0 * 0.5 - gap / 2
        hb = (h0 - gap) / 2
        regions = [(x0, y0, wa, h0), (x0 + wa + gap, y0, w0 - wa - gap, hb), (x0 + wa + gap, y0 + hb + gap, w0 - wa - gap, hb)]
        if flip:
            regions = [(x0 + w0 - wa, y0, wa, h0), (x0, y0, w0 - wa - gap, hb), (x0, y0 + hb + gap, w0 - wa - gap, hb)]
    else:
        els = els[:4]
        wa = (w0 - gap) / 2
        hb = (h0 - gap) / 2
        regions = [(x0, y0, wa, hb), (x0 + wa + gap, y0, wa, hb), (x0, y0 + hb + gap, wa, hb), (x0 + wa + gap, y0 + hb + gap, wa, hb)]
    for idx, (e, (x, y, w, h)) in enumerate(zip(els, regions)):
        if idx > 0:
            k.keyingi()
        KOMP.get(e["tur"], komp_matnli)(k, e, x, y, w, h, idx)
    if bar:
        k.keyingi()
        komp_eslatma(k, bar[0], x0, CB - 60, w0, 56)
    pastki(k)


def blok_titul(k: K, d):
    u, m = k.u, d["meta"]
    s = k.s
    v = k.rng.randrange(2)
    s.matn(M + 16, 40, 760, 18, (m.get("muassasa") or "").upper(), size=11.5, bold=True, color=u.muted, spc=120, min_scale=0.7)
    if m.get("kafedra"):
        s.matn(M + 16, 60, 760, 18, m["kafedra"], size=12, color=u.muted)
    tur = (m.get("tur") or "dars").upper()
    badge = f"{m['raqam']}-{tur}" if m.get("raqam") else tur
    bw = pill(k, M + 16, 104, badge, u.acc[0], size=11, a=k.A("accent", 0))
    sub = m.get("fan") or ""
    if m.get("sinf"):
        sub = f"{sub} · {m['sinf']}" if sub else m["sinf"]
    s.matn(M + 30 + bw, 104, 560, 23, sub, size=13, color=u.muted, va="m", min_scale=0.6)
    s.matn(M + 16, 168, 640, 210, m["mavzu"], size=46, font=u.head, bold=True, color=u.ink, va="m", nm="!!title", lh=1.08, min_scale=0.55,
           a=k.A("big", 0, dl=100) if v else None)
    if m.get("tayanch"):
        s.matn(M + 16, 392, 620, 60, " · ".join(m["tayanch"]), size=15, color=u.muted, a=k.A("item", 0, dl=300), lh=1.25)
    if m.get("muallif"):
        ikon(k, M + 30, 538, "✎", u.acc[0], r=14)
        s.matn(M + 54, 526, 420, 22, f"**{'Ma’ruzachi' if 'ma' in (m.get('tur') or '').lower() else 'Muallif'}:** {m['muallif']}", size=14, color=u.ink, min_scale=0.7)
        if m.get("davr"):
            s.matn(M + 54, 548, 420, 20, m["davr"], size=12, color=u.muted)
    # tugmalar
    by = 600
    s.rect(M + 16, by, 140, 40, fill=None, line=u.acc[0], lw=1.6, r=20, lnk=d.get("reja"))
    s.matn(M + 16, by, 140, 40, "Reja", size=15, bold=True, color=u.acc[0], align="c", va="m", lnk=d.get("reja"))
    s.rect(M + 172, by, 170, 40, fill=u.acc[0], r=20, lnk="next", sh=0 if u.qorongi else 1)
    s.matn(M + 172, by, 170, 40, "Boshlash  ›", size=15, bold=True, color=u.matn_ustida(u.acc[0]), align="c", va="m", lnk="next")
    # o'ng tomon: rasm / chizma / belgi
    hx, hy, hw, hh = 760, 110, 460, 480
    if m.get("rasm") and k.rasm_bor(m["rasm"]):
        s.img(hx, hy, hw, hh, "rasm:" + m["rasm"], a=k.A("big", 0, dl=200))
    elif m.get("chizma"):
        k.s.doira(hx + hw / 2, hy + hh / 2, 232, fill=u.acc[0], op=0.06 if not u.qorongi else 0.12, a=k.A("big", 0))
        CH.chiz(s, m["chizma"], hx + 40, hy + 40, hw - 80, hh - 80, u, qadam=0, kechikish=300)
    else:
        cx, cy = hx + hw / 2, hy + hh / 2
        s.doira(cx, cy, 210, fill=u.acc[0], op=0.08 if not u.qorongi else 0.14, a=k.A("big", 0))
        s.doira(cx, cy, 160, fill=None, line=u.acc[0], lw=1.2, op=0.6, a=k.A("big", 0, dl=120))
        s.doira(cx, cy, 128, fill=u.acc[0], a=k.A("big", 0, dl=200), sh=0 if u.qorongi else 1)
        belgi = m.get("belgi") or (m.get("qisqa") or m["mavzu"])[:2]
        if "$" in belgi or "\\" in belgi:
            FM.chiz(s, belgi, cx - 110, cy - 80, 220, 160, size=72, color=u.matn_ustida(u.acc[0]), a=k.A("accent", 0, dl=400))
        else:
            s.matn(cx - 115, cy - 80, 230, 160, belgi, size=72 if len(belgi) <= 3 else 44, font="serif", bold=True, color=u.matn_ustida(u.acc[0]),
                   align="c", va="m", a=k.A("accent", 0, dl=400), min_scale=0.4)


def blok_adabiyot(k: K, d):
    u, a = k.u, d["adabiyotlar"]
    bosh_qism(k, "Adabiyotlar", "Adabiyotlar va manbalar")
    lw = 700
    ix, iy, iw, ih = _yorliq_kartasi(k, M, CT, lw, CB - CT, "Asosiy adabiyotlar", u.acc[0], 0, a=k.A("card", 0))
    books = a["asosiy"][:5]
    rh = min(80, ih / max(len(books), 1))
    for j, b in enumerate(books):
        y = iy + j * rh
        k.s.rect(ix, y + 6, 34, 44, fill=u.acc[j % 4], op=0.85, r=4, a=k.A("item", 0, dl=(j + 1) * k.st))
        k.s.rect(ix + 4, y + 10, 4, 36, fill="#FFFFFF", op=0.5, a=k.A("item", 0, dl=(j + 1) * k.st))
        k.s.matn(ix + 50, y + 4, iw - 56, rh - 8,
                 f"**{b['muallif']}**" + (" " if b['muallif'] else "") + f"*{b['nomi']}*" + (f"\n{b['nashr']}" if b.get("nashr") else ""),
                 size=15, color=u.ink, a=k.A("item", 0, dl=(j + 1) * k.st), lh=1.18, sp=2)
    rx = M + lw + 20
    rw = W - M - rx
    half = (CB - CT - 20) / 2
    ix, iy, iw, ih = _yorliq_kartasi(k, rx, CT, rw, half, "Elektron manbalar", u.acc[1], 1, a=k.A("card", 1))
    txt = "\n".join(f"**{e['nomi']}** — {e['izoh']}" if e.get("izoh") else f"**{e['nomi']}**" for e in a["elektron"]) or "ziyonet.uz — ta’lim portali"
    k.s.matn(ix, iy, iw, ih, txt, size=15, color=u.ink, a=k.A("item", 1, dl=k.st), sp=6)
    ix, iy, iw, ih = _yorliq_kartasi(k, rx, CT + half + 20, rw, half, "Mustaqil o‘qish", u.acc[2], 2, a=k.A("card", 2))
    k.s.matn(ix, iy, iw, ih, a.get("mustaqil") or "Ma’ruza matni slayd izohlarida (Notes) berilgan.", size=15, color=u.ink, a=k.A("item", 2, dl=k.st))
    pastki(k)


def blok_takrorlash(k: K, d):
    u, tk = k.u, d["takrorlash"]
    sv = tk["savollar"]
    if tk.get("oyin") == "mosini_top" and len(sv) >= 3:
        return _mosini_top(k, tk)
    bosh_qism(k, "O‘tgan mavzuni takrorlash · o‘yin", "«Blits-so‘rov» o‘yini")
    if tk.get("mavzu"):
        w0 = pill(k, M, CT - 6, "O‘tgan mavzu", u.acc[0], size=10)
        k.s.matn(M + w0 + 10, CT - 6, 600, 22, tk["mavzu"], size=14, bold=True, color=u.ink, va="m", min_scale=0.6)
    k.s.matn(W - M - 520, CT - 6, 520, 22, "Avval o‘zingiz javob bering, so‘ng kartani bosing — javob chiqadi", size=12, italic=True, color=u.muted, align="r", va="m")
    n = len(sv)
    cols = 3 if n > 4 else 2
    rows = (n + cols - 1) // cols
    gap = 18
    top = CT + 30
    cw = (W - 2 * M - gap * (cols - 1)) / cols
    ch = (CB - top - gap * (rows - 1)) / rows
    for j, q in enumerate(sv):
        r_, c_ = divmod(j, cols)
        x, y = M + c_ * (cw + gap), top + r_ * (ch + gap)
        col = u.acc[j % 4]
        kart(k, x, y, cw, ch, j, a=k.A("card", 0, dl=j * 90))
        pill(k, x + 16, y + 14, f"{j + 1}-savol", col, size=10, a=k.A("card", 0, dl=j * 90))
        k.s.matn(x + 16, y + 44, cw - 32, ch - 100, q["savol"], size=17, color=u.ink, a=k.A("card", 0, dl=j * 90))
        hit = tegish(k, x, y, cw, ch)
        ans_y = y + ch - 54
        k.s.rect(x + 12, ans_y, cw - 24, 42, fill=col, op=0.12 if not u.qorongi else 0.22, r=8, a={"tr": hit["id"], "e": "zoom", "ms": 400})
        k.s.matn(x + 22, ans_y, cw - 44, 42, "**Javob:** " + q["javob"], size=14.5, color=u.ink, va="m", a={"tr": hit["id"], "e": "zoom", "ms": 400}, min_scale=0.55)
    pastki(k)


def _mosini_top(k: K, tk):
    u = k.u
    sv = tk["savollar"][:6]
    bosh_qism(k, "O‘tgan mavzuni takrorlash · o‘yin", "«Mosini top» o‘yini")
    if tk.get("mavzu"):
        w0 = pill(k, M, CT - 6, "O‘tgan mavzu", u.acc[0], size=10)
        k.s.matn(M + w0 + 10, CT - 6, 600, 22, tk["mavzu"], size=14, bold=True, color=u.ink, va="m", min_scale=0.6)
    order = list(range(len(sv)))
    k.rng.shuffle(order)
    letters = "ABCDEF"
    pos_of = {qi: li for li, qi in enumerate(order)}
    top = CT + 34
    rh = (CB - top) / len(sv)
    lw = 520
    for j, q in enumerate(sv):
        y = top + j * rh
        kart(k, M, y + 4, lw, rh - 10, j, a=k.A("item", 0, dl=j * 80))
        k.s.matn(M + 14, y + 4, lw - 28, rh - 10, f"**{j + 1}.** {q['savol']}", size=15, color=u.ink, va="m", a=k.A("item", 0, dl=j * 80), min_scale=0.55)
        qi = order[j]
        kart(k, W - M - lw, y + 4, lw, rh - 10, j + 1, a=k.A("item", 0, dl=j * 80 + 40))
        k.s.matn(W - M - lw + 14, y + 4, lw - 28, rh - 10, f"**{letters[j]})** {sv[qi]['javob']}", size=15, color=u.ink, va="m", a=k.A("item", 0, dl=j * 80 + 40), min_scale=0.55)
    for j in range(len(sv)):
        st = k.keyingi()
        y = top + j * rh
        k.s.rect(M + lw + 30, y + rh / 2 - 15, W - 2 * M - 2 * lw - 60, 30, fill=u.ok, r=15, a=k.A("accent", st))
        k.s.matn(M + lw + 30, y + rh / 2 - 15, W - 2 * M - 2 * lw - 60, 30, f"{j + 1} → {letters[pos_of[j]]}", size=13, bold=True, color="#FFFFFF", align="c", va="m", a=k.A("accent", st))
    pastki(k)


def blok_reja(k: K, d):
    u = k.u
    secs = d["sections"]
    bosh_qism(k, "Mundarija · interaktiv", "Reja" if "dars" in d.get("tur", "") else "Ma’ruza rejasi", "Kerakli bo‘limni bosing — o‘sha joyga o‘tasiz")
    n = len(secs)
    cols = 3 if n in (3, 5, 6) else 2 if n in (2, 4) else min(n, 3)
    rows = (n + cols - 1) // cols
    gap = 18
    top = CT + 8
    bottom = CB - (76 if d.get("maqsad") else 0)
    cw = (W - 2 * M - gap * (cols - 1)) / cols
    ch = min(190, (bottom - top - gap * (rows - 1)) / rows)
    glyphs = ["↗", "↔", "◔", "⇄", "★", "✓"]
    for j, (nom, first, last, belgi) in enumerate(secs):
        r_, c_ = divmod(j, cols)
        x, y = M + c_ * (cw + gap), top + r_ * (ch + gap)
        col = u.acc[j % 4]
        a = k.A("card", 0, dl=j * 100)
        kart(k, x, y, cw, ch, j, a=a, lnk=first)
        k.s.matn(x + 20, y + 14, 90, 46, f"{j + 1:02d}", size=34, font=u.head, bold=True, color=col, a=a, lnk=first)
        k.s.matn(x + cw - 60, y + 18, 40, 36, belgi or glyphs[j % len(glyphs)], size=24, color=col, align="c", va="m", a=a, lnk=first, min_scale=0.5)
        k.s.matn(x + 20, y + 66, cw - 40, ch - 100, nom, size=17, bold=True, color=u.ink, a=a, lnk=first)
        k.s.matn(x + 20, y + ch - 30, cw - 40, 18, f"{first + 1}–{last + 1}-slaydlar" if last > first else f"{first + 1}-slayd", size=11.5, color=u.muted, a=a, lnk=first)
    if d.get("maqsad"):
        y = CB - 62
        k.s.rect(M, y, W - 2 * M, 58, fill=u.acc[1], op=0.1 if not u.qorongi else 0.2, line=u.acc[1], lw=1, r=12, a=k.A("accent", 0, dl=n * 100))
        ikon(k, M + 28, y + 29, "◎", u.acc[1], r=14, a=k.A("accent", 0, dl=n * 100), solid=True)
        k.s.matn(M + 54, y, W - 2 * M - 70, 58, f"**{'Dars' if 'dars' in d.get('tur', '') else 'Ma’ruza'} maqsadi:** " + d["maqsad"], size=14, color=u.ink, va="m",
                 a=k.A("accent", 0, dl=n * 100), min_scale=0.55)
    pastki(k)


def blok_bolim(k: K, d):
    u = k.u
    i = d["no"]
    col = u.acc[i % 4]
    v = k.rng.randrange(2)
    k.s.matn(M + 20, 190, 300, 110, f"{i + 1:02d}", size=96, font=u.head, bold=True, color=col, a=k.A("big", 0), nm="!!kicker")
    k.s.matn(M + 20, 310, 680, 150, d["nom"], size=42, font=u.head, bold=True, color=u.ink, a=k.A("card", 0, dl=200), nm="!!title", lh=1.1)
    if d.get("izoh"):
        k.s.matn(M + 20, 470, 640, 60, d["izoh"], size=17, color=u.muted, a=k.A("item", 0, dl=400))
    cx, cy = 930, 340
    s = k.s
    s.doira(cx, cy, 200, fill=col, op=0.07 if not u.qorongi else 0.12, a=k.A("big", 0))
    s.doira(cx, cy, 150, fill=None, line=col, lw=1.2, op=0.6, a=k.A("big", 0, dl=120))
    s.doira(cx, cy, 118, fill=col, a=k.A("big", 0, dl=220), sh=0 if u.qorongi else 1)
    belgi = d.get("belgi") or f"{i + 1}"
    if "$" in belgi or "\\" in belgi:
        FM.chiz(s, belgi, cx - 100, cy - 70, 200, 140, size=60, color=u.matn_ustida(col), a=k.A("accent", 0, dl=400))
    else:
        s.matn(cx - 100, cy - 70, 200, 140, belgi, size=58 if len(belgi) <= 4 else 36, font="serif", bold=True, color=u.matn_ustida(col), align="c", va="m",
               a=k.A("accent", 0, dl=400), min_scale=0.4)
    pastki(k)


def blok_muammo(k: K, d):
    u, mu = k.u, d["muammo"]
    bosh_qism(k, d["kicker"], mu.get("sarlavha") or "Muammoli vaziyat")
    ms = mu["masalalar"][:2]
    top = CT
    n = len(ms)
    gap = 20
    cw = (W - 2 * M - gap * (n - 1)) / max(n, 1)
    ch = 170
    glyphs = ["?", "!"]
    for j, q in enumerate(ms):
        x = M + j * (cw + gap)
        col = u.acc[(j + 2) % 4]
        a = k.A("card", 0 if j == 0 else k.keyingi())
        kart(k, x, top, cw, ch, j, a=a)
        ikon(k, x + 36, top + 36, glyphs[j % 2], col, r=18, a=a)
        k.s.matn(x + 66, top + 20, cw - 84, 30, q.get("sarlavha") or f"{j + 1}-masala", size=18, bold=True, color=col, a=a)
        k.s.matn(x + 24, top + 66, cw - 48, ch - 80, q["matn"], size=16.5, color=u.ink, a=k.A("item", k.qadam, dl=k.st))
    y = top + ch + 24
    if mu.get("goya"):
        st = k.keyingi()
        k.s.rect(M, y, W - 2 * M, 54, fill=u.acc[3], op=0.1 if not u.qorongi else 0.2, r=12, a=k.A("accent", st))
        ikon(k, M + 28, y + 27, "✦", u.acc[3], r=14, a=k.A("accent", st), solid=True)
        k.s.matn(M + 54, y, W - 2 * M - 70, 54, "**G‘oya:** " + mu["goya"], size=16, color=u.ink, va="m", a=k.A("item", st, dl=k.st))
        y += 76
    z = mu.get("zanjir") or []
    if z:
        n = len(z)
        bw = min(300, (W - 2 * M - 60 * (n - 1)) / n)
        tot = n * bw + (n - 1) * 60
        x = (W - tot) / 2
        hh = min(110, CB - y - 10)
        for j, item in enumerate(z):
            st = k.keyingi()
            col = u.acc[j % 4]
            k.s.rect(x, y, bw, hh, fill=col, r=16, a=k.A("card", st), sh=0 if u.qorongi else 1)
            k.s.matn(x + 12, y, bw - 24, hh, item, size=20, bold=True, color=u.matn_ustida(col), align="c", va="m", a=k.A("card", st))
            if j < n - 1:
                k.s.matn(x + bw, y, 60, hh, "→", size=34, bold=True, color=u.muted, align="c", va="m", a=k.A("accent", st, dl=k.st))
            x += bw + 60
    pastki(k)


def blok_tarix(k: K, d):
    u, tr = k.u, d["tarix"]
    bosh_qism(k, d["kicker"], tr.get("sarlavha") or "Tarixdan")
    vs = tr["voqealar"]
    n = len(vs)
    if not n:
        pastki(k)
        return
    ly = CT + 18
    k.s.line(M, ly, W - M, ly, color=u.muted, lw=1.4, dash=1, a=k.A("diagram", 0, d="l"))
    gap = 18
    cw = (W - 2 * M - gap * (n - 1)) / n
    bottom = CB - (64 if tr.get("xulosa") else 0)
    ch = bottom - (ly + 34)
    for j, v in enumerate(vs):
        st = 0 if j == 0 else k.keyingi()
        x = M + j * (cw + gap)
        col = u.acc[j % 4]
        cx = x + cw / 2
        pw = kenglik(v["davr"].upper(), "sans", True, 10.5) + 30
        pill(k, cx - pw / 2, ly - 12, v["davr"], col, size=10.5, a=k.A("accent", st))
        k.s.line(cx, ly + 12, cx, ly + 34, color=col, lw=1.4, a=k.A("accent", st))
        y = ly + 34
        kart(k, x, y, cw, ch, j, a=k.A("card", st))
        ikon(k, x + 30, y + 30, "◷", col, r=16, a=k.A("card", st))
        k.s.matn(x + 56, y + 14, cw - 70, 40, v["nom"], size=17, bold=True, color=col, va="m", a=k.A("card", st), font=u.head)
        vis_h = 0
        if v.get("rasm") and k.rasm_bor(v["rasm"]):
            vis_h = min(150, ch * 0.4)
            k.s.img(x + 14, y + ch - vis_h - 10, cw - 28, vis_h, "rasm:" + v["rasm"], a=k.A("big", st, dl=2 * k.st))
        elif v.get("belgi"):
            vis_h = 64
            k.s.rect(x + 14, y + ch - vis_h - 10, cw - 28, vis_h, fill=col, op=0.08 if not u.qorongi else 0.16, r=10, a=k.A("accent", st, dl=2 * k.st))
            if "$" in v["belgi"]:
                FM.chiz(k.s, v["belgi"], x + 20, y + ch - vis_h - 6, cw - 40, vis_h - 8, size=26, color=col, a=k.A("accent", st, dl=2 * k.st))
            else:
                k.s.matn(x + 20, y + ch - vis_h - 10, cw - 40, vis_h, v["belgi"], size=22, bold=True, color=col, align="c", va="m", a=k.A("accent", st, dl=2 * k.st), min_scale=0.5)
        k.s.matn(x + 18, y + 62, cw - 36, ch - 80 - vis_h, v["matn"], size=14.5, color=u.ink, a=k.A("item", st, dl=k.st), lh=1.22)
    if tr.get("xulosa"):
        st = k.keyingi()
        k.s.matn(M, CB - 48, W - 2 * M, 44, tr["xulosa"], size=14, italic=True, color=u.muted, align="c", va="m", a=k.A("item", st))
    pastki(k)


def blok_xatolar(k: K, d):
    u = k.u
    xs = d["xatolar"]
    bosh_qism(k, d["kicker"], "Tipik xatolar: toping va tuzating!", "Avval xatoni o‘zingiz toping, so‘ng kartani bosing — tuzatilgan javob chiqadi")
    n = len(xs)
    cols = 3 if n > 4 else 2 if n > 1 else 1
    rows = (n + cols - 1) // cols
    gap = 18
    top = CT + 6
    cw = (W - 2 * M - gap * (cols - 1)) / cols
    ch = (CB - top - gap * (rows - 1)) / rows
    for j, x_ in enumerate(xs):
        r_, c_ = divmod(j, cols)
        x, y = M + c_ * (cw + gap), top + r_ * (ch + gap)
        a = k.A("card", 0, dl=j * 90)
        kart(k, x, y, cw, ch, j, a=a)
        pill(k, x + 14, y + 12, "✗ xato", u.bad, size=10, a=a)
        yozuv(k, x_["xato"], x + 14, y + 40, cw - 28, ch * 0.32, size=21, align="c", va="m", a=a, bold=True, min_scale=0.5)
        k.s.matn(x + 14, y + 40 + ch * 0.32, cw - 28, ch * 0.22, x_["sabab"], size=13, italic=True, color=u.muted, align="c", a=a, min_scale=0.55)
        hit = tegish(k, x, y, cw, ch)
        trg = {"tr": hit["id"], "e": "zoom", "ms": 400}
        by = y + ch - 52
        k.s.rect(x + 12, by, cw - 24, 42, fill=u.ok, op=0.14 if not u.qorongi else 0.28, line=u.ok, lw=1, r=10, a=trg)
        tg = x_["togri"]
        if FORMULA_FAQAT.match(tg):
            k.s.matn(x + 20, by, 80, 42, "**To‘g‘ri:**", size=14, color=u.ink, va="m", a=trg)
            FM.chiz(k.s, tg, x + 96, by + 2, cw - 120, 38, size=20, color=u.ink, a=trg, align="l")
        else:
            k.s.matn(x + 20, by, cw - 40, 42, "**To‘g‘ri:** " + tg, size=14, color=u.ink, va="m", a=trg, min_scale=0.55)
    pastki(k)


def blok_metodika(k: K, d):
    u, me = k.u, d["metodika"]
    bosh_qism(k, d["kicker"], me.get("sarlavha") or "Boshlang‘ich sinfda qanday o‘rgatamiz?")
    bs = me["bosqichlar"]
    y = CT
    if bs:
        n = len(bs)
        bw = (W - 2 * M - 40 * (n - 1)) / n
        for j, b in enumerate(bs):
            col = u.acc[j % 4]
            x = M + j * (bw + 40)
            a = k.A("card", 0, dl=j * 160)
            k.s.rect(x, y, bw, 64, fill=col, r=12, a=a, sh=0 if u.qorongi else 1)
            k.s.matn(x + 14, y, bw - 28, 64, f"**{j + 1}.** {b}", size=15, color=u.matn_ustida(col), va="m", a=a, min_scale=0.55)
            if j < n - 1:
                k.s.matn(x + bw, y, 40, 64, "→", size=26, bold=True, color=u.muted, align="c", va="m", a=a)
        y += 84
    ks = me["kartalar"]
    bottom = CB - (70 if me.get("tavsiya") else 0)
    if ks:
        n = len(ks)
        gap = 18
        cw = (W - 2 * M - gap * (n - 1)) / n
        for j, c in enumerate(ks):
            st = k.keyingi()
            x = M + j * (cw + gap)
            col = u.acc[(j + 1) % 4]
            ix, iy, iw, ih = _yorliq_kartasi(k, x, y, cw, bottom - y, c.get("sarlavha") or "", col, j, a=k.A("card", st))
            if c.get("chizma"):
                th = ih * 0.38
                k.s.matn(ix, iy, iw, th, c["matn"], size=14.5, color=u.ink, a=k.A("item", st, dl=k.st))
                CH.chiz(k.s, c["chizma"], ix, iy + th, iw, ih - th, u, qadam=st, kechikish=2 * k.st)
            else:
                k.s.matn(ix, iy, iw, ih, c["matn"], size=15.5, color=u.ink, a=k.A("item", st, dl=k.st))
    if me.get("tavsiya"):
        st = k.keyingi()
        k.s.rect(M, CB - 56, W - 2 * M, 54, fill=u.acc[0], op=0.08 if not u.qorongi else 0.18, r=12, a=k.A("accent", st))
        k.s.matn(M + 18, CB - 56, W - 2 * M - 36, 54, "**Metodik tavsiya:** " + me["tavsiya"], size=14, color=u.ink, va="m", a=k.A("item", st), min_scale=0.55)
    pastki(k)


def blok_xulosa(k: K, d):
    u, xu = k.u, d["xulosa"]
    if xu["bilaman"] or xu["bilib_oldim"]:
        bosh_qism(k, d["kicker"], "Xulosa: «B/B/B» jadvali")
        heads = [("Bilaman", xu["bilaman"]), ("Bilishni xohlayman", xu["bilishni_xohlayman"]), ("Bilib oldim", xu["bilib_oldim"])]
        gap = 18
        cw = (W - 2 * M - 2 * gap) / 3
        rows = max(len(h[1]) for h in heads) or 1
        rh = min(76, (CB - CT - 56) / rows)
        for c, (nom, items) in enumerate(heads):
            x = M + c * (cw + gap)
            col = [u.acc[1], u.acc[2], u.acc[0]][c]
            a = k.A("card", 0 if c < 2 else k.keyingi())
            k.s.rect(x, CT, cw, 44, fill=col, r=12, a=a)
            k.s.matn(x, CT, cw, 44, nom, size=16, bold=True, color=u.matn_ustida(col), align="c", va="m", a=a)
            for r_, it in enumerate(items):
                y = CT + 54 + r_ * rh
                kart(k, x, y, cw, rh - 8, c, a=k.A("item", k.qadam, dl=r_ * 90))
                k.s.matn(x + 14, y, cw - 28, rh - 8, it, size=14, color=u.ink, va="m", a=k.A("item", k.qadam, dl=r_ * 90), min_scale=0.55)
    else:
        bosh_qism(k, d["kicker"], "Xulosa")
        fs = xu["fikrlar"]
        n = len(fs)
        rh = min(84, (CB - CT) / max(n, 1))
        for j, f in enumerate(fs):
            st = 0 if j == 0 else k.keyingi()
            y = CT + j * rh
            kart(k, M, y, W - 2 * M, rh - 12, j, a=k.A("item", st))
            ikon(k, M + 32, y + (rh - 12) / 2, "✓", u.ok, r=15, a=k.A("accent", st), solid=True)
            if FORMULA_FAQAT.match(f):
                FM.chiz(k.s, f, M + 64, y + 4, W - 2 * M - 90, rh - 20, size=24, color=u.ink, align="l", a=k.A("item", st))
            else:
                k.s.matn(M + 64, y, W - 2 * M - 90, rh - 12, f, size=17, color=u.ink, va="m", a=k.A("item", st), min_scale=0.55)
    pastki(k)


def blok_test(k: K, d):
    u = k.u
    ts = d["test"]
    bosh_qism(k, d["kicker"], "Interaktiv test: javob variantini bosing", "To‘g‘ri variant bosilsa — yashil ✓, noto‘g‘ri bosilsa — qizil ✗")
    n = len(ts)
    cols = 3 if n > 4 else 2 if n > 1 else 1
    rows = (n + cols - 1) // cols
    gap = 16
    top = CT + 4
    cw = (W - 2 * M - gap * (cols - 1)) / cols
    ch = (CB - top - gap * (rows - 1)) / rows
    letters = "ABCD"
    for j, q in enumerate(ts):
        r_, c_ = divmod(j, cols)
        x, y = M + c_ * (cw + gap), top + r_ * (ch + gap)
        a = k.A("card", 0, dl=j * 80)
        kart(k, x, y, cw, ch, j, a=a)
        qh = min(56, ch * 0.32)
        sv = q["savol"]
        k.s.matn(x + 14, y + 10, cw - 28, qh, f"**{j + 1}.** " + sv, size=14.5, color=u.ink, a=a, min_scale=0.55)
        vs = q["variantlar"]
        vh = (ch - qh - 24) / len(vs)
        for vi, v in enumerate(vs):
            vy = y + 16 + qh + vi * vh
            k.s.rect(x + 12, vy, cw - 24, vh - 6, fill=u.acc[j % 4], op=0.08 if not u.qorongi else 0.16, line=u.muted, lw=0.6, r=8, a=a)
            if FORMULA_FAQAT.match(v):
                k.s.matn(x + 22, vy, 30, vh - 6, f"{letters[vi]})", size=13.5, color=u.ink, va="m", a=a)
                FM.chiz(k.s, v, x + 50, vy + 2, cw - 110, vh - 10, size=17, color=u.ink, align="l", a=a)
            else:
                k.s.matn(x + 22, vy, cw - 80, vh - 6, f"{letters[vi]})  {v}", size=13.5, color=u.ink, va="m", a=a, min_scale=0.55)
            ok = vi == q["javob"]
            opt = tegish(k, x + 12, vy, cw - 24, vh - 6)
            mark = {"tr": opt["id"], "e": "zoom", "ms": 350}
            k.s.doira(x + cw - 36, vy + (vh - 6) / 2, 11, fill=u.ok if ok else u.bad, a=mark)
            k.s.matn(x + cw - 47, vy + (vh - 6) / 2 - 11, 22, 22, "✓" if ok else "✗", size=13, bold=True, color="#FFFFFF", align="c", va="m", a=mark)
    pastki(k)


def blok_yakun(k: K, d):
    u = k.u
    bosh_qism(k, d["kicker"], "Nazorat, mustaqil ish va keyingi mavzu")
    lw = 620
    ix, iy, iw, ih = _yorliq_kartasi(k, M, CT, lw, CB - CT - 64, "Nazorat savollari", u.acc[0], 0, a=k.A("card", 0))
    qs = d["nazorat"]
    k.s.matn(ix, iy, iw, ih, "\n".join(f"{j + 1}. {q}" for j, q in enumerate(qs)) or "—", size=15, color=u.ink, a=k.A("item", 0, dl=k.st), sp=5, lh=1.18)
    rx = M + lw + 20
    rw = W - M - rx
    hh = (CB - CT - 84) / 2
    ix, iy, iw, ih = _yorliq_kartasi(k, rx, CT, rw, hh, "Mustaqil ish", u.acc[1], 1, a=k.A("card", 1))
    k.s.matn(ix, iy, iw, ih, "\n".join(f"{j + 1}. {q}" for j, q in enumerate(d["mustaqil_ish"])) or "—", size=14.5, color=u.ink, a=k.A("item", 1, dl=k.st), sp=4)
    ke = d["keyingi"]
    ix, iy, iw, ih = _yorliq_kartasi(k, rx, CT + hh + 20, rw, hh, "Keyingi mavzu", u.acc[2], 2, a=k.A("card", 2))
    k.s.matn(ix, iy, iw, ih, (f"**{ke['mavzu']}**" if ke.get("mavzu") else "") + (f"\n{ke['izoh']}" if ke.get("izoh") else ""), size=15, color=u.ink, a=k.A("item", 2, dl=k.st))
    a = k.A("big", 3)
    k.s.rect(rx, CB - 50, rw, 48, fill=u.acc[0], r=24, a=a, sh=0 if u.qorongi else 1)
    k.s.matn(rx, CB - 50, rw, 48, "E’tiboringiz uchun rahmat!", size=18, bold=True, color=u.matn_ustida(u.acc[0]), align="c", va="m", a=a)
    pastki(k)


BLOKLAR = {
    "titul": blok_titul, "adabiyot": blok_adabiyot, "takrorlash": blok_takrorlash, "reja": blok_reja, "bolim": blok_bolim,
    "muammo": blok_muammo, "tarix": blok_tarix, "kontent": blok_kontent, "xatolar": blok_xatolar, "metodika": blok_metodika,
    "xulosa": blok_xulosa, "test": blok_test, "yakun": blok_yakun,
}
