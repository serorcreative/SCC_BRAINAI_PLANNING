"""Décomposition d'un objectif en phases, étapes et tâches (déterministe).

Combine : les tâches fournies par l'appelant, un gabarit canonique par type
d'objectif, les enseignements de Learning et les délibérations de Reasoning.
Les prérequis sont exprimés par **titre** ici ; ils sont résolus en identifiants
par :mod:`scc_brainai_planning.dependencies`.
"""

from __future__ import annotations

from typing import Any, Dict, List

from scc_brainai_planning.core.model import Objective, PlanTask

_TYPES = [
    ("migrate", ["migrer", "migration", "basculer", "refonte"]),
    ("build", ["construire", "bâtir", "batir", "créer", "creer", "développer", "developper"]),
    ("improve", ["améliorer", "ameliorer", "optimiser", "renforcer", "réduire", "reduire"]),
    ("investigate", ["analyser", "investiguer", "diagnostiquer", "étudier", "etudier"]),
    ("rollout", ["déployer", "deployer", "livrer", "publier", "mettre en production"]),
]

# Gabarit canonique : (titre, phase, étape, [prérequis-titres], complexité, priorité, risque, impact)
_TEMPLATE = [
    ("Clarifier l'objectif", "Cadrage", "Analyse", [], 1, 5, 0.1, 0.6),
    ("Recenser prérequis et contraintes", "Cadrage", "Analyse", ["Clarifier l'objectif"], 2, 5, 0.2, 0.6),
    ("Décomposer en composants", "Conception", "Design", ["Recenser prérequis et contraintes"], 3, 4, 0.2, 0.7),
    ("Concevoir l'approche", "Conception", "Design", ["Décomposer en composants"], 3, 4, 0.3, 0.7),
    ("Réaliser les composants", "Réalisation", "Build", ["Concevoir l'approche"], 4, 4, 0.4, 0.8),
    ("Intégrer les composants", "Réalisation", "Build", ["Réaliser les composants"], 3, 3, 0.4, 0.7),
    ("Tester", "Validation", "Verify", ["Intégrer les composants"], 3, 5, 0.3, 0.8),
    ("Revue et gouvernance", "Validation", "Verify", ["Tester"], 2, 5, 0.2, 0.7),
    ("Documenter", "Clôture", "Deliver", ["Revue et gouvernance"], 2, 3, 0.1, 0.5),
    ("Livrer", "Clôture", "Deliver", ["Revue et gouvernance"], 2, 4, 0.3, 0.7),
]


def classify_objective(objective: Objective) -> str:
    if objective.otype:
        return objective.otype
    g = (objective.goal + " " + objective.context).lower()
    for otype, kws in _TYPES:
        if any(k in g for k in kws):
            return otype
    return "generic"


def _task_from_dict(d: Dict[str, Any], default_phase: str = "Réalisation") -> PlanTask:
    return PlanTask(
        title=str(d.get("title", "")).strip(),
        description=str(d.get("description", "")),
        phase=str(d.get("phase", default_phase)), step=str(d.get("step", "")),
        prerequisites=list(d.get("prerequisites", []) or []),   # titres à ce stade
        kind=str(d.get("kind", "task")), agent=str(d.get("agent", "")),
        complexity=int(d.get("complexity", 2)), priority=int(d.get("priority", 3)),
        risk=float(d.get("risk", 0.3)), impact=float(d.get("impact", 0.5)),
        sources=list(d.get("sources", []) or []), tags=list(d.get("tags", []) or []))


def build_tasks(objective: Objective, otype: str, learnings: List[Dict[str, Any]],
                deliberations: List[Dict[str, Any]], provider=None) -> List[PlanTask]:
    tasks: List[PlanTask] = []

    if objective.given_tasks:
        for d in objective.given_tasks:
            t = _task_from_dict(d)
            if t.title:
                t.tags = t.tags + ["given"]
                tasks.append(t)
    else:
        for (title, phase, step, prereq, cx, pr, rk, im) in _TEMPLATE:
            tasks.append(PlanTask(title=title, phase=phase, step=step, prerequisites=list(prereq),
                                  complexity=cx, priority=pr, risk=rk, impact=im,
                                  sources=[f"template:{otype}"], tags=["canonical", otype]))

    # Intégration Learning : chaque recommandation validée → une tâche d'application.
    for lg in learnings:
        title = f"Appliquer la recommandation : {lg.get('title', lg.get('id', ''))}"
        tasks.append(PlanTask(
            title=title, phase="Réalisation", step="Improvements",
            prerequisites=[], kind="apply_recommendation",
            complexity=2, priority=3, risk=float(lg.get("impact", 0.4)) * 0.5,
            impact=float(lg.get("impact", 0.5)), sources=[f"learning:{lg.get('id')}"],
            tags=["learning", "integration"]))

    # Intégration Reasoning : la décision délibérée → une tâche de mise en œuvre.
    for delib in deliberations:
        dec = delib.get("decision", {})
        opt = dec.get("data", {}).get("option", "")
        if opt:
            tasks.append(PlanTask(
                title=f"Mettre en œuvre la décision : {opt}", phase="Réalisation", step="Decision",
                prerequisites=[], kind="implement_decision", complexity=3, priority=4,
                risk=0.4, impact=0.8, sources=[f"reasoning:{delib.get('id')}"],
                tags=["reasoning", "integration"], data={"decision_status": dec.get("status")}))

    # Extension LLM (optionnelle) : suggestions de tâches, jamais requises.
    if provider is not None and provider.available():
        for d in provider.suggest_tasks(objective.goal, [t.title for t in tasks]) or []:
            if isinstance(d, dict) and d.get("title"):
                t = _task_from_dict(d)
                t.tags = t.tags + ["assisted"]
                tasks.append(t)

    for t in tasks:
        t.finalize()
    # déduplique par id (titre+phase+étape+kind), tri déterministe
    uniq: Dict[str, PlanTask] = {}
    for t in tasks:
        uniq.setdefault(t.id, t)
    return sorted(uniq.values(), key=lambda t: t.id)


__all__ = ["classify_objective", "build_tasks"]
