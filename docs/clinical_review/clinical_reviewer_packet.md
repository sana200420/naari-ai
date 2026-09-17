# NaariAI Sindhi KB — Clinical Reviewer Packet
## ⚠️ STATUS: PENDING CLINICAL REVIEW — NOT YET APPROVED

No item in this packet has been reviewed, corrected, or signed off by a doctor or LHW (Lady Health Worker) supervisor. Nothing here should be treated as clinically approved or pushed to production until the sign-off section at the end is completed by a qualified reviewer.

---

## 1. Project / Review Purpose

This packet supports **Phase 4: Clinical Review and Pilot** of the NaariAI Sindhi-language women's health voice assistant. The assistant answers spoken Sindhi questions from its knowledge base (KB); before pilot deployment, every answer that could involve a medical judgment call — and especially every answer touching thyroid/hormonal conditions or pregnancy/postpartum emergencies — needs sign-off from a doctor or LHW supervisor.

This specific packet has one job: **get a doctor or LHW supervisor through the reviewer checklist**, prioritising:
1. **Thyroid & other hormonal imbalances** content
2. **Pregnancy & postpartum danger signs** content

as flagged in `REVIEW_NOTES.md`.

---

## 2. ⚠️ Data-Mapping Note — Read Before Reviewing

`REVIEW_NOTES.md` identifies the priority rows by ID range from an **earlier, different file**: `naariai_faq_english_v1.csv` (500 rows, English, not yet translated to Sindhi), where thyroid was IDs 411–432 and danger signs was IDs 231–250.

The Sindhi KB file actually supplied for this review (`1789500167637_Womens_Health_KB_SINDHI_2021_FINAL.csv`) is a **different, larger, already-Sindhi file — 2,021 rows** (matches the "Womens_Health_KB_-_2000_final_1_.csv" KB used elsewhere in this project, plus ~21 appended rows). Its category order is different, so **those ID numbers do not point to the same content**:

- ID range 411–432 in this Sindhi file actually falls in **ذهني صحت ۽ جذباتي ڀلائي → سمهڻ ۽ ذهني صحتيابي** (Mental Health → Sleep & mental recovery) — not thyroid.
- ID range 231–250 in this Sindhi file actually falls in **حيض جي صحت ۽ مدت → حيض بابت ڳالهيون ۽ ثقافتي پابنديون** (Menstrual Health → Taboos & cultural restrictions) — not danger signs.

**What this packet does instead:** it locates the correct priority content in the *actual* Sindhi KB by matching the **sub-category names** named in `REVIEW_NOTES.md` ("Thyroid & other hormonal imbalances" and "Pregnancy & postpartum danger signs"), which do exist in this file under different IDs:

