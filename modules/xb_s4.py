"""TIMSS 4-sinf fan: 11 mavzu (S4-*), fakt banklari + hisoblash shablonlari."""
from fractions import Fraction

from modules.pisa_mat_g import reg, num, _y, _o, _yopiq, fig_stolbik
from modules.xb_ps import _fakt, _d

TOP = "T11_G4_S"

def _tema(kod, nom, belgi, maqsad, dars):
    return {"nom": nom, "soha": "Fan", "belgi": belgi, "maqsad": maqsad, "bolim": kod, "toplam": TOP, "dars": dars}

def _b(sv, tj, no, iz=""):
    return (sv, tj, no, iz or f"To‘g‘ri javob: {tj}.")

_fakt("S4-TIR", [
    _b("Quyidagilardan qaysi biri tirik organizm?", "Qo‘ziqorin", ["Tosh", "Suv", "Havo"], "Qo‘ziqorin ovqatlanadi, o‘sadi va ko‘payadi."),
    _b("Qaysi hayvon umurtqali?", "Baliq", ["Qurt", "Hasharot", "Salyangoz"], "Baliqlarda umurtqa pog‘onasi bor."),
    _b("Qaysi hayvon sutemizuvchi?", "Ot", ["Burgut", "Kaltakesak", "Baliq"], "Sutemizuvchilar bolalarini sut bilan boqadi."),
    _b("O‘simlik ildizining vazifasi nima?", "Suv va mineral moddalarni so‘rish", ["Urug‘ hosil qilish", "Nur yutish", "Gul ochish"], "Ildiz o‘simlikni mahkamlaydi va suv so‘radi."),
    _b("Barg qaysi jarayonda ishtirok etadi?", "Fotosintez", ["Hazm", "Ko‘payish faqat", "Uxlash"], "Bargda yorug‘likdan oziq hosil bo‘ladi."),
    _b("O‘txo‘r hayvon tishlari qanday bo‘ladi?", "Yassi, maydalovchi tishlar", ["Uzun o‘tkir tishlar", "Tishsiz", "Faqat kemiruvchi emas"], "O‘tni maydalash uchun yassi tishlar kerak."),
    _b("Qaysi tirik organizm nafas olish uchun o‘pkadan foydalanadi?", "Qush", ["Baliq (jabra)", "Qurt faqat teri", "Qo‘ziqorin"], "Qushlar o‘pka bilan nafas oladi."),
    _b("Qaysi guruhga ari kiradi?", "Hasharotlar", ["Sutemizuvchilar", "Baliqlar", "Qushlar"], "Hasharotlarning 6 oyog‘i bor."),
    _b("Tirik organizmlarning umumiy belgisi qaysi?", "Ko‘payish", ["Rangi", "Og‘irligi katta", "Tez yuguradi"], "Barcha tirik organizm ko‘payadi."),
    _b("Qaysi hayvon sovuq qonli?", "Kaltakesak", ["Mushuk", "Ot", "Qush"], "Sudralib yuruvchilar tana haroratini o‘zi saqlamaydi."),
    _b("Qaysi biri yirtqich hayvonning belgisi?", "O‘tkir qoziq tishlar", ["Yassi tishlar", "Tishsizlik", "Uzun quloq"], "Yirtqich go‘sht yirtish uchun o‘tkir tishga ega."),
    _b("O‘simlik poyasining vazifasi?", "Suv va moddalarni tashish hamda bargni tutib turish", ["Faqat gul ochish", "Nafas olish uchun o‘pka", "Urug‘ni yutish"], "Poya o‘simlik tayanchi."),
])
_fakt("S4-KOP", [
    _b("Kapalakning hayot sikli qaysi tartibda?", "Tuxum → lichinka → g‘umbak → kapalak", ["Kapalak → tuxum → g‘umbak", "Tuxum → kapalak → lichinka", "G‘umbak → tuxum → kapalak"], "To‘liq o‘zgarish: 4 bosqich."),
    _b("Baqa hayotining boshida qayerda yashaydi?", "Suvda (itbaliq)", ["Daraxtda", "Cho‘lda", "Tuproq ostida"], "Itbaliq suvda yashab, keyin baqaga aylanadi."),
    _b("Qush ko‘payishi qaysi?", "Tuxum qo‘yadi", ["Tirik bola tug‘adi", "Kurtak beradi", "Bo‘linadi"], "Qushlar tuxum qo‘yadi."),
    _b("O‘simlik ko‘payishi uchun nima kerak?", "Urug‘", ["Faqat suv", "Faqat tosh", "Faqat shamol"], "Urug‘dan yangi o‘simlik unadi."),
    _b("Urug‘ unib chiqishi uchun nima zarur?", "Suv, issiqlik va havo", ["Faqat yorug‘lik", "Faqat sovuq", "Faqat tuz"], "Unib chiqish shartlari."),
    _b("Ko‘payishning ahamiyati nima?", "Turni saqlab qoladi", ["Hayvonni semirtiradi", "Rangini o‘zgartiradi", "Suvni tejaydi"], "Ko‘payish tur saqlanishini ta’minlaydi."),
    _b("Qaysi hayvon o‘z bolasini sut bilan boqadi?", "Sigir", ["Baliq", "Toshbaqa", "Ari"], "Sigir — sutemizuvchi."),
    _b("Kartoshka ko‘payishi qanday?", "Tugunagi orqali", ["Faqat urug‘i bilan", "Tuxum bilan", "Bo‘linish bilan"], "Tugunak orqali vegetativ ko‘payadi."),
    _b("Lichinka qaysi bosqichdan keyin keladi?", "Tuxum", ["G‘umbak", "Voyaga yetgan", "Urug‘"], "Tuxumdan lichinka chiqadi."),
    _b("Gulda urug‘ nimadan hosil bo‘ladi?", "Changlanish va urug‘lanishdan", ["Faqat yomg‘irdan", "Tuproqdan", "Shamoldan faqat"], "Changlanishdan keyin urug‘ pishadi."),
])
_fakt("S4-MUH", [
    _b("Tuya cho‘lda yashashga qanday moslashgan?", "O‘rkachida yog‘ to‘playdi", ["Qalin mo‘yna", "Qanotlari bor", "Jabrasi bor"], "Tuya uzoq suvsiz yashay oladi."),
    _b("Qutb ayig‘ining qalin mo‘ynasi nima uchun kerak?", "Sovuqdan saqlanish", ["Issiqda salqinlash", "Uchish", "Suzmaslik"], "Qalin mo‘yna issiqlikni saqlaydi."),
    _b("Baliqning jabra nima uchun?", "Suvda nafas olish", ["Uchish", "Yugurish", "Ovqatni hazm"], "Jabra suvdan kislorod oladi."),
    _b("Kaktusning qalin poyasi nima uchun?", "Suvni to‘plash", ["Mevani ushlash", "Ovqat hazm", "Nur sochish"], "Cho‘l o‘simligi suvni saqlaydi."),
    _b("Qaysi moslashish tungi hayvon uchun?", "Katta ko‘zlar", ["Qalin mo‘yna", "Qanotlar", "Yupqa tuklar"], "Katta ko‘z kam yorug‘likda ko‘radi."),
    _b("Ko‘rshapalak nima bilan yo‘nalish topadi?", "Tovush aks-sadosi bilan", ["Hid bilan", "Rang bilan", "Shamol bilan"], "Ultratovush yo‘l ko‘rsatadi."),
    _b("Ayiq qishda nima qiladi?", "Uyquga ketadi (qishki uyqu)", ["Janubga uchadi", "Suvga tushadi", "Ko‘payadi"], "Qishki uyqu ovqat tanqisligidan saqlaydi."),
    _b("O‘rmondagi qo‘ng‘ir rangli hayvon nima uchun ko‘rinmaydi?", "Maskirovka (rangi muhitga o‘xshash)", ["U uchadi", "U juda katta", "U tungi"], "Yirtqichdan yashirinadi."),
    _b("Ko‘l o‘simliklari suvda qanday turadi?", "Yengil poyali, suv bilan ko‘tariladi", ["Qalin tog‘ ildiz", "Tikanli", "Bargsiz"], "Suv o‘simlikni ko‘taradi."),
])
_fakt("S4-EKO", [
    _b("Oziq zanjiri qayerdan boshlanadi?", "O‘simlikdan", ["Yirtqichdan", "Qo‘ziqoringa", "Suvdan"], "O‘simlik energiyani Quyoshdan oladi."),
    _b("Zanjir: o‘t → quyon → tulki. Tulki kim?", "Yirtqich", ["O‘txo‘r", "Produtsent", "Parchalovchi"], "Tulki quyonni yeydi."),
    _b("Ekotizimda o‘simlik energiya manbai nima?", "Quyosh nuri", ["Tuproq", "Shamol", "Yomg‘ir"], "Fotosintez Quyosh nuri bilan ishlaydi."),
    _b("O‘lik organizmlarni parchalovchi nima?", "Bakteriya va qo‘ziqorin", ["Quyon", "Burgut", "Baliq"], "Parchalovchilar moddalarni tuproqqa qaytaradi."),
    _b("Qaysi biri o‘txo‘r hayvon?", "Qo‘y", ["Bo‘ri", "Burgut", "Timsoh"], "Qo‘y faqat o‘simlik yeydi."),
    _b("Quyon kamayib ketsa, tulki soniga nima bo‘ladi?", "Kamayadi", ["Ko‘payadi", "O‘zgarmaydi", "Yo‘qoladi darhol"], "Oziq kamayadi."),
    _b("Hamma narsa yeydigan hayvon nima deyiladi?", "Hamma narsaxo‘r", ["O‘txo‘r", "Yirtqich", "Parchalovchi"], "Ayiq, inson hamma narsaxo‘r."),
    _b("Ko‘lda zanjir: suv o‘ti → mayda baliq → katta baliq. Eng oxirgi nima?", "Katta baliq", ["Suv o‘ti", "Mayda baliq", "Qum"], "Katta baliq zanjirning oxirgi halqasi."),
    _b("Oziq zanjirida strelka nimani bildiradi?", "Energiya yo‘nalishini", ["Hayvon tezligini", "Suv oqimini", "Tur nomini"], "Strelka kim kimni yeyishini ko‘rsatadi."),
])
_fakt("S4-SOG", [
    _b("Suyaklarni mustahkamlash uchun qaysi modda kerak?", "Kalsiy", ["Shakar", "Tuz faqat", "Yog‘"], "Sut mahsulotlarida kalsiy ko‘p."),
    _b("Qo‘lni sovun bilan yuvishning maqsadi?", "Mikroblarni yo‘qotish", ["Qo‘lni qizitish", "Terini bo‘yash", "Tirnoq o‘stirish"], "Kasalliklar oldini oladi."),
    _b("Sog‘lom odamning tana harorati taxminan?", "36,6 °C", ["20 °C", "50 °C", "10 °C"], "Normal tana harorati 36,6 °C atrofida."),
    _b("Qaysi ovqat vitamin manbai?", "Meva va sabzavot", ["Konfet", "Chips", "Gazlangan suv"], "Meva va sabzavotda vitaminlar ko‘p."),
    _b("Yuqumli kasallik qanday tarqaladi?", "Mikroblar orqali", ["Tush orqali", "Rang orqali", "Soya orqali"], "Mikroblar odamdan odamga o‘tadi."),
    _b("Mushaklarni qurish uchun qaysi oziq muhim?", "Oqsil (go‘sht, tuxum)", ["Shakar", "Tuz", "Sharbat"], "Oqsil to‘qimalarni qurish materiali."),
    _b("Tishni kuniga necha marta yuvish tavsiya?", "2 marta", ["Hech", "Haftada 1", "Yilda 1"], "Ertalab va kechqurun."),
    _b("Sport nima beradi?", "Yurak va mushaklarni mustahkamlaydi", ["Charchatadi faqat", "Kasallik tarqatadi", "Suyakni yumshatadi"], "Harakat salomatlikka foyda."),
    _b("Emlash nimadan himoya qiladi?", "Ayrim yuqumli kasalliklardan", ["Yomg‘irdan", "Sovuqdan faqat", "Charchoqdan"], "Emlash immunitetni shakllantiradi."),
])
_fakt("S4-MOD", [
    _b("Muz erisa nimaga aylanadi?", "Suvga", ["Bug‘ga", "Toshga", "Havoga"], "Qattiq → suyuq (erish)."),
    _b("Suv qaynaganda nimaga aylanadi?", "Bug‘ga (gazga)", ["Muzga", "Tuzga", "Qumga"], "Suyuq → gaz."),
    _b("Qaysi modda gaz holatida?", "Havo", ["Tosh", "Sut", "Yog‘och"], "Havo — gaz."),
    _b("Tuz suvda eriganda nima hosil bo‘ladi?", "Eritma", ["Tosh", "Gaz", "Yog‘"], "Tuz suvda erib eritma hosil qiladi."),
    _b("Qum va suv aralashmasi qanday ajratiladi?", "Filtrlash orqali", ["Qaynatish bilan", "Muzlatish bilan", "Aralashtirib"], "Filtr qumni ushlab qoladi."),
    _b("Qaysi jism suvda cho‘kadi?", "Tosh", ["Qog‘oz kema", "Ko‘pik", "Quruq barg"], "Tosh suvdan zich."),
    _b("Suyuqlik idish shaklini...", "Oladi", ["Saqlaydi", "Yo‘qotadi hajmini", "Gazga aylanadi"], "Suyuqlik oquvchan."),
    _b("Qattiq jism shakli...", "O‘zgarmaydi", ["Idishga bog‘liq", "Bug‘lanadi", "Oqadi"], "Qattiq jism shaklini saqlaydi."),
    _b("Temir nima uchun zanglaydi?", "Namlik va kislorod ta’siridan", ["Quyoshdan faqat", "Sovuqdan faqat", "Shamoldan"], "Zang — kimyoviy o‘zgarish."),
])
_fakt("S4-ENR", [
    _b("Qaysi biri yorug‘lik manbai?", "Quyosh", ["Oyna", "Oy", "Daftar"], "Quyosh o‘zi yorug‘lik chiqaradi."),
    _b("Soya qachon hosil bo‘ladi?", "Yorug‘lik yo‘lini jism to‘sganda", ["Hamma vaqt", "Kechasi faqat", "Yomg‘irda"], "To‘siq soya beradi."),
    _b("Qaysi material issiqlikni yaxshi o‘tkazadi?", "Metall", ["Yog‘och", "Plastmassa", "Rezina"], "Metall o‘tkazgich."),
    _b("Elektr zanjiri ishlashi uchun nima kerak?", "Berk yo‘l (zanjir)", ["Ochiq uzilgan sim", "Faqat lampa", "Faqat tok"], "Zanjir berk bo‘lishi shart."),
    _b("Qaysi material elektrni o‘tkazmaydi?", "Rezina", ["Mis", "Temir", "Alyuminiy"], "Rezina izolyator."),
    _b("Oyna yorug‘likni nima qiladi?", "Qaytaradi", ["Yutadi", "Sindiradi", "Yo‘qotadi"], "Qaytish hodisasi."),
    _b("Qo‘lni olovga yaqin tutsak nima yuz beradi?", "Issiqlik uzatiladi", ["Sovuq uzatiladi", "Hech narsa", "Yorug‘lik so‘nadi"], "Issiqlik issiqdan sovuqqa."),
    _b("Qaysi qurilma elektr manbai?", "Batareya", ["Lampochka", "Sim", "Tugma"], "Batareya energiya beradi."),
    _b("Kechasi Oy nima uchun ko‘rinadi?", "Quyosh nurini qaytaradi", ["O‘zi yonadi", "Yer nuri", "Yulduz"], "Oy yorug‘lik manbai emas."),
])
_fakt("S4-KUC", [
    _b("Itarish va tortish nima?", "Kuch turlari", ["Tezlik turlari", "Massa", "Harorat"], "Kuch itarish yoki tortish."),
    _b("Nima uchun olma yerga tushadi?", "Og‘irlik kuchi tufayli", ["Shamol uchun", "Issiqlik uchun", "Tovush uchun"], "Yer jismlarni o‘ziga tortadi."),
    _b("Qaysi yuza ishqalanishi eng ko‘p?", "Dag‘al yuza", ["Muz", "Moy surilgan", "Silliq oyna"], "Dag‘al yuzada ishqalanish katta."),
    _b("Ishqalanish harakatga nima qiladi?", "Sekinlashtiradi", ["Tezlashtiradi doim", "Yo‘qotadi", "Yorug‘ qiladi"], "Ishqalanish harakatga qarshilik."),
    _b("Arg‘imchoq tengligi uchun nima muhim?", "Og‘irlik va uzoqlik", ["Rang", "Shakl", "Nom"], "Muvozanat."),
    _b("Shamol yelkanni nima qiladi?", "Itaradi", ["Tortadi pastga", "Yoritadi", "Isitadi"], "Shamol kuchi yelkanni itaradi."),
    _b("Magnit nimani tortadi?", "Temirni", ["Yog‘ochni", "Shishani", "Plastmassani"], "Magnit temir buyumlarni tortadi."),
    _b("Kuch o‘lchov birligi qaysi?", "Nyuton", ["Metr", "Kilogramm", "Litr"], "Kuch nyutonda o‘lchanadi."),
    _b("Velosiped tormozi nimaga asoslanadi?", "Ishqalanishga", ["Isitishga", "Yorug‘likka", "Tovushga"], "Tormoz g‘ildirakni ishqalab to‘xtatadi."),
])
_fakt("S4-YER", [
    _b("Yer yuzasining ko‘p qismi nima bilan qoplangan?", "Suv", ["Tosh", "Qum", "Muz"], "Yer yuzasining taxminan 70% suv."),
    _b("Qaysi tuproq suvni yaxshi ushlaydi?", "Loy", ["Qum", "Shag‘al", "Tosh"], "Loy suvni sekin o‘tkazadi."),
    _b("Qaysi tuproq suvni tez o‘tkazadi?", "Qum", ["Loy", "Gil", "Qora tuproq"], "Qumda zarrachalar yirik."),
    _b("Tabiiy resurslarni tejash nega kerak?", "Ular tugab qolishi mumkin", ["Ular cheksiz", "Ular foydasiz", "Ular qimmat emas"], "Resurslar cheklangan."),
    _b("Qaysi biri tiklanadigan resurs?", "Quyosh energiyasi", ["Ko‘mir", "Neft", "Tabiiy gaz"], "Quyosh nuri tugamaydi."),
    _b("Tuproq qanday hosil bo‘ladi?", "Tog‘ jinslarining yemirilishidan va chirindidan", ["Faqat yomg‘irdan", "Shamol bilan", "Quyoshdan"], "Yemirilish va chirindi."),
    _b("Suvni tejash uchun nima qilamiz?", "Jo‘mrakni yopib qo‘yamiz", ["Kun bo‘yi ochiq", "Yerga to‘kamiz", "Bo‘sh oqiramiz"], "Har tomchi muhim."),
    _b("Havoni nima ifloslaydi?", "Zavod va avtomobil tutuni", ["Daraxt", "Yomg‘ir", "Quyosh"], "Tutun havoni ifloslaydi."),
])
_fakt("S4-JAR", [
    _b("Yomg‘ir qayerdan keladi?", "Bulutlardagi suv tomchilaridan", ["Quyoshdan", "Shamoldan", "Yerdan"], "Suv aylanishi."),
    _b("Suv bug‘lanishi nimani anglatadi?", "Suvning gazga aylanishi", ["Suvning muzlashi", "Suv tushishi", "Suv to‘kilishi"], "Quyosh issiqligi bug‘latadi."),
    _b("Daryo qayoqqa oqadi?", "Baland joydan pastga", ["Pastdan balandga", "Tog‘ cho‘qqisiga", "Atrofga"], "Suv pastga oqadi."),
    _b("Haroratni nima bilan o‘lchaymiz?", "Termometr", ["Barometr", "Tarozi", "Chizg‘ich"], "Termometr haroratni o‘lchaydi."),
    _b("Qazilma qoldiq (fossil) nima?", "Qadimgi organizm izi yoki qoldig‘i", ["Yangi daraxt", "Tosh turi faqat", "Metall"], "Fossillar qadimgi hayotni ko‘rsatadi."),
    _b("Qor qaysi haroratda yog‘adi?", "0 °C dan past", ["30 °C", "20 °C", "40 °C"], "Sovuqda suv muz kristalliga aylanadi."),
    _b("Shamol nima?", "Havoning harakati", ["Suvning oqimi", "Yerning aylanishi", "Quyosh nuri"], "Isigan havo ko‘tariladi, shamol hosil bo‘ladi."),
    _b("Bulut nimadan tuzilgan?", "Mayda suv tomchilaridan", ["Tutundan", "Changdan faqat", "Gazdan"], "Bug‘ sovub tomchi bo‘ladi."),
])
_fakt("S4-QUY", [
    _b("Yer Quyosh atrofida necha kunda aylanadi?", "Taxminan 365 kun (1 yil)", ["1 kun", "30 kun", "7 kun"], "Bir yil."),
    _b("Kecha va kunduz nima uchun almashadi?", "Yer o‘z o‘qi atrofida aylanadi", ["Quyosh aylanadi", "Oy yo‘qoladi", "Bulut"], "Yer 24 soatda aylanadi."),
    _b("Fasllar nima uchun almashadi?", "Yer o‘qi egilgan va Quyosh atrofida aylanadi", ["Quyosh o‘chadi", "Oy aylanadi", "Shamol"], "Egilgan o‘q."),
    _b("Oy nima?", "Yerning tabiiy yo‘ldoshi", ["Yulduz", "Sayyora", "Quyosh"], "Oy Yer atrofida aylanadi."),
    _b("Quyosh nima?", "Yulduz", ["Sayyora", "Yo‘ldosh", "Asteroid"], "Quyosh — o‘zi yorug‘lik beradi."),
    _b("Qaysi sayyora Quyoshga eng yaqin?", "Merkuriy", ["Yupiter", "Saturn", "Neptun"], "Merkuriy birinchi."),
    _b("Quyosh energiyasi nima uchun muhim?", "Hayot va o‘simliklar uchun zarur", ["Zararli", "Foydasiz", "Faqat Oy uchun"], "Quyosh nuri hayot manbai."),
    _b("Oy tutilishida nima yuz beradi?", "Yer soyasi Oyga tushadi", ["Oy Quyoshni yopadi", "Quyosh o‘chadi", "Yer to‘xtaydi"], "Yer Quyosh va Oy orasida."),
])

