var CACHE_NAME='fangdong-v57';
var CACHE_URLS=[
  './',
  './index.html',
  './app.html',
  './sign.html',
  './match.html',
  './tools.html',
  './whatsnew.html',
  './image_converter.html',
  './image_compress.html',
  './birthday_manager.html',
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
function _isAuthRequest(url){
  var u=url.split('#')[0];
  return u.indexOf('type=recovery')>=0
    || u.indexOf('code=')>=0
    || u.indexOf('access_token=')>=0
    || u.indexOf('error=')>=0
    || u.indexOf('reset=1')>=0;
}
self.addEventListener('fetch',function(e){
  if(e.request.method!=='GET')return;
  var reqUrl=e.request.url||'';
  if(_isAuthRequest(reqUrl)){
    e.respondWith(fetch(e.request,{cache:'no-store'}).catch(function(){
      return caches.match(e.request,{ignoreSearch:false})
    }));
    return;
  }
  if(reqUrl.indexOf('/app.html')>=0){
    var urlObj=new URL(reqUrl);
    if(urlObj.search&&urlObj.search.length>0){
      e.respondWith(fetch(e.request,{cache:'no-store'}).catch(function(){
        return caches.match(e.request,{ignoreSearch:false})
      }));
      return;
    }
  }
  e.respondWith(
    fetch(e.request).then(function(r){
      if(r&&r.status===200&&r.type==='basic'){
        var rc=r.clone();
        caches.open(CACHE_NAME).then(function(c){c.put(e.request,rc)});
      }
      return r;
    }).catch(function(){
      return caches.match(e.request);
    })
  );
});
