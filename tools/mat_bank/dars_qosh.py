"""REV564: Repetitor «miyasi» — har mavzu uchun tushunarli DARS (nazariya) fayllarini bankka qo'shish.

Ishlatish:  python tools/mat_bank/dars_qosh.py <bank.json> <dars.json> <KABUTAR_DARS_100_100.docx|.md> […]
Fayl formati (docx yoki md; sarlavhalar «## **NOM**» yoki «## NOM»):
  # DARS: 100 | ROMB            (raqam fayl nomidan: KABUTAR_DARS_100_100; nom bankdagi bilan mos bo'lsin)
  BOB: 3-bob. PLANIMETRIYA      (ixtiyoriy)
  ## MAQSAD · ## OLDIN BIL · ## TUSHUNCHA (### 1. Nom — kamida 2 ta) · ## MISOL TAHLILI (### Misol 1 | TUR 2 | (97-3-47) — G'OYA, qadamlar, JAVOB: X)
  ## KO'P UCHRAYDIGAN XATOLAR · ## ESDA TUT · ## O'ZINI TEKSHIR ((96-7-47) (97-7-47) … — 3–6 ta manba kodi)
Misol SAVOLINI GPT yozmaydi: dars faqat manba kodini beradi, savol va variantlarni server bankdan qo'yadi.
QATTIQ TEKSHIRUV (xato bo'lsa fayl qo'shilmaydi): bo'limlar bor; misol va o'zini-tekshir kodlari bankda shu mavzuda bor va [TEKSHIR] emas;
  misol JAVOBI bank kaliti bilan bir xil; TUR bankdagi bilan mos; o'zini-tekshir savollari misollardan FARQLI (aks holda javobi ko'rinib qoladi).
[TEKSHIR] belgisi bor dars saqlanadi, lekin o'quvchiga ko'rsatilmaydi (o'qituvchi ko'rib chiqadi).
Taxmin qilib bo'lmaydigan narsa: nazariya matnining ILMIY TO'G'RILIGI — uni dasturchi emas, o'qituvchi ko'rib chiqadi.
"""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_chizma as GEO   # noqa: E402  — aniq geometrik chizma (REV566)

BOLIMLAR = ["MAQSAD", "OLDIN BIL", "TUSHUNCHA", "MISOL TAHLILI", "KO'P UCHRAYDIGAN XATOLAR", "ESDA TUT", "O'ZINI TEKSHIR"]
IXTIYORIY = ["MATEMATIKA TARIXI"]      # ixtiyoriy: bo'sh vaqtda o'qish uchun qisqa tarixiy ma'lumot (3–8 gap; aniq ism, sana, asar — ishonchsiz bo'lsa [TEKSHIR])
TARIX_ENG_UZUN = 1600
VIDJETLAR = {"GRAFIK", "INTEGRAL", "BIRLIK_AYLANA", "DOSKA", "CHIZMA"}      # virtual doska: frontend src/matbank/vidjetRules.js bilan bir xil qoidalar
VID_QATOR = re.compile(r"^\s*\[\[\s*([A-Z_]+)\s*(?::\s*(.*?))?\s*\]\]\s*$")
SON = r"-?\d+(?:[.,]\d+)?"
TEKSHIR = r"\\?\[TEKSHIR\\?\]"
KOD = re.compile(r"\((\d{2,4}-\d+-\d+)\)")


