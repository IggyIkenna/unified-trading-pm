---
doc_type: issue
title: KALSHI_PERP perp_funding manifest emits fail — source='kalshi_perp' not registered for (defi, perp_funding)
summary: >-
  Discovered live during a scoped defi-rebuild pass for day=2026-07-22: every KALSHI_PERP perp_funding object
  (KXBCHPERP/KXBTCPERP/KXDOGEPERP/KXETHPERP/KXHYPEPERP) fails manifest emission with "source='kalshi_perp' which is not
  a registered source for asset_group='defi' data_type='perp_funding'. Allowed: ['hyperliquid']" — the objects exist on
  GCS and are written under asset_group=defi, but SOURCE_PRIORITY[(defi, perp_funding)] only lists hyperliquid, so these
  rows never enter the manifest at all (silent, logged-and-skipped, not a crash).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [defi, kalshi-perp, source-priority, manifest, registry-gap]
related:
  [
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-23
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineer
drift_direction: worsening-slowly
depends_on: []
resolved_by:
locked_by:
source: ["discovered live during defi_consolidated_closeout_2026_07_18.md's manifest rebuild work, 2026-07-23"]
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/source_priority.py,
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_perp_funding_kalshi_polymarket.py,
  ]
---

# KALSHI_PERP perp_funding manifest emits fail — source not registered

## What was measured (live, during a scoped defi-rebuild for day=2026-07-22)

`rebuild_defi_manifest` logged, for every KALSHI_PERP perp_funding object on that day:

```
manifest emit failed for raw_tick_data/by_date/day=2026-07-22/pipeline_mode=batch_kalshi_perp/asset_group=defi/
venue=KALSHI_PERP/chain=KALSHI_PERP/instrument_type=perpetual/data_type=perp_funding/KXBCHPERP.parquet:
Manifest write passed source='kalshi_perp' which is not a registered source for asset_group='defi'
data_type='perp_funding'. Allowed (UAC SOURCE_PRIORITY batch sources + live/replay vendors): ['hyperliquid'].
```

Same failure for KXBTCPERP, KXDOGEPERP, KXETHPERP, KXHYPEPERP — every KALSHI_PERP market symbol seen that day. The
objects themselves ARE written to GCS (confirmed present at the cited path); only the MANIFEST ROW never gets created,
so this data is invisible to any manifest-driven reader/coverage calculation.

## Likely relationship to the existing census finding

This directly parallels the `KALSHI_PERP`/`POLYMARKET_PERP` asset_group-classification ambiguity already documented in
`distinct_values_noncanonical_audit_2026_07_20.md` (KALSHI_PERP appears under BOTH defi and cefi in different contexts,
with an operator KEEP ruling preserving existing stamps rather than reclassifying). This writer stamps KALSHI_PERP's
perp_funding capture as `asset_group=defi` with `source=kalshi_perp`, but
`unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY[("defi", "perp_funding")]` only lists
`hyperliquid` as a registered source — so either (a) `kalshi_perp` needs adding to that SOURCE_PRIORITY entry, or (b)
KALSHI_PERP's perp_funding capture should be stamped under a different asset_group entirely (matching whatever the
eventual resolution of the broader classification question turns out to be). Not resolved here — this doc records the
concrete, currently-failing symptom; the classification question is the census audit's to rule on.

## Not yet done

