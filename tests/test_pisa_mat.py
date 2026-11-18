import random
import sys
sys.dont_write_bytecode = True
from modules import pisa_mat as P, pisa_mat_g as G


def test_hammasi_shablon():
    for m, lst in G.SH.items():
        for f, t in lst:
            for sd in range(150):
                q = f(random.Random(sd))
                assert q["tur"] == ("yopiq" if t == "yopiq" else "ochiq")
                if q["tur"] == "yopiq":
                    assert len(set(q["variantlar"])) == 4 and q["javob"] in "ABCD"


def test_30_ta_va_mukammal():
    for m in [k for k in P.MAVZULAR if k in G.SH]:
        for tur in ("mashq", "test"):
            sv = P.tuz(m, tur, "s1")
            assert len(sv) == 30 and sv == P.tuz(m, tur, "s1")
            jav = {}
            for i, q in enumerate(sv, 1):
                if q["tur"] == "yopiq":
                    jav[str(i)] = q["javob"]
                else:
                    for z in q["qismlar"]:
                        jav[f"{i}{z['h']}"] = z["son"]
            r = P.baholash(m, tur, "s1", jav)
            assert r["ball"] == r["maks"] and r["foiz"] == 100
            assert P.baholash(m, tur, "s1", {})["ball"] == 0
        assert len(P.dars_tuz(m)["qadamlar"]) >= 6
