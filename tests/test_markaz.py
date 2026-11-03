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


def test_mashq_kitobdan():
    from modules.markaz_kitob import mashq_darsdan
    steps = [
        {"turi": "kirish", "sarlavha": "[en]Can I have a coffee, please?[/en]", "doska": "[en]Can I have a coffee, please?[/en]", "ovoz": ""},
        {"turi": "tushuncha", "sarlavha": "[en]Listen to the conversation[/en]", "ovoz": "",
         "doska": "[en]Waiter: Good afternoon! What would you like?[/en]\n[en]Madina: A tea, please.[/en]\n[en]Waiter: Here you are.[/en]"},
        {"turi": "tushuncha", "sarlavha": "☕ [en]coffee[/en] — qahva", "doska": "☕ [en]coffee[/en]\nqahva\n[en]A coffee, please.[/en]", "ovoz": ""},
        {"turi": "tushuncha", "sarlavha": "[en]Can I have …, please?[/en]", "doska": "[en]Can I have a coffee, please?[/en]\n[en]Here you are.[/en]", "ovoz": ""},
        {"turi": "tushuncha", "sarlavha": "[en]Your turn![/en]", "doska": "[en]Order a drink.[/en]\n[en]Can I have …, please?[/en]", "ovoz": "[en]Order a drink.[/en] Ichimlik buyuring."},
        {"turi": "tushuncha", "sarlavha": "🌟 [en]Today we learned[/en]", "doska": "☕ [en]coffee[/en]  🍵 [en]tea[/en]", "ovoz": ""},
    ]
    m = mashq_darsdan({"steps": steps, "topic": {"mavzu": "Kafeda"}})
    assert [d["kim"] for d in m["dialog"]] == ["Waiter", "Madina", "Waiter"] and m["rol_kim"] == "Waiter"
    assert m["diktant"] == [{"emoji": "☕", "soz": "coffee", "mano": "qahva", "gap": "A coffee, please."}]
    assert all(t["variantlar"][t["javob"]] == t["gap"] for t in m["tinglash"])
    assert "coffee" not in [g["gap"] for g in m["gapirish"]] and "Can I have a coffee, please?" in [g["gap"] for g in m["gapirish"]]
    assert m["rol"]["topshiriq"] == "Order a drink." and "Ichimlik" in m["rol"]["izoh"]


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


def test_excel_kontent():
    import io, openpyxl
    from modules.markaz_excel import sinov_shablon, sinov_oqish, strategiya_shablon, strategiya_oqish
    from modules.markaz_sinov_toliq import LISTENING, READING, baholash
    from modules.markaz_sertifikat import WRITING, SPEAKING
    from modules.markaz_strategiya import STRATEGIYALAR
    d, xato = sinov_oqish(sinov_shablon(LISTENING, READING, WRITING, SPEAKING))
    assert not xato and d["soni"] == {"listening": 35, "reading": 35}
    qs = lambda B: [q for b in B for q in [y for _, y in b.get("audio", [])] + b.get("savollar", [])]
    togri = {q["id"]: (q["javob"] if q["tur"] == "tanlash" else q["javob"][0]) for q in qs(d["listening"]) + qs(d["reading"])}
    assert baholash(togri, d["listening"], d["reading"])["reading"]["ball"] == 75
    # buzilgan qator — xato qator raqami bilan, hech narsa saqlanmaydi
    wb = openpyxl.load_workbook(io.BytesIO(sinov_shablon(LISTENING, READING, WRITING, SPEAKING)))
    wb["Sinov"]["O3"] = "Z"; bio = io.BytesIO(); wb.save(bio)
    _, xato2 = sinov_oqish(bio.getvalue())
    assert xato2 and xato2[0]["qator"] == 3
    s, xato3 = strategiya_oqish(strategiya_shablon(STRATEGIYALAR))
    assert not xato3 and len(s) == len(STRATEGIYALAR)
    assert sinov_oqish(b"bu excel emas")[1][0]["xabar"].startswith("Fayl")


def test_rus_daraja_va_aralash():
    from collections import Counter
    from modules.markaz_daraja import RU, EN, baholash, savollar
    assert len(RU) == 40 and len(savollar("ru")) == 40
    assert baholash("ru", {q["id"]: q["javob"] for q in RU})["daraja"] == "C1"
    for bank in (RU, EN):   # to'g'ri javob bitta harfda to'planmagan
        assert max(Counter(q["javob"] for q in bank).values()) <= 20


def test_rev298_test_yasash():
    from modules.test_yasash import yasash, lugat
    L = {"steps": [{"sarlavha": "🎪 [en]circus[/en] — sirk", "doska": "🎪 [en]circus[/en]\nsirk"},
                   {"sarlavha": "🏟️ [en]stadium[/en] — stadion", "doska": "🏟️ [en]stadium[/en]"},
                   {"sarlavha": "🎭 [en]theatre[/en] — teatr", "doska": "🎭 [en]theatre[/en]"},
                   {"sarlavha": "🟣 Rolli o'yin", "doska": "🟣 [en]the teacher[/en]"},
                   {"sarlavha": "Sanaymiz", "doska": "🍎🍎🍎"}]}
    assert len(lugat(L, "uz")) == 3   # 🍎🍎🍎 — sanoq qatori, so'z emas
    qs = yasash(L, "uz", 30, seed="x")
    assert len(qs) >= 12
    for q in qs:
        assert len(q["variantlar"]) == 3 and len(set(q["variantlar"])) == 3 and 0 <= q["togri"] < 3
        if q["savol"].startswith("Nechta"):
            assert "🍎" in q["savol"] and q["variantlar"][q["togri"]] == str(q["savol"].split("? ")[1].count("🍎"))
        if "circus" in q["savol"] and "nima degani" in q["savol"]:
            assert q["variantlar"][q["togri"]] == "sirk"
