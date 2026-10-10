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
