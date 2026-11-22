"""Sahna → PowerPoint (.pptx).

Hamma narsa PowerPoint'ning o'z obyektlari bilan yoziladi: shakllar, matn, chiziqlar, rasm. Shuning uchun
o'qituvchi istalgan joyini tahrirlay oladi. Animatsiyalar haqiqiy PowerPoint animatsiyalari (bosilganda bittadan
chiqadi), reja kartalari va pastki nuqtalar giperhavola, sarlavhalar slayddan slaydga «Morph» bilan o'tadi.
"""
from __future__ import annotations

import contextvars
import io
from xml.sax.saxutils import escape

from lxml import etree
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Emu

from .olchov import SHRIFTLAR

EMU = 9525
NSMAP = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
         'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
         'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')


def e(v):
    return int(round(v * EMU))


def _col(c):
    return (c or "#000000").lstrip("#").upper()[:6]


def _solid(c, op=1.0):
    if c is None:
        return "<a:noFill/>"
    alpha = "" if op >= 0.999 else f'<a:alpha val="{int(max(0, op) * 100000)}"/>'
    return f'<a:solidFill><a:srgbClr val="{_col(c)}">{alpha}</a:srgbClr></a:solidFill>'


def _grad(g, op=1.0):
    stops = "".join(
        f'<a:gs pos="{int(pos * 100000)}"><a:srgbClr val="{_col(c)}">' + ("" if op >= 0.999 else f'<a:alpha val="{int(op * 100000)}"/>') + "</a:srgbClr></a:gs>"
        for pos, c in g["stops"])
    ang = int(g.get("ang", 90) * 60000)
    return f'<a:gradFill rotWithShape="1"><a:gsLst>{stops}</a:gsLst><a:lin ang="{ang}" scaled="0"/></a:gradFill>'


def _ln(c, lw, dash=0, op=1.0, arr=None):
    if not c:
        return "<a:ln><a:noFill/></a:ln>"
    d = '<a:prstDash val="dash"/>' if dash == 1 else '<a:prstDash val="sysDot"/>' if dash == 2 else ""
    tail = ""
    if arr in ("end", "both"):
        tail += '<a:tailEnd type="triangle" w="med" len="med"/>'
    if arr in ("start", "both"):
        tail = '<a:headEnd type="triangle" w="med" len="med"/>' + tail
    return f'<a:ln w="{e(lw)}" cap="rnd">{_solid(c, op)}{d}<a:round/>{tail}</a:ln>'


def _shadow(sh, qorongi=False):
    if not sh:
        return ""
    return ('<a:effectLst><a:outerShdw blurRad="228600" dist="57150" dir="5400000" algn="t" rotWithShape="0">'
            f'<a:srgbClr val="{"000000" if not qorongi else "000000"}"><a:alpha val="{14000 if sh == 1 else 24000}"/></a:srgbClr>'
            '</a:outerShdw></a:effectLst>')


def _xfrm(x, y, w, h, flipH=False, flipV=False):
    fl = (' flipH="1"' if flipH else "") + (' flipV="1"' if flipV else "")
    return f'<a:xfrm{fl}><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{max(e(w), 1)}" cy="{max(e(h), 1)}"/></a:xfrm>'


def _nv(sid, name, link_xml=""):
    return f'<p:cNvPr id="{sid}" name="{escape(name, {chr(34): "&quot;"})}">{link_xml}</p:cNvPr>'


# ------------------------------------------------------------------ matn
_YUZLAR = contextvars.ContextVar("pptx_shrift_yuzlari", default=None)  # sahna["shriftlar"]: mantiqiy → PowerPoint shrifti


