# Instagram carousels for parents (25 Oct 2026) -> out/carrousels/<slug>/<n>.jpg (1080 x 1350).
# Instagram favours carousels for saves and sends; each one is useful on its own (to save or to send to another
# parent) and ends on the quest, the free offer until 6 Nov and « send it / save it ».
#   python3 dev/video/serie/carrousel_ig.py [slug …]
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright
HERE = Path(__file__).parent
REPO = HERE.parents[2]
OUT = HERE / "out" / "carrousels"
IMG = HERE / "img"
HOME = (HERE.parent / "campagne/img/phone/home.jpg").as_uri()
NOMS = REPO / "audio/noms"
U = lambda n: (IMG / f"{n}.jpg").as_uri()


def cover(eb, title, sub, bg):
    return dict(bg=U(bg), veil='linear-gradient(rgba(17,21,42,.78),rgba(17,21,42,.25) 55%,rgba(17,21,42,.8))', html=f'<div class="wrap"><span class="eb">{eb}</span><h1>{title}</h1><p class="sub">{sub}</p>'
                               f'<span class="swipe">Glissez →</span></div>')


def step(seal, title, text, tip, bg, round_=False):
    t = f'<div class="tip">{tip}</div>' if tip else ""
    return dict(bg=U(bg), blur=True, veil="rgba(17,21,42,.25)",
                html=f'<div class="wrap"><div class="card"><span class="seal{" round" if round_ else ""}">{seal}</span>'
                     f'<h2>{title}</h2><p>{text}</p>{t}</div></div>')


def names(title, lst, bg):
    return dict(bg=U(bg), blur=True, veil="rgba(17,21,42,.3)",
                html=f'<div class="wrap"><div class="card"><h2 style="margin-top:0">{title}</h2>'
                     f'<div class="names">{"".join(f"<span>{n}</span>" for n in lst)}</div></div></div>')


def final(title, text, bg, ask="Envoyez-le à un parent"):
    return dict(bg=U(bg), blur=True, veil="rgba(17,21,42,.35)",
                html=f'<div class="wrap"><div class="final"><h2>{title}</h2>'
                     f'<div class="row"><div class="phone"><div><img src="{HOME}"></div></div><p style="max-width:470px">{text}</p></div>'
                     f'<span class="link">maquetelegendaire.fr</span>'
                     f'<span class="offer">Quête <b>offerte</b> jusqu\'au 6 novembre · écrivez <b>CHEVALIER</b></span>'
                     f'<div class="asks"><span>Enregistrez</span><span>{ask}</span></div></div></div>')


PRODUCT = ("Une chasse au trésor de chevaliers <b>dans les rues autour de chez vous</b>. Le Grand Maître appelle votre enfant "
           "<b>par son prénom</b>. Prête en 2 minutes, rien à imprimer.")

