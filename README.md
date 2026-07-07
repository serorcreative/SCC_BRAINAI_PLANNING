# SCC BrainAI Planning

**Couche officielle de planification de BrainAI.**

Planning **construit des plans d'action** structurés, ordonnés, traçables et
gouvernés. Il n'est ni Kernel (orchestration), ni Memory (expérience), ni Learning
(apprentissages), ni Reasoning (délibération) :

- **Kernel** orchestre. · **Memory** conserve l'expérience. · **Learning** en tire
  des apprentissages. · **Reasoning** délibère sur un problème.
- **Planning** transforme un **objectif** en **plan d'action** : phases → étapes →
  tâches, prérequis et dépendances, ordonnancement, estimations, plusieurs
  stratégies, plan recommandé, et **manifeste exécutable par le Kernel plus tard**.

> **Garde-fous : aucune auto-modification ; aucune exécution automatique non
> validée ; aucune décision souveraine sans validation humaine** (un plan reste
> *proposé*). **Fonctionne sans aucune IA** (planification déterministe ; LLM
> optionnel et branchable). Stdlib pur, sans réseau, déterministe.

## Réutilisation, jamais duplication

Planning **intègre** les enseignements de **Learning (12)** et les délibérations de
**Reasoning (13)** via leurs **interfaces publiques**, sans les modifier. Le
manifeste produit est destiné au **Kernel (10)** — mais Planning **n'exécute
jamais**.

## Installation

```bash
cd 14_BRAINAI_PLANNING
python -m pip install -e .        # expose la commande `scc-brain-planning`
```

Aucune dépendance externe.

## Utilisation (CLI)

```bash
scc-brain-planning plan "Construire la couche API de SCC"
scc-brain-planning plan "Migrer le stockage" \
    --task "Concevoir|Conception||5|0.8" \
    --task "Implémenter|Réalisation|Concevoir|4|0.7" \
    --task "Tester|Validation|Implémenter|5|0.8"
scc-brain-planning plan "Améliorer la gouvernance" --learning <id> --deliberation <id>
scc-brain-planning explain <id>                      # plan lisible (Markdown)
scc-brain-planning validate <id> --by frederique --reason "go"   # validation HUMAINE
scc-brain-planning reject <id> --by frederique
scc-brain-planning search --status proposed
scc-brain-planning report | audit | self-check | providers
```

## Utilisation (Python)

```python
from scc_brainai_planning import PlanningEngine

engine = PlanningEngine()
ps = engine.plan("Construire la couche API de SCC")
print(ps["recommended"]["strategy_name"], ps["recommended"]["status"])   # complète proposed
engine.validate(ps["id"], approver="frederique", reason="go")            # humain requis
```

## Ce qui est produit

Objectif → tâches (phases/étapes) · prérequis/dépendances · **ordonnancement
topologique** · estimations (complexité/priorité/risque/impact) · **plusieurs
stratégies** comparées et scorées · **plan recommandé** · **manifeste exécutable**
(`execution_status = not_executed`) · **blocages** (cycles, prérequis manquants) ·
traçabilité (Learning/Reasoning/sources).

## Composants

`PlanningEngine` · `Objective` · `PlanTask` · `PlanStrategy` · `Plan` · `PlanSet` ·
`HumanValidationPolicy` · `ProviderRegistry` (LLM optionnel) · `InsightSource`
(intégration Learning/Reasoning).

Détails : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
[`docs/PLANNING_MODEL.md`](docs/PLANNING_MODEL.md) ·
[`docs/PLANNING_PROCESS.md`](docs/PLANNING_PROCESS.md) ·
[`docs/GOVERNANCE_SAFETY.md`](docs/GOVERNANCE_SAFETY.md).

## Tests

```bash
python -m pytest -q      # 27 tests (déterministes ; 2 intégrations Learning/Reasoning réelles)
```
