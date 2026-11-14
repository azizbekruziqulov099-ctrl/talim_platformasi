"""REV561: «KABUTAR_TEMATIKA_*.docx» (GPT tayyorlagan: TUR, qiyinlik, ishlangan misollar, qisqa yechimlar, [TEKSHIR]) fayllarini bankka qo'shish.

Ishlatish:  python tools/mat_bank/qosh.py <bank.json> <fayl1.docx> [fayl2.docx …]
Har fayl avval TEKSHIRILADI; birorta qattiq xato bo'lsa fayl bankka QO'SHILMAYDI va sababi aytiladi (hech narsa o'zgarmaydi):
  • mavzu raqami fayl nomidan (KABUTAR_TEMATIKA_100_100 → 100), kitob bo'limi (MAVZU: 3.4.2) bankdagi bilan mos bo'lishi kerak;
  • testlar to'plami (manba kodlari) bankdagi bilan AYNAN bir xil: ortiq ham, kam ham bo'lmasin;
  • HAR testning javob harfi manba kaliti bilan bir xil (JAVOBLAR ham, qisqa yechim oxiridagi «→ X» ham);
  • har ishlangan misolda JAVOB bor, TUR belgisi testlardagi bilan mos, javobi manba kaliti bilan bir xil;
  • har testda TUR, qiyinlik (O/R/Q) va qisqa yechim bor.
Qo'shiladigan maydonlar — test: tur, qiyinlik, yechim, tekshir (+tekshir_izoh); mavzu: misollar, turlar, (manbada qoida bo'lmasa) qoida. Savol, variant va javob manbadagicha QOLADI.
"""
import json, os, re, shutil, subprocess, sys, tempfile

RASM_PAPKA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "modules", "mat_bank_data", "rasm")
TEKSHIR = r"\\?\[TEKSHIR\\?\]"   # pandoc qavslarni «\[TEKSHIR\]» deb yozadi


def n(s):
    """Solishtirish uchun: bo'shliq, **, $, qavslar va teskari chiziqlarsiz."""
    return re.sub(r"[\s{}\\*$]", "", s or "")


def pandoc_md(docx, media_dir):
    r = subprocess.run(["pandoc", docx, "-t", "markdown", "--wrap=none", f"--extract-media={media_dir}"], capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"pandoc: {r.stderr[:200]}")
    return r.stdout


def oqi(md):
    """KABUTAR markdown → {kitob, nom, qoida, misollar:[{nn,tur,tip,matn}], testlar:[{n,tur,q,manba,matn,tekshir_izoh}], javob:{n:harf}, shubha:{n}, qisqa:{n:matn}}."""
    L = md.replace("\r", "").split("\n")
    h = next((l for l in L if l.startswith("# ")), "")
    m = re.match(r"^# \*\*MAVZU:\s*([\d.]+)\s*\\\|\s*(.+?)\*\*\s*$", h)
    if not m:
        raise ValueError("«MAVZU: 3.4.2 | NOM» sarlavhasi topilmadi")
    sar = [(i, l) for i, l in enumerate(L) if l.startswith("## **")]
    nom = lambda l: re.sub(r"^## \*\*|\*\*\s*$", "", l).strip()
    bolim = {}
    for k, (i, l) in enumerate(sar):
        oxir = sar[k + 1][0] if k + 1 < len(sar) else len(L)
        bolim.setdefault(nom(l), []).append("\n".join(L[i + 1:oxir]).strip())
    bosh = "\n".join(L[: sar[0][0]] if sar else L)
    mb = re.search(r"^\**BOB:\s*(.+?)\**\s*$", bosh, re.M)                       # ixtiyoriy: «BOB: 3-bob. PLANIMETRIYA»
    r = {"kitob": m.group(1), "nom": m.group(2).strip(), "bob": (mb.group(1).strip() if mb else ""), "qoida": (bolim.get("QOIDA") or [""])[0], "misollar": [], "testlar": [], "javob": {}, "shubha": set(), "qisqa": {}}
    for k, (i, l) in enumerate(sar):
        mm = re.match(r"^NAMUNA (\d+) \\\| TUR (\d+) \\\| (.+)$", nom(l))
        if mm:
            oxir = sar[k + 1][0] if k + 1 < len(sar) else len(L)
            r["misollar"].append({"nn": int(mm.group(1)), "tur": int(mm.group(2)), "tip": mm.group(3).strip(), "matn": "\n".join(L[i + 1:oxir]).strip()})
    for nm in ("TESTLAR", "JAVOBLAR", "QISQA YECHIMLAR"):
        if nm not in bolim:
            raise ValueError(f"«{nm}» bo'limi topilmadi")
    cur = None
    for l in bolim["TESTLAR"][0].split("\n"):
        t = re.match(r"^(\d+) \\\| TUR (\d+) \\\| ([ORQ]) \\\| (.*)$", l)
        if t:
            cur = {"n": int(t.group(1)), "tur": int(t.group(2)), "q": t.group(3), "satr": [t.group(4)], "izoh": []}
            r["testlar"].append(cur)
        elif cur is not None:
            if re.match(r"^\s*" + TEKSHIR, l):
                cur["izoh"].append(re.sub(r"^\s*" + TEKSHIR + r"\s*", "", l).strip())
            elif l.strip():
                cur["satr"].append(l)
    for t in r["testlar"]:
        txt = "\n".join(t["satr"]).strip(); mb = re.match(r"^\*\*\(([\d-]+)\)\*\*", txt)
        t["manba"] = mb.group(1) if mb else None; t["matn"] = txt; t["tekshir_izoh"] = " ".join(t.pop("izoh")); del t["satr"]
    for l in bolim["JAVOBLAR"][0].split("\n"):
        for a, b, tk in re.findall(r"(\d+)-([A-E])( " + TEKSHIR + ")?", l):
            r["javob"][int(a)] = b
            if tk:
                r["shubha"].add(int(a))
    for l in bolim["QISQA YECHIMLAR"][0].split("\n"):
        mq = re.match(r"^(\d+)\\\. (.*)$", l)
        if mq:
            r["qisqa"][int(mq.group(1))] = mq.group(2).strip()
    return r


