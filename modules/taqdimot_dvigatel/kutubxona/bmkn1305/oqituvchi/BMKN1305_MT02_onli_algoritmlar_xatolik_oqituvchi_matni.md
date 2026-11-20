# O‘nli algoritmlar, taqribiy hisob va xatolik

Boshlang‘ich matematika kursi nazariyasi. 2-kurs kunduzgi, 3-semestr.

Mashg‘ulot turi: mustaqil ta’lim. Raqam: 2.

**Maqsad:** Talaba o‘nli amallarni asoslaydi, yaxlitlash qoidasini belgilaydi, absolyut va nisbiy xatoni hisoblaydi, berilgan oraliqlardan natija chegarasini topadi.

## Takrorlash

1. Asosiy natija nimadan tekshiriladi?
   Javob: Shart, manba, hisob va xulosadan.

2. Manbada yo‘q gapni iqtibos deyish mumkinmi?
   Javob: Yo‘q; o‘z tahlili alohida yoziladi.

3. Rasm o‘zi isbot bo‘ladimi?
   Javob: Faqat rasmga qarab umumiy isbot deb bo‘lmaydi.

4. Birliklar qayerda ko‘rsatiladi?
   Javob: Berilganlarda, hisobda va javobda.

5. Tekshiruv qachon bajariladi?
   Javob: Yakuniy topshirishdan oldin.

6. Talabaning mustaqil hissasi qayerda?
   Javob: Yangi misol, izoh, tekshiruv va metodik xulosada.

## Muammoli vaziyat

**1-vaziyat**
Algoritm sabablari va manbalar ko‘rsatilgan qisqa konspekt

**2-vaziyat**
Kamida 6 misol va teskari tekshiruv

Har bir xulosa uchun manba yoki tekshiriladigan asos taqdim etiladi.

## Algoritm va nazorat

### 1-slayd. Qo‘shishda razryadlar

**12,45+0,786**
Hisoblang.
1. 12,450+0,786.
2. Mingdan bir ulushlar bo‘yicha qo‘shish.
3. 13,236−0,786=12,450.
**Javob:** 13,236.

**O‘qituvchi izohi:** Vergulni vergul ostiga qo‘yish razryadlarni tenglashtirishdir. Oxiriga nol yozish son qiymatini o‘zgartirmaydi. Hisobdan oldingi taxmin natijaning miqyosini nazorat qiladi.

### 2-slayd. Ko‘paytirishda masshtab

**4,8·0,35**
Hisoblang va baholang.
1. 48·35=1680.
2. 1680/1000=1,68.
3. 0,35<1, shuning uchun natija 4,8 dan kichik.
**Javob:** 1,68.

**O‘qituvchi izohi:** 4,8=48/10 va 0,35=35/100. Butunlar ko‘paytmasi 1680, keyin 1000 ga bo‘linadi. Vergul qoidasining sababi kasr yozuvidan keladi.

### 3-slayd. Bo‘lishda bir xil masshtab

**5,04:0,12**
Hisoblang.
1. Ikkalasini 100 ga ko‘paytiramiz: 504:12.
2. 504:12=42.
3. 42·0,12=5,04.
**Javob:** 42.

**O‘qituvchi izohi:** Bo‘linuvchi va nol bo‘lmagan bo‘luvchini ayni 10 darajasiga ko‘paytirish nisbatni saqlaydi. Faqat bo‘luvchining vergulini siljitish mumkin emas.

## Yaxlitlash

### 4-slayd. Qadam va oraliq

**18,245 ni yuzdan birgacha**
Tanlangan qoida bilan yaxlitlang.
1. 18,24 va 18,25 dan teng uzoqlikda.
2. Musbat son, yarmida yuqoriga.
**Javob:** 18,25.

**Diqqat**
Yaxlitlash qoidasini aytmasdan chegara holatni “dastur xatosi” demang.

**O‘qituvchi izohi:** Eng yaqin 0,01 ga yaxlitlashda qo‘shni natijalar orasi 0,01. Ushbu paketda musbat son uchun aynan yarmida yuqoriga yaxlitlash olinadi. Boshqa dastur yarmida juft songa yaxlitlashi mumkin.

### 5-slayd. Erta yaxlitlash

**1/3 ning uch baravari**
Ikki usulni solishtiring.
1. Aniq: (1/3)·3=1.
2. Avval 0,33 olsak: 0,33·3=0,99.
3. Farq 0,01.
**Javob:** Erta yaxlitlash ta’siri bor.

**O‘qituvchi izohi:** Oraliq natijani kesish yakuniy javobni o‘zgartirishi mumkin. Hisobni yetarli aniqlikda saqlab, maqsad qilingan bosqichda yaxlitlang.

### 6-slayd. Yaxlitlash xatosi chegarasi

**Eng yaqin qiymatga yaxlitlash**
h=0,01 bo‘lsa, yuqori chegara 0,005. Qirqib tashlash boshqa qoida va boshqa chegaraga ega.

$$|a-x|\leq h/2$$


