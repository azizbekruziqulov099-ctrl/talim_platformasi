# Kabutar: shaxsiy jadval va AI yordamchi — REV42

Bu yangilanish o‘quvchining haftalik jadvali, o‘qituvchining shaxsiy rejasi va bazadagi testlar bilan ishlaydigan yordamchini qo‘shadi. Kodlar ikkita alohida arxivda: frontend va backend. Telegram botiga ushbu yangilanish uchun o‘zgartirish kerak emas.

## Jadval qanday ishlaydi?

- Butun hafta bir qatorda. Tor ekranda hafta yon tomonga suriladi; kunlar pastga ikkinchi qator bo‘lib tushmaydi.
- Fanlar va haftalik soatlar adminning faol maktab andozasidan, o‘quvchining sinfi va ta’lim tiliga qarab olinadi. Shaxsiy jadval maktab jadvali tasdiqlanishini kutmaydi.
- Soatlar kunlarga tengroq taqsimlanadi. Masalan, 22 soat va 5 kun uchun cheklovlar imkon bersa `4–5–4–5–4`; 27 soat uchun `5–6–5–6–5` chiqadi. Admin belgilagan metod kuni, kunlik maksimum va smena vaqtlari hisobga olinadi.
- Andozada Kelajak soati bo‘lsa, dushanba birinchi darsga qo‘yiladi. Andozaga kiritilmagan qo‘shimcha soat yashirincha qo‘shilmaydi.
- `0.5` va `1.5` soatli fanlarning qoldig‘i ikki haftaga navbat bilan joylanadi. Ikki haftalik jami soat yo‘qolmaydi.
- Admin kalendaridagi choraklar, ta’tillar va maxsus kunlar hisobga olinadi. Kalendar yo‘q bo‘lsa, haftalik fan-soatlar chiqadi va kalendar yetishmayotgani ko‘rsatiladi; sanali mavzu o‘ylab topilmaydi.
- Mavzular shu sinf, fan va chorakdagi DTS yozuvlaridan olinadi. Bo‘sh qolgan darslarga shu haqiqiy mavzularni takrorlash, chorak oxirida shaxsiy nazorat taklifi qo‘yiladi.
- «Chet tili» kabi umumiy nomda qaysi til ekani noma’lum bo‘lsa, DTSdagi mavjud tillardan o‘zingiz tanlaysiz.
- «Jadvalni moslash» orqali darslarni ko‘chirish/almashtirish, mavzu va mashg‘ulot turini tanlash mumkin. «Saqlash» server muvaffaqiyatli javob berganidan keyingina tasdiqlanadi. Fanlarning jami soati saqlanadi.
- O‘zgartirish foydalanuvchi, maktab, sinf, til va hafta bo‘yicha shaxsiy saqlanadi. O‘qituvchi o‘z rejasini sozlaydi; maktabning rasmiy jadvali o‘zgarmaydi. Ota-ona bog‘langan farzandining rejasini ko‘radi.

## Yordamchining ishlash tartibi

Tepadagi **Ta’lim maydoni — AI yordamchi — Kabutar** qatoridan robot tugmasini bosing. Oyna yopilganda ortiqcha ovoz va animatsiya ishlamaydi. Boshlangan imtihonning vaqti davom etadi.

| Qadam | Nima qiladi? |
|---|---|
| So‘rovni tushunish | Sinf, chorak, mavzular, savollar soni, qiyinlik va vaqtni ajratadi. Noaniq so‘rovga aniqlik kiritishni so‘raydi. |
| Bazadan topish | Faol DTS mavzularini va ulardagi haqiqiy savollar sonini tekshiradi. O‘xshash nomlarni tanlash uchun ko‘rsatadi. |
| Reja | Bir nechta mavzu, 10–100 savol, qiyinlik, 5–180 daqiqa, mashq/imtihon va fan bo‘yicha ball tanlanadi. |
| Tasdiq | Mavzular va barcha shartlar ko‘rsatiladi. Reja o‘zgarsa, oldingi tasdiq yaroqsiz bo‘ladi. |
| Test | Faqat bazadagi savollar takrorlanmasdan tanlanadi. Savol yetmasa, sonni yoki tanlovni o‘zgartirish so‘raladi. |
| Natija | Javoblar serverda tekshiriladi. Imtihon muddati server tomonidan ham nazorat qilinadi. Natija va tushuntirish yakunda ochiladi. |
| Eksport | Word yoki Excel savollar varag‘i; ruxsati bor o‘qituvchi/admin uchun alohida javoblar kaliti. |

Misol: «7-sinf, algebra, 2 ta mavzudan 20 ta o‘rtacha savol, 30 daqiqalik imtihon». Yordamchi taklif qilgan aniq mavzularni belgilang, ball va vaqtni tekshiring, keyin tasdiqlang.

