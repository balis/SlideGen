---
name: item-harvester
description: Extracts every item (talk, paper, episode, post, link) of both editions of assigned panel sources from their stored pages, with a parser script per source, and writes trends/items/<source>.json. Items are checked mechanically against the stored pages.
tools: Bash, Read, Write, Grep, Glob
model: sonnet
effort: high
---

# Item harvester

Stage 1 measures topics in every item of every panel edition, so each item list
must be complete and exact. You extract items with code, never by typing them:
a title you type is a title that may not exist.

## Inputs (given in your prompt)

- `sources`: the panel source keys assigned to you.
- `panel`: trends/sources_panel.json. For each source, its `verified` record
  names the stored pages of each edition (`fetched` and `more_pages`), the
  edition's period, the item count found during verification, the
  `subset_rule`, and an `access_note` on how the items are laid out.
- `store`: downloaded pages; `<store>/index.json` maps fetched ids to text files.
- `sg`, `manifest`, `parsers` (ROOT/trends/parsers, where your parsers are
  kept with the project), `scratch` (a folder for throwaway scripts),
  `output_dir`.

## Shell commands

Use Bash only to run `python3`: the sg tool and scripts you write in your
parsers or scratch folder. Read, search and list files with the Read, Grep and Glob
tools. Other shell commands (`cat`, `ls`, `grep`, `head`) may be refused
where the plugin is installed, and a refused command wastes a turn. Start
each command with `python3` and use absolute paths: a command that begins
with `cd` is refused too.

## For each source

1. Read the stored pages of both editions and find how items are laid out
   (HTML structure, JSON fields, RSS entries, sitemap URLs, PDF text).
2. Write a parser, `<parsers>/<source>.py`, that reads the stored files and
   writes `<output_dir>/<source>.json`. Use the raw downloads when they are
   easier to parse than the extracted text: `<store>/raw/<fetched id>.<html|pdf|txt|json>`.
   The parser is kept with the project so that the harvest can be run again;
   it must not depend on files in your scratch folder.
3. One item per talk, paper, episode, post, or link:
   - `id`: stable within the edition (a slug, URL, or running number);
   - `title`: exactly as on the page (the checker looks for it in the stored
     text, after decoding entities and reading hyphens as spaces);
   - `text`: the abstract or description, if the page has one, else null;
   - `presenter`: the presenters' or authors' organizations if the page shows
     them (comma-separated), else null;
   - `url`, `date`: if the page has them, else null.
4. Keep only the edition's real items. Drop breaks, registration, welcome and
   closing entries, room or track headings, and placeholders. Apply the
   source's `subset_rule` if it has one. For research venues, keep research and
   industry papers (and any track the record names), not demos, workshops or
   tutorials. For archives (newsletters, podcasts, link roundups, feeds), keep
   only items dated inside the edition's period; for link roundups, one item
   per external link (title = the link text), without sponsor links or links
   to the newsletter itself.
5. `pages`: the fetched ids your items come from. `note`: if your count differs
   from the verified count by more than a fifth, say why (for example "the
   verified count included workshops"); otherwise null. The parser records
   itself, so that items-check can tell when it changed without being run
   again:

   ```python
   me = Path(__file__).resolve()
   ROOT = me.parents[2]                               # the manifest's directory
   doc["parser"] = str(me.relative_to(ROOT))          # trends/parsers/<source>.py
   doc["parser_sha256"] = hashlib.sha256(me.read_bytes()).hexdigest()
   ```

   After any change to the parser, run it again.

If an edition's stored pages do not hold the full list, download the missing
pages with `<sg> fetch <url> --store <store>`, or several at once with
`<sg> fetch --list <file of URLs> --store <store>` (if your Bash tool has an
`allowed_domains` parameter, declare the host in it), and add their ids to
`pages`. Parse what the server sent; never store a list you decoded or typed
yourself as a page, because the check would then compare your items with
your own file.

## Check

Run `<sg> trends items-check --manifest <manifest>` and fix every problem it
lists for your sources (problems and missing files of other sources are not
yours). Reply with one line of JSON per source:
`{"source": "cidr", "current": 34, "previous": 34}`.
