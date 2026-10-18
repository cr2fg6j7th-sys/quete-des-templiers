# Pinterest pins (1000x1500) and their texts: python3 dev/video/pins.py -> dist/pins/
import asyncio, csv, json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1].parent
OUT = ROOT / "dist" / "pins"
HOME, GUIDE = "?ref=pinterest", "anniversaire-chevalier.html"

# title on the pin; Pinterest title and description (what people search); page it links to
PINS = [
    dict(theme="navy", kicker="Anniversaire 7-10 ans", title="Anniversaire chevalier\u00a0: la chasse au trésor dans votre ville", art="route",
         pt="Anniversaire chevalier : une chasse au trésor dans votre ville",
         pd="Une quête de chevaliers de lieu en lieu (église, fontaine, vieille porte, parc), au prénom de votre enfant. Prête en deux minutes, rien à imprimer. Aperçu gratuit.", link=HOME),
    dict(theme="stone", kicker="Idée d'anniversaire", title="Une quête de chevalier pour ses 8\u00a0ans", sub="De vrais lieux, une voix qui dit son prénom, un mot secret à retrouver.", art="seal",
         pt="Idée d'anniversaire 8 ans : une quête de chevalier",
         pd="Pour un anniversaire de 7 à 10 ans : une quête dans les rues de votre ville, avec la voix du Grand Maître qui appelle votre enfant par son prénom.", link=HOME),
    dict(theme="rose", kicker="Chasse au trésor sans préparation", title="Rien à imprimer, rien à cacher", sub="La quête est prête en deux minutes, autour de l'adresse de votre choix.", art="route",
         pt="Chasse au trésor d'anniversaire sans rien préparer",
         pd="Pas d'indices à imprimer ni à cacher : la quête se construit avec les lieux publics autour de chez vous. Aperçu gratuit avant de payer.", link=HOME),
    dict(theme="navy", kicker="La voix du Grand Maître", title="Il appelle votre enfant par son prénom", sub="Plus de mille prénoms enregistrés.", art="seal",
         pt="Anniversaire chevalier : le Grand Maître appelle votre enfant",
         pd="Une voix de vieux Grand Maître qui confie une mission à votre enfant, par son prénom. Pour une quête d'anniversaire de chevaliers, de 7 à 10 ans.", link=HOME),
    dict(theme="stone", kicker="Organiser la fête", title="Le déroulé parfait en 2\u00a0h\u00a030", art="items", numbered=True, small=True,
         items=["Accueil des compagnons", "La quête, une heure", "Le banquet du château", "L'adoubement", "Jeux libres et cadeaux"], cta="Le guide complet",
         pt="Anniversaire chevalier 7-10 ans : le déroulé en 2 h 30",
         pd="Accueil, quête, goûter, adoubement : le programme d'un anniversaire chevalier réussi, avec une invitation à copier et des costumes faits maison.", link=GUIDE),
    dict(theme="rose", kicker="Jeux d'anniversaire", title="3 jeux de chevaliers qui marchent", art="items", small=True,
         items=["La joute à la frite de piscine", "La course des destriers", "Le siège du château de gobelets"], cta="Les règles dans le guide",
         pt="3 jeux de chevaliers pour un anniversaire d'enfant",
         pd="Joute à la frite, course des destriers, siège du château : trois jeux simples pour un anniversaire chevalier de 7 à 10 ans.", link=GUIDE),
    dict(theme="navy", kicker="Le moment dont ils se souviennent", title="L'adoubement", art="quote", sub="Un genou à terre, l'épée en mousse sur l'épaule, et la formule.",
         quote="« Pour ton courage, ta fidélité et ta bonne humeur, je te fais chevalier. »", cta="La cérémonie dans le guide",
         pt="Anniversaire chevalier : faire un adoubement",
         pd="Comment faire un adoubement à la fin d'un anniversaire chevalier : la position, la formule, et le diplôme.", link=GUIDE),
    dict(theme="stone", kicker="Et s'il pleut ?", title="La quête se joue aussi à la maison", sub="Même histoire, mêmes énigmes, des défis dans le salon.", art="seal",
         pt="Anniversaire chevalier à la maison, même s'il pleut",
         pd="Une quête de chevaliers qui se joue dehors, ou à la maison quand il pleut : même histoire, mêmes énigmes, défis adaptés à l'intérieur.", link=HOME),
    dict(theme="rose", kicker="Pour qui ?", title="Une heure de jeu, de 4\u00a0à\u00a015\u00a0enfants", sub="Pour les 7 à 10 ans, avec un adulte pour cinq enfants.", art="route",
         pt="Jeu d'anniversaire pour 4 à 15 enfants de 7 à 10 ans",
         pd="Une quête d'une heure pour un groupe de 4 à 15 enfants : chacun devient gardien d'une lettre du mot secret.", link=HOME),
    dict(theme="navy", kicker="À copier", title="Invitation d'anniversaire chevalier", art="quote", small=True,
         quote="« Oyez, oyez ! Le chevalier Léo convoque ses compagnons d'armes… »", cta="Le texte complet",
         pt="Texte d'invitation d'anniversaire chevalier à copier",
         pd="Un texte d'invitation d'anniversaire chevalier à copier, avec le déroulé de la fête et des idées de costumes faits maison.", link=GUIDE),
    dict(theme="stone", kicker="Il pleut le jour J ?", title="Anniversaire chevalier à la maison", art="items", small=True,
         items=["L'atelier blason", "Le dragon endormi", "Le pont-levis", "La chasse aux lettres"], cta="Le guide complet",
         pt="Anniversaire chevalier à la maison quand il pleut : jeux et déroulé",
         pd="Un anniversaire chevalier de 2 h à l'intérieur pour les 7-10 ans : la pièce à préparer, cinq jeux de chevaliers, l'atelier blason, une chasse aux lettres et l'adoubement.", link="anniversaire-chevalier-a-la-maison.html"),
]

async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1000, "height": 1500})
        await pg.goto((Path(__file__).parent / "pin.html").as_uri())
        for i, cfg in enumerate(PINS, 1):
            await pg.evaluate(f"pin({json.dumps(cfg)})")
            await pg.evaluate("document.fonts.ready")
            await pg.screenshot(path=str(OUT / f"epingle-{i:02d}.png"))
        await b.close()
    with open(OUT / "epingles.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Image", "Titre", "Description", "Lien (à compléter avec l'adresse du site)"])
        for i, cfg in enumerate(PINS, 1):
            w.writerow([f"epingle-{i:02d}.png", cfg["pt"], cfg["pd"], cfg["link"]])
    print(len(PINS), "épingles")

asyncio.run(main())
