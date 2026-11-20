#!/usr/bin/env python3
"""13.00.02 (tayanch doktorantura) — BIR BO'LIM = BITTA DARS (7 ta dars).

Darsda bo'limning barcha savollari savol tartibida: har savol — bitta qadam (doskaga savol, KOD va mag'iz — rangli bosh
harflar yoki sxema; Kabu 2–4 gapda tushuntiradi), har 10 savoldan keyin «Esda tut» (kodlar). Dars oxirida bo'limning
barcha testlari (har savolga 2–3 ta, bo'limga 100–150 ta). Yozma javob topshiriqlari yo'q.

Dars fayli: darslar_mavzu/s<n>.txt
  ### 1.1 | Fan va tushunchalar        — faqat fayl ichidagi guruh (darsga ta'sir qilmaydi)
  @kirish                             — (ixtiyoriy) o'qituvchi kirish so'zi; bo'lmasa avtomatik
  @savol 1.7                          — savol qadami; «| » satrlar doskaga (KOD:, SXEMA:, ZANJIR:, JADVAL:, QOIDA:, rangli
                                        [s][k][y][p] teglar), qolganlari o'qituvchi gapi. Doska satri yozilmasa — sxemadagi
                                        mag'iz rangli bosh harflar bilan avtomatik chiqadi.
  @sodda / @tekshiruv Savol? => to'g'ri | xato | xato
  @test oson|o'rta|qiyin              — shu savolga test (2–3 ta): savol, A) … D), = B, «A: izoh» har xato variantga, «? izoh»
  Qo'shimcha test uchun shu savolni matnsiz qayta ochish mumkin: «@savol 1.7» + faqat @test bloklari.

python3 build_dars.py [1 2 …]  → out/13_00_02_doktorantura_paket.zip (mavzular + har bo'limga AI miya)
"""
import glob, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_miya as BM                      # uz, plain, bolim_nomi, doska_xatosi, DARAJA, template_workbook, parse_sheets
from build_miya import SX, uz, plain, gap, L

DARS_DIR = os.path.join(HERE, "darslar_mavzu")


def magiz_qatorlari(m):
    """Sxemadagi mag'iz: **B**osh harf → [s]B[/s]osh; « · » bo'yicha qatorlarga (doskaga sig'sin)."""
    t = re.sub(r"\*\*(.+?)\*\*", r"[s]\1[/s]", uz(m))
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", t)
    out, cur = [], ""
    for part in re.split(r"\s+·\s+", t):
        if cur and len(cur) + len(part) > 70:
            out.append(cur)
            cur = part
        else:
            cur = f"{cur} · {part}" if cur else part
    if cur:
        out.append(cur)
    return out[:6]


def parse(path):
    out, dars, sav, blk = [], None, None, None
    for n, raw in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
        line = raw.rstrip()
        m = re.match(r"^###\s+(\d+)\.(\d+)\s*\|\s*(.+?)\s*$", line)
        if m:
            dars = {"sid": int(m.group(1)), "n": int(m.group(2)), "sarlavha": m.group(3), "kirish": "", "savollar": []}
            out.append(dars)
            sav, blk = None, None
            continue
        if dars is None or (not line.strip() and blk is None):
            continue
        m = re.match(r"^@(\w+)\s*(.*)$", line)
        if m:
            tur, arg = m.group(1), m.group(2).strip()
            if tur == "kirish":
                blk = "kirish"
            elif tur == "savol":
                mm = re.match(r"^(\d+)\.(\d+)$", arg)
                if not mm:
                    raise ValueError(f"{path}:{n}: @savol 1.7 ko'rinishida bo'lsin")
                sav = {"key": arg, "n": int(mm.group(2)), "doska": [], "matn": [], "sodda": [], "tekshiruv": "", "testlar": []}
                dars["savollar"].append(sav)
                blk = "savol"
            elif tur == "sodda":
                blk = "sodda"
            elif tur == "tekshiruv":
                sav["tekshiruv"] = arg
                blk = None
            elif tur == "test":
                if sav is None:
                    raise ValueError(f"{path}:{n}: test savoldan oldin")
                sav["testlar"].append({"daraja": arg or "o'rta", "savol": [], "variantlar": [], "javob": "", "xato": {}, "izoh": ""})
                blk = "test"
            else:
                raise ValueError(f"{path}:{n}: noma'lum blok @{tur}")
            continue
        if blk is None or not line.strip():
            continue
        s = line.strip()
        if blk == "kirish":
            dars["kirish"] = (dars["kirish"] + " " + s).strip()
        elif blk == "savol":
            (sav["doska"] if line.startswith("|") else sav["matn"]).append(line.lstrip("|").strip())
        elif blk == "sodda":
            sav["sodda"].append(s)
        elif blk == "test":
            t = sav["testlar"][-1]
            mv, mj, mx = re.match(r"^([A-F])\)\s*(.+)$", s), re.match(r"^=\s*([A-F])$", s), re.match(r"^([A-F]):\s*(.+)$", s)
            if mv:
                t["variantlar"].append(mv.group(2))
            elif mj:
                t["javob"] = mj.group(1)
            elif mx:
                t["xato"][mx.group(1)] = mx.group(2)
            elif s.startswith("?"):
                t["izoh"] = s[1:].strip()
            else:
                t["savol"].append(s)
    return out


