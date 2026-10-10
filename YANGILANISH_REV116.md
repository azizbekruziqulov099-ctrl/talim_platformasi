# Bog'cha — umumlashgan yangilanish (REV110 → REV116)

Bu ikkala loyiha (backend + frontend) uchun bitta umumiy ro'yxat. Hozirgi kodingiz ustiga to'liq qo'yiladi
(sizdagi kod mening boshlang'ich nusxam bilan bir xil — ziddiyat yo'q).

## Frontend (talim_platformasi_frontend-main)
Yangi fayllar:
- src/kid/BogchaOlami.jsx, olam.css, olamRules.js — «Bog'cha olami»: bino → yo'lak → sinfxonalar, zal, sport maydoni, hayvonot bog'i, hovli. Haqiqiy ob-havo va kun vaqti (kechasi qorong'i).
- src/kid/UstozSahna.jsx, ustozSahna.css, ustozlar.js, ustozRules.js — jonli ustozlar (Sardor aka — matematika, Nilufar opa — til, Malika opa — atrof-olam). Ustoz polda turadi, ko'z pirpiratadi, gapiradi; xona mavzuga qarab o'zgaradi; derazada ob-havo.
- src/kid/darsOchilishi.js, ochilishLugat.js — dars boshi: ustoz o'z uslubida salomlashadi, bugungi ob-havoni aytadi, o'tgan darsdan so'raydi (10 tilda).
- src/kid/suhbat.js — ustoz bilan suhbat: faqat bola bilgan so'zlardan, yoshga qarab murakkablashadi, javobni tahlil qiladi.
- src/kid/sozBoyligi.js — bola o'rgangan so'zlarni eslab qoladi.
- src/kid/izohTil.js — izoh tili (o'zbek / rus / ingliz) avtomatik aniqlanadi.
- src/kid/useHavo.js — ob-havo (server orqali, 30 daqiqa kesh).
- src/speech/childRecorder.js — xato bo'lsa bolaga o'z ovozini eshittirish (faqat qurilmada, serverga yuborilmaydi).
- src/kid/ustoz/**, src/kid/olam/** — ustoz va xona rasmlari (webp, 960/1600).
- Testlar: ustoz110, darsOchilishi110, suhbat110, voiceCoach110, izoh111, olam112.

O'zgargan fayllar: src/lesson/DarsXonasi.jsx, VoiceCheck.jsx, voiceCheckRules.js, kidLessonRules.js, dars-xonasi.css,
src/kid/kidStageRules.js, src/curriculum/LearnerTopics.jsx, kidTopics.css.

## Backend (talim_platformasi-main)
- modules/tez_kesh.py (yangi) — xotira keshi: 100 ming bola birdan kirsa ham DB va tashqi API bosilmaydi.
- modules/dars_xonasi.py — dars va rasm keshi (ETag/304, 1 yillik brauzer keshi), /api/bogcha/havo (14 shahar, 30 daqiqa kesh).
- TEZLIK_REV110.md — Cloudflare kesh qoidalari.
- tools/bogcha_*.py — miya generatori: 2-3 yosh 50 dars, 4-5 yosh 80 dars, 6-7 yosh 100 dars; 10 til; izoh tili uz/ru/en (90 miya);
  chet so'zlar doim o'z til tegida ([en]…[/en]) — test va bellashuvda ham to'g'ri ovozda o'qiladi.
- tools/bogcha_content/** — 10 til × 3 yosh kitoblari, tarjimalar, izoh lug'atlari.
- tools/bogcha_rasmlar/svg, png_preview — 179 ta yangi jonli rasm (1–197; bo'laklarga ajratilgan harakat).
- Testlar: test_tez_kesh_rev110, test_bogcha_plus_rev110, test_bogcha_teg_rev111, test_bogcha_rasm_rev113.

## Tekshiruv
- Backend: barcha o'zgargan modullar kompilyatsiya qilinadi, bog'cha testlari o'tdi; izoh lug'atlari ru/en — 0 muammo.
- Frontend: 251 test o'tdi; 24 ta yiqilgan test sizning hozirgi kodingizda ham xuddi shunday yiqiladi (yangi xato yo'q). App, DarsXonasi, LearnerTopics, BogchaOlami yig'iladi (bundle OK).

## O'rnatish
1. Backend: zipni oching, eski papka ustiga yozing (ikki qism: _kod va _rasmlar — bitta papkaga). Server qayta ishga tushirilsin. DB o'zgarmaydi (migratsiya kerak emas).
2. Frontend: zipni ustiga yozing, `npm run build`.
3. Miyalar — rasmlar tugagach alohida yig'iladi va yuklanadi.

## REV119 (rasmlar va miyalar)
- tools/bogcha_rasmlar/svg — manifestdagi 429 ta rasmning hammasi jonli (2-avlod: butun rasm 1,8 s harakat, kesilmaydi, ma'noga mos effektlar),
  + yangi darslar uchun ma'nosi aynan bir xil bo'lgan 48 ta rasm (teng_rasmlar.json). Sonli rasmlar soni tekshirilgan (5,6,7,8,9,10).
- Rasm ichidagi yozuvlar (rahmat, look, lets play, well done, olti/yetti yosh, Good Morning, payshanba) olib tashlangan — 10 tilda to'g'ri.
- 90 ta miya (10 til × 3 yosh × izoh uz/ru/en) qayta yig'ildi: 2-3 yosh 50, 4-5 yosh 80, 6-7 yosh 100 dars.
- tests/test_bogcha_rasm_rev113.py — 429 rasm: bor, xavfsiz, <160 KB, cheksiz animatsiya yo'q.

## REV121 — doska, deraza, chiroq, haqiqiy o'yin, yulduz, qavatlar, yangi miyalar

**Dars xonasi (frontend)**
- **Doska.** Rasm yoki emoji chiqqanda doska yaqinlashadi: sahnaning o'ng qismini egallaydi, ustoz chapda qoladi. Rasmlar oq kartochkalarda katta chiqadi, telefonda ham aniq ko'rinadi.
  - Rasmi yo'q darslarda (matematika, atrof-muhit, mantiq) doskaga emojilar chiqadi va sanog'i saqlanadi: «🍎🍎🍎» — uchta olma.
  - Doska kechqurun ham qorong'ilashmaydi.
- **Deraza.** Faqat shisha bo'laklari ichida (rom, bayroqcha va gul ustiga emas) jonli osmon chiziladi:
  - kunduzi — quyosh nurlari aylanadi, bulutlar suzadi;
  - ertalab — pushti osmon;
  - kechqurun — quyosh botadi;
  - kechasi — oy va yulduzlar miltillaydi;
  - bulut, yomg'ir, qor va momaqaldiroq (chaqmoq) ham alohida ko'rinadi.
- **Chiroq.** Kechqurun va kechasi shiftdagi chiroq yonadi va xona yoritiladi.
- **Kechki gaplar.** Ustoz kechasi «quyosh charaqlayapti» demaydi. Uning o'rniga «Xayrli kech», «oy va yulduzlar» va «chiroqni yoqdik» deydi. Bu iboralar 10 tilda va 3 izoh tilida bor.
- **«Top-chi» o'yini endi haqiqiy o'yin:**
  - ustoz so'zni aytadi va bola bosishini kutadi;
  - birinchi urinishda to'g'ri bossa — ⭐;
  - xato bossa — «Yana qidir!» deyiladi, lekin yulduz berilmaydi;
  - bosmasa — ustoz qayta so'raydi, keyin to'g'ri rasmni ko'rsatadi, yulduz berilmaydi.
  - O'yindan tashqarida rasmni bossa, maqtov aytilmaydi — faqat rasmning nomi aytiladi.
- **Yulduz.** Test va o'yin birga hisoblanadi: 80% va undan yuqori — 3 ⭐; 50% va undan yuqori — 2 ⭐; bittasi to'g'ri — 1 ⭐; hech biri to'g'ri bo'lmasa — 0 ⭐ (dars baribir «o'tildi» bo'ladi).
  - Serverdagi `stars_for` ham shunday hisoblaydi.
- **Test.** Bog'cha testida savoldagi rasmlar (naqsh, sanoq, ortiqchasi) katta kartochkada ko'rsatiladi.
- **Izoh tili.** Matematika, atrof-muhit va mantiq rus yoki ingliz izohida ham til darsi deb hisoblanmaydi:
  - maqtov, «o'ynaymiz», natija va ovozli tekshiruv izoh tilida aytiladi;
  - fan emojisi to'g'ri chiqadi («Arab tili (izoh: rus)» → 🇸🇦).
- **Ustoz.** Mantiq darsini Sardor aka o'tadi.
- **Yo'lak.** Har qavatda 4 ta eshik bor. 5-fandan boshlab 2-qavat, 9-fandan 3-qavat ochiladi va qavatlar orasida 🪜 zinapoyadan o'tiladi.

**Miyalar (backend tools)**
- **Mantiq.** Yangi fan, `tools/bogcha_mantiq.py`. Har yoshda 5 xil mantiqiy o'yin bor:
  - 2-3 yosh — 20 dars;
  - 4-5 yosh — 25 dars;
  - 6-7 yosh — 30 dars.
  - Matnlar uch tilda yoziladi; rus va ingliz tarjimasi lug'atga o'zi tushadi.
- **Atrof-muhit va Matematika.** `tools/bogcha_fanlar.py` ularni 3 yosh guruhiga yig'adi, «sen» va robot Kabu uslubida:
  - Atrof-muhit: 42 / 43 / 64 dars;
  - Matematika: 39 / 41 / 64 dars.
  - 7 247 ta yangi matn rus va ingliz tiliga tarjima qilindi (`izoh/ru.json`, `izoh/en.json`).
- **4-5 yosh til darslari.** 3-pog'onaga o'tdi: gaplar chet tilida aytiladi, ma'nosi qavs ichida beriladi. Chet tili ulushi bosqichlari:
  - 2-3 yosh — ~11%;
  - 4-5 yosh — ~58% (oldin 27% edi);
  - 6-7 yosh — ~88%.
- **Amaliy qadam kirish so'zi.** `ai_miya_varoq` endi kitob tilida yozadi: rus izohli miyada «Endi amaliy topshiriq» emas, «Теперь практическое задание» bo'ladi.
- **Yig'ish.** `python tools/bogcha_izoh.py build <uz|ru|en> --out PAPKA --rasmlar tools/bogcha_rasmlar/svg` — 13 fan × 3 yosh. `tozala` buyrug'i eskirgan tarjimalarni olib tashlaydi.

### REV121 (davomi) — ommaviy paket: mavzular va miyalar bitta yuklashda
- **Qayerda:** Admin → Kitob darslari (AI miya) → «⚡ Paketni birdan o'rnatish».
- **Nimani tanlash mumkin:** bitta ZIP (papkalari bilan) yoki bir nechta Excel.
- **Server o'zi qiladi:**
  - har faylni ichidan taniydi: Mavzular («Fan» va «Mavzu» ustunlari) yoki miya (KITOB varag'i);
  - rasmlar ro'yxatini o'tkazib yuboradi;
  - avval hamma mavzularni o'rnatadi, keyin har miyani tekshiradi, import va nashr qiladi.
- **Natija:** har fayl aniq nom bilan ✅ / ❌ ko'rinadi, masalan «Ingliz tili · izoh rus · 4-5 yosh · miya». Xato chiqqan faylni qayta urinish mumkin.
- **Yangi API:**
  - `POST /api/admin/paket/yukla` — ZIP navbatga qo'yiladi yoki Excel darhol o'rnatiladi;
  - `POST /api/admin/paket/fayl/{id}` — paketdagi bitta faylni o'rnatadi.
- **Vaqtinchalik saqlash:** `ai_brain_paket_fayllar` jadvali; fayllar 3 kundan keyin o'chiriladi.
- **Cheklovlar:** ZIP 400 MB gacha, 400 tagacha Excel.
- **Mavzular qayerga yoziladi:** yuqorida tanlangan dasturga, masalan «Bog'cha — umumiy katalog».

### REV121 (davomi) — sayt 3 tilda, tungi rejim
- **Tillar.** Sozlamalarda faqat 3 til qoldi: O'zbekcha, Русский, English.
  - Interfeysdagi hamma matnlar (10 600 dan ortiq) rus va ingliz tiliga oldindan tarjima qilindi: `src/interface/locales/ru.js`, `en.js`.
  - Har bir til paketi faqat o'sha til tanlanganda yuklanadi. Tarjima uchun tarmoq (Google) kerak emas.
- **Til almashtirish.** Avval til paketi yuklanadi, keyin ilova qayta chiziladi.
  - Har bir yozuv, jumladan o'zbekchaga qaytganda ham, darhol yangi tilda chiqadi.
  - Eski tanlov (kirill, turk, qozoq) saqlangan bo'lsa, o'zbekchaga qaytadi.
- **Tungi rejim.** Butun sahifaga bitta qoida qo'llanadi: ranglar teskari qilinadi, rasm, video va xaritalar asl rangida qoladi.
  - «To'q fonda to'q yozuv» endi hech qayerda bo'lmaydi; eski qisman qoidalar o'chirildi.
  - Bolalar sahifalari (bog'cha darsi, bog'cha olami, darslar ro'yxati) tungi rejimda ham yorqin qoladi.

### REV121 (davomi) — paketda miyalar ham o'tadi
- **Nega miyalar o'tmagan edi.** Rus va ingliz izohli miyalarning topshiriq kodlari o'zbekchasi bilan bir xil edi (EN23-01-A01 …). Shu sababli ular «kod band» xatosi bilan to'xtagan.
  - Endi har izoh tilining o'z prefiksi bor: o'zbekcha — EN23 (o'zgarmadi), ruscha — EN23R, inglizcha — EN23E.
  - Rus va ingliz izohli miyalar qayta yig'ildi.
- **Qayta yuklashda nima bo'ladi:**
  - aynan shu Excel avval nashr qilingan bo'lsa — «oldin o'rnatilgan» deb bir zumda o'tkaziladi;
  - o'zgargan bo'lsa — o'sha kitob yangi versiyaga yangilanadi;
  - mavzular «oldin bor» deb qayta yaratilmaydi.
- **Paket hajmi:** bitta paketda 400 tagacha Excel bo'lishi mumkin.
