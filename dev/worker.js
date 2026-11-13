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
     POST /api/rappel   optional: e-mail the preview's link now, and one reminder 7 days later if still unpaid
     GET  /api/rappel/stop  the unsubscribe link of those e-mails (signed); POST too, for one-click unsubscribe
   And a daily cron (wrangler.toml [triggers]) that sends the reminders due (scheduled handler).
   The tester mode is on while the variable TESTEURS = "1" (wrangler.toml); removing it ends it everywhere.
   The token is encrypted (AES-GCM), so the places of a quest stay hidden until payment.
   Secrets: STRIPE_SECRET_KEY, QUEST_KEY, BREVO_API_KEY (optional: without it the e-mails are off).
   Variables: PRICE_CENTS, STRIPE_API (tests only), MAIL_FROM, MAIL_FROM_NAME, MAIL_REPLY_TO, BREVO_API (tests only).
   Optional binding: STATS (Workers KV) for the counts and the e-mail reminders; without it, both are simply off. */

const HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const reply = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: HEADERS });
const MAX_BODY = 3000000;
// One line per event in the Cloudflare logs, to count previews, payments and unlocks. No personal data.
const refOf = b => String(b && b.ref || "").replace(/[^a-z0-9-]/gi, "").slice(0, 20);
const log = (evt, data) => console.log(JSON.stringify(Object.assign({ evt }, data)));

// Anonymous counts of the visit, one KV key per event: "day|event|ref|random", kept 400 days.
// No IP address, no identifier, no cookie: only how many times each step happened, and the ref.
const EVENTS = new Set(["home", "setup", "preview", "few", "nodata", "neterr", "checkout", "unlock", "achat", "promo", "demo", "diploma",
  "invite", "diplome", "imprime", "share", "apercu", "apercu-ouvert", "horsligne", "geo-refus", "geo-echec", "testeur", "avis",
  "liens", "liens-site", "liens-instagram", "liens-tiktok", "liens-pinterest",
  "prologue", "annule", "apercu-retour", "apercu-garde", "paybar",
  "commune-liste", "commune-tapee", "commune-proche", "localiser-ok", "localiser-echec",
  "mail-demande", "mail-rappel", "mail-stop", "mail-retour"]);
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
    // promotion codes (NOEL10…) are created by Nathan in the Stripe Dashboard and typed on the payment page
    allow_promotion_codes: "true",
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
  // back from the payment page (?paid=, not a reopening): the purchase confirmed, counted once
  if (b.first === true) count(env, ctx, "achat", refOf(m));
  // paid with a promotion code from the Stripe Dashboard (which code: see Stripe)
  if (b.first === true && s.total_details && s.total_details.amount_discount > 0) count(env, ctx, "promo", refOf(m));
  // Paid: no e-mail reminder for this quest. Best effort, after the answer; it can never fail or slow the unlock.
  if (ctx && ctx.waitUntil) ctx.waitUntil(forgetReminders(env, token).catch(() => {}));
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

/* ---------- The preview by e-mail, and one reminder (on only with BREVO_API_KEY, MAIL_FROM and STATS) ----------
   The parent leaves an address on the preview: the link is sent at once, then one reminder 7 days later if the
   quest is still not paid. The e-mails hold no text typed by the visitor: the quest comes from the sealed token,
   the town from the State's API Géo (from the token's start point), the first name only if it is one of the
   1,000 most given in France (dev/prenoms.json); anything else reads « votre enfant ».
   Keys in the KV (binding STATS), next to the counts:
     rappel:<t>.<e>      one request: { email, link, name, hero, kids, town, indoor, count, walkM, minutes, created, ref },
                         metadata { c: created (ms), x: expiration (s), n: reminder attempts, p: 1 while a reminder is going out }.
                         Expires 10 days after the request; deleted after the reminder, on payment, on unsubscribe.
     rappel-n:<e>        times of the requests for one address, kept 24 hours (at most 3 per 24 hours)
     rappel-jour:<date>  e-mails sent that UTC day (the route stops at MAIL_DAY_MAX, 200 by default), kept 2 days
     rappel-paye:<t>     this quest was paid: no reminder, kept 10 days
   <t> and <e> are HMACs of the token and of the address (key derived from QUEST_KEY, which itself never changes),
   cut to 16 hex characters: no address in a key name, and no key can be guessed from an address. */
