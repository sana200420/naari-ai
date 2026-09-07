"""
Safety Gate — Phase 1
Pure function over normalised text.
No LLM, no retrieval, no network calls.
A bug here has a physical consequence for a real woman.

v2: 
- Canonical Sindhi escalation script from kb_safety_always_on.md
- Sindhi keywords added for all 11 canonical categories
- Embedding similarity detection added (Phase 1 requirement)
"""

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

# ── Escalation script — canonical Sindhi from kb_safety_always_on.md ─────────
ESCALATION_SCRIPT = (
    "اها نشاني انتظار ڪرڻ جهڙي ناهي. "
    "مهرباني ڪري هينئر ئي ويجهي صحت مرڪز يا اسپتال وڃو، "
    "۽ ڪنهن کي پاڻ سان وٺي وڃو. دير نه ڪريو."
)

ESCALATION_SCRIPT_EN = (
    "This sign is not one to wait on. Please go to the nearest health centre "
    "or hospital now, and take someone with you. Don't delay."
)

# ── 11 Canonical Danger Categories (from kb_safety_always_on.md) ─────────────
DANGER_CATEGORIES = {
    "heavy_bleeding": {
        "description": "Any bleeding during pregnancy or heavy postpartum bleeding",
        "keywords_sindhi": [
            "رت وهڻ", "گھڻو رت", "تيز رت", "رت بند نٿو ٿئي",
            "ويم کان پوءِ گهڻو رت وهڻ", "پيڊ ڀرجي وڃي",
        ],
        "keywords_english": [
            "heavy bleeding", "soaking pads", "bleeding won't stop",
            "hemorrhage", "blood clots large", "flooding",
            "miscarriage bleeding", "tissue passing from vagina",
        ],
        "keywords_urdu": ["زیادہ خون", "خون بند نہیں", "بہت خون"]
    },
    "severe_headache": {
        "description": "Severe headache",
        "keywords_sindhi": [
            "سِر ۾ سخت سور", "سر ۾ تيز سور", "بي انتها مٿي جو سور",
        ],
        "keywords_english": [
            "severe headache", "worst headache", "unbearable headache",
            "thunderclap headache",
        ],
        "keywords_urdu": ["شدید سر درد", "ناقابل برداشت سر درد"]
    },
    "blurred_vision": {
        "description": "Blurred vision or darkness before eyes",
        "keywords_sindhi": [
            "اکين اڳيان ڌنڌ يا اونداهي", "اکين اڳيان اونداهي",
            "نظر ڌنڌلو", "وڄ جون چمڪون", "پاڇولا",
        ],
        "keywords_english": [
            "blurred vision", "blurred vision pregnancy", "darkness before eyes",
            "seeing spots", "vision changes",
        ],
        "keywords_urdu": ["دھندلی نظر", "آنکھوں کے آگے اندھیرا"]
    },
    "severe_pain": {
        "description": "Severe abdominal or pelvic pain",
        "keywords_sindhi": [
            "پيٽ ۾ سخت سور", "سخت درد", "تيز درد", "اڻ سهڻو درد",
            "سيخ وانگر سور", "نچوڙيندڙ سور",
        ],
        "keywords_english": [
            "severe pain", "unbearable pain", "sudden pain",
            "sharp pain", "excruciating", "worst pain",
            "severe abdominal pain",
        ],
        "keywords_urdu": ["شدید درد", "ناقابل برداشت درد", "اچانک درد"]
    },
    "swelling_face_hands": {
        "description": "Swelling of hands and face",
        "keywords_sindhi": [
            "هٿن ۽ منهن جو سُڄڻ", "چهري ۽ هٿن تي سوجن",
            "منهن سڄجڻ", "هٿ سڄجڻ",
        ],
        "keywords_english": [
            "swollen face", "swollen hands", "swelling of hands and face",
            "face swelling pregnancy", "puffiness face",
        ],
        "keywords_urdu": ["چہرہ سوجن", "ہاتھ سوجن", "حمل میں سوجن"]
    },
    "fever": {
        "description": "Fever",
        "keywords_sindhi": [
            "بخار", "تيز بخار", "سخت بخار", "ٿڌ سان بخار",
            "بخار ويم کان پوءِ",
        ],
        "keywords_english": [
            "fever after delivery", "very high fever", "fever won't break",
            "high fever", "fever with chills", "burning up",
        ],
        "keywords_urdu": ["تیز بخار", "بخار اتر نہیں رہا", "ڈلیوری کے بعد بخار"]
    },
    "reduced_fetal_movement": {
        "description": "Reduced or absent fetal movement",
        "keywords_sindhi": [
            "ٻار جو چرپر گهٽ ٿيڻ", "ٻار نٿو چري",
            "ٻار جي حرڪت", "حرڪت محسوس ناهي",
        ],
        "keywords_english": [
            "baby not moving", "no fetal movement", "reduced fetal movement",
            "baby not moving for hours", "can't feel baby",
        ],
        "keywords_urdu": ["بچہ نہیں ہل رہا", "حرکت نہیں", "بچے کی حرکت نہیں"]
    },
    "breathing_difficulty": {
        "description": "Difficulty breathing",
        "keywords_sindhi": [
            "ساهه کڻڻ ۾ تڪليف", "ساهه نٿو اچي", "ساهه گھٽجڻ",
            "ساهه بلڪل بند", "ساهه ٻوسڻ",
        ],
        "keywords_english": [
            "can't breathe", "difficulty breathing", "shortness of breath",
            "chest pain", "gasping", "breathless",
        ],
        "keywords_urdu": ["سانس نہیں آ رہی", "سینے میں درد", "دم گھٹ رہا ہے"]
    },
    "postpartum_danger": {
        "description": "Danger signs after delivery",
        "keywords_sindhi": [
            "ويم کان پوءِ گهڻو رت وهڻ", "بدبودار پاڻي",
            "گندي بوءِ", "ساواڻ مائل پاڻي",
        ],
        "keywords_english": [
            "postpartum bleeding", "foul smell after birth",
            "foul-smelling discharge", "infection after delivery",
            "lochia smell", "wound not healing",
        ],
        "keywords_urdu": ["ڈلیوری کے بعد خون", "بدبو ڈلیوری کے بعد", "بچے کے بعد بخار"]
    },
    "fits_fainting": {
        "description": "Fits or fainting",
        "keywords_sindhi": [
            "ڪَڙَ يا بيهوشي", "بيهوش", "دورو", "هٿ پير ڏڪڻ",
            "چڪرائي ڪري پيس",
        ],
        "keywords_english": [
            "fits", "seizure", "convulsion", "unconscious", "fainted",
            "passed out", "not waking up", "fits in pregnancy",
            "she is unconscious",
        ],
        "keywords_urdu": ["بیہوش", "دورہ پڑا", "ہوش نہیں", "غش"]
    },
    "infant_danger": {
        "description": "Danger signs in newborn",
        "keywords_sindhi": [
            "نوزائيده خطرو", "کير پيئڻ ڇڏي ڏنو",
        ],
        "keywords_english": [
            "baby not breathing", "newborn not feeding", "baby yellow",
            "jaundice newborn", "baby cold", "baby limp", "infant fits",
        ],
        "keywords_urdu": ["بچہ سانس نہیں لے رہا", "نوزائیدہ خطرہ"]
    },
    "abuse_violence": {
        "description": "Domestic violence or abuse",
        "keywords_sindhi": ["مار کٽ", "گهريلو تشدد"],
        "keywords_english": [
            "husband hitting", "husband hitting me", "domestic violence",
            "being beaten", "physical abuse", "he hit me", "forced sex", "rape"
        ],
        "keywords_urdu": ["مار پیٹ", "گھریلو تشدد", "زبردستی"]
    },
    "suicide_self_harm": {
        "description": "Suicidal ideation or self-harm",
        "keywords_sindhi": [
            "پاڻ کي نقصان", "زندگي ختم", "خودڪشي",
            "پاڻ کي ماري", "زندگي مان اميد ختم",
        ],
        "keywords_english": [
            "want to die", "kill myself", "i want to die", "i want to kill myself",
            "end my life", "self harm", "cut myself", "hurt myself",
            "suicide", "no reason to live",
        ],
        "keywords_urdu": ["مرنا چاہتی ہوں", "خود کو نقصان", "زندگی ختم کرنا"]
    },
}

