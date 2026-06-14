---
marp: true
theme: default
paginate: true
---

# Practical Productivity with LLMs
Emails, Documents, Summaries, Planning
Practical AI for Professionals · Session 2

<!-- Speaker: Welcome everyone back. Quick check — you should have your chat tool open and ready. Today is all hands-on; these slides just set the stage for the exercises you'll do in your workbook. -->

<!-- Notes:
Arrive with the workbook link or handout ready to share. Confirm everyone has access to their chat tool before moving on. If anyone is new (missed Session 1), pair them with a neighbour who can help with prompting basics.
-->

---

## How this session works

- Six short concepts, each followed by a hands-on exercise
- You work from the **workbook**, not these slides
- Use your own AI assistant (enterprise tool for anything confidential)
- By the end you leave with a **personal prompt library**

<!-- Speaker: Walk through the four bullets quickly. Stress that the workbook is their primary reference — slides are just the signpost. Mention the prompt-library payoff so they know where we're heading. -->

<!-- Notes:
Set expectations early: this is a working session, not a lecture. Remind participants that exercises build on each other — the prompts they write in exercises 2-5 become the raw material for the capstone prompt library in exercise 6. Point to the workbook (digital or printed) and make sure everyone can find Exercise 1.
-->

---

## What AI assistants do well (green zone)

- Drafting, summarising, restructuring, and tone-shifting text are high-reliability tasks for current chat tools <!-- claim:llm_productivity:001 -->
- AI-generated summaries consistently match or beat human-written ones across news, dialogue, and code tasks <!-- claim:llm_productivity:001 -->

<!-- Speaker: Open with "What have you already used a chat tool for?" — collect a few answers, then anchor: drafting and summarising are the sweet spot. -->

<!-- Notes:
This slide sets the floor for the green/yellow/red framework. Let participants share
their own experience first so the claims land as confirmation, not lecture. Keep it
brisk — the exercise right after this block is where the real learning happens.
-->

---

## What needs scaffolding (yellow zone)

- Arithmetic inside word problems degrades: error rates jump up to 14 percentage points as numbers get harder <!-- claim:llm_productivity:002 -->
- Chat tools fabricate citations at high rates — even the best models invent 18-29% of references <!-- claim:llm_productivity:003 -->
- Yellow-zone tasks can still use AI, but you must verify the output yourself

<!-- Speaker: Ask "Has anyone caught a wrong number or a fake link from a chat tool?" — normalise verification as a habit, not a sign of distrust. -->

<!-- Notes:
The two claims here are the strongest motivators for the verification habit you will
reinforce throughout the session. Do not deep-dive the research — just land the
punchline: arithmetic and citations are where the tool trips, so always check.
-->

---

## What to keep out (red zone)

- Sensitive-data leakage is the #2 risk in the OWASP Top 10 for AI apps (2025) — consumer tools may train on what you paste <!-- claim:llm_productivity:004 -->
- Samsung banned ChatGPT after engineers pasted source code, meeting notes, and chip-test data in three incidents within 20 days <!-- claim:llm_productivity:005 -->
- Rule of thumb: confidential data goes only to your organisation's enterprise tool, never a consumer chat

<!-- Speaker: The Samsung story is memorable — tell it briefly, then ask "What data at your workplace would be red-zone?" Let two or three people answer. -->

<!-- Notes:
This is the slide that should make the room slightly uncomfortable — that is the
point. Transition straight into the exercise: "Now let's test your instincts on
ten real-ish tasks."
-->

---

## Exercise 1 · Sort the task list

- **8 min** · Sort 10 office tasks into green / yellow / red zones and justify two choices
- Tool: any general consumer chat LLM
- → Open your workbook: **Exercise 1**

<!-- exercise:E1 -->

<!-- Speaker: Hand out or display the 10-task list. Tell them to paste it into their chat tool, read the model's sorting, then decide whether they agree. Call time at 8 minutes. -->

<!-- Notes:
Facilitation: circulate and watch for boundary tasks (budget variance, salary
upload). The most common stumbling point is placing the salary task in yellow
instead of red — the issue is confidentiality, not accuracy. Surface two or three
boundary disagreements in the debrief that follows.
-->

