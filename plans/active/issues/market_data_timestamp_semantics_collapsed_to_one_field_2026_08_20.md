---
doc_type: issue
title: Live market-data ticks carry ONE overloaded timestamp — exchange time and local arrival time are the same column, meaning varies by adapter
summary: >-
  UAC mandates `["exchange_timestamp", "local_timestamp", "sequence_number"]` for MARKET_DATA events and the Tardis
  schemas define both, but the LIVE ingest path collapses them: `ReceivedTick` has a single `timestamp` field whose
  semantics depend on which adapter wrote it. Databento's exchange time is aliased INTO it via `_COLUMN_ALIASES`, while
  Binance-spot-book and Hyperliquid write `datetime.now(UTC)` arrival time into the same column. No local monotonic
  receive ORDER is captured anywhere, and no region tag exists. This blocks per-region replay, makes lookahead
  prevention unverifiable, and means cross-venue ordering cannot be reconstructed.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, market-data-processing-service]
scope: [engineer, admin]
tags: [mtds, timestamps, determinism, replay, ordering, lookahead, state-fabric]
related:
  [
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /plans/epics/system_readiness_master.md,
  ]
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/_ws_window_helpers.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py,
    unified-api-contracts/unified_api_contracts/internal/events.py,
    unified-api-contracts/unified_api_contracts/external/tardis/schemas.py,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P0
severity: P0
source: >-
  Sonnet-5 sub-agent measurement audit 2026-08-20. Surfaced after the operator correctly challenged an earlier
  orchestrating-session claim that no receive-time capture existed at all — that claim searched the wrong vocabulary
  and was wrong; the real defect is narrower and worse.
drift_direction: advance-code
depends_on: []
---

# One column, two meanings

## The correction that led here

The orchestrating session claimed 2026-08-20 that MTDS had no receive-time capture, having searched
`receive_time|recv_time|rx_time|local_receive`. **The operator challenged it** — the Tardis schema our ingestion was
based on carries exchange vs local timestamps. The operator was right. `local_timestamp` appears in **44 files** across
MTDS, MDPS and UAC, is defined five times in `unified_api_contracts/external/tardis/schemas.py` as "Local arrival
timestamp in microseconds", and `unified_api_contracts/internal/events.py:17` **mandates**
`["exchange_timestamp", "local_timestamp", "sequence_number"]` for every MARKET_DATA event.

The original claim was a search reported as a conclusion. The real defect is different and more specific.

## Measured 2026-08-20

**The contract has both fields. The live path has one.**

`ReceivedTick` (`market_tick_data_service/live/_ws_window_helpers.py`) is
`instrument_id, instrument_type, chain, timestamp, tick: dict[str, object]` — a **single** timestamp whose semantics
depend entirely on which adapter populated it:

| Adapter | What lands in `timestamp` |
| ------- | ------------------------- |
| Databento (tradfi) | **exchange event time** — `record.ts_event`, aliased in via `_COLUMN_ALIASES = {"ts_event": "timestamp", ...}` (`engine/orchestrator/symbol_rules.py:85`) |
| Binance spot book (cefi) | **local arrival time** — `datetime.now(UTC)` |
| Hyperliquid ticker (cefi) | **local arrival time** — asserted by `tests/unit/test_hyperliquid_ticker_ws_connector.py:58 test_timestamp_is_arrival_time` |

`_TICK_REQUIRED_COLUMNS` requires only `["timestamp", ...]` — nothing enforces which meaning it carries.

**This collision is already a known, named problem** in the codebase (`resolve_mtds_ts_event_timestamp_naming_collision`
referenced in `symbol_rules.py` comments). It was named and not closed.

**Also measured absent on the live tick path**, with the vocabulary that actually exists (`observed_at`, `captured_at`,
`observed_at_utc`, `local_ts`, plus the four original patterns — all searched):

- **Local monotonic receive ORDER** — zero hits. `time.monotonic()` is used only for rate-limiter and cache-TTL
  bookkeeping, never stamped on a tick.
- **Region** — no concept.
- **Normalizer version** — zero hits in MTDS, features-service or UAC.
- **Recovery/run epoch** — zero hits.
- **Persistence time per tick** — `available_at`/`period_end` exist only on the *window* envelope
  (`unified_api_contracts/events/persist.py:71-106`), never per tick.

Note: `observed_at_block` / `observed_at_utc` / `captured_at` DO exist — on the DeFi liquidation-candidate schema, the
DeFi aggregator-route parser and UTL position-reconciliation snapshots. **None is on the live WS tick path.** Separate
models, unrelated to this defect.

