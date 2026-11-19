"""PIRLS (4-sinf o'qish savodxonligi): PL-TOP, PL-XUL, PL-TAL, PL-BAH — badiiy va axborot matnlari, 4 ta o'qish jarayoni."""
from modules.pisa_mat_g import reg, _y, _o, _yopiq
from modules import xb_ps

def _tema(kod, nom, belgi, maqsad, dars):
    return {"nom": nom, "soha": "O‘qish", "belgi": belgi, "maqsad": maqsad, "bolim": kod, "toplam": "PIRLS_4", "dars": dars}

def _d(sar, doska, ovoz):
    return {"sarlavha": sar, "doska": doska, "ovoz": ovoz}

# har matn: (matn, TOP[3], XUL[2], TAL[2], BAH[2]); savol = (savol, to'g'ri, [3 noto'g'ri])
T = [
 ("«Bahor keldi. Bobo bog‘ga chiqib, olma ko‘chatlarini ekdi. Nevarasi Aziza unga suv olib keldi. Uch haftadan keyin ko‘chatlarda yashil barglar paydo bo‘ldi.»",
  [("Bobo bog‘ga nima ekdi?", "Olma ko‘chatlarini", ["Uzum tokini", "Gul urug‘ini", "Sabzi urug‘ini"]), ("Aziza bobosiga nima olib keldi?", "Suv", ["Kitob", "Ketmon", "Non"]), ("Ko‘chatlarda qachon barg paydo bo‘ldi?", "Uch haftadan keyin", ["Ertasi kuni", "Bir yildan keyin", "Kuzda"])],
  [("Ko‘chatlar nega barg chiqardi?", "Ularga suv va parvarish berildi", ["Ular plastmassadan edi", "Bobo qo‘shiq aytdi", "Qor yog‘di"]), ("Voqea qaysi fasldan boshlangan?", "Bahordan", ["Qishdan", "Yozdan", "Kuzdan"])],
  [("Matn asosan nima haqida?", "Bobo va nevara ko‘chat ekib parvarishlagani", ["Bahor sovuq bo‘lgani", "Aziza maktabga borgani", "Bog‘ sotilgani"]), ("Aziza qanday bola ekani seziladi?", "Yordamga tayyor", ["Dangasa", "Yolg‘onchi", "Qo‘pol"])],
  [("Muallif bu matn orqali nimani o‘rgatmoqchi?", "Mehnat va parvarish natija beradi", ["Bahor eng yomon fasl", "Bog‘ qurish foydasiz", "Bobolar charchaydi"]), ("Matn sarlavhasi uchun qaysi biri mos?", "Bobo bilan bog‘da", ["Dengiz sayohati", "Futbol o‘yini", "Yangi telefon"])]),
 ("«Ari ninasi bilan chaqqanda ham o‘zi ham halok bo‘ladi. Shuning uchun u faqat xavfda qolganda chaqadi. Bir ari tuzgan asal bir choy qoshiqning o‘n ikkidan bir qismiga teng.»",
  [("Ari qachon chaqadi?", "Xavfda qolganda", ["Har doim", "Tunda", "Uxlaganda"]), ("Ari chaqqach nima bo‘ladi?", "Halok bo‘ladi", ["Asal tuzadi", "Uchib ketadi", "Katta bo‘ladi"]), ("Bir ari qancha asal tuzadi?", "Choy qoshiqning 12 dan bir qismini", ["Bir chelak", "Bir stakan", "Bir kilogramm"])],
  [("Nega ari kamdan-kam chaqadi?", "Chaqqach halok bo‘ladi", ["U chaqishni yoqtirmaydi", "Ninasi yo‘q", "Faqat kechasi uyg‘oq"]), ("Bir qoshiq asal uchun nechta ari ishlashi kerak?", "Taxminan 12 ta", ["1 ta", "2 ta", "100 ta"])],
  [("Matn asosan nima haqida?", "Ari va uning asal tuzishi haqida", ["Qushlar haqida", "Baliqlar haqida", "Mevalar haqida"]), ("«Halok bo‘ladi» so‘ziga ma’nodosh qaysi?", "Nobud bo‘ladi", ["Uxlaydi", "Uchadi", "Kuladi"])],
  [("Bu matn qanday turdagi matn?", "Axborot beruvchi", ["Ertak", "She’r", "Hazil"]), ("Muallif aridan qanday xulosa chiqaradi?", "Ari ehtiyotkor va mehnatkash", ["Ari yovvoyi hayvon", "Ari foydasiz", "Ari yolg‘iz yashaydi"])]),
 ("«Quyon bilan toshbaqa musobaqalashdi. Quyon tez yugurib ketdi va yo‘lda uxlab qoldi. Toshbaqa sekin bo‘lsa-da to‘xtamadi va marraga birinchi yetib keldi.»",
  [("Kim musobaqalashdi?", "Quyon va toshbaqa", ["Tulki va bo‘ri", "Ot va eshak", "Ari va chumoli"]), ("Quyon yo‘lda nima qildi?", "Uxlab qoldi", ["Ovqatlandi", "Yig‘ladi", "O‘ynadi"]), ("Marraga birinchi kim yetdi?", "Toshbaqa", ["Quyon", "Ikkalasi bir vaqtda", "Hech kim"])],
  [("Toshbaqa nega g‘olib bo‘ldi?", "To‘xtamasdan davom etdi", ["Tezroq yugurdi", "Quyonni itardi", "Yo‘lni qisqartirdi"]), ("Quyonning xatosi nima edi?", "O‘ziga ortiqcha ishongani", ["Juda sekin yurgani", "Marrani topolmagani", "Qo‘rqqani"])],
  [("Ertakning asosiy g‘oyasi qaysi?", "Qat’iyat g‘ururdan ustun", ["Tez yugurish eng muhim", "Uxlash foydali", "Musobaqa yomon"]), ("«Marra» so‘zi nimani bildiradi?", "Yugurish tugaydigan joy", ["Boshlanish joyi", "Uxlash joyi", "Suv ichish joyi"])],
  [("Muallif toshbaqani qanday tasvirlagan?", "Sabrli va qat’iyatli", ["Dangasa", "Maqtanchoq", "Qo‘rqoq"]), ("Bu ertak bizga qaysi maqolni eslatadi?", "Sekin borsang, uzoq borasan", ["Ko‘p gapirgan ko‘p biladi", "Tez bor, tez qayt", "Yolg‘iz otning changi chiqmas"])]),
 ("«Samarqandning Registon maydoni uchta madrasadan iborat: Ulug‘bek, Sherdor va Tillakori. Ulug‘bek madrasasi 1420-yilda qurilgan. Har yili bu yerga minglab sayyoh keladi.»",
  [("Registonda nechta madrasa bor?", "Uchta", ["Ikkita", "To‘rtta", "Beshta"]), ("Ulug‘bek madrasasi qachon qurilgan?", "1420-yilda", ["1620-yilda", "1920-yilda", "1220-yilda"]), ("Registonga har yili kimlar keladi?", "Minglab sayyohlar", ["Faqat talabalar", "Hech kim", "Faqat bolalar"])],
  [("Nega Registon mashhur?", "Uchta tarixiy madrasa shu yerda", ["U dengiz bo‘yida", "U yangi qurilgan", "U yopiq maydon"]), ("Matn qaysi shaharga oid?", "Samarqandga", ["Buxoroga", "Xivaga", "Toshkentga"])],
  [("Matnning asosiy fikri qaysi?", "Registon — Samarqandning mashhur tarixiy majmuasi", ["Madrasalar buzilgan", "Samarqand yangi shahar", "Sayyohlar kelmaydi"]), ("«Sayyoh» so‘zining ma’nosi?", "Sayohat qiluvchi kishi", ["Quruvchi", "O‘qituvchi", "Haydovchi"])],
  [("Bu matn nima uchun yozilgan?", "Ma’lumot berish uchun", ["Kuldirish uchun", "Reklama uchun", "Qo‘rqitish uchun"]), ("Matndagi qaysi gap fakt?", "Ulug‘bek madrasasi 1420-yilda qurilgan", ["Registon eng chiroyli joy", "Bu yerga borish zerikarli", "Hamma kelishi shart"])]),
 ("«Dilnoza yangi maktabga bordi. U hech kimni tanimasdi va yuragi tez-tez urardi. Tanaffusda bir qiz unga: «Biz bilan o‘ynaysanmi?» dedi. Dilnoza jilmaydi.»",
  [("Dilnoza qayerga bordi?", "Yangi maktabga", ["Kutubxonaga", "Bog‘ga", "Do‘konga"]), ("Tanaffusda kim unga gapirdi?", "Bir qiz", ["O‘qituvchi", "Direktor", "Bir bola"]), ("Dilnoza nima qildi?", "Jilmaydi", ["Yig‘ladi", "Qochdi", "Baqirdi"])],
  [("Dilnozaning yuragi nega tez urardi?", "U hayajonlangan va hech kimni tanimasdi", ["U yugurgan", "U kasal edi", "U ovqatlangan"]), ("Qizning taklifidan keyin Dilnoza o‘zini qanday his qildi?", "Yengil va xursand", ["Yolg‘iz", "Jahldor", "Uyqusirab"])],
  [("Hikoyaning asosiy mazmuni qaysi?", "Yangi do‘st topish qo‘rquvni yengillashtiradi", ["Maktab yopilgan", "Dilnoza yutqazdi", "Tanaffus qisqa"]), ("Qiz Dilnozaga qanday munosabatda bo‘ldi?", "Mehribon", ["Beparvo", "Jahldor", "Masxara qiluvchi"])],
  [("Muallif nima uchun «yuragi tez-tez urardi» deb yozgan?", "Hayajonni ko‘rsatish uchun", ["Yurak kasalligi uchun", "Yugurishni aytish uchun", "Soatni ko‘rsatish uchun"]), ("Hikoya qanday tugaydi?", "Umidli", ["Qayg‘uli", "Qo‘rqinchli", "Tushunarsiz"])]),
 ("«Quyosh tizimida sakkizta sayyora bor. Merkuriy Quyoshga eng yaqin, Neptun esa eng uzoq. Yer Quyoshdan uchinchi o‘rinda joylashgan va unda hayot mavjud.»",
  [("Quyosh tizimida nechta sayyora bor?", "Sakkizta", ["Yettita", "To‘qqizta", "O‘nta"]), ("Quyoshga eng yaqin sayyora qaysi?", "Merkuriy", ["Neptun", "Yer", "Mars"]), ("Yer Quyoshdan nechanchi o‘rinda?", "Uchinchi", ["Birinchi", "Beshinchi", "Sakkizinchi"])],
  [("Nega Yer alohida ahamiyatli?", "Unda hayot mavjud", ["U eng katta", "U eng issiq", "U Quyoshdan eng uzoq"]), ("Neptun haqida nima aytish mumkin?", "U Quyoshdan eng uzoqda", ["U eng yaqin", "U Yerdan kichik emas", "U Yerdan keyin turadi"])],
  [("Matn nima haqida?", "Quyosh tizimi sayyoralari haqida", ["Yer osti boyliklari haqida", "Okeanlar haqida", "Yulduz yog‘ishi haqida"]), ("«Joylashgan» so‘zi nimani bildiradi?", "O‘rnashgan", ["Yo‘qolgan", "Kichraygan", "Yonib ketgan"])],
  [("Bu matn qaysi turga kiradi?", "Ilmiy-ommabop", ["Ertak", "Hazil", "Reklama"]), ("Matndagi qaysi gap fikr emas, fakt?", "Quyosh tizimida sakkizta sayyora bor", ["Bu juda zerikarli", "Hamma Marsga borishi kerak", "Neptun eng chiroyli"])]),
 ("«Sherzod do‘konga borib, uchta non va bitta sut oldi. Non 2 000 so‘m, sut 8 000 so‘m turadi. Sotuvchi unga rahmat aytdi. Sherzod sutni ehtiyotkorlik bilan sumkasiga soldi.»",
  [("Sherzod nechta non oldi?", "Uchta", ["Bitta", "Ikkita", "To‘rtta"]), ("Sut necha so‘m?", "8 000 so‘m", ["2 000 so‘m", "6 000 so‘m", "10 000 so‘m"]), ("Sotuvchi nima dedi?", "Rahmat", ["Xayr", "Kechirasiz", "Tezroq"])],
  [("Sherzod nega sutni ehtiyotkorlik bilan soldi?", "Sut to‘kilmasligi uchun", ["U sutdan qo‘rqdi", "Sut juda og‘ir edi", "U sutni yoqtirmaydi"]), ("Sherzod nechta mahsulot turini oldi?", "Ikki turini: non va sut", ["Bir turini", "Uch turini", "Besh turini"])],
  [("Hikoya asosan nima haqida?", "Sherzodning do‘kondan xarid qilgani", ["Maktab sayohati", "Sport musobaqasi", "Bog‘ ekish"]), ("Sherzod qanday bola?", "Ehtiyotkor", ["Beparvo", "Dangasa", "Qo‘pol"])],
  [("Muallif nega narxlarni yozgan?", "Voqeani aniq va ishonarli qilish uchun", ["Reklama qilish uchun", "Do‘konni sotish uchun", "Sonlarni o‘rgatish uchun faqat"]), ("Bu matn qaysi turga yaqin?", "Kundalik hikoya", ["Ilmiy maqola", "Reklama e’loni", "Qonun matni"])]),
 ("«Qishda ayiqlar uzoq uyquga ketadi. Bu davrda ular ovqatlanmaydi, chunki kuzda yig‘ilgan yog‘ bilan yashaydi. Bahorda ular uyg‘onib, oziq izlay boshlaydi.»",
  [("Ayiqlar qishda nima qiladi?", "Uzoq uyquga ketadi", ["Janubga uchadi", "Ko‘p ovqatlanadi", "Suvda suzadi"]), ("Ular qachon uyg‘onadi?", "Bahorda", ["Kuzda", "Yozda", "Qishning o‘rtasida"]), ("Ular uyqu paytida nima bilan yashaydi?", "Kuzda yig‘ilgan yog‘ bilan", ["Qor bilan", "Suv bilan", "Daraxt bilan"])],
  [("Ayiq nega kuzda ko‘p ovqatlanadi?", "Qishga yog‘ yig‘ish uchun", ["Qorin og‘rigani uchun", "Ovqat arzon uchun", "Bahorni kutish uchun"]), ("Agar ayiq kuzda kam ovqatlansa nima bo‘lishi mumkin?", "Qishda quvvati yetmasligi mumkin", ["Uxlamaydi", "Tezroq o‘sadi", "Hech narsa bo‘lmaydi"])],
  [("Matnning asosiy g‘oyasi qaysi?", "Ayiqlar qishga yog‘ yig‘ib, uxlab o‘tkazadi", ["Ayiqlar qushga o‘xshaydi", "Ayiqlar suvda yashaydi", "Ayiqlar hech uxlamaydi"]), ("«Oziq» so‘zining ma’nosi?", "Yeyiladigan narsa", ["Ichimlik idishi", "Uy", "Yo‘l"])],
  [("Bu matnni kim yozgan bo‘lishi mumkin?", "Hayvonot haqida bilimdon odam", ["Reklama agenti", "Futbolchi", "Haydovchi"]), ("Matndagi ma’lumot ishonchlimi?", "Ha, ilmiy faktga tayanadi", ["Yo‘q, u hazil", "Yo‘q, u ertak", "Bilib bo‘lmaydi hech qachon"])]),
 ("«Mansur kitob o‘qishni yoqtirmasdi. Bir kuni buvisi unga sarguzasht haqidagi kitob berdi. Mansur bir bobni o‘qidi, keyin yana bir bobni. Kechgacha butun kitobni tugatib qo‘ydi.»",
  [("Mansur nimani yoqtirmasdi?", "Kitob o‘qishni", ["Futbolni", "Ovqatni", "Maktabni"]), ("Kitobni kim berdi?", "Buvisi", ["Opasi", "Do‘sti", "O‘qituvchisi"]), ("Mansur kitobni qachon tugatdi?", "Kechgacha", ["Ertasi kuni", "Bir haftada", "Ertalab"])],
  [("Mansur nega butun kitobni o‘qib chiqdi?", "Kitob unga qiziq bo‘lib qoldi", ["Majbur qilishdi", "Imtihon bor edi", "Boshqa ish yo‘q edi"]), ("Voqea Mansurni qanday o‘zgartirdi?", "U o‘qishni yoqtirib qoldi", ["U o‘qishdan qo‘rqdi", "U kitobni yo‘qotdi", "U buvisiga xafa bo‘ldi"])],
  [("Hikoyaning asosiy mazmuni qaysi?", "To‘g‘ri kitob o‘qishga havas uyg‘otadi", ["Buvi uzoqda yashaydi", "Mansur kasal bo‘ldi", "Kitob qimmat"]), ("«Sarguzasht» nima?", "Qiziqarli, xavfli voqealar", ["Uzun yo‘l", "Maktab fani", "Ovqat turi"])],
  [("Muallif nega «keyin yana bir bobni» deb yozgan?", "Mansurning qiziqishi ortganini ko‘rsatish uchun", ["Kitob qisqa ekanini aytish uchun", "Bob soni muhimligi uchun", "Zerikishini ko‘rsatish uchun"]), ("Hikoyaning ohangi qanday?", "Iliq va umidbaxsh", ["Qo‘rqinchli", "Qayg‘uli", "Kinoyali"])]),
 ("«Daryolar tog‘lardan boshlanadi. Qor va muz erib, suv bo‘lib pastga oqadi. Daryo oxir-oqibat ko‘l yoki dengizga quyiladi. Daryo suvi dalalarni sug‘orish uchun ishlatiladi.»",
  [("Daryolar qayerdan boshlanadi?", "Tog‘lardan", ["Cho‘llardan", "Dengizdan", "Shaharlardan"]), ("Daryo oxirida qayerga quyiladi?", "Ko‘l yoki dengizga", ["Tog‘ga", "Bulutga", "Qumga"]), ("Daryo suvi nimaga ishlatiladi?", "Dalalarni sug‘orishga", ["Uy qurishga", "Yo‘l solishga", "Havo tozalashga"])],
  [("Daryoda suv qayerdan paydo bo‘ladi?", "Qor va muzning erishidan", ["Yomg‘irsiz hosil bo‘ladi", "Yer ostidan qazib olinadi", "Dengizdan keladi"]), ("Agar tog‘larda qor kam bo‘lsa, daryoga nima bo‘ladi?", "Suvi kamayishi mumkin", ["Suvi ko‘payadi", "Ko‘lga aylanadi", "Hech narsa"])],
  [("Matn nima haqida?", "Daryolarning boshlanishi va foydasi haqida", ["Tog‘ ko‘tarish haqida", "Qor odam haqida", "Baliq ovlash haqida"]), ("«Oxir-oqibat» nimani bildiradi?", "Nihoyat, so‘ngida", ["Boshida", "Hech qachon", "Har doim"])],
  [("Bu matn nima maqsadda yozilgan?", "Daryo haqida bilim berish", ["Sayohatga chaqirish", "Reklama qilish", "Qo‘rqitish"]), ("Matnga qaysi sarlavha mos?", "Daryo yo‘li", ["Tez yugurish", "Yangi o‘yinchoq", "Qishki sport"])]),
 ("«Navro‘z — bahor bayrami. U 21-martda nishonlanadi. Bu kuni odamlar sumalak pishiradi, ko‘kat ekadi va bir-birini tabriklaydi. Navro‘zda tabiat uyg‘onadi.»",
  [("Navro‘z qaysi kuni nishonlanadi?", "21-martda", ["1-yanvarda", "1-sentyabrda", "21-iyulda"]), ("Navro‘zda nima pishiriladi?", "Sumalak", ["Osh faqat", "Tort", "Shashlik"]), ("Navro‘z qaysi fasl bayrami?", "Bahor", ["Qish", "Yoz", "Kuz"])],
  [("Nega Navro‘z bahorda nishonlanadi?", "Bu paytda tabiat uyg‘onadi", ["Bahor sovuq bo‘ladi", "Qor yog‘adi", "Maktablar yopiladi"]), ("Ko‘kat ekish nimani anglatadi?", "Yangi hayot boshlanishini", ["Qish kelishini", "Urush boshlanishini", "Ovqat tugashini"])],
  [("Matnning asosiy fikri qaysi?", "Navro‘z — tabiat uyg‘onishi va tabriklash bayrami", ["Sumalak faqat qishda pishadi", "Bayram yo‘q", "Hamma uyda yotadi"]), ("«Tabriklaydi» so‘zi nimani anglatadi?", "Xushxabar bilan qutlaydi", ["Urishadi", "Qochadi", "Uxlaydi"])],
  [("Matndagi qaysi gap fikr (baho)?", "Navro‘zda tabiat uyg‘onadi — bu eng go‘zal fasl", ["Navro‘z 21-martda", "Sumalak pishiriladi", "Ko‘kat ekiladi"]), ("Bu matn qaysi maqsadda yozilgan?", "Bayram haqida ma’lumot berish", ["Mahsulot sotish", "Sayohatga chaqirish", "Hazillashish"])]),
 ("«Bir bor ekan, bir yo‘q ekan, o‘rmonda kichik tulki yashagan ekan. U har kuni qarg‘adan pishloq o‘g‘irlashga urinarkan. Bir kuni qarg‘a: «Yolg‘on gapirma, men seni tanidim!» deb pishloqni yutib yuboribdi.»",
  [("O‘rmonda kim yashagan?", "Kichik tulki", ["Katta ayiq", "Quyon", "Bo‘ri"]), ("Tulki nimani o‘g‘irlamoqchi bo‘lgan?", "Pishloqni", ["Olmani", "Asalni", "Tuxumni"]), ("Qarg‘a nima dedi?", "Yolg‘on gapirma, men seni tanidim", ["Menga yordam ber", "Rahmat", "Kechir"])],
  [("Qarg‘a nega pishloqni berib yubormadi?", "U tulkining hiylasini tushundi", ["U pishloqni yoqtirmadi", "U tulkidan qo‘rqdi", "U ochiqmadi"]), ("Tulkining rejasi nima bo‘ldi?", "Amalga oshmadi", ["Muvaffaqiyatli bo‘ldi", "Ikkalasi ham yutdi", "Qarg‘a ketib qoldi"])],
  [("Ertakning asosiy g‘oyasi qaysi?", "Yolg‘on va hiyla har doim ish bermaydi", ["Tulki eng aqlli", "Qarg‘a qo‘rqoq", "Pishloq foydali"]), ("«Bir bor ekan, bir yo‘q ekan» nimani anglatadi?", "Ertak boshlanishi", ["Hisob-kitobni", "Maktab zangini", "Do‘kon e’lonini"])],
  [("Muallif tulkini qanday tasvirlaydi?", "Hiylakor", ["Mehribon", "Halol", "Qo‘rqoq"]), ("Siz qarg‘aning qilmishini qanday baholaysiz?", "Ehtiyotkorlik ko‘rsatdi, to‘g‘ri qildi", ["Yomon ish qildi", "Behuda ish qildi", "Hech narsa demaydi"])]),
]

