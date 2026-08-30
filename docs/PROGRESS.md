# Naari AI — Progress Log

**Last updated:** 30 August 2026
**Repo:** https://github.com/sana200420/naari-ai (public)
**Current phase:** Phase 0 — Foundations
**Team:** Sana · Sabiha · Tooba · Mahnoor — SZABIST

A running record of what has actually been done, what was decided and why, and
what is next. Update this when something meaningful lands, not on a schedule.
Doubles as raw material for the FYP report and for supervisor updates.

---

## 1. What the project is

A Sindhi-first women's health assistant for rural Sindh. A woman asks a health
question in Sindhi; the system retrieves an answer from a vetted, source-cited
knowledge base rather than generating medical content freely with a language model.

Text-based web app now. Voice (Sindhi speech in, speech out) in prototype 2.

The purpose is health literacy: giving women access to accurate reproductive and
maternal health information without needing to reach a human first, in a region
where that access is limited.

---

## 2. Completed

### 2.1 Knowledge base — 2,000 vetted Q&A pairs

The core asset of the project, and the part that distinguishes it from a general
chatbot. Built across the team, 500 pairs each, split into eight subtopics:

| Member | Categories | Rows |
|---|---|---:|
| Sana | Pregnancy & Maternal Health · PCOS & Hormonal Health | 500 |
| Tooba | Fertility & Reproductive Health · Vaginal & Personal Hygiene | 500 |
| Sabiha | Menstrual Health & Periods · Mental Health & Emotional Well-being | 500 |
| Mahnoor | Women's Nutrition & Wellness · Menopause & Menopausal Health | 500 |
| | **Total** | **2,000** |

Schema is six columns: `id, category, sub_category, question, answer, source`.

**Update, 30 Aug 2026 (later same day):** the merged file had two real bugs found
during the Lever 1 work below — a structural one (24 columns instead of 6, from a
bad merge) and a content one (317 exact-duplicate rows, later independently fixed
by the team, plus one row with a genuinely blank question field). Both are now
fixed: the file is a clean 2,000 rows × 6 columns, `id` 1–2000, 250 rows per
category, zero duplicate questions, zero blank fields. The one gap this left (249
rows in Menstrual Health & Periods) was backfilled with a new, sourced question in
the same sub-category rather than left short.

**Sourcing discipline.** Every citation is a document that was actually retrieved
and read during the build — no URL written from memory, no citation inferred.
Primary sources are WHO fact sheets and guidelines (antenatal care, postnatal care,
maternal mortality, pre-eclampsia, anaemia, menstrual health, preterm birth, infant
feeding), the 2023 International Evidence-based PCOS Guideline, and ATA thyroid
guidance.

**Safety constraints applied at authoring time.** No medicine is named, no dose is
given, no diagnosis is made in any answer. Danger-sign rows escalate rather than
explain. Answers are 22–50 words, written short and plain so they translate
faithfully into Sindhi and read well aloud.

**Automated checks that passed on the English set:** no empty cells, no duplicate
IDs, no duplicate questions across the whole set, every source resolving to the
verified registry, no medicine names or doses anywhere.

Files:
- `knowledge_base/Womens_Health_KB - 2000_final.csv` — merged corpus, 2,000 rows
- `knowledge_base/naariai_faq_english_v1.csv` — Sana's 500, English
- `knowledge_base/naariai_faq_sindhi_v1.csv` — Sana's 500, Sindhi
- `knowledge_base/kb_category_boundaries.md` — subtopic scope definitions
- `knowledge_base/REVIEW_NOTES.md` — build notes and reviewer priorities

### 2.2 Safety layer, specified

`assets/kb_safety_always_on.md` defines eleven danger-sign categories in Sindhi,
Roman Sindhi and English, with a fixed escalation script and hard limits: never
diagnose, never name a medicine, never say a symptom is nothing to worry about,
never ask for identifying details, and refuse out-of-scope topics (abortion, named
contraceptives, domestic violence) with a referral rather than improvising.

The architectural decision that follows from this: safety runs **before** retrieval,
so escalation can never depend on a vector search succeeding.

### 2.3 Earlier prototype work

A working agent was demonstrated on ElevenLabs with a 15-topic Sindhi knowledge
base, including RAG configuration tuned for Sindhi (`assets/ELEVENLABS_RAG_SETUP.md`).
This proved the concept and produced the retrieval findings that shaped the current
architecture — particularly that real questions look nothing like FAQ questions,
which became Lever 2 in the current plan.

