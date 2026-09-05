# Naari AI — Lever & Risk Playbooks, and Per-Person Phase Detail

Companion to `ROADMAP.md`. The roadmap says what gets built; this says how the levers are executed, what to do when each risk fires, and what each person owns in every phase.

---

## 1. Lever playbooks

### Lever 1 — Script normalisation
**Owner: Sana · Phase 1, first task**

Do not copy an Urdu normalisation map off the internet. Sindhi has 52 letters and several — ڏ ڄ ٺ ٿ ڪ ڳ ڱ ڃ ڻ ھ — are meaning-bearing in ways an Urdu map will destroy. Build the map from your own corpus:

1. Codepoint frequency histogram over all 2000 Sindhi rows (expect 80–110 distinct codepoints).
2. For each: decide **keep / map to X / drop**. Write the decision + reason into `docs/adr/0002-normalisation-map.md`.
3. Fixed order: NFC → strip zero-width (U+200B–U+200F, U+FEFF) → strip tatweel (U+0640) → remove harakat (U+064B–U+065F, U+0670) → apply character map → Arabic-Indic + Extended digits to ASCII → collapse whitespace.
4. Make it impossible to bypass: the embedding function calls the normaliser internally and is the only public way to embed anything.

**Tests that matter**
- *Idempotence:* `normalize(normalize(x)) == normalize(x)` for all 2000 rows.
- *Golden fixtures:* ~40 hand-written `(raw, expected)` pairs including messy input — mixed keyboards, Roman Sindhi, Urdu punctuation.
- *Non-destruction:* no two different KB questions may normalise to the same string. If they do, the map is too aggressive.

**Worked if:** Recall@5 measured with and without normalisation, gap reported in the ADR. Zero collisions.
**Fails like:** silently. No exception is ever raised — recall just sits 15 points lower and nobody knows why.

---

### Lever 2 — Colloquial question variants
**Owner: Mahnoor runs the pipeline; each person reviews their own two categories**
**Stage A starts Phase 0. Stages C–E in Phase 3.**

Chosen route: **harvest real speech first, then use it to steer generation.** An LLM asked cold for "Sindhi variants" produces textbook Sindhi — grammatical, clean, nothing like what a woman in Thatta says. Seeded with twelve real examples from the same category, the same model produces something usable.

**Stage A — Harvest 250–300 real questions**
- Sources by value: lady health workers (they hear these all day and can produce twenty in ten minutes), women in your families and neighbourhoods, WhatsApp voice notes, questions from pitch demos, the recording already in `assets/`.
- Transcribe **verbatim**. Do not clean grammar, do not standardise, keep hesitation and indirectness. The indirectness *is* the data — women rarely ask about reproductive health in direct clinical terms.
- `data/variants/seed_real.csv`: `text`, `source_type`, `rough_age_band`, `urban_rural`, `mapped_category`. No names, no villages — the safety rules apply to your own data collection too.

**Stage B — Extract the register**
`docs/sindhi_register_notes.md`: each clinical term mapped to the 2–4 ways real women say it. How do they refer to a period, being pregnant, pain, discharge, not conceiving? Which topics get approached sideways rather than named? This is a publishable artifact and a report chapter in its own right.

**Stage C — Generate, few-shot, per category**
- Batch by category so few-shot examples come from the same topic. Twelve real examples + the KB row → five variants in that register.
- Temperature ~0.9. You want spread, not the safest phrasing five times.
- Dedupe twice: exact match on normalised text, then cosine > 0.95.
- Quota: batch ten rows per call ≈ 200 calls — inside Groq's 1,000/day. This is an offline build step, so rate limits don't matter; just run it over an afternoon.

**Stage D — Review with a realistic budget**
Not a CSV in Excel. A three-column Google Sheet (variant / keep-fix-drop / corrected text) clears ~200 rows per hour.
Do the arithmetic out loud, because this is where projects like this die: 2000 × 5 = 10,000 lines ÷ 200/hr = 50 hours = 12.5 hours each. Survivable **if split and tracked**. See Risk 5 for cutting it to ~6,400.

**Stage E — Priority order:** danger-sign and pregnancy clusters → high-frequency symptom rows → myth-busting last.

> ⚠️ **The mistake that would invalidate your results:** gold eval queries must be written **independently of the variants**, ideally by a different person, drawn from the seed real-question set rather than generated. If eval queries and indexed variants come from the same generator you are measuring whether an LLM matches itself. Mahnoor writes the gold set; whoever generates variants does not touch it.

**Worked if:** Recall@5 on the held-out gold set improves by ≥8 points with the variant index on vs off.
**Fails like:** slowly. Review stalls at 40%, nobody says so, retrieval ends up tuned to phrasing no real woman uses.

---

### Lever 3 — Hybrid dense + sparse with rank fusion
**Owner: Sana · Phase 1, right after the dense baseline**

- One Qdrant collection, two named vectors per point: `dense` (1024-d, cosine) and `sparse`. bge-m3 returns both from one forward pass (`return_dense=True, return_sparse=True`).
- Query both legs, top 25 each, then RRF: `score = Σ 1/(60 + rank)`. Use RRF rather than a weighted blend — the two scores live on different scales and RRF needs no calibration.
- Produce an ablation table: dense-only / sparse-only / fused Recall@5.

> ⚠️ **Known trap:** bge-m3's sparse weights are keyed by its own tokeniser's token IDs, so query and index must use the same tokeniser — and exporting the sparse head to ONNX is fiddlier than the dense head. If ONNX export of sparse fights you, don't lose a week: swap the sparse leg for plain BM25 (`rank_bm25`) over whitespace-tokenised normalised text. 90% of the benefit for 10% of the trouble, and a legitimate engineering decision to write up.

**Worked if:** fused Recall@5 beats the better single leg by ≥3 points. If not, drop it and document why — a measured negative result is worth more than a feature kept out of hope.

