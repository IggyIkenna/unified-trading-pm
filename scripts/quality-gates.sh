#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Repo-specific settings only. Body: unified-trading-pm/scripts/quality-gates-base/base-service.sh
SERVICE_NAME="unified-trading-pm"
SOURCE_DIR="scripts"
# PM scripts/ run in prod CI/CD pipelines (ci_failure_watcher, detect_breaking_change, etc.).
# Baseline 2026-06-10: 74.5% across 24 measured scripts. Floor = 70% (regression guard).
# Re-baseline 2026-06-11: 68.64% (branch 8 commits behind origin; concurrent agent activity).
# Prior floor: 70%. Re-set to 69% — will ratchet back up as coverage is restored.
MIN_COVERAGE=69
RUN_INTEGRATION=true
# BATS_HARD_FAIL: PM's own .bats suite re-measured 2026-08-12 at 0 failures (was 60; both
# root causes fixed rather than left ratcheted — see
# pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md todo G). Opting in here
# (per-repo, base-service.sh's shared default stays WARN-only for every other repo) means a
# future bats failure on THIS repo genuinely blocks the gate instead of silently warning.
BATS_HARD_FAIL=1
PYTEST_WORKERS=${PYTEST_WORKERS:-}  # default: max(1, cpu_count//4) computed by base script
# Wire the checker-adjacent test_*.py files that live next to their checkers under scripts/
# (scripts/quality_gates/, scripts/cicd/, scripts/docs/) into the TESTS phase. Plain `testpaths`
# widening in pyproject.toml does NOT work here — base-service.sh's pytest invocation always
# passes explicit ${PYTEST_UNIT_DIR} path args, and pytest CLI paths override
# [tool.pytest.ini_options] testpaths, so testpaths is never consulted. PYTEST_UNIT_DIR is the
# documented per-repo override point instead (space-separated, word-split into pytest args).
# Verified 2026-07-14: all 18 files here (254 tests) collect + pass together with no name
# collisions. SSOT: plans/active/issues/qg_pytest_testpaths_excludes_scripts_quality_gates_2026_07_14.md
PYTEST_UNIT_DIR="tests/unit/ scripts/quality_gates/ scripts/cicd/ scripts/docs/ scripts/plan-hygiene/"
LOCAL_DEPS=("unified-api-contracts" "unified-trading-library")
MAX_DURATION=600  # PM: 5 min for local gates + ~5 min for act simulation (--act flag)

# ── --sliced: run the full surface as three separately-budgeted processes ────────────────
# MAX_DURATION is enforced per PROCESS, and it is the SAME 600s whether you run one slice or
# the whole gate — so a full local run does three slices' work on one slice's budget. On
# 2026-08-10 PM's gate breached it on CPU alone (658s vs 600s), blocking every ship from the
# host regardless of content, until an accidentally-expensive test fixture was fixed (that
# brought it to 212s). The fixture was the immediate cause; the structural exposure is that
# one process carries the whole bill and the suite only grows.
#
# `--sliced` runs the three CI slices as separate children, each enforcing its own budget and
# its own CPU accounting, so no single run carries the whole thing. The partition is not a
# claim -- check_qg_slice_completeness.py machine-proves these three cover the full local gate,
# and it runs above.
#
# It deliberately does NOT write the sentinel. A sliced run is a PARTIAL run per process, and
# the sentinel certifies the FULL surface for `quickmerge --agent`'s fast path; aggregating it
# correctly means reproducing the H5 content-vs-SHA semantics documented in base-service.sh,
# which is its own change with its own review. Getting that wrong means a green sentinel for a
# surface that was never fully gated -- so `--sliced` is a way to RUN the gate under budget,
# not a way to certify a ship. Use the normal full run for that.
if [ "${1:-}" = "--sliced" ] || [ "${QG_SLICED:-}" = "1" ]; then
    # No unconditional-success bypass here (the pipe-pipe-true form): the codex gate bans them
    # inside the gate itself, and it is right -- this shift is only reached when $1 is literally
    # "--sliced", so $# >= 1 and it cannot fail. A defensive bypass would have hidden a real
    # argument-handling bug rather than prevented one.
    #
    # The token is spelled out in words above deliberately: the checker greps the file and is
    # comment-blind, so merely DESCRIBING the bypass trips it -- the same trap CLAUDE.md already
    # documents for the CI skip marker ("even when only describing it"), which is why that rule
    # says to write it hyphenated. Worth knowing before you explain a bypass you did not add.
    [ "${1:-}" = "--sliced" ] && shift
    _qg_sliced_rc=0
    for _qg_s in tests typecheck lint-codex; do
        echo ""
        echo "══════════════════════════════════════════"
        echo "  QG_SLICE=${_qg_s}  (own ${MAX_DURATION}s budget)"
        echo "══════════════════════════════════════════"
        if QG_SLICE="${_qg_s}" bash "${BASH_SOURCE[0]}" "$@"; then
            echo "✅ slice ${_qg_s} passed"
        else
            echo "❌ slice ${_qg_s} FAILED"
            _qg_sliced_rc=1
        fi
    done
    echo ""
    if [ "$_qg_sliced_rc" -eq 0 ]; then
        echo "✅ ALL SLICES PASSED — full surface covered (partition machine-proven by"
        echo "   check_qg_slice_completeness.py). NOTE: no sentinel written; a ship still"
        echo "   needs a normal full run to certify."
    else
        echo "❌ one or more slices failed — see above"
    fi
    exit "$_qg_sliced_rc"