def _run_xml(r, sc):
    font_key = r.get("f", "sans")
    face = (_YUZLAR.get() or {}).get(font_key) or SHRIFTLAR.get(font_key, SHRIFTLAR["sans"])[0]
    sz = int(round(r.get("sz", 16) * sc * 0.75 * 100))
    if r.get("bl"):
        sz = int(sz)  # PowerPoint o'zi kichraytiradi (baseline bilan)
    attrs = f'lang="uz-Latn-UZ" sz="{max(sz, 100)}" b="{1 if r.get("b") else 0}" i="{1 if r.get("i") else 0}" dirty="0"'
    if r.get("bl") == "sup":
        attrs += ' baseline="30000"'
    elif r.get("bl") == "sub":
        attrs += ' baseline="-25000"'
    if r.get("spc"):
        attrs += f' spc="{int(r["spc"])}"'
    t = escape(r["t"])
    return (f'<a:r><a:rPr {attrs}>{_solid(r.get("c", "#222222"))}<a:latin typeface="{face}"/><a:ea typeface="{face}"/>'
            f'<a:cs typeface="{face}"/><a:sym typeface="{face}"/></a:rPr><a:t>{t}</a:t></a:r>')


def _txbody(el):
    sc = el.get("sc", 1.0)
    anchor = {"t": "t", "m": "ctr", "b": "b"}[el.get("va", "t")]
    lh = el.get("lh", 1.18)
    paras = []
    spc = el.get("spc", 0)
    for pp in el["pp"]:
        al = {"l": "l", "c": "ctr", "r": "r"}[pp.get("al", "l")]
        sp_after = pp.get("sp", 0) * sc * 0.75 * 100
        bul = pp.get("bul")
        rs = pp.get("rs") or []
        ppr = f'<a:pPr algn="{al}"'
        bul_xml = "<a:buNone/>"
        if bul:
            from .olchov import kenglik
            bsz = (rs[0].get("sz", 16) if rs else 16) * sc
            ind = kenglik(bul + " ", rs[0].get("f", "sans") if rs else "sans", False, bsz) + 2
            ppr += f' marL="{e(ind)}" indent="{-e(ind)}"'
            bc = rs[0].get("c", "#222222") if rs else "#222222"
            bul_xml = f'<a:buClr><a:srgbClr val="{_col(bc)}"/></a:buClr><a:buFont typeface="Arial"/><a:buChar char="{escape(bul)}"/>'
        ppr += f'><a:lnSpc><a:spcPct val="{int(lh / 1.2 * 100000)}"/></a:lnSpc><a:spcBef><a:spcPts val="0"/></a:spcBef><a:spcAft><a:spcPts val="{int(sp_after)}"/></a:spcAft>{bul_xml}</a:pPr>'
        runs = "".join(_run_xml(dict(r, spc=spc) if spc else r, sc) for r in rs)
        end_sz = int(round((rs[0].get("sz", 16) if rs else 16) * sc * 75))
        paras.append(f"<a:p>{ppr}{runs}<a:endParaRPr lang=\"uz-Latn-UZ\" sz=\"{max(end_sz, 100)}\" dirty=\"0\"/></a:p>")
    return (f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}" rtlCol="0">'
            f'<a:noAutofit/></a:bodyPr><a:lstStyle/>{"".join(paras)}</p:txBody>')


