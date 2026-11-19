"""Yangi mavzular tekshiruvi: python tools/xb_tekshir.py pm_ [prefiks]  — har generator 200 urinish, 30 xil savol, javob variantlar ichida."""
import sys, os, random, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import pisa_mat as P, pisa_mat_g as G
pref = sys.argv[1] if len(sys.argv) > 1 else "pm_"
bad = 0
for k in sorted(P.MAVZULAR):
    if not k.startswith(pref): continue
    sh = G.SH.get(k, [])
    xato = []
    for f, t in sh:
        for s in range(150):
            try:
                q = f(random.Random(s))
                if q["tur"] != t: xato.append(f"{f.__name__}: tur {q['tur']}!={t}"); break
                if t == "yopiq":
                    assert q["javob"] in "ABCD" and len(set(q["variantlar"])) == 4, "variantlar"
                else:
                    assert q["qismlar"] and all(z["javob"] != "" for z in q["qismlar"]), "qism"
                assert q["yechim"].strip() and q["savol"].strip(), "bo'sh"
            except Exception as e:
                xato.append(f"{f.__name__} seed{s}: {type(e).__name__} {e}"); break
    kor = set()
    try:
        for s in range(60):
            for q in (P.tuz(k, "mashq", f"t{s}") if not xato else []):
                kor.add(q["savol"] + json.dumps(q.get("qismlar", q.get("variantlar")), ensure_ascii=False))
    except Exception as e:
        xato.append(f"tuz: {type(e).__name__} {e}")
    nm = len({(q) for q in kor})
    if not xato:
        for tur in ("mashq", "test"):
            for sd in ("s1", "s2", "s3"):
                sv = P.tuz(k, tur, sd); jav = {}
                for i, q in enumerate(sv, 1):
                    if q["tur"] == "yopiq": jav[str(i)] = q["javob"]
                    else:
                        for z in q["qismlar"]: jav[f"{i}{z['h']}"] = z["son"]
                r = P.baholash(k, tur, sd, jav)
                if r["ball"] != r["maks"]: xato.append(f"to'g'ri javoblar 100% bermadi ({tur},{sd}: {r['ball']}/{r['maks']})"); break
    yop = sum(1 for f, t in sh if t == "yopiq"); och = len(sh) - yop
    holat = "OK " if not xato and nm >= 60 else "XATO"
    if holat != "OK ": bad += 1
    print(holat, k, f"gen={len(sh)} (y{yop}/o{och}) xil={nm}", xato[:3])
print("jami xato mavzu:", bad)