def _x(kod, idx):
    out = []
    for ti, row in enumerate(T):
        for qi, (sv, tj, no) in enumerate(row[idx]):
            out.append((ti, qi, row[0], sv, tj, no))
    return out

_ST = {"PL-TOP": 1, "PL-XUL": 2, "PL-TAL": 3, "PL-BAH": 4}
xb_ps._matnlar.update({k: [(r[0], r[i]) for r in T] for k, i in _ST.items()})

def _qur(kod):
    for ti, qi, matn, sv, tj, no in _x(kod, _ST[kod]):
        def f(rng, matn=matn, sv=sv, tj=tj, no=no):
            return _yopiq(rng, f"{matn}\n\n{sv}", tj, ["Javobni matndan topib, mantiq bilan tekshiring."], noto=list(no), tartib=False)
        f.__name__ = f"{kod}_t{ti}_{qi}"
        reg(kod, "yopiq")(f)
for _k in _ST:
    _qur(_k)

# ochiq savollar: sonlar o'zgaradi (matndagi raqamni topish / hisoblash)
@reg("PL-TOP", "ochiq")
def top_son(rng):
    n = rng.choice([2, 3, 4, 5, 6]); p = rng.choice([2000, 3000, 4000, 5000])
    return _o(f"Matnda: «Sherzod do‘konga borib {n} ta non oldi. Har bir non {p} so‘m turadi.»", [("a) Sherzod nechta non oldi?", n), ("b) Bitta non necha so‘m?", p)], ["Raqamlar matnning o‘zida berilgan."])