# ------------------------------------------------------------------ shakllar
def _sp_xml(el, sid, link_xml, qorongi):
    k = el["k"]
    name = el.get("nm") or f"{k}{sid}"
    nv = f"<p:nvSpPr>{_nv(sid, name, link_xml)}<p:cNvSpPr/><p:nvPr/></p:nvSpPr>"
    if k == "text":
        sp = f'<p:spPr>{_xfrm(el["x"], el["y"], el["w"], el["h"])}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>'
        nv = f'<p:nvSpPr>{_nv(sid, name, link_xml)}<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
        return f"<p:sp>{nv}{sp}{_txbody(el)}</p:sp>"
    fill = _grad(el["grad"], el.get("op", 1.0)) if el.get("grad") else _solid(el.get("fill"), el.get("op", 1.0))
    ln = _ln(el.get("line"), el.get("lw", 1), el.get("dash", 0), el.get("lop", 1.0))
    eff = _shadow(el.get("sh"), qorongi)
    if k == "rect":
        r = el.get("r", 0)
        if r:
            adj = int(min(50000, r / max(1, min(el["w"], el["h"])) * 100000))
            geom = f'<a:prstGeom prst="roundRect"><a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst></a:prstGeom>'
        else:
            geom = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
    elif k == "ell":
        geom = '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>'
    else:  # path
        W, H = max(e(el["w"]), 1), max(e(el["h"]), 1)
        pts = el["pts"]
        cmds = [f'<a:moveTo><a:pt x="{e(pts[0][0] - el["x"])}" y="{e(pts[0][1] - el["y"])}"/></a:moveTo>']
        for px, py in pts[1:]:
            cmds.append(f'<a:lnTo><a:pt x="{e(px - el["x"])}" y="{e(py - el["y"])}"/></a:lnTo>')
        if el.get("z", True):
            cmds.append("<a:close/>")
        pfill = "" if el.get("z", True) and el.get("fill") else ' fill="none"'
        geom = (f'<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/><a:rect l="0" t="0" r="r" b="b"/>'
                f'<a:pathLst><a:path w="{W}" h="{H}"{pfill}>{"".join(cmds)}</a:path></a:pathLst></a:custGeom>')
        if not el.get("z", True):
            fill = "<a:noFill/>"
    sp = f'<p:spPr>{_xfrm(el["x"], el["y"], el["w"], el["h"])}{geom}{fill}{ln}{eff}</p:spPr>'
    return f"<p:sp>{nv}{sp}</p:sp>"


