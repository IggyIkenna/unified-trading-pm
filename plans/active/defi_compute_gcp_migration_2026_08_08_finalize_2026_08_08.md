---
doc_type: plan
title: DeFi AWS-to-GCP compute migration — finalize
summary: >-
  Gated closeout for `defi_compute_gcp_migration_2026_08_08.md` — machine-held via `depends_on` + `gate_on_depends:
  true` until all 18 of that plan's todos are done. Self-contained plan (not a batch extraction), so this reconciles its
  own evidence, re-checks the two investigation-derived findings for any new follow-up they produced, confirms the
  ~$250/month savings target was actually re-measured (not assumed), and runs the standard archival ritual.
status: active
nature: process
asset_group: [defi, infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [defi, aws, gcp, cloud-migration, close-out, archival, plan-hygiene]
related:
  [
    /plans/active/defi_compute_gcp_migration_2026_08_08.md,
    /plans/epics/security_and_cross_cutting_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/defi_compute_gcp_migration_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [defi_compute_gcp_migration_2026_08_08]
gate_on_depends: true
sequential: true
source: >-
  Operator directive 2026-08-08 (flip the parent plan to AO dispatch) — required companion per
  `plans/active/task_template.md` §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# DeFi AWS-to-GCP compute migration — finalize

> **Machine-gated on `defi_compute_gcp_migration_2026_08_08.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 18 tasks in that plan are `done`. `sequential: true` because todo 2
> needs todo 1's evidence-verification pass finished, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Verify every one of the parent plan's 18 `- [x]` todos actually carries checkable evidence, not just a claim.** For each: if it cites a commit sha, confirm it's a real ancestor of the relevant repo's live
      branch (`git merge-base --is-ancestor <sha> origin/<branch>`); if it cites a Cloud Run revision/health-check
      result, re-run the check live rather than trusting the recorded text (`gcloud run services describe` for `Ready`
      state); if it cites an AWS resource deletion (`uts-defi-prod` cluster, the 3 ECS services, the AWS Batch job
      definitions/queue), confirm via a live `describe`/`list` call that the resource is actually gone, not just that
      the todo says so. **Done when**: every todo has an independently-reverified evidence line, and any todo whose
      evidence does NOT hold up is reopened with the discrepancy stated, not silently left `[x]`. Repo:
      unified-trading-pm.

- [ ] [REVIEW] P1. **Re-check the parent plan's two investigation-derived findings for follow-up work they might have produced.** Todo 1 (execution-service's actual role) and todo 2 (what scaled `uts-defi-prod` from 0→running) were
      open questions at authoring time — read what they actually found. If either surfaced a real gap (e.g. a live
      caller that needed repointing, an automated scale-up process nobody had disabled), confirm the parent plan's own
      todos already closed that gap; if not, write a new tracked todo (own doc if it doesn't fit an existing one) rather
      than letting the finding evaporate into this finalize plan's Progress Log. **Done when**: both findings are traced
      to either "fully closed within the parent plan, here's the todo that did it" or a new `- [ ]` todo exists for the
      gap. Repo: unified-trading-pm.

- [ ] [REVIEW] P2. **Confirm the ~$250/month AWS savings target was actually re-measured, not assumed.** The parent
      plan's own todo 18 calls for a post-decommission Cost Explorer re-measurement — verify that todo's evidence is a
      real before/after dollar figure (same `SERVICE`/`USAGE_TYPE` group-by, filtered `REGION=ap-northeast-1`
      methodology used to scope the parent plan), not a restatement of the original estimate. If the realized saving
      materially undershoots $250/mo,
      note why (e.g. data-transfer-out didn't drop as much as expected — worth its own follow-up todo if so). **Done
      when**: a real dollar figure is recorded here, sourced from a live Cost Explorer query, not copied from the plan's
      summary. Repo: unified-trading-pm.

- [ ] [DOCS] P2. **Archive the parent plan per the 6-step ritual, and only then.** In order: (1) confirm zero open
      `- [ ]` todos remain (all 18, post-verification above); (2) add the archival banner + set `status: complete`; (3)
      confirm the codex doc updates the parent plan's own todos 15 and 17 already made (`cloud-agnostic-migration.md`,
      `dual-cloud-cost-ops-playbook.md`, `manifest-consolidator-ssot.md`) are live on `origin/live-defi-rollout`, not
      just committed locally; (4) confirm the `security_and_cross_cutting_master` epic's two stale todos ("Operator sign-off on
      dual-cloud parity", "GCP bucket decommission") were actually flipped/annotated per the parent plan's todo 16 —
      re-verify live, don't trust the parent's own claim; (5) update every referrer's path corpus-wide — grep for
      `defi_compute_gcp_migration_2026_08_08` and repoint each hit to the archived path (leading-slash,
      repo-root-relative); (6) clear the lock if any was set (confirm rather than assume). Then physically move the
      parent plan under `plans/archive/2026_08/`. **Done when**:
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py` shows no
      NEW dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans for this
      doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside `defi_compute_gcp_migration_2026_08_08.md` when that plan was flipped from
  `assigned_vm: NA` to `planning` per operator directive. `status: active` immediately (not `draft`) — machine-held from
  actually dispatching via `depends_on` + `gate_on_depends: true` until the parent plan's 18 todos are done.
- **context-scout 2026-08-15**: refreshed context_scope (5 entries), still accurate — a code-free finalize gate, the set
  is the gated parent plan + the 6-step archival ritual's codex/format SSOTs.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
