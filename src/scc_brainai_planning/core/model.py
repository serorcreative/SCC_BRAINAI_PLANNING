"""Modèle de planification BrainAI.

Un **PlanTask** est l'unité atomique (tracée, estimée, chaînée par prérequis). Les
tâches se regroupent en **phases** et **étapes**. Une **PlanStrategy** est une
variante de plan ; un **Plan** est une stratégie matérialisée (ordonnée, gouvernée,
exécutable par le Kernel plus tard). Un **Objective** est l'entrée ; un **PlanSet**
la sortie complète.

Tout est déterministe (identifiants dérivés du contenu) et **gouverné** : un plan
reste *proposé* jusqu'à validation humaine ; il n'est jamais exécuté automatiquement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar, Dict, List

from scc_brainai_planning.core.clock import digest, short_id


class PlanStatus(str, Enum):
    PROPOSED = "proposed"
    VALIDATED = "validated"
    REJECTED = "rejected"
    REVOKED = "revoked"


_PLAN_TRANSITIONS = {
    "proposed": {"validated", "rejected"},
    "validated": {"revoked"},
    "rejected": set(),
    "revoked": set(),
}


def can_transition(current: str, target: str) -> bool:
    return target in _PLAN_TRANSITIONS.get(current, set())


@dataclass
class PlanTask:
    """Unité d'action atomique, estimée et tracée."""

    title: str = ""
    description: str = ""
    phase: str = "Réalisation"
    step: str = ""
    prerequisites: List[str] = field(default_factory=list)   # ids de tâches amont
    kind: str = "task"                                        # indice d'exécution (agent/intent/action)
    agent: str = ""                                           # rôle Kernel cible (optionnel)
    complexity: int = 2                                       # 1..5
    priority: int = 3                                         # 1..5 (5 = critique)
    risk: float = 0.3                                         # 0..1
    impact: float = 0.5                                       # 0..1
    sources: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    id: str = ""
    hash: str = ""

    KIND: ClassVar[str] = "task"

    def _identity(self) -> Dict[str, Any]:
        # identité stable (n'inclut pas les prérequis, résolus après coup)
        return {"title": self.title, "phase": self.phase, "step": self.step, "kind": self.kind}

    def _content(self) -> Dict[str, Any]:
        return {**self._identity(), "description": self.description,
                "prerequisites": sorted(self.prerequisites), "agent": self.agent,
                "complexity": self.complexity, "priority": self.priority,
                "risk": self.risk, "impact": self.impact, "sources": sorted(self.sources)}

    def finalize(self) -> "PlanTask":
        self.id = short_id("task", self._identity())
        self.hash = digest(self._content())
        return self

    def seal(self) -> "PlanTask":
        """Recalcule l'empreinte après résolution des prérequis (id inchangé)."""
        self.hash = digest(self._content())
        return self

    def verify(self) -> bool:
        return self.hash == digest(self._content())

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "kind": self.kind, "title": self.title,
                "description": self.description, "phase": self.phase, "step": self.step,
                "prerequisites": list(self.prerequisites), "agent": self.agent,
                "complexity": self.complexity, "priority": self.priority,
                "risk": self.risk, "impact": self.impact, "sources": list(self.sources),
                "tags": list(self.tags), "data": dict(self.data), "hash": self.hash}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlanTask":
        t = cls(title=str(d.get("title", "")), description=str(d.get("description", "")),
                phase=str(d.get("phase", "Réalisation")), step=str(d.get("step", "")),
                prerequisites=list(d.get("prerequisites", []) or []),
                kind=str(d.get("kind", "task")), agent=str(d.get("agent", "")),
                complexity=int(d.get("complexity", 2)), priority=int(d.get("priority", 3)),
                risk=float(d.get("risk", 0.3)), impact=float(d.get("impact", 0.5)),
                sources=list(d.get("sources", []) or []), tags=list(d.get("tags", []) or []),
                data=dict(d.get("data", {}) or {}))
        t.id = str(d.get("id", "")) or t.finalize().id
        t.hash = str(d.get("hash", "")) or t.hash
        return t


@dataclass
class PlanStrategy:
    """Variante de plan : sous-ensemble ordonné de tâches + scores + justification."""

    name: str
    description: str = ""
    task_ids: List[str] = field(default_factory=list)   # ordonnées
    scores: Dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    id: str = ""

    def finalize(self) -> "PlanStrategy":
        self.id = short_id("strat", {"name": self.name, "task_ids": self.task_ids})
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "description": self.description,
                "task_ids": list(self.task_ids), "scores": dict(self.scores),
                "rationale": self.rationale}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlanStrategy":
        s = cls(name=str(d.get("name", "")), description=str(d.get("description", "")),
                task_ids=list(d.get("task_ids", []) or []), scores=dict(d.get("scores", {}) or {}),
                rationale=str(d.get("rationale", "")))
        s.id = str(d.get("id", "")) or s.finalize().id
        return s


