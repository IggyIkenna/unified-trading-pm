---
doc_type: plan
title: DeFi protocol outage detector (R-NEW-6) — on-chain pause/freeze window detector populating PROTOCOL_PAUSE_WINDOWS
summary:
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: [/plans/archive/2026_05/defi_catalogue_chain_primitives_2026_05_10.md]
created: 2026-05-20
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: brand-new
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3
depends_on: [defi_catalogue_chain_primitives_2026_05_10]
parent_epic: defi_master
---

> **ARCHIVED 2026-05-21** — Phases 0-6 complete (Aave/Compound/Hyperliquid pause detection shipped, mtds@c9ff1f7 +
> uac@cc6a629). Phase 7.A (Curve emergency pause) DEFERRED-POST-CUTOVER; no further work needed before May-23. status:
> active → archived.

## Deferred work — migrated to:

| Item                                                                                     | Successor plan                                                                            |
| ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Phase 7.A — Curve emergency pause detection (Curve `kill_me()` kill-switch; POST-MAY-23) | Post-cutover DeFi hardening scope — no named active plan yet; tracked in `defi_master.md` |

# DeFi protocol outage detector (R-NEW-6)

> **Operator directive 2026-05-20 round 4**: "I can't just tell you when protocols are out — it needs to be understood
> from data. Isn't that something instruments-service can understand OR a script per chain which checks for outages
> using governance or otherwise?"
>
> **Decision**: detector-derived, not operator-typed. On-chain governance events
>
> - reserve configuration history = authoritative source. Registry stays empty until detector runs; honest default is
>   better than stale static dates.

## Why this plan exists

Mega-audit R-NEW-6 surfaced that `PROTOCOL_PAUSE_WINDOWS` in `unified_api_contracts/registry/protocol_pause_windows.py`
is empty — and must stay empty until a DETECTOR populates it. The detector reads existing on-chain data already captured
by MTDS (governance events / reserve config history) and computes `(start_date, end_date)` pairs for known protocol
pause periods.

Without this detector:

- `expected_coverage()` never fires `EXPECTED_PROTOCOL_PAUSED`
- Cells inside Aave V2 freeze windows show as `MISSING_EXPECTED` (false alarm)
- Cells inside Compound V2 pause windows show as `MISSING_EXPECTED` (false alarm)
- A2 audit re-run cannot verify "protocol pause = expected empty" classification

Known historical pauses (detector must surface these from on-chain evidence):

| Protocol    | Chain    | Asset      | Period                        | Source                                                             |
| ----------- | -------- | ---------- | ----------------------------- | ------------------------------------------------------------------ |
| AAVE_V2     | ETHEREUM | (all)      | 2023-Q1 onwards (per reserve) | LendingPoolConfigurator `ReserveConfigurationHistoryItem.isFrozen` |
| COMPOUND_V2 | ETHEREUM | (varies)   | 2023-2024 wind-down           | Comptroller `ActionPaused` events                                  |
| CURVE       | ETHEREUM | (specific) | 2023-07-30 → 2023-08-05       | Re-entrancy exploit emergency pause (Phase 2)                      |

## Architecture

```
On-chain sources (The Graph subgraphs)
         │
         ▼
┌────────────────────────────────────┐
│ ProtocolOutageDetectorHandler       │  MTDS handler (daily batch)
│ (market-tick-data-service)          │  operation: detect-protocol-outages
│                                    │
│  ┌──────────────────────────────┐  │
│  │ protocol_outage_adapter.py   │  │
│  │                              │  │
│  │ fetch_aave_v2_freeze_windows │  │  ReserveConfigurationHistoryItem
│  │   → Aave V2 Ethereum subgraph│  │  where isFrozen transitions
│  │                              │  │
│  │ fetch_compound_v2_pause_wins │  │  Comptroller ActionPaused events
│  │   → Compound V2 subgraph     │  │  where pauseState: true/false
│  └──────────────────────────────┘  │
│            │                       │
│            ▼                       │
│  Writes protocol_outages parquet   │
│  to GCS (data_type=protocol_outages│
│  venue=<PROTOCOL>-<CHAIN>)         │
└────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ refresh_protocol_pause_windows.py  │  Script (cron or post-batch)
│ (market-tick-data-service/scripts) │
│                                    │
│  Reads protocol_outages parquets   │
│  → aggregates (start, end) pairs   │
│  → refreshes UAC registry dict     │
└────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│ protocol_pause_windows.py (UAC)    │  Consumer-side cache
│ PROTOCOL_PAUSE_WINDOWS dict        │  read by expected_coverage() oracle
│ is_protocol_paused(proto,chain,dt) │
└────────────────────────────────────┘
```

