"""The packaged retrieval entrypoint — see docs/contracts/retrieval.json for
the exact request/response shape Sabiha's /api imports and depends on.

    from retrieval.pipeline import search
    result = search("حيض جي چڪر ڇا آهي؟")

Composes: normalise -> Sindhi dense + sparse (fused) -> rerank -> [if
uncertain] translated English dense leg, combined candidates reranked again
-> top_k. Every model (bge-m3, bge-reranker-v2-m3, NLLB) is a lazy
module-level singleton (retrieval/embed.py, retrieval/rerank.py,
retrieval/translate.py) — the first call pays the load cost, every call
after is warm. This module adds one more singleton on top: the Qdrant
client + HybridRetriever pair.

Lever 4's cascade (docs/PLAYBOOKS.md): "if the Sindhi reranked top score
already clears tau_high, skip translation entirely" — note *reranked*, not
the raw fused score, so the gate is Sindhi-only candidates run through
rerank() first, and only on an uncertain result does the English leg run
and get merged in for a second, combined rerank pass. This means the
uncertain path pays for two rerank calls, not one — accepted cost, since
Lever 4 exists specifically to be a rare, targeted rescue, not an
always-on tax.

tau_high defaults from the TAU_HIGH env var (see .env.example) with a
0.75 fallback — a placeholder until Phase 2's threshold-tuning item
(docs/PLAYBOOKS.md, needs Mahnoor's negative set) produces a calibrated
value from real score distributions.
"""

import os
import threading
import time

from retrieval.normalize import normalize_sd
from retrieval.rerank import rerank as rerank_fn
from retrieval.search import COLLECTION, HybridRetriever, reciprocal_rank_fusion
from retrieval.translate import translate_sd_to_en

DEFAULT_TAU_HIGH = 0.75

_client = None
_retriever = None
_retriever_lock = threading.Lock()


def _get_retriever() -> HybridRetriever:
    global _client, _retriever
    if _retriever is None:
        with _retriever_lock:
            if _retriever is None:
                from qdrant_client import QdrantClient

                from retrieval.embed import embed_text

                _client = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])
                _retriever = HybridRetriever(_client, collection=COLLECTION, embed_fn=embed_text)
    return _retriever


def _to_result(row: dict, path: str) -> dict:
    return {
        "answer_id": row["answer_id"],
        "category": row["category"],
        "sub_category": row["sub_category"],
        "question": row["question"],
        "answer": row["answer"],
        "source": row["source"],
        "score": row["rerank_score"],
        "path": path,
    }


def search(
    query: str,
    top_k: int = 5,
    candidate_k: int = 20,
    tau_high: float | None = None,
    retriever: HybridRetriever | None = None,
    translate_fn=translate_sd_to_en,
    rerank_fn=rerank_fn,
) -> dict:
    """The retrieval.json contract entrypoint. `retriever`/`translate_fn`/
    `rerank_fn` are injectable so this is testable against fakes without
    loading any real model or hitting Qdrant."""
    start = time.perf_counter()
    if tau_high is None:
        tau_high = float(os.environ.get("TAU_HIGH", DEFAULT_TAU_HIGH))
    active_retriever = retriever if retriever is not None else _get_retriever()

    sd_dense = active_retriever.dense_search(query, top_k=candidate_k, lang="sd")
    sd_sparse = active_retriever.sparse_search(query, top_k=candidate_k, lang="sd")

    row_by_id: dict = {}
    path_by_id: dict = {}
    for path_name, rows in (("sindhi_dense", sd_dense), ("sindhi_sparse", sd_sparse)):
        for row in rows:
            row_by_id.setdefault(row["answer_id"], row)
            path_by_id.setdefault(row["answer_id"], path_name)

    sd_fused = reciprocal_rank_fusion([
        [row["answer_id"] for row in sd_dense],
        [row["answer_id"] for row in sd_sparse],
    ])
    sd_candidates = [row_by_id[answer_id] for answer_id, _score in sd_fused[:candidate_k]]

    reranked = rerank_fn(query, sd_candidates, top_k=top_k) if sd_candidates else []
    top_score = reranked[0]["rerank_score"] if reranked else 0.0

    if top_score < tau_high:
        en_query = translate_fn(query)
        en_dense = active_retriever.dense_search(en_query, top_k=candidate_k, lang="en")
        for row in en_dense:
            row_by_id.setdefault(row["answer_id"], row)
            path_by_id.setdefault(row["answer_id"], "english_dense")

        combined = {row["answer_id"]: row for row in sd_candidates}
        for row in en_dense:
            combined.setdefault(row["answer_id"], row)
        reranked = rerank_fn(query, list(combined.values()), top_k=top_k) if combined else []

    results = [_to_result(row, path_by_id[row["answer_id"]]) for row in reranked]

    latency_ms = int((time.perf_counter() - start) * 1000)
    return {
        "query_normalised": normalize_sd(query),
        "results": results,
        "latency_ms": latency_ms,
    }
