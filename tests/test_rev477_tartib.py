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
