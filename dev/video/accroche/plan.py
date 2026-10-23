# Which intro goes in front of which video of the hand-posting page, 23 Oct - 20 Nov 2026 (ids of the page).
# Keyword lines come from the searches that found us (22 Oct stats): « grand jeu chevalier enfant »,
# « idée jeu de piste », « chasse au trésor anniversaire (adulte) », « château fort énigme ».
#   python3 dev/video/accroche/plan.py ORIG_DIR OUT_DIR [id …]   (ORIG_DIR holds videos/<id>.mp4 as published)
import json, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

BOYS = ["Gabriel", "Léo", "Hugo", "Jules", "Noah", "Tom", "Louis", "Maël", "Nathan", "Sacha", "Arthur", "Lucas"]
GIRLS = ["Jade", "Louise", "Inès", "Mia", "Ambre", "Zoé", "Lina", "Manon", "Rose", "Alice", "Emma", "Chloé"]
KIDS = ["Jade", "Léo", "Inès", "Hugo", "Louise", "Gabriel", "Mia", "Noah", "Ambre", "Jules", "Zoé", "Tom", "Lina", "Nathan", "Manon", "Sacha"]
ADULTS = ["Sophie", "Nicolas", "Julie", "Thomas", "Céline", "Julien", "Aurélie", "Sébastien", "Émilie", "Maxime", "Laura", "Kevin", "Camille"]
KW_KID = "Grand jeu chevalier enfant"
KW_PISTE = "Idée jeu de piste d'anniversaire"
KW_TRESOR = "Chasse au trésor d'anniversaire"
KW_ENIGME = "Énigme château fort · jeu de piste"
KW_ADULTE = "Chasse au trésor anniversaire adulte"
KW_VILLAGE = "Jeu de piste dans votre village"


def roulette(final, top="Il s'arrête sur <em>UN</em> prénom.", kw=KW_KID, names=KIDS):
    others = [n for n in names if n != final]
    # a real first name opens the roulette too, so the first frame (the cover) already shows it
    first = [final] if "?" not in final else []
    return dict(type="roulette", dur=1.6, land=1.05, sealTop=520, names=first + others, final=final, top=top, kw=kw)


def alerte(sub, sub2, kw=KW_PISTE, huge="ALERTE."):
    return dict(type="alerte", dur=1.5, t1=0.45, t2=0.8, sealTop=300, huge=huge, sub=sub, sub2=sub2, kw=kw)


def ans(age, kw=KW_TRESOR):
    return dict(type="ans", dur=1.6, t2=0.75, sealTop=300, huge=f"{age} ans.", sub2="Une seule fois.", kw=kw)


def defi(label="DÉFI PARENTS", big="Plus fort que <em>votre enfant</em> ?", kw=KW_ENIGME):
    return dict(type="defi", dur=1.4, seconds=3, sealTop=400, label=label, big=big, kw=kw)


def question(q, sub2, kw=KW_PISTE, cal="Anniversaire", days=7):
    """« Ton enfant a bientôt son anniversaire ? »: a calendar counts down J-7 ... J-1, then the seal hits it."""
    return dict(type="question", dur=2.7, step=0.2, days=days, land=1.48, t2=1.68, sealTop=1050, sealSize=300, q=q, sub2=sub2, cal=cal, kw=kw)


def village(kw=KW_VILLAGE, sub2="… même dans votre village."):
    return dict(type="village", dur=1.6, land=0.75, t2=0.95, sealTop=640, top="Il y a une quête <em>ici.</em>", sub2=sub2, kw=kw)


