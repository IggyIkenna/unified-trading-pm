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
# ---------------------------------------------------------------------------
# Instrument snapshot from GCS (full universe for UI mock realism)
# ---------------------------------------------------------------------------
echo ""
echo "=== Generating Instrument Snapshot ==="
python "$SCRIPT_DIR/generate_instrument_snapshot.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi" \
    --date "${INSTRUMENT_SNAPSHOT_DATE:-2026-03-27}"

# ---------------------------------------------------------------------------
# Type usage audit (dead type detection)
# ---------------------------------------------------------------------------
echo ""
echo "=== Running Type Usage Audit ==="
python "$SCRIPT_DIR/audit_type_usage.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"

# ---------------------------------------------------------------------------
# Dead code path audit (orphan modules in services)
# ---------------------------------------------------------------------------
echo ""
echo "=== Running Dead Code Path Audit ==="
python "$SCRIPT_DIR/audit_dead_code.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"

# ---------------------------------------------------------------------------
# API/UI coverage audit (endpoints exposed vs consumed)
# ---------------------------------------------------------------------------
echo ""
echo "=== Running API/UI Coverage Audit ==="
python "$SCRIPT_DIR/audit_api_ui_coverage.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"

# ---------------------------------------------------------------------------
# Capability manifest (typed graph over archetypes/venues/sources/risk/gaps)
# Deterministic (run twice = byte-identical). Service-resident registries are
# imported in each service's own .venv subprocess; unimportable sources emit
# typed gap edges so the manifest always generates.
# ---------------------------------------------------------------------------
echo ""
echo "=== Generating Capability Manifest ==="
python "$SCRIPT_DIR/generate_capability_manifest.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"

# ---------------------------------------------------------------------------
# Exhaustive verdict matrix (Phase 6A): archetype x venue x instrument_type x
# (instruction_action x algo) -> available | blocked | not_registered.  Appends
# its count summary to capability-orphan-report.txt (run AFTER the manifest so the
# orphan report exists).  Deterministic (run twice = byte-identical).
# ---------------------------------------------------------------------------
echo ""
echo "=== Generating Capability Verdict Matrix (exhaustive) ==="
python "$SCRIPT_DIR/generate_capability_verdict_matrix.py" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"

# ---------------------------------------------------------------------------
# Capability changelog (Wave-2 #5): diff the manifest vs the committed
# edge-status baseline -> openapi/capability-changelog.md ("what the system
# learned to do" + regressions).  Does NOT --update-baseline (that is a
# deliberate, reviewed action); the regression GATE
# (scripts/quality_gates/check_capability_regression.py) reads the same baseline.
# Deterministic (run twice = byte-identical).
# ---------------------------------------------------------------------------
echo ""
echo "=== Generating Capability Changelog (vs baseline) ==="
python "$SCRIPT_DIR/generate_capability_changelog.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"

# ---------------------------------------------------------------------------
# Capability unlock report (Wave-2 #1): for every BLOCKED edge, the minimal
# unlock set (unlock_distance + typed missing pieces) -> the demand-weighted
# gap report (closest-to-available first = highest-leverage roadmap items).
# Reads the manifest JSON (decoupled from the registry walk) -> deterministic
# (run twice = byte-identical).  --emit-todos appends the N closest-to-unlock
# roadmap todos to the gap tracker (dedup-idempotent) — NOT run in the suite by
# default (the plan-flip / tracker append is a deliberate action).
# ---------------------------------------------------------------------------
echo ""
echo "=== Generating Capability Unlock Report (minimal unlock sets) ==="
python "$SCRIPT_DIR/generate_capability_unlock_report.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi"

# ---------------------------------------------------------------------------
# Strategy prospectus (per-archetype markdown docs: 7 sections, machine+codex)
# Deterministic (run twice = byte-identical).  Output: UAC openapi/prospectus/
# ---------------------------------------------------------------------------
echo ""
echo "=== Generating Strategy Prospectus Docs ==="
python "$SCRIPT_DIR/generate_strategy_prospectus.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi/prospectus"

