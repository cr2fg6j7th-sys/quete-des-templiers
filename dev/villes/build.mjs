// Town pages for Google: « Anniversaire chevalier à Colmar », one page per commune of villes.json,
// built from the same places of France the quests use (OpenStreetMap tiles of dev/places/).
//   node dev/villes/build.mjs places-data site https://maquetelegendaire.fr [--communes test.json]
// Run by the deploy workflow after build.py, once the tiles are there. Each page carries what only
// this town has: how many quest places stand within walking distance of its town hall, their names,
// and the length of a quest from there. It never shows a route nor a riddle: that is what is sold.
// A town without enough named places gets no page (no thin pages). The pages are added to the sitemap.
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const E = require("../engine.js");
const here = path.dirname(new URL(import.meta.url).pathname);
const args = process.argv.slice(2);
const [placesDir, siteDir, SITE] = args;
const communesFile = args.includes("--communes") ? args[args.indexOf("--communes") + 1] : null;
if (!placesDir || !siteDir || !SITE) { console.error("usage: build.mjs places-dir site-dir site-url [--communes file]"); process.exit(2); }

const TILE = 0.1, R = E.SEARCH_RADIUS;
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const slug = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const nb = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");
const km = m => m < 1000 ? `${m} m` : `${(m / 1000).toFixed(1).replace(".", ",")} km`;

