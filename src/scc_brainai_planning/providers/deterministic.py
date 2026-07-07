"""Planificateur déterministe — la construction par défaut de BrainAI Planning.

Aucun LLM, aucun réseau : la planification est portée par des règles pures. C'est
ce fournisseur qui garantit que Planning **fonctionne toujours**, même sans IA.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from scc_brainai_planning.providers.base import BaseProvider


class DeterministicPlanner(BaseProvider):
    name = "deterministic"

    def available(self) -> bool:
        return True

    def suggest_tasks(self, goal: str, tasks: List[str]) -> Optional[List[Dict[str, Any]]]:
        return None

    def suggest_strategies(self, goal: str) -> Optional[List[str]]:
        return None

    def critique(self, plan: Dict[str, Any]) -> Optional[str]:
        return None


__all__ = ["DeterministicPlanner"]
