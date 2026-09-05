# Project status

**Current phase:** Phase 2 — Make it a service. Phase 1 checklist fully closed 2026-09-01 (GO, fused Recall@5 = 0.971). Phase 2 started same day: `retrieval/pipeline.py`'s `search()` built. Item 1 (warm loading) and Item 2 (conditional English leg) are both done. **Item 3 (τ tuning) is the live open problem**, and as of 2026-09-05 it's a *characterized* problem, not a mystery: Recall@1 (0.339) vs. Recall@20 pre-rerank (0.726) on the fully-reviewed 248-row gold set is a 39-point gap, meaning the correct answer is usually in the shortlist but the reranker is picking the wrong one — 25/58 audited high-confidence wrong answers had the correct answer sitting at rank 1 of the pre-rerank shortlist before reranking demoted it. See `eval/results.md`'s 2026-09-05 section and the Lever 5 line below.

## Who's on what

| Person | Currently | Blocked on |
|---|---|---|
| Sana | Levers 1, 3, 4 done and measured; reranking (item 8) built and measured; Sindhi+English fully embedded (4000/4000 points, verified live); gold eval set at 248 rows, every row individually reviewed, now also carrying `acceptable_answer_ids` for verified near-duplicate KB rows; Phase 1 go/no-go is a GO; Phase 2 Items 1 and 2 done, Item 3 (τ tuning) diagnosed but not resolved — the reranker demotes an already-correct fused top-1 in ~10% of all queries | Capture Diagnostic 4's margin/fusion-agreement precision-coverage numbers (printed, not yet saved) and decide the fix: reranker retuning, a fusion-agreement gate, or skip-reranking-when-fusion-is-confident |
| Sabiha | FastAPI skeleton + first deploy | — |
| Tooba | Next.js skeleton, Sindhi font audit | — |
| Mahnoor | Corpus merge landed; variant + eval pipeline landed but partial (see below) | Reviewer outreach and real-question harvesting not started yet |

## Lever 1 — Script normalisation: done

- `knowledge_base/Womens_Health_KB - 2000_final.csv` cleaned: 2,000 rows, 6 columns, `id` 1–2000, 250/category, zero duplicate questions, zero blank fields
- `docs/adr/0002-normalisation-map.md`: 145-codepoint histogram, keep/map/drop decision for every one
- `retrieval/normalize.py`: `normalize_sd()`, the fixed 7-step pipeline
- `retrieval/embed.py`: `embed_text()` — real `BGEM3FlagModel` implementation, normalises unconditionally before anything else, the only public embedding entry point
- `retrieval/tests/`: 74 tests passing — idempotence over all 4,000 question+answer strings, 47 golden fixtures, non-destruction (0 collisions), embed-gating check
- CI (`.github/workflows/ci.yml`) now runs `pytest retrieval/ data/tests/` and `eval/run_eval.py` on every PR, fixed to work with bare `pytest` (not just `python -m pytest`)

## Lever 3 — Hybrid dense + sparse + RRF: done

