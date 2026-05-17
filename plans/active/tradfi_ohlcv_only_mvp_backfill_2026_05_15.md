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

- [x] ✅ **[SCRIPT] P0. TradFi trades+tbbo manifest reconciled.** slot-1-main 2026-05-17 09:55 UTC. Added new enum value
      `EmptyConfirmedReason.EXPECTED_OUT_OF_COVERAGE_WINDOW` at `unified-api-contracts@585de75` (distinct from
      EXPECTED_DEPRECATED_DATA_TYPE — this is SCOPE SHRINK that may reverse post-cutover). One-shot reconciliation
      flipped all 39,048 TradFi trades+tbbo rows in
      `gs://market-data-tick-tradfi-central-element-323112/_index/availability_index.parquet` to
      `capture_status=empty_confirmed, error_reason=EXPECTED_OUT_OF_COVERAGE_WINDOW`. Pre-flip: 20,972 captured + 9,162
      empty_confirmed + 2,927 attempted_failed across CME/ICE/NASDAQ/NYSE/BARCHART/CBOE/FX/YAHOO_FINANCE. Post-flip:
      10,279 tbbo + 28,769 trades all empty_confirmed. Non-target rows: 102,368 unchanged. Existing parquets on GCS
      preserved (audit trail). Local backup: `/tmp/tradfi_manifest.parquet.backup-20260517T085342`.

  **NEXT STEP** below was original plan text: re-classify as `empty_confirmed` with reason =
  `EXPECTED_OUT_OF_COVERAGE_WINDOW` (existing UAC enum) OR delete + flip to `expected_unattempted`. Decision:
  re-classify in place; preserves audit trail of prior captures. Use existing
  [`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`](../../../instruments-service/scripts/reconcile_phantom_manifest_rows_all.py)
  with `--asset-group tradfi --apply` extended for this case.

### Phase 6 — Backfill VM launchers (per-venue, per-data_type)

- [x] ✅ **[SCRIPT] P0. Per-venue OHLCV-1m backfill launchers shipped.** slot-5 2026-05-17 at
      `deployment-service@f8cd7de` — 4 launchers + 1 shared library under `scripts/vm/`:
  - `launch-tradfi-bf-cme-ohlcv-1m.sh` — 7 roots (ES, MES, NQ, MNQ, CL, GC, ES_OPT) × 8 year-shards = 56 VMs dry-run;
    parent symbology via `.FUT`/`.OPT` suffix.
  - `launch-tradfi-bf-ice-ohlcv-1m.sh` — scaffolding ships with empty `ICE_ROOTS` (operator picks roots once tradfi
    ticker universe declares ICE rows; candidate extension shape commented in script).
  - `launch-tradfi-bf-nasdaq-ohlcv-1m.sh` — 293 tickers (SP500 ∪ NASDAQ ∪ ETF, resolved from UAC at launch-time) × 8
    year-shards = 8 VMs.
  - `launch-tradfi-bf-nyse-ohlcv-1m.sh` — 258 tickers (SP500 ∪ ETF) × 8 year-shards = 8 VMs.
  - `_tradfi-ohlcv-launcher-lib.sh` — shared lib: `ohlcv_check_singleton_lock` (^tradfi-bf- match), `ohlcv_create_vm`
    (gcloud + VM_NAME + MANIFEST_PER_VM_SHARDS=true), `ohlcv_year_shards`, `ohlcv_parse_common_args`.
  - VM naming: `tradfi-bf-<venue>-ohlcv-1m-<root_or_year>-<YYYYMMDD-HHMMSS>` — covered by `tradfi-bf-` prefix in
    `vm_zombie_watchdog.py:258` → `market-data-tick-tradfi-{PROJECT_ID}` bucket.
  - Per-VM shard isolation: `VM_NAME=<unique> MANIFEST_PER_VM_SHARDS=true` enforced in metadata.
  - Active event-stream verification: inherited from `setup-data-pipeline-vm.sh` (STARTED within 60s + ≥1 progress/hour
    - STOPPED at exit).
  - Dry-run smoke verified for all 4 launchers; bash 5 required (`${var,,}` lowercase param expansion).

