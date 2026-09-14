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

Reranker override guard (2026-09-07, docs/status.md): auditing 58
incorrect-but-high-confidence answers against the fully-reviewed 248-row
gold set found 25 cases where reciprocal-rank-fusion's own top-1 pick was
already correct, and reranking demoted it in favour of a wrong answer —
roughly 10% of all queries. `_prefer_fusion_top1_if_close` is the guard
against that pattern: rerank scores every fused candidate (not just the
top `top_k`) so fusion's #1 pick's rerank score is always available, and
if the reranker's chosen top-1 differs from fusion's #1 by less than
`RERANK_OVERRIDE_MARGIN`, fusion's #1 wins the tie instead of being
silently overridden.

`RERANK_OVERRIDE_MARGIN` was calibrated, not guessed: `eval/gold_scored_full.csv`
captures the pre-guard reranker state for all 248 gold queries, which let
every candidate margin be simulated offline with no extra GPU run. Of the
139 queries where fusion and reranking actually disagreed on the top-1
pick, fusion was right and reranking wrongly overrode it **61 times**;
reranking was right to override fusion only **10 times** — a 6:1 ratio
against trusting the reranker's disagreement, confirmed by randomly
splitting those 139 disagreements in half and checking the ratio holds
independently in each half (30:5 and 31:5). There's no crossover point
where trusting reranking starts winning, so the margin is set to `2.0`
— outside the range a rerank-score gap can ever reach — meaning fusion's
#1 pick always wins when the two disagree. This is a real property of
this reranker on this KB, not a threshold fit to noise; see
`eval/results.md`'s 2026-09-07 section for the full sweep table.
"""

import os
import threading
import time

from retrieval.normalize import normalize_sd
from retrieval.rerank import rerank as rerank_fn
from retrieval.search import COLLECTION, HybridRetriever, reciprocal_rank_fusion
from retrieval.translate import translate_sd_to_en

DEFAULT_TAU_HIGH = 0.75
# The cascade gate is now its own knob. It used to share TAU_HIGH with the
# API's confidence band, which meant one number decided two unrelated things:
# "is this answer confident enough to assert" and "is this answer weak enough
# to be worth translating". Raising the band threshold for safety silently
# made the English leg fire on nearly every query. Defaults to the old shared
# value so nothing changes until someone deliberately tunes it.
DEFAULT_CASCADE_TAU = 0.75
DEFAULT_RERANK_OVERRIDE_MARGIN = 2.0

# Variant legs are OFF by default. Turning them on changes what every query
# retrieves, and the branch's whole claim is that retrieval numbers are
# measured rather than asserted -- so the flag ships off, gets measured on the
# gold set, and is flipped in the environment only if the measurement earns it.
DEFAULT_USE_VARIANTS = False

# How many variant-only candidates get a RESCUE slot beyond the canonical
# top-candidate_k. Originally this was a weighted-RRF blend where variant legs
# competed with canonical legs for the same fixed candidate_k slots -- and a
# Colab measurement (eval/variant_index_lift.csv, w=0.5) showed that design
# regresses Recall@1 by 0.125 while barely moving Recall@20 (+0.008): variant
# noise was crowding correct canonical rows OUT of the candidate window before
# reranking ever got to see them. Lever 4's English cascade leg already solved
# this exact problem below (`combined.setdefault`, canonical rows never
# evicted) -- this reuses that pattern instead of re-deriving a worse one.
DEFAULT_VARIANT_RESCUE_K = 10


def _prefer_fusion_top1_if_close(
    reranked: list[dict], fusion_top1_id, margin: float
) -> list[dict]:
    """If reranking disagrees with fusion's own top-1 pick by less than
    `margin`, put fusion's #1 back on top instead of trusting the reranker.
    `reranked` must already be sorted best-first and must include every
    fused candidate (not just the caller's requested top_k) so fusion's #1
    is guaranteed to have a rerank_score to compare. `margin=0.0` disables
    this entirely (two floats are essentially never exactly equal, so
    nothing ever qualifies); `DEFAULT_RERANK_OVERRIDE_MARGIN` (module
    docstring) is calibrated to always override instead, since the data
    shows reranking is net-harmful whenever it disagrees with fusion here.
    """
    if not reranked or reranked[0]["answer_id"] == fusion_top1_id:
        return reranked

    fusion_top1_row = next((r for r in reranked if r["answer_id"] == fusion_top1_id), None)
    if fusion_top1_row is None:
        return reranked

    gap = reranked[0]["rerank_score"] - fusion_top1_row["rerank_score"]
    if gap >= margin:
        return reranked

    without_fusion_top1 = [r for r in reranked if r["answer_id"] != fusion_top1_id]
    return [fusion_top1_row, *without_fusion_top1]

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


def warmup() -> None:
    """Force every model to load now, instead of lazily on first use.

    Without this, `translate_sd_to_en`'s NLLB model only loads the first
    time some real query's Sindhi score actually lands below tau_high --
    which might be request 1, or request 50. In production that means
    whichever user happens to send the first uncertain query eats a
    ~60s cold-load penalty that should have happened once at container
    startup instead. Call this once when the service boots, before
    serving any requests.
    """
    from retrieval.embed import embed_text
    from retrieval.rerank import rerank as _rerank_warmup
    from retrieval.translate import translate_sd_to_en as _translate_warmup

    embed_text("warmup")
    _translate_warmup("warmup")
    _rerank_warmup("warmup", [{
        "answer_id": 0, "category": "", "sub_category": "",
        "question": "warmup", "answer": "", "source": "",
    }])
    _get_retriever()


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
        # api/pipeline.py's Stage 02b tier enforcement (PR #22) reads this to
        # decide whether a row is allowed to be served. It was added there
        # assuming this contract already carried it -- it did not, so the
        # check was reading a key that was never present and always fell back
        # to Tier B, meaning Tier C could never actually block anything.
        "review_tier": row.get("review_tier", "B"),
    }


def search(
    query: str,
    top_k: int = 5,
    candidate_k: int = 20,
    tau_high: float | None = None,
    cascade_tau: float | None = None,
    rerank_override_margin: float | None = None,
    retriever: HybridRetriever | None = None,
    translate_fn=translate_sd_to_en,
    rerank_fn=rerank_fn,
    use_variants: bool | None = None,
    variant_rescue_k: int | None = None,
) -> dict:
    """The retrieval.json contract entrypoint. `retriever`/`translate_fn`/
    `rerank_fn` are injectable so this is testable against fakes without
    loading any real model or hitting Qdrant."""
    start = time.perf_counter()
    if tau_high is None:
        tau_high = float(os.environ.get("TAU_HIGH", DEFAULT_TAU_HIGH))
    if cascade_tau is None:
        # Falls back to tau_high so existing callers and tests keep their
        # behaviour; CASCADE_TAU overrides it independently.
        cascade_tau = float(os.environ.get("CASCADE_TAU", tau_high))
    if rerank_override_margin is None:
        rerank_override_margin = float(
            os.environ.get("RERANK_OVERRIDE_MARGIN", DEFAULT_RERANK_OVERRIDE_MARGIN)
        )
    if use_variants is None:
        use_variants = os.environ.get(
            "USE_VARIANT_INDEX", str(DEFAULT_USE_VARIANTS)
        ).strip().lower() in ("1", "true", "yes")
    if variant_rescue_k is None:
        variant_rescue_k = int(os.environ.get("VARIANT_RESCUE_K", DEFAULT_VARIANT_RESCUE_K))
    active_retriever = retriever if retriever is not None else _get_retriever()

    sd_dense = active_retriever.dense_search(query, top_k=candidate_k, lang="sd")
    sd_sparse = active_retriever.sparse_search(query, top_k=candidate_k, lang="sd")

    # Colloquial rewordings of the same questions. The gold queries are not
    # phrased the way the KB's FAQ-style questions are, which is what keeps
    # Recall@1 (0.528) so far below Recall@20 (0.762): the right row is
    # usually reachable and merely not first. A variant gives that row a
    # surface that matches how the question actually gets asked.
    var_dense, var_sparse = ([], [])
    if use_variants:
        var_dense, var_sparse = active_retriever.variant_search(query, top_k=candidate_k)

    row_by_id: dict = {}
    path_by_id: dict = {}
    for path_name, rows in (("sindhi_dense", sd_dense), ("sindhi_sparse", sd_sparse)):
        for row in rows:
            row_by_id.setdefault(row["answer_id"], row)
            path_by_id.setdefault(row["answer_id"], path_name)

    # Canonical-only fusion, exactly as it was before variants existed. This
    # MUST stay untouched by variant legs: a first attempt fused all four
    # ranked lists together and sliced to candidate_k, which let variant-only
    # discovered rows outrank and displace correct canonical rows before
    # reranking ever saw them -- Recall@1 dropped 0.125 for a Recall@20 gain
    # of 0.008 (eval/variant_index_lift.csv). Variants are a rescue leg, not
    # a voter: they may only ADD candidates, never bump one out.
    sd_fused = reciprocal_rank_fusion([
        [row["answer_id"] for row in sd_dense],
        [row["answer_id"] for row in sd_sparse],
    ])
    sd_candidates = [row_by_id[answer_id] for answer_id, _score in sd_fused[:candidate_k]]

    # Same rescue pattern as the English cascade leg below (combined =
    # sd_candidates first, setdefault only): variant hits get appended after
    # every canonical candidate is already locked in, so the worst a bad
    # variant match can do is occupy an extra reranker slot, never displace a
    # row the canonical legs already found.
    candidates_for_rerank = sd_candidates
    if use_variants:
        var_dense, var_sparse = active_retriever.variant_search(query, top_k=candidate_k)
        for path_name, rows in (("variant_dense", var_dense), ("variant_sparse", var_sparse)):
            for row in rows:
                row_by_id.setdefault(row["answer_id"], row)
                path_by_id.setdefault(row["answer_id"], path_name)
        var_fused = reciprocal_rank_fusion([
            [row["answer_id"] for row in var_dense],
            [row["answer_id"] for row in var_sparse],
        ])
        canonical_ids = {c["answer_id"] for c in sd_candidates}
        rescued = [row_by_id[answer_id] for answer_id, _score in var_fused
                  if answer_id not in canonical_ids][:variant_rescue_k]
        candidates_for_rerank = sd_candidates + rescued

    # Rerank every candidate, not just top_k, so fusion's #1 pick always has a
    # rerank_score available for the override-guard comparison below -- then
    # truncate to top_k only after that guard has had a chance to run. The
    # guard still anchors to sd_candidates[0] -- the CANONICAL fusion's #1 --
    # never a rescued variant row, so a variant can never win the tie-break
    # that guard exists to protect.
    reranked_full = (rerank_fn(query, candidates_for_rerank, top_k=len(candidates_for_rerank))
                     if candidates_for_rerank else [])
    if reranked_full and sd_candidates:
        reranked_full = _prefer_fusion_top1_if_close(
            reranked_full, sd_candidates[0]["answer_id"], rerank_override_margin
        )
    reranked = reranked_full[:top_k]
    top_score = reranked[0]["rerank_score"] if reranked else 0.0

    if top_score < cascade_tau:
        en_query = translate_fn(query)
        en_dense = active_retriever.dense_search(en_query, top_k=candidate_k, lang="en")
        for row in en_dense:
            row_by_id.setdefault(row["answer_id"], row)
            path_by_id.setdefault(row["answer_id"], "english_dense")

        combined = {row["answer_id"]: row for row in sd_candidates}
        for row in en_dense:
            combined.setdefault(row["answer_id"], row)
        # The guard has to be re-applied here. Without it, every query that
        # takes the rescue path silently loses the fusion-over-reranker
        # preference that moved Recall@1 from 0.339 to 0.540 -- which is most
        # of the gap between that number and the 0.387 measured live.
        if combined:
            combined_full = rerank_fn(query, list(combined.values()),
                                      top_k=len(combined))
            combined_full = _prefer_fusion_top1_if_close(
                combined_full, sd_candidates[0]["answer_id"], rerank_override_margin
            ) if sd_candidates else combined_full
            reranked = combined_full[:top_k]
        else:
            reranked = []

    results = [_to_result(row, path_by_id[row["answer_id"]]) for row in reranked]

    latency_ms = int((time.perf_counter() - start) * 1000)
    return {
        "query_normalised": normalize_sd(query),
        "results": results,
        "latency_ms": latency_ms,
    }
