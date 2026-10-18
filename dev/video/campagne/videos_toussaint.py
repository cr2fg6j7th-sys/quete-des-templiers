# The 19 anecdote videos posted by hand from 19 Oct to 6 Nov 2026 (second video of the day).
# Each one: a question card, the Grand Maître telling the story (recorded clip, exact text), a card
# that ties it to the quest, and the testers' end card.
#   python3 dev/video/campagne/build.py --set toussaint [slug …]
import json, subprocess
from pathlib import Path
from videos import end

# The exact words of each recorded clip, from dev/voice.js (the captions follow them sentence by sentence).
_LINES = json.loads(subprocess.check_output(["node", "-e", "process.stdout.write(JSON.stringify(require('./dev/voice.js').LINES))"],
                                            cwd=Path(__file__).resolve().parents[3]))
LINES_OF = _LINES.__getitem__


def anecdote(question, where, clip, close_big, close_sub):
    eyebrow = "Une lettre cachée à la maison" if clip.startswith("maison-") else "Le saviez-vous ?"
    first = {"seal": True, "eyebrow": eyebrow, "big": question.replace("<b>", "<em>").replace("</b>", "</em>")}
    return ([
        ("card", first, 2.6),
        ("voice", clip, {"top": where}, LINES_OF(clip)),
        ("card", {"big": close_big, "sub": close_sub}, 3.0),
        end(),
    ], 0)


AT_HOME = "Une lettre cachée "

VIDEOS = {
  "anecdote-cloche": anecdote("Une cloche plus lourde que <b>deux éléphants</b> ?", "Devant une <b>église</b>", "recit-church-0",
      "Église, fontaine, vieille porte…", "Une anecdote vraie à chaque étape de la quête."),
  "anecdote-armure": anecdote("Combien pesait l'armure d'un <b>chevalier</b> ?", "Au bord d'un <b>terrain de sport</b>", "recit-sport-0",
      "Le stade devient un champ de tournoi", "La quête se joue dans les vrais lieux autour de chez vous."),
  "anecdote-colee": anecdote("Pourquoi le nouveau chevalier recevait-il <b>une tape sur la nuque</b> ?", "Devant une <b>chapelle</b>", "recit-church-1",
      "À la fin de la quête : l'adoubement", "Le Grand Maître nomme votre enfant chevalier, devant tous ses amis."),
  "anecdote-cochon": anecdote("Au Moyen Âge, il fallait payer pour faire entrer… <b>un cochon</b> ?", "Devant une <b>vieille porte</b>", "recit-gate-1",
      "Les vieilles portes ont des histoires", "Le Grand Maître les raconte à vos enfants, de lieu en lieu."),
  "maison-chaussure": anecdote("Des chevaliers coupaient le bout de <b>leurs chaussures</b>. Pourquoi ?", AT_HOME + "<b>dans une chaussure</b>", "maison-chaussure",
      "Il pleut pendant les vacances ?", "La quête se joue aussi à la maison : six lettres à cacher en 5 minutes."),
  "anecdote-bartholdi": anecdote("La statue de la Liberté a été imaginée par… <b>un Alsacien</b> ?", "Devant une <b>statue</b>", "recit-statue-0",
      "Statues, fontaines, lavoirs…", "Le Grand Maître trouve les lieux de votre ville, même au village."),
  "anecdote-quintaine": anecdote("Le sac de sable qui punissait <b>les chevaliers trop lents</b>", "Dans un <b>parc</b>", "recit-park-0",
      "Au parc, un défi de chevalier", "À chaque étape, les enfants relèvent un défi pour gagner leur lettre."),
  "maison-tranchoir": anecdote("Au banquet du Moyen Âge, <b>pas d'assiette</b>. Alors quoi ?", AT_HOME + "<b>sous la table</b>", "maison-table",
      "Le goûter devient un banquet", "Six cachettes dans la maison, une énigme du Grand Maître pour chacune."),
  "anecdote-herse": anecdote("La porte qui se fermait <b>comme une mâchoire géante</b>", "Devant une <b>porte de la ville</b>", "recit-gate-0",
      "Le Templier connaissait le mot de passe…", "Votre enfant, lui, devra retrouver le mot secret."),
  "anecdote-jeux": anecdote("À quoi jouaient les enfants <b>au Moyen Âge</b> ?", "Sur une <b>aire de jeux</b>", "recit-playground-0",
      "Une quête qui fait bouger", "Une heure de jeu dehors, pour 4 à 15 enfants de 7 à 10 ans."),
  "anecdote-meunier": anecdote("Pourquoi le meunier ressemblait-il <b>à un fantôme</b> ?", "Devant un <b>moulin</b>", "recit-mill-0",
      "Moulins, lavoirs, puits…", "Le Grand Maître trouve même les vieux lieux des petits villages."),
  "maison-escargots": anecdote("Dans les vieux livres, des chevaliers combattaient… <b>des escargots géants</b>", AT_HOME + "<b>dans un livre</b>", "maison-livre",
      "Six cachettes dans la maison", "Chaussure, frigo, oreiller, livre, canapé, table : une anecdote pour chacune."),
  "anecdote-arbre": anecdote("Certains arbres étaient déjà là <b>au temps des chevaliers</b>", "Devant un <b>vieil arbre</b>", "recit-tree-0",
      "Votre quartier a une histoire", "Une quête de chevaliers dans les lieux près de chez vous."),
  "anecdote-tablettes": anecdote("Ni cahier ni gomme : comment écrivaient <b>les écuyers</b> ?", "Devant une <b>école</b>", "recit-school-0",
      "Un mercredi avec les copains ?", "Une heure de quête dehors pour les 7 à 10 ans."),
  "anecdote-lavoir": anecdote("Pour laver le linge blanc, on utilisait… <b>de la cendre</b> ?", "Devant un <b>lavoir</b>", "recit-lavoir-0",
      "Un vieux lavoir dans votre village ?", "Il peut devenir une étape de la quête."),
  "maison-ours": anecdote("Au château, le soir, on faisait danser… <b>un ours</b> ?", AT_HOME + "<b>dans le canapé</b>", "maison-canape",
      "Nuit à 17 h, pluie dehors ?", "La quête se joue aussi à la maison : même histoire, mêmes énigmes."),
  "anecdote-maison": anecdote("Au Moyen Âge, des animaux dormaient <b>sous la chambre</b>", "Devant une <b>vieille maison</b>", "recit-house-0",
      "Chaque lieu a son secret", "Le Grand Maître en raconte un à chaque étape de la quête."),
  "anecdote-pere-noel": anecdote("Le Père Noël reçoit combien de lettres <b>chaque année</b> ?", "Devant une <b>boîte aux lettres</b>", "recit-postbox-0",
      "Même la boîte aux lettres a son histoire", "Une quête de chevaliers dans les rues de votre ville."),
  "anecdote-livres": anecdote("Pourquoi attachait-on les livres <b>avec des chaînes</b> ?", "Devant une <b>bibliothèque</b>", "recit-library-0",
      "La quête ouvre demain", "Aujourd'hui encore, testez-la gratuitement : écrivez CHEVALIER."),
}
