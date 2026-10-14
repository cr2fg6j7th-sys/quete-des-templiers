// Weekly sales report from Stripe: node dev/report.mjs > marketing/rapports/AAAA-MM-JJ.md
// Needs STRIPE_SECRET_KEY. Counts payment pages opened, paid quests, refunds, and where the
// buyers came from (?ref=…). Test payments made by the automatic site check (ref "smoke") are left out.
const key = process.env.STRIPE_SECRET_KEY;
if (!key) { console.error("STRIPE_SECRET_KEY manquante"); process.exit(1); }
const mode = /_test_/.test(key) ? "test" : "réel";
const now = Math.floor(Date.now() / 1000), weekAgo = now - 7 * 86400;

async function list(path, params) {
  const out = [];
  let after = "";
  for (let page = 0; page < 50; page++) {
    const q = new URLSearchParams(Object.assign({ limit: "100" }, params, after ? { starting_after: after } : {}));
    const r = await fetch(`${process.env.STRIPE_API || "https://api.stripe.com"}/v1/${path}?${q}`, { headers: { authorization: "Bearer " + key } });
    const j = await r.json();
    if (!r.ok) throw new Error(`Stripe ${r.status} ${j.error && j.error.message}`);
    out.push(...j.data);
    if (!j.has_more) break;
    after = j.data[j.data.length - 1].id;
  }
  return out;
}

const euros = cents => (cents / 100).toFixed(2).replace(".", ",") + " €";
function summary(sessions) {
  const real = sessions.filter(s => (s.metadata || {}).ref !== "smoke");
  const paid = real.filter(s => s.payment_status === "paid");
  const byRef = {};
  for (const s of paid) { const r = (s.metadata || {}).ref || "direct"; byRef[r] = (byRef[r] || 0) + 1; }
  const towns = {};
  for (const s of paid) { const t = (s.metadata || {}).v || "à la maison"; towns[t] = (towns[t] || 0) + 1; }
  return { opened: real.length, paid: paid.length, revenue: paid.reduce((a, s) => a + (s.amount_total || 0), 0), byRef, towns };
}

// Anonymous counts of the visit, kept by the site (see /api/hit in dev/worker.js).
const SITE = process.env.SITE_URL || "https://ma-quete-de-chevalier.pv6ggk8t2v.workers.dev";
async function visits() {
  const enc = new TextEncoder().encode("stats:" + key);
  const k = [...new Uint8Array(await crypto.subtle.digest("SHA-256", enc))].map(b => b.toString(16).padStart(2, "0")).join("");
  try {
    const r = await fetch(SITE + "/api/stats", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ key: k, days: 28 }) });
    const j = await r.json();
    return j.ok ? j.days : null;
  } catch (e) { return null; }
}
// sum of an event over the last n days, without the automatic checks ("smoke") and the free demo ("demo")
function total(days, evt, n, only) {
  let t = 0;
  for (const [day, d] of Object.entries(days)) {
    if ((Date.now() - Date.parse(day + "T00:00:00Z")) / 86400000 >= n) continue;
    for (const [ref, c] of Object.entries(d[evt] || {})) if (only ? ref === only : ref !== "smoke" && ref !== "demo") t += c;
  }
  return t;
}
const pct = (a, b) => b ? Math.round(100 * a / b) + " %" : "—";

const week = summary(await list("checkout/sessions", { "created[gte]": String(weekAgo) }));
const all = summary(await list("checkout/sessions", {}));
const refunds = (await list("refunds", { "created[gte]": String(weekAgo) })).filter(r => r.status !== "failed");
const fmt = o => Object.entries(o).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} (${v})`).join(", ") || "aucune";
const day = new Date().toISOString().slice(0, 10);

console.log(`# Point de la semaine — ${day}

Paiements Stripe en mode ${mode}${mode === "test" ? " : ce sont des achats d'essai, pas de vraies ventes" : ""}.

| | 7 derniers jours | Depuis le début |
| --- | --- | --- |
| Pages de paiement ouvertes | ${week.opened} | ${all.opened} |
| Quêtes payées | ${week.paid} | ${all.paid} |
| Encaissé (avant frais) | ${euros(week.revenue)} | ${euros(all.revenue)} |
| Part des paiements commencés qui aboutissent | ${week.opened ? Math.round(100 * week.paid / week.opened) + " %" : "—"} | ${all.opened ? Math.round(100 * all.paid / all.opened) + " %" : "—"} |
| Remboursements | ${refunds.length} (${euros(refunds.reduce((a, r) => a + r.amount, 0))}) | |

Provenance des ventes de la semaine : ${fmt(week.byRef)}.
Communes des ventes de la semaine : ${fmt(week.towns)}.
`);

const days = await visits();
if (!days) console.log("Parcours des visiteurs : compteurs indisponibles (stockage Cloudflare pas encore branché).\n");
else {
  const row = (label, evt) => `| ${label} | ${total(days, evt, 7)} | ${total(days, evt, 28)} |`;
  const T = (e, n) => total(days, e, n);
  const monthMonth = pct(T("preview", 28), T("home", 28));
  console.log(`## Parcours des visiteurs

Comptes anonymes du site (sans les vérifications automatiques ni la démo).

| | 7 derniers jours | 28 derniers jours |
| --- | --- | --- |
${row("Visites de la page d'accueil", "home")}
${row("Clics sur « Créer l'aperçu »", "setup")}
${row("Aperçus créés", "preview")}
${row("Pas assez de lieux autour du départ", "few")}
${row("Cartes en panne (écran d'erreur)", "neterr")}
${row("Position refusée par le téléphone (« Partir d'ici »)", "geo-refus")}
${row("Position introuvable (« Partir d'ici »)", "geo-echec")}
${row("Aperçus envoyés à quelqu'un", "apercu")}
${row("Aperçus reçus et ouverts", "apercu-ouvert")}
${row("Pages de paiement ouvertes", "checkout")}
${row("Quêtes ouvertes après paiement (avec les réouvertures)", "unlock")}
${row("Voix enregistrée pour jouer sans réseau", "horsligne")}
${row("Invitations en image envoyées", "invite")}
${row("Diplômes atteints (quête finie)", "diploma")}
${row("Diplômes en image", "diplome")}
${row("Impressions des diplômes", "imprime")}
${row("Partages de la quête après la fête", "share")}

Sur 28 jours : ${monthMonth} des visites créent un aperçu, et ${pct(T("checkout", 28), T("preview", 28))} des aperçus ouvrent la page de paiement. Diplômes atteints : ${T("diploma", 28)} en 28 jours, pour ${all.paid} quête${all.paid > 1 ? "s" : ""} payée${all.paid > 1 ? "s" : ""} depuis le début. Avec de petits nombres, ces parts bougent beaucoup d'une semaine à l'autre.

Visites de l'accueil par provenance, 28 jours : ${(() => { const by = {}; for (const [day, d] of Object.entries(days)) { if ((Date.now() - Date.parse(day + "T00:00:00Z")) / 86400000 >= 28) continue; for (const [ref, c] of Object.entries(d.home || {})) if (ref !== "smoke" && ref !== "demo") by[ref === "-" ? "direct" : ref] = (by[ref === "-" ? "direct" : ref] || 0) + c; } return fmt(by); })()} (diplome = QR code des diplômes, fete = partage après la fête).

Démo gratuite (entourage), 28 jours : visites ${total(days, "home", 28, "demo")} · aperçus ${total(days, "preview", 28, "demo")} · diplômes ${total(days, "diploma", 28, "demo")}.
`);
}
