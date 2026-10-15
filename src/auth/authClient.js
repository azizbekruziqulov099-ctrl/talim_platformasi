export const AUTH_REQUEST_TIMEOUT = 12000;

export function authEndpoint(apiBase, path) {
  return `${String(apiBase || "").replace(/\/+$/, "")}${path}`;
}

export async function authRequest(apiBase, path, { body, signal, timeout = AUTH_REQUEST_TIMEOUT } = {}) {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  if (signal?.aborted) abort();
  else signal?.addEventListener("abort", abort, { once: true });
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeout);
  try {
    const response = await fetch(authEndpoint(apiBase, path), {
      method: body === undefined ? "GET" : "POST",
      headers: { Accept: "application/json", ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      cache: "no-store",
      credentials: "omit",
      signal: controller.signal,
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = typeof data?.detail === "string" ? data.detail : typeof data?.error === "string" ? data.error : "";
      // REV146: 502/503/504 — server qayta ishga tushmoqda (Railway). Tarmoq xatosi kabi: kirish o'zi qayta urinadi.
      if ([502, 503, 504].includes(response.status) && !detail) {
        throw Object.assign(new Error("Server hozir javob bermadi (yangilanish yoki qayta ishga tushish bo‘lishi mumkin). 10–20 soniyadan keyin qayta bosing."), { network: true, status: response.status });
      }
      const error = new Error(detail || (response.status === 429
        ? "Urinishlar ko‘payib ketdi. Biroz kutib, qayta urinib ko‘ring."
        : response.status === 404 ? "Kirish xizmati hali yangilanmagan. Boshqa kirish usulini tanlang."
          : "Kirish amalga oshmadi. Qayta urinib ko‘ring."));
      error.status = response.status;
      throw error;
    }
    if (!data || typeof data !== "object") throw new Error("Serverdan kutilmagan javob keldi. Qayta urinib ko‘ring.");
    return data;
  } catch (error) {
    if (timedOut) throw new Error("Server javobi kechikdi. Internetni tekshirib, qayta urinib ko‘ring.");
    if (error?.name === "AbortError" || signal?.aborted) throw error;
    if (error instanceof TypeError) {
      // REV107: internet bor-yo'qligini ajratamiz — ko'pincha internet emas, server qayta ishga tushayotgan bo'ladi.
      const offline = typeof navigator !== "undefined" && navigator.onLine === false;
      throw Object.assign(new Error(offline
        ? "Internet aloqasi yo‘q. Internetni yoqib, qayta urinib ko‘ring."
        : "Server hozir javob bermadi (yangilanish yoki qayta ishga tushish bo‘lishi mumkin). 10–20 soniyadan keyin qayta bosing."), { network: true });
    }
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", abort);
  }
}

export function telegramChallenge(data, now = Date.now()) {
  let url;
  try { url = new URL(data?.bot_url); } catch { return null; }
  if (url.protocol !== "https:" || !["t.me", "telegram.me"].includes(url.hostname) || url.username || url.password) return null;
  if (typeof data?.challenge !== "string" || !data.challenge || typeof data?.browser_secret !== "string" || data.browser_secret.length < 16) return null;
  const duration = Number(data.expires_in);
  if (!Number.isFinite(duration) || duration <= 0 || duration > 600) return null;
  return {
    challenge: data.challenge,
    browser_secret: data.browser_secret,
    bot_url: url.toString(),
    delivery: data.delivery === "code" ? "code" : "approval",
    verification_code: /^\d{6}$/.test(String(data.verification_code || "")) ? String(data.verification_code) : "",
    expires_at: now + duration * 1000,
  };
}

export function challengeStorageKey(apiBase) {
  return `kabutar:telegram:pending:v1:${String(apiBase || "").replace(/\/+$/, "")}`;
}

export function restoreTelegramChallenge(storage, key, now = Date.now()) {
  try {
    const saved = JSON.parse(storage.getItem(key) || "null");
    if (!saved || !Number.isFinite(saved.expires_at)) return null;
    return telegramChallenge({ ...saved, expires_in: (saved.expires_at - now) / 1000 }, now);
  } catch { return null; }
}

export function formatAuthCountdown(seconds) {
  const value = Math.max(0, Math.floor(Number(seconds) || 0));
  return `${String(Math.floor(value / 60)).padStart(2, "0")}:${String(value % 60).padStart(2, "0")}`;
}
