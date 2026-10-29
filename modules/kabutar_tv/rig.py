"""REV197: KABUTAR RIG — o'zimizning tekin 2D skelet animatsiya dvigateli.

Rassom personajni qatlamlarga bo'lib chizadi (PSD, qatlam nomlari — «Qatlamli personaj» topshirig'idagidek). Dastur:
  1) PSD'ni o'qiydi, qatlamlarni ajratadi, bo'g'imlarni (yelka, tirsak, bilak, bo'yin) qatlam nomi va shaklidan o'zi topadi;
  2) admin bo'g'imlarni muharrirda tuzatishi mumkin (rig.json);
  3) har kadrda personajni «poza»dan chizadi: nafas, ko'z qisish, nigoh, bosh burilishi (parallaks — hajm hissi),
     qosh, qo'llar (yelka → bilak → kaft), kaft holati, tovushga mos og'iz (9 shakl);
  4) tayyor imo-ishoralar: salom, kartaga ko'rsatish, qarash, bosh irg'ash, hayron, kulish, gapirganda qo'l harakati.
"""
import json
import math
import os
import re
import shutil
from functools import lru_cache

from PIL import Image

DATA = os.path.join(os.path.dirname(__file__), "data", "rig")
OGIZLAR = ["X", "A", "B", "C", "D", "E", "F", "G", "H"]
KERAKLI = (["soch_orqa", "oyoqlar", "tana", "boyin", "bosh", "burun", "soch_old"]
           + [f"{a}_{t}" for t in ("chap", "ong") for a in ("yelka", "bilak")] + [f"kaft_{t}_bosh" for t in ("chap", "ong")]
           + [f"{a}_{t}" for t in ("chap", "ong") for a in ("qosh", "koz_oq", "qorachiq", "koz_chiziq", "qovoq")]
           + [f"ogiz_{k}" for k in OGIZLAR])
IXTIYORIY = ["yonoq"] + [f"kaft_{t}_{h}" for t in ("chap", "ong") for h in ("ochiq", "korsat")]


def papkalar():
    yol = [os.path.join(os.environ.get("KABUTAR_TV_DIR") or os.path.join(os.getcwd(), "kabutar_tv_data"), "rig"), DATA]
    return [p for p in yol if p]


def rig_yoli(nom):
    for p in papkalar():
        if os.path.exists(os.path.join(p, nom, "rig.json")):
            return os.path.join(p, nom)
    return None


def rig_bormi(nom):
    return rig_yoli(nom) is not None


# ───────────── PSD import ─────────────
def _toza_nom(n):
    n = str(n or "").strip().lower().replace(" ", "_").replace("-", "_").replace("’", "").replace("'", "")
    n = re.sub(r"[^a-z0-9_]", "", n)
    m = re.fullmatch(r"ogiz_([a-hx])", n)   # og'iz shakllari katta harf bilan: ogiz_A … ogiz_H, ogiz_X
    return f"ogiz_{m.group(1).upper()}" if m else n


def bogimlarni_qoy(suyaklar, bogimlar):
    """Rassom bergan bogimlar.json (joints) → rig suyaklari. Nomlar: yelka_X, tirsak_X, bilak_X, boyin, bosh_markazi."""
    j = (bogimlar or {}).get("joints") or {}
    for tom in ("chap", "ong"):
        if f"yelka_{tom}" in j and f"yelka_{tom}" in suyaklar:
            suyaklar[f"yelka_{tom}"]["nuqta"] = list(map(float, j[f"yelka_{tom}"]))
        if f"tirsak_{tom}" in j and f"bilak_{tom}" in suyaklar:
            suyaklar[f"bilak_{tom}"]["nuqta"] = list(map(float, j[f"tirsak_{tom}"]))
        if f"bilak_{tom}" in j and f"kaft_{tom}" in suyaklar:
            suyaklar[f"kaft_{tom}"]["nuqta"] = list(map(float, j[f"bilak_{tom}"]))
    if "boyin" in j and "bosh" in suyaklar:   # bosh bo'yin ustida buriladi
        suyaklar["bosh"]["nuqta"] = list(map(float, j["boyin"]))
    return suyaklar


