---
doc_type: plan
title: AO scheduled-jobs review-gate backlog drain + cross-job sharding/health audit
summary:
  Two tracks. (A) Drain the 25 remaining plan_reconciler review-branch PRs stuck open since 2026-08-02 (0 merged, 0
  reviewed) after graduating plan_reconciler to steady-state direct-push — each needs real per-PR judgment (rebase +
  re-verify vs. close as superseded), not a blind force-merge. (B) Audit the other 7 AO scheduled-jobs (ag-closeout-
  auditor, cefi-mtds-smoke, cefi-reconciliation, context-scout, docs-reconcile, escalation-queue-reconciler,
  na-eligibility-auditor) for the same failure-class plan_reconciler just had — corpus-wide unsharded runs vs. bounded
  shards, measured time-to-complete, whether it still routes through a review-branch/PR gate (silently starving its own
  escalation mechanism the same way), and whether an [OPERATOR]-tagged escalation actually reaches a resolved, archived
  state or quietly stalls.
status:
  complete # (was: active) 2026-08-20 -- Track A (25 PRs) closed 2026-08-16, Track B (7 job audits + synthesis) closed
  # 2026-08-20 (this session): all 8 todos [x], synthesis doc written
  # (plans/active/issues/ao_scheduled_jobs_health_audit_findings_2026_08_20.md), locked_by empty --
  # archival-eligible per plan-completion-and-archival-discipline.md.
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ao, scheduled-jobs, plan_reconciler, review-gate, escalation, sharding, audit, plan-hygiene]
related:
  [
    /plans/archive/2026_08/issues/plan_reconciler_findings_2026_08_08.md,
    /plans/archive/2026_08/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  "interactive session, 2026-08-09 — follow-up from the plan_reconciler steady-state graduation + PR-backlog discovery"
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    agents/plan_reconciler.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/scripts/scheduled_job_already_ran.py,
    /plans/archive/2026_08/issues/plan_reconciler_findings_2026_08_08.md,
    /plans/archive/2026_08/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
  ]
---

# AO scheduled-jobs review-gate backlog drain + cross-job sharding/health audit

## Background

An interactive session on 2026-08-09 traced why no `plan_reconciler_findings_<tranche>_<date>.md` docs were visible in
`plans/active/issues/` despite the systemd timer clearly firing (28 `plan_reconciler/agt-*` review-branch PRs existed on
GitHub). Root cause: `agents/plan_reconciler.md` put every run through a "PROVING PHASE" review-branch + PR gate into
`live-defi-rollout` (added 2026-06-17 after an early version died before pushing) with an explicit graduation criterion
— "≥2 clean proven runs, operator-enabled" — that nobody ever pulled the trigger on. 28+ consecutive runs
(2026-08-02→08-09) each completed cleanly end-to-end with zero mid-flight deaths, but every one sat in an unreviewed,
unmerged PR. Worse: `regen_backlog_from_plan.py` only ever snapshots `origin/live-defi-rollout` (never a local checkout,
never an open PR branch) — so any `[OPERATOR]`-tagged todo filed inside one of those findings docs could NEVER surface
as a `BLK-op-*` dashboard row, never get asked, never resolve. Not a missing hookup — a starved one.

Fixed same session: `plan_reconciler` graduated to steady state (direct push, no review branch/PR —
`unified-trading-pm@9df4d0b69f`). 3 of the 28 stuck PRs merged cleanly (#2396, #2400, #2421 — each touched only its own
findings doc). The other 25 have real conflicts from up to a week of corpus drift and need actual per-PR judgment, not a
blind force-merge — that's Track A below. Given this exact failure class (unsharded-run reliability +
review-gate-starves-escalation) could easily exist in AO's other 7 scheduled jobs and nobody has checked, Track B audits
each one.

## Track A — drain the 25 stuck plan_reconciler PRs — CLOSED OUT 2026-08-16

**Verified 2026-08-16** (interactive session, live check): `gh pr list --state open --search "head:plan_reconciler"`
against `IggyIkenna/unified-trading-pm` returns **zero** open results — every one of the 25 branches below is terminal
(confirmed CLOSED). Individual spot-checks on #1998, #2327, #2522, #2653 confirmed CLOSED directly via `gh pr view`.
**Caveat**: this pass confirmed the terminal/non-open STATE for all 25, not each PR's individual disposition reason
(superseded vs. stale vs. duplicate) — that per-PR narrative wasn't re-derived. If a specific PR's reason is ever
needed, `gh pr view <n> --comments` against the closed branch. The doc's own done-when ("PR is either MERGED or
CLOSED") is satisfied for all 25 on the CLOSED branch.

