---
title: "instruments-service orchestrator: recovery_fixture_ids does not bypass zero-fixture fast path"
created: 2026-05-14
author: slot-2-api-football
source:
  - instruments_service/engine/orchestrator.py
severity: P2
suggested_owner: instruments-service maintainer
---

## What I found

`instruments-service` orchestrator has a zero-fixture fast path: when
`_read_fixture_ids_from_gcs(bucket, date)` returns an empty list (no completed fixtures in GCS for that date), the
orchestrator writes `empty_confirmed` for all leagues and calls:

```python
_fetch_sports_reference_data(fixture_ids_override=[])
```

The `fixture_ids_override=[]` is **hardcoded empty** — it **does not use** the `--recovery-fixture-ids` GCS parquet
path passed via CLI. The `recovery_fixture_ids` argument is an allowlist FILTER applied after `_read_fixture_ids_from_gcs`
populates the list; when that list is empty, the filter has nothing to work with.

**Consequence**: Running the VM in "recovery mode" with `--recovery-fixture-ids <parquet>` does NOT override
the zero-fixture path. If GCS fixtures parquet for the date has no completed fixtures, the VM exits in ~22 seconds
with zero data regardless of the recovery fixture list provided.

**Observed in Phase 3.C (2026-05-14)**: VM `af-backfill-20260514-102928` was launched with
`--recovery-fixture-ids gs://instruments-store-sports-central-element-323112/_smoke_test/phase3c_recovery_fixtures.parquet`
(containing af_fixture_id=1379275, Man City vs Crystal Palace EPL FT). GCS fixtures parquet for 2026-05-13 only had
LA_LIGA NS rows. VM completed in ~22s with no FIXTURE_STATS written.

**Workaround applied (2026-05-14)**: Added the EPL fixture row directly to the GCS fixtures parquet
(`sports_reference/by_date/day=2026-05-13/entity=fixtures/fixtures.parquet`). Then ran `--entity FIXTURE_STATS`
VM which correctly read the fixture from GCS and wrote 2-row × 23-col parquet.

## Why it matters

- `--recovery-fixture-ids` is documented as a way to reprocess specific fixtures without running the full day
- If the date's GCS fixtures file is missing or incomplete (common for backfill scenarios), the recovery mode
  silently does nothing — operator has no indication that recovery was bypassed
- This makes the recovery workflow unreliable for dates where the primary fixtures parquet is stale or absent

## Recommended decision

**Fix**: In orchestrator's zero-fixture path, check if `recovery_fixture_ids` is provided; if so, use those
IDs directly instead of the `fixture_ids_override=[]` empty list. The zero-fixture path should only apply when
BOTH `_read_fixture_ids_from_gcs` returns empty AND no `recovery_fixture_ids` are provided.

```python
# Current (broken):
if not fixture_ids:
    _fetch_sports_reference_data(fixture_ids_override=[])

# Fix:
if not fixture_ids and not recovery_fixture_ids:
    _fetch_sports_reference_data(fixture_ids_override=[])
elif not fixture_ids and recovery_fixture_ids:
    # Use recovery IDs directly — read from parquet and pass as override
    fixture_ids = _load_recovery_fixture_ids(recovery_fixture_ids)
    _fetch_sports_reference_data(fixture_ids_override=fixture_ids)
```

Actual fix may differ depending on orchestrator architecture — maintainer should confirm exact call path.
