# Maktab rejalari — 23-bosqich

2026–2027. Asosiy yangilanish — yana 13 PDFning barcha 44 beti ko‘rildi va 16 davr bo‘yicha 484 dars ajratildi. Oldingi 215 bilan birga 699 dars ro‘yxati bor. Hozirgi 18 PDFning barcha 75 beti shu ish davomida ko‘rilgan. 18 sinf–fan bo‘yicha 22 davr ro‘yxati bor; musiqa qatoridagi nom mosligi manba nomzodi sifatida qolgan.

## Yangi qamrov

| Manba | Sinf va manbadagi fan | Davr / darslar |
| --- | --- | --- |
| S269 | 1-sinf Alifbe | I chorak 36, II chorak 28 |
| S270 | 1-sinf Matematika | I chorak 45 |
| S271 | 1-sinf Yozuv daftari | II chorak 28 |
| S272 | 2-sinf Matematika | I chorak 45 |
| S273 | 2-sinf Ona tili | II chorak 28 |
| S274 | 2-sinf O‘qish savodxonligi | I chorak 27, II chorak 21 |
| S275 | 3-sinf Matematika | I chorak 45, II chorak 35 |
| S276 | 3-sinf Ona tili | II chorak 28 |
| S277 | 3-sinf O‘qish savodxonligi | II chorak 21 |
| S278 | 4-sinf Musiqiy savodxonlik | 1–34-darslar, yillik qamrov tasdig‘i kutiladi |
| S279 | 4-sinf Ona tili | II chorak 28 |
| S280 | 4-sinf O‘qish savodxonligi | II chorak 21 |
| S281 | 5-sinf Tarixdan hikoyalar | II chorak 14 |

Tarbiyaning oldingi 1–4-sinf o‘zbekcha yillik ro‘yxatlari 33/34/34/34 dars va 4-sinf matematika I–II choraklarining 80 darsi saqlandi. To‘rtta TRM yillik ro‘yxati bor, RTM/ERI tasdiqlangan yillik rejalar soni hali 0. TRM va RTM tashkilot nomlari tenglashtirilmagan. Darslik nashrlari aniqlanmagan, portal test rejimini bildiradi. Barcha 699 darsning yangi taqdimot mazmuni hali tayyor deb belgilanmagan.

## To‘rtta bo‘sh soat katagi

| Ro‘yxat | Dars | Mavzu |
| --- | ---: | --- |
| 2-sinf O‘qish, I chorak | 8 | Ilmsizlik zulmati. Rivoyat |
| 2-sinf O‘qish, II chorak | 6 | Kuch – birlikda. О. Usmonova |
| 3-sinf O‘qish, II chorak | 8 | Zumrad va Qimmat (O‘zbek xalq ertagi, davomi) |
| 4-sinf O‘qish, II chorak | 8 | Nyurka. V. Chaplina |

Rejalar sarlavhalaridagi va qatorlardan hisoblangan davr soatlari jami 699. Dars kataklaridagi raqamlar yig‘indisi 695; yuqoridagi to‘rtta katak manbada bo‘sh. Ularga taxminan 1 yozilmadi. JSONda null, CSVda bo‘sh, HTMLda “Manbada bo‘sh” ko‘rsatilgan. Bu ikki soat ko‘rsatkichini bir xil, barcha dars soatlari tasdiqlangan deb bermang. Qidirish oynasidagi alohida belgi shu to‘rtta darsni chiqaradi.

## Manbadagi ustun va bet farqlari

Yozuv daftarining 28 darsida “Sana” ustuni mashq matnlarini o‘z ichiga oladi. Ular `sana_ustunidagi_matn` da saqlandi, dars sanasi null. 3-sinf matematika II choragida “Uy vazifasi” bo‘sh, bet/mashq havolalari “Izoh”ga yozilgan. Shu 35 matn `izoh_manbada` maydonida saqlandi; uy vazifasi sifatida yashirin ko‘chirilmadi. HTMLda ular asl ustun nomi bilan ko‘rinadi. Sana hech qayerda taxminan qo‘yilmadi.

