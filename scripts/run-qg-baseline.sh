#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Run quality gates on all repos with quality-gates.sh and update workspace-manifest.json
# Usage: bash unified-trading-pm/scripts/run-qg-baseline.sh [--dry-run]
# Requires: workspace root, .venv-workspace or repo .venv

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
MANIFEST="$WS_ROOT/unified-trading-pm/workspace-manifest.json"

cd "$WS_ROOT"
[ -f .venv-workspace/bin/activate ] && source .venv-workspace/bin/activate || true

for d in */; do
  [ "$d" = "archive/" ] && continue
  [ ! -f "${d}scripts/quality-gates.sh" ] && continue
  name="${d%/}"
  echo -n "QG $name... "
  if bash "${d}scripts/quality-gates.sh" --no-fix --quick &>/dev/null; then
    echo "PASS"
    python3 -c "
import json
with open('$MANIFEST') as f: m=json.load(f)
if '$name' in m.get('repositories',{}):
  m['repositories']['$name']['ci_status']='PASSING'
# canonical manifest form (see check_workspace_manifest_canonical.py)
with open('$MANIFEST','w') as f: json.dump(m,f,indent=2,ensure_ascii=False); f.write('\n')
" 2>/dev/null || true
  else
    echo "FAIL"
    python3 -c "
import json
with open('$MANIFEST') as f: m=json.load(f)
if '$name' in m.get('repositories',{}):
  m['repositories']['$name']['ci_status']='FAILING'
# canonical manifest form (see check_workspace_manifest_canonical.py)
with open('$MANIFEST','w') as f: json.dump(m,f,indent=2,ensure_ascii=False); f.write('\n')
" 2>/dev/null || true
  fi
done
echo "Done. Manifest updated."
