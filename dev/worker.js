/* WORKER-START
   Server of the paid app (Cloudflare Worker). The build puts geo.js and engine.js in front of
   this file. It serves the site, and these routes:
     POST /api/preview  start point -> free preview + sealed quest token (or a shared token -> its preview)
     POST /api/checkout sealed token -> Stripe Checkout page
     POST /api/unlock   paid Stripe session -> full quest
     POST /api/hit      one anonymous count of a step of the visit (home page, preview, diploma…)
     POST /api/stats    the counts and the testers' answers, for the weekly report (key derived from the Stripe secret)
     POST /api/testeur  before the opening: sealed token -> full quest, free, for a family who tests it
     POST /api/avis     before the opening: a tester's answers to the questionnaire at the end of the quest
     POST /api/espace   Nathan's private page (/espace): login + code -> counts and testers' answers
   The tester mode is on while the variable TESTEURS = "1" (wrangler.toml); removing it ends it everywhere.
   The token is encrypted (AES-GCM), so the places of a quest stay hidden until payment.
   Secrets: STRIPE_SECRET_KEY, QUEST_KEY. Variables: PRICE_CENTS, STRIPE_API (tests only).
   Optional binding: STATS (Workers KV) for the counts; without it, counting is simply off. */

const HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const reply = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: HEADERS });
const MAX_BODY = 3000000;
// One line per event in the Cloudflare logs, to count previews, payments and unlocks. No personal data.
const refOf = b => String(b && b.ref || "").replace(/[^a-z0-9-]/gi, "").slice(0, 20);
const log = (evt, data) => console.log(JSON.stringify(Object.assign({ evt }, data)));

// Anonymous counts of the visit, one KV key per event: "day|event|ref|random", kept 400 days.
// No IP address, no identifier, no cookie: only how many times each step happened, and the ref.
const EVENTS = new Set(["home", "setup", "preview", "few", "nodata", "neterr", "checkout", "unlock", "diploma",
  "invite", "diplome", "imprime", "share", "apercu", "apercu-ouvert", "horsligne", "geo-refus", "geo-echec", "testeur", "avis",
  "liens", "liens-site", "liens-instagram", "liens-tiktok", "liens-pinterest"]);
function count(env, ctx, evt, ref) {
  if (!env.STATS || !EVENTS.has(evt)) return;
  const day = new Date().toISOString().slice(0, 10);
  const key = `${day}|${evt}|${ref || "-"}|${crypto.randomUUID().slice(0, 8)}`;
  // The free plan allows 1,000 writes a day: past that, counts are lost for the day, nothing breaks.
  const p = env.STATS.put(key, "1", { expirationTtl: 400 * 86400 }).catch(() => {});
  if (ctx && ctx.waitUntil) ctx.waitUntil(p);
}
async function statsKey(env) {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("stats:" + (env.STRIPE_SECRET_KEY || "")));
  return [...new Uint8Array(d)].map(b => b.toString(16).padStart(2, "0")).join("");
}

const b64u = {
  enc(bytes) { let s = ""; for (const b of bytes) s += String.fromCharCode(b); return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); },
  dec(str) { const s = atob(str.replace(/-/g, "+").replace(/_/g, "/")); return Uint8Array.from(s, c => c.charCodeAt(0)); }
};

async function cryptoKey(env) {
  if (!env.QUEST_KEY) throw new Error("QUEST_KEY missing");
  const raw = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(env.QUEST_KEY));
  return crypto.subtle.importKey("raw", raw, "AES-GCM", false, ["encrypt", "decrypt"]);
}
async function seal(obj, env) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv }, await cryptoKey(env), new TextEncoder().encode(JSON.stringify(obj))));
  const out = new Uint8Array(12 + data.length); out.set(iv); out.set(data, 12);
  return b64u.enc(out);
}
async function unseal(token, env) {
  try {
    const b = b64u.dec(String(token));
    const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: b.slice(0, 12) }, await cryptoKey(env), b.slice(12));
    return JSON.parse(new TextDecoder().decode(plain));
  } catch (e) { return null; }
}

