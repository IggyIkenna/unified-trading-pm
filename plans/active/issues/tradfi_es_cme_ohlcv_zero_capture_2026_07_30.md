---
doc_type: issue
title: >-
  tradfi CME ES futures ohlcv_1m/1s manifest-verify reveals ZERO real rows ever captured (2020-2026) — the "fleet
  FINISHED" framing was VM-completion, not data-capture, proof
summary: >-
  Executed the 2026-07-29 operator-ruled manifest-count check for CME ES futures ohlcv_1m/1s
  (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s P0 todo). Result is NOT the expected "backfill proven"
  outcome: a direct read of the live `market-data-tick-tradfi-prd` `_index` (5,894,011 rows) shows every one of the
  4,855 `venue=CME, instrument_id=ES.FUT, data_type in {ohlcv_1m, ohlcv_1s}` manifest rows across the full 2020-2026
  history is either `attempted_failed` (3,048, `error_reason=WithinBoundsTradfiSourceZero`) or `empty_confirmed` (1,807,
  `error_reason=SOURCE_RETURNED_ZERO`) — **0 rows have `row_count>0`, and 0 rows are `captured`.** The 7-VM
  `tradfi-bf-cme-ohlcv-1m-es-*` fleet (ran 2026-07-21T03:42-09:48, confirmed zero preemptions) genuinely executed and
  wrote manifest rows for every requested date, but the Databento fetch itself returned zero bars on every single
  attempt for this headline MVP instrument (S&P 500 E-mini futures) — not a partial gap, a total one. This contradicts
  the parent plan's "fleet FINISHED" framing, which was VM-lifecycle proof (STARTED/RUNNING/self-deleted cleanly), not
  data-capture proof — exactly the distinction `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` warns about
  (count target artifacts, not activity/VM-completion).
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service]
scope: [engineer]
tags: [tradfi, databento, ohlcv, cme, manifest, data-correctness, backfill, zero-capture]
related:
  [
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-07-30
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  [
    "manifest-count-check execution 2026-07-30, per the 2026-07-29 operator ruling recorded in
    instruments_tradfi_g1_g5_gate_execution_2026_07_24.md (the P0 'Run the manifest-count check for ES CME ohlcv_1s/1m'
    todo)",
  ]
---

# tradfi CME ES futures ohlcv — manifest-verify shows total capture failure, not a proven backfill

## What I found

Ran the exact query the ruling's todo specified — a single live read of `market-data-tick-tradfi-prd`'s
`_index/availability_index.parquet` (5,894,011 rows, no bucket walk), scoped to `venue=CME` × `instrument_id=ES.FUT`
(the manifest's row-key atom for the ES parent-symbol chain; confirmed this is the correct key —
`data_types=ohlcv_1m;ohlcv_1s` is the launcher's own default per
`deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh:85`) × `data_type ∈ {ohlcv_1m, ohlcv_1s}`, all years
2020-2026.

**Result: 4,855 total scoped rows, `capture_status` distribution:**

| data_type | year | attempted_failed | empty_confirmed |
| --------- | ---- | ---------------- | --------------- |
| ohlcv_1m  | 2020 | 241              | 265             |
| ohlcv_1m  | 2021 | 243              | 85              |
| ohlcv_1m  | 2022 | 133              | 48              |
| ohlcv_1m  | 2023 | 240              | 23              |
| ohlcv_1m  | 2024 | 233              | 159             |
| ohlcv_1m  | 2025 | 241              | 261             |
| ohlcv_1m  | 2026 | 125              | 71              |
| ohlcv_1s  | 2020 | 245              | 261             |
| ohlcv_1s  | 2021 | 251              | 77              |
| ohlcv_1s  | 2022 | 241              | 48              |
| ohlcv_1s  | 2023 | 240              | 23              |
| ohlcv_1s  | 2024 | 246              | 157             |
| ohlcv_1s  | 2025 | 244              | 258             |
| ohlcv_1s  | 2026 | 125              | 71              |

**Zero `captured` rows anywhere.** Confirmed directly: `(row_count > 0).sum() == 0` across all 4,855 rows, any
`written_at`. `error_reason` is one of exactly two values: `WithinBoundsTradfiSourceZero` (3,048 rows, `written_at`
mostly 2026-07-07, pre-dating the fleet) or `SOURCE_RETURNED_ZERO` (1,807 rows). Isolating just the rows the 2026-07-21
fleet itself wrote (`written_at` date == `2026-07-21`, 718 rows spanning `date` 2021-01-04 through 2026-04-15): **100%
are `empty_confirmed` / `SOURCE_RETURNED_ZERO`** — the fleet ran cleanly (per the plan's own VM-lifecycle measurement: 7
shards inserted 03:42-03:44Z, all self-deleted by 09:48Z, zero `compute.instances.preempted` events) but every single
date it attempted returned zero bars from Databento for `ES.FUT` ohlcv_1m/1s.

This is suspicious on its face: ES (S&P 500 E-mini futures) is one of the most liquid futures contracts in the world — a
genuine "Databento has no 1-minute/1-second bars for ES on this date" outcome should be rare-to-never across a 6-year,
~2,600-trading-day window, not 100% of attempts. The uniform, total failure pattern (not a partial/spotty gap) points at
a systemic issue in how the fetch is shaped for this instrument/schema combination — e.g. the `ES.FUT` parent-symbol
(Databento "parent symbology," `stype_in`) request against the `ohlcv-1m`/ `ohlcv-1s` schemas may need a different
`stype_in` (continuous `c.0` or per-contract raw symbols) than what `trades`/`definition` pulls use, or a
date-window/dataset mismatch — **not diagnosed further here**; this issue is the manifest-verify finding, not the
root-cause fix.

## Why it matters

- ES is a named MVP headline instrument ("S&P index futures") gating the tradfi Layer-1 certification effort
  (`tradfi_consolidated_closeout_2026_07_18.md`'s "Certify tradfi Layer-1" todo) and the parent gate-execution plan's
  Phase-2 tradfi rebuild.
- The parent plan's todo (line 104-116) had already marked itself `[x]` based on VM-lifecycle evidence only ("fleet
  FINISHED... zero preemptions") — this is exactly the activity-vs-target-artifact trap the workspace's own
  async-wait-discipline codex SSOT names. The manifest-count check this issue reports on was specifically ordered to
  close that gap, and it found a real problem instead of confirming success.
- If the same `ES.FUT`-parent-symbology shape is used for other CME roots' `ohlcv_1m`/`ohlcv_1s` (not verified here —
  out of scope for this issue), this could be a fleet-wide tradfi capture defect, not an ES-specific one.

## Recommended next steps (not executed here — root-cause diagnosis, not a mechanical todo)

1. Read `market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py`'s actual
   `stype_in`/schema/dataset parameters for an `ohlcv_1m`/`ohlcv_1s` request against a CME parent symbol like `ES.FUT`,
   and compare against Databento's documented symbology requirements for the `ohlcv-1m`/`ohlcv-1s` schemas (parent
   symbology may not be valid there the way it is for `trades`/`definition`).