def tekshir_savol(sid, s, itlar):
    xs, k = [], s["key"]
    if k not in itlar:
        xs.append(f"{k}: sxemada yo'q")
    if not s["matn"]:
        xs.append(f"{k}: o'qituvchi gapi yo'q")
    if len(gap(s["matn"])) > 900:
        xs.append(f"{k}: gap uzun ({len(gap(s['matn']))})")
    for line in s["doska"]:
        if BM.doska_xatosi(line):
            xs.append(f"{k}: {BM.doska_xatosi(line)}")
    if not 2 <= len(s["testlar"]) <= 4:
        xs.append(f"{k}: testlar {len(s['testlar'])} ta (2–3 bo'lsin)")
    for i, t in enumerate(s["testlar"], 1):
        n = len(t["variantlar"])
        if t["daraja"] not in BM.DARAJA:
            xs.append(f"{k} test {i}: daraja «{t['daraja']}»")
        if n < 3 or not t["javob"] or ord(t["javob"]) - 65 >= n:
            xs.append(f"{k} test {i}: variant/javob xato")
        if len({v.strip().lower() for v in t["variantlar"]}) != n:
            xs.append(f"{k} test {i}: bir xil variantlar")
        notog = [L[j] for j in range(n) if L[j] != t["javob"]]
        if set(t["xato"]) != set(notog):
            xs.append(f"{k} test {i}: har noto'g'ri variantga izoh kerak ({''.join(notog)})")
        if not t["izoh"] or not t["savol"]:
            xs.append(f"{k} test {i}: savol yoki izoh yo'q")
    return xs


def birlashtir(darslar):
    """Fayldagi guruhlar → bo'limning savollari (raqam tartibida); matnsiz qayta ochilgan savol — faqat qo'shimcha testlar."""
    by, xs = {}, []
    for d in darslar:
        for s in d["savollar"]:
            if s["key"] not in by:
                by[s["key"]] = s
            elif not s["matn"] and not s["doska"]:
                by[s["key"]]["testlar"] += s["testlar"]
            else:
                xs.append(f"{s['key']}: ikki marta to'liq yozilgan")
    return [by[k] for k in sorted(by, key=lambda k: int(k.split(".")[1]))], xs


def qisqa(q, n=64):
    q = plain(q).rstrip("?.")
    return q if len(q) <= n else q[:n - 1].rsplit(" ", 1)[0] + "…"


_NISHON = []


