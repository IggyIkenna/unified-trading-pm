#!/usr/bin/env bash
# Generate unified OpenAPI spec from all FastAPI services.
#
# Usage:
#   bash unified-trading-pm/scripts/openapi/generate-unified-openapi.sh
#
# Requires: .venv-workspace with all service packages installed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "=== Unified OpenAPI Spec Generator ==="
echo "Workspace: $WORKSPACE_ROOT"

# Activate workspace venv
VENV="$WORKSPACE_ROOT/.venv-workspace"
if [[ ! -d "$VENV" ]]; then
    echo "ERROR: .venv-workspace not found at $VENV"
    exit 1
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
echo "Python: $(which python)"

# Build PYTHONPATH — add every service repo root so importlib can find them
PYTHONPATH_ADDITIONS=""
for repo_dir in "$WORKSPACE_ROOT"/*/; do
    # Only add dirs that contain a Python package (have a pyproject.toml)
    if [[ -f "$repo_dir/pyproject.toml" ]]; then
        PYTHONPATH_ADDITIONS="${PYTHONPATH_ADDITIONS:+$PYTHONPATH_ADDITIONS:}$repo_dir"
    fi
done

export PYTHONPATH="${PYTHONPATH_ADDITIONS}${PYTHONPATH:+:$PYTHONPATH}"

# Run the generator
python "$SCRIPT_DIR/generate_unified_spec.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"

# Basic validation
OUTPUT_JSON="$WORKSPACE_ROOT/unified-api-contracts/openapi/unified-trading-system.openapi.json"
if [[ -f "$OUTPUT_JSON" ]]; then
    echo ""
    echo "=== Validating JSON ==="
    python -c "
import json, sys
with open('$OUTPUT_JSON') as f:
    spec = json.load(f)
paths = len(spec.get('paths', {}))
schemas = len(spec.get('components', {}).get('schemas', {}))
print(f'Valid JSON: {paths} paths, {schemas} schemas')
if paths == 0:
    print('WARNING: No paths found in spec')
    sys.exit(1)
"
    echo "=== Done ==="
else
    echo "ERROR: Output JSON not found at $OUTPUT_JSON"
    exit 1
fi

# Run the UI reference data generator (registries, enums, config schemas)
echo ""
echo "=== Generating UI Reference Data ==="
python "$SCRIPT_DIR/generate_ui_reference_data.py" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"
# Run the config registry generator (per-service config classes)
echo ""
echo "=== Generating Config Registry ==="
python "$SCRIPT_DIR/generate_config_registry.py" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"
# Run the system topology generator (repos, deployment, strategies, data flows)
echo ""
echo "=== Generating System Topology ==="
python "$SCRIPT_DIR/generate_system_topology.py" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"
echo "=== All Done ==="
