"""REV561: Kabu-bot (AI'siz) — yozuv, niyat, masala/savol farqi, mavzu topish, o'quvchi javoblari."""
import unittest
from datetime import datetime, timedelta, timezone

from modules import kabu_bot as K
from modules import pasport as PS
from modules.mat_bank import bank_ol

B = bank_ol()
MAV = {r: {"nom": m["nom"], "kitob": m["kitob"], "jami": len(m["testlar"])} for r, m in B.mavzular.items()}
HOZIR = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)


class Yozuv(unittest.TestCase):
    def test_normallash(self):
        self.assertEqual(K.normallash("O‘quvchi  BO'LINISH"), "oquvchi bolinish")
        self.assertEqual(K.normallash("Şu çiqiş, öğrenci"), "shu chiqish, ogrenci")
        self.assertEqual(K.normallash("Қандай натижам?"), "qanday natijam?")          # kirill
        self.assertEqual(K.normallash("Ўқувчи"), "oquvchi")
        self.assertEqual(K.normallash(None), "")

    def test_apostrofli_va_apostrofsiz_bir_xil(self):
        for a, b in (("o‘quvchi", "oquvchi"), ("bo'linish belgilari", "bolinish belgilari"), ("g‘alaba", "galaba")):
            self.assertEqual(K.normallash(a), K.normallash(b))


NIYAT = [
    ("salom", "salom"), ("Assalomu alaykum", "salom"), ("salom kabu", "salom"), ("hi", "salom"),
    ("natijam qanday?", "pasport"), ("qanday ketyapman", "pasport"), ("holatim qanday", "pasport"), ("men qaysi darajadaman? darajam", "pasport"), ("pasportimni ko‘rsat", "pasport"), ("Натижам қандай", "pasport"),
    ("nimani o‘rganay?", "nozik"), ("zaif mavzularim qaysi", "nozik"), ("qayerda xato qilyapman", "nozik"), ("nozik joylarim", "nozik"), ("nimani organay", "nozik"),
    ("nimani unutdim?", "takror"), ("takrorlash kerak", "takror"), ("esimdan chiqib ketdi", "takror"),
    ("test tuz", "test"), ("7-mavzuda test ber", "test"), ("savol ber", "test"), ("menga test kerak", "test"), ("mashq qilmoqchiman", "test"), ("kasr bo‘yicha test", "test"),
    ("formula so‘ra", "formula"), ("formulani yodlatib tur", "formula"),
    ("eslatmani yoq", "eslatma"), ("eslatmani o‘chir", "eslatma"), ("eslatma kerakmas", "eslatma"), ("eslatma nima?", "eslatma"),
    ("guruhim qaysi", "guruh"), ("reytingim qancha", "guruh"), ("o‘qituvchim kim", "guruh"), ("kirish testi nima", "guruh"),
    ("yordam", "yordam"), ("nima qila olasan?", "yordam"), ("sen kimsan", "yordam"),
    ("rahmat", "rahmat"), ("katta rahmat", "rahmat"), ("xayr", "xayr"), ("", "bosh"), ("   ", "bosh"),
    ("kvadrat tenglama haqida", "mavzu"), ("7-mavzu nima?", "mavzu"), ("oddiy kasrlar", "mavzu"), ("logarifm qoidasi", "mavzu"),
    ("asdfgh qwerty", "nomalum"), ("bugun havo qanday", "nomalum"), ("futbolda kim yutdi", "nomalum"),
]
MASALA = [
    "x^2 - 5x + 6 = 0 ni yechib ber", "12 - 6 : 3 + 2 * 4 nechaga teng", "2x + 3 = 11 tenglamani yeching", "sin(x)+cos(x)=1 yechimini top", "hisobla 25*4+10",
    "poyezd 60 km/soat tezlik bilan 3 soat yurdi, necha km yo‘l bosdi", "300 ning 15 foizini toping", "a+b=10, a-b=2 bo‘lsa a ni top", "3/4 + 5/6 ni hisobla", "√144 + 5^2 nechaga teng",
    "Yechib bering: (x-1)(x+2)>0", "log2(8) ni hisoblang", "5 ta olma 3 ta nok yig‘indisi nechta", "2^10 qancha", "integral x dx ni yechib ber",
]
SAVOL_MASALA_EMAS = ["natijam qanday?", "kvadrat tenglama haqida", "formula so‘ra", "7-mavzuda test ber", "nimani o‘rganay", "eslatmani yoq", "guruhim qaysi", "salom", "yordam", "takrorlash kerak"]


