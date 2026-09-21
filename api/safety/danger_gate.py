"""
Safety Gate — Phase 1
Pure function over normalised text.
No LLM, no retrieval, no network calls.
A bug here has a physical consequence for a real woman.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

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

# ── Semantic anchor phrases per danger category ────────────────────────────────
DANGER_ANCHORS = {
    "heavy_bleeding":       "excessive uncontrolled bleeding blood loss",
    "severe_pain":          "unbearable severe sudden intense pain abdomen pelvis",
    "pregnancy_danger":     "dangerous emergency sign during pregnancy baby not moving fits",
    "postpartum_danger":    "danger after delivery fever infection wound smell",
    "suicide_self_harm":    "wanting to die ending life hurting oneself",
    "unconsciousness":      "passed out fainted seizure loss of consciousness",
    "breathing_difficulty": "unable to breathe gasping chest pain suffocation",
    "high_fever":           "very high temperature fever not breaking burning up",
    "abuse_violence":       "being beaten hit domestic violence forced assault",
    "infant_danger":        "newborn baby not breathing not feeding yellow limp",
    "ectopic_miscarriage":  "pregnancy loss miscarriage bleeding tissue ectopic",
}

SIMILARITY_THRESHOLD = 0.55

# ── Lazy-loaded model ──────────────────────────────────────────────────────────
_model: Optional[SentenceTransformer] = None
_anchor_embeddings: Optional[np.ndarray] = None
_anchor_categories: list[str] = []


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    return _model


def _get_anchor_embeddings() -> tuple[np.ndarray, list[str]]:
    global _anchor_embeddings, _anchor_categories
    if _anchor_embeddings is None:
        model = _get_model()
        _anchor_categories = list(DANGER_ANCHORS.keys())
        anchors = [DANGER_ANCHORS[c] for c in _anchor_categories]
        _anchor_embeddings = model.encode(anchors, normalize_embeddings=True)
    return _anchor_embeddings, _anchor_categories


def _semantic_check(text: str) -> Optional[tuple[str, float]]:
    """
    Embed query and compare against 11 danger anchors.
    Catches phrasing that shares NO keyword but means the same thing.
    """
    model = _get_model()
    anchor_embs, categories = _get_anchor_embeddings()
    query_emb = model.encode([text], normalize_embeddings=True)
    scores = cosine_similarity(query_emb, anchor_embs)[0]
    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])
    if best_score >= SIMILARITY_THRESHOLD:
        return categories[best_idx], best_score
    return None


# ── Normaliser ─────────────────────────────────────────────────────────────────
def normalise(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"\s+", " ", text)
    return text


# ── Result dataclass ───────────────────────────────────────────────────────────
@dataclass
class GateResult:
    escalate: bool
    category: Optional[str]
    scope_block: Optional[str]
    response: Optional[str]
    matched_keyword: Optional[str]
    similarity_score: Optional[float] = field(default=None)


# ── Main gate function ─────────────────────────────────────────────────────────
def run_danger_gate(text: str, use_semantic: bool = True) -> GateResult:
    """
    Two-stage detection:
      1. Keyword matching  — fast, zero model cost.
      2. Embedding similarity — catches keyword-free paraphrases.
    """
    norm = normalise(text)

    # Stage 1: Keyword matching
    for cat_name, cat in DANGER_CATEGORIES.items():
        all_keywords = (
            cat.get("keywords_english", [])
            + cat.get("keywords_sindhi", [])
            + cat.get("keywords_urdu", [])
        )
        for kw in all_keywords:
            if normalise(kw) in norm:
                return GateResult(
                    escalate=True,
                    category=cat_name,
                    scope_block=None,
                    response=ESCALATION_SCRIPT,
                    matched_keyword=kw,
                    similarity_score=None,
                )

    # Stage 2: Embedding similarity
    if use_semantic:
        result = _semantic_check(text)
        if result is not None:
            cat_name, score = result
            return GateResult(
                escalate=True,
                category=cat_name,
                scope_block=None,
                response=ESCALATION_SCRIPT,
                matched_keyword=None,
                similarity_score=score,
            )

    # Stage 3: Scope classifiers
    for scope_name, scope in SCOPE_REFERRALS.items():
        for kw in scope["keywords"]:
            if normalise(kw) in norm:
                return GateResult(
                    escalate=False,
                    category=None,
                    scope_block=scope_name,
                    response=scope["response"],
                    matched_keyword=kw,
                    similarity_score=None,
                )

    # Stage 4: All clear
    return GateResult(
        escalate=False,
        category=None,
        scope_block=None,
        response=None,
        matched_keyword=None,
        similarity_score=None,
    )