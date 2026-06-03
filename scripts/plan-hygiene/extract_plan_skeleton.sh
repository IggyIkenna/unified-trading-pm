#!/usr/bin/env bash
# Deterministic plan-skeleton extractor for the Plan Health Agent.
#
# The full epics+active+issues corpus is ~3 MB (~800K tokens) — ~4x Haiku's 200K
# window, so letting the agent read whole plan bodies is unreliable (it samples).
# Instead we extract ONLY the signal contradiction-detection needs — per plan:
#   - key frontmatter (status / parent_epic / locked_by / depends_on)
#   - level-2 section headers (## …)         → scope signal
#   - open todos (- [ ] …)                    → what's still pending
#   - done/open todo counts                   → claimed completion
# This is ~10-20x smaller, fits the window, and is fully deterministic input.
#
# Scope: plans/active/*.md + plans/epics/*.md + plans/active/issues/*.md.
# Excludes archive + non-plan files (INDEX / template / README / _*.md ledgers).
#
# Output: $1 (default plan_skeleton.md).
# Usage: bash scripts/plan-hygiene/extract_plan_skeleton.sh [out.md]
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PM_DIR" || exit 1
OUT="${1:-plan_skeleton.md}"

MAX_HEADERS=20   # cap level-2 headers per plan
MAX_TODOS=25     # cap open todos per plan

fm() { # extract a frontmatter scalar field ($2) from file ($1), first match only
  grep -m1 -E "^$2:[[:space:]]*" "$1" 2>/dev/null | sed -E "s/^$2:[[:space:]]*//; s/[[:space:]]*$//"
}

emit_plan() {
  local f="$1" group="$2"
  local name status epic lock deps done_n open_n
  name=$(basename "$f")
  status=$(fm "$f" status)
  epic=$(fm "$f" parent_epic)
  lock=$(fm "$f" locked_by)
  deps=$(fm "$f" depends_on)
  # grep -c already prints 0 (and exits 1) when there are no matches — do NOT add
  # `|| echo 0` (that would print a second 0). Just default if the var is empty.
  done_n=$(grep -c '^- \[x\]' "$f" 2>/dev/null); done_n=${done_n:-0}
  open_n=$(grep -c '^- \[ \]' "$f" 2>/dev/null); open_n=${open_n:-0}

  printf '### [%s] %s  {status=%s parent_epic=%s locked_by=%s depends_on=%s done=%s open=%s}\n' \
    "$group" "$name" "${status:-?}" "${epic:-none}" "${lock:-none}" "${deps:-none}" "$done_n" "$open_n"

  # Level-2 headers (scope signal)
  grep -E '^## ' "$f" 2>/dev/null | head -"$MAX_HEADERS"

  # Open todos (pending-work signal)
  local todos
  todos=$(grep -E '^- \[ \] ' "$f" 2>/dev/null | head -"$MAX_TODOS")
  if [ -n "$todos" ]; then
    echo "open todos:"
    printf '%s\n' "$todos"
  fi
  if [ "$open_n" -gt "$MAX_TODOS" ]; then
    echo "… (+$((open_n - MAX_TODOS)) more open todos)"
  fi
  echo ""
}

{
  echo "# Plan skeletons (deterministic extract — frontmatter + headers + open todos)"
  echo "# Scope: plans/active + plans/epics + plans/active/issues. Archive + non-plan files excluded."
  echo ""

  echo "## ── plans/active ──────────────────────────────────────────────"
  while IFS= read -r f; do emit_plan "$f" active; done < <(
    find plans/active -maxdepth 1 -name '*.md' \
      ! -name 'INDEX.md' ! -name 'task_template.md' ! -name 'README*.md' ! -name '_*.md' | sort)

  echo "## ── plans/epics ───────────────────────────────────────────────"
  while IFS= read -r f; do emit_plan "$f" epic; done < <(
    find plans/epics -maxdepth 1 -name '*.md' ! -name 'README*.md' | sort)

  echo "## ── plans/active/issues ───────────────────────────────────────"
  while IFS= read -r f; do emit_plan "$f" issue; done < <(
    find plans/active/issues -maxdepth 1 -name '*.md' ! -name 'README*.md' | sort)
} > "$OUT"

echo "SKELETON_BYTES=$(wc -c < "$OUT" | tr -d ' ')"