class Niyat(unittest.TestCase):
    def test_jadval(self):
        xato = [(m, k, K.niyat_oquvchi(m, MAV)) for m, k in NIYAT if K.niyat_oquvchi(m, MAV) != k]
        self.assertEqual(xato, [])

    def test_masalalar_yechilmaydi(self):
        for m in MASALA:
            self.assertTrue(K.masala_mi(m), m)
            self.assertEqual(K.niyat_oquvchi(m, MAV), "masala", m)
        for m in SAVOL_MASALA_EMAS:
            self.assertFalse(K.masala_mi(m), m)

    def test_eslatma_buyrugi(self):
        for m, v in (("eslatmani yoq", True), ("eslatma yoqing", True), ("eslatmani ochir", False), ("eslatma kerakmas", False), ("eslatma nima", None), ("salom", None)):
            self.assertIs(K.eslatma_buyrugi(K.normallash(m)), v, m)


class Mavzu(unittest.TestCase):
    def test_aniq_raqam(self):
        self.assertEqual(K.mavzu_topish("7-mavzu", MAV), [7]); self.assertEqual(K.mavzu_topish("31 mavzuda test", MAV), [31]); self.assertEqual(K.mavzu_topish("mavzu 20", MAV), [20])
        self.assertEqual(K.mavzu_topish("999-mavzu", MAV), [])

    def test_nom_bo_yicha(self):
        sinov = {"kvadrat tenglamani yech": 20, "oddiy kasrlar": 7, "logarifmik tenglama": 57, "geometrik progressiya": 41, "arifmetik progressiya yig‘indisi": 40, "hosila": 72,
                 "foiz masalasi": 43, "prosentga oid": 43, "viyet teoremasi": 21, "modulli tenglama": 35, "irratsional tengsizlik": 39, "romb yuzi": 100, "silindr hajmi": 132, "vektor uzunligi": 121,
                 "uchburchak yuzi": 97, "bo‘linish belgilari": 2, "ekub va ekuk": 4, "keltirish formulalari": 61, "aniq integral": 84, "sinus va kosinus teoremasi": 92}
        for m, kutilgan in sinov.items():
            self.assertIn(kutilgan, K.mavzu_topish(m, MAV), f"{m}: {K.mavzu_topish(m, MAV)}")

    def test_tuzilmadan_mavzu(self):
        for m, k in (("x^2 - 5x + 6 = 0 ni yechib ber", [20]), ("x² - 4 = 0", [20]), ("2x + 3 = 11", [19]), ("x + 5 > 2x - 1", [29]), ("(x-1)(x+2)>0", [31]), ("3/4 + 5/6", [7]),
                     ("√144 + 5^2", [15]), ("sin x + cos x = 1", None), ("log2(8)", None), ("12 - 6 : 3 + 2 * 4", [1])):
            t = K.mavzu_topish(m, MAV)
            if k is None:      # kalit so'z orqali topiladigan: trigonometriya (60–69) yoki logarifm (55–58)
                self.assertTrue(any(r in t for r in range(60, 70)) or any(r in t for r in range(55, 59)), (m, t))
            else:
                self.assertEqual(t, k, m)

    def test_masala_mavzusi(self):
        self.assertIn(20, K.mavzu_topish("x^2 - 5x + 6 = 0 kvadrat tenglamani yech", MAV))
        self.assertEqual(K.mavzu_topish("12 - 6 : 3 + 2 * 4 nechaga teng", MAV), [1])        # faqat sonlar — hisoblashga oid misollar
        self.assertEqual(K.mavzu_topish("asdfgh", MAV), []); self.assertEqual(K.mavzu_topish("", MAV), [])
        self.assertLessEqual(len(K.mavzu_topish("tenglama", MAV)), 3)


class Formula(unittest.TestCase):
    def test_navbat(self):
        idlar = ["a", "b", "c", "d", "e"]
        t = {"a": (3, 3, True, HOZIR - timedelta(hours=1)),        # mustahkam — navbatda yo'q
             "b": (2, 1, False, HOZIR - timedelta(days=1)),          # xato — birinchi
             "c": (1, 1, True, HOZIR - timedelta(days=9)),           # unutilgan
             "d": (1, 1, True, HOZIR - timedelta(days=2))}           # takrorlash vaqti
        # e — hali ko'rilmagan
        self.assertEqual(K.formula_navbat(idlar, t, HOZIR, 5), ["b", "e", "c", "d"])
        self.assertEqual(K.formula_navbat(idlar, t, HOZIR, 2), ["b", "e"]); self.assertEqual(K.formula_navbat([], {}, HOZIR), [])


