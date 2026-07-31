---
doc_type: issue
title: Decompose deployment-api's 27 pre-existing size-gate violations (unmasked by base-service.sh STEP 5.5z)
summary:
  "unified-trading-pm's base-service.sh STEP 5.5z (qg_size_gate_sentinel_skip_root_cause_2026_07_25.md P0 fix, landed
  2026-07-30) moved the file/function/class/method size checks out of the CODEX_MAX_VIOLATIONS aggregate-tolerance pool
  into a zero-tolerance hard gate. This turned deployment-api's LDR→main promotion PR #430 quality-gates-v2 red: 6 files
  over MAX_FILE_LINES (900) and ~45 functions/methods over MAX_FUNCTION_LINES/MAX_METHOD_LINES, none of them new — all
  silently absorbed for weeks/months by CODEX_MAX_VIOLATIONS=5. Unblocked immediately (ldr_qg_failure escalation
  agt-46da69) by adding all 27 affected files to FUNCTION_SIZE_EXTRA_EXCLUDES (deployment-api/scripts/quality-gates.sh),
  the same sanctioned per-repo allow-list mechanism strategy-service already uses for analogous legacy debt — this is a
  stopgap, not a fix; the actual decomposition work is this doc."
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [code-quality, function-size, file-size, qg-ratchet, quality-gates, deployment-api]
related:
  - /plans/archive/issues/qg_size_gate_sentinel_skip_root_cause_2026_07_25.md
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
depends_on: []
source:
  "ldr_qg_failure escalation agt-46da69 (deployment-api#430, 2026-07-30) — CI wall fix filed the decomposition as its
  own follow-up per findings-triage (outside-plan, real work, not folded into the one-shot CI-fix scope)."
---

# Decompose deployment-api's 27 pre-existing size-gate violations

## Why this doc exists

Today's `base-service.sh` STEP 5.5z change (see `qg_size_gate_sentinel_skip_root_cause_2026_07_25.md`) made the
file/function/class/method size checks a zero-tolerance hard gate instead of a `CODEX_MAX_VIOLATIONS`-tolerated class.
deployment-api was one of the 9 repos flagged in that doc's P0 finding as carrying a nonzero `CODEX_MAX_VIOLATIONS` (5)
that was masking real size debt. Re-measuring locally (same AST/byte-count logic as `base-service.sh`) at LDR HEAD
found:

**File-size violations (>900 lines):**

- `deployment_api/routes/deployments_inventory.py` — 2592 L
- `deployment_api/routes/health_consolidator.py` — 1082 L
- `deployment_api/services/data_status/manifest.py` — 1131 L
- `deployment_api/services/data_status/mtds.py` — 1059 L
- `deployment_api/services/cost_observability/service.py` — 1055 L
- `deployment_api/routes/data_status/_live_coverage.py` — 920 L

**Function/method/class-size violations (>200/50/900 lines respectively):** ~45 functions/methods across 24 files, worst
offenders `deployment_api/services/data_status/manifest.py:_build_manifest_category()` (360L),
`deployment_api/services/data_status/instrument_coverage.py:per_instrument_coverage()` (364L),
`deployment_api/services/data_status/sports_helpers.py:sports_honest_coverage()` (300L),
`deployment_api/services/deploy_missing_launch.py:launch_deploy_missing_vm()` (236L),
`deployment_api/routes/deployment_state.py:refresh_deployment_status_sync()` (234L),
`deployment_api/services/data_status/mtds.py:mtds_honest_coverage_for_venue()` (220L). Full per-file list in the
`FUNCTION_SIZE_EXTRA_EXCLUDES` comment block, `deployment-api/scripts/quality-gates.sh` (2026-07-30 commit).

**Immediate unblock (done, see Progress Log)**: all 27 files added to `FUNCTION_SIZE_EXTRA_EXCLUDES` — the same per-repo
allow-list mechanism `strategy-service/scripts/quality-gates.sh` already uses for its own legacy engine/risk modules.
This restores `quality-gates-v2` to green without touching a coverage floor or pragma-skipping anything, but it means
these 27 files are now EXEMPT from the size gate entirely (both dimensions, since one `find` feeds both checks) — any
further growth inside them will not be caught until this doc's decomposition work removes them from the exclude list
file-by-file.

## Acceptance

