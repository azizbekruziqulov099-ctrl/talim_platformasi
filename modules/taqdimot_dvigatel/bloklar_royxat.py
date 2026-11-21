"""Ro'yxat (xossalar, bandlar) uchun «aqlli joylashuvlar» — Gamma'dagidek bitta ro'yxat har slaydda boshqa tuzilishda.

Variantlar: kartalar, belgili (ikonli) ro'yxat, katta raqamli ustunlar, zinapoya, piramida, vaqt chizig'i, aylana (sikl),
strelkalar. Bandlar soni, matn uzunligi va joy kengligiga mos keladiganlari nomzod; AI elementga "korinish" yozsa — o'sha,
aks holda taqdimot bo'yi kam ishlatilgani tanlanadi (ketma-ket takrorlanmaydi).
"""
from __future__ import annotations

import math
import re

from . import bloklar as B
from . import formula as FM
from .uslub import och, toq

KENG_KERAK = {"piramida", "sikl"}  # to'liq kenglik kerak (chap sarlavhali joylashuvga sig'maydi)
KORINISHLAR = {
    "kartalar": "bandlar kartalarda (to'r)",
    "ikonli": "belgili ro'yxat: raqam doirasi, nom va izoh qatorlarda",
    "raqamli": "katta raqamli ustunlar (01, 02, 03)",
    "zinapoya": "zinapoya: har keyingi band balandroq (bosqichlar, o'sish)",
    "piramida": "piramida: tepadan pastga kengayadi (darajalar, ierarxiya)",
    "vaqt": "gorizontal vaqt chizig'i (ketma-ketlik, tarix)",
    "sikl": "aylana: bandlar doira bo'ylab (takrorlanuvchi jarayon)",
    "strelka": "strelkalar: chapdan o'ngga bosqichlar",
}


def _uz(b) -> int:
    return len(b.get("matn") or "") + len(b.get("nom") or "")


def nomzodlar(e, w, h) -> list:
    bs = e.get("bandlar") or []
    n = len(bs)
    formula = any(b.get("formula") for b in bs)
    eng = max((_uz(b) for b in bs), default=0)
    nom_max = max((len(b.get("nom") or "") for b in bs), default=0)
    hammasida_nom = all(b.get("nom") for b in bs)
    c = ["kartalar"]
    if 2 <= n <= 6 and w >= 480:
        c.append("ikonli")
    if formula:
        return c
    if 2 <= n <= 4 and w >= 640 and eng <= 200:
        c.append("raqamli")
    if 3 <= n <= 5 and w >= 760 and h >= 360 and eng <= 150:
        c.append("zinapoya")
    if 3 <= n <= 5 and w >= 820 and h >= 360 and nom_max <= 26 and eng <= 170 and hammasida_nom:
        c.append("piramida")
    if 3 <= n <= 6 and w >= 760 and eng <= 130:
        c.append("vaqt")
    if 3 <= n <= 6 and w >= 820 and h >= 430 and eng <= 95 and hammasida_nom:
        c.append("sikl")
    if 3 <= n <= 5 and w >= 760 and nom_max <= 22 and eng <= 150 and hammasida_nom:
        c.append("strelka")
    return c


_PUNKT = re.compile(r"^\s*(?:[•\-–*]|\d+[.)])\s+(.+)$")


def punktlar(matn: str):
    """«• a\n• b\n• c» ko'rinishidagi matn → bandlar [{nom, matn}] (3–6 ta, aks holda None)."""
    qatorlar = [q for q in (matn or "").split("\n") if q.strip()]
    bs = []
    for q in qatorlar:
        m = _PUNKT.match(q)
        if not m:
            return None
        t = m.group(1).strip()
        nom, sep, qolgan = t.partition(":")
        if not sep:
            nom, sep, qolgan = t.partition(" — ")
        nom = nom.replace("**", "").strip()
        if sep and 0 < len(nom) <= 30 and qolgan.strip():
            bs.append({"nom": nom, "matn": qolgan.strip()})
        else:
            bs.append({"nom": "", "matn": t})
    return bs if 3 <= len(bs) <= 6 and all(len(b["matn"]) <= 160 for b in bs) else None


def tanla(k, e, w, h) -> str:
    c = nomzodlar(e, w, h)
    xohish = (e.get("korinish") or "").strip().lower()
    if xohish in c:
        return xohish
    holat = k.deck.setdefault("_royxat", {"oxirgi": None, "sanoq": {}})
    tanlov = [x for x in c if x != holat["oxirgi"]] or c
    eng_kam = min(holat["sanoq"].get(x, 0) for x in tanlov)
    tanlov = [x for x in tanlov if holat["sanoq"].get(x, 0) == eng_kam]
    v = k.rng.choice(tanlov)
    holat["oxirgi"] = v
    holat["sanoq"][v] = holat["sanoq"].get(v, 0) + 1
    return v


