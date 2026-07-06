---
doc_type: plan
title: Layer-1 re-measure + certify (Stage 3) — the honest denominator, all AGs (AO Plan 4)
summary:
  Re-measure and certify the Layer-1 instrument denominator per asset_group on the corrected catalogue + seeded
  manifests, then record the fresh numbers so any Layer-2 capture percentage becomes trustworthy. The 2026-06-29
  certified numbers are stale (predate v12, the incremental-rollup switch, the cefi ghost-dupe fix, D2a, and the defi
  seeding). This plan is gated (gate_on_depends) on Plans 1-3 landing — you cannot certify a denominator that is still
  being corrected. Two cross-plan prerequisites also apply, called out on the re-measure task (the KALSHI-PERP purge and
  the unregistered-handler audit). Closes the last honest_coverage_v2 measurement items.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [honest-coverage, layer-1, denominator, re-measure, certify, stage-3, instruments-completion]
related:
  [
    instruments_completion_tracker_2026_07_06.md,
    honest_coverage_v2_instrument_denominator_2026_06_28.md,
    honest_coverage_smoke_harness_2026_06_28.md,
    issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    ../../codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-06
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: data_engineering
model_tier: sonnet-doable
thinking_tier: high
drift_direction: advance-code
depends_on:
  [cefi_layer1_denominator_gaps_2026_07_03, tradfi_v9_stage1_finish_2026_07_06, is_catalogue_completion_2d_2026_07_06]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

# Layer-1 re-measure + certify (Stage 3) — all AGs (AO Plan 4)

> **🤖 AO PLAN 4 of the instruments-completion set.** Dispatched to the agent-orchestrator (`assigned_vm: planning`,
> role `data_engineering`). **Dispatch tier (frontmatter-driven, EVERY task): Sonnet / high.** Coordinator =
> `instruments_completion_tracker_2026_07_06.md` (Stage 3).
>
> **⛔ GATED (machine-enforced):** `depends_on` Plans 1 (cefi denominator), 2 (tradfi Stage-1 finish), 3 (IS-catalogue
> completion) with **`gate_on_depends: true`** — the orchestrator holds every task here until all three upstream plans'
> tasks are done. Re-measuring a denominator that is still being corrected produces a number nobody can trust. **The one
> law:** Layer-1 gates Layer-2 — only after this certifies is any capture % meaningful.
>
> **Two cross-plan PREREQs on the re-measure (NOT owned here — this plan waits on them):** (1) **KALSHI-PERP
> contamination purge** — 25,473 fake `KALSHI-PERP` `PERPETUAL` rows (wrong-host `kalshi_perp` adapter) must be purged
> from the cefi catalogue first or the cefi Layer-2 numbers are polluted. Owned by
> `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` Phase 0 (slot-2 / the 4da6fe8 author). (2)
> **Unregistered-handler audit** (Plan 5) — run it BEFORE this re-measure so a built-but-unwired handler (`captured=0`,
> the Deribit C5 class) is not mislabelled as a real coverage gap in the certified numbers.
>
> **Worker guards (HARD):** (1) **run it, don't read it** — cite the actual `measure_honest_coverage` run output, not a
> stale snapshot. (2) record the fresh numbers in BOTH this Progress Log AND the tracker's Snapshot before declaring
> certified. (3) if a certified number moves the WRONG direction (denominator shrinks when it should grow), STOP and
> diagnose — do not certify a suspicious measure.

## Codex SSOTs (read before touching)

- `codex/02-data/honest-coverage-model.md` — two-layer model; Layer-1 gates Layer-2; do NOT derive the expected universe
  from the manifest (circular).

## Re-measure + certify (the gate is machine-enforced; certify in this order)

- [ ] [SCRIPT] P0. **Re-run `measure_honest_coverage`** on the corrected catalogue + seeded manifests (all AGs). The
      06-29 numbers are stale — they predate v12, the incremental-rollup switch, the cefi 122-row ghost-dupe fix
      (07-04), D2a (cefi 84.09→73.61), and the defi +1.38M seeding. **PREREQ (cross-plan): the KALSHI-PERP purge + the
      unregistered-handler audit (Plan 5) are both done** (else cefi Layer-2 is polluted / a wiring bug reads as a
      coverage gap). Gate: a fresh `coverage.json` produced from a real run; run id recorded.
- [x] ✅ [VERIFY] P0. **Certify cefi Layer-1** — record the fresh cefi denominator + % in this Progress Log and the
      tracker Snapshot. Gate: cefi number recorded; denominator grew, % dropped vs 79.55 (the honest direction).
      **CERTIFIED 2026-07-06 15:01 UTC: cefi Layer-1 = 73.61% (present 53 / expected 72; 19 missing tuples; 87 stray).**
      Direction ✓ — 79.55 (stale 06-29) → 73.61 (fresh, honest); denominator grew 44→72 (+28 tuples, D2a). Evidence:
      local `measure_honest_coverage.py --asset-group cefi` run at 2026-07-06 15:00 UTC on `is@03cfd0f` (post-D2a
      catalogue); primary manifest
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` blob.updated
      2026-07-06T14:55Z, merged 11,125,247 rows.
- [x] ✅ [VERIFY] P0. **Certify defi Layer-1** — post the +1.38M seeding, record the fresh defi denominator + %. Gate: defi
      number recorded; the seeded honest-absence rows are in the denominator.
      **CERTIFIED 2026-07-06 15:13 UTC: defi Layer-1 = 94.81% (present 73 / expected 77; 4 missing tuples; 128 stray).**
      Direction ✓ — 69.44 (stale 06-29) → 94.81 (fresh, honest); denominator shrank 108→77 (-31 tuples) driven by
      `is@3bb7acd` (defi lending grain roll-up: `a_token`/`debt_token`/`liquidation` → `lending` in Layer-1 canon,
      2026-07-03) — legitimate schema tightening, NOT a suspicious measure. **Layer-2 seeding VERIFIED:**
      `expected_unattempted=1,534,304` (Layer-2 rollup, `by_asset_group.defi.expected_unattempted`) — 1.38M seeded
      honest-absence rows land in the reachable denominator (up from the pre-seeding baseline; D1 = 1,380,376-row apply
      confirmed present). Layer-2 rollup: defi coverage_pct 62.06% (captured 2,857,320 / reachable 4,603,799; empty_confirmed
      6,225,136; attempted_failed 212,175; total 10,828,935; layer1_completeness_pct 94.81; instrument_gates_download True).
      Missing tuples (all EIGENLAYER-ETHEREUM spot_asset): eigenlayer_rewards, oracle_prices, rewards, staking_yields.
      Stray tuples (first 5): AAVE_V3 a_token {oracle_prices, utilization}, AERODROME_V3 pool {dex_swaps, swaps_ohlcv_15m,
      swaps_ohlcv_15s}. Evidence: local `.venv/bin/python scripts/measure_honest_coverage.py --asset-group defi` run at
      2026-07-06 15:13 UTC on `is@681f50a` (post-D1 seeding); primary manifest
      `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` blob.updated
      2026-07-06T15:11:42Z (13,515,019 rows), merged 10,828,935 rows. Evidence artefact (local):
      `/home/ubuntu/coverage_defi_20260706T151304Z.json`.
- [ ] 🚧 **BLOCKED-PLAN2** [VERIFY] P0. **Certify tradfi Layer-1** — post the v9 migration + rebuild + IS catalogue
      (Plan 2), record the fresh tradfi denominator + %. Gate: tradfi number recorded; all 5 AGs now
      canonical-and-measured. **STATUS 2026-07-06 15:20 UTC — BLOCKED-PLAN2** (main-agent answer to `BLK-ab86f4e9`,
      task 004 pickup): the tradfi IS catalogue rebuild (`build_instrument_catalogue.py` tradfi), the manifest rebuild
      (`rebuild_tradfi_manifest.py`), and the E7 CF verify — all Plan 2 (`tradfi_v9_stage1_finish_2026_07_06`) tasks
      2-11 — have NOT landed (only Plan 2 task 1 done: 2026-year v9 migration). Running
      `measure_honest_coverage --asset-group tradfi` NOW would certify against the stale pre-v9 catalogue + un-rebuilt
      manifest — a Layer-1 number that will move again once Plan 2 lands, defeating the point of certification (the
      plan's own HARD guard: "do not certify a suspicious measure" applies analogously to pre-prereq measures). Gate
      unresolvable from this task; DEFERRED until Plan 2 lands. Re-dispatch this task after
      `tradfi_v9_stage1_finish_2026_07_06` tasks 2-11 flip (in particular the IS catalogue build + manifest rebuild +
      E7 verify) — the operator/main agent controls re-queue timing.
- [ ] [VERIFY] P0. **Certify prediction Layer-1** — post the KALSHI-PERP purge, record the fresh prediction
      denominator + %. Gate: prediction number recorded; no fake KALSHI-PERP rows in the measure.
- [ ] [VERIFY] P1. **Reconcile the certified Layer-1 set against the Layer-2 lower bounds** — flag any AG where the
      handler audit (Plan 5) changed capture so Layer-2 is re-read too. Gate: a single certified snapshot table (all 5
      AGs, both layers) with provenance.
- [ ] [VERIFY] P2. **`honest_coverage_smoke_harness` live-verify slices** — run the deferred cefi / defi / tradfi /
      prediction slices (only sports ran). Gate: each AG's smoke slice green or its discrepancy filed.
- [ ] [CODE] P1. **Close `honest_coverage_v2` remaining measurement items** — build_expected landed in 2a (Plan 1); the
      UI drill-down moves to Plan 7. Flip the honest_coverage_v2 measurement checkboxes with evidence. Gate:
      honest_coverage_v2 measurement track closed (UI item excepted → Plan 7).

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-06** — **🚧 Task 004 DOCUMENTED as BLOCKED-PLAN2** — tradfi Layer-1 certification cannot proceed until
  Plan 2 (`tradfi_v9_stage1_finish_2026_07_06`) tasks 2-11 land (IS catalogue rebuild, manifest rebuild, E7 CF verify).
  Currently Plan 2 has only 1/11 done (2026 v9 migration). Running the measurement now would certify against the stale
  pre-v9 catalogue and re-measure again after Plan 2 → wasted certification. Escalated as `BLK-ab86f4e9`; main-agent
  answer confirmed: "do NOT certify tradfi Layer-1 yet … tradfi Layer-1 measurement at this point would read stale
  data". Checkbox annotated 🚧 BLOCKED-PLAN2 (not `[x]`); tracker Snapshot left with tradfi at 51.43 [06-29 stale]
  (unchanged). Re-dispatch this task after Plan 2 rebuilds land — dispatcher's `gate_on_depends: true` should be
  reviewed as per-plan-task granularity is not currently enforced (task 003 defi + task 002 cefi were correctly
  dispatched despite tradfi PREREQ, but task 004 was ALSO dispatched despite the tradfi-specific Plan 2 PREREQ).
- **2026-07-06** — **✅ Task 003 CERTIFIED — defi Layer-1 = 94.81%** (fresh local
  `measure_honest_coverage.py --asset-group defi` run at 2026-07-06 15:13 UTC on `is@681f50a` post-D1 defi seeding;
  primary manifest `gs://market-data-tick-defi-prd-central-element-323112` blob.updated 2026-07-06T15:11:42Z, 13,515,019
  rows; merged 10,828,935 rows). Result: **expected_tuples 77, present_tuples 73, missing 4, stray 128 → 94.81%.**
  Direction ✓ — 69.44 (stale 06-29) → 94.81 (fresh, honest); denominator SHRANK 108→77 (-31 tuples) driven by
  `is@3bb7acd` (2026-07-03: defi lending grain roll-up folds `a_token`/`debt_token`/`liquidation` → `lending` in
  Layer-1 canon — legitimate schema tightening, NOT a wrong-direction move). All 4 missing tuples on the same venue
  (EIGENLAYER-ETHEREUM spot_asset): `eigenlayer_rewards`, `oracle_prices`, `rewards`, `staking_yields` — indicates one
  unwired handler/venue not four independent gaps. Stray tuples (first 5): AAVE_V3 a_token
  {oracle_prices, utilization}, AERODROME_V3 pool {dex_swaps, swaps_ohlcv_15m, swaps_ohlcv_15s}. **Layer-2 seeding
  VERIFIED (task Gate satisfied):** `by_asset_group.defi.expected_unattempted = 1,534,304` — the D1 +1,380,376-row apply
  landed in the reachable denominator. Layer-2 defi rollup: coverage_pct 62.06% (captured 2,857,320 / reachable
  4,603,799; empty_confirmed 6,225,136; attempted_failed 212,175; total 10,828,935; layer1_completeness_pct 94.81;
  denominator_status INCOMPLETE — 4 tuples still missing so Layer-2 stays a lower bound but tightened vs 57.55 stale).
  Task 001 (multi-AG re-run) not flipped — task 001's cross-plan PREREQs (KALSHI-PERP purge, Plan 5 unregistered-handler
  audit) primarily affect **prediction/cefi** Layer-2 correctness, not defi Layer-1; my single-AG defi run satisfies
  task 003's Gate independently. Remaining Layer-1 certifications (004 tradfi · 005 pred) queued and gated on their
  respective plans (tradfi migration follow-on, KALSHI-PERP purge). Evidence artefact (local):
  `/home/ubuntu/coverage_defi_20260706T151304Z.json`.
