"""REV194: JONLI KABU — saytdagi robot Kabu (SVG qatlamlari) videoda ham tirik: uchib turadi, qanotlarini qoqadi,
ko'z qisadi, gapirganda og'zidagi chiziqlar ovozga mos sakraydi, salomlashganda qo'l silkitadi, to'g'ri javobda
qo'llarini ko'tarib quvonadi. Qatlamlar bir marta rasmga aylantiriladi (o'lcham bo'yicha kesh), keyin har kadrda
burish/siljitish bilan yig'iladi — tez.
"""
import math
import os
import re
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

DATA = os.path.join(os.path.dirname(__file__), "data")
KW, KH = 320.0, 380.0   # Kabu global koordinatalari (viewBox lar shu tizimda)


@lru_cache(maxsize=1)
def _meta():
    """REV196: Kabu qatlamlari oldindan PNG qilib qo'yilgan (data/kabu) — serverda cairo kerak emas, har doim jonli."""
    import json
    with open(os.path.join(DATA, "kabu", "qatlamlar.json"), encoding="utf-8") as f:
        return json.load(f)


def _markup():
    """Moslik uchun: (defs, {nom: (viewBox, None)})."""
    m = _meta()
    return None, {k: (v, None) for k, v in m["vb"].items()}


@lru_cache(maxsize=64)
def _rasm(nom, s100):
    """Qatlam rasmi kerakli o'lchamda (oldindan tayyorlangan katta PNG'dan kichraytiriladi)."""
    m = _meta()
    im = Image.open(os.path.join(DATA, "kabu", f"{nom}.png")).convert("RGBA")
    vb = m["vb"][nom]
    w, h = max(1, round(vb[2] * s100 / 100)), max(1, round(vb[3] * s100 / 100))
    return im if (im.width, im.height) == (w, h) else im.resize((w, h), Image.LANCZOS)


def _qoy(kanvas, nom, s, burchak=0.0, ox=0.5, oy=0.5, dx=0.0, dy=0.0, sy=1.0):
    """Qatlamni o'z joyiga qo'yish; burchak — (ox, oy) nuqta atrofida (qatlam ichidagi ulush)."""
    _, qatlam = _markup()
    vb = qatlam[nom][0]
    im = _rasm(nom, round(s * 100))
    if sy != 1.0:
        im = im.resize((im.width, max(1, round(im.height * sy))), Image.BILINEAR)
        dy += (vb[3] * s) * (1 - sy) * oy
    x, y = (vb[0] * s) + dx, (vb[1] * s) + dy
    if burchak:
        px, py = im.width * ox, im.height * oy
        r = max(im.width, im.height) * 2
        tmp = Image.new("RGBA", (r, r), (0, 0, 0, 0))
        tmp.alpha_composite(im, (round(r / 2 - px), round(r / 2 - py)))
        tmp = tmp.rotate(burchak, resample=Image.BICUBIC, center=(r / 2, r / 2))
        kanvas.alpha_composite(tmp, (round(x + px - r / 2), round(y + py - r / 2)))
    else:
        kanvas.alpha_composite(im, (round(x), round(y)))


def _koz_qisish(t):
    """Saytdagi k-blink: 5,2 s davr, 45 %, 87,7 %, 91,2 % da ko'z yumiladi."""
    f = (t % 5.2) / 5.2
    for c in (0.45, 0.877, 0.912):
        if abs(f - c) < 0.012:
            return 0.12
    return 1.0


