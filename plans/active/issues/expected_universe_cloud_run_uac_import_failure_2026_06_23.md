---
title: "expected-universe-v2-* Cloud Run jobs broken — UAC import failure in new instruments-service:latest image"
created: 2026-06-23
status: active
priority: P1
locked_by: live-defi-rollout
source:
  - data_completion_to_100_all_ag_2026_06_21.md
parent_epic: manifest_master
---

## What I found

All four `expected-universe-v2-{cefi,tradfi,sports,prediction}` Cloud Run jobs failed with exit code 1 when triggered
manually on 2026-06-23 (~19:48 UTC). Root cause: the `instruments-service:latest` Docker image was updated between the
successful 01:30 UTC scheduled run and ~19:48 UTC on 2026-06-23. The new image has a broken import at line 79 of
`instruments-service/scripts/enumerate_expected_universe.py`:

```python
from unified_api_contracts import (
    DATA_TYPES_BY_ASSET_GROUP,
    GRAIN_BUNDLE_BY_UNDERLYING,
    VENUES_BY_ASSET_GROUP,
    Mode,
    bundle_instrument_type_for_leaf,
    default_transport_for_source,
    external_sources_for,
    grain_for_instrument_type,
    has_source_priority,
    is_in_mvp_capture_universe,
    pipeline_mode_for_source,
    valid_data_types_for_venue_instrument_type,
)
```

One or more of these symbols was removed or renamed in the UAC version baked into the new image. The local workspace
venv (with the current UAC source) imports successfully — confirming the image's baked UAC is the divergent version.

The workaround used: ran `enumerate_expected_universe.py` directly via the workspace `.venv` for all 4 AGs — all
exited 0 successfully.

## Why it matters

The `expected-universe-v2-*` Cloud Run jobs run on a `0 1 * * *` (01:30 UTC) cron schedule to seed
`expected_unattempted` rows in the manifest. If the new image remains broken:

- Tonight's 01:30 UTC scheduled runs will fail for all 4 AGs
- `expected_unattempted` rows stop being seeded → honest-coverage denominator becomes stale → % coverage appears
  inflated (denominator shrinks as new instruments come online without being seeded)
- This affects cefi, tradfi, sports, and prediction (all 4 non-defi AGs use this Cloud Run job)

## Recommended decision

1. **Identify the broken symbol**: diff UAC exports between the working version (local workspace) and the image's baked
   UAC. The import list above has 12 symbols — check which ones changed in recent UAC commits.
2. **Rebuild the image** from the current `instruments-service` LDR head (which imports the current local UAC correctly)
   via `create-code-tarballs.sh` + Cloud Build, and push to `:latest`.
3. **Verify**: trigger one Cloud Run execution manually for any of the 4 jobs and confirm exit 0.
4. **Until fixed**: the next scheduled 01:30 UTC runs will fail. The local workaround (workspace venv) seeded correctly
   on 2026-06-23 so no gap tonight, but the next nightly run needs the fix.

**Urgency**: HIGH — daily scheduled cron fails silently (Cloud Run exit 1 without operator alert) and the gap compounds
each day.
