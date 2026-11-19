"""PISA fan (PS-*) va o'qish (PR-*): kengaytirilgan banklar va qo'lda yozilgan darslar."""
from fractions import Fraction

from modules.pisa_mat_g import reg, num, _o, _yopiq
from modules import xb_ps
from modules.xb_ps import _qosh, _d, _matnlar, _o as _unused  # noqa
from modules.xb_ps import TEMA as _T0

def _b(sv, tj, no, iz=""):
    return (sv, tj, no, iz or f"To‘g‘ri javob: {tj}.")

_qosh("PS-TUS", [
    _b("Nima uchun metall qoshiq issiq choyda tez qiziydi?", "Metall issiqlikni yaxshi o‘tkazadi", ["Metall issiqlikni yutmaydi", "Choy sovuq", "Qoshiq yengil"], "O‘tkazuvchanlik."),
    _b("Nima uchun qishda parkini kiyganda issiq bo‘ladi?", "Pat/jun orasidagi havo issiqlikni ushlab qoladi", ["Parka issiqlik chiqaradi", "Parka sovuqni yutadi", "Parka og‘ir"], "Havo yomon issiqlik o‘tkazgich."),
    _b("Nima uchun suv bilan to‘la shisha muzlatgichda yoriladi?", "Muzlaganda suv kengayadi", ["Suv kamayadi", "Shisha erib ketadi", "Havo ko‘payadi"], "Muz hajmi katta."),
    _b("Nima uchun samolyot uchadi?", "Qanotga havo bosimi ko‘taruvchi kuch beradi", ["Havo yo‘q", "Yer tortmaydi", "Motorsiz"], "Aerodinamika."),
    _b("Nima uchun Yer yuzasida kecha kunduz almashadi?", "Yer o‘z o‘qi atrofida aylanadi", ["Quyosh aylanadi", "Oy tutiladi", "Bulut"], "Aylanish."),
    _b("Nima uchun shamollagan odam yo‘talganda tarqatadi?", "Mikroblar tomchilar bilan chiqadi", ["Hid", "Rang", "Tovush"], "Tomchi yuqumi."),
    _b("Nima uchun kema po‘latdan bo‘lsa ham suzadi?", "Umumiy zichligi suvnikidan kam", ["Po‘lat yengil", "Suv qotadi", "Kemada motor bor"], "Arximed kuchi."),
    _b("Nima uchun kechasi yer sovib ketadi?", "Quyosh issiqligi kelmaydi va yer issiqlikni chiqaradi", ["Oy sovuq", "Havo qiziydi", "Yer to‘xtaydi"], "Nurlanish."),
    _b("Nima uchun shisha oynada tasvir ko‘rinadi?", "Yorug‘lik qaytadi", ["Yorug‘lik yutiladi", "Shisha yorug‘ chiqaradi", "Oyna isiydi"], "Qaytish."),
    _b("Nima uchun o‘simlik yorug‘ tomonga egiladi?", "Yorug‘likka intilish (fototropizm)", ["Shamol", "Suv yo‘q", "Tuproq qattiq"], "Barg yorug‘likni ko‘proq oladi."),
    _b("Nima uchun cho‘lda kechasi sovuq, kunduzi issiq?", "Qum va quruq havo issiqlikni tez yo‘qotadi", ["Quyosh yo‘q", "Oy qizdiradi", "Suv ko‘p"], "Nam kam."),
    _b("Nima uchun ko‘pchilik hayvonlar qishda uyquga ketadi?", "Oziq kam, energiyani tejaydi", ["Qor yoqadi", "Uxlagisi keladi", "Suv bor"], "Moslashish."),
])
_qosh("PS-TAJ", [
    _b("Tajriba natijalari jadvali nima uchun kerak?", "Ma’lumotni tartibli yozish va taqqoslash uchun", ["Bezatish uchun", "Hech narsa uchun", "Faqat baholash"], "Jadval tartib beradi."),
    _b("Qaysi o‘lchash aniqroq?", "Bir necha marta o‘lchab o‘rtachasini olish", ["Bir marta o‘lchash", "Ko‘z bilan taxmin", "O‘lchamaslik"], "Xatoni kamaytiradi."),
    _b("Mustaqil o‘zgaruvchi nima?", "Tadqiqotchi o‘zgartiradigan omil", ["Natija", "Doimiy omil", "Asbob"], "Masalan, yorug‘lik miqdori."),
    _b("Bog‘liq o‘zgaruvchi nima?", "O‘lchanadigan natija", ["O‘zgartiriladigan omil", "Doimiy omil", "Gipoteza"], "Masalan, o‘simlik bo‘yi."),
    _b("Gipotezani rad etish mumkinmi?", "Ha, tajriba natijasi qarama-qarshi bo‘lsa", ["Yo‘q, hech qachon", "Faqat o‘qituvchi", "Faqat bir marta"], "Fan o‘zgaradi."),
    _b("Nima uchun katta namuna yaxshi?", "Tasodifiy farqlar o‘rtacha chiqib ketadi", ["Tezroq tugaydi", "Arzon", "Qiziqarli"], "Ishonchlilik."),
    _b("Grafikda o‘q nomlari nimani bildiradi?", "Qaysi kattalik va birligi", ["Muallif", "Sana", "Rang"], "Aniqlik."),
    _b("Tajriba xavfsizligi uchun nima qilinadi?", "Himoya ko‘zoynagi va qo‘lqop", ["Shoshilish", "Eslab qolmaslik", "Yolg‘iz ishlash"], "Xavfsizlik."),
    _b("Ikki guruh solishtiriladi, ammo biriga ko‘proq suv berilgan. Nima noto‘g‘ri?", "Faqat bir omil farq qilishi kerak edi", ["Hammasi to‘g‘ri", "Guruhlar kam", "Suv yaxshi"], "Nazorat."),
    _b("Olingan natija kutilganga zid bo‘lsa?", "Natijani halol yozib, sababini tekshirish", ["Natijani o‘zgartirish", "Yashirish", "Tajribani tashlash"], "Ilmiy halollik."),
    _b("Tajribada «nazorat» o‘zgaruvchilar nima?", "Bir xil saqlanadigan omillar", ["O‘zgartiriladigan", "Natija", "Asbob"], "Adolat."),
])
_qosh("PS-MAL", [
    _b("Diagrammada ustun balandroq bo‘lsa?", "Qiymat kattaroq", ["Qiymat kichikroq", "Vaqt ko‘proq", "Xato bor"], "Ustun balandligi qiymat."),
    _b("Chiziqli grafik tepaga ketsa?", "Kattalik ortmoqda", ["Kamaymoqda", "O‘zgarmaydi", "Noma’lum"], "Trend."),
    _b("«Yomg‘ir yog‘sa soyabon sotuvi oshadi» — bu...", "Bog‘liqlik (sabab emas, ikkalasi ob-havoga bog‘liq)", ["Soyabon yomg‘ir sababi", "Tasodif", "Qonun"], "Ehtiyot bo‘l."),
    _b("Ishonchli ma’lumot manbasini qanday aniqlaymiz?", "Muallif, sana va dalil borligiga qarab", ["Rasmiga qarab", "Uzunligiga qarab", "Reytingiga faqat"], "Tekshirish."),
    _b("Ma’lumotni qisman ko‘rsatish (faqat qulay qismi) nima?", "Xolis emas, manipulyatsiya", ["Odatiy", "Ilmiy", "Yaxshi"], "Hammasini ko‘rsat."),
    _b("Grafik o‘qida 0 dan boshlanmasa?", "Farq bo‘rttirib ko‘rinishi mumkin", ["Farq kichrayadi", "O‘zgarmaydi", "Xato yo‘q"], "Masshtabga e’tibor."),
    _b("O‘rtacha 50, eng katta 500 bo‘lsa, eng katta qiymat...", "Chetki qiymat bo‘lishi mumkin", ["Odatiy", "O‘rtachaga teng", "Xato emas"], "Outlier."),
    _b("Ikki o‘zgaruvchi orasidagi bog‘liqlikni qaysi grafik yaxshi ko‘rsatadi?", "Nuqtali (scatter)", ["Doira", "Jadval nomi", "Matn"], "Bog‘liqlik."),
    _b("Ilmiy da’vo uchun eng kuchli dalil?", "Ko‘p marta takrorlangan tajribalar", ["Bir kishi fikri", "Reklama", "Mashhur kishi"], "Takrorlanish."),
    _b("«Kuniga 1 kishi o‘ldi, 2 kishi tuzaldi» tipidagi gapda nimani tekshirish kerak?", "Umumiy son va muddat", ["Rang", "Hajm", "Mualliflik"], "Kontekst."),
])

