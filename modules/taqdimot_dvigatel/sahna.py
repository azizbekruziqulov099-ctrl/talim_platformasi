"""Sahna modeli: bitta taqdimot = slaydlar, slayd = elementlar.

Bir xil sahnadan ikki natija chiqadi: PowerPoint (.pptx) va saytdagi ko'rsatish (SVG). Koordinatalar 1280×720 px
(96 dpi, 1 px = 9525 EMU). Har bir elementda animatsiya ("a") bo'lishi mumkin:
    s  — qadam: 0 = slayd ochilganda o'zi chiqadi, 1.. = har bosishda
    e  — effekt: fade, wipe, zoom, fly, rise, wedge, pulse
    d  — yo'nalish (l, r, u, d), ms — davomiylik, dl — kechikish (shu qadam ichida)
    tr — trigger: shu id'li element bosilganda chiqadi (interaktiv savollar)
"lnk" — bosilganda boshqa slaydga o'tish (slayd raqami, "next", "prev").
"""
from __future__ import annotations

from . import formula as _formula
from . import olchov

W, H = 1280, 720


def pps_qur(matn, size=18, font="sans", color="#222222", bold=False, italic=False, align="l", urg=None, sp=None, bul=None):
    """Belgilangan matndan paragraflar (run'lar bilan)."""
    pps = []
    for qator in str(matn).split("\n"):
        b = bul
        q = qator
        if q.startswith("• "):
            b, q = "•", q[2:]
        kf = olchov.olcham_k(font, size)
        asos = {"sz": size if kf == 1.0 else round(size * kf, 2), "f": font, "c": color}
        if bold:
            asos["b"] = 1
        if italic:
            asos["i"] = 1
        rs = _formula.yugurik(q, **asos)
        for r in rs:
            if r.pop("urg", None) and urg:
                r["c"] = urg
        pps.append({"rs": rs or [dict(asos, t=" ")], "al": align, "sp": size * 0.35 if sp is None else sp, "bul": b})
    return pps


def matn_balandligi(matn, eni, size=18, font="sans", bold=False, lh=1.18, sp=None):
    """Matn qisqarmasdan qancha joy egallashi (px)."""
    pps = pps_qur(matn, size, font, "#000000", bold, False, "l", None, sp, None)
    _sc, _qs, h, _ok = olchov.joyla(pps, eni, 10 ** 6, lh=lh, min_scale=1.0)
    return h


KICHIK_CHEGARA = 13.0     # bundan mayda yorliq bo'lmaydi (manba qatorlari — 9 — bundan mustasno)
OSISH_MIN, OSISH_MAX = 12.0, 21.0   # shu o'lchamdagi asosiy matn bo'sh joy bo'lsa kattalashadi
OSISH_K = 1.6             # eng ko'pi bilan shuncha marta
OSISH_CHEK = 26.0         # kattalashgan matn bundan oshmaydi (sarlavhadan kichik qoladi)


def _qator_joyi(el, qs, scale, th, align, size):
    """Qatorlarning sahifadagi o'rni (sayt uchun) — matn() va matnni_ostir() ishlatadi."""
    x, y, w, h, va, pps = el["x"], el["y"], el["w"], el["h"], el["va"], el["pp"]
    top = y + (h - th) / 2 if va == "m" else y + h - th if va == "b" else y
    lines, cy, prev_p = [], top, None
    for q in qs:
        if prev_p is not None and q["p"] != prev_p:
            cy += pps[prev_p].get("sp", 0) * scale
        prev_p = q["p"]
        al = pps[q["p"]].get("al", align)
        lx = x + q["ind"]
        avail = w - q["ind"]
        if al == "c":
            lx = x + q["ind"] + (avail - q["w"]) / 2
        elif al == "r":
            lx = x + w - q["w"]
        base = cy + (q["lh"] - q["sz"] * 1.22) / 2 + q["sz"] * 0.95
        lines.append({"x": round(lx, 1), "y": round(base, 1), "w": round(q["w"], 1), "bul": q.get("bul"), "bx": round(x, 1),
                      "rs": [{k: v for k, v in dict(r, sz=round(r.get("sz", size) * scale, 2)).items() if k != "urg"} for r in q["rs"]]})
        cy += q["lh"]
    return lines


def _balandlik(el, k):
    """Matn k marta kattalashsa egallaydigan balandligi va qatorlari."""
    pps, h, out = el["pp"], 0.0, []
    for pi, pp in enumerate(pps):
        qs = olchov.qatorlar(pp, el["w"], k)
        for q in qs:
            q["lh"] = q["sz"] * el["lh"]
            h += q["lh"]
            q["p"] = pi
        if pi < len(pps) - 1:
            h += pp.get("sp", 0) * k
        out.extend(qs)
    return h, out


