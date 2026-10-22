// Service worker: lets a bought quest play without network (a village with no signal, a phone
// that reloads the page in the middle of the quest). The page fills the cache after the unlock
// (keepOffline in app.template.html); this worker only answers from it.
//   page (navigation): network first, cached copy if the network fails or takes over 6 s
//   voice, fonts, list of names: cached copy first (with "Range" support: phones ask audio in pieces)
//   everything else (/api/, other sites): untouched
const CACHE = "quete-voix-d391eb477b";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil((async () => {
  for (const k of await caches.keys()) if (k.startsWith("quete-voix-") && k !== CACHE) await caches.delete(k);
  await self.clients.claim();
})()));

const home = () => new URL("./", self.registration.scope).href;

async function page(request) {
  const cached = await caches.match(home());
  const net = fetch(request).then(async r => {
    // keep the newest page for later, but only on phones that already keep a quest (cache present)
    if (r.ok && cached) (await caches.open(CACHE)).put(home(), r.clone());
    return r;
  });
  if (!cached) return net;
  const late = new Promise(res => setTimeout(() => res(cached), 6000));
  return Promise.race([net.catch(() => cached), late]);
}

// Audio elements ask "Range: bytes=…": answer 206 with the slice, or Safari refuses to play.
async function ranged(request, response) {
  const range = request.headers.get("range");
  if (!range) return response;
  const m = /bytes=(\d*)-(\d*)/.exec(range);
  const buf = await response.arrayBuffer(), size = buf.byteLength;
  let start = m && m[1] ? parseInt(m[1], 10) : 0, end = m && m[2] ? parseInt(m[2], 10) : size - 1;
  if (m && !m[1] && m[2]) { start = Math.max(0, size - parseInt(m[2], 10)); end = size - 1; }
  end = Math.min(end, size - 1);
  if (start >= size || start > end) return new Response(null, { status: 416, headers: { "content-range": `bytes */${size}` } });
  return new Response(buf.slice(start, end + 1), { status: 206, statusText: "Partial Content", headers: {
    "content-type": response.headers.get("content-type") || "audio/mpeg",
    "content-range": `bytes ${start}-${end}/${size}`, "content-length": String(end - start + 1), "accept-ranges": "bytes" } });
}

self.addEventListener("fetch", e => {
  const r = e.request;
  if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.origin !== self.location.origin) return;
  if (r.mode === "navigate") {
    const root = new URL(home()).pathname;   // only the quest page itself; the guides and legal pages stay online
    if (u.pathname === root || u.pathname === root + "index.html") e.respondWith(page(r));
    return;
  }
  if (/\/(audio|fonts)\//.test(u.pathname)) {
    e.respondWith((async () => {
      const hit = await caches.match(u.href, { ignoreSearch: true });
      return hit ? ranged(r, hit) : fetch(r);
    })());
  }
});
