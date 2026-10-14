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
    const r = await fetch(`https://api.stripe.com/v1/${path}?${q}`, { headers: { authorization: "Bearer " + key } });
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