- [ ] [SCRIPT] P1. Decompose `deployment_api/routes/deployments_inventory.py` (2592L, the largest offender) into a
      facade package (mirrors the 2026-06-11 precedent noted in this repo's own `quality-gates.sh` history: "routes/
      deployments 968 → 3-module package"). Remove its `FUNCTION_SIZE_EXTRA_EXCLUDES` entry once <900L and its own
      functions are compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P1. Decompose `deployment_api/services/data_status/manifest.py` (1131L, contains the 360L
      `_build_manifest_category()` — also a function-size violation) into sibling modules under `services/data_status/`.
      Remove its exclude entry once compliant.
- [ ] [SCRIPT] P1. Decompose `deployment_api/services/data_status/mtds.py` (1059L, contains the 220L
      `mtds_honest_coverage_for_venue()`). Remove its exclude entry once compliant.
- [ ] [SCRIPT] P1. Decompose `deployment_api/services/cost_observability/service.py` (1055L, 6 oversized methods).
      Remove its exclude entry once compliant.
- [ ] [SCRIPT] P1. Decompose `deployment_api/routes/health_consolidator.py` (1082L). Remove its exclude entry once
      compliant.
- [ ] [SCRIPT] P2. Decompose `deployment_api/routes/data_status/_live_coverage.py` (920L, just over the cap). Remove its
      exclude entry once compliant.
- [ ] [SCRIPT] P2. Extract helpers from the 8 oversized methods in
      `deployment_api/services/data_status/breakdowns_core.py` + `breakdowns_domain.py` (both are pure-decomposition
      candidates — mostly independent `_build_*_breakdown()` methods). Remove both exclude entries once compliant.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/routes/deployment_state.py`
      (`refresh_deployment_status_sync()`, 234L). Remove its `FUNCTION_SIZE_EXTRA_EXCLUDES` entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/artifact_pipeline/service.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_analytics_service.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_query_service.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/data_status/cli.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/coverage.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/defi.py`. Remove its exclude entry once compliant; re-run `quality-gates.sh`
      to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/instrument_coverage.py` (`per_instrument_coverage()`, 364L). Remove its
      exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/sports.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/sports_helpers.py` (`sports_honest_coverage()`, 300L). Remove its exclude
      entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/data_status/venue_resolution.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/deploy_missing_launch.py` (`launch_deploy_missing_vm()`, 236L). Remove its exclude entry
      once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/deployment_manager.py`. Remove its exclude entry once compliant; re-run
      `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/deployment_state.py`
      (a different file from `routes/deployment_state.py` above — same basename, different directory). Remove its
      exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/event_processor.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/state_manager.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/services/sync_service.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in
      `deployment_api/services/tarball_staleness.py`. Remove its exclude entry once compliant; re-run `quality-gates.sh`
      to confirm no regression.
- [ ] [SCRIPT] P2. Decompose the remaining function-size-only violation in `deployment_api/utils/path_combinatorics.py`.
      Remove its exclude entry once compliant; re-run `quality-gates.sh` to confirm no regression.
- [ ] [SCRIPT] P3. Once every file above is decomposed and removed from `FUNCTION_SIZE_EXTRA_EXCLUDES`, re-measure
      `CODEX_MAX_VIOLATIONS` honestly (currently 5) and ratchet it down if the size class was the only thing keeping it
      non-zero — verify actual `V` via `QG_SLICE=lint-codex`, don't guess.

## Progress Log

- 2026-07-30 (slot 14, ldr_qg_failure escalation agt-46da69): Root-caused via the already-filed
  `qg_size_gate_sentinel_skip_root_cause_2026_07_25.md` P0 entry (base-service.sh STEP 5.5z, same-day change) — this is
  fleet-wide exposure, deployment-api being one of 9 flagged repos. Confirmed locally (direct AST/byte-count
  re-measurement, same logic as the gate) that all 27 violations are pre-existing, not introduced by PR #430 or any
  recent deployment-api commit. Unblocked the promotion PR by adding all 27 files to `FUNCTION_SIZE_EXTRA_EXCLUDES` in
  `deployment-api/scripts/quality-gates.sh` — verified locally: `✅ File size OK` / `✅ Function/class/method size OK` /
  `✅ ALL QUALITY GATES PASSED`. Filed this doc for the real decomposition work per findings-triage (outside the
  one-shot CI-fix scope). Not assigning `assigned_vm: planning` yet per the default-human rule — an operator/main-agent
  call on whether to AO-dispatch this (each todo above is independently bounded/deterministic once split further, so it
  would likely qualify, but that's a destination decision this escalation role doesn't make unilaterally).
- **na-eligibility-audit 2026-07-31**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-676f1e) — this doc's
  own 2026-07-30 entry above already flagged every todo as independently bounded/deterministic and deferred only the
  destination call, which this audit exists to make. Conflict-check run against
  `parent_epic: deployment_and_user_management_master` (no other active `assigned_vm: planning` doc in this epic) + the
  infra tranche's consolidated-closeout digest: zero overlap, clear to proceed. Flipped `assigned_vm: NA -> planning`,
  `execution_scope: local-only -> orchestrator-agent`. Also split the final bundled "remaining function-size-only
  violators" todo (19 files in one checkbox) into 19 one-file todos, per this doc's own "one todo per file recommended
  when this doc is worked... split at dispatch time if promoted to `assigned_vm: planning`" note — total open todo count
  is now 27 (was 9), still well under the 10-100 authoring cap.
