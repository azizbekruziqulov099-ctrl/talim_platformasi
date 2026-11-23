"""REV702: So'z sandig'i holati — tozalash, ikki qurilmani birlashtirish, hisob."""
from modules.soz_sandiq import tozala, birlashtir, hisob, MAX_SOZ


def test_tozala_notogri_yozuvlarni_tashlaydi():
    s = tozala({"apple": [2, 100], "Bad Key": [1, 1], "x": [9, 1], "y": [1], "z": "a", "w": [3, -1], "ok_2": ["4", "20500"]})
    assert s == {"apple": [2, 100], "ok_2": [4, 20500]}
    assert tozala(None) == {} and tozala([1, 2]) == {}
    assert len(tozala({f"k{i}": [1, 1] for i in range(MAX_SOZ + 50)})) == MAX_SOZ


def test_birlashtir_keyingi_oynalgani_qoladi():
    telefon = {"apple": [3, 110], "cat": [1, 100]}
    kompyuter = {"apple": [2, 104], "cat": [2, 102], "dog": [2, 103]}
    assert birlashtir(telefon, kompyuter) == {"apple": [3, 110], "cat": [2, 102], "dog": [2, 103]}
    assert birlashtir(kompyuter, telefon) == birlashtir(telefon, kompyuter)
    assert birlashtir({"a": [1, 5]}, {"a": [2, 5]}) == {"a": [2, 5]}


def test_hisob():
    assert hisob({"a": [1, 1], "b": [3, 9], "c": [5, 30], "d": [2, 3]}) == {"boshlangan": 4, "organilgan": 2}