const DAY = 86400000, REMIND_AFTER = 7 * DAY, KEEP_DAYS = 10;
const PER_ADDRESS = 3, MAX_SENDS_PER_RUN = 30, MAX_SEEN_PER_RUN = 400, STRIPE_PAGES = 3;
const mailOn = env => !!(env.BREVO_API_KEY && env.MAIL_FROM && env.STATS && env.QUEST_KEY);
const dayCap = env => parseInt(env.MAIL_DAY_MAX || "200", 10) || 200;
// Put here by dev/build.py: the first names the e-mails may print, and the seller's identity (dev/legal/identite.json).
const PRENOMS = new Map((/*PRENOMS*/[]).map(n => [n.toLowerCase(), n]));
const IDENT = /*IDENTITE*/{};

const esc = s => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
const hex = buf => [...new Uint8Array(buf)].map(x => x.toString(16).padStart(2, "0")).join("");
// A strict address: no space, no line break, a plain local part and a real domain name, 254 characters at most.
function cleanEmail(v) {
  if (typeof v !== "string") return "";
  const m = v.trim();
  if (m.length > 254 || !/^[A-Za-z0-9._%+-]{1,64}@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24}$/.test(m)) return "";
  if (/^\.|\.\.|\.@/.test(m)) return "";
  return m.toLowerCase();
}
// The preview's token, given as is or inside the preview's link.
function tokenOf(v) {
  let s = String(v || "").trim();
  if (s.length > 5000) return "";
  if (/^https?:\/\//i.test(s)) { try { s = new URL(s).searchParams.get("apercu") || ""; } catch (e) { return ""; } }
  return /^[A-Za-z0-9_-]{20,4000}$/.test(s) ? s : "";
}
async function mac(env, text, n) {
  const raw = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("rappel:" + env.QUEST_KEY));
  const key = await crypto.subtle.importKey("raw", raw, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(text))).slice(0, n);
}
function sameText(a, b) {
  a = String(a); b = String(b);
  let d = a.length ^ b.length;
  for (let i = 0; i < b.length; i++) d |= (a.charCodeAt(i) || 0) ^ b.charCodeAt(i);
  return d === 0;
}
const baseOf = (env, request) => env.SITE_HOST ? "https://" + env.SITE_HOST : new URL(request.url).origin;
const stopLink = async (env, base, id) => `${base}/api/rappel/stop?id=${id}&s=${await mac(env, "stop:" + id, 32)}`;
// The commune of the quest's start point, from the State's API Géo (Licence Ouverte); "" when it does not answer.
async function communeAt(env, a) {
  try {
    const lat = Number(a[0]), lon = Number(a[1]);
    if (!isFinite(lat) || !isFinite(lon)) return "";
    const r = await fetch(`${env.GEO_API || "https://geo.api.gouv.fr"}/communes?lat=${lat.toFixed(4)}&lon=${lon.toFixed(4)}&fields=nom&format=json`,
      { signal: AbortSignal.timeout(4000), headers: { accept: "application/json" } });
    if (!r.ok) return "";
    const j = await r.json();
    const nom = Array.isArray(j) && j[0] && typeof j[0].nom === "string" ? j[0].nom.trim() : "";
    return nom.length <= 60 ? nom : "";
  } catch (e) { return ""; }
}

// French elision, as on the site: « de Léo », « d'Arthur », « pour Hugo » (before an h); « à Obernai », « au Havre ».
const ofName = n => /^h/i.test(n) ? "pour " + n : /^y[aeiouàâäéèêëîïôöùûü]/i.test(n) ? "de " + n : (/^[aeiouyàâäæéèêëîïôöœùûü]/i.test(n) ? "d'" : "de ") + n;
const inTown = w => { const m = w.match(/^(les?)\s+(.+)$/i); return m ? (m[1].length === 3 ? "aux " : "au ") + m[2] : "à " + w; };

