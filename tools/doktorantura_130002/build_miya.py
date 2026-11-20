#!/usr/bin/env python3
"""13.00.02 (tayanch doktorantura) — sxema va dars matnlaridan saytga yuklanadigan paket yasaydi.

Chiqish (out/):
  13_00_02_mavzular.xlsx          — yozilgan darslar (Sinf: Doktorantura, Bob = bo'lim, Mavzu = «1.1-a. …» / «1.2. …»)
  13_00_02_<n>-bolim_ai_miya.xlsx — mavzu varoqli AI miya: qisqa dars qadamlari + javob namunasi + Esda tut + Kabu testlari
  13_00_02_doktorantura_paket.zip — «Paketni birdan o'rnatish» uchun

Bitta savol 1–3 ta qisqa darsga bo'linadi. Dars matni fayli (darslar/s<n>.txt) formati:
  ### 1.1-a | Fan va maqsad   — savolning a-qismi (sarlavhasi bilan); bo'linmagan savol: «### 1.2»
  @kirish            — o'qituvchi kirish so'zi; doskaga savol, qism va KOD avtomatik yoziladi
  @qadam <sarlavha>  — 3–5 ta qadam: «| » bilan boshlangan satrlar doskaga, qolganlari o'qituvchi gapi
                       Doska buyruqlari: KOD: Q=… | M=…   SXEMA: Markaz > a | b   ZANJIR: 1992 :: izoh | 1997 :: izoh
                       JADVAL: A | B ;; a | b   QOIDA: … («Esda tut» burchagiga). Rangli so'z: [s]sariq[/s] [k]ko'k[/k] [y]yashil[/y] [p]pushti[/p]
  @sodda / @boshqa   — «Tushunmadim» tugmalari uchun (oldingi qadamga)
  @tekshiruv Savol? => to'g'ri | xato | xato   (oldingi qadamga)
  @javob             — imtihon javobi namunasi (savolning OXIRGI qismida): har satr «doskaga || o'qituvchi aytadi»
  @esda              — Esda tut: «| » satrlar doskaga, qolgani gap
  @test oson|o'rta|qiyin — har darsda 5–6 ta; darsga oson → o'rta → qiyin tartibida chiqadi
    savol matni …
    A) …  B) …  C) …  D) …
    = B
    A: nega noto'g'ri   (har noto'g'ri variantga)
    ? to'g'ri javob izohi
"""
import io, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))   # talim_platformasi (modules/ai_miya_varoq.py)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)
import build as SX                                   # sxema ma'lumotlari (data/s*.txt) va THEMES
from modules.ai_miya_varoq import template_workbook, parse_sheets

FAN = "13.00.02 – Ta’lim va tarbiya nazariyasi va metodikasi"
SINF = "Doktorantura"
PREF = {1: "DKA", 2: "DKB", 3: "DKC", 4: "DKD", 5: "DKE", 6: "DKF", 7: "DKG"}
L = "ABCDEF"


def uz(s):
    """o' g' → o‘ g‘, qolgan ' → ’ (sxemadagi bilan bir xil)."""
    return SX.uz(s or "")


def plain(s):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", uz(s))


def mavzu_nomi(key, it, d):
    """«1.1-a. Fan va maqsad» (qism) yoki «1.2. <savol>» (bo'linmagan)."""
    return f"{key}. {uz(d['sarlavha'])}" if d.get("qism") else f"{key}. {plain(it['q'])}"


def bolim_nomi(sec):
    t = plain(sec["title"]).lower()
    t = t[:1].upper() + t[1:]
    t = re.sub(r"(?<=\s)(o‘quv|ta’lim)", lambda m: m.group(1), t)
    return f"{sec['n']}-bo‘lim. {t}"


