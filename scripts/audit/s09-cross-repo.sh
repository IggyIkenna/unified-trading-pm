#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §9 — Cross-Repo Alignment
# Checks: plans registered in SSOT-INDEX, manifest↔topology sync, orphan repos.
# Usage: bash unified-trading-pm/scripts/audit/s09-cross-repo.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §9 Cross-Repo Alignment ==="

# Plans in active/ registered in SSOT-INDEX
if python3 unified-trading-pm/scripts/validate-ssot-index.py > /tmp/ssot-check.txt 2>&1; then
  emit "§9" "all active plans in SSOT-INDEX (validate-ssot-index.py)" "PASS" "none"
else
  issues=$(grep -i "unregistered\|phantom\|missing" /tmp/ssot-check.txt | head -3 || cat /tmp/ssot-check.txt | head -3)
  emit "§9" "all active plans in SSOT-INDEX (validate-ssot-index.py)" "FAIL" \
    "$(echo "$issues" | tr '\n' '; ')"
fi

# Manifest↔topology sync
if python3 unified-trading-pm/scripts/validate-alignment.py > /tmp/align-check.txt 2>&1; then
  emit "§9" "manifest↔topology sync (validate-alignment.py)" "PASS" "none"
else
  issues=$(head -3 /tmp/align-check.txt | tr '\n' '; ')
  emit "§9" "manifest↔topology sync (validate-alignment.py)" "WARN" "$issues"
fi

# Count active plans
active_plan_count=$(find unified-trading-pm/plans/active -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
emit "§9" "active plan count" "PASS" "$active_plan_count active plans"

# Orphan repos: pyproject.toml exists but not in manifest
orphans=$(python3 - <<'PYEOF'
import json, pathlib
m = json.load(open("unified-trading-pm/workspace-manifest.json"))
registered = {r["name"] for r in m["repos"]}
ws_root = pathlib.Path(".")
orphans = []
for p in ws_root.glob("*/pyproject.toml"):
    repo = p.parent.name
    if repo not in registered and not repo.startswith(".") and repo != "unified-trading-pm":
        orphans.append(repo)
print("\n".join(sorted(orphans)))
PYEOF
)
if [ -z "$orphans" ]; then
  emit "§9" "no orphan repos (pyproject.toml not in manifest)" "PASS" "none"
else
  count=$(echo "$orphans" | wc -l | tr -d ' ')
  emit "§9" "no orphan repos (pyproject.toml not in manifest)" "WARN" \
    "$count orphans: $(echo "$orphans" | tr '\n' ', ' | sed 's/,$//')"
fi

audit_summary
