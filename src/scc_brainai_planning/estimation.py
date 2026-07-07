"""Estimation : complexité, priorité, risque, impact (déterministe).

Ajuste les estimations des tâches par des règles de mots-clés, en respectant les
valeurs déjà fournies. Bornées : complexité 1..5, priorité 1..5, risque/impact 0..1.
"""

from __future__ import annotations

from typing import List

from scc_brainai_planning.core.model import PlanTask

_HIGH_RISK = ["migration", "basculer", "production", "irréversible", "irreversible", "sécurité", "securite"]
_HIGH_PRIORITY = ["test", "revue", "gouvernance", "validation", "contrainte"]
_LOW_PRIORITY = ["documenter", "documentation"]


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def estimate(tasks: List[PlanTask]) -> List[PlanTask]:
    for t in tasks:
        text = (t.title + " " + t.description).lower()
        if any(w in text for w in _HIGH_RISK):
            t.risk = _clamp(round(max(t.risk, 0.6), 3), 0.0, 1.0)
            t.complexity = _clamp(max(t.complexity, 4), 1, 5)
        if any(w in text for w in _HIGH_PRIORITY):
            t.priority = _clamp(max(t.priority, 4), 1, 5)
        if any(w in text for w in _LOW_PRIORITY):
            t.priority = _clamp(min(t.priority, 3), 1, 5)
        # bornage systématique
        t.complexity = _clamp(int(t.complexity), 1, 5)
        t.priority = _clamp(int(t.priority), 1, 5)
        t.risk = _clamp(round(float(t.risk), 3), 0.0, 1.0)
        t.impact = _clamp(round(float(t.impact), 3), 0.0, 1.0)
    return tasks


__all__ = ["estimate"]
