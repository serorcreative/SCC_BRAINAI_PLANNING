"""Test d'intégration : intégrer Learning (12) et Reasoning (13) via interfaces publiques.

Construit un enseignement validé (Learning) et une délibération (Reasoning) dans des
stores isolés, injecte une InsightSource pointant dessus, et vérifie que le plan
intègre bien ces sources — sans modifier aucun composant. Ignoré proprement si les
couches ne sont pas localisables.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_LEARN_SRC = _ROOT / "12_BRAINAI_LEARNING" / "src"
_REASON_SRC = _ROOT / "13_BRAINAI_REASONING" / "src"
_MEM_SRC = _ROOT / "11_BRAINAI_MEMORY" / "src"

_available = _LEARN_SRC.exists() and _REASON_SRC.exists() and _MEM_SRC.exists()
if _available:
    for p in (_LEARN_SRC, _REASON_SRC, _MEM_SRC):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

pytestmark = pytest.mark.skipif(not _available, reason="Learning/Reasoning non localisables.")


def _build_reasoning(tmp_path):
    from scc_brainai_reasoning.core.config import ReasoningConfig
    from scc_brainai_reasoning.engine import ReasoningEngine
    eng = ReasoningEngine(config=ReasoningConfig(data_dir=tmp_path / "reason", ground_facts=False))
    d = eng.reason("Faut-il adopter l'approche A ou B ?",
                   options=[{"name": "Approche A", "benefit": 0.8}, {"name": "Approche B", "benefit": 0.4}])
    return eng, d["id"]


def test_plan_integrates_reasoning(tmp_path):
    from scc_brainai_planning.core.config import PlanningConfig
    from scc_brainai_planning.engine import PlanningEngine
    from scc_brainai_planning.sources.insight_source import InsightSource

    reason_eng, delib_id = _build_reasoning(tmp_path)
    cfg = PlanningConfig(data_dir=tmp_path / "plan", integrate_learning=False, integrate_reasoning=True)
    source = InsightSource(cfg, reasoning_engine=reason_eng)
    eng = PlanningEngine(config=cfg, insight_source=source)

    ps = eng.plan("Mettre en œuvre la décision retenue", deliberation_ids=[delib_id])
    # une tâche issue de la délibération est présente et tracée
    titles = [t["title"] for t in ps["tasks"]]
    assert any(t.startswith("Mettre en œuvre la décision") for t in titles)
    sources = {s for t in ps["tasks"] for s in t["sources"]}
    assert any(s.startswith("reasoning:") for s in sources)
    assert delib_id in ps["traceability"]["deliberations"]
    assert eng.audit()["ok"] is True


def test_plan_integrates_learning(tmp_path):
    from scc_brainai_learning.core.config import LearningConfig
    from scc_brainai_learning.engine import LearningEngine
    from scc_brainai_learning.sources.memory_source import MemorySource
    from scc_brainai_memory import BrainMemoryStore, MemoryConfig
    from scc_brainai_memory.recorder import KernelRecorder
    from scc_brainai_planning.core.config import PlanningConfig
    from scc_brainai_planning.engine import PlanningEngine
    from scc_brainai_planning.sources.insight_source import InsightSource

    # mémoire peuplée -> apprentissage -> recommandation validée
    mem = BrainMemoryStore(config=MemoryConfig(data_dir=tmp_path / "mem"))
    rec = KernelRecorder(mem)
    for _ in range(4):
        rec.record_response({"ok": True, "as_of": "2026-07-06T00:00:00+00:00",
                             "request": {"query": "q", "actor": "brainai", "autonomy": "A3"},
                             "intent": "governance", "plan": {"intent": "governance", "steps": [{"action": "a"}]},
                             "agents": [{"id": "SCC-AGENT-0002"}], "governance": {"doctrines": ["SCC-DOC-0016"], "adrs": []},
                             "runtime": {"job_id": "j", "kind": "echo", "status": "succeeded", "trust": "T1",
                                         "human_approval_required": False}, "provider": {"selected": "deterministic"}})
    lcfg = LearningConfig(data_dir=tmp_path / "learn")
    lcfg.extra["memory_data_dir"] = str(mem.config.data_dir)
    learn = LearningEngine(config=lcfg, memory_source=MemorySource(lcfg, store=mem))
    learn.analyze()
    reco = learn.search(kind="recommendation")[0]
    learn.validate(reco["id"], "frederique", "utile")

    cfg = PlanningConfig(data_dir=tmp_path / "plan", integrate_learning=True, integrate_reasoning=False)
    eng = PlanningEngine(config=cfg, insight_source=InsightSource(cfg, learning_engine=learn))
    ps = eng.plan("Améliorer la gouvernance", learning_ids=[reco["id"]])
    assert any(t["title"].startswith("Appliquer la recommandation") for t in ps["tasks"])
    assert reco["id"] in ps["traceability"]["learnings"]
    assert eng.audit()["ok"] is True
