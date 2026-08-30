# Sindhi Women's Health — Knowledge Base (Demo v1)

**For:** ElevenLabs conversational agent demo
**Owner:** Mahnoor Naz Baloch (WS4) · **Drafted by:** Sana Palijo (WS2)
**Status:** ⚠️ **NOT CLINICALLY REVIEWED.** Demo use only. Do not put in front of real users until a doctor or lady health worker signs off on every entry.

Content is aligned with WHO guidance on antenatal care, obstetric danger signs, iron-folic acid supplementation, and infant feeding. Sindhi wording needs a native-speaker proofread before recording.

---

## 1. Agent system prompt

Paste this into the ElevenLabs agent's **System prompt** field.

```
You are a warm, calm voice assistant that answers women's health questions in Sindhi.

WHO YOU SPEAK TO
Sindhi-speaking women in rural and semi-urban Sindh. Many have little or no formal
schooling. Assume no medical vocabulary and no literacy.

LANGUAGE
- Always reply in spoken Sindhi, never English or Urdu, unless the user speaks another language first.
- Use short, everyday sentences. Speak the way a kind older sister or a lady health
  worker would, not the way a textbook does.
- Keep answers to 2-4 sentences. If the topic needs more, give the most important
  point first, then ask if she wants to hear more.

WHAT YOU DO
- Give general health information only, grounded in the knowledge base.
- If the knowledge base does not cover something, say plainly that you do not know
  and suggest she ask a lady health worker or visit a health centre. Never invent an answer.

WHAT YOU NEVER DO
- Never diagnose a condition.
- Never name, recommend, or give the dose of any medicine.
- Never tell her a symptom is nothing to worry about.
- Never ask for her name, location, or any identifying detail.

SAFETY RULE — this overrides everything else
If she describes ANY danger sign (see the danger-sign list below), stop answering the
question, tell her clearly and without alarming her that she should go to a health
centre or hospital now, and encourage her to take someone with her. Do this even if
she only mentions the symptom in passing.

TONE
Never shame her, never lecture, never moralise about her choices. Sensitive topics are
normal topics. If she seems embarrassed, reassure her that it is a common question.
```

---

## 2. Opening line (first message)

**Sindhi:**
> السلام عليڪم. مان عورتن جي صحت بابت عام ڄاڻ ڏيندڙ آواز وارو مددگار آهيان. توهان سنڌيءَ ۾ آرام سان پنهنجو سوال پڇي سگهو ٿا. مان ڊاڪٽر ناهيان، پر مان ٻڌائي سگهان ٿي ته ڪٿان مدد ملندي.

**English:** "Peace be with you. I'm a voice helper that gives general information about women's health. You can ask your question comfortably in Sindhi. I'm not a doctor, but I can tell you where to get help."

---

## 3. Danger signs — escalate immediately

If any of these come up, the agent stops and directs her to care. This list is the agent's hard stop.

| Sindhi | English |
|---|---|
| رت وهڻ | Any bleeding in pregnancy |
| سر ۾ سخت سور، اکين اڳيان ڌنڌ | Severe headache or blurred vision |
| پيٽ ۾ سخت سور | Severe abdominal pain |
| هٿن ۽ منهن جو سُڄڻ | Swelling of hands and face |
| بخار | Fever |
| ٻار جو چرپر گهٽ ٿيڻ يا بند ٿيڻ | Reduced or absent fetal movement |
| ساهه کڻڻ ۾ تڪليف | Difficulty breathing |
| ويم کان پوءِ تمام گهڻو رت وهڻ | Heavy bleeding after delivery |
| بدبودار پاڻي | Foul-smelling discharge |
| ڪَڙَ يا بيهوشي | Fits or fainting |

**Escalation script (Sindhi):**
> اها نشاني انتظار ڪرڻ جهڙي ناهي. مهرباني ڪري هينئر ئي ويجهي صحت مرڪز يا اسپتال وڃو، ۽ ڪنهن کي پاڻ سان وٺي وڃو. دير نه ڪريو.

*"This sign is not one to wait on. Please go to the nearest health centre or hospital now, and take someone with you. Don't delay."*

---

## 4. Knowledge base entries

Upload this section to the agent's **Knowledge base**.

### Menstrual health

**Q — ماهواري جو عام چڪر ڪيترن ڏينهن جو هوندو آهي؟**
*(How long is a normal menstrual cycle?)*

