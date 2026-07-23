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
    /plans/active/distinct_values_noncanonical_audit_2026_07_20.md,
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

- Confirm how many days/rows are affected (this was observed for one spot-checked day, not corpus-wide).
- Decide the registry fix: add `kalshi_perp` to `SOURCE_PRIORITY[("defi", "perp_funding")]`, or confirm the asset_group
  should be something else for this venue/data_type pair.
- Once decided, ship the fix and re-run affected-day manifest rebuilds to backfill the missing rows.

## Codex SSOTs

- `/codex/02-data/defi-canonical-naming-ssot.md` (KALSHI_PERP classification)
- UAC `unified_api_contracts/canonical/crosscutting/source_priority.py` (`SOURCE_PRIORITY` registry)
