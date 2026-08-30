# NaariAI English FAQ Dataset — Build & Review Notes
**File:** `naariai_faq_english_v1.csv` · **500 rows** · Sana's two subtopics
**Status:** ⚠️ **NOT CLINICALLY REVIEWED.** Draft for reviewer sign-off, then Sindhi translation.

---

## What is in the file

Six columns exactly: `id`, `category`, `sub_category`, `question`, `answer`, `source`.
IDs are plain sequential numbers 1–500. The `source` column is a bare URL.

| ID range | Rows | Category | Sub-category |
|---|---:|---|---|
| 1–25 | 25 | Pregnancy & Maternal Health | Confirming & early pregnancy |
| 26–50 | 25 | Pregnancy & Maternal Health | Trimester-by-trimester care |
| 51–80 | 30 | Pregnancy & Maternal Health | Antenatal visits & tests |
| 81–110 | 30 | Pregnancy & Maternal Health | Pregnancy discomforts & symptoms |
| 111–140 | 30 | Pregnancy & Maternal Health | Pregnancy nutrition (iron, folic acid, diet) |
| 141–170 | 30 | Pregnancy & Maternal Health | Labour, delivery & where to give birth |
| 171–200 | 30 | Pregnancy & Maternal Health | Physical postpartum recovery |
| 201–230 | 30 | Pregnancy & Maternal Health | Breastfeeding & newborn basics |
| 231–250 | 20 | Pregnancy & Maternal Health | Pregnancy & postpartum danger signs |
| 251–282 | 32 | PCOS & Hormonal Health | What PCOS is & common symptoms |
| 283–314 | 32 | PCOS & Hormonal Health | Diagnosis & when to get checked |
| 315–346 | 32 | PCOS & Hormonal Health | PCOS and periods |
| 347–378 | 32 | PCOS & Hormonal Health | PCOS, weight & insulin resistance |
| 379–410 | 32 | PCOS & Hormonal Health | Skin & hair changes |
| 411–432 | 22 | PCOS & Hormonal Health | Thyroid & other hormonal imbalances |
| 433–466 | 34 | PCOS & Hormonal Health | Lifestyle management |
| 467–500 | 34 | PCOS & Hormonal Health | Myths about PCOS & hormones |

Sub-cluster scope follows `kb_category_boundaries.md`. Encoding is UTF-8 with BOM so Excel opens it cleanly.

---

## Sourcing rule used

**Every citation in the `source` column is a document that was actually retrieved and read during this build.** No URL was written from memory, and no citation was inferred. Answers were kept inside what the cited document actually supports.

The CSV carries the bare URL only. Here is what each one is, and how many rows it backs:

| Rows | Source | URL |
|---:|---|---|
| 110 | 2023 International Evidence-based Guideline for PCOS (Teede et al., *J Clin Endocrinol Metab* 2023;108(10):2447-2469) | https://academic.oup.com/jcem/article/108/10/2447/7242360 |
| 109 | WHO Fact Sheet — Polycystic ovary syndrome | https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome |
| 83 | WHO — Antenatal care for a positive pregnancy experience (2016) | https://www.who.int/news/item/07-11-2016-new-guidelines-on-antenatal-care-for-a-positive-pregnancy-experience |
| 47 | WHO Fact Sheet — Maternal mortality | https://www.who.int/news-room/fact-sheets/detail/maternal-mortality |
| 36 | WHO — Maternal and newborn care for a positive postnatal experience (2022) | https://www.who.int/news/item/30-03-2022-who-urges-quality-care-for-women-and-newborns-in-critical-first-weeks-after-childbirth |
| 26 | WHO Fact Sheet — Infant and young child feeding | https://www.who.int/news-room/fact-sheets/detail/infant-and-young-child-feeding |
| 25 | WHO Fact Sheet — Pre-eclampsia | https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia |
| 22 | WHO Fact Sheet — Anaemia | https://www.who.int/news-room/fact-sheets/detail/anaemia |
| 21 | WHO Fact Sheet — Menstrual health | https://www.who.int/news-room/fact-sheets/detail/menstrual-health |
| 13 | WHO Fact Sheet — Preterm birth | https://www.who.int/news-room/fact-sheets/detail/preterm-birth |
| 8 | American Thyroid Association 2026 Guidelines (preconception, pregnancy, postpartum) | https://www.thyroid.org/new-ata-guidelines-for-thyroid-disease-in-preconception-pregnancy-and-postpartum/ |

---

## Automated checks that passed

- 500 rows, no empty cells, no duplicate IDs
- **No duplicate questions** across the whole set (two were caught during the build and rewritten)
- Every `source` value resolves to an entry in the verified registry — no orphan citations
- **No medicine names and no doses appear in any answer** — this matches the agent system prompt rule in `kb_womens_health_sindhi.md` ("never name, recommend, or give the dose of any medicine")
- Answer length 22–50 words (avg 34.6), none over 70 — written short for faithful Sindhi translation
- Every symptom-reporting row in the danger-signs cluster escalates urgently; every explanatory row points to care

---

## Where the clinical reviewer should focus

**1. `Thyroid & other hormonal imbalances` (rows 411–432, 22 rows) — highest priority.**
The full ATA 2026 guideline text was not retrievable during this build, only its scope statement. These answers are deliberately kept general ("this is recognised, get tested, see a doctor") and contain no thresholds, no TSH values, no iodine amounts. A reviewer should add specifics or confirm the general level is acceptable. This cluster is 22 rows rather than the planned 30 for the same reason.

**2. Danger-sign rows (231–250).** Confirm the escalation wording matches the escalation script already in `kb_upload_sindhi.md`, so the agent behaves consistently whichever entry it retrieves.

**3. Rows where WHO guidance is population-level.** Some WHO figures are global (e.g. anaemia prevalence, maternal mortality ratios). Reviewer should decide whether to keep global figures or substitute Pakistan/Sindh figures where available.

**4. Medicine framing.** Several PCOS answers refer to treatments descriptively ("hormone tablets doctors use to regulate cycles") without naming or dosing them, per the agent safety rule. Confirm this is the right level for a knowledge base as opposed to an agent utterance.

---

## Notes for the Sindhi translation stage

- Answers are 2–4 short sentences, no medical jargon, written to be spoken aloud.
- Keep the escalation sentences intact — do not soften "go now" into "you may wish to go".
- Numbers are written as words ("ten to thirteen women in every hundred") rather than digits, because that is how they are spoken.
- Terms needing an agreed Sindhi rendering before translation starts: *insulin resistance*, *hirsutism*, *pre-eclampsia*, *antenatal contact*, *skilled birth attendant*, *polycystic*. Agree these once as a team so all four subtopics use the same word.

---

## Rebuilding the file

The dataset is generated from source files, not edited by hand. `build.py` assigns IDs, attaches citations from the verified registry, and runs the duplicate and orphan-citation checks on every build. To change a row, edit its sub-cluster file and rebuild — this keeps IDs and checks consistent across all four team members if the same method is used for the other six subtopics.
