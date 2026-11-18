import random
import sys
sys.dont_write_bytecode = True
from modules import mat_kirish as k


def test_tuzilma():
    for dr in (2, 3):
        t = k.tuz(dr, random.Random(5))
        assert len(t) == 40 and len({s for s, _ in t}) == 40
        assert [l for _, l in t] == [1] * 10 + [dr] * 30
    assert k.maks(2) == 74.0 and k.maks(3) == 104.0


def test_daraja_soni():
    d = k.darajalar()
    for lv in (1, 2, 3):
        assert sum(1 for x in d.values() if x == lv) >= 300
