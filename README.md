# Traversée de Paris — Architecture produit & technique

## 1) Vision du projet
Créer un événement de course à pied en relais couvrant **toutes les rues praticables de Paris** :
- calcul d’un itinéraire couvrant l’ensemble du réseau (type *route inspection problem* adapté aux coureurs),
- découpage en segments d’environ **8 km**,
- génération et publication de fichiers **GPX**,
- mise à disposition via un site web pour visualiser, choisir et télécharger un segment.

---

## 2) Découpage en briques

### A. Données géographiques (ingestion & préparation)
**Responsabilité**
- Récupérer les données de voirie (OpenStreetMap).
- Filtrer les voies réellement praticables en course à pied.
- Construire un graphe routier exploitable par les algorithmes.

**Entrées**
- Extract OSM (Paris + buffer).
- Contraintes métier (exclure autoroutes/tunnels interdits piétons, voies privées, etc.).

**Sorties**
- Graphe géospatial nettoyé (PostGIS + tables de travail).
- Métadonnées qualité (nb d’arcs, couverture, exclusions).

**Technos recommandées**
- **Python** (GeoPandas, OSMnx, Shapely) pour ETL géospatial.
- **PostgreSQL + PostGIS** pour stockage robuste des géométries.
- Exécution batch via **Docker** + scripts versionnés.

---

### B. Moteur d’itinéraire “toutes les rues”
**Responsabilité**
- Résoudre un problème de couverture de graphe (proche du *Chinese Postman Problem* sur graphe non orienté/orienté selon les cas).
- Générer un tracé continu avec répétitions minimisées.

**Entrées**
- Graphe routier nettoyé.

**Sorties**
- Itinéraire global (LineString/MultiLineString ordonné).
- Indicateurs: distance totale, taux de répétition, % couverture.

**Technos recommandées**
- **Python** (NetworkX / OR-Tools selon niveau d’optimisation).
- Persistance intermédiaire en PostGIS.
- Export GeoJSON pour front + pipeline de segmentation.

---

### C. Segmentation 8 km & génération GPX
**Responsabilité**
- Découper l’itinéraire global en segments de 8 km (tolérance configurable).
- Garantir continuité spatiale + points de passage utiles.
- Générer un GPX par segment + un GPX global.

**Entrées**
- Itinéraire global ordonné.

**Sorties**
- `segment_001.gpx`, `segment_002.gpx`, ...
- Manifest JSON des segments (distance, D+, arrondissement(s), difficulté, statut de réservation).

**Technos recommandées**
- **Python** (gpxpy + geopy/pyproj).
- Stockage artefacts sur objet storage compatible S3 (MinIO / AWS S3).

---

### D. API métier (back-end produit)
**Responsabilité**
- Exposer les données segmentées et l’état des inscriptions.
- Fournir URLs de téléchargement GPX.
- Gérer réservation d’un segment (optionnel: auth + paiement/don).

**Endpoints cibles (exemple)**
- `GET /api/route/global`
- `GET /api/segments`
- `GET /api/segments/:id`
- `POST /api/segments/:id/reserve`
- `GET /api/segments/:id/gpx`

**Technos recommandées**
- **TypeScript + NestJS** (ou Fastify) pour robustesse API.
- **PostgreSQL** (métier) + **Redis** (cache sessions / locks de réservation).
- **OpenAPI** pour contrat partagé front/back.

---

### E. Front-end web
**Responsabilité**
- Afficher la carte complète + segments.
- Permettre filtrage/selection d’un segment.
- Détail segment + téléchargement GPX + CTA inscription.

**Fonctionnalités clés**
- Vue carte (itinéraire global + segments colorés selon disponibilité).
- Recherche par arrondissement, distance réelle, difficulté.
- Fiche segment (distance, trace, profil, GPX).
- UX mobile-first.

**Technos recommandées**
- **Next.js (React + TypeScript)**.
- **MapLibre GL JS** (ou Leaflet si simplicité prioritaire).
- UI: Tailwind + composants accessibles (Radix/shadcn).

