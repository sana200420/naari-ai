"""Replace foods a woman in rural Sindh cannot buy with ones she can.

The nutrition answers were written from Western dietary guidance and then
translated, so the Sindhi carries transliterated English food names --
ڪوئنو (quinoa), ٽوفو (tofu), ايوڪاڊو (avocado), سالمن (salmon),
چيا سيڊز (chia seeds). Those are not merely unavailable in a village; the
words themselves carry no meaning for the reader. An answer naming them is
worse than unhelpful, because the high-confidence path serves KB text
verbatim, so the user sees it exactly as stored.

Every substitution below keeps the *nutritional claim* intact and swaps only
the food carrying it: mustard oil is a genuine unsaturated fat, palla and rohu
are genuine omega-3 fish, jaggery and lentils are genuine iron sources. No
clinical statement, dose, or disclaimer is touched.

Only the answers change. Questions are what get embedded into Qdrant
(retrieval/scripts/embed_and_index.ipynb embeds `normalised_questions`), and
answers live in the point payload -- so this needs a payload update, not a
re-embed. See scripts/sync_kb_payloads.py.

Writes a side-by-side proposal to data/processed/nutrition_localisation.csv
for review before anything is trusted in a demo. The Sindhi wording still
wants a native speaker's eye; the substitutions are conservative for that
reason.

    python scripts/localise_nutrition_answers.py --dry-run
    python scripts/localise_nutrition_answers.py --apply
"""

import argparse
import os
import re
import sys

import pandas as pd

SD_KB = os.path.join("knowledge_base", "Womens_Health_KB - 2000_final.csv")
EN_KB = os.path.join("knowledge_base", "Womens_Health_KB_English - 2000_final.csv")
PROPOSAL = os.path.join("data", "processed", "nutrition_localisation.csv")

# (english_phrase, sindhi_phrase, replacement_en, replacement_sd, why)
SUBS = [
    ("quinoa",            "ڪوئنو",          "millet (bajra)",      "باجرو",
     "quinoa is not sold in rural Sindh; bajra is a staple whole grain"),
    ("whole grain pasta", "سڄو اناج پاستا", "sorghum (jowar)",     "جوئر",
     "pasta is urban and imported; jowar is grown locally"),
    ("tofu",              "ٽوفو",           "chickpeas",           "چڻا",
     "tofu is unavailable; chickpeas carry the same protein/calcium role"),
    ("avocados",          "ايوڪاڊو",        "peanuts",             "مونگ ڦلي",
     "avocado is imported and costly; peanuts are a local unsaturated fat"),
    ("olive oil",         "زيتون جو تيل",   "mustard oil",         "سرسون جو تيل",
     "mustard oil is the everyday cooking oil of Sindh and is unsaturated"),
    ("salmon",            "سالمن",          "palla fish",          "پلو",
     "palla is the Indus river fish; salmon does not exist here"),
    ("sardines",          "سارڊين",         "rohu fish",           "رهو",
     "rohu is the common local fish"),
    ("flaxseeds",         "فلڪس سيڊز",      "linseed (alsi)",      "السي",
     "where the Sindhi transliterated it, swap to the name it is sold under"),
    ("chia seeds",        "چيا سيڊز",       "sesame (til)",        "تِر",
     "chia is unavailable; til is a local omega-3 and calcium seed"),
    ("walnuts",           "اخروٽ",          "peanuts",             "مونگ ڦلي",
     "walnuts are expensive; peanuts are affordable and local"),
    # The Sindhi here is not a translation of "kale" -- ڪيلي means *banana*.
    # Gated on the English term, so this only fires in rows that really do
    # recommend kale.
    ("kale",              "ڪيلي",           "local greens (saag)", "ساڳ",
     "kale is unknown, and the Sindhi mistranslates it as banana; saag is the everyday green"),
    ("fortified orange juice", "مضبوط نارنجي جوس", "yoghurt",      "ڏهي",
     "fortified juice is not sold; yoghurt is a real local calcium source"),
    ("iron-fortified cereals", "لوھ سان ڀريل اناج", "jaggery (gur)", "ڳُڙ",
     "fortified cereal is a supermarket product; gur is iron-rich and universal"),
    # "fortified" was rendered قلعي وارا -- "castle-like" -- reading the English
    # as in a fort. The phrase is meaningless to a reader either way.
    ("fortified plant milks", "قلعي وارا ٻوٽن جو کير", "milk and yoghurt", "ڏُڌ ۽ ڏهي",
     "plant milks are unavailable, and the Sindhi renders 'fortified' as 'castle-like'"),
    # the same phrase appears with a second spelling of "plant"
    ("fortified plant milks", "قلعي وارا ٻوٽا کير", "milk and yoghurt", "ڏُڌ ۽ ڏهي",
     "second spelling of the same mistranslated phrase"),
    # السي is already the correct local word for flaxseed, so the Sindhi needs
    # no change -- only the English label is normalised.
    ("flaxseeds",         "",               "linseed (alsi)",      "",
     "alsi is available; the Sindhi already says السي and is left alone"),
]


