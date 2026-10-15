// The worker's address handling, without a network: node dev/test-worker.mjs (after dev/build.py).
// www and workers.dev send page visits to the main address (path and ?ref kept); the main address
// serves the files; the API answers on every address.
import assert from "node:assert";
import worker from "../dist/worker.js";

const env = { SITE_HOST: "maquetelegendaire.fr", ASSETS: { fetch: () => new Response("fichier") } };
const go = (url, init) => worker.fetch(new Request(url, init), env, { waitUntil() {} });

for (const from of ["https://www.maquetelegendaire.fr", "https://ma-quete-de-chevalier.pv6ggk8t2v.workers.dev"]) {
  const r = await go(from + "/anniversaire-chevalier.html?ref=diplome");
  assert.strictEqual(r.status, 301, from);
  assert.strictEqual(r.headers.get("location"), "https://maquetelegendaire.fr/anniversaire-chevalier.html?ref=diplome");
}
assert.strictEqual(await (await go("https://maquetelegendaire.fr/?ref=tiktok")).text(), "fichier", "main address serves the page");
const api = await go("https://ma-quete-de-chevalier.pv6ggk8t2v.workers.dev/api/nope", { method: "POST", body: "{}" });
assert.notStrictEqual(api.status, 301, "the API is never redirected");
const none = await go("https://ma-quete-de-chevalier.pv6ggk8t2v.workers.dev/", undefined);
assert.strictEqual(await (await worker.fetch(new Request("https://x.workers.dev/"), { ASSETS: env.ASSETS }, {})).text(), "fichier", "without SITE_HOST nothing is redirected");
assert.strictEqual(none.status, 301);
// short addresses for the videos and bios
for (const [path, ref] of [["/tiktok", "tiktok"], ["/TikTok/", "tiktok"], ["/insta", "instagram"], ["/pinterest", "pinterest"]]) {
  const r = await go("https://maquetelegendaire.fr" + path);
  assert.strictEqual(r.status, 302, path);
  assert.strictEqual(r.headers.get("location"), "https://maquetelegendaire.fr/?ref=" + ref, path);
}
const viaWww = await go("https://www.maquetelegendaire.fr/tiktok");
assert.strictEqual(viaWww.headers.get("location"), "https://maquetelegendaire.fr/tiktok", "www goes to the main address first");
console.log("Adresses du site : tous les tests passent.");
