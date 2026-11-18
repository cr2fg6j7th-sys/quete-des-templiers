# Référence de direction artistique

Déposer ici `Ma_Quete_Legendaire_Anniversaire_Petit_Prix.mp4` (la vidéo de référence) et toute image de style à réutiliser.

Analyse conseillée quand la vidéo est là :

```
ffmpeg -i Ma_Quete_Legendaire_Anniversaire_Petit_Prix.mp4 -vf "fps=1,scale=270:-1,tile=8x3" -frames:v 1 planche-reference.jpg
ffmpeg -ss 2 -i Ma_Quete_Legendaire_Anniversaire_Petit_Prix.mp4 -frames:v 1 ref-02s.png   # puis 6, 9, 13, 20 s
```

Les valeurs de la DA (positions, tailles, couleurs) sont dans `../gabarit-reel.html` ; les recaler sur la référence si un écart apparaît.

> Au 18/11/2026, la vidéo n'était pas dans le dépôt : le gabarit a été calé sur les mesures du brief (1080×1920, positions y 150/198/234/308/385/470, carte 50→1030 × 575→1330, compte à rebours 1400/1458, CTA 558/630/705→1375).
