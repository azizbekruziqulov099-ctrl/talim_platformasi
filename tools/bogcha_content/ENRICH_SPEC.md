# Ingliz tili (bog'cha 3–7 yosh) — BOYITISH fayli formati (REV87)

Mavjud dastur fayllari (`en_34.json` … `en_67.json`) o'zgarmaydi. Har yosh uchun alohida
`en_XX_enrich.json` yoziladi — dvigatel (`tools/bogcha_spiral.py`) uni asosiy dastur bilan birlashtiradi.

## Immersiya (inglizchaga bosqichma-bosqich o'tish)
| Yosh | Pog'ona | Ovozli tushuntirish tili |
|---|---|---|
| 3–4 | 1 | o'zbekcha, so'zlar inglizcha |
| 4–5 | 2 | o'zbekcha + inglizcha sinf buyruqlari (Look! Listen and repeat! Good job!) |
| 5–6 | 3 | ASOSAN inglizcha; o'zbekcha faqat qisqa izoh va «Tushunmadim» tugmasida |
| 6–7 | 4 | TO'LIQ inglizcha; o'zbekcha faqat «Tushunmadim» tugmasida |

Shuning uchun 5–6 va 6–7 yosh uchun har bir so'z/iboraga oddiy inglizcha MISOL GAP, har darsga
inglizcha KIRISH kerak. 3–7 yoshning hammasiga — HAYOTIY VAZIYAT darslari (dialog, rol o'yini).

## Fayl tuzilishi
```json
{
  "lessons": {
    "<asosiy fayldagi dars nomi AYNAN o'zi>": {
      "intro_en": "Hello, friends! ... (2–3 qisqa gap, faqat 5–6 va 6–7 yosh uchun)",
      "items": {
        "<item.say AYNAN o'zi>": {"sentence": "The cat is small.", "action_en": "Wave your hand!"}
      },
      "tests_en": ["<har bir muallif testi uchun inglizcha savol, tartib bilan>"]
    }
  },
  "scenarios": [ SCENARIO, ... ]        // har bo'limga BITTA: jami 8 ta, "unit": 1..8
}
```
- `sentence`: 3–8 so'zli, bola tushunadigan, SHU KITOBDA yoki oldingi yoshlarda o'tilgan so'zlardan tuzilgan gap.
  So'z/iboraning o'zini ishlatsin (masalan `cat` → "I have a cat.", `Thank you!` → "Thank you for the apple!").
  `action_en` ixtiyoriy (TPR buyrug'i: "Jump!", "Clap your hands!", "Touch your nose!").
- `tests_en`: asosiy fayldagi `tests[i].q` ning inglizcha oddiy varianti (o'zbekcha so'zsiz). Variantlar o'zgarmaydi.
- 3–4 va 4–5 yosh fayllarida `lessons` bo'sh bo'lishi mumkin ({}), faqat `scenarios` yoziladi.

## SCENARIO (hayotiy vaziyat darsi)
```json
{
  "unit": 3,                                   // qaysi bo'lim oxiriga qo'yiladi (1–8)
  "name": "Do'konda: meva olamiz",             // o'zbekcha dars nomi (kitobda TAKRORLANMAYDI)
  "name_en": "At the fruit shop",
  "emoji": "🏪",
  "goal": "Bola do'konda odob bilan meva so'raydi va rahmat aytadi",
  "intro": "o'zbekcha kirish (1–2 gap, 3–4 va 4–5 yosh uchun)",
  "intro_en": "inglizcha kirish (1–2 gap, hamma yosh uchun)",
  "roles": ["Sotuvchi", "Bola"], "roles_en": ["Seller", "Child"],
  "scene": {"image": "en56-s3-fruit-shop.png",
            "image_prompt": "A cheerful fruit shop scene with a friendly seller and a child, cute cartoon scene for kids, soft flat colors, no text, square"},
  "dialog": [
    {"who": 1, "say": "Hello!", "uz": "salom", "emoji": "👋"},
    {"who": 0, "say": "Hello! Can I help you?", "uz": "salom! nima kerak?", "emoji": "🧑‍💼"},
    {"who": 1, "say": "Two apples, please.", "uz": "ikkita olma, iltimos", "emoji": "🍎🍎"},
    {"who": 0, "say": "Here you are.", "uz": "mana, oling", "emoji": "🫴"},
    {"who": 1, "say": "Thank you! Goodbye!", "uz": "rahmat! xayr", "emoji": "🙏"}
  ],
  "questions": [
    {"q": "Olma so'rash uchun nima deysiz?", "q_en": "You want apples. What do you say?",
     "options": ["🍎 Two apples, please.", "👋 Goodbye!", "6️⃣ I am six."], "answer": 0,
     "why": "To'g'ri! [en]Two apples, please.[/en]", "why_en": "Yes! Two apples, please."}
  ]
}
```
Qoidalar:
- Dialog uzunligi: 3–4 yosh — 3–4 qator, juda qisqa (1–3 so'z); 4–5 — 4 qator; 5–6 — 5–6 qator; 6–7 — 6–8 qator.
- Dialog shu bo'lim va oldingi bo'limlarda o'tilgan so'zlardan tuzilsin (+ ko'pi bilan 2 ta yangi oddiy ibora).
- `questions`: 2–3 ta. Variantlar soni: 3–4 va 4–5 yosh — 2 ta; 5–6 — 3 ta; 6–7 — 3–4 ta. Har variant: EMOJI + inglizcha ibora.
- Vaziyatlar HAYOTIY va bolaga tanish: bog'chada, uyda nonushta, do'kon, bozor, shifokor, bog'/park, tug'ilgan kun,
  mehmonga borish, avtobus, telefon qo'ng'irog'i, oshxona, hayvonot bog'i, sport, ob-havo va kiyinish, maktabga tayyorgarlik.
- Rasm nomi: `en<yosh 2 raqam>-s<bo'lim>-<qisqa-inglizcha-nom>.png` (kichik harf, tire). Prompt oxiri:
  `cute cartoon scene for kids, soft flat colors, no text, square`.
- `uz`: lotin, to'g'ri o'zbek imlosi (o' g' uchun ' belgisi). `say`, `sentence`, `*_en` — TO'G'RI, TABIIY ingliz tili.
- Faqat to'g'ri JSON, izohsiz, UTF-8.
