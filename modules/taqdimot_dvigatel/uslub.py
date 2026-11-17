"""Uslublar: oila (tuzilma, fon, kartalar) × palitra (ranglar) × fon varianti × animatsiya to'plami.

Har bir oila qo'lda sozlangan; palitralar faqat mos keladigan oilaga beriladi (yorug' oilaga yorug' palitra,
qorong'i oilaga qorong'i palitra). Shuning uchun har qanday kombinatsiya chiroyli chiqadi.
Uslub kodi: "oila.palitra.v" (masalan "anor.anor.0").
"""
from __future__ import annotations

import io
import math
import random
from functools import lru_cache

# ------------------------------------------------------------------ ranglar


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(c):
    return "#" + "".join(f"{max(0, min(255, int(round(v)))):02X}" for v in c)


def aralash(a, b, t):
    """a rangdan b rangga t ulush."""
    ca, cb = hex2rgb(a), hex2rgb(b)
    return rgb2hex([ca[i] + (cb[i] - ca[i]) * t for i in range(3)])


def och(c, t):
    return aralash(c, "#FFFFFF", t)


def toq(c, t):
    return aralash(c, "#000000", t)


def yorqinlik(c):
    r, g, b = [v / 255 for v in hex2rgb(c)]
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ustidagi_matn(fon):
    return "#FFFFFF" if yorqinlik(fon) < 0.42 else "#1A1A1A"


# ------------------------------------------------------------------ palitralar
YORUG = {
    "anor": dict(nom="Anor", acc=["#B5173A", "#2A9D8F", "#E76F51", "#457B9D"], ink="#2A1A1F", muted="#7A5C63"),
    "dengiz": dict(nom="Dengiz", acc=["#1D4E89", "#00A6A6", "#F4A259", "#6A4C93"], ink="#14213D", muted="#5C677D"),
    "zumrad": dict(nom="Zumrad", acc=["#1B7F5B", "#D4A017", "#2E86AB", "#C8553D"], ink="#16302B", muted="#5B6B66"),
    "lavanda": dict(nom="Lavanda", acc=["#6A4C93", "#E56399", "#3DA5D9", "#E0A422"], ink="#231942", muted="#6B6385"),
    "apelsin": dict(nom="Apelsin", acc=["#D9530F", "#0F8B8D", "#5E8C3A", "#3D5A80"], ink="#2B2118", muted="#75665A"),
    "osmon": dict(nom="Osmon", acc=["#0077B6", "#F77F00", "#06A77D", "#D62828"], ink="#102A43", muted="#52606D"),
    "olcha": dict(nom="Olcha", acc=["#9D0208", "#386641", "#E09F3E", "#335C67"], ink="#2B1B17", muted="#6F5E58"),
    "yalpiz": dict(nom="Yalpiz", acc=["#21867A", "#264653", "#D9A520", "#E76F51"], ink="#1F2D2E", muted="#5F6F70"),
    "gulsafsar": dict(nom="Gulsafsar", acc=["#7B2CBF", "#1FA79A", "#F28C18", "#E71D36"], ink="#240046", muted="#6C5B7B"),
    "tosh": dict(nom="Tosh", acc=["#3A506B", "#3FA7A5", "#E4572E", "#E0A100"], ink="#1C2541", muted="#5B6475"),
}
QORONGI = {
    "olov": dict(nom="Olov", bg=["#1E1236", "#3B1D5E"], glow="#FB923C", acc=["#FB923C", "#8B5CF6", "#F472B6", "#4ADE80"], ink="#FFFFFF", muted="#D9D0F5"),
    "okean": dict(nom="Okean", bg=["#071A33", "#0B3A5B"], glow="#06B6D4", acc=["#22D3EE", "#F59E0B", "#A78BFA", "#34D399"], ink="#F0F9FF", muted="#BAE6FD"),
    "zumrad_tun": dict(nom="Zumrad tun", bg=["#04241E", "#0B4A40"], glow="#D4A017", acc=["#FACC15", "#34D399", "#60A5FA", "#FB7185"], ink="#ECFDF5", muted="#A7F3D0"),
    "oltin": dict(nom="Qora oltin", bg=["#111114", "#2A2A31"], glow="#F59E0B", acc=["#F59E0B", "#38BDF8", "#F43F5E", "#A3E635"], ink="#FAFAFA", muted="#D4D4D8"),
    "olcha_tun": dict(nom="Olcha tun", bg=["#24080F", "#5A1424"], glow="#FB7185", acc=["#FDBA74", "#FDA4AF", "#93C5FD", "#86EFAC"], ink="#FFF7ED", muted="#FECACA"),
    "kosmik": dict(nom="Kosmik", bg=["#080D24", "#1B2A6B"], glow="#818CF8", acc=["#60A5FA", "#F472B6", "#FDE047", "#4ADE80"], ink="#EEF2FF", muted="#C7D2FE"),
}
DOSKA = {
    "yashil": dict(nom="Yashil doska", bg=["#1E3A2C", "#2B4F3C"], acc=["#FDE68A", "#FCA5A5", "#93C5FD", "#BBF7D0"], ink="#F8FAF5", muted="#CFE3D5"),
    "qora": dict(nom="Qora doska", bg=["#1C1F24", "#2C3138"], acc=["#FDE68A", "#F9A8D4", "#7DD3FC", "#BEF264"], ink="#F5F5F4", muted="#D6D3D1"),
    "kok": dict(nom="Ko'k doska", bg=["#14263F", "#1F3A5C"], acc=["#FDE68A", "#FCA5A5", "#A5F3FC", "#BBF7D0"], ink="#F8FAFC", muted="#CBD5E1"),
}

