---
doc_type: issue
title:
  DP-VM-003 manifest-recon-cefi-20260815-093854 heartbeat-stall escalation — VM actually died silently mid-manifest-load
  (no exit marker); replacement now running on e2-highmem-16; recommend slim-column read for the dry-run-only caller
summary: >-
  Escalation agt-9d78d2 (wall_type=data_pipeline_failure) reported `manifest-recon-cefi-20260815-093854` (asset_group
  cefi, launched via `deployment-service/scripts/vm/launch-manifest-recon-all-vm.sh cefi` with `UNPHANTOM_ONLY=true
  VENUES=BINANCE-FUTURES,KRAKEN-FUTURES`, satisfying the still-open todo in
  `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch6_2026_07_30.md`) with a 12-minute-stale heartbeat. Live diagnosis (via
  `deployment_service.data_pipeline_monitors._gcs` SDK reads, never subprocess gsutil/gcloud storage) found the VM's
  `run.log` froze immediately after `Loading manifest from
  gcp://market-data-tick-cefi-prd-central-element-323112/_index/ availability_index.parquet` — the single blocking
  `client.download_bytes(...)` + `pd.read_parquet(...)` call inside
  `unified_trading_library.manifest_writer._read_index.merge_canonical_with_outstanding_shards` (called from
  `reconcile_phantom_manifest_rows_all.py:1719` with `columns=None`, i.e. the FULL unsliced schema, even though
  `--unphantom-only` never writes back and so never needs the full schema retained). By the time this session re-checked
  (~25 min after the VM's last log line), the instance had vanished from `gcloud compute instances list` entirely — no
  `EXIT_STATUS` blob, no `rc=` line in `run.log`, no `PREEMPTED` or `REAPED` marker (ruling out spot-preemption and a
  deliberate tombstone-delete). This is the DP-VM-002/DP-VM-010-class ambiguous "gone with zero terminal evidence"
  shape, most plausibly a `relaunch_stalled_vm.py`-triggered watchdog kill after a genuine hang/heavy-load freeze on
  this specific blocking read — the SAME code path already documented as OOM-risky for `defi`
  (`reconcile_phantom_manifest_rows_all_defi_memory_footprint_2026_07_28.md`) but never previously flagged for `cefi`.
  `launcher_registry.LAUNCHER_FOR_VM_PREFIX["manifest-recon-"] = None` (deliberate — "read-only all-reconciler dry-run")
  meant the `DP_VM_STALL` auto-recover actuator could not auto-relaunch, degrading to this escalation. This worker
  manually relaunched the SAME scoped invocation with a `MACHINE_TYPE=e2-highmem-4` safety-margin override
  (`launch-manifest-recon-all-vm.sh` still defaults `cefi` to `e2-standard-4`); the actual `gcloud compute instances
  create` call for that attempt never fired (a separate `deployment-service` tarball-republish pre-flight step exited 2
  before reaching the create step — no VM was created, no resources wasted). By the time this was checked, a
  **different** `manifest-recon-cefi-20260815-100959` was independently already RUNNING on **`e2-highmem-16`** (128GB) —
  a different actor (not this worker) launched an equivalent, far more generously-sized replacement in the same window;
  its `run.log` shows a healthy heartbeat (two ticks 60s apart) as of this write-up, past the exact point the prior VM
  died. This worker did not launch a second duplicate (the Tardis/singleton-style "don't race a converging concurrent
  actor" principle applies) and did not confirm the other launcher's identity (not essential to closing this
  escalation). No code was shipped this session — the concrete, scoped root-cause fix (thread `columns=` through the
  `--unphantom-only`/dry-run path so the read only pulls the columns that mode's logic needs, mirroring the
  `read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md` precedent for the sibling reader) is left as a
  todo below rather than shipped blind under escalation time pressure, since a wrong column-subset would silently break
  the reverse-revalidation logic.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [instruments-service, unified-trading-library, deployment-service]
scope: [engineer, admin]
tags:
  [dp-vm-003, heartbeat-stall, manifest-recon, cefi, oom-risk, unsliced-manifest-read, data-pipeline-monitors, relaunch]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /plans/archive/issues/reconcile_phantom_manifest_rows_all_defi_memory_footprint_2026_07_28.md,
    /plans/archive/2026_08/read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md,
    /plans/archive/issues/dp_vm_003_manifest_recon_cefi_wedged_non_relaunchable_2026_08_15.md,
  ]
