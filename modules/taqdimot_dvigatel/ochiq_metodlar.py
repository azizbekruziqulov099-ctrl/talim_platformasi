"""Ochiq dars miyasi — metodlar bazasi (ochiq-dars-miya/1).

Tuzilma: yosh guruhlari → dars formatlari (oddiy, ochiq, namunaviy) → dars andozalari (45 / 80 daqiqa,
bosqichlar vaqti bilan) → metodlar katalogi → guruhlash, guruhlarni birlashtirish, rollar, ilovalar,
baholash → fanlar (har fanning o‘ziga xos metodlari).  Generator shu bazadan fan, sinf, mavzu va dars
turiga qarab metod tanlaydi; AI esa tanlangan metodlarning mazmunini (savol, topshiriq, kartochka) yozadi.
"""
import json

MAKTAB = ["1-2", "3-4", "5-6", "7-9", "10-11"]
OTM = ["b1-2", "b3-4", "m"]
HAMMA = MAKTAB + OTM


def oraliq(a, b):
    return HAMMA[HAMMA.index(a): HAMMA.index(b) + 1]


# ---------------------------------------------------------------- 1. yosh guruhlari
YOSH = [
    {"kod": "1-2", "nom": "1–2-sinf", "yosh": "6–8 yosh", "davr": "kichik maktab yoshi: maktabga moslashuv",
     "dars": 45, "yetakchi_faoliyat": "o‘yin va o‘quv faoliyati birga",
     "xususiyatlar": ["ko‘rgazmali-obrazli tafakkur ustun: narsa, rasm, harakat orqali tushunadi",
                      "diqqat qisqa va beqaror — faoliyat har 5–7 daqiqada almashtiriladi",
                      "o‘qituvchi bahosi va rag‘bati juda muhim, xatoga sezgir",
                      "yozuv va o‘qish endi shakllanmoqda — topshiriqlar asosan og‘zaki, rasmli"],
     "tavsiyalar": ["har darsda 1–2 dinamik pauza (1–2 daqiqa)", "topshiriq ko‘rsatmasi bitta, qisqa, namunasi bilan",
                    "baho o‘rniga rag‘bat belgilari: yulduzcha, smaylik, quyoshcha",
                    "guruh 4–5 kishilik yoki 2 katta jamoa (bellashuv)", "ertak qahramoni, qo‘g‘irchoq, «sirli mehmon» kabi syujet"],
     "guruh_hajmi": "4–5", "guruh_soni": [2, 4], "baholash": "rag‘bat belgilari, og‘zaki maqtov, «svetofor»"},
    {"kod": "3-4", "nom": "3–4-sinf", "yosh": "8–10 yosh", "davr": "kichik maktab yoshi: o‘quv faoliyati yetakchi",
     "dars": 45, "yetakchi_faoliyat": "o‘quv faoliyati",
     "xususiyatlar": ["og‘zaki-mantiqiy tafakkurga o‘tish: taqqoslash, umumlashtirishni o‘rganadi",
                      "mustaqil o‘qiydi va yozadi — matn bilan qisqa ishlash mumkin",
                      "musobaqa va jamoa bo‘lib ishlash yoqadi", "diqqat 10–15 daqiqagacha"],
     "tavsiyalar": ["grafik organayzerlar soddalashtirilgan holda (klaster, Venn, BBB)",
                    "guruhda rollar: sardor, kotib, so‘zlovchi", "o‘z-o‘zini baholash varag‘i (smaylik yoki 3 mezon)",
                    "har darsda 1 dinamik pauza"],
     "guruh_hajmi": "4–6", "guruh_soni": [3, 4], "baholash": "mezonli baholash, o‘z-o‘zini baholash, rag‘bat"},
    {"kod": "5-6", "nom": "5–6-sinf", "yosh": "10–12 yosh", "davr": "fan o‘qituvchilari tizimiga moslashuv",
     "dars": 45, "yetakchi_faoliyat": "o‘quv faoliyati va tengdoshlar bilan muloqot",
     "xususiyatlar": ["har fan o‘qituvchisi yangi talab qo‘yadi — moslashuv davri",
                      "qiziquvchan, faol, harakatchan; bellashuvga moyil",
                      "abstrakt tushunchalar hali ko‘rgazma va misol bilan mustahkamlanadi"],
     "tavsiyalar": ["tajriba, model, o‘yin bilan boyitilgan dars", "mozaika, stansiyalar, galereya sayri",
                    "baholash mezonlari dars boshida ochiq aytiladi"],
     "guruh_hajmi": "4–6", "guruh_soni": [3, 4], "baholash": "mezonli (formativ) baholash, o‘zaro baholash"},
    {"kod": "7-9", "nom": "7–9-sinf", "yosh": "12–15 yosh", "davr": "o‘smirlik",
     "dars": 45, "yetakchi_faoliyat": "tengdoshlar bilan muloqot, o‘zini namoyon qilish",
     "xususiyatlar": ["mustaqillik va kattalar kabi munosabatga intilish",
                      "tengdoshlar fikri muhim — ommaviy tanqid, kulgi og‘ir ta’sir qiladi",
                      "abstrakt va tanqidiy tafakkur rivojlanadi, «nima uchun kerak?» degan savol tug‘iladi"],
     "tavsiyalar": ["hayotiy, muammoli topshiriqlar; mavzuning amaliy ahamiyatini ko‘rsatish",
                    "debat, keys, loyiha, tadqiqot", "rollar almashib turadi, har kim so‘zga chiqadi",
                    "tanqid shaxsga emas, ishga qaratiladi"],
     "guruh_hajmi": "4–6", "guruh_soni": [3, 4], "baholash": "rubrika, o‘zaro baholash, formativ izoh"},
    {"kod": "10-11", "nom": "10–11-sinf", "yosh": "15–17 yosh", "davr": "ilk o‘spirinlik: kasbiy o‘zini belgilash",
     "dars": 45, "yetakchi_faoliyat": "o‘quv-kasbiy faoliyat",
     "xususiyatlar": ["nazariy-mantiqiy tafakkur, o‘z nuqtai nazarini asoslashga intilish",
                      "kasb tanlash, imtihonlarga tayyorgarlik bilan bog‘liq motivatsiya"],
     "tavsiyalar": ["keys-stadi, debat, sokratik suhbat, tadqiqot, teskari sinf",
                    "xalqaro baholash (PISA) uslubidagi hayotiy topshiriqlar", "mavzuni kasb va OTM bilan bog‘lash"],
     "guruh_hajmi": "4–6", "guruh_soni": [3, 4], "baholash": "rubrika, o‘zaro va o‘z-o‘zini baholash"},
    {"kod": "b1-2", "nom": "Bakalavr 1–2-kurs", "yosh": "17–20 yosh", "davr": "oliy ta’limga moslashuv",
     "dars": 80, "yetakchi_faoliyat": "o‘quv-kasbiy faoliyat",
     "xususiyatlar": ["ma’ruza va seminar tizimiga moslashuv", "mustaqil ta’lim ko‘nikmasi endi shakllanmoqda"],
     "tavsiyalar": ["interfaol ma’ruza: har 15–20 daqiqada faollashtiruvchi savol yoki topshiriq",
                    "blits-so‘rov, keys, Venn, konseptual jadval", "mustaqil ish topshirig‘i aniq mezon bilan"],
     "guruh_hajmi": "5–7", "guruh_soni": [3, 4], "baholash": "joriy nazorat ballari, rubrika"},
    {"kod": "b3-4", "nom": "Bakalavr 3–4-kurs", "yosh": "19–22 yosh", "davr": "kasbiy-metodik tayyorgarlik",
     "dars": 80, "yetakchi_faoliyat": "kasbiy faoliyatga tayyorlanish",
     "xususiyatlar": ["mutaxassislik fanlari, pedagogik amaliyot", "kasbiy vaziyatlarni hal qilishga tayyor"],
     "tavsiyalar": ["mikrodars, rolli o‘yin (o‘qituvchi — o‘quvchi), pedagogik keys", "loyiha, portfolio, dars tahlili"],
     "guruh_hajmi": "5–7", "guruh_soni": [3, 4], "baholash": "rubrika, portfolio, o‘zaro baholash"},
    {"kod": "m", "nom": "Magistratura 1–2-kurs", "yosh": "21 yoshdan", "davr": "ilmiy-tadqiqot va kasbiy chuqurlashuv",
     "dars": 80, "yetakchi_faoliyat": "ilmiy-tadqiqot faoliyati",
     "xususiyatlar": ["o‘z tadqiqot mavzusi bor", "ilmiy manba, metodologiya bilan ishlay oladi"],
     "tavsiyalar": ["jurnal klubi, tadqiqot seminari, akvarium, sokratik seminar", "o‘zaro taqriz (peer review), loyiha himoyasi"],
     "guruh_hajmi": "4–6", "guruh_soni": [2, 3], "baholash": "rubrika, taqriz, himoya"},
]

# ---------------------------------------------------------------- 2. dars formatlari
FORMATLAR = [
    {"kod": "oddiy", "nom": "Kundalik dars",
     "maqsad": "dastur bo‘yicha mavzuni o‘tish",
     "hujjatlar": ["dars rejasi (ishlanma)", "taqdimot", "tarqatma materiallar"]},
    {"kod": "ochiq", "nom": "Ochiq dars",
     "maqsad": "o‘qituvchi o‘z ijobiy yoki yangi tajribasini, metodik g‘oyasini hamkasblarga ko‘rsatadi; dars real o‘quv jarayoni bo‘lib qoladi",
     "kim_uchun": ["metodbirlashma (kafedra) a’zolari", "tuman, viloyat o‘qituvchilari (seminar)", "attestatsiya (toifa) uchun ekspertlar",
                   "tanlov hakamlari", "OTMda kafedra a’zolari va rahbariyat"],
     "metodik_maqsad": {
         "izoh": "dars maqsadidan tashqari ochiq darsning metodik maqsadi bo‘ladi — o‘qituvchi aynan nimani ko‘rsatmoqchi",
         "namunalar": ["kichik guruhlarda ishlash orqali tanqidiy fikrlashni rivojlantirish usullarini ko‘rsatish",
                       "«Mozaika» metodi yordamida yangi bilimni o‘quvchilar mustaqil egallashini tashkil etish",
                       "STEAM yondashuvida fanlararo topshiriqlardan foydalanish",
                       "formativ baholash vositalarini dars bosqichlarida qo‘llash",
                       "o‘yin texnologiyasi orqali kichik yoshdagi o‘quvchilarning faolligini oshirish"]},
     "hujjatlar": ["ochiq dars ishlanmasi (titul, maqsadlar, texnologik xarita, darsning borishi, ilovalar)",
                   "taqdimot", "ilovalar to‘plami (guruh qoidalari, baholash varag‘i, tarqatmalar, o‘yin kartochkalari, test, refleksiya)",
                   "mehmon varaqasi (fan, sinf, mavzu, metodik maqsad, dars algoritmi)", "kuzatuv (tahlil) varag‘i nusxalari",
                   "o‘z-o‘zini tahlil rejasi"],
     "tayyorgarlik": [
         {"qachon": "2 hafta oldin", "ish": "mavzu va metodik maqsadni metodbirlashma (kafedra) rejasi bilan kelishish; sinf (guruh) tavsifini tayyorlash: o‘zlashtirish darajasi, faol va passiv o‘quvchilar"},
         {"qachon": "10 kun oldin", "ish": "dars turi va tuzilishini tanlash; har bosqich uchun metod, guruhlash usuli va yakuniy birlashtiruvchi o‘yinni belgilash"},
         {"qachon": "1 hafta oldin", "ish": "ishlanma (texnologik xarita + darsning borishi) va ilovalarni yozish; taqdimotni tayyorlash"},
         {"qachon": "5 kun oldin", "ish": "hamkasb yoki metodbirlashma rahbari bilan ko‘rib chiqish; zaxira topshiriqlar va muqobil variantlar tayyorlash"},
         {"qachon": "3 kun oldin", "ish": "jihozlarni sinash: proyektor, kompyuter, ovoz, laboratoriya asboblari; tarqatmalarni chop etish"},
         {"qachon": "1 kun oldin", "ish": "xonani tayyorlash: guruh stollari, guruh nomlari, ball jadvali, mehmonlar uchun joy (orqa yoki yon tomonda); mehmon varaqasi va kuzatuv varag‘i nusxalari"},
         {"qachon": "dars kuni", "ish": "taymer, zaxira topshiriq tayyor; o‘quvchilarni xotirjam qilish — mehmonlar «tekshiruvchi» emasligini aytish"}],
     "qoidalar": ["o‘quvchilar bilan darsni oldindan «mashq qilish», javoblarni yodlatish mumkin emas — dars sun’iy bo‘lib qoladi",
                  "ko‘rgazma, effekt va musiqa mazmundan ustun bo‘lmasin", "xato javob uchun jazolamaslik; xato — o‘rganish imkoniyati",
                  "reja qat’iy emas: vaziyatga qarab o‘zgartirishga tayyor turish (zaxira topshiriq)",
                  "har bir o‘quvchi kamida bir marta faol ishtirok etsin; faqat «kuchli»lar gapirmasin",
                  "vaqt qat’iy nazorat qilinadi — ochiq dars 45 (80) daqiqadan oshmaydi"],
     "tahlil": {
         "tartib": ["o‘qituvchining o‘z-o‘zini tahlili: metodik maqsadga erishildimi, rejadan chetlanishlar sababi, mehmonlar ko‘rmagan jihatlar",
                    "mehmonlarning savollari va o‘qituvchi javoblari",
                    "muhokama: har bir so‘zga chiquvchi 3–5 daqiqa; avval ijobiy, keyin takliflar",
                    "rahbar (metodbirlashma rahbari, direktor o‘rinbosari, kafedra mudiri) xulosasi",
                    "o‘qituvchining yakuniy so‘zi; bayonnoma"],
         "ozini_tahlil_savollari": ["Dars mavzular tizimida qanday o‘rin tutadi?", "Ta’limiy, tarbiyaviy, rivojlantiruvchi maqsadlarga erishildimi — qanday dalil bor?",
                                    "Metodik maqsad qanday amalga oshdi?", "Tanlangan metodlar shu sinf yoshi va darajasiga mos keldimi?",
                                    "Qaysi bosqichda rejadan chetlashdim va nima uchun?", "Har bir o‘quvchi qanchalik faol bo‘ldi?",
                                    "Vaqt taqsimoti to‘g‘ri bo‘ldimi?", "Keyingi safar nimani o‘zgartiraman?"],
         "turlari": ["didaktik", "uslubiy (metodik)", "psixologik", "pedagogik", "metodologik"],
         "kuzatuv_mezonlari": ["maqsadning aniqligi va o‘quvchilarga yetkazilishi", "mazmunning ilmiyligi va yoshga mosligi",
                               "metodlarning maqsadga mosligi va xilma-xilligi", "o‘quvchilar faolligi va mustaqilligi",
                               "guruh ishining tashkil etilishi", "baholashning ochiqligi va adolatliligi (mezonlar)",
                               "vaqtdan foydalanish", "ko‘rgazma va texnik vositalardan o‘rinli foydalanish",
                               "o‘qituvchi nutqi va pedagogik muomala", "fanlararo bog‘lanish, 4K va STEAM unsurlari",
                               "tarbiyaviy jihat", "darsning natijasi: o‘quvchilar nimani o‘rgandi"]}},
    {"kod": "namunaviy", "nom": "Namunaviy dars (mahorat darsi)",
     "maqsad": "standart talablarga to‘liq mos, boshqa o‘qituvchilar takrorlay oladigan «andoza» dars; ko‘pincha videoga yoziladi yoki tajribani ommalashtirishda ko‘rsatiladi",
     "farqi": ["har bosqichda «kuzatuvchi uchun izoh»: bu metod nima uchun tanlangani va qanday natija bergani",
               "metodni boshqa sinf va mavzuga moslashtirish shartlari yoziladi",
               "dars 45 (80) daqiqalik real dars; undan keyin hamkasblar uchun mahorat darsi o‘tkazilishi mumkin"],
     "mahorat_darsi": [{"nom": "Metod g‘oyasi va natijasi", "daq": 5},
                       {"nom": "Hamkasblar metodni «o‘quvchi» sifatida sinab ko‘radi", "daq": 10},
                       {"nom": "Savol-javob, o‘z faniga moslashtirish", "daq": 5}],
     "hujjatlar": ["namunaviy dars ishlanmasi (kuzatuvchi izohlari bilan)", "taqdimot", "ilovalar", "metodik tavsiya (qisqa)", "video yozuv rejasi"]},
]

