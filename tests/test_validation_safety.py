"""Tests des garde-fous : validation humaine, non-exécution, audit."""

from __future__ import annotations

import pytest

from scc_brainai_planning.core.errors import ValidationError
from scc_brainai_planning.providers.registry import ProviderRegistry


def test_plan_starts_proposed(planset):
    assert planset["recommended"]["status"] == "proposed"


def test_validate_requires_human(engine, planset):
    with pytest.raises(ValidationError):
        engine.validate(planset["id"], "")


def test_validate_then_revoke(engine, planset):
    pid = planset["id"]
    engine.validate(pid, "frederique", "go")
    assert engine.get(pid)["recommended"]["status"] == "validated"
    assert engine.get(pid)["recommended"]["validation"]["approver"] == "frederique"
    engine.revoke(pid, "frederique", "obsolète")
    assert engine.get(pid)["recommended"]["status"] == "revoked"


def test_illegal_transition_refused(engine, planset):
    pid = planset["id"]
    engine.validate(pid, "frederique")
    with pytest.raises(ValidationError):
        engine.reject(pid, "frederique")


def test_reject_flow(engine, planset):
    engine.reject(planset["id"], "frederique", "hors périmètre")
    assert engine.get(planset["id"])["recommended"]["status"] == "rejected"


def test_audit_ok(engine, planset):
    a = engine.audit()
    assert a["ok"] is True


def test_audit_detects_tampering(engine, planset):
    pid = planset["id"]
    ps = engine.index.get(pid)
    ps.tasks[0].title = "TAMPERED"
    a = engine.audit()
    assert a["per_planset"][pid]["integrity"]["ok"] is False


def test_self_check_no_execution(engine, planset):
    sc = engine.self_check()
    assert sc["ok"] is True
    labels = {c["label"] for c in sc["checks"]}
    assert {"no_automatic_execution", "works_without_external_llm", "no_llm_no_network"} <= labels


def test_providers_fallback():
    reg = ProviderRegistry()
    assert "deterministic" in reg.available()
    for name in ("claude", "chatgpt", "gemini"):
        assert name in reg.names() and name not in reg.available()
    assert reg.select(["claude", "chatgpt"]).name == "deterministic"
