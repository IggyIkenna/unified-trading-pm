---
doc_type: issue
title: "MDPS manifest-consolidated staleness check appears inverted (age=6s flagged as >86400s)"
summary: >
  Intermittent `Error writing candles to GCS: Consolidated availability_index ... is stale (age=6s, older than
  MANIFEST_CONSOLIDATED_STALENESS_SEC=86400s)` during BITGET-FUTURES 1h backfill. The reported age (6s) is far below the
  threshold (86400s), suggesting the staleness comparison logic is inverted or comparing the wrong values. Intermittent
  — 6/250+ writes fail (2.4%).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [data-correctness, mdps, manifest, bug]
related: [/plans/active/cefi_consolidated_closeout_2026_07_18.md]
parent_epic: infrastructure_master
source:
  "Observed in VM mdps-backfill-cefi-20260810-115835 run.log during BITGET-FUTURES 1h backfill monitoring (2026-08-10)"
assigned_vm: NA
resolved_by:
locked_by:
created: 2026-08-10
priority: P3
---

## Evidence

From VM `mdps-backfill-cefi-20260810-115835` run.log, BITGET-FUTURES 1h backfill for 2026-04-20..04-30:

```
Error writing candles to GCS: Consolidated availability_index for
bucket='market-data-tick-cefi-prd-central-element-323112' is stale
(age=6s, older than MANIFEST_CONSOLIDATED_STALENESS_SEC=86400s)
```

- **age=6s** — the manifest was refreshed 6 seconds ago (fresh)
- **threshold=86400s** — staleness threshold is 24 hours
- 6s < 86400s → should NOT trigger staleness rejection
- Intermittent: 6 failures out of 250+ writes (~2.4%); most writes to the same bucket succeed

## Impact

Low — most writes succeed. But the underlying comparison bug could cause more failures under different timing conditions
or manifest-consolidator refresh patterns.

## Next Steps

- [ ] [DATA] P3. Investigate MDPS `Consolidated availability_index ... is stale` comparison logic — verify the
      age-vs-threshold comparison direction and the `MANIFEST_CONSOLIDATED_STALENESS_SEC` config value at runtime.
