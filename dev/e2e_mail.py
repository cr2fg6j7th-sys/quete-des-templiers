# End-to-end test of the preview by e-mail (and its one reminder) in headless Chromium, against dev/serve.mjs
# (fake Stripe, fake Brevo: no e-mail leaves this machine). Run: python3 dev/e2e_mail.py
# It builds the site with --mail, then without it at the end (the state of the repository).
import asyncio, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT, PORT_OFF = 8793, 8794
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
search = [{"lat": "48.5", "lon": "7.47", "display_name": "Place de l'Église, Bourg-Test, Bas-Rhin, France", "name": "Place de l'Église", "address": {"village": "Bourg-Test"}}]
ban = {"type": "FeatureCollection", "features": [
    {"type": "Feature", "geometry": {"type": "Point", "coordinates": [7.47002, 48.50001]}, "properties": {"label": "Place de l'Église 67999 Bourg-Test", "score": 0.92, "city": "Bourg-Test"}}]}
fails = []
def check(cond, label):
    print(("ok   " if cond else "FAIL ") + label)
    if not cond: fails.append(label)

def call(path, body=None, base=BASE, method=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, headers={"content-type": "application/json"}, method=method or ("POST" if data else "GET"))
    try:
        r = urllib.request.urlopen(req, timeout=20); code, raw = r.status, r.read()
    except urllib.error.HTTPError as e:
        code, raw = e.code, e.read()
    try: return code, json.loads(raw)
    except Exception: return code, raw.decode("utf-8", "replace")
mails = lambda: call("/__mails")[1]
records = lambda: [k for k in call("/__kv?prefix=rappel:")[1]]
today = lambda: time.strftime("%Y-%m-%d", time.gmtime())

def serve(port, **extra):
    # the server's output (the worker's logs) goes to a file, read at the end: no address may be in it
    out = open(ROOT / "dist" / f"serve-{port}.log", "a", encoding="utf-8")
    srv = subprocess.Popen(["node", str(ROOT / "dev" / "serve.mjs"), str(port)], env=dict(os.environ, **extra), stdout=out, stderr=subprocess.STDOUT)
    for _ in range(50):
        try: urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1); break
        except Exception: time.sleep(0.1)
    return srv

