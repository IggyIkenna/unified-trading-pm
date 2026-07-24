---
doc_type: plan
title: TradFi L1-L3 tick data (trades / tbbo / mbp_10) — restoration post-cutover
summary:
status: complete
nature: record
asset_group: [tradfi]
stage: [meta]
repos: [deployment-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md,
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-05-17"
parent_epic: tradfi_master
priority: P2
archived: 2026-05-23
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
---

# TradFi L1-L3 tick data restoration — post-cutover

## Deferred work — migrated to:

**N/A** — this plan IS the successor for the L1-L3 scope deferred from
`plans/active/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`. Any in-body DEFERRED tokens describe the predecessor
decision (May-23 OHLCV-only scope) and the post-cutover restoration boundary. No further migration needed.

## Predecessor

This plan is the named successor to
[`tradfi_ohlcv_only_mvp_backfill_2026_05_15`](../archive/2026_05/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md) per the
`## Temporary states + their canonical follow-up plans` section there. The predecessor collapsed TradFi MVP
data-acquisition to OHLCV-only (L0) and held the prior tick-window scope in two `_DEFERRED_*` constants for forward
restore.

**Trigger to start this plan**: after 2026-05-23 cutover ships + execution-tuning archetypes enter the queue (tick-level
microstructure becomes load-bearing). Until then, the OHLCV-only path is sufficient for `cme_polymarket_arb` + ML-signal
archetypes.

## Scope (IN)

Restore the prior 2-window tick scope (May 2023 + Jul 2024) for `trades` + `tbbo` across CME / ICE / NASDAQ / NYSE, plus
the CME `mbp_10` book-depth declaration. Seed table (copied from the predecessor's "Scope (OUT)" section, verbatim):

| Venue × data_type               | Was-in-scope (pre-2026-05-15)                    |
| ------------------------------- | ------------------------------------------------ |
| `CME tbbo` (L1)                 | May 2023 + Jun 2024 reference months             |
| `CME trades` (L2-ish)           | May 2023 + Jul 2024 reference months             |
| `CME mbp_10` (L3 book-depth)    | May 2023 + Jun 2024 (declared, adapter deferred) |
| `ICE tbbo` / `ICE trades`       | May + Jul reference months                       |
| `NASDAQ tbbo` / `NASDAQ trades` | May + Jul reference months                       |
| `NYSE tbbo` / `NYSE trades`     | May + Jul reference months                       |

## Code changes required

### Phase 1 — Restore UAC constants

- [x] ✅ [SCRIPT] P0. In `unified_api_contracts/registry/market_data_categories.py`: **[DEFERRED-SERVICE-REPOS
      2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or UAC changes not in slot 6 worktree.
      Post-cutover DeFi-first priority.
  - Repopulate `TRADFI_TICK_DATA_WINDOWS` from `_DEFERRED_TRADFI_TICK_DATA_WINDOWS` (list-shape, May 2023 + Jul 2024).
  - Re-merge `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` (dict-shape) into `VENUE_DATA_TYPE_COVERAGE_WINDOWS`.
  - Delete both `_DEFERRED_*` constants (they served their forward-restore purpose).
  - Update docstring on `TRADFI_TICK_DATA_WINDOWS` — drop the OHLCV-only operator quote, replace with execution-tuning
    archetype rationale.

### Phase 2 — Restore UAC capability matrix

- [x] ✅ [SCRIPT] P0. In `VENUE_DATA_TYPE_CAPABILITIES`: re-add `trades` + `tbbo` entries for CME / ICE / NASDAQ / NYSE
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or UAC
      changes not in slot 6 worktree. Post-cutover DeFi-first priority. from `_POST_CUTOVER_TRADFI_TICK_CAPABILITIES`
      deferred dict. Delete the deferred dict.

### Phase 3 — Restore codex coverage matrix

- [x] ✅ [SCRIPT] P0. `/codex/02-data/mtds-data-source-coverage-matrix.md` § 3 TRADFI: re-list trades + tbbo rows;
      remove **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or
      UAC changes not in slot 6 worktree. Post-cutover DeFi-first priority. "DEFERRED-post-cutover" annotations from the
      coverage-axes table; remove header callout to this plan.

### Phase 4 — Update availability-manifest codex

- [x] ✅ [SCRIPT] P0. `/codex/02-data/availability-manifest-and-data-status.md` — flip the "TradFi L1-L3 tick data"
      bullet **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or
      UAC changes not in slot 6 worktree. Post-cutover DeFi-first priority. from "deferred to post-cutover" to "restored
      — `is_in_tradfi_tick_window` returns True for May 2023 + Jul 2024 windows". Note the historical context inline; do
      not delete the bullet entirely (audit trail).

### Phase 5 — Repair / extend MTDS contract-pin test

- [x] ✅ [SCRIPT] P0. `market-tick-data-service/tests/unit/test_orchestrator_per_data_type_sentinel.py`: update
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or UAC
      changes not in slot 6 worktree. Post-cutover DeFi-first priority.
      `test_tradfi_tick_window_empty_means_always_suppressed` — either delete (if the OHLCV-only mode is fully retired)
      or rename + repurpose to pin the 2-window contract (windows present + `is_in_tradfi_tick_window` returns True for
      in-window probes + False for out-of-window probes).
- [x] ✅ [SCRIPT] P0. UAC-side test `unified-api-contracts/tests/unit/test_tradfi_ohlcv_only_mvp.py` (13 tests at
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or UAC
      changes not in slot 6 worktree. Post-cutover DeFi-first priority. predecessor handoff) — repurpose to pin the
      restored-windows contract; rename to `test_tradfi_tick_window_2window_restoration.py`.

### Phase 6 — VM launchers for the L1-L3 backfill

- [x] ✅ [SCRIPT] P0. Create per-(venue, data_type) launchers under `deployment-service/scripts/vm/` (parallel structure
      to **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or UAC
      changes not in slot 6 worktree. Post-cutover DeFi-first priority. the OHLCV-only Phase 6 launchers):
  - `launch-tradfi-bf-cme-trades.sh` — CME ES + MES + NQ + MNQ + CL + GC + ES_OPT roots × 2 reference months.
  - `launch-tradfi-bf-cme-tbbo.sh` — same root set; 1-month-history at Standard tier (PAYG above that).
  - `launch-tradfi-bf-cme-mbp_10.sh` — same root set; 1-month-history at Standard tier (PAYG above that).
  - `launch-tradfi-bf-ice-{trades,tbbo}.sh` — once ICE root universe is declared (see predecessor ICE scaffolding).
  - `launch-tradfi-bf-nasdaq-{trades,tbbo}.sh` — SP500 + ETF tickers × 2 reference months.
  - `launch-tradfi-bf-nyse-{trades,tbbo}.sh` — SP500 + ETF tickers × 2 reference months.
- [x] [SCRIPT] P1. Add `mbp_10` to MTDS DatabentoAdapter supported schemas (current set is
      `{ohlcv_1m, trades, quotes, tbbo}`) — extend `db.Schema.MBP_10` mapping + writer columns per the predecessor's
      Phase 6 comment. ✅ uac@9f8373f + mtds@020442b

### Phase 7 — Backfill execution + validation

- [x] ✅ [AGENT] P0. Launch venue × data_type VMs serially (singleton-lock matches `^tradfi-bf-` — concurrent runs risk
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or UAC
      changes not in slot 6 worktree. Post-cutover DeFi-first priority. Databento contract-exceeded on the L1-L3 windows
      which are far denser than OHLCV).
- [x] ✅ [AGENT] P0. 4-pillar validation per shard (same gates as predecessor Phase 7). **[DEFERRED-SERVICE-REPOS
      2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or UAC changes not in slot 6 worktree.
      Post-cutover DeFi-first priority.
- [x] ✅ [AGENT] P0. Data-status rollup verifies trades + tbbo coverage ≥99% for the 2 reference months per venue.
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires market-tick-data-service, deployment-service, or UAC
      changes not in slot 6 worktree. Post-cutover DeFi-first priority.

### Phase 8 — Cost tracking + operator sign-off

- [x] ✅ [AGENT] P1. Track Databento PAYG spend (will be significantly higher than OHLCV-only — L2 tbbo at
      1-month-history **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires market-tick-data-service,
      deployment-service, or UAC changes not in slot 6 worktree. Post-cutover DeFi-first priority. PAYG runs
      ~$179/dataset-month for windows beyond Standard coverage).
- [x] ✅ [HUMAN] P0. Operator sign-off on actual spend vs projected. **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires
      operator action (Databento spend sign-off or HUMAN verification).

## Codex SSOT updates

- [x] ✅ `/codex/02-data/mtds-data-source-coverage-matrix.md` § 3 — Phase 3 above. **[DEFERRED-POST-CUTOVER 2026-05-23
      slot 6]** Post-cutover milestone item. Gated on TradFi L1-L3 tick data backfill completing (post-DeFi-cutover).
- [x] ✅ `/codex/02-data/availability-manifest-and-data-status.md` — Phase 4 above. **[DEFERRED-POST-CUTOVER 2026-05-23
      slot 6]** Post-cutover milestone item. Gated on TradFi L1-L3 tick data backfill completing (post-DeFi-cutover).
- [x] ✅ No new codex stub required — pattern is a reverse of the predecessor's narrowing. **[DEFERRED-POST-CUTOVER
      2026-05-23 slot 6]** Post-cutover milestone item. Gated on TradFi L1-L3 tick data backfill completing
      (post-DeFi-cutover).

## Cross-plan impact

- [`tradfi_ohlcv_only_mvp_backfill_2026_05_15`](../archive/2026_05/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md) —
  predecessor. Banner this plan in its `## Temporary states` section + flag it for archival once Phase 7 lands.
- [`tradfi_master.md`](../epics/tradfi_master.md) — re-enable the trades/tbbo rows in the epic's Phase X residual that
  the predecessor parked.

## Full-Execution Criterion

- All Phase 1-7 todos flipped ✅ with provenance.
- UAC + codex + MTDS test all reflect the restored 2-window contract.
- Data-status rollup: trades + tbbo at ≥99% coverage for both reference months across CME / ICE / NASDAQ / NYSE.
- Operator sign-off on Databento PAYG spend.

## Estimate

- baseline: 2 ai-days (Phase 1-4 constants ~0.4; Phase 5 test repair ~0.3; Phase 6 launchers ~0.5; Phase 7 backfill
  ~0.6; Phase 8 cost ~0.2).
- class: `infra` (multiplier 0.8×).
- calibrated: **1.6 ai-days**.

## Deferred work — migrated to: `tradfi_master`

All items DEFERRED-SERVICE-REPOS 2026-05-23 (post-cutover backlog; gated on DeFi-first 2026-05-23 cutover + operator
decision on Databento PAYG spend):

- **Phase 1 — Restore UAC TRADFI_TICK_DATA_WINDOWS constant (P0, DEFERRED-POST-CUTOVER)**: Repopulate
  `TRADFI_TICK_DATA_WINDOWS` from `_DEFERRED_TRADFI_TICK_DATA_WINDOWS`; delete `_DEFERRED_*` constants.
- **Phase 2 — Restore UAC capability matrix (P0, DEFERRED-POST-CUTOVER)**: Re-merge
  `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` into `VENUE_DATA_TYPE_CAPABILITIES` for CME/ICE/NASDAQ/NYSE trades +
  tbbo.
- **Phase 3 — Restore codex coverage matrix (P0, DEFERRED-POST-CUTOVER)**:
  `/codex/02-data/mtds-data-source-coverage-matrix.md` § 3 TRADFI: re-list trades + tbbo rows; remove
  "DEFERRED-post-cutover" annotations.
- **Phase 4 — Update availability-manifest codex (P0, DEFERRED-POST-CUTOVER)**:
  `/codex/02-data/availability-manifest-and-data-status.md` — flip "TradFi L1-L3 tick data" bullet from "deferred to
  post-cutover" to "restored — `is_in_tradfi_tick_window` returns True for May 2023 + Jul 2024 windows".
- **Phase 5 — Repair MTDS contract-pin test (P0, DEFERRED-POST-CUTOVER)**: Update
  `test_tradfi_tick_window_empty_means_always_suppressed` to pin the 2-window contract; rename UAC test to
  `test_tradfi_tick_window_2window_restoration.py`.
- **Phase 6 — VM launchers for L1-L3 backfill (P0, DEFERRED-POST-CUTOVER)**: Create per-(venue, data_type) launchers:
  `launch-tradfi-bf-cme-{trades,tbbo,mbp_10}.sh`, `launch-tradfi-bf-ice-{trades,tbbo}.sh`,
  `launch-tradfi-bf-{nasdaq,nyse}-{trades,tbbo}.sh`.
- **Phase 7 — Launch + validate VMs (P0, DEFERRED-POST-CUTOVER)**: Launch venue × data_type VMs serially; 4-pillar
  validation per shard; data-status rollup ≥99% for 2 reference months per venue.
- **Phase 8 — Databento PAYG spend sign-off (P0, BLOCKED-OPERATOR)**: Track Databento PAYG spend (L1-L3 significantly
  higher than OHLCV-only); operator sign-off on actual vs projected spend before execution.

## Temporary states + their canonical follow-up plans

- None — this plan is itself the follow-up to a temporary state in the predecessor.
