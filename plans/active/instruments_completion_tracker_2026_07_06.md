---
doc_type: plan
title: Instruments Completion Tracker — denominator → numerator (cefi-first, operator-driven)
summary:
  Operator-owned working tracker to drive the instruments denominator/numerator completion to done. Points at the source
  plans/issues (does NOT restate them). Holds the live Decision Gates, the dependency-ordered Stage 0–6 checklist, the
  parallel per-AG track status, the blocked/waiting register, and a Progress Log. The governing law is Layer-1
  (instrument denominator) gates Layer-2 (capture) — correct + certify the denominator, cefi-first, then complete
  capture.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, market-tick-data-service, deployment-service, deployment-api]
scope: [admin, engineer]
tags: [tracker, coordinator, honest-coverage, denominator, numerator, instruments, cefi-first, layer-1-gates-layer-2]
related:
  [
    /plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    /plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/archive/2026_07/instruments_catalogue_incremental_rollup_2026_06_29.md,
    issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    issues/cefi_universe_capture_rule_2026_06_23.md,
    issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md,
    issues/instruments_service_plan_reconciliation_2026_06_29.md,
    issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md,
    issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md,
    issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
    issues/aster_mtds_failure_count_regression_2026_07_07.md,
    issues/manifest_reprocessing_generic_utility_2026_07_07.md,
    issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
    issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md,
    issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md,
    issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md,
    issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
    issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
    issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/archive/2026_07/instruments_service_docs_consolidation_2026_07_08.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-07-06
last_updated: 2026-07-10
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
---

> **🧭 HUMAN TRACKER — operator-owned (`assigned_vm: NA`, NOT auto-dispatched).** This is the working checklist to drive
> instruments completion to done. It **points at** the source plans/issues; it does not restate them. Tick items as they
> land, record each decision in the **Decision Gates** table, and append dated notes to the **Progress Log**. The
> tracker's own `estimate_*` reflects tracker maintenance only — the tracked engineering effort lives in the source
> plans.
>
> **⚖️ The one law — Layer-1 gates Layer-2.** The instrument denominator (could-exist universe) must be certified
> 100%-honest **before** any capture (%) number means anything — enforced at runtime, not just on paper
> (`assert_defi_catalog_fresh`; sports odds only enumerate against catalogued fixtures). So the order is always:
> **correct + certify the denominator (cefi-first) → then complete capture.**

> **🟢 TradFi v9 migration APPLY DONE (2026-07-06) — all 6 years 2020-2025 `exit_code=0`, fatal=0.** The D3 fix held at
> scale (e2-standard-16 · SPOT · workers 24 · per-year chunks; memory ~6.7 GB / 64 GB per VM; `moved<planned` =
> idempotent skips of already-canonical objects). Launcher OOM-fix: **deployment-service@77cfcda**. **STILL PENDING
> (deferred → AO/Ikenna):** 2026 (held for the live CME-OHLCV capture VMs) · post-apply chain (orphan-sweep E=0 ·
> straggler re-run · `rebuild_tradfi_manifest` · IS enumerate-seed + catalogue) · Ikenna's migration sign-off (gates the
> legacy-twin bucket deletes). See Stage 1 + the Progress Log.

