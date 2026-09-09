"""
Phase 3 — Review tier enforcement
Tier A: clinician-reviewed — serve normally
Tier B: sourced but unreviewed — serve with disclaimer flag
Tier C: uncertain/flagged — never serve, return refusal
"""
from typing import Optional

TIER_A = "A"
TIER_B = "B"
TIER_C = "C"

TIER_B_DISCLAIMER = (
    "هي معلومات ڪنهن تصديق ٿيل ڪلينشن طرفان جائزو نه ورتل آهي. "
    "مهرباني ڪري ڪنهن صحت ڪارڪن سان تصديق ڪريو."
)

TIER_C_REFUSAL = (
    "معاف ڪجو، هي معلومات في الحال موجود ناهي. "
    "مهرباني ڪري ليڊي هيلٿ ورڪر سان رابطو ڪريو."
)


def enforce_tier(tier: Optional[str], answer: str, disclaimer: bool):
    """
    Returns (answer, disclaimer, blocked).
    blocked=True means Tier C — never serve.
    """
    if tier == TIER_C:
        return TIER_C_REFUSAL, False, True
    if tier == TIER_B:
        return answer, True, False
    # Tier A or unknown — serve normally
    return answer, disclaimer, False
