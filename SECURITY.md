# Security and privacy

## Intended use

Open Long-Term Memory is a template and tooling repository. It should not contain a real user's memory data.

Use a separate private repository for real memories. Generated indexes contain summaries of every indexed record, so treating the source files as private is not enough: the generated files must remain private too.

## Never store

- Passwords or passphrases
- API keys or access tokens
- Private keys or recovery codes
- Card or bank numbers
- Authentication cookies
- Confidential customer data
- Sensitive personal data that is not required for the agent's task

`.gitignore` is a safety aid, not a security boundary. If a secret enters Git history, revoke or rotate it immediately; removing the current file does not remove historical copies.

## Reporting a vulnerability

Please use the repository's GitHub Security Advisory feature rather than a public issue. Include reproduction steps and the affected files or commands. Do not include live credentials in the report.

## Repository controls

The public repository is configured with:

- Secret scanning and push protection.
- Dependabot vulnerability alerts and automated security fixes.
- Private vulnerability reporting.
- CodeQL default setup for GitHub Actions and Python.
- A protected `main` branch requiring a pull request, code-owner approval, resolved conversations, and passing `verify` and `CodeQL` checks.
- No force-push or branch deletion. The repository owner may bypass review requirements on their own PRs, but required checks still apply.
- Administrators retain an emergency bypass for recovery.
- Read-only default `GITHUB_TOKEN` permissions.
- GitHub-owned Actions only, pinned to full commit SHAs, with Dependabot updates.
- Maintainer approval before Actions run for external contributors' pull requests.