---

### Lever 4 — Cross-lingual dual index
**Owner: Sana · Phase 1 (measure), Phase 2 (make conditional)**

- Index the English rows into the same collection with a `lang` payload field, sharing `answer_id` with their Sindhi twins.
- Translate the Sindhi query with **NLLB-200-distilled-600M** locally (supports `snd_Arab`). Free, ~200ms CPU, consumes no API quota and adds no external failure point.
- Fuse English results by `answer_id`.

**Make it a cascade, not a fixed cost.** Three models resident on a free CPU box is tight, and the English leg only helps when the Sindhi leg is struggling. Run it **conditionally**: if the Sindhi reranked top score already clears τ_high, skip translation entirely. Only when uncertain do you pay 200ms for a second opinion. This keeps median latency low, keeps memory manageable, and turns the lever from an always-on tax into a targeted rescue.

**Worked if:** measured on the subset where Sindhi-only retrieval failed — what fraction does English rescue? Report that, not overall recall, which hides the effect.

---

### Lever 5 — The confidence gate
**Owner: Sana sets thresholds · Sabiha owns band behaviour · Mahnoor builds the negative set**
**Phase 2, retuned in Phase 3**

1. Run the gold set through retrieval + reranking. Record top-1 score and whether top-1 was correct.
2. Plot two overlapping distributions: correct vs incorrect top-1. **τ_high** = score where precision of "top-1 is correct" reaches 0.95.
3. For **τ_low** you need what most teams forget: a **negative set** — ~100 health-shaped questions with no correct KB answer ("my child has fever", "my husband's blood pressure", "what causes kidney stones"). Without these you cannot distinguish "low score because retrieval is unsure" from "low score because the answer isn't there", and τ_low is a guess.
4. Set τ_low so ≥90% of the negative set falls below it.
5. Plot the precision/coverage curve. One of your strongest figures when presenting the work — it shows you chose a point on a trade-off deliberately.

**Worked if:** verbatim-path precision ≥0.95 at τ_high, refusal rate on the negative set ≥0.90.

---

## 2. Risk register

### Risk 1 — Sindhi embeddings are simply too weak
**Owner: Sana · Decision point: Phase 1 exit gate**
*Signal: dense-only Recall@5 < 0.55 in the baseline, or < 0.70 after all five levers.*

**Check three things before concluding anything:**
1. **Is normalisation the culprit?** Run the baseline with and without. A too-aggressive character map merges distinct Sindhi letters and looks exactly like "the model is bad".
2. **Are you using the model's required prefixes?** The e5 family needs `"query: "` / `"passage: "` prefixes and quietly underperforms badly without them. bge-m3 does not want prefixes. Getting this backwards is the most common silent RAG bug and costs teams weeks.
3. **Is your gold set fair?** Queries written by looking at KB rows are too close to the source and inflate numbers; queries written from pure imagination may be unfairly hard. Draw them from the seed real-question set.

**Escape hatch — fine-tune the embedder.** You own 2000 aligned Q–A pairs plus thousands of variants: that is a contrastive training set.
- Train on **Google Colab free T4**, not your CPU box. ~1 hour.
- `sentence-transformers` + `MultipleNegativesRankingLoss`, batch 32, 2 epochs, on (variant → correct answer) pairs. In-batch negatives do the work; no hard-negative mining needed for a first gain.
- Hold out 20% of rows entirely so you can prove it isn't memorisation.
- Push to HF Hub, load in the Space like the base model.

**Reframe before panicking:** this is not a setback, it's the strongest possible outcome for the report. *"We fine-tuned a multilingual embedder for Sindhi health retrieval and moved Recall@5 from 0.61 to 0.84"* beats *"we used an off-the-shelf model and it worked."* Budget for the possibility rather than fearing it.

---

### Risk 2 — Free CPU inference too slow
**Owner: Sana** · *Signal: p95 > 5s with models warm.*

Fixed mitigation order: ONNX int8 both models → make the English leg conditional (Lever 4) → cut candidates 25→15 → drop the reranker. Stop as soon as you're under 3s; each step trades away something real.

---

### Risk 3 — the LLM provider rate-limits during a demo
**Owner: Sabiha** · *Signal: 429s under load, or a cold Space taking 40s while a jury watches.*

**Before it fires**
- **Cache on normalised query text** in Postgres, 24h TTL. Demo questions get asked repeatedly in rehearsal, so by demo day they're all warm.
- **Measure your verbatim-path rate.** If >70% of realistic questions clear τ_high, most of your demo never touches an LLM. That's your real insurance — optimise for it deliberately.
- **One `select()` interface, three implementations:** Groq → OpenRouter → deterministic top-1-by-rerank-score (no LLM at all). Because the LLM only picks between retrieved answers, the no-LLM fallback still returns a correct vetted answer — it just picks slightly less well. Test failover by deliberately revoking the Groq key once.
- **A demo-mode flag** forcing verbatim-only, refusing everything below τ_high. Slightly less impressive, completely unbreakable. Have it ready even if unused.
- **Keep the Space warm** with a scheduled ping every 10 min on demo day, or accept a 40s cold start in front of judges.

**When it fires:** flip to demo mode and keep going. Never debug live — say the system is running in conservative mode and continue, which is a perfectly good thing for a health product to be seen doing.

**Rehearsal rule:** run the exact demo script ten times the day before and count the 429s. Any today means any tomorrow.

---

### Risk 4 — No clinical reviewer, and none lined up yet
**Owner: Mahnoor (sourcing) · Sana (schema) · Sabiha (serving) · Tooba (banner)**

> ⚠️ **Amend the roadmap.** `ROADMAP.md` puts reviewer engagement in Phase 4. With nobody lined up that is too late — clinician outreach runs on a scale of weeks and cannot be compressed by working harder. **Move first contact into Phase 0** and let it run in the background.

