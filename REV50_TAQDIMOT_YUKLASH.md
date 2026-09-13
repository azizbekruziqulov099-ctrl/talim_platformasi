# Kabutar taqdimotlari — REV50 yangilanishi

Bu paket avval o‘rnatilgan REV49 taqdimot bo‘limi uchun. Ichida faqat o‘zgargan va yangi fayllar bor. To‘liq sayt nusxasi emas.

## Qanday yangilanadi?

1. Avval `BACKEND_TAQDIMOT_REV50.zip` arxivini oching. Ichidagi `modules` papkasini backend repozitoriysining asosiy joyiga nusxalang; bir xil nomli fayllarni almashtiring. Yangi `modules/presentation_docx.py` fayli ham yuklangan bo‘lsin.
2. Keyin `FRONTEND_TAQDIMOT_REV50.zip` arxivini oching. Ichidagi `src` papkasini frontend repozitoriysining asosiy joyiga nusxalang; bir xil nomli fayllarni almashtiring. Yangi `src/presentations/layouts.js` va `src/presentations/PresentationUI.jsx` fayllari ham yuklangan bo‘lsin.
3. Har bir repozitoriyda o‘zgarishlarni commit/push qiling va Railway yangilanishi tugashini kuting. Frontend deployida `npm run build` muvaffaqiyatli tugashi kerak.
4. Saytni yangilab, Taqdimot yaratish bo‘limini oching. Eski sahifa ochiq turgan bo‘lsa, `Ctrl+Shift+R` bosing.

Papka tuzilishini saqlang. Masalan, `PresentationUI.jsx` faylini `src`ning o‘ziga emas, `src/presentations` ichiga joylang. GitHub Desktop orqali repozitoriyning mahalliy papkasiga nusxalash barcha ichki papkalarni saqlaydi. GitHubdagi yuklash oynasida esa arxivning o‘zini emas, ochilgan `src` yoki `modules` papkasini tortib tashlang va commitdan oldin fayl yo‘llarini tekshiring.

`KABUTAR_TAQDIMOT_REV50.zip` ikkala paketni birga saqlaydi: uning `BACKEND` va `FRONTEND` ichidagilari alohida repozitoriylarga tegishli. Ushbu ikki tashqi papkani repozitoriy ichiga qo‘shimcha qatlam qilib yuklamang.

Bu yangilanishda `App.jsx`, `main.py`, bot va oldingi rasmlar almashtirilmaydi. REV49 dagi `presentation_assets` va frontend `assets` papkalari mavjud bo‘lishi kerak. Yangi pulli xizmat yoki paket bog‘liqligi qo‘shilmadi.

## Nima o‘zgardi?

- Matn olish oynasi saytning yuqori panelidan mustaqil ochiladi. Tepada va pastda `Yopish` bor; o‘rtadagi shakl aylantiriladi. `Mazmunni qo‘llash` pastki boshqaruv qismida turadi.
- Namoyishda `Yopish`, oldingi/keyingi slayd va to‘liq ekran tugmalari bor. `Esc` bilan yopiladi; klaviatura yo‘nalishlari bilan slayd almashtiriladi. Oxirgi slayddan ortiqcha o‘tmaydi.
- Tahrirlash `Mazmun` va `Dizayn` bo‘limlariga ajratildi. Jonli namuna ixcham; pastki maydonlarga o‘tishni katta yopishqoq slayd to‘smaydi.
- Maketlar soni 5 ta. Ustiga sichqoncha olib borilganda yoki `3 ko‘rinish` bosilganda qisqa namoyish ishlaydi va o‘zi to‘xtaydi. Harakatni kamaytirish sozlamasida namuna bosish bilan almashadi.
- Slaydlar o‘z-o‘zidan almashmaydi. Oddiy, yumshoq, surilish va ochilish o‘tishlari tanlanadi; PowerPointga ham tegishli o‘tish yoziladi.

| Maket | Asosiy ko‘rinish |
|---|---|
| Aurora | Oldingi shaffof panel va yorug‘ fon |
| Rangli bo‘limlar | Birinchi PPTga o‘xshash tutash bo‘lim yorliqlari, rangli panel, matn va rasm |
| Tahririy | Yon rang chizig‘i, ochiq fon, ustunlar |
| Galereya | Rasm va qisqa izohlarga kengroq joy |
| Bosqichlar | Raqamlangan qadamlar va o‘rganish ketma-ketligi |

Har bir maketda 8 xil slayd joylashuvi bor. Joylashuvga qarab 1, 2 yoki 3 matn hamda 0, 1 yoki 2 rasm maydoni chiqadi. Rasmli muqovada rasm ixtiyoriy. Formula va misol alohida kiritiladi. Joylashuvni almashtirish yashirin qolgan mazmunni o‘chirmaydi; uni tozalash alohida tasdiqlanadi.

