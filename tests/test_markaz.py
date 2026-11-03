import datetime as dt
from modules.markaz import holat, darvoza, kerakli_kunlar, IMTIHONLAR

D = dt.date


def test_darvoza_chegara():
    assert darvoza(80)["ochildi"] and not darvoza(79.5)["ochildi"]
    assert "foydasiz" in darvoza(40, "Present Simple")["gap"]


def test_kunlar_jadvali_tanbeh_raqamlar_bilan():
    y = {"boshlangan": "2026-10-05", "jadval": {"turi": "kunlar", "kunlar": [0, 3]}, "sozlar_soni": 300, "imtihon_sana": "2026-12-12"}
    f = [{"kun": "2026-10-05"}, {"kun": "2026-10-08"}]           # faqat birinchi hafta
    h = holat(y, f, D(2026, 11, 2))
    assert h["daraja"] == "tanbeh" and h["ketma_ket"] >= 3 and h["yoqolayotgan_soz"] > 0 and h["imtihongacha"] == 40
    assert "so'z esdan chiqmoqda" in h["gap"]


def test_jadval_boyicha_yaxshi():
    y = {"boshlangan": "2026-10-26", "jadval": {"turi": "kunlar", "kunlar": [0, 3]}, "sozlar_soni": 50}
    f = [{"kun": "2026-10-26"}, {"kun": "2026-10-29"}]
    assert holat(y, f, D(2026, 11, 2))["daraja"] == "yaxshi"


def test_haftada_ikki_va_erkin():
    assert len(kerakli_kunlar({"turi": "haftada", "soni": 2}, D(2026, 10, 1), D(2026, 10, 22))) == 6
    y = {"boshlangan": "2026-10-01", "jadval": {"turi": "erkin"}, "sozlar_soni": 0}
    assert holat(y, [{"kun": "2026-10-30"}], D(2026, 11, 2))["daraja"] == "yaxshi"
    assert holat(y, [{"kun": "2026-10-10"}], D(2026, 11, 2))["daraja"] == "tanbeh"


def test_katalog():
    assert IMTIHONLAR["toefl"]["shkala"].startswith("1–6") and "en" in IMTIHONLAR["milliy_cefr"]["tillar"]


def test_daraja_testi():
    from modules.markaz_daraja import EN, baholash, savollar
    assert len(EN) == 40 and all("javob" not in q for q in savollar("en"))
    assert len({q["id"] for q in EN}) == 40 and all(0 <= q["javob"] < len(q["variantlar"]) for q in EN)
    togri = {q["id"]: q["javob"] for q in EN if q["daraja"] in ("A1", "A2", "B1")}
    n = baholash("en", togri)
    assert n["daraja"] == "B1" and n["keyingi"] == "B2"
    assert baholash("en", {})["daraja"] == "A0"
    hammasi = {q["id"]: q["javob"] for q in EN}
    assert baholash("en", hammasi)["daraja"] == "C1"


def test_mashqlar():
    from modules.markaz_mashq import mashqlar
    m = mashqlar("en", "A1", 3, "uz")
    assert m["nom"] == "Kafeda" and len(m["tinglash"]) == 5 and len(m["diktant"]) == 6
    for t in m["tinglash"]:
        assert len(t["variantlar"]) == 3 and 0 <= t["javob"] < 3
    assert mashqlar("en", "A1", 99) is None and mashqlar("ko", "A1", 1) is None
    assert mashqlar("en", "A1", 1, "ru")["nom"] == "Знакомство"


def test_sinov_mini():
    from modules.markaz_sertifikat import sinov_ochiq, obyektiv_ball, LISTENING, READING, chegaralar
    o = sinov_ochiq()
    assert all("javob" not in s for b in o["listening"] + o["reading"] for s in b["savollar"])
    hammasi = {s["id"]: s["javob"] for b in LISTENING + READING for s in b["savollar"]}
    n = obyektiv_ball(hammasi)
    assert n["listening"]["ball"] == 75 and n["reading"]["daraja"] == "C1"
    assert obyektiv_ball({})["listening"]["ball"] == 0
    assert chegaralar(50) == "B1" and chegaralar(51) == "B2" and chegaralar(37) == "B1 dan past"
    ids = [s["id"] for b in LISTENING + READING for s in b["savollar"]]
    assert len(ids) == len(set(ids)) == 20


def test_sinov_toliq():
    import json
    from modules.markaz_sinov_toliq import LISTENING, READING, ochiq, baholash
    qs = lambda B: [q for b in B for q in [x for _, x in b.get("audio", [])] + b.get("savollar", [])]
    assert len(qs(LISTENING)) == 35 and len(qs(READING)) == 35
    assert '"javob"' not in json.dumps(ochiq())
    hammasi = {q["id"]: (q["javob"] if q["tur"] == "tanlash" else q["javob"][0]) for q in qs(LISTENING) + qs(READING)}
    r = baholash(hammasi)
    assert r["listening"]["ball"] == 75 and r["reading"]["togri"] == 35
    assert baholash({"L09": " Ten ", "L11": "40"})["listening"]["togri"] == 2   # yozma javob: katta-kichik harf, bo'shliq farqi yo'q
    head = [q for q in qs(READING) if q["id"] in ("R07", "R08")]
    assert [q["javob"] for q in head] != [0, 1]   # sarlavhalar aralash tartibda


def test_strategiya():
    from modules.markaz_strategiya import royxat, STRATEGIYALAR
    for t in ("uz", "ru", "en"):
        r = royxat(t)
        assert len(r) == len(STRATEGIYALAR) >= 8 and all(x["nom"] and x["qadamlar"] and 0 <= x["mashq"]["javob"] < len(x["mashq"]["variantlar"]) for x in r)
    assert {x["bolim"] for x in royxat()} == {"listening", "reading", "writing", "speaking"}
