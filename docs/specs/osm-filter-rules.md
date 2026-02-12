# Règles de filtrage OSM — Voies praticables en course

## 1. Principe
Construire un graphe “runnable” à partir d’OpenStreetMap en incluant les voies plausiblement praticables par un coureur à Paris.

## 2. Règles d’inclusion (par défaut)
Inclure prioritairement les `highway=*` suivants :
- `footway`
- `pedestrian`
- `path`
- `residential`
- `living_street`
- `service` (hors accès privés explicites)
- `tertiary`, `tertiary_link`
- `secondary`, `secondary_link`
- `primary`, `primary_link` (si accessibilité piéton non interdite)
- `unclassified`
- `steps` (option activable/désactivable, **désactivée pour le MVP**)

## 3. Règles d’exclusion
Exclure systématiquement :
- `highway=motorway`, `motorway_link`, `trunk`, `trunk_link`
- `access=private` ou `foot=private`
- `foot=no`
- segments manifestement non praticables / dangereux (à enrichir par liste d’exceptions)

Exclusion conditionnelle (configurable) :
- tunnels longs (`tunnel=yes` + longueur > seuil)
- ponts complexes avec accessibilité piéton incertaine

## 4. Gestion des sens et restrictions
- Si voie explicitement piétonne bidirectionnelle : graphe non orienté.
- Si règles locales imposent une orientation (cas rares) : conserver la contrainte.
- En cas de tags contradictoires, appliquer une règle de prudence : exclure et logguer.

## 5. Post-traitement qualité
- Supprimer composantes isolées trop petites (< seuil longueur).
- Vérifier continuité topologique (nœuds orphelins, intersections cassées).
- Générer un rapport avec :
  - nombre d’arcs inclus/exclus,
  - motifs d’exclusion,
  - couverture par arrondissement (si disponible).

## 6. Paramètres à figer
- `ALLOW_STEPS=true|false`
- `MAX_TUNNEL_LENGTH_M`
- `MIN_COMPONENT_LENGTH_M`
- `INCLUDE_PRIMARY_ROADS=true|false`

## 7. Validation attendue
- Rapport JSON versionné après chaque run ETL.
- Échantillonnage manuel de segments exclus/inclus pour vérifier les erreurs de filtre.


## 8. Stratégie d'évolution post-MVP
- MVP: `ALLOW_STEPS=false` pour favoriser l'accessibilité globale des segments.
- Post-MVP: activer un run comparatif `ALLOW_STEPS=true` et mesurer l'impact sur `coverage_pct`, `duplication_pct` et la difficulté perçue.
- Si le gain de couverture est significatif sans dégrader excessivement l'expérience coureur, réintégrer les escaliers dans le tracé officiel.
