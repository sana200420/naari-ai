"""Tests for retrieval.pipeline.search() -- the docs/contracts/retrieval.json
entrypoint. Everything heavy (Qdrant client, HybridRetriever, rerank model,
translate model) is injected as a fake, so these never load a real model or
touch the network. Real end-to-end verification against live Qdrant + real
models happens in a notebook, same as the rest of this project."""

import retrieval.embed
import retrieval.rerank
import retrieval.translate
import retrieval.pipeline as pipeline_module
from retrieval.pipeline import search, warmup
from retrieval.tests.test_fake_retriever import REQUIRED_RESULT_KEYS


def _row(answer_id, score=0.5, question=None):
    return {
        "answer_id": answer_id,
        "category": "cat",
        "sub_category": "sub",
        "question": question or f"question {answer_id}",
        "answer": f"answer {answer_id}",
        "source": "src",
        "score": score,
    }


class _FakeRetriever:
    def __init__(self, sd_dense=None, sd_sparse=None, en_dense=None):
        self.sd_dense = sd_dense or []
        self.sd_sparse = sd_sparse or []
        self.en_dense = en_dense or []
        self.calls = []

    def dense_search(self, query, top_k=25, lang="sd"):
        self.calls.append(("dense", lang, query))
        return self.sd_dense if lang == "sd" else self.en_dense

    def sparse_search(self, query, top_k=25, lang="sd"):
        self.calls.append(("sparse", lang, query))
        return self.sd_sparse if lang == "sd" else []


def _fake_rerank(score_map=None):
    score_map = score_map or {}

    def rerank_fn(query, candidates, top_k=5):
        scored = []
        for c in candidates:
            row = dict(c)
            row["rerank_score"] = score_map.get(row["answer_id"], row.get("score", 0.0))
            scored.append(row)
        scored.sort(key=lambda r: -r["rerank_score"])
        return scored[:top_k]

    return rerank_fn


def _fake_translate(query):
    return f"EN:{query}"


def test_search_returns_contract_shape():
    retriever = _FakeRetriever(sd_dense=[_row(1, score=0.9)])
    result = search(
        "query", retriever=retriever, rerank_fn=_fake_rerank({1: 0.95}),
        translate_fn=_fake_translate, tau_high=0.5,
    )

    assert set(result.keys()) == {"query_normalised", "results", "latency_ms"}
    assert isinstance(result["latency_ms"], int)
    assert set(result["results"][0].keys()) == REQUIRED_RESULT_KEYS


def test_search_dedupes_by_answer_id():
    # id 1 appears in both dense and sparse -- must only appear once.
    retriever = _FakeRetriever(sd_dense=[_row(1, score=0.9)], sd_sparse=[_row(1, score=0.8), _row(2, score=0.5)])
    result = search(
        "query", retriever=retriever, rerank_fn=_fake_rerank({1: 0.95, 2: 0.3}),
        translate_fn=_fake_translate, tau_high=0.5,
    )

    ids = [r["answer_id"] for r in result["results"]]
    assert ids.count(1) == 1


def test_search_skips_english_leg_when_sindhi_confident():
    retriever = _FakeRetriever(sd_dense=[_row(1)], en_dense=[_row(99)])
    translate_calls = []

    def spy_translate(q):
        translate_calls.append(q)
        return f"EN:{q}"

    result = search(
        "query", retriever=retriever, rerank_fn=_fake_rerank({1: 0.9}),
        translate_fn=spy_translate, tau_high=0.75,
    )

    assert translate_calls == []
    assert not any(("dense", "en", "EN:query") == c for c in retriever.calls)
    ids = [r["answer_id"] for r in result["results"]]
    assert 99 not in ids


def test_search_runs_english_leg_when_sindhi_uncertain():
    retriever = _FakeRetriever(sd_dense=[_row(1)], en_dense=[_row(99)])

    result = search(
        "query", retriever=retriever, rerank_fn=_fake_rerank({1: 0.2, 99: 0.9}),
        translate_fn=_fake_translate, tau_high=0.75,
    )

    assert ("dense", "en", "EN:query") in retriever.calls
    ids = [r["answer_id"] for r in result["results"]]
    assert 99 in ids
    en_result = next(r for r in result["results"] if r["answer_id"] == 99)
    assert en_result["path"] == "english_dense"


def test_search_translate_fn_receives_the_raw_query():
    # documents current behaviour: translate_fn receives the raw query string
    retriever = _FakeRetriever(sd_dense=[_row(1)], en_dense=[])
    seen = []

    def spy_translate(q):
        seen.append(q)
        return "EN:x"

    search(
        "  سنڌي سوال  ", retriever=retriever, rerank_fn=_fake_rerank({1: 0.1}),
        translate_fn=spy_translate, tau_high=0.75,
    )

    assert seen == ["  سنڌي سوال  "]


def test_search_empty_candidates_returns_empty_results_not_an_error():
    retriever = _FakeRetriever()

    result = search(
        "query", retriever=retriever, rerank_fn=_fake_rerank(),
        translate_fn=_fake_translate, tau_high=0.75,
    )

    assert result["results"] == []


def test_search_path_prefers_dense_leg_when_row_found_in_both():
    retriever = _FakeRetriever(sd_dense=[_row(1)], sd_sparse=[_row(1)])

    result = search(
        "query", retriever=retriever, rerank_fn=_fake_rerank({1: 0.9}),
        translate_fn=_fake_translate, tau_high=0.5,
    )

    assert result["results"][0]["path"] == "sindhi_dense"


