---
doc_type: issue
title: "298 duplicate HYPERLIQUID full-year backfill VMs running simultaneously — active billing-waste runaway, not a normal fleet"
summary:
  "AUDIT (infra, slot-8, 2026-08-16, AO task coverage_floor_registries_no_cross_propagation-8f678c46ae69, while
  checking on the HYPERLIQUID re-verify Follow-up in coverage_floor_registries_no_cross_propagation_2026_07_17.md).
  FINDING: 298 `cefi-hyperliquid-2023-*` VMs (all `e2-highmem-4`) are RUNNING right now, all launched via
  `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`, all carrying the IDENTICAL metadata
  (`VM_START_DATE=2023-01-01 VM_END_DATE=2023-12-31 VM_VENUE=HYPERLIQUID VM_TASK=cefi-hl-aster-backfill
  VM_FORCE=false`) — sampled 4 VMs at random from across the fleet, all 4 identical. This is not a legitimate sharded
  fleet (which would carry distinct date ranges per VM, as the earlier 2026-08-15 7-shard launch correctly did) — it
  is the SAME full-year job launched ~40+ times over. Creation-timestamp histogram shows a runaway acceleration, not
  a single launch: 2 VMs at 19:00Z (08-15), climbing to 188 VMs in the single hour 02:00-03:00Z (08-16). Fleet count
  exceeds the script's own `MAX_CONCURRENT=250` default, consistent with multiple concurrent invocations racing past
  a per-invocation-only concurrency guard. Root cause not fully isolated within this task's scope (no cron/systemd
  timer found on this host referencing hyperliquid; likely repeated AO-worker-session launches against the same
  `cefi_hl_aster_batch_data_gaps_2026_06_22.md` / `coverage_floor_registries_no_cross_propagation_2026_07_17.md`
  HYPERLIQUID re-verify Follow-up without adequately checking for an existing fleet first, per the STEP 0.65
  guardrail in `agents/infra.md` — the prior 2026-08-15 7-shard launch was correctly zero-checked and scoped;
  something after it was not). The launcher script itself has NO built-in cross-invocation duplicate-detection —
  `MAX_CONCURRENT` only bounds parallel subprocess launches WITHIN one script run, not across separate invocations;
  the zero-pre-existing-fleet check is entirely a caller-side manual discipline with no code-level enforcement."
status: open
priority: P0
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [billing-waste, vm-launcher, runaway, duplicate-launch, hyperliquid, cefi, infra]
related:
  [
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
  ]
created: 2026-08-16
author: unknown
parent_epic: mtds_mdps_master
source:
  "infra worker (slot-8, planning VM), 2026-08-16, AO task coverage_floor_registries_no_cross_propagation-8f678c46ae69.
  Discovered while checking the fleet status for the HYPERLIQUID re-verify Follow-up in the coverage-floor issue doc.
  Direct `gcloud compute instances list --filter=\"name~'hyperliquid'\"` (298 RUNNING), `gcloud compute instances
  describe` metadata sampling on 4 VMs spread across the creation-time range (all identical VM_START_DATE/VM_END_DATE),
  creation-timestamp histogram, and a read of
  `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` for guard logic."
locked_by:
resolved_by:
execution_scope: orchestrator-agent
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh,
    /plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
  ]
---

## What I found

298 `cefi-hyperliquid-2023-*` VMs are `RUNNING` right now (`gcloud compute instances list --filter="name~'hyperliquid'"`,
verified live, 2026-08-16). Every sampled VM (`cefi-hyperliquid-2023-20260816-020053`,
`cefi-hyperliquid-2023-20260816-030139`, `cefi-hyperliquid-2023-20260816-040143`,
`cefi-hyperliquid-2023-20260816-070206` — spread across the creation-time range, not clustered) carries IDENTICAL
metadata:

```
VM_ASSET_GROUP = cefi
VM_DATA_TYPES = trades;book_snapshot_5;derivative_ticker
VM_END_DATE = 2023-12-31
VM_FORCE = false
VM_INSTRUMENT_IDS = ALL
VM_OPERATION = collect-onchain-perp-batch
VM_SERVICE = market_tick_data_service
VM_TASK = cefi-hl-aster-backfill
VM_VENUE = HYPERLIQUID
VM_START_DATE = 2023-01-01
```

