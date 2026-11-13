// The worker's address handling, without a network: node dev/test-worker.mjs (after dev/build.py).
// www and workers.dev send page visits to the main address (path and ?ref kept); the main address
// serves the files; the API answers on every address.
import assert from "node:assert";
import worker from "../dist/worker.js";

const env = { SITE_HOST: "maquetelegendaire.fr", ASSETS: { fetch: () => new Response("fichier") } };
const go = (url, init) => worker.fetch(new Request(url, init), env, { waitUntil() {} });

for (const from of ["https://www.maquetelegendaire.fr", "https://ma-quete-de-chevalier.pv6ggk8t2v.workers.dev"]) {
  const r = await go(from + "/anniversaire-chevalier.html?ref=diplome");
  assert.strictEqual(r.status, 301, from);
  assert.strictEqual(r.headers.get("location"), "https://maquetelegendaire.fr/anniversaire-chevalier.html?ref=diplome");
}
assert.strictEqual(await (await go("https://maquetelegendaire.fr/?ref=tiktok")).text(), "fichier", "main address serves the page");
const api = await go("https://ma-quete-de-chevalier.pv6ggk8t2v.workers.dev/api/nope", { method: "POST", body: "{}" });
assert.notStrictEqual(api.status, 301, "the API is never redirected");
const none = await go("https://ma-quete-de-chevalier.pv6ggk8t2v.workers.dev/", undefined);
assert.strictEqual(await (await worker.fetch(new Request("https://x.workers.dev/"), { ASSETS: env.ASSETS }, {})).text(), "fichier", "without SITE_HOST nothing is redirected");
assert.strictEqual(none.status, 301);
// short addresses for the videos and bios
for (const [path, ref] of [["/tiktok", "tiktok"], ["/TikTok/", "tiktok"], ["/insta", "instagram"], ["/pinterest", "pinterest"]]) {
  const r = await go("https://maquetelegendaire.fr" + path);
  assert.strictEqual(r.status, 302, path);
  assert.strictEqual(r.headers.get("location"), "https://maquetelegendaire.fr/?ref=" + ref, path);
}
const viaWww = await go("https://www.maquetelegendaire.fr/tiktok");
assert.strictEqual(viaWww.headers.get("location"), "https://maquetelegendaire.fr/tiktok", "www goes to the main address first");
console.log("Adresses du site : tous les tests passent.");

