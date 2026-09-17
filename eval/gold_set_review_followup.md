# Gold-set review follow-up (2026-09-02)

Response to a review of the 248-row gold-set work: several of the "content gap" drops
and the single-answer-id grading scheme deserved a second look before any more tau
tuning. Two checks done, both local (no GPU/Qdrant needed):

## 1. Re-checked all 52 dropped rows against the full KB, unconstrained by the pipeline

Every row dropped across all three review passes (4 from the New-25 review, 23 from
the never-flagged-151 review, 25 from the bulk-confirmed-105 review) was re-searched
against the full 2000-row KB using token-overlap ranking — not anchored to the
pipeline's original top-3 candidates, to check whether a real answer existed that the
pipeline simply never surfaced for a human to notice.

**Result: no hidden matches found.** Top-5 candidates for every dropped row, including
`gold_276` (postmenopausal bleeding — the safety-relevant one), come back with only
partial keyword overlap and no row that actually answers the question. This confirms
the drops are genuine content gaps, not retrieval failures wearing a disguise —
though note this is a token-overlap proxy, not an unconstrained native-speaker
browse; that remains the more rigorous version of this check if time allows.

Full working data: scratchpad script `recheck_dropped_rows.py` (not committed —
re-run against `eval/new25_review_final.csv`, `eval/never_flagged_151_review.csv`,
and `eval/bulk_confirmed_105_review.csv`'s DROP rows if this needs re-verifying).

## 2. Built `acceptable_answer_ids` — grading against a single correct id was too strict

Ran a same-category, Jaccard-similarity pass over full answer text across all 2000 KB
rows: 39 pairs at Jaccard >= 0.6, 11 at >= 0.7. Manually read all 11 full-text pairs at
>= 0.7 (the full text, not the truncated preview) — **8 are genuine near-duplicate
answers** (same practical content, asked two ways); **3 are false positives** from
shared vocabulary despite different actual content:
- id 1765/1925 — hormonal birth control vs. weight change, both affecting discharge (different causes)
- id 1048/1087 — iron food sources vs. protein food sources (different nutrients, shared words like "meat/chicken/fish")
- id 1841/1959 — BV vs. UTI, both raising preterm-birth risk (different conditions)

This 27% false-positive rate on an already-high similarity threshold is the same
surface-overlap trap the reranker itself seems to fall into (see the Item 8 audit and
today's tau_high finding) — reinforces that surface/lexical similarity is not a
reliable proxy for "same answer" without a manual read.

The 8 verified genuine pairs are recorded in `eval/kb_near_duplicate_answer_groups.csv`
and used to seed an `acceptable_answer_ids` column on `eval/gold_eval_280_linked.csv`
(currently affects 3 of the 248 gold rows directly). This is necessarily incomplete —
a full KB dedup pass (embedding-based, not just text-Jaccard) is future work for
whoever owns KB content — but it's no longer *zero* multi-answer support, and the
tau-tuning notebook now grades against this set instead of a single id.

## Not yet done (needs a live GPU/Qdrant run — added to the notebook instead)

`retrieval/scripts/verify_pipeline_and_tune_thresholds.ipynb` was extended with the
diagnostics that need the live pipeline: Recall@20 vs Recall@1 (ranking vs. retrieval
problem), hub-row shortlist-frequency counting, a structured audit export for every
incorrect-but-score>=0.9 query, margin/agreement/category-consistency as alternative
confidence signals (fit on a 70/30 train/test split), and an NLLB translation printout
for the real Sindhi-only-miss set. See the notebook's "Diagnostics" section. Also fixed
in the same pass: Item 2's forced-off/conditional comparison now includes the correct
always-on (`tau_high=1.1`) baseline, and the notebook runs unmodified on both Colab and
Kaggle.
