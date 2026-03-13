#!/usr/bin/env bash
# Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-service.sh
SERVICE_NAME="unified-trading-pm"
SOURCE_DIR="scripts"
MIN_COVERAGE=70
RUN_INTEGRATION=false
PYTEST_WORKERS=${PYTEST_WORKERS:-2}
LOCAL_DEPS=("unified-events-interface" "unified-internal-contracts")
MAX_DURATION=600  # PM: 5 min for local gates + ~5 min for act simulation (--act flag)
PYRIGHT_TIMEOUT=240  # PM scripts dir is larger — give basedpyright extra time on slow CI runners
WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"

# Optional codex exclusion arrays (base adds --glob; use "!**/file.py" to exclude)
EMPTY_STR_EXCLUDE_GLOBS=(
    "!**/check-repo-readiness.py"
    "!**/smoke-test-dev.py"
    "!**/compute-epic-readiness.py"
    "!**/validate-internal-editable.py"
)
EMPTY_DICT_LIST_EXCLUDE_GLOBS=(
    "!**/check-repo-readiness.py"
    "!**/compute-epic-readiness.py"
    "!**/validate-internal-editable.py"
    "!**/rollout-ui-build-infra.py"
    "!**/github-integration/**"
)
GCP_PROJECT_ID_EXCLUDE_GLOBS=(
    "!**/rollout-quality-gates-ci-workflows.py"
    "!**/smoke-test-dev.py"
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
)
BE_EXCLUDE_GLOBS=(
    "**/smoke-test-dev.py"
    "**/validate-buildspec.py"
    "**/validate-cloudbuild.py"
    "**/validate-internal-editable.py"
    "**/validate-manifest-dag.py"
    "**/rollout-quality-gates-ci-workflows.py"
)
DEEP_IMPORT_EXCLUDE_GLOBS=("!**/check_data_completeness.py")

# Exclude diagram generator from basedpyright/codex checks (uses stdlib only,
# no project deps — type-checking it would require installing graphviz stubs)
PYRIGHT_EXCLUDE_GLOBS=("!**/generate-cicd-diagram.py")
EMPTY_STR_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py")
EMPTY_DICT_LIST_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py")
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

# ── Post-gates: regenerate CI/CD pipeline diagram (SSOT: cicd-pipeline-definition.yaml) ──
REPO_ROOT="$(git rev-parse --show-toplevel)"
DIAGRAM_YAML="${REPO_ROOT}/docs/repo-management/cicd-pipeline-definition.yaml"
DIAGRAM_SCRIPT="${REPO_ROOT}/scripts/generate-cicd-diagram.py"
if [ -f "${DIAGRAM_YAML}" ] && [ -f "${DIAGRAM_SCRIPT}" ]; then
    echo "Regenerating CI/CD pipeline diagram..."
    python3 "${DIAGRAM_SCRIPT}" || { echo "⚠ Diagram regeneration failed (non-blocking)" >&2; }
fi
