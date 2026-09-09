# Kabutar ID, nik va telefon orqali topish

Yangi backend fayli: `kabutar_discovery.py`. `main.py` oxirida modul ulangan.
Qo'shimcha tashqi xizmat yoki pulli SMS kerak emas.

## Profil sozlamasi

`GET /auth/profile/discovery` va `POST /auth/profile/discovery` uchun `Authorization: Bearer <sessiya>` talab qilinadi.
POST tanasi: `{"nickname":"aziz_ustoz","phone_discoverable":false}`.
Nikni o'chirish: `nickname: null`.

Javob: `nickname`, `phone_discoverable`, `phone_verified`, `phone_masked`.
To'liq telefon hatto ushbu javobda ham chiqmaydi.
Nik 5–32 belgili: birinchi belgi lotin harfi; qolganlari lotin harfi, raqam, pastki chiziq.
Niklar kichik harfda saqlanadi va butun platformada takrorlanmaydi.
Nik o'zgarsa ham KB raqami va barcha mavjud ma'lumotlar o'zgarmaydi.

Telefon orqali topish avvaldan o'chirilgan. Uni yoqish uchun Telegram orqali o'z telefonini tasdiqlash kerak.
Eski `telefon_hisob` jadvalidagi yozuvning o'zi tasdiqlangan telefon hisoblanmaydi.
Sozlamani o'chirish bilan keyingi telefon qidiruvlari yopiladi; oldin berilgan kartochka yoki suhbat avtomatik o'chirilmaydi.

## Aniq qidiruv

`GET /api/kabutar/find?query=...` uchun ham Bearer sarlavhasi kerak.
Qidiruv tugmasi bosilganda bitta aniq qiymat yuboriladi:

- `KB-12345678` yoki 6–10 xonali KB raqami;
- `@aziz_ustoz`;
- `+998901234567` — faqat tasdiqlangan telefon va egasining roziligi bo'lsa.

Telefon query qiymatidagi `+` URLda `%2B` qilib kodlanadi (`encodeURIComponent`).
Telefon qismini yozish, ism bo'yicha umumiy qidiruv va ommaviy ro'yxat olish qo'shilmagan.
Qidiruv so'rovlari foydalanuvchiga daqiqasiga 30 ta va IPga 120 ta bilan cheklangan.
Server/proksi access-loglarida telefonli query satrlarini yozmaslik yoki niqoblash kerak.

Natija mavjud Kabutar kartochkasiga mos: `user_id`, `full_name`, `kabutar_id`, `kabutar_nickname`, `rasm_bormi`, `rollar`, `qisqa`.
Natijada telefon, Telegram IDsi, bola/farzandning ma'lumotlari yoki ma'muriy huquqlar berilmaydi.
Google orqali yaratilgan manfiy ichki user IDlari ham qo'llab-quvvatlanadi.

Qidiruvning o'zi muassasa a'zoligi, yozish yoki faylni o'qish ruxsatlarini o'zgartirmaydi.
Birinchi xabar uchun mavjud aniq KB raqami qoidasi, keyingi xabarlar uchun mavjud suhbat qoidalari saqlanadi.

## Tekshiruv

`python -m unittest discover -s tests -p 'test_kabutar_discovery_rev31.py' -v`

12 mahalliy test: format, nik to'qnashuvi, manfiy ID, maxfiy/yo'q/tasdiqlanmagan telefonning bir xil javobi,
rozilikni yoqish-o'chirish, telefonni maskalash, Bearer talabi, admin ko'rish rejimidagi o'zgarish bloklanishi.
Testlar jonli PostgreSQL va haqiqiy foydalanuvchilar bilan bajarilgan yuklama sinovi emas.
