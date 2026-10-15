// REV141: «Harakat o'yinlari» — sof qoidalar (brauzersiz sinaladi): bosqichli yo'l, raundlar, takrorlash,
// barmoq harakatini (imo-ishora) tanish va natijalarni saqlash.
import { HARAKATLAR, BOLIMLAR, BOLIM_XONA, IZOH_H } from "./harakatLugat.js";
import { izohTeg } from "../izohTil.js";

export const IZOH_TILLARI = ["uz", "ru", "en"];
const izohOl = (izoh) => (IZOH_TILLARI.includes(izoh) ? izoh : "uz");
export const harakat = (id) => HARAKATLAR.find((h) => h.id === id) || null;
export const bolimHarakatlari = (bolim) => HARAKATLAR.filter((h) => h.bolim === bolim);

/** Ovoz uchun teg: o'zbekcha tegsiz, boshqa til — [xx]…[/xx]. */
export const teg = (text, til) => (!text ? "" : til === "uz" ? text : `[${til}]${text}[/${til}]`);

/** Buyruq o'rganiladigan tilda: kichiklarga qisqa («Open!»), kattaroqlarga to'liq («Open the door!»). */
export function buyruq(id, til, toliq = false) {
  const h = harakat(id);
  if (!h) return "";
  return (toliq ? h.g[til] || h.g.en : h.s[til] || h.s.en) || "";
}
/** Buyruqning izoh tilidagi ma'nosi (to'liq shakli — bola nimani qilishini tushunadi). */
export function manosi(id, izoh, toliq = true) {
  const h = harakat(id);
  if (!h) return "";
  const l = izohOl(izoh);
  return (toliq ? h.g[l] : h.s[l]) || "";
}

/** Ustozning izoh tilidagi gapi (ovozga tayyor, teglangan). {t} — o'rganiladigan tildagi matn, {i} — izohdagi. */
export function izohGap(key, izoh, { t = "", til = "en", i = "" } = {}) {
  const l = izohOl(izoh);
  const tpl = (IZOH_H[key] || {})[l] || "";
  const qism = (s) => (s ? izohTeg(s, l) : "");
  const parts = tpl.replace("{i}", i).split("{t}");
  return parts.length > 1 ? `${qism(parts[0])}${teg(t, til)}${qism(parts[1])}` : qism(parts[0]);
}
/** Ekranda ko'rsatish uchun (tegsiz). */
export function izohMatn(key, izoh, { t = "", i = "" } = {}) {
  return ((IZOH_H[key] || {})[izohOl(izoh)] || "").replace("{i}", i).replace("{t}", t);
}
/** Imo-ishora maslahati kaliti: «sur_up», «ushla», … */
export const imoKalit = (imo) => imo.kalit || (imo.tur === "sur" ? `sur_${imo.yon}` : imo.tur);

/** Yosh guruhi: «2-3 yosh» → kichik, «4-5» → orta, «6-7» va maktab → katta. */
export function yoshGuruhi(grade = "") {
  const m = /(\d+)/.exec(String(grade || ""));
  const n = m ? Number(m[1]) : 4;
  if (/sinf|class|grade/i.test(String(grade)) || n >= 6) return "katta";
  return n <= 3 ? "kichik" : "orta";
}
export const raundSoni = (yosh) => (yosh === "kichik" ? 6 : yosh === "orta" ? 8 : 10);
export const kartaSoni = (yosh) => (yosh === "kichik" ? 2 : yosh === "orta" ? 3 : 4);

// ───────────────────────────── yo'l (bosqichlar) ─────────────────────────────

/**
 * Yo'l tugunlari tartib bilan: har bo'lim — «o'rgan» → «o'yna» → «xona» (narsalar nomi); 2- va 4-bo'limdan keyin
 * aralash «takror»; oxirida umumiy takror, qolgan xonalar va hech qachon tugamaydigan «cheksiz o'yin».
 */