# ------------------------------------------------------------------ oilalar
# kart: karta ko'rinishi; sarlavha: shrift; fon: fon generatori; mos: qaysi palitralar
OILALAR = {
    "anor": dict(nom="Anor (yumshoq)", turi="yorug", head="serif", fon="aurora", kart=dict(r=14, sh=1, line=None, fill="#FFFFFF", op=1.0), tab="pill"),
    "shisha": dict(nom="Shisha", turi="yorug", head="sans", fon="mesh", kart=dict(r=20, sh=1, line="#FFFFFF", fill="#FFFFFF", op=0.72), tab="pill"),
    "daftar": dict(nom="Daftar", turi="yorug", head="sans", fon="daftar", kart=dict(r=6, sh=0, line="acc", fill="#FFFFFF", op=1.0), tab="bar"),
    "minimal": dict(nom="Minimal", turi="yorug", head="serif", fon="minimal", kart=dict(r=8, sh=0, line=None, fill="tint", op=1.0), tab="bar"),
    "tabiat": dict(nom="Tabiat", turi="yorug", head="serif", fon="barg", kart=dict(r=18, sh=1, line="tint", fill="#FFFDF8", op=1.0), tab="pill"),
    "tun": dict(nom="Tun (yorqin)", turi="qorongi", head="serif", fon="glow", kart=dict(r=12, sh=0, line="#FFFFFF@0.16", fill="#FFFFFF", op=0.08), tab="pill"),
    "yulduz": dict(nom="Yulduzli", turi="qorongi", head="sans", fon="stars", kart=dict(r=16, sh=0, line="acc@0.45", fill="acc", op=0.12), tab="pill"),
    "doska": dict(nom="Sinf doskasi", turi="doska", head="sans", fon="chalk", kart=dict(r=8, sh=0, line="#FFFFFF@0.55", fill="#FFFFFF", op=0.05, dash=1), tab="bar"),
}

ANIMATSIYALAR = {
    # rol → (effekt, yo'nalish, ms)
    "yumshoq": dict(nom="Yumshoq", card=("rise", None, 650), item=("fade", None, 450), diagram=("wipe", "l", 700), accent=("zoom", None, 500), big=("zoom", None, 700), stagger=140),
    "chizgich": dict(nom="Chizg'ich", card=("wipe", "d", 600), item=("wipe", "l", 500), diagram=("wipe", "l", 800), accent=("fade", None, 400), big=("wipe", "u", 700), stagger=120),
    "sakrash": dict(nom="Sakrash", card=("zoom", None, 500), item=("fly", "l", 450), diagram=("zoom", None, 600), accent=("zoom", None, 450), big=("zoom", None, 650), stagger=110),
    "uchish": dict(nom="Uchib kirish", card=("fly", "u", 600), item=("fly", "l", 500), diagram=("wipe", "l", 700), accent=("zoom", None, 450), big=("fly", "r", 700), stagger=150),
    "sokin": dict(nom="Sokin", card=("fade", None, 600), item=("fade", None, 500), diagram=("fade", None, 700), accent=("fade", None, 500), big=("fade", None, 800), stagger=160),
    "sahna": dict(nom="Sahna", card=("rise", None, 700), item=("wipe", "l", 550), diagram=("wipe", "u", 800), accent=("zoom", None, 500), big=("wedge", None, 900), stagger=200),
    "tezkor": dict(nom="Tezkor", card=("zoom", None, 350), item=("fade", None, 300), diagram=("wipe", "l", 450), accent=("zoom", None, 300), big=("zoom", None, 450), stagger=80),
    "tolqin": dict(nom="To'lqin", card=("fly", "d", 650), item=("rise", None, 500), diagram=("wipe", "r", 750), accent=("zoom", None, 500), big=("rise", None, 750), stagger=170),
}


