---
doc_type: issue
title: >-
  code-tarball-refresh Cloud Run Job has silently failed to update ANY tarball for at least 2 days — ModuleNotFoundError
  in the upload helper, masked because the job reports success
summary: >-
  The scheduled `code-tarball-refresh` Cloud Run Job (`*/30 * * * *`, `terraform/gcp/code_tarball_refresh_scheduler.tf`)
  has updated ZERO tarballs on every run since at least 2026-07-30T13:02Z (confirmed via Cloud Logging, ~90+ consecutive
  runs) — every repo's `gcs_upload_via_adc.py` upload step crashes with `ModuleNotFoundError: No module named
  'deployment_service'`, so `refresh_code_tarballs.sh` logs `Refresh PARTIAL — 0/N updated` and the job execution still
  reports `succeededCount=1` (the container's own exit(1) is not surfacing as a job failure). VM launchers only WARN
  (not block) on a stale tarball (`LC_TARBALL_FRESHNESS` defaults to `warn`), so every batch VM launched during this
  window may have silently run on code older than what was actually shipped to `live-defi-rollout` — discovered because
  a just-shipped features-service fix (source-bucket override,
  `features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md`) did not take effect on a real
  verification VM even though it was confirmed on `origin/live-defi-rollout`.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm-tarball-deployment, cloud-run-job, silent-failure, code-freshness, cross-cutting]
related:
  [
    plans/active/issues/features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
created: "2026-08-01"
parent_epic: infrastructure_master
priority: P0
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01-worker]
resolved_by:
locked_by:
context_scope: [/codex/05-infrastructure/vm-tarball-deployment.md]
depends_on: []
---

# code-tarball-refresh Cloud Run Job silently failing since at least 2026-07-30

## What I found

While verifying a features-service fix on a real e2e-check VM
(`features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md`), a force-leg run against a VM launched
at `2026-08-01T12:32:15Z` — well AFTER the fix (`features-service@72393fbf`) was confirmed as an ancestor of
`origin/live-defi-rollout` — still exhibited the pre-fix broken behaviour (reads hit the stale
`instruments-store-sports-stg-...` bucket). Root-caused to the VM having pulled a STALE `features-service-code.tar.gz`
from `gs://deployment-scripts-central-element-323112/code/`.

Checked the scheduled `code-tarball-refresh` Cloud Run Job (`*/30 * * * *`) directly via Cloud Logging:

```
2026-08-01T12:31:13Z [refresh-tarballs] Refresh PARTIAL — 0/10 updated; FAILED: batch-live-reconciliation-service
  deployment-service execution-service features-service instruments-service market-data-processing-service
  market-tick-data-service ml-service strategy-service unified-api-contracts
...
Traceback (most recent call last):
  File "/tmp/ds/scripts/vm/gcs_upload_via_adc.py", line 20, in <module>
    from deployment_service.vm.gcs_upload_cli import main
ModuleNotFoundError: No module named 'deployment_service'
Container called exit(1).
```

Every single run in the queried window (2026-07-30T13:02Z through 2026-08-01T12:31Z — the full extent I checked, likely
longer) shows the identical `Refresh PARTIAL — 0/N updated` failure. `gcloud run jobs executions list` nonetheless
reports `succeededCount=1, failedCount=0` for these executions — the container's own `exit(1)` on
`Container called exit(1).` is not propagating as a Cloud Run Job execution failure, so the standard job-health surface
(whatever alerting/dashboard reads `executions list`) reads GREEN the entire time.

**Root cause**: `scripts/vm/create-code-tarballs.sh`'s upload step resolves its Python interpreter as
`GCS_UPLOAD_PY="${DS_ROOT}/.venv/bin/python"`, falling back to bare `python3` only if that path is missing
(`create-code-tarballs.sh:513-514`). Inside the Cloud Run Job's container, `DS_ROOT` resolves to `/tmp/ds` (per the
traceback's `File "/tmp/ds/scripts/vm/gcs_upload_via_adc.py"`) — and that path has no `.venv/bin/python`, so it falls
back to bare `python3`, which does not have the `deployment_service` package importable (`gcs_upload_via_adc.py` imports
`from deployment_service.vm.gcs_upload_cli import main`). The actual tarball BUILD step succeeds
(`Created: execution-service-code.tar.gz (3.2M)` etc. — confirmed in the same logs); only the final
`gcloud storage`-equivalent upload via `gcs_upload_via_adc.py` crashes, for every changed repo, every run.