def tekshir_va_qosh(bank, raqam, r, rasm_nom=None):
    """→ (xatolar, ogohlar). xatolar bo'sh bo'lsa bank o'zgartiriladi."""
    xato, ogoh = [], []
    m = next((x for x in bank["mavzular"] if x["raqam"] == raqam), None)
    if not m:
        return [f"bankda {raqam}-mavzu yo'q"], ogoh
    if m.get("kitob") and r["kitob"] != m["kitob"]:
        xato.append(f"kitob bo'limi mos emas: fayl {r['kitob']}, bank {m['kitob']}")
    kod = {}
    for t in m["testlar"]:
        kod.setdefault(t["manba"], []).append(t)
    gkod = [t["manba"] for t in r["testlar"]]
    if None in gkod:
        xato.append("manba kodi yo'q testlar: " + str([t["n"] for t in r["testlar"] if not t["manba"]]))
    yoq = sorted(set(kod) - set(gkod)); ortiq = sorted(set(gkod) - set(kod) - {None})
    if yoq:
        xato.append(f"bankdagi, lekin faylda yo'q testlar: {yoq[:8]} (jami {len(yoq)})")
    if ortiq:
        xato.append(f"faylda bor, bankda yo'q testlar: {ortiq[:8]}")
    if len(gkod) != len(set(gkod)):
        xato.append("faylda takrorlangan manba kodlari bor")
    if xato:
        return xato, ogoh
    bog = {}
    for t in r["testlar"]:
        c = kod[t["manba"]]
        if len(c) > 1:      # bir xil kodli ikki test — variantlar bo'yicha ajratamiz
            mk = [(x.group(1), x.start(), x.end()) for x in re.finditer(r"\*\*([A-E])\)\*\*", t["matn"])]
            var = [n(t["matn"][mk[i][2]:(mk[i + 1][1] if i + 1 < len(mk) else len(t["matn"]))]) for i in range(len(mk))]
            c = [x for x in c if [n(v) for v in x["variantlar"]][:4] == var[:4]] or c
        b0 = c[0]; bog[t["n"]] = b0
        if r["javob"].get(t["n"]) != b0["javob"]:
            xato.append(f"{t['n']}-test ({t['manba']}): javob fayldagi {r['javob'].get(t['n'])} ≠ manba kaliti {b0['javob']}")
        q = r["qisqa"].get(t["n"])
        if not q:
            xato.append(f"{t['n']}-testda qisqa yechim yo'q")
        else:
            mq = re.search(r"→\s*([A-E])", q)
            if not mq or mq.group(1) != b0["javob"]:
                xato.append(f"{t['n']}-test: qisqa yechim oxiridagi harf ({mq.group(1) if mq else '—'}) ≠ kalit ({b0['javob']})")
        if t["n"] in r["shubha"] and not t["tekshir_izoh"]:
            ogoh.append(f"{t['n']}-test: JAVOBLAR da [TEKSHIR] bor, lekin testda sabab yozilmagan")
    turlar_t = {t["manba"]: t["tur"] for t in r["testlar"]}
    for x in r["misollar"]:
        mj = re.search(r"\*\*JAVOB:\s*([A-E])\*\*", x["matn"]); mb = re.search(r"\*\*\(([\d-]+)\)\*\*", x["matn"])
        if not mj:
            xato.append(f"NAMUNA {x['nn']}: «JAVOB: X» yo'q"); continue
        if mb and mb.group(1) in kod:
            if kod[mb.group(1)][0]["javob"] != mj.group(1):
                xato.append(f"NAMUNA {x['nn']} ({mb.group(1)}): javob {mj.group(1)} ≠ manba kaliti {kod[mb.group(1)][0]['javob']}")
            if mb.group(1) in turlar_t and turlar_t[mb.group(1)] != x["tur"]:
                xato.append(f"NAMUNA {x['nn']}: TUR {x['tur']} ≠ testdagi TUR {turlar_t[mb.group(1)]}")
        if x["tip"].upper().startswith("TO") and len(re.findall(r"\d+-qadam", x["matn"])) < 2:
            ogoh.append(f"NAMUNA {x['nn']}: to'liq yechimda 2 tadan kam qadam")
    nt = {t["tur"] for t in r["testlar"]}; nm = {x["tur"] for x in r["misollar"]}
    if nt - nm:
        ogoh.append(f"namunasiz TUR: {sorted(nt - nm)}")
    if xato:
        return xato, ogoh
    # ---- hammasi to'g'ri: bankni yangilaymiz
    for t in r["testlar"]:
        b0 = bog[t["n"]]
        b0["tur"] = t["tur"]; b0["qiyinlik"] = t["q"]
        b0["yechim"] = re.sub(r"\s{2,}", " ", re.sub(TEKSHIR, "", r["qisqa"][t["n"]])).strip()      # [TEKSHIR] belgisi yechim matnida qolmaydi (u tekshir maydonida)
        if t["n"] in r["shubha"] or t["tekshir_izoh"]:
            b0["tekshir"] = True; b0["tekshir_izoh"] = t["tekshir_izoh"]
        else:
            b0.pop("tekshir", None); b0.pop("tekshir_izoh", None)
    m["misollar"] = [{"tur": x["tur"], "tip": x["tip"], "matn": x["matn"]} for x in sorted(r["misollar"], key=lambda z: z["nn"])]
    m["turlar"] = sorted(nt)
    if r.get("bob"):
        m["bob"] = r["bob"]
    if not m["qoida"].strip() and r["qoida"].strip():
        m["qoida"] = r["qoida"]; m["qoida_manba"] = "kabutar"
    return [], ogoh


