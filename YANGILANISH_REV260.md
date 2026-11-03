# REV260 — «Xalqaro baholash» (TIMSS darajasida o‘qitish, imtihon va reyting)

Bu ro‘yxat backend va frontend uchun umumiy. Yangilanish hozirgi kodingiz ustiga qo‘yiladi. Bazaga 3 ta yangi jadval qo‘shiladi, ular birinchi so‘rovda o‘zi yaratiladi (alohida migratsiya kerak emas).

## Huquqiy qaror (muhim)
TIMSS savollari IEA mulki. Har PDF sahifasida «tijoriy maqsadda ishlatish mumkin emas» deb yozilgan, tarjimalari ham IEA mulki bo‘lib qoladi. Shuning uchun **asl savollar platformaga ko‘chirilmagan**.

Har bir ochiq e’lon qilingan TIMSS 2011 savoliga **o‘zimiz yozgan 2 ta parallel savol** tayyorlangan. Ular quyidagilar bo‘yicha asl savolga mos:
- mazmun sohasi va mavzu;
- fikrlash darajasi (bilish / qo‘llash / mulohaza);
- format va qiyinlik.

Vaziyatlar o‘zbekcha: so‘m, bozor, metro, paxta dalasi, O‘zbekiston tabiati. Asl savolning xalqaro statistikasi (davlatlar bo‘yicha to‘g‘ri yechganlar foizi) manba ko‘rsatilgan holda ishlatiladi. Bu ochiq ma’lumot.

## Kontent (backend/modules/xalqaro_data)
- **savollar.json** — 4 to‘plam: TIMSS 4-sinf matematika (73), 4-sinf tabiiy fanlar (79), 8-sinf matematika (89), 8-sinf tabiiy fanlar (96). Jami **337 asl savol → 674 parallel savol**. Har birida:
  - yechim qadamlari: doskaga yoziladigan satr + ustoz shu paytda aytadigan gap;
  - har noto‘g‘ri variant uchun «nega xato» izohi;
  - ishora, «nimani tekshiradi» va «yechish yo‘li»;
  - kerak joyda SVG rasm (o‘zbekcha yozuvlar bilan qayta chizilgan).
- **darslar.json** — **50 mavzuning har biriga Kabu darsi**. Tarkibi:
  - kirish (dunyo foizi bilan);
  - qoidalar;
  - kamida 2 ta ishlangan misol (biri TIMSS uslubidagi mulohaza masalasi);
  - 2 ta «birga yechamiz»;
  - xalqaro savolni yechish strategiyasi va xulosa;
  - har tushuncha uchun «Tushunmadim»: soddaroq / hikoya orqali / boshqa usulda.
  Doska satrlari va ovozdagi [1], [2] belgilari aniq mos.
- **natijalar.json** — davlatlarning haqiqiy natijalari, manbalari bilan:
  - TIMSS 2019 va 2023: 4- va 8-sinf, matematika va tabiiy fanlar;
  - PISA 2022 va 2025;
  - PIRLS 2021.
  O‘zbekiston natijalari: TIMSS 2023 — 443 / 412 / 421 / 396; PISA tabiiy fanlar 355 → 438 (+83); PIRLS 2021 — 437.
- **ramka.json** — to‘plamlar va mavzular. Har mavzu 1–11 sinf maktab dasturiga bog‘langan (fan, sinflar, kalit so‘zlar).

