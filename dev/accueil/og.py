# Link preview image of the future home page (1200 x 630): dev/accueil/og-accueil.png
#   python3 dev/accueil/og.py
# Same house style as the site: stone, ink, wax seal, gold; the brand in UnifrakturMaguntia.
import asyncio, re
from pathlib import Path
from playwright.async_api import async_playwright
HERE = Path(__file__).parent
ROOT = HERE.parents[1]
seal = re.search(r'<symbol id="sceau".*?</symbol>', (HERE / "accueil.html").read_text(encoding="utf-8"), re.S).group(0)
F = (ROOT / "fonts").as_uri()
HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:U;src:url({F}/UnifrakturMaguntia-Book.woff)}}
@font-face{{font-family:A;src:url({F}/AlegreyaSans-Bold.woff);font-weight:700}}
@font-face{{font-family:A;src:url({F}/AlegreyaSans-Regular.woff);font-weight:400}}
@font-face{{font-family:S;src:url({F}/AlegreyaSansSC-Bold.woff);font-weight:700}}
*{{margin:0;box-sizing:border-box}}
body{{width:1200px;height:630px;background:#1b2547;color:#fffaf0;font-family:A;display:flex;align-items:center;gap:56px;padding:0 80px;
  background-image:radial-gradient(ellipse 70% 80% at 80% 50%,#2b3770 0%,#1b2547 60%,#11152a 100%)}}
svg{{width:250px;height:250px;flex:none;filter:drop-shadow(0 8px 18px rgba(0,0,0,.45))}}
.b{{font-family:U;font-size:74px;line-height:1;color:#f0a3ac}}
h1{{font-weight:700;font-size:54px;line-height:1.08;margin-top:22px}}
p{{font-family:S;font-size:28px;letter-spacing:.08em;color:#e9c46a;margin-top:26px}}
</style></head><body>
<svg viewBox="-30 -30 60 60">{seal.replace('<symbol id="sceau" viewBox="-30 -30 60 60">','').replace('</symbol>','').replace('var(--rose)','#b8505c')}</svg>
<div><div class="b">Ma Quête Légendaire</div><h1>Des chasses au trésor d'anniversaire pour les 5 à 12 ans</h1>
<p>Dans votre ville · prêtes en 2 minutes</p></div></body></html>"""

async def main():
    page = HERE / "_og.html"; page.write_text(HTML, encoding="utf-8")
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(viewport={"width": 1200, "height": 630})
        await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(300)
        await pg.screenshot(path=str(HERE / "og-accueil.png")); await b.close()
    page.unlink()
    print(HERE / "og-accueil.png")
asyncio.run(main())
