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


def test_foydalanuvchi_sozlamalari():
    from modules.taqdimot_dvigatel import sozlamalar, olchov
    z = sozlamalar.toza({"ramka": "burchak", "fon": "qogoz", "asosiy_rang": "#c2185b", "matn_rangi": "#zzzzzz", "shrift_sarlavha": "georgia",
                         "shrift_matn": "segoe", "olcham_matn": "katta", "chiqish": "birga", "otish": "push", "muallif": "  A.  R. ",
                         "qismlar": {"reja": False, "test": False, "nomalum": False}, "royxat": "zinapoya", "xato": "x", "pastki": "raqam"})
    assert z["asosiy_rang"] == "#C2185B" and "matn_rangi" not in z and "xato" not in z and z["muallif"] == "A. R."
    assert z["qismlar"] == {"reja": False, "test": False}
    m = json.load(open(os.path.join(os.path.dirname(yasash.__file__), "namuna_ratsional.json")))
    oddiy = yasash.yasa(m, seed=5)
    s = yasash.yasa(m, seed=5, sozlama=z)
    assert [x["blok"] for x in oddiy["slaydlar"]].count("reja") == 1 and "reja" not in [x["blok"] for x in s["slaydlar"]]
    assert "test" not in [x["blok"] for x in s["slaydlar"]] and s["meta"]["muallif"] == "A. R."
    assert all(any(el.get("nm") == "!!ramka" for el in x["els"]) for x in s["slaydlar"])
    assert all(x["qadam"] == 0 and x["otish"] == "push" for x in s["slaydlar"])
    assert s["shriftlar"]["head"]["face"] == "Georgia" and s["shriftlar"]["sans"]["face"] == "Segoe UI"
    assert "!qogoz" in s["slaydlar"][0]["fon"]["src"] and "!rc2185b" in s["slaydlar"][0]["fon"]["src"]
    assert uslub.fon_rasm(s["slaydlar"][0]["fon"]["src"][4:])[:2] == b"\xff\xd8"
    for x in s["slaydlar"]:
        for el in x["els"]:
            if el["k"] == "text":
                assert el["fit"]
    data = yasash.pptx(s)
    xml = b"".join(zipfile.ZipFile(io.BytesIO(data)).read(n) for n in zipfile.ZipFile(io.BytesIO(data)).namelist() if n.startswith("ppt/slides/slide"))
    assert b'typeface="Georgia"' in xml and b'typeface="Segoe UI"' in xml and b"<p:push" in xml
    # o'qilmaydigan rang (sariq yorug' fonda) to'qlashtiriladi va ogohlantiriladi
    s2 = yasash.yasa(m, seed=5, uslub_kod="anor.anor.0", sozlama={"asosiy_rang": "#FFF200", "matn_rangi": "#FAFAFA", "fon": "stars"})
    assert s2["uslub"]["acc"][0] != "#FFF200" and len(s2["ogohlantirish"]) == 3
    # sozlamasiz natija avvalgidek: shrift almashtirish oqimdan tashqariga chiqmaydi
    assert olchov.shrift("sans") == ("Calibri", "sans", 1.0) and olchov.olcham_k("sans", 20) == 1.0
    assert api.Dvigatel._korinish_toza({"seed": 3, "sozlama": {"ramka": "qalin", "x": 1}})["sozlama"] == {"ramka": "qalin"}


def test_ai_mazmun_sozlamalari():
    from modules.taqdimot_dvigatel import ai
    z = ai.sozlama_toza({"slayd_soni": 5, "hajm": "toliq", "misollar": "kop", "test_soni": "8", "qismlar": {"tarix": False, "reja": False}})
    assert z["slayd_soni"] == 5 and z["test_soni"] == 8 and z["qismlar"] == {"tarix": False}
    t = ai._sozlama_matni(z, "bakalavr")
    assert "110–160 so‘z" in t and "MISOLLAR: ko‘p" in t and "TEST: 8 ta" in t and "tarixiy ma’lumot" in t
    assert "TEST: yozma" in ai._sozlama_matni({"test_soni": 0})
    assert ai.sozlama_toza({})["test_soni"] is None and "TEST" not in ai._sozlama_matni({})


