---
title:
  "Bar-edge (open/left vs close/right) systemic remediation — close the gate blind-spot, fix latent pre-agg ingestion,
  recompute the left-edge features corpus"
created: 2026-06-08
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-cross-cutting
status: active
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
locked_by: live-defi-rollout
locked_since: 2026-06-08
source:
  - plans/active/issues/bar_edge_left_vs_right_systemic_2026_06_08.md (harsh, data-verified 2026-06-08)
  - plans/active/issues/hyperliquid_ohlcv_left_edge_timestamp_2026_06_08.md (one instance of the class)
  - operator 2026-06-08 ("file it so it blocks us; closed-candle stamped on the open/left is lookahead → leakage for
    MDPS + features")
---

# Bar-edge systemic remediation — one canonical edge (RIGHT = `t_close`) everywhere

> **The invariant (UAC `bar_boundary.py` / UTL `compute_bar_close_boundary`): a CLOSED candle is timestamped on its
> RIGHT edge (`t_close`).** Stamping the OPEN/left (vendor bar-start) edge on a closed bar is **look-ahead → leakage**:
> a feature/PIT-join keyed on that timestamp sees a bar one interval before it actually closed. This is a HARD
> data-correctness issue on the heartbeat path — per the heartbeat rule it BLOCKS feature-layer trust until gated + the
> left-edge corpus is purged. Surfacing issue: [[bar_edge_left_vs_right_systemic_2026_06_08]] (read it — full site
> register + data-state verification).

## Severity (post data-state verification — see the issue doc)

- ✅ **MDPS processed candle store is right-edge CORRECT everywhere verified** (tradfi databento ohlcv, defi dex_swaps):
  MDPS normalizes the open-edge raw to `t_close`. **So the RAW→processed candle migration is NOT corrupted** — this is
  NOT a hard blocker for the per-AG raw/manifest `--apply`.
- 🔴 **Realized bugs = the two features-service re-resamplers** (`candle_resampler.resample_ohlcv`
  `closed/label="left"`; `flow_interaction` `truncate("1m")`) — they took CORRECT right-edge candles and degraded them
  to left-edge, downstream of the gate. **FIXED 2026-06-08 (features-service@7a4fafd9, QG green)** — but the PRE-FIX
  `features-*` corpus carries left-edge timestamps and must be recomputed.
- 🟡 **Latent**: pre-aggregated candle fetchers (HL/Pacifica/Lighter/uniswap/yahoo VIX/massive/ccxt/aster + polygon
  refdata) stamp the open edge but are not currently writing consumed candles to prod. Correctness-in-depth fix so they
  can't bite if activated.
- 🔴 **Gate blind-spot**: `assert_bar_boundary_contract` validates grid-alignment + interval width + `available_at`, but
  a uniform one-interval left-shift stays on-grid → **the gate passes an open-edge bar**. The gate enforces alignment,
  not which edge.

## What this BLOCKS (precise — not a blanket migration halt)

- **Feature-layer trust** for any coarser-than-base timeframe + `flow_interaction` outputs is RED until (a) the gate
  catches edge errors and (b) the pre-fix left-edge `features-*` corpus is recomputed/rolled-forward. New feature
  computes after `7a4fafd9` are correct.
- **Does NOT block** the per-AG raw/manifest/instruments-store `--apply` (candle store verified right-edge). The
  coordinator carries this as a feature-layer gate, not a raw-migration gate.

## Phase 0 — close the gate blind-spot FIRST (so nothing regresses; QG-enforced, all AGs)

- [x] ✅ [SCRIPT] P0. Gate-blind-spot CLOSED — new dedicated **`check_bar_edge_open_ingestion.py` (STEP 5.92)** —
      **unified-trading-pm@b4245a7dd**: AST, per-function; flags a vendor bar-START field (`periodStartUnix`/
      `openTimestamp` anywhere; candle-fn `["t"]`/`.get("t")`) stamped without a close conversion
      (`compute_bar_close_boundary` / vendor close field / `[6]`), baseline-ratchet (2 latent sites baselined: massive→
      Phase 4b, MDPS `liquidity_adapter`), wired into base-service.sh **+ base-library.sh**, fleet-swept green (all 25
      repos per-scope), 8 unit tests + planted-regression proven (exit 1 → exit 0). NOTE: the broad `bar[0]`/`.index`
      heuristics are deliberately left to the runtime ingestion-time assertion (P1 below) — static-flagging them
      false-positived the verified-correct MDPS tick-aggregators (rule-11 fleet-safety).
- [x] ✅ [SCRIPT] P0. **Cross-source edge fixture** — **features-service@438c2c30**:
      `tests/delta_one/unit/test_cross_source_bar_edge_equivalence.py` — Path A (tick-aggregated `resample_ohlcv`) and
      Path B (pre-agg vendor open-edge bar via `compute_bar_close_boundary`) produce IDENTICAL `t_close` across 15s→1m +
      1m→5m (6 tests / 3 guards: t_close equivalence, right-edge labels, volume-grouping). Paths AGREED — confirms the
      `closed="right",label="right"` fix (features-service@7a4fafd9). Runs in features `quality-gates.sh` (the
      peripheral QG wiring); QG exit 0.
- [x] ✅ [SCRIPT] P1. **Ingestion-time assertion** — **unified-trading-library@33ef2d31**:
      `availability_stamping.assert_close_edge(stamped_close, *, vendor_close=None, open_ts=None, timeframe=None)` —
      Mode 1 asserts the stamped edge == the vendor close field (HL/Pacifica `T`, kline `[6]`); Mode 2 asserts it ==
      `compute_bar_close_boundary(open_ts, timeframe)` close (catches a left/open stamp); raises
      `BarBoundaryViolationError` on mismatch / naive-tz. Exported alongside `compute_bar_close_boundary`; 15 tests; QG
      exit 0. Adapter wiring (pacifica/HL/aster already use the close field directly post-Phase-1) is adoptable
      defense-in-depth.

## Phase 1 — fix every pre-aggregated ingestion site to the canonical close edge

> Rule: prefer the vendor's explicit CLOSE field (`T` / kline `[6]`) where it exists; else
> `compute_bar_close_boundary(open_ts, timeframe)`. **Never a hardcoded `+60s`.** Sites from the issue register:

- [ ] [CODE] P1. instruments-service refdata adapters: `cefi/hyperliquid.py:255`, `cefi/aster.py:375`,
      `cefi/ccxt_adapter.py:299` (high blast radius — backs many CEX venues), `tradfi/polygon.py:234` (removed provider
      — fix-or-delete the path). Confirm `cefi/tardis.py:856` is already close (likely ✅, verify vs cassette).
- [ ] [CODE] P1. market-tick-data-service pre-agg fetchers: `umi_tick_provider.py:1115` (`_fetch_pacifica_candles`),
      `:1945/1959` (`_fetch_lighter_candles`), `market_interface/adapters/defi/uniswap_v3_adapter.py:714`
      (`periodStartUnix`), `tradfi/yahoo_finance_adapter.py:84-92` (VIX `ohlcv_15m` index), `cefi/ccxt_adapter.py:359`.
- [ ] [CODE] P1. Massive: `tradfi/massive_tradfi_rest_connector.py:490` (`t` open) — **coordinate with
      `tradfi_massive_dual_source_2026_05_28.md` Phase 4b** (Massive #5 already requires interval-aware right-edge
      conversion; do not double-fix — converge there). Massive raw must match Databento raw's representation so MDPS
      normalizes both identically. ALSO fold in: batch rows pre-stamp `available_at=now(UTC)` (`:472/:484/:503`) which
      the writer persists (orchestrator stamps only when the column is absent) — must become `t_close`-anchored.
- [ ] [CODE] P0. **Databento `ohlcv_1m` — MDPS's protective shift is column-NAME-keyed and the prod raw shape that
      defeats it already exists (METASTABLE, one reprocess from corpus corruption — MTDS audit re-verification
      2026-06-10, reconciled against this plan's 06-08 data-state)**: the issue doc's own two data points, connected:
      (1) prod raw carries OPEN-edge values under the column name **`timestamp`** (AAPL 2026-05-15 sample — "`timestamp`
      column = `ts_event` ns verbatim"; the MTDS alias `ts_event→timestamp` at `engine/orchestrator.py:613-616`, applied
      in PartitionedTickWriter `:1164/:1236`, produces exactly this shape and has been live since 2026-04-16); (2) MDPS
      shifts start→end ONLY when the column is literally named `ts_event`
      (`mdps app/adapters/tradfi/ohlcv_passthrough.py:280,288-293` `is_start = ts_col == "ts_event"`, preference order
      `["timestamp", "ts_event", "ts_init"]`; grid math `:159,:181` then lands an unshifted bar-start one interval
      EARLY). The verified-correct processed store (ETHA `14:30→14:31`, this plan § Severity) is only producible from
      `ts_event`-named input — so the verified corpus was built from a raw vintage/path that kept `ts_event`, while
      `timestamp`-named open-edge raw verifiably exists (AAPL). **Any MDPS reprocess/backfill over the `timestamp`-named
      raw silently produces left-shifted candles; production fetches `ohlcv_1m` by default
      (`databento_adapter.py:918-919`) and keeps writing the laundered shape.** Also: MTDS stamps raw-surface
      `available_at ≈ bar_open+10ms` (`orchestrator.py:1283-1319`) — open-anchored on a closed bar (CF-8 spirit; the
      processed layer re-derives, raw consumers would inherit it). Fix: (a) MTDS ingest converts `ts_event→t_close`
      interval-aware (`compute_bar_close_boundary`) scoped to `ohlcv_*` data_types (trades/tbbo `ts_event` is point
      event time — alias stays) + anchor raw `available_at` to `t_close`; (b) make the MDPS shift content/source-aware,
      not column-name-keyed (it must not silently NOT-shift a `timestamp`-named open-edge input); (c) UAC
      `external/databento/schemas.py:13` calls `DatabentoOhlcvBar.ts_event` "Bar close timestamp" — WRONG (bar start);
      fix the docstring. (d) Data-state: census WHICH raw files carry `ts_event` vs `timestamp` naming before the next
      tradfi candle rebuild. Evidence: `plans/audit/results/mtds_mdps_master_audit_2026_06_09.md` § Re-verification B2.
      — market-tick-data-service + market-data-processing-service + unified-api-contracts
- [x] ✅ [CODE] P2. Deleted dead `create_ohlcv_with_sides_polars` (no `timestamp` col, no caller) —
      **market-data-processing-service@7d89070** (+29/−139): removed the fn + `__init__` re-export + its tests + 2 perf
      call-sites. rg across all of `.tabs/7` confirmed zero non-test callers. QG exit 0.

## Phase 2 — purge the left-edge `features-*` corpus (the realized-bug cleanup)

- [ ] [DATA] P0. Promote **features-service@7a4fafd9** (the fix) staging→main once the staging lock clears (tracked in
      the issue doc § Shipping status; execution-service breaking-bump cascade is unrelated).
- [ ] [DATA] P1. Recompute the pre-fix left-edge `features-*` corpus: scope = every coarser-than-base delta_one
      timeframe + cross_instrument `flow_interaction` outputs. Decide recompute-vs-roll-forward by horizon (a
      backtest/feature consumer reading pre-fix history gets one-interval-early features → leakage). Materialise the
      recompute manifest + sample-verify right-edge labels on the affected days.

## Phase 3 — Era/migration coordination

- [ ] [DATA] P2. Bake the edge check into the per-AG ①–⑫ pre-apply audit (⑪ batch=live now also asserts
      edge-consistency) and into the cross-source equivalence item (`batch_live_symmetry` (k)). See the
      audit-instruction threading below.

## Success criterion

The gate catches an open-edge ingestion (planted-regression test fails); every pre-agg site converts to `t_close`; a
cross-source fixture proves tick-agg and pre-agg produce the same edge; the `features-*` corpus is right-edge on the
affected history (sample-verified). Re-running the bar-edge sweep finds zero open-edge consumed candles.

## Codex SSOT updates

- `codex/02-data/` bar-boundary / candle-edge convention doc — state the RIGHT-edge invariant + "never consume raw ohlcv
  directly; always the processed candle" + the gate's coverage (now incl. ingestion adapters). Write the stub if absent.
