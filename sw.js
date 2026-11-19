importScripts("https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.sw.js");
const CACHE = "azimuth-v18";
self.addEventListener("install", e => { self.skipWaiting(); });
self.addEventListener("activate", e => { e.waitUntil(self.clients.claim()); });
// Network first: always try the latest edition, fall back to the last copy when offline.
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(
    fetch(e.request).then(r => {
      if (r.ok && new URL(e.request.url).origin === location.origin) {
        const copy = r.clone();
        caches.open(CACHE).then(c => c.put(e.request.url.split("?")[0], copy));
      }
      return r;
    }).catch(() => caches.match(e.request.url.split("?")[0]))
  );
});
