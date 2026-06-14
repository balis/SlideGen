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
