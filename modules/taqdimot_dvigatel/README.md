# Taqdimot dvigateli

Mazmun («miya») → uslub × blok × animatsiya → PowerPoint (.pptx) va saytda ko‘rsatish.
AI faqat mazmunni yozadi; dizayn, chizmalar va animatsiyani shu dvigatel qiladi.

## Tuzilma

| Fayl | Vazifasi |
|---|---|
| `sxema.py` | Miya tuzilmasi (`taqdimot-miya/1`) va normallashtirish (AI xatolariga chidamli) |
| `namuna_ratsional.json` | To‘liq namuna: «Ratsional sonlar» ma’ruzasi |
| `uslub.py` | 11 oila × palitralar × 3 fon varianti × 14 animatsiya to‘plami; oila fan va darajaga qarab tanlanadi |
| `bloklar_joy.py` | Joylashuvlar (layout) va dizayn DNK: sarlavha qatori, karta, titul va bo‘lim slaydi variantlari |
| `tarjima.py` | Rus/ingliz taqdimotda dvigatelning tayyor yorliqlari («Ta’rif», «Javob:», «1-savol» ...) |
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
`POST /rasm-yuklash` (admin: ZIP, fayl nomi = kalit) · `GET /rasmlar?q=` ·
`GET /kutubxona` · `GET /kutubxona/{toplam}/{kod}` (tayyor miya) · `GET /kutubxona/{toplam}/{kod}/{oqituvchi|topshiriq|reja|javoblar}` (javoblar — faqat admin)

## Tayyor mavzular va rasmlar (paketlardan)
- `kutubxona/<toplam>/` — `reestr.json` + `miya/` (taqdimot-miya JSON), `oqituvchi/` (.md), `javoblar/`, `mustaqil/`.
  Hozir: `bmkn1305` — BMKN 1305, 39 mavzu (15 ma’ruza, 15 amaliy, 9 mustaqil ta’lim).
- `rasmlar/` — `kalit.webp` (fayl nomi = kalit) + `reestr.json` (tur: rasm / chizma, nom, izoh, tekshiruv).
- `malumot/` — chizmalar reestri, 118 element (IUPAC 2022) — keyingi chizma generatorlari uchun.
- Yangi paket kelganda shu tuzilishda yangi papka qo‘shiladi, kod o‘zgarmaydi.

## Rasmlarni moslash (`rasm_tanla.py`)
- Har yasashda: miyadagi noma’lum rasm kaliti kutubxonadagi eng yaqin rasmga almashtiriladi; topilmasa slaydda
  bo‘sh ramka chiqmaydi, `rasm_hisobot.yoq` ro‘yxatiga (tavsif + prompt) tushadi.
- Rasmsiz slaydga, matni rasm mavzusiga aniq mos kelsa (kamida 2 so‘z yoki shu rasmga xos so‘z, fan mos), kutubxonadan rasm qo‘yiladi;
  titulga mavzu rasmi. O‘chirish: `"rasm_avto": false`.
- AI ko‘rsatmasiga mavzuga yaqin kutubxona rasmlari ro‘yxati qo‘shiladi; `GET /korsatma` — to‘liq katalog bilan.
- Illyustratsiya (tur "rasm") ramkasiz, orqasida yumshoq shakl; chizma — oq kartada.

- Saytning umumiy rasm kutubxonasi (`modules/rasm_kutubxona`, ≈6000 shaffof illyustratsiya, o‘zbek/ingliz/rus/nemis nomlari)
  ham indeksda: lug‘at, galereya, jihoz, moslash bandlari nomi bo‘yicha rasm oladi; slaydga — faqat kuchli moslikda.

## Joylashuv va dizayn DNK (`bloklar_joy.py`)
- Slaydda `"joylashuv"`: `rasm_ong`, `rasm_chap`, `rasm_panel`, `rasm_katta`, `markaz`, `ustunlar`, `qatorlar`, `yon_sarlavha`,
  `standart`, `avto`. Mazmunga to‘g‘ri kelmasa yoki yozilmasa — dvigatel nomzodlardan tanlaydi, ketma-ket takrorlamaydi.
- Har taqdimotga urug‘dan: sarlavha qatori (chap, chiziq, tasma, markaz, raqam), karta (oila, yon, chiziq, soya),
  titul (6 xil), bo‘lim slaydi (5 xil). `yasa(..., dizayn={"titul": 2})` bilan qo‘lda berish mumkin; natijada `sahna["dizayn"]`.
- Animatsiya tanlanmasa slaydlarning bir qismi ikkinchi tinch to‘plam bilan chiqadi (`dizayn.anim2`).

## Fan bezaklari (fon motiflari)
`rasmlar/fonlar/<fan>_<n>.png` — shaffof fonli, qora chiziqli bezak, o‘rtasi bo‘sh (1920×1080). Dastur uni uslub rangiga
bo‘yab, past shaffoflikda fonga qo‘shadi. Fan kalitlari: `uslub.FAN_KALIT` (matematika, fizika, kimyo, biologiya, geografiya,
tabiiy, tarix, adabiyot, ona_tili, xorijiy_til, informatika, musiqa, tasviriy, texnologiya, jismoniy, tarbiya, pedagogika, umumiy).

## Sozlamalar (env)
`GEMINI_API_KEY` / `OPENAI_API_KEY` / `GROQ_API_KEY` — AI matn; `TAQDIMOT_AI_PROVIDERS=gemini,openai,groq`;
`TAQDIMOT_AI_RASM=1` + `OPENAI_API_KEY` — AI rasm chizish (ixtiyoriy); `TAQDIMOT_RASM_PAPKA` — rasm papkasi; `TAQDIMOT_KUTUBXONA` — tayyor mavzular papkasi.

## Kengaytirish
- Yangi chizma: `chizma.py` da funksiya + `CHIZMALAR` ga qator (AI ko‘rsatmasiga avtomatik qo‘shiladi).
- Yangi palitra: `uslub.py` dagi `YORUG` / `QORONGI` / `DOSKA` ga qator.
- Yangi blok: `bloklar.py` da `blok_*` + `BLOKLAR`, `yasash.reja_tuz` da o‘rni.
- Testlar: `tests/test_taqdimot_dvigatel.py`.

## Barcha fanlar uchun slayd turlari (`bloklar_fan.py`, `profil.py`)
lugat (so'z kartalari, tarjima bosganda), dialog, parcha (she'r/matn), vaqt_chizigi, xarita (O'zbekiston viloyatlari va
shaharlari / dunyo davlatlari — `malumot/xarita_*.json`, geoBoundaries ODbL va Natural Earth), tajriba, jarayon
(aylana / zanjir / qadam), galereya, guruhlash; o'yinlar: moslash, togri_notogri, bosh_joy, rasmda_nima.
Ichki rasmlar (lug'at so'zi, jihoz, voqea, bosqich) kutubxonadan o'zi topiladi. `profil.py` — fan va yosh bo'yicha AI ga
qaysi turlarni ishlatishni aytadi. Slaydlar orasida faqat fade (Morph yo'q).
