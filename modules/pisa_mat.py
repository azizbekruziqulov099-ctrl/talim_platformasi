"""PISA matematika: mavzular → dars (animatsiyali, qadamma-qadam) + 30 mashq + 30 test (1/2/4 ballik, chizmali, hayotiy).
Savollar generator bilan (seed bo'yicha deterministik); javob va yechim kod bilan hisoblanadi. Natija tarixi va o'zlashtirish foizi saqlanadi."""
import json
import random
from fractions import Fraction
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from modules import pisa_mat_g as G
from modules.mat_mock import ochiq_son

SONI = 30
REJA = [  # barcha mavzularga umumiy: PISA masalasini yechish rejasi
    {"sarlavha": "PISA masalasini 5 qadamda yechamiz", "doska": "1. O‘qi  2. Ma’lumotni ajrat  3. Reja tuz  4. Hisobla  5. Tekshir",
     "ovoz": "PISA masalalari hayotdan olinadi, matni uzun bo‘ladi. Qo‘rqmang! Har qanday masalani beshta qadamda yechamiz. Birinchi — diqqat bilan o‘qiymiz. Ikkinchi — kerakli sonlarni ajratib olamiz. Uchinchi — qanday yechishni rejalashtiramiz. To‘rtinchi — hisoblaymiz. Beshinchi — javob mantiqqa to‘g‘ri keladimi, tekshiramiz."},
]

