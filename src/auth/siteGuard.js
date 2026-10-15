// REV147: ilova serverga ruxsat etilmagan manzildan ochilgan bo'lsa (masalan, boshqa manzildan o'rnatilgan ilova),
// brauzer kirish so'rovlarini to'xtatadi — «Server javob bermadi» chiqadi, oldin kirgan akkauntlar ham ko'rinmaydi
// (har manzilning xotirasi alohida). Server /auth/config da asosiy sayt manzilini aytadi — shu yerga o'tamiz.
const KEY = "kabutar:site-redirect:v1";

const norm = (u) => String(u || "").trim().replace(/\/+$/, "");

/** Asosiy sayt manzili (bu sahifa ruxsat etilgan manzillardan biri bo'lmasa), aks holda "". */
export function wrongSite(config, origin = globalThis.location?.origin) {
  const site = norm(config?.site);
  const here = norm(origin);
  if (!site || !here || !/^https?:\/\//.test(site)) return "";
  const allowed = new Set([site, ...(Array.isArray(config?.origins) ? config.origins.map(norm) : [])]);
  if (allowed.has(here)) return "";
  if (/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(here)) return "";   // ishlab chiqish
  return site;
}

/** Kerak bo'lsa asosiy saytga bir marta (10 daqiqada) o'tadi. Qaytaradi: o'tildimi. */
export function redirectIfWrongSite(config, { location = globalThis.location, storage = safeSession() } = {}) {
  const site = wrongSite(config, location?.origin);
  if (!site) return false;
  try {
    if (Date.now() - Number(storage?.getItem(KEY) || 0) < 10 * 60 * 1000) return false;
    storage?.setItem(KEY, String(Date.now()));
  } catch { /* xotira yopiq */ }
  location.assign(`${site}/${location.hash || ""}`);
  return true;
}

function safeSession() {
  try { return globalThis.sessionStorage; } catch { return null; }
}