def mos_palitralar(oila):
    t = OILALAR[oila]["turi"]
    return list(YORUG) if t == "yorug" else list(QORONGI) if t == "qorongi" else list(DOSKA)


def barcha_uslublar():
    out = []
    for o in OILALAR:
        for p in mos_palitralar(o):
            out.append(f"{o}.{p}")
    return out


def uslublar_soni():
    return len(barcha_uslublar()) * 3 * len(ANIMATSIYALAR)


class Uslub:
    """Bloklar ishlatadigan tayyor qiymatlar."""

    def __init__(self, kod: str, anim: str | None = None):
        qism = (kod or "anor.anor.0").split(".")
        oila = qism[0] if qism[0] in OILALAR else "anor"
        pal = qism[1] if len(qism) > 1 and qism[1] in mos_palitralar(oila) else mos_palitralar(oila)[0]
        v = int(qism[2]) if len(qism) > 2 and qism[2].isdigit() else 0
        self.oila, self.pal_nom, self.v = oila, pal, v % 3
        self.kod = f"{oila}.{pal}.{self.v}"
        O = OILALAR[oila]
        t = O["turi"]
        P = (YORUG if t == "yorug" else QORONGI if t == "qorongi" else DOSKA)[pal]
        self.qorongi = t != "yorug"
        self.head = O["head"]
        self.acc = list(P["acc"])
        self.ink = P["ink"]
        self.muted = P["muted"]
        self.bg = P.get("bg", [och(self.acc[0], 0.94), "#FFFFFF"])
        self.glow = P.get("glow", self.acc[0])
        self.kart_s = O["kart"]
        self.tab = O["tab"]
        self.fon_turi = O["fon"]
        self.ok = "#22C55E" if self.qorongi else "#1F9D55"
        self.bad = "#F87171" if self.qorongi else "#D62839"
        self.anim_nom = anim if anim in ANIMATSIYALAR else "yumshoq"
        self.anim = ANIMATSIYALAR[self.anim_nom]

    # ---------------------------------------------------- rang yordamchilari
    def tint(self, i=0, t=None):
        """Aksent rangining fonga mos och/yumshoq varianti (karta ichidagi bloklar uchun)."""
        c = self.acc[i % 4]
        if self.qorongi:
            return aralash(self.bg[0], c, 0.28 if t is None else t)
        return och(c, 0.88 if t is None else t)

    def kart_rang(self, i=0):
        f = self.kart_s["fill"]
        if f == "tint":
            return self.tint(i, 0.93) if not self.qorongi else self.tint(i, 0.18)
        if f == "acc":
            return self.acc[i % 4]
        return f

    def kart_chiziq(self, i=0):
        ln = self.kart_s.get("line")
        if not ln:
            return None, 1.0
        op = 1.0
        if "@" in ln:
            ln, o = ln.split("@")
            op = float(o)
        if ln == "acc":
            ln = self.acc[i % 4]
        elif ln == "tint":
            ln = self.tint(i, 0.7)
        return ln, op

    def matn_ustida(self, fon):
        return ustidagi_matn(fon)

    def json(self):
        return {"kod": self.kod, "oila": self.oila, "palitra": self.pal_nom, "qorongi": self.qorongi, "acc": self.acc,
                "ink": self.ink, "muted": self.muted, "anim": self.anim_nom, "head": self.head}


def tanla(rng: random.Random, oila=None, palitra=None, anim=None):
    oilalar = list(OILALAR)
    o = oila if oila in OILALAR else rng.choice(oilalar)
    pals = mos_palitralar(o)
    p = palitra if palitra in pals else rng.choice(pals)
    a = anim if anim in ANIMATSIYALAR else rng.choice(list(ANIMATSIYALAR))
    return Uslub(f"{o}.{p}.{rng.randrange(3)}", a)


# ------------------------------------------------------------------ fon rasmlari (PIL)


def _blob(img, cx, cy, rx, ry, color, alpha, blur):
    from PIL import Image, ImageDraw, ImageFilter
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r, g, b = hex2rgb(color)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(r, g, b, int(255 * alpha)))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)


