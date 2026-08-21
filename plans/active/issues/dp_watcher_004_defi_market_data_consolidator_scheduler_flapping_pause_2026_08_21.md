---
doc_type: issue
title: "DP-WATCHER-004: uts-prod-manifest-consolidator-market-data-defi-cron repeatedly paused/resumed by unified-trading-sa with no live maintenance window — resumed as immediate fix, root actuator not yet identified"
created: 2026-08-21
author: data_pipeline_failure (escalation agt-2b817b, slot 31)
parent_epic: observability_master
assigned_vm: planning
source:
  - DP-WATCHER-004
  - escalation agt-2b817b
locked_by:
summary: >-
  Cloud Scheduler job uts-prod-manifest-consolidator-market-data-defi-cron (asia-northeast1) fired
  DP-WATCHER-004 (CRITICAL, page) PAUSED-with-no-maintenance-window at 2026-08-21T15:39:11Z. Live
  investigation found this is NOT a one-time human pause: Cloud Audit Logs show
  unified-trading-sa@central-element-323112.iam.gserviceaccount.com toggling the SAME job
  PauseJob(14:25:50) -> ResumeJob(15:35:09/10) -> PauseJob(15:39:10/11) within the same ~75-minute
  window -- a flap pattern, not a single deliberate pause. scheduler_maintenance.maintenance_status()
  (the exact read-path DP-WATCHER-004 itself uses) confirmed NO live window on the owning bucket
  (market-data-tick-defi-prd-central-element-323112) at diagnosis time, and no VM matching the known
  canonical-migration-defi-rebuild pattern (or any other defi manifest-rewrite script) was running
  (full gcloud compute instances list checked). RESUMED the job as the immediate fix (data-pipeline
  correctness heartbeat) since no live window and no VM justify holding it paused. Root actuator of
  the repeated pause/resume toggling NOT yet identified -- deployment-service's
  RevocationActuator (FLEET_HALT) is correctly wired (consolidator_bucket_resolver passed at both
  call sites, escalation.py:663 + meta_watchers.py:211) and is the most likely mechanism (its
  pause/release cycle matches this shape exactly), but if it were firing for a defi-scoped alert it
  SHOULD have registered a maintenance window via _register_maintenance_windows() before pausing --
  and none was found live. Whether that means (a) the window write failed silently for this
  specific pause and the true driver IS FLEET_HALT re-triggering on a still-flapping defi CRITICAL
  alert, or (b) something else entirely (not RevocationActuator) is toggling this job, is the open
  question this issue exists to resolve.
status: open
nature: process
asset_group: [defi]
stage: [meta]
repos: [deployment-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-pipeline, dp-alerts, dp-watcher-004, defi, manifest-consolidator, scheduler, fleet-halt, revocation]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md,
    /plans/active/issues/mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md,
  ]
priority: P2
resolved_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    deployment-service/deployment_service/data_pipeline_monitors/revocation_actuator.py,
    deployment-service/deployment_service/data_pipeline_monitors/consolidator_scheduler_watcher.py,
    deployment-service/deployment_service/data_pipeline_monitors/scheduler_maintenance.py,
  ]
---

# DP-WATCHER-004: defi market-data consolidator scheduler flapping pause, root actuator unconfirmed

## What I found

Escalation `agt-2b817b` (DP-WATCHER-004, wall_type=data_pipeline_failure) fired for
`uts-prod-manifest-consolidator-market-data-defi-cron` — no issue doc had been pre-filed (the alert
carried the details directly), so this doc is the first filing.

**Live evidence gathered:**

1. `gcloud scheduler jobs describe` confirmed `state: PAUSED`, `userUpdateTime:
   2026-08-21T15:39:11Z` at diagnosis time.
