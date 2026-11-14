"""REV555: xalqaro sinf — shubhali natija, reyting va barqaror ko'chish (sof qoidalar)."""
import math
import random

from modules.xalqaro_guruh import (KOCHISH_UCHUN, SHUBHA_MATNI, guruhlarga_bol, nomos_ulushi, qayta_guruhla,
                                   reyting_hisobla, urinish_eslatmasi, urinish_shubhasi)


def U(ball, soni=12, soniya=None, chiqishlar=0, foiz=None, **kw):
    """Oddiy toza urinish: bir savolga 60 soniya."""
    return {"ball": ball, "soni": soni, "soniya": soni * 60 if soniya is None else soniya, "chiqishlar": chiqishlar,
            "foiz": foiz if foiz is not None else max(0, min(100, int((ball - 250) / 5))), **kw}


def test_shubha_belgilari():
    assert urinish_shubhasi(U(500)) == []
    assert urinish_shubhasi(U(600, soniya=12 * 8, foiz=90)) == ["juda_tez"]            # 8 soniyadan, 90% to'g'ri
    assert urinish_shubhasi(U(350, soniya=12 * 8, foiz=30)) == []                      # tez, lekin natija past — taxminlab bosgan, shubha emas
    assert urinish_shubhasi(U(500, chiqishlar=3)) == ["ilovadan_chiqdi"]
    assert urinish_shubhasi(U(500, chiqishlar=2)) == []
    assert urinish_shubhasi(U(560), oldingi_reyting=460) == ["keskin_osish"]           # +100 ball
    assert urinish_shubhasi(U(540), oldingi_reyting=460) == []                         # +80 — oddiy o'sish
    assert urinish_shubhasi(U(700, soniya=60, foiz=100, chiqishlar=5), oldingi_reyting=450) == ["juda_tez", "ilovadan_chiqdi", "keskin_osish"]
    assert set(SHUBHA_MATNI) == {"juda_tez", "ilovadan_chiqdi", "keskin_osish", "nomos_javoblar"}


def test_nomos_javoblar_faqat_eslatma_bloklamaydi():
    q = [-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5]
    assert nomos_ulushi(q, [True] * 5 + [False] * 5) == 0.0          # osonlari to'g'ri, qiyinlari xato — odatiy
    assert nomos_ulushi(q, [False] * 5 + [True] * 5) == 1.0          # aksincha — umuman odatiy emas
    assert nomos_ulushi(q, [True] * 10) == 0.0 and nomos_ulushi(q[:3], [False, True, True]) == 0.0   # juftlik kam — baho yo'q
    galati = U(520, qiyinliklar=q, togri=[False] * 5 + [True] * 5)
    assert urinish_shubhasi(galati) == [] and urinish_eslatmasi(galati) == ["nomos_javoblar"]        # shubha EMAS — faqat eslatma
    r = reyting_hisobla([galati])
    assert r["reyting"] == 520 and r["kutmoqda"] == 0 and r["tarix"][0]["holat"] == "hisobga" and r["tarix"][0]["eslatma"] == ["nomos_javoblar"]
    assert urinish_eslatmasi(U(520, qiyinliklar=q, togri=[True, True, True, True, False, True, False, False, False, False])) == []


def test_halol_oquvchi_qisqa_testda_bloklanmaydi():
    # 12–14 savolli testda halol (Rasch bo'yicha yechgan) o'quvchi «g'alati javoblar» sababli tekshiruvga TUSHMASLIGI kerak
    rnd = random.Random(14)
    bank = [rnd.uniform(-2.3, 2.3) for _ in range(160)]
    blok = eslatma = 0
    for _ in range(3000):
        th = rnd.uniform(-2.2, 2.2); q = rnd.sample(bank, rnd.choice([12, 14]))
        u = U(500, qiyinliklar=q, togri=[rnd.random() < 1 / (1 + math.exp(-(th - b))) for b in q])
        blok += bool(urinish_shubhasi(u)); eslatma += bool(urinish_eslatmasi(u))
    assert blok == 0                      # halol o'quvchi hech qachon to'xtatilmaydi
    assert eslatma / 3000 < 0.05          # eslatma ham kam chiqadi (o'qituvchini chalg'itmaydi)


def test_reyting_toza_natijalar_silliq_ozgaradi():
    r = reyting_hisobla([U(480), U(500), U(520)])
    assert r["tarix"][0]["holat"] == "hisobga" and r["kutmoqda"] == 0
    assert r["reyting"] == round(0.65 * round(0.65 * 480 + 0.35 * 500) + 0.35 * 520) == 499
    assert r["toza"] == [480, 500, 520]
    assert reyting_hisobla([]) == {"reyting": None, "tarix": [], "toza": [], "kutmoqda": 0}


