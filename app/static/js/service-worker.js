const CACHE_NAME = 'qualigestor-dynamic-v2'; // Versão nova para forçar atualização
const STATIC_ASSETS = [
    '/static/css/dashboard.css',
    '/static/js/sidebar.js', // Se existir
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://unpkg.com/dexie@latest/dist/dexie.js',
    '/static/img/logo.jpg',
    '/cli/listar-aplicacoes' // Cacheia a lista inicial também
];

self.addEventListener('install', event => {
    self.skipWaiting(); // Ativa imediatamente sem esperar fechar o navegador
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(self.clients.claim()); // Assume o controle das páginas abertas
});

self.addEventListener('fetch', event => {
    const request = event.request;

    // 1. Lógica para PÁGINAS HTML (Navegação)
    // Tenta pegar da rede primeiro (para ter o dado mais fresco),
    // se falhar (offline), pega a cópia salva no cache.
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Se a rede funcionou, salva uma cópia nova no cache para o futuro
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(request, responseClone));
                    return response;
                })
                .catch(() => {
                    // Se a rede falhou, entrega o que tiver no cofre
                    return caches.match(request).then(response => {
                        if (response) return response;
                        // Opcional: retornar uma página de "Você está offline" genérica
                    });
                })
        );
        return;
    }

    // 2. Lógica para Arquivos Estáticos (CSS, JS, Imagens)
    // Tenta o cache primeiro (mais rápido), se não tiver, vai na rede.
    event.respondWith(
        caches.match(request).then(response => response || fetch(request))
    );
});