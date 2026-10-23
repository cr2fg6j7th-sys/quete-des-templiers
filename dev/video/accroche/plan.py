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


def question(q, sub2, kw=KW_PISTE, cal="Anniversaire", days=7, labels=None):
    """« Ton enfant a bientôt son anniversaire ? »: a calendar counts down J-7 ... J-1 (or the given labels), then the seal hits it."""
    c = dict(type="question", dur=DUR, step=0.2, days=days, land=1.48, t2=1.68, sealTop=1050, sealSize=300, q=q, sub2=sub2, cal=cal, kw=kw, beats=BEATS)
    if labels:
        c.update(labels=labels, step=round(min(0.3, 1.2 / max(1, len(labels) - 1)), 3))
    return c


# The « question » model of 23 Oct (Nathan, 16:25: « fais un mix de tous les hooks »): every intro now opens on a
# direct question to the parent, in big letters from the very first frame (that frame is the TikTok cover), lasts
# 2.7 s so it can be read, has a heartbeat that speeds up with a red pulse at the edges, and ends on the seal plus
# one short line. The old kinds (roulette, défi, village, 7 ans) stay as the thing that moves in the middle.
DUR = 2.7
BEATS = [0.05, 0.75, 1.35, 1.95, 2.4]


def q_roulette(final, q, sub2, names=KIDS, kw=KW_KID):
    others = [n for n in names if n != final]
    first = [final] if "?" not in final else []
    return dict(type="roulette", dur=DUR, land=1.6, t2=1.8, d0=0.07, grow=1.13, sealTop=590, sealSize=330, nameTop=1010,
                names=first + others, final=final, top=q, qstyle=True, sub2=sub2, kw=kw, beats=BEATS)


def q_defi(label, q, sub2, kw=KW_ENIGME, seconds=3):
    return dict(type="defi", dur=DUR, land=1.6, t2=1.8, seconds=seconds, sealTop=700, sealSize=360, bigTop=400, sub2Top=1150,
                label=label, big=q, sub2=sub2, kw=kw, beats=BEATS)


def q_village(q, sub2, kw=KW_VILLAGE):
    return dict(type="village", dur=DUR, land=1.5, t2=1.7, sealTop=640, top=q, qstyle=True, sub2=sub2, kw=kw, beats=BEATS)


def q_ans(q, age, kw=KW_TRESOR):
    return dict(type="ans", dur=DUR, t2=1.6, sealTop=900, sealSize=300, hugeTop=600, sub2Top=1260, top=q, qstyle=True,
                huge=f"{age} ans.", sub2="Une seule fois.", kw=kw, beats=BEATS)


def village(kw=KW_VILLAGE, sub2="… même dans votre village."):
    return dict(type="village", dur=1.6, land=0.75, t2=0.95, sealTop=640, top="Il y a une quête <em>ici.</em>", sub2=sub2, kw=kw)


