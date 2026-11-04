from modules.kurslar import kurs_of, qaror, asos_fan, izoh_tili


def test_kurs_kaliti_va_kategoriya():
    assert kurs_of("Matematika", "5") == ("maktab|Matematika|5", "fanlar", "Matematika · 5-sinf", "5")
    assert kurs_of("Matematika (izoh: rus)", "5")[0] == "maktab|Matematika|5"          # uch til — bitta kurs
    assert kurs_of("Ingliz tili (izoh: ingliz)", "7")[1] == "tillar"
    assert kurs_of("Geometriya", "9")[1] == "fanlar"
    assert kurs_of("Ingliz tili — Erkin til", "A1")[:2] == ("erkin|Ingliz tili — Erkin til|A1", "erkin")
    assert kurs_of("Ingliz tili", "2-3 yosh")[:2] == ("bolalar|Ingliz tili", "bolalar")
    assert kurs_of("Ingliz tili", "6-7 yosh")[0] == kurs_of("Ingliz tili (izoh: rus)", "4-5 yosh")[0]   # yoshga bo'linmaydi
    assert asos_fan("Algebra (izoh: ingliz)") == "Algebra" and izoh_tili("Algebra (izoh: rus)") == "ru" and izoh_tili("Algebra") == "uz"


def test_kirish_qoidasi():
    assert qaror("admin", 50000, 5, 30, False)[0] and qaror("oqituvchi", 50000, 5, 30, False)[0]
    assert qaror("oquvchi", 0, 5, 30, False) == (True, "bepul_kurs")          # narx belgilanmagan — bepul
    assert qaror("oquvchi", 50000, 5, 0, False) == (True, "bepul_dars")
    assert qaror("oquvchi", 50000, 5, 4, False) == (True, "bepul_dars")       # 5-dars (indeks 4) bepul
    assert qaror("oquvchi", 50000, 5, 5, False) == (False, "tolov_kerak")     # 6-dars — to'lov
    assert qaror("oquvchi", 50000, 5, 5, True) == (True, "obuna")
    assert qaror("bogcha", 50000, 5, 9, False, True, "bolalar") == (True, "bogcha_obuna")
    assert qaror("bogcha", 50000, 5, 9, False, True, "fanlar")[0] is False   # bog'cha obunasi faqat bolalar kurslariga


def test_rev303_xalqaro_maktab_darslari_funksiyasi_bor():
    from modules.xalqaro_baholash import maktab_darslari_ol
    import inspect
    src = inspect.getsource(maktab_darslari_ol)
    assert "ai_brain_units" in src and "(izoh: rus)" in src and "(izoh: ingliz)" in src   # faqat ochiladigan darslar, 3 tilda


def test_rev304_son_matnli_qiymat():
    from modules.xalqaro_baholash import _son
    assert _son(45) == 45 and _son("45") == 45 and _son("4,5") == 4.5 and _son("-") is None and _son(None) is None and _son(True) is None
