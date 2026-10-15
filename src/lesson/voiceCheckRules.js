// REV105: dars oxiridagi ovozli tekshiruv — «Takrorla!» — sof yordamchilar (brauzersiz sinaladi).
import { gradeSpeech } from '../speech/speakRules.js';
import { gap } from '../kid/izohTil.js';

const FOREIGN = /\[(en|ru|de|fr|es|ar|tr|zh|ja|ko)\]([\s\S]*?)\[\/\1\]/gi;
const NOT_TARGET = /^(?:say it together|say it with me|repeat after me|look|listen|listen and repeat|again|one more time|your turn|now you|good job|well done|great job|let'?s go|hello everyone|bye bye)$/i;
const LEAD = /^[\s\-–—•*·>]+|^\d+[.)]\s*|^[^\p{L}\p{N}]+/u;

/** Har tinglovchiga nechta ibora va qancha uzunlik. */
export const VOICE_LIMITS = {
  // REV110: bog'chada ko'proq gapirsin — darsning 5 tagacha iborasi, 6 so'zgacha gap.
  // REV145: urinish 3 emas — 2 ta (bola zerikmasin; ikkinchisida «yaqin» ham qabul).
  bogcha: { count: 5, maxWords: 6, uzMaxWords: 5, tries: 2 },
  oquvchi: { count: 3, maxWords: 6, uzMaxWords: 12, tries: 2 },
  talaba: { count: 3, maxWords: 8, uzMaxWords: 16, tries: 2 },
};

function words(text) { return String(text || '').trim().split(/\s+/).filter(Boolean); }

function cleanLine(line) {
  return String(line || '')
    .replace(/\[\d{1,2}\]/g, ' ')
    .replace(LEAD, '')
    .replace(/[*_#`]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/[:;,–—-]+$/u, '')
    .trim();
}

function add(out, item, limit) {
  const key = `${item.lang}:${item.phrase.toLowerCase()}`;
  if (out.length < limit && !out.some((x) => `${x.lang}:${x.phrase.toLowerCase()}` === key)) out.push(item);
}

/**
 * Darsdan takrorlatiladigan iboralar:
 * 1) darsda alohida berilgan bo'lsa (lesson.ovozli_tekshiruv) — o'shalar;
 * 2) til darsi — chet tilidagi qisqa so'z/iboralar ([en]Green[/en]);
 * REV145: boshqa fanlarda — tekshiruv yo'q (bo'sh ro'yxat).
 */
export function voiceCheckItems(lesson, audience = 'oquvchi', opts = {}) {
  // REV121: til darsi bo'lmasa (matematika, atrof-muhit, mantiq) izoh tilidagi teglar «chet so'z» emas.
  const tilYoq = opts.tilYoq === true;
  const lim = VOICE_LIMITS[audience] || VOICE_LIMITS.oquvchi;
  const out = [];
  const given = Array.isArray(lesson?.ovozli_tekshiruv) ? lesson.ovozli_tekshiruv : [];
  for (const g of given) {
    const phrase = cleanLine(typeof g === 'string' ? g : g?.matn);
    if (phrase) add(out, { lang: (typeof g === 'object' && g?.til) || 'uz', phrase }, lim.count);
  }
  if (out.length) return out;

  const steps = Array.isArray(lesson?.steps) ? lesson.steps : [];
  for (const s of tilYoq ? [] : steps) {
    for (const m of String(s?.ovoz || '').matchAll(FOREIGN)) {
      const phrase = cleanLine(m[2]).replace(/[.!?。！？]+$/u, '');
      const n = words(phrase).length;
      if (!phrase || n > lim.maxWords || NOT_TARGET.test(phrase) || /[:：]$/.test(phrase)) continue;
      add(out, { lang: m[1].toLowerCase(), phrase }, lim.count);
    }
  }
  if (out.length) return out;

  // REV145: oddiy fanlarda (matematika, atrof-muhit, mantiq…) mikrofon bilan takrorlatilmaydi — faqat til darslarida.
  // Doska qatorlarini o'qitish ma'nosiz edi; dars berilgan ro'yxati (ovozli_tekshiruv) bo'lsa — yuqorida olingan.
  return out;
}

/** Ustoz aytadigan gap (TTS teglari bilan). */
export function voicePrompt(item, kid, attempt = 0, izoh = 'uz') {
  const p = item.lang === 'uz' ? item.phrase : `[${item.lang}]${item.phrase}[/${item.lang}]`;
  if (attempt > 0) return gap(izoh, kid ? 'Yana bir bor ayt: {p}' : 'Yana bir bor, aniqroq takrorlang: {p}', { p });
  return gap(izoh, kid ? 'Endi sen ayt: {p}' : 'Takrorlang: {p}', { p });
}

const APOS = /[‘’ʻʼ`'´]/g;
/** O'zbekchadagi o‘/g‘ tutuq belgilari tanib olishda turlicha keladi — solishtirishdan oldin olib tashlanadi. */
export function gradeVoice(alternatives, item) {
  const fix = (v) => String(v || '').replace(APOS, '');
  return gradeSpeech((alternatives || []).map(fix), fix(item?.phrase), item?.lang || 'uz');
}

/** Ibora o'tdi deb hisoblanadimi (2–3 yulduz). */
export function voicePassed(graded) { return Number(graded?.stars) >= 2; }

export function voiceSummary(results) {
  const list = Array.isArray(results) ? results : [];
  return { togri: list.filter((r) => r?.ok).length, jami: list.length };
}

/**
 * REV110: xato bo'lganda ustozning «murabbiy» gaplari. Bolaning o'z ovozi bo'lsa — avval uni eshittiradi:
 * «Sen shunday aytding» → (bolaning yozuvi) → «Men esa shunday aytaman: …» → «Yana bir bor ayt!».
 * Ovoz umuman eshitilmagan bo'lsa — yozuv qo'yilmaydi, faqat balandroq aytishga undaydi.
 */
export function voiceCoach(item, kid, { attempt = 1, heard = '', stars = 0, hasClip = false, izoh = 'uz' } = {}) {
  const p = item.lang === 'uz' ? item.phrase : `[${item.lang}]${item.phrase}[/${item.lang}]`;
  if (!heard && !hasClip) {
    return { before: '', after: gap(izoh, kid ? 'Ovozing eshitilmadi. Balandroq va dadil ayt: {p}' : 'Ovoz eshitilmadi. Balandroq ayting: {p}', { p }) };
  }
  const near = stars >= 1;
  const praise = gap(izoh, kid ? (near ? 'Juda yaqin!' : 'Yaxshi harakat!') : (near ? 'Yaqin.' : 'Yana urinib ko‘ring.'));
  const after = gap(izoh, kid ? 'Men esa shunday aytaman: {p} Yana bir bor ayt!' : 'To‘g‘risi: {p} Yana bir bor takrorlang.', { p });
  return {
    before: hasClip ? gap(izoh, kid ? '{praise} Sen shunday aytding:' : '{praise} Siz shunday aytdingiz:', { praise }) : '',
    after: hasClip ? after : `${praise} ${after}`,
    attempt,
  };
}

/** Oxirgi urinishdan keyin ham o'tmasa — baribir maqtab, keyingisiga o'tadi (bola xafa bo'lmasin). */
export function voiceGiveUp(item, kid, izoh = 'uz') {
  const p = item.lang === 'uz' ? item.phrase : `[${item.lang}]${item.phrase}[/${item.lang}]`;
  return gap(izoh, kid ? 'Sen zo‘r harakat qilding! Keyingi safar albatta chiqadi. Birga aytamiz: {p}' : 'To‘g‘risi: {p}', { p });
}