- [x] ✅ [REVIEW] P1. Triage PR #1998 (`plan_reconciler/workflow-undefined`, opened 2026-08-02, 54 files changed) —
      CLOSED, confirmed 2026-08-16 (live `gh pr view` check).
- [x] ✅ [REVIEW] P2. Triage PR #2327 (`plan_reconciler/agt-4fdce1`, opened 2026-08-06) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2395 (`plan_reconciler/agt-d4d31f`, opened 2026-08-06) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2397 (`plan_reconciler/agt-24f4b0`, opened 2026-08-06) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2398 (`plan_reconciler/agt-bf8439`, opened 2026-08-06) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2399 (`plan_reconciler/agt-65e60a`, opened 2026-08-06) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2401 (`plan_reconciler/agt-903867`, opened 2026-08-06) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2402 (`plan_reconciler/agt-6c6359`, opened 2026-08-06) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2413 (`plan_reconciler/agt-ec6642`, opened 2026-08-07) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2415 (`plan_reconciler/agt-a2268a`, opened 2026-08-07) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2416 (`plan_reconciler/agt-cf1afa`, opened 2026-08-07) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2418 (`plan_reconciler/agt-c6e8c7`, opened 2026-08-07) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2419 (`plan_reconciler/agt-e7f024`, opened 2026-08-07) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2420 (`plan_reconciler/agt-985cf1`, opened 2026-08-07) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2423 (`plan_reconciler/agt-6eb8c5`, opened 2026-08-07) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2522 (`plan_reconciler/agt-2add8d`, opened 2026-08-08 — whole-corpus `all` run) —
      CLOSED, confirmed 2026-08-16; consistent with the doc's own prediction that this was a pure duplicate of content
      already merged via a different path.
- [x] ✅ [REVIEW] P2. Triage PR #2630 (`plan_reconciler/agt-8af81b`, opened 2026-08-09) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2631 (`plan_reconciler/agt-1a9b86`, opened 2026-08-09) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2644 (`plan_reconciler/agt-2d9a32`, opened 2026-08-09) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2645 (`plan_reconciler/agt-c3a27f`, opened 2026-08-09) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2647 (`plan_reconciler/agt-fe4564`, opened 2026-08-09) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2649 (`plan_reconciler/agt-c80749`, opened 2026-08-09) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2650 (`plan_reconciler/agt-733350`, opened 2026-08-09) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2652 (`plan_reconciler/agt-a3e83c`, opened 2026-08-09) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Triage PR #2653 (`plan_reconciler/agt-a398c9`, opened 2026-08-09) — CLOSED, confirmed 2026-08-16.
- [x] ✅ [REVIEW] P2. Re-ran `gh pr list --state open --search "head:plan_reconciler"` 2026-08-16 — **zero open PRs
      remain.** Final count: 0.

## Track B — audit the other 7 scheduled jobs for the same failure class

Per job: (1) read its `install-<job>-timer.sh` — is it sharded or does it run its full corpus unsharded on every fire;
(2) find its most recent 3-5 run-findings/report docs (or dashboard scheduled-jobs history if reachable) and note actual
measured wall-clock + any `reaped-stale`/`timeout`/`error` outcomes; (3) grep its own agent/skill boot prompt for a
review-branch + PR pattern like the one just fixed — if present, is there a clean graduation path defined, and has
anyone checked whether it's actually still gated; (4) if the job files `[OPERATOR]`-tagged or `BLOCKED-*` findings, pick
2-3 recent examples and trace whether they actually reached a `BLK-op-*` dashboard row and got resolved, or whether
they're sitting the same way plan_reconciler's were. Where a dedicated skill already exists for the job (several do),
run it or read its most recent output rather than re-deriving from scratch — this track is about the JOB'S OWN
reliability/escalation shape, not re-running its normal audit content.

