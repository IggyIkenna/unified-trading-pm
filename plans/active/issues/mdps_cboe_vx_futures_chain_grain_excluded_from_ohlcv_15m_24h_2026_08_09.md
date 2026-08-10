---
doc_type: issue
title:
  CBOE VX-futures ohlcv_1m→ohlcv_15m/24h aggregator (batch9 todo 2) is blocked by the 2026-08-06 default ruling that
  excludes ALL `instrument_type=futures_chain`/`combo` from coarse-timeframe requests — that ruling's own premise ("no
  downstream consumer expects combo-grain 15m/24h candles") is now false for CBOE/VIX specifically
summary: >-
  Dispatched to build `tradfi_satellite_ao_dispatch_batch9_2026_08_09.md` todo 2 (RULED 2026-08-07: build an MDPS-owned
  `ohlcv_1m`→`ohlcv_15m`/`ohlcv_24h` aggregator for CBOE VX-futures, general-purpose, feeding `vix_features`'s
  `ohlcv_15m` required-input). Static-code + live read-only research (a sub-agent queried the real
  `market-data-tick-tradfi-prd-*` availability manifest) found the underlying aggregation MECHANISM already exists and
  is PROVEN working end-to-end for CME/NASDAQ/NYSE (`mdps-backfill-tradfi-20260803-104812`: 99,711 real candles, 788
  captured manifest rows) — `TradfiOhlcv15mAdapter`/`TradfiOhlcv24hAdapter`'s `related_data_types` fix
  (`market-data-processing-service@0671953`) and the UAC `ohlcv_24h` alias fix (`unified-api-contracts@079d48ff`) both
  already ship. So this todo is NOT "genuinely new build" as its own text framed it — EXCEPT for one real, CBOE-specific
  blocker: CBOE VX-futures raw `ohlcv_1m`/`ohlcv_1s` ticks are captured ONLY at `instrument_type=futures_chain` grain
  (2,942 captured rows, 2020-06-01→2026-08-06, confirmed live on GCS), never at the per-contract `future` leaf grain UAC
  allows `ohlcv_15m`/`ohlcv_24h` for. `orchestration_scanner.py`'s `_INSTRUMENT_TYPES_EXCLUDED_FROM_COARSE_TIMEFRAMES =
  frozenset({"combo","futures_chain"})` (`market-data-processing-service@68f95f6`, shipped 2026-08-06 — 3 days before
  batch9's ruling — specifically to stop a CME calendar-spread/combo crash) silently drops every CBOE blob before it
  ever reaches the adapter whenever the requested `data_type` is `ohlcv_15m`/`ohlcv_24h`. That fix's own text justified
  the exclusion as "verified no downstream consumer expects combo-grain 15m/24h candles" — a premise the very next day's
  operator ruling (2026-08-07, vix_features/delta-one need exactly `ohlcv_15m`/`ohlcv_24h` sourced from CBOE's
  futures_chain-grain raw data) makes FALSE specifically for CBOE/VIX. Resolving this needs an owner/operator call on
  which fix path — it is the same shape of judgment call the sibling issue doc already flagged `[OPERATOR]` for the CME
  combo case (fix the CLI/orchestration scoping vs. catch-and-degrade the write path), now recurring for a second,
  narrower (CBOE/VIX-only) case with an opposite desired outcome (ENABLE it here, not exclude it). NOT something a
  single bounded worker todo should resolve unilaterally — a wrong choice risks either silently reopening the CME crash
  this exclusion was built to close, or shipping incorrect/misattributed shard identity for a bundle-grain candle write
  (see "Why it matters").
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-data-processing-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags:
  [tradfi, mdps, cboe, vix, ohlcv_15m, ohlcv_24h, futures_chain, combo, honest-absence, policy-conflict, vix_features]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09_finalize.md,
    /plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md,
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
  ]
created: "2026-08-09"
author: slot-28 (backend_engineer)
parent_epic: instruments_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source:
  [
    tradfi_satellite_ao_dispatch_batch9-29d3d0bec9b3 (slot-28 dispatch),
    live read-only GCS query of
    gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet,
  ]
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md,
    market-data-processing-service/market_data_processing_service/app/core/orchestration_scanner.py,
    market-data-processing-service/market_data_processing_service/app/adapters/tradfi/ohlcv_passthrough.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
depends_on: []
---

# What I found

Dispatched as `tradfi_satellite_ao_dispatch_batch9_2026_08_09.md` todo 2 ([BACKEND] P2, RULED 2026-08-07: "YES, build
it, MDPS-owned... aggregate `ohlcv_1m` up to `ohlcv_15m`/`ohlcv_24h` once, upstream of every consumer... Scope to CBOE
VX-futures only for the first cut"). Before writing code, verified the todo's own premise ("the existing
`TradfiOhlcv15mAdapter`/`GranularityDetector`... are bare passthroughs/labelers, NOT resamplers, so this is genuinely
new build") against the current code + a live, read-only GCS query.

**1. The aggregation mechanism already exists and is proven working, contrary to the todo's framing.**
`TradfiOhlcvPassthroughAdapter.process_to_candles` (`ohlcv_passthrough.py:190-231`) already performs genuine OHLC
bucketing (`open=first, high=max, low=min, close=last, volume=sum`) whenever multiple finer-grain source rows map into
one coarser grid slot — not a pure 1:1 passthrough despite the class name.
`TradfiOhlcv15mAdapter`/`TradfiOhlcv24hAdapter` both declare `related_data_types: list[str] = ["ohlcv_1m", "ohlcv_1s"]`
(shipped `market-data-processing-service@0671953`, 2026-08-03), which lets raw `ohlcv_1m`/`ohlcv_1s` reach this adapter
for `ohlcv_15m`/`ohlcv_24h` output requests. A live verification VM run (`mdps-backfill-tradfi-20260803-104812`,
documented in `/plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`) already proved this
exact mechanism end-to-end: **99,711 real candles, 788 real `captured` manifest rows** for CME/NASDAQ/NYSE
`future`/`equity` (non-combo) instrument_types. The UAC `ohlcv_24h` daily-alias SchemaContract fix
(`unified-api-contracts@079d48ff`) also already ships for `future`/`equity`/`options_chain`/`index`. So a brand-new
aggregator is NOT what's missing.

**2. CBOE VX-futures raw capture sits at exactly the grain a separate, deliberate policy excludes.** A read-only query
of the real `market-data-tick-tradfi-prd-central-element-323112` bucket's `_index/availability_index.parquet` (7,024,311
rows) found: `venue=CBOE`, `data_type∈{ohlcv_1m,ohlcv_1s}`, `capture_status=captured` → **2,942 rows,
2020-06-01→2026-08-06**, under `instrument_type=futures_chain` (confirmed live on GCS for `day=2026-08-06`: both real
CBOE blobs that day sit at `.../venue=CBOE/instrument_type=futures_chain/data_type=ohlcv_1m|1s/underlying=VIX/...`).
Zero `captured` rows exist at `instrument_type=future` (the per-contract leaf grain) for CBOE ohlcv_1m/1s.

`unified_api_contracts.registry.market_data_categories.VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("tradfi", "futures_chain")]`
is `{"trades","ohlcv_1s","ohlcv_1m","tbbo"}` — deliberately excluding `ohlcv_15m`/`ohlcv_24h` (mirrors the `combo`
entry, same comment: "Kept tight... to avoid over-fanning cells the writer never captures").
`market_data_processing_service/app/core/orchestration_scanner.py`'s
`_INSTRUMENT_TYPES_EXCLUDED_FROM_COARSE_TIMEFRAMES = frozenset({"combo","futures_chain"})` (lines ~53-63, applied at
~570-577 and ~838-841) enforces this at the orchestration/scan layer: any blob under `instrument_type=futures_chain/` or
`instrument_type=combo/` is skipped up-front whenever the requested `data_type` is `ohlcv_15m`/`ohlcv_24h`. This was
shipped `market-data-processing-service@68f95f6` on **2026-08-06** — 3 days before batch9's 2026-08-07 ruling —
specifically to stop CME calendar-spread/combo shard writes crashing with "No SchemaContract registered" (documented in
`/plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`, the `[x]` ✅ "DEFAULT-RULED
2026-08-06, option (a)" todo). Its own justification: **"verified no downstream consumer... expects combo-grain 15m/24h
candles to exist."**

**3. That justification is now false, specifically and narrowly for CBOE/VIX.** The very next day's operator ruling
(source doc for this batch: `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`, "RULED
2026-08-07 — YES, build it") explicitly wants `ohlcv_15m` to feed `vix_features`'s
`unified_api_contracts.canonical.domain.features.required_inputs` entry
(`InputReq(asset_group="tradfi", data_type="ohlcv_15m", ...)`), and `ohlcv_24h` to feed delta-one groups — sourced from
EXACTLY the futures_chain-grain raw data the 2026-08-06 exclusion was built to silence. A real downstream consumer for
combo/futures_chain-grain coarse candles does now exist — just for CBOE specifically, not for CME calendar-spread combos
generally.

# Why it matters

Two live operator-adjacent rulings now point in opposite directions over the identical code path
(`_INSTRUMENT_TYPES_EXCLUDED_FROM_COARSE_TIMEFRAMES`), and resolving the conflict wrong has real failure modes on either
side:

- **Blindly removing `futures_chain` from the exclusion set** would re-open the exact CME combo crash ("No
  SchemaContract registered", 432/813 errors in the 2026-08-03 re-run) the 2026-08-06 fix was shipped to close — a
  straight regression of an already-fixed, already-verified-live incident.
- **Building a bundle-grain-aware writer for CBOE specifically** (the narrower, correct-looking fix) still needs a real
  shard-identity decision the sibling issue doc's own `[OPERATOR]` todo explicitly left open for the combo case: what
  does "instrument_id" mean for a `futures_chain`/`underlying=VIX` bundle producing a single `ohlcv_15m`/`ohlcv_24h` row
  — the CME combo crash's root cause was exactly this ("`symbols_processed=0`... the helper correctly declines a
  per-shard row without a valid shard identity"). The manifest's OWN captured rows for CBOE ohlcv_1m/1s show
  `instrument_id=CBOE:FUTURE:VIX` (a `FUTURE`-shaped id) even though the GCS path segment is
  `instrument_type=futures_chain` — worth resolving carefully (which field is the source of truth for downstream
  consumers) rather than guessing.
- Per workspace CLAUDE.md "Data pipeline correctness is the heartbeat" + "a todo is AO-eligible only if its outcome is
  DETERMINABLE by the worker alone... NEVER an open-ended judgment/design call" — this is a genuine architecture call
  (narrow-carve-out vs. re-derive-at-leaf-grain vs. something else), not a bounded, worker-determinable outcome. Per
  `backend_engineer.md`: "If you surface an unknown the plan didn't anticipate... file an issue doc + escalate — do not
  absorb unplanned scope."

# Recommended decision

Two candidate fixes (mirroring the sibling issue doc's own framing for the analogous combo case), scoped NARROWLY to
CBOE/VIX so the CME combo exclusion stays intact:

**(a) Extend a CBOE/VIX-scoped carve-out** in `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` and
`_INSTRUMENT_TYPES_EXCLUDED_FROM_COARSE_TIMEFRAMES` (or a new, more granular exclusion keyed on
`(venue, instrument_type)` rather than `instrument_type` alone) so `futures_chain` stays excluded for CME
combo/calendar-spreads but is admitted for CBOE `underlying=VIX` specifically — then build the bundle-aware
manifest-write path (resolving the shard-identity question above) so a real `ohlcv_15m`/`ohlcv_24h` row lands under a
well-defined `instrument_id`. Recommended: this is what the 2026-08-07 ruling's "MDPS-owned... general-purpose" framing
actually intends, and keeps the fix's blast radius narrow (CBOE/VIX only, not a blanket futures_chain re-enable).

**(b) Re-derive CBOE VX capture at the leaf `future` grain instead** (the grain UAC already fully allows
`ohlcv_15m`/`ohlcv_24h` for, no exclusion-policy change needed) — would require the tick-capture/write layer (likely
market-tick-data-service, not MDPS) to additionally emit or re-key per-contract VX futures ticks at
`instrument_type=future`, a bigger and more invasive change outside this todo's stated MDPS-only repo scope.

## Todos

- [ ] [OPERATOR] P2. **Decide between option (a) and (b) above** (or propose a third path) for unblocking CBOE
      VX-futures `ohlcv_15m`/`ohlcv_24h` aggregation without reopening the CME combo/`SchemaContractNotFoundError` crash
      `market-data-processing-service@68f95f6` was shipped to close. Once decided, re-scope
      `tradfi_satellite_ao_dispatch_batch9_2026_08_09.md` todo 2 (or a fresh satellite-batch todo) to the concrete
      implementation path chosen. Repo: unified-trading-pm (decision) + market-data-processing-service +
      unified-api-contracts (implementation once decided). Done when: the operator/owner has picked (a), (b), or a third
      option, and a properly-scoped follow-up todo exists citing this doc.

# Progress Log

- 2026-08-09 (slot-28, backend_engineer): dispatched `tradfi_satellite_ao_dispatch_batch9_2026_08_09.md` todo 2.
  Static-code read + a read-only sub-agent GCS query of the live tradfi manifest found the aggregation mechanism already
  ships and is proven live for CME/NASDAQ/NYSE, but CBOE VX-futures raw capture sits entirely at
  `instrument_type=futures_chain` grain, which a separate 2026-08-06 default ruling
  (`market-data-processing-service@68f95f6`) deliberately excludes from `ohlcv_15m`/`ohlcv_24h` requests — a policy
  conflict with this todo's 2026-08-07 ruling, not a bounded implementation gap. Filed this issue doc rather than absorb
  the unplanned architecture-judgment scope; batch9 todo 2 left `- [ ]` (NOT flipped) pending the operator decision
  above.
