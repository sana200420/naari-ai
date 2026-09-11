"""Three confidence tiers, measured rather than assumed.

eval/tau_high_sweep.csv over 247 gold queries:

    >= 0.95   26% of traffic, 84% precise  -> assert
    0.75-0.95 17% of traffic, 49% precise  -> ask "did you mean X?"
    < 0.75                                 -> generate, hedged, or refuse

The middle tier exists because a coin flip is the worst thing to state as fact
and the best thing to ask about. At the old TAU_HIGH=0.75 the system asserted
42% of traffic at 70% precision, meaning 12.6% of ALL queries were answered
incorrectly as verified fact.
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


def _pipeline(monkeypatch, top_score):
    mod = types.ModuleType("retrieval.pipeline")
    mod.search = lambda q, **kw: _fake_results(top_score)
    monkeypatch.setitem(sys.modules, "retrieval.pipeline", mod)
    import api.pipeline as p
    import api.safety.danger_gate as dg
    monkeypatch.setattr(p, "run_danger_gate",
                        lambda t: dg.run_danger_gate(t, use_embedding=False))
    # elaboration has its own concerns; leaving it on would rewrite answers here
    monkeypatch.setattr(p, "ELABORATE_ANSWERS", False)
    return p


def _ask(p):
    return p.run_pipeline(AskRequest(query="benign question", language="sindhi"))


def test_top_tier_asserts_without_asking(monkeypatch):
    p = _pipeline(monkeypatch, 0.97)
    r = _ask(p)
    assert r.path == "verbatim"
    assert r.confidence_band == "high"
    assert r.did_you_mean is None


def test_middle_tier_asks_instead_of_asserting(monkeypatch):
    p = _pipeline(monkeypatch, 0.80)
    r = _ask(p)
    assert r.path == "confirm"
    assert r.did_you_mean == "matched question"
    # the answer ships too, so confirming costs no second round-trip
    assert r.answer == "the answer"


def test_rejecting_has_somewhere_to_go(monkeypatch):
    p = _pipeline(monkeypatch, 0.80)
    assert _ask(p).alternatives == ["second question", "third question"]


def test_below_the_ask_floor_falls_through_to_generation(monkeypatch):
    p = _pipeline(monkeypatch, 0.40)
    r = _ask(p)
    assert r.path == "generated"
    assert r.did_you_mean is None


def test_far_below_refuses(monkeypatch):
    p = _pipeline(monkeypatch, 0.05)
    r = _ask(p)
    assert r.path == "refusal"
    assert r.did_you_mean is None


def test_collapsing_the_tier_disables_confirmation(monkeypatch):
    # TAU_CONFIRM == TAU_HIGH leaves no gap, so nothing is ever asked.
    p = _pipeline(monkeypatch, 0.80)
    monkeypatch.setattr(p, "TAU_CONFIRM", p.TAU_HIGH)
    r = _ask(p)
    assert r.path != "confirm"


def test_danger_never_reaches_the_confirm_tier(monkeypatch):
    # A red flag must not be gated behind "did you mean?".
    p = _pipeline(monkeypatch, 0.80)
    r = p.run_pipeline(AskRequest(query="حمل ۾ گھڻو رت وهي رهيو آهي",
                                 language="sindhi"))
    assert r.path == "danger"
    assert r.escalated is True
    assert r.did_you_mean is None