| Priority cluster | Sindhi sub-category | Actual KB IDs | Row count |
|---|---|---|---|
| 1 — Thyroid & hormonal | ٿائرائيڊ ۽ ٻيا هارموني عدم توازن | 910–931 | 22 (matches REVIEW_NOTES.md's expected 22 -- ID 2020 removed, see resolution note in §4) |
| 2 — Danger signs | حمل ۽ زچگي کانپوءِ خطري جون نشانيون | 730–749, plus 2002 | 21 (REVIEW_NOTES.md expected 20 — see §5) |

**Flag for the project lead:** confirm this ID-range discrepancy with whoever wrote `REVIEW_NOTES.md` — it suggests the notes document a build stage that predates this Sindhi file, and the same mismatch could affect other review notes downstream. This packet did not touch or renumber the KB itself.

---

## 3. Reviewer Instructions

1. Work through Priority 1 (thyroid) first, then Priority 2 (danger signs) — both are flagged highest-risk in `REVIEW_NOTES.md`.
2. For each item, tick the boxes and write notes directly in this document, **or** fill in the matching row in `clinical_review_tracking.csv` (same content, spreadsheet form) — use whichever is easier; only one needs to be completed.
3. Do not silently edit the "Current Sindhi answer" text. If a change is needed, mark the decision as **Fix** and write the corrected Sindhi wording in "Suggested fix."
4. Mark **Drop** for any item that should be pulled from the KB or the voice assistant pending rework (e.g. medically unsafe, unclear, or outside the assistant's safe scope).
5. Leave an item **Pending** (don't force Approve/Fix/Drop) if you need more information — note what's missing.
6. Complete the sign-off block at the very end (§7) — a reviewer name, credentials, and date are required for this packet to count as reviewed.

### Reviewer checklist — apply to every item

- [ ] Are the thyroid answers medically accurate and sufficiently safe for a lay audience?
- [ ] Is any important warning/referral information missing?
- [ ] Do the danger-sign answers give the correct urgent-care/escalation instruction (not softened, not delayed)?
- [ ] Could the Sindhi wording, spoken aloud, be misheard or misunderstood in a way that changes the medical meaning?
- [ ] Is treatment/medicine wording safe and appropriate (no medicine named or dosed — per the KB's own safety rule)?
- [ ] Do any population-level claims or numbers need Pakistan/Sindh-specific context instead of global figures?

---

## 4. Priority 1 — Thyroid & Other Hormonal Imbalances (22 items)

Sub-category: ٿائرائيڊ ۽ ٻيا هارموني عدم توازن. Per `REVIEW_NOTES.md`, this is the **highest-priority cluster**: the underlying ATA 2026 guideline text was only partially retrievable during the build, so answers were deliberately kept general (no TSH thresholds, no iodine amounts, no drug names/doses). Reviewer should confirm the general level is acceptable or add specifics.

**Reviewer, please also check specifically:**
- ~~ID 2020 flagged as possibly miscategorized~~ **RESOLVED 2026-09-17, before reviewer sign-off.** Confirmed miscategorized -- its content is PCOS treatment-by-age, not thyroid, and its Mayo Clinic source was correctly outside this cluster's registry for exactly that reason. Recategorized in the KB (both Sindhi and English) from "Thyroid & other hormonal imbalances" to "Lifestyle management," which is where its content -- lifestyle changes as first-line treatment, escalating to medication later -- actually fits among the existing subcategories. Removed from this priority cluster; it's ordinary Tier B content now, same review need as any other non-flagged row, not high-risk-cluster content. See git history for the exact change.
- IDs 922–926 (ovarian failure, fibroids, endometriosis, bleeding disorders) are all cited to the WHO "menstrual health" fact sheet — confirm that fact sheet actually supports these specific clinical claims, since it is a general fact sheet rather than a condition-specific guideline.

### THY-01 — Source KB ID 910

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ٿائرائيڊ ڇا آهي؟
- **Current Sindhi answer:** اها ڳچيءَ ۾ هڪ غدود آهي جيڪا اهڙا هارمون ٺاهي ٿي جيڪي جسم کي توانائي استعمال ڪرڻ جي طريقي کي قابو ۾ رکن ٿا۔ جڏهن اها تمام گھٽ يا تمام گھڻي ٺاهي ٿي ته اهو جسم جي ڪيترن حصن تي اثر انداز ٿئي ٿو۔ هڪ خوني ٽيسٽ چيڪ ڪري سگهي ٿو ته اها ڪيئن ڪم ڪري رهي آهي۔
- **Source/citation:** https://www.thyroid.org/new-ata-guidelines-for-thyroid-disease-in-preconception-pregnancy-and-postpartum/
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-02 — Source KB ID 911

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا ٿائرائيڊ جو مسئلو منهنجي ماهواري تي اثر انداز ٿي سگهي ٿو؟
- **Current Sindhi answer:** ٿائرائيڊ جا مسئلا انهن حالتن مان آهن جن کي ڊاڪٽر ماهواري بگڙڻ وقت خيال ۾ رکن ٿا۔ اهو ئي سبب آهي جو پي سي او ايس جي تشخيص کان اڳ ٻيا سبب رد ڪيا ويندا آهن۔ هڪ خوني ٽيسٽ توهان جي ٿائرائيڊ چيڪ ڪري سگهي ٿو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-03 — Source KB ID 912

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا ٿائرائيڊ جو مسئلو حامله ٿيڻ کي وڌيڪ ڏکيو بڻائي سگهي ٿو؟
- **Current Sindhi answer:** ٿائرائيڊ جي بيماري انهن عورتن لاءِ لاڳاپيل سمجهي وڃي ٿي جن کي زرخيزي ۾ ڏکيائي هجي، ۽ حمل کان اڳ ۽ دوران ان جو جائزو وٺڻ لاءِ خاص رهنمائي موجود آهي۔ جيڪڏهن توهان حامله ٿيڻ لاءِ جدوجهد ڪري رهيا آهيو ته ٿائرائيڊ ٽيسٽ بابت پڇو۔ اهو هڪ سادو خوني ٽيسٽ آهي۔
- **Source/citation:** https://www.thyroid.org/new-ata-guidelines-for-thyroid-disease-in-preconception-pregnancy-and-postpartum/
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-04 — Source KB ID 913

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** جيڪڏهن منهنجي ماهواري بي قاعده آهي ته ڇا منهنجو ٿائرائيڊ چيڪ ٿيڻ گھرجي؟
- **Current Sindhi answer:** ڇاڪاڻ ته ڪيتريون هارموني حالتون ماهواري کي بگاڙي سگهن ٿيون، تنهنڪري ڊاڪٽر پي سي او ايس جي تشخيص کان اڳ ٻيا سبب رد ڪن ٿا۔ ٿائرائيڊ جي جانچ ان جو حصو ٿي سگهي ٿي۔ پنهنجي ڊاڪٽر کان پڇو ته هو ڪهڙا ٽيسٽ ڪري رهيا آهن ۽ ڇو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-05 — Source KB ID 914

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** سست ٿائرائيڊ (Underactive Thyroid) ڇا آهي؟
- **Current Sindhi answer:** ان جو مطلب آهي ته ٿائرائيڊ تمام گھٽ هارمون ٺاهي رهيو آهي، جيڪو جسم جي ڪيترن ڪمن کي سست ڪري ٿو۔ اها انهن حالتن مان هڪ آهي جيڪا حمل کان اڳ ۽ دوران عورتن لاءِ ٿائرائيڊ رهنمائي ۾ شامل آهي۔ ان جي تشخيص خوني ٽيسٽ سان ٿيندي آهي۔
- **Source/citation:** https://www.thyroid.org/new-ata-guidelines-for-thyroid-disease-in-preconception-pregnancy-and-postpartum/
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-06 — Source KB ID 915

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** تيز ٿائرائيڊ (Overactive Thyroid) ڇا آهي؟
- **Current Sindhi answer:** ان جو مطلب آهي ته ٿائرائيڊ تمام گھڻو هارمون ٺاهي رهيو آهي، جيڪو جسم جي ڪيترن ڪمن کي تيز ڪري ٿو۔ اها هڪ سڃاتل ٿائرائيڊ حالت آهي جيڪا عورتن کي حمل دوران ۽ ان کانپوءِ متاثر ڪري ٿي۔ ان کي طبي جانچ ۽ علاج جي ضرورت آهي۔
- **Source/citation:** https://www.thyroid.org/new-ata-guidelines-for-thyroid-disease-in-preconception-pregnancy-and-postpartum/
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-07 — Source KB ID 916

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا مون کي حمل ۾ پنهنجو ٿائرائيڊ چيڪ ڪرائڻ گھرجي؟
- **Current Sindhi answer:** حمل ۾ ٿائرائيڊ جي ڪارڪردگي جو ٽيسٽ خاص طبي رهنمائي هيٺ اچي ٿو، ۽ توهان کي ان جي ضرورت آهي يا نه اهو توهان جي حالت تي منحصر آهي۔ پنهنجي حمل واري صحت ڪارڪن کان پڇو۔ پاڻ ٽيسٽ رٿابندي يا تشريح نه ڪريو۔
- **Source/citation:** https://www.thyroid.org/new-ata-guidelines-for-thyroid-disease-in-preconception-pregnancy-and-postpartum/
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-08 — Source KB ID 917

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا ٿائرائيڊ جا مسئلا ٻار ڄمڻ کانپوءِ ظاهر ٿي سگهن ٿا؟
- **Current Sindhi answer:** ها، ٻار ڄمڻ کانپوءِ ٿيندڙ ٿائرائيڊ جا مسئلا سڃاتل آهن ۽ خاص طور تي طبي رهنمائي ۾ شامل آهن۔ جيڪڏهن ٻار ڄمڻ کان پوءِ وارن مهينن ۾ توهان کي غير معمولي طور تي ٿڪل، اداس يا خراب محسوس ٿئي ته ان جو ذڪر ڪريو۔ هڪ خوني ٽيسٽ ان کي چيڪ ڪري سگهي ٿو۔
- **Source/citation:** https://www.thyroid.org/new-ata-guidelines-for-thyroid-disease-in-preconception-pregnancy-and-postpartum/
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-09 — Source KB ID 918

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا آئوڊين ٿائرائيڊ لاءِ اهم آهي؟
- **Current Sindhi answer:** آئوڊين ٿائرائيڊ جي ڪم ڪرڻ لاءِ گھربل آهي، ۽ حمل کان اڳ، دوران ۽ کانپوءِ عورتن لاءِ آئوڊين بابت رهنمائي موجود آهي۔ پاڻ مرادو ڪا به شيءِ شروع نه ڪريو۔ صحت ڪارڪن کان پڇو ته توهان جي علائقي ۾ ڇا صلاح ڏني وڃي ٿي۔
- **Source/citation:** https://www.thyroid.org/new-ata-guidelines-for-thyroid-disease-in-preconception-pregnancy-and-postpartum/
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-10 — Source KB ID 919

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا آءٌ ٿڃ پيارائي سگهان ٿي جيڪڏهن مون کي ٿائرائيڊ جي حالت آهي؟
- **Current Sindhi answer:** ٿڃ پيارڻ دوران ٿائرائيڊ جي سنڀال خاص طور تي طبي رهنمائي ۾ شامل آهي، تنهنڪري اها سنڀالڻ جوڳي حالت آهي۔ پنهنجي ڊاڪٽر کي ٻڌايو ته توهان ٿڃ پيارائي رهيا آهيو۔ علاج بند نه ڪريو يا صلاح کان سواءِ کير پيارڻ بند نه ڪريو۔
- **Source/citation:** https://www.thyroid.org/new-ata-guidelines-for-thyroid-disease-in-preconception-pregnancy-and-postpartum/
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-11 — Source KB ID 920

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا مون کي هڪ ئي وقت پي سي او ايس ۽ ٿائرائيڊ جو مسئلو ٿي سگهي ٿو؟
- **Current Sindhi answer:** هڪ کان وڌيڪ هارموني حالت هجڻ ممڪن آهي۔ اهو ئي سبب آهي جو ڊاڪٽر هڪ تشخيص تي رڪجڻ بدران وسيع جانچ ڪن ٿا۔ پنهنجيون سڀ نشانيون ٻڌايو، صرف اهي نه جيڪي توهان کي لڳي ته لاڳاپيل آهن۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-12 — Source KB ID 921

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** مون کي ڪيئن خبر پوندي ته منهنجيون نشانيون ٿائرائيڊ آهن يا پي سي او ايس؟
- **Current Sindhi answer:** اڪيلو نشانين کان توهان انهن کي جدا نٿا ڪري سگهو، ڇاڪاڻ ته اهي هڪ ٻئي سان ملن ٿيون۔ خوني ٽيسٽ ئي انهن کي جدا ڪن ٿا۔ پاڻ فيصلو ڪرڻ بدران ڊاڪٽر کي ڏسو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-13 — Source KB ID 922

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** پي سي او ايس کان علاوه ٻيون ڪهڙيون حالتون ماهواري کي بگاڙي سگهن ٿيون؟
- **Current Sindhi answer:** اينڊوميٽرائيوسس، ايڊينوميائوسس، فائبرائيڊز، رت وهڻ جون بيماريون، ماهواري کان اڳ واريون حالتون، ۽ بيضه دان جي جلدي ڪم بند ٿيڻ سڀ سڃاتل سبب آهن۔ ٿائرائيڊ جا مسئلا به خيال ۾ رکيا ويندا آهن۔ اهو ئي سبب آهي جو هڪ مناسب جانچ اهم آهي۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/menstrual-health
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-14 — Source KB ID 923

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** بيضه دان جو جلدي ڪم بند ٿيڻ ڇا آهي؟
- **Current Sindhi answer:** اها هڪ حالت آهي جنهن ۾ بيضه دان اميد کان اڳ ئي ڪم ڪرڻ بند ڪري ڏين ٿا، ۽ اها ماهواري جي مسئلن جي سڃاتل سببن مان هڪ آهي۔ ان کي طبي جانچ جي ضرورت آهي۔ اهو نه سمجهو ته غائب ماهواري هميشه پي سي او ايس آهي۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/menstrual-health
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-15 — Source KB ID 924

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** فائبرائيڊز (Fibroids) ڇا آهن؟
- **Current Sindhi answer:** اهي ٻچيدان ۾ ٿيندڙ واڌ آهن ۽ مسئلن واري ماهواري سان لاڳاپيل سڃاتل حالتن مان هڪ آهن۔ اهي گھڻي يا سور واري رت وهڻ جو سبب بڻجي سگهن ٿيون۔ هڪ ڊاڪٽر جائزو وٺي سگهي ٿو ته ڇا اهي ان جو سبب آهن۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/menstrual-health
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-16 — Source KB ID 925

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** اينڊوميٽرائيوسس (Endometriosis) ڇا آهي؟
- **Current Sindhi answer:** اها ڏکي ۽ سور واري ماهواري جي سبب طور سڃاتل هڪ حالت آهي۔ ان جي تشخيص لاءِ طبي جانچ گھربل آهي۔ جيڪڏهن توهان جو ماهواري وارو سور سخت هجي يا وڌي رهيو هجي ته ان لاءِ جانچ ٿيڻ لاءِ چئو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/menstrual-health
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-17 — Source KB ID 926

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا رت وهڻ جي بيماري گھڻي ماهواري جو سبب بڻجي سگهي ٿي؟
- **Current Sindhi answer:** ها، رت وهڻ جون بيماريون مسئلن واري ماهواري جي رت وهڻ جي سڃاتل سببن مان آهن۔ انهن جي تشخيص خوني ٽيسٽن سان ٿيندي آهي۔ ڪا به آسانيءَ سان ڪَسِڻ يا ٻي هنڌان رت اچڻ پنهنجي ڊاڪٽر کي ٻڌايو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/menstrual-health
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-18 — Source KB ID 927

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا مون کي هارموني مسئلن لاءِ ڪنهن ماهر وٽ وڃڻ جي ضرورت آهي؟
- **Current Sindhi answer:** پنهنجي ويجھي صحت مرڪز يا عام ڊاڪٽر کان شروع ڪريو، جيڪو ابتدائي ٽيسٽ ڪري سگهي ٿو ۽ ضرورت پوڻ تي اڳتي موڪلي سگهي ٿو۔ انهن حالتن جي سنڀال عام خدمتن کان شروع ٿيڻ گھرجي۔ توهان کي پاڻ ڪو ماهر ڳولڻ جي ضرورت ناهي۔
- **Source/citation:** https://academic.oup.com/jcem/article/108/10/2447/7242360
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-19 — Source KB ID 928

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا هارموني مسئلن جو علاج ٿي سگهي ٿو؟
- **Current Sindhi answer:** ها، صحيح طور تي سڃاڻڻ کانپوءِ گھڻيون هارموني حالتون سٺي طرح قابو ۾ رکي سگهجن ٿيون۔ ڏکيائي عام طور تي تشخيص ۾ هوندي آهي، علاج ۾ نه۔ اهو ئي سبب آهي جو جانچ اهم آهي۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-20 — Source KB ID 929

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** ڇا مون کي ڪنهن جي صلاح ڏنل هارموني دوا کائڻ گھرجي؟
- **Current Sindhi answer:** نه۔ ٽيسٽن کانپوءِ ڊاڪٽر جي لکيل تجويز کان سواءِ ڪڏهن به هارموني دوائون نه کائو۔ ساڳيون نشانيون بلڪل مخالف هارموني مسئلن کان به اچي سگهن ٿيون، تنهنڪري غلط علاج نقصان پهچائي سگهي ٿو۔ پهريان ٽيسٽ ڪرايو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-21 — Source KB ID 930

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** هارموني حالتون ڪيتري عرصي رهنديون آهن؟
- **Current Sindhi answer:** گھڻيون ڊگھي مهل جون حالتون آهن جن کي هڪ ڀيري جي علاج بدران مسلسل سنڀال جي ضرورت آهي۔ باقاعده فالو اپ سنڀال جو حصو آهي۔ توهان ٺيڪ محسوس ڪريو ته به پنهنجيون ملاقاتون رکو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/polycystic-ovary-syndrome
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### THY-22 — Source KB ID 931

- **Category / Sub-category:** پي سي او ايس ۽ هارموني صحت / ٿائرائيڊ ۽ ٻيا هارموني عدم توازن
- **Sindhi question:** مون کي پنهنجن هارموني نشانين بابت ڊاڪٽر کي ڇا ٻڌائڻ گھرجي؟
- **Current Sindhi answer:** پنهنجي ماهواري جو نمونو، ۽ وزن، وارن، چمڙي، توانائي يا مزاج ۾ ڪا به تبديلي بيان ڪريو، هر هڪ ڪڏهن شروع ٿي ان سميت۔ پنهنجي چڪر جي تاريخن جو رڪارڊ ساڻ کڻي وڃو۔ مڪمل تصوير ئي کين صحيح طرح جانچڻ جي قابل بڻائي ٿي۔
- **Source/citation:** https://academic.oup.com/jcem/article/108/10/2447/7242360
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### ~~THY-23 — Source KB ID 2020~~ — REMOVED, not a review item

This ID was miscategorized under this thyroid cluster (its real content is
PCOS treatment differences by age) and has been recategorized to "Lifestyle
management" in the KB as of 2026-09-17. It no longer belongs to Priority 1
and is not part of the 43 items this packet asks a reviewer to sign off on.
Kept as a visible strikethrough entry, not deleted outright, so this
packet's own item numbering (THY-01..THY-22, item count 43) stays
traceable against the version a reviewer may have already started on.


---

## 5. Priority 2 — Pregnancy & Postpartum Danger Signs (21 items)

Sub-category: حمل ۽ زچگي کانپوءِ خطري جون نشانيون. Per `REVIEW_NOTES.md`, escalation wording here needs to match the escalation script in `kb_upload_sindhi.md` (not supplied to this review — reviewer/project lead should cross-check separately) so the agent behaves consistently across entries.

**Reviewer, please also check specifically:**
- **ID 2002**'s answer states a specific fever threshold — 100.4°F (38°C) — as a danger sign. This is the only numeric clinical threshold in either priority cluster; confirm it's the correct threshold to give in this context.
- **ID 2002**'s source is cited as "CDC – Urgent Maternal Warning Signs," which also does not appear in the verified registry in `REVIEW_NOTES.md`. Confirm this citation.
- IDs 910–931 and 730–749 are numbered sequentially and were clearly part of the file's original 2,000-row build; IDs 2020 and 2002 sit far outside that range (near the end of the file) and use a different source-citation format ("Source Name - URL" vs. bare URL). This is consistent with them being later additions — reviewer/project lead should confirm when and how they were added and whether they went through the same build/citation process as the rest of the file.

### DNG-01 — Source KB ID 730

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** حمل ۾ اهي ڪهڙيون خطري جون نشانيون آهن جن جو مطلب آهي ته مون کي فوراً مدد وٺڻ گھرجي؟
- **Current Sindhi answer:** رت اچڻ، سخت مٿي جو سور، نظر ڌنڌلي ٿيڻ، پيٽ ۾ سخت سور، هٿن ۽ منهن جي سوڄ، بخار، ساهه کڄڻ، دورا، ٻار جي حرڪت گھٽجڻ، يا بدبودار رطوبت۔ انهن مان ڪا به هجي ته ان جو مطلب آهي هاڻي صحت مرڪز يا اسپتال وڃو۔ پاڻ سان ڪنهن کي وٺي وڃو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/maternal-mortality
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-02 — Source KB ID 731

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** مون کي حمل ۾ رت وهي رهيو آهي۔ مون کي ڇا ڪرڻ گھرجي؟
- **Current Sindhi answer:** حمل ۾ رت اچڻ اهڙي شيءِ ناهي جنهن جو انتظار ڪجي۔ هاڻي ويجھي صحت مرڪز يا اسپتال وڃو، ۽ پاڻ سان ڪنهن کي وٺي وڃو۔ اهو بند ٿئي ٿو يا نه اهو ڏسڻ لاءِ انتظار نه ڪريو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/maternal-mortality
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-03 — Source KB ID 732

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** مون کي سخت مٿي جو سور آهي ۽ منهنجي نظر ڌنڌلي آهي۔ ڇا اهو سنگين آهي؟
- **Current Sindhi answer:** ها، نظر ڌنڌلي ٿيڻ يا اکين اڳيان دنبا نظر اچڻ سان گڏ سخت مٿي جو سور حمل ۾ بلڊ پريشر جي هڪ خطرناڪ مسئلي جي نشاني ٿي سگهي ٿي۔ هاڻي صحت مرڪز يا اسپتال وڃو۔ پنهنجي ايندڙ معائني تائين انتظار نه ڪريو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-04 — Source KB ID 733

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** منهنجا هٿ ۽ منهن سُڄي ويا آهن۔ ڇا مون کي پريشان ٿيڻ گھرجي؟
- **Current Sindhi answer:** هٿن ۽ منهن جي سوڄ حمل ۾ بلڊ پريشر جي هڪ سنگين مسئلي جي نشاني ٿي سگهي ٿي۔ مهرباني ڪري هاڻي صحت مرڪز يا اسپتال وڃو، ڪنهن جي ساٿ سان۔ اها ڳِـٽن جي هلڪي سوڄ جهڙي ناهي۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-05 — Source KB ID 734

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** منهنجي مٿئين پيٽ ۾ سخت سور آهي۔ ان جو ڇا مطلب آهي؟
- **Current Sindhi answer:** حمل ۾ مٿئين پيٽ جو سور بلڊ پريشر جي مسئلي جي هڪ چتاءُ ڏيندڙ نشاني ٿي سگهي ٿو ۽ ان کي فوري ڇنڊڇاڻ جي ضرورت آهي۔ هاڻي صحت مرڪز يا اسپتال وڃو۔ پاڻ سان ڪنهن کي وٺي وڃو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-06 — Source KB ID 735

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** مون کي حامله هوندي بخار آهي۔ ڇا مون کي گھر ۾ ان جو علاج ڪرڻ گھرجي؟
- **Current Sindhi answer:** نه۔ حمل ۾ بخار هڪ خطري جي نشاني آهي ۽ ان کي صحت مرڪز تي ڏسڻ جي ضرورت آهي۔ گھر ۾ ان جو علاج نه ڪريو يا پاڻ مرادو دوا نه وٺو۔ هاڻي وڃو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/maternal-mortality
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-07 — Source KB ID 736

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** ٻار جي حرڪت بند ٿي وئي آهي يا گھڻو گھٽجي وئي آهي۔ مون کي ڇا ڪرڻ گھرجي؟
- **Current Sindhi answer:** حرڪت جو گھٽجڻ يا بند ٿيڻ هڪ خطري جي نشاني آهي جنهن کي فوري ڌيان جي ضرورت آهي۔ حرڪت واپس اچي ٿي يا نه اهو ڏسڻ جو انتظار ڪرڻ کان سواءِ هاڻي صحت مرڪز يا اسپتال وڃو۔ پاڻ سان ڪنهن کي وٺي وڃو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/maternal-mortality
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-08 — Source KB ID 737

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** مون کي ساهه کڻڻ ۾ ڏکيائي ٿي رهي آهي۔ ڇا حمل ۾ اهو ايمرجنسي آهي؟
- **Current Sindhi answer:** حمل ۾ ساهه کڄڻ هڪ خطري جي نشاني آهي۔ فوراً صحت مرڪز يا اسپتال وڃو۔ جيڪڏهن ٿي سگهي ته اڪيلي انتظار نه ڪريو يا اڪيلا سفر نه ڪريو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/maternal-mortality
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-09 — Source KB ID 738

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** حامله هوندي مون کي دورو پيو يا آءٌ بيهوش ٿي وئيس۔ منهنجي خاندان کي ڇا ڪرڻ گھرجي؟
- **Current Sindhi answer:** حمل ۾ دورا يا بيهوش ٿيڻ هڪ ايمرجنسي آهي ۽ جان جو خطرو ٿي سگهي ٿو۔ عورت کي فوراً اسپتال وٺي وڃو۔ رستي ۾ ڪا به گھريلو علاج نه ڪريو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-10 — Source KB ID 739

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** ايڪلمپسيا (Eclampsia) ڇا آهي؟
- **Current Sindhi answer:** اهو حمل جي بلڊ پريشر مسئلي جو سخت روپ آهي، جنهن ۾ دورا پون ٿا، ۽ اهو جان جي خطري وارو آهي۔ ان کي ايمرجنسي اسپتال جي علاج جي ضرورت آهي۔ حمل ۾ ڪنهن به دوري کي ايمرجنسي سمجهي علاج ڪجي۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-11 — Source KB ID 740

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** پري-ايڪلمپسيا (Pre-eclampsia) ڇا آهي؟
- **Current Sindhi answer:** اهو بلڊ پريشر جو مسئلو آهي جيڪو ويهن هفتن کانپوءِ پيدا ٿئي ٿو ۽ ماءُ ۽ ٻار ٻنهي لاءِ خطرناڪ ٿي سگهي ٿو۔ اهو ڄڻندڙ هر سؤ عورتن مان ٽي کان اَٺَ عورتن کي متاثر ڪري ٿو۔ ڪجهه عورتن کي بلڪل به نشاني نه هوندي آهي، اهو ئي سبب آهي جو معائنا اهم آهن۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-12 — Source KB ID 741

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** ڇا مون کي ڪجهه به محسوس ڪرڻ کان سواءِ پري-ايڪلمپسيا ٿي سگهي ٿو؟
- **Current Sindhi answer:** ها، ڪجهه عورتن کي بلڪل به نشاني نه هوندي آهي، اهو ئي سبب آهي جو هر ملاقات تي بلڊ پريشر ۽ پيشاب چيڪ ڪيو ويندو آهي۔ ٺيڪ محسوس ٿيڻ ڪري پاڻ کي محفوظ نه سمجهو۔ پنهنجا معائنا جاري رکو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-13 — Source KB ID 742

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** پري-ايڪلمپسيا ٿيڻ جو امڪان ڪنهن کي وڌيڪ آهي؟
- **Current Sindhi answer:** اهو پهرين حملن ۾، جاڙا يا وڌيڪ ٻار کڻندڙ عورتن ۾، ۽ انهن ۾ جن کي موٽاپو، اڳ ۾ موجود بلند بلڊ پريشر، ذیابيطس، گردن جي بيماري، يا خاندان ۾ ان جي تاريخ هجي، وڌيڪ امڪان رکي ٿو۔ جيڪڏهن انهن مان ڪا به توهان تي لاڳو ٿئي ته شروعات ۾ ئي پنهنجي صحت ڪارڪن کي ٻڌايو۔ توهان کي وڌيڪ ويجھي نظر رکڻ جي ضرورت پئجي سگهي ٿي۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-14 — Source KB ID 743

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** ڇا پري-ايڪلمپسيا کان بچاءُ ٿي سگهي ٿو؟
- **Current Sindhi answer:** باقاعده حمل دوران سنڀال جنهن ۾ بلڊ پريشر ۽ پيشاب جون چڪاسون شامل هجن، سڀ کان اهم بچاءُ آهي، ڇاڪاڻ ته اهي ان کي شروعات ۾ ئي پڪڙين ٿيون۔ وڌيڪ خطري واري عورتن لاءِ ڊاڪٽر بچاءَ وارو علاج صلاح ڏئي سگهن ٿا۔ پنهنجي صحت ڪارڪن سان پنهنجي خطري بابت ڳالهايو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-15 — Source KB ID 744

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** حمل ۾ بلڊ پريشر جا مسئلا ڪيترا خطرناڪ آهن؟
- **Current Sindhi answer:** بلڊ پريشر جون بيماريون هر سؤ ماءُ جي موتين مان لڳ ڀڳ سورهن جو سبب بڻجن ٿيون، جيڪي حمل ۾ موت جي بنيادي سببن مان آهن۔ اهو ئي سبب آهي جو هر ملاقات تي بلڊ پريشر چيڪ ڪيو ويندو آهي۔ جيڪڏهن توهان کي سخت مٿي جو سور، نظر ڌنڌلي ٿيڻ، مٿئين پيٽ جو سور يا هٿن ۽ منهن جي سوڄ هجي ته هاڻي صحت مرڪز يا اسپتال وڃو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/pre-eclampsia
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-16 — Source KB ID 745

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** ڄمڻ کانپوءِ مون کي گھڻو رت وهي رهيو آهي۔ مون کي ڇا ڪرڻ گھرجي؟
- **Current Sindhi answer:** ڄمڻ کانپوءِ سخت رت وهڻ ماءُ جي موت جو هڪ بنيادي سبب آهي ۽ اها ايمرجنسي آهي۔ فوراً اسپتال وٺي وڃو۔ اهو گھٽ ٿئي ٿو يا نه اهو ڏسڻ لاءِ انتظار نه ڪريو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/maternal-mortality
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-17 — Source KB ID 746

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** ٻار ڄمڻ کانپوءِ مون کي بخار ۽ بدبودار رطوبت آهي۔ ڇا اهو سنگين آهي؟
- **Current Sindhi answer:** ها، اهو ڄمڻ کانپوءِ انفيڪشن ٿي سگهي ٿو، جيڪو ماءُ جي موت جي بنيادي سببن مان هڪ آهي۔ هاڻي صحت مرڪز يا اسپتال وڃو۔ گھر ۾ ان جو علاج نه ڪريو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/maternal-mortality
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-18 — Source KB ID 747

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** ڇا ڄمڻ کانپوءِ هفتن ۾ به خطرناڪ مسئلا ٿي سگهن ٿا؟
- **Current Sindhi answer:** ها۔ گھڻيون ماءُ ۽ ٻار جون موتيون ڄمڻ کانپوءِ پهرين ڏينهن ۾ ٿين ٿيون۔ سخت رت وهڻ، بخار، سخت مٿي جو سور، نظر ڌنڌلي ٿيڻ، دورا ۽ ساهه کڄڻ سڀني کي ڄمڻ کانپوءِ به فوري سنڀال جي ضرورت آهي۔ پنهنجيون سڀ پوسٽ نيٽل چيڪون ضرور ڪرايو۔
- **Source/citation:** https://www.who.int/news/item/30-03-2022-who-urges-quality-care-for-women-and-newborns-in-critical-first-weeks-after-childbirth
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-19 — Source KB ID 748

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** جيڪڏهن مون کي خطري جي نشاني نظر اچي ته مون کي ڪيتري جلدي عمل ڪرڻ جي ضرورت آهي؟
- **Current Sindhi answer:** فوراً۔ دنيا ۾ ڪٿي نه ڪٿي هر تقريباً ٻن منٽن ۾ هڪ ماءُ جي موت ٿئي ٿي، ۽ سنڀال تائين پهچڻ ۾ دير هڪ وڏو سبب آهي۔ صبح ٿيڻ، اچ وڃ سولي ٿيڻ، يا اجازت ملڻ جو انتظار نه ڪريو۔ هاڻي وڃو ۽ پاڻ سان ڪنهن کي وٺي وڃو۔
- **Source/citation:** https://www.who.int/news-room/fact-sheets/detail/maternal-mortality
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-20 — Source KB ID 749

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** منهنجي نئين ڄاول ٻار ۾ مون کي ڪهڙين خطري جي نشانين تي نظر رکڻ گھرجي؟
- **Current Sindhi answer:** ساهه کڻڻ ۾ ڏکيائي، کير پيئڻ ۾ ڏکيائي يا کير پيئڻ کان انڪار، بخار، يا ٻار جو ٿڌو، ڍرو يا غير معمولي طور تي ماٺ ٿي وڃڻ۔ انهن کي سڃاڻڻ پوسٽ نيٽل سنڀال جو حصو آهي۔ انهن مان ڪا به ظاهر ٿئي ته فوراً ٻار کي صحت مرڪز وٺي وڃو۔
- **Source/citation:** https://www.who.int/news/item/30-03-2022-who-urges-quality-care-for-women-and-newborns-in-critical-first-weeks-after-childbirth
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________

### DNG-21 — Source KB ID 2002

- **Category / Sub-category:** حمل ۽ ماءُ جي صحت / حمل ۽ زچگي کانپوءِ خطري جون نشانيون
- **Sindhi question:** حمل دوران بخار ٿئي ته ڇا ڪجي؟
- **Current Sindhi answer:** حمل ۾ 100.4°F (38°C) يا مٿي بخار هڪ خطري جي نشاني آهي۔ گھر ۾ پاڻ مرادو دوا نه وٺو، تڪڙو صحت مرڪز يا اسپتال وڃو۔ جڏهن تائين اتي پهچو، وڌيڪ پاڻي پيئو، آرام ڪريو ۽ هلڪا ڪپڙا پايو۔ بخار سان گڏ سور، رطوبت، يا ٻار جي حرڪت گھٽجڻ جھڙيون نشانيون هجن ته اهو وڌيڪ سنگين ٿي سگهي ٿو۔
- **Source/citation:** CDC - Urgent Maternal Warning Signs - https://www.cdc.gov/hearher/pregnant-postpartum-women/index.html
- **Clinical accuracy check:** ☐ Accurate ☐ Partially accurate ☐ Inaccurate — *Pending*
- **Safety check:** ☐ Safe ☐ Needs caveat ☐ Unsafe — *Pending*
- **Referral/escalation check:** ☐ Escalation correct/present ☐ Missing escalation ☐ N/A — *Pending*
- **Reviewer decision:** ☐ Approve ☐ Fix ☐ Drop — *Pending*
- **Reviewer notes:** _______________________________________________
- **Suggested fix (if "Fix"):** _______________________________________________


---

## 6. Appendix — Related File Not Reviewed Item-by-Item: `danger_progress__1_.csv`

This file was supplied as "the Sindhi danger-sign CSV," but its structure is different from the KB and from this packet's review format:

- **Columns:** `question, subcategory, expected_behavior, reason` — there is **no `id`, no `answer`, and no `source` column**. It is not KB question/answer content; it reads as an **escalation-behavior test/eval set** — Sindhi patient scenarios paired with an expected agent behavior (all 100 rows are labeled `ESCALATE`) and an English clinical rationale.
- **Scope:** only 30 of its 100 rows are labeled with the subcategory "Danger Signs" — the other 70 span a much wider set of emergencies (e.g. thyroid storm, ectopic pregnancy, ovarian torsion, postpartum psychosis, anaphylaxis, menopause emergencies) that don't correspond to any single existing KB sub-category.
- **No overlap:** none of the 30 "Danger Signs" questions in this file match the wording of any of the 21 KB danger-sign questions above (checked directly) — it is a separate scenario set, not a Sindhi translation or duplicate of the KB rows.

**Recommendation flagged for the reviewer/project lead, not decided here:** this file looks like it belongs to a separate red-teaming/eval workstream for testing whether the deployed assistant escalates correctly, rather than to this KB clinical-content review. It has not been forced into the Priority 1/2 tables above because doing so would require inventing an `answer`/`source` for each row, which this packet is instructed not to do. Suggest routing it to whoever owns the assistant's escalation-behavior testing, with a note that its 70 non-"Danger Signs" rows currently have no matching KB content to test against.

---

## 7. Final Reviewer Summary

*(To be completed by the clinical reviewer)*

**Overall assessment of Priority 1 (Thyroid):** _______________________________________________

**Overall assessment of Priority 2 (Danger signs):** _______________________________________________

**Items approved as-is:** _____ / 43
**Items needing a fix:** _____ / 43
**Items to drop:** _____ / 43
**Items left pending / need more info:** _____ / 43

**Any systemic issue found (applies beyond a single item):** _______________________________________________

**Cleared for pilot use?** ☐ Yes ☐ No ☐ Yes, with fixes applied first ☐ Not yet — needs another review pass

---

### Reviewer sign-off

- **Reviewer name:** _______________________________________________
- **Credentials / role (e.g. MBBS, LHW Supervisor):** _______________________________________________
- **Date of review:** _______________________________________________
- **Signature:** _______________________________________________

*This packet is not valid as a clinical approval until this section is completed by a named, credentialed reviewer.*
