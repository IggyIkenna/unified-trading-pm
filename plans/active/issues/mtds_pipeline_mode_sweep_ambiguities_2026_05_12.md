---
title: "MTDS Phase 4.MTDS pipeline_mode sweep — operator-decision-required ambiguities"
created: 2026-05-12
author: ikenna-v8-mw-mtds-sweep
source:
  - market-tick-data-service/market_tick_data_service/cli/handlers/_defi_manifest.py
  - market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py
  - market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py
  - market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py
  - market-tick-data-service/market_tick_data_service/engine/orchestrator.py
  - market-tick-data-service/scripts/mtds_reconcile_partial_bundles.py
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# MTDS Phase 4.MTDS pipeline_mode sweep — operator-decision-required ambiguities

> **✅ RESOLVED by operator 2026-05-12** (decision relayed via ikenna-main slot 1).
>
> **Q1 = (α)** — migrate `DefiManifestRecorder.record_captured` legacy `ManifestWriter.add()` path → v8 `record_captured()` path. No further legacy `add()` callsites remain post-sweep.
>
> **Q2 = (A)** — extend UAC `PipelineMode` enum + `SOURCE_PRIORITY` with 6 missing values: `BATCH_YAHOO` / `BATCH_BARCHART` / `BATCH_FOOTYSTATS` / `BATCH_HYPERLIQUID_REST` / `BATCH_PYTH_HERMES` / `BATCH_CHAINLINK`. SOURCE_PRIORITY entries land per existing per-source layering convention (Yahoo / Barchart / footystats / Hyperliquid REST batch fallbacks; Pyth Hermes + Chainlink batch ingest paths).
>
> **Implementation owner**: Ikenna slot 3 (`code_freeze_migrate_backfill` Phase 1.E audit — already grokked the PipelineMode landscape). Estimated ~60 min mechanical sweep once Q1+Q2 triaged. Once shipped: this doc flips to ✅ CLOSED + `locked_by` line removed.
>
> **Unblocks**: Phase 4.MTDS → Phase 4.DEFAULT-REMOVAL → 2026-05-15 Phase 1 freeze gate.

> **Severity**: P0 — blocks Phase 4.DEFAULT-REMOVAL in `unified-trading-library`.
> **Blast radius**: MTDS (26 files / 102 invocations); UTL `ManifestWriter.add()` (legacy path lacks `pipeline_mode`); UAC `PipelineMode` closed-set.
> **Suggested owner**: operator triage (Ikenna — UAC SSOT design call). **→ DECIDED 2026-05-12 (above).**

## What I found

Phase 4.MTDS sweep (sub-agent `ikenna-v8-mw-mtds-sweep` spawned by slot 2 / `ikenna-v8-manifestwriter-tab`) asked to pass explicit `pipeline_mode=PipelineMode.BATCH_<source>` at every `record_captured` / `record_empty` / `record_failed` / `record_expected_empty` / `record_expected_unattempted` callsite in `market-tick-data-service` (per Phase 4.DEFAULT-REMOVAL prerequisite that will delete the `pipeline_mode: PipelineMode | None = None` default in UTL `ManifestWriter`).

Workspace-wide grep + read found **102 real method invocations across 26 files**:

| File class | Files | Invocations | Ambiguity |
|---|---|---|---|
| `_defi_manifest.py` (recorder shim) | 1 | 3 (internal `add`/`record_empty`/`record_failed`) | YES — see Q1 below |
| DeFi handlers (subgraph-only) | 14 | ~42 | NO — `BATCH_ONCHAIN_SUBGRAPH` per UAC `SOURCE_PRIORITY` |
| DeFi handlers (RPC-only) | 3 (gas_fee, token_transfers, vault_share_price) | ~9 | NO — `BATCH_ONCHAIN_RPC` per UAC |
| DeFi handlers (mixed REST + subgraph) | 3 (perp_funding, oracle_prices, lst_rates) | ~25 | **YES — Q2** |
| `engine/orchestrator.py` (cefi/tradfi/sports/prediction dispatch) | 1 | 9 | **YES — Q3** |
| `scripts/build_continuous_es.py` (TradFi continuous future) | 1 | 1 | NO — `BATCH_DATABENTO` |
| `market_tick_data_service/scripts/rebuild_prediction_manifest.py` | 1 | 1 | NO — `BATCH_POLYMARKET_CLOB` |
| `scripts/mtds_reconcile_partial_bundles.py` (reconciler) | 1 | 1 | **YES — Q4** |
| `tests/unit/test_defi_manifest_recorder.py` (MagicMock test) | 1 | 4 | **YES — Q5** |

### Q1 — `DefiManifestRecorder` internal `add()` path doesn't surface `pipeline_mode` to the manifest record

`_defi_manifest.py` `record_captured` calls `self._writer.add(...)` (UTL `ManifestWriter.add()`, lines 1208-1407 of `manifest_writer.py`). The legacy `add()` accepts arbitrary `**kwargs: object` but **does NOT extract `pipeline_mode` and does NOT write it onto `AvailabilityRecord`** (lines 1367-1402). Passing `pipeline_mode=` through `**kwargs` is silently swallowed.

