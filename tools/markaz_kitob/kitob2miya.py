"""Azizjonning «MATEMATIKA · N-KITOB» (docx, qismlarga bo'lingan) → Kabutar Miya (o'quv markazi kursi).

Har dars bir Miya varag'i bo'ladi; dars tartibi kitobdagidek, lekin interaktiv:
  kirish → nazariya (har bo'lim — ustoz gapiradi va doskaga yozadi, rasm ko'rsatadi; bo'lim oxirida 4 variantli savol)
  → «Yodda tuting» → namunaviy yechimlar (qadam-baqadam) → mashqlar (javobi bilan) → spiral takrorlash → test.
Nazorat testlari va oraliq nazoratlar — alohida varaqlar (faqat test).
"""
import glob, json, os, re, shutil, subprocess, sys
from copy import copy

PANDOC_KESH = "/tmp/k4/md"
os.makedirs(PANDOC_KESH, exist_ok=True)


def md_ol(docx, media_dir):
    nom = os.path.splitext(os.path.basename(docx))[0]
    out = os.path.join(PANDOC_KESH, nom + ".md")
    if not os.path.exists(out):
        subprocess.run(["pandoc", "-f", "docx+styles", "-t", "markdown", "--wrap=none", f"--extract-media={media_dir}/{nom}", docx, "-o", out], check=True, timeout=600)
    return open(out, encoding="utf8").read()


# ───────────── markdown → bloklar ─────────────
def toza(t):
    t = re.sub(r"\{width=[^}]*\}", "", t)
    t = t.replace("---", "—").replace("--", "–")
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"(?<![\\$])\*([^*$]+)\*", r"\1", t)
    t = re.sub(r"\\([.\[\]()*_#'\"-])", r"\1", t)   # pandoc qochirishlari
    t = re.sub(r"[ \t]+", " ", t)
    return t.strip()


def bloklar(md):
    """→ [{'t': 'h1|h2|h3|div|li|img|table|p', 'style': ..., 'text': ...}]"""
    out, i, L = [], 0, md.split("\n")
    while i < len(L):
        s = L[i]
        if s.startswith("```"):
            i += 1
            while i < len(L) and not L[i].startswith("```"):
                i += 1
            i += 1; continue
        m = re.match(r"^(#{1,4})\s+(.*?)(\s+\{#.*\})?$", s)
        if m:
            out.append({"t": f"h{len(m.group(1))}", "text": toza(m.group(2))}); i += 1; continue
        m = re.match(r'^:::\s*\{custom-style="([^"]+)"\}', s)
        if m:
            st, buf = m.group(1), []
            i += 1
            while i < len(L) and not L[i].startswith(":::"):
                buf.append(L[i]); i += 1
            i += 1
            matn = "\n".join(buf).strip()
            img = re.search(r"!\[[^\]]*\]\(([^)]+)\)", matn)
            if img:
                out.append({"t": "img", "src": img.group(1), "style": st}); continue
            out.append({"t": "div", "style": st, "text": toza(matn)}); continue
        m = re.match(r"^\s*(?:-|\d+\))\s{1,4}(.*)$", s)
        if m and s.strip():
            buf = [m.group(1)]
            i += 1
            while i < len(L) and L[i].startswith("    ") and L[i].strip():
                buf.append(L[i].strip()); i += 1
            out.append({"t": "li", "text": toza(" ".join(buf)), "num": s.strip()[0].isdigit()}); continue
        if s.startswith("|") or re.match(r"^\s*[-+]{3,}", s):
            buf = []
            while i < len(L) and L[i].strip():
                buf.append(L[i]); i += 1
            qator = []
            for r in buf:
                if r.startswith("|") and not re.match(r"^\|[\s:|-]+\|?$", r):
                    hj = [toza(x) for x in r.strip("|").split("|")]
                    if any(hj): qator.append(" · ".join(x for x in hj if x))
            if qator: out.append({"t": "table", "rows": qator})
            continue
        img = re.search(r"!\[[^\]]*\]\(([^)]+)\)", s)
        if img:
            out.append({"t": "img", "src": img.group(1)}); i += 1; continue
        if s.strip():
            out.append({"t": "p", "text": toza(s)})
        i += 1
    return out


