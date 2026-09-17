"""Script normalisation for Sindhi text.

One function, `normalize_sd`, imported everywhere text is embedded. See
`docs/adr/0002-normalisation-map.md` for the corpus analysis and reasoning
behind every mapping below — this file should not be edited without updating
that ADR.

Pipeline, in this fixed order:
    1. NFC
    2. strip zero-width characters
    3. strip tatweel
    4. remove harakat
    5. apply the character map
    6. Arabic-Indic / Extended Arabic-Indic digits -> ASCII
    7. collapse whitespace
"""

import re
import unicodedata

# U+200B ZWSP, U+200C ZWNJ, U+200D ZWJ, U+200E LRM, U+200F RLM, U+FEFF BOM.
# These characters are invisible in a normal editor; verify with
# [hex(ord(c)) for c in _ZERO_WIDTH] rather than trusting how this looks.
_ZERO_WIDTH = "​‌‍‎‏﻿"
_TATWEEL = "ـ"  # ARABIC TATWEEL

# U+064B-U+065F plus U+0670, per the ADR.
_HARAKAT = "".join(chr(c) for c in range(0x064B, 0x0660)) + "ٰ"

_STRIP_TABLE = str.maketrans("", "", _ZERO_WIDTH + _TATWEEL + _HARAKAT)

# Single-character substitutions decided in docs/adr/0002-normalisation-map.md.
_CHAR_MAP = {
    # Yeh variants -> dominant Sindhi Yeh
    "ی": "ي",  # Farsi Yeh -> Yeh
    "ے": "ي",  # Yeh Barree -> Yeh
    "ى": "ي",  # Alef Maksura -> Yeh
    # Heh variants: only the Urdu word-final form is merged; Doachashmee Heh
    # (aspiration marker) is deliberately left alone.
    "ہ": "ه",  # Heh Goal -> Heh
    # Urdu-keyboard slip corrected to Sindhi's own letter.
    "ٹ": "ٽ",  # Tteh -> Teheh-with-3-dots
    # Defensive: plain Arabic Kaf is a common keyboard substitute for Sindhi's
    # own Kaf, even though it never appears in the LLM-authored KB itself.
    "ك": "ڪ",  # Kaf -> Swash Kaf
    # Typographic quote/comma unification.
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    ",": "،",  # ASCII comma -> Arabic comma
    # Arabic percent sign folded to ASCII, consistent with digit folding.
    "٪": "%",
}

# Arabic-Indic (U+0660-0669) and Extended Arabic-Indic / Urdu (U+06F0-06F9)
# digits -> ASCII. Not present in the KB corpus but expected at query time.
_DIGIT_MAP = {}
for _i in range(10):
    _DIGIT_MAP[chr(0x0660 + _i)] = str(_i)
    _DIGIT_MAP[chr(0x06F0 + _i)] = str(_i)

_TRANSLATE_TABLE = str.maketrans({**_CHAR_MAP, **_DIGIT_MAP})

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_sd(text: str) -> str:
    """Normalise Sindhi (or mixed Sindhi/English) text for embedding.

    Idempotent: normalize_sd(normalize_sd(x)) == normalize_sd(x).
    """
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_STRIP_TABLE)
    text = text.translate(_TRANSLATE_TABLE)
    text = text.lower()
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text
