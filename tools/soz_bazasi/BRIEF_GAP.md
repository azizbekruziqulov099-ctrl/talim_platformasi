# Gap bazasi — «Gap tuz» va «Gapni eshit, rasmni top» o'yinlari uchun (REV696)

Avval `tools/soz_bazasi/BRIEF.md` dagi til qoidalarini o'qi (yozuv turi: ja — hiragana/katakana, kanji YO'Q; ar — harakatsiz; zh — soddalashtirilgan).
Kirish: `tools/soz_bazasi/gap_xom_N.json` — rasmli so'zlar: {kalit, fayl, turkum, w:{11 til}}.
Har so'z uchun BITTA juda sodda gap yoz — 11 tilda bir xil ma'noda. Gap rasmga mos bo'lsin (rasmda faqat o'sha narsa bor deb hisobla):
bola rasmga qarab shu gapni ayta olsin. Gapda albatta o'sha so'z qatnashsin (kerakli kelishik/shaklda).

Qoidalar:
- Daraja A1: hozirgi zamon, 3–6 so'z. Murakkab ergash gap, kam uchraydigan so'z yo'q.
- Gaplar xilma-xil bo'lsin — hammasi «Bu — olma» bo'lmasin. Qoliplar aralash: «Olma qizil», «Men olma yeyman», «Mushuk sut ichadi»,
  «Avtobus katta», «Shifokor kasalxonada ishlaydi», «Men velosiped minaman», «Quyon tez yuguradi», «Menga muzqaymoq yoqadi».
  Bir qolip butun fayl bo'yicha 15% dan oshmasin. Haqiqatga to'g'ri gap yoz (fil kichik emas).
- Grammatika TO'G'RI bo'lishi shart: artikl, kelishik (ru, de, ar, tr, ko, ja), moslashuv (fr/es sifat jinsi). Ishonching komil bo'lmasa soddaroq gap tanla.
- Format: har til uchun TOKENLAR ro'yxati (so'zma-so'z; o'yinda aralashtirib beriladi). Birinchi token bosh harf bilan (lotin/kirill), oxirgi tinish belgisi YOZILMAYDI.
  de/fr/es da artikl alohida token emas, ot bilan birga bitta token EMAS — alohida token bo'lsin («Die», «Katze», «trinkt», «Milch»); fr «l’» ot bilan birga («l’école»).
  zh, ja: ma'noli bo'laklarga bo'l (zh: «我», «吃», «苹果»; ja: «わたしは», «りんごを», «たべます» — yuklama so'zga yopishgan holda). ko: bo'shliq bo'yicha.
  ar: so'zma-so'z, o'qilish tartibida.
- Tokenlar soni har tilda 2–7. Bitta gap ichida bir xil token ikki marta kelmasin.
Chiqish: `tools/soz_bazasi/gap_qism_N.json`: [{"kalit": "<kirishdagi kalit>", "g": {"uz": [...], "ru": [...], "en": [...], "de": [...], "fr": [...], "es": [...], "ar": [...], "tr": [...], "zh": [...], "ja": [...], "ko": [...]}}]
So'zga rasmga mos sodda gap topilmasa — o'sha so'zni tashlab ket.
Tekshir: `python3 tools/soz_bazasi/tekshir_gap.py tools/soz_bazasi/gap_qism_N.json` → 0 xato. Commit qilma, boshqa fayllarga tegma.
Hisobot (qisqa, o'zbekcha): nechta gap, shubhali grammatika (til + gap).