# ───────────── kitob → darslar ─────────────
NAZARIYA = ("nazariya", "qisqa nazariya va usullar", "konspekt", "g'oyalar xaritasi")
AMALIY = (("mashqlar", "mashq", "M"), ("masalalar", "mashq", "M"), ("olimpiada masalalari", "mashq", "O"), ("spiral takrorlash", "spiral", "S"), ("erkin takrorlash", "erkin", "E"))
def darslarga(bl):
    darslar, joriy, bolim, sek = [], None, None, None
    for b in bl:
        if b["t"] == "h1":
            tx = b["text"]
            joriy = {"nom": tx, "turi": "dars" if re.match(r"^\d+-(dars|bob)\b", tx) else "javob" if tx.startswith("Javob") else "ishora" if tx.startswith("Ishora")
                     else "yechim" if tx.startswith("Yechimlar") else "nazorat",
                     "bolim": {}, "kirish": "", "kod": "", "maqsad": []}
            darslar.append(joriy); bolim, sek = "bosh", None; continue
        if joriy is None:
            continue
        if b["t"] == "h2" and joriy["turi"] not in ("javob", "ishora", "yechim"):
            bolim, sek = b["text"].lower().replace("‘", "'").replace("’", "'"), None; joriy["bolim"].setdefault(bolim, []); continue
        if b["t"] in ("h2", "h3") and joriy["turi"] in ("javob", "ishora", "yechim"):
            sek = {"nom": b["text"], "b": []}; joriy["bolim"].setdefault("bosh", []).append(sek); bolim = "bosh"; continue
        if b["t"] == "h3":
            if bolim in NAZARIYA:
                sek = {"nom": b["text"], "b": []}; joriy["bolim"].setdefault(bolim, []).append(sek); continue
        if joriy["turi"] in ("javob", "ishora", "yechim"):
            if sek is None:
                sek = {"nom": "", "b": []}; joriy["bolim"].setdefault(bolim, []).append(sek)
            sek["b"].append(b); continue
        if bolim == "bosh":
            if b.get("style") == "Belgi": joriy["kod"] = b["text"]
            elif b.get("style") == "Kirish": joriy["kirish"] += (" " + b["text"])
            elif b["t"] == "li": joriy["maqsad"].append(b["text"])
            elif joriy["turi"] == "nazorat": joriy["bolim"].setdefault("test", []).append(b)
            continue
        if bolim in NAZARIYA:
            if sek is None:
                sek = {"nom": "", "b": []}; joriy["bolim"].setdefault(bolim, []).append(sek)
            sek["b"].append(b); continue
        joriy["bolim"].setdefault(bolim, []).append(b)
    return darslar


def raqamli(bloklar_):
    """«Mashq» uslubidagi «1. ...» bandlar (+ Variantlar) → [{n, matn, var}]."""
    out = []
    for b in bloklar_:
        t = b.get("text", "")
        if b.get("style") == "Variantlar" and out:
            v = re.split(r"\s*([A-F])\)\s*", " " + t)
            out[-1]["var"] = [v[k + 1].strip() for k in range(1, len(v) - 1, 2)]
            continue
        m = re.match(r"^(\d{1,2})\.\s*(.*)$", t, re.S)
        if m and b.get("style") in ("Mashq", None, "Body Text", "First Paragraph", "Compact"):
            out.append({"n": int(m.group(1)), "matn": m.group(2).strip(), "var": []})
        elif out and b["t"] in ("div", "p", "li") and b.get("style") not in ("Takror",):
            out[-1]["matn"] += "\n" + t
    return out


def javoblar(dars):
    """Javoblar bo'limi: {dars_nomi: {'mashq': {n: javob}, 'spiral': {...}, 'test': {n: harf}}}"""
    out = {}
    for sek in dars["bolim"].get("javoblar", []) + dars["bolim"].get("bosh", []):
        pass
    for sek in dars["bolim"].get("bosh", []):
        pass
    return out


