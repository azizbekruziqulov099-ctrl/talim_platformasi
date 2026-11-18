"""TIMSS 8-sinf fan: 18 mavzu (S8-*)."""
from fractions import Fraction

from modules.pisa_mat_g import reg, num, _y, _o, _yopiq, fig_stolbik
from modules.xb_ps import _fakt, _d

TOP = "T11_G8_S"

def _tema(kod, nom, belgi, maqsad, dars):
    return {"nom": nom, "soha": "Fan", "belgi": belgi, "maqsad": maqsad, "bolim": kod, "toplam": TOP, "dars": dars}

def _b(sv, tj, no, iz=""):
    return (sv, tj, no, iz or f"To‘g‘ri javob: {tj}.")

_F = {
"S8-ORG": [
 _b("Qaysi guruh umurtqali hayvonlarga kiradi?", "Amfibiyalar", ["Hasharotlar", "Mollyuskalar", "Chuvalchanglar"], "Amfibiyalarda umurtqa pog‘onasi bor."),
 _b("Qushlarning umumiy belgisi?", "Tana patlar bilan qoplangan", ["Mo‘ynali", "Tangachali", "Silliq teri"], "Patlar faqat qushlarda."),
 _b("Qaysi hayvon sutemizuvchi?", "Delfin", ["Akula", "Yoyli baliq", "Timsoh"], "Delfin o‘pka bilan nafas oladi va sut bilan boqadi."),
 _b("Tiriklikning belgisi qaysi?", "Ta’sirlanuvchanlik", ["Rangi", "Qattiqligi", "Og‘irligi"], "Tirik organizm muhit ta’siriga javob beradi."),
 _b("Nafas olish jarayonida nima hosil bo‘ladi?", "Energiya", ["Faqat kislorod", "Tosh", "Metall"], "Hujayralarda glyukoza oksidlanib energiya beradi."),
 _b("Sudralib yuruvchilar tanasi nima bilan qoplangan?", "Tangachalar", ["Patlar", "Mo‘yna", "Shilimshiq"], "Quruqlikka moslashgan."),
 _b("Qaysi organizm hasharot?", "Chumoli", ["O‘rgimchak", "Chayon", "Ko‘p oyoqli"], "Hasharotning 6 ta oyog‘i bor."),
 _b("Ovqat hazm qilishning asosiy maqsadi?", "Oziq moddalarni so‘riladigan holga keltirish", ["Suvni chiqarish", "Havoni isitish", "Mushakni sovitish"], "Murakkab moddalar oddiylarga parchalanadi."),
 _b("Qonni tanada nima aylantiradi?", "Yurak", ["O‘pka", "Jigar", "Buyrak"], "Yurak nasos vazifasini bajaradi."),
],
"S8-HUJ": [
 _b("Hujayraning irsiy ma’lumot saqlovchi qismi?", "Yadro", ["Sitoplazma", "Hujayra devori", "Vakuola"], "DNK yadroda."),
 _b("Qaysi organoid fotosintezni amalga oshiradi?", "Xloroplast", ["Mitoxondriya", "Yadro", "Ribosoma"], "Xloroplastda xlorofill bor."),
 _b("Mitoxondriyaning vazifasi?", "Hujayraviy nafas orqali energiya hosil qilish", ["Fotosintez", "Irsiyat", "Himoya"], "Hujayraning «energiya stansiyasi»."),
 _b("Faqat o‘simlik hujayrasida bor qism?", "Hujayra devori", ["Yadro", "Membrana", "Sitoplazma"], "Hayvon hujayrasida devor yo‘q."),
 _b("Hujayra membranasi nima qiladi?", "Moddalar o‘tishini boshqaradi", ["Energiya ishlab chiqaradi", "Irsiyat saqlaydi", "Xlorofill hosil qiladi"], "Tanlab o‘tkazadi."),
 _b("Fotosintez natijasida nima hosil bo‘ladi?", "Glyukoza va kislorod", ["CO₂ va suv", "Azot", "Faqat suv"], "Fotosintez: CO₂ + H₂O → glyukoza + O₂."),
 _b("Bir hujayrali organizmga misol?", "Amyoba", ["Baliq", "Sichqon", "Archa"], "Amyoba bitta hujayradan iborat."),
 _b("Mikroskopda hujayrani kattalashtirish qanday hisoblanadi?", "Okulyar × ob’ektiv", ["Okulyar + ob’ektiv", "Faqat ob’ektiv", "Okulyar − ob’ektiv"], "Umumiy kattalashtirish ko‘paytma."),
],
"S8-KOP": [
 _b("Jinssiz ko‘payishda nasl qanday bo‘ladi?", "Ota-onaga genetik bir xil", ["Har xil", "Aralash", "Sterilligi"], "Bitta ota-onadan klon hosil bo‘ladi."),
 _b("Gen nima?", "Irsiy belgini belgilovchi DNK qismi", ["Oqsil turi", "Hujayra devori", "Gormon"], "Gen belgi haqida ma’lumot saqlaydi."),
 _b("Qaysi belgi orttirilgan?", "Mashq qilgan odam mushagi", ["Ko‘z rangi", "Qon guruhi", "Soch turi"], "Orttirilgan belgi irsiylanmaydi."),
 _b("Jinsiy ko‘payishda nima qo‘shiladi?", "Ikki jinsiy hujayra", ["Ikki mushak", "Ikki suyak", "Ikki qon"], "Urug‘lanish."),
 _b("DNK nima?", "Irsiy ma’lumot tashuvchi molekula", ["Vitamin", "Oqsil turi", "Yog‘"], "DNK genlarni saqlaydi."),
 _b("Bakteriyalar qanday ko‘payadi?", "Ikkiga bo‘linib", ["Urug‘ bilan", "Tuxum bilan", "Kurtak bilan faqat"], "Bo‘linish — jinssiz ko‘payish."),
 _b("Urug‘lanish natijasida nima hosil bo‘ladi?", "Zigota", ["Gamet", "Spora", "Kurtak"], "Zigota — urug‘langan hujayra."),
 _b("Irsiy belgiga misol?", "Ko‘z rangi", ["Sportchi mushaklari", "Yara izi", "Til bilish"], "Ota-onadan beriladi."),
],
"S8-MOS": [
 _b("Tabiiy tanlanishda nima omad qozonadi?", "Muhitga yaxshi moslashganlar", ["Eng kattalar", "Eng qimmatlar", "Hammasi"], "Moslashganlar ko‘proq tirik qoladi."),
 _b("Tur ichidagi farqlar nima deyiladi?", "O‘zgaruvchanlik", ["Tasnif", "Qazilma", "Mutatsiya faqat"], "Individlar bir-biridan farq qiladi."),
 _b("Jirafaning uzun bo‘yni nima uchun?", "Baland daraxt bargiga yetish", ["Suzish", "Uchish", "Yashirinish"], "Moslashish belgisi."),
 _b("Evolyutsiya dalili qaysi?", "Qazilma qoldiqlar", ["Bulutlar", "Ob-havo", "Shamol"], "Fossil o‘zgarishni ko‘rsatadi."),
 _b("Antibiotikka chidamli bakteriyalar qanday ko‘payadi?", "Chidamlilari tirik qoladi va ko‘payadi", ["Hammasi o‘ladi", "Dori ularni o‘zgartiradi", "Hech qachon"], "Tabiiy tanlanish."),
 _b("Mutatsiya nima?", "Genetik materialdagi o‘zgarish", ["Ovqatlanish", "Uyqu", "Harakat"], "Yangi belgi paydo bo‘lishi mumkin."),
 _b("Qutb tulkisi oq rangda — nima uchun?", "Qorda yashirinish", ["Issiqda salqinlash", "Yorug‘ ko‘rinish", "Uchish"], "Maskirovka."),
],
"S8-EKO": [
 _b("Energiya oziq zanjirida har bosqichda taxminan qancha o‘tadi?", "10%", ["100%", "50%", "90%"], "Qolgan qismi issiqlik sifatida yo‘qoladi."),
 _b("Produtsent nima?", "Fotosintez qiluvchi organizm", ["Yirtqich", "Parchalovchi", "O‘txo‘r"], "O‘simlik produtsent."),
 _b("Raqobat nima?", "Bir resurs uchun kurash", ["Hamkorlik", "Ko‘payish", "Uyqu"], "Tur ichida yoki turlar orasida."),
 _b("Yirtqich kamaysa, o‘lja soni...", "Avval ko‘payadi", ["Kamayadi", "Yo‘qoladi", "O‘zgarmaydi"], "Bosim kamayadi."),
 _b("Biotik omil qaysi?", "Yirtqich", ["Harorat", "Yorug‘lik", "Namlik"], "Tirik omillar biotik."),
 _b("Abiotik omil qaysi?", "Harorat", ["Raqobat", "Yirtqich", "Parazit"], "Jonsiz tabiat omili."),
 _b("Parchalovchilar nima qiladi?", "Organik moddalarni mineralga aylantiradi", ["Quyoshdan energiya oladi", "Yirtqichni yeydi", "Urug‘ tarqatadi"], "Moddalar aylanishi."),
 _b("Piramida cho‘qqisida odatda kim turadi?", "Oliy yirtqichlar", ["O‘simliklar", "Bakteriya", "O‘txo‘rlar"], "Soni eng kam."),
],
"S8-SOG": [
 _b("Qaysi kasallik yuqumli?", "Gripp", ["Diabet", "Yurak qon tomir kasalligi", "Allergiya faqat"], "Gripp virus orqali yuqadi."),
 _b("Emlash immunitetni qanday kuchaytiradi?", "Antitanalar hosil qilishni o‘rgatadi", ["Mikrobni ko‘paytiradi", "Qonni to‘kadi", "Tanani isitadi"], "Zaiflashtirilgan antigen."),
 _b("Qonning kislorod tashuvchi hujayrasi?", "Eritrotsit", ["Leykotsit", "Trombotsit", "Plazma"], "Gemoglobin kislorodni olib yuradi."),
 _b("Leykotsitlar vazifasi?", "Infeksiyadan himoya", ["Kislorod tashish", "Qon ivish", "Ovqat hazm"], "Oq qon tanachalari."),
 _b("Trombotsitlar vazifasi?", "Qon ivishi", ["Kislorod tashish", "Himoya", "Energiya"], "Yarani berkitadi."),
 _b("Qaysi kasallik yuqumsiz?", "Qandli diabet", ["Sil", "Gripp", "Suvchechak"], "Mikrobdan yuqmaydi."),
 _b("Antibiotik qaysi kasallikka ta’sir qiladi?", "Bakterial", ["Virusli", "Allergik", "Genetik"], "Antibiotiklar virusga ta’sir qilmaydi."),
 _b("Chekish qaysi a’zoga eng ko‘p zarar?", "O‘pka", ["Teri", "Soch", "Tirnoq"], "Nafas yo‘llariga zarar."),
],
"S8-TAR": [
 _b("Element nima?", "Bir xil atomlardan iborat toza modda", ["Aralashma", "Eritma", "Birikma"], "Masalan, temir, kislorod."),
 _b("H₂O qanday modda?", "Birikma", ["Element", "Aralashma", "Eritma"], "Vodorod va kislorod kimyoviy bog‘langan."),
 _b("Havo qanday?", "Aralashma", ["Birikma", "Element", "Atom"], "Azot, kislorod va boshqalar aralashmasi."),
 _b("Atom markazida nima bor?", "Yadro", ["Elektron", "Molekula", "Ion"], "Yadro proton va neytrondan iborat."),
 _b("CO₂ molekulasida nechta atom bor?", "3", ["2", "4", "1"], "1 ta C va 2 ta O."),
 _b("Tuz suvi qanday ajratiladi?", "Bug‘latish bilan", ["Filtrlash bilan", "Magnit bilan", "Cho‘ktirish bilan"], "Suv bug‘lanadi, tuz qoladi."),
 _b("Qaysi formula kislorodniki?", "O₂", ["O₃ emas", "CO₂", "H₂O"], "Kislorod ikki atomli molekula."),
 _b("Aralashmaning birikmadan farqi?", "Komponentlar kimyoviy bog‘lanmagan", ["Doim bir xil formula", "Yangi modda hosil bo‘ladi", "Ajratib bo‘lmaydi"], "Aralashma fizik usulda ajratiladi."),
],
"S8-XOS": [
 _b("pH = 3 bo‘lsa eritma qanday?", "Kislotali", ["Neytral", "Ishqoriy", "Tuz"], "pH < 7 kislotali."),
 _b("pH = 7 qanday eritma?", "Neytral", ["Kislotali", "Ishqoriy", "Zaharli"], "Toza suv neytral."),
 _b("Qaysi biri fizik xossa?", "Erish harorati", ["Yonuvchanlik", "Zanglash", "Kislota bilan reaksiya"], "Moddani o‘zgartirmaydi."),
 _b("Qaysi biri kimyoviy xossa?", "Yonuvchanlik", ["Rangi", "Zichligi", "Qaynash harorati"], "Yangi modda hosil qiladi."),
 _b("Ishqorning pH qiymati?", "7 dan katta", ["7 dan kichik", "Aynan 7", "0"], "Ishqor pH > 7."),
 _b("Eruvchanlik harorat oshganda (qattiq moddalar uchun) odatda...", "Oshadi", ["Kamayadi", "O‘zgarmaydi", "Nolga teng"], "Isitilsa ko‘proq eriydi."),
 _b("Limon sharbati qanday?", "Kislotali", ["Ishqoriy", "Neytral", "Metall"], "Limon kislotasi bor."),
],
"S8-REA": [
 _b("Qaysi biri kimyoviy hodisa?", "Yog‘ochning yonishi", ["Muzning erishi", "Suvning qaynashi", "Shakarning erishi"], "Yangi moddalar hosil bo‘ladi."),
 _b("Reaksiya belgisi qaysi?", "Gaz ajralishi", ["Rang o‘zgarmasligi", "Shakl o‘zgarishi faqat", "Hajm kichrayishi"], "Gaz, cho‘kma, rang, issiqlik."),
 _b("Massaning saqlanish qonuni nima deydi?", "Reaksiyadan oldingi va keyingi massa teng", ["Massa ko‘payadi", "Massa kamayadi", "Massa nolga teng"], "Atomlar yo‘qolmaydi."),
 _b("Zanglash qanday jarayon?", "Kimyoviy", ["Fizik", "Biologik faqat", "Mexanik"], "Temir oksidlanadi."),
 _b("Qaysi biri fizik hodisa?", "Suvning qaynashi", ["Zanglash", "Yonish", "Chirish"], "Modda o‘zgarmaydi, holat o‘zgaradi."),
 _b("Reaktivlar nima?", "Reaksiyaga kirishuvchi moddalar", ["Hosil bo‘lgan moddalar", "Katalizator faqat", "Idish"], "Reaksiyaning boshlang‘ich moddalari."),
 _b("Sirka va soda aralashtirilganda ko‘pik hosil bo‘ladi. Bu nimani bildiradi?", "Gaz ajraldi (kimyoviy reaksiya)", ["Faqat erish", "Muzlash", "Hech narsa"], "CO₂ ajraladi."),
],
"S8-HOL": [
 _b("Qattiq jismda zarrachalar qanday?", "Tartibli va zich, tebranadi", ["Erkin harakatlanadi", "Uzoq", "Yo‘q"], "Joyida tebranadi."),
 _b("Gazda zarrachalar qanday?", "Bir-biridan uzoq va tez harakatlanadi", ["Zich", "Tartibli", "Qimirlamaydi"], "Gaz idish hajmini to‘ldiradi."),
 _b("Suyuqlik gazga aylanishi nima deyiladi?", "Bug‘lanish", ["Qotish", "Erish", "Sublimatsiya"], "Suyuq → gaz."),
 _b("Qattiq → suyuq?", "Erish", ["Qotish", "Kondensatsiya", "Bug‘lanish"], "Isitilganda."),
 _b("Gaz → suyuq?", "Kondensatsiya", ["Erish", "Qotish", "Bug‘lanish"], "Sovitilganda."),
 _b("Suv 1 atm bosimda necha °C da muzlaydi?", "0 °C", ["100 °C", "−50 °C", "37 °C"], "Muzlash harorati."),
 _b("Suv necha °C da qaynaydi (dengiz sathida)?", "100 °C", ["0 °C", "50 °C", "212 °C"], "Qaynash harorati."),
],
"S8-ISS": [
 _b("Harorat zarrachalarning nimasini ko‘rsatadi?", "O‘rtacha kinetik energiyasini", ["Massasini", "Rangini", "Hajmini"], "Harorat yuqori bo‘lsa zarrachalar tez harakatlanadi."),
 _b("Issiqlik qanday uzatiladi?", "Issiqdan sovuqqa", ["Sovuqdan issiqqa", "Hech qayoqqa", "Tasodifiy"], "Issiqlik oqimi."),
 _b("Konveksiya qayerda?", "Suyuqlik va gazlarda", ["Qattiq jismlarda faqat", "Vakuumda", "Hech qayerda"], "Oqim orqali uzatiladi."),
 _b("Quyoshdan issiqlik Yerga qanday keladi?", "Nurlanish orqali", ["O‘tkazuvchanlik", "Konveksiya", "Ishqalanish"], "Vakuumda ham tarqaladi."),
 _b("Qaysi energiya turi harakatdagi jismda?", "Kinetik", ["Potensial", "Kimyoviy", "Yadro"], "Harakat energiyasi."),
 _b("Tepada turgan jism qanday energiyaga ega?", "Potensial", ["Kinetik", "Elektr", "Yorug‘lik"], "Balandlik tufayli."),
 _b("Energiya saqlanish qonuni?", "Energiya yo‘qolmaydi, shaklini o‘zgartiradi", ["Energiya yo‘qoladi", "Energiya paydo bo‘ladi", "Energiya tugaydi"], "Aylanadi."),
],
"S8-YOR": [
 _b("Yorug‘lik qanday tarqaladi?", "To‘g‘ri chiziq bo‘ylab", ["Egri", "Zigzag", "Doira"], "Bir jinsli muhitda."),
 _b("Qaytish qonuni?", "Tushish burchagi = qaytish burchagi", ["Tushish > qaytish", "Tushish < qaytish", "Bog‘liq emas"], "Oynada."),
 _b("Tovush nima?", "Tebranish", ["Yorug‘lik", "Issiqlik", "Elektr"], "Tebranish to‘lqini."),
 _b("Tovush vakuumda?", "Tarqalmaydi", ["Tarqaladi", "Tezlashadi", "Kuchayadi"], "Muhit kerak."),
 _b("Tovush qaysi muhitda eng tez?", "Qattiq jismda", ["Havoda", "Vakuumda", "Suvda sekinroq"], "Zarrachalar zich."),
 _b("Yorug‘lik havodan suvga o‘tganda...", "Sinadi", ["Yo‘qoladi", "Qaytmaydi", "Tezlashadi"], "Sinish hodisasi."),
 _b("Chastota oshsa tovush...", "Ingichkalashadi", ["Yo‘g‘onlashadi", "Yo‘qoladi", "Kuchsizlanadi"], "Balandlik chastotaga bog‘liq."),
],
"S8-ELE": [
 _b("Om qonuni?", "I = U / R", ["I = U · R", "R = U · I", "U = I / R"], "Tok kuchi kuchlanishga to‘g‘ri, qarshilikka teskari."),
 _b("Ketma-ket ulashda lampalardan biri yonib ketsa?", "Hammasi o‘chadi", ["Qolganlari yonadi", "Yorug‘roq", "Hech narsa"], "Zanjir uziladi."),
 _b("Parallel ulashda lampa o‘chsa?", "Qolganlari yonadi", ["Hammasi o‘chadi", "Hammasi portlaydi", "Zanjir yo‘q"], "Alohida shoxlar."),
 _b("Magnit qutblari?", "Shimol va janub", ["Faqat shimol", "Qizil va ko‘k", "Yo‘q"], "Bir xil qutblar itariladi."),
 _b("Bir xil magnit qutblar...", "Itarishadi", ["Tortishadi", "Ta’sir qilmaydi", "Yo‘qoladi"], "Qarama-qarshilari tortishadi."),
 _b("Tok kuchi birligi?", "Amper", ["Volt", "Om", "Vatt"], "A."),
 _b("Kuchlanish birligi?", "Volt", ["Amper", "Om", "Nyuton"], "V."),
],
"S8-KUC": [
 _b("Kuchlar muvozanatda bo‘lsa jism...", "Tinch holatda yoki tekis harakatda", ["Tezlashadi", "Aylanadi", "Yo‘qoladi"], "Teng ta’sir etuvchi nol."),
 _b("Bosim formulasi?", "p = F / S", ["p = F · S", "p = S / F", "p = m / V"], "Kuch yuzaga bo‘linadi."),
 _b("Atmosfera bosimi balandlik oshganda...", "Kamayadi", ["Oshadi", "O‘zgarmaydi", "Nolga teng"], "Havo siyraklashadi."),
 _b("Zichlik formulasi?", "ρ = m / V", ["ρ = m · V", "ρ = V / m", "ρ = F / S"], "Massa hajmga bo‘linadi."),
 _b("Jism suvda suzishi uchun nima kerak?", "Zichligi suvnikidan kichik", ["Zichligi katta", "Massasi katta", "Rangi och"], "Arximed kuchi."),
 _b("Tezlik formulasi?", "v = s / t", ["v = s · t", "v = t / s", "v = F / m"], "Yo‘l vaqtga bo‘linadi."),
 _b("Yer bilan ta’sir kuchi qanday nomlanadi?", "Og‘irlik kuchi", ["Ishqalanish", "Elastiklik", "Magnit"], "Yer tortadi."),
],
"S8-YER": [
 _b("Yerning eng ichki qatlami?", "Yadro", ["Mantiya", "Po‘st", "Atmosfera"], "Markazda."),
 _b("Topografik xaritada gorizontallar zich bo‘lsa...", "Yon bag‘ir tik", ["Yon bag‘ir tekis", "Suv bor", "Tog‘ yo‘q"], "Zichlik tiklikni bildiradi."),
 _b("Daryo oqimi qayoqqa?", "Pastga qarab", ["Tepaga", "Tog‘ga", "Bir joyda"], "Gorizontal balandlikka qarab."),
 _b("Yer po‘sti qaysi?", "Eng yupqa qatlam", ["Eng qalin", "Suyuq", "Yo‘q"], "Taxminan 5–70 km."),
 _b("Atmosfera qatlami (pastki)?", "Troposfera", ["Stratosfera", "Ekzosfera", "Mezosfera"], "Ob-havo shu yerda."),
 _b("Mantiya holati?", "Qovushqoq (yarim erigan)", ["Qattiq tosh", "Gaz", "Suv"], "Issiq qovushqoq."),
],
"S8-JAR": [
 _b("Zilzila nima sababdan?", "Litosfera plitalari harakati", ["Shamol", "Oy tortishi", "Yomg‘ir"], "Plitalar to‘qnashadi."),
 _b("Vulqon nima?", "Magma chiqadigan joy", ["Daryo", "Ko‘l", "Tog‘ faqat"], "Magma lavaga aylanadi."),
 _b("Materiklar siljishining dalili?", "Qirg‘oq chiziqlarining mosligi", ["Bulutlar", "Daryolar", "Shamollar"], "Afrika va Janubiy Amerika."),
 _b("Suv aylanishida bug‘lanishni nima ta’minlaydi?", "Quyosh energiyasi", ["Oy", "Shamol faqat", "Tog‘lar"], "Issiqlik."),
 _b("Plitalar bir-biridan uzoqlashsa?", "Yangi qobiq hosil bo‘ladi", ["Tog‘ ko‘tariladi faqat", "Hech narsa", "Zilzila yo‘q"], "Okean tubida."),
 _b("Fossillar qaysi jinslarda ko‘proq?", "Cho‘kindi", ["Magmatik", "Metamorfik", "Hammasida bir xil"], "Cho‘kma qatlamlar."),
],
"S8-RES": [
 _b("Tiklanmaydigan resurs?", "Neft", ["Quyosh", "Shamol", "Suv aylanishi"], "Millionlab yilda hosil bo‘ladi."),
 _b("Tiklanadigan resurs?", "Shamol energiyasi", ["Ko‘mir", "Neft", "Gaz"], "Tugamaydi."),
 _b("Eroziya nima?", "Tuproqning yuvilishi yoki shamol bilan uchishi", ["Tuproq hosil bo‘lishi", "O‘g‘itlash", "Sug‘orish"], "Daraxt ekish kamaytiradi."),
 _b("Eroziyaga qarshi chora?", "Daraxt va o‘t ekish", ["Daraxt kesish", "Haydash", "Yoqish"], "Ildizlar ushlab turadi."),
 _b("Chiqindini qayta ishlash...", "Resursni tejaydi", ["Ko‘paytiradi", "Havoni ifloslaydi", "Foydasiz"], "Resurs tejaladi."),
 _b("Issiqxona effektini nima kuchaytiradi?", "CO₂ ko‘payishi", ["O‘rmon ko‘payishi", "Yomg‘ir", "Oy"], "Yoqilg‘i yonishi."),
],
"S8-KOI": [
 _b("Quyosh tizimida eng katta sayyora?", "Yupiter", ["Yer", "Mars", "Venera"], "Gaz gigant."),
 _b("Oy fazalari nimaga bog‘liq?", "Oy, Yer va Quyosh joylashuviga", ["Bulutlarga", "Shamolga", "Yer soyasi faqat"], "Yoritilgan qismning ko‘rinishi."),
 _b("Quyosh tutilishida...", "Oy Quyoshni to‘sadi", ["Yer Oyni to‘sadi", "Quyosh o‘chadi", "Venera o‘tadi"], "Oy Yer va Quyosh orasida."),
 _b("Yulduz va sayyora farqi?", "Yulduz o‘zi yorug‘lik chiqaradi", ["Sayyora o‘zi yonadi", "Farqi yo‘q", "Sayyora kattaroq"], "Yulduzda termoyadro reaksiyasi."),
 _b("Yerning Quyosh atrofida aylanish davri?", "Taxminan 365 kun", ["24 soat", "30 kun", "12 oy emas"], "1 yil."),
 _b("Yer o‘q atrofida aylanishi...", "Kecha-kunduzni hosil qiladi", ["Fasllarni hosil qiladi", "Oy fazalarini", "Tutilishni"], "24 soat."),
 _b("Fasllarga sabab?", "Yer o‘qining egikligi", ["Quyoshgacha masofa", "Oy", "Shamol"], "O‘q 23,5° egilgan."),
],
}
for _k, _v in _F.items():
    _fakt(_k, _v)

