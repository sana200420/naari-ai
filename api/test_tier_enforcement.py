"""Stage 02b: review-tier enforcement (PR #22, api/phase3_tier.py).

PR #22 wired this in by reading `chunks[0].get("tier", "B")`, but the chunks
dict built in run_pipeline() never had a "tier" key and retrieval's contract
(docs/contracts/retrieval.json) never returned review_tier in the first place.
So the lookup always fell back to "B" and the Tier C block could never fire --
inert by construction, not by data. Fixed by threading review_tier through
retrieval/pipeline.py's _to_result() and api/pipeline.py's chunk construction.

Nothing exercised this path before; these are the first tests for it.
"""
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


def test_tier_c_row_is_never_served(monkeypatch):
    from api.phase3_tier import TIER_C_REFUSAL

    p = _pipeline(monkeypatch, review_tier="C")
    r = _ask(p)

    assert r.path == "tier_c_block"
    assert r.answer == TIER_C_REFUSAL
    assert r.retrieved_ids == []


def test_tier_b_row_is_served_normally(monkeypatch):
    """Every row in the KB is Tier B today (knowledge_base/*.csv,
    review_tier column), so this is the path that must not regress."""
    p = _pipeline(monkeypatch, review_tier="B")
    r = _ask(p)

    assert r.path != "tier_c_block"
    assert r.path == "verbatim"


def test_tier_a_row_is_served_normally(monkeypatch):
    p = _pipeline(monkeypatch, review_tier="A")
    r = _ask(p)

    assert r.path != "tier_c_block"


def test_missing_review_tier_defaults_to_b_not_a_block():
    """A row with no review_tier field (a future KB source that forgets the
    column, or a variant/English row shaped slightly differently) must default
    to being servable, not silently blocked."""
    from api.phase3_tier import enforce_tier

    _, disclaimer, blocked = enforce_tier(None, "answer text", False)
    assert blocked is False


def test_tier_c_block_counts_as_a_refusal_in_the_scorecard(monkeypatch):
    """
    scripts/definition_of_done.py's REFUSAL_PATHS decides what counts as "not
    answered" for the refusal-correctness target. A Tier C block refuses to
    serve an answer exactly like "refusal"/"referral"/"danger" do, so it
    belongs in that set -- without it, the day any KB row is actually tiered
    C, a correct block would be scored as an answer and silently lower
    measured refusal correctness.
    """
    from scripts.definition_of_done import REFUSAL_PATHS

    p = _pipeline(monkeypatch, review_tier="C")
    r = _ask(p)

    assert r.path == "tier_c_block"
    assert r.path in REFUSAL_PATHS