@reg("PL-XUL", "ochiq")
def xul_son(rng):
    n = rng.choice([2, 3, 4, 5]); p = rng.choice([2000, 3000, 4000])
    return _o(f"Matnda: «Sherzod {n} ta non oldi. Har bir non {p} so‘m.» Sherzod {n * p + 8000} so‘m to‘ladi, shundan 8 000 so‘mi sut uchun.", [("a) Nonlar uchun necha so‘m to‘lagan?", n * p), ("b) Bitta nonning narxi necha so‘m?", p)], [f"a) {n * p + 8000} − 8 000 = {n * p}.", f"b) {n * p} : {n} = {p}."])

@reg("PL-TAL", "ochiq")
def tal_son(rng):
    a = rng.choice([4, 5, 6]); b = rng.choice([2, 3])
    return _o(f"Matnda ertak qahramonlari: {a} ta hayvon va {b} ta qush.", [("a) Jami nechta qahramon?", a + b), ("b) Hayvonlar qushlardan nechtaga ko‘p?", a - b)], [f"a) {a} + {b} = {a + b}.", f"b) {a} − {b} = {a - b}."])

@reg("PL-BAH", "ochiq")
def bah_son(rng):
    f, p = rng.choice([(3, 2), (4, 1), (5, 2), (2, 3), (4, 3)])
    return _o(f"Matnda {f} ta fakt va {p} ta fikr (baho) bor.", [("a) Jami nechta gap?", f + p), ("b) Faktlar fikrlardan nechtaga ko‘p?", f - p)], [f"a) {f} + {p} = {f + p}.", f"b) {f} − {p} = {f - p}."])