---

### F. Ops, qualité & observabilité
**Responsabilité**
- Industrialiser pipeline + déploiement.
- Contrôler la qualité géographique et applicative.

**Technos recommandées**
- **Docker Compose** (dev), **Terraform** (si cloud), **GitHub Actions** (CI/CD).
- Monitoring: **Sentry** (front/back), **Prometheus/Grafana** (backend).
- Logs structurés + alerting sur jobs de génération.

---

## 3) Architecture logique proposée

```text
[OSM Extract] -> [ETL Geo] -> [PostGIS Graph]
                               -> [Route Solver Engine] -> [Global Route]
                                                       -> [Segmenter + GPX Export]
                                                       -> [S3/Storage]

[Next.js Front] <-> [API Backend] <-> [PostgreSQL Metier]
                                  <-> [Redis Locks/Cache]
                                  <-> [S3 GPX + GeoJSON]
```

---

## 4) Modèle de données minimal

### Table `segments`
- `id`
- `index`
- `distance_m`
- `estimated_duration_min`
- `geom` (LineString)
- `gpx_url`
- `status` (`available`, `reserved`, `confirmed`)
- `runner_id` (nullable)
- `created_at`, `updated_at`

### Table `runners`
- `id`
- `first_name`, `last_name`
- `email`, `phone`
- `club` (nullable)
- `consent_rgpd`
- `created_at`

### Table `reservations`
- `id`
- `segment_id`
- `runner_id`
- `status` (`pending`, `paid`, `cancelled`)
- `expires_at`
- `created_at`

---

## 5) Stratégie de réalisation en phases

### Phase 1 — POC géospatial
- Ingestion OSM Paris.
- Prototype solver de couverture.
- Export route globale + premiers GPX.

### Phase 2 — MVP produit
- Segmentation 8 km stable.
- API lecture segments + téléchargement GPX.
- Front carte + fiche segment.

### Phase 3 — Réservation événement
- Auth légère + réservation segment.
- Gestion collision de réservation (verrou Redis + transaction DB).
- Tableau admin (statut segments, exports, relances).

### Phase 4 — Échelle & fiabilité
- Recalcul automatisé (jobs planifiés).
- Monitoring, alerting, reprise sur erreur.
- Optimisation solver (distance totale / duplication).

---

## 6) Agents (équipes) recommandés

### 1. Agent Produit / Event Ops
- Définit règles métier (distance cible, contraintes, priorités, UX d’inscription).
- Produit user stories et critères d’acceptation.

### 2. Agent Data/GIS
- Gère pipeline OSM -> graphe utilisable.
- Maintient règles de filtrage des voies courables.
- Vérifie la qualité de couverture cartographique.

### 3. Agent Optimisation d’itinéraire
- Implémente et améliore l’algorithme de couverture.
- Mesure répétitions, distance totale et performance.
- Propose heuristiques et compromis opérationnels.

### 4. Agent Backend/API
- Conçoit modèle de données métier.
- Expose endpoints et sécurité des réservations.
- Gère stockage GPX et liens signés.

### 5. Agent Frontend Carto
- Développe carte interactive et parcours utilisateur.
- Intègre recherche, filtres, sélection segment et téléchargement.
- Optimise UX mobile.

### 6. Agent QA/Validation géographique
- Teste cohérence segments (continuité, distance, points aberrants).
- Vérifie intégrité GPX.
- Met en place tests de non-régression sur données et API.

### 7. Agent DevOps/SRE
- CI/CD, environnements, observabilité.
- Sauvegardes DB/artefacts et gestion des incidents.

---

## 7) Choix techno synthèse
- **GIS & algo**: Python + PostGIS.
- **API**: TypeScript (NestJS/Fastify) + PostgreSQL + Redis.
- **Front**: Next.js + MapLibre.
- **Stockage fichiers**: S3 compatible.
- **Infra**: Docker + GitHub Actions (+ cloud provider selon budget).

Ce socle permet de sécuriser d’abord la partie la plus risquée (couverture exhaustive des rues), puis d’itérer rapidement sur l’expérience web et la logistique événementielle.

