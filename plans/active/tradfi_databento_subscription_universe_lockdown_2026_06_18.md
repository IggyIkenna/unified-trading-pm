---
title: TradFi Databento subscription-universe lockdown + billing-safety guards
created: 2026-06-18
parent_epic: tradfi_master
assigned_vm: vm-tradfi
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-06-18
---

# TradFi Databento subscription-universe lockdown + billing-safety guards

## Context

Operator (2026-06-18) committed to **exactly three** Databento datasets — `GLBX.MDP3`, `DBEQ.BASIC` (US Equities), `CFE`
(VIX/VX futures) — and to ingesting **only the free included-history schemas**. Querying anything outside the
subscription is billed pay-as-you-go (metered). We must (a) lock the universe, (b) fetch `ohlcv-1s` + `ohlcv-1m` for
OHLCV (both L0/free) and aggregate coarser bars (15m/1h/24h) downstream, (c) enforce per-level rolling-history floors
(L0 16y / L1 1y / L2+L3 1mo), and (d) hard-block `batch.submit_job` (streaming/live only) so we are never billed
silently.

**Scope note — the guards gate DATABENTO requests ONLY.** They do NOT touch stored data, the manifest/data-status, the
candle aggregator, or any non-Databento source. Barchart/Yahoo VIX `ohlcv_15m` is a DIFFERENT source — the Databento
guards never run on it, `ohlcv_15m`/`ohlcv_24h` remain registered TradFi data_types, and nothing deletes stored rows
(see "Out of scope" below + the codex SSOT "VIX" section).

**Codex SSOT:** `codex/02-data/tradfi-databento-sourcing-ssot.md`. **Contract module:**
`unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py`.

## Shipped 2026-06-18 (this session)

- [x] [UAC] P0. Contract module `databento_subscription_allowlist.py` — dataset allowlist, schema→level map, per-level
      lookback floors, `batch.submit_job` ban, `assert_*` guards (fail-closed). Exported from
      `unified_api_contracts.registry`. Smoke-tested (all allowed/blocked paths + enum-repr normalization).
- [x] [UAC] P0. `market_data_categories.py` — added `ohlcv_1s` as a TradFi `data_type` (base granularity `1s`,
      `needs_candle_processing=True`, `TIMEFRAME_SECONDS["1s"]=1`).
- [x] [MTDS] P0. Wired guards in market-tick-data-service: `_resolve_databento_schema` (schema allowlist),
      `_fetch_timeseries_range` (`assert_databento_request_allowed` at the get_range chokepoint), `submit_batch_job`
      (hard block).
- [x] [DOCS] P0. Codex SSOT `tradfi-databento-sourcing-ssot.md` + CLAUDE.md one-liner.
- [x] [UAC] P0. Event contracts (operator 2026-06-18): `("tradfi","event_contract")` validity matrix admits
      `{trades, ohlcv_1s, ohlcv_1m, tbbo}` (CME `EC*` series on GLBX.MDP3 — covered by the existing subscription, no new
      dataset).
- [x] [UAC/MTDS] P0. OHLCV scope = `ohlcv-1s` **AND** `ohlcv-1m` (operator 2026-06-18; revises the earlier 1s-only).
      Both are L0/free 16y. 1m kept to complete the large existing 1m corpus (exercises migration/manifest/data-status);
      1s is the finer add. `_BANNED_OHLCV_SCHEMAS` now = `{ohlcv-1h, ohlcv-1d}` only; schema_map fetches both 1s+1m.

## Phase 1 — add the ohlcv-1s fetch + 1s aggregation (NON-breaking: 1m stays)

> NOT a breaking cutover — `ohlcv_1m` remains an allowed fetch schema, so the existing 1m pipeline keeps running. 1s is
> purely additive (a new, slower backfill alongside the 1m completion).

- [ ] [MTDS] P0. Add an `ohlcv_1s` fetch request alongside the existing `ohlcv_1m` in the orchestrator/adapter request
      path (`market_interface/adapters/tradfi/`, `engine/orchestrator/venue_fetch.py`). Repo: market-tick-data-service.
- [ ] [MDPS] P1. Aggregate `ohlcv_15m` / `ohlcv_24h` from `ohlcv_1m` (already the base) and optionally re-derive 1m from
      1s for cross-check. Verify NaN/session-grid finalization at both 1s and 1m base. Repo:
      market-data-processing-service.
