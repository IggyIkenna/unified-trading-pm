---
title:
  "footystats source has no BATCH_FOOTYSTATS PipelineMode value (closed-set rule violation when stamping footystats
  catalog refreshes)"
created: 2026-05-12
author: ikenna-v8-mw-instruments-sweep
source:
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py
  - instruments-service/instruments_service/engine/orchestrator.py
  - instruments-service/scripts/backfill_per_league_record_empty.py
  - instruments-service/scripts/backfill_sports_per_entity_manifest.py
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# footystats source has no BATCH_FOOTYSTATS PipelineMode value

> **✅ RESOLVED by operator 2026-05-12** (decision relayed via ikenna-main slot 1).
>
> **Q2 = (A)** — extend UAC `PipelineMode` enum + `SOURCE_PRIORITY` with **`BATCH_FOOTYSTATS`** (plus 5 sibling values
> from `mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md`: `BATCH_YAHOO` / `BATCH_BARCHART` / `BATCH_HYPERLIQUID_REST`
> / `BATCH_PYTH_HERMES` / `BATCH_CHAINLINK`).
>
> **Implementation owner**: Ikenna slot 3 — bundle with the workspace-wide PipelineMode sweep. Once `BATCH_FOOTYSTATS`
> lands in the enum + SOURCE_PRIORITY, the ~7 instruments-service orchestrator callsites + 2 backfill scripts flip from
> workaround closed-set match → exact source tag.
>
> **Unblocks**: accurate footystats-catalog-refresh pipeline_mode tagging + Phase 4.INSTRUMENTS sweep + Phase
> 4.DEFAULT-REMOVAL.

> **Severity**: P1 — blocks accurate `pipeline_mode=` tagging for footystats-served instruments catalog refreshes
> (MATCHES / PREDICTIONS / ODDS data_types). Workaround uses closest closed-set match. Phase 4.DEFAULT-REMOVAL
> prerequisite is still satisfiable. **Blast radius**: instruments-service orchestrator (~7 footystats callsites: lines
> ~4510, 4531, 4743, 4755, 4779, 4953, 4974); `scripts/backfill_per_league_record_empty.py` (MATCHES entry);
> `scripts/backfill_sports_per_entity_manifest.py` (MATCHES + ODDS + PREDICTIONS specs). Same callsite class likely
> exists in MTDS / features-\* once they ship sweeps. **Suggested owner**: operator triage (Ikenna — UAC SSOT design
> call). **→ DECIDED 2026-05-12 (above).**

## What I found

Phase 4.INSTRUMENTS sweep (sub-agent `ikenna-v8-mw-instruments-sweep` spawned by slot 2 /
`ikenna-v8-manifestwriter-tab`) asked to pass explicit `pipeline_mode=PipelineMode.BATCH_<source>` at every
`record_captured` / `record_empty` / `record_failed` / `record_expected_empty` / `record_expected_unattempted` callsite
in `instruments-service` per the closed-set rule "every batch `PipelineMode` value MUST correspond to an entry in
`SOURCE_PRIORITY`, and every source string in `SOURCE_PRIORITY` MUST have a matching `PipelineMode` value"
(`unified_api_contracts/canonical/crosscutting/pipeline_mode.py` lines 23-27).

**The gap**:

- `unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py` has 13 batch values:
  `BATCH_API_FOOTBALL` / `BATCH_DATABENTO` / `BATCH_INSTRUMENTS_SERVICE` / `BATCH_ODDS_API` / `BATCH_ONCHAIN_RPC` /
  `BATCH_ONCHAIN_SUBGRAPH` / `BATCH_OPEN_METEO` / `BATCH_POLYMARKET_CLOB` / `BATCH_POLYMARKET_GAMMA_API` /
  `BATCH_SOCCER_FOOTBALL_INFO` / `BATCH_TARDIS` / `BATCH_TRANSFERMARKT` / `BATCH_UNDERSTAT`. **No `BATCH_FOOTYSTATS`**.
- `SOURCE_PRIORITY` (`source_priority.py`) does NOT register `footystats` as a top entry for any
  `(asset_group, data_type)` pair. The docstring lines 86-88 explicitly say: _"api_football is primary, footystats is
  the multi-source merge candidate (deferred)."_