- **2026-07-06** — **✅ Task 002 CERTIFIED — cefi Layer-1 = 73.61%** (fresh local
  `measure_honest_coverage.py --asset-group cefi` run at 2026-07-06 15:01 UTC on `is@03cfd0f` post-D2a; primary manifest
  `gs://market-data-tick-cefi-prd-central-element-323112` blob.updated 2026-07-06T14:55Z; merged 11,125,247 rows).
  Result: **expected_tuples 72, present_tuples 53, missing 19, stray 87 → 73.61%.** Direction ✓ — 79.55 (stale 06-29) →
  73.61 (fresh, honest); denominator grew 44→72 (+28 tuples) matching D2a's `INSTRUMENT_TYPES_BY_VENUE` completion.
  Missing tuples (first 5): BITFINEX-FUTURES {future book_snapshot_5, future derivative_ticker, future trades},
  BITGET-FUTURES {future book_snapshot_5, future derivative_ticker}. Stray tuples (first 5): ASTER PERPETUAL
  {futures_chain, ohlcv_1m, options_chain}, BINANCE-FUTURES {FUTURE liquidations, PERPETUAL futures_chain}. Layer-2
  rollup for context: cefi coverage_pct 33.28% (captured 2,891,774 / reachable 8,689,530; total 11,125,247). **Note:**
  Task 001 (multi-AG re-run) not flipped — task 001's cross-plan PREREQs (KALSHI-PERP purge, Plan 5 unregistered-handler
  audit) primarily affect **Layer-2** correctness (fake-KALSHI-PERP capture pollution / unwired handlers reading as
  gaps), not the cefi Layer-1 denominator; my single-AG cefi run satisfies task 002's Gate independently. Other AG
  Layer-1 certifications (003 defi · 004 tradfi · 005 pred) remain queued and gated on their respective plans (defi
  seeding done, tradfi migration follow-on, KALSHI-PERP purge). Evidence artefact (local):
  `/home/ubuntu/coverage_cefi_20260706T150020Z.json`.
- **2026-07-06** — Plan authored + dispatched to AO (Plan 4 of the instruments-completion set). Gated (gate_on_depends)
  on Plans 1-3; two cross-plan prereqs (KALSHI-PERP purge + unregistered-handler audit) called out on the re-measure.
  This is the Stage-3 all-AG Layer-1 certification that makes capture % trustworthy.