> **🤖 DISPATCHED TO AGENT-ORCHESTRATOR (2026-07-06) — Stages 1-6 carved into 6 role-homogeneous AO plans, all
> `assigned_vm: planning`.** **Tiering (2026-07-07): ALL 6 plans = Sonnet/high.** _(Plan 1 was Opus/max for the C2
> `_row_data_types` fix; that shipped `is@2170d9a3`, and the all-Opus spawn was thrashing the credit-limited accounts —
> a fleet-stall root cause, see `../archive/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md`. Retiered to
> Sonnet/high 2026-07-07.)_ Note: AO's effort vocabulary has **no `xhigh`**, and **`max` requires Opus** (Sonnet+`max`
> HARD-STOPs the worker self-check), so Sonnet's valid ceiling is `high`. This tracker stays the operator-owned
> coordinator (`assigned_vm: NA`); the engineering now runs on AO. Each plan carries per-task `Gate:`, `PREREQ:`
> ordering, smoke-first / stop-on-surprise guards, and `BLOCKED-OPERATOR-DECISION` / `BLOCKED-CREDENTIALS` lines (regen
> auto-skips `BLOCKED-*` so they stay visible for you, never auto-dispatched — the working agent raises them via the
> blocked-queue).
>
> | AO Plan                            | File                                                | Role             | Tier            | Stages    | Dispatch                              |
> | ---------------------------------- | --------------------------------------------------- | ---------------- | --------------- | --------- | ------------------------------------- |
> | **1** cefi denominator completion  | `issues/cefi_layer1_denominator_gaps_2026_07_03.md` | data_engineering | Sonnet / high   | 2 (cefi)  | now (unblocked)                       |
> | **2** TradFi Stage-1 finish        | `tradfi_v9_stage1_finish_2026_07_06.md`             | data_engineering | Sonnet / high   | 1         | now (parallel)                        |
> | **3** IS-catalogue completion      | `is_catalogue_completion_2d_2026_07_06.md`          | data_engineering | Sonnet / high   | 2d        | now (parallel)                        |
> | **4** Layer-1 re-measure + certify | `layer1_remeasure_and_certify_2026_07_06.md`        | data_engineering | Sonnet / high   | 3         | **gated** `gate_on_depends` Plans 1-3 |
> | **5** foundation gates + capture   | `foundation_gates_and_capture_to_100_2026_07_06.md` | data_engineering | Sonnet / high\* | 4-5       | handler-audit now; rest PREREQ Plan 4 |
> | **6** infra capture + devops       | `infra_capture_and_devops_leftovers_2026_07_06.md`  | data_engineering | Sonnet / high   | 5 (infra) | now (re-homed from infra role 07-07)  |
>
> _\*Plan 5 is the closest call — new `risk_params` handler + defi-oracle design; bump to Opus if you want a margin._
>
> **Stays OFF AO (true hard-stops — operator only):** legacy-twin bucket deletes (Ikenna's migration sign-off) ·
> locked-plan archival/fold (Stage 0 §F.4) · COINBASE/DERIBIT-COMBO `MVP_SCOPE` call · CLOB-on-chain classification ·
> paid-RPC / quota credentials. All are `BLOCKED-*` lines in the plans above (agent raises → you answer). **UI tail:**
> the honest_coverage data-status drill-down (Stage 6) is a single P2 item — too small for its own AO plan (would break
> the ≥10-item + role-homogeneity rule); stays tracked here + in `honest_coverage_v2`.

> **🔴 NEW FROM THE 2026-07-07 ASTER/CEFI AUDIT — three live, currently-unexplained findings, not yet folded into Stage
> 2/3 estimates above.** (1) **LIGHTER and PACIFICA have produced zero manifest rows of any status since 2026-06-26**
> (11 days) — found by actually running `cefi_cumulative_drawdown_guard_2026_06_27.py` against prod; see
> `issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md`. (2) **ASTER's MTDS `attempted_failed` count
> looks regressed to ~its original pre-05-14-fix state** (17,681 → 3,491 documented 06-22 → 17,675 live 07-07) — see
> `issues/aster_mtds_failure_count_regression_2026_07_07.md`. (3) **The DeFi turbo API silently reports 0/0 for venues
> with real, current captured data** (AAVE_V3-ARBITRUM: 18,771 real rows through 2026-06-21; AAVE_V3-POLYGON: 24,278;
> SPARK: 7,405, omitted entirely) — see `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`. All three are
> unassessed against this tracker's own numbers; the cefi Layer-2 37.86 and defi Layer-2 57.55 snapshots above may need
> revisiting once root-caused.

---

## ✅ Decision Gates — clear these first (only the operator can)

D1–D3 **block Stage 2**. D4–D5 are lower-urgency. Record your call + date in the last column.

| #       | Decision                                                                                                                                                                                                                                                                                                                                                                                                  | Options — **[REC]** = my recommendation                                                                                                                                                                                                     | Status            | Your call (date)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1**  | defi `expected_unattempted` seeding (≥1.38M cells never seeded → defi denominator understated + scans halt at 1M cap)                                                                                                                                                                                                                                                                                     | **A: full 1,380,376-row apply, one run [REC]** · B: 684 recent only · Other: custom `--start/--end` slice                                                                                                                                   | ✅ **DECIDED: A** | **A — full apply** (2026-07-06). Genesis-verified safe: MVP floor = CURVE 2020-01-19; per-protocol pre-genesis classification. Still to execute the apply + 3-step verify.                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **D2a** | cefi Layer-1 `(venue,itype)` gate authority (whole venues currently omitted → 79.55% is not even a bound)                                                                                                                                                                                                                                                                                                 | **switch to UAC `INSTRUMENT_TYPES_BY_VENUE` [REC]** · extend `venue_instrument_type_to_tardis` · dedicated map                                                                                                                              | ✅ **DECIDED**    | **switch to `INSTRUMENT_TYPES_BY_VENUE`** + complete the 10 missing declared venues (2026-07-06). DERIBIT-COMBO → OPTION **(CONFIRMED by Ikenna 2026-07-06 — future_combo NOT in MVP, options only)**.                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **D2b** | `VENUE_DATA_TYPE_CAPABILITIES` semantics for wholly-absent venues (BYBIT-SPOT / COINBASE-FUTURES / BINANCE-DELIVERY / KALSHI-PERP …)                                                                                                                                                                                                                                                                      | add owner-verified capability entries · codify the no-entry semantics                                                                                                                                                                       | ✅ **DECIDED**    | **complete the table properly** + codify absent = not-expected (2026-07-06).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **D3**  | TradFi v9 `--apply` OOM restart (lone AG not yet canonical)                                                                                                                                                                                                                                                                                                                                               | restart the migration VM with **lower concurrency / larger machine** (mechanical; operator-launched)                                                                                                                                        | ✅ **DECIDED**    | **`--workers 24`** (fallback 16) · **per-year chunks** 2020→2026 · **e2-standard-16** · idempotent restart (2026-07-06). Manifest schema **v9** confirmed current.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **D4**  | cefi_tick G4 gate — Layer-1 carve-out                                                                                                                                                                                                                                                                                                                                                                     | sanction as intentional Layer-2-only gate · **fold under the two-layer gate [REC]**                                                                                                                                                         | ✅ **DECIDED**    | **Fold under the two-layer gate** — ALREADY RESOLVED by Ikenna 2026-07-03 (C4 option a): G4 enforces Layer-1 AND Layer-2; cefi-MVP not honest-complete while the denominator has holes. Matches the governing law; G4 can't close until D2 (`cefi_layer1_denominator_gaps`) lands. Tracker was stale (reconciliation predated the 07-03 call).                                                                                                                                                                                                                                                                                                     |
| **D5**  | Deribit options stance (`options_chain` effectively uncaptured)                                                                                                                                                                                                                                                                                                                                           | **not a standalone decision** — capture gap, root-caused to an unregistered handler (Ikenna C5)                                                                                                                                             | ✅ **RESOLVED**   | **Not an operator fork — ROOT-CAUSED (Ikenna C5, verified in code 2026-07-06).** DERIBIT `options_chain` captured=0/1 because `DeribitOptionsChainHandler` is BUILT but NEVER REGISTERED (absent from `handlers/__init__.py` `__all__`, `main.py` import, and the operations dispatcher) → no operation invokes it → zero shards. **A re-measure alone won't move it — it's a real CAPTURE GAP.** Fix = Ikenna's 3-line MTDS handler registration (he owns it, in progress) → `deribit-options-chain` backfill (Stage 5) → THEN the honest number shows in the Stage-3 re-measure. MVP "don't widen beyond BTC/ETH `options_chain`" stance STANDS. |
| **D6**  | Shard dimension model for instruments-service: should `instrument_type` become a real breakdown axis everywhere a venue has >1 (today it only works by coincidence for single-type venues — DERIBIT has zero `instrument_types` breakdown; DERIBIT-COMBO is bolted on as a fake 4th venue instead of a sibling type)? See `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`. | **[REC] generalize `instrument_type` as a real dimension + retire the empty `VENUE_REFERENCE_DATA_CAPABILITIES` stub in favor of the already-working `reference_scope.py` mechanism** · leave as-is (accept the Deribit-options blind spot) | ✅ **DECIDED**    | **Approve generalizing `instrument_type` into a first-class breakdown axis** (2026-07-07, per `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md:389-393`; writer fix + DataStatusTab UI fix + bare-BYBIT/OKX phantom removal already shipped — corrected 2026-07-14 per `issues/instruments_remaining_work_audit_2026_07_10.md` doc-reconciliation finding 131; only downstream follow-ups (DERIBIT-COMBO venue retirement, Solana DeFi widening) remain open, not the decision gate itself).                                                                                                                          |

**Already-resolved (no action — context only):** Issue-4 UAC↔writer strays (RESOLVED 07-03, cefi 65.91→79.55) · ASTER
mode-split + C2 direction (Ikenna 07-03) · v10→v12 MVP drift (defi-only, banner text; no operational risk).

---

## 📊 Snapshot (2026-07-06)

- **Certified Layer-1 (denominator) — cefi + defi + sports + prediction CERTIFIED 2026-07-06; tradfi BLOCKED-PLAN2:**
  cefi **73.61** (72 expected / 53 present / 19 missing / 87 stray; `is@03cfd0f`, task 002) — **superseded 2026-07-07
  08:54 UTC by a newer re-measure: cefi Layer-1 = 72.60% (present 53 / expected 73, denominator +1 tuple post-uac@
  3652f99f ASTER book_snapshot_5 live-wire flip), `denominator_status=INCOMPLETE`, 20 missing / 87 stray — see
  `plans/active/issues/cefi_layer1_denominator_gaps_2026_07_03.md:200,786,790`. Corrected 2026-07-12 (finding 362, §A2
  B-queue ruling); this Snapshot header was never bumped to the fresher number (the generic Stage-3 blockquotes below
  note the 73.61%/94.81% snapshot "does not reflect" later changes, but never cited the specific 72.60% figure).** ·
  defi **94.81** (77 expected / 73 present / 4 missing / 128 stray; `is@681f50a` post-D1 seeding, denominator SHRANK
  108→77 via `is@3bb7acd` defi lending grain roll-up 2026-07-03; task 003) · **sports 30.77** (26 expected / 8 present /
  18 missing all BETFAIR odds / 24 stray; `is@ebfd11d`; task 006 side-measurement) · **prediction 66.67** (6 expected /
  4 present / 2 missing MARKET*LIFECYCLE / 17 stray; `is@6716f55` post-KALSHI-PERP-purge, denominator unchanged vs stale
  — purge was cefi-side not prediction-side; task 005) · tradfi 51.43 [06-29 stale — 🚧 BLOCKED-PLAN2 pending
  `tradfi_v9_stage1_finish` tasks 2-11]. *(Upper bounds where UAC under-specifies.)\_
- **Layer-2 lower bounds (capture) — fresh certified 2026-07-06 except tradfi:** cefi **33.28** [fresh `is@03cfd0f`;
  captured 2,891,774 / reachable 8,689,530; total 11,125,247; down from 37.86 stale as D2a expansion grew the
  denominator] · defi **62.06** [fresh post-D1 seeding; expected_unattempted 1,534,304 confirms +1.38M in denominator,
  up from 57.55 stale] · **sports 100.00** [fresh `is@ebfd11d`; captured 38,182 / reachable 38,182; attempted_failed 0;
  expected_unattempted 0; total 41,520] · pred **22.73** [fresh post-purge; captured 8,711 / reachable 38,318;
  expected_unattempted 497; up from 20.56 stale] · tradfi 88.81 [06-29 stale — BLOCKED-PLAN2].
- **DONE already:** denominator **generation** (catalogue built + self-refreshing) · Issue-4 strays · 4/5 AG v9
  `--apply` · opus-checkpoints + registry-consolidation (archived).
- **REMAINING (this tracker):** denominator **correctness + certification** → then **capture**.

---

## Stage 0 — Unblock (decisions + plan consolidation)

- [x] [DESIGN] P0. **D1–D3 decided** (see Decision Gates) — **hard gate on Stage 2** (all three decided 2026-07-06)
- [ ] [ADMIN] P1. Plan consolidation (from `issues/instruments_service_plan_reconciliation_2026_06_29.md` §F.1) —
      **REASSESSED 2026-07-06**:
  - [x] **merge `path_to_100pct` → `data_completion` = ✅ ALREADY DONE** (superseded + archived 2026-06-30;
        `data_completion` § "Folded-in from `path_to_100pct`"; only the DEDUP residual remains = the Stage-5 item).
  - [x] **flip `instruments_catalogue_incremental_rollup` → completed** — was: `⛔ DO NOT FLIP` (its lone open item was
        framed as a LIVE issue: the operator-declined tradfi catalogue-scheduler band-aid re-triggered 2026-07-03,
        tradfi `prod/catalog.parquet` stale since 2026-06-29, daily `lifecycle_catalogue_scheduler` runs killed at 3600s
        timeout). **Corrected 2026-07-12 (finding 361, §A2 B-queue ruling): already moot — the plan's own Progress Log
        shows the exact 3600s-timeout issue was root-caused + shipped 2026-07-03 and fully remediated by 2026-07-04**
        (weekly-full timeout raised to 21600s, verified green), and the plan itself flipped `status: active` →
        `complete` on 2026-07-10 (27 of 28 todos confirmed `[x]` with cited runtime evidence, 1 remaining `[ ]` non-
        blocking). This tracker's directive was never reconciled against that shipped fix; no further operator decision
        needed on this item.
  - [ ] **archive `mvp_catalogue_finalization_v10`** (0-open, done) + **fold `instruments_mtds_subset` cefi items →
        foundation** (60 open, ⚖️ REVIEW) — both `locked_by: live-defi-rollout` → **operator unlock/sign-off REQUIRED**
        (HARD RULE: locked-plan archival is never-autonomous; §F.4 ⚖️). _(Do before engineering so you don't work a plan
        you're about to retire.)_

## Stage 1 — Close the canonical manifest baseline

_(cefi + defi already canonical — they do NOT wait on this; only tradfi does.)_

- [ ] [DATA] P0. TradFi v9 G4 `--apply` — per **D3**: `--workers 24` (fallback 16) · per-year chunks 2020→2026
      (`--start-date/--end-date`) · e2-standard-16 · idempotent restart → `migration_verification_orphan_safety` V6
      closes; **all 5 AGs canonical**. Then `rebuild_tradfi_manifest.py` (E5) + IS enumerate-seed + IS catalogue for
      tradfi. **🟡 IN FLIGHT (2026-07-06): 2025 smoke VALIDATED (memory 6.7 GB / 64 GB steady, 172k candles migrating) →
      FANNED OUT 2020-2024 (6 VMs total: `canonical-migration-tradfi-*`, e2-standard-16 · SPOT · workers 24 · MTDS
      9ecd1e2; launcher fix deployment-service@77cfcda). 2026 held last (live CME-OHLCV capture VMs writing 2026).
      Post-apply: orphan-sweep E=0 + idempotent re-run for transient-503 stragglers, then `rebuild_tradfi_manifest` + IS
      enumerate-seed + IS catalogue.**
- [ ] [DATA] P1. Operator-gated legacy-twin **deletes** (defi / tradfi / pred; cefi + sports already done) in a quiet
      window

## Stage 2 — Denominator correctness (the core; cefi leads)

- [x] [CODE] P0. **2a. Land the single `build_expected` producer — ✅ DONE** (A17 — `honest_coverage_v2` Phase 1). Root
      fix; **now unblocked** (blocker archived 07-03). Bake **D2a** into it. — `instruments-service@681f50a` (canonical
      landed SHA; `a1038eef8` is the pre-quickmerge QG sentinel for the same commit) — consolidates the single public
      `build_expected(ag)` EXPECTED-universe producer, routing `check_enumeration_completeness` +
      `measure_honest_coverage` through it.
- [ ] [CODE] P0. **2b. cefi gate-authority fix on `build_expected`** (`issues/cefi_layer1_denominator_gaps`): apply
      D2a/D2b → ASTER live-forward split (**enumerator `start_date` support is a hard prereq before the UAC capability
      flip**) → BYBIT-SPOT `PERPETUAL` relabel → C2 MVP-data-type intersection
- [ ] [DATA] P0. **2c. cefi capture-rule residual** (`issues/cefi_universe_capture_rule`) — **REASSESSED (opus,
      2026-07-06)**: **cap-drop = ✅ ALREADY DONE `is@0fe8e71` (06-23)** (`_passes_asset_filter` now applies only
      accepted-quote + BTC/ETH- options gates; full-universe enumeration verified). **Reclassification `--apply` = ⛔ DO
      NOT RUN — RE-SCOPED.** The `reclassify_cefi_manifest_mvp_universe_2026_06_23.py` script is unsafe + superseded:
      (a) `_derive_base` DATA-LOSS bug — mis-parses Bitfinex `ADAF0:USTF0` + Kraken `PF_/PI_` wire-forms → would DELETE
      ~380k+ legit in-MVP **captured** BITFINEX/KRAKEN rows; (b) architecturally superseded (honest-coverage-v2 forbids
      deriving the denominator from the manifest — circular); (c) collides with the in-flight ASTER split (461k empty→EU
      flips are ASTER `SOURCE_RETURNED_ZERO`); (d) the 6 "stale" venues are ALREADY in the manifest with real data. It
      already ran 2× on 06-23 (snapshots exist — "never confirmed run" resolved). **→ retire the manifest-pruning
      script; do the MVP filter as a read-time gate in `measure_honest_coverage` folded into 2a `build_expected`,
      sequenced after 2b + the ASTER split.**
  - [ ] [CODE] P1. Fix `_fetch_earliest_funding_date`
        (`instruments-service/instruments_service/reference_data/adapters/cefi/aster.py:247-267`) to exclude the
        synthetic pre-launch placeholder funding rows (flat `0.0001` rate) before deriving `available_from_datetime` —
        otherwise ASTER's per-instrument genesis can still stamp a spuriously pre-2023-07-22 date even though the
        venue-level fallback is correct. Found 2026-07-07 audit.
  - [ ] [DATA] P1. Reconcile ASTER's `trades` genesis cross-registry contradiction (2021-08-30 in
        `expected_start_dates.yaml` vs. 2023-07-22 everywhere else) — see GAP 4 in
        `issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`. Do before any pre-funding-genesis trades
        backfill for ASTER.
- [ ] [DATA] P0. **2d. IS-catalogue completion `B0→B1→B2`** (`instruments_mtds_subset`): backfill instruments to
      no-missing (B0) → regen catalogue + un-pause daily schedulers (B1) → codify MVP-vs-total universe (B2). _B0 gates
      every expected-universe consumer._
- [x] [DATA] P0. **2e. defi seeding apply (D1) — ✅ DONE** (opus, run_id `enum-universe-defi-20260706-130616`):
      **+1,380,376 typed `empty_confirmed` rows** (per-year matches the issue to the row: 2018=695,830 / 2019=683,862 /
      2021-25=684), `expected_unattempted` +0 (zero downloads), fresh full-window scan **→ 0 candidates** (≥1M
      enumerator halt cleared), consolidator merged into the canonical defi manifest. Scan-gate hit EXACTLY 1,380,376 +
      1-day smoke verified first. No enumerator edit (read/run only). **CORRECTION (2026-07-25, per
      `issues/canonical_closeout_open_questions_2026_07_18.md` C2c):** the 1,380,376-row figure above (and the 62.06%
      Layer-2 defi coverage_pct derived from it at line ~634) is the **retired v1 grain**. The v2 SSOT (locked issue
      `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`, corroborated by
      `defi_consolidated_closeout_2026_07_18.md`'s ~63.9M seed figure) puts the real DeFi `expected_unattempted` backlog
      at **~63.9M cells**, not 1.38M — this DONE checkbox and the 62.06% figure are the v1 milestone only, not the final
      denominator; the v2 backlog is open work tracked under Track-3 in
      `issues/canonical_closeout_open_questions_2026_07_18.md`.
- [ ] [VERIFY] P2. **2e follow-on** (was bundled into 2e): the cross-AG never-seeded backlog check on **cefi / tradfi /
      pred** (scan-only investigation — dispatch separately)
- [ ] [CODE] P1. **2f.** Reapply the denominator-gap model to **LIGHTER / EXTENDED / PACIFICA**

## Stage 3 — Re-measure + certify Layer-1

> **✅ PREREQUISITE CLEARED (2026-07-10, verified live) — was ⛔ blocking, added 2026-07-06.** The cefi re-measure was
> GATED on the **KALSHI-PERP contamination purge** — 25,473 fake `KALSHI-PERP` `PERPETUAL` rows (Kalshi _event
> contracts_ mis-emitted by the wrong-host `kalshi_perp` adapter, `is@4da6fe8`). Owned by
> `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` Phase 0 (→
> `plans/active/prediction_capture_incident_remediation_2026_07_06.md` Workstream B Phase 0). **Verified 2026-07-10**
> (live GCS read, not assumed):
> `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (7,219,598 rows) has **0
> `KALSHI-PERP` rows, 0 `POLYMARKET-PERP` rows** — the guarded `is-daily-enum-cefi` runs self-healed the last lingering
> 9 `captured` cells as Phase 0's own doc predicted. This specific prerequisite is CLOSED.
>
> **⛔ NEW BLOCKER (found 2026-07-10, replaces the above):** re-measuring RIGHT NOW would still produce a
> soon-to-be-stale number — a concurrently-running sibling workflow (the "instruments-audit-decisions-execution"
> dispatch, see `issues/instruments_remaining_work_audit_2026_07_10.md` Orchestration state) is actively rewriting the
> exact cefi denominator-authority files this re-measure depends on
> (`instruments_service/engine/orchestrator/venue_core.py`, `instruments_service/reference_data/factory.py`,
> `scripts/check_enumeration_completeness.py` — all mtime <10 min at time of writing, i.e. genuinely live, not stale
> WIP) implementing the OKX-SPOT venue split + Kraken FI*/FF* marker + other operator-decided denominator changes.
> Re-measuring against a mid-flight denominator would just have to be re-run once that workflow lands — **recommend
> waiting for it to quiesce (git status clean / QG green / quickmerged) before re-dispatching this task**, rather than
> burning a re-measure cycle on soon-invalid numbers.
>
> **🟡 RE-ASSESSED 2026-07-10 (later, 17:39 BST) — the specific 3-file live-edit condition above has CLOSED, but full
> quiescence still does not hold; still recommend NOT remeasuring yet.** Verified directly (not re-trusting the prior
> note): `venue_core.py` (last commit `is@e3f677d6`, 15:56), `factory.py` (`is@94512ec3`, 12:48), and
> `check_enumeration_completeness.py` (`is@b90bc2d9`, 14:14) are all now **clean in the working tree and match
> `origin/live-defi-rollout`** — the specific edit-in-flight this blocker cited has landed. Both dispatched sibling
> workflows the blocker names are independently confirmed **COMPLETE** in
> `instruments_remaining_work_audit_2026_07_10.md` (`wf_1e191185-1c2` 8/8 agents returned; `wf_60ecfd13-752` 6/6 agents
> returned; a 2026-07-10-later follow-up pass in that doc re-verified via git history — not self-report — that all 3
> previously "code-complete but unshipped" items (Coinbase S2 dead-branch removal, `mvp_mode` universal build, Kraken
> marker) are now landed with clean working trees). **However `git status` on `instruments-service` is NOT clean right
> now**: `scripts/migration_orphan_sweep.py` + 2 test files carry uncommitted edits (mtime 17:19, ~18 min old) matching
> the still-in-flight **tradfi orphan sweep** (`wf_60ecfd13-752` item 6: background sweep PID 22320, ~850K objects, ETA
> 1.5–2h at that session's end — PID not resolvable from this slot, so live/dead status can't be confirmed locally).
> This edit is Stage-1/tradfi-scoped (GCS orphan-vs-legitimate-infra prefix labeling), not cefi/defi/prediction/sports
> denominator logic, and tradfi's own Layer-1 was already excluded from any near-term remeasure via the pre-existing
> `BLOCKED-PLAN2` gate (task 004) — so it does not newly block a cefi/defi/prediction/sports attempt on file-conflict
> grounds. **But it does mean the tracker's own literal "git status clean" gating criterion is not yet satisfied**, and
> — separately from the file-conflict question — a real backlog of denominator-authority changes has landed since the
> 07-06 certification that the 73.61% (cefi) / 94.81% (defi) Snapshot numbers do not reflect at all: OKX-SPOT
> fold-invert (`is@300b0767`), COINBASE-CDE venue split (`uac@1cafb3c5` + `is@94512ec3`), DERIBIT-COMBO added to
> `MVP_SCOPE.venues` + D10 capability fixes (`uac`, per the audit doc's Orchestration state), the cefi writer
> instrument_type-split fix (07-07), and the UAC two-layer data-type-validity redesign (`uac@fa9cece5`). Net: a fresh
> remeasure right now would be **more honest than a file-conflict risk, but still premature** against the tracker's own
> stated bar, and would not be a single-dispatch-safe action to launch unattended — **recommend the operator (or the
> next dedicated Stage-3 dispatch) confirm the tradfi orphan sweep has actually finished + the tree is clean, then
> re-run `measure_honest_coverage` for cefi/defi/prediction at minimum** (tradfi stays `BLOCKED-PLAN2` regardless). No
> code touched, no measurement run, in reaching this assessment — verification was git-log/git-status/file-mtime only,
> cross-checked against `issues/instruments_remaining_work_audit_2026_07_10.md`'s independently-verified Orchestration
> state.
>
> **🟡 RE-CONFIRMED 2026-07-10 (17:43 BST, independent re-check) — quiescence STILL does not hold; evidence is now
> stronger, not weaker.** Re-verified from scratch rather than trusting the 17:39 note: the 3 denominator-authority
> files (`venue_core.py` `is@e3f677d6`, `factory.py` `is@94512ec3`, `check_enumeration_completeness.py` `is@b90bc2d9`)
> are unchanged and still clean/matching `origin/live-defi-rollout` — that specific blocker remains closed. But
> `instruments-service` `git status` is **actively dirty right now, not just stale-uncommitted**:
> `scripts/migration_orphan_sweep.py` (mtime 17:41:59) and `tests/scripts/test_migration_orphan_sweep.py` (mtime
> 17:42:07) are both **<120s old at time of this check (17:43:27)** — inside the workspace's own live-claim liveness
> window (`per-tab-worktrees.md`: mtime<120s → PROTECT, do not touch) — plus a file rename in progress
> (`scripts/defi_manifest_dedup_2026_07_10.py` deleted, `scripts/manifest_dedup_2026_07_10.py` added untracked). This is
> a sibling agent editing live, this instant, not idle WIP from 18 minutes ago. Confirms the 17:39 assessment's
> conclusion (still tradfi/orphan-sweep-scoped, does not newly block a cefi/defi/prediction attempt on file-conflict
> grounds, but the tracker's own "clean tree" bar is not met) and upgrades its confidence — no code touched, no
> `measure_honest_coverage` run, no files in `instruments-service` written. Not attempting the Stage-3 remeasure per the
> dispatch's own explicit instruction not to when quiescence doesn't hold.

- [ ] [SCRIPT] P0. Re-run `measure_honest_coverage` on the corrected catalogue + seeded manifests (**06-29 numbers are
      stale** — predate v12, the incremental-rollup switch, and the cefi 122-row ghost-dupe fix of 07-04)
- [ ] [VERIFY] P0. Certify per-AG Layer-1; **record fresh numbers in the Progress Log** — only now is any Layer-2 %
      trustworthy
- [ ] [VERIFY] P1. Reconcile ASTER's two disagreeing missing-date counts before certifying: the manifest cell-presence
      view says 0 missing dates (1,082 consecutive days, 2023-07-22→2026-07-07); the live turbo API says 11 missing /
      1,071 expected for the same venue+window. Confirm which methodology the re-measure adopts. Found 2026-07-07 audit,
      `issues/aster_mtds_failure_count_regression_2026_07_07.md` context.
- [ ] [CODE] P1. Close `honest_coverage_v2` remaining (build_expected done in 2a; UI drill-down → Stage 6)

## Stage 4 — Foundation gate sign-offs (formalize the spine, cefi-first)

_(`instruments_foundation_completeness` has heavy checkbox-vs-reality drift — much of G2/G3 actually ran; the work is
reconciling + signing off, not redoing.)_

- [ ] [CODE] P0. cefi **G1.2** (`record_failed` routing + 06-26 re-capture) + **G1.3 follow-up** (on-chain-CeFi-perp
      venue form). **Caveat added 2026-07-07:** this is a thin-day/50%-of-trailing-median gate, not DeFi's strict
      never-regress-below-all-time-max block — confirm with operator whether literal DeFi parity is required, or whether
      the looser threshold is the intended CeFi policy (CeFi delistings are real, expected decreases in today's active
      count, unlike DeFi's provably-monotonic contracts). See
      `issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md` for the alerting gap on top of this same
      guard, and the two currently-dark venues (LIGHTER, PACIFICA) it already missed.
- [x] [VERIFY] P0. Reconcile checkbox drift; take the formal **G2 → G5** sign-offs (cefi) — **DONE 2026-07-06** per
      `foundation_gates_and_capture_to_100_2026_07_06.md:146-159` (status: complete): G2/G3/G3b/G4 all fully **SIGNED
      OFF** with shipped SHAs; **G5 is SUB-SIGNED only** (mechanism + typed-reason discipline shipped — UAC@755c40515 +
      IS@9e6dab5 + IS@3bb7acd — but full G5 sign-off is tracked separately under
      `mvp_backfill_cefi_tick_v10_2026_06_27.md` waves, not fully closed here). Flipped with this caveat rather than a
      bare check. Corrected 2026-07-12 — doc-reconciliation autofix findings 358-360,
      `plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling. (was: `- [ ]`
      unchecked.) > **[⚠️ CORRECTION 2026-07-21, plan-reconcile]**: the "G4 ... fully SIGNED OFF" claim above is
      STALE. > `instruments_foundation_completeness_2026_06_24.md:520-527` ran a later verify-rerun (2026-07-13/14,
      finding > 105) and reversed it: gate G4 enforces Layer-1 AND Layer-2 per operator ruling C4(a) and CANNOT close
      until D2 > (`cefi_layer1_denominator_gaps`) lands — cefi Layer-1 was measured INCOMPLETE (72.60-73.61%) at that
      time. > `instruments_foundation_completeness` is the actual gate-owning plan; treat **G4 as OPEN pending D2**
      unless the > operator has re-ruled since. This tracker's own Stage 2b ("cefi gate-authority fix" / D2 item) is
      still `[ ]` > unchecked, which is internally consistent with G4 still being open — the stale claim was this one
      bullet.
- [ ] [DATA] P1. tradfi **§8 retirement purge** (4-leg GCS delete — ICE / CBOE-OPRA / VX-spread / VIX-cash) —
      **OPERATOR-CONFIRM**
- [ ] [DESIGN] P1. defi completeness **oracle** design

## Stage 5 — Capture to 100% (Layer-2 — only after Layer-1 is honest)

- [ ] [INFRA] P1. `data_completion` operator-gated items: pyth `collect-oracle-prices` launch · Live ODDS quota · MANTLE
      paid RPC · CLOB-on-chain asset_group classification (**Lighter/Pacifica/Extended-Starknet, + HYPERLIQUID/ASTER —
      operator-confirmed 2026-07-07 same hybrid pattern: CEFI holds instrument definitions, DEFI holds chain
      classification**, see `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` Update §3) ·
      rate-limit probe VM
- [ ] [DATA] P1. Reconcile the DEDUP-flagged folded-in tail (from merged `path_to_100pct`) — **do not double-run**
- [x] [CODE] P1. DeFi `risk_params` MTDS handler (193,042 EU, no handler today) — **DONE**, shipped 2026-06-24
      `market-tick-data-service@2854c0a6` (`RiskParamsHandler` + registration + 11 unit tests), with a
      dispatcher-registration regression test added 2026-07-06 `market-tick-data-service@90cd3975` per
      `foundation_gates_and_capture_to_100_2026_07_06.md:177-197` (status: complete). Corrected 2026-07-12 —
      doc-reconciliation autofix findings 358-360, `plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50
      reclassified" blanket ruling. (was: `- [ ]` unchecked.)
- [x] [CODE] P1. **Deribit `options_chain` — handler registration** (Ikenna C5; taken over from Ikenna + verified) —
      **DONE, mtds@9ecd1e29e** (QG-green + quickmerge). Registered `DeribitOptionsChainHandler` in the MTDS operations
      dispatcher (`main.py` import + `"deribit-options-chain"` key) + a regression test asserting the operation
      resolves. NOTE: the `__init__.py` `__all__` step in Ikenna's sketch was cosmetic (main.py imports handlers by full
      path) and correctly skipped. Root cause of D5's captured=0 is now closed at the code level.
- [ ] [INFRA] P1. **Deribit `options_chain` — live runner**: wire a live cron/VM to run
      `--operation deribit-options-chain` (the handler is **live/replay only — no backfill**, `process()` collects
      `date.today()`), so it actually captures BTC/ETH `options_chain` daily → then feeds the Stage-3 re-measure.
      Historical options are NOT captured by this handler (separate concern if ever needed).
- [ ] [SCRIPT] P1. **Systemic unregistered-handler audit** (generalizes the Deribit C5 bug — do BEFORE the Stage-3
      re-measure). Diff every handler class in `market-tick-data-service/.../cli/handlers/` against the `operations={…}`
      dispatcher keys in `cli/main.py` to find handlers that are **built but never wired** (silent `captured=0`, same
      class as Deribit). The MTDS QG live-coverage roll-up flags large `blocked-not-registered` counts (cefi 104 · defi
      1225 · sports 70 · tradfi 40 cells) — the audit distinguishes **built-but-unwired** (fixable like C5: register +
      test) from **genuinely-not-built** (needs a new handler / is honest-absence). Running it before the re-measure
      keeps us from mislabelling a wiring bug as a real coverage gap. Each finding → register-and-test, or file/triage.
      **Widen scope to the adapter-factory layer too** (found 2026-07-07, later same day, spot-checking RADIANT/RENZO):
      `market_tick_data_service/market_interface/factory.py` is a SEPARATE registration point from `cli/main.py`'s
      operations dispatcher. `RENZO` is fully built and registered there (`factory.py:178`, real `RenzoAdapter` class,
      real UAC capability declared) but has zero hits in `cli/main.py` or any `deployment-service/scripts/vm/` launch
      script — built, factory-wired, never actually invoked. `RADIANT` is one step further back: its subgraph IDs were
      verified working via The Graph on Arbitrum + Ethereum 2026-06-02 (`_defi.py:203-210`), but it doesn't even have a
      `factory.py` adapter entry. Neither is "shouldn't exist" clutter — both have real invested infrastructure sitting
      inert. The likely-related "defi 1225 blocked-not-registered" count above may already include these; confirm during
      the audit rather than assuming, and check `factory.py` alongside `cli/handlers/` for every DeFi protocol the audit
      finds silently zero. **Partial-completion note (2026-07-12, doc-reconciliation autofix findings 358-360,
      `plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling):** re-verification
      found this item's ORIGINAL scope (the operations-dispatcher Deribit-class audit, first 8 lines above) is DONE —
      shipped `market-tick-data-service@015abaf5` (register both handlers) + `market-tick-data-service@efd658c8`
      (regression tests) per `foundation_gates_and_capture_to_100_2026_07_06.md:77-85` (status: complete), plus a DONE
      follow-up venue-level WSFeedConnector audit (`foundation_gates_and_capture_to_100_2026_07_06.md:86-100`, filed as
      `issues/wsfeedconnector_phase35_gap_2026_07_06.md`). BUT the **"Widen scope" adapter-factory addendum above was
      appended 2026-07-07 — AFTER that shipped work — and remains OPEN**: this tracker's own Progress Log (2026-07-07,
      "round 3" entry) explicitly folds the RENZO/RADIANT/EULER_V2 adapter-factory-layer gap into "the existing
      RENZO-adjacent unregistered-handler-audit item" as a still-open "finish what's already built" case, tracked in
      `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` (not yet swept systematically). Left unchecked
      rather than flipped — the checkbox governs the item AS CURRENTLY WRITTEN (including the widen-scope addendum), and
      that portion is not evidenced done; a bare flip would overclaim. NOT auto-fixable to `[x]` under the REFUSAL
      CONTRACT (re-read partially contradicts the auto_note's "unambiguous" framing for this item).
- [ ] [CODE] P1. prediction live token-universe fix (owned by `prediction_live_clob_depth_capture_2026_07_24`, successor
      to `prediction_venue_perps_and_live_clob_depth_2026_06_20` which was split + archived 2026-07-24; live=0 today)

## Stage 6 — Hygiene (run in parallel; non-blocking)

- [ ] [ADMIN] P2. Flip stale / self-contradictory checkboxes (`instruments_mtds_subset`: `N9c`, `N5r/N6r`,
      "migrate-first 4 AGs"; `instruments_catalogue_incremental_rollup` → completed)
- [ ] [VERIFY] P2. `honest_coverage_smoke_harness`: run the deferred **cefi / defi / tradfi / prediction** live-verify
      slices (only sports ran)
- [ ] [DATA] P2. v9 `schema_version` tail re-stamp (quiet window, post fleet-drain)
- [ ] [UI] P2. data-status **UI drill-down** (last open `honest_coverage_v2` item)
- [ ] [DESIGN] P2. Delete-or-document decision on instruments-service's dead `GET /api/data-status` endpoint (zero real
      HTTP consumers, only its own unit test). See
      `issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md`.
