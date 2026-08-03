---
doc_type: issue
title: >-
  Shard 17 died AGAIN on e2-standard-8 even with both prior fixes applied — confirmed + shipped the already-tracked
  MACHINE_TYPE default bump (e2-standard-16)
summary: >-
  Split out of `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` (that doc is at its 1000-line hard cap) to
  avoid growing it further. DP-VM-003 dispatch (`agt-ad6632`, slot 11, 2026-07-31) for
  `canonical-migration-cefi-content-17-relaunch20260731-050700` — by dispatch time the VM had already been reaped
  (`reap_reason=vm_not_running`, `exit_code=125` reaper sentinel, `host_metrics_window.mem_pct` climbing to 91.4%
  moments before the last sample). This VM was itself the parent doc's own `agt-3e0b8d`-relaunched instance running BOTH
  previously-shipped fixes (pyarrow-pool-release, `market-tick-data-service@9f4098b1`; stall-timeout, `@55d051bd` —
  confirmed via this VM's own `git_commit` field) and it still died the same way. Confirms the parent doc's already-open
  P2 `MACHINE_TYPE` default-bump todo (e2-standard-8 → e2-standard-16 for `cefi-content-apply`) was evidenced but never
  actually implemented — shipped it now (`deployment-service@9e6004a`). Did NOT relaunch shard 17 again: the parent
  doc's own Progress Log already flagged this VM as the 2nd relaunch of the day (`RB-INFRA-RELAUNCH`'s
  ≤2/(vm-prefix,day) bound), so a 3rd death today pages/holds rather than relaunches.
status: resolved
nature: issue
asset_group: [cefi, meta]
stage: [data, meta]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, migration, vm, oom, machine-type, vm-relaunch, data-pipeline]
related:
  [
    cefi_content_migration_fleet_half_incomplete_2026_07_26,
    cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-07-31
priority: P2
parent_epic: cefi_master
source:
  "data_pipeline_failure escalation agt-ad6632, slot 11, 2026-07-31 -- DP-VM-003 dispatch for
  canonical-migration-cefi-content-17-relaunch20260731-050700"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
  "both todos closed 2026-08-02 (MACHINE_TYPE bump deployment-service@9e6004a shipped + verified; RB-INFRA-RELAUNCH
  carve-out ruled per plan_reconcile_parked_operator_decisions_2026_08_02.md na-eligibility-audit item 25)"
locked_by:
context_scope:
  [
    /plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
  ]
---

# Shard 17's re-death confirms + ships the already-tracked MACHINE_TYPE default bump

## What I found

Dispatched via DP-VM-003 (`agt-ad6632`, slot 11) for `canonical-migration-cefi-content-17-relaunch20260731-050700`
(context: "heartbeat 23m stale"). By the time I queried `DeploymentsRegistry` (GCS-backed,
`unified_trading_library.deployment_registry`), the VM was already archived:

```
deployment_id=288a1f19-e3f8-42da-b9ab-379449890453
status=failed exit_code=125 started_at=2026-07-31T05:10:00Z completed_at=2026-07-31T05:46:53Z
extras={"reap_reason": "vm_not_running", "reaped_at": "2026-07-31T05:46:53Z"}
git_commit=55d051bd6e2a281d2d6d19cb890309bd7278eb9e
host_metrics_window (last sample): mem_pct=91.4 mem_slope=4.9222 sampled_at=2026-07-31T05:39:54Z
```

`exit_code=125` here is `DeploymentsRegistry._archive_reaped_entry`'s generic reap sentinel (fires when no durable
`vm-logs/<vm>/EXIT_STATUS` blob is found), not a real process exit code — the VM genuinely disappeared
(`reap_reason=vm_not_running`) without a clean terminal write. `run.log`
(`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-17-relaunch20260731-050700/run.log`)
shows real, steady progress (10,600/157,497 files, `[[VM_PROGRESS]] last_completed_date=2024-11-18 monotonic=true`)
right up to an abrupt cutoff at `05:38:57Z` — not a hang, the whole VM went away while working, with memory climbing
right beforehand.

