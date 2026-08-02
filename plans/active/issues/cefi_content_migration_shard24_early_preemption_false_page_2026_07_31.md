---
doc_type: issue
title: >-
  Shard 24's -065001 relaunch died to an ordinary SPOT preemption 70s post-insert, false-paged CRITICAL
  DP_VM_GONE_NO_CAPTURE — confirms deployment-service@09a2374 (shipped ~1h later off a tradfi VM repro) generalizes to
  the cefi-content-migration family too; that fix is NOT YET in the live monitor image
summary: >-
  DP-VM-002 escalation (`agt-143fcc`, slot 4, data_pipeline_failure) for
  `canonical-migration-cefi-content-24-relaunch20260731-065001`. Root cause confirmed via direct GCE Operations API +
  GCS evidence (not inferred): the VM was inserted 2026-07-31T06:50:22Z and reclaimed by `compute.instances.preempted`
  at 06:51:32Z — 70 seconds later, before the in-guest shutdown-script could ever write its `PREEMPTED` GCS marker or
  the migration script could write a single `run.log` line (log dir holds only the launcher-written
  `LAUNCH_PARAMS.json`/`TARBALL_PINS.json`). `exit_code_fleet_monitor.sweep()` (pre-fix) had no way to distinguish this
  from a genuine silent-zero death, so it fell through to `SILENT` -> CRITICAL `DP_VM_GONE_NO_CAPTURE` -> page. This is
  the SAME failure class `deployment-service@09a2374` (commit `09a23745dd4bdfc8e0fbf3e5ce8254f3a0ade6ba`,
  2026-07-31T08:06:31Z, agent `agt-8fa8d1`) already root-caused and fixed off a DIFFERENT (tradfi) VM roughly 1h15m
  after this one died — confirms the bug (and the fix) is generic to `exit_code_fleet_monitor.py`, not tradfi-specific.
  Separately confirmed: the currently-`:latest`-tagged `deployment-api` image (digest `bec407b3`, built/tagged
  2026-07-31T07:06:23Z) predates the fix commit (08:06:31Z) — the fix is on `live-defi-rollout` but NOT yet baked into
  the live Cloud Run monitor job, so further early-preemption false-pages remain possible until a fresh `deployment-api`
  build+deploy lands. No new code shipped by this escalation — re-fixing would duplicate `09a2374`. Shard 24's
  `RB-INFRA-RELAUNCH` budget for this vm-prefix is now 2/2 for today (2026-07-31): `-032606` (a genuine wedge/freeze,
  froze at 68,200/155,419=43.9% after `last_completed_date=2026-01-06` checkpoint, deleted 06:32Z) + `-065001` (this
  preemption) — per the runbook's flat bound, did NOT relaunch a 3rd time.
status: open
nature: issue
asset_group: [cefi, meta]
stage: [data, meta]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, migration, vm, preemption, alerting, false-positive, monitoring, data-pipeline, dp-vm-002, deploy-lag]
related:
  [
    cefi_content_migration_fleet_half_incomplete_2026_07_26,
    cefi_content_migration_shard17_default_bump_2026_07_31,
    cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31,
    cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-07-31
priority: P2
parent_epic: infrastructure_master
source:
  "data_pipeline_failure escalation agt-143fcc, slot 4, 2026-07-31 -- DP-VM-002 page for
  canonical-migration-cefi-content-24-relaunch20260731-065001"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.06
assigned_role: data_engineering
drift_direction: none
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
  ]
---

# Shard 24's early-SPOT-preemption false page — corroborates the already-shipped 09a2374 fix; flags deploy lag

## What I found