context_scope: [/codex/15-runbooks/incidents/rb_infra_relaunch.md, /codex/05-infrastructure/data-pipeline-alerts.md, deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py, deployment-service/scripts/vm/launch-manifest-recon-all-vm.sh, instruments-service/scripts/reconcile_phantom_manifest_rows_all.py, unified-trading-library/unified_trading_library/manifest_writer/_read_index.py]
created: "2026-08-15"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: devops
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Escalation agt-9d78d2 (wall_type=data_pipeline_failure, dispatched to slot 18, 2026-08-15). Context: "WARN DP_VM_STALL
  (DP-VM-003) — VM manifest-recon-cefi-20260815-093854 stalled — heartbeat 12m stale. Filed issue: (none — alert carries
  the details). RELAUNCH vm=manifest-recon-cefi-20260815-093854 launcher=(resolve via launcher_registry) deployment_id=?
  asset_group=cefi." No separate audit CSV/candidate list was attached.
---

# DP-VM-003 — manifest-recon-cefi-20260815-093854 silent death mid-manifest-load; replacement running; slim-read fix recommended

## What happened

1. `manifest-recon-cefi-20260815-093854` (asset_group=cefi, `e2-standard-4`, launched via
   `launch-manifest-recon-all-vm.sh cefi` with `UNPHANTOM_ONLY=true VENUES=BINANCE-FUTURES,KRAKEN-FUTURES` — the exact
   invocation `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch6_2026_07_30.md` todo #P3 (line 505) names) fired
   `DP_VM_STALL` at 12 minutes heartbeat-stale.
2. Live re-check (via `deployment_service.data_pipeline_monitors._gcs.run_log_signals`/`heartbeat_blob_age_minutes`/
   `read_terminal_exit_code`, SDK-only per the workspace GCS-object-ops hard rule): `run.log` froze at
   `2026-08-15T09:42:38Z`, immediately after
   `Loading manifest from gcp://market-data-tick-cefi-prd-central-element- 323112/_index/availability_index.parquet` —
   the sole blocking `client.download_bytes()` + `pd.read_parquet()` call inside
   `merge_canonical_with_outstanding_shards`
   (`unified-trading-library/unified_trading_library/manifest_writer/ _read_index.py:1708-1712`), invoked from
   `reconcile_phantom_manifest_rows_all.py:1719` with `columns=None` (the FULL schema — every column, every row of the
   cefi canonical index). Both the worker-life `PIPELINE_HEARTBEAT` bash loop AND the infra `vm-heartbeat` sidecar (a
   normally-independent, always-fresh emitter) went stale together, consistent with the whole VM being starved/wedged
   during this single call rather than merely the python worker being slow.
3. ~25 minutes after that freeze, `gcloud compute instances list --filter="name~^manifest-recon-cefi-"` returned ZERO
   rows — the VM was gone. No `EXIT_STATUS` blob, no `rc=` marker in `run.log`, no `PREEMPTED` blob (not a SPOT VM — the
   launcher's `gcloud compute instances create` call carries no `--provisioning-model=SPOT`), no `REAPED` tombstone.
   This is the DP-VM-002/DP-VM-010 "terminated with zero terminal evidence" shape — most consistent with a
   `relaunch_stalled_vm.py`-class watchdog kill following a genuine multi-minute hang/resource-starvation freeze on the
   manifest-load call (the actuator's own docstring names an unbounded/no-`timeout=` outbound call as its "canonical
   case").
4. `launcher_registry.LAUNCHER_FOR_VM_PREFIX["manifest-recon-"] = None` (comment: "read-only all-reconciler dry-run") —
   a deliberate registry decision, so the `DP_VM_STALL` `auto_recover` tier could not resolve a launcher and degraded to
   `file_issue`/this escalation (`RelaunchStalledVm.relaunch()` returns `status=SKIPPED, reason=no_launcher_binding` for
   an empty launcher).
5. This worker confirmed the batch6 todo is still open (not stale/superseded) and manually relaunched the identical
   scoped invocation with `MACHINE_TYPE=e2-highmem-4` (a moderate safety-margin bump over the `e2-standard-4` default,
   without touching the shared launcher's default for other callers). The `deployment-service` tarball was stale
   relative to this worktree's HEAD and auto-republished cleanly (worktree was clean, 1 commit behind origin — the
   republished tarball is a legitimate committed SHA, not stray local drift). The launch script then exited 2 during a
   later pre-flight step (a "mis-floored peer-repo pin" check, unrelated to `manifest-recon`) — no
   `manifest-recon-cefi-20260815-101142` (the name the script had already echoed) was ever created; confirmed via
   `gcloud compute operations list` (zero matching operations) — no wasted VM, no duplicate.
6. Independently, `manifest-recon-cefi-20260815-100959` was found already RUNNING on **`e2-highmem-16`** (128GB) —
   launched by a different actor in the same window (RUN_TS 10:09:59, `gcloud compute instances create` completed
   10:11:34Z — before this worker's own relaunch attempt even started at 10:11:42). Its `run.log` shows two
   `PIPELINE_HEARTBEAT` ticks 60s apart (10:14:00Z, 10:15:00Z) past the exact point the first VM died, with no signs of
   a repeat freeze as of this write-up. This worker did not launch a second duplicate against an already-converging
   equivalent run, and did not identify who/what launched it (not essential to closing this escalation — the open
   `batch6` todo is now covered by a well-resourced, healthy run).

## Root-cause hypothesis (not fully confirmed — no VM-level dmesg/OOM message was retrievable; the instance was already

gone by the time this worker attempted `gcloud compute ssh` diagnosis, which itself timed out twice against IAP)

`merge_canonical_with_outstanding_shards` supports a `columns=` slim-read parameter specifically "for callers that only
need a handful of columns (verification/audit/dry-run paths)" per its own docstring, and a sibling reader
(`read_availability_index`) already got the equivalent fix for exactly this OOM-at-scale shape
(`read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md`). `reconcile_phantom_manifest_rows_all.py`'s
`--unphantom-only` mode (the mode this VM ran) structurally never writes the manifest back — the header comment says so
explicitly ("skip the FORWARD phantom-flagging pass ENTIRELY... only the reverse re-validation... runs below") — so it
does not need the full schema retained, yet the call site passes `columns=None` unconditionally regardless of mode. This
is the same failure class already fixed for `defi`
(`reconcile_phantom_manifest_rows_all_defi_memory_footprint_ 2026_07_28.md`, which bumped `defi`'s machine type after
OOM-killing at 15.4GB and again stalling near 96% mem at 64GB) — `cefi`'s launcher default (`e2-standard-4`, unchanged)
was never previously flagged as at-risk for this same unsliced read.

## Todos

- [x] [SCRIPT] P2. EXTRACTED — na-eligibility-audit 2026-08-16, conflict-cleared, live todo now
      `cefi_satellite_ao_dispatch_batch20_2026_08_16.md` item 3. Original text: Thread a slim `columns=` list
      through `reconcile_phantom_manifest_rows_all.py`'s
      `merge_canonical_with_outstanding_shards(storage_client, bucket_name, str(cfg["index"]))` call
      (`reconcile_phantom_manifest_rows_all.py:1719`) for the `--unphantom-only` mode specifically — enumerate exactly
      the columns that mode's reverse-revalidation logic (and the dedup-merge base columns
      `unified_trading_library.manifest_writer._read_index._SLIM_MERGE_BASE_COLS`) actually read, mirroring
      `read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md`'s fix for the sibling reader. Do NOT apply the
      same slimming to the full (non-`--unphantom-only`) mode — that path writes the whole DataFrame back and needs the
      full schema. Verify via `quality-gates.sh` + a re-run of the
      `--unphantom-only --venues BINANCE-FUTURES,KRAKEN-FUTURES` scan (or a smaller synthetic venue set) proving
      identical output to the unsliced read.
- [ ] [OPERATOR] P3. DEFERRED-BY-DESIGN — RULED 2026-08-22 (D73): Keep
      `launcher_registry.LAUNCHER_FOR_VM_PREFIX["manifest-recon-"] = None` (no auto-relaunch) — the root cause was
      memory sizing, already fixed via column-slimming; auto-relaunch would mask future OOMs. Source:
      /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
- [x] ✅ [OPERATOR] P3. Confirm `manifest-recon-cefi-20260815-100959` (currently running on `e2-highmem-16`) completes
      successfully and its output satisfies `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch6_2026_07_30.md` todo #P3
      (cefi BINANCE-FUTURES/KRAKEN-FUTURES `--unphantom-only` re-run) — flip that checkbox once confirmed; this issue
      doc does not flip it directly since the run had not completed as of this write-up. **CONFIRMED 2026-08-15
      (slot-17)**: completed cleanly, `exit_code=0`, `Manifest rows: 29,707,581`, "No phantoms found and nothing to
      unphantom. Manifest is clean." Batch6 checkbox flipped.

## Progress Log

- 2026-08-15 (slot 18, data_pipeline_failure escalation agt-9d78d2): Diagnosed DP-VM-003 for
  `manifest-recon-cefi-20260815-093854` via SDK-only GCS reads (never subprocess gsutil — blocked by the workspace
  guardrail hook, correctly). Found the VM had actually died silently (zero terminal exit evidence) ~2 minutes into a
  blocking full-schema manifest-parquet read, not merely stalled. Traced the root-cause hypothesis to the unsliced
  `columns=None` call in `reconcile_phantom_manifest_rows_all.py`, matching a documented `defi` OOM precedent never
  previously flagged for `cefi`. `gcloud compute ssh` diagnosis of the (already-terminated) VM was attempted twice and
  timed out both times against IAP — abandoned rather than continuing to poll. Attempted a manual relaunch with a
  `MACHINE_TYPE=e2-highmem-4` safety margin; that specific `gcloud compute instances create` call never fired (a
  pre-flight step unrelated to this VM class exited 2 first) — confirmed via `gcloud compute operations list` that no VM
  was actually created, so no resources were wasted. Found a different, already-RUNNING, far larger (`e2-highmem-16`)
  replacement (`manifest-recon-cefi-20260815-100959`) launched independently in the same window, healthy as of this
  write-up (`run.log` heartbeats to 10:15:00Z past the point the first VM died) — did not launch a duplicate against it.
  Filed this issue doc with the root-cause hypothesis + a scoped follow-up todo rather than shipping an unverified
  column-slimming change under escalation time pressure. No code changed this session.
- 2026-08-15 (slot-17, data_engineering, batch6 P3 todo owner): Root-cause CONFIRMED (was "not fully confirmed" above) —
  the first VM's own deployment registry entry
  (`gs://deployment-scripts-central-element-323112/deployments/active/b45704e9-266e-4cbd-b9d2-472a0e7541d8.json`, read
  before it was archived) carries a `host_metrics_window` showing `mem_pct` climbing 75.3%→99.2% (`mem_slope=23.9`) in
  the same ~1-minute window `run.log` froze — a genuine guest-level OOM, not a `relaunch_stalled_vm.py` kill or an
  unrelated hang. The VM has since fully vanished (`gcloud compute instances describe` → not found), consistent with an
  OOM-triggered crash rather than a clean shutdown. Confirmed `--venues` scoping does NOT reduce this cost — the
  manifest load happens before any venue filter applies, and the re-run (below) still needed a 128GB box even scoped to
  2 venues. Separately: `launch-manifest-recon-all-vm.sh`/`-apply-vm.sh` were extended this session with
  `UNPHANTOM_ONLY`/`VENUES` scoping so this exact invocation is reproducible without hand-rolling metadata
  (`deployment-service@04fd67e025`) — orthogonal to this doc's `columns=` slim-read todo (still open, still the real
  fix; scoping alone doesn't avoid the full-manifest load). Re-ran on `e2-highmem-16` (128GB):
  `manifest-recon-cefi-20260815-100959` completed cleanly (`exit_code=0`), `Manifest rows: 29,707,581`, "No phantoms
  found and nothing to unphantom. Manifest is clean." — flipped this doc's todo #3 and
  `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s P3 todo. The `columns=` slim-read todo above remains
  open — a genuine efficiency fix, not required to close batch6's todo now that a correctly-sized VM proved sufficient.
- **na-eligibility-audit 2026-08-16** [body-hash:ff4d339f25828573]: RECLASSIFY-SPLIT — extracted bounded item(s) 3 to `cefi_satellite_ao_dispatch_batch20_2026_08_16.md` (see that plan + this doc's own checkbox citations for exact mapping). 1 item remains genuinely NA ([OPERATOR] P3 launcher-registry auto-recovery-binding decision). Doc stays assigned_vm: NA.
**context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17 (re-verify, cefi tranche)** [body-hash:ceaa7f459d29dec2]: KEEP-NA, valid — re-confirmed, same 1 open item as yesterday's marker (hash drift only — context_scope refresh, no content staleness found on this pass). Line 157 ([OPERATOR] P3, reconsider whether `launcher_registry.LAUNCHER_FOR_VM_PREFIX["manifest-recon-"]` should enable auto-recovery) OPERATOR_QUESTION — explicit `[OPERATOR]` tag, genuine policy fork (manual-judgment-only vs. auto-recovery for this VM class) with no decision on record. Doc stays assigned_vm: NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **2026-08-22 — ruling D73 (manifest-recon auto-relaunch)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Keep None — the root cause was memory sizing (already fixed via column-slimming);
  auto-relaunch would mask future OOMs. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