## Backend
- **modules/xalqaro_baholash.py (yangi)** — API: katalog, mavzu, mavzu_oldi, mashq, javob, takror, imtihonlar, imtihon boshla/topshir/tahlil, reyting, natijalar, sinf_natija, rasm.
  - **Mashq javobi serverda tekshiriladi.** Bilim yangilanadi; xato savol takrorlash navbatiga (Leitner usuli) tushadi. Qayta so‘rash oralig‘i: 1, 2, 4, 8, 16 kun, har gal boshqa variantda.
  - **Imtihonlar:** haftalik, oylik, choraklik (TIMSS 1-qism: 4-sinf 36 daqiqa, 8-sinf 45 daqiqa) va yillik (to‘liq TIMSS daftari: matematika + 10 daqiqa tanaffus + tabiiy fanlar).
    - Savollar TIMSS ramkasi nisbatida tanlanadi: sohalar va fikrlash darajalari ulushi saqlanadi. Yaqinda berilgan savollar takrorlanmaydi.
    - Vaqt serverda hisoblanadi; sahifa yangilansa, imtihon qayta boshlanmaydi.
    - Davrdagi birinchi urinish **rasmiy** hisoblanadi va reytingga kiradi, keyingilari mashq.
    - Imtihon oynasidan chiqib ketishlar soni qayd etiladi.
  - **Baholash:** foiz va **taxminiy TIMSS bali**. Ball Rasch modeli bo‘yicha hisoblanadi: savol qiyinligi asl savolning xalqaro foizidan olinadi, xalqaro markaz = 500. Natija TIMSS darajasiga keltiriladi (400 / 475 / 550 / 625) va TIMSS 2023 hamda 2019 davlatlari orasidagi o‘rni ko‘rsatiladi.
  - **Reyting:** sinfda, maktabda va platformada (sinf bo‘yicha). Kamida 3 o‘quvchi bo‘lsa ko‘rsatiladi, sinfdoshlar ismi yashirin.
  - **Ustoz gapi (Kabu):** salom, maqtov, eslatma yoki **tanbeh**. Faollikka qarab tanlanadi: 7 kundan beri mashq qilinmagan, oxirgi imtihon 40% dan past, haftalik nazorat topshirilmagan yoki haftada 10 tadan kam savol yechilgan.
  - **O‘qituvchi:** o‘z maktabidagi sinf o‘quvchilarining natijasi va faolligi.
- **modules/dars_xonasi.py** — «XB-…» kodli darslar `xalqaro_data/darslar.json` dan ochiladi. Barcha ustozlar, xonalar va ovoz o‘zgarishsiz ishlaydi.
- **main.py** — yangi router ulandi.
- **tests/test_xalqaro_rev260.py** — kontent butunligi, javob tekshirish, ball, imtihon rejasi, davrlar.
- **Yangi jadvallar:** `xb_bilim`, `xb_takror`, `xb_imtihon`.

