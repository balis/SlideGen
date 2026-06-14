# Practical AI for Professionals (Session 2) --- Participant Workbook

**How to use this workbook.** Each exercise is hands-on. Read the scenario, fill in
the starter prompt, run it in whatever general consumer chat LLM you have access to (or your employer-approved enterprise assistant when data is sensitive), then use the self-check.
**Never paste real confidential or personal data** into a consumer tool --- the
samples here are fictional on purpose.

---

## Exercise 1 · Sort the task list    :clock: 8 min · intro · any general consumer chat LLM

**Scenario.** You receive a list of 10 office tasks. Sort each into a green (LLM handles well), yellow (LLM can help but needs scaffolding or verification), or red (keep away from the LLM) zone. Then pick two tasks and write one sentence each explaining why you placed them where you did.

**Your goal.** A table or list of all 10 tasks, each assigned to GREEN, YELLOW, or RED, plus two one-sentence justifications for the hardest-to-place tasks.

**Use this material:**

> Task list --- sort each into GREEN / YELLOW / RED:
>
> 1. Rewrite a paragraph from your quarterly update so it sounds more concise and professional.
> 2. Draft a polite reply declining a meeting invitation you cannot attend.
> 3. Calculate the exact budget variance between Q1 actuals (EUR 41,837.12) and Q1 forecast (EUR 39,500.00), including the percentage difference.
> 4. Summarise a 2-page policy document into 5 bullet points for your team.
> 5. Decide which of three job candidates to invite to a final interview.
> 6. Paste a customer complaint email and ask the LLM to identify the core issue and suggest a response outline.
> 7. Ask the LLM to list all colleagues who were absent last Friday based on your company's internal HR system.
> 8. Shift the tone of a project status update from informal Slack-style to a formal board-ready paragraph.
> 9. Generate three subject-line options for a newsletter about an upcoming office move.
> 10. Upload a spreadsheet containing employee salaries and ask the LLM to find who earns above the median.

**Starter prompt** (fill the [BRACKETS]):
```
Here are 10 office tasks. For each task, assign it to one zone:
- GREEN = the LLM handles this well on its own
- YELLOW = the LLM can help, but the result needs human verification or extra scaffolding
- RED = do not use an LLM for this

After sorting all 10, pick the two tasks you found hardest to place and write one sentence each explaining your reasoning.

Tasks:
[PASTE THE 10-TASK LIST HERE]
```

**Steps**
1. Copy the 10-task list from the workbook and paste it into the starter prompt where indicated.
2. Read the model's proposed sorting. For each task, decide whether you agree or disagree with the zone the model chose.
3. Correct any placements you disagree with and note why.
4. Write your own one-sentence justification for the two tasks you found hardest to classify.
5. Run the verification step before finalising your answer.

**Your output** _(write or paste below)_
> ____________________________________________
> ____________________________________________
> ____________________________________________
> ____________________________________________

**Self-check** --- you're done when:
- [ ] All 10 tasks are assigned to exactly one zone.
- [ ] Tasks involving confidential or personal data (e.g. employee salaries in a consumer tool, HR system access) are placed in RED.
- [ ] Tasks requiring precise arithmetic (e.g. budget variance with percentages) are placed in YELLOW or RED, not GREEN.
- [ ] Drafting and tone-shifting tasks with no sensitive data are placed in GREEN.
- [ ] The two justifications each give a concrete reason (not just 'it felt right') tied to a capability or limitation of LLMs.

**Before you trust it:** Review your sorted list and check: Did you flag any task that involves confidential data? Did you catch that the LLM cannot access live company systems? Did you avoid trusting the model with precise arithmetic without a calculator check?

**Takeaway.** Before handing a task to an LLM, ask three questions: Does it need private data? Does it need precise numbers? Does it need a final human decision? Any 'yes' moves the task towards yellow or red.