**Who to approach, roughly in order**
- **Proxima's own network, and your supervisor's** — ask there first. The shortest path is almost always someone who already knows someone.
- **Aga Khan University, Community Health Sciences** — they run LHW and maternal health research and are unusually receptive to student work in this space.
- **Dow University final-year MBBS students** for a first pass, plus one consultant for sign-off. Two tiers costs much less of the scarce person's time.
- **Lady Health Worker Programme district office** (Thatta, Sujawal) — an LHW supervisor is arguably a *better* reviewer than a hospital consultant here, because she knows what rural women actually ask and what advice is actionable where there is no transport.
- **Reproductive health NGOs** — Greenstar, Marie Stopes, Sina Health, Aman Foundation.
- **NIC Karachi mentor network**, if the application progresses.

**Ask small and specifically.** Nobody will review 2000 rows. Build a **150-row high-risk packet**: every danger-sign row, every pregnancy-complication row, the 22 thyroid rows already flagged in your own `REVIEW_NOTES.md`, plus a random 50 for calibration. ~2 hours of a clinician's time is an askable amount. Send it as a document with a yes/no/edit column — not a CSV, not a repo link.

**Engineering fallback — tier the corpus.** Add `review_tier` to the schema:
- **Tier A** — clinician-reviewed. Served normally.
- **Tier B** — sourced to WHO or a named guideline, peer-reviewed in-team, not clinician-verified. Served with a visible banner saying exactly that.
- **Tier C** — uncertain or flagged. Not served; the system refuses and refers.

This turns an unbounded blocker into a bounded, honest product decision. *"We built a tiered disclosure system because clinical review was incomplete"* is a much better answer to a supervisor than either "we didn't get review" or — far worse — presenting unreviewed content as vetted.

**Hard line:** never present Tier B content as clinically verified, in the product, the deck, or the report.

---

### Risk 5 — Variant review stalls at 10,000 lines
**Owner: Mahnoor tracks, everyone delivers** · *Signal: two weeks into Phase 3, completion below 50% and nobody has said so.*

**Cut the number before you start — don't grind through it.** Query frequency in health FAQ systems is heavily skewed; a small set of rows absorbs most real questions. Tier the effort:

| Tier | Rows | Variants each | Total | Which rows |
|---|---:|---:|---:|---|
| High | 400 | 6 | 2,400 | Danger signs, pregnancy, anything matching the seed real-question set |
| Medium | 800 | 3 | 2,400 | Common symptom and care-seeking rows |
| Low | 800 | 2 | 1,600 | Myth-busting, background explanation, rare edge cases |
| **Total** | | | **6,400** | vs 10,000 — about 8 hours each rather than 12.5 |

**Make progress impossible to hide**
- `data/variants/review_status.csv` holds per-category counts; a CI step writes a burn-down line into `docs/status.md` on every push. Nobody has to be asked how it's going.
- A fixed weekly quota per person, agreed once, visible to everyone. Self-set quotas get met far more often than handed-down deadlines.
- Review in pairs for the first session. It's dull work, twice as fast with company, and the first hour is where you agree what "fix" vs "drop" actually means.

**If it still stalls:** ship the High tier only and reindex. 2,400 reviewed variants on rows that matter beats 6,400 half-reviewed ones, and you can report exactly which tiers were covered.

---

### Risk 6 — No usable Sindhi TTS exists
**Owner: Tooba (playback) + Mahnoor (recording)** · *Assume this will happen; free Sindhi TTS is genuinely not solved.*

> ✅ **The insight that makes voice output achievable anyway.** You are not building an open-ended conversational agent. On the high-confidence path your system returns **one of 2000 fixed answers, verbatim**. So you don't need generative TTS at all — you need **2000 audio files**. Record a native Sindhi speaker reading the answers, store them in Supabase storage, play the file. Perfect pronunciation, perfect prosody, real warmth, zero inference cost, no model risk. Record the 300 highest-frequency answers first and you've covered most real traffic — one focused weekend with a decent mic and a quiet room.

**Three honest tiers for prototype 2**
1. **Voice in, text out.** Always achievable. ASR is the harder half anyway, and this alone is a real accessibility gain for women who can speak but read with difficulty.
2. **Voice in, recorded human voice out** for anything on the verbatim path; text for the rest. **Recommended target** — will sound better than anything generative you could reach on a free tier.
3. **Generative TTS** — train Piper/VITS on the same recordings. Only worth attempting once tier 2 works; makes a good future-work section either way.

The recording session does double duty: same clips give Mahnoor an ASR test set, and a small donated-speech dataset is publishable on its own.

---

### Risk 7 — One person becomes the bottleneck
**Owner: Sana (as architecture lead)** · *Signal: anyone blocked >48 hours, or three people waiting on one folder.*

In a four-person project this is the most probable failure mode of all, and it usually points at whoever owns retrieval.

**Contract-first, from Phase 0**
- `docs/contracts/` holds the JSON shapes — retrieval output, `/ask` request and response — agreed and committed *before* implementation. Once the shape is fixed, three people build against it simultaneously.
- **Everyone ships a mock on day one.** Sana ships `FakeRetriever` returning three fixed rows. Sabiha ships `/ask` returning canned responses. Tooba is then never blocked on anyone, which alone removes most of this risk.

**Habits that keep it from returning**
- WIP limit: no more than two open PRs per person. More means work is piling up unreviewed — the same bottleneck wearing a different hat.
- 30-minute weekly sync whose first item is "what am I blocked on". Anything blocked >48h converts to a pairing session, not another status update.
- By Phase 2 each person writes a one-page "how my folder works" in `docs/`, and a second person must run it from those notes alone. Four people is exactly the size where one illness stops everything.

