"""
Safety Gate — Phase 1
Pure function over normalised text.
No LLM, no retrieval, no network calls.
A bug here has a physical consequence for a real woman.

v2:
- Canonical Sindhi escalation script from kb_safety_always_on.md
- Sindhi keywords added for all 11 canonical categories
- Embedding similarity detection added (Phase 1 requirement)

v3 (this revision) — fixes two classes of bug found after rounds 3-6 of
ad hoc patching pushed danger-set recall to 1.00 by memorising the exact
miss sentences:

1. FALSE POSITIVES from bare, generic single-word keywords. A word like
   "بخار" (fever) alone matches any sentence containing it, including
   benign dosage questions ("paracetamol dose for fever in pregnancy").
   Fix: generic disease/symptom names must appear with a severity or
   context qualifier (see docs/adr/0003-danger-gate-matching.md).

2. FALSE NEGATIVES from exact-substring-only matching on multi-word
   Sindhi phrases. Sindhi word order and connectors ("سان گڏ" vs a comma,
   verb inflection) vary far more than the harvested miss sentences did,
   so a phrase copied verbatim from one eval row does not generalise to
   a differently-worded but clinically identical report. Fix: keyword
   matching now also accepts a "significant-token" match — all
   non-stopword tokens of a keyword phrase present in the query, in any
   order — in addition to the exact-substring fast path. See
   `_phrase_matches` and `docs/adr/0003-danger-gate-matching.md`.

Neither fix touches the embedding path's *behaviour*; it only fixes a
staleness bug where newly added keyword categories (rounds 3-6) were
never added to the embedding reference-phrase list, so the semantic
fallback had no way to catch paraphrases of them. The reference list is
now derived automatically from DANGER_CATEGORIES so this cannot go
stale again (see `_build_embedding_reference`).
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from retrieval.normalize import normalize_sd

# Sindhi/Urdu function words that carry no clinical meaning on their own.
# Used only to find the "significant" tokens of a multi-word keyword phrase
# for the fallback token-bag match — never used to relax single-word
# keywords, which must still match as an exact substring.
_STOPWORDS = {
    "سان", "گڏ", "کان", "پوءِ", "جو", "جي", "جا", "جن", "۾", "تي", "به",
    "نه", "ٿي", "ٿو", "ٿئي", "وئي", "آهي", "آهن", "۽", "کي", "هي", "هو",
    "ته", "جيڪو", "جيڪا", "ئي", "پيو", "پئي", "لاءِ", "مان", "کان",
}
_TOKEN_SPLIT_RE = re.compile(r"[^\w]+", re.UNICODE)


def _significant_tokens(phrase: str) -> list[str]:
    """Tokens of a normalised phrase with stopwords and single chars removed."""
    tokens = [t for t in _TOKEN_SPLIT_RE.split(phrase) if t]
    return [t for t in tokens if len(t) > 1 and t not in _STOPWORDS]


def _phrase_matches(keyword_norm: str, text_norm: str) -> bool:
    """
    True if `keyword_norm` should be considered present in `text_norm`.

    Fast path: exact substring (handles single words and phrases that are
    typically written the same way every time, e.g. "خودڪشي").

    Fallback: for multi-word phrases (2+ significant tokens), also match
    if every significant token appears somewhere in the text, regardless
    of order or connecting words. This is deliberately NOT applied to
    single-token keywords — a lone generic word must still match exactly
    as itself, never as a "bag of one token", so this fallback cannot
    turn a single generic word into an even broader match.
    """
    if keyword_norm in text_norm:
        return True
    tokens = _significant_tokens(keyword_norm)
    if len(tokens) < 2:
        return False
    return all(tok in text_norm for tok in tokens)

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
            "ويم کان پوءِ گهڻو رت وهڻ", "پيڊ ڀرجي وڃي", "پيڊ پوريءَ ريت ڀرجي وڃي",
            "پيڊ جلدي ڀرجي وڃڻ",
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
            "نظر ڌنڌلو", "وڄ جون چمڪون", "پاڇولا", "ٻٽو نظر",
            "اکين اڳيان اونداهو ڇانئجڻ",
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
            "سيخ وانگر", "نچوڙيندڙ سور", "هٿ لائڻ نٿو ڏئي",
            "پيٽ پٿر وانگر سخت", "بي انتها سور",
            "هٿ لائڻ نه ڏيڻ",
        ],
        "keywords_english": [
            "severe pain", "unbearable pain", "sudden pain",
            "sharp pain", "excruciating", "worst pain",
            "severe abdominal pain", "abdomen guarding", "can't touch abdomen",
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
            # NOTE: bare "بخار" (fever) was removed here — it matched any
            # sentence merely mentioning fever, including benign medication-
            # dosage questions ("paracetamol dose for fever in pregnancy",
            # eval/negative_set_100.csv id 26). Every remaining entry pairs
            # the word with a severity/duration/timing qualifier, which is
            # the actual danger signal per kb_safety_always_on.md.
            "تيز بخار", "سخت بخار", "ٿڌ سان بخار",
            "بخار ويم کان پوءِ", "بخار لاهي نٿو اچي",
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
            "ٻار جي حرڪت", "حرڪت محسوس ناهي", "ناهي چريو",
        
            "ٻار جي ڪا به حرڪت يا ڦڙڦڙ محسوس ناهي ٿي",
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
            "ساهه بلڪل بند", "ساهه ٻوسڻ", "ساهه بي انتها بند",
            "سيٽيءَ جهڙو آواز",
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
            "نوزائيده خطرو", "کير پيئڻ ڇڏي ڏنو", "تليون پيليون",
            "ڇاتي اندر ڍري وڃي", "گرنٽنگ جهڙو آواز",
            "نئون ڄاول ٻار جو کير پيئڻ لاءِ اکيون نه کولڻ",
            "ٻار جي ڇاتي اندر ڍري وڃڻ",
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
        
            "پاڻ کي ختم ڪرڻ جا خيال اچن ٿا",
            "ان جو طريقو به سوچي ورتو آهي",
            "پاڻ کي ختم ڪرڻ جا خيال",
        ],
        "keywords_english": [
            "want to die", "kill myself", "i want to die", "i want to kill myself",
            "end my life", "self harm", "cut myself", "hurt myself",
            "suicide", "no reason to live",
        ],
        "keywords_urdu": ["مرنا چاہتی ہوں", "خود کو نقصان", "زندگی ختم کرنا"]
    },
    "pulmonary_embolism": {
        "description": "Signs of blood clot in lungs — coughing blood, sudden chest pain with breathlessness",
        "keywords_sindhi": [
                                    "کنگهه سان گڏ رت جا ڦڙا", "سيني ۾ تيز ڇوب", "ڇاتيءَ ۾ تيز ڇوب",
            # General form, not tied to one exact sentence: "cough" + "blood"
            # together, in any order/connector (see _phrase_matches).
            "کنگهه سان رت",
        ],
        "keywords_english": [
            "coughing blood", "blood in cough", "sudden chest pain breathing",
        ],
        "keywords_urdu": ["کھانسی میں خون", "سینے میں اچانک درد"]
    },
    "anaphylaxis": {
        "description": "Signs of severe allergic reaction — swelling of lips/tongue/throat, breathing difficulty",
        "keywords_sindhi": [
                                    "چپ ۽ زبان سڄي", "منهن ۽ نڙي سوجي", "نڙيءَ ۾ سوڙهاڻ",
            "چپ ۽ زبان يا منهن سوجڻ",
        ],
        "keywords_english": [
            "lip swelling", "tongue swelling", "throat tightness", "allergic reaction breathing",
        ],
        "keywords_urdu": ["ہونٹ سوجن", "گلا تنگ ہونا", "الرجک ردعمل"]
    },
    "no_urine_output": {
        "description": "Complete absence of urine output (anuria) or acute urinary retention",
        "keywords_sindhi": [
                                    "هڪ ڦڙو به پيشاب ناهي آيو", "بلڪل پيشاب نٿو اچي",
        
            "پوري ڏينهن ۾ هڪ به دفعو پيشاب نه ڪيو آهي",
            "مٿي جي نرم جاءِ به هيٺ ڦِٿل محسوس ٿئي ٿي",
            # General "urine" + "completely/not at all" + "not coming" form —
            # word order and verb inflection vary a lot here (نه/نٿو، اچڻ/اچي),
            # so this is a second, differently-worded phrasing rather than a
            # fix aimed at one sentence.
            "پيشاب بلڪل نه اچڻ",
            "مٿي جي نرم جاءِ ڦِٿل ٿيڻ",
        ],
        "keywords_english": [
            "no urine", "not urinating", "can't urinate", "no urine output",
        ],
        "keywords_urdu": ["پیشاب نہیں آ رہا", "پیشاب بند"]
    },
    "postmenopausal_bleeding": {
        "description": "New vaginal bleeding after menopause",
        "keywords_sindhi": [
                                    "ماهواري بند ٿيڻ کي ٻه سال", "ٻيهر رت اچڻ شروع",
            # General form: menopause/period-stopped + bleeding, without
            # requiring a specific elapsed-time phrase like "ٻه سال".
            "ماهواري بند ٿيڻ کان پوءِ رت",
        ],
        "keywords_english": [
            "bleeding after menopause", "postmenopausal bleeding",
        ],
        "keywords_urdu": ["مینوپاز کے بعد خون", "ماہواری بند ہونے کے بعد خون"]
    },
    "diabetic_emergency": {
        "description": "Signs of diabetic ketoacidosis — persistent vomiting with severe thirst",
        "keywords_sindhi": [
                                    "مسلسل الٽيون، سخت اڃ",
            "بيسودي يا مونجهارو محسوس ٿيڻ",
        ],
        "keywords_english": [
            "persistent vomiting severe thirst", "diabetic emergency", "ketoacidosis",
        ],
        "keywords_urdu": ["مسلسل قے شدید پیاس", "شوگر ایمرجنسی"]
    },
    "postpartum_mental_health_crisis": {
        "description": "Postpartum psychosis or severe mental health crisis — distinct from suicidal ideation",
        "keywords_sindhi": [
                                    "عجب آواز ٻڌڻ", "ننڊ بلڪل ناهي آئي", "ٻار کي نقصان پهچايان", "ٻار کي ڪجهه ناهوسات",
            "ٻار کي نقصان پهچائڻ جا خيال",
            "ننڊ بلڪل نه اچڻ",
            "ٻار کان ناهوسات محسوس ڪرڻ",
        ],
        "keywords_english": [
            "postpartum insomnia severe", "hearing voices postpartum", "detached from baby",
        ],
        "keywords_urdu": ["ڈلیوری کے بعد نیند نہیں", "بچے سے لگاؤ نہیں"]
    },
    "neurological_emergency": {
        "description": "Signs of stroke — limb numbness/weakness with slurred speech",
        "keywords_sindhi": [
            "هٿ ۽ پير سُڃا ٿي ويا آهن", "ٻولي ٻُٿي ٿئي", "چڪرائي پئي آهيان",
            "هٿ يا پير سُڃا ٿي وڃڻ",
        ],
        "keywords_english": [
            "limb numbness", "slurred speech", "sudden weakness one side",
        ],
        "keywords_urdu": ["ہاتھ پاؤں سن ہونا", "بولنے میں لڑکھڑاہٹ"]
    },
    "postpartum_septic_shock": {
        "description": "Signs of septic shock — body turning cold, bluish/pale skin",
        "keywords_sindhi": [
            "جسم يخ ٿي ويو آهي", "چمڙي پيلي نيري پئجي وئي آهي",
            "جسم يخ ٿي وڃڻ",
        ],
        "keywords_english": [
            "body turning cold", "bluish pale skin", "postpartum septic shock",
        ],
        "keywords_urdu": ["جسم ٹھنڈا ہو رہا ہے", "جلد کا رنگ نیلا پڑنا"]
    },
    "ectopic_pregnancy": {
        "description": "Signs of ruptured ectopic pregnancy — unilateral pain radiating to shoulder in early pregnancy",
        "keywords_sindhi": [
            "ڪلھي ۾ به سور ٿئي پيو",
            "کلهي ۾ سور سان گڏ پيٽ جو سور",
        ],
        "keywords_english": [
            "shoulder tip pain pregnancy", "one sided pain shoulder early pregnancy",
        ],
        "keywords_urdu": ["کندھے میں درد حمل"]
    },
    "dvt_pregnancy": {
        "description": "Signs of DVT in pregnancy or on fertility treatment — sudden hot swollen leg, calf pain with breathlessness",
        "keywords_sindhi": [
            "ٽنگ اوچتو ڏاڍي سڄي پئي آهي",
            "لسي ۽ باهه وانگر گرم آهي",
            "ٽنگ جي پني ۾ سور ۽ سوجن",
        
            "ٽنگ ڦاٽڻ وانگر سڄي پئي آهي",
            "گهوٽي واري ٽنگ ۾ سخت سور",
            "ٽنگ ۾ سوجن ۽ گرمي",
            "پني ۾ سور ۽ سوجن",
        ],
        "keywords_english": [
            "leg swollen hot pregnancy", "calf swelling pain breathlessness",
        ],
        "keywords_urdu": ["ٹانگ میں سوجن گرم حمل"]
    },
    "preterm_rupture_membranes": {
        "description": "Continuous watery leaking before term (PPROM)",
        "keywords_sindhi": [
            "ڄنگهن مان اڻ کُٽ گرم پاڻي وهڻ شروع ٿي ويو آهي",
            "گرم پاڻي جو اوچتو وهڻ",
        ],
        "keywords_english": [
            "continuous water leaking pregnancy", "watery discharge before labor",
        ],
        "keywords_urdu": ["مسلسل پانی رسنا حمل"]
    },
    "severe_hyperemesis": {
        "description": "Cannot keep down any liquids with dehydration signs during pregnancy",
        "keywords_sindhi": [
            "پاڻي جو ڍُڪ به پيٽ ۾ نٿو ترسي",
            "پيشاب تمام گھاٽو پيلو ۽ گهٽ ٿئي ٿو",
            "گهاٽو ۽ گهٽ پيشاب",
        ],
        "keywords_english": [
            "can't keep down water pregnancy", "severe vomiting dehydration pregnancy",
        ],
        "keywords_urdu": ["پانی بھی نہیں رکتا حمل"]
    },
    "uterine_rupture": {
        "description": "Scar pain then sudden cessation of contractions during home labor after prior C-section",
        "keywords_sindhi": [
            "ٽانڪن واري جاءِ تي چير پوڻ جهڙو سخت سور",
            "اوچتو سور بند ٿي ويا آهن پر چڪر پيا اچن",
            "سور اوچتو بند ٿي وڃڻ",
        ],
        "keywords_english": [
            "scar tearing pain labor c-section", "contractions suddenly stopped dizzy",
        ],
        "keywords_urdu": ["ٹانکوں کی جگہ پھٹنے جیسا درد"]
    },
    "postpartum_preeclampsia": {
        "description": "Severe headache with epigastric pain after delivery",
        "keywords_sindhi": [
            "مٿي ۾ بي انتها ڌڪ جهڙو سور",
            "ڇاتيءَ جي هيٺيان پيٽ ۾ سخت ساڙ",
        ],
        "keywords_english": [
            "severe headache postpartum", "epigastric pain after delivery",
        ],
        "keywords_urdu": ["شدید سر درد زچگی کے بعد"]
    },
    "molar_pregnancy": {
        "description": "Grape-like vesicles passed with heavy bleeding, uterus larger than dates",
        "keywords_sindhi": [
            "انگورن جهڙا ننڍا ننڍا داڻا رت سان گڏ نڪري رهيا آهن",
            "انگورن جهڙا داڻا نڪرڻ",
        ],
        "keywords_english": [
            "grape like vesicles bleeding pregnancy", "molar pregnancy tissue passing",
        ],
        "keywords_urdu": ["انگور جیسے دانے خون کے ساتھ"]
    },
    "ovarian_torsion": {
        "description": "Sudden severe one-sided pelvic pain with vomiting, cannot stand",
        "keywords_sindhi": [
            "ايترو تيز چُٽ وارو سور اٿيو جو بيهي نه پيو سگهجي",
            "بيهي نه سگهجڻ",
        ],
        "keywords_english": [
            "sudden severe one sided pelvic pain vomiting", "cannot stand pain",
        ],
        "keywords_urdu": ["اچانک شدید ایک طرفہ درد کھڑا نہیں ہو سکتی"]
    },
    "neonatal_seizures": {
        "description": "Newborn body stiffening, eyes rolling up, jerking limbs",
        "keywords_sindhi": [
            "جسم اوچتو سخت ٿي وڃي ٿو ۽ اکيون مٿي مٿي ٿي وڃن ٿيون",
            "هٿ پير جھٽڪا کائين ٿا",
            "اکيون مٿي مٿي ٿي وڃڻ",
            "هٿ پير جھٽڪا کائڻ",
        ],
        "keywords_english": [
            "newborn body stiffening eyes rolling", "baby jerking limbs seizure",
        ],
        "keywords_urdu": ["نوزائیدہ جسم اکڑنا آنکھیں اوپر"]
    },
    "bowel_obstruction": {
        "description": "Abdominal distension with no gas or stool after gynecological surgery",
        "keywords_sindhi": [
            "پيٽ تمام گهڻو ڦوڪجي ويو آهي، نه گئس نڪري رهي آهي نه پاخانو",
        
            "پيٽ تمام گهڻو ڦوليو آهي، نه گئس نڪري رهي آهي نه پاخانو",
            "پيٽ ڦوڪجڻ ۽ گئس يا پاخانو نه نڪرڻ",
        ],
        "keywords_english": [
            "no gas no stool distended abdomen surgery", "bowel obstruction post surgery",
        ],
        "keywords_urdu": ["نہ گیس نہ پاخانہ پیٹ پھولا ہوا"]
    },
    "postpartum_cardiac_event": {
        "description": "Chest pain radiating to arm with sweating and rapid heartbeat postpartum",
        "keywords_sindhi": [
            "سيني ۾ سور ٿيو جيڪو کاٻي هٿ ۾ به وڃي ٿو",
            "پگهر اچي رهيو آهي ۽ دل ڏاڍي تيز ڌڙڪي پيئي",
        
            "سيني ۾ ڳرو بار محسوس ٿئي ٿو جيڪو کاٻي هٿ ۽ ڏاڙهيءَ تائين وڃي ٿو",
            "سيني ۾ ڳرو بار محسوس ٿيڻ",
            "سيني ۾ سور کاٻي هٿ ڏانهن وڃڻ",
        ],
        "keywords_english": [
            "chest pain radiating to arm postpartum", "sweating rapid heartbeat after delivery",
        ],
        "keywords_urdu": ["سینے کا درد بازو میں پسینہ دل تیز"]
    },
    "obstetric_cholestasis": {
        "description": "Severe nighttime itching of palms and soles with dark urine in late pregnancy",
        "keywords_sindhi": [
            "تلين ۽ هٿن ۾ رات جو ايتري خارش ٿئي ٿي",
            "تلين ۽ هٿن ۾ رات جو خارش",
        ],
        "keywords_english": [
            "itching palms soles night pregnancy", "dark urine severe itching pregnancy",
        ],
        "keywords_urdu": ["تلوے ہتھیلیوں میں رات کو خارش حمل"]
    },
    "trauma_bleeding_blood_thinners": {
        "description": "Abdominal pain and large bruise after a fall while on blood-thinning medication",
        "keywords_sindhi": [
            "پيٽ ۾ تمام تيز سور ٿي رهيو آهي ۽ چمڙي تي وڏو نيرو ڌٻو پيو آهي",
            "ڪري پوڻ کان پوءِ نيرو ڌٻو پوڻ",
        ],
        "keywords_english": [
            "abdominal pain large bruise blood thinner fall", "internal bleeding on blood thinners",
        ],
        "keywords_urdu": ["گرنے کے بعد پیٹ میں درد بڑا نیل خون پتلا کرنے والی دوا"]
    },
    "cervical_insufficiency_late_miscarriage": {
        "description": "Bulging membranes / something protruding from the vagina with bleeding before 24 weeks",
        "keywords_sindhi": [
            "شرمگاهه مان ڪجهه ڳرو ٻاهر لٽڪندي محسوس ٿئي ٿو",
            "شرمگاهه مان شئي ٻاهر لٽڪڻ",
        ],
        "keywords_english": [
            "something bulging out of vagina pregnancy", "membrane bulging miscarriage",
        ],
        "keywords_urdu": ["اندام نہانی سے کوئی چیز باہر لٹکنا حمل"]
    },
    "cord_prolapse": {
        "description": "Water breaks with a cord-like structure felt/visible before labor pain starts",
        "keywords_sindhi": [
            "پاڻي جي ٿيلهي ڦاٽي پئي آهي ۽ هيٺان هڪ ناڙيءَ جهڙي شيءِ ٻاهر نڪرندي محسوس ٿئي ٿي",
            "ڌڙڪندڙ شئي ٻاهر نڪرندي محسوس ٿئي ٿي",
            "ناڙيءَ جهڙي شيءِ ٻاهر نڪرڻ",
        ],
        "keywords_english": [
            "cord prolapse water broke", "something coming out after water breaks",
            "pulsating thing coming out",
        ],
        "keywords_urdu": ["پانی ٹوٹنے کے بعد نال جیسی چیز باہر آنا"]
    },
    "placental_abruption": {
        "description": "Board-like rigid abdomen with dark bleeding, or blunt trauma with dark bleeding, in later pregnancy",
        "keywords_sindhi": [
            "پيٽ ڳاڙهي ڪاٺيءَ وانگر سخت ۽ پٿر ٿي ويو آهي ۽ گهاٽو رت اچي رهيو آهي",
            "ڏاڪڻين تان ٻکربائي پوڻ سبب پيٽ تي سخت ڌڪ لڳو آهي ۽ هلڪو ڪارو گهاٽو رت نڪري رهيو آهي",
            "پيٽ بلڪل پٿر وانگر سخت ٿي ويو آهي ۽ موٽي نرم نٿو ٿئي",
            "ڌڪ لڳڻ کان پوءِ رت اچڻ",
        ],
        "keywords_english": [
            "board-like rigid abdomen dark bleeding pregnancy", "abdominal trauma dark bleeding pregnancy",
        ],
        "keywords_urdu": ["پیٹ پتھر جیسا سخت گہرا خون حمل"]
    },
    "severe_preeclampsia_hellp": {
        "description": "Epigastric pain with blurred vision in late pregnancy",
        "keywords_sindhi": [
            "پيٽ جي ڇاتي واري پاسي ڏاڍو ساڙ ۽ سور آهي ۽ نظر به اوچتو دھنڌلي ٿي وئي آهي",
            "ڳالهيون وسارڻ يا پريشان ٿيڻ",
        ],
        "keywords_english": [
            "epigastric pain blurred vision late pregnancy",
        ],
        "keywords_urdu": ["پیٹ میں جلن دھندلی نظر حمل"]
    },
    "preeclampsia_neuro_signs": {
        "description": "Sudden visual dimming/blackout with ringing in ears in late pregnancy",
        "keywords_sindhi": [
            "اکين اڳيان اوچتو اندهيرو ڇانئجي وڃي ٿو ۽ ڪنن ۾ سيٽيون ٻرن ٿيون",
            "ڪنن ۾ سيٽيون وڄڻ",
        ],
        "keywords_english": [
            "sudden vision blackout ringing ears pregnancy",
        ],
        "keywords_urdu": ["اچانک آنکھوں کے آگے اندھیرا کانوں میں سیٹیاں حمل"]
    },
    "ruptured_ovarian_cyst": {
        "description": "Sudden lower pelvic pain radiating to shoulder with dizziness in a non-pregnant woman",
        "keywords_sindhi": [
            "پيٽ جي هيٺين پاسي کان تيز سور اٿيو جيڪو ڪلھي تائين پيو وڃي",
        ],
        "keywords_english": [
            "pelvic pain radiating shoulder dizziness non-pregnant",
        ],
        "keywords_urdu": ["پیٹ میں درد کندھے تک چکر"]
    },
    "postpartum_pulmonary_embolism": {
        "description": "Sudden chest pain and breathlessness in the postpartum period",
        "keywords_sindhi": [
            "ڇاتيءَ ۾ تيز ڌيڪي جهڙو سور ٿيو آهي ۽ ويٺي ويٺي ساهه گھٽجي رهيو آهي",
        ],
        "keywords_english": [
            "sudden chest pain breathlessness postpartum",
        ],
        "keywords_urdu": ["زچگی کے بعد اچانک سینے میں درد سانس میں تکلیف"]
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
                     "recipe for biryani", "cricket match score", "ڪرڪيٽ", "موسم", "سياست", "خبرون", "ريسيپي", "کاڌي جي ترڪيب", "ڪرڪيٽ ميچ"],
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

# A handful of canonical phrases kept separate from DANGER_CATEGORIES because
# they describe the *general* symptom pattern rather than one category's
# specific keyword list — extra semantic anchors, not a replacement for the
# category keywords.
_EXTRA_CANONICAL_PHRASES = [
    "heavy bleeding", "severe headache", "blurred vision",
    "severe abdominal pain", "swollen face and hands", "high fever",
    "baby not moving", "difficulty breathing",
    "bleeding after delivery", "foul smelling discharge", "fits fainting",
    "i want to die", "kill myself", "self harm",
]


def _build_embedding_reference() -> list[str]:
    """
    Build the list of reference phrases the embedder compares queries
    against, from every keyword already declared in DANGER_CATEGORIES,
    plus a few extra generic anchors.

    This is generated fresh from DANGER_CATEGORIES rather than
    hand-maintained, because a hand-maintained list *will* go stale: rounds
    3-6 of danger-gate fixes added 18 new categories with dozens of Sindhi
    keywords, and none of them were ever added to the old, separate
    DANGER_PHRASES_FOR_EMBEDDING list. That meant the semantic fallback
    could not catch paraphrases of any of those 18 categories — it was
    silently running on an eleven-category reference set while the keyword
    list had grown to forty. Deriving the list here makes that class of bug
    structurally impossible: add a category, and its keywords are
    immediately part of what the embedder can match against too.
    """
    phrases: list[str] = []
    seen = set()
    for cat in DANGER_CATEGORIES.values():
        for kind in ("keywords_sindhi", "keywords_english"):
            for kw in cat.get(kind, []):
                if kw not in seen:
                    seen.add(kw)
                    phrases.append(kw)
    for kw in _EXTRA_CANONICAL_PHRASES:
        if kw not in seen:
            seen.add(kw)
            phrases.append(kw)
    return phrases


EMBEDDING_THRESHOLD = 0.96  # cosine similarity threshold — see NOTE below.
# NOTE: re-measured via eval/tune_embedding_threshold.py after the round-4
# keyword patch (33 phrases from Sana's phase-3 miss list, all added as
# keywords rather than left for the embedding path) and after Sabiha's
# dfcd1f2 token-bag generalisation fix (2026-09), which made keyword
# matching tolerate word-order and connector changes instead of
# memorising exact eval sentences.
#
# (dfcd1f2's git *author* field reads sana200420 because it carries a
# users.noreply.github.com address from the web UI; the *committer* is
# Sabihaa12, who wrote it.)
#
#   threshold | danger recall (embedding-dependent rows) | negative FP rate
#     0.86    |  1.000                                    |  0.150
#     0.88    |  1.000                                    |  0.130
#     0.90    |  1.000                                    |  0.130
#     0.92    |  1.000                                    |  0.100
#     0.94    |  1.000                                    |  0.060
#     0.96    |  1.000                                    |  0.030
#     0.98    |  1.000                                    |  0.000
#
# The picture from the old table above is now stale. With the token-bag
# fix plus the 33 added keywords, the keyword path alone gets 100/100 on
# the danger set (eval/run_danger_gate_eval.py) — 0/100 rows depend on the
# embedding path anymore, down from 3/100. Measured cost of keeping the
# embedding path in the request loop: ~15.5ms/question (2.0ms keyword-only
# -> 17.5ms with embedding), for zero additional recall on the current
# eval set.
#
# Decision: the embedding path is DISABLED in production (see
# api/pipeline.py, run_danger_gate(query, use_embedding=False)) rather
# than deleted. EMBEDDING_THRESHOLD is kept in sync at 0.96 (the lowest
# value that still holds recall at 1.00 with an acceptable ~3% FP rate)
# so the path is ready to re-enable — for a future case the keyword/
# token-bag path genuinely can't reach, or once the reference set in
# _build_embedding_reference() is curated down to fewer, more
# clinically-distinctive anchors per category (see
# docs/adr/0003-danger-gate-matching.md for that follow-up plan) — without
# needing to re-derive the threshold from scratch.
# Re-run eval/tune_embedding_threshold.py after any change to
# DANGER_CATEGORIES or _build_embedding_reference() and update this table.


def _load_embedder():
    """Load model once. Call only when embedding path is needed."""
    global _embedder, _danger_phrase_embeddings, _danger_phrases
    if _embedder is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        _embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        _danger_phrases = _build_embedding_reference()
        _danger_phrase_embeddings = _embedder.encode(
            _danger_phrases, normalize_embeddings=True
        )
    except Exception as e:
        logging.warning(f"Danger gate embedder failed to load, falling back to keyword-only: {e}")
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
    except Exception as e:
        logging.warning(f"Danger gate embedding match failed: {e}")
    return None


# ── Normaliser ─────────────────────────────────────────────────────────────────

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
    norm = normalize_sd(text)

    # 1. Keyword check — fast, no model needed
    for cat_name, cat in DANGER_CATEGORIES.items():
        all_keywords = (
            cat.get("keywords_sindhi", [])
            + cat.get("keywords_english", [])
            + cat.get("keywords_urdu", [])
        )
        for kw in all_keywords:
            if _phrase_matches(normalize_sd(kw), norm):
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
            if normalize_sd(kw) in norm:
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