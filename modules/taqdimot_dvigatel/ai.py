"""AI miyani to'ldiradi (dizaynga aralashmaydi).

Bir xil ko'rsatma ikki joyda ishlatiladi: saytning o'zidagi AI (Gemini / OpenAI / Groq kaliti bo'yicha) va
o'qituvchi ChatGPT'da ommaviy tayyorlash uchun (korsatma() matnini ChatGPT'ga beradi, javobni saytga yuklaydi).
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
import threading
import time
from urllib import error, request

from . import sxema
from .chizma import CHIZMALAR

ENDPOINTS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
}


def _chizma_royxati():
    qatorlar = []
    for k, (_fn, nom, namuna) in CHIZMALAR.items():
        qatorlar.append(f"- {k} — {nom}: {json.dumps(namuna, ensure_ascii=False)}")
    return "\n".join(qatorlar)


def katalog_matni(mavzu: str = "", fan: str = "", n: int = 90, til: str = "uz") -> str:
    """Kutubxona rasmlari ro'yxati (AI uchun): mavzuga yaqinlari, mavzu bo'lmasa — hammasi fan bo'yicha.
    til — taqdimot tili: rasm nomlari shu tilda beriladi (ruscha/inglizcha nomi bo'lsa)."""
    from . import rasm_tanla, rasmlar
    til = til if til in ("ru", "en") else "uz"
    if mavzu or fan:
        rows = rasm_tanla.katalog(f"{mavzu} {fan}", fan, n, til)
        return "\n".join(f"- {k} — {nom}" for k, nom in rows) or "(mos rasm topilmadi)"
    guruh = {}
    for r in rasmlar.papka_reestri():
        if r.get("tur") == "rasm":
            nom = (r.get(f"nom_{til}") if til != "uz" else "") or r.get("nom") or ""
            guruh.setdefault(r.get("fan") or "Boshqa", []).append(f"{r['kalit']} — {nom}")
    return "\n".join(f"[{f}]\n" + "\n".join("- " + x for x in sorted(v)) for f, v in sorted(guruh.items()))


def korsatma(katalog: bool = False) -> str:
    """AI (yoki ChatGPT) uchun to'liq ko'rsatma. katalog=True — oxiriga barcha kutubxona rasmlari."""
    return _korsatma_asos() + (("\nKUTUBXONA RASMLARI (kalit — nima tasvirlangan):\n" + katalog_matni()) if katalog else "")


def _korsatma_asos() -> str:
    return f"""Sen tajribali o‘qituvchi-metodistsan. Berilgan mavzu bo‘yicha TAQDIMOT MIYASINI yozasan — faqat mazmun,
dizayn emas (ranglar, shrift, animatsiyani dastur o‘zi qiladi; sen faqat har slayd uchun joylashuv kodini tanlaysan).
Javob FAQAT bitta JSON obyekt bo‘lsin, izohsiz.

TIL VA USLUB
- O‘zbek lotin yozuvi: o‘, g‘, ’ belgilari bilan (masalan: «bo‘lak», «ta’rif»). Imlo xatosiz, ilmiy va tushunarli.
- Slayd matni hajmi «MATN HAJMI» va «YOSHGA MOS CHUQURLIK» bandlariga mos bo‘lsin (kichik sinfda qisqa, yuqori sinf va OTMda boy).
  Ortiqcha uzun gapni "izoh" maydoniga yoz (o‘qituvchining og‘zaki matni).
- Muhim so‘z **qalin**, asosiy tushuncha ==rangli== belgilanadi. Formulalar $...$ ichida LaTeX: $\\frac{{a}}{{b}}$, $x^2$, $\\sqrt{{x}}$,
  $\\mathbb{{Z}}$, $a\\in A$, $\\le$, $\\ne$, $\\cdot$. Alohida "formula" maydonida $ belgisisiz LaTeX yoziladi.
- Faktlar aniq bo‘lsin: tarixiy sana, olim nomi, formulalar to‘g‘ri. Bilmasang — yozma.

TUZILMA (kalitlar aynan shunday):
{{
 "sxema": "taqdimot-miya/1",
 "meta": {{"fan","daraja":"maktab|bakalavr|magistr|bogcha","sinf":"5-sinf yoki 2-kurs","raqam":1,"tur":"dars|ma’ruza|amaliy|seminar",
          "mavzu","qisqa","maqsad","tayanch":["3–5 tayanch tushuncha"],"muassasa","kafedra","muallif","davr",
          "belgi":"titul uchun belgi: $\\frac{{3}}{{8}}$ yoki ℤ yoki n!","rasm":"titul rasmi kaliti (ixtiyoriy)","chizma":{{titul uchun chizma (ixtiyoriy)}}}},
 "adabiyotlar": {{"asosiy":[{{"muallif","nomi","nashr"}}],"elektron":[{{"nomi","izoh"}}],"mustaqil":"..."}},   (maktab darsida bo‘sh qoldirish mumkin)
 "takrorlash": {{"mavzu":"o‘tgan mavzu","oyin":"blits|mosini_top","savollar":[{{"savol","javob"}} × 6]}},
 "muammo": {{"sarlavha","masalalar":[{{"sarlavha","matn"}} × 2],"goya","zanjir":["2–4 bosqich"]}},
 "tarix": {{"sarlavha","voqealar":[{{"davr","nom","matn","belgi","rasm"}} × 3–4],"xulosa"}},
 "bolimlar": [  3–5 ta bo‘lim
   {{"nom","izoh","belgi","slaydlar":[  har bo‘limda 2–4 slayd
      {{"sarlavha":"slayd sarlavhasi","izoh":"o‘qituvchi gapi (3–6 jumla)","joylashuv":"kod (pastda)","elementlar":[ 1–3 element ]}}
   ]}}
 ],
 "xatolar": [{{"xato","sabab","togri"}} × 4–6],
 "metodika": {{"sarlavha","bosqichlar":["3 bosqich"],"kartalar":[{{"sarlavha","matn","chizma"}} × 3],"tavsiya"}},
 "xulosa": {{"bilaman":[4],"bilishni_xohlayman":[4],"bilib_oldim":[4]}}  yoki  {{"fikrlar":[4–6]}},
 "test": [{{"savol","variantlar":["3 yoki 4 variant"],"javob":0}} × 6],   javob — to‘g‘ri variant tartib raqami (0 dan)
 "nazorat": ["5–8 savol"], "mustaqil_ish": ["3–4 topshiriq"], "keyingi": {{"mavzu","izoh"}},
 "rasmlar": [{{"kalit","tavsif","prompt"}}],   — miyada ishlatilgan har bir rasm kaliti uchun
 "dars": {{"turi":"yangi bilim berish|mustahkamlash|aralash|amaliy|ma’ruza|seminar","davomiylik":45,
          "maqsadlar":{{"talimiy","tarbiyaviy","rivojlantiruvchi"}},"kompetensiyalar":["2–4 ta"],"natijalar":["o‘quvchi … biladi/qila oladi × 3–4"],
          "metodlar":[{{"nom":"metod nomi (masalan Klaster, Aqliy hujum)","bosqich":"qaysi bosqichda","izoh":"qanday o‘tkaziladi — 1–2 jumla"}} × 2–4],
          "jihozlar":["darslik, tarqatma, proyektor …"],
          "bosqichlar":[{{"nom":"Tashkiliy qism","vaqt":2,"oqituvchi":"o‘qituvchi faoliyati","oquvchi":"o‘quvchi faoliyati","metod"}} × 5–7],
          "fanlararo":["bog‘liq fanlar"],"baholash":"qanday baholanadi","uy_vazifasi":"…"}}
}}
"dars" — DARS REJASI: slaydlarda chiqmaydi, o‘qituvchi va ochiq dars uchun. Bosqichlar vaqti yig‘indisi maktabda 45, OTMda 80 daqiqa;
slaydlardagi faoliyatlar (muammo, test, o‘yin) bosqichlarda aks etsin.

ELEMENT TURLARI ("elementlar" ichida, "tur" maydoni):
- tarif / qoida / teorema: {{"tur","matn","formula"(ixtiyoriy),"chizma"(ixtiyoriy)}}
- formula: {{"tur":"formula","sarlavha","formula","matn":"izohi"}}
- xossalar: {{"tur":"xossalar","sarlavha"(ixt.),"bandlar":[{{"nom","matn","formula"}} × 2–6]}}
- misol / masala: {{"tur","sarlavha","shart","qadamlar":["2–5 qadam"],"javob","chizma"(ixt.)}}
- jadval: {{"tur":"jadval","ustunlar":["..."],"qatorlar":[["..."]] (3–6 qator)}}
- taqqoslash: {{"tur":"taqqoslash","bandlar":[{{"nom","formula","matn","misol"}} × 2–4]}}
- chizma: {{"tur":"chizma","sarlavha","matn","chizma":{{...}},"izoh"}}
- rasm / hayotiy: {{"tur","matn","rasm":"kalit","izoh"}}
- eslatma: {{"tur":"eslatma","sarlavha":"Muhim|Diqqat|Tipik xato","matn"}} (slayd pastida chiziq bo‘lib chiqadi)
- matn: {{"tur":"matn","sarlavha","matn"}}
BARCHA FANLAR UCHUN (shu turlar slaydda YOLG‘IZ turadi, eslatma bilan bo‘lishi mumkin):
- lugat: {{"tur":"lugat","sozlar":[{{"soz","oqilishi","tarjima","misol","rasm"}} × 1–6]}}   — tillar, 1–4-sinf; tarjima bosganda chiqadi
- dialog: {{"tur":"dialog","qatorlar":[{{"kim","matn","tarjima"}} × 2–8]}}   — 2 suhbatdosh, har gap bosish bilan
- parcha: {{"tur":"parcha","sarlavha","matn":"qatorlar \n bilan","muallif","belgilar":["muhim so‘zlar"]}}   — she’r/matn
- vaqt_chizigi: {{"tur":"vaqt_chizigi","voqealar":[{{"sana","nom","matn","rasm"}} × 2–6]}}
- xarita: {{"tur":"xarita","hudud":"ozbekiston|dunyo","belgilash":["Samarqand","Buxoro" yoki davlatlar: "Misr"],
           "joylar":[{{"nom":"Xiva","matn":"qisqa izoh"}} yoki {{"nom":"Qohira","lat":30.04,"lon":31.24}} × 1–8]}}
  (O‘zbekiston shaharlari nomi bilan topiladi; dunyo shaharlari uchun lat/lon yoz)
- tajriba: {{"tur":"tajriba","maqsad","jihozlar":["Probirka","Spirtovka"],"bosqichlar":["2–6 qadam"],"natija","xavfsizlik"}}
- jarayon: {{"tur":"jarayon","shakl":"aylana|zanjir|qadam","sarlavha","bosqichlar":[{{"nom","matn","rasm"}} × 2–6]}}
  (aylana — takrorlanuvchi jarayon; zanjir — ketma-ketlik, oziq zanjiri, algoritm; qadam — rasmli mashq/ish bosqichlari)
- galereya: {{"tur":"galereya","rasmlar":[{{"rasm","izoh"}} × 2–4]}}
- guruhlash: {{"tur":"guruhlash","guruhlar":[{{"nom","bandlar":["2–7 ta"]}} × 2–4]}}
- raqamlar: {{"tur":"raqamlar","bandlar":[{{"raqam":"72%","nom":"qisqa nom","matn":"izoh"}} × 2–4]}}   — statistika, faqat aniq raqamlar
- iqtibos: {{"tur":"iqtibos","matn":"iqtibos","muallif":"L.S. Vygotskiy","manba":"asar, yil","rasm":"portret kaliti (ixt.)"}}
O‘YINLAR (javob bosganda chiqadi):
- moslash: {{"tur":"moslash","juftlar":[{{"chap","ong","rasm"(ixt.)}} × 2–6]}}
- togri_notogri: {{"tur":"togri_notogri","fikrlar":[{{"matn","javob":true|false,"izoh"}} × 2–6]}}
- bosh_joy: {{"tur":"bosh_joy","gaplar":[{{"matn":"I ___ a student.","javob":"am"}} × 2–6]}}
- rasmda_nima: {{"tur":"rasmda_nima","rasm":"kutubxona kaliti","savol","variantlar":["2–4"],"javob":0}}
Bitta slaydda: ko‘pi bilan 3 ta element; jadval/taqqoslash/xossalar va yuqoridagi turlar odatda yolg‘iz yoki eslatma bilan.
Fanga mos turlarni tanla: matematika — formula/misol/chizma; tillar — lugat/dialog/bosh_joy; tarix — vaqt_chizigi/xarita;
geografiya — xarita/jarayon; tabiiy fanlar — tajriba/jarayon/galereya; musiqa va san’at — galereya/guruhlash; har mavzuda 1–3 o‘yin.

JOYLASHUV ("joylashuv" — slayd qanday joylashishi; mazmunga mos kelmasa dastur o‘zi to‘g‘rilaydi):
- rasm_ong / rasm_chap — 1–2 qisqa matn va bitta "rasm" elementi: matn bir tomonda, rasm ikkinchi tomonda
- rasm_panel — 1–2 matn + "rasm": rasm yarim slayd rangli panelda katta (eng ta’sirli; bo‘lim boshlarida yaxshi)
- rasm_katta — bitta qisqa matn + "rasm": rasm juda katta, matn kartada (hayotiy vaziyat, kirish)
- markaz — bitta qisqa ta’rif/qoida/teorema/savol (≤ 300 belgi), rasm va chizmasiz: o‘rtada katta harflar bilan
- ustunlar — 2–3 ta qisqa tarif/qoida/matn yonma-yon (har biri ≤ 200 belgi, "sarlavha" bilan): taqqoslash, 3 xossa
- qatorlar — 2–3 ta matn ketma-ket qatorlarda (bosqichlar, sabablar)
- yon_sarlavha — sarlavha chapdagi ustunda, o‘ngda bitta element (xossalar, misol, jadval emas)
- ustma — qisqa qoida/ta’rif/formula tepada keng tasmada, asosiy element (misol, jadval) ostida
- asosiy_yon — asosiy element (misol, jadval, xossalar) keng, qisqa qoida yoki ta’rif yonida tor ustunda
- qadam_qator — bitta misol/masala, 2–5 qisqa qadam: qadamlar chapdan o‘ngga kartalarda
- chizma_chap — chizmali misol/masala: chizma chapda katta
- rasm_tepa — bitta qisqa matn + "rasm": rasm tepadagi keng rangli tasmada sarlavha bilan
- standart — boshqalari (jadval, taqqoslash, lugat, xarita va boshqa keng elementlar shu bilan)
XOSSALAR ko‘rinishi ("korinish" — ixtiyoriy, mazmunga mosini tanla): kartalar | ikonli (ro‘yxat) | raqamli (2–4 band) |
zinapoya (o‘sish, bosqichlar) | piramida (darajalar, ierarxiya) | vaqt (ketma-ketlik, tarix) | sikl (takrorlanuvchi jarayon) |
strelka (bosqichma-bosqich jarayon) | markaz (bir tushunchaning 4–6 tomoni, o‘rtada doira) | zanjir (3–6 ketma-ket bosqich).
Bilmasang — yozma, dastur o‘zi xilma-xil qiladi.
Bir xil joylashuvni ketma-ket ikki slaydda ishlatma; taqdimotda kamida 4 xil joylashuv bo‘lsin; rasmli slaydlarning
yarmidan ko‘pida rasm_panel yoki rasm_katta bo‘lsin. Bilmasang — "avto".

CHIZMALAR (kod chizadi, rasm kerak emas — iloji bo‘lsa chizma ishlat). Turlar va namunalar:
{_chizma_royxati()}
(ichma_ich: qatlamlar ICHKARIDAN tashqariga; son_oqi: dan < gacha, 20 tadan kam bo‘linma.)

RASMLAR: chizma bilan ko‘rsatib bo‘lmaydigan joyda (tarixiy shaxs, buyum, jonzot, hayotiy vaziyat) "rasm" maydoniga
kalit yoz. AVVAL pastdagi «KUTUBXONA RASMLARI» ro‘yxatidan aynan mos kalitni tanla — ular tayyor va slaydda darhol chiqadi.
Saytda 6000 ga yaqin tayyor rasm bor: lugat so‘zlari, galereya, tajriba jihozlari, moslash juftlari va jarayon bosqichlarida
aniq narsa nomini yozsang ("Olma", "Kolba", "Sigir", "apple") — "rasm" yozmasang ham dastur o‘zi mos rasmni qo‘yadi.
Shuning uchun bunday bandlarda umumiy so‘z emas, aniq narsa nomini yoz.
Rasm alohida "rasm" element bo‘lib slaydning ikkinchi elementi sifatida turadi (matn chapda, rasm o‘ngda) yoki
"hayotiy" element ichida. Mavzuga mos 3–8 rasm ishlat; bitta rasmni ikki marta ishlatma; "meta.rasm" — titul rasmi.
Ro‘yxatda mos rasm bo‘lmasa yangi kalit yoz (kichik lotin harflari, raqam va _), "rasmlar" ro‘yxatiga "tavsif"
(o‘zbekcha) va "prompt" (inglizcha: flat vector illustration, transparent background, soft colors, no text, centered,
educational) bilan qo‘sh — u hozircha chiqmaydi, chizish uchun ro‘yxatga tushadi.

YOSHGA MOSLASH: maktab 1–4-sinf — oddiy so‘zlar, ko‘p chizma va hayotiy misol; 5–11-sinf — qoida, misol, mashq;
bakalavr — ta’rif, isbot g‘oyasi, metodika (boshlang‘ich sinfda qanday o‘rgatiladi).
"""


HAJM = {"qisqa": "QISQA: slaydda 1–2 jumla yoki 3–4 punkt (taxminan 20–40 so‘z); izoh 2–3 jumla.",
        "orta": "O‘RTA: slaydda 2–3 jumla yoki 4–5 punkt (taxminan 40–70 so‘z); izoh 3–5 jumla.",
        "batafsil": "BATAFSIL: slaydda 3–4 jumla yoki 5–6 punkt (taxminan 70–110 so‘z); izoh 5–8 jumla; har tushunchaga misol.",
        "toliq": "TO‘LIQ: slayd mazmunga to‘la — har slaydda 2–3 element (ta’rif + izoh + misol yoki jadval), taxminan 110–160 so‘z; "
                 "nazariya, dalil va misol birga; izoh 6–10 jumla."}
MISOLLAR = {"kam": "MISOLLAR: kam — faqat eng muhim tushunchalarga bittadan misol.",
            "orta": "",
            "kop": "MISOLLAR: ko‘p — har tushunchaga kamida bitta yechimli misol, qo‘shimcha hayotiy misollar va mashqlar."}
QISM_NOMI = {"takrorlash": "takrorlash (o‘tgan mavzu savollari)", "muammo": "muammoli vaziyat", "tarix": "tarixiy ma’lumot",
             "xatolar": "ko‘p uchraydigan xatolar", "metodika": "metodika", "xulosa": "xulosa", "test": "test",
             "yakun": "nazorat savollari, mustaqil ish va keyingi mavzu", "adabiyot": "adabiyotlar"}
TIL = {"uz": "O‘zbek tili (lotin yozuvi)", "ru": "Rus tili (barcha matnlar ruscha; kalitlar o‘zgarmaydi)",
       "en": "Ingliz tili (barcha matnlar inglizcha; kalitlar o‘zgarmaydi)"}
OHANG = {"ilmiy": "ILMIY: aniq atamalar, ta’rif manbasi (muallif, yil), mantiqiy dalil.",
         "oddiy": "ODDIY: tushunarli, hayotiy misollar bilan, ortiqcha atamasiz.",
         "oyinli": "O‘YINLI: qiziqarli savollar, o‘yin slaydlari ko‘p, bolalarga yaqin til."}


# Yoshga mos hajm va chuqurlik: 1-sinf va 11-sinf (yoki magistr) uchun bir xil «yupqa» taqdimot bo'lmasin
YOSH_TAVSIYA = {"bogcha": ("qisqa", 8), "1-2": ("qisqa", 10), "3-4": ("orta", 12), "5-6": ("orta", 14), "7-9": ("batafsil", 16),
                "10-11": ("batafsil", 18), "b1-2": ("toliq", 20), "b3-4": ("toliq", 22), "m": ("toliq", 24)}
YOSH_CHUQURLIK = {
    "bogcha": "BOLALAR BOG‘CHASI: juda sodda so‘zlar, har slaydda bitta fikr va katta rasm, o‘yin va savol ko‘p; uzun matn yo‘q.",
    "1-2": "1–2-SINF: sodda va qisqa gaplar, tanish narsalar (olma, o‘yinchoq, oila), har tushunchaga rasm va o‘yin; atamalar minimal.",
    "3-4": "3–4-SINF: oddiy ta’rif + hayotiy misol + mashq; yangi atama albatta tushuntiriladi; rasmli va o‘yinli slaydlar ko‘p.",
    "5-6": "5–6-SINF: aniq ta’rif va qoida, har qoidaga yechimli misol, taqqoslash yoki jadval; hayot bilan bog‘lash; 1–2 murakkabroq savol.",
    "7-9": ("7–9-SINF: to‘liq ta’riflar, qoidalar va formulalar asoslab beriladi; har tushunchaga bosqichma-bosqich yechilgan misol; "
            "sabab-oqibat, tasnif va taqqoslash jadvallari; tipik xatolar; fanlararo bog‘lanish. Yuzaki, umumiy gaplar yetarli emas."),
    "10-11": ("10–11-SINF (bitiruvchi, imtihon darajasi): mazmun CHUQUR va BOY bo‘lsin — aniq ilmiy ta’riflar, formulalar va ularning "
              "kelib chiqishi yoki isboti, qonuniyatlar, 2–4 qadamli murakkab misol va masalalar (imtihon/sertifikat darajasida), "
              "tasnif va taqqoslash jadvallari, grafik yoki sxema, tipik xatolar, amaliy qo‘llanilishi. Har mazmun slaydida 2–3 element. "
              "Boshlang‘ich sinfga xos sodda, yuzaki taqdimot QAT’IYAN mumkin emas."),
    "b1-2": ("BAKALAVR 1–2-KURS (ma’ruza darajasi): akademik mazmun — ta’riflar manba bilan (muallif, yil), tushunchalar tizimi va tasnifi, "
             "teorema/qonun va isbot yoki asoslash, nazariyalar taqqoslanishi (jadval), olimlar fikri (iqtibos), statistik yoki tadqiqot "
             "ma’lumotlari, amaliy misol va keys, muammoli savollar. Har mazmun slaydida 2–3 element; adabiyotlar kamida 5 ta."),
    "b3-4": ("BAKALAVR 3–4-KURS (mutaxassislik darajasi): chuqur nazariya va uning amaliyoti — ilmiy maktablar va yondashuvlar tahlili, "
             "metodika va texnologiyalar, real keyslar va ularning yechimi, me’yoriy hujjatlar, tadqiqot natijalari (raqamlar), "
             "tanqidiy tahlil va munozarali masalalar. Maktab darsligi darajasidagi umumiy ma’lumot yetarli emas; adabiyotlar kamida 6 ta."),
    "m": ("MAGISTRATURA (ilmiy daraja): muammoning ilmiy holati, nazariy-metodologik asoslar, zamonaviy tadqiqotlar va ularning natijalari "
          "(muallif, yil, raqamlar), tadqiqot metodlari, ilmiy maktablar taqqoslanishi, munozarali va hal qilinmagan masalalar, "
          "o‘z tadqiqoti uchun xulosa va yo‘nalishlar. Har slayd mazmunga to‘la; adabiyotlar kamida 8 ta (jumladan xorijiy manbalar)."),
}
_HAJM_TARTIB = ["qisqa", "orta", "batafsil", "toliq"]


def yosh_band(daraja: str = "", sinf="") -> str:
    """Sinf/kursdan yosh guruhi: bogcha, 1-2 … 10-11, b1-2, b3-4, m. Sinf noma'lum bo'lsa — darajaning o'rtachasi."""
    d = (daraja or "").lower()
    sm = str(sinf or "").lower()
    m = re.search(r"\d+", sm)
    n = int(m.group()) if m else 0
    if d.startswith("mag") or "magistr" in sm:
        return "m"
    if d.startswith(("bak", "otm", "oliy")) or "kurs" in sm:
        return "b3-4" if n >= 3 else "b1-2"
    if d.startswith("bog") or "bog" in sm:
        return "bogcha"
    if not n:
        return "5-6"
    return "1-2" if n <= 2 else "3-4" if n <= 4 else "5-6" if n <= 6 else "7-9" if n <= 9 else "10-11"


def yosh_tavsiya(daraja: str = "", sinf="") -> dict:
    h, n = YOSH_TAVSIYA[yosh_band(daraja, sinf)]
    return {"hajm": h, "slayd_soni": n}


def sozlama_yosh(z: dict | None, daraja: str = "", sinf="") -> dict:
    """Foydalanuvchi hajm yoki slayd sonini bermagan bo'lsa — yoshga mos tavsiya qo'yiladi."""
    z = dict(z) if isinstance(z, dict) else {}
    t = yosh_tavsiya(daraja, sinf)
    if z.get("hajm") not in HAJM:
        z["hajm"] = t["hajm"]
    if not z.get("slayd_soni"):
        z["slayd_soni"] = t["slayd_soni"]
    return z


def sozlama_toza(z: dict | None) -> dict:
    z = z if isinstance(z, dict) else {}
    try:
        n = int(z.get("slayd_soni") or 0)
    except (TypeError, ValueError):
        n = 0
    try:
        ts = int(z.get("test_soni")) if z.get("test_soni") not in (None, "") else None
    except (TypeError, ValueError):
        ts = None
    q = z.get("qismlar") if isinstance(z.get("qismlar"), dict) else {}
    return {"slayd_soni": max(5, min(40, n)) if n else 0,
            "hajm": z.get("hajm") if z.get("hajm") in HAJM else "orta",
            "til": z.get("til") if z.get("til") in TIL else "uz",
            "ohang": z.get("ohang") if z.get("ohang") in OHANG else "",
            "misollar": z.get("misollar") if z.get("misollar") in MISOLLAR else "orta",
            "test_soni": max(0, min(20, ts)) if ts is not None else None,
            "qismlar": {k: False for k in sorted(q) if k in QISM_NOMI and q[k] is False}}


def _sozlama_matni(z: dict, daraja: str = "") -> str:
    z = sozlama_toza(z)
    ohang = z["ohang"] or ("ilmiy" if daraja in ("bakalavr", "magistr") else "oyinli" if daraja == "bogcha" else "oddiy")
    s = f"TIL: {TIL[z['til']]}.\nMATN HAJMI: {HAJM[z['hajm']]}\nOHANG: {OHANG[ohang]}\n"
    if z["til"] != "uz":
        s += _til_buyrugi(z["til"]) + "\n"
    if MISOLLAR[z["misollar"]]:
        s += MISOLLAR[z["misollar"]] + "\n"
    if z["test_soni"] is not None:
        s += (f"TEST: {z['test_soni']} ta savol (har birida 4 variant).\n" if z["test_soni"] else "TEST: yozma (test bo‘sh ro‘yxat).\n")
    if z["qismlar"]:
        s += "YOZMA (foydalanuvchi o‘chirgan qismlar — bo‘sh qoldir): " + ", ".join(QISM_NOMI[k] for k in z["qismlar"]) + ".\n"
    if z["slayd_soni"]:
        b = max(2, min(6, round(z["slayd_soni"] / 5)))
        s += (f"SLAYDLAR SONI: bo‘limlardagi mazmun slaydlari jami {z['slayd_soni']} ta (± 1) — {b} ta bo‘lim, har bo‘limda "
              f"{max(1, min(8, round(z['slayd_soni'] / b)))} tadan ko‘pi bilan 8 ta slayd.\n")
    return s


TIL_NOMI = {"uz": "O‘ZBEK tili (lotin yozuvi)", "ru": "RUS tili", "en": "INGLIZ tili"}


def _til_buyrugi(til: str) -> str:
    return (f"MUHIM — TIL: taqdimotdagi BARCHA matn — meta.mavzu, qisqa, maqsad, tayanch, bo‘lim nomlari, slayd sarlavhalari, "
            f"elementlar matni, izoh (o‘qituvchi gapi), test, xulosa, adabiyot izohlari — faqat {TIL_NOMI[til]}da bo‘lsin. "
            f"Mavzu, fan, reja yoki manba o‘zbekcha berilgan bo‘lsa ham ularni {TIL_NOMI[til]}ga tarjima qilib yoz; "
            f"o‘zbekcha so‘z qoldirma. Faqat JSON kalitlari (\"tur\", \"matn\", ...) va rasm kalitlari o‘zgarmaydi.")


def _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, sozlama=None):
    s = f"MAVZU: {mavzu}\nFAN: {fan}\nDARAJA: {daraja}\nSINF/KURS: {sinf}\nTUR: {tur}\n"
    s += _sozlama_matni(sozlama or {}, daraja)
    s += "YOSHGA MOS CHUQURLIK — " + YOSH_CHUQURLIK[yosh_band(daraja, sinf)] + "\n"
    try:
        from .profil import profil_matni
        s += profil_matni(fan, sinf, daraja) + "\n"
    except Exception:
        pass
    try:
        til_ = (sozlama or {}).get("til") or "uz"
        s += f"\nKUTUBXONA RASMLARI (kalit — nima tasvirlangan; avval shulardan tanla):\n{katalog_matni(f'{mavzu} {qoshimcha}', fan, til=til_)}\n\n"
    except Exception:
        pass
    if qoshimcha:
        s += f"QO‘SHIMCHA TALAB: {qoshimcha}\n"
    if manba:
        s += f"MANBA MATN (shunga tayan, ko‘chirma emas):\n{manba[:12000]}\n"
    z_ = sozlama_toza(sozlama or {})
    if z_["til"] != "uz":
        s += "\n" + _til_buyrugi(z_["til"])
    s += "\nTo‘liq JSON miyani yoz."
    return s


