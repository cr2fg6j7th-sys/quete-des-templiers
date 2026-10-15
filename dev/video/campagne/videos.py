# The 9 new videos of the campaign. Each entry: (parts, index of the slide used as cover)
END = ("card", {"brand": True, "cta": "Familles testeuses recherchées", "pill": "Écrivez CHEVALIER",
                "small": "en commentaire · quête offerte avant l'ouverture du 7 novembre", "gap": 60}, 4.2)

def end(sub=None):
    s = dict(END[1])
    if sub: s["sub"] = sub
    return ("card", s, END[2])

PROLOGUE = "Approche. Je suis le Grand Maître de l'Ordre des Gardiens du Temple."

VIDEOS = {
  # 1. Ven. 16 oct. : l'appel aux familles
  "testeurs-1": ([
    ("card", {"eyebrow": "Avis aux parents", "big": "Le Grand Maître cherche <em>10 familles</em>.", "seal": True}, 2.4),
    ("name", "arthur", "Arthur", {"top": "Il appelle chaque enfant <b>par son prénom</b>"}),
    ("voice", "prologue-dehors-m", {"top": "Il appelle chaque enfant <b>par son prénom</b>"}, PROLOGUE, 2),
    ("card", {"big": "Une chasse au trésor de chevaliers", "sub": "dans les vraies rues de votre ville : église, fontaine, vieille porte…"}, 3.2),
    ("card", {"eyebrow": "Avant l'ouverture du 7 novembre", "big": "Testez-la <em>gratuitement</em>", "sub": "pour un anniversaire ou un mercredi, enfants de 7 à 10 ans, contre votre avis honnête."}, 3.8),
    end(),
  ], 0),
  # 2. Dim. 18 oct. : anecdote du château
  "anecdote-chateau": ([
    ("card", {"top": "Au Moyen Âge, les toilettes d'un château donnaient… <b>où ?</b>", "seal": True, "sub": "Le Grand Maître le raconte aux enfants, devant un vrai château."}, 2.6),
    ("voice", "recit-castle-0", {"top": "Les toilettes d'un <b>château fort</b>"},
     "Te voici devant ce château. Les seigneurs vivaient derrière d'épais murs de pierre. Les chevaliers les servaient et défendaient le château. Et les toilettes ? C'était un petit coin accroché au mur, avec un trou qui donnait directement… dans le vide, au-dessus du fossé !"),
    ("card", {"big": "Votre ville a ses propres secrets", "sub": "Une quête d'anniversaire pour les 7-10 ans, dans les lieux près de chez vous."}, 3.0),
    end(),
  ], 0),
  # 3. Lun. 19 oct. : comment ça marche
  "comment-ca-marche": ([
    ("card", {"top": "Un anniversaire de chevalier <b>sans rien préparer</b> ?", "seal": True, "sub": "Voici comment ça marche."}, 2.4),
    ("card", {"steps": ["Vous tapez le prénom et une adresse", "Le Grand Maître prépare 4 à 6 étapes dans les vraies rues autour", "À chaque lieu : un récit, un défi, une énigme", "Les enfants gagnent une lettre", "À la fin : le mot secret… et l'adoubement"], "gap": 54, "pad": "0 80px"}, 6.5),
    ("voice", "intro-dehors-m", {"top": "La voix que les enfants <b>entendent au départ</b>"},
     "Chevalier de l'Ordre, la quête commence ! À chaque lieu, tu gagneras une lettre. Les lettres arrivent dans le désordre : à toi de retrouver le mot secret à la fin.", 3),
    ("card", {"big": "Il pleut ?", "sub": "La quête se joue aussi à la maison : les lettres se cachent dans le frigo, sous l'oreiller…"}, 3.2),
    end(),
  ], 0),
  # 4. Mer. 21 oct. : à la maison (frigo)
  "maison-frigo": ([
    ("card", {"top": "Pluie le jour de l'anniversaire ? <b>La quête vient à la maison</b>", "seal": True, "sub": "Une lettre est cachée… dans le réfrigérateur."}, 2.8),
    ("voice", "maison-frigo", {"top": "Ce que dit le Grand Maître <b>quand on ouvre le frigo</b>"},
     "Bravo, tu l'as trouvée ! Au temps des chevaliers, il n'y avait pas de réfrigérateur. Pour garder la viande, on la salait, ou on la fumait au-dessus du feu, et les provisions restaient au frais dans les caves du château. Et pendant les grands banquets, on servait parfois un paon rôti, recouvert de ses propres plumes, comme s'il était encore vivant !"),
    ("card", {"big": "6 cachettes, 6 lettres", "sub": "Chaussure, frigo, oreiller, livre, canapé, table : à cacher en 5 minutes avant la fête."}, 3.4),
    end(),
  ], 0),
  # 5. Ven. 23 oct. : deuxième appel
  "testeurs-2": ([
    ("card", {"eyebrow": "Vacances de la Toussaint", "big": "Un après-midi avec des enfants de <em>7 à 10 ans</em> ?", "seal": True}, 2.6),
    ("name", "lina", "Lina", {"top": "Le Grand Maître les attend"}),
    ("voice", "prologue-dehors-f", {"top": "Le Grand Maître les attend"}, PROLOGUE, 2),
    ("card", {"steps": ["Vous jouez la quête avant tout le monde", "C'est gratuit", "Vous nous dites ce qui a plu… et ce qui a coincé"], "gap": 60, "pad": "0 80px"}, 4.4),
    end(),
  ], 0),
  # 6. Sam. 24 oct. : le mot secret et l'adoubement
  "mot-secret": ([
    ("card", {"top": "Le moment que les enfants <b>préfèrent</b>", "letters": "RVBAE", "sub": "Cinq lettres gagnées, dans le désordre…"}, 2.8),
    ("voice", "mot-BRAVE-m", {"top": "Le moment que les enfants <b>préfèrent</b>"},
     "Tu as maintenant toutes les lettres, mais elles sont dans le désordre. Retrouve le mot secret. Un indice : un chevalier n'a pas peur : il est…"),
    ("card", {"letters": "BRAVE", "big": "Trouvé !"}, 1.8),
    ("voice", "fin-BRAVE-m", {"top": "Puis vient <b>l'adoubement</b>"},
     "Tu as retrouvé le mot secret : BRAVE. Un chevalier est brave : il avance même quand c'est difficile. Le Sceau du Temple est ouvert ! Grand Maître, remets le trésor aux chevaliers. Et toi,"),
    ("name", "hugo", "Hugo", {"top": "Puis vient <b>l'adoubement</b>"}),
    ("voice", "nomme-m", {"top": "Puis vient <b>l'adoubement</b>"}, "Je te nomme Chevalier de l'Ordre des Gardiens du Temple. Joyeux anniversaire !"),
    end(),
  ], 0),
  # 7. Dim. 25 oct. : anecdote du puits
  "anecdote-puits": ([
    ("card", {"top": "Un seau d'eau du Moyen Âge pesait aussi lourd que… <b>quoi ?</b>", "seal": True}, 2.4),
    ("voice", "recit-well-0", {"top": "Devant un vieux <b>puits</b>"},
     "Bravo. Voici ce puits. Avant l'eau du robinet, les habitants venaient y remplir leurs seaux, chaque jour, même en hiver. Un seau plein d'eau pèse aussi lourd qu'un petit chien : les enfants aidaient souvent à les porter !"),
    ("card", {"big": "Puits, lavoirs, croix, moulins…", "sub": "Le Grand Maître trouve les vieux lieux de votre village, même les plus petits."}, 3.0),
    end(),
  ], 0),
  # 8. Mar. 27 oct. : anecdote de la mairie
  "anecdote-mairie": ([
    ("card", {"top": "D'où vient le mot <b>couvre-feu</b> ?", "seal": True}, 2.2),
    ("voice", "recit-townhall-0", {"top": "Devant la <b>mairie</b>"},
     "Voici cette mairie. C'est ici que se réunit le conseil de la ville pour prendre les décisions. Au Moyen Âge, certaines villes avaient déjà leur propre conseil. Le soir, une cloche sonnait le couvre-feu : l'heure d'éteindre les feux et d'aller se coucher !"),
    ("card", {"big": "Une anecdote vraie à chaque étape", "sub": "Les enfants apprennent sans s'en rendre compte."}, 3.0),
    end(),
  ], 0),
  # 9. Ven. 30 oct. : dernier appel
  "testeurs-3": ([
    ("card", {"eyebrow": "Dernier appel", "big": "Ouverture le <em>7 novembre</em>", "seal": True}, 2.4),
    ("name", "jade", "Jade", {"top": "Votre enfant sera-t-il le prochain appelé ?"}),
    ("voice", "prologue-dehors-f", {"top": "Votre enfant sera-t-il le prochain appelé ?"}, PROLOGUE, 2),
    ("card", {"big": "Jusqu'à l'ouverture, la quête est <em>offerte</em>", "sub": "aux familles qui la testent et nous donnent leur avis."}, 3.6),
    end(),
  ], 0),
}
