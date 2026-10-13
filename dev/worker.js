/* WORKER-START
   Server of the paid app (Cloudflare Worker). The build puts geo.js and engine.js in front of
   this file. It serves the site, and three routes:
     POST /api/preview  places found by the browser -> free preview + sealed quest token
     POST /api/checkout sealed token -> Stripe Checkout page
     POST /api/unlock   paid Stripe session -> full quest
   The token is encrypted (AES-GCM), so the places of a quest stay hidden until payment.
   Secrets: STRIPE_SECRET_KEY, QUEST_KEY. Variables: PRICE_CENTS, STRIPE_API (tests only). */

const HEADERS = { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" };
const reply = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: HEADERS });
const MAX_BODY = 3000000;

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

const priceCents = env => parseInt(env.PRICE_CENTS || "2490", 10);
const priceLabel = env => (priceCents(env) / 100).toFixed(2).replace(".", ",") + " €";

async function readJSON(request) {
  const len = parseInt(request.headers.get("content-length") || "0", 10);
  if (len > MAX_BODY) return null;
  try { return await request.json(); } catch (e) { return null; }
}

async function stripe(env, method, path, params) {
  const base = env.STRIPE_API || "https://api.stripe.com";
  const r = await fetch(base + path, {
    method,
    headers: { authorization: "Bearer " + env.STRIPE_SECRET_KEY, "content-type": "application/x-www-form-urlencoded" },
    body: params ? new URLSearchParams(params).toString() : undefined
  });
  const body = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error("Stripe " + r.status + " " + (body.error && body.error.message || ""));
  return body;
}

async function preview(request, env) {
  const b = await readJSON(request);
  if (!b) return reply({ ok: false, reason: "bad" }, 400);
  let token, quest;
  if (b.indoor) {
    quest = QuestEngine.assemble(null, QuestEngine.indoorStops());
    token = await seal({ i: 1 }, env);
  } else {
    const lat = Number(b.start && b.start.lat), lon = Number(b.start && b.start.lon);
    if (!isFinite(lat) || !isFinite(lon) || Math.abs(lat) > 90 || Math.abs(lon) > 180 || !Array.isArray(b.elements) || b.elements.length > 5000)
      return reply({ ok: false, reason: "bad" }, 400);
    const start = { lat, lon };
    const sel = QuestEngine.select(b.elements, start);
    if (!sel.ok) return reply(sel);
    quest = QuestEngine.assemble(start, sel.stops);
    token = await seal(pack(start, sel.stops), env);
  }
  return reply(Object.assign(QuestEngine.preview(quest), { token, price: priceLabel(env) }));
}

async function checkout(request, env) {
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
    "payment_method_types[0]": "card",
    "line_items[0][quantity]": "1",
    "line_items[0][price_data][currency]": "eur",
    "line_items[0][price_data][unit_amount]": String(priceCents(env)),
    "line_items[0][price_data][product_data][name]": "La Quête des Templiers",
    "line_items[0][price_data][product_data][description]":
      `Quête d'anniversaire de ${name || "votre enfant"} : ${quest.steps.length} étapes${quest.indoorOnly ? " à la maison" : town ? " à " + town : ""}. Accès immédiat.`,
    success_url: origin + "/?paid={CHECKOUT_SESSION_ID}",
    cancel_url: origin + "/?annule=1",
    "custom_text[submit][message]": "Vous avez demandé l'accès immédiat à la quête et renoncé au droit de rétractation (article L221-28 du Code de la consommation). Garantie : quête réussie ou remboursée.",
    "metadata[n]": name, "metadata[h]": hero, "metadata[k]": String(kids), "metadata[v]": town,
    "metadata[consent]": new Date().toISOString()
  };
  for (let i = 0; i * 490 < token.length; i++) params[`metadata[t${i}]`] = token.slice(i * 490, (i + 1) * 490);
  try {
    const s = await stripe(env, "POST", "/v1/checkout/sessions", params);
    return reply({ ok: true, url: s.url });
  } catch (e) {
    console.log(String(e));
    return reply({ ok: false, reason: "stripe" }, 502);
  }
}

async function unlock(request, env) {
  const b = await readJSON(request);
  const id = String(b && b.session || "");
  if (!/^cs_(test|live)_[A-Za-z0-9]{10,200}$/.test(id)) return reply({ ok: false, reason: "bad" }, 400);
  let s;
  try { s = await stripe(env, "GET", "/v1/checkout/sessions/" + id); }
  catch (e) { console.log(String(e)); return reply({ ok: false, reason: "unknown" }, 404); }
  if (s.payment_status !== "paid") return reply({ ok: false, reason: "unpaid" }, 402);
  const m = s.metadata || {};
  let token = "";
  for (let i = 0; m["t" + i]; i++) token += m["t" + i];
  const quest = questOf(await unseal(token, env));
  if (!quest) return reply({ ok: false, reason: "token" }, 500);
  return reply({ ok: true, quest, name: m.n || "", hero: m.h === "f" ? "f" : "m", kids: parseInt(m.k, 10) || 8, town: m.v || "" });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/api/")) {
      if (request.method !== "POST") return reply({ ok: false, reason: "method" }, 405);
      try {
        if (url.pathname === "/api/preview") return await preview(request, env);
        if (url.pathname === "/api/checkout") return await checkout(request, env);
        if (url.pathname === "/api/unlock") return await unlock(request, env);
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