_Stretch (optional):_ Pick one task you placed in YELLOW and write a short prompt that adds the scaffolding needed to move it closer to GREEN (e.g., instruct the model to show its arithmetic so you can verify).

---

## Exercise 2 · Reply to a messy email thread    :clock: 12 min · core · any general consumer chat LLM

**Scenario.** A colleague's 5-message email thread about a logistics event has drifted across topics. You need to identify what is actually being asked of you, draft a reply in a specified tone, and then rewrite one line so it sounds like you.

**Your goal.** A one-sentence identification of the real ask (Sam is asking Priya whether to go ahead and request a GreenPlate catering quote now as a backup, or wait until Jordan hears back from Riverside about dietary options) plus a short reply (under 120 words) that answers that question in the chosen tone, with at least one line rewritten by the learner.

**Use this material:**

> ```
> FROM: Priya Novak <priya.novak@example.com>
> TO: Jordan Lee <jordan.lee@example.com>, Sam Torres <sam.torres@example.com>
> SUBJECT: Re: Re: Re: Q3 Offsite --- venue & catering
> DATE: Tuesday 10:14 AM
>
> --- Message 1 (Monday 8:02 AM) --- Priya Novak ---
> Hi Jordan, hi Sam,
> Quick heads-up: the Riverside Conference Centre just confirmed they can hold
> 40 people on 18 September, but they need a final headcount by this Friday.
> Can one of you pull that together? Also, they offer in-house catering or we
> can bring our own --- any preferences?
>
> --- Message 2 (Monday 9:47 AM) --- Sam Torres ---
> Riverside sounds great. I think last year we had 33 attendees, but a few more
> people joined the analytics team since then. I'd guess 36-38 this time. For
> catering, their in-house lunch menu looked a bit limited when I checked the
> website --- maybe we should get quotes from GreenPlate too?
>
> --- Message 3 (Monday 11:30 AM) --- Jordan Lee ---
> I actually already emailed the team leads yesterday to ask for names. So far
> I have 29 confirmed, waiting on Product and Finance. Catering-wise, I'm fine
> either way, but remember last year two people had allergies that the venue
> couldn't handle.
>
> --- Message 4 (Monday 4:55 PM) --- Priya Novak ---
> Thanks Jordan --- great that you started the count. Could you also find out
> whether Riverside's in-house catering handles nut-free and gluten-free? If
> not, we should definitely go with GreenPlate.
> Sam, unrelated, but do you have the slide template from last year's offsite?
> I want to reuse the branding.
>
> --- Message 5 (Tuesday 10:14 AM) --- Sam Torres ---
> I'll dig up the slide template after lunch. Jordan, while you're checking
> with Riverside on dietary options, could you also ask if they have breakout
> rooms we can book for the afternoon workshops? We had that awkward
> hallway-session problem last time. Priya --- should I go ahead and request a
> GreenPlate quote as a backup, or wait until Jordan hears back?
> ```

**Starter prompt** (fill the [BRACKETS]):
```
Here is an email thread. First, tell me in one sentence what the latest message
(Message 5) is actually asking me to do or decide. Then draft a reply from me
([YOUR NAME]) that is [TONE] and addresses only that ask. Keep the reply under
120 words.

Thread:
[PASTE THREAD]
```

**Steps**
1. Copy the 5-message email thread from the workbook and paste it into the starter prompt, replacing [PASTE THREAD].
2. Replace [YOUR NAME] with a name of your choice and [TONE] with a tone --- for example: 'friendly and decisive', 'concise and professional', or 'warm but direct'.
3. Send the prompt and read the model's one-sentence summary of the ask BEFORE reading the draft reply. Ask yourself: did it capture the real ask, or did it latch onto a side topic?
4. If the one-sentence ask is wrong or incomplete, correct it in a follow-up message (e.g. 'Actually, the real ask is whether to request the GreenPlate quote now or wait --- re-draft.') and regenerate.
5. Once the draft is satisfactory, pick one line and rewrite it in your own words so the reply does not sound entirely AI-generated.
6. Run the verification step before considering the reply 'sent'.

