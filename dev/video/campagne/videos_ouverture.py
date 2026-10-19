# Opening of the paid quest (7 Nov 2026): 8 videos scheduled in Metricool (Instagram + TikTok),
# then 14 anecdote videos posted by hand, 7 to 20 Nov. The end card no longer looks for testers:
# free preview on the site, link in the bio.
#   python3 dev/video/campagne/build.py --set ouverture [slug …]
from pathlib import Path
from videos_toussaint import LINES_OF

IMG = Path(__file__).resolve().parent / "img"


def end_open():
    return ("card", {"brand": True, "cta": "Aperçu gratuit", "pill": "maquetelegendaire.fr", "pillSmall": True,
                     "small": "lien dans la bio · 24,90 € la quête", "gap": 60}, 4.2)


def first(text, n):
    """The first n sentences of a recorded line (the clip is cut after them)."""
    import re
    return " ".join(re.findall(r"[^.!?…]+(?:[.!?…]+|$)", text)[:n]).strip()


PRO_M, PRO_F = LINES_OF("prologue-dehors-m"), LINES_OF("prologue-dehors-f")

VIDEOS = {
  # ---- Metricool, 7 to 20 Nov
  "ouverture": ([
    ("card", {"eyebrow": "Aujourd'hui", "big": "La Quête du Chevalier est <em>ouverte</em>", "seal": True}, 2.6),
    ("name", "louis", "Louis", {"top": "Le Grand Maître appelle <b>votre enfant</b>"}),
    ("voice", "prologue-dehors-m", {"top": "Le Grand Maître appelle <b>votre enfant</b>"}, first(PRO_M, 2), 2),
    ("card", {"big": "Une chasse au trésor de chevaliers dans <em>votre ville</em>", "sub": "Prête en deux minutes. Rien à imprimer, rien à cacher."}, 3.2),
    ("card", {"eyebrow": "Pour les 7 à 10 ans", "big": "24,90 € la quête", "sub": "Aperçu gratuit avant de payer."}, 3.0),
    end_open(),
  ], 0),
  "comment-ca-marche-2": ([
    ("card", {"top": "Un anniversaire de chevalier, <b>comment ça marche ?</b>", "seal": True}, 2.4),
    ("card", {"steps": ["Vous tapez son prénom et votre ville", "Le Grand Maître choisit 4 à 6 lieux à pied autour de la mairie",
                        "À chaque lieu : un récit, un défi, une énigme", "Une lettre gagnée par étape", "Le mot secret… et l'adoubement"],
              "gap": 54, "pad": "0 80px"}, 6.5),
    ("voice", "intro-dehors-f", {"top": "Ce que les enfants <b>entendent au départ</b>"},
     "Chevalière de l'Ordre, la quête commence !|À chaque lieu, tu gagneras une lettre.|À chaque lieu, tu gagneras une lettre."
     "|Les lettres arrivent dans le désordre : à toi de retrouver le mot secret à la fin.|Les lettres arrivent dans le désordre : à toi de retrouver le mot secret à la fin.", 5),
    ("card", {"big": "Et un diplôme pour <em>chaque</em> enfant", "sub": "À son prénom, à imprimer ou à envoyer à ses parents."}, 3.2),
    end_open(),
  ], 0),
  "prenoms": ([
    ("card", {"top": "Le Grand Maître connaît <b>1 500 prénoms</b>", "seal": True}, 2.2),
    ("name", "jules", "Jules", {"top": "Le Grand Maître connaît <b>1 500 prénoms</b>"}),
    ("name", "ines", "Inès", {"top": "Le Grand Maître connaît <b>1 500 prénoms</b>"}),
    ("name", "noah", "Noah", {"top": "Le Grand Maître connaît <b>1 500 prénoms</b>"}),
    ("name", "mia", "Mia", {"top": "Le Grand Maître connaît <b>1 500 prénoms</b>"}),
    ("name", "tom", "Tom", {"top": "Le Grand Maître connaît <b>1 500 prénoms</b>"}),
    ("name", "zoe", "Zoé", {"top": "Le Grand Maître connaît <b>1 500 prénoms</b>"}),
    ("voice", "nomme-f", {"top": "Et à la fin <b>de la quête</b>"}, LINES_OF("nomme-f")),
    ("card", {"big": "Le prénom de votre enfant est dedans ?", "sub": "Tapez-le sur le site, et écoutez le Grand Maître."}, 3.0),
    end_open(),
  ], 0),
  "maison-novembre": ([
    ("card", {"eyebrow": "En novembre", "big": "Nuit à 17 h, pluie… <em>et l'anniversaire ?</em>", "seal": True}, 2.8),
    ("card", {"big": "La quête vient à la maison", "sub": "6 lettres à cacher en 5 minutes : chaussure, frigo, oreiller, livre, canapé, table."}, 3.4),
    ("voice", "cachette-oreiller", {"top": "L'énigme <b>d'une cachette</b>"}, LINES_OF("cachette-oreiller")),
    ("card", {"big": "Les enfants cherchent, trouvent…", "sub": "et le Grand Maître raconte une anecdote vraie à chaque cachette."}, 3.0),
    end_open(),
  ], 0),
  "diplomes": ([
    ("card", {"eyebrow": "La fin de la quête", "big": "Un diplôme pour <em>chaque chevalier</em>", "seal": True}, 2.6),
    ("voice", "fin-EPEE-m", {"top": "Le mot secret <b>est trouvé</b>"},
     "Tu as retrouvé le mot secret : ÉPÉE.|Tu as retrouvé le mot secret : ÉPÉE.|L'épée du chevalier protège les plus faibles.|Le Sceau du Temple est ouvert !", 4),
    ("name", "gabriel", "Gabriel", {"top": "Puis vient <b>l'adoubement</b>"}),
    ("voice", "nomme-m", {"top": "Puis vient <b>l'adoubement</b>"}, LINES_OF("nomme-m")),
    ("card", {"img": (IMG / "diplome-rose.png").as_uri(), "imgw": 640, "sub": "Et chaque compagnon repart avec le sien, à son prénom."}, 3.6),
    ("card", {"big": "À imprimer, ou à envoyer à leurs parents", "sub": "Vous tapez les prénoms à la fin de la quête."}, 3.0),
    end_open(),
  ], 0),
  "mot-fidele": ([
    ("card", {"top": "Les enfants ont gagné <b>6 lettres</b>", "letters": "LEDIFE", "sub": "Vous trouvez le mot avant eux ?"}, 3.0),
    ("voice", "mot-FIDELE-f", {"top": "Le Grand Maître <b>donne un indice</b>"}, LINES_OF("mot-FIDELE-f")),
    ("card", {"letters": "FIDÈLE", "big": "Trouvé !"}, 1.8),
    ("voice", "fin-FIDELE-f", {"top": "Le Sceau du Temple <b>s'ouvre</b>"},
     "Tu as retrouvé le mot secret : FIDÈLE.|Tu as retrouvé le mot secret : FIDÈLE.|Une chevalière est fidèle à ses amis et à sa parole."
     "|Une chevalière est fidèle à ses amis et à sa parole.|Le Sceau du Temple est ouvert !|Le Sceau du Temple est ouvert !", 6),
    ("card", {"big": "6 lettres, 6 gardiens", "sub": "Chaque enfant garde une lettre jusqu'à la fin de la quête."}, 2.8),
    end_open(),
  ], 0),
  "prix": ([
    ("card", {"eyebrow": "Le calcul des parents", "big": "Une fête de 8 enfants : <em>3,11 € par enfant</em>", "seal": True}, 2.8),
    ("card", {"big": "Pas d'animateur à payer", "sub": "Le Grand Maître guide la troupe depuis votre téléphone."}, 3.0),
    ("name", "lena", "Léna", {"top": "Il appelle <b>votre enfant</b> par son prénom"}),
    ("voice", "prologue-dehors-f", {"top": "Il appelle <b>votre enfant</b> par son prénom"}, first(PRO_F, 2), 2),
    ("card", {"big": "24,90 € la quête", "sub": "Aperçu gratuit avant de payer : nombre d'étapes, distance, durée."}, 3.0),
    end_open(),
  ], 0),
  "votre-ville": ([
    ("card", {"top": "Obernai, Molsheim, Mutzig, Ottrott… <b>et votre village ?</b>", "seal": True}, 2.6),
    ("voice", "indice-fountain-0", {"top": "Un indice <b>du Grand Maître</b>"}, LINES_OF("indice-fountain-0")),
    ("card", {"big": "Tapez le nom de votre ville", "sub": "Le Grand Maître choisit les lieux à pied autour de la mairie : église, fontaine, vieille porte…"}, 3.4),
    end_open(),
  ], 0),
}


