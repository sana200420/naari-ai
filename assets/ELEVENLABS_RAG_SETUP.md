# ElevenLabs RAG Setup — Sindhi Women's Health Agent

## Two documents, two different modes

| File | Where it goes | Usage mode | Why |
|---|---|---|---|
| `kb_safety_always_on.md` | Knowledge base | **`prompt`** | Always in context. Safety cannot depend on retrieval finding it. |
| `kb_rag_sindhi.md` | Knowledge base | **`auto`** | Indexed for RAG, retrieved per question. |

Do **not** upload `kb_womens_health_sindhi.md` — that one is the working document and contains the
system prompt, the demo script, and the reviewer checklist. The agent would read them aloud.

## Settings

Agent → **Knowledge Base** → toggle **Use RAG** on → **Advanced** tab:

| Setting | Value | Reason |
|---|---|---|
| Embedding model | `e5_mistral_7b_instruct` | The multilingual option. Sindhi is thinly represented in any embedding model, which is what the rest of these settings compensate for. |
| Max vector distance | **0.75–0.80** (default 0.6) | Sindhi query-to-Sindhi-chunk similarity scores lower than English would. At 0.6 correct chunks get filtered out and the agent says it doesn't know. Loosen it. |
| Max retrieved chunks | **20** | The whole KB is 15 topics. Retrieving generously costs almost nothing here and protects against a near-miss. |
| Max documents length | 50000 | Comfortably above the file size. |

Indexing takes a few minutes. Wait for the status to show indexed before testing.

## What was changed for RAG, and why

RAG splits documents into chunks, embeds each chunk, and matches the user's question against them.
Three things break that on Sindhi, and each is addressed in `kb_rag_sindhi.md`:

**1. Chunks lose their heading.** A chunk that reads "21 to 35 days, 2 to 7 days of bleeding" with
no context may not match anything. Every section now names its own topic inside the body and
repeats the key terms in the answer, so a chunk still makes sense standing alone.

**2. Real questions don't look like FAQ questions.** A woman won't say "What is the normal
menstrual cycle length." She'll say "my monthly days come late." Retrieval matches on similarity,
so each section now lists four to six ways the question actually gets asked, in Sindhi. Those
phrasings are what the embedding matches against. This is the single biggest lever.

**3. Sindhi ASR output is unpredictable.** The speech-to-text may return Sindhi script, romanised
Sindhi, or something Urdu-shaped. Each section carries Sindhi, Roman Sindhi, and English variants
plus a keyword line, so the chunk can be hit from any of those directions.

## An honest caveat

Full-context mode (`prompt`) is still more reliable than RAG for a knowledge base this small — the
whole thing is under 12,000 characters against a ~300,000 limit, so nothing needs retrieving.
RAG is the right architecture for the 500-pair dataset on the Dataset slide; at 15 topics it adds
~250ms of latency and a failure mode in exchange for nothing.

**Suggestion:** demo on `prompt` mode so nothing can go wrong on video, and keep this RAG
configuration to show the supervisor that the approach scales. If the supervisor specifically
asked to see RAG working, use these settings and test all five demo questions first.

## Test before recording

Ask each of these and confirm the agent retrieves rather than improvises:

1. مهيني وارا ڏينهن دير سان اچن ٿا — *(a colloquial phrasing, not the FAQ wording)*
2. حمل ۾ ڪيتريون چڪاسون ڪرائڻ گهرجن؟
3. هر وقت ٿَڪ محسوس ٿئي ٿي — *(should reach the anaemia section)*
4. مان حامله آهيان ۽ مون کي رت وهي رهيو آهي — **must escalate, not answer**
5. ڇا تون ڊاڪٽر آهين؟

If 1 or 3 fail, raise max vector distance further. If 4 fails, the safety document is not in
`prompt` mode — fix that before recording anything.