Every one of these 298 VMs is doing the exact same full-year (2023-01-01 → 2023-12-31) HYPERLIQUID backfill —
not a legitimate date-sharded fleet (compare the correctly-scoped 2026-08-15 7-shard launch documented in
`coverage_floor_registries_no_cross_propagation_2026_07_17.md`'s Progress Log, which used 7 distinct 30-day
`OVERRIDE_START_DATE`/`OVERRIDE_END_DATE` windows).

Creation-timestamp histogram (`gcloud ... --format="value(name,creationTimestamp)"`, grouped by hour):

```
2026-08-15T19  →   2
2026-08-15T20  →   5
2026-08-15T21  →  20
2026-08-15T22  →   9
2026-08-15T23  →  19
2026-08-16T00  →  36
2026-08-16T01  →  19
2026-08-16T02  → 188   ← acceleration, not a single burst launch
```

All 298 are `e2-highmem-4`. This total also EXCEEDS the launcher script's own `MAX_CONCURRENT=250` default
(`launch-cefi-hl-aster-historical-backfill.sh:69`) — consistent with several independent invocations of the script
running concurrently, each racing past its own per-invocation subprocess cap with no cross-invocation awareness.

**Root-cause mechanism (not fully isolated within this task's scope)**: no cron/systemd timer on this host
references hyperliquid. The most likely explanation, given the surrounding Progress Log in
`coverage_floor_registries_no_cross_propagation_2026_07_17.md`, is that multiple separate AO-dispatched worker
sessions across the fleet — each independently working the same HYPERLIQUID re-verify Follow-up (visible: slot-6,
slot-18, slot-22, slot-23, slot-25 all touched this exact Follow-up across 2026-08-15/16) — repeatedly decided to
"relaunch the backfill" without adequately verifying zero pre-existing fleet VMs first, in violation of the STEP 0.65
guardrail (`unified-trading-pm/agents/infra.md`) and the general "no fire-and-forget, verify fleet-empty before
launch" VM-launcher rule. The 2026-08-15 7-shard launch (slot-6) WAS correctly zero-checked and narrowly scoped
(7 VMs, distinct 30-day windows) — whatever produced the subsequent 291+ full-year-duplicate VMs was not.

**Script-level gap**: `launch-cefi-hl-aster-historical-backfill.sh` has no built-in cross-invocation
duplicate-detection. `MAX_CONCURRENT` (line 69) only throttles parallel subprocess launches WITHIN a single script
run (`wait_for_slot()` waits on `running_jobs`, a script-local bash variable) — it does nothing to prevent a SECOND
invocation of the script from launching an entirely parallel set of VMs for the identical venue/date range. The
"verify zero pre-existing fleet VMs first" check that WOULD have caught this is entirely a caller-side manual
discipline (documented in `infra.md` STEP 0.65 and the general VM-launcher runbook), with no code-level enforcement
in the launcher itself.

## Why it matters

This is active, ongoing GCP billing waste at meaningful scale — up to ~298 `e2-highmem-4` VMs simultaneously, all
computing the literal same result, growing hour over hour. Every VM beyond the first doing this exact
(venue, date-range) job is 100% wasted spend; even at SPOT pricing (default `ON_DEMAND=false`) this is dozens of
dollars per hour and rising. It also risks corrupting the underlying investigation: with hundreds of VMs writing to
the same manifest shard concurrently, per-VM shard write contention/duplication is untested at this scale, and the
fleet may itself interfere with legitimate progress tracking (the very Follow-up task this fleet was launched to
serve keeps re-diagnosing "is this a stall or real progress" against a moving, uncoordinated target).

## Recommended decision

1. **Immediate**: an operator or infra worker with delete authority should identify and terminate the duplicate VMs,
   keeping at most one active full-year (or properly-sharded) run for HYPERLIQUID 2023. This task did NOT delete any
   VMs itself — per the STEP 0.65 guardrail, deleting VMs in this task's own fleet requires confirming genuine
   staleness first, and here the VMs are NOT stale (they are actively running, just duplicated), so the delete
   decision needs a human call on which run to keep and needs care to avoid corrupting whichever run(s) are kept.
2. **Root-cause fix (code)**: add a cross-invocation guard to `launch-cefi-hl-aster-historical-backfill.sh` (or a
   shared `lib/launcher_common.sh` helper reusable by sibling launchers) that checks
   `gcloud compute instances list --filter="name~'<venue-prefix>'"` for already-running VMs matching the SAME
   `(venue, start_date, end_date)` before launching, and refuses (or prompts) rather than silently piling on a
   duplicate fleet. This closes the gap the manual STEP 0.65 discipline alone has now visibly failed to catch at
   least once.
3. **Process**: cross-reference the HYPERLIQUID re-verify Follow-up's own Progress Log entries (slot-6/18/22/23/25)
   against actual `gcloud` fleet history to determine which session(s) triggered the extra launches, so the same
   failure mode doesn't recur on the next re-check of that Follow-up.

## Todos

- [ ] [OPERATOR] P0. Review the live `cefi-hyperliquid-2023-*` fleet (298+ VMs as of 2026-08-16, growing) and
      terminate the duplicates, keeping one coherent run. Needs a human call on which specific run-id(s) to preserve
      and safe termination of the rest without corrupting in-flight manifest writes. (repo: infra ops, no code)
- [x] ✅ [INFRA] P1. Add a cross-invocation "is this (venue, date-range) already running?" guard to
      `deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` (and consider hoisting into
      `lib/launcher_common.sh` for reuse by sibling launchers) so a second invocation for an identical range refuses
      or requires an explicit override instead of silently launching a parallel duplicate fleet. (repo:
      deployment-service) — deployment-service@246fa62319: added `lc_metadata_singleton_check()` to
      `launcher_common.sh` (metadata-scoped, unlike the existing prefix-only `lc_singleton_check`, so legitimate
      concurrent year/date shards under one venue prefix are NOT blocked) and wired it into `_launch_vm` so a
      RUNNING VM already carrying the same VM_VENUE/VM_START_DATE/VM_END_DATE refuses the duplicate launch (override
      via FORCE=true). QG green (244s). Verified dry-run + shellcheck clean.
- [ ] [DATA] P2. Once the duplicate fleet is resolved to a single coherent run, re-verify HYPERLIQUID captured-row
      coverage for the 2023-06-14..2023-12-31 window (the original ask in
      `coverage_floor_registries_no_cross_propagation_2026_07_17.md`'s open Follow-up) against that single run's
      completion. (repo: market-tick-data-service / deployment-service)

## Progress Log

- **slot-8 2026-08-16**: filed this issue doc after discovering the runaway fleet while checking status for
  `coverage_floor_registries_no_cross_propagation_2026_07_17.md`'s HYPERLIQUID re-verify Follow-up. No code shipped,
  no VMs deleted (deletion needs a human call per STEP 0.65 — these VMs are not stale, they're duplicated).
- **slot-9 2026-08-16**: shipped the [INFRA] P1 root-cause fix — deployment-service@246fa62319. The [OPERATOR] P0
  fleet-cleanup and [DATA] P2 re-verify todos remain open (both need the duplicate fleet resolved first).
- **2026-08-16 (operator-authorized fleet cleanup)**: fresh `gcloud compute instances list
  --filter="name~'cefi-hyperliquid-2023'"` found 78 RUNNING (not 298 — the P1 singleton-guard fix had already
  stopped new launches; no new VM created after 2026-08-16T02:23-07:00, and all 78 were `SPOT` +
  `instanceTerminationAction=DELETE`, so ~220 preempted duplicates had already self-deleted since the doc's original
  298-count). Verified keeper health via GCS reads (`google.cloud.storage` Python SDK only — no gsutil/gcloud CLI
  object reads) on `vm-heartbeat/<name>.txt` and `vm-logs/<name>/run.log` under
  `gs://deployment-scripts-central-element-323112/`: sampled the oldest ~20 VMs and found progress clusters by
  launch-time group rather than strict creation order (a 7-VM group created ~04:01-04:07 UTC was tied
  furthest-along at HYPERLIQUID/book_snapshot_5 date 2023-08-09, ahead of the single 02:01 VM at 2023-07-30, zero
  errors on every sampled VM). Chose `cefi-hyperliquid-2023-20260816-040653` as keeper. Deleted the other 77 in one
  batched `gcloud compute instances delete <77-names> --zone=asia-northeast1-c --quiet` call — all 77 succeeded.
  Post-delete: exactly 1 VM remained (`cefi-hyperliquid-2023-20260816-040653`, RUNNING), re-verified healthy
  (advanced to 2023-08-10, zero errors, fresh heartbeat, `ManifestWriter` flushing). Waited ~4 minutes and re-ran the
  list filter: still exactly 1 VM, same name/creation-timestamp — **no repopulation observed**, confirming the P1
  singleton-guard fix (deployment-service@246fa62319) is holding live. Todo flipped to done; [DATA] P2 re-verify can
  now proceed against this single coherent keeper run.
