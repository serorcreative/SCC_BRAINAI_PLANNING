"""Assemblage d'un plan : structure hiérarchique et manifeste exécutable.

Le **manifeste** est destiné à être exécuté **plus tard par le Kernel** — jamais
ici, jamais automatiquement. Il porte explicitement ``execution_status =
not_executed`` et n'est activable qu'après validation humaine du plan.
"""

from __future__ import annotations

from typing import Any, Dict, List

from scc_brainai_planning.core.model import PlanTask

# Ordre canonique des phases (pour un affichage stable de la structure).
_PHASE_ORDER = ["Cadrage", "Conception", "Réalisation", "Validation", "Clôture"]


def build_structure(ordered_ids: List[str], tasks_by_id: Dict[str, PlanTask]) -> Dict[str, Any]:
    """Construit phases → étapes → tâches, en suivant l'ordre topologique."""
    phases: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for tid in ordered_ids:
        t = tasks_by_id[tid]
        step_map = phases.setdefault(t.phase, {})
        step_map.setdefault(t.step or "—", []).append(
            {"id": t.id, "title": t.title, "priority": t.priority,
             "complexity": t.complexity, "risk": t.risk, "impact": t.impact})

    def phase_key(name: str):
        return (_PHASE_ORDER.index(name) if name in _PHASE_ORDER else len(_PHASE_ORDER), name)

    out = []
    for phase in sorted(phases, key=phase_key):
        steps = [{"step": step, "tasks": phases[phase][step]} for step in sorted(phases[phase])]
        out.append({"phase": phase, "steps": steps})
    return {"phases": out}


def build_manifest(ordered_ids: List[str], tasks_by_id: Dict[str, PlanTask]) -> List[Dict[str, Any]]:
    """Manifeste ordonné, exécutable par le Kernel plus tard (jamais ici)."""
    manifest: List[Dict[str, Any]] = []
    for i, tid in enumerate(ordered_ids, start=1):
        t = tasks_by_id[tid]
        manifest.append({
            "order": i, "task_id": t.id, "title": t.title,
            "kind": t.kind, "agent": t.agent, "phase": t.phase,
            "prerequisites": list(t.prerequisites),
            "executable": True, "execution_status": "not_executed"})
    return manifest


__all__ = ["build_structure", "build_manifest"]
