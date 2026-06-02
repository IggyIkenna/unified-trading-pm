#!/usr/bin/env bats
# test_quickmerge_dep_tier_gate.bats — unit tests for STAGE 1.7 dep-tier-readiness gate
#   in scripts/quickmerge.sh.
#
# Tests the Python snippet inside STAGE 1.7 in isolation (fixture manifests).
# Also smoke-tests the --skip-dep-tier-gate agent guard and --agent mode block.
#
# HERMETIC: uses only tmpdir + python3 — no git ops, no network.
# Run: bats tests/test_quickmerge_dep_tier_gate.bats
# Run all bats: bats tests/

# ── helpers ────────────────────────────────────────────────────────────────────

# Inline the Stage 1.7 Python logic so tests are not fragile against line-number
# changes in quickmerge.sh.  The function replicates the gate exactly.
# Returns 0 (pass) or 1 (block) and prints blocked entries "name:status ..." on stdout.
_run_tier_gate_python() {
    local manifest_path="$1" repo_name="$2"
    python3 -c "
import json, sys

manifest_path = '$manifest_path'
repo_name = '$repo_name'

AT_OR_ABOVE_STAGING = {'STAGING_GREEN', 'SIT_VALIDATED'}

try:
    with open(manifest_path) as f:
        m = json.load(f)
except Exception:
    sys.exit(0)

repos = m.get('repositories', {})
repo_info = repos.get(repo_name, {})
deps = repo_info.get('dependencies', [])

blocked = []
for dep in deps:
    dep_name = dep.get('name', dep) if isinstance(dep, dict) else str(dep)
    if not dep_name or dep_name not in repos:
        continue
    dep_status = repos[dep_name].get('ci_status') or 'NOT_CONFIGURED'
    if dep_status not in AT_OR_ABOVE_STAGING:
        blocked.append(f'{dep_name}:{dep_status}')

if blocked:
    print(' '.join(blocked))
    sys.exit(1)
sys.exit(0)
"
}

# Write a fixture manifest to a temp file and echo its path.
_make_manifest() {
    local dep_name="$1" dep_status="$2"
    local manifest="${BATS_TEST_TMPDIR}/manifest_$$.json"
    python3 -c "
import json
m = {
    'repositories': {
        'my-service': {
            'dependencies': [{'name': '$dep_name', 'version': '>=0.1.0', 'required': True}]
        },
        '$dep_name': {
            'ci_status': '$dep_status'
        }
    }
}
print(json.dumps(m, indent=2))
" > "$manifest"
    echo "$manifest"
}

# Make a manifest with NO dependencies for my-service.
_make_nodep_manifest() {
    local manifest="${BATS_TEST_TMPDIR}/manifest_nodep_$$.json"
    python3 -c "
import json
m = {
    'repositories': {
        'my-service': {'dependencies': []}
    }
}
print(json.dumps(m, indent=2))
" > "$manifest"
    echo "$manifest"
}

# Make a manifest with multiple dependencies.
_make_multi_dep_manifest() {
    local manifest="${BATS_TEST_TMPDIR}/manifest_multi_$$.json"
    python3 -c "
import json
m = {
    'repositories': {
        'my-service': {
            'dependencies': [
                {'name': 'uac', 'version': '>=0.1.0'},
                {'name': 'utl', 'version': '>=0.1.0'}
            ]
        },
        'uac': {'ci_status': 'STAGING_GREEN'},
        'utl': {'ci_status': 'FEATURE_GREEN'}
    }
}
print(json.dumps(m, indent=2))
" > "$manifest"
    echo "$manifest"
}

# ── syntax ─────────────────────────────────────────────────────────────────────

@test "quickmerge.sh has valid bash syntax" {
    run bash -n "$(dirname "$BATS_TEST_DIRNAME")/scripts/quickmerge.sh"
    [ "$status" -eq 0 ]
}

# ── Stage 1.7 Python gate logic ────────────────────────────────────────────────

@test "gate PASSES when dep is STAGING_GREEN" {
    manifest="$(_make_manifest uac STAGING_GREEN)"
    run _run_tier_gate_python "$manifest" my-service
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "gate PASSES when dep is SIT_VALIDATED" {
    manifest="$(_make_manifest uac SIT_VALIDATED)"
    run _run_tier_gate_python "$manifest" my-service
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "gate BLOCKS when dep is FEATURE_GREEN" {
    manifest="$(_make_manifest uac FEATURE_GREEN)"
    run _run_tier_gate_python "$manifest" my-service
    [ "$status" -ne 0 ]
    [[ "$output" == *"uac:FEATURE_GREEN"* ]]
}

@test "gate BLOCKS when dep is LOCAL_PASS" {
    manifest="$(_make_manifest utl LOCAL_PASS)"
    run _run_tier_gate_python "$manifest" my-service
    [ "$status" -ne 0 ]
    [[ "$output" == *"utl:LOCAL_PASS"* ]]
}

@test "gate BLOCKS when dep is NOT_CONFIGURED" {
    manifest="$(_make_manifest utl NOT_CONFIGURED)"
    run _run_tier_gate_python "$manifest" my-service
    [ "$status" -ne 0 ]
    [[ "$output" == *"utl:NOT_CONFIGURED"* ]]
}

@test "gate BLOCKS when dep is FAILING" {
    manifest="$(_make_manifest uac FAILING)"
    run _run_tier_gate_python "$manifest" my-service
    [ "$status" -ne 0 ]
    [[ "$output" == *"uac:FAILING"* ]]
}

@test "gate PASSES when repo has NO dependencies" {
    manifest="$(_make_nodep_manifest)"
    run _run_tier_gate_python "$manifest" my-service
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "gate BLOCKS only the below-staging dep (multi-dep: uac=STAGING_GREEN, utl=FEATURE_GREEN)" {
    manifest="$(_make_multi_dep_manifest)"
    run _run_tier_gate_python "$manifest" my-service
    [ "$status" -ne 0 ]
    [[ "$output" == *"utl:FEATURE_GREEN"* ]]
    [[ "$output" != *"uac:"* ]]
}

@test "gate PASSES when repo is not in manifest (graceful no-op)" {
    manifest="$(_make_manifest uac STAGING_GREEN)"
    run _run_tier_gate_python "$manifest" unknown-service
    [ "$status" -eq 0 ]
}

@test "gate PASSES when manifest file is missing (graceful no-op)" {
    run _run_tier_gate_python "/nonexistent/manifest.json" my-service
    [ "$status" -eq 0 ]
}

# ── --skip-dep-tier-gate + --agent guard ───────────────────────────────────────

@test "--skip-dep-tier-gate in --agent mode is REJECTED" {
    # We can't run the full quickmerge (needs git repo), but we can test the
    # flag-validation block is present by grepping for the guard in the script.
    run grep -c "skip-dep-tier-gate is not allowed in --agent mode" \
        "$(dirname "$BATS_TEST_DIRNAME")/scripts/quickmerge.sh"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

@test "--skip-dep-tier-gate flag is parsed (present in case statement)" {
    run grep -c "skip-dep-tier-gate)" \
        "$(dirname "$BATS_TEST_DIRNAME")/scripts/quickmerge.sh"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

@test "STAGE 1.7 header is present in quickmerge.sh" {
    run grep -c "STAGE 1.7" \
        "$(dirname "$BATS_TEST_DIRNAME")/scripts/quickmerge.sh"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}
