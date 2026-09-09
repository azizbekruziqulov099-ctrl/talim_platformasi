# Kabutar kirishi — REV31

## O‘zgargan fayllar

- `kabutar_auth.py` — yangi autentifikatsiya moduli.
- `main.py` — autentifikatsiya va tashrif statistikasini ulaydi.
- `samtm_platform.py` — mavjud JWT, Google, ro‘yxatdan o‘tish va profil bilan moslashtirildi. Maktab/institut import qilgan yordamchi funksiyalar ham sessiyani tekshiradi.
- `tests/test_kabutar_auth_rev31.py` — ajratilgan regressiya tekshiruvlari.

Joriy PostgreSQL bazasining zaxirasini olib, avval sinov xizmatida ishga tushiring. Autentifikatsiya jadvallari va indekslar backend ishga tushganda qo‘shiladi. Eski foydalanuvchilar, KB raqamlari, suhbatlar va muassasa bog‘lanishlari ko‘chirilmaydi/o‘chirilmaydi.

## Backend muhit sozlamalari

- `KABUTAR_BOT_USERNAME`: botning foydalanuvchi nomi, `@`siz.
- `KABUTAR_BOT_AUTH_SECRET`: kamida 32 belgili kuchli tasodifiy sir; bot va backendda aynan bir xil. Frontendga berilmaydi. Telegram bot tokenining o‘zi emas.
- `JWT_MAXFIY_KALIT`: mavjud kamida 32 baytli sir; o‘zgartirmang, aks holda eski sessiyalar tugaydi.
- `BAZA_URL`: backendning tashqi HTTPS manzili. Google callback shu manzilga `/auth/google/callback` qo‘shiladi.
- `FRONTEND_URL`: `https://talimkabutar.uz` — Google qaytishi va bot tasdiqlashida ko‘rsatiladigan sayt.
- `FRONTEND_URLS`: ruxsat etilgan frontend manzillari vergul bilan. Kamida `https://talimkabutar.uz,https://www.talimkabutar.uz`. Zarur bo‘lsa amaldagi Railway frontend manzilini ham qo‘shing.
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: mavjud Google OAuth sozlamalari.
- `KABUTAR_TRUST_PROXY_HEADERS=true` faqat tashqi `X-Forwarded-For` sarlavhasini ishonchli proxy almashtirishi kafolatlanganda. Odatiy qiymat — o‘chiq.

Google Console ichidagi Authorized redirect URI backendning `BAZA_URL/auth/google/callback` manziliga aynan mos bo‘lsin. Vite `preview.allowedHosts` ichida yangi domenlar bo‘lishi kerak.

SMS/Eskiz/WhatsApp xarajati yoqilmadi. Eski xavfli `/api/auth/telefon_kod_sorash`, `/telefon_kod_tasdiqla`, `/telefon_royxat` endpointlari `410` qaytaradi va xabar yubormaydi. Eski `/auth/ulash` va `/auth/sayt_kod_yarat` orqali foydalanuvchi IDlarini ko‘chirish/ulash ham yopildi; profilning yangi Telegram/Google ulash oynasi ishlatiladi. Eski xodim kirish kodi shu `/auth/ulash`ga yuborilsa `410` bo‘ladi. Uning o‘rniga yangi `/auth/invite/claim` faqat muassasa bergan kamida 12 belgili, bir martalik taklifni va tasdiqlangan Google grantini qabul qiladi. 2 oylik muddati tugamagan, hali boshqa kirish usuliga/sessiyaga ulanmagan import xodim profiliga kiriladi; mavjud akkaunt IDlari ko‘chirilmaydi.

## Kirish va qayta kirish

Telegram so‘rovi 5 daqiqa yashaydi. Telegramga brauzer siri yuborilmaydi. Bot shaxsiy suhbatda yuboruvchining O‘Z kontaktini tekshiradi; `/confirm` maxsus server siri bilan himoyalangan. Botdagi joriy virtual profil ishlatilmaydi. Tasdiq kodi saytdagi bilan solishtiriladi. Bir martalik tasdiqlash bitta sessiya yaratadi; javob tarmoqda yo‘qolsa aynan shu brauzer 2 daqiqa davomida aynan o‘sha natijani qayta oladi.

Sessiya 30 kun. Sahifa yopilishi logout emas. `/auth/logout` shu qurilma sessiyasini bekor qiladi; `{all_devices:true}` barcha sessiyalar va hali ishlatilmagan eski tokenlarni ham bekor qiladi. Akkaunt ulash uchun oxirgi 10 daqiqada qayta kirilgan bo‘lishi kerak. Boshlangan ulash jarayonida sessiya bekor qilinsa, ulash davom etmaydi. Parol o‘zgarsa boshqa sessiyalar va tugallanmagan ulash so‘rovlari bekor qilinadi.

Parol kamida 10 belgi, scrypt va har foydalanuvchi uchun alohida salt bilan saqlanadi. Hozirgi parolni bilmasdan tiklash uchun so‘nggi 10 daqiqada Google yoki Telegram orqali kirish, so‘ng `reset:true` bilan parol qo‘yish kerak. Parol bilan kirishning o‘zi parolni bilmasdan tiklash vakolatini bermaydi.

Yangi Google foydalanuvchisi uchun rolni tanlash majburiy emas: `kabutar` umumiy akkaunti yaratiladi. Ta’lim bo‘limiga kirganda rol/sinf/til tanlanadi. Mavjud ta’lim roli saqlanadi; muassasa vakolatini foydalanuvchi o‘zi qo‘shib ololmaydi.

Google hisobi ulash uchun `/auth/google/login?intent=link` ishlatiladi. Bu maqsad imzolangan OAuth state va qaytish natijasida saqlanadi. Oldindan kirilgan Kabutar tokeni va yangi Google tasdiq grantini `/auth/google/link` bilan birga yuborish kerak. Boshqa Kabutar akkauntiga tegishli email yoki telefon `409` qaytaradi. Ism/telefon o‘xshashligi asosida akkauntlar birlashtirilmaydi.

## Tekshiruv chegarasi

Ajratilgan regressiya testlari: browser siri, haqiqiy kontakt, eskirish, bekor qilish, virtual profil, akkaunt/telefon to‘qnashuvi, qayta yuborish, sessiyani bekor qilish, eski tokenning qayta yaralmasligi, Google chipta/sessiya ajratilishi, parol hash.

Testlar haqiqiy PostgreSQL o‘rnida tranzaksiyali sinov kursoridan foydalanadi. Bu muhitda FastAPI/psycopg2/python-jose paketlarini o‘rnatish imkoni bo‘lmadi. Shu sabab haqiqiy server, real PostgreSQL blokirovkalari, Google callback va botdan telefon yuborish aylanishi hali sinov xizmatida tekshirilishi kerak. Millionlab bir vaqtdagi foydalanuvchilar uchun yuklama kafolati berilmaydi; auth sessiya tekshiruvi indeksli DB so‘rovidan foydalanadi va bitta HTTP so‘rovi ichidagi takroriy tekshiruvlar keshlanadi.
