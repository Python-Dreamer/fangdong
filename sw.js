var CACHE_NAME='fangdong-v2';
var CACHE_URLS=[
  './',
  './index.html',
  './app.html',
  './manifest.json',
  './icons/icon-192x192.png',
  './icons/icon-512x512.png'
];
self.addEventListener('install',function(e){
  e.waitUntil(caches.open(CACHE_NAME).then(function(c){return c.addAll(CACHE_URLS)}));
  self.skipWaiting();
});
self.addEventListener('activate',function(e){
  e.waitUntil(caches.keys().then(function(ks){
    return Promise.all(ks.filter(function(k){return k!==CACHE_NAME}).map(function(k){return caches.delete(k)}));
  }));
  self.clients.claim();
});
self.addEventListener('fetch',function(e){
  if(e.request.method!=='GET')return;
  // Network first, cache fallback - keeps app data fresh
  e.respondWith(
    fetch(e.request).then(function(r){