## Why it is P0

- **Per-region replay is impossible.** Ordering by "what this location could have known" requires knowing which
  timestamps are arrival times. Today that varies by adapter and is not recorded.
- **Lookahead prevention is unverifiable on the live path.** `PointInTimeEnforcer` guards reference data and
  feature-write boundaries, but a replay cannot prove no-lookahead if the ordering key's meaning is ambiguous.
- **Cross-venue ordering is unsound.** Sorting Databento (exchange time) against Binance (arrival time) in one
  sequence compares two different clocks as if they were one.
- **It silently looks fine.** Every tick has a timestamp; nothing errors. The ambiguity is invisible until someone
  tries to reconstruct an ordering and gets a plausible wrong answer.

## Todos

- [ ] [BACKEND] P0. **Split the field on the live tick model** — carry `exchange_timestamp` and `local_timestamp`
      separately, matching the contract `internal/events.py:17` already mandates and the Tardis schema already models.
      Neither may be defaulted from the other; an adapter that cannot supply exchange time must say so, not silently
      supply arrival time under that name.
- [ ] [BACKEND] P0. **Add local monotonic receive order** to the live tick model. Wall-clock arrival is not sufficient
      for ordering — two ticks in the same millisecond need a total order, and a stepped clock must not reorder them.
- [ ] [BACKEND] P0. **Add a region tag** to the tick or its envelope. Required by the per-region replay ruling.
- [x] ✅ [REVIEW] P1. **EXTRACTED 2026-08-21** — audit every connector (~65 files) for which timestamp meaning it
      writes today. Extracted to `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch
      (na-eligibility-audit, cross-cutting tranche, batch 2 of 3).
- [x] ✅ [REVIEW] P1. **EXTRACTED 2026-08-21** — close or supersede `resolve_mtds_ts_event_timestamp_naming_collision`.
      Extracted to `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch (na-eligibility-audit,
      cross-cutting tranche, batch 2 of 3).
- [ ] [BACKEND] P2. **Add normalizer version and recovery epoch** to the canonical envelope, so a replay can tell
      which code produced a stored event.

## Findings — full connector timestamp-semantics audit (2026-08-21)

Audited all 65 files in `market_tick_data_service/live/connectors/` (excludes the 3 underscore-prefixed shared bases
— `_defi_ws_blocked_credentials_base.py`, `_onchain_liquidation_poller.py`, `_subgraph_polling_connector.py` — which
are not themselves registered connectors). Method: `rg -n "timestamp\s*="` + `rg -n "^\s*(ts|now|tick_ts)\s*="` across
the directory to find every `ReceivedTick(...timestamp=...)` construction site and its variable's derivation, then
read each helper function (`_parse_ts`/`_parse_msg_ts`/`_ts_from_iso`) and each BLOCKED-* scaffold's header in full.
A file that subclasses/retags another already-classified connector's tick (e.g. `okx_spot_ws.py` retagging
`okx_ws.py`'s output) inherits that connector's classification rather than being independently re-derived.

**Legend**: `exchange (fallback)` = primary path parses an exchange-supplied timestamp field, falls back to
`datetime.now(UTC)` only on a missing/unparseable field. `arrival` = always `datetime.now(UTC)`, no exchange field
ever consulted. `mixed` = the file has two distinct tick-emission paths with different semantics. `scaffold (N/A)` =
`BLOCKED-CREDENTIALS`/`BLOCKED-BUILD`/`BLOCKED-UPSTREAM-OUTAGE` stub with no live `stream()` body — no tick is ever
emitted today, so no timestamp semantic exists to classify yet.

