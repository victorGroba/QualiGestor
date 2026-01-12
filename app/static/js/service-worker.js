const CACHE_NAME = 'qualigestor-offline-v1';
const resourcesToCache = [
    '/cli/listar-aplicacoes', // ajuste para sua rota principal
    '/static/css/dashboard.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://unpkg.com/dexie@latest/dist/dexie.js'
];

self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(resourcesToCache)));
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => response || fetch(event.request))
    );
});