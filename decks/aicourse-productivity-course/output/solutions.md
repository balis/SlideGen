# Practical AI for Professionals (Session 2) — Solution Keys (facilitator)

_Sample outputs are dated snapshots from one real model run at generation time.
Model output drifts and the model used here may differ from the participant's tool,
so treat each as a reference, not a guarantee — the date and model are stamped._

---

## Exercise 1 · Sort the task list

**The prompt that produced this output:**

```
Here are 10 office tasks. For each task, assign it to one zone:
- GREEN = the LLM handles this well on its own
- YELLOW = the LLM can help, but the result needs human verification or extra scaffolding
- RED = do not use an LLM for this

After sorting all 10, pick the two tasks you found hardest to place and write one sentence each explaining your reasoning.

Tasks:
1. Rewrite a paragraph from your quarterly update so it sounds more concise and professional.
2. Draft a polite reply declining a meeting invitation you cannot attend.
3. Calculate the exact budget variance between Q1 actuals (EUR 41,837.12) and Q1 forecast (EUR 39,500.00), including the percentage difference.
4. Summarise a 2-page policy document into 5 bullet points for your team.
5. Decide which of three job candidates to invite to a final interview.
6. Paste a customer complaint email and ask the LLM to identify the core issue and suggest a response outline.
7. Ask the LLM to list all colleagues who were absent last Friday based on your company's internal HR system.
8. Shift the tone of a project status update from informal Slack-style to a formal board-ready paragraph.
9. Generate three subject-line options for a newsletter about an upcoming office move.
10. Upload a spreadsheet containing employee salaries and ask the LLM to find who earns above the median.
```

**Live-validated sample output** — _Claude (claude-opus-4-6, self-execution), 2026-05-27T00:00:00Z_:

> Here is my sorting of the 10 tasks:
>
> | # | Task | Zone |
> |---|------|------|
> | 1 | Rewrite a paragraph from your quarterly update so it sounds more concise and professional | GREEN |
> | 2 | Draft a polite reply declining a meeting invitation you cannot attend | GREEN |
> | 3 | Calculate the exact budget variance between Q1 actuals (EUR 41,837.12) and Q1 forecast (EUR 39,500.00), including the percentage difference | YELLOW |
> | 4 | Summarise a 2-page policy document into 5 bullet points for your team | GREEN |
> | 5 | Decide which of three job candidates to invite to a final interview | RED |
> | 6 | Paste a customer complaint email and ask the LLM to identify the core issue and suggest a response outline | YELLOW |
> | 7 | Ask the LLM to list all colleagues who were absent last Friday based on your company's internal HR system | RED |
> | 8 | Shift the tone of a project status update from informal Slack-style to a formal board-ready paragraph | GREEN |
> | 9 | Generate three subject-line options for a newsletter about an upcoming office move | GREEN |
> | 10 | Upload a spreadsheet containing employee salaries and ask the LLM to find who earns above the median | RED |
>
> Two hardest to place:
>
> Task 3 (Budget variance calculation): I placed this in YELLOW rather than GREEN because while the task looks straightforward, LLMs are known to make errors with decimal arithmetic and percentage calculations — the model might get close but could easily slip on the exact figures, so you should always verify the maths with a calculator or spreadsheet.
>
> Task 6 (Customer complaint analysis): I placed this in YELLOW because the LLM is genuinely good at identifying themes and drafting outlines, but a customer complaint email could contain personal data (names, account numbers, order details), so you need to check whether pasting it into a consumer tool is allowed under your data policy, and you should still review the suggested response for tone and accuracy before sending.

**What "good" looks like:** All 10 tasks are assigned to exactly one zone. Tasks 7 and 10 land in RED (LLM has no access to internal HR systems; salary data is confidential and should not go into a consumer tool). Task 3 lands in YELLOW or RED — never GREEN. Tasks 1, 2, 8, and 9 land in GREEN. The two justifications give concrete capability or limitation reasons — not just "it felt risky."

**Common pitfalls:**
- Placing the budget-variance task in GREEN because it looks simple — LLMs frequently get decimal arithmetic and percentages wrong.
- Forgetting that Task 7 is impossible (the LLM has no access to internal HR systems), not just risky.
- Placing Task 10 in YELLOW instead of RED — the issue is not accuracy but that you would be uploading confidential salary data to a consumer tool.
- Accepting the model's sorting without questioning it, defeating the purpose of building your own judgement.

