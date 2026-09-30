# Bog'cha ingliz tili kitobi — JSON format (bitta fayl = bitta yosh guruhi)

Top-level:
{
  "age": "3-4 yosh",             // "3-4 yosh" | "4-5 yosh" | "5-6 yosh" | "6-7 yosh"
  "book_title": "Hello, friend! 3–4 yosh",
  "topics": [ TOPIC, ... ]
}

TOPIC:
{
  "no": 1,                                   // 1..N
  "name": "Salom! Hello!",                   // o'zbekcha mavzu nomi (qisqa, 2-5 so'z), inglizcha qo'shimcha mumkin
  "goal": "Bola hello, bye so'zlarini eshitib qaytaradi va salomga javob beradi",
  "words": [ {"en": "hello", "uz": "salom", "emoji": "👋",
              "image": "en34-01-hello.png",
              "image_prompt": "A cute cartoon child waving hello, soft flat style, white background, no text"} ],
  "rows": [ ROW, ... ]                       // 12–18 qator, tartib bilan
}

ROW (ai miya varag'i qatori):
{
  "turi": "kirish" | "tushuncha" | "topshiriq" | "test" | "xulosa",
  "sarlavha": "Hello — salom",               // doska tepasida, qisqa
  "matn": "...",                             // O'QITUVCHI OVOZI (TTS o'qiydi). O'zbekcha, bolaga mehrli, qisqa gaplar.
                                             // Inglizcha so'z/gap FAQAT [en]...[/en] ichida: "Qani, men bilan ayting: [en]Hello![/en]"
                                             // tushunchada doska qatorlariga [1], [2] bilan ishora qilish mumkin (ixtiyoriy).
                                             // testda — savol matni (ovoz bilan o'qiladi): "Qaysi rasm [en]cat[/en]?"
  "doska": "👋 Hello!\nsalom",               // ekranda katta ko'rinadigan yozuv, har satr alohida. Emoji + inglizcha + o'zbekcha.
  "variantlar": "A) 🐱 cat\nB) 🐶 dog",      // faqat test: 3-4 va 4-5 yoshda 2 ta variant (A,B), 5-6 da 3 ta (A,B,C), 6-7 da 3-4 ta.
                                             // Variant = emoji + so'z (bola rasmni ko'rib tanlaydi). Inglizcha so'z [en] tegisiz.
  "javob": "A",                              // test: to'g'ri harf. To'g'ri javob o'rni aralash bo'lsin (hammasi A bo'lmasin).
  "yechim": "To'g'ri! 🐱 [en]cat[/en] — mushuk.",   // test: to'g'ri javobdan keyin ovoz aytadigan izoh (1-2 gap)
  "sodda": "...",                            // faqat tushuncha: soddaroq tushuntirish (ovoz)
  "boshqa_usul": "..."                       // faqat tushuncha: boshqacha — harakat/qo'shiq/o'yin orqali (ovoz)
}

Qoidalar:
- Bola O'QIY OLMAYDI: hamma narsa ovoz bilan (matn). Doska — ota-ona/tarbiyachi uchun ham yordam.
- Har mavzu: 1 kirish (qahramon Kabutar qushcha salom beradi, mavzuga qiziqtiradi) → 3–6 tushuncha (har birida 1–2 yangi so'z,
  "men bilan takrorla" 2 marta, harakat: "qo'lingizni silkiting") → 1–2 topshiriq (TPR o'yin: "Touch your nose!", sanab
  qo'shiq, "top-chi") → 3 test (3-4, 4-5 yosh) yoki 4–5 test (5-6, 6-7) → 1 xulosa (maqtov, takror, ertangi mavzuga qiziqtirish).
- Matn uzunligi: 3-4 yosh har qatorda ≤ 250 belgi; 4-5 ≤ 320; 5-6 ≤ 400; 6-7 ≤ 450.
- So'zlar Cambridge Pre A1 Starters lug'atiga mos, oddiy va aniq (apple, cat, red, one ...). Kerakli bo'lsa rus tili emas — faqat ingliz.
- O'zbek tili: lotin yozuvi, to'g'ri imlo (o‘ g‘ uchun ' belgisini ishlating: o'yin, g'ildirak), bolaga "siz" emas "sen" ham emas — mehrli "keling", "qani", "barakalla".
- Bir mavzudagi test savollari faqat shu mavzu so'zlaridan; variantlar ham oldin o'tilgan so'zlar.
- Emoji har so'zga aniq mos bo'lsin (🍎 apple, 🍌 banana, 🐱 cat, 🐶 dog, 🔴 red ...). Emoji bo'lmasa — yaqin ma'noli.
- image_prompt: inglizcha, bir xil uslub: "cute cartoon, soft flat colors, white background, no text, square". Fayl nomi:
  en<yosh ikki raqam>-<mavzu 2 xonali>-<so'z>.png (masalan en45-03-red.png). Har mavzuga yana 1 ta sahna rasmi:
  "image_scene": "en34-01-scene.png", "image_scene_prompt": "...".
- Faqat to'g'ri JSON (json.loads o'tsin), UTF-8, izohsiz.