def kadr(balandlik, t, holat="tingla", daraja=0.0, faza=0.0, oyna=False):
    """Bitta Kabu kadri (RGBA). balandlik — px; t — soniya; holat: tingla | gapir | salom | hurra;
    daraja — ovoz balandligi 0..1 (gapir); faza — ikki Kabu bir xil harakat qilmasin; oyna — ko'zgu (o'ng tomondagi)."""
    s = balandlik / KH
    W, H = round(KW * s), round(KH * s) + round(30 * s)
    k = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tt = t + faza
    # alanga (pastda, miltillaydi) va soya
    fl = 0.8 + 0.2 * math.sin(tt * 2 * math.pi / 0.28)
    cx, fy = W / 2, 318 * s
    for rang, kat in (((255, 140, 0, 110), 1.0), ((255, 209, 102, 190), 0.68), ((255, 250, 225, 240), 0.38)):
        q = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rw, rh = 20 * s * kat, 30 * s * kat * fl
        ImageDraw.Draw(q).ellipse((cx - rw, fy, cx + rw, fy + rh * 2), fill=rang)
        k.alpha_composite(q.filter(ImageFilter.GaussianBlur(2.5 * s)))
    # uchish: yuqori-past (3,2 s davr) — butun tana
    ucha = -14 * s * (0.5 - 0.5 * math.cos(tt * 2 * math.pi / 3.2))
    if holat == "hurra":
        ucha += -10 * s * abs(math.sin(tt * 2 * math.pi / 0.8))   # sakraydi
    tana = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # qanotlar (oldin — bosh orqasida)
    qanot_davr = 0.44 if holat == "hurra" else 1.6
    q = math.sin(tt * 2 * math.pi / qanot_davr)
    _qoy(tana, "k-wingL", s, burchak=-(-3.5 + 8.5 * q), ox=0.7869, oy=0.726)
    _qoy(tana, "k-wingR", s, burchak=-(3.5 - 8.5 * q), ox=0.2131, oy=0.726)
    _qoy(tana, "k-body", s)
    _qoy(tana, "k-cstar" if holat == "hurra" else "k-cbook", s)
    # qo'llar
    sway = 4 * math.sin(tt * 2 * math.pi / 6.4)
    if holat == "hurra":
        wig = 9 * math.sin(tt * 2 * math.pi / 0.44)
        chap, ong = 148 + wig, -148 - wig
    elif holat == "salom":
        chap, ong = 16 + sway, -150 + 15 * math.sin(tt * 2 * math.pi / 0.64)
    else:
        chap, ong = 16 + sway, -16 - sway
    _qoy(tana, "k-armL", s, burchak=-chap, ox=0.4545, oy=0.1798)
    _qoy(tana, "k-armR", s, burchak=-ong, ox=0.5455, oy=0.1798)
    # bosh, ko'zlar, og'iz
    bosh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _qoy(bosh, "k-headbase", s)
    if holat in ("hurra", "salom"):
        _qoy(bosh, "k-eyesH", s)
    else:
        _qoy(bosh, "k-eyes", s, sy=_koz_qisish(tt), oy=0.5)
    if holat == "gapir":
        db = ImageDraw.Draw(bosh)
        x0, y0, bw, bh = 139 * s, 146 * s, 42 * s, 20 * s
        for i in range(5):
            tebr = 0.55 + 0.45 * math.sin(tt * 2 * math.pi / (0.26 + 0.04 * i) + i)
            h = max(0.22, min(1.0, daraja * 1.25 * tebr)) * bh
            bx = x0 + bw * (0.2143 * i)
            db.rounded_rectangle((bx, y0 + (bh - h) / 2, bx + bw * 0.1429, y0 + (bh + h) / 2), radius=bw * 0.07, fill=(111, 247, 234, 255))
    else:
        _qoy(bosh, "k-smile", s)
    # antenna nuri (gapirganda tezroq)
    davr = 0.5 if holat == "gapir" else 2.4
    p = 0.5 + 0.5 * math.sin(tt * 2 * math.pi / davr)
    r = 21 * s * (0.75 + 0.45 * p)
    nur = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(nur).ellipse((160 * s - r, 22 * s - r, 160 * s + r, 22 * s + r), fill=(255, 227, 138, round(60 + 120 * p)))
    nur = nur.filter(ImageFilter.GaussianBlur(4 * s))
    tana.alpha_composite(nur)
    tana.alpha_composite(bosh)
    k.alpha_composite(tana, (0, round(ucha)))
    return k.transpose(Image.FLIP_LEFT_RIGHT) if oyna else k
