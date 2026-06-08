#!/usr/bin/env bash
# Linux event-based reflog watcher — inotifywait equivalent of watch-and-audit-reflog.sh (fswatch/macOS).
# Watches each workspace repo's .git/logs and runs the audit (+ alert on high-risk) on change.
#
# DEBOUNCED: a burst of git events (e.g. the 5-min FF-pull touching many repos) collapses into a
# SINGLE audit run once the dust settles, so it never thrashes the host. Scope = the root clones
# the audit actually reads (manifest repos under WORKSPACE_ROOT), ~25 dirs — not the slot worktrees
# (their reflogs live under .git/worktrees/<id>/ and the audit doesn't read them).
#
# Notifications are silent unless HIGH RISK (handled by run-audit-reflog-with-alert.sh).
# Run by: systemd-user audit-reflog-watch.service (install-audit-reflog-guard.sh). Also run manually.
# Prereq: inotify-tools (`sudo apt install inotify-tools`).
#
# Env: AUDIT_REFLOG_DEBOUNCE=<secs> (default 5).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve workspace root (same logic as audit-reflog-resets.sh).
if [[ -f "$(pwd)/unified-trading-pm/workspace-manifest.json" ]]; then
  WORKSPACE_ROOT="$(pwd)"
elif [[ -f "$(pwd)/workspace-manifest.json" ]]; then
  WORKSPACE_ROOT="$(cd .. && pwd)"
else
  WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
fi
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"
WRAPPER="$SCRIPT_DIR/run-audit-reflog-with-alert.sh"
DEBOUNCE="${AUDIT_REFLOG_DEBOUNCE:-5}"

command -v inotifywait >/dev/null 2>&1 || {
  echo "ERROR: inotifywait not found — install inotify-tools (sudo apt install inotify-tools)" >&2
  exit 1
}
[[ -f "$MANIFEST" ]] || { echo "ERROR: missing $MANIFEST" >&2; exit 1; }

# Collect each manifest repo's .git/logs dir (root clones only — what the audit reads).
WATCH=()
while IFS= read -r repo; do
  d="$WORKSPACE_ROOT/$repo/.git/logs"
  [[ -d "$d" ]] && WATCH+=("$d")
done < <(jq -r '.repositories | keys[]' "$MANIFEST" 2>/dev/null)
[[ ${#WATCH[@]} -gt 0 ]] || { echo "ERROR: no .git/logs dirs found under $WORKSPACE_ROOT" >&2; exit 1; }

echo "[$(date -u +%H:%M:%SZ)] watching ${#WATCH[@]} repo reflog dir(s), debounce=${DEBOUNCE}s"

# -m: monitor (don't exit); -r: recurse into logs/ (refs/*, HEAD). On each event, drain the
# burst (read with a DEBOUNCE timeout) then run the audit once. `cd` so the audit/wrapper
# resolve WORKSPACE_ROOT from cwd.
cd "$WORKSPACE_ROOT"
inotifywait -m -r -e modify,create,move,delete "${WATCH[@]}" 2>/dev/null | while read -r _line; do
  # Coalesce: keep consuming events until the stream is quiet for DEBOUNCE seconds.
  while read -t "$DEBOUNCE" -r _drain; do :; done
  bash "$WRAPPER" >/dev/null 2>&1 || true
done
