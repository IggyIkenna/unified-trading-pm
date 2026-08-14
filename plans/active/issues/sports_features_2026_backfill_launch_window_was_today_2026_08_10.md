---
doc_type: issue
title: >-
  DP-VM-001: `features-sports-sports-2026-20260810-051126` exited rc=1 because the per-year 2026 sports features
  backfill fleet's launch window ended today (2026-08-10), whose upstream reference (`entity=fixtures`) was not yet
  written at run time — features-service honest-halted (not a code bug); the 2026 range through 08-09 is already
  captured by four corrected-window runs, so no relaunch is warranted
summary: >-
  The 2026-08-10T05:11Z per-year sports features backfill fleet (`features-sports-sports-{2020..2026}-20260810-051126`)
  launched each year VM with `end_date = {year}-12-31`, EXCEPT the current-year 2026 VM which used `end_date =
  2026-08-10` (the launch day). At its 08:02Z tail the 2026 VM reached date 2026-08-10 and found the upstream
  instruments-store reference `entity=fixtures` for that day was NOT yet written (`17/17 reference entities missing`
  logged; only `fixtures_outcomes`/`fixtures_schedule`/`injuries` exist for 2026-08-10 even at 21:37Z), so
  features-service raised `ERROR [HIGH] dependency error ... Required upstream blob missing within coverage:
  entity=fixtures date=2026-08-10` and exited rc=1 — an HONEST halt (never a fabricated/empty placeholder). Sibling year
  VMs 2020/2021/2023/2024/2025 completed exit 0; 2022 failed exit 125 (`vm_not_running`, reaped). The actual 2026
  features range through 2026-08-09 is ALREADY captured: four corrected-window runs today (`end=2026-08-09`, depl
  85712ea3/7a005c73/e1802a4d/ccde49f5) all completed exit 0, and the availability manifest shows 2026-08-09 captured (21
  rows/613 rows). Today (08-10) is a forward/T+1 item (features-sports T+1 recon at 02:30 per t1_batch_scheduler.tf),
  not a batch-backfill gap. A blind relaunch of the exact window (`end=2026-08-10`) would re-fail identically and
  exceeds RB-INFRA-RELAUNCH's `≤2/(vm-prefix,day)` bound (12+ `features-sports-sports` launches today) — so no relaunch.
status: open
nature: issue
asset_group: [sports]
stage: [features]
repos: [deployment-service, features-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
parent_epic: sports_master
priority: P2
tags: [sports, features, dp-vm, launch-window, dag-ordering, honest-halt, rb-infra-relaunch, data-pipeline]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18_part3_2026_07_26.md,
  ]
created: "2026-08-10"
author: slot-6
last_updated: "2026-08-10"
assigned_vm: planning
execution_scope: orchestrator-agent
source: >-
  DP_VM_EXIT_NONZERO escalation agt-af22dd (fleet exit-code monitor → orchestrator), VM
  features-sports-sports-2026-20260810-051126 (depl a35d016a-3b9d-480d-9f47-d055a751577d), 2026-08-10.
assigned_role: data
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    deployment-service/scripts/vm/launch-features-vm.sh,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
---

# `features-sports-sports-2026-20260810-051126` rc=1 — launch-window (end=today) honest-halt, no relaunch

## The finding (DP-VM-001, escalation agt-af22dd)

The exit-code-aware fleet monitor flagged `features-sports-sports-2026-20260810-051126` — a per-year sports
**features-backfill** VM (deployment `a35d016a-3b9d-480d-9f47-d055a751577d`, `asset_group=SPORTS`,
`start_date=2026-01-01`, `end_date=2026-08-10`, `mode=full`) — with terminal `exit_code=1` and escalated it for
relaunch.

## Root cause — launch-window / DAG ordering, NOT a code bug

