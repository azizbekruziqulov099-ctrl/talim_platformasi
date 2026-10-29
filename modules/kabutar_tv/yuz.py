"""REV201: USTOZ YUZI — rassom chizgan butun rasm buzilmaydi; faqat yuz jonlanadi.

Har ustozda 4 ta butun rasm: tik (oddiy), salom (qo'l silkitadi), korsat (ko'rsatadi), yaqin (yaqin plan).
Yuz nuqtalari (68 ta: ko'z, og'iz, iyak) oldindan aniqlangan (yuz.json). Har kadrda:
  • og'iz — gapga mos, juda yumshoq ochiladi (pastki lab va iyak bir-ikki piksel pastga tushadi, ichi qorayadi);
  • ko'z — 4–5 soniyada bir yumiladi (yarim → yopiq → yarim, ko'z atrofidagi teri rangi bilan);
  • nafas — butun rasm sezilar-sezilmas tebranadi.
Holatlar keshlanadi (poza × og'iz × ko'z), shuning uchun tez.
"""
import json
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

DATA = os.path.join(os.path.dirname(__file__), "data", "ustozlar")
POZALAR = ("tik", "salom", "korsat", "yaqin")


@lru_cache(maxsize=32)
def meta(nom):
    p = os.path.join(DATA, nom, "yuz.json")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def bormi(nom, poza="tik"):
    m = meta(nom)
    return bool(m and poza in m)


@lru_cache(maxsize=48)
def _asl(nom, poza):
    return Image.open(os.path.join(DATA, nom, poza + ".png")).convert("RGBA")