_KALIT_NOMI = {
    "gemini": re.compile(r"^(?:GEMINI_API_KEYS?|GEMINI_KEYS?|GOOGLE_AI_API_KEYS?)(?:_?\d{1,2})?$"),
    "openai": re.compile(r"^OPENAI_API_KEYS?(?:_?\d{1,2})?$"),
    "groq": re.compile(r"^GROQ_API_KEYS?(?:_?\d{1,2})?$"),
}
ZAXIRA_MODEL = {"gemini": "gemini-flash-latest"}   # asosiy model o'chirilgan (404) bo'lsa — Google'ning doimiy taxallusi


def kalitlar(nom: str) -> list:
    """Provayderning barcha kalitlari: GEMINI_API_KEY, GEMINI_API_KEY_2 … (yoki GEMINI_API_KEYS=k1,k2).
    Bitta o'zgaruvchiga vergul/bo'sh joy bilan bir nechta kalit yozilgan bo'lsa ham ajratiladi."""
    andoza = _KALIT_NOMI[nom]
    nomlar = sorted((k for k in os.environ if andoza.match(k)), key=lambda k: (int(re.sub(r"\D", "", k) or 0), k))
    out = []
    for k in nomlar:
        for v in re.split(r"[\s,;]+", os.environ.get(k) or ""):
            if len(v) >= 8 and v not in out:
                out.append(v)
    return out


