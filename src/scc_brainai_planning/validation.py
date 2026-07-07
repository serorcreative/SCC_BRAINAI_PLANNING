"""Validation humaine des plans — garde-fous de gouvernance.

**Aucune décision souveraine sans validation humaine ; aucune exécution automatique
non validée.** Un plan naît *proposé* et ne devient *validé*, *rejeté* ou *révoqué*
que par une **action humaine explicite**, tracée (approbateur, motif, horodatage).
"""

from __future__ import annotations

from typing import Any, Dict

from scc_brainai_planning.core.errors import ValidationError
from scc_brainai_planning.core.model import PlanStatus, can_transition


class HumanValidationPolicy:
    def __init__(self, as_of: str):
        self._as_of = as_of

    def _apply(self, plan: Dict[str, Any], target: str, action: str,
               approver: str, reason: str) -> Dict[str, Any]:
        if not approver:
            raise ValidationError("Une validation exige un approbateur humain explicite.")
        current = plan.get("status", PlanStatus.PROPOSED.value)
        if not can_transition(current, target):
            raise ValidationError(f"Transition interdite : {current} -> {target}.")
        plan["status"] = target
        plan["validation"] = {"action": action, "approver": approver, "reason": reason,
                              "at": self._as_of, "previous": plan.get("validation", {})}
        return plan

    def validate(self, plan: Dict[str, Any], approver: str, reason: str = "") -> Dict[str, Any]:
        return self._apply(plan, PlanStatus.VALIDATED.value, "validate", approver, reason)

    def reject(self, plan: Dict[str, Any], approver: str, reason: str = "") -> Dict[str, Any]:
        return self._apply(plan, PlanStatus.REJECTED.value, "reject", approver, reason)

    def revoke(self, plan: Dict[str, Any], approver: str, reason: str = "") -> Dict[str, Any]:
        return self._apply(plan, PlanStatus.REVOKED.value, "revoke", approver, reason)


__all__ = ["HumanValidationPolicy"]
