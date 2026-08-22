#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# stagger-dispatches.sh — Dispatches repository_dispatch events to repos
# in topologicalOrder (tier) order with configurable delay between tiers.
#
# Prevents GHA API rate-limit bursts by staggering dispatches across tiers.
# Reads tier order from workspace-manifest.json topologicalOrder (SSOT).
# L0 dispatched first, then sleep, L1, sleep, etc.
#
# Usage:
#   bash scripts/stagger-dispatches.sh <event_type> [payload_json]
#
# Environment variables:
#   GH_PAT             — GitHub PAT for cross-repo dispatch (REQUIRED)
#   OWNER              — GitHub org/user (default: read from manifest github_url)
#   MANIFEST_PATH      — Path to workspace-manifest.json (default: workspace-manifest.json)
#   TIER_DELAY_SECONDS — Delay between tier groups (default: 10)
#   DRY_RUN            — Set to "true" to print dispatches without sending (default: false)
#   REPO_FILTER        — Comma-separated list of repos to dispatch to (default: all)
#
# Exit codes:
#   0 — All dispatches succeeded (or dry run)
#   1 — Missing required args or env vars
#   2 — Some dispatches failed (partial success)

set -euo pipefail

EVENT_TYPE="${1:?Usage: stagger-dispatches.sh <event_type> [payload_json]}"
PAYLOAD="${2:-{\}}"
MANIFEST_PATH="${MANIFEST_PATH:-workspace-manifest.json}"
TIER_DELAY="${TIER_DELAY_SECONDS:-10}"
DRY_RUN="${DRY_RUN:-false}"
REPO_FILTER="${REPO_FILTER:-}"

if [ -z "${GH_PAT:-}" ] && [ "$DRY_RUN" != "true" ]; then
  echo "ERROR: GH_PAT is required for dispatches (set DRY_RUN=true for testing)" >&2
  exit 1
fi

if [ ! -f "$MANIFEST_PATH" ]; then
  echo "ERROR: Manifest not found at $MANIFEST_PATH" >&2
  exit 1
fi

# Extract repos grouped by level from topologicalOrder (SSOT)
# Output: JSON array of {level, repos} in topological order
TIER_GROUPS=$(python3 -c "
import json, sys

manifest_path = '${MANIFEST_PATH}'
repo_filter_raw = '${REPO_FILTER}'
repo_filter = set(repo_filter_raw.split(',')) if repo_filter_raw else None

with open(manifest_path) as f:
    m = json.load(f)

topo = m.get('topologicalOrder', {}).get('levels', [])
result = []
for entry in sorted(topo, key=lambda x: x.get('level', 999)):
    level = entry.get('level')
    if level is None or level < 0:
        continue
    repos_in_level = entry.get('repos', [])
    if repo_filter:
        repos_in_level = [r for r in repos_in_level if r in repo_filter]
    if repos_in_level:
        result.append({'level': level, 'repos': sorted(repos_in_level)})

json.dump(result, sys.stdout)
")

# Determine OWNER from first repo's github_url if not set
if [ -z "${OWNER:-}" ]; then
  OWNER=$(python3 -c "
import json
with open('${MANIFEST_PATH}') as f:
    m = json.load(f)
repos = m.get('repositories', {})
for name, data in repos.items():
    url = data.get('github_url', '')
    if url:
        # https://github.com/IggyIkenna/repo-name → IggyIkenna
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2:
            print(parts[-2])
            break
" 2>/dev/null || echo "")
  if [ -z "$OWNER" ]; then
    echo "ERROR: Could not determine OWNER from manifest. Set OWNER env var." >&2
    exit 1
  fi
fi

echo "=== Stagger Dispatches ==="
echo "Event: $EVENT_TYPE"
echo "Owner: $OWNER"
echo "Tier delay: ${TIER_DELAY}s"
echo "Dry run: $DRY_RUN"
echo ""

TOTAL_DISPATCHED=0
TOTAL_FAILED=0
FIRST_TIER=true

# Process each tier group
echo "$TIER_GROUPS" | python3 -c "
import json, sys
groups = json.load(sys.stdin)
for g in groups:
    print(f\"TIER:{g['level']}:{','.join(g['repos'])}\")
" | while IFS= read -r line; do
  LEVEL="${line#TIER:}"
  LEVEL_NUM="${LEVEL%%:*}"
  REPOS_CSV="${LEVEL#*:}"

  if [ "$FIRST_TIER" = "false" ] && [ "$DRY_RUN" != "true" ]; then
    echo "--- Sleeping ${TIER_DELAY}s before level $LEVEL_NUM ---"
    sleep "$TIER_DELAY"
  fi
  FIRST_TIER=false

  echo ">> level $LEVEL_NUM:"

  IFS=',' read -ra REPOS <<< "$REPOS_CSV"
  for REPO in "${REPOS[@]}"; do
    [ -z "$REPO" ] && continue

    if [ "$DRY_RUN" = "true" ]; then
      echo "  [DRY RUN] Would dispatch $EVENT_TYPE → $REPO"
      TOTAL_DISPATCHED=$((TOTAL_DISPATCHED + 1))
      continue
    fi

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
      -H "Authorization: Bearer $GH_PAT" \
      -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/$OWNER/$REPO/dispatches" \
      -d "{\"event_type\": \"$EVENT_TYPE\", \"client_payload\": $PAYLOAD}" \
      2>/dev/null || echo "000")

    if [ "$HTTP_STATUS" = "204" ]; then
      echo "  ✓ $REPO (HTTP $HTTP_STATUS)"
      TOTAL_DISPATCHED=$((TOTAL_DISPATCHED + 1))
    else
      echo "  ✗ $REPO (HTTP $HTTP_STATUS)" >&2
      TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
  done
done

echo ""
echo "=== Summary ==="
echo "Dispatched: $TOTAL_DISPATCHED"
echo "Failed: $TOTAL_FAILED"

if [ "$TOTAL_FAILED" -gt 0 ]; then
  exit 2
fi
