# Contributing

Thanks for improving Open Long-Term Memory.

## Ground rules

- Use fictional examples only.
- Never add secrets, access tokens, personal contact details, private URLs, customer data, or real organizational decisions.
- Keep the runtime dependency-free. Python must use the standard library; synchronization must remain POSIX `sh`.
- Do not hand-edit generated blocks in `INDEX.md` or `moc/*.md`.
- Update documentation and tests when changing the schema or generated output.

## Local checks

```bash
git config core.hooksPath .githooks
python3 -m unittest discover -s tests -v
python3 scripts/build_memory_index.py --check
sh -n scripts/memory-sync.sh
sh -n scripts/install-agent-skills.sh
```

The pre-commit hook also rejects a commit when memory files are modified but not staged, because the generated index is built from the worktree.

## Pull requests

Create a focused pull request into `main`. Describe the behavior change, the reason for it, and the checks performed. Keep changes focused. Include tests for index parsing, validation, relation handling, generated output, or synchronization behavior when applicable.

`main` is protected: the PR needs code-owner approval, resolved conversations, and passing `verify` and `CodeQL` checks. External contributors cannot push directly, force-push, or delete the branch.

By contributing, you agree that your contribution is licensed under the repository's MIT License.
