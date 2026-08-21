---
doc_type: issue
title: >-
  36% of retained scheduled-job family agents ended reaped-stale (2026-08-18 snapshot) — not
  root-caused, flagged for the next /ao-watchdog pass to dig into
summary: >-
  ao-watchdog (2026-08-18, this session) pulled `check-scheduled-job-health.sh agents` and found
  75 retained scheduled-job-family agents fleet-wide, 27 of them (36%) ended `reaped-stale`
  (spawned, then died without ever reaching `/done` — per the skill's own definition, "its
  findings survive only in what it already committed + its durable transcript"). A per-job
  breakdown pulled the same session found `context_scout_auditor` specifically at 2/4 runs (50%)
  reaped-stale in a 48h window (small sample), `na_eligibility_auditor` much healthier at ~1%
  (1/95), `docs_reconciler` at 0% (0/5) — so the fleet-wide 36% is not evenly distributed, some
  specific job type(s) are dragging the average up. This was reported to the operator in chat but
  never persisted anywhere — filed now per the workspace's own "every deferral becomes a tracked
  todo" rule, not investigated further this session (context budget ran out before root-causing
  it).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao-watchdog, scheduled-jobs, reaped-stale]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    /plans/active/issues/ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md,
  ]
created: "2026-08-18"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
assigned_role: infra
drift_direction: none
source: >-
  Interactive /ao-watchdog run, 2026-08-18 (this session) — `check-scheduled-job-health.sh agents`
  and a targeted per-job follow-up pull.
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/ao_scheduled_jobs_health_audit_findings_2026_08_20.md,
    agent-orchestrator/server/tmux_pruner.py,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    /plans/active/issues/ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md,
    /plans/active/issues/ao_scheduled_dispatch_pause_reasons_2026_08_18.md,
  ]
---

# Scheduled-job reaped-stale rate — 36% fleet-wide, not evenly distributed

## The numbers (2026-08-18 snapshot)

- Fleet-wide: 75 retained scheduled-job-family agents, 27 reaped-stale (36%).
- `context_scout_auditor`: 2/4 runs (50%) reaped-stale, 48h window — small sample.
- `na_eligibility_auditor`: 1/95 (~1%) — healthy.
- `docs_reconciler`: 0/5 (0%) — healthy.

The healthy jobs (na_eligibility_auditor, docs_reconciler) show the 36% fleet average isn't a
uniform capacity/account problem — something specific to a subset of job types (context_scout_auditor
at minimum, plus whichever other jobs weren't individually checked this session) is driving it.

## Not yet done

- No root-cause investigation — didn't check WHY `context_scout_auditor` specifically dies before
  reaching `/done` at this rate (a real code bug in that role, a systematically-too-short timeout,
  an account/capacity issue specific to when it runs, etc.).
- Didn't check the other job types (`ag_closeout_auditor`, `cefi_reconciliation_auditor`,
  `ci_reconciler`, `data_pipeline_alerts_reconciler`, `escalation_queue_reconciler`,
  `plan_reconciler`) individually — only the 3 named above were pulled.
- Didn't check whether this is a NEW pattern or a longstanding baseline rate.

## Relationship to the separate "sessions never reaped" gap (same night, different hunter)

Filed the same night (2026-08-18) as
`/plans/active/issues/ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md` — both
live in the same `tmux_pruner.py` subsystem, so they're worth distinguishing rather than conflating. Code-confirmed
(`agent-orchestrator/server/tmux_pruner.py` ~line 730-752): `exit_reason="reaped-stale"` is the label the pruner
applies when it successfully archives a one-shot/scheduled agent whose tmux session it found already gone (a
heuristic "this session died without a confirmed `/done`" call, not a confirmed crash) — i.e. this doc's 36% figure
measures a **death rate** (sessions that DID get cleaned up, just via the stale-archival path instead of a clean
completion), not a failure of the reap mechanism itself. The other doc's title ("never get their tmux sessions torn
down") describes the opposite shape — sessions that are NOT being reaped at all, sitting alive and blocking new
dispatch. Distinct mechanisms per this code read; not asserting they share no common cause (unconfirmed either way),
just that this doc's numbers should not be read as evidence for the other doc's claim or vice versa.