// Token content: start point and chosen stops, rounded. Indoor quest: { i: 1 }.
const r6 = x => Math.round(x * 1e6) / 1e6;
const pack = (start, stops) => ({ a: [r6(start.lat), r6(start.lon)], s: stops.map(s => [s.cat, r6(s.lat), r6(s.lon), s.name || "", s.id || ""]) });
function questOf(t) {
  if (!t) return null;
  if (t.i) return QuestEngine.assemble(null, QuestEngine.indoorStops());
  if (!Array.isArray(t.a) || !Array.isArray(t.s) || t.s.length < 4 || t.s.length > 6) return null;
  return QuestEngine.assemble({ lat: t.a[0], lon: t.a[1] }, t.s.map(([cat, lat, lon, name, id]) => ({ cat, lat, lon, name, id })));
}

const testers = env => env.TESTEURS === "1";
const priceCents = env => parseInt(env.PRICE_CENTS || "2490", 10);
const priceLabel = env => (priceCents(env) / 100).toFixed(2).replace(".", ",") + " €";

async function readJSON(request) {
  const len = parseInt(request.headers.get("content-length") || "0", 10);
  if (len > MAX_BODY) return null;
  try { return await request.json(); } catch (e) { return null; }
}

async function stripe(env, method, path, params, extraHeaders) {
  const base = env.STRIPE_API || "https://api.stripe.com";
  const r = await fetch(base + path, {
    method,
    headers: Object.assign({ authorization: "Bearer " + env.STRIPE_SECRET_KEY, "content-type": "application/x-www-form-urlencoded" }, extraHeaders || {}),
    body: params ? new URLSearchParams(params).toString() : undefined
  });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error("Stripe " + r.status + " " + (body.error && body.error.message || ""));
  return body;
}

// Places of France, extracted once a month from OpenStreetMap into 0.1° tiles (site/places/).
// Returns the classified places around start, or null when the tiles are not deployed.
async function placesFromTiles(start, env, origin) {
  const get = path => env.ASSETS.fetch(new Request(origin + path));
  const index = await get("/places/index.json");
  if (!index.ok) return null;
  const tile = 0.1, r = 900, dLat = r / 111320, dLon = r / (111320 * Math.cos(start.lat * Math.PI / 180));
  const keys = new Set();
  for (const la of [start.lat - dLat, start.lat + dLat]) for (const lo of [start.lon - dLon, start.lon + dLon])
    keys.add(`${Math.floor(la / tile)}_${Math.floor(lo / tile)}`);
  const places = [];
  for (const key of keys) {
    const res = await get(`/places/${key}.json`);
    if (!res.ok) continue;     // no place at all in this tile
    for (const [cat, lat, lon, name, score, id] of await res.json()) places.push({ cat, lat, lon, name, score, id });
  }
  return places;
}

// Fallback when the phone could not reach the map server: try each server from here.
async function placesFromOSM(start, origin) {
  const body = "data=" + encodeURIComponent(QuestGeo.overpassQuery(start.lat, start.lon));
  for (const url of QuestGeo.SERVERS) {
    try {
      const r = await fetch(url, { method: "POST", body, signal: AbortSignal.timeout(15000),
        headers: { "content-type": "application/x-www-form-urlencoded", "user-agent": "MaQueteLegendaire/1.0 (anniversary quests for children)", referer: origin + "/" } });
      if (!r.ok) continue;
      const j = await r.json();
      if (Array.isArray(j.elements) && !(j.remark && !j.elements.length)) return QuestGeo.slim(j.elements);
    } catch (e) { /* next server */ }
  }
  return null;
}

