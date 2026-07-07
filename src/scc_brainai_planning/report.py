"""Rapports de planification — résumé d'un jeu de plans et du registre."""

from __future__ import annotations

from typing import Any, Dict, List

from scc_brainai_planning.core.model import PlanSet


def planset_summary(ps: PlanSet) -> Dict[str, Any]:
    return {
        "id": ps.id, "goal": ps.objective.goal,
        "tasks": len(ps.tasks), "strategies": len(ps.strategies),
        "recommended": ps.recommended.strategy_name,
        "status": ps.recommended.status,
        "blockers": len(ps.recommended.blockers),
    }


def store_report(engine) -> Dict[str, Any]:
    sets = engine.plansets
    by_status: Dict[str, int] = {}
    for ps in sets:
        s = ps.recommended.status
        by_status[s] = by_status.get(s, 0) + 1
    audit = engine.audit()
    return {
        "as_of": engine.config.as_of,
        "total_plansets": len(sets),
        "by_plan_status": dict(sorted(by_status.items())),
        "audit_ok": audit["ok"],
        "plansets": [planset_summary(ps) for ps in sets],
        "safety_note": "Tout plan est proposé ; aucune exécution automatique ; validation humaine requise.",
    }


def render_markdown(ps: PlanSet) -> str:
    lines: List[str] = [
        f"# Plan — {ps.id}",
        "",
        f"> `as_of` : {ps.as_of} · fournisseur : {ps.provider}",
        "",
        f"**Objectif** : {ps.objective.goal}",
        "",
        "## Stratégies comparées", "",
        "| Stratégie | Score | Impact | Risque | Couverture | Tâches |",
        "|-----------|-------|--------|--------|------------|--------|",
    ]
    for s in ps.strategies:
        sc = s.scores
        lines.append(f"| {s.name} | {sc.get('total')} | {sc.get('impact')} | {sc.get('risk')} "
                     f"| {sc.get('coverage')} | {len(s.task_ids)} |")
    lines += ["", f"## Plan recommandé : **{ps.recommended.strategy_name}** "
              f"(statut : {ps.recommended.status})", ""]
    for phase in ps.recommended.structure.get("phases", []):
        lines.append(f"### Phase — {phase['phase']}")
        for step in phase["steps"]:
            lines.append(f"- **{step['step']}**")
            for t in step["tasks"]:
                lines.append(f"  - {t['title']}  _(priorité {t['priority']}, risque {t['risk']})_")
        lines.append("")
    if ps.recommended.blockers:
        lines += ["## Blocages", ""]
        for b in ps.recommended.blockers:
            lines.append(f"- `{b['type']}` {b}")
        lines.append("")
    lines += ["## Manifeste exécutable (par le Kernel, plus tard)", "",
              f"- {len(ps.recommended.executable_manifest)} tâche(s) ordonnée(s), "
              "toutes `execution_status = not_executed`.",
              "",
              "> Plan **proposé** : validation humaine explicite requise ; "
              "jamais exécuté automatiquement.",
              "",
              "*Planification déterministe BrainAI — sans réseau ni LLM obligatoire.*"]
    return "\n".join(lines) + "\n"


__all__ = ["planset_summary", "store_report", "render_markdown"]