> **Sana — this one is aimed at you.** You've taken the core technical layer, which means everyone else's work flows through your folder. Right call for you, wrong shape for the team unless actively defended against. Ship the mock early, publish the contract before the implementation, and treat "someone is waiting on me" as higher priority than whatever you're optimising.

---

## 3. Per-person playbooks

Every item has a **Done when** — if you can't tell whether it's finished, it isn't specified yet. Tags in brackets link the item to its lever or risk.

---

### SANA — Retrieval core, architecture (`/retrieval`)

**Standing scope.** Everything between a normalised string and a ranked list of answer IDs, plus the architectural decisions binding the other three folders together. You own levers 1, 3, 4 and the thresholds in 5, and carry risks 1, 2 and 7. Your judgement calls are ones nobody else is positioned to make: when a lever has stopped earning its complexity, and when to stop tuning and ship.

#### Phase 0 — Set the ground everyone else builds on
*Almost all of this phase's value is in decisions that are cheap now and expensive later. Spend the time.*

- [ ] **Create repo, folder skeleton, README, `.gitignore`, `.env.example`** — *Done when* all three teammates have cloned it and `main` is protected with 1 required approval.
- [ ] **Write and commit the interface contracts** — *Done when* `docs/contracts/retrieval.json` and `ask.json` exist and Sabiha and Tooba have explicitly agreed in a PR comment. `[Risk 7]`
- [ ] **Ship `FakeRetriever` returning three hardcoded rows in the contract shape** — *Done when* Sabiha can import it and get a valid response with no model, index or network. `[Risk 7]`
- [ ] **Add `review_tier` to the corpus schema alongside Mahnoor's merge** — *Done when* every row carries a tier, defaulting to B, enforced by the validator. `[Risk 4]`
- [ ] **Open `docs/adr/0001` recording stack decisions and what was rejected** — *Done when* bge-m3 vs e5, Qdrant vs FAISS, the Railway / HF Spaces split each have a paragraph of reasoning.

#### Phase 1 — Prove Sindhi retrieval works, or find out it doesn't
*Measure after every single change, one at a time, so every point of recall is attributable. Resist adding two levers at once — you won't untangle them afterwards.*

