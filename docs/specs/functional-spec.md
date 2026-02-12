# Spécification fonctionnelle — Traversée de Paris (Étape 0)

## 1. Objectif
Organiser un relais de course à pied couvrant toutes les rues praticables de Paris.
Le système doit produire un itinéraire global, le découper en segments d’environ 8 km, puis permettre aux coureurs de consulter, réserver et télécharger les segments GPX.

## 2. Périmètre MVP
Inclus dans le MVP :
- Import des données de voirie OSM Paris et filtrage “runnable”.
- Génération d’un itinéraire global couvrant le réseau praticable.
- Découpage en segments cible 8 km.
- Export GPX par segment.
- Site web avec carte, détail segment, téléchargement GPX.

Hors MVP (phase ultérieure) :
- Paiement en ligne.
- Application mobile native.
- Classements / social.

## 3. Personas
- **Participant** : choisit un segment, télécharge le GPX, se prépare à courir.
- **Organisateur** : suit l’avancement des inscriptions, ajuste les règles.
- **Admin technique** : relance les pipelines et surveille la qualité des données.

## 4. User stories principales
1. En tant que participant, je veux voir les segments disponibles sur une carte afin de choisir un tronçon.
2. En tant que participant, je veux consulter les détails d’un segment (distance, zones traversées, difficulté) afin de décider si je le réserve.
3. En tant que participant, je veux télécharger le GPX du segment pour l’utiliser sur ma montre/GPS.
4. En tant qu’organisateur, je veux réserver un segment pour un coureur sans conflit concurrent.
5. En tant qu’organisateur, je veux connaître la couverture globale des rues et l’état d’occupation des segments.

## 5. Règles métier
- Un segment a une distance cible de 8 000 m, avec tolérance définie dans `kpi.md`.
- Un segment ne peut être réservé que par un seul participant à la fois.
- Les réservations “pending” expirent automatiquement après une durée configurable.
- Les voies non autorisées à la course sont exclues en amont du graphe.
- Le système doit conserver une traçabilité minimale des modifications de statut de segment.

## 6. Données minimales de réservation
Champs obligatoires :
- `first_name`
- `last_name`
- `email`
- `phone`
- `consent_rgpd` (booléen)

Champs optionnels :
- `club`
- `notes`

## 7. Exigences non-fonctionnelles (MVP)
- Génération complète (route + segments + GPX) relançable en batch.
- Reproductibilité locale via Docker Compose.
- Contrat API documenté (OpenAPI).
- Journalisation des erreurs critiques de pipeline.

## 8. Critères d’acceptation MVP
- Une route globale est produite à partir des données Paris filtrées.
- Au moins 95% des segments générés respectent la tolérance de distance.
- Un utilisateur peut faire le parcours : carte -> sélection segment -> téléchargement GPX.
- Les conflits de réservation simultanée sont bloqués.
