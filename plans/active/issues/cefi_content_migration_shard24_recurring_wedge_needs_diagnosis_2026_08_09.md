---
doc_type: issue
title: >-
  Shard 24's 3rd checkpoint-resumed attempt (-133746, launched 2026-07-31) ALSO wedged at ~31% and self-deleted with no
  clean exit marker — 3 consecutive failures on this exact shard (wedge / preemption / wedge) warrant diagnosis before a
  blind 4th relaunch
summary: >-
  Dispatched via `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` todo 3 ("check shard 24's current state; relaunch if
  still incomplete and not already relaunched"). Found the relaunch had ALREADY happened —
  `canonical-migration-cefi-content-24-relaunch20260731-133746` (inserted 2026-07-31T13:37Z,
  `RESUME_START_DATE=2026-01-06 RESUME_END_DATE=2026-01-15`) — so the todo's own precondition ("hasn't already been
  relaunched by another agent") is false; per the todo's own text, no further launch action was due from that todo. But
  this 3rd attempt did NOT succeed either: `run.log` shows real progress (33,800/108,441 files, 9.0 files/sec)
  interleaved with repeated "No progress in the last poll window — N files still outstanding (possible wedged worker)"
  warnings — the EXACT same symptom shape as the shard's own first attempt (`-032606`, wedged at 43.9% then went silent
  48 min before deletion, per `cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md`). The log
  simply stops at 14:45:17Z (no `PREEMPTED` marker, no stall-kill message, no `EXIT_STATUS`) and the VM instance no
  longer exists in any Tokyo zone (`NOT_FOUND`, self-deleted per `--instance-termination-action=DELETE`).
  `PROGRESS.json` is frozen at `last_completed_date=2026-01-07` (barely past its own `RESUME_START_DATE=2026-01-06`).
  This is shard 24's THIRD consecutive failed attempt (wedge → clean SPOT preemption → wedge again), all sharing the
  shard-24 VM prefix — a recurring, shard-specific pattern rather than three independent random failures, worth
  diagnosing before another blind checkpoint-resumed relaunch.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, migration, vm, wedge, stall, canonical-migration, data-pipeline]