# ── Scope classifier ───────────────────────────────────────────────────────────
SCOPE_REFERRALS = {
    "abortion": {
        "keywords": ["abortion", "terminate pregnancy", "اسقاط حمل کروانا", "حمل گرانا", "اسقاط", "حمل ختم"],
        "response": (
            "هي موضوع مخصوص طبي ۽ قانوني رهنمائي گھري ٿو جيڪا هي سروس مهيا نٿي ڪري سگهي. "
            "مهرباني ڪري ويجهي صحت مرڪز، ليڊي ڊاڪٽر يا تصديق ٿيل فيملي پلاننگ ڪلينڪ سان رابطو ڪريو."
        )
    },
    "named_contraceptives": {
        "keywords": ["pill name", "contraceptive pill", "iud brand", "copper t brand", "مرينا", "ياسمين"],
        "response": (
            "هي سروس مخصوص برانڊ يا پراڊڪٽ جي مقابلي جي صلاح نٿي ڏئي. "
            "پنهنجي حالت لاءِ بهترين آپشن معلوم ڪرڻ لاءِ مهرباني ڪري صحت ڪارڪن يا ڊاڪٽر سان صلاح ڪريو."
        )
    },
    "domestic_violence_referral": {
        "keywords": ["shelter", "escape husband", "leave home safe", "DV helpline"],
        "response": (
            "توهان جي حفاظت اهم آهي. مهرباني ڪري ويجهي مدد ڪندڙ اداري، "
            "پوليس هيلپ لائين يا ڀروسي واري شخص سان رابطو ڪريو. توهان اڪيلا ناهيو."
        )
    },
    "not_health": {
        "keywords": ["recipe", "cooking", "politics", "cricket", "weather", "news",
                     "recipe for biryani", "cricket match score"],
        "response": (
            "معاف ڪجو، هي سوال هن سروس جي دائري کان ٻاهر آهي. "
            "مهرباني ڪري لاڳاپيل شعبي جي ڊاڪٽر يا ماهر سان رابطو ڪريو."
        )
    },
    "doctor_question": {
        "keywords": ["are you a doctor", "kya tum doctor ho", "ڇا تون ڊاڪٽر آهين",
                     "ڇا توهان ڊاڪٽر آهيو", "are you a doctor"],
        "response": (
            "نه، هي هڪ خودڪار معلوماتي سروس آهي، ڊاڪٽر ناهي. "
            "هي عام صحت جي معلومات ڏئي ٿي، تشخيص يا علاج نٿي ڪري. "
            "طبي صلاح لاءِ مهرباني ڪري ڊاڪٽر يا صحت ڪارڪن سان رابطو ڪريو."
        )
    }
}

