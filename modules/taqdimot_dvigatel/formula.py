"""Formulalar: kichik TeX to'plami → chiroyli joylashgan matn bo'laklari va chiziqlar.

Kasr (\\frac), daraja/indeks (^ _), ildiz (\\sqrt), \\overline, \\mathbb{N}, \\text{}, yunon harflari,
munosabat va amal belgilari. Noma'lum buyruq xato bermaydi — nomi oddiy matn bo'lib chiqadi (AI yozgan
formulalar ham buzilmaydi). Natija PowerPoint va saytda bir xil ko'rinadi, butun formula bitta animatsiya
qadamida chiqadi.
"""
from __future__ import annotations

import re

from . import olchov

SYM = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε", "varepsilon": "ε", "zeta": "ζ", "eta": "η",
    "theta": "θ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ", "sigma": "σ", "tau": "τ",
    "phi": "φ", "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ",
    "Lambda": "Λ", "Pi": "Π", "Sigma": "Σ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
    "times": "×", "cdot": "·", "div": "÷", "pm": "±", "mp": "∓", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥",
    "ne": "≠", "neq": "≠", "approx": "≈", "equiv": "≡", "sim": "∼", "infty": "∞", "to": "→", "rightarrow": "→",
    "leftarrow": "←", "Rightarrow": "⇒", "Leftarrow": "⇐", "Leftrightarrow": "⇔", "iff": "⇔", "implies": "⇒",
    "in": "∈", "notin": "∉", "ni": "∋", "subset": "⊂", "subseteq": "⊆", "supset": "⊃", "supseteq": "⊇",
    "cup": "∪", "cap": "∩", "emptyset": "∅", "varnothing": "∅", "forall": "∀", "exists": "∃", "neg": "¬",
    "land": "∧", "wedge": "∧", "lor": "∨", "vee": "∨", "setminus": "∖", "angle": "∠", "triangle": "△",
    "perp": "⊥", "parallel": "∥", "circ": "∘", "degree": "°", "ldots": "…", "dots": "…", "cdots": "⋯",
    "prime": "′", "partial": "∂", "nabla": "∇", "sum": "∑", "prod": "∏", "int": "∫", "cong": "≅", "propto": "∝",
    "lt": "<", "gt": ">", "mid": "|", "vert": "|", "langle": "⟨", "rangle": "⟩", "lfloor": "⌊", "rfloor": "⌋",
    "%": "%", "{": "{", "}": "}", "#": "#", "&": "&", "_": "_",
}
BB = {"N": "ℕ", "Z": "ℤ", "Q": "ℚ", "R": "ℝ", "C": "ℂ", "P": "ℙ"}
FUNCS = {"sin", "cos", "tan", "tg", "ctg", "cot", "log", "ln", "lg", "exp", "max", "min", "lim", "EKUB", "EKUK", "arcsin",
         "arccos", "arctg", "sign", "mod", "gcd", "lcm", "det"}
REL = set("=<>≤≥≠≈≡∈∉⊂⊆⊃⊇→←⇒⇐⇔∼≅∝∋⊥∥:")
BIN = set("+−·×÷±∓∪∩∧∨∖∘")
SPACES = {",": 0.17, ":": 0.22, ";": 0.28, " ": 0.25, "quad": 1.0, "qquad": 2.0, "!": -0.1}


