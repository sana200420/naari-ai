"""Tests for retrieval.pipeline.search() -- the docs/contracts/retrieval.json
entrypoint. Everything heavy (Qdrant client, HybridRetriever, rerank model,
translate model) is injected as a fake, so these never load a real model or
touch the network. Real end-to-end verification against live Qdrant + real
models happens in a notebook, same as the rest of this project."""

from retrieval.pipeline import search
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


def test_search_respects_top_k():
    rows = [_row(i, score=1.0 / i) for i in range(1, 10)]
    retriever = _FakeRetriever(sd_dense=rows)

    result = search(
        "query", top_k=3, retriever=retriever,
        rerank_fn=_fake_rerank({r["answer_id"]: r["score"] for r in rows}),
        translate_fn=_fake_translate, tau_high=0.9,
    )

    assert len(result["results"]) == 3
