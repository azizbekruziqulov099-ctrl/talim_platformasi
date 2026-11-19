"""Xalqaro baholash mavzulari -> Miya Excel (mavzu varoqli): dars + mashq (30) + test (30). Ishlatish: python tools/miya_xb_eksport.py CHIQISH_PAPKA"""
import os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import pisa_mat as P
from modules.ai_miya_varoq import template_workbook, parse_sheets

FAN = {"T11_G4_M": ("Matematika", "4-sinf (TIMSS)"), "T11_G8_M": ("Matematika", "8-sinf (TIMSS)"),
       "T11_G4_S": ("Tabiiy fan", "4-sinf (TIMSS)"), "T11_G8_S": ("Fan (fizika, kimyo, biologiya, geografiya)", "8-sinf (TIMSS)"),
       "P_M": ("Matematika", "PISA"), "P_S": ("Tabiiy fan", "PISA"), "P_R": ("O‘qish savodxonligi", "PISA"), "P_F": ("Moliyaviy savodxonlik", "PISA")}
L = "ABCD"
ETIKET = {"P_M": "PISA mat", "P_S": "PISA fan", "P_R": "PISA o‘qish", "P_F": "PISA moliya", "T11_G4_M": "TIMSS 4 mat", "T11_G8_M": "TIMSS 8 mat", "T11_G4_S": "TIMSS 4 fan", "T11_G8_S": "TIMSS 8 fan"}
PREF = {"P_M": "XPM", "P_S": "XPS", "P_R": "XPR", "P_F": "XPF", "T11_G4_M": "X4M", "T11_G8_M": "X8M", "T11_G4_S": "X4S", "T11_G8_S": "X8S"}
TASHLA = set()
IKKI = {}   # bazada bir xil nomli ikki mavzu — ikkalasiga ham   # bazada bir xil nomli 2 ta mavzu bor — kod aniqlanmaguncha qo'shilmaydi
D = lambda s: re.sub(r"\$", "", s or "")


def sat(s):
    return "\n".join(x.strip() for x in str(s).split("\n") if x.strip())


def anim(line):
    """Oddiy arifmetik satr -> doska animatsiya buyrug'i (raqamlar paydo bo'lib o'z xonasiga o'tiradi)."""
    t = D(line).replace("−", "-").replace("·", "*").replace("×", "*").replace(" ", "")
    m = re.fullmatch(r"(\d{2,6})([+\-])(\d{2,6})(?:=\d+)?", t)
    if m and (m.group(2) == "+" or int(m.group(1)) >= int(m.group(3))):
        return f"USTUN: {m.group(1)}{m.group(2)}{m.group(3)}"
    m = re.fullmatch(r"(\d{2,6})([*:])(\d{1,3})(?:=\d+)?", t)
    if m:
        return f"BOLISH: {m.group(1)}:{m.group(3)}" if m.group(2) == ":" else f"USTUN: {m.group(1)}*{m.group(3)}"
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})", t)
    if m and 0 < int(m.group(1)) < int(m.group(2)) <= 12:
        return f"DOIRA_KASR: {m.group(1)}/{m.group(2)}"
    return line


