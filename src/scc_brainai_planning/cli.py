"""CLI de la couche de planification BrainAI (``scc-brain-planning``).

Planifier un objectif, expliquer, **valider humainement** un plan, exporter,
auditer. Sortie JSON déterministe. Aucune commande n'exécute un plan : seule la
validation humaine change son statut ; le manifeste reste ``not_executed``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from scc_brainai_planning import __version__
from scc_brainai_planning.core.config import load_config
from scc_brainai_planning.core.errors import PlanningError
from scc_brainai_planning.engine import PlanningEngine


def _out(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _engine(args) -> PlanningEngine:
    return PlanningEngine(config=load_config(args.config))


def _parse_tasks(raw: Optional[List[str]]) -> List[Dict[str, Any]]:
    """'titre|phase|prereq1,prereq2|priorité|impact' (champs après le titre optionnels)."""
    tasks = []
    for item in raw or []:
        parts = [p.strip() for p in item.split("|")]
        t: Dict[str, Any] = {"title": parts[0]}
        if len(parts) > 1 and parts[1]:
            t["phase"] = parts[1]
        if len(parts) > 2 and parts[2]:
            t["prerequisites"] = [p.strip() for p in parts[2].split(",") if p.strip()]
        if len(parts) > 3 and parts[3]:
            try:
                t["priority"] = int(parts[3])
            except ValueError:
                pass
        if len(parts) > 4 and parts[4]:
            try:
                t["impact"] = float(parts[4])
            except ValueError:
                pass
        tasks.append(t)
    return tasks


def cmd_plan(args) -> int:
    eng = _engine(args)
    order = args.provider_order.split(",") if args.provider_order else None
    try:
        ps = eng.plan(args.goal, context=args.context or "", otype=args.type or "",
                      given_tasks=_parse_tasks(args.task), constraints=args.constraint or [],
                      learning_ids=args.learning or [], deliberation_ids=args.deliberation or [],
                      provider_order=order)
    except PlanningError as exc:
        _out({"error": str(exc)}); return 1
    _out(ps)
    return 0


def cmd_get(args) -> int:
    try:
        _out(_engine(args).get(args.id)); return 0
    except PlanningError as exc:
        _out({"error": str(exc)}); return 1


def cmd_explain(args) -> int:
    try:
        print(_engine(args).explain(args.id)); return 0
    except PlanningError as exc:
        _out({"error": str(exc)}); return 1


def cmd_search(args) -> int:
    _out(_engine(args).search(status=args.status, text=args.text, limit=int(args.limit))); return 0


def _transition(args, action: str) -> int:
    try:
        _out(getattr(_engine(args), action)(args.id, args.by, args.reason)); return 0
    except PlanningError as exc:
        _out({"error": str(exc)}); return 1


def cmd_report(args) -> int:
    _out(_engine(args).report()); return 0


def cmd_audit(args) -> int:
    a = _engine(args).audit(); _out(a); return 0 if a["ok"] else 1


def cmd_self_check(args) -> int:
    sc = _engine(args).self_check(); _out(sc); return 0 if sc["ok"] else 1


def cmd_providers(args) -> int:
    _out(_engine(args).providers.to_dict()); return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scc-brain-planning",
                                     description="Couche de planification de BrainAI (plans proposés).")
    parser.add_argument("--version", action="version", version=f"scc-brain-planning {__version__}")
    parser.add_argument("--config", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="Transformer un objectif en plan d'action.")
    p.add_argument("goal")
    p.add_argument("--context", default=None)
    p.add_argument("--type", default=None, help="build/migrate/improve/investigate/rollout")
    p.add_argument("--task", action="append", help="'titre|phase|prereqs|priorité|impact' (répétable)")
    p.add_argument("--constraint", action="append")
    p.add_argument("--learning", action="append", help="id d'enseignement Learning (répétable)")
    p.add_argument("--deliberation", action="append", help="id de délibération Reasoning (répétable)")
    p.add_argument("--provider-order", default=None)
    p.set_defaults(func=cmd_plan)

    p_get = sub.add_parser("get", help="Détail d'un jeu de plans."); p_get.add_argument("id"); p_get.set_defaults(func=cmd_get)
    p_ex = sub.add_parser("explain", help="Explication lisible (Markdown)."); p_ex.add_argument("id"); p_ex.set_defaults(func=cmd_explain)

    p_s = sub.add_parser("search", help="Recherche de plans.")
    p_s.add_argument("--status", default=None); p_s.add_argument("--text", default=None)
    p_s.add_argument("--limit", default="50"); p_s.set_defaults(func=cmd_search)

    for action in ("validate", "reject", "revoke"):
        pa = sub.add_parser(action, help=f"{action} (validation humaine) un plan.")
        pa.add_argument("id"); pa.add_argument("--by", required=True); pa.add_argument("--reason", default="")
        pa.set_defaults(func=lambda a, _act=action: _transition(a, _act))

    sub.add_parser("report", help="Rapport du registre de plans.").set_defaults(func=cmd_report)
    sub.add_parser("audit", help="Audit (intégrité, traçabilité, sûreté).").set_defaults(func=cmd_audit)
    sub.add_parser("self-check", help="Auto-vérification.").set_defaults(func=cmd_self_check)
    sub.add_parser("providers", help="Fournisseurs de planification.").set_defaults(func=cmd_providers)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


__all__ = ["main", "build_parser"]