_PS = {
 "PS-TUS": [("Ilmiy tushuntirish tuzilishi", "Hodisa → qonun → sabab → xulosa", "Ilmiy tushuntirish hodisani qonun bilan bog‘laydi: nima bo‘ldi, qaysi qonun, nima uchun."),
   ("Issiqlik va moddalar", "Metall — o‘tkazadi\nHavo, yog‘och — izolyator\nMuz — kengayadi", "Metall issiqlikni yaxshi o‘tkazadi, havo yomon. Suv muzlaganda kengayadi."),
   ("Kuch va suzish", "F = m·g\nρ jism < ρ suv → suzadi\nZichlik = m/V", "Jism suzishi zichligiga bog‘liq. Kema umumiy zichligi suvdan kam bo‘lgani uchun suzadi."),
   ("Yorug‘lik va hayot", "Qaytish: oyna\nFotosintez: CO₂ + H₂O → glyukoza + O₂", "Yorug‘lik qaytadi, o‘simlik yorug‘likdan oziq yaratadi."),
   ("Xato qilmaymiz", "❌ Sovuq issiqlikka kiradi\n✅ Issiqlik issiqdan sovuqqa o‘tadi", "Sovuq narsa alohida modda emas: issiqlik chiqib ketishi natijasida jism soviydi.")],
 "PS-TAJ": [("Tadqiqot bosqichlari", "Savol → gipoteza → tajriba → natija → xulosa", "Ilmiy tadqiqot savoldan boshlanadi va xulosa bilan tugaydi."),
   ("O‘zgaruvchilar", "Mustaqil: o‘zgartiramiz\nBog‘liq: o‘lchaymiz\nNazorat: o‘zgarmaydi", "Faqat bitta omil o‘zgartiriladi, boshqalar bir xil saqlanadi."),
   ("Natijani baholash", "O‘rtacha = yig‘indi / soni\nFoiz = qism / butun · 100", "Takroriy o‘lchashlar o‘rtachasini olamiz, ulushni foizda ifodalaymiz."),
   ("Grafik o‘qish", "O‘q nomlari, birlik, trend", "Grafikda avval o‘qlar nomini va birligini o‘qiymiz, keyin trendni aytamiz."),
   ("Xato qilmaymiz", "❌ Bir marta o‘lchab xulosa\n✅ Takrorlab, o‘rtacha olish", "Bir marta o‘lchash tasodifiy xatoga sabab bo‘lishi mumkin.")],
 "PS-MAL": [("Ma’lumotni o‘qish", "Jadval → grafik → trend", "Avval ma’lumotning turini aniqlaymiz, keyin trendni topamiz."),
   ("Bog‘liqlik va sabab", "Birga o‘zgarish ≠ sabab", "Ikki kattalik birga o‘zgarsa ham, biri ikkinchisining sababi bo‘lmasligi mumkin."),
   ("Manba ishonchliligi", "Muallif, sana, dalil, takrorlanish", "Ishonchli manbada muallif, sana va dalil ko‘rsatiladi."),
   ("Grafik qopqonlari", "0 dan boshlanmagan o‘q\nQisman ma’lumot\nChetki qiymat", "Grafikda masshtab o‘zgarishi farqni bo‘rttirishi mumkin."),
   ("Xulosa yozish", "Dalil → fikr\nKichik namuna — zaif", "Xulosa faqat yetarli dalilga tayanishi kerak.")],
}