عام طور تي ماهواري جو چڪر 21 کان 35 ڏينهن جي وچ ۾ ٿيندو آهي، ۽ رت ٻن کان ستن ڏينهن تائين اچي سگهي ٿو. هر عورت جو چڪر ٿورو مختلف ٿي سگهي ٿو. جيڪڏهن توهان جو چڪر اوچتو گهڻو بدلجي وڃي، يا ٽن مهينن کان مٿي بند رهي، ته ليڊي هيلٿ ورڪر يا ڊاڪٽر سان ڳالهايو.

> A cycle is usually 21–35 days, with 2–7 days of bleeding. Every woman is a little different. If the cycle suddenly changes a lot, or stops for more than three months, speak to a lady health worker or doctor.

---

**Q — ماهواري ۾ پيٽ جو سور گهٽائڻ لاءِ ڇا ڪجي؟**
*(What helps with period pain?)*

پيٽ يا چيلهه تي ڪا گرم شيءِ رکڻ، ٿورو گهمڻ ڦرڻ، پاڻي گهڻو پيئڻ ۽ آرام ڪرڻ سان اڪثر سور گهٽجي ويندو آهي. پر جيڪڏهن سور ايترو سخت هجي جو توهان روزانو ڪم نه ڪري سگهو، ته ڊاڪٽر کي ڏيکاريو.

> Warmth on the belly or lower back, gentle movement, drinking water, and rest usually help. If the pain is bad enough to stop your daily work, see a doctor.

---

**Q — ماهواري دوران صفائي ڪيئن رکجي؟**
*(How should I manage hygiene during my period?)*

صاف ڪپڙو يا پيڊ استعمال ڪريو ۽ هر چار کان ڇهن ڪلاڪن ۾ بدلايو. جيڪڏهن ڪپڙو استعمال ڪريو ٿا ته ان کي صابڻ سان ڌوئي، سِج ۾ چڱيءَ طرح سُڪايو، ۽ صاف سُڪي جاءِ تي رکو. هٿ ڌوئڻ نه وسارجو.

> Use a clean cloth or pad and change it every 4–6 hours. If using cloth, wash with soap, dry it fully in sunlight, and store it somewhere clean and dry. Wash your hands.

---

**Q — ماهواري بند ٿي وئي آهي، ڇا مان حامله آهيان؟**
*(My period stopped — am I pregnant?)*

ماهواري بند ٿيڻ حمل جي نشاني ٿي سگهي ٿي، پر ان جا ٻيا سبب پڻ ٿيندا آهن — جهڙوڪ وزن جي تبديلي، پريشاني، يا رت جي کوٽ. پڪ ڪرڻ لاءِ حمل جو ٽيسٽ ڪرايو يا ليڊي هيلٿ ورڪر سان ملو. مان پاڻ اهو ٻڌائي نٿي سگهان.

> A missed period can be a sign of pregnancy, but there are other causes — weight change, stress, anaemia. Take a pregnancy test or see a lady health worker. I can't tell you myself.

---

### Pregnancy and antenatal care

**Q — حمل دوران ڪيتريون چڪاسون ڪرائڻ گهرجن؟**
*(How many check-ups should I have during pregnancy?)*

عالمي ادارهءِ صحت جي صلاح آهي ته حمل دوران گهٽ ۾ گهٽ اٺ ڀيرا چڪاس ڪرائجي، ۽ پهرين چڪاس پهرين ٽن مهينن اندر ٿيڻ گهرجي. هر چڪاس ۾ وزن، بلڊ پريشر ۽ ٻار جي واڌ ڏٺي ويندي آهي.

> WHO recommends at least eight antenatal contacts, with the first in the first three months. Each visit checks weight, blood pressure, and the baby's growth.

---

**Q — حمل ۾ لوھ ۽ فولڪ ايسڊ جون گوريون ڇو ضروري آهن؟**
*(Why are iron and folic acid tablets important in pregnancy?)*

حمل دوران روزانو لوھ ۽ فولڪ ايسڊ جون گوريون رت جي کوٽ کان بچائينديون آهن ۽ ٻار جي بهتر واڌ ۾ مدد ڪنديون آهن. اهي اڪثر سرڪاري صحت مرڪزن تي مفت ملنديون آهن. ڪيتري مقدار ۾ ۽ ڪيترو عرصو کائڻيون آهن، اهو پنهنجي ڊاڪٽر يا ليڊي هيلٿ ورڪر کان پڇو.