def komp_royxat(k, e, x, y, w, h, i=0):
    if not e.get("bandlar"):
        return
    if e.get("sarlavha") and h > 300:
        k.s.matn(x, y, w, 26, e["sarlavha"], size=18, bold=True, color=k.u.ink, a=k.A("item", k.qadam))
        y += 34
        h -= 34
        e = dict(e, sarlavha="")
    v = tanla(k, e, w, h)
    if v == "kartalar":
        return B._komp_xossalar_kartalar(k, e, x, y, w, h, i)
    return {"ikonli": _ikonli, "raqamli": _raqamli, "zinapoya": _zinapoya, "piramida": _piramida, "vaqt": _vaqt,
            "sikl": _sikl, "strelka": _strelka}[v](k, e["bandlar"], x, y, w, h)


def _rang(k, j):
    return k.u.acc[j % 4]


def _fon(k, col):
    return dict(fill=col, op=0.13 if not k.u.qorongi else 0.24)


def _matn(k, b, x, y, w, h, nom_sz=19, sz=(19, 18, 17, 16, 15, 14), a=None, align="l", col=None, nom_rang=None):
    """Nom (qalin) + izoh; joyga sig'diradi. Qaytaradi: ishlatilgan balandlik."""
    u = k.u
    yy = y
    if b.get("nom"):
        # nom tor ustunda 2 qatorga o'tadi (kichrayib ketmasin)
        ns, nh = B.mos_olcham(b["nom"], w * 0.92, nom_sz * 2.7, sizes=tuple(range(nom_sz, nom_sz - 5, -1)), lh=1.15)
        nh = max(nh, ns * 1.3)
        k.s.matn(x, yy, w, nh + 2, b["nom"], size=ns, bold=True, color=nom_rang or u.ink, align=align, lh=1.15, min_scale=0.6, a=a)
        yy += nh + 6
    if b.get("matn"):
        s_, th = B.mos_olcham(b["matn"], w, max(20, y + h - yy), sizes=sz)
        k.s.matn(x, yy, w, max(th + 4, 20), b["matn"], size=s_, color=col or u.ink, align=align, lh=1.2, min_scale=0.6, a=a)
        yy += th + 4
    if b.get("formula"):
        FM.chiz(k.s, b["formula"], x, yy, w, min(56, y + h - yy), size=26, color=u.ink, align="c" if align == "c" else "l", a=a)
        yy += 56
    return yy - y


# --- 1) belgili ro'yxat (qatorlar)
def _ikonli(k, bs, x, y, w, h):
    u, s = k.u, k.qadam
    n = len(bs)
    gap = 10
    # joy ko'p bo'lsa shrift kattaroq (qisqa ro'yxat slaydning yarmida siqilib qolmasin)
    for fs in (24, 22, 20, 18):
        ehtiyoj = [B.matn_balandligi(b.get("matn") or "", w - 110, fs, lh=1.2) + ((fs + 1) * 1.3 + 8 if b.get("nom") else 0)
                   + (56 if b.get("formula") else 0) + 26 for b in bs]
        if sum(ehtiyoj) + 18 * (n - 1) <= h * 0.86:
            gap = 18
            break
    k_ = min(1.0, (h - gap * (n - 1)) / max(1, sum(ehtiyoj)))
    hs = [max(64, e_ * k_) for e_ in ehtiyoj]
    yy = y + max(0, (h - sum(hs) - gap * (n - 1)) / 2)
    for j, b in enumerate(bs):
        col = _rang(k, j)
        dl = j * k.st
        a = k.A("item", s, dl=dl)
        rh = hs[j]
        k.s.doira(x + 28, yy + min(rh / 2, 34), 24, fill=col, a=k.A("accent", s, dl=dl))
        k.s.matn(x + 4, yy + min(rh / 2, 34) - 24, 48, 48, str(j + 1), size=20, bold=True, color=u.matn_ustida(col), align="c", va="m",
                 a=k.A("accent", s, dl=dl))
        _matn(k, b, x + 74, yy + 6, w - 80, rh - 12, nom_sz=min(24, fs + 1), sz=tuple(range(fs, 13, -1)), a=a,
              nom_rang=col if not u.qorongi else och(col, 0.3))
        if j < n - 1:
            k.s.rect(x + 74, yy + rh + gap / 2, w - 74, 1.2, fill=u.muted, op=0.28, a=a)
        yy += rh + gap


