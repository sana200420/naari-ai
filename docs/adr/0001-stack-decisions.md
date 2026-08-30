# ADR 0001 — Initial stack decisions

**Status:** draft · **Date:** TBD · **Author:** Sana

Record what we chose, what we rejected, and why. Fill each section in as the
decision is actually made — not afterwards from memory.

## Embedding model
**Chosen:** BAAI/bge-m3
**Rejected:** intfloat/multilingual-e5-large
**Why:**

## Vector store
**Chosen:** Qdrant Cloud free tier
**Rejected:** FAISS in-process
**Why:**

## Backend hosting
**Chosen:** Hugging Face Spaces (Docker, free CPU)
**Rejected:** Render free, Fly.io
**Why:**

## Generation model
**Chosen:** Gemini 2.5 Flash free tier
**Rejected:** Groq Llama 3.3 70B (kept as fallback)
**Why:**