def javob_xaritasi(jdars):
    out = {}
    for sek in jdars["bolim"].get("bosh", []) if isinstance(jdars["bolim"].get("bosh"), list) else []:
        pass
    for k, v in jdars["bolim"].items():
        for sek in v if isinstance(v, list) else []:
            if not isinstance(sek, dict) or "nom" not in sek:
                continue
            d = out.setdefault(sek["nom"], {"mashq": {}, "spiral": {}, "test": {}})
            for b in sek["b"]:
                t = b.get("text", "")
                bj = re.match(r"^(\d{1,2})\.\s*Javob:\s*(.*?)(?:\s*Kalit:\s*(.*))?$", t, re.S)
                if bj:
                    d["mashq"][int(bj.group(1))] = bj.group(2).strip().rstrip(".").strip()
                    if bj.group(3): d.setdefault("kalit", {})[int(bj.group(1))] = bj.group(3).strip()
                    continue
                bosh = re.match(r"^(Mashqlar va masalalar|Mashqlar|Masalalar|Olimpiada masalalari|Spiral takrorlash|Test|Erkin takrorlash)\s*:\s*(.*)$", t, re.S)
                kalit, qolgan = ("test", t) if not bosh and re.match(r"^\d+\s*–\s*[A-F]", t) else (None, None)
                if bosh:
                    kalit = {"Mashqlar": "mashq", "Mashqlar va masalalar": "mashq", "Masalalar": "mashq", "Olimpiada masalalari": "mashq",
                             "Spiral takrorlash": "spiral", "Test": "test", "Erkin takrorlash": "erkin"}[bosh.group(1)]
                    qolgan = bosh.group(2)
                if not kalit:
                    continue
                if kalit == "test":
                    for n, h in re.findall(r"(\d+)\s*–\s*([A-F])", qolgan):
                        d["test"][int(n)] = h
                else:
                    qism = re.split(r"(?:^|;\s*)(\d{1,2})\)\s*", qolgan)
                    for j in range(1, len(qism) - 1, 2):
                        d.setdefault(kalit, {})[int(qism[j])] = qism[j + 1].strip().rstrip(";").strip()
    return out


SODDA_JAVOB = re.compile(r"^\$?\s*-?[\d\s\\,.{}/]+(?:\\frac\{\d+\}\{\d+\})?\s*\$?$")


def bandlar_xaritasi(jdars):
    """Ishoralar / Yechimlar: {dars_nomi: {n: matn}} — «**1.** …; **2.** …» yoki ketma-ket paragraflar."""
    out = {}
    for sek in jdars["bolim"].get("bosh", []):
        if not isinstance(sek, dict) or "nom" not in sek:
            continue
        matn = "\n".join(b.get("text", "") for b in sek["b"] if b.get("text"))
        qism = re.split(r"(?:^|\n|;\s*)(\d{1,2})\.\s+", "\n" + matn)
        d = out.setdefault(sek["nom"], {})
        for j in range(1, len(qism) - 1, 2):
            d[int(qism[j])] = (d.get(int(qism[j]), "") + "\n" + qism[j + 1].strip().rstrip(";")).strip()
    return out


def javob_qiymat(j):
    """Oddiy son/kasr bo'lsa — tekshiriladigan javob; aks holda bo'sh (yechimda ko'rsatiladi)."""
    t = j.strip()
    if re.fullmatch(r"\$[^$]+\$", t):
        ich = t[1:-1].replace("\\,", "").replace("\\ ", "").replace(" ", "")
        m = re.fullmatch(r"(-?)\\frac\{(\d+)\}\{(\d+)\}", ich)
        if m: return f"{m.group(1)}{m.group(2)}/{m.group(3)}"
        if re.fullmatch(r"-?\d+([.,]\d+)?", ich): return ich.replace(".", ",") if "," in ich else ich
        m = re.fullmatch(r"x=(-?\d+([.,]\d+)?)", ich)
        if m: return m.group(1)
    return ""


# ───────────── dars → Miya qatorlari ─────────────
MAX_OVOZ = 900


