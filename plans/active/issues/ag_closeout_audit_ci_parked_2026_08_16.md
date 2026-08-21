---
doc_type: issue
title: ag-closeout-audit ci delta report — 2026-08-16 (batch15 same-day delta, no batch16 yet)
summary: >-
  Scheduled ag_closeout_auditor run (2026-08-16, tranche=ci, slot 21, agt-114e5f). batch15 (25 todos) had just been
  drafted the same day by an interactive session, so this run delta-checked rather than re-running a fresh 51-agent
  Phase-1 sweep: cross-referenced the full 51-doc tranche inventory against batch13/batch13-finalize/batch15/
  batch15-finalize/the consolidated closeout, leaving 9 docs genuinely uncited by any of the 5. Classified all 9 via a
  9-agent Workflow. Found and fixed in-run: 2 of batch15's own todos (the pytest_timeout/github_actions_operator_gated
  line-cap splits) were stale on arrival — already shipped via unified-trading-pm@f835f7fcc4 ~53min before batch15 was
  drafted — flipped [x] with commit evidence, verified live. Of the 7 remaining orphan docs, all verdict
  orphaned_never_touched but none is currently AO-eligible enough to warrant drafting batch16 today: 1 has a genuinely
  bounded new item (ready for whenever batch16 next drafts), 4 are correctly self-tracked NA/operator-gated already
  (no new action needed), 1 needs pre-scoping before it's dispatchable, 1 is out of this skill's scope entirely
  (belongs to /plan-reconcile's own Step-4 continuation). Also found 2 asset_group mistags (both should drop `ci`,
  land on `infrastructure` alone) — not fixed here per the concurrent-sharded-worker safety rule.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ag-closeout-audit, parked, ci, orphan, mistag, delta-audit]
related:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/ci_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md,
    /plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md,
    /plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16_finalize.md,
    /plans/active/issues/ci_alert_failure_resolution_linkage_2026_08_16.md,
    /plans/active/issues/deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md,
    /plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md,
    /plans/active/issues/ff_pull_fleet_drift_rca_2026_08_11.md,
    /plans/active/issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-08-16
parent_epic: ci_master
assigned_vm: NA
priority: P3
last_updated: 2026-08-21
source: >-
  ag_closeout_auditor scheduled run 2026-08-16 (tranche=ci, slot 21, DISPATCH_ID=agt-114e5f).
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
supersedes: ag_closeout_audit_ci_parked_2026_08_10
context_scope: [/cursor-configs/skills/ag-closeout-audit/SKILL.md, /plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md, /plans/archive/2026_08/issues/ag_closeout_audit_ci_parked_2026_08_10.md, /plans/archive/issues/promote_pr_non_supersession_after_greeks_service_fix_2026_08_18.md]
---

# ag-closeout-audit ci delta report — 2026-08-16