export function yolTugunlari() {
  const out = [];
  BOLIMLAR.forEach((b, i) => {
    out.push({ id: `organ:${b.id}`, tur: "organ", bolim: b.id });
    out.push({ id: `oyna:${b.id}`, tur: "oyna", bolim: b.id });
    if (BOLIM_XONA[b.id]) out.push({ id: `xona:${BOLIM_XONA[b.id]}`, tur: "xona", xona: BOLIM_XONA[b.id], bolim: b.id });
    if (i === 1 || i === 3 || i === BOLIMLAR.length - 1) out.push({ id: `takror:${i + 1}`, tur: "takror", gacha: i + 1 });
  });
  out.push({ id: "xona:sinf", tur: "xona", xona: "sinf" });
  out.push({ id: "xona:havo", tur: "xona", xona: "havo" });
  out.push({ id: "cheksiz", tur: "cheksiz" });
  return out;
}

/** Tugun bajarilganmi. p — shu tilning natijasi; xonaYulduz(id) — eski xonadagi yulduzlar. */
export function bajarildi(tugun, p = {}, xonaYulduz = () => 0) {
  if (tugun.tur === "organ") return bolimHarakatlari(tugun.bolim).every((h) => (p.organ || {})[h.id]);
  if (tugun.tur === "oyna" || tugun.tur === "takror") return ((p.yulduz || {})[tugun.id] || 0) >= 1;
  if (tugun.tur === "xona") return xonaYulduz(tugun.xona) >= 3;
  if (tugun.tur === "cheksiz") return (p.cheksiz || 0) > 0;
  return false;
}

/** Kuniga nechta yangi bosqich (dars) ochiladi: kichiklarga 2 ta, kattaroqlarga 3 ta. */
export const kunlikLimit = (yosh = "orta") => (yosh === "kichik" ? 2 : 3);

/** Bugun bajarilgan yangi bosqichlar soni. Belgisi hali qo'yilmagan (hozirgina bajarilgan) tugun ham bugungi hisoblanadi. */
export function bugunBajarilgan(p = {}, xonaYulduz = () => 0, bugun = kunRaqami()) {
  if (!p.kun) return 0;   // eski natija: kun belgilari hali yo'q — hammasi oldingi kunlarniki
  let yoldan = true, n = 0;
  for (const tg of yolTugunlari()) {
    const b = bajarildi(tg, p, xonaYulduz);
    if (b && (p.kun[tg.id] === bugun || (p.kun[tg.id] === undefined && yoldan))) n++;
    if (!b) yoldan = false;
  }
  return n;
}

/**
 * Har tugun holati: «tugadi» | «ochiq» (navbatdagi) | «ertaga» (bugungi limit tugadi) | «qulf».
 * Bajarilgan tugunlar har doim qayta o'ynaladi. opts: {limit, bugun, cheklovsiz} — cheklovsiz (admin): kunlik limit yo'q va
 * hamma tugun ochiq.
 */
export function yolHolati(p = {}, xonaYulduz = () => 0, { limit = Infinity, bugun = kunRaqami(), cheklovsiz = false } = {}) {
  const t = yolTugunlari();
  const tolgan = !cheklovsiz && bugunBajarilgan(p, xonaYulduz, bugun) >= limit;
  let ochiqTopildi = false;
  return t.map((tg) => {
    if (bajarildi(tg, p, xonaYulduz)) return { ...tg, holat: "tugadi" };
    if (!ochiqTopildi) { ochiqTopildi = true; return { ...tg, holat: tolgan ? "ertaga" : "ochiq" }; }
    return { ...tg, holat: cheklovsiz ? "ochiq" : "qulf" };
  });
}

/**
 * Bajarilgan tugunlarga bajarilgan kunini yozadi (kunlik limit shundan hisoblanadi). Kun belgilari umuman yo'q bo'lsa (eski
 * natija) — oldin bajarilganlar 0-kun deb belgilanadi, bugungi limitni yemaydi. O'zgarish bo'lmasa — null.
 */
