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
