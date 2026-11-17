import random, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import bilim_zanjiri as b


def test_butun_javobli_savolda_4_variant_va_togri_javob_bor():
    for sd in range(300):
        rr = random.Random(sd)
        for f in (b.ch_tarozi, b.ch_sakrash, b.ch_kuboid, b.ch_yaxlit, b.ch_nur):
            r = f(rr)
            assert len(r["variantlar"]) == 4 and len(set(r["variantlar"])) == 4
            assert 0 <= r["togri"] < 4


def test_tarozi_javobi_togri():
    for sd in range(200):
        r = b.ch_tarozi(random.Random(sd))
        c = r["chizma"]
        assert int(r["variantlar"][r["togri"]]) == c["s"] - c["a"] and c["a"] <= 6
