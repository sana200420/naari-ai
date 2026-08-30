# Naari AI — Build Roadmap v1

Sindhi-first women's health RAG assistant. Text now, voice in prototype 2.

**Given constraints:** own retrieval + hosted LLM · free tier only ($0/mo) · web app first · four engineers, all coding.

---

## 1. The stack

| Layer | Choice | Why | Fallback |
|---|---|---|---|
| Web app | Next.js 15 App Router + Tailwind, RTL, PWA | Free static hosting; PWA installs on cheap Android without Play Store | Vite + React SPA |
| Web hosting | Vercel Hobby | Free, CDN, preview URL per PR | Netlify free |
| API | FastAPI, Python 3.11, Docker | Same language as retrieval; auto OpenAPI docs | — |
| API hosting | Hugging Face Spaces (Docker, free CPU 2vCPU/16GB) | Only free tier with RAM to hold a 568M embedding model resident | Render free, Fly.io |
| Embeddings | `BAAI/bge-m3` run locally | XLM-R backbone covers Sindhi; dense + lexical-sparse from one forward pass | `intfloat/multilingual-e5-large` |
| Reranker | `BAAI/bge-reranker-v2-m3`, ONNX int8 | Largest single precision gain on a low-resource language | Skip rerank, raise k |
| Vector store | Qdrant Cloud free (1GB) | Native named dense + sparse vectors, server-side fusion | FAISS + rank_bm25 in-process |
| Generation | Gemini 2.5 Flash free tier | Best free-tier Sindhi comprehension | Groq Llama 3.3 70B, OpenRouter |
| Feedback/logs | Supabase free Postgres | Feedback must survive container restarts | Neon free |
| CI | GitHub Actions | Runs eval on every PR — catches recall regressions | — |
| Voice (P2) | STT: MMS-1B-all / Whisper-small fine-tuned · TTS: Piper/VITS on donated Sindhi speech | No good off-the-shelf Sindhi TTS — research track | ElevenLabs multilingual |

**Cost stays $0 because embedding and reranking run as local models inside your own container.** The only external API call is generation, and generation only fires on a minority of requests.

⚠️ Convert both models to **ONNX int8** before first deploy and load them once at module level, not per request. If p95 latency still exceeds 3s, drop the reranker before anything else.

---

## 2. The Sindhi problem — five levers

These are the actual technical contribution. Build the FYP report around them.

**Lever 1 — Script normalisation, identical at index and query time.**
Unicode NFC; unify `ي/ی/ى`, `ه/ہ/ھ`, `ك/ک`; strip harakat and tatweel; normalise `۽`; Eastern Arabic digits → ASCII; collapse whitespace. One module, imported everywhere, unit tested. If index-time and query-time normalisation diverge by one character class, recall collapses silently and no error is raised.

**Lever 2 — Colloquial question variants (biggest single gain).**
A woman doesn't say "ماهواري جي عام مدت ڪيتري هوندي آهي؟" — she says "مهيني وارا ڏينهن دير سان اچن ٿا". Write 4–6 real phrasings per FAQ row, index each as its own vector pointing at the same `answer_id`. 2000 × 5 ≈ 10k vectors covering the phrasing space real users occupy. Draft with an LLM, then the category owner reads and fixes every one.

**Lever 3 — Hybrid dense + sparse with Reciprocal Rank Fusion.**
Dense vectors blur rare terms; low-resource languages are full of them. bge-m3 gives both from one pass. Fuse with RRF `1/(60+rank)` — no calibration needed, robust to the two scores living on different scales.

**Lever 4 — Cross-lingual dual index.**
You have 2000 aligned EN/SD pairs sharing an ID — a rare asset. Index both. Sindhi query goes to the Sindhi index; in parallel a translated query goes to the English index where embedding quality is much higher. Fuse by `answer_id`. English frequently rescues rows Sindhi embeddings miss.

