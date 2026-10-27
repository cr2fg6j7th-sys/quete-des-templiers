# Local preview of the future home page (dev/accueil/accueil.html), NOT the live site.
#   python3 dev/accueil/apercu.py            -> dist/accueil/index.html (+ fonts, icons) and screenshots
# It fills {{SITE}} like dev/build.py does, and copies what the page needs next to it, so the page opens
# from the disk. Screenshots (phone and computer, light and dark): dist/accueil/apercu-*.png
import asyncio, shutil, sys
from pathlib import Path
HERE = Path(__file__).parent
ROOT = HERE.parents[1]
OUT = ROOT / "dist" / "accueil"
SITE = "https://maquetelegendaire.fr"

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    html = (HERE / "accueil.html").read_text(encoding="utf-8").replace("{{SITE}}", SITE)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(ROOT / "fonts", OUT / "fonts", dirs_exist_ok=True)
    for f in ("favicon.ico", "icon.svg", "apple-touch-icon.png"):
        shutil.copy(ROOT / "dev" / "static" / f, OUT / f)
    if (HERE / "og-accueil.png").exists():
        shutil.copy(HERE / "og-accueil.png", OUT / "og-accueil.png")
    return OUT / "index.html"

async def shots(page):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, w, h, scheme in (("telephone", 390, 844, "light"), ("ordinateur", 1280, 800, "light"), ("telephone-sombre", 390, 844, "dark")):
            ctx = await b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme)
            pg = await ctx.new_page(); await pg.goto(page.as_uri()); await pg.wait_for_timeout(600)
            await pg.screenshot(path=str(OUT / f"apercu-{name}.png"), full_page=True)
            await ctx.close()
        await b.close()

if __name__ == "__main__":
    page = build()
    if "--sans-captures" not in sys.argv:
        asyncio.run(shots(page))
    print(page)
