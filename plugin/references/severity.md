# Severity rubric

One rubric for every checker. Severity decides what blocks: CRITICAL and MAJOR
issues must be addressed by the change plan; MINOR issues are advisory. When torn
between two levels, choose the lower one.

## MISREPRESENTED (a source exists, but the slide distorts it)

- **CRITICAL**: the source contradicts the slide, or the slide states a wrong
  number, name, or date.
- **MAJOR**: a dropped or added qualifier changes meaning, scope, or strength
  ("always" for "often", "the only way" for "one way"), or the slide states a
  figure the source never gives.
- **MINOR**: precision that does not change the takeaway: a narrower scope, a
  product variant name, wording supported in substance but not verbatim.

## UNVERIFIED (no usable evidence)

- **MAJOR**: a specific number, attribution, or comparison that no source
  supports after a real search.
- **MINOR**: a general statement that is plausible but has no source.

## OUTDATED (true once, not true now)

OUTDATED needs two dated sources: one that supported the claim, and a later one
that shows the state changed. A current page that does not mention the old
behaviour is not evidence of change.

- **CRITICAL**: the claim is now false and would mislead, e.g. "Trino has no
  fault tolerance" after fault-tolerant execution shipped.
- **MAJOR**: still literally true, but a significant change makes the slide
  misleading by omission, e.g. statistics described only per row group after
  the format added a page index that engines use.
- **MINOR**: figures, defaults, or versions drifted without changing the point.

If the change concerns a version newer than the course's `target_versions`, the
severity is at most MINOR, and `beyond_target_versions` is true.

Label each OUTDATED verdict:
- `changed-since`: the change came after the deck's content date.
- `stale-when-written`: the change came before it; the slide was already out of
  date.

## fix_kind

- `line-edit`: a corrected sentence fixes the bullet.
- `new-content`: the slide needs new material (a new mechanism, a new system, a
  restructured comparison).
