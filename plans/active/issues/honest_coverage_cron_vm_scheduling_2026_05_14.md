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

`GET /api/data-status/honest-coverage` returns 404 in dev/staging. During the 6C UI-drilldown smoke (2026-05-14), the
endpoint returned 404 for today's date.

The endpoint EXISTS and is correctly implemented at `deployment_api/routes/data_status.py:2218`. It reads
`gs://central-element-323112-honest-coverage/{date}/coverage.json` from GCS and returns 404 when the file is not found.
This is correct behavior.

**Root cause**: The cron VM (`launch-measure-honest-coverage-vm.sh`) has not run yet for today's date in dev/staging. No
GCS file exists at the expected path for 2026-05-14.

## Why it matters

The Data Status tab attempts to fetch honest-coverage for the currently selected date. The 404 causes a UI error state
display rather than a graceful "not yet computed" state. Once the cron VM runs, the endpoint will return data correctly.

Severity: **P2** — operational gap (not a code bug). The UI should handle the 404 gracefully (shows error, not crash),
but the cron VM needs to be scheduled to produce the coverage files.

## Recommended decision

1. **Schedule `launch-measure-honest-coverage-vm.sh`** as a daily cron in `deployment-service/scripts/vm/` with
   singleton-lock pattern + watchdog dict registration.
2. **Backfill** coverage files for recent dates by running the VM manually for date range.
3. **UI**: Consider treating 404 from honest-coverage as "data not yet available" rather than error state (friendly
   message vs red error).

Suggested owner: **Ikenna** (VM launcher infra) or operator.

execution: owner: operator cadence: one-shot (VM scheduling) + daily cron verifier:
gs://central-element-323112-honest-coverage/{date}/coverage.json exists after VM run last_executed: NEVER

## Resolution

**UI half ✅ RESOLVED** (2026-05-14 — harsh-slot-7 Wave 2):

- `deployment-ui@365c32f` — `HonestCoverageCard.tsx` now renders a neutral info card "Coverage data not yet computed for
  {date}." (with `Info` icon) when the 404 path returns null, replacing the prior silent-hide behavior. Recommended
  decision #3 implemented.

**Cron VM half ✅ RESOLVED** (2026-05-15 — slot-2):

- `deployment-service@19454f1` — `terraform/gcp/honest_coverage_scheduler.tf` adds Cloud Run Job + Cloud Scheduler at
  `0 30 * * * UTC`. The job runs `gcr.io/google.com/cloudsdktool/google-cloud-cli:alpine`, downloads
  `launch-measure-honest-coverage-vm.sh` from `gs://deployment-scripts-{pid}/vm/` and executes it. The bash script
  creates the GCE measurement VM which writes `gs://{pid}-honest-coverage/{date}/coverage.json`. Cron half of
  Recommended decision #1 closed.
- Watchdog dict registration (`measure-honest-coverage-` prefix in `vm_zombie_watchdog.py` at line 570) was already in
  place — re-verified 2026-05-15.
- **Backfill** (Recommended decision #2): one-shot operator concern. Pinging slot-2 to confirm whether one historical
  backfill run is queued; otherwise the first scheduled run on 2026-05-16 00:30 UTC seeds today's file and forward.

**Slot-8 collision note** (2026-05-15): slot-8 (ikenna side) independently shipped a Python launcher
(`deployment-api@d6e72c6`) before discovering slot-2's terraform. Reverted at `deployment-api@3afc016`. Slot-2's bash
approach is canonical (simpler, no dep on deployment-api image).
