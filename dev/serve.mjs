import crypto from "node:crypto";
// Local test server for the paid app: node dev/serve.mjs [port]
// Runs dist/worker.js like Cloudflare would, serves site/ and audio/, and fakes Stripe
// (a pretend checkout page with "Payer" and "Annuler"). Build first: python3 dev/build.py
// It also fakes Brevo (the e-mails are kept in memory, never sent: GET /__mails) and the API Géo, and offers
// a simulated clock (/__clock?days=7) and the daily cron (/__cron). NOBREVO=1: no e-mail key, as before it is set.
// Brevo's log of those e-mails answers too (/__brevo-status sets what happened to them, /__brevo-events breaks it).
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = parseInt(process.argv[2] || "8787", 10);
const base = `http://127.0.0.1:${port}`;

// The worker is an ES module; Node needs the .mjs extension to load it as one.
const tmp = path.join(root, "dist", "worker.test.mjs");
fs.copyFileSync(path.join(root, "dist", "worker.js"), tmp);
const worker = (await import(pathToFileURL(tmp).href)).default;

// Map servers seen from the worker: answered from dist/osm-fixture.json when the tests provide it.
const fixture = path.join(root, "dist", "osm-fixture.json");
const realFetch = globalThis.fetch;
// Fake Brevo: every e-mail the worker sends is kept here (GET /__mails), nothing leaves this machine.
// /__brevo?fail=400 (refused), 500, net (no answer) or 0 (works again).
const mails = [];
let brevoFail = "0";
// Fake API Géo: the commune of any point (/__geo?nom=… changes it).
let geoName = "Bourg-Test";
// Its log (GET /v3/smtp/statistics/events), made from the e-mails above: each one "requests", then the events set by
// /__brevo-status?to=<address>&event=delivered|hardBounces|softBounces|blocked|error|deferred|spam|…&reason=…
// (on every e-mail sent so far to that address). /__brevo-events?fail=500|net|slow|format|0 breaks this API alone.
let eventsFail = "0", eventsCalls = 0;
function brevoLog(url) {
  const all = [];
  mails.forEach((m, i) => {
    const one = (event, at, reason) => all.push(Object.assign({ email: m.to[0], date: new Date(at).toISOString().replace("Z", "+00:00"), subject: m.subject,
      messageId: m.messageId, event, tag: (m.tags || [])[0] || "", from: m.from.email, ts: Math.floor(at / 1000) }, reason ? { reason } : {}));
    one("requests", m.at);
    (m.events || []).forEach(([event, reason], k) => one(event, m.at + 1000 * (k + 1), reason));
  });
  const days = parseInt(url.searchParams.get("days") || "0", 10), limit = parseInt(url.searchParams.get("limit") || "2500", 10), offset = parseInt(url.searchParams.get("offset") || "0", 10);
  const since = days ? Date.now() - days * 86400000 : 0;
  const list = all.filter(e => Date.parse(e.date) >= since).sort((a, b) => url.searchParams.get("sort") === "asc" ? a.ts - b.ts : b.ts - a.ts);
  return list.slice(offset, offset + limit);
}
globalThis.fetch = async (input, init) => {
  const u = String(input && input.url || input);
  if (/overpass/.test(u) && fs.existsSync(fixture)) return new Response(fs.readFileSync(fixture), { headers: { "content-type": "application/json" } });
  if (u.startsWith("https://api.brevo.com/v3/smtp/statistics/events")) {
    eventsCalls++;
    if (new Headers(init && init.headers).get("api-key") !== "xkeysib-test-local") return Response.json({ code: "unauthorized", message: "Key not found" }, { status: 401 });
    if (eventsFail === "net") throw new TypeError("fetch failed");
    if (eventsFail === "slow") { await new Promise((ok, ko) => { const t = setTimeout(ok, 20000); init.signal && init.signal.addEventListener("abort", () => { clearTimeout(t); ko(init.signal.reason); }); }); }
    if (eventsFail === "format") return Response.json({ data: [] });
    if (eventsFail !== "0") return Response.json({ code: "internal_error", message: "fake failure" }, { status: parseInt(eventsFail, 10) });
    const list = brevoLog(new URL(u));
    return list.length ? Response.json({ events: list }) : Response.json({});
  }
  if (u.startsWith("https://api.brevo.com/")) {
    if (brevoFail === "net") throw new TypeError("fetch failed");
    if (brevoFail !== "0") return Response.json({ code: "fake_error", message: "fake failure" }, { status: parseInt(brevoFail, 10) });
    const h = new Headers(init && init.headers);
    if (u !== "https://api.brevo.com/v3/smtp/email" || (init && init.method) !== "POST" || h.get("api-key") !== "xkeysib-test-local")
      return Response.json({ code: "unauthorized", message: "Key not found" }, { status: 401 });
    const b = JSON.parse(init.body);
    if (!b.sender || !b.sender.email || !Array.isArray(b.to) || !b.to[0] || !b.subject || !b.htmlContent) return Response.json({ code: "missing_parameter" }, { status: 400 });
    const messageId = `<20261114.fake${mails.length + 1}@smtp-relay.test>`;
    mails.push({ to: b.to.map(x => x.email), from: b.sender, replyTo: b.replyTo || null, subject: b.subject, html: b.htmlContent, text: b.textContent || "",
      headers: b.headers || {}, tags: b.tags || [], at: Date.now(), messageId, events: [] });
    return Response.json({ messageId }, { status: 201 });
  }
  if (u.startsWith("https://geo.api.gouv.fr/communes?")) return Response.json(geoName ? [{ nom: geoName, code: "67999" }] : []);
  return realFetch(input, init);
};
// Simulated clock for the reminders: /__clock?days=7 moves Date.now() (the worker's and the fake KV's) 7 days ahead.
const realNow = Date.now.bind(Date);
let offset = 0;
Date.now = () => realNow() + offset;