def vidjet_xatosi(tur, arg):
    """[[TUR: arg]] qatori to'g'rimi → xato matni yoki None. Ifodaning MA'NOSINI frontend testi tekshiradi; bu yerda — tuzilma, belgilar, qavslar, oraliq va parametrlar."""
    if tur not in VIDJETLAR:
        return f"noma'lum virtual doska: {tur}"
    arg = (arg or "").strip()
    if tur == "DOSKA":
        return None
    if tur == "CHIZMA":
        try:
            GEO.coz(arg)
        except GEO.GeoXato as e:
            return str(e)
        return None
    if tur == "BIRLIK_AYLANA":
        try:
            v = float(arg.replace(",", ".")) if arg else 30.0
        except ValueError:
            return "BIRLIK_AYLANA: burchak son bo'lsin"
        return None if 0 <= v <= 360 else "BIRLIK_AYLANA: burchak 0–360 bo'lsin"
    bo = [x.strip() for x in arg.split("|")]
    ifoda = re.sub(r"^\s*[yf](\(x\))?\s*=\s*", "", bo[0], flags=re.I)
    if not ifoda or len(ifoda) > 120 or not re.fullmatch(r"[0-9A-Za-z+\-*/^().,\sπ]+", ifoda) or "=" in ifoda:
        return f"{tur}: ifoda noto'g'ri («{bo[0]}»)"
    if ifoda.count("(") != ifoda.count(")") or not re.search(r"\bx\b|(?<![A-Za-z])x(?![A-Za-z])", ifoda):
        return f"{tur}: ifodada qavslar teng emas yoki x yo'q («{bo[0]}»)"
    oraliqlar = 0
    for q in bo[1:]:
        if "=" in q:
            if not all(re.fullmatch(r"\s*[A-Za-z]\s*=\s*-?\d+(?:\.\d+)?\s*", x) for x in q.split(",")):
                return f"{tur}: parametr «{q}» noto'g'ri («a=1, b=-2»; o'nli kasr — nuqta bilan)"
            continue
        m = re.fullmatch(rf"({SON})\s*\.\.\s*({SON})", q)
        if not m or float(m.group(1).replace(",", ".")) >= float(m.group(2).replace(",", ".")):
            return f"{tur}: oraliq «{q}» noto'g'ri («-4..6», birinchi son kichik)"
        oraliqlar += 1
    if tur == "INTEGRAL" and oraliqlar < 1:
        return "INTEGRAL: integral chegaralari kerak («0..2»)"
    return None


def lx_norm(s):
    """LaTeX yozuvini solishtirish uchun yagona ko'rinishga: bo'shliq, \\left/\\right, \\cdot, bitta belgili {…} qavslar farqi hisobga olinmaydi."""
    s = re.sub(r"\\(left|right|bigl|bigr|Big|big)(?![A-Za-z])", "", s)
    s = s.replace("\\dfrac", "\\frac").replace("\\cdot", "*").replace("\\times", "*").replace("\\,", "").replace("\\;", "").replace("\\!", "")
    for a, b in (("\\bot", "\\perp"), ("\\lbrack", "["), ("\\rbrack", "]"), ("\\prime", "'"), ("\\leqslant", "\\leq"), ("\\geqslant", "\\geq"), ("\\operatorname{tg}", "tg"), ("\\operatorname{ctg}", "ctg")):
        s = s.replace(a, b)
    s = re.sub(r"\\le(?![A-Za-z])", r"\\leq", s)
    s = re.sub(r"\\ge(?![A-Za-z])", r"\\geq", s)
    s = re.sub(r"\s+", "", s)
    return re.sub(r"\{(\w)\}", r"\1", s)


def _qavssiz(f):
    """Butun formulani o'rab turgan BIR juft qavsni olib tashlaydi: «(n \\neq -1)» → «n \\neq -1»; «(a+b)(c+d)» ga tegmaydi."""
    if f.startswith("(") and f.endswith(")"):
        d = 0
        for i, c in enumerate(f):
            d += (c == "(") - (c == ")")
            if d == 0 and i < len(f) - 1:
                return f
        return f[1:-1].strip()
    return f


def formulalar(matn):
    out = []
    for m in re.finditer(r"\$\$(.+?)\$\$|\$([^$\n]+?)\$", matn or "", re.S):
        for f in re.split(r"(?:\s*,?\s*\\q?quad)+", (m.group(1) or m.group(2)).strip()):     # «A,\\quad B» — ikki formula
            f = f.strip().rstrip(".,;")
            f = _qavssiz(f)
            if f:
                out.append(f)
    return out


FUNKSIYA_KITOB = re.compile(r"^(1\.1[234]|2\.1\.(1[0-3]|[5-9])|2\.2|2\.3)")      # funksiya, trigonometriya, hosila, integral bo'limlari: virtual doska foydali