**Lever 5 — Confidence gate, so the system can say it doesn't know.**
After reranking: ≥ τ_high → return the vetted Sindhi answer verbatim. τ_low–τ_high → LLM stitches 2–3 retrieved answers under a strict no-new-facts prompt. < τ_low → refuse and refer to a lady health worker. Thresholds tuned on the gold set, not guessed.

**Why generation is deliberately constrained:** free-tier LLMs read Sindhi far better than they write it, and a fluent wrong answer about pregnancy is the worst outcome this project can produce. On high-confidence hits the model is bypassed entirely. A post-filter blocks any output containing a medicine name, dose, diagnosis phrasing, or reassurance that a symptom is nothing.

---

## 3. Request pipeline

Safety runs *before* retrieval. A danger sign must never depend on a vector search succeeding.

```
00  Normalise                 shared normaliser; everything downstream sees normalised text
01  DANGER-SIGN GATE          keyword bank from kb_safety_always_on.md OR cosine similarity
    (short circuit)           to the 11 danger phrases → escalation script, log, STOP
02  Scope check               abortion / named contraceptives / DV / non-health → referral
03  Retrieve (4 lists)        Sindhi dense · Sindhi sparse · English dense · variant index (top 25 each)
04  Fuse & dedupe             RRF by answer_id → top 20 unique rows
05  Rerank                    cross-encoder over (query, Sindhi question) → top 5 + scores
06  CONFIDENCE GATE           ≥τ_high verbatim · τ_low–τ_high constrained LLM · <τ_low refuse
07  Output filter             medicine names, doses, diagnosis phrasing, "nothing to worry about"
08  Respond + log             answer + source URLs; log query, IDs, scores, path, latency, rating
```

Every response carries its source URL. That is what separates Naari AI from a general chatbot — put it on screen and in the demo.

---

## 4. Who owns what

Four vertical slices, each with real depth, each demonstrable alone. The split maps one-to-one onto top-level folders, which is what keeps four Git beginners out of merge conflicts.

### Sana — Retrieval core (`/retrieval`)
- The normaliser, its tests, and enforcing its use everywhere
- Chunking & indexing; Qdrant schema with named dense + sparse vectors
- bge-m3 embedding service; ONNX int8 conversion of both models
- Hybrid search + RRF + cross-lingual dual index
- Cross-encoder reranking and threshold tuning against the gold set
- Retrieval API contract Sabiha's service consumes
- Architecture decisions, recorded as ADRs in `/docs`

**Ships:** a `search(query) → ranked rows + scores` module with a measured Recall@5, callable from a notebook before any web app exists.

### Sabiha — Backend, orchestration & safety (`/api`)
- FastAPI service, Docker image, HF Spaces deploy, secrets handling
- The full section-3 pipeline wired end to end
- Danger-sign gate and scope classifier — highest-stakes code in the project
- Gemini integration, prompt design, retries, Groq fallback
- Output filter blocklists; refusal and escalation templates
- Sessions, rate limiting, structured logging into Supabase
- Owns the OpenAPI contract Tooba builds against

**Ships:** `POST /ask` returning answer, source URLs, path taken and latency — testable with curl before any UI exists.

### Tooba — Web app & product (`/web`)
- Next.js RTL Sindhi chat UI; font selection and legibility at small sizes
- Low-literacy design: large tap targets, category shortcut cards, minimal typing
- Streaming responses, loading/error states, offline PWA shell
- Source citation display — visible, not buried in a tooltip
- Thumbs up/down capture → Supabase → Mahnoor's eval loop
- A microphone-shaped hole in the UI, stubbed for P2
- Vercel deployment, preview URLs, basic analytics

**Ships:** a public URL a woman with a Rs.15,000 Android phone can use one-handed on 3G.

### Mahnoor — Data, evaluation & QA (`/data`, `/eval`)
- Merge four members' CSVs into one schema-validated corpus; dedupe; source registry
- Own the build script so the corpus is generated, never hand-edited
- The 10k colloquial variant set — generate, route to category owners for review
- Gold eval set: 300 colloquial Sindhi queries mapped to correct answer IDs
- Adversarial sets: 100 danger-sign phrasings, 100 out-of-scope questions
- Eval harness in CI on every PR; results committed as markdown
- Clinical reviewer coordination and Sindhi user testing

