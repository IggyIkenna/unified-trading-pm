---
doc_type: issue
title: Prod terraform drift backlog needs a deliberate operator-gated reconcile-apply (21 add / 18 change)
summary: |
  A full `tofu plan` against `terraform/state/prod` (`deployment-service/terraform/gcp`) shows 21-add/18-change/0-destroy
  of committed-but-un-applied resources (BigQuery `feature_external` tables, `paper_stream` job/cron,
  `batch_live_smoke_matrix`, the recovered `expected_universe_v2` run.invoker IAM, `odum_portal` domain mapping,
  defi_forward_poll updates). Surfaced 2026-06-23 during an unrelated watch-the-watchers dead-man's-switch `tofu apply`
  (targeted to that apply's own resources only, to avoid blindly sweeping this backlog in). Excised
  2026-07-24 from `data_pipeline_hardening_self_monitoring_2026_06_22.md` (plan line-cap remediation split, row 9) —
  this is a general prod-infra terraform-drift item, not a data-pipeline-hardening concern.
status: open
nature: process
asset_group: [cross-cutting, infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infra, terraform, drift, prod, reconcile-apply]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
source:
  [
    "Excised 2026-07-24 from data_pipeline_hardening_self_monitoring_2026_06_22.md per the plan line-cap remediation
    triage (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 9) — the original author's own note already
    said 'filing as a P1 issue todo', this doc completes that filing.",
    "Originally surfaced 2026-06-23 during the watch-the-watchers dead-man's-switch tofu apply.",
  ]
related: [/plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md]
depends_on: []
---

# Prod terraform drift backlog needs a deliberate operator-gated reconcile-apply

## What I found

- **FINDING (separate, flagged not swept):** prod `terraform/state/prod` has a DRIFT BACKLOG of committed-but-un-applied
  changes (BigQuery `feature_external` tables, `paper_stream` job/cron, `batch_live_smoke_matrix`, the recovered
  `expected_universe_v2` run.invoker IAM, `odum_portal` domain mapping, defi_forward_poll updates — 21 add / 18 change
  in the full plan). NOT mine to sweep in a deadman apply. Needs a deliberate operator-gated reconcile-apply. → filing
  as a P1 issue todo.

## Why it matters

Committed-but-unapplied terraform means the working tree and the deployed prod state have drifted apart in ways nobody
has explicitly reviewed — some of these resources (e.g. `paper_stream` job/cron, `batch_live_smoke_matrix`) may be
load-bearing for in-flight work and their absence in prod could be masking a gap, while others (e.g. `odum_portal`
domain mapping) may be intentionally staged ahead of a cutover. Applying blind risks reverting or half-shipping
unrelated resources; not applying at all risks the drift silently growing. This is a general prod-infra concern
(`deployment-service/terraform/gcp`), not scoped to any one asset-group's data pipeline — it does not belong inside a
data-pipeline-hardening plan.

## Recommended decision

Someone with prod-infra + terraform context should walk the current `tofu plan` diff resource-by-resource, confirm each
is intended (not stale/abandoned), and apply in a deliberate operator-gated pass — mirroring how the watch-the-watchers
dead-man's-switch apply was scoped to `-target=...` its own resources rather than a blanket apply. Re-run `tofu plan`
fresh before acting (the 21/18 counts are as of 2026-06-23 and may have shifted).

## Todos

- [ ] [INFRA] P1. **Reconcile the prod terraform drift backlog** (`deployment-service/terraform/gcp`, state
      `terraform/state/prod`): a full `tofu plan` shows 21-add/18-change/0-destroy of committed-but-un-applied resources
      (bigquery feature_external tables, paper_stream, batch_live_smoke_matrix, expected_universe_v2 run.invoker IAM,
      odum_portal domain mapping). Review each is intended + operator-gated apply. Surfaced 2026-06-23 during the
      deadman apply (targeted to avoid sweeping these blindly).
