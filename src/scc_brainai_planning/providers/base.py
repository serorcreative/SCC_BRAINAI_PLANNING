"""Contrat des fournisseurs de planification — point d'extension pour un futur LLM.

La planification **ne dépend d'aucun LLM** : sa construction par défaut est
déterministe (règles). Un LLM pourra plus tard *enrichir* les plans (suggérer des
tâches, des stratégies, critiquer un ordonnancement) **sans jamais** en devenir un
prérequis ni valider/exécuter quoi que ce soit.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class PlanningProvider(Protocol):
    name: str

    def available(self) -> bool: ...

    def suggest_tasks(self, goal: str, tasks: List[str]) -> Optional[List[Dict[str, Any]]]: ...

    def suggest_strategies(self, goal: str) -> Optional[List[str]]: ...

    def critique(self, plan: Dict[str, Any]) -> Optional[str]: ...


class BaseProvider:
    name = "base"

    def available(self) -> bool:
        return False

    def suggest_tasks(self, goal: str, tasks: List[str]) -> Optional[List[Dict[str, Any]]]:
        return None

    def suggest_strategies(self, goal: str) -> Optional[List[str]]:
        return None

    def critique(self, plan: Dict[str, Any]) -> Optional[str]:
        return None


__all__ = ["PlanningProvider", "BaseProvider"]
