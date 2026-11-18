import random
import sys
sys.dont_write_bytecode = True
from modules import mat_kirish as k


def test_tuzilma():
    t = k.tuz(0, random.Random(5))
    assert len(t) == 30 and len({s for s, _ in t}) == 30
    assert [l for _, l in t] == [1] * 10 + [2] * 10 + [3] * 10 and k.MAKS == 63.0


def test_daraja_soni():
    d = k.darajalar()
    for lv in (1, 2, 3):
        assert sum(1 for x in d.values() if x == lv) >= 300