def passport(**o):
    ms = [{"raqam": 7, "nom": "Oddiy kasrlar", "kitob": "1.2.1", "jami": 19, "ko_rilgan": 8, "hozirgi": 25, "aniqlik": 50, "holatlar": {"mustahkam": 0, "takror": 0, "unutilgan": 6, "xato": 2}, "nozik": True},
          {"raqam": 2, "nom": "Bo‘linish belgilari", "kitob": "1.1.2", "jami": 29, "ko_rilgan": 10, "hozirgi": 90, "aniqlik": 90, "holatlar": {"mustahkam": 9, "takror": 1, "unutilgan": 0, "xato": 0}, "nozik": False}]
    p = {"kim": {"user_id": 1, "ism": "Ali", "sinf": "8", "rol": "oquvchi"}, "faollik": {"oxirgi": "x", "kun_7": 3, "kun_30": 5, "jami_harakat": 30},
         "matematika": {"ko_rilgan": 18, "jami_savol": 5392, "qamrov": 0, "hozirgi": 56, "urinish": 25, "holatlar": {"mustahkam": 9, "takror": 1, "unutilgan": 6, "xato": 2}, "daraja": "o‘rta",
                        "elementar": {"ko_rilgan": 18, "jami": 121, "hozirgi": 56, "daraja": "o‘rta", "ishonchli": True}, "mavzular": ms, "nozik": [ms[0]], "takrorlash": [ms[0], ms[1]]},
         "xalqaro": {"sinflar": [{"nom": "TIMSS 8-A", "toplam": "T11_G8_M", "oqituvchi": "Karim ustoz", "guruh": 2, "guruhlar_soni": 3, "reyting": 488}], "imtihonlar": [], "sohalar": [], "fikrlash": [], "zaif_mavzular": []},
         "eslatma": "x", "xulosa": ["Birinchi gap.", "Ikkinchi gap."]}
    p.update(o)
    return p


def ctx(p=None, **kw):
    return K.Ctx(MAV, (lambda: p) if p is not None else None, hozir=HOZIR, **kw)


def matn(r):
    return " ".join(b["s"] if b["t"] == "matn" else " ".join(b["items"]) for b in r["javob"])


