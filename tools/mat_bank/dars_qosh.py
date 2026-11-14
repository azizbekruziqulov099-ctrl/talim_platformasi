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

BOLIMLAR = ["MAQSAD", "OLDIN BIL", "TUSHUNCHA", "MISOL TAHLILI", "KO'P UCHRAYDIGAN XATOLAR", "ESDA TUT", "O'ZINI TEKSHIR"]
IXTIYORIY = ["MATEMATIKA TARIXI"]      # ixtiyoriy: bo'sh vaqtda o'qish uchun qisqa tarixiy ma'lumot (3–8 gap; aniq ism, sana, asar — ishonchsiz bo'lsa [TEKSHIR])
TARIX_ENG_UZUN = 1600
VIDJETLAR = {"GRAFIK", "INTEGRAL", "BIRLIK_AYLANA", "DOSKA"}      # virtual doska: frontend src/matbank/vidjetRules.js bilan bir xil qoidalar
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
    xat = [x for x in re.split(r"\n(?=\s*\d+\\?\.\s)", r["bolim"]["KO'P UCHRAYDIGAN XATOLAR"]) if x.strip()]
    if len(xat) < 2:
        xato.append("KO'P UCHRAYDIGAN XATOLAR da kamida 2 ta band («1. … 2. …») bo'lsin")
    if len([x for x in r["bolim"]["ESDA TUT"].split("\n") if x.strip()]) < 2:
        xato.append("ESDA TUT da kamida 2 qator bo'lsin")
    if xato:
        return xato, ogoh
    butun = "\n".join(r["bolim"].values())
    d = {"nom": m["nom"], "bob": r["bob"] or m.get("bob") or "", "maqsad": r["bolim"]["MAQSAD"], "oldin_bil": r["bolim"]["OLDIN BIL"],
         "tushuncha": [{"sarlavha": a, "matn": b} for a, b in tush], "misollar": mis, "xatolar": r["bolim"]["KO'P UCHRAYDIGAN XATOLAR"], "esda_tut": r["bolim"]["ESDA TUT"],
         "tekshir_manbalar": tek, "tarix": tarix, "tekshir": bool(re.search(TEKSHIR, butun))}
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