def _modellar(nom: str) -> list:
    asosiy = {"gemini": os.getenv("TAQDIMOT_GEMINI_MODEL") or os.getenv("PRESENTATION_GEMINI_MODEL") or "gemini-2.5-flash",
              "openai": os.getenv("TAQDIMOT_OPENAI_MODEL") or "gpt-4o-mini",
              "groq": os.getenv("TAQDIMOT_GROQ_MODEL") or "openai/gpt-oss-120b"}[nom]
    out = [m.strip() for m in asosiy.split(",") if m.strip()]
    if ZAXIRA_MODEL.get(nom) and ZAXIRA_MODEL[nom] not in out:
        out.append(ZAXIRA_MODEL[nom])
    return out


def provayderlar():
    """(provayder, kalit, model) — sinash tartibida: har provayderning asosiy modeli barcha kalitlari bilan, so'ng zaxira modeli."""
    order = [x.strip() for x in (os.getenv("TAQDIMOT_AI_PROVIDERS") or os.getenv("PRESENTATION_AI_PROVIDERS") or "gemini,openai,groq").split(",")]
    out = []
    for n in order:
        if n not in _KALIT_NOMI:
            continue
        ks = kalitlar(n)
        for model in _modellar(n):
            out += [(n, k, model) for k in ks]
    return out