- `retrieval/search.py`: `HybridRetriever` (dense/sparse/fused search against Qdrant) + `reciprocal_rank_fusion`, tested against fakes and verified against the live collection
- Sindhi KB (2000 rows) + English KB (1999/2000 rows) embedded into Qdrant Cloud collection `naari_ai_kb`: named `dense` (1024-d cosine) + `sparse` vectors, `lang` payload field (`sd`/`en`) with a payload index, shared `answer_id` join key across languages
- **Final ablation table (`eval/results.md`, 2026-09-01), 275-query human-reviewed gold set, `lang="sd"` bug fixed:**

  | Leg | Recall@1 | Recall@5 | Recall@20 |
  |---|---:|---:|---:|
  | dense | 0.462 | 0.880 | 0.975 |
  | sparse | 0.542 | 0.898 | 0.971 |
  | fused | 0.967 | 0.971 | 0.975 |

  Fused clears the Phase 1 exit gate (≥0.85) comfortably. Getting here took two real bugs found and fixed along the way: (1) `dense_search`/`sparse_search` had no `lang` filter, so a "Sindhi-only" search was silently mixing in English points once the English KB shared the collection — fixed by defaulting to `lang="sd"`; (2) the first two re-run attempts of the Colab notebook silently kept using stale pre-fix code (`git pull` run from the wrong directory, then Python's module cache not reloaded, then a reconnected Colab tab reusing an already-stale VM) — fixed by making the notebook re-clone unconditionally and reload modules explicitly rather than trusting `git pull`.
- `retrieval/translate.py` + `HybridRetriever.cross_lingual_search()` (Lever 4 cascade): built and measured. Of 8 Sindhi-only misses in the corrected gold set, English rescued **0 (0%)** — small sample, but a real number, not yet a flattering one. Worth checking the actual NLLB translations on those 8 before Phase 2 makes this leg conditional.
- **Prefix convention empirically confirmed:** no-prefix Recall@1 0.552 vs. prefixed 0.431 on the same candidate pool — confirms ADR 0001, bge-m3 needs none.
- **Reranking (item 8):** `retrieval/rerank.py` (`bge-reranker-v2-m3`) built and measured. Raw Recall@1 dropped to 0.385, which looked alarming — but a 40-row manual audit of the disagreements (`eval/rerank_regression_audit.csv`) found the reranker was right about as often (12/40) as genuinely wrong (11/40), with another 12/40 cases where fused's own top-1 was *also* wrong (i.e. the never-individually-reviewed gold rows, not reranking, are the actual weak point) and 5/40 near-duplicate-content ties. One real, occasional weakness confirmed: cross-category confusion from surface phrase overlap. Latency is well inside budget (p95 112ms/20 candidates). The gold-set review needed to fairly re-score this is now complete (see below) — worth re-running this audit against the cleaned set.

## Gold eval set — 248 rows, every row now individually reviewed

- `eval/gold_eval_280_linked.csv`: original 280 gold questions linked via fused search. History: 129 category-mismatch/low-confidence rows triaged against `docs/PLAYBOOKS.md`'s category-boundary rules down to 24 genuine unknowns, each manually re-searched against the full KB (`eval/gold_eval_280_needs_review_enriched.csv`): 9 corrections, 5 drops, 10 confirmed-OK (280 → 275). 105 more were "confirmed-OK-in-bulk" via category-boundary reasoning only, not individually verified at the time.
- 2026-09-02: Mahnoor's 25 new independently-written questions (`eval/New_25_Gold_Questions.csv`) reviewed individually — 11 OK, 10 corrected, 4 dropped as genuine KB content gaps (postpartum swelling, first-labor duration, period symptoms at work, PMS breast tenderness — worth a content-team follow-up). Full reasoning: `eval/new25_review_final.csv`. (275 → 296)
- 2026-09-02: the 151 rows that were *never flagged at all* (fused's top-1 happened to match category on the first pass, zero scrutiny) reviewed individually — 39 corrected, 23 dropped. Full reasoning: `eval/never_flagged_151_review.csv`. (296 → 273). One drop flagged as more than a gold-set issue: `gold_276` (postmenopausal bleeding, a real red-flag symptom) has no matching KB row at all — worth prioritizing for the KB content team. Recurring pattern found: a handful of high-frequency generic KB rows (e.g. "what to eat during pregnancy", "PCOS problems during pregnancy") were repeatedly winning fused-search ties for questions asking something else entirely.
- 2026-09-02: the last 105 "bulk-confirmed" legacy rows (only ever category-boundary-checked, never individually verified) reviewed individually — 54 corrected, 25 dropped. Full reasoning: `eval/bulk_confirmed_105_review.csv`. (273 → 248). **The gold set is now fully, individually reviewed end to end** — no more rows accepted on category-match alone. Same recurring-generic-row pattern confirmed again (id=610 "what to eat during pregnancy", id=821 "heavy periods causing weakness" both kept winning ties for unrelated queries). Two new content-gap categories surfaced, both worth flagging to the KB content team: (1) **period-pain home-relief methods** — the KB only has reassurance-style rows ("pain is treatable"), no actual relief-method content (heat, ibuprofen, warm bath) — affects 4 rows; (2) **general unexplained fatigue** — several queries ask "I'm tired despite enough sleep/healthy eating/resting, why?" and the KB only answers this in pregnancy/postpartum/PCOS-specific framing, no general-population fatigue-causes row exists — affects 3 rows. Also newly dropped: general (non-pregnancy) rows for bloating, acidity/heartburn, and constipation-diet — the KB's only coverage of these is pregnancy-specific.
- `New_300_Womens_Health_Gold_Set_KB.csv` (a separate attempt) was rejected — every one of its 300 questions was a byte-identical copy of an existing KB question, unusable as an independent gold set
- 2026-09-05: a review of the completed gold-set work flagged two real gaps, both addressed. (1) All 52 dropped rows re-searched against the full KB unconstrained by the pipeline's own candidates — every drop holds up as a genuine content gap, including `gold_276` (postmenopausal bleeding). Method/result: `eval/gold_set_review_followup.md`. (2) Grading against a single `correct_answer_id` was too strict — found 8 genuine near-duplicate KB answer pairs (of 11 candidates at Jaccard≥0.7 on full answer text; 3 were false positives from shared vocabulary alone) and added an `acceptable_answer_ids` column seeded from them (`eval/kb_near_duplicate_answer_groups.csv`). The tau-tuning notebook now grades against this set.

## Phase 2, Item 3 (τ tuning) — diagnosed 2026-09-05, not yet resolved

Re-ran `verify_pipeline_and_tune_thresholds.ipynb` against the fully-reviewed 248-row set with real diagnostics instead of more guessing (full writeup: `eval/results.md`'s 2026-09-05 section):

- **Recall@1 (final pipeline) = 0.339, Recall@20 (fused shortlist, pre-rerank) = 0.726.** A 39-point gap — the correct answer is usually *in* the shortlist. This is a ranking/reranking problem, not a retrieval/embedding problem. 68/248 (27%) never reach the shortlist at all — a separate, smaller retrieval-pool gap.
- Of 58 incorrect-but-score≥0.9 queries audited: **25 had the correct answer at rank 1 of the pre-rerank fused shortlist** — the reranker actively demoted an already-correct answer for ~10% of all queries. `gold_7` (flagged in the original Item 8 audit) is one of these — confirms the failure mode recurs at scale, not a one-off.
- Corrected finding: the notebook's category-mismatch check initially compared English (`stated_category`) against Sindhi (KB `category`) as raw strings, which can never match — reported a false 58/58 (100%) mismatch. Fixed with an explicit category map; the true split is 27/58 (47%) genuine cross-category confusion, 31/58 (53%) same-category-but-wrong-row.
- Item 2 (conditional English leg) resolved cleanly in the same run: conditional vs. always-on (`tau_high=1.1`) shows identical Recall@1 (0.339) at 543ms less median latency. Checklist item done.
- English-leg closure: of 20 sampled Sindhi-only misses, the leg rescued 4 (20%) — meaningfully better than the earlier 0/8 (0%) finding, reopens the "should this leg be kept" question.
- **Not yet done:** Diagnostic 4 (margin / fusion-agreement / category-consistency as alternative confidence signals, on a proper train/test split) printed to the notebook but wasn't saved to a file this run — needed before deciding the fix.

## Lever 2 / data & eval pipeline — landed, partial

Mahnoor's `data/build_corpus.py` + eval pipeline is landed in `/data` and `/eval`. Details and dataset sizes: `eval/results.md`.

- `data/processed/final_corpus.csv`: 2,000 rows, schema-validated, 0 duplicates — ready for embedding
- `eval/out_of_scope_eval.csv`: 100 rows, 20/scope-type — **fixed** a generator bug that had produced only 4 distinct queries per type repeated to pad to 20 (80% exact duplicates); regression tests added in `data/tests/test_eval_sets.py`
- `eval/run_eval.py`: harness works end-to-end for dataset sizes; retrieval/safety metrics correctly report "NOT AVAILABLE" rather than fabricating numbers until predictions exist — **fixed** a crash when the (expected-missing) danger-sign file isn't present yet
- `eval/negative_set_100.csv`, `eval/danger_sign_eval_100.csv`, `eval/out_of_scope_eval_v2_100.csv`: newer deliverables from Mahnoor, verified clean (0 dup, 0 blank)
- `data/variants/colloquial_variants.csv`: smoke-test batch only, answer_id 1–30 of ~2000 (resumable via `_progress.json`)
- Danger-sign eval set: correctly not generated — blocked on an approved clinical source file, not fabricated

## Latest eval numbers

See `eval/results.md`. Provisional dense/sparse/fused ablation exists; final numbers against the human-reviewed 275-query gold set are queued but not yet run (needs a live Colab pass with GPU + the bge-m3 model — local machine is RAM-constrained).

## Variant review burn-down

Not yet started — variant generation itself is only ~1.5% complete (30/2000 answer_ids).

---
*Update this file when reality changes, not on a schedule.*
