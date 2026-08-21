---
doc_type: issue
title: ASTER adapter carries a dead "off-chain" chain default + an unverified "off-chain" instrument-catalogue field — manifest itself confirmed CORRECT, this is a smaller code-hygiene loose end
summary: >-
  Operator asked whether `AsterAdapter`'s `chain="off-chain"` constructor default (vs. `umi_tick_provider.py`'s
  `_ASTER_CHAIN = ChainKind.BSC` and `migrate_defi_full_v9_canonical.py`'s `"ASTER": "BSC"`) represents a live bug
  where production data is being recorded with the wrong chain value. Investigated with live evidence (not
  assumed): the real CEFI manifest (`market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`)
  shows 2,571,675 real ASTER rows across every data_type (book_snapshot_5/derivative_ticker/futures_chain/
  liquidations/ohlcv_1m/options_chain/perp_funding/trades/volatility_index) and every capture_status — 100% carry
  `chain=""`, zero rows show `"BSC"`, `"off-chain"`, or `"ASTER"`. **The manifest is correct and consistent with the
  intended cefi-no-chain-axis convention** (`onchain_perp_batch_handler.py::_venue_chain("ASTER")` returns `""`,
  matching the already-executed `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py` cleanup for this exact venue).
  This is NOT the same class of bug as the resolved KALSHI-PERP manifest-chain contradiction. What remains: (1)
  `AsterAdapter.__init__`'s `chain="off-chain"` parameter is genuinely DEAD — `self.chain` is referenced nowhere in
  the file except `__repr__` — yet a real production call site
  (`onchain_perp_batch_handler.py:710`, `AsterAdapter(project_id=self._project_id)`) constructs it without ever
  overriding `chain`, so the misleading default silently flows through unused; (2) `_ASTER_BASE_INSTRUMENT`'s
  `"chain": "off-chain"` feeds INSTRUMENT-DEFINITION dicts (`_convert_symbol_to_instrument`/
  `_convert_symbol_to_spot_pair`, an instrument-catalogue shape — instrument_key/instrument_type/symbol/base_asset/
  tick_size/etc.), NOT the MTDS tick-data manifest; where that catalogue data ultimately lands and whether any
  consumer there expects `"BSC"` instead was not traced to completion. Separately, `umi_tick_provider.py`'s
  `_route_aster`/`_ChainAnnotatingWriter` stamps `chain="BSC"` into the PARQUET PAYLOAD DataFrame column (row
  content, not the manifest partition key) for a general multi-venue download path
  (`download()` → `_route_aster()`) that appears to be a separate live-tick-collection surface from
  `onchain_perp_batch_handler.py`'s own direct `AsterAdapter.fetch_trades`/`fetch_funding_rates` calls;
  `umi_tick_provider.py` itself performs no manifest recording (zero `record_captured`/`ManifestWriter` references
  in that file), so its actual caller's manifest-chain resolution was not traced. No production write made; this
  doc records the measured state only.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, aster, chain-axis, code-hygiene, dead-code, low-priority]
related:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/archive/issues/defi_cefi_kalshi_perp_manifest_chain_convention_contradiction_2026_08_21.md,
    /plans/active/issues/defi_cefi_hyperliquid_perp_funding_manifest_chain_contradiction_2026_08_21.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-21"
author: unknown
last_updated: "2026-08-21"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineer
drift_direction: stable
depends_on: []
resolved_by:
locked_by:
source: >-
  Operator question 2026-08-21, raised while reviewing the resolved KALSHI-PERP chain-convention finding — asked
  whether ASTER has a live analogue after spotting `AsterAdapter`'s "off-chain" default contradicting `"BSC"`
  elsewhere in the repo. Investigated with the same live-evidence discipline before concluding anything.
context_scope:
  [
    market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/aster_adapter.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py,
    market-tick-data-service/market_tick_data_service/adapters/umi_tick_provider.py,
  ]
---

# ASTER dead chain default + unverified instrument-catalogue field

## Headline: the manifest is correct — this is NOT a live data-correctness bug