**Debrief prompts:**
1. "Which zone surprised you the most when the model placed a task there — and did you agree or change it?"
2. "What's the difference between Task 7 (can't do it) and Task 10 (shouldn't do it) — does that distinction matter in practice?"
3. "If you had to give a colleague one rule for deciding GREEN vs. RED before they ever open a chat window, what would it be?"

---

## Exercise 2 · Reply to a messy email thread

**The prompt that produced this output:**

```
Here is an email thread. First, tell me in one sentence what the latest message (Message 5) is actually asking me to do or decide. Then draft a reply from me (Alex) that is friendly and decisive and addresses only that ask. Keep the reply under 120 words.

Thread:
FROM: Priya Novak <priya.novak@example.com>
TO: Jordan Lee <jordan.lee@example.com>, Sam Torres <sam.torres@example.com>
SUBJECT: Re: Re: Re: Q3 Offsite — venue & catering
DATE: Tuesday 10:14 AM

--- Message 1 (Monday 8:02 AM) — Priya Novak ---
Hi Jordan, hi Sam,
Quick heads-up: the Riverside Conference Centre just confirmed they can hold 40 people on 18 September, but they need a final headcount by this Friday. Can one of you pull that together? Also, they offer in-house catering or we can bring our own — any preferences?

--- Message 2 (Monday 9:47 AM) — Sam Torres ---
Riverside sounds great. I think last year we had 33 attendees, but a few more people joined the analytics team since then. I'd guess 36–38 this time. For catering, their in-house lunch menu looked a bit limited when I checked the website — maybe we should get quotes from GreenPlate too?

--- Message 3 (Monday 11:30 AM) — Jordan Lee ---
I actually already emailed the team leads yesterday to ask for names. So far I have 29 confirmed, waiting on Product and Finance. Catering-wise, I'm fine either way, but remember last year two people had allergies that the venue couldn't handle.

--- Message 4 (Monday 4:55 PM) — Priya Novak ---
Thanks Jordan — great that you started the count. Could you also find out whether Riverside's in-house catering handles nut-free and gluten-free? If not, we should definitely go with GreenPlate.
Sam, unrelated, but do you have the slide template from last year's offsite? I want to reuse the branding.

--- Message 5 (Tuesday 10:14 AM) — Sam Torres ---
I'll dig up the slide template after lunch. Jordan, while you're checking with Riverside on dietary options, could you also ask if they have breakout rooms we can book for the afternoon workshops? We had that awkward hallway-session problem last time. Priya — should I go ahead and request a GreenPlate quote as a backup, or wait until Jordan hears back?
```

**Live-validated sample output** — _claude-opus-4-6 (own model), 2026-05-27T00:00:00Z_:

> One-sentence ask: Sam is asking Priya whether he should go ahead and request a GreenPlate catering quote now as a backup, or wait until Jordan hears back from Riverside about their dietary options.
>
> Draft reply:
>
> Hi Sam,
>
> Great thinking on getting ahead of the catering question. Go ahead and request the GreenPlate quote now — no point waiting when we're on a Friday deadline for the headcount anyway, and having a backup quote gives us options regardless of what Jordan hears back from Riverside.
>
> On the slide template — thanks for digging that up, no rush as long as I have it by end of week.
>
> Jordan — yes please on the breakout rooms question when you contact Riverside. Last year's hallway sessions were not ideal!
>
> Best,
> Alex

**What "good" looks like:** The one-sentence extract correctly identifies Sam's question to Priya (proceed with GreenPlate quote now, or wait?). The reply gives a clear decision — yes or no — rather than restating the question. Side topics (slide template, breakout rooms) are acknowledged at most in one brief line each and do not hijack the reply. Tone matches what the learner specified. Point out that the one-sentence step does the heavy lifting: without it, most people would write a reply that wanders across the whole thread.

**Common pitfalls:**
- Skipping the extract step and asking the model to "just reply to this thread" — which often produces a reply to the most recent surface topic rather than the underlying decision request.
- Accepting the model's draft verbatim without personalising any line, resulting in obviously AI-generated language.
- Letting the reply address every topic in the thread instead of focusing on the actual ask.

**Debrief prompts:**
1. "Did the model get the one-sentence ask right on the first try, or did you have to correct it? What did it latch onto instead?"
2. "Read your final reply out loud — which line did you rewrite, and how did it change the feel of the message?"
3. "Would you be comfortable sending this reply without checking it? What would you still want to verify before hitting send?"

