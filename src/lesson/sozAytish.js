// REV145: til darsida yangi so'z o'rgatilganda bola uni mikrofonga BIR MARTA aytadi (eshitilmasa — yana bir imkon,
// jami 2 urinish). Sof qismi (so'zni ajratish, baho) brauzersiz sinaladi; tingla() — brauzer SpeechRecognition.
import { gradeSpeech } from "../speech/speakRules.js";
import { CONTENT_LOCALES } from "../speech/language.js";

const TEG = /\[(en|ru|de|fr|es|ar|tr|zh|ja|ko)\]([^[\]]{1,60}?)\[\/\1\]/gi;
const BUYRUQ_SOZ = /^(?:say it together|say it with me|repeat after me|look|listen|listen and repeat|again|one more time|your turn|now you|now you say it|good job|well done|great job|let'?s go|hello everyone|bye bye|let'?s say it together)$/i;

function chunkSozi(bolak, til) {
  let topildi = null;
  for (const m of bolak.matchAll(TEG)) {
    if (m[1].toLowerCase() !== til) continue;
    const phrase = m[2].trim().replace(/[.!?。！？]+$/u, "").trim();
    if (!phrase || phrase.split(/\s+/).length > 4 || BUYRUQ_SOZ.test(phrase) || /[:：]$/.test(phrase)) continue;
    topildi = phrase;
  }
  return topildi;
}

/**
 * Gap «⏸» (bolaga qaytarish joyi) bo'yicha bo'laklarga ajratiladi: [{ matn, soz }]. soz — shu bo'lakdan keyin bola
 * aytadigan o'rganiladigan tildagi qisqa ibora ({lang, phrase}) yoki null. Bir so'z ikki marta so'ralmaydi, jami ≤3.
 */
export function sozBolaklari(spoken, til) {
  const s = String(spoken || "");
  const qismlar = s.split("⏸");
  const out = [];
  const korilgan = new Set();
  qismlar.forEach((q, k) => {
    const matn = q.replace(/\s{2,}/g, " ").trim();
    let soz = null;
    if (til && k < qismlar.length - 1 && korilgan.size < 3) {
      const p = chunkSozi(q, til);
      if (p && !korilgan.has(p.toLowerCase())) { korilgan.add(p.toLowerCase()); soz = { lang: til, phrase: p }; }
    }
    if (matn || soz) out.push({ matn, soz });
  });
  return out;
}

/** Gapdagi bola aytishi kerak bo'lgan so'zlar: [{ lang, phrase }] (takrorlanmaydi, ko'pi bilan 3 ta). */
export function aytiladiganSozlar(spoken, til) {
  return sozBolaklari(spoken, til).map((b) => b.soz).filter(Boolean);
}

/** Bola aytgani to'g'rimi. Bog'cha bolasi uchun yumshoq: 2-urinishda «yaqin» ham qabul. */
export function aytdiMi(alternatives, item, urinish = 0) {
  const g = gradeSpeech(alternatives || [], item?.phrase || "", item?.lang || "");
  return { ...g, ok: g.stars >= (urinish > 0 ? 1 : 2) };
}

/** Gapdan bolaga qaytarish pauzalari olinadi (mikrofon o'zi kutadi). */
export const pauzasiz = (spoken) => String(spoken || "").replace(/\s*⏸\s*/g, " ").replace(/\s{2,}/g, " ").trim();

/**
 * Mikrofonni ochib bir marta tinglaydi. Qaytaradi: Promise<{ alts: string[], xato?: "ruxsat" | "yoq", toxtatildi?: true }>.
 * xato «ruxsat» — mikrofonga ruxsat berilmagan, «yoq» — qurilmada mikrofon/tanish yo'q (darsning qolgan qismida so'ralmaydi).
 * stop() — tinglashni to'xtatadi (toxtatildi: true).
 */
export function tingla(lang, { kutish = 7000 } = {}) {
  const Recognition = globalThis.SpeechRecognition || globalThis.webkitSpeechRecognition;
  let r = null, tugadi = false, timer = null, resolveFn = () => {};
  const promise = new Promise((resolve) => {
    resolveFn = (v) => { if (tugadi) return; tugadi = true; clearTimeout(timer); try { r?.abort(); } catch { /* */ } resolve(v); };
    if (!Recognition) { resolveFn({ alts: [], xato: "yoq" }); return; }
    try {
      r = new Recognition();
      r.lang = CONTENT_LOCALES[lang] || "en-US";
      r.interimResults = false;
      r.maxAlternatives = 5;
      r.onresult = (e) => resolveFn({ alts: Array.from(e.results?.[0] || []).map((a) => a.transcript) });
      r.onerror = (e) => resolveFn({ alts: [], xato: e?.error === "not-allowed" || e?.error === "service-not-allowed" ? "ruxsat"
        : e?.error === "audio-capture" || e?.error === "language-not-supported" ? "yoq" : undefined });
      r.onend = () => resolveFn({ alts: [] });
      r.start();
      timer = setTimeout(() => resolveFn({ alts: [] }), kutish);
    } catch { resolveFn({ alts: [], xato: "yoq" }); }
  });
  return { promise, stop: () => resolveFn({ alts: [], toxtatildi: true }) };
}