MAVZULAR = {
    "pisa_foiz": {"nom": "Foiz, chegirma va soliq", "soha": "Miqdor", "belgi": "💯", "maqsad": "Do‘kondagi chegirma, QQS, bank foizi va narx o‘zgarishini hisoblash",
                  "dars": [
                      {"sarlavha": "Foiz — yuzdan bir ulush", "doska": "1% = 1/100\nP ning p% i = P · p / 100\n20% = 0,2   25% = 1/4   50% = 1/2",
                       "ovoz": "Foiz — bu yuzdan bir ulush. Bir foiz — yuzdan bir. Demak, sondan yigirma foiz olish uchun uni nolga ikki, ya’ni nol butun ikki ga ko‘paytiramiz. Yigirma besh foiz — to‘rtdan bir, ellik foiz — yarmi."},
                      {"sarlavha": "Chegirma va oshish", "doska": "Chegirmadan keyin: P · (100 − d) / 100\nOshgandan keyin: P · (100 + p) / 100\nFoiz o‘zgarishi = (yangi − eski) / eski · 100",
                       "ovoz": "Chegirma d foiz bo‘lsa, yangi narx eski narxning yuz minus d foiziga teng. Narx oshsa — yuz plyus p foiz. O‘zgarish necha foiz ekanini topish uchun farqni ESKI narxga bo‘lamiz."},
                      {"sarlavha": "Eng ko‘p uchraydigan tuzoq", "doska": "10% + 10% ≠ 20%!\nIkki chegirma: P · 0,9 · 0,9 = P · 0,81",
                       "ovoz": "Diqqat! Ketma-ket ikki chegirmani qo‘shib bo‘lmaydi. Ikkinchi chegirma yangi, kamaygan narxdan olinadi. O‘n foiz va yana o‘n foiz — yigirma emas, balki o‘n to‘qqiz foiz chegirma beradi."}]},
    "pisa_nisbat": {"nom": "Nisbat, masshtab va o‘lchov birliklari", "soha": "Miqdor", "belgi": "⚖️", "maqsad": "Xarita masshtabi, retsept, aralashma, valyuta va tezlik birliklarini almashtirish",
                    "dars": [
                        {"sarlavha": "Nisbat va proporsiya", "doska": "a : b = 3 : 5  →  jami 8 qism\n1 qism = jami / 8\nTo‘g‘ri proporsionallik: bir necha marta ko‘p → bir necha marta ko‘p",
                         "ovoz": "Nisbat bo‘lak-bo‘laklarga bo‘lishni bildiradi. Uch ga besh nisbatda — jami sakkiz teng qism. Bir qismni topish uchun jami miqdorni sakkizga bo‘lamiz, keyin kerakli qismga ko‘paytiramiz."},
                        {"sarlavha": "Masshtab", "doska": "1 : 50 000 → xaritada 1 sm = haqiqatda 50 000 sm = 500 m\n1 km = 1000 m = 100 000 sm",
                         "ovoz": "Masshtab bir ga ellik ming degani — xaritadagi bir santimetr haqiqatda ellik ming santimetr. Uni metrga, kilometrga o‘tkazishni unutmang: yuz ming santimetr — bir kilometr."},
                        {"sarlavha": "Birliklarni almashtirish", "doska": "km/soat → m/s: ÷ 3,6\nm/s → km/soat: · 3,6\nTeskari proporsionallik: ishchi ↑ → kun ↓",
                         "ovoz": "Soatiga kilometrni sekundiga metrga o‘tkazish uchun uch butun olti ga bo‘lamiz. Ishchilar ko‘paysa, ish kamroq kunda bitadi — bu teskari proporsionallik, ko‘paytma o‘zgarmaydi."}]},
    "pisa_chiziqli": {"nom": "Chiziqli bog‘lanish: tarif, yo‘l, grafik", "soha": "O‘zgarish va bog‘liqlik", "belgi": "📈", "maqsad": "Taksi va mobil tariflari, bak to‘lishi, harorat formulasi, grafikni o‘qish",
                      "dars": [
                          {"sarlavha": "y = kx + b", "doska": "y = k · x + b\nb — boshlang‘ich qiymat (x = 0 da)\nk — har 1 birlikda o‘zgarish (qiyalik)",
                           "ovoz": "Hayotdagi ko‘p bog‘lanishlar to‘g‘ri chiziqli. Formula: y teng k x plyus b. Bu yerda b — boshlang‘ich qiymat, ya’ni x nolga teng bo‘lgandagi y. k esa x bir birlikka oshganda y qancha o‘zgarishini bildiradi."},
                          {"sarlavha": "Grafikni o‘qish", "doska": "Chiziq y o‘qini kesgan joy = b\nChiziq har 1 qadamda k ga ko‘tariladi\nIkki chiziq kesishgan joy — narxlar teng bo‘ladi",
                           "ovoz": "Grafikda avval chiziq y o‘qini qayerda kesishini ko‘ring — bu boshlang‘ich qiymat. Keyin x bir qadam o‘ngga siljiganda chiziq qancha ko‘tarilishini sanang — bu qiyalik. Ikki tarif grafigi kesishgan nuqtada narxlar teng bo‘ladi."},
                          {"sarlavha": "Tenglama tuzish", "doska": "Tarif: a + b · x = T\nx = (T − a) / b\nTeng bo‘lish: a + b₁x = b₂x",
                           "ovoz": "Masalada nimani so‘rashayotganini x deb belgilang, formulaga qo‘ying va tenglamani yeching. Avval abonent to‘lovini ayirib, qolganini bir birlik narxiga bo‘ling."}]},
    "pisa_yuza": {"nom": "Yuza, perimetr, hajm va Pifagor", "soha": "Fazo va shakl", "belgi": "📐", "maqsad": "Xona, bog‘, hovuz, akvarium va narvon masalalarini chizma bo‘yicha yechish",
                  "dars": [
                      {"sarlavha": "Asosiy formulalar", "doska": "To‘rtburchak: S = a·b,  P = 2(a + b)\nDoira: C = πd,  S = πr²\nQutining hajmi: V = a·b·c;  1 dm³ = 1 litr",
                       "ovoz": "To‘rtburchak yuzi — uzunlik ko‘paytirilgan enga, perimetri — ikki marta uzunlik va en yig‘indisi. Doira uzunligi — pi ko‘paytirilgan diametrga, yuzi — pi er kvadrat. Quti hajmi — uch o‘lcham ko‘paytmasi. Bir kub detsimetr — bir litr."},
                      {"sarlavha": "Murakkab shakl — bo‘laklarga", "doska": "L shakl: katta to‘rtburchak − kesilgan qism\nyoki: ikkita to‘rtburchak yig‘indisi",
                       "ovoz": "Murakkab shakl yuzini topish uchun uni oddiy shakllarga bo‘lamiz yoki katta to‘rtburchakdan ortiqcha qismini ayiramiz. Chizmaga har bir o‘lchamni yozib chiqing."},
                      {"sarlavha": "Pifagor teoremasi", "doska": "c² = a² + b²\n3-4-5,  6-8-10,  5-12-13,  8-15-17\nNarvon, devor va yer — to‘g‘ri burchakli uchburchak",
                       "ovoz": "To‘g‘ri burchakli uchburchakda gipotenuza kvadrati katetlar kvadratlari yig‘indisiga teng. Narvon, devor va yer aynan shunday uchburchak hosil qiladi. Uch to‘rt besh va olti sakkiz o‘n kabi uchliklarni yodlab oling."}]},
    "pisa_malumot": {"nom": "Ma’lumot, diagramma va ehtimol", "soha": "Noaniqlik va ma’lumot", "belgi": "📊", "maqsad": "O‘rtacha, mediana, diagramma o‘qish va oddiy ehtimol hisoblash",
                     "dars": [
                         {"sarlavha": "O‘rtacha va mediana", "doska": "O‘rtacha = yig‘indi / soni\nMediana = tartiblangan qatorning o‘rtasi\nOraliq = eng katta − eng kichik",
                          "ovoz": "O‘rtacha — hamma sonlarni qo‘shib, sonlar soniga bo‘lamiz. Mediana — sonlarni tartiblaganda aynan o‘rtada turgan son. Oraliq — eng katta va eng kichik son farqi."},
                         {"sarlavha": "Diagrammani o‘qish", "doska": "1) Sarlavha va o‘qlarni o‘qi\n2) Ustun balandligi = qiymat\n3) Kerakli ustunlarni qo‘sh / ayir",
                          "ovoz": "Diagrammani o‘qishda avval sarlavha va o‘qlarni ko‘ring. Ustun balandligi qiymatni bildiradi. Savolda so‘ralgan ustunlarni topib, qo‘shing yoki ayiring."},
                         {"sarlavha": "Ehtimol", "doska": "P = qulay hollar / barcha hollar\n0 ≤ P ≤ 1\nIkki zar: 36 ta teng imkoniyat",
                          "ovoz": "Ehtimol — qulay hollar sonining barcha mumkin bo‘lgan hollar soniga nisbati. U doim nol bilan bir orasida bo‘ladi. Ikkita zar tashlanganda jami o‘ttiz olti teng imkoniyat bor."}]},
    "pisa_tezlik": {"nom": "Tezlik, masofa va vaqt", "soha": "O‘zgarish va bog‘liqlik", "belgi": "🚗", "maqsad": "Yo‘l, uchrashuv, o‘rtacha tezlik, yoqilg‘i sarfi va harakat grafigi",
                    "dars": [
                        {"sarlavha": "Asosiy formula", "doska": "S = v · t\nv = S / t\nt = S / v\n1 soat = 60 daqiqa",
                         "ovoz": "Masofa tezlik ko‘paytirilgan vaqtga teng. Tezlikni topish uchun masofani vaqtga bo‘lamiz, vaqtni topish uchun masofani tezlikka bo‘lamiz. Soatni daqiqaga o‘tkazishda oltmishga ko‘paytiramiz."},
                        {"sarlavha": "Uchrashuv va o‘rtacha tezlik", "doska": "Qarama-qarshi yurishda: v = v₁ + v₂\nO‘rtacha tezlik = jami yo‘l / jami vaqt\n(tezliklar o‘rtachasi emas!)",
                         "ovoz": "Ikki mashina bir-biriga qarab yursa, tezliklar qo‘shiladi. O‘rtacha tezlik — jami yo‘lni jami vaqtga bo‘lish. Uni tezliklarning o‘rtacha arifmetigi deb o‘ylamang."}]},
    "pisa_geometriya": {"nom": "Geometrik shakllar va o‘xshashlik", "soha": "Fazo va shakl", "belgi": "🔺", "maqsad": "Burchaklar, ko‘pburchaklar, o‘xshash shakllar, uchburchak va trapetsiya yuzi",
                        "dars": [
                            {"sarlavha": "Burchaklar", "doska": "Uchburchak: 180°\nn burchak: (n − 2) · 180°\nTo‘liq aylana: 360°",
                             "ovoz": "Uchburchak burchaklari yig‘indisi yuz sakson gradus. N burchakli ko‘pburchakda — n minus ikki ko‘paytirilgan yuz sakson. To‘liq aylana — uch yuz oltmish gradus."},
                            {"sarlavha": "Yuzalar", "doska": "Uchburchak: S = a · h / 2\nTrapetsiya: S = (a + b) · h / 2\nKattalashtirish k marta → yuz k² marta",
                             "ovoz": "Uchburchak yuzi — asos ko‘paytirilgan balandlikka, ikkiga bo‘lingan. Trapetsiya yuzi — asoslar yig‘indisining yarmi ko‘paytirilgan balandlikka. Shakl k marta kattalashsa, yuzi k kvadrat marta ortadi."},
                            {"sarlavha": "O‘xshashlik: soya masalasi", "doska": "Balandlik / soya = bir xil\nh / s = H / S",
                             "ovoz": "Bir vaqtda tayoq va daraxt soyalari o‘xshash uchburchaklar hosil qiladi. Shuning uchun balandlikning soyaga nisbati ikkalasida bir xil."}]},
    "pisa_ketma": {"nom": "Qonuniyat va ketma-ketlik", "soha": "O‘zgarish va bog‘liqlik", "belgi": "🔢", "maqsad": "Sonlar qonuniyati, har qadamda o‘sish, jamg‘arma va ko‘payish",
                   "dars": [
                       {"sarlavha": "Arifmetik qonuniyat", "doska": "Har qadamda d ga oshadi\nn-had: a + (n − 1) · d\nYig‘indi: n · (birinchi + oxirgi) / 2",
                        "ovoz": "Agar har qadamda son bir xil miqdorga oshsa, n-chi had birinchi had plyus n minus bir ko‘paytirilgan o‘sishga teng. Yig‘indi — birinchi va oxirgi had yig‘indisining yarmi ko‘paytirilgan hadlar soniga."},
                       {"sarlavha": "Ko‘payish (geometrik)", "doska": "Har qadamda k marta: a · kⁿ\n2, 6, 18, 54 …",
                        "ovoz": "Agar har qadamda son bir necha marta ko‘paysa, n-chi qadamda boshlang‘ich son ko‘paytirilgan k ning n-chi darajasiga teng bo‘ladi."}]},
    "pisa_pul": {"nom": "Pul, byudjet va xarid", "soha": "Miqdor", "belgi": "💰", "maqsad": "Qaytim, arzon variantni tanlash, oila byudjeti, muddatli to‘lov, valyuta va foyda",
                 "dars": [
                     {"sarlavha": "Qaysi biri arzon?", "doska": "Birlik narxi = narx / dona soni\nBirlik narxlarni solishtir",
                      "ovoz": "Qaysi qadoq arzonligini bilish uchun har birining bitta donasi narxini topamiz: umumiy narxni dona soniga bo‘lamiz va natijalarni solishtiramiz."},
                     {"sarlavha": "Byudjet va foyda", "doska": "Qism = jami · foiz / 100\nFoyda = sotilgan narx − olingan narx\nMuddatli to‘lov = (narx + ustama) / oylar",
                      "ovoz": "Byudjetning qismi — jami summa ko‘paytirilgan foizga, yuzga bo‘lingan. Foyda — sotish narxi minus sotib olish narxi. Muddatli to‘lovda avval ustamali jami narxni topib, oylar soniga bo‘lamiz."}]},
    "pisa_diagramma": {"nom": "Diagramma va jadvalni tahlil qilish", "soha": "Noaniqlik va ma’lumot", "belgi": "📉", "maqsad": "Doira va chiziqli diagramma, o‘sish, o‘rtacha, mediana va ehtimol",
                       "dars": [
                           {"sarlavha": "Doira diagramma", "doska": "Butun doira = 100%\nQism = jami · foiz / 100\nFoizlar yig‘indisi 100% bo‘ladi",
                            "ovoz": "Doira diagrammada butun doira yuz foiz. Biror toifa nechtaligini topish uchun jami sonni shu toifa foiziga ko‘paytirib, yuzga bo‘lamiz."},
                           {"sarlavha": "Chiziqli diagramma va o‘sish", "doska": "O‘sish = keyingi − oldingi\nEng katta o‘sish — eng tik ko‘tarilgan joy",
                            "ovoz": "Chiziqli diagrammada o‘sishni topish uchun har ikki qo‘shni nuqta farqini hisoblaymiz. Eng tik ko‘tarilgan oraliq eng katta o‘sishni bildiradi."},
                           {"sarlavha": "Ehtimol va qarama-qarshi hodisa", "doska": "P(A) = qulay / barcha\nP(A emas) = 1 − P(A)",
                            "ovoz": "Ehtimol — qulay hollar sonining barcha hollar soniga nisbati. Hodisa yuz bermasligi ehtimoli — bir minus uning yuz berish ehtimoli."}]},
}