# ---------------------------------------------------------------- 3. dars andozalari (vaqt bilan)
def B(nom, daq, oqituvchi, oquvchi, tur=(), izoh="", guruh=False, ilova=(), afzal=()):
    """afzal — shu bosqichga eng mos metodlar (tanlovda birinchi navbatda shulardan olinadi)."""
    return {"nom": nom, "daq": daq, "oqituvchi": oqituvchi, "oquvchi": oquvchi, "metod_turi": list(tur),
            "izoh": izoh, "guruh": guruh, "ilova": list(ilova), "afzal": list(afzal)}


AF_TAKROR = ["blits", "ha_yoq", "zanjir", "domino", "matematik_diktant", "xatoni_top", "breyn_ring", "men_kimman", "ortiqchasini_top", "tarif_egasi", "intervyu"]
AF_IZLANISH = ["mozaika", "tadqiqot_mini", "yonaltiruvchi_matn", "insert", "modellashtirish", "bashorat_kuzatish", "manba_tahlili", "venn",
               "klaster", "xronologik_lenta", "evristik_suhbat", "keys"]
AF_TAQDIMOT = ["galereya", "charxpalak", "bumerang", "juft_tekshirish", "kubik", "mezonli_baholash"]
AF_REFLEKSIYA = ["uch_ikki_bir", "svetofor", "chiqish_chiptasi", "tugallanmagan_gap", "besh_barmoq", "bbb", "smayliklar", "bilim_daraxti", "pmi", "sinkveyn"]