Musiqa 30-darsining davomi 4-bet boshida; bitta dars bo‘lib birlashtirildi, `pdf_betlar` 3 va 4. 8-darsning Chelesta haqidagi davom matni ham saqlandi. 2-sinf Ona tilining 14-darsi birinchi bet oxirida bo‘lingan; to‘liq ro‘yxatda bor. 5-dars uy vazifasi manbada “14 bet 4-mashq”; 104 deb o‘zgartirilmadi. 5-sinf Tarix haftasiga 2 soat, ammo uning 14 darsi har biri 1 soat: haftalik yuklama dars soatiga ko‘paytirilmadi. BSB/CHSB nomlari va manbadagi 50/40 ball yozuvlari saqlandi, yangi baholash mezoni yaratilmagan.

Musiqa hujjatida birinchi yarim yillik 16 soat deb yozilgan, so‘ng 17–34-darslar davom etadi. Ikkinchi yarim yillikning alohida sarlavhasi yoki umumiy yillik soati yo‘q. 34 ketma-ket dars/34 soat ajratilgan, ammo `annual_complete` false. Manbadagi fan nomi “Musiqiy savodxonlik”; ishchi ro‘yxatdagi “Musiqa madaniyati” qatoriga nomzod moslik, aynan bir xil nom deb almashtirilmagan.

Asl PDFlarning ayrim davom betlarida jadval cheti/sarlavhasi kesilgan yoki matnning bir qismi ko‘rinmaydi. Asl hujjatlar o‘zgartirilmagan. Raqamlar, soatlar va matn qatlami Word bilan mos joylarda solishtirildi. Musiqa 1–3-darslarining matn qatlamida begona raqam va harf orasidagi ajralish bo‘lgan; PDF ko‘rinishidagi o‘qiladigan nomlar bilan aniq transkripsiya qilindi. Uch farq `Matn_qatlami_korinish_farqlari_23.json` da xom va ko‘rinishga mos matn bilan qayd etilgan. Bu fayllar yangi bezatilgan yoki bosmaga tuzatilgan PDFlar emas.

Alifbe va 3-sinf matematika PDFlarida II chorak bor, Wordda esa faqat I chorak. 1–3-sinf matematika va Alifbening I chorak o‘zbekcha nom/soatlari Word bilan solishtirilgan. Ruscha variantlar qo‘shimcha dars sifatida sanalmaydi va aynan mos tarjima deb olinmaydi: masalan, 2-sinf matematikada birinchi dars o‘zbekcha 1–10, ruscha 1–20. Avvalgi 4-sinf matematika Word/PDF farqi va Tarbiya 3–4-sinflarining ruscha qismi 16-darsda tugashi haqidagi cheklovlar saqlangan.

## 1-sinf mosligi tuzatildi

S02 tayanch reja nusxasining 6-beti, 1-band yana ko‘rildi. 1–2-chorakda Yozuv “Ona tili” negizida, Alifbe esa “O‘qish savodxonligi” negizida o‘tilishi yozilgan. Shunga ko‘ra Yozuv MK-01-001, Alifbe MK-01-002 bilan bog‘landi. Oldingi havola auditida Alifbe ham Ona tili qatoriga nomzod sifatida qo‘yilgan edi; yangi auditda bu moslik tuzatilib, reja havolali qatorlar 17 dan 18 ga chiqdi. `Alifbe_Yozuv_mosligi_23.json` da bet, band va nusxa SHA-256 qaydi bor. Bu uchinchi tomon tarqatgan tayanch nusxa; vazirlikdagi asl/ERI tasdig‘i kutilayotgani o‘zgarmadi.

154 fan sahifasi va 27 original hujjat avvalgi paketda saqlandi. Yangi 13 manba yaratilmagan: mavjud S269–S281ning tekshiruv holati va S264 auditi yangilandi. 14 ta eski/yangi qayd `Manba_holati_ozgarishlari_23.json` da. 18 PDF, 9 Word va 281 umumiy manba qaydi bor. Eski paketlar hamda xom hujjatlar o‘zgarmagan; yangilangan ro‘yxatlar ushbu 23-papkada.