Live query, `market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, filtered to
`venue="ASTER"`:

```
total ASTER manifest rows: 2,571,675
every (data_type, capture_status) combination → chain=""  (zero exceptions)
```

Covers `book_snapshot_5`, `derivative_ticker` (391,781 `captured`), `futures_chain`, `liquidations`, `ohlcv_1m`,
`options_chain`, `perp_funding`, `trades` (803,575 `captured`), `volatility_index`. This matches
`onchain_perp_batch_handler.py::_venue_chain()`'s documented, intentional convention (cefi venues have no chain
shard axis → `""`) and the already-executed `restamp_cefi_onchain_perp_venue_chain_2026_07_21.py` cleanup, which
specifically targeted ASTER (alongside HYPERLIQUID/EXTENDED-STARKNET/LIGHTER-ZKSYNC) for the identical
venue-as-chain contamination class. No restamp, no code fix, no operator ruling needed for the manifest itself.

## What's left: two loose ends, neither confirmed to touch real data

1. **Dead default parameter.** `AsterAdapter.__init__(..., chain: str = "off-chain", ...)` — `self.chain` (set via
   `super().__init__(chain=chain, ...)`) is referenced nowhere else in `aster_adapter.py` except
   `__repr__` (`f"AsterAdapter(chain={self.chain}, ...)"`). `onchain_perp_batch_handler.py:710` constructs
   `AsterAdapter(project_id=self._project_id)` — no `chain` override — so the misleading default is live-exercised
   in production but provably inert for any real behavior.
2. **Unverified instrument-catalogue consumer.** `_ASTER_BASE_INSTRUMENT: dict = {"venue": "ASTER", "chain":
   "off-chain", ...}` is spread into `_convert_symbol_to_instrument()`/`_convert_symbol_to_spot_pair()`'s returned
   dicts — an instrument-DEFINITION shape (`instrument_key`, `instrument_type`, `symbol`, `base_asset`, `tick_size`,
   `min_size`, ...), not a manifest row. Where these definitions are ultimately consumed (an instruments-service
   catalogue sync? a local registry file? discarded?) was not traced, so whether any real consumer expects
   `"chain": "BSC"` here instead and silently gets `"off-chain"` is genuinely unknown — distinct from the manifest
   question, which IS answered.
3. **Separate live surface, not fully traced.** `umi_tick_provider.py`'s `download()` dispatcher routes ASTER
   through `_route_aster()`, which wraps the writer in `_ChainAnnotatingWriter(writer, ChainKind.BSC)` — stamping
   `chain="BSC"` into the PARQUET PAYLOAD (a DataFrame column inside the row content), not the manifest partition
   key. `umi_tick_provider.py` does no manifest recording itself (`grep -n 'record_captured\|ManifestWriter'` — zero
   hits); whatever calls `download()` for ASTER (likely `tick_data_handler.py`'s general multi-venue path, given
   its own comment references `umi_tick_provider` routing) resolves the manifest chain value independently, not
   traced here. Given the manifest is confirmed `""` for every ASTER row including the same data_types this path
   would produce, this is very likely benign (either this path isn't live for ASTER, or its own manifest write also
   resolves to `""`) — not confirmed either way.

## Recommended next step

- [ ] [DIAG] P3. **Trace loose ends 2 and 3 to their actual consumers, low urgency.** (a) Find where
      `_convert_symbol_to_instrument`/`_convert_symbol_to_spot_pair`'s returned instrument-definition dicts are
      used/written, and confirm whether any real consumer cares about the `"chain"` field's value there (if yes,
      decide `"off-chain"` vs `"BSC"` is correct for THAT context — instrument metadata is a different question from
      the manifest partition key). (b) Confirm whether `umi_tick_provider.download()` is actually live-invoked for
      `ASTER` in production (vs. `onchain_perp_batch_handler.py`'s own direct `AsterAdapter` calls being the only
      real path), and if so, trace its caller's manifest-chain resolution to confirm it also lands on `""` (matching
      the live-verified manifest state) rather than assuming it does. (c) If both trace to genuinely dead/unused
      code, remove `AsterAdapter.__init__`'s misleading `chain` parameter (or default it to `""` to match reality)
      as a small, low-risk cleanup — not urgent, no data-correctness impact either way per the manifest evidence
      above. Repo: market-tick-data-service. Source: this doc. **Done when**: both consumers are identified with
      evidence (not assumed dead), and either confirmed harmless (doc closes citing the trace) or a scoped fix ships
      if a real consumer is found relying on the wrong value.

## Codex SSOTs

- `/codex/02-data/defi-canonical-naming-ssot.md` § "On-chain perp CLOBs are CeFi, NOT DeFi" (the settled
  asset_group + chain-axis convention this doc's manifest evidence confirms is being followed correctly for ASTER)

## Progress Log

- **2026-08-21**: Filed after operator question about ASTER's chain-value conventions. Manifest live-verified clean
  (2,571,675 rows, 100% `chain=""`) — the core data-correctness question is answered negative (no bug in recorded
  data). Filed as a tracked P3 follow-up per this workspace's hard rule against prose-only conclusions, not because
  the finding is urgent.