// The two e-mails (kind 1: the preview, at once; kind 2: the reminder, 7 days later), HTML and plain text.
// Every value is escaped; the promises are those of the payment card of the preview (dev/app.template.html).
function mailOf(env, rec, kind, stop) {
  const who = rec.name ? ofName(rec.name) : "", price = priceLabel(env), n = rec.count;
  const km = (Number(rec.walkM || 0) / 1000).toFixed(1).replace(".", ",");
  const quest = who ? `la quête d'anniversaire ${who}` : "votre quête d'anniversaire";
  const where = rec.indoor ? `${n} cachettes à la maison, environ ${rec.minutes} minutes de jeu`
    : `${n} étapes à pied ${rec.town ? inTown(rec.town) : "autour de votre point de départ"}, environ ${km} km et ${rec.minutes} minutes de jeu`;
  const subject = kind === 1 ? (who ? `L'aperçu de la quête ${who}` : "L'aperçu de votre quête d'anniversaire")
    : (who ? `La quête ${who} vous attend` : "Votre quête d'anniversaire vous attend");
  const steps = rec.indoor ? `Les ${n} cachettes et leurs cartes à imprimer, la voix du Grand Maître, les défis et les énigmes`
    : `Les ${n} étapes, la voix du Grand Maître, les défis et les énigmes`;
  const list = kind === 1 ? [steps, "Le guide de l'adulte, l'invitation et les diplômes"]
    : [steps, !rec.indoor && "S'il pleut : la même quête à la maison, sans rien racheter", "Le guide de l'adulte, l'invitation et les diplômes",
       "Le lien de la quête, valable au moins douze mois", "Jouable sans réseau, une fois la voix enregistrée"].filter(Boolean);
  // paragraphs: [text] or ["list", title, items] or ["button"]
  const body = kind === 1 ? [
    `Voici l'aperçu de ${quest}, « La Quête du Chevalier » : ${where}.`,
    "Ce lien ouvre l'aperçu sur n'importe quel téléphone ou ordinateur, sans compte :",
    ["button"],
    ["list", "Dans la quête complète", list],
    `${price} pour tout le groupe, seulement si vous décidez de la débloquer ; l'aperçu, lui, est gratuit. Paiement sécurisé par Stripe.`,
    "Nous vous écrirons une seule autre fois, dans une semaine, si la quête n'est pas débloquée. Une question ? Répondez simplement à ce message."
  ] : [
    `Il y a une semaine, vous avez créé l'aperçu de ${quest} : ${where}. Il vous attend toujours :`,
    ["button"],
    ["list", `Si vous la débloquez (${price} pour tout le groupe)`, list],
    "Paiement sécurisé par Stripe : carte, Apple Pay ou Google Pay. Un souci le jour J ? Nous vous aidons. Si la quête ne peut vraiment pas fonctionner, nous vous remboursons.",
    "C'est le seul rappel que vous recevrez : nous effaçons votre adresse de notre serveur juste après l'envoi de ce message. Une question ? Répondez simplement à ce message."
  ];
  const seller = [IDENT.nom, "entrepreneur individuel", IDENT.adresse].filter(Boolean).join(", ");
  const why = `Ce message vous est envoyé par Ma Quête Légendaire${seller ? " (" + seller + ")" : ""}, parce que vous avez demandé à recevoir l'aperçu de votre quête par e-mail sur ${new URL(rec.link).host}.`;
  const stopText = kind === 1 ? "Pour ne pas recevoir le rappel" : "Rien d'autre ne vous sera envoyé. Désinscription";
  const privacy = new URL(rec.link).origin + "/legal/confidentialite";

  const text = [ "Bonjour,", "",
    ...body.flatMap(p => p[0] === "button" ? [rec.link, ""] : p[0] === "list" ? [p[1] + " :", ...p[2].map(x => "- " + x), ""] : [p, ""]),
    "--", why, `${stopText} : ${stop}`, `Vos données : ${privacy}` ].join("\n");

  const F = "font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;";
  const P = s => `<p style="margin:0 0 16px">${esc(s)}</p>`;
  const html = `<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>${esc(subject)}</title></head>
<body style="margin:0;padding:0;background:#f4ecda">
<div style="display:none;max-height:0;overflow:hidden;opacity:0">${esc(kind === 1 ? "Le lien de votre aperçu, à ouvrir sur n'importe quel appareil." : "Votre aperçu vous attend toujours. C'est notre seul rappel.")}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f4ecda"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:560px;background:#fffaf0;border:1px solid #e2d3ae;border-radius:12px">
<tr><td style="background:#1b2547;border-radius:11px 11px 0 0;padding:18px 24px;font-family:Georgia,'Times New Roman',serif;font-size:19px;color:#f4ecda">Ma Quête Légendaire
<div style="height:2px;width:44px;background:#c9a04a;margin-top:8px;font-size:0;line-height:0">&nbsp;</div></td></tr>
<tr><td style="padding:24px;${F}font-size:16px;line-height:1.55;color:#1b2547">
<h1 style="font-family:Georgia,'Times New Roman',serif;font-weight:normal;font-size:24px;line-height:1.25;margin:0 0 18px;color:#1b2547">${esc(subject)}</h1>
${P("Bonjour,")}
${body.map(p => p[0] === "button"
    ? `<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:4px 0 10px"><tr><td style="background:#1b2547;border-radius:8px"><a href="${esc(rec.link)}" style="display:inline-block;padding:13px 22px;${F}font-size:16px;font-weight:bold;color:#ffffff;text-decoration:none;border-radius:8px">Retrouver l'aperçu</a></td></tr></table>
<p style="margin:0 0 20px;font-size:12px;line-height:1.4;color:#5b6482">Si le bouton ne s'ouvre pas, copiez ce lien dans le navigateur :<br><a href="${esc(rec.link)}" style="color:#5b6482;word-break:break-all">${esc(rec.link)}</a></p>`
    : p[0] === "list"
    ? `<p style="margin:0 0 6px;font-weight:bold;color:#1b2547">${esc(p[1])}</p><table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 16px">${p[2].map(x =>
        `<tr><td valign="top" style="padding:3px 10px 3px 0;color:#a87a1f;font-weight:bold">&#10003;</td><td style="padding:3px 0">${esc(x)}</td></tr>`).join("")}</table>`
    : P(p)).join("\n")}
