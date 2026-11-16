from datetime import date
from modules.xb_yosh import yosh_hisobla, yonalishlar, ruxsat_etilgan, PISA, TIMSS4, TIMSS8


def test_yosh_hisobla():
    assert yosh_hisobla("2016-11-17", date(2026, 11, 16)) == 9
    assert yosh_hisobla("2016-11-16", date(2026, 11, 16)) == 10
    assert yosh_hisobla("2030-01-01", date(2026, 11, 16)) is None and yosh_hisobla("xato") is None


def test_yonalish_yoshga_mos():
    assert yonalishlar(6) == [] and yonalishlar(None) == []
    for y in range(7, 12):
        assert yonalishlar(y) == list(TIMSS4)
    for y in range(12, 15):
        assert yonalishlar(y) == list(TIMSS8)
    for y in (15, 16, 25):
        assert yonalishlar(y) == list(PISA)


def test_noto_gri_yoshga_chiqmaydi():
    # 4-sinf yoshidagi bolaga PISA, kattaga TIMSS 4-sinf hech qachon chiqmaydi
    assert not set(yonalishlar(9)) & set(PISA) and not set(yonalishlar(13)) & set(TIMSS4) and not set(yonalishlar(16)) & set(TIMSS4 + TIMSS8)
    assert ruxsat_etilgan(9, ["P_M", "T11_G4_S", "T11_G8_M"]) == ["T11_G4_S"]


def test_kirish_tartibi_osondan_qiyinga():
    import importlib, sys
    m = importlib.import_module("modules.xalqaro_baholash")
    sv = [{"id": f"s{i}", "xalqaro_ortacha": p} for i, p in enumerate([20, 90, 55, 70, 35])]
    out = [s["xalqaro_ortacha"] for s in m.kirish_tartibi(sv)]
    assert out == sorted(out, reverse=True)   # to'g'ri yechilish foizi kamayadi = qiyinlik ortadi
    assert m.IMTIHON_TURLARI["kirish"]["4"][0] == m.IMTIHON_TURLARI["kirish"]["P"][0] == 15


def test_kop_javobli_savol_tekshiruvi():
    import importlib
    m = importlib.import_module("modules.xalqaro_baholash")
    v = {"turi": "kop", "togri": [0, 2]}
    assert m.tekshir(v, "A,C") and m.tekshir(v, "ca")
    assert not m.tekshir(v, "A") and not m.tekshir(v, "ABC") and not m.tekshir(v, "")