- However, the live code paths `_fetch_footystats_matches` / `_fetch_footystats_predictions` / `_fetch_footystats_odds`
  in `instruments_service/engine/orchestrator.py` CALL the footystats adapter directly and write manifest rows for
  `MATCHES` / `PREDICTIONS` / `ODDS` data_types. Per the live=batch principle ("`pipeline_mode` identifies the
  source-and-mode that produced it"), these rows SHOULD carry `pipeline_mode=batch_footystats`.

**Same shape applies to multi-source readers**:

- `scripts/backfill_per_league_record_empty.py` line 56 declares `("MATCHES", "footystats", ["Prediction", "Features"])`
  — `source="footystats"` is documented as the source string but cannot be round-tripped through
  `pipeline_mode_for_source("footystats")` (raises `ValueError` per the closed-set guard).
- `scripts/backfill_sports_per_entity_manifest.py` `SPECS` (lines 85-162) declares `source="footystats"` for `MATCHES`
  (line 117) / `ODDS` (line 124) / `PREDICTIONS` (line 131).
- UAC `get_expected_leagues_for_source("footystats", ...)` (used by these scripts) IS supported — footystats has a
  league list in UAC even though it lacks a SOURCE_PRIORITY entry.

## Why it matters

1. **Closed-set round-trip rule is violated** for footystats-served data: writing manifest rows requires picking a
   non-footystats `PipelineMode` value, hiding the actual source identity at write time. Downstream batch-vs-live
   reconciliation queries (writegate Phase 12) that pivot on `pipeline_mode` will mis-classify footystats rows as
   `BATCH_API_FOOTBALL` / `BATCH_ODDS_API`, conflating two genuinely different adapters.
2. **Phase 4.DEFAULT-REMOVAL prerequisite** (delete the `pipeline_mode: PipelineMode | None = None` default in UTL
   `ManifestWriter`) cannot ship cleanly while any sweep callsite still relies on a workaround. The current workaround
   (use closest closed-set match) leaks "approximately tagged" rows that will need a re-tag migration if
   `BATCH_FOOTYSTATS` is later added.
3. **Same shape likely exists in MTDS / features-\* sweeps** — the sub-agent for `ikenna-v8-mw-mtds-sweep` may surface
   the same gap if MTDS reads footystats anywhere. Resolving once at UAC SSOT level fixes every downstream sweep.

## What this sweep did as workaround

Per the spawn-prompt anti-pattern _"DON'T add new PipelineMode enum values without filing a finding first"_, this Phase
4.INSTRUMENTS sweep tagged the footystats-served callsites with the closest closed-set match per UAC `SOURCE_PRIORITY`:

- `MATCHES` / `PREDICTIONS` data_types → `PipelineMode.BATCH_API_FOOTBALL` (because `SOURCE_PRIORITY` registers
  `api_football` for the canonical fixture-lifecycle data_types and footystats is documented as the "multi-source merge
  candidate" for the same shard).
- `ODDS` data_type → `PipelineMode.BATCH_ODDS_API` (because `SOURCE_PRIORITY` registers `odds_api` for `ODDS_SNAPSHOT` /
  `ODDS_MOVEMENT` / `ARBITRAGE`).

The mapping is documented in `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` (orchestrator.py header comment cites this finding by
filename) so a follow-up sweep can find every workaround tag and re-stamp with `BATCH_FOOTYSTATS` once UAC ships it.

## Recommended decision

Three valid options (operator picks):

**Option A — Add `BATCH_FOOTYSTATS` + register footystats in SOURCE_PRIORITY (CLEANEST)**:

1. UAC `pipeline_mode.py`: add `BATCH_FOOTYSTATS = "batch_footystats"` to `PipelineMode` enum.
2. UAC `source_priority.py`: add the multi-source merge entries for footystats-served data_types — likely
   `("sports", "MATCHES"): ["api_football", "footystats"]` (api_football primary, footystats secondary),
   `("sports", "PREDICTIONS"): ["footystats"]` (footystats sole source),
   `("sports", "ODDS"): ["footystats", "odds_api"]` (or the inverse depending on which adapter is canonical for the
   legacy `ODDS` data_type vs the new `ODDS_SNAPSHOT`).
3. UAC `EMISSION_LATENCY_MS_BY_SOURCE`: add footystats entry (likely ~600_000 ms — the adapter's polling cadence is
   ~10min).
4. Re-run Phase 4.INSTRUMENTS sweep's `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` to point `MATCHES` / `PREDICTIONS` / `ODDS`
   at `BATCH_FOOTYSTATS`.
5. Backfill / migration script to re-tag historical footystats-served manifest rows from `BATCH_API_FOOTBALL` /
   `BATCH_ODDS_API` to `BATCH_FOOTYSTATS`.

**Option B — Keep current workaround + bake the "approximate tag" into UAC docstring**:

- Accept that footystats catalog refreshes carry `BATCH_API_FOOTBALL` / `BATCH_ODDS_API` until the multi-source merge
  plan ships.
- Document the approximation in UAC `pipeline_mode.py` docstring + `SOURCE_PRIORITY` so the data-status UI /
  batch-vs-live recon queries don't mis-attribute the rows.
- Phase 4.DEFAULT-REMOVAL ships cleanly (every callsite has an explicit closed-set value).
- Re-tag migration deferred until UAC adds `BATCH_FOOTYSTATS` (potentially never if the multi-source merge plan retires
  footystats).

**Option C — Retire footystats as a write-side source**:

- The "multi-source merge candidate (deferred)" status implies eventual retirement of footystats's distinct write path:
  merge happens at read time from the canonical api_football / odds_api parquets.
- If footystats data is never written to the manifest under its own identity, the gap is moot — the workaround tag is
  the right answer permanently.
- Requires explicit plan to shut down `_fetch_footystats_*` write paths + migrate any consumers that read distinct
  footystats parquets today.

**Strong recommendation** (in absence of operator direction): **Option A**. Closed-set rule violations are precisely the
kind of "drift between sources of truth" that the writegate plan is closing — keeping a workaround tag invites
re-divergence when a follow-up sub-agent re-runs the sweep without reading this finding. The +1 enum value + 1
SOURCE_PRIORITY entry per data_type is a 30min UAC change; the re-tag migration is a one-time script.

## Composes with

- `plans/active/issues/mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md` — the MTDS sister sweep raised 5 ambiguities;
  this finding is the 6th class (different repo, but same closed-set design call).
- `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` Phase 4.DEFAULT-REMOVAL — depends on every sub-agent's
  sweep resolving cleanly.
- `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 4 — the umbrella that owns the
  explicit-pipeline-mode rollout.