- [x] ✅ [REVIEW] P2. **HEALTHY — no gap found.** Audit `ag-closeout-auditor` (`install-ag-closeout-auditor-timer.sh`,
      `/ag-closeout-audit` skill) — sharding shape, measured run time, review-gate check, escalation-resolution trace.
      Findings recorded inline below (checkbox was stale — content was already fully answered, flipped 2026-08-20).
      * **1. Sharding shape**: Sharded into exactly 10 topic tranches (`ALL_TRANCHES=(cefi defi tradfi prediction sports cross-cutting ao ci infra ui)`) via `scripts/install-ag-closeout-auditor-timer.sh` (line 129). Dispatched in batches of up to `MAX_CONCURRENT_TRANCHES="4"` (configured in lines 73, 179) via POST requests to `/api/plan-health/dispatch` with `{"mode": "ag_closeout", "tranche": "<name>"}`.
      * **2. Measured run time**: Real measured single-tranche runtimes on record range from **6.5 min to 63.9 min** (cited in `scripts/install-ag-closeout-auditor-timer.sh` lines 315-320, tracking `registered_at -> AgentRow finished_at`). Systemd timer timeout `TimeoutStartSec` is set to `21600` (6 hours) to accommodate batched multi-tranche execution without premature SIGTERM.
      * **3. Review-gate check**: No review-branch/PR gate exists for this job (unlike `plan_reconciler`'s historical PR gate). As specified in `agents/ag_closeout_auditor.md` (lines 35-42) and `cursor-configs/skills/ag-closeout-audit/SKILL.md`, the worker executes its audit one-shot, writes draft plans (`status: draft`) for extracted bounded work (`<tranche>_satellite_ao_dispatch_batch<N>_<date>.md` + `_finalize`), and reports text summaries directly via `/done` evidence, bypassing any blocking PR queue.
      * **4. Escalation-resolution trace**: Successfully produces actionable issue and parked findings reports. For instance, the scheduled `/ag-closeout-audit sports` run on 2026-08-16 produced `unified-trading-pm/plans/active/issues/ag_closeout_audit_sports_parked_2026_08_16.md`, identifying 24 genuine orphans and extracting 10 items into a concrete draft batch (`sports_satellite_ao_dispatch_batch14_2026_08_16.md`), demonstrating that escalations and orphan discoveries actively reach operator visibility rather than starving behind unmerged PRs.
- [x] ✅ [REVIEW] P2. **N/A — job RETIRED 2026-08-15, confirmed via codex + repo state (measured 2026-08-20).** Audit
      `cefi-mtds-smoke` — same 4 checks. `agent-orchestrator/scripts/install-cefi-mtds-smoke-timer.sh` no longer exists
      in the repo (deleted); `codex/04-architecture/agent-orchestrator-scheduled-jobs.md` § "RETIRED 2026-08-15"
      documents the operator decision directly: the underlying `/data-pipeline-check-mtds` sweep has no
      `--asset_group` scoping (walks the FULL MVP matrix, not just CeFi), so firing it every 2h burned real VM spend
      and starved the shared Tardis N=1 concurrency slot from every other real backfill — confirmed live 2026-08-15, a
      `pipeline-e2e-check-mtds-*` driver VM ran 3+ hours, its sub-VM launches blocking the fleet. Timer + both unit
      files removed from the orchestrator VM (`systemctl --user disable --now cefi-mtds-smoke-tester.timer`); the
      `mode="cefi_mtds_smoke"` dispatch handler in `plan_health.py` and `agents/cefi_mtds_smoke_tester.md` role are
      left intact but unused (deliberately, no code cleanup was in scope). **1-4 are moot — nothing to check for
      sharding/run-time/review-gate/escalation on a job with no active timer.** The check itself remains available as
      a manual, operator-run `/data-pipeline-check-mtds` invocation.
- [x] ✅ [REVIEW] P2. **HEALTHY — no gap found (measured 2026-08-20).** Audit `cefi-reconciliation`
      (`install-cefi-reconciliation-timer.sh`) — same 4 checks.
      1. **Sharding shape**: Unsharded, single `{"mode": "cefi_reconciliation"}` dispatch — runs
         `/data-pipeline-reconciliation --asset-group cefi` (Tier-1: Phase 0 reachability/freshness + distinct-value
         census), read-only against PROD except for narrowly-scoped fixes the run itself surfaces.
      2. **Measured run time / cadence**: Fires every 2h on even hours at :05 (`install-cefi-reconciliation-timer.sh`),
         but the already-ran guard (`--window day`, the default) admits at most one successful run per day — same
         "hourly-attempts, daily-effective" shape as the other 2h-cadence jobs; remaining same-day fires are cheap
         no-ops once it lands. codex table confirms: `cefi-reconciliation-auditor.service`, `curl --max-time 5950`,
         `TimeoutStartSec=6000`, no timeout/`reaped-stale` pattern found in the commit history below.
      3. **Review-gate check**: No review-branch/PR gate — `grep -n "review.branch\|pull request\|gh pr\|branch:"
         agents/cefi_reconciliation_auditor.md` → zero hits; the role file explicitly instructs "fix it via the
         normal quality-gates.sh + quickmerge two-pass" (direct ship to `live-defi-rollout`, same as every other
         healthy job in this audit).
      4. **Escalation-resolution trace**: Live, regular, productive cadence confirmed via `git log --all --grep="cefi
         reconciliation"` — real findings docs landed 2026-08-08, 08-09, 08-18, and most recently **2026-08-19**
         (`plans/audit/results/data_pipeline_reconciliation_cefi_2026_08_19.md`), including a real escalation
         (2026-08-09: honest-coverage OOM raised to P1 on its 3rd/4th missed cycle) and a real live fix (2026-08-08's
         origin run found + fixed a bare-OKX capture regression). `grep -rl "OPERATOR" plans/active/issues/*cefi_reconciliation*
         plans/archive/*/issues/*cefi_reconciliation*` → zero hits — no stuck `[OPERATOR]`-tagged finding from this
         job. **No gap found.**
