# Phone-Based Health Services in Sindh — Gap Analysis

**Purpose:** check the deck's claim that existing phone health services are menu-driven IVR.
**Finding:** that claim is wrong, and the supervisor is likely to know it. The real gap is different — and stronger.

---

## 1. The headline correction

Slide 7 currently says:

| Category | Examples | Gap |
|---|---|---|
| IVR health helplines | Menu-driven rural phone lines | Not conversational; limited topic coverage |

**Sindh's flagship health line is not IVR.** Tele-Tabeeb 1123, run by SIEHS (Sindh Integrated Emergency and Health Services), connects callers directly to a PMDC-certified doctor or licensed psychologist. Its own material makes the point explicitly: *"Every call is answered by a PMDC certified doctor or a licensed mental health professional, not a call centre operator reading from a script."*

Worse for the current framing: the SIEHS procurement documents for Tele-Tabeeb specify medical staff able to communicate with callers **in regional languages, namely Urdu and Sindhi**.

If your supervisor asks "what about Tele-Tabeeb?" and the deck answers "menu-driven IVR, no Sindhi," the credibility of the whole landscape slide goes with it.

---

## 2. What actually exists

### Tele-Tabeeb 1123 — SIEHS, Government of Sindh
- Free, 24/7, every day of the year, nationwide.
- Live PMDC-certified doctors and licensed mental health professionals.
- Any mobile or landline. No internet, no app, no account, no registration.
- **621,024+ consultations** since launch in August 2021.
- Staffing spec includes Urdu and Sindhi speakers.
- Covers general medicine, mental health, and chronic conditions.

### Sehat Kahani
- Telemedicine social enterprise, founded 2017, network of predominantly **female** health professionals.
- Mobile app plus a 24/7 helpline plus nurse-assisted e-clinics for people without connectivity.
- Operating across 35+ cities, expanded into districts of Sindh and Punjab.
- Directly relevant: it targets women, and female doctors address exactly the stigma barrier.

### Awaaz-e-Sehat — LUMS
- Voice-assisted app that guides frontline health workers through structured questions in local languages.
- Its APPA component holds antenatal conversations in **Roman Urdu**, tracks symptoms, and triages using a WHO-aligned three-tier framework.
- The closest academic analogue to this project — but built for **providers**, not for women directly, and not in Sindhi.

### Aiza — CBT chatbot
- Text-based mental health chatbot. Supports Urdu, English, Punjabi **and Sindhi**.
- A Sindhi-supporting conversational health bot already exists. It is text, and it is mental health only.

### Ilaaj AI
- Urdu and English symptom chat with AI triage and doctor-verified follow-up.

### Actual IVR (menu-driven) work
- Genuine IVR maternal-health projects are mostly **research and pilots, and mostly outside Sindh**: an IVR antenatal/postnatal trial in rural Bangladesh, IVR reproductive-health messaging trials in India, and a Punjab-based RCT using voice and text messages plus telephone counselling for postpartum contraception.
- So "menu-driven IVR lines" describe the research literature, not Sindh's deployed services.

### Uplift AI — relevant to your build, not a competitor
- Commercial voice models for Pakistani regional languages, with **Sindhi voices already available** (including a female Sindhi voice), from $5/month.
- Implication: Sindhi text-to-speech is a solved, purchasable component. It is not the hard part of this project, and claiming it is will invite a correction.

---

## 3. The gap that actually holds up

Every service above fails a Sindhi-speaking rural woman on at least one axis. State it this way:

**A human answers.** On Tele-Tabeeb and Sehat Kahani, a stranger hears her voice and her question. Your own Problem slide argues that stigma around menstrual and reproductive health stops women asking openly. A human-answered line does not remove that barrier — it is the barrier, with a phone attached. An automated assistant is private in a way a staffed line cannot be.

**Human capacity does not scale.** 621,024 consultations over roughly five years is on the order of 340 calls a day for the whole of Pakistan. Rural Sindh alone has about 25.6 million people. Every additional call costs clinician time; an automated service costs almost nothing per call.

**Sindhi is a staffing preference, not a guarantee.** The procurement asks for Sindhi-capable staff. Nothing guarantees the doctor who picks up at 2am speaks Sindhi, or that a woman with limited Urdu can hold a clinical conversation with whoever answers.

**Nobody is Sindhi-first and women's-health-specialised.** Aiza covers Sindhi but only mental health, and only in text. Ilaaj AI is Urdu-first text. Awaaz-e-Sehat is Roman Urdu and aimed at health workers. No service combines: spoken Sindhi, women's health depth, always available, no human on the line.

**Menus cannot take an open question.** Where true IVR exists, a keypad tree can only offer what was anticipated. A woman does not always know which menu branch her question belongs to.

---

## 4. Suggested replacement for the slide 7 table

| Category | Examples | Gap |
|---|---|---|
| Government telemedicine helplines | Tele-Tabeeb 1123 (SIEHS) | Free and Sindhi-capable, but a human hears every question — and clinician time caps how far it scales |
| Telemedicine platforms | Sehat Kahani | Female doctors, but needs an app, data, or a visit to an e-clinic; not automated |
| Health chatbots | Aiza, Ilaaj AI | Text-based and Urdu-first; Aiza reaches Sindhi but only for mental health |
| Voice AI for health workers | Awaaz-e-Sehat (LUMS) | Roman Urdu, and built for providers rather than for women themselves |
| General voice assistants | Siri, Alexa, Google Assistant | No Sindhi support at all |

---

## 5. What this means for the positioning

The differentiator is **not** "nobody serves Sindhi speakers." That is now false and easy to disprove.

The differentiator is: **no one gives a Sindhi-speaking woman a private, always-available, spoken answer about her own body without another person on the line.**

That is narrower, true, and harder to argue with. It also explains why the project is worth doing even though Tele-Tabeeb exists — the two are complementary, and the assistant's escalation path should route urgent cases *to* 1123 rather than pretending to replace it.

**Worth adding to the deck:** escalating to Tele-Tabeeb 1123 by name, on the safety and architecture slides. It turns a competitor into infrastructure, and it shows the supervisor you know the landscape.

---

## Sources

- [Tele-Tabeeb 1123 — SIEHS](https://www.siehs.org/tele-tabeeb-1123/)
- [What Is Tele-Tabeeb? SIEHS free 24/7 telemedicine explained](https://www.siehs.org/2026/04/siehs-tele-tabeeb-1123-24-7-free-telemedicine-service/)
- [SIEHS Tele-Tabeeb tender documents (language requirements)](https://www.siehs.org/wp-content/uploads/2023/05/Tender-76-2023-Tele-Tabeeb-Application.pdf)
- [Sehat Kahani](https://sehatkahani.org/)
- [How Pakistan's community health workers use telemedicine for women's health](https://pmc.ncbi.nlm.nih.gov/articles/PMC9924177/)
- [Awaaz-e-Sehat](https://www.awaazesehat.com/)
- [Gates Foundation — AI for maternal health in Pakistan](https://www.gatesfoundation.org/ideas/articles/ai-maternal-health-pakistan)
- [Aiza — Pakistan's first CBT chatbot](https://www.dilkibaat.ca/aiza-pakistan-cbt-chatbot/)
- [Ilaaj AI](https://www.ilaaj.ai/)
- [Uplift AI — voice models for Pakistani languages](https://upliftai.org/)
- [IVR antenatal/postnatal trial, rural Bangladesh](https://www.socialscienceregistry.org/trials/14721)
- [mHealth RCT for postpartum contraception, Punjab, Pakistan](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6686472/)