---

## Debrief — your task-fit rule of thumb

- Before handing a task to an AI assistant, ask three questions:
  1. Does it need private or confidential data?
  2. Does it need precise numbers I cannot easily check?
  3. Does the outcome require a final human judgement call?
- Any "yes" shifts the task from green toward yellow or red

<!-- Speaker: Ask 2-3 participants which task was hardest to place and why. Reinforce: when in doubt, treat it as yellow, not green. Close with the three-question rule of thumb. -->

<!-- Notes:
This debrief cements the framework they will use for the rest of the session.
The three-question heuristic is intentionally simple — it should be easy to
remember after the course ends. Transition: "Now that you know where AI helps
most, let's put it to work on emails."
-->

---

## Email drafting — intent + recipient + tone

- Tell the model what you want to say, who you are writing to, and the tone you need — that is the minimum viable email prompt <!-- claim:llm_productivity:006 -->
- Tone-shifting is one of the most reliable things an LLM can do: name the target tone and it will adjust <!-- claim:llm_productivity:008 -->
- A bare "write me an email" gives you generic filler; adding context gives you a usable first draft <!-- claim:llm_productivity:006 -->

<!-- Speaker: Walk through the three ingredients live — intent, recipient, tone. Show a side-by-side: bare prompt vs. a prompt that names all three. Keep it quick; the exercise is where they practise. -->

<!-- Notes:
This slide sets up the email exercise. Emphasise that "who is this for?" and "what tone?" are the two additions that make the biggest difference. If participants ask about confidential emails, point back to the red-zone rule from chunk A: confidential content goes to the enterprise tool only.
-->

---

## Extract the ask, then reply

- With messy threads, first ask the model "What is actually being requested?" before you draft a reply — you get a more focused response <!-- claim:llm_productivity:007 -->
- Treat the AI draft as a starting point: review it, edit the facts and tone, rewrite at least one line in your own voice, then send <!-- claim:llm_productivity:009 -->

<!-- Speaker: Describe the two-step pattern — extract, then draft. Stress that jumping straight to "reply to this" often latches onto the wrong topic. Preview the exercise: they will try this on a real thread in a moment. -->

<!-- Notes:
The extract-then-reply pattern is the core takeaway of this block. In the debrief after Exercise 2, ask who skipped the extract step and went straight to drafting — and whether the reply addressed the right question. The "rewrite one line" step is there to keep their voice in the loop; mention it now so they know to do it during the exercise.
-->

---

## Exercise 2 · Reply to a messy thread

- **12 min** · Extract the real ask from a 5-message thread, draft a reply in a specified tone, then rewrite one line in your voice
- Tool: any general consumer chat LLM
- → Open your workbook: **Exercise 2**

<!-- exercise:E2 -->

<!-- Speaker: Remind them to read the model's one-sentence extract BEFORE looking at the draft reply — that is the whole point. Call time at 10 minutes and use the last 2 for a quick debrief: who got a different "real ask" on the first try? Tell them to save their extract-then-reply prompt — it goes into the prompt library later. -->

<!-- Notes:
Facilitation: give them 30 seconds to scan the thread before they start prompting. The most common stumbling point is skipping the extract step and asking the model to "just reply." In the debrief, surface 2-3 different one-sentence extracts — participants often disagree on the real ask, which is itself a useful insight. The full prompt, data, steps, and sample solution are in the workbook and solution key.
-->

---

## Change and preserve constraints

- Tell the model what to fix **and** what not to touch — explicit constraints narrow the output and reduce unwanted edits <!-- claim:llm_productivity:011 -->
- Pair "do" instructions with "don't" exclusions (e.g., "fix grammar; do not change numbers or technical terms") to keep critical details intact <!-- claim:llm_productivity:012 -->

<!-- Speaker: Walk through the idea with a quick example: "Imagine you paste rough meeting notes and ask the model to polish them — without a 'do not change the numbers' rule, it may round your budget figures or rename a product." Then preview Exercise 3. -->

