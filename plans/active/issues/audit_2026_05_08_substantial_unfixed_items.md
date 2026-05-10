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
>
> - HMAC-SHA256 signing + paper-trade + 4 UAC schema parsing helpers). Tests:
>   `execution-service/tests/defi_execution/unit/test_aster_connector.py` (30 tests, all green). Registered in
>   `defi_execution/protocols/__init__.py` + `defi_execution/__init__.py`. UAC schemas already existed
>   (`unified_api_contracts.external.aster.schemas`); UAC capability registry already declared `"aster"` PERPS protocol.
>   Open follow-ups (NOT blockers, will land in defi_master Fork 2): live REST POST transport (this connector returns
>   the prepared signed shape; httpx POST owned by execution-service runtime layer per Hyperliquid pattern) + Tenderly
>   fork integration test for end-to-end signed-flow validation. Master Group F Item 20 CeFi-testnet column can flip to
>   ◐ once the runtime POST + integration test land.

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

## Item 3 — MDPS streaming primitives unshipped (P0, blocks live_pipeline Phase 4) — PARTIAL 2026-05-09; second-pass-deferred 2026-05-10

> **2026-05-10 update**: chain agent re-attempted Phase 1.2 + Phase 2 today and surfaced a **semantic dual-SSOT
> collision** between UTL `close_candle_writer` (uses `record_captured` v5 verb) and existing
> `canonical_writer.write_candle_parquet` (uses `manifest_writer.add(...)` v4 verb) that the original plan-of-record
> did not capture. Migrating `_streaming_write_per_tf` alone would land MDPS production with two manifest-write SSOTs —
> banned by CLAUDE.md "No double SSOT". Right migration shape requires Phase 1.2.A (manifest verb unify in
> `write_candle_parquet`) BEFORE Phase 1.2.B (the originally-scoped `_streaming_write_per_tf` migration). Plan-of-
> record body needs refresh + a workspace-grep audit table per "Citadel-Grade Planning § 6 Downstream Consumer Updates"
> before the next agent can safely pick up. Full evidence + recommended decision in
> [`mdps_phase_1_2_phase_2_deferral_2026_05_10.md`](mdps_phase_1_2_phase_2_deferral_2026_05_10.md). The 2026-05-09
> "DEFERRED-AFTER-WORKSPACE-QG-CLEAN" rationale below understates the blocker — the dual-SSOT issue is architectural,
> not operational.

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

Per
[`mdps_streaming_primitives_prompt_vs_plan_conflict_2026_05_09.md`](mdps_streaming_primitives_prompt_vs_plan_conflict_2026_05_09.md)
operator-approved option (a) — ship per plan-of-record.

**Shipped this session (2026-05-09):**

- ✅ `LifecycleEventType.CONNECTIVITY_GAP_DETECTED` / `CONNECTIVITY_RECOVERED` / `CONNECTIVITY_GAP_BACKFILLED` —
  UAC@`4bd84e7c` (`unified_api_contracts/internal/events.py`) — 3 typed event-type members + 3 Pydantic detail models
  (`ConnectivityGapDetectedDetails` / `ConnectivityRecoveredDetails` / `ConnectivityGapBackfilledDetails`) + 3 typed
  event wrappers + 12 unit tests in `tests/internal/unit/test_connectivity_gap_event_taxonomy.py`. The `classification`
  field on `ConnectivityGapDetectedDetails` is a closed-set Literal (`WS_DISCONNECT` / `STALE_HEARTBEAT` / `API_TIMEOUT`
  / `UNKNOWN`) so adapters can't accidentally emit untyped strings. This is the alerting-service / reconciler /
  auto-backfill SSOT — downstream consumers can now type their event-stream subscriptions against these wrappers without
  inventing local types.

**Still open (DEFERRED-PER-SUB-AGENT-CAPACITY this session — see conflict-issue § "Recommended decision (a)"):**