**Your output** _(write or paste below)_
> ____________________________________________
> ____________________________________________
> ____________________________________________
> ____________________________________________

**Self-check** --- you're done when:
- [ ] The one-sentence ask correctly identifies Sam's question to Priya: proceed with the GreenPlate backup quote now, or wait for Jordan's Riverside dietary-options answer.
- [ ] The reply addresses that decision and gives a clear answer (yes go ahead, or wait) rather than restating the question.
- [ ] The reply does not wander into unrelated threads (slide template, headcount, breakout rooms) unless briefly acknowledging them.
- [ ] The reply matches the tone the learner specified in the prompt.
- [ ] At least one line in the final reply has been rewritten in the learner's own voice.

**Before you trust it:** Before 'sending' the reply, check: (1) Are any names wrong or swapped? (2) Does the reply accidentally commit to something you did not intend (e.g. volunteering to handle catering yourself)? (3) Does the tone actually match what you asked for? (4) Did the model invent any facts not in the thread (dates, numbers, promises)?

**Takeaway.** Extract the ask first, then draft --- decomposing a messy thread into 'what is actually being requested' before generating a reply produces more focused, accurate responses than one-shot 'reply to this'.

_Stretch (optional):_ Forward the same thread to the model but this time ask it to reply from Jordan's perspective instead of Priya's. Notice how the relevant ask changes (Jordan is being asked about breakout rooms and dietary options). Compare how the decomposition step surfaces a different action item depending on who 'you' are.

---

## Exercise 3 · Bullets to memo    :clock: 12 min · core · any general consumer chat LLM

**Scenario.** Your manager jotted down bullet points after a site visit and asked you to turn them into a clean one-page memo for the leadership team. The numbers and technical terms must survive exactly as written; everything else should be tightened up.

**Your goal.** A structured one-page memo (Subject, Summary, Key Findings, Recommended Actions, Timeline) that reads professionally and preserves every number, date, product name, and technical term from the original bullets without alteration.

**Use this material:**

> ```
> SITE VISIT NOTES --- Greenfield Distribution Centre, 14 May 2026
>
> - toured the new Greenfield DC with Priya Sharma (ops director) and two
>   shift leads
> - facility is 24,000 m2 across 3 zones: inbound, pick-pack, outbound
> - current throughput 8,400 parcels/hr but rated capacity is 11,200
>   parcels/hr --- running at 75% utilisation
> - main bottleneck is the sorter divert at Zone 2; belt speed limited to
>   1.8 m/s because older OCR cameras misread barcode at higher speeds
> - Priya wants to upgrade to Cognex DataMan 380 cameras --- vendor quote
>   EUR 74,500 for 12 units incl. installation
> - expected result: belt speed up to 2.4 m/s, throughput gain ~1,400
>   parcels/hr
> - ROI calc from ops team: payback in 14 weeks at current volume
> - secondary issue: HVAC in Zone 3 is failing intermittently --- 3
>   unplanned shutdowns last quarter, each ~45 min, costing roughly
>   EUR 6,200 per event in overtime + delayed shipments
> - Priya asked for a budget decision on the cameras by 31 May and wants
>   the HVAC on the Q3 capex list
> - overall impression: team is competent, facility is clean, biggest risk
>   is doing nothing on the sorter before peak season (starts 1 Sep)
> ```

**Starter prompt** (fill the [BRACKETS]):
```
Below are rough bullet-point notes from a site visit. Turn them into a one-page
professional memo addressed to [RECIPIENT/ROLE].

Constraints:
- Fix grammar, spelling, and sentence flow for clarity
- Do NOT change any numbers, dates, currency amounts, product names, or
  technical terms --- keep them exactly as they appear
- Use a [TONE] tone suitable for [AUDIENCE]
- Structure the memo with: Subject line, Summary (2-3 sentences), Key Findings,
  Recommended Actions, and Timeline

Notes:
[PASTE BULLET POINTS]
```

