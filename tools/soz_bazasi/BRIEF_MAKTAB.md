# So'z bazasi — MAKTAB so'zlari (1–11-sinf til o'yinlari) — tarjimon uchun topshiriq (REV695)

Avval `tools/soz_bazasi/BRIEF.md` ni o'qi: chiqish formati, til qoidalari (artikl, yozuv turi) va talablar AYNAN o'sha.
Farqlari:

## Kirish
`tools/soz_bazasi/xom_mN.json` — maktab til kurslari uchun chizilgan lug'at rasmlari: {id, fayl, sozlar:[...]}.
`sozlar` aralash tilda (o'zbekcha ma'no + ba'zan inglizcha/fransuzcha/nemischa/ispancha/ruscha asl so'z). Tushunchani shulardan aniqla.

## Qaror
- QOLDIR: lug'at so'zi bo'la oladigan har qanday ot, fe'l, sifat, ravish yoki turg'un qisqa birikma — MAVHUM bo'lsa ham
  (ekologik, migratsiya, tartibsizlik, huquqshunos, uy vazifasini bajarmoq) — chunki rasmi bor va o'yin maktab o'quvchilari uchun.
- TASHLA: tuslangan fe'l shakllari («aytdim», «men edim», «borib keldim»), bog'lovchi va grammatik qoliplar («shuning uchun ham», «shunga ko'ra»),
  to'liq gaplar, atoqli otlar, bir so'z bilan 11 tilda aniq berib bo'lmaydigan iboralar, bolalar uchun nomaqbul so'zlar,
  va ishonchli tarjima qila olmaydiganlaring. Bir xil tushuncha ikki marta kelsa — bittasi qoladi.

## Chiqish
`tools/soz_bazasi/qism_mN.json` va `tools/soz_bazasi/tashlandi_mN.json` — format BRIEF.md dagidek, QO'SHIMCHA maydonlar bilan:
- "turkum": BRIEF.md dagi ro'yxatdan; mos kelmasa "boshqa".
- "soz_turi": "ot" | "fel" | "sifat" | "ravish" | "ibora"
- "daraja": 1 (1–4-sinf, A1) | 2 (5–8-sinf, A2–B1) | 3 (9–11-sinf, B1–B2)
Shakl qoidalari:
- ot: de/fr/es/ar da aniq artikl bilan (BRIEF.md dagidek).
- fe'l: lug'aviy shakl — en: «meet» (to siz), de: «treffen», fr: «rencontrer», es: «conocer», ru: «встречать», tr: «tanışmak»,
  ar: masdar «ال» bilan («اللقاء») yoki o'tgan zamon 3-shaxs emas — masdarni tanla; zh/ja/ko: lug'aviy shakl (ja: «あう», ko: «만나다»).
- sifat: erkak jinsi birlik lug'aviy shakl (de: «klein», fr: «petit», es: «pequeño», ru: «маленький», ar: «صغير» artiklsiz).
- ja: hiragana/katakana (kanji yozma). uz: o‘ g‘ uchun ‘ belgisi.
`tekshir.py` otlardan artikl talab qiladi: "turkum":"harakat" bo'lmasa de/fr/es/ar da artikl bo'lishi shart. Shuning uchun
fe'llarga "turkum":"harakat" qo'y; sifat/ravish/iboralar uchun tekshiruvdan o'tish maqsadida ham "turkum":"harakat" EMAS, balki
"turkum":"boshqa" qo'y va `python3 tools/soz_bazasi/tekshir.py --maktab tools/soz_bazasi/qism_mN.json` bilan tekshir (bu rejimda artikl faqat soz_turi "ot" bo'lganda talab qilinadi; arabcha izofa — ikkinchi so'zi «ال» li birikma — ham qabul qilinadi).
0 xato bo'lishi shart. Commit qilma, boshqa fayllarga tegma.
Hisobot (qisqa, o'zbekcha): nechta qoldi, nechta tashlandi, shubhali tarjimalar (til + so'z).
