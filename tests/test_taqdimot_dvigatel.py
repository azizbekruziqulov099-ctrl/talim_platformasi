"""Taqdimot dvigateli: miya → sahna → PPTX, Excel, chizmalar, formulalar, API (bazasiz)."""
import io
import json
import os
import zipfile

import pytest

from modules.taqdimot_dvigatel import api, chizma, excel, formula, sxema, uslub, yasash
from modules.taqdimot_dvigatel.sahna import Slayd

NAMUNA = json.load(open(os.path.join(os.path.dirname(yasash.__file__), "namuna_ratsional.json"), encoding="utf-8"))


def test_namuna_yasaladi_va_sigadi():
    sah = yasash.yasa(NAMUNA, seed=5, uslub_kod="anor.anor.0")
    bloklar = [s["blok"] for s in sah["slaydlar"]]
    assert bloklar[0] == "titul" and "reja" in bloklar and "test" in bloklar
    for s in sah["slaydlar"]:
        for el in s["els"]:
            if el["k"] == "text":
                assert el["fit"], el["pp"][0]["rs"][0]["t"]


@pytest.mark.parametrize("kod", uslub.barcha_uslublar()[::7])
def test_har_xil_uslub_pptx(kod):
    sah = yasash.yasa(NAMUNA, seed=9, uslub_kod=kod + ".1")
    data = yasash.pptx(sah)
    z = zipfile.ZipFile(io.BytesIO(data))
    slides = [n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
    assert len(slides) == len(sah["slaydlar"])
    xml = z.read("ppt/slides/slide3.xml").decode()
    assert "<p:timing>" in xml or "<p:timing " in xml
    assert "hlinksldjump" in z.read("ppt/slides/slide4.xml").decode()


def test_urug_har_xil_natija():
    a = yasash.yasa(NAMUNA, seed=1)
    b = yasash.yasa(NAMUNA, seed=2)
    c = yasash.yasa(NAMUNA, seed=1)
    assert a["uslub"] == c["uslub"]
    assert len(uslub.barcha_uslublar()) * 3 * len(uslub.ANIMATSIYALAR) >= 100
    assert (a["uslub"]["kod"], a["uslub"]["anim"]) != (b["uslub"]["kod"], b["uslub"]["anim"]) or a["slaydlar"] != b["slaydlar"]


def test_buzuq_miya_buzmaydi():
    m = sxema.normallashtir({"meta": {"mavzu": "Kasrlar"}, "bolimlar": [{"nom": "A", "elementlar": ["oddiy matn", {"tur": "noma'lum", "matn": "x"},
                                                                                                    {"tur": "jadval", "ustunlar": [], "qatorlar": []},
                                                                                                    {"tur": "chizma", "chizma": {"tur": "son_oqi", "dan": "abc"}}]}],
                                 "test": [{"savol": "?", "variantlar": ["1", "2"], "javob": "B"}]})
    assert m["test"][0]["javob"] == 1
    sah = yasash.yasa(m, seed=3)
    assert len(sah["slaydlar"]) >= 2
    yasash.pptx(sah)


def test_hamma_chizmalar():
    u = uslub.Uslub("tun.olov.0")
    for k, (fn, _nom, sp) in chizma.CHIZMALAR.items():
        s = Slayd()
        A = chizma._A(u, 1)
        fn(s, sp, 0, 0, 400, 300, u, A)
        assert s.els, k


def test_formula():
    w, a, d = formula.olcha(r"\frac{a}{b}+\sqrt{x^2}=\mathbb{Q}", 30)
    assert w > 60 and a > 20
    s = Slayd()
    formula.chiz(s, r"C_n^k=\frac{n!}{k!(n-k)!}", 0, 0, 400, 100, a={"s": 1, "e": "zoom"})
    assert all(el.get("a", {}).get("s") == 1 for el in s.els)
    rs = formula.yugurik("son $\\frac{1}{2}$ va $x^2$")
    assert any(r.get("bl") == "sup" for r in rs)


def test_excel_aylanma():
    data = excel.shablon(NAMUNA)
    m2 = excel.oqi(data)[0]
    n1 = sxema.normallashtir(NAMUNA)
    assert m2["test"] == n1["test"] and m2["meta"] == n1["meta"]
    assert sum(len(b["slaydlar"]) for b in m2["bolimlar"]) == sum(len(b["slaydlar"]) for b in n1["bolimlar"])
    assert excel.oqi(excel.shablon(None))[0]["meta"]["mavzu"]


def test_api_bazasiz(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    class P:
        pass
    app = FastAPI()
    D = api.register_taqdimot_dvigatel(app, P())
    monkeypatch.setattr(D, "actor", lambda auth: 7)
    c = TestClient(app)
    r = c.post(api.PREFIX + "/yasash", json={"miya": NAMUNA, "seed": 4, "uslub": "daftar.dengiz.1"})
    assert r.status_code == 200 and r.json()["uslub"]["kod"] == "daftar.dengiz.1"
    r = c.post(api.PREFIX + "/pptx", json={"miya": NAMUNA, "seed": 4})
    assert r.status_code == 200 and r.content[:2] == b"PK"
    r = c.get(api.PREFIX + "/fon/anor.anor.0.jpg")
    assert r.status_code == 200 and r.content[:2] == b"\xff\xd8"
    r = c.get(api.PREFIX + "/fon/../x.jpg")
    assert r.status_code == 404
    r = c.post(api.PREFIX + "/import", content=excel.shablon(NAMUNA), headers={"x-fayl-nomi": "a.xlsx"})
    assert r.status_code == 200 and r.json()["miyalar"][0]["meta"]["mavzu"]
    r = c.post(api.PREFIX + "/yasash", json={"miya": NAMUNA, "uslub": "../../etc"})
    assert r.status_code == 422


def test_kutubxona_hammasi_yasaladi():
    from modules.taqdimot_dvigatel import kutubxona
    for t in kutubxona.toplamlar():
        r = kutubxona.mavzular(t["kod"])
        assert r["mavzular"]
        for m in r["mavzular"]:
            s = yasash.yasa(kutubxona.miya(t["kod"], m["kod"]), seed=11)
            assert len(s["slaydlar"]) >= 8, m["kod"]
            for sl in s["slaydlar"]:
                for el in sl["els"]:
                    if el["k"] == "text":
                        assert el["sc"] >= 0.5, (m["kod"], sl["blok"])


def test_formula_tex_qisqa_yozuv():
    assert formula.parse(r"\frac13 Bh")[1][0] == ("frac", ("ch", "1", False), ("ch", "3", False))
    w, a, d = formula.olcha(r"|a|=\begin{cases}a,&a\ge0,\\-a,&a<0.\end{cases}", 30)
    assert a > 30 and d > 15 and a + d > 55


def test_api_kutubxona(monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    class P:
        pass
    app = FastAPI()
    D = api.register_taqdimot_dvigatel(app, P())
    monkeypatch.setattr(D, "actor", lambda auth: 7)
    monkeypatch.setattr(D, "admin", lambda uid: False)
    c = TestClient(app)
    r = c.get(api.PREFIX + "/kutubxona")
    t = r.json()["toplamlar"][0]
    m = t["mavzular"][0]
    assert r.status_code == 200 and "fayl" not in m
    r = c.get(f"{api.PREFIX}/kutubxona/{t['kod']}/{m['kod']}")
    assert r.status_code == 200 and r.json()["bolimlar"]
    r = c.get(f"{api.PREFIX}/kutubxona/{t['kod']}/{m['kod']}/oqituvchi")
    assert r.status_code == 200 and len(r.content) > 100
    assert c.get(f"{api.PREFIX}/kutubxona/{t['kod']}/{m['kod']}/javoblar").status_code == 403
    assert c.get(f"{api.PREFIX}/kutubxona/{t['kod']}/yoq").status_code == 404
    assert c.get(f"{api.PREFIX}/kutubxona/..%2F..%2Fetc/{m['kod']}").status_code == 404


def test_kutubxona_chizmalar_joylanadi():
    from modules.taqdimot_dvigatel import kutubxona, rasmlar
    for t in kutubxona.toplamlar():
        for m in kutubxona.reestr(t["kod"])["mavzular"]:
            for ch in m.get("chizmalar") or []:
                for k in ch["kalitlar"]:
                    assert rasmlar.bor(k), k
            if not m.get("chizmalar"):
                continue
            d = kutubxona.miya(t["kod"], m["kod"])
            joy = {e["rasm"] for b in d["bolimlar"] for sl in b["slaydlar"] for e in sl["elementlar"] if e.get("tur") == "rasm"}
            for ch in m["chizmalar"]:
                assert set(ch["kalitlar"]) <= joy, (m["kod"], ch["id"])
            toza = kutubxona.miya(t["kod"], m["kod"], chizmali=False)
            assert not any(e.get("tur") == "rasm" for b in toza["bolimlar"] for sl in b["slaydlar"] for e in sl["elementlar"])


def test_rasm_tanla_kutubxona():
    from modules.taqdimot_dvigatel import rasm_tanla, rasmlar
    if not rasmlar.papka_reestri():
        return
    m = sxema.normallashtir({
        "meta": {"mavzu": "Amir Temur davri", "fan": "Tarix"},
        "rasmlar": [{"kalit": "uchar_ajdar_xyz", "tavsif": "Uchar ajdar", "prompt": "dragon"}],
        "bolimlar": [{"nom": "A", "slaydlar": [
            {"sarlavha": "Me’moriy obidalar", "elementlar": [{"tur": "matn", "matn": "Go‘ri Amir maqbarasi va Registon maydoni Samarqandda."}]},
            {"sarlavha": "Ertak", "elementlar": [{"tur": "matn", "matn": "Ertak"}, {"tur": "rasm", "rasm": "uchar_ajdar_xyz"}]},
            {"sarlavha": "Faqat rasm", "elementlar": [{"tur": "rasm", "rasm": "uchar_ajdar_xyz"}]}]}]})
    h = rasm_tanla.boyit(m)
    assert h["yoq"] and h["yoq"][0]["kalit"] == "uchar_ajdar_xyz" and h["yoq"][0]["prompt"] == "dragon"
    hammasi = [e for b in m["bolimlar"] for sl in b["slaydlar"] for e in sl["elementlar"]]
    assert all(not e.get("rasm") or rasmlar.bor(e["rasm"]) for e in hammasi)  # bo'sh ramka qolmaydi
    assert len(m["bolimlar"][0]["slaydlar"]) == 2  # faqat yo'q rasmdan iborat slayd olib tashlandi
    assert h["qoshildi"]
    s = yasash.yasa(m, seed=3)
    assert not any("rasm:" in (el.get("pp") and "".join(r["t"] for p in el["pp"] for r in p["rs"]) or "")
                   for sl in s["slaydlar"] for el in sl["els"] if el["k"] == "text")


def test_barcha_fan_turlari():
    from tests.taqdimot_fan_namuna import TEST
    from modules.taqdimot_dvigatel import sxema as SX
    m = sxema.normallashtir(TEST)
    turlar = {e["tur"] for b in m["bolimlar"] for sl in b["slaydlar"] for e in sl["elementlar"]}
    assert SX.YANGI_KENG | {"parcha"} <= turlar
    for kod in ("anor.anor.0", "tun.okean.0", "daftar.dengiz.1"):
        s = yasash.yasa(TEST, seed=5, uslub_kod=kod)
        for sl in s["slaydlar"]:
            for el in sl["els"]:
                if el["k"] == "text":
                    assert el["sc"] >= 0.45, (kod, sl["blok"])
        assert yasash.pptx(s)[:2] == b"PK"


def test_ai_reja_va_bolimma_bolim(monkeypatch):
    import json as _j
    from modules.taqdimot_dvigatel import ai
    monkeypatch.setattr(ai, "provayderlar", lambda: [("gemini", "k", "m")])

    def fake(nom, kalit, model, system, user, timeout=0):
        if "REJASINI" in system:
            return _j.dumps({"meta": {"mavzu": "T"}, "bolimlar": [{"nom": f"B{i}", "slaydlar": [{"sarlavha": f"S{i}{j}"} for j in range(4)]} for i in range(5)]})
        if "FAQAT 3-BO" in user:
            raise TimeoutError()
        if "FAQAT" in user:
            n = int(user.split("FAQAT ")[1].split("-")[0])
            return _j.dumps({"bolim": {"nom": f"B{n - 1}", "slaydlar": [{"sarlavha": f"S{j}", "elementlar": [{"tur": "matn", "matn": "x"}]} for j in range(4)]}})
        return _j.dumps({"meta": {"mavzu": "T"}, "test": [{"savol": "?", "variantlar": ["a", "b"], "javob": 1}]})
    monkeypatch.setattr(ai, "_chaqir", fake)
    m = ai.miya_yoz("T", "Pedagogika", "magistr", sozlama={"slayd_soni": 20, "til": "ru"})
    assert len(m["bolimlar"]) == 5 and sum(len(b["slaydlar"]) for b in m["bolimlar"]) == 20
    assert m["meta"]["til"] == "ru" and m["test"]
    r = ai.reja_toza({"bolimlar": [{"nom": "A", "slaydlar": ["x", {"sarlavha": "y"}]}] * 9})
    assert len(r["bolimlar"]) == 6


def test_tarjima_va_joylashuv():
    from modules.taqdimot_dvigatel import tarjima, bloklar_joy, rasm_tanla
    tr = tarjima.tarjimon("en")
    assert tr("2-MA’RUZA") == "LECTURE 2" and tr("**Javob:** 5") == "**Answer:** 5" and tr("Javobgarlik") == "Javobgarlik"
    assert tarjima.tarjimon("uz") is None
    assert rasm_tanla.buyum_rasmi("Olma") and rasm_tanla.buyum_rasmi("Mototsikl")
    m = {"meta": {"mavzu": "Test", "til": "ru"}, "bolimlar": [{"nom": "A", "slaydlar": [
        {"sarlavha": "S1", "joylashuv": "markaz", "elementlar": [{"tur": "tarif", "matn": "Qisqa ta’rif."}]},
        {"sarlavha": "S2", "elementlar": [{"tur": "matn", "matn": "a"}, {"tur": "matn", "matn": "b"}, {"tur": "matn", "matn": "c"}]},
        {"sarlavha": "S3", "elementlar": [{"tur": "matn", "matn": "Fil katta."}, {"tur": "rasm", "rasm": "d_elephant"}]}]}]}
    s = yasash.yasa(m, seed=2)
    assert s["miya"]["bolimlar"][0]["slaydlar"][0]["joylashuv"] == "markaz"
    assert set(s["dizayn"]) >= {"sarlavha", "kart", "titul", "bolim"}
    matn = " ".join(r["t"] for sl in s["slaydlar"] for el in sl["els"] if el["k"] == "text" for p in el["pp"] for r in p["rs"])
    assert "Определение" in matn or "ОПРЕДЕЛЕНИЕ" in matn
    assert set(bloklar_joy.JOYLASHUVLAR) >= {"rasm_panel", "markaz", "ustunlar"}


def test_kichik_sinf_royxat_rasmlari():
    from modules.taqdimot_dvigatel import rasm_tanla
    assert rasm_tanla._royxat_sozlari("Sabzi, piyoz, bodring va pomidor polizda o‘sadi.") == ["Sabzi", "piyoz", "bodring"]
    m = sxema.normallashtir({"meta": {"mavzu": "Polizda", "sinf": "1-sinf"}, "bolimlar": [{"nom": "A", "slaydlar": [
        {"sarlavha": "Sabzavotlar", "elementlar": [{"tur": "matn", "matn": "Sabzi, piyoz, bodring va pomidor polizda o‘sadi."}]}]}]})
    rasm_tanla.boyit(m)
    gal = [e for e in m["bolimlar"][0]["slaydlar"][0]["elementlar"] if e["tur"] == "galereya"]
    assert gal and len(gal[0]["rasmlar"]) >= 2


def test_ai_bolimlari_royxat_yoki_matn_bolsa_ham():
    m = sxema.normallashtir({"meta": {"mavzu": "T"}, "bolimlar": [{"nom": "A", "slaydlar": [{"sarlavha": "S", "elementlar": [{"tur": "matn", "matn": "x"}]}]}],
                             "takrorlash": [{"savol": "?", "javob": "!"}], "muammo": "matn", "metodika": ["a", "b"], "xatolar": {"x": 1},
                             "test": {"savol": "?"}, "keyingi": ["x"], "rasmlar": "yo'q", "meta2": 1})
    assert m["takrorlash"]["savollar"][0]["savol"] == "?" and m["metodika"]["bosqichlar"] == ["a", "b"]
    assert m["xatolar"] == [] and m["test"] == [] and m["rasmlar"] == []
    assert yasash.pptx(yasash.yasa(m, seed=1))[:2] == b"PK"


def test_saqlangan_korinish_va_fayl_nomi():
    from modules.taqdimot_dvigatel import api
    k = api.Dvigatel._korinish_toza({"seed": 5, "oila": "akademik", "palitra": "<x>", "dizayn": {"titul": 2, "yomon": 1}, "rasm_avto": False})
    assert k == {"seed": 5, "oila": "akademik", "dizayn": {"titul": 2}, "rasm_avto": False}
    d = api._biriktirma("Oʻzbekiston.pptx")
    d.encode("latin-1")
    assert 'filename="Ozbekiston.pptx"' in d and "filename*=UTF-8''" in d


def test_rus_tili_tanlansa_ozbekcha_qolgan_matn_tarjima_qilinadi(monkeypatch):
    import json as _j
    from modules.taqdimot_dvigatel import ai
    monkeypatch.setattr(ai, "provayderlar", lambda: [("gemini", "k", "m")])
    chaqiruvlar = []

    def fake(nom, kalit, model, system, user, timeout=0):
        chaqiruvlar.append(system[:30])
        if "tarjimonsan" in system:
            return _j.dumps({k: "Перевод: " + v[:20] for k, v in _j.loads(user).items()})
        assert "RUS tili" in user  # til buyrug'i xabarda bor
        return _j.dumps({"meta": {"mavzu": "Uy hayvonlari va ularning foydasi"}, "bolimlar": [{"nom": "Uy hayvonlari", "slaydlar": [
            {"sarlavha": "Sigir va qo‘y", "elementlar": [{"tur": "matn", "matn": "Млекопитающие кормят детёнышей молоком."},
                                                          {"tur": "lugat", "sozlar": [{"soz": "olma", "tarjima": "яблоко"}]}]}]}],
            "test": [{"savol": "Qaysi biri uy hayvoni?", "variantlar": ["Sigir", "Ayiq"], "javob": 0}]})
    monkeypatch.setattr(ai, "_chaqir", fake)
    m = ai.miya_yoz("Uy hayvonlari", "Biologiya", "maktab", "5-sinf", sozlama={"slayd_soni": 8, "til": "ru"})
    assert m["meta"]["mavzu"].startswith("Перевод") and m["bolimlar"][0]["nom"].startswith("Перевод")
    sl = m["bolimlar"][0]["slaydlar"][0]
    assert sl["sarlavha"].startswith("Перевод") and sl["elementlar"][0]["matn"].startswith("Млекопитающие")
    assert sl["elementlar"][1]["sozlar"][0]["soz"] == "olma"  # lug'at so'ziga tegilmaydi
    assert m["test"][0]["savol"].startswith("Перевод") and m["_tarjima"] >= 4
    assert sum(1 for c in chaqiruvlar if c.startswith("Sen tarjimonsan")) == 1


def test_aqlli_royxat_korinishlari():
    from modules.taqdimot_dvigatel import bloklar_royxat as BR
    assert set(BR.KORINISHLAR) >= {"kartalar", "ikonli", "raqamli", "zinapoya", "piramida", "vaqt", "sikl", "strelka"}
    assert BR.punktlar("• Kuzatish: bola ko‘radi\n• Hamkorlik — birga\n• Mustaqillik: o‘zi")[1] == {"nom": "Hamkorlik", "matn": "birga"}
    assert BR.punktlar("Oddiy matn.") is None
    bs = [{"nom": n, "matn": "Qisqa izoh matni"} for n in ("Bilim", "Tushunish", "Qo‘llash", "Tahlil")]
    sl = [{"sarlavha": kor, "elementlar": [{"tur": "xossalar", "bandlar": bs, "korinish": kor}]} for kor in BR.KORINISHLAR]
    m = sxema.normallashtir({"meta": {"mavzu": "Ro‘yxatlar"}, "bolimlar": [{"nom": "A", "slaydlar": sl}]})
    assert m["bolimlar"][0]["slaydlar"][3]["elementlar"][0]["korinish"] == "zinapoya"
    s = yasash.yasa(m, seed=3)
    for x in s["slaydlar"]:
        for el in x["els"]:
            if el["k"] == "text":
                assert el["fit"] and el["sc"] >= 0.7
    pir = [x for x in s["slaydlar"] if x.get("sarlavha") == "piramida" or any(
        el["k"] == "text" and any(r["t"] == "piramida" for p in el["pp"] for r in p["rs"]) for el in x["els"])]
    assert pir and sum(el["k"] == "path" for el in pir[0]["els"]) >= 4
    assert yasash.pptx(s)[:2] == b"PK"