def _pm(kod, lst):
    t = dict(_T0[kod]); t["dars"] = [_d(a, b, c) for a, b, c in lst]; return t

# ───── PISA o'qish: ko'proq matn ─────
_YANGI = {
"PR-TOP": [
 ("«Toshkent metrosi 1977-yilda ochilgan. U O‘rta Osiyodagi birinchi metro edi. Hozir uch chiziq va 40 dan ortiq bekat bor.»",
  [("Toshkent metrosi qachon ochilgan?", "1977-yilda", ["1991-yilda", "1950-yilda", "2000-yilda"]), ("Matnga ko‘ra metro qayerdagi birinchi?", "O‘rta Osiyoda", ["Yevropada", "Osiyoda", "Afrikada"])]),
 ("«Zarafshon daryosi Zarafshon tizmasidan boshlanadi va Samarqand hamda Buxoro vohalarini suv bilan ta’minlaydi. Uzunligi taxminan 877 km.»",
  [("Zarafshon qaysi vohalarni suv bilan ta’minlaydi?", "Samarqand va Buxoro", ["Xorazm", "Farg‘ona", "Surxondaryo"]), ("Daryo uzunligi?", "Taxminan 877 km", ["100 km", "5000 km", "50 km"])]),
 ("«Kutubxona dushanbadan jumagacha 9:00 dan 18:00 gacha, shanba kuni 10:00 dan 14:00 gacha ishlaydi. Yakshanba — dam olish kuni.»",
  [("Kutubxona shanba kuni qachongacha ochiq?", "14:00 gacha", ["18:00 gacha", "12:00 gacha", "Yopiq"]), ("Qaysi kun yopiq?", "Yakshanba", ["Shanba", "Juma", "Dushanba"])]),
 ("«Mevalar tarkibida vitamin va tolalar ko‘p. Bolalar kuniga kamida besh porsiya meva va sabzavot iste’mol qilishi tavsiya etiladi.»",
  [("Kuniga nechta porsiya tavsiya?", "Kamida besh", ["Bitta", "Ikkita", "O‘n"]), ("Mevalarda nimalar ko‘p?", "Vitamin va tolalar", ["Yog‘", "Tuz", "Shakar faqat"])]),
 ("«Kitob ko‘rgazmasi 12-aprelda boshlanib, 15-aprelda tugaydi. Kirish bepul. Maktab o‘quvchilari uchun ekskursiya soat 11:00 da.»",
  [("Ko‘rgazma necha kun davom etadi?", "4 kun (12–15 aprel)", ["1 kun", "10 kun", "2 kun"]), ("Ekskursiya soat nechada?", "11:00 da", ["9:00 da", "15:00 da", "18:00 da"])]),
 ("«Quyosh batareyalari Quyosh nurini elektr energiyasiga aylantiradi. Ular chiqindi chiqarmaydi, lekin bulutli kunlarda kam energiya beradi.»",
  [("Quyosh batareyasi nimani nimaga aylantiradi?", "Quyosh nurini elektrga", ["Elektrni nurga", "Suvni bug‘ga", "Shamolni nurga"]), ("Kamchiligi nima?", "Bulutli kunda kam energiya beradi", ["Chiqindi chiqaradi", "Juda og‘ir", "Ovozi baland"])]),
 ("«Alisher Navoiy 1441-yilda Hirotda tug‘ilgan. U o‘zbek adabiy tilining asoschisi hisoblanadi. «Xamsa» asarini yozgan.»",
  [("Navoiy qachon tug‘ilgan?", "1441-yilda", ["1500-yilda", "1300-yilda", "1900-yilda"]), ("Navoiy yozgan asar?", "Xamsa", ["Boburnoma", "Qutadg‘u bilig", "Mirzo Ulug‘bek zij"])]),
 ("«Buxoro arki IV asrda qurila boshlangan. Hozir u yerda muzey bor. Arkka kirish chiptasi kattalar uchun 30 000 so‘m, bolalar uchun 10 000 so‘m.»",
  [("Bolalar chiptasi qancha?", "10 000 so‘m", ["30 000 so‘m", "5 000 so‘m", "Bepul"]), ("Arkda hozir nima bor?", "Muzey", ["Maktab", "Bozor", "Stadion"])]),
],
"PR-TUS": [
 ("«Ba’zi shaharlarda tungi yoritish kamaytirilganda, yulduzlar yaxshiroq ko‘rina boshladi va qushlar ko‘proq tinchlik topdi, biroq jinoyatchilik haqida bahslar davom etmoqda.»",
  [("Matndan qanday xulosa chiqadi?", "Tungi yoritishni kamaytirishning ham foydasi, ham bahsli tomoni bor", ["Yoritish zarar", "Yulduz yo‘qoladi", "Hamma rozi"]), ("«Biroq» so‘zi nimani bildiradi?", "Qarama-qarshilik", ["Sabab", "Vaqt", "Misol"])]),
 ("«Ahmad darsga kech qoldi, chunki avtobus buzilib qoldi. Shu sababli u birinchi darsni o‘tkazib yubordi.»",
  [("Ahmad nima uchun kech qoldi?", "Avtobus buzilgan", ["Uxlab qolgan", "Kasal bo‘lgan", "Dars bekor"]), ("Natija nima bo‘ldi?", "Birinchi darsni o‘tkazib yubordi", ["Mukofot oldi", "Uyga ketdi", "Do‘st orttirdi"])]),
 ("«Qishloq xo‘jaligida tomchilatib sug‘orish suvni 40 foizgacha tejaydi. Biroq uni o‘rnatish dastlab qimmat turadi.»",
  [("Tomchilatib sug‘orish nimasi bilan yaxshi?", "Suvni tejaydi", ["Arzon", "Tezkor", "Ovozsiz"]), ("Qanday kamchilik bor?", "Dastlabki xarajat yuqori", ["Suvni isrof qiladi", "Hosilni kamaytiradi", "Juda sekin"])]),
 ("«Sinfdosh Zilola doim kitob o‘qiydi. Uning lug‘ati boy, insholari ravon va ko‘p mukofot oladi.»",
  [("Zilola nega yaxshi yozadi (matnga ko‘ra)?", "Ko‘p kitob o‘qiydi", ["Tez yuguradi", "Rasm chizadi", "Kam uxlaydi"]), ("Matn qaysi fikrni qo‘llab-quvvatlaydi?", "Kitob o‘qish yozuv qobiliyatini oshiradi", ["Kitob o‘qish zarar", "Mukofot kerak emas", "Insho oson"])]),
 ("«Tadqiqot shuni ko‘rsatdiki, uyqusiz o‘quvchilar testda o‘rtacha 15 foiz past ball olgan.»",
  [("Uyqusizlik natijaga qanday ta’sir qilgan?", "Ballni pasaytirgan", ["Oshirgan", "Ta’sir qilmagan", "Noma’lum"]), ("15 foiz nimani bildiradi?", "Ballning pasayish ulushi", ["O‘quvchilar soni", "Test vaqti", "Savollar soni"])]),
 ("«Kuz fasli kelganda daraxt barglari sarg‘ayadi, chunki xlorofill parchalanadi va boshqa pigmentlar ko‘rinib qoladi.»",
  [("Barglar nega sarg‘ayadi?", "Xlorofill parchalanadi", ["Suv ko‘payadi", "Yorug‘ ko‘p", "Shamol urgani uchun"]), ("Sarg‘ayish nimaga bog‘liq?", "Pigmentlar ko‘rinishiga", ["Ildiz uzunligiga", "Oy fazasiga", "Qor yog‘ishiga"])]),
 ("«Fermer bahorda urug‘ ekdi, yozda sug‘ordi, kuzda hosil yig‘di.»",
  [("Fermer hosilni qachon yig‘di?", "Kuzda", ["Bahorda", "Yozda", "Qishda"]), ("Ishlarning to‘g‘ri tartibi?", "Ekish → sug‘orish → yig‘ish", ["Yig‘ish → ekish → sug‘orish", "Sug‘orish → yig‘ish → ekish", "Ekish → yig‘ish → sug‘orish"])]),
 ("«Maktab bog‘iga 20 ta olma va 30 ta o‘rik ko‘chati ekildi. Ularning yarmi birinchi yilda ko‘kardi.»",
  [("Nechta ko‘chat ekildi?", "50 ta", ["20 ta", "30 ta", "25 ta"]), ("Birinchi yilda nechta ko‘chat ko‘kardi?", "25 ta", ["50 ta", "10 ta", "20 ta"])]),
],
"PR-BAH": [
 ("«Maqola: «Barcha o‘smirlar kun bo‘yi telefonda o‘tiradi» deb yozilgan, lekin hech qanday so‘rovnoma keltirilmagan.»",
  [("Bu da’voning kamchiligi nima?", "Dalil ko‘rsatilmagan va umumlashtirilgan", ["Juda qisqa", "Sarlavha yo‘q", "Rasm yo‘q"]), ("Yaxshilash uchun nima qilish kerak?", "So‘rovnoma natijasini keltirish", ["Ko‘proq ta’kidlash", "Qichqirish", "Hech narsa"])]),
 ("«Do‘stim aytdi: bu dori hamma kasallikni davolaydi. Men esa shifokordan so‘radim va u bunday dori yo‘qligini aytdi.»",
  [("Qaysi manba ishonchliroq?", "Shifokor", ["Do‘stim", "Reklama", "Tasodifiy kishi"]), ("Nega?", "Mutaxassis va dalilga tayanadi", ["U baland ovozda", "U do‘st", "U boy"])]),
 ("«Matn muallifi: Shaharda daraxt ekish kerak. Chunki daraxtlar havoni tozalaydi, soya beradi va shovqinni kamaytiradi.»",
  [("Muallifning pozitsiyasi?", "Shaharda daraxt ekish kerak", ["Daraxtlarni kesish kerak", "Shahar kerak emas", "Soya zararli"]), ("Dalillar nechta?", "Uchta", ["Bitta", "Ikkita", "To‘rtta"])]),
 ("«Reklama: «Eng yaxshi telefon! Sinab ko‘rmaganlar afsuslanadi!» — Bu fakt emas, bu...»",
  [("Bu gap nima?", "Reklama bahosi (fikr)", ["Isbotlangan fakt", "Statistika", "Qonun"]), ("Narx haqida ma’lumot bormi?", "Yo‘q", ["Ha", "Bor, 1 mln", "Bor, bepul"])]),
 ("«Birinchi maqola bir tadqiqotga tayanadi, ikkinchisi esa uch alohida tadqiqotga. Natijalar bir xil.»",
  [("Qaysi xulosa ishonchliroq?", "Ikkinchisi", ["Birinchisi", "Ikkalasi teng", "Hech biri"]), ("Nega?", "Ko‘p mustaqil dalil bor", ["Uzunroq", "Rasmli", "Yangi"])]),
 ("«Sarlavha: «Hayratlanarli! Bu usul bilan 1 haftada 10 kg ozasiz!» — Maqolada hech qanday shifokor tavsiyasi yo‘q.»",
  [("Sarlavha qanday xarakterga ega?", "Haddan tashqari va’da, e’tibor jalb qiluvchi", ["Ilmiy", "Neytral", "Rasmiy"]), ("Nima qilish kerak?", "Shifokorga murojaat qilib tekshirish", ["Darhol sinash", "Hammaga tarqatish", "Pul to‘lash"])]),
 ("«Fikr: «Bu film juda zerikarli edi.» Fakt: «Film 2 soat 10 daqiqa davom etdi.»»",
  [("Qaysi gap fakt?", "Film 2 soat 10 daqiqa davom etdi", ["Film juda zerikarli edi", "Ikkalasi", "Hech biri"]), ("Qaysi gap fikr?", "Film juda zerikarli edi", ["Film 2 soat 10 daqiqa", "Ikkalasi ham", "Hech qaysisi"])]),
],
}

