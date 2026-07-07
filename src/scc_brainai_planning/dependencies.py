"""Prérequis, dépendances, ordonnancement et blocages (déterministe).

Résout les prérequis (titres → identifiants), construit le graphe de dépendances,
détecte les **blocages** (prérequis introuvable, cycle) et produit un **ordre
topologique** stable (départage par identifiant).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from scc_brainai_planning.core.model import PlanTask


def resolve_prerequisites(tasks: List[PlanTask]) -> List[Dict[str, Any]]:
    """Convertit les prérequis-titres en identifiants ; retourne les blocages."""
    title_to_id: Dict[str, str] = {}
    for t in tasks:
        title_to_id.setdefault(t.title, t.id)

    blockers: List[Dict[str, Any]] = []
    for t in tasks:
        resolved: List[str] = []
        for pr in t.prerequisites:
            if pr in title_to_id:
                resolved.append(title_to_id[pr])
            elif pr in {x.id for x in tasks}:
                resolved.append(pr)
            else:
                blockers.append({"type": "missing_prerequisite", "task": t.id,
                                 "missing": pr})
        t.prerequisites = sorted(set(resolved))
        t.seal()
    return blockers


def topological_order(tasks: List[PlanTask]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Ordre topologique déterministe (Kahn) ; détecte les cycles."""
    ids = {t.id for t in tasks}
    deps: Dict[str, set] = {t.id: {p for p in t.prerequisites if p in ids} for t in tasks}
    # arêtes sortantes : prérequis -> dépendant
    dependents: Dict[str, List[str]] = {tid: [] for tid in ids}
    for tid, prereqs in deps.items():
        for p in prereqs:
            dependents[p].append(tid)

    indeg = {tid: len(deps[tid]) for tid in ids}
    ready = sorted([tid for tid in ids if indeg[tid] == 0])
    order: List[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for nxt in sorted(dependents[node]):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(nxt)
        ready.sort()

    blockers: List[Dict[str, Any]] = []
    if len(order) != len(ids):
        cyclic = sorted(tid for tid in ids if tid not in set(order))
        blockers.append({"type": "cycle", "tasks": cyclic})
        # complète l'ordre par les tâches cycliques (déterministe) pour ne rien perdre
        order += cyclic
    return order, blockers


__all__ = ["resolve_prerequisites", "topological_order"]