---

## 8) Prochaines étapes concrètes (plan d’exécution)

### Étape 0 — Cadrage (J1-J3)
**Objectif**: figer les règles métier avant de coder.

- Définir la règle “rue praticable” (liste `highway=*` OSM autorisée/interdite).
- Définir la tolérance de segment (`8 km ± X m`) et les règles de découpe (pas de coupure en tunnel/pont long si possible).
- Valider les champs obligatoires dans une réservation (email, téléphone, consentement RGPD).
- Fixer les KPI de réussite:
  - `% couverture rues` cible,
  - `% duplication distance` max,
  - `% segments générés valides`.

**Livrables**
- `docs/specs/functional-spec.md`
- `docs/specs/osm-filter-rules.md`
- `docs/specs/kpi.md`

### Étape 1 — Setup technique minimal (Semaine 1)
**Objectif**: avoir un environnement reproductible local.

- Créer monorepo:
  - `apps/api`
  - `apps/web`
  - `services/geo-pipeline`
  - `infra/`
  - `docs/`
- Ajouter `docker-compose.yml` (Postgres/PostGIS, Redis, MinIO).
- Préparer CI basique (lint + tests + build).

**Definition of Done**
- `docker compose up` démarre toute la stack.
- API + web bootent localement.

### Étape 2 — Pipeline GIS POC (Semaine 1-2)
**Objectif**: produire un graphe Paris “runable”.

- Télécharger extract OSM Paris.
- Implémenter ETL de filtrage des voies.
- Charger le graphe dans PostGIS.
- Générer un premier rapport qualité (nombre d’arcs/noeuds exclus).

**Definition of Done**
- Script unique: `make geo-pipeline`.
- Tables PostGIS remplies + rapport JSON versionné.

### Étape 3 — Route globale “toutes rues” (Semaine 2-3)
**Objectif**: obtenir un itinéraire continu couvrant le réseau.

- Implémenter solveur initial (heuristique CPP).
- Exporter trace globale GeoJSON + métriques.
- Mesurer le taux de répétition et itérer sur les heuristiques.

**Definition of Done**
- `global_route.geojson` généré automatiquement.
- Dashboard minimal de métriques (`distance_total`, `coverage_pct`, `duplication_pct`).

### Étape 4 — Segmentation 8 km + GPX (Semaine 3)
**Objectif**: produire des segments exploitables par les coureurs.

- Découpage par distance cumulée.
- Vérifications de continuité (pas de saut GPS).
- Export GPX unitaire + manifest JSON.

**Definition of Done**
- Dossier `artifacts/gpx/` complet.
- `segments_manifest.json` validé par tests.

### Étape 5 — API MVP (Semaine 4)
**Objectif**: exposer les segments au front.

- Implémenter endpoints de lecture (`/route/global`, `/segments`, `/segments/:id`).
- Exposer téléchargement GPX via URL signée MinIO/S3.
- Ajouter pagination et filtres.

**Definition of Done**
- OpenAPI publiée.
- Collection de tests d’intégration verte.

### Étape 6 — Front MVP carte + sélection (Semaine 4-5)
**Objectif**: permettre sélection + téléchargement côté utilisateur.

- Carte globale + segments colorés.
- Panneau détail segment.
- Bouton téléchargement GPX.

**Definition of Done**
- Parcours complet “je choisis un segment -> je télécharge son GPX”.
- Version mobile utilisable.

### Étape 7 — Réservation (Semaine 5-6)
**Objectif**: ouvrir les inscriptions sans collision.

- POST réservation avec validation.
- Verrouillage transactionnel (`SELECT FOR UPDATE` + lock Redis).
- État des segments en temps réel.

**Definition of Done**
- Deux utilisateurs ne peuvent pas réserver le même segment simultanément.
- Journaux d’audit disponibles.

---

## 9) Backlog initial (ordre de priorité)

### P0 (indispensable)
1. Pipeline OSM reproductible.
2. Solveur de couverture fonctionnel.
3. Segmentation 8 km + GPX fiables.
4. API lecture segments.
5. Front carte + téléchargement.