# ───────────────────────── dars matni fayli ─────────────────────────
def parse_darslar(path):
    if not os.path.exists(path):
        return {}
    out, cur, blk = {}, None, None
    for raw in open(path, encoding="utf-8").read().splitlines():
        line = raw.rstrip()
        m = re.match(r"^###\s+(\d+\.\d+)(?:-([a-z]))?\s*(?:\|\s*(.+?))?\s*$", line)
        if m:
            key = m.group(1) + (f"-{m.group(2)}" if m.group(2) else "")
            if key in out:
                raise ValueError(f"{path}: {key} ikki marta")
            if bool(m.group(2)) != bool(m.group(3)):
                raise ValueError(f"{path}: {key} — qismli darsga sarlavha kerak («### 1.1-a | Sarlavha»)")
            cur = out[key] = {"savol": m.group(1), "qism": m.group(2) or "", "sarlavha": (m.group(3) or "").strip(), "kirish": "",
                              "qadamlar": [], "javob": [], "esda": {"doska": [], "matn": []}, "testlar": []}
            blk = None
            continue
        if cur is None or (not line.strip() and blk is None):
            continue
        m = re.match(r"^@(\w+)\s*(.*)$", line)
        if m:
            tur, arg = m.group(1), m.group(2).strip()
            if tur == "kirish":
                blk = ("kirish", None)
            elif tur == "qadam":
                cur["qadamlar"].append({"sarlavha": arg, "doska": [], "matn": [], "sodda": [], "boshqa": [], "tekshiruv": ""})
                blk = ("qadam", cur["qadamlar"][-1])
            elif tur in ("sodda", "boshqa"):
                blk = (tur, cur["qadamlar"][-1])
            elif tur == "tekshiruv":
                cur["qadamlar"][-1]["tekshiruv"] = arg
                blk = None
            elif tur == "javob":
                blk = ("javob", None)
            elif tur == "esda":
                blk = ("esda", None)
            elif tur == "test":
                cur["testlar"].append({"daraja": arg or "o'rta", "savol": [], "variantlar": [], "javob": "", "xato": {}, "izoh": ""})
                blk = ("test", cur["testlar"][-1])
            else:
                raise ValueError(f"{path}: noma'lum blok @{tur}")
            continue
        if blk is None or not line.strip():
            continue
        kind, obj = blk
        if kind == "kirish":
            cur["kirish"] = (cur["kirish"] + " " + line.strip()).strip()
        elif kind == "qadam":
            (obj["doska"] if line.startswith("|") else obj["matn"]).append(line.lstrip("|").strip())
        elif kind in ("sodda", "boshqa"):
            obj[kind].append(line.strip())
        elif kind == "javob":
            cur["javob"].append(line.strip())
        elif kind == "esda":
            (cur["esda"]["doska"] if line.startswith("|") else cur["esda"]["matn"]).append(line.lstrip("|").strip())
        elif kind == "test":
            s = line.strip()
            mv = re.match(r"^([A-F])\)\s*(.+)$", s)
            mj = re.match(r"^=\s*([A-F])$", s)
            mx = re.match(r"^([A-F]):\s*(.+)$", s)
            if mv:
                obj["variantlar"].append(mv.group(2))
            elif mj:
                obj["javob"] = mj.group(1)
            elif mx:
                obj["xato"][mx.group(1)] = mx.group(2)
            elif s.startswith("?"):
                obj["izoh"] = s[1:].strip()
            else:
                obj["savol"].append(s)
    return out


DARAJA = {"oson": 0, "o'rta": 1, "orta": 1, "qiyin": 2}
RANG_RE = re.compile(r"\[(s|k|y|p)\]([\s\S]*?)\[/\1\]")


