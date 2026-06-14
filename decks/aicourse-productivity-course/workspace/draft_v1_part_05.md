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