- [ ] [CODE] P2. Build a generic manifest-reprocessing utility (11 near-identical one-off reclassify scripts written
      across instruments-service + market-tick-data-service in 8 weeks; codex's own `script-homes.md` says a recurring
      need like this should graduate to a permanent tool). See
      `issues/manifest_reprocessing_generic_utility_2026_07_07.md`.

---

## Folded-in scope 2026-07-15 (plan-reconcile §6)

- [ ] [UI] P2. Surface the drill-down/roll-up in the data-status UI (defer until the harness schema is stable; `[UI]`
      gate applies). **→ MOVED to `instruments_completion_tracker_2026_07_06.md` Stage 6 (last open `honest_coverage_v2`
      item; too small for its own AO plan, tracked as tracker hygiene singleton per operator 2026-07-06).** This plan's
      **measurement track is now CLOSED** — every Phase 0/1/2 measurement item complete; only this UI drill-down
      remains, and it is now owned by tracker Stage 6. (FOLDED IN from
      honest_coverage_v2_instrument_denominator_2026_06_28, 2026-07-15, plan-reconcile §6 operator ruling)

---

## 🚦 Parallel per-AG tracks (current gate on each)

| AG             | Canonical? | Current gate / next action                                                                          |
| -------------- | ---------- | --------------------------------------------------------------------------------------------------- |
| **cefi**       | ✅ yes     | **LEAD.** Needs D2a/D2b → Stage 2a→2c → re-measure (3) → capture (5)                                |
| **tradfi**     | ❌ no      | Blocked on **D3** (OOM restart) → Stage 1 → B0 backfill → denominator                               |
| **defi**       | ✅ yes     | Blocked on **D1** (seeding) → 2e → honest denominator                                               |
| **sports**     | ✅ yes     | **RE-HOMED** to `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` — out of this tracker |
| **prediction** | ✅ yes     | Denominator ~ok; **live=0** blocked on the prediction CLOB plan (stale IS token universe)           |