# hisoblash shablonlari
@reg("S4-TIR", "ochiq")
def s4_tir(rng):
    a, b, c = rng.choice([(5, 3, 2), (8, 4, 3), (6, 6, 4)])
    return _o(f"Fermada {a} ta sigir, {b} ta qo‘y va {c} ta tovuq bor.", [("a) Sutemizuvchilar soni?", a + b), ("b) Jami hayvonlar soni?", a + b + c)], [f"a) {a} + {b} = {a + b}.", f"b) {a + b} + {c} = {a + b + c}."])

@reg("S4-KOP", "ochiq")
def s4_kop(rng):
    t = rng.choice([30, 40, 60]); k = rng.choice([4, 5, 6])
    return _o(f"Baliq {t} ta ikra qo‘ydi, {t // k * 2 if False else t // 2} tasidan lichinka chiqdi.", [("a) Chiqmagan ikralar?", t - t // 2), ("b) Lichinkalar soni?", t // 2)], [f"a) {t} − {t // 2} = {t - t // 2}.", f"b) {t // 2}."])

@reg("S4-MUH", "ochiq")
def s4_muh(rng):
    d = rng.choice([8, 10, 12]); m = rng.choice([3, 4, 5])
    return _o(f"Tuya {d} kun suvsiz yurdi, har kuni {m * 10} km yo‘l bosdi.", [("a) Jami necha km?", d * m * 10), ("b) 100 km yo‘l necha kun?", Fraction(10, m))], [f"a) {d}·{m * 10} = {d * m * 10}.", f"b) 100/{m * 10} = {num(Fraction(10, m))}."])

@reg("S4-EKO", "ochiq")
def s4_eko(rng):
    a = rng.choice([100, 200, 500]); 
    return _o(f"Oziq zanjirida har bosqichda energiyaning 10% i keyingisiga o‘tadi. O‘simlikda {a * 10} birlik energiya bor.", [("a) O‘txo‘rga necha birlik o‘tadi?", a), ("b) Yirtqichga necha birlik o‘tadi?", a // 10)], [f"a) {a * 10}·10% = {a}.", f"b) {a}·10% = {a // 10}."])

@reg("S4-SOG", "ochiq")
def s4_sog(rng):
    t = rng.choice([37, 38, 39]); 
    return _o(f"Bolaning harorati {t}°C. Normal harorat 36,6°C.", [("a) Normadan necha °C yuqori? (o‘nli kasr)", Fraction(t * 10 - 366, 10)), ("b) 10 kunda har kuni 3 marta o‘lchansa, jami necha o‘lchash?", 30)], [f"a) {t} − 36,6 = {num(Fraction(t * 10 - 366, 10))}.", "b) 10·3 = 30."])

@reg("S4-MOD", "ochiq")
def s4_mod(rng):
    v = rng.choice([200, 300, 500]); 
    return _o(f"Stakanda {v} ml suv bor. Unga {v // 2} ml suv qo‘shildi, keyin {v // 4} ml to‘kildi.", [("a) Qo‘shilgandan keyin necha ml?", v + v // 2), ("b) Oxirida necha ml?", v + v // 2 - v // 4)], [f"a) {v} + {v // 2} = {v + v // 2}.", f"b) {v + v // 2} − {v // 4} = {v + v // 2 - v // 4}."])

@reg("S4-ENR", "ochiq")
def s4_enr(rng):
    n = rng.choice([4, 5, 6]); w = rng.choice([5, 10])
    return _o(f"Zanjirda {n} ta lampa, har biri {w} Vt.", [("a) Hammasi yonsa jami necha Vt?", n * w), ("b) 3 soat yonsa necha Vt·soat?", n * w * 3)], [f"a) {n}·{w} = {n * w}.", f"b) {n * w}·3 = {n * w * 3}."])

@reg("S4-KUC", "ochiq")
def s4_kuc(rng):
    m = rng.choice([2, 3, 5]); 
    return _o(f"Arg‘imchoqda {m * 10} kg bola chap tomonda, o‘ng tomonda {m * 5} kg bola.", [("a) Og‘irlik farqi?", m * 5), ("b) Muvozanat uchun o‘ng tomonga yana necha kg kerak?", m * 5)], [f"a) {m * 10} − {m * 5} = {m * 5}.", f"b) {m * 5} kg."])

@reg("S4-YER", "ochiq")
def s4_yer(rng):
    t = rng.choice([60, 80, 100]); 
    return _o(f"Hovlida {t} litr suv bor. Kuniga {t // 10} litr ishlatiladi.", [("a) Necha kunga yetadi?", 10), ("b) Tejab, kuniga {0} litr ishlatilsa, necha kunga yetadi?".format(t // 20), 20)], [f"a) {t}/{t // 10} = 10.", f"b) {t}/{t // 20} = 20."])

@reg("S4-JAR", "ochiq")
def s4_jar(rng):
    t = [rng.randint(10, 30) for _ in range(5)]; n = ["Dush", "Sesh", "Chor", "Pay", "Jum"]
    q = _o("Diagrammada 5 kunlik harorat (°C) ko‘rsatilgan.", [("a) Eng issiq kun harorati?", max(t)), ("b) Eng issiq va eng sovuq kun farqi?", max(t) - min(t))], [f"a) {max(t)}.", f"b) {max(t)} − {min(t)} = {max(t) - min(t)}."])
    q["rasm"] = fig_stolbik(n, t, "Harorat °C"); return q

@reg("S4-QUY", "ochiq")
def s4_quy(rng):
    s = rng.choice([24, 12]); 
    return _o("Yer o‘z o‘qi atrofida 24 soatda bir marta aylanadi.", [("a) 3 kunda necha soat?", 72), ("b) Bir kunda necha marta aylanadi? (yarim kunda necha marta?)", Fraction(1, 2))], ["a) 3·24 = 72.", "b) 12/24 = 1/2."])

TEMA = {
 "S4-TIR": _tema("S4-TIR", "Tirik organizmlar va hayotiy jarayonlar", "🌱", "Tirikni notirikdan ajratish, guruhlash, tuzilish", [_d("Tirik belgilari", "Tirik: ovqatlanadi, nafas oladi, o‘sadi, ko‘payadi\nGuruhlar: sutemizuvchi, qush, baliq, hasharot", "Tirik organizmlar ovqatlanadi, nafas oladi, o‘sadi va ko‘payadi. Hayvonlar tuzilishiga ko‘ra guruhlarga bo‘linadi.")]),
 "S4-KOP": _tema("S4-KOP", "Hayot sikli va ko‘payish", "🦋", "Hayot sikli bosqichlari va ko‘payish", [_d("Hayot sikli", "Tuxum → lichinka → g‘umbak → kapalak\nUrug‘ → maysa → gul → urug‘", "Hayot sikli bosqichlar ketma-ketligidan iborat. Ko‘payish turni saqlab qoladi.")]),
 "S4-MUH": _tema("S4-MUH", "Organizm va muhit", "🐪", "Moslashish misollari", [_d("Moslashish", "Muhit → moslashish\nTuya: o‘rkachida yog‘\nQutb ayig‘i: qalin mo‘yna", "Har bir organizm yashash muhitiga moslashgan: tuzilishi va xulqi bilan.")]),
 "S4-EKO": _tema("S4-EKO", "Ekotizimlar va oziq zanjiri", "🔗", "Oziq zanjirini o‘qish", [_d("Oziq zanjiri", "Quyosh → o‘simlik → o‘txo‘r → yirtqich\nStrelka = energiya yo‘nalishi", "Zanjir o‘simlikdan boshlanadi. Strelka kim kimni yeyishini va energiya yo‘nalishini ko‘rsatadi.")]),
 "S4-SOG": _tema("S4-SOG", "Inson salomatligi", "🍎", "Ovqatlanish, kasalliklar, gigiyena", [_d("Salomatlik", "Kalsiy — suyak\nOqsil — mushak\nQo‘l yuvish — kasallikdan saqlanish", "Sog‘lom ovqatlanish, gigiyena va harakat salomatlikni saqlaydi.")]),
 "S4-MOD": _tema("S4-MOD", "Moddalar va ularning xossalari", "🧊", "Holatlar, eritma, aralashma", [_d("Holatlar", "Qattiq ↔ suyuq ↔ gaz\nErish, qaynash\nEritma, aralashma", "Modda qattiq, suyuq va gaz holatda bo‘ladi. Isitish yoki sovitish holatni o‘zgartiradi.")]),
 "S4-ENR": _tema("S4-ENR", "Energiya: yorug‘lik, issiqlik, elektr", "💡", "Yorug‘lik, issiqlik, elektr zanjiri", [_d("Energiya", "Soya: yorug‘lik to‘sildi\nMetall — o‘tkazgich\nRezina — izolyator\nBerk zanjir", "Yorug‘lik to‘siqda soya hosil qiladi. Metall issiqlik va tokni o‘tkazadi. Elektr zanjiri berk bo‘lishi kerak.")]),
 "S4-KUC": _tema("S4-KUC", "Kuch va harakat", "🧲", "Kuch turlari, ishqalanish", [_d("Kuchlar", "Itarish / tortish\nOg‘irlik kuchi — pastga\nIshqalanish — sekinlatadi", "Kuch itarish yoki tortish. Og‘irlik kuchi jismlarni yerga tortadi, ishqalanish harakatni sekinlashtiradi.")]),
 "S4-YER": _tema("S4-YER", "Yer tuzilishi va resurslari", "🌍", "Tuproq, suv, resurslarni tejash", [_d("Resurslar", "Tiklanadigan: Quyosh, shamol\nTugaydigan: neft, ko‘mir\nSuvni tejaymiz", "Ba’zi resurslar tugaydi, shuning uchun ularni tejash kerak.")]),
 "S4-JAR": _tema("S4-JAR", "Ob-havo va tabiat jarayonlari", "🌦️", "Ob-havo, suv aylanishi, fossillar", [_d("Suv aylanishi", "Bug‘lanish → bulut → yomg‘ir → daryo\nTermometr — harorat", "Quyosh suvni bug‘latadi, bug‘ sovub bulut bo‘ladi, yomg‘irdan daryo to‘ladi.")]),
 "S4-QUY": _tema("S4-QUY", "Quyosh tizimi", "☀️", "Kecha-kunduz, fasllar, Oy", [_d("Yer harakati", "O‘q atrofida: 24 soat — kecha/kunduz\nQuyosh atrofida: 1 yil — fasllar", "Yer o‘z o‘qi atrofida aylansa kecha va kunduz almashadi, Quyosh atrofida aylansa fasllar almashadi.")]),
}
