# TANQIDCHI hisoboti — Ingliz tili (en_*), 2–7 yosh (til mutaxassisi: TPR/immersion + lingvist)

Qamrov: asosiy tekshiruv — joriy "y" kitoblari (en_23y 2–3 yosh, en_45y 4–5 yosh, en_67y 6–7 yosh) va ulardan dvigatel
(tools/bogcha_kitob.build_books) yasagan tayyor kitoblar (50 / 80 / 100 dars). Qo'shimcha — manba fayllar (en_23, en_34, en_45,
en_56, en_67 va *_enrich.json), chunki out_kids/asosiy da 3–4 va 5–6 yosh ingliz tili kitoblari ham bor.
Usul: json ni python bilan ommaviy skanerlash (siz-shakl, Kabutar/qush, emoji soni, [en] teg, so'z takrori, o'rgatilmagan so'z),
build_books natijasini (ovoz matni) o'qish, bogcha_oyin_tekshir.py (uchala y fayl: 0 xato — ya'ni validator quyidagi xatolarni ushlamaydi).
Raqamlar skript bilan sanalgan; taxminiy joylar "~" bilan belgilangan.

Qisqartma: 23y/45y/67y = en_23y.json / en_45y.json / en_67y.json; "qurilgan kitob" = build_books natijasi.

---------------------------------------------------------------------------------------------------

## A. IMMERSIYA, OVOZ VA YOSHGA MOSLIK

