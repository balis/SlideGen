# PowerPoint conversion prompt (copy/paste)

Paste everything below the dividing line into the PowerPoint chat agent.
Attach the deck's Marp markdown file (typically `output/slides.md`, but the
filename can be anything). Optionally also attach the sources manifest
(`output/provenance.json`) — if provided, the agent adds a References
appendix slide.

---

Attached:
- A **Marp markdown deck** (required) — a finalized, fact-checked lecture deck in Marp format. The filename may be anything (e.g. `slides.md`, `lecture-04.md`); identify it by content (Marp frontmatter at the top: `marp: true`).
- A **sources manifest JSON** (optional) — typically named `provenance.json`, with a `claims[]` array where each entry has `id`, `source_title`, and `source_url`. If attached, it drives the References appendix; if absent, skip the References slide entirely.

Convert the Marp deck to PowerPoint. Preserve slide order and content exactly; your job is to render, not redesign.

## Visual style

Default to a style suited to academic lecture delivery: clean and information-dense without feeling crowded. Sans-serif type, generous whitespace, and structured layouts (card grids, flow diagrams, comparison tables) give each idea visual shape. Use color **deliberately as a semantic encoding** — categories, comparison poles, or pipeline stages each carry a consistent accent color — rather than as decoration. Conventions that work well at this level:

- Card-based layouts (rounded rectangles with colored left bars or header strips) to group related bullets
- Pipeline/flow steps as connected colored boxes; comparisons as tables with colored headers
- Big numeric callouts for statistics (percentages, multipliers, thresholds)
- A short italicized takeaway line at the bottom of most slides
- Small thematic icons in slide corners are fine if they're functional, not ornamental

Avoid stock photography, decorative gradients, drop shadows beyond what the template provides, and transition animations. Polish comes from clarity and disciplined structure, not visual flourish.

If reference slides are attached (images, screenshots, or a sample deck from another lecture), use them as the style guide — match their typography, color palette, layout density, and overall feel — instead of the default.

## Per-slide transformations

- **Title slide (leading `# H1 Title`)** — use the title-slide layout. The H1 is the title, the bold line below is the subtitle, the plain line after that is a context/affiliation line.
- **Other slide titles (`## Slide N: Title`)** — strip the `Slide N:` prefix; the PowerPoint title is only what follows the colon.
- **Bullets, code, tables, prose** — preserve verbatim. **Strip `[claim:...]` traceability tags** from the end of each bullet (along with any whitespace they leave). If `provenance.json` is attached, record the unique claim IDs you strip — they drive the References appendix below.
- **Mermaid diagrams (` ```mermaid ` fences)** — render as images and place them appropriately given the rest of the slide's content (a diagram-only slide can fill the body; a slide that mixes a diagram with bullets or code needs to balance them). If a diagram cannot be rendered, substitute `[Diagram: {first non-empty source line}]` text and continue.
- **`<!-- Speaker: ... -->` and `<!-- Notes: ... -->` HTML comments** — never display on the visible slide. Move both into the speaker-notes pane, formatted as:

      [Speaker]
      {Speaker comment contents}

      [Lecturer notes]
      {Notes comment contents}

A slide may combine several of these elements (bullets + diagram, table + caption, etc.). Pick a PowerPoint layout that fits each slide's actual content — don't force every slide into the same template.

## References appendix (only if `provenance.json` is attached)

If `provenance.json` is attached, add one slide titled **References** as the last slide. Build it by looking up each stripped claim ID in `provenance.json.claims[]`, deduplicating the resulting sources by `source_url`, sorting alphabetically by `source_title`, and rendering each as a single bullet:

    {source_title}. {source_url}

If references won't fit comfortably, paginate as "References (1/2)", "References (2/2)" — don't shrink the type to force-fit.

If `provenance.json` is not attached, skip this section entirely — do not add a References slide.

## Don'ts

- No transitional, motivational, or "Thank you / Questions?" slides not in the source.
- No commentary or summary content of your own.
- Bullet wording is fixed — only the trailing `[claim:...]` tag is removed.

Let me know if anything in the source was ambiguous or could not be rendered.