def _quti(b):
    if b.get("k") == "line":
        return min(b["x1"], b["x2"]), min(b["y1"], b["y2"]), abs(b["x2"] - b["x1"]), abs(b["y2"] - b["y1"])
    return b["x"], b["y"], b["w"], b["h"]


def matnni_ostir(els):
    """Kartada ko'p bo'sh joy qolsa, asosiy matn kattalashadi (proyektorda uzoqdan o'qilsin). Yonma-yon kartalar
    (bir xil o'lcham va kenglik) bir xil kattalashadi; rasm, chizma yoki boshqa yozuv ustiga chiqilmaydi."""
    nomzod = [e for e in els if e.get("k") == "text" and e.get("_o")]
    if nomzod:
        guruh = {}
        for e in nomzod:
            o = e["_o"]
            x0, x1, y0, y1 = e["x"], e["x"] + e["w"], e["y"], e["y"] + e["h"]
            h_eff, k = e["h"], OSISH_K
            mt = y0 + o["th"] if e["va"] == "t" else y1
            for b in els:
                if b is e:
                    continue
                bx, by, bw, bh = _quti(b)
                if not (bx < x1 - 1 and bx + bw > x0 + 1 and by < y1 - 1 and by + bh > y0 + 1):
                    continue
                if bx <= x0 + 1 and by <= y0 + 1 and bx + bw >= x1 - 1 and by + bh >= y1 - 1:
                    continue   # karta yoki fon — matn uning ichida
                if e["va"] == "t" and by >= mt - 2:
                    h_eff = min(h_eff, by - y0 - 6)          # pastdagi rasm yoki yozuvgacha
                else:
                    k = 1.0                                   # matn ustida/atrofida narsa bor — tegilmaydi
                    break
            if k > 1.0 and o["th"] > 0.66 * h_eff:
                k = 1.0
            while k > 1.0:
                if o["sz"] * k <= OSISH_CHEK:
                    bh, bq = _balandlik(e, k)
                    if bh <= 0.9 * h_eff and max((q["w"] for q in bq), default=0) <= e["w"] + 1:
                        break
                k = round(k - 0.05, 2)
            if k > 1.0:
                # ierarxiya: matn o'z tepasidagi qalin sarlavhasidan katta bo'lib ketmasin
                for b in els:
                    if b is e or b.get("k") != "text" or not b["ly"] or not b["ly"][0]["rs"] or not b["ly"][0]["rs"][0].get("b"):
                        continue
                    if 0 <= y0 - (b["y"] + b["h"]) + 8 <= 26 and b["x"] < x1 - 8 and b["x"] + b["w"] > x0 + 8:
                        hs = max(r.get("sz", 0) for r in b["ly"][0]["rs"])
                        if hs >= o["sz"] * 0.95:
                            k = min(k, hs / o["sz"])
            o["k"] = max(1.0, k)
            guruh.setdefault((round(o["sz"]), round(e["w"] / 12)), []).append(e)
        for g in guruh.values():
            k = min(e["_o"]["k"] for e in g)
            if k < 1.08:
                continue
            for e in g:
                th, qs = _balandlik(e, k)
                e["sc"] = round(k, 3)
                e["ly"] = _qator_joyi(e, qs, k, th, e["_o"]["al"], e["_o"]["sz"])
    for e in els:
        e.pop("_o", None)


