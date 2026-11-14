"""REV558: «Tematika» (matematika, 1996–2003 test to'plami) Word fayllarini bankka o'tkazish.

Ishlatish:  python tools/mat_bank/oqi.py <docx papka> <chiqish.json>
Word → pandoc → markdown (formulalar LaTeX bo'lib, AYNAN o'qiladi) → mavzular, qoidalar, ishlangan misollar, testlar, javoblar kaliti.
Uch xil joylashuv (oila) tanib olinadi:
  A  «# 1.1.1 Nom»            — mavzu oxirida «## JAVOBLAR» (1–30-mavzular)
  B  «# 31. 1.7.3 Nom»        — «## QOIDALAR / Ishlangan misol / TESTLAR» + «## JAVOBLAR» (31–99)
  C  «# 100-MAVZU. NOM»       — «## Testlar … ### … javoblar» (har blokdan keyin; 100–141)
Hech narsa taxmin qilinmaydi: javobi yoki 5 varianti yo'q test «muammo» ro'yxatiga tushadi va bankka KIRMAYDI.
"""
import json, os, re, subprocess, sys

BELGI = "ABCDE"
RE_TEST = re.compile(r"^(\d+)\\?\.\s*\(?\s*(\d{2,4}-\d+-\d+)\s*\)?\s*(.*)$", re.S)
RE_JAVOB = re.compile(r"(\d+)\s*-{1,3}\s*\**\s*([A-E])\b")
RE_MARKER = re.compile(r"(?:(?<=\s)|^)\**([A-E])\\?\)\**(?=\s|\$|\\|$)")


def pandoc(docx):
    r = subprocess.run(["pandoc", docx, "-t", "markdown", "--wrap=none"], capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f"pandoc: {r.stderr[:200]}")
    return r.stdout


def toza(s):
    """Qator oxiridagi «\\» (pandoc qator uzilishi), blockquote belgisi, ortiqcha bo'shliqlar."""
    s = re.sub(r"^\s*>\s?", "", s)
    s = re.sub(r"\\\s*$", "", s.rstrip())
    return s.strip()


def bold_yech(s):
    return re.sub(r"\*\*", "", s).strip()


RE_FORMULA = re.compile(r"\$\$(.+?)\$\$|\$(.+?)\$", re.S)
RE_QAVS_SISTEMA = re.compile(r"\\begin\{matrix\}\s*\\begin\{matrix\}\s*[⎧⎨⎩⎪\s\\]+\\end\{matrix\}\s*&\s*(\\begin\{matrix\}.*?\\end\{matrix\})\s*\\end\{matrix\}", re.S)


def formula_toza(e):
    """Word'dan kelgan formulani KaTeX o'qiy oladigan holatga keltiradi (ma'noni o'zgartirmaydi)."""
    e = re.sub(r"(?<!\\)\\\s*$", "", e)                         # oxiridagi yolg'iz «\» (Word qator uzilishi)
    e = re.sub(r"\\mspace\{[^}]*\}", r"\\,", e)                  # \mspace{6mu} — KaTeX bilmaydi
    e = RE_QAVS_SISTEMA.sub(lambda m: r"\left\{ " + m.group(1) + r" \right.", e)    # ⎧⎨⎩ jadvali → figurali qavs
    return e


def matn_toza(t):
    """Matndagi har bir $…$ / $$…$$ formulani tozalaydi."""
    def f(m):
        if m.group(1) is not None:
            return "$$" + formula_toza(m.group(1)) + "$$"
        return "$" + formula_toza(m.group(2)) + "$"
    return RE_FORMULA.sub(f, t)


