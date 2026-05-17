---
title: "TradFi MVP — OHLCV-only Databento backfill (drop L1-L3 to post-cutover)"
slug: tradfi_ohlcv_only_mvp_backfill_2026_05_15
type: plan
status: active
created: 2026-05-15
deadline: 2026-05-23
owner: ikenna
parent_epic: tradfi_master_2026_05_07
asset_group: tradfi
priority: P1
locked_by: live-defi-rollout
locked_since: 2026-05-15
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
related_plans:
  - master_to_live_defi_2026_05_23
  - tradfi_master_2026_05_07
  - cefi_tradfi_tick_data_backfill_2026_04_10
  - market_tick_data_to_100pct_2026_05_05
codex_ssots:
  - codex/02-data/mtds-data-source-coverage-matrix.md
  - codex/02-data/availability-manifest-and-data-status.md
---

# TradFi MVP — OHLCV-only Databento backfill

## Deferred work — migrated to:

L1/L2/L3 tick data (tbbo / mbp_10 / trades) scope is intentionally DEFERRED to post-cutover per operator direction
2026-05-15 — successor: `plans/active/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` (to be created in Phase 7
HUMAN item below; seed table from "Scope (OUT)" section). The `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` constant in
MTDS holds the prior tick windows for forward-restore by that successor plan.

## Operator direction (2026-05-15)

> "lets to ohlcv 1m for all the tradfi mvp instruments only please and ping agent orchestrator to repurpose the slots to
> this and make plan fold under tradfi epic as this is cheapest solution also i want the full period for tradfi thats
> available"
>
> Follow-ups: "since 2019 1st jan at least" / "or 2020 whatever we are starting at" / "we can deal with the other data
> types later" / "no need for l1-l3 yet".

**Decision**: collapse TradFi MVP data-acquisition to OHLCV-only (L0). Drop `trades` / `tbbo` / `mbp_10` (L1 / L2 / L3)
from MVP scope — move to `post-cutover`. Backfill OHLCV to the full Databento-available period per (venue, instrument),
floored at 2019-01-01 (or 2020-01-01 where that matches workspace tick-data anchor convention).

**Cost rationale**: Databento OHLCV (~$20/dataset-month at PAYG vs $179/mo Standard subscription) is roughly 10-100×
cheaper than tick data (tbbo / trades / mbp_10). Standard tier covers L0 (~15+ years) but L2/L3 are 1-month-history and
L1 is 1-year-history — so PAYG for tick data on historical windows would dominate cost regardless of subscription. Going
OHLCV-only at PAYG collapses TradFi data cost to roughly bottom-of-bracket without compromising MVP archetype support
(CME options-derived skew + ML signals work off bar data; tick-level execution microstructure is post-cutover scope).

## Scope (IN — MVP, must ship by 2026-05-23)

Per [`codex/02-data/mtds-data-source-coverage-matrix.md`](../../codex/02-data/mtds-data-source-coverage-matrix.md)
TradFi venue × data_type matrix (current state); after this plan only OHLCV-grain remains in MVP:

| Venue  | data_type   | Source                                   | Start date (floor)                                |
| ------ | ----------- | ---------------------------------------- | ------------------------------------------------- |
| CME    | `ohlcv_1m`  | Databento `GLBX.MDP3`                    | 2019-01-01 OR Databento earliest, whichever later |
| ICE    | `ohlcv_1m`  | Databento `IFEU.IMPACT` / `IFUS.IMPACT`  | 2019-01-01 floor                                  |
| NASDAQ | `ohlcv_1m`  | Databento `XNAS.ITCH`                    | 2019-01-01 floor                                  |
| NYSE   | `ohlcv_1m`  | Databento `XNYS.PILLAR` / `XCHI.PITCH`   | 2019-01-01 floor                                  |
| CBOE   | `ohlcv_15m` | Barchart (preload) + Yahoo (rolling 60d) | already-shipped per VIX-layering rule             |
| FX     | `ohlcv_24h` | (existing daily-only source — unchanged) | unchanged                                         |

