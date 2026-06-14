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
