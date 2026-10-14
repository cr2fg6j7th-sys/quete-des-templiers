// Availability of brand names: trademarks (TMview: INPI France, EUIPO, WIPO), domains .fr and .com
// (RDAP), and Instagram / TikTok / Pinterest accounts. Public lookups only: a "free" here means
// "nothing found", to be confirmed by hand before buying or filing anything.
//   node dev/brand/check.mjs > marketing/noms/verification.json   (run by .github/workflows/noms.yml)
// Candidates: dev/brand/names-<lot>.json, lot given as the first argument (default 1).
import fs from "node:fs";
const LOT = process.argv[2] || "1";
const NAMES = JSON.parse(fs.readFileSync(new URL(`./names-${LOT}.json`, import.meta.url), "utf8"));
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36";
const get = (url, headers = {}) => fetch(url, { headers: Object.assign({ "user-agent": UA, "accept-language": "fr-FR,fr;q=0.9" }, headers), redirect: "follow", signal: AbortSignal.timeout(20000) });
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function domain(d) {
  const tld = d.split(".").pop();
  const url = tld === "fr" ? `https://rdap.nic.fr/domain/${d}` : `https://rdap.verisign.com/com/v1/domain/${d}`;
  try { const r = await get(url, { accept: "application/rdap+json" }); return r.status === 404 ? "libre" : r.status === 200 ? "pris" : `? (HTTP ${r.status})`; }
  catch (e) { return "? (" + e.name + ")"; }
}

async function instagram(h) {
  try {
    const r = await get(`https://www.instagram.com/api/v1/users/web_profile_info/?username=${h}`, { "x-ig-app-id": "936619743392459", accept: "*/*" });
    if (r.status === 404) return "libre";
    const t = await r.text();
    if (r.status === 200 && /"username"\s*:\s*"/.test(t)) return "pris";
    return `? (HTTP ${r.status})`;
  } catch (e) { return "? (" + e.name + ")"; }
}
async function tiktok(h) {
  try {
    const r = await get(`https://www.tiktok.com/@${h}`);
    const t = await r.text();
    if (new RegExp(`"uniqueId"\\s*:\\s*"${h}"`, "i").test(t)) return "pris";
    if (/"statusCode"\s*:\s*10221|user-not-found|Couldn't find this account|compte introuvable/i.test(t) || r.status === 404) return "libre";
    return `? (HTTP ${r.status})`;
  } catch (e) { return "? (" + e.name + ")"; }
}
async function pinterest(h) {
  try {
    const data = encodeURIComponent(JSON.stringify({ options: { username: h, field_set_key: "profile" }, context: {} }));
    const r = await get(`https://www.pinterest.com/resource/UserResource/get/?source_url=%2F${h}%2F&data=${data}`, { accept: "application/json", "x-requested-with": "XMLHttpRequest" });
    const t = await r.text();
    if (/"username"\s*:\s*"/.test(t) && r.status === 200) return "pris";
    if (r.status === 404 || /"status"\s*:\s*"failure"|"code"\s*:\s*30\b/.test(t)) return "libre";
    const page = await get(`https://www.pinterest.com/${h}/`);
    const html = await page.text();
    if (page.status === 404) return "libre";
    if (page.status === 200 && new RegExp(`"username"\\s*:\\s*"${h}"`, "i").test(html)) return "pris";
    return `? (HTTP ${r.status}/${page.status})`;
  } catch (e) { return "? (" + e.name + ")"; }
}

// TMview (the EU's trademark search, fed by INPI, EUIPO and WIPO), its own JSON search.
async function trademarks(term) {
  const body = { page: "1", pageSize: "100", criteria: "C", basicSearch: term, fOffices: ["FR", "EM", "WO"],
    fields: ["ST13", "tmName", "tmOffice", "applicationNumber", "applicationDate", "tradeMarkStatus", "niceClass", "applicantName"] };
  try {
    const r = await fetch("https://www.tmdn.org/tmview/api/search/results", { method: "POST", signal: AbortSignal.timeout(30000),
      headers: { "content-type": "application/json", accept: "application/json", "user-agent": UA, origin: "https://www.tmdn.org", referer: "https://www.tmdn.org/tmview/" },
      body: JSON.stringify(body) });
    const t = await r.text();
    let j; try { j = JSON.parse(t); } catch (e) { return { error: `HTTP ${r.status} ${t.slice(0, 200)}` }; }
    const list = j.tradeMarks || j.trademarks || j.results || [];
    return { total: j.totalResults ?? list.length, marks: list.map(m => ({ name: m.tmName, office: m.tmOffice, status: m.tradeMarkStatus, classes: m.niceClass, date: m.applicationDate, owner: m.applicantName, id: m.ST13 })) };
  } catch (e) { return { error: String(e) }; }
}

const out = [];
for (const n of NAMES) {
  const row = { name: n.name, trademarks: {}, slugs: {} };
  for (const term of n.tm) { row.trademarks[term] = await trademarks(term); await sleep(1500); }
  for (const s of n.slugs) {
    row.slugs[s] = { fr: await domain(s + ".fr"), com: await domain(s + ".com"), instagram: await instagram(s), tiktok: await tiktok(s), pinterest: await pinterest(s) };
    await sleep(1500);
  }
  out.push(row);
  console.error(n.name, JSON.stringify(row.slugs));
}
console.log(JSON.stringify(out, null, 1));
