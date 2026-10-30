---
name: write-long-term-memory
description: >-
  Use when a durable fact should be saved to this Markdown memory repository,
  including a user preference, standing rule, project fact, person fact, locked
  decision, or open loop. Draft one fact per file, confirm sensitive writes
  when needed, rebuild the index, and commit on the intended branch.
---

# Write long-term memory

Persist durable facts as one Markdown file per fact with YAML frontmatter. Keep the user's burden low: detect quietly, confirm rarely, and commit only after the fact is unambiguous.

## When to propose a write

| Trigger | Suggested type |
|---------|----------------|
| User says "remember", "save this", or "always do X" | As appropriate |
| User locks a decision | `decision` |
| Long-lived preference or rule that will not be superseded | `profile` |
| Dated call that a future entry may supersede | `decision` |
| Stable identity, role, project, or communication detail | `profile` / `person` / `project` |
| Unfinished item with a clear close condition | `open-loop` |
| User corrects a durable fact | Update the file or create a superseding record |

### `profile` or `decision`?

Ask: **could a later entry supersede this?**

- No: use `profile`.
- Yes: use `decision`, which has a date and a replacement history.

Do not duplicate the same rule in both types.

## Never write

- One-off instructions or temporary paths
- Guesses or unverified inferences
- Duplicates of another system of record unless the user wants a short pointer
- Secrets such as passwords, tokens, keys, or card numbers
- More personal data than the task requires

If unsure whether a fact is durable, ask once: "Save this to long-term memory?"

## Write workflow

### 1. Sync first

From the repository root:

```bash
sh scripts/memory-sync.sh
```

- `OK` / `SYNCED`: continue.
- `STALE` / `OFFLINE`: you may write, but the new fact may conflict with unseen data. Disclose the risk and clean or reconnect if possible.
- `AHEAD`: push the existing local commits before adding more.
- `DIVERGED`: stop and ask the user. A normal recovery may use `git pull --rebase origin main` once; abort on conflicts and show both sides.
- `SKIP`: treat the repository as local and say it is not a shared `main` clone.

### 2. Draft the record

Follow `SCHEMA.md`.

- Use a globally unique lowercase hyphenated ID.
- Make the filename equal the ID.
- Choose exactly one type matching the directory.
- Use `author: user` if the user dictated or wrote the fact; otherwise use your stable agent short name.
- Put the conclusion in the first non-heading paragraph.
- Keep one fact to roughly one screen.

### 3. Confirm when required

Show a short draft and wait for confirmation for:

- Standing rules
- Judgments about people
- External communication voice or policy
- Sensitive or ambiguous facts

Routine project facts and open loops may be saved directly when the user has already authorized that class of write.

### 4. Write and rebuild

Create or update the memory file. Do not edit `INDEX.md` or `moc/*.md` by hand.

If the pre-commit hook is enabled, it rebuilds the index during commit. Otherwise run:

```bash
python3 scripts/build_memory_index.py
```

### 5. Offer neighbours once

```bash
python3 scripts/build_memory_index.py --suggest-links <new-id>
```

If any candidates are genuinely related, ask one question: "Should I link these?" Add only confirmed IDs to `links:`.

Never bulk-backfill relations. A wrong edge is worse than no edge.

### 6. Commit

Stage the memory files before committing. The pre-commit hook intentionally rejects a commit when memory files are modified but unstaged, because the generated index is built from the worktree.

Use a focused commit message, for example:

```text
memory(decision): record sample app stack
```

Push to the repository's intended branch, normally `main`. Do not open a pull request for a routine memory write unless the repository owner requires it.

Tell the user one line identifying the saved ID and path.

## Conflicts

If a push is rejected because the branch moved:

1. Run `git pull --rebase origin main` once.
2. Resolve source-file conflicts by preserving each fact.
3. Regenerate generated files rather than hand-merging them.
4. Push once.

If a rebase conflicts in a way you cannot resolve safely, abort and show both sides to the user. Never force-push.

## Out of scope

Search and recall belong to the `recall-long-term-memory` skill.