2. `scheduler_maintenance.maintenance_status("market-data-tick-defi-prd-central-element-323112")`
   (the SAME read path `check_consolidator_scheduler_paused`'s `maintenance_window_reader` uses)
   returned **no live window** — confirming this pause was correctly classified as unsanctioned by
   the watcher's own logic, not a reader bug.
3. `gcloud compute instances list` (full fleet, no filter) found no VM matching
   `canonical-migration-defi-rebuild-*` or any other name suggesting a manual defi manifest rewrite
   in progress — ruling out the exact precedent pattern from
   `/plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` (that
   incident's VM is long gone; current fleet has `instr-backfill-defi*`, `mdps-defi-2025-*`,
   `mdps-features-live-defi-*` running, none of which pause the consolidator per their own
   documented contract).
4. **Cloud Audit Logs** (`cloudaudit.googleapis.com/activity`,
   `protoPayload.resourceName:"uts-prod-manifest-consolidator-market-data-defi-cron"`, last 24h)
   show a flap, not a single pause:
   ```
   2026-08-21T14:25:50Z  unified-trading-sa@...  CloudScheduler.PauseJob
   2026-08-21T15:35:09Z  unified-trading-sa@...  CloudScheduler.ResumeJob
   2026-08-21T15:35:10Z  unified-trading-sa@...  CloudScheduler.ResumeJob
   2026-08-21T15:39:10Z  unified-trading-sa@...  CloudScheduler.PauseJob
   2026-08-21T15:39:11Z  unified-trading-sa@...  CloudScheduler.PauseJob
   ```
   The actor is the SERVICE ACCOUNT the runtime monitors/actuators use (`unified_trading_sa`), not
   a human operator identity — this points at an automated actuator, not a manual `gcloud` command.
5. The double Pause/double Resume (each pair ~1s apart) is itself notable — either two independent
   triggers fired within the same second, or one caller calls pause/resume twice per cycle.
6. `deployment-service`'s `RevocationActuator._pause_schedulers` (FLEET_HALT delivery for
   `DependentAction.FLEET_HALT`) is the only known mechanism in this codebase that pauses a
   consolidator scheduler programmatically outside a human `gcloud`/CLI call — see
   `revocation_actuator.py`. It is wired correctly at BOTH production call sites
   (`escalation.py:663`, `meta_watchers.py:211` both pass
   `consolidator_bucket_resolver=consolidator_job_to_bucket`), and per its own docstring it
   registers a maintenance window BEFORE pausing (`_register_maintenance_windows`, closing the
   2026-08-15 double-page gap) — so if FLEET_HALT were the driver, a live window should exist. None
   was found (point 2 above). This is either evidence FLEET_HALT is NOT the driver, or evidence the
   window write is failing silently for this specific bucket/target combination (the method
   swallows `MaintenanceWindowActiveError` and any other exception with only a `logger.warning`,
   so a failure here would not be visible without checking Cloud Logging for that warning
   specifically — NOT yet done in this session).
