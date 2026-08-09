---
doc_type: plan
title: CI satellite AO batch 7 — seventh AO-dispatch extraction for the ci tranche (infrastructure_master group)
summary: >-
  Manual satellite-batch-extraction pass over the `ci` tranche's 15 docs that today's `/ag-closeout-audit ci` run
  (2026-08-08, `issues/ag_closeout_audit_ci_parked_2026_08_08.md`) did NOT whole-doc-reclassify to `assigned_vm:
  planning` — mirrors the `/ag-closeout-audit` satellite-batch-extraction pattern, applied by hand against the same 15
  candidates. A full per-doc read found the corpus heavily pre-mined: 6 prior `ci` satellite batches, 7+ rounds of
  `na-eligibility-audit`, and today's own 42-agent Phase-1 sweep already extracted or explicitly gated nearly every open
  item across all 15 docs (dependency-blocked, operator-sign-off-pending, live-incident-too-hot, or already claimed by
  an active sibling batch — see this doc's own Progress Log for the full per-doc disposition ledger). Exactly ONE
  genuinely-uncovered, bounded, worker-determinable item surfaced under this `parent_epic` — a 3-doc codex sync now
  unblocked by the 2026-08-08 CI-VM downsize + public-repo-migration completing. The sibling `assigned_role: devops`
  frontmatter-hygiene item (different `parent_epic`) is drafted separately as batch 8 per the parent_epic-grouping rule.
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-7, satellite-docs, codex-sync]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /plans/active/ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch7_finalize_2026_08_09.md,
    /plans/active/ci_satellite_ao_dispatch_batch8_2026_08_09.md,
    /plans/active/ci_satellite_ao_dispatch_batch8_finalize_2026_08_09.md,
    /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md,
    /plans/active/issues/ag_closeout_audit_ci_parked_2026_08_08.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
assigned_role: cicd
effort: high
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md,
    /codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md,
    /codex/07-security/self-hosted-runner-security-posture.md,
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Manual satellite-batch-extraction pass, run 2026-08-09, against the exact 15 `ci`-tranche candidate docs today's
  `/ag-closeout-audit ci` run left un-reclassified (`issues/ag_closeout_audit_ci_parked_2026_08_08.md`). Task: mirror
  the skill's own extraction pattern by hand — pull bounded, worker-determinable sub-items out of docs that as a WHOLE
  did not qualify for reclassification, leaving genuinely-gated items behind. Full per-doc disposition in the Progress
  Log below.
---