ANDOZALAR = [
    {"kod": "aralash_45", "nom": "Aralash (yangi bilim beruvchi) dars", "daqiqa": 45, "yosh": oraliq("3-4", "10-11"),
     "bosqichlar": [
         B("Tashkiliy qism", 2, "salomlashadi, davomatni aniqlaydi, kun hikmati yoki dars shiorini e’lon qiladi", "darsga tayyorlanadi", ["motivatsiya"]),
         B("Uy vazifasini tekshirish va takrorlash", 6, "o‘tgan mavzu bo‘yicha savol, topshiriq beradi", "javob beradi, uy vazifasini tahlil qiladi", ["takrorlash"],
           afzal=AF_TAKROR),
         B("Motivatsiya va maqsad", 4, "muammoli savol yoki hayotiy vaziyat bilan mavzuga olib kiradi, maqsadni o‘quvchilar bilan aniqlaydi", "taxmin qiladi, maqsadni aytadi", ["motivatsiya"]),
         B("Yangi mavzu", 15, "yangi bilimni tashkil etadi: kichik bayon, ko‘rgazma, izlanish topshirig‘i", "o‘rganadi, yozib boradi, savol beradi", ["yangi_bilim"]),
         B("Mustahkamlash", 11, "mashq, juftlik yoki guruh topshirig‘ini beradi, yordam beradi", "bajaradi, tekshiradi", ["mustahkamlash"], guruh=True),
         B("Baholash va refleksiya", 4, "mezonlar asosida baholaydi, refleksiya o‘tkazadi", "o‘zini baholaydi, fikr bildiradi", ["refleksiya"], afzal=AF_REFLEKSIYA),
         B("Uy vazifasi", 3, "darajali uy vazifasini tushuntiradi", "yozib oladi", [], ilova=["uy_vazifasi"])]},
    {"kod": "aralash_45_kichik", "nom": "Aralash dars (1–2-sinf)", "daqiqa": 45, "yosh": ["1-2"],
     "bosqichlar": [
         B("Tashkiliy qism (salomlashish o‘yini)", 2, "quvnoq salomlashish, kayfiyat yaratadi", "darsga tayyorlanadi"),
         B("Takrorlash o‘yini", 6, "o‘tgan mavzuni o‘yin shaklida takrorlaydi", "o‘ynab javob beradi", ["takrorlash", "oyin"]),
         B("Motivatsiya", 3, "sirli quti, topishmoq yoki ertak qahramoni bilan mavzuni ochadi", "taxmin qiladi", ["motivatsiya"]),
         B("Yangi bilim (1-qism)", 8, "ko‘rgazma, predmet, rasm bilan tushuntiradi", "kuzatadi, takrorlaydi", ["yangi_bilim"]),
         B("Dinamik pauza", 2, "mavzuga oid harakatli she’r yoki sanoq", "harakat bajaradi", ["energizer"]),
         B("Yangi bilim (2-qism, amaliy)", 7, "predmetlar, kartochkalar bilan amaliy ish beradi", "qo‘l bilan bajaradi", ["yangi_bilim", "amaliy"]),
         B("Mustahkamlash o‘yini", 10, "juftlik yoki guruh o‘yinini boshqaradi", "o‘ynaydi, bir-biriga yordam beradi", ["oyin", "mustahkamlash"], guruh=True),
         B("Refleksiya va rag‘bat", 4, "rag‘bat belgilarini beradi, kayfiyatni so‘raydi", "smaylik yoki svetofor bilan baholaydi", ["refleksiya"]),
         B("Yakun va uyga topshiriq", 3, "uyga ijodiy yoki kuzatish topshirig‘ini beradi (1-sinfda — faqat ixtiyoriy)", "tinglaydi")]},
    {"kod": "ochiq_guruh_45", "nom": "Ochiq dars (guruhli)", "daqiqa": 45, "yosh": oraliq("3-4", "10-11"),
     "bosqichlar": [
         B("Tashkiliy qism, guruhlarga ajratish", 4, "guruhlash usuli bilan 2–4 guruhga ajratadi, guruh nomlari, qoidalar va baholash mezonlarini e’lon qiladi",
           "guruhga bo‘linadi, sardor va rollarni tanlaydi", ["guruhlash"], guruh=True, ilova=["guruh_qoidalari", "baholash_varagi", "guruh_nomlari"]),
         B("Takrorlash: guruhlar bellashuvi", 6, "o‘tgan mavzu bo‘yicha guruhlarga savol beradi, ball qo‘yadi", "guruh bo‘lib javob beradi",
           ["takrorlash", "oyin"], guruh=True, ilova=["oyin_kartochkalari"], afzal=AF_TAKROR),
         B("Motivatsiya, muammo va maqsad", 4, "muammoli vaziyat yaratadi, maqsadni o‘quvchilar bilan aniqlaydi", "taxmin va savollarini aytadi", ["motivatsiya"]),
         B("Yangi bilim: kirish va guruhlarda izlanish", 13, "5 daqiqa qisqa kirish beradi, so‘ng har guruhga mavzuning bir qismini yoki topshirig‘ini beradi, yo‘naltiradi",
           "guruhda o‘rganadi, natijani tayyorlaydi", ["yangi_bilim", "guruh_ishi"], guruh=True, ilova=["tarqatma", "tayanch_konspekt"], afzal=AF_IZLANISH),
         B("Guruh taqdimotlari va o‘zaro baholash", 8, "taqdimotlarni tartibga soladi, aniqlik kiritadi", "taqdim etadi, boshqa guruhni mezon bilan baholaydi",
           ["mustahkamlash"], guruh=True, afzal=AF_TAQDIMOT),
         B("Guruhlarni birlashtirish: yakuniy umumiy topshiriq", 5, "barcha guruhlar natijasi kerak bo‘ladigan umumiy o‘yin yoki topshiriqni boshqaradi",
           "birgalikda yakuniy natijani yig‘adi", ["birlashtirish"], guruh=True),
         B("Baholash, refleksiya, rag‘bat", 3, "ball jadvalini yakunlaydi, faollarni rag‘batlantiradi", "refleksiya varag‘ini to‘ldiradi", ["refleksiya"],
           ilova=["refleksiya_varagi"], afzal=AF_REFLEKSIYA),
         B("Uy vazifasi (darajali)", 2, "A/B/C darajali uy vazifasini beradi", "tanlab yozib oladi", [], ilova=["uy_vazifasi"])]},
    {"kod": "ochiq_guruh_45_kichik", "nom": "Ochiq dars (1–2-sinf, o‘yinli)", "daqiqa": 45, "yosh": ["1-2"],
     "bosqichlar": [
         B("Tashkiliy qism, guruhlarga ajratish", 4, "rangli kartochka yoki rasm bo‘laklari bilan 2 yoki 4 guruhga ajratadi; guruh belgisi va qoidalar",
           "guruh belgisini oladi, joylashadi", ["guruhlash"], guruh=True, ilova=["guruh_nomlari", "guruh_qoidalari"]),
         B("Takrorlash o‘yini (jamoalar bellashuvi)", 6, "o‘yin savollari, rag‘bat belgisi beradi", "jamoa bo‘lib javob beradi", ["takrorlash", "oyin"], guruh=True),
         B("Motivatsiya: «sirli mehmon»", 3, "ertak qahramoni, sirli quti yoki topishmoq bilan mavzuni ochadi", "topadi, taxmin qiladi", ["motivatsiya"]),
         B("Yangi bilim (ko‘rgazmali)", 8, "predmet, rasm, harakat bilan tushuntiradi", "kuzatadi, takrorlaydi", ["yangi_bilim"]),
         B("Dinamik pauza", 2, "mavzuga oid harakatli she’r", "harakat bajaradi", ["energizer"]),
         B("Guruhlarda o‘yin-topshiriq", 10, "stansiya yoki estafeta topshiriqlarini boshqaradi", "guruhda bajaradi", ["oyin", "mustahkamlash"], guruh=True,
           ilova=["oyin_kartochkalari"]),
         B("Guruhlarni birlashtirish", 6, "har guruh topgan «bo‘lak» bilan umumiy rasm, daraxt yoki xazinani yig‘dirtiradi", "birgalikda yig‘adi", ["birlashtirish"], guruh=True),
         B("Refleksiya va rag‘bat", 4, "har bir bolani rag‘batlantiradi", "smaylik bilan kayfiyatini ko‘rsatadi", ["refleksiya"]),
         B("Uyga ijodiy topshiriq", 2, "rasm chizish, kuzatish kabi ixtiyoriy topshiriq", "tinglaydi")]},
    {"kod": "amaliy_45", "nom": "Amaliy dars", "daqiqa": 45, "yosh": oraliq("3-4", "10-11"),
     "bosqichlar": [
         B("Tashkiliy qism, jihozlar", 2, "jihozlarni tekshiradi, kerak bo‘lsa xavfsizlik qoidasini eslatadi", "ish joyini tayyorlaydi"),
         B("Bilimlarni faollashtirish", 5, "qoida, formula yoki algoritmni takrorlatadi", "aytadi, yozadi", ["takrorlash"]),
         B("Namuna (ko‘rsatish)", 7, "namunani ovoz chiqarib fikrlab bajaradi, yo‘riqnoma kartasini beradi", "kuzatadi, savol beradi", ["yangi_bilim"],
           ilova=["yoriqnoma_kartasi"]),
         B("Boshqariladigan mashq", 8, "juftlikda bajarishni kuzatadi, xatolarni to‘g‘rilaydi", "juftlikda bajaradi", ["mustahkamlash"], guruh=True),
         B("Mustaqil amaliy ish", 15, "A/B/C darajali topshiriqlarni beradi, individual yordam beradi", "mustaqil bajaradi", ["amaliy"], ilova=["tarqatma"]),
         B("Tekshirish va taqdimot", 5, "natijalarni ko‘rsattiradi, o‘zaro tekshiruvni tashkil etadi", "taqdim etadi, tekshiradi", ["nazorat"]),
         B("Refleksiya, uy vazifasi", 3, "yakun qiladi, uy vazifasini beradi", "fikr bildiradi", ["refleksiya"], ilova=["uy_vazifasi"])]},
    {"kod": "laboratoriya_45", "nom": "Laboratoriya darsi", "daqiqa": 45, "yosh": oraliq("5-6", "10-11"),
     "bosqichlar": [
         B("Tashkiliy qism, xavfsizlik yo‘riqnomasi", 5, "juftlik yoki guruhlarga ajratadi, xavfsizlik qoidalarini tushuntiradi", "qoidalarni takrorlaydi",
           ["guruhlash"], guruh=True, ilova=["xavfsizlik"]),
         B("Nazariy tayyorgarlik va gipoteza", 5, "ish maqsadini aytadi, kirish savollari beradi, natijani bashorat qildiradi", "javob beradi, gipoteza yozadi",
           ["takrorlash", "motivatsiya"]),
         B("Ish tartibi bilan tanishish", 5, "yo‘riqnoma kartasi va jihozlarni ko‘rsatadi", "jihozlarni tekshiradi", [], ilova=["yoriqnoma_kartasi"]),
         B("Tajribani bajarish va o‘lchash", 18, "kuzatadi, maslahat beradi, xavfsizlikni nazorat qiladi", "tajriba qiladi, natijani jadvalga yozadi", ["tadqiqot"], guruh=True),
         B("Hisoblash, grafik, xulosa", 7, "hisoblash va xulosa yozishga yo‘naltiradi", "hisoblaydi, xulosa yozadi"),
         B("Natijalarni taqqoslash, baholash", 3, "guruhlar natijasini taqqoslaydi, mezon bo‘yicha baholaydi; ish joyi tartibga keltiriladi", "natijani aytadi",
           ["nazorat"], ilova=["baholash_varagi"]),
         B("Uy vazifasi", 2, "hisobotni yakunlash yoki uyda takrorlash mumkin bo‘lgan tajriba", "yozib oladi", [], ilova=["uy_vazifasi"])]},
    {"kod": "takrorlash_45", "nom": "Takrorlash-umumlashtirish darsi (o‘yinli)", "daqiqa": 45, "yosh": oraliq("3-4", "10-11"),
     "bosqichlar": [
         B("Tashkiliy qism, guruhlar, o‘yin qoidalari", 3, "guruhlarga ajratadi, bosqichlar va ball tizimini e’lon qiladi", "joylashadi, rollarni tanlaydi", ["guruhlash"],
           guruh=True, ilova=["guruh_qoidalari", "baholash_varagi"]),
         B("1-bosqich: blits", 5, "tez savollar beradi", "tez javob beradi", ["takrorlash"], guruh=True),
         B("2-bosqich: stansiyalar yoki charxpalak", 15, "topshiriqlar aylanishini boshqaradi", "har stansiyada topshiriq bajaradi", ["mustahkamlash"], guruh=True,
           ilova=["tarqatma"]),
         B("3-bosqich: ijodiy topshiriq", 10, "klaster, plakat yoki mini-loyiha topshirig‘ini beradi", "yaratadi, taqdim etadi", ["mustahkamlash"], guruh=True),
         B("4-bosqich: final — guruhlarni birlashtirish", 7, "barcha guruhlar birga ishtirok etadigan final o‘yinini o‘tkazadi", "birgalikda o‘ynaydi", ["birlashtirish"], guruh=True),
         B("Natijalar, refleksiya, rag‘bat", 3, "ball jadvalini yakunlaydi", "refleksiya qiladi", ["refleksiya"], afzal=AF_REFLEKSIYA),
         B("Uy vazifasi", 2, "umumlashtiruvchi uy vazifasi", "yozib oladi", [], ilova=["uy_vazifasi"])]},
    {"kod": "jismoniy_45", "nom": "Jismoniy tarbiya darsi", "daqiqa": 45, "yosh": MAKTAB, "fan": ["jismoniy"],
     "bosqichlar": [
         B("Tayyorlov qismi", 10, "saf, salom, vazifalarni e’lon qiladi; yurish, yugurish, umumrivojlantiruvchi mashqlar", "mashqlarni bajaradi"),
         B("Asosiy qism: yangi harakatni o‘rgatish", 12, "harakatni ko‘rsatadi, bo‘laklab o‘rgatadi, xatolarni tuzatadi", "takrorlaydi", ["yangi_bilim"]),
         B("Asosiy qism: takomillashtirish", 8, "guruh yoki aylana (stansiya) usulida mashq qildiradi", "guruhda mashq qiladi", ["mustahkamlash"], guruh=True),
         B("Asosiy qism: harakatli o‘yin yoki estafeta", 8, "jamoalarga ajratib o‘yin o‘tkazadi", "o‘ynaydi", ["oyin", "mustahkamlash"], guruh=True,
           afzal=["estafeta", "stansiyalar"]),
         B("Yakuniy qism", 5, "tinchlantiruvchi mashqlar, puls, yakun va baho", "nafasni rostlaydi"),
         B("Uyga vazifa", 2, "uyda bajariladigan mashq", "tinglaydi")]},
    {"kod": "xorijiy_til_45", "nom": "Chet tili darsi", "daqiqa": 45, "yosh": MAKTAB, "fan": ["ingliz_tili", "rus_tili"],
     "bosqichlar": [
         B("Greeting & warm-up", 5, "salomlashadi, qisqa o‘yin yoki qo‘shiq", "faollashadi", ["motivatsiya"]),
         B("Review / homework check", 5, "o‘tgan leksika va uy vazifasini tekshiradi", "javob beradi", ["takrorlash"]),
         B("Lead-in", 3, "mavzuga rasm yoki savol bilan olib kiradi", "taxmin qiladi", ["motivatsiya"]),
         B("Presentation", 8, "yangi so‘z va grammatikani kontekstda ko‘rsatadi", "tinglaydi, takrorlaydi", ["yangi_bilim"]),
         B("Controlled practice", 8, "boshqariladigan mashqlar beradi", "juftlikda bajaradi", ["mustahkamlash"], guruh=True),
         B("Production", 11, "muloqot topshirig‘i: rolli o‘yin, information gap, loyiha", "guruhda gapiradi", ["mustahkamlash", "guruh_ishi"], guruh=True),
         B("Feedback & reflection", 3, "xatolar ustida ishlaydi, refleksiya", "fikr bildiradi", ["refleksiya"]),
         B("Homework", 2, "uy vazifasi", "yozib oladi", [], ilova=["uy_vazifasi"])]},
    # ------------------------------------------------ OTM: 80 daqiqa (kirish 10 — asosiy 60 — yakuniy 10)
    {"kod": "maruza_80", "nom": "Interfaol ma’ruza", "daqiqa": 80, "yosh": OTM,
     "bosqichlar": [
         B("Kirish bosqichi", 10, "mavzu, reja, maqsad va kutilgan natijalarni e’lon qiladi; muammoli savol yoki BBB bilan faollashtiradi", "yozib oladi, fikr bildiradi",
           ["motivatsiya"]),
         B("Asosiy bosqich: 1-blok", 17, "12 daqiqa bayon, so‘ng 5 daqiqalik faollashtiruvchi savol yoki topshiriq", "konspekt qiladi, javob beradi", ["yangi_bilim"]),
         B("Asosiy bosqich: 2-blok", 17, "bayon va grafik organayzer (klaster, Venn)", "organayzerni to‘ldiradi", ["yangi_bilim", "mustahkamlash"]),
         B("Asosiy bosqich: 3-blok", 16, "bayon, mini-keys yoki Insert", "tahlil qiladi", ["yangi_bilim"]),
         B("Asosiy bosqich: umumlashtirish va savollar", 10, "asosiy g‘oyalarni umumlashtiradi, savollarga javob beradi", "savol beradi", ["mustahkamlash"]),
         B("Yakuniy bosqich", 10, "blits-nazorat, mustaqil ish topshirig‘i va adabiyotlarni beradi", "javob beradi, yozib oladi", ["nazorat", "refleksiya"],
           ilova=["adabiyotlar", "uy_vazifasi"])]},
    {"kod": "seminar_80", "nom": "Seminar mashg‘uloti", "daqiqa": 80, "yosh": OTM,
     "bosqichlar": [
         B("Kirish bosqichi", 10, "maqsad, reja, guruhlarga ajratish, baholash mezonlari", "guruhlarga bo‘linadi", ["guruhlash"], guruh=True, ilova=["baholash_varagi"]),
         B("Blits-so‘rov", 10, "nazariy savollar", "javob beradi", ["takrorlash"]),
         B("Guruhlarda muammoli topshiriq yoki keys", 20, "topshiriq beradi, maslahatchi bo‘ladi", "tahlil qiladi, yechim tayyorlaydi", ["mustahkamlash", "tadqiqot"], guruh=True,
           ilova=["tarqatma"]),
         B("Taqdimot va muhokama", 20, "muhokamani boshqaradi", "taqdim etadi, savol beradi", ["mustahkamlash"], guruh=True),
         B("Debat yoki akvarium", 10, "munozarani tashkil etadi", "ishtirok etadi yoki kuzatib baholaydi", ["mustahkamlash", "birlashtirish"], guruh=True),
         B("Yakuniy bosqich", 10, "umumlashtiradi, baholaydi, mustaqil ish beradi", "refleksiya qiladi", ["refleksiya", "nazorat"], ilova=["uy_vazifasi"])]},
    {"kod": "amaliy_80", "nom": "Amaliy mashg‘ulot", "daqiqa": 80, "yosh": OTM,
     "bosqichlar": [
         B("Kirish bosqichi", 10, "nazariy asosni takrorlatadi, maqsadni aytadi", "javob beradi", ["takrorlash"]),
         B("Namuna yechim", 10, "namunani tahlil qilib yechadi", "kuzatadi", ["yangi_bilim"]),
         B("Juftlikda mashq", 15, "kuzatadi, yordam beradi", "juftlikda bajaradi", ["mustahkamlash"], guruh=True),
         B("Mustaqil yoki guruh topshirig‘i", 25, "darajali topshiriqlar, keys yoki loyiha qismi", "bajaradi", ["amaliy", "tadqiqot"], guruh=True, ilova=["tarqatma"]),
         B("Tekshirish va muhokama", 10, "natijalarni muhokama qiladi", "taqdim etadi, o‘zaro tekshiradi", ["nazorat"]),
         B("Yakuniy bosqich", 10, "baholaydi, mustaqil ish beradi", "refleksiya qiladi", ["refleksiya"], ilova=["uy_vazifasi"])]},
    {"kod": "laboratoriya_80", "nom": "Laboratoriya mashg‘uloti", "daqiqa": 80, "yosh": OTM,
     "bosqichlar": [
         B("Kirish: xavfsizlik va kirish nazorati", 15, "xavfsizlik yo‘riqnomasi, ishga ruxsat savollari, maqsad", "javob beradi, ish rejasini tuzadi", ["takrorlash"],
           ilova=["xavfsizlik", "yoriqnoma_kartasi"]),
         B("Tajribani bajarish", 35, "kuzatadi, maslahat beradi", "tajriba qiladi, o‘lchaydi", ["tadqiqot"], guruh=True),
         B("Hisoblash va grafik", 15, "xatoliklar tahliliga yo‘naltiradi", "hisoblaydi, grafik chizadi"),
         B("Xulosa va hisobot", 5, "xulosa talablarini eslatadi", "xulosa yozadi", []),
         B("Yakuniy: hisobot himoyasi, baholash", 10, "savollar beradi, baholaydi", "himoya qiladi", ["nazorat"], ilova=["baholash_varagi"])]},
    {"kod": "ochiq_otm_80", "nom": "Ochiq mashg‘ulot (OTM, guruhli)", "daqiqa": 80, "yosh": OTM,
     "bosqichlar": [
         B("Kirish bosqichi, guruhlarga ajratish", 10, "3–4 guruhga ajratadi, qoidalar, baholash mezonlari, maqsad va kutilgan natijalar", "guruhlarga bo‘linadi, rollarni taqsimlaydi",
           ["guruhlash"], guruh=True, ilova=["guruh_qoidalari", "baholash_varagi"]),
         B("Faollashtirish", 8, "blits yoki BBB", "javob beradi", ["takrorlash", "motivatsiya"]),
         B("Nazariy asos: kichik ma’ruza", 12, "asosiy tushunchalarni bayon qiladi, Insert bilan ishlatadi", "belgilab o‘qiydi", ["yangi_bilim"], ilova=["tayanch_konspekt"]),
         B("Guruhlarda ishlash", 20, "keys, mozaika yoki loyiha topshirig‘ini beradi", "tahlil qiladi, natija tayyorlaydi", ["guruh_ishi", "tadqiqot"], guruh=True,
           ilova=["tarqatma"]),
         B("Taqdimot va o‘zaro baholash", 15, "tartibni boshqaradi, aniqlik kiritadi", "taqdim etadi, baholaydi", ["mustahkamlash"], guruh=True),
         B("Guruhlarni birlashtirish", 7, "guruh natijalaridan umumiy model, klaster yoki qaror yig‘diradi", "birgalikda yakunlaydi", ["birlashtirish"], guruh=True),
         B("Yakuniy bosqich", 8, "baholaydi, refleksiya, mustaqil ish", "refleksiya qiladi", ["refleksiya", "nazorat"], ilova=["refleksiya_varagi", "uy_vazifasi"])]},
    {"kod": "magistr_seminar_80", "nom": "Tadqiqot seminari (magistratura)", "daqiqa": 80, "yosh": ["m"],
     "bosqichlar": [
         B("Kirish", 10, "maqsad, kun tartibi, baholash mezonlari", "tayyorlanadi", ["motivatsiya"]),
         B("Maqola yoki keys tahlili (jurnal klubi)", 20, "muhokamani yo‘naltiradi", "tahlil qiladi, tanqidiy savol beradi", ["tadqiqot"], guruh=True),
         B("Tadqiqot loyihalari taqdimoti va o‘zaro taqriz", 25, "taqriz mezonlarini beradi", "taqdim etadi, taqriz qiladi", ["tadqiqot", "mustahkamlash"], guruh=True),
         B("Akvarium yoki debat", 15, "munozarani boshqaradi", "ichki doirada bahslashadi yoki kuzatadi", ["mustahkamlash", "birlashtirish"], guruh=True),
         B("Yakun, refleksiya, topshiriq", 10, "umumlashtiradi, keyingi topshiriqni beradi", "refleksiya qiladi", ["refleksiya"])]},
]