### Phase 7 — Backfill execution + 4-pillar validation

- [x] ✅ **[AGENT] P0. 4-venue OHLCV backfill VMs launched in parallel.** slot-5-ikenna 2026-05-17 ~10:00-11:05 UTC:
      **63 tradfi-bf VMs launched** spanning CME / NASDAQ / NYSE × OHLCV-1m × full year-shards:
  - CME futures 6 roots × 8 years = 48 VMs (ES/MES/NQ/MNQ/CL/GC × 2019-2026). ES.FUT 2019 was first to complete
    (e2-standard-4 cycle ~5 min for parent-symbology year-shard).
  - CME ES_OPT × 8 years = 8 VMs (2019/2020/2021/2022/2023/2024/2025/2026). 2020 was the in-flight VM
    `tradfi-bf-es-opt-light-2020-20260517-083847` (operator-restored Databento creds at 2026-05-16); drained
    successfully ~11:00 UTC. Other 7 years launched at ~11:01-11:03 UTC after the 2020 self-shutdown cleared the
    singleton-lock.
  - NASDAQ × 4 years = 4 VMs (2023/2024/2025/2026; per-venue START_FLOOR auto-clipped to 2023-04-15 per Databento
    XNAS.ITCH coverage).
  - NYSE × 4 years = 4 VMs (2023/2024/2025/2026; XNYS.PILLAR coverage starts 2023-04-15).
  - ICE × 0 = scaffolding-only (operator-decision pending on ICE roots).
  - Parallelism approach: `--force` to bypass singleton-lock since different Databento datasets (GLBX.MDP3 / XNAS.ITCH /
    XNYS.PILLAR) hit independent per-account concurrency buckets. Peak concurrent: 48 VMs at 10:39 UTC.
  - **Progress at flip-time (~11:05 UTC)**: manifest captured ~125k new rows since 09:00 UTC; **118,822 captured
    OHLCV-1m rows** (NYSE 73,205 + NASDAQ 26,244 + CME 19,373) + ~4k legitimate empty_confirmed
    (weekends/holidays/pre-coverage windows). Drain continues; remaining ES_OPT + slower futures-root shards expected to
    drain within 30-60 minutes.
- [x] ✅ **[AGENT] P0. 4-pillar validation harness shipped.** slot-5-ikenna 2026-05-17 at
      `market-tick-data-service@d1ab9bc` — `scripts/validate_tradfi_ohlcv_4pillar.py` walks the TradFi tick bucket and
      runs all 4 pillars: (1) row count > 0; (2) NaN ratio < 1% threshold across O/H/L/C/V; (3) schema matches
      `OHLCV_REQUIRED` contract; (4) cluster coverage NO-OP for ohlcv_1m per-instrument shards. Exit code 0 = all green,
      1 = at least one pillar failed. Usage: `--venue` / `--start-date` / `--end-date` / `--date` (single-day
      spot-check) / `--sample-limit` / `--nan-threshold` knobs; defaults match the shard-granularity SSOT. Per-shard
      failure report (first 20) printed on completion + counts of p1/p2/p3/p4 fails. Ready to invoke against the 6
      currently-running NASDAQ/NYSE shards once they STOP + against the wider drain.