<!-- Notes:
This is the setup slide for the bullets-to-memo exercise. Stress that constraints work in pairs: what to change plus what to preserve. Ask one or two participants what kind of detail they would never want an AI to silently alter — names, dates, and dollar amounts usually come up fast. Keep it brief; the exercise will make the point concrete.
-->

---

## Register shifting and few-shot templating

- Register means the way your language changes with the situation — a Slack message reads differently from a board memo <!-- claim:llm_productivity:013 -->
- Few-shot prompting — showing 2-5 examples in your prompt — lets the model pick up a pattern and apply it to new input without any training <!-- claim:llm_productivity:015 -->

<!-- Speaker: Give a 30-second live demo or verbal example: "If I show the model two of my own Slack updates, then paste a formal paragraph and say 'rewrite in this style,' it mirrors my voice instead of guessing." Bridge into Exercise 3, where they will use constraints and can optionally try a register shift in the stretch task. -->

<!-- Notes:
Register is not the same as tone — it covers vocabulary, sentence length, and formality level tied to the situation. Few-shot examples are the easiest way to steer register without writing a long style description. Mention the stretch task in Exercise 3 (shifting the memo to a casual Slack update) for participants who finish early. Keep this slide quick — the exercise is where the learning happens.
-->

---

## Exercise 3 · Bullets to memo

- **12 min** · Turn rough site-visit bullets into a one-page memo using a change/preserve constraint
- Tool: any general consumer chat LLM
- → Open your workbook: **Exercise 3**

<!-- exercise:E3 -->

<!-- Speaker: Before they start, remind the group of the key constraint: "fix grammar and clarity, do not change numbers or technical terms." Tell them to have the original bullets visible side-by-side so they can verify afterwards. Call time at 10 minutes and leave 2 minutes for a quick show-of-hands: who caught the model altering a number? -->

<!-- Notes:
Facilitation: hand out or display the bullet-point input so everyone starts from the same data. The most common stumbling point is accepting the memo without checking — several participants will find the model rounded a currency figure or dropped the product name. In the debrief, ask who found a changed number and what category it fell into (rounding, reformatting, or outright invention). This reinforces the constraint lesson from the concept slides.
-->

---

## From "summarise this" to extract-X-for-Y-in-Z

- A bare "summarise this" gives you a generic recap; specifying what to extract, who will read it, and what format you need improves results by 6-30% <!-- claim:llm_productivity:016 -->
- Tell the model the decision it should support: "summarise to help me decide whether to X" focuses the output on what actually matters <!-- claim:llm_productivity:020 -->
- Three levers you can set every time: **intent** (why you need this), **audience** (who reads it), **format** (bullets, table, one-liner) <!-- claim:llm_productivity:016 -->

<!-- Speaker: Walk through a before/after example on screen -- show a vague 'summarise this' output next to a decision-focused one so the contrast is visible before they try it themselves. -->

<!-- Notes:
This slide sets up Exercise 4. The core message is that summarisation quality jumps when you replace an open-ended request with a structured one. Ask the group: "When was the last time you asked an AI to 'just summarise' something -- and were the results actually useful?" Then preview the three levers (intent, audience, format) they will practise in the exercise.
-->

---

## Position bias and the shuffle check

- LLMs pay most attention to the start and end of long inputs -- when the key information sits in the middle, accuracy can drop by over 30% <!-- claim:llm_productivity:017 -->
- In multi-document summaries, whichever document comes first shapes the framing of the output <!-- claim:llm_productivity:018 -->
- Quick fix: shuffle the input order across two runs and compare -- differences reveal what the model missed the first time <!-- claim:llm_productivity:019 -->

<!-- Speaker: Mention that this is a well-documented blind spot, not a rare edge case. If anyone is summarising meeting notes or multiple reports, the order they paste them in matters more than they think. -->

<!-- Notes:
This is a brief awareness slide, not something they will exercise directly today. The point is to plant a practical habit: when a summary feels incomplete, reorder the inputs and re-run. In the debrief after Exercise 4, ask if anyone noticed differences when they changed the order of sections they pasted.
-->