15, 20 va 25 slayd uchun kirishdan xulosagacha besh bo‘limli reja va turli joylashuvlar tayyorlanadi. Mavzu bo‘yicha faktik mazmunni foydalanuvchi yoki AI to‘ldiradi. Bo‘lim yorlig‘i bosilganda shu bo‘limning birinchi slaydi ochiladi.

## Word yoki AI bilan to‘ldirish

1. Mavzu, slaydlar soni va maketni tanlang. Kerakli slaydlarning joylashuvlarini sozlang.
2. `Word shablon` tugmasini bosing. Faylda qisqa tushuntirish va har bir slayd uchun alohida to‘ldirish sahifasi bo‘ladi. Har bir slaydning kerakli matn va rasm tavsifi joylari oldindan belgilanadi.
3. Teglardan keyingi joylarni to‘ldiring. `[SLAYD:n]`, `[ID]`, `[MAKET]`, `[BOLIM]` va `[/SLAYD]` belgilarini o‘zgartirmang. `(Yordam: ...)` satrlari yo‘riqnoma, taqdimot mazmuni sifatida olinmaydi.
4. AI ishlatsangiz, `AI yo‘riqnomasini nusxalash` tugmasi aynan shu rejani ko‘chirishga tayyorlaydi. Uni tanlagan AI suhbatiga joylang. Ushbu tugma o‘zidan AI xizmatiga so‘rov yubormaydi.
5. To‘ldirilgan `.docx` faylini `Matn olish` orqali tanlang yoki tegli matnni joylang. Natijani tekshiring, tasdiq katagini belgilang va `Mazmunni qo‘llash`ni bosing.

Reja asosidagi importda slaydlar soni, tartibi, bo‘limlari, maketlari, alohida dizaynlari va saytda biriktirilgan rasmlar saqlanadi. Boshqa rejaning IDlari yoki o‘zgartirilgan maketi bo‘lsa, tushuntiruvchi xato ko‘rsatiladi. Eski IDsiz tegli matn bilan joriy slaydlarni almashtirish alohida ogohlantiriladi va tasdiqlanadi.

`[RASM1]` va `[RASM2]` — rasmning tavsifi. Rasmni PNG/JPG sifatida saytda yuklang: Word ichidagi rasmlar avtomatik olinmaydi. Formulani `[FORMULA]` maydonida LaTeX matni bilan yozing; Word Equation obyektini import qilish qo‘shilmagan. Matn yoki formula joyga sig‘masa, ogohlantirish chiqadi va PPT eksporti uni kesib chiqarish o‘rniga tuzatishni so‘raydi.

## Tekshiruv va uning chegarasi

- Model va API uchun 25 test; backend xizmatlari uchun 29 test o‘tdi.
- Asl JSX hodisa funksiyalari bilan 9 ta integratsiya tekshiruvi o‘tdi: reja, Word so‘rovi, tasdiqli import, yopish, Escape, slayd chegaralari va bo‘limga o‘tish. Bu React hook/DOM taqlididagi tekshiruv, haqiqiy brauzer sinovi emas.
- Frontendning 62 moduli tahlil qilindi; mahalliy import va eksport xatolari topilmadi. O‘zgargan Python fayllarining sintaksisi tekshirildi.
- Brauzer va PPT joylashuv hisobi 642 holatda taqqoslandi. Barcha besh maketning 15/20/25 slaydli eksportlari tekshirildi; rasmlar, matnlar, tahrirlanadigan formulalar, bo‘lim havolalari va o‘tishlar fayl ichida tekshirildi.
- 15/20/25 slaydli Word shakllari yaratilgan, render qilingan va qayta import qilingan; reja ma’lumotlari aynan saqlangan.

Bu muhitda Vite bog‘liqliklarini yuklash cheklangan va brauzer o‘rnatilmagan. Shu sababli to‘liq `npm run build`, haqiqiy brauzer, PowerPoint dasturi, Railway hamda haqiqiy FastAPI/PostgreSQL bilan ishga tushirish bu yerda tasdiqlanmagan. Backend testlarida bog‘liqliklar o‘rnini bosuvchi test vositalari va SQLite ishlatilgan. Jonli saytdagi deployni paketlar yuklangach tekshirish kerak.

Foydalanuvchiga ochishdan oldin saytda qisqa tekshiring: 25 slayd tanlash → Word shablon olish → bitta sarlavhani to‘ldirib qayta olish → namoyishni ochib `Yopish`/`Esc` bilan chiqish → PPT yuklash. Telefon ekranida ham matn shaklining pastki tugmalarini tekshiring.
