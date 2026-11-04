"""REV329: o'yin natijalaridan qobiliyatlar foizi."""
from modules.bola_qobiliyat import hisobla, OYIN_QOBILIYAT, QOB_KALIT


def test_ulushlar_toliq():
    for oid, q in OYIN_QOBILIYAT.items():
        assert abs(sum(q.values()) - 1) < 1e-9, oid
        assert set(q) <= set(QOB_KALIT)


def test_hisobla():
    n = [{"oyin_id": 89, "togri": 4, "xato": 0, "soniya": 60}] * 3 + [{"oyin_id": 31, "togri": 2, "xato": 2, "soniya": 60}] * 3
    x = hisobla(n)
    q = x["qobiliyatlar"]
    assert q["xotira"]["foiz"] == 100 and q["sanash"]["foiz"] == 50
    assert q["nutq"]["foiz"] is None            # ma'lumot yo'q — xulosa qilinmaydi
    assert x["kuchli"] == "xotira" and x["zaif"] in ("sanash", "tezlik")
    assert hisobla([{"oyin_id": 999, "togri": 3}])["jami_oyin"] == 1
