## Brain dump to plan

- About 40% of ChatGPT messages are task-oriented — drafting, planning, programming — so planning is already one of the top reasons people reach for an LLM <!-- claim:llm_productivity:021 -->
- Give the model an unstructured list of thoughts and ask it to categorise, prioritise, and sequence them into an action plan <!-- claim:llm_productivity:022 -->

<!-- Speaker: Ask who already uses an LLM for planning. The brain-dump pattern works because you offload the organisation step — you supply the raw material, the model supplies the structure. Lead into the exercise. -->

<!-- Notes:
This slide anchors the planning block by showing that planning is one of the most common real-world uses of ChatGPT, not just a niche trick. The brain-dump pattern is concrete and immediately actionable. Keep it brief — the exercise is where they actually feel the benefit. 2-3 sentences of framing is enough.
-->

---

## The date arithmetic trap

- LLMs are unreliable at date and calendar arithmetic: accuracy on basic temporal operations ranges from near-zero to perfect depending on the model and prompting approach <!-- claim:llm_productivity:023 -->
- Tokenizers fragment calendar dates into meaningless pieces — a root cause of errors that can drop accuracy by up to 10 percentage points <!-- claim:llm_productivity:024 -->
- Even GPT-4 shows a significant gap versus humans on temporal reasoning tasks <!-- claim:llm_productivity:025 -->

<!-- Speaker: This is the key safety point before the exercise. LLMs look confident when they get dates wrong — the model won't flag uncertainty. Emphasise: always open a real calendar and check every date in a generated plan. -->

<!-- Notes:
Learners often trust AI-generated plans completely, including dates. This slide prepares them to catch errors in the exercise, where the brain dump contains several date traps. The point is practical: the tool is helpful for structure, but dates must always be verified against a real calendar. Keep the tone matter-of-fact, not alarming.
-->

---

## Exercise 5 · Week plan from a brain dump

- **12 min** · Turn a Sunday-evening brain dump into a prioritised week plan, then verify every date against a real calendar
- Tool: any general consumer chat LLM
- → Open your workbook: **Exercise 5**

<!-- exercise:E5 -->

<!-- Speaker: Tell them to paste the brain dump as-is — no editing. Their job after the model responds is to open a real calendar and check every date and day-of-week pair. Expect at least one wrong date; catching it is the point. Call time at 12 minutes and ask who found an error. -->

<!-- Notes:
Facilitation: the brain dump contains several deliberate date traps (first Friday of June, second Monday of June, 5-business-day back-count, a same-day expense deadline). Most learners will find at least one error. The debrief should surface what the model got wrong and why — link back to the tokenisation slide. The main stumbling point is learners who trust the model's dates without opening a calendar.
-->
