---
doc_type: plan
title: ── Architectural context ───────────────────────────────────────────────────
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

---

name: universe-ssot-fix overview: Phase B architectural drift fix. instruments-service must be the SSOT for every
venue's instrument universe across all 5 categories. No MTDS adapter should discover symbols / markets at download time
— every adapter reads the pre-written instruments.parquet from GCS. Filters (UAC capability_declarations +
service_config) apply ON TOP of the full universe to produce the MVP subset; they do not replace universe discovery.
Coverage = fetched / filtered_universe → honest 100% even when the filter is small. type: mixed epic:
epic-data-platform-honest-coverage status: active

locked_by: live-defi-rollout locked_since: 2026-04-21

completion_gates: code: C5 deployment: D3 business: B3

depends_on:

- smoke_dep_chain_tactical_fixes_2026_04_20

# ── Architectural context ───────────────────────────────────────────────────

#

# Canonical design: instruments-service discovers universe ONCE per date per

# venue, writes instruments.parquet to GCS. Every downstream (MTDS, features,

# strategy, execution) reads that parquet. Filters from UAC registry +

# service_config constrain the MVP universe post-read.

#

# Current drift (as of 2026-04-20 canary):

# \* CEFI/Tardis venues → CORRECT (BINANCE-FUTURES/Bybit/etc. read via URDI)

# \* TradFi/Databento (CME, NASDAQ) → DRIFTED: MTDS reads UAC registry inline

# \* Hyperliquid/Aster → DRIFTED: hardcoded SYMBOL arrays in MTDS adapter

# \* Polymarket → DRIFTED: MTDS calls `/markets` API at download time

# \* Kalshi → DRIFTED: MTDS calls `/markets` API at download time

# \* DeFi standard ticks → mixed (lending_indices reads on-chain directly; pool

# swaps need instruments-service universe)

# \* Sports bookmakers → DRIFTED: adapters poll odds API `/sports` at runtime

# \* Sports fixtures → CORRECT (instruments-service writes via api-football)

#

# `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT` frozenset in

# market-tick-data-service/market_tick_data_service/engine/orchestrator.py

# documents the drift — only CEFI-via-Tardis + DeFi venues are in the set.

# All others skip pre-flight because they source universe elsewhere.

#

# After this plan: every venue goes through the pre-flight. The frozenset

# becomes "all venues" (or is deleted).

#

# Filters (NOT touched by this plan, already correct):

# \* UAC `capability_declarations` for TradFi (still the canonical filter)

# \* service_config mvp_symbols / mvp_markets allowlists

# \* Applied AFTER loading instruments.parquet, BEFORE fetching ticks

# \* Unchanged — still produce the MVP subset

todos:

# ─── Phase B1 — TradFi/Databento ──────────────────────────────────────────

- id: phase-b1-tradfi-urdi-adapter content: |
  - [ ] [AGENT] P0. Add `instruments-service/instruments_service/reference_data/adapters/tradfi/databento_adapter.py`
        that discovers TradFi instruments for (date, venue) and emits `list[InstrumentRecord]`. Source: Databento
        Definitions API (`/v0/metadata.list_symbols` or `batch.list_jobs` — whichever is canonical per their docs).
        Venues covered: CME, NASDAQ, NYSE, plus any others in UAC TradFi registry. Respect UAC capability_declarations
        as filter: fetch full universe, filter to capability-declared subset. Honour IS_TEST_RUN (write to -test-
        bucket). Emit `instruments.parquet` at the canonical path:
        `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet` (matches CEFI layout per
        /codex/02-data/per-category-bucket-layouts.md). status: pending

- id: phase-b1-tradfi-mtds-read content: |
  - [ ] [AGENT] P0. Update MTDS Databento adapter
        (`market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py`) to read the symbol universe
        from
        `gs://instruments-store-tradfi-{bucket-suffix}/instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`
        via `get_write_bucket_name("instruments", "tradfi")` (IS_TEST_RUN-aware). Apply UAC capability_declarations
        filter IN MEMORY after the read — filters produce the MVP subset. Delete the existing inline UAC registry walk —
        it's no longer the runtime source of truth, only the upstream for instruments-service. status: pending