7. `vm-census/admission-hold/` (the FLEET_HALT hold-marker prefix) has 32 defi-related objects, but
   none inspected so far carry a timestamp matching the 15:39Z pause — the freshest-vs-stale split
   was not fully resolved this session (time-boxed by the one-shot escalation's liveness budget).

## Immediate action taken

Resumed the job (`gcloud scheduler jobs resume uts-prod-manifest-consolidator-market-data-defi-cron
--location=asia-northeast1`) at 2026-08-21T15:52:59Z — justified because (a) no live maintenance
window covers it, (b) no VM/backfill needs it paused, (c) per the "data pipeline correctness is the
heartbeat" HARD RULE, an unjustified pause is never left in place pending investigation. Armed a
5-minute background watch (`gcloud scheduler jobs describe` poll every 20s) to catch an immediate
re-pause, which would be strong evidence the driving condition is still live. See Progress Log for
the watch's outcome.

## Why root-cause is NOT closed by the resume alone

If an automated actuator (most likely FLEET_HALT, per point 6) is genuinely reacting to a still-
firing defi CRITICAL alert, resuming the scheduler only wins until the next actuation cycle — the
job will flap paused again. The real fix is identifying WHICH `alert_identity`/`target` is driving
this (if any) and root-causing THAT alert, not repeatedly resuming the scheduler. If the watch
below shows no re-pause, the flap may have been transient (the underlying alert self-cleared) —
still worth confirming what it was, since an unregistered FLEET_HALT-window bug (point 6) is itself
a real gap worth fixing even if this specific occurrence has now settled.

## 2026-08-21 UPDATE (escalation agt-0b7473, slot 4) — root actuator IDENTIFIED, not FLEET_HALT

Re-fired for the same job (`state: PAUSED`, `userUpdateTime: 2026-08-21T16:27:11.636614Z`) — well after
agt-2b817b's clean 5-minute watch ended, confirming this is a genuine recurrence, not a stale re-fire.
Two findings resolve this doc's open "root actuator" question:

**1. FLEET_HALT/RevocationActuator is structurally INCAPABLE of pausing this job — ruled out, not just
unproven.** `RevocationActuator._pause_schedulers` resolves its job list via
`_scheduler_jobs_for(target)` (`revocation_actuator.py:124`), which selects names FROM
`unified_api_contracts...scheduler_registry.SCHEDULER_REGISTRY` — a hand-written, non-generated list
(confirmed: 15 `SchedulerSpec(` literals, no loop/comprehension). That registry contains **exactly one**
consolidator-named entry, `"manifest-consolidator-60s"` (`asset_group="infra"`, `target_ref="deployment-api"`,
a 60s Cloud Run cron unrelated to the per-AG manifest consolidators). **None of the 10 real
`uts-prod-manifest-consolidator-{market-data|instruments}-{ag}-cron` jobs are registered at all** — so
`_scheduler_jobs_for()` can never return `uts-prod-manifest-consolidator-market-data-defi-cron`, for any
`target` string. `_register_maintenance_windows`'s bucket resolver (`consolidator_job_to_bucket()`,
correctly wired, keys sourced from `meta_targets.consolidator_scheduler_job(ag)`) is a red herring here —
the job never reaches that function because `_pause_schedulers` never selects it in the first place. This
answers todo 2 below in favor of "genuinely wasn't FLEET_HALT-driven," not a silent window-write failure.
Also grepped fleet-wide (deployment-service, market-tick-data-service, unified-trading-library) for any
OTHER `pause_job`/`CloudSchedulerClient()`/`make_scheduler_pauser()`/`pause_for_maintenance()` caller — zero
hits outside `revocation_actuator.py` and `scheduler_maintenance.py`'s own CLI entrypoint (which nothing
calls programmatically). **No in-repo code path can pause this job at all.**

