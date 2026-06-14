## Email drafting — intent + recipient + tone

- Give the model three things: what you want to say, who you are writing to, and the tone you want <!-- claim:llm_productivity:006 -->
- Tone-shifting is a common LLM use case: name the target tone and audience and the model will adjust the draft accordingly
- One-line intent + recipient role + tone word = a minimum viable email prompt

<!-- Speaker: Ask: "How long does it take you to draft a tricky email today?" Then show how the three-part formula cuts that down. Lead straight into the exercise. -->

<!-- Notes:
This slide sets up the first email exercise. The point is not that LLMs write perfect emails, but that giving three explicit inputs (intent, recipient, tone) produces a much more usable first draft than a bare "write me an email." Keep it brief — the exercise is where the learning happens.
-->

---

## Extract the ask, then reply

- When a thread is messy, ask the model to name the one thing being requested before drafting anything <!-- claim:llm_productivity:007 -->
- Once the model has drafted a reply, review it, check the facts and tone, then edit before you send <!-- claim:llm_productivity:009 -->
- Decompose first, then draft — it produces more focused, accurate replies than one-shot "reply to this"

<!-- Speaker: Emphasise the two-step rhythm: extract, then draft. Point out that skipping the extract step is the most common mistake — the model latches onto the surface topic, not the real ask. -->

<!-- Notes:
This slide pairs directly with Exercise 2. The extract-then-reply pattern is the main takeaway for the email block. Remind participants to save the prompt they build here — it goes into their prompt library in the final exercise.
-->

---

## Exercise 2 · Reply to a messy thread

- **12 min** · A colleague's 5-message thread has drifted across topics — find the real ask, draft a reply in a specified tone
- Tool: any general consumer chat LLM
- → Open your workbook: **Exercise 2**

<!-- exercise:E2 -->

<!-- Speaker: Tell participants to read the extracted one-sentence ask before they look at the draft reply. If the ask is wrong, the whole reply is wrong — that's the lesson. Call time at 12 min and ask one person to share which ask the model identified. -->

<!-- Notes:
Facilitation: the most common stumbling point is skipping the extract step and asking the model to "just reply" — surface this in the debrief. Watch for participants who accept a draft that addresses the wrong topic. Debrief question: "Did the model find the real ask on the first try, or did you have to correct it?" The full prompt, thread, steps, and sample solution are in the workbook.
-->
