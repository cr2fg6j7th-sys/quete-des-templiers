# Ma Quête de Chevalier

Une quête d'anniversaire pour enfants de 7 à 10 ans, au prénom de l'enfant, générée en deux minutes avec les vrais lieux autour d'une adresse en France (église, fontaine, vieille porte, parc…). L'adulte guide avec son téléphone, les enfants relèvent les défis et retrouvent les lettres du mot secret. La voix du Grand Maître est enregistrée (Gemini TTS, voix Algenib).

## Deux versions

- **Démo gratuite** (`index.html`, GitHub Pages) : tout tourne dans le téléphone, le bouton de déblocage est gratuit. À retirer le jour du lancement.
- **Version payante** (Cloudflare) : le téléphone cherche les lieux publics, le serveur choisit les étapes et ne renvoie qu'un aperçu et un jeton chiffré. Après paiement Stripe, le serveur ouvre la quête. Le lien `?quete=…` rouvre la quête sur n'importe quel téléphone.

## Fichiers

- `dev/geo.js` : requête OpenStreetMap et distances (téléphone et serveur).
- `dev/engine.js` : choix et ordre des étapes, textes de la quête.
- `dev/voice.js` : phrases enregistrées du Grand Maître et prénoms.
- `dev/worker.js` : serveur Cloudflare (`/api/preview`, `/api/checkout`, `/api/unlock`).
- `dev/app.template.html` : l'interface.
- `dev/legal/` : conditions de vente, mentions légales, confidentialité ; l'identité du vendeur se remplit une seule fois dans `dev/legal/identite.json`.
- `dev/villes/` : pages « Anniversaire chevalier à [ville] » pour Google, construites à la mise en ligne avec les lieux de chaque ville (`villes.json` : la zone, pour l'instant les communes de plus de 1 000 habitants à 15 km autour d'Obernai et de Rosheim ; une commune sans assez de lieux nommés n'a pas de page).
- `dev/snapshot.py` : copie l'accueil tel qu'affiché dans `dev/home.static.html`, pour les robots des IA qui n'exécutent pas le JavaScript. À relancer après chaque changement de l'accueil.
- `dev/build.py` : construit `index.html` (démo), `site/` (version payante), `legal/` et `dist/worker.js`.
- `dev/test.js` : tests du moteur ; `dev/serve.mjs` + `dev/e2e_paid.py` : test complet de la version payante avec un faux Stripe.
- `audio/` : voix et prénoms, produits par l'action « Voix du Grand Maître » à partir de `audio/manifest.json`.
- `fonts/` : polices (licence SIL OFL), servies par le site.
- `wrangler.toml` + `.github/workflows/deploy.yml` : mise en ligne sur Cloudflare.

## Mise en ligne

L'action « Mise en ligne (Cloudflare) » publie la version payante à chaque modification. Elle attend trois secrets du dépôt : `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` et `STRIPE_SECRET_KEY` (clé de test d'abord, clé réelle au lancement). La clé de chiffrement des quêtes (`QUEST_KEY`) est créée une fois chez Cloudflare et ne doit jamais changer.

## Données

Lieux : © contributeurs OpenStreetMap, licence ODbL, via l'API Overpass. Recherche d'adresse : Nominatim.
