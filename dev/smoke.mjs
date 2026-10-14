// Checks the site once it is online: node dev/smoke.mjs https://…workers.dev
// Prints one GitHub annotation per check. In Stripe test mode it also opens a test payment page
// (nothing is charged; unpaid pages expire on their own).
import QuestGeo from "./geo.js";

const site = process.argv[2].replace(/\/$/, "");
const testKey = /^(sk|rk)_test_/.test(process.env.STRIPE_SECRET_KEY || "");
let failed = 0;
const ok = msg => console.log(`::notice::OK ${msg}`);
const ko = msg => { failed++; console.log(`::error::ÉCHEC ${msg}`); };
const post = (path, body) => fetch(site + path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) })
  .then(async r => ({ status: r.status, json: await r.json().catch(() => null) }));

try {
  const home = await fetch(site + "/");
  const html = await home.text();
  home.ok && html.includes("Ma Quête de Chevalier") && html.includes("QUEST_VOICE_KEYS") ? ok("page d'accueil") : ko(`page d'accueil (HTTP ${home.status})`);
  for (const f of ["/audio/voix/prologue-dehors-m.mp3", "/audio/noms/lea.mp3", "/audio/noms.json", "/fonts/AlegreyaSans-Regular.woff", "/legal/cgv.html", "/anniversaire-chevalier.html"]) {
    const r = await fetch(site + f, { method: "HEAD" });
    r.ok ? ok(f) : ko(`${f} (HTTP ${r.status})`);
  }

  // A real quest around the church square of Rosheim, places fetched like the phone does.
  const start = { lat: 48.4983, lon: 7.4703 };
  let elements = [];
  try {
    const r = await fetch("https://overpass-api.de/api/interpreter", { method: "POST", headers: { "content-type": "application/x-www-form-urlencoded", "user-agent": "ma-quete-de-chevalier-smoke" },
      body: "data=" + encodeURIComponent(QuestGeo.overpassQuery(start.lat, start.lon)) });
    elements = QuestGeo.slim((await r.json()).elements);
  } catch (e) { console.log("::warning::OpenStreetMap ne répond pas, test sur la quête à la maison seulement"); }
  let token = "";
  if (elements.length) {
    const p = await post("/api/preview", { start, elements, ref: "smoke" });
    if (p.json && p.json.ok && p.json.token && !JSON.stringify(p.json).includes("Rosheim")) { ok(`aperçu à Rosheim : ${p.json.count} étapes, ${p.json.walkM} m`); token = p.json.token; }
    else ko(`aperçu à Rosheim (HTTP ${p.status} ${JSON.stringify(p.json).slice(0, 120)})`);
  }
  const home2 = await post("/api/preview", { indoor: true, ref: "smoke" });
  home2.json && home2.json.ok && home2.json.count === 6 ? ok("aperçu de la quête à la maison") : ko(`quête à la maison (HTTP ${home2.status})`);
  token = token || (home2.json && home2.json.token) || "";

  const bad = await post("/api/checkout", { token: "faux", consent: true });
  bad.status === 400 ? ok("jeton trafiqué refusé") : ko(`jeton trafiqué (HTTP ${bad.status})`);
  const unpaid = await post("/api/unlock", { session: "cs_test_inexistant1234567890" });
  unpaid.status === 404 ? ok("session inconnue refusée") : ko(`session inconnue (HTTP ${unpaid.status})`);

  if (testKey && token) {
    const c = await post("/api/checkout", { token, consent: true, name: "Test", hero: "m", kids: 8, town: "Rosheim", ref: "smoke" });
    c.json && c.json.ok && /^https:\/\/checkout\.stripe\.com\//.test(c.json.url) ? ok("page de paiement Stripe (mode test) créée") : ko(`paiement Stripe (HTTP ${c.status} ${JSON.stringify(c.json)})`);
  } else if (!testKey) console.log("::notice::Clé Stripe réelle : pas de page de paiement créée par le test");
} catch (e) {
  ko(String(e));
}
process.exit(failed ? 1 : 0);
