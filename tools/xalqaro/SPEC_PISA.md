# Vazifa: PISA uslubidagi parallel birliklar (o‘zbek tilida, 15 yoshli o‘quvchilar — 9–10-sinf)

PISA savollari **birlik** (unit) ko‘rinishida: avval umumiy **stimul** (vaziyat matni, jadval, grafik, xarita, bir nechta
manba), keyin unga oid 1–6 ta savol. Har savolning: mazmun sohasi (`tools/ramka_pisa.json` → `mavzular`), jarayoni
(`jarayonlar`), konteksti (shaxsiy / kasbiy / ijtimoiy / ilmiy), qiyinligi (PISA balli va darajasi) bo‘ladi.

Sizga manba PDF va sahifa oralig‘i beriladi (`pdf/<KOD>.pdf`). Matnni `pdftotext -layout -f N -l M pdf/<KOD>.pdf -` bilan
o‘qing; rasm/grafik/jadval bo‘lsa sahifa rasmini `pages/P/<KOD>/p-NNN.png` (yoki `p-NN.png`) Read bilan ko‘ring.
Javoblar va izohlar (to‘g‘ri javob, OECD bo‘yicha to‘g‘ri yechganlar foizi, qiyinlik balli, daraja) ko‘pincha
alohida «Answers / scoring» bo‘limida yoki savol ostida — ularni ham o‘qing.

## MUHIM — huquqiy talab
PISA savollari va matnlari OECD mulki. Asl matnni, stimulni, savolni **ko‘chirmang va tarjima qilmang**.
Har bir asl birlikni o‘qib, uning **turi, tuzilishi, ko‘nikmasi, jarayoni, qiyinligini** tushuning va **o‘zingiz yangi
parallel birlik** yozing: boshqa vaziyat, boshqa sonlar, boshqa matn — o‘zbek hayoti (Toshkent metrosi, Orol dengizi,
Samarqand, paxta, bozor, mahalla, so‘m, Chorvoq, Qizilqum, IT-park, oilaviy byudjet, bank kartasi, Humo/Uzcard...).
O‘qish savodxonligi birliklarida o‘zingiz **yangi matn** yozasiz: janri va hajmi asliga o‘xshash (hikoya parchasi,
ilmiy-ommabop maqola, e’lon, blog/forum, jadval va grafikli hisobot, ikki manbani solishtirish...), 150–600 so‘z.
Matn haqiqiy faktlarni buzmasin (o‘ylab topilgan voqea bo‘lsa — badiiy yoki taxminiy ekani aniq bo‘lsin).

## Chiqish fayli: JSON massiv, har asl birlikka bitta parallel birlik
```json
{
  "birlik": "P-TT-M07",                  // sizga berilgan prefiks + tartib raqami (ikki xonali)
  "asl": "Take the Test, Mathematics unit 7: Speed of Racing Car",   // asl manba (faqat havola uchun)
  "toplam": "P_M",                       // P_M | P_R | P_S | P_F
  "nom": "Chorvoq yo‘lidagi velopoyga",  // yangi birlik nomi
  "stimul": "Matn... \n\nJadval satrlari oddiy matnda yoki SVG da",   // umumiy vaziyat (formula $...$)
  "stimul_rasm": null,                   // kerak bo‘lsa SVG (qoidalar pastda)
  "savollar": [
    {
      "id": "P-TT-M07-1",                // birlik + "-" + savol tartibi
      "asl_id": "M159Q01",               // asl savol kodi yoki "Speed of Racing Car Q1"
      "mavzu": "PM-OZG",                 // ramka_pisa.json dagi mavzu kaliti (shu to‘plamniki)
      "jarayon": "talqin",               // ramka_pisa.json → jarayonlar dagi kalit
      "kontekst": "shaxsiy",
      "fikrlash": "qollash",             // umumiy: bilish | qollash | mulohaza (jarayon va qiyinlikka qarab)
      "qiyinlik_ball": 492,              // asl hujjatda bo‘lsa — aynan o‘sha son; bo‘lmasa taxmin qiling
      "taxminiy": false,                 // qiyinlik hujjatdan olingan bo‘lsa false, taxmin bo‘lsa true
      "oecd_foiz": 67,                   // hujjatda «X% of students across OECD countries» bo‘lsa, aks holda null
      "kunikma": "Grafikdan tezlik o‘zgarishini o‘qish va talqin qilish",
      "usul": "Avval o‘qlar nimani bildirishini aniqlang, keyin grafik qayerda ko‘tarilishi/tushishini kuzating.",
      "turi": "tanlov",                  // "tanlov" (4 variant) yoki "ochiq" (qisqa javob)
      "savol": "…",
      "rasm": null,                      // savolga xos rasm (SVG) — kerak bo‘lsa
      "javoblar": ["…","…","…","…"],     // tanlov uchun
      "togri": 1,
      "javob": "",                       // ochiq: "12|12 ta"
      "javob_turi": "",                  // ochiq: son | kasr | soz
      "yechim": [{"doska": "…", "ovoz": "…"}],   // 3–6 qadam; oxirgisi "Javob: B) …" yoki "Javob: 12"
      "xatolar": {"0": "…", "2": "…", "3": "…"}, // tanlov: har noto‘g‘ri variant; ochiq: {"umumiy": "…"}
      "maslahat": "…"
    }
  ]
}
```