def nazariya_qatorlari(sek, rasm_nomi):
    """Bitta nazariya bo'limi → 1–4 ta «tushuncha» qatori (ovoz + doska qatorlari + rasm)."""
    qatorlar, ovoz, doska, rasm = [], [], [], ""
    qiziq = []

    def yop():
        nonlocal ovoz, doska, rasm
        if ovoz or doska:
            qatorlar.append({"ovoz": " ".join(ovoz), "doska": doska[:8], "rasm": rasm})
        ovoz, doska, rasm = [], [], ""

    for b in sek["b"]:
        st, t = b.get("style", ""), b.get("text", "")
        if b["t"] == "img":
            if rasm: yop()
            rasm = rasm_nomi(b["src"]); continue
        if st in ("RasmIzoh", "Rasm izohi"):
            if t: ovoz.append(t.replace("‑rasm.", "-rasmga qarang:"))
            continue
        if st == "Qiziq":
            qiziq.append(t); continue
        if b["t"] == "table":
            doska.extend(b["rows"][:6]); continue
        if st == "Formula":
            doska.append(t); continue
        k = len(doska) + 1
        if st == "Qoida":
            doska.append("QOIDA: " + re.sub(r"\$\$?", "$", t)[:220]); ovoz.append(f"[{k}] " + t); continue
        if st == "Diqqat":
            doska.append("⚠️ " + t[:200]); ovoz.append(f"[{k}] " + t); continue
        if b["t"] == "li":
            doska.append(("• " if not b.get("num") else "") + t[:200]); ovoz.append(f"[{k}] " + t); continue
        if t:
            if sum(len(x) for x in ovoz) + len(t) > MAX_OVOZ and ovoz:
                yop(); k = 1
            formulalar = [f for f in re.findall(r"\$[^$]+\$", t) if len(f) >= 5]
            if formulalar and len(doska) < 8:
                doska.append("   ".join(formulalar[:2])); ovoz.append(f"[{len(doska)}] " + t)
            else:
                ovoz.append(t)
    yop()
    for q in qiziq:
        qatorlar.append({"ovoz": "Bilasizmi? " + q.replace("Bilasizmi?", "").strip(), "doska": ["💡 Bilasizmi?"], "rasm": "", "qiziq": True})
    return qatorlar


def belgilarni_mosla(ovoz, doska):
    """[n] belgisi doska qatorlaridan ko'p bo'lmasin; birinchi qator — gap boshida."""
    n = len([d for d in doska if d.strip()])
    ovoz = re.sub(r"\s*\[(\d{1,2})\]", lambda m: f" [{m.group(1)}]" if int(m.group(1)) <= n else "", ovoz).strip()
    return ovoz