def doska_xatosi(line):
    """Frontend (pedDoska.js) tahlilining nusxasi: buyruq noto'g'ri yozilsa — oddiy yozuv bo'lib qolmasin, shu yerda ushlansin."""
    toza = RANG_RE.sub(r"\2", line)
    if re.search(r"\[/?[skyp]\]", toza):
        return "rang tegi yopilmagan"
    m = re.match(r"^\s*(KOD|SXEMA|ZANJIR|JADVAL|QOIDA)\s*:\s*(.*)$", line)
    if not m:
        if re.match(r"^\s*(kod|sxema|zanjir|jadval|qoida)\s*:", line, re.I) and not line.startswith(("Kod:", "Kod :")):
            return "buyruq KATTA harf bilan yoziladi"
        return ""
    tur, arg = m.group(1), m.group(2)
    if tur == "KOD":
        q = [x.strip() for x in arg.split("|") if x.strip()]
        ok = 2 <= len(q) <= 12 and all(re.match(r"^([^=]{1,6}?)\s*=\s*\S", x) for x in q)
    elif tur == "SXEMA":
        mm = re.match(r"^([^>]+?)\s*>\s*(.+)$", arg)
        ok = bool(mm) and 2 <= len([x for x in mm.group(2).split("|") if x.strip()]) <= 8
    elif tur == "ZANJIR":
        q = [x.strip() for x in arg.split("|") if x.strip()]
        ok = 2 <= len(q) <= 8 and all(x.split("::")[0].strip() for x in q)
    elif tur == "JADVAL":
        rows = [[c.strip() for c in r.split("|")] for r in arg.split(";;") if r.strip()]
        ok = 2 <= len(rows) <= 11 and 2 <= len(rows[0]) <= 4 and all(len(r) == len(rows[0]) for r in rows)
    else:
        ok = bool(arg.strip())
    return "" if ok else f"{tur} buyrug'i noto'g'ri: {arg[:60]}"


def tekshir_dars(key, d, oxirgi_qism):
    xs = []
    if not d["kirish"]:
        xs.append("kirish yo'q")
    if not 2 <= len(d["qadamlar"]) <= 5:
        xs.append(f"qadamlar {len(d['qadamlar'])} ta (2–5 bo'lsin)")
    for q in d["qadamlar"]:
        if not q["matn"] or not q["doska"]:
            xs.append(f"qadam «{q['sarlavha']}»: matn yoki doska yo'q")
        if len(gap(q["matn"])) > 900:
            xs.append(f"qadam «{q['sarlavha']}»: gap uzun ({len(gap(q['matn']))} belgi)")
        for line in q["doska"]:
            if doska_xatosi(line):
                xs.append(f"qadam «{q['sarlavha']}»: {doska_xatosi(line)}")
    for line in d["esda"]["doska"]:
        if doska_xatosi(line):
            xs.append(f"Esda tut: {doska_xatosi(line)}")
    if oxirgi_qism and not d["javob"]:
        xs.append("javob namunasi yo'q (savolning oxirgi qismida bo'lishi kerak)")
    if d["javob"] and not oxirgi_qism:
        xs.append("javob namunasi faqat oxirgi qismda bo'ladi")
    if not d["esda"]["doska"]:
        xs.append("Esda tut doskasi yo'q")
    for i, t in enumerate(d["testlar"], 1):
        n = len(t["variantlar"])
        if t["daraja"] not in DARAJA:
            xs.append(f"test {i}: daraja «{t['daraja']}» noma'lum")
        if n < 3 or not t["javob"] or ord(t["javob"]) - 65 >= n:
            xs.append(f"test {i}: variant/javob xato")
        if len(set(v.strip().lower() for v in t["variantlar"])) != n:
            xs.append(f"test {i}: bir xil variantlar")
        notog = [L[k] for k in range(n) if L[k] != t["javob"]]
        if set(t["xato"]) != set(notog):
            xs.append(f"test {i}: har noto'g'ri variantga izoh kerak ({''.join(notog)})")
        if not t["izoh"]:
            xs.append(f"test {i}: to'g'ri javob izohi («? …») yo'q")
    if not 5 <= len(d["testlar"]) <= 8:
        xs.append(f"testlar {len(d['testlar'])} ta (5–6 bo'lsin)")
    dar = {t["daraja"] for t in d["testlar"]}
    if not {"oson", "qiyin"} <= dar:
        xs.append("testlarda oson ham, qiyin ham bo'lsin")
    javoblar = [t["javob"] for t in d["testlar"]]
    if javoblar and max(javoblar.count(x) for x in set(javoblar)) > (len(javoblar) + 1) // 2:
        xs.append(f"to'g'ri javoblar bir harfga to'planib qolgan: {''.join(javoblar)}")
    return [f"{key}: {x}" for x in xs]