def test_kutubxona_mundarija_va_dastur():
    from modules.taqdimot_dvigatel import kutubxona_ai as ka
    html = ("<ul><li>I BOB. MEXANIKA</li><li>1-mavzu. Mexanik harakat</li><li>2-mavzu. Tezlik &amp; yo‘l</li>"
            "<li>1-mavzu. Mexanik harakat</li><li>3-mavzu. Механическое движение</li><li>II BOB. ISSIQLIK</li>"
            "<li>§ 4. Temperatura</li></ul><script>1-mavzu. yo'q</script>")
    m = ka.mundarija(ka.html_matn(html))
    assert [x["mavzu"] for x in m] == ["Mexanik harakat", "Tezlik & yo‘l", "Temperatura"]
    assert m[0]["bob"].startswith("I-bob") and m[-1]["bob"].startswith("II-bob") and m[-1]["raqam"] == 4
    d = ka.dastur_qatorlari("Fan dasturi\n1. To‘plamlar nazariyasi asoslari\n2) Natural sonlar va amallar\nMavzu 3: Kasr sonlar haqida\n4. X")
    assert [x["raqam"] for x in d] == [1, 2, 3] and d[2]["mavzu"] == "Kasr sonlar haqida"
    matn, jadval = ka.fayl_matni("d.txt", "1-mavzu. Kasrlar\n2-mavzu. O‘nli kasrlar".encode())
    assert "Kasrlar" in matn


def test_kutubxona_yozish_argumentlari_va_dars_rejasi():
    from modules.taqdimot_dvigatel import kutubxona_ai as ka
    r = {"id": 1, "daraja": "maktab", "sinf": "7", "fan": "Fizika", "raqam": 5, "bob": "I-bob. Mexanika", "mavzu": "Tezlik",
         "en": "speed", "yonalish": ""}
    assert ka.yozish_sozlamasi(r)["slayd_soni"] == 10 and ka.yozish_sozlamasi({**r, "sinf": "2"})["hajm"] == "orta"
    assert ka.yozish_sozlamasi({**r, "daraja": "bakalavr", "sinf": "2"})["slayd_soni"] == 14
    mavzu, fan, daraja, sinf, tur, qosh, manba = ka.yozish_argumentlari(r, ["Yo‘l"], ["Tezlanish"])
    assert (mavzu, fan, tur) == ("Tezlik", "Fizika", "dars") and "Tezlanish" in qosh and "5-mavzu" in qosh and "speed" in manba
    # dars rejasi (ochiq dars uchun asos) normallashadi, noma'lum maydonlar tashlanadi
    m = sxema.normallashtir({"meta": {"mavzu": "Tezlik"}, "dars": {
        "maqsadlar": {"talimiy": "a", "tarbiyaviy": "b", "rivojlantiruvchi": "c"}, "metodlar": ["Klaster", {"nom": "Aqliy hujum"}],
        "bosqichlar": [{"nom": "Tashkiliy qism", "vaqt": "2 daqiqa"}, {"nom": "Yangi mavzu", "vaqt": 25}, {"vaqt": 3}], "x": 1}})
    d = m["dars"]
    assert d["davomiylik"] == 27 and [b["nom"] for b in d["bosqichlar"]] == ["Tashkiliy qism", "Yangi mavzu"]
    assert [x["nom"] for x in d["metodlar"]] == ["Klaster", "Aqliy hujum"] and "x" not in d
    assert sxema.normallashtir({"meta": {"mavzu": "A"}})["dars"]["bosqichlar"] == []


def test_rejadagi_rasmlar_katalogda():
    from modules.taqdimot_dvigatel import rasm_tanla
    k = rasm_tanla.katalog("Tezlik va mexanik harakat", "Fizika")
    assert any("rejada" in nom for _, nom in k)