- [x] ✅ [REVIEW] P2. **GAP FOUND — 2 issues, follow-ups filed below (checkbox was stale, content already fully
      answered; flipped 2026-08-20).** Audit `context-scout` (`install-context-scout-timer.sh`, `/context-scout`
      skill) — same 4 checks; read-mostly (populates `context_scope`), confirmed no review-gate applies (see finding 3
      below). Findings recorded inline.

      - **Audit Findings (measured 2026-08-19, slot-26)**:
        1. **Sharding shape**: NOT sharded — by design. The dispatch POST is a single `{"mode": "context_scout"}` with
           no tranche key (`agent-orchestrator/scripts/install-context-scout-timer.sh:118-120`); codex table row says
           `Sharded? No` (`unified-trading-pm/codex/04-architecture/agent-orchestrator-scheduled-jobs.md:75`); the role
           file explicitly declines tranche sharding ("the skill batches its own doc population internally via a
           Workflow, so one worker per run is sufficient" — `agents/context_scout_auditor.md`, `does_not:` block). Its
           scaling mechanism is Phase-0 incremental skip (NEVER_SCOUTED/STALE/UP_TO_DATE via
           `scripts/plan-hygiene/generate_context_scope_inventory.py`;
           `cursor-configs/skills/context-scout/SKILL.md:48-64`) — but the corpus has NOT reached the "small daily
           residual" steady state that design assumes: the 2026-08-19 session still reported `NEVER_SCOUTED 22->2,
           STALE 581->511` over 97 docs (unified-trading-pm@fdce77f5f7), so each fire is currently a multi-hour
           backfill, not a cheap incremental pass.
        2. **Measured run time**: real completion exceeds 3.5h — that measured number is the stated reason the cadence
           was moved hourly→every-12h on 2026-08-15 (agent-orchestrator@238a4a64, "reschedule context-scout to every
           12h (was hourly vs a 3.5h+ real completion time)", diff: `OnCalendar=*-*-* *:52` → `0/12:52`, installer
           `:221`). Config ceilings: `curl --max-time 5950` (installer `:118`) / `TimeoutStartSec=6000` (installer
           `:211`) — consistent with a 3.5h+ run never hitting them. Measured commit span of one scheduled day
           (2026-08-17, worker `[slot-29·planning]`): context-scout-tagged commits from 01:49:40 UTC (63a8cccf38
           "batch 1/14") to 15:48:33 UTC (4400a483b9 "grind4 batch 5/5") across ≥3 refire sessions — consistent with
           reaped-stale refires re-attempting within the day. Live terminal outcomes (2026-08-19,
           `scripts/orchestrator/check-scheduled-job-health.sh agents` via SSM): `context_scout_auditor` = 1
           `lifecycle-complete` vs **5 `reaped-stale`** (83% of retained runs died before `/done`; family baseline
           27/74 = 36%). Per-day dispatch rows: 2026-08-12/13/14 = `error` ×13/×24/×3 (hourly-retry storms predating
           the reschedule); 08-15→18 = queued/dispatched/quarantined only, no `error` day since. (The 2026-08-19
           backfill commits e88ab02465/fdce77f5f7 are `[slot-2·laptop]` — interactive, not scheduled; excluded from
           run-time evidence.)
        3. **Review-gate check — CONFIRMED N/A (measured, not assumed)**: grep of the job's own boot prompt + skill
           for the plan_reconciler pattern (`review.branch|pull request|gh pr|branch:`) → zero hits (rg exit 1 across
           `cursor-configs/skills/context-scout/SKILL.md` + `agents/context_scout_auditor.md`). Both instruct DIRECT
           shipping: SKILL.md Phase 2 (`:177-179`) "commit prefix `docs(plans):`, ship … (`quickmerge.sh --agent
           --files`)" and the role file STEP 1 ("ship via `quickmerge.sh --agent --files`, per CLAUDE.md"). Live
           confirmation the path is actually used: worker commit 65cffd6d83 carries the `Quickmerge: agent` trailer
           (verified `git show -s`); `gh pr list --state open` (2026-08-19) → zero context-scout PRs; `git branch -r`
           → zero `context*` review branches. No PR/review-branch gate exists to starve — the todo's hunch is
           confirmed on both the prompt side and the live-repo side.
        4. **[OPERATOR]-escalation trace**: the job DOES file durable findings —
           `plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` (author frontmatter
           "context_scout_auditor (dispatch agt-23f116, slot 4)"), still `status: open`. Sibling context-scout issues
           DID reach resolved+archived: `plans/archive/issues/context_scout_source_hunting_gap_2026_08_03.md:29`
           (`status: resolved`); `plans/archive/2026_08/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md:33`
           (`resolved_by: … all 3 Follow-ups closed, 0 open todos remain`). The stale one: the marker-count issue's
           sole open todo is `[OPERATOR] P1. Human line-cap trim of data_completion_defi_2026_07_15.md` (`:159`),
           deferred because that doc "sits at the 1000L hard cap" with no safe edit path (Deferred table `:299`). That
           premise has since EXPIRED — a later context-scout run itself did the trim ("line-cap remediation …
           1033L→469L", `plans/active/data_completion_defi_2026_07_15.md:481-482`; measured 520L today) and restored 1
           of the 2 named drops (`data_completion_to_100_all_ag_2026_06_21.md` present at `:37`;
           `migrate_defi_full_v9_canonical.py` still absent). Yet the `[OPERATOR]` todo sits unchecked since 2026-08-06
           and has NO `BLK-op-*` dashboard row: the live pending operator-gated queue (2026-08-19,
           `scripts/orchestrator/list_operator_gated_queue.py` via `query-ao-state-db-readonly.sh`) holds exactly 2
           rows, both `strategy_service_centralization_fixes` — the context-scout todo exists only as plan-doc prose an
           operator watching the queue never sees. Same terminal shape as plan_reconciler (work landed, escalation
           never closed), different mechanism: a rotted-premise `[OPERATOR]` tag never retagged per the CLAUDE.md
           same-edit retag rule. NOT fixed here — out of audit scope; feed to the Track-B synthesis todo below.
        5. **Doc-drift found during the audit (misled-me class; NOT fixed, out of scope — for the synthesis todo)**:
           three sources still say "hourly" after 238a4a64 (2026-08-15) moved the timer to every-12h — codex table
           `agent-orchestrator-scheduled-jobs.md:75` ("hourly"), SKILL.md Scheduled-cadence `:218-223` ("Fires hourly
           … staggered to :52 past the hour, after plan-reconciler (:00)"), and the installer's own header
           `install-context-scout-timer.sh:21-31` ("in every hourly cycle … the timer retries HOURLY") contradicting
           its own unit at `:216-221`.
- [x] ✅ [REVIEW] P2. **HEALTHY — no gap found.** Audit `docs-reconcile` (`install-docs-reconcile-timer.sh`,
      `/docs-reconcile` skill) — same 4 checks (checkbox was stale, content already fully answered; flipped
      2026-08-20).
      * **1. Sharding shape**: Unsharded. The job (`install-docs-reconcile-timer.sh`, `agents/docs_reconciler.md`, `cursor-configs/skills/docs-reconcile/SKILL.md`) runs corpus-wide across all docs in the PM repository per fire as a single monolithic one-shot run, unlike `ag-closeout-auditor` or `na-eligibility-auditor` which shard into 10 tranches (`ALL_TRANCHES=(cefi defi tradfi prediction sports cross-cutting ao ci infra ui)`).
      * **2. Measured run time**: Runs are structured as one-shot jobs with a high timeout limit (`TimeoutStartSec=6000` in `scripts/install-docs-reconcile-timer.sh` line 215, curl `--max-time 5950` on line 123) to accommodate deep semantic sweeps across the codex corpus. Recent execution records (e.g. dispatch `agt-192c24` on 2026-08-17, recorded in `unified-trading-pm/plans/active/issues/docs_reconcile_findings_2026_08_17.md` line 50) complete successfully without timeout or `reaped-stale` failure, with incremental batch commits per `agents/docs_reconciler.md` line 197 protecting completed work.
      * **3. Review-gate check**: No review-branch/PR gate exists for this job (unlike `plan_reconciler`'s historical PR gate). As specified in `agents/docs_reconciler.md` (lines 96-97) and `cursor-configs/skills/docs-reconcile/SKILL.md` (lines 44, 186-187), the worker executes its audit and ships verified mechanical fixes directly via `quickmerge.sh --agent --files`, committing incrementally and merging straight to the integration branch (`live-defi-rollout`) without sitting in an unmerged PR queue.
      * **4. Escalation-resolution trace**: Successfully produces issue documentation for non-auto-fixable authority and scope questions (e.g., `unified-trading-pm/plans/active/issues/docs_reconcile_findings_2026_08_17.md` containing `[OPERATOR]`-tagged todos regarding archived-doc summary backfills and archival path definitions). Unlike `plan_reconciler` (where PRs were unmerged and `regen_backlog_from_plan.py` ignored open PR branches), `docs_reconciler` writes findings directly to the `unified-trading-pm` repo (`plans/active/issues/`), allowing extraction into conflict-checked satellite dispatch batches (e.g., `ao_satellite_ao_dispatch_batch23_2026_08_17.md`) that actively reach operator visibility rather than starving behind unmerged PRs.
- [x] ✅ [REVIEW] P2. **GAP FOUND — blind spot to external GitHub state, follow-up filed below** (checkbox was stale,
      content already fully answered; flipped 2026-08-20). Audit `escalation-queue-reconciler`
      (`install-escalation-queue-reconciler-timer.sh`, `/escalation-queue-reconcile` skill) — same 4 checks; note this
      job watches OTHER jobs' escalation health, so also check whether IT would have caught the plan_reconciler
      PR-backlog problem itself, and if not, why not (is there a gap in what it watches worth folding into that skill
      separately).

      - **Audit Findings**:
        1. **Sharding shape**: Non-sharded. Polls the centralized active escalation state (`GET /api/escalations/active`) in a single pass across the corpus. (Citation: `agent-orchestrator/scripts/install-escalation-queue-reconciler-timer.sh`, `unified-trading-pm/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` § Table row for `escalation-queue-reconciler.service`).
        2. **Measured run time**: Fires every 3 hours at :40 UTC. Common-case cheap path (Step 1: healthy queue) executes in seconds (<1 min worker time). Deep path has a generous timeout ceiling (`TimeoutStartSec=6000`, `curl --max-time 5950`). (Citation: `agent-orchestrator/scripts/install-escalation-queue-reconciler-timer.sh` lines 32–36, 182–186; `unified-trading-pm/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` § Table).
        3. **Review-branch/PR gate check**: No review-branch or GitHub PR gate. Fixes/findings produced by the worker ship directly via `bash scripts/quality-gates.sh --no-fix` and `quickmerge.sh --agent --files '<paths>'` to the integration branch (`live-defi-rollout`), avoiding the stuck-PR pattern that affected `plan_reconciler`. (Citation: `unified-trading-pm/cursor-configs/skills/escalation-queue-reconcile/SKILL.md` § Step 4).
        4. **Escalation resolution and archival trace**: Escalations surface via live `/blocked` questions (`POST /api/slots/$SLOT_ID/blocked`, skill Step 3) or durable issue docs (`plans/active/issues/`). Note that a historical defect (`server/escalation.py:_poll_wall_resolution`) previously caused non-PR wall types like `data_pipeline_failure` to falsely auto-close on unrelated QG-green events without worker dispatch, which was fixed in `agent-orchestrator@884a9bfe1`. (Citation: `unified-trading-pm/plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md`).
        5. **Cross-check against `plan_reconciler` PR-backlog problem**:
           - *Would it have caught the problem?* **No.**
           - *Why not?* `escalation-queue-reconciler` monitors internal orchestrator database escalation state (`GET /api/escalations/active`, `server/escalation.py`). Because `plan_reconciler` runs completed successfully (`lifecycle-complete`) without failing in the escalation queue or crashing the worker, no database escalation row was created for unmerged PRs. External GitHub pull requests (`plan_reconciler/agt-*`) are completely opaque to internal DB escalation monitoring.
           - *Identified gap worth folding into the skill*: A blind spot exists where internal orchestrator watchdogs inspect database and API states but fail to audit external Git/GitHub collaboration state (such as accumulation of unmerged PRs or stale review branches produced by scheduled jobs). Folding this into `/escalation-queue-reconcile` (or a dedicated audit check) would require querying GitHub for open PRs matching scheduled job branch patterns (`head:plan_reconciler`, etc.) older than a safe threshold (e.g., >24h), ensuring stranded PR backlogs trigger alerts or issue records.
- [x] ✅ [REVIEW] P2. **HEALTHY — no gap found.** Audit `na-eligibility-auditor`
      (`install-na-eligibility-auditor-timer.sh`, `/na-eligibility-audit` skill) — same 4 checks (checkbox was stale,
      content already fully answered; flipped 2026-08-20).
      * **1. Sharding shape**: Sharded into exactly 10 topic tranches (`ALL_TRANCHES=(cefi defi tradfi prediction sports cross-cutting ao ci infra ui)`) via `scripts/install-na-eligibility-auditor-timer.sh` (line 126). Dispatched in batches of up to `MAX_CONCURRENT_TRANCHES="4"` (configured in lines 70, 179) via POST requests to `/api/plan-health/dispatch` with `{"mode": "na_eligibility", "tranche": "<name>"}`.
      * **2. Measured run time**: Each tranche runs independently as a one-shot worker via `agents/na_eligibility_auditor.md`. Measured per-tranche runtimes range from a few minutes up to the 6-hour completion window (`TimeoutStartSec=21600`). Server-side duplicate dispatch protection (`_tranche_dispatch_gate`) ensures same-day same-tranche concurrent dispatches coalesce correctly.
      * **3. Review-gate check**: No review-branch/PR gate exists for this job (unlike `plan_reconciler`'s historical PR gate). As specified in `agents/na_eligibility_auditor.md` and `cursor-configs/skills/na-eligibility-audit/SKILL.md`, the worker executes its audit one-shot, flips `assigned_vm: NA → planning` in place or extracts per-todo items into satellite batches (`{topic}_satellite_ao_dispatch_batch{N}_{date}.md` + `_finalize`), and reports text summaries via `/done` evidence, bypassing any blocking PR queue. **Audit finding: No gap found** in review-gate checks — output does not get trapped in unmerged PRs; edits and extraction reports land directly in the PM repository.
      * **4. Resolution & escalation trace**: Successfully processes `assigned_vm: NA` documents, performing conflict checks before any reclassification or satellite extraction. Escalations and conflicts are explicitly parked as operator-decision-blocked within tranche report/findings (e.g., `unified-trading-pm/plans/active/issues/na_eligibility_audit_defi_blocks_2026_08_18.md`), ensuring operator visibility rather than starving behind unmerged PRs. **Audit finding: No gap found** in escalation-resolution trace — findings and blocked items are written directly to tracked PM issue docs which are correctly indexed by backlog generators and operator audits. Confidence is established by verifying direct PM issue commits and server-side gate logs (e.g. `_tranche_dispatch_gate` in `server/plan_health.py`).
- [x] ✅ [REVIEW] P1. **DONE 2026-08-20.** Synthesized Track B's 7 audits into
      `/plans/active/issues/ao_scheduled_jobs_health_audit_findings_2026_08_20.md` — one row per job (sharded y/n,
      measured run time, review-gate y/n, escalation health). **Headline: no job reproduces plan_reconciler's exact
      failure** — none route through a PR/review-branch gate at all, every one ships direct via `quickmerge.sh
      --agent --files`. Two smaller, differently-shaped gaps found and filed as follow-up todos in that doc rather
      than fixed inline (per this plan's own evidence-bar rule): (1) `context-scout`'s 83% reaped-stale rate + one
      stale `[OPERATOR]` tag whose blocking premise already expired but was never retagged; (2) `escalation-queue-reconciler`
      is structurally blind to external GitHub PR-backlog state (would not have caught plan_reconciler's own
      problem) — low-urgency since no job currently uses a review-branch pattern.

**Track B is now fully closed — all 8 todos done (7 job audits + this synthesis).** Both Track A and Track B are
complete; this plan is a candidate for archival per the plan-completion-and-archival-discipline SSOT.

## Progress Log

- **2026-08-20 (interactive session)**: Track B fully closed out. Flipped 5 stale checkboxes whose findings were
  already fully answered inline but never marked done (`ag-closeout-auditor`, `context-scout`, `docs-reconcile`,
  `escalation-queue-reconciler`, `na-eligibility-auditor`); audited the 2 never-touched jobs live —
  `cefi-mtds-smoke` turned out to be RETIRED 2026-08-15 (operator VM-cost/Tardis-contention decision, documented in
  the scheduled-jobs codex SSOT, confirmed by the installer script's absence from the repo), `cefi-reconciliation`
  confirmed healthy (regular findings 08-08/08-09/08-18/08-19, no review-gate, zero stuck `[OPERATOR]` tags); wrote
  the Track B synthesis doc (`ao_scheduled_jobs_health_audit_findings_2026_08_20.md`) with 2 filed follow-ups. Every
  Track A and Track B todo in this plan is now `[x]`.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **2026-08-09 (interactive session)**: plan authored following the operator's explicit "human plan" ruling on this
  exact scope. Track A's 25-PR list and Track B's 7-job list both pulled live from `gh pr list` / the installer-script
  directory listing this same session, immediately before authoring.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — first audit pass on this doc.
- **2026-08-16 (interactive session, operator directive)**: Track A's 26 todos flipped `[x]` after live verification
  (`gh pr list --state open --search "head:plan_reconciler"` returns zero; individual spot-checks on #1998/#2327/#2522/
  #2653 confirmed CLOSED) found all 25 PRs already terminal — this doc's own findings were STALE (the underlying work
  had already resolved, checkboxes just never flipped), not a live remaining backlog. Track B (7 job audits + synthesis,
  8 todos) remains genuinely open — this doc stays `active`, not archived. Discovered as part of a broader AO-corpus
  dedup audit that also confirmed via the live agent-orchestrator backlog (`check-ao-backlog-status.sh`) that this doc
  correctly shows zero live backlog rows (`assigned_vm: NA`, never ingested — matches its own frontmatter).
  Its own `source:` frontmatter and body state it was authored "following the operator's explicit 'human plan' ruling on
  this exact scope" — a citable dated ruling on citation alone. Independently, every open todo is genuine per-item human
  judgment (Track A: rebase-and-re-verify vs. close-as-superseded per PR, 25 individual calls; Track B: a 7-job
  reliability/escalation-health audit), not mechanical/bounded work.

- **context-scout 2026-08-15**: populated/refreshed context_scope (6 entries) — trimmed from 17 to the shared root-cause
  files (`plan_reconciler.md`, `regen_backlog_from_plan.py`, `scheduled_job_already_ran.py`), the scheduled-jobs codex
  SSOT, and the 2 related issue docs already in `related:`; dropped the 7 individual `install-<job>-timer.sh` scripts
  (each already named inline in its own Track B todo) plus the plan-reconcile skill doc, `operator_gated_options.py`,
  and the single-vm-architecture codex ref.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:152b32e9fcb7971e]: KEEP-NA, valid — Track A (25 PRs) fully closed; Track B's 7 remaining todos are a genuine per-job reliability/escalation-health audit requiring real judgment, under an explicit dated operator 'human plan' ruling on this exact scope.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