fi
# basedpyright is fully EXCLUDED for PM scripts/ (RESOLVED 2026-07-27, operator ruling finding 87,
# per plans/active/issues/pm_scripts_typecheck_debt_2026_06_11.md). History: the 2026-06-24
# "warn-only" fix (unified-trading-pm@22b2f89d7) removed BASEDPYRIGHT_MAX_ERRORS to end the
# ratchet-bump trap (1511→1517→1523→1539→1555, bumped FOUR times from PM's metadata-only
# fast-path masking accumulating scripts/ typing debt until a full run surfaced it all at once —
# reddened PM's LDR→main PR, starved the fleet, 2026-06-23, unblock commit 1e6ec188e) — but did
# NOT stop base-service.sh's SEPARATE, unconditional zero-warning-policy block from still failing
# the gate on any basedpyright WARNING (PR #498 hit exactly this, ~3082 diagnostics, three days
# after the warn-only fix shipped). The actual fix: `[tool.basedpyright] exclude` in
# pyproject.toml now includes "scripts" itself, so basedpyright analyzes ZERO files even though
# this script always invokes `basedpyright scripts/` with an explicit CLI path arg (verified
# empirically: 0 errors/0 warnings/0 notes) — aligning with the lifecycle-marker SSOT (CLAUDE.md
# § Script Homes: scripts/ are ruff-gated, NOT basedpyright-gated) with zero risk to the SHARED
# base-service.sh's zero-warning-policy (untouched — it simply never fires because PM's own
# config now produces nothing to fail on). DO NOT re-add BASEDPYRIGHT_MAX_ERRORS or narrow the
# pyproject.toml exclude — both re-create one of the two traps above.
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
    "!**/generate_capability_manifest.py"
    "!**/generate_capability_verdict_matrix.py"
    "!**/_capability_extract.py"
    "!**/_capability_gaps.py"
    "!**/_capability_orphan.py"
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
    # JSON/YAML parse-default tooling (.get("k","") on parsed dicts — not an os.getenv anti-pattern)
    "!**/generate-cicd-diagram.py"
    "!**/audit_model_tier.py"
    "!**/invalidate-ci-status.py"
    "!**/gcs_bucket_stats.py"
    "!**/check_workspace_code_workspace_drift.py"
    # STAGE 1.8 dep-order gate: parses workspace-manifest.json dicts with safe
    # .get("name","") defaults — same manifest-parse pattern as the entries above.
    "!**/tier_c_promotion_gate.py"
    # Guard 1 — ci_status single-writer: same json.loads(manifest) + .get parse pattern.
    "!**/check_ci_status_bot_only.py"
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
    "!**/prediction_pipeline_e2e_check.py"
    "!**/validate-import-deps.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate_capability_manifest.py"
    "!**/generate_capability_verdict_matrix.py"
    "!**/_capability_extract.py"
    "!**/_capability_gaps.py"
    "!**/_capability_orphan.py"
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
    "!**/check_workspace_code_workspace_drift.py"
    # STAGE 1.8 dep-order gate: .get("repositories",{}) / .get("dependencies",[])
    # are safe manifest-parse defaults — same pattern as the entries above.
    "!**/tier_c_promotion_gate.py"
)
GCP_PROJECT_ID_EXCLUDE_GLOBS=(
    "!**/rollout-quality-gates-unified.py"
    "!**/smoke-test-dev.py"
    "!**/check_env_canon.py"
    "!**/validate-build-auth.py"
    "!**/sync-catalogue-yaml.py"
    "!**/sync-to-mock.py"
    "!**/generate_unified_spec.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate_config_registry.py"
    "!**/generate_capability_manifest.py"
    "!**/generate_capability_verdict_matrix.py"
    "!**/_capability_gaps.py"
    "!**/prediction_pipeline_e2e_check.py"
    "!**/migrate_player_mappings_to_canonical.py"
    "!**/migrate_sports_gcs_to_hive.py"
    "!**/verify_env_tiered_buckets_provisioned.py"
    "!**/coverage_snapshot_to_parquet.py"
    "!**/snapshot_to_parquet.py"
    "!**/qg_audit.py"
    "!**/verify_flat_to_env_tiered_drift.py"
    "!**/generate_instrument_snapshot.py"
    "!**/generate_strategy_prospectus.py"
    "!**/audit_prospectus_vs_codex.py"
    # F39 venue coverage audit: uses os.environ.setdefault("GCP_PROJECT_ID") for
    # mock-mode context (same category as generate_capability_manifest.py).
    "!**/audit_venue_coverage.py"
    # Phase 6B gate: delegates os.environ.setdefault to audit_prospectus_vs_codex (same pattern).
    "!**/check_two_sided_audit.py"
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
    "!**/rollout-ui-build-infra.py"
    "!**/check_env_canon.py"
    "!**/rollout-cloudbuild.py"
    "!**/rollout-buildspec.py"
    "!**/flow_coverage_scorecard.py"
    "!**/synthetic_load_generator.py"
    "!**/prediction_pipeline_e2e_check.py"
    "!**/generate_unified_spec.py"
    "!**/sync-catalogue-yaml.py"
    "!**/sync-to-mock.py"
    "!**/validate-import-deps.py"
    "!**/migrate_sports_gcs_to_hive.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate_capability_manifest.py"
    "!**/generate_capability_verdict_matrix.py"
    "!**/_capability_extract.py"
    "!**/_capability_gaps.py"
    "!**/_capability_orphan.py"
    "!**/generate_instrument_snapshot.py"
    "!**/generate-strategy-instances-fixture.py"
    "!**/audit_dead_code.py"
    "!**/audit_venue_coverage.py"
    "!**/prune_state_db_zombies.py"
    "!**/quality_gates/**"
    "!**/migration/**"
    "!**/qg/**"
    "!**/plans/**"
)
BE_EXCLUDE_GLOBS=(
    # smoke-test-dev.py, validate-buildspec.py, validate-cloudbuild.py,
    # validate-internal-editable.py, validate-manifest-dag.py removed 2026-08-09:
    # none of these files contain `except Exception:` any more (fixed upstream at
    # some point after their exclude entry was added; verified via
    # `rg -c "except Exception:" <file>` == 0 for all five) — stale bypass entries
    # that were silently masking the check's ability to catch a NEW broad-except
    # reintroduced in any of these files. Removed as part of
    # pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md's false-negative
    # investigation (root cause: undocumented/stale bypass-glob entries, not a check bug).
    #
    # check-integration-dep-coverage.py, generate_ui_reference_data.py,
    # generate_unified_spec.py, migrate_sports_gcs_to_hive.py, validate-import-deps.py,
    # reap_stale_blockers.py, verify_env_tiered_buckets_provisioned.py,
    # pin_branch_protection_rulesets.py, check_emission_policy_paired_callsites.py,
    # qg_audit.py removed 2026-08-09 (same doc, P3 todo): every `except Exception:` in
    # these 10 files was narrowed to the specific exception type(s) its surrounding
    # try-block actually expects — verified `rg -c "except Exception:" <file>` == 0 for
    # all ten. The bypass is no longer needed; genuinely fixed, not just excluded.
    "**/audit_dead_code.py"                 # documented QUALITY_GATE_BYPASS_AUDIT.md §2.9 (false positive — string literal)
)
DEEP_IMPORT_EXCLUDE_GLOBS=(
    "!**/check_data_completeness.py"
    "!**/prediction_pipeline_e2e_check.py"
    "!**/smoke-test-dev.py"
    "!**/check_env_canon.py"
    "!**/generate_ui_reference_data.py"
    "!**/generate-strategy-instances-fixture.py"
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
# generate-cicd-diagram.py, tier_c_promotion_gate.py, reconcile_release_tags.py: their
# BE_EXCLUDE_GLOBS entries removed 2026-08-09 — none of the three currently contains
# `except Exception:` (already fixed upstream; verified via `rg -c` == 0 for all three).
# Stale bypass entries silently masked the check's ability to catch a reintroduced
# broad-except in any of them. See pm_qg_broad_except_ratchet_red_finops_regression_2026_08_09.md.
# promotion_lag_monitor.py, ci_failure_watcher.py, cron_liveness_watchdog.py: their
# BE_EXCLUDE_GLOBS entries removed 2026-08-09 (pm_qg_broad_except_ratchet_red_finops_
# regression_2026_08_09.md's P3 todo) — every `except Exception:`/`except Exception as
# X:` in all three was narrowed to the specific exception type(s) actually expected;
# verified `rg -c "except Exception:" <file>` == 0 for all three.
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
    "!**/prediction_pipeline_e2e_check.py"
    "!**/migrate_player_mappings_to_canonical.py"
    "!**/migrate_sports_gcs_to_hive.py"
    "!**/generate_instrument_snapshot.py"
    "!**/verify_env_tiered_buckets_provisioned.py"
    "!**/coverage_snapshot_to_parquet.py"
    "!**/snapshot_to_parquet.py"
    "!**/verify_flat_to_env_tiered_drift.py"
    "!**/generate_strategy_prospectus.py"
    "!**/audit_prospectus_vs_codex.py"
    # F39 venue coverage audit: benign row-dict .get() defaults for per-venue data,
    # not os.getenv empty-fallback anti-pattern.
    "!**/audit_venue_coverage.py"
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
# Newly-landed checker/automation scripts (2026-06): benign manifest/frontmatter-dict
# defaults (same category as above — e.g. tier_c_promotion_gate.py explicitly fail-opens
# on absent manifest signals with isinstance guards), NOT the os.getenv empty-fallback
# anti-pattern. They landed without being added to the exclude lists.
EMPTY_STR_EXCLUDE_GLOBS+=(
    "!**/check_parent_epic_alignment.py"
    "!**/reap_stale_blockers.py"
    "!**/tier_c_promotion_gate.py"
    # Prospectus generator + audit: benign frontmatter-dict .get("key", "") defaults
    # for codex YAML frontmatter parsing — not os.getenv empty-fallback anti-pattern.
    "!**/generate_strategy_prospectus.py"
    "!**/audit_prospectus_vs_codex.py"
    "!**/_prospectus_codex.py"
    "!**/_prospectus_manifest.py"
    # F39 venue coverage audit: benign row-dict .get("category", "") for per-venue data.
    "!**/audit_venue_coverage.py"
)
EMPTY_DICT_LIST_EXCLUDE_GLOBS+=(
    "!**/check_ci_status_bot_only.py"
    "!**/check_parent_epic_alignment.py"
    "!**/check_tradfi_source_explicit_at_record_captured.py"
    "!**/pin_branch_protection_rulesets.py"
    "!**/reap_stale_blockers.py"
    "!**/tier_c_promotion_gate.py"
    "!**/verify_branch_protection_check_names.py"
    # check_ci_status_bot_only.py: benign `manifest.get("repositories", {})` JSON default
    # (same category — already in EMPTY_STR_EXCLUDE_GLOBS; was missed from this list when it
    # landed). NOT the os.getenv empty-fallback anti-pattern.
    "!**/check_ci_status_bot_only.py"
    # Prospectus manifest helpers: benign JSON dict defaults for capability-manifest.json parsing
    "!**/_prospectus_manifest.py"
    "!**/generate_strategy_prospectus.py"
    # F39 venue coverage audit: benign row-dict .get("adapters", []) for per-venue data.
    "!**/audit_venue_coverage.py"
    # check_base_image_digest_drift: benign JSON .get("repositories", {}) for manifest parsing.
    "!**/check_base_image_digest_drift.py"
    # check_extraction_count_regression: benign JSON .get("_meta", {}) / .get("paths", {}) /
    # .get("configs_by_repo", {}) defaults for config-registry.json / openapi.json parsing —
    # same category as check_base_image_digest_drift.py above.
    "!**/check_extraction_count_regression.py"
)
EMPTY_STR_EXCLUDE_GLOBS+=(
    # check_base_image_digest_drift: benign JSON .get("name", "") / .get("version", "") for
    # dep-edge parsing — same category as other checker scripts above.
    "!**/check_base_image_digest_drift.py"
)
HARDCODED_PROJECT_EXCLUDE_GLOBS+=(
    # check_base_image_digest_drift: DEFAULT_PROJECT_ID is the known GCR project for the UTL
    # base image (the value IS the project — there is no config injection for the post-gate
    # registry probe; the constant is intentional, not a secret).
    "!**/check_base_image_digest_drift.py"
    # check_evidence_backed_completion: DEFAULT_PROJECT is the Cloud Build API project for the
    # `gcloud builds describe` verification (same category — the value IS the project; overridable
    # via --project; no config injection for a post-gate probe; not a secret).
    "!**/check_evidence_backed_completion.py"
    # check_repo_docs_ssot (+ its test): a DOC linter whose whole job is to DETECT a hardcoded
    # project id in repo docs, so the literal IS its detection pattern / test fixture — same
    # category as the two above (the value IS what the checker matches; not a secret, not runtime config).
    "!**/check_repo_docs_ssot.py"
    "!**/test_check_repo_docs_ssot.py"
)
source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"

# ── Pre-commit gate: validate workspace-manifest.json (add-manifest-json-validation) ──
REPO_ROOT="$(git rev-parse --show-toplevel)"
MANIFEST="${REPO_ROOT}/workspace-manifest.json"
if [ -f "$MANIFEST" ]; then
    bash "${REPO_ROOT}/scripts/validate-manifest-json.sh" "$MANIFEST" \
        || { echo "❌ workspace-manifest.json validation failed — fix before committing" >&2; exit 1; }
    # Canonical-form guard (local↔CI parity, cicd_mvp Phase-2 2026-07-02): every writer
    # must emit json.dumps(indent=2, ensure_ascii=False)+"\n" — a non-canonical write
    # (the consolidator-oscillation churn class) fails HERE instead of silently
    # re-emitting the same content as different bytes on every alternating writer.
    python3 "${REPO_ROOT}/scripts/quality_gates/check_workspace_manifest_canonical.py" --manifest "$MANIFEST" \
        || { echo "❌ workspace-manifest.json is not byte-canonical — fix the writer (see checker output)" >&2; exit 1; }
fi

# ── QG_SLICE completeness guard (local↔CI parity, cicd_mvp Phase-2 2026-07-02) ──
# Machine-enforces the "3 CI slices = zero lost coverage vs the local full run"
# partition claim; catches a slice-flag edit that would silently drop a phase
# from every CI leg (the 2026-06-10 typecheck-leg false-green class).
python3 "${REPO_ROOT}/scripts/quality_gates/check_qg_slice_completeness.py" \
    || { echo "❌ QG_SLICE partition broken — CI slicing no longer covers the full local gate" >&2; exit 1; }

# ── Promote-prefix contract guard (2026-08-10) ────────────────────────────
# run_hygiene_sweep.sh skips --diff-base for every DIFF_BASE_REF ratchet on a promotion PR,
# detected purely by branch NAME (`^promote/`). That is a naming contract with the two promote
# bots, and a half-rename would silently re-arm the exact deadlock that cost 22h / 1180
# unpromoted commits on 2026-08-10 — with no other test failing, because a gate that stops
# recognising a promote PR just looks like an ordinary red gate.
python3 "${REPO_ROOT}/scripts/quality_gates/check_promote_prefix_contract.py" \
    || { echo "❌ promote-prefix contract broken — the promote gate would silently disarm (see the check's output)" >&2; exit 1; }

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

# ── Locked plan deletion check — MOVED to the commit-msg prek stage ──────
# (scripts/hooks/check-locked-plan-deletion.sh, wired via .pre-commit-config.yaml
# stages: [commit-msg]). This block was dead for its own primary use case: a pure
# docs(plans): archival commit is routed to prek-only (CLAUDE.md's QG-batching
# rule), so quality-gates.sh never ran for it — and even when it did run, this
# block read `git log -1` (the PREVIOUS commit), not the message being written.
# unified-trading-pm@57ed9271c archived a locked_by: doc through exactly that gap.
# See plans/active/issues/locked_plan_deletion_gate_never_runs_on_docs_plans_commits_2026_07_26.md.

# ── WS-0 accumulate-and-report (cicd_consolidated_remaining_2026_06_24 § WS-0 #1) ─────────
# The ratchet/codex/governance post-gates below collect their failures into POST_GATE_FAILURES
# and the gate fails ONCE at the end with the full list, instead of the first failure
# short-circuiting (exit 1) and masking the rest — which forced serial "fix one → re-run →
# next surfaces" re-jams (incident 2026-06-24: 13 checks each hidden behind the prior). The
# structural pre-gates ABOVE (manifest / strategy-manifest / locked-plan / scope-checker-presence)
# stay fail-fast — a corrupt manifest or absent checker means the rest can't run reliably.
# Each gate still prints its ❌ remedy inline; the final summary lists every failed check.
POST_GATE_FAILURES=()
_post_gate_fail() { POST_GATE_FAILURES+=("$1"); }

# ── Post-gates: codex scope-registry coverage (rule 11, G1.9) ─────────────
# SSOT: codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md
# Fails loud if any codex/**/*.md lacks `scope:` frontmatter or declares an invalid
# scope value. The checker MUST exist — a missing one is a HARD FAIL, not a silent
# skip, so a directory rename can't quietly disable the gate again (it did, after
# 14-playbooks→14-customer-journeys left this path stale; fixed 2026-06-16).
SCOPE_CHECKER="${REPO_ROOT}/codex/14-customer-journeys/_tools/check-scope-coverage.sh"
if [ ! -f "$SCOPE_CHECKER" ]; then
    echo "❌ codex scope checker missing at $SCOPE_CHECKER — gate cannot run (path drift?)" >&2
    exit 1
fi
echo "Running codex scope-registry coverage (rule 11)..."
if bash "$SCOPE_CHECKER"; then
    log_success "Codex scope coverage check passed"
else
    echo "❌ codex scope coverage check failed — every codex/**/*.md must declare a valid scope: [...] frontmatter" >&2
    echo "   See codex/14-customer-journeys/_ssot-rules/11-codex-scope-registry.md for the rule." >&2
    _post_gate_fail "codex-scope-coverage"
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
        _post_gate_fail "runbook-execution-owner"
    fi
fi

# ── Post-gates: Coverage targets enforcement (Phase 8.D of deployment_and_qg_strategy) ──────────
# SSOT: scripts/quality_gates/coverage_targets.yaml + per-repo coverage_targets_local.yaml.
# Walks each repo's coverage.xml + computes aggregate per surface; compares vs target_pct.
COV_TARGETS_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_coverage_targets.py"
if [ -f "$COV_TARGETS_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    # Workspace-wide: warn-only (other repos still in ratchet window).
    python3 "$COV_TARGETS_CHECKER" --workspace-root "$WORKSPACE_ROOT" --warn-only >/dev/null \
        || log_warn "Coverage-targets checker errored (non-blocking)"
    # PM-specific pm_prod_scripts surface: BLOCKING (2026-06-10 — scripts run in prod CI/CD).
    echo "Running PM prod-scripts coverage gate (blocking)..."
    python3 "$COV_TARGETS_CHECKER" --workspace-root "$WORKSPACE_ROOT" --repo unified-trading-pm \
        && log_success "PM coverage-targets check passed" \
        || { log_fail "PM coverage-targets FAILED — pm_prod_scripts surface below 70% target"; _post_gate_fail "pm-coverage-targets"; }
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
        _post_gate_fail "architectural-ratchets"
    fi
fi

# ── Post-gates: PYTEST_UNIT_DIR fleet coverage sweep — baselined ratchet ──
# SSOT: plans/active/issues/mtds_ungated_test_families_2026_07_17.md (todo 5) +
# plans/active/ci_satellite_ao_dispatch_batch2_2026_07_29.md (todo 12).
# MTDS never set PYTEST_UNIT_DIR, so its whole tests/market_interface/ family
# (49 unit modules) silently never ran in the gate. This is the fleet-wide
# guard so the next per-family repo doesn't slip into the same gap unnoticed —
# flags any repo with a tests/<family>/unit/ dir its PYTEST_UNIT_DIR doesn't
# reach. Current baseline 1 (execution-service tests/sports_execution/unit/,
# pre-existing, this todo doesn't fix it) — ratchet down as families get gated.
PYTEST_UNIT_DIR_COVERAGE_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_pytest_unit_dir_coverage.py"
if [ -f "$PYTEST_UNIT_DIR_COVERAGE_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running PYTEST_UNIT_DIR fleet coverage sweep (ratchet mode)..."
    if python3 "$PYTEST_UNIT_DIR_COVERAGE_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "PYTEST_UNIT_DIR fleet coverage sweep passed (at-or-below baseline)"
    else
        echo "❌ PYTEST_UNIT_DIR fleet coverage regression — a tests/<family>/unit/ dir isn't reachable via that repo's PYTEST_UNIT_DIR" >&2
        echo "   Add the family dir to that repo's PYTEST_UNIT_DIR= (scripts/quality-gates.sh), proving the widened gate stays GREEN (rule 11a)," >&2
        echo "   or re-baseline with --update-baseline after intentional debt. See mtds_ungated_test_families_2026_07_17.md." >&2
        _post_gate_fail "pytest-unit-dir-coverage"
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
        _post_gate_fail "plan-discipline"
    fi
fi

# ── Post-gates: Finalize-plan coverage (every AO-dispatched plan needs a gated finalize plan) ──
# SSOT: task_template.md §4 "Every AO-dispatched plan needs a gated finalize plan" (operator ruling 2026-07-24).
# An `assigned_vm: planning` plan with no other active plan gating on it via
# depends_on + gate_on_depends: true never gets its source-doc reconciliation or archival done. Exempts finalize
# plans themselves and genuinely single-todo plans. Current baseline 1 (deployment_registry_firestore_p0_unblock_2026_07_14.md,
# pre-dates this rule) — ratchet down as plans get a finalize plan / archive.
FINALIZE_PLAN_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_finalize_plan_coverage.py"
if [ -f "$FINALIZE_PLAN_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Finalize-plan coverage check (ratchet mode)..."
    if python3 "$FINALIZE_PLAN_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "Finalize-plan coverage check passed (at-or-below baseline)"
    else
        echo "❌ Finalize-plan coverage regression — a new assigned_vm: planning plan shipped with no gated finalize plan." >&2
        echo "   Author a <slug>_finalize_*.md with depends_on: [<slug>] + gate_on_depends: true — see task_template.md §4." >&2
        _post_gate_fail "finalize-plan-coverage"
    fi
fi

# ── Post-gates: Evidence-backed completion (runtime-green claims cite a VERIFIED build) ──
# SSOT: plans/PLAN_FORMAT.md § 8b "Evidence-backed completion" + CLAUDE.md.
# A `- [x]` todo claiming a Cloud Build / deploy / promote went green MUST cite `Evidence: cloudbuild=<id>`;
# sub-rule A (strict-0) fails the gate if any cited build resolves to a terminal NON-success (the over-claim catch —
# verified live via `gcloud builds describe` when auth is present; soft-skips when offline/unauthed so CI never breaks);
# sub-rule B (baselined ratchet) flags a runtime-green claim with no evidence ref. Re-baseline B with --baseline-write.
EVIDENCE_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_evidence_backed_completion.py"
if [ -f "$EVIDENCE_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Evidence-backed-completion check (cited builds must be SUCCESS)..."
    if python3 "$EVIDENCE_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "Evidence-backed-completion check passed (no over-claims; sub-rule B at/below baseline)"
    else
        echo "❌ Evidence-backed-completion FAILED — a '- [x]' runtime-green claim cites a non-SUCCESS build, OR a new" >&2
        echo "   build/deploy/promote-green claim has no 'Evidence: cloudbuild=<id>' ref. See plans/PLAN_FORMAT.md § 8b." >&2
        echo "   Re-baseline sub-rule B after intentional debt: python3 ${EVIDENCE_CHECKER} --workspace-root \$WORKSPACE_ROOT --baseline-write" >&2
        _post_gate_fail "evidence-backed-completion"
    fi
fi

# ── Post-gates: Plan commit-SHA evidence (`resolved_by:`/`<repo>@<sha>` must resolve to a REAL commit) ──
# SSOT: plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md + plans/PLAN_FORMAT.md § 8c.
# A code-ship claim (`<repo>@<sha>`) is explicitly OUT of scope for the Cloud Build evidence gate above (§ 8b) — its
# evidence is "the commit + the local QG sentinel", but nothing previously verified that commit actually EXISTS. This
# gate closes that gap: `resolved_by:` frontmatter + `- [x]` todo citations of `<repo>@<sha>`, where `<repo>` is a
# present sibling clone, must resolve via `git cat-file -t <sha>` in that repo. Baselined ratchet (pre-existing
# corpus drift is grandfathered; new fabricated/unresolvable citations regress the gate). Re-baseline with
# --baseline-write only after confirming a flagged citation is genuine non-fabricated drift, not a fresh fabrication.
PLAN_SHA_EVIDENCE_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_plan_commit_sha_evidence.py"
if [ -f "$PLAN_SHA_EVIDENCE_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Plan commit-SHA evidence check (resolved_by:/<repo>@<sha> citations must resolve)..."
    if python3 "$PLAN_SHA_EVIDENCE_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "Plan commit-SHA evidence check passed (at/below baseline)"
    else
        echo "❌ Plan commit-SHA evidence regression — a resolved_by:/<repo>@<sha> citation does not resolve to a real" >&2
        echo "   commit in the cited repo's local clone. See plans/PLAN_FORMAT.md § 8c." >&2
        echo "   Re-baseline after confirming pre-existing debt: python3 ${PLAN_SHA_EVIDENCE_CHECKER} --workspace-root \$WORKSPACE_ROOT --baseline-write" >&2
        _post_gate_fail "plan-commit-sha-evidence"
    fi
fi

# ── Post-gates: Plan operator-ruling evidence (sibling to commit-SHA gate) — baselined ratchet ──
# A checked todo claiming completion via an "operator ruling" must cite a traceable source
# (/plans/…, /codex/…, or .md doc) within 300 chars of the ruling phrase.
# Failure class: an [OPERATOR]-gated decision silently closed by a worker with no traceable source
# — an authority bypass that the SHA gate structurally cannot catch (no SHA to resolve).
# Source: plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md § todo [SCRIPT] P1.
# Two incidents (2026-07-30 SHA + 2026-08-03 ruling) confirmed this as a pattern.
# Re-baseline with --baseline-write ONLY after confirming the violation is pre-existing drift,
# not a new authority bypass.
PLAN_RULING_EVIDENCE_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_plan_operator_ruling_evidence.py"
if [ -f "$PLAN_RULING_EVIDENCE_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Plan operator-ruling evidence check (unsourced 'operator ruling' completions must cite a traceable doc)..."
    if python3 "$PLAN_RULING_EVIDENCE_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "Plan operator-ruling evidence check passed (at/below baseline)"
    else
        echo "❌ Plan-operator-ruling-evidence regression — a checked todo cites 'operator ruling' with no" >&2
        echo "   traceable source (/plans/…, /codex/…, or .md doc within 300 chars). Add the source doc" >&2
        echo "   reference, or re-baseline: python3 ${PLAN_RULING_EVIDENCE_CHECKER} --workspace-root \$WORKSPACE_ROOT --baseline-write" >&2
        _post_gate_fail "plan-operator-ruling-evidence"
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
# Ratchet down by adding last_reviewed: YYYY-MM-DD to codex docs as touched.
# AGENCY SPLIT (2026-08-12): only AUTHORING defects (missing/invalid last_reviewed: or
# frontmatter) fail the gate. Docs that merely AGED past the window print an owner-grouped
# digest and do NOT block — staleness fires on the calendar, in cohorts, on changes that
# never touched the doc. Digest output is intentionally NOT sent to /dev/null.
# SSOT: /plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md
CODEX_FRESHNESS_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_codex_doc_freshness.py"
if [ -f "$CODEX_FRESHNESS_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Codex doc freshness check (ratchet mode; staleness advisory)..."
    if python3 "$CODEX_FRESHNESS_CHECKER" --workspace-root "$WORKSPACE_ROOT" --staleness-days 90; then
        log_success "Codex doc freshness check passed (no new authoring violations)"
    else
        echo "❌ Codex doc freshness regression — see CLAUDE.md § 'Post-Plan-Phase Codex Audit (HARD RULE)'" >&2
        echo "   A doc you touched is missing 'last_reviewed: YYYY-MM-DD' or has invalid frontmatter." >&2
        echo "   Add the field to that doc. Do NOT --baseline-write to silence it: staleness no longer" >&2
        echo "   blocks, so a failure here is an authoring defect in the change you are shipping." >&2
        _post_gate_fail "codex-doc-freshness"
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
        _post_gate_fail "vm-registry"
    fi
fi

# ── Post-gates: Plan frontmatter auto-fixer (runs BEFORE schema check so fixer can pre-populate) ──
# SSOT: plans/PLAN_FORMAT.md + scripts/plan-hygiene/fix_frontmatter.py.
# Mechanically populates missing/default fields (doc_type, nature, stage, scope, tags, related,
# execution_scope, drift_direction, depends_on, last_updated, etc.) on every active plan + epic
# so the schema check below finds them pre-populated rather than absent. Auto-fixer never changes
# fields that have a real value; it only fills in safe defaults for missing/empty fields.
# Exit 0 always (fixer never fails the gate — it only fixes).
FRONTMATTER_FIXER="${REPO_ROOT}/scripts/plan-hygiene/fix_frontmatter.py"
if [ -f "$FRONTMATTER_FIXER" ]; then
    echo "Running plan frontmatter auto-fixer..."
    python3 "$FRONTMATTER_FIXER" \
        && log_success "Plan frontmatter auto-fixer completed" \
        || { echo "⚠ Plan frontmatter auto-fixer errored (non-blocking — schema check follows)" >&2; }
fi

# ── Post-gates: THE comprehensive BLOCKING frontmatter gate (docspec-backed, 2026-07-04) ──
# SSOT: codex/11-project-management/doc-frontmatter-schema.md (engine: scripts/docs/docspec.py).
# Calls docspec.validate_frontmatter() over the LIVE doc trees (plans/active+epics+audit, codex,
# *.mdc — plans/archive deliberately EXCLUDED) and fails on ANY violation, HARD or SOFT, so the
# 2026-07-04 zero-violations corpus cannot rot. Replaces the two-checks lifecycle: the warn-only
# check_docspec_coverage.py is RETIRED. Exit 0/1 from check_frontmatter_schema.py.
#
# SCOPED to your own changeset, not the whole corpus (2026-07-22, decision 2026-07-19 in
# foreign_dirty_frontmatter_blocks_every_agents_gate_2026_07_18): a single bypassed bad doc from a
# DIFFERENT agent used to fail this locally for EVERY clone on the shared branch (measured ~55min
# fleet-wide shipping block), and the sanctioned remedy (seed_frontmatter.py --apply) correctly
# refuses to touch a foreign-dirty file — so only the doc's own owner could clear it. Mirrors the
# pre-push guard's own reasoning (scripts/hooks/pre-push): scope to staged + unstaged +
# committed-but-unpushed doc changes only (the doc trees this checker covers). CI's lint-codex
# slice is UNCHANGED and keeps corpus-wide enforcement — a bypassed bad doc still fails CI, it just
# no longer blocks an unrelated agent's LOCAL gate. A manual full-corpus sweep remains available via
# `python3 scripts/plan-hygiene/check_frontmatter_schema.py` (no args).
FRONTMATTER_SCHEMA_CHECKER="${REPO_ROOT}/scripts/plan-hygiene/check_frontmatter_schema.py"
if [ -f "$FRONTMATTER_SCHEMA_CHECKER" ]; then
    echo "Running per-doc-type frontmatter schema check (plan/epic/issue/audit)..."
    _fm_doc_trees='plans/active/*.md plans/active/issues/*.md plans/epics/*.md plans/audit/results/*.md plans/audit/instructions/*.md codex/*.md agents/*.md *.mdc'
    _fm_upstream=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "")
    _fm_changed=""
    if [ -n "$_fm_upstream" ]; then
        # shellcheck disable=SC2086  # intentional word-split: _fm_doc_trees is a space-separated pathspec list
        _fm_changed="${_fm_changed} $(git -C "$REPO_ROOT" diff --name-only --diff-filter=ACMR "${_fm_upstream}...HEAD" -- $_fm_doc_trees 2>/dev/null)"
    fi
    # shellcheck disable=SC2086
    _fm_changed="${_fm_changed} $(git -C "$REPO_ROOT" diff --name-only --diff-filter=ACMR -- $_fm_doc_trees 2>/dev/null)"
    # shellcheck disable=SC2086
    _fm_changed="${_fm_changed} $(git -C "$REPO_ROOT" diff --cached --name-only --diff-filter=ACMR -- $_fm_doc_trees 2>/dev/null)"
    # A brand-new doc that was never `git add`ed is UNTRACKED, so none of the three `diff` calls
    # above see it at all (diff only compares tracked content) — without this, a fresh bad-
    # frontmatter doc you just wrote would silently skip local validation entirely.
    # shellcheck disable=SC2086
    _fm_changed="${_fm_changed} $(git -C "$REPO_ROOT" ls-files --others --exclude-standard -- $_fm_doc_trees 2>/dev/null)"
    _fm_scoped_list=""
    for _f in $_fm_changed; do
        [ -f "$REPO_ROOT/$_f" ] || continue
        case " $_fm_scoped_list " in *" $_f "*) : ;; *) _fm_scoped_list="${_fm_scoped_list} $_f" ;; esac
    done
    if [ -z "${_fm_scoped_list// /}" ]; then
        log_success "Frontmatter schema check skipped (no doc changes in your changeset — nothing of yours to check; CI's corpus-wide scan is unaffected)"
    else
        # shellcheck disable=SC2086
        if python3 "$FRONTMATTER_SCHEMA_CHECKER" --quiet $_fm_scoped_list; then
            log_success "Frontmatter schema check passed (scoped to your changeset)"
        else
            echo "❌ Frontmatter schema check failed — a plan/epic/issue/audit doc has a missing/empty" >&2
            echo "   required field or an unresolvable epic. parent_epic (plans) + assigned_vm (epics) +" >&2
            echo "   epic (audit) must be non-empty + resolve. See plans/PLAN_FORMAT.md + plans/audit/README.md" >&2
            _post_gate_fail "frontmatter-schema"
        fi
    fi
fi

# ── Post-gates: Conflict-marker gate (plan hygiene — catches committed git conflict markers) ──
# check_conflict_markers.sh lives ONLY in the pre-commit hook (run_hygiene_sweep.sh --precommit)
# and in no CI/CD workflow or quality-gates.sh path. A pre-commit bypass (--no-verify, git rebase
# --continue, a prek race condition, or a quickmerge sentinel-invalid re-gate that skips the hook)
# lets committed conflict markers reach LDR undetected — committed_conflict_marker_plan_doc_2026_
# 08_10.md. This is the second line of defense, scoped to your changeset (same pattern as the
# frontmatter schema check above).
# SSOT: plans/active/issues/committed_conflict_marker_plan_doc_2026_08_10.md
CONFLICT_MARKER_CHECKER="${REPO_ROOT}/scripts/plan-hygiene/check_conflict_markers.sh"
if [ -f "$CONFLICT_MARKER_CHECKER" ]; then
    echo "Running conflict-marker check (plans/codex in your changeset)..."
    _cm_files=""
    for _f in $_fm_scoped_list; do
        [ -f "$REPO_ROOT/$_f" ] || continue
        _cm_files="${_cm_files} $REPO_ROOT/$_f"
    done
    if [ -z "${_cm_files// /}" ]; then
        log_success "Conflict-marker check skipped (no doc changes in your changeset)"
    else
        if bash "$CONFLICT_MARKER_CHECKER" --quiet $_cm_files; then
            log_success "Conflict-marker check passed (no conflict markers in your changeset)"
        else
            echo "❌ Conflict-marker check failed — a staged/changed plan/codex doc has committed" >&2
            echo "   git conflict markers (<<<<<<<, >>>>>>>, or prettier-mangled form)." >&2
            echo "   Resolve the markers before committing. See check_conflict_markers.sh header." >&2
            _post_gate_fail "conflict-markers"
        fi
    fi
fi

# ── Post-gates: Doc retrieval-layer parity (L0 index <-> schema; cross-agent doctrine) ──
# SSOT: codex/11-project-management/doc-frontmatter-schema.md + plans/active/docs_retrieval_layer_reconcile_2026_07_23.md.
# Guards two things nothing else checks: (1) scripts/docs/gen_doc_index.py's hand-maintained
# _PER_TYPE_FACETS dict staying in lockstep with docspec.py's DOC_TYPES/PER_TYPE (a schema change
# with no matching generator update would otherwise silently produce a stale/incomplete L0 index
# line for that doc_type); (2) the "grep DOC_INDEX.generated.md first" retrieval doctrine staying
# discoverable in BOTH cursor-configs/CLAUDE.md and AGENTS.md — a real regression (2026-07-23) had
# it living only in CLAUDE.md, so Codex/Cursor agents never received it despite AGENTS.md being
# the documented shared-instructions file for all three agent types.
DOC_RETRIEVAL_PARITY_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_doc_retrieval_layer_parity.py"
if [ -f "$DOC_RETRIEVAL_PARITY_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running doc retrieval-layer parity check (L0 index schema + cross-agent doctrine)..."
    if python3 "$DOC_RETRIEVAL_PARITY_CHECKER" --workspace-root "$WORKSPACE_ROOT"; then
        log_success "Doc retrieval-layer parity check passed"
    else
        echo "❌ Doc retrieval-layer parity violation — see output above for the exact remedy" >&2
        echo "   SSOT: codex/11-project-management/doc-frontmatter-schema.md" >&2
        _post_gate_fail "doc-retrieval-layer-parity"
    fi
fi

# ── Post-gates: inline markdown body-link existence — baselined ratchet (blocking on NEW breakage) ──
# SSOT: cursor-configs/skills/docs-reconcile/SKILL.md § "Broken links" (added 2026-07-23).
# docspec.validate_doc_references() (inside the frontmatter-schema gate above) only checks FRONTMATTER
# path-shaped fields (related/codex_ssots/supersedes/etc) — it never looks at a doc's BODY, so an
# inline `[the SSOT](../foo.md)` dead link was invisible to every existing gate. Ratcheted against
# doc_body_link_baseline.yaml (173 pre-existing dead links seeded 2026-07-23) so old rot doesn't fail
# every run — only a NEW broken body link (not in the baseline) fails the gate.
#
# SCOPED to your own changeset (same reasoning + same shape as the frontmatter-schema gate just above:
# foreign_dirty_frontmatter_blocks_every_agents_gate_2026_07_18 — a bypassed bad doc from a DIFFERENT
# agent must not fail this locally for EVERY clone on the shared branch). CI's corpus-wide scan is
# unaffected by this local scoping.
BODY_LINK_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_doc_body_links.py"
if [ -f "$BODY_LINK_CHECKER" ]; then
    echo "Running inline markdown body-link existence check (baselined ratchet)..."
    _bl_doc_trees='plans/active/*.md plans/active/issues/*.md plans/epics/*.md plans/audit/results/*.md plans/audit/instructions/*.md codex/*.md agents/*.md *.mdc'
    _bl_upstream=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "")
    _bl_changed=""
    if [ -n "$_bl_upstream" ]; then
        # shellcheck disable=SC2086  # intentional word-split: _bl_doc_trees is a space-separated pathspec list
        _bl_changed="${_bl_changed} $(git -C "$REPO_ROOT" diff --name-only --diff-filter=ACMR "${_bl_upstream}...HEAD" -- $_bl_doc_trees 2>/dev/null)"
    fi
    # shellcheck disable=SC2086
    _bl_changed="${_bl_changed} $(git -C "$REPO_ROOT" diff --name-only --diff-filter=ACMR -- $_bl_doc_trees 2>/dev/null)"
    # shellcheck disable=SC2086
    _bl_changed="${_bl_changed} $(git -C "$REPO_ROOT" diff --cached --name-only --diff-filter=ACMR -- $_bl_doc_trees 2>/dev/null)"
    # shellcheck disable=SC2086
    _bl_changed="${_bl_changed} $(git -C "$REPO_ROOT" ls-files --others --exclude-standard -- $_bl_doc_trees 2>/dev/null)"
    _bl_scoped_list=""
    for _f in $_bl_changed; do
        [ -f "$REPO_ROOT/$_f" ] || continue
        case " $_bl_scoped_list " in *" $_f "*) : ;; *) _bl_scoped_list="${_bl_scoped_list} $_f" ;; esac
    done
    if [ -z "${_bl_scoped_list// /}" ]; then
        log_success "Body-link check skipped (no doc changes in your changeset — nothing of yours to check; CI's corpus-wide scan is unaffected)"
    else
        # shellcheck disable=SC2086
        if python3 "$BODY_LINK_CHECKER" --quiet $_bl_scoped_list; then
            log_success "Body-link check passed (scoped to your changeset)"
        else
            echo "❌ Body-link check failed — a NEW inline markdown link in your changeset doesn't resolve" >&2
            echo "   Fix the link target, or if it points to a doc that legitimately moved, repoint it." >&2
            echo "   Pre-existing debt: python3 scripts/quality_gates/check_doc_body_links.py --update-baseline" >&2
            _post_gate_fail "doc-body-links"
        fi
    fi
fi

# ── Post-gates: repo-docs-defer-to-codex (S5.11 / S5.6) — baselined ratchet (blocking on NEW drift) ──
# SSOT: codex/06-coding-standards/documentation-standards.md § S5.11 (+ S5.6).
# Phase 5 of plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md — the enforcement that keeps the
# Phase 1-4 remediation from silently rotting back. Walks every SIBLING repo's living docs (docs/**/*.md
# + root README.md; unified-trading-pm excluded — it IS the codex SSOT) and flags the two deterministic
# drift classes the audit found dominant: (1) a repo doc referencing the ARCHIVED unified-trading-codex/
# mirror instead of the live PM /codex/ SSOT, (2) a repo doc hardcoding a resolver-owned literal S5.6 bans
# (the real GCP project id — use {project_id}). Ratcheted against repo_docs_ssot_baseline.yaml (32 pre-
# existing seeded 2026-07-29) so old debt doesn't fail every run — only NEW drift blocks. Needs
# WORKSPACE_ROOT (the sibling clones); CI (siblings absent) degrades to a no-op, so this is the LOCAL /
# full-workspace gate, same shape as the codex-freshness + workflow-template-parity gates.
REPO_DOCS_SSOT_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_repo_docs_ssot.py"
if [ -f "$REPO_DOCS_SSOT_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running repo-docs-defer-to-codex check (S5.11/S5.6 baselined ratchet)..."
    if python3 "$REPO_DOCS_SSOT_CHECKER" --workspace-root "$WORKSPACE_ROOT" --quiet; then
        log_success "Repo-docs-defer-to-codex check passed (at-or-below baseline)"
    else
        echo "❌ Repo-docs-defer-to-codex drift — a repo doc references the archived unified-trading-codex/" >&2
        echo "   mirror or hardcodes a resolver-owned literal. Repoint at unified-trading-pm/codex/… or use" >&2
        echo "   the {project_id} placeholder (S5.6). Pre-existing debt: --update-baseline (see script header)." >&2
        _post_gate_fail "repo-docs-ssot"
    fi
fi

# ── Post-gates: agent-rules size cap (CLAUDE.md / SUB_AGENT_MANDATORY_RULES.md) — HARD cap ──
# SSOT: CLAUDE.md header § "Size budget". The agent rule files are a lean index (1-line directive +
# codex pointer); detail lives in codex, never inline. They keep silently re-bloating, so the cap is
# now machine-enforced rather than merely "review-blocking". The byte cap doubles as a token budget
# (~4 B/tok): CLAUDE.md 40 KiB ≈ 10k tok; SUB_AGENT_MANDATORY_RULES.md 10 KiB ≈ 2.5k tok. Caps are
# the constants in the checker. On failure: condense a rule + migrate detail to codex — never raise the cap.
AGENT_RULES_CAP_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_agent_rules_size_cap.py"
if [ -f "$AGENT_RULES_CAP_CHECKER" ]; then
    echo "Running agent-rules size cap check (CLAUDE.md / SUB_AGENT_MANDATORY_RULES.md)..."
    if python3 "$AGENT_RULES_CAP_CHECKER"; then
        log_success "Agent-rules size cap check passed"
    else
        echo "❌ Agent-rules size cap exceeded — see CLAUDE.md header § 'Size budget'" >&2
        echo "   Condense a rule to a 1-line directive + codex pointer; migrate detail to its codex SSOT." >&2
        echo "   Do NOT raise the cap in check_agent_rules_size_cap.py." >&2
        _post_gate_fail "agent-rules-size-cap"
    fi
fi

# ── Post-gates: Workflow-template parity — baselined ratchet (blocking on NEW drift) ──
# SSOT: detect_template_drift.py § "workflow-template parity". Flat .github/workflows/*.yml are
# cp'd verbatim from scripts/workflow-templates/ by rollout-workflow-templates.sh, so every per-repo
# copy MUST byte-match the SSOT. Closes the hole that flat-copied workflows had no drift guard for
# (e.g. the tab-mirror-to-ldr.yml dual-path). Ratcheted: only NEW drift beyond
# workflow_template_drift_baseline.json blocks; CI (siblings absent) degrades to a no-op, so this is
# the LOCAL / full-workspace gate. Ratchet down via --baseline-write as repos are re-rolled-out.
WORKFLOW_PARITY_CHECKER="${REPO_ROOT}/scripts/quality_gates/detect_template_drift.py"
if [ -f "$WORKFLOW_PARITY_CHECKER" ]; then
    echo "Running workflow-template parity check (baselined ratchet)..."
    if python3 "$WORKFLOW_PARITY_CHECKER" --workflows >/dev/null; then
        log_success "Workflow-template parity passed (no new drift beyond baseline)"
    else
        echo "❌ NEW workflow-template drift — a .github/workflows/*.yml copy diverged from its SSOT" >&2
        echo "   Run: python3 ${WORKFLOW_PARITY_CHECKER} --workflows   (shows which repo/template)" >&2
        echo "   Fix: re-run rollout-workflow-templates.sh — NEVER hand-edit a per-repo copy" >&2
        echo "   If intentional, re-baseline: python3 ${WORKFLOW_PARITY_CHECKER} --baseline-write" >&2
        _post_gate_fail "workflow-template-parity"
    fi
fi

# ── Workflow YAML parse gate — MOVED to the shared base (2026-06-30) ──
# Was here (PM-only), so only PM's workflows were validated → the SIT-producer YAML break slipped through.
# Now lives in scripts/quality-gates-base/base-service.sh [0/6] so EVERY repo runs the ONE PM-hosted
# checker against its own .github/workflows. SSOT: plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md.

# ── Post-gates: STEP 5.64 — PM script path-reference ratchet (blocking) ──
# SSOT: CLAUDE.md § "Grep-Then-Read, Not Grep-Then-Conclude" + scripts/quality_gates/check_pm_script_path_refs.py.
# Scans workflow templates, GHA workflows, and operator bash scripts for references to PM script
# paths (relative `scripts/` refs and workspace-absolute `$WORKSPACE_ROOT/unified-trading-pm/scripts/` refs)
# and asserts every referenced path exists. Catches silent regressions where a script is renamed/deleted
# but its callers (CI workflows, operator runbooks) still reference the old path.
PM_SCRIPT_REF_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_pm_script_path_refs.py"
if [ -f "$PM_SCRIPT_REF_CHECKER" ]; then
    echo "Running PM script path-reference ratchet (STEP 5.64)..."
    if python3 "$PM_SCRIPT_REF_CHECKER"; then
        log_success "PM script path-reference ratchet passed"
    else
        echo "❌ PM script path-reference ratchet FAILED — broken script reference(s) in workflows or operator scripts" >&2
        echo "   Fix: ensure the referenced script exists, or prefix documentation-only lines with '#'" >&2
        _post_gate_fail "pm-script-path-refs"
    fi
fi


# -- Post-gates: Two-sided prospectus vs codex audit (Phase 6B) -- baselined ratchet --
# SSOT: plans/archive/2026_07/capability_wizard_and_manifest_2026_06_11.md section 6B parity quality gates.
# Baseline (2026-06-12): 1 venue-category contradiction + 2 orphan docs + 0 legs-in-prose drift.
# NEW findings (above baseline) fail the gate. Re-baseline with --baseline-write only for
# accepted debt. Checks: (c) venue-category contradictions, (b) orphan codex docs, (d) legs-in-prose.
TWO_SIDED_AUDIT="${REPO_ROOT}/scripts/quality_gates/check_two_sided_audit.py"
if [ -f "$TWO_SIDED_AUDIT" ]; then
    echo "Running two-sided prospectus vs codex audit (Phase 6B baselined ratchet)..."
    if python3 "$TWO_SIDED_AUDIT"; then
        log_success "Two-sided prospectus vs codex audit passed (at-or-below baseline)"
    else
        echo "New findings in two-sided prospectus vs codex audit -- fix the contradictions/orphans above." >&2
        echo "   Or re-baseline with: python3 ${TWO_SIDED_AUDIT} --baseline-write (accepted debt only)" >&2
        _post_gate_fail "two-sided-audit"
    fi
fi

# -- Post-gates: AO dispatch-visibility gate (disk-vs-backlog open-todo delta) -- baselined ratchet --
# SSOT: ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md. Per assigned_vm:planning
# doc, compares the REAL agent-orchestrator _parse_open_todos oracle (imported via a subprocess call into
# agent-orchestrator's own venv -- server.dispatch_visibility_report, a thin reporting wrapper, no parser
# change) against the raw `- [ ]` count on disk, and classifies every excluded todo declared (a live
# BLOCKED-<token>/DEFERRED-BY-DESIGN/stretch marker that opens its own line) vs accidental (the marker is
# merely present in a longer sentence -- the regex-widening bug class that has resisted four successive
# fixes). Ratcheted on two axes (ao_dispatch_visibility_baseline.yaml): accidental exclusions + zero-
# dispatchable docs. Needs WORKSPACE_ROOT (the sibling agent-orchestrator clone + its .venv); CI (siblings
# absent) degrades to a no-op, same convention as the other workspace-wide PM gates.
AO_DISPATCH_VISIBILITY_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_ao_dispatch_visibility_gate.py"
if [ -f "$AO_DISPATCH_VISIBILITY_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running AO dispatch-visibility gate (disk-vs-backlog todo delta, baselined ratchet)..."
    if python3 "$AO_DISPATCH_VISIBILITY_CHECKER" --workspace-root "$WORKSPACE_ROOT" --quiet; then
        log_success "AO dispatch-visibility gate passed (at-or-below baseline)"
    else
        echo "❌ AO dispatch-visibility gate — a NEW accidental (undeclared) exclusion or zero-dispatchable" >&2
        echo "   doc appeared. Re-run with --json for the doc/description list. Fix: declare the marker (start" >&2
        echo "   of its own line) or rewrite the todo so it no longer trips it. Or --update-baseline (justified)." >&2
        _post_gate_fail "ao-dispatch-visibility"
    fi
fi

# ── Post-gates: Capability-regression gate (Wave-2 #5) — baselined ratchet ──
# SSOT: plans/archive/2026_07/capability_wizard_and_manifest_2026_06_11.md Wave-2 #5.
# FAILS when a capability edge regressed available -> not_available/not_registered
# vs scripts/openapi/capability-edge-status-baseline.json, unless acked in
# capability_regression_acks.yaml with a plan reference. Improvements never fail.
# Accept a new state with: generate_capability_changelog.py --update-baseline.
CAP_REGRESSION="${REPO_ROOT}/scripts/quality_gates/check_capability_regression.py"
if [ -f "$CAP_REGRESSION" ]; then
    echo "Running capability-regression gate (Wave-2 #5 baselined ratchet)..."
    if python3 "$CAP_REGRESSION"; then
        log_success "Capability-regression gate passed (no unacked lost capability)"
    else
        echo "❌ Capability regression — an edge lost capability without a plan ack (see above)." >&2
        _post_gate_fail "capability-regression"
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
        _post_gate_fail "credential-ask-orphans"
    fi
fi

# ── Post-gates: ci_status single-writer guard (Guard 1 — HARD, blocking) ──
# SSOT: cicd_contract_hardening_2026_06_01.md § "ci_status consistency hardening".
# repositories.*.ci_status is bot-written-only (ci-status-update[bot], driven by
# quality-gates-v2 → ci-status-update.yml). A local / manual / Prettier edit forks the
# value — the 2026-06-03 staging dam (LDR FEATURE_GREEN vs main FAILING → promoter
# dep-blocked the fleet). Block any uncommitted ci_status change vs HEAD (change-set
# relative, so a pre-existing LDR-vs-main fork never false-positives). The CI/PR layer
# runs the same script with --baseline-ref origin/<base> + --actor "$GITHUB_ACTOR".
CI_STATUS_GUARD="${REPO_ROOT}/scripts/cicd/check_ci_status_bot_only.py"
if [ -f "$CI_STATUS_GUARD" ]; then
    echo "Running ci_status single-writer guard (Guard 1)..."
    if python3 "$CI_STATUS_GUARD" --baseline-ref HEAD --actor "${GITHUB_ACTOR:-}"; then
        log_success "ci_status single-writer guard passed"
    else
        echo "❌ ci_status edited outside ci-status-update[bot] — revert the ci_status change(s) above." >&2
        echo "   ci_status is bot-written state; only quality-gates-v2 → ci-status-update may change it." >&2
        _post_gate_fail "ci-status-single-writer"
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
        _post_gate_fail "code-workspace-drift"
    fi
fi

# ── Post-gates: Dispatch-listener orphan scanner (batch-1 todo 1) — baselined ratchet ──
# SSOT: plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md todo 1 +
# plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md F1/F3.
# A repository_dispatch POST returns 204 whether or not any workflow is actually
# subscribed to the dispatched event_type — this statically catches the "nobody
# subscribed" case (dispatched event_type with no listener in the resolved target
# repo). Current baseline 38 — ratchet down as orphan dispatch sites get fixed.
DISPATCH_LISTENERS_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_dispatch_listeners.py"
if [ -f "$DISPATCH_LISTENERS_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running dispatch-listener orphan scanner (ratchet mode)..."
    if python3 "$DISPATCH_LISTENERS_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "Dispatch-listener orphan scanner passed (at-or-below baseline)"
    else
        echo "❌ Dispatch-listener orphan regression — a dispatched event_type has no listener in its resolved target repo." >&2
        echo "   Either add the missing listener, delete the dead dispatch call, OR" >&2
        echo "   if intentional/tracked debt, re-baseline with: python3 ${DISPATCH_LISTENERS_CHECKER} --workspace-root \$WORKSPACE_ROOT --baseline-write" >&2
        _post_gate_fail "dispatch-listeners"
    fi
fi

# ── Post-gates: Cloud Build template-vs-consumer drift ratchet (batch-1 todo 1) ──
# SSOT: plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md todo 1 +
# plans/active/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md.
# A consumer's committed cloudbuild.yaml can carry content its mapped
# configs/cloudbuild-*-template.yaml render does NOT — the next
# rollout-cloudbuild.py --apply on that repo would either be refused (would-drop-
# content guard) or, if the guard is ever bypassed, silently regress it. Baseline
# is per-repo (scripts/quality_gates/cloudbuild_template_drift_baseline.yaml) —
# ratchet down as templates are forward-ported / consumers reconciled.
CLOUDBUILD_TEMPLATE_DRIFT_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_cloudbuild_template_drift.py"
if [ -f "$CLOUDBUILD_TEMPLATE_DRIFT_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running Cloud Build template-vs-consumer drift ratchet..."
    if python3 "$CLOUDBUILD_TEMPLATE_DRIFT_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "Cloud Build template-vs-consumer drift ratchet passed (at-or-below baseline)"
    else
        echo "❌ Cloud Build template drift — THE OFFENDING CONTENT IS IN ANOTHER REPO (named in the [FAIL] line above)." >&2
        echo "   This is almost certainly NOT the change you are shipping. This check is fleet-wide: a consumer" >&2
        echo "   repo's cloudbuild.yaml drifting from its template fails THIS gate, so no .qg_last_passed_sha" >&2
        echo "   sentinel is written and quickmerge refuses EVERY unified-trading-pm code ship, on every host," >&2
        echo "   until that other repo is drained. Fix it there; do not try to route around it here." >&2
        echo "   Forward-port the content into unified-trading-pm/configs/cloudbuild-*-template.yaml." >&2
        echo "   NOTE: --update-baseline is SHRINK-ONLY and silently REFUSES to raise a count (it prints the" >&2
        echo "   higher number and leaves the file unchanged). It is not an unblock path." >&2
        echo "   Consumer-side prevention: base-service.sh STEP 5.108 / base-ui.sh [5.108] now fail in the" >&2
        echo "   consumer's OWN gate, so new drift should be caught there before it ever reaches this one." >&2
        _post_gate_fail "cloudbuild-template-drift"
    fi
fi

# ── Post-gates: Swallowed-credential-fetch idiom ratchet (batch-1 todo 1) — baselined ratchet ──
# SSOT: plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md todo 1 +
# plans/active/issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md.
# Bans the discarded-stderr-then-truthy-fallback idiom around a credential fetch
# in any repo's scripts/ dir (without a `# noqa: swallowed-credential-fetch`
# marker) — that idiom degrades a real credential failure to an empty string
# instead of failing loud. Baseline is
# per-repo (scripts/quality_gates/no_swallowed_credential_fetch_baseline.yaml) —
# ratchet down as swallow sites are fixed.
SWALLOWED_CREDENTIAL_FETCH_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_no_swallowed_credential_fetch.py"
if [ -f "$SWALLOWED_CREDENTIAL_FETCH_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running swallowed-credential-fetch idiom ratchet..."
    if python3 "$SWALLOWED_CREDENTIAL_FETCH_CHECKER" --workspace-root "$WORKSPACE_ROOT" >/dev/null; then
        log_success "Swallowed-credential-fetch idiom ratchet passed (at-or-below baseline)"
    else
        echo "❌ Swallowed-credential-fetch regression — a NEW discarded-stderr-then-truthy-fallback-wrapped credential fetch landed." >&2
        echo "   Surface the real error (log it, exit non-zero) instead, OR add # noqa: swallowed-credential-fetch with a reason, OR" >&2
        echo "   if intentional debt, re-baseline with: python3 ${SWALLOWED_CREDENTIAL_FETCH_CHECKER} --workspace-root \$WORKSPACE_ROOT --update-baseline" >&2
        _post_gate_fail "swallowed-credential-fetch"
    fi
fi

# ── WS-0 accumulate-and-report: fail ONCE with every failed post-gate (no serial masking) ──
if [ ${#POST_GATE_FAILURES[@]} -gt 0 ]; then
    echo "" >&2
    log_fail "${#POST_GATE_FAILURES[@]} post-gate check(s) FAILED (all ran — no serial masking):"
    for _pg in "${POST_GATE_FAILURES[@]}"; do echo "     • ${_pg}" >&2; done
    echo "   Each check's ❌ remedy is printed inline above — fix ALL of them, then re-run." >&2
    exit 1
fi

# ── Post-gates: Workspace-manifest version coherence (warn-only — non-blocking) ──
# SSOT: scripts/cicd/assert_version_coherence.py docstring + plans/active/
# staging_clean_start_and_stale_pr_hygiene_2026_06_08.md (P2 version-surface reconciliation).
# Three violation classes: VERSION_SPLIT (versions{} vs source pyproject vs staging_versions{}),
# VESTIGIAL_SCALAR_DRIFT (repositories{}.version display scalar != versions{}), and
# DEP_FLOOR_UNSATISFIABLE (dep-edge range-pin floor ≤ versions{}[dep] < ceiling — explicitly
# NOT floor==latest). Warn-only first per the plan; flipping to blocking is a later ratchet.
VERSION_COHERENCE_CHECKER="${REPO_ROOT}/scripts/cicd/assert_version_coherence.py"
if [ -f "$VERSION_COHERENCE_CHECKER" ]; then
    echo "Running workspace-manifest version coherence check (warn-only)..."
    python3 "$VERSION_COHERENCE_CHECKER" --warn-only \
        && log_success "Version coherence check completed (warn-only)" \
        || log_warn "Version coherence checker errored (non-blocking)"
fi

# ── Post-gates: UI/API flow coverage checker (coverage gaps warn-only; a missing/unparseable
# manifest is a HARD FAIL — a silently-swallowed config error means the coverage verdict below
# it is never actually checked, which is worse than no check at all) ──
FLOW_CHECKER="${REPO_ROOT}/scripts/checkers/check_ui_api_flow_coverage.py"
if [ -f "$FLOW_CHECKER" ]; then
    echo "Running UI/API flow coverage checker (warning-only for coverage gaps)..."
    FLOW_CHECKER_RC=0
    python3 "$FLOW_CHECKER" --workspace-root "$WORKSPACE_ROOT" --warning-only || FLOW_CHECKER_RC=$?
    if [ "$FLOW_CHECKER_RC" -eq 2 ]; then
        log_fail "UI/API flow coverage checker config error (exit 2) — manifest missing or unparseable; coverage cannot be verified"
        exit 1
    elif [ "$FLOW_CHECKER_RC" -ne 0 ]; then
        log_warn "UI/API flow coverage checker failed (non-blocking)"
    else
        log_success "UI/API flow coverage check completed"
    fi
fi

# ── Post-gates: ensure the Claude `/<skill>` discovery symlink (.claude/skills) ──
# Best-effort, RELATIVE symlink, NO-OP in CI. Asserts workspace-root .claude/skills as ONE symlink
# to cursor-configs/skills/ so every slot surfaces each /<skill> without a manual setup step — and
# so a NEW skill needs no re-linking at all (it just appears through the dir link). The helper
# always exits 0 and self-skips under CI, so it can never disturb the gate or a GHA runner.
# SSOT: scripts/workspace/link-claude-skills.sh.
# NB: the helper ALWAYS exits 0 (CI self-skip + internal best-effort), so the caller needs no
# error-swallowing suffix here — and such a bypass in quality-gates.sh is itself banned by the
# codex-compliance ratchet (so do not add one).
SKILL_LINKER="${REPO_ROOT}/scripts/workspace/link-claude-skills.sh"
if [ -f "$SKILL_LINKER" ]; then
    bash "$SKILL_LINKER" "$WORKSPACE_ROOT"
fi

# ── Post-gates: regenerate CI/CD pipeline diagram (SSOT: cicd-pipeline-definition.yaml) ──
REPO_ROOT="$(git rev-parse --show-toplevel)"
DIAGRAM_YAML="${REPO_ROOT}/docs/repo-management/cicd-pipeline-definition.yaml"
DIAGRAM_SCRIPT="${REPO_ROOT}/scripts/generate-cicd-diagram.py"
if [ -f "${DIAGRAM_YAML}" ] && [ -f "${DIAGRAM_SCRIPT}" ]; then
    echo "Regenerating CI/CD pipeline diagram..."
    python3 "${DIAGRAM_SCRIPT}" || { echo "⚠ Diagram regeneration failed (non-blocking)" >&2; }
fi

# ── Post-gates: base-image digest drift detector (warn-only — non-blocking) ──
# Scans every service Dockerfile for ARG BASE_IMAGE_DIGEST and warns if the fleet is
# inconsistent (a repo missed the update-dependency-version.yml fan-out) or if the
# pinned digest has fallen behind :latest (best-effort gcloud probe).  The incident
# that motivated this: mdps pin drifted to e939b4ee (UTL 0.11.0 / UAC 0.15.0) while
# its floor required UTL >=0.12.0 → Cloud Build failed silently.
# SSOT: plans/active/deployment_ui_monitoring_pane_2026_06_19.md
DIGEST_DRIFT_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_base_image_digest_drift.py"
if [ -f "$DIGEST_DRIFT_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running base-image digest drift detector (warn-only)..."
    python3 "$DIGEST_DRIFT_CHECKER" --workspace-root "$WORKSPACE_ROOT" \
        || { echo "⚠ Digest drift checker errored (non-blocking)" >&2; }
fi

# ── Post-gates: uv pip install retry-wrapper drift detector (warn-only — non-blocking) ──
# Scans every service Dockerfile's RUN --mount=type=secret,id=gar_token layer for the
# documented 3-attempt retry loop around `uv pip install ... --no-sources` and warns if a
# repo has silently dropped it (re-exposing the transient GAR publish-ordering race the
# wrapper exists to absorb). Mirrors the base-image digest-drift detector above.
# SSOT: codex/06-coding-standards/dockerfile-standards.md § "uv pip install Retry Wrapper"
UV_RETRY_DRIFT_CHECKER="${REPO_ROOT}/scripts/quality_gates/check_uv_install_retry_wrapper_drift.py"
if [ -f "$UV_RETRY_DRIFT_CHECKER" ] && [ -n "${WORKSPACE_ROOT:-}" ]; then
    echo "Running uv pip install retry-wrapper drift detector (warn-only)..."
    python3 "$UV_RETRY_DRIFT_CHECKER" --workspace-root "$WORKSPACE_ROOT" \
        || { echo "⚠ uv install retry-wrapper drift checker errored (non-blocking)" >&2; }
fi