async function preview(request, env, ctx) {
  const b = await readJSON(request);
  if (!b) return reply({ ok: false, reason: "bad" }, 400);
  let token, quest;
  // A preview sent to someone else (the other parent): same quest, places still hidden.
  if (typeof b.token === "string" && b.token) {
    quest = questOf(await unseal(b.token, env));
    if (!quest) return reply({ ok: false, reason: "token" }, 400);
    count(env, ctx, "apercu-ouvert", refOf(b));
    return reply(Object.assign(QuestEngine.preview(quest), { token: b.token, price: priceLabel(env), testeur: testers(env) }));
  }
  if (b.indoor) {
    quest = QuestEngine.assemble(null, QuestEngine.indoorStops());
    token = await seal({ i: 1 }, env);
  } else {
    const lat = Number(b.start && b.start.lat), lon = Number(b.start && b.start.lon);
    if (!isFinite(lat) || !isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180) return reply({ ok: false, reason: "bad" }, 400);
    const start = { lat, lon };
    // 1. our own copy of OpenStreetMap places (no elements sent by the phone)
    if (!Array.isArray(b.elements) && !b.fetch) {
      const places = await placesFromTiles(start, env, new URL(request.url).origin);
      if (!places) { count(env, ctx, "nodata", refOf(b)); return reply({ ok: false, reason: "nodata" }, 503); }
      const sel = QuestEngine.selectPlaces(places, start);
      log("preview", { ok: sel.ok, source: "tiles", found: sel.found, ref: refOf(b) });
      count(env, ctx, sel.ok ? "preview" : "few", refOf(b));
      if (!sel.ok) return reply(sel);
      quest = QuestEngine.assemble(start, sel.stops);
      token = await seal(pack(start, sel.stops), env);
      return reply(Object.assign(QuestEngine.preview(quest), { token, price: priceLabel(env), testeur: testers(env) }));
    }
    // 2. places fetched from Overpass, by the phone or (fallback) by this server
    if (b.fetch && !Array.isArray(b.elements)) {
      b.elements = await placesFromOSM(start, new URL(request.url).origin);
      log("osm", { ok: !!b.elements });
      if (!b.elements) return reply({ ok: false, reason: "osm" }, 503);
    }
    if (!Array.isArray(b.elements) || b.elements.length > 5000) return reply({ ok: false, reason: "bad" }, 400);
    const sel = QuestEngine.select(b.elements, start);
    if (!sel.ok) { log("preview", { ok: false, found: sel.found, ref: refOf(b) }); count(env, ctx, "few", refOf(b)); return reply(sel); }
    quest = QuestEngine.assemble(start, sel.stops);
    token = await seal(pack(start, sel.stops), env);
  }
  log("preview", { ok: true, indoor: !!b.indoor, steps: quest.steps.length, ref: refOf(b) });
  count(env, ctx, "preview", refOf(b));
  return reply(Object.assign(QuestEngine.preview(quest), { token, price: priceLabel(env), testeur: testers(env) }));
}

