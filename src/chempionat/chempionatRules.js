// REV143: Bolalar ligasi — sof yordamchilar (brauzersiz sinaladi).

/** Jamoa nomlari (server kalit beradi, nom bola tilida ko'rsatiladi). */
export const JAMOA_NOM = {
  sherlar: { uz: "Sherlar", ru: "Львы", en: "Lions" },
  burgutlar: { uz: "Burgutlar", ru: "Орлы", en: "Eagles" },
  delfinlar: { uz: "Delfinlar", ru: "Дельфины", en: "Dolphins" },
  yolbarslar: { uz: "Yo‘lbarslar", ru: "Тигры", en: "Tigers" },
  ayiqlar: { uz: "Ayiqlar", ru: "Медведи", en: "Bears" },
  tulkilar: { uz: "Tulkilar", ru: "Лисята", en: "Foxes" },
  fillar: { uz: "Fillar", ru: "Слоны", en: "Elephants" },
  pandalar: { uz: "Pandalar", ru: "Панды", en: "Pandas" },
  pingvinlar: { uz: "Pingvinlar", ru: "Пингвины", en: "Penguins" },
  boyogli: { uz: "Boyo‘g‘lilar", ru: "Совы", en: "Owls" },
  asalarilar: { uz: "Asalarilar", ru: "Пчёлки", en: "Bees" },
  kapalaklar: { uz: "Kapalaklar", ru: "Бабочки", en: "Butterflies" },
  toshbaqalar: { uz: "Toshbaqalar", ru: "Черепахи", en: "Turtles" },
  raketalar: { uz: "Raketalar", ru: "Ракеты", en: "Rockets" },
  yulduzlar: { uz: "Yulduzlar", ru: "Звёзды", en: "Stars" },
  kamalaklar: { uz: "Kamalaklar", ru: "Радуги", en: "Rainbows" },
  chaqmoqlar: { uz: "Chaqmoqlar", ru: "Молнии", en: "Lightning" },
  kungaboqar: { uz: "Kungaboqarlar", ru: "Подсолнухи", en: "Sunflowers" },
  jirafalar: { uz: "Jirafalar", ru: "Жирафы", en: "Giraffes" },
  delfin2: { uz: "Kitlar", ru: "Киты", en: "Whales" },
};

const L = (loc) => (loc === "ru" || loc === "en" ? loc : "uz");

/** Jamoa ko'rinadigan nomi: admin bergan nom (yoki yakka bolaning ismi), bo'lmasa — kalit nomi bola tilida. */
export function jamoaNomi(j, loc = "uz") {
  if (!j) return "—";
  if (j.nomi) return /^\d+$/.test(j.nomi) ? `${JAMOA_NOM[j.kalit]?.[L(loc)] || ""} ${j.nomi}`.trim() : j.nomi;
  return JAMOA_NOM[j.kalit]?.[L(loc)] || j.kalit || "—";
}

export const BOSQICH_TARTIB = ["1/32", "1/16", "1/8", "1/4", "1/2", "final"];
export const BOSQICH_NOM = {
  guruh: "Guruh bosqichi", "1/32": "1/32 final", "1/16": "1/16 final", "1/8": "1/8 final", "1/4": "Chorak final",
  "1/2": "Yarim final", final: "Final", "3-orin": "3-o‘rin uchun",
};
export const bosqichNomi = (b) => BOSQICH_NOM[b] || b || "";

export const HOLAT = {
  royxat: { emoji: "📝", nom: "Ro‘yxat ochiq" },
  jamoa: { emoji: "👥", nom: "Jamoalar tuzildi" },
  davom: { emoji: "⚽", nom: "Davom etmoqda" },
  tugadi: { emoji: "🏁", nom: "Tugadi" },
  bekor: { emoji: "✖️", nom: "Bekor qilindi" },
};

export const KUBOK = {
  oltin: { emoji: "🏆", nom: "Oltin kubok", tartib: 0 },
  kumush: { emoji: "🥈", nom: "Kumush kubok", tartib: 1 },
  bronza: { emoji: "🥉", nom: "Bronza kubok", tartib: 2 },
  yulduz: { emoji: "⭐", nom: "Eng yaxshi o‘yinchi", tartib: 3 },
  ishtirok: { emoji: "🎖️", nom: "Ishtirokchi medali", tartib: 4 },
};

export const FAN = {
  soz: { emoji: "🗣️", nom: "Til so‘zlari" },
  harakat: { emoji: "🤸", nom: "Harakat o‘yinlari" },
  bilim: { emoji: "🧠", nom: "Bilim: sanash va mantiq" },
};

export const TIL = {
  uz: ["🇺🇿", "O‘zbek tili"], ru: ["🇷🇺", "Rus tili"], en: ["🇬🇧", "Ingliz tili"], de: ["🇩🇪", "Nemis tili"],
  fr: ["🇫🇷", "Fransuz tili"], es: ["🇪🇸", "Ispan tili"], ar: ["🇸🇦", "Arab tili"], tr: ["🇹🇷", "Turk tili"],
  zh: ["🇨🇳", "Xitoy tili"], ja: ["🇯🇵", "Yapon tili"], ko: ["🇰🇷", "Koreys tili"],
};

/** Pley-off ustunlari (to'r): mavjud bosqichlar tartib bilan; 3-o'rin alohida. */
export function pleyoffUstunlar(uchrashuvlar = []) {
  const ko = uchrashuvlar.filter((u) => u.bosqich !== "guruh");
  const ustun = BOSQICH_TARTIB.filter((b) => ko.some((u) => u.bosqich === b))
    .map((b) => ({ bosqich: b, uchrashuvlar: ko.filter((u) => u.bosqich === b).sort((a, c) => a.tartib - c.tartib) }));
  return { ustun, uchinchi: ko.find((u) => u.bosqich === "3-orin") || null };
}

/** Qolgan vaqt: «2 kun 3 soat», «5 soat 10 daq», «12 daq». */
export function qolganVaqt(msLeft, T = (s) => s) {
  const m = Math.max(0, Math.round(msLeft / 60000));
  const kun = Math.floor(m / 1440), soat = Math.floor((m % 1440) / 60), daq = m % 60;
  if (kun) return `${kun} ${T("kun")}${soat ? ` ${soat} ${T("soat")}` : ""}`;
  if (soat) return `${soat} ${T("soat")}${daq ? ` ${daq} ${T("daq.")}` : ""}`;
  return `${Math.max(1, daq)} ${T("daq.")}`;
}

/** Bolaning kubok javoni: qimmatlisi oldinda, keyin yangisi. */
export function javon(kuboklar = []) {
  return [...kuboklar].sort((a, b) => (KUBOK[a.kubok]?.tartib ?? 9) - (KUBOK[b.kubok]?.tartib ?? 9) || (b.created_at || 0) - (a.created_at || 0));
}

/** Natija yulduzlari (o'yin oxirida): to'g'ri javoblar ulushi bo'yicha 1–3. */
export function yulduzlar(togri, jami) {
  if (!jami) return 0;
  const f = togri / jami;
  return f >= 0.9 ? 3 : f >= 0.6 ? 2 : f > 0 ? 1 : 0;
}

/** Sanash kartasidagi bitta narsa o'lchami (kartaning 4:3 maydoniga n ta narsa sig'sin): kenglikka nisbatan %. */
export function sanoqOlcham(n) {
  const c = n <= 1 ? 1 : n <= 4 ? 2 : n <= 6 ? 3 : 4;
  const r = Math.ceil(n / c);
  return Math.floor(Math.min(100 / c, 75 / r) * 0.96);
}
