---
title:
  "P0/P1 substantial work surfaced by 2026-05-08 9-agent audit (Aster connector / 2yr backtest / MDPS streaming / 18
  MTDS VMs)"
created: 2026-05-08
author: 9-agent-audit-2026-05-08
status: open
source:
  - 9-agent parallel cluster audit 2026-05-08 (clusters 3, 7, 8)
  - master_to_live_defi_2026_05_23.md Group F items 17-22
  - defi_master_2026_05_07.md leveraged_funding_arb hedge venues
  - mdps_streaming_and_backpressure_2026_05_07.md Phase 1.1 + Phase 2
locked_by: live-defi-rollout
locked_since: 2026-05-08
execution:
  owner: operator triage → distribute to Ikenna/Harsh tabs
  cadence: one-shot per item; review at next daily-split sweep
  verifier: per-item exit criteria below
  last_executed: "NEVER"
---

# 4 P0/P1 items surfaced by 9-agent audit needing operator triage

> **Severity**: P0 for items #1-3 (May-23 critical-path); P1 for #4 (operational hygiene). **Blast radius**:
> leveraged_funding_arb live-trading + paper-trade smoke + live-pipeline Phase 4. **Suggested owner**: operator triage;
> cannot auto-assign.

This doc collects the 4 substantial-work findings the 9-agent audit surfaced that are too big to silently fix and need
explicit operator decisions on owner + scope. The audit's mechanical false-negative fixes shipped in batches 1+2+3
(PM@a370911b + PM@daf844e8 + PM@c6ced960) and the paper-trade smoke harness was repaired in-session
(e2e-testing@dfb7abe6). The 4 items below are NOT yet shipped + need operator decision.

---

## Item 1 — Aster execution connector — ✅ RESOLVED 2026-05-09 (execution-service@25a1d561)

> **Status update 2026-05-09**: Connector shipped at `execution-service@25a1d561`. File:
> `execution-service/execution_service/defi_execution/protocols/aster.py` (550+ lines, full Binance Futures-compat REST
> + HMAC-SHA256 signing + paper-trade + 4 UAC schema parsing helpers). Tests:
> `execution-service/tests/defi_execution/unit/test_aster_connector.py` (30 tests, all green). Registered in
> `defi_execution/protocols/__init__.py` + `defi_execution/__init__.py`. UAC schemas already existed
> (`unified_api_contracts.external.aster.schemas`); UAC capability registry already declared `"aster"` PERPS protocol.
> Open follow-ups (NOT blockers, will land in defi_master Fork 2): live REST POST transport (this connector returns the
> prepared signed shape; httpx POST owned by execution-service runtime layer per Hyperliquid pattern) + Tenderly fork
> integration test for end-to-end signed-flow validation. Master Group F Item 20 CeFi-testnet column can flip to ◐ once
> the runtime POST + integration test land.

### What

`leveraged_funding_arb` archetype requires 6 perp venues per CLAUDE.md "Master Plan — Live DeFi Trading":

> Hedge legs across 6 perp venues (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster)

Verified state of execution-service connectors:

- ✅ Bybit, Deribit, Binance, OKX —
  `execution-service/execution_service/trade_execution/adapters/{bybit_ccxt,deribit_ccxt,binance_ccxt,okx_ccxt}.py` all
  exist
- ✅ Hyperliquid — `execution-service/execution_service/defi_execution/protocols/hyperliquid.py` exists
- ❌ **Aster — NO connector anywhere in execution-service** (grep `class AsterConnector` returns 0 hits)

### Why it matters

Without an Aster connector, the 6-venue hedge universe is 5-venue and `leveraged_funding_arb` cannot ship live. Master
Group F Item 20 (live testnet replicates prod) is logged as "CeFi side has not been validated end-to-end" — this is more
severe: the connector is not just unvalidated, it doesn't exist.

### Recommended decision

(a) **Author Aster connector** in execution-service — needs Aster API spec + auth + sandbox, ~1-2 days work. Add to
defi_master Fork 2 (leveraged_funding_arb branch).

(b) **Drop Aster from the 6-venue universe + reduce to 5 venues** — operator decision; CLAUDE.md master-plan promise
needs to update.