export function kunBelgila(til, xonaYulduz = () => 0, st = store(), bugun = kunRaqami()) {
  const p = tilNatija(til, st);
  const eski = !p.kun;
  const kun = { ...(p.kun || {}) };
  let ozgardi = eski;
  let yoldan = true;   // shu tugungacha hammasi bajarilgan — demak bola unga yo'l bo'ylab keldi
  for (const tg of yolTugunlari()) {
    const b = bajarildi(tg, p, xonaYulduz);
    // yo'ldan tashqarida (ro'yxatdan) oldinroq o'ynalgan xona bugungi limitni yemaydi
    if (kun[tg.id] === undefined && b) { kun[tg.id] = eski || !yoldan ? 0 : bugun; ozgardi = true; }
    if (!b) yoldan = false;
  }
  return ozgardi ? saqla(til, (c) => ({ ...c, kun }), st) : null;
}

/** Takror tugunidagi harakatlar: shu tugungacha bo'lgan bo'limlar. */
export function takrorHarakatlari(gacha) {
  const b = new Set(BOLIMLAR.slice(0, gacha).map((x) => x.id));
  return HARAKATLAR.filter((h) => b.has(h.bolim)).map((h) => h.id);
}
/** O'rganilgan harakatlar (o'rgan bosqichida bajarilganlar). */
export const organilgan = (p = {}) => HARAKATLAR.filter((h) => (p.organ || {})[h.id]).map((h) => h.id);

// ───────────────────────────── raundlar ─────────────────────────────

export function aralashtir(list, rng = Math.random) {
  const a = [...list];
  for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}

/**
 * O'yin raundlari. Har raund: { id (bajariladigan harakat), kartalar: [id, …] (tanlash uchun rasmlar) }.
 * Har harakat kamida bir marta chiqadi; ketma-ket bir xil harakat bo'lmaydi; zaif (kuchi past, vaqti kelgan)
 * harakatlar ko'proq chiqadi. pool — o'ynaladigan harakatlar, hamma — chalg'ituvchi kartalar uchun.
 */
export function raundlar(pool, { yosh = "orta", rng = Math.random, kuch = {}, bugun = kunRaqami(), n = null, hamma = null } = {}) {
  const ids = pool.filter((id) => harakat(id));
  if (!ids.length) return [];
  const soni = n || raundSoni(yosh);
  const vazn = (id) => { const k = kuch[id]; if (!k) return 3; return (k.due || 0) <= bugun ? 3 : Math.max(1, 3 - (k.k || 0) / 2); };
  const tartib = [...aralashtir(ids, rng)];
  while (tartib.length < soni) {
    const jami = ids.reduce((a, id) => a + vazn(id), 0);
    let r = rng() * jami;
    let pick = ids[0];
    for (const id of ids) { r -= vazn(id); if (r <= 0) { pick = id; break; } }
    tartib.push(pick);
  }
  const ketma = tartib.slice(0, soni);
  for (let i = 1; i < ketma.length; i++) {
    if (ketma[i] === ketma[i - 1]) {
      const j = ketma.findIndex((x, k) => k > i && x !== ketma[i] && x !== ketma[i - 1] && x !== ketma[k + 1]);
      if (j > i) [ketma[i], ketma[j]] = [ketma[j], ketma[i]];
    }
  }
  const kk = Math.max(1, kartaSoni(yosh));
  const tanlov = (hamma || ids).filter((id) => harakat(id));
  return ketma.map((id) => {
    const boshqa = aralashtir(tanlov.filter((x) => x !== id && !juftmi(x, id)), rng).slice(0, kk - 1);
    return { id, kartalar: aralashtir([id, ...boshqa], rng) };
  });
}
// Bir xil sahnadagi qarama-qarshi juftlar (och/yop, yoq/o'chir, shishir/yor) bitta raundda chiqmaydi —
// sahna rasmi o'xshash, bola adashmasin (ular alohida raundlarda o'rganiladi).
const JUFT = [["open", "close"], ["lighton", "lightoff"], ["blow", "pop"], ["drive", "stop"]];
export const juftmi = (a, b) => JUFT.some(([x, y]) => (x === a && y === b) || (x === b && y === a));