# ------------------------------------------------------------------ parser
class _P:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def cmd(self):
        self.i += 1
        if self.i < len(self.s) and not self.s[self.i].isalpha():
            c = self.s[self.i]
            self.i += 1
            return c
        j = self.i
        while j < len(self.s) and self.s[j].isalpha():
            j += 1
        name = self.s[self.i:j]
        self.i = j
        return name

    def group(self):
        """{...} yoki bitta atom."""
        while self.peek() == " ":
            self.i += 1
        if self.peek() == "{":
            self.i += 1
            node = self.seq("}")
            if self.peek() == "}":
                self.i += 1
            return node
        return self.atom()

    def seq(self, end=""):
        items = []
        while self.i < len(self.s):
            c = self.peek()
            if end and c == end:
                break
            if c == "}" and not end:
                self.i += 1
                continue
            if c == "^" or c == "_":
                self.i += 1
                arg = self.group()
                base = items.pop() if items else ("ch", "", False)
                if base[0] == "sup" and c == "_":
                    base = ("subsup", base[1], arg, base[2])
                elif base[0] == "sub" and c == "^":
                    base = ("subsup", base[1], base[2], arg)
                else:
                    base = ("sup" if c == "^" else "sub", base, arg)
                items.append(base)
                continue
            if c == "\\" and self.s.startswith("\\right", self.i) and end == "\\right":
                break
            a = self.atom()
            if a is not None:
                items.append(a)
        return ("seq", items)

    def atom(self):
        c = self.peek()
        if c == "\\":
            name = self.cmd()
            if name in ("frac", "dfrac", "tfrac"):
                return ("frac", self.group(), self.group())
            if name == "sqrt":
                idx = None
                if self.peek() == "[":
                    j = self.s.find("]", self.i)
                    if j > 0:
                        idx = _P(self.s[self.i + 1:j]).seq()
                        self.i = j + 1
                return ("sqrt", self.group(), idx)
            if name in ("overline", "bar"):
                return ("over", self.group())
            if name in ("mathbb", "Bbb"):
                g = self.group()
                txt = _flat(g)
                return ("ch", "".join(BB.get(ch, ch) for ch in txt), False)
            if name in ("text", "mathrm", "textrm", "operatorname", "mbox"):
                g = self.group()
                return ("txt", _flat(g, raw=True))
            if name in ("mathbf", "textbf", "boldsymbol"):
                g = self.group()
                return ("bold", g)
            if name in ("left", "right", "big", "Big", "bigl", "bigr", "Bigl", "Bigr", "displaystyle"):
                if name == "left":
                    op = self._delim()
                    body = self.seq("\\right")
                    cl = ""
                    if self.s.startswith("\\right", self.i):
                        self.i += 6
                        cl = self._delim()
                    return ("paren", op, body, cl)
                if name == "right":
                    self._delim()
                return None
            if name in SPACES:
                return ("sp", SPACES[name])
            if name in FUNCS:
                return ("txt", name)
            if name in SYM:
                return ("ch", SYM[name], False)
            return ("txt", name)
        self.i += 1
        if c == "{":
            node = self.seq("}")
            if self.peek() == "}":
                self.i += 1
            return node
        if c == " ":
            return None
        if c == "-":
            return ("ch", "−", False)
        if c == "*":
            return ("ch", "·", False)
        if c == "'":
            return ("ch", "′", False)
        if c.isalpha() and c.isascii():
            # funksiya nomlari (sin, cos...) harflab emas, yaxlit
            for f in sorted(FUNCS, key=len, reverse=True):
                if self.s.startswith(f, self.i - 1) and (self.i - 1 + len(f) >= len(self.s) or not self.s[self.i - 1 + len(f)].isalpha()):
                    self.i += len(f) - 1
                    return ("txt", f)
            return ("ch", c, True)
        if c.isdigit() or c == "." or c == ",":
            # raqamlar ketma-ketligi
            j = self.i
            while j < len(self.s) and (self.s[j].isdigit() or (self.s[j] in ".," and j + 1 < len(self.s) and self.s[j + 1].isdigit())):
                j += 1
            txt = c + self.s[self.i:j]
            self.i = j
            if txt == ",":
                return ("ch", ",", False)
            return ("ch", txt, False)
        if "α" <= c <= "ω":
            return ("ch", c, True)
        return ("ch", c, False)

    def _delim(self):
        c = self.peek()
        if c == "\\":
            n = self.cmd()
            return {"{": "{", "}": "}", "langle": "⟨", "rangle": "⟩", "vert": "|", "lvert": "|", "rvert": "|", "|": "‖"}.get(n, "")
        self.i += 1
        return "" if c == "." else c


def _flat(node, raw=False):
    if node is None:
        return ""
    k = node[0]
    if k == "seq":
        return "".join(_flat(n, raw) for n in node[1])
    if k in ("ch", "txt"):
        return node[1]
    if k == "sp":
        return " "
    return ""


def parse(tex: str):
    tex = (tex or "").strip()
    for l, r in (("$$", "$$"), ("$", "$"), ("\\(", "\\)"), ("\\[", "\\]")):
        if tex.startswith(l) and tex.endswith(r) and len(tex) > len(l) + len(r):
            tex = tex[len(l):-len(r)]
            break
    return _P(tex).seq()