const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".png": "image/png", ".svg": "image/svg+xml", ".txt": "text/plain", ".xml": "application/xml", ".json": "application/json", ".mp3": "audio/mpeg", ".woff": "font/woff", ".css": "text/css", ".mp4": "video/mp4", ".webm": "video/webm", ".jpg": "image/jpeg", ".webp": "image/webp" };
// Same HTML handling as Cloudflare's static assets ("auto-trailing-slash", the default):
// /page serves page.html and /page.html redirects to /page (307); /dir/ serves dir/index.html,
// /dir and /dir/index.html redirect to /dir/.
const isFile = f => fs.existsSync(f) && fs.statSync(f).isFile();
function file(p, search = "") {
  const clean = decodeURIComponent(p).replace(/\.\.+/g, "");
  const site = path.join(root, "site");
  const moved = to => new Response(null, { status: 307, headers: { location: to + search } });
  if (clean.endsWith("/index.html") && isFile(path.join(site, clean))) return moved(clean.slice(0, -"index.html".length));
  if (clean.endsWith(".html") && isFile(path.join(site, clean))) return moved(clean.slice(0, -".html".length));
  if (!clean.endsWith("/") && !path.extname(clean) && isFile(path.join(site, clean, "index.html"))) return moved(clean + "/");
  if (clean.length > 1 && clean.endsWith("/") && isFile(path.join(site, clean.slice(0, -1) + ".html"))) return moved(clean.slice(0, -1));
  for (const dir of ["site", "."]) {
    let f = path.join(root, dir, clean);
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, "index.html");
    else if (dir === "site" && !isFile(f) && isFile(f + ".html")) f += ".html";
    if (isFile(f) && (dir === "site" || clean.startsWith("/audio/")))
      return new Response(fs.readFileSync(f), { headers: { "content-type": TYPES[path.extname(f)] || "application/octet-stream" } });
  }
  return new Response("Not found", { status: 404 });
}

