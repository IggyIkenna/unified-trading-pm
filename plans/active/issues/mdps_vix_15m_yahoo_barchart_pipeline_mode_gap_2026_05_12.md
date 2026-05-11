---
title: "VIX 15m route (Yahoo + Barchart) has no BATCH_YAHOO / BATCH_BARCHART PipelineMode values (closed-set rule violation when stamping VIX-gap empty_confirmed rows)"
created: 2026-05-12
author: ikenna-v8-mw-mdps-sweep
source:
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py
  - market-data-processing-service/market_data_processing_service/app/core/orchestration_writer.py
  - market-tick-data-service/market_tick_data_service/adapters/umi_tick_provider.py
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# VIX 15m route (Yahoo + Barchart) has no BATCH_YAHOO / BATCH_BARCHART PipelineMode values

> **Severity**: P1 — blocks accurate `pipeline_mode=` tagging for VIX-gap `empty_confirmed` rows emitted by `MDPS orchestration_writer._maybe_write_vix_gap_placeholder`. Workaround uses closest closed-set match. Phase 4.DEFAULT-REMOVAL prerequisite is still satisfiable.
> **Blast radius**: 1 callsite in `market-data-processing-service/market_data_processing_service/app/core/orchestration_writer.py:343` (`record_empty_for_shard` for VIX 15m gap dates 2025-11-13 → today−60d). Same shape will surface in MTDS sweep when the VIX 15m route at `market_tick_data_service/adapters/umi_tick_provider.py` is touched — Yahoo fetcher's `record_captured` writes will need a `pipeline_mode=` value that matches the actual source.
> **Suggested owner**: operator triage (Ikenna — UAC SSOT design call).

## What I found

Phase 4.MDPS sweep (sub-agent `ikenna-v8-mw-mdps-sweep` spawned by slot 2 / `ikenna-v8-manifestwriter-tab`) asked to pass explicit `pipeline_mode=PipelineMode.BATCH_<source>` at every `record_captured` / `record_empty` / `record_failed` / `record_expected_empty` / `record_expected_unattempted` callsite in `market-data-processing-service` per the closed-set rule "every batch `PipelineMode` value MUST correspond to an entry in `SOURCE_PRIORITY`, and every source string in `SOURCE_PRIORITY` MUST have a matching `PipelineMode` value" (`unified_api_contracts/canonical/crosscutting/pipeline_mode.py` lines 23-27).

**The gap**:

- `unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py` has 13 batch values: `BATCH_API_FOOTBALL` / `BATCH_DATABENTO` / `BATCH_INSTRUMENTS_SERVICE` / `BATCH_ODDS_API` / `BATCH_ONCHAIN_RPC` / `BATCH_ONCHAIN_SUBGRAPH` / `BATCH_OPEN_METEO` / `BATCH_POLYMARKET_CLOB` / `BATCH_POLYMARKET_GAMMA_API` / `BATCH_SOCCER_FOOTBALL_INFO` / `BATCH_TARDIS` / `BATCH_TRANSFERMARKT` / `BATCH_UNDERSTAT`. **No `BATCH_YAHOO`, no `BATCH_BARCHART`**.
- `SOURCE_PRIORITY` (`source_priority.py`) registers `("tradfi", "ohlcv_15m"): ["databento"]` — the docstring comment lines 144-148 explicitly cites VIX 15m as a routing exception: *"Yahoo for VIX 15m rolling window; Barchart for VIX 15m historical preload (handled at the MTDS routing layer, not here — both are listed for the same shard but the orchestrator picks by date)."*
- The MTDS routing layer (`market_tick_data_service/adapters/umi_tick_provider.py`'s `_fetch_yahoo_vix_15m` short-circuit + Barchart preload at `BARCHART_VIX_FIRST_DATE` → `BARCHART_VIX_LAST_DATE`) reads from Yahoo / Barchart but neither source is in `SOURCE_PRIORITY` as a top entry, and neither has a `PipelineMode` enum value.
- The MDPS `_maybe_write_vix_gap_placeholder` helper (orchestration_writer.py:270-360) emits `record_empty_for_shard(..., reason=EXPECTED_KNOWN_SOURCE_GAP)` for the documented mid-history gap (2025-11-13 → today−60d). Per the live=batch principle ("`pipeline_mode` identifies the source-and-mode that produced it"), the VIX-gap row carries... no actual source (the gap exists BECAUSE no source covers it). But the writer needs SOME closed-set value to satisfy the new explicit-pipeline-mode kwarg.

## Why it matters

1. **Closed-set round-trip rule is violated** for any Yahoo / Barchart-served VIX 15m data: writing manifest rows (whether `record_captured` for real Yahoo fetches OR `record_empty` for the documented gap window) requires picking a non-Yahoo-non-Barchart `PipelineMode` value, hiding the actual source identity at write time. Downstream batch-vs-live reconciliation queries (writegate Phase 12) that pivot on `pipeline_mode` will mis-classify VIX 15m rows as `BATCH_DATABENTO`, conflating two genuinely different adapters (Databento Glbx.Mdp3 vs Yahoo Finance vs Barchart CSV preload).
2. **Phase 4.DEFAULT-REMOVAL prerequisite** (delete the `pipeline_mode: PipelineMode | None = None` default in UTL `ManifestWriter`) cannot ship cleanly while any sweep callsite still relies on a workaround. The current workaround (use `BATCH_DATABENTO` because SOURCE_PRIORITY's top entry for `(tradfi, ohlcv_15m)` is `databento`) leaks "approximately tagged" rows that will need a re-tag migration if `BATCH_YAHOO` / `BATCH_BARCHART` is later added.
3. **The empty_confirmed VIX-gap row is the cleanest workaround case** — no parquet on disk, `capture_status=empty_confirmed` short-circuits downstream consumers, and the row reason `EXPECTED_KNOWN_SOURCE_GAP` IS the structural truth ("no source covers this date"). The pipeline_mode tag on this specific row is informational, not load-bearing. The same workaround applied to a `record_captured` row for an actual Yahoo VIX fetch would be more problematic.
4. **Same shape WILL surface in MTDS sweep** — the sub-agent for `ikenna-v8-mw-mtds-sweep` (if it touches `umi_tick_provider.py`'s VIX route) will need to tag `record_captured` writes for actual Yahoo / Barchart fetches. Resolving once at UAC SSOT level fixes every downstream sweep.

## What this sweep did as workaround

Per the spawn-prompt anti-pattern *"DON'T add new PipelineMode enum values without filing a finding first"*, this Phase 4.MDPS sweep tagged the single VIX 15m callsite at `orchestration_writer.py:343` with the closest closed-set match per UAC `SOURCE_PRIORITY`:

- VIX 15m `record_empty_for_shard(reason=EXPECTED_KNOWN_SOURCE_GAP)` → `PipelineMode.BATCH_DATABENTO` (because `SOURCE_PRIORITY[("tradfi", "ohlcv_15m")] = ["databento"]` is the top entry; the Yahoo / Barchart routing exception is documented at MTDS routing layer, not as a SOURCE_PRIORITY override).

The mapping is documented in an inline comment at the callsite (orchestration_writer.py lines 341-350) so a follow-up sweep can find the workaround tag and re-stamp with `BATCH_YAHOO` / `BATCH_BARCHART` once UAC ships them.

## Recommended decision

Three valid options (operator picks):

**Option A — Add `BATCH_YAHOO` + `BATCH_BARCHART` + register them as VIX-specific overrides in SOURCE_PRIORITY (CLEANEST)**:

1. UAC `pipeline_mode.py`: add `BATCH_YAHOO = "batch_yahoo"` and `BATCH_BARCHART = "batch_barchart"` to `PipelineMode` enum.
2. UAC `source_priority.py`: either (a) restructure `SOURCE_PRIORITY` to support per-instrument overrides like `("tradfi", "ohlcv_15m", "VIX"): ["yahoo", "barchart"]` (introduces a 3-tuple key — schema change), OR (b) document the VIX exception as a comment + add `yahoo` / `barchart` to `EMISSION_LATENCY_MS_BY_SOURCE` only (without a SOURCE_PRIORITY top-entry — keeps the 2-tuple key shape but means the closed-set round-trip rule needs adjustment to allow "registered in PipelineMode + EMISSION_LATENCY_MS_BY_SOURCE but not SOURCE_PRIORITY" as a valid state for routing-exception sources).
3. UAC `EMISSION_LATENCY_MS_BY_SOURCE`: add yahoo entry (~5min polling cadence) + barchart entry (one-time CSV preload, no live emission).
4. Re-stamp the `orchestration_writer.py:343` callsite to use the appropriate value:
   - For the documented gap (no source covers) — stay with `BATCH_DATABENTO` (most-canonical) or introduce a `BATCH_KNOWN_GAP` sentinel.
   - For actual Yahoo VIX fetches in MTDS — use `BATCH_YAHOO`.
   - For Barchart preload re-emissions — use `BATCH_BARCHART`.
5. Migrate historical VIX-route manifest rows from `BATCH_DATABENTO` to `BATCH_YAHOO` / `BATCH_BARCHART` where the actual fetch date implies the route.

**Option B — Keep current workaround + bake the "approximate tag" into UAC docstring (PRAGMATIC)**:

- Accept that VIX 15m manifest rows carry `BATCH_DATABENTO` until the multi-source merge plan ships.
- Document the approximation in UAC `pipeline_mode.py` docstring + at the `SOURCE_PRIORITY[("tradfi", "ohlcv_15m")]` comment line so the data-status UI / batch-vs-live recon queries don't mis-attribute the rows.
- Phase 4.DEFAULT-REMOVAL ships cleanly (every callsite has an explicit closed-set value).
- Re-tag migration deferred until UAC adds the new values (potentially never if Yahoo / Barchart preload is retired in favor of a future Databento VIX route).

**Option C — Document the gap row as a special case + use `BATCH_DATABENTO` permanently for the gap, address Yahoo / Barchart separately when MTDS sweep ships**:

- The VIX-gap row is a `record_empty` with `reason=EXPECTED_KNOWN_SOURCE_GAP` — semantically "no source exists." Tagging it with the canonical SOURCE_PRIORITY top entry (`BATCH_DATABENTO`) is the right answer FOR THE GAP because the missing data IS what Databento would have provided if it covered VIX (it doesn't — that's why Yahoo / Barchart exist as the routing exception).
- The `record_captured` callsite for actual Yahoo / Barchart fetches is owned by MTDS, not MDPS — leave the UAC enum decision until that sweep surfaces concrete callsites.
- This option is essentially "B for MDPS gap row + defer A/B decision for MTDS Yahoo / Barchart fetches."

**Strong recommendation** (in absence of operator direction): **Option C**. The MDPS gap-row callsite is the only concrete callsite this sweep introduces; tagging it with `BATCH_DATABENTO` is semantically defensible (it's the gap in what Databento SHOULD have provided per SOURCE_PRIORITY). The Yahoo / Barchart enum decision should be made when MTDS sweep surfaces real `record_captured` callsites for actual Yahoo / Barchart fetches — at that point Option A's enum additions become load-bearing rather than speculative.

## Composes with

- `plans/active/issues/footystats_pipeline_mode_gap_2026_05_12.md` — sister finding (footystats source missing from `PipelineMode` enum). Same closed-set design call shape.
- `plans/active/issues/mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md` — MTDS sister sweep raised 5 ambiguities; this finding is the 7th class (different repo, but same closed-set design call).
- `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` Phase 4.DEFAULT-REMOVAL — depends on every sub-agent's sweep resolving cleanly.
- `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 4 — the umbrella that owns the explicit-pipeline-mode rollout.

## SSOT references for VIX 15m route

- UAC `BARCHART_VIX_FIRST_DATE` / `BARCHART_VIX_LAST_DATE` (Barchart historical preload bounds).
- UAC `YAHOO_VIX_15M_WINDOW_DAYS` (Yahoo rolling 60d window length).
- UAC `is_vix_15m_gap_date(date)` (2025-11-13 → today−60d gap predicate).
- MTDS `market_tick_data_service/adapters/umi_tick_provider.py` — `(CBOE, ohlcv_15m)` route to `_fetch_yahoo_vix_15m` BEFORE generic Databento path.
- MDPS `market_data_processing_service/app/core/orchestration_writer.py:270-360` — `_maybe_write_vix_gap_placeholder` helper.