// ---- Places around a point, from the tiles ----
const tileCache = new Map();
function tile(key) {
  if (!tileCache.has(key)) {
    const f = path.join(placesDir, key + ".json");
    tileCache.set(key, fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf-8")) : []);
  }
  return tileCache.get(key);
}
function placesAround(lat, lon, r) {
  const dLat = r / 111320, dLon = r / (111320 * Math.cos(lat * Math.PI / 180)), keys = new Set(), out = [];
  for (const a of [lat - dLat, lat + dLat]) for (const b of [lon - dLon, lon + dLon]) keys.add(`${Math.floor(a / TILE)}_${Math.floor(b / TILE)}`);
  for (const k of keys) for (const [cat, la, lo, name, score, id] of tile(k)) {
    const p = { cat, lat: la, lon: lo, name, score, id };
    if (E.dist({ lat, lon }, p) <= r) out.push(p);
  }
  return out;
}

// ---- Communes: name, département, population and the point of the chef-lieu ----
async function getJSON(url) {
  for (let i = 0; i < 3; i++) {
    try { const r = await fetch(url, { headers: { "User-Agent": "MaQueteLegendaire/1.0 (pages villes)" } }); if (r.ok) return await r.json(); }
    catch (e) {}
    await new Promise(res => setTimeout(res, 1500 * (i + 1)));
  }
  return null;
}
// All communes of the zone: within rayonKm of its centre, in its départements, above populationMin.
async function zoneCommunes(z) {
  const out = [];
  for (const dep of z.departements) {
    const list = await getJSON(`https://geo.api.gouv.fr/departements/${dep}/communes?fields=nom,code,centre,population`);
    if (!list) { console.warn(`département ${dep} : liste des communes indisponible`); continue; }
    for (const g of list) {
      if (!g.centre || (g.population || 0) < z.populationMin) continue;
      const [lon, lat] = g.centre.coordinates;
      if (E.dist({ lat: z.centre[0], lon: z.centre[1] }, { lat, lon }) <= z.rayonKm * 1000) out.push({ insee: g.code, nom: g.nom });
    }
  }
  return out;
}
async function commune(c) {
  const g = await getJSON(`https://geo.api.gouv.fr/communes/${c.insee}?fields=nom,population,departement,region,centre`);
  if (!g || g.nom !== c.nom) { console.warn(`${c.nom} : commune introuvable ou nom différent (${g && g.nom})`); return null; }
  // The address base gives the point of the chef-lieu (the town centre), better than the middle of the area.
  const b = await getJSON(`https://data.geopf.fr/geocodage/search?q=${encodeURIComponent(c.nom)}&type=municipality&citycode=${c.insee}&limit=1`);
  const f = b && b.features && b.features[0];
  const [lon, lat] = f ? f.geometry.coordinates : g.centre.coordinates;
  return { nom: g.nom, dep: g.departement.nom, depCode: g.departement.code, region: g.region.nom, population: g.population, lat, lon };
}

// ---- Where a town is, for parents of the area: « à 6 km d'Obernai » ----
const de = n => /^[aeiouyéèêâîôûh]/i.test(n) ? `d'${n}` : `de ${n}`;
let REPERES = [];
function repere(c) {
  const r = REPERES.map(x => ({ nom: x.nom, km: Math.round(E.dist(c, x) / 1000) })).sort((a, b) => a.km - b.km)[0];
  return r && r.km >= 2 && !REPERES.some(x => x.nom === c.nom) ? r : null;
}

// ---- What the page says about one town ----
const CAT = {
  church: ["église ou chapelle", "églises et chapelles"], gate: ["porte ancienne", "portes anciennes"], castle: ["château ou fort", "châteaux et forts"],
  ruins: ["ruine", "ruines"], tower: ["tour", "tours"], well: ["puits", "puits"], fountain: ["fontaine", "fontaines"], viewpoint: ["belvédère", "belvédères"],
  townhall: ["mairie", "mairies"], square: ["place", "places"], park: ["parc ou jardin", "parcs et jardins"], statue: ["statue ou monument", "statues et monuments"],
  memorial: ["monument aux morts", "monuments aux morts"], artwork: ["œuvre d'art", "œuvres d'art"], playground: ["aire de jeux", "aires de jeux"],
  cross: ["croix de chemin", "croix de chemin"], watertower: ["château d'eau", "châteaux d'eau"], lavoir: ["lavoir", "lavoirs"], mill: ["moulin", "moulins"],
  tree: ["arbre remarquable", "arbres remarquables"], house: ["maison ancienne", "maisons anciennes"], fire: ["caserne de pompiers", "casernes de pompiers"],
  library: ["bibliothèque", "bibliothèques"], school: ["école", "écoles"], sport: ["terrain de sport", "terrains de sport"], postbox: ["boîte aux lettres", "boîtes aux lettres"]
};
const ORDER = ["gate", "castle", "tower", "ruins", "church", "house", "mill", "lavoir", "fountain", "well", "cross", "tree", "square", "park", "statue", "memorial",
  "viewpoint", "artwork", "watertower", "townhall", "fire", "library", "school", "sport", "playground", "postbox"];

function study(c) {
  // Start from the town hall when it stands near the chef-lieu: that is where parents would start.
  const near = E.dedupe(placesAround(c.lat, c.lon, 600));
  const hall = near.filter(p => p.cat === "townhall").sort((a, b) => E.dist(c, a) - E.dist(c, b))[0];
  const start = hall ? { lat: hall.lat, lon: hall.lon } : { lat: c.lat, lon: c.lon };
  const startLabel = hall ? "la mairie" : "le centre-ville";
  const places = E.dedupe(placesAround(start.lat, start.lon, R)).filter(p => p.cat !== "townhall");
  const sel = E.selectPlaces(places, start);
  const quest = sel.ok ? E.assemble(start, sel.stops) : null;
  const counts = {};
  for (const p of places) counts[p.cat] = (counts[p.cat] || 0) + 1;
  // The best-known named places (unique names), highest score first.
  const seen = new Set(), named = [];
  for (const p of places.filter(p => p.name).sort((a, b) => b.score - a.score || E.dist(start, a) - E.dist(start, b))) {
    const k = p.name.toLowerCase();
    if (seen.has(k)) continue;
    seen.add(k); named.push(p);
  }
  return { start, startLabel, places, counts, named, quest };
}

function countsText(counts) {
  return ORDER.filter(k => counts[k]).map(k => `${counts[k]} ${CAT[k][counts[k] > 1 ? 1 : 0]}`);
}
const list = a => a.length < 2 ? a.join("") : a.slice(0, -1).join(", ") + " et " + a[a.length - 1];

const style = fs.readFileSync(path.join(path.dirname(siteDir), "dist", "page-style.html"), "utf-8");
const built = (() => { try { return JSON.parse(fs.readFileSync(path.join(placesDir, "index.json"), "utf-8")).built.slice(0, 10); } catch (e) { return ""; } })();
const moisFr = d => d ? new Date(d + "T12:00:00Z").toLocaleDateString("fr-FR", { month: "long", year: "numeric" }) : "";
const EXTRA_CSS = `<style>
.cta{background:var(--rose-soft);border-radius:14px;padding:18px;margin:1.6em 0}
.cta p{margin:.3em 0}.cta a.btn{display:inline-block;margin-top:.6em;background:var(--rose);color:var(--on-rose);text-decoration:none;padding:12px 18px;border-radius:12px;font-weight:700}
.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;text-align:center;margin:1em 0}
.facts div{background:var(--card);border-radius:10px;padding:10px 4px}.facts b{display:block;font-size:1.4rem}.facts span{font-size:.85rem;color:var(--muted)}
.lieux{columns:2;column-gap:24px;padding-left:1.1em}@media (max-width:480px){.lieux{columns:1}}
.src{color:var(--muted);font-size:.85rem}
h3{font-size:1rem;margin:1.1em 0 .2em}
</style>`;

function page(c, s, siblings) {
  const file = `anniversaire-chevalier-${slug(c.nom)}.html`;
  const url = `${SITE}/${file}`;
  const big = c.population >= 100000;
  const n = s.places.length, q = s.quest;
  const top = s.named.slice(0, 8);
  const ex = top.slice(0, 2).map(p => p.name);
  const title = `Anniversaire chevalier à ${c.nom} (7-10 ans) | Ma Quête Légendaire`;
  const desc = `Une chasse au trésor de chevaliers à ${c.nom}, ${ex.length ? `de ${list(ex)}` : "dans les rues du centre"} : ${n} lieux à pied autour de ${s.startLabel}, au prénom de votre enfant. Prête en 2 minutes, aperçu gratuit.`;
  const faq = [
    [`Est-ce que la quête marche à ${c.nom} ?`, `Oui. Autour de ${s.startLabel} de ${c.nom}, ${n} lieux publics peuvent servir d'étapes, dont ${list(countsText(s.counts).slice(0, 3))}. Le Grand Maître en choisit 4 à 6 selon votre point de départ, et l'aperçu gratuit vous dit le nombre d'étapes, la distance et la durée avant de payer.`],
    [`Peut-on partir d'ailleurs que du centre de ${c.nom} ?`, big ? `Oui, et c'est même conseillé : à ${c.nom}, chaque quartier a ses propres lieux. Indiquez votre rue, une place ou un parc près de chez vous : la quête se construit autour.` : `Oui : indiquez votre rue, une place ou un parc. La quête se construit avec les lieux à pied autour du point choisi.`],
    [`Et s'il pleut à ${c.nom} le jour de la fête ?`, "Passez en mode maison : même histoire, mêmes énigmes, et des défis à faire à l'intérieur."],
    ["Les enfants entrent-ils dans les églises ?", "Non. Tout se passe dehors, devant les lieux."]
  ];
  const ld = [
    { "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: [
      { "@type": "ListItem", position: 1, name: "Ma Quête Légendaire", item: `${SITE}/` },
      { "@type": "ListItem", position: 2, name: "Par ville", item: `${SITE}/anniversaire-chevalier-villes.html` },
      { "@type": "ListItem", position: 3, name: c.nom, item: url }] },
    { "@context": "https://schema.org", "@type": "FAQPage", mainEntity: faq.map(([q, a]) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: a } })) }
  ];
  const ref = ("v-" + slug(c.nom)).slice(0, 20);
  const html = `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<link rel="canonical" href="${url}">
<meta property="og:type" content="article">
<meta property="og:locale" content="fr_FR">
<meta property="og:title" content="${esc(`Anniversaire chevalier à ${c.nom}`)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${url}">
<meta property="og:image" content="${SITE}/og.png">
<link rel="icon" href="icon.svg" type="image/svg+xml">
${style}
${EXTRA_CSS}
${ld.map(o => `<script type="application/ld+json">${JSON.stringify(o)}</script>`).join("\n")}
</head>
<body>
<main>
<p class="back"><a href="./">Ma Quête Légendaire</a> › <a href="anniversaire-chevalier-villes.html">Par ville</a> › ${esc(c.nom)}</p>
<h1>Anniversaire chevalier à ${esc(c.nom)}</h1>
<p>À ${esc(c.nom)} (${esc(c.dep)}${repere(c) ? `, à ${repere(c).km} km ${esc(de(repere(c).nom))}` : ""}), Ma Quête Légendaire prépare en deux minutes une chasse au trésor d'une heure pour un anniversaire de 7 à 10 ans : ${n} lieux publics à moins de ${R} m de ${s.startLabel} peuvent servir d'étapes${ex.length ? `, comme ${esc(list(ex))}` : ""}. Le Grand Maître appelle votre enfant par son prénom et guide la troupe de lieu en lieu.</p>

<h2>Une quête au départ de ${s.startLabel}</h2>
<div class="facts"><div><b>${q.steps.length}</b><span>étapes</span></div><div><b>${km(q.walkM)}</b><span>à pied</span></div><div><b>${q.minutes} min</b><span>de jeu environ</span></div></div>
<p>À chaque étape, les enfants écoutent le Grand Maître, relèvent un défi, résolvent une énigme et gagnent une lettre du mot secret. Le parcours exact reste une surprise jusqu'au jour de la fête : l'aperçu gratuit le calcule pour votre point de départ.</p>
${big ? `<p>À ${esc(c.nom)}, inutile d'aller dans le centre : partez de votre rue, d'une place ou d'un parc de votre quartier, la quête se construit avec les lieux autour.</p>` : ""}

