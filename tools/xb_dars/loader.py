"""Xalqaro baholash darslari — matn formatidan Miya qatorlariga.

Format (bitta fayl — bir nechta mavzu):
## mavzu_kodi
@kirish Sarlavha | @tushuncha Sarlavha | @xulosa Sarlavha     — yangi qadam
OVOZ: ustoz gapi. [1] [2] — doska qatorlariga havola. {sekin} {tez} {past} {baland} {urgu} {pauza} — ohang belgilari
DOSKA: bitta doska qatori (buyruq: QOIDA:, USTUN:, DOIRA_KASR:, GRAFIK: ...). Qator ketma-ket qo'shiladi.
TEKSH: Savol? => to'g'ri javob [ | xato | xato ]   (yaqin savol — o'rgatilganning aynan o'zi emas)
SODDA: yengil tushuntirish   BOSHQA: boshqa usul
Davomli satr oldingi kalit davomi (bo'sh qator bilan ajratilmaydi).
"""
import re

KALIT = re.compile(r"^(OVOZ|DOSKA|TEKSH|SODDA|BOSHQA):\s*(.*)$")


def oqi(matn):
    mavzular, joriy, qadam, kalit = {}, None, None, None
    qoshimcha = False
    for xom in matn.splitlines():
        s = xom.rstrip()
        if not s.strip() or s.lstrip().startswith("#!"):
            continue
        if s.startswith("## "):
            nom = s[3:].strip().split()[0]
            qosh = nom.startswith("+")
            joriy = nom.lstrip("+")
            if not qosh or joriy not in mavzular: mavzular[joriy] = []
            qadam = None; qoshimcha = qosh; kalit = None
            if qosh:
                mavzular["__q__" + joriy] = mavzular.get("__q__" + joriy, [])
            continue
        m = re.match(r"^@(kirish|tushuncha|xulosa)\s+(.*)$", s)
        if m:
            qadam = {"turi": m.group(1), "sarlavha": m.group(2).strip(), "ovoz": "", "doska": [], "teksh": [], "sodda": "", "boshqa": ""}
            (mavzular["__q__" + joriy] if qoshimcha else mavzular[joriy]).append(qadam); kalit = None; continue
        m = KALIT.match(s)
        if m and qadam is not None:
            kalit, v = m.group(1), m.group(2).strip()
            if kalit == "OVOZ": qadam["ovoz"] = v
            elif kalit == "DOSKA": qadam["doska"].append(v)
            elif kalit == "TEKSH": qadam["teksh"].append(v)
            elif kalit == "SODDA": qadam["sodda"] = v
            elif kalit == "BOSHQA": qadam["boshqa"] = v
            continue
        if qadam is not None and kalit == "OVOZ":
            qadam["ovoz"] += " " + s.strip()
        elif qadam is not None and kalit == "SODDA":
            qadam["sodda"] += " " + s.strip()
        elif qadam is not None and kalit == "BOSHQA":
            qadam["boshqa"] += " " + s.strip()
        else:
            raise ValueError(f"Tushunarsiz satr ({joriy}): {s[:70]}")
    for k in [x for x in mavzular if x.startswith("__q__")]:
        q = mavzular.pop(k); asl = mavzular.get(k[5:])
        if asl is None: raise ValueError("qo'shimcha uchun asosiy mavzu yo'q: " + k[5:])
        if asl and asl[-1]["turi"] == "xulosa": asl[-1:-1] = q
        else: asl.extend(q)
    return mavzular


def qatorlar(qadamlar):
    out = []
    for q in qadamlar:
        r = {"turi": q["turi"], "sarlavha": q["sarlavha"], "matn": q["ovoz"].strip(), "doska": "\n".join(q["doska"])}
        if q["teksh"]: r["tekshiruv"] = "\n".join(q["teksh"])
        if q["sodda"]: r["sodda"] = q["sodda"].strip()
        if q["boshqa"]: r["boshqa_usul"] = q["boshqa"].strip()
        out.append(r)
    return out


def tekshir(kod, qadamlar):
    """Sifat tekshiruvi: xatolar ro'yxati."""
    x = []
    if not qadamlar or qadamlar[0]["turi"] != "kirish": x.append("birinchi qadam @kirish bo'lsin")
    if qadamlar and qadamlar[-1]["turi"] != "xulosa": x.append("oxirgi qadam @xulosa bo'lsin")
    t = [q for q in qadamlar if q["turi"] == "tushuncha"]
    if len(t) < 3: x.append(f"kamida 3 tushuncha kerak ({len(t)})")
    if sum(len(q["teksh"]) for q in qadamlar) < 4: x.append("kamida 4 tekshiruv savoli")
    for q in qadamlar:
        if q["turi"] != "xulosa" and len(q["ovoz"]) < 60: x.append(f"«{q['sarlavha']}»: ovoz juda qisqa")
        mats = (q["ovoz"] + " " + " ".join(q["doska"])).lower()
        for s in q["teksh"]:
            if " => " not in s: x.append(f"tekshiruv «{s[:30]}» => yo'q")
            else:
                savol = s.split(" => ")[0].strip().lower()
                if savol in mats: x.append(f"tekshiruv savoli darsdagi misolning aynan o'zi: {savol[:40]}")
        m = re.findall(r"\[(\d+)\]", q["ovoz"])
        if q["doska"] and q["turi"] != "kirish" and m and max(map(int, m)) > len(q["doska"]): x.append(f"«{q['sarlavha']}»: [n] doska qatoridan ko'p")
    if len(" ".join(q["ovoz"] for q in qadamlar)) < 1500: x.append("dars juda qisqa (<1500 belgi ovoz)")
    return x