# CI satellite AO batch 7 (infrastructure_master group)

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** The single todo's 3-codex-doc sync shipped (`unified-trading-pm@d938e9275`),
> every fact live-verified against AWS at execution time (not copied from the source audit doc). Archived in the same
> session per the archival HARD RULE (a plan whose only todo just went `[x]` is a zero-dispatchable doc if left `active`
> — `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). Finalize plan
> `ci_satellite_ao_dispatch_batch7_finalize_2026_08_09.md` (source-doc reconciliation + this archival) completed and
> archived alongside. Successor: none.

> **Why this plan exists.** This is a deliberately THIN batch — the honest result of re-auditing 15 already
> heavily-mined docs. `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (42/43 done), `..._batch4_2026_07_31.md` (8/9
> done), `..._batch5_2026_08_02.md` (5/6 done), and `..._batch6_2026_08_08.md` (drafted the same day as this batch's
> source candidate list) between them have already extracted essentially every bounded item these 15 docs ever carried.
> This batch carries the ONE item that survived a fresh per-doc read: a 3-codex-doc sync that was blocked on
> infrastructure state (the CI-VM downsize + public-repo migration) that only finished completing 2026-08-07/08.

## Todos

- [x] ✅ 1. [DOC] P2. **Sync 3 stale CI-infrastructure codex docs to the now-current dedicated-CI-VM state.** All three
      describe an infrastructure topology that changed materially in the last 3 weeks and is now stable enough to
      document for real (verify every fact against LIVE state before writing — do not copy the source doc's numbers
      blind, it is itself several days old): (a) `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md` —
      full rewrite: self-hosted runners no longer live on the planning/orchestrator VM at all; they moved to a dedicated
      CI VM (`i-042a6332509482556`, resized 2026-08-08 to `m8i.2xlarge` / 8 vCPU / 32 GB, volume `vol-03880fe9bf1ea805b`
      at 12,000 IOPS / 312 MB/s) via the `POOL_TAG`-parameterized `setup-glue-runners.sh` multi-tenancy mechanism
      (`unified-trading-pm@30872b269`, 2026-07-27) — this doc's relaunch/reinstall procedure must target the CI VM, not
      the planning VM. (b) `/codex/07-security/self-hosted-runner-security-posture.md` — update to describe the CURRENT
      threat model: the dedicated CI VM (not the shared orchestrator VM), the current self-hosted repo set (re-derive
      live from `scripts/workflow-templates/self-hosted-qg-repos.txt` — 7 private repos as of 2026-08-08:
      `agent-orchestrator`, `strategy-service`, `e2e-testing`, `features-service`, `market-tick-data-service`,
      `execution-service`, `ml-service`), and document the RESOLVED 2026-08-05/07
      `unified-trading-pm`-public-with-self-hosted-runners incident as a standing invariant/lesson ("never register a
      self-hosted runner pool on a public repo" — verify the live grep pattern
      `grep -lE '^\s*runs-on: \[self-hosted' .github/workflows/*.yml | xargs grep -lE '^\s*(pull_request|pull_request_target):'`
      still returns zero and cite it as the standing check). (c) `/codex/05-infrastructure/agent-orchestrator-deploy.md`
      — re-verify (do not assume) the current AO/orchestrator VM (`i-0c9b283b31d6b5ca7`) instance type live
      (`aws ec2 describe-instances`), and make explicit that this VM is now DISTINCT from the dedicated CI VM in (a) —
      the doc must not conflate the two hosts. **Done when**: all three codex docs' `last_reviewed` date is bumped to
      the date of this fix, every fact above is confirmed against a live query (cite the exact command + output for
      each, not the number in this todo), and neither doc still describes self-hosted runners as living on the
      planning/orchestrator VM. Source: `issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` Part
      8, `[DOC] P2` ("Update stale codex docs") — never cited by any covering doc; blocked-by-infra-state until the
      CI-VM downsize (DONE 2026-08-08) and the public-repo migration (DONE 2026-08-07) both landed, which is why 6 prior
      `ci` batches never picked it up.

## Codex SSOTs (read before executing the todo above)

- `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md` — the doc being rewritten
- `/codex/07-security/self-hosted-runner-security-posture.md` — the doc being rewritten
- `/codex/05-infrastructure/agent-orchestrator-deploy.md` — the doc being rewritten
- `/codex/08-workflows/ci-cd-flow.md` — pipeline/runner-pool context
- `plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-08-09** — Drafted manually (mirroring `/ag-closeout-audit ci`'s satellite-batch-extraction pattern) against the
  15-doc `ci`-tranche candidate list from today's `/ag-closeout-audit ci` run
  (`issues/ag_closeout_audit_ci_parked_2026_08_08.md`), none of which whole-doc-reclassified. Full per-doc read +
  verdict (parent_epic in parens):

  - `github_actions_operator_gated_followups_2026_07_17.md` (`deployment_and_user_management_master`) — **0
    extractable.** All 10 open items are either already tracked in an active batch (billing/utilization re-pulls in
    batch4; the ~2-week fleet re-pull), gated on the operator's own account-provisioning timeline (slot-concurrency,
    explicitly cross-tranche `ao`-scope per batch6's own same-day finding, out of scope here), blocked on the open-ended
    `digest-drift-sweep` dormant-cascade investigation (STEP 2d), or explicitly "NOT recommended to start"
    (org-migration REVIEW). Re-confirmed by 6+ consecutive na-eligibility-audit passes; nothing new.
  - `issues/ag_closeout_audit_ci_parked_2026_08_08.md` (`infrastructure_master`) — **0 extractable.** This doc IS the
    report that produced batch6 and this candidate list; 0 checkbox todos, prose findings only.
  - `issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md` (`agent_operating_framework_master`) — **1
    extractable**, different `parent_epic` — drafted separately as batch 8, not here.
  - `issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` (`infrastructure_master`) — considered,
    **NOT extracted**: the open `[SCRIPT] P2` item ("implement the consumer-QG promote fan-out per the 2026-08-08
    operator ruling") has an approved design DIRECTION but no settled INTEGRATION POINT — UAC promotes via the shared
    fleet `ldr-to-main-promote(-fleet).yml`, not a per-service `image-build-gate.yml`-style workflow the cited pattern
    assumes, so "land as a new job in UAC's own promote-gate workflow" is underspecified against real UAC promotion
    plumbing. Modifying the shared fleet promote mechanism (or inventing a UAC-specific one) is a genuine re-scoping
    call, not a bounded implementation — left behind per "do not extract borderline items," matching this tranche's
    established caution around fleet-wide-promote-touching work.
  - `issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` (`infrastructure_master`) — **0
    extractable.** Sole open item (#3, "confirm whether the cicd-events ledger should carry `build_id`") is an explicit
    low-confidence judgment call, re-confirmed by the 2026-08-08 na-eligibility-audit round.
  - `issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` (no `parent_epic` field; treated as
    `infrastructure_master` to match its sibling CI-VM docs) — **1 extractable** (this batch's todo 1). Other open items
    considered and rejected: the job-minutes re-measure is already claimed by batch6 todo 1 (active, unfinished);
    re-baselining `qg_resource_baseline.json` and reaping the governor's marker-file leak both touch the SAME
    `.benchmarks/qg-governor/` mechanism that `qg_host_adaptive_resource_governor_2026_07_14.md` — a standing,
    twice-reconfirmed 2026-07-14 operator "human-driven, not AO-ingested" ruling — owns; extracting either would
    conflict with that ruling, so both stay behind. CI-volume investigation on the 2 heaviest repos has no stated
    done-when (borderline, not extracted). Staggering the promote-fleet fan-out and the fleet-wide concurrency cap are
    both real judgment calls on a shared, high-blast-radius mechanism, already deferred as such (D6-22) by batch6. The
    `[OPERATOR]` fork-PR-approval item is explicitly operator-deferred 2026-08-08.
  - `issues/ci_vm_exposure_remediation_2026_08_06.md` referenced as sibling context only, not itself in the 15.
  - `issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` (`deployment_and_user_management_master`) —
    **0 extractable.** Sole open item is the open-ended "why has the primary cascade been dormant" investigation,
    explicitly re-confirmed non-bounded by 4+ na-eligibility-audit passes.
  - `issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` (`infrastructure_master`) — **0
    extractable.** The `[REVIEW] P2` item is dependency-gated on a separate un-actioned allowlist-cleanup step; the
    `[SCRIPT] P1` automation-gap item is the SAME work already shipped via batch6 todo 3
    (`unified-trading-pm@b073c47f9`) — this doc's own checkbox is simply not yet reconciled, which is batch6-finalize's
    job (todo 1), not fresh work for this batch.
  - `issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` (`orchestrator_master`) — **0 extractable.**
    Today's own round7 na-eligibility-audit pass explicitly held this at KEEP-NA despite the head `[OPERATOR-DECISION]`
    resolving today, citing fleet-wide credential-resolution blast radius as "too_large_or_risky" — respected here, not
    overridden.
  - `issues/post_cutover_silent_assumption_sweep_2026_07_23.md` (`infrastructure_master`) — **0 extractable.** F1
    (kill-switch) is explicitly TIME-GATED on execution-service handling live order flow. The "reconcile ~4 weeks of
    missing tags" item is KEEP-NA-STALE, already duplicated in batch1. The F3 unconditional-success-reporting remainder
    is already extracted into `ci_satellite_ao_dispatch_batch5_2026_08_02.md` (verified via direct grep before
    considering it — avoided a near-duplicate here). F4 (vacuous crons) was explicitly considered and deferred by
    batch1's own Deferred table (D6/D3 in that doc's numbering) as needing "a per-cron ruling" (bug vs. genuinely-rare
    condition) before it is bounded — same call reached independently here. `sit_validated_workspace_digest` is an
    explicit design call.
  - `issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` (`infrastructure_master`) — **0
    extractable.** The sole remaining open item (delete the redundant hook script + repoint 4 referrers) is already
    owned by `ci_satellite_ao_dispatch_batch4_2026_07_31.md` todo 1 (active, verbatim claim) per the 2026-08-08
    na-eligibility-audit's own conflict-check.
  - `issues/pytest_timeout_60s_flaky_under_contention_continued2_2026_08_03.md` (no explicit `parent_epic`; part of the
    live capacity-crisis doc-chain) — **0 extractable.** Both open items are explicitly gated on
    `qg_governor_glue_runner_ledger_coordination_2026_08_03.md` Phases 2-3 landing first — a real dependency, not a
    judgment call, but not currently satisfiable.
  - `issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` (`infrastructure_master`) — **0
    extractable.** Filed hours before this batch; today's own round7 na-eligibility-audit pass explicitly holds todo 1
    (bounded in isolation) back as "too hot to batch while live" — a live, actively-diagnosed incident. Respected, not
    overridden.
  - `issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` (`infrastructure_master`) — **0
    extractable.** [A]/[B] explicitly await the operator reviewing a delivered design walkthrough before any ship
    (operator ruling 2026-08-08: "wants to SEE the exact keying logic... NOT shipping this session"). The one other live
    item (red-SIT-should-escalate-to-a-worker) is an operator-ruled design decision not yet scoped into a bounded
    implementation todo — explicitly stated as needing further scoping before it is dispatchable.
  - `plans/active/monitoring_control_plane_master_2026_06_10.md` (`observability_master`) — **0 extractable.** The 3
    open `[CODE] P0` items are dashboard/panel feature builds; today's own `/ag-closeout-audit ci` Phase-1 sweep already
    classified this doc
    `orphaned_partial_coverage — not AO-eligible (human_only_judgment; already parked in batch2's own Deferred)` —
    respected, not overridden, on the same reasoning (panel scope/layout is a design call, per this doc's own DONE items
    showing each required a concrete design pass before it became implementable).

  **Net: 15 docs read, 2 items extracted total (1 here + 1 in the sibling batch 8), 13 docs contributed zero.** This is
  the honest yield of a corpus this heavily pre-mined — not a shortfall in this pass's thoroughness.

- **2026-08-09 (execution)** — Todo 1 done. All 3 codex docs rewritten with every fact live-verified against AWS
  (`describe-instances`/`describe-volumes`) and the repo's own workflow-template config, not copied from the source
  audit doc: CI-runner VM `i-042a6332509482556` confirmed `m8i.2xlarge` (8 vCPU/32GB, downsized 2026-08-08 from
  `c8i.4xlarge` — the source doc's own agent-orchestrator-deploy.md text had this wrong as `m8i.4xlarge`→`m8i.2xlarge`
  on the wrong date 2026-08-07, both fixed), root volume `vol-03880fe9bf1ea805b` confirmed 12,000 IOPS/312 MB/s
  (matching that instance's EBS baseline, not the stale 6,000/500 interim figure); planning VM `i-0c9b283b31d6b5ca7`
  confirmed `m8i.2xlarge`/running, now stated explicitly as a distinct box from the CI VM; self-hosted repo set
  re-derived live from `scripts/workflow-templates/self-hosted-qg-repos.txt` (7 private repos, matches the todo's list
  exactly); the fork-PR security grep re-run live (zero matches); the `unified-trading-pm`-public-with-self-hosted
  incident updated from "open P0" to "RESOLVED 2026-08-07" with the standing invariant + live check documented.
  `last_reviewed`/`last_updated` bumped to 2026-08-09 on all three. Files:
  `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md`,
  `/codex/07-security/self-hosted-runner-security-posture.md`, `/codex/05-infrastructure/agent-orchestrator-deploy.md`.