@dataclass
class Plan:
    """Stratégie matérialisée : ordonnée, structurée, gouvernée, exécutable plus tard."""

    strategy_name: str = ""
    ordering: List[str] = field(default_factory=list)          # ids de tâches (ordre topologique)
    structure: Dict[str, Any] = field(default_factory=dict)    # phases -> étapes -> tâches
    executable_manifest: List[Dict[str, Any]] = field(default_factory=list)
    blockers: List[Dict[str, Any]] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    status: str = PlanStatus.PROPOSED.value
    validation: Dict[str, Any] = field(default_factory=dict)
    id: str = ""

    def finalize(self) -> "Plan":
        self.id = short_id("plan", {"strategy": self.strategy_name, "ordering": self.ordering})
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "strategy_name": self.strategy_name, "ordering": list(self.ordering),
                "structure": dict(self.structure), "executable_manifest": list(self.executable_manifest),
                "blockers": list(self.blockers), "scores": dict(self.scores),
                "status": self.status, "validation": dict(self.validation)}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Plan":
        p = cls(strategy_name=str(d.get("strategy_name", "")), ordering=list(d.get("ordering", []) or []),
                structure=dict(d.get("structure", {}) or {}),
                executable_manifest=list(d.get("executable_manifest", []) or []),
                blockers=list(d.get("blockers", []) or []), scores=dict(d.get("scores", {}) or {}),
                status=str(d.get("status", "proposed")), validation=dict(d.get("validation", {}) or {}))
        p.id = str(d.get("id", "")) or p.finalize().id
        return p


@dataclass
class Objective:
    """Objectif à transformer en plan."""

    goal: str
    context: str = ""
    otype: str = ""                                        # build / migrate / improve / investigate / rollout
    given_tasks: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    learning_ids: List[str] = field(default_factory=list)  # enseignements à intégrer
    deliberation_ids: List[str] = field(default_factory=list)  # délibérations à intégrer
    actor: str = "brainai"
    tags: List[str] = field(default_factory=list)
    id: str = ""

    def finalize(self) -> "Objective":
        self.id = short_id("obj", {"goal": self.goal, "given_tasks": self.given_tasks,
                                   "constraints": sorted(self.constraints)})
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "goal": self.goal, "context": self.context, "otype": self.otype,
                "given_tasks": list(self.given_tasks), "constraints": list(self.constraints),
                "learning_ids": list(self.learning_ids), "deliberation_ids": list(self.deliberation_ids),
                "actor": self.actor, "tags": list(self.tags)}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Objective":
        o = cls(goal=str(d.get("goal", "")), context=str(d.get("context", "")),
                otype=str(d.get("otype", "")), given_tasks=list(d.get("given_tasks", []) or []),
                constraints=list(d.get("constraints", []) or []),
                learning_ids=list(d.get("learning_ids", []) or []),
                deliberation_ids=list(d.get("deliberation_ids", []) or []),
                actor=str(d.get("actor", "brainai")), tags=list(d.get("tags", []) or []))
        o.id = str(d.get("id", "")) or o.finalize().id
        return o


@dataclass
class PlanSet:
    """Sortie complète : objectif, tâches, stratégies, plan recommandé, traçabilité."""

    objective: Objective
    as_of: str = ""
    tasks: List[PlanTask] = field(default_factory=list)
    strategies: List[PlanStrategy] = field(default_factory=list)
    recommended: Plan = field(default_factory=Plan)
    blockers: List[Dict[str, Any]] = field(default_factory=list)
    traceability: Dict[str, Any] = field(default_factory=dict)
    explanation: Dict[str, Any] = field(default_factory=dict)
    provider: str = "deterministic"
    id: str = ""

    def finalize(self) -> "PlanSet":
        self.id = short_id("planset", {"objective": self.objective.id,
                                       "recommended": self.recommended.id})
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "as_of": self.as_of, "provider": self.provider,
                "objective": self.objective.to_dict(),
                "tasks": [t.to_dict() for t in self.tasks],
                "strategies": [s.to_dict() for s in self.strategies],
                "recommended": self.recommended.to_dict(),
                "blockers": list(self.blockers), "traceability": dict(self.traceability),
                "explanation": dict(self.explanation)}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PlanSet":
        ps = cls(objective=Objective.from_dict(d.get("objective", {})),
                 as_of=str(d.get("as_of", "")), provider=str(d.get("provider", "deterministic")),
                 tasks=[PlanTask.from_dict(x) for x in d.get("tasks", [])],
                 strategies=[PlanStrategy.from_dict(x) for x in d.get("strategies", [])],
                 recommended=Plan.from_dict(d.get("recommended", {})),
                 blockers=list(d.get("blockers", []) or []),
                 traceability=dict(d.get("traceability", {}) or {}),
                 explanation=dict(d.get("explanation", {}) or {}))
        ps.id = str(d.get("id", "")) or ps.finalize().id
        return ps


__all__ = [
    "PlanStatus", "can_transition", "PlanTask", "PlanStrategy", "Plan",
    "Objective", "PlanSet",
]
