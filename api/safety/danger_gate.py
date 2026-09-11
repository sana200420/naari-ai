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
import logging
from retrieval.normalize import normalize_sd
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
            "ويم کان پوءِ گهڻو رت وهڻ", "پيڊ ڀرجي وڃي", "پيڊ پوريءَ ريت ڀرجي وڃي",
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
        ],
        "keywords_english": [
            "abdominal pain large bruise blood thinner fall", "internal bleeding on blood thinners",
        ],
        "keywords_urdu": ["گرنے کے بعد پیٹ میں درد بڑا نیل خون پتلا کرنے والی دوا"]
    },
    "cord_prolapse": {
        "description": "Water breaks with a cord-like structure felt/visible before labor pain starts",
        "keywords_sindhi": [
            "پاڻي جي ٿيلهي ڦاٽي پئي آهي ۽ هيٺان هڪ ناڙيءَ جهڙي شيءِ ٻاهر نڪرندي محسوس ٿئي ٿي",
        ],
        "keywords_english": [
            "cord prolapse water broke", "something coming out after water breaks",
        ],
        "keywords_urdu": ["پانی ٹوٹنے کے بعد نال جیسی چیز باہر آنا"]
    },
    "placental_abruption": {
        "description": "Board-like rigid abdomen with dark bleeding, or blunt trauma with dark bleeding, in later pregnancy",
        "keywords_sindhi": [
            "پيٽ ڳاڙهي ڪاٺيءَ وانگر سخت ۽ پٿر ٿي ويو آهي ۽ گهاٽو رت اچي رهيو آهي",
            "ڏاڪڻين تان ٻکربائي پوڻ سبب پيٽ تي سخت ڌڪ لڳو آهي ۽ هلڪو ڪارو گهاٽو رت نڪري رهيو آهي",
            "پيٽ بلڪل پٿر وانگر سخت ٿي ويو آهي ۽ موٽي نرم نٿو ٿئي",
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
            if normalize_sd(kw) in norm:
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