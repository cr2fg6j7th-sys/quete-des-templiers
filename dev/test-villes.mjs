// Town pages when the API Géo or the address base fail, without a network: node dev/test-villes.mjs
// (after dev/build.py, which writes dist/page-style.html). A fake API Géo and address base run on
// 127.0.0.1; places are the e2e fixture's seven places (dev/e2e_paid.py) copied around each town.
import assert from "node:assert";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import http from "node:http";
import { execFile } from "node:child_process";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "villes-"));
const placesDir = path.join(tmp, "places"), siteDir = path.join(tmp, "site"), cacheFile = path.join(tmp, "cache.json");
fs.mkdirSync(path.join(tmp, "dist"));
fs.copyFileSync(path.join(root, "dist", "page-style.html"), path.join(tmp, "dist", "page-style.html"));

// Towns of the fake département 67, inside the zone of villes.json (15 km around Obernai/Rosheim).
const TOWNS = [
  { code: "67901", nom: "Testbourg", lat: 48.50, lon: 7.47, places: true },
  { code: "67902", nom: "Villetest", lat: 48.46, lon: 7.52, places: true },
  { code: "67903", nom: "Montest", lat: 48.53, lon: 7.42, places: true },
  { code: "67904", nom: "Rocbourg", lat: 48.44, lon: 7.43, places: true },
  { code: "67905", nom: "Videville", lat: 48.42, lon: 7.50, places: false },   // no places: no page, no error
  { code: "67906", nom: "Loinville", lat: 48.80, lon: 7.90, places: true },    // outside the zone
  { code: "67907", nom: "Hameau", lat: 48.49, lon: 7.45, places: true, population: 300 }   // too small
];
// the fixture of dev/e2e_paid.py, around each town (metres north, east)
const FIXTURE = [[20, -150, { amenity: "place_of_worship", religion: "christian", name: "Église Saint-Martin" }], [-30, 60, { amenity: "fountain", name: "Fontaine du Marché" }],
  [0, 300, { historic: "city_gate", name: "Porte Haute" }], [10, -420, { historic: "city_gate", name: "Porte Basse" }], [-250, 100, { leisure: "park", name: "Parc des Remparts" }],
  [150, 20, { historic: "memorial", memorial: "war_memorial", name: "Monument aux morts" }], [80, -60, { historic: "memorial", memorial: "statue", name: "Jeanne d'Arc" }]];
let id = 1, seq = "";
for (const t of TOWNS.filter(t => t.places)) for (const [dn, de, tags] of FIXTURE) {
  const lat = t.lat + dn / 111320, lon = t.lon + de / (111320 * Math.cos(t.lat * Math.PI / 180));
  seq += "\x1e" + JSON.stringify({ type: "Feature", geometry: { type: "Point", coordinates: [lon, lat] }, properties: Object.assign({}, tags, { "@type": "node", "@id": id++ }) }) + "\n";
}
fs.writeFileSync(path.join(tmp, "fixture.geojsonseq"), seq);
await run([path.join(root, "dev", "places", "build.mjs"), path.join(tmp, "fixture.geojsonseq"), placesDir]);

