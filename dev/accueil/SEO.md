# Future page d'accueil multi-quêtes : SEO et mise en ligne

Demande de Nathan (27/10/2026) : une page d'accueil « entreprise de quêtes d'anniversaire pour les enfants de 5 à 12 ans », qui dit qui nous sommes, avec la charte actuelle et un SEO soigné. Elle sera mise en ligne quand il y aura plusieurs quêtes (prévu le mois prochain, avec les voix et les images des nouvelles quêtes).

**État : PAS EN LIGNE.** Le fichier est dev/accueil/accueil.html. dev/build.py ne lit pas ce dossier, donc rien n'est déployé. L'accueil actuel (la Quête du Chevalier) reste en place.

- Aperçu local : `python3 dev/accueil/apercu.py` → dist/accueil/index.html, et des captures téléphone, ordinateur et mode sombre (dist/accueil/apercu-*.png).
- Image d'aperçu des liens (1200 × 630) : `python3 dev/accueil/og.py` → dev/accueil/og-accueil.png.

## 1. Mots-clés et intentions (une intention = une page)
Les volumes ne sont pas mesurés : c'est une estimation d'après la page de résultats de Google (27/10) et les recherches qui nous ont trouvés sur TikTok (22/10). À confirmer avec Google Search Console (après la mise en ligne) et le Planificateur de mots-clés de Google Ads (gratuit avec un compte).

| Page | Intention | Mots-clés visés |
| --- | --- | --- |
| / (cette page) | Trouver une animation d'anniversaire clé en main | chasse au trésor d'anniversaire (enfant), jeu de piste d'anniversaire, chasse au trésor clé en main, animation anniversaire enfant, idée anniversaire enfant 5 à 12 ans, anniversaire 6 / 8 / 10 / 12 ans, Ma Quête Légendaire |
| /quete-du-chevalier/ (l'accueil actuel, déplacé) | Un anniversaire sur le thème des chevaliers | anniversaire chevalier, chasse au trésor chevalier, jeu de piste chevalier, anniversaire 7 à 10 ans chevalier |
| /anniversaire-chevalier.html (guide) | S'informer : organiser un anniversaire chevalier | organiser un anniversaire chevalier, jeux, costumes, déroulé |
| /anniversaire-chevalier-a-la-maison.html (guide) | Anniversaire à l'intérieur quand il pleut | anniversaire chevalier à la maison, jeux d'intérieur |
| Pages villes (anniversaire-chevalier-*.html) | Local | anniversaire chevalier à [ville], chasse au trésor [ville] |
| Plus tard : /quete-des-…/ (une page par quête) | Thème de la quête | anniversaire pirate, anniversaire fée, etc. |

L'accueil vise les recherches générales (« chasse au trésor d'anniversaire »). Le mot « chevalier » est laissé aux pages chevalier, pour que deux pages ne se fassent pas concurrence sur la même recherche.

**Concurrence vue sur Google (27/10) :** places de marché d'animations (Funbooker), kits à imprimer (Quizotrésor, En Cavale, Helvetiq, Nature & Découvertes), médias parents (CitizenKid). Notre angle, que les autres n'ont pas : un jeu de piste dans les vraies rues de sa ville, au prénom de l'enfant, sans rien imprimer ni cacher. La page le dit en tête et le montre dans un tableau comparatif.

