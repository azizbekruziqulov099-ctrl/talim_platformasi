// REV111: bog'cha darsi uch tilda tushuntiriladi — o'zbek, rus, ingliz (izoh tili). O'rganiladigan til o'zgarmaydi.
// Miyadagi matnlar allaqachon izoh tilida keladi; bu yerda — ustozning o'zi aytadigan tayyor gaplari (salom, ob-havo,
// maqtov, «yana bir bor ayt»). Izoh tili rus/ingliz bo'lsa, gap shu til tegiga olinadi — o'z ovozida o'qilsin.

const TAGS = /\[(uz|en|ru|de|fr|es|ar|tr|zh|ja|ko)\]([\s\S]*?)\[\/\1\]/gi;

/** Miya qaysi tilda tushuntirilgan.
 *  REV126: 1) fan nomidagi «(izoh: ingliz)» — eng ishonchli; 2) birinchi qadam to'liq [ru]/[en] ichida bo'lsa — o'sha;
 *  3) birinchi qadam faqat o'rganiladigan tilda bo'lsa (koreyscha salom) — butun dars bo'yicha: tegsiz o'zbekcha matn
 *  deyarli yo'q, [en]/[ru] izohlar bor — demak izoh shu til. Avval bunday darslar «uz» deb topilib, ustoz o'zbekcha gapirardi. */
