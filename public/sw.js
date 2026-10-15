const CACHE = "samtm-shell-v10-rev147";
const SHELL = ["/", "/manifest.webmanifest", "/icons/icon-192.png", "/icons/icon-512.png"];
const STATIC_PREFIXES = ["/assets/", "/icons/"];

function isStaticAsset(url) {
  return url.pathname === "/manifest.webmanifest"
    || STATIC_PREFIXES.some(prefix => url.pathname.startsWith(prefix));
}

function mayStore(response) {
  const cacheControl = response.headers.get("Cache-Control") || "";
  return response.ok
    && response.type === "basic"
    && !/no-store|private/i.test(cacheControl);
}

function matchesAssetType(url, response) {
  const contentType = String(response.headers.get("Content-Type") || "").toLowerCase();
  if (/\.(?:m?js)$/i.test(url.pathname)) {
    return contentType.includes("javascript") || contentType.includes("ecmascript");
  }
  if (/\.css$/i.test(url.pathname)) return contentType.includes("text/css");
  // Rasm, shrift, manifest va boshqa statik fayllarda HTML fallbackni
  // keshlamaslikning o'zi yetarli.
  return !contentType.includes("text/html");
}

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key.startsWith("samtm-") && key !== CACHE).map(key => caches.delete(key))
    ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  // Faqat ochiq ilova qobig'i va buildning statik fayllari keshlanadi.
  // Login, token, API, XLSX va boshqa shaxsiy javoblar bu yerga kirmaydi.
  if (url.origin !== self.location.origin) return;
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).then(async response => {
        const contentType = response.headers.get("Content-Type") || "";
        if (mayStore(response) && contentType.includes("text/html")) {
          await caches.open(CACHE).then(cache => cache.put("/", response.clone())).catch(() => {});
        }
        return response;
      }).catch(async () => {
        const cached = await caches.match("/");
        return cached || new Response("Ilova qobig‘ini yuklab bo‘lmadi. Internetni tekshirib qayta urinib ko‘ring.", {
          status: 503,
          headers: { "Content-Type": "text/plain; charset=utf-8" },
        });
      })
    );
    return;
  }
  if (!isStaticAsset(url) || request.headers.has("Authorization")) return;
  // REV130: build fayllari nomida xesh bor (o'zgarmaydi) — avval keshdan, tarmoqqa chiqmasdan (sekin internetda qotmaydi).
  if (url.pathname.startsWith("/assets/") && /-[A-Za-z0-9_-]{6,}\.[a-z0-9]+$/.test(url.pathname)) {
    event.respondWith(caches.match(request).then(hit => hit || fetch(request).then(async response => {
      if (mayStore(response) && matchesAssetType(url, response)) {
        await caches.open(CACHE).then(cache => cache.put(request, response.clone())).catch(() => {});
      }
      return response;
    })));
    return;
  }
  event.respondWith(
    fetch(request).then(async response => {
      if (!matchesAssetType(url, response)) {
        const cached = await caches.match(request);
        return cached || new Response("Statik fayl o‘rniga HTML javobi keldi; qayta yuklang.", {
          status: 502,
          headers: { "Content-Type": "text/plain; charset=utf-8" },
        });
      }
      if (mayStore(response)) {
        // Kesh kvotasi yoki eski WebView cache xatosi haqiqiy network
        // javobini yo'qotmasligi kerak.
        await caches.open(CACHE).then(cache => cache.put(request, response.clone())).catch(() => {});
      }
      return response;
    }).catch(async () => {
      const cached = await caches.match(request);
      return cached || new Response("Statik faylni yuklab bo‘lmadi.", {
        status: 503,
        headers: { "Content-Type": "text/plain; charset=utf-8" },
      });
    })
  );
});