> **Supersedes `ag_closeout_audit_ci_parked_2026_08_10.md`** (archived) in doc-chain lineage only — note the method
> basis differs from that immediate predecessor: batches 11-15 shipped/archived in the 6-day gap between the two
> reports, so this run delta-checks against batch15's own same-day survey, not against the 2026-08-10 report's
> candidate list.
>
> Additional archived historical context (cited as evidence, not routed to as live pointers, per the archival ritual —
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` step 5): the predecessor report itself lives at
> `plans/archive/2026_08/issues/ag_closeout_audit_ci_parked_2026_08_10.md`; the gcloud WIF-poisoning operator ruling at
> `plans/archive/2026_08/issues/operator_ruling_record_gcloud_wif_poisoning_2026_08_08.md`; two plan-reconciler CI
> findings sweeps at `plans/archive/issues/plan_reconciler_ci_late_findings_2026_08_06.md` and
> `plans/archive/issues/plan_reconciler_findings_ci_2026_08_16.md`; and the placeholder-prettier-mangling incident at
> `plans/archive/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md`.

## Method note — delta audit, not a fresh 51-agent Workflow sweep

`ci_satellite_ao_dispatch_batch15_2026_08_16.md` was drafted **the same day**, in an interactive session, from its own
2-agent follow-up survey of the 39 CI-tagged docs still open after batch14 shipped (25 fresh todos, 0 done, plus a
14-item Deferred section). Re-running a full fresh Phase-1 sweep immediately after would just re-ask the same ~39 docs
the same questions with the same answers. Instead:

1. Ran `python3 scripts/plan-hygiene/generate_tranche_doc_inventory.py --tranche ci` → **51 total members**.
2. Cross-referenced every member's basename against the 5 current covering docs (`ci_consolidated_closeout_2026_07_25`,
   `ci_satellite_ao_dispatch_batch13_2026_08_13` + its finalize, `ci_satellite_ao_dispatch_batch15_2026_08_16` + its
   finalize) via full-text grep, not just `Source:` lines.
3. Left **9 genuinely uncited docs** (7 orphan candidates + 2 dual-tagged mistag checks) — classified all 9 via a
   9-agent `Workflow` using the standard Phase-1 schema (full end-to-end read, dated-section-override check,
   checkbox-vs-prose enumeration, coverage-bar check against the 4 `assigned_vm:planning`+`status:active` covering
   docs).
4. Ran the Orthogonality dual-tag grep against the full 9-tranche peer set (not just the 5 original AGs) as part of
   step 2 — surfaced the 2 mistags below.

## Phase 0 — covering-plan set

- `ci_consolidated_closeout_2026_07_25.md` — `assigned_vm: NA`, pure reachability digest, not a dispatch vehicle.
- `ci_satellite_ao_dispatch_batch13_2026_08_13.md` (+ finalize) — **23/24 done**, 1 open ([CODE] P2, bare-VM CI
  bootstrap proof, IN PROGRESS by slot 15/infra since 2026-08-14, VM terminated mid-run, resume point documented
  in-doc). Finalize plan correctly still gated (batch not yet at 0 open).
- `ci_satellite_ao_dispatch_batch15_2026_08_16.md` (+ finalize) — drafted today, **now 25/25 done in this run's
  bookkeeping sense**: originally 0/25 done, this run flipped 2 line-cap-split todos to done as stale-on-arrival
  (see below), leaving 23 genuinely unworked. `status: active`, already operator-approved per batch14 precedent
  (source note in frontmatter).
- All 11 prior batches (1-12, 14) are archived — confirmed coverage, not a gap.

## Resolved this run — 2 stale todos in batch15, fixed in-place

`ci_satellite_ao_dispatch_batch15_2026_08_16.md`'s two `[DOC] P1` line-cap-split todos (splitting
`pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` and
`plans/active/github_actions_operator_gated_followups_2026_07_17.md`) cited
`plan_reconciler_findings_ci_2026_08_10.md` as Source. Verified live: both splits were **already shipped** via
`unified-trading-pm@f835f7fcc4` (slot-9, dispatch `agt-4f7ad9`, "ci-tranche line-cap splits under Trust Mode",
committed 2026-08-16T18:12:10Z) — **~53 minutes before batch15 was drafted** (2026-08-16T19:05:03Z). batch15's authors
cited the older `..._2026_08_10.md` doc and missed that the newer `..._2026_08_16.md` doc's own Phase -1 had already
completed this exact work. Confirmed via `wc -l`: `github_actions_operator_gated_followups_2026_07_17.md` is now
738L (was 1006L), `pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` is now 145L (was 1013L) — both
comfortably under the 1000L cap. Flipped both checkboxes `[x]` in `ci_satellite_ao_dispatch_batch15_2026_08_16.md`
with commit-sha evidence, per SKILL.md's "mechanical corpus hygiene is fixed in-run, never parked" rule. This is a
real AO-worker-hours saving: without this fix, whichever worker next claimed those 2 todos would have redone
already-shipped work.

## Phase 1 — the 9-doc delta classification

All 9 read end-to-end (dated-section-override check + checkbox/prose enumeration + coverage-bar check against the 4
live covering docs). Full per-doc reasoning in the Workflow journal
(`wf_298fe193-3e7`); summarized dispositions below.

### 7 orphan candidates — all verdict `orphaned_never_touched`, none warrant drafting batch16 today

- **`ci_alert_failure_resolution_linkage_2026_08_16.md`** — filed today, same day as batch15, plausibly just after its
  survey cutoff. 2 open items: (1) bounded/AO-eligible — extend the `streak_start_sha` failure-resolution linkage to
  `ldr-to-main-promote.yml`'s drain-bot "closed as superseded" INFO messages; (2) a P3 scoping question for whether
  `ldr-ci-monitor.yml`'s RED→GREEN posts should also cite it. **Ready to extract into batch16 whenever one is next
  drafted** — conflict-checked clear, no overlap with any live todo.
- **`deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md`** — 1 open P3 item (why does
  `unified_trading_library`'s dual global-event-state architecture leak on CI specifically), already independently
  verdicted KEEP-NA valid by na-eligibility-audit (2026-08-07) — genuine open-ended investigation, fails the
  AO-eligibility bounded-outcome bar. **No new action** — doc's own NA self-classification is correct and current.
- **`operator_ruling_record_gcloud_wif_poisoning_2026_08_08.md`** — RESOLVED 2026-08-19: operator confirmed the
  transcribed ruling accurate (interactive session), doc's `[OPERATOR]` todo flipped `[x]` and the doc archived to
  `/plans/archive/2026_08/issues/operator_ruling_record_gcloud_wif_poisoning_2026_08_08.md`
  (unified-trading-pm@3e477497254f). No action remains here.
- **`plan_reconciler_ci_late_findings_2026_08_06.md`** — **RESOLVED + ARCHIVED 2026-08-16 (plan_reconciler Phase -1)**:
  the 14th (last-open) item, a title/summary editorial rewrite, was closed via a trust-mode won't-fix ruling
  (unanimous across 4 independent audits); doc now at `/plans/archive/issues/plan_reconciler_ci_late_findings_2026_08_06.md`.
- **`plan_reconciler_findings_ci_2026_08_16.md`** — filed today by a `/plan-reconcile` dispatch (slot 9, `agt-4f7ad9`)
  as a candidate ledger awaiting its own not-yet-run STEP-4 adversarial verification (9 flip candidates, 8
  contradictions, 11 codex-drift findings, 4 archive candidates, misc hygiene — zero checkboxes, all prose-form).
  **Out of this skill's scope by design** — SKILL.md is explicit that this skill is not `/plan-reconcile` and doesn't
  duplicate its verification work. This doc's remaining work is "run `/plan-reconcile`'s own Step 4 on it", not
  CI-engineering work a satellite batch could pick up. Flagging for whoever runs `/plan-reconcile` next, not drafting
  a ci todo for it.
- **`workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md`** — 2 open items (an atomic-rollout design
  question, a standing conditional runbook), independently reconfirmed KEEP-NA by **six** separate na-eligibility-audit
  passes (2026-08-01, 08-02, 08-06 ×2, 08-07, 08-09, 08-10). **Escalating rather than re-confirming a 7th time** — see
  Todos below.
- **`workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md`** — 1 open item (P2, investigate
  why a promote-PR wasn't superseded after a specific merge — two unconfirmed hypotheses, no done-when).
  na-eligibility-audit already recommended (2026-08-08/09) splitting this into its own properly-scoped doc or
  resolving interactively; never acted on. **Formalizing that recommendation as a todo below** rather than leaving it
  as a 3rd-run prose reconfirmation.

### 2 dual-tag mistags found — NOT fixed here (wrong owning tranche)

Both confirmed via full-content read + `parent_epic` cross-check against sibling docs. Per SKILL.md's concurrent-
sharded-worker safety rule, a doc's write belongs to its actual owning tranche, not to `ci` just because `ci` happens
to be one of its two current tags — so these are reported, not edited, here.

- **`ff_pull_fleet_drift_rca_2026_08_11.md`** — currently `[infrastructure, ci]`. Content is 100%
  per-tab-worktrees FF-pull/starvation-detection subsystem (`slot-cron-ff-pull.sh`, `ff-starvation-detect.sh`,
  `resume_lifecycle.py`'s clean-slot invariant) — zero genuine CI/CD-pipeline-mechanics content; the one
  `.github/workflows/semver-agent.yml` mention is cited only as inert local dirt blocking a fast-forward, never as CI
  behavior. `parent_epic: infrastructure_master` corroborates. **Recommend: drop `ci`, land on `[infrastructure]`
  alone.**
- **`todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md`** — currently `[ci, ao]`. **Note:
  this contradicts the 2026-08-10 `ci` report's own Finding, which called it `ao`-owned via `parent_epic` alone**
  (`agent_operating_framework_master`). This run's classification read the actual content (a PM plan-corpus
  authoring-convention contradiction — `task_template.md`'s CANCELLED/SUPERSEDED marker convention vs.
  `scripts/plan-hygiene/check_todo_regression.sh`'s checkbox-count invariant — touches neither real CI-pipeline
  mechanics nor real AO runtime/dispatch mechanics) and found two directly-analogous sibling docs under the *same*
  `parent_epic: agent_operating_framework_master` that are tagged `asset_group: [infrastructure]` alone
  (`plan_quality_four_line_defense_architecture_2026_07_23.md`, `reference_path_convention_2026_07_23.md`) —
  establishing that this epic does not cleanly imply `ao` at the individual-issue-doc granularity. **This tag has now
  sat unresolved for 6+ days** because both `ci` and `ao` correctly declined to write a tag that isn't theirs, and
  neither tranche apparently owns `infrastructure`'s classification of it either. Flagging as overdue — see Todos.

## Phase 2 — synthesis

**51 total tranche members.** 2 self-dispatched (`assigned_vm: planning`, cover themselves — unrelated docs, not in
the delta set). 2 batch13/batch15-mechanism docs + their 2 finalize twins (not candidates). ~34 already covered by
batch13's 3 Sources + batch15's 5 Sources + Deferred-section citations (unchanged from batch15's own survey, not
re-verified line-by-line this run — trusting the same-day sweep). **9 delta docs classified fresh**: 7 orphaned
(all `orphaned_never_touched`, 4 already-correctly-NA and needing no new action, 1 out-of-skill-scope, 2 genuinely
actionable — see Todos), 2 mistags (not `ci`'s to fix). **2 stale batch15 todos found and fixed in-run** (see above).
**0 items rose to `BLOCKED-OPERATOR-DECISION`** in the Phase-3 conflict-check sense — the one true operator-facing ask
(`operator_ruling_record_gcloud_wif_poisoning`) is already correctly tagged in its own doc, just relayed here.

## Phase 3 — no batch16 drafted this run

Only one delta doc (`ci_alert_failure_resolution_linkage_2026_08_16.md`, todo 1) is currently bounded/AO-eligible.
Drafting a whole new `batch16` + gated finalize pair for a single item, while `batch15`'s own 23 still-unworked todos
sit completely undispatched (this run only touched 2 of them, both via stale-checkbox reconciliation, not actual
work), would front-run the iterative-drain model SKILL.md describes rather than serve it. **Recommendation: fold this
one item into `batch16` once `batch15` has meaningfully drained, or let the operator decide to add it to `batch15`
directly if they want it sooner** — noting it here satisfies the "every genuine finding gets a durable, not just
chat-ephemeral, home" rule regardless.

## Todos

- [x] [OPERATOR] P2. ✅ **Confirm or correct the transcribed gcloud-WIF-poisoning ruling** at
      `/plans/archive/2026_08/issues/operator_ruling_record_gcloud_wif_poisoning_2026_08_08.md` line 77 — operator
      confirmed accurate as transcribed 2026-08-19 (interactive session); doc's own checkbox flipped and archived
      (unified-trading-pm@3e477497254f). No correction needed.
- [ ] [OPERATOR] P3. BLOCKED-OPERATOR-DECISION (named 2026-08-21, D32 ruling: "Provide the ruling — 6 audit passes
      with no forward decision is pure churn either way" — the ruling adopted is that the operator must actually
      decide, not that a design answer was itself supplied). **Rule on
      `workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md`'s 2 open items** (atomic multi-repo
      rollout mechanism design; standing git-log-first runbook worth formalizing or not) — reconfirmed KEEP-NA by 6
      separate na-eligibility-audit passes since 2026-08-01 with no scoping decision ever made. Done when: operator
      rules, or the doc is explicitly marked won't-fix. Ledger: D32,
      /plans/active/issues_corpus_completion_dispatch_2026_08_21.md.
- [x] ✅ [DOCS] P2. **DONE 2026-08-18 (na-eligibility-audit, ci tranche).** Extracted into
      `plans/archive/issues/promote_pr_non_supersession_after_greeks_service_fix_2026_08_18.md` (content carried
      forward verbatim; the issue was later archived after a live re-check). Source doc
      (`workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md`) checkbox flipped citing the
      extraction; it now has 0 open todos. Was: **Pre-scope `workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md`'s
      surviving P2 item** (investigate why a promote-PR wasn't superseded after greeks-service@f5a63a8 landed —
      2 unconfirmed hypotheses, no done-when) — split into its own bounded issue doc with a concrete done-when, or
      resolve the judgment call interactively. na-eligibility-audit recommended this exact fix on 2026-08-08/09; never
      executed. Done when: either a new properly-scoped doc exists with a checkable done-when, or the investigation is
      resolved directly with cited evidence.
- [ ] [DOC] P3. **Retag `ff_pull_fleet_drift_rca_2026_08_11.md`** from `asset_group: [infrastructure, ci]` to
      `[infrastructure]` (drop `ci`) — confirmed mistag, zero genuine CI-pipeline-mechanics content. NOT this tranche's
      to execute directly (concurrent-sharded-worker safety rule — an `infra`-tranche run may be mid-classification on
      the same file); flagged for `infra`'s own next run, a `/na-eligibility-audit`, or a corpus-hygiene sweep. Done
      when: tag is single-value `[infrastructure]`, `check_ag_closeout_linkage.py` re-run clean.
- [ ] [DOC] P2. **Resolve the 6-day-stuck `[ci, ao]` dual-tag on
      `todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md`** — the 2026-08-10 `ci` report
      called it `ao`-owned via `parent_epic` alone; this run's content-based read (plus 2 sibling docs under the same
      epic tagged `[infrastructure]` alone) points at `[infrastructure]` instead. Neither `ci` nor `ao` has written a
      fix in 6+ days because each correctly declines to guess a tag that isn't theirs — this needs someone to actually
      decide rather than a 3rd tranche re-parking it again. Recommend routing through a corpus-hygiene sweep (same
      mechanism the 2026-08-10 report's own 4-doc `ci`/`infra` mistag eventually used:
      `meta_plan_corpus_hygiene_ao_dispatch_batchN`) rather than waiting on `ci`/`ao`/`infra` to each individually
      notice it again. Done when: tag reflects one specific tranche (or a deliberate `cross-cutting` call), re-verified
      via `check_ag_closeout_linkage.py`.
- [x] ✅ [DOCS] P3. **Extract `ci_alert_failure_resolution_linkage_2026_08_16.md`'s todo 1** (extend `streak_start_sha`
      failure-resolution linkage to `ldr-to-main-promote.yml`'s drain-bot "closed as superseded" INFO messages) into
      the next `ci_satellite_ao_dispatch_batchN` once `batch15`'s 23 remaining todos have meaningfully drained —
      conflict-checked clear this run, ready to extract without further triage. Done when: extracted into a batch
      todo citing this doc as Source, or the operator explicitly asks for it sooner. **DONE 2026-08-21
      (na-eligibility-audit, ci tranche wave 2)** — `batch15` re-checked: 11 open / 14 done (meaningfully drained
      from the 23-open count at this todo's filing). Extracted into `ci_satellite_ao_dispatch_batch16_2026_08_21.md`
      todo 3, citing this doc's conflict-check per this todo's own instruction. Note: the target doc numbers this
      item "todo 2" in its own body (a `[x]`-closed todo 1 precedes it, shipped 2026-08-16) — same content either
      way, extracted correctly by text match, not by number.

## Progress Log

- **2026-08-16 (scheduled `ag_closeout_auditor`, slot 21, `agt-114e5f`)**: Delta-only audit per the Method note above
  — `batch15` was drafted the same day by an interactive session, so a fresh 51-agent Phase-1 sweep would have
  re-asked already-answered questions. Found + fixed in-run: 2 of `batch15`'s own line-cap-split todos were already
  shipped via `unified-trading-pm@f835f7fcc4` before `batch15` was even drafted (stale Source citation to a superseded
  predecessor doc) — flipped `[x]` with commit evidence. Classified the 9 genuinely-uncited delta docs via a 9-agent
  Workflow: 7 orphans (4 already-correctly-NA needing no new action, 1 out-of-skill-scope, 2 genuinely actionable —
  now tracked as todos above) + 2 asset_group mistags (both belong to `infrastructure`, flagged not fixed). No
  `batch16` drafted — only 1 delta item is currently AO-eligible, and `batch15`'s own 23 unworked todos should drain
  first per the iterative-drain model. 5 todos filed above (2 operator-facing, 3 mechanical/scoping).

**Parked-findings reconciliation**: 7 orphan classifications + 2 mistag findings = 9 delta docs classified this run.
5 converted to formal `- [ ]` todos above (2 already-correctly-NA docs and 1 out-of-scope doc needed no new todo —
correctly re-confirmed, not silently dropped, per the "informational finding is not a todo" rule). **9 findings
generated this run, 9 accounted for (5 as todos + 4 as explicit no-new-action re-confirmations documented above) —
balanced.**
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-18** (ci tranche): KEEP-NA, valid — the 4 no-new-action items (gcloud-WIF ruling,
  workflow_template_drift_repeated design question, plan_reconciler_findings_ci_2026_08_16 out-of-scope, the 2
  cross-tranche mistag flags) all independently re-confirmed unchanged on direct read. Todos item 3 (pre-scope
  workflow_template_runs_on_placeholder) executed this run — see the flipped checkbox above. The remaining items
  (2 [OPERATOR], 2 [DOC] cross-tranche retags not this tranche's to execute, 1 [DOCS] extraction still gated on
  batch15 draining) are unchanged and correctly still open.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)

**2026-08-21 — ruling D32 (Workflow-drift design items)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
AUTONOMOUS_AGENT_RULES rule 2): Provide the ruling — 6 audit passes with no forward decision is pure churn either
way. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.

**na-eligibility-audit 2026-08-21** (ci tranche wave 2): KEEP-NA, valid — 5 open items re-read end-to-end. Item
(extract ci_alert linkage) executed this pass, closed above with citation to `ci_satellite_ao_dispatch_batch16_
2026_08_21.md`. The 2 `[OPERATOR]` P3 items (rule on `workflow_template_drift_repeated...`'s 2 open design
questions; the concurrent-sharded-worker retag items) remain genuinely operator-gated/cross-tranche-not-mine-to-
execute per their own explicit text. The 2 `[DOC]` cross-tranche retags stay correctly un-executed by this tranche
(concurrent-sharded-worker safety rule — `infra` tranche owns one, a corpus-hygiene sweep owns the other). No
`assigned_vm` change.