def _gradient(w, h, c1, c2, angle=90):
    from PIL import Image
    a = hex2rgb(c1)
    b = hex2rgb(c2)
    img = Image.new("RGB", (w, h))
    px = img.load()
    rad = math.radians(angle)
    dx, dy = math.cos(rad), math.sin(rad)
    span = abs(dx) * w + abs(dy) * h
    # tez: chiziqlab chizamiz
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    if abs(dy) >= abs(dx):
        for y in range(h):
            t = y / max(1, h - 1)
            d.line([(0, y), (w, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    else:
        for x in range(w):
            t = x / max(1, w - 1)
            d.line([(x, 0), (x, h)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return img


@lru_cache(maxsize=256)
def fon_rasm(kod: str) -> bytes:
    """Uslub kodi bo'yicha 1280×720 JPEG fon."""
    from PIL import Image, ImageDraw, ImageFilter
    u = Uslub(kod)
    W, H = 1280, 720
    rng = random.Random(kod)
    t = u.fon_turi
    a0, a1, a2 = u.acc[0], u.acc[1], u.acc[2]
    if t == "aurora":
        img = _gradient(W, H, och(a0, 0.93), "#FFFFFF").convert("RGBA")
        corners = [(W * 0.95, -40), (-60, H * 0.25), (W * 0.85, H + 40), (W * 0.2, H + 60)]
        rng.shuffle(corners)
        for (cx, cy), c, al in zip(corners[:3], [a0, a2, a1], [0.22, 0.16, 0.12]):
            _blob(img, cx, cy, rng.randint(320, 460), rng.randint(220, 320), och(c, 0.35), al, 110)
    elif t == "mesh":
        img = _gradient(W, H, och(a1, 0.86), och(a0, 0.86), angle=0).convert("RGBA")
        for _ in range(4):
            _blob(img, rng.randint(0, W), rng.randint(0, H), rng.randint(260, 420), rng.randint(200, 320),
                  och(rng.choice([a0, a1, a2]), 0.4), 0.35, 130)
        _blob(img, W * 0.5, H * 0.5, 700, 380, "#FFFFFF", 0.35, 160)
    elif t == "daftar":
        img = Image.new("RGBA", (W, H), (252, 250, 243, 255))
        d = ImageDraw.Draw(img)
        g = hex2rgb(och(a0, 0.8))
        for x in range(0, W, 28):
            d.line([(x, 0), (x, H)], fill=g + (60,), width=1)
        for y in range(0, H, 28):
            d.line([(0, y), (W, y)], fill=g + (60,), width=1)
        d.line([(34, 0), (34, H)], fill=hex2rgb(a2) + (110,), width=2)
    elif t == "minimal":
        img = Image.new("RGBA", (W, H), (251, 251, 250, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 10, H], fill=hex2rgb(a0) + (255,))
        _blob(img, W + 60, -60, 260, 200, och(a0, 0.6), 0.25, 70)
    elif t == "barg":
        img = _gradient(W, H, "#FBF8EF", och(a0, 0.9)).convert("RGBA")
        for _ in range(7):
            layer = Image.new("RGBA", (420, 180), (0, 0, 0, 0))
            dd = ImageDraw.Draw(layer)
            c = hex2rgb(och(rng.choice([a0, a1]), 0.55))
            dd.ellipse([10, 30, 410, 150], fill=c + (40,))
            layer = layer.rotate(rng.randint(-60, 60), expand=True, resample=Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
            side = rng.choice([0, 1])
            x = rng.randint(-220, 120) if side == 0 else rng.randint(W - 300, W - 60)
            img.alpha_composite(layer, (int(x), rng.randint(-120, H - 100)))
    elif t == "glow":
        img = _gradient(W, H, u.bg[0], u.bg[1], angle=60).convert("RGBA")
        _blob(img, W * 0.92, H * 1.0, 520, 340, u.glow, 0.55, 150)
        _blob(img, W * 0.05, -40, 380, 240, u.acc[1], 0.25, 140)
    elif t == "stars":
        img = _gradient(W, H, u.bg[0], u.bg[1], angle=70).convert("RGBA")
        _blob(img, W * 0.8, H * 0.2, 420, 300, u.glow, 0.22, 150)
        d = ImageDraw.Draw(img)
        for _ in range(170):
            x, y = rng.randint(0, W), rng.randint(0, H)
            r = rng.choice([0.6, 0.8, 1.0, 1.4, 1.8])
            al = rng.randint(70, 220)
            d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, al))
    else:  # chalk
        img = _gradient(W, H, u.bg[0], u.bg[1], angle=90).convert("RGBA")
        noise = Image.effect_noise((W, H), 18).convert("L")
        tex = Image.new("RGBA", (W, H), (255, 255, 255, 0))
        tex.putalpha(noise.point(lambda v: max(0, v - 120) // 6))
        img.alpha_composite(tex)
        for _ in range(5):
            _blob(img, rng.randint(0, W), rng.randint(0, H), rng.randint(200, 380), rng.randint(60, 120), "#FFFFFF", 0.05, 40)
        d = ImageDraw.Draw(img)
        d.rectangle([0, H - 14, W, H], fill=hex2rgb(toq(u.bg[0], 0.25)) + (255,))
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=86, optimize=True, progressive=True)
    return buf.getvalue()