// Fake Stripe: sessions kept in memory.
const sessions = new Map();
let n = 0;
async function fakeStripe(req, url) {
  const auth = req.headers.get("authorization") || "";
  if (!auth.startsWith("Bearer sk_test_")) return Response.json({ error: { message: "bad key" } }, { status: 401 });
  if (req.method === "POST" && url.pathname === "/stripe/v1/checkout/sessions") {
    const p = new URLSearchParams(await req.text());
    const id = "cs_test_" + "a1B2c3D4e5".repeat(3) + String(++n).padStart(4, "0");
    const metadata = {};
    for (const [k, v] of p) { const m = k.match(/^metadata\[(.+)\]$/); if (m) metadata[m[1]] = v; }
    sessions.set(id, { id, payment_status: "unpaid", status: "open", metadata, params: Object.fromEntries(p) });
    return Response.json({ id, url: `${base}/fake-checkout?id=${id}` });
  }
  if (req.method === "GET" && url.pathname === "/stripe/v1/checkout/sessions")
    return Response.json({ data: [...sessions.values()].map(x => Object.assign({ amount_total: x.payment_status === "paid" ? 2490 : null }, x)).reverse(), has_more: false });
  if (req.method === "GET" && url.pathname === "/stripe/v1/refunds") return Response.json({ data: [], has_more: false });
  const m = url.pathname.match(/^\/stripe\/v1\/checkout\/sessions\/([^/]+)$/);
  if (req.method === "GET" && m) {
    const s = sessions.get(m[1]);
    return s ? Response.json(s) : Response.json({ error: { message: "No such checkout.session" } }, { status: 404 });
  }
  return Response.json({ error: { message: "route" } }, { status: 404 });
}
function fakeCheckout(url) {
  const s = sessions.get(url.searchParams.get("id"));
  if (!s) return new Response("no session", { status: 404 });
  if (url.searchParams.get("pay")) {
    s.payment_status = "paid"; s.status = "complete";
    return Response.redirect(s.params.success_url.replace("{CHECKOUT_SESSION_ID}", s.id), 303);
  }
  return new Response(`<!doctype html><meta charset="utf-8"><title>Fake Stripe</title><h1>Paiement factice</h1>
<p>${s.params["line_items[0][price_data][product_data][description]"]}</p><p>${s.params["line_items[0][price_data][unit_amount]"]} centimes</p>${s.params.allow_promotion_codes === "true" ? "<p>Champ « Ajouter un code promotionnel » proposé</p>" : ""}
<p id="msg">${s.params["custom_text[submit][message]"]}</p>
<a id="pay" href="/fake-checkout?id=${s.id}&pay=1">Payer</a> <a id="cancel" href="${s.params.cancel_url}">Annuler</a>`,
    { headers: { "content-type": "text/html; charset=utf-8" } });
}

// Fake Workers KV (binding STATS): values, metadata, expiration (on the simulated clock), list by prefix in
// key order with pages (KV_PAGE=n makes pages of n keys, to test the cursor; Cloudflare's default is 1000).
const kv = new Map();
const alive = k => { const e = kv.get(k); if (e && e.exp && e.exp <= Date.now()) kv.delete(k); return kv.has(k); };
const PAGE = parseInt(process.env.KV_PAGE || "1000", 10);
const STATS = {
  put: async (k, v, o = {}) => {
    const exp = o.expiration ? o.expiration * 1000 : o.expirationTtl ? Date.now() + o.expirationTtl * 1000 : 0;
    if (exp && exp < Date.now() + 60000) throw new Error("KV PUT failed: 400 Invalid expiration (less than 60 seconds ahead)");
    kv.set(k, { v: String(v), exp, meta: o.metadata === undefined ? null : JSON.parse(JSON.stringify(o.metadata)) });
  },
  get: async k => alive(k) ? kv.get(k).v : null,
  delete: async k => { kv.delete(k); },
  list: async ({ prefix = "", cursor, limit } = {}) => {
    // the cursor is the last key given, so keys deleted meanwhile do not shift the next page
    const all = [...kv.keys()].filter(k => k.startsWith(prefix) && alive(k) && (!cursor || k > cursor)).sort();
    const n = Math.min(limit || PAGE, PAGE);
    const keys = all.slice(0, n).map(name => { const e = kv.get(name); const o = { name };
      if (e.exp) o.expiration = Math.floor(e.exp / 1000); if (e.meta !== null) o.metadata = e.meta; return o; });
    return all.length <= n ? { keys, list_complete: true } : { keys, list_complete: false, cursor: keys[keys.length - 1].name };
  }
};
const env = {
  STATS,
  TESTEURS: process.env.TESTEURS || "",   // TESTEURS=1 node dev/serve.mjs: the tester mode (before the opening)
  // private page /espace in the tests: login "test", code "TEST-CODE-0000-0000"
  ESPACE_ID: "test", ESPACE_SALT: "sel",
  ESPACE_HASH: crypto.createHash("sha256").update("sel:test:TEST-CODE-0000-0000").digest("hex"),
  QUEST_KEY: "cle-de-test", STRIPE_SECRET_KEY: "sk_test_local", STRIPE_API: `${base}/stripe`, PRICE_CENTS: "2490",
  // the e-mails (fake Brevo above); NOBREVO=1: as before the secret exists
  BREVO_API_KEY: process.env.NOBREVO === "1" ? undefined : "xkeysib-test-local", MAIL_DAY_MAX: process.env.MAIL_DAY_MAX || "200",
  MAIL_FROM: "bonjour@maquetelegendaire.fr", MAIL_FROM_NAME: "Ma Quête Légendaire", MAIL_REPLY_TO: "maquetelegendaire@gmail.com",
  ASSETS: { fetch: req => { const u = new URL(req.url); return file(u.pathname, u.search); } }
};

