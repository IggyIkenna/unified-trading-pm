---
doc_type: issue
title: rescan_sports_fixtures_canonical.py's FIXTURES handler never matches any real per-league blob
summary: >-
  rescan_sports_fixtures_canonical.py's per-league FIXTURES handler exact-suffix blob match never matches a real
  per-league object (only a bare date-level file), so it has silently scanned zero objects since fixtures data went
  per-league -- discovered as a pre-existing, orthogonal defect while repointing the same file's stale entity=fixtures
  references to entity=fixtures_schedule (Track E, sports_satellite_ao_dispatch_batch13_2026_08_13.md).
created: "2026-08-14"
last_updated: "2026-08-14"
author: slot-10
assigned_vm: planning
execution_scope: orchestrator-agent
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, manifest, rescan, fixtures-schedule, follow-up]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
parent_epic: sports_master
priority: P2
locked_by:
resolved_by:
source: [instruments-service/scripts/rescan_sports_fixtures_canonical.py]
status: archived
resolved_by: instruments-service@622b641628
drift_direction: advance-code
depends_on: []
---

# rescan_sports_fixtures_canonical.py FIXTURES handler suffix-match is per-league-incompatible

## What I found

While repointing `instruments-service/scripts/rescan_sports_fixtures_canonical.py`'s `_FIXTURES_HANDLER` from the dead
bare `entity=fixtures/fixtures.parquet` path to the canonical per-league
`entity=fixtures_schedule/league={L}/fixtures_schedule.parquet` layout (Track E,
`sports_satellite_ao_dispatch_batch13_2026_08_13.md`), found that `_list_entity_blob_paths()`'s blob-matching logic is
structurally incompatible with ANY per-league entity, independent of which entity name it points at:

```python
prefix = f"{FIXTURES_PREFIX}day={date_str}/{handler.prefix_suffix}" if date_str else FIXTURES_PREFIX
suffix_match = f"/{handler.prefix_suffix}{handler.blob_filename}"
...
for meta in storage.list_blobs(bucket, prefix=prefix):
    if not meta.name.endswith(suffix_match):
        continue
```

`suffix_match` requires the blob name to end EXACTLY with `/entity=<X>/<X>.parquet` — a bare date-level file. A real
per-league object (`.../entity=fixtures_schedule/league=EPL/fixtures_schedule.parquet`) ends with
`/league=EPL/fixtures_schedule.parquet` instead, so it never matches. This means the FIXTURES handler in this rescan
tool has found **zero** real objects since fixtures data went per-league (well before the 2026-07-14
fixtures_schedule/fixtures_outcomes split — FIXTURES was already written per-league under the old entity name). WEATHER
and XG handlers are unaffected — their entities are genuinely bare per-day files, so the same exact-suffix check is
correct for them.

The entity-name repoint (bare `entity=fixtures/` → `entity=fixtures_schedule/`, `instruments-service@304711c8`) is
honest — it points the handler at the live canonical location — but does not restore functionality, since the match
logic itself needs to tolerate an intervening `league={L}/` path segment.

## Why it matters

`rescan_sports_fixtures_canonical.py --entity-type FIXTURES` (single-VM, worker, and coordinator modes) silently finds
"0 files" and does nothing, with no error — anyone relying on this tool to rebuild/repair the FIXTURES manifest rows
from GCS truth gets a false "nothing to scan" instead of the real per-league data.

## Recommended decision

Fix `_list_entity_blob_paths()` to match a per-league blob shape too — e.g. check
`meta.name.endswith(f"/{handler.blob_filename}")` and that the parsed prefix contains `handler.prefix_suffix`
(tolerating an intervening `league=<L>/` segment), rather than an exact full-suffix match. Needs care not to regress
WEATHER/XG (bare per-day files, where the exact match is correct and should stay strict). Out of scope for the Track E
repoint itself (a labeling fix), this is a distinct blob-matching defect.

## Todos

- [x] [CODE] P2. ✅ Fix `_list_entity_blob_paths()` in `instruments-service/scripts/rescan_sports_fixtures_canonical.py`
      to match per-league blobs (tolerate an intervening `league={L}/` segment between `prefix_suffix` and
      `blob_filename`) for entities whose data is written per-league (FIXTURES/fixtures_schedule today), while keeping
      the existing exact match for genuinely bare per-day entities (WEATHER, XG). Add a regression test asserting
      `_list_entity_blob_paths` returns a real per-league fixtures_schedule blob path, since
      `test_entity_handlers_registered` only checks handler config, not actual matching behavior. Verify against a real
      bucket listing (or a mocked `list_blobs`) before/after. — instruments-service@622b641628, QG green. Added
      `per_league` field to `_EntityHandler`, set on `_FIXTURES_HANDLER`; `_list_entity_blob_paths` now checks
      `endswith(blob_filename)` + `prefix_suffix in name` when `per_league`, exact suffix otherwise. Two regression
      tests (mocked `list_blobs`): FIXTURES matches a real per-league blob + skips a bare-day one; WEATHER keeps the
      strict exact match (rejects a hypothetical per-league-shaped WEATHER blob). Also fixed an adjacent bug found while
      live-verifying against the real bucket: `BUCKET_NAME` was hardcoded to a bucket that doesn't exist
      (`instruments-store-sports-central-element-323112`, missing the `-prd-` segment — the SAME defect already fixed in
      `audit_fixtures_via_api_football.py`) — repointed to
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")`, instruments-service@85ca3727,
      QG green. **Live-bucket verification also surfaced a THIRD, separate defect** (upstream prefix mismatch —
      canonical writes live under an intervening `pipeline_mode=batch_api_football/` segment this handler's prefix never
      reaches) — out of scope for this todo (needs its own range-scan-safe design), filed as
      `/plans/archive/2026_08/issues/rescan_sports_fixtures_canonical_missing_pipeline_mode_prefix_2026_08_14.md`
      (resolved instruments-service@6e81874504).
