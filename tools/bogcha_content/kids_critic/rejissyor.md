# REJISSYOR + SSENARIST tanqidi — bolalar darslari (2–7 yosh)

Rol: bolalar teleko'rsatuvi/animatsiya rejissyori + ssenaristi. Faqat o'qildi, hech narsa tahrirlanmadi.
Usul: `tools/bogcha_content/*.json` (am_*, mt_*, mn_*, en_*; 1037 muallif darsi, 32 fayl) `build_books()` orqali to'liq qurildi
(/tmp/kc_built.json) va bola ko'radigan/eshitadigan QATORLAR (kirish, tushuncha, topshiriq, test, xulosa) bo'yicha tekshirildi.
Front-end qoidalari (`kidStageRules.js`) va dvigatel (`tools/bogcha_spiral.py`) ham o'qildi — ayrim xatolar dvigateldan keladi (shuning uchun ko'p qatorda takrorlanadi).
Eslatma: audio (TTS) eshitilmadi — "ovoz" deganda matn maydoni (`matn`) nazarda tutilgan.

## Ko'zdan kechirilgan namunalar (kamida 30 dars, hamma fan va yosh)
Format: fayl:dars-raqami (qurilgan kitobdagi tartib raqami, `topics[].no`).
- am: am_23y:1 (Mushuk va it), am_23y:12 (Tarvuz va qovun), am_23y:48 (Meva nima?), am_34:10 (takror), am_45:5 (takror), am_45y:3 (Bahor), am_45y:41 (Suv va havo transporti), am_56:12 (Shamol), am_67y:30 (takror), am_67y:52 (Rangli selderey)
- mt: mt_23y:1 (Bitta va ko'p), mt_23y:5 (Katta va kichik), mt_23y:45 (Tenglashtiramiz), mt_23y:49 (Burchaklarni sanaymiz), mt_34:4 (Sanaymiz 1-2-3), mt_34:6 (To'rt soni), mt_45:1 (Beshgacha), mt_45y:2 (Baland va past), mt_45y:4 (Balandroq?), mt_56:3 (To'rt va besh), mt_67:12 (Beshgacha ayiramiz), mt_67:21 / mt_67y:61 (Uchburchak va to'rtburchak), mt_67y:79 (Maktabga tayyormiz)
- mn: mn_23y:3, mn_23y:4, mn_45y:1, mn_45y:8, mn_67y:12, mn_67y:32
- en: en_23y:1, en_23y:15 (takror), en_23p:2, en_34:4, en_34:6 (takror), en_45y:2, en_45y:5, en_45y:20, en_45y:32, en_45p:2, en_56:5, en_67:4, en_67p:3, en_67y:99 (Katta bayram)
Jami ~48 dars to'liq o'qildi; qolgani skript bilan ommaviy tekshirildi (matn uzunligi, siz/sen, Kabu/Kabutar, sanoq, test variantlari, doska-ovoz).

Raqamli ko'rsatkichlar (o'lchangan):
- Bitta ovoz matni 2–7 yoshda chegaradan (220/300/400) chiqmagan — uzunlik MUAMMO EMAS. Dars ovozi: 2–3 yosh ≈ 65–76 s, 4–5 ≈ 78–99 s, 6–7 ≈ 95–115 s; 13–17 qadam. Diqqat nuqtai nazaridan hajm me'yorda; muammo MAZMUN SIFATI va tartibida.
- 1037/1037 darsning kirish doskasi = «🕊️ <dars nomi>» (kabutar belgisi; kirish matni ko'rsatilmaydi).
- 205 ta «Harakatli o'yin» qatori (har bo'lim takrori + katta bayram) buzuq (qarang №12).

---
## TOPILMALAR

### A. Qahramon (robot Kabu) izchilligi

**1. [JIDDIY]** am_23, am_34, am_45, am_56, am_67, mt_23, mt_34, mt_45, mt_56, mt_67, en_34, en_56, en_67 (eski fayllar, jami ~339 dars) | har darsning kirishi | «Gu-gu! Men — Kabutar qushcha» (masalan am_23:1 «Gu-gu! Salom, bolajonlar! Men — Kabutar qushcha»; en_34:11 «Kabutar qushcha uyingizga uchib keldi»; en_67:4 «Kabutar loves counting»; en_56:1 «I am Kabutar»). Qoida: faqat «robot Kabu». | Tuzatish: shu 13 faylni nashrdan olib tashlash yoki «y» kitoblar bilan almashtirish; almashtirish mumkin bo'lmasa «Gu-gu!»→«Bip-bip!», «Kabutar qushcha»→«robot Kabu» + parrandalik gaplarni (2-band) qayta yozish.

