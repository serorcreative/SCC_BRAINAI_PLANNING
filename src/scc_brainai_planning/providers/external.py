"""Adaptateurs LLM externes — emplacements d'extension (non branchés en V1).

Matérialisent la place d'un LLM (Claude, ChatGPT, Gemini…) dans la planification,
**sans aucun appel réseau**. Indisponibles tant qu'un transport n'est pas fourni ;
le moteur les ignore alors et planifie de façon déterministe.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from scc_brainai_planning.providers.base import BaseProvider


class ExternalPlanner(BaseProvider):
    name = "external"

    def __init__(self, client: Optional[Any] = None):
        self._client = client

    def available(self) -> bool:
        return self._client is not None

    def _guard(self):
        raise NotImplementedError(
            f"Fournisseur '{self.name}' : transport non implémenté dans le socle (aucun réseau).")

    def suggest_tasks(self, goal: str, tasks: List[str]) -> Optional[List[Dict[str, Any]]]:
        if not self.available():
            return None
        self._guard()

    def suggest_strategies(self, goal: str) -> Optional[List[str]]:
        if not self.available():
            return None
        self._guard()

    def critique(self, plan: Dict[str, Any]) -> Optional[str]:
        if not self.available():
            return None
        self._guard()


class ClaudePlanner(ExternalPlanner):
    name = "claude"


class ChatGPTPlanner(ExternalPlanner):
    name = "chatgpt"


class GeminiPlanner(ExternalPlanner):
    name = "gemini"


KNOWN_EXTERNAL = {"claude": ClaudePlanner, "chatgpt": ChatGPTPlanner, "gemini": GeminiPlanner}

__all__ = ["ExternalPlanner", "ClaudePlanner", "ChatGPTPlanner", "GeminiPlanner", "KNOWN_EXTERNAL"]
