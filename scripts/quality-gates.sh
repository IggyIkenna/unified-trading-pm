#!/usr/bin/env bash
# Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-service.sh
SERVICE_NAME="unified-trading-pm"
SOURCE_DIR="scripts"
MIN_COVERAGE=70
RUN_INTEGRATION=true
PYTEST_WORKERS=${PYTEST_WORKERS:-}  # default: max(1, cpu_count//4) computed by base script
LOCAL_DEPS=("unified-api-contracts" "unified-trading-library")
MAX_DURATION=600  # PM: 5 min for local gates + ~5 min for act simulation (--act flag)
PYRIGHT_TIMEOUT=240  # PM scripts dir is larger — give basedpyright extra time on slow CI runners
WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"

# Optional codex exclusion arrays (base adds --glob; use "!**/file.py" to exclude)
# JSON-parsing scripts use .get("key", "") / .get("key", {}) / .get("key", []) as safe
# defaults when parsing manifest dicts — not os.getenv empty-fallback anti-pattern.
EMPTY_STR_EXCLUDE_GLOBS=(
    "!**/check-repo-readiness.py"
    "!**/smoke-test-dev.py"
    "!**/compute-epic-readiness.py"
    "!**/validate-internal-editable.py"
    "!**/network_evidence_parser.py"
    "!**/check_ui_api_flow_coverage.py"
    "!**/fixture_drift_checker.py"
    "!**/triad_assertion_checker.py"
    "!**/flow_coverage_scorecard.py"
    "!**/check-data-availability.py"
    "!**/check-strategy-maturity.py"
    "!**/reverse-dependency-lookup.py"
    "!**/generate_dependency_viz.py"
    "!**/auto-populate-tags.py"
    "!**/validate-strategy-manifest.py"
    "!**/migrate_player_mappings_to_canonical.py"
    "!**/generate_unified_spec.py"
    "!**/generate_config_registry.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate_instrument_snapshot.py"
    "!**/prune_removed_repositories.py"
    "!**/generate-strategy-instrument-matrix.py"
    "!**/_align_workspace_manifest.py"
    "!**/rollout-quality-gates-unified.py"
    "!**/sync_restriction_profiles_to_ui.py"
)
EMPTY_DICT_LIST_EXCLUDE_GLOBS=(
    "!**/check-repo-readiness.py"
    "!**/compute-epic-readiness.py"
    "!**/validate-internal-editable.py"
    "!**/rollout-ui-build-infra.py"
    "!**/github-integration/**"
    "!**/network_evidence_parser.py"
    "!**/check_ui_api_flow_coverage.py"
    "!**/fixture_drift_checker.py"
    "!**/triad_assertion_checker.py"
    "!**/flow_coverage_scorecard.py"
    "!**/check-data-availability.py"
    "!**/check-strategy-maturity.py"
    "!**/reverse-dependency-lookup.py"
    "!**/generate_dependency_viz.py"
    "!**/generate_strategy_manifest_dag.py"
    "!**/auto-populate-tags.py"
    "!**/check-strategy-instruments.py"
    "!**/validate-strategy-manifest.py"
    "!**/sync-catalogue-yaml.py"
    "!**/generate_system_topology.py"
    "!**/generate_unified_spec.py"
    "!**/test_prediction_pipeline_e2e.py"
    "!**/validate-import-deps.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate_instrument_snapshot.py"
    "!**/check-cross-plan-gates.py"
    "!**/check-integration-dep-coverage.py"
    "!**/check_schema_provenance.py"
    "!**/check_manifest_import_alignment.py"
    "!**/add-cloudbuild-deploy-via-dispatch.py"
    "!**/rollout-buildspec.py"
    "!**/rollout-cloudbuild.py"
    "!**/rollout-quality-gates-unified.py"
    "!**/sync_restriction_profiles_to_ui.py"
)
GCP_PROJECT_ID_EXCLUDE_GLOBS=(
    "!**/rollout-quality-gates-ci-workflows.py"
    "!**/rollout-quality-gates-unified.py"
    "!**/smoke-test-dev.py"
    "!**/check_env_canon.py"
    "!**/validate-build-auth.py"
    "!**/sync-catalogue-yaml.py"
    "!**/sync-to-mock.py"
    "!**/generate_unified_spec.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate_config_registry.py"
    "!**/test_prediction_pipeline_e2e.py"
    "!**/migrate_player_mappings_to_canonical.py"
    "!**/migrate_sports_gcs_to_hive.py"
)
SETUP_NO_SINK_EXCLUDE_GLOBS=(
    "!**/smoke-test-dev.py"
    "!**/check_data_completeness.py"
)
IMPORT_INSIDE_EXCLUDE_GLOBS=(
    "!**/smoke-test-dev.py"
    "!**/github-integration/**"
    "!**/validate-buildspec.py"
    "!**/validate-cloudbuild.py"
    "!**/check-repo-readiness.py"
    "!**/rollout-quality-gates-ci-workflows.py"
    "!**/rollout-ui-build-infra.py"
    "!**/check_env_canon.py"
    "!**/rollout-cloudbuild.py"
    "!**/rollout-buildspec.py"
    "!**/flow_coverage_scorecard.py"
    "!**/synthetic_load_generator.py"
    "!**/test_prediction_pipeline_e2e.py"
    "!**/generate_unified_spec.py"
    "!**/sync-catalogue-yaml.py"
    "!**/sync-to-mock.py"
    "!**/validate-import-deps.py"
    "!**/migrate_sports_gcs_to_hive.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate_instrument_snapshot.py"
    "!**/generate-strategy-instances-fixture.py"
    "!**/audit_dead_code.py"
)
BE_EXCLUDE_GLOBS=(
    "**/smoke-test-dev.py"
    "**/validate-buildspec.py"
    "**/validate-cloudbuild.py"
    "**/validate-internal-editable.py"
    "**/validate-manifest-dag.py"
    "**/rollout-quality-gates-ci-workflows.py"
    "**/check-integration-dep-coverage.py"
    "**/generate_ui_reference_data.py"
    "**/generate_unified_spec.py"
    "**/migrate_sports_gcs_to_hive.py"
    "**/validate-import-deps.py"
    "**/audit_dead_code.py"
)
DEEP_IMPORT_EXCLUDE_GLOBS=(
    "!**/check_data_completeness.py"
    "!**/test_prediction_pipeline_e2e.py"
    "!**/smoke-test-dev.py"
    "!**/check_env_canon.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate-strategy-instances-fixture.py"
)