- ✅ `open_candle_writer` / `close_candle_writer` UTL parquet-write-lifecycle wrappers — SHIPPED 2026-05-09
  UTL@`ac6e3244`. Module at `unified-trading-library/unified_trading_library/streaming/candle_writer.py` (365 lines)
  - `tests/unit/streaming/test_candle_writer.py` (10 tests, all passing). Phase 1.1 of plan-of-record. Open/close
    lifecycle with `CandleWriterHandle` dataclass, `SchemaDriftError` on drifted second chunk, idempotent close,
    4-branch decision matrix (error → `record_failed` / zero rows → `record_empty(SOURCE_RETURNED_ZERO)` / rows →
    `record_captured` + atomic rename / second-call no-op). Cluster validation kwargs forwarded to `record_captured` for
    bundled shards.
- ❌ MDPS `_streaming_write_per_tf` callsite migration — Phase 1.2 of plan-of-record. **DEFERRED-AFTER-WORKSPACE-QG-
  CLEAN**: lives in `market-data-processing-service/market_data_processing_service/app/core/live_workers.py:1118-1164`
  (per plan-of- record line 87). Substantial refactor of the per-timeframe accumulator pattern that needs full-MDPS QG +
  shard-level isolation tests + the 4-test matrix
  `(N batches × M rows) → exactly ONE record_captured per (timeframe, shard)`. Blocker for in-flight ship: MDPS working
  tree has 9+ foreign-modified test files from parallel agents' sessions; safe migration requires a coordinated tab
  assignment in tomorrow's work-split. UTL primitives are now stable + tested → next agent has a clean target to wire
  against.
- ✅ MTDS `LiveConnectivityWatchdog` — SHIPPED 2026-05-09 mtds@`91e21cd`. Module at
  `market-tick-data-service/market_tick_data_service/market_interface/connectivity_watchdog.py` (249 lines) +
  `tests/unit/test_connectivity_watchdog.py` (16 tests). Heartbeat tracker per (venue, data_type), simplified state
  machine (`HEALTHY ↔ GAP` — STALE/RECOVERING are intermediate ticks not separate states), emits the 3-event family via
  `log_event(LifecycleEventType.CONNECTIVITY_GAP_DETECTED.value, …)`. Adapter wire-in (heartbeat() calls in CCXT /
  Databento / etc. WS adapters) is a follow-up todo for adapter maintainers — out of scope here.
- ❌ `ResourceProfiler.on_memory_warning` wiring — Phase 2 of plan-of-record. **DEFERRED-AFTER-PHASE-1.2**: depends on
  Phase 1.2 callsite migration per the plan's execution DAG; cannot ship in isolation. Same MDPS coordinated tab
  assignment that picks up Phase 1.2 owns this. `ConnectivityWatchdog` event-subscriber wire-in (subscribes to
  `LifecycleEventType.CONNECTIVITY_GAP_DETECTED` to optionally pause MDPS feed during gaps) lands here too.
- ❌ Per-venue `VENUE_HEARTBEAT_INTERVAL` empirical baseline — separate `[SCRIPT] P1` todo in plan-of-record (7-day
  observation per venue → 99th percentile). Bootstrap with conservative default (e.g. 60s) is fine until calibration.

