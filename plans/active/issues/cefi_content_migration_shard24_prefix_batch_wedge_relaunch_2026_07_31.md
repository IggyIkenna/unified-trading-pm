---
doc_type: issue
title: >-
  Shard 24 (canonical-migration-cefi-content-24) — pre-fix `-032606` batch wedge, checkpoint-resumed relaunch on the
  fixed tarball
summary: >-
  Split out of `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` (that doc is at its 1000-line hard cap) to
  avoid growing it further. DP-VM-003 (`agt-3b5ecf`, slot 4, 2026-07-31) dispatched for
  `canonical-migration-cefi-content-24-relaunch20260731-032606` (heartbeat 48m stale at dispatch). This is NOT a new
  root cause — it is a corroborating 5th+ instance of the SAME `-032606`-batch pre-fix silent-freeze wedge already
  root-caused and fixed in the parent doc (`market-tick-data-service@55d051bd`, the `hard_deadline` scaling bug),
  alongside shards 17/21 already documented there. Action taken: verified genuinely dead (registry `reap_reason`
  sentinel, not a real exit code), confirmed within the daily relaunch budget (1st failure-relaunch for this shard
  today), checkpoint-resumed from `PROGRESS.json` (`last_completed_date=2026-01-06` → relaunched from `2026-01-07`,
  not a blind replay of the original `2026-01-02`), relaunched on the now-fixed tarball
  (`mtds-code@90e9876cd3a4`, confirmed `55d051bd` is an ancestor), verified STARTED + real per-file PROGRESS. No code
  changed.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, migration, canonicalisation, vm-fleet, vm-relaunch, dp-vm-003, data-pipeline]
