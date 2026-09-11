# 0003 — Danger gate: generalising matching, not memorising misses

## Context

Rounds 3–6 of danger-gate fixes (see git history on `sabiha/pr1-ci-eval`)
took `eval/danger_sign_eval_100.csv` misses and, for each one, added a new
category or keyword copied close to verbatim from the missed sentence.
Recall on that 100-row set went 0.72 → 0.88 → 0.99 → 1.00.

That recall number was misleading. A hand test against six phrases *not*
in the eval set — the same clinical content, worded differently — found:

- 4 of 6 failed to escalate at all (`کنگهه سان رت اچڻ`, `پيشاب بلڪل نه
  اچڻ`, `ماهواري بند ٿيڻ کان پوءِ رت اچڻ`, `مسلسل الٽيون سان گڏ سخت اڃ`).
  Each of these has an existing category whose keyword was copied from a
  differently-worded sentence, so a change in word order or connector word
  (comma vs `سان گڏ`, verb inflection) broke the exact-substring match.
- Separately, `eval/negative_set_100.csv` — 100 benign questions that
  should never escalate — had a confirmed false positive: a dosage
  question about paracetamol for fever during pregnancy escalated because
  the `fever` category's keyword list included the bare word `بخار`
  (fever) with no severity qualifier, so it matched any mention of fever
  at all.

Root cause in both directions: `run_danger_gate` matched keywords via
plain substring containment (`normalize_sd(kw) in norm`) with no token
awareness, and the keyword lists themselves were built by generalising
from a sample of one — the exact sentence a miss report contained.

There was also a structural staleness bug: the embedding fallback's
reference-phrase list (`DANGER_PHRASES_FOR_EMBEDDING`) was a hand-
maintained list of ~25 canonical phrases from the original 11 categories.
Rounds 3–6 added 18 new categories and dozens of new keywords to
`DANGER_CATEGORIES` but never touched the embedding reference list, so
the semantic fallback had no way to catch paraphrases of any of the new
categories — it was running against roughly a quarter of the gate's
actual keyword surface.

## Decision

1. **Token-bag fallback matching.** `_phrase_matches` first tries exact
   substring (fast path, correct for most single-word or fixed phrases),
   then falls back to requiring every *significant* (non-stopword,
   length > 1) token of a multi-word keyword to appear in the query, in
   any order. This is deliberately not applied to single-token keywords —
   a lone generic word must still match exactly as itself, so this cannot
   make a single generic word match more broadly than before.

2. **Remove bare generic single-word keywords for common symptoms.**
   `بخار` (fever) was removed from `fever`'s keyword list; every remaining
   entry pairs it with a severity/duration/timing qualifier (`تيز بخار`,
   `سخت بخار`, `بخار ويم کان پوءِ`, `بخار لاهي نٿو اچي`). Generalise this
   principle before adding new categories: a common disease/symptom name
   alone is not a danger signal, the qualifier is.

3. **Auto-derive the embedding reference list from `DANGER_CATEGORIES`.**
   `_build_embedding_reference()` replaces the hand-maintained list.
   Adding a keyword to a category now automatically extends what the
   embedding fallback can match against — this class of staleness bug is
   now structurally impossible, not just fixed once.

4. **Add held-out adversarial regression tests**
   (`test_danger_escalates_on_paraphrase`) using paraphrases of the same
   clinical content as the eval set, never copied from it. If one of
   these starts failing, the fix is a more general keyword or a better
   matcher, not re-adding the exact failing sentence — that would repeat
   the same mistake this ADR documents.

5. **Add a false-positive regression test suite and a committed
   `eval/run_negative_set_eval.py`**, wired into CI as report-only (same
   posture as the recall check) until a verified false-positive baseline
   exists.

## What this does not fix

- ~~The embedding threshold (`EMBEDDING_THRESHOLD = 0.75`) is still a
  guessed constant.~~ **Update (measured on live model, 2026-09):**
  `eval/tune_embedding_threshold.py` was run against the real model and
  the auto-derived 276-phrase reference list. Result: **there is no
  threshold that gives both good recall and low false-positive rate** —
  it is a cliff, not a dial:

  | threshold | danger recall (embedding-dependent rows) | negative FP rate |
  |-----------|---|---|
  | 0.86 | 1.000 | 0.150 |
  | 0.88 | 0.667 | 0.130 |
  | 0.90 | 0.333 | 0.130 |
  | 0.92 | 0.000 | 0.100 |
  | 0.96 | 0.000 | 0.030 |

  Only 3/100 gold danger rows actually depend on the embedding path (the
  keyword + token-bag path alone already reaches 97/100 recall on its
  own). Every threshold that preserves that embedding-dependent recall
  also false-positives on 15%+ of the negative set — i.e. roughly 1 in 7
  benign questions would be told this is a medical emergency. Set to
  `0.90` as a precision-biased compromise, accepting most of the loss of
  the embedding path's already-small recall contribution.

  **Root cause, and the actual follow-up work:** `_build_embedding_reference()`
  pools all ~276 keywords from every category into one flat reference
  set with a single global threshold. A generic multilingual sentence
  embedder does not reliably separate "this sentence mentions the
  symptom" from "this sentence reports acutely experiencing the symptom
  right now" in Sindhi — e.g. a UTI-antibiotic-dosage question and a
  no-urine-output emergency both score close to "urine"-adjacent
  reference phrases. Fixing this needs reference-set curation (fewer,
  more clinically distinctive anchor phrases; possibly per-category
  thresholds instead of one global number), not a further threshold
  search. This is now the highest-priority open item for whoever owns
  Lever 5 next — the confidence-gate work in Phase 2/3 will hit the same
  problem if it pools reference phrases the same way.
- Sindhi's flexible word order and rich verb inflection mean even the
  token-bag fallback will miss phrasings that use a different verb form
  of the same idea (e.g. `اچڻ` vs `اچي` vs `آيو`). True robustness here
  needs either a small stemmer or leaning more on the embedding leg once
  it's properly tuned — this ADR buys generalisation across connector
  words and word order, not across morphology.
- Scope-classifier keyword matching (`SCOPE_REFERRALS`) still uses plain
  substring matching. Lower risk (misrouting to a referral message is not
  a safety miss the way failing to escalate is) but the same fragility
  exists there and hasn't been touched in this pass.

## Verification

- `pytest api/safety/test_danger_gate.py` — 44 tests, all passing,
  including the 4 new adversarial-paraphrase tests and 2 new
  false-positive guard tests.
- `python eval/run_danger_gate_eval.py` — 97/100 keyword-only in an
  environment without model access (up from a keyword-only baseline that
  would have missed the same 4 phrases this ADR fixes); the remaining 3
  rows have no keyword overlap with any category and depend on the
  (untested-here, structurally-fixed) embedding path.
- `python eval/run_negative_set_eval.py` — 0/100 false positives
  (previously 1 confirmed, `id 26`, and see the wider
  `negative_set_false_positives.csv` list from before this fix for
  further embedding-path false positives that need re-checking once
  the model can be run against the updated reference list).
