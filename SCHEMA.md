# Memory schema

One fact per Markdown file. YAML frontmatter is the source of truth. `INDEX.md` and `moc/*.md` are generated projections and must not be edited between their markers.

## Directories and types

| Directory | Required `type` | Purpose |
|-----------|-----------------|---------|
| `profile/` | `profile` | Stable identity, preferences, and standing rules |
| `people/` | `person` | People, roles, and relationships |
| `projects/<slug>/` | `project` | Facts about one project; `<slug>` is the project anchor |
| `decisions/` | `decision` | Dated decisions that may later be superseded |
| `journal/` | `journal` | Time-bound notes that may be archived |
| `open-loops/` | `open-loop` | Unfinished items with explicit close conditions |

The `type` must match the containing directory. A mismatch is a hard error.

### `profile` or `decision`?

Ask one question: **could a later fact supersede this?**

- No: use `profile` for long-lived identity, preferences, and standing rules.
- Yes: use `decision` so the change has a date and a history.

Do not record the same rule in both places.

## Frontmatter

```yaml
---
id: dec-2026-01-15-example-stack
type: decision
status: active
created: 2026-01-15
updated: 2026-01-15
author: user
tags: [example, architecture]
projects: [sample-app]
people: [person-example-maintainer]
links: [journal-2026-01-16-example-kickoff]
contradicts: []
supersedes: null
source: chat
recall_hint: "How should the sample app be built?"
confirm_required: true
---
```

Required fields:

- `id`
- `type`
- `status`
- `created`
- `author`

Recommended fields:

- `updated`
- `tags`
- `projects`
- `people`
- `links`
- `contradicts`
- `supersedes`
- `source`
- `recall_hint`
- `confirm_required`

### Field reference

| Field | Meaning |
|-------|---------|
| `id` | Globally unique lowercase identifier using letters, digits, and hyphens |
| `type` | One of `profile`, `person`, `project`, `decision`, `journal`, `open-loop` |
| `status` | `active`, `superseded`, or `archived` |
| `created` | Creation date in `YYYY-MM-DD` format |
| `updated` | Last meaningful update date in `YYYY-MM-DD` format |
| `author` | `user`, or the short name of the agent that recorded the fact |
| `tags` | Free-form retrieval tags |
| `projects` | Project directory slugs under `projects/` |
| `people` | IDs of existing `person` records |
| `links` | Related memory IDs; direction-free |
| `contradicts` | IDs of conflicting facts that have not been resolved |
| `supersedes` | ID of the fact replaced by this one |
| `source` | `chat`, `manual`, or `import` |
| `recall_hint` | A phrase the user might naturally use when recalling this fact |
| `confirm_required` | Whether a write should be confirmed in chat first |

Every fact should answer: **who recorded this?**

- Use `author: user` when the user dictates or writes the fact.
- Otherwise use the agent's short, stable name.
- Never use generic values such as `assistant` or `AI`.
- Never sign on behalf of another person or agent.

### File names

The filename must equal `<id>.md`.

```text
id: dec-2026-01-15-example-stack
path: decisions/dec-2026-01-15-example-stack.md
```

This lets Obsidian resolve `[[id]]` links and lets `rg` find a fact by ID.

Files whose names start with `_` or `.` are ignored by the indexer.

Content directories should contain memory files only. Put other notes in `journal/` or exclude them with an underscore-prefixed filename.

Arrays may use inline syntax:

```yaml
tags: [example, architecture]
```

or a block list:

```yaml
projects:
  - sample-app
```

Do not declare the same field twice.

## Anchors

`projects` and `people` are the primary axes used to retrieve a fact.

| Type | Anchor requirement | If missing |
|------|--------------------|------------|
| `decision` | At least one project or person | Listed in `moc/unfiled.md`; warning |
| `open-loop` | At least one project or person | Listed in `moc/unfiled.md`; warning |
| `journal` | Recommended, not required | Not listed as unfiled |
| `person` / `profile` | Exempt | — |
| `project` | Inferred from `projects/<slug>/` | — |