Karnay tugmasi yordamchi yozgan matnni o‘qiydi. Bir xabar ikki marta o‘z-o‘zidan boshlanmaydi; ovoz tayyor bo‘lmasa xabar chiqadi. O‘zbekcha matn uchun tasodifiy ruscha ovoz tanlanmaydi.

Javoblar serverga avtomatik saqlanadi. Sahifa qayta ochilganda egasi tasdiqlangan tugallanmagan urinish tiklanadi. Bu shaxsiy mashq/imtihon natijalari alohida jadvalda saqlanadi; rasmiy maktab monitoringi yoki o‘yin ochkolari avtomatik o‘zgartirilmaydi.

## AI ulanishi

Backenddagi `GROQ_API_KEY` mavjud bo‘lsa, erkin matnni tushunish uchun model ishlatiladi. Kalit frontendga yozilmaydi. Modelni `KABUTAR_ASSISTANT_MODEL` orqali almashtirish mumkin; boshlang‘ich qiymat `openai/gpt-oss-20b`. Ushbu modelning JSON chiqishi [Groq rasmiy hujjatida](https://console.groq.com/docs/structured-outputs) ko‘rsatilgan.

Kalit bo‘lmasa yoki provayder javob bermasa, bazadan izlash va shakl orqali reja tuzish ishlaydi. Bu rejim erkin suhbatdagi barcha imlo xatolarini tushunadi degan kafolat bermaydi. Model bergan natija ham serverdagi sinf, mavzu, son va ruxsat tekshiruvidan o‘tadi; model SQL yozmaydi va javoblar kalitini olmaydi.

Hozirgi bosqich — katalog, test va imtihon. Kitobdan dars o‘tish keyingi alohida bosqich.

## Bitta yuklashda yangilash

Arxivlar har loyiha uchun to‘liq manba fayllarini o‘z papka tuzilishi bilan beradi. Eski loyihangizning nusxasini saqlab oling.

1. `BACKEND_JADVAL_AI_REV42.zip`ni oching. Ichidagi `main.py`, `samtm_platform.py`, `modules` va boshqa fayl/papkalarni **backend GitHub loyihasining ildiziga**, mavjudlarini almashtirib yuklang. Tashqi ZIP papkasini qo‘shimcha ichki papka qilib yuklamang. Commit qiling.
2. Backend ishga tushgach, `FRONTEND_JADVAL_AI_REV42.zip`ni oching. Ichidagi `src`, `public`, `package.json` va qolgan fayllarni **frontend GitHub loyihasining ildiziga**, papka tuzilishini saqlab yuklang. Commit qiling.
3. Railway backend va frontend deploylarini tekshiring. Backendda mavjud `DATABASE_URL`, `JWT_MAXFIY_KALIT`, domen va CORS sozlamalari saqlanadi. Frontend build buyrug‘i: `npm run build`.
4. Saytni yangilang. O‘quvchi hisobida hafta, o‘qituvchi hisobida shaxsiy reja va tepadagi robot tugmasini tekshiring.

Yordamchining yangi bazaviy jadvallari backend ishga tushganda yaratiladi. Shaxsiy jadval jadvali birinchi so‘rovda yaratiladi. Eski foydalanuvchilar va mavjud jadval yozuvlari o‘chirib tashlanmaydi.

## Tekshiruv va amaliy chegaralar

Tekshirildi: Python sintaksisi; frontenddagi lokal import/eksport va rasm yo‘llari; aniq soat taqsimoti; dushanba birinchi dars; ikki haftalik yarim soatlar; DTS sinf/fan tekshiruvi; foydalanuvchi/maktab bo‘yicha ajratish; bir vaqtda o‘zgargan jadval uchun versiya tekshiruvi; muvaffaqiyatsiz saqlash; eskirgan so‘rovlar; tasdiqsiz test yaratishni rad etish; server baholashi; muddat; eksport fayllarining ochilishi va kalitlarning ajratilishi.

Bu muhitda haqiqiy Vite build, brauzerda ko‘rinish, Railway PostgreSQL, AI provayderi va ovoz xizmatiga jonli ulanish tekshirilmagan. Railwaydagi build va hisoblar bilan amaliy tekshiruv zarur. Millionlab bir vaqtdagi foydalanuvchi uchun yuklama sinovi o‘tkazilmagan.

Eksport bazada saqlangan xavfsiz rasm baytlarini qo‘shadi. Faqat tashqi havolada turgan rasmni o‘zboshimchalik bilan yuklamaydi; bunday savolda aniq xabar beradi. Formulalar matn/LaTeX ko‘rinishida saqlanadi, Wordning tahrirlanadigan formulalariga avtomatik aylantirilmaydi.