/** Cheksiz o'yinda vaqt (soniya): har 3 to'g'ri javobda qisqaradi, lekin 4 soniyadan kam emas. */
export function cheksizVaqt(togri, yosh = "orta") {
  const bosh = yosh === "kichik" ? 14 : yosh === "orta" ? 11 : 9;
  return Math.max(4, bosh - Math.floor(togri / 3));
}

/** Yulduzlar: 90% va undan yuqori — 3, 70% — 2, 50% — 1. */
export function yulduzHisob(togri, jami) {
  if (!jami) return 0;
  const f = togri / jami;
  return f >= 0.9 ? 3 : f >= 0.7 ? 2 : f >= 0.5 ? 1 : 0;
}

// ───────────────────────────── takrorlash (SRS) ─────────────────────────────

export function kunRaqami(d = new Date()) {
  return Math.floor((d.getTime() - d.getTimezoneOffset() * 60000) / 86400000);
}
const ORALIQ = [1, 2, 4, 7, 14, 30];
/** Harakat kuchini yangilash: to'g'ri — keyingi takror uzoqroqda, xato — ertaga yana. */
export function kuchYangila(k = { k: 0, due: 0 }, ok, bugun = kunRaqami()) {
  const kk = ok ? Math.min(ORALIQ.length - 1, (k.k || 0) + 1) : Math.max(0, (k.k || 0) - 2);
  return { k: kk, due: bugun + (ok ? ORALIQ[kk] : 1) };
}
/** Bugun takrorlanishi kerak bo'lgan (vaqti kelgan) o'rganilgan harakatlar. */
export function bugungiTakror(p = {}, bugun = kunRaqami()) {
  return organilgan(p).filter((id) => ((p.kuch || {})[id]?.due || 0) <= bugun);
}

// ───────────────────────────── saqlash ─────────────────────────────

const KEY = "kabutar:harakat:v1";
const store = () => { try { return globalThis.localStorage; } catch { return null; } };
export function natija(st = store()) {
  try { return JSON.parse(st?.getItem(KEY) || "{}") || {}; } catch { return {}; }
}
export function tilNatija(til, st = store()) {
  const n = natija(st)[til] || {};
  return { organ: {}, yulduz: {}, kuch: {}, cheksiz: 0, ...n };
}
export function saqla(til, ozgar, st = store()) {
  const all = natija(st);
  const cur = { organ: {}, yulduz: {}, kuch: {}, cheksiz: 0, ...(all[til] || {}) };
  const next = ozgar(cur) || cur;
  all[til] = next;
  try { st?.setItem(KEY, JSON.stringify(all)); } catch { /* joy yo'q */ }
  return next;
}
/** Natijalarni yozish yordamchilari (eng yaxshi natija saqlanadi). */
export const organdi = (til, id, st) => saqla(til, (c) => ({ ...c, organ: { ...c.organ, [id]: 1 }, kuch: { ...c.kuch, [id]: c.kuch[id] || kuchYangila(undefined, true) } }), st);
export const yulduzYoz = (til, tugunId, y, st) => saqla(til, (c) => ({ ...c, yulduz: { ...c.yulduz, [tugunId]: Math.max(c.yulduz[tugunId] || 0, y) } }), st);
export const kuchYoz = (til, id, ok, st, bugun = kunRaqami()) => saqla(til, (c) => ({ ...c, kuch: { ...c.kuch, [id]: kuchYangila(c.kuch[id], ok, bugun) } }), st);
export const cheksizYoz = (til, ball, st) => saqla(til, (c) => ({ ...c, cheksiz: Math.max(c.cheksiz || 0, ball) }), st);

