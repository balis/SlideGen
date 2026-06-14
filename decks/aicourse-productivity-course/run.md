# Course Brief

**Topic:** Practical Productivity with LLMs — Emails, Documents, Summaries, Planning
**Course:** Practical AI for Professionals (Session 2, hands-on)
**Audience:** non-IT professionals; basic computer literacy, no coding background
**Prerequisites:** Session 1 (structured prompting — audience/format/constraints,
zero- vs few-shot, common failure modes: hallucination, weak arithmetic, stale
knowledge).
**Duration:** 90 minutes, hands-on (expect ~50% of time spent in exercises)
**Target tools:** a general consumer chat LLM (whatever each participant has access
to); where a task touches confidential data, the employer-approved/enterprise
assistant instead. No installs, no API keys, no coding.

**Session plan** — each concept block is short and is followed by an exercise the
participant completes in the workbook. Keep concept slides lean (2–4 bullets); the
depth lives in the exercise + workbook.

1. **Task-fit: green / yellow / red zones.** Which work LLMs do well (drafting,
   restructuring, summarising, tone-shifting), which need scaffolding (arithmetic,
   citations, live data), which to keep out (final-authority decisions, confidential
   data in consumer tools).
   - Exercise: sort a provided list of 10 real office tasks into the three zones and
     justify two of them. Input: the 10-task list (provided). 8 min. Keeps: a
     personal rule of thumb for "should I bring this to AI?".

2. **Email workflows.** Drafting from a one-line intent + recipient profile; the
   extract-the-ask-then-reply pattern for messy threads; tone shifting; the
   edit-don't-send hybrid loop.
   - Exercise: given a provided 5-message thread, first prompt the model for the
     one-sentence real ask, then draft a reply in a specified tone, then rewrite one
     line in your own voice. Input: the sample thread (provided). 12 min. Keeps: a
     reusable "extract then reply" prompt.

3. **Document workflows.** Rough bullets → drafted memo with explicit
   change/preserve constraints; register shifting (technical → plain); turning a good
   example into a reusable template via few-shot.
   - Exercise: turn a provided set of rough bullets into a one-page memo using a
     change/preserve constraint ("fix grammar and clarity; do not change numbers or
     technical terms"). Input: the rough bullets (provided). 12 min. Keeps: a
     fill-in memo prompt template.

4. **Summarisation workflows.** Replace "summarise this" with "extract X for
   audience Y in format Z"; decision-focused summaries; multi-document
   agree/disagree/silent synthesis with the shuffle check.
   - Exercise: given a provided 2-page report, write a decision-focused summary
     prompt ("summarise to help me decide whether to ___") and compare it to a bare
     "summarise this". Input: the report (provided). 10 min. Keeps: the
     extract-X-for-Y-in-Z formula.

5. **Planning workflows.** Brain dump → prioritised plan with effort estimates;
   meeting agendas and project briefs; the date/calendar arithmetic trap.
   - Exercise: turn a provided weekend brain dump into a prioritised week plan with
     effort estimates and a daily order — then verify every date against a real
     calendar. Input: the brain dump (provided). 12 min. Keeps: a brain-dump-to-plan
     prompt + the "always check dates" habit.

6. **Sustainable habits.** Confidentiality and data perimeter; the pre-send
   verification checklist (facts, names, numbers, links, tone); preserving your
   voice; building a personal prompt library.
   - Exercise: take the prompts you saved in exercises 2–5 and assemble your starting
     prompt library (Task | Prompt | Notes); apply the 5-item verification checklist
     to one output you generated earlier. Input: the participant's own earlier work.
     10 min. Keeps: a personal prompt library page + the verification checklist.

**Source recency policy** (governs concept facts shown on slides; exercises are
validated separately by running them):

1. Time-sensitive claims (specific AI products, pricing, model names, feature
   availability, benchmarks, adoption numbers): source from the last 3 months; if the
   freshest source is older than 6 months, flag as potentially stale or omit.
2. Slowly evolving guidance (prompt patterns, "how to use X effectively"): prefer the
   last 6–12 months; note on the slide that this is a fast-moving field if older than
   6 months.
3. Conceptual foundations (how LLMs work, why outputs vary, why hallucinations
   happen): recency does not apply.
4. Pricing, model versions, direct competitive comparisons: verify within 30 days of
   delivery; date-stamp on the slide.
5. Product-specific capability claims: check official docs/changelog from the last 60
   days; do not rely on older third-party comparisons.
6. When in doubt, omit rather than approximate.
7. For every factual claim on a slide, the source and its publication date must be
   nameable on request, or the claim does not belong on the slide.
