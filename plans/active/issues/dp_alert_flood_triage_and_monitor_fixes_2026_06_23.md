---
title: DP #data-pipeline-alerts flood — real-vs-false triage + monitor signal fixes (2026-06-23)
created: 2026-06-23
author: ikennaigboaka [autonomous-infra-fix]
source:
  - alerts.log (830 lines, 2026-06-23 #data-pipeline-alerts flood)
  - aggregated AG-agent prompts (deadman crash / tradfi fleet-monitor false-positives / alert-lifecycle gaps)
parent_epic: mtds_mdps_master
priority: P1
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-23
---

## What I found

`alerts.log` is **5 alert classes** (de-duping grep artifacts). Live GCS/Cloud-Run direct-checks (ADC, 2026-06-23
~20:50Z) classify each as a **monitor-signal false-positive** vs a **REAL outage the monitor correctly reports** — they
are a MIX, so blanket "fix the monitors" would have HIDDEN real problems:

| Class                                        | n   | Verdict               | Live evidence (2026-06-23)                                                                                                                                                                                                                      | Action                                   |
| -------------------------------------------- | --- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `DP_VM_STALL`                                | 115 | **FALSE** (fixed)     | tradfi-bf VM captured 114k rows + on-box `PIPELINE_HEARTBEAT`/60s, but the watcher's GCS-tee'd run.log lagged ~42m → false "heartbeat 42m stale"                                                                                                | **SHIPPED** deployment-service@`6b76244` |
| `DP_CRON_DID_NOT_FIRE` [consolidator-tradfi] | 28  | **FALSE / transient** | scheduler ENABLED `*/1`, last attempt 20:50:04; Cloud Run exec completed 20:49:40; `_index/availability_index.parquet` updated 20:51:56 (fresh)                                                                                                 | alert-lifecycle hardening (below)        |
| `DP_VM_GONE_NO_CAPTURE`                      | 26  | **likely REAL**       | `tradfi-es-2024-futures` "drained, captured 0→0, no rows written" — the silent-0-row tradfi class (`--source` not forwarded → `TickDataHandler` raises)                                                                                         | investigate (below)                      |
| `DP_CATALOG_NOT_RUNNING` [tradfi]            | 18  | **REAL**              | regen `lifecycle-catalogue-regen-tradfi` SUCCEEDS (17:19/17:06/…, re-ran `ncct7` 20:51 → succeeded) but `instruments-store-tradfi-prd/prod/catalog.parquet` is FROZEN at **2026-06-17** (6d; budget 24h). Monitor is CORRECT.                   | regen write-path bug (below)             |
| `DP_ZOMBIE_WATCHDOG_DOWN`                    | 4   | **FALSE / transient** | `vm-zombie-watchdog-…171612` RUNNING; census `gs://deployment-scripts-…/vm-census/watchdog-census.json` fresh (20:46, 4m). Monitor reads the CORRECT bucket (`_log_bucket()` = `deployment-scripts-<proj>`) — it was briefly stale at fire-time | alert-lifecycle hardening (below)        |

**`monitoring-deadman` (separate channel, not the #data-pipeline-alerts flood):** the `uts-prod-monitoring-deadman`
Cloud Run job FAILED every `*/15` run (X/X, 0/1). Root cause: `deadman_poster.py:343` entered
`run_lifecycle(service_name="monitoring-deadman")` → UTL `run_lifecycle` calls `log_event` WITHOUT `setup_events()` →
`RuntimeError("Event logging not initialized")`. The deadman is the **out-of-band** watcher whose own docstring forbids
`log_event`/PubSub (it must be independent of the path it monitors), and GCP-native execution-absence alerting is its
bedrock — so the fix is to REMOVE `run_lifecycle` (its sibling out-of-band monitors use none) + honor "never raises,
exits 0 always". **SHIPPED** deployment-service@`9b32ea5`.

## Why it matters

The flood reads as "monitoring tools broken/unconfigured" (operator). Most classes are monitors reading a signal that's
fresh-but-they-mis-time, OR a genuinely stale artifact — but DP_CATALOG-tradfi + DP_VM_GONE are REAL data outages the
monitor correctly pages. Silencing them would mask a 6-day-stale tradfi instrument catalogue. The data pipeline is the
heartbeat — real issues get fixed, not hushed.

## Shipped (this pass, all QG-green + tested, draining LDR→staging)

1. **Deadman crash** — `deadman_poster.py` drop `run_lifecycle` + exit-0 contract — deployment-service@`9b32ea5`.
2. **DP_VM_STALL authoritative signal** — `heartbeat_stall_watcher.classify_vm_liveness` + `is_vm_progressing` now key
   on the **per-VM manifest-shard mtime** (`_index/per_vm/{vm}.parquet`, written DIRECTLY to GCS as the worker captures,
   ~60s, low-lag): a fresh shard OVERRIDES a stale tee'd `PIPELINE_HEARTBEAT` → a capturing VM never false-stalls AND is
   never auto-killed; fail-safe `None` ⇒ heartbeat/run.log signals still catch a non-writing VM. Wired in `cli.py`
   (`_make_shard_mtime_reader` via `_gcs.blob_age_minutes`). +3 unit tests. deployment-service@`6b76244`.
3. **cefi backfill venues** — `launch-cefi-sharded-backfill.sh` default += `BYBIT-SPOT`, `COINBASE-FUTURES`.

## Open work (tracked todos)

- [ ] [DEPLOY] P0. **deployment-service LDR is 170 commits ahead of main** → `deployment-api:latest` (which the
      deadman + dp-fleet-monitor Cloud Run jobs run) won't carry the shipped fixes until the promotion backlog drains to
      `main` (the image rebuilds on main via cloudbuild.yaml/semver-agent). Either drain the backlog or do a manual
      `deployment-api:latest` rebuild, then re-execute `uts-prod-monitoring-deadman` + confirm 1/1 green and DP_VM_STALL
      subsides. **Live verification of the deadman/flood is blocked on this.**
- [ ] [DATA] P1. **DP_CATALOG-tradfi REAL**: `lifecycle-catalogue-regen-tradfi` succeeds but does NOT update
      `instruments-store-tradfi-prd/prod/catalog.parquet` (frozen 2026-06-17). Find the regen write-path divergence
      (instruments-service `build_instrument_catalogue.py` tradfi branch vs the consumer path
      `-prd-/prod/catalog.parquet` that CEFI reads fresh) and fix so the regen actually refreshes the consumed object.
- [ ] [MONITOR] P1. **Alert-lifecycle hardening** (root fix for DP_CRON + DP_ZOMBIE transient false-positives + any
      self-resolving DP_CATALOG/DP_VM_GONE): in `data_pipeline_monitors/escalation.py` (route_finding) + the watchers,
      (a) RE-PROBE the condition immediately before firing (catch the already-resolved case), and (b) post a
      RESOLVED/INFO bookend when a previously-fired condition clears (mirror
      `scripts/repo-management/ci_failure_watcher.py` RESOLVED bookend). Drives the transient flood to zero WITHOUT
      silencing a real persistent stall.
- [ ] [DATA] P1. **DP_VM_GONE-tradfi**: confirm whether `tradfi-es-2024-futures` genuinely captured 0 (the silent-0-row
      `--source`-not-forwarded class — `VM_TASK=mtds-backfill` + `VM_SOURCE` + `setup-data-pipeline-vm.sh --source`
      forwarding) vs a manifest-read miss; fix the wrong side.
- [ ] [MONITOR] P2. **TRADFI HTTP-hang defensive hardening** (market-tick-data-service): bound every outbound
      Databento/HTTP call (`timeout=`) + wrap the per-shard fetch in `asyncio.wait_for` so a stall fails the shard
      (attempted_failed + `classify_venue_error`), never the VM. NOTE the VMs are currently HEALTHY (the DP_VM_STALL
      flood was the lagging-tee false-positive, now fixed) — this is defence-in-depth, not the live incident.

## Recommended decision

Land the shipped fixes to `main` (drain the deployment-service promotion backlog OR manual image rebuild) → re-execute
the deadman + confirm green. Treat DP_CATALOG-tradfi + DP_VM_GONE as REAL data issues (do NOT silence). Build the
re-probe+RESOLVED-bookend alert-lifecycle hardening as the systemic fix for transient false-positives.