async function checkout(request, env, ctx) {
  // Before the opening (TESTEURS = "1"), no payment at all, even with the real Stripe key in place.
  if (testers(env)) return reply({ ok: false, reason: "closed" }, 403);
  const b = await readJSON(request);
  if (!b || b.consent !== true) return reply({ ok: false, reason: "consent" }, 400);
  const t = await unseal(b.token, env);
  const quest = questOf(t);
  if (!quest) return reply({ ok: false, reason: "token" }, 400);
  const origin = new URL(request.url).origin;
  const name = String(b.name || "").slice(0, 24), hero = b.hero === "f" ? "f" : "m";
  const town = String(b.town || "").slice(0, 60), kids = Math.max(2, Math.min(15, parseInt(b.kids, 10) || 8));
  const token = String(b.token);
  const params = {
    mode: "payment",
    locale: "fr",
    "line_items[0][quantity]": "1",
    "line_items[0][price_data][currency]": "eur",
    "line_items[0][price_data][unit_amount]": String(priceCents(env)),
    "line_items[0][price_data][product_data][name]": "La Quête du Chevalier · Ma Quête Légendaire",
    "line_items[0][price_data][product_data][description]":
      `Quête d'anniversaire de ${name || "votre enfant"} : ${quest.steps.length} étapes${quest.indoorOnly ? " à la maison" : town ? " à " + town : ""}. Accès immédiat.`,
    success_url: origin + "/?paid={CHECKOUT_SESSION_ID}",
    cancel_url: origin + "/?annule=1",
    "custom_text[submit][message]": "Vous avez demandé l'accès immédiat à la quête et renoncé au droit de rétractation (article L221-28 du Code de la consommation).",
    "metadata[n]": name, "metadata[h]": hero, "metadata[k]": String(kids), "metadata[v]": town,
    "metadata[consent]": new Date().toISOString(), "metadata[ref]": refOf(b)
  };
  for (let i = 0; i * 490 < token.length; i++) params[`metadata[t${i}]`] = token.slice(i * 490, (i + 1) * 490);
  // The brand on the payment page, set here so it is the same in Stripe's test and live modes
  // (a sandbox does not share the Dashboard's branding). Needs API version 2025-09-30.clover or later;
  // if Stripe refuses it, the payment page opens with the Dashboard's branding instead.
  const brand = {
    "branding_settings[display_name]": "Ma Quête Légendaire",
    "branding_settings[background_color]": "#1b2547",
    "branding_settings[button_color]": "#b8505c",
    "branding_settings[border_style]": "rounded",
    "branding_settings[icon][type]": "url", "branding_settings[icon][url]": origin + "/stripe-icon.png",
    "branding_settings[logo][type]": "url", "branding_settings[logo][url]": origin + "/stripe-logo.png"
  };
  try {
    let s, branding = "ok";
    try { s = await stripe(env, "POST", "/v1/checkout/sessions", Object.assign({}, params, brand), { "stripe-version": "2025-09-30.clover" }); }
    catch (e) { branding = String(e.message || e).slice(0, 200); console.log("branding refused: " + branding); s = await stripe(env, "POST", "/v1/checkout/sessions", params); }
    log("checkout", { ref: refOf(b), branding: branding === "ok" });
    count(env, ctx, "checkout", refOf(b));
    return reply({ ok: true, url: s.url, branding });
  } catch (e) {
    console.log(String(e));
    // Stripe's own message (for example a missing account setting) helps fix the setup; it holds no secret.
    return reply({ ok: false, reason: "stripe", detail: String(e.message || e).slice(0, 300) }, 502);
  }
}

async function unlock(request, env, ctx) {
  const b = await readJSON(request);
  const id = String(b && b.session || "");
  if (!/^cs_(test|live)_[A-Za-z0-9]{10,200}$/.test(id)) return reply({ ok: false, reason: "bad" }, 400);
  let s;
  try { s = await stripe(env, "GET", "/v1/checkout/sessions/" + id); }
  catch (e) { console.log(String(e)); return reply({ ok: false, reason: "unknown" }, 404); }
  if (s.payment_status !== "paid") { log("unlock", { ok: false, reason: "unpaid" }); return reply({ ok: false, reason: "unpaid" }, 402); }
  const m = s.metadata || {};
  let token = "";
  for (let i = 0; m["t" + i]; i++) token += m["t" + i];
  const quest = questOf(await unseal(token, env));
  if (!quest) return reply({ ok: false, reason: "token" }, 500);
  log("unlock", { ok: true, ref: m.ref || "" });
  count(env, ctx, "unlock", refOf(m));
  return reply({ ok: true, quest, name: m.n || "", hero: m.h === "f" ? "f" : "m", kids: parseInt(m.k, 10) || 8, town: m.v || "" });
}

// Before the opening: a family who tests the quest gets it free, and answers a few questions at the end.
async function testeur(request, env, ctx) {
  if (!testers(env)) return reply({ ok: false, reason: "closed" }, 403);
  const b = await readJSON(request);
  const quest = questOf(await unseal(b && b.token, env));
  if (!quest) return reply({ ok: false, reason: "token" }, 400);
  log("testeur", { ref: refOf(b) });
  count(env, ctx, "testeur", refOf(b));
  return reply({ ok: true, quest });
}

