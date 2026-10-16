# One print-ready PDF per shop: A5 recto + verso, 3 mm bleed, fonts embedded, vector text and QR codes.
import asyncio, re
from pathlib import Path
from playwright.async_api import async_playwright
from pypdf import PdfWriter, PdfReader

H = Path(__file__).parent
SRC, SVG, OUT = H / "root/project", H / "svg", H / "pdf"
FONTS = Path("/home/claude/quete-des-templiers/fonts").as_uri()
BLOBS = {"13a57c3c0a39487849c6c13408258883": "blason", "cb681d095f04ac9fef6c1d7895f8ee03": "labyrinthe-1",
  "a9b22e460e3ee99d1ec98a8395055784": "labyrinthe-2", "866828803f31c99a551a42be587b3f8e": "qr-f-boulangerie",
  "2eb368c5eb0f498b9f376d72c6f5ded3": "qr-f-deguisement", "9ec908d2ba93cff16953dac261e55127": "qr-f-jouets",
  "6e2481da5da458cc2a5b4f8371b05bcc": "qr-f-librairie", "0131447936635a1ebe4287e7d940a451": "qr-f-restaurant",
  "e54582dbdb057a9698ecf96b8d5b20ea": "qr-f-salle", "e44e519a3a96dffbc202aa15af1bce37": "qr-f-tourisme",
  "fb95573b4fb5926547c882e1dde5902e": "sceau"}
FLYERS = {
  "flyer-boulangerie": ("Main", "Verso"), "flyer-magasin-de-jouets": ("Jouets", "Verso"),
  "flyer-librairie-mediatheque": ("Librairie", "Verso"), "flyer-deguisements-fete": ("Deguisement", "Verso"),
  "flyer-tourisme-gites-campings": ("Tourisme", "Verso"), "flyer-restaurant": ("Restaurant", "RestaurantJeux"),
  "flyer-salle-attente": ("Salle", "SalleJeux")}
HEAD = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>
@font-face{{font-family:"UnifrakturMaguntia";src:url({FONTS}/UnifrakturMaguntia-Book.woff)}}
@font-face{{font-family:"Alegreya Sans";src:url({FONTS}/AlegreyaSans-Regular.woff);font-weight:400}}
@font-face{{font-family:"Alegreya Sans";src:url({FONTS}/AlegreyaSans-Italic.woff);font-weight:400;font-style:italic}}
@font-face{{font-family:"Alegreya Sans";src:url({FONTS}/AlegreyaSans-Bold.woff);font-weight:600 900}}
@font-face{{font-family:"Alegreya Sans SC";src:url({FONTS}/AlegreyaSansSC-Bold.woff);font-weight:700}}
@page{{size:154mm 216mm;margin:0}}
html,body{{margin:0;width:154mm;height:216mm;overflow:hidden;background:BG;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{position:absolute;left:3mm;top:3mm}}
</style></head><body><div class="page">"""

def page(name):
    s = (SRC / f"{name}.dc.html").read_text()
    body = re.search(r"<x-dc>(.*)</x-dc>", s, re.S).group(1)
    body = re.sub(r"<helmet>.*?</helmet>", "", body, flags=re.S)
    for k, v in BLOBS.items(): body = body.replace(f"/_blob/{k}", (SVG / f"{v}.svg").as_uri())
    assert "/_blob/" not in body and "{{" not in body, name
    bg = re.search(r"background: (#[0-9a-f]{6})", body).group(1)
    return HEAD.replace("BG", bg) + body + "</div></body></html>"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page()
        for out, (rec, ver) in FLYERS.items():
            w = PdfWriter()
            for i, name in enumerate((rec, ver)):
                f = OUT / f"_{name}.html"; f.write_text(page(name))
                await pg.goto(f.as_uri()); await pg.evaluate("document.fonts.ready")
                pdf = OUT / f"_{out}-{i}.pdf"
                await pg.pdf(path=str(pdf), prefer_css_page_size=True, print_background=True)
                for pp in PdfReader(str(pdf)).pages: w.add_page(pp)
            w.add_metadata({"/Title": f"Ma Quête Légendaire — {out.replace('flyer-','').replace('-',' ')} (A5 recto verso)", "/Author": "Ma Quête Légendaire"})
            w.write(str(OUT / f"{out}.pdf")); print(out, len(w.pages), "pages")
        await b.close()
    for f in OUT.glob("_*"): f.unlink()
asyncio.run(main())