**exchange (fallback)** — 37 files: `aave_liquidations_ethereum_ws.py` (on-chain event time via ISO parse),
`aster_book_liq_ws.py` (retags `binance_futures_ws`/`binance_futures_book_ticker_ws`), `binance_futures_ws.py`,
`binance_futures_book_ticker_ws.py`, `binance_spot_ws.py` (retags `binance_futures_ws`), `bitfinex_futures_ws.py`
(subclasses `bitfinex_spot_ws`), `bitfinex_spot_ws.py`, `bitget_futures_ws.py` (subclasses `bitget_spot_ws`),
`bitget_spot_ws.py`, `bybit_ws.py`, `bybit_futures_book_ticker_ws.py`, `bybit_spot_ws.py` (retags `bybit_ws`),
`coinbase_cde_ws.py` (ISO `raw_time`), `coinbase_spot_ws.py` (ISO `raw_time`), `databento_tradfi_ws.py` (`ts_event`,
already known), `deribit_ws.py`, `deribit_book_ticker_ws.py`, `hyperliquid_ws.py` (`ts_ms`), `hyperliquid_l2book_ws.py`,
`kalshi_ws.py` (`ts_ms`→`ts_s`→now 3-tier), `kalshi_clob_ws.py` (`_parse_ts`), `kalshi_perp_ws.py`,
`kalshi_trades_ws.py` (`_parse_ts`), `kraken_futures_ws.py`, `kraken_futures_book_ticker_ws.py`, `kraken_spot_ws.py`
(ISO `raw_ts`), `okx_ws.py`, `okx_futures_ws.py`, `okx_futures_book_ticker_ws.py`, `okx_spot_ws.py` (retags `okx_ws`),
`okx_spot_book_ws.py` (retags `okx_futures_book_ticker_ws`), `pacifica_solana_perp_ws.py`, `polymarket_clob_ws.py`
(`_parse_msg_ts`, epoch), `polymarket_trades_ws.py` (`_parse_msg_ts`), `tardis_machine_ws.py` (`_ts_from_iso`, tardis's
own ISO ts), `upbit_book_ws.py`, `upbit_spot_ws.py`.

**arrival (always `datetime.now(UTC)`)** — 11 files: `binance_spot_book_ws.py` (depth/book-snapshot builder called
with `datetime.now(UTC)` unconditionally — the vendor gives no per-snapshot exchange ts), `coinbase_book_ws.py` (same
shape), `hyperliquid_ticker_ws.py` (already known, `test_timestamp_is_arrival_time` confirms), `jito_defi_ws.py`,
`jupiter_solana_ws.py`, `morpho_defi_ws.py`, `odds_api_ws.py`, `orca_defi_ws.py`, `phoenix_ws.py`, `polymarket_ws.py`
(the base WS ticker path — distinct from `polymarket_clob_ws.py`/`polymarket_trades_ws.py`, which DO parse an exchange
ts), `raydium_defi_ws.py`.

**mixed (two distinct emission paths)** — 2 files: `curve_defi_ws.py` (one path emits `now` i.e. arrival, a second
emits `tick_ts` derived from an on-chain `ts_unix` with arrival fallback — needs code-owner input on which path is
live/primary), `dex_swap_uniswap_v3_ws.py` (same shape: one `tick_ts`-from-block-time path, one plain `now` path).

**scaffold (N/A — no live emission yet)** — 15 files, all header-confirmed `BLOCKED-CREDENTIALS` /
`BLOCKED-BUILD` / `BLOCKED-UPSTREAM-OUTAGE`: `betfair_ws.py`, `coinbase_intx_ws.py`, `defi_lending_scaffold_ws.py`,
`dex_swap_scaffold_ws.py`, `eigenlayer_ethereum_ws.py`, `ethena_ethereum_ws.py`, `etherfi_ethereum_ws.py`,
`extended_starknet_perp_ws.py`, `fluid_ethereum_ws.py`, `kamino_solana_ws.py`, `lido_ethereum_ws.py`,
`lighter_zksync_perp_ws.py`, `marinade_solana_ws.py`, `polymarket_perp_ws.py` (BLOCKED-UPSTREAM-OUTAGE, not
credentials), `spark_ethereum_ws.py`.

37 + 11 + 2 + 15 = 65, matching this todo's own "~65 connector files" estimate exactly. No file was left
unclassified. This confirms and generalizes the doc's original dozen-file sample (Databento/exchange, Binance-spot-
book/Hyperliquid-ticker/arrival): the arrival-time failure mode is not confined to those two — it recurs across every
book-snapshot/depth-rebuild connector (no per-update exchange ts exists to carry) and every DeFi/on-chain poller that
doesn't parse the underlying chain event's own timestamp. The P0 schema-split todo above must account for `mixed`
connectors needing a per-path decision, not just a per-file one.

## Findings — `resolve_mtds_ts_event_timestamp_naming_collision` disposition (2026-08-21)

