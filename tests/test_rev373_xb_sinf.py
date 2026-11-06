from modules import xalqaro_baholash as xb

def test_kod_va_parol():
    k = xb.sinf_kodi_yasa(); assert len(k) == 6 and all(c in xb._KOD_HARF for c in k)
    assert xb.kod_norm(" ab-3c d9 ") == "AB3CD9"
    h = xb.parol_hash("7a sinf", "ABC234")
    assert xb.parol_togri(h, "7a sinf", "ABC234") and not xb.parol_togri(h, "7b", "ABC234")
    assert not xb.parol_togri(h, "7a sinf", "ZZZ999")   # boshqa sinf kodi bilan ishlamaydi
    assert xb.parol_togri("", "", "ABC234")              # parolsiz sinf

def test_malumot_tekshir():
    assert xb.sinf_malumot_tekshir("7-«A»", 7, "")[0] == {"nom": "7-«A»", "sinf": 7}
    assert xb.sinf_malumot_tekshir("x", 0, "")[1] == "sinf_raqam"
    assert xb.sinf_malumot_tekshir("x", 12, "")[1] == "sinf_raqam"
    assert xb.sinf_malumot_tekshir("  ", 5, "")[1] == "sinf_nom"
    assert xb.sinf_malumot_tekshir("5A", 5, "ab")[1] == "sinf_parol"
    for m in ("sinf_raqam", "sinf_nom", "sinf_parol", "sinf_yoq", "sinf_parol_xato", "sinf_egasi_emas"):
        assert xb.matn(m, "ru") and xb.matn(m, "en")
