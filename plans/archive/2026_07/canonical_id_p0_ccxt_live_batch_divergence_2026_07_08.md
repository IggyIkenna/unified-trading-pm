---
doc_type: plan
title: Fix CCXT live-mode instrument_id divergence — 13 major CeFi venues get a structurally different id live vs batch
summary: >-
  instruments-service's CCXTReferenceDataAdapter stores instrument_key as the bare, unmodified ccxt-native market symbol
  (e.g. "BTC/USDT", "BTC/USDT:USDT") with zero canonicalization — this is the live-mode route for 13 canonical venues
  (BINANCE-SPOT/-FUTURES, BYBIT(+SPOT/FUTURES), OKX(+SPOT/SWAP/FUTURES), DERIBIT, COINBASE-SPOT, UPBIT,
  KRAKEN-SPOT/-FUTURES). Batch mode (Tardis) produces a differently-shaped canonical id for the same real instrument. A
  direct live=batch determinism violation on this workspace's most heavily-traded CeFi venues.
status: complete
nature: notes
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [instrument-id, live-vs-batch, determinism, bug-fix, p0, ccxt]
related:
  [
    ../audit/results/canonical_instrument_id_audit_2026_07_08.md,
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
created: 2026-07-08
last_updated: 2026-07-10 # (was: 2026-07-08 -- corrected 2026-07-12, finding 24, §A2 B-queue ruling: Progress Log records a 2026-07-10 status-flip active->complete that postdated the recorded last_updated)
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  "Canonical instrument-id audit, 2026-07-08 (canonical_instrument_id_audit_2026_07_08.md, finding #4), cross-referenced
  under batch_live_symmetry_master per operator decision (2026-07-08) to track under existing epics rather than a new
  one, since this is precisely that epics scope: per-service batch=live audit + reconciliation."
---

> **Direct violation of a core workspace invariant** — paper(W) must equal batch-rerun(W) trade-for-trade. If the same
> real instrument has two different ids depending on capture mode, nothing downstream can reconcile live vs batch data
> for it without a lossy manual join.

## Root cause

`instruments_service/reference_data/adapters/cefi/ccxt_adapter.py:156-157` (`_parse_ccxt_market`) builds
`InstrumentRecord(instrument_key=symbol, ...)` where `symbol` is the raw ccxt unified market symbol verbatim
(`"BTC/USDT"` spot, `"BTC/USDT:USDT"` perp, `"BTC/USDT:USDT-250328"` future) — never passed through
`canonical_id_builder.build_instrument_id()` or given any `VENUE:TYPE:` structure. This adapter is the live-mode route
for 13 canonical venues per `factory.py`'s `_CANONICAL_VENUE_TO_CCXT_EXCHANGE` (routed from `factory.py:95-114,383-398`
and `router.py:193-197,290-307`): `BINANCE-SPOT`, `BINANCE-FUTURES`, `BYBIT`/`-SPOT`/`-FUTURES`, `OKX`/`-SPOT`/`-SWAP`/
`-FUTURES`, `DERIBIT`, `COINBASE-SPOT`, `UPBIT`, `KRAKEN-SPOT`, `KRAKEN-FUTURES`. Batch mode for the same venues goes
through Tardis, which (per this session's earlier real-catalog reads) produces properly dash-cleaned canonical ids for
most of these (e.g. `BYBIT:PERPETUAL:BTC-USDT`).

## Todos

- [x] [DATA] P0. **Route `CCXTReferenceDataAdapter`'s instrument_key construction through the same canonicalization path
      batch mode uses** — the target isn't necessarily `canonical_id_builder.py` itself (per the audit, that module is
      barely used in practice) but whatever real logic produces the correct batch-mode ids for these same 13 venues, so
      live and batch converge on an identical id for the identical instrument. — instruments-service@8544273d + evidence
      below.
- [x] [VERIFY] P0. **Confirm convergence for all 13 venues** — for at least one real instrument per venue, confirm the
      live-mode CCXT-derived id now matches the real batch-mode (Tardis) id exactly. — instruments-service@8544273d +
      evidence below (real GCS/API reads, all 13 venues MATCH).
- [x] [VERIFY] P1. **Check every real consumer of CCXT-adapter instrument_ids** (strategy-service's reconciliation
      engine, per `canonical_id_p0_strategy_reconciliation_2026_07_08.md`, is one confirmed consumer) — changing this id
      shape is a breaking change for anything that persisted or compared against the OLD raw ccxt-symbol shape. —
      findings below; corrective, not breaking, for every real consumer found.
- [x] [SCRIPT] P1. **Ship via quickmerge**, quality-gates green. Coordinate with
      `canonical_id_p0_strategy_reconciliation_2026_07_08.md` since fixing this is a prerequisite for that plan's
      reconciliation-engine fix to actually work end-to-end. — instruments-service@8544273d, quickmerge landed on
      live-defi-rollout, QG green (exit 0).

## Progress Log

