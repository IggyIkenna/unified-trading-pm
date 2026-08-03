---
doc_type: issue
title:
  "`deployment-service/terraform/gcp/live_event_log/` is a fully independent OpenTofu root (own state/backend), not an
  actual `module` of the parent root, despite a comment claiming inheritance — unclear if intentional"
summary: >-
  Deferred follow-up from deployment_service_root_state_orphaned_pubsub_publisher_iam_member_2026_08_03.md
  (resolved/archived): that doc's root cause was two independent OpenTofu roots (the parent `terraform/gcp/` root and
  `terraform/gcp/live_event_log/`) each owning state for the same live GCP IAM binding. `live_event_log/` has its own
  `.terraform/`, `.terraform.lock.hcl`, and `backend "gcs"` block (`live_event_log/main.tf:22`), and no `module
  "live_event_log" { source = "./live_event_log" }` block exists anywhere in the parent root's `.tf` files — yet
  `live_event_log/main.tf:9` carries a comment claiming "Provider + backend are inherited from the parent terraform/gcp/
  root module," which is not actually true (no module relationship exists; it's convention/copy-paste only). Not
  investigated: whether this disconnected-root structure was an intentional design choice (e.g. to isolate the event-log
  backend state for blast-radius reasons) or a historical accident (e.g. a module block that was removed/never added).
  Left as-is, it remains a standing risk for the SAME class of drift the parent issue found (two roots, one resource) to
  recur for any other resource `live_event_log/` declares.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [terraform, opentofu, gcp, state-hygiene, live_event_log]
related:
  [
    /plans/archive/issues/deployment_service_root_state_orphaned_pubsub_publisher_iam_member_2026_08_03.md,
    /codex/05-infrastructure/deployment-service-gcp-tofu-state.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
sequential: false
drift_direction: correct-code
source: >-
  Flagged 2026-08-03 (slot-12, infra) as an explicit deferred follow-up when closing out
  deployment_service_root_state_orphaned_pubsub_publisher_iam_member_2026_08_03.md — not investigated in that doc's
  scope.
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/deployment-service-gcp-tofu-state.md,
    deployment-service/terraform/gcp/main.tf,
    deployment-service/terraform/gcp/live_event_log/main.tf,
  ]
---

# `live_event_log/` disconnected OpenTofu root — intentional isolation or historical accident?

## What I found

See summary. `git log --follow` / `git blame` on `live_event_log/main.tf:9`'s inheritance comment and on the parent
`main.tf` around when `live_event_log/` was first added would show whether a `module` block ever existed and was
removed, or whether the directory was always structured this way.

## Why it matters

Whichever the answer, it determines the right fix: (a) if intentional isolation, the misleading "inherited from parent"
comment should be corrected to say so explicitly, so the NEXT person doesn't assume a module relationship exists (which
is exactly what let the orphaned-state drift in the parent issue go unnoticed); (b) if accidental, it's a real
architectural gap — either wire it as an actual `module "live_event_log" { source = "./live_event_log" }` block
(consolidating state, eliminating the two-roots-one-resource class of drift for good), or keep it separate but fix the
comment either way.

## Recommended decision

Needs an operator/architect call on which of (a)/(b) is intended — not a mechanical fix. A worker CAN do the git-history
investigation (bounded, checkable) and report findings; the decision on whether to consolidate the roots is the human
judgment call, hence `assigned_vm: NA`.

## Todos

- [ ] [OPERATOR] P3. Investigate via `git log --follow`/`git blame` on `deployment-service/terraform/gcp/main.tf` and
      `live_event_log/main.tf` whether `live_event_log/` was ever wired as an actual `module` block of the parent root
      (and if so, when/why it was split out), then decide: (a) intentional isolation — fix the misleading "inherited
      from parent" comment at `live_event_log/main.tf:9` to state the roots are independent by design, or (b) accidental
      — wire it as a real `module` block to consolidate state. (repo: deployment-service)

## Progress Log
