"""Barcha fanlar uchun slayd komponentlari: lug'at, dialog, parcha, vaqt chizig'i, xarita, tajriba, jarayon,
galereya, guruhlash va o'yinlar (moslash, to'g'ri/noto'g'ri, bo'sh joy, rasmda nima).

Har komponent (k, e, x, y, w, h, i) oladi — bloklar.blok_kontent bergan joyni to'ldiradi. Animatsiya qoidasi:
birinchi qism slayd bilan chiqadi, keyingi qismlar bosish bilan (k.keyingi()); o'yinlarda javob — kartani bosganda
(trigger). Rasm kaliti kutubxonada bo'lmasa rasm joyi qoldirilmaydi, matn kengayadi.
"""
from __future__ import annotations

import json
import math
import os
import re
from functools import lru_cache

from . import bloklar as B
from . import rasmlar as RS
from .uslub import och


def _rasm(k, key):
    return bool(key) and k.rasm_bor(key)


def _img(k, key, x, y, w, h, a, taglik=False):
    """Rasmni (w×h) ichiga joylaydi; taglik=True — orqasida yumshoq doira."""
    info = RS.malumot(key)
    iw, ih = (info.get("olcham") or [1024, 1024])[:2]
    sc = min(w / iw, h / ih)
    bw, bh = iw * sc, ih * sc
    cx, cy = x + w / 2, y + h / 2
    if taglik:
        r = max(bw, bh) * 0.52
        if k.u.qorongi:
            k.s.doira(cx, cy, r, fill="#FFFFFF", op=0.92, a=a)
        else:
            k.s.doira(cx, cy, r, fill=k.u.acc[0], op=0.1, a=a)
    elif k.u.qorongi and info.get("tur") == "chizma":
        k.s.rect(cx - bw / 2, cy - bh / 2, bw, bh, fill="#FFFFFF", r=8, a=a)
    k.s.img(cx - bw / 2, cy - bh / 2, bw, bh, "rasm:" + key, a=a)


def _tint(k, j, op_y=0.1, op_q=0.22):
    return k.u.acc[j % 4], (op_y if not k.u.qorongi else op_q)