- **2026-07-10** — **Status-flip note**: all 4 todos confirmed `[x]` with cited evidence (fix shipped, all 13 venues
  verified converged against real GCS/API reads, consumer-impact check done, QG green). Flipped `status: active` →
  `complete`.
- **2026-07-08** — Filed from the canonical instrument-id audit's P0 finding #4. Root cause + affected venue list
  confirmed via direct code reads. No fix applied yet.
- **2026-07-08** — **Fixed + shipped.** `instruments-service@8544273d67f2865151ce0aec8e03e2b51ba37397`
  (`fix(cefi): route CCXT live-mode instrument_key through Tardis-matching VENUE:TYPE:SYMBOL construction`).

  **Fix**: `ccxt_adapter.py`'s `CCXTReferenceDataAdapter` gained `_build_instrument_key()`, which mirrors
  `TardisReferenceDataAdapter._parse_tardis_instrument`'s construction (the REAL batch-mode logic for these 13 venues —
  NOT `canonical_id_builder.build_instrument_id`, which the audit correctly flagged as barely used and which would
  reconstruct FUTURE/OPTION ids from expiry/strike/right rather than passing through the raw exchange-native id like
  Tardis does): `VENUE:TYPE:BASE-QUOTE` for SPOT_PAIR/PERPETUAL (reconstructed from ccxt's own `base`/`quote` market
  fields, matching Tardis's `f"{base}-{quote}"`), `VENUE:TYPE:RAW_SYMBOL` for FUTURE/OPTION (ccxt's exchange native
  `market['id']`, upper-cased, matching Tardis's `raw_id.upper()` verbatim passthrough). Also added
  `_resolve_instrument_key_venue()`: a handful of UAC-registered canonical venues (`BYBIT-FUTURES`) are aliases that
  resolve to the SAME underlying Tardis exchange as a "primary" venue (`BYBIT`) — Tardis's own parser always tags such
  batch-mode records with the PRIMARY venue token, so the CCXT-side VENUE token now resolves through the same
  `VenueMapping.tardis_to_venue` lookup for byte-identical convergence on those aliases too.

  **Per-venue verification (real GCS/Tardis-API + live CCXT-API reads, one real instrument per venue, old id vs new id
  vs real batch-mode id)** — all 13 canonical venues converge exactly:

  | Venue           | Sample instrument (base/quote or raw)         | OLD ccxt instrument_key (pre-fix, no VENUE:TYPE prefix) | NEW ccxt instrument_key                                           | REAL Tardis instrument_key           | Match                                     |
  | --------------- | --------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------ | ----------------------------------------- |
  | BINANCE-SPOT    | BTC/USDT                                      | `BTCUSDT` (raw ccxt symbol, unstructured)               | `BINANCE-SPOT:SPOT_PAIR:BTC-USDT`                                 | `BINANCE-SPOT:SPOT_PAIR:BTC-USDT`    | ✅                                        |
  | BINANCE-FUTURES | BTC/USDT perp                                 | `BTC/USDT:USDT`                                         | `BINANCE-FUTURES:PERPETUAL:BTC-USDT`                              | `BINANCE-FUTURES:PERPETUAL:BTC-USDT` | ✅                                        |
  | BYBIT           | 0G/USDT perp                                  | `0G/USDT:USDT`                                          | `BYBIT:PERPETUAL:0G-USDT`                                         | `BYBIT:PERPETUAL:0G-USDT`            | ✅                                        |
  | BYBIT-SPOT      | BTC/USDT                                      | `BTCUSDT`                                               | `BYBIT-SPOT:SPOT_PAIR:BTC-USDT`                                   | `BYBIT-SPOT:SPOT_PAIR:BTC-USDT`      | ✅                                        |
  | BYBIT-FUTURES   | BTCUSDT-10JUL26 (dated)                       | `BTCUSDT-10JUL26` (raw, no venue/type)                  | `BYBIT:FUTURE:BTCUSDT-10JUL26`                                    | `BYBIT:FUTURE:BTCUSDT-10JUL26`       | ✅ (alias→primary venue-token resolution) |
  | OKX-SPOT        | BTC/USD                                       | `BTC/USD`                                               | `OKX-SPOT:SPOT_PAIR:BTC-USD`                                      | `OKX-SPOT:SPOT_PAIR:BTC-USD`         | ✅                                        |
  | OKX-SWAP        | BTC/USD:USD                                   | `BTC/USD:USD`                                           | `OKX-SWAP:PERPETUAL:BTC-USD`                                      | `OKX-SWAP:PERPETUAL:BTC-USD`         | ✅                                        |
  | OKX-FUTURES     | BTC-USD-260710 (dated)                        | `BTC/USD:USD-260710`                                    | `OKX-FUTURES:FUTURE:BTC-USD-260710`                               | `OKX-FUTURES:FUTURE:BTC-USD-260710`  | ✅                                        |
  | DERIBIT         | ADA_USDC-PERPETUAL; BTC-9JUL26-56000-C option | `ADA_USDC:USDC-PERPETUAL`; raw option symbol            | `DERIBIT:PERPETUAL:ADA-USDC`; `DERIBIT:OPTION:BTC-9JUL26-56000-C` | same                                 | ✅ (perp + option both verified)          |
  | COINBASE-SPOT   | BTC/USD                                       | `BTC/USD`                                               | `COINBASE-SPOT:SPOT_PAIR:BTC-USD`                                 | `COINBASE-SPOT:SPOT_PAIR:BTC-USD`    | ✅                                        |
  | UPBIT           | WAXP/KRW                                      | `WAXP/KRW`                                              | `UPBIT:SPOT_PAIR:WAXP-KRW`                                        | `UPBIT:SPOT_PAIR:WAXP-KRW`           | ✅                                        |
  | KRAKEN-SPOT     | 0G/USD                                        | `0G/USD`                                                | `KRAKEN-SPOT:SPOT_PAIR:0G-USD`                                    | `KRAKEN-SPOT:SPOT_PAIR:0G-USD`       | ✅                                        |
  | KRAKEN-FUTURES  | PI_XBTUSD perp                                | `BTC/USD:BTC`                                           | `KRAKEN-FUTURES:PERPETUAL:BTC-USD`                                | `KRAKEN-FUTURES:PERPETUAL:BTC-USD`   | ✅                                        |

  Bare `OKX` (a legacy UAC-registered alias distinct from `OKX-SPOT`) was checked too:
  `VenueMapping. get_tardis_exchange_for_venue("OKX")` returns `None`, so
  `factory.get_adapter_for_canonical_venue("OKX", mode="batch")` raises `ValueError` in production — it has no live
  batch-mode counterpart to converge with, so it is correctly left unresolved (passthrough) rather than silently
  remapped.

  **Consumer-impact findings** (sub-agent research, cross-workspace grep): no consumer found that parses the OLD bare
  ccxt-symbol shape — the OPPOSITE is true: strategy-service (`risk_monitor.py:387-393`,
  `exit_playbook_executor. py:339-341`, `settlement_service.py:545`, `pnl_monitor.py:129`, `exposure_monitor.py:113`,
  `grid_generator. py:234`), execution-service (`instrument_resolver.py`, `dataframe_preparers.py:267,297`,
  `multi_leg_config_gcs.py`), features-service/ml-service (`data_loader.py`, `feature_query_support.py:149`), and MTDS
  live connectors (`bybit_ws.py:44-48`) all already assume the `VENUE:TYPE:SYMBOL` (≥3 colon-parts) shape — this fix is
  corrective for all of them, not breaking. instruments-service's own test suite (`test_coverage_gaps_adapters.py`,
  `test_cefi_tradfi_comprehensive.py`) passes raw ccxt strings only as lookup-key _arguments_, never asserts
  `instrument_key` equals the old bare shape — no test breakage confirmed (and QG ran green).
  `strategy-service/strategy_service/position/core/reconciliation_engine.py:178` does a bare equality join with no
  transform on either side (no double-transform risk from this fix), but its `ex_pos["instrument"]` side is populated
  independently by strategy-service's OWN position-query adapters
  (`position_interface/adapters/{ccxt.py:101, binance.py:124, bybit.py:103}`), which build ids straight from the raw
  exchange REST response, bypassing instruments-service entirely — **this fix alone does NOT close that reconciliation
  gap**; the companion plan `canonical_id_p0_strategy_reconciliation_2026_07_08.md`'s own P0 todo (fixing those
  position-query adapters) is still required and unblocked by this landing. **Residual/unconfirmed**:
  instruments-service's reference-data GCS write path (`process_write.py` / `writers.py`) unconditionally stamps
  `pipeline_mode=BATCH_INSTRUMENTS_SERVICE` regardless of the `--mode` CLI flag (no live-mode partition exists for CeFi
  reference-data persistence) — so IF `--mode live` reference-data fetches for these 13 venues were ever historically
  persisted to `instrument_availability/by_date/day=.../venue=.../instruments.parquet`, that day's file would carry the
  OLD bare-symbol shape until the next capture for that same (venue, date) overwrites it. Could not confirm from static
  code whether `--mode live` CeFi reference-data capture has ever actually been scheduled in production (the only
  confirmed `--mode live` CeFi production usage found is MTDS's unrelated websocket-streaming tick-data VM, not
  instruments-service reference-data) — flagging as a low-confidence, self-healing-on-recapture residual risk rather
  than a blocker.

  **QG**: `bash scripts/quality-gates.sh --no-fix` → exit 0, sentinel `.qg_last_passed_sha` == HEAD (`4b4185b6`) before
  ship. Shipped commit: `instruments-service@8544273d67f2865151ce0aec8e03e2b51ba37397`, landed on `live-defi-rollout`
  via quickmerge (Tier-C drain promotes LDR→staging within ~15min).