http.createServer(async (nreq, nres) => {
  const chunks = [];
  for await (const c of nreq) chunks.push(c);
  const url = new URL(nreq.url, base);
  const req = new Request(url, { method: nreq.method, headers: nreq.headers, body: ["GET", "HEAD"].includes(nreq.method) ? undefined : Buffer.concat(chunks) });
  let res;
  try {
    if (url.pathname.startsWith("/stripe/")) res = await fakeStripe(req, url);
    else if (url.pathname === "/fake-checkout") res = fakeCheckout(url);
    else if (url.pathname === "/__sessions") res = Response.json([...sessions.values()]);
    else if (url.pathname === "/__counts") res = Response.json([...kv.keys()].filter(k => !k.startsWith("rappel") && alive(k)));
    else if (url.pathname === "/__mails") { res = Response.json(mails); if (url.searchParams.get("clear")) mails.length = 0; }
    else if (url.pathname === "/__brevo") { brevoFail = url.searchParams.get("fail") || "0"; res = Response.json({ fail: brevoFail }); }
    else if (url.pathname === "/__brevo-events") { if (url.searchParams.has("fail")) eventsFail = url.searchParams.get("fail") || "0"; res = Response.json({ fail: eventsFail, calls: eventsCalls }); }
    else if (url.pathname === "/__brevo-status") {
      const to = (url.searchParams.get("to") || "").toLowerCase(), hit = mails.filter(m => m.to[0] === to);
      for (const m of hit) m.events.push([url.searchParams.get("event") || "delivered", url.searchParams.get("reason") || ""]);
      res = Response.json({ mails: hit.length });
    }
    else if (url.pathname === "/__geo") { geoName = url.searchParams.get("nom") || ""; res = Response.json({ nom: geoName }); }
    else if (url.pathname === "/__clock") { offset = parseFloat(url.searchParams.get("days") || "0") * 86400000; res = Response.json({ now: new Date(Date.now()).toISOString() }); }
    else if (url.pathname === "/__kv") {
      if (req.method === "POST") { const b = await req.json(); await STATS.put(b.key, b.value, b.options || {}); }
      if (req.method === "DELETE") await STATS.delete(url.searchParams.get("key") || "");
      res = Response.json(Object.fromEntries([...kv.keys()].filter(k => k.startsWith(url.searchParams.get("prefix") || "") && alive(k)).map(k => [k, kv.get(k)])));
    }
    else if (url.pathname === "/__cron") {
      // the daily cron, at the simulated time; waits for everything the handler started
      const before = mails.length, waits = [];
      await worker.scheduled({ scheduledTime: Date.now(), cron: "17 8 * * *" }, env, { waitUntil: p => waits.push(p) });
      await Promise.all(waits);
      res = Response.json({ ok: true, sent: mails.length - before });
    }
    else res = await worker.fetch(req, env, { waitUntil: p => p });
  } catch (e) { res = new Response(String(e && e.stack || e), { status: 500 }); }
  nres.writeHead(res.status, Object.fromEntries(res.headers));
  nres.end(Buffer.from(await res.arrayBuffer()));
}).listen(port, "127.0.0.1", () => console.log("Serveur de test : " + base));
