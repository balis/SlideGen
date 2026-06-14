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