def _en_hits(answer_en: str) -> list[tuple]:
    """Which substitutions this row genuinely calls for, judged on the English.

    The English side is the gate for both languages. A naive substring match on
    the Sindhi is unsafe: ڪيل ("kale") is also the everyday past participle
    "done/made", so it appears inside تجويز ڪيل ("recommended") and اڪيلو
    ("alone"). Matching it directly rewrote 20+ unrelated health answers in a
    dry run -- "recommended preventive screening" would have become nonsense.
    Gating on the English row confines every edit to answers that really do
    recommend the food.
    """
    low = str(answer_en).lower()
    hits = []
    for sub in SUBS:
        en = sub[0].lower()
        # A word boundary is meaningless against Arabic script but correct here: the gate
        # is always the English term.
        if re.search(rf"\b{re.escape(en)}\b", low):
            hits.append(sub)
    return hits


def apply_subs(text: str, lang: str, subs: list[tuple]) -> tuple[str, list[str]]:
    """Apply only the given substitutions. Returns (new_text, labels)."""
    out, applied = str(text), []
    for en, sd, rep_en, rep_sd, _why in subs:
        needle, repl = (en, rep_en) if lang == "en" else (sd, rep_sd)
        if not needle:
            continue
        if lang == "en":
            new = re.sub(rf"\b{re.escape(needle)}\b", repl, out, flags=re.I)
        else:
            new = out.replace(needle, repl)
        if new != out:
            out = new
            applied.append(en)
    return out, applied


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the KB files")
    ap.add_argument("--dry-run", action="store_true", help="report only (default)")
    args = ap.parse_args()

    sd = pd.read_csv(SD_KB)
    en = pd.read_csv(EN_KB)
    assert (sd.id.values == en.id.values).all(), "KB files are not id-aligned"

    rows = []
    for idx in range(len(en)):
        wanted = _en_hits(en.at[idx, "answer"])
        if not wanted:
            continue
        new_en, hit_en = apply_subs(en.at[idx, "answer"], "en", wanted)
        new_sd, hit_sd = apply_subs(sd.at[idx, "answer"], "sd", wanted)
        if not hit_en and not hit_sd:
            continue
        rows.append({
            "id": int(en.at[idx, "id"]),
            "category": en.at[idx, "category"],
            "substitutions": "; ".join(sorted(set(hit_en) | set(hit_sd))),
            "sd_not_matched": "; ".join(sorted(set(hit_en) - set(hit_sd))),
            "en_before": en.at[idx, "answer"],
            "en_after": new_en,
            "sd_before": sd.at[idx, "answer"],
            "sd_after": new_sd,
        })
        en.at[idx, "answer"] = new_en
        sd.at[idx, "answer"] = new_sd

    proposal = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(PROPOSAL), exist_ok=True)
    proposal.to_csv(PROPOSAL, index=False, encoding="utf-8")

    print(f"rows affected: {len(proposal)}")
    for _, r in proposal.iterrows():
        print(f"  id {r.id:4}  {r.substitutions}")
    print(f"\nproposal written to {PROPOSAL}")

    if args.apply:
        en.to_csv(EN_KB, index=False, encoding="utf-8")
        sd.to_csv(SD_KB, index=False, encoding="utf-8")
        print(f"applied to {EN_KB} and {SD_KB}")
        print("next: python scripts/sync_kb_payloads.py  (updates Qdrant payloads)")
    else:
        print("dry run -- no KB file written. Re-run with --apply to commit the change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
