---
title: "validate_manifest_coverage.py expects stale instruments_catalogue.jsonl path"
type: issue
status: open
created: 2026-05-17
author: slot-5
priority: P2
source:
  - market-tick-data-service/scripts/validate_manifest_coverage.py
  - instruments-store-tradfi-central-element-323112/_catalogue/instruments-service/day=*/manifest.json
locked_by: live-defi-rollout
---

# `validate_manifest_coverage.py` expects stale `instruments_catalogue.jsonl` path

## What I found

Running
`python3 scripts/validate_manifest_coverage.py --asset-group TRADFI --start-date 2023-04-15 --end-date 2024-12-31` fails
with:

```
google.api_core.exceptions.NotFound: 404 GET ... /b/instruments-store-tradfi-central-element-323112/o/
  instruments_catalogue.jsonl: No such object
```

The script (line 104 `_load_catalogue`) tries to download a single top-level `instruments_catalogue.jsonl` from the
instruments-store-{asset_group}-{PROJECT_ID} bucket. That file does NOT exist anywhere in the bucket. The actual
catalogue layout is per-day:

```
_catalogue/instruments-service/day=YYYY-MM-DD/manifest.json
```

i.e. one ~340-byte manifest per trading day, dating back to 2026-03-21 (verified by `list_blobs(max_results=10)`).

Additionally a separate but related bug at line 264:

```python
categories = list(_CATEGORIES) if args.all else [args.category.upper()]
```

References `args.category` but argparse declares `--asset-group` → `args.asset_group`. Fixed in `--bucket`-flag commit
(MTDS@f1621c0 — line 264 patched).

## Why it matters

- The script is referenced as the canonical Phase 6 / Phase 7 coverage gate in
  `plans/active/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md` (and earlier writegate plans).
- Without a working script the Phase 7 ≥99% gate can only be evidenced via ad-hoc python snippets against the manifest
  parquet — which slot 5 did 2026-05-17 (18/18 sampled 4-pillar green + manifest-aggregate 100% honest-fill rate /
  98.40% capture rate / 0 attempted_failed across 214,586 today rows). The ad-hoc evidence is real but the formal gate
  stays red until the script is fixed.
- Likely instruments-service catalogue layout migration (legacy single-file → per-day manifest.json) didn't update the
  script's `_load_catalogue` consumer.

## Recommended decision

Two options:

1. **Aggregate at runtime**: rewrite `_load_catalogue` to iterate `_catalogue/instruments-service/day=*/manifest.json`
   and aggregate the InstrumentRecord set across the requested [start, end] window. Cost: ~50 LOC + tests.
2. **Restore the legacy single-file**: have instruments-service write a single rollup `instruments_catalogue.jsonl` per
   asset-group bucket (consolidating the per-day manifests). Cost: instruments-service change + the per-day files stay
   as the operational source of truth.

Option 1 is simpler and keeps the script self-contained. Recommended unless instruments-service team has a different
preference.

Owner: slot 5 OR instruments-service Phase 4 owner (whoever ships the per-day manifest layout). Not blocking May-23
cutover since the Phase 7 ≥99% gate has been evidenced via the ad-hoc manifest-aggregate approach (10× faster too).

## Status taxonomy

`DEFERRED` per CLAUDE.md status taxonomy — named successor IS this issue doc; operator can dispatch as a post-cutover
small-cleanup task.