# --- 2) katta raqamli ustunlar
def _raqamli(k, bs, x, y, w, h):
    u, s = k.u, k.qadam
    n = len(bs)
    gap = 30
    cw = (w - gap * (n - 1)) / n
    kerak = max(B.matn_balandligi(b.get("matn") or "", cw, 20, lh=1.2) for b in bs) + 160
    ch = min(h, max(220, kerak))
    yy = y + (h - ch) / 2
    for j, b in enumerate(bs):
        col = _rang(k, j)
        dl = j * k.st
        cx = x + j * (cw + gap)
        k.s.matn(cx, yy, cw, 70, f"{j + 1:02d}", size=58, font=u.head, bold=True, color=col if not u.qorongi else och(col, 0.2), a=k.A("big", s, dl=dl))
        k.s.rect(cx, yy + 78, cw, 4, fill=col, r=2, a=k.A("accent", s, dl=dl + 60))
        _matn(k, b, cx, yy + 96, cw, ch - 100, nom_sz=22, sz=(21, 20, 19, 18, 17, 16, 15), a=k.A("item", s, dl=dl + 120))


# --- 3) zinapoya
def _zinapoya(k, bs, x, y, w, h):
    u, s = k.u, k.qadam
    n = len(bs)
    gap = 14
    cw = (w - gap * (n - 1)) / n
    pastki = y + h
    for j, b in enumerate(bs):
        col = _rang(k, j)
        dl = j * k.st
        bh = h * (0.42 + 0.58 * (j + 1) / n)
        bx, by = x + j * (cw + gap), pastki - bh
        a = k.A("card", s, dl=dl)
        k.s.rect(bx, by, cw, bh, r=14, a=a, **_fon(k, col))
        k.s.rect(bx, by, cw, 8, fill=col, r=4, a=a)
        k.s.matn(bx + 16, by + 18, 80, 40, f"{j + 1}", size=30, font=u.head, bold=True, color=col if not u.qorongi else och(col, 0.25), a=a)
        _matn(k, b, bx + 16, by + 64, cw - 32, bh - 76, nom_sz=20, sz=(19, 18, 17, 16, 15, 14), a=k.A("item", s, dl=dl + 100))


# --- 4) piramida
def _piramida(k, bs, x, y, w, h):
    u, s = k.u, k.qadam
    n = len(bs)
    gap = 8
    pw = w * 0.46
    lh = (h - gap * (n - 1)) / n
    cx = x + pw / 2
    for j, b in enumerate(bs):
        col = _rang(k, j)
        dl = j * k.st
        ly = y + j * (lh + gap)
        tw = pw * (0.30 + 0.70 * j / n)
        bw = pw * (0.30 + 0.70 * (j + 1) / n)
        a = k.A("card", s, dl=dl)
        k.s.path([(cx - tw / 2, ly), (cx + tw / 2, ly), (cx + bw / 2, ly + lh), (cx - bw / 2, ly + lh)], fill=col, a=a)
        fg = u.matn_ustida(col)
        # nom trapetsiyaning o'rta kengligiga sig'adi (tepa pog'ona tor) — kerak bo'lsa 2 qator
        ichki = (tw + bw) / 2 - 24
        nom = b.get("nom") or f"{j + 1}"
        ns, nh = B.mos_olcham(nom, ichki * 0.92, lh - 10, sizes=tuple(range(int(min(20, lh * 0.32)), 11, -1)), lh=1.12)
        k.s.matn(cx - ichki / 2, ly, ichki, lh, nom, size=ns, bold=True, color=fg, align="c", va="m", lh=1.12, min_scale=0.6, a=a)
        tx = x + pw + 34
        k.s.rect(cx + bw / 2 + 8, ly + lh / 2, tx - (cx + bw / 2) - 16, 1.4, fill=col, op=0.6, a=k.A("item", s, dl=dl + 80))
        if b.get("matn"):
            sz, th = B.mos_olcham(b["matn"], x + w - tx, lh, sizes=(19, 18, 17, 16, 15, 14))
            k.s.matn(tx, ly, x + w - tx, lh, b["matn"], size=sz, color=u.ink, va="m", lh=1.2, min_scale=0.6, a=k.A("item", s, dl=dl + 120))


