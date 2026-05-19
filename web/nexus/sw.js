const CACHE = 'citasflash-v1';
const ASSETS = ['/panel/', '/panel/index.html'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).catch(()=>{}));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  // Solo cachear GET del panel, no la API
  if(e.request.method !== 'GET') return;
  if(e.request.url.includes('/api/') || e.request.url.includes('supabase')) return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
