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

def test_rev374_sinf_fani():
    assert xb.sinf_toplami("T11_G4_S", 4) == "T11_G4_S"
    assert xb.sinf_toplami("", 3) == "T11_G4_M" and xb.sinf_toplami("", 7) == "T11_G8_M" and xb.sinf_toplami("", 10) == "P_M"
    assert xb.sinf_toplami("XYZ", 9) == "P_M"
    assert set(xb.XB_TOPLAMLAR) >= set(xb.tavsiya_toplamlar(0)) | set(xb.tavsiya_toplamlar(10))

def test_rev401_auditoriya():
    assert xb.auditoriya_norm("talaba") == "talaba" and xb.auditoriya_norm("x") == "maktab"
