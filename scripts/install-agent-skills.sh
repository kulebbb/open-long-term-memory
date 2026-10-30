#!/bin/sh
# Install or remove the Open Long-Term Memory Agent Skills.
#
# The default installation uses symlinks so `git pull` in the memory repository
# immediately updates both the Skill files and the global instruction pointer.
set -eu

BEGIN_MARK="<!-- open-long-term-memory:begin -->"
END_MARK="<!-- open-long-term-memory:end -->"
SKILL_NAMES="recall-long-term-memory write-long-term-memory"

AGENT="auto"
SKILLS_DIR_OVERRIDE=""
INSTRUCTIONS_FILE_OVERRIDE=""
DRY_RUN=0
UNINSTALL=0

usage() {
  cat <<'EOF'
Usage: sh scripts/install-agent-skills.sh [options]

Options:
  --agent auto|codex|claude|generic
                               Agent platform (default: auto)
  --skills-dir DIR             Override the platform Skills directory
  --instructions-file FILE     Override the global instruction file
  --dry-run                    Print actions without changing files
  --uninstall                  Remove managed links and the instruction block
  -h, --help                   Show this help

Defaults:
  codex    CODEX_HOME/skills and CODEX_HOME/AGENTS.md
           (CODEX_HOME defaults to ~/.codex)
  claude   ~/.claude/skills and ~/.claude/CLAUDE.md
  generic  Requires --skills-dir and --instructions-file

The installer only replaces symlinks that point to this repository. It never
overwrites a regular file or an unrelated directory.
EOF
}

die() {
  echo "error: $*" >&2
  exit 2
}

need_value() {
  [ "$#" -ge 2 ] && [ -n "$2" ] || die "$1 requires a value"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --agent)
      need_value "$@"
      AGENT=$2
      shift 2
      ;;
    --skills-dir)
      need_value "$@"
      SKILLS_DIR_OVERRIDE=$2
      shift 2
      ;;
    --instructions-file)
      need_value "$@"
      INSTRUCTIONS_FILE_OVERRIDE=$2
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --uninstall)
      UNINSTALL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown option: $1 (run with --help)"
      ;;
  esac
done

case "$AGENT" in
  auto|codex|claude|generic) ;;
  *) die "--agent must be auto, codex, claude, or generic" ;;
esac

[ -n "${HOME:-}" ] || die "HOME is not set"

SCRIPT_DIR=$(CDPATH= cd "$(dirname "$0")" && pwd -P) || die "cannot resolve script directory"
REPO_ROOT=$(CDPATH= cd "$SCRIPT_DIR/.." && pwd -P) || die "cannot resolve repository root"
SOURCE_SKILLS="$REPO_ROOT/skills"

detect_agent() {
  codex_present=0
  claude_present=0
  if [ -n "${CODEX_HOME:-}" ] || [ -d "$HOME/.codex" ]; then
    codex_present=1
  fi
  if [ -d "$HOME/.claude" ]; then
    claude_present=1
  fi

  if [ "$codex_present" -eq 1 ] && [ "$claude_present" -eq 1 ]; then
    die "both Codex and Claude directories were detected; pass --agent codex or --agent claude"
  fi
  if [ "$codex_present" -eq 1 ]; then
    AGENT="codex"
  elif [ "$claude_present" -eq 1 ]; then
    AGENT="claude"
  else
    die "no supported agent directory detected; pass --agent or use --agent generic with paths"
  fi
}

[ "$AGENT" = "auto" ] && detect_agent

case "$AGENT" in
  codex)
    CODEX_BASE="${CODEX_HOME:-$HOME/.codex}"
    SKILLS_DIR="${SKILLS_DIR_OVERRIDE:-$CODEX_BASE/skills}"
    INSTRUCTIONS_FILE="${INSTRUCTIONS_FILE_OVERRIDE:-$CODEX_BASE/AGENTS.md}"
    ;;
  claude)
    SKILLS_DIR="${SKILLS_DIR_OVERRIDE:-$HOME/.claude/skills}"
    INSTRUCTIONS_FILE="${INSTRUCTIONS_FILE_OVERRIDE:-$HOME/.claude/CLAUDE.md}"
    ;;
  generic)
    [ -n "$SKILLS_DIR_OVERRIDE" ] || die "--agent generic requires --skills-dir"
    [ -n "$INSTRUCTIONS_FILE_OVERRIDE" ] || die "--agent generic requires --instructions-file"
    SKILLS_DIR=$SKILLS_DIR_OVERRIDE
    INSTRUCTIONS_FILE=$INSTRUCTIONS_FILE_OVERRIDE
    ;;
esac

for name in $SKILL_NAMES; do
  [ -f "$SOURCE_SKILLS/$name/SKILL.md" ] || die "missing source Skill: $SOURCE_SKILLS/$name/SKILL.md"
done

marker_state() {
  file=$1
  if [ ! -f "$file" ]; then
    echo "absent"
    return
  fi
  awk -v begin="$BEGIN_MARK" -v end="$END_MARK" '
    $0 == begin { begin_count++; begin_line = NR }
    $0 == end { end_count++; end_line = NR }
    END {
      if (begin_count == 0 && end_count == 0) {
        print "absent"
      } else if (begin_count == 1 && end_count == 1 && begin_line < end_line) {
        print "present"
      } else {
        print "invalid"
      }
    }
  ' "$file"
}