Recommended: (a) — operator-driven scope decision. Open item on defi_master_2026_05_07.md DEX-perp adapters section.

### Exit criteria

- `class AsterConnector` exists in execution-service with `connect()` + `place_order()` + position-query
- Tenderly fork or Aster sandbox integration test green
- Master Group F Item 20 column (CeFi testnet) flips to ◐

---

## Item 2 — 2-year config-grid backtest runner — **SHIPPED 2026-05-09 (strategy-service@`3dea3c7`); RESOLVED-PENDING-OPERATOR-RUN**

> **Status update 2026-05-09**: script + 22 unit tests shipped; smoke verified on both archetypes; basedpyright + ruff
> clean. The full 2-yr grid run (~8-12h) is operator-scheduled — launch command documented in the script docstring.
> Master Group F Item 18 line item flipped to `[x]` with the same evidence. The remaining work is purely operational:
> launch the full grid on a same-region GCE VM and read the resulting per-archetype `summary.parquet` to inform live
> config selection.

## Item 2 — Original triage (2026-05-08, kept for archaeology) — 2-year config-grid backtest runner does NOT exist (P0, master Group F Item 18)

### What

Master plan Item 18: "2-year batch backtest run — completed across config grid; P&L variance per archetype configuration
captured so the live-trading config is informed, not guessed."

Verified state: `strategy-service/scripts/` has `trace_carry_staked_basis.py` + `trace_all_carry_archetypes.py`
(tracing/simulation, NOT config-grid sweep). No `run_2yr_config_grid_backtest.py`.

### Why it matters

Live-trading config (gas thresholds, slippage caps, position sizing per archetype) needs P&L variance distribution from
a config-grid sweep over 2 years of data — not single-config tracing. Without the runner the live-config is
judgment-based instead of evidence-based.

### Recommended decision

Author `strategy-service/scripts/run_2yr_config_grid_backtest.py` — sweeps parameter space (e.g. position-size grid ×
max-drawdown grid × slippage-cap grid) for `carry_staked_basis` + `leveraged_funding_arb`; emits P&L variance + Sharpe +
max-drawdown distribution per archetype config dimension; writes to
`gs://strategy-results-{pid}/backtests/config_grid_2yr/<archetype>/<run_id>/`. ~2-3 days work + 8-12h grid runtime.

Owner: strategy-service maintainer + Ikenna (config-grid design ownership). Add to
strategy_and_dart_master_2026_05_07.md.

### Exit criteria

- Script runs end-to-end against 2yr historical data
- Per-archetype config-grid P&L distribution emitted to GCS
- Live-trading config selection cites the grid evidence
- Master Group F Item 18 closure criterion met

---

## Item 3 — MDPS streaming primitives unshipped (P0, blocks live_pipeline Phase 4) — PARTIAL 2026-05-09

### What