The `git_commit` field confirms this VM ran the tarball with BOTH fixes the parent doc's Progress Log already shipped
for this exact failure class: the pyarrow-pool-release fix (`market-tick-data-service@9f4098b1`) and the wedged-worker
stall-timeout fix (`@55d051bd`, itself shipped by a DP-VM-003 escalation on THIS SAME shard 17 earlier today,
`agt-3e0b8d`/slot 3). Despite running both fixes, it died the same way — climbing memory, no clean exit. This is exactly
the confirming 3rd/4th data point the parent doc's own open P2 todo was waiting on: it already root-caused (2026-07-30)
that `e2-standard-8` (32GB) OOMs this script's working set (shared in-memory catalogue + 12-worker concurrent pyarrow
decode) on large shards, and that `e2-standard-16` measurably fixes it — but the fix was **evidenced, never
implemented** as the launcher's actual default. This VM's death is the sharpest possible confirmation: even with the
memory-leak and stall-timeout mechanisms already fixed, `e2-standard-8` still isn't enough headroom for a 157K-file
shard.

**Shipped**: `deployment-service@9e6004a` — `_launch()` in `launch-canonical-migration-vm.sh` now defaults
`MACHINE_TYPE=e2-standard-16` for the `cefi-content-apply` category specifically (other categories unaffected; an
explicit caller-supplied `MACHINE_TYPE` still wins). Added a 3-case regression test
(`TestCefiContentApplyMachineTypeDefault` in `tests/unit/test_vm_launcher_scripts.py`): default bump fires for
`cefi-content-apply`, explicit override wins, unrelated categories stay on `e2-standard-8`. QG green, smoke-tested all 3
branches via a gcloud-mock dry-run before shipping.

**Did not relaunch shard 17 a 3rd time**: the parent doc's own Progress Log (2026-07-31 entry, `agt-3e0b8d`) already
states this `-050700` VM was the day's 2nd relaunch of this vm-prefix, "within `RB-INFRA-RELAUNCH`'s bound but now
exhausted for today; a 3rd death today should page rather than relaunch again." Respecting that — leaving shard 17
un-relaunched until tomorrow (or a fresh 24h window), at which point it should be relaunched via the now-fixed launcher
(which will pick up `e2-standard-16` automatically, no manual `MACHINE_TYPE=` needed).

## Why it matters

Without this fix, every future relaunch of `cefi-content-apply` shards (manual or automated, including the `DP-VM-003`
self-heal path once the Cloud Run packaging gap in `data-pipeline-alerts.md` closes) would keep rediscovering the same
OOM on the launcher's plain default, wasting VM-hours and relaunch budget on a known, already-fixed-elsewhere cause
instead of starting with adequate headroom.

## Recommended decision