def test_ochiq_dars_metodlar_bazasi():
    from modules.taqdimot_dvigatel import ochiq_metodlar as om
    d = om.miya()
    assert om.tekshir(d) == []
    assert len(d["metodlar"]) >= 80 and len(d["andozalar"]) == 15
    for a in d["andozalar"]:
        assert sum(b["daq"] for b in a["bosqichlar"]) == a["daqiqa"] in (45, 80)
    kodlar = {m["kod"] for m in d["metodlar"]}
    # har fan × yosh × andoza bosqichi uchun kamida bitta mos metod bor
    for f in d["fanlar"]:
        for a in (x for x in d["andozalar"] if x["kod"] in f["andozalar"]):
            for y in set(f["yosh"]) & set(a["yosh"]):
                for b in a["bosqichlar"]:
                    t = set(b["metod_turi"]) - {"guruhlash", "birlashtirish"}
                    if t:
                        assert any(t & set(m["tur"]) and y in m["yosh"] and (m["fan"] == "*" or f["kod"] in m["fan"])
                                   and m["vaqt"][0] <= b["daq"] for m in d["metodlar"]), (f["kod"], a["kod"], y, b["nom"])
                    assert set(b["afzal"]) <= kodlar


@pytest.mark.parametrize("daraja,sinf,fan,fmt,andoza", [
    ("maktab", "1", "O‘qish savodxonligi", "ochiq", ""), ("maktab", "2", "Matematika", "ochiq", ""), ("maktab", "7", "Fizika", "namunaviy", ""),
    ("maktab", "9", "Kimyo", "ochiq", "laboratoriya"), ("maktab", "10", "Tarix", "oddiy", ""), ("maktab", "5", "Jismoniy tarbiya", "ochiq", ""),
    ("bakalavr", "2", "Pedagogika", "ochiq", ""), ("bakalavr", "4", "Boshlang‘ich ta’limda matematika o‘qitish metodikasi", "namunaviy", ""),
    ("magistr", "1", "Psixologiya", "oddiy", "")])
def test_ochiq_dars_generator_word_va_pptx(daraja, sinf, fan, fmt, andoza):
    from docx import Document
    from modules.taqdimot_dvigatel import ishlanma, ochiq_dars as od
    for rejim in ("tezkor", "qolda"):
        d = od.tuz({"daraja": daraja, "sinf": sinf, "fan": fan, "mavzu": "Sinov mavzusi", "format": fmt, "andoza": andoza,
                    "rejim": rejim, "urug": 7}, NAMUNA if rejim == "qolda" else None)
        assert d["meta"]["rasm"], "titulga universal rasm qo'yilmadi"
        assert sum(b["daq"] for b in d["bosqichlar"]) == d["meta"]["daqiqa"]
        metodlar = [b["metod"]["kod"] for b in d["bosqichlar"] if b["metod"] and b["metod"]["tur"] == "metod"]
        assert len(metodlar) == len(set(metodlar)), "bir metod ikki marta tanlangan"
        assert len(d["kompetensiyalar"]) == len(set(d["kompetensiyalar"]))
        if andoza:
            assert d["meta"]["andoza"].startswith(andoza)
        doc = Document(io.BytesIO(ishlanma.docx_yoz(d, NAMUNA)))
        matn = "\n".join(p.text for p in doc.paragraphs)
        assert "Darsning borishi" in matn and "1-ilova" in matn and "**" not in matn and "«mavzu»" not in matn
        sah = yasash.yasa(od.ochiq_miya(d, NAMUNA), seed=3, bolim_titul=True)
        assert sah["slaydlar"][0]["blok"] == "titul" and len(sah["slaydlar"]) >= 8


def test_ochiq_dars_sinf_majburiy_va_fan_yoshga_mos():
    from modules.taqdimot_dvigatel import ochiq_dars as od
    with pytest.raises(ValueError):
        od.tuz({"daraja": "maktab", "fan": "Matematika", "mavzu": "Kasrlar"})
    assert od.fan_kodi("Ona tili", "5-6") == "ona_tili" and od.fan_kodi("Ona tili", "1-2") == "oqish"
    assert od.fan_kodi("Algebra", "7-9") == "matematika" and od.fan_kodi("Oliy matematika", "b1-2") == "otm_aniq"


