# Modèle de planification

## 1. L'objectif (`Objective`) — entrée

```json
{
  "id": "obj_…", "goal": "Construire la couche API de SCC",
  "context": "", "otype": "build",
  "given_tasks": [{"title": "Concevoir", "prerequisites": [], "priority": 5, "impact": 0.8}],
  "constraints": ["Respecter le découplage par contrats."],
  "learning_ids": [], "deliberation_ids": [], "actor": "brainai"
}
```

Si `given_tasks` est vide, un **gabarit canonique** est dérivé selon le type
d'objectif (Cadrage → Conception → Réalisation → Validation → Clôture).

## 2. La tâche (`PlanTask`) — unité atomique

```json
{
  "id": "task_…", "title": "Réaliser les composants",
  "phase": "Réalisation", "step": "Build",
  "prerequisites": ["task_…"], "kind": "task", "agent": "",
  "complexity": 4, "priority": 4, "risk": 0.4, "impact": 0.8,
  "sources": ["template:build"], "hash": "…"
}
```

Estimations bornées : complexité 1..5, priorité 1..5, risque/impact 0..1. Chaque
tâche cite ses **sources** (gabarit, `learning:…`, `reasoning:…`, `given`) — traçabilité.

## 3. La stratégie (`PlanStrategy`) — variante

Trois variantes déterministes, chacune un **sous-ensemble ordonné** de tâches :
- **complète** : couverture maximale ;
- **essentielle** : tâches critiques (priorité ≥ 4) + prérequis ;
- **rapide** : tâches à fort impact (≥ 0.6) + prérequis.

Chacune est **scorée** (impact / risque / complexité / couverture → total pondéré).

## 4. Le plan (`Plan`) — stratégie matérialisée

```json
{
  "id": "plan_…", "strategy_name": "complète",
  "ordering": ["task_…", "…"],                 // ordre topologique
  "structure": {"phases": [{"phase": "…", "steps": [{"step": "…", "tasks": [...]}]}]},
  "executable_manifest": [{"order": 1, "task_id": "…", "executable": true,
                           "execution_status": "not_executed"}],
  "blockers": [], "scores": {...},
  "status": "proposed", "validation": {}
}
```

- **ordering** : topologique (une tâche après ses prérequis) ;
- **structure** : phases → étapes → tâches ;
- **executable_manifest** : destiné au Kernel, **jamais exécuté ici** ;
- **status** : `proposed` → `validated` | `rejected` ; `validated` → `revoked`.

## 5. Le jeu de plans (`PlanSet`) — sortie complète

`{ objective, tasks[], strategies[], recommended (Plan), blockers[], traceability,
explanation }`. La **traçabilité** relie le plan aux enseignements/délibérations
intégrés et aux sources des tâches.

## 6. Déterminisme

Identifiants dérivés du **contenu** ; ordonnancement topologique **stable** (départage
par identifiant) ; horodatage figé (`as_of`). Planifier deux fois le même objectif
produit le **même** plan (vérifié en processus et cross-process).