# ---------------------------------------------------------------- 4. metodlar katalogi
def M(kod, nom, tur, yosh, fan, vaqt, shakl, qadamlar, natija, ehtiyot="", jihoz=""):
    return {"kod": kod, "nom": nom, "tur": tur, "yosh": yosh, "fan": fan, "vaqt": vaqt, "shakl": shakl,
            "qadamlar": qadamlar, "natija": natija, "ehtiyot": ehtiyot, "jihoz": jihoz}


TABIIY = ["tabiiy_fanlar", "fizika", "kimyo", "biologiya", "geografiya", "otm_tabiiy", "otm_aniq"]
ANIQ = ["matematika", "algebra", "geometriya", "fizika", "informatika", "otm_aniq"]
GUM = ["tarix", "huquq", "adabiyot", "tarbiya", "iqtisod", "otm_gumanitar", "otm_pedagogika"]
TIL = ["ingliz_tili", "rus_tili", "otm_til"]

METODLAR = [
    # --- motivatsiya, faollashtirish
    M("aqliy_hujum", "Aqliy hujum", ["motivatsiya", "yangi_bilim"], oraliq("3-4", "m"), "*", [3, 7], "jamoa",
      ["muammo yoki savol e’lon qilinadi", "2–3 daqiqa davomida barcha g‘oyalar tanqidsiz yoziladi", "g‘oyalar guruhlanadi",
       "eng asoslilari tanlanadi va mavzuga ko‘prik qilinadi"], "faollik, mavzuga qiziqish, g‘oyalar ko‘pligi",
      "baholash g‘oyalar yig‘ilgandan keyin; bir-ikki o‘quvchi ustunlik qilmasin"),
    M("muammoli_vaziyat", "Muammoli vaziyat (muammoli savol)", ["motivatsiya", "yangi_bilim"], oraliq("3-4", "m"), "*", [3, 5], "jamoa",
      ["hayotiy, ziddiyatli savol yoki hodisa ko‘rsatiladi", "o‘quvchilar taxmin qiladi, taxminlar doskaga yoziladi",
       "dars davomida javob izlanadi", "dars oxirida taxminlarga qaytiladi"], "o‘rganishga ichki ehtiyoj, maqsadni o‘quvchi o‘zi aniqlaydi"),
    M("bbb", "«Bilaman — Bilishni xohlayman — Bilib oldim» (BBB)", ["motivatsiya", "refleksiya"], oraliq("3-4", "b1-2"), "*", [5, 8], "yakka",
      ["uch ustunli jadval chiziladi", "dars boshida 1- va 2-ustun to‘ldiriladi", "dars oxirida 3-ustun to‘ldiriladi",
       "2- va 3-ustun taqqoslanadi"], "dars boshi va oxirini bog‘laydi, o‘z o‘sishini ko‘radi", jihoz="jadval varag‘i"),
    M("sirli_quti", "«Sirli quti»", ["motivatsiya"], ["1-2", "3-4"], "*", [2, 4], "jamoa",
      ["qutiga mavzuga oid buyum yoki rasm solinadi", "o‘quvchilar faqat «ha/yo‘q» javobli savollar bilan topishga urinadi",
       "quti ochiladi, mavzu e’lon qilinadi"], "qiziqish, diqqatni jamlash", jihoz="quti, buyum"),
    M("topishmoq", "Topishmoq yoki rebus", ["motivatsiya", "oyin"], ["1-2", "3-4", "5-6"], "*", [2, 3], "jamoa",
      ["topishmoq yoki rebus ko‘rsatiladi", "javob — mavzuning kalit so‘zi", "kalit so‘z bilan mavzuga o‘tiladi"], "qiziqish, mantiq"),
    M("bashorat_kuzatish", "«Bashorat — kuzatish — tushuntirish»", ["motivatsiya", "yangi_bilim", "tadqiqot"], oraliq("3-4", "b1-2"), TABIIY, [8, 12], "juft",
      ["vaziyat yoki tajriba sharti ko‘rsatiladi", "o‘quvchilar natijani asoslab bashorat qiladi va yozadi",
       "tajriba yoki video kuzatiladi", "bashorat va natija farqi tushuntiriladi"], "ilmiy fikrlash, xato tasavvurlarni tuzatish",
      "tajriba oldindan sinab ko‘rilsin", "tajriba jihozlari yoki video"),
    M("ha_yoq", "«Ha — yo‘q» (to‘g‘ri / noto‘g‘ri bayonotlar)", ["motivatsiya", "takrorlash", "nazorat"], MAKTAB, "*", [3, 5], "jamoa",
      ["5–7 bayonot o‘qiladi", "o‘quvchilar yashil (ha) yoki qizil (yo‘q) kartochka ko‘taradi",
       "noto‘g‘ri bayonotlar birga tuzatiladi"], "tezkor diagnostika — kim nimani bilmasligi darhol ko‘rinadi", jihoz="ikki rangli kartochka"),
    M("kun_hikmati", "Kun hikmati / dars shiori", ["motivatsiya"], MAKTAB, "*", [1, 2], "jamoa",
      ["mavzuga oid hikmat, maqol yoki shior ekranga chiqariladi", "ma’nosi 1–2 jumlada muhokama qilinadi"], "tarbiyaviy kayfiyat"),
    M("warm_up", "Warm-up (qizdiruvchi til o‘yini)", ["motivatsiya", "energizer"], HAMMA, TIL, [3, 5], "juft",
      ["«Find someone who», «Lie detector», qo‘shiq yoki chant tanlanadi", "o‘quvchilar maqsadli tilda qisqa muloqot qiladi"],
      "til muhitiga kirish, faollik"),
    M("video_lavha", "Qisqa video yoki rasm lavha", ["motivatsiya"], HAMMA, "*", [2, 3], "jamoa",
      ["1 daqiqalik video yoki rasm ko‘rsatiladi", "«Nimani ko‘rdingiz? Qanday savol tug‘ildi?» deb so‘raladi"], "mavzuga ko‘prik", jihoz="proyektor"),
    # --- takrorlash
    M("zanjir", "«Zanjir» (bo‘g‘inlar zanjiri)", ["takrorlash", "oyin"], oraliq("1-2", "7-9"), "*", [4, 6], "jamoa",
      ["birinchi o‘quvchi tushuncha yoki javob aytadi", "keyingisi unga bog‘liq tushuncha yoki keyingi qadamni aytadi",
       "zanjir uzilsa, sinf yordam beradi"], "tushunchalar orasidagi bog‘lanish"),
    M("domino", "Domino", ["takrorlash", "oyin"], oraliq("1-2", "5-6"), ["matematika", "ona_tili", "oqish", "ingliz_tili", "tabiiy_fanlar"], [5, 7], "guruh",
      ["kartochkaning bir tomonida savol, ikkinchisida boshqa savolning javobi", "kartochkalar to‘g‘ri ulanib zanjir hosil qilinadi"],
      "tez takrorlash, o‘z-o‘zini tekshirish", jihoz="domino kartochkalari"),
    M("matematik_diktant", "Matematik diktant", ["takrorlash", "nazorat"], oraliq("3-4", "10-11"), ["matematika", "algebra", "geometriya", "fizika"], [5, 7], "yakka",
      ["6–10 qisqa topshiriq og‘zaki o‘qiladi", "o‘quvchilar faqat javobni yozadi", "kalit ekranda ko‘rsatiladi, juftlikda tekshiriladi"],
      "hisoblash va qoidalarni tez takrorlash"),
    M("blits", "Blits-so‘rov (tezkor so‘rov)", ["takrorlash", "nazorat"], oraliq("3-4", "m"), "*", [3, 5], "jamoa",
      ["tez savollar beriladi", "javoblar qisqa", "to‘g‘ri javobga ball yoki rag‘bat"], "bilimni tez faollashtirish"),
    M("xatoni_top", "«Xatoni top»", ["takrorlash", "mustahkamlash"], oraliq("3-4", "b1-2"),
      ["matematika", "algebra", "geometriya", "fizika", "kimyo", "ona_tili", "ingliz_tili", "rus_tili", "informatika", "otm_aniq", "otm_til"], [4, 6], "juft",
      ["atayin xato qilingan yechim yoki matn beriladi", "juftlik xatoni topadi va tuzatadi", "xato sababi tushuntiriladi"],
      "tanqidiy tahlil, tipik xatolarning oldini olish"),
    M("bumerang", "«Bumerang»", ["takrorlash", "mustahkamlash"], oraliq("5-6", "b3-4"), "*", [10, 15], "guruh",
      ["matn yoki mavzu qismlari guruhlarga beriladi", "guruhlar o‘rganib, boshqa guruhga savollar tuzadi",
       "savollar «otiladi» va javoblar qaytadi", "javoblar baholanadi"], "o‘zaro o‘rganish, savol tuzish ko‘nikmasi"),
    M("intervyu", "Intervyu", ["takrorlash"], oraliq("3-4", "10-11"), "*", [5, 7], "juft",
      ["juftlikda biri «jurnalist», biri «olim»", "jurnalist mavzu bo‘yicha savol beradi", "rollar almashadi"], "nutq, savol berish ko‘nikmasi"),
    M("ortiqchasini_top", "«Ortiqchasini top»", ["takrorlash", "oyin"], oraliq("1-2", "7-9"), "*", [3, 4], "jamoa",
      ["4–5 tushunchadan biri boshqalarga mos emas", "o‘quvchilar ortiqchasini topadi va sababini aytadi"], "tasniflash, mantiq"),
    M("men_kimman", "«Men kimman?»", ["takrorlash", "oyin"], oraliq("1-2", "7-9"), "*", [4, 6], "jamoa",
      ["o‘quvchi tushuncha, shaxs yoki obyekt «rolida» o‘zini tasvirlaydi", "boshqalar uni topadi"], "tushuncha belgilarini mustahkamlash"),
    M("tarif_egasi", "«Ta’rif egasini top»", ["takrorlash"], oraliq("3-4", "7-9"), "*", [3, 5], "juft",
      ["atamalar va ta’riflar alohida kartochkalarda", "juftlik ularni moslashtiradi"], "atamalarni mustahkamlash", jihoz="kartochkalar"),
    # --- yangi bilim
    M("insert", "Insert (belgilash: ✓ + − ?)", ["yangi_bilim"], oraliq("5-6", "m"), "*", [8, 12], "yakka",
      ["matn o‘qiladi va belgilanadi: ✓ bilardim, + yangi, − fikrimga zid, ? tushunmadim", "belgilar jadvalga yoziladi",
       "«?» belgilar juftlikda va sinfda muhokama qilinadi"], "matn bilan ongli ishlash", jihoz="matn"),
    M("klaster", "Klaster", ["yangi_bilim", "mustahkamlash", "birlashtirish"], HAMMA, "*", [5, 10], "guruh",
      ["markazga asosiy tushuncha yoziladi", "undan shoxlar — bog‘liq tushunchalar", "shoxlar orasidagi bog‘lanishlar ko‘rsatiladi",
       "guruh klasterini taqdim etadi"], "tushunchalar tizimi ko‘rinadi", "1–2-sinfda rasmli klaster", "plakat, flomaster"),
    M("mozaika", "«Mozaika» (Jigsaw, arra)", ["yangi_bilim", "guruh_ishi"], oraliq("5-6", "m"), "*", [15, 20], "guruh",
      ["mavzu 3–4 teng qismga bo‘linadi", "«uy» guruhlarida har a’zo bitta qismni oladi",
       "bir xil qism olganlar «ekspert» guruhida o‘rganadi", "ekspertlar uy guruhiga qaytib o‘rgatadi", "umumiy topshiriq yoki test"],
      "har bir o‘quvchi ham o‘rganuvchi, ham o‘rgatuvchi", "qismlar hajmi teng bo‘lsin, vaqt qat’iy", "4 xil matn"),
    M("kichik_maruza", "Kichik ma’ruza + tekshiruv savoli", ["yangi_bilim"], HAMMA, "*", [5, 8], "jamoa",
      ["3 ta tayanch fikr ko‘rgazma bilan bayon qilinadi", "har fikrdan keyin bitta tekshiruv savoli"], "asosiy bilim aniq yetkaziladi",
      "7–8 daqiqadan oshmasin (maktabda)"),
    M("evristik_suhbat", "Evristik suhbat", ["yangi_bilim"], oraliq("3-4", "b1-2"), "*", [8, 12], "jamoa",
      ["o‘qituvchi savollar zanjirini tuzadi", "har savol o‘quvchini keyingi xulosaga yetaklaydi", "qoida yoki formulani o‘quvchilar «kashf» qiladi"],
      "mustaqil xulosa chiqarish"),
    M("tajriba_namoyish", "Namoyish tajribasi", ["yangi_bilim"], oraliq("1-2", "b1-2"), ["tabiiy_fanlar", "fizika", "kimyo", "biologiya", "otm_tabiiy", "otm_aniq"], [5, 8], "jamoa",
      ["xavfsizlik qoidasi aytiladi", "kuzatish savollari beriladi", "tajriba ko‘rsatiladi", "xulosa birga chiqariladi"], "hodisani ko‘z bilan ko‘rish",
      "tajriba oldindan sinab ko‘rilsin", "tajriba jihozlari"),
    M("yonaltiruvchi_matn", "Yo‘naltiruvchi matn", ["yangi_bilim", "tadqiqot"], oraliq("7-9", "m"), "*", [10, 15], "juft",
      ["savollar va manba matni beriladi", "o‘quvchilar javoblarni matndan topadi", "o‘qituvchi maslahatchi"], "mustaqil o‘rganish"),
    M("venn", "Venn diagrammasi", ["yangi_bilim", "mustahkamlash"], oraliq("3-4", "m"), "*", [6, 10], "juft",
      ["ikki yoki uch tushuncha uchun kesishuvchi doiralar", "farqlar alohida, umumiy belgilar kesishmaga yoziladi"], "taqqoslash, tahlil"),
    M("t_jadval", "T-jadval", ["mustahkamlash"], oraliq("5-6", "m"), "*", [5, 8], "juft",
      ["jadvalning ikki ustuni: afzallik / kamchilik (yoki ha / yo‘q, sabab / oqibat)", "juftlik to‘ldiradi", "umumlashtiriladi"], "qarama-qarshi tomonlarni tahlil"),
    M("baliq_skeleti", "«Baliq skeleti» (sabab — oqibat)", ["yangi_bilim", "mustahkamlash"], oraliq("5-6", "m"),
      ["tarix", "biologiya", "geografiya", "huquq", "adabiyot", "fizika", "kimyo", "tarbiya", "iqtisod", "otm_gumanitar", "otm_pedagogika", "otm_tabiiy"], [8, 12], "guruh",
      ["baliq boshiga muammo yoziladi", "yuqori suyaklarga sabablar, pastki suyaklarga dalillar", "yechim yoki xulosa yoziladi"], "sabab-oqibat tafakkuri"),
    M("konseptual_jadval", "Konseptual jadval", ["mustahkamlash"], oraliq("7-9", "m"), "*", [8, 12], "guruh",
      ["tushunchalar qatorlarga, taqqoslash mezonlari ustunlarga yoziladi", "guruh jadvalni to‘ldiradi", "xulosa chiqariladi"], "tizimli taqqoslash"),
    M("nima_uchun", "«Nima uchun?» sxemasi", ["yangi_bilim"], oraliq("5-6", "b3-4"), "*", [6, 8], "juft",
      ["muammo yoziladi", "«Nima uchun?» savoli bilan sabablar zanjiri tuziladi", "ildiz sabab aniqlanadi"], "chuqur tahlil"),
    M("xronologik_lenta", "Xronologik lenta", ["yangi_bilim", "mustahkamlash"], oraliq("5-6", "b3-4"), ["tarix", "adabiyot", "huquq", "otm_gumanitar"], [6, 10], "guruh",
      ["sana va voqea kartochkalari beriladi", "guruh ularni lentaga joylaydi", "davrlar rang bilan ajratiladi", "lenta bo‘yicha savollar"],
      "voqealar ketma-ketligi va davrlar"),
    M("manba_tahlili", "Birlamchi manba bilan ishlash", ["yangi_bilim", "tadqiqot"], oraliq("5-6", "m"), ["tarix", "huquq", "adabiyot", "otm_gumanitar"], [10, 15], "guruh",
      ["manba parchasi beriladi", "kim, qachon, nima uchun yozgan — aniqlanadi", "ishonchliligi baholanadi", "xulosa chiqariladi"], "tarixiy tafakkur, manbashunoslik"),
    M("kontur_xarita", "Kontur xarita bilan ishlash", ["mustahkamlash", "amaliy"], oraliq("5-6", "10-11"), ["geografiya", "tarix"], [8, 12], "juft",
      ["topshiriq ro‘yxati beriladi", "obyektlar xaritaga belgilanadi", "atlas bilan tekshiriladi"], "makoniy tasavvur", jihoz="kontur xarita, atlas"),
    M("ppp", "PPP (Presentation — Practice — Production)", ["yangi_bilim"], HAMMA, TIL, [25, 30], "jamoa",
      ["Presentation: yangi til birligi kontekstda", "Practice: boshqariladigan mashqlar", "Production: erkin muloqot topshirig‘i"],
      "til birligini bosqichma-bosqich egallash"),
    M("tpr", "TPR (harakat bilan javob)", ["yangi_bilim", "energizer"], ["1-2", "3-4", "5-6"], ["ingliz_tili", "rus_tili"], [3, 6], "jamoa",
      ["o‘qituvchi buyruq beradi va ko‘rsatadi", "o‘quvchilar harakat bilan bajaradi", "keyin o‘quvchilar o‘zi buyruq beradi"], "so‘zlarni harakat orqali eslab qolish"),
    M("modellashtirish", "Modellashtirish (sxema, chizma, model)", ["yangi_bilim", "mustahkamlash"], HAMMA,
      ["matematika", "algebra", "geometriya", "fizika", "kimyo", "biologiya", "informatika", "texnologiya", "otm_aniq", "otm_tabiiy", "otm_it"], [8, 15], "juft",
      ["masala sharti sxema, chizma yoki modelga aylantiriladi", "model asosida yechim topiladi", "natija shartga qaytib tekshiriladi"],
      "masalani tushunish va yechish ko‘nikmasi"),
    M("namunaviy_yechim", "Namunaviy yechim tahlili", ["yangi_bilim", "amaliy"], oraliq("3-4", "b1-2"),
      ["matematika", "algebra", "geometriya", "fizika", "kimyo", "informatika", "texnologiya", "tasviriy", "chizmachilik", "otm_aniq"], [6, 10], "jamoa",
      ["o‘qituvchi ovoz chiqarib fikrlab namunani bajaradi", "o‘xshash topshiriq juftlikda", "uchinchisi mustaqil"], "algoritmni egallash"),
    M("zinama_zina", "«Zinama-zina»", ["yangi_bilim", "mustahkamlash"], oraliq("3-4", "10-11"), "*", [8, 12], "guruh",
      ["topshiriqlar oddiydan murakkabga «zina» qilib beriladi", "har zina to‘g‘ri bajarilsa keyingisiga o‘tiladi"], "bosqichma-bosqich o‘sish"),
    M("tadqiqot_mini", "Kichik tadqiqot (mini-loyiha)", ["tadqiqot"], oraliq("3-4", "m"), "*", [15, 25], "guruh",
      ["tadqiqot savoli qo‘yiladi", "gipoteza", "ma’lumot yig‘ish yoki o‘lchash", "xulosa va taqdimot"], "tadqiqotchilik ko‘nikmasi"),
    M("keys", "Keys-stadi", ["mustahkamlash", "tadqiqot"], oraliq("7-9", "m"), "*", [15, 25], "guruh",
      ["real yoki modellashtirilgan vaziyat matni beriladi", "muammo aniqlanadi", "yechim variantlari ishlab chiqiladi",
       "eng maqbuli tanlanib asoslanadi", "taqdimot va muhokama"], "bilimni real vaziyatda qo‘llash", jihoz="keys matni"),
    M("teskari_sinf", "Teskari sinf (flipped classroom)", ["yangi_bilim"], oraliq("10-11", "m"), "*", [30, 40], "guruh",
      ["uyda video yoki matn orqali nazariya o‘rganiladi", "darsda savollar aniqlanadi", "dars vaqti amaliy qo‘llashga sarflanadi"],
      "dars vaqtidan faol ishlash uchun foydalanish", "uy topshirig‘i bajarilganini tekshirish kerak"),
    M("loyiha", "O‘quv loyihasi (himoya)", ["tadqiqot", "birlashtirish"], oraliq("3-4", "m"), "*", [15, 20], "guruh",
      ["loyiha oldindan bajariladi", "darsda himoya: muammo, jarayon, natija", "savol-javob, mezon bilan baholash"], "amaliy natija, hamkorlik"),
    # --- mustahkamlash, o'yin
    M("charxpalak", "«Charxpalak»", ["mustahkamlash", "guruh_ishi"], oraliq("5-6", "b3-4"), "*", [10, 12], "guruh",
      ["har guruhga savollar yozilgan varaq beriladi", "varaqlar belgilangan vaqtda soat yo‘nalishida aylanadi",
       "har guruh javob qo‘shadi yoki oldingisini tekshiradi", "oxirida to‘g‘ri javoblar muhokama qilinadi"], "barcha guruhlar barcha savollarda ishlaydi"),
    M("galereya", "«Galereya sayri»", ["mustahkamlash", "birlashtirish"], oraliq("3-4", "m"), "*", [8, 12], "guruh",
      ["guruhlar natijasini plakatga tushiradi", "plakatlar devorga ilinadi", "guruhlar aylanib izoh va savol stikerlarini qoldiradi",
       "muallif guruhlar javob beradi"], "o‘zaro baholash, umumiy ko‘rgazma", jihoz="plakat, stiker"),
    M("rolli_oyin", "Rolli o‘yin", ["mustahkamlash"], HAMMA, "*", [8, 15], "guruh",
      ["vaziyat va rollar taqsimlanadi", "tayyorgarlik 3–5 daqiqa", "ijro", "rol ichidan chiqib muhokama"], "bilimni vaziyatda qo‘llash, empatiya"),
    M("sahnalashtirish", "Sahnalashtirish (dramatizatsiya)", ["mustahkamlash"], oraliq("1-2", "7-9"), ["oqish", "adabiyot", "tarix", "ingliz_tili", "rus_tili", "tarbiya"], [8, 12], "guruh",
      ["parcha yoki voqea tanlanadi", "rollar taqsimlanadi", "qisqa sahna ko‘rsatiladi", "muhokama"], "matnni chuqur his qilish"),
    M("debat", "Debat", ["mustahkamlash"], oraliq("7-9", "m"), ["tarix", "huquq", "adabiyot", "biologiya", "geografiya", "ingliz_tili", "tarbiya", "iqtisod",
                                                           "otm_gumanitar", "otm_pedagogika", "otm_til", "otm_tabiiy"], [15, 25], "guruh",
      ["munozarali tezis e’lon qilinadi", "ikki jamoa: tasdiqlovchi va inkor etuvchi", "tartib: nutq — savol — raddiya — yakuniy nutq",
       "hakamlar mezon bilan baholaydi"], "dalillash, nutq madaniyati", "tezis aniq va teng imkoniyatli bo‘lsin"),
    M("fsmu", "FSMU (Fikr — Sabab — Misol — Umumlashtirish)", ["mustahkamlash", "refleksiya"], oraliq("7-9", "m"), "*", [8, 10], "yakka",
      ["savol beriladi", "o‘quvchi fikrini, sababini, misolini va umumlashtirishini yozadi", "guruhda muhokama"], "fikrni asoslash"),
    M("sinkveyn", "Sinkveyn", ["mustahkamlash", "refleksiya"], oraliq("3-4", "m"), "*", [5, 7], "juft",
      ["1-qator: mavzu (ot)", "2-qator: ikki sifat", "3-qator: uch fe’l", "4-qator: to‘rt so‘zli gap", "5-qator: bitta sinonim yoki xulosa so‘z"],
      "mavzuni ixcham umumlashtirish", "3-sinfda soddalashtirilgan holda"),
    M("kubik", "«Kubik»", ["mustahkamlash"], oraliq("3-4", "b1-2"), "*", [8, 10], "guruh",
      ["kubik yoqlarida: tasvirla, taqqosla, bog‘la, tahlil qil, qo‘lla, baho ber", "guruh kubikni tashlaydi",
       "tushgan yoq bo‘yicha topshiriqni bajaradi"], "mavzuni turli tomondan ko‘rish", jihoz="kubik"),
    M("estafeta", "Estafeta (topshiriqlar estafetasi)", ["mustahkamlash", "oyin", "birlashtirish"], MAKTAB, "*", [6, 10], "guruh",
      ["har a’zo topshiriqning bitta qadamini bajaradi", "natijani keyingi a’zoga uzatadi", "vaqt va to‘g‘rilik baholanadi"], "jamoaviy mas’uliyat"),
    M("breyn_ring", "Breyn-ring", ["mustahkamlash", "oyin", "nazorat"], oraliq("5-6", "b1-2"), "*", [10, 15], "guruh",
      ["savol beriladi", "jamoalar 1 daqiqa maslahatlashadi", "birinchi signal bergan jamoa javob beradi", "ball hisoblanadi"], "tezkor fikrlash, jamoaviylik"),
    M("zakovat", "«Zakovat» (intellektual o‘yin)", ["mustahkamlash", "oyin", "birlashtirish"], oraliq("7-9", "b3-4"), "*", [10, 15], "guruh",
      ["mavzuga oid mantiqiy savollar", "1 daqiqa muhokama", "javob kartochkaga yoziladi", "ball jadvali yuritiladi"], "mantiqiy va keng fikrlash"),
    M("mojizalar_maydoni", "«Mo‘jizalar maydoni»", ["oyin", "mustahkamlash"], oraliq("3-4", "7-9"), "*", [8, 12], "jamoa",
      ["mavzuning kalit so‘zi yashirin yoziladi", "savolga to‘g‘ri javob bergan harf ochadi", "so‘zni topgan g‘olib"], "qiziqarli takrorlash"),
    M("krossvord", "Krossvord", ["mustahkamlash"], oraliq("3-4", "7-9"), "*", [6, 10], "juft",
      ["mavzu atamalari bo‘yicha krossvord", "juftlikda yechiladi", "kalit so‘z topiladi"], "atamalarni mustahkamlash", jihoz="krossvord varag‘i"),
    M("loto", "Loto yoki bingo", ["oyin", "mustahkamlash"], oraliq("1-2", "5-6"), ["matematika", "ona_tili", "oqish", "ingliz_tili"], [6, 8], "yakka",
      ["o‘quvchida javoblar yozilgan karta", "o‘qituvchi savol yoki misol aytadi", "javobni topgan belgilaydi", "qator to‘lsa — «Loto!»"],
      "tez hisoblash yoki so‘z boyligi", jihoz="loto kartalari"),
    M("dokon", "«Do‘kon» (rolli matematik o‘yin)", ["oyin", "amaliy"], ["1-2", "3-4"], ["matematika"], [8, 10], "guruh",
      ["narxlar yozilgan buyumlar va pul modellari", "sotuvchi va xaridor rollari", "hisob-kitob va qaytim"], "hisoblashni hayot bilan bog‘lash"),
    M("labirint", "Labirint (to‘g‘ri javoblar yo‘li)", ["oyin", "mustahkamlash"], oraliq("1-2", "5-6"), "*", [5, 7], "juft",
      ["har kesishmada savol", "to‘g‘ri javob to‘g‘ri yo‘lga olib boradi", "chiqishda kalit so‘z yoki rasm"], "o‘z-o‘zini tekshirish"),
    M("juft_tekshirish", "Juftlikda tekshirish", ["mustahkamlash", "nazorat"], oraliq("3-4", "m"), "*", [3, 5], "juft",
      ["daftarlar almashtiriladi", "kalit bo‘yicha tekshiriladi", "xatoga izoh yoziladi"], "o‘zaro o‘rganish, mas’uliyat"),
    M("differensial", "Darajali (A/B/C) kartochkalar", ["mustahkamlash", "amaliy"], oraliq("3-4", "b1-2"), "*", [10, 15], "yakka",
      ["uch daraja topshiriq: A — asosiy, B — qo‘llash, C — ijodiy", "o‘quvchi darajani tanlaydi yoki o‘qituvchi beradi", "har daraja mezoni ochiq"],
      "har kim o‘z darajasida o‘sadi", "kuchsizlarni ommaviy ajratmaslik"),
    M("stansiyalar", "Stansiyalar (rotatsiya)", ["mustahkamlash", "amaliy", "birlashtirish"], oraliq("1-2", "b1-2"), "*", [15, 20], "guruh",
      ["3–4 stansiya: o‘qish, hisoblash, tajriba, o‘yin", "har stansiyada 4–5 daqiqa", "signal bilan almashinadi", "marshrut varag‘ida ball"],
      "turli faoliyat, harakat, barcha guruhlar barcha topshiriqda", jihoz="stansiya kartochkalari, taymer"),
    M("akvarium", "«Akvarium»", ["mustahkamlash"], oraliq("10-11", "m"), "*", [15, 20], "guruh",
      ["ichki doira muammoni muhokama qiladi", "tashqi doira kuzatib, mezon bo‘yicha baholaydi", "doiralar almashadi", "umumiy xulosa"],
      "muhokama madaniyati, tahlil"),
    M("sokratik", "Sokratik suhbat (seminar)", ["yangi_bilim", "mustahkamlash"], oraliq("10-11", "m"), "*", [15, 25], "jamoa",
      ["ochiq savol qo‘yiladi", "ishtirokchilar dalil bilan javob beradi", "savollar orqali tushuncha chuqurlashtiriladi"], "tanqidiy fikrlash"),
    M("mikrodars", "Mikrodars (mikroo‘qitish)", ["amaliy"], ["b3-4", "m"], ["otm_metodika", "otm_pedagogika"], [20, 30], "guruh",
      ["talaba 5–10 daqiqalik dars parchasini o‘tadi", "video yoziladi yoki kuzatuv varag‘i to‘ldiriladi", "guruh fikr bildiradi", "talaba qayta o‘tadi"],
      "o‘qituvchilik ko‘nikmasi"),
    M("jurnal_klubi", "Jurnal klubi (maqola tahlili)", ["tadqiqot"], ["b3-4", "m"], "*", [20, 30], "guruh",
      ["maqola oldindan o‘qiladi", "ma’ruzachi qisqa bayon qiladi", "metodologiya va xulosalar tanqidiy muhokama qilinadi", "o‘z tadqiqotiga xulosa"],
      "ilmiy tahlil"),
    M("juft_dasturlash", "Juftlikda dasturlash", ["amaliy"], oraliq("7-9", "b3-4"), ["informatika", "otm_it"], [15, 25], "juft",
      ["«haydovchi» kod yozadi, «navigator» kuzatib yo‘naltiradi", "har 5–7 daqiqada rollar almashadi"], "kod sifati, hamkorlik"),
    M("unplugged", "Kompyutersiz informatika (unplugged)", ["yangi_bilim", "oyin"], oraliq("1-2", "5-6"), ["informatika", "matematika"], [8, 10], "guruh",
      ["algoritm kartochka yoki harakat bilan bajariladi", "«robot» va «dasturchi» rollari"], "algoritmik fikrlash"),
    # --- nazorat, refleksiya, energizer
    M("test_interaktiv", "Interaktiv test (Kahoot, Quizizz, Plickers yoki qog‘oz)", ["nazorat"], oraliq("3-4", "m"), "*", [5, 8], "yakka",
      ["5–10 savollik test", "natija darhol ko‘rinadi", "eng ko‘p xato qilingan savol tahlil qilinadi"], "tezkor nazorat", jihoz="telefon yoki kartochka"),
    M("chiqish_chiptasi", "Chiqish chiptasi", ["nazorat", "refleksiya"], oraliq("3-4", "m"), "*", [2, 3], "yakka",
      ["kichik varaqqa bitta savol javobi va «nima tushunarsiz qoldi?»", "chiqishda topshiriladi", "keyingi dars shunga qarab rejalanadi"], "formativ ma’lumot"),
    M("svetofor", "Svetofor", ["refleksiya", "nazorat"], oraliq("1-2", "7-9"), "*", [1, 2], "jamoa",
      ["yashil — tushundim, sariq — qisman, qizil — yordam kerak", "o‘quvchilar kartochka ko‘taradi"], "tezkor fikr-mulohaza", jihoz="uch rangli kartochka"),
    M("smayliklar", "Smayliklar (kayfiyat shkalasi)", ["refleksiya"], ["1-2", "3-4"], "*", [1, 2], "jamoa",
      ["har o‘quvchi kayfiyatini smaylik bilan belgilaydi"], "hissiy refleksiya"),
    M("uch_ikki_bir", "«3 — 2 — 1»", ["refleksiya"], oraliq("5-6", "m"), "*", [3, 4], "yakka",
      ["3 ta yangi narsa", "2 ta qiziq narsa", "1 ta savol"], "o‘zlashtirishni anglash"),
    M("tugallanmagan_gap", "Tugallanmagan gaplar", ["refleksiya"], oraliq("3-4", "m"), "*", [2, 3], "yakka",
      ["«Bugun men bildimki…», «Menga qiyin bo‘ldi…», «Endi men qila olaman…»"], "refleksiya"),
    M("bilim_daraxti", "«Bilim daraxti»", ["refleksiya", "birlashtirish"], oraliq("1-2", "5-6"), "*", [3, 5], "jamoa",
      ["har o‘quvchi yoki guruh rangli barg yopishtiradi (yashil — tushundim, sariq — qisman, qizil — qiyin)", "daraxt ko‘rinishi umumlashtiriladi"],
      "jamoaviy natija ko‘rinadi", jihoz="daraxt plakati, barglar"),
    M("besh_barmoq", "«Besh barmoq»", ["refleksiya"], oraliq("1-2", "7-9"), "*", [2, 3], "yakka",
      ["katta barmoq — kayfiyat", "ko‘rsatkich — nimani o‘rgandim", "o‘rta — nima qiyin bo‘ldi", "nomsiz — kimga yordam berdim", "jimjiloq — yana nimani bilmoqchiman"],
      "ko‘p tomonlama refleksiya"),
    M("pmi", "PMI (Plyus — Minus — Qiziq)", ["refleksiya"], oraliq("7-9", "m"), "*", [3, 5], "yakka",
      ["darsning ijobiy, salbiy va qiziq tomonlari yoziladi"], "tanqidiy refleksiya"),
    M("dinamik_pauza", "Dinamik pauza (jismoniy daqiqa)", ["energizer"], ["1-2", "3-4", "5-6"], "*", [1, 2], "jamoa",
      ["mavzuga oid harakatli she’r yoki sanoq bilan 1–2 daqiqa harakat"], "charchoqni yozish, diqqatni tiklash"),
    M("barmoq_gimnastikasi", "Barmoq va ko‘z gimnastikasi", ["energizer"], ["1-2", "3-4"], "*", [1, 2], "jamoa",
      ["yozuvdan oldin barmoq mashqi", "ekrandan keyin ko‘z mashqi"], "yozuvga tayyorlash, ko‘z charchog‘ini olish"),
    M("mezonli_baholash", "Mezonli (formativ) baholash varag‘i", ["nazorat"], oraliq("3-4", "m"), "*", [2, 4], "yakka",
      ["mezonlar dars boshida e’lon qilinadi", "o‘quvchi o‘zini va guruhdoshini baholaydi", "o‘qituvchi izoh beradi"], "baholashning ochiqligi"),
]

