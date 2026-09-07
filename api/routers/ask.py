from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# ── Request shape ──────────────────────────────────────────────
class AskRequest(BaseModel):
    query: str
    language: str = "sindhi"
    session_id: Optional[str] = None

# ── Response shape ─────────────────────────────────────────────
class AskResponse(BaseModel):
    answer: str
    audio_url: Optional[str]
    path: str                    # "danger" | "verbatim" | "generated" | "referral" | "refusal"
    confidence_band: str         # "high" | "mid" | "low"
    escalated: bool
    disclaimer: bool
    retrieved_ids: list[int]
    latency_ms: Optional[float]


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Phase 2: real pipeline wired in.
    Danger gate runs first — always.
    """
    from api.pipeline import run_pipeline
    return run_pipeline(request)