_PM_BOLIM = {"pisa_foiz": "PM-MIQ", "pisa_nisbat": "PM-MIQ", "pisa_pul": "PM-MIQ", "pisa_chiziqli": "PM-OZG", "pisa_tezlik": "PM-OZG", "pisa_ketma": "PM-OZG",
              "pisa_yuza": "PM-FAZ", "pisa_geometriya": "PM-FAZ", "pisa_malumot": "PM-NOA", "pisa_diagramma": "PM-NOA"}
for _k, _b in _PM_BOLIM.items():
    MAVZULAR[_k]["bolim"] = _b
    MAVZULAR[_k]["toplam"] = "P_M"

# Qo'shimcha modullar: har biri TEMA = {kod: {...,"bolim","toplam"}} va G.reg bilan shablonlar beradi
for _nom in ("xb_m4", "xb_m8", "xb_pf", "xb_s4", "xb_s8", "xb_ps", "xb_pr", "xb_s4b", "xb_s8b", "xb_psb", "xb_pirls", "xb_pm2", "xb_pm3"):
    try:
        _m = __import__(f"modules.{_nom}", fromlist=["TEMA"])
        MAVZULAR.update(_m.TEMA)
    except Exception:
        pass
try:
    from modules import xb_dars as _xd
    _xd.boyit(MAVZULAR)