### P1 (forte valeur)
1. Réservation de segment.
2. Dashboard admin de suivi de remplissage.
3. Monitoring erreurs + performances.

### P2 (optimisation)
1. Amélioration heuristique anti-duplication.
2. Scoring difficulté segment avancé.
3. Notifications automatiques (email/WhatsApp).

---

## 10) Risques majeurs & mitigation

1. **Qualité OSM hétérogène**
   - Mitigation: rapport qualité + exceptions métier versionnées.
2. **Explosion de la distance due aux répétitions**
   - Mitigation: itérations heuristiques + KPI `duplication_pct` plafonné.
3. **Segments “non naturels” pour coureurs**
   - Mitigation: post-traitement (points de passage, lissage, contrôles QA).
4. **Conflits de réservation en pic de trafic**
   - Mitigation: verrou Redis + transaction DB + expiration courte.

---

## 11) Ce qu’on fait dès maintenant (checklist J+7)

- [x] Valider la spec fonctionnelle (Produit + Data) — livrables créés dans `docs/specs/`.
- [x] Créer structure monorepo + Docker Compose — bootstrap ajouté (`apps/`, `services/`, `docker-compose.yml`).
- [~] Implémenter ETL OSM minimal et charger PostGIS — filtrage + script de chargement PostGIS (`postgis-load`) implémentés; validation DB en attente d'environnement Docker.
- [x] Générer une première route globale test (mode démo): `artifacts/routes/global_route.geojson`.
- [x] Générer 10 segments GPX de démonstration (mode démo) + `artifacts/gpx/segments_manifest.json`.
- [x] Publier un front MVP lisant un manifest statique (`apps/web/public/index.html` + `segments_manifest.json`).

Si cette checklist est terminée en 7 jours, vous avez un **MVP démontrable** pour recruter les premiers relayeurs.


## 12) Source OSM recommandée pour la suite
- **Mode recommandé**: fichier local (extract préparé) pour reproductibilité des runs et comparaison KPI.
- **Mode bootstrap rapide**: Overpass via `make geo-fetch`, puis exécution du pipeline sur le JSON généré.

Exemples:
- `make geo-fetch`
- `python3 services/geo-pipeline/run_pipeline.py --input-file services/geo-pipeline/data/overpass_edges.json`
- `python3 services/geo-pipeline/run_pipeline.py --input-file services/geo-pipeline/data/overpass_edges.json --allow-steps`


## 13) Commandes démo itinéraires (premiers livrables)
- `make geo-demo` (inclut le solveur CPP heuristique v1)
- Sorties:
  - `artifacts/reports/geo_pipeline_report.json`
  - `artifacts/intermediate/included_edges.json`
  - `artifacts/routes/global_route.geojson`
  - `artifacts/gpx/segment_001.gpx` ... `segment_010.gpx`
  - `artifacts/gpx/segments_manifest.json`


## 14) Chargement PostGIS (étape suivante en cours)
- Script: `services/geo-pipeline/load_to_postgis.py`
- Dry-run (sans DB): `python3 services/geo-pipeline/load_to_postgis.py --dry-run`
- Chargement DB: `make postgis-load`
- Table cible: `geo_edges` (geom `LineString`, SRID 4326)


## 15) Front MVP démo (manifest statique)
- Lancer: `npm --workspace apps/web run dev`
- Préparer assets: `make geo-demo web-demo-assets`
- Page: sélection de segments + téléchargement GPX depuis `/gpx/*.gpx`.


## 16) Solveur d'itinéraire global (heuristique CPP v1)
- Script: `services/geo-pipeline/solve_cpp_route.py`
- Commande: `make route-cpp` (ou `make geo-demo`)
- Sorties:
  - `artifacts/routes/global_route_cpp.geojson`
  - `artifacts/routes/route_metrics.json`
- Métriques produites: `distance_base_m`, `distance_traversed_m`, `duplication_pct`, `coverage_pct`.