def repetitor_tahlili(m, d, kod):
    """Repetitor darajasi uchun SIFAT ogohlantirishlari (xato emas — dars qabul qilinadi, lekin GPT/o'qituvchi shularni to'g'rilaydi). → [matn]."""
    og = []
    butun = [d["maqsad"], d["oldin_bil"], d["xatolar"], d["esda_tut"], *[t["matn"] for t in d["tushuncha"]], *[x["matn"] for x in d["misollar"]]]
    dars_f = "|".join(lx_norm(f) for t in butun for f in formulalar(t))
    # 1) manbadagi qoida formulalari darsda bormi
    yoq = []
    for f in formulalar(m.get("qoida", "")):
        n = lx_norm(f)
        if len(n) >= 5 and not re.fullmatch(r"[\d.,+\-*/=()]+", n) and n not in dars_f:
            yoq.append(f)
    if yoq:
        og.append(f"manbadagi qoidaning {len(yoq)} ta formulasi darsda topilmadi: " + "; ".join(f"${x[:48]}$" for x in yoq[:4]) + (" …" if len(yoq) > 4 else ""))
    # 2) TUR xilma-xilligi (bankda TUR belgisi bo'lsa)
    turlar = sorted({t["tur"] for t in m["testlar"] if t.get("tur") and not t.get("tekshir")})
    olingan = {x["tur"] for x in d["misollar"] if x.get("tur")}
    if len(turlar) >= 4 and len(olingan) < min(len(turlar), 4):
        og.append(f"misollar bankdagi {len(turlar)} xil turdan faqat {len(olingan)} tasini qamraydi: yana boshqa TURdan misol qo'shing")
    # 3) qiyinlik asta-sekin oshsin; qiyinroq misolda qadamlar ko'proq bo'lsin
    daraja = {"O": 1, "R": 2, "Q": 3}; qs = [daraja.get((kod.get(x["manba"]) or {}).get("qiyinlik"), 0) for x in d["misollar"]]
    if all(qs) and qs != sorted(qs):
        og.append("misollar qiyinligi oshib bormaydi (oson → o'rta → qiyin tartibida bo'lsin)")
    for x, q in zip(d["misollar"], qs):
        if q >= 2 and len(re.findall(r"\d+-qadam", x["matn"])) < 3:
            og.append(f"misol ({x['manba']}): o'rta/qiyin misolda kamida 3 qadam bo'lsin")
    # 4) o'qilishi oson: gap uzunligi
    uzun = []
    for t in [d["maqsad"], *[b["matn"] for b in d["tushuncha"]], d["xatolar"]]:
        plain = re.sub(r"\$[^$]*\$", "F", t)
        for g in re.split(r"(?<=[.!?:])\s+|\n+", plain):
            if len(g.split()) > 30:
                uzun.append(g[:50])
    if uzun:
        og.append(f"{len(uzun)} ta gap 30 so'zdan uzun (qisqartiring): «{uzun[0]}…»")
    # 5) virtual doska va tarix
    vid = any(VID_QATOR.match(re.sub(r"\\([\[\]_*^])", r"\1", q)) for t in butun for q in t.split("\n"))
    if not vid and FUNKSIYA_KITOB.match(str(m.get("kitob") or "")):
        og.append("bu mavzuda virtual doska tavsiya etiladi ([[GRAFIK: …]], [[INTEGRAL: …]] yoki [[BIRLIK_AYLANA]])")
    if not d.get("tarix"):
        og.append("«MATEMATIKA TARIXI» bo'limi yo'q (ixtiyoriy, lekin tavsiya etiladi)")
    if not d.get("geo") and re.match(r"^[34]\.", str(m.get("kitob") or "")):
        og.append("geometriya mavzusida aniq chizma tavsiya etiladi ([[CHIZMA: romb a=5 d1=6 d2=8]] kabi; hisoblangan, masshtabli)")
    # 6) «oldin bil»dagi mavzu raqamlari bankda bormi
    for n in re.findall(r"\((\d{1,3})-mavzu\)", d["oldin_bil"]):
        pass
    return og


KATEX_NOMZODLAR = ["KATEX_YOLI", "../talim_platformasi_frontend/node_modules/katex/dist/katex.mjs", "../../../talim_platformasi_frontend/node_modules/katex/dist/katex.mjs", "/tmp/cleanb2/node_modules/katex/dist/katex.mjs"]
KATEX_JS = """import fs from 'node:fs'; const k = (await import(process.argv[2])).default;
const L = JSON.parse(fs.readFileSync(process.argv[3], 'utf8')); const x = [];
for (const f of L) { try { k.renderToString(f.e, { displayMode: f.d, throwOnError: true, strict: 'ignore', trust: false, maxExpand: 1000 }); } catch (e) { x.push(f.e.slice(0, 70) + ' — ' + String(e.message).slice(0, 70)); } }
console.log(JSON.stringify(x));"""