const IZOH_FAN = /\(\s*izoh\s*:\s*([^)]+)\)/i;
const IZOH_NOM = { rus: "ru", ruscha: "ru", ru: "ru", ingliz: "en", inglizcha: "en", en: "en", english: "en", "o'zbek": "uz", uz: "uz" };
const harflar = (t) => (String(t).match(/\p{L}/gu) || []).length;
export function darsIzohi(steps = [], fan = "") {
  const fm = IZOH_FAN.exec(String(fan || ""));
  if (fm) { const k = IZOH_NOM[fm[1].trim().toLowerCase().replace(/[‘’ʻ`]/g, "'")]; if (k) return k; }
  const s = steps.find((x) => String(x?.ovoz || "").trim());
  if (!s) return "uz";
  const text = String(s.ovoz);
  const target = fanTili(fan);
  const m = /^\s*\[(ru|en)\]/i.exec(text);
  if (m && m[1].toLowerCase() !== target && !/\p{L}/u.test(text.replace(TAGS, " "))) return m[1].toLowerCase();
  let tegsiz = 0;
  const izohda = { ru: 0, en: 0 };
  for (const x of steps) {
    const t = String(x?.ovoz || "");
    tegsiz += harflar(t.replace(TAGS, " "));
    for (const mm of t.matchAll(TAGS)) { const l = mm[1].toLowerCase(); if (l in izohda) izohda[l] += harflar(mm[2]); }
  }
  if (target && target in izohda) delete izohda[target];   // ingliz tili darsida [en] — o'rganiladigan til, izoh emas
  const [best, n] = Object.entries(izohda).concat([["uz", 0]]).sort((a, b) => b[1] - a[1])[0];
  // ingliz tili darsi o'zbek izohida: [en] ko'p, lekin tegsiz o'zbekcha ham ko'p — «uz» qoladi
  if (n > 0 && tegsiz <= n * 0.25) return best;
  return "uz";
}

const FAN_TILI = [[/ingliz|english/i, "en"], [/rus|russian|русск/i, "ru"], [/arab/i, "ar"], [/turk/i, "tr"], [/nemis|german/i, "de"],
  [/fransuz|french/i, "fr"], [/ispan|spanish/i, "es"], [/koreys|korean/i, "ko"], [/yapon|japan/i, "ja"], [/xitoy|chinese/i, "zh"]];
const TIL_EMAS = /matem|atrof|tabiat|mantiq|logic|math|nature|science|sanoq/i;

/** REV121: fan nomidan o'rganiladigan til. «Matematika (izoh: rus)» — null (til darsi emas); noma'lum fan — undefined. */
export function fanTili(fan = "") {
  const f = String(fan || "").replace(/\(\s*izoh[^)]*\)/gi, "");
  if (!f.trim()) return undefined;
  if (TIL_EMAS.test(f)) return null;
  const hit = FAN_TILI.find(([re]) => re.test(f));
  return hit ? hit[1] : undefined;
}

/** O'rganiladigan til: qisqa (≤4 so'z) teglangan bo'laklarning eng ko'p uchragani, izoh tilidan boshqasi.
 *  REV121: fan nomi berilsa — avval undan (matematika/atrof-muhit/mantiq rus izohida ham til darsi emas). */
export function darsTiliIzoh(steps = [], izoh = "uz", fan = "") {
  const byFan = fanTili(fan);
  if (byFan === null) return null;
  if (byFan) return byFan;
  const count = {};
  for (const s of steps) {
    for (const m of String(s?.ovoz || "").matchAll(TAGS)) {
      const lang = m[1].toLowerCase();
      if (lang === "uz" || m[2].trim().split(/\s+/).length > 4) continue;
      count[lang] = (count[lang] || 0) + 1;
    }
  }
  const other = Object.entries(count).filter(([l]) => l !== izoh).sort((a, b) => b[1] - a[1]);
  if (other.length) return other[0][0];
  return count[izoh] ? izoh : null;
}

/** Tegsiz qolgan matnni izoh tili tegiga oladi (o'zbekcha bo'lsa — o'zgarmaydi). */
export function izohTeg(text, izoh = "uz") {
  if (!text || !izoh || izoh === "uz") return text;
  const out = [];
  let pos = 0;
  const push = (part) => {
    if (!/\p{L}/u.test(part)) { out.push(part); return; }
    const lead = part.match(/^\s*/)[0];
    const trail = part.match(/\s*$/)[0];
    out.push(`${lead}[${izoh}]${part.slice(lead.length, part.length - trail.length)}[/${izoh}]${trail}`);
  };
  for (const m of String(text).matchAll(TAGS)) {
    if (m.index > pos) push(text.slice(pos, m.index));
    out.push(m[0]);
    pos = m.index + m[0].length;
  }
  if (pos < text.length) push(text.slice(pos));
  return out.join("");
}

/** Ustozning tayyor gaplari. Kalit — o'zbekcha shablon ({p}, {w} — chet tilidagi teglangan bo'lak). */
export const GAPLAR = {
  ru: {
    "Endi sen ayt: {p}": "Теперь ты скажи: {p}",
    "Yana bir bor ayt: {p}": "Скажи ещё раз: {p}",
    "Takrorlang: {p}": "Повторите: {p}",
    "Yana bir bor, aniqroq takrorlang: {p}": "Ещё раз, чётче: {p}",
    "Ovozing eshitilmadi. Balandroq va dadil ayt: {p}": "Тебя не слышно. Скажи громче и смелее: {p}",
    "Ovoz eshitilmadi. Balandroq ayting: {p}": "Голос не слышно. Скажите громче: {p}",
    "Juda yaqin!": "Почти получилось!", "Yaxshi harakat!": "Хорошая попытка!", "Yaqin.": "Близко.", "Yana urinib ko‘ring.": "Попробуйте ещё раз.",
    "{praise} Sen shunday aytding:": "{praise} Ты сказал так:",
    "{praise} Siz shunday aytdingiz:": "{praise} Вы сказали так:",
    "Men esa shunday aytaman: {p} Yana bir bor ayt!": "А я говорю так: {p} Скажи ещё раз!",
    "To‘g‘risi: {p} Yana bir bor takrorlang.": "Правильно так: {p} Повторите ещё раз.",
    "Sen zo‘r harakat qilding! Keyingi safar albatta chiqadi. Birga aytamiz: {p}": "Ты очень старался! В следующий раз обязательно получится. Скажем вместе: {p}",
    "To‘g‘risi: {p}": "Правильно так: {p}",
    "Barakalla! Juda to‘g‘ri aytding!": "Молодец! Очень правильно!", "Zo‘r! Ana shunday!": "Здорово! Вот так!", "Ofarin! Sen zo‘rsan!": "Умница! Ты супер!",
    "Barakalla! Hammasini aytding!": "Молодец! Ты всё сказал!", "Yaxshi harakat! Keyingi safar yana aytamiz.": "Хорошая попытка! В следующий раз скажем ещё.",
    "Barakalla! {p}": "Молодец! {p}",
    "Sen {w} deding — bu ham sen bilgan so'z, zo'r! Lekin bu yerda: {p} Qani, ayt!": "Ты сказал {w} — это тоже слово, которое ты знаешь, здорово! Но здесь: {p} Ну-ка, скажи!",
    "Qalaysan? ⏸": "Как дела? ⏸",
    "Sen ham shunday javob ber: {p} ⏸": "Ответь и ты так же: {p} ⏸",
    "Derazaga qara! {p} ⏸": "Посмотри в окно! {p} ⏸",
    "Derazaga qara! Bugun havo qanday? ⏸": "Посмотри в окно! Какая сегодня погода? ⏸",
    "Tashqari sovuq: {p} Issiq kiyin!": "На улице холодно: {p} Одевайся тепло!",
    "Tashqari issiq: {p} Ko'p suv ich!": "На улице жарко: {p} Пей больше воды!",
    "O'tgan safar «{name}» darsini o'tgandik.": "В прошлый раз у нас был урок «{name}».",
    "Esingdami?": "Помнишь?", "Bu nima? ⏸": "Что это? ⏸", "Bu — {p}.": "Это — {p}.", "Endi yangi darsga o'tamiz!": "А теперь — новый урок!",
    "👋 Salom!": "👋 Привет!", "Bugungi ob-havo": "Погода сегодня", "🔁 Esingdami?": "🔁 Помнишь?",
    // REV121: o'yin, natija, test
    "Qani, top: {p}": "Ну-ка, найди: {p}", "Barmog'ing bilan bos: {p}": "Нажми пальчиком: {p}",
    "Bu emas. Yana qidir!": "Не то. Поищи ещё!", "Mana u: {p}": "Вот он: {p}", "Topding! Yulduzcha seniki!": "Нашёл! Звёздочка твоя!",
    "Barakalla! O'yinda {n} ta yulduzcha yig'ding!": "Молодец! В игре ты собрал звёздочек: {n}!",
    "Hechqisi yo'q, keyingi safar albatta topasan!": "Ничего, в следующий раз обязательно найдёшь!",
    "Barakalla! Endi o'ynaymiz!": "Молодец! А теперь поиграем!", "Barakalla! To'g'ri!": "Молодец! Правильно!",
    "Hechqisi yo'q! To'g'ri javob yashil rasmda.": "Ничего страшного! Правильный ответ — на зелёной картинке.",
    "Barakalla! Uchta yulduz! Sen zo'rsan!": "Молодец! Три звезды! Ты супер!",
    "Yaxshi harakat! Yana o'ynasak, yulduzlar ko'payadi!": "Хорошая попытка! Сыграем ещё — звёзд станет больше!",
    "Bu safar yulduzcha yo'q. Qani, yana bir bor urinib ko'ramiz!": "В этот раз звёздочек нет. Давай попробуем ещё раз!",
    "Xayrli tong!": "Доброе утро!", "Xayrli kech!": "Добрый вечер!",
    "Rasmga qara! Bu — {p}. Endi sen ayt!": "Посмотри на картинку! Это — {p}. Теперь скажи ты!",
    "Rasmga qara. Men so'rayman:": "Посмотри на картинку. Я спрошу:", "Shu tilda javob ber!": "Ответь на этом языке!",
    "Men so'rayman, sen javob ber:": "Я спрошу, а ты ответь:", "Birga aytamiz: {p} ⏸": "Скажем вместе: {p} ⏸",
    "Hechqisi yo'q! To'g'ri javob — {p}.": "Ничего страшного! Правильный ответ — {p}.",
    "Yaxshi harakat! Mana bunday: {p}": "Хорошая попытка! Вот так: {p}",
  },
  en: {
    "Endi sen ayt: {p}": "Now you say it: {p}",
    "Yana bir bor ayt: {p}": "Say it one more time: {p}",
    "Takrorlang: {p}": "Repeat: {p}",
    "Yana bir bor, aniqroq takrorlang: {p}": "Once more, a bit clearer: {p}",
    "Ovozing eshitilmadi. Balandroq va dadil ayt: {p}": "I can't hear you. Say it louder and braver: {p}",
    "Ovoz eshitilmadi. Balandroq ayting: {p}": "I couldn't hear you. Please say it louder: {p}",
    "Juda yaqin!": "So close!", "Yaxshi harakat!": "Good try!", "Yaqin.": "Close.", "Yana urinib ko‘ring.": "Try again.",
    "{praise} Sen shunday aytding:": "{praise} You said:",
    "{praise} Siz shunday aytdingiz:": "{praise} You said:",
    "Men esa shunday aytaman: {p} Yana bir bor ayt!": "And I say it like this: {p} Say it again!",
    "To‘g‘risi: {p} Yana bir bor takrorlang.": "The right way is: {p} Please repeat it.",
    "Sen zo‘r harakat qilding! Keyingi safar albatta chiqadi. Birga aytamiz: {p}": "You tried really hard! Next time you'll get it. Let's say it together: {p}",
    "To‘g‘risi: {p}": "The right way is: {p}",
    "Barakalla! Juda to‘g‘ri aytding!": "Well done! That's exactly right!", "Zo‘r! Ana shunday!": "Great! Just like that!", "Ofarin! Sen zo‘rsan!": "Bravo! You're a star!",
    "Barakalla! Hammasini aytding!": "Well done! You said them all!", "Yaxshi harakat! Keyingi safar yana aytamiz.": "Good try! We'll say them again next time.",
    "Barakalla! {p}": "Well done! {p}",
    "Sen {w} deding — bu ham sen bilgan so'z, zo'r! Lekin bu yerda: {p} Qani, ayt!": "You said {w} — that's a word you know too, great! But here it's: {p} Come on, say it!",
    "Qalaysan? ⏸": "How are you? ⏸",
    "Sen ham shunday javob ber: {p} ⏸": "You answer like this too: {p} ⏸",
    "Derazaga qara! {p} ⏸": "Look out of the window! {p} ⏸",
    "Derazaga qara! Bugun havo qanday? ⏸": "Look out of the window! What's the weather like today? ⏸",
    "Tashqari sovuq: {p} Issiq kiyin!": "It's cold outside: {p} Dress warmly!",
    "Tashqari issiq: {p} Ko'p suv ich!": "It's hot outside: {p} Drink lots of water!",
    "O'tgan safar «{name}» darsini o'tgandik.": "Last time we had the lesson «{name}».",
    "Esingdami?": "Do you remember?", "Bu nima? ⏸": "What is it? ⏸", "Bu — {p}.": "This is {p}.", "Endi yangi darsga o'tamiz!": "Now let's start a new lesson!",
    "👋 Salom!": "👋 Hello!", "Bugungi ob-havo": "Today's weather", "🔁 Esingdami?": "🔁 Do you remember?",
    // REV121: game, result, test
    "Qani, top: {p}": "Can you find it? {p}", "Barmog'ing bilan bos: {p}": "Tap it with your finger: {p}",
    "Bu emas. Yana qidir!": "Not that one. Look again!", "Mana u: {p}": "Here it is: {p}", "Topding! Yulduzcha seniki!": "You found it! A star for you!",
    "Barakalla! O'yinda {n} ta yulduzcha yig'ding!": "Well done! You collected {n} stars in the game!",
    "Hechqisi yo'q, keyingi safar albatta topasan!": "That's okay, next time you'll find it!",
    "Barakalla! Endi o'ynaymiz!": "Well done! Now let's play!", "Barakalla! To'g'ri!": "Well done! That's right!",
    "Hechqisi yo'q! To'g'ri javob yashil rasmda.": "That's okay! The right answer is the green picture.",
    "Barakalla! Uchta yulduz! Sen zo'rsan!": "Well done! Three stars! You're great!",
    "Yaxshi harakat! Yana o'ynasak, yulduzlar ko'payadi!": "Good try! Play again to get more stars!",
    "Bu safar yulduzcha yo'q. Qani, yana bir bor urinib ko'ramiz!": "No stars this time. Let's try once more!",
    "Xayrli tong!": "Good morning!", "Xayrli kech!": "Good evening!",
    "Rasmga qara! Bu — {p}. Endi sen ayt!": "Look at the picture! This is {p}. Now you say it!",
    "Rasmga qara. Men so'rayman:": "Look at the picture. I'll ask:", "Shu tilda javob ber!": "Answer in this language!",
    "Men so'rayman, sen javob ber:": "I'll ask, and you answer:", "Birga aytamiz: {p} ⏸": "Let's say it together: {p} ⏸",
    "Hechqisi yo'q! To'g'ri javob — {p}.": "That's okay! The right answer is {p}.",
    "Yaxshi harakat! Mana bunday: {p}": "Good try! Like this: {p}",
  },
};

/** Shablon → izoh tilidagi gap (teglangan). vars ichidagilar o'zgarishsiz qo'yiladi. */
// REV125: kalit tutuq belgisidan qat'i nazar topiladi («to'g'ri» = «to‘g‘ri») — aks holda o'zbekcha gap chet ovozida o'qilardi
const tutuq = (t) => String(t).replace(/[‘’ʻʼ`´]/g, "'");
const GAP_INDEX = {};
function gapTarjima(izoh, tpl) {
  const lugat = GAPLAR[izoh];
  if (!lugat) return null;
  if (!GAP_INDEX[izoh]) GAP_INDEX[izoh] = new Map(Object.entries(lugat).map(([k, v]) => [tutuq(k), v]));
  return lugat[tpl] || GAP_INDEX[izoh].get(tutuq(tpl)) || null;
}

export function gap(izoh, tpl, vars = {}) {
  const src = (izoh && izoh !== "uz" && gapTarjima(izoh, tpl)) || tpl;
  const keys = Object.keys(vars);
  if (!keys.length) return birlashtir(izohTeg(src, izoh));
  // avval shablonni teglaymiz (o'zgaruvchilar belgisi bilan), keyin o'zgaruvchilarni qo'yamiz — ular tegdan tashqarida qoladi
  const marked = src.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? `\u0000${k}\u0001` : m));
  const parts = marked.split(/(\u0000\w+\u0001)/);
  return birlashtir(parts.map((part) => {
    const v = /^\u0000(\w+)\u0001$/.exec(part);
    return v ? String(vars[v[1]] ?? "") : izohTeg(part, izoh);
  }).join(""));
}

/** Ustozlarning fe'li rus va ingliz tilida. */
export const FEL_IZOH = {
  ru: {
    sardor: {
      salom: ["Привет, умница! Я — Сардор-ака.", "Здравствуй, маленький математик! Сардор-ака пришёл.", "Привет, дружок! Сегодня снова считаем вместе!"],
      javob: "У меня тоже всё хорошо, спасибо! Настроение — на пятёрку!",
      maqtov: ["Отлично посчитали!", "Вот это умница!", "Раз, два, три — молодец!"],
      havo: { quyosh: "Сегодня ярко светит солнце!", bulut: "Сегодня на небе много облаков. Посчитаем?", yomgir: "Сегодня идёт дождь. Капли не сосчитать!", qor: "Сегодня идёт снег! Снежинок не сосчитать!" },
    },
    nilufar: {
      salom: ["Привет, солнышко! Я — Нилуфар-опа.", "Здравствуй, милый! Нилуфар-опа пришла с новой сказкой.", "Привет, моя звёздочка! Я по тебе соскучилась!"],
      javob: "У меня тоже всё хорошо, спасибо! А как увидела тебя — стало ещё лучше!",
      maqtov: ["Умница, солнышко!", "Как в сказке!", "Ты очень умный!"],
      havo: { quyosh: "Сегодня солнце светит, как в сказке!", bulut: "Сегодня облака гуляют по небу.", yomgir: "Сегодня капли дождя стучат в окно.", qor: "Сегодня идёт белый снег, как в сказке!" },
    },
    malika: {
      salom: ["Привет, маленький путешественник! Я — Малика-опа.", "Здравствуй, исследователь! Малика-опа зовёт в новое путешествие.", "Привет, дружок! Я взяла лупу — что сегодня откроем?"],
      javob: "У меня тоже всё хорошо, спасибо! Я готова к путешествию!",
      maqtov: ["Чудесное открытие!", "Настоящий путешественник!", "Вот это да, здорово!"],
      havo: { quyosh: "Сегодня солнечно — отличный день для путешествия!", bulut: "Сегодня облачно. Посмотрим, на что похожи облака!", yomgir: "Сегодня дождь. Растения пьют воду и радуются!", qor: "Сегодня идёт снег. Природа надела белое платье!" },
    },
  },
  en: {
    sardor: {
      salom: ["Hello, clever kid! I'm Sardor.", "Hi there, little mathematician! Sardor is here.", "Hello, my friend! Today we'll count together again!"],
      javob: "I'm fine too, thank you! I feel like a top score!",
      maqtov: ["Great counting!", "What a clever kid!", "One, two, three — well done!"],
      havo: { quyosh: "The sun is shining brightly today!", bulut: "There are lots of clouds today. Shall we count them?", yomgir: "It's raining today. Too many drops to count!", qor: "It's snowing today! Too many snowflakes to count!" },
    },
    nilufar: {
      salom: ["Hello, my sunshine! I'm Nilufar.", "Hi, sweetheart! Nilufar is here with a new story.", "Hello, my little star! I missed you!"],
      javob: "I'm fine too, thank you! Seeing you makes me even happier!",
      maqtov: ["Well done, sunshine!", "Just like in a fairy tale!", "You're so clever!"],
      havo: { quyosh: "The sun is shining like in a fairy tale!", bulut: "The clouds are taking a walk across the sky.", yomgir: "Raindrops are tapping on the window today.", qor: "White snow is falling, just like in a fairy tale!" },
    },
    malika: {
      salom: ["Hello, little traveller! I'm Malika.", "Hi, explorer! Malika is inviting you on a new trip.", "Hello, my friend! I've got my magnifying glass — what shall we discover today?"],
      javob: "I'm fine too, thank you! I'm ready for an adventure!",
      maqtov: ["What a discovery!", "A real explorer!", "Wow, that's great!"],
      havo: { quyosh: "It's sunny today — perfect for a trip!", bulut: "It's cloudy today. Let's look at the cloud shapes!", yomgir: "It's raining today. The plants are drinking and happy!", qor: "It's snowing today. Nature is wearing a white dress!" },
    },
  },
};

/** Yonma-yon bir xil teglar birlashtiriladi: «[ru]A[/ru] [ru]B[/ru]» → «[ru]A B[/ru]» (ovoz uzilmasin). */
export function birlashtir(text) {
  return String(text).replace(/\[\/(uz|en|ru|de|fr|es|ar|tr|zh|ja|ko)\](\s*)\[\1\]/g, "$2");
}
