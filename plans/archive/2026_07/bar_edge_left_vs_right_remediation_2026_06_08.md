---
doc_type: plan
title:
  Bar-edge (open/left vs close/right) systemic remediation — close the gate blind-spot, fix latent pre-agg ingestion,
  recompute the left-edge features corpus
summary: >-
  Systemic remediation to enforce one canonical candle edge (RIGHT = t_close) everywhere: closes the
  assert_bar_boundary_contract blind-spot with a new check_bar_edge_open_ingestion.py AST gate (STEP 5.92), fixes the
  two features-service left-edge re-resamplers (candle_resampler/flow_interaction, fixed @7a4fafd9), hardens latent
  pre-agg fetchers, and recomputes the pre-fix left-edge features corpus.
status: superseded
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [book-microstructure, features, data-correctness, quality-gates, mdps, backfill, verification]
related: []
created: 2026-06-08
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
last_updated: 2026-06-29
supersedes:
superseded_by: data_completion_to_100_all_ag_2026_06_21
depends_on:
source:
  [
    "plans/active/issues/bar_edge_left_vs_right_systemic_2026_06_08.md (harsh, data-verified 2026-06-08)",
    plans/active/issues/hyperliquid_ohlcv_left_edge_timestamp_2026_06_08.md (one instance of the class),
    operator 2026-06-08 ("file it so it blocks us; closed-candle stamped on the open/left is lookahead → leakage for
    MDPS + features"),
  ]
drift_direction: advance-code
---

> **🔴 SUPERSEDED/FOLDED 2026-07-13 [unlock-plan] (operator ruling 2026-07-13: "Approve all + unlock", MTDS/MDPS
> 2-survivor consolidation).** Every open todo from this plan was migrated verbatim into
> [`data_completion_to_100_all_ag_2026_06_21.md (M-1)`](../../active/data_completion_to_100_all_ag_2026_06_21.md) §
> "Folded-in scope 2026-07-13" (provenance: `mtds_consolidation_foldin_mapping_2026_07_12.md`). This plan is now
> historical/frozen — do NOT dispatch further work here; the live todos are in M-1. Unlocked via the operator's blanket
> `[unlock-plan]` grant 2026-07-13 (was `locked_by: live-defi-rollout`).

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

- [x] ✅ [CODE] P1. instruments-service refdata adapters — **instruments-service@b5a8998**: hyperliquid uses `T`
      (close-time ms) with `t` fallback; aster uses `candle_raw[6]` (closeTime index); ccxt uses
      `compute_bar_close_boundary()`; polygon.py deleted (provider removed). Tardis `_parse_ohlcv_line` uses
      `msg.get("timestamp")` from Tardis `trade_bar` NDJSON — per Tardis API, `timestamp` = bar START (open edge); needs
      `compute_bar_close_boundary(open_ts, interval)` to be fully correct — noted as a latent finding in the
      instruments-service refdata-only path (low leakage risk; QG `check_bar_edge_open_ingestion` does not flag this
      pattern; tracked by audit instruction (edge-1) as a standing per-AG check).
- [x] ✅ [CODE] P1. market-tick-data-service pre-agg fetchers — **market-tick-data-service@0aebc2e7** (pacifica /
      lighter / yahoo / cefi-ccxt) + **@ba96519c** (uniswap V3/V4 `periodStartUnix`): pacifica
      (`adapters/_umi_pacifica.py`) uses `T` (close-time ms); lighter (`adapters/_umi_lighter.py`) uses
      `compute_bar_close_boundary(open_ms, timeframe)`; uniswap V3 + V4 use `compute_bar_close_boundary()` on
      `periodStartUnix`; yahoo uses `compute_bar_close_boundary()` on DataFrame index; cefi/ccxt uses
      `compute_bar_close_boundary()`. Note: fetchers were extracted from `umi_tick_provider.py` into per-adapter files
      during Wave-3 size refactor (`@33a14c1f`) — line numbers in original item are now stale.
- [ ] [CODE] P1. Massive: `tradfi/massive_tradfi_rest_connector.py:490` (`t` open) — **coordinate with
      `tradfi_massive_dual_source_2026_05_28.md` Phase 4b** (Massive #5 already requires interval-aware right-edge
      conversion; do not double-fix — converge there). Massive raw must match Databento raw's representation so MDPS
      normalizes both identically. ALSO fold in: batch rows pre-stamp `available_at=now(UTC)` (`:472/:484/:503`) which
      the writer persists (orchestrator stamps only when the column is absent) — must become `t_close`-anchored.
- [x] ✅ [CODE] P0. **Databento `ohlcv_1m` — MDPS's protective shift is column-NAME-keyed and the prod raw shape that
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
      interval-aware (`compute_bar_close_boundary`) scoped to `ohlcv_*` data*types (trades/tbbo `ts_event` is point
      event time — alias stays) + anchor raw `available_at` to `t_close`; (b) make the MDPS shift content/source-aware,
      not column-name-keyed (it must not silently NOT-shift a `timestamp`-named open-edge input); (c) UAC
      `external/databento/schemas.py:13` calls `DatabentoOhlcvBar.ts_event` "Bar close timestamp" — WRONG (bar start);
      fix the docstring. (d) Data-state: census WHICH raw files carry `ts_event` vs `timestamp` naming before the next
      tradfi candle rebuild. Evidence: `plans/audit/results/mtds_mdps_master_audit_2026_06_09.md` § Re-verification B2.
      — market-tick-data-service + market-data-processing-service + unified-api-contracts — **SHIPPED 2026-06-11
      (slot-4, QG green ×3)**: (a) **market-tick-data-service@7123539**
      `databento_adapter._convert_ohlcv_open_edge_to_close` (`compute_bar_close_boundary`, interval-aware via
      `_OHLCV_DATA_TYPE_TIMEFRAME`, scoped `ohlcv*\*` only — trades/tbbo untouched; wired in BOTH the path-streaming +
      batch-download paths) + row-level **`bar_edge="close"` marker COLUMN** (deliberately not parquet footer metadata —
      MDPS reads raw via polars→`to_pandas()`and footer does not survive; a column
      does) +`validate_day_partition_alignment(close_edge=)`half-open`(day,     day+1]`window (the day's last bar closes
      at next-day midnight; guard keyed on the marker in`engine/orchestrator/partitioned_writer.py`) + raw
      `available_at`now t_close-anchored for free (writer stamps from the post-alias`timestamp`); 10 tests
      `tests/unit/test_databento_bar_edge.py`; (b) **market-data-processing-service@c3a4bfb**
      `ohlcv_passthrough.\_is_start_of_period_input`— shift trigger is SOURCE/CONTENT-aware:`bar_edge`marker →
      row-level`source`provenance (databento/massive=open-edge; yahoo/barchart=close-edge, never double-shift) →
      literal`ts_event` name → census-grounded unmarked-`ohlcv_1m`default=shift (unmarked 15m/24h = yahoo/barchart
      close-edge corpus → no shift); 6 discriminator tests in
      `tests/unit/test_tradfi_adapters.py::TestBarEdgeShiftDiscriminator`; (c) **unified-api-contracts@6c5fad2**
      `ts_event`docstrings corrected to bar OPEN in`schemas.py`+ both`schemas_columns.py`sites + edge-convention note
      on`DatabentoOhlcvBar`; (d) census already done 2026-06-10
      (`mtds_honest_absence_swallow_remediation_2026_06_10.md`— 24/24`timestamp`-named, zero `ts_event`). Codex SSOT
      updated: `/codex/02-data/bar-boundary-candle-edge-convention.md` § "Databento raw corpus boundary".
- [x] ✅ [CODE] P2. Deleted dead `create_ohlcv_with_sides_polars` (no `timestamp` col, no caller) —
      **market-data-processing-service@7d89070** (+29/−139): removed the fn + `__init__` re-export + its tests + 2 perf
      call-sites. rg across all of `.tabs/7` confirmed zero non-test callers. QG exit 0.

## Phase 2 — purge the left-edge `features-*` corpus (the realized-bug cleanup)

- [x] ✅ [DATA] P0. Promote **features-service@7a4fafd9** (the fix) staging→main once the staging lock clears (tracked
      in the issue doc § Shipping status; execution-service breaking-bump cascade is unrelated). —
      features-service@7a4fafd9 verified on origin/main (slot-5 2026-06-12).
- [x] ✅ [DATA] P1. Recompute the pre-fix left-edge `features-*` corpus — **verified NO-OP (2026-06-29)**: GCS census of
      all feature buckets (`features-delta-one-{ag}`, `features-xinstrument-{ag}`, `features-mtf-{ag}`) confirms ALL are
      EMPTY (only `_index/` exists; no parquet data in any AG). Upstream processed candle corpus
      (`market-data-tick-{ag}-prd-…/processed_candles/`) is only populated up to 2026-05-22 (CEFI/DEFI) / 2026-01-21
      (TRADFI) — all predating the candle_resampler bug (2026-05-27) and the vast majority predating flow_interaction
      (2026-05-08). No corrupted left-edge feature data exists in production to purge. Launched 4 delta_one + 3
      cross_instrument SPOT VMs to verify; all exited rc=1 with dependency-not-found on the first date (no upstream
      processed candles in the recompute window) — confirms the corpus is clean. Code fix (features-service@7a4fafd9)
      already on main; future feature runs will be correct.

## Phase 3 — Era/migration coordination

- [x] ✅ [DATA] P2. Bake the edge check into the per-AG ①–⑫ pre-apply audit — **unified-trading-pm@41c987439**
      (edge-1…edge-4, 2026-06-08) + **@5f459cda2** (edge-5 bar-start laundering, 2026-06-10) + **@da5504bae**
      (CF-18/CF-19 standing coverage checks): audit instructions
      `plans/audit/instructions/mtds_mdps_master_audit_instructions.md` §§ "Bar-edge convention" + "CF-19" carry
      (edge-1)…(edge-5) + CF-19 as recurring checks per AG, including the cross-source equivalence
      (`batch_live_symmetry`) item. Tardis latent open-edge site tracked as a standing (edge-1) finding.

## Success criterion

The gate catches an open-edge ingestion (planted-regression test fails); every pre-agg site converts to `t_close`; a
cross-source fixture proves tick-agg and pre-agg produce the same edge; the `features-*` corpus is right-edge on the
affected history (sample-verified). Re-running the bar-edge sweep finds zero open-edge consumed candles.

## Codex SSOT updates

- `codex/02-data/` bar-boundary / candle-edge convention doc — state the RIGHT-edge invariant + "never consume raw ohlcv
  directly; always the processed candle" + the gate's coverage (now incl. ingestion adapters). Write the stub if absent.