---

## Exercise 4 -- Decision-focused summary

- **10 min** -- Run two prompts on the same office-move report: a bare "summarise this" and a decision-focused version, then compare side by side
- Tool: any general consumer chat LLM
- -> Open your workbook: **Exercise 4**

<!-- exercise:E4 -->

<!-- Speaker: Have them start a fresh chat for each prompt so the first answer does not leak into the second. Remind them to fill in the bracketed placeholders in Prompt B with their own wording -- that is where the learning happens. Call time at 8 minutes so there are 2 minutes for pair comparison. -->

<!-- Notes:
Facilitation: the most common stumbling point is leaving the [DECISION] placeholder vague ("decide about the report") instead of specific ("approve the office move this quarter"). If you see someone stuck, nudge them to name the actual decision. In the debrief, ask one or two people to share a concrete piece of information that appeared in Prompt B's output but was missing from Prompt A's -- this makes the value of structured prompting tangible.
-->

---

## Brain dump to plan

- About 40% of ChatGPT conversations are task-oriented — drafting, planning, organising — so planning is already one of the top reasons people reach for an LLM <!-- claim:llm_productivity:021 -->
- The brain-dump-to-plan pattern: paste your messy list of thoughts and ask the model to categorise, prioritise, and sequence them into an action plan <!-- claim:llm_productivity:022 -->
- LLMs are strong at restructuring text — turning chaos into structure is exactly where they shine

<!-- Speaker: Walk through the brain-dump pattern live: you have a jumble of tasks, you paste them in, you get a clean week plan back. Emphasise that this is a starting point, not a finished plan — they will see why in the next slide. -->

<!-- Notes:
This slide sets up the exercise by showing the high-value use case: unstructured thoughts turned into a prioritised plan. Keep it brief — the exercise will make the concept concrete. Mention that planning rivals coding in ChatGPT usage to validate the audience's interest.
-->

---

## The date arithmetic trap

- LLMs are unreliable at date and calendar maths — accuracy on basic date operations ranges from near-zero to perfect depending on the task <!-- claim:llm_productivity:023 -->
- Tokenisers chop dates into meaningless fragments (e.g. "20250312" becomes "202", "503", "12"), which can drop accuracy by up to 10 percentage points on unusual dates <!-- claim:llm_productivity:024 -->
- On a temporal reasoning benchmark, the best LLM still trailed human performance by over 25% on event-based time questions <!-- claim:llm_productivity:025 -->

<!-- Speaker: This is the 'trust but verify' slide. Tell participants: the plan you just saw looks great, but any date in it could be wrong. Ask them to guess which dates a model would get wrong — they will find out in the exercise. -->

<!-- Notes:
This slide exists to set up a healthy scepticism before the exercise. The key message: never trust a date in AI output without checking a real calendar. Keep the tone light — this is a known weakness, not a reason to avoid LLMs, just a reason to verify.
-->

---

## Exercise 5 · Week plan from a brain dump

- **12 min** · Turn a Sunday-evening brain dump into a prioritised week plan with effort estimates, then verify every date against a real calendar
- Tool: any general chat LLM
- → Open your workbook: **Exercise 5**

<!-- exercise:E5 -->

<!-- Speaker: Hand out the brain dump. Tell them: the brain dump has deliberate date traps — their job is to catch every wrong date the model produces. Remind them to open a real calendar app alongside the chat. Call time at 10 minutes and leave 2 minutes for a quick show of hands: who found at least one wrong date? -->

<!-- Notes:
Facilitation: the brain dump contains tricky references like "first Friday of June" and "second Monday of June" plus a 5-business-day countdown. Expect most models to get at least one date wrong. The most common stumbling point is trusting the model's day-of-week labels without checking. In the debrief, ask who found a wrong date and what category it fell into — this reinforces the verify-before-you-act habit.
-->

---

## Confidentiality and the data perimeter