# ───────────────────────── miya qatorlari ─────────────────────────
def gap(lines):
    return uz(" ".join(x for x in lines if x)).strip()


def miya_qatorlari(sec, it, d, qismlar):
    sid, n = sec["n"], it["n"]
    shox = SX.theme_of(sid, n)
    doska = [f"[k]Savol {sid}.{n}[/k] — {plain(it['q'])}"]
    if d["qism"]:
        i = qismlar.index(d["qism"]) + 1
        doska.append(f"{i}-qism ({len(qismlar)} tadan): [s]{uz(d['sarlavha'])}[/s]")
    doska += [f"Kod: [p]{plain(it['kod'])}[/p]", f"Shox: {uz(shox)}"]
    rows = [{"turi": "kirish", "sarlavha": uz(f"Savol {sid}.{n}" + (f" · {d['qism']}-qism" if d["qism"] else "")), "matn": uz(d["kirish"]),
             "doska": "\n".join(doska)}]
    for q in d["qadamlar"]:
        r = {"turi": "tushuncha", "sarlavha": uz(q["sarlavha"]), "matn": gap(q["matn"]), "doska": "\n".join(uz(x) for x in q["doska"])}
        if q["sodda"]:
            r["sodda"] = gap(q["sodda"])
        if q["boshqa"]:
            r["boshqa_usul"] = gap(q["boshqa"])
        if q["tekshiruv"]:
            r["tekshiruv"] = uz(q["tekshiruv"])
        rows.append(r)
    if d["javob"]:
        rows.append({"turi": "misol", "kod": "J01", "sarlavha": "Imtihon javobi namunasi (T·K·M·A·X)",
                     "matn": uz(f"«{plain(it['q'])}» savoliga imtihonda yozma javob yozing. Avval o‘zingiz reja tuzing, keyin namunani oching."),
                     "yechim": "\n".join(uz(x) for x in d["javob"]), "javob": "",
                     "maslahat": uz("Avval KODni yozib oling: har harf — javobning bitta xatboshisi.\nTa’rif bilan boshlang, oxirida o‘z fikringiz bilan xulosa qiling."),
                     "qiyinlik": "o'rta"})
    links = " · ".join(it["links"])
    oxirgi = not d["qism"] or d["qism"] == qismlar[-1]
    rows.append({"turi": "xulosa", "sarlavha": "Esda tut", "matn": gap(d["esda"]["matn"]),
                 "doska": "\n".join([uz(x) for x in d["esda"]["doska"]] + ([f"Bog‘liq savollar: [k]{links}[/k]"] if links and oxirgi else []))})
    testlar = sorted(d["testlar"], key=lambda t: DARAJA.get(t["daraja"], 1))   # oson → o'rta → qiyin
    for i, t in enumerate(testlar, 1):
        notog = [L[k] for k in range(len(t["variantlar"])) if L[k] != t["javob"]]
        rows.append({"turi": "test", "kod": f"T{i:02d}", "sarlavha": f"Test {i}", "matn": gap(t["savol"]),
                     "variantlar": "\n".join(f"{L[k]}) {uz(v)}" for k, v in enumerate(t["variantlar"])),
                     "javob": t["javob"], "yechim": uz(t["izoh"]),
                     "xato_izohi": "\n".join(f"{k} => {uz(t['xato'][k])}" for k in notog),
                     "qiyinlik": t["daraja"]})
    return rows


# ───────────────────────── fayllar ─────────────────────────
def mavzular_xlsx(qatorlar, path):
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Mavzular"
    head = ["Sinf", "Fan", "Chorak", "Bob", "Bo'lim", "Mavzu", "Kichik mavzu"]
    ws.append(head)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="173B57")
    for b, nom in qatorlar:
        ws.append([SINF, FAN, "1", b, b, nom, ""])
    for col, w in zip("ABCDEFG", (14, 46, 8, 40, 40, 80, 12)):
        ws.column_dimensions[col].width = w
    wb.save(path)


