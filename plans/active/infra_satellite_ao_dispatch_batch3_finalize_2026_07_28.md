---
doc_type: plan
title: Infra satellite AO dispatch batch 3 — finalize (reconcile source-doc checkboxes + archive)
summary: >-
  Gated closeout for `infra_satellite_ao_dispatch_batch3_2026_07_28.md`, per the finalize-plan-coverage rule
  (`task_template.md` §4). Once each of the parent batch's 6 todos is done, reconciles the corresponding checkbox(es)
  back into its true source doc (`e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md`,
  `issues/git_health_not_clean_since_pinned_constant_2026_07_27.md`,
  `issues/legacy_bucket_template_literals_2026_07_16.md`,
  `issues/heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md`,
  `issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md`,
  `issues/relaunch_stalled_vm_no_checkpoint_resume_gap_2026_07_27.md`) and checks whether any source doc now has zero
  open todos and is itself an archival candidate.
status: draft
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, close-out, batch-3, satellite-docs, archival, plan-hygiene]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch3_2026_07_28.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-28"
last_updated: "2026-07-28"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
sequential: true
drift_direction: advance-code
depends_on: [infra_satellite_ao_dispatch_batch3_2026_07_28]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  `/ag-closeout-audit infra` run 2026-07-28, per the standing finalize-plan-coverage rule (every assigned_vm:planning
  plan needs a gated finalize twin), mirroring `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`'s pattern.
---

# Infra satellite AO dispatch batch 3 — finalize

> **`status: draft` — NOT ingested, NOT dispatched.** Flips to `active` only together with its parent batch, on
> explicit operator approval.

> **Machine-gated on `infra_satellite_ao_dispatch_batch3_2026_07_28.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 6 tasks in that plan are `done`.

## Todos

- [ ] [REVIEW] P2. **Reconcile all 6 source docs' checkboxes + check archival eligibility.** For each of batch 3's 6
      now-done todos: find the corresponding checkbox(es) in the source doc its text names (every todo ends with
      `Source: <doc>.md`) and flip them `[x]`, citing the batch-3 commit(s) that shipped it. **Verify each cited sha
      actually exists and is an ancestor of `origin/live-defi-rollout`
      (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`) before citing it.** The 6 source docs:
      `e2e_coverage_gaps_alerting_deployment_trading_agent_2026_07_27.md` (all 3 checkboxes),
      `issues/git_health_not_clean_since_pinned_constant_2026_07_27.md` (all 3),
      `issues/legacy_bucket_template_literals_2026_07_16.md` (prose-only, no checkboxes — update the Disposition
      section instead), `issues/heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md` (Todo 1
      only — Todo 4 stays open, OPERATOR-gated), `issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md`
      (Todo 7 only — Todos 1-6 already closed), `issues/relaunch_stalled_vm_no_checkpoint_resume_gap_2026_07_27.md`
      (its one todo). For each source doc left with zero open todos after this reconciliation, run the standard
      6-step archival ritual (migrate DEFERRED → banner → codex-alignment check → corpus-wide referrer-path fixup →
      clear lock — none of these 6 carry a lock) rather than just flipping the checkbox. **Also handle the 2
      `archivable_now` findings this batch's own audit surfaced but did NOT touch** (out of this skill's scope,
      `/plan-reconcile`'s territory): `issues/rotate_exchange_keys_stale_venue_registry_2026_07_23.md` and
      `issues/capability_manifest_ml_models_probe_stale_import_2026_07_26.md` are both fully shipped with only stale
      `status`/`resolved_by` frontmatter — verify the shipped-work claims (cited commit shas resolve on
      `origin/live-defi-rollout`) and, if confirmed, flip `status: resolved` + fill `resolved_by:` + run the archival
      ritual on both (this is safe, evidence-backed housekeeping, not a fresh judgment call). **Done when**: every one
      of the 6 batch-3 source docs' checkbox state matches reality (closed with a verified commit sha, or explicitly
      left open with a re-confirmed reason), any source doc left with zero open todos has been through the 6-step
      archival ritual, the 2 archivable_now docs are confirmed + archived, and this finalize plan + its parent are
      themselves archived once all of the above is done. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/11-project-management/` (findings triage, archival ritual, issue-doc lifecycle) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` (`status: draft` semantics)
· `plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-07-28** — Drafted alongside `infra_satellite_ao_dispatch_batch3_2026_07_28.md` by `/ag-closeout-audit infra`
  (Autonomous mode). Left `status: draft` — flips to `active` only with its parent, on explicit operator approval.