<h2>Les lieux du Grand Maître à ${esc(c.nom)}</h2>
<p>Autour de ${s.startLabel}, à pied : ${esc(list(countsText(s.counts)))}.</p>
${top.length ? `<p>Parmi eux :</p>\n<ul class="lieux">\n${top.map(p => `<li>${esc(p.name)} <span class="src">(${CAT[p.cat][0]})</span></li>`).join("\n")}\n</ul>` : ""}
<p class="src">Lieux tirés d'OpenStreetMap${built ? ` (mis à jour en ${moisFr(built)})` : ""}. On reste toujours dehors, devant les lieux.</p>

<div class="cta">
<p><b>Créez la quête de votre enfant à ${esc(c.nom)}</b> : tapez son prénom et votre point de départ, l'aperçu est gratuit.</p>
<p>La quête coûte 24,90 €, à payer après l'aperçu.</p>
<a class="btn" href="./?ref=${ref}">Créer l'aperçu gratuit</a>
</div>

<h2>Questions fréquentes</h2>
${faq.map(([qq, a]) => `<h3>${esc(qq)}</h3>\n<p>${esc(a)}</p>`).join("\n")}

<h2>Pour le reste de la fête</h2>
<p>Le déroulé sur 2 h 30, une invitation à copier, des costumes faits maison et l'adoubement final : <a href="anniversaire-chevalier.html">organiser un anniversaire chevalier</a>.</p>
${siblings.length ? `<p>Aussi près de ${esc(c.nom)} : ${siblings.map(o => `<a href="anniversaire-chevalier-${slug(o.c.nom)}.html">${esc(o.c.nom)}</a>`).join(", ")}.</p>` : ""}
<p class="src">Lieux : © contributeurs OpenStreetMap (licence ODbL). Communes : geo.api.gouv.fr. Point de départ : Base Adresse Nationale (IGN).</p>
</main>
</body>
</html>
`;
  return { file, html, url };
}

function hub(done) {
  const url = `${SITE}/anniversaire-chevalier-villes.html`;
  const z = zone ? zone.nom : "";
  const sorted = done.slice().sort((a, b) => a.c.nom.localeCompare(b.c.nom, "fr"));
  return `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Anniversaire chevalier ${esc(z || "près de chez vous")} : la quête ville par ville | Ma Quête Légendaire</title>