clean_instructions() {
  file=$1
  input=$2
  awk -v begin="$BEGIN_MARK" -v end="$END_MARK" '
    $0 == begin { inside = 1; next }
    $0 == end { inside = 0; next }
    !inside { lines[++count] = $0 }
    END {
      while (count > 0 && lines[count] == "") {
        count--
      }
      for (i = 1; i <= count; i++) {
        print lines[i]
      }
    }
  ' "$input" > "$file"
}

instruction_block() {
  cat <<EOF
$BEGIN_MARK
Long-term memory:
- Before recalling durable facts, read "$REPO_ROOT/skills/recall-long-term-memory/SKILL.md".
- Before saving a durable fact, read "$REPO_ROOT/skills/write-long-term-memory/SKILL.md".
- Before either operation, run "sh $REPO_ROOT/scripts/memory-sync.sh".
$END_MARK
EOF
}

preflight_skill_link() {
  source_dir=$1
  destination=$2

  if [ -L "$destination" ]; then
    resolved_destination=$(CDPATH= cd "$destination" 2>/dev/null && pwd -P || true)
    resolved_source=$(CDPATH= cd "$source_dir" && pwd -P)
    [ "$resolved_destination" = "$resolved_source" ] \
      || die "refusing to replace unrelated symlink: $destination"
  elif [ -e "$destination" ]; then
    die "refusing to replace existing path: $destination"
  fi
}

preflight_instructions() {
  state=$(marker_state "$INSTRUCTIONS_FILE")
  [ "$state" != "invalid" ] \
    || die "invalid or duplicate managed markers in $INSTRUCTIONS_FILE"
  if [ -e "$INSTRUCTIONS_FILE" ] && [ ! -f "$INSTRUCTIONS_FILE" ]; then
    die "instruction path is not a regular file: $INSTRUCTIONS_FILE"
  fi
}

write_instructions() {
  action=$1
  state=$(marker_state "$INSTRUCTIONS_FILE")

  if [ "$DRY_RUN" -eq 1 ]; then
    if [ "$action" = "install" ]; then
      echo "would install managed instruction block in $INSTRUCTIONS_FILE"
    elif [ "$state" = "present" ]; then
      echo "would remove managed instruction block from $INSTRUCTIONS_FILE"
    fi
    return
  fi

  if [ "$action" = "uninstall" ] && { [ ! -f "$INSTRUCTIONS_FILE" ] || [ "$state" = "absent" ]; }; then
    echo "instructions: no managed block in $INSTRUCTIONS_FILE"
    return
  fi

  parent_dir=$(dirname "$INSTRUCTIONS_FILE")
  mkdir -p "$parent_dir"
  tmp="$INSTRUCTIONS_FILE.tmp.$$"
  trap 'rm -f "$tmp"' EXIT HUP INT TERM

  if [ -f "$INSTRUCTIONS_FILE" ]; then
    cp -p "$INSTRUCTIONS_FILE" "$tmp"
  else
    : > "$tmp"
  fi

  if [ -f "$INSTRUCTIONS_FILE" ]; then
    clean_instructions "$tmp" "$INSTRUCTIONS_FILE"
  else
    : > "$tmp"
  fi
  if [ "$action" = "install" ]; then
    if [ -s "$tmp" ]; then
      printf '\n' >> "$tmp"
    fi
    instruction_block >> "$tmp"
  fi
  mv "$tmp" "$INSTRUCTIONS_FILE"
  trap - EXIT HUP INT TERM

  if [ "$action" = "install" ]; then
    echo "instructions: installed managed block in $INSTRUCTIONS_FILE"
  else
    echo "instructions: removed managed block from $INSTRUCTIONS_FILE"
  fi
}

install_skills() {
  for name in $SKILL_NAMES; do
    source_dir="$SOURCE_SKILLS/$name"
    destination="$SKILLS_DIR/$name"
    preflight_skill_link "$source_dir" "$destination"
  done

  if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$SKILLS_DIR"
  fi

  for name in $SKILL_NAMES; do
    source_dir="$SOURCE_SKILLS/$name"
    destination="$SKILLS_DIR/$name"
    if [ -L "$destination" ]; then
      echo "skills: already linked $destination"
      continue
    fi
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "would link $destination -> $source_dir"
    else
      ln -s "$source_dir" "$destination"
      echo "skills: linked $destination"
    fi
  done
}

uninstall_skills() {
  for name in $SKILL_NAMES; do
    source_dir="$SOURCE_SKILLS/$name"
    destination="$SKILLS_DIR/$name"
    if [ ! -L "$destination" ]; then
      echo "skills: no managed link at $destination"
      continue
    fi
    resolved_destination=$(CDPATH= cd "$destination" 2>/dev/null && pwd -P || true)
    resolved_source=$(CDPATH= cd "$source_dir" && pwd -P)
    if [ "$resolved_destination" != "$resolved_source" ]; then
      echo "skills: leaving unrelated symlink at $destination" >&2
      continue
    fi
    if [ "$DRY_RUN" -eq 1 ]; then
      echo "would remove link $destination"
    else
      rm "$destination"
      echo "skills: removed link $destination"
    fi
  done
}

preflight_instructions

echo "agent: $AGENT"
echo "skills directory: $SKILLS_DIR"
echo "instructions file: $INSTRUCTIONS_FILE"

if [ "$UNINSTALL" -eq 1 ]; then
  uninstall_skills
  write_instructions uninstall
else
  install_skills
  write_instructions install
fi

if [ "$DRY_RUN" -eq 1 ]; then
  echo "dry run complete; no files changed"
else
  echo "done; restart the agent session to load the updated instructions"
fi
