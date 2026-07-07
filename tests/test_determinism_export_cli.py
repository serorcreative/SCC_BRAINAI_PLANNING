"""Tests de déterminisme, export, explication et CLI."""

from __future__ import annotations

import json

from scc_brainai_planning.cli import main
from scc_brainai_planning.core.config import PlanningConfig
from scc_brainai_planning.engine import PlanningEngine


def _plan(data_dir):
    eng = PlanningEngine(config=PlanningConfig(data_dir=data_dir, integrate_learning=False,
                                               integrate_reasoning=False))
    return eng.plan("Construire la couche API de SCC",
                    given_tasks=[{"title": "Concevoir", "priority": 5, "impact": 0.8},
                                 {"title": "Implémenter", "prerequisites": ["Concevoir"], "impact": 0.7}])


def test_deterministic_planning(tmp_path):
    a = _plan(tmp_path / "a")
    b = _plan(tmp_path / "b")
    assert json.dumps(a, sort_keys=True, ensure_ascii=False) == \
           json.dumps(b, sort_keys=True, ensure_ascii=False)


def test_explain_markdown(engine, planset):
    md = engine.explain(planset["id"])
    for section in ("## Stratégies comparées", "## Plan recommandé", "## Manifeste exécutable"):
        assert section in md
    assert "validation humaine" in md
    assert "not_executed" in md


def test_export_and_report(engine, planset, tmp_path):
    data = engine.export_dict()
    assert data["plansets"]
    jp = engine.export_json(tmp_path / "p.json")
    assert jp.exists()
    report = engine.report()
    assert report["total_plansets"] == 1
    assert report["by_plan_status"].get("proposed") == 1


def test_persistence_roundtrip(config):
    e1 = PlanningEngine(config=config)
    ps = e1.plan("Objectif persistant")
    e2 = PlanningEngine(config=config)   # relit depuis le disque
    assert e2.get(ps["id"])["id"] == ps["id"]
    assert e2.audit()["ok"] is True


def test_cli_plan_and_validate(tmp_path, capsys):
    cfg = tmp_path / "planning.json"
    cfg.write_text(json.dumps({"paths": {"data_dir": str(tmp_path / "d")},
                               "as_of": "2026-07-06T00:00:00+00:00",
                               "integrate_learning": False, "integrate_reasoning": False}),
                   encoding="utf-8")
    rc = main(["--config", str(cfg), "plan", "Construire la couche API",
               "--task", "Concevoir|Conception||5|0.8",
               "--task", "Implémenter|Réalisation|Concevoir|4|0.7"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    pid = out["id"]
    assert out["recommended"]["status"] == "proposed"
    rc = main(["--config", str(cfg), "validate", pid, "--by", "frederique", "--reason", "go"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["status"] == "validated"


def test_cli_audit(tmp_path, capsys):
    cfg = tmp_path / "planning.json"
    cfg.write_text(json.dumps({"paths": {"data_dir": str(tmp_path / "d")},
                               "integrate_learning": False, "integrate_reasoning": False}),
                   encoding="utf-8")
    main(["--config", str(cfg), "plan", "Objectif X"])
    capsys.readouterr()
    rc = main(["--config", str(cfg), "audit"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["ok"] is True