def psd_import(psd_yoli, nom, bogimlar=None):
    """PSD → <KABUTAR_TV_DIR>/rig/<nom>/ (qatlam PNG'lari + rig.json). Qaytaradi: (rig, ogohlantirishlar)."""
    from psd_tools import PSDImage
    psd = PSDImage.open(psd_yoli)
    W, H = psd.width, psd.height
    chiqish = os.path.join(papkalar()[0], _toza_nom(nom))
    if os.path.exists(chiqish):
        shutil.rmtree(chiqish)
    os.makedirs(chiqish, exist_ok=True)
    qatlamlar, tartib, ogoh = {}, [], []
    for layer in psd.descendants():
        if layer.is_group():
            continue
        n = _toza_nom(layer.name)
        if not n or n in qatlamlar:
            continue
        # yashirin qatlamlar ham kerak (og'izlar, yumuq ko'z, kaft variantlari) — ko'rinishidan qat'i nazar piksellar olinadi
        try:
            im = layer.topil()
        except Exception:
            im = None
        if im is None:
            try:
                im = layer.composite(force=True)
            except Exception:
                im = None
        if im is None:
            continue
        im = im.convert("RGBA")
        left, top = layer.bbox[0], layer.bbox[1]
        bb = im.getbbox()
        if not bb:
            continue
        im = im.crop(bb)
        left, top = left + bb[0], top + bb[1]
        im.save(os.path.join(chiqish, n + ".png"), optimize=True)
        qatlamlar[n] = {"x": left, "y": top, "w": im.width, "h": im.height}
        tartib.append(n)
    yoq = [k for k in KERAKLI if k not in qatlamlar]
    if yoq:
        ogoh.append("Yetishmayotgan qatlamlar: " + ", ".join(yoq))
    notanish = [k for k in qatlamlar if k not in KERAKLI and k not in IXTIYORIY and k != "nuqtalar"]
    if notanish:
        ogoh.append("Notanish nomli qatlamlar (ishlatilmaydi): " + ", ".join(notanish))
    suyaklar = avto_suyaklar(qatlamlar)
    if bogimlar:
        bogimlarni_qoy(suyaklar, bogimlar)
    rig = {"nom": _toza_nom(nom), "kanvas": [W, H], "qatlamlar": qatlamlar, "tartib": tartib, "suyaklar": suyaklar}
    with open(os.path.join(chiqish, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(rig, f, ensure_ascii=False, indent=1)
    rig_ol.cache_clear()
    return rig, ogoh


def avto_suyaklar(q):
    """Bo'g'imlarni qatlam shaklidan taxmin qilish (admin muharrirda tuzatadi)."""
    def bb(n):
        x = q.get(n)
        return (x["x"], x["y"], x["x"] + x["w"], x["y"] + x["h"]) if x else None
    s = {}
    t = bb("tana") or (0, 0, 1, 1)
    s["tana"] = {"ota": None, "nuqta": [(t[0] + t[2]) / 2, t[1] + (t[3] - t[1]) * 0.55]}
    b = bb("boyin") or (t[0], t[1] - 100, t[2], t[1])
    s["boyin"] = {"ota": "tana", "nuqta": [(b[0] + b[2]) / 2, b[3] - (b[3] - b[1]) * 0.15]}
    s["bosh"] = {"ota": "boyin", "nuqta": [(b[0] + b[2]) / 2, b[1] + (b[3] - b[1]) * 0.25]}
    for tom in ("chap", "ong"):
        y = bb(f"yelka_{tom}")
        if y:
            s[f"yelka_{tom}"] = {"ota": "tana", "nuqta": [(y[0] + y[2]) / 2, y[1] + (y[2] - y[0]) * 0.5]}
        bl = bb(f"bilak_{tom}")
        if bl:
            s[f"bilak_{tom}"] = {"ota": f"yelka_{tom}", "nuqta": [(bl[0] + bl[2]) / 2, bl[1] + (bl[2] - bl[0]) * 0.5]}
        k = bb(f"kaft_{tom}_bosh") or bb(f"kaft_{tom}_ochiq")
        if k:
            s[f"kaft_{tom}"] = {"ota": f"bilak_{tom}", "nuqta": [(k[0] + k[2]) / 2, k[1] + (k[3] - k[1]) * 0.15]}
    return s


@lru_cache(maxsize=16)
def rig_ol(nom):
    p = rig_yoli(nom)
    if not p:
        return None
    with open(os.path.join(p, "rig.json"), encoding="utf-8") as f:
        r = json.load(f)
    r["_yol"] = p
    return r


def rig_saqla(nom, suyaklar):
    p = rig_yoli(nom)
    if not p:
        raise FileNotFoundError(nom)
    with open(os.path.join(p, "rig.json"), encoding="utf-8") as f:
        r = json.load(f)
    for k, v in (suyaklar or {}).items():
        if k in r["suyaklar"] and isinstance(v, dict) and "nuqta" in v:
            r["suyaklar"][k]["nuqta"] = [float(v["nuqta"][0]), float(v["nuqta"][1])]
    with open(os.path.join(p, "rig.json"), "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
    rig_ol.cache_clear()
    _qatlam.cache_clear()
    return r


@lru_cache(maxsize=256)
def _qatlam(nom, qatlam, s1000):
    r = rig_ol(nom)
    q = r["qatlamlar"].get(qatlam)
    if not q:
        return None
    im = Image.open(os.path.join(r["_yol"], qatlam + ".png")).convert("RGBA")
    s = s1000 / 1000.0
    w, h = max(1, round(q["w"] * s)), max(1, round(q["h"] * s))
    return im.resize((w, h), Image.LANCZOS)


# ───────────── chizish ─────────────
def _aylantir_qoy(kanvas, im, joy_xy, pivot_im, burchak, alfa=1.0):
    """im ni pivot_im nuqtasi atrofida burab, kanvasdagi joy_xy nuqtaga (pivot) qo'yadi."""
    if im is None:
        return
    if alfa < 0.999:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda a: int(a * alfa)))
    if abs(burchak) < 0.05:
        kanvas.alpha_composite(im, (round(joy_xy[0] - pivot_im[0]), round(joy_xy[1] - pivot_im[1])))
        return
    r = int(max(im.width, im.height) * 2 + 4)
    tmp = Image.new("RGBA", (r, r), (0, 0, 0, 0))
    tmp.alpha_composite(im, (round(r / 2 - pivot_im[0]), round(r / 2 - pivot_im[1])))
    tmp = tmp.rotate(burchak, resample=Image.BICUBIC, center=(r / 2, r / 2))
    bb = tmp.getbbox()
    if not bb:
        return
    kanvas.alpha_composite(tmp.crop(bb), (round(joy_xy[0] - r / 2 + bb[0]), round(joy_xy[1] - r / 2 + bb[1])))


def _rot(p, c, a):
    """p nuqtani c atrofida a gradusga (PIL yo'nalishida — soat millariga teskari) burish."""
    ar = math.radians(a)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(ar) + dy * math.sin(ar), c[1] - dx * math.sin(ar) + dy * math.cos(ar))