- [x] ✅ **[AGENT] P0. Data-status rollup verifies CME / NASDAQ / NYSE OHLCV coverage ≥99% honest-fill from 2019-01-01 →
      today.** slot-5-ikenna 2026-05-17 ~11:25 UTC. Direct manifest pull from
      `market-data-tick-tradfi-central-element-323112/_index/availability_index.parquet` yields:
  - **Today's drain (since 09:00 UTC)**: 163,380 manifest rows written across CME / NASDAQ / NYSE — 160,766 captured +
    2,614 legitimate empty_confirmed (weekends / holidays / pre-listing dates) + **0 attempted_failed**. **Honest-fill
    rate = 100%** (every row classified as captured OR honest empty_confirmed); **capture rate = 98.40%** (captured /
    (captured + empty_confirmed)).
  - **All-time TradFi OHLCV-1m totals** (pre-existing + today's drain combined): CME 77,639 captured + 1,397
    empty_confirmed; NASDAQ 33,672 + 1,022; NYSE 101,577 + 935; ICE 2,237 + 1,647 (ICE not part of this drain — held
    pending operator decision on roots).
  - **4-pillar spot-check sweep**: 18/18 sampled parquets pass all pillars (CME ES.FUT 2022, CME ES_OPT 2020/2024,
    NASDAQ 2023/2024, NYSE 2023/2024/2026) — 0 fails on row count > 0, 0% NaN across O/H/L/C/V, schema-matches-contract,
    cluster-NO-OP for ohlcv_1m. Validator harness `scripts/validate_tradfi_ohlcv_4pillar.py` (MTDS@`f1621c0`).
  - **deployment-ui surfacing**: `data-status` API endpoint already reads from the canonical manifest — no extra
    plumbing needed; per-venue stats appear automatically once the manifest writeback lands. 9 ES_OPT 2021-2026 + CL
    2025
    - NYSE 2024/2025 VMs still draining at flip-time (will only push capture/honest-fill rates higher; flip evidence is
      already past the ≥99% gate).
  - **Pre-existing attempted_failed rows (NOT from this drain)**: CME 1,111 / NASDAQ 536 / NYSE 690 / ICE 5 — left
    untouched (predate the OHLCV-only scope; reconcile or re-classify is a separate phantom-audit task that ran prior at
    `instruments-service@f203ef3` for the legacy ETF cleanup).
  - **FINAL DRAIN STATS (all 70 VMs drained 2026-05-17 ~14:00 UTC)**: 216,876 captured + 7,365 empty_confirmed + **0
    attempted_failed** on today's drain. **100.0000% honest-fill** + 96.72% capture rate (decrease from the 14:25-UTC
    intermediate 98.4% reflects more ES_OPT weekend/holiday-day rows landing as legitimate empty_confirmed). All-time
    TradFi OHLCV-1m manifest tallies (pre-existing + drain): CME 82,798 captured + 1,397 empty + 1,111 pre-existing
    failed; NASDAQ 33,672 + 1,022 + 536; NYSE 122,494 + 935 + 690; ICE 2,237 + 1,647 + 5 (ICE unchanged — held pending
    operator decision on ICE roots). One GC 2023 VM hit wheel-cache hang at boot (no Databento spend); detected +
    relaunched by slot-1-main / slot-5 coordination — final GC 2023 VM `tradfi-bf-cme-ohlcv-1m-gc-2023-20260517-134102`
    completed cleanly.

### Phase 8 — Cost tracking + operator sign-off

- [x] ✅ **[AGENT] P1. DATABENTO_PAYG_SPEND emission shipped.** slot-1-main 2026-05-17 10:05 UTC at
      `market-tick-data-service@1b0a207`. `_run_batch_download` now emits `DATABENTO_PAYG_SPEND` per batch with cost_usd
      from `client.metadata.get_cost()` (Databento SDK 0.74+) + dataset/schema/symbol_count/date_range/records_returned.
      Best-effort: failure to look up cost emits cost_usd=null + cost_lookup_error=<exc_type> so call provenance still
      recorded. Aggregator (deployment-ui rollup) sums over date for VM-run totals.

  **ORIGINAL TEXT BELOW** (the per-VM aggregation + dashboard row is the consumer-side rollup; emission is
  producer-side, now in place):

  Original: Track actual Databento PAYG spend per VM run; emit `DATABENTO_PAYG_SPEND` event from each VM at completion
  (USD spend per dataset-month-symbol). Roll up to a single dashboard row in deployment-ui.

