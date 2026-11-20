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


def test_rev315_besh_til():
    assert izoh_tili("Matematika (izoh: nemis)") == "de" and izoh_tili("Matematika (izoh: ispan)") == "es"
    assert kurs_of("Matematika (izoh: ispan)", "5")[0] == kurs_of("Matematika", "5")[0]   # 5 til — bitta kurs


def test_rev321_oz_tilida():
    from modules.kurslar import oz_tilida
    assert oz_tilida("Ingliz tili (izoh: ingliz)") and oz_tilida("Rus tili — Erkin til (izoh: rus)")
    assert not oz_tilida("Ingliz tili (izoh: rus)") and not oz_tilida("Ingliz tili") and not oz_tilida("Matematika (izoh: ingliz)")


def test_doktorantura_oliy_kursi():   # REV470: 13.00.02 tayanch doktorantura kursi — «Oliy ta'lim kurslari»da
    from modules.kurslar import kurs_of
    fan = "13.00.02 – Ta’lim va tarbiya nazariyasi va metodikasi"
    assert kurs_of(fan, "doktorantura") == (f"oliy|{fan}|doktorantura", "oliy", fan, "doktorantura")
    assert kurs_of(fan, "Doktorantura")[1] == "oliy"
    assert kurs_of("Matematika", "2 kurs")[1] == "oliy"          # eski qoida o'zgarmagan


def test_doktorantura_70_foiz():   # REV470: keyingi dars faqat dars testidan 70% olinganda ochiladi
    from modules.kurslar import doktorantura_mi, mashq_otdi, test_otganlar, tartib_qulf
    assert doktorantura_mi("doktorantura") and doktorantura_mi("Doktorantura") and not doktorantura_mi("2 kurs")

    class Cur:
        def execute(self, *a): pass
        def fetchall(self): return [{"topic_code": "A", "togri": 7, "jami": 10}, {"topic_code": "B", "togri": 6, "jami": 10},
                                    {"topic_code": "C", "togri": 0, "jami": None}]
    assert test_otganlar(Cur(), 1, "oliy|X|doktorantura") == {"A"}
    assert mashq_otdi(7, 10) and not mashq_otdi(6, 10)
    # B tugatilgan, lekin 70% emas — tugaganlar ro'yxatiga kirmaydi, B navbatda qoladi, C yopiq
    holat = tartib_qulf([("A", True), ("B", True), ("C", True)], {"A"}, set(), False)
    assert [h for _, h in holat] == ["tugadi", "navbat", "qulf"]


def test_doktorantura_dars_tartibi():   # REV470: «1.2.», «1.1-b.», «1.10.» — savol raqami bo'yicha, DTS kodidan qat'i nazar
    from modules.kurslar import _dars_tartibi
    rows = [{"nom": "1.10. O'quvchi faoliyati", "topic_code": "a1"}, {"nom": "1.1-b. Vazifalar", "topic_code": "a9"},
            {"nom": "2.1. Samarqand", "topic_code": "a2"}, {"nom": "1.1. Pedagogika fanining maqsad", "topic_code": "a5"},
            {"nom": "1.2. Qonun", "topic_code": "a3"}]
    assert [r["nom"][:5] for r in _dars_tartibi(rows, savol_raqami=True)] == ["1.1. ", "1.1-b", "1.2. ", "1.10.", "2.1. "]


def test_doktorantura_nazorat_zinapoyasi():   # REV470: bo'lim ichida har 5 darsda mini-test, bo'lim oxirida bo'lim testi, oxirida yakuniy
    from modules.kurslar import nazorat_doktorantura, NAZORAT
    nomlar = [f"1.{i}. Savol" for i in range(1, 13)] + ["2.1-a. A", "2.1-b. B", "2.2. C"]
    items = [{"topic_code": f"t{k}", "nomi": n, "ochiq": True} for k, n in enumerate(nomlar)]
    out = nazorat_doktorantura(items)
    nz = [(x["topic_code"], x["nazorat"], len(x["darslar"])) for x in out if x.get("nazorat")]
    assert nz == [("NZ:B1M5", "dk_mini", 5), ("NZ:B1M10", "dk_mini", 5), ("NZ:B1", "dk_bolim", 12), ("NZ:B2", "dk_bolim", 3),
                  ("NZ:YAKUNIY", "dk_yakuniy", 15)]
    assert out[5]["nomi"].endswith("1.1 – 1.5") and NAZORAT["dk_bolim"][2] == 30 and NAZORAT["dk_bolim"][3] == 70
    assert [x["topic_code"] for x in out if not x.get("nazorat")] == [x["topic_code"] for x in items]
    # bitta bo'lim bo'lsa — yakuniy imtihon qo'shilmaydi
    assert not any(x.get("nazorat") == "dk_yakuniy" for x in nazorat_doktorantura(items[:4]))