# --- 5) vaqt chizig'i (gorizontal)
def _vaqt(k, bs, x, y, w, h):
    u, s = k.u, k.qadam
    n = len(bs)
    cw = w / n

    def olcham(matnlar, ww, hh, sizes, lh=1.2):
        # hamma bandga bitta shrift (bir tekis ko'rinadi)
        for sz in sizes:
            th = max((B.matn_balandligi(t, ww, sz, lh=lh) for t in matnlar if t), default=0)
            if th <= hh:
                return sz, th
        return sizes[-1], hh

    ns, nh = olcham([b.get("nom") or "" for b in bs], (cw - 20) * 0.92, h * 0.34, (26, 24, 22, 20, 19, 18, 17, 16), lh=1.15)
    ms, mh = olcham([b.get("matn") or "" for b in bs], cw - 24, h - nh - 110, (22, 21, 20, 19, 18, 17, 16, 15, 14))
    jami = nh + 40 + 44 + mh
    ly = y + max(0, (h - jami) / 2) + nh + 40
    k.s.rect(x, ly - 2, w, 4, fill=u.muted, op=0.4, r=2, a=k.A("diagram", s))
    for j, b in enumerate(bs):
        col = _rang(k, j)
        dl = j * k.st
        cx = x + cw * (j + 0.5)
        a = k.A("item", s, dl=dl)
        k.s.doira(cx, ly, 16, fill=col, a=k.A("accent", s, dl=dl))
        k.s.doira(cx, ly, 26, fill=None, line=col, lw=1.6, op=0.6, a=k.A("accent", s, dl=dl))
        if b.get("nom"):
            k.s.matn(cx - cw / 2 + 10, ly - 40 - nh, cw - 20, nh + 4, b["nom"], size=ns, bold=True, color=col if not u.qorongi else och(col, 0.3),
                     align="c", va="b", lh=1.15, min_scale=0.6, a=a)
        if b.get("matn"):
            k.s.matn(cx - cw / 2 + 12, ly + 44, cw - 24, mh + 4, b["matn"], size=ms, color=u.ink, align="c", va="t", lh=1.2, min_scale=0.6, a=a)


# --- 6) aylana (sikl)
def _sikl(k, bs, x, y, w, h):
    u, s = k.u, k.qadam
    n = len(bs)
    cx, cy = x + w / 2, y + h / 2
    R = min(h * 0.36, w * 0.2)
    k.s.doira(cx, cy, R, fill=None, line=u.muted, lw=2, op=0.45, a=k.A("diagram", s))
    lw_ = min(300, (w - 2 * R) / 2 - 40)
    for j, b in enumerate(bs):
        col = _rang(k, j)
        dl = j * k.st
        # tepada tugun qolmasin (matni aylana chizig'iga tegadi): yarim qadam buriladi
        ang = -math.pi / 2 + math.pi / n + 2 * math.pi * j / n
        px, py = cx + R * math.cos(ang), cy + R * math.sin(ang)
        a = k.A("item", s, dl=dl)
        k.s.doira(px, py, 30, fill=col, a=k.A("accent", s, dl=dl), sh=0 if u.qorongi else 1)
        k.s.matn(px - 30, py - 30, 60, 60, str(j + 1), size=22, bold=True, color=u.matn_ustida(col), align="c", va="m", a=k.A("accent", s, dl=dl))
        cos = math.cos(ang)
        if abs(cos) < 0.3:  # tepada yoki pastda
            tx, align, tw = px - lw_ / 2 - 60, "c", lw_ + 120
            ty = py - 30 - 92 if math.sin(ang) < 0 else py + 38
            if math.sin(ang) < 0:
                tx, align, tw, ty = px + 44, "l", lw_ + 40, py - 44
        elif cos > 0:
            tx, align, tw, ty = px + 44, "l", min(lw_, x + w - px - 50), py - 44
        else:
            tw = min(lw_, px - x - 50)
            tx, align, ty = px - 44 - tw, "r", py - 44
        _matn(k, b, tx, ty, tw, 92, nom_sz=19, sz=(17, 16, 15, 14, 13), a=a, align=align, nom_rang=col if not u.qorongi else och(col, 0.3))


# --- 7) strelkalar (chevron)
def _strelka(k, bs, x, y, w, h):
    u, s = k.u, k.qadam
    n = len(bs)
    uch = 30
    cw = (w + uch * (n - 1)) / n
    chh = 92
    kerak = max(B.matn_balandligi(b.get("matn") or "", cw - 50, 20, lh=1.2) for b in bs) + chh + 30
    yy = y + max(0, (h - kerak) / 2)
    for j, b in enumerate(bs):
        col = _rang(k, j)
        dl = j * k.st
        bx = x + j * (cw - uch)
        a = k.A("card", s, dl=dl)
        pts = [(bx, yy), (bx + cw - uch, yy), (bx + cw, yy + chh / 2), (bx + cw - uch, yy + chh), (bx, yy + chh)]
        if j:
            pts.append((bx + uch, yy + chh / 2))
        k.s.path(pts, fill=col, a=a)
        k.s.matn(bx + (uch + 12 if j else 18), yy, cw - uch - (uch + 24 if j else 30), chh, b.get("nom") or f"{j + 1}-bosqich", size=20, bold=True,
                 color=u.matn_ustida(col), align="c", va="m", min_scale=0.5, a=a)
        if b.get("matn"):
            sz, th = B.mos_olcham(b["matn"], cw - 50, y + h - yy - chh - 20, sizes=(21, 20, 19, 18, 17, 16, 15, 14))
            k.s.matn(bx + 16, yy + chh + 18, cw - 50, th + 4, b["matn"], size=sz, color=u.ink, align="c", lh=1.2, min_scale=0.6,
                     a=k.A("item", s, dl=dl + 100))