<meta name="description" content="Une chasse au trésor de chevaliers pour un anniversaire de 7 à 10 ans, dans les rues de votre village ou de votre ville : les lieux du Grand Maître à ${esc(list(sorted.slice(0, 5).map(o => o.c.nom)))}…">
<link rel="canonical" href="${url}">
<link rel="icon" href="icon.svg" type="image/svg+xml">
${style}
</head>
<body>
<main>
<p class="back"><a href="./">Ma Quête Légendaire</a></p>
<h1>Anniversaire chevalier ${esc(z || "près de chez vous")}</h1>
<p>La quête se construit dans chaque village ou ville où il y a quelques lieux publics à pied : église, fontaine, vieille porte, place, parc. Voici, commune par commune, combien de lieux le Grand Maître peut choisir autour de la mairie.</p>
<ul>
${sorted.map(o => { const r = repere(o.c); return `<li><a href="${o.file}">Anniversaire chevalier à ${esc(o.c.nom)}</a> : ${o.s.places.length} lieux à pied${r ? `, à ${r.km} km ${esc(de(r.nom))}` : ""}</li>`; }).join("\n")}
</ul>
<p>Votre commune n'est pas dans la liste ? La quête marche partout en France : <a href="./?ref=v-hub">créez l'aperçu gratuit</a> avec votre adresse.</p>
<p class="src">Lieux : © contributeurs OpenStreetMap (licence ODbL).</p>
</main>
</body>
</html>
`;
}

// ---- Build ----
const villes = JSON.parse(fs.readFileSync(path.join(here, "villes.json"), "utf-8"));
const zone = villes.zone;
const given = communesFile ? JSON.parse(fs.readFileSync(communesFile, "utf-8")) : null;
const conf = [...(villes.communes || [])];
REPERES = zone && zone.reperes || [];
for (const x of zone ? (given ? Object.entries(given).map(([insee, c]) => ({ insee, nom: c.nom })) : await zoneCommunes(zone)) : [])
  if (!conf.some(y => y.insee === x.insee)) conf.push(x);
const done = [];
for (const x of conf) {
  const c = given ? given[x.insee] : await commune(x);
  if (!c) continue;
  const s = study(c);
  if (!s.quest || s.named.length < 4) { console.warn(`${c.nom} : pas assez de lieux nommés (${s.named.length}), pas de page`); continue; }
  done.push({ c, s });
}
const out = [];
for (const o of done) {
  const siblings = done.filter(x => x !== o).sort((a, b) => E.dist(o.c, a.c) - E.dist(o.c, b.c)).slice(0, 4).filter(x => E.dist(o.c, x.c) < 150000);
  const p = page(o.c, o.s, siblings);
  o.file = p.file;
  fs.writeFileSync(path.join(siteDir, p.file), p.html);
  out.push(p.url);
}
if (done.length) {
  fs.writeFileSync(path.join(siteDir, "anniversaire-chevalier-villes.html"), hub(done));
  out.unshift(`${SITE}/anniversaire-chevalier-villes.html`);
  const sm = path.join(siteDir, "sitemap.xml");
  const xml = fs.readFileSync(sm, "utf-8").replace("</urlset>", out.map(u => `  <url><loc>${u}</loc></url>\n`).join("") + "</urlset>");
  fs.writeFileSync(sm, xml);
}
console.log(`${done.length} pages de ville sur ${conf.length} : ${done.map(o => `${o.c.nom} (${o.s.places.length} lieux)`).join(", ")}`);
