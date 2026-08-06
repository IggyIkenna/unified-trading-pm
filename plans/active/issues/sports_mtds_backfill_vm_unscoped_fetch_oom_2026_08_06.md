---
doc_type: issue
title: >-
  MTDS sports backfill VM path still runs the unscoped 30-league odds fetch (LEAGUE="") — catch-up VM
  mtds-backfill-odds-catchup-20260806 OOM-killed (exit=137) 2026-08-06; the --league scoping fix covered the live
  dispatch only, never the VM backfill path
summary: >-
  Follow-up filed from the -015 backfill dispatch on sports_fast_t1_recon_oom_live_capture_outage_2026_08_01 (slot 3,
  2026-08-06). The root-cause --league scoping fix (deployment-service@4e0e03d) scoped the LIVE fixture-proximate
  dispatch only. The backfill VM launcher (launch-mtds-sports-odds-backfill-vm.sh) still launches with LEAGUE="" (no
  --league), so a wide-window backfill runs the unscoped 30-league full-day fetch whose `all_rows` in-memory
  accumulation is the original OOM mechanism. Confirmed live: catch-up VM mtds-backfill-odds-catchup-20260806 (window
  03-28→08-06, SPOT e2-highmem-4 32GB) was SIGKILLed mid-chunk with exit=137 (CHUNK_FAILED reason=OOM_KILLED) at
  13:29:02Z after RSS climbed 4.6→30.7GiB in ~4min, before ever reaching the gap days. Does NOT re-block the -015 gap
  backfill (the gap-day VM mtds-backfill-odds-gap-20260806, 07-27→08-06 --force, completed cleanly) — it blocks any
  FUTURE wide-window backfill (e.g. the 03-28..07-26 catch-up the OOM'd VM was doing).
status: open
nature: issue
asset_group: [sports]
stage: [data, live]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [sports, data-pipeline-correctness, odds-api, oom, memory-limit, backfill, vm, follow-up]
related: [./sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md]
created: 2026-08-06
author: unknown
last_updated: 2026-08-06
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: ["-015 backfill dispatch (sports_fast_t1_recon_oom_live_capture_outage), 2026-08-06 slot 3"]
---

# MTDS sports backfill VM: unscoped 30-league odds fetch still OOMs (the --league fix never reached the VM path)

## What I found

While verifying the -015 backfill's VM terminal state (2026-08-06, slot 3), the wide-window catch-up VM
`mtds-backfill-odds-catchup-20260806` was found **OOM-killed**:

- LAUNCH_PARAMS
  (`deployment-scripts-central-element-323112/vm-logs/mtds-backfill-odds-catchup-20260806/LAUNCH_PARAMS.json`):
  `LEAGUE: ""` — the backfill ran with **no `--league` scoping**.
- run.log tail: `CHUNK_FAILED: chunk=1/1 range=2026-03-28→2026-08-06 exit=137 reason=OOM_KILLED` at 13:29:02Z;
  RESOURCE_SAMPLE RSS climbed 4.6→30.7GiB in ~4min on a busy-date fetch; EXIT_STATUS=0 is the wrapper rc, not the
  chunk's.
- The VM was SIGKILLed before reaching the gap days; it never contributed to -015's gap-day coverage.

**Why this is the original OOM bug, not a new one**: `OddsApiAdapter._fetch_all_leagues` (`odds_api_adapter.py:543-588`)
with no `--league` iterates all ~30 Prediction-tier candidate leagues, accumulating every row dict into one in-memory
`all_rows` list per day before `download_batch` materialises `pd.DataFrame(all_rows)`. The `--league` scoping fix
(`deployment-service@4e0e03d`, 2026-08-01) injects `--league=<id>` into the LIVE fixture-proximate dispatch
(`SportsTriggerScheduler.fire_trigger` → `_dispatch_services`), but the **backfill VM launcher
(`deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh`) never passes `--league`** — `VM_LEAGUE`
metadata is only emitted when the operator supplies `--league` to the launcher, and the -015/-catchup launches did not.

## Why it matters

The memory-limit stop-gap (16Gi) masks the defect on the live Cloud Run Job, but a SPOT backfill VM has no such cap — a
wide-window unscoped backfill reliably OOMs the process (and on a SPOT VM, OOM ≠ preemption, so the RelaunchPreemptedVm
recovery does not apply — it just dies and re-runs from scratch, wasting the whole window). Any future wide-window odds
backfill (e.g. the 03-28..07-26 catch-up this VM was attempting) will fail the same way until this is fixed.

## Recommended decision

Fix the backfill VM path so a wide-window odds backfill cannot OOM, then (optionally) re-run the 03-28..07-26 catch-up.

- [ ] [DATA] P2. Fix the backfill VM path's unscoped odds fetch: `launch-mtds-sports-odds-backfill-vm.sh` launches with
      `LEAGUE=""` so a wide-window backfill runs the unscoped 30-league full-day fetch and OOMs (confirmed:
      `mtds-backfill-odds-catchup-20260806` exit=137 RSS→30.7GiB 2026-08-06 — same `all_rows` accumulation-OOM the
      `--league` fix at `deployment-service@4e0e03d` eliminated on the live dispatch but never mirrored to the VM path).
      Options: (a) per-league sharded launches passing `--league` (full coverage = up to ~30 VMs), or (b) stream-write
      in the odds fetch loop (mirror the `writer=`-based streaming path noted in
      `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`'s root-cause section) so `all_rows` never
      materialises a whole day in memory. Done when: a wide-window backfill VM completes without OOM. (repo:
      market-tick-data-service, deployment-service)
