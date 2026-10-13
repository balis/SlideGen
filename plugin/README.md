# slidegen plugin

Claude Code skills for lecture decks whose claims are checked against downloaded
sources. The design is in `docs/design/slidegen-plugin.md` of the repository
that contains this plugin.

| Skill | Status |
|---|---|
| `field-trends` | for any field: drafts the field's manifest, selects and verifies sources, measures attention per topic, and writes topic profiles (maturity, production use, limitations) |
| `course-plan` | reference curriculum, field trends per course topic, gap analysis, lecture plan, decisions checklist |
| `deck-modernize` | report phase: claim check, developments survey, change plan, report, checklist, annotated PPTX |
| `lecture-build` | one lecture of a planned course: an outline checked against the plan and the author's slide count, native slides on the author's template (`sg pptx build`), a rendered visual check (`sg pptx render`), and the claim check of deck-modernize |
| `deck-create`, `deck-review`, `deck-export` | not yet ported (deck-create: a deck from a topic description, without a course plan); use the pipelines in the repository root |

## Install

The repository root holds a marketplace with this one plugin. Add it once, then
install the plugin:

```bash
claude plugin marketplace add /path/to/slide-agent
claude plugin install slidegen@slidegen-marketplace
```

The plugin is read from this folder in place, so local edits take effect at the
next session start, or after `/reload-plugins` in a running session. To try it
without installing, start a session with `claude --plugin-dir /path/to/slide-agent/plugin`.

## Use

Each skill takes a manifest as its argument and works in any directory:

```text
/slidegen:field-trends    trends.yaml          what is current in a field
/slidegen:course-plan     plan.yaml            a lecture plan for a course
/slidegen:lecture-build   plan.yaml 3          one lecture of the plan as a PPTX deck
/slidegen:deck-modernize  course.yaml          what to change in existing decks
```

Example manifests are in `references/examples/`:
- `trends.yaml` names a field, its time windows, source families and anchors.
- `plan.yaml` describes a course: level, lectures and their length, expected
  slides per lecture, existing decks, recurring themes.
- `course.yaml` lists existing decks and what the author knows about them.

The examples come from the course the plugin was developed with, so their file
paths point into that repository. `field-trends` can also draft a trends manifest
for a new field from a short course brief. `references/deck_spec_example.py`
shows how `lecture-build` writes a deck specification.

## Requirements

- Python 3.10+ with the packages in `requirements.txt`, installed in a virtual
  environment whose `python3` comes first on PATH when Claude Code starts, since
  the skills and agents run bare `python3`:

  ```bash
  python3 -m venv .venv && .venv/bin/pip install -r plugin/requirements.txt
  ```

  A project's `.claude/settings.json` can put the environment on PATH with
  `"env": {"PATH": "<venv>/bin:..."}`; the value replaces PATH, so list the
  system directories too.
- LibreOffice (`soffice`) for `sg pptx render`, which `lecture-build` uses to
  look at every slide. LibreOffice cannot open its IPC pipe inside the Linux
  sandbox; see "Permissions and network" for running the render command
  outside it.
- `inkscape`, for vector EMF/WMF images that contain no bitmap. Without it,
  `sg ingest` reports those images as failed and returns `"ok": false`.
- The deck's fonts, or metric-compatible substitutes, for renders whose line
  breaks match PowerPoint. On Debian and Ubuntu, `fonts-crosextra-carlito`
  replaces Calibri and `fonts-crosextra-caladea` replaces Cambria.

## Permissions and network

Plugins cannot ship permission rules. The skill pre-approves `python3` commands
for its own turn through `allowed-tools`; subagents may still need these rules in
the project's `.claude/settings.json`:

```json
{"permissions": {"allow": ["Bash(python3 *)", "WebSearch", "WebFetch"]}}
```

`sg fetch` downloads sources through Bash, so in a sandboxed session the source
hosts must be reachable from Bash: either allow them in the sandbox network
settings, or approve each host when asked. A headless `claude -p` run denies any
call that is not allowed and continues, so set these rules before batch runs.
Where the sandbox proxy re-signs TLS, `requests` trusts the proxy through the
environment, but yt-dlp needs `--compat-options no-certifi` to do the same.

In a sandboxed session, list the render command in the project's
`sandbox.excludedCommands`, with the absolute path of `sg.py`, so that it runs
outside the sandbox. This works even where `allowUnsandboxedCommands` is
false; the command must then be called exactly in that form, without `cd`,
pipes or redirects:

```json
{"sandbox": {"excludedCommands": ["python3 /abs/path/to/plugin/scripts/sg.py pptx render *"]}}
```

## The sg tool

`scripts/sg.py` does every step that has one correct answer; run it with `--help`
for the commands. Tests: `python3 -m pytest plugin/tests`.