1. [JIDDIY] tools/bogcha_spiral.py (IMMERSION) + en_45y | butun 4–5 yosh kitobi | `IMMERSION["4-5 yosh"] = 4`, ENRICH_SPEC jadvalida esa 4–5 yosh = 2-pog'ona
   («o'zbekcha + inglizcha sinf buyruqlari»). Natija: qurilgan 4–5 yosh kitobida ovozli qatorlarning (kirish/tushuncha/topshiriq/xulosa)
   540 tasi 710 dan (76%) TO'LIQ inglizcha ("[en]Look and listen: Hello, Goodbye, Thank you.[/en]"), o'zbekcha tushuntirish yo'q.
   2–3 yoshda esa 0 ta sof inglizcha qator — bola 100% o'zbekchadan to'satdan 76% inglizchaga sakraydi (immersiya zinasi 1 → 4, 2–3-pog'ona tushib qolgan).
   Tuzatish: 4–5 yosh uchun IMMERSION = 2 (qisqa o'zbekcha ko'prik + inglizcha buyruq), 5–6/6–7 uchun 3→4; 45y dagi `"immersion": 3` belgisini ham 2 ga tushir.

2. [JIDDIY] qurilgan 4–5 yosh kitobi | har darsdagi «🎲 Point to it!» topshirig'i (masalan №2 «Salom va rahmat», №5 «To'rt rangni eslaymiz») |
   O'yin qoidasi faqat inglizcha: "Game time! I say it, you point to the picture: red, blue, yellow, green. Ready? Go!" — 4 yoshli bola
   qanday o'ynashni tushunmaydi, o'yin ishlamaydi. Tuzatish: 4–5 yoshda qoida avval o'zbekcha: "Men aytaman, sen rasmni bos!", keyin inglizcha "Ready? Go!".

3. [JIDDIY] 23y, 45y, 67y (qurilgan kitoblarda) | har darsning «kirish» doskasi | doskada 🕊️ (kaptar) belgisi: 2–3 yoshda 38 qator, 4–5 da 51, 6–7 da 100 dan 64 qator
   ("🕊️ Hello va Hi", "🕊️ Salom va rahmat"). Qahramon faqat robot Kabu bo'lishi kerak. Manba kitoblarda (en_23/34/45/56/67) ham 31–32 darsda 🕊️.
   Tuzatish: bogcha_spiral dagi kirish doskasi belgisini 🤖 ga almashtir (hamma tilga ta'sir qiladi — ehtiyot bo'l).

4. [JIDDIY] en_45y | «Touch your nose!» (№33) va «Ichimliklar» (№49), «Tushlik» (№50), «Soyabon va kamalak» (№63) | «🕊️ Kabutar aytdi» sarlavhasi;
   ovozda inglizcha "Kabutar: Water or juice? Child: Juice, please! Kabutar: Here you are." va "…Mix, mix! Kabutar: I'm hungry!" — bola "Kabutar" ismini eshitadi (TTS ham o'qiydi).
   Tuzatish: "Kabu says" / "Kabu:" ga almashtir (matn_en: 4 joy, sarlavha: «🤖 Kabu aytdi»). Eslatma: ENRICH 5–6 dan ko'chirilgan, qolgan 45y matnlari allaqachon "robot Kabu".

5. [JIDDIY] en_67y | «Nechta ekan?» (units[0].lessons[3].items[0]) va «Menga yoqmaydi» ("I don't like rain.", units[8].lessons[1].items[1]) image_prompt | rasm promptlari "A pigeon pointing at a pile of apples…" va "A wet grumpy pigeon under the rain…" — chizilgan rasmda
   robot Kabu emas, kaptar bo'ladi. Tuzatish: promptlarda "a friendly small robot with an antenna" yoz; shu rasm nomi bilan allaqachon chizilgan bo'lsa qayta chiz.

6. [JIDDIY] manba: en_34.json, en_34_enrich.json, en_45(+_enrich), en_56(+_enrich), en_67(+_enrich) | scenariy intro, dars intro, test q, dialoglar |
   "Kabutar qushcha", "Gu-gu!", "Kabutar the bird", "Hello! I am Kabutar.", "Goodbye, Kabutar!" — qurilgan kitoblarda Kabutar qatorlari: 3–4 yosh 12, 4–5 (en_45) 3, 5–6 yosh 13, 6–7 (en_67) 25.
   en_34 testi: "Kabutar qushcha — mushukmi?" (javob: "Kabutar qushcha mushuk emas") — qahramon xato nomda ham o'rgatilmoqda.
   Rasm promptlari: "A pigeon looking around…" (en_56, en_67). Tuzatish: shu fayllar hali chiqarilayotgan bo'lsa tools/bogcha_yosh_rev99.py dagi ROBOT/«Kabutar»→«Kabu» almashtirishini
   ularga ham qo'llash yoki 3–4 / 5–6 kitoblarini kataloqdan olib tashlash.

7. [JIDDIY] manba: en_34, en_45, en_56, en_67 va *_enrich | uzbekcha matnlar | «sen» o'rniga «siz» shakli ommaviy: en_34 58 (+17 enrich), en_45 38 (+18), en_56 118 (+16), en_67 96 (+5) joy.
   Misol: "Qo'lingizni baland ko'taring!", "Ayiqcha sizga olma berdi. Nima deysiz?", "Ertalab bog'chaga keldingiz", "Yozda sizni juda sog'indim. Keling, salomlashamiz".
   Tuzatish: 3–4 va 5–6 kitoblari ham rev99 «warm()» filtridan o'tkazilsin (siz→sen, keling→qani, -ingiz→-ing, -ing/-ang buyruq→-/…).

8. [JIDDIY] qurilgan 2–3 yosh kitobi (23y) | barcha «Top-chi» testlari | dvigatel shabloni "Qani, toping: [en]Good morning![/en] qayerda?" — «siz» (toping) shakli, 68 qatorda (2–3 yosh eng kichik bolalar!).
   Tuzatish: bogcha_spiral.py dagi test shabloni "Qani, toping" → "Qani, top:" (CLASS/UZ matnlari).

9. [O'RTA] 23y | «O'g'il bola va qiz bola» (extra «🙋 Men kimman?») | "O'g'il bolalar, ayting: [en]Boy![/en] Qiz bolalar, ayting: [en]Girl![/en]" — «siz/ko'plik» shakli + bola yolg'iz o'ynaydi.
   Tuzatish: "Agar sen o'g'il bola bo'lsang, ayt: Boy! Qiz bola bo'lsang, ayt: Girl!".

10. [O'RTA] 45y | «Yovvoyi hayvonlar» (items.action) | action maydonlari «siz» shaklida: "Sherday «rrr» deng!", "Bo'riday «uu-uu» deng!", "Boyo'g'liday «uhu» deng!", "Qo'llaringni timsoh jag'iday oching-yum!",
    "Qorningni silab, «mm» deng!" (Yummy!), «Soyabon va kamalak»: "Rostdan soyabonni oching". Bir gap ichida ham aralash: "Qo'llaringni … oching-yum". Tuzatish: "de!", "och-yum!", "och".

11. [O'RTA] 45y scenario dialog `uz` | «Zoo», «Buvijonnikida», «Bog'ga chiqamizmi?», «Nonushta», «Tushlik» | "qarang, buvijon!", "mana, oling", "sut bering, iltimos", "keling, yotoqxonaga qaraymiz", "iltimos, non bering"; 6–7 scenariylarda: "mana, oling",
    "kiring, iltimos", "o'tiring, iltimos. choy ichasizmi?", "salat yeysizmi?", "savatingga sol. mana, oling" (bir qatorda sen+siz aralash). Kattaga hurmat bo'lishi mumkin, lekin qoida «sen»; kamida aralashmasin.
    Tuzatish: bola → buvi/ona: "qara, buvijon!", "mana, ol", "choy ichasanmi?", "kir, iltimos".

12. [JIDDIY] 67y | «O'n bir va o'n ikki» (item eleven) | TPR: "Show me eleven fingers!" — bolada 10 ta barmoq bor, bajarib bo'lmaydi (bola noto'g'ri tushunadi/uyaladi).
    Tuzatish: "Show ten fingers and one more finger!" yoki "Jump eleven times!".

13. [JIDDIY] 67y | «Men endi kattaman!» (item I am six.) | action_en "Show five fingers!" — olti deb aytib besh barmoq ko'rsattiradi. («Ismim va yoshim» da "Show me six fingers!" to'g'ri.)
    Tuzatish: "Show six fingers!" (bir qo'lda 5 + 1 barmoq).

14. [O'RTA] qurilgan 4–5 va 6–7 kitob | «🔁 Remember» («Esingdami») qatorlari | [en]…[/en] teg ICHIDA emoji bor: "[en]Do you remember? 🏃 run. Say: run. 🙆 head. Say: head.[/en]" —
    4–5 yoshda 90, 6–7 da 121 qator; 6–7 da raqamli emoji ham: "[en]Yes! 7️⃣ Sunday.[/en]". Ingliz TTS emoji nomini ("running person", "keycap seven") o'qishi yoki to'xtab qolishi mumkin → talaffuz/ovoz buzilishi.
    Tuzatish: [en] ichidan emojini chiqarib tashla (emoji faqat doskada qolsin); TTS ga yuborishdan oldin emoji filtri.

15. [O'RTA] qurilgan 6–7 kitob (+4–5) | ertak/ismlar | O'zbekcha atoqli so'zlar inglizcha [en] ichida: "[en]Zumrad. She is kind.[/en]", "[en]Qimmat. She is lazy.[/en]" (16 marta), "plov" (57), Malika (104), Anvar (55), Ali (169+36), Laylo (132+21) —
    ingliz TTS "Qimmat" ni "Kimmat", "Laylo" ni "Lailo" o'qiydi. Tuzatish: ismlarni [uz]…[/uz] bilan ajrat yoki [en] chegarasini ismdan oldin yop: "[en]She is kind.[/en]" va "Zumrad" o'zbekcha o'qilsin.

16. [O'RTA] 23y, 45y | «Mehmon o'yini» / «Salom va rahmat» | 4–5 yosh ovozida inglizcha sinf buyruqlari ("Repeat after me", "Your turn!", "One more time", "Great!") hech qachon o'zbekchada tushuntirilmagan; 2–3 yosh bunday buyruqlarni umuman eshitmaydi.
    Tuzatish: 2–3 yoshda "Look!" va "Listen!" ni (2 ta) bosqichma-bosqich kirit, 4–5 da sinf buyruqlari ro'yxatini birinchi darsda o'zbekcha tushuntirish bilan o'rgat.

---------------------------------------------------------------------------------------------------

## B. RASM / EMOJI VA SO'Z MOSLIGI (o'yin va test uchun)

17. [JIDDIY] 45y | «Salom va rahmat» (Goodbye!), «Mening uyim» (door), 23y «Bye va Thank you» (Bye!) | bir xil 🚪 emoji: Bye!, Goodbye! va door. 4–5 yosh kitobida Goodbye! va door bir xil rasm: bola "door" ni "xayr" deb,
    "Goodbye" ni "eshik" deb o'rganishi mumkin; testda "Find the picture" ikki variant ham 🚪 bo'lishi mumkin. Tuzatish: Bye/Goodbye = 👋 (qo'l silkitish, Hello dan farqlash uchun 🤚 yoki 👋🚶), door = 🚪.

18. [O'RTA] 45y «Bu nima? Bu — koptok», 67y «Menda bor» | item ball = ⚽, lekin "It's a ball." = 🏀 va "I have a ball." = 🏀 (bir darsda ikki xil koptok; 2–3 yoshda ball = ⚽).
    Tuzatish: hamma joyda ⚽ yoki umumiy 🏐; "I have a ball." ni ⚽ qil.

19. [O'RTA] 23y/45y/67y | doll | 🪆 (rus matryoshkasi) "doll"/qo'g'irchoq sifatida: 2–3 «Koptok va qo'g'irchoq», 4–5 «Robot, varrak, qo'g'irchoq», 67y «I have a doll.» — rasm matryoshka. Tuzatish: 🧸 teddy bilan chalkashmasligi uchun 👧/🎎 yoki chizilgan rasm (image) majburiy.

20. [O'RTA] 23y «Sakra va yugur», qurilgan «Katta bayram» | jump = 🦘 (kenguru), savol esa "Quyoncha hop-hop qilyapti. Bu nima?" — savolda quyon, variantda kenguru. Bayram testida ham xuddi shu savol. Tuzatish: "Kenguru hop-hop qilyapti" yoki jump = 🤸; quyon darsda 🐰 sifatida o'tilgan.

21. [O'RTA] 23y «Katta va kichik», 45y/67y | big = 🐘, small = 🐭; lekin elephant ham 🐘 (45y), mouse ham 🐭 (67y): bola "big = fil", "small = sichqon" deb o'rganadi, sifat emas, hayvon. Tuzatish: bir narsaning katta/kichik juftligi (🔴 katta/🔴 kichik, katta/kichik koptok) yoki 🐘/🐜 emas — yagona obyekt.

22. [O'RTA] 23y/45y | head = 🙆 ("OK ishorasi qilayotgan odam"), shoulders = 🤷 | bosh va yelka uchun mos emas (2–3 «Bosh va ko'zlar», 4–5 «Bosh, yelka, tizza»). Tuzatish: head = 🗣️/🧒 (bosh ajratilgan rasm), shoulders — haqiqiy rasm (image); doskada emoji bo'lmasa, image majburiy.

23. [O'RTA] 23y, 45y | pink = 🩷, grey = 🩶 | Unicode 15.0 (2022) emojilari: eski Android/iOS larda "□" chiqadi. Rang darsida yagona ko'rsatkich shu emoji — rang o'rgatilmaydi va test savoli ko'rinmaydi.
    Tuzatish: rangni 🟣 emas, rangli doira rasmi (image PNG) yoki CSS rang bloki bilan ber (pink/grey uchun emoji ishlatma). Xuddi shuningdek 🪆 🪥 🫓 🫖 🫴 (13.0–14.0).

24. [JIDDIY] 45y | «Yetti va sakkiz» → «🌈 Kamalak sanash» | doska "🔴🟠🟡🟢🔵🟣🟤" va ovoz "Kamalakda yettita rang bor!" — jigarrang (🟤) kamalakda YO'Q (ko'k-havorang-binafsha bor). Bola noto'g'ri fakt o'rganadi.
    Tuzatish: 🔴🟠🟡🟢🔵🟣 + indigo (🔵 ning to'q turi) yoki "Kamalakda ko'p rang bor" va 7 ni boshqa narsada ko'rsat (7 kun). «Ranglar qo'shig'i»da ham kamalak = pushti qo'shilgan — "kamalak" deb atama.

25. [O'RTA] 45y | «To'rt rangni eslaymiz» → «🚦 Svetofor o'yini» | Blue — «qo'lingni osmonga ko'tar» (svetoforda ko'k rang yo'q); Yellow — «chapak chal» (haqiqatda sariq = ehtiyot bo'l, tayyorlan). Keyin 67y «Yo'l qoidalari» da Red=Wait. Qoida ziddiyati.
    Tuzatish: o'yinni «Ranglar o'yini» deb ata yoki svetoforda faqat red/yellow/green qoldir (yellow = «sekinla»).

26. [KICHIK] 67y | «Katta sholg'om» | turnip = 🥬 (bargli sabzavot/pak-choy) — sholg'omga o'xshamaydi. Tuzatish: image chiz yoki 🥔/🧅 emas — kartoshka/piyoz bilan adashtirmaydigan chizma.

27. [KICHIK] 67y «Qayerda?» (next to / behind / in front of) | emoji 🐱📦, 🫣📦, 🧍📦 — nisbiy joylashuvni ko'rsatmaydi (bir xil "mushuk va quti"). Test "Mosh qutining orqasiga yashirindi" ham faqat matnga tayanadi. Bola 3 ibora orasidagi farqni rasmdan ko'ra olmaydi.
    Tuzatish: har bir ibora uchun alohida chizilgan rasm (cat behind/next to/in front of box) majburiy; emoji o'rniga 📦🐱 / 🐱📦 / 🐱 ➡️📦 tartibi bilan.

28. [KICHIK] 67y «Qayerda?» | "Mosh" ismi: "Mosh yana yashirindi!" — «yana» deyiladi, lekin Mosh hech qayerda tanishtirilmagan (4–5 darsida mushuk ismsiz). English qismda "the cat". Tuzatish: "Mushuk yana yashirindi" yoki Mosh ni oldin tanishtir.

29. [O'RTA] 45y «Qanday his qilyapsan?» | items: "How do you feel?", "I'm happy.", "I'm sad.", **"angry"** — to'rtinchi element qolip bo'yicha emas ("I'm angry." bo'lishi kerak); bola savolga "angry" deb bir so'z bilan javob beradi, to'liq gap o'rgatilmaydi. Tuzatish: "I'm angry.".

---------------------------------------------------------------------------------------------------

## C. BOSQICHMA-BOSQICH O'SISH (so'z → ibora → dialog) VA O'RGATILMAGAN SO'ZLAR

30. [O'RTA] 45y | 4-5 yosh kitobining 8–12-bo'limlari (Ovqat, Uy, Ob-havo, Odob, Mening kunim) | 5–6 yosh kitobidan ko'chirilgan: item.sentence + action_en + intro_en bor ("Dad makes hot soup.", "In spring, flowers are pink.", "Look out of the window!",
    "Where is the cat? I don't know!"), 1–7-bo'limlarda esa sentence umuman yo'q (123 ta item 170 dan sentencesiz). Qiyinlik bir kitob ichida keskin sakraydi (so'z → 5-6 so'zli gap, oraliq «ibora» pog'onasi yo'q); 4–5 yosh uchun 3 pog'onali ketma-ketlik buzilgan.
    Tuzatish: 8–14-bo'limlarda sentence ni 3–4 so'zgacha qisqartir ("I drink milk.", "It's sunny.") yoki bu bo'limlarni 5–6 yoshga qoldir.

31. [O'RTA] 45y | «Mening ismim» (U1 №3), «Qalaysan?» (№4) | 4 yoshli birinchi 5 darsda 3 ta to'liq ibora ("What's your name?", "My name is…", "Nice to meet you!"; "How are you?", "I'm fine!") — 2–3 yoshda faqat 1 so'zli elementlar edi (72/77),
    spec bir darsga 2–4 so'z/ibora deydi, lekin ibora-ibora sakrash 4 yoshga og'ir. 45y: 1 so'z 113, 2–3 so'z 49, 4+ so'z 8 (to'g'ri o'sish), lekin boshida ibora zichligi (U1: 7 ta ibora 13 dan) yuqori. Tuzatish: U1 ni «Hello/Goodbye/Thank you» + 1 ta «What's your name?», qolganini U3–4 ga ko'chir.

32. [O'RTA] 45y (4–5 yosh) | scenariy «Rasm darsida kamalak chizamiz» (U2) | dialogda bola "It's purple!", "It's green!" deydi, lekin "It's …" qolipi 45y da faqat U8 («It's a ball.») va U11 («It's sunny.») da o'rgatiladi — 6 bo'lim keyin. "Good job!" ham hech bir darsda element emas.
    Tuzatish: U2 da item sifatida "It's purple." / "It's green." (ibora) qo'sh, yoki dialogni "Purple!" / "Green!" ga soddalashtir.

33. [O'RTA] 45y | scenariylar «Bozorda meva olamiz» (U7) va «Uyda nonushta» (U9) | dialogda "Here you are!" — bu ibora 45y da faqat U12 «Menga berasanmi?» da element. Bola dialog qatorini yangi "so'z" sifatida eshitadi, lekin darsda oldin o'rgatilmagan.
    Tuzatish: "Here you are." ni U7 «Olma, banan, apelsin» ga o'tkaz yoki scenariyni U12 dan keyinga ko'chir. (Xuddi shunday: «Parkka kiyinamiz» da "Put on your hat!" element emas.)

34. [O'RTA] 45y sentence/dialog (4–5) | sentence qatorlarida o'rgatilmagan so'zlar: take, make(s), mouse, likes, every, day, hot, birthday, open, watch, sit, table, park, fly, flowers, leaves… (29 ta). Dialoglarda: job, ducks, ready, park (21 ta).
    67y sentence: sky, draw, helps, flies, new, works, buy, fast, tree, put, kind, long, high, much, song, after, visit, sick, people… (~140 ta qo'llanish; ularning ~60 tasi haqiqiy yangi, qolgani ko'plik/ismlar).
    Eslatma: intro_en/matn_en dagi say/ask/put/show — sinf tili, ular normal. Tuzatish: sentence ni faqat o'tilgan so'zlar bilan tuz; bitta yangi so'zdan ortiq kiritma ("sky" → "star" bilan "There are nineteen stars.").

35. [O'RTA] 67y «Kecha» («Kecha nima qilding?» U16) | bitta darsda 4 ta qaror o'tgan zamon: "I played football", "I went to the park", "I drew a picture", "I ate ice cream/ I saw …" — went/drew/saw/ate noto'g'ri fe'llar, 6–7 yoshga qiyin; oldin "I'm playing" (hozirgi zamon) faqat 1 bo'lim oldin o'tilgan.
    Tuzatish: o'tgan zamonni faqat 2 ta tartibli fe'l ("played", "visited") bilan, noto'g'rilarini (went/saw/ate/drew) chunk sifatida alohida 2 dars qilib ber, ularni vizual vaqt chizig'i (kecha/bugun) bilan bog'la.

36. [O'RTA] 45y va 67y | scenariy qatorlari "so'z" sifatida hisoblanadi | qurilgan kitobda 4–5: 227 "so'z" (170 item + 57 dialog qator), 6–7: 375 (256 + 119): scenariy qatorlari faqat 2 dars (o'z darsi + takror) ichida uchraydi — 4–5 da 21 ta, 6–7 da 59 ta ibora keyingi darslarda ≤1 marta qaytadi
    ("Hello, Grandma!", "Dad, where is the cat?", "Hello! My name is Anvar." va h.k.). Spiral (3 ta eski savol) bu qatorlarni yetarli takrorlamaydi. Tuzatish: dialog qatorlaridan kamida 1 tasini keyingi bo'limda «Remember» ga majburiy qo'sh; "so'z soni" statistikasida dialogni alohida sana.

37. [KICHIK] 23y | «Iltimos va uzr» (Please!, Sorry!) | qurilgan 2–3 kitobida bu ikki so'z faqat o'z darsida va 2 ta takror-bayramda uchraydi (jami 17 eslatma, 2 dars): eng kam takrorlanadigan so'zlar; boshqa so'zlar ~6.5 darsda uchraydi.
    Tuzatish: 11-bo'lim takrorini 1 ta so'z-o'yin bilan kengaytir, «Please/Sorry» ni oldingi darslarning rolli o'yinlariga kiritib ket.

38. [O'RTA] 45y | «Ko'z, quloq, og'iz, burun», «Qo'l, barmoq, oyoq», «To'rt rangni eslaymiz», «Ona, ota, oila» | 4–5 yosh 170 elementdan 41 tasi (24%) 2–3 yoshdagi so'zlarning aynan o'zi (head, eyes, ears, nose, mouth, hands, legs, red/blue/yellow/green, apple, banana, milk, water, baby, family…).
    Ba'zi darslar (masalan «Ko'z, quloq, og'iz, burun») to'liq takror, lekin «yangi» deb e'lon qilinadi → haqiqiy yangi so'z: ~129 ta. Ikki yosh orasida sinonimlar: mum/mother, granny/grandma, bye/goodbye — bola farqini bilmaydi.
    Tuzatish: takror darslarni "Eslaymiz" deb belgila va qisqartir; mum→mother, granny→grandma bog'lanishini («mum = mother») bitta jumlada tushuntir.

39. [KICHIK] 67y | takror elementlar ("week" 2 marta U2, "fourteen", "seventeen", "shop", "I can swim", "I am six" 2 marta) | bir kitob ichida dublikat: "week" U2 L1 va L3 da, "I am six" U8 va U10 da turlicha action bilan (qarama-qarshi, №13).
    Tuzatish: dublikatlarni birlashtir.

40. [O'RTA] 23y/45y/67y | dastur bo'shlig'i | Hech bir yosh guruhida harflar/tovushlar (alifbo, phonics: a-b-c, /k/ cat, /d/ dog) va shakllar yo'q; 6–7 yosh maktabga tayyorlik kitobida ham. Ingliz tilini erta o'rgatishda tovush-harf moslashuvi 5–7 yoshda markaziy.
    Tuzatish: 6–7 yoshga 3–4 dars "Letters and sounds" (A–Z qo'shig'i, boshlang'ich tovushlar, rasm bilan) qo'sh; 4–5 ga shakllar (circle, square, triangle) qo'sh.

---------------------------------------------------------------------------------------------------

## D. TEST VA O'YIN SIFATI (o'lchash uchun ham muhim)

41. [O'RTA] 23y, 45y | muallif testlari | Hamma testlar 2 variantli (23y 46/46, 45y 92/92), ya'ni tasodifiy topish ehtimoli 50%; qurilgan 2–3 kitobida 284 test, 4–5 da 454. Bola 3 ta ketma-ket testda tasodifan 12,5% ehtimol bilan hammasini topadi.
    Tuzatish: kamida 3 variant (4–5 yoshda), 2–3 yoshda 2 variant qolsin, lekin natijani «tasodif» tuzatish bilan hisobla (pastdagi o'lchash modeliga qara).

42. [O'RTA] 23y «Hello va Hi» | uch testning uchalasi ham bir xil ikki variantdan iborat ("Qaysi biri Hi?", "Hello! — qaysi biri?", "Qaysi rasm Hi!?"), va Hello/Hi ikkalasi «salom» — ma'no jihatidan ajratib bo'lmaydi; test faqat tovushni eslab qolishni o'lchaydi, tushunishni emas.
    Tuzatish: Hello va Hi ni bitta darsda tanishtir, test = "Do'sting 'Hi!' dedi. Sen nima deysan?" (Hi!/Bye!).

43. [O'RTA] 45y | «To'rt rangni eslaymiz», «Salom va rahmat» va hk. | qurilgan testlarda noto'g'ri variantlar boshqa toifadan: "Find the picture: red — 🚪 Goodbye!", "Where is it: blue? — 🤗 How are you?", "yellow — 🙋 My name is…": bola so'zni bilmasdan toifa bo'yicha topadi (rang so'zi — rang emoji).
    Tuzatish: distraktorlar faqat shu bo'lim/toifadan (red/blue/green).

44. [O'RTA] 67y | testlarning noto'g'ri variantlari | "🛑 Stop!", "🤫 Be quiet!", "📕 Close your book!", "❓🔢 How many?", "📆✅ Today is Monday." turli mavzuli savollarda takror distraktor (masalan «Can you fly?», «Sotuvchi senga olma berib…», «Xarid qilgan narsalarimizni nimaga solamiz?»).
    Natijada bola muloqotni emas, "begona" variantni chiqarib tashlashni o'rganadi. Tuzatish: har test uchun shu mavzudan 2 ta aqlli distraktor.

45. [O'RTA] 67y/45y scenariy savollari | javob savolning o'zida: "Ko'lda oltita o'rdak bor. Nechta?" (6 va 8 variant), "Ko'lda…", "Q: O'n barmoqni sana! ['🔟 …nine, ten!', '5️⃣ …four, five!']", "Burningni ushla! Bu nima?". Test hech narsani o'lchamaydi. Tuzatish: savolda rasm ko'rsat (🦆🦆🦆🦆🦆🦆) va "Nechta?" deb so'ra.

46. [KICHIK] 45y scenariy "Bozorda meva olamiz" | savol "Senga uchta banan kerak. Nima deysan? → 🍌 Three bananas, please." izohi esa "[en]Banana[/en] — banan." — izoh javob ibora (Three bananas, please) ni emas, bitta so'zni tushuntiradi. Tuzatish: izoh = "Three bananas, please. — uchta banan, iltimos."

47. [O'RTA] 67y | 9 ta test | variantlar bir xil ❓ emojili ("❓ What's the matter? / ❓🔢 How many? / ❓ What time is it?", «Ali bog'ni topa olmayapti…»); bola o'qiy olmaydi — variantlar ovozda o'qilmasa farqlab bo'lmaydi. Tuzatish: har variantga individual emoji (⏰ What time is it?, 🗺️ Where is the park?) — qurilgan test ovozida variantlar o'qilishini tekshir.

48. [KICHIK] 45y | «To'rt rangni eslaymiz» «Svetofor» va 23y «Yes/No» (Ha-yo'q o'yini) | ovoz o'zi javob beradi: "Robot Kabu mushukmi? Yo'q! No! Sen bolamisan? Ha! Yes!" — bola o'yinda tomoshabin, javob bermaydi (TPR/produktsiya yo'q). "Muzqaymoq yaxshi ko'rasanmi? Yes!" bolaning o'rniga javob beradi.
    Tuzatish: savolni ber, 3 soniya kut («Ha yoki yo'q?»), keyin javobni tasdiqla.

49. [KICHIK] 45y «Touch your nose!» «🕊️ Kabutar aytdi» | "Simon says" o'yini emas: barcha buyruqlar bajarilishi kerak ("Touch your head! Touch your ears! … Clap your hands!"), "Kabu says" filtri yo'q — o'yinning mohiyati (diqqat) yo'q, va lessonda o'rgatilmagan "head/ears/knees" buyruqlari qo'llanadi (faqat "Touch your nose!").
    Tuzatish: "Kabu says: Touch your head!" bajar, "Touch your ears!" (Kabu says yo'q) — bajarma; head/ears/knees alohida item sifatida kirit.

50. [KICHIK] 67y | «Maktabga qanday borasan?» | element "Stop!" kontekstsiz (transport darsiga mos emas; svetofor U13 da o'tiladi), keyin hamma testlarda distraktor sifatida qaytadi. Tuzatish: U4 dan olib tashla, U13 «Yo'l qoidalari» ga ko'chir.

---------------------------------------------------------------------------------------------------

## E. TPR / QO'SHIQ / ROLLI O'YIN YETARLILIGI

51. [O'RTA] 45y | TPR qamrovi | 170 elementdan faqat 85 tasida (50%) harakat (action/action_en) bor; U1–U7 da ko'p so'zlarda action yo'q: ranglar (7 ta: red/blue/yellow…), sonlar 4,6,7,8,9, yovvoyi hayvonlar (zebra, tiger, fox…), «Oilam» (hamma element), «Hissiyot»da qisman. 2–3 yoshda 77/77 (100%).
    4–5 yosh TPR ga eng muhtoj yosh. Tuzatish: har elementga harakat qo'sh (rang → mos narsaga teg, son → shuncha sakra).

52. [O'RTA] qurilgan kitoblar | qo'shiq | "Qo'shiq" belgili qatorlar: 23y 4 ta (38 dars), 45y 6 ta + 1 (50 dars), 67y 10 ta; ularning ko'pchiligi (masalan «Salom qo'shig'i», «Days of the week song», «Dasturxon qo'shig'i») aslida 1–2 qatorli chant — kuy/ritm ko'rsatilmagan, audio yo'q.
    Haqiqiy qo'shiq faqat «Head, shoulders, knees and toes». Tuzatish: har bo'limga 1 ta haqiqiy (kuyli) qo'shiq/chant (Hello Song, Colours song, Count 1–10 song) va audio-fayl.

53. [O'RTA] 23y | rolli o'yin | 38 darsdan faqat 4 ta rolli/dialogli topshiriq («Rolli o'yin: sovg'a», «Ali va Laylo», «Allalash o'yini», «Ayiqcha chanqadi»); scenariylar yo'q (spec 2–3 yoshga scenariy talab qilmaydi). 2 yoshli bolaga rolli o'yinda "Hello!" → "Thank you!" → "Bye!" ketma-ketligini mashq qildiradigan bitta oddiy kunlik vaziyat (ayiqcha mehmon) kerak.
    Tuzatish: 2–3 ga 2–3 ta 3-qatorli «ayiqcha bilan» rolli o'yin qo'sh (Hello → apple → Thank you → Bye).

54. [KICHIK] 67y «Zumrad va Qimmat» | ertakda bolaga nom bilan "lazy" (dangasa) yorlig'i beriladi ("She is lazy", "Qimmat doesn't help") va test "She is lazy" ni distraktor qiladi; ertakdagi tarbiyaviy g'oya saqlanadi, lekin salbiy sifat bolaga yopishmasligi uchun "She doesn't help" shaklida yumshat. Test javobi "Zumrad qanday qiz? kind" — to'g'ri.

---------------------------------------------------------------------------------------------------

## F. FAYL/TEXNIK (qisqa)

55. [KICHIK] 23y | rasm nomlari | 2–3 yosh (prefiks en23) kitobida 77 rasmdan 61 tasi "en34-u1-hello.png" ko'rinishida (3–4 yosh kitobidan olingan nom) — prefiks/yosh noto'g'ri, lekin brief rasm nomini o'zgartirmaslikni talab qiladi → faqat ogohlantirish: yangi rasm chizilganda en23- nomlash.

56. [KICHIK] bogcha_oyin_tekshir.py | validator | uchala y faylda "0 xato" beradi, lekin yuqoridagi № 3, 8, 10, 11, 14, 17, 24 kabi xatolarni ushlamaydi (🕊️, «siz» shabloni, emoji [en] ichida, bir xil emoji, fakt). Tuzatish: validatorga: [en] ichida emoji, 🕊️/Kabutar/qushcha, siz-shakl ro'yxati, bir kitobda bir emoji — ikki so'z (yuqori ahamiyatlilar uchun), action ichidagi son va "fingers" soni mosligi qoidalarini qo'sh.

---------------------------------------------------------------------------------------------------

## XULOSA (10 qator)

1. 2–3 yosh kitobi (50 dars, 77 so'z, ~6,5 dars/so'z, 100% TPR) pedagogik jihatdan eng sog'lom; asosiy nuqsonlar — 🕊️ belgisi (38 doska), "Qani, toping" (siz, 68 qator) va bir-nechta mos kelmaydigan emoji (🦘, 🙆, 🚪).
2. Eng katta tizimli xato: 4–5 yosh immersiyasi spec (2-pog'ona) emas, 4-pog'ona — ovozli qatorlarning 76% sof inglizcha, o'yin qoidalari ham inglizcha; 2–3 dan 4–5 ga o'tish "jarlik".
3. Qahramon qoidasi: Kabutar/🕊️/pigeon hamon ko'p joyda (45y da 4 ovoz qatori, 67y rasm promptlari, 3–4/5–6/6–7 manba kitoblarda 12–25 qator, har dars doskasida 🕊️).
4. «Siz» shakli: 3–4 va 5–6 manba kitoblarida yuzlab, y kitoblarda — action'lar (deng/oching), dialog tarjimalari (oling/bering/kiring) va dvigatel shabloni ("toping").
5. Ovoz teglari: [en] ichida emoji (4–5: 90, 6–7: 121 qator) va o'zbekcha ismlar (Zumrad/Qimmat/plov/Malika) — TTS talaffuzini buzadi.
6. Faktik/TPR xatolar: kamalakda jigarrang, "Show me eleven fingers!", "I am six" → besh barmoq, svetoforda ko'k.
7. Emoji moslik: bir emoji — ikki so'z (🚪, ⚽/🏀, 🐘, 🐭), noto'g'ri belgilar (🙆 head, 🪆 doll, 🥬 turnip), Unicode 15 (🩷🩶) rang uchun yagona ko'rsatkich.
8. O'sish: so'z → ibora → dialog tuzilishi 6–7 yoshda yaxshi (1 so'z 95 / 2–3 so'z 94 / 4+ 67), lekin 4–5 yoshda 8–14-bo'limlar 5–6 yoshdan ko'chirilgan sentence'lar bilan keskin qiyinlashadi; scenariylar o'rgatilmagan qolipni ("It's…", "Here you are") ishlatadi.
9. Takror: asosiy so'zlar ~6–8 darsda uchraydi (yaxshi), lekin scenariy iboralari (4–5 da 21, 6–7 da 59) ≤1 marta qaytadi; harf/tovush (phonics) va shakllar umuman yo'q.
10. Test sifati: 2 variantli (50% taxmin), begona toifadagi distraktorlar, savolda javob ochiq — shuning uchun foizni o'lchash uchun quyidagi tasodif-tuzatilgan model kerak.

---------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------

# BOLA TILNI NECHA FOIZ O'RGANGANINI O'LCHASH MODELI

## 0. Asosiy tushunchalar va ma'lumot manbalari

Platformada allaqachon mavjud ma'lumotlar (qurilgan kitob tuzilishidan):
- har dars: `words` ro'yxati (o'rgatilgan so'z/iboralar), tushuncha qatorlari, «Point to it!» o'yini (rasmni bosish), 3 ta dars testi,
  «🔁 Old question / Eski savol» (1, 3 va 7 dars oldingi so'zlar — kechiktirilgan eslab qolish), bo'lim takrori, «Katta bayram» (yakuniy takror);
- 4–7 yoshda scenariy (rolli o'yin) + 2–3 savol (ibora/dialog tushunish);
- harakat (TPR) topshiriqlari: ota-ona yoki kamera tasdig'i yo'q — shuning uchun «bajardi» tugmasi (ota-ona/bola bosadi) kerak.

Yangi (kerak bo'ladigan) hodisalar jurnali — har javob uchun bitta yozuv:
`{child_id, age_group, lesson_no, word_id, kind: tushunish|so'z|ibora|dialog|talaffuz|TPR, source: test|game|old|scenario|mic|parent, n_options, correct, time_ms, attempt_no, date}`.

Har so'z/ibora uchun 4 ta alohida o'lchov (bitta "to'g'ri/noto'g'ri" emas):
1. T — TUSHUNISH (receptive): eshitib to'g'ri rasmni/harakatni tanlaydi (test «Qaysi biri…», «Point to it!», TPR «bajardi»).
2. S — SO'Z/IBORA ISHLAB CHIQARISH (productive): o'zi aytadi (mikrofon yozuvi bor-yo'q, 2–3 yoshda ota-ona tasdig'i; «Say:» qadamida bola qaytarganini «bajardi» tugmasi/mikrofon bilan qayd).
3. E — ESLAB QOLISH (retention): kamida 3 dars (yoki 2 kun) keyin «Old question» yoki bo'lim takrorida to'g'ri javob.
4. R — TALAFFUZ (pronunciation): ASR (nutqni tanish) ishonch bahosi yoki ota-ona 3 pog'onali bahosi (aniq / yaqin / tushunarsiz). Faqat 4–5 yoshdan; 2–3 yoshda hisobga QO'SHILMAYDI.

## 1. Tasodif (taxmin) tuzatishi — barcha test natijalari uchun

Variantlar soni k bo'lsa (2–3 va 4–5 yoshda asosan k=2, 6–7 da k=3–4), xom aniqlik a (to'g'ri/jami) ni tuzat:

    a_adj = max(0, (a - 1/k) / (1 - 1/k))

Misol: k=2, a=0,75 → a_adj = 0,50. k=3, a=0,67 → a_adj = 0,50. Shunda 50% tasodifiy "bilim" foizga aylanmaydi.
Bitta so'zga kamida 3 ta alohida urinish (turli kontekst: dars testi, o'yin, eski savol) bo'lsa — shu so'z "o'lchangan" hisoblanadi; bo'lmasa "hali o'lchanmagan" (foizga kirmaydi, ota-onaga «hali yetarli ma'lumot yo'q» ko'rsatiladi).

## 2. So'z darajasidagi o'zlashtirish (m_w)

Har so'z w uchun:

    T_w = tuzatilgan o'rtacha aniqlik, so'nggi 4 ta tushunish urinishi (test + o'yin + TPR), yangi urinish og'irligi 1,0; eski 0,7; undan eski 0,5
    S_w = so'nggi 3 ta ishlab chiqarish urinishi: aniq = 1,0; yaqin = 0,5; tushunarsiz = 0 (ota-ona/ASR)
    E_w = «Old question» va takror testlari bo'yicha tuzatilgan aniqlik (faqat ≥3 dars/2 kun oldingi urinishlar)
    R_w = talaffuz bahosi o'rtachasi (0–1), faqat 4–5 va 6–7 yoshda

Yosh bo'yicha og'irliklar (yig'indi = 1):

| Yosh | T tushunish | S ayta oladi | E eslab qolish | R talaffuz | Izoh |
|---|---|---|---|---|---|
| 2–3 | 0,50 | 0,20 | 0,30 | 0 | Asosiy maqsad — eshitib tanish; talaffuz o'lchanmaydi (bola nutqi tuzilmagan, ASR ishonchsiz) |
| 4–5 | 0,40 | 0,20 | 0,30 | 0,10 | So'z + qisqa ibora; talaffuz "yaqin" darajasi yetarli |
| 6–7 | 0,30 | 0,25 | 0,25 | 0,20 | Ibora/dialogda ishlab chiqarish va talaffuz muhim |

    m_w = wT·T_w + wS·S_w + wE·E_w + wR·R_w            (0…1)
    So'z "o'zlashtirilgan" deb hisoblanadi, agar m_w ≥ 0,70 VA kamida bitta kechiktirilgan (E) urinish to'g'ri bo'lsa
    (bu bitta tasodifiy to'g'ri javobni "o'zlashtirish" deb hisoblashga yo'l qo'ymaydi).

## 3. Yosh bo'yicha: nimani o'lchash va foiz formulasi

Umumiy foiz (kitob bo'yicha, "Til foizi"):

    Til_foizi = 100 · Σ_w (m_w · v_w) / Σ_w v_w

v_w — so'z og'irligi: yangi so'z/ibora 1,0; dialog qatori (scenariy) 1,5 (ibora + kontekst); takroriy (2–3 yoshdan keyingi) so'z 0,5 (qayta hisoblanmasin).
Foiz faqat O'LCHANGAN (≥3 urinish) so'zlar bo'yicha emas, hamma so'zlar bo'yicha hisoblanadi; hali o'tilmagan so'zlarning m_w = 0, shuning uchun foiz "dastur bo'yicha"
darajani ko'rsatadi. Qo'shimcha "o'tilgan qismga nisbatan" foiz ham beriladi (faqat o'tilgan darslar bo'yicha).

### 2–3 yosh (77 so'z; hamma so'z 1 so'zli, 50 dars)
O'lchanadigan: (a) tushunish — eshitib rasmni bosish (qurilgan «Point to it!» + 3 test/dars, jami 284 test); (b) so'z — "Say:" qadamida bola qaytardi (ota-ona tasdig'i: «Ayta oldi / hali yo'q»);
(c) TPR — buyruqni eshitib to'g'ri harakat (ota-ona tugmasi); (d) eslab qolish.
Formula: Til_foizi_2-3 = 100 · mean_w(0,50·T_w + 0,20·S_w + 0,30·E_w); TPR natijasi T_w ga qo'shiladi (T_w = 0,7·test + 0,3·TPR, harakat so'zlari uchun: jump, run, clap, dance, sleep, eat, drink, Go/Stop).
Maqsad: 2–3 yosh uchun 100% emas, "faol lug'at" 30–40 so'z (~50% foiz) yaxshi natija; "tushunadigan" so'zlar ko'proq bo'lishi tabiiy.

### 4–5 yosh (227 birlik: 170 so'z/ibora + 57 dialog qatori)
O'lchanadigan: tushunish (rasm tanlash), so'z, qisqa IBORA (3–4 so'zli: "What's your name?", "Apple, please!"), talaffuz (soddalashtirilgan), qisqa dialog (scenariy savollari: 2–3/ta).
Formula: so'zlar va iboralar alohida:
    So'z_foizi   = 100 · mean(m_w) — yagona so'zlar (113 ta)
    Ibora_foizi  = 100 · mean(m_w) — 2+ so'zli elementlar (57 ta) + scenariy qatorlari
    Til_foizi_4-5 = 0,55·So'z_foizi + 0,45·Ibora_foizi
Scenariy natijasi: Dialog_foizi = 100 · (to'g'ri scenariy savollari, tasodif tuzatilgan) / (jami savollar) — Ibora_foiziga 40% og'irlik bilan qo'shiladi.

### 6–7 yosh (375 birlik: 256 so'z/ibora/gap + 119 dialog qatori)
O'lchanadigan: tushunish (inglizcha savol→javob), ibora, dialog (scenariy: rol o'ynash, javob tanlash), talaffuz (ASR), gap tuzish (sentence ni takrorlash).
Formula: Til_foizi_6-7 = 0,25·So'z + 0,30·Ibora + 0,30·Dialog + 0,15·Talaffuz, bunda
    So'z = 1 so'zli elementlar; Ibora = 2–3 so'zli; Dialog = 4+ so'zli gaplar va 17 scenariy qatorlari (savol + takror-bayram);
    Talaffuz = ASR/ota-ona o'rtachasi (talaffuz bahosi har ibora uchun 3 darajali: 1,0 / 0,5 / 0).

## 4. Daraja (ota-ona uchun tushunarli) va nazorat qoidalari

| Til foizi | Daraja | Ota-onaga matn |
|---|---|---|
| 0–19 | Tanishuv | Bola endi eshitishni o'rganyapti |
| 20–39 | Boshlang'ich | Ba'zi so'zlarni tanib, takrorlaydi |
| 40–59 | Rivojlanmoqda | Ko'p so'zni tushunadi, qisqa iboralarni aytadi |
| 60–79 | Yaxshi | So'z va iboralarni ishonchli ishlatadi |
| 80–100 | A'lo | Yosh dasturini mustahkam o'zlashtirgan |

Qoidalar (adolatsiz past/yuqori foizni oldini olish):
- Kamida 5 ta o'lchangan so'z bo'lmaguncha foiz ko'rsatilmaydi ("ma'lumot to'planmoqda").
- Bir kunda bir so'z uchun 3 tadan ortiq urinish bitta kun deb hisoblanadi (bola "qayta urinib" foizni oshirmasin).
- Xato yo'q jazosi: 5 ta ketma-ket noto'g'ri bo'lsa, so'z "qayta o'rgatish" ro'yxatiga tushadi va keyingi dars boshida qaytariladi (foiz pasaymaydi, faqat m_w yangilanadi).
- Faollik past bo'lsa (hafta davomida 2 kundan kam) foiz "eskirgan" deb belgilanadi (E_w qiymati vaqt bilan kamayadi: E_w ← E_w · 0,95^(hafta bo'yicha o'tgan kunlar/7)).

## 5. Ota-onaga ko'rsatiladigan 6 ko'rsatkich

1. **Til foizi** (katta raqam, doira diagramma) — yuqoridagi formula bo'yicha, haftalik o'zgarish (+X%).
2. **Tushunadigan so'zlar** — "47 / 77 so'z" (T_w ≥ 0,7): eshitib rasm/harakatni topadi. Yonida "yangi: 6 ta bu hafta".
3. **Ayta oladigan so'z va iboralar** — "21 so'z, 8 ibora" (S_w ≥ 0,7): ro'yxat, bola aytgan misollar ("apple", "Thank you!").
4. **Eslab qolish** — "kechiktirilgan savollarga 78%" (E): bola 3+ kun oldingi so'zlarni qanchalik eslaydi; "takrorlash kerak: red, sheep, Please!" (eng past 5 ta so'z).
5. **Talaffuz** — 4–5 va 6–7 yoshda: "aniq 62% / yaqin 28% / mashq kerak 10%" (R); 2–3 yoshda bu ko'rsatkich o'rniga **"Harakat bilan javob (TPR)"** — "Jump! Clap! Stop! buyruqlarining 85% ini bajaradi".
6. **Faollik va izchillik** — "bu hafta 5 kun, 42 daqiqa, 9 dars; 12 kunlik seriya" + "Keyingi qadam: ota-ona bilan o'ynash taklifi" (dars «boshqa_usul» dan: "uyda onang bilan Wash your hands! deb ayt").

(Qo'shimcha, ixtiyoriy 7-ko'rsatkich: "Eng yaxshi mavzu / qiyin mavzu" — bo'lim bo'yicha o'rtacha m_w, bola qiziqishini ko'rsatadi.)

## 6. Joriy etish uchun minimal talablar

- Test hodisalariga `word_id`, `n_options`, `kind`, `lesson_no`, `age_group` yoz (hozir faqat "to'g'ri/noto'g'ri" bo'lsa, tasodif tuzatilmaydi).
- Qurilgan test qatorlariga so'z identifikatori qo'sh (`words[].say`), "Old question" belgisi (`🔁`) saqlansin — E_w uchun shu kerak.
- 2–3 yoshda "bajardi / aytdi" tugmalari (ota-ona rejimi), 4–5 yoshda mikrofon + 3 darajali baho; 6–7 yoshda ASR (agar ishonchi past — "yaqin").
- №8, 14, 15 (siz-shakl, [en] ichida emoji, ismlar) tuzatilmaguncha talaffuz (R) ni 4–5 yoshda hisobga QO'SHMA — TTS/ASR bahosi noto'g'ri ketadi.
- Dastlabki 2 hafta "kalibrovka": foizni ota-onaga ko'rsatmay, o'rtacha m_w taqsimotini yig'ib, daraja chegaralarini (20/40/60/80) real ma'lumotga moslab sozla.

---------------------------------------------------------------------------------------------------
Fayl: /tmp/kids_critic/til.md  |  Tekshirilgan topilmalar: 56  |  Skriptlar: /tmp/kc/*.py (vaqtinchalik)
