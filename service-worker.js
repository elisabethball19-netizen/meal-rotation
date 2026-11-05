/* Bump this version when changing the offline app shell. */
const SHELL_VERSION = 'v88';
const CACHE_PREFIX = `meal-rotation-shell:${self.registration.scope}:`;
const CACHE_NAME = CACHE_PREFIX + SHELL_VERSION;
const SHELL_FILES = [
  './', './index.html', './meal-rotation-test.html', './pwa.js',
  './manifest.webmanifest', './manifest-test.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png',
  './icons/test-icon-192.png', './icons/test-icon-512.png', './icons/test-apple-touch-icon.png',
  './icons/icon-16.png', './icons/icon-32.png', './icons/favicon.ico',
  './icons/test-icon-16.png', './icons/test-icon-32.png', './icons/test-favicon.ico'
];
const SHELL_URLS = new Set(SHELL_FILES.map(path => new URL(path, self.registration.scope).href));

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(SHELL_FILES.map(path => new Request(
      new URL(path, self.registration.scope), { cache: 'reload' }
    )));
  })());
  // Let an existing editing session finish before a new worker takes over.
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)
      .map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  // Only cache this app's static shell, never imports, backups, or other sites.
  const canonical = new URL(url.pathname, url.origin).href;
  if (!SHELL_URLS.has(canonical)) return;

  const network = fetch(event.request).then(async response => {
    if (!response.ok || response.type === 'opaque') throw new Error('App file unavailable');
    // Serve the current file even if storage is full or unavailable.
    try {
      const cache = await caches.open(CACHE_NAME);
      await cache.put(canonical, response.clone());
    } catch (_) {}
    return response;
  });
  // Attach background work while the fetch event is still being dispatched.
  event.waitUntil(network.then(() => {}, () => {}));
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    if (event.request.mode === 'navigate') {
      // A stalled connection should not keep an installed offline app on a blank screen.
      const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error('Offline fallback')), 4000));
      try { return await Promise.race([network, timeout]); }
      catch (_) {
        const saved = await cache.match(canonical);
        if (saved) {
          return saved;
        }
        return network;
      }
    }
    try { return await network; }
    catch (_) { return (await cache.match(canonical)) || Response.error(); }
  })());
});