def dars_qatorlari(dars, jv, rasm_nomi, ishora=None, yechimlar=None):
    ishora, yechimlar = ishora or {}, yechimlar or {}
    R = []
    tests = raqamli(dars["bolim"].get("test", []))
    tj = jv.get("test", {})
    tekshiruv = []
    for t in tests:
        h = tj.get(t["n"])
        if h and len(t["var"]) >= 2 and "ABCDEF".index(h) < len(t["var"]):
            togri = t["var"]["ABCDEF".index(h)]
            boshqa = [v for k, v in enumerate(t["var"]) if k != "ABCDEF".index(h)]
            if all(" | " not in x for x in t["var"]) and len(t["matn"]) < 400 and "\n" not in t["matn"]:
                tekshiruv.append(f"{t['matn']} => " + " | ".join([togri] + boshqa))
    # testi yo'q darslarda (3-kitob boblari) — javobi son bo'lgan masalalar nazariya oxirida savol bo'ladi (variantlarni sayt tuzadi)
    if len(tekshiruv) < 6:
        for bolim, kalit, _ in AMALIY:
            for m in raqamli(dars["bolim"].get(bolim, [])):
                jq = javob_qiymat(jv.get(kalit, {}).get(m["n"], ""))
                matn = re.sub(r"\*?\[[A-Z]\d{2}\.\d{2}(?:,\s*[A-Z]\d{2}\.\d{2})*\]\*?", "", m["matn"].replace("★", "").replace("●", "")).strip()
                if jq and len(matn) < 300 and "\n" not in matn:
                    tekshiruv.append(f"{matn} => {jq}")
    # kirish
    maqsad = dars["maqsad"][:4]
    R.append(("kirish", "", "🎯 " + re.sub(r"^\d+-dars\.\s*", "", dars["nom"]), dars["kirish"].strip()[:MAX_OVOZ] or dars["nom"],
              "Bu darsda:\n" + "\n".join("• " + m for m in maqsad) if maqsad else "", "", "", "", "", "", "", "", "", "", ""))
    # nazariya
    tk = 0
    for sek in [x for k in NAZARIYA for x in dars["bolim"].get(k, [])]:
        if not sek["b"]:
            continue
        nom = re.sub(r"^\d+\.\s*", "", sek["nom"]) or "Nazariya"
        if nom.lower().startswith("yodda tuting"):
            continue
        qq = nazariya_qatorlari(sek, rasm_nomi)
        for j, q in enumerate(qq):
            last = j == len([x for x in qq if not x.get("qiziq")]) - 1
            tek = ""
            if last and tk < len(tekshiruv):
                tek = tekshiruv[tk]; tk += 1
            doska = "\n".join(q["doska"])
            R.append(("tushuncha", "", (nom if j == 0 else nom + " (davomi)")[:80] if not q.get("qiziq") else "💡 Bilasizmi?",
                      belgilarni_mosla(q["ovoz"], q["doska"])[:1450], doska, q["rasm"], "", "", "", "", "", tek, "", "", ""))
    yodda = []
    for sek in [x for k in NAZARIYA for x in dars["bolim"].get(k, [])]:
        if sek["nom"].lower().startswith("yodda tuting"):
            yodda = [b["text"] for b in sek["b"] if b.get("text")]
    # namunaviy yechimlar
    nam, cur = [], None
    for b in dars["bolim"].get("namunaviy yechimlar", []):
        st, t = b.get("style", ""), b.get("text", "")
        if st == "Namuna":
            m = re.match(r"^(\d+)-namuna\s*(★)?\s*(.*)$", t, re.S)
            cur = {"shart": (m.group(3) if m else t).strip(), "yulduz": bool(m and m.group(2)), "qadam": [], "javob": ""}; nam.append(cur); continue
        if cur is None:
            continue
        if st == "Javob":
            cur["javob"] = re.sub(r"^Javob:\s*", "", t); continue
        if st == "Yechim" or not t:
            continue
        if b["t"] == "img":
            cur["qadam"].append(f"[rasm: {rasm_nomi(b['src'])}]"); continue
        cur["qadam"].append(t)
    for k, n in enumerate(nam, 1):
        yechim = "\n".join(re.sub(r"\s+", " ", q) for q in n["qadam"] if not q.startswith("[rasm")) + (f"\nJavob: {n['javob']}" if n["javob"] else "")
        R.append(("misol", f"N{k:02d}", f"{k}-namuna", n["shart"][:900], "", "", "", javob_qiymat(n["javob"]), yechim[:2500], "", "", "", "", "qiyin" if n["yulduz"] else "o‘rta", ""))
    # mashqlar, spiral
    for bolim, kalit, prefiks in AMALIY:
        for m in raqamli(dars["bolim"].get(bolim, [])):
            j = jv.get(kalit, {}).get(m["n"], "")
            yulduz = m["matn"].count("★") + m["matn"].count("●")
            matn = re.sub(r"\*?\[[A-Z]\d{2}\.\d{2}(?:,\s*[A-Z]\d{2}\.\d{2})*\]\*?", "", m["matn"].replace("★", "").replace("●", "")).strip()
            kal = jv.get("kalit", {}).get(m["n"], "") if kalit == "mashq" else ""
            yech = (yechimlar.get(m["n"], "") if kalit == "mashq" else "") or kal
            yechim = (yech + "\n" if yech else "") + (f"Javob: {j}" if j else "")
            R.append(("masala", f"{prefiks}{m['n']:02d}", f"{bolim.capitalize()} {m['n']}"[:60], matn[:900], "", "", "", javob_qiymat(j),
                      yechim.strip()[:2500], "", "", "", "", "qiyin" if yulduz >= 2 else "o‘rta" if yulduz == 1 or kalit != "mashq" else "oson",
                      ishora.get(m["n"], "")[:600] if kalit == "mashq" else ""))
    # test
    for t in tests:
        h = tj.get(t["n"], "")
        if len(t["var"]) >= 2 and h:
            R.append(("test", f"T{t['n']:02d}", f"Test {t['n']}", t["matn"][:900], "", "", "\n".join(f"{'ABCDEF'[k]}) {v}" for k, v in enumerate(t["var"][:6])), h,
                      "", "", "", "", "", "o‘rta", ""))
    if yodda:
        R.append(("xulosa", "", "🌟 Yodda tuting", " ".join(yodda)[:MAX_OVOZ], "\n".join(yodda[:7]), "", "", "", "", "", "", "", "", "", ""))
    return R


def nazorat_qatorlari(dars, jv):
    R = []
    tests = raqamli(dars["bolim"].get("test", []) + [b for v in dars["bolim"].values() for b in (v if isinstance(v, list) else []) if isinstance(b, dict) and "t" in b])
    seen = set()
    for t in tests:
        if t["n"] in seen: continue
        seen.add(t["n"])
        h = jv.get("test", {}).get(t["n"], "")
        if len(t["var"]) >= 2 and h:
            R.append(("test", f"T{t['n']:02d}", f"Savol {t['n']}", t["matn"][:900], "", "", "\n".join(f"{'ABCDEF'[k]}) {v}" for k, v in enumerate(t["var"][:6])), h,
                      "", "", "", "", "", "o‘rta", ""))
    return R