**Steps**
1. Read through the bullet points and identify the numbers, dates, and technical terms that must be preserved (e.g., 24,000 m2, EUR 74,500, Cognex DataMan 380, 14 weeks).
2. Copy the starter prompt template and fill in the [BRACKETED] placeholders: choose a recipient (e.g., 'the VP of Operations'), a tone (e.g., 'concise and professional'), and an audience (e.g., 'senior leadership').
3. Paste the bullet points into the [PASTE BULLET POINTS] placeholder and send the complete prompt to your LLM.
4. Compare every number, date, product name, and technical term in the output against the original bullets. Circle or highlight any that were changed, dropped, or rounded.
5. If any protected detail was altered, add a follow-up message: 'You changed [specific item]. Restore the original value exactly.' Re-check after the correction.
6. Read the memo once for tone and flow --- does it sound like a memo your leadership team would expect?

**Your output** _(write or paste below)_
> ____________________________________________
> ____________________________________________
> ____________________________________________
> ____________________________________________

**Self-check** --- you're done when:
- [ ] All numbers appear exactly as in the original bullets (8,400 parcels/hr, 11,200 parcels/hr, 75%, 24,000 m2, 1.8 m/s, 2.4 m/s, 1,400 parcels/hr, EUR 74,500, 14 weeks, 3 shutdowns, 45 min, EUR 6,200).
- [ ] All dates are unchanged (14 May 2026, 31 May, 1 Sep, Q3).
- [ ] Product names and technical terms are exact (Cognex DataMan 380, OCR, HVAC, sorter divert).
- [ ] The memo has a clear structure with at least a subject line, summary, findings, and recommended actions.
- [ ] Grammar and sentence flow are improved over the raw bullets --- no bullet-point fragments remain in the body.

**Before you trust it:** Go through the original bullets line by line with the memo open beside them. Check off each number, date, and technical term. If anything was rounded (e.g., 'approximately 75,000' instead of 'EUR 74,500'), paraphrased (e.g., 'DataMan cameras' instead of 'Cognex DataMan 380'), or dropped entirely, the constraint was violated --- fix it before sending.

**Takeaway.** State what to change AND what to preserve --- explicit constraints act as guardrails that prevent the model from 'improving' details you need kept intact.

_Stretch (optional):_ Add a second pass: ask the model to shift the memo's register from leadership-formal to a casual Slack update for the warehouse team, keeping the same change/preserve constraint. Compare which numbers survived in each version.

---

## Exercise 4 · Decision-focused summary vs. bare 'summarise this'    :clock: 10 min · core · any general consumer chat LLM

**Scenario.** You have received a two-page internal report on a proposed office move. Your manager wants a quick read so she can decide whether to approve the move this quarter. You will run two prompts on the same report --- a bare 'summarise this' and a decision-focused version --- and compare the results side by side.

**Your goal.** Two summaries of the same report. Prompt A produces a general recap. Prompt B produces a decision-ready brief with a clear bottom line, pro/con structure, conditions for approval, and a cost-of-delay note.

**Use this material:**