---

## Exercise 3 · Bullets to memo

**The prompt that produced this output:**

```
Below are rough bullet-point notes from a site visit. Turn them into a one-page professional memo addressed to the VP of Operations.

Constraints:
- Fix grammar, spelling, and sentence flow for clarity
- Do NOT change any numbers, dates, currency amounts, product names, or technical terms — keep them exactly as they appear
- Use a concise and professional tone suitable for senior leadership
- Structure the memo with: Subject line, Summary (2-3 sentences), Key Findings, Recommended Actions, and Timeline

Notes:
SITE VISIT NOTES — Greenfield Distribution Centre, 14 May 2026

- toured the new Greenfield DC with Priya Sharma (ops director) and two shift leads
- facility is 24,000 m² across 3 zones: inbound, pick-pack, outbound
- current throughput 8,400 parcels/hr but rated capacity is 11,200 parcels/hr — running at 75% utilisation
- main bottleneck is the sorter divert at Zone 2; belt speed limited to 1.8 m/s because older OCR cameras misread barcode at higher speeds
- Priya wants to upgrade to Cognex DataMan 380 cameras — vendor quote EUR 74,500 for 12 units incl. installation
- expected result: belt speed up to 2.4 m/s, throughput gain ~1,400 parcels/hr
- ROI calc from ops team: payback in 14 weeks at current volume
- secondary issue: HVAC in Zone 3 is failing intermittently — 3 unplanned shutdowns last quarter, each ~45 min, costing roughly EUR 6,200 per event in overtime + delayed shipments
- Priya asked for a budget decision on the cameras by 31 May and wants the HVAC on the Q3 capex list
- overall impression: team is competent, facility is clean, biggest risk is doing nothing on the sorter before peak season (starts 1 Sep)
```

**Live-validated sample output** — _Claude (claude-opus-4-6, self-execution), 2026-05-27T00:00:00Z_:

> MEMO
>
> To: Maria Chen, VP of Operations
> From: [Author]
> Date: 14 May 2026
> Subject: Greenfield Distribution Centre Site Visit — Camera Upgrade and HVAC Findings
>
> Summary
> On 14 May 2026, a site visit to the Greenfield Distribution Centre was conducted with Ops Director Priya Sharma and two shift leads. The facility is performing well at 75% utilisation but faces a sorter bottleneck that limits throughput, along with recurring HVAC failures in Zone 3. Two capital investments are recommended to address these issues before peak season begins on 1 Sep.
>
> Key Findings
>
> - The Greenfield DC spans 24,000 m² across three zones: inbound, pick-pack, and outbound.
> - Current throughput is 8,400 parcels/hr against a rated capacity of 11,200 parcels/hr, representing 75% utilisation.
> - The primary bottleneck is the sorter divert at Zone 2, where belt speed is limited to 1.8 m/s because older OCR cameras misread barcodes at higher speeds.
> - Upgrading to Cognex DataMan 380 cameras (12 units, vendor quote EUR 74,500 including installation) is projected to increase belt speed to 2.4 m/s and deliver a throughput gain of approximately 1,400 parcels/hr.
> - The operations team estimates a payback period of 14 weeks at current volume.
> - HVAC in Zone 3 is failing intermittently, causing 3 unplanned shutdowns last quarter, each lasting approximately 45 min and costing roughly EUR 6,200 per event in overtime and delayed shipments.
>
> Recommended Actions
>
> 1. Approve the Cognex DataMan 380 camera upgrade (EUR 74,500) before peak season begins on 1 Sep.
> 2. Add the Zone 3 HVAC remediation to the Q3 capex list.
>
> Timeline
>
> - Budget decision on camera upgrade required by 31 May.
> - HVAC to be included in Q3 capital expenditure planning.
> - Peak season begins 1 Sep — camera upgrade should be completed before this date.
>
> Overall Assessment
> The facility team is competent and the site is well maintained. The greatest risk is inaction on the sorter upgrade before peak season.

