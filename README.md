# La Quête des Templiers

Une quête d'anniversaire pour enfants de 7 à 10 ans, au prénom de l'enfant, générée en deux minutes avec les vrais lieux autour d'une adresse en France (église, fontaine, vieille porte, parc…). L'adulte guide avec son téléphone, les enfants relèvent les défis et retrouvent les lettres du mot secret.

Version de test : aucun paiement, les étapes sont générées dans le navigateur.

## Fichiers

- `index.html` : l'appli complète, prête à être servie par GitHub Pages.
- `dev/engine.js` : le moteur qui choisit et ordonne les étapes à partir des données OpenStreetMap.
- `dev/test.js` : tests du moteur (`node dev/test.js`).
- `dev/app.template.html` + `dev/build.py` : source de l'interface ; `python3 dev/build.py` reconstruit `index.html`.

## Données

Lieux : © contributeurs OpenStreetMap, licence ODbL, via l'API Overpass. Recherche d'adresse : Nominatim.