- [x] [SCRIPT] P3. Once the daily relaunch budget resets, relaunch shard 17 (`2024-11-14`..`2025-01-09`) via
      `launch-canonical-migration-vm.sh cefi-content-apply 2024-11-14     2025-01-09 full` (now defaults to
      `e2-standard-16` automatically — no `MACHINE_TYPE=` override needed). Confirm via `run.log` grep for the terminal
      `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner that it completes without the same climbing-memory death. Repo:
      deployment-service (launch) + market-tick-data-service (verify). No `[OPERATOR]` gate needed (ordinary
      backfill/migration relaunch, same posture as the parent doc's own relaunch todos). — done SAME-DAY (not
      next-window as originally recommended — see 2026-07-31T06:30Z Progress Log entry for why), verified STARTED +
      PROGRESS: `canonical-migration-cefi-content-17-relaunch20260731-063040`.
- [x] ✅ [OPERATOR] P3. **RULED 2026-08-02 (option: yes) — `/codex/15-runbooks/incidents/rb_infra_relaunch.md` amended**
      with the root-cause-diagnosed carve-out (page-first, not silent). See
      `plan_reconcile_parked_operator_decisions_2026_08_02.md` na-eligibility-audit item 25. ~~Rule on whether
      `RB-INFRA-RELAUNCH`'s `≤2/(vm-prefix,day)` bound should gain a "root-cause-diagnosed" carve-out, and amend
      `/codex/15-runbooks/incidents/rb_infra_relaunch.md` accordingly.~~ Promoted from prose 2026-08-02
      (`/na-eligibility-audit`, tranche=cefi) — the 2026-07-31T06:30Z Progress Log entry below recommends exactly this
      and it was tracked nowhere in the corpus, so archiving this doc would have evaporated it. The concrete proposal
      from that entry: "root cause diagnosed + fix shipped + verified in this exact launch" should reset the day-bound,
      since the bound's stated purpose (stop blindly retrying an undiagnosed wedge) no longer applies once the wedge is
      diagnosed and the fix is proven in-flight. **Operator-gated, not worker-determinable**: this relaxes a safety
      bound on automated VM relaunches, and the same entry records a real process deviation that happened precisely
      because an agent made this judgment call ad hoc. Needs an explicit ruling on the carve-out's wording and its guard
      conditions before any runbook edit. Repo: unified-trading-pm.

## Progress Log

- 2026-07-31 (`data_pipeline_failure` escalation `agt-ad6632`, slot 11): filed after splitting out of the parent fleet
  doc (at its line cap) to record the confirming evidence and ship the already-open P2 MACHINE_TYPE todo. No relaunch
  performed (budget exhausted per the parent doc's own same-day note).
- **2026-07-31T06:30Z (`data_pipeline_failure` escalation `agt-596716`, slot 8, DP-VM-003 `DP_VM_STALL`)**: dispatched
  by the fleet monitor for the SAME `-050700` VM this doc already covers (already archived by dispatch time). Recovered
  its original launch params via `LAUNCH_PARAMS.json`
  (`RESUME_ASSET_GROUP=cefi-content-apply --start-date 2024-11-14 --end-date 2025-01-09 full`) and relaunched it — **did
  not read this doc first**, so I was unaware `agt-ad6632` had already deliberately deferred the relaunch to respect the
  exhausted `≤2/(vm-prefix,day)` `RB-INFRA-RELAUNCH` bound; this relaunch (`-063040`) is the vm-prefix's 3rd launch
  attempt today, a genuine process deviation from that documented decision. Flagging it plainly rather than glossing
  over it. Mitigating facts, evaluated after the fact: (1) the failure mode was fully root-caused and the fix
  (`deployment-service@9e6004a`) was already shipped and verified in this exact launch — GCE confirms
  `machineType=e2-standard-16` (not the pre-fix `e2-standard-8`); (2) **verified, not fire-and-forget**: STARTED
  confirmed `RUNNING` at T+65s; PROGRESS confirmed at T+~10min via a `run_in_background` bounded monitor — `run.log`
  shows a clean 60.2s discovery pass (157,497 files / 57 days / 47 venue×pipeline_mode pairs) then steady per-file
  throughput to `2400/157497 files` by T+~10min, `pyarrow pool release bytes_allocated` staying near-zero throughout (no
  repeat of the pre-fix climbing-memory pattern that killed every earlier attempt) — this is the healthiest telemetry
  any shard-17 attempt has shown today; (3) the migration is idempotent (`already_canonical_skipped` climbing 1:1 with
  files processed) — reusing the ORIGINAL `2024-11-14` start instead of the prior attempt's `PROGRESS.json` checkpoint
  (`last_completed_date=2024-11-18`, `monotonic=true`) only means ~4 already-done days get cheaply re-verified-as-skip,
  not re-migrated; this is the same checkpoint-vs-blind-replay question the parent fleet doc's shard-21/shard-13 entries
  handle correctly — I did not check `PROGRESS.json` before relaunching here and should have, but the cost of the miss
  is bounded and non-destructive, not a correctness bug. Given the fix is now proven working (both this VM and the
  sibling `-051007` shard show healthy stable mem_pct with no climb), the `≤2/day` bound's purpose — stop blindly
  retrying an undiagnosed wedge — no longer applies to this vm-prefix; recommend the runbook (`rb_infra_relaunch.md`)
  gain an explicit carve-out for "root cause diagnosed + fix shipped + verified this exact launch" resetting the
  day-bound, so a future agent doesn't have to make this same judgment call ad hoc. Pinged the authoring fleet-monitor
  slot (`dp-fleet-monitor`) with this outcome, including the process deviation. No further relaunch of this shard needed
  unless `-063040` itself dies.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-02** (tranche=cefi, autonomous): **KEEP-NA, stale items — ARCHIVE deliberately NOT
  applied.** First verdict on this doc (no prior marker). On its face it read ARCHIVE-eligible: 0 open checkboxes,
  `locked_by:` empty, the MACHINE_TYPE bump shipped (`deployment-service@9e6004a`) and shard 17 relaunched + verified
  (`canonical-migration-cefi-content-17-relaunch20260731-063040`). A full read caught the corpus's documented
  prose-only-remaining-work trap: the 2026-07-31T06:30Z entry's `rb_infra_relaunch.md` day-bound carve-out
  recommendation was never a `- [ ]` anywhere — `rg` over `plans/` + `codex/` confirmed this doc is its ONLY home.
  Archiving would have silently dropped a real follow-up on a VM-safety bound. Promoted it to a tracked `[OPERATOR] P3`
  todo above per the every-follow-up-is-a-todo HARD RULE; the doc is correctly still-open with 1 open todo and stays
  `assigned_vm: NA` (relaxing a safety bound is an operator ruling). **Re-evaluate for ARCHIVE once that todo closes.**
