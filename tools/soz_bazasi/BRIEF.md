# So'z bazasi — tarjimon uchun topshiriq (REV695)

Maqsad: «Kabutar Ta'lim» bolalar til o'yinlari (2–7 yosh va boshlang'ich sinf) uchun RASMLI so'z bazasi. Har so'z 11 tilda.
Rasm allaqachon bor (katalogdagi `fayl`). Sen rasmni ko'rmaysan — `id` va `sozlar` dan tushunchani aniqlaysan
(id ko'pincha inglizcha yoki o'zbekcha so'zdan yasalgan: `d_en67-u13-bakery` → novvoyxona; `d_kurka` → kurka).

## Kirish
`tools/soz_bazasi/xom_N.json` — ro'yxat: {id, fayl, sozlar:[...], turkum}.

## Nima qilasan
Har element uchun qaror:
- QOLDIR — agar u bitta ANIQ, rasmda ko'rsa bo'ladigan narsa, jonzot, joy, kasb yoki oddiy harakat bo'lsa (olma, kurka, novvoyxona, sakramoq).
- TASHLA — mavhum tushuncha (teng, qonuniyat, cheksiz, narx), matematik belgi/misol, son so'zlari («beshta»), sifat-qiyos («uzunroq»),
  joylashuv iboralari («daraxt tepasida»), dars sahnasi nomi, bolaga mos bo'lmagan yoki rasmini bir so'z bilan atab bo'lmaydigan narsa.
  Shubha bo'lsa — TASHLA. Sifat sonidan muhim.
- Ikki element bir xil tushuncha bo'lsa (masalan `d_kit` va `d_kit-2`) — bittasini qoldir.

## Chiqish
`tools/soz_bazasi/qism_N.json` (N — o'z raqaming), UTF-8, ro'yxat:
{"id": "<katalog id>", "fayl": "<fayl>", "kalit": "<inglizcha snake_case, noyob: bakery, turkey>", "turkum": "<quyidagilardan biri>",
 "daraja": 1|2|3, "emoji": "<eng mos bitta emoji yoki bo'sh>",
 "w": {"uz": "...", "ru": "...", "en": "...", "de": "...", "fr": "...", "es": "...", "ar": "...", "tr": "...", "zh": "...", "ja": "...", "ko": "..."}}
va `tools/soz_bazasi/tashlandi_N.json`: [{"id": "...", "sabab": "qisqa"}].

turkum: odam | hayvon | meva | sabzavot | ovqat | ichimlik | kiyim | oyinchoq | transport | maktab | uy | tabiat | tana | joy | kasb | harakat | buyum | osimlik | boshqa
daraja: 1 — 2–4 yoshli bola biladigan eng oddiy so'z (olma, mushuk); 2 — 5–7 yosh (novvoyxona, kurka); 3 — boshlang'ich sinf (mikroskop).

## Til qoidalari (mavjud bazadagi uslub — aynan shunday yoz)
- uz: lotin, o‘ g‘ uchun ‘ (U+2018) belgisi: «o‘qituvchi». Kichik harf.
- ru: bolalar aytadigan oddiy shakl, kichik harf: «яблоко».
- en: kichik harf, artiklsiz: «apple». Britaniya/Amerika farqida keng tarqalgani.
- de: aniq artikl bilan: «der Apfel», «die Katze», «das Haus». Ot bosh harf bilan. Fe'l — infinitiv: «springen».
- fr: aniq artikl bilan: «la pomme», «le chat», «l’école» (apostrof ’). Fe'l — infinitiv: «sauter».
- es: aniq artikl bilan: «la manzana», «el gato». Fe'l — infinitiv: «saltar».
- ar: «ال» artikli bilan, harakatsiz (tashkilsiz) oddiy yozuv: «التفاحة». Fe'l — masdar yoki hozirgi zamon 3-shaxs emas, lug'aviy shakl (masalan «القفز»).
- tr: kichik harf, artiklsiz: «elma». Fe'l — «-mak/-mek»: «zıplamak».
- zh: soddalashtirilgan iyerogliflar: «苹果».
- ja: bolalarcha yozuv — hiragana (chetdan kirgan so'zlar katakana): «りんご», «パイロット». Kanji ishlatma.
- ko: hangul: «사과».
Misollar (mavjud bazadan):
apple: olma | яблоко | apple | der Apfel | la pomme | la manzana | التفاحة | elma | 苹果 | りんご | 사과
teacher: o‘qituvchi | учитель | teacher | der Lehrer | le maître | el maestro | المعلم | öğretmen | 老师 | せんせい | 선생님

## Talablar
- Har 11 til TO'LIQ va to'g'ri bo'lsin; bilmagan so'zni to'qima — bunday elementni TASHLA (sabab: «ishonchsiz tarjima»).
- Artikl jinsi to'g'ri bo'lsin (de: der/die/das; fr: le/la/l’; es: el/la). Buni alohida tekshir.
- Bitta tushuncha — bitta so'z yoki qisqa birikma (ko'pi bilan 3 so'z). Izoh, qavs, variant («/») yozma.
- `kalit` qism ichida takrorlanmasin.
- Ishni Python skripti bilan emas, o'zing bilib yoz (tarjima — bilim ishi); faylni yozish uchun skript ishlatsang bo'ladi.
- Oxirida: `python3 tools/soz_bazasi/tekshir.py tools/soz_bazasi/qism_N.json` — 0 xato bo'lishi kerak.
- Hech narsani commit qilma, boshqa fayllarga tegma.
Hisobot (qisqa, o'zbekcha): nechta qoldi, nechta tashlandi, shubhali joylar (qaysi til, qaysi so'z).
