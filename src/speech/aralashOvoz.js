// REV145: HAMMA TILLAR — serverdagi tabiiy (Azure neyron) ovozda. Qurilma ovozi (speechSynthesis) robotdek va
// ustozning jinsini bilmaydi (Sardor aka ayol ovozida gapirardi) — u faqat server umuman javob bermasa, zaxira sifatida
// ishlatiladi (qurilmadaOqi). Quyidagi aralash o'qish faqat qurilma: true berilganda yoqiladi.
export const QURILMA_OVOZI = false;
// REV139: aralash ovoz — o'zbekcha bo'laklar serverdan (Azure, bir marta yaratilib bazada saqlanadi),
// chet tildagi bo'laklar (Hello, Привет, 안녕…) qurilmaning o'z bepul ovozi (speechSynthesis) bilan o'qiladi.
// Shunda Azure'ning bepul oylik limiti faqat o'zbekchaga sarflanadi. Qurilmada o'sha tilning ovozi bo'lmasa
// (masalan, ba'zi telefonlarda arabcha yoki koreyscha) — bo'lak serverga beriladi, gap jim qolmaydi.

const TEG = /\[(en|ru|de|fr|es|ar|tr|zh|ja|ko|uz)\]([\s\S]*?)\[\/\1\]/gi;
const LOKAL = { en: "en", ru: "ru", de: "de", fr: "fr", es: "es", ar: "ar", tr: "tr", zh: "zh", ja: "ja", ko: "ko" };
const harfBor = (s) => /[\p{L}\p{N}]/u.test(String(s || ""));
// REV140: brauzer ovozi emojini nomi bilan o'qiydi («red apple», «яблоко») — gap g'alati chiqardi. Emoji, belgi va
// tire-chiziqlar olib tashlanadi (server o'zi ham shunday qiladi).
const EMOJI = /(?:\p{Extended_Pictographic}|\p{Regional_Indicator}|[\u20E3\uFE0F\u200D]|\p{Emoji_Modifier})+/gu;
export const brauzerMatni = (s) => String(s || "").replace(/⏸/g, " ").replace(EMOJI, " ").replace(/[|•→←↔＝=_*#~^]+/g, " ").replace(/\s+([,.!?;:])/g, "$1").replace(/\s+/g, " ").trim();

/** Matnni bo'laklarga ajratadi: [{ til: "uz" | "en" | …, matn }]. Tegsiz matn — o'zbekcha. */
export function segmentlar(text) {
  const s = String(text || "");
  const out = [];
  let last = 0;
  for (const m of s.matchAll(TEG)) {
    if (m.index > last) out.push({ til: "uz", matn: s.slice(last, m.index) });
    out.push({ til: m[1].toLowerCase(), matn: m[2] });
    last = m.index + m[0].length;
  }
  if (last < s.length) out.push({ til: "uz", matn: s.slice(last) });
  return out.map((x) => ({ ...x, matn: x.matn.replace(/\s+/g, " ").trim() })).filter((x) => x.matn);
}

// — brauzer ovozlari —
let OVOZLAR = [];
function yangila() {
  try { OVOZLAR = globalThis.speechSynthesis?.getVoices?.() || []; } catch { OVOZLAR = []; }
}
try {
  yangila();
  globalThis.speechSynthesis?.addEventListener?.("voiceschanged", yangila);
} catch { /* eski brauzer */ }

// REV140: rus tili har doim serverdagi tabiiy (neyron) ovozda o'qiladi — qurilmalardagi ruscha ovozlar
// (Windows «Irina», Android «compact» va h.k.) robotdek, urg'ularni xato qo'yadi. Server ovozi bir marta yaratilib,
// bazada saqlanadi — keyingi safar limit sarflanmaydi.
export const SERVERDA = new Set(["ru"]);
// Faqat sifatli brauzer ovozi ishlatiladi (Google, Microsoft «Online (Natural)», Apple «Enhanced/Premium»).
// Qurilmada faqat oddiy (robot) ovoz bo'lsa — bo'lak serverga beriladi.
const SIFATLI = /google|natural|online|neural|premium|enhanced/i;

/** Shu til uchun sifatli brauzer ovozi yoki null (null — bo'lak serverda o'qiladi). */
export function brauzerOvozi(til, ovozlar = null) {
  const kod = LOKAL[til];
  if (!kod || SERVERDA.has(til)) return null;
  if (!ovozlar && !OVOZLAR.length) yangila();
  const ro = (ovozlar || OVOZLAR).filter((v) => String(v.lang || "").toLowerCase().replace("_", "-").startsWith(kod) && SIFATLI.test(v.name || ""));
  if (!ro.length) return null;
  const ball = (v) => (/google/i.test(v.name) ? 3 : 0) + (/natural|online|neural|premium|enhanced/i.test(v.name) ? 2 : 0) + (v.localService ? 0 : 1);
  return [...ro].sort((a, b) => ball(b) - ball(a))[0];
}

/** Reja: ketma-ket bo'laklar — { tur: "server", matn } (teglar saqlanadi) | { tur: "brauzer", til, matn, ovoz } | { tur: "pauza", ms }. */
export function reja(text, { ovozlar = null, takror = false, qurilma = QURILMA_OVOZI } = {}) {
  const out = [];
  const qosh = (q) => {
    const prev = out[out.length - 1];
    if (q.tur === "server" && prev?.tur === "server") { prev.matn = `${prev.matn} ${q.matn}`; return; }
    out.push(q);
  };
  for (const seg of segmentlar(text)) {
    const ovoz = qurilma && seg.til !== "uz" ? brauzerOvozi(seg.til, ovozlar) : null;
    if (ovoz && harfBor(brauzerMatni(seg.matn))) {
      qosh({ tur: "brauzer", til: seg.til, matn: brauzerMatni(seg.matn), ovoz });
      const n = (seg.matn.match(/⏸/g) || []).length;   // so'zdan keyingi jimlik (bola qaytarishi uchun) saqlanadi
      if (n) qosh({ tur: "pauza", ms: n * (takror ? 1800 : 900) });
      continue;
    }
    const matn = seg.til === "uz" ? seg.matn : `[${seg.til}]${seg.matn}[/${seg.til}]`;
    if (!harfBor(seg.matn)) {
      const n = (seg.matn.match(/⏸/g) || []).length;
      if (n) qosh({ tur: "pauza", ms: n * (takror ? 1800 : 900) });
      continue;
    }
    qosh({ tur: "server", matn });
  }
  return out;
}

/** Aralash o'qish kerakmi: kamida bitta chet tildagi bo'lakni brauzer o'qiy oladi. */
export function aralashKerak(text, ovozlar = null, { qurilma = QURILMA_OVOZI } = {}) {
  return reja(text, { ovozlar, qurilma }).some((q) => q.tur === "brauzer");
}

/**
 * REV145: zaxira — server ovoz bera olmasa, gap qurilma ovozida o'qiladi (jim qolgandan yaxshi). Har bo'lak o'z tilida;
 * qurilmada shu tilning ovozi bo'lmasa — bo'lak o'tkazib yuboriladi. Qaytaradi: stop().
 */
export function qurilmadaOqi(text, { rate = 0.9, onEnd } = {}) {
  const synth = globalThis.speechSynthesis;
  let toxtadi = false, timer = null;
  const tamomla = () => { if (toxtadi) return; toxtadi = true; clearTimeout(timer); onEnd?.(); };
  if (!synth || typeof SpeechSynthesisUtterance === "undefined") { timer = setTimeout(tamomla, 400); return { stop() { toxtadi = true; clearTimeout(timer); } }; }
  if (!OVOZLAR.length) yangila();
  const bolaklar = segmentlar(text).map((b) => ({ ...b, matn: brauzerMatni(b.matn) })).filter((b) => harfBor(b.matn));
  let i = -1;
  const keyingi = () => {
    if (toxtadi) return;
    i += 1;
    if (i >= bolaklar.length) { tamomla(); return; }
    const b = bolaklar[i];
    const kod = b.til === "uz" ? "uz" : LOKAL[b.til];
    const ovoz = OVOZLAR.find((v) => String(v.lang || "").toLowerCase().replace("_", "-").startsWith(kod));
    if (!ovoz && b.til !== "uz") { keyingi(); return; }
    let tugadi = false;
    const bitdi = () => { if (tugadi) return; tugadi = true; clearTimeout(timer); setTimeout(keyingi, 150); };
    try {
      const u = new SpeechSynthesisUtterance(b.matn);
      if (ovoz) { u.voice = ovoz; u.lang = ovoz.lang; } else u.lang = "uz-UZ";
      u.rate = rate; u.onend = bitdi; u.onerror = bitdi;
      synth.speak(u);
      timer = setTimeout(bitdi, 3000 + b.matn.length * 160 / Math.max(0.5, rate));
    } catch { bitdi(); }
  };
  try { synth.cancel(); } catch { /* */ }
  keyingi();
  return { stop() { if (toxtadi) return; toxtadi = true; clearTimeout(timer); try { synth.cancel(); } catch { /* */ } } };
}

/**
 * Aralash o'qish. serverUrl(matn) — serverdagi /api/ovoz manzili. Qaytaradi: stop().
 * opts: { rate (brauzer tezligi), playbackRate (server ovozi), takror, onEnd, onBolak(i, q) }
 */
export function aralashOqi(text, serverUrl, opts = {}) {
  const { rate = 0.9, playbackRate = 1, takror = false, onEnd, onBolak } = opts;
  const qadamlar = reja(text, { takror });
  let i = -1, toxtadi = false, audio = null, timer = null;
  const synth = globalThis.speechSynthesis;
  // REV140: o'zbekcha bo'laklar BOSHIDAN birdaniga yuklana boshlaydi — chet so'zdan keyin o'zbekcha davom etganda
  // har safar serverni kutib, gap uzilib-uzilib chiqmasin (tabiiy, ravon nutq).
  const tayyor = new Map();
  try {
    qadamlar.forEach((q, j) => {
      if (q.tur !== "server" || typeof Audio === "undefined") return;
      const a = new Audio(); a.preload = "auto"; a.src = serverUrl(q.matn);
      tayyor.set(j, a);
    });
  } catch { /* eski brauzer — navbat bilan yuklanadi */ }
  const tozala = () => {
    clearTimeout(timer); timer = null;
    if (audio) { try { audio.onended = audio.onerror = null; audio.pause(); audio.src = ""; } catch { /* */ } audio = null; }
  };
  const keyingi = () => {
    if (toxtadi) return;
    tozala();
    i += 1;
    if (i >= qadamlar.length) { toxtadi = true; onEnd?.(); return; }
    const q = qadamlar[i];
    onBolak?.(i, q);
    if (q.tur === "pauza") { timer = setTimeout(keyingi, q.ms); return; }
    if (q.tur === "brauzer" && synth) {
      let tugadi = false;
      const tamom = () => { if (tugadi) return; tugadi = true; clearTimeout(timer); setTimeout(keyingi, takror ? 1500 : 250); };
      try {
        const u = new SpeechSynthesisUtterance(q.matn);
        u.voice = q.ovoz; u.lang = q.ovoz.lang; u.rate = rate;
        u.onend = tamom; u.onerror = tamom;
        synth.speak(u);
        // ba'zi brauzerlarda onend kelmay qoladi — gap uzunligiga qarab davom etamiz
        timer = setTimeout(tamom, 3000 + q.matn.length * 160 / Math.max(0.5, rate));
      } catch { tamom(); }
      return;
    }
    // server bo'lagi (o'zbekcha yoki qurilmada ovozi yo'q til)
    let tugadi = false;
    const tamom = () => { if (tugadi) return; tugadi = true; keyingi(); };
    try {
      const a = tayyor.get(i) || new Audio(serverUrl(q.matn));
      tayyor.delete(i);
      audio = a;
      a.playbackRate = playbackRate;
      a.onended = tamom;
      a.onerror = () => setTimeout(tamom, 400);
      a.play().catch(() => setTimeout(tamom, 600));
      timer = setTimeout(tamom, Math.min(30000, 6000 + q.matn.length * 150));
    } catch { tamom(); }
  };
  try { synth?.cancel(); } catch { /* */ }
  keyingi();
  return {
    stop() {
      if (toxtadi) return;
      toxtadi = true; tozala();
      for (const a of tayyor.values()) { try { a.src = ""; } catch { /* */ } }
      tayyor.clear();
      try { synth?.cancel(); } catch { /* */ }
    },
    get qadamlar() { return qadamlar; },
  };
}