def dars_qatorlari(k):
    d = P.dars_tuz(k); rows = []
    for q in d["qadamlar"]:
        t = q["turi"]
        doska = sat(q.get("doska", "")); ovoz = q.get("ovoz", "")
        if t in ("kirish", "qoida"):
            satr = [x for x in doska.split("\n") if x]
            # [n] belgilari: gap bo'laklari doska qatorlariga teng taqsimlanadi
            gap = re.split(r"(?<=[.!?])\s+", ovoz.strip())
            if satr:
                per = max(1, -(-len(gap) // len(satr)))
                ovoz = " ".join((f"[{i // per + 1}] " if i % per == 0 and i // per < len(satr) else "") + g for i, g in enumerate(gap))
            if t == "qoida" and satr:
                satr = [anim(x) for x in satr]; satr[0] = satr[0] if satr[0].split(":")[0] in ("USTUN", "BOLISH", "DOIRA_KASR") else "QOIDA: " + satr[0]; doska = "\n".join(satr)
            rows.append({"turi": "kirish" if t == "kirish" else "tushuncha", "sarlavha": q["sarlavha"], "matn": ovoz, "doska": doska})
        elif t == "misol":
            sat_ = [x for x in doska.split("\n") if x]
            rows.append({"turi": "misol", "sarlavha": q["sarlavha"], "matn": D(q.get("savol", "")),
                         "yechim": "\n".join(f"{anim(x)} || {D(x)}" for x in sat_), "javob": D(sat_[-1].replace("Javob:", "").strip()) if sat_ else "",
                         "maslahat": "Avval shartdan kerakli sonlarni ajrating.\nHar qadamni doskadagidek yozib boring.", "qiyinlik": "oson", "rasm": ""})
        elif t == "xulosa":
            rows.append({"turi": "xulosa", "sarlavha": "Esda tut", "matn": ovoz, "doska": doska})
    return d, rows


def savol_qatorlari(k, tur, bosh, kod_h):
    rows = []; n = 0
    for q in P.tuz(k, tur, 1):
        yech = sat(q["yechim"]); n += 1
        if q["tur"] == "yopiq" and tur == "test":
            j = q["javob"]
            xi = "\n".join(f"{L[i]} => Bu javob noto‘g‘ri. To‘g‘ri yechimni qayta ko‘rib chiqing." for i in range(4) if L[i] != j)
            rows.append({"turi": "test", "kod": f"T{n:02d}", "sarlavha": f"Test {n}", "matn": q["savol"],
                         "variantlar": "\n".join(f"{L[i]}) {v}" for i, v in enumerate(q["variantlar"])), "javob": j, "yechim": yech,
                         "xato_izohi": xi, "qiyinlik": "o'rta"})
        elif q["tur"] == "yopiq":
            j = q["javob"]; tv = q["variantlar"][ord(j) - 65]
            rows.append({"turi": "masala", "kod": f"{kod_h}{n:02d}", "sarlavha": f"Mashq {n}",
                         "matn": q["savol"] + "\n" + "  ".join(f"{L[i]}) {v}" for i, v in enumerate(q["variantlar"])),
                         "javob": f"{j}|{D(tv)}", "yechim": yech, "maslahat": "Shartni diqqat bilan o‘qing.\nNoto‘g‘ri variantlarni yechim bilan tekshirib chiqarib tashlang.", "qiyinlik": "o'rta"})
        else:
            qs = q["qismlar"]
            matn = q["savol"] + "\n" + "\n".join(f"{z['h']}) {z['savol']}" for z in qs)
            javob = "; ".join(f"{z['h']}) {D(z['javob'])}" for z in qs) if len(qs) > 1 else D(qs[0]["javob"])
            rows.append({"turi": "masala", "kod": f"{'S' if tur == 'test' else kod_h}{n:02d}" if tur != "test" else f"O{n:02d}",
                         "sarlavha": f"{'Mashq' if tur == 'mashq' else 'Ochiq test'} {n} ({q['ball']} ball)", "matn": matn, "javob": javob,
                         "yechim": yech, "maslahat": "Avval ma’lumotni ajrating, keyin reja tuzing.", "qiyinlik": "o'rta"})
    return rows


def main(out):
    os.makedirs(out, exist_ok=True)
    guruh = {}
    for k, m in P.MAVZULAR.items():
        if k in P.G.SH:
            guruh.setdefault(m.get("toplam"), []).append(k)
    files = []
    for tp, ks in guruh.items():
        fan, sinf = FAN.get(tp, (tp, "kurs"))
        book = {"kitob_nomi": f"Xalqaro baholash — {fan}, {sinf}", "fan": fan, "sinf": sinf, "kitob_kodi": f"XB-{tp}", "til": "uz",
                "kod_prefiksi": PREF[tp], "mualliflar": "Kabutar Ta’lim"}
        pre = []
        for i, k in enumerate([x for x in sorted(ks) if x not in TASHLA], 1):
            d, rows = dars_qatorlari(k)
            rows += savol_qatorlari(k, "mashq", "", "S") + savol_qatorlari(k, "test", "", "S")
            for kod in IKKI.get(k, [""]):
                pre.append({"mavzu_kodi": kod, "mavzu_nomi": f'{P.MAVZULAR[k]["nom"]} ({ETIKET[tp]})', "mavzu_raqami": str(len(pre) + 1), "rows": rows})
        wb = template_workbook(prefill=pre, book=book)
        path = os.path.join(out, f"miya_{tp}.xlsx"); wb.save(path); files.append(path)
        import openpyxl
        r = parse_sheets(openpyxl.load_workbook(path))
        print(tp, len(ks), "mavzu", "xato:", [e for e in r["errors"]][:3] if isinstance(r, dict) and "errors" in r else r.get("summary"))
    return files


if __name__ == "__main__":
    main(sys.argv[1])
