# Raw source CSVs

The four per-member FAQ files, 500 rows each, six columns:
`id, category, sub_category, question, answer, source`

| Member | Categories |
|---|---|
| Sana | Pregnancy & Maternal Health · PCOS & Hormonal Health |
| Tooba | Fertility & Reproductive Health · Vaginal & Personal Hygiene |
| Sabiha | Menstrual Health & Periods · Mental Health & Emotional Well-being |
| Mahnoor | Women's Nutrition & Wellness · Menopause & Menopausal Health |

The existing files currently live in `../../knowledge_base/`. Mahnoor's Phase 0
task moves them here and merges them into `../processed/naariai_faq_v1.csv`
via `scripts/build.py`.

Never hand-edit the merged file. Edit the source and rebuild.
