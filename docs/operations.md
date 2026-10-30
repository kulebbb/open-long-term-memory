# Operations

## Backups

The Git remote is the primary backup. Keep at least one protected copy of the repository, and ensure generated indexes are committed alongside source memories.

## Multiple machines

Run `sh scripts/memory-sync.sh` before reading or writing. The script reports one explicit state so an agent can distinguish a current clone from a stale or offline one.

## Index recovery

Generated files can always be recreated:

```bash
python3 scripts/build_memory_index.py
python3 scripts/build_memory_index.py --check
```

Never hand-merge `INDEX.md` or `moc/*.md`. Rebase source memories, then regenerate.

## Rotating a leaked secret

1. Revoke or rotate the secret outside this repository.
2. Remove the value from the working tree.
3. Determine whether it exists in Git history.
4. Rewrite history only with explicit owner approval and a coordinated backup.
5. Force-push only under that approved recovery plan; normal memory workflows must never force-push.

## Retiring a project

Set the project's memory records to `status: archived`. If the project has no active facts, the generator removes its project page. If the generated page was manually edited outside the markers, the generator preserves it and reports an error for human review.
