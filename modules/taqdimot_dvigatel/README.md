# Taqdimot dvigateli

Mazmun («miya») → uslub × blok × animatsiya → PowerPoint (.pptx) va saytda ko‘rsatish.
AI faqat mazmunni yozadi; dizayn, chizmalar va animatsiyani shu dvigatel qiladi.

## Tuzilma

| Fayl | Vazifasi |
|---|---|
| `sxema.py` | Miya tuzilmasi (`taqdimot-miya/1`) va normallashtirish (AI xatolariga chidamli) |
| `namuna_ratsional.json` | To‘liq namuna: «Ratsional sonlar» ma’ruzasi |
| `uslub.py` | 8 oila × palitralar × 3 fon varianti × 8 animatsiya to‘plami (1 560 kombinatsiya) |
| `bloklar.py` | Slayd-bloklar: titul, adabiyot, o‘yin, reja, bo‘lim, muammo, tarix, mazmun, xatolar, metodika, xulosa, test, yakun |
| `chizma.py` | Kod bilan chiziladigan 19 xil chizma (son o‘qi, ulush, tasma, daraxt, Venn, tarozi, grafik...) |
| `formula.py` | TeX formulalar (kasr, daraja, ildiz...) — PowerPoint va saytda bir xil |
| `olchov.py`, `metrika.json` | Calibri/Cambria kengliklari — matn qutiga aniq sig‘adi |
| `sahna.py` | Umumiy sahna modeli (1280×720) |
| `pptx_yoz.py` | Sahna → .pptx: animatsiya, triggerlar, giperhavolalar, Morph |
| `yasash.py` | Slaydlar rejasi va chizish |
| `excel.py` | Excel shablon ⇄ miya |
| `ai.py` | AI ko‘rsatmasi (sayt AI va ChatGPT uchun bitta matn), AI rasm (ixtiyoriy) |
| `rasmlar.py` | Rasm kaliti → fayl / bazadagi rasm / umumiy rasm kutubxonasi |
| `api.py` | `/api/taqdimot-dvigatel/*` |

## API
`GET /uslublar` · `POST /yasash` (sahna JSON) · `POST /pptx` · `POST /import` (.xlsx/.json) · `POST /ai` + `GET /ai/{ish}` ·
`GET /shablon.xlsx?namuna=1` · `GET /korsatma` · `GET /namuna` · `GET /fon/{kod}.jpg` · `GET /rasm/{kalit}` ·
`POST /rasm-yuklash` (admin: ZIP, fayl nomi = kalit) · `GET /rasmlar?q=`

## Sozlamalar (env)
`GEMINI_API_KEY` / `OPENAI_API_KEY` / `GROQ_API_KEY` — AI matn; `TAQDIMOT_AI_PROVIDERS=gemini,openai,groq`;
`TAQDIMOT_AI_RASM=1` + `OPENAI_API_KEY` — AI rasm chizish (ixtiyoriy); `TAQDIMOT_RASM_PAPKA` — rasm papkasi.

## Kengaytirish
- Yangi chizma: `chizma.py` da funksiya + `CHIZMALAR` ga qator (AI ko‘rsatmasiga avtomatik qo‘shiladi).
- Yangi palitra: `uslub.py` dagi `YORUG` / `QORONGI` / `DOSKA` ga qator.
- Yangi blok: `bloklar.py` da `blok_*` + `BLOKLAR`, `yasash.reja_tuz` da o‘rni.
- Testlar: `tests/test_taqdimot_dvigatel.py`.