PLAN = {
    "10-23-1745-serie-ecran-ecouter": roulette("Et vous ?", "Et <em>votre</em> prénom, il le connaît ?", KW_ADULTE, ADULTS),
    "10-24-1145-serie-ep2-gateau": ans(8),
    "10-24-1800-lucas-approche": roulette("Lucas"),
    "10-25-1200-serie-activite-vacances": alerte("Demain, vacances.", "Rien de prévu ?", "Grand jeu chevalier enfant · vacances"),
    "10-25-1745-serie-faq-prenom": roulette("Le vôtre ?", "Prénom rare ? <em>Il le connaît</em> peut-être.", KW_ADULTE,
                                           ["Ysée", "Ulysse", "Maëlys", "Kenzo", "Nahia", "Eliott", "Swann", "Maddie", "Côme", "Aliénor", "Thelma", "Gaspard"]),
    "10-26-1145-serie-prenoms-garcons": roulette("Votre fils ?", names=BOYS),
    "10-26-1745-serie-ecran-2-minutes": alerte("Ses 40 ans samedi.", "Rien de prêt ?", KW_ADULTE),
    "10-27-1215-rose-approche": roulette("Rose"),
    "10-27-1745-serie-faq-presentation": alerte("Anniversaire samedi.", "Rien de prêt ?"),
    "10-28-1000-raphael-approche": roulette("Raphaël"),
    "10-28-1745-serie-defi-herse": defi(),
    "10-29-1145-serie-budget": alerte("10 enfants.", "Et votre budget ?"),
    "10-29-1800-emma-approche": roulette("Emma"),
    "10-30-1145-serie-prenoms-filles": roulette("Votre fille ?", names=GIRLS),
    "10-30-1745-serie-faq-preparer": alerte("J-3 avant la fête.", "Rien de prêt ?"),
    "10-31-1000-le-meunier-fantome-halloween": defi("DÉFI HALLOWEEN"),
    "10-31-1800-adam-approche": roulette("Adam"),
    "11-01-1000-serie-parents": defi("TEST PARENTS", "Vous êtes <em>lequel</em> ?", KW_TRESOR),
    "11-01-1745-serie-faq-appli": alerte("Anniversaire dimanche.", "Toujours pas d'idée ?"),
    "11-02-1145-serie-defi-trou": defi(),
    "11-02-1800-arthur-approche": roulette("Arthur"),
    "11-02-2000-serie-ecran-offerts": ans(7),
    "11-03-1145-serie-faq-securite": defi("LA QUESTION DES MAMANS", "10 enfants <em>dehors</em> ?", KW_PISTE),
    "11-03-1800-lea-approche": roulette("Léa"),
    "11-04-0900-serie-activite-mercredi": alerte("Mercredi, 14 h.", "Encore les écrans ?", "Grand jeu chevalier enfant · mercredi"),
    "11-04-1145-serie-faq-pluie": alerte("Pluie samedi.", "Et la fête ?"),
    "11-04-1800-alice-approche": roulette("Alice"),
    "11-05-1145-serie-faq-village": village(),
    "11-05-1745-serie-ecran-jour-j": ans(9),
    "11-06-1145-serie-faq-prix": alerte("Anniversaire en vue.", "Budget serré ?"),
    "11-06-1800-chloe-approche": roulette("Chloé"),
    "11-07-1355-combien-boit-un-cheval": defi(),
    "11-08-1750-un-million-d-euros-dans-une-fontaine": village(sub2="… près de la fontaine."),
    "11-09-1805-la-statue-de-la-liberte-etait-cuivree": defi(),
    "11-10-1220-peindre-avec-du-jaune-d-uf": village(sub2="… même dans votre rue."),
    "11-11-1030-des-cochons-au-marche": defi("DÉFI DU 11 NOVEMBRE"),
    "11-12-1810-la-lavande-contre-les-puces": village(sub2="… même dans votre parc."),
    "11-13-1800-pourquoi-les-chateaux-etaient-en-hauteur": defi(),
    "11-14-1745-la-coquille-des-pelerins": village(),
    "11-15-1015-sans-gps-au-moyen-age": defi(),
    "11-16-1820-un-chateau-plein-d-eau": village(sub2="… même au plus petit village."),
    "11-17-1210-les-pompiers-chevaliers-d-aujourd-hui": defi(),
    "11-18-1400-tuuut-l-alerte-des-guetteurs": defi("DÉFI DU MERCREDI"),
    "11-19-1815-des-des-retrouves-dans-les-ruines": village(sub2="… même près des vieilles pierres."),
    "11-20-1230-la-selle-en-guise-d-oreiller": alerte("Pluie samedi.", "Plan B ?", "Anniversaire chevalier à la maison"),
}


def run(orig, out, ids):
    from accroche import make
    from son_serie import put_sound
    import tempfile
    for i in ids:
        src = Path(orig) / "videos" / f"{i}.mp4"
        dst = Path(out) / f"{i}.mp4"
        if "-serie-" in i:     # silent since 22 Oct: rebuild the sound first
            with tempfile.TemporaryDirectory() as td:
                based = Path(td) / "based.mp4"
                put_sound(i.split("-serie-")[1], src, based)
                make(based, dst, PLAN[i])
        else:
            make(src, dst, PLAN[i])
        print("ok", i, flush=True)


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3:] or list(PLAN))