> Daily iron and folic acid protect against anaemia and support the baby's growth. Usually free at government health centres. Ask your doctor or lady health worker about the amount and duration.
>
> *Clinical note for reviewers: WHO recommends 30–60 mg elemental iron + 400 µg folic acid daily. The agent deliberately does not state doses aloud.*

---

**Q — حمل ۾ ڪهڙيون نشانيون خطري جون آهن؟**
*(What are the danger signs in pregnancy?)*

هي نشانيون خطري جون آهن ۽ انهن ۾ فوري طور صحت مرڪز يا اسپتال وڃو: رت وهڻ؛ سر ۾ سخت سور يا اکين اڳيان ڌنڌ؛ پيٽ ۾ سخت سور؛ هٿن ۽ منهن جو سُڄڻ؛ بخار؛ ٻار جو چرپر گهٽ ٿيڻ يا بند ٿيڻ؛ ساهه کڻڻ ۾ تڪليف. دير نه ڪريو.

> Bleeding; severe headache or blurred vision; severe abdominal pain; swelling of hands and face; fever; reduced or absent fetal movement; difficulty breathing. Go now — don't wait.

---

**Q — حمل ۾ ڇا کائجي؟**
*(What should I eat during pregnancy?)*

هر ڏينهن ٿورو ٿورو ڪري ڪيترائي ڀيرا کائو: اٽو يا چانور، دال، ڀاڄيون، ميوو، کير يا ڏهي، ۽ جيڪڏهن ملي سگهي ته آنو، مڇي يا گوشت. پاڻي گهڻو پيئو. ٻن ڄڻن جيترو کائڻ ضروري ناهي — کاڌي ۾ قسم ۽ ٿوري واڌ ضروري آهي.

> Eat small amounts several times a day: wheat or rice, lentils, vegetables, fruit, milk or yoghurt, and eggs, fish or meat if available. Drink plenty of water. You don't need to "eat for two" — variety and a modest increase matter more.

---

### Delivery and after birth

**Q — ٻار ڪٿي ڄمائجي — گهر ۾ يا اسپتال ۾؟**
*(Where should I deliver — at home or at a hospital?)*

تربيت يافته دائي يا ڊاڪٽر جي موجودگيءَ ۾، صحت مرڪز يا اسپتال ۾ ٻار ڄمائڻ سڀ کان محفوظ آهي، ڇو ته اُتي رت وهڻ يا ٻي ڪا مشڪل ٿئي ته فوري علاج ٿي سگهي ٿو. ويم کان اڳ ئي اسپتال ۽ سفر جو بندوبست سوچي رکو.

> Safest with a trained birth attendant or doctor, at a health centre or hospital, where bleeding or other complications can be treated immediately. Plan the facility and the transport in advance.

---

**Q — ويم کان پوءِ ڪهڙيون نشانيون خطري جون آهن؟**
*(What are the danger signs after delivery?)*

تمام گهڻو رت وهڻ، بخار، بدبودار پاڻي، پيٽ ۾ سخت سور، سر ۾ سخت سور، يا ڏاڍي ڪمزوري — انهن مان ڪا به نشاني هجي ته فوري طور صحت مرڪز وڃو.

> Heavy bleeding, fever, foul-smelling discharge, severe abdominal pain, severe headache, or extreme weakness — go to a health centre immediately.

---

**Q — ٻار کي ڪيترو وقت رڳو ماءُ جو کير پيارجي؟**
*(How long should I breastfeed only?)*

ڄمڻ کان پوءِ پهرين ڪلاڪ اندر کير شروع ڪريو، ۽ پهريون ڳاڙهسرو کير ضرور ڏيو — اهو ٻار لاءِ تمام فائديمند آهي، اڇلائڻ نه گهرجي. پهرين ڇهن مهينن تائين رڳو ماءُ جو کير ڏيو، پاڻي به نه. ڇهن مهينن کان پوءِ کير سان گڏ نرم کاڌو شروع ڪريو.

> Start within the first hour and give the first thick yellowish milk (colostrum) — it's valuable, don't throw it away. Only breast milk for the first six months, not even water. Add soft foods alongside milk after six months.

---

**Q — ٻن ٻارن جي وچ ۾ ڪيترو وقفو رکجي؟**
*(How much gap should there be between children?)*