## ⛔ Blocked / waiting register

- **✅ All Stage-0 decisions DECIDED 2026-07-06** (D1 full-seed · D2a/D2b declarative gate · D3 tradfi restart).
  Remaining before execution = leaving "local" mode to run the live steps. **Ikenna's DERIBIT-COMBO reply LANDED
  2026-07-06 — OPTION-only (future_combo not in MVP); resolved below.**
- **✅ DERIBIT-COMBO `future_combo` — RESOLVED (Ikenna 2026-07-06): OPTION-only.** `future_combo` is **NOT in MVP**
  (Deribit MVP = `options_chain` only), so DERIBIT-COMBO stays `{OPTION}` in `INSTRUMENT_TYPES_BY_VENUE` — the
  provisional is now final, **no code change beyond it**. D2a fully closed; nothing further to wire for Deribit combo in
  the denominator.
- **✅ KALSHI-PERP contamination purge (25,473 fake rows) — RESOLVED, verified live 2026-07-10.** Owned by
  `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md` Phase 0 (→
  `prediction_capture_incident_remediation_2026_07_06.md` Workstream B). Live GCS read confirms 0 `KALSHI-PERP` / 0
  `POLYMARKET-PERP` rows in the cefi manifest — the guard + purge + self-heal all held. **This prerequisite no longer
  blocks Stage 3** — see the new Stage-3 header note for the current (different) blocker.
- **KALSHI-PERP / POLYMARKET-PERP real capture** — BLOCKED-CREDENTIALS: real perps live on the auth'd margin API (Kalshi
  member-rollout; Polymarket beta), not the events host. **Venues STAY declared in the cefi denominator (D2 unchanged)**
  but read as credentials-gated honest-absence until the Phase-4 prod cutover.