# o'tish uchun: har matnning har jarayoni bo'yicha aralash savol (4 jarayon — 4 kalit so'z)
_TEMA = {
 "PL-TOP": ("Aniq ma’lumotni topish", "🔎", "Matndagi aniq gap, raqam, ism va joyni topish",
            [_d("Topish strategiyasi", "1. Savolni o‘qi\n2. Kalit so‘zni belgila\n3. Matndan shu so‘zni top\n4. Javobni tekshir", "Savoldagi kalit so‘zni belgilang va matndan aynan shu so‘z yoki unga yaqin so‘zni qidiring. Javob odatda shu gapning ichida bo‘ladi.")]),
 "PL-XUL": ("To‘g‘ridan-to‘g‘ri xulosa chiqarish", "🧩", "Sabab va oqibatni, voqealar ketma-ketligini matndan topish",
            [_d("Xulosa qanday chiqariladi", "Matnda ochiq yozilmagan\nLekin matndan kelib chiqadi\nChunki → sabab\nShuning uchun → oqibat", "Xulosa matnda so‘zma-so‘z yozilmagan, lekin aytilgan gaplardan mantiqan kelib chiqadi. «Chunki» sabab, «shuning uchun» oqibatni bildiradi.")]),
 "PL-TAL": ("Talqin qilish va umumlashtirish", "📖", "Asosiy g‘oya, mavzu va qahramon xarakterini tushunish",
            [_d("Asosiy g‘oya", "Matn nima haqida?\nMuallif nimani o‘rgatmoqchi?\nQahramon qanday?", "Asosiy g‘oya butun matnning mazmunini qamrab oladi. Avval matn nima haqida ekanini, keyin muallif bizga nimani o‘rgatmoqchi ekanini o‘ylang.")]),
 "PL-BAH": ("Mazmun va tilni baholash", "⚖️", "Fakt va fikrni ajratish, muallif maqsadi, tasvir va ohang",
            [_d("Matnni baholash", "Fakt — tekshiriladi\nFikr — baho\nMuallif maqsadi: o‘rgatish / kuldirish / ishontirish\nOhang: iliq, qayg‘uli, hazil", "Fakt tekshirib bo‘ladigan ma’lumot, fikr esa muallifning bahosi. Muallif nega aynan shu so‘zlarni tanlaganini o‘ylab, matn ohangini aniqlang.")]),
}
TEMA = {k: _tema(k, v[0], v[1], v[2], v[3]) | {"toplam": "PIRLS_4"} for k, v in _TEMA.items()}