class OquvchiJavobi(unittest.TestCase):
    def test_masala_yechilmaydi_test_taklif_qilinadi(self):
        r = K.oquvchi_javobi("x^2 - 5x + 6 = 0 kvadrat tenglamani yechib ber", ctx(passport()))
        self.assertEqual(r["niyat"], "masala"); t = matn(r)
        self.assertIn("yechib bermayman", t); self.assertNotRegex(t, r"x\s*=\s*[23]|x1|x2")              # javob (ildizlar) berilmaydi
        self.assertIn("20. Kvadrat tenglamalar", t)
        self.assertEqual(r["amallar"][0]["tur"], "test"); self.assertIn(20, r["amallar"][0]["mavzu"]); self.assertEqual(r["xotira"], {"oxirgi_mavzu": 20})
        r2 = K.oquvchi_javobi("asd 5 + 5 yechib ber", ctx(passport()))
        self.assertEqual(r2["amallar"][0]["tur"], "test")

    def test_pasport_javobi_raqamlar_pasportdan(self):
        r = K.oquvchi_javobi("natijam qanday?", ctx(passport())); self.assertEqual(r["niyat"], "pasport")
        self.assertIn("Birinchi gap.", matn(r)); self.assertEqual(r["amallar"][0]["tur"], "pasport")
        bosh = K.oquvchi_javobi("natijam qanday?", ctx(passport(matematika={**passport()["matematika"], "ko_rilgan": 0}, xalqaro={"sinflar": [], "imtihonlar": [], "sohalar": [], "fikrlash": [], "zaif_mavzular": []})))
        self.assertIn("natija yo‘q", matn(bosh))                     # o'ylab topilgan natija yo'q

    def test_nozik_va_takrorlash(self):
        t = matn(K.oquvchi_javobi("nimani o‘rganay?", ctx(passport())))
        self.assertIn("7. Oddiy kasrlar: 25% (8 savol)", t); self.assertIn("Takrorlash vaqti kelgan", t)
        r = K.oquvchi_javobi("nimani o‘rganay?", ctx(passport())); self.assertEqual(r["amallar"][0], {"tur": "test", "mavzu": [7], "yozuv": "7. Oddiy kasrlar: test"})
        h = matn(K.oquvchi_javobi("nimani unutdim", ctx(passport()))); self.assertIn("1 ta savolni takrorlash vaqti keldi, 6 tasi unutilgan", h); self.assertIn("taxmin", h)
        yoq = K.oquvchi_javobi("nimani o‘rganay", ctx(passport(matematika={**passport()["matematika"], "ko_rilgan": 0}))); self.assertIn("savol yetarli emas", matn(yoq))

    def test_test_tuz(self):
        self.assertEqual(K.oquvchi_javobi("7-mavzuda test ber", ctx(passport()))["amallar"][0]["mavzu"], [7])
        r = K.oquvchi_javobi("test tuz", ctx(passport())); self.assertEqual(r["amallar"][0]["mavzu"], [7])            # mavzu aytilmasa — eng nozik mavzu
        r = K.oquvchi_javobi("test tuz", ctx(passport(matematika={**passport()["matematika"], "nozik": []}))); self.assertEqual(r["amallar"][0]["mavzu"], [])
        r = K.oquvchi_javobi("yana shu mavzuda test", ctx(passport(), xotira={"oxirgi_mavzu": 31})); self.assertEqual(r["amallar"][0]["mavzu"], [31])     # xotira

    def test_mavzu_haqida(self):
        r = K.oquvchi_javobi("oddiy kasrlar haqida", ctx(passport())); t = matn(r)
        self.assertIn("7. Oddiy kasrlar", t); self.assertIn("8 ta savol ko‘rgansiz", t); self.assertIn("25% to‘g‘ri", t); self.assertEqual({a["tur"] for a in r["amallar"]}, {"mavzu", "test"})
        self.assertIn("hali savol yechmagansiz", matn(K.oquvchi_javobi("kvadrat tenglama haqida", ctx(passport()))))

    def test_eslatma_va_formula_va_guruh(self):
        self.assertEqual(K.oquvchi_javobi("eslatmani yoq", ctx(passport()))["xotira"], {"eslatma": True})
        self.assertEqual(K.oquvchi_javobi("eslatmani o‘chir", ctx(passport()))["xotira"], {"eslatma": False})
        self.assertIn("o‘chiq", matn(K.oquvchi_javobi("eslatma nima?", ctx(passport(), xotira={"eslatma": False}))))
        f = K.oquvchi_javobi("formula so‘ra", ctx(passport(), formulalar=["kv_p", "kv_s"])); self.assertEqual(f["amallar"][0], {"tur": "formula", "id": "kv_p", "yozuv": "Formula mashqi"})
        g = matn(K.oquvchi_javobi("guruhim qaysi", ctx(passport()))); self.assertIn("2 (3 ta guruhdan), reyting 488", g); self.assertIn("Karim ustoz", g)
        self.assertIn("qo‘shilmagansiz", matn(K.oquvchi_javobi("guruhim", ctx(passport(xalqaro={"sinflar": [], "imtihonlar": [], "sohalar": [], "fikrlash": [], "zaif_mavzular": []})))))

    def test_nomalum_halol(self):
        r = K.oquvchi_javobi("bugun havo qanday", ctx(passport())); self.assertEqual(r["niyat"], "nomalum"); self.assertIn("tushunmadim", matn(r)); self.assertEqual(r["amallar"], [])
        self.assertTrue(r["takliflar"])


# ───────────────────────── o'qituvchi miyasi ─────────────────────────
def qator(uid, ism, kun=None, ko=0, tg=0, guruh=None, reyting=None, kirish=True):
    return {"user_id": uid, "ism": ism, "oxirgi": (HOZIR - timedelta(days=kun)) if kun is not None else None, "mat_ko": ko, "mat_tg": tg, "guruh": guruh, "reyting": reyting, "kirish_bor": kirish}


JURNAL = [qator(101, "Abdullayev Sardor", 1, 40, 36, 1, 610), qator(102, "Karimova Dilnoza", 12, 25, 8, 2, 430), qator(103, "Valiyev Ali", 0, 30, 24, 1, 560), qator(104, "Valiyeva Zilola", None, 0, 0, None, None, False),
          qator(105, "Yusupov Bobur", 9, 12, 4, 2, 440), qator(106, "Qodirov Aziz", 3, 6, 5, None, None, True)]
SINFLAR = [{"kalit": "xb:7", "id": 7, "nom": "TIMSS 8-A", "tur": "xb", "soni": 6}]


