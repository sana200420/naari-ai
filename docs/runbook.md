# NaariAI — Incident Runbook
**Owner:** Sabiha  
**Last updated:** September 2026  
**Purpose:** Any team member can restore service using only this document.

---

## Service URLs

| Service | URL |
|---|---|
| Backend (production) | https://huggingface.co/spaces/Sanapalijo/naari-ai |
| Backend direct / API | https://sanapalijo-naari-ai.hf.space |
| Space dashboard | https://huggingface.co/spaces/Sanapalijo/naari-ai/settings |
| Railway (retired) | https://naari-ai-production.up.railway.app — served a Phase 0 mock from 2026-08-30; see ADR 0001 amendment |
| Supabase logs | https://supabase.com/dashboard/project/nyvqcvqqbxwwzenuukpx |
| GitHub repo | https://github.com/sana200420/naari-ai |

---

## Quick health check

Open https://sanapalijo-naari-ai.hf.space in a browser — the Sindhi chat UI
should load. Ask "حيض جي چڪر ڇا آهي؟" and expect a real answer, not the
refusal string.

To check the API the frontend actually calls:

```bash
python -c "
from gradio_client import Client
print(Client('Sanapalijo/naari-ai').predict(
    query='حيض جي چڪر ڇا آهي؟', language='sindhi', api_name='/ask'))"
```

Returns a JSON string with `answer`, `path`, `confidence_band`,
`retrieved_ids` and `latency_ms`.

**Deploying:** the Space is a git remote. From the repo:
`git push space <branch>:main`. Build and run logs:
`hf spaces logs Sanapalijo/naari-ai [--build]`.

**Cold start:** the models are ~7GB and download on boot, so a restarted Space
takes several minutes before the first answer. Warmup runs in a background
thread, so the UI loads before the models are ready.

**Secrets** live in Space Settings → Variables and secrets, not in `.env`.

---

## Incident 1 — Service returning 404 or 500

**Steps:**
1. Go to Railway dashboard → naari-ai → **Deployments** tab
2. Check latest deployment status — is it **Active** or **Failed**?
3. Click **View logs** — look for Python errors
4. If crash: check if a new commit broke something → revert with:
```bash
git revert HEAD
git push origin main
```

---

## Incident 2 — Cold start (40 second delay)

**Cause:** Railway free tier sleeps after inactivity.

**Fix:**
- Run `keep_warm.py` before demo:
```bash
python3 keep_warm.py
```
- Or ping manually every 10 minutes:
```bash
curl https://naari-ai-production.up.railway.app/health
```

---

## Incident 3 — 429 Rate limit errors

**Cause:** Too many requests per minute (limit: 60/min per IP).

**Fix:**
- Enable demo mode (verbatim-only, more stable):
  - Go to Railway → Variables → set `DEMO_MODE=true`
  - Redeploy not needed — env var is read at runtime

---

## Incident 4 — Gemini API failing

**Cause:** Gemini rate limit or key expired.

**Fix:**
- Pipeline auto-falls back to Groq → static response
- No action needed unless both fail
- If both fail: set `DEMO_MODE=true` in Railway variables

---

## Incident 5 — Supabase logs not appearing

**Cause:** Supabase credentials missing or wrong.

**Check:**
- Railway → Variables → confirm `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY` exist
- Supabase dashboard → Table Editor → `query_logs` table

**Fix:**
- Re-add variables from Supabase Settings → API Keys

---

## Environment variables (Railway)

| Variable | What it does |
|---|---|
| `QDRANT_URL` | Qdrant Cloud endpoint — **required**, retrieval raises `KeyError` without it |
| `QDRANT_API_KEY` | Qdrant Cloud key — **required**, same |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Supabase service key |
| `GEMINI_API_KEY` | Gemini 2.5 Flash key |
| `GROQ_API_KEY` | Groq fallback key |
| `TAU_HIGH` | High confidence threshold (default 0.75) — see warning below |
| `TAU_LOW` | Low confidence threshold (default 0.2034) |
| `DEMO_MODE` | Set `true` to force verbatim-only |

> **`TAU_HIGH` is read by two different modules with two different meanings:**
> `api/pipeline.py` uses it as the verbatim band threshold, while
> `retrieval/pipeline.py` uses it as the Lever 4 cascade gate (skip English
> translation if the Sindhi score already clears it). Setting it here changes
> both at once. Setting it to `0.0` to disable the English leg would also send
> every query down the verbatim path. Don't set it until these are split.

> **`TAU_LOW = 0.2034`** is calibrated against `eval/negative_set_100.csv`
> (90/100 out-of-scope queries fall below it). The previous `0.40` was a
> placeholder and refused a large share of *correct* answers.

---

## Demo day checklist

- [ ] Run health check — expect 200
- [ ] Run keep_warm.py 30 min before demo
- [ ] Test `/ask` with a danger phrase — expect escalation response
- [ ] Test `/ask` with a normal question — expect answer
- [ ] Check Railway logs — no errors
- [ ] DEMO_MODE ready to flip if needed