def katex_yoli():
    for n in KATEX_NOMZODLAR:
        y = os.environ.get(n) if n == "KATEX_YOLI" else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", n) if not n.startswith("/") else n
        if y and os.path.isfile(y):
            return os.path.abspath(y)
    return None


def formula_chizilmaganlar(matnlar):
    """KaTeX chiza olmaydigan formulalar ro'yxati; KaTeX topilmasa — None (tekshirilmadi)."""
    yol = katex_yoli()
    if not yol:
        return None
    L = []
    for t in matnlar:
        for m in re.finditer(r"\$\$(.+?)\$\$|\$([^$\n]+?)\$", t or "", re.S):
            L.append({"d": m.group(1) is not None, "e": (m.group(1) or m.group(2)).strip()})
    if not L:
        return []
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        fj, fs_ = os.path.join(tmp, "f.json"), os.path.join(tmp, "k.mjs")
        json.dump(L, open(fj, "w", encoding="utf8"), ensure_ascii=False); open(fs_, "w", encoding="utf8").write(KATEX_JS)
        r = subprocess.run(["node", fs_, "file://" + yol, fj], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return None
        return json.loads(r.stdout.strip().splitlines()[-1])


def norm_nom(s):
    return re.sub(r"[^a-z0-9]+", "", re.sub(r"[‘’ʻʼ`´]", "'", s or "").casefold().replace("'", ""))


def bolim_nomi(s):
    t = re.sub(r"^#+\s*|\*\*|\\", "", s).strip().rstrip(".:")
    t = re.sub(r"[‘’ʻʼ`´]", "'", t).upper()
    return t


def oqi(md):
    L = md.replace("\r", "").split("\n")
    h = next((l for l in L if re.match(r"^#\s", l)), "")
    m = re.match(r"^#\s*\**DARS:\s*(\d+)\s*\\?\|\s*(.+?)\**\s*$", h)
    if not m:
        raise ValueError("«# DARS: 100 | NOM» sarlavhasi topilmadi")
    sar = [(i, l) for i, l in enumerate(L) if re.match(r"^##\s", l)]
    bosh = "\n".join(L[: sar[0][0]] if sar else L)
    mb = re.search(r"^\**BOB:\s*(.+?)\**\s*$", bosh, re.M)
    r = {"raqam": int(m.group(1)), "nom": m.group(2).strip(), "bob": mb.group(1).strip() if mb else "", "bolim": {}}
    for k, (i, l) in enumerate(sar):
        oxir = sar[k + 1][0] if k + 1 < len(sar) else len(L)
        r["bolim"][bolim_nomi(l)] = "\n".join(L[i + 1:oxir]).strip()
    return r


def kichiklar(matn, daraja="###"):
    """### sarlavha bo'yicha bo'laklar: [(sarlavha, matn)]."""
    out, cur = [], None
    for l in matn.split("\n"):
        if re.match(r"^" + daraja + r"\s", l):
            cur = [re.sub(r"^#+\s*|\*\*", "", l).strip(), []]; out.append(cur)
        elif cur is not None:
            cur[1].append(l)
    return [(a, "\n".join(b).strip()) for a, b in out]


def tekshir_va_qosh(bank, raqam, r, dars):
    """→ (xatolar, ogohlar). xatolar bo'sh bo'lsa dars['darslar'][raqam] yoziladi."""
    xato, ogoh = [], []
    m = next((x for x in bank["mavzular"] if x["raqam"] == raqam), None)
    if not m:
        return [f"bankda {raqam}-mavzu yo'q"], ogoh
    if r["raqam"] != raqam:
        xato.append(f"sarlavhadagi raqam ({r['raqam']}) fayl nomidagi ({raqam}) bilan mos emas")
    if norm_nom(r["nom"]) != norm_nom(m["nom"]):
        xato.append(f"mavzu nomi mos emas: fayl «{r['nom']}», bank «{m['nom']}»")
    for b in BOLIMLAR:
        if not r["bolim"].get(b):
            xato.append(f"«{b}» bo'limi yo'q yoki bo'sh")
    if xato:
        return xato, ogoh
    kod = {t["manba"]: t for t in m["testlar"]}
    tush = kichiklar(r["bolim"]["TUSHUNCHA"])
    if len(tush) < 2:
        xato.append("TUSHUNCHA da kamida 2 ta «### 1. Nom» bandi bo'lsin")
    mis, ishlatilgan = [], set()
    bl = kichiklar(r["bolim"]["MISOL TAHLILI"])
    if len(bl) < 2:
        xato.append("MISOL TAHLILI da kamida 2 ta misol («### Misol 1 | TUR 2 | (97-3-47)») bo'lsin")
    elif len(bl) < 3:
        ogoh.append("misollar 3 tadan kam")
    for sar, matn in bl:
        mk = KOD.search(sar)
        if not mk:
            xato.append(f"«{sar}»: sarlavhada (manba kodi) yo'q"); continue
        t = kod.get(mk.group(1))
        if not t:
            xato.append(f"misol ({mk.group(1)}): bankning {raqam}-mavzusida bunday test yo'q"); continue
        if t.get("tekshir"):
            xato.append(f"misol ({mk.group(1)}): bu test manbada nuqsonli ([TEKSHIR]) — misol qilib bo'lmaydi"); continue
        mt = re.search(r"TUR\s*(\d+)", sar)
        if mt and t.get("tur") and int(mt.group(1)) != t["tur"]:
            xato.append(f"misol ({mk.group(1)}): TUR {mt.group(1)} ≠ bankdagi TUR {t['tur']}")
        mj = re.search(r"JAVOB:\**\s*([A-E])\b", matn)
        if not mj:
            xato.append(f"misol ({mk.group(1)}): «JAVOB: X» yo'q")
        elif mj.group(1) != t["javob"]:
            xato.append(f"misol ({mk.group(1)}): javob {mj.group(1)} ≠ manba kaliti {t['javob']}")
        if not re.search(r"G.OYA:", matn):
            xato.append(f"misol ({mk.group(1)}): «G'OYA:» yo'q (bitta gapda asosiy fikr)")
        if len(re.findall(r"\d+-qadam", matn)) < 2:
            ogoh.append(f"misol ({mk.group(1)}): 2 tadan kam qadam")
        ishlatilgan.add(mk.group(1))
        mis.append({"manba": mk.group(1), "tur": t.get("tur"), "nom": re.sub(r"\s*\|\s*", " · ", re.sub(r"\s*\|\s*\(.*$", "", sar).strip()), "matn": matn})
    tek = list(dict.fromkeys(KOD.findall(r["bolim"]["O'ZINI TEKSHIR"])))
    if not 3 <= len(tek) <= 6:
        xato.append(f"O'ZINI TEKSHIR da 3–6 ta manba kodi bo'lsin (hozir {len(tek)})")
    for k in tek:
        if k not in kod:
            xato.append(f"o'zini tekshir ({k}): bankda yo'q")
        elif kod[k].get("tekshir"):
            xato.append(f"o'zini tekshir ({k}): nuqsonli ([TEKSHIR]) test")
        elif k in ishlatilgan:
            xato.append(f"o'zini tekshir ({k}): bu savol misolda yechib bo'lingan — boshqa savol tanlang")
    tarix = (r["bolim"].get("MATEMATIKA TARIXI") or "").strip()
    if len(tarix) > TARIX_ENG_UZUN:
        xato.append(f"MATEMATIKA TARIXI {TARIX_ENG_UZUN} belgidan oshmasin (hozir {len(tarix)}): qisqa va aniq yozing")
    for nom_, matn_ in r["bolim"].items():
        for qator in matn_.split("\n"):
            q2 = re.sub(r"\\([\[\]_*^])", r"\1", qator)
            mv = VID_QATOR.match(q2)
            if mv:
                e = vidjet_xatosi(mv.group(1), mv.group(2))
                if e:
                    xato.append(f"{nom_}: «{qator.strip()[:60]}» — {e}")
    geo = {}
    for matn_ in r["bolim"].values():
        for qator in matn_.split("\n"):
            mv = VID_QATOR.match(re.sub(r"\\([\[\]_*^])", r"\1", qator))
            if mv and mv.group(1) == "CHIZMA":
                try:
                    f = GEO.coz(mv.group(2)); geo[f["arg"]] = f
                except GEO.GeoXato:
                    pass        # xato yuqorida yig'ilgan
    xat = [x for x in re.split(r"\n(?=\s*\d+\\?\.\s)", r["bolim"]["KO'P UCHRAYDIGAN XATOLAR"]) if x.strip()]
    if len(xat) < 2:
        xato.append("KO'P UCHRAYDIGAN XATOLAR da kamida 2 ta band («1. … 2. …») bo'lsin")
    if len([x for x in r["bolim"]["ESDA TUT"].split("\n") if x.strip()]) < 2:
        xato.append("ESDA TUT da kamida 2 qator bo'lsin")
    if xato:
        return xato, ogoh
    chiz = formula_chizilmaganlar(list(r["bolim"].values()))
    if chiz is None:
        ogoh.append("formulalarning chizilishi tekshirilmadi (KaTeX topilmadi: KATEX_YOLI muhit o'zgaruvchisi)")
    elif chiz:
        return [f"formula chizilmaydi: {c}" for c in chiz[:6]], ogoh
    butun = "\n".join(r["bolim"].values())
    d = {"nom": m["nom"], "bob": r["bob"] or m.get("bob") or "", "maqsad": r["bolim"]["MAQSAD"], "oldin_bil": r["bolim"]["OLDIN BIL"],
         "tushuncha": [{"sarlavha": a, "matn": b} for a, b in tush], "misollar": mis, "xatolar": r["bolim"]["KO'P UCHRAYDIGAN XATOLAR"], "esda_tut": r["bolim"]["ESDA TUT"],
         "tekshir_manbalar": tek, "tarix": tarix, "geo": geo, "tekshir": bool(re.search(TEKSHIR, butun))}
    ogoh.extend(repetitor_tahlili(m, d, kod))
    dars.setdefault("darslar", {})[str(raqam)] = d
    if d["tekshir"]:
        ogoh.append("darsda [TEKSHIR] belgisi bor: saqlandi, lekin o'quvchiga ko'rsatilmaydi")
    return [], ogoh


def main(bank_yoli, dars_yoli, fayllar):
    bank = json.load(open(bank_yoli, encoding="utf8"))
    dars = json.load(open(dars_yoli, encoding="utf8")) if os.path.exists(dars_yoli) else {"darslar": {}}
    ok_hammasi = True
    for f in fayllar:
        mn = re.search(r"KABUTAR_DARS_(\d+)_(\d+)", os.path.basename(f))
        if not mn or mn.group(1) != mn.group(2):
            print(f"✗ {os.path.basename(f)}: fayl nomi KABUTAR_DARS_<raqam>_<raqam> (bitta mavzu) bo'lsin"); ok_hammasi = False; continue
        try:
            if f.lower().endswith(".md"):
                md = open(f, encoding="utf8").read()
            else:
                rr = subprocess.run(["pandoc", os.path.abspath(f), "-t", "markdown", "--wrap=none"], capture_output=True, text=True, timeout=180)
                if rr.returncode != 0:
                    raise RuntimeError(rr.stderr[:200])
                md = rr.stdout
            xato, ogoh = tekshir_va_qosh(bank, int(mn.group(1)), oqi(md), dars)
        except Exception as e:   # noqa: BLE001
            xato, ogoh = [f"o'qib bo'lmadi: {e}"], []
        if xato:
            ok_hammasi = False; print(f"✗ {os.path.basename(f)} — QO'SHILMADI ({len(xato)} xato):"); [print("    •", x) for x in xato[:14]]
        else:
            d = dars["darslar"][str(int(mn.group(1)))]
            print(f"✓ {os.path.basename(f)} — {mn.group(1)}-mavzu: {len(d['tushuncha'])} band, {len(d['misollar'])} misol, {len(d['tekshir_manbalar'])} o'zini-tekshir savoli" + (" [TEKSHIR]" if d["tekshir"] else ""))
        for o in ogoh:
            print("    ⚠", o)
    json.dump(dars, open(dars_yoli, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    return ok_hammasi


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1], sys.argv[2], sys.argv[3:]) else 1)