In contrast, `record_empty()` / `record_failed()` / `record_expected_empty()` / `record_expected_unattempted()` / `record_captured()` (the v8 path) all accept `pipeline_mode: PipelineMode | None = None` explicitly and stamp it on the manifest record.

**Implication**: For the 20 DeFi handlers that route `record_captured` through the recorder (which calls `add()`), there is currently NO way to set `pipeline_mode` on the CAPTURED row even after this sweep — the value would be empty-string by default per `_coerce_pipeline_mode("")`.

**Two valid resolutions**:
- **Option α (recommended)**: Migrate `DefiManifestRecorder.record_captured` from `self._writer.add(...)` to `self._writer.record_captured(...)` (the v8 path). This is the canonical write-path per UTL Phase 1B comments + plan `gcs_migration_bundle_pipeline_mode_2026_05_08`. Requires schema validation kwargs (`df`, `category`, `instrument_type`, `data_type`) — recorder currently lacks the `df` it just built (the parquet write is done outside the recorder).
- **Option β**: Extend UTL `ManifestWriter.add()` to extract `pipeline_mode` from `**kwargs` and stamp it on `AvailabilityRecord`. Less invasive but perpetuates the legacy `add()` path that the codebase is trying to retire.

**This is a UTL design call** — α is the cleaner shape per the workspace direction (canonical `record_captured` over legacy `add()`) but is invasive for the DeFi recorder. β is mechanical but contradicts the "no double SSOT" rule.

### Q2 — DeFi handlers using non-canonical sources within a UAC-declared `(asset_group, data_type)`

UAC `SOURCE_PRIORITY` declares ONE source per `(asset_group, data_type)` pair under the closed-set rule (Phase 1B top-entry-only convention). For DeFi, this means every DeFi data_type maps to either `onchain_subgraph` or `onchain_rpc`. The closed-set `PipelineMode` has matching enum values.

But three handlers use **multiple heterogeneous sources within a single data_type**:

- **`perp_funding_handler.py`** (`data_type = perp_funding`): protocols are `hyperliquid` (REST API, no subgraph), `aster` (REST), `gmx` (subgraph). `perp_funding` is **NOT in UAC `SOURCE_PRIORITY`** at all (only `("cefi", "funding_rate"): ["tardis"]` exists). Is DeFi-perp-funding a missing UAC entry, or should it be folded into `("cefi", "funding_rate")` since these are CeFi venues despite their on-chain nature?
- **`oracle_prices_handler.py`** (`data_type = ?`): Chainlink (eth_call → RPC) + Pyth Hermes (HTTPS pull). Both are oracle prices. Chainlink fits `BATCH_ONCHAIN_RPC`; Pyth Hermes is `BATCH_PYTH_HERMES` or `BATCH_ONCHAIN_RPC` (Pyth Hermes serves Solana via HTTPS, not RPC). **No `BATCH_PYTH_HERMES` enum exists.**
- **`lst_rates_handler.py`** (`data_type = lst_yields`): Tier-1 RPC at historical block (RPC), Tier-2 subgraph daily snapshot. UAC maps `("defi", "lst_yields"): ["onchain_subgraph"]` — but Tier-1 RPC is the primary path; subgraph is fallback.

**Operator decisions needed**:
- Should `perp_funding` get a UAC `SOURCE_PRIORITY` entry? If so, with what source token? If we add it, we may need new `PipelineMode` enum values (e.g., `BATCH_HYPERLIQUID_REST` / `BATCH_GMX_SUBGRAPH`) OR collapse to `BATCH_ONCHAIN_SUBGRAPH` as an umbrella.
- For oracle_prices Pyth-Hermes path: add `BATCH_PYTH_HERMES` enum value, or umbrella under `BATCH_ONCHAIN_RPC`?
- For lst_rates RPC path: even though UAC declares `onchain_subgraph`, the runtime path is RPC. Should `pipeline_mode` reflect the actual runtime source (RPC) or the UAC-declared canonical source (subgraph)?

**This is a UAC closed-set extension call** — per the spec "DON'T add new `PipelineMode` enum values without filing a finding first (operator-only design call)".

### Q3 — `engine/orchestrator.py` has 9 `record_*` callsites where source is determined by per-venue adapter dispatch

The orchestrator's `process_ticks` flow routes per `(asset_group, venue, data_type)` to one of: Tardis (cefi), Databento (tradfi), Yahoo (cefi VIX 15m fallback BUT only via the umi_tick_provider path, not orchestrator), api_football / footystats / understat / transfermarkt / soccer_football_info / open_meteo (sports), polymarket_clob (prediction). The 9 `record_*` callsites in orchestrator.py at lines 2388, 2502, 2668, 2675, 2807, 2816, 2855, 2860 are inside dispatch branches.