## Qoidalar
1. Asl birlikdagi **har bir savolga** bitta parallel savol (savollar soni asl bilan bir xil). Asl savol ochiq javobli
   (tushuntirish, insho) bo‘lsa — avtomatik tekshiriladigan qiling: 4 variantli test (eng to‘g‘ri tushuntirishni tanlash,
   «Ha/Yo‘q + sabab» juftliklari) yoki bir ma’noli qisqa javob (son, kasr, 1–2 so‘z). Bir nechta to‘g‘ri yozilish `|` bilan.
2. **Qiyinlik:** hujjatda «difficulty … score points» yoki «Difficulty 497 – Level 3» bo‘lsa — shu sonni `qiyinlik_ball`
   ga yozing, `taxminiy: false`. Bo‘lmasa — savol murakkabligiga qarab PISA shkalasida taxmin qiling (oddiy bir qadamli
   ~400–450; ikki-uch qadamli ~480–560; ko‘p bosqichli mulohaza, asoslash ~600–700) va `taxminiy: true`.
   Parallel savol asl qiyinligini saqlasin.
3. **Til:** sof adabiy o‘zbek (lotin), o‘ g‘ — U+2018 (‘), tutuq — U+2019 (’). O‘nli kasr vergul bilan (formulada `2{,}5`).
   15 yoshli o‘quvchiga mos, aniq va bir ma’noli. Sonlar real hayotga mos (narxlar so‘mda, masofalar haqiqiy).
4. **Yechim:** `doska` — doskaga yoziladigan qisqa satr (≤ 60 belgi), `ovoz` — ustoz shu satrni yozayotganda aytadigan
   1–2 gap. O‘qish savollarida yechim — matnning qaysi joyidan javob topilishi va nega boshqalari noto‘g‘ri ekani.
   Hisoblarni python bilan tekshiring.
5. **Distraktorlar** tipik xatolardan (masalan, matnda bor-u, savolga javob bermaydigan jumla; birlikni almashtirish).
6. **SVG** (stimul_rasm yoki rasm): `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H">`, kenglik 240–520,
   14 KB dan kichik, faqat line/rect/circle/ellipse/polygon/polyline/path/text/g; script/image/href/url yo‘q.
   Chiziq `#222`, yengil to‘ldirish, `font-family="sans-serif"`, yozuvlar o‘zbekcha, qiymatlar shartga aniq mos.
   `rsvg-convert` bilan PNG ga aylantirib ko‘ring. Jadvalni stimul matnida oddiy satrlar bilan ham berish mumkin.
7. Asl hujjatdagi kompyuter simulyatsiyasi (2015/2025 fan birliklari) bo‘lsa — uni jadval/grafik ko‘rinishidagi tayyor
   tajriba natijalari bilan almashtiring (o‘quvchi natijalarni o‘qib xulosa chiqaradi).

## Ish tartibi
1. Berilgan sahifalardagi barcha birliklarni (va javob/scoring bo‘limini) o‘qing.
2. Natijani `content/pisa/<nom>.json` ga yozing (JSON massiv).
3. Tekshiring: `python3 -I tools/tekshir_pisa.py content/pisa/<nom>.json` — OK bermaguncha tuzating.
4. Yakunda o‘zbekcha qisqa hisobot: nechta birlik/savol, qaysilarining formati o‘zgardi, qiyinliklar qayerdan olindi.
