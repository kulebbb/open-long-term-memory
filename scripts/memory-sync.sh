#!/bin/sh
# Multi-host synchronization for a long-term memory clone.
# This script only fetches and fast-forwards. It never merges, rebases, or
# modifies uncommitted files.
#
# Usage: sh scripts/memory-sync.sh
#
# Stdout is one status tag. Exit codes:
#   0  OK / SYNCED / SKIP
#   3  OFFLINE
#   4  STALE
#   5  AHEAD / DIVERGED
#
# Warnings on stderr do not change the status.
set -u

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "SKIP not a git repository; using local files"
  exit 0
}
cd "$ROOT" || {
  echo "SKIP could not enter repository root; using local files"
  exit 0
}

BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"

short() { git rev-parse --short=7 "$1"; }

# Check local configuration that can make recall silently inconsistent.
check_local() {
  if [ "$(git config --get core.hooksPath 2>/dev/null)" != ".githooks" ]; then
    echo "hint: pre-commit hook is not enabled in this clone. Enable it with: git config core.hooksPath .githooks" >&2
  fi
  # If memory files are dirty, the generated index is expected to be stale.
  # Ignore unrelated untracked files outside the memory directories.
  if [ -z "$(git status --porcelain -- profile people projects decisions journal open-loops)" ] \
    && command -v python3 >/dev/null 2>&1 \
    && [ -f scripts/build_memory_index.py ]; then
    if ! python3 scripts/build_memory_index.py --check >/dev/null 2>&1; then
      echo "warning: index check failed. Run: python3 scripts/build_memory_index.py --check" >&2
    fi
  fi
}

finish() {
  check_local
  exit "$1"
}

if [ "$BRANCH" != "main" ]; then
  echo "SKIP current branch is ${BRANCH}, not main; nothing was synchronized"
  finish 0
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "SKIP no origin remote; using local main@$(short HEAD)"
  finish 0
fi

if ! git fetch --quiet --prune origin main 2>/dev/null; then
  echo "OFFLINE could not fetch; using local main@$(short HEAD) without checking the remote"
  finish 3
fi

if ! REMOTE="$(git rev-parse --verify --quiet origin/main)"; then
  echo "OFFLINE origin/main is unavailable; using local main@$(short HEAD)"
  finish 3
fi

LOCAL="$(git rev-parse HEAD)"

if [ "$LOCAL" = "$REMOTE" ]; then
  echo "OK main@$(short HEAD)"
  finish 0
fi

AHEAD="$(git rev-list --count "$REMOTE..$LOCAL")"
BEHIND="$(git rev-list --count "$LOCAL..$REMOTE")"

if [ "$AHEAD" -gt 0 ] && [ "$BEHIND" -gt 0 ]; then
  echo "DIVERGED main@$(short HEAD), ahead ${AHEAD} / behind ${BEHIND}; stop and ask the user (never force-push)"
  finish 5
fi

if [ "$AHEAD" -gt 0 ]; then
  echo "AHEAD main@$(short HEAD), ${AHEAD} unpushed commit(s); push before writing elsewhere"
  finish 5
fi

# If tracked files are dirty, do not pull. This keeps uncommitted work intact.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "STALE main@$(short HEAD), behind ${BEHIND}; uncommitted changes prevented fast-forward"
  finish 4
fi

if git merge --ff-only --quiet "$REMOTE"; then
  echo "SYNCED main@$(short HEAD), fast-forwarded ${BEHIND} commit(s)"
  finish 0
fi

echo "STALE main@$(short HEAD), behind ${BEHIND}; fast-forward failed"
finish 4