def _sh(kod):
    def deco(f): reg(kod, "ochiq")(f); return f
    return deco

@_sh("S8-ORG")
def n_org(rng):
    a = rng.choice([6, 12, 18]); r = rng.choice([2, 3, 4]); 
    return _o(f"Bakteriya har 20 daqiqada ikkiga bo‘linadi. Boshida {a} ta bor.", [("a) 20 daqiqadan keyin nechta?", a * 2), ("b) 1 soatdan keyin nechta?", a * 8)], [f"a) {a}·2 = {a * 2}.", f"b) 3 marta bo‘linadi: {a}·2³ = {a * 8}."])

@_sh("S8-HUJ")
def n_huj(rng):
    o, ob = rng.choice([(10, 10), (10, 40), (15, 40), (10, 100)]); 
    return _o(f"Mikroskopda okulyar {o}×, ob’ektiv {ob}×.", [("a) Umumiy kattalashtirish?", o * ob), ("b) 2 µm li hujayra qanday kattalikda ko‘rinadi? (µm)", 2 * o * ob)], [f"a) {o}·{ob} = {o * ob}.", f"b) 2·{o * ob} = {2 * o * ob}."])

@_sh("S8-KOP")
def n_kop(rng):
    return _o("Ota-onaning ikkalasi ham geterozigota (Aa) bo‘lsa, 4 ta kombinatsiya: AA, Aa, aA, aa.", [("a) Aa (geterozigota) kombinatsiyalar soni?", 2), ("b) aa kombinatsiya ehtimoli? (kasr)", Fraction(1, 4))], ["a) Aa va aA — 2 ta.", "b) 1/4."])