**Ships:** the numbers the FYP is graded on, and the regression suite that stops anyone breaking them.

### Shared, non-negotiable
Variant review for your own two categories is yours: Sana → Pregnancy/Maternal + PCOS · Tooba → Fertility + Hygiene · Sabiha → Menstrual + Mental Health · Mahnoor → Nutrition + Menopause. Nobody merges to `main` without one teammate's approval. Everybody writes tests for their own folder.

---

## 5. Phases and their gates

No dates. A phase ends on a stated condition, written into `docs/status.md`, not because it feels finished.

### Phase 0 — Foundations
*Get four people committing to one repo without stepping on each other; get the corpus into one canonical file.*

- **Sana** — repo + folder skeleton, README, `.gitignore`, `.env.example`, add three collaborators, protect `main`
- **Mahnoor** — merge all four CSVs, enforce six-column schema, global dedupe across 2000 rows, verify every source URL resolves
- **Sabiha** — FastAPI skeleton with `/health`, Dockerfile, first Space deploy (deploy on day one, not at the end)
- **Tooba** — Next.js skeleton, RTL layout, Sindhi font verified on a real Android phone, deployed to Vercel
- **All** — agree the Sindhi rendering of the shared clinical terms flagged in `REVIEW_NOTES.md`, once, for all eight categories

**Exit gate:** two empty deployed apps at public URLs, one merged corpus of 2000 validated rows, every member has opened and merged one PR.

### Phase 1 — The retrieval spike
*Prove Sindhi retrieval works before building on top of it. This phase can fail; finding out now is cheap.*

- **Sana** — normaliser + tests; embed all 2000 Sindhi and English rows; Qdrant collection; dense-only baseline
- **Mahnoor** — first 100 gold queries in colloquial Sindhi, mapped to answer IDs
- **Sana** — add sparse + RRF, then English dual path, then reranking. Measure Recall@5 after *each* addition so you can report each lever's contribution
- **Sabiha** — danger-sign gate as a standalone tested module, independent of retrieval
- **Tooba** — chat UI against a mocked API; category shortcut cards; citation display

**Exit gate:** Recall@5 ≥ 0.85 on the 100-query set, with a table showing what each lever added. Below 0.70 after reranking → stop and reconsider the embedding model.

### Phase 2 — The vertical slice
*One question typed in Sindhi on a phone browser produces a correct, cited answer from the deployed stack.*

- **Sabiha** — wire the full pipeline; Gemini; confidence gate; refusal/escalation templates; `POST /ask` live
- **Sana** — package retrieval as an importable module with warm model loading; tune τ_high and τ_low
- **Tooba** — connect UI to the real API; streaming; error states; deploy
- **Mahnoor** — gold set to 300 queries; adversarial danger-sign and out-of-scope sets; first full eval run

**Exit gate:** all five test questions from `assets/ELEVENLABS_RAG_SETUP.md` pass on the deployed URL, including Q4 escalating rather than answering.

### Phase 3 — Variants and hardening
*Close the gap between FAQ phrasing and how women actually speak; make the safety layer provably hard to get past.*

- **Mahnoor** — generate 4–6 variants per row (~10k), build the review queue, merge reviewed variants, reindex
- **All** — review variants for your own two categories, ~2500 short lines each
- **Sana** — variant index into fusion; retune thresholds; ONNX int8; latency work
- **Sabiha** — output filter blocklists; rate limiting; Supabase logging; provider fallback; structured errors
- **Tooba** — feedback capture; PWA offline shell; accessibility pass; low-bandwidth testing
- **Mahnoor** — eval harness into GitHub Actions; every PR now reports recall and safety numbers

**Exit gate:** all section-7 targets met, with danger-sign recall at exactly 1.00. Any miss blocks the phase outright.

### Phase 4 — Clinical review and pilot
*The step that makes this a health product rather than a demo.*