def rasmlar(md, media_dir, raqam):
    """pandoc chiqargan rasmlarni modules/mat_bank_data/rasm/ ga ko'chiradi va md dagi havolani «rasm:T100-1.png» ga almashtiradi."""
    os.makedirs(RASM_PAPKA, exist_ok=True); k = [0]; kopiya = []

    def f(m):
        src = os.path.join(media_dir, m.group(2))
        if not os.path.exists(src):
            return m.group(0)
        k[0] += 1; nom = f"T{raqam:03d}-{k[0]}{os.path.splitext(src)[1].lower()}"
        kopiya.append((src, os.path.join(RASM_PAPKA, nom)))
        return f"![{m.group(1) or 'chizma'}](rasm:{nom})"
    md = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)\)(\{[^}]*\})?", f, md)
    return md, kopiya


def main(bank_yoli, fayllar):
    bank = json.load(open(bank_yoli, encoding="utf8")); hammasi_ok = True
    for f in fayllar:
        mn = re.search(r"KABUTAR_TEMATIKA_(\d+)_(\d+)", os.path.basename(f))
        if not mn or mn.group(1) != mn.group(2):
            print(f"✗ {os.path.basename(f)}: fayl nomi KABUTAR_TEMATIKA_<raqam>_<raqam> bo'lishi va ikkala raqam bir xil (bitta mavzu)"); hammasi_ok = False; continue
        raqam = int(mn.group(1)); tmp = tempfile.mkdtemp(); kopiya = []
        try:
            md = pandoc_md(os.path.abspath(f), tmp)
            md, kopiya = rasmlar(md, tmp, raqam)
            r = oqi(md)
            xato, ogoh = tekshir_va_qosh(bank, raqam, r)
            if not xato:
                for a, b in kopiya:      # vaqtinchalik papka o'chirilishidan OLDIN ko'chiramiz
                    shutil.copy(a, b)
        except Exception as e:   # noqa: BLE001
            xato, ogoh = [f"o'qib bo'lmadi: {e}"], []
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if xato:
            hammasi_ok = False; print(f"✗ {os.path.basename(f)} — QO'SHILMADI ({len(xato)} xato):"); [print("    •", x) for x in xato[:12]]
        else:
            sh = sum(1 for t in next(x for x in bank["mavzular"] if x["raqam"] == raqam)["testlar"] if t.get("tekshir"))
            print(f"✓ {os.path.basename(f)} — {raqam}-mavzu: {len(r['testlar'])} test, {len(r['misollar'])} misol, {len({t['tur'] for t in r['testlar']})} TUR, {sh} ta [TEKSHIR], {len(kopiya)} rasm")
        for o in ogoh:
            print("    ⚠", o)
    json.dump(bank, open(bank_yoli, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))   # xatosiz fayllar saqlanadi, xatolilar bankka tegmaydi
    return hammasi_ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1], sys.argv[2:]) else 1)