@_sh("S8-MOS")
def n_mos(rng):
    a = rng.choice([100, 200, 400]); p = rng.choice([20, 25, 50])
    return _o(f"Aholida {a} ta qo‘ng‘iz bor, {p}% i yashil (ko‘rinadigan), qolgani jigarrang.", [("a) Yashillar soni?", a * p // 100), ("b) Jigarranglar soni?", a - a * p // 100)], [f"a) {a}·{p}/100 = {a * p // 100}.", f"b) {a} − {a * p // 100} = {a - a * p // 100}."])

@_sh("S8-EKO")
def n_eko(rng):
    e = rng.choice([10000, 20000, 50000])
    return _o(f"Zanjir: o‘simlik ({e} kJ) → o‘txo‘r → yirtqich. Har bosqichda 10% o‘tadi.", [("a) O‘txo‘rga necha kJ?", e // 10), ("b) Yirtqichga necha kJ?", e // 100)], [f"a) {e}·10% = {e // 10}.", f"b) {e // 10}·10% = {e // 100}."])

@_sh("S8-SOG")
def n_sog(rng):
    n = rng.choice([200, 400, 500]); p = rng.choice([80, 90, 95])
    return _o(f"{n} bolaga emlash qilindi, {p}% ida immunitet hosil bo‘ldi.", [("a) Immunitet hosil bo‘lganlar?", n * p // 100), ("b) Hosil bo‘lmaganlar?", n - n * p // 100)], [f"a) {n}·{p}/100 = {n * p // 100}.", f"b) {n} − {n * p // 100} = {n - n * p // 100}."])

@_sh("S8-TAR")
def n_tar(rng):
    ar = {"H": 1, "C": 12, "O": 16, "N": 14}
    f, a = rng.choice([("H₂O", 18), ("CO₂", 44), ("CH₄", 16), ("O₂", 32), ("NH₃", 17)])
    return _o(f"Atom massalari: H=1, C=12, N=14, O=16. Molekula: {f}.", [("a) Molyar massasi (g/mol)?", a), ("b) 2 mol massasi (g)?", 2 * a)], [f"a) Atom massalari yig‘indisi = {a}.", f"b) 2·{a} = {2 * a}."])

@_sh("S8-XOS")
def n_xos(rng):
    t = rng.choice([20, 40, 60, 80]); s = rng.choice([30, 35, 40])
    return _o(f"100 g suvda 20°C da {s} g tuz eriydi. 250 g suvda necha g tuz eriydi?", [("a) 100 g suvda?", s), ("b) 250 g suvda?", Fraction(s * 250, 100))], [f"a) {s}.", f"b) {s}·2,5 = {num(Fraction(s * 250, 100))}."])

@_sh("S8-REA")
def n_rea(rng):
    a = rng.randint(10, 40); b = rng.randint(10, 40)
    return _o(f"Reaksiyada {a} g A va {b} g B moddasi to‘liq reaksiyaga kirishdi.", [("a) Reaksiyaga kirishgan jami massa?", a + b), ("b) Hosil bo‘lgan modda massasi (massa saqlanish qonuni)?", a + b)], [f"a) {a} + {b} = {a + b}.", f"b) {a + b}."])

@_sh("S8-HOL")
def n_hol(rng):
    m = rng.choice([100, 200, 500]); 
    return _o(f"Muzning erish issiqligi 334 J/g (yaxlitlab 330 deb oling). {m} g muzni eritish uchun necha J kerak?", [("a) 1 g uchun?", 330), (f"b) {m} g uchun?", 330 * m)], ["a) 330.", f"b) 330·{m} = {330 * m}."])

@_sh("S8-ISS")
def n_iss(rng):
    m = rng.choice([1, 2, 5]); dt = rng.choice([10, 20, 30])
    return _o(f"Suvning solishtirma issiqlik sig‘imi 4 kJ/(kg·°C) (yaxlitlangan). {m} kg suv {dt}°C ga isitiladi.", [("a) Q = c·m·Δt (kJ)?", 4 * m * dt), ("b) Massa ikki baravar bo‘lsa Q (kJ)?", 8 * m * dt)], [f"a) 4·{m}·{dt} = {4 * m * dt}.", f"b) {8 * m * dt}."])

@_sh("S8-YOR")
def n_yor(rng):
    t = rng.choice([2, 3, 5, 10])
    return _o(f"Tovush havoda 340 m/s tezlikda tarqaladi. Chaqmoq chaqnadi, {t} soniyadan keyin guldurak eshitildi.", [("a) Chaqmoqqacha masofa (m)?", 340 * t), ("b) Km da? (kasr yoki o‘nli)", Fraction(340 * t, 1000))], [f"a) 340·{t} = {340 * t}.", f"b) {340 * t}/1000 = {num(Fraction(340 * t, 1000))}."])

@_sh("S8-ELE")
def n_ele(rng):
    u = rng.choice([12, 24, 36]); r = rng.choice([2, 3, 4, 6])
    return _o(f"Zanjirda kuchlanish {u} V, qarshilik {r} Ω.", [("a) Tok kuchi (A)?", Fraction(u, r)), (f"b) Ikkita shunday qarshilik ketma-ket ulansa, tok kuchi (A)?", Fraction(u, 2 * r))], [f"a) I = U/R = {u}/{r} = {num(Fraction(u, r))}.", f"b) R = {2 * r}; I = {u}/{2 * r} = {num(Fraction(u, 2 * r))}."])

@_sh("S8-KUC")
def n_kuc(rng):
    m = rng.choice([200, 500, 800]); v = rng.choice([20, 50, 100])
    while m % v: v = rng.choice([20, 50, 100]); m = v * rng.randint(2, 20)
    return _o(f"Jism massasi {m} g, hajmi {v} sm³.", [("a) Zichligi (g/sm³)?", Fraction(m, v)), ("b) Zichligi 1 g/sm³ dan katta bo‘lsa suvda cho‘kadi. Cho‘kadimi? (1 — ha, 0 — yo‘q)", 1 if m > v else 0)], [f"a) {m}/{v} = {num(Fraction(m, v))}.", f"b) {'katta, cho‘kadi' if m > v else 'kichik, suzadi'}."])

@_sh("S8-YER")
def n_yer(rng):
    h = rng.choice([100, 200, 300]); k = rng.choice([2, 3, 5])
    return _o(f"Xaritada gorizontallar har {h} m dan o‘tkazilgan. A nuqta {k} ta gorizontaldan yuqorida, daryo 0 m da.", [("a) A nuqta balandligi (m)?", h * k), ("b) Shu nuqtadan daryogacha balandlik farqi (m)?", h * k)], [f"a) {k}·{h} = {h * k}.", f"b) {h * k} − 0 = {h * k}."])

@_sh("S8-JAR")
def n_jar(rng):
    v = rng.choice([2, 3, 5, 8]); t = rng.choice([10, 20, 50])
    return _o(f"Plita yiliga {v} sm tezlikda siljiydi.", [(f"a) {t} yilda necha sm?", v * t), ("b) 1 000 000 yilda necha km? (1 km = 100 000 sm)", v * 10)], [f"a) {v}·{t} = {v * t}.", f"b) {v}·10⁶/10⁵ = {v * 10}."])

@_sh("S8-RES")
def n_res(rng):
    z = rng.choice([1000, 2000, 5000]); k = rng.choice([50, 100, 250])
    return _o(f"Konda {z} tonna ko‘mir bor, yiliga {k} tonna qaziladi.", [("a) Necha yilga yetadi?", Fraction(z, k)), ("b) Qazish 2 baravar oshsa necha yilga yetadi?", Fraction(z, 2 * k))], [f"a) {z}/{k} = {num(Fraction(z, k))}.", f"b) {z}/{2 * k} = {num(Fraction(z, 2 * k))}."])

@_sh("S8-KOI")
def n_koi(rng):
    d = rng.choice([150, 300]); 
    return _o("Yer Quyosh atrofida 365 kunda bir marta aylanadi. Yer o‘z o‘qi atrofida 24 soatda aylanadi.", [("a) 10 kunda Yer o‘z o‘qi atrofida necha marta aylanadi?", 10), ("b) 730 kunda Quyosh atrofida necha marta?", 2)], ["a) 10 marta.", "b) 730/365 = 2."])

TEMA = {
 "S8-ORG": _tema("S8-ORG", "Organizmlar tasnifi va hayotiy jarayonlar", "🧬", "Tasnif va hayotiy jarayonlar", [_d("Tasnif", "Tiriklik belgilari\nUmurtqalilar: baliq, amfibiya, sudralib yuruvchi, qush, sutemizuvchi", "Tirik organizmlar umumiy belgilari bilan ajralib turadi va tuzilishiga ko‘ra guruhlarga ajratiladi.")]),
 "S8-HUJ": _tema("S8-HUJ", "Hujayra va uning vazifalari", "🔬", "Hujayra qismlari va fotosintez", [_d("Hujayra", "Yadro — boshqaruv\nMitoxondriya — energiya\nXloroplast — fotosintez\nCO₂ + H₂O → glyukoza + O₂", "Hujayra qismlari alohida vazifa bajaradi. Mikroskopda kattalashtirish — okulyar va ob’ektiv ko‘paytmasi.")]),
 "S8-KOP": _tema("S8-KOP", "Ko‘payish va irsiyat", "🧫", "Jinsiy/jinssiz ko‘payish, gen", [_d("Irsiyat", "Gen → belgi\nJinsiy: 2 hujayra → zigota\nJinssiz: klon", "Genlar irsiy belgilarni belgilaydi. Orttirilgan belgilar irsiylanmaydi.")]),
 "S8-MOS": _tema("S8-MOS", "Xilma-xillik va moslashish", "🦎", "Tabiiy tanlanish", [_d("Tanlanish", "O‘zgaruvchanlik → kurash → omon qolish → nasl", "Muhitga yaxshi moslashganlar tirik qolib, belgilarini avlodlarga beradi.")]),
 "S8-EKO": _tema("S8-EKO", "Ekotizimlar", "🌳", "Energiya oqimi va munosabatlar", [_d("Energiya oqimi", "Har bosqichda 10% o‘tadi\nProdutsent → konsument → parchalovchi", "Oziq zanjirida har bosqichda energiyaning taxminan o‘ndan bir qismi o‘tadi.")]),
 "S8-SOG": _tema("S8-SOG", "Inson salomatligi", "🩺", "Kasalliklar, immunitet, qon", [_d("Immunitet", "Eritrotsit — O₂\nLeykotsit — himoya\nTrombotsit — ivish\nEmlash — antitana", "Qon hujayralari turli vazifalarni bajaradi, emlash esa immunitetni oldindan tayyorlaydi.")]),
 "S8-TAR": _tema("S8-TAR", "Moddalar tasnifi va tarkibi", "⚗️", "Element, birikma, aralashma", [_d("Tasnif", "Element: O₂, Fe\nBirikma: H₂O, CO₂\nAralashma: havo", "Element bir xil atomlardan, birikma kimyoviy bog‘langan turli atomlardan iborat, aralashma esa fizik usulda ajratiladi.")]),
 "S8-XOS": _tema("S8-XOS", "Moddalar xossalari", "🧪", "Fizik/kimyoviy xossa, pH", [_d("pH", "pH < 7 kislota\npH = 7 neytral\npH > 7 ishqor", "pH shkalasi kislota va ishqorni ajratadi. Eruvchanlik jadvaliga ko‘ra erigan modda miqdori hisoblanadi.")]),
 "S8-REA": _tema("S8-REA", "Kimyoviy o‘zgarishlar", "🔥", "Reaksiya belgilari, massa saqlanishi", [_d("Reaksiya", "Belgilar: gaz, cho‘kma, rang, issiqlik\nMassa saqlanadi", "Reaksiyada yangi moddalar hosil bo‘ladi, lekin umumiy massa o‘zgarmaydi.")]),
 "S8-HOL": _tema("S8-HOL", "Moddaning agregat holatlari", "💧", "Zarrachalar va holat o‘zgarishi", [_d("Holatlar", "Erish, qotish, bug‘lanish, kondensatsiya\n0 °C — muzlash, 100 °C — qaynash", "Holat zarrachalarning joylashuvi va harakatiga bog‘liq.")]),
 "S8-ISS": _tema("S8-ISS", "Energiya, issiqlik va harorat", "🌡️", "Energiya turlari, issiqlik uzatish", [_d("Issiqlik", "Q = c·m·Δt\nO‘tkazuvchanlik, konveksiya, nurlanish", "Issiqlik issiqdan sovuqqa uzatiladi. Q = c·m·Δt formulasi isitishda kerakli energiyani beradi.")]),
 "S8-YOR": _tema("S8-YOR", "Yorug‘lik va tovush", "🔊", "Qaytish, sinish, tebranish", [_d("To‘lqinlar", "Qaytish: tushish = qaytish\nTovush — tebranish, vakuumda yo‘q\ns = v·t", "Yorug‘lik to‘g‘ri tarqaladi, qaytadi va sinadi. Tovush muhit kerak bo‘ladigan tebranish.")]),
 "S8-ELE": _tema("S8-ELE", "Elektr va magnetizm", "⚡", "Om qonuni, zanjirlar, magnit", [_d("Om qonuni", "I = U / R\nKetma-ket: R = R₁ + R₂\nBir xil qutblar itariladi", "Tok kuchi kuchlanishga to‘g‘ri, qarshilikka teskari proporsional.")]),
 "S8-KUC": _tema("S8-KUC", "Kuch va harakat", "🚀", "Tezlik, bosim, zichlik", [_d("Formulalar", "v = s/t\np = F/S\nρ = m/V", "Tezlik yo‘lning vaqtga, bosim kuchning yuzaga, zichlik massaning hajmga nisbati.")]),
 "S8-YER": _tema("S8-YER", "Yer tuzilishi", "🗺️", "Qatlamlar, xarita", [_d("Qatlamlar", "Po‘st → mantiya → yadro\nGorizontal zich = tik", "Yer po‘st, mantiya va yadrodan iborat. Xaritada gorizontallar relyefni ko‘rsatadi.")]),
 "S8-JAR": _tema("S8-JAR", "Yerdagi jarayonlar va tarix", "🌋", "Plitalar, vulqon, zilzila", [_d("Plitalar", "Plitalar siljiydi → zilzila, vulqon\nMateriklar siljishi", "Litosfera plitalari harakati zilzila va vulqonlarni keltirib chiqaradi.")]),
 "S8-RES": _tema("S8-RES", "Tabiiy resurslar va ularni asrash", "♻️", "Resurslar, eroziya", [_d("Resurslar", "Tiklanadigan: Quyosh, shamol\nTiklanmaydigan: neft, ko‘mir\nEroziyaga qarshi: daraxt", "Tiklanmaydigan resurslarni tejash va tiklanadiganlardan foydalanish kerak.")]),
 "S8-KOI": _tema("S8-KOI", "Quyosh tizimi va koinot", "🪐", "Sayyoralar, Oy fazalari, tutilish", [_d("Harakatlar", "O‘q atrofida 24 soat\nQuyosh atrofida 365 kun\nFasllar — o‘q egikligi", "Yer harakatlari kecha-kunduz va fasllarni, Oy joylashuvi esa fazalar va tutilishlarni keltirib chiqaradi.")]),
}
