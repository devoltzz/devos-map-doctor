// sw.js - the site's service worker: the site works offline after the first visit. build_site.py writes the version
// (the engine's and a hash of every file) and the file list below; a new build is a new cache, and the old ones go.
// Every request of the site is answered from the cache first; what is not in it (the file name index, names.npz,
// fetched only when the page asks for it) is fetched and kept. The site sends nothing anywhere.
'use strict';

const CACHE = 'doctor-__VERSION__';
const ASSETS = __ASSETS__;
const OPTIONAL = __OPTIONAL__;

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(ASSETS);
    // the game data (served from the host's own folder) and the like: kept when there, never a reason to fail
    await Promise.all(OPTIONAL.map(u => cache.add(u).catch(() => null)));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith('doctor-') && k !== CACHE) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(req, { ignoreSearch: true });
    if (hit) return hit;
    const res = await fetch(req);
    if (res.ok && res.status === 200) cache.put(req, res.clone()).catch(() => null);
    return res;
  })());
});