## Encoding rules (HARD RULE for the detector)

Per `protocol_pause_windows.py` docstring:

- **Protocol pause** (Aave V2 freeze, Compound V2 wind-down, multi-day governance): Encode when **all three** conditions
  hold:
  1. On-chain governance event exists (ReserveFrozen / ActionPaused / PoolPaused)
  2. Pause lasted ≥ 24 hours (configurable, default 24h)
  3. End event observed OR pause extends past audit window (open-ended)
- **Chain-level outage** (Solana 2022-09-30, Arbitrum sequencer down): Do NOT encode — flag for operator review only.
  Too short; high false-positive.

## Phased execution DAG

```
Phase 1 (adapter)  →  Phase 2 (handler)  →  Phase 3 (CLI registration)
                                              ↓
                          Phase 4 (unit tests)  →  Phase 5 (QG + commit)
                                                       ↓
                                               Phase 6 (refresh script)
```

## Checkboxes

### Phase 1 — Protocol outage adapter

- [x] ✅ **[AGENT] P0. 1.A — Create `protocol_outage_adapter.py`** in
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/` with:
  - `ProtocolPauseWindow` dataclass — `(protocol, chain, asset, start_date, end_date | None)`
  - `fetch_aave_v2_freeze_windows(session, api_key, target_date)` — queries Aave V2 Ethereum subgraph for
    `reserveConfigurationHistoryItems` where `isFrozen` transitions; computes `(start_date, end_date)` per reserve;
    aggregates to protocol-wide window if ≥80% reserves frozen
  - `fetch_compound_v2_pause_windows(session, api_key)` — queries Compound V2 subgraph for `ActionPaused` entities;
    computes pause windows per market action type
  - `aggregate_protocol_windows(windows)` — deduplicates + merges overlapping windows per `(protocol, chain)` key;
    returns list ready for parquet write

### Phase 2 — MTDS handler

- [x] ✅ **[AGENT] P0. 2.A — Create `protocol_outage_detector_handler.py`** in
      `market-tick-data-service/market_tick_data_service/cli/handlers/` with:
  - Extends `UnifiedServiceHandler`
  - `preflight()` loads The Graph API key from Secret Manager
  - `process(payload)` calls adapter, writes `protocol_outages` data_type parquets to GCS path
    `raw_tick_data/by_date/day={date}/category=defi/venue={PROTOCOL}-{CHAIN}/ instrument_type=spot_asset/data_type=protocol_outages/ticks.parquet`
  - Writes manifest entry via `DefiManifestRecorder`

### Phase 3 — CLI registration

- [x] ✅ **[AGENT] P0. 3.A — Register `detect-protocol-outages`** in
      `market-tick-data-service/market_tick_data_service/cli/main.py` operation map
- [x] ✅ **[AGENT] P0. 3.B — Register `protocol_outages` data_type** in UAC
      `unified_api_contracts/internal/domain/defi/__init__.py` (or wherever `data_type` enums live)

### Phase 4 — Unit tests

- [x] ✅ **[AGENT] P0. 4.A — Unit tests** at
      `market-tick-data-service/tests/unit/handlers/test_protocol_outage_detector.py`:
  - `test_freeze_window_from_reserve_history` — assert window computed from isFrozen transitions
  - `test_ongoing_freeze` — end_date is None when no unfreeze event seen
  - `test_compound_pause_window` — ActionPaused True/False pair → window
  - `test_aggregate_overlapping_windows` — overlapping windows merged correctly
  - `test_empty_subgraph_response` — no windows returned gracefully

### Phase 5 — Quality gates + commit

- [x] ✅ **[AGENT] P0. 5.A — `bash scripts/quality-gates.sh`** in `market-tick-data-service` exit 0
- [x] ✅ **[AGENT] P0. 5.B — `bash scripts/quality-gates.sh`** in `unified-api-contracts` exit 0
- [x] ✅ **[AGENT] P0. 5.C — Commit + push** (Half-1: code; Half-2: plan flip; same agent turn) —
      market-tick-data-service@88c97b1 2026-05-20

### Phase 6 — Registry refresh script

- [x] ✅ **[AGENT] P1. 6.A — `refresh_protocol_pause_windows.py`** in
      `market-tick-data-service/market_tick_data_service/scripts/`:
  - Reads `protocol_outages` parquets from GCS for a date range
  - Aggregates `(protocol, chain) → list[(start_date, end_date)]`
  - Writes to `unified-api-contracts/unified_api_contracts/registry/data/protocol_pause_windows_cache.json`
  - `protocol_pause_windows.py` loads from the JSON cache at import time (falls back to empty)
  - UAC type updated: `list[tuple[date, date | None]]`; ongoing windows handled in `is_protocol_paused` —
    market-tick-data-service@c9ff1f7 + unified-api-contracts@cc6a629 2026-05-20

### Phase 7 — Curve pause detection (Phase 2 — requires direct RPC)

- [x] ✅ **POST-MAY-23 [AGENT] P1. 7.A** — Extend adapter with Curve emergency pause detection: **(DEFERRED-POST-CUTOVER
      — trivial-sweep 2026-05-21; named successor: reopen after May-23 cutover)**
  - Curve pools emit `RemoveLiquidityImbalance` + `kill_me()` administrative kill switch
  - Query Curve subgraph (`3fy93eAT56UJsRCEht8iFhfi6wjHWXtZ9dnnbQmvFopF` Ethereum) for `Pool.isKilled` state transitions
  - Known event: Curve 2023-07-30 re-entrancy exploit → pools killed for several days
  - Detector spot-check: `is_protocol_paused("CURVE", "ETHEREUM", date(2023, 7, 31))` → True

## Subgraph sources

| Protocol    | Chain    | Subgraph URL (hosted)                                               | Entity queried                          |
| ----------- | -------- | ------------------------------------------------------------------- | --------------------------------------- |
| AAVE_V2     | ETHEREUM | `https://api.thegraph.com/subgraphs/name/aave/protocol-v2`          | `reserveConfigurationHistoryItems`      |
| COMPOUND_V2 | ETHEREUM | `https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2` | Market entity `isActionPaused` / events |

Note: hosted service is legacy (TheGraph migration to decentralized ongoing). Add Gateway subgraph IDs to UAC
`SUBGRAPH_IDS` when decentralized versions are confirmed as equivalents. The plan will track the migration as a Phase 8
item.

## Success criteria

- `is_protocol_paused("AAVE_V2", "ETHEREUM", date(2023, 6, 15))` returns `(True, "<description>")` after Phase 6 refresh
  runs (Aave V2 started freezing reserves in Q1 2023)
- `is_protocol_paused("AAVE_V2", "ETHEREUM", date(2022, 1, 1))` returns `(False, None)` (pre-freeze period)
- `is_protocol_paused("COMPOUND_V2", "ETHEREUM", date(2024, 6, 1))` returns `(True, "<desc>")` (Compound V2 paused new
  borrowing 2023-2024 wind-down)
- A2 audit re-run: cells inside detector-confirmed windows → `EXPECTED_EMPTY[EXPECTED_PROTOCOL_PAUSED]` (reclassified
  from `MISSING_EXPECTED`)
- Detector spot-check Curve 2023-07-30: `(True, "CURVE-ETHEREUM paused 2023-07-30 → 2023-08-05")` after Phase 7 lands
