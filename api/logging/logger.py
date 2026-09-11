"""
Structured logging into Supabase — Phase 2
Logs every request: query, retrieved IDs, scores, band, path, latency, provider.
Falls back to local logging if Supabase is unavailable.
"""
import os
import logging
from typing import List, Optional

logger = logging.getLogger("naari.logger")
_client = None


def _get_client():
    """Get Supabase client — lazy init, cached."""
    global _client
    if _client is not None:
        return _client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        _client = create_client(url, key)
    except Exception as e:
        logger.warning(f"Supabase init failed: {e}")
        _client = None
    return _client


def log_query(
    query: str,
    retrieved_ids: List[int],
    scores: List[float],
    band: str,
    path: str,
    latency_ms: float,
    provider: str,
    session_id: Optional[str] = None,
) -> None:
    """
    Log a query to Supabase query_logs table.
    Never raises — logging must not break the API.
    """
    row = {
        "query": query[:500],  # cap length
        "band": band,
        "path": path,
        "latency_ms": round(latency_ms, 2),
        "provider": provider,
        "session_id": session_id,
        "retrieved_ids": retrieved_ids,
    }

    client = _get_client()
    if client is None:
        # Fallback: local log only
        logger.info(f"[no-supabase] {path} | {band} | {provider} | {latency_ms}ms | q={query[:60]}")
        return

    try:
        client.table("query_logs").insert(row).execute()
        logger.debug(f"Logged to Supabase: {path} | {band} | {provider}")
    except Exception as e:
        logger.warning(f"Supabase log failed: {e} — row={row}")
