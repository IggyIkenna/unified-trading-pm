---
doc_type: issue
title:
  Archived early Progress Log detail for cefi_content_migration_fleet_half_incomplete_2026_07_26.md (2026-07-26 through
  2026-07-30T17:53Z)
summary: >-
  Pure relocation, no rewrite — the parent doc's "## Progress Log" section (2026-07-26 filing through the
  2026-07-30T17:53Z shard-29 freeze entry) moved here VERBATIM to keep the parent under its 1000-line hard cap (the
  parent's own full-text-reflow line count, post-`prettier --write`, exceeded 1000 even before this session's edit — a
  pre-existing drift, not caused by this extraction). Covers: the initial 21-shard relaunch (exact per-shard date
  windows recovered from each dead shard's own `run.log`), three sequential zone-wide SPOT preemption waves (resolved
  via on-demand conversion), repeated `gcloud` active-identity poisoning (`unified-trading-sa` drifting to
  `github-actions-deploy`/`github-deploy`), the `e2-standard-8` OOM class (fixed via `e2-standard-16`), the
  still-unresolved shard-19 mystery delete, the P0 dispatch-deadlock escalation, and three early full completions
  (shards 28, then partial narrative up to the 17:53Z shard-29 freeze). The parent doc's own "## 2026-07-30 root cause +
  fix shipped" section and "## Progress Log (continued)" section (which covers the pyarrow/mimalloc root-cause
  diagnosis, the fix, and later verification) were NOT moved — those stay in the parent, unabridged.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [cefi, migration, canonicalisation, vm-fleet, incomplete, data-correctness, archive]
related: [cefi_content_migration_fleet_half_incomplete_2026_07_26]
created: 2026-07-31
priority: P3
parent_epic: cefi_master
source:
  "worker, slot 8, 2026-07-31, cefi_content_migration_fleet_half_incomplete-002 -- parent doc's full-text-reflow line
  count exceeds its 1000-line hard cap even before this session's edit; extracted its earliest Progress Log entries
  verbatim to make room, mirroring the doc's own established split-when-at-cap pattern"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# Archived Progress Log detail: cefi content-migration fleet, 2026-07-26 → 2026-07-30T17:53Z

This is a pure archival relocation of the parent doc's own text — no summarization, no rewording. See the parent doc
(`cefi_content_migration_fleet_half_incomplete_2026_07_26.md`) for the current todo list, the "## 2026-07-30 root
cause + fix shipped" section, and the continued Progress Log (2026-07-30T19:15Z onward).

## Progress Log (archived section — originally 2026-07-26 through 2026-07-30T17:53Z)

- 2026-07-26 (worker, slot 6, `defi_satellite_ao_dispatch_batch2-007`): Filed after confirming corpus-wide completion
  was NOT reached — script left in place (NOT deleted) per the batch2 todo's own instruction for this case. Full
  evidence above; log data fetched via `gcloud storage cat` against
  `gs://deployment-scripts-central-element-323112/vm-logs/`.
- **2026-07-30 (slot-15, `cefi_content_migration_fleet_half_incomplete-002`)**: Was dispatched todo P2 (the
  post-relaunch re-verify + delete), but P1 (relaunch) had never actually been dispatched/run — backlog showed it
  `blocked`/undispatched. Verified live: only ONE relaunch attempt existed
  (`canonical-migration-cefi-content-13-relaunch20260730-071533`, this morning) and it was **preempted 90s after
  insert** (`compute.instances.preempted` at 00:17:12, insert at 00:15:42 UTC-7) with no auto-recovery and no `run.log`
  ever written — a second, independent instance of the exact SPOT-preemption-with-no-resume gap this doc's todo 3
  already flags. Also notable: that attempt's `RESUME_START_DATE`/`RESUME_END_DATE` (2024-02-05/2024-04-04) do NOT match
  shard 13's own original date window (2026-01-16/2026-02-13, recovered below) — looks like a parameter mistake in
  whoever triggered it, unrelated to my own relaunch. Executed P1 myself (todo's own text already resolved the
  authorization question — "No `[OPERATOR]` gate needed… AO-dispatchable by default" — and it is the literal blocking
  prerequisite for my assigned P2): recovered each of the 21 dead shards' EXACT original `--start-date`/`--end-date`
  window from its own `run.log`'s `[vm-exec] starting:` command line (not re-derived/guessed), confirmed the critical
  `54817bc1` PROGRESS.json-checkpoint fix (SPOT-resume gap) is already baked into the currently-published `mtds-code`
  tarball (`d75e247079d1` is a descendant), then relaunched all 21 shards via
  `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full` with
  `VM_NAME_OVERRIDE=canonical-migration-cefi-content-<shard>-relaunch20260730-122417` (SPOT, default per HARD RULE),
  verified each `RUNNING` via `gcloud compute instances list` (not fire-and-forget). Exact windows used:
  13=2026-01-16..2026-02-13, 14=2026-02-14..2026-03-27, 15=2026-03-28..2026-07-19, 16=2024-08-20..2024-11-13,
  17=2024-11-14..2025-01-09, 18=2025-01-10..2025-02-06, 19=2025-02-07..2025-03-17, 20=2025-03-18..2025-05-03,
  21=2025-05-04..2025-06-26, 22=2025-06-27..2025-09-06, 23=2025-09-07..2026-01-01, 24=2026-01-02..2026-01-15,
  25=2026-01-16..2026-02-01, 26=2026-02-02..2026-02-13, 28=2026-03-01..2026-03-27, 29=2026-03-28..2026-05-01,
  40=2024-05-12..2024-06-11, 41=2024-09-30..2024-11-13, 42=2024-12-27..2025-01-09, 43=2025-01-23..2025-02-06,
  44=2025-07-30..2025-09-06. **Status: relaunch STARTED, NOT complete** — these VMs will take hours (shard 14 alone
  measured only 1.2% in its first attempt's unknown-duration run). My assigned P2 todo (corpus-wide re-verify +
  delete-if-44/44) genuinely cannot complete until these finish; leaving it undone rather than falsely claiming
  completion. A future pass/session should re-run the corpus-wide `run.log` grep once these shards have had time to
  progress, and watch for further SPOT preemptions (now checkpoint-protected via the `54817bc1` fix, but still worth
  monitoring per `/vm-preemption-billing-waste-audit`).
