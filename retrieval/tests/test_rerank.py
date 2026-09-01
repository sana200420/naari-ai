"""Tests for retrieval.rerank. Monkeypatches _get_model() so no real
bge-reranker-v2-m3 weights are ever loaded."""

import retrieval.rerank as rerank_module
from retrieval.rerank import rerank


class _FakeReranker:
    """Scores a (query, passage) pair by how many words they share --
    enough signal to test ordering without a real model."""

    def compute_score(self, pairs, normalize=None):
        scores = []
        for query, passage in pairs:
            q_words = set(query.split())
            p_words = set(passage.split())
            scores.append(len(q_words & p_words) / max(len(q_words), 1))
        return scores


def _candidate(answer_id, question, **extra):
    row = {"answer_id": answer_id, "question": question, "category": "cat",
           "sub_category": "sub", "answer": "ans", "source": "src", "review_tier": "B"}
    row.update(extra)
    return row


def test_rerank_reorders_by_score(monkeypatch):
    monkeypatch.setattr(rerank_module, "_get_model", lambda: _FakeReranker())
    candidates = [
        _candidate(1, "totally unrelated text"),
        _candidate(2, "period cycle length question"),
    ]

    results = rerank("period cycle length", candidates)

    assert [r["answer_id"] for r in results] == [2, 1]


def test_rerank_adds_score_and_marks_path(monkeypatch):
    monkeypatch.setattr(rerank_module, "_get_model", lambda: _FakeReranker())
    candidates = [_candidate(1, "period cycle length")]

    results = rerank("period cycle length", candidates)

    assert "rerank_score" in results[0]
    assert results[0]["path"] == "reranked"


def test_rerank_respects_top_k(monkeypatch):
    monkeypatch.setattr(rerank_module, "_get_model", lambda: _FakeReranker())
    candidates = [_candidate(i, f"word{i}") for i in range(10)]

    results = rerank("query", candidates, top_k=3)

    assert len(results) == 3


def test_rerank_empty_candidates_skips_the_model(monkeypatch):
    def _fail():
        raise AssertionError("should not load the model for an empty candidate list")

    monkeypatch.setattr(rerank_module, "_get_model", _fail)

    assert rerank("query", []) == []


def test_rerank_normalises_the_query_before_scoring(monkeypatch):
    seen_queries = []

    class _RecordingReranker:
        def compute_score(self, pairs, normalize=None):
            seen_queries.extend(q for q, _p in pairs)
            return [0.0 for _ in pairs]

    monkeypatch.setattr(rerank_module, "_get_model", lambda: _RecordingReranker())

    rerank("  extra   spaces  ", [_candidate(1, "question")])

    assert seen_queries == ["extra spaces"]


def test_rerank_preserves_original_candidate_fields(monkeypatch):
    monkeypatch.setattr(rerank_module, "_get_model", lambda: _FakeReranker())
    candidates = [_candidate(1, "period cycle", answer="the real answer text", source="who.int")]

    results = rerank("period cycle", candidates)

    assert results[0]["answer"] == "the real answer text"
    assert results[0]["source"] == "who.int"