def mavjud():
    return bool(provayderlar())


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def _chaqir(nom, kalit, model, system, user, timeout=150):
    body = {"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.6, "response_format": {"type": "json_object"}}
    if nom == "openai":
        body["max_completion_tokens"] = 16000
    else:
        body["max_tokens"] = 16000
    data = json.dumps(body).encode("utf-8")
    req = request.Request(ENDPOINTS[nom], data=data, method="POST",
                          headers={"Content-Type": "application/json", "Authorization": f"Bearer {kalit}"})
    opener = request.build_opener(_NoRedirect)
    with opener.open(req, timeout=timeout) as r:
        raw = r.read(4 * 1024 * 1024)
    env = json.loads(raw.decode("utf-8"))
    text = env["choices"][0]["message"]["content"]
    return text


def json_ajrat(text: str) -> dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("AI javobida JSON topilmadi")
    return json.loads(text[a:b + 1])


# --- kalitlar navbati: limitga yetgan kalit «soviydi», keyingisi ishlaydi --------------------------------------------
_QULF = threading.Lock()
_SOVUQ = {}      # (provayder, kalit, model) → qachongacha (time.monotonic)
_OLIK = {}       # (provayder, model) → qachongacha: model topilmadi (404)
_NAVBAT = [0]    # kalitlar orasida yukni teng bo'lish uchun
_OXIRGI = {}     # (provayder, kalit) → oxirgi xato matni (admin ko'radi)
KUNLIK_SOVUQ = 1800.0
DAQIQA_SOVUQ = 30.0


class AiTugadi(RuntimeError):
    """Barcha kalitlar limitga yetgan yoki AI umuman javob bermayapti — chaqiruvchi o'z bazasidan beradi."""


def _xato_tahlil(exc) -> tuple:
    """HTTP xato → (tur, soviish soniyasi). tur: 'kunlik' | 'daqiqa' | 'kalit' | 'model' | 'band' | 'boshqa'."""
    kod = getattr(exc, "code", None)
    tana = ""
    try:
        tana = exc.read(20000).decode("utf-8", "replace") if hasattr(exc, "read") else ""
    except Exception:
        pass
    if kod == 429:
        if re.search(r"per\s?day|perday|daily|kunlik", tana, re.I):
            return "kunlik", KUNLIK_SOVUQ
        m = re.search(r"retry(?:Delay)?[\"'\s:]+(?:in\s+)?(\d+(?:\.\d+)?)\s*s", tana, re.I)
        return "daqiqa", min(90.0, float(m.group(1)) + 1) if m else DAQIQA_SOVUQ
    if kod in (401, 403) or (kod == 400 and re.search(r"api[ _]?key", tana, re.I)):
        return "kalit", 3600.0
    if kod == 404:
        return "model", 6 * 3600.0
    if kod in (500, 502, 503, 504):
        return "band", 4.0
    return "boshqa", 0.0


def _nomzodlar() -> list:
    """Hozir sinab ko'rsa bo'ladigan (provayder, kalit, model) lar; bir xil darajadagi kalitlar navbat bilan aylanadi."""
    hozir = time.monotonic()
    with _QULF:
        _NAVBAT[0] += 1
        siljish = _NAVBAT[0]
        guruh = {}
        for nom, kalit, model in provayderlar():
            if _OLIK.get((nom, model), 0) > hozir or _SOVUQ.get((nom, kalit, model), 0) > hozir:
                continue
            guruh.setdefault((nom, model), []).append((nom, kalit, model))
    out = []
    for qator in guruh.values():
        k = siljish % len(qator)
        out += qator[k:] + qator[:k]
    return out


def _eng_yaqin_ochilish() -> float:
    """Sovigan kalitlardan eng birinchisi necha soniyadan keyin ochiladi (hech biri sovimagan bo'lsa 0)."""
    hozir = time.monotonic()
    with _QULF:
        v = [u - hozir for (nom, kalit, model), u in _SOVUQ.items() if u > hozir and _OLIK.get((nom, model), 0) <= hozir]
    return min(v) if v else 0.0


def kalitlar_holati() -> dict:
    """Admin uchun: nechta kalit bor, qaysi biri hozir limitda (kalitning faqat oxirgi 4 belgisi ko'rinadi)."""
    hozir = time.monotonic()
    out = []
    with _QULF:
        for nom in _KALIT_NOMI:
            modellar = _modellar(nom)
            for k in kalitlar(nom):
                dam = max([_SOVUQ.get((nom, k, m), 0) - hozir for m in modellar[:1]] + [0])
                out.append({"provayder": nom, "kalit": "…" + k[-4:], "model": modellar[0], "ishlayapti": dam <= 0,
                            "dam": int(dam), "xato": _OXIRGI.get((nom, k), "")})
        olik = [f"{n}: {m}" for (n, m), u in _OLIK.items() if u > hozir]
    return {"kalitlar": out, "ishlayotgan": sum(1 for x in out if x["ishlayapti"]), "topilmagan_modellar": olik}


def tugaganmi() -> bool:
    """Kalit bor, lekin hammasi hozir limitda (yoki umuman kalit yo'q)."""
    return not _nomzodlar()


def _bir_chaqiruv(system, user, deadline, t0):
    """Kalit va provayderlarni navbat bilan sinaydi, JSON obyekt qaytaradi. Limitga yetgan kalit vaqtincha chetlatiladi;
    daqiqalik limit bo'lsa qisqa kutib qayta uriniladi. Hech biri javob bermasa — AiTugadi."""
    oxirgi, kutildi = None, 0
    while True:
        nomzodlar = _nomzodlar()
        for nom, kalit, model in nomzodlar:
            left = deadline - (time.monotonic() - t0)
            if left < 15:
                break
            try:
                raw = _chaqir(nom, kalit, model, system, user, timeout=min(150, left))
                out = json_ajrat(raw)
                out.setdefault("_ai", {"provayder": nom, "model": model})
                with _QULF:
                    _OXIRGI.pop((nom, kalit), None)
                return out
            except (error.URLError, error.HTTPError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
                oxirgi = exc
                tur, dam = _xato_tahlil(exc)
                with _QULF:
                    if tur == "model":
                        _OLIK[(nom, model)] = time.monotonic() + dam
                    elif dam > 0:
                        _SOVUQ[(nom, kalit, model)] = time.monotonic() + dam
                    if tur != "boshqa":
                        _OXIRGI[(nom, kalit)] = {"kunlik": "kunlik limit tugadi", "daqiqa": "daqiqalik limit", "kalit": "kalit yaroqsiz yoki ruxsat yo‘q",
                                                 "model": f"model topilmadi: {model}", "band": "server band"}[tur]
                continue
        left = deadline - (time.monotonic() - t0)
        dam = _eng_yaqin_ochilish()
        if kutildi < 3 and 0 < dam <= 45 and left > dam + 25:   # daqiqalik limit — biroz kutamiz
            kutildi += 1
            time.sleep(dam + 0.5)
            continue
        if not nomzodlar and kutildi == 0 and oxirgi is None:
            raise AiTugadi("AI limiti tugadi: barcha kalitlar band")
        break
    raise AiTugadi(f"AI javob bermadi: {type(oxirgi).__name__ if oxirgi else 'vaqt tugadi'}")


REJA_KORSATMA = """Sen tajribali metodistsan. Mavzu bo‘yicha taqdimot REJASINI tuzasan — faqat tuzilma, to‘liq matn emas.
Javob FAQAT JSON:
{"meta":{"mavzu","qisqa":"2–4 so‘z","maqsad":"1–2 jumla","tayanch":["3–5 tushuncha"]},
 "bolimlar":[{"nom":"bo‘lim nomi","izoh":"1 jumla","slaydlar":[{"sarlavha":"slayd sarlavhasi","maqsad":"bu slaydda nima — 1 jumla",
   "tur":"eng mos element turi: tarif|qoida|misol|masala|jadval|taqqoslash|xossalar|lugat|dialog|parcha|vaqt_chizigi|xarita|tajriba|jarayon|galereya|guruhlash|moslash|togri_notogri|bosh_joy|rasmda_nima|raqamlar|iqtibos|rasm|matn"}]}]}
Bo‘limlar mantiqiy ketma-ket: kirish → asosiy tushunchalar → qo‘llash/misollar → mustahkamlash. Sarlavhalar aniq va qisqa (2–7 so‘z),
takrorlanmasin. Fanga va yoshga mos turlarni tanla, har bo‘limda kamida bitta vizual yoki o‘yin turi bo‘lsin.
Bakalavr/magistr: olimlar fikri uchun iqtibos, tadqiqot natijalari uchun raqamlar, nazariyalar uchun taqqoslash ham bo‘lsin."""


def reja_yoz(mavzu, fan="", daraja="maktab", sinf="", tur="dars", qoshimcha="", manba="", sozlama=None, deadline=120.0):
    if not provayderlar():
        raise RuntimeError("AI kaliti sozlanmagan (GEMINI_API_KEY, OPENAI_API_KEY yoki GROQ_API_KEY).")
    z = sozlama_toza(sozlama_yosh(sozlama, daraja, sinf))
    from .profil import profil_matni
    user = _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, z).replace("To‘liq JSON miyani yoz.", "Faqat REJA JSON'ini yoz.")
    t0 = time.monotonic()
    out = reja_toza(_bir_chaqiruv(REJA_KORSATMA + "\n" + profil_matni(fan, sinf, daraja), user, deadline, t0), mavzu)
    if z["til"] != "uz":
        til_tekshir(out, z["til"], deadline + 30, t0)
    return out


def reja_toza(r: dict, mavzu: str = "") -> dict:
    """Reja (AI yoki o'qituvchi tahrirlagan) — xavfsiz shaklga."""
    t = sxema.t
    meta = r.get("meta") if isinstance(r.get("meta"), dict) else {}
    bol = []
    for b in (r.get("bolimlar") or [])[:6]:
        if not isinstance(b, dict) or not t(b.get("nom")):
            continue
        sl = []
        for x in (b.get("slaydlar") or [])[:8]:
            if isinstance(x, str):
                x = {"sarlavha": x}
            if isinstance(x, dict) and t(x.get("sarlavha")):
                sl.append({"sarlavha": t(x.get("sarlavha"), 110), "maqsad": t(x.get("maqsad"), 240), "tur": t(x.get("tur"), 30)})
        if sl:
            bol.append({"nom": t(b.get("nom"), 60), "izoh": t(b.get("izoh"), 160), "slaydlar": sl})
    if not bol:
        raise RuntimeError("Reja bo‘sh chiqdi — qayta urinib ko‘ring")
    return {"reja": True, "meta": {"mavzu": t(meta.get("mavzu"), 160) or mavzu, "qisqa": t(meta.get("qisqa"), 60),
                                   "maqsad": t(meta.get("maqsad"), 400), "tayanch": sxema.ls(meta.get("tayanch"), 6, 60)},
            "bolimlar": bol}


def _reja_matni(reja: dict) -> str:
    q = [f"MAVZU: {reja['meta'].get('mavzu')}"]
    for i, b in enumerate(reja["bolimlar"]):
        q.append(f"{i + 1}-bo‘lim: {b['nom']}" + (f" — {b['izoh']}" if b.get("izoh") else ""))
        for sl in b["slaydlar"]:
            q.append(f"   • {sl['sarlavha']}" + (f" [{sl['tur']}]" if sl.get("tur") else "") + (f" — {sl['maqsad']}" if sl.get("maqsad") else ""))
    return "\n".join(q)


_UZ_BELGI = re.compile(r"[oOgG][‘’'ʻʼ`][a-z]|\b(va|bilan|uchun|haqida|hamda|yoki|qanday|nima|emas|lekin|kerak|bo['‘’ʻ]?(l|yicha)\w*|"
                       r"\w+(lari|larni|larga|larda|lardan|larning|dagi|imiz|ingiz|sining))\b", re.I)
_KIRILL = re.compile(r"[А-Яа-яЁё]")
_LOTIN = re.compile(r"[A-Za-z]")
_MATN_KALITLAR = {"mavzu", "qisqa", "maqsad", "nom", "izoh", "sarlavha", "matn", "shart", "javob", "savol", "goya", "tavsiya", "xato",
                  "sabab", "togri", "nomi", "davr", "natija", "xavfsizlik", "muassasa", "kafedra", "belgi", "mustaqil", "xulosa"}
# chizma ichidagi yozuvlar (son o'qidagi «3 birlik», tasmadagi «150 bet», to'plam nomlari): ruscha taqdimotda o'zbekcha qolmasin
_CHIZMA_MATN = {"nom", "nomlar", "jami", "bolak_nomi", "boyalgan_nomi", "ichida", "darajalar", "umumiy", "natija", "elementlar", "misol",
                "sarlavha", "izoh", "yorliq", "belgilar", "qatlamlar", "toplamlar", "sakrashlar", "nuqtalar", "kesmalar", "x_nomi", "y_nomi"}
_CHIZMA_TEGMA = {"tur", "shakl", "turi", "funksiya", "tenglama", "rang", "amal", "kalit"}
_ROYXAT_KALITLAR = {"variantlar", "qadamlar", "tayanch", "bandlar", "fikrlar", "bilaman", "bilishni_xohlayman", "bilib_oldim",
                    "nazorat", "mustaqil_ish", "zanjir", "bosqichlar", "jihozlar", "ustunlar", "qatorlar", "gaplar"}
_TIL_OTKAZ_TUR = {"lugat", "dialog", "bosh_joy"}      # til darslari: so'z va tarjima ataylab ikki tilda
_TIL_OTKAZ_KALIT = {"rasm", "rasmlar", "tur", "kalit", "formula", "joylashuv", "chizma", "_ai", "prompt", "muallif", "manba",
                    "raqam", "nashr", "til", "daraja", "sinf", "fan", "reja"}


_MAT_SOZ = {"sin", "cos", "tan", "tg", "ctg", "cot", "log", "lim", "max", "min", "sup", "inf", "mod", "gcd", "lcm", "const", "exp",
            "det", "arcsin", "arccos", "arctg", "deg", "rad", "km", "kg", "mm"}
_UZ_QISQA = {"yil", "hajm", "zich", "oqim", "dan", "ham", "emas", "yoki", "bilan", "uchun", "kun", "ha", "yo'q", "yo‘q", "uchta",
             "ikkita", "nechta", "son", "bor", "yana", "teng", "deb", "agar", "keyin", "avval", "ni", "chunki", "masalan", "ammo",
             "lekin", "umumiy", "toping", "hisoblang", "yozing", "javob", "misol", "qoida", "ta'rif", "xulosa", "maxraj", "surat"}
_UZ_OXIR = ("lar", "lari", "larni", "ning", "dagi", "dan", "ga", "da", "ni", "lik", "ish", "gan", "moq", "chi", "siz", "sini", "imiz",
            "adi", "ydi", "ladi", "mi", "ing")
_EN_SOZ = {"the", "of", "and", "in", "with", "is", "are", "to", "for", "on", "by", "from", "how", "what", "its", "an", "a", "or", "this",
           "that", "be", "it", "as", "at", "we", "you", "they", "has", "have", "was", "were", "can", "not", "if", "then", "each"}


@lru_cache(maxsize=1)
def _uz_sozlar() -> frozenset:
    """Loyihaning o'zbekcha matnlaridan yig'ilgan so'zlar (malumot/uz_sozlar.txt.gz): «daraja», «masofa», «ayirma»."""
    import gzip
    import os
    try:
        with gzip.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "malumot", "uz_sozlar.txt.gz"), "rt",
                       encoding="utf-8") as f:
            return frozenset(x.strip() for x in f if x.strip())
    except OSError:
        return frozenset()


