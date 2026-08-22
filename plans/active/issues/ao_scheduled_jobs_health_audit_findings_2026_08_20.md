---
doc_type: issue
title: AO scheduled-jobs health audit findings — Track B synthesis (2026-08-20)
summary: >-
  Synthesis of the 7-job Track B audit from ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md — for each of
  AO's scheduled jobs (excluding plan_reconciler, whose PR-backlog problem motivated this audit and was already
  resolved in that plan's Track A): sharded y/n, typical run time, review-gate present y/n, escalation-resolution
  health. Two genuine gaps found, both minor and neither reproducing plan_reconciler's review-gate-starves-escalation
  failure class exactly — filed as follow-ups here rather than fixed inline, per the source plan's own evidence bar
  (≥2 clean proven runs before a fix ships).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, scheduled-jobs, health-audit, escalation, review-gate]
related:
  [
    /plans/archive/2026_08/ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/issues/ao_scheduled_job_reaped_stale_rate_2026_08_18.md,
  ]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/2026_08/ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    /plans/active/issues/ao_scheduled_job_reaped_stale_rate_2026_08_18.md,
    agent-orchestrator/scripts/orchestrator/check-scheduled-job-health.sh,
    agent-orchestrator/scripts/orchestrator/list_operator_gated_queue.py,
  ]
source: >-
  Interactive session, 2026-08-20 — completing Track B of
  ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md (the synthesis todo its own text asked for).
---

# AO scheduled-jobs health audit — synthesis (2026-08-20)

One row per scheduled job. "Review-gate" = does the job route its output through a review-branch/PR gate the way
`plan_reconciler` used to (the exact failure class this whole audit exists to catch — a gate nobody graduates, and
`regen_backlog_from_plan.py` never reading open PR branches, meaning `[OPERATOR]`-tagged findings inside them can never
surface as a dashboard row).

| Job                          | Sharded?              | Measured run time                             | Review-gate?                        | Escalation health                                                                            |
| ----------------------------- | ---------------------- | ---------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `plan_reconciler`             | Yes (10 tranches)      | —                                               | **Was — now graduated to direct-push** | Healthy since 2026-08-16 graduation (Track A of the source plan, 0 stuck PRs)                  |
| `ag-closeout-auditor`         | Yes (10 tranches)      | 6.5–63.9 min/tranche                            | None                                  | Healthy — findings reach operator (e.g. sports batch14, 24 orphans → 10-item dispatch batch)   |
| `cefi-mtds-smoke`              | N/A — **RETIRED 2026-08-15** | N/A (no active timer)                    | N/A                                   | N/A — dormant (deliberate operator cost/contention decision, code left intact for manual use)  |
| `cefi-reconciliation-auditor` | No                      | Daily-effective (2h-cadence, day-guard once)    | None                                  | Healthy — findings landed 08-08, 08-09, 08-18, 08-19; zero stuck `[OPERATOR]` tags             |
| `context-scout`                | No (Phase-0 incremental skip instead) | 3.5h+ per fire (rescheduled hourly→12h 08-15)  | None                                  | Direct-ship + escalations reach operator, but see Finding 1 (high reaped-stale rate)           |
| `docs-reconcile`               | No                      | Completes without timeout/reaped-stale (small-sample) | None                            | Direct-ship + escalations reach operator, but see Finding 1 (high reaped-stale rate — corrected 2026-08-20) |
| `escalation-queue-reconciler`  | No                      | Seconds (healthy path); 6000s ceiling for deep path | None                              | Healthy for what it watches — **GAP — see Finding 2 below** (blind to external GitHub state)   |
| `na-eligibility-auditor`       | Yes (10 tranches)      | Minutes to 6h ceiling per tranche               | None                                  | Healthy — conflict-checked satellite extraction batches (e.g. this session's batch25)          |

**Headline: no job reproduces plan_reconciler's exact failure** (a review-branch/PR gate that nobody graduated, silently
starving `[OPERATOR]` findings inside it). None of the other 7 route through a PR gate at all — every one ships direct
via `quickmerge.sh --agent --files`. The two gaps found below are a different shape each, not the same bug recurring.

## Finding 1 — context-scout AND docs-reconcile: high reaped-stale rates (CORRECTED 2026-08-20, same day)

**Corrected same-day**: this finding originally cited a single stale 2026-08-19 snapshot (83% for `context_scout_auditor`
only) and called `docs-reconcile` healthy. A sibling doc,
[`ao_scheduled_job_reaped_stale_rate_2026_08_18.md`](ao_scheduled_job_reaped_stale_rate_2026_08_18.md), already owns
this exact measurement scope and posted a **fresher, larger-sample pull the same day** (2026-08-20,
`check-scheduled-job-health.sh agents`, 89 retained agents fleet-wide): `context_scout_auditor` 5/7 (71%),
`docs_reconciler` 8/18 (44%) — **both** real above-fleet-average drivers (fleet-wide 31%), correcting the earlier
5-run docs_reconciler sample that looked healthy at 0%. `ag_closeout_auditor` (39%) and `plan_reconciler` (30%) are
also above average but closer to the fleet mean; `cefi_reconciliation_auditor` (17%) and `na_eligibility_auditor` (5%)
are the genuinely healthy ones.

