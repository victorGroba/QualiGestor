const CACHE_NAME = 'qualigestor-dynamic-v8'; // ATUALIZADO: v7 -> v8

// 1. Arquivos CRÍTICOS
// Se qualquer um destes falhar ao baixar, o Service Worker NÃO instala.
// Isso garante que, se instalou, o app TEM que funcionar offline.
const CRITICAL_ASSETS = [
    // Estilos e Imagens Locais
    '/static/css/dashboard.css',
    '/static/img/logo.jpg',

    // --- IMPORTANTE: GARANTINDO O JS DO BANCO ---
    // Adicionei aqui para forçar o download da correção do banco de dados
    '/static/js/offline-manager.js', 

    // Bibliotecas Essenciais (CDN)
    // Sem Dexie, o banco não abre. Sem SignaturePad, não assina.
    'https://unpkg.com/dexie@latest/dist/dexie.js',
    'https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js',
    
    // UI (Bootstrap CSS é vital para o layout e modais)
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css'
];

// 2. Arquivos OPCIONAIS 
// Melhoram a experiência, mas o app roda sem eles (ex: ícones podem falhar e virar quadrados)
const OPTIONAL_ASSETS = [
    '/static/js/sidebar.js',
    // Adicione aqui a URL do FontAwesome se estiver usando CDN, ex:
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css' 
];

self.addEventListener('install', event => {
    self.skipWaiting(); // Força o SW a assumir imediatamente
    
    event.waitUntil(
        caches.open(CACHE_NAME).then(async cache => {
            console.log('[SW] Instalando arquivos críticos (v8)...');
            
            try {
                // Instala os críticos (Obrigatório)
                await cache.addAll(CRITICAL_ASSETS);
            } catch (error) {
                console.error('[SW] Falha crítica na instalação:', error);
                // Se falhar aqui, a instalação é abortada (correto para assets críticos)
                throw error;
            }
            
            // Tenta instalar os opcionais (Não quebra se falhar)
            for (let url of OPTIONAL_ASSETS) {
                try {
                    await cache.add(url);
                } catch (err) {
                    console.warn(`[SW] Aviso: Não foi possível cachear opcional: ${url}`);
                }
            }
        })
    );
});

self.addEventListener('activate', event => {
    console.log('[SW] Ativando versão v8 e limpando caches antigos...');
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.map(key => {
                    if (key !== CACHE_NAME) {
                        console.log('[SW] Removendo cache antigo:', key);
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim()) // Controla as páginas abertas imediatamente
    );
});

self.addEventListener('fetch', event => {
    const request = event.request;

    // Apenas requisições GET
    if (request.method !== 'GET') return;

    // 1. Estratégia para HTML (Navegação): Network First -> Cache
    // O usuário tenta abrir a página. Se tiver net, pega a nova e atualiza o cache.
    // Se não tiver net (Rancho), pega a versão cacheada na última visita.
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
                        // Fallback genérico se a página específica nunca foi visitada
                        return new Response('<h1>Você está offline</h1><p>Esta página não foi salva anteriormente.</p><a href="/">Voltar ao Início</a>', {
                            headers: { 'Content-Type': 'text/html' }
                        });
                    });
                })
        );
        return;
    }

    // 2. Estratégia para Estáticos (CSS, JS, Img, Fonts): Cache First -> Network
    // Tenta pegar do cache (rápido). Se não tiver, vai na rede e salva.
    event.respondWith(
        caches.match(request).then(cachedResponse => {
            if (cachedResponse) {
                return cachedResponse;
            }

            return fetch(request).then(networkResponse => {
                // Verifica se a resposta é válida antes de cachear
                if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic' && networkResponse.type !== 'cors') {
                    return networkResponse;
                }

                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(request, responseToCache);
                });

                return networkResponse;
            }).catch(err => {
                // Se falhar rede e não tiver no cache (ex: imagem nova)
                // Retorna nada ou placeholder, mas não quebra o app
                console.log('[SW] Fetch falhou:', request.url);
            });
        })
    );
});