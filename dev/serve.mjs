// Local test server for the paid app: node dev/serve.mjs [port]
// Runs dist/worker.js like Cloudflare would, serves site/ and audio/, and fakes Stripe
// (a pretend checkout page with "Payer" and "Annuler"). Build first: python3 dev/build.py
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

const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json", ".mp3": "audio/mpeg", ".woff": "font/woff", ".css": "text/css" };
function file(p) {
  const clean = decodeURIComponent(p).replace(/\.\.+/g, "");
  for (const dir of ["site", "."]) {
    let f = path.join(root, dir, clean);
    if (fs.existsSync(f) && fs.statSync(f).isDirectory()) f = path.join(f, "index.html");
    if (fs.existsSync(f) && fs.statSync(f).isFile() && (dir === "site" || clean.startsWith("/audio/")))
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
<p>${s.params["line_items[0][price_data][product_data][description]"]}</p><p>${s.params["line_items[0][price_data][unit_amount]"]} centimes</p>
<p id="msg">${s.params["custom_text[submit][message]"]}</p>
<a id="pay" href="/fake-checkout?id=${s.id}&pay=1">Payer</a> <a id="cancel" href="${s.params.cancel_url}">Annuler</a>`,
    { headers: { "content-type": "text/html; charset=utf-8" } });
}

const env = {
  QUEST_KEY: "cle-de-test", STRIPE_SECRET_KEY: "sk_test_local", STRIPE_API: `${base}/stripe`, PRICE_CENTS: "2490",
  ASSETS: { fetch: req => file(new URL(req.url).pathname) }
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
    else res = await worker.fetch(req, env);
  } catch (e) { res = new Response(String(e && e.stack || e), { status: 500 }); }
  nres.writeHead(res.status, Object.fromEntries(res.headers));
  nres.end(Buffer.from(await res.arrayBuffer()));
}).listen(port, "127.0.0.1", () => console.log("Serveur de test : " + base));