Lines 2388 (cluster gate fail for tradfi ES options) → `BATCH_DATABENTO`.
Line 2502 (prediction CQG bundle no envelope) → `BATCH_POLYMARKET_CLOB`.
Lines 2668, 2675 (sports per-fixture sentinel) → source depends on data_type from `get_primary_source("sports", dt)`.
Lines 2807, 2816 (per-instrument cefi sentinel) → `BATCH_TARDIS`.
Lines 2855, 2860 (per-data-type sentinel after venue loop) → source depends on `(asset_group, data_type)` resolution.

**Operator decisions needed**:
- Should the orchestrator's per-call `pipeline_mode` be derived dynamically via `pipeline_mode_for_source(get_primary_source(asset_group, data_type))` at each callsite (clean — UAC SSOT-driven), or hardcoded per branch (mechanical — visible per-call)?
- For the cefi VIX 15m Yahoo fallback path inside Databento routing (orchestrator does NOT itself trigger Yahoo — that's in `umi_tick_provider.py`): the orchestrator branch is still `BATCH_DATABENTO`. Confirm.

### Q4 — `mtds_reconcile_partial_bundles.py` reconciler should NOT stamp a new `pipeline_mode`

This script reads existing manifest rows (which already carry `pipeline_mode` from the original writer) and flips them from `captured` to `attempted_failed` for partial bundles. The original `pipeline_mode` should be **preserved**, not re-stamped. Passing a fresh `pipeline_mode=` kwarg to `record_failed` would clobber the original.

**Operator decision needed**: should reconciler scripts pass the `pipeline_mode` extracted from the row (`pipeline_mode=PipelineMode(row["pipeline_mode"])`)? Currently the row_key dict at line 504-513 doesn't include `pipeline_mode`. Need to add it to preserve provenance.

### Q5 — `tests/unit/test_defi_manifest_recorder.py` constructs the recorder without `pipeline_mode`

If we go with Option α (Q1) — make `DefiManifestRecorder.__init__` accept `pipeline_mode` — the test fixtures need updating. Mechanical change; flagged for visibility.

## Why it matters

1. **Phase 4.DEFAULT-REMOVAL** in UTL `ManifestWriter` will fail-fast on any callsite that relies on the `None` default. Without resolving Q1, the DeFi handlers' `record_captured` path (routing through `add()`) won't even surface `pipeline_mode` to the manifest record at all — Phase 4.DEFAULT-REMOVAL would not catch this silent gap.
2. **Closed-set round-trip** between `SOURCE_PRIORITY` and `PipelineMode` is asserted by `assert_pipeline_mode_source_priority_round_trip` in UAC. Adding `perp_funding` to SOURCE_PRIORITY without a matching `PipelineMode` value would fail that assertion.
3. **Batch-vs-live reconciliation** queries pivot on `pipeline_mode`. Wrong/missing `pipeline_mode` values mean the live-batch parity check (writegate plan Phase 12) can't distinguish which source produced a row.
4. **Manifest-row provenance** in reconcilers — silently overriding `pipeline_mode` during a flip would destroy the original-source signal for any future audit.

## Recommended decision

Operator triage:
- **Q1**: pick α (migrate DeFi recorder to `record_captured()` v8 path) OR β (extend `add()` to plumb `pipeline_mode`). Recommend α despite invasiveness — aligns with "no double SSOT" + canonical write-path direction.
- **Q2**: extend `PipelineMode` + `SOURCE_PRIORITY` with `("defi", "perp_funding"): ["onchain_subgraph"]` (umbrella) OR add `BATCH_HYPERLIQUID_REST` / `BATCH_PYTH_HERMES` granularity? Recommend umbrella for May-23 cutover (less surface area; multi-source merge deferred per existing plan `multi_source_priority_merge_2026_*<TBD>.md`).
- **Q3**: prefer dynamic `pipeline_mode_for_source(get_primary_source(...))` over hardcoded branches — single SSOT (UAC) drives the runtime decision.
- **Q4**: reconcilers extract `pipeline_mode` from the source row + pass it through. Add `pipeline_mode` to the row_key extraction at line 504-513.
- **Q5**: mechanical follow-on once Q1 lands.

## Partial scope shipped while awaiting triage

Sub-agent shipped **zero file changes** in this session — every callsite touches one of the 5 ambiguities above. Net effect of premature implementation would be either forcing wrong values (banned per spec) or extending UTL/UAC without operator approval (banned per spec).

**Next session pickup**: once operator triages Q1-Q5, the sweep is mechanical:
- Resolution path α (Q1) + dynamic source resolution (Q3): ~60 minutes of edits across 26 files.
- All `record_*` callsites pass `pipeline_mode=` explicitly.
- Test fixtures updated (Q5).
- `bash scripts/quality-gates.sh` re-runs clean.
- Bundled FF push to LDR per Half 4.

## Composes with

- `unified-trading-pm/plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` — writegate slice (b)+(c) emission policy SSOT.
- `unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md` — Phase 2 manifest schema work that benefits from clean `pipeline_mode` stamping.
- `unified-trading-pm/plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` (if extant) — Phase 1B established the `pipeline_mode` axis; Phase 4 finalises it.
- `unified-trading-pm/plans/active/predictions_master_2026_05_07.md` — prediction handlers' `pipeline_mode` (Polymarket CLOB vs Gamma API).
