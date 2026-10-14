# End-to-end test of the paid app in headless Chromium, against dev/serve.mjs (fake Stripe)
# with OpenStreetMap services mocked by synthetic places. Run: python3 dev/e2e_paid.py
import asyncio, hashlib, json, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8791
BASE = f"http://127.0.0.1:{PORT}"
fixture = json.loads(subprocess.check_output(["node", "-e", """
const C={lat:48.5,lon:7.47};let id=1;
const m=(dn,de)=>({lat:C.lat+dn/111320,lon:C.lon+de/(111320*Math.cos(C.lat*Math.PI/180))});
const node=(dn,de,tags)=>Object.assign({type:'node',id:id++,tags},m(dn,de));
console.log(JSON.stringify({elements:[
 node(20,-150,{amenity:'place_of_worship',religion:'christian',name:'Église Saint-Martin'}),
 node(-30,60,{amenity:'fountain',name:'Fontaine du Marché'}),
 node(0,300,{historic:'city_gate',name:'Porte Haute'}),
 node(10,-420,{historic:'city_gate',name:'Porte Basse'}),
 node(-250,100,{leisure:'park',name:'Parc des Remparts'}),
 node(150,20,{historic:'memorial',memorial:'war_memorial',name:'Monument aux morts'}),
 node(80,-60,{historic:'memorial',memorial:'statue',name:"Jeanne d'Arc"})]}));
"""]))
PLACES = ["Saint-Martin", "Fontaine du Marché", "Porte Haute", "Porte Basse", "Parc des Remparts", "Monument aux morts", "Jeanne d'Arc"]
search = [{"lat": "48.5", "lon": "7.47", "display_name": "Place de l'Église, Bourg-Test, Bas-Rhin, France", "name": "Place de l'Église", "address": {"village": "Bourg-Test"}}]
# national address base: same spot (merged with the OpenStreetMap answer), and a second address
ban = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [7.47002, 48.50001]}, "properties": {"label": "Place de l'Église 67999 Bourg-Test", "score": 0.92, "city": "Bourg-Test"}},
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [7.48, 48.51]}, "properties": {"label": "Rue de l'Église 67999 Autre-Bourg", "score": 0.5, "city": "Autre-Bourg"}}]}
fails = []
def check(cond, label):
    print(("ok   " if cond else "FAIL ") + label)
    if not cond: fails.append(label)

