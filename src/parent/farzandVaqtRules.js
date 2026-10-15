// REV103: ota-ona paneli — farzandning bugungi vaqti va o'rganish ko'rsatkichlari (sof yordamchilar).

export function minutesText(min) {
  const total = Math.max(0, Math.round(Number(min) || 0));
  const h = Math.floor(total / 60), m = total % 60;
  if (!h) return `${m} daqiqa`;
  return m ? `${h} soat ${m} daqiqa` : `${h} soat`;
}

/** Dars / o'yin / jami: ishlatilgan vaqt limitga nisbatan. */
export function usageRows(vaqt) {
  if (!vaqt || !vaqt.jami) return [];
  return [["dars", "📚", "Dars"], ["oyin", "🎮", "Erkin o‘yin"], ["jami", "⏱", "Jami"]].map(([key, emoji, label]) => {
    const row = vaqt[key] || {};
    const limit = Number(row.limit) || 0;
    const used = Number(row.daqiqa) || 0;
    return { key, emoji, label, daqiqa: used, limit, qoldi: Math.max(0, limit - used),
      pct: limit ? Math.min(100, Math.round((used / limit) * 100)) : 0, full: Boolean(limit) && used >= limit };
  });
}

/** Hozir platformadami: «🟢 Hozir platformada — Shaxmat» / «⚪ 12 daqiqadan beri platformada emas». */
export function presence(hozir, tugadi = false) {
  if (tugadi) return { cls: "is-done", emoji: "🌙", text: "Bugungi vaqt tugadi — platforma ertagacha yopiq" };
  if (!hozir) return { cls: "is-none", emoji: "⚪", text: "Bugun hali platformaga kirmagan" };
  if (hozir.platformada) return { cls: "is-live", emoji: "🟢", text: `Hozir platformada${hozir.nom ? ` — «${hozir.nom}»` : ""}` };
  const ago = Number(hozir.daqiqa) || 0;
  return { cls: ago >= 5 ? "is-away" : "is-pause", emoji: ago >= 5 ? "🔴" : "🟠",
    text: `${ago ? `${minutesText(ago)}dan beri` : "Hozirgina"} platformada emas${hozir.nom ? ` (oxirgi: «${hozir.nom}»)` : ""}` };
}

/** Oxirgi 7 kun: har kun dars + o'yin ustuni (balandlik px). */
export function weekStack(days, maxPx = 56) {
  const list = (days || []).slice(-7);
  const top = Math.max(30, ...list.map((d) => (Number(d.dars) || 0) + (Number(d.oyin) || 0)));
  return list.map((d) => {
    const dars = Number(d.dars) || 0, oyin = Number(d.oyin) || 0;
    return { ...d, dars, oyin, jami: dars + oyin, darsPx: Math.round((dars / top) * maxPx), oyinPx: Math.round((oyin / top) * maxPx) };
  });
}

export function levelDots(n) {
  const v = Math.max(1, Math.min(5, Math.round(Number(n) || 1)));
  return "●".repeat(v) + "○".repeat(5 - v);
}

/** «4–5 yosh guruhida 2-o‘rin (37 bola ichida)». */
export function ratingText(reyting, guruh = "") {
  if (!reyting || !reyting.jami) return "";
  const where = guruh ? `${guruh} guruhida` : "Tengdoshlari ichida";
  return `${where} ${reyting.orin}-o‘rin (${reyting.jami} bola ichida) · ⭐ ${reyting.yulduz} yulduz (7 kun)`;
}

// ── REV145: ota-ona uchun aniq, mantiqiy hisobot (ichma-ich ochiladi) ──

/** Dars bahosi — oddiy so'z bilan. */
export function bahoInfo(r) {
  if (!r?.tugadi) return { cls: "is-half", matn: "Tugallanmagan" };
  if (!r.jami) return { cls: "is-plain", matn: "Tugatdi" };
  const baho = r.baho || (r.togri / r.jami >= 0.8 ? "alo" : r.togri / r.jami >= 0.5 ? "yaxshi" : "mashq");
  return { alo: { cls: "is-top", matn: "A’lo" }, yaxshi: { cls: "is-good", matn: "Yaxshi" }, mashq: { cls: "is-low", matn: "Mashq kerak" } }[baho]
    || { cls: "is-plain", matn: "Tugatdi" };
}

/** Kun xulosasi — yuqoridagi 4 ta katta raqam uchun. */
export function kunXulosa(darslar = [], vaqt = null) {
  const list = Array.isArray(darslar) ? darslar : [];
  const tugadi = list.filter((r) => r.tugadi);
  const togri = tugadi.reduce((n, r) => n + (Number(r.togri) || 0), 0);
  const jami = tugadi.reduce((n, r) => n + (Number(r.jami) || 0), 0);
  const sozlar = new Map();
  for (const r of list) for (const w of r.sozlar || []) {
    const k = String(w.soz || "").toLowerCase();
    if (k) sozlar.set(k, Boolean(sozlar.get(k)) || w.aytdi === true);
  }
  const darsDaqiqa = list.reduce((n, r) => n + (Number(r.daqiqa) || 0), 0);
  return {
    darslar: list.length, tugadi: tugadi.length, togri, jami, foiz: jami ? Math.round((togri / jami) * 100) : null,
    sozJami: sozlar.size, sozAytdi: [...sozlar.values()].filter(Boolean).length,
    daqiqa: vaqt?.jami ? Number(vaqt.jami.daqiqa) || 0 : darsDaqiqa,
    limit: vaqt?.jami ? Number(vaqt.jami.limit) || 0 : 0,
  };
}

/** Darsdan keyin ota-onaga bitta aniq maslahat (uyda nima qilish kerak): { matn, sozlar } yoki null. */
export function maslahat(r) {
  if (!r) return null;
  if (!r.tugadi) return { matn: "Dars yarim qoldi — farzandingiz bilan oxirigacha birga ko‘ring.", sozlar: [] };
  const aytmagan = (r.sozlar || []).filter((w) => w.aytdi === false).map((w) => w.soz);
  if (aytmagan.length) return { matn: "Uyda shu so‘zlarni birga ayting:", sozlar: aytmagan };
  if (r.jami && r.togri / r.jami < 0.5) return { matn: "Bu darsni ertaga yana bir bor takrorlash foydali.", sozlar: [] };
  if ((Number(r.chalgish) || 0) >= 3) return { matn: "Dars paytida tez-tez chalg‘idi — tinch joyda, telefon bildirishnomalarisiz o‘tkazing.", sozlar: [] };
  return null;
}
