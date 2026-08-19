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
assigned_vm: NA
execution_scope: local-only
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

## Follow-up

- [ ] [SCRIPT] P2. Pull per-job reaped-stale rates for every scheduled-job type (not just the 3
      checked 2026-08-18) over a full week, not just 48h, to get a stable baseline and confirm
      which job(s) are actually driving the 36% fleet average. (repo: agent-orchestrator)
- [ ] [SCRIPT] P2. For whichever job(s) the above confirms as the real driver, read its role
      script + recent reaped-stale agent transcripts to root-cause why it's dying before `/done`
      (timeout too short for its real runtime, a crash, an account-rotation mid-task, etc.).
      (repo: agent-orchestrator)

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:92319e5e5f802a59]: KEEP-NA, valid (conflict-parked) — both open todos (per-job reaped-stale-rate measurement + root-cause) read as bounded in isolation, but Track B of `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md` already claims this exact ground (per-job reaped-stale/timeout/error measurement across all 7 non-review-gate scheduled jobs) under an explicit 2026-08-17 operator ruling that Track B 'requires real judgment'. Conflict-check: NOT cleared — parked rather than reclassified or extracted, per the shared conflict-check protocol's verbatim-overlap rule (do not draft a competing todo, do not silently prefer either side). Flagging for an explicit operator ruling on whether this doc's narrower, already-partially-measured claim (3 jobs done this session) is exempt from Track B's broader NA ruling, or should simply feed its results into Track B when that audit runs.