## Runtime-exposure correlation (2026-08-20, interactive /ao-watchdog-style session)

Confirmed via `tmux_pruner.py` (~line 719-752): `exit_reason="reaped-stale"` for a scheduled/one-shot agent fires on
the exact same `has_session()`-returns-False signal as the general `tmux_session_lost` mechanism tracked in
`ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` — this is NOT a separate scheduled-job-specific bug, it's
that root cause landing on scheduled jobs. That doc's own finding ("whatever kills sessions is roughly uniformly
likely per session-second") predicts the per-job rate ordering seen in the 2026-08-20 measurement almost exactly:
the one long-running UNSHARDED job (`context_scout_auditor`, 3.5h+ single session) has the highest rate (71%), while
the sharded jobs whose individual tranches mostly finish in minutes (`na_eligibility_auditor`) have the lowest (5%).
`ag_closeout_auditor`/`plan_reconciler` (sharded but with longer/wider per-tranche runtime, 6.5-64 min) sit in
between (39%/30%). `docs_reconciler`'s 44% is inconsistent with an earlier stale small-sample read that called it
"short-running" — its real per-run duration should be re-checked, since the correlation predicts it's longer than
assumed if the rate holds. Runtime exposure, not job identity, is the leading explanatory variable — continued
progress on the general tmux-death investigation (most recently the 2026-08-20 `setsid`/orphan-reap fix) should
reduce this across every job, not just the worst offenders.

- [ ] [INFRA] P2. Consider sharding `context_scout_auditor` (the one long-running, never-sharded scheduled job) into
      tranches the way `ag_closeout_auditor`/`na_eligibility_auditor`/`plan_reconciler` already are, mirroring the
      "Phase-0 incremental skip instead" note in `ao_scheduled_jobs_health_audit_findings_2026_08_20.md` — reducing
      its per-session runtime should directly cut its reaped-stale exposure window, consistent with the correlation
      above. (repo: agent-orchestrator)
- [ ] [SCRIPT] P2. Re-measure `docs_reconciler`'s actual typical per-run duration (not the stale small-sample
      "completes without timeout" read) — the correlation above predicts it should be longer-running than assumed
      given its 44% reaped-stale rate. (repo: agent-orchestrator)

## Follow-up

- [ ] [SCRIPT] P2. Pull per-job reaped-stale rates for every scheduled-job type (not just the 3
      checked 2026-08-18) over a full week, not just 48h, to get a stable baseline and confirm
      which job(s) are actually driving the 36% fleet average. (repo: agent-orchestrator)
- [ ] [SCRIPT] P2. For whichever job(s) the above confirms as the real driver, read its role
      script + recent reaped-stale agent transcripts to root-cause why it's dying before `/done`
      (timeout too short for its real runtime, a crash, an account-rotation mid-task, etc.).
      (repo: agent-orchestrator)

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:92319e5e5f802a59]: KEEP-NA, valid (conflict-parked) — both open todos (per-job reaped-stale-rate measurement + root-cause) read as bounded in isolation, but Track B of `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md` already claims this exact ground (per-job reaped-stale/timeout/error measurement across all 7 non-review-gate scheduled jobs) under an explicit 2026-08-17 operator ruling that Track B 'requires real judgment'. Conflict-check: NOT cleared — parked rather than reclassified or extracted, per the shared conflict-check protocol's verbatim-overlap rule (do not draft a competing todo, do not silently prefer either side). Flagging for an explicit operator ruling on whether this doc's narrower, already-partially-measured claim (3 jobs done this session) is exempt from Track B's broader NA ruling, or should simply feed its results into Track B when that audit runs.
- **2026-08-20 (interactive session, un-parking)**: Track B of `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md`
  closed out today — but its own per-job pass did NOT do the systematic per-job reaped-stale-rate measurement this
  doc's scope covers (it cited a single older SSM snapshot for `context_scout_auditor` only, from the tracker dated
  2026-08-19). This doc's own numbers, gathered the SAME day via a fresh `check-scheduled-job-health.sh agents` pull
  (see the 2026-08-20 entry above), are the more complete, more current measurement. Ownership question resolved:
  this doc stays the active owner of the reaped-stale-rate investigation — un-parked, both follow-up todos remain
  live. Cross-referenced INTO `ao_scheduled_jobs_health_audit_findings_2026_08_20.md` (the Track B synthesis doc)
  rather than duplicating a competing todo there.
