# KPI & seuils de pilotage — Traversée de Paris

## 1. KPI cœur (géospatial)
1. **coverage_pct**
   - Définition : % de longueur de rues praticables couvertes par l’itinéraire global.
   - Cible MVP : **>= 99.0%**
2. **duplication_pct**
   - Définition : part de distance répétée / distance totale parcourue.
   - Cible MVP : **<= 35.0%**
3. **segment_valid_pct**
   - Définition : % segments dans la tolérance de distance cible.
   - Cible MVP : **>= 95.0%**

## 2. KPI segmentation
1. **segment_distance_target_m**: `8000`
2. **segment_tolerance_m**: `±300`
3. **max_gap_between_points_m** (qualité GPX): `<= 50m`

## 3. KPI produit
1. **download_success_pct** (GPX) : >= 99%
2. **reservation_conflict_block_rate** : 100%
3. **api_p95_ms** (GET segments) : <= 500ms (charge MVP)

## 4. KPI exploitation
1. **pipeline_success_rate** : >= 95%
2. **mean_pipeline_duration_min** : à mesurer puis plafonner
3. **critical_alerts_open_gt_24h** : 0

## 5. Cadence de suivi
- Quotidien (phase build): `pipeline_success_rate`, `coverage_pct`, `segment_valid_pct`.
- Hebdomadaire: revue `duplication_pct` et plan d’optimisation solver.

## 6. Conditions de go/no-go MVP
Go si :
- coverage_pct >= 99%
- segment_valid_pct >= 95%
- parcours front “sélection + téléchargement GPX” valide
- réservation sans double-allocation