**O‘qituvchi izohi:** Eng yaqin h qadamga yaxlitlashda matematik son bilan natija orasidagi masofa h/2 dan oshmaydi. Bu o‘lchov asbobining barcha noaniqligini ifodalamaydi.

## Ikki xil xato va berilgan chegara

### 7-slayd. Absolyut xato

**x=12,5; a=12,4**
Absolyut xato?
1. a−x=−0,1.
2. |a−x|=0,1.
**Javob:** 0,1.

**O‘qituvchi izohi:** Aniq matematik qiymat x va taqribiy a berilsa, absolyut xato |a−x|. Uning birligi x bilan bir xil. Ishorali farq a−x bilan aralashtirmang.

### 8-slayd. Nisbiy xato

**x=12,5; a=12,4**
Nisbiy xato?
1. 0,1/12,5=0,008.
2. 0,008·100%=0,8%.
**Javob:** 0,008 yoki 0,8%.

**O‘qituvchi izohi:** Ushbu kursda nisbiy xato |a−x|/|x| deb olinadi va x≠0 talab qilinadi. Foiz ifodasi uchun 100 ga ko‘paytiriladi. Taqqoslash asosi x ekanini saqlang.

### 9-slayd. Noma’lum qiymat va o‘lchov noaniqligi

**x∈[9,95; 10,05], a=10**
Eng katta mumkin bo‘lgan absolyut farq?
1. Ikkala chetdan masofa 0,05.
2. Oraliqdagi barcha x uchun |10−x|≤0,05.
**Javob:** Yuqori chegara 0,05; haqiqiy xato aniq emas.

**O‘qituvchi izohi:** Agar haqiqiy qiymat noma’lum bo‘lsa, haqiqiy xatoni aynan bilaman deyish mumkin emas. Berilgan ishonchli chegaradan matematik xato bahosi chiqarish mumkin; o‘lchov noaniqligi esa alohida metrologik tushuncha.

## Oraliq bilan hisob va loyiha

### 10-slayd. Musbat oraliqlarning ko‘paytmasi

**x∈[1,95; 2,05], y∈[2,95; 3,05]**
xy chegarasi?
1. 1,95·2,95=5,7525.
2. 2,05·3,05=6,2525.
**Javob:** xy∈[5,7525; 6,2525].

**O‘qituvchi izohi:** Ikkala omil musbat bo‘lsa, eng kichik ko‘paytma chap chetlarda, eng kattasi o‘ng chetlarda olinadi. Manfiy qiymatlar qatnashsa, barcha to‘rtta chet ko‘paytma solishtiriladi.

### 11-slayd. Bitta ish varag‘i


| Masala | Tekshiruv |
| --- | --- |
| Qo‘shish | Ayirish |
| Ko‘paytirish | Razryad va taxmin |
| Bo‘lish | Bo‘luvchiga ko‘paytirish |
| Taqribiy hisob | Aniq qiymat yoki asosli oraliq |

**O‘qituvchi izohi:** Har masalada aniq berilgan, amal, taqribiy natija, yaxlitlash qoidasini va nazoratni yozing. Kalkulyator natijasini teskari amal yoki kasrga aylantirish bilan tekshiring.

### 12-slayd. Xatoni tushuntirish

Metodik parcha: taxmin → hisob → teskari tekshiruv → xato sababini aytish → yangi o‘xshash misol. “Aniqlik” so‘zini yaxlitlash qadami yoki berilgan oraliq bilan konkretlashtiring.

**O‘qituvchi izohi:** Talaba 1,68 o‘rniga 16,8 desa, shunchaki “vergul xato” demang. 0,35<1 sababli musbat natija 4,8 dan kichik bo‘lishi kerakligini so‘rang.

## Tipik xatolar

- Xato: Faqat bo‘luvchini 100 ga ko‘paytirish
  Sabab: Nisbat o‘zgargan
  To‘g‘ri: Ikkala son bir xil ko‘paytiriladi.

- Xato: Nisbiy xatoni a ga bo‘lib ayni ta’rif deyish
  Sabab: Asos almashtirilgan
  To‘g‘ri: Bu paketda maxraj |x|, x≠0.

- Xato: Xato chegarasini haqiqiy xato deyish
  Sabab: Oraliq va aniq qiymat aralashgan
  To‘g‘ri: ≤ belgisi va qiymat noma’lumligi saqlanadi.

## Metodik yondashuv

10 soatlik izlanish va loyiha

1. Manbani belgilash va konspekt

2. Hisob yoki model yaratish

3. Natijani tekshirish va metodik izoh

**Dalil**
Ko‘chirma va o‘z tahlilini farqlang.

**Hisob**
Qadam, birlik va shartlarni yozing.

**Tekshiruv**
Yechim kaliti bilan xato sababini tahlil qiling.

Ilovadagi 10 soatlik reja va tavsiyaviy mezon o‘qituvchi tomonidan guruh sharoitiga moslashtiriladi. Bu tayyor talaba referati emas.

## Xulosa

