"""The high band must offer, not assert.

Cross-validation (eval/results.md, Diagnostic 4) put the ceiling on
high-confidence precision at 83.6%, and live testing found 4 of 11
menstruation questions returning verbatim/high and wrong. Asserting a KB
answer at that precision is the difference between an unhelpful reply and
misinformation, so this behaviour is pinned.
"""
import sys
import types

import pytest

from api.routers.ask import AskRequest


def _fake_results(top_score):
    return {"query_normalised": "q", "latency_ms": 3, "results": [
        {"answer_id": 42, "category": "c", "sub_category": "s", "source": "src",
         "question": "matched question", "answer": "the answer",
         "score": top_score, "path": "sindhi_dense"},
        {"answer_id": 43, "category": "c", "sub_category": "s", "source": "src",
         "question": "second question", "answer": "b", "score": 0.4, "path": "x"},
        {"answer_id": 44, "category": "c", "sub_category": "s", "source": "src",
         "question": "third question", "answer": "c", "score": 0.3, "path": "x"},
    ]}


@pytest.fixture
def pipeline(monkeypatch):
    mod = types.ModuleType("retrieval.pipeline")
    mod.search = lambda q, **kw: _fake_results(0.91)
    monkeypatch.setitem(sys.modules, "retrieval.pipeline", mod)
    import api.pipeline as p
    # keyword-only danger gate: the embedding fallback would load a model
    import api.safety.danger_gate as dg
    monkeypatch.setattr(p, "run_danger_gate", lambda t: dg.run_danger_gate(t, use_embedding=False))
    return p


def test_high_band_offers_the_question_instead_of_asserting(pipeline, monkeypatch):
    monkeypatch.setattr(pipeline, "CONFIRM_HIGH_BAND", True)
    r = pipeline.run_pipeline(AskRequest(query="benign question", language="sindhi"))
    assert r.path == "confirm"
    assert r.did_you_mean == "matched question"
    # the answer still ships, so confirming costs no second round-trip
    assert r.answer == "the answer"


def test_rejecting_has_somewhere_to_go(pipeline, monkeypatch):
    monkeypatch.setattr(pipeline, "CONFIRM_HIGH_BAND", True)
    r = pipeline.run_pipeline(AskRequest(query="benign question", language="sindhi"))
    assert r.alternatives == ["second question", "third question"]


def test_flag_off_restores_assert_verbatim(pipeline, monkeypatch):
    monkeypatch.setattr(pipeline, "CONFIRM_HIGH_BAND", False)
    r = pipeline.run_pipeline(AskRequest(query="benign question", language="sindhi"))
    assert r.path == "verbatim"
    assert r.did_you_mean is None
    assert r.alternatives == []


def test_other_bands_are_untouched(pipeline, monkeypatch):
    monkeypatch.setattr(pipeline, "CONFIRM_HIGH_BAND", True)
    mod = types.ModuleType("retrieval.pipeline")
    mod.search = lambda q, **kw: _fake_results(0.05)   # below tau_low
    monkeypatch.setitem(sys.modules, "retrieval.pipeline", mod)
    r = pipeline.run_pipeline(AskRequest(query="benign question", language="sindhi"))
    assert r.path == "refusal"
    assert r.did_you_mean is None
