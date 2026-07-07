# Architecture de BrainAI Planning

## 1. Position dans SCC

Planning (`14`) est la couche qui **construit des plans d'action**. Elle se situe
entre la délibération (Reasoning) et l'orchestration (Kernel) : elle transforme un
objectif (souvent issu d'une décision délibérée) en un plan ordonné que le Kernel
pourra exécuter **plus tard**.

```
   Learning (12)      Reasoning (13)                       Kernel (10)
   (enseignements)    (délibérations)                      (exécution future)
        \                 \                                    ▲
         \ interfaces publiques (lecture)                      │ manifeste exécutable
          ─────────────────────────────────────               │ (jamais exécuté ici)
   ▶ Planning (14) ── PlanningEngine : objectif -> tâches -> dépendances
        │              -> ordonnancement -> stratégies -> PLAN RECOMMANDÉ (proposé)
   data/plans.jsonl (registre de plans — seul espace d'écriture)
```

## 2. Distinction des rôles

| Couche | Rôle |
|--------|------|
| Kernel (10) | orchestre / exécute |
| Memory (11) | conserve l'expérience |
| Learning (12) | apprend de l'expérience |
| Reasoning (13) | délibère sur un problème → décision candidate |
| **Planning (14)** | **transforme un objectif en plan d'action ordonné et gouverné** |

Aucune duplication : Reasoning décide *quoi faire* ; Planning structure *comment, et
dans quel ordre* ; le Kernel *exécutera* plus tard.

## 3. Chaîne de planification (déterministe)

```
Objective
  │  classify_objective() -> type   (build/migrate/improve/investigate/rollout/generic)
  ▼
build_tasks()      -> tâches (fournies + gabarit + Learning + Reasoning)
estimate()         -> complexité / priorité / risque / impact
resolve_prerequisites() + topological_order()  -> ordre + BLOCAGES (cycles, prérequis manquants)
generate_strategies() + score_all() -> variantes (complète / essentielle / rapide)
select()           -> stratégie recommandée
build_structure() + build_manifest() -> PLAN (phases/étapes + manifeste exécutable)
```

Chaque étape est **pure** : mêmes entrées ⇒ même plan. Identifiants dérivés du
contenu (idempotence).

## 4. Composants

```
core/        config (as_of, poids) · errors · clock (digest) · model (Objective/Task/Strategy/Plan/PlanSet)
providers/   base · deterministic (défaut) · external (Claude/ChatGPT/Gemini) · registry
sources/     insight_source (Learning + Reasoning, lecture seule)
decomposition · estimation · dependencies · strategies · assembly
validation   HumanValidationPolicy (gouvernance)
index        PlanIndex · audit · report
engine       PlanningEngine (façade)
cli          scc-brain-planning
```

## 5. Frontière de sûreté

Le `PlanningEngine` **ne détient aucune API d'écriture** vers une autre couche : il
lit des enseignements/délibérations (interfaces publiques) et n'écrit que dans son
registre de plans. Il **n'exécute jamais** : le manifeste porte
`execution_status = not_executed`, et le plan reste **proposé** jusqu'à validation
humaine (voir [`GOVERNANCE_SAFETY.md`](GOVERNANCE_SAFETY.md)).

## 6. Invariants tenus

| Invariant | Comment |
|-----------|---------|
| Aucun composant modifié | intégration via interfaces publiques seules |
| Aucune auto-modification | aucun accès en écriture hors du registre de plans |
| Aucune exécution automatique non validée | manifeste `not_executed` ; jamais lancé ici |
| Aucune décision souveraine sans humain | plan `proposed` + `HumanValidationPolicy` |
| Fonctionne sans LLM | planification déterministe ; LLM optionnel |
| Aucun réseau / dépendance externe | stdlib pur ; adaptateurs LLM non branchés |
| Déterminisme maximal | identifiants de contenu + horodatage figé + règles pures |
