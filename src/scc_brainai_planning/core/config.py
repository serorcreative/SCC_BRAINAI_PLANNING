"""Configuration de la couche de planification BrainAI (JSON, sans dépendance).

La planification **transforme un objectif en plan d'action** structuré et gouverné.
Elle peut *intégrer* les enseignements de Learning (12) et les délibérations de
Reasoning (13) via leurs interfaces publiques — de façon **optionnelle et
dégradable**. Elle ne possède ni ne modifie aucune autre couche.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from scc_brainai_planning.core.errors import ConfigError

PLANNING_ROOT = Path(__file__).resolve().parents[3]       # .../14_BRAINAI_PLANNING
DEFAULT_SCC_ROOT = PLANNING_ROOT.parent                    # .../01_CCSC
DEFAULT_CONFIG_PATH = PLANNING_ROOT / "config" / "planning.json"

DEFAULT_AS_OF = "2026-07-06T00:00:00+00:00"

# Pondérations de sélection de stratégie (déterministes, bornées).
DEFAULT_WEIGHTS = {"impact": 0.35, "risk": 0.30, "complexity": 0.20, "coverage": 0.15}


@dataclass
class PlanningConfig:
    planning_root: Path = PLANNING_ROOT
    scc_root: Path = DEFAULT_SCC_ROOT
    data_dir: Path = PLANNING_ROOT / "data"
    as_of: str = DEFAULT_AS_OF
    integrate_learning: bool = True
    integrate_reasoning: bool = True
    weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    provider_order: List[str] = field(default_factory=lambda: ["deterministic"])
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def learning_src(self) -> Path:
        return self.scc_root / "12_BRAINAI_LEARNING" / "src"

    @property
    def reasoning_src(self) -> Path:
        return self.scc_root / "13_BRAINAI_REASONING" / "src"

    @property
    def plans_path(self) -> Path:
        return self.data_dir / "plans.jsonl"

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "planning_root": str(self.planning_root), "scc_root": str(self.scc_root),
            "data_dir": str(self.data_dir), "as_of": self.as_of,
            "integrate_learning": self.integrate_learning,
            "integrate_reasoning": self.integrate_reasoning,
            "weights": dict(self.weights), "provider_order": list(self.provider_order),
        }


def _resolve(base: Path, value: str) -> Path:
    p = Path(value).expanduser()
    return p if p.is_absolute() else (base / p).resolve()


def load_config(path: Optional[Path] = None) -> PlanningConfig:
    config = PlanningConfig()
    target = Path(path) if path else DEFAULT_CONFIG_PATH
    if not target.exists():
        if path is not None:
            raise ConfigError(f"Configuration introuvable : {target}")
        return config
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Configuration illisible ({target}) : {exc}") from exc

    base = config.planning_root
    if "scc_root" in raw:
        config.scc_root = _resolve(base, raw["scc_root"])
    paths = raw.get("paths", {})
    if "data_dir" in paths:
        config.data_dir = _resolve(base, paths["data_dir"])
    config.as_of = str(raw.get("as_of", DEFAULT_AS_OF))
    config.integrate_learning = bool(raw.get("integrate_learning", True))
    config.integrate_reasoning = bool(raw.get("integrate_reasoning", True))
    if "weights" in raw:
        config.weights = {**DEFAULT_WEIGHTS, **dict(raw["weights"])}
    config.provider_order = list(raw.get("provider_order", config.provider_order))
    config.extra = dict(raw.get("extra", {}))
    return config


__all__ = ["PLANNING_ROOT", "DEFAULT_SCC_ROOT", "DEFAULT_AS_OF", "DEFAULT_WEIGHTS",
           "PlanningConfig", "load_config"]