**TradFi MVP instrument universe**: per existing
[`unified_api_contracts.registry.tradfi_ticker_universe`](../../../unified-api-contracts/unified_api_contracts/registry/tradfi_ticker_universe.py)
(`SP500_TICKERS` + `ETF_TICKERS` + CME futures roots: ES, MES, NQ, MNQ, CL, GC + CBOE VIX). No new instruments added by
this plan — scope is only the data-type collapse.

## Scope (OUT — moved to post-cutover plan)

These data_types are NOT collected for MVP. Each gets a row in
`plans/active/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` (spawned as successor plan from this one — to be
drafted post-cutover):

| Venue × data_type               | Was-in-scope (pre-2026-05-15)                    | New scope        |
| ------------------------------- | ------------------------------------------------ | ---------------- |
| `CME tbbo` (L1)                 | May 2023 + Jun 2024 reference months             | **POST-CUTOVER** |
| `CME trades` (L2-ish)           | May 2023 + Jul 2024 reference months             | **POST-CUTOVER** |
| `CME mbp_10` (L3 book-depth)    | May 2023 + Jun 2024 (declared, adapter deferred) | **POST-CUTOVER** |
| `ICE tbbo` / `ICE trades`       | May + Jul reference months                       | **POST-CUTOVER** |
| `NASDAQ tbbo` / `NASDAQ trades` | May + Jul reference months                       | **POST-CUTOVER** |
| `NYSE tbbo` / `NYSE trades`     | May + Jul reference months                       | **POST-CUTOVER** |

**Reason for deferral**: archetypes shipping for May-23 cutover (DeFi `carry_staked_basis` +
`arbitrage_price_dispersion`, plus optional TradFi `cme_polymarket_arb`) do NOT require tick-level execution
microstructure. ML signals + skew + basis all compute off OHLCV. Tick data re-enters scope when execution-tuning
archetypes ship post-cutover.

## Code changes required

These are the surgical edits the slot owner ships. Each is a small diff (<30 LOC), bundled with a flip-checkbox commit
per workspace HARD RULE.

### Phase 1 — UAC constant changes (single commit)

- [x] ✅ **[SCRIPT] P0. UAC TRADFI_TICK_DATA_WINDOWS = [] + \_DEFERRED preserved.** slot-1-main 2026-05-17 09:00 UTC at
      `unified-api-contracts@886ad9c`. `is_in_tradfi_tick_window()` now returns False for every date (any([])
      short-circuit). 2 prior windows preserved in `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS`. Smoke-import verified:
  - Set `TRADFI_TICK_DATA_WINDOWS = []` (was `[May 2023, Jul 2024]`) — empty list = "no MVP tick windows; only OHLCV".
  - Set `VENUE_DATA_TYPE_COVERAGE_WINDOWS` to drop `("CME", "tbbo")` and `("CME", "mbp_10")` entries (move them to a
    separate `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` module-level constant for forward-reference by the
    post-cutover plan).
  - Update docstring on `TRADFI_TICK_DATA_WINDOWS` to reference this plan as the operator-acked source of truth for the
    OHLCV-only decision.

### Phase 2 — UAC capability matrix update

