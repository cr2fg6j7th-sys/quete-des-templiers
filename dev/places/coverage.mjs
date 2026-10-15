// How many communes can get a quest: every commune of the Bas-Rhin and the Haut-Rhin, plus a fixed
// sample of French communes by size. Start point as a parent would choose it: the town hall near
// the chef-lieu (point of the Base Adresse Nationale), else the chef-lieu itself.
//   node dev/places/coverage.mjs places-data label > marketing/couverture/<label>.json
// Run by .github/workflows/couverture.yml (the tiles live in the Actions cache).
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const E = require("../engine.js");
const [dir, label = "?"] = process.argv.slice(2);
const TILE = 0.1, R = E.SEARCH_RADIUS;

const cache = new Map();
function tile(k) {
  if (!cache.has(k)) { const f = path.join(dir, k + ".json"); cache.set(k, fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, "utf-8")) : []); }
  return cache.get(k);
}
function around(lat, lon, r) {
  const dLat = r / 111320, dLon = r / (111320 * Math.cos(lat * Math.PI / 180)), keys = new Set(), out = [];
  for (const a of [lat - dLat, lat + dLat]) for (const b of [lon - dLon, lon + dLon]) keys.add(`${Math.floor(a / TILE)}_${Math.floor(b / TILE)}`);
  for (const k of keys) for (const [cat, la, lo, name, score, id] of tile(k)) {
    const p = { cat, lat: la, lon: lo, name, score, id };
    if (E.dist({ lat, lon }, p) <= r) out.push(p);
  }
  return out;
}
async function getJSON(url) {
  for (let i = 0; i < 4; i++) {
    try { const r = await fetch(url, { headers: { "User-Agent": "MaQueteLegendaire/1.0 (couverture des communes)" } }); if (r.ok) return await r.json(); }
    catch (e) {}
    await new Promise(res => setTimeout(res, 1000 * (i + 1)));
  }
  return null;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

// Chef-lieu point from the address base (cached between runs, so before/after use the same points).
const POINTS = path.join(path.dirname(new URL(import.meta.url).pathname), "points-communes.json");
const points = fs.existsSync(POINTS) ? JSON.parse(fs.readFileSync(POINTS, "utf-8")) : {};
async function point(c) {
  if (points[c.code]) return points[c.code];
  const b = await getJSON(`https://data.geopf.fr/geocodage/search?q=${encodeURIComponent(c.nom)}&type=municipality&citycode=${c.code}&limit=1`);
  const f = b && b.features && b.features[0];
  const p = f ? f.geometry.coordinates : c.centre && c.centre.coordinates;
  if (p) points[c.code] = [+p[1].toFixed(5), +p[0].toFixed(5)];
  await sleep(40);
  return points[c.code];
}

function study(lat, lon) {
  const c = { lat, lon };
  const hall = E.dedupe(around(lat, lon, 600)).filter(p => p.cat === "townhall").sort((a, b) => E.dist(c, a) - E.dist(c, b))[0];
  const start = hall ? { lat: hall.lat, lon: hall.lon } : c;
  const places = E.dedupe(around(start.lat, start.lon, R + 120));
  const sel = E.selectPlaces(places, start);
  return { ok: sel.ok, steps: sel.ok ? sel.stops.length : 0, found: places.length, cats: sel.ok ? sel.stops.map(s => s.cat) : [] };
}

const band = p => p < 500 ? "moins de 500" : p < 2000 ? "500 à 2 000" : p < 10000 ? "2 000 à 10 000" : "plus de 10 000";
function rng(seed) { let s = seed >>> 0; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }

const rows = [];
for (const dep of ["67", "68"]) {
  const list = await getJSON(`https://geo.api.gouv.fr/departements/${dep}/communes?fields=nom,code,centre,population`) || [];
  for (const c of list) rows.push({ zone: dep, code: c.code, nom: c.nom, population: c.population || 0, centre: c.centre });
}
// France: 120 communes per size band, always the same ones (fixed seed, sorted by code first).
const all = (await getJSON("https://geo.api.gouv.fr/communes?fields=nom,code,centre,population") || []).filter(c => c.centre).sort((a, b) => a.code.localeCompare(b.code));
const rand = rng(20261015);
for (const b of ["moins de 500", "500 à 2 000", "2 000 à 10 000", "plus de 10 000"]) {
  const pool = all.filter(c => band(c.population || 0) === b && !["67", "68"].includes(c.code.slice(0, 2)));
  for (let i = 0; i < 120 && pool.length; i++) { const c = pool.splice(Math.floor(rand() * pool.length), 1)[0]; rows.push({ zone: "France", code: c.code, nom: c.nom, population: c.population || 0, centre: c.centre }); }
}

const out = [];
for (const r of rows) {
  const p = await point(r);
  if (!p) continue;
  const s = study(p[0], p[1]);
  out.push({ zone: r.zone, code: r.code, nom: r.nom, population: r.population, ...s });
}
fs.writeFileSync(POINTS, JSON.stringify(points));

const summary = {};
for (const r of out) {
  for (const k of [r.zone === "France" ? "France (échantillon)" : r.zone === "67" ? "Bas-Rhin" : "Haut-Rhin", `${r.zone === "France" ? "France" : "Alsace"} · ${band(r.population)}`]) {
    const s = summary[k] || (summary[k] = { communes: 0, quete: 0, six: 0 });
    s.communes++; if (r.ok) s.quete++; if (r.steps === 6) s.six++;
  }
}
for (const s of Object.values(summary)) { s.part = Math.round(100 * s.quete / s.communes) + " %"; s.partSix = Math.round(100 * s.six / s.communes) + " %"; }
const echecs = out.filter(r => r.zone !== "France" && !r.ok).sort((a, b) => b.population - a.population).map(r => `${r.nom} (${r.population} hab., ${r.found} lieux)`);
console.log(JSON.stringify({ label, built: (() => { try { return JSON.parse(fs.readFileSync(path.join(dir, "index.json"), "utf-8")); } catch (e) { return null; } })(), summary, echecsAlsace: echecs, communes: out }, null, 1));
console.error(Object.entries(summary).map(([k, s]) => `${k} : ${s.quete}/${s.communes} (${s.part})`).join(" ; "));
