# Naari AI — نارِي اي آءِ

A Sindhi-first women's health assistant for rural Sindh. Answers come from a
2,000-pair knowledge base built from WHO and clinical-guideline sources, retrieved
with RAG — not generated freely by a language model.

Text-based now. Voice in prototype 2.

**Team:** Sana · Sabiha · Tooba · Mahnoor — SZABIST
**Status:** Phase 0 — Foundations. See [docs/status.md](docs/status.md).
---

## What's in here

| Folder | Owner | What it is |
|---|---|---|
| `retrieval/` | Sana | Normalisation, embedding, indexing, hybrid search, reranking |
| `api/` | Sabiha | FastAPI service, safety gates, LLM orchestration |
| `web/` | Tooba | Next.js Sindhi RTL web app |
| `data/` | Mahnoor | The corpus, question variants, evaluation sets |
| `eval/` | Mahnoor | Evaluation harness and committed results |
| `docs/` | all | Decisions, contracts, status |

**Stay in your own folder.** If you need something changed in someone else's,
ask them. This is what keeps merge conflicts rare.

## Getting started

New to the repo? Read `docs/SETUP.md` to install Git and clone, then
`docs/GIT_GUIDE.md` for how we actually work day to day — branches, pull
requests, who approves what, and how to fix things when they break.

Planning docs: `docs/ROADMAP.md` (what gets built) and `docs/PLAYBOOKS.md`
(how, who, and what to do when things go wrong).

## Rules

1. Never commit to `main` — branch, then open a pull request.
2. Branch names: `yourname/what-it-does`
3. Never commit `.env` or any API key. If you do, rotate the key.
4. Commit messages: `folder: what changed`