def test_gpt_bilan_olingan_natija_kotarmaydi():
    # 450 lik o'quvchi birdan 700 oladi (tez, ilovadan chiqqan) — reyting O'ZGARMAYDI, natija tekshiruvda turadi
    r = reyting_hisobla([U(450), U(700, soniya=90, foiz=100, chiqishlar=4)])
    assert r["reyting"] == 450 and r["kutmoqda"] == 1 and r["tarix"][1]["holat"] == "shubhali"
    assert set(r["tarix"][1]["sabab"]) == {"juda_tez", "ilovadan_chiqdi", "keskin_osish"}
    # keyingi toza natija yana 460 — shubhali natija RAD etiladi, reytingga kirmaydi
    r = reyting_hisobla([U(450), U(700, soniya=90, foiz=100, chiqishlar=4), U(460)])
    assert r["tarix"][1]["holat"] == "rad" and r["kutmoqda"] == 0 and r["toza"] == [450, 460]
    assert r["reyting"] == round(0.65 * 450 + 0.35 * 460) == 454


def test_haqiqiy_osish_ikkinchi_yaqin_natija_bilan_tasdiqlanadi():
    # 450 → 560: keskin o'sish — hozircha kutadi, reyting o'zgarmaydi
    r = reyting_hisobla([U(450), U(560)])
    assert r["reyting"] == 450 and r["kutmoqda"] == 1 and r["tarix"][1]["sabab"] == ["keskin_osish"]
    # → yana 555 (normal sharoitda): o'sish haqiqiy — ikkalasi ham hisobga olinadi (aks holda abadiy tekshiruvda qolardi)
    r = reyting_hisobla([U(450), U(560), U(555)])
    assert [x["holat"] for x in r["tarix"]] == ["hisobga", "tasdiqlandi", "hisobga"] and r["toza"] == [450, 560, 555] and r["kutmoqda"] == 0
    assert r["reyting"] == round(0.65 * round(0.65 * 450 + 0.35 * 560) + 0.35 * 555) == 511
    # → keyingi natija pasaysa (560 dan keyin 470): sakrash tasdiqlanmadi
    r = reyting_hisobla([U(450), U(560), U(470)])
    assert [x["holat"] for x in r["tarix"]] == ["hisobga", "rad", "hisobga"] and r["toza"] == [450, 470]


def test_chindan_osgan_oquvchi_keyin_tekshiruvga_tushavermaydi():
    # 383 → 633 (kutadi) → 613 (tasdiqlandi) → 686: endi u 620 atrofidagi o'quvchi — 686 «sakrash» EMAS, darhol hisobga olinadi
    r = reyting_hisobla([U(383), U(633), U(613), U(686)])
    assert [x["holat"] for x in r["tarix"]] == ["hisobga", "tasdiqlandi", "hisobga", "hisobga"] and r["kutmoqda"] == 0
    assert r["toza"] == [383, 633, 613, 686] and r["reyting"] > 560
    # lekin shu o'quvchi birdan 750 olsa-yu, tez yechgan bo'lsa — baribir tekshiruvga tushadi
    r = reyting_hisobla([U(383), U(633), U(613), U(750, soniya=60, foiz=100)])
    assert r["tarix"][-1]["holat"] == "shubhali" and "juda_tez" in r["tarix"][-1]["sabab"]


def test_kuchli_shubhali_natija_ozi_hech_qachon_hisobga_kirmaydi():
    tez = U(700, soniya=90, foiz=100, chiqishlar=4)
    # ikki marta ketma-ket «tez + ilovadan chiqqan» 700 — ikkalasi ham tekshiruvda qoladi, reyting 450
    r = reyting_hisobla([U(450), tez, dict(tez)])
    assert r["reyting"] == 450 and r["kutmoqda"] == 2 and all(x["holat"] == "shubhali" for x in r["tarix"][1:])
    # keyin normal sharoitda (sekin, ilovadan chiqmay) 690 oldi: shu natija hisobga olinadi, lekin tez olingan 700 — YO'Q
    r = reyting_hisobla([U(450), tez, U(690)])
    assert [x["holat"] for x in r["tarix"]] == ["hisobga", "rad", "hisobga"] and r["toza"] == [450, 690]
    assert r["reyting"] == round(0.65 * 450 + 0.35 * 690) == 534      # reyting ham birdan 690 ga chiqmaydi


def test_kirish_testi_shubhali_bolsa_reyting_berilmaydi():
    r = reyting_hisobla([U(690, soniya=70, foiz=100)])
    assert r["reyting"] is None and r["kutmoqda"] == 1          # guruhga tushmaydi — qayta topshirishi kerak
    r = reyting_hisobla([U(690, soniya=70, foiz=100), U(480)])
    assert r["reyting"] == 480 and r["tarix"][0]["holat"] == "rad"


def _sinf(n=60):
    """n o'quvchi, reyting 700 dan pastga; hammasi guruhlangan, oxirgi natijalari reytingiga teng."""
    az = [{"user_id": i, "reyting": 700 - i * 3, "guruh": None, "toza": [700 - i * 3] * 3} for i in range(1, n + 1)]
    b = guruhlarga_bol(az)
    g = {u: x["raqam"] for x in b["guruhlar"] for u in x["azolar"]}
    for a in az:
        a["guruh"] = g[a["user_id"]]
    return az


