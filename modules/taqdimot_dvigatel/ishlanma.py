"""Ochiq dars rejasidan Word (.docx) ishlanma: titul, umumiy ma'lumot, maqsadlar, texnologik xarita, darsning borishi,
tayyorgarlik va ilovalar (tarqatma, kartochkalar, baholash varag'i, test, kuzatuv varag'i…). Rasmlar mavzu miyasidan."""
from __future__ import annotations

import io
import re

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import ochiq_metodlar as om
from . import rasmlar

_BELGI = re.compile(r"\*\*|==|\$")


def _toza(v) -> str:
    """Miya matnidagi **qalin**, ==ajratilgan== va $formula$ belgilarini Word uchun olib tashlaydi."""
    return _BELGI.sub("", str(v if v is not None else ""))


RIM = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
SHRIFT = "Times New Roman"
TOQ = RGBColor(0x1F, 0x2A, 0x44)


def _hujjat() -> Document:
    d = Document()
    s = d.sections[0]
    s.orientation = WD_ORIENT.PORTRAIT
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.left_margin, s.right_margin, s.top_margin, s.bottom_margin = Cm(2.5), Cm(1.5), Cm(2), Cm(2)
    st = d.styles["Normal"]
    st.font.name, st.font.size = SHRIFT, Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), SHRIFT)
    st.paragraph_format.space_after = Pt(4)
    st.paragraph_format.line_spacing = 1.1
    for nom, kat in (("Heading 1", 15), ("Heading 2", 13), ("Heading 3", 12)):
        h = d.styles[nom]
        h.font.name, h.font.size, h.font.bold, h.font.color.rgb = SHRIFT, Pt(kat), True, TOQ
        rf = h.element.rPr.rFonts
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rf.get(qn(a)) is not None:
                del rf.attrib[qn(a)]
        for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(a), SHRIFT)
        h.paragraph_format.space_before, h.paragraph_format.space_after = Pt(12 if kat > 12 else 8), Pt(6)
        h.paragraph_format.keep_with_next = True
    _sahifa_raqami(s)
    return d


def _sahifa_raqami(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    for tur, matn in (("begin", None), (None, "PAGE"), ("end", None)):
        if tur:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), tur)
        else:
            e = OxmlElement("w:instrText")
            e.set(qn("xml:space"), "preserve")
            e.text = matn
        r._r.append(e)


def _p(d, matn="", bold=False, italic=False, size=None, align=None, after=None, color=None):
    p = d.add_paragraph()
    if matn:
        r = p.add_run(_toza(matn))
        r.bold, r.italic = bold, italic
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = color
    if align:
        p.alignment = align
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def _yorliq(d, yorliq, matn):
    p = d.add_paragraph()
    p.add_run(yorliq).bold = True
    p.add_run(" " + _toza(matn or ""))
    return p


def _royxat(d, bandlar, raqamli=False):
    """Raqamli ro'yxat har safar 1 dan boshlanadi (Word'ning umumiy raqamlashiga ulanmaydi)."""
    i = 0
    for b in bandlar:
        if not b:
            continue
        i += 1
        p = d.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.9)
        p.paragraph_format.first_line_indent = Cm(-0.6)
        p.paragraph_format.space_after = Pt(2)
        p.add_run(f"{i}. " if raqamli else "•  ")
        p.add_run(_toza(b))


def _soya(cell, rang="E8EEF7"):
    tc = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), rang)
    tc.append(sh)