except Exception:
    pass


def _rng(mavzu, tur, seed):
    return random.Random(f"{mavzu}|{tur}|{seed}")


def tuz(mavzu, tur, seed):
    """30 ta savol: shablonlar aylanma, dublikat matn qaytarilmaydi."""
    sh = G.SH[mavzu]
    rng = _rng(mavzu, tur, seed)
    out, korildi = [], set()
    tartib = []
    while len(out) < SONI:
        if not tartib:
            tartib = list(range(len(sh)))
            rng.shuffle(tartib)
        f, t = sh[tartib.pop()]
        for _ in range(8):
            q = dict(f(random.Random(rng.random())))
            if q["savol"] + json.dumps(q.get("qismlar", q.get("variantlar")), ensure_ascii=False) not in korildi:
                break
        korildi.add(q["savol"] + json.dumps(q.get("qismlar", q.get("variantlar")), ensure_ascii=False))
        q["ball"] = 1 if q["tur"] == "yopiq" else 2 * len(q["qismlar"])
        q["mavzu"] = mavzu
        out.append(q)
    return out


def korinish(savollar):
    out = []
    for i, q in enumerate(savollar, 1):
        if q["tur"] == "ochiq":
            out.append({"n": i, "tur": "ochiq", "ball": q["ball"], "savol": q["savol"], "rasm": q.get("rasm"), "qismlar": [{"h": x["h"], "savol": x["savol"]} for x in q["qismlar"]]})
        else:
            out.append({"n": i, "tur": "yopiq", "ball": q["ball"], "savol": q["savol"], "rasm": q.get("rasm"), "variantlar": q["variantlar"]})
    return out


