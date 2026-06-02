#!/usr/bin/env bash
# Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-service.sh
SERVICE_NAME="unified-trading-pm"
SOURCE_DIR="scripts"
# PM is a docs+plans+scripts repo (not a service). Coverage gate disabled —
# scripts/ is operational tooling, not application code; aligns with
# pyproject.toml `fail_under = 0` deviation already documented there.
MIN_COVERAGE=0
RUN_INTEGRATION=true
PYTEST_WORKERS=${PYTEST_WORKERS:-}  # default: max(1, cpu_count//4) computed by base script
LOCAL_DEPS=("unified-api-contracts" "unified-trading-library")
MAX_DURATION=600  # PM: 5 min for local gates + ~5 min for act simulation (--act flag)
PYRIGHT_TIMEOUT=240  # PM scripts dir is larger — give basedpyright extra time on slow CI runners
# basedpyright ratchet baseline (2026-06-01): PM scripts/ has 1511 historic
# typing errors that aren't worth chasing on a docs-mostly repo, but future
# commits MUST NOT regress. Ratchet down opportunistically as files are touched.
BASEDPYRIGHT_MAX_ERRORS=1511
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
    "!**/validate-manifest-dag.py"
    "!**/regenerate_active_plan_inventory.py"
    "!**/populate_epic_bodies_2026_05_21.py"
    "!**/check_architectural_ratchets.py"
    "!**/detect_template_drift.py"
    "!**/test_detect_template_drift.py"
    "!**/check_coverage_targets.py"
    "!**/gcs_migration_bundle_2026_05_08.py"
    # JSON/YAML parse-default tooling (.get("k","") on parsed dicts — not an os.getenv anti-pattern)
    "!**/generate-cicd-diagram.py"
    "!**/audit_model_tier.py"
    "!**/invalidate-ci-status.py"
    "!**/gcs_bucket_stats.py"
    "!**/check_workspace_code_workspace_drift.py"
    # STAGE 1.8 dep-order gate: parses workspace-manifest.json dicts with safe
    # .get("name","") defaults — same manifest-parse pattern as the entries above.
    "!**/tier_c_promotion_gate.py"
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
    "!**/regen_vm_registry.py"
    "!**/generate-derived-manifest.py"
    "!**/check_banned_placeholder_methods.py"
    "!**/verify_env_tiered_buckets_provisioned.py"
    "!**/detect_template_drift.py"
    "!**/profile_qg_steps.py"
    "!**/audit_workspace_constraints_drift.py"
    "!**/check_coverage_targets.py"
    "!**/check_pipeline_mode_explicit_at_record_calls.py"
    "!**/regenerate_active_plan_inventory.py"
    "!**/populate_epic_bodies_2026_05_21.py"
    "!**/check_architectural_ratchets.py"
    "!**/gcs_migration_bundle_2026_05_08.py"
    "!**/check_workspace_code_workspace_drift.py"
    # STAGE 1.8 dep-order gate: .get("repositories",{}) / .get("dependencies",[])
    # are safe manifest-parse defaults — same pattern as the entries above.
    "!**/tier_c_promotion_gate.py"
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
    "!**/verify_env_tiered_buckets_provisioned.py"
    "!**/coverage_snapshot_to_parquet.py"
    "!**/snapshot_to_parquet.py"
    "!**/qg_audit.py"
    "!**/verify_flat_to_env_tiered_drift.py"
    "!**/generate_instrument_snapshot.py"
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
    "!**/prune_state_db_zombies.py"
    "!**/quality_gates/**"
    "!**/migration/**"
    "!**/qg/**"
    "!**/plans/**"
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
    "**/reap_stale_blockers.py"
    "**/gcs_migration_bundle_2026_05_08.py"
    "**/verify_env_tiered_buckets_provisioned.py"
    "**/pin_branch_protection_rulesets.py"
    "**/check_emission_policy_paired_callsites.py"
    "**/qg_audit.py"
)
DEEP_IMPORT_EXCLUDE_GLOBS=(
    "!**/check_data_completeness.py"
    "!**/test_prediction_pipeline_e2e.py"
    "!**/smoke-test-dev.py"
    "!**/check_env_canon.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate-strategy-instances-fixture.py"
    "!**/gcs_migration_bundle_2026_05_08.py"
    "!**/test_check_removed_symbols.py"
    "!**/test_check_canonical_futures_construction.py"
)
# STEP 5.63 — run_lifecycle pairing exclusions for setup_events() entry-points.
# PM scripts are operational CLI tools / diagnostics, not long-lived services.
# smoke-test-dev intentionally exercises setup_events() STANDALONE as Check 6;
# check_data_completeness is a short-lived diagnostic that emits its own report.
LIFECYCLE_EXCLUDE_GLOBS=(
    "!**/smoke-test-dev.py"
    "!**/check_data_completeness.py"
)