def _teri(a, lm, ko):
    """Ko'z ostidagi teri rangi (ko'z yumilganda qovoq shu rangda)."""
    pts = lm[ko]
    x0, x1 = int(pts[:, 0].min()), int(pts[:, 0].max())
    yb = int(pts[:, 1].max())
    eh = max(2, int(pts[:, 1].max() - pts[:, 1].min()))
    band = a[yb + eh // 2: yb + eh * 2, x0:x1, :3].reshape(-1, 3)
    band = band[a[yb + eh // 2: yb + eh * 2, x0:x1, 3].reshape(-1) > 200]
    if len(band) == 0:
        return (230, 180, 150)
    return tuple(int(v) for v in np.median(band, axis=0))


def _koz_yum(im, lm, yumuq):
    """yumuq: 0.5 — yarim, 1 — to'liq yopiq. Ko'z (kipriklar chizig'i bilan birga) teri rangidagi qovoq bilan yopiladi,
    ustiga yopiq ko'z chizig'i (pastga egilgan yoy) chiziladi."""
    a = np.array(im)
    qat = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(qat)
    chiziqlar = Image.new("RGBA", im.size, (0, 0, 0, 0))
    dc = ImageDraw.Draw(chiziqlar)
    for ko in (list(range(36, 42)), list(range(42, 48))):
        pts = lm[ko]
        x0, x1 = pts[:, 0].min(), pts[:, 0].max()
        y0, y1 = pts[:, 1].min(), pts[:, 1].max()
        ew, eh = x1 - x0, max(3.0, y1 - y0)
        cx = (x0 + x1) / 2
        teri = _teri(a, lm, ko)
        # qovoq: ko'zdan kengroq va yuqoriroq (rassom chizgan kiprik chizig'ini ham yopadi)
        top = y0 - eh * 1.0
        if yumuq >= 1:
            pastki = y1 + eh * 0.35
            d.ellipse((x0 - ew * 0.16, top, x1 + ew * 0.16, pastki), fill=teri + (255,))
            yy = y0 + eh * 0.65
            dc.arc((x0 - ew * 0.05, yy - eh * 0.9, x1 + ew * 0.05, yy + eh * 0.55), 20, 160, fill=(50, 32, 32, 255), width=max(2, int(eh * 0.28)))
        else:
            orta = y0 + eh * 0.45
            d.rectangle((x0 - ew * 0.16, top, x1 + ew * 0.16, orta), fill=teri + (255,))
            d.ellipse((x0 - ew * 0.16, top - eh * 0.6, x1 + ew * 0.16, orta + eh * 0.25), fill=teri + (255,))
            dc.line([(x0, orta + eh * 0.15), (cx, orta + eh * 0.05), (x1, orta + eh * 0.15)], fill=(50, 32, 32, 255), width=max(2, int(eh * 0.24)), joint="curve")
    qat = qat.filter(ImageFilter.GaussianBlur(float(max(1.0, (lm[39][0] - lm[36][0]) * 0.06))))
    out = im.copy()
    out.alpha_composite(qat)
    out.alpha_composite(chiziqlar.filter(ImageFilter.GaussianBlur(0.5)))
    return out


def _ogiz_och(im, lm, q):
    """q: 0 yopiq, 1 yarim, 2 ochiq. Pastki lab va iyak biroz pastga tushadi, og'iz ichi qorayadi (juda yumshoq)."""
    if q <= 0:
        return im
    a = np.array(im).astype(np.float32)
    H, W = a.shape[:2]
    yuz_h = lm[8][1] - lm[27][1]                       # burun ko'prigi → iyak
    d = yuz_h * (0.022 if q == 1 else 0.04)            # sezilar-sezilmas
    ym = (lm[62][1] + lm[66][1]) / 2                   # lablar tutashgan chiziq
    mx = (lm[48][0] + lm[54][0]) / 2
    mw = (lm[54][0] - lm[48][0])
    yc = lm[8][1] + yuz_h * 0.12
    x0, x1 = int(max(0, lm[2][0])), int(min(W, lm[14][0]))
    y0, y1 = int(ym), int(min(H, yc + d + 2))
    if x1 <= x0 or y1 <= y0:
        return im
    xs = np.arange(x0, x1)
    ys = np.arange(y0, y1)
    X, Y = np.meshgrid(xs, ys)
    wx = np.exp(-((X - mx) / (mw * 0.95)) ** 2)
    wy = np.clip(1 - (Y - ym) / max(1, (yc - ym)), 0, 1)
    sy = Y - d * wx * wy
    y_lo = np.clip(np.floor(sy).astype(int), 0, H - 1)
    y_hi = np.clip(y_lo + 1, 0, H - 1)
    t = (sy - np.floor(sy))[..., None]
    blok = a[y_lo, X] * (1 - t) + a[y_hi, X] * t
    a[y0:y1, x0:x1] = blok
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    # og'iz ichi: ichki yuqori lab va pastga tushgan ichki pastki lab orasi
    tor = lambda p: (mx + (p[0] - mx) * 0.78, p[1])      # og'iz ichi lablardan torroq — tabiiy
    ichki_yuqori = [tor(lm[i]) for i in (60, 61, 62, 63, 64)]
    ichki_past = [tor((lm[i][0], lm[i][1] + d * 0.9 * np.exp(-((lm[i][0] - mx) / (mw * 0.95)) ** 2))) for i in (64, 65, 66, 67, 60)]
    qat = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(qat).polygon(ichki_yuqori + ichki_past, fill=(110, 45, 50, 200))
    qat = qat.filter(ImageFilter.GaussianBlur(float(max(0.8, mw * 0.03))))
    out.alpha_composite(qat)
    return out


# ───────── REV202: rassom chizgan yuz variantlari (bo'lsa — mukammal; bo'lmasa — dastur o'zi chizadi) ─────────
# Fayl nomlari: <poza>_ogiz_A|B|D|E.png, <poza>_koz_yarim.png, <poza>_koz_yumuq.png — asl rasm bilan bir xil kanvasda.
OGIZ_VARIANT = {"X": None, "A": "A", "B": "B", "C": "B", "G": "B", "H": "B", "D": "D", "E": "E", "F": "E"}


def _variant_yoli(nom, nomi):
    for papka in (os.path.join(os.environ.get("KABUTAR_TV_DIR") or "", "ustozlar", nom), os.path.join(DATA, nom)):
        p = os.path.join(papka, nomi + ".png")
        if papka and os.path.exists(p):
            return p
    return None


@lru_cache(maxsize=128)
def _yamoq(nom, poza, nomi):
    """REV203: rassom variantining o'zgargan qismi (kichik «yamoq») va uning joyi. Yo'q bo'lsa — None."""
    m = meta(nom)[poza]
    joy = (m.get("yamoq") or {}).get(nomi)
    p = _variant_yoli(nom, f"{poza}_{nomi}")
    if joy is None or not p:
        return None
    return Image.open(p).convert("RGBA"), tuple(joy)


def variant_bormi(nom, poza):
    m = meta(nom)
    return bool(m and poza in m and (m[poza].get("yamoq") or {}).get("ogiz_B") is not None and _variant_yoli(nom, f"{poza}_ogiz_B"))


# REV204: yumshoq rejim — og'iz va ko'z o'zgarishi sezilar-sezilmas (rassom yamog'i asl rasm bilan aralashtiriladi)
OGIZ_KUCH = {"A": 1.0, "B": 1.0, "D": 1.0, "E": 1.0}   # aralashtirish «ikki qavat» lab beradi — rassom chizgani o'zi
KOZ_KUCH = {"koz_yarim": 1.0, "koz_yumuq": 1.0}


def _qoy(im, yamoq, kuch):
    """Yamoqni kuch (0..1) bilan qo'yadi: 1 — rassom chizgani to'liq, 0.5 — asl bilan yarmi."""
    patch, joy = yamoq
    if kuch >= 0.999:
        im.paste(patch, joy)
        return
    asl = im.crop((joy[0], joy[1], joy[0] + patch.width, joy[1] + patch.height))
    im.paste(Image.blend(asl, patch, kuch), joy)


@lru_cache(maxsize=512)
def holat_v(nom, poza, ogiz, yumuq10, balandlik):
    """Rassom chizgan og'iz va ko'z bilan kadr. Og'iz (X, A–H) va ko'z (0/5/10) birga bo'lsa — ikkala yamoq qo'yiladi
    (ular yuzning boshqa-boshqa joyida, bir-biriga tegmaydi). Yamoq yo'q holat — dastur o'zi chizadi."""
    m = meta(nom)
    if not m or poza not in m:
        return None
    im = _asl(nom, poza).copy()
    lm = np.array(m[poza]["lm"], dtype=np.float32)
    v = OGIZ_VARIANT.get(ogiz)
    if v:
        y = _yamoq(nom, poza, f"ogiz_{v}")
        if y:
            _qoy(im, y, OGIZ_KUCH.get(v, 0.7))
        else:
            im = _ogiz_och(im, lm, 2 if v in ("D", "E") else 1 if v == "B" else 0)
    if yumuq10:
        nomi = "koz_yumuq" if yumuq10 >= 10 else "koz_yarim"
        y = _yamoq(nom, poza, nomi)
        if y:
            _qoy(im, y, KOZ_KUCH[nomi])
        else:
            im = _koz_yum(im, lm, yumuq10 / 10)
    k = balandlik / im.height
    if abs(k - 1) > 0.01:
        im = im.resize((max(1, round(im.width * k)), balandlik), Image.LANCZOS)
    return im


@lru_cache(maxsize=256)
def holat(nom, poza, q, yumuq10, balandlik):
    """Tayyor kadr (RGBA): poza, og'iz q (0/1/2), ko'z (0, 5, 10 — ochiq/yarim/yopiq), bo'yi balandlik px."""
    m = meta(nom)
    if not m or poza not in m:
        return None
    im = _asl(nom, poza)
    lm = np.array(m[poza]["lm"], dtype=np.float32)
    if q:
        im = _ogiz_och(im, lm, q)
    if yumuq10:
        im = _koz_yum(im, lm, yumuq10 / 10)
    k = balandlik / im.height
    if abs(k - 1) > 0.01:
        im = im.resize((max(1, round(im.width * k)), balandlik), Image.LANCZOS)
    return im


@lru_cache(maxsize=8)
def _koz_jadval(faza100):
    """REV202: odamdek tasodifiy ko'z qisish: 2–6 s oraliq, ba'zan ketma-ket ikki marta. (boshlanish, ikki_martami)"""
    import random as _r
    rr = _r.Random(faza100)
    t, out = rr.uniform(1.0, 3.0), []
    while t < 3600:
        out.append((t, False))
        t += rr.uniform(3.5, 7.0)   # REV204: kamroq va xotirjam
    return out


def koz_holati(t, faza=0.0):
    """Ko'z qisish: yarim (1 kadr) → yopiq (2 kadr) → yarim (1 kadr) ≈ 0,27 s; ikki marta — 0,35 s keyin yana."""
    import bisect
    jad = _koz_jadval(int(faza * 100))
    i = bisect.bisect_right([b for b, _ in jad], t) - 1
    if i < 0:
        return 0
    b, ikki = jad[i]
    for start in ((b, b + 0.35) if ikki else (b,)):
        f = t - start
        if 0 <= f < 0.067 or 0.2 <= f < 0.267:
            return 5
        if 0.067 <= f < 0.2:
            return 10
    return 0


def og_iz_daraja(daraja):
    return 2 if daraja > 0.6 else 1 if daraja > 0.2 else 0