# ------------------------------------------------------------------ lug'at
def komp_lugat(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    sz = e["sozlar"]
    n = len(sz)
    cols = n if n <= 3 else (2 if n == 4 else 3)
    rows = (n + cols - 1) // cols
    gap = 18
    cw, ch = (w - gap * (cols - 1)) / cols, (h - gap * (rows - 1)) / rows
    for j, it in enumerate(sz):
        r_, c_ = divmod(j, cols)
        cx, cy = x + c_ * (cw + gap), y + r_ * (ch + gap)
        col = u.acc[j % 4]
        a = k.A("card", s, dl=j * k.st)
        B.kart(k, cx, cy, cw, ch, j, a=a)
        bor = _rasm(k, it.get("rasm"))
        ih = ch * (0.46 if rows == 1 else 0.4) if bor else 0
        if bor:
            _img(k, it["rasm"], cx + 18, cy + 14, cw - 36, ih, a)
        wsz = min(48, ch * (0.11 if bor else 0.2), cw * 0.17)
        # mazmun bloki balandligi: so'z + o'qilishi + tarjima + misol
        blok = wsz * 1.32 + (wsz * 0.72 if it.get("oqilishi") else 0) + (wsz * 0.95 + 8 if it.get("tarjima") or it.get("misol") else 0) \
            + (max(13, wsz * 0.4) * 2.6 if it.get("misol") else 0)
        ty = cy + 14 + ih + 8 if bor else cy + max(12, (ch - blok) / 2)
        k.s.matn(cx + 12, ty, cw - 24, wsz * 1.3, it["soz"], size=wsz, bold=True, color=col if not u.qorongi else och(col, 0.3),
                 align="c", va="m", min_scale=0.45, a=a)
        ty += wsz * 1.32
        if it.get("oqilishi"):
            k.s.matn(cx + 12, ty, cw - 24, wsz * 0.7, it["oqilishi"], size=wsz * 0.48, italic=True, color=u.muted, align="c", min_scale=0.6, a=a)
            ty += wsz * 0.72
        if it.get("tarjima") or it.get("misol"):
            # tarjima va misol — kartani bosganda (o'quvchi avval o'zi topsin)
            ph = wsz * 0.95
            pw = min(cw - 40, max(90, len(it.get("tarjima") or "?") * wsz * 0.42 + 40))
            px = cx + (cw - pw) / 2
            k.s.rect(px, ty + 4, pw, ph, fill=None, line=u.muted, lw=1, dash=1, r=ph / 2, a=a)
            k.s.matn(px, ty + 4, pw, ph, "?", size=wsz * 0.5, bold=True, color=u.muted, align="c", va="m", a=a)
            tg = B.tegish(k, cx, cy, cw, ch)
            ra = {"tr": tg["id"], "e": "zoom", "ms": 350}
            if it.get("tarjima"):
                k.s.rect(px, ty + 4, pw, ph, fill=col, r=ph / 2, a=ra)
                k.s.matn(px, ty + 4, pw, ph, it["tarjima"], size=wsz * 0.5, bold=True, color=u.matn_ustida(col), align="c", va="m",
                         min_scale=0.5, a=ra)
            if it.get("misol"):
                my = ty + ph + 12
                k.s.matn(cx + 14, my, cw - 28, cy + ch - my - 8, it["misol"], size=max(13, wsz * 0.4), italic=True, color=u.ink,
                         align="c", min_scale=0.55, a=ra)


# ------------------------------------------------------------------ dialog
def komp_dialog(k, e, x, y, w, h, i=0):
    u = k.u
    qs = e["qatorlar"]
    ism = []
    for q in qs:
        if q["kim"] not in ism:
            ism.append(q["kim"])
    n = len(qs)
    gap = 10
    rh = min(118, (h - gap * (n - 1)) / n)
    top = y + (h - (rh * n + gap * (n - 1))) / 2
    for j, q in enumerate(qs):
        st = k.qadam if j == 0 else k.keyingi()
        side = ism.index(q["kim"]) % 2
        col = u.acc[side * 2 % 4]
        a = k.A("item", st)
        ry = top + j * (rh + gap)
        av_x = x + 30 if side == 0 else x + w - 30
        k.s.doira(av_x, ry + rh / 2, 26, fill=col, a=a)
        k.s.matn(av_x - 26, ry + rh / 2 - 26, 52, 52, q["kim"][:1].upper(), size=22, bold=True, color=u.matn_ustida(col),
                 align="c", va="m", a=a)
        tsz = 22 if rh >= 96 else 18 if rh >= 72 else 15
        kerak = max(k.s.olcham(q["matn"], tsz), k.s.olcham(q.get("tarjima") or "", tsz * 0.78), k.s.olcham(q["kim"], 12, bold=True)) + 48
        bw = min(w * 0.72, max(w * 0.3, kerak))
        bx = x + 70 if side == 0 else x + w - 70 - bw
        fop = 0.12 if not u.qorongi else 0.26
        k.s.rect(bx, ry, bw, rh, fill=col, op=fop, line=col, lw=1.2, r=min(22, rh / 2), a=a)
        k.s.matn(bx + 18, ry + 6, bw - 36, 18, q["kim"], size=12, bold=True, color=col if not u.qorongi else och(col, 0.35), a=a)
        th = rh - 30 - (tsz * 1.15 if q.get("tarjima") else 0)
        k.s.matn(bx + 18, ry + 24, bw - 36, max(20, th), q["matn"], size=tsz, color=u.ink, min_scale=0.5, a=a)
        if q.get("tarjima"):
            k.s.matn(bx + 18, ry + rh - tsz * 1.2 - 6, bw - 36, tsz * 1.2, q["tarjima"], size=tsz * 0.78, italic=True, color=u.muted,
                     min_scale=0.5, a=k.A("item", st, dl=300))


# ------------------------------------------------------------------ parcha (matn, she'r)
def komp_parcha(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    col = u.acc[i % 4]
    a = k.A("card", s)
    B.kart(k, x, y, w, h, i, a=a)
    k.s.matn(x + 22, y + 4, 80, 90, "“", size=90, font="serif", bold=True, color=col, a=a)
    if e.get("sarlavha"):
        B.pill(k, x + 90, y + 22, e["sarlavha"], col, a=a, size=11)
    matn = e["matn"]
    for soz in e.get("belgilar") or []:
        if soz and soz in matn and f"=={soz}==" not in matn:
            matn = matn.replace(soz, f"=={soz}==", 1)
    pastki = 34 if e.get("muallif") else 10
    ix, iy, iw, ih = x + 70, y + 60, w - 120, h - 60 - pastki - 14
    sz, th = B.mos_olcham(matn, iw, ih, sizes=(36, 34, 32, 30, 28, 26, 24, 22, 20, 19, 18, 17, 16, 15), lh=1.32)
    k.s.matn(ix, iy, iw, ih, matn, size=sz, font="serif", color=u.ink, urg=col, lh=1.32, va="m", min_scale=0.55,
             a=k.A("item", s, dl=k.st))
    if e.get("muallif"):
        k.s.matn(x + 40, y + h - pastki - 10, w - 80, 26, "— " + e["muallif"], size=16, italic=True, color=u.muted, align="r",
                 a=k.A("item", s, dl=2 * k.st))


# ------------------------------------------------------------------ vaqt chizig'i
def komp_vaqt_chizigi(k, e, x, y, w, h, i=0):
    u = k.u
    vs = e["voqealar"]
    n = len(vs)
    my = y + h / 2
    k.s.line(x + 10, my, x + w - 10, my, color=u.muted, lw=2.5, arr="end", a=k.A("diagram", k.qadam))
    seg = w / n
    cw = min(seg * 1.75 - 16, 330)
    chh = h / 2 - 46
    for j, v in enumerate(vs):
        st = k.qadam if j == 0 else k.keyingi()
        col = u.acc[j % 4]
        a = k.A("item", st)
        cx = x + seg * (j + 0.5)
        k.s.doira(cx, my, 9, fill=col, a=a)
        tepada = j % 2 == 0
        cy = y if tepada else my + 46
        bx = min(max(x, cx - cw / 2), x + w - cw)
        k.s.line(cx, my - 9 if tepada else my + 9, cx, cy + chh if tepada else cy, color=col, lw=1.5, a=a)
        B.kart(k, bx, cy, cw, chh, j, a=a)
        if v.get("sana"):
            pw = B.pill(k, bx + 14, cy + 12, v["sana"], col, a=a, size=12)
        ty = cy + 44
        bor = _rasm(k, v.get("rasm"))
        tw = cw - 28
        if bor:
            iw = min(chh - 56, cw * 0.36)
            _img(k, v["rasm"], bx + cw - iw - 10, cy + 10, iw, iw, a)
            tw = cw - iw - 34
        k.s.matn(bx + 14, ty, tw, 26, v.get("nom") or "", size=16, bold=True, color=u.ink, min_scale=0.55, a=a)
        if v.get("matn"):
            k.s.matn(bx + 14, ty + 28, cw - 28 if not bor or chh - 84 > (min(chh - 56, cw * 0.36) - 34) else tw, cy + chh - ty - 34,
                     v["matn"], size=13.5, color=u.muted if not u.qorongi else och(u.ink, 0.1), min_scale=0.55, a=a)


# ------------------------------------------------------------------ galereya
def komp_galereya(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    rs = e["rasmlar"]
    n = len(rs)
    cols = n if n <= 3 else 2
    rows = (n + cols - 1) // cols
    gap = 22
    cw, ch = (w - gap * (cols - 1)) / cols, (h - gap * (rows - 1)) / rows
    for j, r in enumerate(rs):
        r_, c_ = divmod(j, cols)
        cx, cy = x + c_ * (cw + gap), y + r_ * (ch + gap)
        a = k.A("big", s, dl=j * k.st)
        caph = 28 if r.get("izoh") and _rasm(k, r.get("rasm")) else 0
        if _rasm(k, r.get("rasm")):
            _img(k, r["rasm"], cx + 10, cy + 6, cw - 20, ch - caph - 14, a, taglik=RS.malumot(r["rasm"]).get("tur") == "rasm")
            kr = RS.kredit(r["rasm"])
            if kr:
                k.s.matn(cx, cy + ch - caph - 14, cw, 12, kr, size=8.5, color=u.muted, align="c", min_scale=0.6, a=a)
        else:
            # rasm yo'q — bo'sh karta emas: rangli plitka, nomi katta
            col = u.acc[j % 4]
            th = ch - 8
            k.s.rect(cx, cy, cw, th, fill=col, op=0.14 if not u.qorongi else 0.3, line=col, lw=1.4, r=min(22, cw / 8), a=a)
            k.s.doira(cx + cw / 2, cy + th * 0.4, min(cw, th) * 0.18, fill=col, op=0.9, a=a)
            k.s.matn(cx + cw / 2 - 40, cy + th * 0.4 - 40, 80, 80, str(j + 1), size=34, bold=True, color=u.matn_ustida(col), align="c", va="m", a=a)
            k.s.matn(cx + 14, cy + th * 0.62, cw - 28, th * 0.32, r.get("izoh") or "", size=min(26, cw * 0.08), bold=True, color=u.ink,
                     align="c", va="m", min_scale=0.5, a=a)
            continue
        if r.get("izoh"):
            k.s.matn(cx, cy + ch - caph, cw, caph, r["izoh"], size=16, bold=True, color=u.ink, align="c", va="m", min_scale=0.6, a=a)


# ------------------------------------------------------------------ guruhlash
def komp_guruhlash(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    gs = e["guruhlar"]
    n = len(gs)
    gap = 18
    cw = (w - gap * (n - 1)) / n
    st2 = k.keyingi()
    for j, g in enumerate(gs):
        col = u.acc[j % 4]
        cx = x + j * (cw + gap)
        a = k.A("card", s, dl=j * k.st)
        B.kart(k, cx, y, cw, h, j, a=a)
        k.s.rect(cx, y, cw, 52, fill=col, r=min(u.kart_s["r"], 12), a=a)
        k.s.rect(cx, y + 30, cw, 22, fill=col, a=a)
        k.s.matn(cx + 10, y, cw - 20, 52, g["nom"], size=19, bold=True, color=u.matn_ustida(col), align="c", va="m", min_scale=0.55, a=a)
        bs = g["bandlar"]
        if not bs:
            continue
        bh = min(62, (h - 72 - 10 * len(bs)) / len(bs))
        for b_i, b in enumerate(bs):
            by = y + 66 + b_i * (bh + 10)
            ba = k.A("item", st2, dl=(j * len(bs) + b_i) * 70)
            fop = 0.1 if not u.qorongi else 0.22
            k.s.rect(cx + 14, by, cw - 28, bh, fill=col, op=fop, line=col, lw=1, r=bh / 2, a=ba)
            k.s.matn(cx + 24, by, cw - 48, bh, b, size=min(21, bh * 0.42), color=u.ink, align="c", va="m", min_scale=0.5, a=ba)


# ------------------------------------------------------------------ tajriba
def komp_tajriba(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    top = y
    if e.get("maqsad"):
        pw = B.pill(k, x, top + 4, "Maqsad", u.acc[0], a=k.A("item", s), size=11)
        k.s.matn(x + pw + 12, top, w - pw - 12, 30, e["maqsad"], size=17, color=u.ink, va="m", min_scale=0.6, a=k.A("item", s))
        top += 42
    pastki = 52 if e.get("xavfsizlik") else 0
    hh = y + h - top - pastki
    gap = 16
    w1, w3 = w * 0.25, w * 0.29
    w2 = w - w1 - w3 - 2 * gap
    # jihozlar
    ix, iy, iw, ih = B._yorliq_kartasi(k, x, top, w1, hh, "Jihozlar", u.acc[2], 0, a=k.A("card", s))
    jh = e.get("jihozlar") or []
    if jh:
        rh = min(58, ih / len(jh))
        for j, it in enumerate(jh):
            ry = iy + j * rh
            a = k.A("item", s, dl=j * 80)
            if _rasm(k, it.get("rasm")):
                _img(k, it["rasm"], ix, ry + 2, rh - 6, rh - 6, a)
                k.s.matn(ix + rh + 2, ry, iw - rh - 2, rh, it["nom"], size=15, color=u.ink, va="m", min_scale=0.55, a=a)
            else:
                k.s.matn(ix, ry, iw, rh, "• " + it["nom"], size=15, color=u.ink, va="m", min_scale=0.55, a=a)
    # bosqichlar — har biri bosish bilan
    bx = x + w1 + gap
    ix, iy, iw, ih = B._yorliq_kartasi(k, bx, top, w2, hh, "Bosqichlar", u.acc[0], 1, a=k.A("card", s))
    bq = e["bosqichlar"]
    rh = ih / len(bq)
    for j, b in enumerate(bq):
        st = k.keyingi()
        a = k.A("item", st)
        ry = iy + j * rh
        B.ikon(k, ix + 16, ry + rh / 2, str(j + 1), u.acc[0], r=14, a=a, solid=True)
        k.s.matn(ix + 40, ry, iw - 40, rh - 4, b, size=18 if rh >= 70 else 16 if rh >= 50 else 14, color=u.ink, va="m",
                 min_scale=0.55, a=a)
    # natija
    nx = bx + w2 + gap
    st = k.keyingi()
    ix, iy, iw, ih = B._yorliq_kartasi(k, nx, top, w3, hh, "Natija", u.ok, 2, a=k.A("card", st))
    if e.get("natija"):
        sz, _ = B.mos_olcham(e["natija"], iw, ih, sizes=(22, 20, 19, 18, 17, 16, 15))
        k.s.matn(ix, iy, iw, ih, e["natija"], size=sz, color=u.ink, va="m", a=k.A("item", st, dl=k.st))
    if e.get("xavfsizlik"):
        B.komp_eslatma(k, {"sarlavha": "Xavfsizlik", "matn": e["xavfsizlik"]}, x, y + h - pastki + 6, w, pastki - 6)


# ------------------------------------------------------------------ jarayon (aylana / zanjir / qadam)
def komp_jarayon(k, e, x, y, w, h, i=0):
    u = k.u
    bs = e["bosqichlar"]
    n = len(bs)
    sh = e.get("shakl") or "zanjir"
    if sh == "qadam":
        gap = 16
        cw = (w - gap * (n - 1)) / n
        for j, b in enumerate(bs):
            st = k.qadam if j == 0 else k.keyingi()
            col = u.acc[j % 4]
            a = k.A("card", st)
            cx = x + j * (cw + gap)
            B.kart(k, cx, y, cw, h, j, a=a)
            B.ikon(k, cx + 26, y + 26, str(j + 1), col, r=16, a=a, solid=True)
            ih = h * 0.5 if any(_rasm(k, x_.get("rasm")) for x_ in bs) else 0
            if ih and _rasm(k, b.get("rasm")):
                _img(k, b["rasm"], cx + 12, y + 46, cw - 24, ih - 20, a)
            elif ih:
                k.s.doira(cx + cw / 2, y + 36 + ih / 2, min(cw, ih) * 0.3, fill=col, op=0.14 if not u.qorongi else 0.3, a=a)
                k.s.matn(cx, y + 36 + ih / 2 - 40, cw, 80, str(j + 1), size=54, bold=True, color=col, align="c", va="m", a=a)
            ty = y + 46 + ih
            k.s.matn(cx + 14, ty, cw - 28, 28, b.get("nom") or "", size=17, bold=True, color=u.ink, min_scale=0.55, a=a)
            if b.get("matn"):
                k.s.matn(cx + 14, ty + 30, cw - 28, y + h - ty - 40, b["matn"], size=14.5, color=u.ink, min_scale=0.55, a=a)
            if j < n - 1:
                k.s.matn(cx + cw - 2, y + h / 2 - 14, gap + 4, 28, "›", size=24, bold=True, color=u.muted, align="c", va="m", a=a)
        return
    # tugunlar joyi
    r = min(70 if sh != "aylana" else 54, w / (n * 3.0), h * 0.15)
    pts = []
    if sh == "aylana":
        cx0, cy0 = x + w / 2, y + h / 2 - 10
        rx, ry = min(w * 0.36, 420), h * 0.34
        for j in range(n):
            ang = -math.pi / 2 + 2 * math.pi * j / n
            pts.append((cx0 + rx * math.cos(ang), cy0 + ry * math.sin(ang)))
        if e.get("sarlavha"):
            k.s.matn(cx0 - rx * 0.55, cy0 - 40, rx * 1.1, 80, e["sarlavha"], size=22, bold=True, color=u.ink, align="c", va="m",
                     font=u.head, min_scale=0.5, a=k.A("accent", k.qadam))
    else:
        seg = w / n
        for j in range(n):
            pts.append((x + seg * (j + 0.5), y + h * 0.4))
    lw_ = min(240, (w / n) * 0.92) if sh != "aylana" else 220
    for j, b in enumerate(bs):
        st = k.qadam if j == 0 else k.keyingi()
        col = u.acc[j % 4]
        a = k.A("big", st)
        px, py = pts[j]
        if j > 0 or sh == "aylana" and n > 2 and j == 0:
            pass
        if j > 0:
            ox, oy = pts[j - 1]
            _strelka(k, ox, oy, px, py, r, col, a)
        rb = _rasm(k, b.get("rasm"))
        k.s.doira(px, py, r, fill=("#FFFFFF" if u.qorongi else col) if rb else col, op=(0.92 if u.qorongi else 0.14) if rb else 1,
                  line=col if rb else None, lw=2, sh=0 if u.qorongi else 1, a=a)
        if _rasm(k, b.get("rasm")):
            _img(k, b["rasm"], px - r * 0.95, py - r * 0.95, r * 1.9, r * 1.9, a)
        else:
            k.s.matn(px - r, py - r, 2 * r, 2 * r, str(j + 1), size=r * 0.75, bold=True, color=u.matn_ustida(col), align="c", va="m", a=a)
        ly = py + r + 6
        nsz = 19 if sh != "aylana" else 16
        k.s.matn(px - lw_ / 2, ly, lw_, nsz * 1.4, b.get("nom") or "", size=nsz, bold=True, color=u.ink, align="c", min_scale=0.5, a=a)
        if b.get("matn"):
            mh = (y + h - ly - 30) if sh != "aylana" else 54
            k.s.matn(px - lw_ / 2, ly + nsz * 1.45, lw_, max(30, mh), b["matn"], size=16 if sh != "aylana" else 13.5, color=u.ink,
                     align="c", min_scale=0.55, a=a)
    if sh == "aylana" and n > 2:
        ox, oy = pts[-1]
        px, py = pts[0]
        _strelka(k, ox, oy, px, py, r, u.acc[(n - 1) % 4], k.A("big", k.qadam, dl=200))


def _strelka(k, x1, y1, x2, y2, r, col, a):
    d = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    k.s.line(x1 + ux * (r + 8), y1 + uy * (r + 8), x2 - ux * (r + 10), y2 - uy * (r + 10), color=col, lw=2.6, arr="end", a=a)


# ------------------------------------------------------------------ xarita
@lru_cache(maxsize=2)
def _xarita(nom):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "malumot", f"xarita_{nom}.json")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _kalit(sv):
    return re.sub(r"[^a-z]", "", (sv or "").lower().replace("‘", "").replace("’", "").replace("'", "").replace("ʻ", ""))


DAVLAT_UZ = {"ozbekiston": "Uzbekistan", "qozogiston": "Kazakhstan", "qirgiziston": "Kyrgyzstan", "tojikiston": "Tajikistan",
             "turkmaniston": "Turkmenistan", "afgoniston": "Afghanistan", "eron": "Iran", "rossiya": "Russia", "xitoy": "China",
             "hindiston": "India", "pokiston": "Pakistan", "turkiya": "Turkey", "mongoliya": "Mongolia", "mogoliston": "Mongolia",
             "yaponiya": "Japan", "koreya": "South Korea", "janubiykoreya": "South Korea", "misr": "Egypt", "germaniya": "Germany",
             "fransiya": "France", "italiya": "Italy", "ispaniya": "Spain", "angliya": "United Kingdom", "buyukbritaniya": "United Kingdom",
             "aqsh": "United States of America", "amerika": "United States of America", "kanada": "Canada", "braziliya": "Brazil",
             "avstraliya": "Australia", "saudiyaarabistoni": "Saudi Arabia", "gretsiya": "Greece", "iroq": "Iraq", "suriya": "Syria",
             "ozarbayjon": "Azerbaijan", "ukraina": "Ukraine", "belarus": "Belarus", "polsha": "Poland", "meksika": "Mexico",
             "argentina": "Argentina", "indoneziya": "Indonesia", "nigeriya": "Nigeria", "efiopiya": "Ethiopia", "jazoir": "Algeria"}


def komp_xarita(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    dunyo = e.get("hudud") == "dunyo"
    d = _xarita("dunyo" if dunyo else "ozbekiston")
    shakllar = d["davlatlar"] if dunyo else d["viloyatlar"]
    if dunyo:
        lo0, lo1, la0, la1 = -170.0, 180.0, -56.0, 78.0
    else:
        lo0, lo1, la0, la1 = 55.9, 73.3, 37.1, 45.65
    kx = math.cos(math.radians((la0 + la1) / 2)) if not dunyo else 1.0
    gw, gh = (lo1 - lo0) * kx, (la1 - la0)
    sc = min(w / gw, (h - 22) / gh)
    ox = x + (w - gw * sc) / 2
    oy = y + (h - 22 - gh * sc) / 2

    def P(lon, lat):
        return ox + (lon - lo0) * kx * sc, oy + (la1 - lat) * sc

    belgi = {_kalit(b) for b in e.get("belgilash") or []}
    belgi |= {_kalit(DAVLAT_UZ.get(b, "")) for b in list(belgi)}
    fill0, fop0, lcol = (u.kart_rang(0), 1.0, u.muted) if not u.qorongi else ("#FFFFFF", 0.14, "#FFFFFF")
    a0 = k.A("diagram", s)
    tanlangan = []
    for sh in shakllar:
        if sh.get("qita") == "Antarctica":
            continue
        kk = _kalit(sh["nom"])
        on = any(b and (b == kk or b in kk or kk in b) for b in belgi) if belgi else False
        if on:
            tanlangan.append(sh)
            continue
        for poly in sh["poly"]:
            if dunyo and min(la for _, la in poly) < la0:
                poly = [(lo, max(la, la0)) for lo, la in poly]
            k.s.path([P(lo, la) for lo, la in poly], fill=fill0, line=lcol, lw=0.6 if dunyo else 0.9, op=fop0, a=a0)
    st = k.keyingi() if tanlangan else s
    for j, sh in enumerate(tanlangan):
        col = u.acc[j % 4]
        for poly in sh["poly"]:
            k.s.path([P(lo, la) for lo, la in poly], fill=col, line=col, lw=1.2, op=0.55, a=k.A("accent", st, dl=j * 120))
    # nuqtalar
    joylar = []
    shaharlar = {_kalit(c["nom"]): c for c in (d.get("shaharlar") or d.get("poytaxtlar") or [])}
    for jy in e.get("joylar") or []:
        lat, lon = jy.get("lat"), jy.get("lon")
        if lat is None or lon is None:
            c = shaharlar.get(_kalit(jy["nom"]))
            if not c:
                continue
            lat, lon = c["lat"], c["lon"]
        if lo0 <= lon <= lo1 and la0 <= lat <= la1:
            joylar.append((jy, lat, lon))
    if joylar:
        st2 = k.keyingi()
        for j, (jy, lat, lon) in enumerate(joylar):
            px, py = P(lon, lat)
            col = u.acc[(j + 1) % 4]
            a = k.A("item", st2, dl=j * 140)
            k.s.doira(px, py, 7, fill=col, line="#FFFFFF", lw=1.5, a=a)
            label = (jy.get("yorliq") or jy["nom"]) + (f" — {jy['matn']}" if jy.get("matn") else "")
            tw = min(260, k.s.olcham(label, 13, bold=True) + 18)
            lx = px + 10 if px + 10 + tw < x + w else px - 10 - tw
            k.s.rect(lx, py - 12, tw, 24, fill="#FFFFFF" if not u.qorongi else u.bg[0], op=0.92, line=col, lw=1, r=12, a=a)
            k.s.matn(lx + 6, py - 12, tw - 12, 24, label, size=13, bold=True, color=u.ink if not u.qorongi else "#FFFFFF",
                     align="c", va="m", min_scale=0.5, a=a)
    k.s.matn(x, y + h - 16, w, 14, d.get("kredit") or "", size=8.5, color=u.muted, align="r", min_scale=0.6, a=a0)


# ------------------------------------------------------------------ o'yinlar
def komp_moslash(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    js = e["juftlar"]
    n = len(js)
    tartib = list(range(n))
    rng = k.rng
    for _ in range(5):
        rng.shuffle(tartib)
        if n < 2 or any(tartib[j] != j for j in range(n)):
            break
    gap = 12
    rh = min(84, (h - gap * (n - 1)) / n)
    top = y + (h - (rh * n + gap * (n - 1))) / 2
    lw_, rw_ = w * 0.36, w * 0.36
    rx = x + w - rw_
    pos_ong = {}
    for pos, jdx in enumerate(tartib):
        ry = top + pos * (rh + gap)
        pos_ong[jdx] = ry
        jj = js[jdx]
        a = k.A("card", s, dl=pos * 60)
        B.kart(k, rx, ry, rw_, rh, pos + 1, a=a)
        if jj.get("rasm") and _rasm(k, jj["rasm"]) and not jj.get("ong"):
            _img(k, jj["rasm"], rx + 10, ry + 4, rw_ - 20, rh - 8, a)
        else:
            if jj.get("rasm") and _rasm(k, jj["rasm"]):
                _img(k, jj["rasm"], rx + 8, ry + 4, rh - 8, rh - 8, a)
                k.s.matn(rx + rh + 4, ry, rw_ - rh - 14, rh, jj["ong"], size=18, color=u.ink, va="m", min_scale=0.5, a=a)
            else:
                k.s.matn(rx + 14, ry, rw_ - 28, rh, jj["ong"], size=18, color=u.ink, align="c", va="m", min_scale=0.5, a=a)
    for j, jj in enumerate(js):
        ly = top + j * (rh + gap)
        col = u.acc[j % 4]
        a = k.A("card", s, dl=j * 60)
        k.s.rect(x, ly, lw_, rh, fill=col, op=0.12 if not u.qorongi else 0.25, line=col, lw=1.4, r=min(14, rh / 2), a=a)
        k.s.matn(x + 14, ly, lw_ - 28, rh, jj["chap"], size=19, bold=True, color=u.ink, align="c", va="m", min_scale=0.5, a=a)
        tg = B.tegish(k, x, ly, lw_, rh)
        ra = {"tr": tg["id"], "e": "wipe", "d": "l", "ms": 450}
        ry = pos_ong[j]
        k.s.line(x + lw_ + 4, ly + rh / 2, rx - 6, ry + rh / 2, color=col, lw=3, arr="end", a=ra)
        k.s.rect(rx - 3, ry - 3, rw_ + 6, rh + 6, fill=None, line=col, lw=2.6, r=min(16, rh / 2), a=ra)


def komp_togri_notogri(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    fs = e["fikrlar"]
    n = len(fs)
    cols = 1 if n <= 3 else 2 if n <= 4 else 3
    rows = (n + cols - 1) // cols
    gap = 16
    cw, ch = (w - gap * (cols - 1)) / cols, (h - gap * (rows - 1)) / rows
    for j, f in enumerate(fs):
        r_, c_ = divmod(j, cols)
        cx, cy = x + c_ * (cw + gap), y + r_ * (ch + gap)
        a = k.A("card", s, dl=j * 70)
        B.kart(k, cx, cy, cw, ch, j, a=a)
        bh = 34
        mh = ch - bh - 24 - (min(60, ch * 0.3) if f.get("izoh") else 0)
        k.s.matn(cx + 18, cy + 12, cw - 36, mh, f["matn"], size=min(21, ch * 0.13 + 6), color=u.ink, va="m", min_scale=0.5, a=a)
        k.s.matn(cx + 18, cy + ch - bh - 10, cw - 36, bh, "To‘g‘rimi? — bosing", size=12.5, italic=True, color=u.muted, align="c",
                 va="m", a=a)
        tg = B.tegish(k, cx, cy, cw, ch)
        col = u.ok if f["javob"] else u.bad
        ra = {"tr": tg["id"], "e": "zoom", "ms": 350}
        k.s.rect(cx + 18, cy + ch - bh - 10, cw - 36, bh, fill=col, r=bh / 2, a=ra)
        k.s.matn(cx + 18, cy + ch - bh - 10, cw - 36, bh, "✓ To‘g‘ri" if f["javob"] else "✗ Noto‘g‘ri", size=15, bold=True,
                 color="#FFFFFF", align="c", va="m", a=ra)
        if f.get("izoh"):
            iz_h = min(60, ch * 0.3)
            k.s.matn(cx + 18, cy + ch - bh - 14 - iz_h, cw - 36, iz_h, f["izoh"], size=13.5, italic=True, color=u.ink, va="b",
                     min_scale=0.5, a=ra)


_BOSH = re.compile(r"_{2,}|…{1,}|\.{3,}|\[\s*\]")


def komp_bosh_joy(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    gs = e["gaplar"]
    n = len(gs)
    gap = 12
    rh = min(82, (h - gap * (n - 1)) / n)
    top = y + (h - (rh * n + gap * (n - 1))) / 2
    for j, g in enumerate(gs):
        ry = top + j * (rh + gap)
        col = u.acc[j % 4]
        a = k.A("item", s, dl=j * 90)
        B.kart(k, x, ry, w, rh, j, a=a)
        B.ikon(k, x + 28, ry + rh / 2, str(j + 1), col, r=14, a=a, solid=True)
        m = _BOSH.search(g["matn"])
        oldin, keyin = (g["matn"][:m.start()], g["matn"][m.end():]) if m else (g["matn"] + " ", "")
        sz = 26 if rh >= 76 else 22 if rh >= 60 else 18
        bw = max(110, k.s.olcham(g["javob"], sz, bold=True) + 34)
        w1, w2 = k.s.olcham(oldin, sz), k.s.olcham(keyin, sz)
        x0 = x + 56
        if w1 + bw + w2 + 20 <= w - 70:
            k.s.matn(x0, ry, w1 + 6, rh, oldin, size=sz, color=u.ink, va="m", a=a)
            bx = x0 + w1 + 6
            by, bh = ry + (rh - sz * 1.6) / 2, sz * 1.6
            k.s.rect(bx, by, bw, bh, fill=None, line=col, lw=1.6, dash=1, r=8, a=a)
            if keyin:
                k.s.matn(bx + bw + 6, ry, w2 + 10, rh, keyin, size=sz, color=u.ink, va="m", a=a)
        else:  # uzun gap: bo'sh joy oxirida
            k.s.matn(x0, ry, w - 70 - bw - 16, rh, g["matn"], size=sz * 0.85, color=u.ink, va="m", min_scale=0.5, a=a)
            bx, bh = x + w - bw - 16, sz * 1.6
            by = ry + (rh - bh) / 2
            k.s.rect(bx, by, bw, bh, fill=None, line=col, lw=1.6, dash=1, r=8, a=a)
        tg = B.tegish(k, bx, by, bw, bh)
        ra = {"tr": tg["id"], "e": "zoom", "ms": 350}
        k.s.rect(bx, by, bw, bh, fill=col, op=0.18 if not u.qorongi else 0.35, line=col, lw=1.6, r=8, a=ra)
        k.s.matn(bx, by, bw, bh, g["javob"], size=sz, bold=True, color=col if not u.qorongi else "#FFFFFF", align="c", va="m",
                 min_scale=0.5, a=ra)


def komp_rasmda_nima(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    lw_ = w * 0.46
    a = k.A("big", s)
    if _rasm(k, e["rasm"]):
        _img(k, e["rasm"], x + 10, y + 10, lw_ - 20, h - 20, a, taglik=True)
    rx, rw = x + lw_ + 20, w - lw_ - 20
    k.s.matn(rx, y + 6, rw, 60, e.get("savol") or "Rasmda nima?", size=24, bold=True, color=u.ink, font=u.head, min_scale=0.55,
             a=k.A("item", s))
    vs = e["variantlar"]
    top = y + 82
    vh = min(74, (h - 92 - 12 * (len(vs) - 1)) / len(vs))
    for vi, v in enumerate(vs):
        vy = top + vi * (vh + 12)
        col = u.acc[vi % 4]
        va = k.A("card", s, dl=vi * 80)
        k.s.rect(rx, vy, rw, vh, fill=col, op=0.1 if not u.qorongi else 0.22, line=col, lw=1.2, r=min(16, vh / 2), a=va)
        k.s.matn(rx + 20, vy, rw - 80, vh, f"{'ABCD'[vi]})  {v}", size=19, color=u.ink, va="m", min_scale=0.5, a=va)
        tg = B.tegish(k, rx, vy, rw, vh)
        ok = vi == e.get("javob", 0)
        mark = {"tr": tg["id"], "e": "zoom", "ms": 350}
        k.s.doira(rx + rw - 32, vy + vh / 2, 14, fill=u.ok if ok else u.bad, a=mark)
        k.s.matn(rx + rw - 46, vy + vh / 2 - 14, 28, 28, "✓" if ok else "✗", size=15, bold=True, color="#FFFFFF", align="c", va="m", a=mark)


# ------------------------------------------------------------------ katta raqamlar (statistika)
def komp_raqamlar(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    bs = e["bandlar"]
    n = len(bs)
    gap = 22
    cw = (w - gap * (n - 1)) / n
    rszs = [min(96, cw * 0.4, 1.9 * (cw - 44) / max(2, len(b["raqam"]))) for b in bs]
    kerak = max(26 + r * 1.25 + (34 if b.get("nom") else 0) + (B.matn_balandligi(b["matn"], cw - 44, size=15) + 8 if b.get("matn") else 0) + 26
                for r, b in zip(rszs, bs))
    ch = min(h, max(200, kerak))
    cy = y + (h - ch) / 2
    for j, b in enumerate(bs):
        st = k.qadam if j == 0 else k.keyingi()
        col = u.acc[j % 4]
        a = k.A("big", st)
        cx = x + j * (cw + gap)
        B.kart(k, cx, cy, cw, ch, j, a=a)
        k.s.rect(cx, cy, 8, ch, fill=col, r=4, a=a)
        rsz = rszs[j]
        k.s.matn(cx + 24, cy + 26, cw - 44, rsz * 1.2, b["raqam"], size=rsz, bold=True, font=u.head, color=col if not u.qorongi else och(col, 0.25),
                 min_scale=0.5, a=a)
        ty = cy + 26 + rsz * 1.25
        if b.get("nom"):
            k.s.matn(cx + 24, ty, cw - 44, 30, b["nom"], size=19, bold=True, color=u.ink, min_scale=0.55, a=a)
            ty += 34
        if b.get("matn"):
            k.s.matn(cx + 24, ty, cw - 44, cy + ch - ty - 18, b["matn"], size=15, color=u.ink, min_scale=0.55, a=k.A("item", st, dl=k.st))


# ------------------------------------------------------------------ iqtibos
def komp_iqtibos(k, e, x, y, w, h, i=0):
    u, s = k.u, k.qadam
    col = u.acc[i % 4]
    portret = _rasm(k, e.get("rasm"))
    pw = min(h * 0.82, w * 0.34) if portret else 0
    if portret:
        pcx, pcy = x + pw / 2 + 10, y + h / 2
        r = pw * 0.5
        k.s.doira(pcx, pcy, r, fill=col if not u.qorongi else "#FFFFFF", op=0.14 if not u.qorongi else 0.9, a=k.A("big", s))
        _img(k, e["rasm"], pcx - r * 0.92, pcy - r * 0.92, r * 1.84, r * 1.84, k.A("big", s))
        kr = RS.kredit(e["rasm"])
        if kr:
            k.s.matn(x, pcy + r + 4, pw + 20, 14, kr, size=8.5, color=u.muted, align="c", min_scale=0.6, a=k.A("big", s))
    tx = x + pw + (50 if portret else 40)
    tw = x + w - tx - 20
    k.s.matn(tx - 34, y + 2, 130, 150, "“", size=120, font="serif", bold=True, color=col, a=k.A("accent", s), min_scale=1)
    qh = h - 110
    sz, _ = B.mos_olcham(e["matn"], tw, qh, sizes=(40, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18), lh=1.28)
    k.s.matn(tx, y + 70, tw, qh, e["matn"], size=sz, font="serif", italic=True, color=u.ink, va="m", lh=1.28, min_scale=0.55,
             a=k.A("item", s, dl=k.st))
    if e.get("muallif"):
        k.s.rect(tx, y + h - 34, 40, 3, fill=col, a=k.A("item", s, dl=2 * k.st))
        k.s.matn(tx + 52, y + h - 46, tw - 52, 26, e["muallif"], size=18, bold=True, color=u.ink, va="m", min_scale=0.6, a=k.A("item", s, dl=2 * k.st))
        if e.get("manba"):
            k.s.matn(tx + 52, y + h - 22, tw - 52, 20, e["manba"], size=13, italic=True, color=u.muted, min_scale=0.6, a=k.A("item", s, dl=2 * k.st))


KOMP_FAN = {
    "lugat": komp_lugat, "dialog": komp_dialog, "parcha": komp_parcha, "vaqt_chizigi": komp_vaqt_chizigi, "xarita": komp_xarita,
    "tajriba": komp_tajriba, "jarayon": komp_jarayon, "galereya": komp_galereya, "guruhlash": komp_guruhlash,
    "moslash": komp_moslash, "togri_notogri": komp_togri_notogri, "bosh_joy": komp_bosh_joy, "rasmda_nima": komp_rasmda_nima,
    "raqamlar": komp_raqamlar, "iqtibos": komp_iqtibos,
}
