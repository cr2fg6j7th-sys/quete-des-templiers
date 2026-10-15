// Which first names to record next, from the INSEE file of first names (births by year, France and
// by département): children born 2014-2021 (5 to 12 years old in 2026), France and Alsace (67, 68).
//   node dev/prenoms/analyse.mjs nat.csv dpt.csv > dev/prenoms/candidats.json
// A name counts as covered when the Grand Master already says it, or a name that sounds the same
// (same rule as the app: QuestVoice.nameClip).
import fs from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const V = require("../voice.js");

const [natFile, dptFile] = process.argv.slice(2);
const YEARS = new Set(["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021"]);
const ALSACE = new Set(["67", "68"]);

function rows(file) {
  const lines = fs.readFileSync(file, "utf-8").split(/\r?\n/).filter(Boolean);
  const head = lines[0].replace(/^﻿/, "").split(";").map(h => h.trim().toUpperCase().replace(/"/g, ""));
  const col = names => head.findIndex(h => names.includes(h));
  const iName = col(["PRENOM", "PREUSUEL"]), iYear = col(["PERIODE", "ANNAIS"]), iN = col(["VALEUR", "NOMBRE"]), iDpt = col(["DPT"]), iSex = col(["SEXE"]);
  return lines.slice(1).map(l => l.split(";").map(x => x.replace(/"/g, "").trim())).map(c => ({ name: c[iName], year: c[iYear], n: +c[iN] || 0, dpt: iDpt >= 0 ? c[iDpt] : null, sex: c[iSex] }));
}
const pretty = s => s.toLowerCase().replace(/(^|[-\s'])(\p{L})/gu, (m, a, b) => a + b.toUpperCase());

const nat = new Map(), als = new Map(), sexOf = new Map();
let natTotal = 0, alsTotal = 0;
for (const r of rows(natFile)) {
  if (!YEARS.has(r.year) || !r.name || r.name.startsWith("_")) continue;
  const k = pretty(r.name);
  nat.set(k, (nat.get(k) || 0) + r.n); natTotal += r.n;
  sexOf.set(k, (sexOf.get(k) || 0) + (r.sex === "1" ? r.n : -r.n));
}
for (const r of rows(dptFile)) {
  if (!YEARS.has(r.year) || !ALSACE.has(r.dpt) || !r.name || r.name.startsWith("_")) continue;
  const k = pretty(r.name);
  als.set(k, (als.get(k) || 0) + r.n); alsTotal += r.n;
}
// Births with a rare name (grouped by INSEE) still count in the totals: they are the children we cannot name.
for (const r of rows(natFile)) if (YEARS.has(r.year) && r.name && r.name.startsWith("_")) natTotal += r.n;
for (const r of rows(dptFile)) if (YEARS.has(r.year) && ALSACE.has(r.dpt) && r.name && r.name.startsWith("_")) alsTotal += r.n;

const recorded = new Set(JSON.parse(fs.readFileSync(new URL("../../audio/noms.json", import.meta.url), "utf-8")));
const covered = (name, set) => !!V.nameClip(name, set);
function coverage(set) {
  let a = 0, b = 0;
  for (const [k, n] of nat) if (covered(k, set)) a += n;
  for (const [k, n] of als) if (covered(k, set)) b += n;
  return { france: +(100 * a / natTotal).toFixed(1), alsace: +(100 * b / alsTotal).toFixed(1) };
}

// Candidates: not covered yet, ranked by their share in France plus their share in Alsace.
const all = new Set([...nat.keys(), ...als.keys()]);
const cands = [...all].filter(k => !covered(k, recorded))
  .map(k => ({ prenom: k, france: nat.get(k) || 0, alsace: als.get(k) || 0, genre: (sexOf.get(k) || 0) >= 0 ? "m" : "f",
    poids: (nat.get(k) || 0) / natTotal + (als.get(k) || 0) / alsTotal }))
  .filter(c => c.france >= 20 || c.alsace >= 10)
  .sort((a, b) => b.poids - a.poids);
// One recording per sound: the most frequent spelling stands for the others.
const picked = [], sounds = new Set();
for (const c of cands) { const s = V.sound(V.slug(c.prenom)); if (sounds.has(s)) continue; sounds.add(s); picked.push(c); }

const steps = {};
for (const n of [250, 500, 750, 1000, 1250, 1500]) {
  const set = new Set(recorded); picked.slice(0, n).forEach(c => set.add(V.slug(c.prenom)));
  steps[n] = coverage(set);
}
console.log(JSON.stringify({ naissances: "2014-2021", total: { france: natTotal, alsace: alsTotal }, aujourdhui: coverage(recorded), apres: steps,
  candidats: picked.slice(0, 1600).map(({ poids, ...c }) => c) }, null, 1));
console.error(`aujourd'hui ${JSON.stringify(coverage(recorded))} ; après ${JSON.stringify(steps)}`);