**2. [JIDDIY]** «y» (yangi, robot Kabu) fayllarda ham QUSH xususiyatlari qolgan — robot «uchadi», «uyam», «qushchaman»: mt_23y:25 «Men uchib tepaga ko'tarildim»; mt_45y:2 «Men uchib yuribman»; mt_45y:8 «Kunduzi men uchaman, tunda uxlayman»; mt_45y:38 «Mening uyamda … tuxum»; mt_45y:49 «Shoxda ikkita qushcha … bu men edim!»; mt_67y:28 «Men qushchaman, yil bo'yi tabiatni kuzataman»; mt_67y:67 «robot Kabuning kuni … bog'chaga uchadi, tushlik qiladi»; am_67y:31 «Men bog'da uchib yurib»; am_67y:66 «Men O'zbekiston ustidan uchib o'tdim»; en_23y:33 «Men uchaman»; en_67y:(3-bo'lim)1 «Kecha tumov bo'lib qoldim, shifokor meni davoladi»; en_67y «Men shahar ustidan uchib…», «Men bog'chaga uchib boraman», «Men palovni yaxshi ko'raman — ayniqsa guruchini», «Oyim…» (mt_45y:15). | Tuzatish: robotga mos: «Men antennam bilan qaradim / g'ildiragimda yuribman», «batareykam», «tunda zaryadlanaman» (en_45y «Men batareykamni yaxshi ko'raman» — to'g'ri namuna, boshqalar shunday bo'lsin). mt_45y:49 da «bu men edim» o'rniga «Bu — mening robot do'stim edi».

**3. [O'RTA]** en_45y:32,48,49,62; en_45y; en_56; en_67 | «🕊️ Kabutar aytdi» (32 sarlavha), dialoglar «Kabutar: Water or juice?» (48), «Kabutar: I'm hungry!» (49), «Kabutar: What's the weather like?» (62) — yangi «y» faylda eski qahramon. | Tuzatish: «Kabu:» / «🤖 Kabu aytdi».

**4. [O'RTA]** am_34, mt_23, en_34, am_23y (4 dars) | bir kitob ichida ikki ovoz: har darsning kirishi «Gu-gu!», takror/bayram kirishlari «Bip-bip!» (dvigatel shabloni, `bogcha_spiral.py` 827/858/896-qator). am_34:10 da bir darsda ikkalasi; am_34:29 «Gu-gu! Ko'chada «bip-bip» qilib…»; en_34:34, :48 da ham aralash. | Tuzatish: butun kitobni bitta qahramonga keltirish.

**5. [O'RTA]** «y» kitoblarda Kabuning ISMI KIRISHLARDA deyarli aytilmaydi (kirish qatorida «Kabu» nomi: am_23y 1 dars, am_67y 1, mt_23y 2, mt_45y 1, mt_67y 2; am_45y, mn_23y/45y/67y, en_45y/en_45p da 0). Bola «Bip-bip» eshitadi, lekin kim gapirayotganini bilmaydi (obraz yo'q: antenna, batareyka, "xatosi" yo'q). | Tuzatish: har bo'lim birinchi darsida 1 gaplik tanishuv («Men — robot Kabu, batareykam to'la!») va doimiy "tic": batareyka indikatori, «Bip-bip» — yangi sir belgisi; bo'lim oxirida Kabuning "xatosi" (en_67p «Kabu is wrong!» yaxshi namuna).

**6. [O'RTA]** `bogcha_spiral.py:707,709` | HAR kirish doskasi «🕊️ <nom>» (kabutar emoji) va sarlavha emojisi bo'lim emojisi (dars emas): am_23y:1 «Mushuk va it» kirish sarlavhasi 🐄; am_23y:12 «Tarvuz va qovun» — 🍎; en_67p:3 «Kechqurun» — ☀️. Robot obrazi bilan zid. | Tuzatish: «🤖» + dars emojisi.

**7. [KICHIK]** mexanik almashtirish izlari: gap boshida kichik harf «robot Kabu» — mt_23y:1,4 test «robot Kabu nechta? Bitta yoki ko'p?» (ma'nosiz savol, variantlar 🤖 / 🤖🤖🤖🤖); am_23y:19 «robot Kabuga ko'rsat»; am_67y:21,22,27,58,66,68; mt_67y:67 «Bip-bip! robot Kabuning…»; mt_67y:79 «Bip-bip!, sendan faxrlanaman!» va «Bip-bip!, barakalla!» (vergul TTS ni buzadi). | Tuzatish: «Robot Kabu», «Bip-bip! Sendan faxrlanaman!»; mt_23y:1 testini «Qaysi rasmda bitta olma?» ga almashtirish.

### B. «Sen» shakli (siz/keling YO'Q)

**8. [O'RTA]** `bogcha_spiral.py:473` | har bir tushunchaning «sodda» varianti «Keling, sekinroq: …» — 2986 qator (am/mt/mn «y» kitoblarda ham: am_23y 188, mt_67y 291, mn_67y 126). «Keling» = siz. | Tuzatish: «Qani, sekinroq:».

**9. [O'RTA]** `bogcha_spiral.py:789,896` | «Keling, rol o'ynaymiz!», «Keling, eng qiziq so'zlarni eslaymiz» (har katta bayram darsi, en_23p:11 ham). | Tuzatish: «Qani, rol o'ynaymiz!».

**10. [O'RTA]** eski fayllarda siz-shakl ommaviy: en_56 (96 joy), en_67 (77), en_34 (52), mt_45 (50), mt_34 (47), mt_56 (37), am_23/am_67 (28). Misollar: mt_56:3 «Qo'lingizni oching va sanang»; mt_67:12 «Orqaga sanashni eslang!»; mt_67:21 «Esingizdami, kubning yuzlari…»; en_34:34 test «Tarbiyachi sizga Hello! dedi. Nima deysiz?»; en_67:4 «Sanashga yordam berasizmi?»; am_34:34 «siz shifokorsiz… Yuragini eshiting». | Tuzatish: 1-bandga qarang (fayllarni almashtirish).

**11. [KICHIK]** «y» fayllarda qoldiq: en_23y (68 joy), en_23p (5), en_34 testlarida «Qani, toping: …qayerda?» («toping» = siz; sen: «top»); am_45y:19 «sanang», «ko'rsating» (2); mt_23y:1 «sizlarga»; mt_67y «oching», «sakrang». | Tuzatish: «Qani, top: …».

### C. Ovoz ↔ doska mosligi

**12. [JIDDIY]** 205 ta «🏃 Harakatli o'yin» (har bo'lim takrori va katta bayram; am_34:10, am_45:5, am_67y:30, en_23y:15, en_34:6, mt_23y:4 …) | ovoz: «rasm ekranda bo'lsa — sakra, bo'lmasa — o'tir!» (ingliz tilida «If you see the picture — jump! If not — sit down!»), lekin doskada bo'limning BARCHA 8–12 rasmi bir vaqtda turibdi va ovoz hech qanday so'z aytmaydi → o'yin ishlamaydi (hamma rasm doim ekranda; «o'tir» holati hech qachon bo'lmaydi). | Tuzatish: har qadamda 1 ta rasm ko'rsatilsin (yoki ba'zi qadamda «?»/bo'sh), ovoz so'zni aytsin: «Qani: mushuk! … mashina!»; yoki «Top-chi» (bosiladigan) mexanikasiga o'tkazish.

**13. [JIDDIY]** 1037 darsning KIRISH qadami | hikoya/sir savoli («Eshik oldida kimdir «miyov» dedi… Kim ekan?» am_23y:1; «Biri ichi qizil, biri xushbo'y. Qani, top!» am_23y:12; «Pastda jirafa va toshbaqa. Kim baland?» mt_45y:2) — doskada faqat «🕊️ nom»: sirli rasm/siluet yo'q, ovozda aytilgan narsa ko'rinmaydi. | Tuzatish: kirish doskasi = sir sahnasi (🚪❓🐈🐕 / 🍉🍈❓), javob ochilishi keyingi qadamda.

**14. [JIDDIY]** hamma fan | kirishdagi savol javobsiz qoladi: kirishdan keyin darhol 1–2 ta «🔁 Eslaymiz» kartasi (am_23y:12 «Qani, top!» → Banan/Uzum, Kurka/O'rdak; am_45y:3 «Qaysi fasl uyg'ondi?» → Qish/Chana; mn_67y:12). 2–3 yoshda takror ovozi o'qitish qismining 24–31 % ini oladi (am_23y 24 %, mt_23y 29 %, mn_23y 31 %). Qiziqtirish uziladi, sir 20–30 s javobsiz. | Tuzatish: yangi bilimni (sir javobi) AVVAL, «Eslaymiz» ni keyin yoki o'yin sifatida oxirda; har darsda ko'pi bilan 1 takror kartasi (2–3 yosh).

**15. [O'RTA]** mt_23y:45 «Tenglashtiramiz» «🎭 Do'kon o'yini» | ovoz: «Sen sotuvchi bo'l. Har bir o'yinchoqqa bittadan olma ber. Yetmasa — bitta qo'sh, ortsa — ol!»; doska: «🐰🐰🐰 🥕🥕➕🥕 / 🐶 🦴➖🦴» (quyon-sabzi, it-suyak; o'yinchoq ham, olma ham yo'q). | Tuzatish: ovozni doskaga moslash («Quyonga sabzi ber…») yoki doskaga 🧸🍎.

**16. [O'RTA]** am_23y:48 «Meva nima?» «🧺 Daraxtdan meva teramiz» | ovoz: «Olma — hop! Apelsin — hop! Uzum — hop!»; doska: «🌳 ➡️ 🧺» (meva ko'rinmaydi). | Tuzatish: «🍎🍊🍇 ➡️ 🧺».

**17. [O'RTA]** am_45y:41 «Yer, suv, havo» | ovoz bir nafasda «Avtobus! Kema! Samolyot! Poyezd! Vertolyot!» deb sanab o'tadi (pauzasiz, harakat qilishga ulgurmaydi); doska «🛣️ 🌊 ☁️» (transport rasmi yo'q). | Tuzatish: har transportga alohida qadam/pauza, doskada 🚌🚢✈️🚂🚁.

**18. [O'RTA]** en_34:4 «Ha va yo'q» o'yini | savollarga ovoz O'ZI javob beradi («Kabutar qushcha mushukmi? Yo'q! No! Siz bolamisiz? Ha! Yes!») — bola gapirmaydi; doskada faqat ✅ ❌ (mushuk/bola/muzqaymoq ko'rinmaydi); «siz», «Kabutar qushcha». | Tuzatish: savol → pauza → «Endi sen ayt!», doskada 🐱❓🧒🍦.

**19. [JIDDIY]** en_67:4 va en_67y:4 testlari «How many stars can you see?» (variantlar 15/20/12/11), en_67:3 «Fingers and toes together. How many?», en_45/en_45y:16 «There are six ducks. How many?» | savolda yulduz/o'rdak rasmi YO'Q (manba faylda 12 ⭐ bor edi, qurilgan qatorda tushib qolgan) — bola sanay olmaydi, to'g'ri javobni taxmin qiladi (savolda stars deyilgan, o'rgatilgan «twenty stars» esa javob emas). | Tuzatish: savolga ⭐×12 / 🦆×6 qaytarish va doskaga chiqarish.

**20. [JIDDIY]** en_45/en_45y 14,15; en_56:6; en_67:4; en_45y:2 | dvigatel shabloni ma'nosiz savol beradi: «Which one is: Let's count?», «Which one is: How many?», «Find the picture: How many», «Find the picture: What's your name» (ibora uchun «rasm top» — rasm yo'q, 🤔/🧮 belgilar). Bola tilni noto'g'ri tushunadi. | Tuzatish: iboralar uchun savol «Qaysi biri «nechta?» degani?» (o'zbekcha) yoki «Nima deysan?» + vaziyat rasmi.

**21. [O'RTA]** mn_67y:3 va yana 12 qator (jami 13) | «Top-chi» gapi: «…To'rtta rasmli naqsh, Bo'lakda nechta rasm?. Topsang…» — savol sarlavhasi bosiladigan nishon deb o'qiladi + «?.» tinish belgisi. mt_67:36/37/38, mn_67y:31 da nishonlar mavhum («Sabab, Oqibat, Voqea tartibi», «Qoida, Xulosa» → 📋 💡; mt_34:4 «Barmoq bilan sanash, Oxirgi son»; mt_45:1 «Har biriga bitta tegamiz») — rasmdan topib bo'lmaydi. | Tuzatish: nishon sifatida faqat ko'rsatib bo'ladigan narsalar; mavhum iboralarni o'yindan chiqarish.

**22. [O'RTA]** en_45y:5, en_56:5 «🎭 Role play» | oltita qatorli dialog BIR ovozda, bir qadamda o'qiladi (bolaning gaplari ham), faqat inglizcha yo'riqnoma («I am the new friend, you are the child… Now we change roles!»); bola o'zi gapirmaydi. | Tuzatish: har qatorga alohida qadam; Kabu qatori → pauza → bola qatori; yo'riqnoma o'zbekcha.

**23. [O'RTA]** en_45y:20 «Timsoh o'yini», en_45y:32 «Kabutar aytdi», en_45p:8 | «o'yin» = so'zlar ro'yxatini o'qish: «Let's play! Zebra! Snake! Crocodile! Excellent!»; «Touch your head! Touch your ears! Touch your knees! Clap your hands! Stamp your feet!» (5 buyruq pauzasiz, bola bajarishga ulgurmaydi; head/ears doskada yo'q); en_45p:8 «dinner bath go to bed Good night, Kabu!» | Tuzatish: Simon-says: bitta buyruq → pauza → harakat → maqtov.

**24. [O'RTA]** en_67y:99 «Katta bayram» (va boshqa en_*y bayram darslari) | «Remember:» kartalari bog'lanmagan iboralardan iborat chalkash gap: «I visited my granny. Where do you live? morning. I drew a picture. You know them all!», «Eat fruit! chest. Let's make a salad! house.», «pilot. OK! Here you are. next to.» | Tuzatish: har so'z/iborani alohida qadam, yoki mavzu bo'yicha guruhlash.

**25. [JIDDIY]** en_67y:99 «🎉 Party question» | «Look at the picture. What is it?» + faqat emoji (🐦 / 😋 / 🥰) — variantlar gaplar: to'g'ri javob «A bird can fly.», «It's delicious!», «I love my mum.» — «What is it?» ga javob emas (noto'g'ri inglizcha), variantlarda rasm yo'q. | Tuzatish: «What can it do?» / «Say it!» + rasmli variantlar.

### D. Sanoq va matematika

**26. [JIDDIY]** mt_67:21 va mt_67y:61 «Cho'plardan shakl yasaymiz» | «Oltita cho'p olamiz. Uchtasidan uchburchak, to'rttasidan kvadrat (3+4=7 > 6!). Endi ikkita uzun va ikkita qisqa qalamdan to'g'ri to'rtburchak» (yana 4 ta) — jami 11 ta kerak. Doska «🔺 = 3 cho'p / 🟥 = 4 cho'p». Bola hisoblasa chiqmaydi. | Tuzatish: «O'n bitta cho'p…» yoki bitta-bitta qilib («Uchta cho'p — uchburchak. Endi to'rtta — kvadrat»).

**27. [O'RTA]** `kidStageRules.js` 446–458 (sanashTopshiriq) | sanash qadami interaktiv bo'lishi uchun doskada 2–12 ta emoji kerak va ⭐🌟 chiqarib tashlangan: am_56:18 «Yulduzlar» (12 ta ⭐ «birga sanaymiz» — ⭐ filtrlanadi, interaktiv sanash ishlamaydi); en_67:4 va en_67y:4 «Let's count together» (12 ta 🍎 + 🧮 = 13 belgi > 12 → null, sanash qadami oddiy ko'rsatishga aylanadi). 5–6 yoshda 20 gacha sanash bo'lishi kerak. | Tuzatish: sanash narsalari uchun ⭐/🌟 dan boshqa emoji (🔵, 🍎) yoki filtrni olib tashlash; limitni yoshga qarab (20) ko'tarish.

**28. [O'RTA]** mt_56 (5–6 yosh) va mt_67/mt_67y (6–7 yosh) | CURRICULUM talabi: 5–6 yosh 1–20, 6–7 yosh 1–100. mt_56 faqat 10 gacha («O'n soni» — oxirgi son); mt_67 faqat 20 gacha («O'n to'qqiz va yigirma»), 21–100 yo'q. | Tuzatish: mt_56 ga 11–20, mt_67 ga 21–100 (o'nliklar bilan sanash) darslari.

**29. [O'RTA]** mt_67y (81 dars) boshidan 41 dars aynan mt_56 mazmuni («Nol va bir», «Ikki va uch» …); xuddi shunday am_67y/am_56 (41/81), am_45y/am_34 (15/56), mt_45y/mt_34 (14/54), mt_23y/mt_34 (13/52). 6–7 yoshli bola kitobni «Nol va bir» dan boshlaydi (yoshga past). | Tuzatish: bu niyat bo'lsa (kumulyativ) yosh sarlavhasini aniqlash; aks holda takroriy darslarni olib tashlash/«o'tgan yilni eslaymiz» ga qisqartirish.

**30. [O'RTA]** mt_45y:2,4,43,44 «Baland/Balandroq», test «Qaysi minora balandroq? 🧱🧱 / 🧱🧱🧱🧱» | balandlik emojilarning GORIZONTAL qatori bilan ko'rsatilgan — bola «uzunroq» ko'radi, «balandroq» emas; «Uzunroq» uchun ham xuddi shu ➖➖➖➖. | Tuzatish: vertikal ustun (har emoji yangi qatorda) yoki rasm (mt45-… PNG) bilan, doskada vertikal tizilma.

**31. [O'RTA]** mt_45y:4 («Eslaymiz: ➖➖➖➖ Uzunroq»), «Eski savol ✏️➖ qisqa / ✏️➖➖➖ uzun»; shu kitoblarda ➖ = «minus» (mt_23y:44–45 «🦴➖🦴 Bittasini olamiz», mt_67 «➖ Minus belgisi») | 4 yoshli uchun bir belgi ikki ma'noda. | Tuzatish: chiziq uchun 📏 yoki ▬.

**32. [O'RTA]** mt_67:11 / mt_67y:11 «Ayirish» elementi emojisi 👋 (qo'l silkitish = salom); «Eslaymiz: 👋 Ayirish» keyingi darslarda; mt_67:2 «🧠 Katta sondan sanab ketish» mavhum karta. | Tuzatish: 🍎➖🍎 yoki 🐦💨; «Katta sondan sanab ketish» uchun 🔢➡️.

**33. [O'RTA]** mt_67y:54, mt_67:14/15/18/23 «Qaysi misol to'g'ri? ✅» | variantlar oldindan belgilangan: «A) ❌ 6 − 2 = 8  B) ✅ 6 − 2 = 4  C) ❌ 6 + 2 = 4» — to'g'ri javob ✅ bilan ko'rsatilgan, test tekshirmaydi. en_67y:9 «📆✅ Today is Monday.» ham. | Tuzatish: variantlardan ✅/❌ olib tashlash.

**34. [JIDDIY]** am_67y:62 (va am_67:22) «Tish yuvayotganda jo'mrak qanday bo'lishi kerak?» | variantlar: «🚰❌ yopiq» (TO'G'RI), «🚰✅ doim ochiq» (NOTO'G'RI). Yashil ✅ belgisi noto'g'ri variantda, ❌ to'g'risida — o'qiy olmaydigan bola belgiga ishonadi va «ochiq» ni tanlaydi (suv isrofini o'rganadi). | Tuzatish: belgilarni olib tashlash (🚰 yopiq / 🚰💦 ochiq).

**35. [O'RTA]** mn_67y:12 «Rangi boshqa» testlari «🍓🍌🟥🍎 Qaysi biri ortiqcha?» (to'g'ri: 🍌 banan), «🔴🟢🍅🍒» (🟢), «🍎🔵❤️🟥» | qoida aytilmagan: bir xil rasmda ikki to'g'ri javob bor (🟥 — meva emas; 🍌 — qizil emas). Bola mantiqan to'g'ri javobni «xato» deb belgilaydi. | Tuzatish: savol «RANGI bo'yicha qaysi biri ortiqcha?» (shu lug'at har mn «ortiqcha» savolida mezon aytilsin).

**36. [O'RTA]** mn_23y:4 («Bir xil shakllar») «Kvadratning to'rtta burchagi bor. Barmog'ing bilan to'rt burchakni ko'rsat!»; mt_23y:49 «Burchaklarni sanaymiz» (burchak tushunchasi, «burchak yo'q» inkor); mt_23y:44–45 «Teng emas / Tenglashtiramiz» (➕➖ belgilar, «🐻 🍯🍯. Teng qilish uchun nima qilamiz?»); mn_23y:20 «Naqsh» (🔴🔵🔴❓ ABAB davom ettirish) | 2–3 yosh uchun chegara 1–3 va 2 ta tushuncha; to'rtlik sanoq, burchak, qo'shish-ayirish, naqsh — 4–5 yosh darajasi. | Tuzatish: 2–3 yoshdan olib, 3–4 / 4–5 ga ko'chirish.

**37. [KICHIK]** mt_23y:2 «Ko'pdan bitta» — «ko'p» sifatida 🍬🍬🍬 (3 ta) ko'rsatilgan, 1-darsda «ko'p» = 🍎×5; mt_45:18, 22, 27 «🐤🐤🐥🐤 — nechta jo'ja?» aralash emoji (🐤 va 🐥) sanoqda — bola «ikki xil» deb o'ylashi mumkin; mt_56 «🐞 qo'ng'iz» vs am «xonqizi». | Tuzatish: bir xil emoji, bir xil nom.

### E. Mantiq va yosh moslik (diqqat, hikoya, qo'shiq)

**38. [O'RTA]** mt_34:4, mt_34:6, mt_45:1 «Eslaymiz: 🐥🐥🐥 3️⃣ Oxirgi son … 👉🐥🐥🐥 Barmoq bilan sanash» (3–5 yosh) | «Oxirgi aytilgan son — nechtaligi» (kardinallik tamoyili) kattalar atamasi; bola uchun to'rt qatorli «Eslaymiz» kartasi 3 yoshga og'ir. | Tuzatish: «Oxirgi son — nechta ekanini aytadi» deb harakat bilan («barmoq tegib, oxirgisida to'xta»).

**39. [O'RTA]** hamma «takror» darslari (am_34:10, am_45:5, am_67y:30, en_34:6) | 3 qatorli «Eslaymiz» kartalari 3 tadan so'z (9–12 tushuncha ketma-ket), so'ng 5 test: hikoya, sir, qo'shiq, harakat yo'q — «dars jonsiz» (yulduzcha ham ko'rsatilmaydi: «Har to'g'ri javob — bitta yulduzcha!»). Bo'lim emojilari takrorlanuvchi (12 emoji bir doskada, am_45:5). | Tuzatish: takror = mini-sarguzasht (Kabuning "yo'qolgan so'zlari" izlash), har kartada 1–2 tushuncha.

**40. [O'RTA]** `bogcha_spiral.py:476-488` item_other/«boshqa_usul» — am/mt/mn kitoblardagi 2989 qatorda: «Atrofingga qara: miyov deydi, sut ichadi qayerda bor? Barmog'ing bilan ko'rsat va ayt!» / «hech narsa yo'q qayerda bor?» (mt_56:1) / «suvning bug'ga aylanib havoga ko'tarilishi qayerda bor?» (am_67y) / «naqshning takrorlanish qoidasi qayerda bor?» (mn_67y). `uz` maydoni (tavsif) gapga qo'yilgani uchun ma'nosiz/tushunarsiz. | Tuzatish: `explain` dan harakat ishlatish yoki «boshqa_usul» ni muallif yozsin; shablonni faqat konkret ot (mushuk, sigir) uchun qoldirish.

**41. [O'RTA]** hamma darsning xulosasi (1037 ta): «Bugun biz Katta, Kichik ni o'rgandik / Mushuk, It ni o'rgandik / Hello!, Hi! ni o'rgandik. Ertaga yana uchrashamiz — yangi sir bor!» | katta harf, vergul-ro'yxat + «ni» (ayniqsa «Qo'shamiz, Ayiramiz, Ikki marta ni»), "yangi sir" hech qachon aytilmaydi, Kabu bilan xayrlashuv yo'q. | Tuzatish: «Bugun mushuk bilan itni o'rgandik. Ertaga sening yangi do'sting kutadi — qani, kim ekan? Bip-bip, xayr!» (keyingi dars nomidan avtomatik teaser).

**42. [O'RTA]** en_45, en_45y, en_45p (38/79, 30/47, 8/15 dars) va en_56 (8 «Review day!») kirishlari | faqat inglizcha ro'yxat: «[en]Look and listen: zebra, crocodile, snake.[/en]» (en_45y:20), «Look and listen: Excuse me, Sorry, That's OK.» (en_45p:2) — 4–5 yoshli ona tilida tushunmaydi; hikoya/sir/Kabu yo'q (kirish shu yerda eng zaif). | Tuzatish: o'zbekcha 1–2 gaplik sir («Bip-bip! Hayvonot bog'ida yo'l-yo'l kimdir turibdi!») + 1 inglizcha so'z.

**43. [O'RTA]** qo'shiqlar: barcha «🎵 … qo'shig'i» (am 6–13, mt 4–9, en 2–10 har kitobda) | qo'shiq = oddiy matn qatori («Bir — katta barmoq, ikki — ko'rsatkich…», mt_56:3; «Qo'shiq aytamiz! Mushukcha — miyov…» am_23y:1) — ovoz TTS bilan nutq sifatida o'qiladi; ritm/qofiya/qaytarma (refren) belgisi yo'q. Ayniqsa mn_45y, mn_67y da 🎵 umuman yo'q; tajriba/hikoya mn va mt da deyarli yo'q (tajriba — faqat am da). | Tuzatish: `musiqa`/`ritm` maydoni yoki kuyga tayyor matn (qofiyali, har qatorda bitta harakat), qo'shiq audio qo'shish.

**44. [KICHIK]** am_23 (va am_23y:1) «Ovoz qo'shig'i»: «Kuchukcha — vov, vov, vov!» — darsda «It» o'rgatilgan, «kuchukcha» o'tilmagan so'z; mt/mn kitoblarda «kuchuk», am da «it» — bir kitob ichida ikki nom (mt_45y:4 «🐕 kuchuk», mn_45y:8 «🐶 kuchuk»). | Tuzatish: birlashtirish («it»).

**45. [KICHIK]** emoji–so'z nomuvofiqligi: am_67y:68 «🗼 Buxoro» (🗼 = Tokio minorasi); «🍉 Bozor», «🍌 Kompost», «🥬 Suv shimish», «🧢 Ehtiyot bo'lish», «🛞 Nasos»; en «🙆 head» (imo-ishora odam), en_45y:32 «☝️ Touch your nose!» (bir joyda 👃 nose) ; «🚪 Bye!» va «🚪 Goodbye!» bir xil emoji; fasllar: Yoz = 🌞 (am_34) / 🏖️ (am_45y) / 🌻 (am_67) — kitoblararo nomuvofiq. | Tuzatish: aniq emoji (🕌 Buxoro: Kalon, 🛒 bozor) va yagona lug'at jadvali.

**46. [KICHIK]** am_67y «Qon» elementi 🩸 (qon tomchisi) — 6–7 yoshga qo'rqinchli bo'lishi mumkin (qoida: qo'rqituvchi belgilarsiz); | Tuzatish: ❤️‍🩹 yoki 🫀 + «qon tomirlari 🔴».

**47. [KICHIK]** mt_67y:79 / am_67y:30 va boshqa 6–7 yosh takrorlarida har savolda 3–4 variant, lekin 2–3, 3–4, 4–5 yoshda har doim 2 variant (50 % taxmin); «Qo'tosni sovuqdan nima saqlaydi? ☀️ issiq ko'ylak» kabi aniq xato variantlar: bola o'ylamaydi. | Tuzatish: 3–4 yoshdan 3 variant (bittasi yaqin-xato).

**48. [KICHIK]** en_34:6 (takror) | «Eslaymiz» kartalari takrorlanadi: «🌅 Good morning!» ham «☀️ Good morning!» ham, «🙋 Hi!» ikki marta, «👩‍🏫 Hello! Good morning!» uchinchi marta; test «Qaysi biri Hi?» ham ikki darsda. | Tuzatish: har so'z takrorda bir marta.

**49. [KICHIK]** am_23y:12 testi «Qaysi meva xushbo'y va sariq? 🍎 olma / 🍈 qovun» — olma sariq va xushbo'y bo'la oladi (ikki javob). | Tuzatish: «Qaysi meva sariq va uzun?» kabi aniq mezon.

---
## XULOSA (10 qator)
1. Uzunlik chegarasi hamma joyda o'tilgan; asosiy yo'qotishlar — qahramon, ovoz/doska va dvigatel shablonlari (sistem xatolar: 6, 8, 12, 13, 14, 40, 41).
2. Qahramon: ~339 eski dars hamon «Kabutar qushcha/Gu-gu», yangi «y» fayllarda ham robot «uchadi/uyam/qushchaman» (2-band); Kabu ismi y kitoblarda deyarli aytilmaydi.
3. «Sen» shakli: dvigatel «Keling, sekinroq» (2986 qator) va eski fayllardagi siz-shakllar tuzatilsin.
4. Ovoz–doska: kirish doskasi har darsda 🕊️+nom (1037/1037), kirish savoli takror kartalari bilan uziladi; 205 «Harakatli o'yin» ishlamaydi.
5. JIDDIY o'quv xatolari: cho'p hisobi (7>6), am_67y:62 jo'mrak (✅/❌ teskari), en_67 «How many stars?» rasmsiz, en_67y «What is it? → A bird can fly».
6. Test javobini oshkor qiluvchi ✅/❌ belgilar (mt_67y:54, en_67y:9) va noaniq «ortiqcha» mezonlari (mn_67y:12).
7. Yosh moslik: 2–3 yoshda burchak, naqsh, qo'shish/ayirish; 6–7 yoshda 21–100 yo'q; mt_67y 41 darsi mt_56 dan nusxa.
8. Dars jonli emas joylari: takror darslari (hikoya/qo'shiq/harakat yo'q), ingliz 4–5 yosh kirishlari (faqat inglizcha ro'yxat), qo'shiqlar faqat matn.
9. Yaxshi namunalar (andoza qilish uchun): mn_45y:1 «Harakatli naqsh» (👏🦶), en_67p:3 «Kabu is wrong!», en_45y «Men batareykamni yaxshi ko'raman», am_45y:25 «Sen — gulsan!» (TPR) — shu uslub hamma darsga.
10. Birinchi navbat: 1-, 2-, 12-, 13-, 26-, 34-, 19-, 25-, 33-bandlar (JIDDIY), so'ng dvigatel shablonlari (6, 8, 9, 40, 41) — bir tuzatish minglab qatorni to'g'rilaydi.