def _jadval(d, ustunlar, qatorlar, kenglik, sarlavha=True, size=11):
    t = d.add_table(rows=0, cols=len(kenglik))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblpr = t._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblpr.append(lay)
    for ci, w in enumerate(kenglik):
        t.columns[ci].width = Cm(w)
    rows = ([ustunlar] if sarlavha and ustunlar else []) + list(qatorlar)
    for ri, q in enumerate(rows):
        cells = t.add_row().cells
        for ci, w in enumerate(kenglik):
            c = cells[ci]
            c.width = Cm(w)
            val = q[ci] if ci < len(q) else ""
            c.text = ""
            p = c.paragraphs[0]
            r = p.add_run(_toza(val))
            r.font.size = Pt(size)
            if sarlavha and ri == 0:
                r.bold = True
                _soya(c)
            p.paragraph_format.space_after = Pt(0)
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def _rasm(d, kalit, kenglik=8.0, izoh=""):
    kalit = rasmlar.kalit_toza(str(kalit or ""))
    if not kalit:
        return False
    try:
        got = rasmlar.ol(kalit)
    except Exception:
        got = None
    if not got:
        return False
    png = got[0] if isinstance(got, tuple) else got
    try:
        d.add_picture(io.BytesIO(png), width=Cm(kenglik))
        d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if izoh:
            _p(d, izoh, italic=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        return True
    except Exception:
        return False


def _sahifa(d):
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


# ---------------------------------------------------------------- material
def _material(d, mat: dict, kalit_bilan=True):
    t = mat.get("tur")
    if t == "savollar":
        if mat.get("kalit_soz"):
            _yorliq(d, "Kalit so‘z:", mat["kalit_soz"])
        for i, q in enumerate(mat["savollar"], 1):
            p = d.add_paragraph()
            p.add_run(f"{i}. {q['savol']}")
            if kalit_bilan and q.get("javob"):
                r = p.add_run(f"  (Javob: {q['javob']})")
                r.italic = True
            p.paragraph_format.space_after = Pt(2)
    elif t == "bayonotlar":
        _jadval(d, ["№", "Bayonot", "Javob"], [[i, b["matn"], ("to‘g‘ri" if b["togri"] else "noto‘g‘ri") + (f" — {b['izoh']}" if b.get("izoh") else "")]
                                              for i, b in enumerate(mat["bayonotlar"], 1)], [1, 10, 6])
    elif t == "atamalar":
        _jadval(d, ["Atama", "Ta’rif"], [[a["atama"], a["tarif"]] for a in mat["atamalar"]], [5, 12])
    elif t == "ortiqcha":
        for i, q in enumerate(mat["qatorlar"], 1):
            _p(d, f"{i}. {', '.join(q['qator'])}" + (f"  (Ortiqchasi: {q['ortiqcha']} — {q['sabab']})" if kalit_bilan else ""))
    elif t == "qismlar":
        for q in mat["qismlar"]:
            _p(d, (f"{q['guruh']}: " if q.get("guruh") else "") + q["nom"], bold=True, after=2)
            _p(d, q["matn"])
            if q.get("savol"):
                _yorliq(d, "Savol:", q["savol"])
    elif t == "matn":
        if mat.get("sarlavha"):
            _p(d, mat["sarlavha"], bold=True, after=2)
        _p(d, mat["matn"], italic=True)
    elif t == "keys":
        _yorliq(d, "Vaziyat:", mat["keys"]["vaziyat"])
        _royxat(d, mat["keys"]["savollar"], raqamli=True)
    elif t == "taqqoslash":
        q = mat["taqqoslash"]
        n = max(len(q["a_farq"]), len(q["umumiy"]), len(q["b_farq"]), 1)
        _jadval(d, [q["a"], "Umumiy", q["b"]], [[(q["a_farq"] + [""] * n)[i], (q["umumiy"] + [""] * n)[i], (q["b_farq"] + [""] * n)[i]] for i in range(n)],
                [5.6, 5.6, 5.8])
    elif t == "klaster":
        k = mat["klaster"]
        _yorliq(d, "Markaz:", k["markaz"])
        for s in k["shoxlar"]:
            _p(d, (f"{s['guruh']}: " if s.get("guruh") else "") + s["nom"] + (" — " + ", ".join(s["bandlar"]) if s["bandlar"] else ""), after=2)
    elif t == "topishmoq":
        _p(d, mat["topishmoq"]["matn"], italic=True)
        if kalit_bilan and mat["topishmoq"].get("javob"):
            _yorliq(d, "Javob:", mat["topishmoq"]["javob"])
    elif t == "xato":
        x = mat["xato"]
        if x.get("shart"):
            _yorliq(d, "Shart:", x["shart"])
        _yorliq(d, "Xato yechim:", x["xato"])
        if kalit_bilan:
            _yorliq(d, "To‘g‘ri yechim:", x.get("togri") or "")
            if x.get("sabab"):
                _yorliq(d, "Xato sababi:", x["sabab"])
    elif t == "vazifalar":
        v = mat["vazifalar"]
        for k, nom in (("A", "A — asosiy"), ("B", "B — qo‘llash"), ("C", "C — ijodiy")):
            if v.get(k):
                _yorliq(d, f"{nom}:", v[k])
    elif t == "royxat":
        if mat.get("sarlavha"):
            _p(d, mat["sarlavha"], bold=True, after=2)
        _royxat(d, mat["bandlar"])
    elif t == "qadamlar":
        _royxat(d, mat["bandlar"], raqamli=True)
        if mat.get("savol"):
            _yorliq(d, "Yakuniy savol:", mat["savol"])
        if mat.get("rasm"):
            _rasm(d, mat["rasm"], 6)
    elif t == "jamoaviy":
        _yorliq(d, "Masala:", mat["shart"])
        for q in mat["qismlar"]:
            _yorliq(d, f"{q['guruh']}:", q["matn"])
        if kalit_bilan and mat.get("yakun"):
            _yorliq(d, "Yakuniy javob:", mat["yakun"])
    elif t == "voqealar":
        _jadval(d, ["Davr", "Voqea", "Mazmuni"], [[v.get("davr") or "", v.get("nom") or "", v.get("matn") or ""] for v in mat["voqealar"]], [3, 4.5, 9.5])
    elif t == "tajriba":
        tj = mat["tajriba"]
        _yorliq(d, "Tajriba:", tj["nom"])
        if tj["jihozlar"]:
            _yorliq(d, "Jihozlar:", ", ".join(tj["jihozlar"]))
        _royxat(d, tj["bosqichlar"], raqamli=True)
        if tj.get("kuzatish"):
            _yorliq(d, "Kuzatish:", tj["kuzatish"])
        if tj.get("xavfsizlik"):
            _yorliq(d, "Xavfsizlik:", tj["xavfsizlik"])
        if mat.get("savol"):
            _yorliq(d, "Bashorat savoli:", mat["savol"])
    elif t == "test":
        for i, q in enumerate(mat["test"], 1):
            _p(d, f"{i}. {q['savol']}", after=1)
            _p(d, "   ".join(f"{'ABCD'[j]}) {v}" for j, v in enumerate(q["variantlar"])), after=4)
        if kalit_bilan:
            _yorliq(d, "Javoblar kaliti:", ", ".join(f"{i}-{'ABCD'[q['javob']]}" for i, q in enumerate(mat["test"], 1)))
    elif t == "slaydlar":
        for sl in mat["slaydlar"]:
            _p(d, sl.get("sarlavha") or "", bold=True, after=2)
            for e in sl.get("elementlar") or []:
                matn = e.get("matn") or e.get("shart") or e.get("formula") or ""
                if e.get("bandlar"):
                    matn = (matn + " " if matn else "") + "; ".join(f"{b.get('nom') or ''} {b.get('matn') or ''}".strip() for b in e["bandlar"])
                if matn:
                    _p(d, matn, after=2)
                if e.get("qadamlar"):
                    _royxat(d, e["qadamlar"], raqamli=True)
                if e.get("rasm"):
                    _rasm(d, e["rasm"], 7)
    elif t == "guruhlar":
        for g in mat["guruhlar"]:
            _p(d, g["nom"] + (": " + ", ".join(g["kartochkalar"]) if g.get("kartochkalar") else ""), after=2)


# ---------------------------------------------------------------- ilovalar
def _ilova(d, il: dict, dars: dict, miya: dict | None):
    k = il["kod"]
    gr = dars["guruhlash"]
    mas = dars.get("masalliq") or {}
    if k == "guruh_qoidalari":
        _royxat(d, gr["qoidalar"])
        _p(d, "Rollar:", bold=True, after=2)
        _royxat(d, [f"{r['rol']} — {r['vazifa']}" for r in gr["rollar"]])
    elif k == "baholash_varagi":
        b = dars["baholash"]
        _p(d, "Mezonlar:", bold=True, after=2)
        _royxat(d, b["mezonlar"])
        if b["ustunlar"]:
            kol = [3.5] + [max(1.6, 11.5 / len(b["ustunlar"]))] * len(b["ustunlar"]) + [2]
            jami = sum(kol)
            if jami > 17:
                kol = [x * 17 / jami for x in kol]
            _jadval(d, ["Guruh"] + [u[:24] for u in b["ustunlar"]] + ["Jami"], [[g] + [""] * (len(b["ustunlar"]) + 1) for g in b["guruhlar"]], kol, size=10)
            _p(d, f"Har bosqich — {b['max_ball']} ballgacha. {b['ragbat']}.", italic=True, size=10)
    elif k == "guruh_nomlari":
        for g in gr["guruhlar"]:
            if g.get("rasm") and _rasm(d, g["rasm"], 4):
                pass
            _p(d, g["nom"], bold=True, size=26, align=WD_ALIGN_PARAGRAPH.CENTER, after=14)
    elif k in ("tarqatma", "oyin_kartochkalari", "tayanch_konspekt"):
        bor = False
        for b in dars["bosqichlar"]:
            mt = b["material"]
            mos = (k == "tarqatma" and mt["tur"] in ("qismlar", "keys", "taqqoslash", "klaster", "xato", "jamoaviy")) or \
                  (k == "oyin_kartochkalari" and mt["tur"] in ("savollar", "atamalar", "bayonotlar", "ortiqcha", "topishmoq")) or \
                  (k == "tayanch_konspekt" and mt["tur"] in ("slaydlar", "qismlar"))
            if mos and il["raqam"] in b.get("ilova_raqam", []):
                _p(d, f"{b['nom']} — {b['metod']['nom'] if b['metod'] else ''}", bold=True, color=TOQ, after=2)
                _material(d, mt, kalit_bilan=(k != "tarqatma"))
                bor = True
        if not bor and k == "tayanch_konspekt" and mas.get("qismlar"):
            _material(d, {"tur": "qismlar", "qismlar": mas["qismlar"]})
            bor = True
        if not bor:   # mavzuda tayyor material yo'q — o'qituvchi to'ldiradigan kartochkalar namunasi
            _p(d, "Mavzu bo‘yicha savol va javoblarni kartochkalarga yozing (har guruhga bir to‘plam), qirqib tarqating.", italic=True)
            _jadval(d, [], [["Savol / topshiriq:\n\n\n", "Javob:\n\n\n"] for _ in range(6)], [8.5, 8.5], sarlavha=False)
    elif k == "test":
        for b in dars["bosqichlar"]:
            if b["material"]["tur"] == "test":
                _material(d, b["material"])
    elif k == "refleksiya_varagi":
        for b in dars["bosqichlar"]:
            if b["metod"] and b["material"]["tur"] == "royxat" and "refleksiya" in (om_tur(b["metod"]["kod"])):
                _p(d, b["metod"]["nom"], bold=True, after=2)
                for x in b["material"]["bandlar"]:
                    _p(d, f"{x}: ________________________________________", after=6)
                return
        for x in ("Bugun men bildimki…", "Menga qiyin bo‘ldi…", "Endi men qila olaman…"):
            _p(d, f"{x} ________________________________", after=6)
    elif k == "uy_vazifasi":
        _material(d, {"tur": "vazifalar", "vazifalar": dars.get("uy_vazifasi") or {}})
    elif k == "yoriqnoma_kartasi":
        tj = mas.get("tajriba") or {}
        if tj.get("bosqichlar"):
            _material(d, {"tur": "tajriba", "tajriba": tj})
        else:
            _royxat(d, ["Ish maqsadini o‘qing va gipotezangizni yozing.", "Jihozlarni tekshiring.", "Ishni bosqichma-bosqich bajaring.",
                        "Natijalarni jadvalga yozing.", "Xulosa chiqaring."], raqamli=True)
        _p(d, "Natijalar jadvali:", bold=True, after=2)
        _jadval(d, ["№", "O‘lchangan / kuzatilgan", "Natija", "Izoh"], [[i, "", "", ""] for i in range(1, 5)], [1, 7, 4, 5])
    elif k == "xavfsizlik":
        _royxat(d, ["Ish joyini toza va tartibli saqlang.", "Jihoz va moddalar bilan faqat o‘qituvchi ruxsati bilan ishlang.",
                    "Moddalarni hidlamang, tatib ko‘rmang; himoya ko‘zoynagi va qo‘lqopdan foydalaning.",
                    "Shisha idishlarni ehtiyotkorlik bilan ushlang; singan idishni o‘zingiz yig‘mang.",
                    "Ish tugagach jihozlarni joyiga qo‘ying, qo‘lingizni yuving."])
    elif k == "mehmon_varaqasi":
        mt = dars["meta"]
        _jadval(d, [], [["Fan", mt["fan"]], ["Sinf / guruh", mt["sinf"]], ["Mavzu", mt["mavzu"]], ["Dars turi", mt["andoza_nom"]],
                        ["Metodik maqsad", dars.get("metodik_maqsad") or ""]], [5, 12], sarlavha=False)
        _p(d, "Dars algoritmi:", bold=True, after=2)
        _royxat(d, [f"{b['nom']} — {b['daq']} daq." + (f" ({b['metod']['nom']})" if b["metod"] else "") for b in dars["bosqichlar"]], raqamli=True)
        _p(d, "Darsdan keyin savollaringiz uchun vaqt ajratilgan.", italic=True)
    elif k == "kuzatuv_varagi":
        mezon = (dars.get("tahlil") or {}).get("kuzatuv_mezonlari") or []
        _jadval(d, ["№", "Mezon", "Ball (0–2)", "Izoh"], [[i, m, "", ""] for i, m in enumerate(mezon, 1)], [1, 10, 2.5, 3.5], size=10)
        _p(d, "Umumiy xulosa va takliflar: _____________________________________________________________", after=6)
    elif k == "ozini_tahlil":
        _royxat(d, (dars.get("tahlil") or {}).get("ozini_tahlil_savollari") or [], raqamli=True)
    elif k == "adabiyotlar":
        a = ((miya or {}).get("adabiyotlar") or {})
        _royxat(d, [f"{x.get('muallif') or ''} {x.get('nomi') or ''}. {x.get('nashr') or ''}".strip() for x in a.get("asosiy") or []], raqamli=True)


def om_tur(kod: str) -> list:
    for m in om.METODLAR:
        if m["kod"] == kod:
            return m["tur"]
    return []


# ---------------------------------------------------------------- hujjat
def docx_yoz(dars: dict, miya: dict | None = None) -> bytes:
    mt = dars["meta"]
    otm = mt["yosh"] in om.OTM
    oquvchi = "Talaba" if otm else "O‘quvchi"
    d = _hujjat()
    # titul
    _p(d, "TASDIQLAYMAN", bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT, after=0)
    _p(d, ("Kafedra mudiri" if otm else "O‘quv ishlari bo‘yicha direktor o‘rinbosari") + ": ____________", align=WD_ALIGN_PARAGRAPH.RIGHT, after=0)
    _p(d, "«____» ______________ 20___ y.", align=WD_ALIGN_PARAGRAPH.RIGHT, after=40)
    _p(d, "______________________________________________", align=WD_ALIGN_PARAGRAPH.CENTER, after=0)
    _p(d, "(ta’lim muassasasi nomi)", italic=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, after=30)
    nom = {"ochiq": "OCHIQ DARS ISHLANMASI", "namunaviy": "NAMUNAVIY DARS ISHLANMASI"}.get(mt["format"], "DARS ISHLANMASI")
    if otm:
        nom = nom.replace("DARS", "MASHG‘ULOT")
    _p(d, nom, bold=True, size=24, align=WD_ALIGN_PARAGRAPH.CENTER, after=14, color=TOQ)
    _p(d, f"«{mt['mavzu']}»", bold=True, size=18, align=WD_ALIGN_PARAGRAPH.CENTER, after=14)
    _p(d, f"Fan: {mt['fan']}    {'Kurs' if otm else 'Sinf'}: {mt['sinf']}", size=14, align=WD_ALIGN_PARAGRAPH.CENTER, after=20)
    _rasm(d, mt.get("rasm"), 9)
    _p(d, "", after=30)
    _p(d, "O‘qituvchi: ______________________________", align=WD_ALIGN_PARAGRAPH.RIGHT, after=4)
    _p(d, "Sana: ____________", align=WD_ALIGN_PARAGRAPH.RIGHT, after=4)
    _sahifa(d)

    # umumiy ma'lumot
    d.add_heading("Dars haqida umumiy ma’lumot" if not otm else "O‘quv mashg‘ulotida ta’lim texnologiyasi modeli", level=1)
    metodlar = list(dict.fromkeys(b["metod"]["nom"] for b in dars["bosqichlar"] if b["metod"]))
    ng = len(dars["guruhlash"]["guruhlar"])
    qator = [["Fan", mt["fan"]], ["Kurs" if otm else "Sinf", mt["sinf"]], ["Mavzu", mt["mavzu"]],
             ["Dars formati", mt["format_nom"]], ["Dars turi", mt["andoza_nom"]], ["Davomiyligi", f"{mt['daqiqa']} daqiqa"],
             [f"{oquvchi}lar soni", f"{mt['oquvchilar']} nafar, {ng} guruh ({dars['guruhlash']['nom'].lower()})"]]
    if dars.get("metodik_maqsad"):
        qator.append(["Metodik maqsad", dars["metodik_maqsad"]])
    qator += [["Ta’lim usullari (metodlar)", ", ".join(metodlar)], ["Ta’lim shakli", "jamoaviy, guruhli, juftlikda va yakka"],
              ["Ta’lim vositalari", ", ".join(dars["jihozlar"])], ["Monitoring va baholash", "; ".join(dars["baholash"]["mezonlar"][:3])]]
    _jadval(d, [], qator, [5, 12], sarlavha=False)

    d.add_heading("Darsning maqsadlari", level=1)
    mq = dars["maqsadlar"]
    _yorliq(d, "Ta’limiy:", mq["talimiy"])
    _yorliq(d, "Tarbiyaviy:", mq["tarbiyaviy"])
    _yorliq(d, "Rivojlantiruvchi:", mq["rivojlantiruvchi"])
    _p(d, "Shakllantiriladigan kompetensiyalar:", bold=True, after=2)
    _royxat(d, dars["kompetensiyalar"])
    _p(d, "Kutilgan natijalar — " + oquvchi.lower() + ":", bold=True, after=2)
    _royxat(d, dars["natijalar"])

    # texnologik xarita
    d.add_heading("Darsning texnologik xaritasi", level=1)
    qat = []
    for i, b in enumerate(dars["bosqichlar"]):
        mtd = (b["metod"]["nom"] if b["metod"] else "") + (f" ({', '.join(f'{n}-ilova' for n in b.get('ilova_raqam') or [])})" if b.get("ilova_raqam") else "")
        qat.append([RIM[i], f"{b['nom']} ({b['daq']} daq.)", b["oqituvchi"].split(". «")[0], b["oquvchi"], mtd])
    _jadval(d, ["№", "Bosqich", "O‘qituvchi faoliyati", f"{oquvchi} faoliyati", "Metod, ilova"], qat, [1, 3.5, 5.5, 3.5, 3.5], size=10)

    # darsning borishi
    d.add_heading("Darsning borishi", level=1)
    korilgan: dict = {}
    for i, b in enumerate(dars["bosqichlar"]):
        d.add_heading(f"{RIM[i]}. {b['nom']} ({b['daq']} daqiqa)", level=2)
        if b["metod"]:
            _yorliq(d, "Metod:", b["metod"]["nom"] + (f" ({', '.join(f'{n}-ilova' for n in b.get('ilova_raqam') or [])})" if b.get("ilova_raqam") else ""))
            if len(b["metod"]["qadamlar"]) > 1:
                _royxat(d, b["metod"]["qadamlar"], raqamli=True)
            else:
                _p(d, b["metod"]["qadamlar"][0])
        if b.get("nutq"):
            _yorliq(d, "O‘qituvchi:", b["nutq"])
        _yorliq(d, f"{oquvchi}lar:", b["oquvchi"])
        if b["material"]["tur"] not in ("yoq",):
            iz = repr(sorted((k, repr(v)) for k, v in b["material"].items() if k != "guruh"))
            if iz in korilgan:
                _p(d, f"Material: {korilgan[iz]}-bosqichdagi topshiriqlar natijasi asosida.", italic=True)
            else:
                korilgan[iz] = RIM[i]
                _material(d, b["material"])
        if b.get("rasm"):
            _rasm(d, b["rasm"], 8)
        if b.get("izoh"):
            _p(d, b["izoh"], italic=True, size=11, color=RGBColor(0x55, 0x55, 0x55))

    if dars.get("tayyorgarlik"):
        d.add_heading("Ochiq darsga tayyorgarlik", level=1)
        _royxat(d, [f"{x['qachon']} — {x['ish']}" for x in dars["tayyorgarlik"]])

    # ilovalar
    for il in dars["ilovalar"]:
        _sahifa(d)
        d.add_heading(f"{il['raqam']}-ilova. {il['nom']}", level=1)
        _ilova(d, il, dars, miya)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()
