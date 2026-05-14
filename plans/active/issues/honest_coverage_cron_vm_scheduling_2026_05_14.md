---
title: "honest-coverage cron VM not yet scheduled"
created: 2026-05-14
author: harsh-slot-7
source:
  - plans/active/data_status_ui_phase_2f.md
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

## What I found

`GET /api/data-status/honest-coverage` returns 404 in dev/staging. During the 6C UI-drilldown smoke
(2026-05-14), the endpoint returned 404 for today's date.

The endpoint EXISTS and is correctly implemented at
`deployment_api/routes/data_status.py:2218`. It reads
`gs://central-element-323112-honest-coverage/{date}/coverage.json` from GCS and returns 404 when the
file is not found. This is correct behavior.

**Root cause**: The cron VM (`launch-measure-honest-coverage-vm.sh`) has not run yet for today's date
in dev/staging. No GCS file exists at the expected path for 2026-05-14.

## Why it matters

The Data Status tab attempts to fetch honest-coverage for the currently selected date. The 404 causes a
UI error state display rather than a graceful "not yet computed" state. Once the cron VM runs, the
endpoint will return data correctly.

Severity: **P2** — operational gap (not a code bug). The UI should handle the 404 gracefully (shows
error, not crash), but the cron VM needs to be scheduled to produce the coverage files.

## Recommended decision

1. **Schedule `launch-measure-honest-coverage-vm.sh`** as a daily cron in `deployment-service/scripts/vm/`
   with singleton-lock pattern + watchdog dict registration.
2. **Backfill** coverage files for recent dates by running the VM manually for date range.
3. **UI**: Consider treating 404 from honest-coverage as "data not yet available" rather than error
   state (friendly message vs red error).

Suggested owner: **Ikenna** (VM launcher infra) or operator.

execution:
  owner: operator
  cadence: one-shot (VM scheduling) + daily cron
  verifier: gs://central-element-323112-honest-coverage/{date}/coverage.json exists after VM run
  last_executed: NEVER
