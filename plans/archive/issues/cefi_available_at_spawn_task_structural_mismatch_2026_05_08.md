---
doc_type: issue
title:
  Tab F2 CeFi `available_at` spawn task structurally blocked — adapter file layout + UTL helper + UAC SOURCE_PRIORITY
  shape don't match the spec
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
author: cefi-available-at-stamping-tab
source:
  - {
      unified-trading-pm/plans/archive/work_split_2026_05_08_ikenna.md (§ "Spawn prompts — fresh fan-out:
        'instruments-service + MTDS", Tab F2 entry)',
    }
  - unified-trading-pm/plans/epics/cefi_master_2026_05_07.md (§ "`available_at` adapter stamping (coordinated)" lines
    380-396 + new § "Open questions" Q1)
  - unified-trading-pm/plans/archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md (Phase 1 P0 "CeFi
    adapter stamping" todo)
  - market-tick-data-service/market_tick_data_service/adapters/ (only 2 files, NOT 10 venue-shaped)
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/ (5 source-shaped, NOT 10
    venue-shaped)
  - unified-trading-library/unified_trading_library/availability_stamping.py (5 sports-shaped helpers; no
    `stamp_available_at_cefi_tick`)
  - {
      "unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py:84 (`SOURCE_PRIORITY":
        "dict[tuple[str, str], list[str]]` — no latency field)",
    }
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Tab F2 CeFi `available_at` spawn task structurally blocked

> **Status**: ✅ RESOLVED 2026-05-09 by UAC@e197173 (`EMISSION_LATENCY_MS_BY_SOURCE`) + UTL@29555212
> (`stamp_available_at_cefi_tick`) + MTDS@4a00bd5 (PartitionedTickWriter writer-boundary stamping). The reshape
> recommended below was applied: not 10 per-venue commits but a single writer-boundary integration in
> `PartitionedTickWriter.write_chunk` that stamps
> `available_at = timestamp + emission_latency_ms_for_source(primary_source)` for cefi shards before the parquet lands
> on disk. Primary source resolved per UAC `SOURCE_PRIORITY[("cefi", data_type)]` (Tardis canonical = 50ms). 5 unit
> tests at `market-tick-data-service/tests/unit/test_partitioned_writer_cefi_available_at.py`. Bar-data stamping still
> depends on Phase 0 MDPS bar-boundary contract. Plan checkbox flipped at
> `plans/active/available_at_lookahead_bias_completion_2026_05_08.md` Phase 1 P0 CeFi adapter stamping.

> **Severity**: P0 — multi-day shape mismatch; Tab F2 cannot ship as scoped. **Blast radius**: 3 repos (UAC
> `SOURCE_PRIORITY` shape extension + UTL `availability_stamping` cefi-tick helper + MTDS multi-callsite stamping
> wiring); changes the daily work-split (Tab F2 cannot produce 10 per-venue commits); contradicts the master plan's CeFi
> adapter file premise. **Suggested owner**: operator triage — collision with Tab 2 LIVE-PIPELINE (writegate Phase
> 2.D) + Tab F1 (master gate A.10 UTL helper). Probably absorbs into the
> [`available_at_lookahead_bias_completion_2026_05_08`](../available_at_lookahead_bias_completion_2026_05_08.md) Phase 1
> P0 todo with reshaped per-callsite (not per-venue) execution.

## What I found

The Tab F2 spawn prompt directs the agent to:

1. Edit "every CeFi adapter file at `market-tick-data-service/market_tick_data_service/adapters/{venue}.py`" across 10
   venues (bybit / binance / okx / deribit / kraken / bitfinex / bitget / coinbase / gate / kucoin).
2. Add `df["available_at"] = stamp_available_at_cefi_tick(df["timestamp"], venue, data_type)` using a UTL helper from
   `unified_trading_library.availability_stamping`.
3. Stamp via the formula `available_at = tick_ts + emission_latency_ms` per UAC SOURCE_PRIORITY top entry.
4. Ship 10 commits (1 per venue) + 10 unit tests.

**Probe results 2026-05-08 (before any code edit)**:

### Fact 1: per-venue adapter files don't exist

```
$ ls market-tick-data-service/market_tick_data_service/adapters/
hyperliquid_s3.py
umi_tick_provider.py
__pycache__
```

The CeFi venues are routed through `market_interface/adapters/cefi/`:

```
$ ls market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/
__init__.py
ccxt_adapter.py            # source-shape (covers many venues via ccxt unified API)
databento_mbo_adapter.py   # source-shape (Databento order-book channel)
l2_book_state.py           # state machine, not an adapter
tardis_incremental_book_adapter.py
tardis_shared.py
upbit_adapter.py           # the only venue-shaped file (upbit needs venue-native REST, not ccxt)
```

There are **5 source-shaped adapters** (ccxt / databento / tardis / upbit / shared), not **10 venue-shaped adapters**.

### Fact 2: `stamp_available_at_cefi_tick` does not exist

```
$ ls unified-trading-library/unified_trading_library/availability_stamping*
unified-trading-library/unified_trading_library/availability_stamping.py    # SINGLE FILE, not a package
```

The module exports (lines 257-267):

```python
__all__ = [
    "AVAILABLE_AT_COL",
    "DEFAULT_MATCH_DURATION",
    "LINEUPS_PRE_KICKOFF_OFFSET",
    "AvailableAtStampingError",
    "stamp_available_at_event_time",
    "stamp_available_at_explicit",
    "stamp_available_at_lineups",
    "stamp_available_at_offset",
    "stamp_available_at_post_match",
]
```

All 5 helpers are sports-shaped (lineups / event_time / post_match / offset / explicit). **No CeFi/DeFi/TradFi
tick-shape helper exists.** This is the gating UTL helper the Tab F2 prompt's PRE-REQ GATE explicitly cites — it has not
been shipped.

### Fact 3: `SOURCE_PRIORITY` doesn't carry latency

```
unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py:84

SOURCE_PRIORITY: Final[dict[tuple[str, str], list[str]]] = {
    ...
}
```

The value type is `list[str]` — just source-name strings, top-entry-only per Phase 1B convention. **There is no
per-source `emission_latency_ms` / `scrape_latency` field.** The formula `tick_ts + source_priority_scrape_latency` that
both the spawn prompt and the plan-of-record cite cannot be evaluated against the current UAC shape — UAC needs the
field added (cross-cutting design call = Ikenna-side per work-split principle) before any adapter can stamp via this
rule.

The plan-of-record
[`available_at_lookahead_bias_completion_2026_05_08`](../available_at_lookahead_bias_completion_2026_05_08.md) Phase 1
P0 todo `**CeFi adapter stamping**` (line 260) cites the same formula:
`available_at = tick_timestamp + source_priority_scrape_latency per UAC SOURCE_PRIORITY`. This todo is **also
structurally blocked** until the UAC field lands.

### Fact 4: `record_captured` callsites are in handlers, not per-venue files

```
$ grep -rn "record_captured(" market-tick-data-service/market_tick_data_service/ --include="*.py"
```

returns 27+ callsites, almost all in `cli/handlers/*.py`:

- DeFi: `lst_rates_handler.py:480`, `perp_funding_handler.py:245`, `dex_swaps_handler.py:377`,
  `oracle_prices_handler.py:650+677`, `liquidations_handler.py:297`, `flash_loan_events_handler.py:141`,
  `bridge_events_handler.py:142`, `token_transfers_handler.py:187`, `staking_yields_handler.py:115+160+205`,
  `eigenlayer_rewards_handler.py:181`, `gas_fee_handler.py:219+252+285`, `liquidation_events_handler.py:153`,
  `dex_pools_handler.py:374`, `governance_events_handler.py:124`, `lending_indices_handler.py:350`,
  `vault_share_price_handler.py:481`, `solana_defi_handler.py:225`, plus `_defi_manifest.py:120`
- Generic: `position_data_handler.py:124+171`

CeFi bar-shaped writes flow through `engine/orchestrator.py:1940` per writegate plan Phase 2.B Option α refactor —
itself listed as PENDING under Tab 2 LIVE-PIPELINE 2026-05-08 evening DONE block in
[`live_pipeline_mtds_mdps_features_2026_05_08`](../live_pipeline_mtds_mdps_features_2026_05_08.md). There is no 1:1
`(venue, data_type) -> single record_captured callsite` mapping to wrap with a per-venue stamping call.

Sample CeFi-relevant callsite (perp_funding_handler.py:245) — note the absence of any `available_at` stamping in scope:

```python
total_written += written
if written > 0:
    recorder.record_captured(
        venue=protocol,
        chain=chain_for_manifest,
        data_type=_PERP_FUNDING_DATA_TYPE,
        row_count=written,
        instrument_type="perpetual",
        attempted_at=attempted_at,
    )
```

## Why it matters

- **Tab F2 cannot ship as scoped.** 10 per-venue commits cannot be created against files that don't exist. The DONE
  block + plan-flip cadence the spawn prompt requires has no shippable atom under the current shape.
- **The plan-of-record itself is partially structurally blocked.** Phase 1 P0 CeFi/DeFi/TradFi/Predictions adapter
  stamping todos in `available_at_lookahead_bias_completion_2026_05_08.md` all cite
  `tick_timestamp + source_priority_scrape_latency per UAC SOURCE_PRIORITY` — this only works once UAC SOURCE_PRIORITY
  gains the `emission_latency_ms` field.
- **Order-of-ops dependency**: master-gate `[A.10]` UTL `stamp_available_at_cefi_tick` helper MUST ship before any
  per-callsite wiring. Per CLAUDE.md "Live = batch — same data, same fields, same timing semantics, different sources
  OK" rule, the helper signature is the SSOT — wiring at the writer boundary is mechanical once the helper + UAC field
  exist.
- **Collision risk with Tab 2 LIVE-PIPELINE.** writegate Phase 2.B Option α (orchestrator refactor to use
  `record_captured`) is listed as `helper-shipped` deferred-after-features-consolidation in the 2026-05-08 PM/evening
  Tab 2 DONE block. A naive "wrap every record_captured callsite with a stamp" sweep would collide with that refactor's
  writer-boundary changes.

## Recommended decision

The Tab F2 task should reshape from **per-venue files** to **per-callsite at the writer boundary**, AND should be
sequenced behind the three master-gate items:

1. **UAC `SOURCE_PRIORITY` shape extension** (Ikenna-side, cross-cutting design): extend the registry value type to
   carry per-source `emission_latency_ms` (or equivalent named field) so live-mode emission timing is deterministically
   stampable from the canonical historical source. Per CLAUDE.md "Live = batch" rule the latency must reflect what the
   live pipeline would have observed for that source, not the historical archive's slower lag.
2. **UTL `stamp_available_at_cefi_tick(df, *, timestamp_col, venue, data_type)` helper** (Harsh-side once design is
   pinned): mirror sports helper shape but consume the new SOURCE_PRIORITY field for the per-(venue, data_type) latency
   lookup. Empty df pass-through + `AvailableAtStampingError` on missing column / all-NaT, like the existing sports
   helpers.
3. **Per-callsite wiring** at the writer atomicity boundary (Harsh-side, mechanical implement-from-spec): walk every
   CeFi-relevant `record_captured(` callsite (perp_funding / vault_share_price / position_data + the orchestrator Phase
   2.B refactor's bar-write path) and stamp the df immediately before the call. Pair test:
   `assert "available_at" in df.columns and df["available_at"].notna().all()`. The number of commits ≈ number of
   callsites (~5 cefi-relevant handlers + orchestrator), not 10 venue files.

The reshape lands cleanly inside Phase 1 of `available_at_lookahead_bias_completion_2026_05_08.md` (which already
correctly identifies the dependency on Phase 0 MDPS bar boundary contract for bar data + the formula needing UAC
SOURCE_PRIORITY field). No new plan needed; the existing P0 todo absorbs.

**Lift this issue doc** when (a) UAC SOURCE_PRIORITY emission_latency field shipped + (b) UTL
`stamp_available_at_cefi_tick` helper shipped + (c) writegate Phase 2.B orchestrator refactor lands. Then a follow-up
Tab can do the per-callsite wiring as ~5-7 mechanical commits with QG-clean unit tests, NOT 10 per-venue commits.