I also reproduced the identical failure interactively on this shared host: `.tabs/2/deployment-service` had no `.venv`
at all (same missing-venv class as `RULES.md`'s "stale sibling .venv's → uv sync" note) — after `uv sync`, the SAME
bare-`create-code-tarballs.sh --include features-service` upload succeeded cleanly. That confirms the fix class (a
working `.venv` with `deployment_service` importable resolves it) but the **production Cloud Run Job's own container
image** is the thing that needs fixing — it's not a "stale sibling venv on a dev host" instance, it's the job's own
deployed image lacking (or losing) its own venv at `/tmp/ds`.

## Why it matters

- **Cross-cutting, active, multi-day production gap**: every batch/backfill VM across every service+asset_group that
  launches via the tarball-deployment path (`launch-*.sh` scripts calling `lc_verify_tarball_freshness`) has been
  running on whatever code was tarball-current as of before 2026-07-30T13:02Z, regardless of what has shipped to
  `live-defi-rollout` since — for at least ~2 days and counting.
- **The staleness gate does not block** — `LC_TARBALL_FRESHNESS` defaults to `warn`, so launches proceed silently on
  stale code; nothing in the normal launch path would have surfaced this without someone specifically diffing real-VM
  behaviour against a just-shipped fix, as happened here.
- **The job's own health signal is false-green** — `succeededCount=1` even though the container logs its own `exit(1)`,
  so whatever monitors `code-tarball-refresh` executions for health (if anything does) would not have caught this
  either.
- Directly caused a false-negative on an UNRELATED task's verification (the sports source-bucket fix genuinely works —
  confirmed once the tarball was manually rebuilt via a direct `create-code-tarballs.sh --include features-service`
  invocation from a fixed local venv — see
  `features_sports_env_staging_reads_empty_staging_reference_data_2026_08_01.md`).

## Todos

- [ ] [INFRA] P0. Fix the Cloud Run Job's `code-tarball-refresh` container image so `gcs_upload_via_adc.py` can import
      `deployment_service` — either bake a working `.venv` at the `DS_ROOT` the container resolves (`/tmp/ds`), install
      `deployment_service` into the container's system/base Python, or make `create-code-tarballs.sh`'s `GCS_UPLOAD_PY`
      resolution robust to a missing venv (e.g. fall back to a `PYTHONPATH`-aware invocation instead of silently falling
      back to a bare interpreter that can't import the package). Verify by triggering a manual job execution and
      confirming `Refresh COMPLETE` / `N/N updated` in the logs, not `PARTIAL`. (repo: deployment-service)
- [ ] [INFRA] P0. Make a genuine upload failure inside `refresh_code_tarballs.sh` propagate as a Cloud Run Job execution
      FAILURE, not a silently-successful exit — the job currently reports `succeededCount=1` for a run that logs
      `Container called exit(1).` and `Refresh PARTIAL`. Confirm the fix by checking
      `gcloud run jobs executions     list` reports `failedCount=1` (not `succeededCount=1`) on an intentionally-broken
      reproduction. (repo: deployment-service)
- [ ] [INFRA] P1. Audit whether any VM launched since 2026-07-30T13:02Z under `LC_TARBALL_FRESHNESS=warn` (the default)
      ran on materially stale code for a repo with a real bugfix shipped in that window — cross-reference
      `vm-logs/*/TARBALL_PINS.json` / launch timestamps against each repo's `live-defi-rollout` history for that window.
      If any backfill/compute run produced data using stale (pre-fix) logic, file the resulting data- correctness gap as
      its own P0/P1 issue per the data-pipeline-correctness HARD RULE — do not silently accept it. (repo:
      unified-trading-pm)

## Codex SSOTs

`/codex/05-infrastructure/vm-tarball-deployment.md`.
