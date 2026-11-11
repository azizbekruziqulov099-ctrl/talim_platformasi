"""REV508: 5-sinf Miya paketini qayta qurish — har darsdagi misol, mashq va testlar xilma5 bilan almashtiriladi
(nazariya, kirish va xulosa qatorlari o'z joyida qoladi). Sifat tekshiruvi: bitta shablon 30% dan oshsa — xato."""
import re, sys, collections, random
from openpyxl import load_workbook
import xilma5 as X

def oddiy(j):
    j = str(j)
    m = re.fullmatch(r"\\frac\{(\d+)\}\{(\d+)\}", j)
    if m: return f"{m.group(1)}/{m.group(2)}"
    m = re.fullmatch(r"(\d+)\\frac\{(\d+)\}\{(\d+)\}", j)
    if m: return f"{m.group(1)} {m.group(2)}/{m.group(3)}"
    return j

def tex(v):
    v = str(v)
    return f"${v}$" if ("\\frac" in v or re.fullmatch(r"-?\d+([.,]\d+)?", v)) else v

def qur(manba, chiqish, urug=2026, tanla=None):
    wb = load_workbook(manba)
    hisob = collections.Counter(); oilasiz = []
    for si, ws in enumerate(wb.worksheets[2:], 1):
        nom = ws.cell(2, 7).value
        t = X.topshiriqlar(nom, urug * 1000 + si, tanla=tanla)
        if not t:
            oilasiz.append(nom); continue
        misol, masala, test = t
        rows = [[ws.cell(r, c).value for c in range(1, 15)] for r in range(7, ws.max_row + 1)]
        rows = [r for r in rows if any(x not in (None, "") for x in r)]
        bosh = [r for r in rows if r[1] not in ("misol", "masala", "test", "xulosa")]
        oxir = [r for r in rows if r[1] == "xulosa"]
        yangi = []
        for i, (q, j, y, xs, _) in enumerate(misol, 1):
            yangi.append([None, "misol", f"N{i:02d}", "Namunaviy misol", q, "", "", "", "", f"{y}\nJavob: {tex(j)}", "", "", "", ""])
        for i, (q, j, y, xs, _) in enumerate(masala, 1):
            yangi.append([None, "masala", f"M{i:02d}", f"Mashq {i}", q, "", "", "", oddiy(j), f"{y}\nJavob: {tex(j)}", "", "", "", ""])
        for i, (q, j, y, xs, _) in enumerate(test, 1):
            vs = [str(j)] + [str(x) for x in xs if str(x) != str(j)][:3]
            def _yaqin(j, k):   # tabiiy xato variantlari: o'nli — 10 marta katta/kichik, butun — atrofidagi «chiroyli» sonlar
                t = str(j).replace(",", ".")
                try:
                    v = float(t)
                except ValueError:
                    return f"{j} emas" if k == 0 else None
                if "." in t:
                    c = [v * 10, v / 10, v * 100][k % 3]
                    return f"{c:.4f}".rstrip("0").rstrip(".").replace(".", ",")
                step = max(1, int(abs(v)) // 10 or 1)
                return str(int(v) + [step, -step, 2 * step][k % 3])
            k_ = 0
            while len(vs) < 4 and k_ < 9:
                c_ = _yaqin(j, k_); k_ += 1
                if c_ and c_ not in vs: vs.append(c_)
            vs = list(dict.fromkeys(vs))[:4]
            rr = random.Random(f"{nom}{i}"); rr.shuffle(vs)
            harf = "ABCD"[vs.index(str(j))]
            yangi.append([None, "test", f"T{i:02d}", "Test", q, "", "", "\n".join(f"{h}) {tex(v)}" for h, v in zip("ABCD", vs)), harf, "", "", "", "", ""])
        hammasi = bosh + yangi + oxir
        for r in range(7, ws.max_row + 1):
            for c in range(1, 15):
                ws.cell(r, c).value = None
        for k, row in enumerate(hammasi):
            row[0] = k + 1
            for c, v in enumerate(row, 1):
                ws.cell(7 + k, c).value = v
        # sifat: bitta shablon ulushi
        shab = collections.Counter(re.sub(r"\d+([.,]\d+)?", "#", str(r[4]))[:50] for r in yangi)
        hisob["dars"] += 1
        if shab.most_common(1)[0][1] > 0.3 * len(yangi): hisob["shablon_ko'p"] += 1
    wb.save(chiqish)
    return hisob, oilasiz

if __name__ == "__main__":
    tanla = None
    if len(sys.argv) > 3:   # masalan: python3 qayta5.py manba.xlsx chiqish.xlsx xilma6
        tanla = __import__(sys.argv[3]).oila_tanla
    h, o = qur(sys.argv[1], sys.argv[2], tanla=tanla)
    print(dict(h)); print("oilasiz:", o)