def tctx(sinflar=SINFLAR, jurnal=JURNAL, tanlangan=None, mavzu_stat=None):
    return K.TCtx(MAV, sinflar, lambda kalit: list(jurnal), lambda uid: passport(kim={"user_id": uid, "ism": "x", "sinf": "8", "rol": "oquvchi"}), mavzu_stat or (lambda uids: []), tanlangan, HOZIR)


class OqituvchiNiyati(unittest.TestCase):
    def test_jadval(self):
        for m, k in (("22-o‘quvchi qayerda?", "oquvchi"), ("22 chi oquvchi qanday", "oquvchi"), ("3-talaba", "oquvchi"), ("#103 haqida", "oquvchi"), ("kim eng zaif?", "zaif"), ("qiynalayotganlar", "zaif"),
                     ("kim faol emas", "nofaol"), ("5 kundan beri kirmaganlar", "nofaol"), ("kirish testini kim topshirmagan", "kirish"), ("shubhali natijalar bormi", "tekshiruv"), ("GPT dan foydalanganlar", "tekshiruv"),
                     ("qaysi mavzuda xato ko‘p", "mavzu_xato"), ("sinf holati", "sinf"), ("umumiy hisobot", "sinf"), ("yordam", "yordam"), ("salom", "salom"), ("rahmat", "rahmat"), ("", "bosh"), ("futbol", "nomalum")):
            self.assertEqual(K.niyat_ustoz(m), k, m)

    def test_oquvchi_topish(self):
        q = sorted(JURNAL, key=lambda x: K.normallash(x["ism"]))      # jurnal: ism bo'yicha
        t, n = K.oquvchi_topish("3-o‘quvchi qayerda", q); self.assertEqual((t[0]["ism"], n), (q[2]["ism"], 3))
        self.assertEqual(K.oquvchi_topish("#103", q)[0][0]["ism"], "Valiyev Ali")
        self.assertEqual(K.oquvchi_topish("99-o‘quvchi", q)[0], []); self.assertEqual(K.oquvchi_topish("0-o‘quvchi", q)[0], [])
        self.assertEqual([x["ism"] for x in K.oquvchi_topish("sardor qanday", q)[0]], ["Abdullayev Sardor"])
        self.assertEqual({x["ism"] for x in K.oquvchi_topish("valiyev haqida", q)[0]}, {"Valiyev Ali", "Valiyeva Zilola"})      # noaniq — ikkalasi
        self.assertEqual(K.oquvchi_topish("hech kim", q)[0], [])