Also produced: pitch deck (multiple iterations), NIC Karachi application materials,
and a gap analysis of existing phone health services in Sindh.

### 2.4 Architecture and planning, decided

Three planning documents now exist in `docs/`:

- **`ROADMAP.md`** — the full stack, the request pipeline, four workstreams, six
  phases with measurable exit gates, and the definition of done.
- **`PLAYBOOKS.md`** — how each retrieval lever is actually executed, a risk register
  with owners and contingencies, and per-person per-phase checklists with acceptance
  criteria.
- **`GIT_GUIDE.md`** and **`SETUP.md`** — how the team works, written for four people
  new to Git.

### 2.5 Lever 1 — Script normalisation, done (30 Aug 2026)

The first Phase 1 task, started ahead of the formal phase transition since the
corpus was ready. Full writeup in `docs/adr/0002-normalisation-map.md`.

- Codepoint frequency histogram over all 2,000 rows: **145 distinct codepoints**,
  every one classified keep/map/drop with a reason (script:
  `retrieval/scripts/build_normalisation_table.py`)
- `retrieval/normalize.py` — `normalize_sd()`, the fixed 7-step pipeline (NFC →
  strip zero-width → strip tatweel → remove harakat → character map → digit
  folding → collapse whitespace)
- `retrieval/embed.py` — `embed_text()`, the only public embedding entry point;
  normalises unconditionally before anything else (model loading itself is the
  next task, not done yet)
- `retrieval/tests/` — **52 tests, all passing**: idempotence over all 4,000
  question+answer strings, 47 golden fixtures (including a genuine transcription
  bug in my own first draft, caught by actually running the tests rather than
  assuming), non-destruction (0 collisions), embed-gating check
- CI now runs `pytest retrieval/` on every PR instead of being commented out
- **Open:** the ADR's "worked if" clause (Recall@5 with/without normalisation)
  can't be measured yet — no embeddings, no gold queries. Tracked as the
  remaining line item on ADR 0002.

### 2.6 Repository, live

- Created at github.com/sana200420/naari-ai, public
- Folder skeleton matching the four workstreams: `retrieval/` `api/` `web/` `data/`
  `eval/` `scripts/` `docs/`
- `README.md`, `.gitignore`, `.env.example`, `.gitattributes`, CI workflow stub
- `main` protected: no direct pushes, pull request plus one approval required
- Git installed and configured on Sana's machine
- **PR #1 open** — awaiting review from Sabiha. Deliberately a low-stakes change,
  used to verify branch protection actually blocks an unreviewed merge.

---

## 3. Decisions made, and why

| Decision | Chosen | Reasoning |
|---|---|---|
| RAG ownership | Own retrieval pipeline, hosted LLM | Sindhi retrieval quality has to be tunable and measurable; a managed platform is a black box and produces no reportable metrics |
| Budget | Free tiers only | Embedding and reranking run as local models inside our own container, so retrieval costs nothing; only generation touches an external API, and only on a minority of requests |
| Embedding model | `BAAI/bge-m3` | XLM-R backbone covers Sindhi; returns dense and lexical-sparse vectors from one forward pass, so hybrid search costs one model, not two |
| Vector store | Qdrant Cloud free tier | Native named dense + sparse vectors and server-side fusion; ~10k vectors uses about 2% of the tier |
| Backend hosting | Hugging Face Spaces, free CPU | The only free tier with enough RAM to hold a 568M embedding model resident |
| Generation | Gemini 2.5 Flash free tier | Best free-tier Sindhi comprehension, with Groq as automatic fallback |
| Generation policy | Extractive-first | On high-confidence retrieval the LLM is bypassed entirely and the vetted Sindhi answer is returned verbatim. Free-tier models read Sindhi far better than they write it, and a fluent wrong answer about pregnancy is the worst outcome available to this project |
| Delivery | Mobile-first web app (PWA) | Works on cheap Android without a Play Store listing; mobile apps later |
| Repo visibility | Public | Branch protection is not available on private repos on a free GitHub account, and branch protection is what keeps `main` working |

---

## 4. The technical approach, in short

Five levers address the fact that standard RAG assumes English and fails quietly
on Sindhi:

1. **Script normalisation** — one function applied identically at index and query
   time, with the character map derived from our own corpus rather than copied from
   an Urdu map that would destroy Sindhi-specific letters.
2. **Colloquial question variants** — real women don't use FAQ phrasing. Harvest
   250–300 real questions from lady health workers and families, use them as
   few-shot examples to generate variants, review by hand. Largest expected gain.
3. **Hybrid dense + sparse retrieval** with Reciprocal Rank Fusion.
4. **Cross-lingual dual index** — we hold 2,000 aligned English/Sindhi pairs, so an
   English query path can rescue rows the Sindhi embeddings miss.
5. **A confidence gate** — above a threshold, return the vetted answer verbatim;
   in the middle band, let the LLM stitch retrieved answers under strict constraints;
   below, refuse and refer to a lady health worker.

Full detail in `PLAYBOOKS.md`.

---

## 5. Current state — Phase 0

| Task | Owner | Status |
|---|---|---|
| Repo, skeleton, README, .gitignore, .env.example | Sana | Done |
| `main` protected, 1 approval required | Sana | Done |
| Collaborators added | Sana | Invitations sent |
| First PR opened and reviewed | All | PR #1 open, awaiting approval |
| Interface contracts in `docs/contracts/` | Sana | Not started |
| `FakeRetriever` stub | Sana | Not started |
| Lever 1 — script normalisation (`retrieval/normalize.py` + tests + ADR 0002) | Sana | **Done** — see 2.5 above |
| Corpus merged and schema-validated | Mahnoor | Merged file cleaned to 2,000×6, `id` 1–2000, zero duplicates/blanks (fixed 30 Aug during Lever 1 work); formal validation script still pending |
| `build.py` so corpus is generated not hand-edited | Mahnoor | Not started |
| Clinical reviewer outreach | Mahnoor | **Not started — highest lead time, start now** |
| 150-row high-risk review packet | Mahnoor | Not started |
| Real-question harvesting begun | Mahnoor | Not started |
| FastAPI skeleton + first deploy | Sabiha | Not started |
| Next.js skeleton + Sindhi font audit | Tooba | Not started |
| Agree shared Sindhi clinical terminology | All | Not started |

**Phase 0 exit gate:** two empty deployed apps at public URLs, one merged corpus of
2,000 validated rows, and every member having opened and merged one pull request.

---

## 6. Live risks

| Risk | Status | Note |
|---|---|---|
| No clinical reviewer identified | **Open, urgent** | Longest lead time of anything in the project. Outreach must start in Phase 0, not Phase 4 as originally planned. Fallback is a tiered corpus with visible disclosure on unreviewed content |
| Sindhi embeddings may be too weak | Unknown until Phase 1 | Escape hatch is fine-tuning bge-m3 on our own 2,000 pairs on Colab's free T4. Would be a stronger contribution than using an off-the-shelf model |
| Variant review may stall | Not yet started | Tiered to ~6,400 variants instead of 10,000, with a public burn-down |
| No usable free Sindhi TTS | Deferred to Phase 5 | Mitigation: record a native speaker reading the 300 most common answers rather than synthesising them |
| One person becoming a bottleneck | Being mitigated | Contracts and mocks first, so nobody waits on retrieval |

---

## 7. Immediate next steps

**Sana** — Lever 1 is done. Still open from Phase 0: write the interface contracts
in `docs/contracts/`, ship `FakeRetriever`, open ADR 0001 recording the stack
decisions above. Next Lever 1 task specifically: embed all 2,000 Sindhi + 2,000
English rows and stand up the Qdrant collection — blocked on a Qdrant Cloud
account and, for the dense baseline, Mahnoor's first 100 gold queries.

**Sabiha** — accept the invite, approve PR #1, then FastAPI skeleton with `/health`
and a first deploy to Hugging Face Spaces. Deploy on day one, not at the end.

**Tooba** — accept the invite, Next.js skeleton with RTL layout, and verify Sindhi
characters render correctly on a real budget Android phone before building anything
on top.

**Mahnoor** — accept the invite, send the first three clinical reviewer approaches,
assemble the 150-row high-risk packet, and begin harvesting real questions.

**All four** — read `docs/GIT_GUIDE.md`, agree the Sindhi rendering of the shared
clinical terms flagged in `REVIEW_NOTES.md`.
