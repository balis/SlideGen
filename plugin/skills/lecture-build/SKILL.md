---
name: lecture-build
description: Write one lecture of a planned course as a PowerPoint deck on the author's template - an outline checked against the course plan and the author's slide count, native slides built and rendered, and every claim on new slides fact-checked against downloaded sources. Use after /slidegen:course-plan, once per lecture.
argument-hint: <plan.yaml> <lecture number> [--template deck.pptx]
allowed-tools: Read, Write, Bash(python3 *), WebSearch, WebFetch
---

# lecture-build

Turns lecture N of a course plan into a deck the author can teach from. The
plan says what the lecture covers and for how long. This skill decides the
slides, builds them on the author's master, checks them visually and checks
their facts.

## Setup

- `SG` = `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/sg.py`. On `"ok": false`, read
  `error`, fix the cause, and run the command again.
- `P` = the plan manifest (`plan.yaml`) given as the argument; `ROOT` = its
  directory; `N` = the lecture number; `L` = `ROOT/lectures/L<NN>/` (N with two
  digits). The lecture's files go to `L`, downloaded sources to
  `ROOT/lectures/sources/`.
- Inputs from the course plan: `ROOT/plan/proposal.json` (lecture N: summary,
  objectives, topics with hours and depth, `reuse`, `new_material` with
  minutes), `ROOT/plan/reference_curriculum.json` (topic descriptions), and,
  when `P` names `trends`, `profiles.md` in that folder (maturity, production
  use, limitations of current topics).
- `P` sets `lectures.slides`, the author's expected slide count, and may list
  `themes`: ideas that return in every lecture. The template is
  `--template`, or else the first deck in `P`'s `decks`.
- Agents: as in /slidegen:deck-modernize (plugin agent `slidegen:<name>`, or a
  general-purpose subagent with the body of the agent file and its model).

## Steps

1. **Outline.** Write `L/outline.json` (schema `lecture_outline`): one entry
   per slide with its title, topic, kind (`reuse` with deck and slide, or
   `new`) and a one-sentence `content`. Follow these rules:
   - **Size.** Use the whole slide range of `P`. Give each topic slides in
     proportion to its hours. Course organisation, dividers and the summary
     take `topic: null`.
   - **Depth.** For each topic this lecture owns, plan a concept slide, the
     mechanism, a worked example, the trade-off it makes, and an exercise
     where it fits.
   - **Previews.** A topic taught in another lecture gets one preview slide,
     marked `preview_of: <lecture>`. Do not teach it here.
   - **Reuse and themes.** Reuse the slides the plan lists. Bring in each
     theme of `P` where the lecture's content touches it, and close each part
     with a one-line takeaway.

   Run `SG lecture outline-check --plan P --lecture N` until it passes. Then
   show the author the outline as a table (number, title, kind, topic) and
   wait for approval.
2. **Specification and build.** Write `L/deck.json` (schema `deck_spec`) with
   `base` = the template. Write it from a generator script `L/make_spec.py`:
   start from `${CLAUDE_PLUGIN_ROOT}/references/deck_spec_example.py`, which
   has helpers for text, boxes, arrows and tables and one slide of each kind.
   - **Reused slides:** use `copy` with `edits` and `insert`.
   - **New slides:** a layout of the template with `bullets` or `shapes`:
     boxes, arrows, text and tables.
   - **Speaker notes:** every new slide gets notes that name its sources.
   - **Text size:** keep diagram text at 11 pt or more and bullets at 14 pt or
     more.
   - **Worked examples:** label assumed values on the slide ("Assumed: …"), so
     that the claim extractor lists them as assumptions instead of facts to
     research.

   Run `SG lecture outline-check --plan P --lecture N --spec L/deck.json`: the
   spec must have the outline's slides and copy template slides exactly where
   the outline reuses them. If a slide changed kind while you wrote it, update
   the outline. Then run `SG pptx build --spec L/deck.json`.
3. **Visual check.** `SG pptx render --pptx <deck> --out $TMPDIR/render-L<NN>`.
   LibreOffice writes a profile, so in a sandboxed session run this command
   outside the sandbox. Read every page image. Fix overflowing or overlapping
   text and empty areas, then rebuild.
4. **Fact check.**
   - Add the deck to `ROOT/lectures/course.yaml`: id `lecture<NN>`, path,
     minutes, `last_revised` = this year, `hidden_slides: skip`,
     `target_versions`.
   - Run steps 1–7 of phase A of /slidegen:deck-modernize for this deck only.
     Leave out the topic-mapper.
   - Give the claim-extractors `skip` = the slides whose outline entry has
     `checked: true`.
   - After `claims merge`, run `SG claims carry` with `--from` the workspaces
     of the decks this lecture reuses (their `workspace` in `P`) and of earlier
     lectures. Reused text verified there is not researched again.
   - Never drop claims by hand. Takeaway lines and stated judgements are the
     extractor's `framing` kind, and labelled example values are
     `assumption`.
5. **Fixes.**
   - CRITICAL and MAJOR verdicts: change the slide.
   - MINOR verdicts: change the line, or keep it and say why in the speaker
     notes, for example when it is the lecturer's framing.
   - Rebuild, render the changed slides again, and set `checked: true` on
     the slides whose claims were all VERIFIED and whose text did not change
     after the check, so that later rebuilds skip them. A slide with any
     other verdict stays unmarked, even after its fix, so that the next
     build checks it again.
6. **Report** to the author:
   - the deck path and its slide count per part;
   - the fact-check counts;
   - what was changed and what was kept, with reasons;
   - placeholders left for the author, such as course organisation.

## Cost

New slides carry about 5 claims each, and the fact check dominates the cost.
Measured on one course:
- **34 new or changed slides:** 167 claims, about 2.5M tokens for research and
  checking.
- **54 new slides:** 292 claims; the whole run, from specification to report,
  cost about $72 and took about 75 minutes.

Before the fact check, tell the author the number of claims and the expected
cost. Ways to lower it:
- Mark reused slides `checked` when their claims were verified in their own
  deck.
- Label worked-example assumptions (they are not researched).
- Use research batches of 10 claims, and give each fact-checker up to three
  batches.

Never lower the cost by changing an agent's model: the fact-checker runs on the
model its definition names. If the budget will not cover the fact check, stop
before it and tell the author what is left and what it would cost.