# ---- by hand, 7 to 20 Nov: one anecdote a day
def anecdote(question, where, clip, close_big, close_sub):
    eyebrow = "Une lettre cachée à la maison" if clip.startswith("maison-") else "Le saviez-vous ?"
    head = {"seal": True, "eyebrow": eyebrow, "big": question.replace("<b>", "<em>").replace("</b>", "</em>")}
    return ([("card", head, 2.6), ("voice", clip, {"top": where}, LINES_OF(clip)),
             ("card", {"big": close_big, "sub": close_sub}, 3.0), end_open()], 0)


VIDEOS.update({
  "anecdote-cheval": anecdote("Combien d'eau boit un cheval <b>chaque jour</b> ?", "Près d'une <b>fontaine</b>", "recit-fountain-0",
      "Une quête qui fait bouger", "De fontaine en vieille porte, une heure de jeu dehors."),
  "anecdote-rome": anecdote("Plus d'un million d'euros <b>au fond d'une fontaine</b> ?", "Près d'une <b>fontaine</b>", "recit-fountain-1",
      "Chaque lieu garde une lettre", "Les enfants la gagnent en relevant le défi du Grand Maître."),
  "anecdote-verte": anecdote("Pourquoi la statue de la Liberté <b>est devenue verte</b> ?", "Devant un <b>monument</b>", "recit-statue-1",
      "Les monuments de votre ville", "deviennent des étapes de la quête."),
  "anecdote-oeuf": anecdote("Au Moyen Âge, on peignait avec… <b>du jaune d'œuf</b> ?", "Devant une <b>œuvre d'art</b>", "recit-artwork-0",
      "Une anecdote vraie à chaque étape", "Les enfants apprennent sans s'en rendre compte."),
  "anecdote-marche": anecdote("Des cochons <b>en liberté</b> sur la place du marché ?", "Sur la <b>place</b>", "recit-square-0",
      "La place devient un terrain de jeu", "Récit, défi, énigme : la troupe gagne sa lettre."),
  "anecdote-lavande": anecdote("Contre les puces, les chevaliers avaient… <b>de la lavande</b>", "Dans un <b>jardin</b>", "recit-park-1",
      "Au parc, un défi de chevalier", "Une quête pour 4 à 15 enfants de 7 à 10 ans."),
  "anecdote-horizon": anecdote("Pourquoi les châteaux étaient <b>tout en haut</b> ?", "Devant un <b>point de vue</b>", "recit-viewpoint-0",
      "Votre ville vue par le Grand Maître", "Une quête dans les vrais lieux autour de chez vous."),
  "anecdote-coquille": anecdote("Pourquoi des pèlerins portaient <b>une coquille</b> sur leur chapeau ?", "Devant une <b>croix de chemin</b>", "recit-cross-0",
      "Même au plus petit village", "le Grand Maître trouve des lieux pour la quête."),
  "anecdote-gps": anecdote("Sans GPS, comment ne pas se perdre <b>au Moyen Âge</b> ?", "À un <b>carrefour</b>", "recit-cross-1",
      "Suivez les indices du Grand Maître", "Ils mènent la troupe de lieu en lieu."),
  "anecdote-baignoires": anecdote("Un château qui garde <b>des milliers de baignoires</b> ?", "Devant un <b>château d'eau</b>", "recit-watertower-0",
      "Un château d'eau, un lavoir, un moulin…", "Les lieux de votre village ont des histoires."),
  "anecdote-pompiers": anecdote("Les chevaliers d'aujourd'hui, <b>ce sont eux</b>", "Devant une <b>caserne</b>", "recit-fire-0",
      "Courage, entraide, bonne humeur", "Les valeurs du chevalier, à chaque étape de la quête."),
  "anecdote-tuuut": anecdote("Comment les guetteurs donnaient-ils <b>l'alerte</b> ?", "Au pied d'une <b>tour</b>", "recit-tower-0",
      "Votre enfant a un bon souffle ?", "Une quête de chevaliers pour son anniversaire."),
  "anecdote-des": anecdote("Les enfants du Moyen Âge jouaient déjà… <b>aux dés</b>", "Devant des <b>ruines</b>", "recit-ruins-0",
      "Vieilles pierres, grandes histoires", "Le Grand Maître les raconte aux enfants."),
  "maison-oreiller": anecdote("En voyage, les chevaliers dormaient sur… <b>leur selle</b> ?", "Une lettre cachée <b>sous l'oreiller</b>", "maison-oreiller",
      "Il pleut ? La quête vient à la maison", "Six lettres à cacher en 5 minutes."),
})