# Exclude diagram generator from basedpyright/codex checks (uses stdlib only,
# no project deps — type-checking it would require installing graphviz stubs)
PYRIGHT_EXCLUDE_GLOBS=("!**/generate-cicd-diagram.py")
EMPTY_STR_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py" "!**/invalidate-ci-status.py")
EMPTY_DICT_LIST_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py" "!**/invalidate-ci-status.py")
IMPORT_INSIDE_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py")
BE_EXCLUDE_GLOBS+=("**/generate-cicd-diagram.py")

# requests CVE-2026-25645: no fix version available yet (fix in requests>=2.33.0, not released)
PIP_AUDIT_EXTRA_ARGS="--ignore-vuln CVE-2026-25645 --ignore-vuln CVE-2026-34515 --ignore-vuln CVE-2026-34513 --ignore-vuln CVE-2026-34516 --ignore-vuln CVE-2026-34517 --ignore-vuln CVE-2026-34519 --ignore-vuln CVE-2026-34518 --ignore-vuln CVE-2026-34520 --ignore-vuln CVE-2026-34525 --ignore-vuln CVE-2026-22815 --ignore-vuln CVE-2026-34514 --ignore-vuln CVE-2026-4539"
# sync-catalogue-yaml.py: B608 (SQL injection) is a false positive — bucket param comes from CLI arg, not user input
BANDIT_EXTRA_ARGS="--exclude scripts/catalogue/sync-catalogue-yaml.py"
# PM is not a service — ServiceBootstrap (5.61) and Health API (5.62) don't apply.
# Ratchet down as violations are fixed.
CODEX_MAX_VIOLATIONS=2
# PM utility scripts legitimately use cloud SDKs, hardcoded project IDs (migration tools),
# and local BaseModel (checker/validator scripts).
SCHEMA_PROVENANCE_SKIP=true  # PM checker scripts define local BaseModel (not domain schemas)
MANIFEST_ALIGNMENT_SKIP=true  # PM is infrastructure (L0) — scripts import libs for validation, not as runtime deps
HARDCODED_PROJECT_EXCLUDE_GLOBS=(
    "!**/test_prediction_pipeline_e2e.py"
    "!**/migrate_player_mappings_to_canonical.py"
    "!**/migrate_sports_gcs_to_hive.py"
    "!**/generate_instrument_snapshot.py"
)
CLOUD_SDK_EXCLUDE_GLOBS=(
    "!**/migrate_sports_gcs_to_hive.py"
    "!**/sync-to-mock.py"
)
# PM is infrastructure (scripts); ServiceBootstrap + FastAPI health checks apply to deployable services only.
export SKIP_SERVICE_LIFECYCLE_STEPS=true
EMPTY_DICT_LIST_EXCLUDE_GLOBS+=(
    "!**/generate-cicd-diagram.py"
    "!**/invalidate-ci-status.py"
)
source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"