> ```
> INTERNAL REPORT --- PROPOSED OFFICE RELOCATION TO RIVERSIDE BUSINESS PARK
> Prepared by: Facilities & Finance Working Group
> Date: 14 May 2026
> Distribution: Senior Leadership Team
>
> 1. BACKGROUND
> Our current lease at 40 Queen Street expires on 30 September 2026. The
> landlord has offered a three-year renewal at EUR 26.50 per square metre per
> month, a 12 % increase over the current rate of EUR 23.60. Meanwhile the
> Riverside Business Park development (completion: August 2026) is marketing
> fitted-out office space at EUR 21.00 per square metre per month on a
> five-year term with a 14-month rent-free fit-out period already included.
>
> The working group was asked to evaluate whether relocating to Riverside is
> financially and operationally viable in time for a Q3 2026 decision.
>
> 2. COST COMPARISON (ANNUAL, 1 200 m2 FOOTPRINT)
>                            Queen Street (renewal)    Riverside
> Base rent                  EUR 381 600               EUR 302 400
> Service charge             EUR   54 000              EUR   48 000
> Parking (40 spaces)        EUR   72 000              EUR   36 000
> Insurance                  EUR    9 200              EUR    8 100
> -------------------------------------------------------------------
> Total occupancy cost       EUR  516 800              EUR  394 500
> Annual saving at Riverside                           EUR  122 300
>
> One-off relocation costs are estimated at EUR 85 000 (IT cabling, furniture
> logistics, staff downtime). The net saving in Year 1 after relocation costs
> is therefore approximately EUR 37 300, rising to EUR 122 300 per year from
> Year 2 onward.
>
> 3. OPERATIONAL FACTORS
> - Commute: Riverside is 2.4 km farther from the central train station
>   (12 min extra by bus, dedicated cycle path available). A staff survey
>   (n = 94, 68 % response rate) showed 31 % neutral, 27 % positive (prefer
>   newer building and parking), 42 % negative (longer commute).
> - Building spec: Riverside offers BREEAM Excellent rating, 24/7 access,
>   on-site cafe, EV charging for 12 vehicles. Queen Street has no EV
>   charging and limited after-hours HVAC.
> - IT readiness: Riverside has pre-installed Cat 6A cabling and dual-fibre
>   entry. Our IT team estimates a 10-business-day migration window with one
>   weekend of partial downtime.
> - Lease flexibility: Queen Street offers a break clause at 18 months.
>   Riverside has no break clause before Year 3.
>
> 4. RISKS
> - Timeline: Riverside completion is currently on schedule but any delay
>   beyond September 2026 would force a short-term Queen Street extension at
>   the higher rate, adding an estimated EUR 6 600 per month.
> - Staff retention: HR flags that 11 employees (8 % of headcount) listed
>   commute length as a top-3 factor in their last engagement survey.
>   Targeted mitigation (subsidised transport passes, two additional
>   remote-work days) is costed at EUR 18 000 per year.
> - Contractual: The Riverside landlord requires a deposit equal to three
>   months' rent (EUR 75 600) payable on signing.
>
> 5. RECOMMENDATION
> The working group recommends proceeding with Riverside subject to:
> a) Confirmation of the August 2026 completion date by 15 June.
> b) Negotiation of a Year-3 break clause.
> c) Board approval of the deposit and relocation budget (total EUR 160 600).
>
> If conditions (a) and (b) are not met by 30 June 2026, the group recommends
> renewing at Queen Street with the 18-month break clause to preserve future
> optionality.
>
> --- END OF REPORT ---
> ```

**Starter prompt** (fill the [BRACKETS]):

Prompt A (bare):
```
Summarise this report.

[PASTE REPORT]
```

Prompt B (decision-focused):
```
Extract the key facts from this report to help me decide whether to
[DECISION --- e.g. approve the office move this quarter]. Present your answer as:
1. One-sentence bottom line
2. Three strongest arguments FOR
3. Three strongest arguments AGAINST
4. Conditions that must be true for a YES
5. What I lose if I delay the decision

Audience: [AUDIENCE --- e.g. a non-technical senior manager who has 2 minutes]
Format: [FORMAT --- e.g. numbered list, no jargon, max 200 words]

[PASTE REPORT]
```

**Steps**
1. Copy the report from the workbook (Input Data section).
2. Open your chat LLM. Paste and send Prompt A (bare 'summarise this') with the report.
3. Read the output. Note what it covers and what it leaves out.
4. Start a NEW chat (or clear context). Paste Prompt B, filling in the three [BRACKETED] placeholders with your own wording, then paste the same report and send.
5. Compare the two outputs side by side: which one would actually help your manager make the go/no-go decision in two minutes?