**2. The actual actor: a MacOS-hosted Claude Code CLI session, not a human `gcloud` typo, not an
in-repo actuator.** Corrected the audit-log query (the original had `--order=asc` + `--freshness`
interacting badly, silently returning entries back to 2026-05 instead of today — re-ran with default
descending order + explicit user-agent field). Every one of the 7 pause/resume toggles on this job across
14:25:49Z-16:27:11Z (3h window) carries `protoPayload.requestMetadata.callerSuppliedUserAgent` identifying
`google-cloud-sdk ... agent-name/claude-code_2-1-237_agent ... command/gcloud.scheduler.jobs.{pause,resume}
... client-os/MACOSX ... interactive/False ... from-script/True`, from a consistent IP (`148.252.159.201`,
one earlier event from `148.252.148.83`) — i.e. a **non-interactive, scripted Claude Code CLI invocation
running on a Mac**, entirely separate from this fleet's central orchestrator VM (whose escalation workers
run Linux, e.g. agt-2b817b's own 15:52:59Z resume shows `client-os/LINUX`, IP `13.113.200.22` — the
orchestrator's own EIP per workspace CLAUDE.md). Full timeline: `14:25 Pause(mac) → 15:35 Resume(mac) →
15:39 Pause(mac) → 15:52:59 Resume(orchestrator, agt-2b817b) → 16:20:37 Resume(mac, redundant — job was
already ENABLED) → 16:25:41 Pause(mac) → 16:25:53 Resume(mac, 12s later) → 16:27:11 Pause(mac, 78s later)`.
The redundant 16:20 resume-of-an-already-enabled-job and the accelerating cadence toward the end (5min →
12sec → 78sec) reads as active, real-time, hands-on iteration on this exact resource — not a one-off
mistake, and not a code bug.

**Why I did not resume a 3rd time.** Per this doc's own "Known gap" note in
`/codex/05-infrastructure/data-pipeline-alerts.md` (DP-WATCHER-004 cannot distinguish an accidental pause
from a deliberate, plan/session-tracked one) and the directly-analogous near-miss precedent in
`/plans/active/issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md` (a triage agent
resuming mid-flight of someone else's in-progress work), repeatedly resuming a job that a live, currently-
active session keeps re-pausing every few minutes would very likely just race that work, not fix anything
— and per the observed cadence would probably be flipped back within minutes anyway. This is a genuine
judgment call, not something to guess at, so I escalated via `/blocked` (`BLK-fbcafec2`,
`can_continue: false`) asking whether to leave it paused (assume deliberate active work) or resume anyway.
No answer arrived within the 2-minute bound — per role protocol, stopping here rather than holding the
slot; the question persists on the dashboard for the operator, and a later answer re-dispatches a fresh
worker. **Current live state: still `PAUSED` as of this escalation's close** — deliberately left untouched
pending that answer, not by omission.

## Recommended decision

- [x] ✅ [DATA] P1. **ANSWERED 2026-08-21 (agt-0b7473) — NOT FLEET_HALT.** See the UPDATE section above:
      `SCHEDULER_REGISTRY` has zero entries for any of the 10 real per-AG consolidator jobs, so
      `_scheduler_jobs_for()` structurally cannot select this job — FLEET_HALT is ruled out, not just
      unconfirmed. The actual re-pausing actor is a MacOS-hosted Claude Code CLI session (non-interactive,
      from-script), not any registered DP-* alert_identity — there is no "that alert" to root-cause via
      the DP-* registry path this todo originally proposed.
- [x] ✅ [CODE] P2. **ANSWERED 2026-08-21 (agt-0b7473) — not a silent window-write failure; the pause
      never reached `_register_maintenance_windows` at all**, because `_pause_schedulers`'s upstream job
      selection (`_scheduler_jobs_for`) never included this job to begin with (see UPDATE section, finding
      1). The real caller is the MacOS Claude Code CLI session identified in finding 2 — not an in-repo
      caller, so there is no further code path to grep.
- [ ] [DATA] P3. Cross-check against `/plans/active/issues/mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md`
      (filed earlier the same day, ~10:50 UTC) — that doc found the consolidator running healthily
      every ~1-2 min with a stale OUTPUT blob; this doc found the scheduler ITSELF paused a few
      hours later (14:25-15:39Z). If the flap traces back further than 14:25Z, the two findings may
      share a root cause (something intermittently disrupting the defi consolidator's steady
      state, of which "output blob staleness" and "scheduler flapping paused" are two symptoms) —
      not established this session, flagged as a hypothesis only.
- [ ] [OPERATOR] P1. Answer blocked question `BLK-fbcafec2` (posted 2026-08-21 by agt-0b7473, unanswered
      after the 2-minute bound): is the repeated MacOS-session pause/resume of
      `uts-prod-manifest-consolidator-market-data-defi-cron` deliberate active work (leave alone, no
      further agent action needed) or a stuck/erroneous local loop (needs stopping, then the job resumed)?
      ~~Job is currently `PAUSED` pending this answer.~~ **CORRECTED 2026-08-21 (agt-0fc6b2, slot 9): job is
      `ENABLED` again (resumed 17:45:45Z by a THIRD, unidentified actor — not the MacOS session, not either
      prior escalation's own resume) and stable 41+ min as of this check. `BLK-fbcafec2` itself is still
      formally unanswered. The immediate correctness risk this todo tracked is resolved for now; the
      identity/authorization question remains open for main/operator. See Progress Log for full evidence.**
      **RECORRECTED 2026-08-21 (agt-17e0d2, slot 33): job is `PAUSED` again (`userUpdateTime:
      2026-08-21T19:11:55.938445Z`) — the MacOS session's toggling never stopped, it resumed after the
      ~41min quiet window agt-0fc6b2 observed. `BLK-fbcafec2` remains formally unanswered. Still
      genuinely open — see Progress Log.**
      **UPDATED 2026-08-21 (agt-bb2394, slot 31): job remains `PAUSED`, unchanged, through 20:07:38Z —
      a ~56min quiet window with zero further toggles, the longest quiet period observed across this
      whole incident. A legitimate, `deployment-service`-managed VM
      (`defi-manifest-projection-20260821-195038`, labels `asset-group=defi env=prod
      managed-by=deployment-service purpose=defi-manifest-projection`) is now `RUNNING` (created
      ~20:01Z, i.e. after the last toggle). This is new evidence FOR option A (leave paused) — a
      genuine in-flight defi manifest-projection job is exactly the kind of operation that would want
      the consolidator held off, and its timing (started shortly after the toggling settled) is
      consistent with the earlier MacOS-session iteration having been the operator setting this run
      up rather than erratic tinkering. `BLK-fbcafec2` is STILL formally unanswered — did not resume,
      did not duplicate the blocked-question (same reasoning as the 3 prior escalations: an open,
      unanswered question already covers this exact decision). See Progress Log.**
- [ ] [CODE] P3. Separate, confirmed, genuine gap (not the cause of this incident): if FLEET_HALT is
      *supposed* to be able to halt the manifest-consolidator schedulers during a defi-scoped revocation
      (implied by `_register_maintenance_windows`'s own docstring, which assumes the write/read bucket
      mapping is the only thing that matters), `SCHEDULER_REGISTRY` needs `SchedulerSpec` entries for the
      10 real `uts-prod-manifest-consolidator-{market-data|instruments}-{ag}-cron` jobs — currently zero
      exist, so `_scheduler_jobs_for()` can never select them regardless of `target`. If FLEET_HALT was
      never intended to reach the consolidator crons, close this as a documentation-only clarification
      instead. Repo: unified-api-contracts (registry) + deployment-service (docstring, if scope is
      clarified as intentional).

## Codex SSOTs

- `/codex/05-infrastructure/data-pipeline-alerts.md` § DP-WATCHER-004, § "Alert-driven dependency
  revocation" (FLEET_HALT mechanism + the 2026-08-17-closed double-page gap this doc's finding 6
  may be a NEW recurrence of, in a different shape — a window that isn't just double-paging but
  possibly not writing at all for this bucket).
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` (consolidator runtime + liveness
  contract).