- **Mahnoor** — get a doctor or LHW supervisor through the reviewer checklist; prioritise the thyroid rows (411–432) and the danger-sign cluster flagged in `REVIEW_NOTES.md`
- **All** — test with 10–15 Sindhi-speaking women; record every question verbatim, especially refused ones
- **Sana** — feed real unanswered questions back as new variants or KB rows; measure the recall lift
- **Tooba** — fix what the sessions expose (usually onboarding and font size, not the model)
- **Sabiha** — uptime monitoring, cold-start mitigation, incident runbook

**Exit gate:** reviewer sign-off recorded in the repo, and a real-user session log with a measured answer rate and a written list of what failed.

### Phase 5 — Voice (prototype 2)
*Only start once text is stable. Sindhi speech is a research problem; attaching it to unstable retrieval means you can't tell which half is broken.*

- **Sana** — Sindhi ASR evaluation: MMS-1B-all vs Whisper-small fine-tuned on Common Voice Sindhi. Report WER honestly
- **Mahnoor** — collect a Sindhi speech set (team + volunteers reading the gold queries aloud) — doubles as the ASR test set
- **Sabiha** — audio endpoints; ASR-error tolerance in retrieval (the normaliser matters even more here)
- **Tooba** — push-to-talk UI, waveform feedback, audio playback, graceful text fallback
- **All** — TTS decision: train a Piper voice on donated Sindhi speech, or accept an imperfect multilingual voice for the demo

**Exit gate:** a woman speaks a question in Sindhi and hears a correct spoken answer, end to end, on a phone.

---

## 6. Git & GitHub for four beginners

Most Git pain in student teams comes from everyone editing the same files. The folder ownership above removes most of it structurally.

### Repository layout

```
naari-ai/
├── README.md              # what it is, how to run it locally
├── .gitignore             # .env, __pycache__, node_modules, *.onnx, .venv
├── .env.example           # key NAMES only, never key values
├── .github/workflows/     # CI: lint, tests, retrieval eval
├── data/                  # MAHNOOR
│   ├── raw/               #   four per-member source CSVs
│   ├── processed/         #   naariai_faq_v1.csv — the merged corpus
│   ├── variants/          #   colloquial question variants
│   └── eval/              #   gold_queries.csv, danger_set.csv, oos_set.csv
├── retrieval/             # SANA — normalise, embed, index, search, rerank
├── api/                   # SABIHA — FastAPI, safety, LLM, Dockerfile
├── web/                   # TOOBA — Next.js app
├── eval/                  # MAHNOOR — harness + committed results
└── docs/                  # ADRs, status.md, architecture notes
```

### The four rules

1. **Never commit to `main`.** Settings → Branches → Add rule → require a pull request, require 1 approval. Now Git enforces it and nobody has to remember.
2. **One branch per piece of work**, named `yourname/what-it-does` — `sana/script-normaliser`, `tooba/rtl-chat-ui`.
3. **Stay inside your own folder.** Need a change in someone else's folder? Ask them. This one habit prevents nearly every merge conflict.
4. **Never commit `.env`, API keys, or model weights.** Keys go in HF Spaces secrets and Vercel env vars. If a key does get committed, *rotate it* — deleting the commit is not enough.

### Your daily loop

```bash
# start of the day — get everyone else's merged work
git checkout main
git pull

# start a piece of work
git checkout -b sana/script-normaliser

# ... write code ...

git add .
git commit -m "retrieval: normalise ye and he variants, add tests"
git push -u origin sana/script-normaliser

# then open a Pull Request on github.com and request a review
```

Commit messages: `folder: what changed`. Present tense, one line. `api: add danger-sign gate before retrieval` is good; `updated stuff` is not — in six months that's the difference between a history you can read and one you can't.

### Pull requests

The PR description is where documentation actually happens. Write what changed and why, and paste the evidence — a test output, a recall number, a screenshot. Tag one teammate. They read it, comment, approve, and you click **Squash and merge** (keeps `main` one commit per piece of work rather than eleven "fix typo" commits).