async def new_page(browser, rappel_calls=None):
    ctx = await browser.new_context(viewport={"width": 390, "height": 860})
    pg = await ctx.new_page()
    pg.errs = []
    pg.on("pageerror", lambda e: pg.errs.append(str(e)))
    if rappel_calls is not None: pg.on("request", lambda r: rappel_calls.append(r.post_data) if r.url.endswith("/api/rappel") else None)
    await pg.route("**/overpass-api.de/**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(fixture)))
    await pg.route("**/nominatim.openstreetmap.org/search**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(search)))
    await pg.route("**/data.geopf.fr/**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(ban)))
    await pg.route("**/geo.api.gouv.fr/**", lambda r: r.fulfill(status=200, content_type="application/json", body="[]"))
    return ctx, pg

async def open_setup(pg, name):
    await pg.goto(BASE + "/")
    await pg.click("button.big >> nth=0")
    await pg.fill("#hero-name", name)

async def start_by_address(pg):
    await pg.evaluate("document.querySelectorAll('details.more').forEach(d=>d.open=true)")
    await pg.fill("#start-q", "place de l'église Bourg-Test")
    await pg.click("button:has-text('Chercher')")
    await pg.wait_for_selector("text=Place de l'Église 67999 Bourg-Test", timeout=8000)
    await pg.click("text=Place de l'Église 67999 Bourg-Test")

def link_of(m):
    return re.search(r"https?://\S+\?apercu=\S+", m["text"]).group(0)
def stop_of(m):   # the unsubscribe link, from the List-Unsubscribe header
    return m["headers"]["List-Unsubscribe"][1:-1]

def pay(token):
    code, c = call("/api/checkout", {"token": token, "consent": True, "name": "Léo", "hero": "m", "kids": 8, "town": "Bourg-Test", "ref": "test"})
    sid = urllib.parse.parse_qs(urllib.parse.urlparse(c["url"]).query)["id"][0]
    urllib.request.urlopen(BASE + "/fake-checkout?id=" + sid + "&pay=1").read()
    return call("/api/unlock", {"session": sid, "first": True})

async def main():
    subprocess.run([sys.executable, str(ROOT / "dev" / "build.py"), "--mail"], check=True)
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "osm-fixture.json").write_text(json.dumps(fixture), encoding="utf-8")
    seq = "".join("\x1e" + json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [e["lon"], e["lat"]]},
                   "properties": dict(e["tags"], **{"@type": e["type"], "@id": e["id"]})}) + "\n" for e in fixture["elements"])
    (ROOT / "dist" / "fixture.geojsonseq").write_text(seq, encoding="utf-8")
    for port in (PORT, PORT_OFF): (ROOT / "dist" / f"serve-{port}.log").write_text("", encoding="utf-8")
    subprocess.run(["node", str(ROOT / "dev" / "places" / "build.mjs"), str(ROOT / "dist" / "fixture.geojsonseq"), str(ROOT / "site" / "places")], check=True, stdout=subprocess.DEVNULL)
    srv = serve(PORT, KV_PAGE="3")
    errs = []
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()

            # 1. the field on the form: optional, last before the button, with its notice
            calls = []
            ctx, pg = await new_page(b, calls)
            await open_setup(pg, "Arthur")
            f = pg.locator("#mail-to")
            check(await f.count() == 1 and await f.get_attribute("type") == "email" and await f.get_attribute("autocomplete") == "email"
                  and await f.get_attribute("inputmode") == "email" and await f.get_attribute("required") is None, "formulaire : champ e-mail facultatif (type, autocomplete, inputmode)")
            box = await pg.inner_text(".mailbox")
            check("Recevoir mon aperçu par e-mail (facultatif)" in box and "puis un seul rappel une semaine plus tard si la quête n'est pas débloquée. Rien d'autre, et vous pouvez vous désinscrire en un clic." in box,
                  "formulaire : libellé et information")
            check(await pg.get_attribute(".mailbox a", "href") == "legal/confidentialite", "formulaire : lien vers la confidentialité")
            check(await pg.evaluate("document.querySelector('form.town button[type=submit]').previousElementSibling.classList.contains('mailbox')"), "formulaire : champ placé juste avant le bouton (ville)")
            await pg.click("label[for=mode-maison]")
            check(await pg.evaluate("document.getElementById('create-home').previousElementSibling.classList.contains('mailbox')"), "formulaire : champ placé juste avant le bouton (maison)")
            await pg.click("label[for=mode-ville]")
            # a wrong address: said under the field, nothing sent, the form stays
            await f.fill("parent@exemple")
            await pg.click("form.town button[type=submit]")
            await pg.wait_for_selector("#mail-to-err", timeout=3000)
            check("videz le champ pour continuer sans e-mail" in await pg.inner_text("#mail-to-err") and await pg.evaluate("document.getElementById('app').dataset.screen") == "setup",
                  "adresse invalide : message doux sous le champ, on reste sur le formulaire")
            await start_by_address(pg)
            await pg.wait_for_timeout(300)
            check(await pg.evaluate("document.getElementById('app').dataset.screen") == "setup", "adresse invalide : la recherche d'adresse ne part pas non plus")
            # emptied: the preview is made, no e-mail at all
            await f.fill("")
            await start_by_address(pg)
            await pg.wait_for_selector("text=Ce qui vous attend", timeout=10000)
            await pg.wait_for_timeout(500)
            check(not calls and not mails(), "adresse vidée : aperçu créé, aucun appel ni e-mail")
            check(await pg.locator("#mail-keep").count() == 1 and not await pg.locator("#mail-keep").is_visible() and await pg.locator(".keep button:has-text('Envoyer à l')").count() == 1,
                  "aperçu : champ e-mail replié dans « Gardez cet aperçu », à côté des deux boutons")
            await pg.click(".keep button:has-text(\"M'envoyer l'aperçu\")")
            kp = await pg.inner_text(".keep")
            check(await pg.locator("#mail-keep").is_visible() and "Recevoir l'aperçu par e-mail" in kp and "un seul rappel une semaine plus tard" in kp
                  and await pg.locator(".keep a[href^='mailto:']").count() == 1, "« M'envoyer l'aperçu » : le champ, l'information, et l'application e-mail en second choix")
            await ctx.close()

            # 2. the address given on the form: the e-mail goes after the preview is shown
            calls = []
            ctx, pg = await new_page(b, calls)
            await open_setup(pg, "Arthur")
            await pg.fill("#mail-to", "  Parent.Test@Exemple.fr ")
            await start_by_address(pg)
            await pg.wait_for_selector("text=Ce qui vous attend", timeout=10000)
            await pg.wait_for_selector("text=Aperçu envoyé à Parent.Test@Exemple.fr", timeout=8000)
            check(await pg.locator("#mail-keep").count() == 0, "aperçu : confirmation discrète à la place du champ")
            store = await pg.evaluate("JSON.stringify(localStorage)+JSON.stringify(sessionStorage)")
            check("exemple.fr" not in store.lower(), "l'adresse n'est pas gardée dans le stockage du navigateur")
            ms = mails()
            check(len(ms) == 1 and ms[0]["to"] == ["parent.test@exemple.fr"] and ms[0]["subject"] == "L'aperçu de la quête d'Arthur", "e-mail n°1 envoyé : " + (ms[0]["subject"] if ms else "aucun"))
            m1 = ms[0]
            link = link_of(m1)
            check("&n=Arthur&h=m&k=8&v=Bourg-Test&ref=mail" in link and link.startswith(BASE + "/?apercu="), "e-mail n°1 : le lien de l'aperçu " + link[-60:])
            check("à Bourg-Test" in m1["text"] and "24,90 €" in m1["text"] and "une seule autre fois" in m1["text"] and m1["from"]["email"] == "bonjour@maquetelegendaire.fr"
                  and m1["replyTo"]["email"] == "maquetelegendaire@gmail.com", "e-mail n°1 : contenu, prix, expéditeur, réponse")
            check(not re.search(r"promo|NOEL", m1["html"] + m1["text"], re.I), "e-mail n°1 : aucun code promo")
            check(m1["headers"].get("List-Unsubscribe-Post") == "List-Unsubscribe=One-Click" and "/api/rappel/stop?id=" in stop_of(m1) and stop_of(m1) in m1["html"].replace("&amp;", "&"),
                  "e-mail n°1 : lien de désinscription (en-tête et pied)")
            token = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)["apercu"][0]
            check(token == await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).token"), "e-mail n°1 : le jeton de cet aperçu")
            check(len(records()) == 1, "un enregistrement de rappel")
            await ctx.close()

            # 3. the link opens the preview in a new browser, and counts mail-retour
            ctx, pg = await new_page(b)
            await pg.goto(link)
            await pg.wait_for_selector("text=Ce qui vous attend", timeout=10000)
            body = await pg.inner_text("body")
            check("La quête d'Arthur" in body and "Bourg-Test" in body and "Débloquer la quête" in body, "le lien rouvre l'aperçu dans un navigateur neuf")
            # the same field in « Gardez cet aperçu »
            await pg.click(".keep button:has-text(\"M'envoyer l'aperçu\")")
            await pg.fill("#mail-keep", "autre.parent@exemple.fr")
            await pg.click(".mailform button")
            await pg.wait_for_selector("text=Aperçu envoyé à autre.parent@exemple.fr", timeout=8000)
            check(len(mails()) == 2 and mails()[1]["to"] == ["autre.parent@exemple.fr"], "« Gardez cet aperçu » : e-mail envoyé")
            await pg.screenshot(path=str(ROOT / "dist" / "mail-apercu.png"))
            # an e-mail that cannot go: said, and the preview stays usable
            call("/__brevo?fail=500")
            await pg.evaluate("localStorage.clear()")
            await pg.goto(link.replace("ref=mail", "ref=x"))
            await pg.wait_for_selector("#mail-keep", state="attached", timeout=10000)
            await pg.click(".keep button:has-text(\"M'envoyer l'aperçu\")")
            await pg.fill("#mail-keep", "panne@exemple.fr")
            await pg.click(".mailform button")
            await pg.wait_for_selector("text=L'e-mail n'a pas pu partir : gardez ce lien.", timeout=8000)
            check(await pg.locator("#mail-keep").is_visible() and await pg.locator(".keep a[href^='mailto:']").count() == 1, "échec d'envoi (502) : message visible, on peut réessayer ou garder le lien")
            kept = [json.loads(v["v"]) for v in call("/__kv?prefix=rappel:")[1].values()]
            failed = [r for r in kept if r["email"] == "panne@exemple.fr"]
            check(len(kept) == 3 and len(failed) == 1 and failed[0]["st"] == "echec" and failed[0]["err"]["status"] == 500,
                  "échec d'envoi : la demande est gardée, marquée « échec » (pour un renvoi depuis l'espace)")
            call("/__brevo?fail=0")
            # 429: three requests for this address today already
            for _ in range(3): call("/api/rappel", {"email": "limite@exemple.fr", "apercu": token})
            await pg.fill("#mail-keep", "limite@exemple.fr")
            await pg.click(".mailform button")
            await pg.wait_for_selector("text=Cette adresse a déjà reçu plusieurs aperçus aujourd'hui : réessayez demain, ou gardez ce lien.", timeout=8000)
            check(await pg.locator(".mailfail").count() == 1, "limite atteinte (429) : son propre message")
            # 503: the cap of the day
            day = call("/__kv?prefix=rappel-jour:")[1]["rappel-jour:" + today()]["v"]
            call("/__kv", {"key": "rappel-jour:" + today(), "value": "200", "options": {"expirationTtl": 172800}})
            await pg.fill("#mail-keep", "plafond@exemple.fr")
            await pg.click(".mailform button")
            await pg.wait_for_selector("text=L'envoi par e-mail est momentanément indisponible : gardez ce lien.", timeout=8000)
            check(await pg.locator(".mailfail").count() == 1 and await pg.locator(".keep a[href^='mailto:']").count() == 1, "service complet (503) : son propre message, le lien reste")
            call("/__kv", {"key": "rappel-jour:" + today(), "value": day, "options": {"expirationTtl": 172800}})
            for k, v in call("/__kv?prefix=rappel:")[1].items():   # keep the next counts simple
                if json.loads(v["v"])["email"] in ("panne@exemple.fr", "limite@exemple.fr"): call("/__kv?key=" + urllib.parse.quote(k), method="DELETE")
            errs += pg.errs
            await ctx.close()

            # 4. at home, field left empty: no call
            calls = []
            ctx, pg = await new_page(b, calls)
            await open_setup(pg, "Léa")
            await pg.click("label[for=mode-maison]")
            await pg.click("#create-home")
            await pg.wait_for_selector("text=Ce qui vous attend", timeout=10000)
            await pg.wait_for_timeout(400)
            check(not calls, "champ vide (maison) : aucun appel à /api/rappel")
            errs += pg.errs
            await ctx.close()

            # 5. the server's checks
            call("/__mails?clear=1")
            _, home = call("/api/preview", {"indoor": True})
            bad = home["token"][:-3] + ("AAA" if home["token"][-3:] != "AAA" else "BBB")
            check(call("/api/rappel", {"email": "x@exemple.fr", "apercu": bad}) == (400, {"ok": False, "reason": "token"}), "jeton d'aperçu trafiqué : refusé")
            for addr in ["x@exemple", "x@exemple.fr\nBcc: y@exemple.fr", "x y@exemple.fr", "a" * 250 + "@exemple.fr"]:
                check(call("/api/rappel", {"email": addr, "apercu": home["token"]})[1].get("reason") == "email", "adresse refusée : " + repr(addr[:30]))
            check(not mails(), "aucun e-mail pour les demandes refusées")
            call("/__geo?nom=" + urllib.parse.quote("<b>x</b>"))
            _, out = call("/api/preview", {"start": {"lat": 48.5, "lon": 7.47}})
            check(call("/api/rappel", {"email": "html@exemple.fr", "apercu": out["token"], "n": "<b>x</b>", "ref": "moi"})[0] == 200, "prénom et commune piégés : envoyé")
            m = mails()[-1]
            check("<b>x</b>" not in m["html"] and "&lt;b&gt;x&lt;/b&gt;" in m["html"] and m["subject"] == "L'aperçu de votre quête d'anniversaire", "échappement HTML : prénom écarté, commune échappée")
            call("/__geo?nom=Bourg-Test")
            # anti-abuse: 3 per address per 24 hours, and a cap for the day
            codes = [call("/api/rappel", {"email": "trois@exemple.fr", "apercu": home["token"]})[0] for _ in range(4)]
            check(codes == [200, 200, 200, 429], "limite : 3 demandes par adresse en 24 h " + str(codes))
            sent_today = int(call("/__kv?prefix=rappel-jour:")[1]["rappel-jour:" + today()]["v"])
            call("/__kv", {"key": "rappel-jour:" + today(), "value": "200", "options": {"expirationTtl": 172800}})
            check(call("/api/rappel", {"email": "plafond@exemple.fr", "apercu": home["token"]}) == (503, {"ok": False, "reason": "full"}), "plafond du jour : indisponible")
            call("/__kv", {"key": "rappel-jour:" + today(), "value": str(sent_today), "options": {"expirationTtl": 172800}})

            # 6. the reminder: not before 7 days, once at 7 days; none after payment or unsubscribe
            call("/__mails?clear=1")
            tokens = {}
            for who in ["r1", "r2", "r3", "r4", "r5", "paye", "stop", "parti"]:
                _, pv = call("/api/preview", {"indoor": True})
                tokens[who] = pv["token"]
                check(call("/api/rappel", {"email": who + "@exemple.fr", "apercu": pv["token"], "n": "Léo", "ref": "test"})[0] == 200, "demande " + who)
            ms = {x["to"][0].split("@")[0]: x for x in mails()}
            code, unl = pay(tokens["paye"])
            # paid, but the tab was closed during Stripe's redirect: no /api/unlock, the request stays until the cron
            _, c = call("/api/checkout", {"token": tokens["parti"], "consent": True, "name": "Léo", "hero": "m", "kids": 8, "town": "", "ref": "test"})
            urllib.request.urlopen(urllib.request.Request(c["url"].replace("/fake-checkout?", "/fake-checkout?pay=1&"), method="HEAD"))
            time.sleep(0.4)
            kvs = call("/__kv?prefix=rappel")[1]
            check(unl.get("ok") is True and set(unl) == {"ok", "quest", "name", "hero", "kids", "town"}, "paiement : la quête s'ouvre, réponse inchangée")
            check(not any(k.startswith("rappel:") and json.loads(v["v"])["email"] == "paye@exemple.fr" for k, v in kvs.items()) and any(k.startswith("rappel-paye:") for k in kvs),
                  "paiement : demande de rappel effacée tout de suite")
            # unsubscribe in the browser
            ctx, pg = await new_page(b)
            good = stop_of(ms["stop"])
            r = await pg.goto(good[:-1] + ("0" if good[-1] != "0" else "1"))
            check(r.status == 403 and "Lien non valable" in await pg.inner_text("body"), "désinscription : signature fausse refusée")
            r = await pg.goto(stop_of(ms["stop"]))
            check(r.status == 200 and "C'est noté : vous ne recevrez pas de rappel." in await pg.inner_text("body"), "désinscription : page de confirmation")
            await pg.screenshot(path=str(ROOT / "dist" / "mail-stop.png"))
            r = await pg.goto(stop_of(ms["stop"]))
            check(r.status == 200, "désinscription : fonctionne encore si déjà effacée")
            await ctx.close()
            check(call(stop_of(ms["r5"])[len(BASE):], {"List-Unsubscribe": "One-Click"})[0] == 200, "désinscription en un clic (POST) : acceptée")
            left = {json.loads(v["v"])["email"].split("@")[0] for k, v in call("/__kv?prefix=rappel:")[1].items()}
            check({"r1", "r2", "r3", "r4", "parti"} <= left and not {"paye", "stop", "r5"} & left, "restent à relancer : " + ", ".join(sorted(left)))
            left.discard("parti")   # paid without coming back: Stripe says so at the cron
            call("/__mails?clear=1")
            call("/__clock?days=6.9")
            check(call("/__cron")[1]["sent"] == 0, "rappel : rien avant 7 jours")
            call("/__clock?days=7.05")
            res = call("/__cron")[1]
            ms2 = mails()
            got = sorted(x["to"][0].split("@")[0] for x in ms2)
            check(res["sent"] == len(left) and sorted(got) == sorted(left), f"rappel à 7 jours : un par demande restante ({res['sent']}) {got}")
            check("paye" not in got and "stop" not in got and "r5" not in got, "rappel : aucun après paiement ni désinscription")
            check("parti" not in got, "rappel : aucun après un paiement sans retour sur le site (vérifié auprès de Stripe)")
            rm = next(x for x in ms2 if x["to"] == ["r1@exemple.fr"])
            check(rm["subject"] == "La quête de Léo vous attend" and "C'est le seul rappel que vous recevrez" in rm["text"] and "nous vous remboursons" in rm["text"]
                  and "Le lien de la quête, valable au moins douze mois" in rm["text"] and tokens["r1"] in rm["text"] and not re.search(r"promo|NOEL", rm["html"], re.I),
                  "e-mail n°2 : objet, garanties, lien, seul rappel")
            check(not [k for k in records()], "enregistrements supprimés après le rappel")
            check(call("/__cron")[1]["sent"] == 0, "rappel : jamais deux fois")
            with open(ROOT / "dist" / "mail-1.html", "w", encoding="utf-8") as fh: fh.write(m1["html"])
            with open(ROOT / "dist" / "mail-2.html", "w", encoding="utf-8") as fh: fh.write(rm["html"])
            call("/__clock?days=0")

            # 6b. the owner's private page: section « E-mails » (Brevo's log, faked by dev/serve.mjs)
            call("/__mails?clear=1")
            for k in call("/__kv?prefix=rappel")[1]: call("/__kv?key=" + urllib.parse.quote(k), method="DELETE")
            etok = {}
            for who in ["livre", "rebond", "bloque", "attente", "refus"]:
                _, pv = call("/api/preview", {"indoor": True})
                etok[who] = pv["token"]
                call("/__brevo?fail=" + ("400" if who == "refus" else "0"))
                check(call("/api/rappel", {"email": who + "@exemple.fr", "apercu": pv["token"], "n": "Léo"})[0] == (502 if who == "refus" else 200), "espace : demande " + who)
            call("/__brevo?fail=0")
            call("/__brevo-status?to=livre@exemple.fr&event=delivered")
            call("/__brevo-status?to=rebond@exemple.fr&event=hardBounces&reason=" + urllib.parse.quote("550 5.1.1 user unknown"))
            call("/__brevo-status?to=bloque@exemple.fr&event=blocked&reason=" + urllib.parse.quote("domaine d'envoi non authentifié"))
            first = {m["to"][0]: m for m in mails()}
            for body in [{}, {"id": "test", "code": "TEST-CODE-0000-0001"}, {"id": "nathan", "code": "TEST-CODE-0000-0000"}]:
                for path in ["/api/espace/mails", "/api/espace/renvoi"]:
                    code, j = call(path, dict(body, email="livre@exemple.fr"))
                    check(code == 403 and "exemple" not in json.dumps(j), f"espace : {path} sans le bon code → 403, aucune adresse")
            calls0 = call("/__brevo-events")[1]["calls"]
            ctx, ep = await new_page(b)
            await ep.goto(BASE + "/espace/")
            check(await ep.get_attribute("meta[name=robots]", "content") == "noindex, nofollow", "espace : noindex")
            await ep.fill("#id", "test"); await ep.fill("#code", "TEST-CODE-0000-0000")
            await ep.click("#go")
            await ep.wait_for_selector("#app:not([hidden])", timeout=8000)
            check(not await ep.evaluate("document.getElementById('mails-box').open") and call("/__brevo-events")[1]["calls"] == calls0,
                  "espace : section E-mails repliée, Brevo pas interrogé à l'ouverture")
            await ep.click("#mails-box summary")
            await ep.click("#m-load")
            await ep.wait_for_selector("#m-err .mi", timeout=8000)
            errt = await ep.inner_text("#m-err")
            check("rebond@exemple.fr" in errt and "Adresse inexistante ou refusée" in errt and "550 5.1.1 user unknown" in errt
                  and "bloque@exemple.fr" in errt and "Bloqué par Brevo" in errt and "refus@exemple.fr" in errt and "Refusé par Brevo au moment de l'envoi" in errt,
                  "espace : « En erreur » (rebond, bloqué, échec d'envoi) avec la raison")
            sentt = await ep.inner_text("#m-sent")
            check("livre@exemple.fr" in sentt and "Délivré" in sentt and "attente@exemple.fr" in sentt and "en attente de livraison" in sentt and "rebond@" not in sentt, "espace : « Partis » avec leur état")
            dem = await ep.inner_text("#m-dem")
            check(dem.count("@exemple.fr") == 5 and "Premier envoi échoué" in dem and "Rappel prévu le" in dem, "espace : « Demandes en cours »")
            summ = await ep.inner_text("#m-sum")
            check(re.sub(r"\s+", " ", summ).startswith("Partis 4 7 jours Délivrés 1 7 jours En erreur 3"), "espace : résumé " + re.sub(r"\s+", " ", summ))
            check(await ep.evaluate("[...document.querySelectorAll('#m-err .mi, #m-sent .mi, #m-dem .mi')].every(x => !x.querySelector('script,img,a'))"), "espace : textes insérés comme texte")
            # « Renvoyer l'aperçu » on the bounce: the same e-mail n°1, the reminder's date unchanged
            meta0 = {k: v["meta"] for k, v in call("/__kv?prefix=rappel:")[1].items()}
            item = ep.locator("#m-err .mi", has_text="rebond@exemple.fr")
            await item.locator("button").click()
            await item.locator(".res.ok").wait_for(timeout=8000)
            check("Aperçu renvoyé à rebond@exemple.fr" in await item.locator(".res").inner_text(), "espace : renvoi réussi, affiché")
            again = mails()[-1]
            check(again["to"] == ["rebond@exemple.fr"] and all(again[f] == first["rebond@exemple.fr"][f] for f in ("subject", "html", "text", "headers")),
                  "renvoi : même e-mail n°1 (gabarit, lien, désinscription)")
            meta1 = {k: v["meta"] for k, v in call("/__kv?prefix=rappel:")[1].items()}
            check(meta0 == meta1, "renvoi : date du rappel inchangée")
            await ep.screenshot(path=str(ROOT / "dist" / "espace-mails.png"), full_page=True)
            for _ in range(2):
                await item.locator("button").click()
                await ep.wait_for_timeout(300)
                await item.locator(".res.ok").wait_for(timeout=8000)
            check(await item.locator("button").is_disabled(), "renvoi : bouton désactivé après 3 renvois")
            rid = next(k for k, v in call("/__kv?prefix=rappel:")[1].items() if json.loads(v["v"])["email"] == "rebond@exemple.fr")[len("rappel:"):]
            n = len(mails())
            code, j = call("/api/espace/renvoi", {"id": "test", "code": "TEST-CODE-0000-0000", "rid": rid})
            check(code == 429 and j["reason"] == "limit" and len(mails()) == n, "renvoi : 4e refusé en 24 h, rien d'envoyé")
            # paid: the request is gone, the button says so, nothing is sent
            pay(etok["bloque"])
            item = ep.locator("#m-err .mi", has_text="bloque@exemple.fr")
            await item.locator("button").click()
            await item.locator(".res.err").wait_for(timeout=8000)
            check("Demande introuvable : le parent a payé" in await item.locator(".res").inner_text() and len(mails()) == n, "renvoi après paiement : introuvable, aucun envoi")
            # by address: an alias of a request is sent to the address given by the parent; an unknown one, nothing
            await ep.fill("#m-addr", "inconnu@exemple.fr"); await ep.click("#m-addr-go")
            await ep.wait_for_selector("#m-addr-msg.err", timeout=8000)
            check("Aucune demande en cours pour cette adresse" in await ep.inner_text("#m-addr-msg") and len(mails()) == n, "renvoi à une adresse qui n'a rien demandé : refusé")
            await ep.fill("#m-addr", "Livre+essai@exemple.fr"); await ep.click("#m-addr-go")
            await ep.wait_for_selector("#m-addr-msg.ok", timeout=8000)
            check("renvoyé à livre@exemple.fr" in await ep.inner_text("#m-addr-msg") and mails()[-1]["to"] == ["livre@exemple.fr"], "renvoi par adresse (alias) : à l'adresse de la demande")
            # Brevo's log down: said, the rest of the section still there
            call("/__brevo-events?fail=500")
            await ep.click("#m-load")
            await ep.wait_for_selector("#m-brevo:not([hidden])", timeout=8000)
            check("Brevo n'a pas répondu (code 500)" in await ep.inner_text("#m-brevo") and (await ep.inner_text("#m-dem")).count("@exemple.fr") == 4
                  and "refus@exemple.fr" in await ep.inner_text("#m-err") and await ep.locator("#tiles .tile").count() == 5, "Brevo en panne : message clair, le reste de l'espace fonctionne")
            call("/__brevo-events?fail=0")
            errs += ep.errs
            await ctx.close()
            # the failed first send, never sent again: one e-mail on the 7th day, saying so, then nothing
            call("/__mails?clear=1")
            call("/__clock?days=7.05")
            call("/__cron")
            late = [m for m in mails() if m["to"] == ["refus@exemple.fr"]]
            check(len(late) == 1 and "notre envoi n'avait pas pu partir" in late[0]["text"] and etok["refus"] in late[0]["text"] and late[0]["subject"] == "L'aperçu de la quête de Léo",
                  "échec d'envoi : un seul e-mail à 7 jours, qui le dit, avec le lien")
            check(call("/__cron")[1]["sent"] == 0 and not records(), "échec d'envoi : jamais deux fois, demande effacée")
            call("/__clock?days=0")

            # 7. anonymous counts for the report
            counts = call("/__counts")[1]
            events = {k.split("|")[1]: k.split("|")[2] for k in counts}
            check({"mail-demande", "mail-rappel", "mail-stop", "mail-retour"} <= set(events), "compteurs : " + ", ".join(sorted(e for e in events if e.startswith("mail"))))
            check(all(len(k.split("|")) == 4 for k in counts) and not any("exemple" in k for k in counts), "compteurs anonymes (aucune adresse)")
            check(any(k.split("|")[1] == "mail-demande" and k.split("|")[2] == "moi" for k in counts), "appareil du propriétaire : compté sous « moi » (hors rapport)")
            check(not errs, "aucune erreur JavaScript " + str(errs[:3]))
            await b.close()
    finally:
        srv.terminate()

    # 8. without the key: the route says « indisponible », the cron sends nothing
    srv = serve(PORT_OFF, NOBREVO="1")
    try:
        off = f"http://127.0.0.1:{PORT_OFF}"
        _, home = call("/api/preview", {"indoor": True}, base=off)
        check(call("/api/rappel", {"email": "a@exemple.fr", "apercu": home["token"]}, base=off) == (503, {"ok": False, "reason": "off"}), "sans BREVO_API_KEY : route indisponible")
        check(call("/__cron", base=off)[1]["sent"] == 0 and not call("/__mails", base=off)[1], "sans BREVO_API_KEY : aucun envoi")
    finally:
        srv.terminate()

    # 9. built without --mail (as in the repository): no field anywhere
    subprocess.run([sys.executable, str(ROOT / "dev" / "build.py")], check=True)
    srv = serve(PORT_OFF)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            ctx, pg = await new_page(b)
            await pg.goto(f"http://127.0.0.1:{PORT_OFF}/")
            await pg.click("button.big >> nth=0")
            await pg.fill("#hero-name", "Léa")
            check(await pg.locator("input[type=email]").count() == 0, "site construit sans --mail : pas de champ e-mail")
            await pg.click("label[for=mode-maison]")
            await pg.click("#create-home")
            await pg.wait_for_selector("text=Gardez cet aperçu", timeout=10000)
            check(await pg.locator("input[type=email]").count() == 0, "site construit sans --mail : pas de champ sur l'aperçu")
            priv = (ROOT / "site" / "legal" / "confidentialite.html").read_text(encoding="utf-8")
            check("Brevo" not in priv and "18 octobre 2026" in priv, "site construit sans --mail : confidentialité sans les e-mails")
            await b.close()
    finally:
        srv.terminate()

    logs = "".join((ROOT / "dist" / f"serve-{port}.log").read_text(encoding="utf-8") for port in (PORT, PORT_OFF))
    check("rappel" in logs and "renvoi" in logs and not re.search(r"exemple\.fr|@exemple", logs, re.I), "aucune adresse dans les journaux du serveur")
    print("\n" + ("TOUT EST BON" if not fails else f"{len(fails)} échec(s)"))
    sys.exit(1 if fails else 0)

asyncio.run(main())
