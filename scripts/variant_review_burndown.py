"""Per-category human-review burn-down for the variant corpus.

docs/PLAYBOOKS.md, Risk 5: "data/variants/review_status.csv holds
per-category counts; a CI step writes a burn-down line into docs/status.md
on every push. Nobody has to be asked how it's going." Neither the file
nor the tracking mechanism existed until now -- this builds both.

This is deliberately a DIFFERENT signal from variant_queue_clean.csv's
existing `review_status` column (auto_ok / regenerate), which only means
"not padding, not an exact duplicate of the original question" -- an
automated check, not a person confirming a variant reads naturally in
Sindhi and actually fits its category. That's what `human_review_status`
(added to variant_queue_clean.csv alongside this script) tracks, and
what this burn-down measures: not_reviewed / approved / fix / drop, one
per variant row, filled in by whoever owns that category.

Ownership (docs/PLAYBOOKS.md, each person's own Phase 3 "review your own
two categories" line):
    Sana    -- Pregnancy & Maternal Health, PCOS & Hormonal Health
    Sabiha  -- Menstrual Health & Periods, Mental Health & Emotional Well-being
    Tooba   -- Fertility & Reproductive Health, Vaginal & Personal Hygiene
    Mahnoor -- Women's Nutrition & Health, Menopause & Menopausal Health

Note for whoever reads the first burn-down this produces: Sabiha's PR #32
approved data/variants/colloquial_variants.csv's 150-row smoke-test batch
for her two categories. That is a DIFFERENT file (superseded, see
docs/status.md) -- it does not count toward this tracker, which measures
the real 4,000-row corpus. Everyone starts at 0%, including her; that is
correct, not a bug in this script.

    python scripts/variant_review_burndown.py
"""
import sys

import pandas as pd

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass  # not all stdout streams support reconfigure (e.g. piped/redirected in some CI runners)

VARIANTS = "data/processed/variant_queue_clean.csv"
OUT_CSV = "data/variants/review_status.csv"

OWNER_OF_CATEGORY = {
    "حمل ۽ ماءُ جي صحت": "Sana",
    "پي سي او ايس ۽ هارموني صحت": "Sana",
    "حيض جي صحت ۽ مدت": "Sabiha",
    "ذهني صحت ۽ جذباتي ڀلائي": "Sabiha",
    "زرخيزي ۽ پيداواري صحت": "Tooba",
    "ويجنل ۽ ذاتي صفائي": "Tooba",
    "عورتن جي غذائيت ۽ صحت": "Mahnoor",
    "مينوپاز ۽ مينوپاسل صحت": "Mahnoor",
}

STATUSES = ("not_reviewed", "approved", "fix", "drop")


def build() -> pd.DataFrame:
    v = pd.read_csv(VARIANTS)
    if "human_review_status" not in v.columns:
        raise SystemExit(
            f"{VARIANTS} has no human_review_status column -- run the "
            f"column-add step in the commit that introduced this script first."
        )

    unknown_status = set(v.human_review_status.unique()) - set(STATUSES)
    if unknown_status:
        print(f"WARNING: unrecognised human_review_status values: {unknown_status}",
              file=sys.stderr)

    unmapped_cat = set(v.category.unique()) - set(OWNER_OF_CATEGORY)
    if unmapped_cat:
        raise SystemExit(
            f"category not in OWNER_OF_CATEGORY, add it before this can run: "
            f"{unmapped_cat}"
        )

    rows = []
    for category, group in v.groupby("category", sort=False):
        total = len(group)
        counts = group.human_review_status.value_counts()
        reviewed = total - counts.get("not_reviewed", 0)
        rows.append({
            "category": category,
            "owner": OWNER_OF_CATEGORY[category],
            "total_variants": total,
            "approved": int(counts.get("approved", 0)),
            "fix": int(counts.get("fix", 0)),
            "drop": int(counts.get("drop", 0)),
            "not_reviewed": int(counts.get("not_reviewed", 0)),
            "reviewed": int(reviewed),
            "percent_complete": round(100 * reviewed / total, 1) if total else 0.0,
        })

    out = pd.DataFrame(rows).sort_values("owner").reset_index(drop=True)
    return out


def main() -> int:
    out = build()
    out.to_csv(OUT_CSV, index=False, encoding="utf-8")

    print(f"{'owner':<8} {'category':<28} {'total':>6} {'reviewed':>9} {'%':>6}")
    for _, r in out.iterrows():
        print(f"{r.owner:<8} {r.category:<28} {r.total_variants:>6} "
              f"{r.reviewed:>9} {r.percent_complete:>5.1f}%")

    overall_total = out.total_variants.sum()
    overall_reviewed = out.reviewed.sum()
    overall_pct = round(100 * overall_reviewed / overall_total, 1) if overall_total else 0.0
    print(f"\noverall: {overall_reviewed}/{overall_total} ({overall_pct}%)")
    print(f"wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
