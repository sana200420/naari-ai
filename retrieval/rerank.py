"""Cross-encoder reranking over the fused top-20 (item 8, feeds Lever 5's
confidence gate).

BAAI/bge-reranker-v2-m3, loaded once (module-level singleton) and lazily --
mirrors retrieval/embed.py's and retrieval/translate.py's pattern. Tests in
retrieval/tests/test_rerank.py monkeypatch _get_model() so they never
actually load the model.

Per docs/ROADMAP.md's pipeline (stage 05), this reranks (query, Sindhi
question) pairs -- feed it fused_search()'s (lang="sd") output, not
cross_lingual_search()'s mixed-language one.
"""

import threading

from retrieval.normalize import normalize_sd

MODEL_NAME = "BAAI/bge-reranker-v2-m3"

_model = None
_model_lock = threading.Lock()


def _load_model():
    from FlagEmbedding import FlagReranker

    return FlagReranker(MODEL_NAME, use_fp16=True)


def _get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                _model = _load_model()
    return _model


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """Cross-encoder rerank of a fused candidate list.

    `candidates` is the shape HybridRetriever.fused_search()/dense_search()/
    sparse_search() return (each dict needs at least "answer_id" and
    "question"). Always normalises the query first, matching every other
    entry point into these models.

    Returns candidates sorted by rerank score best-first, each with a
    "rerank_score" key added and "path" set to "reranked", truncated to
    top_k. Empty input returns empty output without loading the model.
    """
    if not candidates:
        return []

    model = _get_model()
    normalized_query = normalize_sd(query)
    pairs = [[normalized_query, c["question"]] for c in candidates]
    scores = model.compute_score(pairs, normalize=True)
    if isinstance(scores, float):
        scores = [scores]

    reranked = []
    for candidate, score in zip(candidates, scores):
        row = dict(candidate)
        row["rerank_score"] = float(score)
        row["path"] = "reranked"
        reranked.append(row)

    reranked.sort(key=lambda r: -r["rerank_score"])
    return reranked[:top_k]
