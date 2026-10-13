// Synthetic test data in Overpass format (invented places, not real coordinates).
const E = require("./engine.js");
const assert = require("assert");
const C = { lat: 48.5000, lon: 7.4700 };
const m = (dn, de) => ({ lat: C.lat + dn / 111320, lon: C.lon + de / (111320 * Math.cos(C.lat * Math.PI / 180)) });
let id = 1;
const node = (dn, de, tags) => Object.assign({ type: "node", id: id++, tags }, m(dn, de));
const way = (dn, de, tags) => ({ type: "way", id: id++, center: m(dn, de), tags });

const dense = [
  node(20, -150, { amenity: "place_of_worship", religion: "christian", name: "Église Saint-Martin", historic: "church" }),
  way(25, -140, { amenity: "place_of_worship", religion: "christian", building: "church", name: "Église Saint-Martin" }), // duplicate
  node(-30, 60, { amenity: "fountain", name: "Fontaine du Marché" }),
  node(0, 300, { historic: "city_gate", name: "Porte Haute" }),
  node(10, -420, { historic: "city_gate", name: "Porte Basse" }),
  node(-10, 90, { amenity: "townhall", name: "Mairie" }),
  way(-250, 100, { leisure: "park", name: "Parc des Remparts" }),
  node(-260, 140, { leisure: "playground" }),
  node(150, 20, { historic: "memorial", memorial: "war_memorial", name: "Monument aux morts" }),
  node(5, 5, { historic: "memorial", memorial: "plaque", name: "Plaque" }),           // excluded
  node(-20, 40, { place: "square", name: "Place du Marché" }),
  node(80, -60, { historic: "memorial", memorial: "statue", name: "Jeanne d'Arc" }),
  way(300, 300, { leisure: "garden", access: "private" }),                               // excluded
  node(120, 200, { amenity: "place_of_worship", religion: "muslim", name: "Mosquée" }),  // not used (theme)
  node(40, 10, { historic: "memorial", memorial: "stolperstein" }),                      // excluded
  node(900, 900, { historic: "castle", name: "Château lointain" })                       // too far
];

function check(name, q) {
  assert(q.ok, name + ": quest should build");
  const n = q.steps.length;
  assert(n >= 4 && n <= 6, name + ": 4 to 6 steps");
  assert(q.walkM <= E.MAX_WALK + 10, name + ": walk too long " + q.walkM);
  assert.strictEqual([...q.scrambled].sort().join(""), [...q.word].sort().join(""), name + ": letters must spell the word");
  assert.notStrictEqual(q.scrambled, q.word, name + ": letters must be scrambled");
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++)
    assert(E.dist(q.steps[i], q.steps[j]) >= 60, name + ": stops too close");
  console.log(`\n${name}: ${n} étapes, ${q.walkM} m, ~${q.minutes} min, mot ${q.word} (lettres : ${q.scrambled})`);
  q.steps.forEach((s, i) => console.log(`  ${i + 1}. [${s.cat}] ${s.P}  (+${s.legM} m vers ${s.dir}) lettre ${s.letter}`));
}

const q1 = E.build(dense, C);
check("Bourg dense", q1);
assert(!q1.steps.some(s => /Plaque|Mosquée|Château lointain/.test(s.name)), "excluded places must not appear");
assert(q1.steps.filter(s => s.name === "Église Saint-Martin").length <= 1, "duplicate church merged");

// Sparse village: only 3 usable places -> must refuse and suggest indoor mode
const sparse = [node(0, 50, { amenity: "place_of_worship", religion: "christian", name: "Église" }),
  node(100, 0, { leisure: "playground" }), node(-80, -40, { amenity: "fountain" })];
const q2 = E.build(sparse, C);
assert(!q2.ok && q2.reason === "few", "sparse village must report too few places");
console.log("\nVillage pauvre en lieux :", q2);

// Spread-out places: must trim to stay under the walking limit
const spread = [
  node(0, 650, { historic: "city_gate", name: "Porte Est" }), node(0, -650, { historic: "city_gate", name: "Porte Ouest" }),
  node(650, 0, { historic: "tower", name: "Tour Nord" }), node(-650, 0, { historic: "tower", name: "Tour Sud" }),
  node(100, 100, { amenity: "fountain", name: "Fontaine" }), node(-100, -120, { leisure: "park", name: "Parc" }),
  node(60, -200, { amenity: "townhall", name: "Hôtel de ville" }), node(-200, 200, { place: "square", name: "Place Neuve" })];
check("Lieux dispersés", E.build(spread, C));

// Article handling
console.log("\nArticles :", ["Église Saints-Pierre-et-Paul", "Saint-Étienne", "Parc des Remparts", "Porte du Lion", "Jeanne d'Arc", "Hôtel de ville", "Le Belvédère"]
  .map((n, i) => E.articleize(n, ["l'église", "l'église", "le parc", "la porte", "la statue", "la mairie", "le point de vue"][i])));

// Every template has what the app needs
for (const [cat, list] of Object.entries(E.T)) for (const t of list)
  for (const k of ["teaser", "generic", "clue", "story", "defi", "defiIn", "q", "choices", "fact", "hints", "adult"])
    assert(t[k] !== undefined && (k !== "hints" || t.hints.length === 3), `template ${cat} missing ${k}`);
// The paid quest stores only the chosen stops: rebuilding from them gives the same quest,
// and the free preview gives away no place, position or answer.
const sel = E.select(dense, C);
assert(sel.ok && sel.stops.length >= 4, "select must choose stops");
const full = E.build(dense, C), again = E.assemble(C, JSON.parse(JSON.stringify(sel.stops)));
assert.deepStrictEqual(again, full, "assemble(select) must equal build");
const pv = JSON.stringify(E.preview(full));
for (const s of full.steps) assert(!pv.includes(s.name) && !pv.includes(String(s.lat).slice(0, 7)) && !pv.includes(s.choices[s.answer]), "preview leaks " + s.name);
const home = E.assemble(null, E.indoorStops());
assert(home.indoorOnly && home.steps.length === 6 && home.scrambled === "ELFIED" && home.steps.every(s => s.lat === null && s.v === 0), "indoor quest");
console.log("\nTous les tests passent.");
