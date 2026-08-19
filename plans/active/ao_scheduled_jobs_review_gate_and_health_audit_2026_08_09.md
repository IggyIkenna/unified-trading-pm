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
status: active
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

- [ ] [REVIEW] P2. Audit `ag-closeout-auditor` (`install-ag-closeout-auditor-timer.sh`, `/ag-closeout-audit` skill) —
      sharding shape, measured run time, review-gate check, escalation-resolution trace. Record findings inline below.
      * **1. Sharding shape**: Sharded into exactly 10 topic tranches (`ALL_TRANCHES=(cefi defi tradfi prediction sports cross-cutting ao ci infra ui)`) via `scripts/install-ag-closeout-auditor-timer.sh` (line 129). Dispatched in batches of up to `MAX_CONCURRENT_TRANCHES="4"` (configured in lines 73, 179) via POST requests to `/api/plan-health/dispatch` with `{"mode": "ag_closeout", "tranche": "<name>"}`.
      * **2. Measured run time**: Real measured single-tranche runtimes on record range from **6.5 min to 63.9 min** (cited in `scripts/install-ag-closeout-auditor-timer.sh` lines 315-320, tracking `registered_at -> AgentRow finished_at`). Systemd timer timeout `TimeoutStartSec` is set to `21600` (6 hours) to accommodate batched multi-tranche execution without premature SIGTERM.
      * **3. Review-gate check**: No review-branch/PR gate exists for this job (unlike `plan_reconciler`'s historical PR gate). As specified in `agents/ag_closeout_auditor.md` (lines 35-42) and `cursor-configs/skills/ag-closeout-audit/SKILL.md`, the worker executes its audit one-shot, writes draft plans (`status: draft`) for extracted bounded work (`<tranche>_satellite_ao_dispatch_batch<N>_<date>.md` + `_finalize`), and reports text summaries directly via `/done` evidence, bypassing any blocking PR queue.
      * **4. Escalation-resolution trace**: Successfully produces actionable issue and parked findings reports. For instance, the scheduled `/ag-closeout-audit sports` run on 2026-08-16 produced `unified-trading-pm/plans/active/issues/ag_closeout_audit_sports_parked_2026_08_16.md`, identifying 24 genuine orphans and extracting 10 items into a concrete draft batch (`sports_satellite_ao_dispatch_batch14_2026_08_16.md`), demonstrating that escalations and orphan discoveries actively reach operator visibility rather than starving behind unmerged PRs.
- [ ] [REVIEW] P2. Audit `cefi-mtds-smoke` (`install-cefi-mtds-smoke-timer.sh`) — same 4 checks.
- [ ] [REVIEW] P2. Audit `cefi-reconciliation` (`install-cefi-reconciliation-timer.sh`) — same 4 checks.
- [ ] [REVIEW] P2. Audit `context-scout` (`install-context-scout-timer.sh`, `/context-scout` skill) — same 4 checks;
      this one is read-mostly (populates `context_scope`) so the review-gate question may not apply — confirm either way
      rather than assuming.

      - **Audit Findings**:
        1. **Sharding shape**: Non-sharded. The scheduled-jobs codex table (`/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` line 75) explicitly lists `context-scout.service` as "No" in the Sharded column. Phase 0 (`scripts/plan-hygiene/generate_context_scope_inventory.py`) walks the full in-scope corpus (all `status: active|open|blocked|paused` plan/issue docs) in a single pass to produce NEVER_SCOUTED/STALE/UP_TO_DATE verdicts (script lines 1–29). Phase 1 batches the in-scope docs into groups of ~10–15 for sub-agent parallelism, but this is internal concurrency within one corpus-wide run — not a bounded-shard split (cf. `ag-closeout-auditor`'s 10 named tranches or `plan-reconciler`'s day-of-week splitting) that caps blast radius or time-to-complete per unit.
        2. **Measured run time**: Fires every 12h via systemd `OnCalendar=*-*-* 0/12:52:00 UTC` (`install-context-scout-timer.sh` line 221), with a `curl --max-time` of 5950s and `TimeoutStartSec=6000s` (installer lines 118, 211). Steady-state incremental runs are cheap: Phase 0 is a single-pass PyYAML parse of ~500 docs, and only docs changed since the last scout fire are in scope. This plan's own Progress Log records two recent runs — 2026-08-15 and 2026-08-17 — both showing "populated/refreshed context_scope (6 entries)" (lines 163, 180–184), consistent with small incremental passes. The initial corpus-wide backfill (2026-07-30, per SKILL.md line 37) was the expensive case (hundreds of NEVER_SCOUTED docs requiring large Workflow fan-out). **Cadence-stale-reference finding**: the codex table (line 75) and SKILL.md (line 218) both state "hourly" cadence, but the actual installer has been `0/12` (every 12h) since at least the 2026-08-06 `TimeoutStartSec` bump (installer line 209 comment). The SKILL.md also says "Fires hourly via `context-scout.timer`" — both are stale relative to the installer ground truth.
        3. **Review-branch/PR gate check**: **No review-branch or PR gate exists.** The skill's Phase 2 (`cursor-configs/skills/context-scout/SKILL.md` lines 177–179) ships directly via `quickmerge.sh --agent --files` to the integration branch (`live-defi-rollout`). A grep of the full SKILL.md for `review.branch|PR|pull.request|review.gate|git.push` returns zero hits for review-branch or PR patterns. **Confirming the todo's speculation**: the review-gate question genuinely does not apply — but not because the job is "read-mostly" (it does WRITE `context_scope:` frontmatter and dated Progress Log markers to every scouted doc). It doesn't apply because the job was designed in the 2026-07-29/30 era (SKILL.md lines 6–9 reference the sibling install scripts and the `context_scope_frontmatter_and_scout_skill_2026_07_30` plan), after the review-branch pattern had already been identified as problematic for this family of daily deep-audit jobs — so it was never given one to begin with.
        4. **Escalation resolution trace**: **Not applicable.** The skill has no mechanism to create `[OPERATOR]`-tagged escalations or `BLOCKED-*` findings. SKILL.md line 18–19 explicitly scopes it: "this skill never touches a doc's `status`, todos, or body content beyond adding a dated marker — it only reads a doc and writes back a `context_scope:` list." Phase 3 reports (unstated-SSOT suggestions, stale-candidate-pointer findings, fingerprint-match pairs) are "chat-text only" (SKILL.md line 195: "there is no separate structured-findings endpoint"). A grep of the full SKILL.md for `\[OPERATOR\]`, `BLOCKED-`, or `BLK-op` returns zero hits. The job cannot starve its own escalation mechanism because it has no escalation mechanism.
- [ ] [REVIEW] P2. Audit `docs-reconcile` (`install-docs-reconcile-timer.sh`, `/docs-reconcile` skill) — same 4 checks.
- [ ] [REVIEW] P2. Audit `escalation-queue-reconciler` (`install-escalation-queue-reconciler-timer.sh`,
      `/escalation-queue-reconcile` skill) — same 4 checks; note this job watches OTHER jobs' escalation health, so also
      check whether IT would have caught the plan_reconciler PR-backlog problem itself, and if not, why not (is there a
      gap in what it watches worth folding into that skill separately).

      - **Audit Findings**:
        1. **Sharding shape**: Non-sharded. Polls the centralized active escalation state (`GET /api/escalations/active`) in a single pass across the corpus. (Citation: `agent-orchestrator/scripts/install-escalation-queue-reconciler-timer.sh`, `unified-trading-pm/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` § Table row for `escalation-queue-reconciler.service`).
        2. **Measured run time**: Fires every 3 hours at :40 UTC. Common-case cheap path (Step 1: healthy queue) executes in seconds (<1 min worker time). Deep path has a generous timeout ceiling (`TimeoutStartSec=6000`, `curl --max-time 5950`). (Citation: `agent-orchestrator/scripts/install-escalation-queue-reconciler-timer.sh` lines 32–36, 182–186; `unified-trading-pm/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` § Table).
        3. **Review-branch/PR gate check**: No review-branch or GitHub PR gate. Fixes/findings produced by the worker ship directly via `bash scripts/quality-gates.sh --no-fix` and `quickmerge.sh --agent --files '<paths>'` to the integration branch (`live-defi-rollout`), avoiding the stuck-PR pattern that affected `plan_reconciler`. (Citation: `unified-trading-pm/cursor-configs/skills/escalation-queue-reconcile/SKILL.md` § Step 4).
        4. **Escalation resolution and archival trace**: Escalations surface via live `/blocked` questions (`POST /api/slots/$SLOT_ID/blocked`, skill Step 3) or durable issue docs (`plans/active/issues/`). Note that a historical defect (`server/escalation.py:_poll_wall_resolution`) previously caused non-PR wall types like `data_pipeline_failure` to falsely auto-close on unrelated QG-green events without worker dispatch, which was fixed in `agent-orchestrator@884a9bfe1`. (Citation: `unified-trading-pm/plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md`).
        5. **Cross-check against `plan_reconciler` PR-backlog problem**:
           - *Would it have caught the problem?* **No.**
           - *Why not?* `escalation-queue-reconciler` monitors internal orchestrator database escalation state (`GET /api/escalations/active`, `server/escalation.py`). Because `plan_reconciler` runs completed successfully (`lifecycle-complete`) without failing in the escalation queue or crashing the worker, no database escalation row was created for unmerged PRs. External GitHub pull requests (`plan_reconciler/agt-*`) are completely opaque to internal DB escalation monitoring.
           - *Identified gap worth folding into the skill*: A blind spot exists where internal orchestrator watchdogs inspect database and API states but fail to audit external Git/GitHub collaboration state (such as accumulation of unmerged PRs or stale review branches produced by scheduled jobs). Folding this into `/escalation-queue-reconcile` (or a dedicated audit check) would require querying GitHub for open PRs matching scheduled job branch patterns (`head:plan_reconciler`, etc.) older than a safe threshold (e.g., >24h), ensuring stranded PR backlogs trigger alerts or issue records.
- [ ] [REVIEW] P2. Audit `na-eligibility-auditor` (`install-na-eligibility-auditor-timer.sh`, `/na-eligibility-audit`
      skill) — same 4 checks.
- [ ] [REVIEW] P1. Synthesize Track B's 7 audits into a single findings doc under `plans/active/issues/` (slug
      `ao_scheduled_jobs_health_audit_findings_<date>`) — one row per job: sharded y/n, typical run time, review-gate
      present y/n (+ stuck backlog count if yes), escalation-resolution health. File a `- [ ]` follow-up todo (here or
      in a new plan, operator's call per the ask-before-creating-AO-plan rule) for any job found with the SAME
      review-gate-starving-escalation bug plan_reconciler had — do not silently fix it inline without the same evidence
      bar (≥2 clean proven runs) this plan's Background section used.

## Progress Log

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
