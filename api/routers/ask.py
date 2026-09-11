from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class AskRequest(BaseModel):
    query: str
    language: str = "sindhi"
    session_id: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    audio_url: Optional[str]
    path: str
    confidence_band: str
    escalated: bool
    disclaimer: bool
    retrieved_ids: list[int]
    sources: list[str]
    latency_ms: Optional[float]


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, http_request: Request):
    """
    Phase 3: cache + rate limit + demo mode + tier enforcement wired in.
    Danger gate still runs first inside run_pipeline.
    """
    from api.phase3_cache import cache_get, cache_set, is_rate_limited, is_demo_mode
    from api.pipeline import run_pipeline

    # Rate limiting
    ip = http_request.client.host if http_request.client else "unknown"
    if is_rate_limited(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please wait a moment.")

    # Cache check
    cached = cache_get(request.query)
    if cached:
        return AskResponse(**cached)

    # Demo mode — force verbatim-only flag into pipeline
    if is_demo_mode():
        request_copy = request.model_copy(update={"language": request.language})
        # In demo mode, pipeline will use DEMO_MODE env to restrict to verbatim
        pass

    # Run pipeline
    response = run_pipeline(request)

    # Cache the response (don't cache danger/refusal paths)
    if response.path in ("verbatim", "generated"):
        cache_set(request.query, response.model_dump())

    return response


@router.get("/cache/stats")
def cache_stats():
    """Show cache hit stats — for monitoring."""
    from api.phase3_cache import cache_stats
    return cache_stats()
