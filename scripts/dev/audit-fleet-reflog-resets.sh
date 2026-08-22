#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: campaign
# Delete-when: plans/active/issues/slot11_silent_branch_reset_data_loss_2026_07_13.md closed (INFRA todos 1/2/4 fixed + verified in prod)
#
# Fleet-wide audit for the "branch: Reset to origin/<branch>" reflog signature (see
# plans/active/issues/slot11_silent_branch_reset_data_loss_2026_07_13.md) — an unidentified
# process silently `git reset --hard`s a slot clone straight to origin, discarding
# already-committed local work. `git merge --ff-only` (the documented agent path) produces a
# "merge: Fast-forward" reflog line, NOT "branch: Reset to origin/...", so any occurrence of the
# latter is evidence of the out-of-band mechanism, not normal agent git usage.
#
# For every repo clone in every .tabs/<slot>/ directory, scans `git reflog show HEAD` for a
# "Reset to origin" entry immediately preceded (in wall-clock time — i.e. the NEXT-older reflog
# line) by a "commit:"/"commit (amend):" entry — meaning a locally-committed commit was discarded
# by that reset. Reports whether the discarded SHA is still reachable from current HEAD or from
# origin (already safe) or orphaned (recoverable only via reflog, at risk once the reflog entry
# ages out of the default 90-day expiry).
#
# Usage: bash scripts/dev/audit-fleet-reflog-resets.sh [--json]
#
# Read-only: runs `git reflog show` / `git merge-base --is-ancestor` only. Never mutates any
# slot's clone.

set -euo pipefail

WS_ROOT="${WORKSPACE_ROOT:-$HOME/unified-trading-system-repos}"
TABS_DIR="$WS_ROOT/.tabs"
JSON_MODE=0
[ "${1:-}" = "--json" ] && JSON_MODE=1

if [ ! -d "$TABS_DIR" ]; then
  echo "no .tabs directory found at $TABS_DIR" >&2
  exit 1
fi

hits=0
json_rows=()

for slot_dir in "$TABS_DIR"/*/; do
  [ -d "$slot_dir" ] || continue
  slot_name="$(basename "$slot_dir")"

  for repo_dir in "$slot_dir"*/; do
    [ -e "$repo_dir/.git" ] || continue
    repo_name="$(basename "$repo_dir")"

    reflog="$(git -C "$repo_dir" reflog show --date=iso HEAD 2>/dev/null || true)"
    [ -n "$reflog" ] || continue

    total_lines=$(wc -l <<<"$reflog")
    reset_linenos="$(grep -n 'Reset to origin' <<<"$reflog" | cut -d: -f1 || true)"
    [ -n "$reset_linenos" ] || continue

    while IFS= read -r lineno; do
      [ -n "$lineno" ] || continue
      reset_line="$(sed -n "${lineno}p" <<<"$reflog")"
      discard_lineno=$((lineno + 1))
      [ "$discard_lineno" -le "$total_lines" ] || continue
      discard_line="$(sed -n "${discard_lineno}p" <<<"$reflog")"

      # Only a genuine discard if the entry one step older is a real commit action
      # (as opposed to e.g. another checkout/reset noise line).
      if ! grep -qE 'commit(\s*\(amend\))?:' <<<"$discard_line"; then
        continue
      fi

      discard_sha="$(awk '{print $1}' <<<"$discard_line")"
      branch="$(git -C "$repo_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"

      reachable_head="no"
      if git -C "$repo_dir" merge-base --is-ancestor "$discard_sha" HEAD 2>/dev/null; then
        reachable_head="yes"
      fi

      reachable_origin="no"
      if git -C "$repo_dir" merge-base --is-ancestor "$discard_sha" "origin/$branch" 2>/dev/null; then
        reachable_origin="yes"
      fi

      status="RECOVERED"
      if [ "$reachable_head" = "no" ] && [ "$reachable_origin" = "no" ]; then
        status="AT_RISK_REFLOG_ONLY"
      fi

      hits=$((hits + 1))
      if [ "$JSON_MODE" -eq 1 ]; then
        json_rows+=("{\"slot\":\"$slot_name\",\"repo\":\"$repo_name\",\"discarded_sha\":\"$discard_sha\",\"reset_line\":\"$(sed 's/"/\\"/g' <<<"$reset_line")\",\"discard_line\":\"$(sed 's/"/\\"/g' <<<"$discard_line")\",\"reachable_from_head\":\"$reachable_head\",\"reachable_from_origin\":\"$reachable_origin\",\"status\":\"$status\"}")
      else
        echo "slot=$slot_name repo=$repo_name status=$status discarded_sha=$discard_sha reachable_from_HEAD=$reachable_head reachable_from_origin=$reachable_origin"
        echo "  reset:    $reset_line"
        echo "  discarded: $discard_line"
      fi
    done <<<"$reset_linenos"
  done
done

if [ "$JSON_MODE" -eq 1 ]; then
  printf '{"total_hits": %d, "findings": [%s]}\n' "$hits" "$(IFS=,; echo "${json_rows[*]:-}")"
else
  echo "---"
  echo "total 'Reset to origin' + discarded-commit signatures found: $hits"
fi
