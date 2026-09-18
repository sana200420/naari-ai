"""Stage 02b must thread enforce_tier()'s disclaimer value through to the
response, not just its `blocked` flag. Regression test for the bug where
`_, _, blocked = enforce_tier(...)` silently discarded the disclaimer."""
import sys
import types

from api.routers.ask import AskRequest


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


def test_tier_b_high_band_carries_disclaimer(monkeypatch):
    p = _pipeline(monkeypatch, review_tier="B", top_score=0.97)
    r = _ask(p)
    assert r.path == "verbatim"
    assert r.disclaimer is True, "Tier B answer served without the disclosure flag"


def test_tier_b_confirm_band_carries_disclaimer(monkeypatch):
    p = _pipeline(monkeypatch, review_tier="B", top_score=0.80)
    r = _ask(p)
    assert r.path == "confirm"
    assert r.disclaimer is True, "Tier B answer served without the disclosure flag"


def test_tier_a_high_band_has_no_disclaimer(monkeypatch):
    p = _pipeline(monkeypatch, review_tier="A", top_score=0.97)
    r = _ask(p)
    assert r.disclaimer is False, "Tier A answer wrongly carries a disclaimer"
