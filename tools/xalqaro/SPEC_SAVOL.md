# Vazifa: TIMSS uslubidagi parallel savollar (o‘zbek tilida)

Siz o‘zbek maktab o‘quvchilari uchun xalqaro baholash (TIMSS) tayyorlov platformasiga savollar yozasiz.
Har bir ish faylida (`jobs/<nom>.json`) TIMSS 2011 ning ochiq e’lon qilingan savollari ro‘yxati bor:
ID, mazmun sohasi, mavzu, fikrlash darajasi (bilish / qo‘llash / mulohaza), ball, kalit va savol sahifalarining
rasmlari (`sahifalar` — PNG). Ikkinchi sahifa odatda baholash yo‘riqnomasi (Scoring Guide) bo‘ladi.

## MUHIM — huquqiy talab
Asl TIMSS savollari IEA mulki, tijoriy maqsadda ishlatib bo‘lmaydi. Shuning uchun asl savol matnini, sonlarini,
nomlarini, rasmini **ko‘chirmang va tarjima qilmang**. Siz har bir asl savolni ko‘rib, uning **o‘lchaydigan ko‘nikmasini,
formatini, qiyinligini** tushunasiz va **o‘zingiz yangi, o‘xshash (parallel) savol** yozasiz: boshqa vaziyat, boshqa sonlar,
boshqa nomlar (o‘zbekcha ismlar: Aziz, Malika, Jasur, Nilufar...; o‘zbek hayoti: bozor, choyxona, paxta dalasi, metro, so‘m).
Ko‘nikma, fikrlash darajasi va qiyinlik asl savolga mos bo‘lsin.

## Har bir asl savol uchun chiqadigan yozuv
```json
{
  "id": "M032166",                       // asl ID (o‘zgartirmang)
  "kunikma": "Ko‘paytma va bo‘linmaning qiymatini yaxlitlash orqali taxminan baholash",   // nimani o‘lchaydi — 1 gap
  "usul": "Har bir sonni eng yaqin butun songa yaxlitlang, keyin amallarni bajaring va natijani variantlar bilan solishtiring.", // yechish strategiyasi, 1–2 gap
  "variantlar": [ V1, V2 ]               // aynan 2 ta parallel savol
}
```
Har bir `V`:
```json
{
  "turi": "tanlov",                      // "tanlov" (4 variantli test) yoki "ochiq" (qisqa javob yoziladi)
  "savol": "…",                          // to‘liq shart. Formula: $\\frac{3}{4}$, $2{,}5 \\cdot 4$. Yangi qator: \n
  "rasm": null,                          // kerak bo‘lsa — SVG matni (pastdagi qoidalar), aks holda null
  "javoblar": ["…", "…", "…", "…"],      // faqat "tanlov" uchun, A B C D tartibida, harfsiz
  "togri": 2,                            // "tanlov": to‘g‘ri javob indeksi 0–3. To‘g‘ri javob o‘rni har xil bo‘lsin (hammasi B emas)
  "javob": "",                           // "ochiq": qabul qilinadigan javoblar | bilan: "12|12 ta" yoki "3/4|0,75|0.75"
  "javob_turi": "",                      // "ochiq": "son" | "kasr" | "soz" (bitta-ikki so‘z)
  "yechim": [                            // 3–7 qadam: doskaga yoziladi va ustoz AYNAN shu paytda aytadi
    {"doska": "$7{,}21 \\approx 7$,  $3{,}86 \\approx 4$", "ovoz": "Avval sonlarni yaxlitlaymiz: yetti butun yigirma bir taxminan yetti, uch butun sakson olti taxminan to‘rt."},
    {"doska": "…", "ovoz": "…"}
  ],
  "xatolar": {"0": "A ni tanlagan o‘quvchi … deb o‘ylagan", "1": "…", "3": "…"},   // "tanlov": har noto‘g‘ri variant uchun tipik xato (indeks kalit). "ochiq": {"umumiy": "…"} 1–2 ta tipik xato
  "maslahat": "…"                        // 1 gap: yechimni aytmasdan yo‘naltiruvchi ishora
}
```

