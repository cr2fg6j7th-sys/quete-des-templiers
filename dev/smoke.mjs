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
  const files = ["/audio/voix/prologue-dehors-m.mp3", "/audio/noms/lea.mp3", "/audio/noms.json", "/fonts/AlegreyaSans-Regular.woff", "/legal/cgv.html", "/anniversaire-chevalier.html"];
  const missing = [];
  for (const f of files) { const r = await fetch(site + f, { method: "HEAD" }); if (!r.ok) missing.push(`${f} (HTTP ${r.status})`); }
  missing.length ? ko("fichiers : " + missing.join(", ")) : ok(`${files.length} fichiers (voix, prénoms, polices, pages)`);

  // Quests from our own copy of the places of France: a village, two dense city centres.
  let token = "";
  const towns = [];
  for (const [label, c] of [["Rosheim", { lat: 48.4983, lon: 7.4703 }], ["Strasbourg", { lat: 48.5818, lon: 7.7509 }], ["Paris", { lat: 48.8530, lon: 2.3499 }]]) {
    const t0 = Date.now();
    const p = await post("/api/preview", { start: c, ref: "smoke" });
    if (p.json && p.json.ok) { towns.push(`${label} ${p.json.count} étapes ${p.json.walkM} m (${Date.now() - t0} ms)`); token = token || p.json.token; }
    else if (p.json && p.json.reason === "nodata") { towns.push(`${label} : copie des lieux absente`); }
    else { towns.push(`${label} : HTTP ${p.status} ${JSON.stringify(p.json).slice(0, 80)}`); failed++; }
  }
  console.log((towns.some(t => /HTTP|absente/.test(t)) ? "::warning::" : "::notice::") + "Aperçus depuis notre copie des lieux : " + towns.join(" ; "));

  // The free demo (GitHub Pages) reads the same tiles from another origin.
  {
    const r = await fetch(site + "/places/index.json", { headers: { origin: "https://cr2fg6j7th-sys.github.io" } });
    r.ok && r.headers.get("access-control-allow-origin") === "*" ? ok("lieux lisibles par la démo (CORS)") : console.log(`::warning::Lieux non lisibles par la démo (HTTP ${r.status}, CORS ${r.headers.get("access-control-allow-origin")})`);
  }

  // Fallback without the copy: our server asks the public Overpass servers (often busy).
  {
    const p = await post("/api/preview", { start: { lat: 48.4983, lon: 7.4703 }, fetch: true, ref: "smoke" });
    p.json && p.json.ok ? ok("relais OpenStreetMap par le serveur") : console.log(`::warning::Relais OpenStreetMap indisponible (HTTP ${p.status})`);
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