- 11% of data employees paste into ChatGPT is confidential — source code, client data, internal documents <!-- claim:llm_productivity:026 -->
- Samsung banned employee use of ChatGPT after engineers pasted proprietary code, meeting notes, and chip-test data on three separate occasions within 20 days <!-- claim:llm_productivity:027 -->
- Rule of thumb: if it is confidential, use your company's enterprise AI tool — never a consumer chatbot

<!-- Speaker: Open with "raise your hand if you've ever pasted something into a chatbot and then thought 'wait, should I have done that?'" Then walk through the Samsung story as a concrete wake-up call. -->

<!-- Notes:
This slide sets the safety frame for everything that follows. Emphasise that the risk is not theoretical — real companies have had real leaks. The 11% stat lands well because participants can picture themselves copying and pasting without thinking. Transition by saying: "So the enterprise tool is for anything sensitive — but even then, you still need to check the output before you hit send."
-->

---

## Verify before you send

- AI text needs a human check: facts, names, numbers, links, and tone — the model can sound confident while getting details wrong <!-- claim:llm_productivity:028 -->
- LLMs default to a generic, middle-of-the-road voice; preserve yours by editing the final draft, not just skimming it <!-- claim:llm_productivity:029 -->
- A quick 5-item checklist before sending: facts, names, numbers, links, tone

<!-- Speaker: Walk through the five items one at a time, asking participants to recall an example from an earlier exercise where the model got one of these wrong (e.g., a date error in Exercise 5, or a number rounding in Exercise 3). -->

<!-- Notes:
This is the operational heart of the safety message. Connect each checklist item back to something participants already experienced: date errors in the week-plan exercise, number rounding in the memo exercise, tone mismatches in the email exercise. The point is that they already know how to catch these — now they have a reusable checklist. Keep it brisk; the next slide turns this into a habit.
-->

---

## Build your prompt library

- A personal prompt library — tested prompts organised by task — cuts setup time and keeps your outputs consistent <!-- claim:llm_productivity:030 -->
- You have already built four prompts today (email reply, memo, summary, week plan) — save them, label them, reuse them
- A good library entry: the prompt text, one line on what you learned, and a note on which checklist items to watch

<!-- Speaker: Show the simple table format — Task, Prompt, Notes — and tell them the next exercise is where they actually build it. -->

<!-- Notes:
This is the bridge to the capstone exercise. Frame it as: "You have done the hard work already — now you are packaging it so Monday-morning-you can grab a prompt and go." Mention that the best libraries grow over time: every time they write a prompt that works, they add a row.
-->

---

## Exercise 6 · Build your prompt library and verify an earlier output

- **10 min** · Assemble a starting prompt library from exercises 2–5; apply the 5-item verification checklist to one earlier output
- Tool: your own earlier work from this session
- → Open your workbook: **Exercise 6**

<!-- exercise:E6 -->

<!-- Speaker: Tell them this is the capstone — they leave with two things: a library they can use on Monday and a checklist habit. Remind them to use the fallback prompts in the workbook if they did not save their own. Call time at 10 minutes and ask two or three people to share one checklist finding. -->

<!-- Notes:
Facilitation: give them a minute to gather their earlier prompts before starting. The most common stumbling point is that people did not save their prompts from earlier exercises — point them to the fallback library in the workbook. In the debrief, ask: "What did the checklist catch that you would have missed?" and "Which prompt are you most likely to reuse next week?" This surfaces the practical value and closes the loop on the whole session.
-->

---

## Wrap-up — what you take away

- Six workflows you can use on Monday: task-fit sorting, email replies, document polishing, decision-focused summaries, brain-dump planning, and verification
- Your prompt library is yours to keep — add a row every time a new prompt works well
- The safety habits: enterprise tool for anything confidential, 5-item checklist before you send

<!-- Speaker: Do a quick lightning recap of the six blocks. Then ask: "Which workflow will you use first this week?" Take three or four answers. Close with: "Your prompt library and your checklist are the two things that make this stick beyond today." -->

<!-- Notes:
Keep this to two minutes. The goal is not to re-teach but to anchor the session in action: what will they do differently starting tomorrow? If time allows, invite one participant to share the stretch task they are most curious to try. End on an energetic note — they built something real today.
-->