- Qabul qilingan shartlar ochiq yoziladi.

- Manba va yangi o‘quv misoli farqlanadi.

- Hisob va xulosa mustaqil tekshiriladi.

- Natija 10 soatlik ish rejasi bo‘yicha topshiriladi.

## Nazorat savollari

1. Mavzudagi ikki asosiy tushunchani farqlang.

2. Bitta natijani boshqa usulda tekshiring.

3. Misolda qabul qilingan farazlarni ayting.

4. Manba bilan o‘z xulosangiz chegarasini ko‘rsating.

5. Bitta keng tarqalgan xatoni tahlil qiling.

6. Boshlang‘ich sinf uchun moslashtirishda nimalar o‘zgaradi?

## Test

**1. 4,8·0,35 nechaga teng?**
A. 16,8
B. 1,68
C. 0,168
D. 168

**2. 5,04:0,12 nechaga teng?**
A. 42
B. 4,2
C. 0,42
D. 420

**3. Musbat 18,245 yarmida yuqoriga 0,01 gacha?**
A. 18,24
B. 18,2
C. 18,3
D. 18,25

**4. x=12,5, a=12,4; nisbiy xato foizda?**
A. 8%
B. 0,08%
C. 0,8%
D. 1%

**5. Eng yaqin 0,01 ga yaxlitlashning maksimal absolyut xatosi?**
A. 0,01
B. 0,005
C. 0,1
D. 0,0005

**6. x=0 bo‘lsa |a−x|/|x|?**
A. Doim 0
B. Doim 1
C. a ga teng
D. Aniqlanmagan

**Test kaliti:** 1 — B, 2 — A, 3 — D, 4 — C, 5 — B, 6 — D

## Mustaqil ish

1. 7,25+0,608; 6,4·0,125; 3,78:0,09 ni teskari amal bilan tekshiring.

2. Musbat 4,765 va 9,994 ni yarmida yuqoriga yuzdan birgacha yaxlitlang; xato chegarasini ayting.

3. x=80, a=79,2 uchun absolyut va nisbiy xatoni toping. x noma’lum bo‘lsa, nima o‘zgaradi?

4. x∈[3,9; 4,1], y∈[1,9; 2,1] uchun ko‘paytma chegarasini toping; bitta xato javobni tuzatadigan metodik kartochka yozing.

Javoblar alohida javoblar JSON faylida. Metodik topshiriqlarda kutiladigan mezonlar ham berilgan.

**Keyingi mavzu:** Navbatdagi mustaqil ta’lim bandi. Reja, mahsulot va tekshiruv mezonlari bilan ish davom etadi.

## Manbalar

Boshlang‘ich matematika kursi nazariyasi fanining o‘quv dasturi, BMKN 1305. 2-kurs kunduzgi, 2026–2027; MT2, asl skanning 6-beti. Mavzu qamrovi uchun.
- [Cornell, David Bindel: Notions of error](https://www.cs.cornell.edu/courses/cs4220/2026sp/lec/2026-02-02.html)
- [NIST TN1297, terminology](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-appendix-d1-terminology)
## 10 soatlik mustaqil ish rejasi

Topshiriq va tekshiruv paketi tayyor; talabaning ishi bajarildi degani emas

| Bosqich | Soat | Ish |
|---|---:|---|
| 1 | 2 | O‘nli algoritmlar va manbalarni o‘rganish |
| 2 | 2 | Amallarni ikki usulda bajarish |
| 3 | 2 | Yaxlitlash, xato va oraliq masalalarini yechish |
| 4 | 2 | Xato tahlilli ish varag‘i va metodik parcha tayyorlash |
| 5 | 1 | Teskari amal va chegaralar bilan tekshirish |
| 6 | 1 | Natijani himoya qilish va tuzatish qaydi |

## Topshiriladigan natijalar

- D1: Algoritm sabablari va manbalar ko‘rsatilgan qisqa konspekt
- D2: Kamida 6 misol va teskari tekshiruv
- D3: Yaxlitlash hamda xato/oraliq hisoblari jadvali
- D4: Xato tahlilli metodik kartochka va refleksiya

## Tavsiyaviy baholash

Tavsiyaviy ichki mezon; muassasaning rasmiy baholash nizomi o‘rniga olinmaydi

| Mezon | Maksimal ball | Talab |
|---|---:|---|
| Algoritm asosi | 5 | Razryad va teng masshtab izohlangan. |
| Aniq hisob | 5 | Amallar va teskari tekshiruvlar mos. |
| Xato tushunchasi | 5 | Ta’rif, maxraj, qoida va chegaralar saqlangan. |
| Metodik izoh | 5 | Xato sababi va tuzatish savoli aniq. |

Jami:20 ball.

- 0: Dalil yo‘q yoki vazifa bajarilmagan
- 1–2: Qisman, asosiy xato yoki yetishmaydigan dalil bor
- 3–4: Asosan to‘g‘ri, tekshiruv yoki izohda ayrim kamchiliklar
- 5: Talab to‘liq, asosli va tekshirilgan