# ---------------------------------------------------------------- 5. guruhlash, birlashtirish, rollar, ilovalar, baholash
GURUHLASH = [
    {"kod": "rangli_kartochka", "nom": "Rangli kartochka yoki stiker", "yosh": HAMMA, "qanday": "eshikda har o‘quvchiga rangli kartochka beriladi; bir rangdagilar bir guruh"},
    {"kod": "rasm_bolaklari", "nom": "Rasm bo‘laklari (puzzle)", "yosh": oraliq("1-2", "7-9"),
     "qanday": "mavzuga oid 3–4 rasm 4–6 bo‘lakka kesiladi; bo‘laklari birlashib rasm hosil qilganlar bir guruh; rasm guruh nomi bo‘ladi"},
    {"kod": "raqam_sanash", "nom": "Sanab chiqish (1-2-3-4)", "yosh": HAMMA, "qanday": "o‘quvchilar navbat bilan 1 dan N gacha sanaydi; bir xil raqamlilar bir guruh"},
    {"kod": "juft_moslash", "nom": "Savol — javob (so‘z — tarjima, formula — qiymat, sana — voqea) moslash", "yosh": oraliq("3-4", "m"),
     "qanday": "kartochkaning mosini topganlar juft bo‘ladi, juftlar birlashib guruh hosil qiladi — guruhlash takrorlashga aylanadi"},
    {"kod": "tushuncha_oilasi", "nom": "Tushunchalar oilasi", "yosh": oraliq("3-4", "10-11"),
     "qanday": "har o‘quvchiga tushuncha kartochkasi (masalan: kasr, foiz, ulush…); bir turkumga kiruvchilar o‘zini topadi"},
    {"kod": "oldindan_tuzilgan", "nom": "Oldindan tuzilgan aralash guruhlar", "yosh": HAMMA,
     "qanday": "o‘qituvchi har guruhga kuchli, o‘rta va yordamga muhtoj o‘quvchilarni teng taqsimlaydi; ochiq dars uchun eng ishonchli usul"},
    {"kod": "qiziqish_tanlovi", "nom": "Qiziqish bo‘yicha tanlov", "yosh": oraliq("3-4", "m"),
     "qanday": "topshiriq turlari e’lon qilinadi (tadqiqotchilar, rassomlar, muxbirlar, hisobchilar); o‘quvchi o‘zi tanlaydi"},
    {"kod": "tasodifiy_dastur", "nom": "Ekranda tasodifiy guruhlash", "yosh": oraliq("5-6", "m"), "qanday": "ro‘yxat tasodifiy guruhlovchi dasturga kiritiladi, natija ekranda"},
    {"kod": "darajali", "nom": "Darajali guruhlar (A/B/C)", "yosh": oraliq("5-6", "m"),
     "qanday": "topshiriq darajasiga qarab guruhlanadi", "ehtiyot": "ochiq darsda kuchsizlarni alohida guruhga ajratmaslik; faqat qisqa vaqt uchun"},
]

