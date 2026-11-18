"""PISA tabiiy fanlar (PS-TUS, PS-TAJ, PS-MAL) va o'qish (PR-TOP, PR-TUS, PR-BAH)."""
from fractions import Fraction

from modules.pisa_mat_g import reg, num, _y, _o, _yopiq, fig_stolbik, fig_chiziq

def _tema(kod, nom, soha, belgi, maqsad, dars, top):
    return {"nom": nom, "soha": soha, "belgi": belgi, "maqsad": maqsad, "bolim": kod, "toplam": top, "dars": dars}

def _d(sar, doska, ovoz):
    return {"sarlavha": sar, "doska": doska, "ovoz": ovoz}

def _fakt(kod, banki):
    """banki: [(savol, to'g'ri, [noto'g'rilar], izoh)] — har biri alohida shablon."""
    for i, (sv, tj, no, iz) in enumerate(banki):
        def f(rng, sv=sv, tj=tj, no=no, iz=iz):
            return _yopiq(rng, sv, tj, [iz], noto=list(no), tartib=False)
        f.__name__ = f"{kod}_f{i}"
        reg(kod, "yopiq")(f)

# ───── PS-TUS: hodisalarni ilmiy tushuntirish ─────
_fakt("PS-TUS", [
    ("Nima uchun yozda asfalt qora kiyimdan ko‘ra sekinroq qiziydi? Mos tushuntirishni tanlang.", "Asfalt issiqlikni to‘plab, sekin uzatadi", ["Asfalt issiqlikni umuman yutmaydi", "Quyosh faqat kiyimga tushadi", "Asfalt yengil materialdir"], "Issiqlik sig‘imi va yutilish materialga bog‘liq."),
    ("Suv qaynaganda nima sodir bo‘ladi?", "Suyuqlik bug‘ga aylanadi", ["Suv elementlarga parchalanadi", "Suv yo‘qoladi", "Suv muzlaydi"], "Qaynash — suyuqlikning gazga aylanishi (fizik o‘zgarish)."),
    ("O‘simlik fotosintezda qaysi gazni yutadi?", "Karbonat angidrid", ["Kislorod", "Azot", "Vodorod"], "Fotosintez: CO₂ + suv + yorug‘lik → glyukoza + O₂."),
    ("Nima uchun Oy bizga yorug‘ ko‘rinadi?", "Quyosh nurini qaytaradi", ["O‘zi yorug‘lik chiqaradi", "Yer nurini qaytaradi", "Yulduz bo‘lgani uchun"], "Oy o‘zi yorug‘lik chiqarmaydi, Quyosh nurini qaytaradi."),
    ("Sovuq stakan sirtida suv tomchilari nima uchun hosil bo‘ladi?", "Havodagi bug‘ sovuq sirtda kondensatsiyalanadi", ["Stakan suv o‘tkazadi", "Stakan ichidan suv sizadi", "Havo suvga aylanadi"], "Iliq nam havo sovuq sirtga tegib, suv tomchisiga aylanadi."),
    ("Mashina keskin tormoz bersa, yo‘lovchilar oldinga intiladi. Bu qaysi hodisa?", "Inersiya", ["Ishqalanish", "Magnitlanish", "Bug‘lanish"], "Jism o‘z harakat holatini saqlashga intiladi — inersiya."),
    ("Nima uchun qishda qor ostidagi o‘simliklar ko‘pincha saqlanadi?", "Qor issiqlik izolyatori vazifasini bajaradi", ["Qor issiqlik ishlab chiqaradi", "Qor o‘g‘it bo‘ladi", "Qor sovuqni kuchaytiradi"], "Qor orasida havo ko‘p — issiqlikni yomon o‘tkazadi."),
])

@reg("PS-TUS", "yopiq")
def tus_zichlik(rng):
    m = rng.choice([200, 300, 500, 800]); v = rng.choice([10, 20, 25, 40, 50])
    while m % v: v = rng.choice([10, 20, 25, 40, 50]); m = v * rng.randint(2, 20)
    return _y(rng, f"Jismning massasi {m} g, hajmi {v} sm³. Zichligi necha g/sm³?", Fraction(m, v), [f"ρ = m/V = {m}/{v} = {num(Fraction(m, v))}."], noto=[m * v, Fraction(v, m), m + v])