def main(faqat=None):
    import openpyxl
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    sections = SX.load()
    probs = SX.check(sections)
    if probs:
        sys.exit("\n".join(probs))
    files, xatolar, mavzular, jami = [], [], [], {"dars": 0, "test": 0, "savol": 0}
    for sec in sections:
        sid = sec["n"]
        darslar = {}
        import glob
        for f in sorted(glob.glob(os.path.join(HERE, "darslar", f"s{sid}.txt")) + glob.glob(os.path.join(HERE, "darslar", f"s{sid}_*.txt"))):
            for k, d in parse_darslar(f).items():   # bo'lim bir necha faylda bo'lishi mumkin: s1.txt, s1_04-10.txt …
                if k in darslar:
                    raise ValueError(f"{k} ikki faylda bor")
                darslar[k] = d
        itlar = {f"{sid}.{it['n']}": it for it in sec["items"]}
        for k, d in darslar.items():
            if d["savol"] not in itlar:
                xatolar.append(f"{k}: bunday savol {sid}-bo'limda yo'q")
        pre = []
        for it in sec["items"]:
            sav = f"{sid}.{it['n']}"
            if faqat and sav not in faqat:
                continue
            qism = sorted([(k, d) for k, d in darslar.items() if d["savol"] == sav], key=lambda x: x[1]["qism"])
            if not qism:
                continue
            harflar = [d["qism"] for _, d in qism]
            if len(qism) > 1 and harflar != list("abcdef"[:len(qism)]):
                xatolar.append(f"{sav}: qismlar a, b, c … tartibida bo'lsin ({harflar})")
            jami["savol"] += 1
            for k, d in qism:
                xatolar += tekshir_dars(k, d, oxirgi_qism=(d["qism"] == harflar[-1]))
                nom = mavzu_nomi(k, it, d)
                raqam = it["n"] * 10 + (harflar.index(d["qism"]) + 1 if d["qism"] else 0)   # barqaror kod: 1.1-a → DKA-11, 1.2 → DKA-20
                pre.append({"mavzu_kodi": "", "mavzu_nomi": nom, "mavzu_raqami": str(raqam), "rows": miya_qatorlari(sec, it, d, harflar)})
                mavzular.append((bolim_nomi(sec), nom))
                jami["dars"] += 1
                jami["test"] += len(d["testlar"])
        if not pre:
            continue
        book = {"kitob_nomi": f"13.00.02 · {bolim_nomi(sec)} (tayanch doktorantura)", "fan": FAN, "sinf": SINF,
                "kitob_kodi": f"D130002-{sid}", "til": "uz", "kod_prefiksi": PREF[sid], "mualliflar": "Kabutar Ta’lim"}
        wb = template_workbook(prefill=pre, book=book)
        path = os.path.join(out, f"13_00_02_{sid}-bolim_ai_miya.xlsx")
        wb.save(path)
        r = parse_sheets(openpyxl.load_workbook(path))
        errs = r.get("errors") or []
        warns = r.get("warnings") or []
        print(f"{sid}-bo'lim: {len(pre)} dars; parse xato: {len(errs)}, ogohlantirish: {len(warns)}; summary={r.get('summary')}")
        for e in errs[:10]:
            print("   XATO:", e)
        for w in warns[:5]:
            print("   ogoh:", w)
        files.append(path)
    mp = os.path.join(out, "13_00_02_mavzular.xlsx")
    mavzular_xlsx(mavzular, mp)
    files.insert(0, mp)
    if xatolar:
        print("DARS TEKSHIRUVI:")
        print("\n".join("   " + x for x in xatolar))
    zp = os.path.join(out, "13_00_02_doktorantura_paket.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, os.path.join("13.00.02 doktorantura", os.path.basename(f)))
    print(f"Jami: {jami['savol']} savol → {jami['dars']} dars, {jami['test']} test -> {zp}")
    return zp, xatolar


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
