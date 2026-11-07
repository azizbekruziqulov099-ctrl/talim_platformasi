from modules import ai_miya_varoq as v
from modules import dars_xonasi as dx

def test_tekshiruv_variantlari():
    assert v.tekshiruv_variantlari("5 | 4 | 6") == ("5", ["5", "4", "6"])
    assert v.tekshiruv_variantlari("katta") == ("katta", [])
    assert len(v.tekshiruv_variantlari(" | ".join(str(i) for i in range(9)))[1]) == 6
    assert v.tekshiruv_ajrat("Nechta olma? => 5 | 4 | 6") == ("Nechta olma?", "5 | 4 | 6")

def test_olti_variantli_test():
    assert v.parse_options("A) 1\nB) 2\nC) 3\nD) 4\nE) 5\nF) 6") == ["1", "2", "3", "4", "5", "6"]
    assert dx.xato_izohlari("F => chunki") == {"5": "chunki"}

def test_markaz_kursi():
    from modules import kurslar as k
    assert k.kurs_of("Matematika — markaz", "1-kitob")[1] == "markaz"
    assert k.kurs_of("Matematika", "1")[1] == "fanlar"

def test_oliy_kurs():
    from modules import kurslar as k
    assert k.kurs_of("Ehtimollar nazariyasi va matematik statistika", "2 kurs")[1] == "oliy"

def test_repetitor_guruhlari():
    from modules import kurslar as k
    assert k.repetitor_guruhi("Matematika", "3") == "1-4" and k.repetitor_guruhi("Matematika", "6") == "5-7"
    assert k.repetitor_guruhi("Algebra", "9") == "7-11" and k.repetitor_guruhi("Geometriya", "11") == "7-11"
    assert k.repetitor_guruhi("Ona tili", "9") is None and k.repetitor_guruhi("Fransuz tili", "5") is None   # REV421: tillar yo'q
    assert k.repetitor_guruhi("Matematika", "x") is None
    assert k.kurs_of("Matematika", "1-4") == ("repetitor|Matematika|1-4", "repetitor", "Matematika · 1–4-sinf", "1-4")

def test_repetitor_narxi():
    from modules import kurslar as k
    asl = k.narx_ol
    try:
        k.narx_ol = lambda cur, kalit, kat: (0, 5) if kat == "repetitor" else (10000, 5)
        assert k.kurs_narxi(None, "repetitor|Matematika|5-7", "repetitor") == (24000, 5)   # 3 × 10 000 − 20%
        assert k.kurs_narxi(None, "repetitor|Matematika|1-4", "repetitor") == (32000, 5)
        k.narx_ol = lambda cur, kalit, kat: (15000, 3)
        assert k.kurs_narxi(None, "repetitor|Algebra|7-11", "repetitor") == (15000, 3)       # admin narxi ustun
    finally:
        k.narx_ol = asl
    assert k.repetitor_kaliti("Matematika", "6") == "repetitor|Matematika|5-7" and k.repetitor_kaliti("Fizika", "6") is None
