"""REV693: til o'zlashtirish foizi — mustahkam so'z qoidasi, bosqich va fanlar foizi."""
from datetime import date
from modules.til_foiz import ozlashtirish

KURS = {"en": {"nom": "Ingliz tili", "turi": "til", "emoji": "🇬🇧"}, "mt": {"nom": "Matematika", "turi": "fan", "emoji": "🔢"}}
kurs_of = lambda fan: (("en", KURS["en"]) if "ngliz" in fan else ("mt", KURS["mt"]) if "atem" in fan else ("", {}))
D = lambda n: date(2026, 11, n)


def q(fan, kun, sozlar=(), togri=None, jami=None, tugadi=True):
    return {"fan": fan, "sana": D(kun), "sozlar": [{"soz": s, "aytdi": a} for s, a in sozlar], "togri": togri, "jami": jami, "tugadi": tugadi}


def test_mustahkam_3_marta_va_2_xil_kun():
    rows = [q("Ingliz tili", 1, [("cat", True), ("dog", None)]), q("Ingliz tili", 1, [("cat", None)]), q("Ingliz tili", 2, [("cat", None), ("dog", None)]),
            q("Ingliz tili", 1, [("sun", None)]), q("Ingliz tili", 1, [("sun", None)]), q("Ingliz tili", 1, [("sun", None)])]
    t = ozlashtirish(rows, kurs_of)["tillar"][0]
    assert t["sozlar"] == 3 and t["mustahkam"] == 1 and t["foiz"] == 33      # cat: 3 marta, 2 kun; sun: 3 marta, 1 kun — yo'q
    assert t["aytdi"] == 1 and t["bosqich"] == 1 and t["darslar"] == 6


def test_bosqichlar():
    sozlar = [(f"w{i}", True) for i in range(6)] + [(f"x{i}", None) for i in range(4)]
    assert ozlashtirish([q("Ingliz tili", 1, sozlar)], kurs_of)["tillar"][0]["bosqich"] == 2
    gap = [(f"i like w{i}", True) for i in range(5)]
    assert ozlashtirish([q("Ingliz tili", 1, gap)], kurs_of)["tillar"][0]["bosqich"] == 3


def test_fanlar_foizi_va_notanish_fan():
    r = ozlashtirish([q("Matematika", 1, togri=3, jami=4), q("Matematika", 2, togri=4, jami=4, tugadi=False), q("Noma'lum", 1, [("a", True)])], kurs_of)
    assert r["tillar"] == [] and len(r["fanlar"]) == 1
    f = r["fanlar"][0]
    assert f["foiz"] == 88 and f["darslar"] == 1 and f["kunlar"] == 2