def aralashtir(t, j):
    """To'g'ri javob harfini A–D bo'ylab teng taqsimlash: to'g'ri variant navbatdagi «nishon» o'ringa ko'chiriladi,
    qolgan variantlar tartibi saqlanadi, xato izohlari yangi harflarga o'tkaziladi (deterministik)."""
    import random
    while len(_NISHON) <= j:
        blok = [0, 1, 2, 3]
        random.Random(len(_NISHON)).shuffle(blok)
        _NISHON.extend(blok)
    n = len(t["variantlar"])
    eski = L.index(t["javob"])
    yangi = _NISHON[j] % n
    qolgan = [k for k in range(n) if k != eski]
    tartib = qolgan[:yangi] + [eski] + qolgan[yangi:]          # yangi o'rin → eski indeks
    harf = {L[old]: L[new] for new, old in enumerate(tartib)}
    return {**t, "variantlar": [t["variantlar"][k] for k in tartib], "javob": L[yangi],
            "xato": {harf[k]: v for k, v in t["xato"].items()}}


def dars_nomi(sec, savollar):
    return f"{BM.bolim_nomi(sec)} — {len(savollar)} savol"


def qatorlar(sec, savollar, itlar):
    sid = sec["n"]
    kir = (f"Assalomu alaykum! Bu darsda {BM.bolim_nomi(sec).split('. ', 1)[1]} bo‘limining {len(savollar)} ta savolini "
           "ketma-ket o‘rganamiz. Har savolning kodini doskaga yozaman va mag‘zini qisqa tushuntiraman: kodni eslab qolsangiz, "
           "javobni ham eslaysiz. Har o‘n savoldan keyin kodlarni takrorlaymiz. Oxirida bo‘lim bo‘yicha test bor, "
           "keyingi bo‘limga o‘tish uchun kamida 70 foiz kerak.")
    rows = [{"turi": "kirish", "sarlavha": uz(f"{sid}-bo‘lim"), "matn": uz(kir),
             "doska": "\n".join([f"[k]{BM.bolim_nomi(sec)}[/k]", f"Savollar: [s]{sid}.1 – {sid}.{len(savollar)}[/s]",
                                 f"Yo‘l: [y]{uz(plain(sec.get('flow', '')))}[/y]"])}]
    blok = []
    for i, s in enumerate(savollar, 1):
        it = itlar[s["key"]]
        doska = [f"[k]{s['key']}[/k] {plain(it['q'])}", f"Kod: [p]{plain(it['kod'])}[/p]"]
        doska += [uz(x) for x in s["doska"]] if s["doska"] else magiz_qatorlari(it["mag"])
        r = {"turi": "tushuncha", "sarlavha": uz(f"{s['key']} · {qisqa(it['q'])}"), "matn": gap(s["matn"]), "doska": "\n".join(doska)}
        if s["sodda"]:
            r["sodda"] = gap(s["sodda"])
        rows.append(r)
        blok.append(s)
        if len(blok) == 10 or i == len(savollar):
            esda = [f"[k]{x['key']}[/k] {qisqa(itlar[x['key']]['q'], 38)} — [p]{plain(itlar[x['key']]['kod'])}[/p]" for x in blok]
            rows.append({"turi": "xulosa", "sarlavha": f"Esda tut: {blok[0]['key']} – {blok[-1]['key']}", "doska": "\n".join(esda),
                         "matn": uz(f"To‘xtab, {blok[0]['key']} dan {blok[-1]['key']} gacha bo‘lgan savollarning kodlarini bir marta "
                                    "ovoz chiqarib takrorlang. Har kod — bitta javobning rejasi.")})
            blok = []
    testlar = [aralashtir(t, j) for j, t in enumerate([t for s in savollar for t in s["testlar"]])]   # savol tartibida
    for i, t in enumerate(testlar, 1):
        notog = [L[k] for k in range(len(t["variantlar"])) if L[k] != t["javob"]]
        rows.append({"turi": "test", "kod": f"T{i:03d}", "sarlavha": f"Test {i}", "matn": gap(t["savol"]),
                     "variantlar": "\n".join(f"{L[k]}) {uz(v)}" for k, v in enumerate(t["variantlar"])),
                     "javob": t["javob"], "yechim": uz(t["izoh"]),
                     "xato_izohi": "\n".join(f"{k} => {uz(t['xato'][k])}" for k in notog), "qiyinlik": t["daraja"]})
    return rows