related:
  [
    /plans/archive/2026_08/issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md,
    /plans/active/cefi_satellite_ao_dispatch_batch12_2026_08_09.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-09
author: slot-8 (infra)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.48
assigned_role: infra
drift_direction: none
sequential: false
locked_by:
context_scope:
  [
    /plans/archive/2026_08/issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
  ]
resolved_by:
source: >-
  Discovered 2026-08-09 (slot-8, infra) while working `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` todo 3 — the
  todo's own precondition check surfaced that a relaunch already happened AND also failed, a state the todo's done-when
  did not anticipate.
depends_on: []
---

# Shard 24's 3rd attempt also wedged — recurring shard-specific pattern, diagnose before a 4th blind relaunch

## What I found

Checked `gs://deployment-scripts-central-element-323112/vm-logs/` for any `canonical-migration-cefi-content-24-*` launch
after `-065001` (2026-07-31T06:50Z, the early-preemption death the source issue doc tracks). Found one:
`-relaunch20260731-133746` (inserted 2026-07-31T13:37Z).

**Direct evidence:**

- `LAUNCH_PARAMS.json`:
  `RESUME_ASSET_GROUP=cefi-content-apply RESUME_START_DATE=2026-01-06 RESUME_END_DATE=2026-01-15 RESUME_SHARD_OF=1 RESUME_SHARD_INDEX=0`
  — a correctly checkpoint-resumed, single-VM (non-sharded) relaunch, matching the source doc's prescribed 3rd-attempt
  window almost exactly (day-1 earlier start).
- `PROGRESS.json`: `{"last_completed_date":"2026-01-07","monotonic":true,"updated":"2026-07-31T14:24:14Z"}` — only 1 day
  past its own start.
- `run.log`: shows genuine progress to `33,800/108,441 files (9.0 files/sec, 3747.1s elapsed)` at 14:43:17Z, but
  interleaved with repeated
  `WARNING No progress in the last poll window — N files still outstanding (possible wedged worker)` — the tool's own
  self-diagnostic warning (not a stall-kill event). The log's last line is at **14:45:17Z**, then nothing — no
  `PREEMPTED` marker written, no stall-kill message, no `EXIT_STATUS` file of any kind in the vm-logs directory
  (confirmed via `gcloud storage ls -r .../133746/**` — only the 4 launcher-time files exist).
- `gcloud compute instances describe canonical-migration-cefi-content-24-relaunch20260731-133746` across all 3 Tokyo
  zones: `NOT_FOUND` — self-deleted, consistent with `--instance-termination-action=DELETE`.
- `gcloud compute operations list` for this VM name returns **nothing** — likely past the Compute Engine operations
  retention window (9 days old at time of check), so the GCE-Operations-API root-cause technique the source doc used for
  `-065001` (insert/preempt timestamps) is no longer available for this VM.

**Why "wedge" is the leading hypothesis, not preemption**: unlike `-065001` (died 70s after insert, before any `run.log`
line could be written), `-133746` ran ~55 minutes and wrote 100+ progress lines — if it had been preempted at that
point, the in-guest shutdown-script would have had ample time to write the `PREEMPTED` GCS marker (per the source doc's
own established evidence pattern). Its absence points to something that prevented a graceful shutdown entirely — either
a genuine worker freeze (matching `-032606`'s IDENTICAL symptom: real progress, then repeated "possible wedged worker"
warnings, then silence) that the `STALL_PROGRESS_REGEX=progress:|files/sec` watchdog (`deployment-service@b2d135a1e8`,
landed 2026-07-27 — already live for this run) caught and force-killed the VM without the kill event reaching this
particular log stream, or a different failure mode not yet identified.

**Pattern across shard 24's 3 attempts today (2026-07-31), all same VM-name-prefix family:**

| Attempt   | Started | Outcome                         | Symptom                                                                    |
| --------- | ------- | ------------------------------- | -------------------------------------------------------------------------- |
| `-032606` | 03:27Z  | Wedged at 43.9%, deleted 06:32Z | Progress then silence, "possible wedged worker" warnings                   |
| `-065001` | 06:50Z  | Preempted 70s later             | Clean SPOT reclaim, zero progress made                                     |
| `-133746` | 13:37Z  | Wedged at ~31%, self-deleted    | Progress then silence, SAME "possible wedged worker" warnings as `-032606` |

Two of three failures share an identical symptom signature specific to this shard. This is not conclusive proof of a
shard-24-specific root cause (could be coincidental timing/host issues), but it's a strong enough pattern that another
blind checkpoint-resumed relaunch without understanding WHY this shard specifically keeps wedging risks repeating the
same failure a 4th time.

## Why it matters

`cefi_satellite_ao_dispatch_batch12_2026_08_09.md` todo 3's own precondition ("if shard 24 is still incomplete and
**hasn't already been relaunched by another agent**") is now false — the relaunch action it asked for was already taken
(by whoever/whatever launched `-133746`). Blindly launching a 4th attempt today, using the todo's literal window
(`2026-01-07 2026-01-15`), would also silently REPLAY the already-completed `2026-01-07` checkpoint day — a violation of
the workspace's "preemption recovery resumes from measured PROGRESS, never replays START_DATE" hard rule (CLAUDE.md §
"Launching VMs / infra"). The correct resume point (if a 4th attempt is warranted) is `RESUME_START_DATE=2026-01-08`,
not `2026-01-07`.

## Recommended decision

## Todos

- [ ] [SCRIPT] P2. Launch shard 24's 4th checkpoint-resumed attempt from its ACTUAL last checkpoint:
      `RESUME_START_DATE=2026-01-08 RESUME_END_DATE=2026-01-15` (day AFTER `-133746`'s `last_completed_date=2026-01-07`
      — do NOT replay 2026-01-07).
      `RESUME_ASSET_GROUP=cefi-content-apply RESUME_SHARD_OF=1 RESUME_SHARD_INDEX=0 bash     scripts/vm/launch-canonical-migration-vm.sh cefi-content-apply 2026-01-08 2026-01-15 full`.
      Verify STARTED <60s + ≥1 progress line/hr (per infra craft north-star — no fire-and-forget) and check back at
      T+90min for either completion, active progress past `2026-01-08`, or a repeat wedge (in which case STOP
      relaunching and treat todo 2 below as blocking). Repo: deployment-service.
- [ ] [SCRIPT] P3. Only if todo 1 also wedges (3rd wedge on this exact shard): diagnose the shared root cause across
      `-032606` and `-133746`'s identical "possible wedged worker" signature — check whether shard 24's specific date
      range/file population has an outlier (e.g. one pathologically large/malformed parquet, a specific venue's file
      count spike) that the migration script's per-file loop chokes on, by comparing shard 24's file-count/size
      distribution against a shard that completed cleanly. Repo: market-tick-data-service.

## Progress Log

- **2026-08-09 (slot-8, infra)**: Filed while working `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` todo 3 — the
  todo's own precondition check found a relaunch already happened (`-133746`) but it also failed, a state the original
  todo's done-when didn't anticipate. Closing the batch12 todo per its own stated logic (relaunch action already taken
  by another agent, so no duplicate launch from that todo); tracking the actual remaining work (a correctly-checkpointed
  4th attempt + wedge diagnosis if it recurs) here instead.