# qo'shimcha ochiq savollar (har seedda boshqa sonlar) — har mavzuda kamida 30 ta har xil savol uchun
def _qosh_ochiq(kod, shablon):
    for i, sh in enumerate(shablon):
        sh.__name__ = f"{kod}_oo{i}"
        reg(kod, "ochiq")(sh)

def _mk(kod, fmt):
    def a(rng):
        n = rng.randint(12, 48); m = rng.randint(3, 9)
        return _o(fmt[0].format(n=n, m=m), [(fmt[1], n), (fmt[2], n - m)], [f"Birinchi javob matnda berilgan: {n}.", f"{n} − {m} = {n - m}."])
    def b(rng):
        k = rng.randint(3, 8); s = rng.randint(2, 6)
        return _o(fmt[3].format(k=k, s=s), [(fmt[4], k * s), (fmt[5], k)], [f"{k} · {s} = {k * s}.", f"Matnda aytilgan: {k}."])
    return [a, b]

_qosh_ochiq("PL-TOP", _mk("PL-TOP", ["Matnda: «Kutubxonada {n} ta kitob bor edi, {m} tasini o‘quvchilar olib ketdi.»", "a) Kutubxonada dastlab nechta kitob bor edi?", "b) Kitoblardan keyin nechta qoldi?",
    "Matnda: «Har bir javonda {s} ta kitob, jami {k} ta javon bor.»", "a) Jami nechta kitob?", "b) Nechta javon bor?"]))
