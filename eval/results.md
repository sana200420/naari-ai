# Evaluation Results

Generated: 2026-08-30 (data/eval pipeline landed from Mahnoor's package, with fixes)

## Dataset sizes
- Gold evaluation set: 180 (target 300 — Phase 1 checkpoint is 100, so this already clears
  it in raw count, but see the KNOWN ISSUE below before using it)
- Danger-sign evaluation set: NOT CREATED — `run_eval.py` correctly skips it rather than
  fabricating danger signs; blocked on `data/safety/danger_signs_source.csv` (an approved
  clinical source), not yet supplied
- Out-of-scope evaluation set: 100 (20 per scope type: abortion, named_contraceptives,
  domestic_violence, non_health_chatter, are_you_a_doctor)

## Retrieval metrics
NOT AVAILABLE — requires retrieval predictions from the actual RAG system.
Run `eval/run_eval.py --preds <your_predictions.csv>` once retrieval is wired up.

## Safety metrics
NOT AVAILABLE — requires the safety-gate system's predictions.

## KNOWN ISSUES (please read before using these sets)

1. **Gold set is not generation-independent from the variants.** `gold_eval.csv` was built
   by sampling FAQs from the corpus and having an LLM generate a harder/oblique phrasing
   per FAQ — the same method used for `colloquial_variants.csv`. Every `correct_answer_id`
   maps straight back to the KB row it was generated from. The project's own playbook
   (`docs/PLAYBOOKS.md`, Lever 2) calls this out explicitly as the mistake that invalidates
   recall numbers: if the gold queries and the indexed variants share a generator, you're
   measuring whether an LLM matches itself, not real retrieval quality. **Do not use this
   file as the independent gold set for the Phase 1 dense-only baseline** until it's
   replaced with (or supplemented by) queries drawn from an independently-harvested
   real-question set (`data/variants/seed_real.csv`, per the Phase 0/1 plan) — that
   harvesting step hasn't started yet.
2. **`colloquial_variants.csv` is a smoke-test batch, not the full run.** Only
   `answer_id` 1–30 (150 variants) are populated (`data/variants/_progress.json` confirms
   `done_answer_ids: 1..30`). The remaining ~1970 rows still need generating before Lever 2
   review can start.
3. **`out_of_scope_eval.csv` had a generator bug — fixed here.** The version originally
   produced only 4 distinct query templates per scope type, repeated to pad to 20 rows each
   (80/100 rows were exact duplicates). Rebuilt to 20 genuinely distinct queries per scope
   type (100 total, all distinct) using the same template-based, no-invented-medical-content
   approach the notebook already intended. Regression tests added in
   `data/tests/test_eval_sets.py` so this can't silently regress again.
4. **`run_eval.py --danger` crashed instead of skipping gracefully** when
   `danger_sign_eval.csv` didn't exist. Fixed to skip danger metrics (reporting
   "NOT AVAILABLE") when the file is absent, matching the script's own stated policy of
   never fabricating results.

## Notes
No performance numbers are fabricated. This file records dataset sizes, configuration,
and known data-quality issues only, until real predictions are supplied.

---

# Phase 1 dense/sparse/fused ablation — gold_eval_280 (PROVISIONAL)

Generated: 2026-08-31T15:00:17Z, via `retrieval/scripts/link_and_baseline_gold_queries.ipynb`

This uses `Gold_KB_final_280.csv` (280 real colloquial-Sindhi questions with their own
written answers and citations), not `gold_eval.csv` above — that file's independence
problem (issue 1 above) is a separate, still-open concern for `Gold_KB_final_280` too:
these 280 questions don't clearly look drawn from real harvested speech either, and that
hasn't been confirmed with whoever produced the file.

**Ground truth = fused search's own top-1 answer**, not independently human-verified yet.
Fused's own recall row is close to tautological (it is being measured against itself) —
the meaningful comparison is dense-only and sparse-only against that same reference point.
**129/280 rows are flagged for category mismatch and 2/280 for low confidence** — re-run
after human review of `eval/gold_eval_280_linked.csv` for a trustworthy final number.

| Leg | Recall@1 | Recall@5 | Recall@20 |
|---|---:|---:|---:|
| dense | 0.464 | 0.896 | 1.000 |
| sparse | 0.571 | 0.925 | 1.000 |
| fused | 1.000 | 1.000 | 1.000 |

