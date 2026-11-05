"""REV339: server albomi — frontend qoidalari bilan bir xil."""
from datetime import date, timedelta
from modules.bola_albom import stiker_ber, bosh, orol_soni


def test_albom_qoidalari():
    a = bosh(); d = date(2026, 11, 2)   # dushanba
    a, n = stiker_ber(a, "MT45-01", d); assert n["stiker"] == "stiker_quyon" and n["mukofot"] is None
    a, n = stiker_ber(a, "MT45-01", d); assert n is None                     # bir kunda bir marta
    for i in range(2, 6):
        a, n = stiker_ber(a, f"MT45-0{i}", d + timedelta(days=i - 1))
    assert a["jami"] == 5 and a["sanoq"]["medal_oltin"] == 1
    assert orol_soni(a, d + timedelta(days=5)) == 5 and a["orollar"] == 1
    assert orol_soni(a, d + timedelta(days=8)) == 0                          # yangi hafta