_qosh_ochiq("PL-XUL", _mk("PL-XUL", ["Matnda: «Sinfda {n} ta o‘quvchi bor edi. {m} tasi kasal bo‘lib, darsga kelmadi.»", "a) Sinfdagi jami o‘quvchilar soni?", "b) Darsga nechta o‘quvchi keldi?",
    "Matnda: «{k} ta bola har biri {s} tadan olma terdi.»", "a) Jami nechta olma terildi?", "b) Nechta bola olma terdi?"]))
_qosh_ochiq("PL-TAL", _mk("PL-TAL", ["Ertakda {n} ta qahramon bor, shundan {m} tasi hayvon.", "a) Ertakda jami nechta qahramon bor?", "b) Hayvon bo‘lmagan qahramonlar soni?",
    "Hikoyada {k} ta bob bor, har bobda {s} ta sahifa.", "a) Hikoya jami nechta sahifa?", "b) Hikoyada nechta bob bor?"]))
_qosh_ochiq("PL-BAH", _mk("PL-BAH", ["Matnda {n} ta gap bor, ulardan {m} tasi fikr (baho).", "a) Matnda jami nechta gap bor?", "b) Faktlar soni nechta?",
    "Matnda {k} ta abzats, har birida {s} ta gap.", "a) Jami nechta gap?", "b) Nechta abzats bor?"]))

