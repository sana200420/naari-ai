# NaariAI — Incident Runbook
**Owner:** Sabiha  
**Last updated:** September 2026  
**Purpose:** Any team member can restore service using only this document.

---

## Service URLs

| Service | URL |
|---|---|
| API (production) | https://naari-ai-production.up.railway.app |
| Health check | https://naari-ai-production.up.railway.app/health |
| Railway dashboard | https://railway.app/dashboard |
| Supabase logs | https://supabase.com/dashboard/project/nyvqcvqqbxwwzenuukpx |
| GitHub repo | https://github.com/sana200420/naari-ai |

---

## Quick health check

Open in browser:
```
https://naari-ai-production.up.railway.app/health
```
Expected response:
```json
{"status": "ok", "service": "naari-ai"}
```

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
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Supabase service key |
| `GEMINI_API_KEY` | Gemini 2.5 Flash key |
| `GROQ_API_KEY` | Groq fallback key |
| `TAU_HIGH` | High confidence threshold (default 0.75) |
| `TAU_LOW` | Low confidence threshold (default 0.40) |
| `DEMO_MODE` | Set `true` to force verbatim-only |

---

## Demo day checklist

- [ ] Run health check — expect 200
- [ ] Run keep_warm.py 30 min before demo
- [ ] Test `/ask` with a danger phrase — expect escalation response
- [ ] Test `/ask` with a normal question — expect answer
- [ ] Check Railway logs — no errors
- [ ] DEMO_MODE ready to flip if needed