def _boshqa_tilda(s: str, til: str) -> bool:
    toza = re.sub(r"\$[^$]*\$", " ", s or "")
    lat, cyr = len(_LOTIN.findall(toza)), len(_KIRILL.findall(toza))
    if til == "ru":
        # bitta qisqa so'z ham («Yo‘q», «Hajm», «Xiva») — lotincha so'z (katta harfli qisqartma va matematik belgi emas)
        sozlar = [w for w in re.findall(r"[A-Za-z‘’'ʻ]{3,}", toza) if not w.isupper() and w.lower() not in _MAT_SOZ]
        return (bool(sozlar) or bool(re.search(r"\b(va|ham|yoki)\b", toza))) and lat > cyr * 2
    if til == "en":
        if cyr >= 4 or _UZ_BELGI.search(toza):
            return True
        # o'zbekcha belgili so'zlar (q, o‘/g‘, xa/xo, -lar/-dan/-ish/-gan…) inglizcha belgililardan (the, of, w, th, -tion…) ko'p
        uz = en = 0
        for w in re.findall(r"[A-Za-z‘’'ʻ]{2,}", toza):   # bitta harf (formuladagi a, c, x) hisobga olinmaydi
            lw = w.lower()
            if (lw in _UZ_QISQA or re.search(r"q(?!u)|[og][‘’'ʻ]", lw) or re.sub("[‘’ʻ]", "'", lw).strip("'") in _uz_sozlar()
                    or (len(lw) >= 5 and lw.endswith(_UZ_OXIR) and not lw.endswith(("ular", "olar", "ilar", "glish", "inish")))):
                uz += 1
            if lw in _EN_SOZ or (len(lw) >= 3 and re.search(r"w|th|ph|c(?!h)|tion$|ly$|ous$|ness$", lw)):
                en += 1
        return uz > en
    return cyr >= 6 and cyr > lat  # o'zbekcha taqdimotda ruscha qolgan gap


