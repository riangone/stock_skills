// Service Worker for Stock Skills PWA
const CACHE_NAME = 'stock-skills-v2';

const STATIC_ASSETS = [
  '/',
  '/static/styles.css',
  '/static/utils.js',
  '/static/manifest.json',
  'https://cdn.jsdelivr.net/npm/daisyui@4.7.2/dist/full.min.css',
  'https://cdn.tailwindcss.com',
  'https://unpkg.com/htmx.org@1.9.10',
  'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js',
];

// Install: cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS).catch((err) => {
        console.warn('[SW] Failed to cache some assets:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Fetch: network-first for API/partials, cache-first for static
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API calls and HTMX partials: network only, no caching
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/partials/')) {
    return;
  }

  // Login/logout: network only
  if (url.pathname === '/login' || url.pathname === '/logout') {
    return;
  }

  // Static assets: cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        return cached || fetch(event.request).then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          return response;
        });
      })
    );
    return;
  }

  // HTML pages: network-first with offline fallback
  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Cache successful page responses
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => {
        // Offline fallback: serve cached version
        return caches.match(event.request).then((cached) => {
          if (cached) return cached;
          // Final fallback for navigation
          if (event.request.mode === 'navigate') {
            return caches.match('/');
          }
          return new Response('Offline', { status: 503 });
        });
      })
  );
});