**What "good" looks like:** Every number from the bullets survives unchanged (8,400 parcels/hr, 11,200 parcels/hr, 75%, 24,000 m², 1.8 m/s, 2.4 m/s, ~1,400 parcels/hr, EUR 74,500, 14 weeks, 3 shutdowns, ~45 min, EUR 6,200). All dates are exact (14 May 2026, 31 May, 1 Sep, Q3). Technical terms are intact (Cognex DataMan 380, OCR, HVAC, sorter divert). The structure (Subject, Summary, Key Findings, Recommended Actions, Timeline) is present. Bullet fragments from the original are gone — the body reads in full sentences. Point out that the change/preserve constraint is what prevents the model from "helpfully" rounding EUR 74,500 to ~EUR 75K.

**Common pitfalls:**
- The model rounds or reformats numbers (e.g., "24,000 m²" becomes "24,000 square metres" or "EUR 74,500" becomes "~EUR 75K").
- The model drops the less prominent data points (e.g., the HVAC issue or the EUR 6,200 per-event cost).
- The learner forgets to verify and assumes the constraint was followed because it was stated in the prompt.
- The model invents details not present in the bullets (e.g., adding a specific HVAC vendor or a cost estimate for the HVAC repair).

**Debrief prompts:**
1. "Did your model change any number or technical term despite the explicit constraint? Which one, and why do you think it happened?"
2. "What is the difference between telling the model 'be accurate' and telling it 'do not change these specific values'?"
3. "Where else in your day-to-day work would a change/preserve constraint be useful — what data do you need to protect from 'improvement'?"

---

## Exercise 4 · Decision-focused summary vs. bare 'summarise this'

**The prompt that produced this output:**

```
Prompt A (bare):
"Summarise this report.

[FULL REPORT TEXT PASTED — the office-relocation report from input_data]"

Prompt B (decision-focused):
"Extract the key facts from this report to help me decide whether to approve the office move this quarter. Present your answer as:
1. One-sentence bottom line
2. Three strongest arguments FOR
3. Three strongest arguments AGAINST
4. Conditions that must be true for a YES
5. What I lose if I delay the decision

Audience: a non-technical senior manager who has 2 minutes
Format: numbered list, no jargon, max 200 words

[FULL REPORT TEXT PASTED — the office-relocation report from input_data]"
```

**Live-validated sample output** — _Claude Opus 4.6 (Anthropic, via self-execution as the validating agent), 2026-05-27T00:00:00Z_:

> --- PROMPT A OUTPUT (bare 'summarise this') ---
> This report evaluates whether the company should relocate from its current office at 40 Queen Street to the new Riverside Business Park when the current lease expires on 30 September 2026. The Queen Street landlord is offering a three-year renewal at EUR 26.50/m²/month (a 12% increase), while Riverside offers space at EUR 21.00/m²/month on a five-year term with a 14-month rent-free fit-out period already included.
>
> For a 1,200 m² footprint, Riverside would save EUR 122,300 annually in total occupancy costs (EUR 394,500 vs EUR 516,800). One-off relocation costs are estimated at EUR 85,000, yielding a net Year 1 saving of approximately EUR 37,300. On the operational side, Riverside is 2.4 km farther from the train station, and a staff survey showed 42% of respondents view the longer commute negatively. However, Riverside offers a newer building with BREEAM Excellent rating, EV charging, and better IT infrastructure. Key risks include a possible construction delay, potential staff retention concerns (8% of employees cite commute as a top factor), and a required three-month deposit of EUR 75,600. The working group recommends proceeding with Riverside, subject to confirmation of the completion date by 15 June, negotiation of a Year-3 break clause, and board approval of EUR 160,600 in upfront costs. If these conditions are not met by 30 June 2026, they recommend renewing at Queen Street with an 18-month break clause.
>
> --- PROMPT B OUTPUT (decision-focused) ---
> 1. Bottom line: The move to Riverside saves EUR 122,300 per year and pays for itself within the first year, but only if the new building is confirmed on time and you secure a break clause.
>
> 2. Three strongest arguments FOR:
>    - Annual cost saving of EUR 122,300 (EUR 516,800 vs EUR 394,500) starting Year 2, with EUR 37,300 net saving even in Year 1 after relocation costs
>    - Newer, better-equipped building: BREEAM Excellent rating, EV charging, modern IT cabling, 24/7 access
>    - Staying at Queen Street means paying 12% more rent with no building upgrades
>
> 3. Three strongest arguments AGAINST:
>    - 42% of surveyed staff are negative about the longer commute (2.4 km farther from the train station); 8% of headcount flag commute as a retention factor
>    - No break clause before Year 3 at Riverside, locking you in for longer than Queen Street's 18-month break
>    - Construction delay risk: if Riverside is not ready by September, a temporary Queen Street extension costs EUR 6,600/month at the higher rate
>
> 4. Conditions that must be true for a YES:
>    - Riverside completion confirmed by 15 June 2026
>    - Year-3 break clause successfully negotiated
>    - Board approves EUR 160,600 upfront (EUR 85,000 relocation + EUR 75,600 deposit)
>
> 5. What you lose if you delay:
>    - The Queen Street lease expires 30 September 2026; delaying past 30 June forces either the higher-rate renewal or a scramble for short-term space
>    - Each month of delay at the renewed Queen Street rate costs roughly EUR 10,200 more than Riverside would