2. Run one small, targeted live probe (a single date, single root, `--dry-run`-equivalent or a direct Databento API call
   outside the full pipeline) to see the raw API response/error before re-launching any VM-scale backfill — cheap, fast,
   avoids repeating the same zero-yield fleet run.
3. Once root-caused, decide whether this needs an adapter code fix (likely `[CODE]`) + a targeted re-run (not a blind
   re-run of the same shape that already produced 0 rows twice).
4. Check whether other CME roots (CL, GC, HG, NG, NQ, SI — named as "in flight" in this same plan) show the same
   0%-captured pattern for ohlcv_1m/1s, to know if this is ES-specific or systemic.

## Todos

- [ ] [DIAG] P1. Diagnose why the `ES.FUT` parent-symbol Databento request for `ohlcv_1m`/`ohlcv_1s` returns zero rows
      on 100% of attempts (2020-2026) — read the adapter's request-shaping code, compare against Databento's
      schema/symbology docs, and run one small targeted live probe before any re-launch. Repo: market-tick-data-service.
- [ ] [DATA] P2. Once root-caused and fixed, re-verify whether the same zero-capture pattern affects the other "in
      flight" CME roots (CL/GC/HG/NG/NQ/SI) via the same manifest-count method (no bucket walk). Repo:
      instruments-service.
