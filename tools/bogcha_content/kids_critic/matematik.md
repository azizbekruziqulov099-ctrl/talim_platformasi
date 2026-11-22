# Matematika (mt_*) — tanqidchi hisoboti (bolalar matematikasi metodisti + sanash/hisoblash inspektori)

Tekshirilgan fayllar: mt_23, mt_23y, mt_34, mt_45, mt_45y, mt_56, mt_67, mt_67y (tools/bogcha_content/). Hamma fayl build_books orqali qurilgan holatda (jami 8 kitob, 1 133 dars qatori to'plami, 837 noyob test, 6 000+ qator) Python skriptlar bilan tekshirildi.
`bogcha_oyin_tekshir.py` hamma 8 faylda "0 xato" beradi — lekin quyida ko'rsatilgan o'yin xatolari (bir nechta to'g'ri javob, nishon-rasm nomuvofiqligi) shu tekshiruvdan o'tib ketgan.

Avtomatik tekshiruvda XATO TOPILMAGAN joylar (to'qima emas, skript natijasi):
- Eshak/donkey/🫏: 8 faylning birortasida yo'q. TOPILMADI.
- Sanoq chegarasi: so'z va raqam bo'yicha tekshirildi (2–3: ≤3, 3–4: ≤5, 4–5: ≤10) — chegaradan oshgan son YO'Q. (Faqat "ko'p" tushunchasi 4–5 ta emoji bilan ko'rsatilgan, qarang #43.)
- Emoji soni = javob: "nechta/qoldi/hammasi" so'zli ~100 noyob savol va 34 ta "a ± b = ?" ifoda — hammasida emoji soni va to'g'ri javob mos. Qo'shish/ayirish natijalari hammasi to'g'ri. TOPILMADI.
- Variantlar soni: 2–3, 3–4, 4–5 yosh — 2 ta; 5–6 — 3 ta; 6–7 — 3–4 ta. Yoshga mos. TOPILMADI.
- Test javob harfi mavjudligi, takror variant matni: xato yo'q.
- Matn uzunligi limiti (220/300/400): oshgan qator yo'q.

======================================================================
JIDDIY (bola noto'g'ri o'rganadi yoki o'yin ishlamaydi)
======================================================================

1. [JIDDIY] mt_56.json va mt_67y.json (1–40 bo'lim) | "Ko'p, kam, teng" (L9) | "Kam" qadamida OVOZ: "🐤🐤🐤 — uchta, 🐤 — bitta... bitta jo'ja bor joyda kam", DOSKA va rasm esa "🍎🍎 Kam" (rasm: "A small basket with only two red apples"). Ovoz bilan doska umuman mos emas. Kirishda "ikki sincap yong'oq terdi", "Teng" qadamida "endi sincaplar yarashadi", doskada esa 🍪/🍎. Tuzatish: "Kam" qatorini doskaga 🐤🐤🐤 va 🐤 qo'yib yozish (yoki matnni "🍎🍎 — ikkita, 🍎🍎🍎🍎🍎 — beshta. Ikki beshdan kam" ga o'zgartirish); rasm prompti "two groups: 5 apples and 2 apples" bo'lsin; sincap hikoyasi bo'lsa doskada 🐿️🌰 ko'rinsin.

2. [JIDDIY] mt_23.json, mt_23y.json | "Ona va bolasi" (L7) | O'rdakcha emoji sifatida 🐥 (jo'ja!) berilgan. Ovozda "Bu — o'rdakcha, sariq", tushuncha doskasi "🐥 Kichik o'rdakcha", topshiriq doskasi esa "🐥 Kichik jo'ja" — bir darsning ichida o'zi-o'ziga zid. Test: "Kim katta? 🦆 o'rdak / 🐥 o'rdakcha". Bola jo'jani o'rdakcha deb o'rganadi (L11 "Onasini top" da 🐤 = jo'ja, ya'ni emoji ikki xil narsaga ishlatilgan). Tuzatish: 🐥 o'rniga rasm/emoji juftligi "🦆 + 🦆(kichik)" yoki mavzuni "Tovuq va jo'ja" ga almashtirish (L11 da bor), L7 da faqat 🦆 ona va rasm faylida o'rdakcha; doskadagi "Kichik jo'ja" yozuvini ovozga moslab tuzatish.

3. [JIDDIY] mt_23.json, mt_23y.json | "Katta ayiq, kichik ayiqcha" (L6) | "Kichik ayiqcha" = 🧸 (o'yinchoq ayiq, teddy). Ovozda "ayiqcha kichik, yumshoq, tip-tip yuradi", testda "Kim kichik? 🐻 ayiq / 🧸 ayiqcha". Bola ayiq bolasini o'yinchoq deb o'rganadi; rasm prompti ham "teddy bear cub" (arala). Keyin L35 "Ayiqlar oilasi: dada, oyi, kichik ayiqcha" doskada 🐻🐻🐻 (uchalasi bir xil o'lchamda) — "kichik" ko'rinmaydi. Tuzatish: rasm faylida katta va kichik jonli ayiq; emoji 🐻 + "kichik 🐻" (kichik shrift/nom bilan), 🧸 ni "o'yinchoq ayiq" alohida tushuncha qilib ajratish.

4. [JIDDIY] mt_23.json, mt_23y.json | "Qizil va sariq" (L13), "Ko'k va yashil" (L14) | L13 ovozi: "Olma — qizil" (umumlashtirish), L14 testi: "Olma qanday rangda? 🔴 qizil / 🟢 yashil → qizil". Olma yashil ham bo'ladi — yagona to'g'ri javob yo'q, bola "yashil olma xato" deb o'rganadi. Tuzatish: savolni "🍎 olma qanday rangda?" (aniq emoji) yoki "Qaysi rang qulupnayniki?" qilish; L13 matnini "Bu olma qizil" ga o'zgartirish.

5. [JIDDIY] mt_23y.json (L34, L35), mt_34.json (L2, L3, L6, L7) | "Ikki soni", "Uch soni", "To'rt soni", "Besh soni" — "🎲 Top-chi" o'yini | Nishonlar: "Ikki, Ikkita, Bizda ikkitadan" (doska 2️⃣ 🍐🍐 👀🙌); "Uch, Uchta, Uchta ayiq" (3️⃣ 🎈🎈🎈 🐻🐻🐻); "To'rt, To'rtta, To'rt oyoq" (4️⃣ 🐞🐞🐞🐞 🐾🐾🐾🐾); "Besh, Beshta barmoq, Beshta" (5️⃣ 🖐️ 🌸×5). "Uchta" ham 🎈🎈🎈 ga ham 🐻🐻🐻 ga to'g'ri keladi, "ikkita" ham 🍐🍐 ga ham 👀 ga — YAGONA to'g'ri javob yo'q. "Ikki" va "ikkita"ni 2–4 yoshli bola eshitib ajratolmaydi. Tuzatish: har nishon yagona bo'lsin ("ikki" faqat 2️⃣; "ikkita nok", "ikkita ko'z" — har biri o'z so'zi bilan), "bare Xta" nishonlarni olib tashlash; bir xil sonli ikki rasm bo'lsa ularni turli darslarga ajratish. Xuddi shu: mt_45.json L5 va mt_45y.json L22 "Olti, Oltita, Chumolining olti oyog'i" (🍩×6 va 🐜 ikkalasi "oltita").

6. [JIDDIY] mt_45.json (L12), mt_45y.json (L29) | "Sanab solishtiramiz" — "Top-chi" | Nishonlar: "Katta son — ko'p", "Kichik son — kam"; doska: "🎈🎈🎈🎈🎈 🎈🎈🎈  🍎🍎 🍎🍎🍎🍎🍎🍎" (ikki juft guruh). Qaysi rasm "katta son" ekani aniqlanmaydi (ikkala juftda ham katta va kichik guruh bor). O'yin yechilmaydi. Tuzatish: nishonlar "Beshta shar", "Uchta shar" kabi aniq; yoki doskada bitta juft va "7️⃣ 4️⃣" raqamlar.

7. [JIDDIY] mt_67.json va mt_67y.json | "Hammasi nechta?" (L17/L57), "Nechta qoldi?" (L18/L58), "Plyusmi yoki minus?" (L14/L54), "Chorak" (L24/L64), "So'm tangalari" (L33/L73), "Katak daftar" (L31/L71), "O'ngacha qo'shamiz" (L8/L48) — "Top-chi" o'yini | Nishon so'zlari savol/jumla: "Birga nechta?", "Nechta qoldi?", "Keldi — plyus", "Ketdi — minus", "Katta sondan sanab ketish", "To'rt chorak — butun", "Ikki yuz va besh yuz", "Chap va o'ng qo'l". Doskalar esa mavhum: "🧮 🚶", "🎈 🍪", "📈 📉 ✅", "💯🪙 💰", "🧠 🙌 🔟". Bola ovozdan qaysi rasmni bosishni bilolmaydi (jumla rasmga tushmaydi) — o'yin ishlamaydi. Tuzatish: har nishon doskadagi rasm bilan bir so'z: "Qo'shish — 🤲", "Minus — ➖", "Tanga — 🪙", "Chorak — 🍕".

8. [JIDDIY] mt_67.json (L9), mt_67y.json (L49) | "Nol va o'rin almashtirish" | Test: "1 + 8 ni oson yechish uchun qanday yozamiz? A) ➖ 8 − 1 B) 🔄 8 + 1 C) 🟰 1 = 8" — minus belgisi va ayirish ayirish darsidan (L11/L51) 2 dars OLDIN testda. Shuningdek "🟰 1 = 8" sanoqqa ziddir (xato variant, hech kim tanlamaydi). Tuzatish: distraktorlarni qo'shishga oid qiling ("8 + 1", "1 + 8", "8 + 8").

9. [JIDDIY] mt_67.json (L1), mt_67y.json (L41) | "O'nlik va o'n bir" | Darsning birinchi darsida: doska "🎀🔟 + ✏️ = 11", "🎀🔟 + ✏️✏️ = 12" — "+" va "=" belgilari L6 da o'tiladi; shuningdek ovozda cho'p 🥢, doskada ✏️ (qalam) — ovoz-doska mos emas; ovozda "Soat siferblatida eng katta son — o'n ikki 🕛" (soat L26 da o'tiladi); test varianti "0️⃣ yo'q" (nol bu kitobda, mt_67 alohida o'qilsa, o'tilmagan). Tuzatish: "+/=" ni olib, "🎀 va 🥢" ni so'z bilan; soat gapini olib tashlash.

10. [JIDDIY] mt_67.json (L37), mt_67y.json (L77) | "Qonuniyatni top" | Ovoz: "Qator o'sib borishi: 🟦, 🟦🟦, 🟦🟦🟦 ... Keyingisi — to'rtta kub!" — 🟦 kvadrat, "kub" emas (kub 3D, L21 'Shar va kub' darsida o'tilgan). Bola kvadrat=kub deb o'rganadi. Tuzatish: "to'rtta kvadrat" yoki 🧱 kubik emoji.

11. [JIDDIY] mt_23.json, mt_23y.json (L17–19) va mt_56/mt_67y (L21, L23) | "Doira", "Doira yoki kvadrat?" vs "Shar va kub" | 2–3 yoshda: "To'p dumaloq... Ular doiraga o'xshaydi. To'p dumalaydi", nishonlar "Doira dumalaydi ⚽➡️", "Kvadrat dumalamaydi 🎲" (🎲 = kubik, 3D); testlar "Qaysi biri dumalaydi? ⚽ to'p / 🎲 kubik". Ya'ni doira=to'p, kvadrat=kubik. 5–6 yoshda esa to'p = shar, kubik = kub. Bir bola ikki yoshda "to'p doira, kubik kvadrat" desa, 5 yoshda qayta o'rganadi; "kvadrat dumalamaydi" matematik jihatdan ma'nosiz (kvadrat tekis shakl). Shunga o'xshash: "Sovg'a qutisi" mt_23(y)/mt_34 da "kvadrat" (test: "Sovg'a qutisi qaysi shaklga o'xshaydi? 🟥 kvadrat"), mt_56/mt_67y da "🎁 → 🧊 kub". Tuzatish: 2–3 yoshda "to'p dumalaydi — dumaloq" va "kubik turadi — burchakli" (doira/kvadrat nomisiz), sovg'a qutisi misolini olib tashlash.

12. [JIDDIY] mt_34.json (L30), mt_45.json (L17), mt_45y.json (L11) | "O'ng qo'l va chap qo'l" | O'ng qo'l = ✋ (yoki 🥄✋/👉), chap qo'l = 🤚/👈: bu emojilar o'ng/chapni ajratmaydi (ikkalasi ko'tarilgan kaft). Testlar: "Qoshiqni qaysi qo'lda ushlaymiz? ✋ o'ng / 🤚 chap → o'ng" — chapaqay bola uchun noto'g'ri (ovozda "ko'pchilik ... ushlaydi" deyilgan, testda mutlaq). "Salomlashganda qaysi qo'lni beramiz? → o'ng" madaniy qoida (to'g'ri, lekin ko'rinish yo'q). Rasm promptlari: "A child raising the right hand" — rasm generatori o'ng/chapni tez-tez adashtiradi va bola yuzma-yuz turganda "o'ng" tomoni ekranning chap tomonida; nuqtai nazar aytilmagan. Tuzatish: savolni "Qaysi qo'lda soat/uzuk bor?" kabi rasmga bog'lash, ✋/🤚 ni belgi sifatida ishlatmaslik, "o'zing o'ng qo'lingni ko'tar" harakati bilan, rasmni tekshirib chiqish.

13. [JIDDIY] mt_23.json, mt_34.json, mt_45.json, mt_56.json, mt_67.json (5 ta kitob) | butun kitob | Qahramon hali ham "Kabutar qushcha" va "Gu-gu!": mt_23 (L1 kirish, L1 va L4 testi: "Kabutar qushcha nechta?"), mt_34 L1, mt_45 L1, mt_56 L1 va L29 ("Kabutar qushcha so'raydi"), mt_67 L1 va L27 ("Kabutar qushchaning kuni"); "Gu-gu!" kirishlar: mt_23 24, mt_34 28, mt_45 29, mt_56 33, mt_67 34 marta. Qoida: faqat "robot Kabu". Shu bilan birga bu kitoblarning takrorlash darslari "Bip-bip!" deydi (har kitobda 9 ta) — bitta kitobda ikki xil qahramon ovozi. y-fayllar (mt_23y, mt_45y, mt_67y) tuzatilgan, lekin ular bilan bir qatorda turgan mt_23/34/45/56/67 emas. Tuzatish: mt_*y dagi matnlarni mos kitoblarga ko'chirish; "Gu-gu" -> "Bip-bip", "Kabutar qushcha" -> "robot Kabu".

14. [JIDDIY] mt_23.json (55/422 qator), mt_34.json (68/495), mt_45.json (56/515), mt_56.json (75/624), mt_67.json (51/629) | butun kitoblar | Muloqot "siz" shaklida: "Qarang", "sanang", "ko'rsating", "qo'lingizni ko'taring", "Tayyormisiz?", "Esingizdami", "sizlarga", "Siz mushukcha bo'ling". Bir jumlada aralash ham bor: mt_56 L29 "«Kecha nima qilding?» Siz javob bering" (sen + siz). Tuzatish: mt_*y dagi "sen" variantlarini ko'chirish; o'zgartirish ro'yxati: -ing(iz) → -ing; -ing/-ang buyruq → -; "siz" → "sen".
    Qolgan "siz" izlari "y" fayllarda: mt_23y L1 "sizlarga", L49 "sanang"; mt_67y L8 "sakrang/aylaning", L12 "sanang", L19 "oching", L22 "bering", L33–34 "oching", L38 "sizniki" (9 qator).

15. [JIDDIY] mt_67.json (L26–27), mt_67y.json (L66–67) | "Soat bilan tanishamiz" | "Kichik mil" = 🕐, "Katta mil" = 🕛: bu emojilar butun soat siferblati (1:00 va 12:00), mil emas. Test: "Qaysi mil soatni ko'rsatadi? A) 🕐 kichik mil B) 🕛 katta mil", "Qaysi mil uzun va ingichka? 🕛 katta mil". Bola 🕐 ni "kichik mil" deb o'rganadi — soatni o'qishni tushunish o'rniga emoji yodlaydi. Tuzatish: rasm faylida millari ajratilgan siferblat (kichik mil qalin/qisqa rangli); doska/testda "🕰️ + ➡️ kichik mil" shaklida; emojini mil nomi sifatida ishlatmaslik.

16. [JIDDIY] mt_67.json (L27, L39), mt_67y.json (L67, L79) | "Butun soatlar" | Savollar javobni o'zi aytadi: "🕒 Katta mil 12 da, kichik mil 3 da. Soat nechchi? → 🕒 uch", "🕗 Kichik mil 8 da. Soat nechchi? → 🕗 sakkiz", "🕘 ... kichik mil 9 da → 🕘 to'qqiz", "Soat 5 bo'lsa, kichik mil qaysi sonni ko'rsatadi? → 5". Bola soat o'qimaydi: matndagi raqam yoki bir xil emojini tanlaydi. Tuzatish: stemda faqat 🕒 (matnsiz "Soat nechchi?"), variantlarda raqamlar ("3", "6", "9"), distraktor sifatida "yarim"ga o'xshash narsa emas.

======================================================================
O'RTA
======================================================================

17. [O'RTA] mt_45y.json | butun kitob tartibi | 4–5 yosh "y" kitobda sanash darsi L18 ("Beshgacha sanaymiz"), lekin undan oldin sanoq ishlatilgan: L1 "🔢 Vagonni sanaymiz (Nechta vagon?)", L4 test "🧱🧱 ikkita / 🧱🧱🧱🧱 to'rtta", L5 test "🧱🧱🧱 nechta kubik?", L9 test "⭐⭐⭐⭐ nechta yulduz?", L11 "Bizda nechta qo'l bor?". "Konkret → rasm → belgi" ketma-ketligi buzilgan (sanash o'tilmay savol). Tuzatish: sanoq blokini (L18–L26) boshiga ko'chirish yoki oldingi darslardagi nechta-savollarni "ko'p/kam" ga almashtirish.

18. [O'RTA] mt_67.json, mt_67y.json | "Qaysi misol to'g'ri? ✅" (L14/L54) | Stemda ✅, variantlarda ❌ ❌ ✅ — to'g'ri javob belgi bilan ko'rsatilgan. Savol hech narsani tekshirmaydi. Tuzatish: ✅/❌ ni olib tashlash.

19. [O'RTA] 35 ta noyob test (mt_23, mt_34, mt_45y, mt_56, mt_67, mt_67y) | savol emojisi = to'g'ri javob emojisi | Misollar: "Qaysi faslda qor yog'adi? ❄️ → ❄️ qish", "Soatning son yozilgan yuzi nima deyiladi? 🕰️ → 🕰️ siferblat", "Bosh barmoq va jimjiloq orasi? 🖐️ → 🖐️ qarich", "Narsa qancha turishi? 🏷️ → 🏷️ narx", "Kunlar va oylar jadvali? 📅 → 📅 kalendar", "Daftardagi kichik kvadrat? 🔲 → 🔲 katak", "Pitsa 4 teng bo'lak. Bir bo'lagi? 🍕 → 🍕 chorak", "🍎 olmaning juftini top! → 🍎 olma", "🧤 qo'lqopning juftini top → 🧤", "👉 qaysi tomonga? → 👉 o'ngga", "⬆️ strelka → ⬆️ yuqoriga", "🔴🟡🔴🟡🔴 keyingisi → 🟡". Bola emojini moslashtiradi, tushunchani emas. Tuzatish: stemdagi emoji o'rniga ovozda tavsif; yoki savoldagi emojini variantlardagi barcha emojiga o'xshatib berish.

20. [O'RTA] 25 ta test (mt_34, mt_45, mt_45y, mt_56, mt_67, mt_67y) | bema'ni distraktorlar | "🧵 ip", "🍎 olma" (soat savolida), "🙈 ko'zni yumamiz", "🎲 tashlaymiz", "😴 uxlaymiz" (labirintda), "🧱 devorni buzamiz", "🍴 yeb ko'ramiz", "🙈 qaramaymiz" (teng bo'laklarni tekshirish). Misol: "Qaysi mil soatni ko'rsatadi? 🕐 kichik mil / 🕛 katta mil / 🧵 ip", "Soatning yuzi? 🧵 ip / 🍎 olma / 🕰️ siferblat". 3 variantdan 1 tasi javob bo'lishi uchun chinakam chalg'ituvchi variant kerak (masalan "raqamlar", "mil"). Tuzatish: distraktor sifatida shu darsdagi boshqa tushuncha.

21. [O'RTA] Hamma 8 fayl (jami 289 kirish qatori: mt_23 24/33, mt_23y 39/52, mt_34 28/37, mt_45 29/38, mt_45y 41/54, mt_56 32/41, mt_67 32/41, mt_67y 64/81) | har dars "kirish" qadami | Ovozda hikoya ("daraxtda olmalar bor", "sharlar olib keldim", "ikki sincap yong'oq terdi", "ayiqlar oilasi", "ikkita lentam bor"), doskada esa faqat "🕊️ + dars nomi". Ovozda aytilgan narsa doskada ko'rinmaydi. Y-fayllarda qahramon robot Kabu, doskadagi belgi esa 🕊️ (kaptar) — robot emas. Tuzatish: kirish doskasiga hikoyadagi 1–2 emoji ("🌳🍎", "🎈", "🐿️🌰") va 🤖.

22. [O'RTA] mt_67.json va mt_67y.json (qo'shish/ayirish bo'limlari) + mt_56/mt_67y | "tushuncha" qadamlarida misol faqat ovozda | L6/L46 "Qo'shish" (doska "🤲 Qo'shish", ovozda 🍎🍎 va 🍎 → 🍎🍎🍎), L7/L47 "Rasmli misol" (doska 🖼️; ovozda 🎈🎈 + 🎈🎈🎈), L9/L49 "O'rin almashtirish" (ovozda 🍎🍎+🍎🍎🍎🍎🍎=7; doska 🔄), L11/L51 "Ayirish" (ovozda 🐦×5 → 🐦×3; doska 👋), L12/L52 (🍩×3), L13/L53 (🐸 sakrash), L14/L54 ("3 ❓ 2 = 5"), L34/L74 (🪙🪙🪙), L37/L77 (🔺🟥🟥🔺... qatori); mt_56 L12 (🍪🍪🍪🍪, doska "➖ Bittaga kam"), L13 (🐤🐤🐤🐤, doska "👉 Keyingi son"), L37 (➡➡⬆, doska "🗺 Yo'lni kuzatish"). Bola o'qiy olmaydi: misol doskada bo'lmasa ko'ra olmaydi. Tuzatish: har misolni doskaga yozish ("🍎🍎 ➕ 🍎 🟰 🍎🍎🍎").

23. [O'RTA] mt_23y.json (L44, L45) | "Teng emas", "Tenglashtiramiz" | Topshiriq ovozi: "Uchta o'yinchoq va ikkita olma ol... Kimga yetmadi?", "Sen sotuvchi bo'l. Har bir o'yinchoqqa bittadan olma ber"; doska: "🐰🐰🐰 🥕🥕 Teng emas / 🐶 🦴🦴". O'yinchoq/olma vs quyon/sabzi — ovoz bilan doska mos emas.

24. [O'RTA] mt_23.json, mt_23y.json (L43 "Juftlab qo'yamiz"), mt_34.json (L11) | "kosa" = ☕ | Ovozda "har bir kosaga bitta qoshiq", "Kosa uchta, qoshiq uchta"; emoji ☕ (issiq ichimlik/piyola), test "☕☕☕ nechta kosa?". Kosa (🥣) emas, choy piyolasi. Tuzatish: ovozda "piyola", yoki 🥣.

25. [O'RTA] mt_23.json, mt_23y.json (L9 "Paypoq jufti") | Ovoz: "Bu ikki paypoq bir xil. Ular — juft! Bittasi o'ng oyoqqa, bittasi chap oyoqqa kiyiladi." Paypoq o'ng/chap bo'lmaydi (poyabzal bo'ladi). Bola "paypoq o'ngi/chapi bor" deb o'rganadi. Tuzatish: gapni "ikkala oyoqqa bittadan kiyamiz" ga o'zgartirish. (L10 da poyabzalda to'g'ri.) Shuningdek "Poyabzal jufti — ular bir xil" aslida ko'zgudagi aks (o'ng va chap) — "bir xil" emas.

26. [O'RTA] mt_45.json (L18), mt_45y.json (L35) | "Chapdan boshlab sanaymiz" | "🐤🐤🐥🐤 — kichik jo'ja nechanchi? → 🥉 uchinchi" (mt_45) va "🐤🐤🦆🐤 — o'rdakcha nechanchi?" (mt_45y): 🐤 va 🐥 deyarli bir xil emoji, "kichik" farqi ko'rinmaydi; 🦆 kattalar o'rdagi (o'rdakcha emas), 🐤 jo'ja. Tuzatish: turli hayvonlar qatori (🐤🐤🐱🐤 — "mushuk nechanchi?").

27. [O'RTA] mt_45.json (L15–16), mt_45y.json (L32–33) | "Birinchi, ikkinchi, uchinchi", "To'rtinchi va beshinchi" | Testlar "🐰🦊🐢 — kim birinchi?", "🍎🍐🍌🍇🍓 — beshinchisi qaysi?" yo'nalish aytilmagan; "Chapdan" o'tilishi L18/L35 da (3 dars keyin). Qatorni o'ngdan sanaydigan bola "toshbaqa birinchi" deydi. Tuzatish: har savolda "chapdan" yoki raqamli chiziq.

28. [O'RTA] mt_34.json (L29), mt_45y.json (L10) | "Oldida va orqasida" | Doskada oldi/orqa bir qatorda chapga-o'ngga ko'rsatilgan: "🐶🧒 Oldida", "🧒🐶 Orqasida", test "Mushuk qutining oldida: 🐱📦 oldida / 📦🐱 orqasida". Keyingi darslarda ("O'ngda va chapda", L31) 🍐👈 / 👉🍎 bilan aynan shu emoji tartibi "chapda/o'ngda" bo'ladi. Bola "oldida" = "chap tomonda" deb o'rganadi. Tuzatish: rasm faylida chuqurlik (bola orqasidan itcha) ko'rsatilsin, emoji juftligi ishlatilmasin.

29. [O'RTA] mt_34.json (L29), mt_45y.json (L10) | test "Poyezdda vagon qayerda? 🚃 orqasida / 🚃 oldida" | "Nimaning" orqasida aytilmagan (lokomotivning? boshqa vagonning?), yagona javob yo'q. Tuzatish: "Lokomotiv oldida, vagon ... ?".

30. [O'RTA] mt_56.json va mt_67y.json (L24 "Dumalaydi yoki turadi") | Test: "G'isht qaysi shaklga o'xshaydi? 🧱 → 📦 quti (kub)" — g'isht kub emas (to'g'ri to'rtburchakli prizma). Kub tanlovi bola uchun noto'g'ri. "Sovg'a qutisi qaysi shakl? 🎁 → 🧊 kub" ham shubhali (ko'pincha to'g'ri burchakli quti). Tuzatish: "quti (kub)" -> "g'isht shakli" yoki 6–7 yoshda "to'g'ri to'rtburchakli quti".

31. [O'RTA] mt_45.json (L35), mt_45y.json (L51) | "Hikoyali masalalar" | Testlar rasmsiz sof matn: "Alida 2 ta mashina bor edi. Dadasi yana 2 ta berdi. Nechta bo'ldi?", "Tarelkada 4 ta pechenye... bittasini yedi", "Kimda qalam ko'p: Alida 6 ta, Zeboda 9 ta?", "«Kuchukcha yugurib keldi». Kuchuklar nima bo'ldi?" — 4–5 yoshga "konkret → rasm → belgi" bo'lmagan mavhum masala (raqamlar ovozda aytilgan). Tuzatish: stemga 🚗🚗 + 🚗🚗.

32. [O'RTA] mt_56.json | butun kitob mazmuni | 5–6 yosh uchun checklistda "10 ichida qo'shish/ayirish (rasm bilan), soat" bor. mt_56 da ayirish/qo'shish darslari yo'q (faqat "Sonning tarkibi", "Orqaga sanash"), soat yo'q, 11–20 yo'q (chegara 1–20 edi); qo'shish-ayirish va soat faqat mt_67 (L6–13, L26–27) da. Ya'ni 5–6 yoshli bola qo'shish/ayirish o'rganmasdan 6–7 kitobga o'tadi, yoki 5–6 yoshda umuman ko'rmaydi. Tuzatish: mt_56 ga 3–4 ta dars ("Qo'shish rasm bilan", "Ayirish rasm bilan", "Soat — butun soat") qo'shish yoki mt_67 dan bir qismini ko'chirish.

33. [O'RTA] mt_67.json (L38), mt_67y.json (L78) | "Tartib sonlar" | Test: "Poyga: 🐇 ➡️ 🦊 ➡️ 🐢. Kim birinchi?" — strelka zanjiri "kim kimdan keyin", "kim ortidan quvyapti" ma'nosini ham beradi; poygada 🐇 tez ekani ham qo'shimcha dalil, yagona tartib belgisi yo'q. "Navbatda siz oxirgisiz 🐢" (mt_67 — 'siz' + 🐢 bola emas). Tuzatish: raqamlangan qator 1️⃣2️⃣3️⃣.

34. [O'RTA] mt_67.json, mt_67y.json (L29/L69) | test "Bolalar maktabga qaysi oyda boradi? 🍂 sentabr / 🌷 may / ☀️ iyul / ❄️ yanvar" — bolalar maktabga yanvar va mayda ham boradi (iyul bundan mustasno); yagona javob yo'q ("boshlanadi" so'zi tushib qolgan). Tuzatish: "Maktab qaysi oyda boshlanadi?".

35. [O'RTA] mt_34.json (L22), mt_45.json (L26), mt_45y.json (L3, L42), mt_34/L22 | ➖ emoji "uzun lenta" sifatida ("➖➖➖➖ Uzunroq", "✏️➖➖➖ uzun") | ➖ — minus belgisi (6–7 yoshda "Minus belgisi" darsi, "Ayirish"); shu belgi uzunlik tasviri sifatida ishlatilgan. Shuningdek ➕/➖ belgilari belgi sifatida erta: mt_23y L40–45 "🐦➕🐦", mt_34 L13 "🥕➕🥕", "🦴➖🦴" (3–4 yosh), mt_56 L12–13, L15 "➖ Bittaga kam" (5–6 yosh, minus L51 gacha o'tilmagan), mt_56 L16 "🔴➕🔴🔴 Uchning tarkibi". Tuzatish: lentalar uchun 🟧🟧🟧 / 🪢 yoki rasm; ➕/➖ ni "qo'shamiz/olamiz" ning rasmli ishorasi sifatida emas, faqat belgi darsida.

36. [O'RTA] Hamma fayllar (1 242 "tushuncha" qatori) | "boshqa_usul" shabloni "Atrofingga qara: X qayerda bor? Barmog'ing bilan ko'rsat va ayt!" | X o'rnida tushuncha nomi qo'yilgani uchun ma'nosiz gaplar: "hech narsa yo'q qayerda bor?", "juda ko'p, joy qolmagan qayerda bor?", "ko'p narsadan bittasini olamiz qayerda bor?", "tarvuz katta, olcha kichik qayerda bor?", "daraxt katta, nihol kichik qayerda bor?", "har biriga bitta qayerda bor?" (mt_23y L2, L3, L5, L6, L7, L9...). Dars jonsiz ko'rinadi, bola uchun bema'ni. Tuzatish: shablonni faqat jismoniy narsalar uchun ishlatish; mavhum nomlar uchun alohida matn ("Qo'llaring bilan ko'rsat").

37. [O'RTA] mt_23y.json (L47–L51) va mt_23.json | "Doira va kvadrat" (L47) ikkinchi marta | 2–3 yoshli kitob 52 dars: L17–20 "Doira/Kvadrat" va L47–51 "Doira va kvadrat/Uchburchak/Burchaklarni sanaymiz/Shakldan uy" — takror va 3–4 yosh mazmuni (mt_34 L15–19 bilan so'zma-so'z bir xil, testlar ham). 2–3 yoshga "burchak sanash" va "uchburchak" mavhum; bir dars = 2 tushuncha qoidasi buzilgan (L48–49 da 3 ta). Tuzatish: L47–51 ni mt_23y dan olib tashlash yoki bir darsga qisqartirish.

38. [O'RTA] mt_67.json (L1, L2, L3, L4, L5; mt_67y L41–L45) | "O'nlik 🎀" | O'nlik = 🎀 (bitta bant emoji) va "🎀🥢🥢🥢🥢 = 14": bola 5 ta emoji ko'radi, "10 ta cho'p bog'langan"ni ko'rmaydi; 🎀🎀 = 20 testida ikki bant 20 ga teng. Sanash qoidasi (emoji soni = son) o'nlikda buziladi, rasmsiz ("faqat belgi") o'nlik tushunchasi shakllanmaydi. Tuzatish: rasm faylida 10 ta cho'p bog'lamini ko'rsatish, doskada "🔟" (o'nlik kartasi) + 🥢×birliklar.

39. [O'RTA] mt_56.json (L6/L27), mt_67y.json | "Kamalakda nechta rang bor? 🌈 → 7" | Kamalak emojisida 6–7 yo'l, bola sanab tekshirolmaydi; boshqa son savollarida emoji sanaladigan (🍎🍎) — bu yerda ko'rinishdan sanab bo'lmaydi. 4–5 yoshdagi mt_45 L6 da ham ("Kamalakda nechta rang?"). Tuzatish: savolni "Kamalakda ... rang" faktini matnda o'rgatib, tekshiruvga 7 ta rangli doira (🔴🟠🟡🟢🔵🟣⚪) bilan.

40. [O'RTA] mt_67.json (L21 "Uchburchak va to'rtburchak"), mt_67y.json (L61) | Test: "Hamma tomoni teng, 4 burchakli shakl qaysi? → 🟥 kvadrat" | Hamma tomoni teng to'rtburchak — romb ham. Kvadrat "hamma burchaklari to'g'ri va tomonlari teng". Tuzatish: "Hamma tomoni va hamma burchagi bir xil".

41. [O'RTA] mt_67.json (L38), mt_67y.json (L78) | "Eslaymiz" qatorlari va "Qatorda birinchi turgan bola eshikka eng yaqin" kabi mutlaq gaplar — ayrim variantlarda "Oxirgi: 🐢" (har oxirgi = toshbaqa). 6–7 yosh "oxirgi" = eng sekin degan stereotip; "Toshbaqa oxirgi keldi" faktiga bog'lanib, test "Navbatda siz oxirgisiz 🐢. Orqangizda nechta bola bor?" 🐢 bola o'rnini bosgan. Tuzatish: 🧒 bilan.

42. [O'RTA] mt_67.json (L27; L1 kirish) | Kirish: "Kabutar qushchaning kuni: soat 7 da uyg'onadi, soat 8 da bog'chaga uchadi, soat 1 da tushlik qiladi" — darsda faqat 3 va 8 o'rgatiladi; 7, 1 ko'rsatilmaydi; "soat 1 da tushlik" (13:00) 12/24 soatlik tushuntirishsiz. Tuzatish: darsda o'tilgan soatlar (3 va 8).

======================================================================
KICHIK
======================================================================

43. [KICHIK] mt_23.json, mt_23y.json, mt_34.json | "Ko'p" tushunchasi turlicha sonda ko'rsatilgan: 🍎×5 ("Ko'p"), 🧺🍎×4 ("to'la"), ✋🍬×4, 🕊️×4, 🚃×4 ("uzun poyezd") — 2–3 yosh chegarasi 3 ta; "ko'p" 4 va 5 bilan berilgan, hech qaerda nechta ekani so'ralmaydi, lekin 2–3 yoshli ularni sanashga urinadi. Tuzatish: "ko'p" uchun 4 ta (bir xil) yoki sanalmaydigan to'plam rasmi.

44. [KICHIK] mt_23.json, mt_23y.json (L22 "Uzun poyezd, qisqa poyezd") | "Qisqa poyezd tez-tez yuradi" — asossiz (noto'g'ri) fakt. Tuzatish: olib tashlash.

45. [KICHIK] mt_45.json (L37), mt_45y.json (L18) | "Uyada 5 ta jo'ja bor edi. 2 tasi yugurib ketdi" (test), "Uyada jo'jalar bor..." (topshiriq) — "Uyada" imlo xatosi (to'g'risi "Uyda"/"Hovlida"). Shuningdek mt_45 L3/L20 kirish: "biri oldida, biri keyinida" ("keyinida" yo'q so'z; "keyin" / "keyingisi").

46. [KICHIK] mt_56.json (L34), mt_67y.json (L34) | Kirish: "Men patchaman — juda yengilman", "Filning og'irligi shunchalik ko'pki" — grammatik noto'g'ri/g'alati ("patdekman", "shunchalik ko'pki"). Tuzatish: "Men patdek yengilman. Fil esa shunchalik og'irki, uni hech kim ko'tarolmaydi."

47. [KICHIK] Hamma fayllar (~900 "xulosa" qatori) | "Bugun biz Ikki, Ikkita, Bizda ikkitadan ni o'rgandik" / "Oxirgi son — nechta ni o'rgandik" / "Qo'shish, Plyus belgisi, Teng belgisi ni o'rgandik" — ro'yxat oxirida "ni" (shablon); iborali nomlar (jumlalar) bilan ayniqsa g'alati. Tuzatish: "Bugun biz shularni o'rgandik: ..." yoki darsning nomini aytish.

48. [KICHIK] mt_34.json (L13), mt_23y.json (L45) | "Tenglashtiramiz": "Teng qilish uchun nima qilamiz? A) ➖ bitta asal olamiz B) ➕ bitta asal qo'shamiz" ("🐻 🍯🍯") — ayiq ham qo'shilsa teng bo'ladi (variantda yo'q), yagona javob faqat variantlar tufayli; matn "ortiqchasini olamiz" o'rgatilgan. KICHIK, lekin "qo'shamiz/olamiz" ikkita yo'l (ham 🐻 qo'shish, ham 🍯 olish).

49. [KICHIK] mt_56.json, mt_67y.json | Kub rasm prompti: "A wooden toy cube with letters, a sugar cube" — "no text" qoidasiga zid (harflar). mt_67 L26 rasm "mt67-u6-minute-hand.png" bola o'qimaydi, lekin prompt "minute" mil nomi bilan... (kichik/katta mil emas). Tuzatish: "with colorful dots like a dice".

50. [KICHIK] mt_67.json, mt_67y.json (L33 "So'm tangalari") | "yuzlik" pul birligi sifatida: "Uchta yuz so'mlik 🪙🪙🪙. Hammasi qancha? → uch yuz so'm", "Bitta ikki yuzlik nechta yuzlikka teng?" — "yuz so'm", "yuzlik" terminlari aralash; bola sonlar 100 gacha deb o'rgangan, "yuz" so'zi o'tilmagan tushuncha (yuzlik = 100, shu kitobda yuz soni yo'q). Tuzatish: "bitta tanga — 1 yuzlik (konvensiya)" ni darsda tushuntirish yoki "tanga" bilan.

51. [KICHIK] mt_67.json (L14), mt_67y.json (L54) | Topshiriq: "«Mushuk bolaladi»" (ko'paydi) — 6–7 yoshga hayvon tug'ish ma'nosida "bolaladi" so'zi; o'rniga "mushukning bolasi tug'ildi"/"yana bitta mushukcha keldi".

52. [KICHIK] mt_23.json, mt_34.json, mt_45.json, mt_56.json, mt_67.json (barcha) va y-fayllar | Test javoblarining raw JSON dagi `answer` indeksi 0 ga juda moyil: mt_45 104/104, mt_67 130/130, mt_34 85/95, mt_23y 92/121, mt_67y 239/258 (build_books'dagi deterministik shuffle uni aralashtiradi: yig'ilgan javoblar A 55%, B 45% (2 variantli kitoblarda)). Agar boshqa vosita (masalan, JSON ni to'g'ridan-to'g'ri o'qiydigan) shuffle'siz ishlatilsa — to'g'ri javob har doim birinchi. Tuzatish: muallif JSON'ida ham `answer`ni aralashtirish.

53. [KICHIK] mt_56.json, mt_67y.json (L26–27) | "Haftaning boshlanishi/Payshanbadan yakshanbagacha" "Top-chi" nishonlari: "Dushanba" = 1️⃣, "Seshanba va chorshanba" = 📆, "Payshanba va juma" = 📆, "Shanba va yakshanba" = 🏖️ — raqam belgisi (1️⃣) yakka kun bilan, boshqalar juft kunlar bilan bir rasmda; bola 2 kun nomini bitta 📆 rasmga bog'laydi, "Seshanba"ni yakka bosa olmaydi. Tuzatish: har kun uchun alohida karta 1️⃣…7️⃣.

54. [KICHIK] mt_67y.json (L34 "Og'ir va yengil", L33) | "sodda" qatori "Eslaymiz"dan: "Keling, sekinroq: 🖐️ bu — bosh va jimjiloq orasi. Kaftni keng oching..." — og'irlik darsida qarich takrori (oldingi dars) — spiral takrordan bo'lsa ham "sodda" ovozi yangi mavzuga bog'lanmaydi. KICHIK, tartibni tekshirish.

======================================================================
XULOSA (10 qator)
======================================================================
1. Sanash/hisoblash to'g'riligi YAXSHI: emoji soni = javob, qo'shish/ayirish natijalari, sanoq chegarasi, variantlar soni, eshak — avtomatik tekshiruvda 0 xato (qarang tepada).
2. Eng jiddiy muammo — O'YINLAR: "Top-chi" nishonlari bir nechta rasmga mos keladi (#5, #6) yoki jumla bo'lib rasmga tushmaydi (#7); oyin_tekshir buni ushlamaydi.
3. Ovoz bilan doska mos emas: kirish qadamida 289 ta (#21), mt_67 qo'shish/ayirish tushunchalarida misol faqat ovozda (#22), mt_56 "Kam" da butunlay boshqa rasm (#1).
4. Qahramon/muloqot qoidasi 5 ta kitobda hamon buzilgan: mt_23/34/45/56/67 — "Kabutar qushcha", "Gu-gu", "siz" (#13, #14); faqat mt_*y tuzatilgan.
5. Tushunchalar noto'g'ri tasvirlangan: 🐥=o'rdakcha, 🧸=ayiqcha, olma=qizil, to'p=doira/kubik=kvadrat, 🟦=kub, 🕐/🕛=soat millari, ✋/🤚=o'ng/chap (#2,#3,#4,#10,#11,#12,#15).
6. O'tilmagan tushuncha oldinroq: mt_67 L1 da +/=, soat; L9 testida minus; mt_56 da ➖/➕ (#8, #9, #35); mt_45y da sanoq darsidan oldin "nechta" (#17).
7. Testlar o'zi javobni beradi: stem emojisi = javob emojisi (35 ta), ✅/❌, soat savollari matnda javob; distraktorlar bema'ni (#16, #18–#20).
8. Yagona to'g'ri javob yo'q joylar: "Olma qanday rangda?", "qaysi oyda maktabga boradi?", "poyezdda vagon qayerda?", "qoshiqni qaysi qo'lda", "birinchi" (#4, #34, #29, #12, #27).
9. Kitoblar tuzilishi: 5–6 yoshda qo'shish/ayirish/soat yo'q (#32); 2–3 yoshli kitob 52 dars va 3–4 yosh mazmunini takrorlaydi (#37).
10. Shablon jonsizligi: "boshqa_usul" 1 242 qatorda ma'nosiz ("hech narsa yo'q qayerda bor?"), "xulosa"da "ni o'rgandik" — dvigatel shablonini tuzatish tavsiya etiladi (#36, #47).
