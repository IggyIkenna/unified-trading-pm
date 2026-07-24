---
doc_type: issue
title: launch-features-sports-parallel-backfill-vm.sh silently deletes another shard's live VM on a single-VM relaunch
summary: >
  A `--vms 1` relaunch (the standard gap-fill pattern used repeatedly on
  sports_p2_features_history_to_ml_ready_2026_06_27.md) always names the new VM `fss-backfill-vm-1` regardless of what's
  already running, and the launcher unconditionally `gcloud compute instances delete`s any existing VM of that name
  before creating the new one (no collision check). If a DIFFERENT gap-fill (for a different date range) already claimed
  that freed name, the new relaunch silently kills it mid-run with no warning. Hit this live 2026-07-13 (slot 14): a
  gap-fill relaunch for vm-8's range (2023-01-26→2024-03-21) deleted slot-8's separate, actively-healthy
  OOM-verification VM (range 2018-06-17→2019-08-11). No data was lost this time (the two critical dates it had already
  captured survived, and recovery via the collision-free consolidated launcher was straightforward) but the next
  occurrence may not be caught as fast.
status: resolved
nature: notes
asset_group: [sports]
stage: [features]
repos: [deployment-service]
scope: [engineer]
tags: [vm-launcher, name-collision, footgun, sports, backfill]
related:
  [
    plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    plans/active/issues/features_sports_unbounded_memory_early_history_dates_2026_07_13.md,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source:
  sports_p2_features_history_to_ml_ready-001 dispatch, slot 14, 2026-07-13 (self-inflicted, caught + recovered same
  session)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-20
locked_by:
resolved_by: deployment-service@d3e1a3f
---

> **🟡 Priority bumped P2→P1 (2026-07-13, operator feedback)**: already caused one live-VM deletion this session; the
> fix is small enough that P1 is low-cost. See the Todos section.

# launch-features-sports-parallel-backfill-vm.sh name-collision-on-delete footgun

## What I found

`deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh` names every VM in a launch
`fss-backfill-vm-${VM_NUM}` where `VM_NUM` is always `1..NUM_VMS` for THAT invocation — a `--vms 1` relaunch is always
named `fss-backfill-vm-1`, with no way to target a different, currently-free slot number (no `--name`/`--offset` flag).

Before creating each VM, the launcher unconditionally deletes any existing VM of that name
(`launch-features-sports-parallel-backfill-vm.sh:392-396`):

```bash
# Delete existing VM if present (from previous run)
gcloud compute instances delete "${VM_NAME}" \
  --project="${PROJECT_ID}" \
  --zone="${ZONE}" \
  --quiet 2>/dev/null || true
```

This comment's own framing ("from previous run") assumes the only existing VM of that name is a stale leftover from the
SAME logical gap-fill being re-run — it does not anticipate that a DIFFERENT gap-fill (a different date range, launched
by a different dispatch/slot) may have already claimed that same freed number.

**Live incident (2026-07-13, slot 14)**: `sports_p2_features_history_to_ml_ready_2026_06_27.md`'s Todo 1 is a multi-day,
multi-VM fleet backfill worked across dozens of dispatches; individual shards die (OOM, preemption) and get gap-filled
with single-VM relaunches routinely — this is the ESTABLISHED, expected pattern per the plan's own Progress Log. Slot 8
(same day, earlier) gap-filled the dead `vm-4` shard by relaunching with `--vms 1`, which named the new VM
`fss-backfill-vm-1` (the original `vm-1` had already completed and freed that name). Later the same day, I
(independently) found `vm-8` dead (SPOT-preempted at 365/421 dates, no crash) and gap-filled IT the same way —
`--vms 1`, ALSO landing on the name `fss-backfill-vm-1`, which by then was slot-8's live, healthy, mid-run VM. My
launch's delete-before-create step silently killed it. No error, no warning —
`gcloud compute instances delete ... || true` swallows the fact that a live VM with real, unrelated, unfinished work
just got destroyed.

**Verified via the deleted VM's own `run.log`**: last real log line was <3 minutes before my delete, actively processing
fixture rows — this was not a leftover/stale VM, it was live production work.

## Why it matters

- This plan's own precedent is "gap-fill single shards with `--vms 1` relaunches" — happens multiple times per day
  across many dispatches/slots. Every one of those relaunches is a collision risk against ANY other slot's concurrent
  single-VM relaunch, silently, with no error surfaced to either party.
- The failure mode is silent — `2>/dev/null || true` means the deleting slot sees a normal-looking launch, and the
  victim slot's next check just finds its VM "mysteriously gone" with no correlation back to the cause unless someone
  manually reads timestamps closely (as this session did).
- This time the two most valuable outputs (the OOM-fix validation dates) had already landed before the kill, so recovery
  was cheap. A less lucky timing (e.g. the deleted VM mid-computing its own poison-date memory profile, or close to
  finishing a long range with no partial credit) could waste hours of VM-time and, worse, could destroy in-flight
  debugging state for a different active investigation.

## Recommended decision

Two independent, complementary fixes (not mutually exclusive):

1. **Collision check before delete** — before the unconditional `gcloud compute instances delete`, check if the existing
   VM (if any) has been alive/making-progress recently (e.g. `run.log` freshness <5 min, or simply check
   `STATUS == RUNNING` and require an explicit `--force-replace` flag to proceed if so). Refuse by default, matching
   this workspace's own git-multi-agent-safety pattern ("never overwrite live foreign WIP without a liveness check").
2. **Prefer the consolidated single-VM launcher for gap-fills** — `launch-features-vm.sh`'s
   `VM_NAME="features-${FAMILY_DASHED}-${ASSET_GROUP_LOWER}-${RUN_TS}"` naming (timestamp-suffixed) makes this whole
   class of collision structurally impossible. The parallel launcher's own docstring already recommends the consolidated
   launcher for "NEW single-VM features-sports backfills" — worth calling this out explicitly in this plan's own
   `## Mechanics` section so future dispatches default to it for single-shard gap-fills instead of `--vms 1` on the
   parallel launcher.

Did not implement either fix myself this dispatch — this is a shared launcher script touching every concurrent
dispatcher on this plan; a real fix needs its own scoped review + testing (verifying it doesn't break the legitimate
"re-run a truly-stale/dead VM of the same name" case), out of this data_engineering dispatch's craft scope.

## Todos

- [x] ✅ [INFRA] P1. Add a liveness/collision check to `launch-features-sports-parallel-backfill-vm.sh`'s
      delete-before-create step (line ~392-396) — refuse (or require an explicit override flag) if the existing VM of
      that name has a `run.log` fresher than ~5 minutes, rather than unconditionally deleting. (repo:
      deployment-service) — **bumped P2→P1 per operator feedback (2026-07-13): this already destroyed a live VM once
      this session, part of a broader unconditional-destructive-operation pattern; the fix is small (a liveness check)
      so P1 is low-cost.** — **FIXED, slot 11, 2026-07-13**: `deployment-service@d3e1a3f`. Added
      `lc_refuse_if_vm_alive()` to `scripts/vm/lib/launcher_common.sh` — refuses (exit 1, fails CLOSED when the log age
      is unreadable) if the exact-named VM is `RUNNING` with a `run.log` updated within the last 5 minutes;
      `--force-replace` overrides. Wired into `launch-features-sports-parallel-backfill-vm.sh` immediately before the
      delete-then-create step. Verified with `gcloud`/`gsutil` stubs across all 4 branches (running+fresh refuses;
      force-replace / not-running / stale-log all allow); `shellcheck` clean; full `quality-gates.sh` green.
- [x] ✅ [DOCS] P3. Add a one-line note to `sports_p2_features_history_to_ml_ready_2026_06_27.md`'s `## Mechanics`
      section recommending `launch-features-vm.sh --feature-family sports` (collision-free timestamped naming) over
      `launch-features-sports-parallel-backfill-vm.sh --vms 1` for single-shard gap-fill relaunches on this plan. (repo:
      unified-trading-pm) — **DONE, slot 4 (infra), 2026-07-14**: added the note as a new `## Mechanics` bullet on
      `sports_p2_features_history_to_ml_ready_2026_06_27.md`, linking back to this issue doc.
