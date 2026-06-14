## Email drafting — intent + recipient + tone

- Give the model three things: what you want to say, who you are writing to, and the tone you want
- A bare "write me an email" gives you generic filler; adding context gives you a usable first draft <!-- claim:llm_productivity:006 -->
- LLMs can reliably shift tone — casual to formal, blunt to diplomatic — when the prompt names the target tone and audience

<!-- Speaker: Walk through the three-part prompt idea with a quick example — "email to my manager, declining a meeting, polite but firm." Then move straight into the exercise. -->

<!-- Notes:
This slide sets up the core email-drafting habit: front-load intent, recipient, and tone. Keep it brief — the hands-on work in Exercise 2 will make the pattern stick far better than further explanation. The tone-shifting point (claim:008) reassures learners that the model is genuinely good at this task so they feel confident trying it.
-->

---

## Extract the ask, then reply

- When facing a messy thread, ask the model first: "What is the one thing being requested here?" — then draft the reply <!-- claim:llm_productivity:007 -->
- Once the model has drafted a reply, review it and edit before you send <!-- claim:llm_productivity:009 -->

<!-- Speaker: Emphasise the two-step habit: extract, then draft. Stress that the review step is not optional — the model may misread who the reply is addressed to or invent a commitment you did not make. -->

<!-- Notes:
Decomposing before drafting is the key insight of this block. Learners often skip the extraction step and send a "reply to this thread" prompt, which produces replies to the most recent surface topic rather than the underlying request. The review-before-sending point (claim:009) reinforces human-in-the-loop habits and ties naturally into the verification theme that recurs throughout the session.
-->

---

## Exercise 2 · Reply to a messy thread

- **12 min** · Extract the real ask from a 5-message thread, draft a reply in a specified tone, then rewrite one line in your voice
- Tool: any general consumer chat LLM
- → Open your workbook: **Exercise 2**

<!-- exercise:E2 -->

<!-- Speaker: Ask participants to read the thread first before prompting — that primes them to judge whether the model's extraction is right. Remind them to save their extract-then-reply prompt for the prompt library later. Call time at 12 minutes and ask one person to share which line they rewrote and why. -->

<!-- Notes:
Facilitation: The most common stumbling point is skipping the extraction step and going straight to "reply to this thread" — the thread is deliberately messy so that shortcut produces a poor result. Watch for learners who accept the model's draft verbatim; in the debrief, ask whether their reply sounds like them. Surface the verification habit: did anyone catch a name swap or an invented commitment in the draft?
-->
