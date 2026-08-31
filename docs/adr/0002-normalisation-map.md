# ADR 0002 — Script normalisation map

**Status:** accepted · **Date:** 2026-08-30 · **Author:** Sana

Lever 1 from `docs/PLAYBOOKS.md`. One function, `retrieval.normalize.normalize_sd()`,
imported everywhere text is embedded, so index-time and query-time text are always
identical.

## Method

The map below was **not** copied from an Urdu normalisation table. Sindhi has 52
letters and several — ڏ ڄ ٺ ٿ ڪ ڳ ڱ ڃ ڻ ھ — are meaning-bearing in ways a generic
Urdu map would happily merge away. Instead:

1. Ran a codepoint frequency histogram over the `question` and `answer` columns of
   all 2,000 rows in `knowledge_base/Womens_Health_KB - 2000_final.csv`. Result:
   **145 distinct codepoints** (script generating this table:
   `retrieval/scripts/build_normalisation_table.py`).
2. For every codepoint, decided once: **keep**, **map to X**, or **drop**, with a
   reason. Full table below.
3. A handful of codepoints that don't appear in the corpus at all (zero-width
   characters, Arabic-Indic/Extended digits, plain Arabic Kaf) are mapped
   **defensively** anyway, because they're expected at query time — a phone
   keyboard or a different input method can produce characters an LLM-authored,
   already-cleaned KB never will. The corpus histogram tells you what the KB
   contains; it does not tell you what a real woman will type.

## Fixed pipeline order

```
1. NFC                                                (unicodedata.normalize)
2. strip zero-width characters (U+200B–U+200F, U+FEFF)
3. strip tatweel (U+0640)
4. remove harakat (U+064B–U+065F, U+0670)
5. apply the character map (below)
6. Arabic-Indic (U+0660–0669) and Extended Arabic-Indic (U+06F0–06F9) digits → ASCII
7. collapse whitespace
```

Order matters: NFC first so every later step sees a canonical representation;
harakat removed *before* the character map so a mapped base letter never ends up
carrying a stray diacritic; digit folding and whitespace collapse last because
they're insensitive to everything before them.

## Decisions that need explaining

**Sindhi-specific letters are never merged with anything.** ڏ ڄ ٺ ٿ ڪ ڳ ڱ ڃ ڻ ھ,
plus ڊ ڀ ٻ ڌ ڙ ڍ ڦ ڇ, are each kept as their own codepoint, distinct from every
Arabic/Urdu letter they visually resemble. This is the one rule a copied Urdu map
would violate first.

**ه / ھ / ہ are three different things, not typos of each other.**
`ه` (Heh, U+0647) is the plain letter (19,099 occurrences — the default).
`ھ` (Heh Doachashmee, U+06BE) marks aspirated consonant digraphs (بھ, پھ, تھ,
کھ, گھ) and is **kept separate** — collapsing it into `ه` would turn aspirated
and unaspirated consonants into the same string. `ہ` (Heh Goal, U+06C1, 58
occurrences) is the Urdu word-final form and has no comparable functional load in
Sindhi orthography here; at 58 uses against 19,099 for the plain letter, and given
every other Urdu-keyboard artifact in this corpus is similarly rare, it's mapped
to `ه`.

**ي / ی / ے / ى are unified into `ي`.** All three of the rare forms (89 + 5 + 1 =
95 occurrences) sit far below the dominant Yeh (46,012). This is a corpus-evidence
call, not a rule imported from Urdu conventions: Sindhi text overwhelmingly uses
`ي`, and the rare forms look like font/keyboard artifacts rather than a deliberate
second phoneme.

**ٹ (Urdu Tteh) → ٽ (Sindhi Teheh-with-3-dots), 1 occurrence.** Sindhi's alphabet
doesn't include `ٹ`; it uses `ٽ` for this sound (2,638 occurrences). One row typed
the Urdu letter instead of the Sindhi one — almost certainly an Urdu-keyboard
default. This is corrected *to* the correct Sindhi letter, which is the opposite
of what a naive Urdu map does (an Urdu map would merge `ٽ` *into* `ٹ`).

