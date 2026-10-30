# Open Long-Term Memory

Markdown-native long-term memory for AI agents.

This project is a small, auditable framework for storing durable facts as plain Markdown files. It is designed for people and agents who want memory that is readable in any editor, versioned with Git, and usable from multiple machines without building a database or vector store.

The core rule is simple: **one fact per file**. YAML frontmatter is the source of truth; indexes and maps of content are generated projections.

## Why this exists

- **Human-readable**: every memory is a normal Markdown file.
- **Progressive disclosure**: agents start from small indexes instead of loading the whole repository into context.
- **Auditable**: Git records who changed which fact and when.
- **Agent-friendly**: bundled Skills define when and how to recall or write memory.
- **Multi-host aware**: a fast-forward-only sync script makes stale clones visible.
- **Zero runtime dependencies**: the indexer uses only the Python standard library; sync uses POSIX `sh`.
- **Obsidian-compatible**: file names equal memory IDs, so `[[id]]` links become graph edges.

## How it works

Recall follows three levels:

| Level | Read this | Purpose |
|-------|-----------|---------|
| L0 | `INDEX.md` and the smallest relevant `moc/*.md` | Fast navigation and summaries |
| L1 | A candidate file's frontmatter and first paragraph | Decide whether it applies |
| L2 | The full body of one to three clearly relevant files | Load only the evidence needed |

Agents should never dump the entire memory repository into a prompt.

## Quick start

Requirements:

- Python 3.9 or newer
- Git
- A POSIX-compatible shell for `scripts/memory-sync.sh`

```bash
git clone https://github.com/kulebbb/open-long-term-memory.git
cd open-long-term-memory

# Enable automatic index rebuilds before each commit.
git config core.hooksPath .githooks

# Verify the demo data and generated index.
python3 -m unittest discover -s tests -v
python3 scripts/build_memory_index.py --check
```

The repository ships with a fictional `sample-app` dataset so every index page has useful content. Replace or remove the `example-*` records when starting your own memory store.

## Connect an agent

Keep this repository as a separate clone. Add a pointer in the agent's global instructions, using the actual local clone path:

```text
Long-term memory:
- Read <clone>/skills/recall-long-term-memory/SKILL.md before recalling durable facts.
- Read <clone>/skills/write-long-term-memory/SKILL.md before saving one.
- Before either operation, run `sh <clone>/scripts/memory-sync.sh`.
```

This keeps instructions in the repository. Updating memory workflows is then a normal `git pull`, with no second copy to maintain.

More detail: [Agent integration](docs/agent-integration.md).

## Daily commands

```bash
# Rebuild INDEX.md and moc/*.md
python3 scripts/build_memory_index.py

# Validate without writing
python3 scripts/build_memory_index.py --check

# Treat missing project/person anchors as errors
python3 scripts/build_memory_index.py --strict

# Suggest up to five possible neighbours for a new memory
python3 scripts/build_memory_index.py --suggest-links <id>

# Check whether this clone is current
sh scripts/memory-sync.sh

# Run all tests
python3 -m unittest discover -s tests -v
```

The `pre-commit` hook rebuilds generated files whenever memory changes are committed. GitHub Actions repeats the checks so bypassed hooks cannot silently publish a stale index.

## Layout

| Path | Purpose |
|------|---------|
| `profile/` | Stable identity, preferences, and standing rules |
| `people/` | People, roles, and relationships |
| `projects/<slug>/` | Facts about one product, team, or initiative |
| `decisions/` | Dated decisions, ADR-lite |
| `journal/` | Time-bound notes that may later be archived |
| `open-loops/` | Unfinished work with explicit close conditions |
| `moc/` | Generated maps of content |
| `skills/` | Agent workflows for recall and write |
| `scripts/` | Index generation and multi-host synchronization |
| `templates/` | Copyable frontmatter templates |
| `tests/` | Standard-library test suite |
| `INDEX.md` | Generated top-level index |

`profile` answers "what remains true until explicitly changed?"

`decision` answers "what was decided at a point in time, and may later be superseded?"

See [SCHEMA.md](SCHEMA.md) for frontmatter fields, relation rules, validation behavior, and generated-page semantics. A Chinese translation is available at [SCHEMA.zh-CN.md](SCHEMA.zh-CN.md).

## Multi-host synchronization

Every machine keeps its own clone. Run `sh scripts/memory-sync.sh` before reading or writing memory. The script only fetches and fast-forwards; it never merges, rebases, or touches uncommitted files.

| Tag | Meaning | Recommended action |
|-----|---------|--------------------|
| `OK` / `SYNCED` | Current | Continue |
| `STALE` | Behind, but local changes prevented a pull | Read with a freshness warning; clean before writing |
| `OFFLINE` | Remote unavailable | Read local data and disclose that it was not checked |
| `AHEAD` | Local commits are not pushed | Push before writing elsewhere |
| `DIVERGED` | Both sides advanced | Stop and ask the user; never force-push |
| `SKIP` | Not on `main`, no remote, or no Git repository | Treat as a local copy and say so |

## Privacy and security

This framework is safe to open source as a **template**. A real memory repository usually should not be public.

- Never store passwords, API keys, access tokens, card numbers, or private keys.
- Treat personal data, customer data, internal URLs, and proprietary decisions as sensitive.
- Keep the real memory repository private unless every contributor has reviewed its contents for publication.
- Generated indexes include memory summaries. Files ignored by `.gitignore` and symbolic links are excluded from indexing to reduce accidental disclosure.
- The bundled demo records are fictional. Do not contribute real personal or organizational memory to the public template.

See [SECURITY.md](SECURITY.md) for reporting and operational guidance.

Deployment, backup, recovery, and project-retirement procedures are documented in [Operations](docs/operations.md).

## Extending the framework

The default model deliberately keeps a small set of types:

- `profile`
- `person`
- `project`
- `decision`
- `journal`
- `open-loop`

If you add a new type, update `SCHEMA.md`, `scripts/build_memory_index.py`, templates, and tests together. Generated indexes are never hand-edited; run the indexer instead.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributions must use synthetic examples and must not include secrets or real personal data.

## License

MIT. See [LICENSE](LICENSE).
