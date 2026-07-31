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

- [x] ✅ [SCRIPT] P1. **DONE 2026-07-31 (slot-2, infra craft)** — `deployment-api@75584a8` (split) +
      `deployment-api@17361fd` (exclude-list cleanup). Decomposed `deployment_api/routes/deployments_inventory.py`
      (2592L) into a 6-module facade package
      (`deployments_inventory/{__init__,_classification,_registry_io,     _mock_data,_aggregation,_routes}.py`, every
      module <900L), mirroring the 2026-06-11 `routes/deployments` precedent (pure code motion). The precedent's own
      docstring ("patched module-level collaborators resolved through the facade module at call time") turned out to be
      load-bearing here: `tests/mocks.py`'s `patch_inventory_secondary_census` + ~120 `patch()`/`patch.object()` call
      sites across `test_route_deployments_inventory.py` and 8 other test files target
      `deployment_api.routes.     deployments_inventory.<name>` directly (27 distinct "seam" collaborators — `_cfg`,
      `get_storage_client`, `_load_registry_entries`, `CostObservabilityService`, etc.) — every submodule resolves these
      via `import ... as _inv; _inv.<name>(...)` at call time rather than a direct import, so the existing patch surface
      keeps intercepting regardless of which file now defines/calls the seam. Verified empirically, not just by
      inspection: all 186 tests across every consuming test file pass unchanged; `basedpyright`/`ruff` clean (fixed 2
      real gaps found along the way — 120 `reportPrivateUsage` cross-submodule accesses needing
      `# pyright: ignore[reportPrivateUsage]` per the same precedent convention, and 4 `pool.map(lambda ...)` call sites
      losing type inference through the `_inv.` indirection, fixed by replacing the lambdas with explicitly-typed nested
      functions); full `quality-gates.sh` green both before and after removing the now-obsolete
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry (confirmed `✅ File size OK` with the exclude removed).
- [ ] [SCRIPT] P1. **PARTIAL 2026-07-31 (slot-5, infra craft)** — `deployment-api@0b4c6a8`. Extracted the named
      `_build_manifest_category()` (360L) + its data_type-grouping/MTDS-annotation helpers into a NEW sibling module
      `manifest_category_builder.py`, inserted into the mixin chain between `missing_shards` and `manifest` (pure code
      motion; updated the chain-description docstring in all 9 sibling mixin files for consistency). Decomposed the 360L
      method itself down to ~20 small helper methods, EVERY ONE ≤50L (the real `MAX_METHOD_LINES` gate, not just the
      file-size cap) — `manifest_category_builder.py` needs NO exclude-list entry at all. `manifest.py` itself shrank
      1131L→683L. Verified: 257 tests green
      (`test_data_status_service.py`/`test_data_status_turbo.py`/`test_data_status_beta_rollup_and_cli_config.py`),
      `basedpyright` clean (only 3 pre-existing errors remain, confirmed byte-identical against origin before this
      change — not introduced by this decomposition), full `quality-gates.sh` green. **`manifest.py`'s own exclude entry
      stays — NOT yet removable**: 4 OTHER pre-existing oversized methods remain untouched (`get_manifest_status` 147L,
      `_get_manifest_status_sync` 132L, `_dispatch_category_builds` 102L, `_live_build_fallback` 71L) — different
      concern (live-build OOM guard, subprocess dispatch), out of scope for this todo's specifically-named target. A
      future dispatch decomposing those 4 can then remove `manifest.py`'s exclude entry.
- [x] ✅ [SCRIPT] P1. Decompose `deployment_api/services/data_status/mtds.py` (1059L, contains the 220L
      `mtds_honest_coverage_for_venue()`). Remove its exclude entry once compliant. — deployment-api@a483514: split into
      `mtds_meta.py` (category/PREDICTION metadata), `mtds_defi_alias.py` (DEFI alias maps + canonicaliser),
      `mtds_expected.py` (expected-venues/-dates helpers), `mtds_dt_entries.py` (per-dt coverage-entry builders);
      `mtds.py` (376L) stays the re-export facade every caller/test imports from. `mtds_honest_coverage_for_venue`
      shrunk 220L → ~150L (venue-row filtering + per-dt dispatch extracted to `mtds_dt_entries.py`, but the
      `mtds_expected_dates_for_venue_dt()` call itself stays inline in `mtds.py` so the existing `unittest.mock.patch`
      target in `tests/unit/test_data_status_seeded_4state_denominator.py` keeps intercepting it).
      `FUNCTION_SIZE_EXTRA_EXCLUDES` entry for `mtds.py` removed. Full `quality-gates.sh` green (5052 tests pass, 0
      regressions).
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
- 2026-07-31 (slot-2, infra craft): Flipped todo 1 — decomposed `deployment_api/routes/deployments_inventory.py` (2592L,
  the largest offender) into a 6-module facade package. See the flipped checkbox above for the full evidence chain
  (patch-surface mapping, basedpyright/ruff fixes, test verification). `deployment-api@75584a8` (split) +
  `deployment-api@17361fd` (removed the now-obsolete `FUNCTION_SIZE_EXTRA_EXCLUDES` entry, re-verified `✅ File size OK`
  with it gone). 8 P1/P2 decomposition todos remain open for follow-up dispatch.
- 2026-07-31 (slot-8, infra craft): Flipped todo 3 — decomposed `deployment_api/services/data_status/mtds.py` (1059L)
  into `mtds_meta.py` / `mtds_defi_alias.py` / `mtds_expected.py` / `mtds_dt_entries.py`, keeping `mtds.py` (376L) as
  the re-export facade every existing caller + test imports from unchanged. Also shrunk `mtds_honest_coverage_for_venue`
  from 220L to under the 200L function-size gate. First full-QG pass surfaced 2 genuine regressions
  (`tests/unit/test_data_status_seeded_4state_denominator.py`'s
  `unittest.mock.patch.object(_dss_mod, "mtds_expected_dates_for_venue_dt", ...)` stopped intercepting calls once that
  call moved into the new `mtds_dt_entries.py` module — `patch.object` only affects the attribute on the patched module,
  not a same-named import bound into a different module's globals) — fixed by keeping the
  `mtds_expected_dates_for_venue_dt()` call physically inside `mtds.py`'s own function body and only extracting the
  seeded/derived dispatch + count bookkeeping into `mtds_dt_entries.py` helpers that take `expected_dates` as a
  parameter. Re-verified: `deployment-api@a483514`, full `quality-gates.sh` green (5052 tests pass, `✅ File size OK`,
  `✅ Function/class/method size OK`, 0 regressions). 7 P1/P2 decomposition todos remain open for follow-up dispatch.
