"""TIMSS 4-sinf fan: kengaytirilgan faktlar va qo'lda yozilgan chuqur darslar."""
from modules.xb_ps import _qosh, _d, BANK
from modules.xb_s4 import TEMA as _T0

def _b(sv, tj, no, iz=""):
    return (sv, tj, no, iz or f"To‘g‘ri javob: {tj}.")

_qosh("S4-TIR", [
    _b("Qaysi organizm o‘simlik emas?", "Qo‘ziqorin", ["Lola", "Archa", "Moxlar"], "Qo‘ziqorinlar alohida dunyo: fotosintez qilmaydi."),
    _b("Hayvonlar o‘simliklardan nimasi bilan farq qiladi?", "Tayyor oziq bilan ovqatlanadi va harakatlanadi", ["Fotosintez qiladi", "Ildizi bor", "Faqat suvda yashaydi"], "Hayvon oziqni o‘zi yaratmaydi."),
    _b("Qaysi organ hayvonda nafas olishga xizmat qiladi (quruqlikda)?", "O‘pka", ["Yurak", "Oshqozon", "Bosh miya"], "O‘pka havodan kislorod oladi."),
    _b("Yurak vazifasi nima?", "Qonni tanaga haydash", ["Ovqat hazm qilish", "Nafas olish", "Tovush chiqarish"], "Yurak nasosdek ishlaydi."),
    _b("Qaysi hayvon o‘txo‘r?", "Quyon", ["Arslon", "Burgut", "Bo‘ri"], "Quyon o‘t va sabzavot yeydi."),
    _b("Qaysi hayvon yirtqich?", "Bo‘ri", ["Sigir", "Echki", "Qo‘y"], "Bo‘ri go‘sht yeydi."),
    _b("Baliqlar harakatlanishi uchun nimaga ega?", "Suzgich qanotlar", ["Qanot", "Tuyoq", "Ildiz"], "Suzgichlar suvda suzishga yordam beradi."),
    _b("O‘simlik gulining vazifasi?", "Urug‘ hosil qilish (ko‘payish)", ["Suv so‘rish", "Qurilish", "Nafas olish uchun o‘pka"], "Gul meva va urug‘ beradi."),
    _b("Qushlarning patlari nima uchun kerak?", "Uchish va issiqni saqlash", ["Suzish", "Qazish", "Ovqat hazm"], "Patlar qanot va tanani qoplaydi."),
    _b("Hasharotning tana qismlari nechta?", "3 (bosh, ko‘krak, qorin)", ["2", "5", "7"], "Hasharotlar 3 qismli."),
    _b("Qaysi hayvonning umurtqa pog‘onasi yo‘q?", "Qurt", ["Baliq", "Qush", "Qurbaqa"], "Qurt umurtqasiz."),
    _b("Qaysi jarayon barcha tirik organizmlarga xos?", "Nafas olish", ["Uchish", "Gapirish", "Rang o‘zgartirish"], "Hamma tirik nafas oladi."),
])
_qosh("S4-KOP", [
    _b("Tovuq tuxumidan nima chiqadi?", "Jo‘ja", ["Kuchuk", "Lichinka", "Itbaliq"], "Tuxumdan jo‘ja chiqadi."),
    _b("Qurbaqa hayot sikli bosqichlari tartibi?", "Ikra → itbaliq → qurbaqa", ["Qurbaqa → ikra → itbaliq", "Itbaliq → ikra → qurbaqa", "Ikra → qurbaqa → itbaliq"], "Itbaliq oyoq chiqarib qurbaqaga aylanadi."),
    _b("Mushukcha qaysi usulda tug‘iladi?", "Tirik tug‘iladi va sut bilan boqiladi", ["Tuxumdan", "Urug‘dan", "G‘umbakdan"], "Sutemizuvchi."),
    _b("Gulchangi nima uchun kerak?", "Urug‘lanish uchun", ["Hid uchun", "Suv uchun", "Rang uchun"], "Changlanish — urug‘lanish boshlanishi."),
    _b("O‘simlik urug‘i ichida nima bor?", "Yangi o‘simlik murtagi", ["Faqat suv", "Faqat havo", "Tosh"], "Murtakdan yangi o‘simlik o‘sadi."),
    _b("Kapalak lichinkasi nima deyiladi?", "Qurtsimon lichinka", ["Itbaliq", "Jo‘ja", "Qo‘zichoq"], "Lichinka g‘umbakka aylanadi."),
    _b("Hayot siklidagi eng oxirgi bosqich?", "Voyaga yetgan organizm", ["Tuxum", "Lichinka", "Urug‘"], "U yana ko‘payadi."),
    _b("Qaysi hayvon tuxum qo‘yadi?", "Toshbaqa", ["Sigir", "Ot", "Echki"], "Sudralib yuruvchi."),
    _b("Meva ichida odatda nima bor?", "Urug‘", ["Tosh", "Suv faqat", "Barg"], "Meva urug‘ni himoya qiladi."),
    _b("Yosh organizm ota-onaga qanday bo‘ladi?", "O‘xshash", ["Butunlay boshqa", "Bir xil emas va rangi boshqa faqat", "Hech o‘xshamaydi"], "Belgilar avlodga o‘tadi."),
])
_qosh("S4-MUH", [
    _b("Dengiz ayiqlari (morj) qalin yog‘ qatlamiga ega. Nima uchun?", "Sovuq suvda issiqni saqlash", ["Tezroq yurish", "Uchish", "Qazish"], "Yog‘ qatlami issiqlik saqlaydi."),
    _b("Kaktusda barglar tikanga aylangan. Sababi?", "Suv bug‘lanishini kamaytirish", ["Ko‘proq yorug‘lik olish", "Mevani himoya qilish faqat", "Ovqat tayyorlash"], "Tikan suv yo‘qotilishini kamaytiradi."),
    _b("Qaysi hayvon tunda ov qiladi?", "Boyqush", ["Tovus", "Kaptar", "Chumchuq"], "Boyqushning ko‘zi tungi ko‘rishga moslangan."),
    _b("Baliqning tana shakli oqimsimon. Nima uchun?", "Suvda tez suzish", ["Uchish", "Qazish", "Yugurish"], "Qarshilik kam bo‘ladi."),
    _b("Yirtqich hayvonning ko‘zlari oldinda. Nima beradi?", "Masofani aniq baholash", ["Orqani ko‘rish", "Suvda ko‘rish", "Ko‘rmaslik"], "Ov uchun muhim."),
    _b("O‘txo‘r hayvonning ko‘zlari yon tomonda. Nima beradi?", "Atrofni keng ko‘rish", ["Ovni topish", "Qazish", "Suzish"], "Yirtqichni ko‘rib qolish uchun."),
    _b("Qutb tulkisi yozda qanday rangda bo‘ladi?", "Qo‘ng‘ir-kulrang", ["Doim oq", "Qizil", "Ko‘k"], "Muhitga mos rang."),
    _b("Cho‘l kaltakesagi kunduzi nima qiladi?", "Soyada yoki ko‘milib issiqdan saqlanadi", ["Quyosh ostida yuguradi", "Uchib ketadi", "Suvda suzadi"], "Issiqdan saqlanish xulqi."),
    _b("Suv o‘simliklari ildizi nega zaif?", "Suv bevosita so‘riladi", ["Tuproq qattiq", "Yorug‘ yo‘q", "Hayvon yeydi"], "Suvdan ham modda oladi."),
])
_qosh("S4-EKO", [
    _b("Zanjir: don → sichqon → ilon. Ilon nima?", "Yirtqich", ["O‘txo‘r", "O‘simlik", "Parchalovchi"], "Ilon sichqonni yeydi."),
    _b("Qurbaqa nimani yeydi?", "Hasharotlarni", ["Qumni", "Toshni", "Suvni"], "Qurbaqa hasharotxo‘r."),
    _b("Qaysi organizm produtsent (oziq yaratadi)?", "Daraxt", ["Sigir", "Bo‘ri", "Burgut"], "O‘simlik fotosintez qiladi."),
    _b("Yirtqich ko‘paysa, o‘lja soni...", "Kamayadi", ["Ko‘payadi", "O‘zgarmaydi", "Ikki baravar"], "Ko‘proq yeyiladi."),
    _b("Bir ekotizimga misol?", "Ko‘l va uning jonzotlari", ["Bitta tosh", "Faqat bir baliq", "Bitta barg"], "Ekotizim — jonli va jonsiz tabiat birligi."),
    _b("Qaysi hayvon o‘lik hayvonni yeyishi mumkin (leshxo‘r)?", "Kalxat", ["Quyon", "Sigir", "Ot"], "Kalxat leshxo‘r."),
    _b("Oziq zanjirida eng ko‘p energiya qayerda?", "O‘simlikda", ["Yirtqichda", "Oxirgi halqada", "Bakteriyada"], "Pastga qarab kamayadi."),
    _b("Cho‘lda o‘simlik yo‘qolsa, o‘txo‘rlar nima bo‘ladi?", "Ocharchilikdan kamayadi", ["Ko‘payadi", "O‘zgarmaydi", "Yirtqichga aylanadi"], "Oziq manbai yo‘qoladi."),
    _b("Ilon, bo‘ri, burgut nega yirtqich?", "Boshqa hayvonlarni ovlaydi", ["O‘simlik yeydi", "Faqat suv ichadi", "Quyoshdan oziqlanadi"], "Yirtqich ov qiladi."),
])
_qosh("S4-SOG", [
    _b("Qaysi vitamin meva va sabzavotda ko‘p?", "C vitamini", ["Faqat D", "Temir", "Tuz"], "Meva immunitetni mustahkamlaydi."),
    _b("Suv nima uchun kerak?", "Tana ish faoliyati uchun", ["Faqat yuvish", "Faqat rang uchun", "Kerak emas"], "Tanamiz ko‘p suvdan iborat."),
    _b("Yuqumli kasallikni oldini olish yo‘li?", "Qo‘lni yuvish va emlanish", ["Yalang oyoq yurish", "Kam uxlash", "Kir kiyim"], "Gigiyena va emlash."),
    _b("Tana harorati 39 °C bo‘lsa, bu...", "Isitma (yuqori harorat)", ["Normal", "Past harorat", "Sog‘lom belgi"], "Normadan yuqori."),
    _b("Sog‘lom uyqu miqdori bolalar uchun taxminan?", "9–11 soat", ["2 soat", "4 soat", "16 soat"], "Uyqu o‘sishga yordam beradi."),
    _b("Qaysi ovqat sog‘lom nonushta?", "Bo‘tqa, tuxum, meva", ["Chips", "Gazlangan ichimlik", "Konfet"], "To‘yimli oziq."),
    _b("Yo‘talganda nima qilish kerak?", "Og‘izni tirsak yoki ro‘mol bilan yopish", ["Boshqaga qarab yo‘talish", "Qo‘l bilan yopmaslik", "Hech narsa"], "Mikrob tarqalmasligi uchun."),
    _b("Tish nima uchun chiriydi?", "Shirinlik qoldiqlari va mikroblar tufayli", ["Suv ichgani uchun", "Uxlagani uchun", "Sport uchun"], "Tish tozaligi muhim."),
    _b("Mushaklarga ko‘proq kerak bo‘ladigan oziq?", "Oqsil", ["Faqat tuz", "Faqat shakar", "Faqat suv"], "Go‘sht, tuxum, loviya."),
])
_qosh("S4-MOD", [
    _b("Suv bug‘i qaysi holatda?", "Gaz", ["Qattiq", "Suyuq", "Plazma emas, qum"], "Bug‘ — gaz."),
    _b("Shokolad issiq qo‘lda nima bo‘ladi?", "Eriydi", ["Qotadi", "Bug‘lanadi", "Yonadi"], "Qattiq → suyuq."),
    _b("Moyli suyuqlik suvda nima qiladi?", "Ustida suzadi", ["Cho‘kadi", "Eriydi", "Bug‘lanadi"], "Moy suvdan yengil."),
    _b("Shakar choyda eriganda...", "Choy shirin bo‘ladi, shakar ko‘rinmaydi", ["Shakar yo‘qoladi", "Choy muzlaydi", "Suv bug‘lanadi"], "Eritma hosil bo‘ladi."),
    _b("Qaysi aralashma ajratiladi magnit bilan?", "Temir qipig‘i va qum", ["Tuz va suv", "Shakar va suv", "Sut"], "Magnit temirni tortadi."),
    _b("Tuz va suv aralashmasidan tuzni olish?", "Suvni bug‘latish", ["Filtrlash", "Magnit", "Silkitish"], "Suv ketadi, tuz qoladi."),
    _b("Muz suvdan zichroqmi?", "Yo‘q, kamroq zich (suzadi)", ["Ha, cho‘kadi", "Bir xil", "Bug‘lanadi"], "Muz suvda suzadi."),
    _b("Gaz idishga solinsa...", "Butun idishni to‘ldiradi", ["Pastda qoladi", "Qotadi", "Yo‘qoladi"], "Gaz hajmi idishga bog‘liq."),
    _b("Qaysi o‘zgarish qaytarilmaydi?", "Qog‘ozning yonishi", ["Muzning erishi", "Suvning qaynashi", "Mumning erishi"], "Yonish — yangi modda."),
])
_qosh("S4-ENR", [
    _b("Soya kattaligi nimaga bog‘liq?", "Yorug‘lik manbaigacha masofaga", ["Rangiga", "Og‘irligiga", "Ovoziga"], "Manbaga yaqinlashsa soya kattalashadi."),
    _b("Oyna nima uchun yaltiraydi?", "Yorug‘likni yaxshi qaytaradi", ["Yorug‘lik chiqaradi", "Yutadi", "Sindiradi"], "Silliq yuza."),
    _b("Elektr zanjirida kalit nima qiladi?", "Zanjirni ulaydi va uzadi", ["Energiya beradi", "Tokni ko‘paytiradi", "Lampani kuydiradi"], "Kalit — ulagich."),
    _b("Qaysi material izolyator?", "Plastmassa", ["Mis", "Temir", "Alyuminiy"], "Tokni o‘tkazmaydi."),
    _b("Issiq choy tez sovishi uchun?", "Keng idishga quyish", ["Qopqoq yopish", "Termosga solish", "Choyni isitish"], "Yuza katta bo‘lsa tez soviydi."),
    _b("Qaysi manba tabiiy yorug‘lik beradi?", "Quyosh", ["Lampa", "Fonar", "Shamchirog‘"], "Quyosh tabiiy manba."),
    _b("Batareya tugasa lampa...", "Yonmaydi", ["Yorug‘ yonadi", "Issiq bo‘ladi", "Tovush chiqaradi"], "Energiya yo‘q."),
    _b("Metall qoshiq issiq choyda...", "Tez qiziydi", ["Sovuq qoladi", "Qiziydi lekin sekin", "Muzlaydi"], "Metall issiqlik o‘tkazadi."),
    _b("Yog‘och qoshiq nega qo‘lni kuydirmaydi?", "Issiqlikni yomon o‘tkazadi", ["Sovuq", "Og‘ir", "Silliq"], "Yog‘och issiqlik izolyatori."),
])
_qosh("S4-KUC", [
    _b("Qutini surish kuchi nimaga bog‘liq?", "Ishqalanish va massaga", ["Rangiga", "Soyasiga", "Hidiga"], "Og‘ir va dag‘al — qiyin."),
    _b("Magnit qaysi jismni tortmaydi?", "Plastmassa", ["Mix", "Qaychi", "Skrepka"], "Faqat temir jismlarni."),
    _b("Qanday kuch tushayotgan yomg‘ir tomchisini pastga tortadi?", "Og‘irlik kuchi", ["Magnit", "Shamol", "Ishqalanish yo‘q"], "Yer tortishi."),
    _b("Arg‘imchoqni kim kuchsiz bola siljitadi?", "Uzoqroq o‘tirib", ["Yaqinroq o‘tirib", "Ko‘zini yumib", "Turib"], "Uzoq tomon ko‘proq ta’sir qiladi."),
    _b("Toshni ko‘tarish uchun nima kerak?", "Kuch", ["Rang", "Hid", "Tovush"], "Ko‘tarish tortish kuchi."),
    _b("Silliq muzda sirpanish nima uchun oson?", "Ishqalanish kam", ["Og‘irlik yo‘q", "Magnit bor", "Issiq"], "Silliq yuza."),
    _b("Shamol kuchi nimani harakatlantiradi?", "Yelkanli kema va shamol tegirmoni", ["Faqat quyosh", "Tosh", "Daftar"], "Shamol kuchli."),
    _b("Qaysi kuch jismni tortib yerga yaqin ushlaydi?", "Tortishish", ["Itarish", "Ishqalanish", "Elastiklik"], "Yer tortishi."),
    _b("Prujinani cho‘zsak nima bo‘ladi?", "Qaytish kuchi paydo bo‘ladi", ["Yo‘qoladi", "Qotadi", "Muzlaydi"], "Elastiklik."),
])
_qosh("S4-YER", [
    _b("Yer yuzasidagi eng katta suv havzasi?", "Okean", ["Ko‘l", "Daryo", "Hovuz"], "Okean Yer yuzasining katta qismini egallaydi."),
    _b("Qaysi tuproq o‘simlik uchun yaxshi (unumdor)?", "Chirindiga boy tuproq", ["Toza qum", "Toza tosh", "Shag‘al"], "Chirindi oziq beradi."),
    _b("Tog‘ jinslari qanday maydalanadi?", "Shamol, suv va harorat ta’sirida", ["Faqat yomg‘ir emas", "O‘z-o‘zidan", "Tovush bilan"], "Yemirilish."),
    _b("Qayta ishlanadigan chiqindi qaysi?", "Qog‘oz", ["Banan po‘sti", "Hech qaysi", "Chang"], "Qog‘ozdan yangi qog‘oz qilinadi."),
    _b("Suvni ifloslantirish nimaga olib keladi?", "Baliq va o‘simliklar zarar ko‘rishiga", ["Suv tozalanishiga", "Hech narsaga", "Quyosh yaxshi"], "Toza suv zarur."),
    _b("Daraxt ekishning foydasi?", "Havo tozalanadi va tuproq ushlanadi", ["Havo ifloslanadi", "Tuproq yuviladi", "Suv kamayadi"], "O‘simlik tabiatni himoyalaydi."),
    _b("Qaysi manba cheklangan?", "Neft", ["Quyosh nuri", "Shamol", "Suv aylanishi"], "Tugab qolishi mumkin."),
    _b("Elektrni tejash uchun nima qilamiz?", "Keraksiz chiroqni o‘chiramiz", ["Hamma chiroqni yoqib qo‘yamiz", "Hech narsa", "Ko‘proq yoqamiz"], "Energiya tejaladi."),
])
_qosh("S4-JAR", [
    _b("Qaysi bulut yomg‘ir olib keladi?", "Qora, qalin bulut", ["Yupqa oq", "Bulut yo‘q", "Rangi qizil"], "Qalin bulutda ko‘p suv bor."),
    _b("Ob-havo kuzatish asboblaridan biri?", "Termometr", ["Chizg‘ich", "Tarozi", "Soat"], "Harorat o‘lchaydi."),
    _b("Yomg‘ir o‘lchagich nimani o‘lchaydi?", "Yog‘in miqdorini", ["Haroratni", "Shamolni", "Bosimni"], "Yomg‘ir miqdori."),
    _b("Daryo tog‘dan qayoqqa oqadi?", "Pastga, dengiz yoki ko‘lga", ["Tog‘ cho‘qqisiga", "Osmonga", "Orqaga"], "Pastga."),
    _b("Qor eriganda nima hosil bo‘ladi?", "Suv", ["Muz", "Bug‘", "Havo"], "Muz/qor erib suv bo‘ladi."),
    _b("Fossil topilgan tosh nima haqida ma’lumot beradi?", "Qadimda yashagan organizm haqida", ["Hozirgi ob-havo", "Yangi yulduz", "Tuproq rangi"], "Fossil — qadimgi tirik izi."),
    _b("Qaysi fasl eng sovuq?", "Qish", ["Yoz", "Bahor", "Kuz"], "Qishda harorat past."),
    _b("Kamalak qachon paydo bo‘ladi?", "Yomg‘irdan keyin quyosh chiqqanda", ["Kechasi", "Qorda", "Shamolda"], "Yorug‘lik tomchida sinadi."),
])
_qosh("S4-QUY", [
    _b("Yer Quyoshdan nechanchi sayyora?", "Uchinchi", ["Birinchi", "Beshinchi", "Sakkizinchi"], "Merkuriy, Venera, Yer."),
    _b("Sutkada Yer necha marta aylanadi?", "Bir marta", ["Ikki marta", "O‘n marta", "Aylanmaydi"], "24 soatda."),
    _b("Oy Yer atrofida taxminan necha kunda aylanadi?", "Taxminan 1 oyda (28 kun)", ["1 kunda", "1 yilda", "1 soatda"], "Oy fazalari shundan."),
    _b("Qaysi sayyora «Qizil sayyora» deyiladi?", "Mars", ["Yupiter", "Venera", "Saturn"], "Marsning tuprog‘i qizg‘ish."),
    _b("Quyoshning Yerga qaysi tomoni qaragan bo‘lsa, o‘sha yerda...", "Kunduz", ["Kecha", "Qish", "Hech narsa"], "Yoritilgan tomon — kunduz."),
    _b("Yozda kunduz qanday?", "Uzun", ["Qisqa", "Bor emas", "Doimiy qorong‘i"], "Quyosh uzoq ko‘rinadi."),
    _b("Qaysi sayyoraning halqalari bor?", "Saturn", ["Mars", "Yer", "Merkuriy"], "Saturn halqalari mashhur."),
    _b("Yulduzlar kechasi nima uchun ko‘rinadi?", "Quyosh yo‘q va osmon qorong‘i", ["Quyosh chiqqani uchun", "Bulut yo‘qligi uchun faqat", "Oy o‘chgani uchun"], "Kunduzi Quyosh yorug‘ligi to‘sadi."),
])