# ---------------------------------------------------------------------------
# Two-sided audit: StrategyArchetype enum vs codex archetype docs
# Outputs: openapi/prospectus/prospectus-codex-audit.md
#          Appends to plans/active/issues/ (findings + gap tracker)
# ---------------------------------------------------------------------------
echo ""
echo "=== Running Prospectus vs Codex Audit ==="
python "$SCRIPT_DIR/audit_prospectus_vs_codex.py" \
    --workspace-root "$WORKSPACE_ROOT" \
    --output-dir "$WORKSPACE_ROOT/unified-api-contracts/openapi/prospectus"

# ---------------------------------------------------------------------------
# Sync to UI repos (if present as sibling directories)
# ---------------------------------------------------------------------------
echo ""
echo "=== Syncing to UI repos ==="

OUTPUT_DIR="$WORKSPACE_ROOT/unified-api-contracts/openapi"
SYNCED=0

for UI_REPO in unified-trading-system-ui unified-trading-system-ui\ copy; do
    UI_DIR="$WORKSPACE_ROOT/$UI_REPO"
    REGISTRY_DIR="$UI_DIR/lib/registry"

    if [[ -d "$REGISTRY_DIR" ]]; then
        cp "$OUTPUT_DIR/unified-trading-system.openapi.json" "$REGISTRY_DIR/openapi.json"
        cp "$OUTPUT_DIR/unified-trading-system.openapi.yaml" "$REGISTRY_DIR/openapi.yaml"
        [[ -f "$OUTPUT_DIR/ui-reference-data.json" ]] && cp "$OUTPUT_DIR/ui-reference-data.json" "$REGISTRY_DIR/ui-reference-data.json"
        [[ -f "$OUTPUT_DIR/instruments-snapshot.json" ]] && cp "$OUTPUT_DIR/instruments-snapshot.json" "$REGISTRY_DIR/instruments-snapshot.json"
        [[ -f "$OUTPUT_DIR/config-registry.json" ]] && cp "$OUTPUT_DIR/config-registry.json" "$REGISTRY_DIR/config-registry.json"
        [[ -f "$OUTPUT_DIR/system-topology.json" ]] && cp "$OUTPUT_DIR/system-topology.json" "$REGISTRY_DIR/system-topology.json"
        [[ -f "$OUTPUT_DIR/capability-manifest.json" ]] && cp "$OUTPUT_DIR/capability-manifest.json" "$REGISTRY_DIR/capability-manifest.json"
        [[ -f "$OUTPUT_DIR/capability-verdict-matrix.json" ]] && cp "$OUTPUT_DIR/capability-verdict-matrix.json" "$REGISTRY_DIR/capability-verdict-matrix.json"
        echo "  Synced spec → $UI_REPO/lib/registry/"

        # Deduplicate operationIds (multiple services share /health and /readiness)
        DEDUPE_SCRIPT="$UI_DIR/scripts/dedupe-openapi-operation-ids.py"
        if [[ -f "$DEDUPE_SCRIPT" ]]; then
            python "$DEDUPE_SCRIPT" "$REGISTRY_DIR/openapi.json" --in-place
        fi

        # Regenerate TypeScript types if npx is available
        TYPES_FILE="$UI_DIR/lib/types/api-generated.ts"
        if [[ -f "$TYPES_FILE" ]] && command -v npx &>/dev/null; then
            (cd "$UI_DIR" && npx --yes openapi-typescript lib/registry/openapi.json --output lib/types/api-generated.ts 2>/dev/null) \
                && echo "  Regenerated TypeScript types → $UI_REPO/lib/types/api-generated.ts" \
                || echo "  WARNING: TypeScript type generation failed (run manually: cd $UI_REPO && npx openapi-typescript lib/registry/openapi.json --output lib/types/api-generated.ts)"
        fi
        SYNCED=$((SYNCED + 1))
    fi
done

if [[ $SYNCED -eq 0 ]]; then
    echo "  No UI repos found — skipping sync (expected: unified-trading-system-ui as sibling)"
fi

echo "=== All Done ==="