# ── Embedding similarity (Phase 1 requirement) ────────────────────────────────
# Loaded once at module level — never reload per request
_embedder = None
_danger_phrase_embeddings = None
_danger_phrases = []

DANGER_PHRASES_FOR_EMBEDDING = [
    # Canonical Sindhi from kb_safety_always_on.md
    "رت وهڻ", "سِر ۾ سخت سور", "اکين اڳيان ڌنڌ يا اونداهي",
    "پيٽ ۾ سخت سور", "هٿن ۽ منهن جو سُڄڻ", "بخار",
    "ٻار جو چرپر گهٽ ٿيڻ", "ساهه کڻڻ ۾ تڪليف",
    "ويم کان پوءِ گهڻو رت وهڻ", "بدبودار پاڻي", "ڪَڙَ يا بيهوشي",
    # English equivalents
    "heavy bleeding", "severe headache", "blurred vision",
    "severe abdominal pain", "swollen face and hands", "high fever",
    "baby not moving", "difficulty breathing",
    "bleeding after delivery", "foul smelling discharge", "fits fainting",
    "i want to die", "kill myself", "self harm",
]

EMBEDDING_THRESHOLD = 0.75  # cosine similarity threshold


def _load_embedder():
    """Load model once. Call only when embedding path is needed."""
    global _embedder, _danger_phrase_embeddings, _danger_phrases
    if _embedder is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        _embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        _danger_phrases = DANGER_PHRASES_FOR_EMBEDDING
        _danger_phrase_embeddings = _embedder.encode(
            _danger_phrases, normalize_embeddings=True
        )
    except Exception:
        _embedder = None


def _embedding_match(text: str) -> Optional[str]:
    """
    Returns matched danger phrase if embedding similarity >= threshold.
    Returns None if embedder not available or no match.
    """
    if _embedder is None:
        return None
    try:
        import numpy as np
        query_emb = _embedder.encode([text], normalize_embeddings=True)
        scores = (_danger_phrase_embeddings @ query_emb.T).flatten()
        best_idx = int(np.argmax(scores))
        if scores[best_idx] >= EMBEDDING_THRESHOLD:
            return _danger_phrases[best_idx]
    except Exception:
        pass
    return None


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
    category: str | None
    scope_block: str | None
    response: str | None
    matched_keyword: str | None
    method: str = "none"  # "keyword" | "embedding" | "scope" | "none"


# ── Main gate function ─────────────────────────────────────────────────────────
def run_danger_gate(text: str, use_embedding: bool = True) -> GateResult:
    """
    Pure function. Call this FIRST — before retrieval, before LLM.
    Returns GateResult with escalate=True if any danger keyword matches.
    use_embedding=True enables semantic fallback when keyword misses.
    """
    norm = normalise(text)

    # 1. Keyword check — fast, no model needed
    for cat_name, cat in DANGER_CATEGORIES.items():
        all_keywords = (
            cat.get("keywords_sindhi", [])
            + cat.get("keywords_english", [])
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
                    method="keyword",
                )

    # 2. Embedding similarity — catches paraphrases that share no keyword
    if use_embedding:
        _load_embedder()
        matched_phrase = _embedding_match(text)
        if matched_phrase:
            return GateResult(
                escalate=True,
                category="embedding_match",
                scope_block=None,
                response=ESCALATION_SCRIPT,
                matched_keyword=matched_phrase,
                method="embedding",
            )

    # 3. Scope classifier
    for scope_name, scope in SCOPE_REFERRALS.items():
        for kw in scope["keywords"]:
            if normalise(kw) in norm:
                return GateResult(
                    escalate=False,
                    category=None,
                    scope_block=scope_name,
                    response=scope["response"],
                    matched_keyword=kw,
                    method="scope",
                )

    # 4. All clear
    return GateResult(
        escalate=False,
        category=None,
        scope_block=None,
        response=None,
        matched_keyword=None,
        method="none",
    )