// ───────────────────────────── sahna ko'rinishi (telefon ekraniga moslash) ─────────────────────────────

/**
 * REV144: sahna 400×300 da chiziladi, lekin quti istalgan nisbatda bo'lishi mumkin (telefonda — kvadratga yaqin, katta).
 * SVG «slice» bilan to'ldiradi — chetlar qirqiladi. Qaytaradi: ko'rinadigan qism {x0, y0, vw, vh} (sahna birligida).
 */
export function sahnaKorinish(w, h) {
  const ar = w > 0 && h > 0 ? w / h : 4 / 3;
  if (ar < 4 / 3) { const vw = 300 * ar; return { x0: (400 - vw) / 2, y0: 0, vw, vh: 300 }; }
  const vh = 400 / ar;
  return { x0: 0, y0: (300 - vh) / 2, vw: 400, vh };
}
/** Sahna ulushi (0..1, 400×300 ga nisbatan) → quti ulushi. r — kenglik ulushida. */
export function qutiga(f, k) {
  if (!f) return f;
  const o = { x: (f.x * 400 - k.x0) / k.vw, y: (f.y * 300 - k.y0) / k.vh };
  if (f.r != null) o.r = (f.r * 400) / k.vw;
  return o;
}
/** Quti ulushi → sahna ulushi (barmoq qayerda ekanini sahnada chizish uchun). */
export function sahnaga(b, k) {
  return b ? { x: (k.x0 + b.x * k.vw) / 400, y: (k.y0 + b.y * k.vh) / 300 } : b;
}

// ───────────────────────────── imo-ishorani tanish ─────────────────────────────

/**
 * Barmoq harakatini taniydi. olcham — sahna o'lchami {w, h} (px). Har voqea { p (0..1), tayyor } qaytaradi.
 * opts: markaz (aylantirish uchun, ulushda), boshi/nishon (olib borish uchun, ulushda {x, y, r}).
 */