# qo'lda yozilgan, kengaytirilgan darslar
def _mav(kod, qad):
    t = dict(_T0[kod]); t["dars"] = qad; return t

TEMA = {
 "S4-TIR": _mav("S4-TIR", [
  _d("Tirikni notirikdan ajratamiz", "Tirik: ovqatlanadi, nafas oladi, o‘sadi, ko‘payadi\nNotirik: tosh, suv, havo", "Avval tirik organizmning belgilarini eslaymiz. Tirik ovqatlanadi, nafas oladi, o‘sadi va ko‘payadi. Tosh, suv va havo bu belgilarga ega emas."),
  _d("Hayvonlar guruhlari", "Umurtqali: baliq, qurbaqa, kaltakesak, qush, sutemizuvchi\nUmurtqasiz: hasharot, qurt, salyangoz", "Hayvonlar ikkiga bo‘linadi: umurtqali va umurtqasiz. Umurtqalilar o‘z ichida beshta sinfga bo‘linadi."),
  _d("O‘simlik qismlari", "Ildiz — suv so‘radi\nPoya — tutib turadi\nBarg — oziq yaratadi\nGul — urug‘ beradi", "Har bir o‘simlik qismi o‘z vazifasini bajaradi. Ildiz suv so‘radi, poya tayanch bo‘ladi, bargda oziq tayyorlanadi, gul urug‘ beradi."),
  _d("Tish — oziq belgisi", "O‘txo‘r: yassi tishlar\nYirtqich: o‘tkir qoziq tishlar\nHamma narsaxo‘r: ikkalasi", "Tishlarga qarab hayvon nima yeyishini bilish mumkin. Yirtqichning o‘tkir qoziq tishlari, o‘txo‘rning yassi tishlari bor."),
  _d("Xato qilmaymiz", "❌ Hamma suvda yashaydiganlar baliq\n✅ Delfin — sutemizuvchi, baliq emas", "Suvda yashaganining o‘zi baliq degani emas. Delfin va kit sutemizuvchi, ular o‘pka bilan nafas oladi."),
 ]),
 "S4-KOP": _mav("S4-KOP", [
  _d("Hayot sikli nima?", "Tug‘ilish → o‘sish → ko‘payish → qarish", "Har bir tirik organizm tug‘iladi, o‘sadi, ko‘payadi. Bu hayot sikli deyiladi."),
  _d("Kapalak sikli", "Tuxum → lichinka → g‘umbak → kapalak", "Kapalakning rivojlanishi to‘rt bosqichdan iborat: tuxum, lichinka, g‘umbak, kapalak."),
  _d("Baqa sikli", "Ikra → itbaliq → qurbaqa", "Qurbaqa suvda ikra qo‘yadi, ikradan itbaliq chiqadi, itbaliq oyoq chiqarib qurbaqaga aylanadi."),
  _d("O‘simlik sikli", "Urug‘ → maysa → o‘simlik → gul → meva (urug‘)", "O‘simlik urug‘dan unadi, o‘sadi, gullaydi va yana urug‘ beradi."),
  _d("Nima uchun ko‘payish kerak?", "Ko‘payish = turni saqlash", "Agar organizmlar ko‘paymasa, tur yo‘qolib ketadi. Shuning uchun ko‘payish juda muhim."),
 ]),
 "S4-MUH": _mav("S4-MUH", [
  _d("Moslashish nima?", "Tuzilish yoki xulq muhitga mos", "Moslashish — organizmning yashash joyiga mos tuzilishi yoki xulqi."),
  _d("Issiq cho‘l", "Tuya: o‘rkachida yog‘, uzun kipriklar\nKaktus: qalin poya, tikan", "Cho‘lda suv kam. Tuya yog‘ zaxira qiladi, kaktus suvni poyasida saqlaydi."),
  _d("Sovuq qutb", "Qalin mo‘yna va yog‘ qatlami\nOq rang — yashirinish", "Qutbda sovuq. Hayvonlar qalin mo‘yna va yog‘ bilan issiqni saqlaydi."),
  _d("Suv va tun", "Baliq: jabra, suzgich\nBoyqush: katta ko‘z", "Suvda yashovchilar jabra bilan nafas oladi. Tunda yashovchilar katta ko‘zli bo‘ladi."),
  _d("Maskirovka", "Rang muhitga o‘xshash → yirtqich ko‘rmaydi", "Ba’zi hayvonlarning rangi muhitga o‘xshash. Bu ularni yirtqichdan yashiradi."),
 ]),
 "S4-EKO": _mav("S4-EKO", [
  _d("Oziq zanjiri", "Quyosh → o‘simlik → o‘txo‘r → yirtqich", "Oziq zanjiri energiya yo‘lini ko‘rsatadi. U Quyoshdan boshlanadi."),
  _d("Strelkani o‘qish", "o‘t → quyon → tulki\nstrelka: «yeyiladi va energiya beradi»", "Strelka yeyilayotgandan yeyayotganga qaraydi."),
  _d("Guruhlar", "Produtsent: o‘simlik\nKonsument: hayvon\nParchalovchi: bakteriya, qo‘ziqorin", "O‘simlik oziq yaratadi, hayvon yeydi, parchalovchilar o‘likni tuproqqa qaytaradi."),
  _d("Soni o‘zgarsa", "Quyon ↓ → tulki ↓\nTulki ↓ → quyon ↑", "Zanjirdagi bir halqa o‘zgarsa, boshqalar ham o‘zgaradi."),
  _d("Xato qilmaymiz", "❌ Strelka — kim kimdan qochishi\n✅ Strelka — energiya yo‘nalishi", "Strelka qochishni emas, energiya o‘tishini bildiradi."),
 ]),
 "S4-SOG": _mav("S4-SOG", [
  _d("Sog‘lom ovqat", "Kalsiy — suyak\nOqsil — mushak\nVitamin — himoya", "Turli oziq moddalar tanaga turli foyda beradi."),
  _d("Gigiyena", "Qo‘lni yuvish\nTishni tozalash\nYo‘talganda og‘izni yopish", "Toza yurish kasallikni oldini oladi."),
  _d("Kasallik qanday tarqaladi?", "Mikroblar: havo, qo‘l, suv, oziq", "Mikroblar yo‘tal, tegish yoki iflos suv orqali o‘tadi."),
  _d("Harorat va uyqu", "Normal 36,6°C\nUyqu 9–11 soat", "Harorat normadan yuqori bo‘lsa, kasallik belgisi. Yetarli uyqu o‘sishga kerak."),
  _d("Harakat", "Sport → yurak va mushaklar kuchli", "Harakat yurakni va mushaklarni mustahkamlaydi."),
 ]),
 "S4-MOD": _mav("S4-MOD", [
  _d("Uch holat", "Qattiq → shakl saqlaydi\nSuyuq → idish shaklini oladi\nGaz → hamma yerni to‘ldiradi", "Modda uch holatda bo‘ladi: qattiq, suyuq va gaz."),
  _d("Holat o‘zgarishi", "Erish: qattiq → suyuq\nQaynash: suyuq → gaz\nQotish: suyuq → qattiq", "Isitsak qattiq suyuqqa, suyuq gazga aylanadi. Sovitsak aksincha."),
  _d("Eritma va aralashma", "Eritma: tuz + suv\nAralashma: qum + suv", "Eritmada modda ko‘rinmay qoladi, aralashmada esa qismlar ko‘rinib turadi."),
  _d("Ajratish usullari", "Filtr: qum\nBug‘latish: tuz\nMagnit: temir", "Aralashmani qismlarga ajratish usuli ularning xossasiga bog‘liq."),
  _d("Fizik va kimyoviy", "Muz erishi — fizik\nYonish, zanglash — kimyoviy", "Fizik o‘zgarishda modda o‘zgarmaydi, yonishda esa yangi modda hosil bo‘ladi."),
 ]),
 "S4-ENR": _mav("S4-ENR", [
  _d("Yorug‘lik va soya", "Manba → to‘siq → soya", "Yorug‘lik to‘g‘ri yo‘l bilan tarqaladi. To‘siq yo‘lni to‘ssa, soya hosil bo‘ladi."),
  _d("Qaytish", "Oyna: yorug‘likni qaytaradi\nOy: Quyosh nurini qaytaradi", "Silliq yuza yorug‘likni qaytaradi."),
  _d("Issiqlik o‘tishi", "Metall — o‘tkazadi\nYog‘och, plastmassa — o‘tkazmaydi", "Metall issiqlikni yaxshi o‘tkazadi, yog‘och esa yomon."),
  _d("Elektr zanjiri", "Batareya + sim + lampa\nZanjir BERK bo‘lishi kerak", "Lampa yonishi uchun zanjir berk bo‘lishi kerak."),
  _d("O‘tkazgich va izolyator", "Mis, temir — o‘tkazadi\nRezina, plastmassa — o‘tkazmaydi", "Metallar tokni o‘tkazadi, rezina va plastmassa o‘tkazmaydi."),
 ]),
 "S4-KUC": _mav("S4-KUC", [
  _d("Kuch nima?", "Kuch = itarish yoki tortish\nBirligi: nyuton", "Kuch jismni itaradi yoki tortadi."),
  _d("Og‘irlik kuchi", "Yer hamma jismni o‘ziga tortadi", "Shu sababli narsalar pastga tushadi."),
  _d("Ishqalanish", "Dag‘al yuza → ko‘p\nSilliq yuza → kam", "Ishqalanish harakatga qarshilik qiladi."),
  _d("Magnit va shamol", "Magnit: temirni tortadi\nShamol: yelkanni itaradi", "Magnit temirni tortadi, shamol esa yelkanni itaradi."),
  _d("Arg‘imchoq", "Og‘ir bola yaqinroq, yengil bola uzoqroq", "Muvozanat uchun og‘ir bola markazga yaqin o‘tiradi."),
 ]),
 "S4-YER": _mav("S4-YER", [
  _d("Yer yuzasi", "Ko‘p qismi suv\nQuruqlik: tog‘, tekislik", "Yer yuzasining ko‘p qismi okeanlardan iborat."),
  _d("Tuproq", "Qum — suv o‘tkazadi\nLoy — ushlaydi\nChirindi — unumdor", "Tuproq turlari suvni turlicha ushlaydi."),
  _d("Resurslar", "Tiklanadigan: Quyosh, shamol\nTugaydigan: neft, ko‘mir", "Tugaydigan resurslarni tejash kerak."),
  _d("Tejash", "Suvni tejaymiz\nChiroqni o‘chiramiz\nQayta ishlaymiz", "Har kim kichik qadam bilan tabiatga yordam beradi."),
  _d("Ifloslanish", "Tutun → havo\nChiqindi → suv va tuproq", "Ifloslanish tirik tabiatga zarar qiladi."),
 ]),
 "S4-JAR": _mav("S4-JAR", [
  _d("Ob-havo", "Harorat, shamol, yog‘in, bulut\nTermometr — harorat", "Ob-havo bir necha ko‘rsatkichdan iborat."),
  _d("Suv aylanishi", "Bug‘lanish → bulut → yog‘in → daryo", "Suv hech qachon yo‘qolmaydi, aylanib yuradi."),
  _d("Daryo", "Baland joydan pastga oqadi", "Daryo har doim pastga qarab oqadi."),
  _d("Fossillar", "Qadimgi tirik izi → qatlamlarda topiladi", "Fossillar qadimgi hayot haqida xabar beradi."),
  _d("Fasllar va harorat", "Qish — sovuq, qor\nYoz — issiq", "Fasllarga qarab ob-havo o‘zgaradi."),
 ]),
 "S4-QUY": _mav("S4-QUY", [
  _d("Quyosh tizimi", "Quyosh (yulduz)\nSayyoralar: Merkuriy, Venera, Yer, Mars…", "Quyosh yulduz, Yer esa uchinchi sayyora."),
  _d("Kecha va kunduz", "Yer o‘q atrofida 24 soatda aylanadi", "Yerning yoritilgan tomonida kunduz, soyadagi tomonida kecha."),
  _d("Fasllar", "Yer Quyosh atrofida 365 kunda aylanadi\nO‘q egik → fasllar", "Fasllar Yer o‘qi egilgani va Quyosh atrofida aylanishi tufayli almashadi."),
  _d("Oy", "Yer yo‘ldoshi\n28 kunda aylanadi\nO‘zi yorug‘ emas", "Oy Yer atrofida aylanadi va Quyosh nurini qaytaradi."),
  _d("Quyosh energiyasi", "Quyosh → yorug‘lik + issiqlik → hayot", "Quyosh nuri bo‘lmasa hayot bo‘lmas edi."),
 ]),
}