## Progress Log

- **2026-08-21, data_pipeline_failure escalation agt-2b817b (slot 31)**: filed after live diagnosis.
  Resumed the job at 15:52:59Z (no live window, no justifying VM). 5-minute background watch armed
  to check for immediate re-pause — result pending, will be appended below before this escalation
  closes.
- **2026-08-21, same session, watch completed**: `gcloud scheduler jobs describe` polled every 20s
  for 300s straight — job stayed `state: ENABLED` the entire window (re-verified live once more
  after the watch exited: still `ENABLED`, `userUpdateTime` unchanged at `15:52:59Z`). No re-pause
  observed. Per this doc's own todo 1 decision rule: downgrading priority `P1 -> P2` (no active
  re-triggering condition caught live), but NOT closing the doc — the missing-maintenance-window
  question (todo 2) is real regardless of whether this specific occurrence recurs, since
  `RevocationActuator._register_maintenance_windows` is correctly wired yet no window was found at
  diagnosis time. Escalation `agt-2b817b` closing out here (one-shot lifecycle); this doc stays
  `assigned_vm: planning` for a future dispatch to pick up todos 1-3.
- **2026-08-21, data_pipeline_failure escalation agt-0b7473 (slot 4)**: re-fired for the same job, now
  `PAUSED` again at `16:27:11Z` — confirmed recurrence, not a stale re-fire (well past agt-2b817b's clean
  5-min watch). Root-caused both previously-open questions: (1) FLEET_HALT/RevocationActuator ruled out
  structurally — `SCHEDULER_REGISTRY` has zero entries for any of the 10 real per-AG consolidator jobs, so
  `_scheduler_jobs_for()` can never select this job name; (2) the actual actor across all 7 toggles in the
  3h window is a MacOS-hosted, non-interactive Claude Code CLI session (`agent-name/claude-code_2-1-237_agent`,
  consistent IP), not any in-repo code path — grepped fleet-wide for other `pause_job`/`CloudSchedulerClient`
  callers, zero hits. See the "2026-08-21 UPDATE" section above for full evidence. Did NOT resume a 3rd
  time — the accelerating toggle cadence (5min → 12sec → 78sec gaps) reads as live, active work on this
  exact resource, and repeatedly resuming risked racing it (precedent:
  `defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md`'s near-miss). Escalated via `/blocked`
  (`BLK-fbcafec2`, recommendation "leave paused"), polled 2 minutes per role protocol, no answer arrived —
  stopping per protocol rather than holding the slot or guessing. Flipped todos 1-2 (answered); added a new
  `[OPERATOR]` todo for the blocked-question answer and a new `[CODE]` P3 todo for the separate, confirmed
  `SCHEDULER_REGISTRY` coverage gap (real bug, not this incident's cause — flagging whether FLEET_HALT is
  even supposed to reach the consolidator crons is itself an open design question). Job left `PAUSED`
  deliberately, pending the operator's answer. Doc stays `assigned_vm: planning`, `status: open`.
- **2026-08-21, data_pipeline_failure escalation agt-0fc6b2 (slot 9)**: re-dispatched for the same
  DP-WATCHER-004 condition. By the time this session reached live diagnosis, the job was already `ENABLED`
  (`gcloud scheduler jobs describe` → `state: ENABLED`, `userUpdateTime: 2026-08-21T17:45:45Z`). A
  corrected-format audit-log read (`logName=cloudaudit.googleapis.com%2Factivity`, default descending
  order, explicit `callerSuppliedUserAgent`, `timestamp>=2026-08-21T16:00:00Z`) shows the full tail:
  `16:20:37Z Resume(mac) → 16:25:41Z Pause(mac) → 16:25:53Z Resume(mac) → 16:27:11Z Pause(mac) →
  17:43:23Z Pause(mac, redundant — already paused) → 17:45:45Z Resume(LINUX, term/tmux-256color,
  interactive/False, from-script/False)`. The 17:45:45Z resume's user-agent does NOT match the recurring
  MacOS actor's signature (`client-os/MACOSX`, `from-script/True`) — it is a THIRD, distinct actor, closer
  in shape to an orchestrator-VM-hosted agent session (matches the pattern noted for agt-2b817b's own
  15:52:59Z resume) than to either the Mac session or a plain human `gcloud` call. No further toggle
  observed in the ~41 min between that resume and this check (18:26:58Z) — longer than the ~27 min quiet
  window that preceded agt-2b817b's own resume getting flipped back, so this is somewhat stronger (not
  conclusive) evidence the Mac session's active-work period has concluded. Checked `BLK-fbcafec2` directly
  (`GET /api/blocked/BLK-fbcafec2`): still `answered_at: null` / `answer: null` — the 17:45:45Z resume did
  NOT go through the official answer flow; whatever performed it did so out-of-band, consistent in outcome
  with option B but not a formal answer. Did NOT re-pause the job, did NOT call the answer API myself (this
  question was addressed to `main_agent`/operator authority, not a fresh escalation worker — left for them
  to close formally), and did NOT post a second `/blocked` question (one is already open and paged;
  duplicating it would just be alert noise). Re-verified the DP-WATCHER-004 read path
  (`check_consolidator_scheduler_paused` reads `state != "PAUSED"` via the same `gcloud describe`
  equivalent) no longer flags this job as of this check. No code change shipped — root cause was already
  conclusively established by the two prior escalations as an external actor, not an in-repo bug; nothing
  in this session's findings changes that conclusion. Corrected the now-stale "Job is currently `PAUSED`
  pending this answer" claim in the `[OPERATOR]` todo above (strikethrough + correction, same edit). Doc
  stays `assigned_vm: planning`, `status: open`, `priority: P2` — the residual open items (BLK-fbcafec2's
  formal answer, the third-actor identity, the `SCHEDULER_REGISTRY` design question, the cross-link todo)
  are all still genuinely open, none resolved by this session. One-shot escalation `agt-0fc6b2` closing out
  here.