- [x] **Codepoint histogram + commit the normalisation decision table** — *Done when* every codepoint is classified keep/map/drop in `docs/adr/0002` with a reason. `[Lever 1]` — 145 codepoints classified in `docs/adr/0002-normalisation-map.md`.
- [x] **Implement `normalize_sd()` with idempotence, golden-fixture and non-destruction tests** — *Done when* all three test classes pass and no two distinct KB questions collide. `[Lever 1]` — `retrieval/normalize.py` + `retrieval/tests/test_normalize.py`, idempotence over all 4000 question+answer strings, 47 golden fixtures, 0 collisions.
- [x] **Embed 2000 Sindhi + 2000 English rows; create the Qdrant collection** — *Done when* it holds 4000 points with named dense/sparse vectors and a `lang` payload. — **4000/4000 as of 2026-09-01**, verified live against the collection (`points_count` + direct point retrieval, not just trusting the notebook's own print statement). `id=2000`'s English translation (`retrieval/scripts/embed_missing_english_row.ipynb`) closed the last gap.
- [x] **Dense-only baseline against the first 100 gold queries** — *Done when* Recall@1/@5/@20 are committed to `eval/results/` with the commit hash. `[Risk 1]` — superseded by the fuller 275-query linked gold set (see Lever 3 ablation below); numbers live in `eval/results.md`, committed to git.
- [x] **Verify the model prefix convention before trusting the baseline** — *Done when* you've confirmed in the model card whether prefixes are required, and tested both ways if unsure. `[Risk 1]` — empirically confirmed 2026-09-01 (`eval/results.md`): no-prefix Recall@1 0.552 vs prefixed 0.431 on the same 58-query candidate pool. Confirms ADR 0001; Risk 1's "most common silent RAG bug" is not present here.
- [x] **Add the sparse leg and RRF fusion; produce the ablation table** — *Done when* dense-only, sparse-only and fused Recall@5 appear in one committed table. `[Lever 3]` — `retrieval/search.py` (`HybridRetriever`, `reciprocal_rank_fusion`). **Final, trustworthy table in `eval/results.md` as of 2026-09-01** (275-query human-reviewed gold set, `lang="sd"` bug fixed): dense 0.462/0.880/0.975, sparse 0.542/0.898/0.971, fused 0.967/0.971/0.975 (Recall@1/5/20). Fused beats the better single leg by well over the ≥3-point bar at every K.
- [x] **Add the English dual path with local NLLB translation** — *Done when* you can state what fraction of Sindhi-only failures English rescues. `[Lever 4]` — `retrieval/translate.py` (NLLB-200-distilled-600M) + `HybridRetriever.cross_lingual_search()` built and measured 2026-09-01: of 8 Sindhi-only misses in the corrected gold set, English rescued **0 (0.0%)**. Small n, and not blocking Phase 1 exit since fused already clears the bar without it — but a real, unflattering number, not a flattering assumption. Worth checking the actual NLLB translations on those 8 queries before Phase 2 makes this leg conditional.
- [x] **Add cross-encoder reranking over the fused top 20** — *Done when* the Recall@1 improvement from reranking is measured and committed. `retrieval/rerank.py` built and tested. Raw measurement (Recall@1 0.385) came back confounded by gold-set noise, not a real capability finding — a 40-row manual audit of the disagreements (`eval/rerank_regression_audit.csv`) found the reranker right about as often (12) as genuinely wrong (11), with another 30% of disagreements being cases where fused's own top-1 was *also* wrong (BOTH_WRONG) — meaning the never-individually-reviewed 146/275 gold rows are too coarse to fairly score a component this discriminating. One real, confirmed weakness: occasional cross-category confusion from surface phrase overlap. Latency (p95 112ms/20 candidates) is well inside budget. Not blocking Phase 1's GO. Before this feeds anything load-bearing (Lever 5 thresholds), the gold set needs the rest of its rows individually reviewed, not just the original 24.
- [x] **Phase 1 go/no-go on the embedding model** — *Done when* Recall@5 ≥ 0.85, or a written decision to fine-tune on Colab with a named date. `[Risk 1]` — **GO.** Fused Recall@5 = 0.971 on the 275-query human-reviewed gold set, well clear of the 0.85 exit gate (`docs/ROADMAP.md` §5) and the 0.70 fine-tune-escalation floor. No fine-tuning needed to proceed to Phase 2. Reranking (previous item) remains worth doing for Recall@1/confidence-gate precision, not to hit this bar.

#### Phase 2 — Make it a service, not a notebook
*The gap between "works in my notebook" and "works in Sabiha's container at 3am" is mostly model loading, memory and cold starts. Handle it now, not during a demo.*

- [x] **Package retrieval as an importable module, models loaded once at startup** — *Done when* a second query returns under 1s and memory is flat across 100 requests. Live-verified 2026-09-02: second query 1067ms (67ms over target, reads as noise not a real problem given this started at 25000-60000ms before the `retrieval/translate.py` GPU-device fix), memory flat (+13MB over 100 calls). Effectively done.
- [ ] **Make the English leg conditional on the Sindhi top score** — *Done when* median latency drops measurably and Recall@5 does not. `[Lever 4] [Risk 2]` — code done and live-tested 2026-09-02, but the comparison run (forced-off vs conditional) tested the wrong pair — needs conditional vs. **always-on** (`tau_high=1.1`) to actually answer "does making it conditional save time over always translating". Re-run pending.
- [ ] **Tune τ_high and τ_low from score distributions and the negative set** — *Done when* the precision/coverage curve is committed as a figure and both thresholds have a stated justification. `[Lever 5]` — **Gold-set review complete** (2026-09-02): every row in `eval/gold_eval_280_linked.csv` individually verified against the KB (25 new + 151 never-flagged + 105 bulk-confirmed legacy rows; 280 → 248 rows, no coarse category-only acceptances left). Re-run against the cleaned set on Kaggle 2026-09-02T09:45:31Z: `tau_low = 0.1647` (hits the ≥90% negative-set target), but **`tau_high` still doesn't converge** — no threshold reaches 0.95 precision anywhere. **This changes the diagnosis.** With labels now fully clean, the score-distribution figure (`eval/tau_score_distributions.png`, this run) shows the correct (n=80) and incorrect (n=168) top-1 predictions still overlapping heavily even at score ≈0.9–1.0 (43 correct vs. 35 incorrect in that bin — ~55% precision at the very top of the range). **This is no longer a gold-set noise problem — it's a real pipeline/reranker calibration gap**: `bge-reranker-v2-m3` is handing out near-1.0 confidence to a substantial fraction of wrong answers, consistent with the cross-category surface-overlap weakness flagged in the Item 8 audit (`gold_7`). Recall@1 against the now-clean labels also dropped to ~0.32 (was ~0.38 against noisy labels) — expected, since inflated matches against wrong ground truth are gone. **Next step:** pull the ~35 incorrect-but-≥0.9-scoring queries from this run and manually audit them (same method as the Item 8 rerank audit) to characterize the failure mode before deciding whether to fix via reranker prompt/threshold tuning, per-category thresholds, or a different confidence signal.
- [ ] **Convert both models to ONNX int8** — *Done when* p95 retrieval latency is under 1.5s on the free Space and recall is within 1 point of float32. `[Risk 2]`

#### Phase 3 — Absorb the variants and retune
*The index roughly quadruples. Thresholds tuned before variants will be wrong after them — retuning is the step that converts Mahnoor's review hours into actual recall.*

- [ ] **Index reviewed variants as their own points sharing `answer_id`** — *Done when* retrieval dedupes by `answer_id` before reranking and never returns the same answer twice. `[Lever 2]`
- [ ] **Measure recall with variant index on vs off, on the held-out gold set** — *Done when* the lift is committed. Target +8 points Recall@5. `[Lever 2]`
- [ ] **Retune both thresholds against the enlarged index** — *Done when* verbatim precision is still ≥0.95 and negative-set refusal still ≥0.90. `[Lever 5]`
- [ ] **Review your own two categories — Pregnancy/Maternal and PCOS** — *Done when* your rows show 100% in the burn-down. `[Risk 5]`
- [ ] **Write the "how retrieval works" page in `docs/`** — *Done when* a teammate rebuilds the index from scratch using only that page. `[Risk 7]`

#### Phase 4 — Close the loop with what real users asked
*Questions that got refused in user testing are the highest-value data the project will ever produce: free, real, and precisely targeted at your blind spots.*

- [ ] **Build the unanswered-question pipeline from logs** — *Done when* a weekly export lists every query below τ_low, clustered by similarity.
- [ ] **Turn pilot questions into new variants or KB rows and reindex** — *Done when* the pre/post-pilot recall lift on real user questions is measured.
- [ ] **Apply reviewer edits and promote reviewed rows to Tier A** — *Done when* tier counts appear in `docs/status.md` and the index reflects them. `[Risk 4]`

#### Phase 5 — Sindhi ASR, measured honestly
*ASR output is noisy in ways your normaliser wasn't designed for. Expect retrieval quality to drop; closing that gap is the actual research question of prototype 2.*

- [ ] **Evaluate MMS-1B-all vs Whisper-small fine-tuned on Common Voice Sindhi** — *Done when* WER for both is committed, measured on Mahnoor's recordings, not a public benchmark.
- [ ] **Measure retrieval recall on ASR transcripts vs clean text** — *Done when* the gap is quantified. This number is prototype 2's headline result.
- [ ] **Harden retrieval against ASR noise** — *Done when* fuzzy or phonetic matching recovers at least half the recall lost to transcription errors. `[Lever 1]`

---

### SABIHA — Backend, orchestration & safety (`/api`)

**Standing scope.** Everything between an HTTP request and a response: pipeline order, safety gates, LLM, filters, logs. You own the highest-stakes code in the project — the danger-sign gate is the one component where a bug has a physical consequence for a real woman. You also own Risk 3, the risk most likely to show up in front of judges.

#### Phase 0 — Deploy something empty, immediately
*Teams that leave deployment until the end discover their container problems under maximum pressure. A deployed `/health` on day one means every later deploy is a small change to something that already works.*

- [x] **FastAPI skeleton with `/health`, Dockerfile, deployed to Railway** — *Done.* `naari-ai-production.up.railway.app/health` returns 200; `/ask` matches the agreed contract.
- [ ] **Mock `/ask` returning canned responses in the agreed contract shape** — *Done when* Tooba can build the entire UI against it with no real backend. `[Risk 7]`
- [ ] **Secrets handling: `.env.example` in git, real values in Space secrets only** — *Done when* a fresh clone runs with mocks and no secrets, and no key has ever been committed.

#### Phase 1 — Build the safety gate independently of everything else
*It must not depend on retrieval, the LLM, or anything that can be slow or down. Building it standalone lets it be tested to exhaustion long before it's wired in.*

- [ ] **Danger-sign gate as a pure function over normalised text** — *Done when* it detects all eleven danger categories from `kb_safety_always_on.md` and returns the exact escalation script.
- [ ] **Add embedding-similarity detection alongside keyword matching** — *Done when* a phrasing sharing no keyword with the bank, but meaning the same thing, still triggers escalation.
- [ ] **Scope classifier for abortion, named contraceptives, DV, non-health** — *Done when* each routes to its own referral response and "are you a doctor?" is handled explicitly.
- [ ] **Test against Mahnoor's first adversarial phrasings** — *Done when* danger-set recall is 1.00 and every miss found has been added as a regression test.

#### Phase 2 — Wire the pipeline and constrain the model hard
*The prompt is a safety control, not a formatting preference. Write it as though the model will look for any opening to be helpful in a way you did not authorise — because it will.*

- [ ] **Implement stages 00–08 in order, danger gate short-circuiting everything** — *Done when* a danger-sign query provably never reaches retrieval or the LLM, verified in logs.
- [ ] **Implement the three-band confidence gate behaviour** — *Done when* the response payload states which band and path produced it. `[Lever 5]`
- [ ] **Write the selection prompt for the middle band** — *Done when* the model returns only an `answer_id` or `NONE`, never prose, and returns `NONE` in a test where all five retrieved candidates are deliberately irrelevant. Anything that isn't a valid ID from the candidate list is rejected by the parser and treated as `NONE`.
- [ ] **Build `select()` with Groq → OpenRouter → deterministic fallback** — *Done when* revoking the Groq key mid-session degrades cleanly with no user-visible error and answers still return. `[Risk 3]`
- [ ] **Structured logging into Supabase** — *Done when* query, retrieved IDs, scores, band, path, latency and provider are queryable for any request.

#### Phase 3 — Harden: filters, limits, tiers, caching
*This is where the service stops being a demo. The output filter is your last line of defence and must be able to override a confident model.*

- [ ] **Output filter blocklists: medicine names, dose patterns, diagnosis phrasing, false reassurance** — *Done when* a trip downgrades to refusal and logs it. Verified against a deliberately adversarial prompt-injection test.
- [ ] **Enforce `review_tier` in serving** — *Done when* Tier B responses carry the disclosure flag and Tier C rows are never served. `[Risk 4]`
- [ ] **Response cache keyed on normalised query, 24h TTL** — *Done when* a repeated question returns from cache and hit rate is visible in logs. `[Risk 3]`
- [ ] **Rate limiting and a demo-mode flag** — *Done when* demo mode forces verbatim-only and toggles without a redeploy. `[Risk 3]`
- [ ] **Review your own two categories — Menstrual and Mental Health** — *Done when* your rows show 100% in the burn-down. `[Risk 5]`

#### Phase 4 — Operate it like something people depend on
*During the pilot it's being used by real women in front of you. Nothing degrades a session faster than a cold start nobody warned the tester about.*

- [ ] **Uptime monitoring and cold-start mitigation** — *Done when* a scheduled ping keeps the Space warm during testing windows and downtime is visible without manual checking.
- [ ] **Write the incident runbook** — *Done when* another team member can restore service from it alone, without asking you. `[Risk 7]`
- [ ] **Demo rehearsal: run the full script ten times, count 429s and cold starts** — *Done when* ten consecutive clean runs are recorded. `[Risk 3]`

#### Phase 5 — Audio in, audio out
*Audio changes the failure modes: uploads fail on bad connections, transcription is slow, and the safety gate now runs on possibly-garbled text.*

- [ ] **Audio upload and transcription endpoints with size/duration limits** — *Done when* a 30-second Sindhi clip returns a transcript and oversized uploads fail with a clear message.
- [ ] **Serve pre-recorded answer audio from Supabase storage** — *Done when* a verbatim-path answer returns an audio URL alongside its text. `[Risk 6]`
- [ ] **Make the danger gate ASR-noise tolerant** — *Done when* deliberately corrupted transcripts of danger phrases still escalate. Err toward false escalation here, never away from it.

---

### TOOBA — Web app & product (`/web`)

**Standing scope.** Everything the user sees, and the judgement about whether a woman with limited literacy and a cheap phone can actually use it. Your hardest constraint isn't technical — it's that your instincts as a CS student are calibrated to users nothing like your users. Test on a real budget Android phone, on mobile data, early and often. You co-own Risk 6 and the Tier B disclosure design under Risk 4.

#### Phase 0 — Prove Sindhi renders correctly before building on top of it
*Sindhi has characters many fonts and Android versions render as boxes or drop entirely. Finding out in Phase 0 costs an afternoon; in Phase 3 it costs a rebuild.*

- [ ] **Next.js skeleton with RTL layout, deployed to Vercel** — *Done when* a public URL renders a Sindhi sentence right-aligned and correctly ordered.
- [ ] **Font audit on a real budget Android device** — *Done when* ڏ ڄ ٺ ٿ ڪ ڳ ڱ ڃ ڻ ھ all render correctly in your chosen face, tested on a phone and not only desktop Chrome.
- [ ] **Set the type scale for low-literacy reading** — *Done when* body text is ≥18px with generous line height, and someone unfamiliar has read a full answer aloud without straining.

#### Phase 1 — Build the whole experience against a mock
*You're unblocked by design here. Use the freedom on the genuinely hard product problem: how does a woman who is unsure what to ask, and may be uncomfortable typing it, get started at all?*

- [ ] **Chat UI against Sabiha's mock endpoint** — *Done when* the full send/receive loop works with zero real backend. `[Risk 7]`
- [ ] **Category shortcut cards for the eight KB categories** — *Done when* a user can reach a relevant answer without typing a full question.
- [ ] **Source citation display** — *Done when* the WHO or guideline source is visible with the answer, not hidden behind a tap.
- [ ] **Design the escalation response treatment** — *Done when* a danger-sign response is visually unmistakable and calm rather than alarming. Get a Sindhi speaker's reaction before finalising.

#### Phase 2 — Connect to reality, including its slowness
*A cold Space takes ~40s to wake. On 3G with no feedback, users conclude the app is broken and leave. How you handle waiting is a real feature here, not polish.*

- [ ] **Swap the mock for the live API with streaming responses** — *Done when* answers appear progressively rather than after a silent wait.
- [ ] **Cold-start and error states** — *Done when* a 40s wake shows honest progress in Sindhi and a failed request offers a retry, never a stack trace.
- [ ] **Refusal and referral treatment** — *Done when* "I can't answer this, please ask a lady health worker" reads as helpful rather than a failure. `[Lever 5]`
- [ ] **Test the deployed app on a budget Android phone on mobile data** — *Done when* a full round trip is usable one-handed and you've written down what was awkward.

#### Phase 3 — Feedback, offline, accessibility, disclosure
*The thumbs rating isn't a vanity metric — it's the input to the next KB version and the only signal you'll get from users you can't observe. Make it effortless.*

- [ ] **Thumbs up/down capture wired to Supabase** — *Done when* a rating is one tap, requires no account, and lands in a table Mahnoor can query.
- [ ] **Tier B disclosure banner** — *Done when* unreviewed content is visibly marked in a way a non-technical user actually understands. `[Risk 4]`
- [ ] **PWA offline shell with install prompt** — *Done when* the app opens offline and explains it needs a connection, rather than showing a browser error page.
- [ ] **Accessibility and low-bandwidth pass** — *Done when* first contentful paint is under 3s on throttled 3G and every control has a visible focus state.
- [ ] **Stub the microphone affordance for Phase 5** — *Done when* the button exists, is disabled, and the layout won't need rework when enabled.
- [ ] **Review your own two categories — Fertility and Hygiene** — *Done when* your rows show 100% in the burn-down. `[Risk 5]`

#### Phase 4 — Watch real women use it, then fix what you see
*Uncomfortable and the most valuable thing you do. Expect the failures to be onboarding, font size and the first screen — almost never the model.*

- [ ] **Run usability sessions without helping** — *Done when* you've watched 10–15 women use it and recorded every hesitation without intervening.
- [ ] **Fix the top five friction points** — *Done when* each has a before/after note in `docs/` and a second session confirms the fix.
- [ ] **Rework the first screen based on what you saw** — *Done when* a first-time user knows what to do within ten seconds, unprompted.

#### Phase 5 — Voice interaction
*Voice is the point of the whole project — it's what makes this reachable for women who can't comfortably read or type. It also has to fail gracefully, because it will fail sometimes.*

- [ ] **Push-to-talk with live waveform feedback** — *Done when* a user can tell the app is listening without reading any text.
- [ ] **Audio playback of answers with replay** — *Done when* a woman can replay an answer as many times as she wants with one tap. `[Risk 6]`
- [ ] **Show the transcript and let her correct it** — *Done when* a misheard question can be fixed without re-recording. This is the main mitigation for imperfect Sindhi ASR.
- [ ] **Graceful fallback to text on any audio failure** — *Done when* denied mic permission or a failed upload still leaves a fully working app.

---

### MAHNOOR — Data, evaluation & QA (`/data`, `/eval`)

**Standing scope.** The corpus, the variants, the evaluation sets, the harness, the clinical review, the user testing. You own two of the project's three largest risks — the reviewer (4) and the variant review (5) — and you produce the numbers the whole project is graded on. Your work has the longest lead times of anyone's, which is why several Phase 3 and 4 tasks start in Phase 0.

#### Phase 0 — Start the two things that cannot be rushed later
*Clinician outreach and real-speech harvesting both depend on other people's calendars. Every week you delay the first email is a week added to the end of the project.*

- [ ] **Merge all four CSVs into one schema-validated corpus** — *Done when* 2000 rows pass validation, no duplicate IDs, no duplicate questions across the whole set, every source URL resolves.
- [ ] **Make the corpus generated, never hand-edited** — *Done when* `build.py` reproduces the merged file from sources and runs duplicate/orphan-citation checks in CI.
- [ ] **Send the first three clinical reviewer approaches** — *Done when* three named contacts have been emailed and logged in `docs/reviewer_outreach.md` with dates. `[Risk 4]`
- [ ] **Assemble the 150-row high-risk review packet** — *Done when* it exists as a document with a yes/no/edit column, ready to send the moment anyone says yes. `[Risk 4]`
- [ ] **Begin harvesting real questions from LHWs, family and neighbours** — *Done when* 50 verbatim questions are in `data/variants/seed_real.csv` with no identifying details. `[Lever 2]`

#### Phase 1 — Give Sana something honest to measure against
*The gold set is the instrument the entire project is judged with. If it's biased toward the KB's own wording, every number after it is inflated and you won't find out until someone checks your method.*

- [ ] **Write the first 100 gold queries in colloquial Sindhi** — *Done when* each maps to a correct `answer_id` and each was written from the seed real-question set, not by reading the KB row. `[Risk 1]`
- [ ] **Build the first adversarial danger-sign set** — *Done when* 40 indirect phrasings exist that share no keyword with the bank but mean the same thing.
- [ ] **Reach 200 harvested real questions** — *Done when* all eight categories are represented and at least half come from outside your own social circle. `[Lever 2]`
- [ ] **Write `docs/sindhi_register_notes.md` from the harvest** — *Done when* every clinical term in the KB has 2–4 real colloquial equivalents recorded. `[Lever 2]`

#### Phase 2 — Complete the measurement instrument
*The negative set is the piece teams skip and then can't set a refusal threshold. Without it τ_low is guesswork and the system either refuses constantly or never.*

- [ ] **Expand the gold set to 300 queries** — *Done when* all eight categories are proportionally covered and a second person has spot-checked 30 mappings.
- [ ] **Build the 100-question negative set** — *Done when* 100 health-shaped questions with no correct KB answer exist and are confirmed to have none. `[Lever 5]`
- [ ] **Complete the danger set to 100 and out-of-scope set to 100** — *Done when* both are committed and Sabiha's gate has been run against them.
- [ ] **Write the eval harness** — *Done when* one command produces every metric in the definition-of-done table as a committed markdown report.

#### Phase 3 — Run the variant machine and make progress visible
*The phase you own most heavily and the one most likely to slip. Your job is as much coordination as engineering — the burn-down is what makes a stall visible before it becomes fatal.*

- [ ] **Tier the rows High/Medium/Low by expected query frequency** — *Done when* the split is 400/800/800 and the rationale is written down. `[Risk 5]`
- [ ] **Generate variants few-shot per category from the real-question seed** — *Done when* ~6,400 candidates exist, deduped by exact match and cosine > 0.95. `[Lever 2]`
- [ ] **Set up the review sheet and run the first session in pairs** — *Done when* all four have reviewed together for one hour and agreed what "fix" vs "drop" means. `[Risk 5]`
- [ ] **Publish the review burn-down automatically** — *Done when* CI writes per-person completion into `docs/status.md` on every push. `[Risk 5]`
- [ ] **Review your own two categories — Nutrition and Menopause** — *Done when* your rows show 100% in the burn-down.
- [ ] **Wire the eval harness into GitHub Actions** — *Done when* every PR comments with recall and safety numbers, and a drop in danger-sign recall fails the build.

#### Phase 4 — Clinical review and real users
*Where the project earns the word "vetted" — or honestly declines to use it. Both outcomes are acceptable; quietly claiming the first without the second is not.*

- [ ] **Get the high-risk packet reviewed and signed** — *Done when* a named reviewer with stated credentials has returned the packet and the sign-off is committed. `[Risk 4]`
- [ ] **Apply reviewer edits and set tiers across the corpus** — *Done when* every row has a final tier and counts are in `docs/status.md`. `[Risk 4]`
- [ ] **Run user testing sessions and log every question verbatim** — *Done when* 10–15 sessions are logged, with refused questions listed separately as the priority backlog.
- [ ] **Publish the pilot report** — *Done when* answer rate, refusal rate, escalation count and the list of what failed are written up in `docs/`.
- [ ] **If no reviewer has responded, trigger the fallback** — *Done when* all content is Tier B, the banner ships, and the report states plainly that clinical review was not obtained. `[Risk 4]`

#### Phase 5 — Build the speech assets
*One recording effort produces three things: the ASR test set, the answer audio bank that removes your TTS dependency, and a donated-speech dataset publishable on its own.*

- [ ] **Record native speakers reading the 300 gold queries aloud** — *Done when* 300 clips from ≥4 speakers exist with consent recorded and no identifying details stored.
- [ ] **Record the 300 highest-frequency answers as the audio bank** — *Done when* clips are in Supabase storage keyed by `answer_id` and Sabiha can serve them. `[Risk 6]`
- [ ] **Evaluate ASR on the recordings and report WER by speaker** — *Done when* WER is broken down by speaker and dialect, not a single averaged number that hides who the system fails.

---

## 4. Working rhythm

**Label every issue with its lever or risk.** Create GitHub labels `lever-1`…`lever-5` and `risk-1`…`risk-7` and apply them when opening the issue. Filtering by `risk-5` then shows instantly whether anyone is working on the thing most likely to sink the project. Labels turn this document from a plan into something queryable.

**The 30-minute weekly sync.** Same time each week, three items only: what moved, what's blocked, one look at the burn-down and the latest eval numbers. Anything blocked >48h becomes a pairing session in the same meeting.

**Update `docs/status.md` when reality changes.** Current phase, what each person is on, what's blocked, latest eval numbers, review burn-down. Not a weekly ritual — updated when something changes, so it's trustworthy enough to read instead of asking.

**Write the ADR while you still remember the reasoning.** Every time you choose between two real options, that's a short file in `docs/adr/`: what you chose, what you rejected, why. Four months from now, writing the report, you won't remember why bge-m3 beat e5 — and reconstructing it costs far more than the ten minutes it costs now.
