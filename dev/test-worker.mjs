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
  const allLogs = [], quiet = s => allLogs.push(String(s));
  console.log = quiet;   // the worker's one-line logs, kept to check that none holds an address
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
  assert.ok(m.htmlContent.includes("à &lt;img src=x onerror=alert(1)&gt;") && !m.htmlContent.includes("<img src=x"), "the town is escaped");
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
    console.log = s => { logs.push(String(s)); quiet(s); };
    globalThis.fetch = async (u, init) => String(u).includes("brevo") ? Response.json({ code: "invalid_parameter", message: "Invalid email address journal@exemple.fr" }, { status: 400 }) : keep(u, init);
    assert.strictEqual((await call("/api/rappel", { email: "journal@exemple.fr", apercu: home.token }))[0], 502);
    globalThis.fetch = keep; console.log = quiet;
    assert.ok(logs.some(l => l.startsWith("brevo 400") && l.includes("<adresse>")) && !logs.some(l => l.includes("journal@")), "no address in the logs: " + logs.join(" | "));
    // refused by Brevo: the request is kept, marked as failed with Brevo's answer (without the address quoted in it)
    const k = [...kv.keys()].find(x => x.startsWith("rappel:") && JSON.parse(kv.get(x).v).email === "journal@exemple.fr");
    const r = k && JSON.parse(kv.get(k).v);
    assert.ok(r && r.st === "echec" && r.err.status === 400 && r.err.code === "invalid_parameter" && r.err.message === "Invalid email address <adresse>", "failed send kept: " + JSON.stringify(r && r.err));
    assert.deepStrictEqual(Object.keys(kv.get(k).meta).sort(), ["c", "n", "x"], "failed send: the reminder stays planned");
  }
  sent.length = 0;

  // the reminder: not before 7 days, once at 7 days, then the request is gone
  const records = () => [...kv.keys()].filter(k => k.startsWith("rappel:"));
  const before = records().length;
  assert.strictEqual(before, 4, "one record per address and token (the failed one too)");
  days = 6.9; await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(sent.length, 0, "no reminder before 7 days");
  days = 7.01; await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(sent.length, 4, "one reminder each at 7 days");
  const late = sent.filter(x => x.body.to[0].email === "journal@exemple.fr");
  assert.ok(late.length === 1 && late[0].body.subject === "L'aperçu de votre quête d'anniversaire" && late[0].body.textContent.includes("notre envoi n'avait pas pu partir")
    && late[0].body.textContent.includes("C'est le seul message que vous recevrez") && !late[0].body.textContent.includes("seul rappel") && !late[0].body.textContent.includes("pour ne pas recevoir le rappel") && late[0].body.textContent.includes("?apercu=" + home.token),
    "the first e-mail never went: the 7th day's e-mail says so, with the link");
  sent.splice(sent.indexOf(late[0]), 1);
  assert.ok(sent.every(x => / vous attend$/.test(x.body.subject) && x.body.textContent.includes("Nous vous écrirons une dernière fois dans trois semaines")
    && x.body.textContent.includes("Pour ne pas recevoir le dernier rappel") && !x.body.textContent.includes("seul rappel")), "reminder text (requests since 25/11: one more a month after)");
  assert.ok(sent.every(x => x.body.tags[0] === "rappel") && late[0].body.tags[0] === "apercu", "Brevo tags");
  sent.push(late[0]);
  assert.ok(sent.some(x => x.body.textContent.includes("S'il pleut")) && sent.some(x => !x.body.textContent.includes("S'il pleut")), "rain line only outdoors");
  assert.strictEqual(records().length, 0, "records deleted after the reminder");
  await worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(sent.length, 4, "never twice");

  // the last reminder, 30 days after the request (requests since 25/11/2026), not after the late preview (kind 3)
  const months = () => [...kv.keys()].filter(k => k.startsWith("rappel2:"));
  const cron = () => worker.scheduled({ scheduledTime: Date.now() }, menv, { waitUntil() {} });
  assert.strictEqual(months().length, 3, "kept for the month: the 3 reminded, not the late preview");
  assert.ok(months().every(k => JSON.parse(kv.get(k).v).r === 1 && JSON.parse(kv.get(k).v).v === 2 && Object.keys(kv.get(k).meta).sort().join() === "c,n,x"), "month record");
  sent.length = 0;
  days = 29.9; await cron();
  assert.strictEqual(sent.length, 0, "no last reminder before 30 days");
  days = 30.01; await cron();
  assert.strictEqual(sent.length, 3, "the last reminder at 30 days, one each");
  assert.ok(sent.every(x => / est toujours prête$/.test(x.body.subject) && x.body.tags[0] === "rappel-mois" && x.body.textContent.includes("Il y a un mois")
    && x.body.textContent.includes("C'est notre dernier message") && x.body.textContent.includes("Rien d'autre ne vous sera envoyé")
    && x.body.htmlContent.includes("Un mois plus tard") && !x.body.htmlContent.includes("L&#39;aperçu de la quête") && !/promo|NOEL/i.test(x.body.textContent)), "last reminder: text");
  assert.ok(sent.every(x => /^<https:\/\/maquetelegendaire\.fr\/api\/rappel\/stop\?id=[0-9a-f]{16}\.[0-9a-f]{16}&s=[0-9a-f]{32}>$/.test(x.body.headers["List-Unsubscribe"])), "last reminder: unsubscribe link");
  assert.ok(sent.some(x => x.body.subject === "La quête de Léo est toujours prête") && sent.some(x => x.body.subject === "Votre quête d'anniversaire est toujours prête"), "last reminder: subjects");
  assert.strictEqual(months().length, 0, "deleted after the last reminder");
  await cron();
  assert.strictEqual(sent.length, 3, "the last reminder never twice");
  // a request made before 25/11/2026 (no "v"): one reminder only, as it was promised, with its old text
  days = 0; sent.length = 0;
  await call("/api/rappel", { email: "ancien@exemple.fr", apercu: home.token });
  assert.ok(sent[0].body.textContent.includes("Nous vous écrirons au plus deux autres fois, dans une semaine puis un mois après votre demande")
    && sent[0].body.textContent.includes("Pour ne pas recevoir les rappels"), "first e-mail: announces the two reminders");
  { const e = kv.get(records()[0]), r = JSON.parse(e.v); delete r.v; e.v = JSON.stringify(r); }
  days = 7.01; await cron();
  assert.ok(sent.length === 2 && sent[1].body.textContent.includes("C'est le seul rappel que vous recevrez") && sent[1].body.textContent.includes("Rien d'autre ne vous sera envoyé"), "old request: its one reminder, as promised");
  assert.ok(records().length === 0 && months().length === 0, "old request: nothing kept for the month");
  // unsubscribe and payment after the 7th day: no last reminder
  days = 0; sent.length = 0;
  await call("/api/rappel", { email: "stopmois@exemple.fr", apercu: home.token });
  await call("/api/rappel", { email: "payemois@exemple.fr", apercu: outdoor.token });
  const stopMois = sent[0].body.headers["List-Unsubscribe"].slice(1, -1);
  days = 7.01; await cron();
  assert.strictEqual(months().length, 2, "both kept for the month");
  const resend = sent.find(x => x.body.to[0].email === "stopmois@exemple.fr");
  assert.strictEqual(resend.body.headers["List-Unsubscribe"].slice(1, -1), stopMois, "the same unsubscribe link in every e-mail");
  const r1 = await worker.fetch(new Request(stopMois), menv, { waitUntil() {} });
  assert.ok(r1.status === 200 && months().length === 1, "unsubscribe after the 7th day: the month's record deleted");
  kv.set("rappel-paye:" + months()[0].slice("rappel2:".length).split(".")[0], { v: "1", meta: null });
  sent.length = 0;
  days = 30.2; await cron();
  assert.ok(sent.length === 0 && months().length === 0, "paid (or unsubscribed) after the 7th day: no last reminder");
  for (const k of [...kv.keys()]) if (k.startsWith("rappel-paye:")) kv.delete(k);
  // the cron late by more than 10 days: the request has expired, nothing goes (and nothing is kept for the month)
  days = 0; sent.length = 0;
  await call("/api/rappel", { email: "tard@exemple.fr", apercu: home.token });
  days = 10.5; await cron();
  assert.ok(sent.length === 1 && records().length === 0 && months().length === 0, "expired request: no reminder, nothing kept");
  days = 0; sent.length = 0;

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

  // The owner's private page: the e-mails crossed with Brevo's log, and « Renvoyer l'aperçu »
  {
    const { createHash } = await import("node:crypto");
    const eenv = Object.assign({}, menv, { ESPACE_ID: "test", ESPACE_SALT: "sel", ESPACE_HASH: createHash("sha256").update("sel:test:TEST-CODE-0000-0000").digest("hex"),
      STRIPE_SECRET_KEY: "sk_test_unit", STRIPE_API: "https://stripe.test", MAIL_DAY_MAX: "200" });
    const login = { id: "test", code: "TEST-CODE-0000-0000" };
    const blog = [];   // what fake Brevo took: { mid, body, at, events: [[event, reason]] }
    let brevoSend = "ok", brevoLog = "up", logCalls = 0, paidSessions = [], stripeExpand = "ok";
    const chunks = t => { const m = {}; for (let i = 0; i * 490 < t.length; i++) m["t" + i] = t.slice(i * 490, (i + 1) * 490); return m; };
    globalThis.fetch = async (u, init) => {
      u = String(u);
      if (u === "https://api.brevo.com/v3/smtp/email") {
        const b = JSON.parse(init.body);
        if (brevoSend === "refuse") return Response.json({ code: "permission_denied", message: "Sender not allowed to send to " + b.to[0].email }, { status: 403 });
        const mid = `<m${blog.length + 1}@relay.test>`;
        blog.push({ mid, body: b, at: Date.now(), events: [] }); sent.push({ body: b });
        return Response.json({ messageId: mid }, { status: 201 });
      }
      if (u.startsWith("https://api.brevo.com/v3/smtp/statistics/events?")) {
        logCalls++;
        assert.strictEqual(new Headers(init.headers).get("api-key"), "xkeysib-unit", "Brevo's log: the server's key");
        if (brevoLog === "down") return Response.json({ code: "unavailable", message: "down" }, { status: 503 });
        if (brevoLog === "net") throw new TypeError("fetch failed");
        if (brevoLog === "format") return Response.json({ events: "nope" });
        const q = new URL(u).searchParams;
        assert.ok(+q.get("limit") <= 100 && q.get("days") === "35" && q.get("sort") === "desc", "Brevo's log: query " + u);
        const ev = blog.flatMap(m => [{ email: m.body.to[0].email, date: new Date(m.at).toISOString(), subject: m.body.subject, messageId: m.mid, event: "requests", tag: m.body.tags[0], from: "x" },
          ...m.events.map(([event, reason], i) => Object.assign({ email: m.body.to[0].email, date: new Date(m.at + 1000 * (i + 1)).toISOString(), messageId: m.mid, event }, reason ? { reason } : {}))]).reverse();
        return Response.json({ events: ev.slice(+q.get("offset"), +q.get("offset") + +q.get("limit")) });
      }
      if (u.startsWith("https://stripe.test/v1/checkout/sessions/")) return Response.json(paidSessions.find(s => u.endsWith(s.id)) || {}, { status: paidSessions.some(s => u.endsWith(s.id)) ? 200 : 404 });
      if (u.startsWith("https://stripe.test/v1/checkout/sessions?")) {
        const q = new URL(u).searchParams;
        if (q.getAll("expand[]").length && stripeExpand === "refuse") return Response.json({ error: { message: "This property cannot be expanded" } }, { status: 400 });
        if (stripeExpand === "down") return Response.json({ error: { message: "down" } }, { status: 500 });
        // not unfolded: the payment is only its id, as Stripe gives it
        const unfold = q.getAll("expand[]").includes("data.payment_intent.latest_charge");
        return Response.json({ data: paidSessions.map(x => unfold ? x : Object.assign({}, x, { payment_intent: x.payment_intent ? "pi_test_1" : null })), has_more: false });
      }
      if (u.startsWith("https://stripe.test/")) return Response.json({ data: paidSessions, has_more: false });
      if (u.startsWith("https://geo.api.gouv.fr/")) return Response.json([{ nom: "Obernai" }]);
      throw new Error("unexpected fetch " + u);
    };
    const status = (to, event, reason) => blog.filter(m => m.body.to[0].email === to).forEach(m => m.events.push([event, reason]));
    const mails = async () => { const [st, j] = await call("/api/espace/mails", login, eenv); assert.strictEqual(st, 200); return j; };
    const ridOf = (j, email) => (j.demandes.find(d => d.email === email) || {}).rid;
    days = 0; sent.length = 0;
    const tok = {};
    for (const who of ["livre", "rebond", "bloque", "bizarre", "refus", "refus2", "paye", "parti", "stop", "plainte"]) {
      tok[who] = (await call("/api/preview", { indoor: true }))[1].token;
      brevoSend = who.startsWith("refus") ? "refuse" : "ok";
      const [st] = await call("/api/rappel", { email: who + "@exemple.fr", apercu: tok[who], n: "Léo" }, eenv);
      assert.strictEqual(st, who.startsWith("refus") ? 502 : 200, "request " + who);
    }
    brevoSend = "ok";
    status("livre@exemple.fr", "delivered"); status("livre@exemple.fr", "opened");
    status("rebond@exemple.fr", "hardBounces", "550 5.1.1 <rebond@exemple.fr>: user unknown");
    status("bloque@exemple.fr", "blocked", "sender domain not authenticated");
    status("bizarre@exemple.fr", "superNewEvent", "something");
    status("plainte@exemple.fr", "delivered"); status("plainte@exemple.fr", "spam");
    const first = Object.fromEntries(blog.map(m => [m.body.to[0].email, m.body]));

    // no login, a wrong code, another login: 403, nothing else (the same check as /api/espace)
    for (const bad of [{}, { id: "test" }, { id: "test", code: "TEST-CODE-0000-0001" }, { id: "autre", code: "TEST-CODE-0000-0000" }, { id: "test", code: "" }])
      for (const path of ["/api/espace/mails", "/api/espace/renvoi"]) {
        const t0 = performance.now();
        const [st, j] = await call(path, Object.assign({ email: "livre@exemple.fr", rid: "0".repeat(16) + "." + "0".repeat(16) }, bad), eenv);
        assert.deepStrictEqual([st, j], [403, { ok: false, reason: "login" }], path + " " + JSON.stringify(bad));
        assert.ok(performance.now() - t0 >= 390, "the same 400 ms delay on a failed login");
      }
    assert.ok(logCalls === 0 && blog.length === 8, "refused logins: Brevo neither read nor used");
    assert.strictEqual((await call("/api/espace/mails", { id: " TEST ", code: "test-code-0000-0000 " }, eenv))[0], 200, "the same login rules (case, spaces)");

    // the list: the requests kept here, Brevo's messages with their last state, crossed
    let j = await mails();
    assert.ok(j.ok && j.on && j.brevo.ok && j.renvoiMax === 3, "list: " + JSON.stringify(j.brevo).slice(0, 200));
    const d = Object.fromEntries(j.demandes.map(x => [x.email.split("@")[0], x]));
    assert.deepStrictEqual(Object.keys(d).sort(), ["bizarre", "bloque", "livre", "parti", "paye", "rebond", "refus", "refus2", "stop"], "requests (the spam complaint is forgotten)");
    assert.ok(d.refus.st === "echec" && d.refus.err.status === 403 && d.refus.err.code === "permission_denied" && !d.refus.err.message.includes("@"), "failed send: visible, Brevo's reason without the address");
    assert.ok(d.livre.st === "envoye" && d.livre.livraison === "delivre" && d.livre.name === "Léo" && d.livre.rappelLe - d.livre.created === 7 * 86400000, "request: delivered, reminder date");
    const msg = Object.fromEntries(j.brevo.messages.map(m => [m.email.split("@")[0], m]));
    assert.deepStrictEqual(Object.keys(msg).sort(), ["bizarre", "bloque", "livre", "parti", "paye", "plainte", "rebond", "stop"], "Brevo's messages (none for the refused sends)");
    assert.ok(msg.livre.state === "delivre" && msg.livre.opened && !msg.livre.erreur && msg.livre.rid === d.livre.rid, "delivered and opened");
    assert.ok(msg.rebond.state === "rebond-definitif" && msg.rebond.erreur && msg.rebond.reason.includes("user unknown") && msg.rebond.rid === d.rebond.rid, "hard bounce, with Brevo's reason");
    assert.ok(msg.bloque.state === "bloque" && msg.bloque.erreur && msg.bloque.reason === "sender domain not authenticated", "blocked");
    assert.ok(msg.bizarre.state === "parti" && msg.bizarre.events.some(e => e.e === "autre" && e.raw === "superNewEvent"), "an unknown event is kept as is");
    assert.ok(msg.plainte.state === "spam" && msg.plainte.rid === "" && !kv.has("rappel:" + msg.plainte.rid), "spam complaint: no resend possible");
    assert.ok(msg.parti.state === "parti" && msg.parti.subject === "L'aperçu de la quête de Léo" && msg.parti.tag === "apercu", "sent, waiting");

    // « Renvoyer l'aperçu »: the same e-mail n°1 (template, link, unsubscribe), the reminder's date unchanged
    const recOf = rid => ({ rec: JSON.parse(kv.get("rappel:" + rid).v), meta: kv.get("rappel:" + rid).meta });
    const before = recOf(d.rebond.rid);
    sent.length = 0; days = 1;
    let [st, r] = await call("/api/espace/renvoi", Object.assign({ rid: d.rebond.rid }, login), eenv);
    assert.ok(st === 200 && r.ok && r.to === "rebond@exemple.fr" && r.renvoisJour === 1, "resend: " + JSON.stringify(r));
    assert.strictEqual(sent.length, 1);
    for (const f of ["subject", "htmlContent", "textContent", "headers", "to", "sender", "replyTo", "tags"]) assert.deepStrictEqual(sent[0].body[f], first["rebond@exemple.fr"][f], "resend: the same " + f);
    const after = recOf(d.rebond.rid);
    assert.deepStrictEqual(after.meta, before.meta, "resend: the reminder's date and expiration unchanged");
    assert.ok(after.rec.renvois.length === 1 && after.rec.last.ok === true && after.rec.mids.length === 2 && after.rec.created === before.rec.created, "resend: kept on the request");
    for (let i = 0; i < 2; i++) assert.strictEqual((await call("/api/espace/renvoi", Object.assign({ rid: d.rebond.rid }, login), eenv))[0], 200);
    [st, r] = await call("/api/espace/renvoi", Object.assign({ rid: d.rebond.rid }, login), eenv);
    assert.ok(st === 429 && r.reason === "limit" && sent.length === 3, "a 4th resend in 24 hours: refused, nothing sent");
    j = await mails();
    assert.ok(j.demandes.find(x => x.rid === d.rebond.rid).renvoisJour === 3, "the count shown");

    // the failed first send: sent again from here; the request is then an ordinary one
    [st, r] = await call("/api/espace/renvoi", Object.assign({ rid: d.refus.rid }, login), eenv);
    assert.ok(st === 200 && recOf(d.refus.rid).rec.st === "envoye", "failed send, resent");
    // Brevo refuses the resend: said with its reason, the request stays as it was
    brevoSend = "refuse";
    [st, r] = await call("/api/espace/renvoi", Object.assign({ rid: d.bloque.rid }, login), eenv);
    assert.ok(st === 502 && r.reason === "send" && /code 403/.test(r.message) && recOf(d.bloque.rid).rec.last.ok === false, "resend refused by Brevo: " + r.message);
    brevoSend = "ok";

    // the request deleted while the resend is going out (the parent unsubscribes, or the cron sends its reminder):
    // it is not written back, so no reminder after an unsubscribe and never a second reminder
    for (const [who, meanwhile] of [["course-stop", async (rid, stopUrl) => { await worker.fetch(new Request(stopUrl), eenv, { waitUntil() {} }); }],
      ["course-rappel", async rid => { const e = kv.get("rappel:" + rid); kv.set("rappel:" + rid, { v: e.v, meta: Object.assign({}, e.meta, { p: 1 }) }); }]]) {
      sent.length = 0;
      assert.strictEqual((await call("/api/rappel", { email: who + "@exemple.fr", apercu: (await call("/api/preview", { indoor: true }))[1].token }, eenv))[0], 200);
      const stopUrl = sent[0].body.headers["List-Unsubscribe"].slice(1, -1), rid = new URL(stopUrl).searchParams.get("id");
      const keepFetch = globalThis.fetch;
      globalThis.fetch = async (u, init) => { if (String(u) === "https://api.brevo.com/v3/smtp/email") await meanwhile(rid, stopUrl); return keepFetch(u, init); };
      [st, r] = await call("/api/espace/renvoi", Object.assign({ rid }, login), eenv);
      globalThis.fetch = keepFetch;
      assert.ok(st === 200 && r.ok, who + ": the resend went");
      if (who === "course-stop") assert.ok(!kv.has("rappel:" + rid), "unsubscribed during the resend: the request is not brought back");
      else assert.strictEqual(kv.get("rappel:" + rid).meta.p, 1, "reminder going out during the resend: its mark is kept");
    }

    // by address: the requests of the mailbox (aliases too), sent to the address the parent gave; none: nothing sent
    sent.length = 0;
    [st, r] = await call("/api/espace/renvoi", Object.assign({ email: " Livre+autre@Exemple.fr " }, login), eenv);
    assert.ok(st === 200 && r.to === "livre@exemple.fr" && sent.length === 1 && sent[0].body.to[0].email === "livre@exemple.fr", "by address (alias): to the requested address");
    [st, r] = await call("/api/espace/renvoi", Object.assign({ email: "inconnu@exemple.fr" }, login), eenv);
    assert.ok(st === 404 && r.reason === "introuvable" && sent.length === 1, "an address that asked nothing: nothing sent");
    assert.strictEqual((await call("/api/espace/renvoi", Object.assign({ email: "pas une adresse" }, login), eenv))[1].reason, "email");
    await call("/api/rappel", { email: "livre@exemple.fr", apercu: tok.bizarre }, eenv);
    sent.length = 0;
    [st, r] = await call("/api/espace/renvoi", Object.assign({ email: "livre@exemple.fr" }, login), eenv);
    assert.ok(st === 409 && r.reason === "plusieurs" && r.demandes.length === 2 && sent.length === 0, "two requests: the owner chooses");

    // gone: paid (back on the site, or not), unsubscribed, a made-up request: « introuvable », nothing sent
    paidSessions = [{ id: "cs_test_" + "x".repeat(20), status: "complete", payment_status: "paid", created: Math.floor(Date.now() / 1000), metadata: Object.assign(chunks(tok.paye), { n: "Léo" }) }];
    assert.strictEqual((await call("/api/unlock", { session: paidSessions[0].id }, eenv)).at(0), 200);
    await new Promise(ok => setTimeout(ok, 20));
    paidSessions.push({ id: "cs_test_" + "y".repeat(20), status: "complete", payment_status: "paid", created: Math.floor(Date.now() / 1000), metadata: chunks(tok.parti) });
    await worker.fetch(new Request(first["stop@exemple.fr"].headers["List-Unsubscribe"].slice(1, -1)), eenv, { waitUntil() {} });
    for (const who of ["paye", "parti", "stop"]) {
      [st, r] = await call("/api/espace/renvoi", Object.assign({ rid: d[who].rid }, login), eenv);
      assert.ok(st === 404 && r.reason === "introuvable" && r.message.startsWith("Demande introuvable : le parent a payé, s'est désinscrit"), who + ": " + JSON.stringify(r));
      assert.ok(!kv.has("rappel:" + d[who].rid), who + ": the request is gone");
    }
    assert.strictEqual((await call("/api/espace/renvoi", Object.assign({ rid: "1".repeat(16) + "." + "2".repeat(16) }, login), eenv))[0], 404);
    assert.strictEqual(sent.length, 0, "nothing sent to a request that is gone");

    // the sales (Stripe): the paid ones with their buyer and the quest; the others without any address
    Object.assign(paidSessions[0], { amount_total: 2241, total_details: { amount_discount: 249 }, customer_details: { email: "acheteur@exemple.fr", name: "Marie Martin" },
      payment_intent: { latest_charge: { refunded: false, amount_refunded: 0 } } });
    paidSessions[1].payment_intent = { latest_charge: { refunded: true, amount_refunded: 2490 } };
    paidSessions.push({ id: "cs_test_" + "z".repeat(20), status: "expired", payment_status: "unpaid", created: Math.floor(Date.now() / 1000) - 3600,
      customer_details: { email: "pas-paye@exemple.fr", name: "Pas Payé" }, metadata: Object.assign(chunks(tok.bizarre), { n: "Emma", v: "Obernai", k: "6", ref: "instagram" }) });
    [st, r] = await call("/api/espace/ventes", Object.assign({ days: 30 }, login), eenv);
    assert.ok(st === 200 && r.on && r.ventes.length === 3 && r.remboursements === true && !r.live, "sales: " + JSON.stringify(r).slice(0, 300));
    const v0 = r.ventes[0], v1 = r.ventes[1], vx = r.ventes[2];
    assert.ok(v0.paid && v0.email === "acheteur@exemple.fr" && v0.buyer === "Marie Martin" && v0.child === "Léo" && v0.amount === 2241 && v0.discount === 249
      && v0.steps > 0 && v0.refund === "" && v0.at > 0, "a sale: its buyer and its quest " + JSON.stringify(v0));
    assert.strictEqual(v1.refund, "total", "a refunded sale");
    assert.ok(!vx.paid && vx.email === "" && vx.buyer === "" && vx.amount === null && vx.child === "Emma" && vx.town === "Obernai" && vx.kids === 6 && vx.ref === "instagram",
      "an unpaid payment page: what was chosen, never an address " + JSON.stringify(vx));
    assert.ok(!JSON.stringify(r).includes("pas-paye@") && !JSON.stringify(r).includes("t0"), "no address of an unpaid page, no token");
    stripeExpand = "refuse";
    [st, r] = await call("/api/espace/ventes", login, eenv);
    assert.ok(st === 200 && r.ventes.length === 3 && r.remboursements === false && r.ventes[0].refund === null, "Stripe refuses to unfold the payments: the list still comes");
    stripeExpand = "down";
    [st, r] = await call("/api/espace/ventes", login, eenv);
    assert.ok(st === 200 && r.on && r.ventes.length === 0 && /^Stripe 500/.test(r.error), "Stripe down: said, " + JSON.stringify(r));
    stripeExpand = "ok";
    assert.strictEqual((await call("/api/espace/ventes", { id: "test", code: "FAUX" }, eenv))[0], 403, "sales: the login is checked");
    [st, r] = await call("/api/espace/ventes", login, Object.assign({}, eenv, { STRIPE_SECRET_KEY: "" }));
    assert.ok(st === 200 && r.on === false, "sales: no Stripe key");
    paidSessions = [];

    // the hour of each count (UTC, in the key's metadata), returned for the last 8 days; "?" for the older counts
    const today = new Date().toISOString().slice(0, 10), hNow = String(new Date().getUTCHours());
    assert.strictEqual((await worker.fetch(new Request("https://maquetelegendaire.fr/api/hit", { method: "POST", body: JSON.stringify({ e: "diploma", ref: "instagram" }) }), eenv, { waitUntil() {} })).status, 204);
    await new Promise(ok => setTimeout(ok, 20));
    kv.set(today + "|diploma|flyer|ancien00", { v: "1", meta: null });
    [st, r] = await call("/api/espace", Object.assign({ days: 28 }, login), eenv);
    assert.ok(st === 200 && r.hours && r.hours[today] && r.hours[today][hNow].diploma.instagram === 1 && r.hours[today]["?"].diploma.flyer === 1
      && r.days[today].diploma.instagram === 1 && Object.keys(r.hours).length === 8, "hours: " + JSON.stringify(r.hours && r.hours[today]));
    kv.delete(today + "|diploma|flyer|ancien00");

    // the cap of the day applies to the resends too
    const dayKey = "rappel-jour:" + new Date(Date.now()).toISOString().slice(0, 10), keepDay = kv.get(dayKey);
    kv.set(dayKey, { v: "200", meta: null });
    [st, r] = await call("/api/espace/renvoi", Object.assign({ rid: d.bizarre.rid }, login), eenv);
    assert.ok(st === 503 && r.reason === "full" && sent.length === 0, "cap of the day");
    if (keepDay) kv.set(dayKey, keepDay); else kv.delete(dayKey);

    // Brevo's log down, unreadable, or no answer: said, the rest of the section still there
    for (const [state, check] of [["down", b => b.status === 503], ["net", b => b.status === 0], ["format", b => b.format === true]]) {
      brevoLog = state;
      j = await mails();
      assert.ok(j.ok && !j.brevo.ok && check(j.brevo) && j.demandes.length >= 5, "Brevo's log " + state + ": " + JSON.stringify(j.brevo));
    }
    brevoLog = "up";
    assert.deepStrictEqual(await call("/api/espace/mails", login, Object.assign({}, eenv, { BREVO_API_KEY: "" })), [200, { ok: true, on: false }], "e-mails off: said");

    // the 7th day: one e-mail each; the failed first send never resent gets the late preview, once
    sent.length = 0;
    days = 6.9; await worker.scheduled({ scheduledTime: Date.now() }, eenv, { waitUntil() {} });
    assert.strictEqual(sent.length, 0, "resends do not move the reminder: nothing before 7 days");
    days = 7.05; await worker.scheduled({ scheduledTime: Date.now() }, eenv, { waitUntil() {} });
    const to = Object.fromEntries(sent.map(x => [x.body.to[0].email.split("@")[0], x.body]));
    assert.ok(to.refus2 && to.refus2.textContent.includes("notre envoi n'avait pas pu partir") && to.refus && / vous attend$/.test(to.refus.subject) && to.rebond && / vous attend$/.test(to.rebond.subject),
      "7th day: " + Object.keys(to).join(", "));
    assert.ok(!to.paye && !to.parti && !to.stop && !to.plainte, "none after payment, unsubscribe or spam complaint");
    const n = sent.length;
    days = 7.6; await worker.scheduled({ scheduledTime: Date.now() }, eenv, { waitUntil() {} });
    assert.strictEqual(sent.length, n, "once only");
    // waiting for the last reminder: listed with its date, and can be sent again (its text then announces one more e-mail)
    j = await mails();
    const wait = j.demandes.find(x => x.email.startsWith("refus@"));
    assert.ok(wait && wait.mois === true && wait.rappelLe - wait.created === 30 * 86400000 && !j.demandes.some(x => x.email.startsWith("refus2@")),
      "month stage listed: " + JSON.stringify(wait));
    sent.length = 0;
    [st, r] = await call("/api/espace/renvoi", Object.assign({ rid: wait.rid }, login), eenv);
    assert.ok(st === 200 && sent.length === 1 && sent[0].body.textContent.includes("Nous vous écrirons une seule autre fois, un mois après votre demande"), "resend at the month stage: " + JSON.stringify(r));
    const kept2 = kv.get("rappel2:" + wait.rid);
    assert.ok(kept2 && Object.keys(kept2.meta).sort().join() === "c,n,x" && JSON.parse(kept2.v).last.ok === true && JSON.parse(kept2.v).r === 1, "resend: the month's record kept, its date unchanged");
    kv.clear(); sent.length = 0; days = 0;

    // a request written before the section « E-mails » (no st, mids, renvois, last; metadata { c, x, n }), as kept in
    // production: listed, can be sent again, gets its ordinary reminder once
    {
      const t = (await call("/api/preview", { indoor: true }))[1].token;
      assert.strictEqual((await call("/api/rappel", { email: "ancien@exemple.fr", apercu: t, n: "Léo" }, eenv))[0], 200);
      const key = [...kv.keys()].find(k => k.startsWith("rappel:")), rec = JSON.parse(kv.get(key).v), meta = kv.get(key).meta;
      for (const f of ["st", "err", "mids", "renvois", "last", "v"]) delete rec[f];
      assert.deepStrictEqual(Object.keys(rec).sort(), ["created", "count", "email", "hero", "indoor", "kids", "link", "minutes", "name", "ref", "town", "walkM"].sort(), "the former record's fields");
      kv.set(key, { v: JSON.stringify(rec), meta: { c: meta.c, x: meta.x, n: 0 } });
      j = await mails();
      assert.ok(j.demandes.length === 1 && j.demandes[0].st === "envoye" && j.demandes[0].renvois === 0 && j.demandes[0].err === null, "former record listed: " + JSON.stringify(j.demandes));
      sent.length = 0;
      assert.strictEqual((await call("/api/espace/renvoi", Object.assign({ rid: key.slice(7) }, login), eenv))[0], 200, "former record: sent again");
      days = 7.05; await worker.scheduled({ scheduledTime: Date.now() }, eenv, { waitUntil() {} });
      days = 7.6; await worker.scheduled({ scheduledTime: Date.now() }, eenv, { waitUntil() {} });
      assert.ok(sent.length === 2 && / vous attend$/.test(sent[1].body.subject) && !kv.has(key), "former record: one ordinary reminder");
      kv.clear(); sent.length = 0; days = 0;
    }
  }
  assert.ok(allLogs.length > 20 && !allLogs.some(l => /exemple\.fr|@exemple/i.test(l)), "no address in the logs: " + allLogs.filter(l => /exemple/.test(l)).join(" | "));
  globalThis.fetch = realFetch; Date.now = realNow; console.log = realLog;
}
console.log("Aperçu par e-mail et section E-mails de l'espace : tous les tests passent.");