- **2026-08-21, data_pipeline_failure escalation agt-17e0d2 (slot 33)**: re-dispatched for the same
  DP-WATCHER-004 condition (boot context carried the raw finding, no pre-filed slug — this doc already
  existed from the 3 prior escalations, so appending here rather than filing a duplicate). Live check:
  `state: PAUSED`, `userUpdateTime: 2026-08-21T19:11:55.938445Z`. Corrected-format audit log
  (`logName=cloudaudit.googleapis.com%2Factivity`, `--freshness=6h`) shows the MacOS actor's toggling
  never actually stopped after agt-0fc6b2's 41-min quiet window — it resumed: `19:02:41Z Resume(mac) →
  19:11:15Z Pause(mac) → 19:11:20Z Resume(mac) → 19:11:21Z Resume(mac) → 19:11:55Z Pause(mac) →
  19:11:56Z Pause(mac)` (same signature throughout: `agent-name/claude-code_2-1-237_agent`,
  `client-os/MACOSX`, non-interactive). No defi VM in the current fleet (`instr-backfill-defi*`,
  `mdps-defi-2025-*`, `mdps-features-live-defi-*`, all healthy per their own contracts) matches a
  manual-manifest-rewrite pattern that would justify a deliberate pause. Checked `BLK-fbcafec2` directly:
  still `answered_at: null` — genuinely unanswered, not just stale. **Did not resume the job and did not
  post a second `/blocked` question** — same reasoning as agt-0b7473/agt-0fc6b2: an already-open,
  unanswered blocked question covers this exact decision, a duplicate would be alert noise, and the
  toggling is evidently still live/active (6 toggles in the ~9 min immediately preceding this check),
  so resuming would very likely just be flipped back and could race whatever the Mac-side session is
  doing. Corrected the now-stale "stable 41+ min" framing in the `[OPERATOR]` todo above (same edit).
  Root cause remains what agt-0b7473 already conclusively established (external actor, not an in-repo
  bug) — nothing in this session's findings changes that; no code shipped. Doc stays
  `assigned_vm: planning`, `status: open`, `priority: P2`. One-shot escalation `agt-17e0d2` closing out
  here.
- **2026-08-21, data_pipeline_failure escalation agt-bb2394 (slot 31)**: re-dispatched for the same
  DP-WATCHER-004 condition (boot context carried the raw finding, no pre-filed slug — appending to this
  already-existing doc rather than filing a duplicate, per the pattern set by the 3 prior re-dispatches).
  Live check (20:07:38Z): `state: PAUSED`, `userUpdateTime` unchanged at `2026-08-21T19:11:55.938445Z` —
  a ~56min quiet window with no further toggle, longer than any quiet window observed so far in this
  incident (previous longest was agt-0fc6b2's ~41min, which then resumed toggling per agt-17e0d2's
  follow-up). `gcloud logging read` for the job confirmed zero scheduler-pause/resume events since
  `19:11:56Z`. New finding: `gcloud compute instances list` shows `defi-manifest-projection-20260821-195038`
  currently `RUNNING` (zone `asia-northeast1-c`), labeled `asset-group=defi env=prod
  managed-by=deployment-service purpose=defi-manifest-projection`, created ~`20:01Z` — i.e. after the
  MacOS session's toggling settled. This is a genuine, deployment-service-managed defi manifest job,
  which plausibly explains the pause as deliberate (holding the consolidator off while a manifest
  projection is in flight) rather than erratic local iteration — strengthening, not just repeating, the
  case for option A on `BLK-fbcafec2`. Checked `BLK-fbcafec2` directly: still `answered_at: null`. Per
  the same reasoning as the 3 prior escalations (an open, unanswered blocked-question already covers this
  exact leave-vs-resume decision; a duplicate would be alert noise; resuming risks racing genuine
  in-flight work), did **not** resume the job and did **not** post a second `/blocked` question. No code
  shipped — this session's contribution is the new correlating VM evidence, appended above and here. Doc
  stays `assigned_vm: planning`, `status: open`, `priority: P2`. One-shot escalation `agt-bb2394` closing
  out here.