`live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 4 is gated on UTL primitives + MDPS wiring per
`mdps_streaming_and_backpressure_2026_05_07.md` Phase 1.1 + Phase 2.

Verified state (cluster 8 audit grep, 2026-05-08):

- ❌ `open_candle_writer` — 0 hits in unified-trading-library
- ❌ `close_candle_writer` — 0 hits
- ❌ `ResourceProfiler.on_memory_warning` wiring — 0 hits in MDPS source
- ❌ `LiveConnectivityWatchdog` / `CONNECTIVITY_GAP_DETECTED` — 0 hits in MTDS or UAC

These are explicitly named as STRICT BLOCKER for live-pipeline Phase 4 in the live_pipeline plan banner.

### Update 2026-05-09 — UAC SSOT shipped, code wiring still open

Per [`mdps_streaming_primitives_prompt_vs_plan_conflict_2026_05_09.md`](mdps_streaming_primitives_prompt_vs_plan_conflict_2026_05_09.md)
operator-approved option (a) — ship per plan-of-record.

**Shipped this session (2026-05-09):**

- ✅ `LifecycleEventType.CONNECTIVITY_GAP_DETECTED` / `CONNECTIVITY_RECOVERED` / `CONNECTIVITY_GAP_BACKFILLED` —
  UAC@`4bd84e7c` (`unified_api_contracts/internal/events.py`) — 3 typed event-type members + 3 Pydantic detail models
  (`ConnectivityGapDetectedDetails` / `ConnectivityRecoveredDetails` / `ConnectivityGapBackfilledDetails`) + 3 typed
  event wrappers + 12 unit tests in `tests/internal/unit/test_connectivity_gap_event_taxonomy.py`. The `classification`
  field on `ConnectivityGapDetectedDetails` is a closed-set Literal (`WS_DISCONNECT` / `STALE_HEARTBEAT` /
  `API_TIMEOUT` / `UNKNOWN`) so adapters can't accidentally emit untyped strings. This is the alerting-service /
  reconciler / auto-backfill SSOT — downstream consumers can now type their event-stream subscriptions against
  these wrappers without inventing local types.

**Still open (DEFERRED-PER-SUB-AGENT-CAPACITY this session — see conflict-issue § "Recommended decision (a)"):**

- ❌ `open_candle_writer` / `close_candle_writer` UTL parquet-write-lifecycle wrappers in
  `unified-trading-library/unified_trading_library/streaming/candle_writer.py` — Phase 1.1 of plan-of-record.
- ❌ MDPS `_streaming_write_per_tf` callsite migration — Phase 1.2 of plan-of-record. Lives in
  `market-data-processing-service/market_data_processing_service/app/core/live_workers.py:1118-1164` (per plan-of-
  record line 87). Substantial refactor of the per-timeframe accumulator pattern; tests `(N batches × M rows) →
  exactly ONE record_captured per (timeframe, shard)` shape.
- ❌ MTDS `LiveConnectivityWatchdog` — Phase 1's "Migrated issue 2026-05-08" item. Module location per conflict-issue
  proposal: `market-tick-data-service/market_tick_data_service/market_interface/connectivity_watchdog.py`.
  Heartbeat tracker per (venue, data_type), state machine
  (`HEALTHY → STALE → GAP → RECOVERING → HEALTHY`), emits the 3-event family this session shipped.
- ❌ `ResourceProfiler.on_memory_warning` wiring — Phase 2 of plan-of-record. Depends on Phase 1.2 callsite migration
  per the plan's execution DAG; cannot ship in isolation.
- ❌ Per-venue `VENUE_HEARTBEAT_INTERVAL` empirical baseline — separate `[SCRIPT] P1` todo in plan-of-record (7-day
  observation per venue → 99th percentile). Bootstrap with conservative default (e.g. 60s) is fine until calibration.

**Why this session shipped only the SSOT half:** Each of the 5 deliverables is a separate full-QG cycle in a
different repo (UTL / UAC / MTDS / MDPS×2). The MDPS Phase 1.2 callsite migration alone is a substantial refactor of
a 1100+ line file that needs schema-drift detection across chunks + shard-level failure isolation + 4-test matrix
verification — not safe in a parallel-agent slot with foreign WIP in the shared working tree (UTL had 9 foreign-
modified files from a parallel agent's session at start). The UAC SSOT extension is the cleanest, smallest, and
most-independent of the 5 — it has zero downstream wire-in dependency for landing the SSOT, alerting-service +
reconciler can now subscribe by type, and the next agent picking up the remaining items has a typed event surface to
implement against rather than inventing one.

### Why it matters

Live-pipeline Phase 4 (MDPS live mode) cannot start without the open/close candle writer primitives + backpressure
wiring. The mdps_streaming plan declares this dependency explicitly. Live-pipeline is Group F item 21+22 prereq for the
May-23 cutover.

### Recommended decision

Tab 2 (live-pipeline) was 10-commit-shipped 2026-05-08 evening but ONLY for UTL primitives that DON'T cover the
MDPS-specific streaming layer (StreamingHealthSnapshot / batch_live_reconciler / honest_coverage_ratchet are utility
classes, not the open/close candle writer). The mdps_streaming plan Phase 1.1 needs explicit owner.

Owner candidates: (a) Tab 2 next session if live-pipeline plan body extends scope; (b) MDPS-dedicated tab in next
work-split; (c) Harsh implement-from-spec if Ikenna pre-designs.

### Exit criteria

- `open_candle_writer` + `close_candle_writer` exist in `unified-trading-library/unified_trading_library/streaming/` —
  ❌ STILL OPEN
- MDPS `app/core/live_workers.py` consumes them — ❌ STILL OPEN (Phase 1.2 callsite migration)
- `ResourceProfiler.on_memory_warning` wired in MDPS — ❌ STILL OPEN (Phase 2; depends on Phase 1.2)
- `CONNECTIVITY_GAP_DETECTED` event type in UAC — ✅ SHIPPED 2026-05-09 UAC@`4bd84e7c`
- `LiveConnectivityWatchdog` in MTDS — ❌ STILL OPEN
- live-pipeline Phase 4 unblocks — ❌ STILL BLOCKED until UTL primitives + MDPS wiring land

---

## Item 4 — 18 MTDS bounce-sweep VMs never launched (P1, parallelization fix verification)

### What

Per session memory entry 2026-05-07: "MTDS parallelization fix shipped 2026-05-07 — 18 VMs awaiting bounce-sweep.
UTL@50ad40ef ParallelPerSymbolRunner + 12 tests; MTDS@28db65a Tardis swap...".

Verified state (cluster 8 probe 2026-05-08):

- 0 MTDS bounce-sweep VMs running per `gcloud compute instances list --filter="name~mtds-"`
- Currently only 2 MTDS VMs running (`mtds-gas-fees`, `mtds-lending-indices`) — these are forward-poll/backfill, NOT the
  bounce-sweep validation set
- The "wiring agent dispatched at session end" for RSS-pause integration is unverifiable — no evidence it landed

### Why it matters

The parallelization fix is shipped to source but the validation that it actually works at scale (18 VMs concurrently
with shard-isolation) was never run. Per "Plans Run To Actual Completion" HARD RULE, code-shipped without
operationally-shipped is silent rot.

### Recommended decision

(a) **Run the bounce-sweep**: launch 18 MTDS backfill VMs with the new `ParallelPerSymbolRunner` + per-VM-shard
isolation; verify event stream + manifest growth + RSS-pause integration via memory-warning trigger. Operator-runnable;
no cross-side dependency.

(b) **Document as deferred-post-cutover** if the bounce-sweep isn't on May-23 critical path — the existing 9 cefi
heavy-backfill VMs are running fine; bounce-sweep is parity validation for a future scaling event.

Recommended: (b) for this cycle (focus on May-23); track as P1 in `mtds_databento_path_streaming_2026_05_07.md` Phase 4
(real-VM validation gap is already noted there).

### Exit criteria

- 18-VM bounce-sweep run + monitored with full event-stream + manifest verification, OR
- Issue formally deferred to post-May-23 cycle with named successor plan

---

## Cross-item summary

| #   | Item                            | P   | Blocks May-23?              | Recommended owner                                 |
| --- | ------------------------------- | --- | --------------------------- | ------------------------------------------------- |
| 1   | Aster connector                 | P0  | YES (leveraged_funding_arb) | defi_master Fork 2 + execution-service maintainer |
| 2   | 2yr config-grid backtest runner | P0  | YES (Group F Item 18)       | strategy_and_dart_master + Ikenna                 |
| 3   | MDPS streaming primitives       | P0  | YES (live_pipeline Phase 4) | live_pipeline next session OR MDPS-dedicated tab  |
| 4   | 18 MTDS bounce-sweep VMs        | P1  | NO                          | mtds_databento Phase 4 (defer-post-cutover OK)    |

## Cross-references

- 9-agent audit chat session 2026-05-08 (cluster 3 + 7 + 8 reports)
- master_to_live_defi_2026_05_23.md Group F items 17-22
- defi_master_2026_05_07.md leveraged_funding_arb section
- mdps_streaming_and_backpressure_2026_05_07.md Phase 1.1 + 2
- live_pipeline_mtds_mdps_features_2026_05_08.md Phase 4
- mtds_databento_path_streaming_2026_05_07.md Phase 4
- runbook_execution_governance_gaps_2026_05_08.md (related: peripheral QG wiring rule)