**What "good" looks like:** Prompt B's output has a clear one-sentence bottom line. It includes at least two concrete financial figures (e.g., EUR 122,300 annual saving, EUR 160,600 upfront cost). It names at least one condition that could change the decision (completion confirmation by 15 June). The learner can point to at least one piece of decision-relevant information in Prompt B that Prompt A does not surface — the cost-of-delay framing and the structured pro/con list are the obvious examples. If Prompt A and Prompt B outputs look nearly identical, the learner likely used a vague [DECISION] placeholder — point out that specificity is the lever.

**Common pitfalls:**
- Leaving the [DECISION] placeholder vague ('decide about the report') instead of specific ('approve the office move this quarter') — the more specific the decision, the sharper the output.
- Running both prompts in the same chat session, so the model's second answer is influenced by the first.
- Accepting the structured summary without verifying that the numbers match the original report.

**Debrief prompts:**
1. "What appeared in Prompt B's output that was completely absent from Prompt A's — and would that missing piece matter if you were the manager making the call?"
2. "How specific was your [DECISION] placeholder? What would change if you made it more precise?"
3. "Did either output contain a number or fact that you could not verify from the report? How would you catch that before forwarding it?"

---

## Exercise 5 · Week plan from a brain dump

**The prompt that produced this output:**

```
Here is my brain dump of tasks for the coming week. Today is Sunday 31 May 2026.

1. Turn this into a prioritised plan for Monday 1 June to Friday 5 June.
2. For each task give an effort estimate (S = under 30 min, M = 30-90 min, L = half-day).
3. Assign each task to a specific day (or days), with the most urgent items earliest.
4. Flag any scheduling conflicts or tight deadlines.

Brain dump:
--- BRAIN DUMP (Sunday 31 May 2026, evening) ---

Stuff I need to get done this week:

- Finish the budget slides for Hanna. She needs them by Thursday 4 June. Important — last time I was late and she had to wing it.
- Dentist appointment already booked for Tuesday 2 June at 14:00, takes about 1.5 hrs with travel.
- Reply to Marcus's contract question — he first emailed 10 days ago (that was Wednesday 21 May) and I still haven't answered. Embarrassing.
- Team lunch is on the first Friday of June. Book a restaurant for 8 people.
- Renew my parking permit — it expires exactly two weeks from today, so that's Sunday 14 June. The office that handles it is closed on weekends, so I need to go before that.
- Prep talking points for the board call. The call is the second Monday of June.
- Order Liam's birthday present — his birthday is Saturday 13 June and delivery takes 5 business days so I need to order by… some day this week?
- Water the office plants (every Monday and Thursday).
- Submit the travel-expense report. Deadline is 30 days after the trip, and the trip ended 1 May 2026, so the deadline should be Sunday 31 May — wait, that's today! Or is it tomorrow? Need to check.

---
```

**Live-validated sample output** — _Claude Opus 4 (claude-opus-4-6), acting as both the target LLM and the validator, 2026-05-27T00:00:00Z_:

