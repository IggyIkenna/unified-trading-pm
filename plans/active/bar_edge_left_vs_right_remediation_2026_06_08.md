---
title: "Bar-edge (open/left vs close/right) systemic remediation — close the gate blind-spot, fix latent pre-agg ingestion, recompute the left-edge features corpus"
created: 2026-06-08
author: ikenna
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
  - operator 2026-06-08 ("file it so it blocks us; closed-candle stamped on the open/left is lookahead → leakage for MDPS + features")
---

# Bar-edge systemic remediation — one canonical edge (RIGHT = `t_close`) everywhere

> **The invariant (UAC `bar_boundary.py` / UTL `compute_bar_close_boundary`): a CLOSED candle is timestamped on its
> RIGHT edge (`t_close`).** Stamping the OPEN/left (vendor bar-start) edge on a closed bar is **look-ahead → leakage**:
> a feature/PIT-join keyed on that timestamp sees a bar one interval before it actually closed. This is a HARD
> data-correctness issue on the heartbeat path — per the heartbeat rule it BLOCKS feature-layer trust until gated +
> the left-edge corpus is purged. Surfacing issue:
> [[bar_edge_left_vs_right_systemic_2026_06_08]] (read it — full site register + data-state verification).

## Severity (post data-state verification — see the issue doc)

- ✅ **MDPS processed candle store is right-edge CORRECT everywhere verified** (tradfi databento ohlcv, defi dex_swaps):
  MDPS normalizes the open-edge raw to `t_close`. **So the RAW→processed candle migration is NOT corrupted** — this is
  NOT a hard blocker for the per-AG raw/manifest `--apply`.
- 🔴 **Realized bugs = the two features-service re-resamplers** (`candle_resampler.resample_ohlcv` `closed/label="left"`;
  `flow_interaction` `truncate("1m")`) — they took CORRECT right-edge candles and degraded them to left-edge, downstream
  of the gate. **FIXED 2026-06-08 (features-service@7a4fafd9, QG green)** — but the PRE-FIX `features-*` corpus carries
  left-edge timestamps and must be recomputed.
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

- [ ] [SCRIPT] P0. Extend `check_mdps_bar_boundary_compliance.py` (the MDPS bar-boundary QG) to cover **reference-data +
      pre-aggregated ingestion adapters** (not just the MDPS write path) — flag any adapter that stamps a vendor bar's
      START field (`t`/`periodStartUnix`/DataFrame index/`bar[0]`) without a `compute_bar_close_boundary` /
      explicit-close-field conversion. Baseline-ratchet the known latent sites; NEW open-edge ingestion fails the commit.
- [ ] [SCRIPT] P0. Add a **cross-source edge fixture** to the QG: the same instrument+window from a tick-aggregated and a
      pre-aggregated source MUST produce the SAME `t_close`. Wire it as a peripheral-script QG (MDPS + features).
- [ ] [SCRIPT] P1. **Ingestion-time assertion**: where a vendor close field exists (HL/Pacifica `T`, Binance kline `[6]`),
      assert it matches the stamped edge; raise on mismatch (no silent pass-through of the open edge).

## Phase 1 — fix every pre-aggregated ingestion site to the canonical close edge

> Rule: prefer the vendor's explicit CLOSE field (`T` / kline `[6]`) where it exists; else
> `compute_bar_close_boundary(open_ts, timeframe)`. **Never a hardcoded `+60s`.** Sites from the issue register:

- [ ] [CODE] P1. instruments-service refdata adapters: `cefi/hyperliquid.py:255`, `cefi/aster.py:375`,
      `cefi/ccxt_adapter.py:299` (high blast radius — backs many CEX venues), `tradfi/polygon.py:234` (removed provider —
      fix-or-delete the path). Confirm `cefi/tardis.py:856` is already close (likely ✅, verify vs cassette).
- [ ] [CODE] P1. market-tick-data-service pre-agg fetchers: `umi_tick_provider.py:1115` (`_fetch_pacifica_candles`),
      `:1945/1959` (`_fetch_lighter_candles`), `market_interface/adapters/defi/uniswap_v3_adapter.py:714`
      (`periodStartUnix`), `tradfi/yahoo_finance_adapter.py:84-92` (VIX `ohlcv_15m` index), `cefi/ccxt_adapter.py:359`.
- [ ] [CODE] P1. Massive: `tradfi/massive_tradfi_rest_connector.py:490` (`t` open) — **coordinate with
      `tradfi_massive_dual_source_2026_05_28.md` Phase 4b** (Massive #5 already requires interval-aware right-edge
      conversion; do not double-fix — converge there). Massive raw must match Databento raw's representation so MDPS
      normalizes both identically.
- [ ] [CODE] P2. Delete dead `polars_candle_engine.py:138 create_ohlcv_with_sides_polars` (no `timestamp` col, no caller).

## Phase 2 — purge the left-edge `features-*` corpus (the realized-bug cleanup)

- [ ] [DATA] P0. Promote **features-service@7a4fafd9** (the fix) staging→main once the staging lock clears (tracked in
      the issue doc § Shipping status; execution-service breaking-bump cascade is unrelated).
- [ ] [DATA] P1. Recompute the pre-fix left-edge `features-*` corpus: scope = every coarser-than-base delta_one timeframe
      + cross_instrument `flow_interaction` outputs. Decide recompute-vs-roll-forward by horizon (a backtest/feature
      consumer reading pre-fix history gets one-interval-early features → leakage). Materialise the recompute manifest +
      sample-verify right-edge labels on the affected days.

## Phase 3 — Era/migration coordination

- [ ] [DATA] P2. Bake the edge check into the per-AG ①–⑫ pre-apply audit (⑪ batch=live now also asserts edge-consistency)
      and into the cross-source equivalence item (`batch_live_symmetry` (k)). See the audit-instruction threading below.

## Success criterion

The gate catches an open-edge ingestion (planted-regression test fails); every pre-agg site converts to `t_close`; a
cross-source fixture proves tick-agg and pre-agg produce the same edge; the `features-*` corpus is right-edge on the
affected history (sample-verified). Re-running the bar-edge sweep finds zero open-edge consumed candles.

## Codex SSOT updates

- `codex/02-data/` bar-boundary / candle-edge convention doc — state the RIGHT-edge invariant + "never consume raw ohlcv
  directly; always the processed candle" + the gate's coverage (now incl. ingestion adapters). Write the stub if absent.