@reg("PS-TUS", "ochiq")
def tus_tezlik(rng):
    s = rng.choice([120, 180, 240]); t = rng.choice([2, 3, 4, 6])
    return _o(f"Velosipedchi {s} m ni {t} daqiqada bosib o‘tdi.", [("a) O‘rtacha tezligi necha m/daqiqa?", Fraction(s, t)), (f"b) Shu tezlikda {t * 3} daqiqada necha metr yuradi?", Fraction(s, t) * t * 3)], [f"a) {s}/{t} = {num(Fraction(s, t))}.", f"b) {num(Fraction(s, t))}·{t * 3} = {num(Fraction(s * 3))}."])

@reg("PS-TUS", "ochiq")
def tus_isitish(rng):
    a = rng.choice([20, 25, 30]); b = rng.choice([60, 70, 80]); m = rng.choice([2, 3, 5])
    return _o(f"Suv harorati {a}°C dan {b}°C gacha isitildi. Har 1°C ga isitish uchun {m} birlik energiya ketadi.", [("a) Harorat necha °C ga ko‘tarildi?", b - a), ("b) Jami necha birlik energiya ketdi?", (b - a) * m)], [f"a) {b} − {a} = {b - a}.", f"b) {b - a}·{m} = {(b - a) * m}."])

@reg("PS-TUS", "ochiq")
def tus_elektr(rng):
    p = rng.choice([40, 60, 100]); h = rng.choice([4, 5, 10]); k = rng.choice([500, 600, 800])
    return _o(f"{p} Vt lampa kuniga {h} soat yonadi. 1 kVt·soat narxi {k} so‘m.", [("a) Kunlik energiya (Vt·soat)?", p * h), ("b) 30 kunda necha kVt·soat?", Fraction(p * h * 30, 1000))], [f"a) {p}·{h} = {p * h}.", f"b) {p * h}·30/1000 = {num(Fraction(p * h * 30, 1000))}."])

@reg("PS-TUS", "yopiq")
def tus_aralash(rng):
    a = rng.choice([30, 40, 50]); b = rng.choice([20, 25, 30]); 
    return _y(rng, f"Eritmada {a} g tuz va {b * 10} g suv bor. Eritma massasi necha g?", a + b * 10, [f"{a} + {b * 10} = {a + b * 10}."], noto=[b * 10 - a, a * b, a + b])

# ───── PS-TAJ: ilmiy tadqiq (tajriba) ─────
_fakt("PS-TAJ", [
    ("Tajribada faqat bitta omil o‘zgartiriladi, qolganlari bir xil qoladi. Nima uchun?", "Natija aynan shu omilga bog‘liqligini bilish uchun", ["Tajriba tezroq tugashi uchun", "Hamma natija bir xil chiqishi uchun", "Asbob tejalishi uchun"], "Nazorat qilinadigan o‘zgaruvchilar adolatli taqqoslash beradi."),
    ("O‘simlikka yorug‘lik ta’sirini o‘rganishda qaysi omil bir xil bo‘lishi kerak?", "Suv miqdori", ["Yorug‘lik miqdori", "Hech narsa", "O‘simlik rangi turli"], "Faqat yorug‘lik o‘zgaradi, suv bir xil bo‘lishi lozim."),
    ("Gipoteza nima?", "Tekshirish mumkin bo‘lgan taxminiy tushuntirish", ["Isbotlangan qonun", "Tajriba natijasi", "Asbob nomi"], "Gipoteza tajriba bilan tekshiriladi."),
    ("Nima uchun tajribani bir necha marta takrorlash kerak?", "Tasodifiy xatolar ta’sirini kamaytirish uchun", ["Vaqtni ko‘paytirish uchun", "Natijani o‘zgartirish uchun", "Hech qanday sababsiz"], "Takrorlash natijaning ishonchliligini oshiradi."),
    ("Nazorat guruhi nima uchun kerak?", "Taqqoslash uchun asos beradi", ["Natijani buzish uchun", "Tajribani qiyinlashtirish uchun", "Hajmni kamaytirish uchun"], "Nazorat guruhi ta’sir qo‘llanilmagan holatni ko‘rsatadi."),
    ("Qaysi biri o‘lchanadigan (bog‘liq) o‘zgaruvchi: «Urug‘ ko‘karish tezligi»?", "Ha, natija sifatida o‘lchanadi", ["Yo‘q, u o‘zgartiriladigan omil", "Yo‘q, u doimiy omil", "Hech qaysi"], "Natija o‘lchanadigan o‘zgaruvchi hisoblanadi."),
])

