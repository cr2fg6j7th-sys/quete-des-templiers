# Images of the e-mails (the preview and its reminder): python3 dev/video/mail.py -> dev/static/mail-*.{png,jpg}
# (copied to the site by build.py; the e-mails load them from the site, see mailOf in dev/worker.js).
# mail-entete.png  the header band: seal + « Ma Quête Légendaire » (600 x 112, drawn at 2x)
# mail-quete.jpg   the picture of the preview e-mail (the children running, from accueil-defi.webp)
# mail-rappel.jpg  the picture of the reminder (the children around the map, from accueil-troupe.webp)
# mail-dragon.png  the dragon pointing at the reader, beside the list of what the quest holds
# The images must stay at these addresses: e-mails already sent load them.
import asyncio
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
STATIC = HERE.parent / "static"
SEAL = (HERE / "og.py").read_text(encoding="utf-8").split('SEAL = """', 1)[1].split('"""', 1)[0]

HEAD = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:"UnifrakturMaguntia";src:url({(ROOT / "fonts" / "UnifrakturMaguntia-Book.woff").as_uri()}) format("woff")}}
@font-face{{font-family:"Alegreya Sans SC";src:url({(ROOT / "fonts" / "AlegreyaSansSC-Bold.woff").as_uri()}) format("woff");font-weight:700}}
html,body{{margin:0;background:#192342}}
#h{{width:600px;height:112px;box-sizing:border-box;padding:0 28px;background:#192342;display:flex;align-items:center;gap:16px}}
#h svg{{width:68px;height:68px;flex:none}}
.k{{font-family:"Alegreya Sans SC",sans-serif;font-weight:700;font-size:13px;letter-spacing:.14em;color:#e9c46a;margin:0 0 2px 2px}}
.w{{font-family:"UnifrakturMaguntia",serif;font-size:38px;line-height:1.05;color:#fffaf0;white-space:nowrap}}
</style></head><body><div id="h">{SEAL}<div><div class="k">ANNIVERSAIRE 7-10 ANS</div><div class="w">Ma Quête Légendaire</div></div></div></body></html>"""


def crop(src, out, width, ratio, top):
    im = Image.open(STATIC / src).convert("RGB")
    h = round(im.width * ratio)
    im = im.crop((0, top, im.width, top + h))
    if im.width > width:
        im = im.resize((width, round(width * ratio)), Image.LANCZOS)
    im.save(STATIC / out, quality=74, optimize=True, progressive=True)


async def main():
    tmp = HERE / "_mail-entete.html"
    tmp.write_text(HEAD, encoding="utf-8")
    try:
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 600, "height": 112}, device_scale_factor=2)
            await pg.goto(tmp.as_uri())
            await pg.evaluate("document.fonts.ready")
            await (await pg.query_selector("#h")).screenshot(path=str(STATIC / "mail-entete.png"))
            await b.close()
    finally:
        tmp.unlink()
    Image.open(STATIC / "mail-entete.png").convert("RGB").quantize(64).save(STATIC / "mail-entete.png", optimize=True)
    # 600 x 270 in the e-mail, drawn at about 2x (the source is 1136 px wide) and 1.2x
    crop("accueil-defi.webp", "mail-quete.jpg", 1136, 0.45, 70)
    crop("accueil-troupe.webp", "mail-rappel.jpg", 720, 0.45, 170)
    # 76 px wide in the e-mail, drawn at 2x, on the parchment of its box (#f7f0df): no transparency to band
    d = Image.open(STATIC / "dragon-montre.webp").convert("RGBA")
    d = d.resize((152, round(152 * d.height / d.width)), Image.LANCZOS)
    bg = Image.new("RGBA", d.size, (0xf7, 0xf0, 0xdf, 255))
    bg.alpha_composite(d)
    bg.convert("RGB").quantize(256).save(STATIC / "mail-dragon.png", optimize=True)
    for f in ("mail-entete.png", "mail-quete.jpg", "mail-rappel.jpg", "mail-dragon.png"):
        print(f"dev/static/{f}  {(STATIC / f).stat().st_size // 1024} Ko")

asyncio.run(main())