def baho_bitta(q, i, javoblar):
    if q["tur"] == "ochiq":
        qis, ball = [], 0
        for z in q["qismlar"]:
            kir = str(javoblar.get(f"{i}{z['h']}", "")).strip()
            v = ochiq_son(kir)
            ok = v is not None and v == Fraction(z["son"])
            ball += 2 if ok else 0
            qis.append({"h": z["h"], "savol": z["savol"], "javob": z["javob"], "kiritildi": kir, "togri": ok})
        return {"n": i, "tur": "ochiq", "ball": q["ball"], "olindi": ball, "savol": q["savol"], "rasm": q.get("rasm"), "qismlar": qis, "yechim": q["yechim"], "togri": ball == q["ball"]}
    tanl = str(javoblar.get(str(i), "")).strip().upper()[:1]
    ok = tanl == q["javob"]
    return {"n": i, "tur": "yopiq", "ball": 1, "olindi": 1 if ok else 0, "savol": q["savol"], "rasm": q.get("rasm"), "variantlar": q["variantlar"], "javob": q["javob"],
            "tanlandi": tanl, "yechim": q["yechim"], "togri": ok}


def baholash(mavzu, tur, seed, javoblar):
    sv = tuz(mavzu, tur, seed)
    tafsilot = [baho_bitta(q, i, javoblar) for i, q in enumerate(sv, 1)]
    maks = sum(x["ball"] for x in tafsilot); ball = sum(x["olindi"] for x in tafsilot)
    return {"mavzu": mavzu, "tur": tur, "seed": seed, "ball": ball, "maks": maks, "foiz": round(100 * ball / maks) if maks else 0,
            "togri": sum(1 for x in tafsilot if x["togri"]), "jami": len(tafsilot), "tafsilot": tafsilot, "daraja": daraja(round(100 * ball / maks) if maks else 0)}