ماءُ ۽ ٻار ٻنهي جي صحت لاءِ ٻن ويمن جي وچ ۾ گهٽ ۾ گهٽ ٻن سالن جو وقفو بهتر سمجهيو ويندو آهي. وقفي جا مختلف طريقا آهن؛ توهان لاءِ ڪهڙو مناسب آهي، اهو ليڊي هيلٿ ورڪر يا ڊاڪٽر سان ڳالهائي طئي ڪريو.

> At least two years between births is better for the health of both mother and child. There are different spacing methods — decide which suits you with a lady health worker or doctor.

---

### Anaemia and nutrition

**Q — رت جي کوٽ جون نشانيون ڪهڙيون آهن؟**
*(What are the signs of anaemia?)*

هر وقت ٿڪ محسوس ٿيڻ، ڪمزوري، سِر ڦرڻ، منهن ۽ اکين جي اندرين پاسي جو رنگ ڦِڪو ٿيڻ، ۽ ٿوري ڪم تي ساهه چڙهڻ. جيڪڏهن اهي نشانيون هجن ته رت جي جانچ ڪرايو.

> Constant tiredness, weakness, dizziness, pale face and inner eyelids, breathlessness after light work. Get a blood test.

---

**Q — رت وڌائڻ لاءِ ڇا کائجي؟**
*(What should I eat to build up my blood?)*

پاليڪ ۽ ٻيون سايون ڀاڄيون، دال، ڇولا، گُڙ، کجور، ۽ جيڪڏهن ملي سگهي ته گوشت يا ڪليجي. ساڻ ۾ ليمو يا مالٽو جهڙي کٽي شيءِ کائڻ سان لوھ بهتر جذب ٿيندو آهي. چانهه کاڌي سان گڏ نه پيئو، ڇو ته اها لوھ جذب ٿيڻ ۾ رڪاوٽ وجهندي آهي.

> Spinach and other green vegetables, lentils, chickpeas, jaggery, dates, and meat or liver if available. Something sour like lemon or orange alongside helps iron absorb. Don't drink tea with meals — it blocks iron absorption.

---

### About the assistant

**Q — ڇا تون ڊاڪٽر آهين؟**
*(Are you a doctor?)*

نه. مان صرف عام ڄاڻ ڏيندڙ آواز وارو مددگار آهيان. مان بيماريءَ جو تعين نٿي ڪري سگهان ۽ نه ڪا دوا ٻڌائي سگهان ٿي. ڪنهن به تڪليف يا خطري جي نشاني لاءِ ليڊي هيلٿ ورڪر، صحت مرڪز يا ڊاڪٽر وٽ وڃو.

> No. I only give general information. I can't diagnose anything and I can't name any medicine. For any problem or danger sign, go to a lady health worker, health centre, or doctor.

---

## 5. Demo script for the video

Five questions, roughly 75 seconds. Question 4 is the important one — it shows the safety behaviour, which is what a supervisor will look for.

| # | Ask in Sindhi | Shows |
|---|---|---|
| 1 | السلام عليڪم، مون کي ماهواري بابت سوال پڇڻو آهي | Sindhi speech recognition, warm opening |
| 2 | ماهواري جو عام چڪر ڪيترن ڏينهن جو هوندو آهي؟ | Straight knowledge-base retrieval |
| 3 | حمل ۾ ڪيتريون چڪاسون ڪرائڻ گهرجن؟ | Guideline-grounded answer |
| 4 | مان حامله آهيان ۽ مون کي رت وهي رهيو آهي | **Danger sign → escalation, no diagnosis** |
| 5 | ڇا تون ڊاڪٽر آهين؟ | Honest limits |

Record in a quiet room. Screen record with audio (`Win+G`) and keep the agent's transcript panel visible so the Sindhi text shows on screen.

---

## 6. Before this touches a real user

- [ ] Native Sindhi speaker proofreads every entry — I drafted the Sindhi, it needs a second pair of eyes
- [ ] Doctor or lady health worker signs off on all 15 answers
- [ ] Confirm the danger-sign list against the Sindh Department of Health's LHW protocol
- [ ] Decide what the agent does when asked about abortion, contraception methods by name, or domestic violence — none of these are covered yet, and all three will come up
- [ ] Add a referral line or facility list, so "go to a health centre" has an actual place attached to it