**Your output** _(write or paste below)_
> ____________________________________________
> ____________________________________________
> ____________________________________________
> ____________________________________________

**Self-check** --- you're done when:
- [ ] Prompt B's output contains a clear one-sentence recommendation (bottom line).
- [ ] Prompt B's output lists at least two concrete financial figures from the report (e.g. EUR 122 300 annual saving, EUR 160 600 upfront cost).
- [ ] Prompt B's output names at least one condition or risk that could change the decision (e.g. completion date confirmation by 15 June).
- [ ] The learner can articulate at least one concrete piece of decision-relevant information present in Prompt B's output but absent from Prompt A's output.

**Before you trust it:** Before trusting either summary, check: (1) Are the financial figures quoted in the summary accurate against the original report? (2) Has the model invented any deadline, percentage, or condition not in the source? (3) Are named parties (Riverside, Queen Street) correct and not swapped?

**Takeaway.** Replace 'summarise this' with 'extract X for audience Y in format Z' --- specifying the decision, the reader, and the structure turns a generic recap into an actionable brief.

_Stretch (optional):_ Run Prompt B a second time but change the decision to 'decide whether to renew at Queen Street instead.' Compare how the same facts are reframed when the decision question flips.

---

## Exercise 5 · Week plan from a brain dump    :clock: 12 min · core · any general consumer chat LLM

**Scenario.** It is Sunday evening and you have scribbled a brain dump of everything on your plate for the coming week. You ask your LLM to turn it into a prioritised plan with effort estimates and a day-by-day schedule. The brain dump deliberately contains tricky date references that the model is likely to get wrong --- your job is to catch every mistake before you trust the plan.

**Your goal.** A day-by-day week plan (Mon 1 Jun -- Fri 5 Jun) with effort estimates, plus a list of date errors the learner found and corrected.

**Use this material:**

> ```
> --- BRAIN DUMP (Sunday 31 May 2026, evening) ---
>
> Stuff I need to get done this week:
>
> - Finish the budget slides for Hanna. She needs them by Thursday 4 June.
>   Important --- last time I was late and she had to wing it.
> - Dentist appointment already booked for Tuesday 2 June at 14:00, takes
>   about 1.5 hrs with travel.
> - Reply to Marcus's contract question --- he first emailed 10 days ago
>   (that was Wednesday 21 May) and I still haven't answered. Embarrassing.
> - Team lunch is on the first Friday of June. Book a restaurant for 8
>   people.
> - Renew my parking permit --- it expires exactly two weeks from today, so
>   that's Sunday 14 June. The office that handles it is closed on weekends,
>   so I need to go before that.
> - Prep talking points for the board call. The call is the second Monday of
>   June.
> - Order Liam's birthday present --- his birthday is Saturday 13 June and
>   delivery takes 5 business days so I need to order by... some day this
>   week?
> - Water the office plants (every Monday and Thursday).
> - Submit the travel-expense report. Deadline is 30 days after the trip,
>   and the trip ended 1 May 2026, so the deadline should be Sunday 31 May
>   --- wait, that's today! Or is it tomorrow? Need to check.
>
> ---
> ```

**Starter prompt** (fill the [BRACKETS]):
```
Here is my brain dump of tasks for the coming week. Today is Sunday 31 May 2026.

1. Turn this into a prioritised plan for Monday 1 June to Friday 5 June.
2. For each task give an effort estimate (S = under 30 min, M = 30-90 min,
   L = half-day).
3. Assign each task to a specific day (or days), with the most urgent items
   earliest.
4. Flag any scheduling conflicts or tight deadlines.

Brain dump:
[PASTE BRAIN DUMP]

[OPTIONAL: add any real tasks of your own to the list]
```