**ں (Noon Ghunna) is kept, flagged, not guessed at.** One occurrence, no
comparably clean single-character correction. Rather than force a mapping on weak
evidence, it's left alone. Revisit if it recurs once the colloquial variants
(Lever 2) land — more data may make the right call obvious.

**`.` and `۔` are NOT merged**, even though both are sentence-final punctuation
(2,681 and 1,602 occurrences respectively). The corpus uses `.` for **decimal
points** in numbers (`0.3`, `500mg+/day`) as well as sentence endings. Merging
them would turn `0.3` into `0۔3`, conflating a decimal point with a full stop —
a real meaning change for numeric content, for no retrieval benefit (punctuation
isn't a strong embedding signal either way). Both are kept, unmodified, as
themselves.

**ASCII letters are case-folded** (`A-Z` → `a-z`) because the corpus embeds
English medical acronyms inline (`uterine`, `HSG`, `IUI`, `IVF`, `BV`) and a user
typing `hsg` should match `HSG` in the KB. Arabic-script letters have no case, so
this fold only ever touches the Latin subset.

**Quotes and one stray comma are unified** (`‘ ’` → `'`, `“ ”` → `"` defensively,
`,` → `،`) — pure typography, no meaning distinction, and the corpus is
overwhelmingly Arabic-script punctuation already.

**۽ (Sindhi ampersand, "and") and ۾ (Sindhi postposition, "in") are untouched.**
Both are `So` (symbol) category, not letters, but function as words in Sindhi and
are extremely high-frequency (2,050 and 2,105). No decision needed beyond "don't
touch these."

## Full codepoint table (145 codepoints, all question+answer text, 2,000 rows)

| Codepoint | Char | Name | Count | Decision | Reason |
|---|---|---|---:|---|---|
| U+0020 |   | SPACE | 96816 | keep | word-separator space — kept as-is; collapsed at the whitespace step, not here |
| U+064A | ي | ARABIC LETTER YEH | 46012 | keep | dominant Sindhi Yeh — meaning-bearing, kept distinct |
| U+0627 | ا | ARABIC LETTER ALEF | 37318 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0646 | ن | ARABIC LETTER NOON | 26048 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0648 | و | ARABIC LETTER WAW | 23639 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0631 | ر | ARABIC LETTER REH | 21585 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0647 | ه | ARABIC LETTER HEH | 19099 | keep | plain Heh — see "ه/ھ/ہ" note above |
| U+0645 | م | ARABIC LETTER MEEM | 14408 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+062A | ت | ARABIC LETTER TEH | 13133 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+062C | ج | ARABIC LETTER JEEM | 12959 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+06AA | ڪ | ARABIC LETTER SWASH KAF | 11662 | keep | Sindhi Kaf — meaning-bearing, distinct from ک and (defensive) ك |
| U+0633 | س | ARABIC LETTER SEEN | 11276 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0644 | ل | ARABIC LETTER LAM | 9982 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+062F | د | ARABIC LETTER DAL | 7384 | keep | letter of the Sindhi alphabet — meaning-bearing, distinct from ڏ/ڊ/ڌ |
| U+0628 | ب | ARABIC LETTER BEH | 6386 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+067F | ٿ | ARABIC LETTER TEHEH | 5178 | keep | Sindhi-specific letter — meaning-bearing, never merged |
| U+062D | ح | ARABIC LETTER HAH | 4994 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0639 | ع | ARABIC LETTER AIN | 4912 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+06BB | ڻ | ARABIC LETTER RNOON | 4696 | keep | Sindhi-specific letter — meaning-bearing, never merged |
| U+06A9 | ک | ARABIC LETTER KEHEH | 4509 | keep | Sindhi letter — meaning-bearing, distinct from ڪ |
| U+0635 | ص | ARABIC LETTER SAD | 4385 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+06AF | گ | ARABIC LETTER GAF | 4369 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+060C | ، | ARABIC COMMA | 4315 | keep | punctuation — target of the ASCII-comma unification |
| U+067E | پ | ARABIC LETTER PEH | 4265 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0622 | آ | ARABIC LETTER ALEF WITH MADDA ABOVE | 4115 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0626 | ئ | ARABIC LETTER YEH WITH HAMZA ABOVE | 3843 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0634 | ش | ARABIC LETTER SHEEN | 3636 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+062E | خ | ARABIC LETTER KHAH | 2909 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+002E | . | FULL STOP | 2681 | keep | decimal point AND sentence end — see "." vs "۔" note above |
| U+067D | ٽ | ARABIC LETTER TEH WITH THREE DOTS ABOVE DOWNWARDS | 2638 | keep | Sindhi-specific letter — meaning-bearing, never merged; target of ٹ correction |
| U+0621 | ء | ARABIC LETTER HAMZA | 2339 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0637 | ط | ARABIC LETTER TAH | 2321 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0641 | ف | ARABIC LETTER FEH | 2150 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+06FE | ۾ | ARABIC SIGN SINDHI POSTPOSITION MEN | 2105 | keep | Sindhi grammatical marker ("in") — untouched |
| U+0687 | ڇ | ARABIC LETTER TCHEHEH | 2074 | keep | Sindhi-specific letter (used in ڇا, "what") — meaning-bearing |
| U+06FD | ۽ | ARABIC SIGN SINDHI AMPERSAND | 2050 | keep | Sindhi grammatical marker ("and") — untouched |
| U+061F | ؟ | ARABIC QUESTION MARK | 1999 | keep | punctuation — semantically neutral |
| U+0642 | ق | ARABIC LETTER QAF | 1983 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0632 | ز | ARABIC LETTER ZAIN | 1865 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+068F | ڏ | ARABIC LETTER DAL WITH THREE DOTS ABOVE DOWNWARDS | 1821 | keep | Sindhi-specific letter — meaning-bearing, never merged with د |
| U+0650 | *(nonprint)* | ARABIC KASRA | 1609 | **drop** | harakat — stripped by the fixed pipeline step |
| U+06D4 | ۔ | ARABIC FULL STOP | 1602 | keep | sentence end — see "." vs "۔" note above |
| U+0686 | چ | ARABIC LETTER TCHEH | 1460 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+06BE | ھ | ARABIC LETTER HEH DOACHASHMEE | 1417 | keep | aspiration marker — see "ه/ھ/ہ" note above, never merged |
| U+068A | ڊ | ARABIC LETTER DAL WITH DOT BELOW | 1347 | keep | Sindhi-specific letter — meaning-bearing, never merged with د |
| U+0630 | ذ | ARABIC LETTER THAL | 1263 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0680 | ڀ | ARABIC LETTER BEHEH | 1152 | keep | Sindhi-specific letter — meaning-bearing |
| U+067B | ٻ | ARABIC LETTER BEEH | 1115 | keep | Sindhi-specific letter — meaning-bearing |
| U+068C | ڌ | ARABIC LETTER DAHAL | 1101 | keep | Sindhi-specific letter — meaning-bearing, never merged with د |
| U+0636 | ض | ARABIC LETTER DAD | 1037 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0699 | ڙ | ARABIC LETTER REH WITH FOUR DOTS ABOVE | 1008 | keep | Sindhi-specific letter — meaning-bearing |
| U+06B3 | ڳ | ARABIC LETTER GUEH | 886 | keep | Sindhi-specific letter — meaning-bearing, never merged |
| U+063A | غ | ARABIC LETTER GHAIN | 696 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+062B | ث | ARABIC LETTER THEH | 655 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0638 | ظ | ARABIC LETTER ZAH | 558 | keep | letter of the Sindhi alphabet — meaning-bearing |
| U+0683 | ڃ | ARABIC LETTER NYEH | 545 | keep | Sindhi-specific letter — meaning-bearing, never merged |
| U+0684 | ڄ | ARABIC LETTER DYEH | 426 | keep | Sindhi-specific letter — meaning-bearing, never merged |
| U+067A | ٺ | ARABIC LETTER TTEHEH | 394 | keep | Sindhi-specific letter — meaning-bearing, never merged |
| U+064F | *(nonprint)* | ARABIC DAMMA | 279 | **drop** | harakat — stripped by the fixed pipeline step |
| U+006F | o | LATIN SMALL LETTER O | 259 | keep | embedded English term/acronym letter |
| U+064E | *(nonprint)* | ARABIC FATHA | 244 | **drop** | harakat — stripped by the fixed pipeline step |
| U+0069 | i | LATIN SMALL LETTER I | 228 | keep | embedded English term/acronym letter |
| U+0061 | a | LATIN SMALL LETTER A | 202 | keep | embedded English term/acronym letter |
| U+0074 | t | LATIN SMALL LETTER T | 183 | keep | embedded English term/acronym letter |
| U+006E | n | LATIN SMALL LETTER N | 180 | keep | embedded English term/acronym letter |
| U+0065 | e | LATIN SMALL LETTER E | 175 | keep | embedded English term/acronym letter |
| U+0028 | ( | LEFT PARENTHESIS | 173 | keep | punctuation — semantically neutral |
| U+0029 | ) | RIGHT PARENTHESIS | 173 | keep | punctuation — semantically neutral |
| U+068D | ڍ | ARABIC LETTER DDAHAL | 168 | keep | Sindhi-specific letter — meaning-bearing |
| U+0049 | I | LATIN CAPITAL LETTER I | 141 | map → `i` | ASCII case fold |
| U+006C | l | LATIN SMALL LETTER L | 139 | keep | embedded English term/acronym letter |
| U+0072 | r | LATIN SMALL LETTER R | 138 | keep | embedded English term/acronym letter |
| U+0075 | u | LATIN SMALL LETTER U | 129 | keep | embedded English term/acronym letter |
| U+0073 | s | LATIN SMALL LETTER S | 124 | keep | embedded English term/acronym letter |
| U+061B | ؛ | ARABIC SEMICOLON | 119 | keep | punctuation — semantically neutral |
| U+0076 | v | LATIN SMALL LETTER V | 118 | keep | embedded English term/acronym letter |
| U+0054 | T | LATIN CAPITAL LETTER T | 94 | map → `t` | ASCII case fold |
| U+06CC | ی | ARABIC LETTER FARSI YEH | 89 | map → `ي` | rare variant of dominant Yeh — see note above |
| U+0053 | S | LATIN CAPITAL LETTER S | 72 | map → `s` | ASCII case fold |
| U+0055 | U | LATIN CAPITAL LETTER U | 71 | map → `u` | ASCII case fold |
| U+0031 | 1 | DIGIT ONE | 65 | keep | ASCII digit, already target form |
| U+003A | : | COLON | 65 | keep | punctuation — semantically neutral |
| U+06A6 | ڦ | ARABIC LETTER PEHEH | 64 | keep | Sindhi-specific letter — meaning-bearing |
| U+0032 | 2 | DIGIT TWO | 62 | keep | ASCII digit, already target form |
| U+002D | - | HYPHEN-MINUS | 61 | keep | punctuation — semantically neutral |
| U+0027 | ' | APOSTROPHE | 59 | keep | punctuation — target of curly-quote unification |
| U+06C1 | ہ | ARABIC LETTER HEH GOAL | 58 | map → `ه` | Urdu artifact — see "ه/ھ/ہ" note above |
| U+064C | *(nonprint)* | ARABIC DAMMATAN | 58 | **drop** | harakat — stripped by the fixed pipeline step |
| U+0030 | 0 | DIGIT ZERO | 56 | keep | ASCII digit, already target form |
| U+0064 | d | LATIN SMALL LETTER D | 56 | keep | embedded English term/acronym letter |
| U+006D | m | LATIN SMALL LETTER M | 55 | keep | embedded English term/acronym letter |
| U+0063 | c | LATIN SMALL LETTER C | 54 | keep | embedded English term/acronym letter |
| U+064B | *(nonprint)* | ARABIC FATHATAN | 49 | **drop** | harakat — stripped by the fixed pipeline step |
| U+0035 | 5 | DIGIT FIVE | 47 | keep | ASCII digit, already target form |
| U+0033 | 3 | DIGIT THREE | 39 | keep | ASCII digit, already target form |
| U+0070 | p | LATIN SMALL LETTER P | 38 | keep | embedded English term/acronym letter |
| U+0056 | V | LATIN CAPITAL LETTER V | 37 | map → `v` | ASCII case fold |
| U+0044 | D | LATIN CAPITAL LETTER D | 36 | map → `d` | ASCII case fold |
| U+0034 | 4 | DIGIT FOUR | 34 | keep | ASCII digit, already target form |
| U+0068 | h | LATIN SMALL LETTER H | 33 | keep | embedded English term/acronym letter |
| U+0079 | y | LATIN SMALL LETTER Y | 33 | keep | embedded English term/acronym letter |
| U+0038 | 8 | DIGIT EIGHT | 32 | keep | ASCII digit, already target form |
| U+0042 | B | LATIN CAPITAL LETTER B | 31 | map → `b` | ASCII case fold |
| U+0067 | g | LATIN SMALL LETTER G | 30 | keep | embedded English term/acronym letter |
| U+0048 | H | LATIN CAPITAL LETTER H | 28 | map → `h` | ASCII case fold |
| U+0050 | P | LATIN CAPITAL LETTER P | 26 | map → `p` | ASCII case fold |
| U+0624 | ؤ | ARABIC LETTER WAW WITH HAMZA ABOVE | 22 | keep | legitimate low-frequency letter — not a variant to merge |
| U+0043 | C | LATIN CAPITAL LETTER C | 21 | map → `c` | ASCII case fold |
| U+0036 | 6 | DIGIT SIX | 20 | keep | ASCII digit, already target form |
| U+0066 | f | LATIN SMALL LETTER F | 19 | keep | embedded English term/acronym letter |
| U+0062 | b | LATIN SMALL LETTER B | 19 | keep | embedded English term/acronym letter |
| U+0046 | F | LATIN CAPITAL LETTER F | 16 | map → `f` | ASCII case fold |
| U+004F | O | LATIN CAPITAL LETTER O | 14 | map → `o` | ASCII case fold |
| U+0045 | E | LATIN CAPITAL LETTER E | 13 | map → `e` | ASCII case fold |
| U+0037 | 7 | DIGIT SEVEN | 10 | keep | ASCII digit, already target form |
| U+004D | M | LATIN CAPITAL LETTER M | 9 | map → `m` | ASCII case fold |
| U+0041 | A | LATIN CAPITAL LETTER A | 9 | map → `a` | ASCII case fold |
| U+06B1 | ڱ | ARABIC LETTER NGOEH | 9 | keep | Sindhi-specific letter — meaning-bearing, never merged |
| U+006B | k | LATIN SMALL LETTER K | 8 | keep | embedded English term/acronym letter |
| U+0039 | 9 | DIGIT NINE | 7 | keep | ASCII digit, already target form |
| U+004C | L | LATIN CAPITAL LETTER L | 6 | map → `l` | ASCII case fold |
| U+002F | / | SOLIDUS | 6 | keep | punctuation — semantically neutral |
| U+2019 | ' | RIGHT SINGLE QUOTATION MARK | 5 | map → `'` | curly-quote unification |
| U+2018 | ' | LEFT SINGLE QUOTATION MARK | 5 | map → `'` | curly-quote unification |
| U+06D2 | ے | ARABIC LETTER YEH BARREE | 5 | map → `ي` | rare variant of dominant Yeh |
| U+0077 | w | LATIN SMALL LETTER W | 5 | keep | embedded English term/acronym letter |
| U+004E | N | LATIN CAPITAL LETTER N | 4 | map → `n` | ASCII case fold |
| U+0057 | W | LATIN CAPITAL LETTER W | 4 | map → `w` | ASCII case fold |
| U+0691 | ڑ | ARABIC LETTER RREH | 4 | keep | letter — meaning-bearing |
| U+0640 | ـ | ARABIC TATWEEL | 4 | **drop** | tatweel — stripped by the fixed pipeline step |
| U+0651 | *(nonprint)* | ARABIC SHADDA | 4 | **drop** | harakat — stripped by the fixed pipeline step |
| U+007A | z | LATIN SMALL LETTER Z | 4 | keep | embedded English term/acronym letter |
| U+0670 | *(nonprint)* | ARABIC LETTER SUPERSCRIPT ALEF | 3 | **drop** | harakat — stripped by the fixed pipeline step |
| U+0078 | x | LATIN SMALL LETTER X | 3 | keep | embedded English term/acronym letter |
| U+004B | K | LATIN CAPITAL LETTER K | 3 | map → `k` | ASCII case fold |
| U+002C | , | COMMA | 3 | map → `،` | ASCII comma is rare here — unified to the dominant Arabic comma |
| U+0047 | G | LATIN CAPITAL LETTER G | 3 | map → `g` | ASCII case fold |
| U+002B | + | PLUS SIGN | 2 | keep | legitimate symbol (e.g. "500mg+/day") |
| U+00B0 | ° | DEGREE SIGN | 1 | keep | legitimate symbol (temperature) |
| U+0679 | ٹ | ARABIC LETTER TTEH | 1 | map → `ٽ` | Urdu-keyboard slip — see note above |
| U+06BA | ں | ARABIC LETTER NOON GHUNNA | 1 | keep (flagged) | 1 occurrence, no confident mapping — see note above |
| U+066A | ٪ | ARABIC PERCENT SIGN | 1 | map → `%` | folded to ASCII, consistent with digit folding |
| U+0058 | X | LATIN CAPITAL LETTER X | 1 | map → `x` | ASCII case fold |
| U+0059 | Y | LATIN CAPITAL LETTER Y | 1 | map → `y` | ASCII case fold |
| U+0649 | ى | ARABIC LETTER ALEF MAKSURA | 1 | map → `ي` | 1 occurrence, typo/variant of dominant Yeh |

**Defensive additions not present in the corpus** (kept out of the table above
since there's no row to attach them to, but implemented in `normalize.py` because
they're well-known query-time risks):

| Codepoint(s) | Maps to | Why |
|---|---|---|
| U+0643 (ك, plain Arabic Kaf) | ڪ (U+06AA) | Common Arabic/Urdu-keyboard substitute for Sindhi's own Kaf; never appears in the LLM-authored KB but plausible from a phone keyboard |
| U+0660–0669 (Arabic-Indic digits) | ASCII 0–9 | Some phone keyboards default to these |
| U+06F0–06F9 (Extended Arabic-Indic / Urdu digits) | ASCII 0–9 | Same, Urdu-keyboard variant |
| U+200B–U+200F, U+FEFF (zero-width chars) | stripped | WhatsApp/browser autocorrect commonly inserts these invisibly |

## Recall@5 with/without normalisation

**Not yet measured — blocked on embeddings and a gold query set, neither of which
exist yet.** This ADR will be updated with the number once the Phase 1 dense
baseline (`retrieval/embed.py` + Qdrant collection) and Mahnoor's first 100 gold
queries land. Tracked as the remaining open item on this ADR.

## Tests

`retrieval/tests/test_normalize.py`:
- **Idempotence** — `normalize_sd(normalize_sd(x)) == normalize_sd(x)` for all
  4,000 question+answer strings in the corpus.
- **Golden fixtures** — 47 hand-written `(raw, expected)` pairs covering every
  pipeline step, mixed keyboard layouts, Roman Sindhi, and trailing Urdu
  punctuation.
- **Non-destruction** — no two distinct KB questions normalise to the same
  string, checked against all 2,000 rows.

Run with `pytest retrieval/`.
