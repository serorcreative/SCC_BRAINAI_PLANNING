"""Fixtures des tests de planification (isolées, déterministes, hermétiques).

L'intégration de Learning/Reasoning est désactivée par défaut pour des tests
rapides ; un test dédié vérifie l'intégration réelle via leurs interfaces publiques.
"""

from __future__ import annotations

import pytest

from scc_brainai_planning.core.config import PlanningConfig
from scc_brainai_planning.engine import PlanningEngine


@pytest.fixture
def config(tmp_path):
    return PlanningConfig(data_dir=tmp_path / "data",
                          integrate_learning=False, integrate_reasoning=False)


@pytest.fixture
def engine(config):
    return PlanningEngine(config=config)


@pytest.fixture
def planset(engine):
    return engine.plan("Construire la couche API de SCC")