RARE = ["Ysée", "Ulysse", "Maëlys", "Kenzo", "Nahia", "Eliott", "Swann", "Maddie", "Côme", "Aliénor", "Thelma", "Gaspard"]
PLAN = {
    "10-23-1745-serie-ecran-ecouter": question("Tu as bientôt <em>un anniversaire</em> à fêter ?", "Écoute ça.", KW_TRESOR),
    "10-24-1145-serie-ep2-gateau": q_ans("Ton enfant grandit <em>trop vite</em> ?", 8),
    "10-24-1800-lucas-approche": q_roulette("Lucas", "Et si un chevalier appelait <em>ton enfant</em> ?", "Par son prénom."),
    "10-25-1200-serie-activite-vacances": question("Les vacances, <em>c'est demain</em> ?", "Rien de prévu ?", "Grand jeu chevalier enfant · vacances", cal="Vacances"),
    "10-25-1745-serie-faq-prenom": q_roulette("Le tien ?", "Ton prénom est <em>rare</em> ?", "Il le connaît peut-être.", RARE, KW_ADULTE),
    "10-26-1145-serie-prenoms-garcons": q_roulette("Ton fils ?", "Ton fils est <em>dans la liste</em> ?", "Arrête la vidéo.", BOYS),
    "10-26-1745-serie-ecran-2-minutes": question("Les 40 ans de <em>ta meilleure amie</em> ?", "Rien de prêt ?", KW_ADULTE, cal="40 ans"),
    "10-27-1215-rose-approche": q_roulette("Rose", "Il connaît le prénom de <em>ta fille</em> ?", "Écoute.", GIRLS),
    "10-27-1745-serie-faq-presentation": question("L'anniversaire, <em>c'est samedi</em> ?", "Et rien de prêt ?"),
    "10-28-1000-raphael-approche": q_roulette("Raphaël", "Il connaît le prénom de <em>ton fils</em> ?", "Écoute.", BOYS),
    "10-28-1745-serie-defi-herse": q_defi("DÉFI PARENTS", "Plus fort que <em>ton enfant</em> ?", "Tu as 5 secondes.", seconds=5),
    "10-29-1145-serie-budget": question("<em>10 enfants</em> à occuper samedi ?", "Et ton budget ?"),
    "10-29-1800-emma-approche": q_roulette("Emma", "Ta fille s'appelle <em>comment</em> ?", "Monte le son.", GIRLS),
    "10-30-1145-serie-prenoms-filles": q_roulette("Ta fille ?", "Ta fille est <em>dans la liste</em> ?", "Arrête la vidéo.", GIRLS),
    "10-30-1745-serie-faq-preparer": question("La fête, c'est dans <em>3 jours</em> ?", "Et rien de prêt ?", labels=["J-7", "J-6", "J-5", "J-4", "J-3"]),
    "10-31-1000-le-meunier-fantome-halloween": q_defi("DÉFI HALLOWEEN", "Plus fort que <em>ton enfant</em> ?", "Écoute bien."),
    "10-31-1800-adam-approche": q_roulette("Adam", "Ton fils s'appelle <em>comment</em> ?", "Monte le son.", BOYS),
    "11-01-1000-serie-parents": q_defi("TEST PARENTS", "Tu es <em>lequel</em> ?", "Sois honnête.", KW_TRESOR, seconds=0),
    "11-01-1745-serie-faq-appli": question("L'anniversaire, <em>c'est dimanche</em> ?", "Toujours pas d'idée ?"),
    "11-02-1145-serie-defi-trou": q_defi("DÉFI PARENTS", "Tu trouves <em>en 5 secondes</em> ?", "Ton enfant, oui.", seconds=5),
    "11-02-1800-arthur-approche": q_roulette("Arthur", "Il dit <em>UN</em> prénom. Celui de ton fils ?", "Écoute.", BOYS),
    "11-02-2000-serie-ecran-offerts": q_ans("Tu as vu <em>comme il grandit</em> ?", 7),
    "11-03-1145-serie-faq-securite": q_defi("LA QUESTION DES MAMANS", "10 enfants <em>dehors</em> ?", "C'est prudent ?", KW_PISTE, seconds=0),
    "11-03-1800-lea-approche": q_roulette("Léa", "Ta fille s'appelle <em>comment</em> ?", "Monte le son.", GIRLS),
    "11-04-0900-serie-activite-mercredi": question("Mercredi 14 h, <em>encore les écrans</em> ?", "On sort ?", "Grand jeu chevalier enfant · mercredi",
                                                   cal="Mercredi", labels=["10 h", "11 h", "12 h", "13 h", "14 h"]),
    "11-04-1145-serie-faq-pluie": question("Pluie annoncée <em>samedi</em> ?", "Et la fête ?", "Anniversaire chevalier à la maison"),
    "11-04-1800-alice-approche": q_roulette("Alice", "Il connaît le prénom de <em>ta fille</em> ?", "Écoute.", GIRLS),
    "11-05-1145-serie-faq-village": q_village("Tu habites <em>un petit village</em> ?", "Ça marche aussi."),
    "11-05-1745-serie-ecran-jour-j": q_ans("Le grand jour <em>approche</em> ?", 9),
    "11-06-1145-serie-faq-prix": question("Budget serré pour <em>l'anniversaire</em> ?", "Regarde.", "Idée anniversaire petit budget"),
    "11-06-1800-chloe-approche": q_roulette("Chloé", "Et si un chevalier appelait <em>ta fille</em> ?", "Par son prénom.", GIRLS),
    "11-07-1355-combien-boit-un-cheval": q_defi("DÉFI PARENTS", "Un cheval boit <em>combien</em> par jour ?", "Réponds avant lui."),
    "11-08-1750-un-million-d-euros-dans-une-fontaine": q_village("Un million d'euros <em>dans une fontaine</em> ?", "Où ça ?"),
    "11-09-1805-la-statue-de-la-liberte-etait-cuivree": q_defi("DÉFI PARENTS", "Sa couleur <em>d'origine</em> ?", "Pas verte."),
    "11-10-1220-peindre-avec-du-jaune-d-uf": q_defi("ÉNIGME", "On peignait <em>avec quoi</em> ?", "Indice : au frigo."),
    "11-11-1030-des-cochons-au-marche": q_defi("DÉFI DU 11 NOVEMBRE", "Au marché, <em>on croisait qui</em> ?", "Réponds vite."),
    "11-12-1810-la-lavande-contre-les-puces": q_village("L'arme secrète <em>des châteaux</em> ?", "Elle pousse chez toi."),
    "11-13-1800-pourquoi-les-chateaux-etaient-en-hauteur": q_defi("ÉNIGME CHÂTEAU FORT", "Pourquoi <em>tout en haut</em> ?", "Ton enfant sait ?"),
    "11-14-1745-la-coquille-des-pelerins": q_village("Pourquoi <em>une coquille</em> ?", "Regarde bien."),
    "11-15-1015-sans-gps-au-moyen-age": q_defi("DÉFI PARENTS", "Sans GPS, <em>tu te perds</em> ?", "Eux, non."),
    "11-16-1820-un-chateau-plein-d-eau": q_village("Un château <em>plein d'eau</em> ?", "Près de chez toi ?"),
    "11-17-1210-les-pompiers-chevaliers-d-aujourd-hui": q_defi("DÉFI PARENTS", "Les chevaliers <em>existent encore</em> ?", "Devine qui.", seconds=0),
    "11-18-1400-tuuut-l-alerte-des-guetteurs": q_defi("DÉFI DU MERCREDI", "Comment donner <em>l'alerte</em> ?", "Sans téléphone."),
    "11-19-1815-des-des-retrouves-dans-les-ruines": q_village("Trouvé <em>dans les ruines</em> ?", "Devine."),
    "11-20-1230-la-selle-en-guise-d-oreiller": q_defi("DÉFI PARENTS", "Un chevalier dormait <em>sur quoi</em> ?", "Pas sur un oreiller."),
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