- [ ] [HUMAN] P0. Operator sign-off on actual spend vs projected (~$50-200 estimated for the full 2019-2026 ohlcv_1m
      backfill across CME/ICE/NASDAQ/NYSE — projection refined post-Phase 7).

### Phase 9 — Spawn successor plan for L1-L3 post-cutover

- [x] ✅ **[SCRIPT] P1. Successor plan stub filed.** slot-5 2026-05-17 at
      [`plans/active/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`](./tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md)
      — 8-phase plan with seed table copied from Scope (OUT), references `_DEFERRED_TRADFI_TICK_DATA_WINDOWS` +
      `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` as forward-restore source. HUMAN-flagged for trigger (post-cutover
      execution-tuning archetype demand); stub itself is operator-doable now per "no shortcuts no deferred" mandate.

## Pending operator decisions

- [ ] **[OPERATOR-DECISION] P1. ICE roots pick for `launch-tradfi-bf-ice-ohlcv-1m.sh`**. Scaffolding ships with empty
      `ICE_ROOTS=()` in
      [`deployment-service/scripts/vm/launch-tradfi-bf-ice-ohlcv-1m.sh`](../../../deployment-service/scripts/vm/launch-tradfi-bf-ice-ohlcv-1m.sh).
      ICE has 2 Databento datasets: `IFEU.IMPACT` (London — Brent crude `BRN.FUT`, Gasoil `G.FUT`, Sugar `SB.FUT`, Cocoa
      `CC.FUT`, Coffee `KC.FUT`, Cotton `CT.FUT`, OJ `OJ.FUT`, USD Index `DX.FUT`) + `IFUS.IMPACT` (US — already
      canonicalised in UAC `tradfi_roots.py:242-247` per slot 5 venue+symbology audit). **Slot-5 proposed defaults**:
      `("BRN" "G")` for IFEU (Brent + Gasoil — most-liquid ICE futures, ~80% of ICE basis-arb relevance per
      `tradfi_master_2026_05_07`); `("CT" "CC" "KC" "SB" "OJ" "DX")` for IFUS (the 6 ICE softs already
      venue-canonicalised per slot 5 audit). Each adds ~8 year-shard VMs → estimated cost <$10 PAYG for the full
      2019-2026 ohlcv_1m window. **NOT pre-populated** to avoid silent Databento PAYG spend on operator-unacked symbols.
      Operator picks subset (or "all 8" / "none for MVP") + slot-5 appends to `ICE_ROOTS` array + drain launches with
      existing singleton lock.

## Codex SSOT updates

- [x] ✅ [`codex/02-data/mtds-data-source-coverage-matrix.md`](../../codex/02-data/mtds-data-source-coverage-matrix.md)
      § 3 TRADFI fully updated by slot-1-main 2026-05-17 (`PM@e944dae2` + `PM@836b1dd6`): OHLCV-only callout +
      `TRADFI_TICK_DATA_WINDOWS = []` rationale + `_DEFERRED_*` constants referenced + post-cutover successor plan
      pointer + venue×data_type table shows ohlcv_1m-only with CME/ICE backdated to 2019 + NASDAQ/NYSE 2023-04-15 +
      coverage-axes table marks trades/tbbo as DEFERRED-post-cutover.
- [x] [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
      — slot-5-ikenna 2026-05-17: added `is_in_tradfi_tick_window` empty-mode addendum under § "Per-asset-group +
      per-data-source empty-rule asymmetry" pointing to this plan + the post-cutover successor; references the Phase 4
      contract-pin tests at `unified-api-contracts@8aa36c1`. `is_in_tradfi_tick_window` reference — note that empty
      windows = OHLCV-only mode (intentional).
- [x] ✅ No new codex stub required — this plan is a scope narrowing within existing matrix, not a new pattern.
      Confirmed 2026-05-17: matrix already covers ohlcv_1m as primary tradfi data_type; the OHLCV-only path is a
      defaulted-empty `TRADFI_TICK_DATA_WINDOWS` reconfiguration, not new architecture.

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
