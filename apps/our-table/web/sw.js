/* Website-only offline cache. Android loads bundled assets and never registers this. */
const CACHE='our-table-0.1.0';
const ASSETS=['./','./index.html','./style.css','./core.js','./seed.js','./app.js','./icon.svg','./manifest.webmanifest'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS))));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('our-table-')&&k!==CACHE).map(k=>caches.delete(k))))));
self.addEventListener('fetch',event=>{if(event.request.method==='GET'&&new URL(event.request.url).origin===self.location.origin)event.respondWith(caches.match(event.request).then(hit=>hit||fetch(event.request)));});