// ---- Fake services ----
const S = { geo: "up", ban: "up", renamed: {}, missing: new Set(), only: null, calls: { geo: 0, ban: 0 } };
const server = http.createServer((req, res) => {
  const u = new URL(req.url, "http://x"), svc = u.pathname.startsWith("/geo/") ? "geo" : "ban";
  S.calls[svc]++;
  const mode = S[svc];
  if (mode === "hang") return;   // never answers
  if (mode === "reset") return req.socket.destroy();
  if (mode === "down") { res.writeHead(503); return res.end("Service Unavailable"); }
  const json = (o, st = 200) => { res.writeHead(st, { "content-type": "application/json" }); res.end(JSON.stringify(o)); };
  const towns = TOWNS.filter(t => !S.only || S.only.includes(t.nom));
  const centre = t => ({ type: "Point", coordinates: [t.lon, t.lat] });
  let m;
  if (u.pathname === "/geo/departements/67/communes") return json(towns.map(t => ({ nom: t.nom, code: t.code, centre: centre(t), population: t.population || 2000 })));
  if ((m = u.pathname.match(/^\/geo\/communes\/(\d+)$/))) {
    const t = TOWNS.find(t => t.code === m[1]);
    if (!t || S.missing.has(t.nom)) return json({ code: 404, message: "Commune non trouvée" }, 404);
    return json({ nom: S.renamed[t.nom] || t.nom, code: t.code, population: t.population || 2000, departement: { code: "67", nom: "Bas-Rhin" }, region: { code: "44", nom: "Grand Est" }, centre: centre(t) });
  }
  if (u.pathname === "/ban/search") {
    const t = TOWNS.find(t => t.code === u.searchParams.get("citycode"));
    return json({ type: "FeatureCollection", features: t ? [{ type: "Feature", geometry: { type: "Point", coordinates: [t.lon + 0.0001, t.lat] }, properties: {} }] : [] });
  }
  json({}, 404);
});
await new Promise(r => server.listen(0, "127.0.0.1", r));
const base = `http://127.0.0.1:${server.address().port}`;

function run(args, env = {}) {
  return new Promise(resolve => {
    const t0 = Date.now();
    execFile("node", args, { env: Object.assign({}, process.env, env), timeout: 60000 }, (err, stdout, stderr) =>
      resolve({ code: err ? err.code : 0, out: stdout, err: stderr, all: stdout + stderr, ms: Date.now() - t0 }));
  });
}
function freshSite() {
  fs.rmSync(siteDir, { recursive: true, force: true });
  fs.mkdirSync(siteDir);
  fs.writeFileSync(path.join(siteDir, "sitemap.xml"), "<urlset>\n</urlset>\n");
}
const pages = () => fs.readdirSync(siteDir).filter(f => /^anniversaire-chevalier-(?!villes).*\.html$/.test(f)).sort();
async function build(extraEnv = {}, cache = cacheFile) {
  freshSite();
  S.calls = { geo: 0, ban: 0 };
  return run([path.join(root, "dev", "villes", "build.mjs"), placesDir, siteDir, "https://exemple.fr"],
    Object.assign({ VILLES_GEO_API: base + "/geo", VILLES_BAN_API: base + "/ban", VILLES_CACHE: cache, VILLES_TIMEOUT_MS: "300", VILLES_RETRY_MS: "20", VILLES_BAISSE_OK: "" }, extraEnv));
}
const ALL = ["anniversaire-chevalier-montest.html", "anniversaire-chevalier-rocbourg.html", "anniversaire-chevalier-testbourg.html", "anniversaire-chevalier-villetest.html"];
const show = r => `exit ${r.code}\n${r.all}`;

