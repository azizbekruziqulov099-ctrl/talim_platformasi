# Tarjimon uchun ko'rsatma (bog'cha 3–7 yosh til kitoblari)

Manba: `manba.json` → "matnlar": {id: {"en": matn, "kind": tur, "ctx": qayerda}}.
Natija: `<til>.json` = {"t": {id: tarjima, ...}, "rom": {id: lotincha o'qilishi, ...}}. HAR bir id uchun "t" bo'lishi SHART.

Turlar:
- say — bola o'rganadigan so'z/ibora (qisqa, tabiiy, bolalar tili). Tinish belgilari mazmunga mos (Hello! → «Привет!»).
  ctx ichida (uz: …) — o'zbekcha ma'nosi: tarjima shu ma'noga mos bo'lsin.
- en — inglizcha gap (misol gap, kirish, savol, dialog izohi): tabiiy, sodda, bolaga mo'ljallangan.
- seg — o'zbekcha matn ichidagi inglizcha bo'lak: faqat shu bo'lakni tarjima qiling.
- option — test varianti: EMOJI saqlanadi; matn inglizcha bo'lsa tarjima; O'ZBEKCHA bo'lsa AYNAN o'zgarishsiz qoladi.
- board — doska matni (bir necha satr, «—» bilan dialog bo'lishi mumkin): faqat inglizcha qismlar tarjima, o'zbekcha va emoji saqlanadi, satrlar tartibi o'zgarmaydi.
- uzname — O'ZBEKCHA nom/maqsad: o'zgarishsiz qoldiring; faqat ichidagi inglizcha so'z/ibora bo'lsa (Hello va Hi, Touch your nose!, «Can I help you?») o'shani tarjima qiling.
- class — o'qituvchining sinf iborasi ("Look!", "Listen and repeat:" …). {w}, {r}, {names}, {a}, {b}, {name} belgilari AYNAN saqlansin.

Qoidalar: hech qanday [en] kabi teg yozmang. Ismlar (Anvar, Ali, Madina, Kabutar) o'zgarmaydi. «Kabutar» — qushcha qahramon nomi.
Bir xil ingliz matni turli joyda bitta tarjimaga ega bo'ladi (id bitta). Rom: "say" turidagi HAR bir id uchun (ru, ar, ko, ja, zh) —
standart lotincha o'qilishi: ru — oddiy transliteratsiya (Privet!), ar — oddiy transliteratsiya (marhaban), ko — Revised Romanization,
ja — Hepburn, zh — pinyin tovush belgilari bilan (nǐ hǎo).
Tekshirish: `python tools/bogcha_tillar.py check <til>` (loyiha ildizida) — "0 muammo" bo'lishi kerak.