# ------------------------------------------------------------------ joylashuv
class Box:
    __slots__ = ("w", "asc", "desc", "items")

    def __init__(self, w=0.0, asc=0.0, desc=0.0, items=None):
        self.w, self.asc, self.desc, self.items = w, asc, desc, items or []


def _txt_box(t, size, italic=False, bold=False, upright_font=False):
    w = olchov.kenglik(t, "math", bold, size)
    if italic:
        w += size * 0.03
    return Box(w, size * 0.72, size * 0.24, [("t", 0.0, 0.0, t, size, italic, bold)])


def _shift(items, dx, dy):
    out = []
    for it in items:
        if it[0] == "t":
            out.append(("t", it[1] + dx, it[2] + dy) + it[3:])
        elif it[0] == "l":
            out.append(("l", it[1] + dx, it[2] + dy, it[3] + dx, it[4] + dy, it[5]))
        else:
            out.append(("p", [(x + dx, y + dy) for x, y in it[1]], it[2]))
    return out


def _hcat(boxes):
    x = 0.0
    asc = desc = 0.0
    items = []
    for b in boxes:
        items += _shift(b.items, x, 0)
        x += b.w
        asc = max(asc, b.asc)
        desc = max(desc, b.desc)
    return Box(x, asc, desc, items)


def _lay(node, S, depth=0, bold=False):
    k = node[0]
    if k == "seq":
        boxes = []
        items = node[1]
        for idx, n in enumerate(items):
            b = _lay(n, S, depth, bold)
            if n[0] == "ch" and len(n[1]) == 1 and (n[1] in REL or n[1] in BIN):
                prev_is_op = idx == 0 or (items[idx - 1][0] == "ch" and (items[idx - 1][1] in REL or items[idx - 1][1] in BIN or items[idx - 1][1] in "(["))
                if n[1] in BIN and prev_is_op:
                    boxes.append(b)  # unar minus
                    continue
                gap = S * (0.24 if n[1] in REL else 0.18) * (0.6 if depth > 0 else 1)
                boxes.append(Box(gap, 0, 0))
                boxes.append(b)
                boxes.append(Box(gap, 0, 0))
            elif n[0] == "ch" and n[1] in (",", ";"):
                boxes.append(b)
                boxes.append(Box(S * 0.18, 0, 0))
            elif n[0] == "txt" and idx > 0 and items[idx - 1][0] in ("ch",) and items[idx - 1][2]:
                boxes.append(Box(S * 0.12, 0, 0))
                boxes.append(b)
                boxes.append(Box(S * 0.08, 0, 0))
            else:
                boxes.append(b)
        if not boxes:
            return Box(0, S * 0.72, S * 0.24)
        return _hcat(boxes)
    if k == "ch":
        return _txt_box(node[1], S, italic=node[2] and not bold, bold=bold)
    if k == "txt":
        return _txt_box(node[1], S, italic=False, bold=bold)
    if k == "bold":
        return _lay(node[1], S, depth, True)
    if k == "sp":
        return Box(S * node[1], 0, 0)
    if k in ("sup", "sub", "subsup"):
        base = _lay(node[1], S, depth, bold)
        s2 = S * 0.68
        parts = [base]
        items = list(base.items)
        w = base.w
        asc, desc = base.asc, base.desc
        sup = sub = None
        if k == "sup":
            sup = _lay(node[2], s2, depth + 1, bold)
        elif k == "sub":
            sub = _lay(node[2], s2, depth + 1, bold)
        else:
            sub = _lay(node[2], s2, depth + 1, bold)
            sup = _lay(node[3], s2, depth + 1, bold)
        ex = 0.0
        if sup:
            dy = -max(S * 0.42, base.asc - sup.asc * 0.6)
            items += _shift(sup.items, w + S * 0.03, dy)
            asc = max(asc, -dy + sup.asc)
            ex = max(ex, sup.w)
        if sub:
            dy = S * 0.22
            items += _shift(sub.items, w + S * 0.02, dy)
            desc = max(desc, dy + sub.desc)
            ex = max(ex, sub.w)
        return Box(w + ex + S * 0.05, asc, desc, items)
    if k == "frac":
        s2 = S * (0.92 if depth == 0 else 0.78)
        num = _lay(node[1], s2, depth + 1, bold)
        den = _lay(node[2], s2, depth + 1, bold)
        w = max(num.w, den.w) + S * 0.24
        axis = S * 0.27
        gap = S * 0.10
        lw = max(1.0, S * 0.055)
        items = []
        items += _shift(num.items, (w - num.w) / 2, -axis - gap - num.desc)
        items += _shift(den.items, (w - den.w) / 2, -axis + gap + den.asc)
        items.append(("l", S * 0.06, -axis, w - S * 0.06, -axis, lw))
        box = Box(w + S * 0.08, axis + gap + num.desc + num.asc, -axis + gap + den.asc + den.desc, _shift(items, S * 0.04, 0))
        return box
    if k == "sqrt":
        body = _lay(node[1], S, depth, bold)
        gap = S * 0.12
        top = -(body.asc + gap)
        bot = body.desc
        sw = S * 0.5
        lw = max(1.0, S * 0.055)
        pts = [(0, -S * 0.25), (S * 0.12, -S * 0.32), (S * 0.25, bot), (sw - S * 0.05, top), (sw + body.w + S * 0.08, top)]
        items = [("p", pts, lw)] + _shift(body.items, sw, 0)
        if node[2] is not None:
            idx = _lay(node[2], S * 0.55, depth + 1, bold)
            items += _shift(idx.items, S * 0.02, -S * 0.42)
        return Box(sw + body.w + S * 0.14, -top + lw, bot, items)
    if k == "over":
        body = _lay(node[1], S, depth, bold)
        y = -body.asc - S * 0.06
        lw = max(1.0, S * 0.05)
        return Box(body.w, body.asc + S * 0.1, body.desc, body.items + [("l", 0, y, body.w, y, lw)])
    if k == "paren":
        body = _lay(node[2], S, depth, bold)
        h = body.asc + body.desc
        scale = max(1.0, h / (S * 1.0))
        op, cl = node[1], node[3]
        ps = S * min(scale * 1.15, 2.6)
        boxes = []
        dy = (body.desc - body.asc) / 2 + ps * 0.24 - ps * 0.0
        if op:
            b = _txt_box(op, ps)
            b.items = _shift(b.items, 0, dy + S * 0.24 - ps * 0.24)
            b.asc, b.desc = body.asc, body.desc
            boxes.append(b)
        boxes.append(body)
        if cl:
            b = _txt_box(cl, ps)
            b.items = _shift(b.items, 0, dy + S * 0.24 - ps * 0.24)
            b.asc, b.desc = body.asc, body.desc
            boxes.append(b)
        return _hcat(boxes)
    return Box()