Missing anchors warn by default. `--strict` upgrades the warning to an error.

Do not invent an unrelated anchor just to silence the warning. A false edge is harder to clean than a missing one.

## Relations

Only three relation fields are supported:

| Field | Semantics | Example |
|-------|-----------|---------|
| `supersedes` | This fact replaces an older fact; mark the old fact `status: superseded` | A new pricing rule replaces an old one |
| `contradicts` | Two facts conflict and neither is resolved; keep both | "Prefers A" versus "Actually prefers B" |
| `links` | Contextually related; no direction | A decision derived from a project lesson |

Relation values are memory IDs, never paths.

A missing target ID is a hard error. A `supersedes` target that is still `active` produces a warning.

For an explicit Obsidian graph edge, add this to the body:

```markdown
Related: [[other-memory-id]]
```

The generator does not rewrite body content.

## Body conventions

- The first non-heading paragraph is the conclusion and becomes the index summary.
- Keep one fact within roughly one screen.
- Start the conclusion with `Conclusion:` if your team wants a visible convention.
- Add a `Do not infer` section when a nearby but incorrect inference would be harmful.
- Never include secrets.

## Generated files

`INDEX.md` and `moc/*.md` are generated. Only content between `<!-- moc:begin -->` and `<!-- moc:end -->` is replaced.

```bash
python3 scripts/build_memory_index.py
python3 scripts/build_memory_index.py --check
```

Generated outputs:

- `INDEX.md`: L0 entry point with recent decisions and counts
- `moc/standing-rules.md`: active profiles
- `moc/people.md`: active people, including related projects
- `moc/decisions.md`: active and superseded decisions
- `moc/open-loops.md`: active open loops
- `moc/journal.md`: active and superseded journal records
- `moc/unfiled.md`: active decisions/open loops with no anchors
- `moc/project-<slug>.md`: one aggregation page per project

Project aggregation pages collect the project file, decisions, open loops, journal notes, and related people. A page is generated when a project has at least one active fact.

If a project is deleted or fully archived, its generated page is removed only when the content outside the markers is byte-for-byte what the generator wrote. A hand-edited page is preserved and produces an error for human review.

`status: archived` records are omitted from indexes. Search them with `rg` when history is needed.

Files ignored by `.gitignore`, hidden files, and symbolic links are not indexed.

## Link suggestions

```bash
python3 scripts/build_memory_index.py --suggest-links <id>
```

This command is read-only. It scores candidates by:

- shared project anchor: weight 2
- shared tag: weight 1

Candidates must score at least 2. Archived records and project container files are excluded.

Relations are not added automatically. Show candidates to the user and add only confirmed IDs. A wrong edge is worse than no edge.

## Multi-host synchronization

Run this before reading or writing:

```bash
sh scripts/memory-sync.sh
```

It prints one status tag:

| Tag | Meaning |
|-----|---------|
| `OK` / `SYNCED` | Current and usable |
| `STALE` | Behind; uncommitted changes prevented fast-forward |
| `OFFLINE` | Remote could not be checked |
| `AHEAD` | Local has unpushed commits |
| `DIVERGED` | Local and remote both advanced |
| `SKIP` | Not on `main`, no `origin`, or not a Git repository |

The script never force-pushes, merges, rebases, or edits uncommitted files.

For `DIVERGED`, stop and ask the user. A normal write-flow recovery may use `git pull --rebase origin main` once, but do not force-push. If a rebase conflicts, abort it and show both sides to the user.

## Validation summary

Hard errors:

- Missing required fields
- Invalid or duplicate ID
- Filename not equal to ID
- Directory/type mismatch
- Invalid type, status, or date
- Dangling `links`, `contradicts`, or `supersedes` target
- Unknown project slug
- Marker count not exactly one pair
- Unsafe deletion of a generated project page

Warnings:

- Missing project/person anchor
- `people` entry is not a `person` record
- Invalid `source`
- `supersedes` target is still active
- Missing `updated`
- Markdown file directly under `projects/`
- Ignored or symbolic-link memory files

`--check` exits with code 2 when generated files are stale.
