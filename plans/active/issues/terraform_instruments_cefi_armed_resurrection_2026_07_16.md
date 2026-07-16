---
doc_type: issue
title:
  ARMED RESURRECTION — `google_storage_bucket.instruments_cefi` is still declared + in prod state while the physical
  bucket is 404; the next `tofu apply` on prod WILL recreate `instruments-store-cefi-central-element-323112` as an empty
  shell
summary:
  "Measured live 2026-07-16 while executing the sports legacy-bucket cutover T4.4 gate: a real `tofu plan` against
  `terraform/state/prod` (run via the Cloud Build executor, which holds the bucket perms `unified-trading-sa` lacks)
  reports **`google_storage_bucket.instruments_cefi will be created`** — the ONLY bucket-create in the whole plan. The
  physical bucket `instruments-store-cefi-central-element-323112` is **404** (confirmed by the elevated Cloud Build SA,
  not by the 403-prone local SA). Cause: `terraform/gcp/main.tf:137` still DECLARES the resource and the prod state
  still holds the entry, but the bucket was deleted out-of-band — the exact documented resurrection class that recreated
  ~30 cleanup-deleted buckets on 2026-07-12T21:59Z ([[terraform_bucket_estate_drift_resurrection_2026_07_13]]), and
  which `main.tf` itself warns about verbatim in five separate REMOVED-comments. cefi is the one twin that got the
  physical delete WITHOUT the config removal + `state rm`. **Not introduced by the sports cutover** — the sports leg
  removed its own block + `state rm`-ed its entry first, precisely so this could not happen to it, and the same plan
  shows ZERO actions on the sports legacy bucket. Fix = remove the `instruments_cefi` block + `terraform state rm` it,
  mirroring the tradfi/defi removals at `main.tf:172-180`."
status: open
nature: issue
asset_group: [cefi]
stage: [data, meta]
repos: [deployment-service, unified-trading-pm]
scope: [admin, engineer]
tags: [terraform, gcs, bucket-canonicalisation, resurrection, drift, infra, destructive-risk]
related:
  [
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ../bucket_estate_consolidation_to_sub100_2026_07_13.md,
    ../gcs_bucket_estate_cleanup_2026_07_10.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.2
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: [sports_legacy_bucket_cutover_2026_07_16.md T4.4 gate execution 2026-07-16]
---

# `instruments_cefi` is an ARMED terraform resurrection

> **Found while running the sports cutover's T4.4 `tofu plan` gate. Read-only measurement; NOT fixed here** — fixing it
> means touching another plan's resource (`bucket_estate_consolidation`), and the sports leg's rule is findings-triage:
> outside every plan → issue doc + notify.

## The measurement

`tofu plan` against `terraform/state/prod` (OpenTofu 1.12.3, vars `project_id=central-element-323112`,
`region=asia-northeast1`, `environment=prod`, `bucket_prefix=uts`), executed inside Cloud Build
**`ea03c145-25a0-4280-acc3-75a99486ed76` (SUCCESS)** because `unified-trading-sa` lacks `storage.buckets.get` and dies
on 174 pre-existing 403 refresh errors locally:

```
Plan: 1 to import, 20 to add, 51 to change, 1 to destroy.

=== ALL bucket CREATE actions (resurrection candidates) ===
  # google_storage_bucket.instruments_cefi will be created      <-- THE ONLY ONE
```

And the bucket does not exist — via the **elevated** Cloud Build SA (build `0aa821f4-adf2-4ff2-b68d-96d917c4ed1d`), so
this is not the local SA's 403-masquerading-as-404:

```
ERROR: (gcloud.storage.buckets.describe) gs://instruments-store-cefi-central-element-323112 not found: 404.
```

## Why it is armed

| layer         | state                                                                                           |
| ------------- | ----------------------------------------------------------------------------------------------- |
| physical      | **404 — deleted** (2026-07-14, `bucket_estate_consolidation` W2 / item E)                       |
| terraform cfg | **still DECLARED** — `deployment-service/terraform/gcp/main.tf:137` `"instruments_cefi"`        |
| prod state    | **still present** — `google_storage_bucket.instruments_cefi`                                    |
| ⇒ next apply  | **CREATES an empty shell** `instruments-store-cefi-central-element-323112` (metageneration = 1) |

This is the **documented** failure mode. `main.tf` warns about it verbatim in five REMOVED-comments, e.g. `:315-320`:

> _"…was recreated as an empty shell by an out-of-band `tofu apply` (metageneration=1,
> creation_time=2026-07-13T00:52:06Z) because this resource block was still declared here after the physical bucket was
> deleted"_

and `:326-329`:

> _"Removing the resource blocks BEFORE the physical delete (paired with `terraform state rm`) so a future apply cannot
> resurrect them as empty shells — the exact failure that recreated ~30 cleanup-deleted buckets on 2026-07-12T21:59Z"_

**The tradfi / defi / prediction / sports twins all got the config-removal + `state rm` treatment. cefi got the physical
delete without it.** It is the last one holding the loaded chamber.

## Blast radius

Anyone running `tofu apply` on `terraform/gcp` @ `terraform/state/prod` — a routine `bootstrap_gcp.sh --env prod` — will
recreate the bucket. An empty `instruments-store-cefi-…` shell then:

- re-contaminates the estate the `sub-100` consolidation is driving down (it counts against the bucket budget);
- re-creates a **flat, no-env Group-A name** that the 2026-05-11 operator reversal explicitly retired
  (`cloud-providers.yaml:136-140`), which is precisely what `main.tf:6-8`'s corrected header now warns against;
- silently re-arms every "is the flat twin gone?" audit that closed on cefi.

## Fix (one commit, mirrors the existing precedent exactly)

1. Delete the `resource "google_storage_bucket" "instruments_cefi"` block at `terraform/gcp/main.tf:137`, leaving a
   REMOVED comment in the verbatim shape of `:172-180` (tradfi/defi).
2. `tofu state rm google_storage_bucket.instruments_cefi` against
   `bucket=uts-terraform-state-central-element-323112 prefix=terraform/state/prod`.
3. Re-run the plan and require **zero** `google_storage_bucket.* will be created`.

Do **1 before 2 is applied anywhere** — and never run a full `tofu apply` on prod until this is fixed, because that
apply is the very thing that resurrects it.

## Related landmine found in the same plan (NOT fixed, lower severity)

The prod state carries **orphaned entries whose config was removed 2026-07-13 and whose live resources are already
gone** — `google_cloud_scheduler_job.manifest_consolidator_cron["instruments-sports-legacy"]` and
`module.manifest_consolidator_job["instruments-sports-legacy"]` (+ the `market-data-sports-legacy` pair). Both
`gcloud scheduler jobs describe` and `run jobs describe` return NOT_FOUND. These are self-healing (refresh sees 404 →
drops from state) and are **not** delete-blockers, but they are evidence that **no clean `tofu apply` has run against
prod since at least 2026-07-13** — which is itself why this issue could sit armed for days.

## Progress Log

**2026-07-16** — Found by the sports cutover's T4.4 gate (Phase-5/delete leg). Measured, not inherited: real `tofu plan`
via Cloud Build `ea03c145-25a0-4280-acc3-75a99486ed76`; 404 confirmed via elevated SA build
`0aa821f4-adf2-4ff2-b68d-96d917c4ed1d`. Filed rather than fixed — `instruments_cefi` belongs to
`bucket_estate_consolidation_to_sub100_2026_07_13`, and the sports leg's scope was explicitly the instruments-sports
bucket only (its own block WAS removed + `state rm`-ed, and the same plan proves ZERO actions reference it). **Operator
notified in the leg's final report.**
