"""Audit de la planification : intégrité, traçabilité, sûreté (gouvernance).

* **intégrité** : l'empreinte de chaque tâche correspond à son contenu ;
* **traçabilité** : chaque tâche cite au moins une source ; le plan référence des
  tâches existantes ;
* **sûreté** : tout plan non-proposé porte un approbateur **humain** ; aucune tâche
  du manifeste n'est marquée exécutée (aucune exécution automatique).
"""

from __future__ import annotations

from typing import Any, Dict, List

from scc_brainai_planning.core.model import PlanSet, PlanStatus


def audit_planset(ps: PlanSet) -> Dict[str, Any]:
    integrity_broken = sorted(t.id for t in ps.tasks if not t.verify())
    untraced = sorted(t.id for t in ps.tasks if not t.sources)

    task_ids = {t.id for t in ps.tasks}
    dangling = sorted(tid for tid in ps.recommended.ordering if tid not in task_ids)

    plan = ps.recommended
    status = plan.status
    safe = True
    reasons: List[str] = []
    if status != PlanStatus.PROPOSED.value and not plan.validation.get("approver"):
        safe = False; reasons.append("plan non-proposé sans approbateur humain")
    executed = [m for m in plan.executable_manifest if m.get("execution_status") != "not_executed"]
    if executed:
        safe = False; reasons.append("manifeste marqué exécuté (exécution non permise)")

    return {
        "ok": not integrity_broken and not untraced and not dangling and safe,
        "integrity": {"ok": not integrity_broken, "broken": integrity_broken},
        "traceability": {"ok": not untraced and not dangling,
                         "untraced": untraced, "dangling_ordering": dangling},
        "safety": {"ok": safe, "reasons": reasons, "plan_status": status},
        "tasks": len(ps.tasks),
    }


def audit_all(sets: List[PlanSet]) -> Dict[str, Any]:
    reports = {ps.id: audit_planset(ps) for ps in sets}
    return {"ok": all(r["ok"] for r in reports.values()) if reports else True,
            "count": len(sets), "per_planset": reports}


__all__ = ["audit_planset", "audit_all"]