class Slayd:
    def __init__(self, fon=None, otish="fade", izoh=""):
        self.fon = fon or {}
        self.els: list[dict] = []
        self.otish = otish
        self.izoh = izoh
        self._id = 0
        self.qadam_soni = 0
        self.bolim = None
        self.tr = None  # rus/ingliz taqdimotda tayyor yorliqlar tarjimasi (tarjima.py)

    # ------------------------------------------------------------- yordamchi
    def _qosh(self, el, a=None, lnk=None, nm=None):
        self._id += 1
        el["id"] = self._id
        if a:
            el["a"] = dict(a)
            if el["a"].get("s", 0) > self.qadam_soni and not el["a"].get("tr"):
                self.qadam_soni = el["a"]["s"]
        if lnk is not None:
            el["lnk"] = lnk
        if nm:
            el["nm"] = nm
        self.els.append(el)
        return el

    def yangi_qadam(self):
        self.qadam_soni += 1
        return self.qadam_soni

    # ------------------------------------------------------------- shakllar
    def rect(self, x, y, w, h, fill=None, line=None, lw=1.0, r=0, op=1.0, sh=0, dash=0, a=None, lnk=None, nm=None, grad=None):
        el = {"k": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill, "line": line, "lw": lw, "r": r, "op": op, "sh": sh, "dash": dash}
        if grad:
            el["grad"] = grad
        return self._qosh(el, a, lnk, nm)

    def ell(self, x, y, w, h, fill=None, line=None, lw=1.0, op=1.0, sh=0, a=None, lnk=None, nm=None):
        return self._qosh({"k": "ell", "x": x, "y": y, "w": w, "h": h, "fill": fill, "line": line, "lw": lw, "op": op, "sh": sh}, a, lnk, nm)

    def doira(self, cx, cy, r, **kw):
        return self.ell(cx - r, cy - r, 2 * r, 2 * r, **kw)

    def line(self, x1, y1, x2, y2, color="#000000", lw=1.5, dash=0, arr=None, op=1.0, a=None, nm=None):
        return self._qosh({"k": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2, "line": color, "lw": lw, "dash": dash, "arr": arr, "op": op}, a, None, nm)

    def path(self, pts, fill=None, line=None, lw=1.5, closed=True, op=1.0, dash=0, a=None, lnk=None, nm=None):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x, y = min(xs), min(ys)
        w, h = max(max(xs) - x, 0.5), max(max(ys) - y, 0.5)
        return self._qosh({"k": "path", "x": x, "y": y, "w": w, "h": h, "pts": [[round(px, 2), round(py, 2)] for px, py in pts],
                           "z": closed, "fill": fill, "line": line, "lw": lw, "op": op, "dash": dash}, a, lnk, nm)

    def img(self, x, y, w, h, src, fit="contain", a=None, lnk=None, nm=None, shakl=None):
        el = {"k": "img", "x": x, "y": y, "w": w, "h": h, "src": src, "fit": fit}
        if shakl:               # "doira" — rasm doira (ellips) ichida qirqib ko'rsatiladi
            el["shakl"] = shakl
        return self._qosh(el, a, lnk, nm)

    # ------------------------------------------------------------- matn
    def matn(self, x, y, w, h, matn, size=18, font="sans", color="#222222", bold=False, italic=False, align="l", va="t",
             lh=1.18, min_scale=0.55, a=None, lnk=None, nm=None, sp=None, urg=None, spc=0, bul=None, osish=True):
        """matn: satr (\\n — yangi paragraf, '• ' — punkt) yoki tayyor paragraflar ro'yxati.
        osish=False — bo'sh joy qolsa ham matn kattalashtirilmaydi (yorliq, manba qatori)."""
        if self.tr and isinstance(matn, str):
            matn = self.tr(matn)
        if 9.5 <= size < KICHIK_CHEGARA:   # proyektorda o'qilmaydigan mayda yorliqlar (10–11) — kamida 12
            size = KICHIK_CHEGARA
        pps = matn if isinstance(matn, list) else pps_qur(matn, size, font, color, bold, italic, align, urg, sp, bul)
        for pp in pps:
            pp.setdefault("al", align)
        scale, qs, th, sigdi = olchov.joyla(pps, w, h, lh=lh, min_scale=min_scale)
        el = {"k": "text", "x": x, "y": y, "w": w, "h": h, "pp": pps, "va": va, "lh": lh, "sc": round(scale, 3), "spc": spc}
        eng = max((q["w"] for q in qs), default=0)
        if eng > w + 1 and w > 40:   # bo'linmaydigan uzun so'z (havola) qutidan chiqib ketmasin
            scale = max(0.5, scale * w / eng * 0.98)
            el["sc"] = round(scale, 3)
            th, qs = _balandlik(el, scale)
        el["ly"] = _qator_joyi(el, qs, scale, th, align, size)
        el["fit"] = sigdi
        if osish and sigdi and scale >= 0.999 and not spc and OSISH_MIN <= size <= OSISH_MAX and not (nm or "").startswith("!!"):
            el["_o"] = {"sz": size, "th": th, "al": align}   # json() da olib tashlanadi
        return self._qosh(el, a, lnk, nm)

    def olcham(self, matn, size=18, font="sans", bold=False):
        if 9.5 <= size < KICHIK_CHEGARA:   # matn() bilan bir xil: yorliq eni kattalashgan yozuvga mos
            size = KICHIK_CHEGARA
        return olchov.kenglik(matn, font, bold, size * olchov.olcham_k(font, size))

    def json(self):
        matnni_ostir(self.els)
        return {"fon": self.fon, "els": self.els, "otish": self.otish, "izoh": self.izoh, "qadam": self.qadam_soni, "bolim": self.bolim}
