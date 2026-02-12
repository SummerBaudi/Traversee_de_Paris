# Questions à trancher

## Q-001 — Inclure les `steps` dans les rues praticables ? ✅ Tranché

### Contexte
Les escaliers (`highway=steps`) peuvent améliorer la couverture mais rendent certains segments moins accessibles et peuvent casser l’expérience de relais grand public.

### Options
- **Option A (inclure)** : meilleure couverture, mais segments plus difficiles.
- **Option B (exclure par défaut)** : expérience plus homogène, légère baisse de couverture.

### Recommandation actuelle
Démarrer avec **Option B (exclure par défaut)** puis ouvrir un mode “expert” plus tard.

### Décision prise
- **MVP**: **Option B** (`ALLOW_STEPS=false`) pour accélérer la livraison et garder des segments homogènes.
- **Après MVP**: réintégration des escaliers via un mode dédié (`ALLOW_STEPS=true`) avec indicateur de difficulté adapté.

### Action de suivi
Créer un ticket de backlog pour réintégrer `highway=steps` en P2, avec comparaison KPI (couverture, duplication, difficulté).
