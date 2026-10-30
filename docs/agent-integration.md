# Agent integration

The repository is designed to be usable from Codex, Claude, and other agents that can read local files and run shell commands.

## Minimal integration

Add a pointer to the agent's global or project instructions:

```text
Long-term memory:
- Before recalling durable facts, read <clone>/skills/recall-long-term-memory/SKILL.md.
- Before saving a durable fact, read <clone>/skills/write-long-term-memory/SKILL.md.
- Always run `sh <clone>/scripts/memory-sync.sh` before either operation.
- Never load the whole memory repository into the prompt.
```

Use the actual absolute clone path for `<clone>`.

## Recommended git policy

- Use one clone per machine.
- Keep real memory data in a private repository.
- Enable `git config core.hooksPath .githooks` in every clone.
- Do not force-push.
- Do not store generated output from a different worktree state.

## Agent behavior checklist

Before recall:

1. Run the sync script.
2. Read `INDEX.md`.
3. Open the smallest relevant MOC.
4. Read frontmatter and first paragraph before full bodies.
5. Report IDs, paths, freshness, and conflicts.

Before write:

1. Run the sync script.
2. Decide `profile` versus `decision`.
3. Check whether a fact already exists.
4. Confirm sensitive writes.
5. Write one fact per file.
6. Regenerate the index.
7. Suggest neighbours once.
8. Commit and push with a focused message.