Dispatched via DP-VM-002 (`agt-143fcc`, slot 4, CRITICAL) for
`canonical-migration-cefi-content-24-relaunch20260731-065001` — context: "VM drained but manifest captured did not climb
(0 -> 0) AND its run.log shows no rows-written / honest-absence / rate-limit signal — a genuine silent zero." No issue
doc had been auto-filed (the page itself carried the details, per DP-VM-002's `page`-only escalation tier).

**Direct evidence, not inferred:**

- `gcloud storage ls gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-24-relaunch20260731-065001/`
  returns exactly two objects: `LAUNCH_PARAMS.json`, `TARBALL_PINS.json` — both written by the **launcher**, before the
  VM's own workload starts. **No `run.log`, no `EXIT_STATUS`, no `PREEMPTED` marker.**
- `gcloud compute operations list --filter="targetLink~canonical-migration-cefi-content-24-relaunch20260731-065001"`:
  ```
  insert                        DONE  2026-07-30T23:50:22.650-07:00 (=2026-07-31T06:50:22Z)
  compute.instances.preempted   DONE  2026-07-30T23:51:32.402-07:00 (=2026-07-31T06:51:32Z)
  ```
  **70 seconds** between insert and preemption — the guest never got far enough through boot (env + metadata-server
  round-trip + gcloud auth) to run its shutdown-script and write the `PREEMPTED` GCS blob, let alone start the Python
  migration script. `gcloud compute instances describe` on the VM returns `NOT_FOUND` (self-deleted per
  `--instance-termination-action=DELETE`).
- `LAUNCH_PARAMS.json` shows this was a **correct checkpoint-resumed relaunch**: `RESUME_START_DATE=2026-01-07`,
  `RESUME_END_DATE=2026-01-15` — exactly the day after the prior attempt's own checkpoint.

**Shard 24's fuller history today** (traced via every `canonical-migration-cefi-content-24-*` `vm-logs/` dir +
`gcloud compute operations list`, not assumed from the parent fleet doc's table alone):

- `-relaunch20260731-032606` (inserted 03:27:09Z, part of the parent doc's "18 shards" relaunch wave): ran real progress
  to `68,200/155,419 files (43.9%)` at `05:44:24Z` (`PROGRESS.json`: `last_completed_date=2026-01-06`,
  `monotonic=true`), `pyarrow pool release: bytes_allocated` staying near-zero throughout (the `9f4098b1` leak fix
  visibly working) — then went silent for 48 minutes before being deleted at `06:32:11Z`. This is the SAME freeze/wedge
  signature the parent fleet doc + its `cefi_content_apply_memory_freeze...` sibling doc already diagnosed as open (not
  this doc's finding to re-litigate).
- `-relaunch20260731-065001` (inserted 06:50:22Z, correctly resumed from `-032606`'s own checkpoint): preempted 70s
  later, as above. **This is a clean, no-fault SPOT reclaim** — zero data risk, zero wasted migration progress (it never
  started the migrate phase).

**The false-page mechanism**: `deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py::sweep()`
(pre-`09a2374`) resolves `is_preempted` solely from the in-guest-written GCS `PREEMPTED` marker
(`_gcs.is_vm_preempted`). Absent that marker, absent any `run.log` progress vocabulary match (there is none — no
`run.log` at all here), and with `captured` flat (true both because this script family never writes the availability
manifest at all — the ALREADY-RESOLVED, unrelated `cefi_content_migration_vm_wedged_worker_2026_07_23.md` finding — AND
because zero data was ever touched), the sweep has nothing left to classify this as but `SILENT` ->
`TerminationVerdict.GONE_NO_CAPTURE` -> CRITICAL `DP_VM_GONE_NO_CAPTURE` -> page.

**Already fixed, independently, off a different VM**: `deployment-service@09a23745dd4bdfc8e0fbf3e5ce8254f3a0ade6ba`
(2026-07-31T08:06:31Z, agent `agt-8fa8d1`) root-caused and shipped a fix for this EXACT mechanism — reproduced there via
`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260731-060117` (inserted 23:01:22Z, preempted 23:03:07Z, zero run.log lines, no
PREEMPTED blob — the identical shape as shard 24's `-065001`, ~1h15m earlier and in a completely different asset_group).
The fix adds an optional `preemption_op_checker` fallback to `sweep()`, consulted only on the `GONE_NO_CAPTURE`
candidate path when the GCS marker is absent, backed by a new `ComputeEngineClient.was_instance_preempted()` querying
the Compute Engine Operations API directly (immune to the guest-boot race). **I did not re-implement this — it would
duplicate/conflict with already-shipped, QG-green, tested work.** This escalation's marginal value is confirming the fix
generalizes beyond its one tradfi repro (it does — same code path, same evidence shape, different asset_group and
different VM-prefix family entirely) and catching a deploy-lag gap the original fix's author didn't check.

**Deploy-lag gap (new finding)**: `deployment-api` (the Cloud Run image `uts-prod-dp-exit-code-monitor` actually runs —
`deployment_service` is vendored into it at build time via `Dockerfile`'s
`COPY _deployment-service/ /tmp/deployment-service/` + `uv pip install --system --no-deps`, NOT a versioned wheel pin)
is currently `:latest`-tagged at digest `sha256:bec407b3ecda...`, per
`gcloud artifacts docker images list ... --include-tags --sort-by=~UPDATE_TIME`: **tagged/updated
`2026-07-31T07:06:23Z`** — a full hour BEFORE the fix commit (`08:06:31Z`). So `09a2374` is on `live-defi-rollout` but
**not yet baked into the live monitor image**. Until a fresh `deployment-api` build+deploy runs, ANY future
early-SPOT-preemption (any asset_group, any VM prefix) can still false-page CRITICAL the same way. I did not trigger a
redeploy myself — I could not find a simple, well-understood "just rebuild deployment-api now" command in this
one-shot's scope (the Dockerfile references a "tier-3 deploy script" that rsyncs sibling repos into the build context
pre-`docker build`, which reads like a controlled deploy pipeline step rather than something safe to improvise against a
live, UI-serving production service) — flagging rather than guessing, per this role's own
`does_not: guess at an ambiguous fix`.

**Relaunch-budget state**: per `RB-INFRA-RELAUNCH`'s flat `≤2/(vm-prefix,day)` bound (no preemption carve-out in the
runbook text), `canonical-migration-cefi-content-24-*` has used 2/2 today (`-032606` wedge + `-065001` preemption). Did
**not** relaunch a 3rd time — verified no other agent had either (`vm-logs/` listing re-checked immediately before
filing this doc, no new `-24-` object appeared).

## Why it matters

Each early-preemption false-page burns an on-call page + a full escalation-worker dispatch (context, tool calls,
diagnosis time) for a genuinely benign, self-recovering SPOT event — pure toil until the fix is live. The deploy-lag gap
means the fix landing on `live-defi-rollout` is necessary but not sufficient; without confirming the image actually
redeployed, this exact false-page class will keep recurring across every asset_group (not just cefi/tradfi) until
someone checks.

## Recommended decision

- [ ] [OPERATOR] P2. Confirm (or trigger) a fresh `deployment-api` build+deploy so the live
      `uts-prod-dp-exit-code-monitor` / `uts-prod-monitoring-deadman` / `uts-prod-mtds-monitor-snapshot-governance`
      Cloud Run jobs pick up `deployment-service@09a2374`. **Done when**:
      `gcloud artifacts docker images list     asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/deployment-api --include-tags     --sort-by=~UPDATE_TIME --limit=1`
      shows an `UPDATE_TIME` after `2026-07-31T08:06:31Z`, AND
      `test_sweep_early_preemption_no_marker_falls_back_to_op_checker` (already shipped in
      `tests/unit/test_data_pipeline_monitors.py`) is confirmed passing on that build. Tagged `[OPERATOR]` because I
      could not identify a safe, well-understood redeploy trigger for this live UI-serving service within this
      one-shot's scope — a human (or a properly-scoped follow-up task) should confirm the correct deploy pipeline rather
      than have an escalation worker improvise against production. Repo: deployment-api (deploy only — no code change).
- [ ] [SCRIPT] P3. Once the above is confirmed deployed, relaunch shard 24
      (`launch-canonical-migration-vm.sh cefi-content-apply 2026-01-07 2026-01-15 full` — the exact checkpoint-resumed
      window `-065001` was already using) for its 3rd attempt today. If the operator wants it relaunched sooner
      (accepting the `RB-INFRA-RELAUNCH` budget as a deliberate exception, mirroring the 2026-07-31T06:30Z shard-17
      precedent in `cefi_content_migration_shard17_default_bump_2026_07_31.md`), that is an operator call, not one this
      escalation makes unilaterally. No `[OPERATOR]` gate needed for the relaunch action itself once the budget
      genuinely resets (ordinary backfill relaunch, AO-dispatchable by default per
      `/codex/05-infrastructure/vm-launcher-runbook.md`). Repo: deployment-service (launch) + market-tick-data-service
      (verify).

## Progress Log

- 2026-07-31 (`data_pipeline_failure` escalation `agt-143fcc`, slot 4): filed after confirming this DP-VM-002 page was a
  benign early-SPOT-preemption (GCE Operations API + GCS evidence, not inferred) matching an already-shipped fix
  (`deployment-service@09a2374`, landed ~1h15m after this VM died, off an unrelated tradfi VM repro). No code shipped
  (would duplicate). Did not relaunch shard 24 a 3rd time today (`RB-INFRA-RELAUNCH` budget 2/2 exhausted for this
  vm-prefix). Pinged the authoring slot (`dp-fleet-monitor`) with this outcome.

- **na-eligibility-audit 2026-08-01** (tranche=cefi, autonomous): KEEP-NA, valid. Item 1 is `[OPERATOR]`-tagged
  (confirm/trigger a deployment-api redeploy — a live production-redeploy decision, not worker-determinable); item 2
  gated on item 1. Independently corroborated by `cefi_satellite_ao_dispatch_batch4_2026_07_31.md`'s own
  Deferred/operator-gated list (same conclusion, same reasoning). No reclassification.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