@reg("PS-TAJ", "ochiq")
def taj_grafik(rng):
    k = rng.choice([2, 3, 4]); b = rng.choice([5, 10]); 
    q = _o(f"O‘simlik bo‘yi (sm) kunlar bo‘yicha o‘lchandi: h = {k}·t + {b} (t — kun).", [("a) Boshlang‘ich bo‘yi necha sm?", b), ("b) 5-kunda bo‘yi necha sm?", 5 * k + b)], [f"a) t = 0: h = {b}.", f"b) {k}·5 + {b} = {5 * k + b}."])
    q["rasm"] = fig_chiziq(b, k, 5, "t", "h", sarlavha="O‘simlik bo‘yi"); return q

@reg("PS-TAJ", "ochiq")
def taj_ortacha(rng):
    xs = [rng.randint(10, 20) for _ in range(4)]; xs.append(5 * 15 - sum(xs) if 10 <= 75 - sum(xs) <= 20 else 15)
    return _o(f"Besh marta o‘lchash natijalari (soniya): {', '.join(map(str, xs))}.", [("a) Yig‘indi?", sum(xs)), ("b) O‘rtacha natija?", Fraction(sum(xs), 5))], [f"a) {' + '.join(map(str, xs))} = {sum(xs)}.", f"b) {sum(xs)}/5 = {num(Fraction(sum(xs), 5))}."])

@reg("PS-TAJ", "yopiq")
def taj_ustun(rng):
    n = ["A", "B", "V", "G"]; v = rng.sample(range(10, 60, 5), 4); i = v.index(max(v))
    q = _yopiq(rng, "Diagrammada 4 xil o‘g‘it bilan o‘sgan o‘simlik bo‘yi (sm) ko‘rsatilgan. Qaysi o‘g‘it eng yaxshi natija bergan?", n[i], [f"Eng baland ustun: {n[i]} ({v[i]} sm)."], noto=[x for x in n if x != n[i]], tartib=False)
    q["rasm"] = fig_stolbik(n, v, "O‘simlik bo‘yi"); return q

