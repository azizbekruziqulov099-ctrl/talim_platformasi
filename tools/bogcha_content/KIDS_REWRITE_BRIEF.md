# BOLALAR (2–7 yosh) DARSLARINI QAYTA TEKSHIRISH VA YOZISH — umumiy topshiriq

Foydalanuvchi (Azizjon, SamDPI o'qituvchisi) shikoyatlari — HAMMASINI tuzat:
1. O'yin «mushukni top» deydi, lekin doskada sigir/it bor, MUSHUK YO'Q (ovozda aytilgan narsa bosiladigan nishon emas). Sabab: o'yin doskasida
   shu darsda o'tilmagan (eski) rasm turadi, nishon esa FAQAT shu darsning yangi bilim qadamlaridan (tushuncha sarlavhasi «emoji so'z») olinadi.
   Dvigatel tuzatildi (o'yin faqat yangi so'zlar bilan), endi MUALLIF o'yin/extra qatorlari ham shunday bo'lsin.
2. Hali o'tilmagan so'zlar o'yinlarda uchraydi — taqiqlanadi. O'yin va testda faqat shu darsda yoki OLDINGI darslarda o'rgatilgan so'zlar.
3. «Nomini ayt» (ovoz chiqarib nomini aytish / ochilishi) noto'g'ri — savol, rasm va ochiladigan javob mos bo'lsin.
4. ESHAK (donkey, 🫏, ослик ...) so'zi va rasmi bolalar darslaridan OLIB TASHLANSIN (so'kish ma'nosida ham ishlatiladi). Almashtirish: ot, sigir, echki, qo'y va h.k.
   (Eshik = door qolishi mumkin — faqat eshak olib tashlanadi.)
5. SANASH (sana) to'g'ri bo'lsin: har bir sanoq savolida rasmlar soni javobga aniq teng; 1 dan boshlab bir-bir sanash, oxirgi son «nechta»; 2–3 yoshda 1–3, 3–4 yoshda 1–5,
   4–5 yoshda 1–10, 5–6 yoshda 1–20, 6–7 yoshda 1–100 kabi chegaradan chiqma; savol va to'g'ri javob orasida nomuvofiqlik bo'lmasin.
   Platformaning sanash imkoniyatlari: `src/kid` (kidStageRules.js: sanoqBosish, sanashTopshiriq, sanoqKarta) — bola rasmni bosib sanaydi. Matematikada sanash qadamlarini shu uslubga keltir
   (doskada aniq emojilar soni, ovozda «bir, ikki, uch»).
6. Boshqa narsalarni o'zgartirma (fan tuzilishi, rasm fayl nomlari `image`, kitob kodi/prefiksi, bo'lim/dars soni asosan shunday qolsin; rasm nomi o'zgarsa ham eski nomlar yo'qolmasin).
7. Dars jonli, hayotiy, qiziqarli: hikoya, sir, harakat (TPR: «qo'lingni qars!»), qo'shiq-hisob, o'yin, kichik tajriba. Ovoz matni va doska MOS (ovozda aytilgan narsa doskada ko'rinsin).

## 2–7 yosh mutaxassisi (rivojlanish psixologi + maktabgacha metodist) nazorat ro'yxati — har dars uchun o'zing tekshir
- 2–3 yosh: 1–2 so'zli gap, bir dars = 2 ta tushuncha, takror ko'p, ovoz-harakat, nuqtai nazar «bu — …».
- 3–4: 3–4 so'zli gap, rang/shakl/hayvon/oila, juftlash, 1–5 gacha sanash.
- 4–5: «nega?» savollari, taqqoslash (katta/kichik, uzun/qisqa), guruhlash, 1–10, oddiy naqsh.
- 5–6: sabab-oqibat, ketma-ketlik, qo'shish/ayirish 10 ichida (rasm bilan), soat, fasllar, harf/bo'g'in.
- 6–7: maktabga tayyorlik: 20/100 gacha sanash, qo'shish-ayirish ko'rinishda, mantiqiy chiqarish, hikoya tuzish.
- Faktlar to'g'ri (hayvon ovozi, qaysi hayvon nima yeydi, fasllar, tana a'zolari soni, rang aralashishi va h.k.).
- Hech qachon qo'rqitadigan, kasal/o'lim, so'kish, noto'g'ri stereotip, ortiqcha murakkab so'z yo'q.
- Bola O'QIY OLMAYDI: hamma narsa ovozda; doskada emoji va qisqa belgi.

## Texnik
Format: CURRICULUM_SPEC.md (shu papkada) — o'qi. Dvigatel: tools/bogcha_spiral.py (o'zgartirma). Tilli kitoblarda sodda uz izohlari saqlansin.
Tekshiruv (o'zing ishga tushir, 0 xato bo'lguncha):
  cd /home/claude/talim_platformasi
  python3 tools/bogcha_oyin_tekshir.py tools/bogcha_content/<fayl>.json        # o'yin qoidalari
  python3 -c "import sys;sys.path.insert(0,'.');from tools.bogcha_kitob import build_books;b=build_books(['tools/bogcha_content/<fayl>.json']);print(len(b[0]['topics']))"   # qurilish xatosiz
  (til kitoblarida `<nom>_enrich.json` avtomatik qo'shiladi — uni ham tekshir va kerak bo'lsa tuzat.)
Bitta faylni yozganda butun JSON to'g'ri bo'lsin (python json.load bilan tekshir). Git commit QILMA — men qilaman.
Oxirida QISQA hisobot: nima topding (xatolar soni), nimani tuzatding, qolgan shubhalar. O'zbekcha.
