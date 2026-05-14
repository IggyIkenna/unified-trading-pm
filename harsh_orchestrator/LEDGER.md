---
title: Main Agent Ledger — Harsh side
type: orchestration-ledger
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Main Agent Ledger (Harsh side)

> Tracks today's slot assignments and live state. Universal mechanics and reading order → [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md). Full task briefs → today's work-split. History → `git log`.

---

## Current shift: 2026-05-14 Day-3 of density push (Wave 1 — closeout + freeze-gate eve, Harsh-side)

**Work-split**: [`plans/active/work_split_2026_05_14_harsh.md`](../plans/active/work_split_2026_05_14_harsh.md) § "Today's slot assignments"
**Model**: Sonnet 4.6 / thinking: high (all slots).
**Cycle context**: Day-3 of 4-day density push (2026-05-12 → 2026-05-15). Phase 1 freeze gate fires TOMORROW.
**Operator direction (this turn)**: spawn clear+stable Wave 1 slots first; Wave 2 (test sweeps) queued; Wave 3 (`batch_live_symmetry`) pending cross-side Ikenna handshake.

**Wave structure today**:

- **Wave 1** — slot 2/6/7/9 — clear/stable/low-risk, spawn first.
- **Wave 2** — slot 3/4 — test-fix sweeps (mechanical but bigger surface), spawn after Wave 1 in flight.
- **Wave 3** — slot 5/8 — `batch_live_symmetry` Tabs 1-3, pending cross-side handshake with Ikenna (plan `operator: ikenna`; Ikenna's PM@`e1e67656` audit asked Harsh to take Tabs 1-3 but explicit cross-side ack not yet exchanged).

| Slot | Theme (today) | State | Plan-of-record | Branch |
|------|---------------|-------|----------------|--------|
| 1 | Main orchestrator + freeze-gate monitoring + Wave 1/2/3 spawn cadence | 🟢 ONLINE | (this LEDGER + work-split) | `tab/hk/1` |
| 2 | ✅ **Wave 2 DONE** — P1.1 PoolStateResult (already fixed, RESOLVED) + P1.2 deployment-api missing dep (edce262 + PM@1d472ee9). Going quiet. | ✅ DONE Wave 2 (deployment-api@edce262 + PM@1d472ee9). Ready for reassignment. | `api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md` ✅ → `issues/pool_state_result_import_error_2026_05_13.md` ✅ | `tab/hk/2` |
| 3 | ✅ **Wave 2 DONE** — 117 UTL pipeline_mode kwarg sweep complete (utl@26ded7d). 3482 tests pass, 9 xfailed (per-family freshness; issue doc filed, owner=Ikenna). Going quiet. | ✅ DONE (utl@26ded7d). Ready for reassignment. | `unified-trading-library` pipeline_mode sweep ✅ | `tab/hk/3` |
| 4 | 🟡 **SCOPE QUESTION** — Phase 6.8 already shipped (instruments-service@27fbc90+29d511d). 28 stashed files = Phase 6.8 follow-up test-fixture sweep. Awaiting operator direction: (b) pop stash + commit cleanup, or (a/c) new assignment. | 🟡 BLOCKED — standing by for operator direction on stash@{0} "slot4-pre-rebase-instruments-2026-05-14". | `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.8 ✅ | `tab/hk/4` |
| 5 | 🟢 **Wave 3** — batch_live_symmetry Tabs 1-2 (codex docs half) | 🆕 READY TO SPAWN — worktree clean. See § "Day-3 Wave 3 task briefs — Slot 5" | `batch_live_symmetry_2026_05_10.md` Tabs 1-2 | `tab/hk/5` |
| 6 | ✅ **Wave 2 DONE** — zero-fixture bypass (instruments-service@b91b88a + PM@23c0f3b5); enrichment-preflight already fixed 2026-05-13. Going quiet. | ✅ DONE Wave 2 (instruments-service@b91b88a + PM@23c0f3b5). Ready for reassignment. | `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 6.5 ✅ → instruments-service Wave 2 ✅ | `tab/hk/6` |
| 7 | ✅ **Wave 2 DONE** — HonestCoverageCard graceful 404 (deployment-ui@365c32f); ICE softs + issue docs RESOLVED. Cron VM half still operator/Ikenna. Going quiet. | ✅ DONE Wave 2 (deployment-ui@365c32f). Ready for reassignment. | `data_status_ui_phase_2f.md` ✅ → `issues/honest_coverage_cron_vm_scheduling_2026_05_14.md` (cron VM half open) | `tab/hk/7` |
| 8 | 🟢 **Wave 3** — batch_live_symmetry Tab 3 + UAC + QG STEPs (enforcement half) | 🆕 READY TO SPAWN — worktree clean. See § "Day-3 Wave 3 task briefs — Slot 8" | `batch_live_symmetry_2026_05_10.md` Tab 3 + new QG STEP | `tab/hk/8` |
| 9 | ✅ **Day-3 continuation DONE** — peripheral scripts pipeline_mode (6 scripts fixed) + QG step 6 (validate_plan_links.py) | ✅ DONE 05:44 UTC (features-service@268919ad + market-tick-data-service@bc77f94 + PM@5c1cfc7f). Going quiet — needs new assignment if operator has work. | `writegate_honest_coverage_endtoend_2026_05_06.md` Phase 4 ✅ + strategy-service QG step 6 ✅ | `tab/hk/9` |
| 10 | (✅ DONE 2026-05-13 — yesterday's dex_perp shipped; idle today) | ✅ DONE (idle) | `dex_perp_and_venue_data_expansion_2026_05_12.md` | `tab/hk/10` |

**Wave 1 closeout** (commits on LDR for the record):
- Slot 2 ✅ DONE (PM@3b317e65) — propagation chain Gate 1 fired
- Slot 3 ✅ DONE (PM@3a16656d) — GCP 3 buckets shipped, AWS deferred Phase 2.6
- Slot 4 ✅ DONE (PM@42755747) — Phase 8A-D rescued via cherry-pick (execution-service@38b3e8a5, foot-gun #5 intercept)
- Slots 5-9 ✅ DONE (PM@3d3d5c14) — batch closure; full per-slot detail in pings/slot_N.md
- Slot 10 ✅ DONE — all in-scope tasks shipped to LDR; 4 items DEFERRED with successor annotations in `dex_perp_and_venue_data_expansion_2026_05_12.md` scoreboard PM@6090e183

**Wave 2 reset status (2026-05-13 09:35-09:40 UTC, PM@7ca204a6)**:
- Slots 2, 3, 4, 6, 7, 9 — reset clean to origin/live-defi-rollout ✅
- Slot 5 — rebase failed (collision casualty cc62f02 in MTDS); deferred to manual cleanup
- Slot 8 — UAC rebase failed (collision casualty 949185c); deferred to manual cleanup
- Slot 10 — skipped per operator (still working at reset time); finished after reset

**Cleanup queue (DONE 2026-05-13 ~11:55 UTC)**:
- ✅ Slot 5 reset: local tab/hk/5 hard-reset to LDR; cc62f02 preserved on origin/tab/hk/5
- ✅ Slot 8 reset: local tab/hk/8 hard-reset to LDR; 949185c preserved on origin/tab/hk/8
- ✅ Slot 10 foot-gun #5 intercept: MDPS@0c92b91 (19-test fix) was NOT on LDR despite slot 10's "all work synced" claim. Main cherry-picked to LDR as MDPS@c30d8e0; slot 10 worktree reset clean.

All 10 slots are now in clean known state on LDR (or as ✅ DONE for slot 10).

---

## Day-3 Wave 2 continuation — 2026-05-14 (slots 2/6/7 post-second-task)

### Slot 2 — P1 bug fixes: pool_state_result ImportError + deployment-api missing dep (Sonnet 4.6 / thinking: high)

- **Owned repos**: `execution-service` + `deployment-api` + `unified-trading-pm`
- **Issue docs**:
  - [`plans/active/issues/pool_state_result_import_error_2026_05_13.md`](../plans/active/issues/pool_state_result_import_error_2026_05_13.md) (P1 — blocks all execution-service test collection)
  - [`plans/active/issues/deployment_api_missing_position_balance_dep_2026_05_14.md`](../plans/active/issues/deployment_api_missing_position_balance_dep_2026_05_14.md) (P1 — Docker/CI broken)
- **Task**:
  1. **Fix PoolStateResult import** (execution-service): `execution_service/defi_execution/protocols/__init__.py:78` imports `PoolStateResult` which was renamed. Run `git -C execution-service log --all --oneline -20 | head -20` + `grep -r "PoolStateResult\|class.*PoolState" execution_service/` to find the new symbol name. Fix the import. Run `bash scripts/quality-gates.sh` — test collection must unblock. FF-push.
  2. **Fix deployment-api missing dep**: Add `position-balance-monitor-service` to `deployment-api/pyproject.toml` `[project.dependencies]` + `workspace-manifest.json` `deps` list for deployment-api. Run `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh` to align versions. FF-push per repo. Mark both issue docs as RESOLVED with SHAs.
- **Done-def**: execution-service `bash scripts/quality-gates.sh` step 3 (test collection) passes (no ImportError); deployment-api Docker build would succeed (verify with `cd deployment-api && bash scripts/quality-gates.sh`); both issue docs flipped to RESOLVED.
- **No big decisions needed** — diagnose-first rule applies (read function body before patching; if PoolStateResult was deleted vs renamed, that's different fixes).

### Slot 6 — instruments-service bug fixes: enrichment preflight + zero-fixture bypass (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `unified-trading-pm`
- **Issue docs**:
  - [`plans/active/issues/api_football_enrichment_preflight_runtime_mismatch_2026_05_13.md`](../plans/active/issues/api_football_enrichment_preflight_runtime_mismatch_2026_05_13.md) (P1)
  - [`plans/active/issues/orchestrator_zero_fixture_path_recovery_bypass_bug_2026_05_14.md`](../plans/active/issues/orchestrator_zero_fixture_path_recovery_bypass_bug_2026_05_14.md) (P2)
- **Task**:
  1. **Enrichment preflight fix**: Read the issue doc carefully. Locate the enrichment entry point in `instruments-service/` (grep `enrichment_mode\|preflight\|instruments.parquet`). The issue: enrichment mode entered without verifying the instruments parquet exists first. Fix: add existence check before entering enrichment path; if missing → either auto-build mapping from fixtures OR raise clear `DependencyError`. Use `Findings Triage` rule: read BOTH sides of the contract before picking fix direction. FF-push.
  2. **Zero-fixture bypass bug**: Read the issue doc. Locate `recovery_fixture_ids` usage in the orchestrator. The bug: zero-fixture fast path fires even when `recovery_fixture_ids` are provided. Fix: guard the fast path with `if not recovery_fixture_ids:`. FF-push.
  3. Mark both issue docs as RESOLVED with SHAs in body. FF-push (PM).
- **Done-def**: Both issue docs marked RESOLVED; `bash scripts/quality-gates.sh` green in instruments-service; enrichment mode doesn't crash on missing instruments.parquet.
- **No big decisions needed** — diagnose-first rule applies. Both fixes are single-repo surgical.

### Slot 7 — UAC ice_us_softs fix + honest-coverage 404 graceful UI (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-api-contracts` + `deployment-ui` + `unified-trading-pm`
- **Issue docs**:
  - [`plans/active/issues/ice_us_softs_dataset_disambiguation_2026_05_14.md`](../plans/active/issues/ice_us_softs_dataset_disambiguation_2026_05_14.md) (P2 — UAC TRADFI_ROOTS missing 6 ICE US softs)
  - [`plans/active/issues/honest_coverage_cron_vm_scheduling_2026_05_14.md`](../plans/active/issues/honest_coverage_cron_vm_scheduling_2026_05_14.md) (P2 — honest-coverage 404 shows error state instead of graceful message)
- **Task**:
  1. **ICE US softs UAC fix**: Read `unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py` (or wherever TRADFI_ROOTS lives). Add CT/CC/KC/SB/OJ/DX to TRADFI_ROOTS with `IFUS.IMPACT` venue. Fix any stale CME entries for CT. Run QG (`bash scripts/quality-gates.sh`). FF-push. Mark issue doc RESOLVED.
  2. **Honest-coverage graceful 404 in UI**: Locate the honest-coverage fetch in deployment-ui (grep `honest-coverage\|honestCoverage\|honest_coverage`). The fetch currently returns 404 when no data for the date → UI shows error state. Change: treat HTTP 404 from `/api/data-status/honest-coverage` as "data not yet computed" — show a neutral info message (`"Coverage data not yet computed for this date"`) instead of an error state. Run `pnpm build` + QG. FF-push.
  3. Update both issue docs with RESOLVED + SHAs. FF-push (PM).
- **Done-def**: TRADFI_ROOTS includes CT/CC/KC/SB/OJ/DX with IFUS.IMPACT; UAC QG green; deployment-ui shows graceful message on 404 from honest-coverage; both issue docs RESOLVED.
- **GREP-THEN-READ warning**: Read the TRADFI_ROOTS source dict body before adding — confirm CT is actually CME vs ICE before patching. Don't assume from the issue doc alone.

---

## Day-3 continuation task briefs — 2026-05-14 (slots 4/6/7/9 post-first-task)

### Slot 4 — writegate Phase 6.8 instruments-service (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `unified-api-contracts` (if seed dict missing) + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md) § "Phase 6.8 — instruments-service catalog snapshot"
- **Task**: Phase 6.8 decision = Option (a): migrate all 41 `.add()` callsites in instruments-service to `record_captured()`. Steps:
  1. `grep -rn "\.add(" instruments_service/ --include="*.py" | grep -v test | grep -v venv` — count + locate all 41 callsites.
  2. Read 3 representative callsites to understand the shape: what positional args does `.add()` receive today? Map to `record_captured(date, data_type, venue, pipeline_mode=..., shard_id=..., row_count=...)`.
  3. Sweep: replace `.add(` → `record_captured(` with correct kwargs. Add `pipeline_mode` from the CLI `--mode` arg (already wired in most instruments-service handlers).
  4. Wire `publish_with_policy` at the write boundary (same pattern as Phase 6.3 features-volatility @features-service@d7514a08 — read that commit for the template).
  5. `bash scripts/quality-gates.sh` from instruments-service root — all tests green.
  6. Plan-flip Phase 6.8 `[x]` with evidence + FF-push per shippable unit.
- **Reference**: Phase 6.3 template commit features-service@d7514a08. Phase 6.8 plan body at writegate plan line ~3458.
- **Done-def**: All 41 `.add()` callsites migrated + `publish_with_policy` wired + QG green + Phase 6.8 checkbox flipped.
- **Scope boundary**: Do NOT touch Phase 6.7 (strategy-service / execution-service / position-balance / risk) — Ikenna-owned.

### Slot 6 — writegate Phase 6.5 remaining open todos (Sonnet 4.6 / thinking: high)

- **Owned repos**: `features-service` + `unified-api-contracts` (if seed dict missing) + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md) § "Phase 6.5" — scan for `- [ ]` todos only.
- **Task**: Phase 6.5 main wiring is ✅ done. Open items are:
  1. **Sports live_handler** — `live_feature_subset` STRICT_FAIL wiring deferred per task boundary. Wire `_check_emission_policy()` in `features_service/sports/cli/handlers/live_handler.py` (same pattern as batch_handler@a93dc3b4 but for live mode path).
  2. **P2 delta-one finding** — ~24 ohlcv-derived feature_groups share NAN_FILL policy but policy not seeded individually; either verify the catch-all covers them or add explicit UAC seed entries.
  3. **P2 cross-instrument seed drift** — `paired_spec` + registry drift flag; verify `_SEEDED_FEATURE_GROUPS` dict is in sync with `features_service/cross_instrument/schemas/`.
  4. **P2 multi-timeframe ambiguity** — `intraday_regime` + `tf_risk_reward` + `wedge_confluence` cross-TF aggregate classification; verify STRICT_FAIL is correct policy per plan notes.
  - For each: grep-then-read before changing. Fix if clear; file P2 issue doc if needs design call.
  5. Run `bash scripts/quality-gates.sh` from features-service root after each fix.
  6. Plan-flip each `[ ]` todo as shipped. FF-push per unit.
- **Done-def**: All open `- [ ]` Phase 6.5 todos resolved (fixed or filed as issue doc) + QG green.
- **Scope boundary**: Do NOT touch Phase 6.6 (ml-training / ml-inference) — Ikenna-owned.

### Slot 7 — Data Status UI Phase 2F: deployment-api/UI gap fixes from 6C smoke (Sonnet 4.6 / thinking: high)

- **Owned repos**: `deployment-api` + `deployment-ui` + `unified-trading-pm`
- **Plan-of-record**: First action = create `plans/active/data_status_ui_phase_2f.md` as the plan file for these 4 gaps (referenced from cross_asset plan line ~610 but never filed). Use it as your single plan-of-record for this slot.
- **Context**: Slot 7 Day-3 Wave 1 ran the 6C UI-drilldown smoke (deployment-stack up, Data Status panel loaded) and found 4 gaps. Implement what's unambiguous; file issue doc for anything needing spec/design.
- **Task — 4 gaps, work in order**:
  1. **GAP-2 — `cross_asset` absent from breakdown/filter** (mechanical UI fix):
     - `grep -rn "asset_group\|assetGroup\|CEFI\|TRADFI\|DEFI" deployment-ui/src/ --include="*.ts" --include="*.tsx" | grep -i filter | head -20`
     - Find the filter button array that lists CEFI/TRADFI/DEFI and add `CROSS_ASSET` (or `cross_asset`). Also check deployment-api router for `/data-status` — add `cross_asset` to any hardcoded allowlist.
     - Verify: `pnpm build` in deployment-ui; `bash scripts/quality-gates.sh` in deployment-api.
  2. **GAP-3 — SPORTS/PREDICTION absent from Asset Groups filter** (mechanical UI fix, same pattern as GAP-2):
     - Add `SPORTS` + `PREDICTION` to the same filter array. Check backend asset_group allowlist too.
  3. **GAP-4 — asset group rows not interactive** (UI behavior change):
     - Find the Data Status breakdown table/component. Add `onClick` → navigate to `?asset_group=X` or existing drilldown route. If no drilldown route exists for these groups → file as issue doc (scope too large for this slot, needs route design).
  4. **GAP-1 — `GET /api/data-status/honest-coverage` → 404** (new deployment-api endpoint):
     - Grep deployment-api router files for the endpoint. If endpoint spec is clear from adjacent code (e.g., `/data-status/coverage` or `/data-status/summary` already exists and this is a variant) → implement it.
     - If spec is ambiguous (unclear response shape, unclear data source) → file issue doc with proposed spec. Do NOT guess implementation for a new public API endpoint.
- **Plan file**: Create `data_status_ui_phase_2f.md` with standard format (`estimate_class: design`, baseline ~3 AI-days, calibrated ~1.8), enumerate all 4 gaps as `- [ ]` todos, flip each as you ship.
- **Done-def**: `data_status_ui_phase_2f.md` plan created; GAP-2 + GAP-3 implemented + QG green; GAP-4 implemented OR issue doc filed; GAP-1 implemented OR issue doc filed with proposed spec. FF-push per shippable unit.
- **Scope boundary**: Do NOT touch data_status_drilldown_shard_atom_alignment plan Phase 3 (Ikenna-adjacent). Do NOT touch honest-coverage Python script (`measure_honest_coverage.py`). UI + deployment-api only.

### Slot 9 — peripheral scripts pipeline_mode fix + workspace-manifest QG step 6 investigation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `market-tick-data-service` + `features-service` + `unified-trading-library` + `instruments-service` + `strategy-service` (QG investigation only) + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md) Phase 4 (manifest writer API) + strategy-service QG step 6 flag from slot 4.
- **Task Part A — peripheral scripts pipeline_mode sweep** (mechanical):
  The following 10 scripts still call `record_captured/record_empty/record_failed/record_expected_unattempted` without `pipeline_mode` kwarg — they will fail at runtime:
  - `market-tick-data-service/scripts/mtds_reconcile_partial_bundles.py`
  - `market-tick-data-service/scripts/build_continuous_es.py`
  - `market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py`
  - `features-service/scripts/sports/features_sports_reconcile_available_at.py`
  - `features-service/scripts/sports/backfill_fixture_features_manifest.py`
  - `features-service/scripts/sports/compute_sfi_progressive_only.py`
  - `unified-trading-library/unified_trading_library/manifest_completeness.py`
  - `unified-trading-library/unified_trading_library/options_cluster_lookup.py`
  - `instruments-service/scripts/backfill_drift_funding_2026_05_13.py`
  - `unified-trading-library/unified_trading_library/manifest_freshness.py`
  For each: read the callsite → determine correct `pipeline_mode` from context (batch scripts → `PipelineMode.BATCH`; reconcilers → `PipelineMode.BATCH`) → add kwarg → commit + push per repo.
- **Task Part B — workspace-manifest QG step 6 investigation**:
  Slot 4 flagged strategy-service QG step 6 (production readiness) failing on `workspace-manifest.json`. Investigate: `cd strategy-service && bash scripts/quality-gates.sh 2>&1 | grep -A 20 "step 6\|STEP 6\|workspace-manifest"`. Determine root cause: version misalignment, missing field, or stale dep? If it's a version alignment issue: `cd unified-trading-pm && bash scripts/repo-management/run-version-alignment.sh --fix`. If code-level: fix it directly. File issue doc if diagnosis is ambiguous.
- **Done-def**: All 10 scripts updated + QG step 6 diagnosed (fixed or issue doc filed) + plan todos flipped.

---

## Day-3 Wave 1 task briefs — 2026-05-14 (clear/stable; spawn first)

### Slot 2 — api_football Phase 3.C EPL forward-poll VM + UI verify (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `deployment-service` (tarball + VM launcher) + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md`](../plans/active/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md) (Phase 3.B ✅ DONE 2026-05-13; this is Phase 3.C only)
- **Task**:
  1. Refresh VM tarball: `bash deployment-service/scripts/vm/create-code-tarballs.sh --sports-only`. Verify tarball @ `gs://deployment-scripts-${PID}/code/`.
  2. Launch EPL forward-poll VM: `bash deployment-service/scripts/vm/launch-sports-instruments-reference-vm.sh --asset-group sports --start-date 2026-05-13 --end-date 2026-05-13`. NOT a reconciliation VM — Ikenna's hold does NOT apply.
  3. Monitor execution 1-2 hours wall clock — `gs://${PROJECT_ID}-events/events/instruments-service/` for `INSTRUMENT_ENTITY_CAPTURED` events; abort on `ADAPTER_FETCH_FAILED`.
  4. Verify data-status panel schema: open deployment-ui → Data Status → Sports → Match → Fixtures → Schema modal: FIXTURE_STATS shows ~18 columns (not old 2-column schema). Screenshot.
  5. Spot-check features-sports calculator if any depend on fixture_stats (skip if no calculator exists yet).
  6. Plan-flip Phase 3.C `[x]` with VM-run evidence + screenshot. Write DONE-2026-05-14 block. FF-push per shippable unit.
- **Done-def**: Plan body Phase 3.C `[x]` flipped with VM-run evidence + screenshot + features verification (or skip-noted); api_football plan DONE-2026-05-14 block. Schema rows on UI match expected per-data_type column counts.
- **Credentials**: `gcloud secrets versions access latest --secret=api-football-api-key` (already-verified in Phase 3.B 2026-05-13).
- **No big decisions needed.**

### Slot 6 — Phase 1 freeze-gate readiness audit (Sonnet 4.6 / thinking: high; read-only audit)

- **Owned repos**: `unified-trading-pm` (output only) + workspace-wide read-only grep
- **Plan-of-record**: [`plans/active/master_to_live_defi_2026_05_23.md`](../plans/active/master_to_live_defi_2026_05_23.md) § "Phase 1 freeze-gate items status (post Day-1 EOD)" + [`writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md) Phase 4
- **Task**: For each of the 6 freeze-gate items, run workspace-wide grep + verification — confirm plan-flip matches on-disk reality. Items #3 (PipelineMode 37-callsite migration) + #6 (LookaheadBiasError strict-mode features-\*) are the two 🟡 partials from Day-2 EOD; specifically:
  1. Item #3: workspace-grep for `pipeline_mode=` at every `record_*` callsite + verify QG STEP 5.68 baseline `0 new occurrences`. If any callsite still uses default, file as P0 with file:line.
  2. Item #6: workspace-grep for `LookaheadBiasError` strict-mode wire-ins across `features-*-service/`. Verify all 8 families (delta_one / volatility / calendar / commodity / cross_instrument / multi_timeframe / onchain / sports) have `strict=True` enforcement at writer boundary.
  3. Items #1-#2, #4-#5: spot-check evidence cited in master plan against actual SHA + grep proof.
  4. Write audit report at `plans/active/issues/freeze_gate_readiness_audit_2026_05_14.md` if ANY mismatch found; OR ack as report at master plan inline + ping `harsh_orchestrator/pings/slot_6.md`.
- **Done-def**: All 6 items confirmed green-on-disk; if mismatch found, P0 issue doc filed + slot 1 main pinged.
- **No big decisions needed.**

### Slot 7 — Slot 7 Wave 4 carry-forward sweep (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-trading-system-ui` + `unified-trading-pm` + read-only on UAC + instruments-service
- **Plan-of-record**: [`plans/active/cross_asset_group_catalogue_audit_2026_05_10.md`](../plans/active/cross_asset_group_catalogue_audit_2026_05_10.md) Phase 6C + Phase 1D consumer migration
- **Task**: 3 items, ship in order:
  1. **UI `ui-reference-data.json` copies** — slot 7 Wave 4 shipped TRADER_JOEV2 producer-side migration across 3 backend repos (UAC@`da3ef9b` + instruments-service@`dd03a15` + MTDS@`3cf0f09`). Consumer side: 4 `ui-reference-data.json` copies in `unified-trading-system-ui` need the same TRADER_JOEV2/TRADERJOEV2 fix. Find via `grep -rn TRADER unified-trading-system-ui/`. Update each + run UI build smoke (`pnpm build`) to confirm no schema breakage.
  2. **6C UI-drilldown smoke** — start deployment-stack (`bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh`). Verify which UI panels work pre-cutover. Walk Data Status → cross_asset drilldown for at least 1 venue per asset_group; capture screenshots OR report gaps as issue doc.
  3. **ICE US softs (CT/CC/KC/SB/OJ/DX) dataset disambiguation** — `tradfi_symbology.py` (IFUS.IMPACT) vs `tradfi_instrument_universe.py` (GLBX.MDP3) — reconcile to single dataset per softs symbol OR file design-call issue doc with proposed dataset + reasoning.
- **Done-def**: 4 UI copies updated + build green; 6C smoke walk-through done with screenshots OR gap report; ICE US softs disambiguated or filed.
- **No big decisions needed** (DF-5 sDAI design call DEFERRED post-cutover per master plan scope; do NOT touch).

### Slot 9 — defi_recursive_borrow DESCOPE successor plan + plan-body annotation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-trading-pm` only (no code changes)
- **Plan-of-record**: [`plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`](../plans/active/defi_recursive_borrow_archetypes_2026_05_10.md) descope + new successor plan
- **Task**:
  1. Read current plan body — understand which phases are shipped vs unshipped vs partial. Per Ikenna audit batch PM@`e1e67656`: ~7% truly done (UAC half), Solidity (`RecursiveLeverageReceiver.sol`) + execution-service orchestrator + strategy-service tracer + codex + deployment-ui halves genuinely unshipped.
  2. Annotate current plan body with descope decision: "May-23 ships archetype documented; Phase 2-3 Solidity + execution halves deferred to successor". Reference master plan only commits `carry_staked_basis` + `arbitrage_price_dispersion` for May-23 live (recursive_borrow not in live cutover scope).
  3. File new successor plan `plans/active/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` (or `_2026_06_15.md`) with:
     - `migrated_from: defi_recursive_borrow_archetypes_2026_05_10.md`
     - `estimate_class: design` + `estimate_baseline_ai_days` + `estimate_calibrated_ai_days` (use Ikenna's audit estimate: Solidity + execution + strategy + codex + UI halves, multi-week scope)
     - Migrated todos with `**MIGRATED FROM:** defi_recursive_borrow_archetypes_2026_05_10.md` provenance per CLAUDE.md "Plan Archival" HARD RULE
     - Successor-plan banner on current plan
  4. Update master plan inventory dashboard line for recursive_borrow (rerun `python3 scripts/plans/regenerate_active_plan_inventory.py`).
- **Done-def**: Current plan annotated with descope decision + successor banner; successor plan filed at `plans/active/`; master plan inventory regenerated.
- **No big decisions needed** (descope decision pre-confirmed by operator this morning).

---

## Day-3 Wave 2 task briefs — 2026-05-14 (queued; spawn after Wave 1 in flight)

### Slot 3 — 117 UTL test-fixture sweep (Sonnet 4.6 / thinking: high; mechanical sweep)

- **Owned repos**: `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**: UTL@`547ff3c` API drift (file issue doc if root-cause needs design) + [`writegate_honest_coverage_endtoend_2026_05_06.md`](../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md) Phase 4 follow-up
- **Task**: UTL Phase 4.DEFAULT-REMOVAL (UTL@`547ff3c`) added `pipeline_mode` as a required kwarg to all `ManifestWriter.record_*` methods. Test fixtures across UTL test suite call the old signature → 117 test failures yesterday per slot 9's side-finding. Sweep:
  1. Use repo-local `.venv` (NOT workspace `.venv-workspace`) per CLAUDE.md venv rule. Run `bash scripts/quality-gates.sh` from `unified-trading-library/` to reproduce + count failures.
  2. Sweep tests under `unified-trading-library/tests/` — add `pipeline_mode="batch"` (or `pipeline_mode=PipelineMode.BATCH` if importing the enum) to all `record_captured` / `record_empty` / `record_failed` / `record_expected_unattempted` callsites that lack it. Scope: ~35 `record_empty` + ~37 `record_captured` + ~14 `record_failed` + ~4 `record_expected_unattempted` test callsites.
  3. Re-run QG; surface any non-mechanical failures as issue docs (file under `plans/active/issues/` with `severity: P1`).
  4. Plan-flip the writegate plan Phase 4 follow-up checkbox (if exists) OR file issue doc closing 117-test-failure side-finding.
- **Done-def**: 117 UTL tests pass via `bash scripts/quality-gates.sh`; pre-existing-foreign issues (non-mechanical) filed as issue docs with owner-tag.
- **GREP-THEN-READ warning**: before mass-replacing, read 3 sample test callsites + the UTL `record_*` signature to confirm correct kwarg name + value. Don't grep-then-replace blindly.
- **No big decisions needed.**

### Slot 4 — 2-of-17 remaining strategy-service test failures (Sonnet 4.6 / thinking: high; diagnose-first)

- **Owned repos**: `strategy-service` + `unified-trading-pm` (for issue docs if needed)
- **Plan-of-record**: strategy-service test suite (slot 4's Wave 4 carry-forward from strategy-service@`114f8b2`)
- **Task**: Slot 4 yesterday fixed 15 of 17 pre-existing strategy-service test failures at strategy-service@`114f8b2`. 2 remaining — identify which 2 from yesterday's 14:30 UTC slot 4 ping list (TestResolverFactoryCoverage + test_factory_builds_all_v1_archetypes + test_target_universe + test_coverage_uncovered_modules + test_risk_preflight_gate + test_error_handling). Apply Findings Triage HARD RULE diagnose-first principle:
  1. Use strategy-service local `.venv` (NOT workspace venv) per CLAUDE.md venv rule. Run `bash scripts/quality-gates.sh` from `strategy-service/` to identify the 2 remaining failures.
  2. For each failure: read BOTH sides of the contract (test + code-under-test). Diagnose: is code stale or is test stale per current SSOT?
  3. If code stale → fix code; if test stale → fix test; if genuinely ambiguous → file issue doc with explicit "needs design call" diagnosis.
  4. Plan-flip OR file issue.
- **Done-def**: 2 remaining strategy-service tests EITHER fixed OR filed as issue doc with explicit "needs design call" diagnosis.
- **No big decisions needed** (Findings Triage HARD RULE codified yesterday in CLAUDE.md — diagnose-first, don't just patch tests blindly).

---

## Day-3 Wave 3 — batch_live_symmetry (2026-05-14)

### Slots 5 + 8 — batch_live_symmetry Tabs 1-3 (Sonnet 4.6 / thinking: high; paired slot work)

- **Status**: ✅ CLEARED — operator override 2026-05-14. Cross-side handshake deferred; Harsh-side ownership of Tabs 1-3 confirmed by operator. Slots 5 + 8 ready to spawn fresh.
- **Owned repos**: `unified-trading-pm` (codex) + `unified-api-contracts` + per-service test wiring
- **Plan-of-record**: [`plans/active/batch_live_symmetry_2026_05_10.md`](../plans/active/batch_live_symmetry_2026_05_10.md) Tabs 1-3

---

### Day-3 Wave 3 task briefs — Slot 5 (batch_live_symmetry Tabs 1-2)

**Model**: Sonnet 4.6 / thinking: high
**Worktree**: `.tabs/5/` — fresh spawn, align all repos to origin/live-defi-rollout before starting
**Owned repos**: `unified-trading-pm` (codex docs) + `unified-api-contracts` (Tab 2 UAC contract)

**Scope — Tab 1 (codex SSOT batch)**:
- NEW `codex/04-architecture/cefi-batch-live.md` — per-asset-group narrative for cefi (matcher pattern + shard atomicity + venue list per pre-audit § 1 Tab 1). Cross-link to `batch-live-architecture.md` § 5.
- NEW `codex/06-coding-standards/mode-axis-discipline.md` — cartesian product table for `RuntimeMode` × `OperationalMode` × `BatchExecutionMode` × `MaturityPhase`. Anti-pattern list. Cite pre-audit § 1.
- UPDATE `codex/04-architecture/batch-live-architecture.md` — add cross-asset-group meta section + UI mode-context guidance + consolidated anti-patterns.
- UPDATE `codex/06-coding-standards/quality-gates.md` — STEP entries for L1/L2/L3/L7. Defer L4/L5/L6.
- UPDATE `codex/05-infrastructure/replay-subsystem.md` — implementation status + REPLAY_BACKSTOP_REACHED wiring note.
- UPDATE `codex/04-architecture/features-service-architecture.md` — sports + calendar live-handler timeline.
- Land 4 IN-FLIGHT REFACTOR banners at top of cross-plan target files.

**Scope — Tab 2 (UAC + UTL)**:
- Ship `unified_api_contracts/canonical/crosscutting/execution/batch_execution_mode.py` — `BatchExecutionMode` enum.
- Ship `unified_api_contracts/canonical/crosscutting/alerting/thresholds.py` — `RECON_GREEN_THRESHOLDS` dict with initial values for `carry_staked_basis` + `leveraged_funding_arb`.
- ServiceEmissionPolicy: audit existing `SERVICE_OUTPUT_POLICIES` (71 rows already shipped per slot 3 audit). Verify the 9 originally-specified entries are present; flip that checkbox if ✅.
- L7 verification sweep — confirm 3 violations at MDPS (`storage_dispatch_worker.py:49`, `output_writer_service.py:318`, `orchestration_writer.py:388`); audit 2 at UTL `domain/standardized_service.py:100,299`; produce fix-list (NOT fixes — hand to Tab 3/MDPS owner).
- J1 helper: ship design stub only at `unified_api_contracts/internal/domain/strategy_service/lifecycle.py:91-116` (wire-in deferred post-cutover per defaults #2).
- QG green on both repos before push.

**Done-def**:
- Tab 1: 2 NEW + 4 UPDATE codex docs committed to PM + pushed. 4 cross-plan banners landed. Plan checkboxes flipped.
- Tab 2: BatchExecutionMode enum + RECON_GREEN_THRESHOLDS + L7 fix-list committed to UAC + pushed. QG green.

**Pre-reads** (before any work):
1. `plans/active/batch_live_symmetry_2026_05_10.md` § Tab 1 + § Tab 2
2. `plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md` § 1.Tab1 + § 1.Tab2 + § 3 + § 7
3. `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
4. The 6 codex docs in plan frontmatter `related_codex`

---

### Day-3 Wave 3 task briefs — Slot 8 (batch_live_symmetry Tab 3)

**Model**: Sonnet 4.6 / thinking: high
**Worktree**: `.tabs/8/` — fresh spawn, align all repos to origin/live-defi-rollout before starting
**Owned repos**: `unified-trading-pm` (base-service.sh template) + all service repos touched by L1/L2/L3/L7 STEPs

**Scope — Tab 3 (QG STEPs L2/L3/L7 workspace AST sweeps)**:
- L1 + L5 DAY-1 ENABLE — add STEP entries to `scripts/quality-gates-base/base-service.sh`. Pre-flight = 0 violations so no fixes needed first.
- L2 violation fix-batch — ~21 violations across features-\*/strategy/MDPS per pre-audit § 1 Tab 3. Audit each: move-to-seam OR unify-path. Fan out to ~5 service commits; serialise commits within this slot to avoid collision per pre-audit § 7.
- L2 STEP enable — only AFTER fix-batch lands + workspace CI green.
- L3 violation fix-batch — UAC re-export RuntimeMode from UTL canonical (1 PR); `unified-trading-system-ui/context/internal-contracts/schemas/modes.py` re-export from UAC (1 PR).
- L3 STEP enable — only after fix-batch lands.
- L7 enforcement verification sweep — AST-walk every `record_captured(` callsite; ensure UTL `assert_available_at_present` fires on every write path.
- PM QG green + push after each STEP enable.

**Critical sequencing constraint**: Tab 3 depends on Tab 2's `BatchExecutionMode` enum being on LDR first (Slot 5 ships Tab 2). Check that `unified_api_contracts/canonical/crosscutting/execution/batch_execution_mode.py` exists on origin/live-defi-rollout before enabling L3 STEP. If Slot 5 is still in flight, do L1/L5/L2 work first and hold L3 until UAC is visible on LDR.

**Done-def**:
- 4 STEPs (L1+L5+L2+L3) enabled in `base-service.sh` template + rollout-propagated to all service repos.
- L2 fix-batch: ~5 service commits on LDR.
- L3 fix-batch: UAC + UI redeclaration replaced with re-export imports.
- L7 audit complete with fix-list issued.
- Workspace CI green for 2h continuous post-L2-enable.
- Plan checkboxes flipped per shippable unit.

**Pre-reads** (before any work):
1. `plans/active/batch_live_symmetry_2026_05_10.md` § Tab 3
2. `plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md` § 1.Tab3
3. `scripts/quality-gates-base/base-service.sh` (understand existing STEP structure)
4. `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`

---

## 2026-05-13 PM shift end — final closeout (harsh-main, 2026-05-13 15:30 UTC ish)

**Shift status**: ✅ ALL 6 active implementor slots reported DONE. Slots 5/8/10 idle/closed; slot 1 main online.

**Per-slot final state** (all verified on LDR via commit-sha checks):

- **Slot 2** ✅ Wave 4 DONE — data_status_drilldown Phase 7 P1+P2 across deployment-{service,api,ui} (PM@531f04f3 closeout). Plan 31/41 + scoreboard.
- **Slot 3** ✅ Wave 4 DONE — execution-service C901 + 7 pre-existing test fixes (execution-service@2dee623f + @9758f9fc + @6a993bdb partial codex). Surfaced 2 issue docs for defi 604,951-row finding.
- **Slot 4** ✅ Wave 4 DONE — arbitrage 20/20 + 15-of-17 pre-existing strategy-service test fixes (strategy-service@114f8b2) + sigma RUF002 + C901 refactor + service_entry --synthetic-input-uri stash-pop. BIG FINDING (defi 604k rows) now tracked in 2 issue docs.
- **Slot 6** ✅ Wave 3 DONE — wave3x_residual_ssots + per_agent_worktrees 30/30 + api_football 13/16. Reported "honest gap": LEDGER regression from Ikenna merge `634e15d9` was unflagged — fixed in this consolidated re-flip.
- **Slot 7** ✅ Wave 4 SHIFT-END DONE — TRADER_JOEV2 producer migration (3 repos: UAC@da3ef9b + instruments-service@dd03a15 + MTDS@3cf0f09) + STEP 5.72 QG ratchet (PM@fd9aee9e) + force-push recovery (UAC@e7c12fa wallet_treasury Phase 1 + UAC@861d2a6 RUF003 cherry-picked from reflog).
- **Slot 9** ✅ Wave 3 DONE — sports classifier extension (UTL@3928e3a, 52 tests) + Script 3 sports DRY-RUN (0 upgrades).

**🔴 Force-push incidents today** (4 in PM + 2 in UAC + ≥1 in instruments-service):
- Source: `semver-rollout[bot]` (Ikenna-side committer pattern). Every force-push target was a sports-flatten / sports_master commit (C.4 Transfermarkt / C.6 SPORTS_FIXTURES / C.7 STANDINGS / sports-fixtures-lifecycle).
- Operator flagged to Ikenna directly. Slot 7 cherry-picked + restored all Harsh-side work; Ikenna-side casualties (writegate Phase 6.6/6.7/6.9, data_status_drilldown Phase 7 P2, api_football Phase 3.B) handed to Ikenna-main triage.
- Each repo's reflog preserved as evidence (`git reflog origin/live-defi-rollout` shows `forced-update` markers).

**Operator-pending carry-forward** (not blocking):
1. Telegram OPS chat_id (DEFERRED-PER-USER).
2. AWS bucket creation (Phase 2.6 window 2026-05-15→19, needs GCE VM with aws CLI).
3. **117 UTL test failures** from UTL@547ff3c `ManifestWriter.record_empty()` `pipeline_mode` kwarg API drift — unassigned, Harsh-side API hardening that didn't sweep test fixtures.
4. defi 604,951 rows reclassification scope (2 issue docs filed) — awaits design call.
5. DF-5 sDAI protocol-attribution split — needs operator/ikenna design call (audit recommends MAKER consolidation; blocked by hard-asserting test at `tests/unit/test_lst_protocol_asset.py:73`).
6. Slot 6 / api_football 3 DEFERRED items — operator-executable post-cutover.
7. UI-drilldown half of cross_asset Phase 6C — needs deployment-stack live.
8. wallet_treasury_client_flow_2026_05_10.md Phase 1 was `[x]` while UAC@ca36caa was missing from LDR for hours — now consistent with UAC@e7c12fa (cherry-pick recovery).

**Cron loop (3-min poll, ID `4269c2cc`) stopped at shift end.**

**Critical-path sequencing (slot 1 monitors during Wave 2)**:
1. Slot 4 ships Script 3 classifier fix → unblocks defi/sports/prediction legacy-blank reclassification (deferred apply-flips still pending post-cutover)
2. Slot 9 ships mock_data Phase 3.D → benchmark report has real 6-stage timings (not extrapolated)
3. Slots 2/3/6/7 fully independent — run in parallel
4. New HARD RULE: LDR-alignment cadence (codified 2026-05-13 PM@f49d5f7d). Slots that boot must rebase ALL owned repos; FF-push per shippable unit, not end-of-session

**Wave 1 audit retrospective**: 3 critical follow-ups pushed PM@7ca204a6 — see `plans/active/issues/audit_wave1_quality_2026_05_13.md` for synthesis. Two impact Wave 2 spawn:
1. Slot 9 Task 3 strategy-paper VM was never actually launched in Wave 1 — re-opened in `promote_workflow_may23_cli_path_2026_05_10.md` Phase 1 as P0. Available for any slot that finishes early to absorb.
2. Sports classifier extension never shipped (slot 9 Wave 1 grep-then-conclude miss) — re-filed as `plans/active/issues/sports_classifier_extension_followup_2026_05_13.md` P1. Available for reserve pickup.

**Operator-pending**: None blocking Wave 2 spawn. Carry-forward (post-cycle operator decisions): slot 8's A/B/C UAC architecture triage (deferred; lives in cross-side `_agent_pings.md`); Telegram OPS chat_id (operator action); AWS bucket creation (Phase 2.6 window, needs GCE VM with aws CLI).

---

## Wave 2 task briefs (slot N agents — read your row)

Each row is a full task brief. After `--reset-slot N` (done 2026-05-13 09:35 UTC), your worktree at `.tabs/N/` is clean on `tab/hk/N` matching `origin/live-defi-rollout`. Just boot + read your row + start.

### Slot 2 — risk_simulations finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `risk-and-exposure-service` + `unified-api-contracts` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/risk_simulations_limits_alerting_2026_05_10.md`](../plans/active/risk_simulations_limits_alerting_2026_05_10.md) (currently 33/40 P0 = 82%)
- **Task**: Ship the 7 open P0 items:
  1. Phase 4.A — risk-and-exposure-service rule migration to UAC registry; rule_evaluator wired
  2. Phase 8.A — Per-rule synthetic-fire test (uses `simulation_scenarios_topology_price_shocks_2026_05_09`)
  3. Phase 8.B — Per-archetype suite: ≥10 rules per archetype fire on schedule + alert routes per archetype
  4. Phase 8.C — Evidence capture
  5. Phase 9.A — Master plan Group F item 20 row gains "risk rule taxonomy + pre-flight + alerting wire"
  6. Phase 9.B — Banners removed
  7. (4 P1 stablecoin items D.2/D.5/D.6/D.7 — only if time after P0s done)
- **Done-def**: 33/40 → 40/40 P0; rule_evaluator wired; per-archetype suite green; Group F item 20 flipped.
- **No big decisions needed.**

### Slot 3 — DR finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `deployment-service` + `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/disaster_recovery_circuit_breakers_2026_05_10.md`](../plans/active/disaster_recovery_circuit_breakers_2026_05_10.md) (currently 28/42 = 67%)
- **Task**: Write scripts + master-plan rows. **DO NOT LAUNCH ANY VMs** — Ikenna's hold direction on backfill/recon VMs is conservative; treat DR-drill VM launches the same and gate execution on operator OK.
  1. Phase 6.A — Cron VM `disaster-drill-cron-` launcher SCRIPT (writes only; no launch)
  2. Phase 6.B — Drill-report tooling (pass/fail per scenario; alerting rule on red >24h)
  3. Phase 9.A — Per-archetype `dr-drill-cutover-` launcher SCRIPT (arm `KILL_PER_ARCHETYPE`, etc.)
  4. Phase 9.B — Evidence-capture format
  5. Phase 10.A — Master plan rows Group F item 20 + 21 green
  6. Phase 10.B — Banners removed
- **Done-def**: 28/42 → ~38/42; SCRIPT artifacts written + linted + dry-run validated locally; ping `pings/slot_3.md` when scripts ready for operator OK to launch VMs.
- **No big decisions needed.**

### Slot 4 — 🐛 Script 3 classifier P1 + arbitrage final (Sonnet 4.6 / thinking: high)

- **Owned repos**: `instruments-service` + `unified-trading-library` + `strategy-service` + `unified-trading-pm`
- **Plans-of-record**:
  - [`plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md`](../plans/active/issues/classify_blank_reason_fixture_manifest_kwarg_2026_05_13.md) (P1 bug, slot 6 Wave-1 filed)
  - [`plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md`](../plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md) (18/20 = 90%, 2 P1 items left)
- **Task**:
  1. **Fix `classify_blank_reason_row()` `fixture_manifest` kwarg mismatch**: Read UTL `unified_trading_library.manifest.classify_blank_reason_row` signature; read `instruments-service/scripts/reconcile_legacy_blank_to_typed_reason.py` call-site; align (add `fixture_manifest` handling to reconciler OR drop from UTL — pick per which is canonical intent). FF-push.
  2. **Re-run Script 3 DRY-RUN** for defi/sports/prediction (NO `--apply-flips` — Ikenna's hold direction on manifest reconciliation VMs still applies). Update the issue doc with dry-run upgrade counts. FF-push.
  3. **Arbitrage final 2 items**: canonical BTC/USDT slot entry in strategy-service + tests (per plan-of-record line `^- \[ \]`). FF-push.
- **Done-def**: Script 3 classifier signature aligned + dry-run shows non-zero upgrades for defi/sports/prediction; arbitrage_price_dispersion 18/20 → 20/20.
- **No big decisions needed.**

### Slot 6 — wave3x_residual_ssots finalisation (Sonnet 4.6 / thinking: high)

- **Owned repos**: `unified-api-contracts` + `unified-trading-library` + per-asset_group services (as items dictate) + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/wave3x_residual_ssots_2026_05_08.md`](../plans/active/wave3x_residual_ssots_2026_05_08.md) (currently 16/22 = 73%, 6 items left across Tracks B/C/D/E)
- **Task**: Read the plan. Scan open `- [ ]` todos under Tracks B (sports per-source SSOTs) / C (reconcilers) / D (zero-activity-bar audit) / E (sports availability stamping cascade). Ship in plan order. FF-push per shippable unit.
- **Done-def**: 16/22 → 22/22; all Wave 3.X dimensions covered.
- **No big decisions needed.**

### Slot 7 — cross_asset Phase 5 TradFi consolidation (**Opus 4.7 / thinking: high** ⬆ — multi-callsite refactor)

- **Owned repos**: `unified-api-contracts` + `instruments-service` + `market-tick-data-service` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/cross_asset_group_catalogue_audit_2026_05_10.md`](../plans/active/cross_asset_group_catalogue_audit_2026_05_10.md) § Phase 5 + reference [`plans/archive/issues/catalogue_audit_tradfi_2026_05_12.md`](../plans/archive/issues/catalogue_audit_tradfi_2026_05_12.md) for TF-1..TF-10 detail
- **Task**:
  1. **Phase 5A — `tradfi_etfs.py`**: Diff-merge 4 ETF universes → single SSOT at `unified_api_contracts/canonical/domain/derivatives/tradfi_etfs.py`. Sources: `tradfi_symbology.py:459` `KNOWN_ETFS` + `tradfi_ticker_universe.py:295` `ETF_TICKERS` + `tradfi_instrument_universe.py:151` `_BTC_SPOT_ETFS`+`_ETH_SPOT_ETFS` + `TRADFI_TICKER_COVERAGE_START` ETF subset. **READ each source file body** — do not grep-then-conclude on membership equivalence. Escalate membership conflicts to operator via `pings/slot_7.md`.
  2. **Phase 5B — `tradfi_roots.py`**: Diff-merge 3 futures-roots universes (`TRADFI_INSTRUMENTS` + `TRADFI_DATABENTO_INSTRUMENTS` + `databento_cme_converter.py:57` `SUPPORTED_UNDERLYINGS`) → single SSOT.
  3. **Phase 5C — `asset_group_registry.py`**: TradFi entries point at new SSOTs.
  4. **Phase 7 (small) — VIX-15m doc-pointer fix (TF-7)**: VIX-15m constants live in `registry/data_source_continuity.py` NOT `canonical/crosscutting/honest_coverage.py` as CLAUDE.md L535 claims. Fix the doc reference in CLAUDE.md + any codex doc that mirrors the wrong pointer.
- **Done-def**: 4 ETF universes → 1 SSOT (membership diff documented in plan body); 3 futures-roots → 1 SSOT; cross_asset audit Phase 5 checkboxes flipped with evidence; VIX-15m doc-pointer corrected.
- **GREP-THEN-READ warning**: This is multi-callsite refactor. Wave 1 audit found Sonnet had grep-then-conclude failures on this exact shape (3 of 3 slots). Read each source file's actual dict/tuple contents — don't trust the variable name to imply the contents.
- **Escalated to Opus 4.7** per Wave 1 audit recommendation.

### Slot 9 — mock_data Phase 3.D per-reader threading (**Opus 4.7 / thinking: high** ⬆ — 3-reader bespoke wire-in)

- **Owned repos**: `market-tick-data-service` + `ml-inference-service` + `strategy-service` + `unified-trading-library` + `unified-trading-pm`
- **Plan-of-record**: [`plans/active/mock_data_pipeline_benchmarking_2026_05_10.md`](../plans/active/mock_data_pipeline_benchmarking_2026_05_10.md) § Phase 3.D (currently 19/29 = 66%)
- **Task**: Wire `default_subprocess_pipeline()` benchmark harness into 3 readers that bypass `resolve_bucket_uri`. For EACH reader, OPEN the function body before deciding the wire-in shape:
  1. **MTDS Tardis/Databento fetch**: External-API non-GCS readers. Needs benchmark-specific instrumentation hook (NOT standard `resolve_bucket_uri` override since these don't go through GCS).
  2. **ml-inference direct feature-vector loader**: Add bespoke `_STAGE_COMMAND_TEMPLATES` entry.
  3. **strategy direct signal+features loader**: Same pattern as (b).
  Then verify with subprocess-pipeline benchmark on 1-day batch.
- **Done-def**: mock_data 19/29 → ~25/29; Phase 3.D `[x]` flipped with shipped SHAs; benchmark report includes all 6 pipeline stages with REAL timings (currently extrapolated for these 3).
- **GREP-THEN-READ warning**: Slot 9 in Wave 1 had a grep-then-conclude failure on sports classifier. Don't repeat — open each reader's function body before declaring shape.
- **Escalated to Opus 4.7** per Wave 1 audit recommendation.

---

## Spawned tab — boot

You are slot N. Do this in order, nothing else until done:

1. Read [`AGENT_ONBOARDING.md`](AGENT_ONBOARDING.md) — git discipline, LDR-alignment HARD RULE, workspace-drift recognition, communication bus, pre-commit check, sub-agent rules.
2. Find your **Slot N task brief** in this LEDGER § "Wave 2 task briefs" above → that's your full assignment (owned repos + scope items + done-def + model tier).
3. Read your **plan-of-record** (named in your brief) — scan open `- [ ]` todos for your phase.
4. Append boot ack to [`pings/slot_N.md`](pings/) using `date -u` for timestamp, then start work.

**COMPACT-CYCLE GUARD**: Do NOT read repo-level `.claude/CLAUDE.md` files from repos you're working in — the workspace CLAUDE.md (auto-loaded in system context) covers all critical cross-cutting rules. Only read a repo's CLAUDE.md if it's explicitly named in your task brief.

---

## Default agent-spawn workflow (HARD RULE — codified 2026-05-13)

**This is the default for every wave / morning / mid-day relaunch.** Operator should NEVER receive a verbose paste-ready spawn prompt from main unless they explicitly ask for one. Task briefs live in this LEDGER § "Wave N task briefs" — agents read them from there.

**Step 1 (slot 1 main runs, background, parallel)** — reset all 6 slots in one shot:

```bash
cd /home/hk/unified-trading-system-repos
for n in 2 3 4 6 7 9; do
  (
    find ".tabs/$n" -maxdepth 2 -name ".git" 2>/dev/null | while read g; do
      git -C "$(dirname $g)" checkout -- . 2>/dev/null
    done
    bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot $n 2>&1 | grep -E "Resetting|complete|ERROR" | sed "s/^/[slot $n] /"
  ) &
done
wait
```

Swap the slot list `2 3 4 6 7 9` for whichever slots the operator wants to spawn this wave. The `git checkout -- .` step silently discards any leftover uncommitted state from the prior agent (usually a STARTED ack — no real work lost). Reset then rebases `tab/hk/N` cleanly onto `origin/live-defi-rollout`.

**Step 2 (operator opens N terminals)** — paste this lean prompt (swap `N`):

```
You are Harsh-side slot N. Pull origin/live-defi-rollout in unified-trading-pm, read harsh_orchestrator/LEDGER.md to find your Slot N task brief, then start working on it. If any owned repo in your worktree at /home/hk/unified-trading-system-repos/.tabs/N/ is behind LDR, fetch + rebase first. Follow harsh_orchestrator/AGENT_ONBOARDING.md for git discipline + ping mechanics + LDR-alignment HARD RULE.
```

That's it. No COMPACT-CYCLE GUARD lectures, no LDR-alignment explanations, no GREP-THEN-READ warnings inline — all that lives in `AGENT_ONBOARDING.md` (universal mechanics) and the LEDGER task brief (per-slot specifics including model tier + grep-then-read warnings on multi-callsite scopes).

**Step 3 (main monitors)** — agent reads LEDGER + plan-of-record + boots. If agent asks clarifying questions, the answer is "the LEDGER brief is the SSOT — re-read it; if still unclear, ping `pings/slot_N.md`". Don't expand the prompt; expand the LEDGER brief.

**Deviation only when operator explicitly says**: "give me a direct prompt for slot N" or "use a custom prompt for X reason". Otherwise: default workflow.

---

## Main orchestrator — fresh boot (slot 1)

Fresh main-agent chat (context window died, new session):

1. `git -C /home/hk/unified-trading-system-repos/unified-trading-pm fetch origin --quiet && git -C /home/hk/unified-trading-system-repos/unified-trading-pm log --oneline -5 origin/live-defi-rollout` — see recent origin activity.
2. `cat harsh_orchestrator/pings/slot_{2..10}.md 2>/dev/null` — intra-side pings.
3. `cat plans/active/_agent_pings.md` — cross-side pings.
4. Read this LEDGER § "Current shift" table — note each slot's state; update any SPAWN PENDING → IN FLIGHT based on ping acks.
5. Ack to operator: "Main online. Slots in flight: N. Pings: M intra / K cross. Standing by."