- **UPDATED 2026-07-28 (slot-16) — corpus-wide scope now measured, replacing the single-day framing.** Scanned GCS under
  the scoped prefix `raw_tick_data/by_date/day=<D>/pipeline_mode=batch_kalshi_perp/asset_group=defi/venue=KALSHI_PERP/`
  (single-prefix listing per day, never a whole-corpus walk). A bucket-root delimiter-descent first confirmed exactly
  2,400 `day=` partitions total (2020-01-01..2026-07-27); the per-day scoped scan below was bounded to that window,
  live-verified empty on both edges (back through 2026-01-01, forward through 2026-07-27) rather than assumed:
  - **Full affected window: 2026-05-29 through 2026-07-25** (55 of 58 calendar days in that span carry >=1 KALSHI_PERP
    defi-labeled object). Confirmed **zero** objects before 2026-05-29 and **zero** from 2026-07-26 onward — the latter
    confirms the `market-tick-data-service@2aa23de5` cefi-reroute fix (already shipped earlier in this same batch1 plan)
    took effect for new writes: no further DEFI-asset_group KALSHI_PERP objects appear after it landed.
  - **13 distinct real perp symbols observed, not 5** (this doc's original single-day spot-check only saw the 5 that
    happened to exist on 2026-07-22). Coverage grew in 3 steps: `KXBTCPERP/KXETHPERP/KXSOLPERP/KXXRPPERP` from
    2026-06-03; `+KXHYPEPERP` from 2026-06-08; `+KXBCHPERP/KXDOGEPERP/KXKSHIBPERP/KXLINKPERP/KXLTCPERP/KXSUIPERP` from
    2026-06-09 (11 symbols, steady through 2026-06-23); `+KXNEARPERP/KXZECPERP` from 2026-06-24 (13 symbols, steady
    through the last active day 2026-07-25). 2026-05-29 through 2026-06-02 carry no real-symbol data yet (see marker
    finding below).
  - **TOTAL (day, symbol) GCS-present instances: 567** across the 13 real symbols.
  - **3 zero-object gap days inside the otherwise-daily-cadence active window**: 2026-07-17, 2026-07-20, 2026-07-21 —
    not root-caused here (read-only audit scope); tracked as a new follow-up below.
  - **Secondary finding — non-symbol marker objects**: a `_migrated_kalshi_perp_<UTC-timestamp>.parquet` object (one per
    day, e.g. `_migrated_kalshi_perp_20260714182652`) appears under the SAME scoped venue prefix every day from
    2026-05-29 through 2026-07-16 (57 total instances), then stops appearing entirely from 2026-07-17 onward. Not a real
    perp market symbol — reads as a one-off migration/backfill script's marker artifact left in the live data path. Not
    root-caused here; tracked as a new follow-up below.
  - **Manifest-side cross-check**: streamed the full DEFI availability manifest (26,978,131 rows,
    `market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`, never materialized whole) and
    confirmed **zero** rows with `venue=KALSHI_PERP` (any `data_type`) — every one of the 567 GCS-present (day, symbol)
    instances above is manifest-absent, with no exceptions. (The 4 stale pre-existing KALSHI_PERP/ POLYMARKET_PERP
    manifest rows this same batch1 plan's `remove_kalshi_polymarket_defi_manifest_rows_2026_07_26.py` cleanup removed
    are confirmed gone via this same live read.)
- Decide the registry fix: add `kalshi_perp` to `SOURCE_PRIORITY[("defi", "perp_funding")]`, or confirm the asset_group
  should be something else for this venue/data_type pair. **Effectively already decided for NEW writes**: the routing
  fix shipped earlier in this batch1 plan (`market-tick-data-service@2aa23de5`) reroutes captures to `asset_group=cefi`
  instead (option b) — confirmed live above (zero new defi-labeled objects after 2026-07-26). **Still open**: whether
  the 567 already-written, still-GCS-present, still-manifest-absent 2026-05-29..2026-07-25 DEFI objects above should be
  (a) backfilled into the DEFI manifest as-is, (b) migrated/re-emitted into the CEFI manifest to match the new routing,
  or (c) left as an accepted historical gap — an operator/design decision, not resolved here.
- Once decided, ship the fix and re-run affected-day manifest rebuilds to backfill the missing rows.

## Follow-up (filed 2026-07-28, from the corpus-wide scope audit above)

- [ ] [DIAG] P2. Root-cause the 3 zero-object gap days inside the KALSHI_PERP defi capture window (2026-07-17,
      2026-07-20, 2026-07-21) — check the collector's run logs/cron history for those UTC days to determine whether each
      is a transient fetch failure (worth a `record_failed`/backfill) or an intentional pause, and whether the gap is
      visible anywhere downstream today. Repo: market-tick-data-service.
- [ ] [DIAG] P2. Root-cause the daily `_migrated_kalshi_perp_<timestamp>.parquet` marker object written into the live
      KALSHI_PERP venue prefix (2026-05-29 through 2026-07-16, 57 instances, then stops) — identify which migration/
      backfill script wrote it, confirm it is inert (no reader depends on it) or needs cleanup, and whether its abrupt
      stop on 2026-07-17 is related to the gap-day finding above. Repo: market-tick-data-service.

## Codex SSOTs

- `/codex/02-data/defi-canonical-naming-ssot.md` (KALSHI_PERP classification)
- UAC `unified_api_contracts/canonical/crosscutting/source_priority.py` (`SOURCE_PRIORITY` registry)

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - the doc's central open item is a prose-only (a)/(b)/(c)
  operator-design decision on 567 already-written manifest-absent objects; the 2 checkbox DIAGs are bounded but
  secondary
- **context-scout 2026-08-01**: populated context_scope (4 entries).