def variantlar_ajrat(matn):
    """matn ichidan A)…E) variantlarni ajratadi. → (savol_matni, [5 variant]) yoki (matn, None). Oxirgi to'liq A→E ketma-ketligi olinadi."""
    m = [(x.group(1), x.start(), x.end()) for x in RE_MARKER.finditer(matn)]
    for i in range(len(m) - 1, -1, -1):
        if m[i][0] != "A":
            continue
        zanjir, k = [m[i]], 1
        for x in m[i + 1:]:
            if x[0] == BELGI[k]:
                zanjir.append(x); k += 1
                if k == 5:
                    break
        if len(zanjir) == 5:
            savol = matn[: zanjir[0][1]].strip()
            var = []
            for j, z in enumerate(zanjir):
                oxir = zanjir[j + 1][1] if j < 4 else len(matn)
                t = re.sub(r"\\\s*$", "", matn[z[2]:oxir].strip()).strip()
                var.append(re.sub(r"^\*\*|\*\*$", "", t).strip())
            return savol, var
    return matn.strip(), None


def oila_va_mavzular(satrlar):
    """Mavzu sarlavhalari: [(indeks, oila, raqam, kitob_bolimi, nom)]. Mundarijadagi qatorlar sarlavha emas — ular o'tkazib yuboriladi."""
    out = []
    for i, l in enumerate(satrlar):
        t = l.strip()
        if not t.startswith("#"):
            continue
        s = bold_yech(re.sub(r"^#+\s*", "", t))
        if "bet" in s and re.search(r"\d+-bet", s):
            continue
        m = re.match(r"^(\d+)\.\s+(\d+\.\d+(?:\.\d+)?)\s+(.+)$", s)           # B: «31. 1.7.3 Nom» yoki «86. 2.3 Nom» (raqamdan keyin BO'SHLIQ; A da yo'q)
        if m:
            out.append((i, "B", int(m.group(1)), m.group(2), m.group(3).strip(" .")))
            continue
        m = re.match(r"^(\d+)-MAVZU\.?\s*(.+)$", s, re.I)                  # C
        if m:
            out.append((i, "C", int(m.group(1)), None, m.group(2).strip(" .")))
            continue
        m = re.match(r"^(\d+\.\d+\.\d+)\s+(.+)$", s)                        # A
        if m and not t.startswith("###") and not re.search(r"javob|testlar|test\b", s, re.I):
            out.append((i, "A", None, m.group(1), m.group(2).strip(" .")))
    return out


def mundarija_raqamlari(satrlar):
    """A oilasi: mundarijadan «N. 1.1.1 Nom — 2-bet» → {1.1.1: N}."""
    d = {}
    for l in satrlar[:200]:
        # bir qatorda ikki ustun bo'lishi mumkin; pandoc «1\.» deb yozadi
        for m in re.finditer(r"(?:^|\s)\**(\d+)\\?\.\**\s*(\d+\.\d+\.\d+)\s+.*?(?:[—–]|-{2,3})\s*\**\d+-bet", l):
            d.setdefault(m.group(2), int(m.group(1)))
    return d


