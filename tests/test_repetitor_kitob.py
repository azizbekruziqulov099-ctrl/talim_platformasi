from modules import repetitor_kitob as rk
from modules.kurslar import kurs_of, REPETITOR_FANLAR


def test_148_dars_tartibi():
    assert len(rk.NOMLAR) == 148 and len(set(rk.NOMLAR)) == 148
    assert rk.tartib_raqam(rk.NOMLAR[0] + rk.QOSHIMCHA) == 1
    assert rk.tartib_raqam(rk.NOMLAR[147]) == 148
    assert rk.korinadigan_nom(rk.NOMLAR[4] + rk.QOSHIMCHA).startswith("5-dars. ")


def test_kurs_sinfga_bogliq_emas():
    kalit, kat, nomi, _ = kurs_of("Matematika", "Repetitor")
    assert kalit == rk.KALIT and kat == "repetitor"
    assert kurs_of("Matematika", "11")[0] == "maktab|Matematika|11"   # eski kurslar o'zgarmaydi
    assert kurs_of("Matematika", "5-7")[0] == "repetitor|Matematika|5-7"


def test_sql_sharti_parametr_bilan_ishlaydi():
    assert "%%" in rk.nom_sql("d") and "(Repetitor)" in rk.nom_sql("d")