- [ ] [DATA] P1. Backfill: complete the `ohlcv_1m` corpus first (good test of migration/manifest/data-status), then run
      the longer `ohlcv_1s` backfill. Manifest-verified rows + sample-inspected parquets per Plans-Run-To-Completion.
- [x] [UAC] P1. SOURCE_PRIORITY: add `("tradfi","ohlcv_1s")` entry in `canonical/crosscutting/_source_priority_data.py`
      (mirrors `ohlcv_1m` = `["massive","databento"]`) + matching `("tradfi","ohlcv_1s")` in `availability_semantics.py`
      (`tick_timestamp`, required by the closed-set round-trip test). — unified-api-contracts@3b76c0bc | QG green.
      **Operator decision still open:** Databento is now a paid subscription — keep the ratified massive-first ordering
      or flip to databento-first for tradfi? Default = mirror `ohlcv_1m` ordering until operator rules. Repo:
      unified-api-contracts.

## Phase 2 — prune the instrument universe to the 3 datasets

- [ ] [UAC] P0. Drop ICE-only instruments from `registry/tradfi_instrument_universe.py`: Brent (`BRN`), Gasoil (`G`),
      ICE Dollar Index (`DX`), softs (`CT`/`CC`/`KC`/`SB`/`OJ`) — and remove `IFEU.IMPACT` / `IFUS.IMPACT` datasets.
      Repo: unified-api-contracts.
- [ ] [UAC] P0. Consolidate equity ETFs/stocks onto `DBEQ.BASIC` (currently ETFs on `XNAS.ITCH`); drop the per-venue
      equity datasets. Repo: unified-api-contracts.
- [ ] [UAC] P0. Wire `CFE` dataset + VX (VIX) futures instruments into `tradfi_instrument_universe.py` and the live-ws
      venue→dataset map (`live/connectors/databento_tradfi_ws.py`, currently `IFEU.IMPACT`/per-venue equities). Repo:
      market-tick-data-service + unified-api-contracts.
- [ ] [UAC] P1. Remove `ICE` from `VENUES_BY_ASSET_GROUP["tradfi"]`; add a `CFE`/Cboe venue if VX futures need a
      distinct venue token. Repo: unified-api-contracts.
- [ ] [UAC] P1. Verify the CME event contracts (`EC*` series: ECES/ECNQ/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECBTC) in
      `tradfi_instrument_universe.py` survive the prune, stay on `GLBX.MDP3`, and are tagged `event_contract` (not bare
      `option`) so the validity matrix admits `{trades, ohlcv_1s, tbbo}`. Repo: unified-api-contracts.

## Phase 3 — enforcement + tests + codex alignment

- [ ] [UAC] P1. Unit tests for `databento_subscription_allowlist` (allowed/blocked dataset, banned OHLCV schema,
      per-level lookback floor boundaries, batch ban, break-glass, enum-repr normalization). Repo:
      unified-api-contracts.
- [ ] [PM] P1. QG grep-ratchet: no raw `batch.submit_job` call outside the guarded `submit_batch_job`; no off-allowlist
      dataset string literal in tradfi fetch paths. Wire into market-tick-data-service `quality-gates.sh`. Repo: PM +
      market-tick-data-service.
- [x] [DOCS] P2. Update `codex/02-data/tradfi-data-types-catalog.md` to reflect **1m+1s** OHLCV (added `ohlcv_1s` row +
      the "OHLCV fetch = 1m AND 1s" note; CFE/VX-futures venue). — unified-trading-pm (this commit). **Still open:**
      `codex/04-architecture/tradfi-batch-live.md` (3-dataset universe + CFE) — pairs with the Phase-2 universe prune.
      Repo: unified-trading-pm.

## Out of scope / explicit non-goals

- **VIX 15m cash index gap** stays Barchart+Yahoo — `CFE` provides VX **futures**, not the cash index at 15m
  (`registry/data_source_continuity.py` unchanged).
- ICE / OPRA / EEX / Eurex subscriptions — re-add only on an explicit operator subscription decision.

## Codex SSOT updates

- `codex/02-data/tradfi-databento-sourcing-ssot.md` (NEW — authoritative).
- `codex/02-data/tradfi-data-types-catalog.md` (Phase 3 — reflect **1m+1s** OHLCV — DONE: `ohlcv_1s` row + OHLCV note).
- `codex/04-architecture/tradfi-batch-live.md` (Phase 3 — reflect 3-dataset + CFE).
