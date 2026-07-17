const CACHE_NAME = 'dehon-ai-cache-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/Avatar.png',
  '/favicon.png',
  '/Navbar.png',
  '/Sidebar.png'
];

// Instalação do Service Worker e Caching dos ativos estáticos iniciais
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('PWA Cache inicializado.');
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Ativação e limpeza de caches antigos
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('Limpando cache antigo do PWA:', cache);
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Interceptação de requisições (Network-first com fallback para Cache para ativos locais)
self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url);

  // Não cachear chamadas de API (FastAPI) nem requisições externas do Supabase
  if (requestUrl.pathname.startsWith('/api') || requestUrl.hostname.includes('supabase.co')) {
    return; // Deixa ir direto para a rede
  }

  // Apenas tratar requisições GET
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Se a resposta for válida, clona e atualiza o cache local
        if (response && response.status === 200 && response.type === 'basic') {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return response;
      })
      .catch(() => {
        // Se a rede falhar, busca no cache local
        return caches.match(event.request);
      })
  );
});
