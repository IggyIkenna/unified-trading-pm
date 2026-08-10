#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Staged-files-only gate for ACCIDENTAL (undeclared) dispatch exclusions.
#
# THE GAP THIS CLOSES. `check_ao_dispatch_visibility_gate.py` is corpus-wide and runs only in the
# FULL quality gate. A `docs(plans):` push takes prek alone, so a plan whose open todo is held by
# a marker buried mid-sentence lands on origin unchallenged — and the failure then surfaces on
# some unrelated agent's full QG run, attributed to whichever commit happened to trigger it. That
# happened on 2026-08-10 and cost this session a wrong diagnosis before the real authoring
# mistake was identified. Same fast-path-blind-to-full-gate shape as check_todo_regression /
# check_effort_signal_ratchet / check_prosewrap_padding, all migrated 2026-08-09.
#
# NO SECOND IMPLEMENTATION OF THE ORACLE. The verdict comes from agent-orchestrator's own
# `dispatch_visibility_report --check-files`, which reuses `_eligible_todos` (the dispatcher's
# real walk, captured via a spy) and `_is_declared`. Re-deriving either here is exactly the
# failure the AO module documents four separate incidents of; a marker regex that drifts from the
# dispatcher's is worse than no check, because it reports confidently on a rule nobody enforces.
#
# HEAD-vs-current, per file: only an exclusion THIS commit introduces is flagged. A pre-existing
# one in a plan you happen to be editing is corpus debt for the full-sweep ratchet, not your
# commit's problem (RULE-11 blast radius).
#
# COST, and why the pre-filter is not optional: the AO module costs ~8s to import — on a repo
# whose whole livelock story is "the commit critical section is longer than the gap between
# commits", adding that to every doc push would be self-defeating. A marker-token grep (~10ms)
# decides whether the expensive check runs at all; measured 2026-08-10, 184 of 785 active plans
# carry a marker token, so roughly three in four pushes pay nothing.
#
# Degrades to a silent no-op when the sibling AO checkout or its venv is absent, mirroring
# check_ao_dispatch_visibility_gate.py's own "CI without siblings is unaffected" convention.
#
# Usage: check_accidental_exclusions_only.sh <plan> [<plan> ...]
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PM_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
WS_ROOT="$(dirname "$PM_DIR")"
AO_DIR="$WS_ROOT/agent-orchestrator"
AO_PY="$AO_DIR/.venv/bin/python3"
MARKER_RE='BLOCKED-[A-Z]|DEFERRED-BY-DESIGN|STRETCH'

[ "$#" -gt 0 ] || exit 0
[ -x "$AO_PY" ] && [ -f "$AO_DIR/server/dispatch_visibility_report.py" ] || exit 0

# Pre-filter: only plans that actually mention a marker can carry an exclusion.
CANDIDATES=()
for f in "$@"; do
  [ -f "$f" ] || continue
  case "$f" in */plans/archive/* | plans/archive/*) continue ;; esac
  grep -qE "$MARKER_RE" "$f" 2>/dev/null && CANDIDATES+=("$f")
done
[ "${#CANDIDATES[@]}" -gt 0 ] || exit 0

_report() { # <file> -> one description per undeclared exclusion
  # ABSOLUTISE FIRST. The module has to be run from the AO checkout (`-m server.…`), and a
  # caller-relative path silently does not exist from there — `check_files` skips a missing file,
  # so the whole gate degrades to "found nothing" while still exiting 0. Caught in test: the
  # injected violation was invisible until this line existed.
  local abs
  abs="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
  (cd "$AO_DIR" && "$AO_PY" -m server.dispatch_visibility_report --check-files "$abs" 2>/dev/null) |
    sed 's/^[^:]*: //'
}

TMPD="$(mktemp -d "${TMPDIR:-/tmp}/accex-XXXXXX")"
trap 'rm -rf "$TMPD"' EXIT
FOUND=0
for f in "${CANDIDATES[@]}"; do
  rel="$(cd "$(dirname "$f")" && pwd)/$(basename "$f")"
  rel="${rel#"$PM_DIR"/}"

  # HEAD's version, written under the SAME basename: the report prints the path it was given,
  # and a differing name would be a needless difference between the two sides.
  head_dir="$TMPD/head"
  mkdir -p "$head_dir"
  if ! git -C "$PM_DIR" show "HEAD:$rel" > "$head_dir/$(basename "$f")" 2>/dev/null; then
    : > "$head_dir/$(basename "$f")" # new file: everything in it is new
  fi

  cur="$(_report "$f" | sort -u)"
  [ -n "$cur" ] || continue
  prev="$(_report "$head_dir/$(basename "$f")" | sort -u)"
  new="$(comm -23 <(printf '%s\n' "$cur") <(printf '%s\n' "$prev") 2>/dev/null | grep -v '^$' || true)"
  [ -n "$new" ] || continue

  FOUND=1
  echo "  ❌ ${rel}: open todo(s) held by a marker that does not declare itself:"
  printf '%s\n' "$new" | sed 's/^/       /' | head -5
done

if [ "$FOUND" = "1" ]; then
  echo "     A marker only DECLARES a hold when it opens the checkbox line — inside the leading"
  echo "     [TAG] cluster or at the head of the description. Buried mid-sentence it still stops"
  echo "     the todo dispatching, but reads as an accident, and the corpus-wide gate will fail"
  echo "     later on someone else's run. Fix: move the marker to the head of the line"
  echo "     (e.g. '- [ ] [BLOCKED-CREDENTIALS][INFRA] P1. …'), or reword so it no longer trips."
  echo "     Never hand-edit ao_dispatch_visibility_baseline.yaml."
  exit 1
fi
exit 0
