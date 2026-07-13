var CACHE_NAME='fangdong-v30';
var CACHE_URLS=[
  './',
  './index.html',
  './app.html',
  './match.html',
  './manifest.json',
  './match-manifest.json',
  './icons/icon-192x192.png',
  './icons/icon-512x512.png',
  './icons-extra/icon-180x180.png',
  './match-icons/icon-192x192.png',
  './match-icons/icon-512x512.png',
  './match-icons/icon-180x180.png'
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
  e.respondWith(
    fetch(e.request).then(function(r){
      if(r&&r.status===200){
        var rc=r.clone();
        caches.open(CACHE_NAME).then(function(c){c.put(e.request,rc)});
      }
      return r;
    }).catch(function(){
      return caches.match(e.request);
    })
  );
});