GURUH_QOIDALARI = {
    "soni": [{"guruh": 2, "qachon": "bellashuv, debat, breyn-ring; 1–2-sinf yoki kichik sinf"},
             {"guruh": 3, "qachon": "mavzuning uch jihati yoki uch daraja; 15–24 o‘quvchi"},
             {"guruh": 4, "qachon": "mozaika (4 qism), stansiyalar; 24–32 o‘quvchi"}],
    "hajm": "guruhda 4–6 o‘quvchi (1–2-sinfda 4–5, OTMda 5–7)",
    "rollar": [{"rol": "sardor", "vazifa": "ishni taqsimlaydi, guruh nomidan gapiradi"}, {"rol": "kotib", "vazifa": "javoblarni yozadi"},
               {"rol": "so‘zlovchi", "vazifa": "taqdimot qiladi"}, {"rol": "vaqt nazoratchisi", "vazifa": "taymerni kuzatadi"},
               {"rol": "tekshiruvchi", "vazifa": "javoblarni tekshiradi, materiallar uchun mas’ul"}],
    "rollar_kichik": "1–2-sinfda faqat sardor va yordamchi",
    "guruh_nomlari": ["mavzu tushunchalaridan (masalan «Kasrlar»: «Surat», «Maxraj», «Butun qism»)",
                      "fan olimlari yoki mavzuga oid shaxslar nomidan", "1–2-sinfda hayvon, meva, rang nomlari"],
    "qoidalar": ["bir-birini tinglaymiz, gapni bo‘lmaymiz", "hamma ishtirok etadi", "yordam so‘rash va berish — odatiy hol",
                 "vaqtga rioya qilamiz", "tanqid ishga qaratiladi, odamga emas"],
}