def _matn_qosh(kod):
    L = _YANGI[kod]; _matnlar[kod].extend(L)
    base = len(_matnlar[kod]) - len(L)
    for ti, (matn, qs) in enumerate(L):
        for qi, (sv, tj, no) in enumerate(qs):
            def f(rng, matn=matn, sv=sv, tj=tj, no=no):
                return _yopiq(rng, f"{matn}\n\n{sv}", tj, ["Javob matnda to‘g‘ridan-to‘g‘ri yoki mantiqiy xulosa orqali topiladi."], noto=list(no), tartib=False)
            f.__name__ = f"{kod}_n{base + ti}_{qi}"
            reg(kod, "yopiq")(f)
for _k in _YANGI:
    _matn_qosh(_k)

# PISA uslubidagi hayotiy ochiq savollar
@reg("PS-TAJ", "ochiq")
def ps_tajriba_sinfi(rng):
    a = rng.choice([4, 5, 6]); b = rng.choice([10, 12, 15])
    return _o(f"Maktab tajribasida {a} ta stakanga har xil miqdorda suv quyildi va unga o‘simlik ekildi. Har bir stakan uchun {b} dona urug‘ ishlatildi.", [("a) Jami nechta urug‘ ishlatildi?", a * b), ("b) Agar 60% urug‘ unib chiqsa, necha dona unib chiqadi? (butun son bo‘lmasa o‘nli)", Fraction(a * b * 60, 100))], [f"a) {a}·{b} = {a * b}.", f"b) {a * b}·60/100 = {num(Fraction(a * b * 60, 100))}."])

