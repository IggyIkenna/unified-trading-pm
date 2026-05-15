---
title:
  "features-calendar-service has no clean PipelineMode for time_features (datetime-only) + economic_events (FRED API)"
created: 2026-05-12
author: harsh-codefreeze-impl-tab (slot 3)
source:
  - features-service/features_service/calendar/engine/calendar_orchestrator.py
  - features-service/features_service/calendar/engine/calculators/economic_calendar_loader.py
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# features-calendar-service has no clean PipelineMode for time_features + economic_events

> **Severity**: P2 — same shape as `footystats_pipeline_mode_gap_2026_05_12.md` but for features-calendar-service. Phase
> 4.FEATURES sweep can ship cleanly with a documented workaround tag (mirrors footystats Option B); the long-tail clean
> fix is a UAC enum + SOURCE_PRIORITY extension proposal for operator decision.
>
> **Blast radius**: features-service `calendar/engine/calendar_orchestrator.py` `_record_manifest_failed` (line 241) +
> `_record_manifest_empty` (line 264). No other features-calendar callsites today; live*handler / batch_handler in the
> calendar subpackage don't currently invoke `record*\*` directly. **Suggested owner**: operator triage (Ikenna — UAC
> SSOT design call).

## What I found

Phase 4.FEATURES sweep (per `manifest_schema_final_gate_2026_05_09.md` Phase 4 +
`pipeline_mode_explicit_baseline.yaml`'s 2 calendar entries) asked to pass an explicit
`pipeline_mode=PipelineMode.BATCH_<source>` kwarg at every `record_*` callsite in features-service/calendar.

**The gap**:

- `CALENDAR_FEATURE_GROUPS = ["time_features", "economic_events"]` per
  `features-service/features_service/calendar/cli/handlers/batch_handler.py:46`
  - `live_handler.py:30`.
- `time_features` is computed purely from datetime arithmetic (no external source) — see `_generate_time_features` in
  `calendar_orchestrator.py:445`.
- `economic_events` is loaded from the FRED API (see `engine/calculators/economic_calendar_loader.py:4,150-262` —
  `EconomicCalendarLoader` reads "FRED API + hardcoded schedule fallback").
- UAC `PipelineMode` enum (`canonical/crosscutting/pipeline_mode.py:44-73`) has **no** `BATCH_FRED` or
  `BATCH_FEATURES_CALENDAR_SERVICE` value. UAC `SOURCE_PRIORITY` (`canonical/crosscutting/source_priority.py:198-199`)
  registers `instruments_service` for `("reference", "instruments")` / `("reference", "venue_trading_calendar")` but
  does NOT register a source for calendar features or FRED economic releases.

## Why it matters

Per the closed-set round-trip rule (`pipeline_mode.py:23-27`), every batch `PipelineMode` value MUST correspond to a
SOURCE_PRIORITY entry, and every source string in SOURCE_PRIORITY MUST have a matching `PipelineMode`. With no clean
closed-set value:

1. **Phase 4.DEFAULT-REMOVAL prerequisite** (delete `pipeline_mode: PipelineMode | None = None` default in UTL
   `ManifestWriter`) cannot ship until every callsite passes an explicit value.
2. **Batch-vs-live reconciliation queries** (writegate Phase 12) that pivot on `pipeline_mode` will mis-classify
   calendar features under whatever workaround tag we pick.
3. **Live-pipeline activation** (live_pipeline_mtds_mdps_features_2026_05_08.md) intends features-calendar-service to
   emit `LIVE_WEBSOCKET`-tagged rows; that's fine for live mode but the batch backfill path still needs a clean batch
   tag.

## What this sweep did as workaround

Per the footystats precedent — tag the 2 callsites with the closest closed-set match per UAC SOURCE_PRIORITY:

- **time_features** → `PipelineMode.BATCH_INSTRUMENTS_SERVICE` (because `SOURCE_PRIORITY` registers
  `instruments_service` for `("reference", "instruments")` / `("reference", "venue_trading_calendar")` — time-based
  session bitmaps + cyclic encodings are the closest semantic neighbour to a venue trading calendar; both are
  pure-derived from clock + venue-session config, no external API).
- **economic_events** → `PipelineMode.BATCH_INSTRUMENTS_SERVICE` (same fallback — FRED-sourced economic release dates
  are also "reference-data-ish" calendar entries; the FRED API isn't registered in `SOURCE_PRIORITY` so we don't have a
  `BATCH_FRED` value to use).

The mapping is documented in `_FEATURE_GROUP_TO_PIPELINE_MODE` at the top of `calendar_orchestrator.py` (same shape as
`instruments-service/instruments_service/engine/orchestrator.py` `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE`) so a follow-up
sweep can find every workaround tag and re-stamp once the UAC enum extension ships.

## Recommended decision

**Option A — Add `BATCH_FRED` + register FRED in SOURCE_PRIORITY (CLEANEST for economic_events)**:

1. UAC `pipeline_mode.py`: add `BATCH_FRED = "batch_fred"` to `PipelineMode` enum.
2. UAC `source_priority.py`:
   - Add `("calendar", "economic_events"): ["fred"]` entry to SOURCE_PRIORITY.
   - Add `"fred": 86_400_000` (or appropriate cadence) to `EMISSION_LATENCY_MS_BY_SOURCE` (FRED releases happen on
     schedule, mostly daily/weekly/monthly; pick the most-frequent cadence).
3. Re-stamp `economic_events` callsite → `PipelineMode.BATCH_FRED`.
4. Leaves `time_features` still on a workaround tag pending operator call.

**Option B — Add `BATCH_FEATURES_CALENDAR_SERVICE` for the whole calendar (CLEANEST for time_features)**:

1. UAC `pipeline_mode.py`: add `BATCH_FEATURES_CALENDAR_SERVICE = "batch_features_calendar_service"`.
2. UAC `source_priority.py`: add `("calendar", "time_features"): ["features_calendar_service"]` entry; possibly also
   `("calendar", "economic_events")` if we want to subsume FRED under the service rather than naming the upstream API
   directly.
3. Re-stamp both `time_features` and `economic_events` callsites.

**Option C — Keep current workaround + bake "approximate tag" into UAC docstring** (mirrors footystats Option B):

- Accept that calendar features carry `BATCH_INSTRUMENTS_SERVICE` until a clean enum extension lands.
- Document the approximation in UAC `pipeline_mode.py` docstring + `SOURCE_PRIORITY` so the data-status UI /
  batch-vs-live recon queries don't mis-attribute the rows.
- Phase 4.DEFAULT-REMOVAL ships cleanly (every callsite has an explicit closed-set value).
- Re-tag migration deferred until UAC adds a clean value.

**Strong recommendation** (in absence of operator direction): **Option A** for economic_events (FRED is a real external
API + the data has a well-defined release cadence — natural closed-set fit) + **Option B's
BATCH_FEATURES_CALENDAR_SERVICE** for time_features (pure-derived computed in-service rows are conceptually parallel to
BATCH_INSTRUMENTS_SERVICE's role for instruments-service self-derived catalog refreshes). Both are ~30min UAC changes;
the re-tag migration is a one-time script.

## Composes with

- `plans/archive/issues/footystats_pipeline_mode_gap_2026_05_12.md` — sister finding (different source family, same
  closed-set design call).
- `plans/active/issues/mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md` — same shape.
- `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` Phase 4.DEFAULT-REMOVAL — depends on every callsite
  resolving cleanly.
- `plans/active/manifest_schema_final_gate_2026_05_09.md` Phase 4.FEATURES — this issue blocks the clean version of the
  calendar callsite migration.
- `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 4 — umbrella owning the explicit-pipeline-mode
  rollout.