export function imoTanish(imo, olcham, opts = {}) {
  const w = Math.max(1, olcham.w), h = Math.max(1, olcham.h);
  const min = Math.min(w, h);
  const s = { p: 0, tayyor: false, down: null, last: null, taps: [], burchak: 0, oldingi: null, yon: 0, burilish: 0, chekka: null, ushlash: null };
  const natijaQ = () => ({ p: Math.max(0, Math.min(1, s.p)), tayyor: s.tayyor, x: s.last?.x, y: s.last?.y });
  const bitir = () => { s.p = 1; s.tayyor = true; };
  const mx = (opts.markaz?.x ?? 0.5) * w, my = (opts.markaz?.y ?? 0.5) * h;
  return {
    get p() { return s.p; },
    get tayyor() { return s.tayyor; },
    down(x, y, t) {
      if (s.tayyor) return natijaQ();
      s.down = { x, y, t }; s.last = { x, y, t };
      if (imo.tur === "aylantir") s.oldingi = Math.atan2(y - my, x - mx);
      if (imo.tur === "ishqala") { s.chekka = x; s.yon = 0; }
      if (imo.tur === "ushla") s.ushlash = t;
      if (imo.tur === "olib") {
        const b = opts.boshi || { x: 0.25, y: 0.6, r: 0.22 };
        s.ushlash = Math.hypot(x / w - b.x, (y / h - b.y) * (h / w)) <= b.r ? { dx: x / w - b.x, dy: y / h - b.y } : null;
      }
      return natijaQ();
    },
    move(x, y, t) {
      if (s.tayyor || !s.down) return natijaQ();
      s.last = { x, y, t };
      const dx = x - s.down.x, dy = y - s.down.y;
      if (imo.tur === "sur") {
        const kerak = min * 0.28;
        const d = imo.yon === "up" ? -dy : imo.yon === "down" ? dy : Math.abs(dx);
        s.p = Math.max(s.p, d / kerak);
        if (s.p >= 1) bitir();
      } else if (imo.tur === "aylantir") {
        const a = Math.atan2(y - my, x - mx);
        let d = a - s.oldingi;
        if (d > Math.PI) d -= 2 * Math.PI;
        if (d < -Math.PI) d += 2 * Math.PI;
        if (Math.hypot(x - mx, y - my) > min * 0.06) s.burchak += d;   // markazga juda yaqin — hisoblanmaydi
        s.oldingi = a;
        s.p = Math.abs(s.burchak * 180 / Math.PI) / (imo.deg || 180);
        if (s.p >= 1) bitir();
      } else if (imo.tur === "ishqala") {
        const amp = w * 0.07;
        const dir = Math.sign(x - s.chekka);
        if (Math.abs(x - s.chekka) >= amp) {
          if (s.yon && dir !== s.yon) { s.burilish += 1; s.p = s.burilish / (imo.n || 5); if (s.p >= 1) bitir(); }
          s.yon = dir; s.chekka = x;
        } else if ((dir > 0 && x > s.chekka && s.yon > 0) || (dir < 0 && x < s.chekka && s.yon < 0)) s.chekka = x;
      } else if (imo.tur === "olib" && s.ushlash) {
        const n = opts.nishon || { x: 0.72, y: 0.42, r: 0.14 };
        const b = opts.boshi || { x: 0.25, y: 0.6 };
        const ox = x / w - s.ushlash.dx, oy = y / h - s.ushlash.dy;
        const jami = Math.hypot(n.x - b.x, n.y - b.y);
        const qoldi = Math.hypot(n.x - ox, n.y - oy);
        s.p = Math.max(0, 1 - qoldi / jami);
        s.joy = { x: ox, y: oy };
        if (qoldi <= n.r) bitir();
      }
      return natijaQ();
    },
    up(x, y, t) {
      if (s.tayyor || !s.down) { s.down = null; return natijaQ(); }
      const kichikHarakat = Math.hypot(x - s.down.x, y - s.down.y) < min * 0.08 && t - s.down.t < 700;
      if (imo.tur === "bos" && kichikHarakat) bitir();
      else if (imo.tur === "ikki" && kichikHarakat) {
        s.taps = [...s.taps.filter((tt) => t - tt < 650), t];
        s.p = s.taps.length / 2;
        if (s.taps.length >= 2) bitir();
      } else if (imo.tur === "tez" && kichikHarakat) {
        // zanjir: har bosish oldingisidan 900 ms ichida bo'lsa — davom etadi (to'xtab qolsa, boshidan)
        const oxirgi = s.taps[s.taps.length - 1];
        s.taps = oxirgi != null && t - oxirgi < 900 ? [...s.taps, t] : [t];
        s.p = Math.max(s.p, s.taps.length / (imo.n || 7));
        if (s.taps.length >= (imo.n || 7)) bitir();
      } else if (imo.tur === "ushla") {
        s.ushlash = null;
      } else if (imo.tur === "olib") {
        s.ushlash = null;
        if (!s.tayyor) { s.p = 0; s.joy = null; }
      }
      s.down = null;
      return natijaQ();
    },
    /** Vaqt o'tishi (ushlab turish va «tez-tez» susayishi uchun). */
    tick(t) {
      if (s.tayyor) return natijaQ();
      if (imo.tur === "ushla") {
        const dt = Math.max(0, Math.min(200, t - (s.tt ?? t)));
        s.tt = t;
        if (s.down && s.ushlash != null) s.p += dt / (imo.ms || 1500);
        else s.p = Math.max(0, s.p - dt / ((imo.ms || 1500) * 2));
        if (s.p >= 1) bitir();
      } else if (imo.tur === "tez" && s.taps.length && t - s.taps[s.taps.length - 1] > 900) {
        s.taps = []; s.p = Math.max(0, s.p - 0.02);
      }
      return natijaQ();
    },
    /** Olib borilayotgan narsaning joyi (ulushda) — sahnada chizish uchun. */
    get joy() { return s.joy || null; },
  };
}