> Here's your prioritised week plan for Monday 1 June – Friday 5 June 2026:
>
> URGENT — Action needed TODAY (Sunday 31 May):
> - Submit travel-expense report — The deadline is 30 days after your trip ended (1 May), which puts it at 31 May — that's today. Submit it tonight if your system allows online submission, or first thing Monday morning with a note explaining the one-day delay. Effort: S
>
> Monday 1 June
> | Task | Effort | Priority | Notes |
> | Submit travel-expense report (if not done Sunday) | S | Overdue | Do this first thing |
> | Reply to Marcus's contract question | S | High | 10 days overdue — already embarrassing |
> | Water office plants | S | Medium | Recurring |
> | Start budget slides for Hanna | L | High | Due Thursday — start early |
>
> Tuesday 2 June
> | Task | Effort | Priority | Notes |
> | Continue budget slides for Hanna | M | High | Morning block before dentist |
> | Dentist appointment | — | Fixed | 14:00–15:30 (blocked, including travel) |
> | Book restaurant for team lunch (8 people) | S | Medium | Team lunch is Friday 5 June (first Friday of June) |
> | Order Liam's birthday present | S | High | His birthday is Saturday 13 June. 5 business days delivery = order by Wednesday 4 June at the latest (Wed 4 → Thu 5 → Fri 6 → Mon 9 → Tue 10 = arrives Wed 10 June) |
>
> Wednesday 3 June
> | Task | Effort | Priority | Notes |
> | Finish budget slides for Hanna | M–L | High | Final polish — deliver by end of day |
> | Renew parking permit | S | Medium | Expires Sunday 14 June; any day this week works |
>
> Thursday 4 June
> | Task | Effort | Priority | Notes |
> | Budget slides → deliver to Hanna | S | Deadline | Hard deadline — morning handoff |
> | Prep talking points for board call | M | High | Board call is Monday 8 June (second Monday of June) |
> | Water office plants | S | Medium | Recurring |
>
> Friday 5 June
> | Task | Effort | Priority | Notes |
> | Finish board call talking points | M | High | Board call is Monday — finalise today |
> | Team lunch | — | Fixed | First Friday of June |
>
> Scheduling conflicts / tight deadlines flagged:
> 1. Travel-expense report is due TODAY (31 May) — highest urgency
> 2. Marcus's email is already 10+ days old — reputational risk
> 3. Budget slides have a hard Thursday deadline — block significant time Mon–Wed
> 4. Liam's present needs to be ordered by Wednesday 4 June to allow 5 business days for delivery before the 13th

**What "good" looks like:** The plan covers all nine tasks from the brain dump. Every task has an effort estimate (S / M / L). The learner found and corrected at least one date error — the sample output contains deliberate traps: the order-by date for Liam's present is stated as Wednesday 4 June, but the correct latest order date is Monday 8 June (5 business days back from Saturday 13 June: Fri 12, Thu 11, Wed 10, Tue 9, Mon 8). Additionally, the brain dump's claim that 21 May was a Wednesday is wrong — 21 May 2026 is a Thursday. The travel-expense ambiguity (31 May is a Sunday, so the effective business deadline was Friday 29 May) is acknowledged. Point out that every date error in this output was the kind a model produces confidently — without hedging or flagging.

**Common pitfalls:**
- Trusting the model's day-of-week labels without checking a real calendar (e.g., the model may say "4 June is Wednesday" when it is actually Thursday).
- Accepting the 5-business-day back-count without manually counting weekends.
- Overlooking that 31 May 2026 is a Sunday, so the travel-expense deadline may effectively be the previous business day (Friday 29 May) or needs immediate action.
- Not noticing if the model silently drops one of the nine tasks.

**Debrief prompts:**
1. "How many date errors did you find — and did any of them surprise you? Which one was easiest to miss?"
2. "The model gave Liam's order-by date as Wednesday 4 June. Walk us through the correct calendar count. What did the model get wrong in its own reasoning?"
3. "If you had acted on this plan without checking, what is the worst real-world consequence that could have resulted?"

---

## Exercise 6 · Build your prompt library and verify an earlier output

**The prompt that produced this output:**

