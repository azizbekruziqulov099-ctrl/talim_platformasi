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

    def img(self, x, y, w, h, src, fit="contain", a=None, lnk=None, nm=None):
        return self._qosh({"k": "img", "x": x, "y": y, "w": w, "h": h, "src": src, "fit": fit}, a, lnk, nm)

    # ------------------------------------------------------------- matn
    def matn(self, x, y, w, h, matn, size=18, font="sans", color="#222222", bold=False, italic=False, align="l", va="t",
             lh=1.18, min_scale=0.55, a=None, lnk=None, nm=None, sp=None, urg=None, spc=0, bul=None):
        """matn: satr (\\n — yangi paragraf, '• ' — punkt) yoki tayyor paragraflar ro'yxati."""
        if self.tr and isinstance(matn, str):
            matn = self.tr(matn)
        pps = matn if isinstance(matn, list) else pps_qur(matn, size, font, color, bold, italic, align, urg, sp, bul)
        for pp in pps:
            pp.setdefault("al", align)
        scale, qs, th, sigdi = olchov.joyla(pps, w, h, lh=lh, min_scale=min_scale)
        el = {"k": "text", "x": x, "y": y, "w": w, "h": h, "pp": pps, "va": va, "lh": lh, "sc": round(scale, 3), "spc": spc}
        # sayt uchun qatorlar joylashuvi
        if va == "m":
            top = y + (h - th) / 2
        elif va == "b":
            top = y + h - th
        else:
            top = y
        lines = []
        cy = top
        prev_p = None
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
            lines.append({"x": round(lx, 1), "y": round(base, 1), "w": round(q["w"], 1),
                          "bul": q.get("bul"), "bx": round(x, 1),
                          "rs": [{k: v for k, v in dict(r, sz=round(r.get("sz", size) * scale, 2)).items() if k != "urg"} for r in q["rs"]]})
            cy += q["lh"]
        el["ly"] = lines
        el["fit"] = sigdi
        return self._qosh(el, a, lnk, nm)

    def olcham(self, matn, size=18, font="sans", bold=False):
        return olchov.kenglik(matn, font, bold, size * olchov.olcham_k(font, size))

    def json(self):
        return {"fon": self.fon, "els": self.els, "otish": self.otish, "izoh": self.izoh, "qadam": self.qadam_soni, "bolim": self.bolim}