# Exclude diagram generator from basedpyright/codex checks (uses stdlib only,
# no project deps — type-checking it would require installing graphviz stubs)
PYRIGHT_EXCLUDE_GLOBS=("!**/generate-cicd-diagram.py")
EMPTY_STR_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py" "!**/invalidate-ci-status.py")
EMPTY_DICT_LIST_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py" "!**/invalidate-ci-status.py")
IMPORT_INSIDE_EXCLUDE_GLOBS+=("!**/generate-cicd-diagram.py")
BE_EXCLUDE_GLOBS+=("**/generate-cicd-diagram.py")

# requests CVE-2026-25645: no fix version available yet (fix in requests>=2.33.0, not released)
# urllib3 PYSEC-2026-141/142: fix in urllib3>=2.7.0 (transitive dep, not yet updated upstream)
PIP_AUDIT_EXTRA_ARGS="--ignore-vuln CVE-2026-25645 --ignore-vuln CVE-2026-34515 --ignore-vuln CVE-2026-34513 --ignore-vuln CVE-2026-34516 --ignore-vuln CVE-2026-34517 --ignore-vuln CVE-2026-34519 --ignore-vuln CVE-2026-34518 --ignore-vuln CVE-2026-34520 --ignore-vuln CVE-2026-34525 --ignore-vuln CVE-2026-22815 --ignore-vuln CVE-2026-34514 --ignore-vuln CVE-2026-4539 --ignore-vuln PYSEC-2026-141 --ignore-vuln PYSEC-2026-142"
# sync-catalogue-yaml.py: B608 (SQL injection) is a false positive — bucket param comes from CLI arg, not user input
BANDIT_EXTRA_ARGS="--exclude scripts/catalogue/sync-catalogue-yaml.py"
# PM is not a service — ServiceBootstrap (5.61) and Health API (5.62) don't apply.
# Ratchet down as violations are fixed.
CODEX_MAX_VIOLATIONS=0  # ratcheted 2026-06-01: 3 violations fixed (deep-import bulk-noqa across 8 files; empty-dict-list bulk-noqa across 38 files; hardcoded prod project-id excludes for verify_flat_to_env_tiered_drift + generate_instrument_snapshot)
# PM utility scripts legitimately use cloud SDKs, hardcoded project IDs (migration tools),
# and local BaseModel (checker/validator scripts).
SCHEMA_PROVENANCE_SKIP=true  # PM checker scripts define local BaseModel (not domain schemas)
MANIFEST_ALIGNMENT_SKIP=true  # PM is infrastructure (L0) — scripts import libs for validation, not as runtime deps
HARDCODED_PROJECT_EXCLUDE_GLOBS=(
    "!**/gcs_bucket_stats.py"
    "!**/test_prediction_pipeline_e2e.py"
    "!**/migrate_player_mappings_to_canonical.py"
    "!**/migrate_sports_gcs_to_hive.py"
    "!**/generate_instrument_snapshot.py"
    "!**/verify_env_tiered_buckets_provisioned.py"
    "!**/coverage_snapshot_to_parquet.py"
    "!**/snapshot_to_parquet.py"
    "!**/verify_flat_to_env_tiered_drift.py"
)
CLOUD_SDK_EXCLUDE_GLOBS=(
    "!**/migrate_sports_gcs_to_hive.py"
    "!**/sync-to-mock.py"
    "!**/verify_env_tiered_buckets_provisioned.py"
)
# PM is infrastructure (scripts); ServiceBootstrap + FastAPI health checks apply to deployable services only.
export SKIP_SERVICE_LIFECYCLE_STEPS=true
EMPTY_DICT_LIST_EXCLUDE_GLOBS+=(
    "!**/generate-cicd-diagram.py"
    "!**/invalidate-ci-status.py"
    "!**/gcs_bucket_stats.py"
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
DELETED_PLANS=$(git diff --cached --diff-filter=D --name-only -- 'plans/active/*.md' 2>/dev/null || :)
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

# ── Post-gates: Runbook Execution-Owner SSOT (HARD RULE) — baselined ratchet ──
# SSOT: CLAUDE.md § "Runbook Execution-Owner SSOT (HARD RULE)"
# Origin: plans/archive/issues/runbook_execution_governance_gaps_2026_05_08.md
# Codification: plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md
# Asserts every *runbook*.md (excluding archive) declares execution.{owner,cadence,verifier,last_executed}.
# Current baseline 9 — ratchet down by adding the 4-field block to existing runbooks one PR at a time.
RUNBOOK_OWNER_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_runbook_execution_owner.py"
if [ -f "$RUNBOOK_OWNER_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Runbook Execution-Owner SSOT check (ratchet mode)..."
    if python3 "$RUNBOOK_OWNER_CHECKER" --workspace-root "$WORKSPACE_ROOT"; then
        log_success "Runbook Execution-Owner SSOT check passed"
    else
        echo "❌ Runbook Execution-Owner SSOT regression — see CLAUDE.md § 'Runbook Execution-Owner SSOT (HARD RULE)'" >&2
        echo "   Either add execution.{owner,cadence,verifier,last_executed} to any new runbook, OR" >&2
        echo "   if intentional debt, re-baseline with: python3 ${RUNBOOK_OWNER_CHECKER} --workspace-root \$WORKSPACE_ROOT --baseline-write" >&2
        exit 1
    fi
fi

# ── Post-gates: Coverage targets enforcement (Phase 8.D of deployment_and_qg_strategy) — warn-only ──
# SSOT: scripts/quality_gates/coverage_targets.yaml + per-repo coverage_targets_local.yaml.
# Walks each repo's coverage.xml + computes aggregate per surface; compares vs target_pct.
# Currently warn-only — surface failures must be triaged per-repo before flipping to error mode.
# Per plan: ratchet starting 2026-05-18 (post-warn-only window).
COV_TARGETS_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_coverage_targets.py"
if [ -f "$COV_TARGETS_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Coverage-targets enforcement (warn-only)..."
    python3 "$COV_TARGETS_CHECKER" --workspace-root "$WORKSPACE_ROOT" --warn-only >/dev/null \
        && log_success "Coverage-targets check completed (warn-only)" \
        || log_warn "Coverage-targets checker errored (non-blocking)"
fi

# ── Post-gates: Architectural ratchets (Group C — ST-19 + PB-19 + UI-18) — baselined ratchet ──
# SSOT: governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group C.
# Rules in scripts/quality_gates/architectural_ratchets.yaml:
#   ST-19: no standalone backtest engine in strategy-service without V2EngineOrchestrator
#   PB-19: no mode-branching in PBMS engine/core
#   UI-18: no React/Next/Vite/Webpack package.json in any Python service repo
# Current baseline 0 — any new violation in any rule = regression.
ARCH_RATCHETS_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_architectural_ratchets.py"
if [ -f "$ARCH_RATCHETS_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Architectural ratchets check (ST-19 + PB-19 + UI-18)..."
    if python3 "$ARCH_RATCHETS_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "Architectural ratchets check passed (at-or-below baseline)"
    else
        echo "❌ Architectural ratchets regression — see governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group C" >&2
        echo "   Either fix the new violation OR re-baseline with --baseline-write after intentional debt" >&2
        exit 1
    fi
fi

# ── Post-gates: Plan discipline (Group A of governance_qg_automation_gaps) — baselined ratchet ──
# SSOT: governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group A (G-2 + G-5 + G-13).
# Three sub-rules: (a) DEFERRED-without-migration-banner, (b) filename-convention,
# (c) archived plans mentioning DEFERRED/post-cutover/out-of-scope must reference a successor.
# Current baseline 231 — ratchet down as plans get touched / archived clean.
PLAN_DISCIPLINE_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_plan_discipline.py"
if [ -f "$PLAN_DISCIPLINE_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Plan discipline check (ratchet mode)..."
    if python3 "$PLAN_DISCIPLINE_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "Plan discipline check passed (at-or-below baseline)"
    else
        echo "❌ Plan discipline regression — see governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group A" >&2
        echo "   Add migrated-to banner / fix filename / add successor ref. Re-baseline with --baseline-write after intentional debt." >&2
        exit 1
    fi
fi

# ── Post-gates: OpenAPI drift (Group D) — DISABLED 2026-05-16 per orchestrator audit finding ──
# The check compared full-file hashes of two structurally-different files:
#   unified-trading-api/openapi.json (61 paths — slim FastAPI facade)
#   unified-trading-system-ui/lib/registry/openapi.json (479 paths — aggregated UI mirror)
# Hash comparison will ALWAYS show drift by design. Need an aggregator-aware semantic.
# See plans/active/issues/openapi_mirror_drift_2026_05_16.md § INVESTIGATION for the path-count
# diagnosis. The check script stays as documentation; QG wiring removed until the canonical
# aggregator is identified (post-cutover scope).

# ── Post-gates: Codex doc freshness (Group B of governance_qg_automation_gaps) — baselined ratchet ──
# SSOT: CLAUDE.md § "Post-Plan-Phase Codex Audit (HARD RULE)"
# Origin: plans/active/governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group B
# Walks cutover-critical codex surfaces (codex/02-data, /04-architecture, /05-infrastructure,
# /11-project-management) and asserts every *.md has last_reviewed: + is ≤90 days old.
# Current baseline 188 — ratchet down by adding last_reviewed: YYYY-MM-DD to codex docs as touched.
CODEX_FRESHNESS_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_codex_doc_freshness.py"
if [ -f "$CODEX_FRESHNESS_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Codex doc freshness check (ratchet mode)..."
    if python3 "$CODEX_FRESHNESS_CHECKER" --workspace-root "$WORKSPACE_ROOT" --staleness-days 90 >/dev/null; then
        log_success "Codex doc freshness check passed (at-or-below baseline)"
    else
        echo "❌ Codex doc freshness regression — see CLAUDE.md § 'Post-Plan-Phase Codex Audit (HARD RULE)'" >&2
        echo "   Add 'last_reviewed: YYYY-MM-DD' to any new codex doc in 02-data/04-architecture/05-infrastructure/11-project-management, OR" >&2
        echo "   if intentional debt, re-baseline with: python3 ${CODEX_FRESHNESS_CHECKER} --workspace-root \$WORKSPACE_ROOT --baseline-write" >&2
        exit 1
    fi
fi

# ── Post-gates: VM registry validation — assigned_vm frontmatter must reference known vm-id ──
# SSOT: plans/epics/README.md § "VM topology (10 VMs serving 20 epics)" + orchestrator_vm_registry.yaml.
# Every epic + master plan declares assigned_vm: <vm-id> in frontmatter; vm-id MUST exist in
# orchestrator_vm_registry.yaml or dispatch breaks silently. Exit 0/1 from regen_vm_registry.py --check.
VM_REGISTRY_CHECKER="${REPO_ROOT}/scripts/orchestrator/regen_vm_registry.py"
if [ -f "$VM_REGISTRY_CHECKER" ]; then
    echo "Running VM registry validation (assigned_vm frontmatter)..."
    if python3 "$VM_REGISTRY_CHECKER" --check >/dev/null; then
        log_success "VM registry validation passed"
    else
        echo "❌ VM registry validation — assigned_vm references unknown vm-id" >&2
        echo "   See plans/epics/README.md § 'VM topology' for the canonical 10-VM registry" >&2
        echo "   Either fix the plan's assigned_vm OR add the vm to orchestrator_vm_registry.yaml" >&2
        exit 1
    fi
fi

# ── Post-gates: Credential-ask orphan scanner — baselined ratchet ──
# SSOT: CLAUDE.md § "External Data Is Always Available — Never Silently Defer Adapters" (HARD RULE).
# Every BLOCKED-CREDENTIALS plan item MUST cite an operator credential-ask ping (filed in
# <side>_orchestrator/pings/slot_<N>.md or _agent_pings.md). Orphan items block dispatch silently.
# Current baseline (2026-05-23): 7 — ratchet down as plans get cleaned up.
CRED_ASK_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_credential_ask_orphans.py"
if [ -f "$CRED_ASK_CHECKER" ]; then
    echo "Running credential-ask orphan scanner (ratchet mode)..."
    if python3 "$CRED_ASK_CHECKER" >/dev/null; then
        log_success "Credential-ask orphan scanner passed (at-or-below baseline)"
    else
        echo "❌ Credential-ask orphan regression — see CLAUDE.md § 'External Data Is Always Available'" >&2
        echo "   File the ping + reference it in the plan line, OR" >&2
        echo "   if intentional debt, re-baseline with: python3 ${CRED_ASK_CHECKER} --baseline-write" >&2
        exit 1
    fi
fi

# ── Post-gates: Workspace .code-workspace repo-list drift guard (HARD — blocking) ──
# SSOT: plans/active/workspace_config_drift_remediation_2026_06_01.md (Item 3) +
#       plans/active/issues/workspace_config_repo_list_drift_2026_06_01.md.
# Asserts the canonical multi-root .code-workspace folders[] == active+scaffolded repo set in
# workspace-manifest.json, and no listed path is a known archived/consolidated repo. Closes the
# Finding-3 gap where the workspace file drifted both ways (stale deleted repos still listed +
# real repos missing) until VS Code threw "<repo> does not appear to be a git repository".
WS_DRIFT_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_workspace_code_workspace_drift.py"
if [ -f "$WS_DRIFT_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running .code-workspace repo-list drift guard..."
    if python3 "$WS_DRIFT_CHECKER" --workspace-root "$WORKSPACE_ROOT"; then
        log_success ".code-workspace repo-list drift guard passed"
    else
        echo "❌ .code-workspace repo-list drift — see plans/active/workspace_config_drift_remediation_2026_06_01.md" >&2
        echo "   Sync cursor-configs/unified-trading-system-repos.code-workspace folders[] to the active repo set." >&2
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
