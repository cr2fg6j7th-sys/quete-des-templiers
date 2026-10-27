# End-to-end test of the tester mode (before the opening): dev/serve.mjs with TESTEURS=1.
# The payment is hidden, the quest opens free, the questionnaire at the end is stored and readable
# by the weekly report. Run: python3 dev/e2e_testeurs.py
import asyncio, hashlib, json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8792
BASE = f"http://127.0.0.1:{PORT}"
fails = []
def check(cond, label):
    print(("ok   " if cond else "FAIL ") + label)
    if not cond: fails.append(label)

def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers={"content-type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")

async def main():
    srv = subprocess.Popen(["node", str(ROOT / "dev" / "serve.mjs"), str(PORT)], env=dict(os.environ, TESTEURS="1"),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(50):
        try: urllib.request.urlopen(BASE + "/", timeout=1); break
        except Exception: time.sleep(0.1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            errs = []
            ctx = await b.new_context(viewport={"width": 390, "height": 860})
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e: errs.append(str(e)))
            await pg.goto(BASE + "/?ref=instagram")
            await pg.click("button.big >> nth=0")
            await pg.fill("#hero-name", "Léa")
            await pg.click("text=Chevalière")
            await pg.click("text=Il pleut ?")
            await pg.wait_for_selector("text=quête à la maison", timeout=6000)
            body = await pg.inner_text("body")
            check("Devenir famille testeuse" in body and "La quête ouvre le 7 novembre" in body, "avant-première : bouton « Devenir famille testeuse »")
            check(await pg.locator("#consent").count() == 0 and "Débloquer la quête" not in body, "avant-première : paiement caché")
            await pg.screenshot(path=str(ROOT / "dist" / "t1-testeur.png"), full_page=True)
            await pg.click("button:has-text('Devenir famille testeuse')")
            await pg.wait_for_selector("text=Le guide du Grand Maître", timeout=6000)
            st = json.loads(await pg.evaluate("localStorage.getItem('quete-templiers-v3')"))
            check(st["unlocked"] and st["tester"] and st["quest"]["indoorOnly"] and not st["paid"], "quête offerte ouverte, sans paiement")
            # straight to the end of the quest
            await pg.evaluate("""(()=>{const k='quete-templiers-v3';const s=JSON.parse(localStorage.getItem(k));s.screen='diploma';localStorage.setItem(k,JSON.stringify(s));})()""")
            await pg.reload()
            await pg.wait_for_selector("text=Votre avis sur la quête", timeout=6000)
            await pg.click("button[aria-label='4 sur 5']")
            await pg.click(".avis button:has-text('adoré')")
            await pg.click(".avis button:has-text('juste bien')")
            await pg.click(".avis button:has-text('peut-être')")
            await pg.fill(".avis textarea >> nth=0", "Le frigo, ils ont hurlé de rire")
            await pg.fill(".avis textarea >> nth=1", "Une énigme | trop dure")
            await pg.check("#citer")
            await pg.click("button:has-text('Envoyer mon avis')")
            await pg.wait_for_selector("text=Indiquez votre prénom et votre nom", timeout=3000)
            check(True, "sans prénom ni nom : envoi bloqué")
            await pg.fill("#avis-prenom", "Julie")
            await pg.fill("#avis-nom", "Martin")
            await pg.fill("#avis-email", "julie.martin@exemple")
            await pg.click("button:has-text('Envoyer mon avis')")
            await pg.wait_for_selector("text=adresse e-mail ne semble pas complète", timeout=3000)
            check(True, "e-mail incomplet : envoi bloqué")
            await pg.fill("#avis-email", "Julie.Martin@exemple.fr")
            await pg.screenshot(path=str(ROOT / "dist" / "t2-questionnaire.png"), full_page=True)
            await pg.click("button:has-text('Envoyer mon avis')")
            await pg.wait_for_selector("text=Merci pour votre avis", timeout=6000)
            await pg.reload()
            await pg.wait_for_selector("text=Merci pour votre avis", timeout=6000)
            check(True, "questionnaire envoyé, une seule fois (gardé après rechargement)")
            # the report reads it
            key = hashlib.sha256(b"stats:sk_test_local").hexdigest()
            code, j = post("/api/stats", {"key": key, "days": 2})
            a = (j.get("avis") or [{}])[0]
            check(code == 200 and a.get("note") == 4 and a.get("enfants") == "adore" and a.get("prix") == "peut-etre" and a.get("maison")
                  and a.get("prenom") == "Julie" and a.get("nom") == "Martin" and a.get("email") == "julie.martin@exemple.fr" and a.get("citer") and a.get("ref") == "instagram" and a.get("etapes") == 6, "réponses stockées et lues par le rapport " + json.dumps(a, ensure_ascii=False)[:160])
            check("testeur" in str(j.get("days")) and "avis" in str(j.get("days")), "compteurs testeur et avis")
            code, _ = post("/api/avis", {})
            check(code == 400, "questionnaire vide : refusé")
            code, _ = post("/api/avis", {"note": 5, "prenom": "Julie", "nom": "Martin", "email": "pas-un-mail"})
            check(code == 400, "e-mail invalide : refusé par le serveur")
            code, _ = post("/api/testeur", {"token": "faux"})
            check(code == 400, "jeton trafiqué : refusé")
            # Nathan's private page
            code, _ = post("/api/espace", {"id": "test", "code": "TEST-CODE-0000-0001"})
            check(code == 403, "espace : mauvais code refusé")
            code, j = post("/api/espace", {"id": "test", "code": "test-code-0000-0000 "})
            check(code == 200 and j.get("testeurs") is True and (j.get("avis") or [{}])[0].get("email") == "julie.martin@exemple.fr", "espace : bon code (minuscules acceptées), avis lu")
            ep = await ctx.new_page()
            ep.on("pageerror", lambda e: errs.append(str(e)))
            await ep.goto(BASE + "/espace/")
            await ep.fill("#id", "test"); await ep.fill("#code", "MAUVAIS")
            await ep.click("#go")
            await ep.wait_for_selector("text=Identifiant ou code incorrect", timeout=6000)
            await ep.fill("#code", "TEST-CODE-0000-0000")
            await ep.click("#go")
            await ep.wait_for_selector("text=Julie Martin", timeout=6000)
            body = await ep.inner_text("body")
            check("julie.martin@exemple.fr" in body and "Le frigo" in body and "Avant-première active" in body, "espace : page avec nom, e-mail et réponses")
            await ep.screenshot(path=str(ROOT / "dist" / "t3-espace.png"), full_page=True)
            await ep.reload()
            await ep.wait_for_selector("text=Julie Martin", timeout=6000)
            check(True, "espace : reste connecté après rechargement")
            await ep.click("#logout")
            await ep.reload()
            await ep.wait_for_timeout(400)
            check(not await ep.is_visible("#app"), "espace : déconnexion")
            check(not errs, "aucune erreur JavaScript " + str(errs))
            await b.close()
    finally:
        srv.terminate()
    # without the variable: the routes are closed
    srv = subprocess.Popen(["node", str(ROOT / "dev" / "serve.mjs"), str(PORT)], env={k: v for k, v in os.environ.items() if k != "TESTEURS"},
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(50):
        try: urllib.request.urlopen(BASE + "/", timeout=1); break
        except Exception: time.sleep(0.1)
    try:
        code, j = post("/api/preview", {"indoor": True})
        check(j.get("testeur") is False, "sans TESTEURS : l'aperçu propose le paiement")
        code, _ = post("/api/testeur", {"token": j.get("token")})
        check(code == 403, "sans TESTEURS : quête offerte refusée")
        code, _ = post("/api/avis", {"note": 5})
        check(code == 403, "sans TESTEURS : questionnaire refusé")
    finally:
        srv.terminate()
    print("\nTOUT EST BON" if not fails else f"\n{len(fails)} ÉCHEC(S)")
    sys.exit(1 if fails else 0)

asyncio.run(main())