# ─── Phase B2 — Hyperliquid / Aster ────────────────────────────────────────

- id: phase-b2-hyperliquid-urdi content: |
  - [ ] [AGENT] P0. Add `instruments-service/.../reference_data/adapters/cefi/hyperliquid_adapter.py` +
        `aster_adapter.py` that call each venue's perpetual-listing API (`/info` on Hyperliquid, `/api/v1/exchangeInfo`
        on Aster) and emit `list[InstrumentRecord]` for each active perp. Write same canonical path as BINANCE-FUTURES.
        Honour IS_TEST_RUN. status: pending

- id: phase-b2-hyperliquid-mtds-read content: |
  - [ ] [AGENT] P0. Delete hardcoded `SYMBOLS_HYPERLIQUID` + `SYMBOLS_ASTER` arrays from MTDS. Make Hyperliquid/Aster
        adapters read the universe from GCS via `get_write_bucket_name("instruments", "cefi")`. Apply filter (UAC or
        service_config) post-read. Add venues to `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT` (or see phase-b6 for total
        removal). status: pending

# ─── Phase B3 — Polymarket ─────────────────────────────────────────────────

- id: phase-b3-polymarket-urdi content: |
  - [ ] [AGENT] P0. Add `instruments-service/.../reference_data/adapters/prediction/polymarket_adapter.py` that calls
        Polymarket `/markets` and `/books` once per date, emits `list[InstrumentRecord]` with
        instrument_type=PREDICTION_BINARY, instrument_key=`POLYMARKET:prediction_binary:{condition_id}`,
        `available_from/to_datetime` from market's start/end_time. Output path differs per
        per-category-bucket-layouts.md: PREDICTION uses
        `instrument_availability/by_date/day={date}/venue=POLYMARKET/instruments.parquet` (same shape as CEFI — `venue=`
        partition — despite MTDS tick path having `instrument_type=` level). status: pending

- id: phase-b3-polymarket-mtds-read content: |
  - [ ] [AGENT] P0. Update MTDS Polymarket adapter
        (`market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py`) to read universe from
        GCS instead of calling `/markets`. Delete the `/markets` + `/books` calls from the download path — move them to
        instruments-service only. Filter via service_config mvp allowlist if present. Coverage = fetched /
        (filtered_universe ∩ live_market_set). status: pending

# ─── Phase B4 — Kalshi ─────────────────────────────────────────────────────

- id: phase-b4-kalshi-urdi content: |
  - [ ] [AGENT] P0. Add `instruments-service/.../reference_data/adapters/prediction/kalshi_adapter.py` that calls Kalshi
        `/markets` once per date, emits InstrumentRecord[] at canonical path (same as Polymarket). status: pending

- id: phase-b4-kalshi-mtds-read content: |
  - [ ] [AGENT] P0. Update MTDS Kalshi adapter to read universe from GCS. Delete `/markets` call. Filter via
        service_config. status: pending

# ─── Phase B5 — Sports bookmakers ──────────────────────────────────────────

- id: phase-b5-sports-bookmakers-urdi content: |
  - [ ] [AGENT] P0. Extend sports reference pipeline to write a
        `sports_reference/by_date/day={date}/entity=bookmakers/bookmakers.parquet` artefact listing the bookmaker
        universe per date (bookie_id, name, supported_sports, supported_markets, in_play_capable, territory). Source:
        Odds-API `/sports` + `/sports/{sport}/bookmakers`, plus static registry for OB-only bookmakers like SFI/Betfair.
        Every bookie returned becomes an InstrumentRecord with instrument_type=BOOKMAKER. status: pending

