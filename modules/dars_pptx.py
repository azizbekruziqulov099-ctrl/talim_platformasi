"""REV427: dars → PowerPoint (ochiq dars taqdimoti).

Tuzilishi (ochiq darsga xos): titul → dars maqsadi va jihozlar → dars rejasi (bosqich + vaqt) → har bir dars
qadami (doska yozuvlari bosilganda bittadan chiqadi, formulalar rasm, kombinatorika chizmalari PowerPoint'ning o'z
shakllari bilan bosqichma-bosqich) → savol slaydlari (to'g'ri javob bosilganda yashil bo'ladi) → namunaviy misollar
(yechim qadamlari bittadan) → test (javob kaliti bosilganda) → xulosa → refleksiya → uy vazifasi.
Ustozning gapi slayd izohlariga (speaker notes) yoziladi.
"""
import re
from io import BytesIO
from itertools import permutations

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from modules.dars_export import STEP_LABELS, _meta, _no_emoji, _outline, _png, _tegsiz, _voice, plain

NAVY, TEAL, CHALK, YELLOW, BOARD = "1B4B7A", "0D7A77", "F4F1E8", "FFD54A", "17324D"
INK, MUTED, GREEN, LIGHT = "1D2B3A", "5B6573", "1F8A4C", "EEF3F8"
HARF_RANG = {"A": "F4A6A6", "B": "A8E6A1", "C": "9CC9FF", "D": "FFD37A", "E": "D7B4F3", "F": "FFB38A", "G": "8EE0D6", "H": "E8E8E8"}
W, H = Inches(13.333), Inches(7.5)
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


def _rgb(h):
    return RGBColor.from_string(h)


# ───────────── animatsiya (bosilganda chiqadi) ─────────────
def animatsiya(slide, guruhlar):
    """guruhlar: [[shape, ...], ...] — har guruh bitta bosishda birga chiqadi (Fade)."""
    guruhlar = [g for g in guruhlar if g]
    if not guruhlar:
        return
    nid = [2]

    def n():
        nid[0] += 1
        return nid[0]

    click_xml = []
    for g in guruhlar:
        effects = []
        for i, sh in enumerate(g):
            sp = sh.shape_id
            effects.append(f'''<p:par><p:cTn id="{n()}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" nodeType="{'clickEffect' if i == 0 else 'withEffect'}">
<p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>
<p:set><p:cBhvr><p:cTn id="{n()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl>
<p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>
<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{n()}" dur="450"/><p:tgtEl><p:spTgt spid="{sp}"/></p:tgtEl></p:cBhvr></p:animEffect>
</p:childTnLst></p:cTn></p:par>''')
        click_xml.append(f'''<p:par><p:cTn id="{n()}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst><p:childTnLst>
<p:par><p:cTn id="{n()}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>{''.join(effects)}</p:childTnLst></p:cTn></p:par>
</p:childTnLst></p:cTn></p:par>''')
    xml = f'''<p:timing xmlns:p="{P_NS}"><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>
<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>{''.join(click_xml)}</p:childTnLst></p:cTn>
<p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>
<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>
</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>'''
    el = etree.fromstring(xml)
    sld = slide._element
    old = sld.find(f"{{{P_NS}}}timing")
    if old is not None:
        sld.remove(old)
    ext = sld.find(f"{{{P_NS}}}extLst")
    if ext is not None:
        ext.addprevious(el)
    else:
        sld.append(el)


# ───────────── formulalar (matplotlib mathtext → PNG) ─────────────
def _mathtext(s):
    s = re.sub(r"\\[dt]frac", r"\\frac", s)
    s = s.replace("\\le ", "\\leq ").replace("\\ge ", "\\geq ").replace("\\;", "\\ ").replace("\\,", "\\ ")
    s = re.sub(r"\\text\{([^{}]*)\}", r"\\mathrm{\1}", s)
    return s