related:
  [
    cefi_content_migration_fleet_half_incomplete_2026_07_26,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-07-31
priority: P3
parent_epic: cefi_master
source: "data_pipeline_failure escalation agt-3b5ecf, slot 4, 2026-07-31 -- DP-VM-003 relaunch of canonical-migration-cefi-content-24"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.05
estimate_calibrated_ai_days: 0.02
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# Shard 24 — pre-fix batch wedge, checkpoint-resumed relaunch (no new root cause)

## What I found

Dispatched via DP-VM-003 (`agt-3b5ecf`) for `canonical-migration-cefi-content-24-relaunch20260731-032606`
(`WARN DP_VM_STALL`, heartbeat 48m stale at dispatch, `context` carried `RELAUNCH vm=... launcher=launch-canonical-
migration-vm.sh asset_group=cefi` per `rb_infra_relaunch.md`; no separate issue had been filed — the alert carried the
details).

The named VM did **not** exist under `gcloud compute instances list` in any state — this is expected, not an anomaly:
`heartbeat_stall_watcher.sweep()` both raises the WARN finding AND (once the stall age passes `kill_minutes=45`) calls
its own `vm_killer` to auto-kill the VM in the same pass ("auto-kill + respawn then file issue" is the documented
DP-VM-003 escalation shape) — the escalation to me is specifically the "respawn" half, which the in-image actuator
can't do (packaging gap, `data-pipeline-alerts.md` § Self-heal actuator layer). `DeploymentsRegistry.list_recent_archive()`
confirmed the row: `deployment_id=4ba61339-8f5d-44cb-b8ea-56ec4f11d618`, `status=failed`, `exit_code=125`,
`completed_at=2026-07-31T06:36:39Z`. **`exit_code=125` here is a generic sentinel, not a real process exit code** —
`DeploymentsRegistry.reap_stale()` (`unified_trading_library/deployment_registry.py:559-599`) stamps it on every entry
archived for `vm_not_running`/`heartbeat_stale`, regardless of cause; do not read it as "the migration script itself
returned 125."

`run.log` showed genuine steady progress (68,200/155,419 files, ~8.6 files/sec climbing, periodic pyarrow-pool-release
diagnostic lines firing normally) through `05:44:24Z`, then went **completely silent** — no `rc=137`, no `Killed`, no
exception, nothing — for the remaining ~52 minutes until the external reaper caught it. This is the exact signature the
parent doc already root-caused for shards 17/21 (both also from the same `-032606` launch batch, `03:26-03:30Z`
2026-07-31): `TARBALL_PINS.json` for my target confirms it launched with all 4 tarballs FLOATING at `03:27:01Z` — i.e.
before `market-tick-data-service@55d051bd` (the `hard_deadline = 5s * total_files_discovered` fix, landed ~05:13Z) was
published. The wedged-worker force-exit safety valve was mathematically defeated for a shard this size (`5s *
135,828 files ≈ 7.9 days`), so once genuinely wedged (GIL contention / a hung native call — the `9f4098b1`
pyarrow-pool-release fix addresses memory GROWTH, not this), it could never self-heal and just sat until the
*external* heartbeat_stall_watcher's 45-min kill threshold caught it. **Not a new failure mode** — corroborating
instance #3 of the already-fixed `55d051bd` bug (after shards 17, 21).

## Why it matters

Same fleet-completion gap the parent doc tracks (shard 24 is one of the 18 shards not yet showing the terminal
`SCRIPT 1 CONTENT MIGRATION SUMMARY` banner in any attempt as of the 2026-07-31T03:30Z corpus-wide check). No new
code risk — filed for the audit trail (registry-verified budget count, checkpoint-resume math, tarball-fix
provenance) so a future corpus-wide re-verify or root-cause pass doesn't have to re-derive this shard's history from
raw GCS logs.

## Action taken (no code change)

1. **Budget check** (`RB-INFRA-RELAUNCH` ≤2/(vm-prefix,day)): `DeploymentsRegistry.list_recent_archive(days=3)`
   showed exactly one 2026-07-31 attempt for shard 24 (the `-032606` one that just died) — this relaunch is the 1st
   failure-triggered relaunch of the day for this shard, within bound.
2. **Checkpoint-aware resume**: `PROGRESS.json` for the dead VM read `last_completed_date=2026-01-06,
   monotonic=true` → relaunched from `2026-01-07` (end date unchanged, `2026-01-15`), not a blind replay of the
   shard's original `2026-01-02` start.
3. **Tarball freshness**: confirmed `unified-trading-sa` was the active identity (no gcloud poisoning this time),
   then launched — `lc_verify_tarball_freshness` reported all 4 tarballs fresh, `mtds-code @ 90e9876cd3a4`.
   `git merge-base --is-ancestor 55d051bd 90e9876cd3a4` confirmed the stall-timeout fix is included.
4. **Relaunched** as `canonical-migration-cefi-content-24-relaunch20260731-065001`
   (`MACHINE_TYPE=e2-standard-16`, SPOT default, `cefi-content-apply` category, `full` mode):
   ```
   MACHINE_TYPE=e2-standard-16 VM_NAME_OVERRIDE=canonical-migration-cefi-content-24-relaunch20260731-065001 \
     bash launch-canonical-migration-vm.sh cefi-content-apply 2026-01-07 2026-01-15 full
   ```
5. **Verified, not fire-and-forget**: `gcloud compute instances list` confirmed `RUNNING` at launch (T+~15s); a
   bounded background poll confirmed a real per-file `Progress:` line in `run.log` shortly after (see Progress Log
   for the exact line — appended once the poll returned).

## Recommended decision

- [ ] [SCRIPT] P3. Once this relaunch (and the fleet generally) settles, fold shard 24 into the parent doc's
      corpus-wide re-verify grep (`SCRIPT 1 CONTENT MIGRATION SUMMARY` banner check) rather than tracking it
      separately — this doc's only remaining purpose is the audit trail above. No action needed unless shard 24
      dies again; if it does, check whether it's now running the `55d051bd`-fixed code (it should be, per this
      doc) — a repeat wedge on this exact tarball would mean the fix is incomplete and warrants a fresh
      investigation, not another blind relaunch.

## Progress Log

- 2026-07-31 (`data_pipeline_failure` escalation `agt-3b5ecf`, slot 4): filed after splitting out of the parent
  fleet doc to keep it under its line cap. Diagnosis + relaunch as described above. Pinged the authoring slot
  (`dp-fleet-monitor`) with the outcome.