- **MANTLE paid RPC** — BLOCKED-CREDENTIALS (paid endpoint key → Secret Manager)
- **SFI + Transfermarkt sports keys** — BLOCKED-CREDENTIALS (subscription, not rotation)
- **cefi batch-Tardis historical (~776k cells)** — billing-gated, **permanent sanctioned exclusion** (not "open")
- **rate-limit probe** — needs a disposable-IP VM (operator-gated)
- **`source_data_latency.py` re-pin** — needs ~2 weeks of live accrual (time-gated, not a decision)

## 📓 Progress Log

- **2026-07-10 (later still, 17:43 BST)** — **Second independent re-assessment dispatch on this same tracker item —
  re-verified from scratch, did not trust the 17:39 entry below at face value.** Re-confirmed: the 3 specific
  denominator-authority files the original Stage-3 blocker named (`venue_core.py`, `factory.py`,
  `check_enumeration_completeness.py`) remain clean/unchanged since 15:56/12:48/14:14 respectively — that blocker stays
  closed. But `instruments-service`'s working tree is **actively dirty at the moment of this check, inside the
  workspace's own <120s live-claim window** (`scripts/migration_orphan_sweep.py` mtime 17:41:59, one of its test files
  mtime 17:42:07, checked at 17:43:27 — both <90s old), plus an in-progress file rename
  (`defi_manifest_dedup_2026_07_10.py` → `manifest_dedup_2026_07_10.py`). This is a sibling agent editing live, right
  now, not stale WIP — stronger, fresher evidence for the same conclusion the 17:39 entry reached (tradfi/orphan-sweep
  scoped, doesn't block a cefi/defi/prediction attempt file-conflict-wise, but the tracker's own literal "clean tree"
  criterion still isn't met). Per the dispatch's explicit instruction not to force a Stage-3 remeasure while quiescence
  doesn't hold, **did not run `measure_honest_coverage`, did not touch `instruments-service` or any sibling repo's
  code**, and did not flip any Stage 2/3/4/5 checkbox (nothing was re-measured). This item (the tracker itself) has no
  single checkbox to flip — it is the coordinator doc, not a line item; the 33/37-open count is unchanged and remains
  real. Only this doc was edited, committed directly to `unified-trading-pm` (pure `docs(plans):` change, PM-repo
  direct- push carve-out — no quickmerge needed, no code repo touched).
- **2026-07-10 (later, 17:39 BST)** — **Dispatched re-assessment of this tracker item itself (not a Stage-3 remeasure) —
  verified real current state, no engineering executed.** Confirmed live: (1) `git status` on `instruments-service`
  matches `origin/live-defi-rollout` for the 3 files the Stage-3 blocker cited as "actively rewriting" (`venue_core.py`
  `is@e3f677d6`, `factory.py` `is@94512ec3`, `check_enumeration_completeness.py` `is@b90bc2d9`) — that specific
  live-edit condition has closed. (2) Both sibling dispatched workflows the blocker names (`wf_1e191185-1c2`,
  `wf_60ecfd13-752`) are independently confirmed COMPLETE in `issues/instruments_remaining_work_audit_2026_07_10.md`,
  including a git-history-verified (not self-reported) follow-up pass confirming all previously "code-complete but
  unshipped" items actually landed. (3) `git status` is nonetheless currently NOT clean — an ~18-min-old uncommitted
  edit to `scripts/migration_orphan_sweep.py` + 2 test files, matching the still-in-flight tradfi orphan sweep (Stage 1,
  tradfi already excluded from any near-term remeasure via the pre-existing `BLOCKED-PLAN2` gate) — so the tracker's own
  literal "clean tree" bar is not yet met, even though the specific denominator-file conflict is resolved. (4) A real
  backlog of cefi/defi denominator-authority changes (OKX-SPOT split, COINBASE-CDE split, DERIBIT-COMBO MVP_SCOPE
  addition + D10 capability fixes, cefi writer instrument_type fix, UAC two-layer redesign) has landed since the 07-06
  certification that the current 73.61%/94.81% Snapshot numbers do not reflect — the Stage-3 remeasure is now MORE
  overdue than when the blocker was written, not less, but launching it unattended right now still isn't a clean
  single-dispatch action per the tracker's own stated bar. Updated the Stage-3 header blockquote with the full
  reasoning + evidence; no checkboxes flipped (nothing was actually (re)measured), no code touched in
  `instruments-service` or any sibling repo. Full detail in the Stage-3 header note above this log.
- **2026-07-07 (later same day, round 3)** — **🔴 P0 filed: `defi_turbo_api_hides_real_captured_data_2026_07_07.md`.**
  Chasing an operator hypothesis that AAVE_V3-ARBITRUM/POLYGON/EULER_V2/FLUID's `0/0` turbo readings might be a
  venue-naming mismatch: no naming mismatch was found (the write path produces the exact canonical strings), but a live
  GCS manifest read found something worse — **AAVE_V3-ARBITRUM has 18,771 real captured rows and AAVE_V3-POLYGON has
  24,278, both current through 2026-06-21, under the exact canonical key**, yet the turbo API reports both as `0/0`.
  **SPARK has 7,405 real captured rows and doesn't appear in the turbo response at all.** This is a deployment-api
  read/aggregation bug, not a capture gap — real coverage is being silently understated. EULER_V2 (both chains) and
  FLUID-ARBITRUM/PLASMA, by contrast, are confirmed genuinely zero real data anywhere — those readings are accurate.
  Also found: EULER_V2's real, Goldsky-verified-working (2026-06-02) subgraph infra has never actually been polled — a
  "finish what's already built" case, folded into the existing RENZO-adjacent unregistered-handler-audit item above.
  Scope of the read-path bug beyond these 3 venues is unknown — flagged as a P1 follow-up in the new doc, not yet swept
  systematically.
- **2026-07-07 (later same day, round 4)** — **Full ~34-venue systematic sweep of the turbo-API read-bug's true scope.**
  Found 5 more confirmed "REAL DATA HIDDEN" venues (MANTLE/PUFFER/STADER/STAKEWISE/SWELL-ETHEREUM — each ~1
  row/manifest-entry, likely liveness markers rather than real volume, but the same dashboard bug either way) plus 4
  bonus finds needing a live turbo-API cross-check (HYPERLIQUID 3.77M rows, ASTER 1.07M rows, COMPOUND_V3 233K rows,
  FLUID-ETHEREUM 690 rows). Everything else checked (BEEFY ×6 chains, IDLE ×3, KARAK ×2, RENZO ×2,
  YEARN_V3-ARBITRUM/OPTIMISM, etc.) came back genuinely empty. Folded into
  `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`.
- **2026-07-07 (writer fix implemented)** — Per operator go-ahead, ran a 3-agent pre-audit then implemented the
  CeFi/TradFi manifest writer fix in `instruments-service/instruments_service/engine/orchestrator/writers.py`
  (`_derive_instrument_type` → `_split_by_instrument_type`, one `record_captured()` call per distinct `instrument_type`
  instead of one blended call per venue×date). Confirmed this is ONE shared code path for CeFi AND TradFi (CME hits the
  identical bug live) and flagged 5 more likely-affected CeFi venues from registry evidence. Deleted the dead/broken
  `fix_manifest_venue_casing.py` one-off as a companion cleanup. Verified against today's real DERIBIT day-snapshot
  (2,965 rows → 5 correct groups: OPTION 2,586/COMBO 273/FUTURE 71/PERPETUAL 21/SPOT_PAIR 14). Quality gates green
  (153s). Shipped via quickmerge to `is@<pending sha>`. Full detail in
  `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`.
- **2026-07-07 (later same day)** — **D6/combinator docs updated with the round-2 findings; nothing new filed.** (1) The
  CEFI chains-vs-venues rendering fix (Progress Log entry two above) is now implemented + tested in code — not yet
  committed. (2) Pulling the full real `chain → venue → instrument_type → data_type` tree for DeFi found the writer-side
  blank-`instrument_type` bug isn't Deribit-only: all 7 Solana DeFi venues (DRIFT, KAMINO, MARGINFI, MARINADE, ORCA,
  RAYDIUM, SOLEND) plus CURVE-OPTIMISM have real captured data but zero `instrument_types` breakdown — same root cause,
  wider scope. (3) HYPERLIQUID/ASTER's dual CEFI+DEFI listing (both `0/0` under DEFI) is operator-confirmed intentional
  — same hybrid on-chain-CLOB pattern as Lighter/Pacifica/Extended-Starknet, folded into that existing Stage-5 item
  above rather than filed as a new finding. (4) Added Aave's `debt_token` (declared, schema-ready, zero captured rows —
  the supply side `a_token` works, the borrow side doesn't) to the combinator doc's existing DeFi-drift finding. (5)
  **Still open**: a workflow is checking whether AAVE_V3-ARBITRUM/POLYGON, EULER_V2, and FLUID's `0/0` readings are
  genuinely never-captured or a canonical-venue-naming mismatch hiding real data under a different key — will update
  once it resolves. All changes landed in `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`
  and `issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`; no new docs this round.
- **2026-07-07** — **UAC data-type-validity combinator audit — 1 new issue doc filed, scoped by operator.** Follow-up to
  the D6 shard-dimension work: asked whether UAC is a consistent SSOT for "which data_types are valid for (venue,
  instrument_type)" across all 5 asset groups. 5-way parallel audit found: **no asset group has a real combinator** —
  CEFI has a flat venue map + an asset-group-wide (not venue-wide) instrument-shape matrix patched by 3
  independently-bolted-on venue overrides; DeFi has a real `(protocol, instrument_type)` object but it's drifted from
  its own "actually captured" registry; TradFi has 3 never-joined axes producing a **live, provably-wrong cell** (CME
  and ICE get an identical `futures_chain` data_type set despite ICE having no Databento coverage). **Operator scoped
  the fix to CEFI/DEFI/TRADFI only** — Sports has no tradeable-instrument concept at all (correct as-is, not a gap) and
  Prediction's instrument is always one shape by domain nature (also correct as-is); Prediction DOES have a separate,
  smaller, unrelated gap (its flat venue map under-declares real data types). Filed
  `issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` with the CME/ICE fix flagged P1 as a
  live-wrong-answer item independent of whether the full combinator redesign is approved. No files edited beyond this
  doc + tracker pointers.
- **2026-07-07** — **ASTER/CEFI instrument-service data-status audit — 5 new issue docs filed + GAP 4 appended.**
  Operator-driven audit starting from the ASTER CEFI data-status dashboard, verified against live production APIs (not
  code-reading alone) and one real execution of `cefi_cumulative_drawdown_guard_2026_06_27.py` against prod GCS. Filed:
  (1) `issues/aster_mtds_failure_count_regression_2026_07_07.md` — 🔴 ASTER MTDS `attempted_failed` looks regressed from
  a documented 3,491 (06-22) back to 17,675 (live 07-07), near its original pre-05-14-fix total; unexplained, staleness
  ruled out. (2) `issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md` — 🔴 LIGHTER and PACIFICA have
  had zero captured data of any status since 2026-06-26 (11 days), found only by actually running the manual guard
  script (its own stdout truncates to top-40 and hides its own `total_thin` counter of 1,007 catalogue-wide collapses);
  the monotonicity guard that DOES run daily has zero alerting wired anywhere. (3)
  `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` — new Decision Gate **D6**:
  `instrument_type` is only a real breakdown dimension by coincidence today (works for ASTER because it has exactly one
  type; DERIBIT, which has 4, has zero `instrument_types` breakdown, and DERIBIT-COMBO is faked in as a 4th venue); the
  same MTDS-daily-axis-on-definitional-data mismatch was independently confirmed live for PREDICTION's
  `market_metadata`. (4) `issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md` — IS's own
  `GET /api/data-status` has zero real HTTP consumers. (5) `issues/manifest_reprocessing_generic_utility_2026_07_07.md`
  — 11 near-identical one-off reclassify scripts across 8 weeks, no generic mechanism. Also appended **GAP 4** to
  `issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`: the GAP-2 genesis sweep to 2023-07-22 never touched
  `expected_start_dates.yaml`'s `trades` entry for ASTER, which still disagrees at 2021-08-30 — flagged as live-risk
  since that file drives completion-% calculations, and as a blocker on the file's own pending pre-funding-genesis
  trades backfill todo. Separately confirmed as NOT bugs from this audit: TradFi's non-trading-day handling (already
  correct), the `2023-07-22` ASTER genesis vs. `2021-08-30` trades floor being a deliberate GAP-2 split (not solely an
  oversight — see GAP 4 for the residual it missed), and the Sports "bookmaker vs. data-source-then-league" view
  difference (a `secondary_axis` selector, not a regression). Wired into Stage 2b/3/4/6 above + D6 + the urgent-findings
  banner; none of these are yet reflected in the cefi Layer-2 37.86 snapshot number.
