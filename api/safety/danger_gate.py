"""
Safety Gate — Phase 1
Pure function over normalised text.
No LLM, no retrieval, no network calls.
A bug here has a physical consequence for a real woman.
"""

import re
import unicodedata
from dataclasses import dataclass

# ── Escalation script (fixed — never change without clinical review) ──────────
ESCALATION_SCRIPT = (
    "یہ معلومات آپ کی مدد کے لیے کافی نہیں ہیں۔ "
    "براہ کرم فوری طور پر کسی لیڈی ہیلتھ ورکر یا ڈاکٹر سے ملیں۔ "
    "اگر آپ کو شدید تکلیف ہے تو قریبی اسپتال جائیں۔"
)

ESCALATION_SCRIPT_EN = (
    "This information is not enough to help you. "
    "Please immediately contact a lady health worker or doctor. "
    "If you are in severe pain, go to the nearest hospital."
)

# ── 11 Danger Categories ───────────────────────────────────────────────────────
DANGER_CATEGORIES = {
    "heavy_bleeding": {
        "description": "Heavy or uncontrolled bleeding",
        "keywords_sindhi": ["گھڻو رت", "تيز رت", "رت بند نٿو ٿئي"],
        "keywords_english": [
            "heavy bleeding", "soaking pads", "bleeding won't stop",
            "hemorrhage", "blood clots large", "flooding"
        ],
        "keywords_urdu": ["زیادہ خون", "خون بند نہیں", "بہت خون"]
    },
    "severe_pain": {
        "description": "Severe or sudden abdominal/pelvic pain",
        "keywords_sindhi": ["سخت درد", "تيز درد", "اڻ سهڻو درد"],
        "keywords_english": [
            "severe pain", "unbearable pain", "sudden pain",
            "sharp pain", "excruciating", "worst pain"
        ],
        "keywords_urdu": ["شدید درد", "ناقابل برداشت درد", "اچانک درد"]
    },
    "pregnancy_danger": {
        "description": "Danger signs in pregnancy",
        "keywords_sindhi": ["حمل ۾ خطرو", "پيٽ ۾ درد حمل"],
        "keywords_english": [
            "blurred vision pregnancy", "swollen face pregnancy",
            "no fetal movement", "baby not moving", "preeclampsia",
            "fits in pregnancy", "convulsion pregnant", "water broke early"
        ],
        "keywords_urdu": ["حمل میں خطرہ", "بچہ نہیں ہل رہا", "دھندلی نظر حمل"]
    },
    "postpartum_danger": {
        "description": "Danger signs after delivery",
        "keywords_sindhi": ["ڄڻڻ کان پوءِ تڪليف"],
        "keywords_english": [
            "postpartum bleeding", "fever after delivery", "foul smell after birth",
            "lochia smell", "infection after delivery", "wound not healing"
        ],
        "keywords_urdu": ["بچے کے بعد بخار", "ڈلیوری کے بعد خون", "بدبو ڈلیوری کے بعد"]
    },
    "suicide_self_harm": {
        "description": "Suicidal ideation or self-harm",
        "keywords_sindhi": ["پاڻ کي نقصان", "زندگي ختم"],
        "keywords_english": [
            "want to die", "kill myself", "end my life", "self harm",
            "cut myself", "hurt myself", "suicide", "no reason to live"
        ],
        "keywords_urdu": ["مرنا چاہتی ہوں", "خود کو نقصان", "زندگی ختم کرنا"]
    },
    "unconsciousness": {
        "description": "Loss of consciousness or fits",
        "keywords_sindhi": ["بيهوش", "دورو"],
        "keywords_english": [
            "unconscious", "fainted", "passed out", "seizure",
            "fits", "convulsion", "not waking up"
        ],
        "keywords_urdu": ["بیہوش", "دورہ پڑا", "ہوش نہیں"]
    },
    "breathing_difficulty": {
        "description": "Difficulty breathing",
        "keywords_sindhi": ["ساهه نٿو اچي"],
        "keywords_english": [
            "can't breathe", "difficulty breathing", "shortness of breath",
            "chest pain", "gasping"
        ],
        "keywords_urdu": ["سانس نہیں آ رہی", "سینے میں درد", "دم گھٹ رہا ہے"]
    },
    "high_fever": {
        "description": "Very high fever",
        "keywords_sindhi": ["تيز بخار", "سخت بخار"],
        "keywords_english": [
            "very high fever", "fever won't break", "104 fever",
            "105 fever", "burning up", "fever with rash"
        ],
        "keywords_urdu": ["تیز بخار", "بخار اتر نہیں رہا"]
    },
    "abuse_violence": {
        "description": "Domestic violence or abuse",
        "keywords_sindhi": ["مار کٽ", "گهريلو تشدد"],
        "keywords_english": [
            "husband hitting", "domestic violence", "being beaten",
            "physical abuse", "he hit me", "forced sex", "rape"
        ],
        "keywords_urdu": ["مار پیٹ", "گھریلو تشدد", "زبردستی", "زیادتی"]
    },
    "infant_danger": {
        "description": "Danger signs in newborn",
        "keywords_sindhi": ["نوزائيده خطرو"],
        "keywords_english": [
            "baby not breathing", "newborn not feeding", "baby yellow",
            "jaundice newborn", "baby cold", "baby limp", "infant fits"
        ],
        "keywords_urdu": ["بچہ سانس نہیں لے رہا", "نوزائیدہ خطرہ", "بچہ پیلا"]
    },
    "ectopic_miscarriage": {
        "description": "Signs of ectopic pregnancy or miscarriage",
        "keywords_sindhi": ["اسقاط حمل", "حمل ضايع"],
        "keywords_english": [
            "miscarriage", "bleeding in pregnancy", "tissue passing",
            "ectopic", "pregnancy loss", "clots in pregnancy"
        ],
        "keywords_urdu": ["اسقاط حمل", "حمل گر گیا", "حمل میں خون"]
    },
}