# ── Pre-commit gate: validate workspace-manifest.json (add-manifest-json-validation) ──
REPO_ROOT="$(git rev-parse --show-toplevel)"
MANIFEST="${REPO_ROOT}/workspace-manifest.json"
if [ -f "$MANIFEST" ]; then
    bash "${REPO_ROOT}/scripts/validate-manifest-json.sh" "$MANIFEST" \
        || { echo "❌ workspace-manifest.json validation failed — fix before committing" >&2; exit 1; }
fi

# ── Pre-commit gate: validate strategy-manifest.json ──────────────────────
STRATEGY_MANIFEST="${REPO_ROOT}/strategy-manifest.json"
STRATEGY_VALIDATOR="${REPO_ROOT}/scripts/validation/validate-strategy-manifest.py"
if [ -f "$STRATEGY_MANIFEST" ] && [ -f "$STRATEGY_VALIDATOR" ]; then
    echo "Validating strategy-manifest.json..."
    if python3 "$STRATEGY_VALIDATOR"; then
        log_success "Strategy manifest validation passed"
    else
        echo "❌ strategy-manifest.json validation failed — fix before committing" >&2
        exit 1
    fi
fi

# ── Locked plan deletion check ──────────────────────────────────────────
# Prevent agents from deleting locked plans without [unlock-plan] tag
DELETED_PLANS=$(git diff --cached --diff-filter=D --name-only -- 'plans/active/*.plan.md' 2>/dev/null || :)
if [ -n "$DELETED_PLANS" ]; then
    COMMIT_MSG=$(git log -1 --format=%B 2>/dev/null || :)
    for plan_file in $DELETED_PLANS; do
        # Check if the deleted plan had locked_by in its frontmatter
        # Read from the old version (before deletion)
        LOCKED_BY=$(git show "HEAD:$plan_file" 2>/dev/null | grep -oP '^\s*locked_by:\s*\K.*' | head -1 || :)
        if [ -n "$LOCKED_BY" ] && ! echo "$COMMIT_MSG" | grep -q '\[unlock-plan\]'; then
            echo "❌ BLOCKED: $plan_file is locked by '$LOCKED_BY'."
            echo "   To delete a locked plan, include [unlock-plan] in your commit message."
            echo "   This prevents agents from accidentally removing plans that are actively being implemented."
            exit 1
        fi
    done
fi

# ── Post-gates: codex scope-registry coverage (rule 11, G1.9) ─────────────
# SSOT: codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md
# Fails loud if any codex/**/*.md lacks `scope:` frontmatter or declares an
# invalid scope value.
SCOPE_CHECKER="${REPO_ROOT}/codex/14-playbooks/_tools/check-scope-coverage.sh"
if [ -f "$SCOPE_CHECKER" ]; then
    echo "Running codex scope-registry coverage (rule 11)..."
    if bash "$SCOPE_CHECKER"; then
        log_success "Codex scope coverage check passed"
    else
        echo "❌ codex scope coverage check failed — every codex/**/*.md must declare scope: [...] frontmatter" >&2
        echo "   See codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md for the rule." >&2
        exit 1
    fi
fi

# ── Post-gates: UI/API flow coverage checker (warning-only — non-blocking) ──
FLOW_CHECKER="${REPO_ROOT}/scripts/checkers/check_ui_api_flow_coverage.py"
if [ -f "$FLOW_CHECKER" ]; then
    echo "Running UI/API flow coverage checker (warning-only)..."
    if python3 "$FLOW_CHECKER" --workspace-root "$WORKSPACE_ROOT" --warning-only; then
        log_success "UI/API flow coverage check completed"
    else
        log_warn "UI/API flow coverage checker failed (non-blocking)"
    fi
fi

# ── Post-gates: regenerate CI/CD pipeline diagram (SSOT: cicd-pipeline-definition.yaml) ──
REPO_ROOT="$(git rev-parse --show-toplevel)"
DIAGRAM_YAML="${REPO_ROOT}/docs/repo-management/cicd-pipeline-definition.yaml"
DIAGRAM_SCRIPT="${REPO_ROOT}/scripts/generate-cicd-diagram.py"
if [ -f "${DIAGRAM_YAML}" ] && [ -f "${DIAGRAM_SCRIPT}" ]; then
    echo "Regenerating CI/CD pipeline diagram..."
    python3 "${DIAGRAM_SCRIPT}" || { echo "⚠ Diagram regeneration failed (non-blocking)" >&2; }
fi
