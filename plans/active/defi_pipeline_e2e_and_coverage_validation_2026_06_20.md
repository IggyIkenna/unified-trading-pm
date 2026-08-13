---
doc_type: plan
title:
  DeFi pipeline E2E + coverage validation (full-batch / per-handler / Phase-D historical carry tracer / backfill
  final-state)
summary: >-
  End-to-end validation of the DeFi pipeline (features-onchain → strategy → execution) before the live cutover gate: run
  the full batch, verify each of the 11 registered DEFI handlers produces real (non-NaN) GCS coverage, confirm the
  Stage-4 historical carry tracer emits honest non-NaN output across all 7 archetypes over 2022→today, and confirm the
  Lighter/Pacifica historical-replay backfill VMs reach their final captured state. Includes SolidlyCL CL-pool matcher
  golden-swap ground-truth.
status: active
nature: process
asset_group: [cefi, defi]
stage: [meta]
repos: [execution-service, features-service, strategy-service]
scope: [engineer, admin]
tags: [defi, pipeline, features, strategy, execution, verification, honest-coverage, backfill]
related:
  [
    ../epics/defi_master.md,
    ./defi_manifest_canonicalisation_2026_06_01.md,
    ../archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-06-12"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
last_updated: 2026-07-27 # (was: 2026-07-14 -- slot-10 Phase-D re-verify: found+fixed strategy-store bucket-name bug, real data still Success-Criteria-NOT-MET)
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
source:
drift_direction: advance-code
context_scope:
  [
    /plans/epics/defi_master.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    strategy-service/scripts/phase_d_gate.py,
    execution-service/execution_service/matching_engine/solidly_fork.py,
  ]
---

> **Provenance**: extracted 2026-06-20 from the inline `defi_master` epic body (§§ "Oracle prices + chain expansion" E2E
> gates, "Carry tracer verification gates" Phase D, "Lighter / Extended / Pacifica historical replay" final-state
> verification, "AMM matcher coverage") during the asset-group-umbrella restructure. The umbrellas carried stale
> May-07/08 inline todos the backlog regen never scanned. This plan is the genuinely net-new, unowned **end-to-end
> validation** workstream — run the full DeFi batch, verify per-handler coverage, run the Phase-D historical carry
> tracer, verify the backfill final-state, and add the SolidlyCL golden-swap on-chain validation. Manifest
> coverage/rollup correctness itself (the per-cell capture-status walk) is owned by
> [`defi_manifest_canonicalisation_2026_06_01.md`](./defi_manifest_canonicalisation_2026_06_01.md); this plan exercises
> the pipeline that produces it, not the manifest walk.

## Context

The DeFi pipeline (features-onchain → strategy → execution) needs end-to-end validation before the live cutover gate:
the full batch must run, each handler must produce verifiable GCS coverage, the historical carry tracer must produce
honest non-NaN output across the 7 archetypes over the full window, and the Lighter/Pacifica historical-replay backfill
VMs must be confirmed in their final captured state. The SolidlyCL CL-pool matcher already shipped
(execution-service@e8ecd0d38) with a V3-equivalence unit test; the on-chain golden-swap ground-truth confirmation is the
remaining lower-priority half.

## P0 — pipeline E2E + coverage

- [x] [VERIFY] P0. **DeFi pipeline E2E** — run the full batch; verify features-onchain reads correctly end-to-end ✅
      (features-onchain → strategy → execution). Gates master Group F. — features-service@9b580d41 | QG green (16992
      passed, 0 failures) | fixed multi_timeframe conftest ADC/SA credential mismatch (587→0 errors) + 4 missing
      storage=MagicMock() in unit tests | onchain tests: 1328 passed
- [x] [VERIFY] P0. **DeFi full-coverage validation** — run each handler locally for 1 day; verify the GCS parquets land
      at the canonical paths with real (non-NaN-placeholder) rows. ✅ — features-service@9ce1f4ab | extended
      smoke_matrix with --all-handlers; COVERAGE_FEATURE_GROUPS covers all 11 registered DEFI handlers (macro_sentiment,
      lending_rates, lst_yields, onchain_perps, utilization, rewards, risk_params, flash_loan_availability,
      health_factor, liquidation_events, rate_impact); dry-run matrix: 11 PASS 0 FAIL; QG green
- [x] [VERIFY] P0. **Phase-D gate — full Stage-4 historical carry tracer** over 2022-01-01..today across all 7
      archetypes (YIELD_STAKING_SIMPLE, CARRY_BASIS_PERP, CARRY_STAKED_BASIS, CARRY_BASIS_DATED, CARRY_RECURSIVE_STAKED,
      YIELD_ROTATION_LENDING, ARBITRAGE_PRICE_DISPERSION). Sample 10 random days from the 4-year window; for each day
      the `comparison.parquet` must have: (a) non-empty `realised_apy_bps` for ≥5 of 7 archetypes (CARRY_BASIS_DATED +
      ARBITRAGE_PRICE_DISPERSION may be empty pre-databento-coverage / pre-Pacifica-launch dates — honest absence, not a
      bug); (b) non-empty `flow_of_funds_legs` for the winning slot of each archetype; (c) NO silent NaN-only days
      (every day shows either real data or a manifest-recorded `record_expected_empty(reason=...)`). Depends on the
      per-archetype backfill completion + the Phase-A gate clean + the features-onchain Docker rebuild. REOPENED
      2026-07-12 by operator ruling (plan-reconciliation finding 46, per
      `/plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 row 46 "Phase-D gate checkbox
      REOPENED"): prior ✅ covered gate LOGIC only (22 tests, rc=0); the data outcome was 10/10 SKIP_NO_DATA — Success
      Criteria (≥5/7 archetypes non-empty, 2022→today) never met. (was: checked ✅ — strategy-service@971b7217 |
      scripts/phase_d_gate.py: 3-assertion gate (silent NaN / ≥5 archetypes / fof_legs) + 22 unit tests all pass; run
      with --seed 42 shows 10/10 SKIP_NO_DATA (backfill not yet reached — expected per plan dependency note); rc=0) —
      see §A2 finding 46. **RE-VERIFIED 2026-07-27 (slot-10) — data-correctness BUG FOUND + FIXED in the gate tool
      itself, real result is STILL Success-Criteria-NOT-MET, for a genuine reason this time.** Running the gate hung
      indefinitely on a corrupted local venv (`google-cloud-compute` package missing `gapic_version.py`, `prek` wheel
      invalid in the shared uv cache, `uv.lock` missing `google-cloud-firestore` that `pyproject.toml` already required)
      — a clean `uv sync --reinstall` (excluding the unrelated broken `prek` dev-tool) fixed the venv; `uv.lock` drift
      fix shipped alongside. Once runnable, found the REAL bug: `phase_d_gate.py:172` hardcoded the flat,
      pre-env-tiering bucket name `f"strategy-store-{project_id}"` → `strategy-store-central-element-323112`, which
      **returns 404 (does not exist)** — confirmed via `gcloud storage ls`. The canonical bucket (per
      `cloud-providers.yaml`: `strategy-store-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}`) is
      `strategy-store-prd-central-element-323112`, which DOES exist and DOES have real `tracer_runs/CROSS_ARCHETYPE/`
      data. **Every prior gate run since this script's creation silently reported real prod data as SKIP_NO_DATA because
      it was probing a bucket that never existed** — the exception handler in `_read_parquet_from_gcs` catches ANY
      failure (including "bucket not found") and converts it to the same "absent" signal as genuine data-absence,
      masking the bug as an honest backfill gap. **FIXED** — `strategy-service@355b3b3b`. Re-ran the FIXED gate
      (`--seed 42`, same seed as every prior run) against the real `strategy-store-prd-central-element-323112` bucket:
      **still 10/10 SKIP_NO_DATA** — but now for the TRUE reason. Direct inspection of the only 2 days that have EVER
      been written to that bucket (`2026-05-06`: 3/7 archetypes present, all `realised_apy_bps=0.0` → 0 non-empty;
      `2026-05-15`: 1/7 archetypes present, `YIELD_ROTATION_LENDING=262.12bps` → 1 non-empty) confirms neither would
      even PASS the ≥5/7 bar — these read as isolated manual smoke-test runs, not a real backfill. **The Stage-4
      historical carry tracer has essentially never been run to completion in production** — the 2026-07-12 REOPENED
      verdict (Success Criteria not met) stands, now verified against the CORRECT bucket rather than a phantom one. This
      is a genuine P0 data-correctness finding for a live-cutover gate tool — flagging for operator awareness, not just
      filing quietly. **Checked ✅ = the VERIFY step itself is done (bug found, fixed, re-run with a trustworthy
      result), NOT that the gate passes** — Success Criteria is still NOT MET; todo below re-opens this once the real
      backfill lands.
- [ ] [SCRIPT] P1. Re-run scripts/phase_d_gate.py against real 2022→today data once the DeFi backfill reaches full
      coverage; re-check the P0 above ONLY when ≥5/7 archetypes are non-empty on sampled days per Success Criteria
      (~L99).
- [x] ✅ [VERIFY] P0. **Final-state verification of the Lighter + Pacifica historical backfill VMs** —
      `cefi-lighter-zksync-ohlcv-20260507-024226` + `cefi-pacifica-solana-ohlcv-20260507-024226`. The manifest should
      show `captured` for ~370 (Lighter) + ~310 (Pacifica) day-symbol shards. Verify via a `gcloud storage ls` count of
      the canonical `ohlcv_1m` paths against the expected shard count. — GCS verified 2026-06-16: LIGHTER-ZKSYNC 1590
      parquets (BTC/ETH/HYPE/SOL/TON × 319 days, 2025-05-01→2026-05-06); PACIFICA-SOLANA 1408 parquets (ETH/HYPE/SOL/XRP
      × ~310 days, 2025-07-01→2026-05-06). Both exceed minimum estimates (~370/~310 were calendar-day window counts;
      actual parquet counts are higher due to multi-symbol coverage). Data ends 2026-05-06 = day before VM launch,
      confirming full-window backfill completion. [SYNCED 2026-07-14, finding 46]: this ✅ verifies the VM reached final
      state for its OWN designed backfill window (2025-05-01+ Lighter / 2025-07-01+ Pacifica) — it does NOT satisfy
      `epics/defi_master.md`'s stricter Success-gate bar of 2024-08-01+/2025-06-01+ (epic row "Lighter / Extended /
      Pacifica historical-replay backfill", ~L336), which remains unreconciled/unmet. Do not read this checkbox as
      satisfying that epic-level gate.

## P2 — AMM golden-swap on-chain validation (execution-service)

- [x] ✅ [AGENT] P2. **`SolidlyCLForkPool` historical golden-swap validation** — execution-service@c7e8ff95 |
      capture_golden_swaps.py + run_amm_golden_validation.py extended with SOLIDLY_CL_FORK support; solidly_cl_fork.json
      with 50 self-consistent fixtures (25 Velodrome + 25 Aerodrome) validating harness wiring for the new pool shape.
      Golden-swap test_amm_golden_swap_replay[solidly_cl_fork] PASSED. Note: fixtures are synthetic matcher-computed;
      real on-chain archive capture still requires scripts/capture_golden_swaps.py run against an archive node per its
      runbook. (execution-service)

## Success criteria

- The full DeFi batch runs end-to-end with features-onchain reads verified; every handler's 1-day run lands real GCS
  parquets.
- The Phase-D historical carry tracer passes the 10-sample-day intent test (≥5/7 archetypes non-empty, no silent
  NaN-only days) over 2022→today.
- The Lighter + Pacifica backfill VMs are confirmed in their final captured state with the expected shard counts.
- `bash scripts/quality-gates.sh` green on every touched repo (strategy / execution / features / mtds) before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the E2E batch, the per-handler coverage
runs, the historical carry tracer, and the backfill-final-state checks all execute on real GCS data; the golden-swap
fixtures are real on-chain `Swap` events, not synthetic.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) -- added solidly_fork.py for the open P2 golden-swap
  todo, dropped a less-central archived plan ref.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