def _uz_ball(matnlar) -> float:
    """O'zbekcha belgilari (o‘, g‘, q, -lar…) ko'pmi — inglizcha belgilar (w, th, c…) ayirilgan o'rtacha ball."""
    jami = 0.0
    for x in matnlar:
        x = x or ""
        uz = len(_UZ_BELGI.findall(x)) + len(re.findall(r"q(?!u)|[oOgG][‘’'ʻ]", x))
        en = len(re.findall(r"w|th|ph|c(?!h)|\b(the|of|and|is|are)\b", x, re.I))
        jami += uz - en
    return jami / max(1, len(matnlar))


def _chizma_matnlar(obj, til, yol, out, yozuv=False):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k not in _CHIZMA_TEGMA:
                _chizma_matnlar(v, til, yol + (k,), out, k in _CHIZMA_MATN)
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            _chizma_matnlar(x, til, yol + (i,), out, yozuv)
    elif isinstance(obj, str) and yozuv and _boshqa_tilda(obj, til):
        out.append((yol, obj))
    return out


def _qosh(out, yol, v, til):
    if isinstance(v, str) and v.strip() and _boshqa_tilda(v, til):
        out.append((yol, v))


def _til_darsimi(m) -> bool:
    """Chet tili darsi (ingliz, rus, nemis…): o'rganilayotgan tildagi so'z va gaplar ataylab o'sha tilda qoladi."""
    try:
        from . import rasm_tanla
        fan = ((m.get("meta") or {}).get("fan") or "") if isinstance(m, dict) else ""
        return "tillar" in rasm_tanla._fan_guruh(fan)
    except Exception:
        return False


def _element_matnlari(obj, til, yol, out, til_darsi) -> bool:
    """Maxsus elementlar. True — element to'liq ko'rildi (umumiy yurish kerak emas)."""
    tur = obj.get("tur")
    if tur in _TIL_OTKAZ_TUR:
        # lug'at so'zi, misol gap va dialog qatori ataylab o'rganilayotgan tilda — tegilmaydi;
        # faqat ona tilidagi tarjima taqdimot tiliga: «apple — olma» → «apple — яблоко»
        for maydon in ("sozlar", "qatorlar"):
            for i, x in enumerate(obj.get(maydon) or []):
                if isinstance(x, dict):
                    _qosh(out, yol + (maydon, i, "tarjima"), x.get("tarjima"), til)
        if not til_darsi:   # «bo'sh joyni to'ldir» boshqa fanlarda — oddiy gap
            for i, x in enumerate(obj.get("gaplar") or []):
                if isinstance(x, dict):
                    for k in ("matn", "javob"):
                        _qosh(out, yol + ("gaplar", i, k), x.get(k), til)
        return True
    if tur == "moslash" and isinstance(obj.get("juftlar"), list):
        js = [x for x in obj["juftlar"] if isinstance(x, dict)]
        chap, ong = _uz_ball([x.get("chap") for x in js]), _uz_ball([x.get("ong") for x in js])
        # o'zbekcha tomon tarjima qilinadi; til darsida ikkinchi (o'rganilayotgan) tomon tegilmaydi
        tomonlar = ["chap", "ong"] if not til_darsi or (chap > 0 and ong > 0) else (["chap"] if chap >= ong else ["ong"])
        if not til_darsi and chap <= 0 and ong <= 0:
            tomonlar = ["chap", "ong"]
        for i, x in enumerate(obj["juftlar"]):
            if isinstance(x, dict):
                for k in tomonlar:
                    _qosh(out, yol + ("juftlar", i, k), x.get(k), til)
        return True
    if tur == "galereya":
        for i, x in enumerate(obj.get("rasmlar") or []):
            if isinstance(x, dict):
                _qosh(out, yol + ("rasmlar", i, "izoh"), x.get("izoh"), til)
        return True
    if tur == "xarita":
        # joy nomi xaritadagi nuqtani topish uchun o'zgarmaydi — tarjimasi «yorliq»da ko'rinadi
        for i, x in enumerate(obj.get("joylar") or []):
            if isinstance(x, dict):
                if not x.get("yorliq"):
                    _qosh(out, yol + ("joylar", i, "yorliq"), x.get("nom"), til)
                _qosh(out, yol + ("joylar", i, "matn"), x.get("matn"), til)
        return True
    if tur in ("iqtibos", "parcha"):
        for k in ("muallif", "manba"):
            _qosh(out, yol + (k,), obj.get(k), til)
        for i, x in enumerate(obj.get("belgilar") or []):   # she'rdagi ajratilgan so'zlar — tarjima qilingan matnga mos
            _qosh(out, yol + ("belgilar", i), x, til)
    return False


def _matnlar(obj, til, yol=(), out=None, til_darsi=None):
    """Tarjima kerak bo'lgan satrlar: (yo'l, matn)."""
    out = [] if out is None else out
    if til_darsi is None:
        til_darsi = _til_darsimi(obj)
    if isinstance(obj, dict):
        if isinstance(obj.get("chizma"), dict):
            _chizma_matnlar(obj["chizma"], til, yol + ("chizma",), out)
        if obj.get("tur") and _element_matnlari(obj, til, yol, out, til_darsi):
            for k in ("sarlavha", "izoh", "savol", "matn"):   # element sarlavhasi va izohi — oddiy matn
                if k == "matn" and obj.get("tur") in _TIL_OTKAZ_TUR:
                    continue
                if isinstance(obj.get(k), str) and _boshqa_tilda(obj[k], til):
                    out.append((yol + (k,), obj[k]))
            return out
        if isinstance(obj.get("chap"), str) and isinstance(obj.get("ong"), str):
            # moslash jufti: ikkala tomoni ham boshqa tilda bo'lsagina (til darsidagi «apple — olma» juftiga tegilmaydi)
            if _boshqa_tilda(obj["chap"], til) and _boshqa_tilda(obj["ong"], til):
                out += [(yol + ("chap",), obj["chap"]), (yol + ("ong",), obj["ong"])]
        for k, v in obj.items():
            if k in _TIL_OTKAZ_KALIT:
                continue
            if isinstance(v, str):
                if k in _MATN_KALITLAR and _boshqa_tilda(v, til):
                    out.append((yol + (k,), v))
            elif isinstance(v, list) and k in _ROYXAT_KALITLAR:
                for i, x in enumerate(v):
                    if isinstance(x, str):
                        if _boshqa_tilda(x, til):
                            out.append((yol + (k, i), x))
                    elif isinstance(x, list):
                        for j, y in enumerate(x):
                            if isinstance(y, str) and _boshqa_tilda(y, til):
                                out.append((yol + (k, i, j), y))
                    else:
                        _matnlar(x, til, yol + (k, i), out, til_darsi)
            elif isinstance(v, (dict, list)):
                _matnlar(v, til, yol + (k,), out, til_darsi)
    elif isinstance(obj, list):
        for i, x in enumerate(obj):
            _matnlar(x, til, yol + (i,), out, til_darsi)
    return out


