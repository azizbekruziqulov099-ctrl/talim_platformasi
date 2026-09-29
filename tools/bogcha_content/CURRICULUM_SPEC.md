# Bog'cha kitobi — MUALLIF formati (curriculum JSON)

Muallif faqat MAZMUNNI yozadi. Dvigatel (`tools/bogcha_spiral.py`) undan to'liq kitob yasaydi:
har darsga «🔁 Eslaymiz» (oldingi darslardan takror), yangi bilim qatorlari, o'yin, aralash test
(yangi + eski savollar: 1, 3 va 7 dars oldingi), har bo'lim oxirida TAKRORLASH darsi va kitob oxirida
KATTA BAYRAM (yakuniy takror) darsi. Shuning uchun muallif takrorni o'zi yozmaydi.

```json
{
  "subject": "Ingliz tili",            // fan nomi (katalogda chiqadi)
  "lang": "en",                         // "en" | "ru" | null (matematika, atrof-muhit: null)
  "age": "3-4 yosh",                    // "2-3 yosh" … "6-7 yosh"
  "book_title": "Hello, friend! 3–4 yosh",
  "prefix": "EN",                       // kitob kodi prefiksi, 2–3 lotin harf: EN, RU, MT, AM
  "units": [ UNIT, ... ]                // 8 ta bo'lim
}
```

UNIT:
```json
{ "name": "Salomlashamiz", "emoji": "👋", "lessons": [ LESSON, LESSON, LESSON ] }   // bo'limda 3–4 dars
```

LESSON (= saytdagi bitta mavzu):
```json
{
  "name": "Hello va Bye",               // QISQA, kitob ichida TAKRORLANMAYDIGAN nom (2–5 so'z)
  "goal": "Bola hello va bye so'zlarini eshitib qaytaradi",
  "intro": "Kabutar qushchaning kirish so'zi (ovoz, 1–3 gap). Qiziqtiruvchi: hikoya, sir, savol.",
  "items": [ ITEM, ... ],               // YANGI bilim: tilda 2–4 so'z/ibora, matematika/atrof-muhitda 2–3 tushuncha
  "extra": [ ROW, ... ],                // ixtiyoriy: qo'shimcha qator (qo'shiq, dialog, o'yin, tajriba, sanash o'yini)
  "tests": [ TEST, ... ]                // ixtiyoriy (matematika/atrof-muhitda MAJBURIY, 3–5 ta): muallif savollari
}
```

ITEM:
```json
{
  "say": "Hello!",                      // TIL fanida: o'rganiladigan so'z/ibora (inglizcha yoki ruscha). Boshqa fanda: tushuncha nomi (o'zbekcha).
  "uz": "salom",                        // o'zbekcha ma'nosi / qisqa izoh
  "emoji": "👋",                        // aniq mos emoji (rasm o'rnida). Sonlarda 3️⃣ yoki 🍎🍎🍎 kabi.
  "image": "en34-u1-hello.png",         // rasm fayl nomi: <prefiks kichik><yosh 2 raqam>-u<bo'lim>-<so'z>.png
  "image_prompt": "A cute cartoon child waving hello, soft flat colors, white background, no text, square",
  "action": "Qo'lingizni silkiting!",   // ixtiyoriy: harakat (TPR)
  "explain": "…"                        // IXTIYORIY tilda; MATEMATIKA/ATROF-MUHITDA MAJBURIY: ovozda aytiladigan tushuntirish (2–4 gap)
}
```

ROW (extra): `{"turi": "tushuncha"|"topshiriq", "sarlavha": "…", "matn": "ovoz…", "doska": "ekran yozuvi\nsatr2", "sodda": "…", "boshqa_usul": "…"}`

TEST (muallif savoli):
```json
{ "q": "Savatda 🍎🍎🍎 bor. Nechta olma?", "options": ["3️⃣ uch", "2️⃣ ikki"], "answer": 0, "why": "To'g'ri: bir, ikki, uch — uchta olma." }
```
- `options`: 2 ta (2–3, 3–4, 4–5 yosh), 3 ta (5–6 yosh), 3–4 ta (6–7 yosh). Har variant: EMOJI + qisqa so'z.
- `answer`: to'g'ri variant indeksi (0 dan). Dvigatel tartibni o'zi aralashtiradi.

QOIDALAR
- Bola O'QIY OLMAYDI: hamma narsa ovoz bilan. Ovoz matnlarida til so'zlari FAQAT `[en]…[/en]` yoki `[ru]…[/ru]` ichida
  (items.say ni dvigatel o'zi teglaydi; intro/extra/tests/explain matnlarida o'zingiz teglang).
- O'zbek tili: lotin, to'g'ri imlo (o', g' uchun '), mehrli: «keling», «qani», «barakalla». Qahramon — Kabutar qushcha («Gu-gu!»).
- Mavzular yoshga mos, oddiydan murakkabga. Har dars oldingisiga tayanadi. Kitob oxirida bola hamma so'zni/tushunchani biladi.
- Test savollari faqat shu kitobda O'TILGAN narsalardan.
- Matn uzunligi (bitta ovoz matni): 2–4 yosh ≤ 220 belgi, 4–5 ≤ 300, 5–7 ≤ 400.
- Faqat to'g'ri JSON (izohsiz), UTF-8.