def _cxn_xml(el, sid):
    x1, y1, x2, y2 = el["x1"], el["y1"], el["x2"], el["y2"]
    x, y = min(x1, x2), min(y1, y2)
    w, h = abs(x2 - x1), abs(y2 - y1)
    flipH = x2 < x1
    flipV = y2 < y1
    name = el.get("nm") or f"line{sid}"
    return (f'<p:cxnSp><p:nvCxnSpPr>{_nv(sid, name)}<p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
            f'<p:spPr>{_xfrm(x, y, w, h, flipH, flipV)}<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'{_ln(el.get("line"), el.get("lw", 1.5), el.get("dash", 0), el.get("op", 1.0), el.get("arr"))}</p:spPr></p:cxnSp>')


def _pic_xml(el, sid, rid, img_w, img_h, link_xml):
    x, y, w, h = el["x"], el["y"], el["w"], el["h"]
    if el.get("fit", "contain") == "contain" and img_w and img_h:
        k = min(w / img_w, h / img_h)
        nw, nh = img_w * k, img_h * k
        x, y, w, h = x + (w - nw) / 2, y + (h - nh) / 2, nw, nh
        crop = ""
    else:
        crop = ""
        if img_w and img_h:
            ar_box, ar_img = w / h, img_w / img_h
            if ar_img > ar_box:
                cut = (1 - ar_box / ar_img) / 2
                crop = f'<a:srcRect l="{int(cut * 100000)}" r="{int(cut * 100000)}"/>'
            elif ar_img < ar_box:
                cut = (1 - ar_img / ar_box) / 2
                crop = f'<a:srcRect t="{int(cut * 100000)}" b="{int(cut * 100000)}"/>'
    name = el.get("nm") or f"rasm{sid}"
    return (f'<p:pic><p:nvPicPr>{_nv(sid, name, link_xml)}<p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/>{crop}<a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr>{_xfrm(x, y, w, h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')


# ------------------------------------------------------------------ animatsiya
class _Id:
    def __init__(self):
        self.n = 2

    def __call__(self):
        self.n += 1
        return self.n


def _vis(spid, nid):
    return (f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="visible"/></p:to></p:set>')


def _anim(spid, nid, attr, v0, v1, ms):
    def val(v):
        return f'<p:fltVal val="{v}"/>' if isinstance(v, (int, float)) else f'<p:strVal val="{v}"/>'
    return (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base"><p:cTn id="{nid()}" dur="{ms}" fill="hold"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>{attr}</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:tavLst><p:tav tm="0"><p:val>{val(v0)}</p:val></p:tav><p:tav tm="100000"><p:val>{val(v1)}</p:val></p:tav></p:tavLst></p:anim>')


def _effect(spid, nid, filt, ms):
    return (f'<p:animEffect transition="in" filter="{filt}"><p:cBhvr><p:cTn id="{nid()}" dur="{ms}"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>')


WIPE = {"l": (8, "wipe(left)"), "r": (2, "wipe(right)"), "u": (1, "wipe(up)"), "d": (4, "wipe(down)")}
FLY = {"u": (4, "ppt_y", "1+#ppt_h/2"), "d": (1, "ppt_y", "0-#ppt_h/2"), "l": (8, "ppt_x", "0-#ppt_w/2"), "r": (2, "ppt_x", "1+#ppt_w/2")}


def _effect_par(spid, a, node_type, nid):
    eff = a.get("e", "fade")
    ms = int(a.get("ms", 500))
    dl = int(a.get("dl", 0))
    d = a.get("d") or "l"
    cid = nid()
    if eff == "pulse":
        body = (f'<p:animScale><p:cBhvr><p:cTn id="{nid()}" dur="{max(ms // 2, 150)}" autoRev="1" fill="hold"/>'
                f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr><p:by x="112000" y="112000"/></p:animScale>')
        head = f'presetID="6" presetClass="emph" presetSubtype="0"'
    elif eff == "wipe":
        sub, filt = WIPE.get(d, WIPE["l"])
        head = f'presetID="22" presetClass="entr" presetSubtype="{sub}"'
        body = _vis(spid, nid) + _effect(spid, nid, filt, ms)
    elif eff == "zoom":
        head = 'presetID="53" presetClass="entr" presetSubtype="16"'
        body = (_vis(spid, nid) + _anim(spid, nid, "ppt_w", 0, "#ppt_w", ms) + _anim(spid, nid, "ppt_h", 0, "#ppt_h", ms)
                + _effect(spid, nid, "fade", ms))
    elif eff == "fly":
        sub, attr, start = FLY.get(d, FLY["u"])
        other = "ppt_x" if attr == "ppt_y" else "ppt_y"
        head = f'presetID="2" presetClass="entr" presetSubtype="{sub}"'
        body = _vis(spid, nid) + _anim(spid, nid, other, "#" + other, "#" + other, ms) + _anim(spid, nid, attr, start, "#" + attr, ms)
        # x, y tartibi PowerPoint'dagidek
    elif eff == "rise":
        head = 'presetID="42" presetClass="entr" presetSubtype="0"'
        body = (_vis(spid, nid) + _effect(spid, nid, "fade", ms) + _anim(spid, nid, "ppt_x", "#ppt_x", "#ppt_x", ms)
                + _anim(spid, nid, "ppt_y", "#ppt_y+.1", "#ppt_y", ms))
    elif eff in ("circle", "box", "split"):
        pid, sub, filt = {"circle": (6, 16, "circle(in)"), "box": (4, 16, "box(in)"), "split": (16, 21, "barn(inVertical)")}[eff]
        head = f'presetID="{pid}" presetClass="entr" presetSubtype="{sub}"'
        body = _vis(spid, nid) + _effect(spid, nid, filt, ms)
    elif eff in ("slide", "drop"):
        head = 'presetID="42" presetClass="entr" presetSubtype="0"'
        x0 = "#ppt_x-.04" if eff == "slide" else "#ppt_x"
        y0 = "#ppt_y-.06" if eff == "drop" else "#ppt_y"
        body = (_vis(spid, nid) + _effect(spid, nid, "fade", ms) + _anim(spid, nid, "ppt_x", x0, "#ppt_x", ms)
                + _anim(spid, nid, "ppt_y", y0, "#ppt_y", ms))
    elif eff == "grow":
        head = 'presetID="53" presetClass="entr" presetSubtype="16"'
        body = (_vis(spid, nid) + _anim(spid, nid, "ppt_w", "#ppt_w*0.85", "#ppt_w", ms) + _anim(spid, nid, "ppt_h", "#ppt_h*0.85", "#ppt_h", ms)
                + _effect(spid, nid, "fade", ms))
    elif eff == "wedge":
        head = 'presetID="20" presetClass="entr" presetSubtype="0"'
        body = _vis(spid, nid) + _effect(spid, nid, "wedge", ms)
    else:
        head = 'presetID="10" presetClass="entr" presetSubtype="0"'
        body = _vis(spid, nid) + _effect(spid, nid, "fade", ms)
    return (f'<p:par><p:cTn id="{cid}" {head} fill="hold" nodeType="{node_type}"><p:stCondLst><p:cond delay="{dl}"/></p:stCondLst>'
            f'<p:childTnLst>{body}</p:childTnLst></p:cTn></p:par>')


def _timing(slide_els, spids):
    """slide_els: [(el, spid)]. Qadamlar bo'yicha guruhlaydi."""
    nid = _Id()
    qadamlar = {}
    trig = {}
    for el, spid in slide_els:
        a = el.get("a")
        if not a:
            continue
        if a.get("tr"):
            tsp = spids.get(a["tr"])
            if tsp:
                trig.setdefault(tsp, []).append((el, spid))
            continue
        qadamlar.setdefault(int(a.get("s", 0)), []).append((el, spid))
    if not qadamlar and not trig:
        return ""
    groups = []
    for s in sorted(qadamlar):
        items = sorted(qadamlar[s], key=lambda t: t[0]["a"].get("dl", 0))
        outer = nid()
        inner = nid()
        effs = []
        for i, (el, spid) in enumerate(items):
            if s == 0:
                nt = "afterEffect" if i == 0 else "withEffect"
            else:
                nt = "clickEffect" if i == 0 else "withEffect"
            effs.append(_effect_par(spid, el["a"], nt, nid))
        cond = ('<p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond>' if s == 0
                else '<p:cond delay="indefinite"/>')
        groups.append(f'<p:par><p:cTn id="{outer}" fill="hold"><p:stCondLst>{cond}</p:stCondLst><p:childTnLst>'
                      f'<p:par><p:cTn id="{inner}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
                      f'<p:childTnLst>{"".join(effs)}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
    parts = []
    if groups:
        parts.append('<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
                     + "".join(groups) +
                     '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
                     '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>')
    for tsp, items in trig.items():
        seq_id = nid()
        o1, o2 = nid(), nid()
        effs = "".join(_effect_par(spid, el["a"], "clickEffect" if i == 0 else "withEffect", nid) for i, (el, spid) in enumerate(items))
        parts.append(
            f'<p:seq concurrent="1" nextAc="seek"><p:cTn id="{seq_id}" restart="whenNotActive" fill="hold" evtFilter="cancelBubble" nodeType="interactiveSeq">'
            f'<p:stCondLst><p:cond evt="onClick" delay="0"><p:tgtEl><p:spTgt spid="{tsp}"/></p:tgtEl></p:cond></p:stCondLst>'
            f'<p:endSync evt="end" delay="0"><p:rtn val="all"/></p:endSync><p:childTnLst>'
            f'<p:par><p:cTn id="{o1}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'<p:par><p:cTn id="{o2}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{effs}</p:childTnLst></p:cTn></p:par>'
            f'</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn>'
            f'<p:nextCondLst><p:cond evt="onClick" delay="0"><p:tgtEl><p:spTgt spid="{tsp}"/></p:tgtEl></p:cond></p:nextCondLst></p:seq>')
    return ('<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
            + "".join(parts) + '</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')


P_NS = 'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'


def _transition(kind):
    if kind == "morph":
        return ('<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
                '<mc:Choice xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" '
                'xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" Requires="p159">'
                f'<p:transition {P_NS} spd="slow" p14:dur="1000"><p159:morph option="byObject"/></p:transition>'
                f'</mc:Choice><mc:Fallback><p:transition {P_NS} spd="med"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>')
    inner = {"push": '<p:push dir="u"/>', "wipe": '<p:wipe dir="r"/>', "none": None}.get(kind, "<p:fade/>")
    if inner is None:
        return ""
    return f'<p:transition {P_NS} spd="med">{inner}</p:transition>'


# ------------------------------------------------------------------ asosiy
def yoz(sahna: dict, rasm_ol) -> bytes:
    """sahna: {"slaydlar": [...]} ; rasm_ol(src) -> (bytes, w, h) yoki None."""
    belgi = _YUZLAR.set({k: v.get("face") for k, v in (sahna.get("shriftlar") or {}).items() if isinstance(v, dict) and v.get("face")})
    try:
        return _yoz(sahna, rasm_ol)
    finally:
        _YUZLAR.reset(belgi)


def _yoz(sahna: dict, rasm_ol) -> bytes:
    from PIL import Image

    prs = Presentation()
    prs.slide_width = Emu(12192000)
    prs.slide_height = Emu(6858000)
    blank = prs.slide_layouts[6]
    slides = [prs.slides.add_slide(blank) for _ in sahna["slaydlar"]]
    pic_cache = {}

    for idx, (sd, slide) in enumerate(zip(sahna["slaydlar"], slides)):
        part = slide.part
        tree = slide.shapes._spTree
        # fon
        fon = sd.get("fon") or {}
        cSld = slide._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}cSld")
        if fon.get("src"):
            got = rasm_ol(fon["src"])
            if got:
                _ip, rid = part.get_or_add_image_part(io.BytesIO(got[0]))
                bg = etree.fromstring(f'<p:bg {NSMAP}><p:bgPr><a:blipFill dpi="0" rotWithShape="1"><a:blip r:embed="{rid}"/><a:srcRect/>'
                                      f'<a:stretch><a:fillRect/></a:stretch></a:blipFill><a:effectLst/></p:bgPr></p:bg>')
                cSld.insert(0, bg)
        elif fon.get("rang"):
            bg = etree.fromstring(f'<p:bg {NSMAP}><p:bgPr>{_solid(fon["rang"])}<a:effectLst/></p:bgPr></p:bg>')
            cSld.insert(0, bg)

        spids = {}
        sid = 1
        pairs = []
        for el in sd["els"]:
            sid += 1
            spids[el["id"]] = sid
        for el in sd["els"]:
            spid = spids[el["id"]]
            link_xml = ""
            lnk = el.get("lnk")
            if lnk is not None:
                if lnk == "next":
                    link_xml = '<a:hlinkClick r:id="" action="ppaction://hlinkshowjump?jump=nextslide"/>'
                elif lnk == "prev":
                    link_xml = '<a:hlinkClick r:id="" action="ppaction://hlinkshowjump?jump=previousslide"/>'
                elif isinstance(lnk, int) and 0 <= lnk < len(slides) and lnk != idx:
                    rid = part.relate_to(slides[lnk].part, RT.SLIDE)
                    link_xml = f'<a:hlinkClick r:id="{rid}" action="ppaction://hlinksldjump"/>'
            k = el["k"]
            if k == "line":
                xml = _cxn_xml(el, spid)
            elif k == "img":
                got = rasm_ol(el["src"])
                if not got:
                    continue
                data, iw, ih = got
                key = el["src"]
                if key not in pic_cache:
                    pic_cache[key] = data
                _ip, rid = part.get_or_add_image_part(io.BytesIO(data))
                xml = _pic_xml(el, spid, rid, iw, ih, link_xml)
            else:
                xml = _sp_xml(el, spid, link_xml, sd.get("qorongi"))
            node = etree.fromstring(f"<root {NSMAP}>{xml}</root>")[0]
            tree.append(node)
            pairs.append((el, spid))
        # o'tish va animatsiya
        root = slide._element
        tr = _transition(sd.get("otish", "fade"))
        if tr:
            root.append(etree.fromstring(tr))
        tm = _timing(pairs, spids)
        if tm:
            root.append(etree.fromstring(tm.replace("<p:timing>", f'<p:timing {NSMAP}>', 1)))
        if sd.get("izoh"):
            slide.notes_slide.notes_text_frame.text = sd["izoh"]

    meta = sahna.get("meta") or {}
    cp = prs.core_properties
    cp.title = (meta.get("mavzu") or "Taqdimot")[:200]
    cp.author = (meta.get("muallif") or "talimkabutar.uz")[:120]
    cp.subject = (meta.get("fan_nomi") or meta.get("fan") or "")[:200]
    cp.keywords = "talimkabutar.uz taqdimot dvigateli"
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