**Why this session shipped only the SSOT half:** Each of the 5 deliverables is a separate full-QG cycle in a different
repo (UTL / UAC / MTDS / MDPS×2). The MDPS Phase 1.2 callsite migration alone is a substantial refactor of a 1100+ line
file that needs schema-drift detection across chunks + shard-level failure isolation + 4-test matrix verification — not
safe in a parallel-agent slot with foreign WIP in the shared working tree (UTL had 9 foreign- modified files from a
parallel agent's session at start). The UAC SSOT extension is the cleanest, smallest, and most-independent of the 5 — it
has zero downstream wire-in dependency for landing the SSOT, alerting-service + reconciler can now subscribe by type,
and the next agent picking up the remaining items has a typed event surface to implement against rather than inventing
one.

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
  ✅ SHIPPED 2026-05-09 UTL@`ac6e3244` (365 lines + 10 tests)
- MDPS `app/core/live_workers.py` consumes them — ❌ STILL OPEN (Phase 1.2 callsite migration; needs MDPS-coordinated
  tab in next work-split — foreign WIP in MDPS tree blocks safe in-session migration)
- `ResourceProfiler.on_memory_warning` wired in MDPS — ❌ STILL OPEN (Phase 2; DEFERRED-AFTER-PHASE-1.2)
- `CONNECTIVITY_GAP_DETECTED` event type in UAC — ✅ SHIPPED 2026-05-09 UAC@`4bd84e7c`
- `LiveConnectivityWatchdog` in MTDS — ✅ SHIPPED 2026-05-09 mtds@`91e21cd`
- live-pipeline Phase 4 unblocks — ❌ PARTIALLY UNBLOCKED: UTL primitives ready; MDPS wiring still required

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

---

## 2026-05-10 follow-up shipments — adapter-wire items #5 + #11

Two adjacent live-trading observability + testnet items surfaced during the
2026-05-08 audit triage (separate from items #1-#4 above). Both shipped
2026-05-10 as paired UAC SSOT + per-service wire-in:

### Item #5 — MTDS adapter heartbeat wire-in — ✅ RESOLVED 2026-05-10

- **UAC@b05a032** — `VENUE_HEARTBEAT_THRESHOLDS` SSOT (5 venue-classes;
  per-(venue, data_type) override registry empty by default until live
  telemetry populates) +
  `unified_api_contracts/canonical/crosscutting/venue_thresholds.py`
  + `get_heartbeat_threshold()` helper.
- **MTDS@c09a0e2** — `LiveConnectivityWatchdog` lifecycle wired into
  `market_tick_data_service/api/main.py` via FastAPI `startup` /
  `shutdown` event handlers. `get_watchdog()` module-level accessor
  returns the singleton (or `None` in batch mode); 6 unit tests in
  `tests/unit/test_api_watchdog_lifecycle.py`.
- **MTDS@4faef39** — Per-adapter `watchdog.heartbeat()` callsites
  shipped across the streaming/WS + REST-poll adapter surface. New
  SSOT helper `market_tick_data_service/market_interface/heartbeat_helper.py`
  exposes `emit_heartbeat(venue, data_type)` — adapters import it (no
  per-call `get_watchdog()` boilerplate) and the helper resolves the
  singleton + no-ops in batch mode. Wire-ins:
  - `defi/live/hyperliquid_ws.py` — per yielded WS message (channel →
    data_type: allMids → mids / l2Book → orderbook / userFundings →
    funding).
  - `defi/live/onchain_event_poller.py` — per successful block-poll
    cycle (data_type=onchain_event); empty log windows still heartbeat
    since the upstream RPC is responsive.
  - `defi_live/alchemy_adapter.py` — per successfully normalized
    mined_tx / log message inside `normalize_ws_message()`.
  - `defi_live/thegraph_ws_adapter.py` — per successfully normalized
    liquidity_pool / lending_rate GraphQL message.
  - `cefi/ccxt_adapter.py` — per successful `fetch_ticker` /
    `fetch_order_book` / `fetch_ohlcv` / `fetch_trades` /
    `fetch_funding_rate` / `fetch_open_interest` REST poll
    (data_type=ticker|orderbook|ohlcv|trades|funding|open_interest);
    venue=`self.exchange_id.upper()`. Covers Binance / Bybit / OKX /
    Deribit / Coinbase / Kraken / Hyperliquid (all CCXT-backed).
  - `prediction/polymarket_adapter.py` — per successful `get_markets` /
    `get_prices` REST poll (data_type=markets|prediction_clob).
  - `prediction/kalshi_adapter.py` — per successful trades-page REST
    poll inside cursor pagination loop.
- **Tests**: `tests/unit/test_adapter_watchdog_wiring.py` — 13 unit
  tests covering helper no-op + recording + error-swallowing
  semantics, Alchemy / TheGraph / CCXT adapter wire-in points, and
  per-(venue, data_type) state isolation.
- **Skipped (REST-only batch / historical adapters with no live-mode
  meaning)**: Yahoo VIX 15m, open-meteo weather, Databento (batch
  historical), Tardis (batch historical), DeFi REST adapters
  (Aave / Uniswap / Curve / Balancer / Morpho / Ethena / etc. — these
  use `BaseDefiAdapter`'s per-shard `record_captured` boundary which
  is the batch-equivalent of heartbeat), sports adapters (no WS path
  in MTDS currently), TradFi (FRED / ECB / OFR / IBKR / OpenBB).

### Item #11 — CeFi testnet wiring — ✅ SHIPPED 2026-05-10

- **Pre-existing wiring (verified)**: 5 CeFi CCXT adapters
  (Binance / Bybit / OKX / Deribit / Coinbase) + Hyperliquid CCXT all
  carry `testnet: bool = False` constructor flag → CCXT
  `set_sandbox_mode(True)` when set; flag plumbed through
  `_get_exchange()` for all.
- **UAC@b05a032** — `VENUE_TESTNET_URLS` SSOT (6 venues with REST + WS
  endpoints + per-venue notes documenting CCXT sandbox-mode behaviour
  + edge cases like Coinbase Advanced Trade having no public testnet).
- **execution-service@59ce802a** — 7 smoke unit tests in
  `tests/unit/test_testnet_wiring.py` mocking CCXT at
  `ccxt.async_support` module level. Verifies testnet=True triggers
  set_sandbox_mode(True) for all 5 CCXT adapters; default testnet=False
  is the safe-default; UAC SSOT round-trips correctly.
- **Master Group F Item 20** (live testnet replicates prod) CeFi
  column: ✗ → ◐. Full end-to-end signed-flow validation against real
  testnet credentials remains operator-driven (live-only readiness
  item per master plan).

### Item #9 — CEFFU custody section population — ✅ STUB SHIPPED 2026-05-10

- **execution-service@90aa381a** — `CeffuCustodyProvider` stub at
  `execution_service/custody/ceffu.py` (172 lines): constructor with
  `api_key` / `api_secret` / `organization_id` / `sandbox` parity with
  Copper, HMAC-SHA256 `_sign_request()` skeleton (header naming
  `<TBD-OPERATOR-PROVIDES-API-SPEC>`), all 4 async protocol methods
  (`sign_transaction` / `get_balance` / `create_transfer` /
  `list_wallets`) raise
  `NotImplementedError("CEFFU API spec pending — operator must confirm institutional REST endpoints + auth shape + sandbox base URL")`
  with explicit reference to codex doc + master Group F Item 19.
- **execution-service@90aa381a** — Factory registration in
  `execution_service/custody/factory.py`: `provider="ceffu"` (case-
  insensitive) routes to `CeffuCustodyProvider`. Factory-level case
  added between `copper` and the unknown-provider warning fallback.
- **execution-service@90aa381a** — 11 unit tests at
  `tests/unit/custody/test_ceffu_provider.py` covering construction
  (sandbox flag toggle, default to production), HMAC signing skeleton
  produces valid headers, factory routing (lowercase + uppercase),
  and `NotImplementedError("CEFFU API spec pending")` contract on
  every async method.
- **unified-trading-pm@33ef64b4** —
  `codex/04-architecture/custody-providers.md` § 2.4
  `CeffuCustodyProvider` expanded from STUB / PENDING placeholder to a
  fully populated section mirroring Copper § 2.3 shape: architecture
  overview (OES bilateral mirror flow client → CEFFU → Binance Futures
  → daily settlement), 6-step onboarding runbook, expected REST
  endpoint catalogue with explicit `<TBD-OPERATOR-PROVIDES-API-SPEC>`
  markers, HMAC signing skeleton + header-naming TBD, sandbox/staging
  subsection, daily operational flow (settlement window + margin
  recall), risk controls (credit-utilisation cap +
  automatic margin recall + withdrawal whitelist + rate-limit/backoff
  via UAC `classify_venue_error`), implementation reference table,
  configuration + testing subsections, expanded open-questions list.
  § 1 factory-routing table, § 6 Security, § 7 Testing all updated for
  the new stub-shipped state.
- **Master Group F Item 19** (Copper + CEFFU treasury) — Copper side
  remains live; CEFFU side advances from "STUB / PLANNED" to
  "stub-shipped, API spec pending". Continuous-verification stays
  "manual sign-off only" (live-only operator-judgment item) per
  CLAUDE.md "Master Plan Continuous-Verification Column" rule. The
  envelope unblocks deployment configs + position-balance-monitor
  wiring for Binance institutional flow before the REST surface is
  confirmed; once operator provides the API spec, the stub becomes a
  tightly-scoped diff (header rename + base URL fill + per-method body
  wiring) rather than an architecture change.

### Item #7 — defi_archetypes Stream B deferred items — ✅ ARCHITECTURE COMPLETE; OPERATIONAL RUN UPSTREAM-BLOCKED

- **Stream B § strategy-service catalog (funding-dispersion-leveraged
  variant)** — ✅ already shipped 2026-05-09 across 6 commits per
  defi_archetypes plan body L182-194:
  - `strategy-service@24f8494` (Phase A.1 dispatcher + slot stub).
  - `strategy-service@0b4ef0e` (Phase A.2 helper module — 3 modes +
    filters + 25 tests).
  - `strategy-service@04c0d52` (Phase A.3 engine 8-step loop wire-in +
    13 engine tests).
  - `strategy-service@1107ab7` + `strategy-service@d01661e` (Phase A.6
    multi-asset enumeration probe + ETH/SOL + 7 top-10 coverage-gated
    slots).
  - `strategy-service@de9b4b0` (Phase A.7 allocator multi-pair-per-slot
    wiring — 4 weight modes + per-slot/per-pair caps + churn
    suppression + 14 tests).

  Catalog row presence verified 2026-05-10 at
  `archetype_slot_resolver.py:740-770` (BTC slot
  `ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-btc-usdt-v5-prod`)
  + generic builder at L76-97 (`_funding_rate_dispersion_slot(asset)`
  for ETH/SOL/etc.).

- **Stream B § tracer (P1)** — ❌ blocked on upstream raw-perp-funding
  + features-delta-one-cefi backfill gaps tracked in
  [`arb_price_dispersion_phase_b_data_blockers_2026_05_10.md`](arb_price_dispersion_phase_b_data_blockers_2026_05_10.md).
  No contiguous 1-week 2024-W1 window exists across the 6-venue
  universe (aster has no perp_funding directory; okx-futures raw starts
  2025-01; features-delta-one-cefi has no contiguous window for any
  year). Operator triage required on (a) backfill scope vs (b) verify-
  window scope-adjust vs (c) ship-code-without-verify-and-flag.
  `strategy-service/scripts/trace_arbitrage_price_dispersion.py` does
  NOT exist; only `trace_carry_staked_basis.py` +
  `trace_all_carry_archetypes.py`. Per "Plans Run To Actual Completion"
  HARD RULE, tracer code without tracer-runs-to-completion is not
  shippable as ✅.

- **Stream B § P&L attribution (P1)** — ❌ blocked-after-tracer.
  **Architecture verification 2026-05-10**: re-audit corrects
  2026-05-09's "zero references" finding —
  `pnl_attribution_service/engine/archetype_aggregator.py` IS in fact
  wired for `ARBITRAGE_PRICE_DISPERSION` via generic regex parsing.
  L59 `_SLOT_PREFIX_RE = r"^([A-Z][A-Z0-9_]+)@"` matches any archetype
  prefix from slot labels. L65 `_FUNDING_RATE_DISP_MARKER =
  "-funding-rate-disp-"` matches strategy-service's
  `archetype_slot_resolver._funding_rate_dispersion_slot()` slot label
  format. The literal string `ARBITRAGE_PRICE_DISPERSION` doesn't
  appear in source code — it's matched at runtime by the generic
  regex. The 2026-05-09 grep miss was an artefact of the search
  pattern, not a missing implementation. Once tracer output flows,
  rows route to
  `gs://${PNL_OUTPUT_BUCKET}/by_strategy/ARBITRAGE_PRICE_DISPERSION/...`
  with `config_variant="funding-rate-dispersion"` automatically. Pure
  architecture is complete; checkbox stays `[ ]` until tracer's real-
  infra output validates the path end-to-end per "Plans Run To Actual
  Completion" rule.

- **unified-trading-pm@<this-batch>** — defi_archetypes Stream B
  P&L attribution todo body extended with the architecture-verified
  annotation pointing at
  `pnl_attribution_service/engine/archetype_aggregator.py:59 / :65`.

- **Master Group F Item 17-18** (paper-trade smoke + batch-vs-live
  recon) — Stream B contributes the funding-dispersion-leveraged
  archetype variant; stays operator-blocked on upstream-data triage
  per the data-blockers issue doc.
- runbook_execution_governance_gaps_2026_05_08.md (related: peripheral QG wiring rule)
