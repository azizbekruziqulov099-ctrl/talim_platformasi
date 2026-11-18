import random
import sys
from fractions import Fraction
sys.dont_write_bytecode = True
from modules import mat_mock as m


def test_tuzilma_va_noyoblik():
    a, b = m.imtihon_tuz("s1"), m.imtihon_tuz("s2")
    assert len(a) == 45 and sum(1 for q in a if q["tur"] == "ochiq") == 10
    assert [q["savol"] for q in a] != [q["savol"] for q in b]
    assert [q["savol"] for q in m.imtihon_tuz("s1")] == [q["savol"] for q in a]
    assert sorted(i for q in a for i in q["bandlar"]) == list(range(55))


def test_ball_monoton_va_chegaralar():
    sav = m.imtihon_tuz("x")
    hamma = {}
    for q in sav:
        if q["tur"] == "ochiq":
            for qq in q["qismlar"]:
                hamma[f"{q['slot']}{qq['h']}"] = qq["javob"] if "frac" not in qq["javob"] else str(Fraction(qq["son"]))
                hamma[f"{q['slot']}{qq['h']}"] = qq["son"]
        else:
            hamma[str(q["slot"])] = q["javob"]
    top = m.baholash("x", hamma)
    bosh = m.baholash("x", {})
    assert top["xom"] == 55 and top["ball"] > 65 and top["sertifikat"]
    assert bosh["xom"] == 0 and bosh["ball"] < 30
    yarim = {k: v for i, (k, v) in enumerate(hamma.items()) if i % 2 == 0}
    assert bosh["ball"] < m.baholash("x", yarim)["ball"] < top["ball"]


def test_ochiq_son():
    assert m.ochiq_son("5,5") == Fraction(11, 2) and m.ochiq_son("-11/2") == Fraction(-11, 2) and m.ochiq_son("abc") is None


def test_ko_p_seed():
    for s in range(60):
        for q in m.imtihon_tuz(f"k{s}"):
            assert q["yechim"]
            if q["tur"] == "yopiq":
                assert q["javob"] in "ABCD" and len(set(q["variantlar"])) == 4
