"""
Phase 3 — Response cache + rate limiting + demo mode
Cache: normalised query -> AskResponse, 24h TTL (in-memory for free tier)
Rate limit: 60 requests/minute per IP
Demo mode: forces verbatim-only, toggled via env var
"""
import os
import time
import hashlib
from collections import defaultdict
from typing import Optional

# ── Demo mode ─────────────────────────────────────────────────
def is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"

# ── In-memory cache (24h TTL) ─────────────────────────────────
_cache: dict = {}
_CACHE_TTL = 60 * 60 * 24  # 24 hours


def _cache_key(query: str) -> str:
    # normalize_sd is the project's one normaliser -- retrieval embeds through
    # it, so a cache keyed on anything else could hand back the answer to a
    # different question.
    #
    # This used to import `normalise` from api.safety.danger_gate, which has
    # never existed in any version of that module. It went unnoticed because
    # nothing called cache_get: the Space serves Gradio, which bypassed
    # routers/ask.py entirely. Wiring the cache into the Gradio path turned a
    # dormant ImportError into a total /ask outage.
    from retrieval.normalize import normalize_sd

    return hashlib.sha256(normalize_sd(query).encode()).hexdigest()


def cache_get(query: str) -> Optional[dict]:
    key = _cache_key(query)
    if key not in _cache:
        return None
    entry = _cache[key]
    if time.time() - entry["ts"] > _CACHE_TTL:
        del _cache[key]
        return None
    return entry["response"]


def cache_set(query: str, response: dict) -> None:
    key = _cache_key(query)
    _cache[key] = {"response": response, "ts": time.time()}


def cache_stats() -> dict:
    now = time.time()
    valid = sum(1 for e in _cache.values() if now - e["ts"] <= _CACHE_TTL)
    return {"total": len(_cache), "valid": valid}


# ── Rate limiting (60 req/min per IP) ─────────────────────────
_rate_store: dict = defaultdict(list)
RATE_LIMIT = 60
RATE_WINDOW = 60  # seconds


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_WINDOW
    _rate_store[ip] = [t for t in _rate_store[ip] if t > window_start]
    if len(_rate_store[ip]) >= RATE_LIMIT:
        return True
    _rate_store[ip].append(now)
    return False