- **2026-07-06** — **Reconciled certified snapshot published** (via `layer1_remeasure_and_certify_2026_07_06` task 006).
  Fresh-measured sports as part of the reconciliation (never re-measured in this plan cycle previously) — sports Layer-1
  30.77% (8/26; 18 missing all BETFAIR odds; 24 stray) unchanged vs stale; sports Layer-2 100.00% (38,182/38,182
  reachable; 0 attempted_failed; 0 expected_unattempted; total 41,520). Full 5-AG reconciliation table (Layer-1 +
  Layer-2 + provenance + handler-audit-reread flags) added to `layer1_remeasure_and_certify_2026_07_06.md` under
  task 006. **Handler-audit re-read flags:** 🟡 cefi only (Deribit `DeribitOptionsChainHandler` register `mts@015abaf5`
  will move cefi L2 on next capture); defi/sports/prediction 🟢 clean; tradfi 🚧 STALE-BLOCKED-PLAN2. 73 unregistered
  venues per WSFeedConnector audit (`wsfeedconnector_phase35_gap_2026_07_06`) are honest handler-not-built gaps, NOT
  C5-class re-read triggers. All 4/5 fresh certifications retain `denominator_status: INCOMPLETE` → Layer-2 % remains a
  LOWER BOUND per the two-layer governing law. Sports evidence: `/home/ubuntu/coverage_sports_20260706T153104Z.json`.
- **2026-07-06** — **prediction Layer-1 CERTIFIED — 66.67% fresh** (via `layer1_remeasure_and_certify_2026_07_06` task
  005). Ran `measure_honest_coverage.py --asset-group prediction` locally at 2026-07-06 15:27 UTC on `is@6716f55`
  post-KALSHI-PERP-purge; primary manifest `gs://market-data-tick-pred-prd-central-element-323112` blob.updated
  2026-07-06T15:26:46Z, 760,300 rows; merged 706,197 rows. Result: **expected_tuples 6 / present_tuples 4 / missing 2 /
  stray 17 → 66.67%.** Direction ✓ — 66.67 stale (06-29) → 66.67 fresh; denominator stable at 6 (purge affected cefi
  catalogue, not prediction). **Purge Gate verified:** 0 `KALSHI-PERP` mentions + 0 `POLYMARKET-PERP` mentions in the
  prediction coverage.json (post-purge cefi state: catalogue 376,984→351,511 rows, KALSHI-PERP==0, 25→24 venues per
  `prediction_capture_incident_remediation_2026_07_06` Workstream B Phase 0). Layer-2 prediction rollup: coverage_pct
  **22.73%** (captured 8,711 / reachable 38,318; empty_confirmed 667,879; attempted_failed 29,110; expected_unattempted
  497; total 706,197; layer1_completeness_pct 66.67; denominator_status INCOMPLETE — 2 unwired MARKET_LIFECYCLE handlers
  so Layer-2 stays a lower bound, up +2.17 pp vs 20.56 stale). 2 missing tuples both MARKET_LIFECYCLE (KALSHI +
  POLYMARKET prediction_market) — unwired handlers not adapter contamination. **Task 001 (multi-AG re-run) PREREQs both
  now DONE** (KALSHI-PERP purge ✓ + Plan 5 unregistered-handler audit ✓ per
  `foundation_gates_and_capture_to_100_2026_07_06` line 77 `- [x]`) — task 001 will re-dispatch as its own
  /boot-per-shippable-unit. Snapshot updated above; evidence artefact (local):
  `/home/ubuntu/coverage_prediction_20260706T152707Z.json`.
- **2026-07-06** — **task 004 tradfi Layer-1 DOCUMENTED as BLOCKED-PLAN2** (via
  `layer1_remeasure_and_certify_2026_07_06` task 004). Main-agent answer to `BLK-ab86f4e9` confirmed: do NOT certify
  tradfi Layer-1 now — the tradfi IS catalogue rebuild + manifest rebuild + E7 CF verify from Plan 2
  (`tradfi_v9_stage1_finish_2026_07_06`) tasks 2-11 have NOT landed (only Plan 2 task 1 done). Running
  measure_honest_coverage --asset-group tradfi against the pre-v9 catalogue produces a certification that would
  re-measure again. Task 004 checkbox annotated 🚧 BLOCKED-PLAN2; tradfi Snapshot entry unchanged at 51.43 [06-29
  stale]. Re-dispatch after Plan 2 rebuilds land. Also noted: dispatcher's `gate_on_depends: true` needs review —
  per-plan-task granularity is not enforced (task 004 was dispatched despite Plan 2 not being done).
- **2026-07-06** — **defi Layer-1 CERTIFIED — 94.81% fresh** (via `layer1_remeasure_and_certify_2026_07_06` task 003).
  Ran `measure_honest_coverage.py --asset-group defi` locally at 2026-07-06 15:13 UTC on `is@681f50a` (post-D1 +1.38M
  seeding); primary manifest `gs://market-data-tick-defi-prd-central-element-323112` blob.updated 2026-07-06T15:11:42Z,
  13,515,019 rows; merged 10,828,935 rows. Result: **expected_tuples 77 / present_tuples 73 / missing 4 / stray 128 →
  94.81%.** Honest direction ✓ — 69.44 stale (06-29) → 94.81 fresh; denominator SHRANK 108→77 (-31 tuples) driven by
  `is@3bb7acd` (defi lending grain roll-up folds `a_token`/`debt_token`/`liquidation` → `lending` in Layer-1 canon,
  2026-07-03) — legitimate schema tightening, NOT a wrong-direction shrink. **D1 seeding VERIFIED in Layer-2:**
  `by_asset_group.defi.expected_unattempted = 1,534,304` — the +1,380,376-row apply landed in the reachable denominator.
  Layer-2 defi rollup: coverage_pct **62.06%** (captured 2,857,320 / reachable 4,603,799; empty_confirmed 6,225,136;
  attempted_failed 212,175; total 10,828,935; layer1_completeness_pct 94.81; denominator_status INCOMPLETE — 4 tuples
  still missing so Layer-2 stays a lower bound but tightened +4.51 pp vs 57.55 stale). 4 missing tuples all one venue
  (EIGENLAYER-ETHEREUM spot_asset {eigenlayer_rewards, oracle_prices, rewards, staking_yields}) — indicates one unwired
  handler/venue not four independent gaps. Task 001 (multi-AG re-run) NOT flipped by this task — its cross-plan PREREQs
  (KALSHI-PERP purge · Plan 5 unregistered-handler audit) primarily affect cefi/prediction Layer-2, not defi Layer-1.
  Snapshot updated above; evidence artefact (local): `/home/ubuntu/coverage_defi_20260706T151304Z.json`.
- **2026-07-06** — **cefi Layer-1 CERTIFIED — 73.61% fresh** (via `layer1_remeasure_and_certify_2026_07_06` task 002).
  Ran `measure_honest_coverage.py --asset-group cefi` locally at 2026-07-06 15:01 UTC on `is@03cfd0f` (post-D2a);
  primary manifest `gs://market-data-tick-cefi-prd-central-element-323112` blob.updated 2026-07-06T14:55Z, merged
  11,125,247 rows. Result: **expected_tuples 72 / present_tuples 53 / missing 19 / stray 87 → 73.61%.** Honest direction
  ✓ — 79.55 stale → 73.61 fresh; denominator grew 44→72 (+28 tuples) matching D2a's `INSTRUMENT_TYPES_BY_VENUE`
  completion. Layer-2 rollup context: cefi coverage_pct 33.28% (captured 2,891,774 / reachable 8,689,530; total
  11,125,247; denominator_status INCOMPLETE — 19 tuples still missing so Layer-2 stays a lower bound). Task 001
  (multi-AG re-run) NOT flipped by this task — its cross-plan PREREQs (KALSHI-PERP purge · Plan 5 unregistered-handler
  audit) primarily affect Layer-2 correctness, so a single-AG cefi run satisfies task 002's Gate independently. Other AG
  Layer-1 tasks (003 defi · 004 tradfi · 005 pred) remain queued and gated on their respective plans. Snapshot updated
  above; evidence artefact (local): `/home/ubuntu/coverage_cefi_20260706T150020Z.json`.
- **2026-07-06** — **AO tiering revised (operator): Plan 1 Opus/max, Plans 2-6 Sonnet/high.** Initial dispatch tagged
  all 6 Opus/max; operator dialed back after the per-plan reasoning — only **Plan 1** (the C2 `_row_data_types`
  instrument-type/bundle-aware fix that defeated two prior attempts + the denominator correctness) clearly needs Opus.
  Plans **2** (tradfi, proven tooling), **3** (catalogue ops), **4** (measure+certify, guarded), **5** (foundation
  reconcile + pattern-following handler), **6** (infra ops) run **Sonnet/high** with the smoke-first guards +
  main/review agents as backstop. Turns on the AO-vocabulary facts: **no `xhigh`; `max` requires Opus** (Sonnet+`max`
  HARD-STOPs the worker self-check), so Sonnet's valid ceiling is `high`. Frontmatter flipped on P2-6
  (`model_tier: sonnet-doable` + `thinking_tier: high`); P1 unchanged. **P5 is the bump-to-Opus candidate** (new
  `risk_params` handler + defi-oracle design) if a margin is wanted.
- **2026-07-06** — **Stages 1-6 DISPATCHED TO AO as 6 role-homogeneous plans (tiered — see the entry above).** Carved
  the tracker's remaining engineering into 6 AO plans (`assigned_vm: planning`, `execution_scope: orchestrator-agent`):
  P1 cefi denominator (`cefi_layer1_denominator_gaps`, assigned in-place — D2a/D2b marked done, 2a/2c/2f folded in)
  `pm@5bff1354c`; P2 tradfi Stage-1 finish (`tradfi_v9_stage1_finish`) `pm@f8bb8aa5f`; P3 IS-catalogue B0→B1→B2
  (`is_catalogue_completion_2d`) + P4 Layer-1 re-measure/certify (`layer1_remeasure_and_certify`, `gate_on_depends`
  Plans 1-3) `pm@64a1c00f8`; P5 foundation+capture (`foundation_gates_and_capture_to_100`, handler-audit ungated so it
  can precede P4) + P6 infra capture/devops (`infra_capture_and_devops_leftovers`, infra role) `pm@3dc6fcf04`. Contract
  verified against `agent-orchestrator/server/regen_backlog_from_plan.py`: model/effort is **per-plan** (frontmatter or
  role file), AO has **no `xhigh`** (max is the ceiling; `data_engineering` role default = the rejected sonnet/high, so
  the explicit opus-required+max override is load-bearing); `BLOCKED-*` lines auto-skip dispatch (operator-visible);
  `gate_on_depends` machine-holds P4 until P1-3 done. Hard-stops (bucket deletes, locked-plan archival, COINBASE
  `MVP_SCOPE`, CLOB classification, paid-RPC creds) stay off AO as `BLOCKED-*` lines the agents raise. UI drill-down (1
  P2 item) left off AO — too small for a standalone plan.