# ── Scope classifier ───────────────────────────────────────────────────────────
SCOPE_REFERRALS = {
    "abortion": {
        "keywords": ["abortion", "terminate pregnancy", "اسقاط حمل کروانا", "حمل گرانا"],
        "response": (
            "NaariAI صرف عورتوں کی صحت کی عمومی معلومات دیتی ہے۔ "
            "براہ کرم کسی ڈاکٹر سے ملیں۔"
        )
    },
    "named_contraceptives": {
        "keywords": ["pill name", "contraceptive pill", "iud brand", "copper t brand"],
        "response": (
            "مخصوص دوائیوں کے بارے میں معلومات کے لیے ڈاکٹر سے رجوع کریں۔"
        )
    },
    "domestic_violence_referral": {
        "keywords": ["shelter", "escape husband", "leave home safe", "DV helpline"],
        "response": (
            "آپ کی مدد کے لیے لیڈی ہیلتھ ورکر سے رابطہ کریں۔ "
            "آپ اکیلی نہیں ہیں۔"
        )
    },
    "not_health": {
        "keywords": ["recipe", "cooking", "politics", "cricket", "weather", "news"],
        "response": (
            "NaariAI صرف عورتوں کی صحت سے متعلق سوالوں کے جواب دیتی ہے۔"
        )
    },
    "doctor_question": {
        "keywords": ["are you a doctor", "kya tum doctor ho", "ڇا تون ڊاڪٽر آهين"],
        "response": (
            "نہیں، میں NaariAI ہوں — ایک معلوماتی آواز کا ساتھی۔ "
            "میں ڈاکٹر نہیں ہوں۔ ہمیشہ کسی لیڈی ہیلتھ ورکر یا ڈاکٹر سے تصدیق کریں۔"
        )
    }
}


# ── Normaliser ─────────────────────────────────────────────────────────────────
def normalise(text: str) -> str:
    """Lowercase, strip diacritics, collapse whitespace."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"\s+", " ", text)
    return text


# ── Result dataclass ───────────────────────────────────────────────────────────
@dataclass
class GateResult:
    escalate: bool
    category: str | None          # which danger category triggered
    scope_block: str | None       # which scope referral triggered
    response: str | None          # fixed response if blocked
    matched_keyword: str | None   # for logging/regression tests


# ── Main gate function ─────────────────────────────────────────────────────────
def run_danger_gate(text: str) -> GateResult:
    """
    Pure function. Call this FIRST — before retrieval, before LLM.
    Returns GateResult with escalate=True if any danger keyword matches.
    """
    norm = normalise(text)

    # 1. Check all 11 danger categories
    for cat_name, cat in DANGER_CATEGORIES.items():
        all_keywords = (
            cat.get("keywords_english", [])
            + cat.get("keywords_sindhi", [])
            + cat.get("keywords_urdu", [])
        )
        for kw in all_keywords:
            if re.search(r"\b" + re.escape(normalise(kw)) + r"\b", norm):
                return GateResult(
                    escalate=True,
                    category=cat_name,
                    scope_block=None,
                    response=ESCALATION_SCRIPT,
                    matched_keyword=kw,
                )

    # 2. Check scope classifiers
    for scope_name, scope in SCOPE_REFERRALS.items():
        for kw in scope["keywords"]:
            if re.search(r"\b" + re.escape(normalise(kw)) + r"\b", norm):
                return GateResult(
                    escalate=False,
                    category=None,
                    scope_block=scope_name,
                    response=scope["response"],
                    matched_keyword=kw,
                )

    # 3. All clear
    return GateResult(
        escalate=False,
        category=None,
        scope_block=None,
        response=None,
        matched_keyword=None,
    )
