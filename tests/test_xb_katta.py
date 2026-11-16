"""Katta sinf (havola → yosh bo'yicha yo'nalish → kirish testlari → guruhlash) qoidalari."""
import json
import os

import pytest

from modules import xalqaro_baholash as xb
from modules import xb_yosh as xy


# ── yosh bo'yicha yo'nalish: chegaralar ──
@pytest.mark.parametrize("yosh,kutilgan", [
    (6, []), (7, list(xy.TIMSS4)), (11, list(xy.TIMSS4)), (12, list(xy.TIMSS8)), (14, list(xy.TIMSS8)),
    (15, list(xy.PISA)), (16, list(xy.PISA)), (30, list(xy.PISA)),
])
def test_yosh_chegaralari(yosh, kutilgan):
    assert list(xy.yonalishlar(yosh)) == kutilgan


def test_hech_qachon_noto_g_ri_dastur():
    for yosh in range(7, 12):
        assert not set(xy.yonalishlar(yosh)) & set(xy.PISA)          # kichik bolaga PISA yo'q
    for yosh in range(12, 40):
        assert not set(xy.yonalishlar(yosh)) & set(xy.TIMSS4)        # 4-sinfdan o'tgan/katta bolaga 4-sinf TIMSS yo'q
    for yosh in range(7, 15):
        assert not set(xy.yonalishlar(yosh)) & set(xy.PISA)
    # o'quvchi o'zi tanlasa ham yoshiga mos bo'lmagani qo'shilmaydi
    assert not set(xy.ruxsat_etilgan(9, ["P_M", "T11_G4_M"])) & set(xy.PISA)
    assert "T11_G4_M" not in xy.ruxsat_etilgan(16, ["T11_G4_M", "P_M"])


def test_tartib_matematika_birinchi():
    # ketma-ket testlar: matematika → tabiiy fan → o'qish → moliya
    assert list(xy.PISA) == ["P_M", "P_S", "P_R", "P_F"]
    assert xy.TIMSS4[0].endswith("_M") and xy.TIMSS8[0].endswith("_M")


# ── kirish testi ──
def test_kirish_testi_15_savol_hamma_yonalishda():
    for band in ("4", "8", "P"):
        assert xb.IMTIHON_TURLARI["kirish"][band][0] == 15
        assert xb.IMTIHON_TURLARI["kirish"][band][1] >= 20


def test_kirish_tartibi_birlik_bolinmaydi():
    sv = [{"id": "a", "xalqaro_ortacha": 90, "birlik": "U1"}, {"id": "b", "xalqaro_ortacha": 20},
          {"id": "c", "xalqaro_ortacha": 85, "birlik": "U1"}, {"id": "d", "xalqaro_ortacha": 50}]
    t = [s["id"] for s in xb.kirish_tartibi(sv)]
    assert t.index("a") + 1 == t.index("c") or t.index("c") + 1 == t.index("a")   # bitta stimul savollari yonma-yon
    assert t[0] in ("a", "c") and t[-1] == "b"                                     # xalqaro foizi yuqori = oson birinchi, 20% = eng qiyin oxirida


# ── guruhlash qoidasi ──
def test_guruh_oqituvchi_bosmaguncha_tuzilmaydi():
    from datetime import datetime
    assert xb.guruhlash_kerak(False, None, True, {1, 2}, set()) is False   # birinchi marta, o'qituvchi bosmagan
    assert xb.guruhlash_kerak(True, None, False, {1, 2}, set()) is True    # o'qituvchi bosdi
    t = datetime(2026, 11, 1)
    assert xb.guruhlash_kerak(False, t, False, {1}, {1}) is False          # hech narsa o'zgarmagan
    assert xb.guruhlash_kerak(False, t, True, {1}, {1}) is True            # hafta o'tdi
    assert xb.guruhlash_kerak(False, t, False, {1, 2}, {1}) is True        # yangi reytingli o'quvchi
    assert xb.guruhlash_kerak(False, t, False, {1}, {1, 2}) is True        # guruhdagi kimdir ketdi


# ── savol turlari ──
def test_savol_turlari_tekshiruvi():
    assert xb.tekshir({"turi": "tanlov", "togri": 2}, "C") and not xb.tekshir({"turi": "tanlov", "togri": 2}, "B")
    k = {"turi": "kop", "togri": [1, 3]}
    assert xb.tekshir(k, "B,D") and xb.tekshir(k, "db")
    assert not xb.tekshir(k, "B") and not xb.tekshir(k, "BCD") and not xb.tekshir(k, "")
    assert not xb.tekshir({"turi": "kop", "togri": []}, "A")


def test_bazadagi_savollar_yaroqli():
    """Fixture bazasi: har savolda kamida bitta variant, tanlovda to'g'ri indeks variantlar ichida, kopda 2–4 ta to'g'ri."""
    yol = os.path.join(os.path.dirname(__file__), "fixtures", "xalqaro_data", "savollar.json")
    sv = json.load(open(yol, encoding="utf8"))
    assert len(sv) > 100
    ids = [s["id"] for s in sv]
    assert len(ids) == len(set(ids))
    for s in sv:
        assert s["variantlar"], s["id"]
        for v in s["variantlar"]:
            assert v["turi"] in ("tanlov", "ochiq", "kop"), (s["id"], v["turi"])
            if v["turi"] == "tanlov":
                assert 0 <= v["togri"] < len(v["javoblar"]) <= 4, s["id"]
            if v["turi"] == "kop":
                assert 2 <= len(v["togri"]) <= 4 and all(0 <= i < len(v["javoblar"]) for i in v["togri"]), s["id"]
            if v["turi"] == "ochiq":
                assert str(v.get("javob", "")).strip(), s["id"]