OSM_CALLS = []
async def new_page(browser, errs):
    ctx = await browser.new_context(viewport={"width": 390, "height": 860})
    pg = await ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("request", lambda r: OSM_CALLS.append(r.url) if "overpass" in r.url else None)
    await pg.route("**/overpass-api.de/**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(fixture)))
    await pg.route("**/nominatim.openstreetmap.org/search**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(search)))
    await pg.route("**/data.geopf.fr/**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(ban)))
    return ctx, pg

async def main():
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "osm-fixture.json").write_text(json.dumps(fixture), encoding="utf-8")
    seq = "".join("\x1e" + json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [e["lon"], e["lat"]]},
                   "properties": dict(e["tags"], **{"@type": e["type"], "@id": e["id"]})}) + "\n" for e in fixture["elements"])
    (ROOT / "dist" / "fixture.geojsonseq").write_text(seq, encoding="utf-8")
    subprocess.run(["node", str(ROOT / "dev" / "places" / "build.mjs"), str(ROOT / "dist" / "fixture.geojsonseq"), str(ROOT / "site" / "places")], check=True)
    srv = subprocess.Popen(["node", str(ROOT / "dev" / "serve.mjs"), str(PORT)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(50):
        try: urllib.request.urlopen(BASE + "/", timeout=1); break
        except Exception: time.sleep(0.1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            errs = []
            ctx, pg = await new_page(b, errs)
            await pg.goto(BASE + "/")
            check("Le jour de la fête" in await pg.inner_text("body"), "accueil : présentation avant le formulaire")
            await pg.click("button.big >> nth=0")
            await pg.fill("#hero-name", "Michael")
            await pg.fill("#start-q", "place de l'église Bourg-Test")
            await pg.click("button:has-text('Chercher')")
            await pg.wait_for_selector("text=Rue de l'Église 67999 Autre-Bourg", timeout=8000)
            labels = await pg.eval_on_selector_all("button.result", "b=>b.map(x=>x.textContent)")
            check(labels == ["Place de l'Église 67999 Bourg-Test", "Rue de l'Église 67999 Autre-Bourg"], "adresses : base nationale d'abord, doublon OpenStreetMap fusionné " + str(labels))
            await pg.click("text=Place de l'Église 67999 Bourg-Test")
            await pg.wait_for_selector("text=Ce qui vous attend", timeout=8000)
            store = await pg.evaluate("localStorage.getItem('quete-templiers-v3')")
            dom = await pg.content()
            check(not any(x in store for x in PLACES) and not any(x in dom for x in PLACES), "aperçu : aucun lieu dans la page ni dans le téléphone")
            check('"quest":null' in store and '"token":"' in store, "aperçu : seul un jeton chiffré est gardé")
            check("function choose" not in dom, "le moteur de choix des lieux n'est pas dans la page")
            check(not OSM_CALLS, "aperçu fait depuis notre copie des lieux, sans appeler OpenStreetMap")
            await pg.screenshot(path=str(ROOT / "dist" / "p1-apercu.png"), full_page=True)
            # send the preview to the other parent: it opens on another phone, places still hidden
            await pg.evaluate("navigator.clipboard.writeText=t=>{window.__copied=t;return Promise.resolve()};navigator.share=undefined")
            await pg.click("text=Décider à deux")
            shared = (await pg.evaluate("window.__copied")).split(" ")[-1]
            check("?apercu=" in shared and "&n=Michael" in shared, "aperçu : lien à envoyer à l'autre parent")
            ctxS, pgS = await new_page(b, errs)
            await pgS.goto(shared.replace("http://127.0.0.1:%d" % PORT, BASE))
            await pgS.wait_for_selector("text=Ce qui vous attend", timeout=8000)
            bodyS = await pgS.inner_text("body"); domS = await pgS.content()
            check("La quête de Michael" in bodyS and "Débloquer la quête" in bodyS and not any(x in domS for x in PLACES) and "?apercu" not in pgS.url,
                  "aperçu reçu : même quête, prête à payer, lieux cachés, adresse nettoyée")
            await ctxS.close()
            await pg.click("button:has-text('Débloquer la quête')")
            check("Cochez d'abord" in await pg.inner_text("body"), "paiement refusé sans la case cochée")
            await pg.check("#consent")
            await pg.click("button:has-text('Débloquer la quête')")
            await pg.wait_for_url("**/fake-checkout**", timeout=5000)
            body = await pg.inner_text("body")
            check("2490" in body and "Michael" in body and "renoncé au droit de rétractation" in body, "page de paiement : prix, prénom, mention de renonciation")
            sessions = json.loads(urllib.request.urlopen(BASE + "/__sessions").read())
            meta = sessions[-1]["metadata"]
            check(meta.get("n") == "Michael" and meta.get("consent") and meta.get("t0") and not any(x in json.dumps(meta) for x in PLACES), "Stripe : prénom, accord daté, lieux chiffrés")
            # cancel, then pay
            await pg.click("#cancel")
            await pg.wait_for_selector("text=Paiement annulé", timeout=5000)
            check("?annule" not in pg.url, "retour après annulation : aperçu et message")
            await pg.check("#consent")
            await pg.click("button:has-text('Débloquer la quête')")
            await pg.wait_for_url("**/fake-checkout**", timeout=5000)
            await pg.click("#pay")
            await pg.wait_for_selector("text=Le guide du Grand Maître", timeout=8000)
            check("?paid" not in pg.url, "retour de paiement : quête ouverte, adresse nettoyée")
            check("Votre lien de quête" in await pg.inner_text("body"), "guide : carte du lien de quête")
            mail = await pg.get_attribute("a:has-text(\"par e-mail\")", "href")
            check(mail.startswith("mailto:?subject=") and "quete%3Dcs_test_" in mail, "guide : lien de quête envoyable par e-mail")
            # the voice of this quest is kept on the phone
            await pg.wait_for_function("(document.getElementById('offline-status')||{}).textContent.includes('enregistrée')", timeout=20000)
            check(True, "voix de la quête enregistrée dans le téléphone")
            # invitation as an image
            await pg.fill("#inv-date", "2026-11-21")
            await pg.fill("#inv-time", "14:30")
            await pg.fill("#inv-place", "Place de l'Église")
            await pg.click("text=Créer l'invitation")
            await pg.wait_for_function("(()=>{const i=document.querySelector('img.parchment');return i&&i.naturalWidth===1080})()", timeout=8000)
            await pg.locator("img.parchment").first.screenshot(path=str(ROOT / "dist" / "p3-invitation.png"))
            check(await pg.is_visible("text=Envoyer ou enregistrer l'image"), "invitation en image prête à envoyer")
            # without network: reload, the page and the voice come from the phone
            await ctx.set_offline(True)
            await pg.reload()
            await pg.wait_for_selector("text=Le guide du Grand Maître", timeout=8000)
            st206 = await pg.evaluate("""(async()=>{const k=JSON.parse(localStorage.getItem('quete-templiers-v3'));
              const r=await fetch('audio/voix/'+(k.hero==='f'?'intro-dehors-f':'intro-dehors-m')+'.mp3',{headers:{Range:'bytes=0-99'}});return [r.status,(await r.arrayBuffer()).byteLength]})()""")
            check(st206 == [206, 100], f"sans réseau : page rouverte et voix servie par morceaux {st206}")
            await ctx.set_offline(False)
            sid = json.loads(urllib.request.urlopen(BASE + "/__sessions").read())[-1]["id"]
            await pg.screenshot(path=str(ROOT / "dist" / "p2-guide.png"), full_page=True)
            # play the whole quest
            await pg.click("text=Commencer la quête")
            await pg.click("text=Première étape")
            n = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).quest.steps.length")
            answers = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).quest.steps.map(s=>s.choices[s.answer])")
            first_place = await pg.inner_text("h2")
            for i in range(n):
                await pg.click("text=Nous y sommes")
                if i == 1:  # reload mid-quest keeps progress
                    await pg.reload(); await pg.wait_for_selector("text=Défi réussi", timeout=4000)
                await pg.click("text=Défi réussi")
                await pg.click(f"button.choice:has-text(\"{answers[i]}\")")
                await pg.wait_for_selector("text=Lettre gagnée", timeout=4000)
                await pg.click("text=Trouver le mot secret" if i == n - 1 else "text=Étape suivante")
            word = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).quest.word")
            await pg.fill("#secret", "fidèle" if word == "FIDELE" else word.lower())
            await pg.click("text=Ouvrir le Sceau")
            await pg.wait_for_selector("text=Le trésor est à vous", timeout=4000)
            check("Michael" in await pg.inner_text(".diploma"), f"quête jouée jusqu'au diplôme ({n} étapes, mot {word})")
            await pg.evaluate("window.print=()=>{window.__printed=document.querySelectorAll('#print .dip').length}")
            await pg.locator("button:has-text('Imprimer les diplômes')").click()
            kids = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).kids")
            pages = await pg.evaluate("window.__printed")
            check(pages == kids, f"diplômes imprimables : celui du héros et un par compagnon ({pages} pages A4)")
            await pg.click("text=Créer le diplôme en image")
            await pg.wait_for_function("(()=>{const i=document.querySelector('img.parchment');return i&&i.naturalWidth===1080})()", timeout=8000)
            await pg.locator("img.parchment").first.screenshot(path=str(ROOT / "dist" / "p4-diplome.png"))
            check(True, "diplôme en image")
            await pg.evaluate("navigator.clipboard.writeText=t=>{window.__copied=t;return Promise.resolve()};navigator.share=undefined")
            await pg.click("text=Partager la quête")
            copied = await pg.evaluate("window.__copied")
            check(copied and copied.endswith("?ref=fete") and "cs_" not in copied, "diplôme : partage de la présentation, jamais du lien payé")
            sw = await pg.evaluate("document.documentElement.scrollWidth")
            check(sw <= 390, "pas de défilement horizontal")
            await ctx.close()
            # another phone opens the reopen link
            ctx2, pg2 = await new_page(b, errs)
            await pg2.goto(f"{BASE}/?quete={sid}")
            await pg2.wait_for_selector("text=Le guide du Grand Maître", timeout=8000)
            st = json.loads(await pg2.evaluate("localStorage.getItem('quete-templiers-v3')"))
            check(st["name"] == "Michael" and st["unlocked"] and len(st["quest"]["steps"]) == n, "lien de quête : même quête sur un autre téléphone")
            await ctx2.close()
            # unpaid session and fake session
            sessions = json.loads(urllib.request.urlopen(BASE + "/__sessions").read())
            unpaid = sessions[0]["id"]
            ctx3, pg3 = await new_page(b, errs)
            await pg3.goto(f"{BASE}/?quete={unpaid}")
            await pg3.wait_for_selector("text=n'a pas pu s'ouvrir", timeout=8000)
            check("pas encore confirmé" in await pg3.inner_text("body"), "session non payée : refus")
            await pg3.goto(f"{BASE}/?quete=cs_test_inventee1234567890")
            await pg3.wait_for_selector("text=n'a pas pu s'ouvrir", timeout=8000)
            check("pas valable" in await pg3.inner_text("body"), "session inventée : refus")
            # API refusals
            r = await pg3.evaluate("""fetch('api/checkout',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({token:'abc',consent:true})}).then(r=>r.status)""")
            check(r == 400, "jeton trafiqué : refusé")
            r = await pg3.evaluate("""fetch('api/unlock',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({session:'cs_test_x'})}).then(r=>r.status)""")
            check(r == 400, "identifiant de session invalide : refusé")
            # indoor quest, paid build
            await pg3.goto(BASE + "/")
            await pg3.evaluate("localStorage.clear()")
            await pg3.goto(BASE + "/?ref=fete")
            await pg3.click("button.big >> nth=0")
            await pg3.fill("#hero-name", "Léa")
            await pg3.click("text=Chevalière")
            await pg3.click("text=Il pleut ?")
            await pg3.wait_for_selector("text=quête à la maison", timeout=6000)
            await pg3.check("#consent")
            await pg3.click("button:has-text('Débloquer la quête')")
            await pg3.wait_for_url("**/fake-checkout**", timeout=5000)
            await pg3.click("#pay")
            await pg3.wait_for_selector("text=Le guide du Grand Maître", timeout=8000)
            st = json.loads(await pg3.evaluate("localStorage.getItem('quete-templiers-v3')"))
            check(st["quest"]["indoorOnly"] and st["hero"] == "f" and st["quest"]["scrambled"] == "ELFIED", "quête à la maison payée et ouverte")
            sessions = json.loads(urllib.request.urlopen(BASE + "/__sessions").read())
            check(sessions[-1]["metadata"].get("ref") == "fete" and "?ref" not in pg3.url, "provenance « fete » suivie jusqu'au paiement")
            await ctx3.close()
            # without our copy of the places, and the main map server busy: our server fetches the places
            idx = ROOT / "site" / "places" / "index.json"; idx.rename(idx.with_suffix(".off"))
            ctx4 = await b.new_context(viewport={"width": 390, "height": 860})
            pg4 = await ctx4.new_page()
            await pg4.route("**/overpass-api.de/**", lambda r: r.fulfill(status=504, body="Gateway Timeout"))
            await pg4.route("**/nominatim.openstreetmap.org/search**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(search)))
            await pg4.route("**/data.geopf.fr/**", lambda r: r.abort())
            await pg4.goto(BASE + "/")
            await pg4.click("button.big >> nth=0")
            await pg4.fill("#hero-name", "Léo")
            await pg4.fill("#start-q", "place de l'église Bourg-Test")
            await pg4.click("button:has-text('Chercher')")
            await pg4.click("text=Place de l'Église, Bourg-Test")
            await pg4.wait_for_selector("text=Ce qui vous attend", timeout=10000)
            check(True, "sans copie des lieux et carte injoignable : relais par notre serveur ; base d'adresses injoignable : OpenStreetMap seul")
            await ctx4.close()
            idx.with_suffix(".off").rename(idx)
            # anonymous counts of the visit, and the report's access to them
            counts = json.loads(urllib.request.urlopen(BASE + "/__counts").read())
            events = {k.split("|")[1] for k in counts}
            want = {"home", "setup", "preview", "checkout", "unlock", "diploma", "apercu", "apercu-ouvert", "horsligne", "share"}
            check(want <= events and all(len(k.split("|")) == 4 for k in counts), "compteurs anonymes : " + ", ".join(sorted(events)))
            key = hashlib.sha256(b"stats:sk_test_local").hexdigest()
            req = lambda body: urllib.request.Request(BASE + "/api/stats", data=json.dumps(body).encode(), headers={"content-type": "application/json"}, method="POST")
            st = json.loads(urllib.request.urlopen(req({"key": key, "days": 2})).read())
            day = time.strftime("%Y-%m-%d", time.gmtime())
            check(st["ok"] and st["days"][day]["preview"].get("fete") == 1, "compteurs lisibles par le rapport (provenance comprise)")
            try: urllib.request.urlopen(req({"key": "faux"})); bad = 200
            except urllib.error.HTTPError as e: bad = e.code
            check(bad == 403, "compteurs refusés sans la bonne clé")
            check(not errs, "aucune erreur JavaScript " + str(errs[:3]))
            await b.close()
    finally:
        srv.terminate()
    print("\n" + ("TOUT EST BON" if not fails else f"{len(fails)} échec(s)"))
    sys.exit(1 if fails else 0)

asyncio.run(main())
