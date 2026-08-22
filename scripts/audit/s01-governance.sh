#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# §1 — Workspace Governance
# Checks: repo count, DAG validity, required manifest fields, semver_rules_ref presence.
# Usage: bash unified-trading-pm/scripts/audit/s01-governance.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
source "$SCRIPT_DIR/lib.sh"
cd "$WORKSPACE_ROOT"

echo "=== §1 Workspace Governance ==="

MANIFEST="unified-trading-pm/workspace-manifest.json"

# Repo count
repo_count=$(python3 -c "import json; m=json.load(open('$MANIFEST')); print(len(m['repos']))")
if [ "$repo_count" -ge 65 ]; then
  emit "§1" "repo count ≥65" "PASS" "$repo_count repos registered"
else
  emit "§1" "repo count ≥65" "FAIL" "only $repo_count repos — expected 65+"
fi

# DAG acyclic
if python3 unified-trading-pm/scripts/validate-dag.py > /dev/null 2>&1; then
  emit "§1" "DAG acyclic (validate-dag.py exits 0)" "PASS" "none"
else
  emit "§1" "DAG acyclic (validate-dag.py exits 0)" "FAIL" "cycle detected — run validate-dag.py for details"
fi

# Required fields on every repo entry
missing_fields=$(python3 - <<'PYEOF'
import json, sys
m = json.load(open("unified-trading-pm/workspace-manifest.json"))
required = ["name","arch_tier","ci_status","git_url","dependencies"]
hits = []
for r in m["repos"]:
    missing = [f for f in required if f not in r]
    if missing:
        hits.append(f"{r.get('name','?')}: missing {missing}")
print("\n".join(hits))
PYEOF
)
pass_if_empty "§1" "all repos have required manifest fields" "$missing_fields"

# semver_rules_ref on every repo
missing_semver=$(python3 - <<'PYEOF'
import json
m = json.load(open("unified-trading-pm/workspace-manifest.json"))
hits = [r.get("name","?") for r in m["repos"] if "semver_rules_ref" not in r]
print("\n".join(hits))
PYEOF
)
if [ -z "$missing_semver" ]; then
  emit "§1" "semver_rules_ref on every repo" "PASS" "none"
else
  count=$(echo "$missing_semver" | wc -l | tr -d ' ')
  emit "§1" "semver_rules_ref on every repo" "WARN" "$count repos missing it — first: $(echo "$missing_semver" | head -1)"
fi

audit_summary
