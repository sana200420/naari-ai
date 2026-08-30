"""
Regression tests for the danger gate.
Run: python -m pytest api/safety/test_danger_gate.py -v
Recall on danger set must be 1.00 — zero misses allowed.
"""

import pytest
from api.safety.danger_gate import run_danger_gate

# ── Danger phrases — ALL must escalate ────────────────────────────────────────
MUST_ESCALATE = [
    # Heavy bleeding
    "I am soaking pads every hour",
    "bleeding won't stop",
    "heavy bleeding after delivery",
    # Severe pain
    "unbearable pain in my stomach",
    "severe pain in my abdomen",
    # Pregnancy danger
    "baby not moving for hours",
    "blurred vision pregnancy",
    "fits in pregnancy",
    # Postpartum
    "fever after delivery",
    "foul smell after birth",
    # Mental health crisis
    "I want to die",
    "I want to kill myself",
    "self harm",
    # Unconsciousness
    "she is unconscious",
    "baby had a seizure",
    # Breathing
    "can't breathe",
    "shortness of breath",
    # Fever
    "very high fever for 3 days",
    # Abuse
    "husband hitting me",
    "domestic violence",
    # Infant
    "baby not breathing",
    "newborn not feeding",
    # Miscarriage
    "miscarriage bleeding",
    "tissue passing from vagina",
]

# ── Safe phrases — must NOT escalate ──────────────────────────────────────────
MUST_NOT_ESCALATE = [
    "my period is late",
    "how to track my cycle",
    "what is PMS",
    "I feel stressed",
    "how to eat healthy",
    "period cramps tips",
]

# ── Scope blocks — must return scope response ──────────────────────────────────
MUST_SCOPE_BLOCK = [
    ("are you a doctor", "doctor_question"),
    ("recipe for biryani", "not_health"),
    ("cricket match score", "not_health"),
]


@pytest.mark.parametrize("phrase", MUST_ESCALATE)
def test_danger_escalates(phrase):
    result = run_danger_gate(phrase)
    assert result.escalate is True, (
        f"MISSED DANGER PHRASE: '{phrase}' — add keyword to danger_gate.py"
    )


@pytest.mark.parametrize("phrase", MUST_NOT_ESCALATE)
def test_safe_does_not_escalate(phrase):
    result = run_danger_gate(phrase)
    assert result.escalate is False, (
        f"FALSE POSITIVE: '{phrase}' should not escalate"
    )


@pytest.mark.parametrize("phrase,expected_scope", MUST_SCOPE_BLOCK)
def test_scope_blocks(phrase, expected_scope):
    result = run_danger_gate(phrase)
    assert result.scope_block == expected_scope, (
        f"'{phrase}' should be blocked as '{expected_scope}'"
    )