CARROUSELS = {
    "planning-2h": [
        cover("Anniversaire 7-10 ans", "Le planning de <b>2 heures</b>, minute par minute", "À enregistrer avant le jour J.", "ville"),
        step("14 h 00", "L'accueil", "Un petit jeu dès l'arrivée : chaque invité se choisit un <b>nom de chevalier</b>.",
             "Les retardataires ne ratent rien : le jeu se rejoint en cours.", "ville"),
        step("14 h 15", "La grande activité", "Le moment fort, quand ils ont le plus d'énergie : <b>chasse au trésor</b>, jeu de piste, grand jeu.",
             "Comptez environ 1 heure, c'est la durée idéale à 7-10 ans.", "ville"),
        step("15 h 15", "Le goûter", "Gâteau, bougies, cadeaux : après l'aventure, <b>ils ont faim</b> et se posent enfin.",
             "Gardez le gâteau pour après : avant, ils sont surexcités.", "gateau"),
        step("15 h 45", "Le jeu calme", "Un <b>blason à colorier</b>, un jeu de cartes : de quoi redescendre avant l'arrivée des parents.", "", "gateau"),
        step("16 h 00", "Le départ", "Les pochettes-surprises <b>près de la porte</b> : chacun repart sans que personne n'attende.", "", "gateau"),
        final("Et la grande activité&nbsp;?", PRODUCT, "ville", "Envoyez-le à un parent"),
    ],
    "erreurs": [
        cover("Parents, attention", "<b>5 erreurs</b> qui gâchent un anniversaire d'enfant", "Vous faites laquelle ?", "cherche"),
        step("1", "Trop d'invités", "La règle souvent citée par les parents : <b>son âge, plus un</b>. 8 ans, 9 invités.",
             "Au-delà, prévoyez un adulte de plus.", "cherche", True),
        step("2", "Pas de fil rouge", "Sans activité principale, 10 enfants <b>s'ennuient vite</b>… et inventent leurs propres jeux.",
             "Une seule grande activité suffit, le reste peut être libre.", "cherche", True),
        step("3", "Le gâteau trop tôt", "Du sucre dès l'arrivée, et l'après-midi devient <b>très agité</b>.",
             "Gâteau après la grande activité, pas avant.", "cherche", True),
        step("4", "Tout faire seul", "Dehors, comptez <b>un adulte pour cinq enfants</b> environ.",
             "Demandez à un ou deux parents de rester : ils disent rarement non.", "cherche", True),
        step("5", "Aucun plan B", "Météo, retard, enfant fatigué : sans plan B, <b>c'est vous qui improvisez</b>.",
             "Ayez toujours une version à la maison.", "cherche", True),
        final("La grande activité, <b>déjà prête</b>", PRODUCT + " Et s'il pleut, elle se joue à la maison.", "cherche"),
    ],
    "plan-b-pluie": [
        cover("Il pleut le jour J ?", "Le <b>plan B</b> en 5 minutes", "Pour ne rien annuler.", "pluie"),
        step("1", "Gardez la même histoire", "Ils attendaient une aventure : ne l'annulez pas, <b>déplacez-la</b> à l'intérieur.", "", "pluie", True),
        step("2", "Cachez 6 indices", "Sous un coussin, dans une chaussure, entre deux livres, au frigo… <b>5 minutes</b> suffisent.",
             "Une cachette par pièce : ça fait bouger tout le monde.", "pluie", True),
        step("3", "Des défis pour le salon", "Passer sans réveiller <b>le dragon endormi</b>, le pont-levis, la joute aux ballons.",
             "À genoux, personne ne tombe de haut.", "pluie", True),
        step("4", "Gardez le grand final", "Le mot secret, le trésor, le diplôme : <b>la fin reste la même</b>, dehors ou dedans.", "", "pluie", True),
        final("Le mode maison <b>est inclus</b>", "La quête de Ma Quête Légendaire se joue <b>dehors ou à la maison</b> : six cartes à cacher, "
              "les énigmes du Grand Maître font le reste.", "pluie"),
    ],
    "prenoms": [
        cover("Parents, testez", "Le Grand Maître connaît-il <b>le prénom</b> de votre enfant ?", "Il en prononce 1 500.", "lettre"),
        names("Garçons : <b>il les dit tous</b>", ["Gabriel", "Léo", "Raphaël", "Louis", "Arthur", "Jules", "Adam", "Maël", "Lucas",
                                                 "Hugo", "Noah", "Sacha", "Nathan", "Tom", "Liam"], "lettre"),
        names("Filles : <b>elles aussi</b>", ["Jade", "Louise", "Ambre", "Emma", "Rose", "Alice", "Lina", "Chloé", "Inès",
                                               "Mia", "Zoé", "Léa", "Anna", "Mila", "Lola"], "lettre"),
        step("1 500", "Et les autres ?", "Prénom rare ? Le Grand Maître dit <b>« jeune chevalier »</b>, et le prénom s'affiche quand même, "
             "jusque sur le diplôme.", "", "lettre"),
        final("Écoutez-le <b>gratuitement</b>", "Tapez le prénom sur le site : le Grand Maître l'appelle, avec la voix que votre enfant "
              "entendra <b>le jour de sa quête</b>.", "lettre", "Identifiez la maman d'une Jade"),
    ],
}


def check_names():
    import unicodedata
    def key(n): return "".join(c for c in unicodedata.normalize("NFD", n.lower()) if unicodedata.category(c) != "Mn")
    for s in CARROUSELS["prenoms"]:
        for n in [x.split("<")[0] for x in s["html"].split("<span>")[1:]] if "names" in s["html"] else []:
            if not (NOMS / f"{key(n)}.mp3").exists(): raise SystemExit(f"prénom sans voix : {n}")


async def main(slugs):
    check_names()
    page = HERE / "_carrousel-ig.html"
    page.write_text((HERE / "carrousel-ig.html").read_text().replace("FONTS/", (REPO / "fonts").as_uri() + "/"))
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1350})
        for slug in slugs:
            d = OUT / slug; d.mkdir(parents=True, exist_ok=True)
            slides = CARROUSELS[slug]
            for i, s in enumerate(slides, 1):
                await pg.goto(page.as_uri()); await pg.evaluate("document.fonts.ready")
                await pg.evaluate(f"show({json.dumps(dict(s, n=f'{i} / {len(slides)}'), ensure_ascii=False)})")
                await pg.wait_for_timeout(500)
                await pg.screenshot(path=str(d / f"{i}.jpg"), type="jpeg", quality=92)
            print(slug, len(slides), flush=True)
        await b.close()
    page.unlink()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or list(CARROUSELS)))
