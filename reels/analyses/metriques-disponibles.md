# Métriques Metricool utiles (cache — ne pas redemander)

> Mis à jour le 2026-11-18 via `getAnalyticsAvailableMetrics` (instagram/reels et instagram/evolution).
> Ne relancer `getAnalyticsAvailableMetrics` que si un appel échoue ou si une métrique revient dépréciée.

## Compte

- **brandId** : `7429848` (marque « MaQueteLegendairee », Instagram `maquetelegendaire`)
- **Fuseau** : `Europe/Paris`
- Réseau : `instagram` (TikTok et Pinterest aussi connectés, hors périmètre)

## Liste « Reels (par Reel) » — une ligne par Reel, colonnes dans cet ordre

`["IGRE02","IGRE03","IGRE06","IGRE11","IGRE23","IGRE24","IGRE27","IGRE28","IGRE30","IGRE26","IGRE21","IGRE12","IGRE07","IGRE10","IGRE09","IGRE08"]`

| ID | Métrique | Remarque |
|---|---|---|
| IGRE02 | Date et heure (AAAAMMJJhhmmss) | |
| IGRE03 | Légende | sert à relier à `historique.md` ; ne pas recopier |
| IGRE06 | URL du Reel | |
| IGRE11 | Portée (comptes atteints) | organique |
| IGRE23 | Vues | organique (IGRE13/IGRE15 dépréciés) |
| IGRE24 | Durée moyenne de visionnage (s) | |
| IGRE27 | Rétention (% moyen de la vidéo vue) | **souvent null** au 2026-11-18 |
| IGRE28 | Taux de visionnage > 3 s (%) | **indicateur n° 1 de l'accroche** |
| IGRE30 | Taux de saut < 3 s (%) | = 100 − IGRE28 |
| IGRE26 | Durée de la vidéo (s) | donnée « paid » : **souvent null** |
| IGRE21 | Partages | |
| IGRE12 | Enregistrements | |
| IGRE07 | Commentaires | |
| IGRE10 | J'aime | |
| IGRE09 | Interactions (j'aime + comm. + enreg. + partages) | |
| IGRE08 | Engagement (interactions pour 1 000… en pratique % de la portée) | |

Non retenus : IGRE29 reposts (toujours null), métriques payantes IGRE14-20/22 (pas de publicité).

## Liste « Compte (par jour) » — une ligne par jour (la date AAAAMMJJ arrive en dernière colonne)

`["IGEV01","IGEV43","IGEV44","IGEV22","IGEV26","IGEV23","IGEV42"]`

| ID | Métrique |
|---|---|
| IGEV01 | Abonnés (valeur du jour) |
| IGEV43 | Abonnés gagnés (null avant ~2026-11-10) |
| IGEV44 | Abonnés perdus |
| IGEV22 | Nombre de Reels publiés |
| IGEV26 | Portée des Reels |
| IGEV23 | Vues des Reels |
| IGEV42 | Comptes ayant interagi |

## Non disponibles (ne pas citer de chiffre)

- Visites du profil (IGEV07) et clics sur le site / lien en bio (IGEV10) : **dépréciés** dans Metricool.
- Part de non-abonnés touchés : non fournie.

## Meilleur créneau

`getBestTimeToPostByNetwork` (socialNetwork `instagram`, timezone `Europe/Paris`, 7 jours à venir). `dayOfWeek` : 1 = lundi … 7 = dimanche.
