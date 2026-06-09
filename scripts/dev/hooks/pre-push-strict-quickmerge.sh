#!/usr/bin/env bash
# pre-push-strict-quickmerge.sh — Path-B local enforcement of the strict-quickmerge HARD RULE.
#
# Installed as each slot clone's .git/hooks/pre-push (by setup-tab-worktrees.sh, or the one-shot
# install loop). On a push to live-defi-rollout / staging / main it runs the strict-quickmerge
# guard over the commits being pushed: a CODE commit that bypassed quickmerge (no `Quickmerge:`
# trailer, not a carve-out) is flagged. WARN by default; set STRICT_QUICKMERGE_BLOCK=1 to block.
# Bypassable with `git push --no-verify` (it is the local floor; the staging-PR quality-gates-v2 is
# the server backstop — it sees every commit at the promotion boundary).
#
# stdin: <local_ref> <local_sha> <remote_ref> <remote_sha>  (per pushed ref)
set -euo pipefail

# Resolve PM root (the guard SSOT) from the workspace root.
_here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
_ws="${UNIFIED_TRADING_WORKSPACE_ROOT:-}"
if [ -z "$_ws" ]; then
  # walk up to the dir containing unified-trading-pm
  _d="$(pwd)"
  while [ "$_d" != "/" ] && [ ! -d "$_d/unified-trading-pm/scripts/cicd" ]; do _d="$(dirname "$_d")"; done
  _ws="$_d"
fi
_guard="${_ws}/unified-trading-pm/scripts/cicd/check_strict_quickmerge.py"
[ -f "$_guard" ] || exit 0   # guard not found → no-op (never block a push on a missing tool)

_protected="refs/heads/live-defi-rollout refs/heads/staging refs/heads/main"
_rc=0
while read -r _lref _lsha _rref _rsha; do
  case " $_protected " in *" $_rref "*) : ;; *) continue ;; esac
  [ "$_lsha" = "0000000000000000000000000000000000000000" ] && continue  # delete
  if [ "$_rsha" = "0000000000000000000000000000000000000000" ]; then
    _range="$_lsha"   # new ref — check all reachable (bounded by the guard's rev-list)
  else
    _range="${_rsha}..${_lsha}"
  fi
  python3 "$_guard" --range "$_range" || _rc=$?
done
exit "$_rc"
