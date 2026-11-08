# Full-page captures of the real app after the quest is created (390 px phone, 2x), for the
# scrolling phone videos of the website mockup. Same local setup as dev/video/serie/captures.py.
import asyncio, json, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent / 'ecrans'
PORT = 8797
BASE = f"http://127.0.0.1:{PORT}"
ns = {"__file__": str(ROOT / "dev" / "e2e_paid.py")}
exec((ROOT / "dev" / "e2e_paid.py").read_text().split("fails = []")[0], ns)
fixture = ns["fixture"]
search = json.loads(json.dumps(ns["search"]).replace("Bourg-Test", "Bourg-la-For\u00eat"))
ban = json.loads(json.dumps(ns["ban"]).replace("Bourg-Test", "Bourg-la-For\u00eat"))
NAME = "Gabriel"

async def shot(pg, name):
    await pg.wait_for_timeout(400)
    await pg.evaluate("scrollTo(0,0)")
    await pg.wait_for_timeout(150)
    await pg.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
    print("ok", name, await pg.evaluate("document.documentElement.scrollHeight"))

async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "dist").mkdir(exist_ok=True)
    (ROOT / "dist" / "osm-fixture.json").write_text(json.dumps(fixture), encoding="utf-8")
    seq = "".join("\x1e" + json.dumps({"type": "Feature", "geometry": {"type": "Point", "coordinates": [e["lon"], e["lat"]]},
                   "properties": dict(e["tags"], **{"@type": e["type"], "@id": e["id"]})}) + "\n" for e in fixture["elements"])
    (ROOT / "dist" / "fixture.geojsonseq").write_text(seq, encoding="utf-8")
    subprocess.run(["node", str(ROOT / "dev/places/build.mjs"), str(ROOT / "dist/fixture.geojsonseq"), str(ROOT / "site/places")], check=True, capture_output=True)
    srv = subprocess.Popen(["node", str(ROOT / "dev/serve.mjs"), str(PORT)], cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(80):
        try: urllib.request.urlopen(BASE + "/", timeout=1); break
        except Exception: time.sleep(0.1)
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            ctx = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
            pg = await ctx.new_page()
            await pg.route("**/overpass-api.de/**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(fixture)))
            await pg.route("**/nominatim.openstreetmap.org/search**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(search)))
            await pg.route("**/data.geopf.fr/**", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps(ban)))
            await pg.goto(BASE + "/"); await pg.evaluate("document.fonts.ready")
            await pg.click("button.big >> nth=0")
            await pg.fill("#hero-name", NAME)
            await pg.evaluate("document.querySelectorAll('details.more').forEach(d=>d.open=true)")
            await pg.fill("#start-q", "place de l'église Bourg-la-Forêt")
            await pg.click("button:has-text('Chercher')")
            await pg.wait_for_selector("text=Rue de l'Église 67999 Autre-Bourg", timeout=8000)
            await pg.click("text=Place de l'Église 67999 Bourg-la-Forêt")
            await pg.wait_for_selector("text=Ce qui vous attend", timeout=8000)
            await shot(pg, "01-apercu")
            await pg.evaluate("navigator.clipboard.writeText=t=>Promise.resolve();navigator.share=undefined")
            await pg.check("#consent")
            await pg.click("button:has-text('Débloquer la quête')")
            await pg.wait_for_url("**/fake-checkout**", timeout=5000)
            await pg.click("#pay")
            await pg.wait_for_selector("text=Le guide du Grand Maître", timeout=8000)
            await shot(pg, "02-guide")
            await pg.click("text=Commencer la quête")
            await shot(pg, "03-debut")
            await pg.click("text=Première étape")
            await shot(pg, "04-etape")
            n = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).quest.steps.length")
            answers = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).quest.steps.map(s=>s.choices[s.answer])")
            for i in range(n):
                await pg.click("text=Nous y sommes")
                if i == 0: await shot(pg, "05-recit")
                await pg.click("text=Défi réussi")
                if i == 0: await shot(pg, "06-enigme")
                await pg.click(f"button.choice:has-text(\"{answers[i]}\")")
                await pg.wait_for_selector("text=Lettre gagnée", timeout=4000)
                if i == 0: await shot(pg, "07-lettre")
                await pg.click("text=Trouver le mot secret" if i == n - 1 else "text=Étape suivante")
                if i == 0: await shot(pg, "08-etape2")
            word = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).quest.word")
            await shot(pg, "09-mot-secret")
            await pg.fill("#secret", "fidèle" if word == "FIDELE" else word.lower())
            await pg.click("text=Ouvrir le Sceau")
            await pg.wait_for_selector("text=Le trésor est à vous", timeout=4000)
            await shot(pg, "10-tresor")
            await b.close()
    finally:
        srv.terminate()

asyncio.run(main())
