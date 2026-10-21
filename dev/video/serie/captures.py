# Screens of the real site for the "screen" videos (from 21 Oct 2026): the app runs locally (dev/serve.mjs,
# fake Stripe, OpenStreetMap answered by a few invented places), a 390 x 844 phone at 3x, and the key
# moments are saved as PNG in out/ecrans/. Place names and addresses are invented and blurred in the videos.
#   python3 dev/video/serie/captures.py
import asyncio, json, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
OUT = HERE / "out" / "ecrans"
PORT = 8793
BASE = f"http://127.0.0.1:{PORT}"
sys.path.insert(0, str(ROOT / "dev"))
E2E = (ROOT / "dev" / "e2e_paid.py").read_text()
# reuse the test's invented places, address search answers and place build
ns = {"__file__": str(ROOT / "dev" / "e2e_paid.py")}
exec(E2E.split("fails = []")[0], ns)
fixture, search, ban = ns["fixture"], ns["search"], ns["ban"]


async def shot(pg, name, full=False):
    await pg.wait_for_timeout(350)
    await pg.screenshot(path=str(OUT / f"{name}.png"), full_page=full)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "dist" / "osm-fixture.json").write_text(json.dumps(fixture), encoding="utf-8")
    seq = "".join("\x1e" + json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [e["lon"], e["lat"]]},
                   "properties": dict(e["tags"], **{"@type": e["type"], "@id": e["id"]})}) + "\n" for e in fixture["elements"])
    (ROOT / "dist" / "fixture.geojsonseq").write_text(seq, encoding="utf-8")
    subprocess.run(["node", str(ROOT / "dev/places/build.mjs"), str(ROOT / "dist/fixture.geojsonseq"), str(ROOT / "site/places")], check=True, capture_output=True)
    srv = subprocess.Popen(["node", str(ROOT / "dev/serve.mjs"), str(PORT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try: urllib.request.urlopen(BASE + "/", timeout=1); break
        except Exception: time.sleep(0.1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3)
            pg = await ctx.new_page()
            await pg.route("**/overpass-api.de/**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(fixture)))
            await pg.route("**/nominatim.openstreetmap.org/search**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(search)))
            await pg.route("**/data.geopf.fr/**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(ban)))
            await pg.goto(BASE + "/"); await pg.evaluate("document.fonts.ready")
            await shot(pg, "01-accueil")
            await pg.click("button.big >> nth=0")
            await shot(pg, "02-formulaire")
            await pg.fill("#hero-name", "Léo")
            await shot(pg, "03-prenom")
            await pg.evaluate("document.querySelectorAll('details.more').forEach(d=>d.open=true)")
            await pg.fill("#start-q", "place de l'église Bourg-Test")
            await pg.locator("#start-q").scroll_into_view_if_needed()
            await shot(pg, "04-adresse")
            await pg.click("button:has-text('Chercher')")
            await pg.wait_for_selector("text=Rue de l'Église 67999 Autre-Bourg", timeout=8000)
            await pg.click("text=Place de l'Église 67999 Bourg-Test")
            await pg.wait_for_selector("text=Ce qui vous attend", timeout=8000)
            await pg.evaluate("scrollTo(0,0)")
            await shot(pg, "05-apercu")
            await shot(pg, "05-apercu-long", full=True)
            await pg.evaluate("navigator.clipboard.writeText=t=>Promise.resolve();navigator.share=undefined")
            await pg.check("#consent")
            await pg.click("button:has-text('Débloquer la quête')")
            await pg.wait_for_url("**/fake-checkout**", timeout=5000)
            await pg.click("#pay")
            await pg.wait_for_selector("text=Le guide du Grand Maître", timeout=8000)
            await pg.evaluate("scrollTo(0,0)")
            await shot(pg, "06-guide")
            await pg.fill("#inv-date", "2026-11-21"); await pg.fill("#inv-time", "14:30"); await pg.fill("#inv-place", "Place de l'Église")
            await pg.click("text=Créer l'invitation")
            await pg.wait_for_function("(()=>{const i=document.querySelector('img.parchment');return i&&i.naturalWidth===1080})()", timeout=8000)
            await pg.locator("img.parchment").first.screenshot(path=str(OUT / "07-invitation.png"))
            await pg.click("text=Commencer la quête")
            await shot(pg, "08-debut")
            await pg.click("text=Première étape")
            await shot(pg, "09-etape")
            n = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).quest.steps.length")
            answers = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).quest.steps.map(s=>s.choices[s.answer])")
            for i in range(n):
                await pg.click("text=Nous y sommes")
                if i == 0: await shot(pg, "10-recit")
                await pg.click("text=Défi réussi")
                if i == 0: await shot(pg, "11-enigme")
                await pg.click(f"button.choice:has-text(\"{answers[i]}\")")
                await pg.wait_for_selector("text=Lettre gagnée", timeout=4000)
                if i == 0: await shot(pg, "12-lettre")
                await pg.click("text=Trouver le mot secret" if i == n - 1 else "text=Étape suivante")
            word = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).quest.word")
            await shot(pg, "13-mot-secret")
            await pg.fill("#secret", "fidèle" if word == "FIDELE" else word.lower())
            await pg.click("text=Ouvrir le Sceau")
            await pg.wait_for_selector("text=Le trésor est à vous", timeout=4000)
            await pg.evaluate("scrollTo(0,0)")
            await shot(pg, "14-tresor")
            await pg.click("text=Créer le diplôme en image")
            await pg.wait_for_function("(()=>{const i=document.querySelector('img.parchment');return i&&i.naturalWidth===1080})()", timeout=8000)
            await pg.locator("img.parchment").first.screenshot(path=str(OUT / "15-diplome.png"))
            await b.close()
    finally:
        srv.terminate()
    print("\n".join(sorted(x.name for x in OUT.glob("*.png"))))

asyncio.run(main())
