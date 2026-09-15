"""
Tests for Phase 3 tier enforcement.
Tier A: serve normally
Tier B: serve with disclaimer flag = True
Tier C: block, return refusal
"""
import sys
import types
import pytest
from api.phase3_tier import enforce_tier, TIER_A, TIER_B, TIER_C, TIER_B_DISCLAIMER, TIER_C_REFUSAL
from api.routers.ask import AskRequest


def test_tier_a_serves_normally():
    answer, disclaimer, blocked = enforce_tier(TIER_A, "test answer", False)
    assert answer == "test answer"
    assert disclaimer is False
    assert blocked is False


def test_tier_b_sets_disclaimer():
    answer, disclaimer, blocked = enforce_tier(TIER_B, "test answer", False)
    assert answer == "test answer"
    assert disclaimer is True
    assert blocked is False


def test_tier_c_blocks():
    answer, disclaimer, blocked = enforce_tier(TIER_C, "test answer", False)
    assert blocked is True
    assert answer == TIER_C_REFUSAL


def test_tier_c_never_serves_original():
    answer, _, blocked = enforce_tier(TIER_C, "sensitive content", False)
    assert blocked is True
    assert answer != "sensitive content"


def test_missing_tier_serves_normally():
    answer, disclaimer, blocked = enforce_tier(None, "test answer", False)
    assert blocked is False


def _fake_results(review_tier="B", top_score=0.97):
    return {"query_normalised": "q", "latency_ms": 3, "results": [
        {"answer_id": 42, "category": "c", "sub_category": "s", "source": "src",
         "question": "matched question", "answer": "the answer",
         "score": top_score, "path": "sindhi_dense", "review_tier": review_tier},
    ]}


def _pipeline(monkeypatch, review_tier="B", top_score=0.97):
    mod = types.ModuleType("retrieval.pipeline")
    mod.search = lambda q, **kw: _fake_results(review_tier, top_score)
    monkeypatch.setitem(sys.modules, "retrieval.pipeline", mod)
    import api.pipeline as p
    import api.safety.danger_gate as dg
    monkeypatch.setattr(p, "run_danger_gate",
                        lambda t, **kw: dg.run_danger_gate(t, use_embedding=False))
    monkeypatch.setattr(p, "ELABORATE_ANSWERS", False)
    return p


def _ask(p):
    return p.run_pipeline(AskRequest(query="benign question", language="sindhi"))


def test_tier_c_row_is_never_served(monkeypatch):
    p = _pipeline(monkeypatch, review_tier="C")
    r = _ask(p)
    assert r.path == "tier_c_block"
    assert r.answer == TIER_C_REFUSAL
    assert r.retrieved_ids == []


def test_tier_b_row_is_served_normally(monkeypatch):
    p = _pipeline(monkeypatch, review_tier="B")
    r = _ask(p)
    assert r.path != "tier_c_block"
    assert r.path == "verbatim"


def test_tier_a_row_is_served_normally(monkeypatch):
    p = _pipeline(monkeypatch, review_tier="A")
    r = _ask(p)
    assert r.path != "tier_c_block"


def test_missing_review_tier_defaults_to_b_not_a_block():
    from api.phase3_tier import enforce_tier
    _, disclaimer, blocked = enforce_tier(None, "answer text", False)
    assert blocked is False


def test_tier_c_block_counts_as_a_refusal_in_the_scorecard(monkeypatch):
    from scripts.definition_of_done import REFUSAL_PATHS
    p = _pipeline(monkeypatch, review_tier="C")
    r = _ask(p)
    assert r.path == "tier_c_block"
    assert r.path in REFUSAL_PATHS
