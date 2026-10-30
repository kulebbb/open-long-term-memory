---
name: recall-long-term-memory
description: >-
  Use when the user asks to recall a preference, person, project, decision, or
  prior context, or when a task needs durable facts from this Markdown memory
  repository. Search progressively and never paste the whole repository into
  context.
---

# Recall long-term memory

This repository stores durable facts as Markdown files, one fact per file. Never load the entire tree "just in case".

## When to use

Use this skill when:

- The user asks what they decided, prefer, or said before.
- The task depends on a person, project, standing rule, or past decision that is not already in context.
- Two sources may conflict and you need dated evidence.

Do not use it for one-off steps that require no durable history.

## Repository location

Use the configured memory repository clone. If the path is unknown, ask once. The root normally contains:

- `INDEX.md`
- `moc/`
- `profile/`
- `people/`
- `projects/`
- `decisions/`
- `journal/`
- `open-loops/`
- `SCHEMA.md`

## Sync before trusting the clone

From the repository root, run once per recall:

```bash
sh scripts/memory-sync.sh
```

| Tag | Action |
|-----|--------|
| `OK` / `SYNCED` | Continue |
| `STALE` | Continue, but disclose that the clone may be behind |
| `OFFLINE` | Continue with local data, and disclose that the remote was not checked |
| `AHEAD` | Continue using local data, and mention unpushed commits |
| `DIVERGED` | Stop and ask the user; do not choose a side or rebase automatically |
| `SKIP` | Continue as a local copy and disclose that it is not a synced `main` clone |

The script only fast-forwards. It does not merge, rebase, or modify uncommitted files.

## Progressive disclosure

### L0: navigation

Read only:

1. `INDEX.md`.
2. The smallest relevant `moc/*.md`.

For a known project, read `moc/project-<slug>.md` first. It already aggregates project facts, decisions, open loops, journal notes, and related people.

Use the per-type MOCs only when the topic is not project-shaped:

- `moc/decisions.md`
- `moc/open-loops.md`
- `moc/people.md`
- `moc/unfiled.md`

### L1: candidate screening

For candidate files, read frontmatter plus the title and first paragraph. Prefer `status: active`. Skip `superseded` and `archived` unless history is requested.

Use `projects`, `people`, `links`, `contradicts`, and `supersedes` to judge relevance before opening the full body.

### L2: evidence

Read the complete body only for the one to three clearest records. If more may apply, list their titles and ask the user which to expand.

Never bulk-read a whole content directory.

## Search order

1. Match `recall_hint`, file name, title, project slug, person ID, and tags with `rg`.
2. Prefer exact slugs or IDs when known.
3. If nothing solid matches, say that no durable memory was found. Do not invent a fact.

## Reporting results

- State the recalled fact briefly and include its path or ID.
- If sync was not clean, include the revision basis, such as `main@<sha>`, plus the relevant freshness warning.
- Mention `author` when source trust matters.
- Follow declared `supersedes`, `contradicts`, and `links` relations and report the chain.
- If active records conflict without a declared relation, prefer the newer `updated` or `created` value and disclose the conflict.
- Never reproduce a secret if one appears. Warn the user and avoid repeating the value.

## Out of scope

Writing or editing memory belongs to the `write-long-term-memory` skill.
