"""Tests de la construction de plan (décomposition, dépendances, stratégies)."""

from __future__ import annotations

import pytest

from scc_brainai_planning.core.errors import ObjectiveError


def test_planset_structure(planset):
    ps = planset
    for key in ("objective", "tasks", "strategies", "recommended", "blockers",
                "traceability", "explanation"):
        assert key in ps
    assert len(ps["tasks"]) == 10
    assert len(ps["strategies"]) == 3


def test_phases_steps_tasks(planset):
    phases = planset["recommended"]["structure"]["phases"]
    names = [p["phase"] for p in phases]
    assert names == ["Cadrage", "Conception", "Réalisation", "Validation", "Clôture"]
    # chaque phase a des étapes, chaque étape des tâches
    assert all(p["steps"] and all(s["tasks"] for s in p["steps"]) for p in phases)


def test_topological_ordering(planset):
    order = planset["recommended"]["ordering"]
    tbi = {t["id"]: t for t in planset["tasks"]}
    pos = {tid: i for i, tid in enumerate(order)}
    # chaque tâche vient après ses prérequis
    for tid in order:
        for pr in tbi[tid]["prerequisites"]:
            assert pos[pr] < pos[tid]


def test_estimates_bounded(planset):
    for t in planset["tasks"]:
        assert 1 <= t["complexity"] <= 5
        assert 1 <= t["priority"] <= 5
        assert 0.0 <= t["risk"] <= 1.0
        assert 0.0 <= t["impact"] <= 1.0


def test_strategies_scored_and_recommended(planset):
    for s in planset["strategies"]:
        assert "total" in s["scores"]
    rec = planset["recommended"]["strategy_name"]
    assert rec in {s["name"] for s in planset["strategies"]}
    # la stratégie recommandée a le meilleur score
    best = max(planset["strategies"], key=lambda s: s["scores"]["total"])
    assert planset["recommended"]["strategy_name"] == best["name"] or \
        planset["recommended"]["scores"]["total"] == best["scores"]["total"]


def test_given_tasks_and_dependencies(engine):
    ps = engine.plan("Objectif custom", given_tasks=[
        {"title": "Concevoir", "priority": 5, "impact": 0.8},
        {"title": "Implémenter", "prerequisites": ["Concevoir"], "impact": 0.7},
        {"title": "Tester", "prerequisites": ["Implémenter"], "priority": 5}])
    order = ps["recommended"]["ordering"]
    tbi = {t["id"]: t["title"] for t in ps["tasks"]}
    titles = [tbi[i] for i in order]
    assert titles.index("Concevoir") < titles.index("Implémenter") < titles.index("Tester")


def test_cycle_detected_as_blocker(engine):
    ps = engine.plan("Cycle", given_tasks=[
        {"title": "A", "prerequisites": ["B"]}, {"title": "B", "prerequisites": ["A"]}])
    assert any(b["type"] == "cycle" for b in ps["recommended"]["blockers"])


def test_missing_prerequisite_blocker(engine):
    ps = engine.plan("Missing", given_tasks=[
        {"title": "A", "prerequisites": ["Inexistant"]}])
    assert any(b["type"] == "missing_prerequisite" for b in ps["recommended"]["blockers"])


def test_empty_goal_rejected(engine):
    with pytest.raises(ObjectiveError):
        engine.plan("   ")


def test_executable_manifest_not_executed(planset):
    manifest = planset["recommended"]["executable_manifest"]
    assert manifest
    assert all(m["executable"] is True for m in manifest)
    assert all(m["execution_status"] == "not_executed" for m in manifest)
    # le manifeste est ordonné
    assert [m["order"] for m in manifest] == list(range(1, len(manifest) + 1))