def til_tekshir(m: dict, til: str, deadline: float = 60.0, t0: float | None = None) -> int:
    """Natijada tanlangan tildan boshqa tilda qolgan matnlarni (masalan, ruscha taqdimotdagi o'zbekcha sarlavhalar)
    bitta-ikkita qo'shimcha AI chaqiruvi bilan tarjima qiladi. Qaytaradi: tarjima qilingan satrlar soni."""
    if til not in TIL_NOMI:
        return 0
    t0 = time.monotonic() if t0 is None else t0
    royxat = _matnlar(m, til)
    # fan nomi: «fan» o'zgarmaydi (rasm, bezak, metodlar uni o'zbekcha kutadi) — titulda «fan_nomi» ko'rinadi
    mt = m.get("meta") if isinstance(m.get("meta"), dict) else {}
    fan = mt.get("fan") or ""
    if fan and not mt.get("fan_nomi"):
        from . import tarjima
        tr = tarjima.tarjimon(til)
        tayyor = tr(fan) if tr else fan
        if tayyor != fan and not _boshqa_tilda(tayyor, til):
            mt["fan_nomi"] = tayyor
        elif _boshqa_tilda(fan, til):
            mt["fan_nomi"] = fan
            royxat.insert(0, (("meta", "fan_nomi"), fan))
    if not royxat:
        return 0
    system = (f"Sen tarjimonsan. Berilgan JSON obyektidagi har bir qiymatni {TIL_NOMI[til]}GA tarjima qil. Ma’noni, **qalin** va "
              f"==ajratilgan== belgilarini, $...$ formulalarni, raqamlar va xususiy nomlarni saqla. Javob — xuddi shu kalitlar bilan "
              f"FAQAT JSON obyekt.")
    soni = 0
    for bosh in range(0, min(len(royxat), 240), 80):
        qism = royxat[bosh:bosh + 80]
        if deadline - (time.monotonic() - t0) < 20:
            break
        try:
            javob = _bir_chaqiruv(system, json.dumps({str(i): s for i, (_, s) in enumerate(qism)}, ensure_ascii=False), deadline, t0)
        except Exception:
            break
        for i, (yol, _) in enumerate(qism):
            yangi = javob.get(str(i))
            if not isinstance(yangi, str) or not yangi.strip():
                continue
            o = m
            for p in yol[:-1]:
                o = o[p]
            o[yol[-1]] = yangi.strip()
            soni += 1
    return soni


MASALLIQ_KORSATMA = """Sen tajribali metodistsan. Mavzu bo‘yicha OCHIQ DARS MASALLIQLARINI tayyorlaysan — o‘qituvchi ulardan turli
interfaol metodlar (domino, blits, mozaika, «ha-yo‘q», keys, debat, klaster, Venn, o‘yinlar) uchun foydalanadi. Faktlar aniq,
sinf yoshiga mos, o‘zbek tilida (lotin), imlo xatosiz. Javob FAQAT JSON:
{"atamalar":[{"atama","tarif":"1 jumla"}] × 6–8,
 "bayonotlar":[{"matn","togri":true|false,"izoh":"nega"}] × 8 (yarmi noto‘g‘ri — tipik xato tasavvurlar),
 "savollar":[{"savol","javob":"qisqa, 1–5 so‘z"}] × 10 (blits va o‘yinlar uchun, oddiydan murakkabga),
 "qismlar":[{"nom","matn":"4–6 jumla — mavzuning shu qismi","savol":"qism bo‘yicha tekshiruv savoli"}] × 4 (mavzu 4 teng qismga; mozaika va stansiyalar uchun),
 "muammoli_savol":"darsni boshlaydigan hayotiy, qiziqarli muammo",
 "keys":{"vaziyat":"real hayotiy vaziyat 3–5 jumla","savollar":["2–3 savol"]},
 "tezis":"munozarali tezis (debat uchun; bahsli bo‘lsin)",
 "taqqoslash":{"a","b","umumiy":[2–3],"a_farq":[2–3],"b_farq":[2–3]} (mavzudagi ikki tushuncha),
 "klaster":{"markaz","shoxlar":[{"nom","bandlar":[2–3]}] × 4},
 "topishmoq":{"matn","javob"} (kichik sinflar uchun ayniqsa),
 "hikmat":"mavzuga yoki bilimga oid maqol yoki hikmat (aniq mavjud bo‘lgan)",
 "kalit_soz":"mavzuning bitta kalit so‘zi (5–10 harf, o‘yin uchun)",
 "xato_yechim":{"shart","xato":"atayin xato yechim yoki gap","togri","sabab"},
 "guruh_nomlari":["mavzu tushunchalaridan 4 ta guruh nomi"],
 "hayotiy_topshiriq":{"nom","topshiriq":"STEAM yoki amaliy, 10–15 daqiqalik guruh ishi"},
 "tajriba":{"nom","jihozlar":[],"bosqichlar":[],"kuzatish","xavfsizlik"} (faqat tajriba qilish mumkin bo‘lgan mavzuda, aks holda bo‘sh),
 "vazifalar":{"A":"asosiy daraja uy vazifasi","B":"qo‘llash darajasi","C":"ijodiy daraja"},
 "sinkveyn":["5 qator: ot; 2 sifat; 3 fe’l; 4 so‘zli gap; 1 so‘z"],
 "jamoaviy_masala":{"shart":"bitta katta masala","qismlar":["4 qism — har guruhga bittadan"],"yakun":"qismlar natijasidan yakuniy javob"} (aniq fanlarda; boshqa fanlarda umumiy loyiha qismlari)}"""


DARS_MAZMUNI_KORSATMA = """Sen fan bo‘yicha eng kuchli o‘qituvchi va metodistsan. Mavzu bo‘yicha DARSNING O‘ZINI — o‘qituvchi sinfda nimani,
qanday ketma-ketlikda o‘rgatishi, guruhlar aynan nimani yechishi va javoblari bilan — to‘liq yozasan. Ochiq, namunaviy, loyiha va
ekskursiya darslari shu mazmundan tuziladi. Talablar:
- Mazmun DARSLIKDAGI MAVZUNING O‘ZI: aniq ta’riflar, qoidalar, formulalar, sanalar, nomlar, raqamlar. Umumiy gaplar («mavzu muhim»,
  «bilimlar shakllanadi») YOZILMAYDI. Har jumla o‘quvchiga yangi narsa o‘rgatsin.
- Sinf yoshiga mos til va qiyinlik; 1–4-sinfda oddiy so‘zlar, hayotiy narsalar (olma, pul, soat), qisqa gaplar.
- Misol va masalalarning hisob-kitobi ANIQ tekshirilgan bo‘lsin; yechim qadamma-qadam.
- Fanga mos misol: matematika/fizika/kimyo — masala va yechim; tillar — gap yoki matn tahlili; tarix — manba yoki voqea tahlili;
  biologiya/geografiya — hodisa yoki jarayonni tushuntirish; san’at, texnologiya, jismoniy tarbiya — bajarish tartibi.
- Rasm kalitlari FAQAT berilgan ro‘yxatdan (mos bo‘lmasa bo‘sh qoldir). O‘zbek tili (lotin), imlo xatosiz.
Javob FAQAT JSON:
{"bayon":[{"sarlavha":"o‘rgatish qadami nomi","matn":"o‘qituvchi tushuntiradigan mazmun — 3–5 jumla, aniq faktlar",
   "misol":"shu qadamga bitta aniq misol","savol":"o‘quvchilarga tekshiruv savoli","javob":"qisqa javob","rasm":"kalit yoki bo‘sh"}] × 4–5
   (o‘rgatish ketma-ketligi: oddiydan murakkabga, mavzuning hamma asosiy qismi),
 "asosiy_qoida":"darsning asosiy qoidasi / ta’rifi / formulasi — o‘quvchi daftarga yozadi (1–2 jumla)",
 "misollar":[{"shart","yechim":["1-qadam","2-qadam","…"],"javob"}] × 3 (o‘qituvchi doskada ko‘rsatadigan yechimli namunalar),
 "guruh_topshiriqlari":[{"nom":"qisqa nom","topshiriq":"guruh kartochkasidagi aniq topshiriq — kerakli barcha ma’lumot bilan",
   "yechim":"to‘liq yechim yoki namunaviy javob (o‘qituvchi uchun)","mahsulot":"guruh nima taqdim etadi"}] × 4
   (har guruhga ALOHIDA topshiriq, teng qiyinlikda, mavzuning turli jihati; 8–10 daqiqada bajariladigan),
 "mashqlar":[{"shart","javob"}] × 6 (mustaqil ish: 1–2 oson, 3–4 o‘rta, 5–6 murakkab),
 "qiyinchiliklar":[{"xato":"o‘quvchilar odatda qayerda adashadi","sabab","oldini_olish":"o‘qituvchi nima qiladi"}] × 3,
 "fanlararo":[{"fan","boglanish":"1 jumla — aniq bog‘lanish"}] × 2–3,
 "loyiha":{"nom","muammo":"hayotiy muammo","mahsulot":"plakat | maket | model | buklet | video | jadval…","bosqichlar":["4–6 qadam"],
   "guruh_vazifalari":["4 guruh uchun alohida vazifa"],"mezonlar":["3–5 baholash mezoni"]},
 "ekskursiya":{"joy":"mavzuga mos real joy (muzey, tabiat, korxona, obida) yoki «virtual sayohat: …»",
   "bekatlar":[{"nom","matn":"2–4 jumla aniq va qiziqarli fakt","topshiriq":"bekatdagi topshiriq","javob","rasm":"kalit yoki bo‘sh"}] × 4–5,
   "xavfsizlik":["2–3 qoida"],"kundalik":["kuzatuv kundaligi uchun 3 savol"]}}"""


def _masalliq_xabar(mavzu, fan, daraja, sinf, qoshimcha, mazmun=None) -> str:
    x = f"MAVZU: {mavzu}\nFAN: {fan}\nDARAJA: {daraja}\nSINF/KURS: {sinf}\n" + (f"QO‘SHIMCHA: {qoshimcha}\n" if qoshimcha else "")
    if mazmun:
        x += "\nMAVZU MATERIALI (shunga tayan):\n" + mazmun[:3500] + "\n"
    return x