```
This exercise has two parts and does not require a model prompt.

Part A — Prompt Library: Copy the table template below and fill it in with prompts you used in exercises 2-5. Add a 'Notes' column with one lesson you learned per prompt.

| # | Task | Prompt | Notes |
|---|------|--------|-------|
| 1 | Extract-then-reply (email) | "Here is an email thread. First tell me in one sentence what the latest message is actually asking. Then draft a reply that is [TONE] and addresses only that ask. Thread: [PASTE THREAD]" | Always read the extracted ask before the draft; rewrite at least one line in your own voice |
| 2 | Bullets to memo | "Turn the following rough bullets into a one-page internal memo. Fix grammar and clarity. Do NOT change any numbers or technical terms. Bullets: [PASTE BULLETS]" | The change/preserve constraint prevents the model from inventing figures |
| 3 | Decision-focused summary | "Summarise the following report to help me decide whether to [DECISION]. Pull out only the facts that bear on that decision. Format: 3-5 bullet points, then a one-sentence recommendation. Report: [PASTE REPORT]" | Compare against a bare 'summarise this' to see the difference |
| 4 | Brain-dump to week plan | "Here is everything on my mind for next week. Turn it into a prioritised week plan: columns for Day, Task, Effort estimate, Priority. Put the highest-effort items on my least-busy days. Brain dump: [PASTE BRAIN DUMP]" | Always verify every date against a real calendar; the model gets date arithmetic wrong |

Part B — Verification Checklist applied to the fallback sample output:

Sample output under test:
"Hi Sarah,
Thanks for the update. Based on the thread, I understand the core request is to confirm the Q3 budget figures before Friday's board meeting.
Here is what I propose:
- I will send the updated spreadsheet by Wednesday 14 August
- The revised total is EUR 142,500, reflecting the 12% reduction Marcus suggested
- I have cc'd Priya so Finance can validate the numbers independently
Let me know if I have missed anything.
Best regards,
Alex"

Checklist results:
1. Facts — FAIL: No source thread is provided alongside this sample output, so the factual claims (Q3 budget figures, Friday board meeting) cannot be verified. A learner should flag this as unverifiable.
2. Names — CANNOT VERIFY: Sarah, Marcus, Priya, Alex appear but without the original thread we cannot confirm correct attribution. If compared to the E2 thread, these names do not match (E2 has Priya Novak, Sam Torres, Jordan Lee discussing an offsite, not budget figures).
3. Numbers — FAIL: 'EUR 142,500' and '12% reduction' cannot be traced to any source data. Also, 'Wednesday 14 August' is wrong — 14 August 2026 is a Friday, not a Wednesday. This is a clear date-day mismatch.
4. Links/references — PASS: No URLs or citations present, nothing to verify.
5. Tone — PASS: Professional, concise, appropriate for a work email reply.
```

**Live-validated sample output** — _claude-opus-4-6 (self-execution: no external model needed; exercise is a paper/table exercise), 2026-05-27_:

> Part A — Completed prompt library table with 4 rows (one per exercise E2-E5), each containing the fallback prompt and a transferable lesson in the Notes column. Straightforward copy-and-annotate task, no model interaction needed.
>
> Part B — Verification checklist applied to fallback sample output identified two concrete issues:
>   (a) DATE ERROR: 'Wednesday 14 August' — verified via calendar that 14 August 2026 is a Friday, not a Wednesday. Checklist item 3 (Numbers/dates) = FAIL.
>   (b) UNVERIFIABLE FIGURES: EUR 142,500 and the 12% reduction have no traceable source. A careful learner would flag these for double-checking. Checklist item 3 = FAIL.
>   (c) UNVERIFIABLE FACTS: Without the original source thread, the factual claims cannot be confirmed. Checklist item 1 = FAIL.
>   Checklist items 4 (links) and 5 (tone) = PASS.

**What "good" looks like:** The prompt library has at least 4 rows, one per exercise E2–E5. Each Notes field contains a transferable lesson — not just a label. The verification checklist explicitly addresses all 5 items (facts, names, numbers, links, tone) with a pass or fail. At least one concrete error is identified: the date-day mismatch ("Wednesday 14 August" — 14 August 2026 is a Friday) is the clearest catch. The unverifiable figures (EUR 142,500, 12% reduction) are flagged as untraceable. A learner who marks everything PASS without re-reading has failed the exercise.

**Common pitfalls:**
- Copying prompts into the library without adding personalised notes — the library becomes useless within a week.
- Rushing the checklist by marking everything "pass" without actually re-reading the output line by line.
- Skipping the numbers check because the output "looks about right" — the fallback sample has a percentage and a euro amount that should be traced back to source.
- Forgetting the confidentiality dimension: not asking whether the original input should have gone into an enterprise tool instead.

**Debrief prompts:**
1. "Which of the 5 checklist items do you think you are most likely to skip under time pressure — and what is the worst thing that could go wrong if you do?"
2. "Did you catch the date error in the fallback sample? How long did it take — and how would you have caught it if you were in a hurry?"
3. "Look at your prompt library: which prompt would you use again tomorrow? Is there one you would not trust without changes — and why?"

---