def blokni_oqi(satrlar):
    """Bir mavzu satrlarini bo'laklarga: qoida / namuna / test bloklari / javoblar bloklari."""
    qoida, namuna, bloklar = [], [], []   # bloklar: {"testlar": [...], "javob": {n: harf} | None}
    holat, joriy, javob_bloki, namuna_joriy = "qoida", None, None, []

    def yop_test():
        nonlocal joriy
        if joriy is not None:
            bloklar[-1]["testlar"].append(joriy)
            joriy = None

    def blok_och():
        yop_test()
        bloklar.append({"testlar": [], "javob": None, "nom": ""})

    for raw in satrlar:
        t = toza(raw)
        if not t:
            if joriy is not None:
                joriy["_qator"].append("")
            elif holat == "namuna":
                namuna_joriy.append("")
            elif holat == "qoida":
                qoida.append("")          # abzatslar chegarasi saqlanadi (aks holda misolning savoli, variantlari va yechimi yopishib qoladi)
            continue
        bosh = re.sub(r"^#+\s*", "", bold_yech(t)).strip()
        sar = t.startswith("#")
        low = bosh.lower()
        if sar and re.search(r"javoblar\s*$", low) or (sar and re.match(r"^javoblar\b", low)):   # javoblar kaliti
            yop_test(); holat = "javob"
            if not bloklar:
                blok_och()
            javob_bloki = bloklar[-1]; javob_bloki["javob"] = javob_bloki["javob"] or {}
            continue
        if sar and ("ishlangan misol" in low or "namuna" in low and not low.startswith("test")):
            yop_test(); holat = "namuna"; namuna_joriy = []; namuna.append(namuna_joriy); continue
        if sar and (low.startswith("testlar") or low.startswith("test ") or "bo'yicha testlar" in low or "bo'lim testlari" in low or low == "testlar"):
            yop_test(); holat = "test"
            if not bloklar or bloklar[-1]["javob"] is not None:      # javoblar kaliti kelmaguncha blok davom etadi
                blok_och(); bloklar[-1]["nom"] = bosh
            continue
        if sar and holat == "javob":
            # javoblar kalitidan keyingi sarlavha — yangi test bloki (C oila: o'z javoblari bilan)
            holat = "test"; blok_och(); bloklar[-1]["nom"] = bosh; continue
        if sar and holat == "test":
            # test ichidagi kichik sarlavha («A. Oraliqlar usuli»): raqamlash davom etadi, matnga qo'shilmaydi
            yop_test(); continue
        if sar and holat == "namuna" and t.startswith(("# ", "## ")):
            # «## Trapetsiyaning elementlari» — misoldan keyingi birinchi bo'lim sarlavhasi: testlar shu yerdan boshlanadi
            holat = "test"; blok_och(); bloklar[-1]["nom"] = bosh; continue
        if sar and holat == "qoida" and (low.startswith("qoida") or "formulalar" in low):
            continue
        if holat == "javob":
            if sar:
                holat = "qoida"; continue
            for n, h in RE_JAVOB.findall(t):
                javob_bloki["javob"][int(n)] = h
            continue
        if holat == "test" or (holat == "qoida" and RE_TEST.match(re.sub(r"^\*\*|\*\*", "", t).strip())):
            if holat == "qoida":
                holat = "test"; blok_och()
            if not bloklar:
                blok_och()
            u = bold_yech(t); m = RE_TEST.match(u)
            if m:
                yop_test()
                joriy = {"n": int(m.group(1)), "manba": m.group(2), "_qator": [m.group(3)]}
                continue
            if joriy is not None:
                joriy["_qator"].append(t)
            continue
        if holat == "namuna":
            if RE_TEST.match(bold_yech(t)):          # «31–99-mavzular»: testlar sarlavhasiz, misoldan keyin boshlanadi
                holat = "test"
                # test bo'limi ichidagi «### Ishlangan misol» yangi blok ochmaydi: raqamlash javoblar kalitigacha davom etadi
                if not bloklar or bloklar[-1]["javob"] is not None:
                    blok_och()
                else:
                    yop_test()
                m = RE_TEST.match(bold_yech(t)); joriy = {"n": int(m.group(1)), "manba": m.group(2), "_qator": [m.group(3)]}
                continue
            namuna_joriy.append(t); continue
        qoida.append(t)
    yop_test()
    return [x for x in qoida], namuna, bloklar


def mavzularni_oqi(md):
    satrlar = md.split("\n")
    bosh = oila_va_mavzular(satrlar)
    mund = mundarija_raqamlari(satrlar)
    mavzular = []
    for k, (i, oila, raqam, kitob, nom) in enumerate(bosh):
        oxir = bosh[k + 1][0] if k + 1 < len(bosh) else len(satrlar)
        qoida, namuna, bloklar = blokni_oqi(satrlar[i + 1: oxir])
        if oila == "A":
            raqam = mund.get(kitob)
        if oila == "C" and kitob is None:
            for q in satrlar[i + 1: i + 6]:
                m = re.search(r"Kitobdagi bo.lim:\**\s*(\d+\.\d+\.\d+)", q)
                if m:
                    kitob = m.group(1)
        mavzular.append({"raqam": raqam, "kitob": kitob, "nom": nom, "oila": oila, "qoida": re.sub(r"\n{3,}", "\n\n", "\n".join(qoida)).strip(),
                         "namunalar": [re.sub(r"\n{3,}", "\n\n", "\n".join(x)).strip() for x in namuna if any(x)], "bloklar": bloklar})
    return mavzular


