# Publications à faire à la main (19 octobre – 20 novembre 2026)

Demande de Nathan (18/10, 11 h 49) : « augmente le nombre de posts sur les réseaux, je les posterai moi, on peut poster plusieurs fois par jour ». Puis (12 h 04) : une page avec une ligne par publication, dans l'ordre des dates, un bouton pour enregistrer la vidéo dans sa pellicule, et la légende à copier sur la même ligne.

**La page à utiliser chaque jour : https://claude.ai/artifact/8dm9LiXNaBGCWcbHCGuC6v** (« Publications à la main »). Pour chaque publication : l'heure, le réseau, le bouton « Télécharger la vidéo » ou « Télécharger l'image » (dans l'appli Claude sur iPhone, il ouvre le menu de partage, puis « Enregistrer la vidéo »), la légende ou le titre, la description, le lien et le tableau Pinterest, chacun avec un bouton « Copier », et une case « Publié » (gardée sur son téléphone).

## Rythme
- Instagram (Reel) + TikTok : 2 vidéos par jour (avec celles de Metricool), en général 12 h 15 et 18 h, ou 10 h et 18 h le week-end.
- Pinterest : 2 épingles par jour, 13 h et 21 h (ou 20 h 30).
- Au total 68 publications à la main jusqu'au 6/11 : 31 vidéos et 37 épingles.
- Du 7 au 20/11 (après l'ouverture) : 42 publications à la main, 1 vidéo d'anecdote et 2 épingles par jour (14 vidéos, 28 épingles), à des heures volontairement irrégulières, en plus des 8 vidéos d'ouverture que Metricool publie seul.
- Tout se publie dans les applis, hors Metricool : son quota gratuit est plein en octobre et en novembre (20 sur 20).

## Ce qui a changé le 18/10
- Légendes : « (Voix créée par IA) » retiré partout, à la demande de Nathan, qui active lui-même l'étiquette des réseaux (Instagram « Étiquette IA », TikTok « Contenu généré par IA »). Retiré aussi des 6 vidéos encore programmées dans Metricool (19, 21, 23, 24, 27 et 30/10), qui gardent l'étiquette IA activée.
- Métadonnées des vidéos vidées (balises, dates, nom de l'encodeur, jusque dans la piste son) : outil dev/video/clean.py, appelé automatiquement par dev/video/make.py et dev/video/campagne/build.py. Il n'y avait aucune mention de l'IA dedans, seulement FFmpeg/x264. Le filigrane inaudible que Google met en principe dans ses voix n'est pas une métadonnée et reste.
- Arthur (2/11), Alice (4/11) et Chloé (6/11) passent à la main au lieu de Metricool.

## Le contenu
- 19 nouvelles vidéos d'anecdotes (question, le Grand Maître qui raconte, carte, appel « Écrivez CHEVALIER ») : cloche de Notre-Dame, armure, colée, octroi du cochon, poulaines (maison), Bartholdi, quintaine, tranchoir (maison), herse, jeux du Moyen Âge, meunier fantôme (Halloween), escargots géants des livres (maison), arbres de mille ans, tablettes de cire (rentrée du 2/11), lavoir, ours du château (maison), animaux sous la chambre, Père Noël, livres enchaînés. Outil : dev/video/campagne/videos_toussaint.py (`python3 dev/video/campagne/build.py --set toussaint`). Fichiers : marketing/videos-toussaint/.
- 4 nouvelles vidéos de prénoms : Lucas, Rose, Adam, Léa (marketing/videos-toussaint/).
- 31 nouvelles épingles, n° 12 à 42 (marketing/epingles/, textes dans epingles.csv) : anecdotes « Le saviez-vous ? », idées du guide (costumes, gâteau château, potion, noms de chevalier, sécurité), du guide à la maison (dragon endormi, couleurs du blason, énigmes de cachettes, pont-levis et joute, règles du château, conseil des chevaliers, mot secret), anniversaires 7, 9 et 10 ans, chevalière, Toussaint, mercredi, et 4 pages de villes (Obernai, Molsheim, Mutzig, Ottrott).
- Appel à l'action : « Familles testeuses recherchées avant l'ouverture du 7 novembre : écrivez CHEVALIER » jusqu'au 30/10, puis « Encore quelques jours… », et le 6/11 « Dernier jour… Ouverture demain ! ».

## Ouverture du 7 novembre (ajouté le 19/10)
Demande de Nathan (19/10, 20 h 53) : « tu peux t'occuper des vidéos d'ouverture du 7 novembre… les mettre dans Metricool… saturer l'espace de la façon la plus réelle possible pour pas qu'on te prenne pour un robot ».
- Metricool (Instagram Reel + TikTok, étiquette IA activée, TikTok « votre marque ») : 8 vidéos, 16 places, novembre plein (20/20 avec les 4 épingles du 2, 9, 16 et 23/11). Heures irrégulières, légendes toutes différentes, sans « (Voix créée par IA) » :
  - sam. 7/11, 9 h 42 : « La quête est ouverte » (ouverture.mp4)
  - sam. 7/11, 18 h 17 : comment ça marche, 5 étapes et diplôme pour chaque enfant (comment-ca-marche-2.mp4)
  - dim. 8/11, 10 h 36 : Jules, Inès, Noah, Mia, Tom, Zoé… 1 500 prénoms (prenoms.mp4)
  - mar. 10/11, 18 h 08 : novembre, nuit à 17 h, la quête à la maison (maison-novembre.mp4)
  - jeu. 12/11, 12 h 21 : l'adoubement et un diplôme pour chaque compagnon (diplomes.mp4)
  - sam. 14/11, 10 h 53 : énigme LEDIFE → FIDÈLE (mot-fidele.mp4)
  - mar. 17/11, 18 h 34 : le calcul des parents, 3,11 € par enfant pour 8 enfants (prix.mp4)
  - ven. 20/11, 17 h 46 : Obernai, Molsheim, Mutzig, Ottrott… et votre village ? (votre-ville.mp4)
- À la main : 14 vidéos d'anecdotes avec la fin « Aperçu gratuit » (cheval, fontaine de Rome, statue de la Liberté verte, jaune d'œuf, cochons au marché, lavande, châteaux en hauteur, coquille des pèlerins, sans GPS, château d'eau, pompiers, Tuuut, dés des archéologues, selle-oreiller) et 28 épingles n° 43 à 70 (15 pages de villages vérifiées en ligne : Dorlisheim, Urmatt, Blaesheim, Westhouse, Ergersheim, Dinsheim-sur-Bruche, Hangenbieten, Ernolsheim-Bruche, Niedernai, Scharrachbergheim-Irmstett, Stotzheim, Breuschwickersheim, Westhoffen, Hipsheim, Innenheim ; et 13 anecdotes).
- Test du quota (demande de Nathan, 19/10, 21 h 38) : Nathan pense qu'une publication Instagram + TikTok ne compte que pour 1 ; l'aide de Metricool dit 2 (« Les publications en double sont comptabilisées une fois pour chaque réseau social »). 4 vidéos de plus sont programmées après la dernière épingle de novembre : mer. 25/11 14 h 12 « Devinez le lieu » (devinez-le-lieu.mp4), ven. 27/11 18 h 23 « Hugo, Lina, Sacha… » (prenoms-hiver.mp4), sam. 28/11 10 h 47 « Où est cachée la lettre ? » (maison-hiver.mp4), lun. 30/11 18 h 05 « Un mot de 4 lettres » (mot-epee.mp4). Si elles partent, Nathan avait raison ; sinon elles ne partent simplement pas, sans toucher à ce qui passe avant. Rappel programmé le 26/11 pour vérifier.
- Appel à l'action à partir du 7/11 : l'aperçu gratuit sur maquetelegendaire.fr (lien en bio), et non plus « CHEVALIER ».
- Fichiers : marketing/videos-ouverture/ (outil dev/video/campagne/videos_ouverture.py, `python3 dev/video/campagne/build.py --set ouverture`), marketing/epingles/epingle-43.png à 70.
- Le 19/10, la vidéo de Jade (26/10, 18 h, Metricool) avait encore « (Voix créée par IA) » dans sa légende : retiré.

## Chaque jour
Répondre aux commentaires et messages (« CHEVALIER », prénoms, villages) avec le lien https://maquetelegendaire.fr.

## Le planning complet

| Jour | Heure | Réseau | Publication | Fichier dans le dépôt |
| --- | --- | --- | --- | --- |
| lun. 19 oct. | 12 h 15 | Instagram + TikTok | La cloche plus lourde que deux éléphants | marketing/videos-toussaint/anecdote-cloche.mp4 |
| lun. 19 oct. | 13 h | Pinterest | Activité vacances de la Toussaint 7-10 ans : une quête de chevaliers (tableau Chasse au trésor enfant) | marketing/epingles/epingle-12.png |
| lun. 19 oct. | 20 h 30 | Pinterest | Chasse au trésor d'anniversaire sans rien préparer (tableau Chasse au trésor enfant) | marketing/epingles/epingle-03.png |
| mar. 20 oct. | 12 h 15 | Instagram + TikTok | L'armure aussi lourde qu'un enfant de 6 ans | marketing/videos-toussaint/anecdote-armure.mp4 |
| mar. 20 oct. | 13 h | Pinterest | Anecdote de chevalier pour enfants : la cloche de Notre-Dame (tableau Chasse au trésor enfant) | marketing/epingles/epingle-13.png |
| mar. 20 oct. | 18 h | Instagram + TikTok | Louise, approche… | marketing/videos/grand-maitre-louise.mp4 |
| mar. 20 oct. | 21 h | Pinterest | Costume de chevalier fait maison pour un anniversaire (tableau Anniversaire chevalier) | marketing/epingles/epingle-14.png |
| mer. 21 oct. | 13 h | Pinterest | Jeu d'anniversaire chevalier à l'intérieur : le dragon endormi (tableau Anniversaire chevalier) | marketing/epingles/epingle-15.png |
| mer. 21 oct. | 18 h | Instagram + TikTok | La tape sur la nuque du nouveau chevalier | marketing/videos-toussaint/anecdote-colee.mp4 |
| mer. 21 oct. | 20 h 30 | Pinterest | Anniversaire chevalier : le Grand Maître appelle votre enfant (tableau Anniversaire chevalier) | marketing/epingles/epingle-04.png |
| jeu. 22 oct. | 12 h 15 | Instagram + TikTok | Une taxe pour faire entrer un cochon | marketing/videos-toussaint/anecdote-cochon.mp4 |
| jeu. 22 oct. | 13 h | Pinterest | Combien pesait une armure de chevalier ? Anecdote pour enfants (tableau Chasse au trésor enfant) | marketing/epingles/epingle-16.png |
| jeu. 22 oct. | 18 h | Instagram + TikTok | Léo, approche… | marketing/videos/grand-maitre-leo.mp4 |
| jeu. 22 oct. | 21 h | Pinterest | Anniversaire chevalier à Obernai : une chasse au trésor dans la ville (tableau Chasse au trésor enfant) | marketing/epingles/epingle-17.png |
| ven. 23 oct. | 12 h 15 | Instagram + TikTok | Les chaussures trop pointues (à la maison) | marketing/videos-toussaint/maison-chaussure.mp4 |
| ven. 23 oct. | 13 h | Pinterest | Gâteau château fort facile pour un anniversaire chevalier (tableau Anniversaire chevalier) | marketing/epingles/epingle-18.png |
| ven. 23 oct. | 20 h 30 | Pinterest | Anniversaire chevalier : faire un adoubement (tableau Anniversaire chevalier) | marketing/epingles/epingle-07.png |
| sam. 24 oct. | 13 h | Pinterest | Idée d'anniversaire 7 ans : une quête de chevalier (tableau Anniversaire chevalier) | marketing/epingles/epingle-19.png |
| sam. 24 oct. | 18 h | Instagram + TikTok | Lucas, approche… | marketing/videos-toussaint/grand-maitre-lucas.mp4 |
| sam. 24 oct. | 20 h 30 | Pinterest | Anniversaire chevalier à la maison quand il pleut : jeux et déroulé (tableau Anniversaire chevalier) | marketing/epingles/epingle-11.png |
| dim. 25 oct. | 10 h | Instagram + TikTok | Aussi lourd qu'un petit chien (le puits) | branche campagne-testeurs : marketing/campagne-testeurs/anecdote-puits.mp4 |
| dim. 25 oct. | 13 h | Pinterest | Atelier blason pour enfants : les couleurs de l'héraldique (tableau Anniversaire chevalier) | marketing/epingles/epingle-20.png |
| dim. 25 oct. | 18 h | Instagram + TikTok | La statue de la Liberté et l'Alsace | marketing/videos-toussaint/anecdote-bartholdi.mp4 |
| dim. 25 oct. | 20 h 30 | Pinterest | Anniversaire chevalier à la maison, même s'il pleut (tableau Chasse au trésor enfant) | marketing/epingles/epingle-08.png |
| lun. 26 oct. | 12 h 15 | Instagram + TikTok | Le sac de sable des chevaliers trop lents | marketing/videos-toussaint/anecdote-quintaine.mp4 |
| lun. 26 oct. | 13 h | Pinterest | Anecdote pour enfants : combien boit un cheval ? (tableau Chasse au trésor enfant) | marketing/epingles/epingle-21.png |
| lun. 26 oct. | 21 h | Pinterest | Anniversaire chevalier à Molsheim : une chasse au trésor dans la ville (tableau Chasse au trésor enfant) | marketing/epingles/epingle-22.png |
| mar. 27 oct. | 12 h 15 | Instagram + TikTok | Rose, approche… | marketing/videos-toussaint/grand-maitre-rose.mp4 |
| mar. 27 oct. | 13 h | Pinterest | Noms de chevalier pour un anniversaire d'enfant (tableau Anniversaire chevalier) | marketing/epingles/epingle-23.png |
| mar. 27 oct. | 20 h 30 | Pinterest | Jeu d'anniversaire pour 4 à 15 enfants de 7 à 10 ans (tableau Chasse au trésor enfant) | marketing/epingles/epingle-09.png |
| mer. 28 oct. | 10 h | Instagram + TikTok | Raphaël, approche… | marketing/videos/grand-maitre-raphael.mp4 |
| mer. 28 oct. | 13 h | Pinterest | Anecdote de chevalier pour enfants : les poulaines (tableau Chasse au trésor enfant) | marketing/epingles/epingle-24.png |
| mer. 28 oct. | 18 h | Instagram + TikTok | Pas d'assiette au banquet (à la maison) | marketing/videos-toussaint/maison-tranchoir.mp4 |
| mer. 28 oct. | 21 h | Pinterest | Énigmes de chasse au trésor à la maison pour enfants (tableau Chasse au trésor enfant) | marketing/epingles/epingle-25.png |
| jeu. 29 oct. | 12 h 15 | Instagram + TikTok | La herse, mâchoire géante | marketing/videos-toussaint/anecdote-herse.mp4 |
| jeu. 29 oct. | 13 h | Pinterest | Idée d'anniversaire 9 ans : une chasse au trésor de chevaliers (tableau Anniversaire chevalier) | marketing/epingles/epingle-26.png |
| jeu. 29 oct. | 18 h | Instagram + TikTok | Emma, approche… | marketing/videos/grand-maitre-emma.mp4 |
| jeu. 29 oct. | 21 h | Pinterest | Goûter d'anniversaire chevalier : potion et épées en bretzel (tableau Anniversaire chevalier) | marketing/epingles/epingle-27.png |
| ven. 30 oct. | 12 h 15 | Instagram + TikTok | Les jeux des enfants du Moyen Âge | marketing/videos-toussaint/anecdote-jeux.mp4 |
| ven. 30 oct. | 13 h | Pinterest | Anniversaire chevalier à Mutzig : une chasse au trésor dans la ville (tableau Chasse au trésor enfant) | marketing/epingles/epingle-28.png |
| ven. 30 oct. | 21 h | Pinterest | Anecdote pour enfants : les banquets du Moyen Âge (tableau Anniversaire chevalier) | marketing/epingles/epingle-29.png |
| sam. 31 oct. | 10 h | Instagram + TikTok | Le meunier fantôme (Halloween) | marketing/videos-toussaint/anecdote-meunier.mp4 |
| sam. 31 oct. | 13 h | Pinterest | Anecdote du Moyen Âge pour enfants : le meunier fantôme (tableau Chasse au trésor enfant) | marketing/epingles/epingle-30.png |
| sam. 31 oct. | 18 h | Instagram + TikTok | Adam, approche… | marketing/videos-toussaint/grand-maitre-adam.mp4 |
| sam. 31 oct. | 21 h | Pinterest | Jeux d'anniversaire chevalier à l'intérieur : pont-levis et joute (tableau Anniversaire chevalier) | marketing/epingles/epingle-31.png |
| dim. 1er nov. | 10 h | Instagram + TikTok | Les escargots géants des vieux livres (à la maison) | marketing/videos-toussaint/maison-escargots.mp4 |
| dim. 1er nov. | 13 h | Pinterest | Anecdote pour enfants : des arbres de plus de mille ans (tableau Chasse au trésor enfant) | marketing/epingles/epingle-32.png |
| dim. 1er nov. | 18 h | Instagram + TikTok | Des arbres de mille ans | marketing/videos-toussaint/anecdote-arbre.mp4 |
| dim. 1er nov. | 21 h | Pinterest | Anniversaire chevalière : une quête pour les filles de 7 à 10 ans (tableau Anniversaire chevalier) | marketing/epingles/epingle-33.png |
| lun. 2 nov. | 12 h 15 | Instagram + TikTok | Les tablettes de cire des écuyers | marketing/videos-toussaint/anecdote-tablettes.mp4 |
| lun. 2 nov. | 13 h | Pinterest | Préparer la maison pour un anniversaire d'enfants (tableau Anniversaire chevalier) | marketing/epingles/epingle-34.png |
| lun. 2 nov. | 18 h | Instagram + TikTok | Arthur, approche… | marketing/videos/grand-maitre-arthur.mp4 |
| mar. 3 nov. | 12 h 15 | Instagram + TikTok | La cendre du lavoir | marketing/videos-toussaint/anecdote-lavoir.mp4 |
| mar. 3 nov. | 13 h | Pinterest | Anniversaire chevalier à Ottrott : une chasse au trésor dans le village (tableau Chasse au trésor enfant) | marketing/epingles/epingle-35.png |
| mar. 3 nov. | 18 h | Instagram + TikTok | Léa, approche… | marketing/videos-toussaint/grand-maitre-lea.mp4 |
| mar. 3 nov. | 21 h | Pinterest | Idée d'anniversaire 10 ans : une quête de chevaliers dans votre ville (tableau Anniversaire chevalier) | marketing/epingles/epingle-36.png |
| mer. 4 nov. | 12 h 15 | Instagram + TikTok | L'ours du château (à la maison) | marketing/videos-toussaint/maison-ours.mp4 |
| mer. 4 nov. | 13 h | Pinterest | Jeu calme pour un anniversaire chevalier : le conseil des chevaliers (tableau Anniversaire chevalier) | marketing/epingles/epingle-37.png |
| mer. 4 nov. | 18 h | Instagram + TikTok | Alice, approche… | marketing/videos/grand-maitre-alice.mp4 |
| mer. 4 nov. | 21 h | Pinterest | Le saviez-vous ? La statue de la Liberté imaginée par un Alsacien (tableau Chasse au trésor enfant) | marketing/epingles/epingle-38.png |
| jeu. 5 nov. | 12 h 15 | Instagram + TikTok | Des animaux sous la chambre | marketing/videos-toussaint/anecdote-maison.mp4 |
| jeu. 5 nov. | 13 h | Pinterest | Anniversaire dehors avec des enfants : les règles de sécurité (tableau Anniversaire chevalier) | marketing/epingles/epingle-39.png |
| jeu. 5 nov. | 18 h | Instagram + TikTok | Les lettres au Père Noël | marketing/videos-toussaint/anecdote-pere-noel.mp4 |
| jeu. 5 nov. | 21 h | Pinterest | Combien de lettres reçoit le Père Noël ? Anecdote pour enfants (tableau Chasse au trésor enfant) | marketing/epingles/epingle-40.png |
| ven. 6 nov. | 12 h 15 | Instagram + TikTok | Les livres attachés par des chaînes | marketing/videos-toussaint/anecdote-livres.mp4 |
| ven. 6 nov. | 13 h | Pinterest | Chasse au trésor : le mot secret à retrouver à la fin (tableau Chasse au trésor enfant) | marketing/epingles/epingle-41.png |
| ven. 6 nov. | 18 h | Instagram + TikTok | Chloé, approche… | marketing/videos/grand-maitre-chloe.mp4 |
| ven. 6 nov. | 21 h | Pinterest | Activité du mercredi pour enfants de 7 à 10 ans : une quête de chevaliers (tableau Chasse au trésor enfant) | marketing/epingles/epingle-42.png |
| sam. 7 nov. | 12 h 40 | Pinterest | Anniversaire chevalier à Dorlisheim : une quête dans le village (tableau Anniversaire chevalier) | marketing/epingles/epingle-43.png |
| sam. 7 nov. | 13 h 55 | Instagram + TikTok | Combien boit un cheval ? | marketing/videos-ouverture/anecdote-cheval.mp4 |
| sam. 7 nov. | 21 h 05 | Pinterest | Anecdote pour enfants : les pièces de la fontaine de Rome (tableau Chasse au trésor enfant) | marketing/epingles/epingle-44.png |
| dim. 8 nov. | 13 h 10 | Pinterest | Chasse au trésor de chevaliers à Urmatt pour un anniversaire (tableau Anniversaire chevalier) | marketing/epingles/epingle-45.png |
| dim. 8 nov. | 17 h 50 | Instagram + TikTok | Un million d'euros dans une fontaine | marketing/videos-ouverture/anecdote-rome.mp4 |
| dim. 8 nov. | 20 h 40 | Pinterest | Pourquoi la statue de la Liberté est verte ? Anecdote pour enfants (tableau Chasse au trésor enfant) | marketing/epingles/epingle-46.png |
| lun. 9 nov. | 12 h 50 | Pinterest | Anniversaire chevalier à Blaesheim : une chasse au trésor dans le village (tableau Anniversaire chevalier) | marketing/epingles/epingle-47.png |
| lun. 9 nov. | 18 h 05 | Instagram + TikTok | La statue de la Liberté était cuivrée | marketing/videos-ouverture/anecdote-verte.mp4 |
| lun. 9 nov. | 21 h | Pinterest | Anecdote du Moyen Âge pour enfants : la peinture au jaune d'œuf (tableau Chasse au trésor enfant) | marketing/epingles/epingle-48.png |
| mar. 10 nov. | 12 h 20 | Instagram + TikTok | Peindre avec du jaune d'œuf | marketing/videos-ouverture/anecdote-oeuf.mp4 |
| mar. 10 nov. | 13 h 05 | Pinterest | Anniversaire chevalier à Westhouse : une quête dans le village (tableau Anniversaire chevalier) | marketing/epingles/epingle-49.png |
| mar. 10 nov. | 20 h 50 | Pinterest | Anecdote pour enfants : le marché au Moyen Âge (tableau Chasse au trésor enfant) | marketing/epingles/epingle-50.png |
| mer. 11 nov. | 10 h 30 | Instagram + TikTok | Des cochons au marché | marketing/videos-ouverture/anecdote-marche.mp4 |
| mer. 11 nov. | 12 h 30 | Pinterest | Chasse au trésor d'anniversaire à Ergersheim (tableau Anniversaire chevalier) | marketing/epingles/epingle-51.png |
| mer. 11 nov. | 21 h 10 | Pinterest | Anecdote pour enfants : la lavande des châteaux forts (tableau Chasse au trésor enfant) | marketing/epingles/epingle-52.png |
| jeu. 12 nov. | 13 h | Pinterest | Anniversaire chevalier à Dinsheim-sur-Bruche : une chasse au trésor (tableau Anniversaire chevalier) | marketing/epingles/epingle-53.png |
| jeu. 12 nov. | 18 h 10 | Instagram + TikTok | La lavande contre les puces | marketing/videos-ouverture/anecdote-lavande.mp4 |
| jeu. 12 nov. | 20 h 35 | Pinterest | Pourquoi les châteaux forts étaient en hauteur ? Anecdote pour enfants (tableau Chasse au trésor enfant) | marketing/epingles/epingle-54.png |
| ven. 13 nov. | 12 h 45 | Pinterest | Anniversaire chevalier à Hangenbieten : une quête dans le village (tableau Anniversaire chevalier) | marketing/epingles/epingle-55.png |
| ven. 13 nov. | 18 h | Instagram + TikTok | Pourquoi les châteaux étaient en hauteur | marketing/videos-ouverture/anecdote-horizon.mp4 |
| ven. 13 nov. | 21 h 05 | Pinterest | Anecdote pour enfants : la coquille des pèlerins de Compostelle (tableau Chasse au trésor enfant) | marketing/epingles/epingle-56.png |
| sam. 14 nov. | 13 h 15 | Pinterest | Anniversaire chevalier à Ernolsheim-Bruche : une chasse au trésor (tableau Anniversaire chevalier) | marketing/epingles/epingle-57.png |
| sam. 14 nov. | 17 h 45 | Instagram + TikTok | La coquille des pèlerins | marketing/videos-ouverture/anecdote-coquille.mp4 |
| sam. 14 nov. | 20 h 55 | Pinterest | Comment se repérer sans GPS au Moyen Âge ? Anecdote pour enfants (tableau Chasse au trésor enfant) | marketing/epingles/epingle-58.png |
| dim. 15 nov. | 10 h 15 | Instagram + TikTok | Sans GPS au Moyen Âge | marketing/videos-ouverture/anecdote-gps.mp4 |
| dim. 15 nov. | 12 h 55 | Pinterest | Anniversaire chevalier à Niedernai : une quête dans le village (tableau Anniversaire chevalier) | marketing/epingles/epingle-59.png |
| dim. 15 nov. | 20 h 30 | Pinterest | Anecdote pour enfants : combien d'eau dans un château d'eau ? (tableau Chasse au trésor enfant) | marketing/epingles/epingle-60.png |
| lun. 16 nov. | 12 h 35 | Pinterest | Anniversaire chevalier à Scharrachbergheim-Irmstett (tableau Anniversaire chevalier) | marketing/epingles/epingle-61.png |
| lun. 16 nov. | 18 h 20 | Instagram + TikTok | Un château plein d'eau | marketing/videos-ouverture/anecdote-baignoires.mp4 |
| lun. 16 nov. | 21 h | Pinterest | Anecdote pour enfants : les pompiers, chevaliers d'aujourd'hui (tableau Chasse au trésor enfant) | marketing/epingles/epingle-62.png |
| mar. 17 nov. | 12 h 10 | Instagram + TikTok | Les pompiers, chevaliers d'aujourd'hui | marketing/videos-ouverture/anecdote-pompiers.mp4 |
| mar. 17 nov. | 13 h 10 | Pinterest | Anniversaire chevalier à Stotzheim : une chasse au trésor dans le village (tableau Anniversaire chevalier) | marketing/epingles/epingle-63.png |
| mar. 17 nov. | 20 h 45 | Pinterest | Anecdote pour enfants : comment les guetteurs donnaient l'alerte (tableau Chasse au trésor enfant) | marketing/epingles/epingle-64.png |
| mer. 18 nov. | 12 h 30 | Pinterest | Anniversaire chevalier à Breuschwickersheim : une quête dans le village (tableau Anniversaire chevalier) | marketing/epingles/epingle-65.png |
| mer. 18 nov. | 14 h | Instagram + TikTok | Tuuut ! L'alerte des guetteurs | marketing/videos-ouverture/anecdote-tuuut.mp4 |
| mer. 18 nov. | 21 h 15 | Pinterest | Anecdote pour enfants : les jeux retrouvés par les archéologues (tableau Chasse au trésor enfant) | marketing/epingles/epingle-66.png |
| jeu. 19 nov. | 13 h | Pinterest | Anniversaire chevalier à Westhoffen : une quête dans le village (tableau Anniversaire chevalier) | marketing/epingles/epingle-67.png |
| jeu. 19 nov. | 18 h 15 | Instagram + TikTok | Des dés retrouvés dans les ruines | marketing/videos-ouverture/anecdote-des.mp4 |
| jeu. 19 nov. | 20 h 50 | Pinterest | Anecdote de chevalier pour enfants : dormir en voyage (tableau Chasse au trésor enfant) | marketing/epingles/epingle-68.png |
| ven. 20 nov. | 12 h 30 | Instagram + TikTok | La selle en guise d'oreiller | marketing/videos-ouverture/maison-oreiller.mp4 |
| ven. 20 nov. | 13 h 20 | Pinterest | Chasse au trésor d'anniversaire à Hipsheim (tableau Anniversaire chevalier) | marketing/epingles/epingle-69.png |
| ven. 20 nov. | 21 h | Pinterest | Anniversaire chevalier à Innenheim : une quête dans le village (tableau Anniversaire chevalier) | marketing/epingles/epingle-70.png |