The 2026-08-10T05:11Z fleet launched one VM per year (`features-sports-sports-{2020..2026}-20260810-051126`). Each year
VM ran `features_service` over `{year}-01-01 .. {year}-12-31`, but the **current-year 2026 VM used `end_date=2026-08-10`
(the launch day)**. At 08:02Z the run reached 2026-08-10 and the upstream `instruments-store-sports-prd` reference for
that day had **not yet been written** — the run logged `Reference data for 2026-08-10: 17/17 entities missing` and
`ERROR [HIGH] dependency error in features-service.compute_features: Required upstream blob missing within coverage: entity=fixtures date=2026-08-10`
→ `Processing failed` → `[vm-exec] command exited rc=1`.

This is the correct **honest-halt** behavior — the features-service raised on the missing required upstream dependency
rather than writing a fabricated/empty placeholder, exactly per the data-pipeline heartbeat rules. There is no code
defect in features-service: its required upstream input simply did not exist yet for a _current_ day included in the
launch window.

## Why no relaunch is warranted

1. **The 2026 range through 2026-08-09 is already captured.** Four corrected-window runs today with `end=2026-08-09`
   (`features-sports-sports-20260810-121107`, `125312`, `140033`, `171344` → depl 85712ea3/7a005c73/e1802a4d/ccde49f5)
   all completed **exit 0**; the availability manifest shows 2026-08-09 captured (21 rows / 613 rows) and 2026-08-07/08
   captured too. The launch window that failed (`end=08-10`) is a strict superset of the already-captured work.
2. **2026-08-10 is a forward/T+1 day, not a batch-backfill gap.** Today's features are produced by the daily forward /
   T+1 features path (`features-sports-service-t1-recon`, 02:30 per `t1_batch_scheduler.tf`) once the day's reference
   data lands — not by re-running a batch backfill whose window ends today. Even at 21:37Z the 2026-08-10 reference
   bucket still lacks `entity=fixtures`, so a relaunch of the exact window would **re-fail identically**.
3. **RB-INFRA-RELAUNCH bound.** The runbook caps relaunches at `≤2/(vm-prefix,day)`; the registry archive shows 12+
   `features-sports-sports` launches today, so the bound is far exceeded and the default disposition is "do NOT relaunch
   again; page the operator". The root-cause-diagnosed carve-out also does not apply: the fix is a corrected launch
   window (end=yesterday for the current year), and that corrected window has ALREADY been run successfully — there is
   no new launch carrying a just-shipped fix to make.

## What was already done

- 2026-08-10T~21:38Z: launcher resolved (`launch-features-vm.sh` via `features-` prefix in `launcher_registry.py`);
  deployment registry row read (`a35d016a`, exit_code=1); run.log + watchdog trace pulled from GCS; manifest inspected.
- 2026-08-10T~21:41Z: operator paged via `/blocked` (BLK-49c0161e) with recommendation **A: do not relaunch** — the
  per-year launch-window root cause + the already-captured corrected-window evidence.

## Recommended follow-up (for the sports features owner / next fleet launch)

- Per-year features fleets must use `end_date = yesterday` for the CURRENT year (or clamp the window to
  `min(today-1, {year}-12-31)`), so a current-day's not-yet-written upstream reference can never be a hard dependency at
  backfill time. The four corrected-window runs today already demonstrate the intended window.
- Confirm the daily features-sports forward/T+1 path (02:30 recon) picks up 2026-08-10 once instruments writes that
  day's reference.
- Note (separate, same fleet): `features-sports-sports-2022-20260810-051126` also failed with exit 125
  (`vm_not_running`, reaped) — not the launch-window class; may warrant its own check if 2022 sports features are
  incomplete.

## Todos

- [ ] [CONFIG] P2. **ADDED 2026-08-12 (/plan-reconcile, Section 2 zero-checkbox conversion)** — Clamp the per-year
      sports features backfill launcher's current-year window to `end_date = min(today-1, {year}-12-31)` so a
      current-day's not-yet-written upstream reference can never be a hard dependency at backfill time (the four
      corrected-window runs on 2026-08-10 already demonstrate the intended window). Repo: deployment-service (launcher).

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- **context-scout 2026-08-14**: populated context_scope (3 entries).