## 2. Ce qui est en place dans la page
- **Title** (61 caractères) : « Chasse au trésor d'anniversaire 5-12 ans | Ma Quête Légendaire ».
- **Meta description** (154 caractères) : la promesse, avec « clé en main », « jeu de piste », « dans votre ville ou à la maison », « au prénom », « prêt en 2 minutes ».
- **Titres :** un seul H1 (« La chasse au trésor d'anniversaire qui appelle votre enfant par son prénom »). Les H2 suivent les questions que posent les parents : comment ça marche, que choisir, quel âge, qui sommes-nous, questions.
- **Réponse directe pour les assistants IA :** environ 40 mots sous le H1, qui disent ce qu'est Ma Quête Légendaire, pour qui, où, et en combien de temps.
- **Tableau comparatif** : kit à imprimer, animateur ou quête. Les IA citent volontiers les tableaux, et ils aident à décider. Il reste honnête : aucun prix inventé pour les autres.
- **Section par âge** (5-6, 7-10 et 11-12 ans), pour les recherches « anniversaire 6 ans », « 10 ans »… Elle dit honnêtement ce qui convient aujourd'hui (la Quête du Chevalier, 7-10 ans).
- **« Qui sommes-nous »** et « Nos engagements », pour la confiance (expérience, entreprise réelle, sécurité, pas d'appli).
- **FAQ visible** de 10 questions, avec les mêmes réponses dans les données structurées. Les réponses reprennent la FAQ du site actuel.
- **Données structurées (JSON-LD)** : Organization (avec les comptes Instagram, TikTok et Pinterest), WebSite, WebPage, ItemList des quêtes (Product « La Quête du Chevalier », 24,90 €, âge 7-10 ans) et FAQPage.
- **Partage :** canonical, Open Graph et Twitter, avec une image d'aperçu propre à l'accueil (og-accueil.png).
- **Liens internes :** vers la quête (bouton principal ×3, texte d'ancre descriptif), les guides, les pages villes et les pages légales.
- **Technique :** HTML sémantique (header, nav, main, section, footer), pas de JavaScript. Le CSS est dans la page, avec les polices du site et leur préchargement. Le texte est affiché tout de suite : le LCP est le titre, et rien ne bouge au chargement. La page marche au téléphone d'abord, en mode sombre, au clavier (lien « Aller au contenu »), et le tableau défile sur téléphone.

## 3. À valider par Nathan avant la mise en ligne
- Les quêtes à afficher : la carte « De nouvelles quêtes » cite « pirates, fées… », les idées notées le 14/10. À remplacer par les vraies quêtes, une carte chacune.
- La phrase « née en Alsace en 2026 » et « testée par des familles avant sa sortie ». Tu peux aussi ajouter ton prénom dans « Qui sommes-nous » : un fondateur nommé inspire confiance (et c'est un signal de confiance pour Google).
- Les âges des futures quêtes (la page promet des quêtes pour les 5-6 ans et pour les 11-12 ans).

## 4. Mise en ligne (le jour où Nathan le demande)
1. **Déplacer la Quête du Chevalier** de / vers /quete-du-chevalier/. dev/build.py écrit alors site/quete-du-chevalier/index.html et la nouvelle page à la racine. Comme les chemins de l'appli sont relatifs (fonts/, audio/, sw.js), il faut ajouter une balise base ou des chemins absolus. Vérifier aussi que la portée du service worker garde la quête jouable sans réseau.
2. **Ne casser aucun lien déjà donné.** Le serveur (dev/worker.js) renvoie vers /quete-du-chevalier/ (redirection 301, en gardant les paramètres) toute adresse / qui porte un paramètre de l'appli : ?quete=, ?apercu=, ?paid=, ?annule=, ?moi=, ?code=. Le paiement Stripe revient sur /quete-du-chevalier/?paid=… (success_url et cancel_url à changer). Les QR codes déjà imprimés sur les diplômes (/?ref=diplome) et les liens des bios (?ref=tiktok…) arrivent sur l'accueil, ce qui est voulu ; on peut aussi les envoyer droit sur la quête.
3. **Adapter la page de la quête**, comme Nathan l'a demandé. Title : « La Quête du Chevalier : chasse au trésor d'anniversaire 7-10 ans | Ma Quête Légendaire ». Le H1 et la promesse disent que c'est la quête des chevaliers. On ajoute un fil d'Ariane « Accueil › La Quête du Chevalier » (BreadcrumbList), un canonical /quete-du-chevalier/ et le menu « Nos quêtes » à jour (liste QUESTS de dev/app.template.html). On relance python3 dev/snapshot.py.
4. **Mettre à jour les liens** : les guides et les pages villes (« ./?ref=guide » → « quete-du-chevalier/?ref=guide »), le sitemap (ajouter /quete-du-chevalier/) et l'image og-accueil.png dans dev/static/.
5. **Tester** : python3 dev/build.py && node dev/test.js && python3 dev/e2e_paid.py && python3 dev/e2e_testeurs.py. Ensuite un achat test, l'ouverture d'un ancien lien ?quete=, et le scan d'un QR de diplôme.
6. **Après la mise en ligne** :
   - Google Search Console : envoyer le sitemap, demander l'indexation de / et de /quete-du-chevalier/, et vérifier les données structurées (test des résultats enrichis).
   - Bing Webmaster Tools : importer depuis Search Console. Bing sert de source à ChatGPT.
   - Mettre la même description courte de l'entreprise partout : bios Instagram, TikTok, Pinterest et fiche Google.

## 5. Ensuite (contenus qui renforcent l'accueil)
- Une page par nouvelle quête, sur le modèle de /quete-du-chevalier/.
- Des guides par âge, à relier depuis la section « par âge » : « Idées d'anniversaire pour 6 ans », « … 8 ans », « … 10 ans », « … 12 ans », avec un vrai déroulé, des jeux et des conseils.
- Des liens entrants à aller chercher : blogs de parents et listes d'idées d'anniversaire (proposer la quête à tester), annuaires locaux d'Alsace, presse locale (DNA) au lancement, mentions de la marque à transformer en liens.

**Niveau de confiance :** moyen. La structure, le balisage et le contenu suivent les bonnes pratiques. Les mots-clés n'ont pas encore de volumes mesurés. Search Console, quelques semaines après la mise en ligne, dira quelles recherches amènent du monde, et on ajustera le title et les H2.