BIRLASHTIRISH = [
    {"kod": "mozaika_rasm", "nom": "Mozaika: umumiy rasmni yig‘ish", "yosh": oraliq("1-2", "7-9"),
     "qanday": "har guruh to‘g‘ri javoblari uchun rasm (xarita, formula, maqol) bo‘lagini oladi; oxirida barcha bo‘laklar birlashib yaxlit rasm hosil qiladi va u mavzuning xulosasi bo‘ladi"},
    {"kod": "umumiy_klaster", "nom": "Umumiy klaster", "yosh": oraliq("3-4", "m"),
     "qanday": "har guruh klasterning bitta shoxini tayyorlaydi; doskada barcha shoxlar bitta markaziy tushunchaga ulanadi"},
    {"kod": "bilim_daraxti", "nom": "Bilim daraxti", "yosh": oraliq("1-2", "5-6"), "qanday": "har guruh o‘rgangan bilimini barg yoki meva ko‘rinishida daraxtga ilib qo‘yadi"},
    {"kod": "xazina_sandigi", "nom": "Xazina sandig‘i", "yosh": oraliq("1-2", "5-6"),
     "qanday": "har guruh topshiriqni bajarib kodning bitta raqamini oladi; faqat barcha raqamlar bilan sandiq (konvert) ochiladi, ichida — rag‘bat va yakuniy savol"},
    {"kod": "jamoaviy_masala", "nom": "Jamoaviy masala", "yosh": oraliq("5-6", "m"),
     "qanday": "katta masala qismlarga bo‘linadi; har guruh bir qismni yechadi; yakuniy javob faqat barcha guruh natijalari bilan chiqadi"},
    {"kod": "galereya_yakun", "nom": "Umumiy ko‘rgazma (galereya)", "yosh": oraliq("3-4", "m"), "qanday": "guruh plakatlari bitta ko‘rgazmaga birlashadi, sinf umumiy xulosani tuzadi"},
    {"kod": "ekspertlar_estafetasi", "nom": "Ekspertlar estafetasi", "yosh": oraliq("5-6", "10-11"),
     "qanday": "har guruhdan bittadan o‘quvchi yangi aralash jamoa tuzadi; final topshiriqlar estafeta tarzida bajariladi"},
    {"kod": "sinf_mehmonlarga_qarshi", "nom": "«Sinf — mehmonlarga qarshi»", "yosh": oraliq("5-6", "b1-2"),
     "qanday": "barcha guruhlar bitta jamoa bo‘lib mehmonlar yoki o‘qituvchi bergan savollarga javob beradi (yoki aksincha — mehmonlarga savol beradi)"},
    {"kod": "umumiy_loyiha", "nom": "Umumiy loyiha", "yosh": oraliq("5-6", "m"),
     "qanday": "har guruh loyihaning bir qismini (masalan «Ideal shahar»: transport, ekologiya, iqtisod) tayyorlaydi; oxirida bitta maket yoki taqdimotga birlashadi"},
    {"kod": "jamoaviy_sinkveyn", "nom": "Jamoaviy sinkveyn", "yosh": oraliq("3-4", "10-11"), "qanday": "har guruh sinkveynning bitta qatorini yozadi, sinf yagona sinkveyn tuzadi"},
    {"kod": "davra_shior", "nom": "Davra va umumiy shior", "yosh": ["1-2", "3-4"], "qanday": "barcha o‘quvchilar davra bo‘lib dars shiorini yoki mavzuga oid qo‘shiqni birga aytadi"},
    {"kod": "konsensus", "nom": "Konsensus xaritasi", "yosh": oraliq("10-11", "m"), "qanday": "guruhlar takliflaridan umumiy qaror yoki model tuziladi; har guruh hissasi ko‘rinadi"},
]

ILOVALAR = [
    {"kod": "guruh_qoidalari", "nom": "Guruhda ishlash qoidalari"},
    {"kod": "baholash_varagi", "nom": "Baholash varag‘i: mezonlar va ball jadvali (guruh × bosqich)"},
    {"kod": "guruh_nomlari", "nom": "Guruh nomlari va belgilari (stol tablichkalari)"},
    {"kod": "tarqatma", "nom": "Guruhlar uchun tarqatma topshiriqlar"},
    {"kod": "oyin_kartochkalari", "nom": "O‘yin kartochkalari va javob kalitlari"},
    {"kod": "tayanch_konspekt", "nom": "Yangi mavzu bo‘yicha tayanch konspekt (matn, sxema)"},
    {"kod": "test", "nom": "Test (javob kaliti bilan)"},
    {"kod": "refleksiya_varagi", "nom": "Refleksiya varag‘i"},
    {"kod": "uy_vazifasi", "nom": "Darajali uy vazifasi (A/B/C)"},
    {"kod": "yoriqnoma_kartasi", "nom": "Yo‘riqnoma kartasi (amaliy yoki laboratoriya ishi tartibi, natijalar jadvali)"},
    {"kod": "xavfsizlik", "nom": "Xavfsizlik yo‘riqnomasi"},
    {"kod": "mehmon_varaqasi", "nom": "Mehmon varaqasi (fan, sinf, mavzu, metodik maqsad, dars algoritmi)"},
    {"kod": "kuzatuv_varagi", "nom": "Dars kuzatuv (tahlil) varag‘i"},
    {"kod": "ozini_tahlil", "nom": "O‘z-o‘zini tahlil rejasi"},
    {"kod": "adabiyotlar", "nom": "Adabiyotlar ro‘yxati (OTM)"},
]

BAHOLASH = {
    "ball_jadvali": "guruhlar × dars bosqichlari; har bosqichda maksimal ball oldindan e’lon qilinadi; yakunda o‘rinlar",
    "guruh_mezonlari": ["javobning to‘g‘riligi va to‘liqligi", "barcha a’zolarning ishtiroki", "hamkorlik va qoidalarga rioya",
                        "taqdimot (aniq, tushunarli)", "vaqtga rioya"],
    "laboratoriya_mezonlari": ["ish maqsadini to‘g‘ri va mustaqil belgilay olish", "nazariy bilimni qo‘llay olish", "tajribani to‘g‘ri bajarish",
                               "o‘lchash va hisoblash aniqligi", "xulosaning asoslanganligi", "ish joyida tartib va tejamkorlik",
                               "xavfsizlik qoidalariga rioya", "daftardagi yozuv, jadval, grafik to‘g‘riligi"],
    "formativ": "dars davomida kuzatish, natijani yaxshilash uchun izoh berish (svetofor, chiqish chiptasi, juftlikda tekshirish)",
    "summativ": "bob yoki chorak yakunidagi nazorat",
    "ragbat": "1–4-sinfda rag‘bat belgilari (yulduzcha, smaylik, token); yuqori sinflarda ball va og‘zaki izoh; OTMda joriy nazorat ballari va rubrika",
}

KOMPETENSIYALAR = {
    "tayanch": ["kommunikativ kompetensiya", "axborot bilan ishlash kompetensiyasi", "o‘zini o‘zi rivojlantirish kompetensiyasi",
                "ijtimoiy faol fuqarolik kompetensiyasi", "milliy va umummadaniy kompetensiya",
                "matematik savodxonlik, fan va texnika yangiliklaridan xabardor bo‘lish hamda foydalanish kompetensiyasi"],
    "4k": ["tanqidiy fikrlash", "kreativlik", "kommunikatsiya", "kollaboratsiya (hamkorlik)"],
    "steam": "fan, texnologiya, muhandislik, san’at va matematikani bitta amaliy topshiriqda bog‘lash",
}

# ---------------------------------------------------------------- 6. fanlar
def F(kod, nom, nomlar, yosh, andozalar, metodlar, xos, amaliy="", lab="", steam=""):
    return {"kod": kod, "nom": nom, "nomlar": nomlar, "yosh": yosh, "andozalar": andozalar, "metodlar": metodlar,
            "xos_usullar": xos, "amaliy_misol": amaliy, "laboratoriya": lab, "steam": steam}


ASOSIY = ["aralash_45", "ochiq_guruh_45", "takrorlash_45"]
KICHIK = ["aralash_45_kichik", "ochiq_guruh_45_kichik"]
OTM_A = ["maruza_80", "seminar_80", "amaliy_80", "ochiq_otm_80"]

