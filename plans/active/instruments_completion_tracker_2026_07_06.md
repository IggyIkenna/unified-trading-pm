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
    /plans/archive/2026_07/instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/archive/2026_07/instruments_catalogue_incremental_rollup_2026_06_29.md,
    issues/cefi_layer1_denominator_gaps_2026_07_03.md,
    issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    issues/cefi_universe_capture_rule_2026_06_23.md,
    issues/honest_coverage_uac_writer_matrix_reconciliation_2026_06_29.md,
    /plans/archive/issues/instruments_service_plan_reconciliation_2026_06_29.md,
    issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
    issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md,
    issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md,
    issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
    issues/aster_mtds_failure_count_regression_2026_07_07.md,
    /plans/archive/issues/manifest_reprocessing_generic_utility_2026_07_07.md,
    issues/perp_funding_data_semantics_and_cadence_2026_06_16.md,
    issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md,
    issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md,
    /plans/archive/issues/mtds_mdps_order_book_imbalance_duplicated_2026_07_07.md,
    issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
    issues/defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
    issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
    issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    /plans/archive/2026_07/instruments_service_docs_consolidation_2026_07_08.md,
    /codex/02-data/honest-coverage-model.md,
    /plans/archive/2026_08/instruments_completion_tracker_progress_log_history_2026_08_03.md,
  ]
created: 2026-07-06
last_updated: 2026-08-03 # line-cap remediation split -- extracted 07-06/07-07 Progress Log history to the archive doc above; context_scope backfilled
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/archive/2026_07/honest_coverage_v2_instrument_denominator_2026_06_28.md,
  ]
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
  `plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md:200,786,790`. Corrected 2026-07-12 (finding 362, §A2
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
- [ ] [ADMIN] P1. Plan consolidation (from `/plans/archive/issues/instruments_service_plan_reconciliation_2026_06_29.md`
      §F.1) — **REASSESSED 2026-07-06**:
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

- [x] ✅ [DATA] P0. TradFi v9 G4 `--apply` — per **D3**: `--workers 24` (fallback 16) · per-year chunks 2020→2026
      (`--start-date/--end-date`) · e2-standard-16 · idempotent restart → `migration_verification_orphan_safety` V6
      closes; **all 5 AGs canonical**. Then `rebuild_tradfi_manifest.py` (E5) + IS enumerate-seed + IS catalogue for
      tradfi. **DONE — reconciled 2026-07-28 against `plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md`
      (`status: resolved`, all 11 own todos `[x]`).** 2020-2026 `--apply` exit_code=0/fatal=0 both waves
      (`deployment-service@77cfcda` launcher fix); orphan-sweep GATE MET 2026-07-10 (`orphan_class_E=0`); E5 rebuild
      done 2026-07-07 (`market-tick-data-service@4ccf52c6`); IS enumerate-seed done 2026-07-09 (run_id
      `enum-universe-tradfi-20260709-020218`); IS catalogue done 2026-07-06
      (`catalogue-rollup-tradfi-20260706T154714Z`). All 5 AGs canonical, `migration_verification_orphan_safety` V6/G4
      closed.
- [ ] [DATA] P1. Legacy-twin **deletes** (defi / tradfi / pred; cefi already done, **sports is NOT done** — 0 of 34,385
      `B_legacy_duplicate` rows pass the 5-part proof per `sports_legacy_duplicate_triage_2026_07_22.md`) in a quiet
      window. **STILL OPEN (reconciled 2026-07-28)** — none of this todo's named archived children cover it; the tradfi
      leg was forked out verbatim to `/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`. **No
      longer operator-gated as of 2026-07-28** — the §3a reversibility carve-out
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, extended) now covers hard-stop #2
      (legacy-object-delete-after-copy) once Part 5's twin-coverage proof independently confirms 100% canonical-twin
      coverage; that child plan's todo has been retagged and re-dispatched with the fresh-check dispatch shape (see its
      own text), not this tracker's own work to execute.

## Stage 2 — Denominator correctness (the core; cefi leads)