// The questionnaire's answers, kept 400 days under "avis|<time>|<random>". No IP or cookie: only what the
// parent typed, with their first name, last name and e-mail (to know who answered and write back; the
// first name alone is shown on the site, and only if they agree to be quoted).
const pick = (v, list) => list.includes(v) ? v : "";
const txt = (v, n) => String(v || "").replace(/[\u0000-\u001f]+/g, " ").trim().slice(0, n);
const mail = v => { const m = txt(v, 120).toLowerCase(); return /^[^\s@|]+@[^\s@|]+\.[^\s@|]{2,}$/.test(m) ? m : ""; };
async function avis(request, env, ctx) {
  if (!testers(env)) return reply({ ok: false, reason: "closed" }, 403);
  const b = await readJSON(request);
  if (!b || typeof b !== "object") return reply({ ok: false, reason: "bad" }, 400);
  const a = {
    note: Math.max(0, Math.min(5, parseInt(b.note, 10) || 0)),
    enfants: pick(b.enfants, ["adore", "bien", "bof"]),
    duree: pick(b.duree, ["court", "juste", "long"]),
    prix: pick(b.prix, ["oui", "peut-etre", "non"]),
    prefere: txt(b.prefere, 400), coince: txt(b.coince, 600),
    citer: b.citer === true, prenom: txt(b.prenom, 40), nom: txt(b.nom, 60), email: mail(b.email),
    maison: !!b.maison, etapes: Math.max(0, Math.min(6, parseInt(b.etapes, 10) || 0)),
    enfantsN: Math.max(0, Math.min(15, parseInt(b.enfantsN, 10) || 0)), ville: txt(b.ville, 60), ref: refOf(b)
  };
  if (!a.note && !a.enfants && !a.prefere && !a.coince) return reply({ ok: false, reason: "empty" }, 400);
  if (!a.prenom || !a.nom || !a.email) return reply({ ok: false, reason: "contact" }, 400);
  count(env, ctx, "avis", a.ref);
  if (env.STATS) {
    const p = env.STATS.put(`avis|${new Date().toISOString()}|${crypto.randomUUID().slice(0, 8)}`, JSON.stringify(a), { expirationTtl: 400 * 86400 });
    if (ctx && ctx.waitUntil) ctx.waitUntil(p.catch(() => {})); else await p.catch(() => {});
  }
  log("avis", { note: a.note });
  return reply({ ok: true });
}

// A step of the visit seen by the phone (sent with navigator.sendBeacon).
async function hit(request, env, ctx) {
  const b = await readJSON(request);
  if (b && typeof b.e === "string") count(env, ctx, b.e, refOf(b));
  return new Response(null, { status: 204 });
}

// Counts for the weekly report: { days: { "2026-10-14": { home: { direct: 3, fete: 1 }, … } } }.
async function stats(request, env) {
  const b = await readJSON(request);
  if (!b || b.key !== await statsKey(env)) return reply({ ok: false, reason: "key" }, 403);
  if (!env.STATS) return reply({ ok: false, reason: "off" }, 503);
  return reply(Object.assign({ ok: true }, await collect(env, b.days)));
}

