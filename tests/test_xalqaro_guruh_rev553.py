"""REV553: xalqaro sinfda reyting bo'yicha guruhlash — sof qoidalar."""
import random

from modules.xalqaro_guruh import guruh_hajmlari, guruh_ozgarishlari, guruhlarga_bol


def test_hajmlar_asosiy_holatlar():
    assert guruh_hajmlari(0) == []
    assert guruh_hajmlari(7) == [7]                 # jami kam — bitta guruh
    assert guruh_hajmlari(29) == [29]
    assert guruh_hajmlari(30) == [30]
    assert guruh_hajmlari(60) == [30, 30]
    assert guruh_hajmlari(50) == [30, 20]           # qoldiq 20 — o'zi guruh
    assert guruh_hajmlari(59) == [30, 29]
    assert guruh_hajmlari(35) == [35]               # qoldiq 5 — oldingisiga qo'shiladi
    assert guruh_hajmlari(68) == [30, 38]           # qoldiq 8 → oxirgi guruh 38 («30 atrofida»)
    assert guruh_hajmlari(45) == [23, 22]           # qoldiq 15 → ikki guruh teng
    assert guruh_hajmlari(75) == [30, 23, 22]
    assert guruh_hajmlari(49) == [25, 24]
    assert guruh_hajmlari(40) == [20, 20]
    assert guruh_hajmlari(39) == [39]


def test_har_guruh_20_dan_kam_emas_va_hech_kim_yoqolmaydi():
    for n in range(1, 1201):
        h = guruh_hajmlari(n)
        assert sum(h) == n, n
        if n >= 20:
            assert all(20 <= x <= 39 for x in h), (n, h)
        else:
            assert h == [n]
        assert h == sorted(h, reverse=True) or h[-1] >= 20, (n, h)   # faqat oxirgi guruhlar boshqacha hajmda


def test_reyting_boyicha_tartib_va_kutayotganlar():
    rnd = random.Random(7)
    oq = [{"user_id": i, "reyting": rnd.choice([None] * 1 + [rnd.randint(300, 700)] * 9)} for i in range(1, 131)]
    b = guruhlarga_bol(oq)
    reytinglilar = [o for o in oq if o["reyting"] is not None]
    assert sorted(b["kutayotgan"]) == sorted(o["user_id"] for o in oq if o["reyting"] is None)
    azolar = [u for g in b["guruhlar"] for u in g["azolar"]]
    assert sorted(azolar) == sorted(o["user_id"] for o in reytinglilar) and len(set(azolar)) == len(azolar)
    assert [g["raqam"] for g in b["guruhlar"]] == list(range(1, len(b["guruhlar"]) + 1))
    for a, c in zip(b["guruhlar"], b["guruhlar"][1:]):
        assert a["eng_past"] >= c["eng_yuqori"]      # 1-guruh — eng kuchlilar; guruhlar reyting bo'yicha ustma-ust tushmaydi
    assert all(len(g["azolar"]) >= 20 for g in b["guruhlar"])


def test_teng_reytingda_natija_barqaror():
    oq = [{"user_id": i, "reyting": 500, "qoshildi": f"2026-11-{(i % 9) + 1:02d}"} for i in range(1, 46)]
    a, b = guruhlarga_bol(oq), guruhlarga_bol(list(reversed(oq)))
    assert a == b and [len(g["azolar"]) for g in a["guruhlar"]] == [23, 22]
    assert a["guruhlar"][0]["azolar"][0] == 9        # avval qo'shilgan (01-kun), teng bo'lsa kichik user_id


def test_guruhlar_kichrayganda_birlashadi_va_oquvchi_xabar_oladi():
    # 11 ta guruh edi (330 o'quvchi); 10- va 11-guruhdan ko'pchilik ketdi: 12 + 14 qoldi → ular bitta guruhga birlashadi
    oq = [{"user_id": i, "reyting": 1000 - i} for i in range(1, 331)]
    eski_b = guruhlarga_bol(oq)
    assert len(eski_b["guruhlar"]) == 11
    eski = {u: g["raqam"] for g in eski_b["guruhlar"] for u in g["azolar"]}
    qolgan = [o for o in oq if o["user_id"] <= 270 or 271 <= o["user_id"] <= 282 or 301 <= o["user_id"] <= 314]
    yangi_b = guruhlarga_bol(qolgan)
    assert [len(g["azolar"]) for g in yangi_b["guruhlar"]] == [30] * 9 + [26]      # 12 + 14 = 26 — bitta guruh
    oz = guruh_ozgarishlari(eski, yangi_b)
    assert {x["user_id"] for x in oz} == set(range(301, 315))                        # faqat 11-guruhdan kelganlar xabar oladi
    assert all(x["eski"] == 11 and x["yangi"] == 10 and x["tur"] == "yuqoriga" for x in oz)


def test_yangi_oquvchi_va_pastga_tushish():
    eski = {1: 1, 2: 2}
    b = {"guruhlar": [{"raqam": 1, "azolar": [2, 3]}, {"raqam": 2, "azolar": [1]}]}
    oz = {x["user_id"]: x for x in guruh_ozgarishlari(eski, b)}
    assert oz[3]["tur"] == "yangi" and oz[3]["eski"] is None
    assert oz[2]["tur"] == "yuqoriga" and oz[1]["tur"] == "pastga"