FANLAR = [
    F("matematika", "Matematika", ["Matematika", "Algebra", "Geometriya", "algebra va analiz", "stereometriya"], MAKTAB, KICHIK + ASOSIY + ["amaliy_45"],
      ["matematik_diktant", "xatoni_top", "modellashtirish", "namunaviy_yechim", "zinama_zina", "differensial", "domino", "loto", "dokon", "labirint",
       "breyn_ring", "juft_tekshirish", "evristik_suhbat", "stansiyalar", "unplugged"],
      ["og‘zaki hisob (tezkor)", "manipulyativlar: cho‘plar, kubiklar, kasr doiralari (1–6-sinf)", "masala shartini sxema yoki jadvalga aylantirish",
       "GeoGebra bilan dinamik chizma", "isbot zanjiri (geometriya)", "hayotiy masalalar (PISA uslubida)", "o‘lchash va hisoblash amaliy ishi"],
      "masalalar yechish praktikumi, geometrik yasash, o‘lchash ishi", steam="o‘lchash, chizma, maket yasash, ma’lumotlar diagrammasi"),
    F("oqish", "O‘qish savodxonligi va alifbe", ["Alifbe", "O‘qish savodxonligi", "Ona tili va o‘qish savodxonligi", "Yozuv daftari", "Bolalar adabiyoti"],
      ["1-2", "3-4"], KICHIK + ASOSIY,
      ["sirli_quti", "topishmoq", "ortiqchasini_top", "domino", "loto", "sahnalashtirish", "klaster", "zanjir", "ha_yoq", "men_kimman", "labirint", "sinkveyn"],
      ["tovush-harf tahlili (tovush sxemasi)", "so‘zdan so‘z yasash", "ifodali va rolli o‘qish", "rasm asosida hikoya tuzish", "harf elementlarini havoda yozish"],
      "ifodali o‘qish, rasm asosida hikoya, harf yozish mashqi"),
    F("ona_tili", "Ona tili", ["Ona tili"], oraliq("3-4", "10-11"), ASOSIY + ["amaliy_45"],
      ["klaster", "insert", "sinkveyn", "xatoni_top", "venn", "zanjir", "tarif_egasi", "ortiqchasini_top", "zinama_zina", "differensial", "kubik"],
      ["grammatik tahlil zanjiri", "matn ustida ishlash (tahrir, qayta tuzish)", "lug‘at diktanti", "esse va bayon", "xatolar ustida ishlash"],
      "matn tahriri, ijodiy yozma ish"),
    F("adabiyot", "Adabiyot", ["Adabiyot"], oraliq("5-6", "10-11"), ASOSIY,
      ["sinkveyn", "insert", "sahnalashtirish", "rolli_oyin", "debat", "fsmu", "baliq_skeleti", "xronologik_lenta", "venn", "klaster", "kubik"],
      ["qahramon xaritasi (tavsif, xatti-harakat, sabab)", "«Muallifga xat»", "ifodali o‘qish va yod olish tanlovi", "asar g‘oyasi bo‘yicha munozara"],
      "insho, qahramon tavsifi, sahna ko‘rinishi"),
    F("ingliz_tili", "Ingliz tili (chet tili)", ["Ingliz tili", "Nemis tili", "Fransuz tili"], MAKTAB, ["xorijiy_til_45", "ochiq_guruh_45", "ochiq_guruh_45_kichik"],
      ["warm_up", "ppp", "tpr", "rolli_oyin", "mozaika", "loto", "domino", "galereya", "chiqish_chiptasi", "intervyu", "xatoni_top", "sahnalashtirish"],
      ["TTT va TBL (vazifaga asoslangan) dars ramkalari", "pre-, while-, post- reading/listening bosqichlari", "information gap", "running dictation",
       "board race", "qo‘shiq va chant (1–4-sinf)"], "muloqot topshirig‘i: dialog, rolli o‘yin, mini-loyiha"),
    F("rus_tili", "Rus tili", ["Rus tili"], MAKTAB, ["xorijiy_til_45", "ochiq_guruh_45"],
      ["warm_up", "ppp", "tpr", "rolli_oyin", "intervyu", "xatoni_top", "loto", "sahnalashtirish"],
      ["dialog asosida o‘rganish", "rasm bo‘yicha nutq", "lug‘at o‘yinlari"], "dialog tuzish"),
    F("tabiiy_fanlar", "Tabiiy fanlar", ["Tabiiy fanlar", "Atrofimizdagi olam", "Science"], oraliq("1-2", "5-6"), KICHIK + ASOSIY + ["laboratoriya_45"],
      ["bashorat_kuzatish", "tajriba_namoyish", "tadqiqot_mini", "klaster", "venn", "sirli_quti", "stansiyalar", "ortiqchasini_top", "bilim_daraxti"],
      ["kuzatish kundaligi", "«Nima bo‘ladi, agar…?» tadqiqot savoli", "tabiat burchagida tajriba", "ekskursiya va o‘lkashunoslik"],
      "oddiy tajribalar, kuzatish", "oddiy kuzatish va o‘lchash tajribalari", steam="tajriba + chizma + model + hisob"),
    F("fizika", "Fizika", ["Fizika", "Astronomiya"], oraliq("5-6", "10-11"), ASOSIY + ["laboratoriya_45", "amaliy_45"],
      ["bashorat_kuzatish", "tajriba_namoyish", "modellashtirish", "namunaviy_yechim", "xatoni_top", "matematik_diktant", "muammoli_vaziyat", "keys",
       "tadqiqot_mini", "breyn_ring", "konseptual_jadval"],
      ["masala yechish algoritmi (berilgan — formula — yechim — tekshirish)", "virtual laboratoriya (PhET kabi)", "grafik tahlili", "kundalik hayotdagi fizika"],
      "masala yechish praktikumi", "o‘lchash, jadval, grafik, xatolik hisobi; xavfsizlik yo‘riqnomasi majburiy", steam="qurilma yoki maket yasash"),
    F("kimyo", "Kimyo", ["Kimyo"], oraliq("7-9", "10-11"), ASOSIY + ["laboratoriya_45", "amaliy_45"],
      ["bashorat_kuzatish", "tajriba_namoyish", "modellashtirish", "xatoni_top", "estafeta", "venn", "keys", "krossvord", "breyn_ring"],
      ["reaksiya tenglamalari estafetasi", "molekula modellari", "davriy jadval o‘yinlari («Element kim?»)", "ekologik keys"],
      "masalalar, tenglamalar tuzish", "reaktivlar bilan ishlash qoidalari, himoya vositalari, kuzatish jadvali", steam="kundalik turmush kimyosi loyihasi"),
    F("biologiya", "Biologiya", ["Biologiya"], oraliq("5-6", "10-11"), ASOSIY + ["laboratoriya_45"],
      ["klaster", "venn", "baliq_skeleti", "rolli_oyin", "modellashtirish", "tajriba_namoyish", "tadqiqot_mini", "keys", "debat", "mozaika", "galereya"],
      ["mikroskop bilan ishlash", "gerbariy va kolleksiya", "kuzatish kundaligi", "organlar «suhbati» (rolli o‘yin)", "sog‘lom turmush keysi"],
      "kuzatish, gerbariy", "mikroskop, preparat tayyorlash, chizish va xulosa", steam="ekotizim maketi"),
    F("geografiya", "Geografiya", ["Geografiya", "Ekologiya"], oraliq("5-6", "10-11"), ASOSIY + ["amaliy_45"],
      ["kontur_xarita", "klaster", "venn", "baliq_skeleti", "keys", "rolli_oyin", "debat", "galereya", "mozaika", "loyiha"],
      ["xarita va atlas bilan ishlash", "virtual sayohat («Men — gid»)", "iqlim grafigi tahlili", "o‘lkashunoslik loyihasi"],
      "kontur xarita, iqlim grafigi, joy rejasi"),
    F("tarix", "Tarix", ["Tarix", "O‘zbekiston tarixi", "Jahon tarixi", "Tarixdan hikoyalar", "eng yangi tarixi"], oraliq("5-6", "10-11"), ASOSIY,
      ["xronologik_lenta", "manba_tahlili", "rolli_oyin", "sahnalashtirish", "debat", "venn", "baliq_skeleti", "kontur_xarita", "zakovat", "men_kimman", "mozaika"],
      ["tarixiy shaxs bilan «intervyu»", "voqea sabab-oqibati", "davrlarni taqqoslash", "muzey yoki virtual ekskursiya"],
      "xronologik jadval, xarita, manba tahlili"),
    F("huquq", "Huquq va tarbiya", ["Huquq", "Davlat va huquq asoslari", "Tarbiya", "Odobnoma", "Chaqiruvga qadar"], MAKTAB, ASOSIY + KICHIK,
      ["keys", "rolli_oyin", "debat", "fsmu", "klaster", "baliq_skeleti", "t_jadval", "sahnalashtirish", "galereya"],
      ["huquqiy vaziyat keysi", "«Sud jarayoni» rolli o‘yini", "qadriyatlar bo‘yicha munozara", "hayotiy vaziyatda to‘g‘ri tanlov"],
      "vaziyatli masalalar"),
    F("iqtisod", "Iqtisodiy bilim asoslari", ["Iqtisodiy bilim", "Iqtisod", "Moliyaviy savodxonlik"], oraliq("7-9", "10-11"), ASOSIY,
      ["keys", "rolli_oyin", "debat", "t_jadval", "baliq_skeleti", "loyiha"], ["oilaviy byudjet loyihasi", "bozor o‘yini", "biznes-reja"],
      "byudjet, hisob-kitob"),
    F("informatika", "Informatika va axborot texnologiyalari", ["Informatika", "Axborot texnologiyalari"], MAKTAB, ASOSIY + ["amaliy_45"],
      ["unplugged", "juft_dasturlash", "namunaviy_yechim", "xatoni_top", "modellashtirish", "loyiha", "zinama_zina", "test_interaktiv"],
      ["algoritm blok-sxemasi", "Scratch kabi bloklarda dasturlash", "debugging (xatoni topish)", "kompyuterda amaliy ish"],
      "kompyuterda amaliy topshiriq", steam="robototexnika, animatsiya, mini-o‘yin yaratish"),
    F("texnologiya", "Texnologiya", ["Texnologiya", "Mehnat"], MAKTAB, ["amaliy_45", "ochiq_guruh_45", "ochiq_guruh_45_kichik"],
      ["namunaviy_yechim", "loyiha", "galereya", "modellashtirish", "stansiyalar", "zinama_zina"],
      ["texnologik karta (ish bosqichlari)", "instruktaj: kirish, joriy, yakuniy", "buyum yasash", "ish joyi va asboblar xavfsizligi"],
      "buyum yasash (qog‘oz, mato, yog‘och)", steam="dizayn — maket — sinov"),
    F("tasviriy", "Tasviriy san’at", ["Tasviriy san’at", "Chizmachilik"], MAKTAB, ["amaliy_45", "ochiq_guruh_45", "ochiq_guruh_45_kichik"],
      ["namunaviy_yechim", "galereya", "klaster", "venn", "loyiha"],
      ["naturadan kuzatib chizish", "bosqichma-bosqich tasvirlash", "san’at asari tahlili", "kompozitsiya loyihasi"], "rasm, kompozitsiya"),
    F("musiqa", "Musiqa", ["Musiqa", "Musiqiy savodxonlik", "Musiqa madaniyati"], MAKTAB, ASOSIY + KICHIK,
      ["rolli_oyin", "klaster", "venn", "zakovat", "loto", "estafeta"],
      ["tinglash va tahlil", "kuylash, jo‘rnavozlik", "ritmik o‘yinlar", "«Kuyni top» o‘yini", "musiqiy viktorina"], "kuylash, ritm"),
    F("jismoniy", "Jismoniy tarbiya", ["Jismoniy tarbiya", "Jismoniy madaniyat"], MAKTAB, ["jismoniy_45"],
      ["estafeta", "stansiyalar"],
      ["frontal, guruhli, aylana (stansiya) usullari", "harakatli o‘yinlar", "yuklamani puls bilan nazorat qilish", "xavfsizlik"],
      "harakat texnikasi, me’yorlar"),
    # ---- OTM fan guruhlari
    F("otm_pedagogika", "OTM: pedagogika, psixologiya va umumkasbiy fanlar",
      ["Pedagogika", "Psixologiya", "Defektologiya", "Maktabgacha", "Kasbiy pedagogik mahorat", "Xalqaro baholash", "Magistratura fanlari", "Falsafa"],
      OTM, OTM_A + ["magistr_seminar_80"],
      ["keys", "rolli_oyin", "debat", "akvarium", "fsmu", "klaster", "venn", "konseptual_jadval", "mikrodars", "jurnal_klubi", "sokratik", "teskari_sinf"],
      ["pedagogik vaziyat keysi", "o‘qituvchi — o‘quvchi rolli o‘yini", "dars tahlili (video bo‘yicha)", "portfolio"], "pedagogik vaziyatlarni hal qilish"),
    F("otm_metodika", "OTM: fan o‘qitish metodikasi", ["metodika", "o‘qitish metodikasi"], OTM, OTM_A,
      ["mikrodars", "namunaviy_yechim", "keys", "rolli_oyin", "galereya", "mozaika", "loyiha", "jurnal_klubi"],
      ["dars ishlanmasi yaratish va himoyasi", "mahorat darsi", "maktab darsini kuzatish va tahlil", "lesson study (dars tadqiqi)"],
      "ishlanma yozish, mikrodars"),
    F("otm_aniq", "OTM: aniq fanlar", ["Matematika (bakalavr)", "Fizika (bakalavr)", "Boshlang‘ich matematika kursi nazariyasi", "Oliy matematika"],
      OTM, OTM_A + ["laboratoriya_80"],
      ["muammoli_vaziyat", "namunaviy_yechim", "modellashtirish", "xatoni_top", "keys", "juft_tekshirish", "teskari_sinf", "mozaika"],
      ["masala-praktikum", "isbot tahlili", "maktab masalalariga metodik yondashuv"], "masalalar yechish", "fizika laboratoriyasi"),
    F("otm_tabiiy", "OTM: tabiiy fanlar",
      ["Kimyo (bakalavr)", "Biologiya (bakalavr)", "Geografiya (bakalavr)", "Ekologiya va barqaror rivojlanish", "Tabiiy fanlar o‘qitish"],
      OTM, OTM_A + ["laboratoriya_80"], ["bashorat_kuzatish", "tajriba_namoyish", "keys", "baliq_skeleti", "debat", "loyiha", "jurnal_klubi"],
      ["virtual laboratoriya", "dala amaliyoti", "ekologik keys"], "laboratoriya va dala ishlari", "laboratoriya mashg‘uloti"),
    F("otm_gumanitar", "OTM: ijtimoiy-gumanitar fanlar", ["Tarix (bakalavr)", "Falsafa", "Huquq", "Milliy g‘oya", "Iqtisod"], OTM, OTM_A,
      ["manba_tahlili", "debat", "sokratik", "akvarium", "keys", "xronologik_lenta", "fsmu", "baliq_skeleti", "jurnal_klubi"],
      ["manbashunoslik tahlili", "esse", "konferensiya-seminar"], "manba tahlili, esse"),
    F("otm_til", "OTM: til va filologiya", ["Filologiya", "Ingliz tili (bakalavr)", "Ona tili va o‘qish savodxonligi metodikasi", "tillar"], OTM, OTM_A,
      ["ppp", "warm_up", "rolli_oyin", "mozaika", "debat", "xatoni_top", "mikrodars", "keys"],
      ["CLT va TBL", "matn lingvistik tahlili", "tarjima praktikumi"], "matn tahlili, tarjima"),
    F("otm_it", "OTM: axborot texnologiyalari", ["Informatika (bakalavr)", "Axborot texnologiyalari ta’limda", "Dasturlash"], OTM, OTM_A + ["laboratoriya_80"],
      ["juft_dasturlash", "namunaviy_yechim", "xatoni_top", "loyiha", "keys", "teskari_sinf"], ["hakaton", "kod tahlili (code review)", "raqamli ta’lim resursi yaratish"],
      "kompyuterda amaliy", "kompyuter laboratoriyasi"),
]


def tekshir(d):
    """Ichki moslik: vaqtlar yig‘indisi, metod va andoza havolalari, yosh kodlari."""
    xato = []
    m_kod = {m["kod"] for m in d["metodlar"]}
    a_kod = {a["kod"] for a in d["andozalar"]}
    turlar = set()
    for m in d["metodlar"]:
        turlar |= set(m["tur"])
        for y in m["yosh"]:
            if y not in HAMMA:
                xato.append(f"metod {m['kod']}: yosh {y}")
    for a in d["andozalar"]:
        s = sum(b["daq"] for b in a["bosqichlar"])
        if s != a["daqiqa"]:
            xato.append(f"andoza {a['kod']}: {s} != {a['daqiqa']}")
        for b in a["bosqichlar"]:
            for t in b["metod_turi"]:
                if t not in turlar | {"guruhlash", "birlashtirish"}:
                    xato.append(f"andoza {a['kod']}: metod_turi {t}")
            for i in b["ilova"]:
                if i not in {x["kod"] for x in d["ilovalar"]}:
                    xato.append(f"andoza {a['kod']}: ilova {i}")
    for f in d["fanlar"]:
        for k in f["metodlar"]:
            if k not in m_kod:
                xato.append(f"fan {f['kod']}: metod {k}")
        for k in f["andozalar"]:
            if k not in a_kod:
                xato.append(f"fan {f['kod']}: andoza {k}")
    f_kod = {f["kod"] for f in d["fanlar"]}
    for m in d["metodlar"]:
        if m["fan"] != "*":
            xato += [f"metod {m['kod']}: fan {k}" for k in m["fan"] if k not in f_kod]
    if len(m_kod) != len(d["metodlar"]):
        xato.append("takror metod kodi")
    return xato


OTA_FAN = {"algebra": "matematika", "geometriya": "matematika", "tarbiya": "huquq", "chizmachilik": "tasviriy"}


def _tozala():
    for m in METODLAR:
        if m["fan"] != "*":
            m["fan"] = list(dict.fromkeys(OTA_FAN.get(k, k) for k in m["fan"]))


def miya():
    _tozala()
    return {"versiya": "ochiq-dars-miya/1", "yosh_guruhlari": YOSH, "formatlar": FORMATLAR, "andozalar": ANDOZALAR,
            "metodlar": METODLAR, "guruhlash": GURUHLASH, "guruh_qoidalari": GURUH_QOIDALARI, "birlashtirish": BIRLASHTIRISH,
            "ilovalar": ILOVALAR, "baholash": BAHOLASH, "kompetensiyalar": KOMPETENSIYALAR, "fanlar": FANLAR}


if __name__ == "__main__":
    d = miya()
    print("xatolar:", tekshir(d) or "yo‘q")
    print({k: len(v) for k, v in d.items() if isinstance(v, list)})
