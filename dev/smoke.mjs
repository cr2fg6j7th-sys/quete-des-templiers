// Checks the site once it is online: node dev/smoke.mjs https://maquetelegendaire.fr [https://…workers.dev]
// Prints one GitHub annotation per check. In Stripe test mode it also opens a test payment page
// (nothing is charged; unpaid pages expire on their own).
import QuestGeo from "./geo.js";

const site = process.argv[2].replace(/\/$/, "");
// optional: the technical workers.dev address, which must send visitors to the main one
const other = (process.argv[3] || "").replace(/\/$/, "");
const testKey = /^(sk|rk)_test_/.test(process.env.STRIPE_SECRET_KEY || "");
let failed = 0;
// GitHub shows at most 10 notices per step: the passed checks are gathered into one line at the end.
const passed = [];
const ok = msg => passed.push(msg);
const ko = msg => { failed++; console.log(`::error::ÉCHEC ${msg}`); };
const post = (path, body) => fetch(site + path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) })
  .then(async r => ({ status: r.status, json: await r.json().catch(() => null) }));

try {
  const home = await fetch(site + "/");
  const html = await home.text();
  home.ok && html.includes("Ma Quête Légendaire") && html.includes("QUEST_VOICE_KEYS") ? ok("page d'accueil") : ko(`page d'accueil (HTTP ${home.status})`);
  const files = ["/audio/voix/prologue-dehors-m.mp3", "/audio/voix/maison-chaussure.mp3", "/audio/musique/accueil.mp3", "/audio/noms/lea.mp3", "/audio/noms.json", "/fonts/AlegreyaSans-Regular.woff", "/legal/cgv.html", "/anniversaire-chevalier.html",
    "/sw.js", "/og.png", "/icon.svg", "/favicon.ico", "/apple-touch-icon.png", "/stripe-icon.png", "/stripe-logo.png", "/robots.txt", "/sitemap.xml"];
  const missing = [];
  for (const f of files) {
    let r = await fetch(site + f, { method: "HEAD" });
    // a file added by this deploy can take a few seconds to reach every Cloudflare server
    for (let i = 0; i < 3 && !r.ok; i++) { await new Promise(res => setTimeout(res, 10000)); r = await fetch(site + f); }
    if (!r.ok) missing.push(`${f} (HTTP ${r.status} ${r.headers.get("content-type") || ""})`);
  }
  missing.length ? ko("fichiers : " + missing.join(", ")) : ok(`${files.length} fichiers (voix, musique, prénoms, polices, pages, image des liens, hors ligne)`);

  // short address for the videos: /tiktok -> /?ref=tiktok
  try {
    const r = await fetch(site + "/tiktok", { redirect: "manual" });
    r.status === 302 && (r.headers.get("location") || "").endsWith("/?ref=tiktok") ? ok("adresse courte /tiktok") : ko(`adresse courte /tiktok (HTTP ${r.status} ${r.headers.get("location") || ""})`);
  } catch (e) { ko("adresse courte /tiktok : " + e.message); }

  // www and the workers.dev address send page visits to the main address, ?ref kept
  const host = new URL(site).hostname;
  for (const from of [other, host.startsWith("www.") || host.endsWith("workers.dev") ? "" : "https://www." + host]) {
    if (!from || from === site) continue;
    try {
      const r = await fetch(from + "/?ref=smoke", { redirect: "manual" });
      const loc = r.headers.get("location") || "";
      r.status === 301 && loc === site + "/?ref=smoke" ? ok(`${new URL(from).hostname} renvoie vers ${host}`) : ko(`renvoi de ${from} (HTTP ${r.status} ${loc})`);
    } catch (e) { ko(`renvoi de ${from} : ${e.message}`); }
  }

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

  // The national address base answers phones (CORS) with Rosheim.
  {
    let msg;
    try {
      const r = await fetch("https://data.geopf.fr/geocodage/search?q=" + encodeURIComponent("place de la République Rosheim") + "&limit=1", { headers: { origin: site } });
      const j = await r.json();
      const f = j.features && j.features[0];
      msg = f && /Rosheim/.test(f.properties.label) && r.headers.get("access-control-allow-origin") ? null : `réponse inattendue (HTTP ${r.status}, CORS ${r.headers.get("access-control-allow-origin")})`;
    } catch (e) { msg = String(e); }
    msg ? console.log(`::warning::Base Adresse Nationale : ${msg} (Nominatim prend le relais)`) : ok("recherche d'adresse (Base Adresse Nationale)");
  }

  // Anonymous counts and the weekly report's access to them.
  {
    const h = await fetch(site + "/api/hit", { method: "POST", body: JSON.stringify({ e: "home", ref: "smoke" }) });
    const key = [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode("stats:" + (process.env.STRIPE_SECRET_KEY || ""))))].map(b => b.toString(16).padStart(2, "0")).join("");
    const st = await post("/api/stats", { key, days: 1 });
    if (h.status === 204 && st.json && st.json.ok) ok("compteurs de visites");
    else console.log(`::warning::Compteurs de visites inactifs (hit HTTP ${h.status}, stats ${st.status} ${st.json && st.json.reason})`);
  }

  const home2 = await post("/api/preview", { indoor: true, ref: "smoke" });
  home2.json && home2.json.ok && home2.json.count === 6 ? ok("aperçu de la quête à la maison") : ko(`quête à la maison (HTTP ${home2.status})`);
  token = token || (home2.json && home2.json.token) || "";

  if (token) {
    const again = await post("/api/preview", { token, ref: "smoke" });
    again.json && again.json.ok ? ok("aperçu envoyé à quelqu'un : rouvert") : ko(`aperçu envoyé (HTTP ${again.status})`);
  }

  const bad = await post("/api/checkout", { token: "faux", consent: true });
  // before the opening the payment route is closed first (403 « closed »): the forged token is checked after it
  bad.status === 400 ? ok("jeton trafiqué refusé")
    : bad.status === 403 && bad.json && bad.json.reason === "closed" ? ok("jeton trafiqué refusé (paiement fermé avant l'ouverture)")
    : ko(`jeton trafiqué (HTTP ${bad.status})`);
  const unpaid = await post("/api/unlock", { session: "cs_test_inexistant1234567890" });
  unpaid.status === 404 ? ok("session inconnue refusée") : ko(`session inconnue (HTTP ${unpaid.status})`);

  // Before the opening the server refuses every payment, whatever the key (no call to Stripe).
  const tp0 = await post("/api/preview", { indoor: true, ref: "smoke" });
  if (token && tp0.json && tp0.json.testeur) {
    const c = await post("/api/checkout", { token, consent: true, name: "Test", hero: "m", kids: 8, town: "Rosheim", ref: "smoke" });
    c.status === 403 && c.json && c.json.reason === "closed" ? ok("paiement fermé pendant l'avant-première") : ko(`paiement ouvert pendant l'avant-première (HTTP ${c.status})`);
  } else if (testKey && token) {
    const c = await post("/api/checkout", { token, consent: true, name: "Test", hero: "m", kids: 8, town: "Rosheim", ref: "smoke" });
    c.json && c.json.ok && /^https:\/\/checkout\.stripe\.com\//.test(c.json.url) ? ok("page de paiement Stripe (mode test) créée") : ko(`paiement Stripe (HTTP ${c.status} ${JSON.stringify(c.json)})`);
    if (c.json && c.json.ok) c.json.branding === "ok" ? ok("page de paiement aux couleurs de Ma Quête Légendaire") : console.log(`::warning::Image de marque refusée par Stripe : ${c.json.branding}`);
  } else if (!testKey) console.log("::notice::Clé Stripe réelle : pas de page de paiement créée par le test");
  // Before the opening (TESTEURS = "1" in wrangler.toml): the quest is offered to tester families.
  const tp = await post("/api/preview", { indoor: true, ref: "smoke" });
  if (tp.json && tp.json.testeur) {
    const t = await post("/api/testeur", { token: tp.json.token, ref: "smoke" });
    t.json && t.json.ok && t.json.quest ? ok("avant-première : quête offerte aux familles testeuses") : ko(`quête des testeurs (HTTP ${t.status})`);
  } else if (tp.json && tp.json.ok) console.log("::notice::Avant-première terminée : le paiement est proposé");
} catch (e) {
  ko(String(e));
}
console.log(`::notice::OK (${passed.length}) : ${passed.join(" ; ")}`);
process.exit(failed ? 1 : 0);
