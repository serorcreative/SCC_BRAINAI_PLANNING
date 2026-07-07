"""Index des jeux de plans (recherche déterministe)."""

from __future__ import annotations

from typing import Dict, List, Optional

from scc_brainai_planning.core.clock import canonical
from scc_brainai_planning.core.model import PlanSet


class PlanIndex:
    def __init__(self) -> None:
        self._by_id: Dict[str, PlanSet] = {}
        self._text: Dict[str, str] = {}

    def add(self, ps: PlanSet) -> None:
        self._by_id[ps.id] = ps
        blob = f"{ps.objective.goal} {ps.recommended.strategy_name} {canonical(ps.recommended.status)}"
        self._text[ps.id] = blob.lower()

    def rebuild(self, sets: List[PlanSet]) -> None:
        self._by_id.clear(); self._text.clear()
        for ps in sets:
            self.add(ps)

    def get(self, ps_id: str) -> Optional[PlanSet]:
        return self._by_id.get(ps_id)

    def search(self, *, status: Optional[str] = None, text: Optional[str] = None,
               limit: int = 50) -> List[PlanSet]:
        q = (text or "").strip().lower()
        out: List[PlanSet] = []
        for pid in sorted(self._by_id):
            ps = self._by_id[pid]
            if status and ps.recommended.status != status:
                continue
            if q and q not in self._text.get(pid, ""):
                continue
            out.append(ps)
        return out[:limit] if limit and limit > 0 else out

    def all(self) -> List[PlanSet]:
        return [self._by_id[k] for k in sorted(self._by_id)]

    def __len__(self) -> int:
        return len(self._by_id)


__all__ = ["PlanIndex"]
