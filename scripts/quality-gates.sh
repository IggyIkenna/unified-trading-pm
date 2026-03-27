#!/usr/bin/env bash
# Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-service.sh
SERVICE_NAME="unified-trading-pm"
SOURCE_DIR="scripts"
MIN_COVERAGE=70
RUN_INTEGRATION=true
PYTEST_WORKERS=${PYTEST_WORKERS:-}  # default: max(1, cpu_count//4) computed by base script
LOCAL_DEPS=("unified-events-interface" "unified-api-contracts")
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
)
GCP_PROJECT_ID_EXCLUDE_GLOBS=(
    "!**/rollout-quality-gates-ci-workflows.py"
    "!**/smoke-test-dev.py"
    "!**/check_env_canon.py"
    "!**/validate-build-auth.py"
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
)
BE_EXCLUDE_GLOBS=(
    "**/smoke-test-dev.py"
    "**/validate-buildspec.py"
    "**/validate-cloudbuild.py"
    "**/validate-internal-editable.py"
    "**/validate-manifest-dag.py"
    "**/rollout-quality-gates-ci-workflows.py"
    "**/check-integration-dep-coverage.py"
)
DEEP_IMPORT_EXCLUDE_GLOBS=("!**/check_data_completeness.py")

# Exclude diagram generator from basedpyright/codex checks (uses stdlib only,
# no project deps — type-checking it would require installing graphviz stubs)
PYRIGHT_EXCLUDE_GLOBS=("!**/generate-cicd-diagram.py")
EMPTY_STR_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py" "!**/invalidate-ci-status.py")
EMPTY_DICT_LIST_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py" "!**/invalidate-ci-status.py")
IMPORT_INSIDE_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py")
BE_EXCLUDE_GLOBS+=("**/generate-cicd-diagram.py")

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
