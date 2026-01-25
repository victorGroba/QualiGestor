const CACHE_NAME = 'qualigestor-dynamic-v5'; // Subi a versão

// 1. Arquivos CRÍTICOS (Se falhar, o app não funciona offline)
const CRITICAL_ASSETS = [
    '/static/css/dashboard.css',
    '/static/img/logo.jpg',
    // Não inclua rotas dinâmicas (ex: /cli/...) aqui na instalação!
    // Deixe elas serem cacheadas na hora que o usuário navega (Runtime Caching).
];

// 2. Arquivos OPCIONAIS (Se falhar, o app continua funcionando)
const OPTIONAL_ASSETS = [
    '/static/js/sidebar.js',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://unpkg.com/dexie@latest/dist/dexie.js'
];

self.addEventListener('install', event => {
    self.skipWaiting();
    
    event.waitUntil(
        caches.open(CACHE_NAME).then(async cache => {
            // Instala os críticos (Obrigatório)
            await cache.addAll(CRITICAL_ASSETS);
            
            // Tenta instalar os opcionais um por um (Não quebra se falhar)
            for (let url of OPTIONAL_ASSETS) {
                try {
                    await cache.add(url);
                } catch (err) {
                    console.log(`[SW] Aviso: Não foi possível cachear ${url} na instalação.`);
                }
            }
        })
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.map(key => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', event => {
    const request = event.request;

    // Apenas requisições GET
    if (request.method !== 'GET') return;

    // 1. Estratégia para HTML (Navegação): Network First -> Cache
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(request, responseClone));
                    return response;
                })
                .catch(() => {
                    return caches.match(request).then(response => {
                        if (response) return response;
                        return new Response('<h1>Você está offline</h1><p>Recarregue quando tiver conexão.</p>', {
                            headers: { 'Content-Type': 'text/html' }
                        });
                    });
                })
        );
        return;
    }

    // 2. Estratégia para Estáticos (CSS, JS, Img): Cache First -> Network
    event.respondWith(
        caches.match(request).then(response => {
            return response || fetch(request).then(networkResponse => {
                return caches.open(CACHE_NAME).then(cache => {
                    cache.put(request, networkResponse.clone());
                    return networkResponse;
                });
            });
        })
    );
});