- [x] [CODE] P0. **2a. Land the single `build_expected` producer — ✅ DONE** (A17 — `honest_coverage_v2` Phase 1). Root
      fix; **now unblocked** (blocker archived 07-03). Bake **D2a** into it. — `instruments-service@681f50a` (canonical
      landed SHA; `a1038eef8` is the pre-quickmerge QG sentinel for the same commit) — consolidates the single public
      `build_expected(ag)` EXPECTED-universe producer, routing `check_enumeration_completeness` +
      `measure_honest_coverage` through it.
- [x] ✅ [CODE] P0. **2b. cefi gate-authority fix on `build_expected`** (`issues/cefi_layer1_denominator_gaps`): apply
      D2a/D2b → ASTER live-forward split (**enumerator `start_date` support is a hard prereq before the UAC capability
      flip**) → BYBIT-SPOT `PERPETUAL` relabel → C2 MVP-data-type intersection. **DONE — reconciled 2026-07-28 against
      `plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md` (`status: resolved`, all own todos `[x]`).**
      `instruments-service@681f50a` (2a fold with D2a baked into `build_expected`) + `03cfd0f` (D2a landing) +
      `2170d9a3` (C2 MVP-data-type intersection). Verified dynamically: `build_expected("cefi")` returns 72 tuples over
      18 of 24 declared cefi venues; every absent venue carries an explicit configuration reason (no silent whole-venue
      omission).
- [x] ✅ [DATA] P0. **2c. cefi capture-rule residual** (`issues/cefi_universe_capture_rule`) — **REASSESSED (opus,
      2026-07-06)**: **cap-drop = ✅ ALREADY DONE `is@0fe8e71` (06-23)** (`_passes_asset_filter` now applies only
      accepted-quote + BTC/ETH- options gates; full-universe enumeration verified). **Reclassification `--apply` = ⛔ DO
      NOT RUN — RE-SCOPED.** The `reclassify_cefi_manifest_mvp_universe_2026_06_23.py` script is unsafe + superseded:
      (a) `_derive_base` DATA-LOSS bug — mis-parses Bitfinex `ADAF0:USTF0` + Kraken `PF_/PI_` wire-forms → would DELETE
      ~380k+ legit in-MVP **captured** BITFINEX/KRAKEN rows; (b) architecturally superseded (honest-coverage-v2 forbids
      deriving the denominator from the manifest — circular); (c) collides with the in-flight ASTER split (461k empty→EU
      flips are ASTER `SOURCE_RETURNED_ZERO`); (d) the 6 "stale" venues are ALREADY in the manifest with real data. It
      already ran 2× on 06-23 (snapshots exist — "never confirmed run" resolved). **→ retire the manifest-pruning
      script; do the MVP filter as a read-time gate in `measure_honest_coverage` folded into 2a `build_expected`,
      sequenced after 2b + the ASTER split.** **DONE — reconciled 2026-07-28 against
      `plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md` (resolved, own todo `[x]`).**
      `instruments-service@2fa3877` — new public `filter_manifest_to_expected(ag, df)` applies the MVP cut at READ TIME
      inside `measure_honest_coverage._compute_coverage` for cefi, ZERO manifest mutation (Layer-1 keeps the unfiltered
      df so stray_tuples stay visible); 11 new + 21 existing tests green.
  - [ ] [CODE] P1. Fix `_fetch_earliest_funding_date`
        (`instruments-service/instruments_service/reference_data/adapters/cefi/aster.py:247-267`) to exclude the
        synthetic pre-launch placeholder funding rows (flat `0.0001` rate) before deriving `available_from_datetime` —
        otherwise ASTER's per-instrument genesis can still stamp a spuriously pre-2023-07-22 date even though the
        venue-level fallback is correct. Found 2026-07-07 audit. **STILL OPEN (reconciled 2026-07-28)** — no mention in
        `cefi_layer1_denominator_gaps_2026_07_03.md` or any of this todo's other named archived children; genuinely
        unaddressed.
  - [ ] [DATA] P1. Reconcile ASTER's `trades` genesis cross-registry contradiction (2021-08-30 in
        `expected_start_dates.yaml` vs. 2023-07-22 everywhere else) — see GAP 4 in
        `issues/perp_funding_data_semantics_and_cadence_2026_06_16.md`. Do before any pre-funding-genesis trades
        backfill for ASTER. **STILL OPEN (reconciled 2026-07-28)** — not covered by any named archived child; genuinely
        unaddressed.
