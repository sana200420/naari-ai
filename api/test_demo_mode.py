"""
Tests for demo mode behavior.
Demo mode = verbatim only, no LLM calls.
"""
import os
import sys
import types
import pytest


def _fake_results(top_score=0.97):
    return {"query_normalised": "q", "latency_ms": 3, "results": [
        {"answer_id": 1, "category": "c", "sub_category": "s", "source": "src",
         "question": "q", "answer": "verbatim answer",
         "score": top_score, "path": "sindhi_dense", "review_tier": "B"},
    ]}


def _pipeline(monkeypatch, score=0.97):
    mod = types.ModuleType("retrieval.pipeline")
    mod.search = lambda q, **kw: _fake_results(score)
    monkeypatch.setitem(sys.modules, "retrieval.pipeline", mod)
    import api.pipeline as p
    import api.safety.danger_gate as dg
    monkeypatch.setattr(p, "run_danger_gate",
                        lambda t, **kw: dg.run_danger_gate(t, use_embedding=False))
    monkeypatch.setattr(p, "ELABORATE_ANSWERS", False)
    return p


def test_high_confidence_returns_verbatim(monkeypatch):
    p = _pipeline(monkeypatch, score=0.97)
    from api.routers.ask import AskRequest
    r = p.run_pipeline(AskRequest(query="ماهواري ڇا آهي", language="sindhi"))
    assert r.path == "verbatim"
    assert r.answer == "verbatim answer"


def test_low_confidence_returns_refusal(monkeypatch):
    p = _pipeline(monkeypatch, score=0.10)
    from api.routers.ask import AskRequest
    r = p.run_pipeline(AskRequest(query="ماهواري ڇا آهي", language="sindhi"))
    assert r.path == "refusal"