# ---- Metricool, 25 to 30 Nov: 4 more videos, after the last November pin (23/11). The free plan counts
# Instagram + TikTok as 2; if it really counts them as 1 (Nathan, 19/10), these go out, otherwise they don't,
# and nothing scheduled before them is affected.
VIDEOS.update({
  "devinez-le-lieu": ([
    ("card", {"eyebrow": "Petit jeu", "big": "Devinez le lieu <em>avant les enfants</em>", "sub": "Trois indices du Grand Maître.", "seal": True}, 2.8),
    ("voice", "indice-mill-0", {"top": "Indice <b>n° 1</b>"}, LINES_OF("indice-mill-0")),
    ("voice", "indice-library-0", {"top": "Indice <b>n° 2</b>"}, LINES_OF("indice-library-0")),
    ("voice", "indice-castle-0", {"top": "Indice <b>n° 3</b>"}, LINES_OF("indice-castle-0")),
    ("card", {"big": "Un moulin, une bibliothèque, un château", "sub": "Les indices changent avec les lieux de votre ville."}, 3.2),
    end_open(),
  ], 0),
  "prenoms-hiver": ([
    ("card", {"top": "Et ces prénoms-là, <b>il les connaît ?</b>", "seal": True}, 2.2),
    ("name", "hugo", "Hugo", {"top": "Et ces prénoms-là, <b>il les connaît ?</b>"}),
    ("name", "lina", "Lina", {"top": "Et ces prénoms-là, <b>il les connaît ?</b>"}),
    ("name", "sacha", "Sacha", {"top": "Et ces prénoms-là, <b>il les connaît ?</b>"}),
    ("name", "manon", "Manon", {"top": "Et ces prénoms-là, <b>il les connaît ?</b>"}),
    ("name", "ethan", "Ethan", {"top": "Et ces prénoms-là, <b>il les connaît ?</b>"}),
    ("name", "camille", "Camille", {"top": "Et ces prénoms-là, <b>il les connaît ?</b>"}),
    ("voice", "nomme-m", {"top": "Et à la fin <b>de la quête</b>"}, LINES_OF("nomme-m")),
    ("card", {"big": "1 500 prénoms, et celui de votre enfant ?", "sub": "Tapez-le sur le site, et écoutez le Grand Maître."}, 3.0),
    end_open(),
  ], 0),
  "maison-hiver": ([
    ("card", {"eyebrow": "Anniversaire en hiver", "big": "Froid, nuit, pluie… <em>la quête vient à la maison</em>", "seal": True}, 3.0),
    ("voice", "cachette-canape", {"top": "Où est cachée <b>la lettre ?</b>"}, LINES_OF("cachette-canape")),
    ("card", {"big": "Sous un coussin du canapé !", "sub": "6 cachettes, une énigme pour chacune, et une anecdote quand on trouve."}, 3.2),
    end_open(),
  ], 0),
  "mot-epee": ([
    ("card", {"top": "Les enfants ont gagné <b>4 lettres</b>", "letters": "EEPE", "sub": "Un mot de chevalier… vous le trouvez ?"}, 3.0),
    ("voice", "mot-EPEE-f", {"top": "Le Grand Maître <b>donne un indice</b>"}, LINES_OF("mot-EPEE-f")),
    ("card", {"letters": "ÉPÉE", "big": "Trouvé !"}, 1.8),
    ("voice", "fin-EPEE-f", {"top": "Le Sceau du Temple <b>s'ouvre</b>"},
     "Tu as retrouvé le mot secret : ÉPÉE.|Tu as retrouvé le mot secret : ÉPÉE.|L'épée de la chevalière protège les plus faibles.|Le Sceau du Temple est ouvert !", 4),
    ("card", {"big": "4, 5 ou 6 lettres", "sub": "Le mot secret change avec le nombre d'étapes : ÉPÉE, BRAVE, FIDÈLE…"}, 3.0),
    end_open(),
  ], 0),
})
