from modules.kurslar import tartib_qulf

D = [("a", True), ("b", True), ("c", True), ("d", True)]

def test_birinchi_tugadi_bugun_keyingisi_ertaga():
    r = tartib_qulf(D, {"a"}, {"a"}, False)
    assert [h for _, h in r] == ["tugadi", "ertaga", "qulf", "qulf"] and [o for o, _ in r] == [True, False, False, False]

def test_kecha_tugagan_keyingisi_ochiq():
    r = tartib_qulf(D, {"a"}, set(), False)
    assert [o for o, _ in r] == [True, True, False, False]

def test_oralab_otgan_oldingilari_ochiq():
    r = tartib_qulf(D, {"c"}, set(), False)
    assert [o for o, _ in r] == [True, True, True, True]

def test_pullik_yopiq_ochilmaydi_va_erkin():
    r = tartib_qulf([("a", True), ("b", False)], {"a"}, set(), False)
    assert r[1][0] is False
    assert all(o for o, _ in tartib_qulf(D, set(), set(), True))


def test_nazorat_zinapoyasi():
    from modules.kurslar import nazorat_qosh
    items = [{"topic_code": f"t{i}", "nomi": f"{i}-dars", "ochiq": True} for i in range(1, 25)]
    out = nazorat_qosh(items)
    nz = [(x["topic_code"], x["nazorat"]) for x in out if x.get("nazorat")]
    assert nz[:4] == [("NZ:3", "mini"), ("NZ:6", "oraliq"), ("NZ:9", "mini"), ("NZ:12", "oylik")]
    assert ("NZ:24", "maksimum") in nz and len(nz) == 8
    assert next(x for x in out if x["topic_code"] == "NZ:12")["darslar"] == [f"t{i}" for i in range(1, 13)]
    # kitobning o'z nazoratlari bo'lsa — qo'shilmaydi
    kitob = items[:3] + [{"topic_code": "k1", "nomi": "nazorat testi: 1-3"}, {"topic_code": "k2", "nomi": "oraliq nazorat: 1-6"}]
    assert not any(x.get("nazorat") for x in nazorat_qosh(kitob))


def test_nazorat_shu_kuni_ochiq():
    D2 = [("a", True), ("b", True), ("c", True), ("NZ:3", True), ("d", True)]
    r = tartib_qulf(D2, {"a", "b", "c"}, {"c"}, False)
    assert r[3] == (True, "navbat") and r[4][0] is False
    r = tartib_qulf(D2, {"a", "b", "c", "NZ:3"}, {"c", "NZ:3"}, False)
    assert r[4] == (False, "ertaga")