def formula_png(text, color="#F4F1E8", size=30):
    """«matn $formula$ matn» qatorini rasmga aylantiradi. Bo'lmasa — None (oddiy matn bo'lib qoladi)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(0.01, 0.01))
        fig.text(0, 0, _mathtext(text), fontsize=size, color=color, family="DejaVu Sans")
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=150, transparent=True, bbox_inches="tight", pad_inches=0.04)
        plt.close(fig)
        from PIL import Image
        im = Image.open(BytesIO(buf.getvalue()))
        return buf.getvalue(), im.width, im.height
    except Exception:   # noqa: BLE001
        return None


# ───────────── yordamchilar ─────────────
def _matn(slide, x, y, w, h, text, size=20, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font="Arial"):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Emu(0))
    lines = str(text).split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size, r.font.bold, r.font.name = Pt(size), bold, font
        r.font.color.rgb = _rgb(color)
    return tb


def _quti(slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = _rgb(fill)
    if line:
        s.line.color.rgb = _rgb(line)
        s.line.width = Pt(1.5)
    else:
        s.line.fill.background()
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    s.shadow.inherit = False
    return s


def _sarlavha(slide, bosqich, title):
    bar = _quti(slide, 0, 0, W, Inches(1.0), NAVY, shape=MSO_SHAPE.RECTANGLE)
    _matn(slide, Inches(0.5), Inches(0.14), Inches(9), Inches(0.3), bosqich.upper(), 12, "A9C4E0", True)
    _matn(slide, Inches(0.5), Inches(0.42), Inches(12.3), Inches(0.5), title, 26 if len(title) <= 55 else 20 if len(title) <= 80 else 16, "FFFFFF", True)
    return bar


def _bosh_slayd(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = _rgb("FFFFFF")
    return s


def _izoh(slide, text):
    t = _voice(text)
    if t:
        slide.notes_slide.notes_text_frame.text = t[:6000]


def _shar(slide, x, y, d, h, yangi=False, xira=False):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, d, d)
    s.fill.solid()
    s.fill.fore_color.rgb = _rgb(YELLOW if yangi else HARF_RANG.get(h, "DDDDDD"))
    if yangi:
        s.line.color.rgb = _rgb("FFFFFF")
        s.line.width = Pt(3)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    tf = s.text_frame
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Emu(0))
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = h
    r.font.size, r.font.bold, r.font.name = Pt(max(12, int(d / 12700 * 0.45))), True, "Arial"
    r.font.color.rgb = _rgb("8899AA" if xira else INK)
    if xira:
        s.fill.fore_color.rgb = _rgb("3A5068")
    return s


HARFLAR = "ABCDEFGH"


def _orin_almash(slide, x0, y0, n):
    """n! = n·(n−1)!: (n−1)! ta tartibning har biriga yangi harf n joyga kiradi. Guruhlar — bosishlar."""
    n = max(1, min(4, n))
    d, gap = (Inches(0.72), Inches(0.1)) if n <= 3 else (Inches(0.5), Inches(0.07))
    tartib = [["A"]]
    for m in range(2, n):
        tartib = [t[:j] + [HARFLAR[m - 1]] + t[j:] for t in tartib for j in range(len(t), -1, -1)]
    guruhlar = []
    if n == 1:
        guruhlar.append([_shar(slide, x0, y0, d, "A")])
        return guruhlar, "1! = 1"
    yangi = HARFLAR[n - 1]
    asoslar = tartib if n <= 3 else tartib
    satr = 0
    for bi, asos in enumerate(asoslar):
        y = y0 + satr * (d + (Inches(0.3) if n <= 3 else Inches(0.12)))
        if n == 4 and bi > 0:   # qolgan asoslar — «→ ×4»
            g = [_shar(slide, x0 + j * (d + gap), y, d, h) for j, h in enumerate(asos)]
            g.append(_matn(slide, x0 + 3 * (d + gap) + Inches(0.15), y + Inches(0.1), Inches(1.2), d, f"→ ×{n}", 20, YELLOW, True))
            guruhlar.append(g)
            satr += 1
            continue
        if n == 4:
            guruhlar.append([_shar(slide, x0 + j * (d + gap), y, d, h) for j, h in enumerate(asos)])
            xs = x0 + 3 * (d + gap) + Inches(0.6)
        else:
            xs = x0
        for j in range(len(asos) + 1):
            t = asos[:j] + [yangi] + asos[j:]
            qx = xs + (j * (len(t) * (d + gap) + Inches(0.35)) if n <= 3 else (j % 2) * (len(t) * (d + gap) + Inches(0.35)))
            qy = y if n <= 3 else y + (j // 2) * (d + Inches(0.12))
            guruhlar.append([_shar(slide, qx + k * (d + gap), qy, d, h, yangi=(h == yangi)) for k, h in enumerate(t)])
        satr += 1 if n <= 3 else 2
    f = 1
    for i in range(2, n):
        f *= i
    return guruhlar, f"{n}! = {n} · {n - 1}! = {n} · {f} = {n * f}"


def _orinlashtir(slide, x0, y0, n, k):
    n, k = max(1, min(8, n)), max(1, min(4, k))
    d, gap = Inches(0.55), Inches(0.12)
    guruhlar = [[_shar(slide, x0 + i * (d + gap), y0, d, HARFLAR[i]) for i in range(n)]]
    tanlov, A = [], 1
    for i in range(k):
        x = x0 + i * Inches(1.9)
        slot = _quti(slide, x, y0 + Inches(1.1), Inches(1.5), Inches(0.9), BOARD, line=CHALK)
        slot.line.dash_style = 4
        guruhlar[0].append(slot)
        v = n - i
        A *= v
        tanlov.append(str(v))
        guruhlar.append([_shar(slide, x + Inches(0.47), y0 + Inches(1.27), d, HARFLAR[i], yangi=True),
                         _matn(slide, x, y0 + Inches(2.1), Inches(1.5), Inches(0.4), f"{v} xil", 20, YELLOW, True, PP_ALIGN.CENTER)])
    if n > k:
        guruhlar.append([_shar(slide, x0 + i * (d + gap), y0, d, HARFLAR[i], xira=True) for i in range(k, n)]
                        + [_matn(slide, x0, y0 + Inches(2.6), Inches(11), Inches(0.4), f"chetda qolgan {n - k} tasining tartibi muhim emas — shuning uchun ({n - k})! ga bo‘lamiz", 17, CHALK)])
    return guruhlar, f"A = {' · '.join(tanlov)} = {A}"


def _guruhlash(slide, x0, y0, n, k):
    n, k = max(1, min(8, n)), max(1, min(3, k))
    d, gap = Inches(0.42), Inches(0.05)
    harf = list(HARFLAR[:k])
    tartiblar = list(permutations(harf))
    satr = [[_shar(slide, x0 + i * (k * (d + gap) + Inches(0.3)) + j * (d + gap), y0, d, h) for j, h in enumerate(t)] for i, t in enumerate(tartiblar)]
    guruhlar = [sum(satr, [])]
    gx = x0 + Inches(3.6)
    box = _quti(slide, gx - Inches(0.2), y0 + Inches(0.9), k * (d + gap) + Inches(0.4), d + Inches(0.4), "3D3A1E", line=YELLOW)
    guruhlar.append([box] + [_shar(slide, gx + j * (d + gap), y0 + Inches(1.1), d, h, yangi=True) for j, h in enumerate(harf)]
                    + [_matn(slide, gx + k * (d + gap) + Inches(0.4), y0 + Inches(1.15), Inches(4), Inches(0.4), f"{len(tartiblar)} = {k}! tartib → 1 guruh", 20, YELLOW, True)])
    A = 1
    for i in range(k):
        A *= n - i
    return guruhlar, f"C = A / {k}! = {A} / {len(tartiblar)} = {A // len(tartiblar)}"


BUYRUQ = re.compile(r"^\s*(OYIN|ORIN_ALMASH|ORINLASHTIR|GURUHLASH|QOIDA|BELGILA|YOZ|DAVOM|USTUN|BOLISH|QISQART|SON_OQI|GRAFIK|CHIZ|KASR_MODEL|DOIRA_KASR|VENN|DARAXT|OCHIR)\s*:?\s*(.*)$", re.I)


def doska_qatorlari(steps):
    out = []
    for s in steps:
        for line in str(s.get("doska") or "").split("\n"):
            line = _tegsiz(line).strip()
            if line and not line.upper().startswith("OCHIR"):
                out.append(line)
    return out


def _doska_slayd(prs, bosqich, title, lines, notes, picture=None):
    s = _bosh_slayd(prs)
    _sarlavha(s, bosqich, title)
    _quti(s, Inches(0.4), Inches(1.25), Inches(12.53), Inches(5.95), BOARD, radius=0.03)
    x, y, maxy = Inches(0.8), Inches(1.55), Inches(6.95)
    guruhlar = []
    if picture:
        conv = _png(picture)
        if conv:
            pw = Inches(3.6)
            ph = int(pw * conv[2] / max(1, conv[1]))
            pic = s.shapes.add_picture(BytesIO(conv[0]), Inches(9.0), Inches(1.55), pw, min(ph, Inches(5.2)))
            guruhlar.append([pic])
    for line in lines:
        if y > maxy - Inches(0.5):
            break
        m = BUYRUQ.match(line)
        tur, arg = (m.group(1).upper(), m.group(2)) if m else ("", line)
        nums = [int(v) for v in re.findall(r"\d+", arg)]
        if tur == "ORIN_ALMASH" and nums:
            g, xul = _orin_almash(s, x, y, nums[0])
            guruhlar += g
            yy = max((sh.top + sh.height for gr in g for sh in gr), default=y) + Inches(0.2)
            guruhlar.append([_matn(s, x, yy, Inches(11), Inches(0.5), xul, 24, YELLOW, True)])
            y = yy + Inches(0.6)
            continue
        if tur in ("ORINLASHTIR", "GURUHLASH") and len(nums) >= 2:
            g, xul = (_orinlashtir if tur == "ORINLASHTIR" else _guruhlash)(s, x, y, nums[0], nums[1])
            guruhlar += g
            yy = max((sh.top + sh.height for gr in g for sh in gr), default=y) + Inches(0.2)
            guruhlar.append([_matn(s, x, yy, Inches(11), Inches(0.5), xul, 24, YELLOW, True)])
            y = yy + Inches(0.6)
            continue
        if tur == "OYIN":   # REV429: doskadagi o'yin — taqdimotda o'qituvchiga eslatma (o'yin platformada o'ynaladi)
            nomi = {"joylashtir": "harflarni har xil tartibda qo‘yish", "tanga": "tangani ko‘p marta tashlash tajribasi",
                    "kub": "kubni ko‘p marta tashlash tajribasi", "galton": "Galton taxtasi — sharlar tashlash",
                    "venn": "Venn diagrammasini bo‘yash", "daraxt": "ehtimollar daraxti — mahsulot olish", "ikkikub": "ikki kub yig‘indisi taqsimoti",
                    "nuqta": "kvadratga nuqta tashlash", "tanlanma": "tanlanmalar va ishonch oraliqlari", "chiziq": "eng yaxshi chiziqni o‘tkazish"}.get((arg.split() or [""])[0].lower(), arg)
            box = _quti(s, x - Inches(0.15), y - Inches(0.08), Inches(11.4), Inches(0.8), "1F4E3D", line="6CC070")
            guruhlar.append([box, _matn(s, x, y + Inches(0.08), Inches(11), Inches(0.6), f"🎮 O‘quvchilar platformada o‘ynaydi: {nomi}", 22, "C9F2C9", True)])
            y += Inches(1.0)
            continue
        qoida = tur == "QOIDA"
        matn = arg if tur in ("QOIDA", "YOZ", "DAVOM", "BELGILA") or not tur else arg
        shapes = []
        img = formula_png(matn, "#FFD54A" if qoida else "#F4F1E8") if "$" in matn else None
        if img:
            hh = Inches(min(1.6, img[2] / 150 * 0.8))   # 30 pt shrift → ~24 pt ko'rinish; kasr baland bo'lsa — balandroq
            ww = int(hh * img[1] / max(1, img[2]))
            if ww > Inches(11.0):
                ww, hh = Inches(11.0), int(Inches(11.0) * img[2] / img[1])
        else:
            hh = Inches(0.55)
        if qoida:   # «Esda tut» qutisi — ichidagi formula/matn balandligida
            shapes.append(_quti(s, x - Inches(0.15), y - Inches(0.1), Inches(11.4), hh + Inches(0.2), "24486B", line=YELLOW))
        if img:
            shapes.append(s.shapes.add_picture(BytesIO(img[0]), x, y, ww, hh))
        else:
            shapes.append(_matn(s, x, y, Inches(11.2) if not picture else Inches(8), hh, plain(matn), 24, YELLOW if qoida else CHALK, qoida))
        guruhlar.append(shapes)
        y += hh + Inches(0.3)
    animatsiya(s, guruhlar)
    _izoh(s, notes)
    return s


def _savol_slayd(prs, savol, variantlar, togri, izoh="", bosqich="Savol — o‘quvchilar javob beradi", aralash=False):
    if aralash and len(variantlar) > 1:   # darsdagi savollarda to'g'ri javob birinchi saqlanadi — slaydda aralashtiriladi
        import random
        rnd = random.Random(str(savol))
        tartib = list(range(len(variantlar)))
        rnd.shuffle(tartib)
        variantlar = [variantlar[i] for i in tartib]
        togri = tartib.index(togri) if 0 <= togri < len(tartib) else 0
    s = _bosh_slayd(prs)
    _sarlavha(s, bosqich, "Savol")
    img = formula_png(savol, "#1D2B3A", 28) if "$" in savol else None
    if img:
        hh = Inches(min(1.4, img[2] / 150 * 0.85))
        ww = min(Inches(12), int(hh * img[1] / max(1, img[2])))
        s.shapes.add_picture(BytesIO(img[0]), Inches(0.6), Inches(1.35), ww, int(ww * img[2] / max(1, img[1])))
    else:
        _matn(s, Inches(0.6), Inches(1.35), Inches(12.1), Inches(1.2), plain(savol), 28, INK, True)
    javob = []
    n = len(variantlar)
    kol = 2 if n > 2 else n
    for i, v in enumerate(variantlar):
        cx, cy = Inches(0.6) + (i % kol) * Inches(6.2), Inches(2.9) + (i // kol) * Inches(1.25)
        _quti(s, cx, cy, Inches(5.9), Inches(1.0), LIGHT, line="C8D3DF")
        _matn(s, cx + Inches(0.25), cy, Inches(5.5), Inches(1.0), f"{'ABCDEF'[i]})  {plain(v)}", 24, INK, False, anchor=MSO_ANCHOR.MIDDLE)
        if i == togri:
            ok = _quti(s, cx, cy, Inches(5.9), Inches(1.0), "DDF3E4", line=GREEN)
            ok.line.width = Pt(3)
            t = _matn(s, cx + Inches(0.25), cy, Inches(5.5), Inches(1.0), f"✓  {'ABCDEF'[i]})  {plain(v)}", 24, GREEN, True, anchor=MSO_ANCHOR.MIDDLE)
            javob += [ok, t]
    if izoh:
        javob.append(_matn(s, Inches(0.6), Inches(6.55), Inches(12), Inches(0.7), plain(izoh), 18, MUTED))
    animatsiya(s, [javob])
    _izoh(s, f"Savol: {plain(savol)}. To‘g‘ri javob: {plain(variantlar[togri]) if 0 <= togri < n else ''}. {plain(izoh)}")
    return s


def _misol_slayd(prs, step, k):
    s = _bosh_slayd(prs)
    _sarlavha(s, "Mustahkamlash — namunaviy misol", step.get("sarlavha") or f"{k}-misol")
    shart = str(step.get("doska") or step.get("savol") or "")
    img = formula_png(shart, "#1D2B3A", 26) if "$" in shart else None
    if img:
        hh = Inches(min(1.1, img[2] / 150 * 0.8))
        s.shapes.add_picture(BytesIO(img[0]), Inches(0.6), Inches(1.35), min(Inches(12), int(hh * img[1] / max(1, img[2]))), hh)
    else:
        _matn(s, Inches(0.6), Inches(1.3), Inches(12.1), Inches(1.1), plain(shart), 26, INK, True)
    _quti(s, Inches(0.4), Inches(2.6), Inches(12.53), Inches(4.6), BOARD, radius=0.03)
    y, guruhlar = Inches(2.9), []
    for q in (step.get("yechim") or [])[:6]:
        t = str(q.get("doska") or "")
        if not t:
            continue
        img = formula_png(t) if "$" in t else None
        if img:
            hh = Inches(min(1.0, img[2] / 150 * 0.72))
            ww = min(Inches(11.5), int(hh * img[1] / max(1, img[2])))
            guruhlar.append([s.shapes.add_picture(BytesIO(img[0]), Inches(0.8), y, ww, hh)])
            y += hh + Inches(0.15)
        else:
            guruhlar.append([_matn(s, Inches(0.8), y, Inches(11.5), Inches(0.6), plain(t), 22, CHALK)])
            y += Inches(0.65)
    if step.get("javob"):
        guruhlar.append([_matn(s, Inches(0.8), min(y, Inches(6.5)), Inches(11.5), Inches(0.6), f"Javob: {plain(str(step['javob']).split('|')[0])}", 26, YELLOW, True)])
    animatsiya(s, guruhlar)
    _izoh(s, step.get("ovoz") or "")
    return s


def lesson_pptx(lesson, images):
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    topic = lesson.get("topic") or {}
    mavzu = _no_emoji(topic.get("mavzu") or topic.get("topic_code") or "Dars")
    groups = _outline(lesson)
    steps = lesson.get("steps") or []

    # 1. Titul
    s = _bosh_slayd(prs)
    _quti(s, 0, 0, W, H, NAVY, shape=MSO_SHAPE.RECTANGLE)
    _quti(s, 0, Inches(5.9), W, Inches(0.12), TEAL, shape=MSO_SHAPE.RECTANGLE)
    _matn(s, Inches(0.9), Inches(1.2), Inches(11), Inches(0.5), "OCHIQ DARS", 20, "A9C4E0", True)
    _matn(s, Inches(0.9), Inches(1.8), Inches(11.5), Inches(2.4), mavzu, 40, "FFFFFF", True)
    meta = dict(_meta(lesson))
    _matn(s, Inches(0.9), Inches(4.4), Inches(11), Inches(1.2), "\n".join(x for x in (meta.get("Fan", ""), meta.get("Sinf", "")) if x), 20, "D8E4F0")
    _matn(s, Inches(0.9), Inches(6.25), Inches(11), Inches(0.8), "O‘qituvchi: ______________________          Sana: ____________", 18, "D8E4F0")

    # 2. Maqsad va jihozlar
    s = _bosh_slayd(prs)
    _sarlavha(s, "Dars haqida", "Darsning maqsadi va jihozlari")
    maqsad = meta.get("Dars maqsadi") or f"«{mavzu}» mavzusidagi tushunchalarni o‘quvchilar o‘zlari kashf qilib o‘zlashtirishi"
    kartalar = [("Ta’limiy", maqsad), ("Tarbiyaviy", "Mustaqil fikrlash, javobini asoslash, bir-birini tinglash"),
                ("Rivojlantiruvchi", "Naqshni ko‘rish, umumlashtirish va formulani o‘zi chiqarish ko‘nikmasi")]
    for i, (k, v) in enumerate(kartalar):
        x = Inches(0.6) + i * Inches(4.15)
        _quti(s, x, Inches(1.4), Inches(3.9), Inches(3.0), LIGHT, line="C8D3DF")
        _matn(s, x + Inches(0.25), Inches(1.6), Inches(3.4), Inches(0.5), k, 22, TEAL, True)
        _matn(s, x + Inches(0.25), Inches(2.2), Inches(3.4), Inches(2.1), v, 17, INK)
    _matn(s, Inches(0.6), Inches(4.75), Inches(12), Inches(2.4),
          "Dars turi: yangi bilim beruvchi (kashfiyot darsi)\nMetodlar: muammoli savol, kashfiyot, savol-javob, mustaqil ish\nJihozlar: proyektor, Kabutar Ta’lim platformasi, qoralama daftar", 19, INK)

    # 3. Reja
    tush = [g for g in groups if g["steps"][0].get("turi") not in ("amaliy", "kirish", "xulosa")]
    amaliy = [st for st in steps if st.get("turi") == "amaliy"]
    savollar = lesson.get("savollar") or []
    reja = [("Tashkiliy qism va motivatsiya", "5 daq"), (f"Yangi mavzu: {len(tush)} ta qadam, har biridan keyin savol", "40 daq"),
            (f"Mustahkamlash: {min(len(amaliy), 3)} ta namunaviy misol", "15 daq"), (f"Nazorat: {len(savollar)} ta test", "12 daq"),
            ("Xulosa va refleksiya", "5 daq"), ("Uy vazifasi", "3 daq")]
    s = _bosh_slayd(prs)
    _sarlavha(s, "Dars haqida", "Dars rejasi (80 daqiqa)")
    for i, (k, v) in enumerate(reja):
        y = Inches(1.35) + i * Inches(0.92)
        _quti(s, Inches(0.6), y, Inches(0.7), Inches(0.7), TEAL, shape=MSO_SHAPE.OVAL)
        _matn(s, Inches(0.6), y, Inches(0.7), Inches(0.7), str(i + 1), 22, "FFFFFF", True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
        _matn(s, Inches(1.55), y + Inches(0.12), Inches(9.5), Inches(0.6), k, 22, INK)
        _matn(s, Inches(11.2), y + Inches(0.12), Inches(1.6), Inches(0.6), v, 22, MUTED, True, PP_ALIGN.RIGHT)

    # 4. Dars qadamlari
    misol_k = 0
    for g in groups:
        first = g["steps"][0]
        turi = first.get("turi")
        if turi == "amaliy":
            for st in g["steps"]:
                if misol_k < 3:
                    misol_k += 1
                    _misol_slayd(prs, st, misol_k)
            continue
        birga = [st for st in g["steps"] if st.get("turi") == "birga"]
        oddiy = [st for st in g["steps"] if st.get("turi") != "birga"]
        if oddiy:
            bosqich = "Tashkiliy qism va motivatsiya" if turi == "kirish" else "Xulosa" if turi == "xulosa" else "Yangi mavzu"
            title = _no_emoji(plain(first.get("sarlavha") or STEP_LABELS.get(turi, "Qadam"))) or "Qadam"
            pic = next((images.get(st.get("rasm") or "") for st in oddiy if images.get(st.get("rasm") or "")), None)
            _doska_slayd(prs, bosqich, title, doska_qatorlari(oddiy), " ".join(st.get("ovoz") or "" for st in oddiy), pic)
        for st in birga:
            vlar = st.get("variantlar") or []
            if len(vlar) >= 2:
                tog = str(st.get("javob") or "").split("|")[0].strip()
                _savol_slayd(prs, str(st.get("doska") or st.get("savol") or ""), vlar, vlar.index(tog) if tog in vlar else 0, st.get("javob_izohi") or "", aralash=True)

    # 5. Test
    for i, q in enumerate(savollar, 1):
        _savol_slayd(prs, str(q.get("savol") or ""), q.get("variantlar") or [], int(q.get("togri") or 0), q.get("izoh") or "", f"Nazorat — {i}-test")

    # 6. Refleksiya
    s = _bosh_slayd(prs)
    _sarlavha(s, "Xulosa", "Refleksiya")
    for i, q in enumerate(["Bugun qaysi formulani o‘zim chiqardim?", "Qaysi qadam eng qiyin bo‘ldi?", "Bu bilim hayotda qayerda kerak bo‘ladi?"]):
        y = Inches(1.5) + i * Inches(1.6)
        _quti(s, Inches(0.8), y, Inches(11.7), Inches(1.25), LIGHT, line="C8D3DF")
        _matn(s, Inches(1.1), y, Inches(11), Inches(1.25), q, 26, INK, False, anchor=MSO_ANCHOR.MIDDLE)

    # 7. Uy vazifasi
    s = _bosh_slayd(prs)
    _sarlavha(s, "Uy vazifasi", "Uy vazifasi")
    uy = [plain(str(st.get("doska") or st.get("savol") or ""))[:160] for st in amaliy[3:8]]
    _matn(s, Inches(0.8), Inches(1.5), Inches(11.8), Inches(5.5),
          "\n\n".join(f"{i}. {t}" for i, t in enumerate(uy, 1)) if uy else "Mavzu bo‘yicha platformadagi amaliy mashg‘ulot masalalarini yechish.", 22, INK)

    buf = BytesIO()
    prs.save(buf)
    return buf.getvalue()
