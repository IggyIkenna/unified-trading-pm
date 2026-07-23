---
doc_type: plan
title: TradFi MVP — OHLCV-only Databento Backfill
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-17"
---

> **ARCHIVED 2026-05-21** — 100% complete. 70 VMs drained 2026-05-17; 216,876 captured + 7,365 empty_confirmed + 0
> attempted_failed; 96.72% capture rate. ICE roots deferred to `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`.

---

title: "TradFi MVP — OHLCV-only Databento backfill (drop L1-L3 to post-cutover)" parent_epic: tradfi_master priority: P1
status: active estimate_class: infra estimate_baseline_ai_days: 4.0 estimate_calibrated_ai_days: 3.2 locked_by:
live-defi-rollout locked_since: 2026-05-15 related_plans:

- trading_agent_service_architecture_unlock_2026_05_22.md
- master_to_live_defi_2026_05_23.md
- tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md
- cme_polymarket_arb_2026_05_08.md

---

# TradFi MVP — OHLCV-only Databento Backfill

Operator-directed 2026-05-15: collapse TradFi MVP data acquisition to OHLCV-1m only; defer trades/tbbo/mbp_10 (L1-L3) to
post-cutover. Backfill OHLCV to full Databento-available period floored at 2019-01-01. CME / ICE / NASDAQ / NYSE x
ohlcv_1m + CBOE VIX 15m (existing). 70 VMs drained 2026-05-17; 216,876 captured + 7,365 empty_confirmed + 0
attempted_failed; 100% honest-fill, 96.72% capture rate.

Codex SSOTs: `/codex/02-data/mtds-data-source-coverage-matrix.md` ·
`/codex/02-data/availability-manifest-and-data-status.md`

---

## Phase 1 — UAC constant changes

- [x] ✅ **[SCRIPT] P0. `TRADFI_TICK_DATA_WINDOWS = []` + `_DEFERRED_*` constants preserved.**
      `is_in_tradfi_tick_window()` returns False for every date. 2 prior windows preserved in
      `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS`. (unified-api-contracts@`886ad9c`)

## Phase 2 — UAC capability matrix

- [x] ✅ **[SCRIPT] P0. `VENUE_DATA_TYPE_CAPABILITIES` drop trades+tbbo from TradFi venues + backdate CME/ICE.**
      CME/ICE: ohlcv_1m at 2019-01-01. NASDAQ/NYSE: ohlcv_1m at 2023-04-15. (unified-api-contracts@`886ad9c`)

## Phase 3 — Codex coverage matrix update

- [x] ✅ **[SCRIPT] P0. Codex coverage matrix § 3 TRADFI updated.** OHLCV-only callout + `_DEFERRED_*` references +
      post-cutover successor pointer. (PM@`e944dae2`)

## Phase 4 — MTDS orchestrator contract-pin

- [x] ✅ **[AGENT] P0. 13 unit tests pin the empty-windows contract.** `TRADFI_TICK_DATA_WINDOWS == []`;
      `is_in_tradfi_tick_window()` False for 6 date probes; `_DEFERRED_*` constants preserved;
      `VENUE_DATA_TYPE_CAPABILITIES` regression guard. (unified-api-contracts@`8aa36c1`)

## Phase 5 — Phantom-row reconciliation

- [x] ✅ **[SCRIPT] P0. TradFi trades+tbbo manifest reconciled.** New enum value
      `EmptyConfirmedReason.EXPECTED_OUT_OF_COVERAGE_WINDOW` added; 39,048 rows flipped to `empty_confirmed`.
      (unified-api-contracts@`585de75`)
- [x] ✅ **[AGENT] P0. deployment-api `_EMPTY_REASON_KEYS` synced + SIM108 fixes + tradfi tick test skips.** 4 tests
      marked `pytest.mark.skip` with reason — restore in `tradfi_l1_l2_l3_tick_data_post_cutover`.
      (deployment-api@`6ce3732`)

## Phase 6 — Backfill VM launchers

- [x] ✅ **[SCRIPT] P0. Per-venue OHLCV-1m backfill launchers shipped.** `launch-tradfi-bf-cme-ohlcv-1m.sh`,
      `launch-tradfi-bf-ice-ohlcv-1m.sh` (scaffold; ICE roots pending operator decision),
      `launch-tradfi-bf-nasdaq-ohlcv-1m.sh`, `launch-tradfi-bf-nyse-ohlcv-1m.sh`, `_tradfi-ohlcv-launcher-lib.sh`.
      (deployment-service@`f8cd7de`)

## Phase 7 — Backfill execution + 4-pillar validation

- [x] ✅ **[AGENT] P0. 63 tradfi-bf VMs launched; all drained 2026-05-17 ~14:00 UTC.** CME 48 VMs (6 futures roots x 8
      years + 8 ES_OPT VMs), NASDAQ 4 VMs, NYSE 4 VMs. ICE 0 (pending operator root pick). Final: 216,876 captured +
      7,365 empty_confirmed + 0 attempted_failed. Honest-fill 100%.
- [x] ✅ **[AGENT] P0. 4-pillar validation harness shipped.** `scripts/validate_tradfi_ohlcv_4pillar.py`; 18/18 sampled
      parquets pass all pillars. (market-tick-data-service@`d1ab9bc`, @`f1621c0`)
- [x] ✅ **[AGENT] P0. Data-status rollup confirms >= 99% honest-fill across CME/NASDAQ/NYSE.** All-time totals: CME
      82,798 captured, NASDAQ 33,672, NYSE 122,494.

## Phase 8 — Cost tracking + operator sign-off

- [x] ✅ **[AGENT] P1. `DATABENTO_PAYG_SPEND` emission shipped.** `_run_batch_download` emits per batch; cost_usd from
      `client.metadata.get_cost()`. (market-tick-data-service@`1b0a207`)
- [x] ✅ **[HUMAN] P0. Operator sign-off.** Drain complete 2026-05-17; spend verification via Databento billing portal
      (slot-8 2026-05-20).

## Phase 9 — Successor plan stub

- [x] ✅ **[SCRIPT] P1. Successor plan stub filed.** `plans/active/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`

## Pending operator decisions

- [x] ✅ **[OPERATOR-DECISION] ICE roots pick.** **DEFERRED -> operator pick at next drain window.** `ICE_ROOTS=()` in
      launcher; proposed: `("BRN" "G")` for IFEU + `("CT" "CC" "KC" "SB" "OJ" "DX")` for IFUS. Ping in slot_7.md
      2026-05-19.

## Temporary states + canonical follow-up plans

- `TRADFI_TICK_DATA_WINDOWS = []` (empty) -> restored in `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`.
- `_DEFERRED_VENUE_DATA_TYPE_COVERAGE_WINDOWS` -> same successor plan restores into `VENUE_DATA_TYPE_COVERAGE_WINDOWS`.
- ICE roots: pending operator decision; launcher scaffolding ready.
