---
doc_type: plan
title: GitHub Actions CI/CD cost reduction — self-host the glue, kill the minute-minimum tax, fix cron cadence
summary: >-
  SPLIT 2026-07-24 (plan line-cap remediation, plan_line_cap_remediation_2026_07_23.md row 13) — this doc is now a thin
  redirect index, not a live record; nothing is tracked here anymore. The full content lives in 3 child docs:
  `plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md` (self-hosted-runner migration,
  COMPLETE, archived, 0 open todos), `plans/active/github_actions_operator_gated_followups_2026_07_17.md`
  (operator-gated followups, ACTIVE, 9 open todos), and
  `plans/active/github_actions_staging_machinery_shutdown_2026_07_24.md` (staging-branch machinery shutdown, ACTIVE, 1
  partially-done todo). Kept only so existing cross-references (`related:`, `parent_epic`, old commit messages) still
  resolve to something — read the matching child instead of this file.
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
last_updated: 2026-07-24
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P0
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