STANDART = {"bosh": 0.0, "yaw": 0.0, "pitch": 0.0, "nigoh": (0.0, 0.0), "koz": 1.0, "qosh": 0.0, "ogiz": "X", "yonoq": 0.0,
            "nafas": 0.0, "yelka_chap": 8.0, "yelka_ong": -8.0, "bilak_chap": 0.0, "bilak_ong": 0.0,
            "kaft_chap": "bosh", "kaft_ong": "bosh", "kaft_chap_b": 0.0, "kaft_ong_b": 0.0}


@lru_cache(maxsize=16)
def mazmun(nom):
    """Personajning o'zi egallagan joy (kanvas koordinatalarida): (x0, y0, x1, y1)."""
    Q = {k: v for k, v in rig_ol(nom)["qatlamlar"].items() if k != "nuqtalar"}
    return (min(q["x"] for q in Q.values()), min(q["y"] for q in Q.values()),
            max(q["x"] + q["w"] for q in Q.values()), max(q["y"] + q["h"] for q in Q.values()))


def joyla(nom, bo_y, poza):
    """Personajni bo'yi bo_y px qilib chizadi. Qaytaradi: (rasm, markaz_x, oyoq_y) — rasm ichidagi koordinatalar."""
    r = rig_ol(nom)
    x0, y0, x1, y1 = mazmun(nom)
    H0 = r["kanvas"][1]
    bal = bo_y * H0 / max(1, (y1 - y0))
    im = chiz(nom, bal, poza)
    s = bal / H0
    pad = round(r["kanvas"][0] * s * 0.35)
    return im, pad + (x0 + x1) / 2 * s, y1 * s