// Nathan's private page (/espace): login + code, checked against a salted SHA-256 kept in wrangler.toml
// (ESPACE_ID, ESPACE_SALT, ESPACE_HASH). The code is random (about 80 bits): the hash can stay public.
async function espace(request, env) {
  const b = await readJSON(request);
  if (!env.ESPACE_HASH || !env.ESPACE_SALT || !env.ESPACE_ID) return reply({ ok: false, reason: "off" }, 503);
  const id = String(b && b.id || "").trim().toLowerCase(), code = String(b && b.code || "").trim().toUpperCase().replace(/\s+/g, "");
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${env.ESPACE_SALT}:${id}:${code}`));
  const h = [...new Uint8Array(d)].map(x => x.toString(16).padStart(2, "0")).join("");
  let diff = h.length ^ env.ESPACE_HASH.length;
  for (let i = 0; i < h.length; i++) diff |= h.charCodeAt(i) ^ (env.ESPACE_HASH.charCodeAt(i) || 0);
  if (id !== env.ESPACE_ID || diff) { await new Promise(r => setTimeout(r, 400)); return reply({ ok: false, reason: "login" }, 403); }
  if (!env.STATS) return reply({ ok: false, reason: "off" }, 503);
  return reply(Object.assign({ ok: true, testeurs: testers(env) }, await collect(env, b.days || 28)));
}

async function collect(env, nDays) {
  const n = Math.max(1, Math.min(60, parseInt(nDays, 10) || 7)), days = {};
  for (let i = 0; i < n; i++) {
    const day = new Date(Date.now() - i * 86400000).toISOString().slice(0, 10), d = days[day] = {};
    let cursor;
    do {
      const page = await env.STATS.list({ prefix: day + "|", cursor });
      for (const k of page.keys) {
        const [, evt, ref] = k.name.split("|");
        (d[evt] = d[evt] || {})[ref] = (d[evt][ref] || 0) + 1;
      }
      cursor = page.list_complete ? null : page.cursor;
    } while (cursor);
  }
  // the testers' answers, newest first
  const answers = [];
  let cur;
  do {
    const page = await env.STATS.list({ prefix: "avis|", cursor: cur });
    for (const k of page.keys) { const v = await env.STATS.get(k.name); if (v) answers.push(Object.assign({ date: k.name.split("|")[1] }, JSON.parse(v))); }
    cur = page.list_complete ? null : page.cursor;
  } while (cur && answers.length < 500);
  answers.sort((x, y) => y.date.localeCompare(x.date));
  return { days, avis: answers };
}

const SHORT = { "/tiktok": "tiktok", "/insta": "instagram", "/instagram": "instagram", "/pinterest": "pinterest", "/youtube": "youtube" };

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    // www and the technical workers.dev address send page visits to the main address, keeping
    // the path and the ?ref (QR codes, links already shared). The API answers on every address.
    if (env.SITE_HOST && url.hostname !== env.SITE_HOST && !url.pathname.startsWith("/api/") && (request.method === "GET" || request.method === "HEAD"))
      return Response.redirect("https://" + env.SITE_HOST + url.pathname + url.search, 301);
    // Short addresses to say or type (videos, bios): maquetelegendaire.fr/tiktok -> /?ref=tiktok,
    // so the visits are counted by origin even when the address is typed by hand.
    const short = SHORT[url.pathname.replace(/\/+$/, "").toLowerCase()];
    if (short && (request.method === "GET" || request.method === "HEAD"))
      return Response.redirect(url.origin + "/?ref=" + short, 302);
    if (url.pathname.startsWith("/api/")) {
      if (request.method !== "POST") return reply({ ok: false, reason: "method" }, 405);
      try {
        if (url.pathname === "/api/preview") return await preview(request, env, ctx);
        if (url.pathname === "/api/checkout") return await checkout(request, env, ctx);
        if (url.pathname === "/api/unlock") return await unlock(request, env, ctx);
        if (url.pathname === "/api/hit") return await hit(request, env, ctx);
        if (url.pathname === "/api/stats") return await stats(request, env);
        if (url.pathname === "/api/espace") return await espace(request, env);
        if (url.pathname === "/api/testeur") return await testeur(request, env, ctx);
        if (url.pathname === "/api/avis") return await avis(request, env, ctx);
      } catch (e) {
        console.log(String(e && e.stack || e));
        return reply({ ok: false, reason: "server" }, 500);
      }
      return reply({ ok: false, reason: "route" }, 404);
    }
    return env.ASSETS.fetch(request);
  }
};
/* WORKER-END */
