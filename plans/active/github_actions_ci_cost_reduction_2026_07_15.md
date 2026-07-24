---
doc_type: plan
title: GitHub Actions CI/CD cost reduction — self-host the glue, kill the minute-minimum tax, fix cron cadence
summary: >-
  PM is ~48% of a ~$1,000/mo GitHub Actions bill despite a code freeze because it is the fleet CI/CD control tower —
  ~79% of its runs are automation (status routing, deploy dispatch, promotion/health crons), only ~8% are doc commits.
  All repos are private (every minute billed) and there are ZERO self-hosted runners, so the biggest untapped lever is
  moving lightweight glue off $0.006/min GitHub-hosted runners onto compute we already run 24/7. Tiered fix — self-host
  the switchboard+crons (39 MOVE: 38 runs-on flips + 1 composite-action conversion), collapse the quality-gates job
  fan-out that pays a 1-min minimum per sub-second job, and fix cron cadence; 17 workflows stay hosted (test gates,
  fleet templates, a cross-repo reusable, the failure-independence monitors + their alert carrier). ALL decisions closed
  2026-07-15/16. ACTIVE + operator-driven (assigned_vm NA — never auto-dispatched). 8 runners live on the orchestrator
  VM (5 JIT-ephemeral glue + 3 long-lived glue-writer, disjoint labels). **STEP 2 COMPLETE 2026-07-17: 37/37 movers
  self-hosted, zero-billed, verified on real runs.** **STEP 2c SHIPPED 2026-07-17 (@a6057ea36, promoted to main same
  day): all 22 persist-cicd-event callers converted to the composite action (~$117/mo of 1-min-minimum persist jobs
  removed); the old reusable's DELETION is staged behind observing green ci-status-update runs on main — until it lands,
  `git revert a6057ea36` is a one-command rollback.** D1 (2b↔2c checkout collision) RESOLVED by operator delegation —
  checkout kept, @main pin rejected. A2 SHIPPED + PROVEN 2026-07-17 (Firestore content-sentinel dedup, fleet-live;
  two-dispatch proof on alerting-service: MISS+save then 22s HIT+skip with the required check green). A1 SHIPPED
  2026-07-17 (docs-only fast-path; tests+typecheck short-circuit, lint-codex always full). Next = A5 + the amended STEP
  2b trim; D2-D4 are open operator decisions. One P0 pending: quickmerge's --agent sentinel races its own rebase on a
  busy branch.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, self-hosted-runner, workflows, spend-reduction]
related:
  - /plans/archive/issues/github_billing_dashboard_access_2026_07_09.md
  - /plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
created: 2026-07-15
last_updated: 2026-07-17
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: infra
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  - "operator ask 2026-07-15 (spend investigation): GitHub bill ~$50-82/day during code freeze; why is PM so expensive"
  - "live Enhanced-Billing usage report (users/IggyIkenna/settings/billing/usage) via github-billing-token, Jun+Jul 2026"
  - "PM Actions run-mix sample: 1000 runs / 13.5h window ending 2026-07-15T06:53Z"
drift_direction: advance-code
---

# GitHub Actions CI/CD cost reduction

> **🗄️ SPLIT 2026-07-24 — this doc is now a thin index, not a live record.** Per the 2026-07-23 plan line-cap
> remediation triage (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row 13), every section this file
> used to carry — the ▶ START HERE runbook, the MOVE/STAY manifest, the full Phase 0-6 narrative, every Progress Log
> entry, the "Deferred work" ledgers, and the 2026-07-23 cost ruling — has been extracted **verbatim** into the three
> child docs below. Nothing here is unique anymore; read the child that matches what you need instead of this file.

- **Self-hosted-runner migration (2026-07-15 → 07-17) — COMPLETE, archived, 0 open todos.** The full deploy runbook
  (D1-D6), the MOVE/STAY manifest, the phased flip (STEP 2/2b/2c), Phase 2 (A1/A2/A5 QG fan-out collapse), Phase 3 (cron
  cadence), Phase 4 (serverless — dropped), and every 2026-07-15/16/17 Progress Log entry:
  `plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md`
- **Operator-gated followups — ACTIVE, 9 open todos.** The quickmerge `--agent` sentinel-race P0, STEP 2d + the
  3-dead-workflow decisions, the `persist-cicd-event` ledger race (D2), the bare-host bootstrap proof, the two
  calendar-gated billing re-pulls (Phase 5), the full "Deferred work after 2026-07-17" operator-decision ledger, the
  2026-07-22 post-migration system check, the 2026-07-23 1-week billing check, the 2026-07-23 semver-agent cost ruling,
  and "Deferred work after 2026-07-23": `plans/active/github_actions_operator_gated_followups_2026_07_17.md`
- **Staging-branch machinery shutdown (Phase 6, same-day 2026-07-23 audit) — ACTIVE, 1 partially-done todo.** The
  dead-cron shutdown + the staging-backmerge-to-ldr escalation-dispatch bugfix (both DONE, measured) and the remaining
  codex-SSOT-homing todo: `plans/active/github_actions_staging_machinery_shutdown_2026_07_24.md`

Nothing is tracked in this file anymore — do not add new todos here; file them against whichever child above they belong
to (or a new plan, if none of the three fit). This doc is kept only so existing cross-references (`related:`,
`parent_epic`, old commit messages, this plan's own frontmatter `title`) still resolve to something.
