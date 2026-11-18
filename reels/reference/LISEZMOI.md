# Référence de direction artistique

Déposer ici `Ma_Quete_Legendaire_Anniversaire_Petit_Prix.mp4` (la vidéo de référence) et toute image de style à réutiliser.

Analyse conseillée quand la vidéo est là :

```
ffmpeg -i Ma_Quete_Legendaire_Anniversaire_Petit_Prix.mp4 -vf "fps=1,scale=270:-1,tile=8x3" -frames:v 1 planche-reference.jpg
ffmpeg -ss 2 -i Ma_Quete_Legendaire_Anniversaire_Petit_Prix.mp4 -frames:v 1 ref-02s.png   # puis 6, 9, 13, 20 s
```

Les valeurs de la DA (positions, tailles, couleurs) sont dans `../gabarit-reel.html` ; les recaler sur la référence si un écart apparaît.

## Valeurs mesurées (18/11/2026) et reprises dans `../gabarit-reel.html`

- Polices : DejaVu Serif Bold (titres ; italique = oblique synthétique) et DejaVu Sans Bold (le reste).
- En-tête : marque 35 px, espacement 0,09 em, centre y 148 ; filet y 198 ; « Chasses au trésor pour enfants » 34 px y 236 (à partir de la solution).
- Scène 1 : badge 34 px y 272 ; titres 76 px (y 368 / 470). Autres scènes : surtitre 31 px or y 310 (« LA SOLUTION » 48 px bordeaux y 318) ; titres 66 px (y 385 / 470).
- Carte 50→1030 × 575→1335 ; CTA : bouton 28 px y 558, « Détails en commentaire » 36 px y 634, carte 705→1375.
- Compte à rebours : pastille 37 px y 1402 (690×72), barre 520×10 y 1458. Pastille solution 27 px y 1406.
- Stickers 38 px, fond #fcf6ef, bord 3 px bordeaux, 2 rangées de 2 ; un trait #bd253d de 10 px par rangée.
- Minutage : scènes 0 / 3,5 / 7 / 11 / 14,5 / 18 / 22 s ; sortie de scène 0,2 s ; textes +40 px en 0,45 s décalés de 0,12 s ; carte 0,25 s après, en 0,45 s ; stickers à début+0,57 s puis toutes les 0,5 s ; barrage à fin−0,77 s ; l'en-tête s'efface presque entièrement au passage à la solution.