def olcha(tex: str, size: float):
    """Formula o'lchami: (eni, yuqori, past)."""
    b = _lay(parse(tex), size)
    return b.w, b.asc, b.desc


def chiz(s, tex, x, y, w, h, size=28, color="#222222", align="c", a=None, min_scale=0.45, nm=None):
    """Formulani slaydga joylaydi. Hamma bo'laklar bir animatsiya bilan chiqadi."""
    tree = parse(tex)
    sc = 1.0
    while True:
        b = _lay(tree, size * sc)
        if (b.w <= w and b.asc + b.desc <= h) or sc <= min_scale:
            break
        sc = max(min_scale, sc * 0.92)
    bx = x + ((w - b.w) / 2 if align == "c" else (w - b.w) if align == "r" else 0)
    base = y + (h - (b.asc + b.desc)) / 2 + b.asc
    # matn bo'laklarini bir xil asos chizig'ida birlashtiramiz
    texts = sorted([it for it in b.items if it[0] == "t"], key=lambda t: (round(t[2], 1), t[4], t[1]))
    groups = []
    for it in texts:
        if groups:
            g = groups[-1]
            last = g[-1]
            end = last[1] + olchov.kenglik(last[3], "math", last[6], last[4]) + (last[4] * 0.03 if last[5] else 0)
            if abs(last[2] - it[2]) < 0.5 and abs(last[4] - it[4]) < 0.01 and abs(end - it[1]) < 0.8:
                g.append(it)
                continue
        groups.append([it])
    made = []
    for g in groups:
        x0 = bx + g[0][1]
        sz = g[0][4]
        runs = [{"t": it[3], "sz": sz, "f": "math", "c": color, "i": 1 if it[5] else 0, "b": 1 if it[6] else 0} for it in g]
        tw = sum(olchov.kenglik(r["t"], "math", bool(r["b"]), sz) for r in runs) + sz * 0.4
        top = base + g[0][2] - sz * 0.95 - (sz * 1.18 - sz * 1.22) / 2
        made.append(s.matn(x0, top, tw, sz * 1.25, [{"rs": runs, "al": "l", "sp": 0}], size=sz, lh=1.18, min_scale=1.0, a=a))
    for it in b.items:
        if it[0] == "l":
            made.append(s.line(bx + it[1], base + it[2], bx + it[3], base + it[4], color=color, lw=it[5], a=a))
        elif it[0] == "p":
            made.append(s.path([(bx + px, base + py) for px, py in it[1]], line=color, lw=it[2], closed=False, a=a))
    if nm and made:
        made[0]["nm"] = nm
    return {"w": b.w, "h": b.asc + b.desc, "x": bx, "y": base - b.asc, "els": made}