def tayyorla(mavzu):
    """Mavzuni bank shakliga: har blok testlari javoblar bilan birlashtiriladi. → (mavzu_dict, muammolar)."""
    muammo, testlar = [], []
    for bi, b in enumerate(mavzu["bloklar"], 1):
        javob = b["javob"] or {}
        sanash = {}
        for t in b["testlar"]:
            sanash[t["n"]] = sanash.get(t["n"], 0) + 1
        for n, k in sanash.items():
            if k > 1:
                muammo.append((f"{mavzu['raqam']}/{bi}/{n}", "", f"blokda {n}-raqam {k} marta uchradi"))
        for t in b["testlar"]:
            matn = "\n".join(t["_qator"]).strip()
            savol, var = variantlar_ajrat(matn)
            savol = matn_toza(savol)
            var = None if var is None else [matn_toza(v) for v in var]
            kim = f"{mavzu['raqam']}/{bi}/{t['n']}"
            if var is None:
                muammo.append((kim, t["manba"], "5 variant topilmadi")); continue
            h = javob.get(t["n"])
            if h is None:
                muammo.append((kim, t["manba"], "javobi yo'q")); continue
            if not savol.strip():
                muammo.append((kim, t["manba"], "savol matni bo'sh")); continue
            testlar.append({"id": f"T{int(mavzu['raqam']):03d}-{bi}-{t['n']:03d}", "blok": bi, "n": t["n"], "manba": t["manba"],
                            "savol": savol, "variantlar": var, "javob": h})
        for n in javob:
            if n not in {t["n"] for t in b["testlar"]}:
                muammo.append((f"{mavzu['raqam']}/{bi}/{n}", "", "javob bor, test topilmadi"))
        if b["testlar"] and not javob:
            muammo.append((f"{mavzu['raqam']}/{bi}", "", f"blokda {len(b['testlar'])} test bor, javoblar kaliti topilmadi"))
    return {"raqam": mavzu["raqam"], "kitob": mavzu["kitob"], "nom": mavzu["nom"], "qoida": matn_toza(mavzu["qoida"]),
            "namunalar": [matn_toza(x) for x in mavzu["namunalar"]], "testlar": testlar}, muammo


def main(papka, chiqish):
    fayllar = sorted(f for f in os.listdir(papka) if f.lower().endswith((".docx", ".md")))
    hammasi, muammolar, hisobot = {}, [], []
    for f in fayllar:
        p = os.path.join(papka, f)
        md = open(p, encoding="utf8").read() if f.endswith(".md") else pandoc(p)
        for mv in mavzularni_oqi(md):
            if mv["raqam"] is None:
                muammolar.append((f"{f}:{mv['nom']}", "", "mavzu raqami aniqlanmadi")); continue
            d, mm = tayyorla(mv)
            muammolar += [(f"{f} · {a}", b, c) for a, b, c in mm]
            if d["raqam"] in hammasi:       # takror mavzu: testlari ko'p bo'lgani qoladi
                if len(d["testlar"]) <= len(hammasi[d["raqam"]]["testlar"]):
                    continue
            hammasi[d["raqam"]] = d
    bank = {"manba": "Tematika — Matematika (1996–2003)", "mavzular": [hammasi[k] for k in sorted(hammasi)]}
    os.makedirs(os.path.dirname(os.path.abspath(chiqish)), exist_ok=True)
    json.dump(bank, open(chiqish, "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
    return bank, muammolar


if __name__ == "__main__":
    bank, muammolar = main(sys.argv[1], sys.argv[2])
    jami = sum(len(m["testlar"]) for m in bank["mavzular"])
    print(f"mavzular: {len(bank['mavzular'])} | testlar: {jami} | muammolar: {len(muammolar)}")
    for x in muammolar[:25]:
        print("  ", x)