**Not duplicating the investigation here** — `ao_scheduled_job_reaped_stale_rate_2026_08_18.md` is the active owner
(un-parked 2026-08-20 now that Track B is closed) with its own 2 open follow-up todos (full-week per-job baseline,
then root-cause the real drivers). Track this there, not as a new todo in this doc.

Separately, `plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` carries one open
`[OPERATOR]` todo (a human line-cap trim) whose blocking premise **expired** — a later context-scout run already did
the trim it was waiting on — but the tag was never retagged to reflect that, violating CLAUDE.md's "retag in the same
edit the moment an `[OPERATOR]` tag resolves" rule. It carries no `BLK-op-*` dashboard row (confirmed live via
`list_operator_gated_queue.py` — only 2 unrelated rows exist), so an operator watching the queue never sees it: the
todo exists only as un-surfaced plan-doc prose, the same terminal shape as plan_reconciler's stuck PRs, via a different
mechanism (a rotted premise, not a starved gate).

- [x] ✅ [DOC] P3. Retag or resolve `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md`'s stale
      `[OPERATOR]` todo now that its blocking premise (the line-cap trim) has already happened — either close it with
      the completed trim as evidence, or retag it to whatever it's actually still waiting on. Repo: unified-trading-pm.
      **CLOSED 2026-08-21 (na-eligibility-audit, ao tranche) — moot, target doc already archived.** Direct check:
      `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` no longer exists under `plans/active/` —
      it is at `plans/archive/2026_08/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md`,
      meaning it already went through normal archival (which requires zero open todos) since this finding was
      written. The stale-tag concern this todo tracked has already been resolved as part of that archival.

## Finding 2 — escalation-queue-reconciler is blind to external GitHub PR-backlog state

`escalation-queue-reconciler` polls the orchestrator's own DB (`GET /api/escalations/active`) — it would **not** have
caught the plan_reconciler PR-backlog problem, because a scheduled job that completes `lifecycle-complete` without
crashing never creates a DB escalation row, regardless of what happens to its output afterward (an unmerged GitHub PR
is invisible to this job's data source entirely). This is a structural blind spot, not a bug — the job was never
designed to watch git/GitHub state.

- [ ] [BACKEND] P3. Consider folding an external-PR-backlog check into `/escalation-queue-reconcile` (or a small
      dedicated check) — query GitHub for open PRs matching known scheduled-job branch patterns (e.g. `head:<job>/`)
      older than a safe threshold (~24h) and file a finding if any exist. Low urgency: no job currently produces
      review-branch PRs (plan_reconciler graduated off that pattern 2026-08-16, nothing else ever used it) — this is
      a preventive gap-closer for if the pattern is reintroduced, not an active incident. Repo: agent-orchestrator.

## Finding 3 — `check-scheduled-job-health.sh` is hardcoded to SSM, fails outright when run ON the orchestrator VM

Found live 2026-08-22 by an `/ao-watchdog` scheduled run dispatched directly on the orchestrator VM (a
`plan_health`-family worker, not an interactive laptop session). The script always dispatches its check via `aws
ssm send-command` against the orchestrator instance, with no branch for "I'm already running on that host, just
curl localhost directly." A `plan_health`-dispatched worker's IAM identity does not necessarily carry
`ssm:SendCommand` on the instance (this run hit `AccessDeniedException: User:
arn:aws:iam::427895769566:user/ikenna-worker is not authorized to perform: ssm:SendCommand`), so the script fails
with zero data instead of degrading to a local call — even though the script's own SSM payload is nothing more
than a curl against `http://localhost:8765`, the exact host the failing caller was already on.

- [ ] [INFRA] P3. Add a local-execution branch to `check-scheduled-job-health.sh`: detect `curl -s -m 5
      localhost:8765/api/mode` succeeding (same detection this skill's own Step 1 already uses) and, if so, call
      `http://localhost:8765` directly instead of wrapping every request in an SSM `send-command`/
      `get-command-invocation` round trip. Cheap workaround documented in `/ao-watchdog`'s own SKILL.md Step 5 in
      the meantime (call `/api/scheduled-jobs/recent?within_hours=N` and `/api/agents?include_finished=true`
      directly), but the script itself should not require a manual workaround for its own most-privileged caller.
      Repo: agent-orchestrator.

## Progress Log

- **2026-08-20**: doc authored, completing the Track B synthesis todo in
  `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md`.
- **`/ao-watchdog` 2026-08-22 (slot 29, scheduled run)**: added Finding 3 — `check-scheduled-job-health.sh`'s
  SSM-only dispatch fails when the caller is already on the orchestrator VM and lacks `ssm:SendCommand`. Worked
  around live by calling the same two `localhost:8765` endpoints the script's own SSM payload hits, and documented
  that workaround in the skill file itself (per its "folding findings back in" standing instruction) so the next
  run doesn't rediscover it from scratch.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-21 (ao tranche)**: KEEP-NA, stale items — closed the DOC retag item above with hard
  evidence (target doc already archived, meaning the stale tag it tracked was already resolved through normal
  archival). The remaining `[BACKEND] P3` item (fold an external-PR-backlog check into escalation-queue-reconciler)
  stays open and NA: its own text explicitly frames it as a low-urgency, speculative "Consider" — a preventive
  gap-closer for a pattern (review-branch PRs) no current job even uses, not a definitively-scoped build task yet.
  Erring toward KEEP-NA per this audit's own guidance rather than force a build decision that isn't clearly ruled.
  Doc stays `assigned_vm: NA`.
