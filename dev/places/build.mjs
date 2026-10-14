// Turns an OpenStreetMap extract (osmium export, GeoJSON sequence) into small tiles of quest
// places, so the server never depends on the busy public Overpass servers.
//   node dev/places/build.mjs places.geojsonseq out-dir
// Each tile covers 0.1° x 0.1° and holds [cat, lat, lon, name, score, id] for every place the
// engine would keep (same classify() as with Overpass). out-dir/index.json records the build.
import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const E = require("../engine.js");
const [input, out] = process.argv.slice(2);
const TILE = 0.1;
export const tileKey = (lat, lon) => `${Math.floor(lat / TILE)}_${Math.floor(lon / TILE)}`;

// Same idea as Overpass "out center": the middle of the bounding box.
function center(geom) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  const walk = c => { if (typeof c[0] === "number") { minX = Math.min(minX, c[0]); maxX = Math.max(maxX, c[0]); minY = Math.min(minY, c[1]); maxY = Math.max(maxY, c[1]); } else c.forEach(walk); };
  walk(geom.coordinates);
  return isFinite(minX) ? { lat: (minY + maxY) / 2, lon: (minX + maxX) / 2 } : null;
}

const tiles = new Map();
let read = 0, kept = 0;
const rl = readline.createInterface({ input: fs.createReadStream(input), crlfDelay: Infinity });
for await (const raw of rl) {
  const line = raw.replace(/^\x1e/, "").trim();   // RFC 8142 record separators
  if (!line) continue;
  read++;
  let f;
  try { f = JSON.parse(line); } catch (e) { continue; }
  if (!f.geometry) continue;
  const props = f.properties || {}, tags = {};
  for (const [k, v] of Object.entries(props)) if (!k.startsWith("@")) tags[k] = v;
  const c = f.geometry.type === "Point" ? { lat: f.geometry.coordinates[1], lon: f.geometry.coordinates[0] } : center(f.geometry);
  if (!c) continue;
  const place = E.classify({ type: props["@type"] || "node", id: props["@id"] || 0, lat: c.lat, lon: c.lon, tags });
  if (!place) continue;
  const key = tileKey(place.lat, place.lon);
  if (!tiles.has(key)) tiles.set(key, []);
  tiles.get(key).push([place.cat, +place.lat.toFixed(5), +place.lon.toFixed(5), place.name, place.score, place.id]);
  kept++;
}

fs.mkdirSync(out, { recursive: true });
for (const [key, list] of tiles) fs.writeFileSync(path.join(out, key + ".json"), JSON.stringify(list));
fs.writeFileSync(path.join(out, "index.json"), JSON.stringify({ built: new Date().toISOString(), tile: TILE, tiles: tiles.size, places: kept }));
console.log(`${read} objets lus, ${kept} lieux gardés, ${tiles.size} tuiles`);