def chiz(nom, balandlik, poza=None):
    """Personaj kadri (RGBA, kanvas proporsiyasida). balandlik — px (kanvas bo'yi shu bo'ladi)."""
    r = rig_ol(nom)
    p = {**STANDART, **(poza or {})}
    W0, H0 = r["kanvas"]
    s = balandlik / H0
    s1000 = round(s * 1000)
    PAD = round(W0 * s * 0.35)   # qo'l yon tomonga cho'zilganda kesilmasin
    W, H = round(W0 * s) + 2 * PAD, round(H0 * s)
    sy = r["suyaklar"]
    pt = lambda n: (sy[n]["nuqta"][0] * s + PAD, sy[n]["nuqta"][1] * s)
    Q = r["qatlamlar"]
    joy = lambda n: (Q[n]["x"] * s + PAD, Q[n]["y"] * s)
    k = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nafas = p["nafas"]
    tana_c = pt("tana")
    # nafas — tana yuqori qismi biroz ko'tariladi (yelka, bo'yin, bosh ham)
    ko = -nafas * 6 * s * (H0 / 3000)

    def qoy(n, dx=0.0, dy=0.0, alfa=1.0):
        im = _qatlam(nom, n, s1000)
        if im is None:
            return
        x, y = joy(n)
        if alfa < 0.999:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda a: int(a * alfa)))
        k.alpha_composite(im, (round(x + dx), round(y + dy)))

    # 1) bosh guruhi alohida kanvasda (burilishi bir martada), parallaks bilan
    bosh_c = pt("bosh")
    bosh_qatlam = [n for n in Q if n in ("bosh", "burun", "yonoq", "soch_old") or n.startswith(("koz_", "qorachiq_", "qovoq_", "qosh_", "ogiz_"))]
    hx0 = min(Q[n]["x"] for n in bosh_qatlam) * s + PAD
    hy0 = min(Q[n]["y"] for n in bosh_qatlam) * s
    hx1 = max(Q[n]["x"] + Q[n]["w"] for n in bosh_qatlam) * s + PAD
    hy1 = max(Q[n]["y"] + Q[n]["h"] for n in bosh_qatlam) * s
    mg = 0.12 * (hx1 - hx0)
    hx0, hy0 = hx0 - mg, hy0 - mg
    boshk = Image.new("RGBA", (round(hx1 - hx0 + 2 * mg), round(hy1 - hy0 + 2 * mg)), (0, 0, 0, 0))
    yaw, pitch = p["yaw"], p["pitch"]
    um = 22 * s * (H0 / 3000)   # parallaks birligi

    def bq(n, dx=0.0, dy=0.0, alfa=1.0, nishon=None):
        im = _qatlam(nom, n, s1000)
        if im is None:
            return
        x, y = joy(n)
        if alfa < 0.999:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda a: int(a * alfa)))
        if nishon is None:
            boshk.alpha_composite(im, (round(x + dx - hx0), round(y + dy - hy0)))
        else:
            nishon.alpha_composite(im, (round(x + dx), round(y + dy)))

    bq("bosh", yaw * um * 0.3, pitch * um * 0.2)
    yuz_dx, yuz_dy = yaw * um, pitch * um
    for t in ("chap", "ong"):
        if p["koz"] > 0.35:
            bq(f"koz_oq_{t}", yuz_dx, yuz_dy)
            # qorachiq — ko'z oqi ichida yuradi (oq qismdan chiqib ketmaydi)
            oq = _qatlam(nom, f"koz_oq_{t}", s1000)
            qr = _qatlam(nom, f"qorachiq_{t}", s1000)
            if oq is not None and qr is not None:
                ox, oy = joy(f"koz_oq_{t}")
                qx, qy = joy(f"qorachiq_{t}")
                gx, gy = p["nigoh"]
                maska = Image.new("RGBA", oq.size, (0, 0, 0, 0))
                maska.alpha_composite(qr, (round(qx - ox + gx * oq.width * 0.22 + yaw * um * 0.2), round(qy - oy + gy * oq.height * 0.18)))
                maska.putalpha(Image.composite(maska.getchannel("A"), Image.new("L", oq.size, 0), oq.getchannel("A")))
                boshk.alpha_composite(maska, (round(ox + yuz_dx - hx0), round(oy + yuz_dy - hy0)))
            bq(f"koz_chiziq_{t}", yuz_dx, yuz_dy)
        else:
            bq(f"qovoq_{t}", yuz_dx, yuz_dy)
        bq(f"qosh_{t}", yuz_dx, yuz_dy - p["qosh"] * 30 * s * (H0 / 3000))
    bq("burun", yuz_dx * 1.15, yuz_dy)
    if p["yonoq"] > 0.01 and "yonoq" in Q:
        bq("yonoq", yuz_dx, yuz_dy, alfa=min(1.0, 0.5 + p["yonoq"]))
    og = f"ogiz_{p['ogiz']}" if f"ogiz_{p['ogiz']}" in Q else "ogiz_X"
    kich = {"D": 0.8, "E": 0.82, "H": 0.85, "C": 0.92}.get(p["ogiz"], 1.0)   # REV199: keng og'izlar yumshoqroq (qo'rqinchli emas)
    if kich < 1.0:
        im = _qatlam(nom, og, s1000)
        if im is not None:
            x, y = joy(og)
            w2, h2 = max(1, round(im.width * kich)), max(1, round(im.height * kich))
            m = im.resize((w2, h2), Image.LANCZOS)
            boshk.alpha_composite(m, (round(x + (im.width - w2) / 2 + yuz_dx - hx0), round(y + (im.height - h2) * 0.35 + yuz_dy - hy0)))
    else:
        bq(og, yuz_dx, yuz_dy)
    bq("soch_old", yaw * um * 0.5, pitch * um * 0.3)

    bosh_burchak = p["bosh"]
    boyin_c = pt("boyin")
    # 2) qatlamlar tartibi: soch_orqa (bosh bilan buriladi) → oyoqlar → tana → bo'yin → qo'llar → bosh
    if "soch_orqa" in Q:
        im = _qatlam(nom, "soch_orqa", s1000)
        x, y = joy("soch_orqa")
        _aylantir_qoy(k, im, (bosh_c[0] - yaw * um * 0.3, bosh_c[1] + ko), (bosh_c[0] - x, bosh_c[1] - y), bosh_burchak)
    qoy("oyoqlar")
    qoy("tana", 0, ko * 0.5)
    qoy("boyin", 0, ko)

    def qol(t):
        if f"yelka_{t}" not in sy:
            return
        y_c = pt(f"yelka_{t}")
        y_c = (y_c[0], y_c[1] + ko)
        a1 = p[f"yelka_{t}"]
        a2 = a1 + p[f"bilak_{t}"]
        a3 = a2 + p[f"kaft_{t}_b"]
        # yelka
        im = _qatlam(nom, f"yelka_{t}", s1000)
        x, y = joy(f"yelka_{t}")
        _aylantir_qoy(k, im, y_c, (pt(f"yelka_{t}")[0] - x, pt(f"yelka_{t}")[1] - y), a1)
        # tirsak — yelka bilan birga buriladi
        if f"bilak_{t}" in sy:
            e0 = pt(f"bilak_{t}")
            e = _rot((e0[0], e0[1] + ko), y_c, a1)
            im = _qatlam(nom, f"bilak_{t}", s1000)
            x, y = joy(f"bilak_{t}")
            _aylantir_qoy(k, im, e, (e0[0] - x, e0[1] - y), a2)
            if f"kaft_{t}" in sy:
                w0 = pt(f"kaft_{t}")
                w1 = _rot((w0[0], w0[1] + ko), y_c, a1)
                w = _rot(w1, e, a2 - a1)
                holat = p[f"kaft_{t}"]
                nomk = f"kaft_{t}_{holat}" if f"kaft_{t}_{holat}" in Q else f"kaft_{t}_bosh"
                im = _qatlam(nom, nomk, s1000)
                if im is not None:
                    x, y = joy(nomk)
                    _aylantir_qoy(k, im, w, (w0[0] - x, w0[1] - y), a3)

    qol("chap")
    qol("ong")
    _aylantir_qoy(k, boshk, (bosh_c[0], bosh_c[1] + ko), (bosh_c[0] - hx0, bosh_c[1] - hy0), bosh_burchak)
    return k


