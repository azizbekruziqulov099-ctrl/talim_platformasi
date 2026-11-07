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
