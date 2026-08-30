from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# ── Request shape ──────────────────────────────────────────────
class AskRequest(BaseModel):
    query: str                        # user's question (text or transcribed audio)
    language: str = "sindhi"          # "sindhi" | "english"
    session_id: Optional[str] = None  # optional, for logging

# ── Response shape ─────────────────────────────────────────────
class AskResponse(BaseModel):
    answer: str                  # text answer
    audio_url: Optional[str]     # pre-recorded audio if verbatim path
    path: str                    # "danger" | "verbatim" | "generated" | "referral"
    confidence_band: str         # "high" | "mid" | "low"
    escalated: bool              # True if danger-sign triggered
    disclaimer: bool             # True if Tier B disclosure needed
    retrieved_ids: list[int]     # KB row IDs used
    latency_ms: Optional[float]  # for logging

# ── Mock response (Phase 0) ────────────────────────────────────
MOCK_RESPONSE = AskResponse(
    answer="یہ این اے آئی کا ٹیسٹ جواب ہے۔ اصل جواب جلد آئے گا۔",
    audio_url=None,
    path="generated",
    confidence_band="high",
    escalated=False,
    disclaimer=False,
    retrieved_ids=[1, 2, 3],
    latency_ms=120.5,
)

@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Phase 0: returns a canned mock response.
    Real pipeline wired in Phase 2.
    """
    return MOCK_RESPONSE
