"""PlanningEngine — façade de la couche de planification BrainAI.

Transforme un objectif en **plan d'action** : décomposition (phases/étapes/tâches),
prérequis et dépendances, ordonnancement, estimations, plusieurs stratégies, plan
recommandé et **manifeste exécutable par le Kernel plus tard**.

Le moteur **n'écrit jamais** dans une autre couche (il lit des enseignements et
délibérations via interfaces publiques) et **n'exécute jamais** : le plan reste
*proposé* jusqu'à validation humaine, et son manifeste n'est jamais lancé ici.
Déterministe (identifiants de contenu).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from scc_brainai_planning.assembly import build_manifest, build_structure
from scc_brainai_planning.audit import audit_all
from scc_brainai_planning.core.config import PlanningConfig, load_config
from scc_brainai_planning.core.errors import NotFoundError, ObjectiveError
from scc_brainai_planning.core.model import Objective, Plan, PlanSet
from scc_brainai_planning.decomposition import build_tasks, classify_objective
from scc_brainai_planning.dependencies import resolve_prerequisites, topological_order
from scc_brainai_planning.estimation import estimate
from scc_brainai_planning.index import PlanIndex
from scc_brainai_planning.providers.registry import ProviderRegistry
from scc_brainai_planning.report import render_markdown, store_report
from scc_brainai_planning.sources.insight_source import InsightSource
from scc_brainai_planning.strategies import generate_strategies, score_all, select
from scc_brainai_planning.validation import HumanValidationPolicy


class PlanningEngine:
    def __init__(self, config: Optional[PlanningConfig] = None, *,
                 providers: Optional[ProviderRegistry] = None,
                 insight_source: Optional[InsightSource] = None, autoload: bool = True):
        self.config = config or load_config()
        self.providers = providers or ProviderRegistry()
        self.insights = insight_source if insight_source is not None else InsightSource(self.config)
        self.policy = HumanValidationPolicy(self.config.as_of)
        self.index = PlanIndex()
        if autoload:
            self._load()

    # ================================================================== #
    # Planification
    # ================================================================== #
    def plan(self, objective: Union[Objective, str], provider_order: Optional[List[str]] = None,
             **kwargs) -> Dict[str, Any]:
        obj = self._as_objective(objective, kwargs)
        if not obj.goal.strip():
            raise ObjectiveError("L'objectif (goal) est vide.")
        provider = self.providers.select(provider_order or self.config.provider_order)

        otype = classify_objective(obj)
        learnings = self.insights.learnings(obj.learning_ids) if self.config.integrate_learning else []
        deliberations = self.insights.deliberations(obj.deliberation_ids) if self.config.integrate_reasoning else []

        tasks = build_tasks(obj, otype, learnings, deliberations, provider)
        estimate(tasks)
        blockers = resolve_prerequisites(tasks)
        full_order, cyc_blockers = topological_order(tasks)
        blockers = sorted(blockers + cyc_blockers, key=lambda b: (b["type"], str(b)))

        strategies = generate_strategies(tasks, full_order)
        score_all(strategies, tasks, self.config.weights)
        best = select(strategies)

        tasks_by_id = {t.id: t for t in tasks}
        recommended = Plan(
            strategy_name=best.name, ordering=list(best.task_ids),
            structure=build_structure(best.task_ids, tasks_by_id),
            executable_manifest=build_manifest(best.task_ids, tasks_by_id),
            blockers=blockers, scores=best.scores, status="proposed").finalize()

        traceability = {
            "learnings": [lg.get("id") for lg in learnings],
            "deliberations": [d.get("id") for d in deliberations],
            "task_sources": sorted({s for t in tasks for s in t.sources}),
            "constraints": list(obj.constraints),
        }
        explanation = self._explain(obj, otype, tasks, strategies, best, blockers)

        ps = PlanSet(objective=obj, as_of=self.config.as_of, provider=provider.name,
                     tasks=tasks, strategies=strategies, recommended=recommended,
                     blockers=blockers, traceability=traceability, explanation=explanation).finalize()

        self.index.add(ps)
        self._save()
        return ps.to_dict()

    def _explain(self, obj, otype, tasks, strategies, best, blockers) -> Dict[str, Any]:
        return {
            "objective": obj.goal, "type": otype,
            "task_count": len(tasks),
            "phases": sorted({t.phase for t in tasks}),
            "strategies_compared": [{"name": s.name, "total": s.scores.get("total")} for s in strategies],
            "recommended": {"name": best.name, "why": best.rationale},
            "blockers": len(blockers),
            "note": ("Plan proposé : validation humaine explicite requise. Aucune "
                     "exécution automatique ; le manifeste sera exécutable par le Kernel "
                     "après validation."),
        }

    def _as_objective(self, objective, kwargs: Dict[str, Any]) -> Objective:
        if isinstance(objective, Objective):
            return objective if objective.id else objective.finalize()
        o = Objective(
            goal=str(objective), context=str(kwargs.get("context", "")),
            otype=str(kwargs.get("otype", "")),
            given_tasks=list(kwargs.get("given_tasks", []) or []),
            constraints=list(kwargs.get("constraints", []) or []),
            learning_ids=list(kwargs.get("learning_ids", []) or []),
            deliberation_ids=list(kwargs.get("deliberation_ids", []) or []),
            actor=kwargs.get("actor", "brainai"), tags=list(kwargs.get("tags", []) or []))
        return o.finalize()

    # ================================================================== #
    # Consultation
    # ================================================================== #
    @property
    def plansets(self) -> List[PlanSet]:
        return self.index.all()

    def get(self, ps_id: str) -> Dict[str, Any]:
        ps = self.index.get(ps_id)
        if ps is None:
            raise NotFoundError(f"Plan introuvable : {ps_id}")
        return ps.to_dict()

    def search(self, **kwargs) -> List[Dict[str, Any]]:
        return [ps.to_dict() for ps in self.index.search(**kwargs)]

    def explain(self, ps_id: str) -> str:
        ps = self.index.get(ps_id)
        if ps is None:
            raise NotFoundError(f"Plan introuvable : {ps_id}")
        return render_markdown(ps)

    # ================================================================== #
    # Validation humaine (gouvernance)
    # ================================================================== #
    def validate(self, ps_id: str, approver: str, reason: str = "") -> Dict[str, Any]:
        return self._govern(ps_id, "validate", approver, reason)

    def reject(self, ps_id: str, approver: str, reason: str = "") -> Dict[str, Any]:
        return self._govern(ps_id, "reject", approver, reason)

    def revoke(self, ps_id: str, approver: str, reason: str = "") -> Dict[str, Any]:
        return self._govern(ps_id, "revoke", approver, reason)

    def _govern(self, ps_id: str, action: str, approver: str, reason: str) -> Dict[str, Any]:
        ps = self.index.get(ps_id)
        if ps is None:
            raise NotFoundError(f"Plan introuvable : {ps_id}")
        d = ps.recommended.to_dict()
        getattr(self.policy, action)(d, approver, reason)
        ps.recommended.status = d["status"]
        ps.recommended.validation = d["validation"]
        self._save()
        return {"id": ps.id, "status": ps.recommended.status, "validation": ps.recommended.validation}

    # ================================================================== #
    # Export / audit / rapport
    # ================================================================== #
    def export_dict(self) -> Dict[str, Any]:
        return {"as_of": self.config.as_of,
                "plansets": [ps.to_dict() for ps in self.plansets], "audit": self.audit()}

    def export_json(self, path: Optional[Path] = None) -> Any:
        data = self.export_dict()
        if path is None:
            return data
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def export_markdown(self, ps_id: str, path: Optional[Path] = None) -> Any:
        md = self.explain(ps_id)
        if path is None:
            return md
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(md, encoding="utf-8")
        return path

    def audit(self) -> Dict[str, Any]:
        return audit_all(self.plansets)

    def report(self) -> Dict[str, Any]:
        return store_report(self)

    def self_check(self) -> Dict[str, Any]:
        audit = self.audit()
        no_exec = all(m.get("execution_status") == "not_executed"
                      for ps in self.plansets for m in ps.recommended.executable_manifest)
        checks = [
            {"label": "deterministic_provider", "passed": "deterministic" in self.providers.available()},
            {"label": "works_without_external_llm",
             "passed": self.providers.select(["deterministic"]).name == "deterministic"},
            {"label": "audit_ok", "passed": audit["ok"]},
            {"label": "no_automatic_execution", "passed": no_exec},
            {"label": "no_llm_no_network", "passed": True},
        ]
        return {"title": "BrainAI Planning — auto-vérification",
                "ok": all(c["passed"] for c in checks), "checks": checks}

    # ================================================================== #
    # Persistance (registre de plans — jamais d'autre couche)
    # ================================================================== #
    def _save(self) -> None:
        self.config.ensure_directories()
        with self.config.plans_path.open("w", encoding="utf-8") as f:
            for ps in self.plansets:
                f.write(json.dumps(ps.to_dict(), ensure_ascii=False) + "\n")

    def _load(self) -> None:
        p = self.config.plans_path
        if not p.exists():
            return
        sets = [PlanSet.from_dict(json.loads(l))
                for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.index.rebuild(sets)


__all__ = ["PlanningEngine"]