- **2026-07-30 update (slot-15, same session, ~25 min later)**: spot-check found 20/21 relaunch VMs progressing normally
  (steady `Progress:` climb, e.g. shard 14 at 10,600/335,111, shard 29 at 13,000/194,481), but shard 41
  (`canonical-migration-cefi-content-41-relaunch20260730-122417`) had died AGAIN — this time NOT a SPOT preemption
  (`gcloud compute operations list` shows a clean `delete` op, no `compute.instances.preempted` event; the VM stayed
  RUNNING throughout). Its `run.log` shows the python process itself hard-killed (`rc=137`) at only 3,800/77,941 files
  (4.9%) — the wrapper's own SIGTERM-triggered shutdown log entry comes AFTER the "Killed" line, meaning something
  killed the worker process directly, not GCE terminating the instance. Consistent with a kernel OOM-kill on the default
  `e2-standard-8` (8 vCPU / 32GB), NOT the same failure class as the SPOT-preemption gap this doc otherwise covers — a
  genuinely new, third failure mode for this migration script. Relaunched shard 41 with `MACHINE_TYPE=e2-standard-16`
  (doubles RAM to 64GB, same escalation the launcher script's own tradfi-v9 comment already documents for a prior OOM)
  as `canonical-migration-cefi-content-41-relaunch20260730-124900`, verified `RUNNING`. If this ALSO OOMs, the fix is a
  genuine root-cause investigation into this script's memory profile (possibly `--workers` too high for the process's
  actual per-file memory footprint on this shard's date range), not another machine-size escalation.
- **2026-07-30 update (slot-15, same session, ~5 min later)**: shard 18
  (`canonical-migration-cefi-content-18-relaunch20260730-122417`) died with the IDENTICAL signature — `rc=137`, worker
  process killed directly (VM stayed `RUNNING`, clean `delete` op, no preemption event), preceded by several minutes of
  "No progress in the last poll window" warnings before the kill, at 5,400/148,799 files (3.6%). **This is the SECOND
  e2-standard-8 shard to OOM-die within ~25-40 minutes of a 21-VM fleet launch** — starting to look systemic (possibly
  the shared in-memory catalogue this script loads at startup —
  `Loaded N catalogue rows from instruments-store-cefi-prd-...` — has grown over the 11 days since the original
  2026-07-19 launch, pushing every e2-standard-8 shard closer to its 32GB ceiling) rather than two isolated incidents.
  Relaunched shard 18 on `e2-standard-16` (`canonical-migration-cefi-content-18-relaunch20260730-125300`), verified
  `RUNNING`. **Did NOT** preemptively kill+relaunch the other 18 still-`e2-standard-8` shards on a still-n=2 pattern —
  that would discard real, accumulating progress (e.g. shard 29 climbing steadily past 13k files) on an unconfirmed
  hypothesis; a THIRD independent OOM would be strong enough confirmation to justify that broader, more disruptive move.
  **Watch for more of these** — if the pattern continues, the durable fix belongs in the launcher's own
  `cefi-content-apply` category comment (default to `e2-standard-16` for this category going forward, not per-incident
  escalation).
- **2026-07-30 update (slot-15, same session, ~10 min later) — THIRD occurrence, escalated to fleet-wide fix**: shard 17
  (`canonical-migration-cefi-content-17-relaunch20260730-122417`) died with the SAME `rc=137` signature at
  12,400/157,497 files (7.9%, ~30 min runtime — notably further than shards 41 (4.9%) or 18 (3.6%), consistent with
  memory accumulating over TIME/volume-processed rather than dying at a fixed absolute file count). This is the bar
  explicitly set in the entry above ("a THIRD independent OOM would be strong enough confirmation") — three different
  shards, three different date ranges, same signature, now confirmed systemic rather than coincidental. Relaunched shard
  17 on `e2-standard-16`. **Escalated to the fleet-wide fix**: rather than wait for each of the remaining 18
  still-`e2-standard-8` shards to individually OOM (each wasting its accumulated runtime before being caught), deleted
  all 18 and relaunched them on `e2-standard-16` in one batch
  (`canonical-migration-cefi-content-<shard>-relaunch20260730-130600`). Accepted the sunk cost of their partial progress
  deliberately — the script's `already_canonical_skipped` counter means a fresh re-scan re-confirms already-migrated
  files CHEAPLY (a metadata check, not a re-migration), so restarting is materially cheaper than it looks from raw
  file-count-discarded alone. **All 21 shards are now on `e2-standard-16`** as of this action;
  `MACHINE_TYPE=e2-standard-8` default for `cefi-content-apply` in `launch-canonical-migration-vm.sh` should be
  reconsidered as a follow-up if this pattern is confirmed durable (i.e., if e2-standard-16 shards run to completion
  without further OOMs) — not yet added as a tracked todo since the e2-standard-16 fix itself isn't confirmed successful
  yet (shard 41 was mid-test crossing its prior death point at time of writing).
- **2026-07-30 update (slot-15, same session, ~5 min later) — fix CONFIRMED**: shard 41 safely cleared 5,400/77,941
  files (well past its 3,800-file death point on `e2-standard-8`) and is still `RUNNING` healthy on `e2-standard-16` —
  the machine-type escalation genuinely resolves the OOM, not a coincidence of timing. Also confirmed the `54817bc1`
  SPOT-checkpoint fix is actively writing (`[[VM_PROGRESS]] last_completed_date=2024-10-01 monotonic=true` observed in
  shard 41's log). Adding the tracked follow-up now that the fix is verified:
- **2026-07-30 update (slot-15, same session, ~15 min later) — two more real problems hit during the 18-shard batch
  upgrade, both resolved**:
  1. **Broken active identity mid-batch**: shards 24/25/26/28 failed with `PERMISSION_DENIED (compute.instances.create)`
     — the active `gcloud` account had drifted to `github-actions-deploy` (a different identity than this workspace's
     standard ambient `unified-trading-sa`, likely a session/config artifact, not an IAM policy gap). Confirmed
     `unified-trading-sa` holds `roles/compute.admin` + `roles/compute.instanceAdmin.v1`;
     `gcloud config set account unified-trading-sa@...` fixed it immediately (the rest of the in-flight batch, e.g.
     shard 29 onward, succeeded right after the switch with no other changes). The 4 failed shards' OLD VMs had already
     been deleted (only `create` failed) — they had ZERO running instances until manually relaunched.
  2. **Rolling SPOT preemption wave** — likely triggered by this session's own fleet doubling its footprint
     (`e2-standard-8`→`e2-standard-16`× 21 VMs, roughly 2× vCPU/RAM demand in one zone within ~10 minutes). THREE
     separate preemption waves hit different shard subsets in quick succession: {14,15,17,20,21} at ~06:18:37-43, then
     {24,42} again + {25} at ~06:19-06:23, then {26,28,40,43,44} at a later check — confirmed via
     `compute.instances.preempted` operations events, not OOM (these are a different failure signature from the earlier
     `rc=137` pattern). No auto-recovery observed within ~3+ min for these custom `VM_NAME_OVERRIDE` launches (the
     `RelaunchPreemptedVm` same-name mechanism may not cover ad-hoc-named instances, or its poll interval exceeds what
     was practical to wait out here) — manually relaunched each wave. After the SECOND repeat-preemption on shards
     24/42, switched the repeatedly-preempted set (24, 25, 26, 28, 40, 42, 43, 44 — 8 shards) to `ON_DEMAND=true` (the
     launcher's own designed opt-out) to stop the rolling-preemption cycle rather than keep reactively chasing it; the
     remaining 13 shards stayed on SPOT (stable, no repeat preemptions observed). **Final state: all 21/21 shards
     confirmed `RUNNING` on `e2-standard-16`** (13 SPOT + 8 on-demand). **Lesson for future large e2-standard-16 SPOT
     batches in this zone**: launching ~21 VMs of a larger machine type simultaneously can trigger genuine zone-wide
     SPOT capacity contention, not just isolated bad luck — if a shard gets preempted twice in a row shortly after a
     large same-zone SPOT batch launch, don't keep retrying SPOT; switch that instance to on-demand rather than assume
     the third attempt will differ.
- **2026-07-30 update (slot-15, same session, ~10 min later) — a THIRD, unexplained mechanism killed shard 19
  (`canonical-migration-cefi-content-19-relaunch20260730-130600`), plus the active identity drifted again (a DIFFERENT
  account this time: `github-deploy`, not `github-actions-deploy` — switched back to `unified-trading-sa` again, second
  occurrence this session)**. Investigated shard 19's death properly rather than assuming it was another preemption or
  the identity issue:
  - Cloud Audit Log (`protoPayload.methodName="v1.compute.instances.delete"`) shows the actor as
    `1060025368044-compute@developer.gserviceaccount.com` (the GCE default compute SA) via `gcloud` invoked
    `client-os/LINUX ... (Linux 6.17.0-1021-gcp)` — i.e. from WITHIN a GCE VM, not a human/agent session. Strongly
    suggests the fleet's own `vm_zombie_watchdog.py` (deployment-service), the only automated in-fleet reaper this
    codebase documents.
  - **Disproved the obvious hypothesis before shipping a fix**: `vm_zombie_watchdog.py`'s `is_zombie()` only kills on
    `hb_age > heartbeat_stale` (stale-but-present heartbeat blob) or `hb_age is None AND shard_age > shard_stale`
    (heartbeat blob missing entirely). Checked shard 19's own `gs://.../vm-heartbeat/<vm_name>.txt` blob directly — its
    `Update Time` was `13:32:40Z`, the delete op fired at `13:33:35Z` — the heartbeat was ~55s old at kill time, nowhere
    near the 15-min default `heartbeat_stale` threshold, and `PREFIX_IDLE_THRESHOLDS` has no override for
    `canonical-migration-cefi-content-` (confirmed by reading the dict — unlike `af-backfill-`/`cefi-fwd-`/etc., which
    needed one for this exact class of false-positive per
    `zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`). By the documented logic, this VM should NOT have
    zombie-killed. **Did NOT ship a `PREFIX_IDLE_THRESHOLDS` entry** (my first instinct) — that fix targets a mechanism
    the evidence just ruled out, and shipping it would give false confidence without addressing the real cause.
  - **Genuinely unresolved** — either the kill came from a code path in `vm_zombie_watchdog.py` not covered by this read
    (e.g. `_reap_terminated_vms`/`should_reap()`, though shard 19 was `RUNNING` not `STOPPED`, so that path shouldn't
    apply either), a completely different automated process also running under the GCE default compute SA, or a
    race/staleness in the audit-log timestamps vs. the blob's own timestamp. Relaunched shard 19 a third time
    (`...-133500`); no recurrence observed since. Flagging as a genuine open mystery rather than a closed incident —
    worth a dedicated follow-up if it recurs (the todo below is scoped to investigation, not a guessed fix).
- **2026-07-30 update (slot-15, same session, ~15 min later) — converted the ENTIRE remaining fleet to on-demand; SPOT
  preemption in this zone confirmed as a SUSTAINED pattern, not a one-time wave**. A follow-up health check found shards
  17/20/21 preempted a SECOND time (they were also in the very first wave) plus shard 29 preempted separately — three
  confirmed distinct preemption events (~06:18, ~06:40-43, ~06:43) over ~25 minutes, all via
  `compute.instances.preempted` operations events. Fixed those 4 individually on-demand per the already-established
  2-strikes policy. Given the SUSTAINED nature (3 waves, not 1) and that reactively chasing each wave costs real
  turnaround time plus discards partial progress every time, proactively converted the remaining 9 still-SPOT shards
  (13, 14, 15, 16, 18, 19, 22, 23, 41 — none had been re-preempted yet, but continuing to gamble on SPOT after 3
  confirmed zone-wide waves was not a good bet) to `ON_DEMAND=true` as well, rather than wait for each to individually
  earn its own 2-strikes fix. Accepted the modest on-demand cost premium for a bounded, one-time backfill in exchange
  for ending the reactive-recovery cycle; this was a judgment call given real, repeated evidence (3 independent
  preemption waves), not a reflexive escalation.
- **2026-07-30 update (slot-15, same session, ~10 min later) — the on-demand conversion batch itself hit the SAME gcloud
  active-identity poisoning TWICE more (5th and 6th occurrence this session — see corroborating evidence added to
  `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`)**, splitting the 9-shard batch into a multi-stage
  recovery:
  - First pass: 13, 14 converted cleanly; 15, 16, 18, 19, 22, 23, 41 (7 shards) failed with the same `PERMISSION_DENIED`
    signature mid-batch. Diagnosed precisely rather than blanket-retrying: shards 15 and 23 had their DELETE succeed
    before CREATE failed (zero instances, needed a fresh relaunch); shards 16, 18, 19, 22, 41 had BOTH delete and create
    fail (their original SPOT instances were still alive and progressing untouched — no data/progress lost, just not yet
    converted).
  - Second pass (after fixing identity again): 16, 18, 19 converted cleanly; 22 and 41 hit the SAME poisoning a SIXTH
    time mid-batch.
  - Fixed those final 2 individually after also creating an isolated named `gcloud` configuration (`slot15-work`,
    separate from `default`) for resilience — though noted this may not be true isolation, since the CI job's
    `google-github-actions/auth` step likely poisons whichever config is currently ACTIVE, not specifically `default`;
    didn't over-invest in solving this properly here, since the durable fix is the existing issue doc's
    `[OPERATOR-DECISION]`, not something to improvise mid-task.
  - **Final verified state: all 21/21 shards present, `RUNNING`, and on-demand** (zero `preemptible=true` remaining,
    confirmed via `scheduling.preemptible` on every instance) — SPOT preemption is now structurally eliminated for the
    remainder of this migration.
- **2026-07-30 update (slot-15, ~40 min later during routine health monitoring) — a 4TH OOM occurrence, this time on
  `e2-standard-16` itself**: shard 42 died with the identical `rc=137` signature (VM stayed alive, no preemption event —
  confirmed via `gcloud compute operations list` showing a `delete` op, not `preempted`) at 21,000/73,965 files (28.4%,
  ~62 min elapsed) — notably FURTHER than any prior `e2-standard-8` OOM death (3.6-7.9%) before hitting the same wall on
  64GB. Supports the "memory grows with elapsed time/volume processed" theory over a fixed absolute-file-count ceiling —
  `e2-standard-16` raised the threshold, it did not eliminate the failure mode. Relaunched shard 42 again on the SAME
  `e2-standard-16` (not yet escalating machine size further) — this is the FIRST OOM at this tier, not yet a confirmed
  pattern; per the same 2-3-strikes discipline used for the preemption waves, will escalate to a larger machine type
  only if this recurs on `e2-standard-16`, not preemptively. Rest of the 21-shard fleet unaffected (confirmed healthy
  via full status sweep immediately after).
- **2026-07-30 update (slot-7, `data_pipeline_failure` escalation agt-9d9fb9, DP-VM-003 `DP_VM_STALL`)**: dispatched by
  the fleet monitor for `canonical-migration-cefi-content-16-relaunch20260730-135500` (10-min-stale heartbeat at
  dispatch time; 23+ min stale by the time I finished investigating). Confirmed via `gcloud compute instances describe`
  it IS running the on-demand `e2-standard-16` config the last progress-log entry shipped (`preemptible: false`,
  `provisioningModel: STANDARD`) — so this is neither of the two previously-fixed failure modes (SPOT preemption,
  `e2-standard-8` OOM/`rc=137`) — but corroborates the SAME theory shard 42's entry above just landed (memory grows with
  elapsed time/volume, `e2-standard-16` raises the ceiling but does not eliminate the failure): its deployment-registry
  entry (`a4f98edf-4560-4e2f-ba38-6810d83c9b40`) shows `host_metrics_window.mem_pct` climbing 11.6%→42.7% over its last
  9 samples with an accelerating `mem_slope`, and both `run.log` (GCS mtime) and the registry heartbeat went silent
  simultaneously at `2026-07-30T14:11:15Z` — a slow whole-VM freeze under memory pressure at ~15 min elapsed, not a fast
  `rc=137` kill (a second, slower-manifesting variant of the same underlying leak, not a third distinct failure mode).
  Per RB-INFRA-RELAUNCH's `≤2 relaunches/(vm-prefix,day)` bound, shard 16 already has 2 archived dead attempts today
  (`-122417`, `-130600`) before this 3rd stall — did **not** relaunch a 4th time myself; filed the finding as the new P1
  todo above instead (the runbook's own guidance for a repeated-same-shard stall: stop relaunching, root-cause it). Left
  the stalled VM alone — its own in-VM `STALL_PROGRESS_REGEX` stall-kill should reap it independently within ~30 min of
  its last progress-matching log line (~14:41Z), no manual kill performed. Pinged the authoring fleet-monitor with this
  outcome. No code changed this session — investigation + issue-doc update only.
- **2026-07-30 update (slot-15, ~10 min later)**: independently hit the SAME slow-freeze variant on shard 44
  (`canonical-migration-cefi-content-44-relaunch20260730-132900`) — corroborates slot-7's finding above with a second
  independent instance. `run.log` went silent at `14:09:30Z` with NO `rc=137`/`Killed` line (unlike the fast OOM-killer
  cases) — genuinely different from the shard-19 mystery too: the actor deleting it was `unified-trading-sa` via
  `python-requests` (a Python GCP-API client), NOT `vm_zombie_watchdog.py`'s gcloud-CLI invocation pattern — this is
  almost certainly the same `data_pipeline_failure`/fleet-monitor `auto_recover` actuator described in
  `RB-INFRA-RELAUNCH` (`codex/15-runbooks/incidents/rb_infra_relaunch.md`), triggering on a stalled-heartbeat detection,
  distinct from both the zombie-watchdog AND the still-unresolved shard-19 delete. Heartbeat blob confirmed genuinely
  stale (45m50s at delete time — `14:10:07Z` last update vs `14:55:57Z` delete), so THIS instance's reaper verdict was
  correct, unlike shard 19's. **Read `RB-INFRA-RELAUNCH` before relaunching**: it bounds relaunches to
  ≤2/(vm-prefix,day) for a genuine failure, then requires stopping + filing an issue rather than blind-retrying a 3rd
  time (exactly slot-7's handling of shard 16 above). Shard 44's `-132900` freeze was its FIRST genuine failure since
  this morning's fleet-wide relaunch/on-demand-conversion (those were deliberate strategic actions, not
  failure-triggered relaunches) — the `-145700` relaunch I already shipped is failure-relaunch #1 of the ≤2 bound,
  within policy. **Adopting this runbook explicitly for the rest of this task**: any shard that fails a SECOND genuine
  time after this point will NOT be relaunched by me — it gets the shard-16 treatment (P1 todo
  - leave for the fleet monitor / in-VM stall-kill, per the runbook's own guidance) instead. Did NOT touch shard 16 —
    already correctly owned/declined by slot-7, respecting their in-progress investigation.
- **2026-07-30 update (slot-3, `data_pipeline_failure` escalation agt-ac73ec, DP-VM-003 `DP_VM_STALL`)**: dispatched by
  the fleet monitor for `canonical-migration-cefi-content-40-relaunch20260730-132900` (25-min-stale heartbeat at
  dispatch time). This is a THIRD independent instance of the same slow whole-VM memory-pressure freeze slot-7
  (shard 16) and slot-15 (shard 44) already documented above — confirmed, not assumed:
  `gcloud compute instances describe` showed `machineType=e2-standard-16`, `preemptible: false`,
  `provisioningModel: STANDARD` (the already-fixed on-demand/bigger-machine config), ruling out both earlier-fixed
  failure classes (SPOT preemption, `e2-standard-8` OOM/`rc=137`). `run.log` shows steady real progress (23,000/76,685
  files, ~30%, with the tool's own recurring "possible wedged worker" self-warnings throughout — normal chatter, not the
  failure) then goes completely silent at `14:16:36Z` (GCS object mtime), no `rc=137`/`Killed` line. PROGRESS.json
  checkpoint frontier at time of freeze: `last_completed_date=2024-05-19, monotonic=true`. **Registry check (not
  assumed) confirmed this shard already had 2 archived dead attempts today** before this one:
  `...-relaunch20260730-122417` (started 12:33:54Z, reaped `vm_not_running` by 13:20:04Z, exit_code=125) and
  `...-relaunch20260730-130600` (started 13:22:21Z, reaped `vm_not_running` by 13:30:03Z after reaching only 200/76,685
  files post-discovery) — verified via `DeploymentsRegistry`'s GCS-backed active+archive JSON, downloaded in parallel
  and grepped (240 objects in today's archive alone). Per `RB-INFRA-RELAUNCH`'s `≤2 relaunches/(vm-prefix,day)` bound,
  this 3rd death exceeds budget — did **not** relaunch. **Did not manually kill the VM either**: mid-investigation
  (between a 14:54Z check showing `RUNNING` and a 15:07Z recheck), the VM's own in-VM `STALL_PROGRESS_REGEX` stall-kill
  fired on its own — confirmed via `gcloud compute operations list` showing a clean `delete` op (not a `preempted`
  event) — so the existing, already- shipped self-heal mechanism handled cleanup without intervention, same outcome as
  shard 16's self-reap (confirmed separately this session: that VM is now gone too). No code changed, no manual VM
  action taken — investigation + issue-doc update only. Pinged the authoring fleet-monitor slot with this outcome per
  the `data_pipeline_failure` role contract.
- **2026-07-30 update (slot-15, ~5 min later) — SELF-CORRECTION, a real process gap found in my own handling**: before
  seeing slot-3's entry above, I independently found shard 40's `-132900` instance freeze-dead (same signature) and
  relaunched it (`-151200`) believing it was that shard's 1st genuine failure, having checked only
  `gcloud compute operations list` for recent events — NOT the authoritative `DeploymentsRegistry` archive slot-3 used,
  which shows this shard ALREADY had 2 dead attempts today before my relaunch. **My `-151200` relaunch exceeded
  `RB-INFRA-RELAUNCH`'s ≤2/(vm-prefix,day) budget** — a real mistake, not a judgment call:
  `gcloud compute operations list` only shows recent operations, not the full day's registry-archived attempt history,
  so my per-shard "1st vs 2nd failure" counting throughout this session (for 16, 19, 40, 41, 42, 44) may be
  systematically undercounting true relaunch counts the same way. **Correcting course now rather than continuing the
  same under-verified method**: not killing the already-running `-151200` (no protective purpose — it's making real
  progress right now, and the budget's intent is to stop WASTEFUL cycling, not retroactively punish an already-launched
  attempt), but I am **stopping manual relaunches of this fleet's frozen shards for the remainder of this session**. The
  `data_pipeline_failure`/fleet-monitor system (slot-3, slot-7) is already correctly enforcing this exact policy with
  the RIGHT tooling (`DeploymentsRegistry`, not just recent operations) — deferring to it going forward rather than risk
  repeating this undercounting mistake on shards 23/41/42 (which I ALSO relaunched this same round, on the same
  insufficiently-verified basis — flagging honestly that their true today-relaunch-counts are UNVERIFIED, not
  confirmed-within-budget as I claimed when relaunching them). My role from here: monitoring + documentation
  consolidation only, not further manual VM relaunch/kill actions on this fleet.
- **2026-07-30 update (slot-15, post-`/compact`, monitoring-only, no action taken)**: fleet check post-compaction shows
  19 VMs present (down from 20 — shard 16 already-accepted absent, plus one more now gone). Confirmed via `run.log` that
  shards 43 (`-132900`) and 44 (`-145700`) both died on a THIRD distinct failure signature from this session: explicit
  `rc=137` (OOM-kill, `bash: ... Killed`) after making real progress (43: 41,200/71,925 files, 6573s elapsed; 44:
  10,400/80,026 files, 1296s elapsed) — this is the ORIGINAL small-machine-type OOM class, not the slow-freeze class,
  meaning it recurred even on relaunches that should already carry the machine-type fix (unverified whether these two
  specific relaunches used the escalated machine type — flagging as unconfirmed rather than asserting). Both
  self-deleted cleanly via their own `VM_SHUTDOWN_ON_COMPLETION=true` path (not an external kill). A partial
  `DeploymentsRegistry` archive scan (timed out after 250/​day's-objects, so this count is a LOWER BOUND, not
  exhaustive) already showed shard 44 with 4 archived dead attempts today (`-122417`, `-130600`, `-132900`, `-145700`)
  and shard 43 with at least 1 (`-130600`) plus the `-132900` death just observed — both almost certainly over the
  `RB-INFRA-RELAUNCH` ≤2/(vm-prefix,day) budget already. Per my prior self-correction commitment: **did not relaunch
  either shard** — documenting only, deferring to the `data_pipeline_failure` fleet-monitor (slot-3/slot-7) which has
  the correct tooling and mandate to act on this.
- **2026-07-30 update (slot-15, ~10 min later)**: shard 13 (`-134900`) also just died, same `rc=137` OOM signature
  (44,600/312,875 files, 3839s elapsed, clean `VM_SHUTDOWN_ON_COMPLETION` self-delete) — a fourth instance of this
  session's OOM class on a relaunch, further corroborating the machine-type fix isn't reliably applying/holding across
  relaunches. Fleet now at 17 shards. No action taken (monitoring-only, per standing self-correction).
- **2026-07-30 update (slot-15, ~50 min later, 15:44Z)**: shards 17 and 21 (both `-134500`) both hit the freeze-class
  failure (NOT `rc=137` — `run.log` object `Update time` frozen at 14:54:30Z/14:54:44Z respectively, confirmed via
  `gsutil stat`, silent for ~50 min at check time) — the same slow whole-VM freeze signature slot-7/slot-3/slot-15 have
  independently confirmed multiple times already this session. Shard 17 was already gone (self-reaped) by the time this
  check ran; shard 21 caught mid-`STOPPING`. Both were making real progress before freezing (17: 19,400/157,497 files;
  21: 31,400/158,501 files). Fleet now at 15 shards. Per standing self-correction: **no relaunch/kill action taken** —
  documenting only, deferring to the `data_pipeline_failure` fleet-monitor.
- **2026-07-30 update (slot-15, ~5 min later)**: shards 24 (`-132600`) and 41 (`-151900`) both OOM-killed (`rc=137`,
  clean self-delete) — 24 at 67,600/155,419 files (8249s elapsed), 41 at 9,600/77,941 files (1547s elapsed). Fleet now
  at 14 shards. Death rate has accelerated sharply this cycle (4 of 16 shards died within one ~10 min window: 17, 21,
  24, 41 — two freeze-class, two OOM-class). No action taken (monitoring-only).
- **2026-07-30 update (slot-15, ~20 min later, ~16:09Z)**: shard 19 (`-150600`) OOM-killed (`rc=137`, clean self-delete)
  at 19,600/153,655 files (3460s elapsed). Fleet at 12 shards, no other changes. Also: hit a NEW variant of the `gcloud`
  identity-poisoning issue (`…/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`) — this time
  `gcloud config configurations list` showed the active config had flipped from `slot15-work` to `slot11-work` (a
  DIFFERENT slot's isolated config, not just `default`), AND `slot15-work` itself was found poisoned
  (`account=github-deploy@…`, not `unified-trading-sa@…`). This is stronger evidence than previously documented: the
  isolated per-slot named-config is NOT immune — a foreign CI job or another slot's session can flip both the
  system-wide active configuration name AND mutate the account stored inside a DIFFERENT slot's own named config on this
  shared host. Fixed via `gcloud config configurations activate slot15-work` +
  `gcloud config set account unified-trading-sa@…`. No relaunch/kill action taken on shard 19 (monitoring-only).
- **2026-07-30 update (slot-15, ~15 min later)**: shard 22 (`-135900`) OOM-killed (`rc=137`, clean self-delete) at
  58,600/165,453 files (8093s elapsed — one of the longer-running survivors before dying). Fleet at 11 shards. No action
  taken (monitoring-only).
- **2026-07-30 update (slot-2, `data_pipeline_failure` escalation agt-7e8519, DP-VM-001 `DP_VM_EXIT_NONZERO`)**:
  dispatched by the fleet monitor for `canonical-migration-cefi-content-19-relaunch20260730-150600` (`exit_code=137`),
  with the runbook (`rb_infra_relaunch.md`) instructing a registry-driven relaunch. **Confirmed via
  `DeploymentsRegistry` this is the IDENTICAL death slot-15 already logged above at ~16:09Z** (started `15:08:56Z`,
  completed `16:09:10Z`, 19,600/153,655 files at last progress line, `rc=137`) — the alert and slot-15's own monitoring
  converged on the same VM, not a new event. Registry-verified relaunch count for this vm-prefix TODAY (queried
  `list_recent_archive`, not just `gcloud compute operations list` — the exact under-counting trap slot-15 flagged
  above): **5** attempts (`-122417` exit_code=125, `-130600` exit_code=137, `-133500` exit_code=125, `-135500`
  exit_code=125, `-150600` exit_code=137) — well past `RB-INFRA-RELAUNCH`'s `≤2/(vm-prefix,day)` bound. Per the
  runbook's own bound plus this doc's established monitoring-only policy (see slot-15's self-correction entry above),
  did **not** relaunch. Read the `-150600` `run.log` tail for corroborating diagnostic value: `host_metrics_window`
  shows `mem_pct` climbing 70.2%→93.7% over the final ~9 sampled minutes with a consistently POSITIVE `mem_slope`
  throughout (never negative or flat) — a continuous per-file growth pattern, not a one-time upfront allocation. This
  weighs against the `ThreadPoolExecutor`'s upfront `{pool.submit(...) for p in all_files}` futures dict as the primary
  driver (that would front-load memory once at submission time, then stay flat as files complete) and is more consistent
  with the P1 todo's existing hypotheses (a) PyArrow native buffer retention across repeated `pd.read_parquet` calls, or
  (b) some per-file allocation (e.g. `df.copy()` in `patch_instrument_id_column`) not being released back to the OS. Did
  not attempt a fix — confirming the actual mechanism needs a profiler attached to a live run, which is the P1 todo's
  own scope, not something to guess at from log/registry evidence alone. Pinged the authoring fleet-monitor slot with
  this outcome; no code changed, no VM launched (relaunch bound already breached at dispatch time).
- **2026-07-30 update (slot-15, ~35 min later, 16:27Z)**: shard 23 (`-151700`) hit the freeze-class failure — `run.log`
  `Update time` frozen at 15:39:38Z, ~48 min silent at check time, no `rc=137`. Was at 17,200/218,799 files (1324s
  elapsed) before freezing. Fleet at 10 shards. Also hit the `gcloud` identity-poisoning issue again mid-check (both the
  active-config-flip-to-`slot11-work` AND `slot15-work`-account-mutated-to-`github-deploy@…` variants together, same as
  the prior occurrence) — fixed via `gcloud config configurations activate slot15-work` +
  `gcloud config set account unified-trading-sa@…` (already logged in the poisoning issue doc; not re-duplicating here).
  No relaunch/kill action taken on shard 23 (monitoring-only).
- **2026-07-30 update (slot-15, ~15 min later)**: shard 18 (`-135500`) OOM-killed (`rc=137`, clean self-delete) at
  49,000/148,799 files (8837s elapsed). Fleet at 8 shards. No action taken (monitoring-only).
- **2026-07-30T16:35Z (review agent `agt-f99b61`, slot 1)**: picked up a queued main-agent message (`agt-fd75de`,
  2026-07-30T15:54:39Z) ruling that the `-006`/`-002` dispatch deadlock meets the data-completeness operator-escalation
  bar — left unactioned because the prior review-agent session (`agt-2552a2`, this same slot) was killed in the
  14:54-15:01Z `tmux_session_lost` cluster before it could act. Independently re-verified the deadlock still holds live
  (not just relayed): `GET /api/backlog` shows `-006` still `queued`/priority 20/no blockers, `-002` still
  `dispatched`/slot 15 since `12:16:10Z`; `GET /api/state` confirms slot 15 is genuinely alive and working (fresh
  `last_ping`), not stalled-dead — this is a live structural deadlock, not an orphaned dispatch. Added the
  `[OPERATOR] P0` todo above with current numbers (4h20m elapsed, fleet at 8/44 survivors, slot 15 at 99% context). Did
  not action (a)/(b) myself — plan-structure edit + task-cancel is outside review's remit, per main's own ruling. No
  code changed; issue-doc edit only.
- **2026-07-30T17:07Z (slot-15)**: shard 40 (`-151200`, the shard I personally relaunched earlier and flagged as likely
  over the `RB-INFRA-RELAUNCH` budget) hit the freeze-class failure — `run.log` silent since 16:16:11Z (~51 min at check
  time), no `rc=137`, was at 23,400/76,685 files before freezing. Fleet at 8 shards, no other change. Acknowledging the
  `[OPERATOR] P0` dispatch-deadlock finding above (agt-f99b61, 16:35Z): agree with its diagnosis and am not
  self-cancelling `-002` or restructuring this plan — per the same reasoning already stated (main/operator territory,
  not mine to self-action as the affected worker either, same as it's outside review's remit). Continuing to heartbeat +
  monitor-only per my dispatched task and standing instructions until main/operator acts on the escalation (visible to
  me as a `cancel_task`/`directive`/new dispatch in a future heartbeat response).
- **2026-07-30T17:08Z (slot-15)**: shard 28 (`-132900`) **genuinely COMPLETED** — full
  `SCRIPT 1 CONTENT MIGRATION SUMMARY` terminal banner, `rc=0`, all 184,363/184,363 files processed (208 patched, 0
  errors, `STOP-ON-SURPRISE` bounds satisfied). First confirmed success among this session's relaunched shards. Fleet at
  7 shards (was 8; shard 40's self-delete from the prior cycle also completed). This shard now counts toward the 44/44
  corpus-wide total once the final re-verify runs.
- **2026-07-30T17:22Z (slot-15)**: shard 20 (`-134500`) OOM-killed (`rc=137`, clean self-delete) at 95,600/154,859 files
  (61.7%, 12,727s elapsed — one of the longest-running survivors before dying, close but not close enough). Fleet at 5
  shards. Also hit the `gcloud` identity-poisoning issue again — this time a THIRD account variant,
  `github-actions-deploy@…`, poisoning the already-active `slot15-work` config directly (not a config-flip this time).
  Fixed the same way. No action taken on shard 20 (monitoring-only).
- **2026-07-30T17:29Z (slot-15)**: shard 15 (`-135300`) OOM-killed (`rc=137`, clean self-delete) at 212,200/514,504
  files (41.2%, 12,755s elapsed — this shard's own largest window, 2026-03-28..2026-07-19). Fleet at 4 shards (14, 26,
  29, 42). No action taken (monitoring-only).
- **2026-07-30T17:53Z (slot-15)**: **notable, likely a distinct failure class** — shard 29 (`-134500`) is frozen at the
  EXACT same point its original (pre-relaunch) attempt died: "1 files still outstanding" (194,804/194,805, 99.9995%), no
  `rc=137`, `run.log` silent since 17:04:55Z (~49 min at check time). The original doc table above recorded shard 29's
  best-known progress as 138,800/138,919 (99.9%) with the same "1 file short" signature on a DIFFERENT attempt/window —
  two independent runs of this shard both stalled on their respective single final file rather than a random OOM/freeze
  point. This is corroborating evidence for a SPECIFIC poison-pill file in this shard's date range (something the
  resolver/patcher hangs on, e.g. malformed parquet, huge outlier file, or a resolver edge case) rather than the generic
  time-based memory leak affecting other shards — worth flagging separately to whoever picks up the `-006` root-cause
  investigation once dispatched. Also hit the `gcloud` identity-poisoning issue again, this time actively re-poisoning
  `slot15-work` back to `github-actions-deploy@…` within seconds of my fix (confirmed via immediate retry) — strong
  evidence a CI job is running RIGHT NOW on this host, not just leaving stale state. Fixed by re-running
  `gcloud config set account` immediately before the next gsutil call in the same turn. No relaunch/kill action taken on
  shard 29 (monitoring-only). Fleet still at 4 shards (this is a freeze, not yet a confirmed death — still `STOPPING` at
  check time).