**Steps**
1. Paste the brain dump into the starter prompt and send it to your LLM.
2. Read the plan the model produces. Before trusting any date, open a real calendar (phone, laptop, or web) for June 2026.
3. Check EVERY date and day-of-week pair the model outputs. Write down each one that is wrong or suspicious.
4. Check the delivery-date arithmetic for Liam's present: does '5 business days back from 13 June' land where the model says?
5. Check whether the model caught the travel-expense deadline ambiguity (31 May is today --- is it already too late, or is it due by end of day?).
6. Correct any errors in the plan and note what you changed.

**Your output** _(write or paste below)_
> ____________________________________________
> ____________________________________________
> ____________________________________________
> ____________________________________________

**Self-check** --- you're done when:
- [ ] The plan covers all nine tasks from the brain dump, assigned to specific days.
- [ ] Every task has an effort estimate (S / M / L).
- [ ] The learner identified at least one date or day-of-week error the model made (the brain dump contains multiple traps).
- [ ] The learner verified the Liam's-present order-by date using real calendar arithmetic (5 business days before Sat 13 June = order by Mon 8 June at the latest, since ordering Mon 8 means delivery Fri 12 June).
- [ ] The travel-expense deadline ambiguity is acknowledged --- the learner noted it needs same-day action or is already overdue.

**Before you trust it:** Open a real calendar for June 2026 and cross-check every date and day-of-week in the model's output. Confirm the 'first Friday of June', the 'second Monday of June', the 5-business-day countdown, and the 30-day deadline. Fix anything wrong before adopting the plan.

**Takeaway.** LLMs are unreliable at date and calendar arithmetic --- always verify every date in a generated plan against a real calendar before acting on it.

_Stretch (optional):_ Add three of your own real tasks (including at least one with a genuine deadline) to the brain dump, regenerate the plan, and verify those dates too.

---

## Exercise 6 · Build your prompt library and verify an earlier output    :clock: 10 min · core · participant's own earlier work

**Scenario.** You have been saving prompts throughout this session. Now assemble them into a personal prompt library table (Task | Prompt | Notes) and then pick one output you generated earlier and run the 5-item verification checklist against it.

**Your goal.** A 4-row prompt library table with Task, Prompt, and Notes columns filled in, plus a completed 5-item verification checklist applied to one earlier output showing pass/fail per item and any corrections needed.

**Use this material:**

Use your own prompts and outputs from exercises 2--5. If you do not have them, use the fallback library and sample output below.

> **Fallback prompt library:**
>
> | # | Task | Prompt | Notes |
> |---|------|--------|-------|
> | 1 | Extract-then-reply (email) | "Here is an email thread. First tell me in one sentence what the latest message is actually asking. Then draft a reply that is [TONE] and addresses only that ask. Thread: [PASTE THREAD]" | Always read the extracted ask before the draft; rewrite at least one line in your own voice |
> | 2 | Bullets to memo | "Turn the following rough bullets into a one-page internal memo. Fix grammar and clarity. Do NOT change any numbers or technical terms. Bullets: [PASTE BULLETS]" | The change/preserve constraint prevents the model from inventing figures |
> | 3 | Decision-focused summary | "Summarise the following report to help me decide whether to [DECISION]. Pull out only the facts that bear on that decision. Format: 3-5 bullet points, then a one-sentence recommendation. Report: [PASTE REPORT]" | Compare against a bare 'summarise this' to see the difference |
> | 4 | Brain-dump to week plan | "Here is everything on my mind for next week. Turn it into a prioritised week plan: columns for Day, Task, Effort estimate, Priority. Put the highest-effort items on my least-busy days. Brain dump: [PASTE BRAIN DUMP]" | Always verify every date against a real calendar; the model gets date arithmetic wrong |
>
> **Fallback sample output to verify:**
>
> The following is a model-generated reply to a messy email thread (from Exercise 2). Apply the verification checklist to it.
>
> "Hi Sarah,
>
> Thanks for the update. Based on the thread, I understand the core request is to confirm the Q3 budget figures before Friday's board meeting.
>
> Here is what I propose:
> - I will send the updated spreadsheet by Wednesday 14 August
> - The revised total is EUR 142,500, reflecting the 12% reduction Marcus suggested
> - I have cc'd Priya so Finance can validate the numbers independently
>
> Let me know if I have missed anything.
>
> Best regards,
> Alex"