</td></tr>
<tr><td style="padding:16px 24px 22px;border-top:1px solid #e2d3ae;${F}font-size:13px;line-height:1.5;color:#5b6482">
<p style="margin:0 0 8px">${esc(why)}</p>
<p style="margin:0">${esc(stopText)} : <a href="${esc(stop)}" style="color:#b8505c">se désinscrire en un clic</a> · <a href="${esc(privacy)}" style="color:#5b6482">vos données</a></p>
</td></tr></table></td></tr></table></body></html>`;
  return { subject, html, text, stop };
}

// The only call to the e-mail service: Brevo's transactional API (POST /v3/smtp/email, header api-key).
// Returns "ok", "refused" (Brevo answered with a 4xx: nothing was sent) or "unknown" (no answer, or a 5xx: maybe sent).
async function sendMail(env, to, m) {
  const body = {
    sender: { name: env.MAIL_FROM_NAME || "Ma Quête Légendaire", email: env.MAIL_FROM },
    to: [{ email: to }],
    subject: m.subject, htmlContent: m.html, textContent: m.text,
    headers: { "List-Unsubscribe": `<${m.stop}>`, "List-Unsubscribe-Post": "List-Unsubscribe=One-Click" }
  };
  if (env.MAIL_REPLY_TO) body.replyTo = { email: env.MAIL_REPLY_TO, name: env.MAIL_FROM_NAME || "Ma Quête Légendaire" };
  let r;
  try {
    r = await fetch((env.BREVO_API || "https://api.brevo.com") + "/v3/smtp/email", {
      method: "POST", signal: AbortSignal.timeout(10000), body: JSON.stringify(body),
      headers: { "api-key": env.BREVO_API_KEY, "content-type": "application/json", accept: "application/json" }
    });
  } catch (e) { console.log("brevo: no answer " + String(e && e.name || e)); return "unknown"; }
  if (r.ok) return "ok";
  console.log("brevo " + r.status + " " + (await r.text().catch(() => "")).slice(0, 300));
  return r.status >= 500 ? "unknown" : "refused";
}

// POST /api/rappel { email, apercu: the preview's token (or link), n, h, k: name, hero, kids, ref }
async function askReminder(request, env, ctx) {
  if (!mailOn(env)) return reply({ ok: false, reason: "off" }, 503);
  const b = await readJSON(request);
  if (!b || typeof b !== "object") return reply({ ok: false, reason: "bad" }, 400);
  const email = cleanEmail(b.email);
  if (!email) return reply({ ok: false, reason: "email" }, 400);
  const token = tokenOf(b.apercu), t = token ? await unseal(token, env) : null, quest = questOf(t);
  if (!quest) return reply({ ok: false, reason: "token" }, 400);
  const now = Date.now(), ref = refOf(b), base = baseOf(env, request);
  // anti-abuse: a cap on the e-mails of the day, then 3 requests per address per 24 hours
  // (ref "moi" is sent by the browser, so it cannot lift a limit; it only keeps the counts apart)
  const dayKey = "rappel-jour:" + new Date(now).toISOString().slice(0, 10);
  const today = parseInt(await env.STATS.get(dayKey), 10) || 0;
  if (today >= dayCap(env)) { log("rappel", { ok: false, reason: "full" }); return reply({ ok: false, reason: "full" }, 503); }
  const he = await mac(env, "e:" + email, 16), ht = await mac(env, "t:" + token, 16), id = ht + "." + he;
  let times = [];
  try { times = JSON.parse(await env.STATS.get("rappel-n:" + he) || "[]").filter(x => typeof x === "number" && now - x < DAY); } catch (e) { times = []; }
  if (times.length >= PER_ADDRESS) { log("rappel", { ok: false, reason: "limit" }); return reply({ ok: false, reason: "limit" }, 429); }
  await env.STATS.put("rappel-n:" + he, JSON.stringify(times.concat(now)), { expirationTtl: 86400 });

  const p = QuestEngine.preview(quest);
  const name = PRENOMS.get(String(b.n || "").trim().toLowerCase()) || "";
  const hero = b.h === "f" ? "f" : "m", kids = Math.max(2, Math.min(15, parseInt(b.k, 10) || 8));
  const town = t.i ? "" : await communeAt(env, t.a);
  const link = `${base}/?apercu=${token}&n=${encodeURIComponent(name)}&h=${hero}&k=${kids}&v=${encodeURIComponent(town)}&ref=mail`;
  const rec = { email, link, name, hero, kids, town, indoor: !!quest.indoorOnly, count: p.count, walkM: p.walkM, minutes: p.minutes, created: now, ref };
  const key = "rappel:" + id, expiration = Math.floor(now / 1000) + KEEP_DAYS * 86400;
  await env.STATS.put(key, JSON.stringify(rec), { expiration, metadata: { c: now, x: expiration, n: 0 } });
  const res = await sendMail(env, email, mailOf(env, rec, 1, await stopLink(env, base, id)));
  if (res !== "ok") {
    // not sent: nothing kept, the visitor is told to keep the link another way
    await env.STATS.delete(key).catch(() => {});
    log("rappel", { ok: false, reason: "send", res });
    return reply({ ok: false, reason: "send" }, 502);
  }
  const done = env.STATS.put(dayKey, String(today + 1), { expirationTtl: 2 * 86400 }).catch(() => {});
  if (ctx && ctx.waitUntil) ctx.waitUntil(done); else await done;
  count(env, ctx, "mail-demande", ref);
  log("rappel", { ok: true, ref });
  return reply({ ok: true });
}

// The daily cron: each request 7 days old or more, not paid, gets its one reminder, then is deleted.
// To never send twice, a record is marked before the send ("p": 1): a sure success deletes it; a sure refusal
// (Brevo answered 4xx) clears the mark for one more try the next day; no answer leaves the mark, and a marked
// record is deleted at the next run without a second send. Missing a reminder is better than sending two.
// At most 30 sends and 3 pages of Stripe a run (Workers allow 50 outgoing requests a run on the free plan) and 400
// records read: the rest go the next day.
async function sendDueReminders(env, ctx, now) {
  if (!mailOn(env)) return { off: true };
  // the list first, then the sends: deleting keys while paging through them could make the list skip some
  const keys = [];
  let sent = 0, later = 0, cursor, paid;
  do {
    const page = await env.STATS.list({ prefix: "rappel:", cursor });
    keys.push(...page.keys);
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor && keys.length < MAX_SEEN_PER_RUN);
  if (cursor || keys.length > MAX_SEEN_PER_RUN) later++;
  for (const k of keys.slice(0, MAX_SEEN_PER_RUN)) {
    try {
      const m = k.metadata || {};
      if (Number(m.c) && now - Number(m.c) < REMIND_AFTER) continue;
      if (sent >= MAX_SENDS_PER_RUN) { later++; continue; }   // the next day (and no KV operation spent on it now)
      const ht = k.name.slice("rappel:".length).split(".")[0];
      if (m.p || (Number(m.n) || 0) >= 2 || await env.STATS.get("rappel-paye:" + ht)) { await env.STATS.delete(k.name); continue; }
      const raw = await env.STATS.get(k.name);
      let rec = null;
      try { rec = JSON.parse(raw); } catch (e) { rec = null; }
      if (!rec || !cleanEmail(rec.email) || !rec.link) { await env.STATS.delete(k.name); continue; }
      const created = Number(m.c) || Number(rec.created) || 0;
      if (now - created < REMIND_AFTER) continue;
      const exp = Number(m.x) || Math.floor(created / 1000) + KEEP_DAYS * 86400;
      if (exp * 1000 - now < 120000) { await env.STATS.delete(k.name); continue; }   // about to expire anyway
      // paid, but the page never came back from Stripe (no /api/unlock, so no "rappel-paye" mark): no reminder.
      // Stripe is read once per run, only when a reminder is about to go; if it does not answer, none goes today.
      if (paid === undefined) paid = await paidTokens(env, now);
      if (paid === null) { later++; break; }
      if (paid.has(tokenOf(rec.link))) { await env.STATS.delete(k.name); continue; }
      const meta = { c: created, x: exp, n: (Number(m.n) || 0) + 1 };
      await env.STATS.put(k.name, raw, { expiration: exp, metadata: Object.assign({ p: 1 }, meta) });
      const res = await sendMail(env, rec.email, mailOf(env, rec, 2, await stopLink(env, new URL(rec.link).origin, k.name.slice("rappel:".length))));
      if (res === "ok") { sent++; await env.STATS.delete(k.name); count(env, ctx, "mail-rappel", rec.ref); }
      else if (res === "refused") await env.STATS.put(k.name, raw, { expiration: exp, metadata: meta });
    } catch (e) { console.log("reminder: " + String(e && e.message || e)); }
  }
  if (sent) {
    const dayKey = "rappel-jour:" + new Date(now).toISOString().slice(0, 10);
    await env.STATS.put(dayKey, String((parseInt(await env.STATS.get(dayKey), 10) || 0) + sent), { expirationTtl: 2 * 86400 }).catch(() => {});
  }
  log("reminders", { sent, later });
  return { sent, later };
}

// The tokens of the Checkout sessions completed in the last 11 days (a request lives 10 days), read from Stripe
// (read only, newest first, at most STRIPE_PAGES pages of 100). null when Stripe does not answer.
async function paidTokens(env, now) {
  if (!env.STRIPE_SECRET_KEY) return new Set();   // no key, no payment possible
  const tokens = new Set(), since = Math.floor(now / 1000) - (KEEP_DAYS + 1) * 86400;
  let after = "";
  try {
    for (let page = 0; page < STRIPE_PAGES; page++) {
      const r = await fetch((env.STRIPE_API || "https://api.stripe.com") + "/v1/checkout/sessions?status=complete&limit=100" +
        (after ? "&starting_after=" + encodeURIComponent(after) : ""), { signal: AbortSignal.timeout(10000), headers: { authorization: "Bearer " + env.STRIPE_SECRET_KEY } });
      if (!r.ok) throw new Error("HTTP " + r.status);
      const j = await r.json(), list = Array.isArray(j.data) ? j.data : [];
      let old = false;
      for (const s of list) {
        if (Number(s.created) && Number(s.created) < since) { old = true; break; }
        if (s.status !== "complete" && s.payment_status !== "paid") continue;
        const m = s.metadata || {};
        let t = "";
        for (let i = 0; m["t" + i]; i++) t += m["t" + i];
        if (t) tokens.add(t);
      }
      if (old || !j.has_more || !list.length) return tokens;
      after = String(list[list.length - 1].id || "");
    }
    console.log("reminders: more paid sessions than read");
    return tokens;
  } catch (e) { console.log("reminders: stripe " + String(e && e.message || e)); return null; }
}

// After a payment (from /api/unlock, in waitUntil): no reminder for this quest, and its requests are deleted now.
async function forgetReminders(env, token) {
  if (!mailOn(env) || !token) return;
  const ht = await mac(env, "t:" + token, 16), mark = "rappel-paye:" + ht;
  if (await env.STATS.get(mark)) return;   // already done at an earlier opening of this quest
  await env.STATS.put(mark, "1", { expirationTtl: KEEP_DAYS * 86400 });
  let cursor;
  do {
    const page = await env.STATS.list({ prefix: "rappel:" + ht + ".", cursor });
    for (const k of page.keys) await env.STATS.delete(k.name);
    cursor = page.list_complete ? null : page.cursor;
  } while (cursor);
}

// GET (or one-click POST) /api/rappel/stop?id=<t>.<e>&s=<signature>: deletes the request, even if already gone.
async function stopReminder(request, env, ctx, url) {
  const id = url.searchParams.get("id") || "", s = url.searchParams.get("s") || "";
  if (!env.QUEST_KEY || !/^[0-9a-f]{16}\.[0-9a-f]{16}$/.test(id) || !/^[0-9a-f]{32}$/.test(s) || !sameText(s, await mac(env, "stop:" + id, 32)))
    return stopPage("Ce lien de désinscription n'est pas valable : vérifiez qu'il est complet, ou écrivez-nous et nous effacerons votre adresse.", 403, env);
  if (env.STATS) {
    const raw = await env.STATS.get("rappel:" + id);
    if (raw) {
      await env.STATS.delete("rappel:" + id);
      let ref = "";
      try { ref = JSON.parse(raw).ref || ""; } catch (e) {}
      count(env, ctx, "mail-stop", ref);
    }
  }
  log("rappel-stop", {});
  return stopPage("", 200, env);
}
function stopPage(error, status, env) {
  const contact = IDENT.email ? `<p>Une question ? <a href="mailto:${esc(IDENT.email)}">${esc(IDENT.email)}</a></p>` : "";
  const html = `<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><meta name="color-scheme" content="light"><title>${error ? "Lien non valable" : "Rappel annulé"} · Ma Quête Légendaire</title>
