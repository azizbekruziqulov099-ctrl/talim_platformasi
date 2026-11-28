"""Kapul hamyoni: 50 sovg'a, yechish, yetmasa 402, qaytarish (bir marta), takror qo'shilmaydi (bazasiz, soxta kursor)."""
import pytest
from fastapi import HTTPException

from modules.taqdimot_dvigatel import kapul


class Kursor:
    def __init__(self):
        self.h = {}
        self.j = []
        self._r = None

    def execute(self, q, a=()):
        q = " ".join(q.split())
        self._r = None
        if q.startswith("SELECT balans FROM kapul_hamyon"):
            self._r = {"balans": self.h[a[0]]} if a[0] in self.h else None
        elif q.startswith("INSERT INTO kapul_hamyon"):
            if a[0] not in self.h:
                self.h[a[0]] = a[1]
                self._r = {"balans": a[1]}
        elif q.startswith("UPDATE kapul_hamyon SET balans = balans - "):
            n, uid, m = a
            if self.h.get(uid, -1) >= m:
                self.h[uid] -= n
                self._r = {"balans": self.h[uid]}
        elif q.startswith("UPDATE kapul_hamyon SET balans = balans + "):
            n, uid = a
            if uid in self.h:
                self.h[uid] += n
                self._r = {"balans": self.h[uid]}
        elif q.startswith("INSERT INTO kapul_jurnal"):
            self.j.append(a)
        elif q.startswith("SELECT 1 FROM kapul_jurnal"):
            uid, ref, sabab = a
            self._r = {"x": 1} if any(x[0] == uid and x[3] == ref and x[2] == sabab for x in self.j) else None
        else:
            raise AssertionError(q)

    def fetchone(self):
        return self._r


def test_sovga_50_va_bir_marta():
    c = Kursor()
    assert kapul.hamyon(c, 7) == 10
    assert kapul.hamyon(c, 7) == 10
    assert len(c.j) == 1 and c.j[0][1] == 10


def test_yechish_va_yetmasa_402():
    c = Kursor()
    assert kapul.yech(c, 1, 3, "ppt", "a") == 7
    with pytest.raises(HTTPException) as e:
        kapul.yech(c, 1, 8, "ochiq_dars", "b")
    assert e.value.status_code == 402 and c.h[1] == 7


def test_qaytarish_bir_marta_va_yechilmaganga_yoq():
    c = Kursor()
    kapul.yech(c, 1, 1, "ochiq_dars", "x")
    kapul.qaytar(c, 1, 1, "ochiq_dars", "x")
    kapul.qaytar(c, 1, 1, "ochiq_dars", "x")
    assert c.h[1] == 10
    kapul.qaytar(c, 1, 1, "ppt", "yoq")
    assert c.h[1] == 10


def test_qosh_takrorlanmaydi():
    c = Kursor()
    assert kapul.qosh(c, 2, 51, "tolov", "t1") == 61
    assert kapul.qosh(c, 2, 51, "tolov", "t1") == 61


def test_narx():
    assert kapul.SOM == 1000 and kapul.NARX == {"ppt_10_slayd": 1, "ochiq_dars": 1}
    assert [kapul.ppt_narx(n) for n in (5, 10, 11, 20, 40)] == [1, 1, 2, 2, 4]