class OqituvchiJavobi(unittest.TestCase):
    def test_oquvchi_raqam_bilan(self):
        q = sorted(JURNAL, key=lambda x: K.normallash(x["ism"]))
        r = K.ustoz_javobi("3-o‘quvchi qayerda?", tctx()); t = matn(r)
        self.assertIn(f"3. {q[2]['ism']}", t); self.assertIn("Birinchi gap.", t)      # pasport xulosasi
        self.assertEqual(r["amallar"][0]["user_id"], q[2]["user_id"]); self.assertEqual(r["sinf"]["nom"], "TIMSS 8-A")
        self.assertIn("jurnalida 99-o‘quvchi yo‘q (jami 6", matn(K.ustoz_javobi("99-o‘quvchi qayerda?", tctx())))

    def test_noaniq_ism(self):
        r = K.ustoz_javobi("valiyev haqida", tctx()); self.assertIn("qaysi biri", matn(r)); t = matn(r)
        self.assertIn("Valiyev Ali", t); self.assertIn("Valiyeva Zilola", t); self.assertEqual(r["amallar"], []); self.assertTrue(all("o‘quvchi qayerda" in x for x in r["takliflar"]))

    def test_zaif_halol(self):
        t = matn(K.ustoz_javobi("kim eng zaif?", tctx()))
        self.assertIn("Karimova Dilnoza: 32% (25 savol)", t); self.assertIn("Yusupov Bobur: 33% (12 savol)", t); self.assertIn("65% dan past", t)
        self.assertNotIn("Abdullayev Sardor: 90%", t); self.assertNotIn("Valiyev Ali: 80%", t)        # yaxshi natijalilar «zaif» ro'yxatiga kirmaydi
        yaxshi = [qator(1, "Aaa Bbb", 1, 20, 18, 1, 600), qator(2, "Ccc Ddd", 2, 15, 12, 1, 580)]
        self.assertIn("Zaif o‘quvchi aniqlanmadi", matn(K.ustoz_javobi("kim zaif", tctx(jurnal=yaxshi))))
        self.assertNotIn("Qodirov Aziz", t.split("Xalqaro")[0].split("Matematika")[1] if "Matematika" in t else "")      # 6 savol — hukm chiqarilmaydi
        self.assertIn("2 o‘quvchi bo‘yicha ma’lumot kam", t); self.assertIn("Xalqaro reytingi eng past", t); self.assertIn("reyting 430", t)
        kam = [qator(1, "Aaa Bbb", 1, 3, 3), qator(2, "Ccc Ddd", 2, 5, 1)]
        self.assertIn("ma’lumot yetarli emas", matn(K.ustoz_javobi("kim zaif", tctx(jurnal=kam))))     # hech kimda yetarli savol yo'q — gap uydirilmaydi

    def test_nofaol(self):
        t = matn(K.ustoz_javobi("kim faol emas?", tctx())); self.assertIn("3 ta", t); self.assertIn("Valiyeva Zilola: hali hech narsa yechmagan", t); self.assertIn("12 kun oldin", t); self.assertNotIn("Abdullayev", t.split(":", 1)[1])
        self.assertIn("1 tasi hali hech narsa yechmagan", t)
        t5 = matn(K.ustoz_javobi("3 kundan beri kirmaganlar", tctx())); self.assertIn("Qodirov Aziz", t5)             # aynan 3 kun — kiradi
        self.assertIn("Hamma o‘quvchi", matn(K.ustoz_javobi("kim faol emas", tctx(jurnal=[qator(1, "Aaa Bbb", 1, 3, 3)]))))

    def test_kirish_va_sinf_va_mavzu(self):
        t = matn(K.ustoz_javobi("kirish testini kim topshirmagan", tctx())); self.assertIn("1 ta (jami 6", t); self.assertIn("Valiyeva Zilola", t)
        self.assertIn("faqat xalqaro", matn(K.ustoz_javobi("kirish testi", tctx(sinflar=[{"kalit": "kurs:1", "id": 1, "nom": "Kurs", "tur": "kurs", "soni": 6}]))))
        h = matn(K.ustoz_javobi("sinf holati", tctx())); self.assertIn("6 ta o‘quvchi", h); self.assertIn("Oxirgi 7 kunda faol: 3 ta", h); self.assertIn("kirish testini topshirmagan: 1 ta", h)
        mx = matn(K.ustoz_javobi("qaysi mavzuda xato ko‘p", tctx(mavzu_stat=lambda u: [{"mavzu": 7, "ko": 40, "tg": 10}, {"mavzu": 2, "ko": 50, "tg": 45}, {"mavzu": 31, "ko": 5, "tg": 0}])))
        self.assertIn("7. Oddiy kasrlar: 25% to‘g‘ri (40 javob)", mx); self.assertNotIn("31.", mx)               # 5 ta javob — hisobga olinmaydi
        self.assertIn("yetarli emas", matn(K.ustoz_javobi("qaysi mavzu xato", tctx())))

    def test_sinf_tanlash(self):
        ikki = SINFLAR + [{"kalit": "kurs:3", "id": 3, "nom": "Matematika to‘garagi", "tur": "kurs", "soni": 6}]
        r = K.ustoz_javobi("kim faol emas", tctx(sinflar=ikki)); self.assertIn("Qaysi sinf", matn(r)); self.assertEqual(len(r["tanlov"]), 2); self.assertTrue(all("kim faol emas" in x for x in r["takliflar"]))
        self.assertEqual(K.ustoz_javobi("timss sinfda kim faol emas", tctx(sinflar=ikki))["sinf"]["kalit"], "xb:7")          # nomi aytildi
        self.assertEqual(K.ustoz_javobi("kim faol emas", tctx(sinflar=ikki, tanlangan="kurs:3"))["sinf"]["kalit"], "kurs:3")  # klient tanladi
        self.assertIn("faol sinf yoki guruh topilmadi", matn(K.ustoz_javobi("kim zaif", tctx(sinflar=[]))))
        self.assertIn("yo‘q", matn(K.ustoz_javobi("kim zaif", tctx(jurnal=[]))))

    def test_nomalum_va_yordam(self):
        self.assertIn("tushunmadim", matn(K.ustoz_javobi("futbol", tctx()))); self.assertIn("jurnaldagi tartib raqami", matn(K.ustoz_javobi("yordam", tctx())))


if __name__ == "__main__":
    unittest.main()
