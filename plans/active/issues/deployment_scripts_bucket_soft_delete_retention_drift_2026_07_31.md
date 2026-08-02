---
doc_type: issue
title: "deployment-scripts bucket's live soft-delete retention (604800s) drifted from terraform's declared 0 (off)"
summary: >-
  While live-verifying uts-prd-sa's new IAM grants for
  bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md P2, a `tofu plan` against
  terraform/gcp (deployment-service) showed `google_storage_bucket.deployment_scripts[0]` would be updated in-place —
  `soft_delete_policy.retention_duration_seconds = 604800 -> 0` — a live/config drift on the
  `deployment-scripts-central-element-323112` bucket. main.tf's own comment + the archived
  `deployment_scripts_bucket_softdelete_log_churn_2026_06_01.md` (resolved 2026-06-09, "soft-delete cleared... TF
  codified") both assert soft-delete should be OFF (0) — matching the current config — but the LIVE bucket has
  retention_duration_seconds=604800 (7-day soft-delete) today. Not applied — deliberately excluded from this session's
  IAM-only apply via -target (out of scope for that task, and a bucket lifecycle/retention change on a live bucket needs
  its own judgment call, not a side-effect of an unrelated grant).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [gcp, terraform, drift, soft-delete, deployment-scripts]
related:
  [
    /plans/active/issues/bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
priority: P3
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
estimate_class: research
drift_direction: unclear
source: >-
  Surfaced 2026-07-31 (slot-7, infra) as a side-observation while running `tofu plan` for
  bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md P2 (uts-prd-sa IAM grants).
resolved_by:
locked_by:
depends_on: []
---

## What I found

`ENV=prod ./tofu.sh plan` (deployment-service/terraform/gcp) shows:

```
google_storage_bucket.deployment_scripts[0] will be updated in-place
~ soft_delete_policy {
    ~ retention_duration_seconds = 604800 -> 0
  }
```

i.e. live has 7-day soft-delete retention; config (and the terraform-managed intent per its own header comment + the
resolved 2026-06-01 issue doc that codified it) declares 0 (off). I did not run `tofu apply` on this resource — my
session's apply was `-target`-scoped to 5 unrelated IAM-grant resources specifically to avoid touching this drift.

## Why it matters

Soft-delete retention is a delete-safety mechanism referenced elsewhere in this workspace
(`gcs_bucket_soft_delete_retention_seconds() >= 604800s` is cited as a reversibility bar for AO delete-eligible todos) —
so whichever direction is correct here is a real safety-relevant decision, not a cosmetic drift:

- If live (604800, ON) is the INTENDED current state (e.g. someone deliberately re-enabled it after the 2026-06-01
  incident for safety, and the config/comment are what's stale), applying the config's `0` would silently DISABLE
  soft-delete recovery on this bucket — a real safety regression.
- If config (0, OFF) is still correct (the 2026-06-09 resolution's steady-state), then live has silently drifted back ON
  (possibly a manual re-enable, a partial rollback, or the original 2026-06-09 apply never actually landing) and the
  bucket may be accumulating the same run.log re-upload churn the archived issue described.

Either way this needs a decision, not a blind `tofu apply` of whichever value config happens to declare.

## Recommended decision

- [x] ✅ [INFRA] P3. **RESOLVED 2026-08-02** (operator ruling on
      `plan_reconcile_parked_operator_decisions_2026_08_02.md` na-eligibility-audit item 24). Terraform's
      `deployment-service/terraform/gcp/main.tf` `google_storage_bucket.deployment_scripts` declares
      `retention_duration_seconds = 0` with a clear, deliberate rationale in its own header comment ("soft-delete OFF —
      was retaining 56 TiB of run.log re-upload shadow copies"), so this was unintentional drift, not a superseding
      decision. Checked live soft-deleted object volume first (`gcloud storage ls -a`): **0 soft-deleted object versions
      present** — nothing at risk from reconciling. Applied option (a): live-corrected via
      `gcloud storage buckets update gs://deployment-scripts-central-element-323112 --clear-soft-delete`, verified
      `softDeletePolicy.retentionDurationSeconds` now reads `0`, matching terraform. No terraform change needed — it was
      already correct; only the live resource had drifted. (repo: deployment-service)

## Progress Log (na-eligibility-audit incremental marker)

- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid.** First verdict for this doc
  (no prior marker). Read end-to-end; `grep -cE '^- \[ \]'` = **1**, matching this verdict's item count. The sole todo
  is a genuine intent judgment call, not a bounded outcome: the two directions are observationally symmetric (apply the
  config's `0` and silently DISABLE soft-delete recovery on a live prod bucket, or update terraform to `604800` and
  bless a possibly-unintended manual re-enable), and the doc's own text says so — "Either way this needs a decision, not
  a blind `tofu apply`". It is additionally delete-safety-adjacent:
  `gcs_bucket_soft_delete_retention_seconds() >= 604800s` is the exact reversibility bar the delete-safety protocol § 3a
  cites for AO delete-eligible todos, so getting the direction wrong weakens a safety gate the rest of the corpus
  depends on. Independently corroborated by the 2026-08-01 `/ag-closeout-audit infra` run, which classified it
  `orphaned_never_touched` but correctly non-batchable on the same grounds.
