# Real-network check of the "Ville ou village" field (public APIs, no mock): suggestions, nearby
# communes, "Me localiser", the commune kept in the form. Screenshots and results in dist/apercu/.
#   python3 dev/build.py && python3 dev/e2e_communes.py
import asyncio, json, subprocess, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "apercu"
STATE = "localStorage.setItem('quete-templiers-v3',JSON.stringify({screen:'setup',name:'Léo',hero:'m',kids:8}))"

async def page(b, geo=None, scheme="light", w=390):
    ctx = await b.new_context(viewport={"width": w, "height": 900}, color_scheme=scheme, locale="fr-FR",
                              geolocation=geo, permissions=["geolocation"] if geo else [])
    await ctx.add_init_script("try{if(!sessionStorage.getItem('t')){sessionStorage.setItem('t','1');" + STATE + "}}catch(e){}")
    pg = await ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    await pg.goto("http://127.0.0.1:8766/index.html"); await pg.wait_for_selector("#commune")
    return ctx, pg, errs

async def chips(pg):
    await pg.wait_for_selector(".near:not([hidden]) .chip", timeout=20000)
    return await pg.eval_on_selector_all(".chip", "e=>e.map(x=>x.textContent)")

async def typed(pg, text):
    await pg.fill("#commune", ""); await pg.type("#commune", text, delay=70)
    await pg.wait_for_selector("#commune-list:not([hidden]) li", timeout=15000); await pg.wait_for_timeout(400)
    return await pg.eval_on_selector_all("#commune-list li", "e=>e.map(x=>x.textContent)")

async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1); res = {}
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            ctx, pg, errs = await page(b)
            res["obernai"] = await chips(pg); res["obernai_label"] = await pg.text_content(".near-lab")
            await pg.screenshot(path=str(OUT / "1-autour-obernai.png"), full_page=True)
            res["be"] = await typed(pg, "be"); await pg.screenshot(path=str(OUT / "2-be.png"))
            res["bern"] = await typed(pg, "bern"); await pg.screenshot(path=str(OUT / "3-bern.png"))
            res["sai"] = await typed(pg, "sai")
            res["metz"] = await typed(pg, "metz")
            res["stras"] = await typed(pg, "stras")
            await pg.keyboard.press("ArrowDown"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(1500)
            res["strasbourg"] = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).commune")
            res["hidden"] = await pg.eval_on_selector_all("form.town input[type=hidden]", "e=>e.map(x=>x.name+'='+x.value)")
            await pg.screenshot(path=str(OUT / "4-strasbourg.png"), full_page=True)
            await pg.click(".chip >> nth=1"); await pg.wait_for_timeout(300)
            res["chip"] = await pg.evaluate("JSON.parse(localStorage.getItem('quete-templiers-v3')).commune")
            await pg.screenshot(path=str(OUT / "5-puce.png"), full_page=True)
            res["errors_obernai"] = errs; await ctx.close()
            for name, geo in (("colmar", {"latitude": 48.0794, "longitude": 7.3585}), ("saint-die", {"latitude": 48.2847, "longitude": 6.9496}), ("paris", {"latitude": 48.8566, "longitude": 2.3522})):
                ctx, pg, errs = await page(b, geo=geo)
                await pg.click(".locate"); await pg.wait_for_timeout(1500)
                res[name + "_label"] = await pg.text_content(".near-lab"); res[name] = await chips(pg)
                await pg.screenshot(path=str(OUT / f"6-{name}.png"), full_page=True)
                res["errors_" + name] = errs; await ctx.close()
            ctx, pg, errs = await page(b, scheme="dark"); await chips(pg); await typed(pg, "ober")
            await pg.screenshot(path=str(OUT / "7-sombre.png")); await ctx.close()
            await b.close()
    finally:
        srv.terminate()
    (OUT / "resultats.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))

asyncio.run(main())
