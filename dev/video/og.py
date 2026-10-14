# Link preview image and icons: python3 dev/video/og.py -> dev/static/ (copied to the site by build.py)
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).parent
OUT = HERE.parent / "static"
SEAL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="-30 -30 60 60">
<path d="M25.0 -1.4Q26.0 0.0 26.8 1.6Q27.5 3.1 26.4 4.4Q25.4 5.8 24.1 6.9Q22.9 8.0 22.9 9.5Q23.0 11.1 22.9 12.7Q22.8 14.3 21.2 15.0Q19.6 15.7 18.1 16.1Q16.6 16.6 16.2 18.2Q15.7 19.7 15.1 21.3Q14.4 22.9 12.8 23.1Q11.2 23.2 9.6 23.1Q8.1 23.0 6.9 24.2Q5.8 25.4 4.5 26.5Q3.1 27.5 1.5 26.7Q0.0 25.9 -1.3 24.9Q-2.7 23.9 -4.2 24.3Q-5.6 24.7 -7.2 25.0Q-8.8 25.3 -9.9 23.9Q-10.9 22.6 -11.7 21.3Q-12.6 20.0 -14.2 19.9Q-15.9 19.9 -17.6 19.6Q-19.3 19.3 -19.8 17.7Q-20.3 16.2 -20.5 14.6Q-20.7 13.0 -22.1 12.2Q-23.5 11.3 -24.7 10.2Q-26.0 9.1 -25.5 7.4Q-25.0 5.7 -24.3 4.2Q-23.6 2.7 -24.4 1.3Q-25.2 0.0 -25.9 -1.5Q-26.5 -3.0 -25.5 -4.3Q-24.5 -5.6 -23.5 -6.7Q-22.4 -7.9 -22.8 -9.5Q-23.1 -11.1 -23.2 -12.9Q-23.3 -14.6 -21.8 -15.4Q-20.4 -16.3 -18.8 -16.8Q-17.3 -17.3 -16.7 -18.8Q-16.2 -20.3 -15.4 -21.7Q-14.5 -23.1 -12.8 -23.0Q-11.0 -22.9 -9.4 -22.6Q-7.8 -22.3 -6.7 -23.4Q-5.6 -24.5 -4.3 -25.5Q-3.0 -26.6 -1.5 -26.0Q-0.0 -25.3 1.3 -24.6Q2.7 -23.8 4.2 -24.5Q5.8 -25.2 7.4 -25.7Q9.1 -26.1 10.2 -24.8Q11.3 -23.5 12.2 -22.1Q13.0 -20.7 14.5 -20.4Q16.1 -20.1 17.6 -19.7Q19.2 -19.2 19.4 -17.5Q19.7 -15.7 19.8 -14.1Q19.9 -12.5 21.3 -11.7Q22.6 -10.9 24.0 -9.9Q25.4 -8.9 25.1 -7.3Q24.9 -5.7 24.5 -4.2Q24.1 -2.7 25.0 -1.4Z" fill="#b8505c"/>
<circle r="17" fill="none" stroke="#fff" stroke-opacity=".35" stroke-width="1.2"/>
<path d="M-1.6-1.6-5-12H5L1.6-1.6 12-5V5L1.6 1.6 5 12H-5L-1.6 1.6-12 5V-5Z" fill="#fff" fill-opacity=".85"/>
</svg>
"""

async def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "icon.svg").write_text(SEAL, encoding="utf-8")
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1200, "height": 900})
        await pg.goto((HERE / "og.html").as_uri())
        await pg.evaluate("document.fonts.ready")
        await (await pg.query_selector("#og")).screenshot(path=str(OUT / "og.png"))
        await (await pg.query_selector("#icon")).screenshot(path=str(OUT / "apple-touch-icon.png"))
        await b.close()
    print("dev/static/ : og.png, apple-touch-icon.png, icon.svg")

asyncio.run(main())