@reg("PS-TAJ", "ochiq")
def taj_foiz(rng):
    n = rng.choice([40, 50, 80]); k = rng.choice([30, 40, 60])
    return _o(f"{n} ta urug‘ ekildi, {n * k // 100} tasi unib chiqdi.", [("a) Unib chiqqanlar necha foiz?", k), ("b) Unmaganlar soni?", n - n * k // 100)], [f"a) {n * k // 100}/{n}·100 = {k}%.", f"b) {n} − {n * k // 100} = {n - n * k // 100}."])

@reg("PS-TAJ", "yopiq")
def taj_masshtab(rng):
    a = rng.choice([4, 5, 8]); b = rng.choice([2, 3])
    return _y(rng, f"Menzurkada suv hajmi {a * 10} ml edi, jism tushirilgach {a * 10 + b * 5} ml bo‘ldi. Jism hajmi necha ml?", b * 5, [f"{a * 10 + b * 5} − {a * 10} = {b * 5}."], noto=[a * 10, a * 10 + b * 5, b])

# ───── PS-MAL: ma'lumot va dalillarni sharhlash ─────
@reg("PS-MAL", "ochiq")
def mal_jadval(rng):
    y = [rng.randint(5, 30) for _ in range(4)]; n = ["Yanvar", "Fevral", "Mart", "Aprel"]
    q = _o("Diagrammada oylar bo‘yicha o‘rtacha harorat (°C) berilgan.", [("a) Eng issiq oy harorati?", max(y)), ("b) Eng issiq va eng sovuq oy farqi?", max(y) - min(y))], [f"a) {max(y)}.", f"b) {max(y)} − {min(y)} = {max(y) - min(y)}."])
    q["rasm"] = fig_stolbik(n, y, "Harorat °C"); return q

_fakt("PS-MAL", [
    ("Grafikda ikki kattalik birga o‘sadi. Bu albatta birining sababi ekanini bildiradimi?", "Yo‘q, bog‘liqlik sabab degani emas", ["Ha, har doim", "Faqat grafik chiziqli bo‘lsa", "Faqat jadval bo‘lsa"], "Korrelyatsiya sababiyatni isbotlamaydi."),
    ("Qaysi manba ilmiy da’voni tasdiqlashda eng ishonchli?", "Hakamlar tekshirgan ilmiy maqola", ["Tasodifiy izoh", "Reklama", "Ijtimoiy tarmoqdagi post"], "Ekspertlar tekshirgan (retsenziyalangan) manba ishonchliroq."),
    ("«Hamma ichimliklarni ichgan 2 kishida yaxshi natija bo‘ldi» — bu xulosa nima uchun zaif?", "Namuna juda kichik", ["Namuna juda katta", "Ma’lumot juda aniq", "Hech qanday kamchilik yo‘q"], "Kichik namunadan umumiy xulosa chiqarib bo‘lmaydi."),
    ("Qaysi grafik vaqt bo‘yicha o‘zgarishni eng yaxshi ko‘rsatadi?", "Chiziqli grafik", ["Doira diagramma", "Faqat jadval nomlari", "Rasm"], "Vaqt o‘qida chiziqli grafik qulay."),
    ("Ma’lumotdagi bitta juda katta qiymat (chetki nuqta) o‘rtachaga qanday ta’sir qiladi?", "O‘rtachani sezilarli oshirishi mumkin", ["Hech ta’sir qilmaydi", "O‘rtachani nolga tushiradi", "Medianani o‘zgartirmaydi va o‘rtachani ham"], "O‘rtacha chetki qiymatlarga sezgir."),
])

@reg("PS-MAL", "ochiq")
def mal_foiz(rng):
    a, b = rng.choice([(40, 50), (50, 60), (20, 25)]); 
    return _o(f"Ilmiy tadqiqotda kasallik soni {a} tadan {b} taga oshdi.", [("a) Farq nechta?", b - a), ("b) Necha foizga oshdi?", Fraction(100 * (b - a), a))], [f"a) {b} − {a} = {b - a}.", f"b) {b - a}/{a}·100 = {num(Fraction(100 * (b - a), a))}%."])

@reg("PS-MAL", "yopiq")
def mal_interpol(rng):
    x1, y1 = 2, rng.choice([10, 20]); d = rng.choice([5, 10]); 
    return _y(rng, f"Jadval: 2 soatda {y1} birlik, 4 soatda {y1 + 2 * d} birlik. Chiziqli bog‘lanish deb olsak, 3 soatda necha birlik?", y1 + d, [f"O‘rtasi: ({y1} + {y1 + 2 * d})/2 = {y1 + d}."], noto=[y1 + 2 * d, y1 + d + 2, y1 + 3])

TEMA = {}
_S = "P_S"; _R = "P_R"
TEMA["PS-TUS"] = _tema("PS-TUS", "Hodisalarni ilmiy tushuntirish", "Fan", "🔬", "Fizik, kimyoviy va biologik hodisalarni asoslash", [
    _d("Tushuntirishni qurish", "Hodisa → qonun → sabab\nZichlik: ρ = m / V\nTezlik: v = s / t", "Ilmiy tushuntirish hodisani qonun bilan bog‘laydi. Masalan, zichlik massaning hajmga nisbati, tezlik esa yo‘lning vaqtga nisbati."),
    _d("Energiya va issiqlik", "Issiqlik — isitilgan jismdan sovuqqa\nKondensatsiya: bug‘ → suyuqlik\nInersiya", "Issiqlik doim issiqroq jismdan sovuqroqqa o‘tadi. Bug‘ sovuq sirtda suvga aylanadi. Jismlar o‘z harakat holatini saqlashga intiladi.")], _S)
TEMA["PS-TAJ"] = _tema("PS-TAJ", "Ilmiy tadqiqotni baholash va loyihalash", "Fan", "🧪", "Gipoteza, o‘zgaruvchilar, nazorat, o‘lchash natijalari", [
    _d("Tajriba loyihasi", "Gipoteza → tajriba → natija → xulosa\nBitta omil o‘zgaradi\nNazorat guruhi", "Yaxshi tajribada faqat bitta omil o‘zgartiriladi, boshqalari bir xil. Nazorat guruhi taqqoslash uchun kerak, takrorlash esa ishonchlilikni oshiradi."),
    _d("Natijani o‘qish", "O‘rtacha = yig‘indi / soni\nFoiz = qism / butun · 100\nGrafik: ustunlarni solishtir", "O‘lchovlar o‘rtachasini hisoblaymiz, foizni qism va butunning nisbatidan topamiz, diagrammada eng yuqori yoki eng past qiymatni aniqlaymiz.")], _S)
TEMA["PS-MAL"] = _tema("PS-MAL", "Ma’lumot va dalillarni ilmiy sharhlash", "Fan", "📈", "Grafik, jadval, xulosa chiqarish va manba baholash", [
    _d("Dalil bilan xulosa", "Grafik → trend → xulosa\nBog‘liqlik ≠ sabab\nKichik namuna — zaif xulosa", "Xulosa faqat ma’lumot yetarli bo‘lganda chiqariladi. Ikki kattalik birga o‘zgarsa ham, biri ikkinchisining sababi bo‘lishi shart emas.")], _S)

# ───────────── PISA o'qish ─────────────
_matnlar = {
    "PR-TOP": [
        ("«Ipak yo‘li Xitoydan O‘rta yer dengizigacha cho‘zilgan savdo yo‘llari tizimi bo‘lgan. Bu yo‘l orqali ipak, ziravorlar va g‘oyalar almashilgan. Samarqand va Buxoro yo‘ldagi muhim shaharlar edi.»",
         [("Matnning asosiy g‘oyasi qaysi?", "Ipak yo‘li savdo va g‘oyalar almashinuvi yo‘li bo‘lgan", ["Ipak faqat Xitoyda ishlab chiqilgan", "Samarqand eng katta dengiz", "Ziravorlar zararli bo‘lgan"]),
          ("Matnda yo‘lda qanday shaharlar eslatilgan?", "Samarqand va Buxoro", ["Toshkent va Dubay", "Parij va Rim", "Moskva va Pekin"])]),
        ("«Suv aylanishi dengiz va ko‘llardan suv bug‘lanishidan boshlanadi. Bug‘ ko‘tarilib bulutga aylanadi, keyin yomg‘ir yoki qor bo‘lib yerga tushadi. Suv daryolar orqali yana dengizga qaytadi.»",
         [("Bulut qanday hosil bo‘ladi?", "Ko‘tarilgan bug‘ sovub bulutga aylanadi", ["Yer qizib", "Shamol hosil qiladi", "Daryo to‘kilib"]),
          ("Suv oxirida qayerga qaytadi?", "Dengizga", ["Tog‘ cho‘qqisiga", "Bulutga", "Cho‘lga"])]),
        ("«Kitob o‘qish xotirani mustahkamlaydi va lug‘at boyligini oshiradi. Kuniga 20 daqiqa o‘qigan o‘quvchi yiliga o‘rtacha 15 ta kitob tugatishi mumkin.»",
         [("Matnga ko‘ra kitob o‘qishning foydasi nima?", "Xotira va lug‘atni boyitadi", ["Ko‘zni charchatadi", "Vaqtni yo‘qotadi", "Hech foydasi yo‘q"]),
          ("Kuniga qancha vaqt o‘qish tavsiya qilingan?", "20 daqiqa", ["2 soat", "5 daqiqa", "1 daqiqa"])]),
        ("«Elektr avtomobillar benzinsiz, batareya quvvatida yuradi. Ular havoni kamroq ifloslantiradi, lekin zaryad olish stansiyalari kerak.»",
         [("Elektr avtomobilning afzalligi nima?", "Havoni kamroq ifloslantiradi", ["Benzin ishlatadi", "Zaryad kerak emas", "Juda arzon"]),
          ("Qanday infratuzilma zarur?", "Zaryad olish stansiyalari", ["Neft quvurlari", "Dengiz portlari", "Aeroportlar"])]),
        ("«Ulug‘bek Samarqandda rasadxona qurdirgan va yulduzlar jadvalini tuzgan. Uning ishlari astronomiya rivojiga katta hissa qo‘shdi.»",
         [("Ulug‘bek nima qurdirdi?", "Rasadxona", ["Ko‘prik", "Kutubxona faqat", "Stadion"]),
          ("Uning asosiy hissasi qaysi sohada?", "Astronomiya", ["Tibbiyot", "Sport", "Qishloq xo‘jaligi"])]),
    ],
}
_matnlar["PR-TUS"] = [
    ("«Sinfdagi o‘quvchilarning 60 foizi sport bilan shug‘ullanadi, lekin faqat 20 foizi musobaqalarda qatnashadi. Qolganlarida vaqt yetishmasligi asosiy sabab.»",
     [("Matndan qanday xulosa chiqadi?", "Ko‘pchilik sport bilan shug‘ullansa ham musobaqada kamchilik qatnashadi", ["Hamma musobaqada qatnashadi", "Hech kim sport qilmaydi", "Sport foydasiz"]),
      ("Qatnashmaslikning asosiy sababi nima?", "Vaqt yetishmasligi", ["Pul yetishmasligi", "Qiziqmaslik", "Salomatlik"])]),
    ("«Ayrim shaharlarda velosiped yo‘laklari ko‘paygach, avtomobil tirbandligi kamaydi va havo toza bo‘ldi.»",
     [("Velosiped yo‘laklarining ta’siri qanday?", "Tirbandlik kamayib, havo tozaladi", ["Tirbandlik oshadi", "Havo ifloslanadi", "Hech narsa o‘zgarmaydi"]),
      ("Matn qaysi xulosani qo‘llab-quvvatlaydi?", "Velosiped infratuzilmasi shaharga foyda keltiradi", ["Avtomobillar kerak emas", "Velosiped xavfli", "Shaharlar kichrayadi"])]),
    ("«Qishda ko‘plab qushlar issiq o‘lkalarga uchib ketadi. Chunki sovuqda oziq topish qiyinlashadi.»",
     [("Qushlar nima uchun uchib ketadi?", "Oziq topish qiyinlashadi", ["Ular sovuqni yaxshi ko‘radi", "Suv ko‘payadi", "Yo‘l qurilgani uchun"]),
      ("«Chunki» so‘zidan keyin nima keladi?", "Sabab", ["Natija", "Savol", "Buyruq"])]),
    ("«Do‘kon e’loni: Faqat shu hafta barcha kitoblar 30% arzon! Chegirma o‘quv adabiyotlariga tegishli emas.»",
     [("Qaysi kitoblarga chegirma yo‘q?", "O‘quv adabiyotlariga", ["Badiiy kitoblarga", "Hech qaysiga", "Hammasiga"]),
      ("Chegirma qancha muddatga?", "Shu hafta", ["Bir yil", "Bir kun", "Doimo"])]),
    ("«Daryo suvi tez oqganda, qirg‘oqni yuvib ketadi. Shu sababli qirg‘oqqa daraxt ekiladi: ildizlar tuproqni ushlab turadi.»",
     [("Daraxt ekishdan maqsad nima?", "Tuproq yuvilishining oldini olish", ["Soya hosil qilish faqat", "Suvni to‘xtatish", "Baliq ko‘paytirish"]),
      ("Daryo tez oqsa nima sodir bo‘ladi?", "Qirg‘oq yuviladi", ["Qirg‘oq o‘sadi", "Suv muzlaydi", "Hech narsa"])]),
]
_matnlar["PR-BAH"] = [
    ("«Muallif yozadi: Telefon maktabda butunlay taqiqlanishi kerak, chunki u e’tiborni chalg‘itadi. Biroq ayrim o‘qituvchilar uni dars vositasi sifatida ishlatadi.»",
     [("Muallifning pozitsiyasi qaysi?", "Telefon maktabda taqiqlanishi kerak", ["Telefon doim kerak", "Maktab yopilsin", "Telefon bepul bo‘lsin"]),
      ("Qaysi fikr qarama-qarshi dalil?", "Ayrim o‘qituvchilar uni dars vositasi sifatida ishlatadi", ["U e’tiborni chalg‘itadi", "Muallif yozgan", "Maktab katta"])]),
    ("«Reklama: Bizning sharbat 100% tabiiy va eng foydali! Hamma bolalar uni ichadi.»",
     [("Bu matn nima maqsadda yozilgan?", "Mahsulotni sotish uchun", ["Ilmiy tadqiqot uchun", "Yangilik uchun", "Dars uchun"]),
      ("«Hamma bolalar ichadi» ifodasi nima?", "Isbotsiz umumlashtirish", ["Aniq statistika", "Ilmiy dalil", "Qonun"])]),
    ("«A maqola: sutkada 8 soat uyqu zarur. B maqola: 6 soat yetarli. Ikkalasi ham tadqiqotga tayanadi.»",
     [("Maqolalar nimasi bilan farq qiladi?", "Tavsiya etilgan uyqu soatlari", ["Mavzusi", "Tili", "Muallifi bir xil"]),
      ("Qaysi qadam to‘g‘ri?", "Tadqiqotlar namunasi va metodini solishtirish", ["Birini tasodifan tanlash", "Ikkalasini rad etish", "Reklamaga ishonish"])]),
    ("«Matn: Ko‘p odam kitob o‘qimay qo‘ydi. Bu davrning eng katta fojiasi!»",
     [("«Eng katta fojia» ifodasi nima?", "Muallifning bahosi (fikr)", ["Isbotlangan fakt", "Statistika", "Ta’rif"]),
      ("Faktni fikrdan qanday ajratamiz?", "Fakt tekshiriladi, fikr baholaydi", ["Ikkalasi bir xil", "Fikr tekshiriladi, fakt baholaydi", "Farqi yo‘q"])]),
    ("«Sarlavha: SHOK! Yangi dori hamma kasallikni davolaydi! — Matn ostida hech qanday tadqiqot ko‘rsatilmagan.»",
     [("Bu xabarga qanday munosabatda bo‘lish kerak?", "Manbani va dalilni tekshirish", ["Darhol ishonish", "Do‘stlarga yuborish", "Dori sotib olish"]),
      ("Nima uchun xabar shubhali?", "Dalil ko‘rsatilmagan va ortiqcha va’da bor", ["Sarlavha qisqa", "Matn uzun", "Rasm yo‘q"])]),
]

def _o_qish(kod):
    L = _matnlar[kod]
    for ti, (matn, qs) in enumerate(L):
        for qi, (sv, tj, no) in enumerate(qs):
            def f(rng, matn=matn, sv=sv, tj=tj, no=no):
                q = _yopiq(rng, f"{matn}\n\n{sv}", tj, ["Javob matnda to‘g‘ridan-to‘g‘ri yoki mantiqiy xulosa orqali topiladi."], noto=list(no), tartib=False)
                return q
            f.__name__ = f"{kod}_m{ti}_{qi}"
            reg(kod, "yopiq")(f)
        if kod == "PR-TOP":
            def g(rng, matn=matn, qs=qs):
                return _o(matn, [("a) " + qs[0][0], 1 if False else 2), ("b) " + qs[1][0], 2)], ["Ikki savolga ham matndan javob toping."]) if False else None
for k in ("PR-TOP", "PR-TUS", "PR-BAH"):
    _o_qish(k)

@reg("PR-TOP", "ochiq")
def top_son(rng):
    n = rng.choice([15, 20, 30]); d = rng.choice([10, 20, 30])
    return _o(f"Matnda: «Kuniga {d} daqiqa o‘qigan o‘quvchi yiliga {n} ta kitob tugatadi.»", [("a) Kuniga necha daqiqa o‘qilgan?", d), ("b) Yiliga necha kitob?", n)], ["Raqamlar matnning o‘zida berilgan."])

@reg("PR-TUS", "ochiq")
def tus_gap(rng):
    a = rng.choice([30, 40, 60]); b = rng.choice([10, 20]);
    return _o(f"Matnda: «Sinfdagi o‘quvchilarning {a}% i sport bilan shug‘ullanadi, {b}% i musobaqada qatnashadi.» Sinfda 50 o‘quvchi bor.", [("a) Sport bilan shug‘ullanuvchilar soni?", 50 * a // 100), ("b) Musobaqada qatnashuvchilar soni?", 50 * b // 100)], [f"a) 50·{a}/100 = {50 * a // 100}.", f"b) 50·{b}/100 = {50 * b // 100}."])

@reg("PR-BAH", "ochiq")
def bah_say(rng):
    f, p = rng.choice([(3, 2), (4, 1), (2, 3), (5, 2)])
    return _o(f"Matnda {f} ta fakt va {p} ta fikr (baho) bor.", [("a) Jami nechta gap?", f + p), ("b) Faktlar fikrlardan nechtaga ko‘p? (kam bo‘lsa manfiy)", f - p)], [f"a) {f} + {p} = {f + p}.", f"b) {f} − {p} = {f - p}."])

TEMA["PR-TOP"] = _tema("PR-TOP", "Ma’lumotni topish", "O‘qish", "🔎", "Matndan aniq ma’lumot, raqam va nomlarni topish", [
    _d("Topish strategiyasi", "1. Savolni o‘qi\n2. Kalit so‘zni ajrat\n3. Matndan shu so‘zni top\n4. Javobni tekshir", "Savoldagi kalit so‘zni belgilang va matndan aynan shu so‘z yoki sinonimini qidiring. Javob odatda shu gap atrofida bo‘ladi.")], _R)
TEMA["PR-TUS"] = _tema("PR-TUS", "Tushunish va talqin qilish", "O‘qish", "📖", "Asosiy g‘oya, sabab-oqibat, xulosa chiqarish", [
    _d("Tushunish", "Asosiy g‘oya — matn nima haqida\nSabab: chunki, shu sababli\nXulosa — matndan mantiqiy natija", "Asosiy g‘oya matnning butun mazmunini qamrab oladi. «Chunki» va «shu sababli» kabi so‘zlar sabab-oqibatni ko‘rsatadi. Xulosa matnda to‘g‘ridan-to‘g‘ri yozilmagan, lekin undan kelib chiqadi.")], _R)
TEMA["PR-BAH"] = _tema("PR-BAH", "Baholash va mulohaza", "O‘qish", "⚖️", "Fakt va fikr, manba ishonchliligi, muallif maqsadi", [
    _d("Matnni baholash", "Fakt — tekshiriladi\nFikr — baho\nMuallif maqsadi: xabar / ishontirish / sotish\nManba ishonchli?", "Fakt tekshirib bo‘ladigan ma’lumot, fikr esa muallifning bahosi. Reklama sotish uchun, ilmiy maqola esa tushuntirish uchun yoziladi. Manbani va dalilni tekshirish kerak.")], _R)