# ───────────── tovush → og'iz shakli ─────────────
_VIS = {}
for harflar, v in (("aаяáàâ", "D"), ("eiéèêëіиыэе", "C"), ("oоёóôö", "E"), ("uуюúùûüw", "F"), ("mbpмбп", "A"),
                   ("fvфв", "G"), ("lл", "H"), ("ʻ'’", "X")):
    for h in harflar:
        _VIS[h] = v


def visema(soz, ulush):
    """So'z ichidagi o'rin (0..1) → og'iz shakli. Unli harflar uzunroq turadi."""
    harflar = [h for h in str(soz).lower() if h.isalpha()]
    if not harflar:
        return "X"
    i = min(len(harflar) - 1, int(ulush * len(harflar)))
    return _VIS.get(harflar[i], "B")


class Silliq:
    """REV199: og'iz har kadrda sakramasin — har shakl kamida 3 kadr turadi, keng shakl (D) faqat baland ovozda."""
    def __init__(self):
        self.joriy, self.qoldi = "X", 0

    def __call__(self, vis, daraja):
        if vis == "D" and daraja < 0.6:
            vis = "C"
        if vis in ("E", "F") and daraja < 0.3:
            vis = "B"
        if self.qoldi > 0 and vis != "X":
            self.qoldi -= 1
            return self.joriy
        if vis != self.joriy:
            self.joriy, self.qoldi = vis, 2
        return self.joriy