- **2026-07-06** — **TradFi v9 migration APPLY COMPLETE — all 6 years (2020-2025), exit_code=0, fatal=0.** The D3 fix
  (e2-standard-16 · SPOT · workers 24 · per-year chunks) held at scale — memory stayed ~6.7 GB / 64 GB per VM, zero OOM
  across the fleet. `moved<planned` on every year = idempotent skips of already-canonical objects (per-year TOTALs: 2021
  moved 783,448 · 2022 738,644 · 2024 786,334 · etc.). **NEXT (deferred → AO / Ikenna):** 2026 migration (after the live
  CME-OHLCV capture VMs drain) → orphan-sweep E=0 + idempotent straggler re-run (transient 503s) →
  `rebuild_tradfi_manifest` (E5) → IS enumerate-seed + catalogue → all 5 AGs canonical +
  `migration_verification_orphan_safety` V6 closes. Ikenna's migration sign-off gates the legacy-twin bucket deletes.
- **2026-07-06** — **2e SHIPPED — defi denominator corrected (+1,380,376 rows).** D1 defi `expected_unattempted` seeding
  ran (opus, v1 enumerator — the `--enumerator-version=v2` in the dispatch was my spec error, caught by the agent +
  confirmed). run_id `enum-universe-defi-20260706-130616`. Scan-gate hit **exactly 1,380,376** (0% dev) → 1-day smoke
  (1,910 rows, 3-step clean) → full apply **1,380,376 rows** (per-year to the row) → fresh scan **→ 0 candidates** (≥1M
  halt cleared), `expected_unattempted` +0 (zero downloads), consolidator merged into the canonical defi manifest. No
  enumerator edit; poisoned `/tmp` cache cleaned. **Ready to flip** `issues/defi_expected_unattempted_backlog_1m` (same
  evidence). Cross-AG never-seeded follow-on (cefi/tradfi/pred) split to a separate P2.
- **2026-07-06** — **D2a SHIPPED + VERIFIED — cefi Layer-1 dropped to the honest number.** Both halves landed:
  **uac@e76d874a** (`INSTRUMENT_TYPES_BY_VENUE` completes the 10 declared venues; DERIBIT-COMBO OPTION-only) +
  **is@03cfd0f** (`_get_cefi_venue_itypes` now sources declarative `INSTRUMENT_TYPES_BY_VENUE`, not the tardis
  fetch-routing table). QG-green both repos, trees clean, in sync, 41 tests pass (dynamic — no golden edits). **Measured
  delta (same manifest snapshot, back-to-back): cefi Layer-1 84.09% → 73.61%** (expected 44→72, +28 tuples, 0 removed) —
  the honest direction (the "79.55%" was a stale point-in-time snapshot; the before/after PAIR is apples-to-apples).
  Agent caught + fixed 2 latent regressions via tuple-diffing: bare `COINBASE` (declared but absent from the dict) +
  `DERIBIT` missing `SPOT_PAIR` (would have REMOVED 2 real tuples). D2b: added `VENUE_DATA_TYPE_CAPABILITIES` for
  PACIFICA/EXTENDED/LIGHTER/COINBASE-FUTURES. **⚠️ BIG FINDING (operator decision): bare `COINBASE` + `DERIBIT-COMBO`
  still produce 0 EXPECTED** — absent from `MVP_SCOPE["cefi"].venues` (which has COINBASE-SPOT/FUTURES, not bare
  COINBASE), so gate #3 zeroes them regardless of the dict fix. **Decide: add bare `COINBASE` to `MVP_SCOPE.venues` (+ a
  DERIBIT-COMBO MVP-membership call), or confirm intentionally out.** (BINANCE-DELIVERY also 0 — COIN-M explicitly
  not-MVP per 06-27 decision #3, correct.)
- **2026-07-06** — **2c cefi capture-rule REASSESSED (opus agent) — prevented a ~380k-row data-loss.** Cap-drop half was
  ALREADY shipped (`is@0fe8e71`, 06-23). Reclassification half STOPPED at the smoke (mutated NOTHING): the
  `reclassify_cefi_manifest_mvp_universe_2026_06_23.py` script would DELETE ~380k+ legit in-MVP **captured**
  BITFINEX/KRAKEN rows via a `_derive_base` bug (mis-parses Bitfinex `ADAF0:USTF0` + Kraken `PF_/PI_` wire-forms → wrong
  base → perp-gate drops their spot rows), is architecturally superseded (honest-coverage-v2 forbids deriving the
  denominator from the manifest — circular), collides with the in-flight ASTER split (461k ASTER `SOURCE_RETURNED_ZERO`
  empty→EU flips), and destabilises measurement (index rewrite flips PRIMARY-bucket selection). It already ran 2× on
  06-23 (snapshots exist). **RE-SCOPE (operator decision): retire the manifest-pruning script → MVP filter as a
  read-time gate in `measure_honest_coverage`, folded into 2a `build_expected`, sequenced after 2b + the ASTER split.**
  No data mutated, no reserved file touched.
- **2026-07-06** — **TradFi smoke VALIDATED → fanned out 2020-2024.** The 2025 smoke proved the D3 fix: memory flat at
  **6.7 GB / 64 GB** for 18+ min while migrating candles (172k/577k, steady ~11k/min) — vs. the 06-29 climb-to-OOM at
  workers 64. Setup ran in ~1 min (`uv` install). Fanned out **2020, 2021, 2022, 2023, 2024** as 5 concurrent per-year
  VMs (disjoint day-partitions; all e2-standard-16 · SPOT · workers 24 · MTDS 9ecd1e2 pinned). **2026 held for last**
  (live `tradfi-bf-cme-ohlcv-1m-*` capture VMs are writing 2026 processed_candles). Noted: a transient GCS 503 burst
  ("internal error, retry") left ~7 objects unmoved on 2025-02-03/04 — not memory / not our bug, self-limited; recovered
  by the migrator's idempotency + the mandatory post-apply orphan-sweep (V6 E=0). Fleet watchdog armed on `run.log` (the
  serial console is blind to the backgrounded migrator — lesson). **Next:** per-year completion (VMs self-stop) → 2026 →
  orphan-sweep + straggler re-run → `rebuild_tradfi_manifest` + IS enumerate-seed + IS catalogue.
- **2026-07-06** — **Stage-0 consolidation REASSESSED (the one-liner was partly stale).** Investigated §F.1 before
  executing: (1) **`path_to_100pct` → `data_completion` merge = already DONE** (superseded + archived 2026-06-30;
  `data_completion` carries the "Folded-in from `path_to_100pct`" section; DEDUP residual is already a Stage-5 item — no
  orphaned work). (2) **`instruments_catalogue_incremental_rollup` → completed = must NOT flip** — its lone open item is
  a LIVE issue: the operator-declined tradfi catalogue-scheduler band-aid **re-triggered 2026-07-03** (tradfi
  `prod/catalog.parquet` stale since 2026-06-29; daily `lifecycle_catalogue_scheduler` runs killed at the 3600s
  timeout). Flipping would bury it. (3+4) **archive `mvp_catalogue_finalization_v10`** (0-open) + **fold
  `instruments_mtds_subset` cefi items → foundation** (60 open, ⚖️ REVIEW) are both `locked_by: live-defi-rollout` →
  **operator unlock/sign-off required** (HARD RULE: locked-plan archival never-autonomous; §F.4). No plan mutated
  pending sign-off; surfaced to operator.