- [x] ✅ [DATA] P0. **2d. IS-catalogue completion `B0→B1→B2`** (`instruments_mtds_subset`): backfill instruments to
      no-missing (B0) → regen catalogue + un-pause daily schedulers (B1) → codify MVP-vs-total universe (B2). _B0 gates
      every expected-universe consumer._ **DONE — reconciled 2026-07-28 against
      `plans/archive/2026_07/is_catalogue_completion_2d_2026_07_06.md` (`status: complete`, all own todos `[x]`).** B0
      (backfill to no-missing): MVP-scoped gap = 83 cells (~0.1% of 76k MVP), every residual classified/tracked, 0
      unexplained gaps. B1 (catalogue regen + un-pause daily schedulers): all 5
      `lifecycle-catalogue-regen-{cefi,defi,tradfi,sports,prediction}-daily` schedulers confirmed ENABLED + green;
      weekly full self-heal confirmed running; all 5 `prod/catalog.parquet` fresh. B2 (wire enumerator to
      `TOTAL_UNIVERSE_AXES` SSOT): `instruments-service@7ded594` — load-time SSOT parity assertion + `is_total_universe`
      gate + MVP⊆TOTAL invariance test (12 new tests, 175 total green), sentinel
      `.qg_last_passed_sha=7ded5940661bc89f7e77591471810b4943541b01`.