def masalliq_yoz(mavzu, fan="", daraja="maktab", sinf="", qoshimcha="", deadline=120.0, t0=None, mazmun=None) -> dict:
    """Ochiq dars masalliqlari: ikki parallel chaqiruv — (1) darsning o'zi (bayon, misollar, guruh topshiriqlari va yechimlari,
    mashqlar, loyiha, ekskursiya), (2) interfaol metodlar xomashyosi (atamalar, bayonotlar, savollar, qismlar, keys…).
    Biri ishlamasa — ikkinchisi saqlanadi; ikkalasi ham ishlamasa — xato."""
    from concurrent.futures import ThreadPoolExecutor
    t0 = time.monotonic() if t0 is None else t0
    xabar = _masalliq_xabar(mavzu, fan, daraja, sinf, qoshimcha, mazmun)
    rasm = "\nRASMLAR (kalit — nomi):\n" + katalog_matni(mavzu, fan, 60)
    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(_bir_chaqiruv, DARS_MAZMUNI_KORSATMA, xabar + rasm + "\nDarsni JSON qilib yoz.", deadline, t0)
        f2 = pool.submit(_bir_chaqiruv, MASALLIQ_KORSATMA, xabar + "Masalliqlarni JSON qilib yoz.", deadline, t0)
        qism, xato = {}, None
        for f in (f1, f2):
            try:
                qism.update({k: v for k, v in f.result().items() if k != "_ai"})
            except Exception as exc:
                xato = exc
    if not qism:
        raise RuntimeError(f"Masalliq yozilmadi: {xato}")
    return sxema.masalliq_toza(qism)


def miya_mazmuni(m: dict, n: int = 3500) -> str:
    """Tayyor miyadan masalliq yozuvchisi uchun qisqa matn (ta'rif, qoida, misollar) — masalliq miya bilan mos bo'lsin."""
    qator = []
    for b in (m or {}).get("bolimlar") or []:
        qator.append(f"# {b.get('nom') or ''}")
        for sl in b.get("slaydlar") or []:
            for e in sl.get("elementlar") or []:
                matn = " ".join(str(e.get(k) or "") for k in ("matn", "shart", "formula", "yechim", "javob") if isinstance(e.get(k), str))
                if e.get("bandlar"):
                    matn += " " + "; ".join(f"{x.get('nom') or ''} {x.get('matn') or ''}".strip() for x in e["bandlar"] if isinstance(x, dict))
                matn = re.sub(r"\s+", " ", matn).strip()
                if matn:
                    qator.append(f"- {sl.get('sarlavha') or ''}: {matn[:300]}")
    return "\n".join(qator)[:n]


def miya_yoz(mavzu, fan="", daraja="maktab", sinf="", tur="dars", qoshimcha="", manba="", deadline=170.0, sozlama=None, reja=None,
             masalliq=False):
    """masalliq=True — ochiq dars masalliqlari ham alohida (parallel) chaqiruv bilan yoziladi (mavzular kutubxonasi uchun)."""
    if masalliq:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as pool:
            f = pool.submit(masalliq_yoz, mavzu, fan, daraja, sinf, qoshimcha, deadline)
            out = miya_yoz(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, deadline, sozlama, reja)
            try:
                out["masalliq"] = f.result()
            except Exception:
                pass
        return out
    """AI'dan miya oladi va normallashtiradi.

    Kichik taqdimot — bitta chaqiruv. Katta taqdimot (yoki tayyor reja bilan) — avval reja, so'ng har bo'lim alohida
    va «yakun qismlari» alohida, parallel: mazmun chuqurroq, javob uzilib qolmaydi.
    """
    provs = provayderlar()
    if not provs:
        raise RuntimeError("AI kaliti sozlanmagan (GEMINI_API_KEY, OPENAI_API_KEY yoki GROQ_API_KEY).")
    z = sozlama_toza(sozlama_yosh(sozlama, daraja, sinf))
    t0 = time.monotonic()
    system = korsatma()
    if reja is None and (z["slayd_soni"] or 12) <= 14:
        m = _bir_chaqiruv(system, _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, z), deadline, t0)
        out = sxema.normallashtir(m)
        out["meta"]["mavzu"] = out["meta"]["mavzu"] if out["meta"]["mavzu"] != "Mavzu" else mavzu
        out["meta"]["til"] = z["til"]
        out["_ai"] = m.get("_ai")
        out["_tarjima"] = til_tekshir(out, z["til"], deadline + 40, t0)
        return out
    if reja is None:
        reja = reja_yoz(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, z, deadline=min(70.0, deadline * 0.4))
    else:
        reja = reja_toza(reja, mavzu)
    rmatn = _reja_matni(reja)
    asos = _xabar(mavzu, fan, daraja, sinf, tur, qoshimcha, manba, z).replace("To‘liq JSON miyani yoz.", "")
    vazifalar = []
    for i, b in enumerate(reja["bolimlar"]):
        try:
            bk = katalog_matni(" ".join([b["nom"]] + [sl["sarlavha"] for sl in b["slaydlar"]]), fan, 40, z["til"])
            bk = f"\nBU BO‘LIMGA MOS RASMLAR (kalit — nima tasvirlangan):\n{bk}\n" if "topilmadi" not in bk else ""
        except Exception:
            bk = ""
        vazifalar.append(("bolim", i, asos + bk + f"\nUMUMIY REJA:\n{rmatn}\n\nFAQAT {i + 1}-BO‘LIMNI to‘liq yoz: "
                          f"{{\"bolim\": {{\"nom\",\"izoh\",\"belgi\",\"slaydlar\":[...]}}, \"rasmlar\":[...]}}. "
                          f"Rejadagi slaydlar ({len(b['slaydlar'])} ta) aynan shu tartibda, shu sarlavhalar bilan"
                          f"{'' if z['til'] == 'uz' else ' (sarlavha va bo‘lim nomini ' + TIL_NOMI[z['til']] + 'ga tarjima qilib)'}; har slaydda \"izoh\" "
                          f"(o‘qituvchi gapi), \"joylashuv\" va 1–3 element. Boshqa bo‘limlarni yozma."))
    vazifalar.append(("yakun", -1, asos + f"\nUMUMIY REJA:\n{rmatn}\n\nBo‘limlarni YOZMA (ular alohida yoziladi). Faqat qolgan qismlarni "
                      "yoz: {\"meta\", \"adabiyotlar\", \"takrorlash\", \"muammo\", \"tarix\", \"xatolar\", \"metodika\", "
                      "\"xulosa\", \"test\" (6 ta, rejadagi mazmun bo‘yicha), \"nazorat\", \"mustaqil_ish\", \"keyingi\", "
                      "\"dars\" (dars rejasi: maqsadlar, kompetensiyalar, natijalar, metodlar, jihozlar, bosqichlar vaqti bilan, baholash, uy vazifasi)}."))
    from concurrent.futures import ThreadPoolExecutor
    natija = {}
    with ThreadPoolExecutor(max_workers=min(7, len(vazifalar))) as pool:
        fut = {pool.submit(_bir_chaqiruv, system, matn, deadline, t0): (tur_, i) for tur_, i, matn in vazifalar}
        for f, (tur_, i) in fut.items():
            try:
                natija[(tur_, i)] = f.result()
            except Exception as exc:  # bitta bo'lim yiqilsa — rejadagi sarlavhalar bilan oddiy slaydlar
                natija[(tur_, i)] = {"_xato": str(exc)[:120]}
    yiqildi = sum(1 for (tur_, i), v in natija.items() if tur_ == "bolim" and "_xato" in v)
    if yiqildi * 2 > len(reja["bolimlar"]):   # faqat sarlavhali bo'sh slaydlar bermaymiz — chaqiruvchi bazadan oladi
        raise AiTugadi("AI bo‘limlarni yoza olmadi")
    yakun = natija.get(("yakun", -1)) or {}
    m = {k: v for k, v in yakun.items() if k not in ("bolimlar", "_ai", "_xato")}
    meta = dict(yakun.get("meta") or {})
    meta.setdefault("mavzu", reja["meta"]["mavzu"])
    for k in ("qisqa", "maqsad", "tayanch"):
        if not meta.get(k) and reja["meta"].get(k):
            meta[k] = reja["meta"][k]
    meta.update({"fan": meta.get("fan") or fan, "daraja": daraja, "sinf": meta.get("sinf") or sinf, "tur": meta.get("tur") or tur, "til": z["til"]})
    m["meta"] = meta
    bolimlar, rasmlar_ = [], list(m.get("rasmlar") or [])
    for i, b in enumerate(reja["bolimlar"]):
        r = natija.get(("bolim", i)) or {}
        bb = r.get("bolim") if isinstance(r.get("bolim"), dict) else (r if r.get("slaydlar") else None)
        if not bb or not bb.get("slaydlar"):
            bb = {"nom": b["nom"], "izoh": b.get("izoh"), "slaydlar": [{"sarlavha": sl["sarlavha"], "elementlar": [
                {"tur": "matn", "matn": sl.get("maqsad") or sl["sarlavha"]}]} for sl in b["slaydlar"]]}
        bb.setdefault("nom", b["nom"])
        bolimlar.append(bb)
        rasmlar_ += [x for x in (r.get("rasmlar") or []) if isinstance(x, dict)]
    m["bolimlar"] = bolimlar
    m["rasmlar"] = rasmlar_[:12]
    out = sxema.normallashtir(m)
    out["meta"]["til"] = z["til"]
    out["_ai"] = yakun.get("_ai")
    out["_tarjima"] = til_tekshir(out, z["til"], deadline + 40, t0)
    return out