- **context-scout 2026-08-19**: populated context_scope (4 entries).
- **ao-watchdog 2026-08-20**: re-pulled `check-scheduled-job-health.sh agents` (cumulative "retained" agents, same
  un-day-scoped query as the 2026-08-18 baseline — NOT a clean day-over-day diff, a bigger sample of the same
  ever-growing retained set). Fleet-wide: 89 retained, 28 reaped-stale (31%, down slightly from 36%/75 on 08-18 —
  within noise, not a real change). Per-job, now with a much bigger sample than the original 3-job/48h pull:
  `ag_closeout_auditor` 7/18 (39%), `cefi_reconciliation_auditor` 1/6 (17%), `context_scout_auditor` 5/7 (71%, up
  from the small 2/4-sample 50% on 08-18 — same job, consistently high), `docs_reconciler` 8/18 (44%, vs the 0/5
  sample on 08-18 — **the earlier 0% was small-sample noise, not a real baseline**; the true rate was always
  closer to this), `na_eligibility_auditor` 1/20 (5%, consistent with 08-18's ~1%), `plan_reconciler` 6/20 (30%,
  not measured individually on 08-18). Read as CLAIM-vs-MEASUREMENT correction, not a fresh regression: with more
  data, `context_scout_auditor` and `docs_reconciler` are the two real above-fleet-average drivers (this doc's
  original "not evenly distributed" hypothesis holds, just with `docs_reconciler` added to the suspect list
  instead of being the healthy control it looked like on a 5-run sample). Feeds directly into the still-open
  Track B claim above — not investigated further here (still parked pending the operator ruling on ownership).
  Also worth noting live during this same run: `scheduled-dispatch/status` still shows exactly the 6 modes paused
  that `ao_scheduled_dispatch_pause_reasons_2026_08_18.md`'s 2026-08-19 MEASURED UPDATE recorded (`ag_closeout`,
  `cefi_mtds_smoke`, `ci_reconcile`, `na_eligibility`, `reconcile`, `report`) — unchanged since that doc's last
  edit, so its open `[OPERATOR] P1` (record reasons for the 3 still-unexplained pauses) remains accurate and live,
  not stale.
- **context-scout 2026-08-20**: refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-21 (ao tranche)**: RECLASSIFY (whole-doc) — Track B (the doc that previously
  conflict-parked this one on 2026-08-19) closed out 2026-08-20 and this doc's own 2026-08-20 entry already
  confirmed it is the un-parked, active owner of the investigation, with real evidence its own scope is more
  complete/current than Track B's synthesis. Re-read all 4 open todos: each is a bounded measurement/data-pull task
  with a stated done-when (shard `context_scout_auditor` mirroring an established sharding pattern already used by
  3 sibling jobs; re-measure `docs_reconciler`'s real per-run duration; pull a full-week per-job baseline; root-cause
  whichever job the baseline confirms as the real driver by reading its role script + transcripts) — no open
  design/judgment fork, each follows a precedent or a direct measurement. Conflict-check: grepped `plans/active/`
  for "reaped-stale"/"reaped_stale" — hits are either this doc's own sibling synthesis doc (already cross-referenced,
  not duplicative), the general tmux-session-death root-cause doc (a different, broader investigation this doc's own
  text already correlates against but does not duplicate), or unrelated passing mentions — no doc claims this
  specific per-job full-week measurement. Flipped `assigned_vm: NA → planning`,
  `execution_scope: local-only → orchestrator-agent`; `assigned_role: infra` was already correct.