def daraja(f):
    return "A’lo" if f >= 85 else "Yaxshi" if f >= 70 else "Qoniqarli" if f >= 50 else "Qayta o‘rganing"


def dars_tuz(mavzu):
    m = MAVZULAR[mavzu]
    qad = [dict(x, turi="kirish") for x in REJA]
    qad += [dict(x, turi="qoida") for x in m["dars"]]
    # Ishlangan misollar: shablondan, qadamma-qadam
    for k, (f, t) in enumerate(G.SH[mavzu][:3]):
        q = f(random.Random(7 + k))
        satrlar = [x for x in q["yechim"].split("\n") if x.strip()]
        if q["tur"] == "yopiq":
            javob = q["variantlar"][ord(q["javob"]) - 65]
        else:
            javob = "; ".join(z["javob"] for z in q["qismlar"])
        sav = q["savol"] + (" " + " ".join(z["savol"] for z in q["qismlar"]) if q["tur"] == "ochiq" and len(q["qismlar"]) > 1 else "")
        qad.append({"turi": "misol", "sarlavha": f"Ishlangan misol {k + 1}", "savol": q["savol"], "rasm": q.get("rasm"),
                    "doska": "\n".join(satrlar + [f"Javob: {javob}"]), "ovoz": "Misolni qadamma-qadam yechamiz. " + " ".join(satrlar) + f" Javob: {javob.replace('$', '')}."})
    qad.append({"turi": "xulosa", "sarlavha": "Endi o‘zingiz!", "doska": "30 ta mashq → 30 ta test", "ovoz": "Dars tugadi. Endi mashq bo‘limida o‘ttizta masalani yeching, xato qilsangiz yechimini ko‘ring, keyin testni topshiring."})
    return {"mavzu": mavzu, "nom": m["nom"], "maqsad": m["maqsad"], "qadamlar": qad}