def test_universal_rasmlar_bor_va_chiroyli():
    from modules.taqdimot_dvigatel import rasm_tanla, rasmlar
    reestr = {r["kalit"]: r for r in rasmlar.papka_reestri()}
    for guruh, kodlar in rasm_tanla.UNIVERSAL.items():
        for k in kodlar.split():
            assert rasmlar.bor(k) and reestr.get(k, {}).get("tur") == "rasm", (guruh, k)
    assert rasm_tanla.universal({"fan": "Geografiya", "sinf": "6", "mavzu": "Vulqonlar"}) == "vulqon"
    assert rasm_tanla.universal({"fan": "Musiqa", "sinf": "3", "mavzu": "Dutor"}) == "dutor"
    # mos rasm topilmagan taqdimot ham titulsiz qolmaydi
    m = {"meta": {"mavzu": "Qwxyz mavzusi", "fan": "Kimyo", "sinf": "8"}, "bolimlar": [{"nom": "Qwxyz", "slaydlar": [
        {"sarlavha": "Qwxyz", "elementlar": [{"tur": "matn", "matn": "Qwxyz zyxwq"}]}]}]}
    m = sxema.normallashtir(m)
    rasm_tanla.boyit(m)
    assert m["meta"]["rasm"] in rasm_tanla.UNIVERSAL["kimyo"].split() and m["bolimlar"][0].get("rasm")


def test_ochiq_dars_ai_rejimi(monkeypatch):
    from modules.taqdimot_dvigatel import ai, ochiq_ai, ochiq_dars as od
    chaqirildi = []

    def soxta(system, user, deadline, t0):
        chaqirildi.append(user)
        return {"tanlov": {"1": "yoq_metod"}, "guruhlash": "oldindan_tuzilgan", "birlashtirish": "nomalum",
                "maqsadlar": {"talimiy": "Kvadrat tenglamani yechish usullarini guruhda o‘rganish"},
                "guruh_nomlari": ["Diskriminant", "Viyet", "Ildiz", "Koeffitsiyent"],
                "nutq": {"0": "Assalomu alaykum, aziz o‘quvchilar!"}, "rasm": {"2": "al_xorazmiy", "3": "yoq_rasm"}, "titul_rasm": "al_xorazmiy"}
    monkeypatch.setattr(ai, "_bir_chaqiruv", soxta)
    monkeypatch.setattr(ai, "masalliq_yoz", lambda *a, **k: sxema.masalliq_toza({"tezis": "Har tenglamaning ildizi bor", "vazifalar": {"A": "1-misol"}}))
    d = ochiq_ai.tuz({"daraja": "maktab", "sinf": "8", "fan": "Algebra", "mavzu": "Kvadrat tenglamalar", "oquvchilar": 24}, None)
    assert d["meta"]["rejim"] == "ai" and d["meta"]["rasm"] == "al_xorazmiy" and d["meta"]["masalliq_bor"]
    assert [g["nom"] for g in d["guruhlash"]["guruhlar"]][:2] == ["Diskriminant", "Viyet"]
    assert d["bosqichlar"][0]["nutq"].startswith("Assalomu") and d["bosqichlar"][2]["rasm"] == "al_xorazmiy" and not d["bosqichlar"][3]["rasm"]
    assert d["maqsadlar"]["talimiy"].startswith("Kvadrat") and d["masalliq"]["tezis"]
    nz = {i: [n["kod"] for n in b["nomzodlar"]] for i, b in enumerate(d["bosqichlar"])}
    assert all(b["metod"]["kod"] in nz[i] for i, b in enumerate(d["bosqichlar"]) if b["metod"] and b["metod"]["tur"] == "metod")
    assert "RASMLAR" in chaqirildi[0] and "Kvadrat tenglamalar" in chaqirildi[0]
    assert od.tuz({"daraja": "maktab", "sinf": "8", "fan": "Algebra", "mavzu": "Kvadrat tenglamalar", "rejim": "qolda",
                   "urug": d["meta"]["urug"]}, None, mas=d["masalliq"])["guruhlash"]["guruhlar"][0]["nom"] == "Diskriminant"
