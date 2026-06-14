# Outline: Practical Productivity with LLMs

## Slide 1: Title slide
- type: TITLE
- content: Practical Productivity with LLMs — Emails, Documents, Summaries, Planning; Practical AI for Professionals · Session 2

## Slide 2: How this session works
- type: AGENDA
- content: Six concept-then-exercise loops; you work from the workbook, not these slides; exercises use your own chat LLM (enterprise tool for anything confidential); at the end you leave with a personal prompt library

<!-- chunk-boundary: A | Task-fit: green / yellow / red zones -->
## Slide 3: What LLMs do well (green zone)
- type: CONTENT
- claims: [claim:llm_productivity:001]
- speaker_notes_hint: Anchor with everyday examples — drafting, restructuring, summarising, tone-shifting

## Slide 4: What needs scaffolding (yellow zone)
- type: CONTENT
- claims: [claim:llm_productivity:002, claim:llm_productivity:003]
- speaker_notes_hint: Arithmetic inside word problems degrades; citations are fabricated at high rates — always verify

## Slide 5: What to keep out (red zone)
- type: CONTENT
- claims: [claim:llm_productivity:004, claim:llm_productivity:005]
- speaker_notes_hint: Final-authority decisions stay human; confidential data never goes into consumer tools — Samsung incident

## Slide 6: Exercise 1 · Sort the task list
- type: EXERCISE
- exercise: E1
- scenario: Sort 10 office tasks into green / yellow / red zones and justify two choices
- minutes: 8
- tool: any general consumer chat LLM
- workbook_ref: "workbook — Exercise 1"
- speaker_notes_hint: Hand out the 10-task list; watch for tasks that sit on a boundary — surface those in the debrief

## Slide 7: Debrief — your task-fit rule of thumb
- type: CONTENT
- claims: []
- speaker_notes_hint: Ask 2-3 participants which task was hardest to place; reinforce: when in doubt, it is yellow, not green

<!-- chunk-boundary: B | Email workflows -->
## Slide 8: Email drafting — intent + recipient + tone
- type: CONTENT
- claims: [claim:llm_productivity:006, claim:llm_productivity:008]
- speaker_notes_hint: One-line intent plus who you are writing to plus the tone you want — that is the minimum viable email prompt

## Slide 9: Extract the ask, then reply
- type: CONTENT
- claims: [claim:llm_productivity:007, claim:llm_productivity:009]
- speaker_notes_hint: Decompose before drafting — first ask the model what the thread is really requesting, then draft a reply to that

## Slide 10: Exercise 2 · Reply to a messy thread
- type: EXERCISE
- exercise: E2
- scenario: Extract the real ask from a 5-message thread, draft a reply in a specified tone, then rewrite one line in your voice
- minutes: 12
- tool: any general consumer chat LLM
- workbook_ref: "workbook — Exercise 2"
- speaker_notes_hint: Remind them to save their extract-then-reply prompt — it goes into the prompt library later

<!-- chunk-boundary: C | Document workflows -->
## Slide 11: Change / preserve constraints
- type: CONTENT
- claims: [claim:llm_productivity:011, claim:llm_productivity:012]
- speaker_notes_hint: Tell the model what to fix AND what not to touch — explicit constraints reduce unwanted edits

## Slide 12: Register shifting and few-shot templating
- type: CONTENT
- claims: [claim:llm_productivity:013, claim:llm_productivity:015]
- speaker_notes_hint: Register = situational language variation; few-shot = show 2-3 examples and the model infers the pattern

## Slide 13: Exercise 3 · Bullets to memo
- type: EXERCISE
- exercise: E3
- scenario: Turn rough bullets into a one-page memo using a change/preserve constraint
- minutes: 12
- tool: any general consumer chat LLM
- workbook_ref: "workbook — Exercise 3"
- speaker_notes_hint: Emphasise the constraint: fix grammar and clarity, do not change numbers or technical terms

<!-- chunk-boundary: D | Summarisation workflows -->
## Slide 14: From "summarise this" to extract-X-for-Y-in-Z
- type: CONTENT
- claims: [claim:llm_productivity:016, claim:llm_productivity:020]
- speaker_notes_hint: Structured prompts improve results 6-30% over bare summarise; specifying intent, audience, and format is the key

## Slide 15: Position bias and the shuffle check
- type: CONTENT
- claims: [claim:llm_productivity:017, claim:llm_productivity:018, claim:llm_productivity:019]
- speaker_notes_hint: LLMs over-weight the first and last documents; shuffling input order across runs reveals what the model missed

## Slide 16: Exercise 4 · Decision-focused summary
- type: EXERCISE
- exercise: E4
- scenario: Write a decision-focused summary prompt and compare it to a bare "summarise this"
- minutes: 10
- tool: any general consumer chat LLM
- workbook_ref: "workbook — Exercise 4"
- speaker_notes_hint: Have them run both prompts on the same report so the difference is visible

<!-- chunk-boundary: E | Planning workflows -->
## Slide 17: Brain dump to plan
- type: CONTENT
- claims: [claim:llm_productivity:021, claim:llm_productivity:022]
- speaker_notes_hint: 40% of ChatGPT use is task-oriented; the brain-dump-to-plan pattern is a high-value starting point

## Slide 18: The date arithmetic trap
- type: CONTENT
- claims: [claim:llm_productivity:023, claim:llm_productivity:024, claim:llm_productivity:025]
- speaker_notes_hint: LLMs are unreliable at date math — tokenizers fragment dates; always verify dates against a real calendar

## Slide 19: Exercise 5 · Week plan from a brain dump
- type: EXERCISE
- exercise: E5
- scenario: Turn a weekend brain dump into a prioritised week plan with effort estimates, then verify every date
- minutes: 12
- tool: any general consumer chat LLM
- workbook_ref: "workbook — Exercise 5"
- speaker_notes_hint: The date-checking step is the point — expect at least one wrong date

<!-- chunk-boundary: F | Sustainable habits -->
## Slide 20: Confidentiality and the data perimeter
- type: CONTENT
- claims: [claim:llm_productivity:026, claim:llm_productivity:027]
- speaker_notes_hint: 11% of pasted data is confidential; Samsung incident — rule: confidential data goes to the enterprise tool only

## Slide 21: Verify before you send
- type: CONTENT
- claims: [claim:llm_productivity:028, claim:llm_productivity:029]
- speaker_notes_hint: The 5-item checklist: facts, names, numbers, links, tone — and preserve your voice by editing the final line

## Slide 22: Build your prompt library
- type: CONTENT
- claims: [claim:llm_productivity:030]
- speaker_notes_hint: A personal prompt library turns one-off wins into a durable workflow

## Slide 23: Exercise 6 · Prompt library and verification
- type: EXERCISE
- exercise: E6
- scenario: Assemble a starting prompt library from exercises 2-5; apply the 5-item verification checklist to one earlier output
- minutes: 10
- tool: participant's own earlier work
- workbook_ref: "workbook — Exercise 6"
- speaker_notes_hint: This is the capstone — they leave with a usable artifact

## Slide 24: Wrap-up — what you take away
- type: CONTENT
- claims: []
- speaker_notes_hint: Recap the six workflows; remind them the prompt library is theirs to keep and grow
