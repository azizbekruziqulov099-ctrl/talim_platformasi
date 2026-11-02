# Vazifa: «Xalqaro baholash» kursi uchun Kabu ustoz darslari (o‘zbek tilida)

Platformada AI ustoz (Kabu) doskada yozib, ovoz bilan tushuntiradi. **Doskaga yozilayotgan narsa va ustoz gapi bir xil
ketadi**: har bir doska satri ustoz aynan o‘sha joyni aytayotganda harfma-harf yoziladi. Siz TIMSS mazmun mavzulari
(`tools/ramka.json` → `mavzular` → sizga berilgan to‘plam) bo‘yicha har bir mavzuga **bitta to‘liq dars** yozasiz.
Dars o‘quvchini shu mavzudagi xalqaro (TIMSS) savollarni mustaqil yecha oladigan darajaga olib chiqishi kerak:
tushuncha → qoida → ishlangan misollar → birga yechish → mulohaza strategiyasi → xulosa.

Har bir mavzu uchun shu to‘plamdagi asl savollar ro‘yxati `meta/<to‘plam>.items.json` da bor (`mavzu` maydoni
bo‘yicha filtrlang): `nom_en` (savol nomi), `fikrlash`, `xalqaro_ortacha` (dunyo bo‘yicha to‘g‘ri yechganlar foizi),
`davlatlar`. Bulardan mavzuda nima so‘ralishini va qaysi joy qiyinligini bilib oling (masalan, xalqaro o‘rtacha 30% dan
past bo‘lgan savollar — qiyin joy, darsda alohida to‘xtaling). Asl savollarni ko‘chirmang — misollarni o‘zingiz tuzing.

## Chiqish fayli: JSON massiv, har mavzuga bitta obyekt
```json
{
  "kod": "XB-M8-KAS",                       // "XB-" + mavzu kaliti
  "mavzu": "M8-KAS",
  "sarlavha": "Kasrlar va o‘nli kasrlar",
  "maqsad": "Kasr va o‘nli kasrlarni taqqoslash, amallar bajarish, taxminiy hisoblash va hayotiy masalada qo‘llash",
  "qadamlar": [
    {"turi": "kirish", "sahna": "kirish", "sarlavha": "Bugun nima o‘rganamiz?",
     "doska": "Pitsaning $\\frac{3}{8}$ qismi\nTIMSS: 8-sinflarning 57% i to‘g‘ri yechgan",
     "ovoz": "[1] Tasavvur qiling, pitsani sakkiz bo‘lakka bo‘ldik va uch bo‘lagini yedik — bu sakkizdan uch qism. [2] Xalqaro TIMSS tadqiqotida shunga o‘xshash savolni dunyodagi sakkizinchi sinflarning ellik yetti foizi to‘g‘ri yechgan. Bugun biz yuz foiz yechadigan bo‘lamiz!"},
    {"turi": "qoida", "sahna": "q1", "sarlavha": "…", "doska": "…\n…", "ovoz": "[1] … [2] …"},
    {"turi": "misol", "sahna": "m1", "sarlavha": "1-misol", "doska": "shart satri", "ovoz": "[1] …"},
    {"turi": "misol", "sahna": "m1", "sarlavha": "", "doska": "1-qadam", "ovoz": "…"},
    {"turi": "birga", "sahna": "b1", "sarlavha": "Endi o‘zingiz", "doska": "savol", "ovoz": "…",
     "savol": "Javobingizni yozing", "javob": "0,75|3/4|0.75"},
    {"turi": "xulosa", "sahna": "xulosa", "sarlavha": "Esda tuting", "doska": "…", "ovoz": "…"}
  ],
  "tushunmadim": {
    "q1": [
      {"turi": "sodda", "doska": "…", "ovoz": "…"},
      {"turi": "hikoya", "doska": "…", "ovoz": "…"},
      {"turi": "boshqa_usul", "doska": "…", "ovoz": "…"}
    ]
  },
  "tipik_xatolar": ["Kasrlarni taqqoslashda faqat maxrajga qarash: 1/8 > 1/4 deb o‘ylash", "…"],
  "strategiyalar": ["Variantlarni taxminiy hisob bilan tekshiring", "…"],
  "kalit_sozlar": ["kasr", "o‘nli kasr", "taqqoslash"]
}
```

## Qoidalar
1. **Doska–ovoz mosligi (eng muhim).** `doska` dagi har bir satr (`\n` bilan ajratilgan) uchun `ovoz` da `[1]`, `[2]` ...
   belgisi bo‘lsin; belgi o‘sha satr yozila boshlaydigan joyda turadi va belgidan keyingi gap aynan shu satr haqida.
   Satrlar soni = belgilar soni. Bir qadamda 1–4 satr. Doska satri qisqa (≤ 60 belgi): qoida, formula, hisob qadami.
   Ovoz — jonli, iliq, aniq og‘zaki tushuntirish (ustoz o‘quvchiga "siz" deb murojaat qiladi), har satr uchun 1–2 gap.
2. Bitta misolning qadamlari bir xil `sahna` da (doskada ketma-ket yig‘iladi). Har yangi tushuncha — yangi `sahna`.
3. Darsda 12–20 qadam: 1 kirish, 3–6 tushuncha/qoida, kamida 2 ta ishlangan misol (biri — mulohaza darajasidagi,
   ko‘p bosqichli, TIMSS uslubida), 2 ta `birga` (javobi qisqa, avtomatik tekshiriladi: son, kasr yoki 1–2 so‘z;
   bir nechta to‘g‘ri yozilishi | bilan), 1 ta "Xalqaro savolni qanday yechamiz" strategiya qadami, 1 xulosa.
4. `tushunmadim` — har bir qoida/tushuncha sahnasi uchun 2–3 variant: `sodda` (soddaroq), `hikoya` (hayotiy hikoya
   orqali), `boshqa_usul` (boshqa usul/ko‘rgazma). Ularda ham `doska` (1–3 satr) va `ovoz` bo‘lsin (bu yerda [n] shart emas).
5. Til: adabiy o‘zbek (lotin), o‘ g‘ — U+2018 (‘), tutuq — U+2019 (’). O‘nli kasr vergul bilan (formulada `2{,}5`).
   Formulalar `$...$` (KaTeX). 4-sinf darslarida juda sodda til, qisqa gaplar, ko‘p hayotiy misol.
   Fanlar darslarida ilmiy aniqlik birinchi o‘rinda (o‘zbek darsliklari atamalari: fotosintez, hujayra, zichlik, tok kuchi...).
6. Kirishda shu mavzu savollari bo‘yicha xalqaro o‘rtacha foizni ayting (meta’dagi `xalqaro_ortacha` lar o‘rtachasi,
   butun songa yaxlitlang) va o‘quvchini ruhlantiring. Raqamni o‘ylab topmang — faqat meta’dan hisoblang.
7. `kalit_sozlar` — o‘zbek maktab dasturidagi shu mavzuga oid 3–8 so‘z (maktab darslari bilan bog‘lash uchun).

## Ish tartibi
1. `tools/ramka.json` va `meta/<to‘plam>.items.json` ni o‘qing.
2. Sizga berilgan mavzular uchun darslarni yozing va `content/dars_<nom>.json` ga saqlang.
3. Tekshiring: `python3 -I tools/tekshir_dars.py content/dars_<nom>.json` — OK bermaguncha tuzating.
4. Qisqa hisobot qaytaring.
