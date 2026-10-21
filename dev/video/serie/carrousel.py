# Renders the "trouve la clé dorée" carousel (5 slides, 1080 x 1350) -> out/carrousel-cle/<n>.jpg
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
HERE = Path(__file__).parent
REPO = HERE.parents[2]
OUT = HERE / "out" / "carrousel-cle"
IMG = (HERE / "img/cherche.jpg").as_uri()
KEY = [331, 804]          # where the key hides, scene space (1080 x 1440): at the foot of the fountain

def card(top, t, s="", eyebrow=""):
    e = f'<div class="eyebrow">{eyebrow}</div>' if eyebrow else ""
    s = f'<div class="s">{s}</div>' if s else ""
    return f'<div class="card" style="top:{top}px">{e}<div class="t">{t}</div>{s}</div>'

def chip(bottom, html):
    return f'<div class="chip" style="bottom:{bottom}px"><div>{html}</div></div>'

def num(n): return f'<div class="num">{n} / 5</div>'

SLIDES = [
    dict(zoom=1.55, cx=600, cy=780, ui=card(50, "Fête d'anniversaire au château : <b>trouve la clé dorée</b>", "Un jeu à faire avec votre enfant", "Cherche et trouve")
         + chip(70, "Elle ressemble à ça : KEY · Glisse") + num(1)),
    dict(ui=chip(40, "La clé est cachée quelque part… Chronomètre lancé !") + num(2)),
    dict(hint=[284, 679, 215], ui=card(40, "Indice : <b>elle a soif</b>", "Regardez près de l'eau…") + num(3)),
    dict(zoom=3.0, cx=KEY[0], cy=KEY[1] - 40, ring=True,
         ui=card(50, "Trouvée ! <b>En combien de secondes ?</b>", "Répondez en commentaire, votre enfant aussi") + num(4)),
    dict(end='<div class="brand">Ma Quête Légendaire</div>'
             '<div class="q">Et si son anniversaire devenait <b>une vraie quête</b> ?</div>'
             "<p>Le Grand Maître cache les indices dans les vrais lieux de votre ville : fontaine, église, vieille porte…</p>"
             "<ul><li><i></i><span>Votre enfant appelé <b>par son prénom</b></span></li><li><i></i><span>7 à 10 ans · prête en <b>2 minutes</b></span></li>"
             "<li><i></i><span>Il pleut ? Elle se joue <b>à la maison</b></span></li></ul>"
             '<div class="link"><b>maquetelegendaire.fr</b><small>Lien dans la bio</small></div>'
             '<div class="save">Enregistrez pour rejouer ce soir</div>'),
]

async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    page = HERE / "_carrousel.html"
    page.write_text((HERE / "carrousel.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/"))
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        for i, s in enumerate(SLIDES, 1):
            await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready")
            await pg.evaluate(f"show({json.dumps(dict(s, img=IMG, key=KEY), ensure_ascii=False)})")
            await pg.wait_for_timeout(400)
            await pg.screenshot(path=str(OUT / f"{i}.jpg"), type="jpeg", quality=92)
        await b.close()
    page.unlink()

asyncio.run(main())