_E = {
 "PL-TOP": ["Matnda: «Maktab bog‘ida {n} ta daraxt bor, {m} tasi olma.»", "Matnda: «Sinf devorida {n} ta rasm, shundan {m} tasi hayvon rasmi.»", "Matnda: «Qishloqda {n} ta uy bor, {m} tasi yangi.»"],
 "PL-XUL": ["Matnda: «Maktabga {n} ta bola keldi, {m} tasi qizlar.»", "Matnda: «Savatda {n} ta meva bor edi, {m} tasi olma.»", "Matnda: «Qushlar to‘dasi {n} ta, {m} tasi uchib ketdi.»"],
 "PL-TAL": ["Hikoyada {n} ta qahramon, {m} tasi bolalar.", "Maqolada {n} ta gap, {m} tasi savol.", "Ertakda {n} ta sahna, {m} tasi o‘rmonda."],
 "PL-BAH": ["Reklamada {n} ta ibora, {m} tasi isbotsiz da’vo.", "Maqolada {n} ta gap, {m} tasi muallif fikri.", "E’londa {n} ta jumla, {m} tasi narx haqida."],
}
for _kod, _L in _E.items():
    def _mkk(txt):
        def f(rng):
            n = rng.randint(10, 60); m = rng.randint(2, 9)
            return _o(txt.format(n=n, m=m), [("a) Jami nechta?", n), ("b) Qolgani nechta?", n - m)], [f"a) Matnda: {n}.", f"b) {n} − {m} = {n - m}."])
        return f
    for _i, _t in enumerate(_L):
        _f = _mkk(_t); _f.__name__ = f"{_kod}_oe{_i}"
        reg(_kod, "ochiq")(_f)
