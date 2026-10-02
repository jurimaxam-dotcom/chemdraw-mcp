// Service Worker: Nach dem ersten Besuch läuft der Rechner ohne Netz — im Labor
// gibt es oft kein WLAN. Strategie: Cache zuerst, sonst Netz und nachlegen.
// VERSION wird von scripts/build-web.sh durch den Git-Stand ersetzt; ein neuer
// Build verwirft damit den alten Cache.
const VERSION = "@@BUILD@@";
const CACHE = `praktikumsrechner-${VERSION}`;
// Jede Datei genau einmal: cache.addAll lehnt doppelte Anfragen ab, und dann wird
// der Worker nie aktiv (E2E hing daran, 02.10.2026).
const KERN = ["./", "@@DATEIEN@@"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(KERN.flat())).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((namen) => Promise.all(namen.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== self.location.origin) return;
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then((treffer) => treffer || fetch(e.request).then((antwort) => {
      if (antwort.ok) { const kopie = antwort.clone(); caches.open(CACHE).then((c) => c.put(e.request, kopie)); }
      return antwort;
    })),
  );
});
