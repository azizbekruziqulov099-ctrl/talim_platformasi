# Kabutar TV — yangi reja (to'xtatib turilgan, keyin davom etadi)

Azizjon bilan kelishilgan (2026-11-02). Batafsil kerakli narsalar ro'yxati: `Kabutar_TV_kerakli_narsalar.xlsx`.

## Format
- Ikki boshlovchining tabiiy suhbati; har ko'rsatuv bitta mavzu atrofida yangi so'zlar bilan (David & Alice, BBC 6 Minute uslubi).
- Daraja: CEFR (A1–C2) / IELTS; 2–4 yosh Pre-A1 (4–5 so'z, 5 daq) … 1–4-sinf A1 (8 so'z) … 5–7-sinf A2 … 8–9-sinf B1 … 10–11-sinf B1–B2 … sertifikat guruhlari B2–C1.
- 7-sinfgacha: tushuntiruvchi til + o'rganilayotgan til; 8-sinfdan: ikkalasi o'rganilayotgan tilda (yoki ikki til: en + ru).
- Ruknlar: ochilish → kirish → asosiy suhbat (yangi so'zda «dzin», karta) → «So'z lupasi» → ob-havo burchagi (5 yoshdan) → o'yin → «Biz bilan qaytaring» (pauza) → mini-test (1-sinfdan) → xayr. Har so'z ≥5 marta.
- Rukn almashganda jingl va o'tish; yaqin plan, reaksiya kadri, so'zga yaqinlashish.

## Hozirgi TV xatolari (2026-11-02 sinov yasashi, en 3-sinf)
1. Ustozlar eski rasmlarda — 19 ustozning TV rasmlari (/tv/<ism>: tik, salom, korsat, yaqin, qara + og'iz/ko'z) ulanmagan.
2. So'z kartalarida emoji — umumiy rasm kutubxonasi (modules/rasm_kutubxona, rasm_top) ishlatilishi kerak.
3. Kun so'zlari mavzuga bog'lanmagan; rasm o'yinida «Where is ready?» kabi ma'nosiz savollar; mavzusiz sanash.
4. Ba'zi kadrlarda doska bo'sh; ustozlar joylashuvi (biri kichik, biri ekrandan chiqib ketgan).
5. Kabu teatrida o'zbekcha Kabuda ham «EN» belgisi.

## Tartib
1) ustozlar → 2) kartalarda rasm → 3) so'z va o'yin mantiqi → 4) yangi tartib → 5) rejissor → 6) mayda xatolar.
Sinov: /tmp da espeak-ng bilan yasab, kadrma-kadr tekshiriladi (serverda edge-tts).

## Yangi materiallar (2026-11-02, Azizjon yubordi) — data/studiya da
- Fonlar: obhavo, oyin, sinf, oshxona, dokon, park, shifokor, kocha, vokzal, ishjoyi, imtihon, zoom — har biri _old/_chap/_ong/_yaqin (1920×1080).
- sfx/: 20_yangi_soz_dzin … 37_kamera_shiq (18 ta); musiqa/: 07–09 fon musiqasi + j_* rukn jingllari (6 ta); ochilish/: 04–06 (1–4-sinf, 5–9-sinf, 10–11/sertifikat) ochilish va yopilish; grafika/: rukn_* belgilari, soz_kartasi_ramka, pastki_lenta, obhavo_xarita.
- Hali ekranlar.json va rejissorga ulanmagan — TV ishida ulanadi.
- Rasmlar: modules/rasm_kutubxona (3904 ta) — so'z kartalari shu yerdan.

## REV262 (2026-11-02) — bajarildi
- 19 ustozning TV rasmlari ulandi (data/ustozlar/<ism>): tik/yaqin — rassom og'iz va ko'z yamoqlari (faqat og'iz/ko'z ellipslari);
  salom/korsat — tik yamoqlari yuz joyiga ko'chirildi (shablon moslik > 0.85); qara — og'izsiz (tinglash pozasi).
- Gapirayotganda og'zi qimirlaydigan poza tanlanadi; ustoz kadrdan chiqib ketmaydi.
- So'z kartalarida rassom rasmlari (modules/rasm_kutubxona), topilmasa — emoji.
## Keyingi: yangi format (suhbat, so'z lupasi, ob-havo sahnasi, jingllar, yangi fonlar), so'zlar mavzudan, ma'nosiz rasm savollarini olib tashlash.