// The preview by e-mail and its one reminder (fake KV, fake Brevo and API Géo: no network, nothing sent).
{
  const kv = new Map();
  const STATS = {
    put: async (k, v, o = {}) => kv.set(k, { v: String(v), meta: o.metadata || null }),
    get: async k => kv.has(k) ? kv.get(k).v : null,
    delete: async k => { kv.delete(k); },
    list: async ({ prefix = "" } = {}) => ({ keys: [...kv.keys()].filter(k => k.startsWith(prefix)).sort().map(name => ({ name, metadata: kv.get(name).meta })), list_complete: true })
  };
  const sent = [];
  let commune = "<img src=x onerror=alert(1)>";
  const realFetch = globalThis.fetch;
  globalThis.fetch = async (u, init) => {
    u = String(u);
    if (u.startsWith("https://api.brevo.com/v3/smtp/email")) { sent.push({ headers: init.headers, body: JSON.parse(init.body) }); return new Response("{}", { status: 201 }); }
    if (u.startsWith("https://geo.api.gouv.fr/communes?")) return Response.json([{ nom: commune }]);
    throw new Error("unexpected fetch " + u);
  };
  const realNow = Date.now, realLog = console.log;
  console.log = () => {};   // the worker's one-line logs
  let days = 0;
  Date.now = () => realNow() + days * 86400000;
  const menv = Object.assign({}, env, { STATS, QUEST_KEY: "cle", BREVO_API_KEY: "xkeysib-unit", MAIL_FROM: "bonjour@maquetelegendaire.fr", MAIL_REPLY_TO: "contact@exemple.fr", PRICE_CENTS: "2490" });
  const call = async (path, body, e = menv) => {
    const r = await worker.fetch(new Request("https://maquetelegendaire.fr" + path, { method: "POST", body: JSON.stringify(body) }), e, { waitUntil() {} });
    return [r.status, await r.json()];
  };
  const [, home] = await call("/api/preview", { indoor: true });
  assert.ok(home.token, "preview token");

  assert.deepStrictEqual(await call("/api/rappel", { email: "a@exemple.fr", apercu: home.token }, Object.assign({}, menv, { BREVO_API_KEY: "" })), [503, { ok: false, reason: "off" }], "off without the key");
  for (const bad of ["", "a@b", "a@exemple", "a b@exemple.fr", "a@exemple.fr\r\nBcc: x@y.fr", "a..b@exemple.fr", ".a@exemple.fr", "a@-x.fr", "x".repeat(250) + "@ex.fr", "<a@exemple.fr>"])
    assert.strictEqual((await call("/api/rappel", { email: bad, apercu: home.token }))[1].reason, "email", "refused address: " + JSON.stringify(bad));
  const tampered = home.token.slice(0, -2) + (home.token.slice(-2) === "AA" ? "BB" : "AA");
  assert.strictEqual((await call("/api/rappel", { email: "a@exemple.fr", apercu: tampered }))[1].reason, "token", "tampered token refused");
  assert.strictEqual((await call("/api/rappel", { email: "a@exemple.fr", apercu: "pas-un-jeton-du-tout-0123456789" }))[1].reason, "token", "made-up token refused");
  assert.strictEqual(sent.length, 0, "nothing sent for refused requests");

  // the first name only from the list; the town from the API Géo, escaped; the link on the site's address
  assert.deepStrictEqual(await call("/api/rappel", { email: "Parent@Exemple.fr", apercu: home.token, n: "<b>x</b>", h: "f", k: 5, ref: "tiktok" }), [200, { ok: true }]);
  let m = sent.pop().body;
  assert.strictEqual(m.subject, "L'aperçu de votre quête d'anniversaire");
  assert.ok(!m.htmlContent.includes("<b>x</b>") && !m.textContent.includes("<b>x</b>"), "no typed text in the e-mail");
  assert.deepStrictEqual(m.to, [{ email: "parent@exemple.fr" }]);
  assert.strictEqual(m.sender.email, "bonjour@maquetelegendaire.fr");
  assert.strictEqual(m.replyTo.email, "contact@exemple.fr");
  assert.ok(m.textContent.includes("https://maquetelegendaire.fr/?apercu=" + home.token + "&n=&h=f&k=5&v=&ref=mail"), "the preview's link");
  assert.ok(/^<https:\/\/maquetelegendaire\.fr\/api\/rappel\/stop\?id=[0-9a-f]{16}\.[0-9a-f]{16}&s=[0-9a-f]{32}>$/.test(m.headers["List-Unsubscribe"]), "List-Unsubscribe");
  assert.ok(!/promo|NOEL/i.test(m.htmlContent + m.textContent), "no promotion code");
  assert.ok(m.textContent.includes("24,90 €"), "price from PRICE_CENTS");
  // a quest outdoors: its token holds the start point (the town is asked from the API Géo)
  const outdoor = await (async () => {
    const start = { lat: 48.5, lon: 7.47 }, d = (n, e) => ({ lat: start.lat + n / 111320, lon: start.lon + e / 73800 });
    const els = [["amenity", "place_of_worship", "Église Saint-Martin", 20, -150], ["amenity", "fountain", "Fontaine", -30, 60], ["historic", "city_gate", "Porte Haute", 0, 300],
      ["historic", "city_gate", "Porte Basse", 10, -420], ["leisure", "park", "Parc", -250, 100], ["historic", "memorial", "Monument", 150, 20]]
      .map(([k, v, name, n, e], i) => Object.assign({ type: "node", id: i + 1, tags: { [k]: v, name, religion: "christian" } }, d(n, e)));
    return (await call("/api/preview", { start, elements: els }))[1];
  })();
  assert.ok(outdoor.ok && outdoor.token, "outdoor preview");
  assert.strictEqual((await call("/api/rappel", { email: "b@exemple.fr", apercu: "https://maquetelegendaire.fr/?apercu=" + outdoor.token + "&n=x", n: "léo" }))[0], 200, "token given inside the link");
  m = sent.pop().body;
  assert.strictEqual(m.subject, "L'aperçu de la quête de Léo");
  assert.ok(m.htmlContent.includes("à &lt;img src=x onerror=alert(1)&gt;") && !m.htmlContent.includes("<img"), "the town is escaped");
  commune = "Le Havre";
  await call("/api/rappel", { email: "c@exemple.fr", apercu: outdoor.token, n: "Hugo" });
  m = sent.pop().body;
  assert.ok(m.subject === "L'aperçu de la quête pour Hugo" && m.textContent.includes("au Havre"), "elision: " + m.subject);
  // 3 requests per address per 24 hours
  for (let i = 0; i < 2; i++) assert.strictEqual((await call("/api/rappel", { email: "c@exemple.fr", apercu: outdoor.token }))[0], 200);
  assert.deepStrictEqual(await call("/api/rappel", { email: "c@exemple.fr", apercu: outdoor.token }), [429, { ok: false, reason: "limit" }], "4th request in 24 h");
  // the same mailbox under other spellings (+tag, Gmail's dots, googlemail) counts as one address
  for (const a of ["victime+1@gmail.com", "vic.time+2@gmail.com", "V.I.C.T.I.M.E@googlemail.com"])
    assert.strictEqual((await call("/api/rappel", { email: a, apercu: home.token }))[0], 200, a);
  assert.strictEqual((await call("/api/rappel", { email: "victime+4@gmail.com", apercu: home.token }))[0], 429, "aliases of one mailbox share its limit");
  assert.strictEqual((await call("/api/rappel", { email: "x+1@exemple.fr", apercu: home.token }))[0], 200);
  assert.strictEqual(sent.pop().body.to[0].email, "x+1@exemple.fr", "the e-mail goes to the address as typed");
  for (const k of [...kv.keys()]) if (k.startsWith("rappel:") && /gmail\.com|googlemail|x\+1@/.test(kv.get(k).v)) kv.delete(k);   // keep the counts below simple
  // Brevo's error message never puts an address in the logs
  {
    const logs = [], keep = globalThis.fetch;
    console.log = s => logs.push(String(s));
    globalThis.fetch = async (u, init) => String(u).includes("brevo") ? Response.json({ code: "invalid_parameter", message: "Invalid email address journal@exemple.fr" }, { status: 400 }) : keep(u, init);
    assert.strictEqual((await call("/api/rappel", { email: "journal@exemple.fr", apercu: home.token }))[0], 502);
    globalThis.fetch = keep; console.log = () => {};
    assert.ok(logs.some(l => l.startsWith("brevo 400") && l.includes("<adresse>")) && !logs.some(l => l.includes("journal@")), "no address in the logs: " + logs.join(" | "));
  }
  sent.length = 0;

  // the reminder: not before 7 days, once at 7 days, then the request is gone
  const records = () => [...kv.keys()].filter(k => k.startsWith("rappel:"));
  const before = records().length;
  assert.strictEqual(before, 3, "one record per address and token");
  days = 6.9; await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(sent.length, 0, "no reminder before 7 days");
  days = 7.01; await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(sent.length, 3, "one reminder each at 7 days");
  assert.ok(sent.every(x => / vous attend$/.test(x.body.subject) && x.body.textContent.includes("C'est le seul rappel que vous recevrez")), "reminder text");
  assert.ok(sent.some(x => x.body.textContent.includes("S'il pleut")) && sent.some(x => !x.body.textContent.includes("S'il pleut")), "rain line only outdoors");
  assert.strictEqual(records().length, 0, "records deleted after the reminder");
  await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(sent.length, 3, "never twice");

  // unsubscribe: signed link only
  days = 0; sent.length = 0;
  await call("/api/rappel", { email: "d@exemple.fr", apercu: home.token });
  const stop = sent.pop().body.headers["List-Unsubscribe"].slice(1, -1);
  const get = async u => { const r = await worker.fetch(new Request(u), menv, { waitUntil() {} }); return [r.status, await r.text()]; };
  assert.strictEqual((await get(stop.replace(/s=([0-9a-f])/, (x, c) => "s=" + (c === "0" ? "1" : "0"))))[0], 403, "wrong signature refused");
  assert.strictEqual(records().length, 1);
  const [st, page] = await get(stop);
  assert.ok(st === 200 && page.includes("C'est noté : vous ne recevrez pas de rappel."), "unsubscribed");
  assert.strictEqual(records().length, 0);
  assert.strictEqual((await get(stop))[0], 200, "works when already gone");

  // Brevo refuses (4xx): kept for one more try; no answer: never sent twice
  sent.length = 0;
  await call("/api/rappel", { email: "e@exemple.fr", apercu: home.token });
  sent.length = 0;
  globalThis.fetch = async u => { if (String(u).includes("brevo")) return new Response("{}", { status: 400 }); return Response.json([]); };
  days = 7.1; await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(records().length, 1, "refused: kept");
  assert.deepStrictEqual(Object.keys(kv.get(records()[0]).meta).sort(), ["c", "n", "x"], "refused: not marked as being sent");
  globalThis.fetch = async u => { if (String(u).includes("brevo")) throw new TypeError("network"); return Response.json([]); };
  days = 8.1; await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(kv.get(records()[0]).meta.p, 1, "no answer: marked");
  globalThis.fetch = async (u, init) => { if (String(u).includes("brevo")) { sent.push(1); return new Response("{}", { status: 201 }); } return Response.json([]); };
  days = 9.1; await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.ok(records().length === 0 && sent.length === 0, "marked: deleted without a second send");
  // at most 30 reminders a run: the rest the next day, each once
  days = 0; sent.length = 0;
  for (let i = 0; i < 32; i++) await call("/api/rappel", { email: `n${i}@exemple.fr`, apercu: home.token });
  sent.length = 0;
  days = 7.2; await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(sent.length, 30, "30 reminders in the first run");
  days = 8.2; await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.ok(sent.length === 32 && records().length === 0, "the 2 others the next day");

  // paid, but the page never came back from Stripe (no /api/unlock): Stripe is read (read only) before the reminder
  {
    const senv = Object.assign({}, menv, { STRIPE_SECRET_KEY: "sk_test_unit", STRIPE_API: "https://stripe.test" });
    const chunks = t => { const m = {}; for (let i = 0; i * 490 < t.length; i++) m["t" + i] = t.slice(i * 490, (i + 1) * 490); return m; };
    let stripeState = "up", stripeCalls = [];
    const sessions = () => [
      { id: "cs_test_open", status: "open", payment_status: "unpaid", created: Math.floor(Date.now() / 1000) - 3600, metadata: chunks(home.token) },
      { id: "cs_test_paid", status: "complete", payment_status: "paid", created: Math.floor(Date.now() / 1000) - 6 * 86400, metadata: chunks(outdoor.token) }];
    globalThis.fetch = async (u, init) => {
      u = String(u);
      if (u.startsWith("https://stripe.test/")) {
        stripeCalls.push({ u, method: (init && init.method) || "GET", auth: new Headers(init && init.headers).get("authorization") });
        if (stripeState === "down") return Response.json({ error: { message: "down" } }, { status: 500 });
        return Response.json({ data: sessions(), has_more: false });
      }
      if (u.startsWith("https://api.brevo.com/")) { sent.push({ body: JSON.parse(init.body) }); return new Response("{}", { status: 201 }); }
      if (u.startsWith("https://geo.api.gouv.fr/")) return Response.json([{ nom: "Obernai" }]);
      throw new Error("unexpected fetch " + u);
    };
    days = 0; sent.length = 0;
    await call("/api/rappel", { email: "paye@exemple.fr", apercu: outdoor.token }, senv);   // will pay, never come back
    await call("/api/rappel", { email: "paspaye@exemple.fr", apercu: home.token }, senv);   // checkout opened, not paid
    sent.length = 0;
    days = 7.1; stripeState = "down";
    await worker.scheduled({ scheduledTime: Date.now() }, senv, { waitUntil() {} });
    assert.ok(sent.length === 0 && records().length === 2, "Stripe does not answer: no reminder this run, requests kept");
    assert.strictEqual(stripeCalls.length, 1, "one Stripe call, then the run stops");
    assert.ok(records().every(k => !kv.get(k).meta.p), "Stripe down: nothing marked as being sent");
    days = 8.1; stripeState = "up"; stripeCalls = [];
    await worker.scheduled({ scheduledTime: Date.now() }, senv, { waitUntil() {} });
    assert.strictEqual(sent.length, 1, "only the unpaid quest gets its reminder");
    assert.deepStrictEqual(sent[0].body.to, [{ email: "paspaye@exemple.fr" }]);
    assert.strictEqual(records().length, 0, "the paid quest's request is deleted without a reminder");
    assert.ok(stripeCalls.length === 1 && stripeCalls.every(c => c.method === "GET" && c.auth === "Bearer sk_test_unit" && /\/v1\/checkout\/sessions\?status=complete&limit=100$/.test(c.u)),
      "Stripe read once, read only: " + JSON.stringify(stripeCalls));
    // nothing due: Stripe is not called at all
    stripeCalls = [];
    await call("/api/rappel", { email: "tot@exemple.fr", apercu: home.token }, senv);
    await worker.scheduled({ scheduledTime: Date.now() }, senv, { waitUntil() {} });
    assert.strictEqual(stripeCalls.length, 0, "no reminder due: no call to Stripe");
    kv.clear(); sent.length = 0;
  }
  globalThis.fetch = realFetch; Date.now = realNow; console.log = realLog;
}
console.log("Aperçu par e-mail : tous les tests passent.");