@reg("PS-MAL", "ochiq")
def ps_mal_trend(rng):
    y = rng.choice([100, 200, 400]); p = rng.choice([10, 20, 25])
    return _o(f"Kasallik holatlari 2023-yilda {y} ta edi, 2024-yilda {p}% ga oshdi.", [("a) 2024-yilda nechta holat bo‘ldi?", y * (100 + p) // 100), ("b) Ortiqcha holatlar soni?", y * p // 100)], [f"a) {y}·{100 + p}/100 = {y * (100 + p) // 100}.", f"b) {y}·{p}/100 = {y * p // 100}."])

@reg("PS-TUS", "ochiq")
def ps_tus_quvvat(rng):
    w = rng.choice([60, 100, 200]); h = rng.choice([2, 3, 5])
    return _o(f"{w} Vt quvvatli qurilma kuniga {h} soat ishlaydi.", [("a) Kunlik energiya (Vt·soat)?", w * h), ("b) 10 kunda necha kVt·soat?", Fraction(w * h * 10, 1000))], [f"a) {w}·{h} = {w * h}.", f"b) {w * h}·10/1000 = {num(Fraction(w * h * 10, 1000))}."])

def _qadam_pr(nom, a, b):
    return [(f"{nom}: strategiya", a, b)]

_PRD = {
 "PR-TOP": [("Savoldan boshlaymiz", "1. Savolni o‘qi\n2. Kalit so‘zni belgila\n3. Matnda qidir", "Avval savolni o‘qib, kalit so‘zni belgilaymiz."),
   ("Raqam va sanalar", "Sana, narx, soat — aniq javob\nO‘lchov birligiga e’tibor", "Raqamli savollarda birlik va yil muhim."),
   ("Jadval va e’lon", "Qator + ustun kesishgan joy\nHaftaning kuni, vaqt", "Jadvalda qator va ustunning kesishmasini topamiz."),
   ("Chalg‘ituvchi javoblar", "Matnda bor, lekin savolga javob emas", "Ba’zi javoblar matnda bor, lekin savolga mos kelmaydi."),
   ("Tekshirish", "Javob matnda aynan shunday yozilganmi?", "Javobni matn bilan solishtirib tekshiramiz.")],
 "PR-TUS": [("Asosiy g‘oya", "Matn nima haqida?\nBir jumlada ayt", "Asosiy g‘oya matnning butun mazmunini bir jumlada beradi."),
   ("Sabab va oqibat", "chunki, shu sababli, natijada", "Bog‘lovchi so‘zlar sabab va oqibatni ko‘rsatadi."),
   ("Xulosa chiqarish", "Matnda ochiq yozilmagan, lekin undan kelib chiqadi", "Xulosa matndagi dalillardan mantiqan kelib chiqadi."),
   ("Tartib", "Avval → keyin → oxirida", "Voqealar tartibini sanalar va so‘zlar bilan aniqlaymiz."),
   ("Xato qilmaymiz", "❌ O‘zimning fikrim\n✅ Matndagi dalil", "Javob matnga tayanishi kerak.")],
 "PR-BAH": [("Fakt va fikr", "Fakt — tekshiriladi\nFikr — baho", "Faktni tekshirib bo‘ladi, fikr esa muallifning bahosi."),
   ("Muallif maqsadi", "Xabar berish / ishontirish / sotish", "Muallif nima maqsadda yozganini aniqlaymiz."),
   ("Manba ishonchliligi", "Muallif, sana, dalil", "Ishonchli manbada dalil va muallif bo‘ladi."),
   ("Dalillarni solishtirish", "Ko‘p mustaqil dalil → kuchli", "Bir nechta mustaqil dalil bitta dalildan kuchli."),
   ("Shubhali belgilar", "Haddan tashqari va’da\nDalilsiz umumlashtirish", "«Hammasi», «doim», «shok» kabi so‘zlar shubha tug‘diradi.")],
}

TEMA = {}
for _k, _v in _PS.items():
    TEMA[_k] = _pm(_k, _v)
for _k, _v in _PRD.items():
    t = dict(_T0[_k]); t["dars"] = [_d(a, b, c) for a, b, c in _v]; TEMA[_k] = t
