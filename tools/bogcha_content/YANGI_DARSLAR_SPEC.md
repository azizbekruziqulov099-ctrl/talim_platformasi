# REV110: yangi darslar (2–3, 4–5, 6–7 yosh) — yozuvchi uchun qo'llanma

Maqsad: platformada 2–3 yoshda 50, 4–5 da 80, 6–7 da 100 dars bo'lsin. Mavjud kitoblar (`en_23.json`, `en_45y.json`,
`en_67y.json`) O'ZGARMAYDI. Yangi darslar alohida «plus» faylga yoziladi va kitob oxiriga qo'shiladi:

| Yosh | Fayl | Bo'lim | Dars | Vaziyat (scenario) |
|---|---|---|---|---|
| 2–3 | `en_23p.json` | 3 | 7 | yo'q |
| 4–5 | `en_45p.json` + `en_45p_enrich.json` | 3 | 8 | har bo'limga 1 ta (3) |
| 6–7 | `en_67p.json` + `en_67p_enrich.json` | 7 | 24 | har bo'limga 1 ta (7) |

Dvigatel (`tools/bogcha_spiral.py`) har darsga takror, aralash test, bo'lim takrori va yakuniy bayramni O'ZI qo'shadi.
Siz faqat MAZMUN yozasiz. Format — `CURRICULUM_SPEC.md` (dastur) va `ENRICH_SPEC.md` (boyitish) bilan bir xil.

## Dars rejasi
Bo'lim, dars nomi, maqsad, so'zlar (`say`, `uz`) va rasm nomlari (`image`) — `reja_rasmli.json` da TAYYOR. Ularni
AYNAN o'zgartirmay oling. `image_prompt` berilgan bo'lsa — o'zini qo'ying; `null` bo'lsa — rasm allaqachon bor, o'sha
so'zga mos qisqa inglizcha prompt yozing (oxiri: `, soft 3D cartoon for kids, white background, no text, square`).

## Qahramonlar va ohang
- Ustoz-qahramon: **robot Kabu** («Bip-bip!»). Qush emas, robot (antenna, temir qo'llar, batareyka).
- Bolaga **«sen»** deb mehr bilan: «Qani, ayt!», «Barakalla!», «Sen zo'rsan!». «Siz», «keling» ISHLATMANG.
- Doimiy bolalar: **Ali** (o'g'il) va **Laylo** (qiz). Misol va dialoglarda shular qatnashadi.
- O'zbek madaniyatiga mos: non, palov, piyola, choy, buvijon, bobojon, Navro'z. Cho'chqa, spirtli ichimlik — yo'q.
- O'zbekcha: lotin, to'g'ri imlo (o', g' uchun ' belgisi). Ingliz tili — tabiiy va to'g'ri.

## Teglar (MAJBURIY)
O'zbekcha ovoz matnida (intro, extra.matn, sodda, boshqa_usul, tests.q, tests.why, scenario intro/q/why) har bir
inglizcha so'z/ibora FAQAT `[en]…[/en]` ichida. `items.say`, `dialog.say`, `*_en` maydonlarida teg YO'Q.
Boshqa tillarga tarjima shu teglar orqali avtomatik bo'ladi — teg yo'qolsa, o'sha so'z tarjima bo'lmay qoladi.

## Uzunlik (bitta ovoz matni, belgilar)
2–3 yosh ≤ 200 · 4–5 yosh ≤ 280 · 6–7 yosh ≤ 380. Gaplar qisqa, bitta fikr.

## LESSON tuzilishi
```json
{"name": "…", "goal": "…", "intro": "…",
 "items": [{"say": "…", "uz": "…", "emoji": "…", "image": "…", "image_prompt": "…", "action": "Qo'lingni silkit!"}],
 "extra": [ROW],
 "tests": [TEST]}
```
- `intro`: 1–3 gap. Qiziqtiruvchi boshlanish: kichik sir, savol yoki hikoya. Masalan: «Bip-bip! Ali ertalab uyg'ondi,
  lekin nimadir unutdi. Topamizmi?»
- `items`: rejadagi so'zlar, tartibi o'sha. Har biriga ANIQ emoji. `action` — o'zbekcha harakat buyrug'i (TPR),
  2–3 yoshda HAR BIR so'zga, boshqa yoshda bor joyda.
- `extra`: 1 ta qator, `turi: "topshiriq"`. Navbatma-navbat: 🎵 qo'shiq / 🎭 dialog / 🎲 o'yin / 👀 «top-chi».
  `sarlavha` emoji bilan boshlanadi. `matn` — ovoz. `doska` — ekranda katta yozuv (emoji + inglizcha, har satr alohida).
  `sodda` — eng oson varianti (faqat bitta-ikkita ibora). `boshqa_usul` — uyda ota-ona bilan qilish (1 gap).
- `tests`: 2 ta. Faqat shu va oldingi darslarda o'tilgan so'zlar. Variantlar: 2–3 va 4–5 yosh — 2 ta; 6–7 — 3 ta.
  Har variant: EMOJI + qisqa inglizcha. `answer` — to'g'ri indeks (har xil o'rinda bo'lsin). `why` — maqtov + izoh.

## Gapirish mashqi (eng muhim)
Bola har darsda O'ZI GAPIRSIN. Shuning uchun:
- `extra.matn` oxirida bolaga savol yoki «Endi sen ayt: [en]…[/en]» bo'lsin.
- 4–5 va 6–7 yoshda vaziyat dialogi bola gapiradigan rolga ega (`who: 1` — bola). Bola qatorlari qisqa, ilgari o'tilgan
  so'zlardan.
- 6–7 yoshda har `items[].sentence` — bola takrorlay oladigan 3–7 so'zli gap.

## Faqat 6–7 yosh: `en_67p_enrich.json`
`ENRICH_SPEC.md` formatida: har dars uchun `intro_en` (1–2 gap, robot Kabu gapiradi: "Beep-beep! Hello, friends! I am
Kabu the robot…"), har `items` uchun `sentence` (+ ixtiyoriy `action_en`), `tests_en` (har test uchun inglizcha savol),
`extras_en` (`sarlavha_en`, `matn_en`). Plus `scenarios`: har bo'limga 1 ta (`unit` — plus fayldagi bo'lim raqami 1..7),
dialog 6–8 qator, 2–3 savol (3 variant).

## Faqat 4–5 yosh: `en_45p_enrich.json`
`{"lessons": {}, "scenarios": [...]}` — har bo'limga 1 ta (`unit` 1..3), dialog 4 qator, 2 savol (2 variant),
`intro` (o'zbekcha) + `intro_en`.

## Vaziyat rasmi nomi
4–5: `en45-s15-<qisqa-nom>.png`, `en45-s16-…`, `en45-s17-…` (bo'lim tartibida).
6–7: `en67-s18-…` … `en67-s24-…`. Prompt: inglizcha, Ali va/yoki Laylo bilan, oxiri
`, soft 3D cartoon scene for kids, warm colors, no text, square`.

## Tekshirish
`python tools/bogcha_plus_check.py` — xato bo'lmasligi kerak.