- [x] ✅ **[SCRIPT] P0. VENUE_DATA_TYPE_CAPABILITIES drop trades+tbbo from TradFi venues + backdate CME/ICE.**
      slot-1-main 2026-05-17 09:00 UTC at `unified-api-contracts@886ad9c` (same commit as Phase 1). NASDAQ/NYSE:
      ohlcv_1m only at 2023-04-15. CME/ICE: ohlcv_1m only at 2019-01-01 (operator full-period ask).
      CBOE/FX/BARCHART/YAHOO_FINANCE/Sports/Prediction unchanged.
  - For `CME` / `ICE` / `NASDAQ` / `NYSE`: remove `trades` and `tbbo` entries (move to a
    `_POST_CUTOVER_TRADFI_TICK_CAPABILITIES` deferred dict).
  - Keep `ohlcv_1m` entries with start dates set to `2019-01-01` (or earlier if Databento's earliest is earlier).

### Phase 3 — Coverage matrix codex update

- [x] ✅ **[SCRIPT] P0. Codex coverage matrix § 3 TRADFI updated.** slot-1-main 2026-05-17 09:05 UTC at
      `unified-trading-pm@e944dae2`. Venue × data_type table shows ohlcv_1m-only with backdated CME/ICE; trades + tbbo
      rows in coverage-axes table marked DEFERRED-post-cutover. Header callout points to this plan + the successor
      restoration plan.
  - Update CME / ICE / NASDAQ / NYSE rows to list only `ohlcv_1m` under "expected data_types".
  - Add a `## Deferred to post-cutover` section listing the L1-L3 data_types with reference to this plan.

### Phase 4 — MTDS orchestrator side-effect verification

- [x] ✅ **[AGENT] P0. is_in_tradfi_tick_window empty-windows contract pinned.** slot-5-ikenna 2026-05-17 at
      `unified-api-contracts@8aa36c1`. 13 unit tests in `tests/unit/test_tradfi_ohlcv_only_mvp.py` pin: (1)
      `TRADFI_TICK_DATA_WINDOWS == []`; (2) `is_in_tradfi_tick_window()` returns False parametrised across 6 dates
      (2019-01-01, mid-2023-05 prior window, mid-2024-07 prior window, today, 2099-12-31); (3)
      `_DEFERRED_TRADFI_TICK_DATA_WINDOWS` preserves the 2 prior windows; (4) `VENUE_DATA_TYPE_COVERAGE_WINDOWS == {}`;
      (5) `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` preserves CME tbbo + mbp_10; (6) live
      `VENUE_DATA_TYPE_CAPABILITIES[CME/ICE/NASDAQ/NYSE]` regression guard — only ohlcv_1m, no trades/tbbo. 13/13 pass;
      orchestrator `any([])` short-circuit verified by inspection (gate at orchestrator.py:3014 is the original spec
      quoted in plan). MTDS-side suppression is contract-pinned.

### Phase 5 — Phantom-row reconciliation

- [x] ✅ **[SCRIPT] P0. TradFi trades+tbbo manifest reconciled.** slot-1-main 2026-05-17 09:55 UTC. Added new enum value `EmptyConfirmedReason.EXPECTED_OUT_OF_COVERAGE_WINDOW` at `unified-api-contracts@585de75` (distinct from EXPECTED_DEPRECATED_DATA_TYPE — this is SCOPE SHRINK that may reverse post-cutover). One-shot reconciliation flipped all 39,048 TradFi trades+tbbo rows in `gs://market-data-tick-tradfi-central-element-323112/_index/availability_index.parquet` to `capture_status=empty_confirmed, error_reason=EXPECTED_OUT_OF_COVERAGE_WINDOW`. Pre-flip: 20,972 captured + 9,162 empty_confirmed + 2,927 attempted_failed across CME/ICE/NASDAQ/NYSE/BARCHART/CBOE/FX/YAHOO_FINANCE. Post-flip: 10,279 tbbo + 28,769 trades all empty_confirmed. Non-target rows: 102,368 unchanged. Existing parquets on GCS preserved (audit trail). Local backup: `/tmp/tradfi_manifest.parquet.backup-20260517T085342`.

  **NEXT STEP** below was original plan text:
      re-classify as `empty_confirmed` with reason = `EXPECTED_OUT_OF_COVERAGE_WINDOW` (existing UAC enum) OR delete +
      flip to `expected_unattempted`. Decision: re-classify in place; preserves audit trail of prior captures. Use
      existing
      [`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`](../../../instruments-service/scripts/reconcile_phantom_manifest_rows_all.py)
      with `--asset-group tradfi --apply` extended for this case.

### Phase 6 — Backfill VM launchers (per-venue, per-data_type)

- [ ] [SCRIPT] P0. Create per-(venue, data_type) backfill launchers under `deployment-service/scripts/vm/` per launcher
      SSOT:
  - `launch-tradfi-bf-cme-ohlcv-1m.sh` (CME ES + MES + NQ + MNQ + CL + GC roots; 2019-01-01 → today)
  - `launch-tradfi-bf-ice-ohlcv-1m.sh`
  - `launch-tradfi-bf-nasdaq-ohlcv-1m.sh` (SP500 + ETF tickers per `tradfi_ticker_universe`)
  - `launch-tradfi-bf-nyse-ohlcv-1m.sh` (SP500 + ETF tickers)
  - VM naming: `tradfi-bf-<venue>-ohlcv-1m-<YYYYMMDD-HHMMSS>` matching `VM_PREFIX_TO_BUCKET` registry.
  - Per-VM shard isolation: `VM_NAME=<unique> MANIFEST_PER_VM_SHARDS=true`.
  - Active event-stream verification: STARTED within 60s + ≥1 progress/hour + STOPPED at exit (per CLAUDE.md).

### Phase 7 — Backfill execution + 4-pillar validation

- [ ] [AGENT] P0. Launch the 4 VMs (CME / ICE / NASDAQ / NYSE) in parallel. Drain ETA: 2-4 hours per venue at Databento
      OHLCV throughput (cheap = fast).
- [ ] [AGENT] P0. Post-drain, 4-pillar validation per shard: (1) row count > 0 OR `record_empty`; (2) NaN ratio <
      threshold; (3) schema matches contract; (4) cluster coverage ≥ expected (per
      [shard-granularity SSOT](../../codex/04-architecture/shard-level-failure-isolation.md)).
- [ ] [AGENT] P0. Data-status rollup verifies CME / ICE / NASDAQ / NYSE OHLCV coverage ≥99% from 2019-01-01 → today;
      surface in deployment-ui.

### Phase 8 — Cost tracking + operator sign-off

- [ ] [AGENT] P1. Track actual Databento PAYG spend per VM run; emit `DATABENTO_PAYG_SPEND` event from each VM at
      completion (USD spend per dataset-month-symbol). Roll up to a single dashboard row in deployment-ui.
- [ ] [HUMAN] P0. Operator sign-off on actual spend vs projected (~$50-200 estimated for the full 2019-2026 ohlcv_1m
      backfill across CME/ICE/NASDAQ/NYSE — projection refined post-Phase 7).

### Phase 9 — Spawn successor plan for L1-L3 post-cutover

- [ ] [HUMAN] P1. After cutover, create `plans/active/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` capturing
      the deferred L1-L3 scope (the table in "Scope (OUT)" above is the seed). Reference
      `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` from Phase 1 as the canonical window list to restore.

## Codex SSOT updates

- [ ] [`codex/02-data/mtds-data-source-coverage-matrix.md`](../../codex/02-data/mtds-data-source-coverage-matrix.md) § 3
      — Phase 3 above.
- [x] [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
      — slot-5-ikenna 2026-05-17: added `is_in_tradfi_tick_window` empty-mode addendum under § "Per-asset-group +
      per-data-source empty-rule asymmetry" pointing to this plan + the post-cutover successor; references the Phase 4
      contract-pin tests at `unified-api-contracts@8aa36c1`. `is_in_tradfi_tick_window` reference — note that empty
      windows = OHLCV-only mode (intentional).
- [ ] No new codex stub required — this plan is a scope narrowing within existing matrix, not a new pattern.

## Slot reassignment ask (slot 1 main pings to follow)

This plan is non-trivial across 4 phases and 9 todo blocks. Per CLAUDE.md "Slot precedence", slot 1 main owns work-split
changes — see `ikenna_orchestrator/pings/slot_1.md` ping at session 2026-05-15 for the explicit re-allocation ask.
Recommended slot mapping:

| Phase                       | Recommended slot               | Rationale                                                                                                  |
| --------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| Phase 1 + 2 (UAC constants) | **slot 5** (TradFi)            | Slot 5 already owns "TradFi Item 2 cascade + tradfi backfill prep" — natural fit                           |
| Phase 3 (codex)             | **slot 5**                     | Doc update co-located with the code change                                                                 |
| Phase 4 (orchestrator test) | **slot 5**                     | MTDS-side test; same surface                                                                               |
| Phase 5 (phantom reconcile) | **slot 8**                     | Slot 8 already owns "SHARD_AXIS_MATRIX drift + audit cleanup + ops verification" — phantom audit is theirs |
| Phase 6 (VM launchers)      | **slot 5** or **harsh slot 6** | Mechanical script creation                                                                                 |
| Phase 7 (backfill run)      | **slot 5** + monitor           | Long-running; needs operator backfill approval gate (≥1 week of data = approval required per CLAUDE.md)    |
| Phase 8 (cost tracking)     | **slot 7**                     | Slot 7 owns Treasury rollup + audit                                                                        |
| Phase 9 (successor plan)    | **slot 1 main**                | Plan creation post-cutover                                                                                 |

## Cross-plan impact

- [`tradfi_master_2026_05_07.md`](../epics/tradfi_master_2026_05_07.md) — this plan supersedes the `trades` / `tbbo`
  references in the TradFi-half tick-data backfill items. Epic's Phase X "5-VM-drain ETA 2026-05-08" residual + IBIT
  NASDAQ trades cold-backfill + ES_OPT trades backfill items are all DEFERRED-post-cutover by this scope change.
- [`cefi_tradfi_tick_data_backfill_2026_04_10`](../archive/cefi_tradfi_tick_data_backfill_2026_04_10.plan.md) — TradFi
  half effectively scope-narrowed to OHLCV-only.
- [`cme_polymarket_arb_2026_05_08.md`](./cme_polymarket_arb_2026_05_08.md) — confirm archetype runs on OHLCV-only (no
  tick dependency); if it does NOT, ESCALATE to operator before Phase 1 ships.
- [`master_to_live_defi_2026_05_23.md`](./master_to_live_defi_2026_05_23.md) — slot 1 main folds this row into the
  dependency graph + Group readiness matrix (this plan can't edit master directly per slot precedence).

## Full-Execution Criterion (per CLAUDE.md "Plans Run To Actual Completion")

- 4 backfill VMs (CME / ICE / NASDAQ / NYSE) drained.
- Data-status rollup shows ≥99% OHLCV coverage 2019-01-01 → today for each venue's MVP instrument universe.
- 4-pillar validation passes per shard.
- Phantom reconciliation: zero `trades` / `tbbo` rows with `capture_status=captured` outside the prior 2-window scope
  (i.e. no orphan tick captures lingering in manifest).
- UAC constants + codex matrix + epic all reflect the OHLCV-only state.
- Operator sign-off on actual Databento PAYG spend.
- Successor plan for L1-L3 post-cutover filed.

## Estimate

- baseline: 4 ai-days (Phase 1-2 constants ~0.3, Phase 3 codex ~0.2, Phase 4 test ~0.3, Phase 5 reconcile ~0.8, Phase 6
  launchers ~0.5, Phase 7 backfill monitor ~1, Phase 8 cost ~0.5, Phase 9 plan stub ~0.3)
- class: `infra` (multiplier 0.8×)
- calibrated: **3.2 ai-days** total; parallel execution across slots brings wall-clock to ~1-1.5 calendar days.

## Temporary states + their canonical follow-up plans

- `TRADFI_TICK_DATA_WINDOWS = []` (empty) → successor restoration in
  `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md` (Phase 9 above).
- `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` (new constant holding the prior tick windows for forward reference) →
  same successor plan restores into `VENUE_DATA_TYPE_COVERAGE_WINDOWS`.