## Qoidalar
1. **Avtomatik tekshiriladigan bo‘lsin.** Asl savol ochiq javobli (tushuntirish, chizish, jadval to‘ldirish) bo‘lsa —
   uni bir ma’noli qisqa javobli ("ochiq": son/kasr/1–2 so‘z) yoki 4 variantli testga aylantiring. Tushuntirish talab
   qiladigan fanlar savolida eng to‘g‘ri tushuntirishni variantlardan tanlatish mumkin. Bir nechta qismli (A, B, C) savolda
   har qism mustaqil: shartni to‘liq takrorlang.
2. **Til:** sof adabiy o‘zbek tili (lotin). Apostrof: o‘ g‘ (U+2018 ‘), tutuq belgisi ’ (U+2019): ma’lumot, sun’iy.
   O‘nli kasrda vergul: 2,5 (formulada `2{,}5`). Atamalar o‘zbek maktab darsliklaridagidek (kasr surati/maxraji,
   perimetr, yuza, hajm, fotosintez, zanjir, tezlik, zichlik...). 4-sinf savollari juda sodda va qisqa gaplarda.
3. **Yechim — doska va ovoz bir xil ketadi:** `doska` — doskaga yoziladigan qisqa satr (formula, hisob, xulosa),
   `ovoz` — ustoz shu satrni yozayotganda aytadigan 1–2 gap; doskadagi narsani so‘z bilan aytadi, sonlarni so‘z bilan
   yozish shart emas. Oxirgi qadam — javob: "Javob: C) …" yoki "Javob: 12". Hisob-kitobni o‘zingiz tekshiring
   (kerak bo‘lsa python bilan). Xato javob — eng katta xato.
4. **Distraktorlar** (noto‘g‘ri variantlar) haqiqiy tipik xatolardan kelib chiqsin, `xatolar` da shu xato tushuntirilsin.
5. **Rasm (SVG)** faqat savol rasm talab qilsa: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 W H">…</svg>`,
   kenglik 200–480, 10 KB dan kichik, faqat oddiy elementlar (line, rect, circle, ellipse, polygon, polyline, path, text, g),
   `<script>`, `<image>`, tashqi havola, `foreignObject`, `style` atributidagi url yo‘q. Chiziq rangi `#222`, to‘ldirish yengil
   (`#e8f1ff`, `#fde9c8`, `#dff3e4`, `none`), matn `font-family="sans-serif" font-size="14"`. Yozuvlar o‘zbekcha.
   Shakl o‘lchamlari shartdagi sonlarga mos (masshtab ko‘rinishi to‘g‘ri). Diagramma/jadvalda qiymatlar aniq ko‘rinsin.
   Jadvalni SVG o‘rniga matnda Markdown jadvali ko‘rinishida ham berish mumkin emas — jadval kerak bo‘lsa SVG bilan chizing.
6. V1 va V2 bir-birini takrorlamasin (boshqa kontekst, boshqa sonlar), lekin ko‘nikma va qiyinlik bir xil.
7. Fanlar (tabiiy fanlar) savollarida ilmiy aniqlik birinchi o‘rinda; noaniq yoki bahsli faktlardan qoching.

## Ish tartibi
1. `jobs/<nom>.json` ni o‘qing. Har bir savol uchun `sahifalar` dagi PNG rasmlarni Read bilan ko‘ring.
2. Natijani `content/<nom>.json` ga yozing: yozuvlar ro‘yxati (JSON massiv), ish fayldagi tartibda, har ID uchun bitta yozuv.
3. Tekshiring: `python3 -I tools/tekshir.py content/<nom>.json jobs/<nom>.json` — xato chiqsa tuzating va qayta tekshiring.
4. Yakunda qisqa hisobot qaytaring: nechta yozuv, qaysi savollarni formatini o‘zgartirdingiz (ochiqdan testga va h.k.).