- id: phase-b5-sports-adapters-read content: |
  - [ ] [AGENT] P0. Update MTDS + features-sports-service sports adapters to read the bookmaker universe from the new
        `entity=bookmakers/` parquet. Delete inline `/sports` + `/bookmakers` API polls from MTDS Odds-API adapter + ATP
        bookmaker-selection logic. status: pending

# ─── Phase B6 — Remove the bypass allowlist ────────────────────────────────

- id: phase-b6-remove-preflight-bypass content: |
  - [ ] [AGENT] P1. In `market-tick-data-service/market_tick_data_service/engine/orchestrator.py`, remove
        `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT` frozenset. Every venue now needs pre-flight. Convert
        `_check_instruments_available` to run unconditionally per-venue; fail loud when instruments.parquet is missing
        (no more silent skip). Per-shard isolation still applies — a single missing venue doesn't block others. status:
        pending note: "Do this AFTER B1-B5 so pre-flight doesn't fail for venues whose universe isn't yet written."

# ─── Phase B7 — DeFi pool/swap universe (follow-up) ────────────────────────

- id: phase-b7-defi-pool-universe content: |
  - [ ] [AGENT] P1. DeFi standard ticks (Uniswap swaps, AAVE positions per pool) need a per-chain pool universe written
        by instruments-service. Currently `lending_indices` reads on-chain directly — that's fine for aggregate rates,
        but pool-level tick data needs a canonical pool list. Add `urdi.defi_pool_adapter` that walks chain-specific DEX
        factories + AAVE/Compound address books (already in UAC + UCI registry), writes instruments.parquet with
        instrument_type=POOL / LENDING / A_TOKEN. status: pending

# ─── Phase B8 — Filters live in UAC + service_config (audit only) ──────────

- id: phase-b8-filter-audit content: |
  - [ ] [AGENT] P2. Audit all filter application sites to confirm they run AFTER universe load, not IN the adapter.
        Expected sites: UAC `capability_declarations` checks, service_config mvp_symbols / mvp_markets. Document the
        canonical filter application pattern in `/codex/02-data/universe-and-filter-model.md` (new doc): 1.
        instruments-service writes full universe (instruments.parquet) 2. MTDS loads instruments.parquet 3. MTDS applies
        capability_declarations + service_config filter 4. MTDS fetches ticks for filtered subset 5. Coverage = fetched
        / filtered_universe (honest 100% possible) status: pending

# ─── Phase B9 — Verify dep chain post-fix ──────────────────────────────────

- id: phase-b9-verify-all-5-categories content: |
  - [ ] [OPERATOR] P0. Post-B1..B7, re-run dep-chain smoke for all 5 categories on VMs. Each cell: Tier-0 writes
        universe → Tier-1 reads universe → ticks land. Verify via gsutil + manifest-row
        `capture_status=captured|empty_confirmed`. Expected outcome: zero "NO INSTRUMENTS FOUND" errors for ANY venue in
        ANY category. 100% honest coverage reported by MTDS manifest for the filtered MVP universe. status: pending

# ── Success criteria ────────────────────────────────────────────────────────

# Phase B is green when:

# - `_VENUES_NEEDING_INSTRUMENT_PREFLIGHT` is empty (or deleted) — every venue

# goes through the instruments.parquet read

# - Zero runtime API calls for universe discovery in any MTDS adapter

# (external venue APIs only fetch TICK data, not symbol/market lists)

# - instruments-service writes instruments.parquet for every (date, venue)

# combination across all 5 categories

# - MTDS pre-flight passes for all 5 category × representative-venue canary

# runs on VMs

# - /codex/02-data/universe-and-filter-model.md documents the pattern

# ── Out of scope (NOT this plan) ─────────────────────────────────────────────

# - Changing filter semantics (filters stay in UAC + service_config as-is)

# - Adding new categories (5-category model unchanged)

# - Changing the test-bucket convention (settled by tactical-fixes plan)

# - Features/strategy/execution universe reads (they're already correct —

# only MTDS has the drift)