# ───────────── imo-ishoralar va hayotiylik ─────────────
def _tebr(t, davr, faza=0.0):
    return math.sin((t + faza) * 2 * math.pi / davr)


TINCH = True   # REV200: qo'l va bosh rasmdagidek turadi (chizilgan rasm buzilmaydi); faqat yuz jonli — ko'z, og'iz, nafas


def poza(t, *, gapir=False, daraja=0.0, ogiz="X", imo=None, imo_t=0.0, qara=0.0, faza=0.0, tomon="chap"):
    if TINCH:
        p = dict(STANDART)
        p.update({"yelka_chap": 0.0, "yelka_ong": 0.0, "bilak_chap": 0.0, "bilak_ong": 0.0})
        p["nafas"] = 0.5 + 0.5 * _tebr(t, 4.0, faza)
        sak = math.floor((t + faza) / 2.6)
        p["nigoh"] = (0.25 * qara + 0.04 * math.sin(sak * 2.1), 0.0)
        davr = 4.3 + (faza % 1.0)
        p["koz"] = 0.0 if ((t + faza) % davr) < 0.12 else 1.0
        p["ogiz"] = ogiz if gapir else "X"
        if imo == "kul":
            p["yonoq"] = 0.8
        return p
    """Kadr pozasi. t — umumiy vaqt; imo — salom | korsat | irgash | hayron | kul | None; imo_t — imo boshlanganidan beri;
    qara — boshqa ustozga qarash (-1 chap … +1 o'ng); tomon — kartaga qaysi qo'l bilan ko'rsatadi."""
    p = dict(STANDART)
    p["nafas"] = 0.5 + 0.5 * _tebr(t, 3.6, faza)
    # REV199: yumshoqroq — yuz «sirpanmaydi», ko'z «aylanmaydi», bosh sekin
    p["bosh"] = 1.0 * _tebr(t, 6.1, faza) + (0.9 * daraja * _tebr(t, 1.6, faza) if gapir else 0)
    p["yaw"] = 0.06 * _tebr(t, 9.3, faza) + 0.35 * qara
    p["pitch"] = (0.1 * daraja * _tebr(t, 1.1, faza)) if gapir else 0.04 * _tebr(t, 6.0, faza)
    sak = math.floor((t + faza) / 2.3)                                   # nigoh — qisqa sakrash va to'xtash (tabiiy)
    p["nigoh"] = (0.3 * qara + 0.06 * math.sin(sak * 2.1), 0.03 * math.sin(sak * 1.3))
    davr = 4.3 + (faza % 1.0)
    p["koz"] = 0.0 if ((t + faza) % davr) < 0.13 else 1.0
    p["qosh"] = (0.08 * daraja if gapir else 0.0)
    p["ogiz"] = ogiz if gapir else "X"
    p["yelka_chap"] = 8 + 2 * _tebr(t, 4.4, faza)
    p["yelka_ong"] = -8 - 2 * _tebr(t, 4.7, faza)
    if gapir:   # gapirganda qo'llar ham «gapiradi» — sekin va kichik
        p["bilak_chap"] = 6 + 7 * daraja * (0.5 + 0.5 * _tebr(t, 2.2, faza))
        p["bilak_ong"] = -6 - 7 * daraja * (0.5 + 0.5 * _tebr(t, 2.5, faza + 0.4))
    e = min(1.0, imo_t / 0.35) if imo else 0.0   # imoga kirish
    if imo == "salom":
        a = "ong" if tomon == "chap" else "chap"
        sgn = -1 if a == "ong" else 1
        p[f"yelka_{a}"] = sgn * (8 + 140 * e)
        p[f"bilak_{a}"] = sgn * (20 * e + 22 * e * _tebr(imo_t, 0.42))
        p[f"kaft_{a}"] = "ochiq"
        p["yonoq"] = 0.4
        p["qosh"] += 0.2 * e
    elif imo == "korsat":
        a = tomon
        sgn = 1 if a == "chap" else -1
        p[f"yelka_{a}"] = sgn * (8 + 72 * e)
        p[f"bilak_{a}"] = sgn * 28 * e
        p[f"kaft_{a}"] = "korsat"
        p["yaw"] += (0.6 if a == "chap" else -0.6) * e
        p["nigoh"] = ((0.6 if a == "chap" else -0.6) * e, 0.1)
    elif imo == "irgash":
        p["pitch"] = 1.2 * abs(_tebr(imo_t, 0.55)) * (1 if imo_t < 1.2 else 0)
    elif imo == "hayron":
        p["qosh"] = 0.9 * e
        p["ogiz"] = "E" if not gapir else p["ogiz"]
    elif imo == "kul":
        p["yonoq"] = 0.9 * e
        p["qosh"] = 0.35 * e
        p["ogiz"] = "D" if not gapir else p["ogiz"]
        p["bosh"] += 3 * _tebr(imo_t, 0.5) * e
    return p