## Frontend
- **src/xalqaro/** (yangi):
  - **XalqaroBaholash.jsx** — bo‘lim: Kurs / Imtihonlar / Takrorlash / Reyting / Dunyo natijalari / (o‘qituvchiga) Sinfim.
  - **XbMavzu.jsx** — mavzu sahifasi: davlatlar foizi, o‘zlashtirish, sinfdoshlar orasidagi o‘rin, yechish yo‘llari, tipik xatolar, har darajadan namuna savol, kerakli 1–11 sinf maktab darslari.
  - **XbMashq.jsx** — mashq va takrorlash:
    - «Nega xato» izohi, ishora va ustoz doskada yechadi.
    - **Aytib + yozib:** ovoz bilan javob bergan o‘quvchiga ustoz javobni yozdirib tasdiqlatadi.
  - **XbImtihon.jsx** — haqiqiy imtihon rejimi va natija tahlili: ball, daraja, davlatlar diagrammasi, sohalar va fikrlash bo‘yicha natija, reyting, har xato savolga yechim.
  - **XbSavol.jsx** — 🔊 savolni ustoz o‘qib beradi, 🎤 javobni ovoz bilan aytish mumkin («be», «to‘rtinchi», «o‘n ikki», «uch butun besh», «to‘rtdan uch»).
  - **XbDoska.jsx** — yechim doskasi: harfma-harf, ovoz bilan bir xil.
  - **XbMavzuOldi.jsx** — maktab mavzusidan oldingi blok.
- **src/lesson/ChalkText.jsx + chalkRules.js (yangi)** — **doskaga harfma-harf yozish**. Ustoz qaysi so‘zni aytayotgan bo‘lsa, satr shu joygacha yoziladi, formulalar chapdan o‘ngga ochiladi. Bo‘r belgisi qimirlab turadi. «Harakatni kamaytirish» sozlamasini hurmat qiladi.
- **DarsXonasi.jsx, dars-xonasi.css** — barcha darslarda (faqat xalqaro emas) yozilayotgan qator endi harfma-harf chiqadi.
- **LearnerTopics.jsx** — maktab o‘quvchisi matematika yoki tabiiy fan mavzusini ochganda, avval **«Mavzu oldidan: xalqaro baholashda»** chiqadi. Unda:
  - dunyo foizi va davlatlar;
  - o‘quvchining darajasi va sinfdoshlar orasidagi o‘rni;
  - ustoz gapi: maqtov, eslatma yoki tanbeh;
  - namuna savollar.
  Keyin o‘quvchi «Maktab darsini boshlash», «Xalqaro darajadagi dars» yoki «Mashq»ni tanlaydi. Mos xalqaro mavzu topilmasa, dars darhol ochiladi.
- **ustozRules.js** — Fizika, Kimyo, Biologiya, Geografiya, Algebra, Geometriya darslarida tegishli fan ustozi chiqadi (avval ona tili ustozi chiqardi).
- **App.jsx** — o‘quvchi va o‘qituvchi menyusida «Xalqaro baholash» bandi. Bog‘cha va talabaga ko‘rinmaydi.
- **src/xalqaro260.test.mjs** — 5 ta yangi test.

## Tekshiruv
- Backendning 8 ta unit testi o‘tdi.
- Haqiqiy PostgreSQL 16 da barcha endpointlar uchdan-uchgacha sinaldi: mashq, takror, 3 o‘quvchi imtihoni, reyting, yillik 2 qism, o‘qituvchi ko‘rinishi.
- Frontendning barcha 538 testi o‘tdi. Bitta test (rev155 favicon.png) yiqildi, lekin sababi kod emas: tekshiruv muhitida PNG fayllar yo‘q edi.
- Chromium’da sinaldi: kurs, mavzu, mashq, harfma-harf doska, haftalik imtihon, natija, mavzu oldi bloki, telefon kengligi. Konsol xatosi yo‘q.
- Barcha 674 variantning javob kaliti yechimning oxirgi qadami bilan avtomatik solishtirildi. Mustaqil tekshiruvchi 72 variant va 10 darsni ham chuqur tekshirdi.

## O‘rnatish
1. **Backend:** fayllarni ustiga yozing va serverni qayta ishga tushiring.
2. **Frontend:** fayllarni ustiga yozing va `npm run build` qiling.
3. **Kontentni kengaytirish** (PISA, TIMSS 2007/2003): `tools/xalqaro/` dagi qo‘llanma va tekshiruvchi skriptlar bilan yangi `content/*.json` tayyorlab, `build_data.py` ni ishga tushiring.

---

# REV261 — o‘qituvchi va admin nazorati, «Xatolarim», menyuda alohida bo‘lim

## Kim nimani ko‘radi
- **O‘quvchi** — menyuda alohida **🌍 XALQARO BAHOLASH** bo‘limi bor: kompyuterda yon menyuda o‘z sarlavhasi va «TIMSS · PISA · imtihonlar» izohi bilan, telefonda «Xalqaro» bandi. Bo‘lim ichidagi yangi **❌ Xatolarim** varag‘ida:
  - hozir ham xato bo‘lib turgan har bir savoli: nima deb javob bergani, to‘g‘ri javob, xato sababi, yechish yo‘li va doskadagi yechim;
  - zaif mavzulari;
  - «Xatolar ustida ishlash» tugmasi.
  Savolni mashqda to‘g‘ri yechsa, u ro‘yxatdan chiqadi.
- **O‘qituvchi** (faqat o‘z maktabi) — **👩‍🏫 Sinfim** paneli, bo‘lim ochilganda birinchi chiqadi. Sinf va harf bo‘yicha filtrlanadi:
  - **O‘quvchilar:** holati (faol / sust / boshlamagan), bu haftadagi faolligi, haftalik nazoratni topshirgani, ochiq xatolari soni, oxirgi rasmiy ball va zaif mavzusi;
  - **O‘quvchi tafsiloti** (qatorni bosish bilan ochiladi): mavzular bo‘yicha o‘zlashtirish, har bir xatosi (bergan javobi bilan), imtihonlar tarixi (oynadan chiqishlar ham), takrorlash navbati;
  - **Sinf xatolari:** sinfda eng ko‘p xato qilingan savollar, eng ko‘p berilgan noto‘g‘ri javob va uning sababi, sinfga ko‘rsatish uchun doskadagi yechim;
  - **Mavzular bo‘yicha:** sinf natijasi dunyo o‘rtachasi bilan solishtiriladi (pastdagilari to‘q sariq) va har mavzuga «Dars» tugmasi.
  O‘qituvchi shu bo‘limning o‘zidan kurs, imtihon va darslarni o‘quvchi ko‘zi bilan ham ko‘radi.
- **Admin** — menyuda «Xalqaro baholash» bandi (**Admin nazorati**):
  - platforma jamlamasi: faol o‘quvchilar, javoblar, rasmiy imtihonlar, o‘rtacha ball;
  - istalgan maktab yoki butun platforma bo‘yicha o‘qituvchi panelidagi hamma ma’lumot.
  **«O‘quvchi ko‘zi bilan»** rejimida maktab tanlansa, «📚 O‘rganish / 🌍 Xalqaro baholash» almashtirgichi chiqadi va admin bo‘limni tanlangan sinf o‘quvchisi ko‘rinishida ko‘radi.

## Backend (modules/xalqaro_baholash.py)
- **Yangi endpointlar:**
  - `/api/xalqaro/xatolarim`;
  - `/api/xalqaro/kuzatuv` — rolni aniqlaydi, admin uchun maktablar ro‘yxatini beradi;
  - `/api/xalqaro/sinf_xatolar`;
  - `/api/xalqaro/oquvchi/{id}`.
  `/api/xalqaro/sinf_natija` kengaytirildi.
- **Ruxsat:** admin — `admin_akkaunt` jadvalidagilar; o‘qituvchi va direktor — faqat o‘z `maktab_id` si. O‘quvchi bu endpointlarga kirsa, 403 qaytadi.
- **`xb_bilim` jadvaliga ikki ustun qo‘shildi:** `oxirgi_v` va `oxirgi_javob`. Shu sababli o‘qituvchi o‘quvchi aynan nima deb javob berganini ko‘radi. Imtihon javoblari ham bilim xaritasiga yoziladi. Ustunlar avtomatik qo‘shiladi (`ADD COLUMN IF NOT EXISTS`).

## Frontend
- **Yangi:** `src/xalqaro/XbOqituvchi.jsx` — o‘qituvchi va admin paneli, o‘quvchi tafsiloti va «Xatolarim».
- **O‘zgarganlar:**
  - `XalqaroBaholash.jsx` — panel va «Xatolarim» varag‘i, `rejim="oquvchi"`;
  - `App.jsx` — admin menyusi, menyudagi alohida bo‘lim, sarlavha;
  - `admin/OquvchiKorinishi.jsx` — «Xalqaro baholash» almashtirgichi;
  - `xalqaro.css`;
  - `xalqaro260.test.mjs` — yangi test.

## Tekshiruv
- **Backend:** haqiqiy PostgreSQL bazada sinaldi — o‘quvchi, o‘qituvchi (o‘z maktabi), admin (butun platforma va maktab), o‘quvchiga 403. Unit testlar o‘tdi.
- **Brauzer:** o‘qituvchi paneli, sinf xatolari, o‘quvchi tafsiloti, admin nazorati va o‘quvchining «Xatolarim» varag‘i ochilib ko‘rildi, konsol xatosi yo‘q.
- **Frontend:** 538 + 6 test o‘tdi. `App.jsx` va `OquvchiKorinishi.jsx` yig‘iladi (bundle OK).

---

# REV262 — PISA va «📖 Qo‘llanma»

## Kontent: PISA (15 yosh, 9–10-sinf)
- **4 yo‘nalish:** Matematik savodxonlik (P_M), O‘qish savodxonligi (P_R), Tabiiy-ilmiy savodxonlik (P_S), Moliyaviy savodxonlik (P_F).
- **Manbalar:** PISA «Take the Test» (2000–2006), PISA 2012 va 2022 matematika, PISA 2018 o‘qish, PISA 2015 va 2025 tabiiy fanlar, PISA 2012 va 2018 moliyaviy savodxonlik.
- **TIMSS dagidek, asl matnlar ko‘chirilmagan va tarjima qilinmagan.** Har bir asl birlikka o‘zbek hayotidan yangi birlik yozilgan:
  - birlik tuzilishi: umumiy stimul (matn, jadval, grafik, bir nechta manba) va unga oid savollar;
  - o‘qish birliklari uchun matnlarning o‘zi yangidan yozilgan (Orol, forum, sut haqida ikki fikr, hikoyalar, e’lonlar va boshqalar);
  - har savolda mazmun sohasi, PISA jarayoni, konteksti va **PISA qiyinlik balli** bor. Ball hujjatda bo‘lsa aynan olingan, bo‘lmasa taxmin qilingan va «≈» belgisi bilan ko‘rsatiladi.
- **14 ta yangi Kabu darsi:** miqdor, noaniqlik va ma’lumotlar, o‘zgarish va bog‘lanishlar, fazo va shakl; ma’lumot topish, matnni tushunish, baholash va mulohaza; hodisani ilmiy tushuntirish, tadqiqot rejalash, dalillarni talqin qilish; pul, byudjet, xavf va daromad, moliyaviy muhit.

## Baholash
- **PISA balli:** savol qiyinligi PISA ballida berilgan (62% ehtimollik nuqtasi) va shu Rasch modeliga o‘tkaziladi.
- **Natija darajalari:** shu yo‘nalishning PISA darajalari bilan ko‘rsatiladi (1b … 6). Tayanch 2-daraja alohida belgilanadi.
- **Solishtirish:** PISA 2022 va 2025 davlatlari, O‘zbekiston va OECD o‘rtachasi bilan.
- **Imtihonlar (PISA):**
  - haftalik — 8 savol, 20 daqiqa;
  - oylik — 16 savol, 40 daqiqa;
  - choraklik — 24 savol, 60 daqiqa;
  - yillik — 2 × 60 daqiqa (haqiqiy PISA kabi 2 soat).
  Bitta birlik savollari ketma-ket keladi. Katta ekranda stimul chapda, savol o‘ngda turadi.
- **Tavsiya:** 1–5-sinf → TIMSS 4-sinf, 6–8-sinf → TIMSS 8-sinf, 9–11-sinf → PISA. Barcha to‘plamlar hammaga ochiq.

## Tushunarlilik
- **«📖 Qo‘llanma» varag‘i** bo‘limga birinchi kirishda ochiladi. Sodda til, har bo‘limni ustoz ovoz chiqarib o‘qib bera oladi. Rolga qarab tarkibi:
  - **hammaga:** TIMSS, PISA va PIRLS nima; ballar va darajalar nima degani; savollar qayerdan olingan;
  - **o‘quvchiga:** bo‘limda nima bor, haftalik reja (kuniga 20 daqiqa), xalqaro savolni yechishning 4 qadami, ovoz bilan ishlash;
  - **o‘qituvchiga:** «Sinfim» panelini o‘qish, sinf xatolari bilan dars o‘tish, haftalik va choraklik imtihonni tashkil etish, ota-onalarga tushuntirish;
  - **adminga:** nimalarni ko‘ra olishi.
- **To‘plamlar ikki guruhda:** «TIMSS — 4- va 8-sinf» va «PISA — 15 yosh». Sizga mos to‘plam ⭐ bilan belgilanadi.
- **«Mavzu oldidan» bloki** endi ona tili, adabiyot, huquq va iqtisod darslarida ham chiqadi (PISA o‘qish va moliya mavzulari). PISA mavzulari 7-sinfdan boshlab ko‘rsatiladi.

---

# REV270 — uch til (o‘zbek · rus · ingliz) va o‘qitish metodlari

## Asosiy qoida: tillar aralashmaydi
- **Bo‘lim tili = interfeys tili.** `ru*` — ruscha, `en*` — inglizcha, qolgan hammasi — o‘zbekcha (platformadagi `izohTili` qoidasi bilan bir xil). Interfeys tili almashsa, bo‘lim boshqatdan ochiladi.
- **Kontent har tilda alohida:**
  - savollar, PISA matnlari va jadvallari, rasmlardagi yozuvlar, 64 ta Kabu darsi, mavzu va soha nomlari;
  - davlat nomlari, darajalar, imtihon nomlari, ustoz gaplari.
  - Fayllar: `modules/xalqaro_data/` — o‘zbekcha, `xalqaro_data/ru/` — ruscha, `xalqaro_data/en/` — inglizcha.
- **Natijalar har tilda alohida.** `xb_bilim`, `xb_takror` va `xb_imtihon` jadvallariga `til` ustuni qo‘shildi.
  - Mashq, takrorlash va xatolar ham til bo‘yicha ajratildi: asosiy kalit `(user_id, til, savol_id)`.
  - Har tilda davrning birinchi imtihoni rasmiy hisoblanadi. Reyting, sinfdoshlar va davlatlar bilan solishtirish ham shu tilda.
  - Natija: o‘zbekcha o‘tilgan mavzu ruschada «o‘tilgan» bo‘lib ko‘rinmaydi, ruscha natija inglizchada chiqmaydi.
  - Eski yozuvlarga avtomatik `til='uz'` qo‘yiladi (migratsiya o‘zi bajariladi).
- **Chala tarjima ko‘rsatilmaydi.** Tarjima tilida faqat to‘liq tayyor to‘plam chiqadi: barcha savollari, birliklari va darslari shu tilda bo‘lishi kerak. Chala to‘plam o‘zbekcha bilan aralashtirilmaydi, o‘rniga «tayyorlanmoqda» deb yoziladi.
- **Ovoz va mikrofon tilda.**
  - Ustoz ovozi `[ru]…[/ru]` yoki `[en]…[/en]` tegi bilan beriladi, shunda server shu tilning ovozini tanlaydi.
  - Mikrofon shu tilda tinglaydi: `ru-RU`, `en-US`.
  - Son javoblari shu tilda ham tushuniladi. Ruscha: «три целых пять», «три дробь четыре». Inglizcha: «three point five», «three over four».
- **Dars xonasi.** `XB-…` darsi `til` bilan ochiladi (`dars_payload(code, til=…)`). Shu tilda dars bo‘lmasa, o‘zbekchasi ko‘rsatilmaydi.
- **O‘qituvchi va admin.**
  - Panelda «🌐 Ta’lim tili» tanlovi bor.
  - «Tillar» ustunida har o‘quvchi qaysi tillarda nechta javob bergani ko‘rinadi.
  - O‘quvchi tafsilotida ham shu ma’lumot bor.
  - Admin jamlamasi ham tanlangan til bo‘yicha.
- **O‘quvchi.** Sarlavha ostida «🇷🇺 Русский · bu tilda o‘qiyapsiz…» belgisi turadi, unda boshqa tillardagi javoblar soni ham ko‘rsatiladi.

## Tarjima
- **Hajmi:** taxminan 1,84 mln belgi × 2 til. Javob kalitlari, id lar va tuzilma o‘zgarmaydi. Inglizchada o‘nli kasr nuqta bilan yoziladi.
- **Manba:** `tools/xalqaro/tr/src` — o‘zbekcha satrlar, `tr/ru` va `tr/en` — tarjimalar.
- **Vositalar:**
  - `tools/xalqaro/tarjima.py` — `extract`, `check` (formulalar, `[n]` belgilar, qatorlar, o‘zbekcha qolmaganini tekshiradi) va `merge`.
  - Qo‘llanma: `SPEC_TARJIMA.md`.
- **Yig‘ish:** `python3 tools/xalqaro/build_data.py --til ru` (yoki `--til en`).
- **Testlar:** `tests/test_xalqaro_rev260.py::Tillar` — tuzilma va javob kalitlari uchala tilda bir xil, son javoblar har tilda qabul qilinadi, darajalar va davlat nomlari tilda.

## «🎓 O‘qitish metodlari» (o‘qituvchi va admin uchun)
- 10 ta usul. Har birida: nima, nega ishlaydi (dalil), sinfda qanday qilinadi (4 qadam), platformada qanday ishlatiladi va manba havolasi.
- Manbalar ochiq e’lon qilingan ekspert ishlari:
  - Rosenshine, «Principles of Instruction» (2012);
  - Dunlosky va boshq. (2013);
  - Black & Wiliam, «Inside the Black Box»;
  - EEF tavsiyalari (metakognitsiya, matematika, savodxonlik, fikr-mulohaza);
  - OECD PISA hisobotlari («Ten Questions for Mathematics Teachers», «21st-Century Readers», «Sky’s the limit»);
  - IEA TIMSS 2023.
- O‘qituvchining haftalik tartibi ham berilgan.
- Qo‘llanmaga «🌐 Uch tilda o‘qish» bo‘limi qo‘shildi.

## Foydalanuvchi qarorlari saqlandi (REV274)
- Admin menyusida «Xalqaro baholash» oddiy band bo‘lib qoldi.
- Maktab mavzusi oldidagi xalqaro blok o‘chiq turadi.