def test_birinchi_marta_reyting_boyicha_bolinadi():
    az = [{"user_id": i, "reyting": 300 + i, "guruh": None, "toza": [300 + i]} for i in range(1, 61)] + [{"user_id": 99, "reyting": None, "guruh": None}]
    r = qayta_guruhla(az)
    assert r["toliq_qayta"] and [len(g["azolar"]) for g in r["guruhlar"]] == [30, 30] and r["kutayotgan"] == [99]
    assert len(r["ozgarishlar"]) == 60 and all(x["tur"] == "yangi" for x in r["ozgarishlar"])


def test_hech_narsa_ozgarmasa_hamma_joyida():
    r = qayta_guruhla(_sinf())
    assert not r["toliq_qayta"] and r["ozgarishlar"] == []


def test_bitta_omadli_natija_guruhni_ozgartirmaydi():
    az = _sinf()
    a = next(x for x in az if x["user_id"] == 45)        # 2-guruhda
    a["reyting"] = 690                                    # reytingi yuqoriga chiqib ketdi …
    a["toza"] = [565, 565, 700]                           # … lekin faqat BITTA yuqori natija bilan
    r = qayta_guruhla(az)
    assert r["ozgarishlar"] == [] and 45 in r["guruhlar"][1]["azolar"]


def test_barqaror_oquvchi_yuqori_guruhga_kochadi_qolganlar_qoladi():
    az = _sinf()
    a = next(x for x in az if x["user_id"] == 45)
    a["reyting"], a["toza"] = 690, [560, 685, 690, 695]   # ketma-ket 3 ta yuqori toza natija
    r = qayta_guruhla(az)
    assert not r["toliq_qayta"]
    assert r["ozgarishlar"] == [{"user_id": 45, "eski": 2, "yangi": 1, "tur": "yuqoriga"}]     # faqat u ko'chdi
    assert [len(g["azolar"]) for g in r["guruhlar"]] == [31, 29]


def test_barqaror_pasaygan_oquvchi_quyi_guruhga_tushadi():
    az = _sinf()
    a = next(x for x in az if x["user_id"] == 10)         # 1-guruhda (reyting 670)
    a["reyting"], a["toza"] = 540, [530, 540, 545]
    r = qayta_guruhla(az)
    assert r["ozgarishlar"] == [{"user_id": 10, "eski": 1, "yangi": 2, "tur": "pastga"}]
    az = _sinf(); a = next(x for x in az if x["user_id"] == 10)
    a["reyting"], a["toza"] = 540, [670, 670, 540]        # bitta yomon kun — joyida qoladi
    assert qayta_guruhla(az)["ozgarishlar"] == []


def test_yangi_oquvchi_reytingiga_mos_guruhga_tushadi():
    az = _sinf() + [{"user_id": 500, "reyting": 695, "guruh": None, "toza": [695]}, {"user_id": 501, "reyting": 400, "guruh": None, "toza": [400]},
                    {"user_id": 502, "reyting": None, "guruh": None}]
    r = qayta_guruhla(az)
    oz = {x["user_id"]: x for x in r["ozgarishlar"]}
    assert oz[500]["yangi"] == 1 and oz[501]["yangi"] == 2 and oz[500]["tur"] == "yangi" and set(oz) == {500, 501}
    assert r["kutayotgan"] == [502]


def test_guruh_kichraysa_birlashadi():
    az = [a for a in _sinf(90) if a["user_id"] <= 65]     # 3 guruh edi; 3-guruhdan 25 kishi ketdi: 30 + 30 + 5
    r = qayta_guruhla(az)
    assert r["toliq_qayta"] and [len(g["azolar"]) for g in r["guruhlar"]] == [30, 35]
    assert {x["user_id"] for x in r["ozgarishlar"]} == {61, 62, 63, 64, 65} and all(x["eski"] == 3 and x["yangi"] == 2 for x in r["ozgarishlar"])


def test_tasodifiy_holatlarda_hech_kim_yoqolmaydi_va_hajm_saqlanadi():
    rnd = random.Random(555)
    for _ in range(300):
        n = rnd.randint(1, 200)
        az = []
        for i in range(1, n + 1):
            rey = rnd.choice([None, None] + [rnd.randint(300, 700)] * 8)
            az.append({"user_id": i, "reyting": rey, "guruh": rnd.choice([None, 1, 2, 3, 4, 5, 6, 7]) if rey else None,
                       "toza": [rnd.randint(300, 700) for _ in range(rnd.randint(0, 5))]})
        r = qayta_guruhla(az)
        ichida = [u for g in r["guruhlar"] for u in g["azolar"]]
        reytingli = [a["user_id"] for a in az if a["reyting"] is not None]
        assert sorted(ichida) == sorted(reytingli) and len(set(ichida)) == len(ichida)
        assert sorted(r["kutayotgan"]) == sorted(a["user_id"] for a in az if a["reyting"] is None)
        if len(reytingli) >= 20:
            assert all(20 <= len(g["azolar"]) <= 39 for g in r["guruhlar"]), [len(g["azolar"]) for g in r["guruhlar"]]
        assert [g["raqam"] for g in r["guruhlar"]] == list(range(1, len(r["guruhlar"]) + 1))
    assert KOCHISH_UCHUN == 3