def test_search_response_includes_normalised_query():
    retriever = _FakeRetriever(sd_dense=[_row(1)])

    result = search(
        "ماهواري", retriever=retriever, rerank_fn=_fake_rerank({1: 0.9}),
        translate_fn=_fake_translate, tau_high=0.5,
    )

    assert result["query_normalised"]  # non-empty; exact normalisation covered in test_normalize.py


def test_warmup_loads_all_three_models_and_the_retriever(monkeypatch):
    calls = []

    monkeypatch.setattr(retrieval.embed, "embed_text", lambda text: calls.append(("embed", text)))
    monkeypatch.setattr(retrieval.translate, "translate_sd_to_en", lambda text: calls.append(("translate", text)))
    monkeypatch.setattr(retrieval.rerank, "rerank", lambda query, candidates, top_k=5: calls.append(("rerank", query)))
    monkeypatch.setattr(pipeline_module, "_get_retriever", lambda: calls.append(("retriever",)))

    warmup()

    kinds = [c[0] for c in calls]
    assert kinds == ["embed", "translate", "rerank", "retriever"]


def test_search_default_margin_always_prefers_fusions_top1_on_disagreement():
    # DEFAULT_RERANK_OVERRIDE_MARGIN is 2.0, calibrated from eval/gold_scored_full.csv
    # (fusion right 61/139 times reranking disagreed with it, reranking right only
    # 10/139) -- a real change here would be a silent regression back to trusting
    # a reranker that's net-harmful on disagreement for this KB.
    retriever = _FakeRetriever(sd_dense=[_row(1, score=0.9), _row(2, score=0.8)])

    result = search(
        "query", retriever=retriever,
        rerank_fn=_fake_rerank({1: 0.10, 2: 0.95}),  # even a decisive-looking gap
        translate_fn=_fake_translate, tau_high=0.0,
    )

    assert result["results"][0]["answer_id"] == 1  # fusion's #1 still wins by default


def test_search_rerank_override_margin_zero_opts_out_and_trusts_reranker():
    retriever = _FakeRetriever(sd_dense=[_row(1, score=0.9), _row(2, score=0.8)])

    result = search(
        "query", retriever=retriever,
        rerank_fn=_fake_rerank({1: 0.80, 2: 0.81}),  # fusion's #1 (id 1) barely loses
        translate_fn=_fake_translate, tau_high=0.0, rerank_override_margin=0.0,
    )

    assert result["results"][0]["answer_id"] == 2  # explicit opt-out restores old behaviour


def test_search_rerank_override_margin_restores_fusions_top1_on_a_close_call():
    retriever = _FakeRetriever(sd_dense=[_row(1, score=0.9), _row(2, score=0.8)])

    result = search(
        "query", retriever=retriever,
        rerank_fn=_fake_rerank({1: 0.80, 2: 0.81}),  # gap of 0.01
        translate_fn=_fake_translate, tau_high=0.0, rerank_override_margin=0.05,
    )

    assert result["results"][0]["answer_id"] == 1  # fusion's #1 wins the close call


def test_search_rerank_override_margin_does_not_override_a_decisive_gap():
    retriever = _FakeRetriever(sd_dense=[_row(1, score=0.9), _row(2, score=0.8)])

    result = search(
        "query", retriever=retriever,
        rerank_fn=_fake_rerank({1: 0.10, 2: 0.95}),  # gap of 0.85 -- not a close call
        translate_fn=_fake_translate, tau_high=0.0, rerank_override_margin=0.05,
    )

    assert result["results"][0]["answer_id"] == 2  # reranker's decisive pick stands


def test_search_respects_top_k():
    rows = [_row(i, score=1.0 / i) for i in range(1, 10)]
    retriever = _FakeRetriever(sd_dense=rows)

    result = search(
        "query", top_k=3, retriever=retriever,
        rerank_fn=_fake_rerank({r["answer_id"]: r["score"] for r in rows}),
        translate_fn=_fake_translate, tau_high=0.9,
    )

    assert len(result["results"]) == 3


def test_search_guard_survives_the_english_rescue_leg():
    # The English leg re-ranks a combined candidate set. It used to do so
    # WITHOUT the fusion-over-reranker guard, so every query below the cascade
    # threshold silently lost the fix that moved Recall@1 from 0.339 to 0.540 --
    # most of the gap between that and the 0.387 measured live on 248 queries.
    retriever = _FakeRetriever(
        sd_dense=[_row(1, score=0.9), _row(2, score=0.8)],
        en_dense=[_row(99, score=0.7)],
    )
    result = search(
        "query", retriever=retriever,
        # id 1 is fusion's top-1; the reranker prefers 2, and the low score
        # forces the English leg to run.
        rerank_fn=_fake_rerank({1: 0.10, 2: 0.20, 99: 0.15}),
        translate_fn=_fake_translate, tau_high=0.75,
    )

    assert result["results"][0]["answer_id"] == 1


def test_search_cascade_tau_is_independent_of_tau_high():
    # One number used to gate both "confident enough to assert" and "weak
    # enough to translate". Raising the first for safety silently made the
    # English leg fire on nearly every query.
    retriever = _FakeRetriever(sd_dense=[_row(1, score=0.9)], en_dense=[_row(99)])
    translated = []

    def spy(q):
        translated.append(q)
        return f"EN:{q}"

    search(
        "query", retriever=retriever, rerank_fn=_fake_rerank({1: 0.5}),
        translate_fn=spy,
        tau_high=0.99,      # band says "not confident"
        cascade_tau=0.10,   # cascade says "no rescue needed"
    )

    assert translated == []