class Tekshir1(BaseModel):
    token: Optional[str] = None
    mavzu: str = Field(max_length=40)
    seed: str = Field(max_length=40)
    n: int = Field(ge=1, le=SONI)
    javoblar: dict = Field(default_factory=dict)


class Topshir(BaseModel):
    token: Optional[str] = None
    mavzu: str = Field(max_length=40)
    tur: str = Field(max_length=8)
    seed: str = Field(max_length=40)
    javoblar: dict = Field(default_factory=dict)
    sekund: int = Field(default=0, ge=0, le=20000)


def create_router(platform):
    router = APIRouter(tags=["pisa_mat"])
    holat = {"tayyor": False}

    def uid(token, authorization=None):
        t = token or (authorization or "").replace("Bearer ", "")
        if not t:
            raise HTTPException(401, "Kirish kerak")
        return int(platform._jwt_tekshir(t))

    def run(fn):
        conn = platform._db(); cur = conn.cursor()
        try:
            if not holat["tayyor"]:
                cur.execute("""CREATE TABLE IF NOT EXISTS pisa_mat_urinish (
                    id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, mavzu TEXT NOT NULL, tur TEXT NOT NULL, seed TEXT NOT NULL, ball INT NOT NULL, maks INT NOT NULL,
                    togri INT NOT NULL, sekund INT NOT NULL DEFAULT 0, javoblar TEXT, yaratildi TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE(user_id, mavzu, tur, seed))""")
                cur.execute("CREATE INDEX IF NOT EXISTS pisa_mat_urinish_u ON pisa_mat_urinish(user_id, mavzu, yaratildi DESC)")
                holat["tayyor"] = True
            r = fn(cur); conn.commit(); return r
        finally:
            cur.close(); conn.close()

    def tekshir_nom(mavzu, tur=None):
        if mavzu not in MAVZULAR:
            raise HTTPException(404, "Mavzu topilmadi")
        if tur is not None and tur not in ("mashq", "test"):
            raise HTTPException(400, "tur: mashq yoki test")

    def seed_ok(seed):
        if not seed or not all(c.isalnum() or c == "-" for c in seed):
            raise HTTPException(400, "seed noto'g'ri")

    @router.get("/api/pisamat/mavzular")
    def mavzular(token: str = None, bolim: str = Query("", max_length=20), authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)

        def f(cur):
            cur.execute("""SELECT mavzu, tur, COUNT(*) AS n, MAX(ROUND(100.0*ball/NULLIF(maks,0))) AS eng, 
                                  (ARRAY_AGG(ROUND(100.0*ball/NULLIF(maks,0)) ORDER BY yaratildi DESC))[1] AS oxirgi
                           FROM pisa_mat_urinish WHERE user_id=%s GROUP BY mavzu, tur""", (u,))
            h = {(r["mavzu"], r["tur"]): r for r in cur.fetchall()}
            out = []
            for k, m in MAVZULAR.items():
                if bolim and m.get("bolim") != bolim:
                    continue
                if k not in G.SH:
                    continue
                t, ms = h.get((k, "test")), h.get((k, "mashq"))
                out.append({"kod": k, "bolim": m.get("bolim", ""), "toplam": m.get("toplam", ""), "nom": m["nom"], "soha": m["soha"], "belgi": m["belgi"], "maqsad": m["maqsad"],
                            "test_eng": int(t["eng"]) if t else None, "test_oxirgi": int(t["oxirgi"]) if t else None, "test_soni": int(t["n"]) if t else 0,
                            "mashq_eng": int(ms["eng"]) if ms else None, "mashq_soni": int(ms["n"]) if ms else 0,
                            "ozlashtirish": int(t["eng"]) if t else (int(ms["eng"] * 0.5) if ms else 0)})
            return out
        mv = run(f)
        return {"mavzular": mv, "ozlashtirish": round(sum(x["ozlashtirish"] for x in mv) / len(mv)) if mv else 0}

    @router.get("/api/pisamat/dars/{kod}")
    def dars(kod: str, token: str = None, authorization: Optional[str] = Header(None)):
        uid(token, authorization); tekshir_nom(kod)
        return dars_tuz(kod)

    @router.get("/api/pisamat/set")
    def set_(mavzu: str, tur: str = "test", seed: str = Query(None, max_length=40), token: str = None, authorization: Optional[str] = Header(None)):
        u = uid(token, authorization); tekshir_nom(mavzu, tur)
        seed = seed or f"{u}-{random.SystemRandom().randrange(10 ** 9)}"
        seed_ok(seed)
        return {"seed": seed, "mavzu": mavzu, "tur": tur, "nom": MAVZULAR[mavzu]["nom"], "daqiqa": 45 if tur == "test" else 0, "savollar": korinish(tuz(mavzu, tur, seed))}

    @router.post("/api/pisamat/bitta")
    def bitta(body: Tekshir1, authorization: Optional[str] = Header(None)):
        """Mashq: bitta savol javobini tekshirib, yechimni qaytaradi."""
        uid(body.token, authorization); tekshir_nom(body.mavzu); seed_ok(body.seed)
        sv = tuz(body.mavzu, "mashq", body.seed)
        return baho_bitta(sv[body.n - 1], body.n, {str(k): v for k, v in body.javoblar.items()})

    @router.post("/api/pisamat/topshir")
    def topshir(body: Topshir, authorization: Optional[str] = Header(None)):
        u = uid(body.token, authorization); tekshir_nom(body.mavzu, body.tur); seed_ok(body.seed)
        jav = {str(k): str(v)[:30] for k, v in body.javoblar.items()}
        r = baholash(body.mavzu, body.tur, body.seed, jav)

        def f(cur):
            cur.execute("""INSERT INTO pisa_mat_urinish(user_id, mavzu, tur, seed, ball, maks, togri, sekund, javoblar) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (user_id, mavzu, tur, seed) DO NOTHING RETURNING id""", (u, body.mavzu, body.tur, body.seed, r["ball"], r["maks"], r["togri"], body.sekund, json.dumps(jav)))
            x = cur.fetchone(); r["id"] = int(x["id"]) if x else None; r["qayta"] = x is None
        run(f)
        return r

    @router.get("/api/pisamat/tarix")
    def tarix(mavzu: str, token: str = None, authorization: Optional[str] = Header(None)):
        u = uid(token, authorization); tekshir_nom(mavzu)

        def f(cur):
            cur.execute("SELECT id, tur, ball, maks, togri, sekund, yaratildi FROM pisa_mat_urinish WHERE user_id=%s AND mavzu=%s ORDER BY yaratildi DESC LIMIT 30", (u, mavzu))
            return [{"id": int(r["id"]), "tur": r["tur"], "ball": int(r["ball"]), "maks": int(r["maks"]), "foiz": round(100 * r["ball"] / r["maks"]) if r["maks"] else 0, "togri": int(r["togri"]), "sana": r["yaratildi"].isoformat()} for r in cur.fetchall()]
        return {"tarix": run(f)}

    @router.get("/api/pisamat/natija")
    def natija(id: int, token: str = None, authorization: Optional[str] = Header(None)):
        u = uid(token, authorization)

        def f(cur):
            cur.execute("SELECT mavzu, tur, seed, javoblar FROM pisa_mat_urinish WHERE id=%s AND user_id=%s", (id, u))
            return cur.fetchone()
        row = run(f)
        if not row or row["javoblar"] is None:
            raise HTTPException(404, "Natija topilmadi")
        r = baholash(row["mavzu"], row["tur"], row["seed"], json.loads(row["javoblar"])); r["id"] = id; r["qayta"] = True
        return r

    return router