def main(faqat=None):
    import openpyxl
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        os.remove(os.path.join(out, f))
    sections = SX.load()
    files, xatolar, mavzular, jami = [], [], [], {"dars": 0, "test": 0, "savol": 0}
    for sec in sections:
        sid = sec["n"]
        if faqat and sid not in faqat:
            continue
        path = os.path.join(DARS_DIR, f"s{sid}.txt")
        if not os.path.exists(path):
            continue
        darslar = []
        for f in sorted(glob.glob(os.path.join(DARS_DIR, f"s{sid}.txt")) + glob.glob(os.path.join(DARS_DIR, f"s{sid}_*.txt"))):
            darslar += parse(f)
        itlar = {f"{sid}.{it['n']}": it for it in sec["items"]}
        savollar, xs = birlashtir(darslar)
        xatolar += xs
        yoq = [k for k in itlar if k not in {s["key"] for s in savollar}]
        if yoq:
            xatolar.append(f"{sid}-bo'lim: yozilmagan savollar ({len(yoq)}): {' '.join(yoq)}")
        for s in savollar:
            xatolar += [f"{sid}-bo'lim: {x}" for x in tekshir_savol(sid, s, itlar)]
        savollar = [s for s in savollar if s["key"] in itlar]
        jv = [aralashtir(t, j)["javob"] for j, t in enumerate([t for s in savollar for t in s["testlar"]])]
        if jv and max(jv.count(x) for x in set(jv)) > len(jv) * 0.4:
            xatolar.append(f"{sid}-bo'lim: to'g'ri javoblar bir harfga to'planib qolgan")
        pre = []
        if savollar:
            nom = dars_nomi(sec, savollar)
            pre.append({"mavzu_kodi": "", "mavzu_nomi": nom, "mavzu_raqami": "1", "rows": qatorlar(sec, savollar, itlar)})
            mavzular.append((BM.bolim_nomi(sec), nom))
            jami["dars"] += 1
            jami["savol"] += len(savollar)
            nt = sum(len(s["testlar"]) for s in savollar)
            jami["test"] += nt
            print(f"{sid}-bo'lim: {len(savollar)} savol, {nt} test; javob harflari: "
                  + " ".join(f"{x}{jv.count(x)}" for x in "ABCD"))
        if not pre:
            continue
        book = {"kitob_nomi": f"13.00.02 · {BM.bolim_nomi(sec)} (tayanch doktorantura)", "fan": BM.FAN, "sinf": BM.SINF,
                "kitob_kodi": f"D130002-{sid}", "til": "uz", "kod_prefiksi": BM.PREF[sid], "mualliflar": "Kabutar Ta’lim"}
        wb = BM.template_workbook(prefill=pre, book=book)
        path = os.path.join(out, f"13_00_02_{sid}-bolim_ai_miya.xlsx")
        wb.save(path)
        r = BM.parse_sheets(openpyxl.load_workbook(path))
        errs = r.get("errors") or []
        print(f"{sid}-bo'lim: {len(pre)} dars, {sum(len(p['rows']) for p in pre)} qator; parse xato: {len(errs)}, "
              f"ogoh: {len(r.get('warnings') or [])}; testlar: {r.get('summary', {}).get('testlar')}")
        for e in errs[:10]:
            print("   XATO:", e)
        files.append(path)
    mp = os.path.join(out, "13_00_02_mavzular.xlsx")
    BM.mavzular_xlsx(mavzular, mp)
    files.insert(0, mp)
    if xatolar:
        print("TEKSHIRUV:")
        print("\n".join("   " + x for x in xatolar))
    zp = os.path.join(out, "13_00_02_doktorantura_paket.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, os.path.join("13.00.02 doktorantura", os.path.basename(f)))
    print(f"Jami: {jami['savol']} savol → {jami['dars']} dars, {jami['test']} test -> {zp}")
    return zp, xatolar


if __name__ == "__main__":
    main({int(x) for x in sys.argv[1:]} or None)
