---
doc_type: issue
title: asia-northeast1-c SPOT preemption storm — 151 preemptions/5h across sports/tradfi/cefi, ongoing
summary: >-
  Found while working `sports_af_full_entity_completion-003` (launch FIXTURE_LINEUPS after FIXTURE_STATS converges):
  relaunched FIXTURE_STATS (`af-backfill-20260804-004955`) and it was SPOT-preempted after only ~1.5 min
  (2026-08-04T00:51:21-32Z) — the THIRD preemption of this same entity's backfill in <24h, each one dying faster than
  the last (17min -> 6min -> ~1.5min). Checking the audit log for the broader picture: this is NOT an af-backfill-
  specific problem. `asia-northeast1-c` is in an active, sustained SPOT preemption storm — 151
  `compute.instances.preempted` events over the 2026-08-03T19:54Z..2026-08-04T00:54Z window (5h), hitting at least 3
  asset groups concurrently (sports `af-backfill-*`/`expected-universe-v2-sports-*`, tradfi
  `tradfi-bf-{nyse,nasdaq,cme,cboe}-ohlcv-1m-*`, cefi `cefi-aster-2026`), still firing as of the last check (3 events in
  the most recent 10-minute window). This is fleet-wide billing waste happening right now, not isolated to this campaign
  — flagging per the CLAUDE.md "regularly check every running VM for preemption ... billing waste" rule and the "big
  finding" escalation bar (affects 3+ asset groups' active backfills simultaneously).
status: open
nature: issue
asset_group: [sports, tradfi, cefi]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [vm-preemption, billing-waste, spot-capacity, cross-cutting, big-finding]
related:
  [
    /plans/active/issues/sports_af_full_entity_completion_2026_08_03.md,
    /plans/active/issues/af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md,
    /plans/active/issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md,
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
created: 2026-08-04
priority: P1
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "sports_af_full_entity_completion-003 (slot 5), 2026-08-04 — found while re-verifying the FIXTURE_LINEUPS launch
    gate",
  ]
drift_direction: advance-code
context_scope:
  [
    deployment-service/scripts/vm/launch-api-football-backfill-vm.sh,
    deployment-service/deployment_service/data_pipeline_monitors/exit_code_fleet_monitor.py,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
  ]
---

# asia-northeast1-c SPOT preemption storm

## What I found

Working `sports_af_full_entity_completion-003`. Re-verified the FIXTURE_LINEUPS launch gate per the standing risk note
in the gating doc: singleton lock was free (no `af-backfill-*`/`af-audit-*` VM RUNNING), but FIXTURE_STATS still had not
converged (125/68,409 non-MVP shards captured via `census_fixture_stats_lineups_widening_volume_2026_07_31.py` —
essentially flat vs. slot 6's last check). Relaunched FIXTURE_STATS as `af-backfill-20260804-004955`
(`--entity FIXTURE_STATS 2020-06-06 2026-08-04`, safe idempotent resume, no `--force`) to keep the campaign moving,
matching the pattern already used twice by slots 4 and 6.

This VM was preempted almost immediately:

```
gcloud logging read 'protoPayload.methodName="compute.instances.preempted" AND protoPayload.resourceName:"af-backfill-20260804-004955"'
2026-08-04T00:51:32Z  .../instances/af-backfill-20260804-004955
2026-08-04T00:51:21Z  .../instances/af-backfill-20260804-004955
```

Launched at 00:49:55Z, preempted at 00:51:21Z — a ~1.5 minute lifetime. This is the **third** preemption of the SAME
entity's backfill in under 24h (`af-backfill-20260803-233053` lived ~16min, `af-backfill-20260804-001203` lived ~6min,
`af-backfill-20260804-002608` — status unconfirmed but also gone by this check, `af-backfill-20260804-004955` lived
~1.5min), each one dying faster than the last.

Checked whether this is af-backfill-specific (as the two prior slots suspected) or something broader — it's broader.
Full audit-log sweep of `compute.instances.preempted` in `asia-northeast1-c`:

- **Last 10 min**: 3 preemption events (storm is ONGOING as of this check, 2026-08-04T00:54Z)
- **Last 3h**: preemption counts by VM-name family — `expected-universe-v2-sports` (10), `af-backfill` (10), then 2 each
  for ~20 distinct `tradfi-bf-{nyse,nasdaq,cme,cboe}-ohlcv-1m-*` shards, plus `cefi-aster-2026` (2)
- **Last 6h** (2026-08-03T19:54Z..2026-08-04T00:54Z): **151 total preemption events**

This spans at least 3 asset groups' active backfills (sports, tradfi, cefi) concurrently, all in the same zone, over a
sustained 5-hour window that is still active. This reads as a genuine SPOT capacity crunch specific to
`asia-northeast1-c` right now, not a bug in any one launcher — every affected campaign is bleeding SPOT compute-minutes
to preemption with proportionally little forward progress while it lasts.