Batch21 item (`cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md`), source: this doc's "Close or supersede
`resolve_mtds_ts_event_timestamp_naming_collision`" todo. **Verdict: PARTIALLY LANDED, THEN REVERTED — the collision is
live again today, in the exact form this parent issue's audit measured.** Not descoped (no deliberate decision to
abandon it) and not forgotten (it's narrated in the current code comments) — it shipped a real fix, which was reverted
5 days later as a hotfix for a regression the fix itself caused, and never re-attempted.

**Method**: found the reference (`market_tick_data_service/engine/orchestrator/symbol_rules.py:70,127` +
`tests/unit/test_symbol_rules_column_aliases.py:18`), then walked full git history via
`git log --all -S"resolve_mtds_ts_event_timestamp_naming_collision"` / `git log -S"_COLUMN_ALIASES"` on
`market-tick-data-service`.

**Timeline** (all commits on `market-tick-data-service`):

1. **2026-08-05, `5efc76cc`** ("dual-write ts_event alongside timestamp in `_apply_column_aliases`") — Phase-1: a
   compatibility copy, `ts_event → timestamp`, added to `_COLUMN_ALIASES`.
2. **2026-08-05, `79c2e961`** ("remove ts_event→timestamp column alias (Phase 4)") — **this is
   `resolve_mtds_ts_event_timestamp_naming_collision`'s actual fix landing**: the alias/copy was removed, so
   Databento's `ts_event` (exchange time) stopped being silently duplicated under the generic `timestamp` name.
3. **2026-08-10, `dcd3b7c4`** ("restore ts_event→timestamp alias copy — unblock VIX/CBOE ohlcv_1m schema
   validation") — **5 days later, Phase-4's removal was REVERTED.** Root cause (per the now-archived
   `plans/archive/issues/tradfi_vix_backfill_launch_failed_2026_08_10.md` todo 1, resolved by this exact commit):
   removing the alias broke `_TICK_REQUIRED_COLUMNS["ohlcv_1m"]` validation for VIX/CBOE (XCBF.PITCH) writes —
   `Schema validation FAILED: missing columns=['timestamp']` on every chunk — because the ohlcv_1m validator and the
   pre-2026-08-05 on-disk corpus both hard-depend on a `timestamp` column existing. The revert restores the dual-write
   copy (current code, `symbol_rules.py:84-88` `_COLUMN_ALIASES = {"ts_event": "timestamp", ...}`), now framed
   explicitly as intentional ("a COPY, not a rename") rather than an oversight.
4. **2026-08-10, `8c46c456`** ("accept Databento-native ts_event as time column in `_validate_tick_schema`") —
   companion fix, same incident.

**Current state, confirmed by direct read of `symbol_rules.py:64-141` (2026-08-21)**: the alias/copy is live. Every
Databento tick still gets `ts_event`'s exchange-time value duplicated verbatim into the generic `timestamp` column —
the identical "one column, two meanings" shape this parent issue documents for the live tick path (`ReceivedTick`),
just on the write-time/schema-validation side rather than the live-ingest side. No follow-up re-attempt of Phase-4 has
been filed or landed since 2026-08-10.

**Implication for the P0 schema-split todos above**: they must not assume Phase-4's prior work is still in effect —
it isn't. The planned fix (first-class, separately-named `exchange_timestamp`/`local_timestamp` fields) is a different
and more correct approach than Phase-4's narrower alias-removal, but it repeats Phase-4's exact failure mode if it
removes/repoints `timestamp` without migrating `_TICK_REQUIRED_COLUMNS`'s ohlcv_1m entry and the pre-2026-08-05
on-disk corpus readers in the SAME change — that is precisely what triggered the 2026-08-10 incident and forced the
revert. Treat "does anything still validate against a bare `timestamp` column for ohlcv_1m" as a required check before
shipping the split, not an afterthought.

## Progress Log

**2026-08-20 — filed.** No code touched. Filed after an operator correction to an orchestrating-session claim; the
correction narrowed the finding from "no receive-time capture" (wrong) to "one overloaded field with adapter-dependent
semantics" (measured). The corrected claim is worse than the original, because a missing field fails loudly on first
use while an ambiguous one does not fail at all.

- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries); all paths re-verified on disk,
  unchanged.
- **na-eligibility-audit 2026-08-21**: RECLASSIFY (per-todo split) — 2 of 6 open todos are pure investigation
  tasks with no design call. Extracted to `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md`. The 3 P0
  schema/engineering todos and the P2 envelope extension stay `assigned_vm: NA` — a real, correctness-critical
  live-schema change across ~65 connector files needing genuine design judgment. Doc's own `assigned_vm: NA`
  unchanged. Cross-cutting tranche, batch 2 of 3.
- **2026-08-21 (slot-16)** — Closed the extracted connector-audit todo (`cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md`
  item under "From `market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md`"). Added the "Findings —
  full connector timestamp-semantics audit" section above: all 65 connector files classified (37 exchange-time w/
  arrival fallback, 11 pure arrival-time, 2 mixed-path, 15 BLOCKED-* scaffolds with no live emission). Pure
  classification, no schema change made.
