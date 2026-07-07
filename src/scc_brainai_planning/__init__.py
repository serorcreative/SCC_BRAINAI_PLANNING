"""SCC BrainAI Planning — couche officielle de planification de BrainAI.

Transforme un **objectif** en **plan d'action** structuré, ordonné, tracé et
gouverné : décomposition en phases/étapes/tâches, prérequis et dépendances,
ordonnancement, estimations (complexité/priorité/risque/impact), plusieurs
stratégies, plan recommandé, et **manifeste exécutable par le Kernel plus tard**.

Planning n'est ni Kernel (orchestration), ni Memory (expérience), ni Learning
(apprentissages), ni Reasoning (délibération). Il **réutilise** leurs interfaces
publiques pour intégrer enseignements et délibérations, sans modifier aucun composant.

Garde-fous : aucune auto-modification ; **aucune exécution automatique non
validée** ; **aucune décision souveraine sans validation humaine** (un plan reste
*proposé*). Fonctionne **sans aucune IA** (planification déterministe ; LLM optionnel
et branchable). Stdlib pur, sans réseau, déterministe.
"""

from __future__ import annotations

__version__ = "1.0.0"

from scc_brainai_planning.core.config import PlanningConfig, load_config
from scc_brainai_planning.core.model import (
    Objective,
    Plan,
    PlanSet,
    PlanStatus,
    PlanStrategy,
    PlanTask,
)
from scc_brainai_planning.engine import PlanningEngine
from scc_brainai_planning.providers.registry import ProviderRegistry
from scc_brainai_planning.validation import HumanValidationPolicy

__all__ = [
    "__version__",
    "PlanningEngine",
    "PlanningConfig",
    "load_config",
    "Objective",
    "PlanTask",
    "PlanStrategy",
    "Plan",
    "PlanSet",
    "PlanStatus",
    "ProviderRegistry",
    "HumanValidationPolicy",
]
