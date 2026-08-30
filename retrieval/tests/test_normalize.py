"""Tests for retrieval.normalize.normalize_sd.

Three test classes, per docs/adr/0002-normalisation-map.md:
    - idempotence over the whole KB corpus
    - ~40 hand-written golden (raw, expected) fixtures
    - non-destruction: no two distinct KB questions collide after normalising
"""

import csv
from pathlib import Path

import pytest

from retrieval.normalize import normalize_sd

KB_PATH = (
    Path(__file__).resolve().parents[2]
    / "knowledge_base"
    / "Womens_Health_KB - 2000_final.csv"
)


def _load_kb_rows():
    with open(KB_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------------

def test_idempotence_over_full_corpus():
    rows = _load_kb_rows()
    assert len(rows) == 2000

    checked = 0
    for row in rows:
        for field in ("question", "answer"):
            text = row[field]
            once = normalize_sd(text)
            twice = normalize_sd(once)
            assert once == twice, f"not idempotent on id={row['id']} field={field}"
            checked += 1
    assert checked == 4000


def test_idempotence_on_empty_and_whitespace_only():
    for raw in ["", "   ", "\t\n\t", "۔۔۔"]:
        once = normalize_sd(raw)
        assert once == normalize_sd(once)


# ---------------------------------------------------------------------------
# Golden fixtures
# ---------------------------------------------------------------------------

# Harakat/tatweel/zero-width cases are built from explicit codepoints (chr())
# rather than typed literally, since they are invisible or near-invisible and
# cannot be proofread by eye.
_FATHA = chr(0x064E)
_DAMMA = chr(0x064F)
_KASRA = chr(0x0650)
_SHADDA = chr(0x0651)
_SUKUN = chr(0x0652)
_FATHATAN = chr(0x064B)
_DAMMATAN = chr(0x064C)
_SUPERSCRIPT_ALEF = chr(0x0670)
_TATWEEL = chr(0x0640)
_ZWSP = chr(0x200B)
_ZWNJ = chr(0x200C)
_ZWJ = chr(0x200D)
_LRM = chr(0x200E)
_RLM = chr(0x200F)
_BOM = chr(0xFEFF)

GOLDEN = [
    # --- harakat removal ---
    ("bare consonant untouched", "حيض", "حيض"),
    ("single fatha stripped", "حَيض", "حيض"),
    ("single kasra stripped", "حِيض", "حيض"),
    ("single damma stripped", "حُيض", "حيض"),
    ("shadda stripped", "درّ", "در"),
    ("sukun stripped", "دْر", "در"),
    ("fathatan stripped", "شکراً", "شکرا"),
    ("dammatan stripped", "کتابٌ", "کتابٌ".replace(_DAMMATAN, "")),
    ("superscript alef stripped", "هٰذا", "هذا"),
    ("multiple harakat in one word stripped",
     "مُتَعَدِّد", "متعدد"),

    # --- tatweel removal ---
    ("single tatweel stripped", "حـيض", "حيض"),
    ("repeated tatweel stripped", "حـــيض", "حيض"),

    # --- zero-width characters stripped ---
    ("ZWSP stripped", f"حيض{_ZWSP}جي", "حيضجي"),
    ("ZWNJ stripped", f"حيض{_ZWNJ}جي", "حيضجي"),
    ("ZWJ stripped", f"حيض{_ZWJ}جي", "حيضجي"),
    ("LRM stripped", f"حيض{_LRM}", "حيض"),
    ("RLM stripped", f"{_RLM}حيض", "حيض"),
    ("BOM stripped", f"{_BOM}حيض", "حيض"),

    # --- Yeh-family unification ---
    ("Farsi Yeh -> Yeh", "کیا", "کيا"),
    ("Yeh Barree -> Yeh", "بھلے", "بھلي"),
    ("Alef Maksura -> Yeh", "علىسبيل", "عليسبيل"),

    # --- Heh-family: only Heh Goal merges, Doachashmee stays separate ---
    ("Heh Goal -> Heh", "وہ", "وه"),
    ("Doachashmee Heh NOT merged into plain Heh", "گھر", "گھر"),

    # --- Kaf / Tteh corrections ---
    ("plain Arabic Kaf -> Sindhi Swash Kaf", "كتاب", "ڪتاب"),
    ("Urdu Tteh -> Sindhi Teheh-with-3-dots", "ٹيهه", "ٽيهه"),

    # --- quotes and comma ---
    ("curly single quotes -> straight apostrophe",
     "‘مختصر’", "'مختصر'"),
    ("curly double quotes -> straight quote",
     "“عام”", '"عام"'),
    ("ASCII comma -> Arabic comma", "هڪ، ٻيو، ٽيون",
     "هڪ، ٻيو، ٽيون"),
    ("ASCII comma literally becomes Arabic comma", "a,b", "a،b"),

    # --- percent sign ---
    ("Arabic percent -> ASCII percent", "٪50", "%50"),

    # --- digit folding ---
    ("Arabic-Indic digits -> ASCII", "٠١٢٣٤٥٦٧٨٩", "0123456789"),
    ("Extended Arabic-Indic digits -> ASCII", "۰۱۲۳۴۵۶۷۸۹", "0123456789"),
    ("ASCII digits already correct, untouched", "12345", "12345"),

    # --- case folding on embedded English ---
    ("uppercase acronym folded", "HSG ٽيسٽ", "hsg ٽيسٽ"),
    ("mixed-case word folded", "Uterine", "uterine"),
    ("already-lowercase untouched", "ivf", "ivf"),

    # --- whitespace collapsing ---
    ("multiple spaces collapsed", "حيض   جي   صحت", "حيض جي صحت"),
    ("tabs and newlines collapsed", "حيض\t\nجي", "حيض جي"),
    ("leading/trailing whitespace stripped", "  حيض جي صحت  ",
     "حيض جي صحت"),

    # --- meaning-bearing Sindhi letters must never change ---
    ("Sindhi implosives untouched", "ڏڄٺٿڪڳڱڃڻ", "ڏڄٺٿڪڳڱڃڻ"),
    ("Sindhi ampersand untouched", "حيض ۽ مدت", "حيض ۽ مدت"),
    ("Sindhi postposition untouched", "دور ۾", "دور ۾"),

    # --- decimal point vs sentence-final stop must stay distinct ---
    ("decimal point not merged with Arabic full stop",
     "0.3 کان 0.5", "0.3 کان 0.5"),
    ("Arabic full stop kept as itself", "بس۔", "بس۔"),

    # --- composite / realistic messy input ---
    ("mixed Urdu-keyboard input (ی، ہ، ٹ together)",
     "یہ ایک ٹيسٽ ہے", "يه ايک ٽيسٽ هي"),
    ("Roman Sindhi passes through, only lowercased + whitespace-collapsed",
     "Mahewari   Jaa Dinh", "mahewari jaa dinh"),
    ("harakat + tatweel + extra whitespace combined",
     f"حَـيض   جِي", "حيض جي"),
]


@pytest.mark.parametrize("label,raw,expected", GOLDEN, ids=[g[0] for g in GOLDEN])
def test_golden_fixtures(label, raw, expected):
    assert normalize_sd(raw) == expected, label


def test_golden_fixture_count_at_least_40():
    assert len(GOLDEN) >= 40


# ---------------------------------------------------------------------------
# Non-destruction
# ---------------------------------------------------------------------------

def test_non_destruction_no_new_collisions_across_kb_questions():
    rows = _load_kb_rows()
    raw_questions = [row["question"] for row in rows]

    # Sanity check: the raw corpus itself has no duplicate questions before
    # normalisation touches anything (this was fixed upstream in the KB).
    assert len(set(raw_questions)) == len(raw_questions)

    normalised = [normalize_sd(q) for q in raw_questions]
    seen = {}
    collisions = []
    for row, norm in zip(rows, normalised):
        if norm in seen:
            collisions.append((seen[norm], row["id"], norm))
        else:
            seen[norm] = row["id"]

    assert collisions == [], f"{len(collisions)} normalisation collisions: {collisions[:5]}"
