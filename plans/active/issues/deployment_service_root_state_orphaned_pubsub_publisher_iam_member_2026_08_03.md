---
doc_type: issue
title:
  "deployment-service/terraform/gcp root state carries an orphaned
  google_project_iam_member.unified_trading_pubsub_publisher entry with no matching config — `tofu apply` would revoke a
  live IAM binding that a SEPARATE OpenTofu root (live_event_log/) still declares under a different resource address"
summary: >-
  While executing unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md P2 (terraform-importing 28 undeclared
  unified-trading-sa IAM roles), `ENV=prod ./tofu.sh plan` in deployment-service/terraform/gcp surfaced one unrelated
  pre-existing drift item outside that task's scope: `google_project_iam_member.unified_trading_pubsub_publisher`
  (grants roles/pubsub.publisher to unified-trading-sa) is present in the parent root's state but has zero matching
  resource block anywhere in the parent root's *.tf files, so `tofu plan` marks it "will be destroyed". The live binding
  it represents is NOT actually undeclared — it is declared, under the different resource address
  `google_project_iam_member.unified_trading_sa_pubsub_publisher`, inside `live_event_log/publisher_iam.tf` — but that
  directory is its OWN separate OpenTofu root (has its own `.terraform/`, `.terraform.lock.hcl`, and `backend "gcs"`
  block; it is NOT invoked as a `module` from the parent root, despite a comment there claiming backend/provider
  "inherited from the parent"). So two independent terraform roots each believe they own the same live GCP IAM binding —
  the parent via a now-orphaned state entry, live_event_log via its actual declared resource — and applying the parent
  root's pending drift (this item is one line in a larger pre-existing "17 add / 5 change / 3 destroy" plan from other
  in-flight work) would call the GCP API to remove unified-trading-sa from roles/pubsub.publisher, a live binding still
  relied on by services publishing to the event-log Pub/Sub topics outside VM contexts (local dev, Cloud Run jobs — per
  publisher_iam.tf's own comment).
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [iam, terraform, opentofu, gcp, state-hygiene, drift, pubsub]
related:
  [
    /plans/active/issues/unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md,
    /codex/05-infrastructure/deployment-service-gcp-tofu-state.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
assigned_role: infra
sequential: false
drift_direction: correct-code
source: >-
  Surfaced 2026-08-03 (slot-8, infra) while executing unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md P2 —
  a side-observation in the `tofu plan` diff, not that task's own scope.
resolved_by:
  "todo done 2026-08-03: orphaned google_project_iam_member.unified_trading_pubsub_publisher removed from the parent
  root's state via `ENV=prod ./tofu.sh state rm` (state-only op, no GCP API call); re-verified via `ENV=prod ./tofu.sh
  plan` that the destroy no longer appears and the pending plan dropped from 3 to 2 destroys with no other diff
  introduced (deployment-service, no code commit needed)."
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/deployment-service-gcp-tofu-state.md,
    deployment-service/terraform/gcp/_imports_reconcile.tf,
    deployment-service/terraform/gcp/live_event_log/publisher_iam.tf,
  ]
---

# Orphaned `unified_trading_pubsub_publisher` state entry in the parent terraform root would revoke a live IAM binding on next apply

## What I found

`cd deployment-service/terraform/gcp && ENV=prod ./tofu.sh plan` shows:

```
# google_project_iam_member.unified_trading_pubsub_publisher will be destroyed
# (because google_project_iam_member.unified_trading_pubsub_publisher is not in configuration)
- resource "google_project_iam_member" "unified_trading_pubsub_publisher" {
    - etag    = "..." -> null
    - id      = "central-element-323112/roles/pubsub.publisher/serviceAccount:unified-trading-sa@central-element-323112.iam.gserviceaccount.com" -> null
    - member  = "serviceAccount:unified-trading-sa@central-element-323112.iam.gserviceaccount.com" -> null
    - project = "central-element-323112" -> null
    - role    = "roles/pubsub.publisher" -> null
  }
```

`grep -rn "unified_trading_pubsub_publisher" --include="*.tf" .` (from the parent root, including subdirectories)
returns **zero matches** — this exact resource address does not exist in any `.tf` file anywhere in the repo. It is a
pure state-only orphan.

The equivalent live binding IS declared — under a different resource address,
`google_project_iam_member.unified_trading_sa_pubsub_publisher` — in
`deployment-service/terraform/gcp/live_event_log/publisher_iam.tf`:

```hcl
resource "google_project_iam_member" "unified_trading_sa_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:unified-trading-sa@${var.project_id}.iam.gserviceaccount.com"
}
```

But `live_event_log/` is **not** a module of the parent root — it has its own `.terraform/`, `.terraform.lock.hcl`, and
a `backend "gcs"` block (`live_event_log/main.tf:22`), and no `module "live_event_log" { source = "./live_event_log" }`
block exists anywhere in the parent root's `.tf` files. It is a fully independent OpenTofu root that happens to live in
a subdirectory, despite a comment in `live_event_log/main.tf:9` claiming "Provider + backend are inherited from the
parent terraform/gcp/ root module" (true only by convention/copy-paste, not an actual module relationship).

**Net effect**: two independent terraform states each have an entry that maps to the SAME live GCP IAM binding
(`roles/pubsub.publisher` → `unified-trading-sa`) — the parent root's is orphaned (no config, destroy-pending), the
`live_event_log` root's is the real, current, config-backed owner.

## Why it matters

This is exactly the kind of drift the parent finding (unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md)
exists to eliminate, just for a different reason (a stale rename, not an out-of-band grant): if anyone ever runs
`ENV=prod ./tofu.sh apply` on the full pending parent-root plan (which currently also carries ~17 add / 5 change / 3
destroy from other unrelated in-flight work — not inspected in detail here, out of this doc's scope), this specific line
would call `google_project_iam_member`'s Delete, revoking `roles/pubsub.publisher` from `unified-trading-sa` on the live
project. Per `publisher_iam.tf`'s own comment, this binding is relied on for non-VM publish paths (local dev, Cloud Run
jobs) into the live-event-log Pub/Sub topics. The `live_event_log` root's own state would not know about the revocation
until its next `plan`/`apply`, at which point it would want to re-add it — a real, if likely brief, gap in publish
capability, entirely avoidable.

## Recommended decision

The parent root's orphaned entry is a pure duplicate of state that `live_event_log/`'s root already owns correctly —
removing it from the PARENT state (not from GCP, not from `live_event_log`'s state) is safe and sufficient:

```bash
cd deployment-service/terraform/gcp
ENV=prod ./tofu.sh state rm google_project_iam_member.unified_trading_pubsub_publisher
ENV=prod ./tofu.sh plan   # verify: this destroy no longer appears
```

`state rm` only edits the parent root's local tracking — it does not call any GCP API and does not touch
`live_event_log`'s separate state, which continues to own and correctly reflect the live binding. No
`google_project_iam_member` create/delete call happens on either side.

(Out of scope for this doc: whether `live_event_log/` being a disconnected root instead of an actual `module` block was
intentional — tracked as its own follow-up at
`/plans/active/issues/deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md`.)

## Todos

- [x] [TERRAFORM] P2. ✅ Ran
      `ENV=prod deployment-service/terraform/gcp/tofu.sh state rm     google_project_iam_member.unified_trading_pubsub_publisher`,
      then verify via `ENV=prod ./tofu.sh plan` that the destroy no longer appears and no other diff was introduced. No
      commit needed unless the state-rm needs to be logged (evidence in this doc's Progress Log is sufficient). (repo:
      deployment-service)

## Progress Log

- 2026-08-03 (slot-12, infra): Re-confirmed the orphaned entry via `ENV=prod ./tofu.sh plan` (destroy-pending, identical
  to the doc's evidence). Ran `ENV=prod ./tofu.sh state rm google_project_iam_member.unified_trading_pubsub_publisher` —
  succeeded ("Removed google_project_iam_member.unified_trading_pubsub_publisher / Successfully removed 1 resource
  instance(s)."). Re-ran `ENV=prod ./tofu.sh plan`: the parent root's pending plan dropped from 17 add/5 change/3
  destroy to **17 add/5 change/2 destroy** — the orphaned `unified_trading_pubsub_publisher` no longer appears anywhere
  in the diff (`grep -c` = 0), and the 2 remaining destroys are pre-existing unrelated drift
  (`google_secret_manager_secret_iam_member.t1_batch_gh_pat_accessor`, `...t1_batch_slack_webhook_accessor`), confirming
  no new diff was introduced. `state rm` only edits local state tracking via the GCS backend — no GCP API create/delete
  call was made, and `live_event_log/`'s separate root/state was not touched. No code change in `deployment-service`
  (state-only op); this plan-doc edit is the full evidence trail.