**Starter prompt** (fill the [BRACKETS]):

This exercise has two parts and does not require a model prompt.

**Part A --- Prompt Library:** Copy the table template below and fill it in with prompts you used in exercises 2--5. Add a 'Notes' column with one lesson you learned per prompt.

| # | Task | Prompt | Notes |
|---|------|--------|-------|
| 1 | [TASK FROM E2] | [YOUR E2 PROMPT] | [WHAT YOU LEARNED] |
| 2 | [TASK FROM E3] | [YOUR E3 PROMPT] | [WHAT YOU LEARNED] |
| 3 | [TASK FROM E4] | [YOUR E4 PROMPT] | [WHAT YOU LEARNED] |
| 4 | [TASK FROM E5] | [YOUR E5 PROMPT] | [WHAT YOU LEARNED] |

**Part B --- Verification Checklist:** Pick one model output from an earlier exercise and run through all five checks:
1. **Facts:** Is every factual claim accurate? (check against the original input)
2. **Names:** Are all person and company names spelled correctly and attributed to the right actions?
3. **Numbers:** Are all figures, percentages, and amounts correct? (recalculate if needed)
4. **Links/references:** Are any URLs, document titles, or citations real? (if present, verify)
5. **Tone:** Does the text match the tone you intended, and would you be comfortable sending it as-is?

**Steps**
1. Open a blank document or note (or use the workbook template).
2. For each of exercises 2--5, copy the prompt you used into the library table. If you did not save one, use the fallback prompts from the input data.
3. In the Notes column, write one practical lesson per prompt (e.g. 'always read the extracted ask first', 'specify what NOT to change').
4. Choose one model output from an earlier exercise (or use the fallback sample output).
5. Walk through all 5 verification checklist items against that output. Write a pass/fail note for each.
6. If you find an error, note what category it falls into (fact, name, number, link, or tone) and how you would fix it.

**Your output** _(write or paste below)_
> ____________________________________________
> ____________________________________________
> ____________________________________________
> ____________________________________________

**Self-check** --- you're done when:
- [ ] The prompt library contains at least 4 entries covering exercises 2--5 (or fallback equivalents).
- [ ] Each entry has a meaningful Notes field capturing a transferable lesson, not just a task label.
- [ ] All 5 verification checklist items are explicitly addressed with a pass or fail judgement.
- [ ] At least one concrete error or risk is identified in the checked output (the fallback sample contains a date that cannot be verified and a figure worth double-checking).
- [ ] The library is structured clearly enough that the learner could reuse a prompt from it next week without re-reading the workbook.

**Before you trust it:** Swap your completed checklist with a neighbour: can they spot an issue you missed? If working alone, re-read the checked output once more looking only for confidentiality leaks (real names, internal project codes, sensitive figures that should not have been pasted into a consumer tool).

**Takeaway.** A prompt library turns one-off experiment wins into a durable personal workflow; the 5-item checklist (facts, names, numbers, links, tone) is the safety net you apply every time before trusting or sending AI output.

_Stretch (optional):_ Add a fifth row to your library for a task you do regularly at work that was not covered in the exercises. Write the prompt template, predict which checklist items are most likely to fail for that task, and note them in the Notes column.

---

## Your prompt library

Use this page to collect the prompt templates that worked best for you. Keep it somewhere you will find it next week.

| # | Task | My prompt | Notes |
|---|------|-----------|-------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |
| 8 | | | |