# ------------------------------------------------------------------ matn ichidagi formula ($...$)
def _inline(node, asos, out, italic_ok=True, bl=None):
    k = node[0]
    if k == "seq":
        for n in node[1]:
            _inline(n, asos, out, italic_ok, bl)
    elif k == "ch":
        t = node[1]
        r = dict(asos, t=t, f="math")
        if node[2]:
            r["i"] = 1
        if t in REL or t in BIN:
            r["t"] = f" {t} " if not bl else t
        if bl:
            r["bl"] = bl
        out.append(r)
    elif k == "txt":
        r = dict(asos, t=node[1])
        if bl:
            r["bl"] = bl
        out.append(r)
    elif k == "bold":
        _inline(node[1], dict(asos, b=1), out, italic_ok, bl)
    elif k == "sp":
        out.append(dict(asos, t=" "))
    elif k in ("sup", "sub", "subsup"):
        _inline(node[1], asos, out, italic_ok, bl)
        if k in ("sub", "subsup"):
            _inline(node[2], asos, out, italic_ok, "sub")
        if k == "sup":
            _inline(node[2], asos, out, italic_ok, "sup")
        if k == "subsup":
            _inline(node[3], asos, out, italic_ok, "sup")
    elif k == "frac":
        simple = lambda n: n[0] == "ch" or (n[0] == "seq" and len(n[1]) == 1 and n[1][0][0] == "ch")
        if not simple(node[1]):
            out.append(dict(asos, t="(", f="math"))
        _inline(node[1], asos, out, italic_ok, bl)
        if not simple(node[1]):
            out.append(dict(asos, t=")", f="math"))
        out.append(dict(asos, t="/", f="math"))
        if not simple(node[2]):
            out.append(dict(asos, t="(", f="math"))
        _inline(node[2], asos, out, italic_ok, bl)
        if not simple(node[2]):
            out.append(dict(asos, t=")", f="math"))
    elif k == "sqrt":
        out.append(dict(asos, t="√", f="math"))
        out.append(dict(asos, t="(", f="math"))
        _inline(node[1], asos, out, italic_ok, bl)
        out.append(dict(asos, t=")", f="math"))
    elif k == "over":
        sub = []
        _inline(node[1], asos, sub, italic_ok, bl)
        for r in sub:
            r["t"] = "".join(ch + "̅" for ch in r["t"])
        out.extend(sub)
    elif k == "paren":
        out.append(dict(asos, t=node[1] or "", f="math"))
        _inline(node[2], asos, out, italic_ok, bl)
        out.append(dict(asos, t=node[3] or "", f="math"))


_DOLLAR = re.compile(r"\$([^$]+)\$")


def yugurik(matn: str, **asos):
    """olchov.yugurik + $...$ ichidagi formulalar."""
    if "$" not in matn:
        return olchov.yugurik(matn, **asos)
    out = []
    pos = 0
    for m in _DOLLAR.finditer(matn):
        if m.start() > pos:
            out += olchov.yugurik(matn[pos:m.start()], **asos)
        rs = []
        _inline(parse(m.group(1)), {k: v for k, v in asos.items()}, rs)
        # yonma-yon bo'shliqlarni siqamiz
        for r in rs:
            if r["t"]:
                out.append(r)
        pos = m.end()
    if pos < len(matn):
        out += olchov.yugurik(matn[pos:], **asos)
    return [r for r in out if r.get("t")]