<style>
@font-face{font-family:"Alegreya Sans";src:url(/fonts/AlegreyaSans-Regular.woff) format("woff");font-display:swap}
body{margin:0;background:#f4ecda;color:#1b2547;font-family:"Alegreya Sans",system-ui,sans-serif;font-size:18px;line-height:1.55}
main{max-width:520px;margin:0 auto;padding:40px 16px 56px}.brand{font-family:Georgia,serif;font-size:1rem;margin:0}
.rule{width:44px;height:2px;background:#a87a1f;margin:10px 0 28px}h1{font-family:Georgia,serif;font-weight:400;font-size:1.65rem;line-height:1.25;margin:0 0 14px}
a{color:#b8505c}p{margin:.5em 0}
</style></head><body><main><p class="brand">Ma Quête Légendaire</p><div class="rule"></div>
${error ? `<h1>Lien non valable</h1><p>${esc(error)}</p>`
  : `<h1>C'est noté : vous ne recevrez pas de rappel.</h1><p>Votre adresse e-mail est effacée de notre serveur pour cet aperçu. Le lien de l'aperçu que vous avez reçu reste valable.</p>`}
${contact}<p><a href="/">Retour au site</a></p></main></body></html>`;
  return new Response(html, { status, headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "x-robots-tag": "noindex", "referrer-policy": "no-referrer" } });
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
      // the unsubscribe link of the e-mails: opened (GET) or one-click from the mail app (POST)
      if (url.pathname === "/api/rappel/stop" && (request.method === "GET" || request.method === "POST")) {
        try { return await stopReminder(request, env, ctx, url); }
        catch (e) { console.log(String(e && e.stack || e)); return stopPage("Le désabonnement n'a pas pu être enregistré. Réessayez dans un instant, ou écrivez-nous.", 500, env); }
      }
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
        if (url.pathname === "/api/rappel") return await askReminder(request, env, ctx);
      } catch (e) {
        console.log(String(e && e.stack || e));
        return reply({ ok: false, reason: "server" }, 500);
      }
      return reply({ ok: false, reason: "route" }, 404);
    }
    return env.ASSETS.fetch(request);
  },
  // The daily cron (wrangler.toml [triggers]): the reminders due. Never throws.
  async scheduled(event, env, ctx) {
    try { await sendDueReminders(env, ctx, (event && event.scheduledTime) || Date.now()); }
    catch (e) { console.log("reminders: " + String(e && e.stack || e)); }
  }
};
/* WORKER-END */