- **2026-07-06** — **TradFi v9 migration RESTARTED (D3 fix) — 2025 smoke launched.** The 2026-06-29 full-range run
  OOM-killed on e2-standard-8 at `--workers 64`; baked the D3 fix into the launcher (`launch-canonical-migration-vm.sh`:
  `MACHINE_TYPE` override, SPOT default + `ON_DEMAND=true` opt-out, tradfi `--workers` default 24) —
  **deployment-service@77cfcda** (QG-green + quickmerge). Verified the VM runs from GCS **code tarballs** (no Docker)
  and pinned `MTDS_TARBALL_SHA=9ecd1e2` (today's build; tradfi migrator byte-identical to LDR HEAD) so the smoke proxies
  the fan-out. Launched the **2025 smoke** `canonical-migration-tradfi-20260706-170108` (e2-standard-16 · SPOT · workers
  24 · `--apply`), verified STARTED (RUNNING <60s), armed a no-fire-and-forget watchdog. Migrator date-shards its walk
  (`_iter_days`) so a 1-year range bounds the up-front object-list accumulation (the OOM cause). **Next:** watchdog
  verdict ~T+16min → if memory-bounded + objects migrating, fan out 2020-2024 + 2026 (2026 last, after the live
  CME-OHLCV capture VMs). NOT blocked on Stage 0 (its leftover is doc-consolidation on cefi/catalogue plans — running in
  parallel).
- **2026-07-06** — **DERIBIT-COMBO `future_combo` RESOLVED (Ikenna).** Ikenna confirmed `future_combo` is **NOT in MVP**
  — Deribit uses `options_chain` (OPTION) only. DERIBIT-COMBO stays `{OPTION}` in `INSTRUMENT_TYPES_BY_VENUE`; the D2a
  provisional is now **final, with no further code change**. Cleared the D2a Decision-Gates note, the Blocked/waiting
  register entry, and the D2 OPEN-NUANCE flag. **D2a fully closed** — the last open external item on this tracker's own
  decisions is resolved (the remaining open items — KALSHI-PERP purge (slot-2) and credentials-gated captures — are not
  our decisions).
- **2026-07-06** — **C5 FIX SHIPPED — took over Ikenna's unfinished fix.** Ikenna's C5 registration fix hadn't landed
  (bad network Friday), so we completed it properly: verified the root cause end-to-end, made the minimal-correct change
  (2 lines in `cli/main.py` — import + `"deribit-options-chain"` dispatcher key; the `__init__.py` `__all__` step in his
  sketch was cosmetic — main.py imports handlers by full path — so skipped), added a regression test
  (`test_deribit_options_chain_operation_registered`), ran the full MTDS QG (green, sentinel written), shipped via
  quickmerge → **mtds@9ecd1e29e** on live-defi-rollout (Tier-C drain runs `quality-gates-v2` on the promote PR).
  **Remaining to actually capture:** the handler is LIVE/replay only (no backfill — `process()` = `date.today()`), so a
  live cron/VM must run `--operation deribit-options-chain` (Stage-5 [INFRA] item) before the Stage-3 re-measure shows
  real Deribit options coverage. Historical options not covered by this handler.
- **2026-07-06** — **D5 root cause CONFIRMED (Ikenna's C5, verified in our code).** DERIBIT `options_chain` captured=0/1
  because `DeribitOptionsChainHandler` (built — `cli/handlers/deribit_options_chain_handler.py`) is NEVER REGISTERED:
  absent from `handlers/__init__.py` `__all__` (line 9), no `cli/main.py` import, and NOT a key in the operations
  dispatcher (`cli/main.py` 533–582: `download`→…→`collect-onchain-perp-batch`, no `deribit-options-chain`). No
  operation invokes it → zero shards → captured=0. **Corrects the earlier "measurement-gated" framing** — a genuine
  CAPTURE GAP, not a re-measure artifact. Fix = Ikenna's 3-line handler registration (his MTDS workstream, in progress)
  → a `deribit-options-chain` backfill (added to Stage 5) → THEN the honest number shows in the Stage-3 re-measure. Not
  touched by me (Ikenna owns the MTDS fix).
- **2026-07-06** — **D5 confirmed NOT a standalone decision** (resolves via Stage-3 re-measure). Deribit
  `options_chain`: reconciliation §E.1 downgraded A18 to indeterminate-pending-remeasure; the
  `cefi_deribit_binance_futures_bundle_verification` GCS scan already found the pre-backfill "138 captured" were genuine
  PHANTOMS (zero options_chain/futures_chain blobs) → the honest number falls out of the Stage-3 re-measure post the
  06-28 backfill. MVP "don't widen beyond BTC/ETH options_chain" stance STANDS (Deribit OPTION = options_chain only).
  Mechanical residual (annotate the Layer-1 gap + gate spot-checks behind ">0 captured") folds into D2 /
  cefi_deribit_bundle. **All 5 decisions now closed** (D1–D3 decided · D4 resolved 07-03 · D5 measurement-gated); open
  external items = Ikenna's DERIBIT-COMBO reply + the KALSHI-PERP purge (slot-2) + credentials-gated captures.
- **2026-07-06** — **D4 found ALREADY RESOLVED** (not a new decision). The cefi_tick G4 "Layer-1 does not block G4"
  carve-out was superseded by **Ikenna's C4 decision 2026-07-03, option (a): G4 enforces Layer-1 AND Layer-2**
  (`mvp_backfill_cefi_tick_v10` § G4 — "verify honest-complete (BOTH layers)"). Same direction as the governing law; G4
  cannot close until D2 (`cefi_layer1_denominator_gaps`) lands. Corrected the stale PENDING → DECIDED (the
  reconciliation snapshot predated the 07-03 call). Next: D5 (Deribit options stance) likely resolves via the Stage-3
  re-measure per reconciliation §E.1 (A18 indeterminate until a live DERIBIT `options_chain` measure), not a standalone
  decision.
- **2026-07-06** — **KALSHI-PERP contamination assessed vs D2** (from the pulled
  `prediction_universe_capture_dead_since_07_01` issue; surfaced by the slot-2 incremental-catalogue agent). The
  `kalshi_perp` adapter points at the WRONG Kalshi host (events `api.elections.kalshi.com`, binary-only) → its category
  filter is a no-op → it emitted **25,473 Kalshi event contracts as fake `KALSHI-PERP` `PERPETUAL`** into the cefi store
  (6.8% of the cefi catalogue; 0 MVP-tagged; span 06-29→07-06 from `is@4da6fe8`). POLYMARKET-PERP clean (0 rows).
  **Impact on D2 (assessed): denominator decision UNCHANGED** — KALSHI-PERP/POLYMARKET-PERP are real declared cefi perp
  venues, already `{PERPETUAL}` in `INSTRUMENT_TYPES_BY_VENUE` (NOT in D2's 10-missing list), operator ruled "keep the
  venues, correct the adapter." **Two sequencing consequences added:** (1) Stage-3 cefi re-measure now GATED on the
  Phase-0 purge; (2) real KALSHI/POLYMARKET-PERP capture is BLOCKED-CREDENTIALS (margin API) → credentials-gated
  honest-absence in the denominator. Correction owned by slot-2 + the 4da6fe8 author — adapters NOT touched here.
- **2026-07-06** — **D3 DECIDED.** TradFi v9 `--apply` (the last un-canonical AG) restart: **`--workers 24`** (fallback
  16 if SSL-EOF/pool-full recurs) · **per-year chunks** 2020→2026 (via `--start-date/--end-date`) · **e2-standard-16
  (64GB)** · idempotent restart (skips the ~37k already done). Root cause = connection-pool thrash at `--workers 64` on
  e2-standard-8 **+** up-front full object-list accumulation (tradfi is the biggest AG, ~6M objects) — NOT a data-volume
  wall (defi succeeded at 96; sports deliberately dropped to 16), so lower concurrency + chunking is the fix, not just
  more RAM. **Manifest schema = v9 confirmed current** (`CANONICAL_SCHEMA_VERSION = 9`; the v12 is MVP-scope, orthogonal
  — operator flagged, verified). Execution step (live VM) — queued for leaving "local" mode; monitor per
  no-fire-and-forget (STARTED<60s · progress · verify T+10min). Migrator fixes object PATHS only;
  `rebuild_tradfi_manifest.py` (E5) + IS enumerate-seed + IS catalogue for tradfi follow. **Closes Stage-0 — all 3
  blockers decided.**
- **2026-07-06** — DERIBIT-COMBO `future_combo` question **relayed to Ikenna** (context message drafted + passed on by
  operator; he'll answer when available). **Proceeding provisionally with `{OPTION}`** (MVP-correct — Deribit MVP =
  `options_chain` only) so D2 is not blocked. Flagged as awaiting-reply in the D2a Decision-Gates row + the
  Blocked/waiting register, with the exact per-answer (A/B/Other) update actions listed there for a one-line change when
  he replies.
- **2026-07-06** — **D2 DECIDED.** **D2a** = switch the cefi Layer-1 itype-gate authority from the tardis fetch-routing
  map (`VenueMapping.venue_instrument_type_to_tardis`, iterated in
  `check_enumeration_completeness._get_cefi_venue_itypes`) → the **declarative `INSTRUMENT_TYPES_BY_VENUE`** (aligns
  cefi with defi `PROTOCOL_CAPABILITIES.instrument_types` / tradfi `TRADFI_VENUE_INSTRUMENT_TYPES`), AND **complete it
  for the 10 declared cefi venues currently missing** (of 24 in `VENUES_BY_ASSET_GROUP["cefi"]`): BINANCE-DELIVERY ·
  DERIBIT-COMBO · COINBASE-FUTURES · BITFINEX-SPOT · BITFINEX-FUTURES · BITGET-SPOT · BITGET-FUTURES · PACIFICA-SOLANA ·
  EXTENDED-STARKNET · LIGHTER-ZKSYNC. Proposed itypes (owner-verify at impl): `-SPOT`→{SPOT_PAIR};
  `-FUTURES`/BINANCE-DELIVERY→{PERPETUAL,FUTURE}; PACIFICA/EXTENDED/LIGHTER →{PERPETUAL}; **DERIBIT-COMBO→{OPTION}**
  (operator 2026-07-06). Rejected: extend-tardis-map (fetch blast radius; sourcing≠existence), dedicated-new-map (drift
  surface). **D2b** = complete `VENUE_DATA_TYPE_CAPABILITIES` for the declared-but-absent venues + codify "a declared
  venue MUST carry a capability entry; absent = stray/not-expected" (resolves the checker-treats-absent-as-carved-out vs
  enumerator-treats-absent-as-not-gated asymmetry). Expected effect: cefi Layer-1 denominator GROWS, % drops below
  79.55% — the honest direction. **✅ DERIBIT-COMBO future_combo RESOLVED (Ikenna 2026-07-06):** OPTION-only —
  `future_combo` is NOT in MVP (Deribit MVP = `options_chain` only), so `{OPTION}` is final (not just provisional) and
  `future_combo` stays out of the MVP denominator. Also reconcile the COINBASE (declared) vs `COINBASE_SPOT` (map
  constant) naming at impl. Sequenced AFTER C2 MVP-gate intersection (already decided); re-measure closes it (Stage 3).
- **2026-07-06** — **D1 DECIDED = A** (full 1,380,376-row apply). Verified safe before deciding: (1) enumerator
  classifies pre-genesis **per-(chain, protocol)** via on-chain-derived `PROTOCOL_LAUNCH_DATES` + `CHAIN_GENESIS_DATES`
  (`enumerate_expected_universe.py` L27-28/96-99); (2) defi MVP universe = 11 curated venues, earliest =
  **CURVE-ETHEREUM 2020-01-19** (web-confirmed Jan 2020; Balancer/Lido/Uniswap-V3 cross-checks all matched the SSOT) →
  all 2018-2019 is pre-genesis for MVP; (3) MAKER (2017) / IDLE (2019-08) are NOT in MVP and are per-protocol-classified
  in the full universe → no real-data clipping. Zero downloads; +1.38M typed honest-absence rows. **Remaining:** execute
  the apply (`enumerate_expected_universe.py --asset-group defi --apply-write --max-writes-per-run 1500000`) + 3-step
  verify (row-delta ≈ +1.38M · fresh scan → ~0 candidates · data-status refresh), then the P2 cross-AG backlog check.
  Minor follow-up noted: Balancer SSOT date 2020-03-31 vs first V1 bronze deploy ~2020-02-26 (~34d, immaterial to this
  seeding; in the 2020 actionable zone, not the 2018-19 pre-genesis block).
- **2026-07-06** — Tracker created. Baseline captured from the 4-plan deep-read +
  `instruments_service_plan_reconciliation` §D/E/F. Awaiting decisions D1–D3 to open Stage 2.

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

---

### Source plans / issues (pointers — read there, don't duplicate here)

- **Model / measure:** `honest_coverage_v2_instrument_denominator_2026_06_28.md` ·
  `honest_coverage_smoke_harness_2026_06_28.md`
- **Denominator generation (done):** `mvp_catalogue_finalization_v10_2026_06_27.md` ·
  `instruments_catalogue_incremental_rollup_2026_06_29.md` · `mvp_scope_catalogue_tagging_2026_06_08.md`
- **Spine / apply gate:** `instruments_foundation_completeness_2026_06_24.md` ·
  `migration_verification_orphan_safety_2026_06_10.md` · `instruments_mtds_subset_consistency_remediation_2026_06_17.md`
- **Capture:** `data_completion_to_100_all_ag_2026_06_21.md`
- **Open corrections:** `issues/cefi_layer1_denominator_gaps_2026_07_03.md` ·
  `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` · `issues/cefi_universe_capture_rule_2026_06_23.md`
- **Resolved / map:** `issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md` ·
  `issues/instruments_service_plan_reconciliation_2026_06_29.md`
- **New from the 2026-07-07 ASTER/CEFI audit:** `issues/aster_mtds_failure_count_regression_2026_07_07.md` (🔴
  unexplained live regression) · `issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md` (🔴
  LIGHTER/PACIFICA dark 11+ days + zero alerting on the monotonicity guard) ·
  `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` (D6 — shard dimension model) ·
  `issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md` (dead-code cleanup) ·
  `issues/manifest_reprocessing_generic_utility_2026_07_07.md` (no generic reprocessing tool) ·
  `issues/perp_funding_data_semantics_and_cadence_2026_06_16.md` GAP 4 (ASTER trades-genesis contradiction, newly
  appended) · `issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` (🔴 no AG has a real (venue,
  instrument_type) → data_types combinator; CME/ICE cell is live-wrong; scoped to CEFI/DEFI/TRADFI only —
  Sports/Prediction correctly excluded) · `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` (🔴 P0 —
  AAVE_V3-ARBITRUM/POLYGON + SPARK have real current captured data the turbo API silently reports as 0/0; a read-path
  bug, not a capture gap)
- **SSOT:** `/codex/02-data/honest-coverage-model.md`