Review each other's work honestly. A PR approved without being read is worse than no review — it creates a false record that someone checked.

### The three things that will go wrong

**Your branch is behind `main`:**
```bash
git checkout main
git pull
git checkout your-branch
git merge main       # fix any conflicts, then commit
```

**A merge conflict:** Git marks the file with `<<<<<<<`, `=======`, `>>>>>>>`. Open it, keep the correct version, delete all three markers, `git add` the file, `git commit`. Nothing is lost — the panic is worse than the problem. `git merge --abort` puts you back exactly where you were.

**You committed something you shouldn't have:**
```bash
# not yet pushed — undo the commit, keep the changes
git reset --soft HEAD~1

# already pushed — add a commit that reverses it
git revert <commit-hash>
```

Avoid `git push --force` on a shared branch. It rewrites history under your teammates and is the one command here that can genuinely lose someone's work.

### Two files that will save the project

- `docs/status.md` — current phase, what each person is on, what's blocked. Updated when it changes, read at every meeting.
- `docs/adr/` — one short markdown file per architectural decision: what you chose, what you rejected, why. "Why bge-m3 and not e5" is a paragraph now and a whole chapter of your report later.

---

## 7. Definition of done

"Production ready" is a number, not a feeling. Measured by Mahnoor's harness on every PR.

| Metric | Measured on | Target | Why |
|---|---|---|---|
| Recall@5 | 300 colloquial Sindhi gold queries | ≥ 0.90 | Correct answer is available to the reranker |
| Recall@1 | same | ≥ 0.70 | Verbatim path fires often enough to keep cost and latency low |
| **Danger-sign recall** | 100 adversarial phrasings | **1.00** | One miss = a woman told to wait when she should go to hospital |
| False-escalation rate | 300 normal queries | ≤ 0.05 | Over-escalation destroys trust and the assistant stops being used |
| Refusal correctness | 100 out-of-scope queries | ≥ 0.95 | Abortion, contraceptives, DV must route to a human |
| Faithfulness | 100 generated answers, human-scored | 1.00 | Zero facts not present in the retrieved rows |
| Citation presence | all non-refusal responses | 1.00 | The vetted-source claim is the product |
| p95 latency | warm service, text mode | ≤ 3.0s | Beyond this on 3G, people assume it's broken |

Commit each eval run into `eval/results/` with the commit hash. By the end you have a chart of recall improving over time — the most persuasive slide you can put in front of a jury.

---

## 8. Risks

| Risk | Signal | What you do |
|---|---|---|
| Sindhi embeddings too weak | Recall@5 < 0.70 after all five levers in Phase 1 | Lean harder on the English dual path and sparse matching; consider fine-tuning bge-m3 on your own 2000 pairs as contrastive data — a strong FYP contribution in itself |
| Free CPU inference too slow | p95 > 5s once models are warm | ONNX int8 first, then drop the reranker, then reduce candidate count. Keep the Space warm with a scheduled ping |
| Gemini rate-limits during a demo | 429s under load | Groq fallback + response caching on normalised query text. The verbatim path needs no LLM at all — that's your real insurance |
| Clinical reviewer never materialises | Phase 4 stalls with no sign-off | Ship with a visible unreviewed-content banner and a hard scope limit. Don't quietly present it as vetted |
| Variant review stalls at 10k lines | Phase 3 drags on | Review by priority, not ID order: danger-sign and pregnancy clusters first, myth-busting rows last |
| No usable Sindhi TTS | Phase 5 output unintelligible to real speakers | Ship voice input with text output as the honest prototype 2; treat TTS as a separate research track |
| One person becomes the bottleneck | Three people blocked on one folder | Mock the interface and keep moving. Every boundary in section 4 is a contract that can be stubbed |

**The one to watch:** the most likely way this underdelivers is not technical failure — it's Phase 3 variant review quietly never finishing, leaving retrieval tuned to FAQ phrasing no real woman uses. Put it on a visible tracker, split by category owner, treat it as seriously as code.
