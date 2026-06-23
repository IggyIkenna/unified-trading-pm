#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# audit_ping_orphans.sh — flag pings that don't reference a plan / issue / audit doc.
#
# Enforces CLAUDE.md HARD RULE "Every Active Ping Must Reference A Plan Item"
# (codified 2026-05-20 round 5; cadence tightened round 6).
#
# Cadence: every 4 hours (6×/day) — operator directive 2026-05-20 round 6:
# "I would grep more often than this every day actually 6 times so every 4
# hours forcing agents to make plans or issues around their pings if they
# can't already reference plan or issues in pm repo."
#
# Behaviour:
# - Scans 3 ping ledgers (cross-side + 2 per-side).
# - For each entry block (delimited by `^## \[` header), checks whether the
#   block body contains at least one reference matching:
#       plans/active/ | plans/epics/ | plans/audit/ | plans/active/issues/
# - Orphan blocks (no match) get appended to BOTH orchestrator inboxes as a
#   structured "ORPHAN-PING NOTIFY" entry.
# - Exits 1 if orphans found, 0 if clean.
#
# Local install (Ikenna's machine — `crontab -e`):
#     0 */4 * * * cd ${WORKSPACE_ROOT}/unified-trading-pm && bash scripts/agents/audit_ping_orphans.sh >> /tmp/orphan_pings_audit.log 2>&1
#
# AWS VM install (agent-orchestrator AWS deployment):
#     Add a Cloud Run scheduler job / EventBridge rule firing every 4h that
#     invokes this script via the orchestrator's worker container. See
#     `plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md`
#     for the deployment surface.
#
# Plan-of-record: this script lands as evidence under master coordinator
# `plans/active/mtds_mdps_master.md` Phase -1
# workspace-discipline prereq.

set -uo pipefail

PM_ROOT="${PM_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"

# Self-pull so local cron scans current ping state, not stale checkout.
# Cloud Run sets K_SERVICE and clones fresh each invocation — skip there.
if [[ -z "${K_SERVICE:-}" ]]; then
  git -C "$PM_ROOT" pull --ff-only origin live-defi-rollout 2>&1 || true
fi

TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

PING_FILES=(
  "${PM_ROOT}/plans/active/_agent_pings.md"
  "${PM_ROOT}/ikenna_orchestrator/_agent_pings.md"
  "${PM_ROOT}/harsh_orchestrator/_agent_pings.md"
)

# Match any of:
# 1. Explicit plans/* path (works for cross-file refs)
# 2. Bare workspace plan-slug convention `<slug>_YYYY_MM_DD.md` (used in relative-link refs
#    inside plans/active/_agent_pings.md where the file already lives in plans/active/)
# 3. Bare workspace plan-slug variants `<slug>_YYYY_MM_DD.plan.md`
# Workspace plan-naming SSOT: plans/PLAN_FORMAT.md.
PLAN_REF_PATTERN='plans/active/|plans/epics/|plans/audit/|plans/active/issues/|[a-z0-9_]+_20[0-9][0-9]_[01][0-9]_[0-3][0-9](\.plan)?\.md'

# Orphan tracking
ORPHAN_COUNT=0
ORPHAN_LIST=""

scan_ping_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "skip: ${file} does not exist"
    return
  fi
  # Walk entry-by-entry. Each entry starts with "## [" and ends at the next "## [" or EOF.
  # Use awk to extract blocks + check for plan refs.
  # HTML comment blocks (<!-- ... -->) are skipped entirely — archived pings inside those
  # blocks are intentionally not active and should not be flagged as orphans.
  awk -v pattern="${PLAN_REF_PATTERN}" -v fname="${file}" '
    BEGIN { block=""; header=""; in_block=0; in_html=0 }
    /^<!--.*-->/ { next }
    /^<!--/ { in_html=1; next }
    /^-->/ { in_html=0; next }
    in_html { next }
    /^## \[/ {
      if (in_block && block !~ pattern) {
        printf("ORPHAN | %s | %s\n", fname, header)
      }
      header=$0
      block=""
      in_block=1
      next
    }
    in_block { block = block "\n" $0 }
    END {
      if (in_block && block !~ pattern) {
        printf("ORPHAN | %s | %s\n", fname, header)
      }
    }
  ' "$file"
}

echo "── orphan-ping audit ${TIMESTAMP} ──"
ORPHANS=""
for f in "${PING_FILES[@]}"; do
  result="$(scan_ping_file "$f")"
  if [[ -n "$result" ]]; then
    ORPHANS+="${result}"$'\n'
    while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      echo "  $line"
      ORPHAN_COUNT=$((ORPHAN_COUNT + 1))
    done <<< "$result"
  fi
done

echo "── total orphans: ${ORPHAN_COUNT}"

if [[ ${ORPHAN_COUNT} -gt 0 ]]; then
  # Append a structured notification to BOTH orchestrator inboxes.
  for inbox in "${PM_ROOT}/ikenna_orchestrator/_agent_pings.md" "${PM_ROOT}/harsh_orchestrator/_agent_pings.md"; do
    [[ -f "$inbox" ]] || continue
    cat >> "$inbox" <<NOTIFY

---

## [orphan-ping-cron → ${inbox##*/}] ${TIMESTAMP} — ⚠️ ${ORPHAN_COUNT} orphan ping(s) detected (no plan/issue/audit reference)

Per CLAUDE.md HARD RULE "Every Active Ping Must Reference A Plan Item" (4h cron cadence):

\`\`\`
${ORPHANS}
\`\`\`

**Action required**: the agent who posted each orphan ping must either:
1. **File a plan** in \`plans/active/<slug>_$(date -u +%Y_%m_%d).md\` (or extend an existing plan in \`plans/active/issues/\` /
   \`plans/epics/\` / \`plans/audit/\`) describing the work the ping references, AND
2. **Edit the orphan ping** to add the new plan path inline,
   OR
3. **Remove the ping** if it's resolved / no longer actionable.

Re-run \`bash scripts/agents/audit_ping_orphans.sh\` until orphan count == 0.

Audit-script SSOT: \`scripts/agents/audit_ping_orphans.sh\`. Cron stack: local crontab on
Ikenna's machine (every 4h) + AWS agent-orchestrator EventBridge (every 4h offset by 2h
so the two passes don't collide). Reference: \`plans/active/mtds_mdps_master.md\`
Phase -1 (workspace-discipline prereq).
NOTIFY
  done
  exit 1
fi

exit 0