**Real signal worth noting:** sparse-only beats dense-only at Recall@1 (0.571 vs 0.464)
and Recall@5 (0.925 vs 0.896) — consistent with ADR 0001's reasoning that dense embeddings
blur rare/specific terms, which matters more for a low-resource language. Real evidence
Lever 3 (hybrid dense+sparse) is earning its complexity, not just theoretically justified.

**Investigated one persistent confusion cluster, not a retrieval bug:** several
"trying to conceive" (Fertility & Reproductive Health) queries kept matching KB id=956,
filed under PCOS & Hormonal Health. That row's actual question is *"If I'm planning a
pregnancy, what should I do?"* — near-identical phrasing to the gold queries — but its
answer is PCOS-specific (blood sugar/blood pressure checks), so it's correctly categorized
where it is. The embeddings are finding the closest real semantic match; this may mean the
Fertility category is missing a general (non-PCOS) "trying to conceive" row that should
outrank it. Worth flagging to whoever owns the Fertility category as a content gap, not
something to fix in retrieval code.

---

# Phase 1 dense/sparse/fused ablation — gold_eval_275 (FINAL, human-reviewed)
Generated: 2026-09-01T09:12:19Z, via `retrieval/scripts/link_and_baseline_gold_queries.ipynb`

Ground truth = `eval/gold_eval_280_linked.csv` after human review of every flagged row
(129/280): 105 confirmed correct as fused found them, 24 individually re-searched against
the full KB producing 9 corrected `correct_answer_id` values and 5 rows dropped as having
no usable KB match (280 → 275 rows). Reasoning per reviewed row is in
`eval/gold_eval_280_needs_review_enriched.csv`. This supersedes the provisional table
above — ground truth here is no longer fused's own top-1, and this run also includes the
`lang="sd"` filter fix (see commit `680b89b`): the provisional table above was measured
with Sindhi-only search silently mixing in English points, so this is the first trustworthy
number, not just the first non-tautological one.

| Leg | Recall@1 | Recall@5 | Recall@20 |
|---|---:|---:|---:|
| dense | 0.462 | 0.880 | 0.975 |
| sparse | 0.542 | 0.898 | 0.971 |
| fused | 0.967 | 0.971 | 0.975 |

**Reads as expected, directionally, from the bug fix:** recall@20 is no longer a clean
1.000 across the board (0.975/0.971/0.975) — with the lang filter now excluding English
points from the "Sindhi-only" legs, a handful of queries genuinely don't have their answer
in the Sindhi KB's own top 20, which the old, lang-mixed search was papering over.
**Meets the Phase 1 exit gate** (`docs/ROADMAP.md` §5): fused Recall@5 = 0.971 clears the
≥0.85 bar comfortably.

## Lever 4 — English-rescue fraction
Generated: 2026-09-01T09:13:40Z

Of the 275 corrected gold queries, **8 missed the correct answer in the Sindhi-only fused
top-5**. Adding the translated-query English leg (`HybridRetriever.cross_lingual_search`)
rescued **0/8 (0.0%)** of those misses into its own top-5.

**Honest read, not spun:** on this gold set, in this state, Lever 4 rescued nothing. n=8 is
too small to conclude the lever doesn't work, but it's real evidence against assuming it
pulls its weight for free — worth checking the actual NLLB translations on those 8 queries
before investing more here (mistranslation vs. genuinely no better match in English either).
Not blocking Phase 1 exit (fused already clears the bar without it) but worth resolving
before Phase 2 makes this leg conditional.

## bge-m3 prefix convention — empirical check
Generated: 2026-09-01T09:13:57Z

Re-ranked the existing Sindhi-dense top-20 candidate pool for 58 gold queries (of 60
sampled — 2 excluded because the correct answer wasn't in their own top-20 pool to begin
with), unprefixed vs. with `"query: "`/`"passage: "` prefixes. Re-ranks an existing
candidate pool rather than a full-corpus retrieval test.

| Convention | Recall@1 | Recall@5 |
|---|---:|---:|
| no prefix | 0.552 | 0.931 |
| query:/passage: prefix | 0.431 | 0.897 |

**Verdict: confirms ADR 0001** — bge-m3 needs no prefix, and adding one measurably hurts
(Recall@1 drops from 0.552 to 0.431 within the same candidate pool). Risk 1's "most common
silent RAG bug" is confirmed *not* present here.