try {
  // 1. API down, no cache: clean failure, no page written, and quick (no long wait per commune).
  S.geo = "down";
  let r = await build();
  assert.strictEqual(r.code, 1, show(r));
  assert.match(r.out, /^::error::Pages de ville : .*ne répondait pas.*Mise en ligne arrêtée/m, show(r));
  assert.deepStrictEqual(pages(), [], "no page when the build stops");
  assert.ok(r.ms < 10000, `failed in ${r.ms} ms`);
  console.log(`ok   API en panne sans cache : échec propre en ${r.ms} ms`);

  // 2. Everything answers: 4 pages, the town without places has none (normal case, no error), cache written.
  S.geo = "up";
  r = await build();
  assert.strictEqual(r.code, 0, show(r));
  assert.deepStrictEqual(pages(), ALL, show(r));
  assert.match(r.err, /Videville : pas assez de lieux nommés/);
  assert.doesNotMatch(r.out, /::error::|::warning::/, show(r));
  assert.match(r.out.trim().split("\n").pop(), /^4 pages de ville sur 5 : /);
  let c = JSON.parse(fs.readFileSync(cacheFile, "utf-8"));
  assert.strictEqual(c.pages.count, 4);
  assert.ok(Object.keys(c.responses).some(k => k.startsWith("API Géo:/departements/67/communes")) && Object.keys(c.responses).some(k => k.startsWith("Base Adresse Nationale:/search")), "answers cached");
  assert.ok(fs.readFileSync(path.join(siteDir, "sitemap.xml"), "utf-8").includes("https://exemple.fr/anniversaire-chevalier-testbourg"), "sitemap");
  const ref = Object.fromEntries(ALL.map(f => [f, fs.readFileSync(path.join(siteDir, f), "utf-8")]));
  console.log("ok   services en ligne : 4 pages, commune sans lieux sans page ni erreur, cache écrit");

  // 3. Both services down, with the cache: every page built, identical, and a warning says so.
  S.geo = "down"; S.ban = "reset";
  r = await build();
  assert.strictEqual(r.code, 0, show(r));
  assert.deepStrictEqual(pages(), ALL);
  for (const f of ALL) assert.strictEqual(fs.readFileSync(path.join(siteDir, f), "utf-8"), ref[f], f + " same page from the cache");
  assert.match(r.out, /::warning::Pages de ville : API Géo sans réponse, \d+ réponses reprises/);
  assert.match(r.out, /::warning::Pages de ville : Base Adresse Nationale sans réponse/);
  // after two calls without an answer, a service is no longer asked
  assert.ok(S.calls.geo <= 6 && S.calls.ban <= 6, JSON.stringify(S.calls));
  console.log(`ok   services en panne avec cache : 4 pages identiques (${S.calls.geo} + ${S.calls.ban} tentatives, ${r.ms} ms)`);

  // 4. Slow API (never answers): the timeout holds; with the cache the pages are built, without it a clean failure.
  S.geo = "hang"; S.ban = "hang";
  r = await build();
  assert.strictEqual(r.code, 0, show(r));
  assert.deepStrictEqual(pages(), ALL);
  assert.ok(r.ms < 8000, `slow API: ${r.ms} ms`);
  r = await build({}, path.join(tmp, "none.json"));
  assert.strictEqual(r.code, 1, show(r));
  assert.match(r.out, /::error::.*pas de réponse en 0\.3 s/, show(r));
  assert.ok(r.ms < 8000, `slow API without cache: ${r.ms} ms`);
  fs.rmSync(path.join(tmp, "none.json"), { force: true });
  console.log(`ok   API lente : délai de 0,3 s respecté (${r.ms} ms sans cache, échec propre)`);

  // 5. Address base down without its answers in the cache, API Géo up: start from the API Géo centre,
  //    pages built. Videville (no places) is no outage as the last build had no page for it either;
  //    with no record of the last build at all, it stops the deploy (it might have lost its page).
  S.geo = "up"; S.ban = "down";
  const c2 = path.join(tmp, "geo-only.json");
  c = JSON.parse(fs.readFileSync(cacheFile, "utf-8"));
  for (const k of Object.keys(c.responses)) if (k.startsWith("Base Adresse Nationale:")) delete c.responses[k];
  fs.writeFileSync(c2, JSON.stringify(c));
  r = await build({}, c2);
  assert.strictEqual(r.code, 0, show(r));
  assert.deepStrictEqual(pages(), ALL);
  assert.match(r.err, /Base Adresse Nationale n'a pas répondu .* départ depuis le centre/);
  delete c.pages; fs.writeFileSync(c2, JSON.stringify(c));
  r = await build({}, c2);
  assert.strictEqual(r.code, 1, show(r));
  assert.match(r.out, /::error::.*Videville \(Base Adresse Nationale, sans réponse en cache\)/, show(r));
  fs.rmSync(c2, { force: true });
  console.log("ok   Base Adresse Nationale en panne sans cache : départ au centre de la commune, pages construites");

  // 6. A renamed commune and a commune unknown to the API: distinct messages, no failure (fresh cache: no earlier count).
  S.ban = "up"; S.renamed = { Montest: "Montest-sur-Bruche" }; S.missing = new Set(["Rocbourg"]);
  const c3 = path.join(tmp, "renamed.json");
  r = await build({}, c3);
  assert.strictEqual(r.code, 0, show(r));
  assert.match(r.err, /Montest \(67903\) : l'API Géo donne maintenant le nom « Montest-sur-Bruche »/);
  assert.match(r.err, /Rocbourg \(67904\) : commune inconnue de l'API Géo \(HTTP 404\)/);
  assert.doesNotMatch(r.all, /n'a pas répondu|::error::/, show(r));
  assert.deepStrictEqual(pages(), ["anniversaire-chevalier-testbourg.html", "anniversaire-chevalier-villetest.html"]);
  fs.rmSync(c3, { force: true });
  S.renamed = {}; S.missing = new Set();
  console.log("ok   commune renommée ou inconnue : messages distincts, pas d'échec");

  // 7. Fewer pages than last time (cache says 4): 2 pages = -50 % -> failure; 3 pages = -25 % -> failure;
  //    then VILLES_BAISSE_OK=1 accepts it once and records the new count.
  S.only = ["Testbourg", "Villetest", "Videville"];
  r = await build();
  assert.strictEqual(r.code, 1, show(r));
  assert.match(r.out, /::error::Pages de ville : 2 construites contre 4 au déploiement du .*Pages qui disparaîtraient : (Montest, Rocbourg|Rocbourg, Montest).*VILLES_BAISSE_OK=1/, show(r));
  assert.deepStrictEqual(pages(), []);
  assert.strictEqual(JSON.parse(fs.readFileSync(cacheFile, "utf-8")).pages.count, 4, "count kept after a refused build");
  S.only = ["Testbourg", "Villetest", "Montest"];
  r = await build();
  assert.strictEqual(r.code, 1, "3 of 4: -25 %\n" + show(r));
  r = await build({ VILLES_BAISSE_OK: "1" });
  assert.strictEqual(r.code, 0, show(r));
  assert.match(r.out, /::warning::.*Baisse acceptée \(VILLES_BAISSE_OK=1\)/);
  assert.strictEqual(pages().length, 3);
  assert.strictEqual(JSON.parse(fs.readFileSync(cacheFile, "utf-8")).pages.count, 3, "new count recorded");
  r = await build();
  assert.strictEqual(r.code, 0, "next deploy compares with 3\n" + show(r));
  console.log("ok   chute du nombre de pages : échec, puis passage outre avec VILLES_BAISSE_OK=1");
  S.only = null;

  // 8. Test data (--communes): no network, no cache, as before.
  const given = path.join(tmp, "communes.json");
  fs.writeFileSync(given, JSON.stringify({ "67901": { nom: "Testbourg", dep: "Bas-Rhin", depCode: "67", region: "Grand Est", population: 2000, lat: 48.5, lon: 7.47 } }));
  S.geo = "down"; S.ban = "down"; S.calls = { geo: 0, ban: 0 };
  freshSite();
  r = await run([path.join(root, "dev", "villes", "build.mjs"), placesDir, siteDir, "https://exemple.fr", "--communes", given],
    { VILLES_GEO_API: base + "/geo", VILLES_CACHE: path.join(tmp, "unused.json") });
  assert.strictEqual(r.code, 0, show(r));
  assert.deepStrictEqual(pages(), ["anniversaire-chevalier-testbourg.html"]);
  assert.ok(!fs.existsSync(path.join(tmp, "unused.json")) && S.calls.geo === 0, "no cache, no network with --communes");
  console.log("ok   données de test (--communes) : sans réseau ni cache");
} finally {
  server.closeAllConnections();
  server.close();
  fs.rmSync(tmp, { recursive: true, force: true });
}
console.log("Pages de ville : tous les tests passent.");
