// REV144: darsdagi rasmlar jonli — har rasm o'z ma'nosiga mos 1–2 soniyalik harakat qiladi (sakraydi, yuradi,
// aylanadi, uchadi…), keyin tinch turadi; bosilsa yana bir marta harakat qiladi. Emoji o'rniga — rassom chizgan rasm.
import { SOZLAR, TURKUM } from "./xonalar/xonaLugat.js";

const tozala = (e) => String(e || "").replace(/[️‍]/g, "").trim();
const sozNorm = (w) => String(w || "").toLowerCase().replace(/[^a-z]/g, "");

let EMOJI_ID = null;
/** Emoji → so'z id (bir emojini ikki so'z ishlatsa — noaniq, olinmaydi). */
function emojiXarita() {
  if (EMOJI_ID) return EMOJI_ID;
  const sanoq = {};
  for (const [id, s] of Object.entries(SOZLAR)) { const e = tozala(s.emoji); if (e) (sanoq[e] = sanoq[e] || []).push(id); }
  EMOJI_ID = Object.fromEntries(Object.entries(sanoq).filter(([, ids]) => ids.length === 1).map(([e, ids]) => [e, ids[0]]));
  return EMOJI_ID;
}

/** Rasm qaysi so'zniki: inglizcha so'z (kitobdagi «🍎|apple») yoki emoji orqali. */
export function sozId({ soz = "", emoji = "" } = {}) {
  const w = sozNorm(soz);
  if (w && SOZLAR[w]) return w;
  return emojiXarita()[tozala(emoji)] || null;
}

/** Bitta emoji uchun chizilgan rasm (xonalar rasmi). rasmlar — {id: url}. Bir nechta emoji (sanoq) — null. */
export function emojiRasm(emoji, rasmlar) {
  const e = tozala(emoji);
  if (!e || /\s/.test(e)) return null;
  const id = emojiXarita()[e];
  return id && rasmlar?.[id] ? { id, src: rasmlar[id] } : null;
}

const MAXSUS = {
  jump: "sakra", run: "yugur", swim: "suz", sing: "kuyla", dance: "raqs", draw: "chiz",
  bird: "uch", plane: "uch", helicopter: "uch", kite: "uch", balloon: "kotaril", butterfly: "uch",
  frog: "sakra", rabbit: "sakra", duck: "lapang", hen: "lapang", fish: "suz",
  ball: "dumala", sun: "nur", rain: "tomchi", snow: "qor", wind: "shamol", cloud: "suzib", rainbow: "kamalak",
  clock: "aylan", happy: "sakra", sad: "egil", cold: "titra", hot: "terla", hungry: "silkin",
  hello: "salom", mother: "salom", father: "salom", teacher: "salom", granny: "salom", grandpa: "salom",
};
const TURKUM_HARAKAT = {
  hayvon: "lapang", transport: "yur", meva: "dumala", ovqat: "sakrab_chiq", ichimlik: "sakrab_chiq", kiyim: "tebran",
  oyinchoq: "sakra", maktab: "aylan", rang: "puls", tana: "silkin", odam: "salom", havo: "suzib", fasl: "puls", vaqt: "puls",
};

/** So'zga mos harakat turi (CSS: .an-{tur}). Noma'lum bo'lsa — «chiq» (sakrab paydo bo'ladi). */
export function harakatTuri(id) {
  if (!id) return "chiq";
  if (MAXSUS[id]) return MAXSUS[id];
  for (const [t, ids] of Object.entries(TURKUM)) if (ids.includes(id)) return TURKUM_HARAKAT[t] || "chiq";
  return "chiq";
}

export const HARAKAT_TURLARI = ["chiq", "sakra", "yugur", "suz", "kuyla", "raqs", "chiz", "uch", "kotaril", "lapang", "dumala", "nur",
  "tomchi", "qor", "shamol", "suzib", "kamalak", "aylan", "egil", "titra", "terla", "silkin", "salom", "yur", "sakrab_chiq", "tebran", "puls"];