**Distinct from, but adjacent to,** `af_backfill_preemption_auto_recovery_not_firing_2026_08_04.md` (already root-caused

- fixed: `af-backfill-`/`af-audit-` were missing from `_DATA_VM_PREFIXES`, so those VMs' preemptions were invisible to
  the auto-relaunch actuator). That fix addresses "preempted but never re-launched" — it does NOT address "gets
  re-preempted within ~2 minutes of every relaunch," which is what's actually blocking FIXTURE_STATS convergence right
  now. Even with working auto-recovery, a relaunch loop against an active capacity storm will keep failing
  near-instantly.

**Not yet checked** (out of this task's scope, flagging for the next investigator):

1. Whether the `af-backfill-`/`af-audit-` prefix fix (`deployment-service@c3594db647c25ae2656ba020e15d3f55a42bd179`) is
   actually live in the deployed `uts-prod-dp-exit-code-monitor` Cloud Run job image yet (image tag is a floating
   `:latest`; did not confirm the image was rebuilt from a commit at-or-after that SHA) — if not yet deployed,
   af-backfill preemptions during this storm are STILL invisible to auto-recovery on top of the storm itself.
2. Whether this is a known/expected SPOT market condition for this zone/time-of-day (transient, will clear on its own)
   or a genuine anomaly worth a support ticket / zone-diversification response.
3. Whether other campaigns' launchers (tradfi/cefi) have working auto-recovery that IS successfully relaunching them
   through this storm (making the same near-instant-repreemption tradeoff, just less visibly since a fix already covers
   their prefix) — if so, af-backfill riding it out via the now-fixed auto-recovery (once confirmed deployed) may be the
   right posture rather than a code change.

## Why it matters

- **Active billing waste, right now**: 151 preemption events in 5h across 3 asset groups means each affected campaign is
  burning SPOT minutes with minimal net throughput for as long as the storm continues.
- **Business-goal-critical for sports**: the operator's explicit ask (`sports_af_full_entity_completion_2026_08_03.md`)
  is full AF entity completion to downgrade the API-Football subscription — FIXTURE_STATS (gating FIXTURE_LINEUPS and
  the eventual re-census) has now made ~0 net progress across 4 launch attempts and ~3 preemptions in <24h, entirely
  attributable to this storm once the auto-recovery gap is factored out.
- **Cross-cutting**: not fixable by continuing to patch the sports/af-backfill launcher alone — tradfi and cefi
  campaigns are hitting the identical capacity wall in the same zone at the same time.

## Recommended decision

1. Someone with Cloud Build access should confirm whether `uts-prod-dp-exit-code-monitor`'s deployed image already
   includes `c3594db647c25ae2656ba020e15d3f55a42bd179` (rebuild timestamp vs. commit timestamp) — if not, expedite that
   redeploy so auto-recovery is genuinely live for af-backfill/af-audit before the storm clears.
2. Re-check the preemption rate in a few hours — if it has genuinely subsided, no further action needed beyond the
   redeploy-confirmation above (transient SPOT market condition). If it is still elevated after a full day, this
   deserves a proper capacity/zone-diversification decision (e.g., an alternate zone for backfill VMs, or a scoped
   on-demand exception for entities on a hard business deadline) — that tradeoff is an operator call, not a worker
   unilateral decision, given the HARD RULE that backfill VMs default to SPOT.
3. Do NOT keep blind-relaunching FIXTURE_STATS on a tight loop while the storm is this active — each attempt is
   consuming real compute for ~1-2 minutes of useful work. The sports campaign issue doc's Progress Log will track when
   it's safe to try again.

## Todos

- [ ] [SCRIPT] P1. Confirm whether `uts-prod-dp-exit-code-monitor`'s deployed Cloud Run image includes
      `deployment-service@c3594db647c25ae2656ba020e15d3f55a42bd179` (the af-backfill/af-audit prefix fix); if not,
      trigger a redeploy (repo: deployment-service).
- [ ] [SCRIPT] P2. Re-check `compute.instances.preempted` volume in `asia-northeast1-c` after several hours — confirm
      whether the storm has subsided; note the outcome in this doc's Progress Log (repo: deployment-service).
- [ ] [SCRIPT] P2. Once (1) is confirmed deployed, verify a real af-backfill preemption during this storm actually
      triggers `RelaunchPreemptedVm` end-to-end (not just that the VM is now visible to the classifier) (repo:
      deployment-service).

## Progress Log

- **2026-08-04 (slot 5)** — Filed while working `sports_af_full_entity_completion-003`. Confirmed the storm is broader
  than af-backfill (151 preemptions/5h across sports/tradfi/cefi, still ongoing). Did not attempt a further
  FIXTURE_STATS relaunch given the active storm — `skip-current-task`'d the sports campaign todo so it requeues once
  conditions improve.
