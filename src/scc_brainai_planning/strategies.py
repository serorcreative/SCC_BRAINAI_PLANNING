"""Stratégies de plan : génère plusieurs variantes, les score et recommande.

Trois variantes déterministes : **complète** (couverture maximale), **essentielle**
(tâches critiques + prérequis) et **rapide** (fort impact + prérequis). Chaque
variante est scorée (impact / risque / complexité / couverture) ; la recommandation
retient la meilleure — mais reste un **plan proposé** (validation humaine requise).
"""

from __future__ import annotations

from typing import Any, Dict, List

from scc_brainai_planning.core.model import PlanStrategy, PlanTask


def _closure(selected: set, tasks_by_id: Dict[str, PlanTask]) -> set:
    """Ajoute transitivement les prérequis des tâches sélectionnées."""
    out = set(selected)
    changed = True
    while changed:
        changed = False
        for tid in list(out):
            for pr in tasks_by_id[tid].prerequisites:
                if pr in tasks_by_id and pr not in out:
                    out.add(pr)
                    changed = True
    return out


def _ordered(subset: set, full_order: List[str]) -> List[str]:
    return [tid for tid in full_order if tid in subset]


def generate_strategies(tasks: List[PlanTask], full_order: List[str]) -> List[PlanStrategy]:
    tasks_by_id = {t.id: t for t in tasks}
    all_ids = set(tasks_by_id)

    complete = _ordered(all_ids, full_order)

    essential_seed = {t.id for t in tasks if t.priority >= 4}
    essential = _ordered(_closure(essential_seed, tasks_by_id), full_order) or complete

    fast_seed = {t.id for t in tasks if t.impact >= 0.6}
    fast = _ordered(_closure(fast_seed, tasks_by_id), full_order) or complete

    variants = [
        ("complète", "Couverture maximale : toutes les tâches, dans l'ordre.", complete),
        ("essentielle", "Tâches critiques (priorité ≥ 4) et leurs prérequis.", essential),
        ("rapide", "Tâches à fort impact (≥ 0.6) et leurs prérequis.", fast),
    ]
    strategies: List[PlanStrategy] = []
    for name, desc, ids in variants:
        strategies.append(PlanStrategy(name=name, description=desc, task_ids=ids).finalize())
    # déduplique par id (deux variantes identiques → une seule)
    uniq: Dict[str, PlanStrategy] = {}
    for s in strategies:
        uniq.setdefault(s.id, s)
    return sorted(uniq.values(), key=lambda s: s.id)


def score_strategy(strategy: PlanStrategy, tasks_by_id: Dict[str, PlanTask],
                   total_tasks: int, weights: Dict[str, float]) -> Dict[str, float]:
    st = [tasks_by_id[i] for i in strategy.task_ids if i in tasks_by_id]
    if not st:
        return {"impact": 0.0, "risk": 1.0, "complexity": 1.0, "coverage": 0.0, "total": 0.0}
    impact = round(sum(t.impact for t in st) / len(st), 3)
    risk = round(sum(t.risk for t in st) / len(st), 3)
    complexity = round((sum(t.complexity for t in st) / len(st)) / 5.0, 3)
    coverage = round(len(st) / total_tasks, 3) if total_tasks else 0.0
    total = round(
        weights.get("impact", 0.35) * impact
        + weights.get("risk", 0.30) * (1.0 - risk)
        + weights.get("complexity", 0.20) * (1.0 - complexity)
        + weights.get("coverage", 0.15) * coverage, 4)
    return {"impact": impact, "risk": risk, "complexity": complexity,
            "coverage": coverage, "total": total}


def score_all(strategies: List[PlanStrategy], tasks: List[PlanTask],
              weights: Dict[str, float]) -> List[PlanStrategy]:
    tasks_by_id = {t.id: t for t in tasks}
    for s in strategies:
        s.scores = score_strategy(s, tasks_by_id, len(tasks), weights)
        s.rationale = (f"Score {s.scores['total']} — impact {s.scores['impact']}, "
                       f"risque {s.scores['risk']}, couverture {s.scores['coverage']}.")
    return strategies


def select(strategies: List[PlanStrategy]) -> PlanStrategy:
    return sorted(strategies, key=lambda s: (-s.scores.get("total", 0.0), s.id))[0]


__all__ = ["generate_strategies", "score_strategy", "score_all", "select"]