- [x] [DATA] P0. **2e. defi seeding apply (D1) — ✅ DONE** (opus, run_id `enum-universe-defi-20260706-130616`):
      **+1,380,376 typed `empty_confirmed` rows** (per-year matches the issue to the row: 2018=695,830 / 2019=683,862 /
      2021-25=684), `expected_unattempted` +0 (zero downloads), fresh full-window scan **→ 0 candidates** (≥1M
      enumerator halt cleared), consolidator merged into the canonical defi manifest. Scan-gate hit EXACTLY 1,380,376 +
      1-day smoke verified first. No enumerator edit (read/run only). **CORRECTION (2026-07-25, per
      `archive/issues/canonical_closeout_open_questions_2026_07_18.md` C2c):** the 1,380,376-row figure above (and the
      62.06% Layer-2 defi coverage_pct derived from it at line ~634) is the **retired v1 grain**. The v2 SSOT (locked
      issue `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`, corroborated by
      `defi_consolidated_closeout_2026_07_18.md`'s ~63.9M seed figure) puts the real DeFi `expected_unattempted` backlog
      at **~63.9M cells**, not 1.38M — this DONE checkbox and the 62.06% figure are the v1 milestone only, not the final
      denominator; the v2 backlog is open work tracked under Track-3 in
      `archive/issues/canonical_closeout_open_questions_2026_07_18.md`.
- [x] ✅ [VERIFY] P2. **2e follow-on** (was bundled into 2e): the cross-AG never-seeded backlog check on **cefi / tradfi
      / pred** (scan-only investigation — dispatch separately). **DONE — reconciled 2026-07-28 against
      `plans/archive/2026_07/foundation_gates_and_capture_to_100_2026_07_06.md` (`status: complete`, own todo `[x]`,
      2026-07-06, Opus slot-7).** Scan-only per contract (zero seeding). Filed
      `plans/active/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md` quantifying each AG's residual backlog:
      cefi = catalogue-vs-writer historical-listing gap (Kraken ~6yr class ≈ ~1.75M cells); tradfi = credential-gated
      EU-seed scaffolds only (recent enumerator commits already moved tradfi honest-cov 5.3%→13.8%, no DeFi-scale
      canonical re-seed remains); prediction = token-id `instrument_availability` lane not seeded + Kalshi launcher
      gap + a documented intentional per-conditionId exclusion. 7 actionable P0-P3 todos filed pointing at each owning
      plan.
- [x] ✅ [CODE] P1. **2f.** Reapply the denominator-gap model to **LIGHTER / EXTENDED / PACIFICA**. **DONE — reconciled
      2026-07-28 against `plans/archive/issues/cefi_layer1_denominator_gaps_2026_07_03.md` (resolved, own todo `[x]`,
      2026-07-08).** Both PREREQs confirmed landed: 2b (above) + enumerator `start_date` support
      (`instruments-service@4a8cff7`, generic per-`(venue, dt)` gate, no ASTER-specific code path); LIGHTER-ZKSYNC /
      EXTENDED-STARKNET / PACIFICA-SOLANA `VENUE_DATA_TYPE_CAPABILITIES` entries landed as part of D2b
      (`unified-api-contracts@e76d874a`). Dynamic verification: `build_expected('cefi')` returns exactly 3 tuples per
      venue for all three, matching the ASTER live-forward profile byte-for-byte — no code change required.

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

- [x] ✅ [SCRIPT] P0. Re-run `measure_honest_coverage` on the corrected catalogue + seeded manifests (**06-29 numbers
      are stale** — predate v12, the incremental-rollup switch, and the cefi 122-row ghost-dupe fix of 07-04). **DONE —
      reconciled 2026-07-28 against `plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md`
      (`status:     complete`, own todo `[x]`, DONE 2026-07-07 06:22 UTC).** Multi-AG
      `measure_honest_coverage.py --asset-group all` run on `is@68f174a` with both cross-plan PREREQs verified
      (KALSHI-PERP purge + Plan-5 unregistered-handler audit). Run id `2026-07-07T06:20:58Z / is@68f174a`; evidence
      artefact `coverage_all_20260707T062058Z.json` (4.6 MB).
- [ ] [VERIFY] P0. Certify per-AG Layer-1; **record fresh numbers in the Progress Log** — only now is any Layer-2 %
      trustworthy. **PARTIALLY DONE (reconciled 2026-07-28) — 4 of 5 AGs certified, tradfi still genuinely open.**
      `plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md` (complete) certified cefi 73.61% / defi 94.81%
      / sports 30.77% / prediction 66.67% (2026-07-06/07, matching this tracker's own Snapshot above). Its tradfi task
      stayed `🚧 BLOCKED-PLAN2` and was **forked out verbatim 2026-07-24** into
      `/plans/active/tradfi_consolidated_closeout_2026_07_18.md`'s own Phase C todo list — that plan, not this checkbox,
      is where tradfi Layer-1 certification now lives. Leaving unchecked: the item's own Gate ("Certify per-AG Layer-1")
      is worded all-5-AG and tradfi is not yet certified.
- [ ] [VERIFY] P1. Reconcile ASTER's two disagreeing missing-date counts before certifying: the manifest cell-presence
      view says 0 missing dates (1,082 consecutive days, 2023-07-22→2026-07-07); the live turbo API says 11 missing /
      1,071 expected for the same venue+window. Confirm which methodology the re-measure adopts. Found 2026-07-07 audit,
      `issues/aster_mtds_failure_count_regression_2026_07_07.md` context. **STILL OPEN (reconciled 2026-07-28)** — no
      resolution found in `layer1_remeasure_and_certify_2026_07_06.md` or any other named archived child; genuinely
      unaddressed.
- [x] ✅ [CODE] P1. Close `honest_coverage_v2` remaining (build_expected done in 2a; UI drill-down → Stage 6). **DONE —
      reconciled 2026-07-28 against `plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md` (complete, own
      todo `[x]`, CLOSED 2026-07-06 task 008).** Phase 1 `build_expected` consolidation flipped in
      `honest_coverage_v2_instrument_denominator_2026_06_28.md` (`instruments-service@681f50a`); Phase 2 UI drill-down
      annotated MOVED to this tracker's Stage 6 (still open there, see below). Measurement track officially closed.

## Stage 4 — Foundation gate sign-offs (formalize the spine, cefi-first)

_(`instruments_foundation_completeness` has heavy checkbox-vs-reality drift — much of G2/G3 actually ran; the work is
reconciling + signing off, not redoing.)_

- [x] ✅ [CODE] P0. cefi **G1.2** (`record_failed` routing + 06-26 re-capture) + **G1.3 follow-up** (on-chain-CeFi-perp
      venue form). **Caveat added 2026-07-07:** this is a thin-day/50%-of-trailing-median gate, not DeFi's strict
      never-regress-below-all-time-max block — confirm with operator whether literal DeFi parity is required, or whether
      the looser threshold is the intended CeFi policy (CeFi delistings are real, expected decreases in today's active
      count, unlike DeFi's provably-monotonic contracts). See
      `issues/cefi_monotonicity_guard_alerting_and_dark_venues_2026_07_07.md` for the alerting gap on top of this same
      guard, and the two currently-dark venues (LIGHTER, PACIFICA) it already missed. **DONE — reconciled 2026-07-28
      against `plans/archive/2026_07/foundation_gates_and_capture_to_100_2026_07_06.md` (`status: complete`, both own
      todos `[x]`).** G1.2: `record_failed` routing shipped `instruments-service@3c10615` (thin-day reclassify,
      captured→attempted_failed below 50%-of-14d-median) + metric `instruments-service@cc81cad`; 06-26 partial-cell
      follow-up VERIFIED 2026-07-06 (single-shard read: count 677 vs 678 baseline = 99.85%, correctly NOT reclassified —
      captured-with-healthy-count branch satisfied). G1.3: `instruments-service@79f2693` — fixed
      `_canonical_bare_venue_chain` to bypass the DeFi PROTOCOL-CHAIN split for cefi venues
      (LIGHTER-ZKSYNC/PACIFICA-SOLANA/EXTENDED-STARKNET), matching the writer's existing bypass; verified cefi `_index`
      already 100% glued for these venues. The operator-confirm caveat above (thin-day vs. DeFi-parity threshold) was
      not itself re-litigated by that plan — it stands as an open policy note, not a blocker on this checkbox's Gate.
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
      bullet. > **[NOTE 2026-07-28, reconciled]**: Stage 2b above is now `[x]` (D2 landed,
      `cefi_layer1_denominator_gaps_2026_07_03.md` resolved) — the internal-consistency condition this correction relied
      on has changed. Whether G4 itself is now signable is a fresh re-verify against
      `instruments_foundation_completeness_2026_06_24.md` (owned by this tracker's sibling
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` [AUDIT] "Reconcile GATE 0" todo, not this one) — not
      re-derived here; G4 stays annotated OPEN pending that dedicated re-check.
- [ ] [DATA] P1. tradfi **§8 retirement purge** (4-leg GCS delete — ICE / CBOE-OPRA / VX-spread / VIX-cash) —
      **OPERATOR-CONFIRM**. **STILL OPEN (reconciled 2026-07-28)** — genuinely operator-gated, not covered by any named
      archived child; expected to stay open per this todo's own instructions.
- [x] ✅ [DESIGN] P1. defi completeness **oracle** design. **DONE — reconciled 2026-07-28 against
      `plans/archive/2026_07/foundation_gates_and_capture_to_100_2026_07_06.md` (`status: complete`, own todo `[x]`,
      2026-07-06).** Design SSOT landed at `/codex/02-data/defi-completeness-oracle.md` (`unified-trading-pm@650c2b881`)
      — `CompletenessProbe` contract (expected_count from on-chain truth vs. enumerated_count from the IS catalogue,
      Tier-A/Tier-B probe kinds, fail-closed on empty/probe-failed) intended to replace DeFi's circular
      `EXPECTED = ENUMERATED` measurement. Design-only, as scoped — implementation follow-ons enumerated in the codex
      doc's §9 (note: the first implementation slice, the UAC `CompletenessProbe` schema itself, has since landed — see
      this doc's sibling AO batch's `[x]` **[SCHEMA] P0** todo, `unified-api-contracts@1407b7f`).

## Stage 5 — Capture to 100% (Layer-2 — only after Layer-1 is honest)

- [ ] [INFRA] P1. `data_completion` operator-gated items: ~~pyth `collect-oracle-prices` launch~~ · Live ODDS quota ·
      ~~MANTLE paid RPC~~ · CLOB-on-chain asset_group classification (**Lighter/Pacifica/Extended-Starknet, +
      HYPERLIQUID/ASTER — operator-confirmed 2026-07-07 same hybrid pattern: CEFI holds instrument definitions, DEFI
      holds chain classification**, see `issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`
      Update §3) · rate-limit probe VM. **STILL OPEN (reconciled 2026-07-28)**, credential/operator-gated, not covered
      by any archived child. **Retagged 2026-07-29**: pyth+MANTLE resolved (see struck clauses above).
- [x] ✅ [DATA] P1. Reconcile the DEDUP-flagged folded-in tail (from merged `path_to_100pct`) — **do not double-run**.
      **DONE — reconciled 2026-07-28 against `plans/archive/2026_07/foundation_gates_and_capture_to_100_2026_07_06.md`
      (`status: complete`, own todo `[x]`, 2026-07-06, Opus slot-3).** Both DEDUP-flagged items in
      `data_completion_to_100_all_ag_2026_06_21.md` §"Folded-in from `path_to_100pct_backfill_mtds_is_2026_06_17`"
      verified against their already-DONE/in-flight parent lanes (Step-0 enumerate = `instruments-service@38cec01` defi
      expected-universe re-seed; per-AG lanes = the 5 `[x]` per-AG launch-matrix items in `data_completion`) and closed
      as DEDUP-RECONCILED (flipped `[x]` with explicit "do NOT double-run" notes) in the parent plan — no new code
      shipped, PM-only plan flip.
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
- [x] ✅ [INFRA] P1. **Deribit `options_chain` — live runner**: wire a live cron/VM to run
      `--operation deribit-options-chain` (the handler is **live/replay only — no backfill**, `process()` collects
      `date.today()`), so it actually captures BTC/ETH `options_chain` daily → then feeds the Stage-3 re-measure.
      Historical options are NOT captured by this handler (separate concern if ever needed). **DONE — reconciled
      2026-07-28 against `plans/active/infra_capture_and_devops_leftovers_2026_07_06.md` (own todo `[x]`, shipped
      2026-07-07 by slot-3).** New one-shot worker launcher `scripts/vm/launch-deribit-options-chain-daily.sh`
      (`deployment-service@e18d585`) — e2-standard-2, singleton-locked on `deribit-opts-fwd-` prefix,
      `VM_SHUTDOWN_ON_COMPLETION=true`, fires `--operation deribit-options-chain --mode batch --asset-group CEFI` with
      today's UTC date; registered in the VM-prefix registry (`deribit-opts-fwd-` → `VmPrefixSpec`, EPHEMERAL_BATCH,
      distinct from the historical `opt-deribit-` Tardis batch prefix).
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
      "migrate-first 4 AGs"; `instruments_catalogue_incremental_rollup` → completed). **STILL OPEN (reconciled
      2026-07-28)** — targets docs outside this todo's 7 named archived children; not covered here.
- [x] ✅ [VERIFY] P2. `honest_coverage_smoke_harness`: run the deferred **cefi / defi / tradfi / prediction**
      live-verify slices (only sports ran). **DONE — reconciled 2026-07-28 against
      `plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md` (complete, own todo `[x]`, 2026-07-06,
      slot-9).** Gate satisfied via "discrepancy filed" (the item's own stated acceptance path): ran what exists live
      in-cloud and surfaced 4 discrepancies (tradfi runner catalogue-404/BLOCKED-PLAN2; prediction runner
      `BucketNamingError`; `run_live_verify_cefi.py`/`run_live_verify_defi.py` don't exist) at
      `plans/active/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` with actionable P2 fix todos. No
      data-correctness impact (Layer-1 certifications use a different, unaffected code path).
- [x] ✅ [DATA] P2. v9 `schema_version` tail re-stamp (quiet window, post fleet-drain). **DONE — reconciled 2026-07-28
      against `plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md` (resolved, own todo `[x]`, GATE MET
      2026-07-16).** The fleet-drain precondition (that blocked this across 15+ prior dispatch sessions) genuinely
      cleared (sustained 8.5-min zero-VM window, both clouds confirmed); the static 13,971-row v4 tail re-stamped; fresh
      corpus-wide read confirms 100% `schema_version=9` across tradfi, independently verified.
- [ ] [UI] P2. data-status **UI drill-down** (last open `honest_coverage_v2` item). **STILL OPEN (reconciled
      2026-07-28)** — not covered by any named archived child; the sibling `layer1_remeasure_and_certify` plan only
      annotated this item as MOVED here, it did not build it. `[UI]` gate applies — genuinely open.
- [x] ✅ [DESIGN] P2. Delete-or-document decision on instruments-service's dead `GET /api/data-status` endpoint (zero
      real HTTP consumers, only its own unit test). See
      `issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md`. **DONE — reconciled 2026-07-28.**
      `issues/instruments_service_data_status_endpoint_dead_code_2026_07_07.md` is `status: resolved`, both its own
      todos `[x]`: operator decided DELETE (2026-07-18), then deleted — `instruments-service@650dd4b7` (removed
      `api/data_status.py` + route registration + its unit test; re-verified no workspace caller at delete time; IS gate
      green, 4559 passed).
- [ ] [CODE] P2. Build a generic manifest-reprocessing utility (11 near-identical one-off reclassify scripts written
      across instruments-service + market-tick-data-service in 8 weeks; codex's own `script-homes.md` says a recurring
      need like this should graduate to a permanent tool). See
      `issues/manifest_reprocessing_generic_utility_2026_07_07.md`. **STILL OPEN (reconciled 2026-07-28)** — not covered
      by any named archived child; genuinely unbuilt.

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

- **2026-07-28 (gate-cleanup pass)** — updated the legacy-twin deletes note (Stage 1) to match its forked child's own
  2026-07-28 retag: the §3a reversibility carve-out now covers hard-stop #2 (legacy-object-delete-after-copy) once Part
  5's twin-coverage proof independently confirms 100% coverage
  (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a extended); see
  `/plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` for the retagged todo. No delete executed;
  this tracker's own item stays open pending that child plan's execution.
- **2026-07-28 — Stage 1–6 checkbox drift reconciled against 7 now-archived/complete AO children** (via
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s [ADMIN] P1 reconciliation todo). Grepped each named
  archived child's own checkboxes/Progress Log for shipped-SHA evidence, per unchecked tracker checkbox; flipped only
  what was genuinely evidenced (citations recorded inline on each item, not restated here). **Flipped `[x]`**: Stage 1
  TradFi v9 G4 apply; Stage 2 2b/2c/2d/2e-follow-on/2f; Stage 3 re-run `measure_honest_coverage` + close
  `honest_coverage_v2`; Stage 4 cefi G1.2+G1.3 + defi oracle design; Stage 5 DEDUP tail + Deribit live runner; Stage 6
  smoke-harness 4-AG slices + v9 schema tail re-stamp + dead `/api/data-status` endpoint deletion. **Left unchecked,
  annotated still-real** (not covered by the 7 named children): Stage 1 legacy-twin deletes; Stage 2c's 2 ASTER
  sub-items; Stage 3 tradfi Layer-1 certification (forked to `tradfi_consolidated_closeout_2026_07_18.md` Phase C) +
  ASTER missing-date reconciliation; Stage 4 tradfi §8 purge; Stage 5 `data_completion` operator-gated items; Stage 6
  stale-checkbox flip / UI drill-down / manifest-reprocessing utility. No code touched, no live measurement re-run.
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

> **Line-cap remediation (2026-08-03)**: every 2026-07-06/07-dated entry that used to follow this note (the D1-D5
> Decision Gate rulings, the 6-plan AO dispatch, TradFi v9 migration apply, the per-AG Layer-1 certifications, the
> turbo-API read-bug sweep, and the ASTER/CEFI data-status audit) was extracted verbatim to
> `/plans/archive/2026_08/instruments_completion_tracker_progress_log_history_2026_08_03.md` to bring this doc back
> under the 1000-line hard cap.

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
  `/plans/archive/issues/instruments_service_plan_reconciliation_2026_06_29.md`
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

**na-eligibility-audit 2026-08-03**: KEEP-NA, stale items. Closed 1 checkbox (generic manifest-reprocessing utility)
whose "STILL OPEN" note pre-dated its actual shipping+archival by 2 days. All other open items reviewed, no other
staleness found — doc stays `assigned_vm: NA`.
