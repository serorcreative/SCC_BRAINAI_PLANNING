"""Intégration des enseignements (Learning 12) et délibérations (Reasoning 13).

Réutilise, **sans les modifier**, les interfaces publiques de Learning
(``search``/``get``) et de Reasoning (``get``) pour intégrer au plan : des tâches
issues de recommandations validées, et des contraintes/tâches issues d'une décision
délibérée. L'intégration est **optionnelle et dégradable** : un composant absent est
ignoré, la planification continue.
"""

from __future__ import annotations

import importlib
import sys
from typing import Any, Dict, List, Optional

from scc_brainai_planning.core.config import PlanningConfig


class InsightSource:
    def __init__(self, config: PlanningConfig, learning_engine: Optional[Any] = None,
                 reasoning_engine: Optional[Any] = None):
        self._config = config
        self._learn = learning_engine
        self._reason = reasoning_engine
        self._learn_tried = learning_engine is not None
        self._reason_tried = reasoning_engine is not None

    def _add_path(self, path) -> bool:
        if not path.exists():
            return False
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
        return True

    def _learning(self):
        if self._learn is None and not self._learn_tried:
            self._learn_tried = True
            if self._add_path(self._config.learning_src):
                try:
                    self._learn = importlib.import_module("scc_brainai_learning").LearningEngine()
                except Exception:  # noqa: BLE001
                    self._learn = None
        return self._learn

    def _reasoning(self):
        if self._reason is None and not self._reason_tried:
            self._reason_tried = True
            if self._add_path(self._config.reasoning_src):
                try:
                    self._reason = importlib.import_module("scc_brainai_reasoning").ReasoningEngine()
                except Exception:  # noqa: BLE001
                    self._reason = None
        return self._reason

    def available(self) -> Dict[str, bool]:
        return {"learning": self._learning() is not None, "reasoning": self._reasoning() is not None}

    # -- enseignements Learning ----------------------------------------- #
    def learnings(self, ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        eng = self._learning()
        if eng is None:
            return []
        try:
            if ids:
                out = []
                for lid in ids:
                    try:
                        out.append(eng.get(lid))
                    except Exception:  # noqa: BLE001
                        continue
                return out
            # sinon : recommandations validées (exploitables), triées
            return eng.search(kind="recommendation", status="validated", limit=50)
        except Exception:  # noqa: BLE001
            return []

    # -- délibérations Reasoning ---------------------------------------- #
    def deliberations(self, ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        eng = self._reasoning()
        if eng is None or not ids:
            return []
        out = []
        for did in ids:
            try:
                out.append(eng.get(did))
            except Exception:  # noqa: BLE001
                continue
        return out


__all__ = ["InsightSource"]
